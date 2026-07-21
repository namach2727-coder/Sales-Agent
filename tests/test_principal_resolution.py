from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher, Type
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService
from app.authz import (
    AuthorizationContext,
    AuthorizationService,
    PermissionCode,
    PermissionRequirement,
    RoleAssignmentService,
)
from app.authz.dependencies import local_provider_admin_principal
from app.models import AuthTenantRoleAssignment, Store, TenantMembership
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def principal_engine(tmp_path: Path):
    path = tmp_path / "principal.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    yield engine
    engine.dispose()


@pytest.fixture
def passwords() -> PasswordService:
    return PasswordService(
        hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID)
    )


def bootstrap(engine, passwords):
    with Session(engine, expire_on_commit=False) as db:
        user = AuthenticationService(db, password_service=passwords).create_user(
            email="principal@example.com",
            display_name="Principal",
            password="correct horse battery staple",
        )
    with Session(engine, expire_on_commit=False) as db, db.begin():
        store = Store(name="Alpha", slug="alpha", status="active")
        db.add(store)
        db.flush()
        store_id = store.id
    with Session(engine, expire_on_commit=False) as db:
        AuthenticationService(db, password_service=passwords).add_tenant_membership(
            user_id=user.id, tenant_id=store_id
        )
    with Session(engine, expire_on_commit=False) as db:
        access = RoleAssignmentService(db, local_provider_admin_principal())
        access.assign_role(
            principal_type="user",
            principal_id=str(user.id),
            role_code="platform_auditor",
        )
        access.assign_role(
            principal_type="user",
            principal_id=str(user.id),
            role_code="tenant_viewer",
            tenant_id=store_id,
        )
    with Session(engine, expire_on_commit=False) as db:
        credential = AuthenticationService(db, password_service=passwords).authenticate_password(
            email=user.email, password="correct horse battery staple"
        )
    return user, store_id, credential


def test_principal_resolves_platform_membership_and_tenant_roles(
    principal_engine, passwords
) -> None:
    user, store_id, credential = bootstrap(principal_engine, passwords)
    principal = credential.principal
    assert principal.user_id == user.id
    assert principal.platform_role_codes == ("platform_auditor",)
    membership = principal.tenant_memberships[0]
    assert membership.tenant_id == store_id
    assert membership.role_codes == ("tenant_viewer",)


def test_resolved_principal_integrates_with_rbac(principal_engine, passwords) -> None:
    _user, store_id, credential = bootstrap(principal_engine, passwords)
    with Session(principal_engine) as db:
        authz = AuthorizationService(db)
        assert authz.require(
            credential.principal.as_authorization_principal(),
            PermissionCode.PLATFORM_AUDIT_READ,
        ).allowed
        assert authz.require(
            credential.principal.as_authorization_principal(store_id),
            PermissionCode.PRODUCT_READ,
            tenant_id=store_id,
        ).allowed


def test_inactive_membership_and_role_assignment_are_not_effective(
    principal_engine, passwords
) -> None:
    user, store_id, credential = bootstrap(principal_engine, passwords)
    with Session(principal_engine) as db, db.begin():
        membership = db.scalar(
            select(TenantMembership).where(TenantMembership.user_id == user.id)
        )
        membership.status = "disabled"
        assignment = db.scalar(
            select(AuthTenantRoleAssignment).where(
                AuthTenantRoleAssignment.membership_id == membership.id
            )
        )
        assignment.status = "revoked"
    with Session(principal_engine, expire_on_commit=False) as db:
        resolved = AuthenticationService(db, password_service=passwords).resolve_session(
            credential.token
        )
    assert resolved.tenant_memberships == ()
    with Session(principal_engine) as db:
        decision = AuthorizationService(db).check(
            resolved.as_authorization_principal(store_id),
            PermissionRequirement(PermissionCode.PRODUCT_READ),
            AuthorizationContext(store_id),
        )
    assert decision.allowed is False
