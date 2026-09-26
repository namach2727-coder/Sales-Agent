from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from alembic import command
from alembic.config import Config
from argon2 import PasswordHasher, Type
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.authentication import AuthenticationService, PasswordService
from app.commerce.router import router
from app.commerce.kpay_provider import KPayCheckResult, KPayCreateResult, KPayCreateUnknown, KPayProviderError, KPayVerifyResult
from app.commerce.service import CommerceService
from app.config import Settings, get_settings
from app.database import get_db
from app.models import AuthPlatformRoleAssignment, CommerceAdminAuditLog, ManualPayment, SaasPlan, Store, StoreModule, SubscriptionOrder, Tenant, TenantSubscription
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


@pytest.fixture
def commerce_api(tmp_path: Path):
    database = tmp_path / "commerce.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = f"sqlite:///{database.as_posix()}"
    command.upgrade(config, "head")
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    SeedRunner(engine, default_registry()).run("test")
    with Session(engine) as db, db.begin():
        paid = SaasPlan(
            code="TEST_PAID",
            name="Test Paid",
            price_amount=2_500_000,
            currency="IRR",
            reply_limit=100,
            automation_limit=2,
            instagram_account_limit=1,
            duration_days=30,
            module_codes=["instagram_automation"],
            is_active=True,
            is_purchasable=True,
            product_family="AUTOMATION",
        )
        db.add(paid)
    settings = Settings(
        _env_file=None,
        database_url=str(engine.url),
        session_cookie_secure=False,
        authentication_enabled=True,
        card_transfer_card_number="0000000000000000",
        card_transfer_account_number="0000000000000",
        card_transfer_account_name="Test Account",
        card_transfer_bank_name="Test Bank",
        card_transfer_instructions="Upload the receipt for review.",
        receipt_storage_root=str(tmp_path / "receipts"),
        kpay_access_token="fake-kpay-access-token",
        kpay_shop_id="fake-shop-id",
        kpay_card_id="fake-card-id",
        kpay_callback_base_url="https://directpilot.example",
    )
    app = FastAPI()
    app.include_router(router)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = lambda: settings
    yield TestClient(app), engine, settings
    engine.dispose()


def register(client: TestClient, suffix: str = "one") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{suffix}@example.com",
            "password": PASSWORD,
            "display_name": f"Customer {suffix}",
            "tenant_name": f"Tenant {suffix}",
            "tenant_slug": f"tenant-{suffix}",
            "store_name": f"Store {suffix}",
            "store_slug": f"store-{suffix}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, suffix: str = "one") -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": f"{suffix}@example.com", "password": PASSWORD})
    assert response.status_code == 200
    payload = response.json()
    assert "user_id" not in response.text and "tenant_id" not in response.text
    return {"Authorization": f"Bearer {payload['access_token']}"}


def platform_admin_headers(client: TestClient, engine, suffix: str) -> dict[str, str]:
    fast = PasswordService(
        hasher=PasswordHasher(
            time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID
        )
    )
    email = f"platform-{suffix}@example.com"
    with Session(engine, expire_on_commit=False) as db:
        admin = AuthenticationService(db, password_service=fast).create_user(
            email=email,
            display_name="Platform Admin",
            password=PASSWORD,
            email_verified=True,
        )
    with Session(engine) as db, db.begin():
        db.add(
            AuthPlatformRoleAssignment(
                principal_type="user",
                principal_id=str(admin.id),
                role_code="platform_super_admin",
                status="active",
            )
        )
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": PASSWORD}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def paid_plan(client: TestClient) -> dict:
    return next(item for item in client.get("/api/v1/plans").json() if item["code"] == "TEST_PAID")


def create_paid_order(client: TestClient, headers: dict[str, str]) -> dict:
    plan = paid_plan(client)
    response = client.post("/api/v1/orders", headers=headers, json={"plan_public_id": plan["public_id"]})
    assert response.status_code == 201
    assert response.json()["price_amount"] == 2_500_000
    return response.json()


def create_payment(client: TestClient, headers: dict[str, str], order: dict) -> dict:
    response = client.post("/api/v1/payments/card-transfer", headers=headers, json={"order_public_id": order["public_id"]})
    assert response.status_code == 201
    assert response.json()["payment"]["amount"] == order["price_amount"]
    assert response.json()["card_number"] == "0000000000000000"
    assert response.json()["account_number"] == "0000000000000"
    assert response.json()["account_name"] == "Test Account"
    assert response.json()["bank_name"] == "Test Bank"
    assert response.json()["instructions"] == "Upload the receipt for review."
    return response.json()["payment"]


