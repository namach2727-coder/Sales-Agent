from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal, PrincipalMembership
from app.authz.context import PrincipalType
from app.models import (
    AuthRole,
    Store,
    StoreAccessAssignment,
    Tenant,
    TenantAuditLog,
    TenantMembership,
    UserIdentity,
)
from app.tenant_management.context import resolve_authorized_context, store_by_domain
from app.tenant_management.domain import (
    AccessDeniedError,
    InvalidTransitionError,
    ResourceNotFoundError,
    ValidationError,
    normalize_custom_domain,
    normalize_subdomain,
)
from app.tenant_management.service import TenantStoreService
from tools.seeding import SeedRunner, default_registry
from app.database import Base


@pytest.fixture()
def tenant_engine(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'tenant-store.db').as_posix()}")
    Base.metadata.create_all(engine)
    SeedRunner(engine, default_registry()).run("production")
    yield engine
    engine.dispose()


def identity(session: Session, email: str) -> UserIdentity:
    item = UserIdentity(
        email=email,
        normalized_email=email.casefold(),
        display_name=email.split("@", 1)[0],
        status="active",
        email_verified=True,
    )
    session.add(item)
    session.commit()
    return item


def principal(user: UserIdentity, membership: TenantMembership | None = None) -> AuthenticatedPrincipal:
    memberships = () if membership is None else (
        PrincipalMembership(
            membership_id=membership.id,
            tenant_id=membership.tenant_id,
            tenant_slug=membership.tenant.slug,
            status=membership.status,
            role_codes=(),
        ),
    )
    return AuthenticatedPrincipal(
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
        session_id="test-session",
        authenticated_at=datetime.now(UTC),
        platform_role_codes=(),
        tenant_memberships=memberships,
    )


def bootstrap(session: Session, owner: UserIdentity, slug: str = "alpha"):
    return TenantStoreService(session, actor_identity_id=owner.id).bootstrap(
        tenant_name="Alpha Commerce",
        tenant_slug=slug,
        store_name="Alpha Main Store",
        store_slug="main",
        owner_identity=owner,
    )


def test_domain_and_subdomain_normalization() -> None:
    assert normalize_subdomain("  Shop-One. ") == "shop-one"
    assert normalize_custom_domain("Store.Example.COM.") == "store.example.com"
    with pytest.raises(ValidationError):
        normalize_subdomain("admin")
    with pytest.raises(ValidationError):
        normalize_custom_domain("https://example.com/path")


def test_bootstrap_is_atomic_and_audited(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "owner@example.invalid")
        tenant, store, membership = bootstrap(session, owner)
        assert tenant.status == store.status == membership.status == "active"
        assert store.tenant_id == tenant.id
        assert membership.tenant_id == tenant.id
        assert membership.public_id and membership.public_id != str(membership.id)
        assert membership.all_store_access is True
        assert session.scalar(select(StoreAccessAssignment.id).where(StoreAccessAssignment.membership_id == membership.id))
        actions = set(session.scalars(select(TenantAuditLog.action).where(TenantAuditLog.tenant_id == tenant.id)).all())
        assert {"tenant.bootstrap", "store.created", "membership.created"} <= actions


def test_bootstrap_rolls_back_if_required_role_is_missing(tenant_engine) -> None:
    with Session(tenant_engine) as session:
        owner = identity(session, "rollback@example.invalid")
        session.query(AuthRole).filter(AuthRole.code == "tenant_owner").delete()
        session.commit()
        with pytest.raises(ValidationError):
            bootstrap(session, owner, "rollback-tenant")
        assert session.scalar(select(Tenant.id).where(Tenant.slug == "rollback-tenant")) is None


def test_tenant_lifecycle_and_invalid_archive_reactivation(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "lifecycle@example.invalid")
        tenant, _, _ = bootstrap(session, owner)
        service = TenantStoreService(session, actor_identity_id=owner.id)
        assert service.transition_tenant(tenant, "suspended").suspended_at is not None
        assert service.transition_tenant(tenant, "active").status == "active"
        assert service.transition_tenant(tenant, "archived").archived_at is not None
        with pytest.raises(InvalidTransitionError):
            service.transition_tenant(tenant, "active")


def test_store_lifecycle_is_blocked_by_suspended_tenant(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "store-life@example.invalid")
        tenant, store, _ = bootstrap(session, owner)
        service = TenantStoreService(session, actor_identity_id=owner.id)
        service.transition_tenant(tenant, "suspended")
        service.transition_store(tenant, store, "suspended")
        with pytest.raises(InvalidTransitionError):
            service.transition_store(tenant, store, "active")
        with pytest.raises(InvalidTransitionError):
            service.create_store(tenant, name="Blocked Store", slug="blocked")


