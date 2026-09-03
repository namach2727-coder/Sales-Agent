from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import uuid

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.authentication.context import AuthenticatedPrincipal, PrincipalMembership
from app.authentication.dependencies import require_authenticated_principal
from app.authz.permissions import PermissionCode, ROLE_BY_CODE
from app.business_knowledge.domain import (
    BusinessKnowledgeConflictError,
    BusinessKnowledgeInvalidTransitionError,
    BusinessKnowledgeNotFoundError,
    BusinessKnowledgeStaleWriteError,
    BusinessKnowledgeStoreStateError,
    BusinessKnowledgeValidationError,
    normalize_keywords,
    normalize_phone,
    normalize_question,
    normalize_url,
)
from app.business_knowledge.models import (
    BusinessFAQ,
    BusinessKnowledgeEntry,
    BusinessPolicy,
    BusinessProfile,
)
from app.business_knowledge.router import router
from app.business_knowledge.schemas import (
    BusinessFAQCreate,
    BusinessFAQRead,
    BusinessKnowledgeEntryCreate,
    BusinessKnowledgeEntryRead,
    BusinessPolicyCreate,
    BusinessPolicyRead,
    BusinessProfileCreate,
    BusinessProfileRead,
)
from app.business_knowledge.service import (
    BusinessKnowledgePermissionError,
    BusinessKnowledgeService,
)
from app.database import get_db
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
TABLES = {
    "business_profiles",
    "business_policies",
    "business_faqs",
    "business_knowledge_entries",
}


@pytest.fixture(scope="module")
def knowledge_engine(tmp_path_factory):
    path = tmp_path_factory.mktemp("foundation07") / "knowledge.db"
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
    store_status: str = "active",
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
            name=f"Tenant {suffix}",
            slug=f"tenant-{suffix}",
            status="active",
        )
        db.add_all([identity, tenant])
        db.flush()
        store = Store(
            tenant_id=tenant.id,
            name="Main",
            slug="main",
            status=store_status,
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
        if role:
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
                    role_codes=(role,) if role else (),
                ),
            ),
        )
        return tenant, store, membership, principal


def service(db: Session, tenant: Tenant, store: Store, actor: int | None = None):
    return BusinessKnowledgeService(
        db,
        tenant_id=tenant.id,
        store_id=store.id,
        tenant_status=tenant.status,
        store_status=store.status,
        actor_identity_id=actor,
    )


def api_client(engine, principal: AuthenticatedPrincipal) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_authenticated_principal] = lambda: principal
    return TestClient(app)


def base_path(tenant: Tenant, store: Store) -> str:
    return (
        f"/api/v1/tenants/{tenant.public_id}/stores/{store.public_id}"
        "/business-knowledge"
    )


def test_domain_normalization_and_unsafe_input_rejection() -> None:
    question, normalized = normalize_question("  How   MUCH？ ")
    assert question == "How MUCH?"
    assert normalized == "how much?"
    assert normalize_keywords([" Phone ", "phone", "قاب"]) == ["Phone", "قاب"]
    assert normalize_phone("+۹۸ ۹۱۲-۱۲۳-۴۵۶۷") == "+989121234567"
    assert normalize_url("HTTPS://example.com/help") == "https://example.com/help"
    with pytest.raises(BusinessKnowledgeValidationError):
        normalize_keywords([str(index) for index in range(26)])
    with pytest.raises(BusinessKnowledgeValidationError):
        normalize_url("javascript:alert(1)")
    with pytest.raises(BusinessKnowledgeValidationError):
        normalize_question("<script>alert(1)</script>")