class FakeKPayProvider:
    def __init__(
        self, *, create_unknown: bool = False, verify_status: str = "paid",
        amount_delta: int = 0, check_paid: bool = True,
        check_authority: str | None = None, verify_authority: str | None = None,
        check_error: bool = False, verify_error: bool = False,
    ) -> None:
        self.create_unknown = create_unknown
        self.verify_status = verify_status
        self.amount_delta = amount_delta
        self.check_paid = check_paid
        self.check_authority = check_authority
        self.verify_authority = verify_authority
        self.check_error = check_error
        self.verify_error = verify_error
        self.create_calls: list[dict[str, object]] = []
        self.check_calls: list[str] = []
        self.verify_calls: list[str] = []

    def create_transaction(self, **values) -> KPayCreateResult:
        self.create_calls.append(values)
        if self.create_unknown:
            raise KPayCreateUnknown("safe unknown")
        amount = int(values["amount"]) + self.amount_delta
        return KPayCreateResult(
            transaction_id="provider-transaction-1",
            authority="provider-authority-1",
            amount=amount,
            final_amount=amount,
            fee=0,
            status="pending",
            payment_url="https://kpay.example/pay/provider-authority-1",
        )

    def verify_transaction(self, *, authority: str) -> KPayVerifyResult:
        self.verify_calls.append(authority)
        if self.verify_error:
            raise KPayProviderError("safe verify failure")
        return KPayVerifyResult(
            transaction_id="provider-transaction-1",
            authority=self.verify_authority or authority,
            status=self.verify_status,
            amount=2_500_000 + self.amount_delta,
            paid_at=datetime.now(UTC) if self.verify_status == "paid" else None,
        )

    def check_transaction(self, *, authority: str) -> KPayCheckResult:
        self.check_calls.append(authority)
        if self.check_error:
            raise KPayProviderError("safe check failure")
        return KPayCheckResult(
            authority=self.check_authority or authority,
            status="provider-status-is-not-authoritative",
            is_paid=self.check_paid,
        )

    def close(self) -> None:
        pass


def test_approved_plan_catalog_is_backend_authoritative(commerce_api) -> None:
    client, engine, _settings = commerce_api
    with Session(engine) as db:
        plans = {
            item.code: item
            for item in db.scalars(select(SaasPlan).where(SaasPlan.code.in_(("TRIAL", "START", "PRO"))))
        }
    assert {
        code: (
            plan.price_amount,
            plan.duration_days,
            plan.reply_limit,
            plan.automation_limit,
            plan.instagram_account_limit,
            plan.is_active,
        )
        for code, plan in plans.items()
    } == {
        "TRIAL": (0, 14, 200, 3, 1, True),
        "START": (2_990_000, 30, 1_500, 10, 1, True),
        "PRO": (6_990_000, 30, 5_000, 30, 1, True),
    }
    assert {
        code: set(plan.module_codes or []) for code, plan in plans.items()
    } == {
        "TRIAL": {"instagram_automation", "knowledge_base", "ai_assistant"},
        "START": {"instagram_automation"},
        "PRO": {"instagram_automation", "knowledge_base", "ai_assistant"},
    }
    public = {item["code"]: item for item in client.get("/api/v1/plans").json()}
    assert "FREE" not in public
    assert {"TRIAL", "START", "PRO"}.isdisjoint(public)
    assert public["TEST_PAID"]["product_family"] == "AUTOMATION"


def test_registration_login_and_duplicate_are_public_only(commerce_api) -> None:
    client, engine, _settings = commerce_api
    created = register(client)
    assert set(created) == {"email", "display_name", "tenant_public_id", "tenant_slug", "store_public_id", "store_slug"}
    with Session(engine) as db:
        tenant = db.scalar(select(Tenant).where(Tenant.public_id == created["tenant_public_id"]))
        assert tenant is not None
        trial_orders = list(db.scalars(select(SubscriptionOrder).where(SubscriptionOrder.tenant_id == tenant.id, SubscriptionOrder.status == "paid")).all())
        trial_subscriptions = list(db.scalars(select(TenantSubscription).where(TenantSubscription.tenant_id == tenant.id, TenantSubscription.status == "active")).all())
    assert len(trial_orders) == len(trial_subscriptions) == 2
    assert {item.product_family for item in trial_subscriptions} == {"AUTOMATION", "AI_ASSISTANT"}
    assert all(item.source == "TRIAL" for item in trial_subscriptions)
    headers = login(client)
    subscription = client.get("/api/v1/subscription/me", headers=headers)
    assert subscription.status_code == 200
    assert set(subscription.json()["effective_capabilities"]) == {
        "instagram_automation",
        "knowledge_base",
        "ai_assistant",
    }
    assert all(item["code"] != "TRIAL" for item in client.get("/api/v1/plans").json())
    duplicate = client.post("/api/v1/auth/register", json={
        "email": "one@example.com", "password": PASSWORD, "display_name": "Duplicate",
        "tenant_name": "Other Tenant", "tenant_slug": "other-tenant", "store_name": "Other Store", "store_slug": "other-store",
    })
    assert duplicate.status_code == 409
    headers = login(client)
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200


