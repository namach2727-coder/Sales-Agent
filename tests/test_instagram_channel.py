from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal, PrincipalMembership
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode, ROLE_BY_CODE
from app.config import Settings, get_settings
from app.database import get_db
from app.instagram_channel.exceptions import (
    InstagramChannelConflictError,
    InstagramChannelInvalidTransitionError,
    InstagramChannelNotFoundError,
    InstagramChannelStaleWriteError,
)
from app.instagram_channel.models import InstagramConnection
from app.instagram_channel.router import router
from app.instagram_channel.security import FernetTokenCipher
from app.instagram_channel.service import (
    InstagramChannelService,
    connection_to_public,
)
from app.models import (
    AuthTenantRoleAssignment,
    Store,
    StoreAccessAssignment,
    Tenant,
    TenantAuditLog,
    TenantMembership,
    UserIdentity,
)
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def channel_engine(tmp_path_factory):
    path = tmp_path_factory.mktemp("foundation08-channel") / "channel.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SeedRunner(engine, default_registry()).run("test")
    yield engine
    engine.dispose()


def tenant_context(
    engine,
    *,
    role: str = "tenant_owner",
    all_store_access: bool = True,
):
    suffix = uuid.uuid4().hex[:10]
    with Session(engine, expire_on_commit=False) as db:
        identity = UserIdentity(
            email=f"{suffix}@example.test",
            normalized_email=f"{suffix}@example.test",
            display_name=f"User {suffix}",
            status="active",
        )
        tenant = Tenant(
            name=f"Tenant {suffix}", slug=f"tenant-{suffix}", status="active"
        )
        db.add_all([identity, tenant])
        db.flush()
        store = Store(
            tenant_id=tenant.id,
            name="Main",
            slug="main",
            status="active",
            currency_code="IRR",
        )
        membership = TenantMembership(
            user_id=identity.id,
            tenant_id=tenant.id,
            principal_type="user",
            principal_id=str(identity.id),
            status="active",
            all_store_access=all_store_access,
        )
        db.add_all([store, membership])
        db.flush()
        db.add(
            AuthTenantRoleAssignment(
                membership_id=membership.id,
                role_code=role,
                status="active",
            )
        )
        if not all_store_access:
            db.add(
                StoreAccessAssignment(
                    membership_id=membership.id,
                    store_id=store.id,
                    status="active",
                )
            )
        db.commit()
        principal = AuthenticatedPrincipal(
            user_id=identity.id,
            email=identity.email,
            display_name=identity.display_name,
            session_id=str(uuid.uuid4()),
            authenticated_at=datetime.now(UTC),
            platform_role_codes=(),
            tenant_memberships=(
                PrincipalMembership(
                    membership_id=membership.id,
                    tenant_id=tenant.id,
                    tenant_slug=tenant.slug,
                    status="active",
                    role_codes=(role,),
                ),
            ),
        )
        return tenant, store, principal


def service(db: Session, tenant: Tenant, store: Store, actor: int | None = None):
    return InstagramChannelService(
        db,
        tenant_id=tenant.id,
        store_id=store.id,
        tenant_status=tenant.status,
        store_status=store.status,
        actor_identity_id=actor,
    )


def add_principal(engine, tenant: Tenant, *, role: str | None):
    suffix = uuid.uuid4().hex[:10]
    with Session(engine, expire_on_commit=False) as db:
        identity = UserIdentity(
            email=f"{suffix}@example.test",
            normalized_email=f"{suffix}@example.test",
            display_name=f"User {suffix}",
            status="active",
        )
        db.add(identity)
        db.flush()
        membership = TenantMembership(
            user_id=identity.id,
            tenant_id=tenant.id,
            principal_type="user",
            principal_id=str(identity.id),
            status="active",
            all_store_access=True,
        )
        db.add(membership)
        db.flush()
        if role is not None:
            db.add(
                AuthTenantRoleAssignment(
                    membership_id=membership.id,
                    role_code=role,
                    status="active",
                )
            )
        db.commit()
        return AuthenticatedPrincipal(
            user_id=identity.id,
            email=identity.email,
            display_name=identity.display_name,
            session_id=str(uuid.uuid4()),
            authenticated_at=datetime.now(UTC),
            platform_role_codes=(),
            tenant_memberships=(
                PrincipalMembership(
                    membership_id=membership.id,
                    tenant_id=tenant.id,
                    tenant_slug=tenant.slug,
                    status="active",
                    role_codes=(role,) if role is not None else (),
                ),
            ),
        )


