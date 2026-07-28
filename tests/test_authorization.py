from __future__ import annotations

from pathlib import Path
from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.authz import (
    AuthorizationContext,
    AuthorizationPrincipal,
    AuthorizationService,
    PermissionCode,
    PermissionRequirement,
    PermissionScope,
    PrincipalType,
    RoleAssignmentService,
)
from app.authz.dependencies import (
    get_current_authorization_principal,
    local_provider_admin_principal,
    require_permission,
)
from app.authz.permissions import (
    PERMISSION_BY_CODE,
    PERMISSION_DEFINITIONS,
    ROLE_DEFINITIONS,
    PermissionDefinition,
    RoleDefinition,
    validate_permission_catalog,
    validate_role_catalog,
)
from app.database import get_db
from app.models import (
    AuthPermission,
    AuthRole,
    AuthRolePermission,
    Store,
    TenantMembership,
)
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]


def _config(path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.attributes["database_url"] = f"sqlite:///{path.as_posix()}"
    return config


@pytest.fixture
def auth_engine(tmp_path: Path) -> Engine:
    path = tmp_path / "authorization.db"
    command.upgrade(_config(path), "head")
    engine = create_engine(f"sqlite:///{path.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    yield engine
    engine.dispose()


def _principal(subject_id: str = "user-1") -> AuthorizationPrincipal:
    return AuthorizationPrincipal(subject_id, PrincipalType.USER, True)


def _store(engine: Engine, slug: str) -> int:
    with Session(engine) as session, session.begin():
        store = Store(name=slug.title(), slug=slug, status="active")
        session.add(store)
        session.flush()
        return store.id


def _assign(
    engine: Engine,
    *,
    principal: AuthorizationPrincipal,
    role: str,
    tenant_id: int | None = None,
) -> None:
    with Session(engine) as session:
        RoleAssignmentService(session, local_provider_admin_principal()).assign_role(
            principal_type=principal.subject_type,
            principal_id=principal.subject_id or "",
            role_code=role,
            tenant_id=tenant_id,
        )


def test_permission_registry_rejects_duplicate_and_invalid_codes() -> None:
    valid = PermissionDefinition("sample.read", PermissionScope.PLATFORM, "Sample")
    with pytest.raises(ValueError, match="duplicate permission"):
        validate_permission_catalog((valid, valid))
    with pytest.raises(ValueError, match="invalid permission"):
        PermissionDefinition("Sample Read", PermissionScope.PLATFORM, "Invalid")


def test_role_registry_rejects_duplicates_and_scope_mismatch() -> None:
    role = RoleDefinition(
        "sample_reader",
        "Sample Reader",
        PermissionScope.PLATFORM,
        "Sample",
        (PermissionCode.TENANT_READ,),
    )
    with pytest.raises(ValueError, match="duplicate role"):
        validate_role_catalog((role, role), PERMISSION_BY_CODE)
    incompatible = RoleDefinition(
        "bad_scope",
        "Bad Scope",
        PermissionScope.PLATFORM,
        "Invalid",
        (PermissionCode.PRODUCT_READ,),
    )
    with pytest.raises(ValueError, match="incompatible permission"):
        validate_role_catalog((incompatible,), PERMISSION_BY_CODE)


def test_unknown_permission_and_anonymous_are_denied(auth_engine: Engine) -> None:
    with Session(auth_engine) as session:
        service = AuthorizationService(session)
        unknown = service.check(_principal(), PermissionRequirement("unknown.action"))
        anonymous = service.check(
            AuthorizationPrincipal.anonymous(),
            PermissionRequirement(PermissionCode.TENANT_READ),
        )
    assert unknown.allowed is False and unknown.reason_code == "unknown_permission"
    assert anonymous.allowed is False and anonymous.reason_code == "unauthenticated"


def test_authenticated_principal_without_role_is_denied(auth_engine: Engine) -> None:
    with Session(auth_engine) as session:
        decision = AuthorizationService(session).check(
            _principal(), PermissionRequirement(PermissionCode.TENANT_READ)
        )
    assert decision.allowed is False
    assert decision.reason_code == "permission_missing"


def test_explicit_platform_role_allows_only_its_permissions(auth_engine: Engine) -> None:
    principal = _principal("auditor")
    _assign(auth_engine, principal=principal, role="platform_auditor")
    with Session(auth_engine) as session:
        service = AuthorizationService(session)
        audit = service.check(
            principal, PermissionRequirement(PermissionCode.PLATFORM_AUDIT_READ)
        )
        manage = service.check(
            principal, PermissionRequirement(PermissionCode.MODULE_CATALOG_MANAGE)
        )
    assert audit.allowed is True
    assert manage.allowed is False


def test_missing_tenant_context_and_platform_role_do_not_imply_tenant_access(
    auth_engine: Engine,
) -> None:
    tenant_id = _store(auth_engine, "alpha")
    principal = _principal("platform-operator")
    _assign(auth_engine, principal=principal, role="platform_operator")
    with Session(auth_engine) as session:
        service = AuthorizationService(session)
        missing = service.check(
            principal, PermissionRequirement(PermissionCode.PRODUCT_READ)
        )
        explicit = service.check(
            principal,
            PermissionRequirement(PermissionCode.PRODUCT_READ),
            AuthorizationContext(tenant_id),
        )
    assert missing.reason_code == "tenant_context_missing"
    assert explicit.allowed is False and explicit.reason_code == "membership_missing"


def test_tenant_role_is_isolated_to_one_tenant(auth_engine: Engine) -> None:
    alpha_id = _store(auth_engine, "alpha")
    beta_id = _store(auth_engine, "beta")
    principal = _principal("viewer")
    _assign(auth_engine, principal=principal, role="tenant_viewer", tenant_id=alpha_id)
    with Session(auth_engine) as session:
        service = AuthorizationService(session)
        alpha = service.check(
            principal,
            PermissionRequirement(PermissionCode.PRODUCT_READ),
            AuthorizationContext(alpha_id),
        )
        beta = service.check(
            principal,
            PermissionRequirement(PermissionCode.PRODUCT_READ),
            AuthorizationContext(beta_id),
        )
    assert alpha.allowed is True
    assert beta.allowed is False and beta.reason_code == "membership_missing"


def test_principal_tenant_binding_rejects_cross_tenant_context(auth_engine: Engine) -> None:
    alpha_id = _store(auth_engine, "alpha")
    beta_id = _store(auth_engine, "beta")
    bound = AuthorizationPrincipal(
        "bound-user", PrincipalType.USER, True, tenant_id=alpha_id
    )
    _assign(auth_engine, principal=bound, role="tenant_viewer", tenant_id=alpha_id)
    with Session(auth_engine) as session:
        decision = AuthorizationService(session).check(
            bound,
            PermissionRequirement(PermissionCode.PRODUCT_READ),
            AuthorizationContext(beta_id),
        )
    assert decision.allowed is False and decision.reason_code == "cross_tenant_denied"


def test_disabled_membership_denies_access(auth_engine: Engine) -> None:
    tenant_id = _store(auth_engine, "alpha")
    principal = _principal("disabled-member")
    _assign(auth_engine, principal=principal, role="tenant_viewer", tenant_id=tenant_id)
    with Session(auth_engine) as session, session.begin():
        membership = session.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant_id,
                TenantMembership.principal_id == "disabled-member",
            )
        )
        membership.status = "disabled"
    with Session(auth_engine) as session:
        decision = AuthorizationService(session).check(
            principal,
            PermissionRequirement(PermissionCode.PRODUCT_READ),
            AuthorizationContext(tenant_id),
        )
    assert decision.allowed is False and decision.reason_code == "membership_inactive"