def test_existing_trial_reconciliation_is_idempotent_and_reuse_preserves_commerce(commerce_api) -> None:
    client, engine, _settings = commerce_api
    created = register(client, "historical")
    headers = login(client, "historical")
    with Session(engine) as db, db.begin():
        tenant = db.scalar(select(Tenant).where(Tenant.public_id == created["tenant_public_id"]))
        store = db.scalar(select(Store).where(Store.public_id == created["store_public_id"]))
        assert tenant is not None and store is not None
        subscription = db.scalar(
            select(TenantSubscription).where(TenantSubscription.store_id == store.id)
        )
        assert subscription is not None
        order = db.get(SubscriptionOrder, subscription.order_id)
        assert order is not None
        snapshot = (
            subscription.public_id,
            subscription.order_id,
            subscription.starts_at,
            subscription.current_period_end,
            dict(subscription.limits_json),
            order.public_id,
        )
        for item in db.scalars(
            select(StoreModule).where(StoreModule.store_id == store.id)
        ).all():
            db.delete(item)

    first = client.post("/api/v1/subscription/me/reconcile-capabilities", headers=headers)
    second = client.post("/api/v1/subscription/me/reconcile-capabilities", headers=headers)
    assert first.status_code == second.status_code == 200
    expected = {"instagram_automation", "knowledge_base", "ai_assistant"}
    assert set(first.json()["effective_capabilities"]) == expected
    assert set(second.json()["effective_capabilities"]) == expected

    with Session(engine) as db, db.begin():
        tenant = db.scalar(select(Tenant).where(Tenant.public_id == created["tenant_public_id"]))
        store = db.scalar(select(Store).where(Store.public_id == created["store_public_id"]))
        assert tenant is not None and store is not None
        subscription = db.scalar(
            select(TenantSubscription).where(TenantSubscription.store_id == store.id)
        )
        assert subscription is not None
        order = db.get(SubscriptionOrder, subscription.order_id)
        assert order is not None
        reused = CommerceService(db).activate_trial(
            tenant=tenant,
            store=store,
            user_id=order.user_id,
        )
        assert reused.id == subscription.id
        assert (
            reused.public_id,
            reused.order_id,
            reused.starts_at,
            reused.current_period_end,
            dict(reused.limits_json),
            order.public_id,
        ) == snapshot
        modules = list(
            db.scalars(select(StoreModule).where(StoreModule.store_id == store.id)).all()
        )
        assert len(modules) == 3
        assert {item.module_code for item in modules if item.status == "active"} == expected


def test_reconciliation_uses_only_effective_plan_and_preserves_tenant_isolation(commerce_api) -> None:
    client, engine, _settings = commerce_api
    first = register(client, "plans-one")
    first_headers = login(client, "plans-one")
    second = register(client, "plans-two")
    now = datetime.now(UTC)

    with Session(engine) as db, db.begin():
        tenant = db.scalar(select(Tenant).where(Tenant.public_id == first["tenant_public_id"]))
        store = db.scalar(select(Store).where(Store.public_id == first["store_public_id"]))
        other_store = db.scalar(select(Store).where(Store.public_id == second["store_public_id"]))
        pro = db.scalar(select(SaasPlan).where(SaasPlan.code == "PRO"))
        assert tenant is not None and store is not None and other_store is not None and pro is not None
        pro_order = SubscriptionOrder(
            tenant_id=tenant.id,
            store_id=store.id,
            user_id=1,
            plan_id=pro.id,
            status="paid",
            price_amount=pro.price_amount,
            currency=pro.currency,
        )
        db.add(pro_order)
        db.flush()
        db.add(
            TenantSubscription(
                tenant_id=tenant.id,
                store_id=store.id,
                plan_id=pro.id,
                order_id=pro_order.id,
                status="active",
                limits_json={"preserved": 1},
                starts_at=now,
                current_period_end=now + timedelta(days=30),
            )
        )
        other_before = {
            item.module_code: (item.status, item.source)
            for item in db.scalars(
                select(StoreModule).where(StoreModule.store_id == other_store.id)
            ).all()
        }

    pro_result = client.post(
        "/api/v1/subscription/me/reconcile-capabilities", headers=first_headers
    )
    assert pro_result.status_code == 200
    assert pro_result.json()["plan_code"] == "PRO"
    assert set(pro_result.json()["effective_capabilities"]) == {
        "instagram_automation",
        "knowledge_base",
        "ai_assistant",
    }

    with Session(engine) as db, db.begin():
        tenant = db.scalar(select(Tenant).where(Tenant.public_id == first["tenant_public_id"]))
        store = db.scalar(select(Store).where(Store.public_id == first["store_public_id"]))
        other_store = db.scalar(select(Store).where(Store.public_id == second["store_public_id"]))
        start = db.scalar(select(SaasPlan).where(SaasPlan.code == "START"))
        assert tenant is not None and store is not None and other_store is not None and start is not None
        start_order = SubscriptionOrder(
            tenant_id=tenant.id,
            store_id=store.id,
            user_id=1,
            plan_id=start.id,
            status="paid",
            price_amount=start.price_amount,
            currency=start.currency,
        )
        db.add(start_order)
        db.flush()
        db.add(
            TenantSubscription(
                tenant_id=tenant.id,
                store_id=store.id,
                plan_id=start.id,
                order_id=start_order.id,
                status="active",
                limits_json={"preserved": 2},
                starts_at=datetime.now(UTC),
                current_period_end=now + timedelta(days=30),
            )
        )

    start_result = client.post(
        "/api/v1/subscription/me/reconcile-capabilities", headers=first_headers
    )
    assert start_result.status_code == 200
    assert start_result.json()["plan_code"] == "START"
    assert set(start_result.json()["effective_capabilities"]) == {
        "instagram_automation", "knowledge_base", "ai_assistant"
    }
    with Session(engine) as db:
        store = db.scalar(select(Store).where(Store.public_id == first["store_public_id"]))
        other_store = db.scalar(select(Store).where(Store.public_id == second["store_public_id"]))
        assert store is not None and other_store is not None
        modules = {
            item.module_code: item.status
            for item in db.scalars(select(StoreModule).where(StoreModule.store_id == store.id)).all()
        }
        assert modules["instagram_automation"] == "active"
        # The newer Automation-only START subscription must not revoke the
        # still-active legacy bundle's AI and Knowledge entitlements.
        assert modules["knowledge_base"] == "active"
        assert modules["ai_assistant"] == "active"
        assert {
            item.module_code: (item.status, item.source)
            for item in db.scalars(
                select(StoreModule).where(StoreModule.store_id == other_store.id)
            ).all()
        } == other_before