def test_profile_singleton_update_lifecycle_and_safe_audit(knowledge_engine) -> None:
    tenant, store, _membership, principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as db:
        manager = service(db, tenant, store, principal.user_id)
        profile = manager.create_profile(
            expected_revision=0,
            display_name="  فروشگاه   نمونه ",
            description="فروش تخصصی موبایل",
            support_email=" SALES@Example.COM ",
        )
        assert profile.display_name == "فروشگاه نمونه"
        assert profile.support_email == "sales@example.com"
        assert profile.status == "draft" and profile.revision == 1
        with pytest.raises(BusinessKnowledgeConflictError):
            manager.create_profile(expected_revision=0, display_name="Duplicate")
        profile = manager.update_profile(
            expected_revision=1,
            changes={"business_category": "  Mobile   Store  "},
        )
        assert profile.business_category == "Mobile Store"
        assert profile.revision == 2
        with pytest.raises(BusinessKnowledgeStaleWriteError):
            manager.update_profile(
                expected_revision=1,
                changes={"description": "stale"},
            )
        with pytest.raises(BusinessKnowledgePermissionError):
            manager.transition(
                BusinessProfile,
                None,
                expected_revision=2,
                target_status="published",
                publish_authorized=False,
            )
        profile = manager.transition(
            BusinessProfile,
            None,
            expected_revision=2,
            target_status="published",
            publish_authorized=True,
        )
        assert profile.status == "published"
        assert profile.published_at is not None and profile.archived_at is None
        with pytest.raises(BusinessKnowledgeConflictError):
            manager.update_profile(
                expected_revision=3,
                changes={"description": "not editable"},
            )
        profile = manager.transition(
            BusinessProfile,
            None,
            expected_revision=3,
            target_status="archived",
            publish_authorized=True,
        )
        assert profile.published_at is None and profile.archived_at is not None
        with pytest.raises(BusinessKnowledgeInvalidTransitionError):
            manager.transition(
                BusinessProfile,
                None,
                expected_revision=4,
                target_status="published",
                publish_authorized=True,
            )
        profile = manager.transition(
            BusinessProfile,
            None,
            expected_revision=4,
            target_status="draft",
            publish_authorized=True,
        )
        assert profile.published_at is None and profile.archived_at is None
        logs = list(
            db.scalars(
                select(TenantAuditLog).where(
                    TenantAuditLog.tenant_id == tenant.id,
                    TenantAuditLog.target_public_id == profile.public_id,
                )
            )
        )
        assert len(logs) == 5
        serialized = repr([item.details_json for item in logs])
        assert "فروش تخصصی موبایل" not in serialized


def test_policy_crud_filters_uniqueness_and_pagination(knowledge_engine) -> None:
    tenant, store, _membership, _principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as db:
        manager = service(db, tenant, store)
        shipping = manager.create_policy(
            expected_revision=0,
            code=" SHIPPING ",
            policy_type="shipping",
            title="  ارسال   سفارش ",
            content="ارسال در دو روز کاری",
            priority=20,
        )
        returns = manager.create_policy(
            expected_revision=0,
            code="returns",
            policy_type="returns",
            title="شرایط مرجوعی",
            content="تا هفت روز",
            priority=10,
        )
        assert shipping.code == "shipping"
        assert manager.get_policy(shipping.public_id).title == "ارسال سفارش"
        with pytest.raises(BusinessKnowledgeConflictError):
            manager.create_policy(
                expected_revision=0,
                code="shipping",
                policy_type="custom",
                title="Duplicate",
                content="Duplicate",
            )
        items, total = manager.list_policies(
            page=1,
            page_size=1,
            policy_type="returns",
            search="مرجوعی",
        )
        assert total == 1 and items[0].public_id == returns.public_id
        updated = manager.update_policy(
            shipping.public_id,
            expected_revision=1,
            changes={"title": "ارسال سریع", "priority": 5},
        )
        assert updated.title == "ارسال سریع" and updated.revision == 2


def test_faq_normalized_uniqueness_keywords_search_and_lifecycle(knowledge_engine) -> None:
    tenant, store, _membership, _principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as db:
        manager = service(db, tenant, store)
        faq = manager.create_faq(
            expected_revision=0,
            question="  قیمت   آیفون چقدر است؟ ",
            answer="قیمت روز در صفحه محصول درج شده است.",
            keywords=["آیفون", " IPHONE ", "iphone"],
            priority=1,
        )
        assert faq.keywords == ["آیفون", "IPHONE"]
        with pytest.raises(BusinessKnowledgeConflictError):
            manager.create_faq(
                expected_revision=0,
                question="قیمت آیفون چقدر است؟",
                answer="duplicate",
            )
        items, total = manager.list_faqs(page=1, page_size=10, search="آیفون")
        assert total == 1 and items[0].public_id == faq.public_id
        published = manager.transition(
            BusinessFAQ,
            faq.public_id,
            expected_revision=1,
            target_status="published",
            publish_authorized=True,
        )
        assert published.status == "published"
        with pytest.raises(BusinessKnowledgeConflictError):
            manager.update_faq(
                faq.public_id,
                expected_revision=2,
                changes={"answer": "cannot edit published"},
            )