def test_super_admin_uses_explicit_finite_platform_grants(auth_engine: Engine) -> None:
    principal = local_provider_admin_principal()
    with Session(auth_engine) as session:
        service = AuthorizationService(session)
        platform = service.check(
            principal, PermissionRequirement(PermissionCode.TENANT_PROVISION)
        )
        tenant = service.check(
            principal,
            PermissionRequirement(PermissionCode.PRODUCT_MANAGE),
            AuthorizationContext(1),
        )
    assert platform.allowed is True
    assert "*" not in platform.effective_permissions
    assert tenant.allowed is False


def test_effective_permissions_are_sorted_and_deterministic(auth_engine: Engine) -> None:
    principal = _principal("operator")
    _assign(auth_engine, principal=principal, role="platform_operator")
    with Session(auth_engine) as session:
        first = AuthorizationService(session).effective_permissions(principal)
        second = AuthorizationService(session).effective_permissions(principal)
    assert first == second == tuple(sorted(first))
    assert PermissionCode.TENANT_PROVISION in first


def test_authorization_seed_is_idempotent_and_production_safe(auth_engine: Engine) -> None:
    runner = SeedRunner(auth_engine, default_registry())
    names = (
        "system.auth_permissions",
        "system.auth_roles",
        "system.auth_role_permissions",
    )
    report = runner.run("production", seed_names=names)
    assert all(result.status.value == "unchanged" for result in report.results)
    definitions = {item.name: item for item in default_registry().definitions()}
    assert all(definitions[name].production_safe for name in names)
    assert definitions["system.auth_permissions"].version == "4"
    assert definitions["system.auth_roles"].version == "2"
    assert definitions["system.auth_role_permissions"].version == "4"
    with Session(auth_engine) as session:
        assert session.scalar(select(func.count()).select_from(AuthPermission)) == len(PERMISSION_DEFINITIONS)
        assert session.scalar(select(func.count()).select_from(AuthRole)) == len(ROLE_DEFINITIONS)
        expected = sum(len(role.permission_codes) for role in ROLE_DEFINITIONS)
        assert session.scalar(select(func.count()).select_from(AuthRolePermission)) == expected


def test_fastapi_guard_returns_401_403_and_success(auth_engine: Engine) -> None:
    api = FastAPI()

    @api.get("/protected")
    def protected(
        _principal: AuthorizationPrincipal = Depends(
            require_permission(PermissionCode.PLATFORM_AUDIT_READ)
        ),
    ) -> dict[str, bool]:
        return {"ok": True}

    def override_db():
        with Session(auth_engine) as session:
            yield session

    api.dependency_overrides[get_db] = override_db
    with TestClient(api) as client:
        assert client.get("/protected").status_code == 401
        api.dependency_overrides[get_current_authorization_principal] = lambda: _principal("no-role")
        assert client.get("/protected").status_code == 403
        auditor = _principal("http-auditor")
        _assign(auth_engine, principal=auditor, role="platform_auditor")
        api.dependency_overrides[get_current_authorization_principal] = lambda: auditor
        assert client.get("/protected").json() == {"ok": True}