def test_plan_price_is_authoritative_and_order_idor_is_denied(commerce_api) -> None:
    client, _engine, _settings = commerce_api
    register(client, "one")
    first = create_paid_order(client, login(client, "one"))
    register(client, "two")
    second_headers = login(client, "two")
    assert client.get(f"/api/v1/orders/{first['public_id']}", headers=second_headers).status_code == 404


def test_order_snapshots_survive_plan_edits_and_drive_activation(commerce_api) -> None:
    client, engine, _settings = commerce_api
    register(client, "snapshot")
    customer_headers = login(client, "snapshot")
    order = create_paid_order(client, customer_headers)
    assert order | {
        "plan_code": "TEST_PAID",
        "plan_name": "Test Paid",
        "product_family": "AUTOMATION",
        "duration_days": 30,
        "instagram_account_limit": 1,
        "automation_limit": 2,
        "ai_reply_limit": 100,
    } == order

    with Session(engine) as db, db.begin():
        plan = db.scalar(select(SaasPlan).where(SaasPlan.code == "TEST_PAID"))
        assert plan is not None
        plan.name = "Changed Later"
        plan.product_family = "AI_ASSISTANT"
        plan.duration_days = 3
        plan.instagram_account_limit = 9
        plan.automation_limit = 99
        plan.reply_limit = 999
        plan.ai_request_limit = 777
        plan.ai_token_limit = 666
        plan.module_codes = ["ai_assistant", "knowledge_base"]

    persisted = client.get(f"/api/v1/orders/{order['public_id']}", headers=customer_headers)
    assert persisted.status_code == 200
    assert persisted.json()["plan_name"] == "Test Paid"
    assert persisted.json()["product_family"] == "AUTOMATION"
    assert persisted.json()["duration_days"] == 30
    assert persisted.json()["automation_limit"] == 2

    payment = create_payment(client, customer_headers, order)
    submitted = client.post(
        f"/api/v1/payments/{payment['public_id']}/receipt",
        headers={**customer_headers, "Content-Type": "image/png"},
        content=b"\x89PNG\r\n\x1a\nsnapshot",
    )
    assert submitted.status_code == 200
    admin_headers = platform_admin_headers(client, engine, "snapshot")
    approved = client.post(
        f"/api/v1/admin/payments/{payment['public_id']}/approve",
        headers=admin_headers,
        json={"expected_revision": submitted.json()["revision"]},
    )
    assert approved.status_code == 200
    with Session(engine) as db:
        stored_order = db.scalar(select(SubscriptionOrder).where(SubscriptionOrder.public_id == order["public_id"]))
        assert stored_order is not None
        subscription = db.scalar(select(TenantSubscription).where(TenantSubscription.order_id == stored_order.id))
        assert subscription is not None
        assert subscription.product_family == "AUTOMATION"
        assert subscription.limits_json == {
            "reply_limit": 100,
            "automation_limit": 2,
            "instagram_account_limit": 1,
            "duration_days": 30,
        }
        assert subscription.current_period_end - subscription.starts_at == timedelta(days=30)