def test_entry_types_slug_search_and_archival_visibility(knowledge_engine) -> None:
    tenant, store, _membership, _principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as db:
        manager = service(db, tenant, store)
        entry = manager.create_entry(
            expected_revision=0,
            slug="IPHONE-DELIVERY",
            entry_type="instruction",
            title="راهنمای ارسال آیفون",
            content="پس از تأیید سفارش، رنگ را دوباره بررسی کنید.",
            keywords=["iphone", "ارسال"],
        )
        assert entry.slug == "iphone-delivery"
        with pytest.raises(BusinessKnowledgeConflictError):
            manager.create_entry(
                expected_revision=0,
                slug="iphone-delivery",
                entry_type="fact",
                title="Duplicate",
                content="Duplicate",
            )
        items, total = manager.list_entries(
            page=1,
            page_size=10,
            entry_type="instruction",
            search="آیفون",
        )
        assert total == 1 and items[0].public_id == entry.public_id
        archived = manager.transition(
            BusinessKnowledgeEntry,
            entry.public_id,
            expected_revision=1,
            target_status="archived",
            publish_authorized=True,
        )
        assert archived.status == "archived"
        visible, total = manager.list_entries(page=1, page_size=10)
        assert visible == [] and total == 0
        archived_items, total = manager.list_entries(
            page=1,
            page_size=10,
            status="archived",
        )
        assert total == 1 and archived_items[0].public_id == entry.public_id


def test_cross_tenant_and_store_queries_use_safe_not_found(knowledge_engine) -> None:
    tenant, store, _membership, _principal = tenant_context(knowledge_engine)
    other_tenant, other_store, _membership, _principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as db:
        item = service(db, tenant, store).create_policy(
            expected_revision=0,
            code="privacy",
            policy_type="privacy",
            title="Privacy",
            content="We protect customer data.",
        )
        with pytest.raises(BusinessKnowledgeNotFoundError):
            service(db, other_tenant, other_store).get_policy(item.public_id)
        same_tenant_other_store = Store(
            tenant_id=tenant.id,
            name="Branch",
            slug=f"branch-{uuid.uuid4().hex[:8]}",
            status="active",
        )
        db.add(same_tenant_other_store)
        db.commit()
        with pytest.raises(BusinessKnowledgeNotFoundError):
            service(db, tenant, same_tenant_other_store).get_policy(item.public_id)


def test_store_state_policy_is_explicit(knowledge_engine) -> None:
    tenant, onboarding, _membership, _principal = tenant_context(
        knowledge_engine, store_status="onboarding"
    )
    with Session(knowledge_engine) as db:
        created = service(db, tenant, onboarding).create_entry(
            expected_revision=0,
            slug="onboarding-entry",
            entry_type="fact",
            title="Onboarding",
            content="Allowed",
        )
        assert service(db, tenant, onboarding).get_entry(created.public_id)
        onboarding.status = "suspended"
        assert service(db, tenant, onboarding).get_entry(created.public_id)
        with pytest.raises(BusinessKnowledgeStoreStateError):
            service(db, tenant, onboarding).create_entry(
                expected_revision=0,
                slug="suspended-entry",
                entry_type="fact",
                title="Denied",
                content="Denied",
            )
        onboarding.status = "archived"
        with pytest.raises(BusinessKnowledgeNotFoundError):
            service(db, tenant, onboarding).get_entry(created.public_id)


