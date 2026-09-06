import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.catalog_training import ensure_default_store
from app.database import Base, get_db
from app.main import app, settings
from app.module_catalog import MODULE_SEEDS, ensure_store_modules
from app.tenancy import normalize_store_slug, parse_tenant_slug


LOCAL_ORIGIN = "http://127.0.0.1:8000"
MUTATION_HEADERS = {"origin": LOCAL_ORIGIN, "sec-fetch-site": "same-origin"}


@pytest.fixture
def module_client(monkeypatch):
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=test_engine)
    with TestSession() as db:
        store = ensure_default_store(db)
        ensure_store_modules(db, store, activate_legacy_defaults=True)
        db.commit()

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(settings, "app_env", "development")
    monkeypatch.setattr(settings, "tenant_base_domain", "agent.example.test")
    monkeypatch.setattr(settings, "tenant_url_scheme", "https")
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(
            app,
            base_url=LOCAL_ORIGIN,
            client=("127.0.0.1", 51000),
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


def test_legacy_store_gets_separately_priced_default_modules(module_client) -> None:
    response = module_client.get("/admin/api/module-marketplace")

    assert response.status_code == 200
    payload = response.json()
    assert payload["store"]["subdomain"] == "default.agent.example.test"
    assert len(payload["modules"]) == len(MODULE_SEEDS)
    modules = {item["code"]: item for item in payload["modules"]}
    assert modules["sales_agent_core"]["enabled"] is True
    assert modules["comments_to_dm"]["enabled"] is True
    assert modules["content_strategy"]["enabled"] is True
    assert modules["instagram_publish"]["enabled"] is False
    assert modules["receipt_review"]["availability"] == "beta"
    assert modules["analytics"]["availability"] == "planned"
    assert payload["monthly_total_irr"] == sum(
        item["monthly_price_irr"] for item in payload["modules"] if item["enabled"]
    )


def test_provider_creates_store_and_activates_dependent_modules(module_client) -> None:
    created = module_client.post(
        "/admin/api/provider/stores",
        json={"name": "فروشگاه آفتاب", "slug": "aftab"},
        headers=MUTATION_HEADERS,
    )
    assert created.status_code == 200, created.text
    payload = created.json()
    assert payload["store"]["subdomain"] == "aftab.agent.example.test"
    assert all(item["enabled"] is False for item in payload["modules"])

    missing_dependency = module_client.patch(
        "/admin/api/provider/stores/aftab/modules/comments_to_dm",
        json={"status": "active"},
        headers=MUTATION_HEADERS,
    )
    assert missing_dependency.status_code == 409

    core = module_client.patch(
        "/admin/api/provider/stores/aftab/modules/sales_agent_core",
        json={"status": "active"},
        headers=MUTATION_HEADERS,
    )
    assert core.status_code == 200
    comment_trial = module_client.patch(
        "/admin/api/provider/stores/aftab/modules/comments_to_dm",
        json={"status": "trial", "trial_days": 14},
        headers=MUTATION_HEADERS,
    )
    assert comment_trial.status_code == 200, comment_trial.text
    modules = {item["code"]: item for item in comment_trial.json()["modules"]}
    assert modules["sales_agent_core"]["enabled"] is True
    assert modules["comments_to_dm"]["enabled"] is True
    assert modules["comments_to_dm"]["trial_ends_at"] is not None


def test_provider_store_endpoint_delegates_to_provisioning_service(
    module_client, monkeypatch
) -> None:
    from app.provisioning.service import TenantProvisioningService

    calls: list[str] = []
    original = TenantProvisioningService.provision

    def observed(self, request, *, dry_run=False):
        calls.append(request.slug)
        return original(self, request, dry_run=dry_run)

    monkeypatch.setattr(TenantProvisioningService, "provision", observed)
    response = module_client.post(
        "/admin/api/provider/stores",
        json={"name": "Delegated Store", "slug": "delegated-store"},
        headers=MUTATION_HEADERS,
    )
    assert response.status_code == 200, response.text
    assert calls == ["delegated-store"]


def test_high_risk_provider_routes_require_explicit_rbac_permissions(
    module_client, monkeypatch
) -> None:
    from app.authz.context import AuthorizationPrincipal, PrincipalType
    from app.authz import dependencies

    monkeypatch.setattr(
        dependencies,
        "local_provider_admin_principal",
        lambda: AuthorizationPrincipal(
            "authenticated-without-role",
            PrincipalType.PROVIDER_ADMIN,
            True,
        ),
    )
    create = module_client.post(
        "/admin/api/provider/stores",
        json={"name": "Denied Store", "slug": "denied-store"},
        headers=MUTATION_HEADERS,
    )
    catalog = module_client.patch(
        "/admin/api/provider/module-catalog/content_strategy",
        json={"monthly_price_irr": 1, "setup_price_irr": 0},
        headers=MUTATION_HEADERS,
    )
    entitlement = module_client.patch(
        "/admin/api/provider/stores/default/modules/sales_agent_core",
        json={"status": "inactive"},
        headers=MUTATION_HEADERS,
    )
    assert create.status_code == 403
    assert catalog.status_code == 403
    assert entitlement.status_code == 403
    assert create.json() == catalog.json() == entitlement.json() == {
        "detail": "Permission denied"
    }


def test_provider_can_edit_sample_price_and_slugs_are_validated(module_client) -> None:
    changed = module_client.patch(
        "/admin/api/provider/module-catalog/content_strategy",
        json={"monthly_price_irr": 7_500_000, "setup_price_irr": 2_000_000},
        headers=MUTATION_HEADERS,
    )
    assert changed.status_code == 200
    assert changed.json()["monthly_price_irr"] == 7_500_000

    refreshed = module_client.get("/admin/api/module-marketplace").json()
    strategy = next(
        item for item in refreshed["modules"] if item["code"] == "content_strategy"
    )
    assert strategy["catalog_price_irr"] == 7_500_000

    reserved = module_client.post(
        "/admin/api/provider/stores",
        json={"name": "فروشگاه نامعتبر", "slug": "admin"},
        headers=MUTATION_HEADERS,
    )
    assert reserved.status_code == 422


def test_tenant_host_resolution_is_strict() -> None:
    development = Settings(
        app_env="development",
        tenant_base_domain="agent.example.test",
    )
    production = Settings(
        app_env="production",
        tenant_base_domain="agent.example.test",
    )

    assert parse_tenant_slug("127.0.0.1:8000", development) == "default"
    assert parse_tenant_slug("[::1]:8000", development) == "default"
    assert parse_tenant_slug("aftab.localhost:8000", development) == "aftab"
    assert parse_tenant_slug("aftab.agent.example.test", production) == "aftab"
    assert parse_tenant_slug("agent.example.test", production) is None
    assert parse_tenant_slug("deep.aftab.agent.example.test", production) is None
    with pytest.raises(ValueError):
        normalize_store_slug("admin")