def create(service: InstagramChannelService, account: str) -> InstagramConnection:
    return service.create_connection(
        expected_revision=0,
        meta_app_id="app-1",
        facebook_page_id=f"page-{account}",
        instagram_account_id=account,
        instagram_username="store",
        external_account_name="Store Account",
    )


def test_connection_lifecycle_token_encryption_and_audit_redaction(
    channel_engine,
) -> None:
    tenant, store, principal = tenant_context(channel_engine)
    secret_token = "meta-token-that-must-never-leak"
    cipher = FernetTokenCipher(Fernet.generate_key().decode())
    with Session(channel_engine, expire_on_commit=False) as db:
        item = create(service(db, tenant, store, principal.user_id), f"ig-{uuid.uuid4()}")
        assert item.status == "pending"
        item = service(db, tenant, store, principal.user_id).update_connection(
            item.public_id,
            expected_revision=item.revision,
            changes={"instagram_username": "updated-store"},
        )
        with pytest.raises(InstagramChannelStaleWriteError):
            service(db, tenant, store).update_connection(
                item.public_id,
                expected_revision=1,
                changes={"instagram_username": "stale"},
            )
        item = service(db, tenant, store, principal.user_id).rotate_token(
            item.public_id,
            expected_revision=item.revision,
            access_token=secret_token,
            token_type="bearer",
            token_expires_at=None,
            scopes=["instagram_business_basic"],
            cipher=cipher,
        )
        assert item.encrypted_access_token != secret_token
        assert cipher.decrypt(item.encrypted_access_token) == secret_token
        public = connection_to_public(item)
        assert public["token_configured"] is True
        assert secret_token not in str(public)
        assert "encrypted_access_token" not in public
        item = service(db, tenant, store, principal.user_id).activate(
            item.public_id,
            expected_revision=item.revision,
            reason=None,
        )
        assert item.status == "active"
        with pytest.raises(InstagramChannelInvalidTransitionError):
            service(db, tenant, store).activate(
                item.public_id,
                expected_revision=item.revision,
                reason=None,
            )
        item = service(db, tenant, store, principal.user_id).disconnect(
            item.public_id,
            expected_revision=item.revision,
            reason="operator request",
        )
        item = service(db, tenant, store, principal.user_id).archive(
            item.public_id,
            expected_revision=item.revision,
            reason="retired",
        )
        assert item.status == "archived"
        with pytest.raises(InstagramChannelConflictError):
            service(db, tenant, store).update_connection(
                item.public_id,
                expected_revision=item.revision,
                changes={"instagram_username": "blocked"},
            )
        audits = list(
            db.scalars(
                select(TenantAuditLog).where(TenantAuditLog.store_id == store.id)
            ).all()
        )
        assert {
            "instagram.connection.created",
            "instagram.connection.updated",
            "instagram.connection.credential_rotated",
            "instagram.connection.activated",
            "instagram.connection.disconnected",
            "instagram.connection.archived",
        }.issubset({audit.action for audit in audits})
        assert secret_token not in str([audit.details_json for audit in audits])
        assert item.encrypted_access_token not in str(
            [audit.details_json for audit in audits]
        )


def test_unique_store_and_account_constraints_are_safe_conflicts(channel_engine) -> None:
    tenant, store, _ = tenant_context(channel_engine)
    account = f"ig-{uuid.uuid4()}"
    with Session(channel_engine) as db:
        create(service(db, tenant, store), account)
        with pytest.raises(InstagramChannelConflictError):
            create(service(db, tenant, store), f"other-{uuid.uuid4()}")
    other_tenant, other_store, _ = tenant_context(channel_engine)
    with Session(channel_engine) as db:
        with pytest.raises(InstagramChannelConflictError):
            create(service(db, other_tenant, other_store), account)