def test_database_constraints_enforce_tenant_and_value_integrity(knowledge_engine) -> None:
    tenant, store, _membership, _principal = tenant_context(knowledge_engine)
    other_tenant, _other_store, _membership, _principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as db:
        db.add(
            BusinessPolicy(
                tenant_id=other_tenant.id,
                store_id=store.id,
                code="cross-tenant",
                policy_type="shipping",
                title="Cross",
                content="Cross",
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
        db.add(
            BusinessKnowledgeEntry(
                tenant_id=tenant.id,
                store_id=store.id,
                slug="invalid-type",
                entry_type="unsupported",
                title="Invalid",
                content="Invalid",
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()
        db.add(
            BusinessFAQ(
                tenant_id=tenant.id,
                store_id=store.id,
                question="Invalid revision",
                normalized_question="invalid revision",
                answer="Invalid",
                revision=0,
            )
        )
        with pytest.raises(IntegrityError):
            db.flush()


def test_optimistic_concurrency_rejects_racing_writer(knowledge_engine) -> None:
    tenant, store, _membership, _principal = tenant_context(knowledge_engine)
    with Session(knowledge_engine) as setup:
        item = service(setup, tenant, store).create_policy(
            expected_revision=0,
            code="concurrency",
            policy_type="custom",
            title="Initial",
            content="Initial",
        )
        public_id = item.public_id
    first = Session(knowledge_engine)
    second = Session(knowledge_engine)
    try:
        one = service(first, tenant, store)
        two = service(second, tenant, store)
        one.get_policy(public_id)
        two.get_policy(public_id)
        one.update_policy(
            public_id,
            expected_revision=1,
            changes={"title": "First"},
        )
        with pytest.raises(BusinessKnowledgeStaleWriteError):
            two.update_policy(
                public_id,
                expected_revision=1,
                changes={"title": "Second"},
            )
        assert service(second, tenant, store).get_policy(public_id).title == "First"
    finally:
        first.close()
        second.close()


def test_permission_catalog_has_exact_required_role_mapping() -> None:
    required = {
        PermissionCode.BUSINESS_PROFILE_READ,
        PermissionCode.BUSINESS_PROFILE_MANAGE,
        PermissionCode.KNOWLEDGE_READ,
        PermissionCode.KNOWLEDGE_MANAGE,
        PermissionCode.KNOWLEDGE_PUBLISH,
    }
    read_only = {
        PermissionCode.BUSINESS_PROFILE_READ,
        PermissionCode.KNOWLEDGE_READ,
    }
    for role in ("tenant_owner", "tenant_admin", "tenant_content_manager", "store_manager"):
        assert required <= set(ROLE_BY_CODE[role].permission_codes)
    assert required - {PermissionCode.KNOWLEDGE_PUBLISH} <= set(
        ROLE_BY_CODE["tenant_operator"].permission_codes
    )
    assert PermissionCode.KNOWLEDGE_PUBLISH not in ROLE_BY_CODE[
        "tenant_operator"
    ].permission_codes
    for role in ("tenant_analyst", "tenant_viewer", "operator", "read_only"):
        assert read_only <= set(ROLE_BY_CODE[role].permission_codes)
        assert PermissionCode.KNOWLEDGE_MANAGE not in ROLE_BY_CODE[role].permission_codes
    assert all("*" not in role.permission_codes for role in ROLE_BY_CODE.values())


def test_public_schemas_exclude_internal_scope_and_actor_ids() -> None:
    schemas = (
        BusinessProfileCreate,
        BusinessProfileRead,
        BusinessPolicyCreate,
        BusinessPolicyRead,
        BusinessFAQCreate,
        BusinessFAQRead,
        BusinessKnowledgeEntryCreate,
        BusinessKnowledgeEntryRead,
    )
    forbidden = {
        "id",
        "tenant_id",
        "store_id",
        "created_by_identity_id",
        "published_by_identity_id",
    }
    for schema in schemas:
        assert forbidden.isdisjoint(schema.model_fields)


def test_api_contract_authorization_safe_404_and_no_delete(knowledge_engine) -> None:
    tenant, store, membership, principal = tenant_context(
        knowledge_engine,
        role="tenant_content_manager",
        all_store_access=False,
    )
    client = api_client(knowledge_engine, principal)
    path = base_path(tenant, store)
    response = client.post(
        f"{path}/profile",
        json={
            "expected_revision": 0,
            "display_name": "DirectPilot Shop",
            "description": "Mobile sales",
        },
    )
    assert response.status_code == 201
    assert {
        "id",
        "tenant_id",
        "store_id",
        "created_by_identity_id",
        "published_by_identity_id",
    }.isdisjoint(response.json())
    response = client.post(
        f"{path}/profile/transitions",
        json={"expected_revision": 1, "target_status": "published"},
    )
    assert response.status_code == 200 and response.json()["status"] == "published"
    assert client.get(f"{path}/profile").status_code == 200
    assert client.delete(f"{path}/profile").status_code == 405

    with Session(knowledge_engine, expire_on_commit=False) as db:
        unassigned = Store(
            tenant_id=tenant.id,
            name="Unassigned",
            slug=f"unassigned-{uuid.uuid4().hex[:8]}",
            status="active",
        )
        db.add(unassigned)
        db.commit()
    assert client.get(base_path(tenant, unassigned) + "/profile").status_code == 404

    other_tenant, other_store, _membership, _principal = tenant_context(
        knowledge_engine
    )
    cross = client.get(base_path(other_tenant, other_store) + "/profile")
    assert cross.status_code == 404
    assert cross.json()["detail"]["code"] == "not_found"

    with Session(knowledge_engine) as db:
        assignment = db.scalar(
            select(StoreAccessAssignment).where(
                StoreAccessAssignment.membership_id == membership.id
            )
        )
        assert assignment is not None and assignment.store_id == store.id


def test_api_operator_is_read_only_and_publish_requires_permission(
    knowledge_engine,
) -> None:
    tenant, store, _membership, principal = tenant_context(
        knowledge_engine,
        role="tenant_operator",
    )
    with Session(knowledge_engine) as db:
        profile = service(db, tenant, store).create_profile(
            expected_revision=0,
            display_name="Operator Store",
            description="Complete profile",
        )
    client = api_client(knowledge_engine, principal)
    path = base_path(tenant, store)
    assert client.get(f"{path}/profile").status_code == 200
    denied = client.post(
        f"{path}/profile/transitions",
        json={"expected_revision": profile.revision, "target_status": "published"},
    )
    assert denied.status_code == 403
    assert denied.json()["detail"]["code"] == "permission_denied"

    viewer_tenant, viewer_store, _membership, viewer = tenant_context(
        knowledge_engine,
        role="read_only",
    )
    viewer_client = api_client(knowledge_engine, viewer)
    mutation = viewer_client.post(
        base_path(viewer_tenant, viewer_store) + "/entries",
        json={
            "expected_revision": 0,
            "slug": "denied",
            "entry_type": "fact",
            "title": "Denied",
            "content": "Denied",
        },
    )
    assert mutation.status_code == 404


def test_migration_contains_exact_tables_and_endpoint_inventory(knowledge_engine) -> None:
    inspector = inspect(knowledge_engine)
    assert TABLES <= set(inspector.get_table_names())
    for name in TABLES:
        indexes = {item["name"] for item in inspector.get_indexes(name)}
        assert any("public_id" in item for item in indexes)
    paths = {
        (route.path, method)
        for route in router.routes
        for method in (route.methods or set())
    }
    assert len(paths) == 21
    assert (
        ("/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/business-knowledge/industry-profile", "GET")
        in paths
    )
    assert (
        ("/api/v1/tenants/{tenant_public_id}/stores/{store_public_id}/business-knowledge/industry-profile", "PUT")
        in paths
    )
    assert all(method != "DELETE" for _path, method in paths)


def test_industry_profile_api_is_revision_checked_and_scope_bound(knowledge_engine) -> None:
    tenant, store, _membership, principal = tenant_context(knowledge_engine)
    client = api_client(knowledge_engine, principal)
    path = base_path(tenant, store) + "/industry-profile"

    assert client.get(path).status_code == 404
    created = client.put(
        path,
        json={
            "expected_revision": 0,
            "industry_code": "fashion",
            "subcategory": "apparel",
            "business_type": "physical",
            "attributes": {"sizes": "S, M", "fabric": "لینن"},
        },
    )
    assert created.status_code == 200
    payload = created.json()
    assert payload["industry_code"] == "fashion"
    assert payload["revision"] == 1
    assert payload["provenance"] == "CUSTOMER_PROVIDED"
    assert payload["business_type"] == "physical"
    assert payload["readiness"]["completion_percent"] == 20
    assert payload["readiness"]["minimum_met"] is False
    assert {item["key"] for item in payload["attributes"]} == {"sizes", "fabric"}

    stale = client.put(
        path,
        json={
            "expected_revision": 0,
            "industry_code": "fashion",
            "subcategory": "apparel",
            "attributes": {"fabric": "کتان"},
        },
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_write"

    other_tenant, other_store, _membership, other_principal = tenant_context(
        knowledge_engine
    )
    del other_tenant, other_store
    other_client = api_client(knowledge_engine, other_principal)
    assert other_client.get(path).status_code == 404

    with Session(knowledge_engine) as db:
        manager = service(db, tenant, store, principal.user_id)
        with pytest.raises(BusinessKnowledgeValidationError, match="reserved"):
            manager.create_entry(
                expected_revision=0,
                slug="industry-profile",
                entry_type="fact",
                title="Collision",
                content="not an industry profile",
            )
