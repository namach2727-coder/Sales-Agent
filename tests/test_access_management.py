from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, func, inspect, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authz import (
    AccessValidationError,
    AuthorizationPrincipal,
    PermissionDeniedError,
    PrincipalType,
    RoleAssignmentService,
)
from app.authz.dependencies import local_provider_admin_principal
from app.models import (
    AuthAuditLog,
    AuthPlatformRoleAssignment,
    AuthTenantRoleAssignment,
    Store,
    TenantMembership,
)
from tools import manage_access
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


def _config(path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    return config


@pytest.fixture
def access_engine(tmp_path: Path) -> Engine:
    path = tmp_path / "access.db"
    command.upgrade(_config(path), "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    yield engine
    engine.dispose()


def _store(engine: Engine, slug: str) -> int:
    with Session(engine) as session, session.begin():
        store = Store(name=slug.title(), slug=slug, status="active")
        session.add(store)
        session.flush()
        return store.id


def _service(engine: Engine, actor=None):
    session = Session(engine, expire_on_commit=False)
    return session, RoleAssignmentService(
        session, actor or local_provider_admin_principal()
    )


def test_platform_assignment_is_idempotent_audited_and_revocable(
    access_engine: Engine,
) -> None:
    session, service = _service(access_engine)
    try:
        first = service.assign_role(
            principal_type="user",
            principal_id="operator-1",
            role_code="platform_operator",
        )
        second = service.assign_role(
            principal_type="user",
            principal_id="operator-1",
            role_code="platform_operator",
        )
        revoked = service.revoke_role(
            principal_type="user",
            principal_id="operator-1",
            role_code="platform_operator",
        )
    finally:
        session.close()
    assert first.changed is True
    assert second.changed is False
    assert revoked.changed is True and revoked.status == "revoked"
    with Session(access_engine) as session:
        assignment = session.scalar(select(AuthPlatformRoleAssignment))
        assert assignment.status == "revoked"
        audits = list(session.scalars(select(AuthAuditLog).order_by(AuthAuditLog.id)))
        assert [item.outcome for item in audits] == ["succeeded", "unchanged", "succeeded"]
        assert all(item.actor_principal_id == "local-provider-admin" for item in audits)


def test_tenant_assignment_creates_explicit_membership_and_role(
    access_engine: Engine,
) -> None:
    tenant_id = _store(access_engine, "alpha")
    session, service = _service(access_engine)
    try:
        result = service.assign_role(
            principal_type="user",
            principal_id="tenant-user",
            role_code="tenant_admin",
            tenant_id=tenant_id,
        )
    finally:
        session.close()
    assert result.tenant_id == tenant_id and result.changed is True
    with Session(access_engine) as session:
        membership = session.scalar(select(TenantMembership))
        assignment = session.scalar(select(AuthTenantRoleAssignment))
        assert membership.tenant_id == tenant_id
        assert membership.principal_id == "tenant-user"
        assert assignment.membership_id == membership.id
        assert assignment.role_code == "tenant_admin"


def test_role_scope_requires_or_rejects_tenant(access_engine: Engine) -> None:
    tenant_id = _store(access_engine, "alpha")
    session, service = _service(access_engine)
    try:
        with pytest.raises(AccessValidationError, match="cannot include a tenant"):
            service.assign_role(
                principal_type="user",
                principal_id="user-1",
                role_code="platform_operator",
                tenant_id=tenant_id,
            )
        with pytest.raises(AccessValidationError, match="requires an explicit tenant"):
            service.assign_role(
                principal_type="user",
                principal_id="user-1",
                role_code="tenant_admin",
            )
    finally:
        session.close()


def test_tenant_admin_cannot_assign_role_in_another_tenant(
    access_engine: Engine,
) -> None:
    alpha_id = _store(access_engine, "alpha")
    beta_id = _store(access_engine, "beta")
    session, bootstrap = _service(access_engine)
    try:
        bootstrap.assign_role(
            principal_type="user",
            principal_id="alpha-admin",
            role_code="tenant_admin",
            tenant_id=alpha_id,
        )
    finally:
        session.close()
    actor = AuthorizationPrincipal(
        "alpha-admin", PrincipalType.USER, True, tenant_id=alpha_id
    )
    session, service = _service(access_engine, actor)
    try:
        with pytest.raises(PermissionDeniedError):
            service.assign_role(
                principal_type="user",
                principal_id="beta-user",
                role_code="tenant_viewer",
                tenant_id=beta_id,
            )
    finally:
        session.close()
    with Session(access_engine) as session:
        assert session.scalar(
            select(func.count()).select_from(TenantMembership).where(
                TenantMembership.tenant_id == beta_id
            )
        ) == 0


def test_database_unique_constraint_prevents_duplicate_assignments(
    access_engine: Engine,
) -> None:
    with Session(access_engine) as session:
        session.add_all(
            [
                AuthPlatformRoleAssignment(
                    principal_type="user",
                    principal_id="duplicate",
                    role_code="platform_operator",
                    status="active",
                ),
                AuthPlatformRoleAssignment(
                    principal_type="user",
                    principal_id="duplicate",
                    role_code="platform_operator",
                    status="active",
                ),
            ]
        )
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()


def test_audit_failure_rolls_back_assignment(access_engine: Engine) -> None:
    def fail_audit(session, record) -> None:
        raise RuntimeError("injected audit failure")

    with Session(access_engine) as session:
        service = RoleAssignmentService(
            session,
            local_provider_admin_principal(),
            audit_writer=fail_audit,
        )
        with pytest.raises(RuntimeError, match="injected audit failure"):
            service.assign_role(
                principal_type="user",
                principal_id="rollback-user",
                role_code="platform_operator",
            )
    with Session(access_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthPlatformRoleAssignment)) == 0
        assert session.scalar(select(func.count()).select_from(AuthAuditLog)) == 0


def test_permission_lookup_failure_rolls_back_membership(
    access_engine: Engine, monkeypatch
) -> None:
    tenant_id = _store(access_engine, "alpha")

    def fail_require(*args, **kwargs):
        raise RuntimeError("injected lookup failure")

    monkeypatch.setattr("app.authz.access.AuthorizationService.require", fail_require)
    with Session(access_engine) as session:
        service = RoleAssignmentService(session, local_provider_admin_principal())
        with pytest.raises(RuntimeError, match="injected lookup failure"):
            service.assign_role(
                principal_type="user",
                principal_id="rollback-user",
                role_code="tenant_viewer",
                tenant_id=tenant_id,
            )
    with Session(access_engine) as session:
        assert session.scalar(select(func.count()).select_from(TenantMembership)) == 0


def test_cli_lists_assigns_revokes_and_shows_effective_permissions(
    access_engine: Engine, capsys
) -> None:
    tenant_id = _store(access_engine, "demo-store")
    url = str(access_engine.url)
    assert manage_access.main(["list-permissions", "--database-url", url]) == 0
    assert "product.read" in capsys.readouterr().out
    assert manage_access.main(["list-roles", "--database-url", url, "--json"]) == 0
    assert "tenant_admin" in capsys.readouterr().out
    assignment = [
        "assign-role",
        "--principal-type", "user",
        "--principal-id", "cli-user",
        "--tenant", "demo-store",
        "--role", "tenant_viewer",
        "--database-url", url,
    ]
    assert manage_access.main(assignment) == 0
    assert manage_access.main(assignment) == 0
    assert manage_access.main([
        "show-effective-permissions",
        "--principal-type", "user",
        "--principal-id", "cli-user",
        "--tenant", "demo-store",
        "--database-url", url,
    ]) == 0
    assert "product.read" in capsys.readouterr().out
    revoke = assignment.copy()
    revoke[0] = "revoke-role"
    assert manage_access.main(revoke) == 0
    with Session(access_engine) as session:
        membership = session.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id))
        assignment_row = session.scalar(
            select(AuthTenantRoleAssignment).where(
                AuthTenantRoleAssignment.membership_id == membership.id
            )
        )
        assert assignment_row.status == "revoked"