def test_service_scope_never_returns_another_tenants_connection(channel_engine) -> None:
    first_tenant, first_store, _ = tenant_context(channel_engine)
    second_tenant, second_store, _ = tenant_context(channel_engine)
    with Session(channel_engine) as db:
        item = create(
            service(db, first_tenant, first_store), f"ig-{uuid.uuid4()}"
        )
        with pytest.raises(InstagramChannelNotFoundError):
            service(db, second_tenant, second_store).get_connection(item.public_id)


def api_client(
    engine,
    principal: AuthenticatedPrincipal,
    settings: Settings,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def database_override():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = database_override
    app.dependency_overrides[require_authenticated_principal] = lambda: principal
    app.dependency_overrides[get_settings] = lambda: settings
    return TestClient(app)


def test_management_api_uses_public_ids_permissions_and_safe_responses(
    channel_engine,
) -> None:
    tenant, store, owner = tenant_context(channel_engine, role="tenant_owner")
    settings = Settings(
        instagram_token_encryption_key=Fernet.generate_key().decode()
    )
    client = api_client(channel_engine, owner, settings)
    base = (
        f"/api/v1/tenants/{tenant.public_id}/stores/{store.public_id}"
        "/instagram-channel"
    )
    created = client.post(
        f"{base}/connections",
        json={
            "expected_revision": 0,
            "instagram_account_id": f"ig-{uuid.uuid4()}",
            "facebook_page_id": f"page-{uuid.uuid4()}",
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert "id" not in body
    assert "encrypted_access_token" not in body
    assert "access_token" not in body
    connection_id = body["public_id"]
    token = "never-return-this-token"
    rotated = client.post(
        f"{base}/connections/{connection_id}/token",
        json={
            "expected_revision": body["revision"],
            "access_token": token,
            "token_type": "bearer",
            "scopes": ["instagram_business_basic"],
        },
    )
    assert rotated.status_code == 200
    assert token not in rotated.text
    listed = client.get(f"{base}/connections?page=1&page_size=10")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    content_manager = add_principal(
        channel_engine, tenant, role="tenant_content_manager"
    )
    content_client = api_client(channel_engine, content_manager, settings)
    assert content_client.get(f"{base}/connections/{connection_id}").status_code == 200
    denied_mutation = content_client.post(
        f"{base}/connections",
        json={
            "expected_revision": 0,
            "instagram_account_id": f"ig-{uuid.uuid4()}",
        },
    )
    assert denied_mutation.status_code == 404

    operator = add_principal(channel_engine, tenant, role="tenant_operator")
    operator_client = api_client(channel_engine, operator, settings)
    denied_credential = operator_client.post(
        f"{base}/connections/{connection_id}/token",
        json={
            "expected_revision": rotated.json()["revision"],
            "access_token": "must-not-be-accepted",
            "scopes": [],
        },
    )
    assert denied_credential.status_code == 404

    no_role = add_principal(channel_engine, tenant, role=None)
    no_role_client = api_client(channel_engine, no_role, settings)
    assert no_role_client.get(f"{base}/connections").status_code == 404

    _, _, other_tenant_owner = tenant_context(
        channel_engine, role="tenant_owner"
    )
    hidden = api_client(
        channel_engine, other_tenant_owner, settings
    ).get(f"{base}/connections/{connection_id}")
    assert hidden.status_code == 404


def test_credential_permission_is_not_implied_by_general_manage(channel_engine) -> None:
    role = ROLE_BY_CODE["tenant_operator"]
    assert PermissionCode.INSTAGRAM_CONNECTION_MANAGE in role.permission_codes
    assert (
        PermissionCode.INSTAGRAM_CONNECTION_CREDENTIALS_MANAGE
        not in role.permission_codes
    )
    assert (
        PermissionCode.INSTAGRAM_CONNECTION_CREDENTIALS_MANAGE
        in ROLE_BY_CODE["store_manager"].permission_codes
    )