def test_manual_receipt_and_atomic_idempotent_approval(commerce_api) -> None:
    client, engine, settings = commerce_api
    register(client)
    customer_headers = login(client)
    order = create_paid_order(client, customer_headers)
    payment = create_payment(client, customer_headers, order)
    invalid = client.post(f"/api/v1/payments/{payment['public_id']}/receipt", headers={**customer_headers, "Content-Type": "text/plain"}, content=b"not an image")
    assert invalid.status_code == 422
    submitted = client.post(f"/api/v1/payments/{payment['public_id']}/receipt", headers={**customer_headers, "Content-Type": "image/png"}, content=b"\x89PNG\r\n\x1a\nreceipt")
    assert submitted.status_code == 200 and submitted.json()["status"] == "submitted"

    fast = PasswordService(hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID))
    with Session(engine, expire_on_commit=False) as db:
        admin = AuthenticationService(db, password_service=fast).create_user(email="admin@example.com", display_name="Admin", password=PASSWORD, email_verified=True)
    with Session(engine) as db, db.begin():
        db.add(AuthPlatformRoleAssignment(principal_type="user", principal_id=str(admin.id), role_code="platform_super_admin", status="active"))
    admin_login = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": PASSWORD})
    assert admin_login.status_code == 200
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    queue = client.get("/api/v1/admin/payments", headers=admin_headers)
    assert queue.status_code == 200
    queued = queue.json()[0]
    assert queued["public_id"] == payment["public_id"]
    assert queued["plan_code"] == "TEST_PAID"
    assert queued["product_family"] == "AUTOMATION"
    assert queued["order_status"] == "payment_submitted"
    assert queued["submitted_at"] is not None
    assert queued["tenant_name"] and queued["store_name"]
    detail = client.get(f"/api/v1/admin/payments/{payment['public_id']}", headers=admin_headers)
    assert detail.status_code == 200 and detail.json() == queued
    approved = client.post(f"/api/v1/admin/payments/{payment['public_id']}/approve", headers=admin_headers, json={"expected_revision": submitted.json()["revision"]})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    assert approved.json()["order_status"] == "paid"
    duplicate = client.post(f"/api/v1/admin/payments/{payment['public_id']}/approve", headers=admin_headers, json={"expected_revision": submitted.json()["revision"]})
    assert duplicate.status_code == 200
    with Session(engine) as db:
        assert len(list(db.scalars(select(TenantSubscription)).all())) == 3
        module = db.scalar(select(StoreModule).where(StoreModule.module_code == "instagram_automation"))
        assert module is not None and module.status == "active" and module.source == "subscription"
    subscription = client.get("/api/v1/subscription/me", headers=customer_headers)
    assert subscription.status_code == 200 and subscription.json()["plan_code"] == "TEST_PAID"
    assert subscription.json()["current_period_end"] is not None
    receipt = client.get(f"/api/v1/admin/payments/{payment['public_id']}/receipt", headers=admin_headers)
    assert receipt.status_code == 200 and receipt.content.startswith(b"\x89PNG")
    assert Path(settings.receipt_storage_root).is_dir()


def test_payment_rejection_and_customer_cannot_use_admin_route(commerce_api) -> None:
    client, _engine, _settings = commerce_api
    register(client)
    headers = login(client)
    payment = create_payment(client, headers, create_paid_order(client, headers))
    submitted = client.post(f"/api/v1/payments/{payment['public_id']}/receipt", headers={**headers, "Content-Type": "application/pdf"}, content=b"%PDF-test")
    assert submitted.status_code == 200
    denied = client.post(f"/api/v1/admin/payments/{payment['public_id']}/reject", headers=headers, json={"expected_revision": submitted.json()["revision"], "reason": "test"})
    assert denied.status_code == 403
    assert client.get("/api/v1/admin/payments", headers=headers).status_code == 403


def test_platform_admin_manages_dynamic_product_catalog(commerce_api) -> None:
    client, engine, _settings = commerce_api
    register(client, "catalog-admin")
    assert client.get("/api/v1/admin/commerce/plans", headers=login(client, "catalog-admin")).status_code == 403
    fast = PasswordService(hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID))
    with Session(engine, expire_on_commit=False) as db:
        admin = AuthenticationService(db, password_service=fast).create_user(email="platform-catalog-admin@example.com", display_name="Catalog Admin", password=PASSWORD, email_verified=True)
    with Session(engine) as db, db.begin():
        db.add(AuthPlatformRoleAssignment(principal_type="user", principal_id=str(admin.id), role_code="platform_super_admin", status="active"))
    token = client.post("/api/v1/auth/login", json={"email":"platform-catalog-admin@example.com","password":PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/admin/commerce/plans", headers=headers, json={
        "code":"AUTOMATION_MONTHLY", "name":"Automation Monthly", "product_family":"AUTOMATION",
        "description":"Configurable automation plan", "price_amount":1000, "currency":"IRR",
        "duration_days":30, "billing_unit":"day", "automation_limit":5, "reply_limit":0,
        "instagram_account_limit":1, "is_active":True, "is_purchasable":True,
        "display_order":1, "trial_eligible":False,
    })
    assert created.status_code == 201
    plan = created.json()
    assert client.get("/api/v1/plans").json()[0]["product_family"] == "AUTOMATION"
    changed = client.patch(f"/api/v1/admin/commerce/plans/{plan['public_id']}", headers=headers, json={"expected_revision":plan["revision"], "price_amount":2000})
    assert changed.status_code == 200
    with Session(engine) as db:
        assert db.query(CommerceAdminAuditLog).count() == 2