def test_cli_validation_exit_codes_and_redaction(access_engine: Engine, capsys) -> None:
    url = str(access_engine.url)
    assert manage_access.main([
        "assign-role",
        "--principal-type", "user",
        "--principal-id", "user-1",
        "--role", "missing-role",
        "--database-url", url,
    ]) == 2
    assert manage_access.main([
        "assign-role",
        "--principal-type", "user",
        "--principal-id", "user-1",
        "--tenant", "missing-store",
        "--role", "tenant_viewer",
        "--database-url", url,
    ]) == 2
    secret = "must-not-appear"
    assert manage_access.main([
        "list-roles",
        "--database-url", f"postgresql://user:{secret}@127.0.0.1:1/database",
    ]) == 1
    assert secret not in capsys.readouterr().out


def test_authorization_migration_downgrade_and_upgrade_round_trip(
    access_engine: Engine,
) -> None:
    path = Path(access_engine.url.database)
    access_engine.dispose()
    config = _config(path)
    command.downgrade(config, "0002_create_seed_history")
    downgraded = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        tables = set(inspect(downgraded).get_table_names())
        assert "auth_permissions" not in tables
        assert "tenant_memberships" not in tables
    finally:
        downgraded.dispose()
    command.upgrade(config, "head")
    upgraded = create_engine(f"sqlite:///{path.as_posix()}")
    try:
        tables = set(inspect(upgraded).get_table_names())
        assert "auth_permissions" in tables
        assert "tenant_memberships" in tables
    finally:
        upgraded.dispose()