def test_store_slug_is_scoped_but_domains_are_globally_unique(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        first = identity(session, "first@example.invalid")
        tenant_a, _, _ = bootstrap(session, first, "tenant-a")
        second = identity(session, "second@example.invalid")
        tenant_b, _, _ = bootstrap(session, second, "tenant-b")
        service = TenantStoreService(session, actor_identity_id=first.id)
        store_a = service.create_store(tenant_a, name="Shared A", slug="shared", subdomain="unique-a")
        store_b = service.create_store(tenant_b, name="Shared B", slug="shared", subdomain="unique-b")
        assert store_a.slug == store_b.slug
        duplicate = Store(tenant=tenant_b, name="Duplicate", slug="other", status="active", subdomain="unique-a")
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_explicit_store_assignment_enforces_cross_store_isolation(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "isolation-owner@example.invalid")
        tenant, first_store, _ = bootstrap(session, owner)
        service = TenantStoreService(session, actor_identity_id=owner.id)
        second_store = service.create_store(tenant, name="Second Store", slug="second")
        manager = identity(session, "manager@example.invalid")
        membership = service.add_membership(
            tenant,
            manager,
            role_codes=("store_manager",),
            stores=(first_store,),
        )
        manager_principal = principal(manager, membership)
        allowed = resolve_authorized_context(
            session,
            manager_principal,
            tenant_public_id=tenant.public_id,
            store_public_id=first_store.public_id,
        )
        assert allowed.store_id == first_store.id
        with pytest.raises(ResourceNotFoundError):
            resolve_authorized_context(
                session,
                manager_principal,
                tenant_public_id=tenant.public_id,
                store_public_id=second_store.public_id,
            )


def test_cross_tenant_public_id_guess_is_not_authorized(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner_a = identity(session, "a@example.invalid")
        tenant_a, _, membership_a = bootstrap(session, owner_a, "alpha-one")
        owner_b = identity(session, "b@example.invalid")
        tenant_b, _, _ = bootstrap(session, owner_b, "beta-two")
        with pytest.raises(ResourceNotFoundError):
            resolve_authorized_context(
                session,
                principal(owner_a, membership_a),
                tenant_public_id=tenant_b.public_id,
            )
        assert tenant_a.public_id != tenant_b.public_id


def test_suspended_scope_rejects_operational_context(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "suspended@example.invalid")
        tenant, store, membership = bootstrap(session, owner)
        TenantStoreService(session, actor_identity_id=owner.id).transition_tenant(tenant, "suspended")
        with pytest.raises(AccessDeniedError):
            resolve_authorized_context(
                session,
                principal(owner, membership),
                tenant_public_id=tenant.public_id,
                store_public_id=store.public_id,
            )


def test_domain_lookup_returns_only_active_store(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "domain@example.invalid")
        tenant, _, _ = bootstrap(session, owner)
        store = TenantStoreService(session, actor_identity_id=owner.id).create_store(
            tenant,
            name="Domain Store",
            slug="domain-store",
            custom_domain="shop.example.com",
        )
        assert store_by_domain(session, "SHOP.EXAMPLE.COM.").id == store.id
        TenantStoreService(session, actor_identity_id=owner.id).transition_store(tenant, store, "suspended")
        assert store_by_domain(session, "shop.example.com") is None


def test_membership_suspension_and_revocation_are_audited(tenant_engine) -> None:
    with Session(tenant_engine, expire_on_commit=False) as session:
        owner = identity(session, "member-owner@example.invalid")
        tenant, store, _ = bootstrap(session, owner)
        user = identity(session, "member@example.invalid")
        service = TenantStoreService(session, actor_identity_id=owner.id)
        membership = service.add_membership(tenant, user, role_codes=("read_only",), stores=(store,))
        assert service.transition_membership(tenant, membership, "suspended").suspended_at
        assert service.transition_membership(tenant, membership, "revoked").revoked_at
        with pytest.raises(InvalidTransitionError):
            service.transition_membership(tenant, membership, "active")
        actions = set(session.scalars(select(TenantAuditLog.action).where(TenantAuditLog.tenant_id == tenant.id)).all())
        assert {"membership.created", "membership.suspended", "membership.revoked"} <= actions