def test_paid_plan_requires_positive_price_before_becoming_purchasable(commerce_api) -> None:
    client, engine, _settings = commerce_api
    customer = register(client, "price-policy")
    normal_headers = login(client, "price-policy")
    fast = PasswordService(hasher=PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1, type=Type.ID))
    with Session(engine, expire_on_commit=False) as db:
        admin = AuthenticationService(db, password_service=fast).create_user(
            email="price-policy-admin@example.com", display_name="Price Policy Admin",
            password=PASSWORD, email_verified=True,
        )
    with Session(engine) as db, db.begin():
        db.add(AuthPlatformRoleAssignment(principal_type="user", principal_id=str(admin.id), role_code="platform_super_admin", status="active"))
    token = client.post("/api/v1/auth/login", json={"email":"price-policy-admin@example.com","password":PASSWORD}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    base = {
        "code":"AUTOMATION_SAFE_DRAFT", "name":"Safe Draft", "product_family":"AUTOMATION",
        "description":"Non-purchasable commercial draft", "price_amount":0, "currency":"IRR",
        "duration_days":30, "billing_unit":"day", "automation_limit":5, "reply_limit":0,
        "instagram_account_limit":1, "ai_request_limit":None, "ai_token_limit":None,
        "is_active":True, "is_purchasable":False, "display_order":8, "trial_eligible":False,
    }
    draft = client.post("/api/v1/admin/commerce/plans", headers=headers, json=base)
    assert draft.status_code == 201
    plan = draft.json()
    rejected = client.patch(
        f"/api/v1/admin/commerce/plans/{plan['public_id']}", headers=headers,
        json={"expected_revision":plan["revision"], "is_purchasable":True},
    )
    assert rejected.status_code == 422
    updated = client.patch(
        f"/api/v1/admin/commerce/plans/{plan['public_id']}", headers=headers,
        json={"expected_revision":plan["revision"], "price_amount":1000, "currency":"USD", "duration_days":2, "billing_unit":"month", "automation_limit":9},
    )
    assert updated.status_code == 200
    sellable = client.patch(
        f"/api/v1/admin/commerce/plans/{plan['public_id']}", headers=headers,
        json={"expected_revision":updated.json()["revision"], "is_purchasable":True},
    )
    assert sellable.status_code == 200
    catalog = client.get("/api/v1/plans").json()
    assert any(item["code"] == "AUTOMATION_SAFE_DRAFT" and item["price_amount"] == 1000 for item in catalog)
    assert client.get("/api/v1/admin/commerce/audit", headers=normal_headers).status_code == 403
    audit = client.get("/api/v1/admin/commerce/audit", headers=headers)
    assert audit.status_code == 200
    assert any(item["action"] == "commercial_plan.updated" and "price_amount" in item["changed_fields"] for item in audit.json())
    assert "password" not in audit.text.casefold()
    assert "bearer" not in audit.text.casefold()
    assert "secret" not in audit.text.casefold()
    granted = client.post("/api/v1/admin/commerce/subscriptions/grants", headers=headers, json={
        "tenant_public_id": customer["tenant_public_id"], "store_public_id": customer["store_public_id"],
        "plan_public_id": plan["public_id"], "expires_at": None,
    })
    assert granted.status_code == 201 and granted.json()["source"] == "ADMIN_GRANT"
    revoked = client.post(
        f"/api/v1/admin/commerce/subscriptions/{granted.json()['public_id']}/revoke",
        headers=headers, json={"expected_status":"active"},
    )
    assert revoked.status_code == 200 and revoked.json()["status"] == "cancelled"
    audit = client.get("/api/v1/admin/commerce/audit", headers=headers).json()
    assert {"subscription.admin_granted", "subscription.admin_revoked"}.issubset({item["action"] for item in audit})


def test_kpay_create_is_idempotent_and_uses_order_snapshot(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, _settings = commerce_api
    register(client, "kpay-create")
    headers = login(client, "kpay-create")
    order = create_paid_order(client, headers)
    fake = FakeKPayProvider(verify_status="not-a-documented-paid-string")
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)

    first = client.post(
        "/api/v1/payments/kpay", headers=headers,
        json={"order_public_id": order["public_id"]},
    )
    second = client.post(
        "/api/v1/payments/kpay", headers=headers,
        json={"order_public_id": order["public_id"]},
    )
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()
    assert first.json()["operation_state"] == "CREATED"
    assert len(fake.create_calls) == 1
    assert fake.create_calls[0]["amount"] == order["price_amount"]
    assert fake.create_calls[0]["factor_number"] == first.json()["payment"]["public_id"]
    assert fake.create_calls[0]["callback_url"].endswith(
        f"/api/v1/payments/kpay/callback/{first.json()['payment']['public_id']}"
    )
    with Session(engine) as db:
        payments = list(db.scalars(select(ManualPayment)).all())
        assert len(payments) == 1
        assert payments[0].provider == "kpay"


def test_kpay_ambiguous_create_never_retries(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _engine, _settings = commerce_api
    register(client, "kpay-unknown")
    headers = login(client, "kpay-unknown")
    order = create_paid_order(client, headers)
    fake = FakeKPayProvider(create_unknown=True)
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    first = client.post("/api/v1/payments/kpay", headers=headers, json={"order_public_id": order["public_id"]})
    second = client.post("/api/v1/payments/kpay", headers=headers, json={"order_public_id": order["public_id"]})
    assert first.status_code == second.status_code == 201
    assert first.json()["operation_state"] == second.json()["operation_state"] == "CREATE_UNKNOWN"
    assert len(fake.create_calls) == 1


def test_kpay_callback_verifies_and_activates_once_from_snapshot(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, _settings = commerce_api
    register(client, "kpay-paid")
    headers = login(client, "kpay-paid")
    order = create_paid_order(client, headers)
    fake = FakeKPayProvider()
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    created = client.post("/api/v1/payments/kpay", headers=headers, json={"order_public_id": order["public_id"]}).json()
    payment_id = created["payment"]["public_id"]

    first = client.get(f"/api/v1/payments/kpay/callback/{payment_id}", follow_redirects=False)
    second = client.get(f"/api/v1/payments/kpay/callback/{payment_id}", follow_redirects=False)
    assert first.status_code == second.status_code == 303
    assert first.headers["location"].endswith(f"/payment/result/{payment_id}?result=success")
    assert len(fake.check_calls) == 1
    assert len(fake.verify_calls) == 1
    status = client.get(f"/api/v1/payments/kpay/{payment_id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["operation_state"] == "PAID"
    with Session(engine) as db:
        stored_order = db.scalar(select(SubscriptionOrder).where(SubscriptionOrder.public_id == order["public_id"]))
        assert stored_order is not None
        subscriptions = list(db.scalars(select(TenantSubscription).where(TenantSubscription.order_id == stored_order.id)).all())
        assert len(subscriptions) == 1
        assert subscriptions[0].product_family == "AUTOMATION"
        assert subscriptions[0].limits_json["automation_limit"] == 2


def test_kpay_unpaid_or_mismatched_verify_never_activates(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, _settings = commerce_api
    register(client, "kpay-unpaid")
    headers = login(client, "kpay-unpaid")
    order = create_paid_order(client, headers)
    fake = FakeKPayProvider(check_paid=False, verify_status="paid")
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    created = client.post("/api/v1/payments/kpay", headers=headers, json={"order_public_id": order["public_id"]}).json()
    payment_id = created["payment"]["public_id"]
    response = client.get(f"/api/v1/payments/kpay/callback/{payment_id}", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].endswith(f"/payment/result/{payment_id}?result=pending")
    assert fake.verify_calls == []
    with Session(engine) as db:
        stored_order = db.scalar(select(SubscriptionOrder).where(SubscriptionOrder.public_id == order["public_id"]))
        assert stored_order is not None
        assert db.scalar(select(TenantSubscription).where(TenantSubscription.order_id == stored_order.id)) is None


def test_kpay_verify_amount_mismatch_fails_without_activation(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, _settings = commerce_api
    register(client, "kpay-verify-mismatch")
    headers = login(client, "kpay-verify-mismatch")
    order = create_paid_order(client, headers)
    fake = FakeKPayProvider()
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    created = client.post(
        "/api/v1/payments/kpay", headers=headers,
        json={"order_public_id": order["public_id"]},
    ).json()
    payment_id = created["payment"]["public_id"]
    fake.amount_delta = 1

    response = client.get(
        f"/api/v1/payments/kpay/callback/{payment_id}", follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].endswith(
        f"/payment/result/{payment_id}?result=failed"
    )
    status = client.get(f"/api/v1/payments/kpay/{payment_id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["operation_state"] == "FAILED"
    with Session(engine) as db:
        stored_order = db.scalar(
            select(SubscriptionOrder).where(
                SubscriptionOrder.public_id == order["public_id"]
            )
        )
        assert stored_order is not None
        assert stored_order.status == "pending"
        assert db.scalar(
            select(TenantSubscription).where(
                TenantSubscription.order_id == stored_order.id
            )
        ) is None


@pytest.mark.parametrize(
    ("case_name", "fake", "expected_state"),
    [
        ("check-mismatch", FakeKPayProvider(check_authority="wrong-authority"), "FAILED"),
        ("verify-mismatch", FakeKPayProvider(verify_authority="wrong-authority"), "FAILED"),
        ("check-error", FakeKPayProvider(check_error=True), "VERIFY_PENDING"),
        ("verify-error", FakeKPayProvider(verify_error=True), "VERIFY_PENDING"),
    ],
)
def test_kpay_provider_mismatch_or_error_never_activates(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
    case_name: str, fake: FakeKPayProvider, expected_state: str,
) -> None:
    client, engine, _settings = commerce_api
    suffix = f"kpay-{case_name}"
    register(client, suffix)
    headers = login(client, suffix)
    order = create_paid_order(client, headers)
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    created = client.post(
        "/api/v1/payments/kpay", headers=headers,
        json={"order_public_id": order["public_id"]},
    ).json()
    payment_id = created["payment"]["public_id"]

    callback = client.get(
        f"/api/v1/payments/kpay/callback/{payment_id}", follow_redirects=False,
    )
    assert callback.status_code == 303
    status = client.get(f"/api/v1/payments/kpay/{payment_id}", headers=headers)
    assert status.status_code == 200
    assert status.json()["operation_state"] == expected_state
    with Session(engine) as db:
        stored_order = db.scalar(
            select(SubscriptionOrder).where(
                SubscriptionOrder.public_id == order["public_id"]
            )
        )
        assert stored_order is not None
        assert stored_order.status == "pending"
        assert db.scalar(
            select(TenantSubscription).where(
                TenantSubscription.order_id == stored_order.id
            )
        ) is None


def test_kpay_provider_identity_collision_fails_closed(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, _settings = commerce_api
    fake = FakeKPayProvider()
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)

    register(client, "kpay-first-identity")
    first_headers = login(client, "kpay-first-identity")
    first_order = create_paid_order(client, first_headers)
    first = client.post(
        "/api/v1/payments/kpay", headers=first_headers,
        json={"order_public_id": first_order["public_id"]},
    )
    assert first.status_code == 201

    register(client, "kpay-second-identity")
    second_headers = login(client, "kpay-second-identity")
    second_order = create_paid_order(client, second_headers)
    second = client.post(
        "/api/v1/payments/kpay", headers=second_headers,
        json={"order_public_id": second_order["public_id"]},
    )
    assert second.status_code == 409
    with Session(engine) as db:
        payments = list(db.scalars(select(ManualPayment).order_by(ManualPayment.id)).all())
        assert len(payments) == 2
        assert payments[0].provider_operation_state == "CREATED"
        assert payments[1].provider_operation_state == "CREATE_UNKNOWN"
        assert payments[1].provider_authority is None
        assert payments[1].provider_transaction_id is None


def test_kpay_is_isolated_from_manual_receipts_and_admin_queue(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, engine, _settings = commerce_api
    register(client, "kpay-isolation")
    headers = login(client, "kpay-isolation")
    order = create_paid_order(client, headers)
    fake = FakeKPayProvider()
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    payment = client.post("/api/v1/payments/kpay", headers=headers, json={"order_public_id": order["public_id"]}).json()["payment"]
    receipt = client.post(
        f"/api/v1/payments/{payment['public_id']}/receipt",
        headers={**headers, "Content-Type": "image/png"}, content=b"\x89PNG\r\n\x1a\nreceipt",
    )
    assert receipt.status_code == 409
    admin_headers = platform_admin_headers(client, engine, "kpay-isolation")
    assert client.get("/api/v1/admin/payments", headers=admin_headers).json() == []


def test_kpay_cross_tenant_create_is_hidden(
    commerce_api, monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _engine, _settings = commerce_api
    register(client, "kpay-owner")
    order = create_paid_order(client, login(client, "kpay-owner"))
    register(client, "kpay-other")
    fake = FakeKPayProvider()
    monkeypatch.setattr("app.commerce.router.build_kpay_provider", lambda _settings: fake)
    response = client.post(
        "/api/v1/payments/kpay", headers=login(client, "kpay-other"),
        json={"order_public_id": order["public_id"]},
    )
    assert response.status_code == 404
    assert fake.create_calls == []


def test_zero_price_trial_is_an_explicit_sellable_exception(commerce_api) -> None:
    CommerceService._validate_sellable_policy(price_amount=0, is_purchasable=True, trial_eligible=True)


def test_admin_customer_listing_is_bounded_paginated_and_authorized(commerce_api) -> None:
    client, engine, _settings = commerce_api
    normal = register(client, "customer-list-normal")
    client.cookies.clear()
    assert client.get("/api/v1/admin/commerce/customers").status_code == 401
    normal_headers = login(client, "customer-list-normal")
    assert (
        client.get(
            "/api/v1/admin/commerce/customers", headers=normal_headers
        ).status_code
        == 403
    )
    headers = platform_admin_headers(client, engine, "customer-list")
    with Session(engine) as db, db.begin():
        for number in range(105):
            tenant = Tenant(
                name=f"000 Customer {number:03d}",
                slug=f"page-tenant-{number:03d}",
                status="active",
            )
            db.add(tenant)
            db.flush()
            db.add(
                Store(
                    tenant_id=tenant.id,
                    name=f"Store {number:03d}",
                    slug=f"page-store-{number:03d}",
                    status="active",
                )
            )

    default_page = client.get(
        "/api/v1/admin/commerce/customers", headers=headers
    )
    assert default_page.status_code == 200
    assert len(default_page.json()) == 100
    first = client.get(
        "/api/v1/admin/commerce/customers?page=1&page_size=2", headers=headers
    )
    second = client.get(
        "/api/v1/admin/commerce/customers?page=2&page_size=2", headers=headers
    )
    assert [item["tenant_name"] for item in first.json()] == [
        "000 Customer 000",
        "000 Customer 001",
    ]
    assert [item["tenant_name"] for item in second.json()] == [
        "000 Customer 002",
        "000 Customer 003",
    ]
    assert client.get(
        "/api/v1/admin/commerce/customers?page=999&page_size=100", headers=headers
    ).json() == []
    assert (
        client.get(
            "/api/v1/admin/commerce/customers?page_size=101", headers=headers
        ).status_code
        == 422
    )
    assert normal["tenant_public_id"] not in {
        item["tenant_public_id"] for item in first.json()
    }
