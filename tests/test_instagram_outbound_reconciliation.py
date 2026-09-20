from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from threading import Event, Lock, Thread
import uuid

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.application.outbound import OutboundDeliveryResult
from app.application.services.instagram_outbound_delivery import (
    InstagramOutboundDeliveryService,
)
from app.application.services.instagram_outbound_reconciliation import (
    InstagramOutboundReconciliationService,
    OutboundReconciliationConflict,
    OutboundReconciliationNotFound,
)
from app.authentication.router import router as auth_router
from app.commerce.router import router as commerce_router
from app.conversation_core.models import Conversation, ConversationMessage
from app.conversation_core.router import router as inbox_router
from app.database import get_db
from app.infrastructure.database.repositories import InstagramOutboundRepository
from app.instagram_channel.models import InstagramConnection
from app.models import Store, Tenant, TenantAuditLog, UserIdentity
from app.tenant_management.context import TenantStoreContext
from tools.seeding import SeedRunner, default_registry


ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery staple"


class _Cipher:
    def decrypt(self, _value: str) -> str:
        return "fake-token"


class _Sender:
    def __init__(self, calls: list[str], gate: Event | None = None) -> None:
        self.calls = calls
        self.gate = gate

    def send(self, message):
        self.calls.append(message.message_public_id)
        if self.gate is not None:
            self.gate.set()
        return OutboundDeliveryResult(
            message_public_id=message.message_public_id,
            conversation_public_id=message.conversation_public_id,
            channel="instagram",
            provider="instagram",
            delivered=True,
            provider_message_id=f"provider-{uuid.uuid4().hex}",
        )


def _context(tenant: Tenant, store: Store) -> TenantStoreContext:
    return TenantStoreContext(
        tenant_id=tenant.id,
        tenant_public_id=tenant.public_id,
        tenant_status=tenant.status,
        membership_id=1,
        store_id=store.id,
        store_public_id=store.public_id,
        store_status=store.status,
    )


def _records(db: Session, *, certainty: str = "DELIVERY_AMBIGUOUS"):
    suffix = uuid.uuid4().hex
    actor = UserIdentity(
        email=f"operator-{suffix}@example.com",
        normalized_email=f"operator-{suffix}@example.com",
        display_name="Operator",
        status="active",
    )
    tenant = Tenant(name=suffix, slug=suffix, status="active")
    db.add_all((actor, tenant))
    db.flush()
    store = Store(
        tenant_id=tenant.id,
        name=suffix,
        slug=suffix,
        status="active",
        currency_code="IRR",
    )
    db.add(store)
    db.flush()
    connection = InstagramConnection(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_account_id=f"ig-{suffix}",
        status="active",
        encrypted_access_token="ciphertext",
    )
    db.add(connection)
    db.flush()
    conversation = Conversation(
        tenant_id=tenant.id,
        store_id=store.id,
        instagram_connection_id=connection.id,
        provider_participant_key=f"customer-{suffix}",
        status="open",
    )
    db.add(conversation)
    db.flush()
    message = ConversationMessage(
        tenant_id=tenant.id,
        store_id=store.id,
        conversation_id=conversation.id,
        instagram_connection_id=connection.id,
        idempotency_key=f"automation:{uuid.uuid4().hex}",
        direction="outbound",
        content_type="text",
        text="persisted deterministic answer",
        occurred_at=datetime.now(UTC),
        metadata_json={
            "author_type": "automation",
            "source": "automation_rule",
            "delivery_status": "pending",
            "delivery_provider": "instagram",
            "delivery_attempt_count": 1,
            "delivery_certainty": certainty,
            "reconciliation_status": "REQUIRED",
            "safe_retry_eligible": False,
        },
    )
    db.add(message)
    db.flush()
    return actor, tenant, store, conversation, message


def _service(db: Session, actor_id: int, calls: list[str]):
    delivery = InstagramOutboundDeliveryService(
        repository=InstagramOutboundRepository(db),
        token_cipher=_Cipher(),
        sender_factory=lambda **_kwargs: _Sender(calls),
    )
    return InstagramOutboundReconciliationService(
        db, outbound_delivery=delivery, actor_identity_id=actor_id
    )


def test_reconciliation_decisions_are_audited_and_never_call_provider(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'decisions.db').as_posix()}")
    from app.database import Base

    Base.metadata.create_all(engine)
    calls: list[str] = []
    with Session(engine) as db, db.begin():
        actor, tenant, store, _, message = _records(db)
        service = _service(db, actor.id, calls)
        unresolved = service.reconcile(
            message.public_id,
            decision="LEAVE_UNRESOLVED",
            context=_context(tenant, store),
        )
        assert unresolved.delivery_certainty == "DELIVERY_AMBIGUOUS"
        assert unresolved.safe_retry_eligible is False
        confirmed = service.reconcile(
            message.public_id,
            decision="CONFIRM_NOT_SENT",
            context=_context(tenant, store),
        )
        assert confirmed.delivery_certainty == "NOT_SENT_CONFIRMED"
        assert confirmed.safe_retry_eligible is True
        assert confirmed.allowed_actions == ("RETRY",)
        assert db.scalar(
            select(func.count(TenantAuditLog.id)).where(
                TenantAuditLog.target_public_id == message.public_id
            )
        ) == 2
    assert calls == []
    engine.dispose()


def test_confirm_sent_without_provider_id_is_terminal_and_not_retryable(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'sent.db').as_posix()}")
    from app.database import Base

    Base.metadata.create_all(engine)
    calls: list[str] = []
    with Session(engine) as db, db.begin():
        actor, tenant, store, _, message = _records(db)
        service = _service(db, actor.id, calls)
        detail = service.reconcile(
            message.public_id,
            decision="CONFIRM_SENT",
            context=_context(tenant, store),
        )
        assert detail.delivery_status == "sent"
        assert detail.delivery_certainty == "SENT_CONFIRMED"
        assert detail.provider_message_id_present is False
        assert detail.allowed_actions == ()
        with pytest.raises(OutboundReconciliationConflict):
            service.retry(
                message.public_id,
                context=_context(tenant, store),
                commit_before_provider_call=db.commit,
            )
    assert calls == []
    engine.dispose()


def test_confirm_not_sent_then_explicit_retry_reuses_message_once(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'retry.db').as_posix()}")
    from app.database import Base

    Base.metadata.create_all(engine)
    calls: list[str] = []
    with Session(engine) as db:
        actor, tenant, store, _, message = _records(db)
        db.commit()
        context = _context(tenant, store)
        service = _service(db, actor.id, calls)
        service.reconcile(
            message.public_id,
            decision="CONFIRM_NOT_SENT",
            context=context,
        )
        db.commit()
        detail, delivery = service.retry(
            message.public_id,
            context=context,
            commit_before_provider_call=db.commit,
        )
        db.commit()
        assert delivery.delivered
        assert detail.delivery_certainty == "SENT_CONFIRMED"
        assert detail.safe_retry_eligible is False
        assert calls == [message.public_id]
        persisted = db.scalar(
            select(ConversationMessage).where(
                ConversationMessage.public_id == message.public_id
            )
        )
        assert persisted is not None
        assert persisted.text == "persisted deterministic answer"
        assert persisted.metadata_json["source"] == "automation_rule"
    engine.dispose()


def test_ambiguous_retry_and_cross_scope_lookup_fail_closed(tmp_path: Path):
    engine = create_engine(f"sqlite:///{(tmp_path / 'scope.db').as_posix()}")
    from app.database import Base

    Base.metadata.create_all(engine)
    calls: list[str] = []
    with Session(engine) as db, db.begin():
        actor, tenant, store, _, message = _records(db)
        _, foreign_tenant, foreign_store, _, _ = _records(db)
        service = _service(db, actor.id, calls)
        with pytest.raises(OutboundReconciliationConflict):
            service.retry(
                message.public_id,
                context=_context(tenant, store),
                commit_before_provider_call=db.commit,
            )
        with pytest.raises(OutboundReconciliationNotFound):
            service.get(
                message.public_id,
                context=_context(foreign_tenant, foreign_store),
            )
    assert calls == []
    engine.dispose()


@pytest.fixture
def reconciliation_api(tmp_path: Path):
    database = tmp_path / "reconciliation-api.db"
    url = f"sqlite:///{database.as_posix()}"
    config = Config(str(ROOT / "alembic.ini"))
    config.attributes["database_url"] = url
    command.upgrade(config, "head")
    engine = create_engine(url)
    SeedRunner(engine, default_registry()).run("test")
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(commerce_router)
    app.include_router(inbox_router)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def _customer(client: TestClient, suffix: str):
    created = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"reconcile-{suffix}@example.com",
            "password": PASSWORD,
            "display_name": "Reconciliation Owner",
            "tenant_name": f"Tenant {suffix}",
            "tenant_slug": f"reconcile-tenant-{suffix}",
            "store_name": f"Store {suffix}",
            "store_slug": f"reconcile-store-{suffix}",
        },
    )
    assert created.status_code == 201, created.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": f"reconcile-{suffix}@example.com", "password": PASSWORD},
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}, created.json()


def test_reconciliation_api_enforces_authenticated_tenant_and_store_scope(
    reconciliation_api,
):
    client, engine = reconciliation_api
    headers_a, scope_a = _customer(client, "scope-a")
    headers_b, scope_b = _customer(client, "scope-b")
    with Session(engine) as db, db.begin():
        tenant = db.scalar(select(Tenant).where(Tenant.public_id == scope_a["tenant_public_id"]))
        store = db.scalar(select(Store).where(Store.public_id == scope_a["store_public_id"]))
        actor = db.scalar(select(UserIdentity).where(UserIdentity.email == "reconcile-scope-a@example.com"))
        assert tenant and store and actor
        connection = InstagramConnection(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_account_id=f"ig-{uuid.uuid4().hex}",
            status="active",
            encrypted_access_token="ciphertext",
        )
        db.add(connection)
        db.flush()
        conversation = Conversation(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_connection_id=connection.id,
            provider_participant_key=f"customer-{uuid.uuid4().hex}",
            status="open",
        )
        db.add(conversation)
        db.flush()
        message = ConversationMessage(
            tenant_id=tenant.id,
            store_id=store.id,
            conversation_id=conversation.id,
            instagram_connection_id=connection.id,
            idempotency_key=f"ai:{uuid.uuid4().hex}",
            direction="outbound",
            content_type="text",
            text="persisted AI answer",
            occurred_at=datetime.now(UTC),
            metadata_json={
                "author_type": "assistant",
                "source": "ai_response_orchestrator",
                "delivery_status": "pending",
                "delivery_provider": "instagram",
                "delivery_certainty": "DELIVERY_AMBIGUOUS",
                "reconciliation_status": "REQUIRED",
                "safe_retry_eligible": False,
            },
        )
        db.add(message)
        db.flush()
        message_id = message.public_id
    route = (
        f"/api/v1/tenants/{scope_a['tenant_public_id']}/stores/"
        f"{scope_a['store_public_id']}/inbox/outbound/{message_id}/reconciliation"
    )
    assert client.get(route).status_code == 401
    assert client.get(route, headers=headers_b).status_code == 404
    foreign_route = route.replace(
        scope_a["store_public_id"], scope_b["store_public_id"]
    )
    assert client.get(foreign_route, headers=headers_a).status_code == 404
    read = client.get(route, headers=headers_a)
    assert read.status_code == 200
    assert read.json()["allowed_actions"] == [
        "CONFIRM_SENT",
        "CONFIRM_NOT_SENT",
        "LEAVE_UNRESOLVED",
    ]


def test_postgres_two_concurrent_retries_have_one_send_owner():
    import conftest

    if not conftest.POSTGRES_TEST_ENABLED:
        pytest.skip("requires explicit PostgreSQL 16 test database")
    from app.database import engine

    calls: list[str] = []
    calls_lock = Lock()
    provider_started = Event()
    provider_release = Event()
    with Session(engine) as db:
        actor, tenant, store, _, message = _records(db)
        context_values = (tenant.id, tenant.public_id, store.id, store.public_id)
        actor_id = actor.id
        message_id = message.public_id
        message.metadata_json = {
            **message.metadata_json,
            "delivery_status": "failed",
            "delivery_certainty": "NOT_SENT_CONFIRMED",
            "reconciliation_status": "RESOLVED",
            "safe_retry_eligible": True,
        }
        db.commit()

    results: list[str] = []

    class _ConcurrentSender(_Sender):
        def send(self, outbound):
            with calls_lock:
                self.calls.append(outbound.message_public_id)
            provider_started.set()
            assert provider_release.wait(10)
            return OutboundDeliveryResult(
                message_public_id=outbound.message_public_id,
                conversation_public_id=outbound.conversation_public_id,
                channel="instagram",
                provider="instagram",
                delivered=True,
                provider_message_id=f"provider-{uuid.uuid4().hex}",
            )

    def run_retry(label: str):
        with Session(engine) as db:
            tenant_id, tenant_public_id, store_id, store_public_id = context_values
            context = TenantStoreContext(
                tenant_id=tenant_id,
                tenant_public_id=tenant_public_id,
                tenant_status="active",
                membership_id=1,
                store_id=store_id,
                store_public_id=store_public_id,
                store_status="active",
            )
            delivery = InstagramOutboundDeliveryService(
                repository=InstagramOutboundRepository(db),
                token_cipher=_Cipher(),
                sender_factory=lambda **_kwargs: _ConcurrentSender(calls),
            )
            service = InstagramOutboundReconciliationService(
                db, outbound_delivery=delivery, actor_identity_id=actor_id
            )
            try:
                service.retry(
                    message_id,
                    context=context,
                    commit_before_provider_call=db.commit,
                )
                db.commit()
                results.append(f"{label}:sent")
            except OutboundReconciliationConflict:
                db.rollback()
                results.append(f"{label}:blocked")

    first = Thread(target=run_retry, args=("first",))
    first.start()
    assert provider_started.wait(10)
    with Session(engine) as db:
        tenant_id, tenant_public_id, store_id, store_public_id = context_values
        context = TenantStoreContext(
            tenant_id=tenant_id,
            tenant_public_id=tenant_public_id,
            tenant_status="active",
            membership_id=1,
            store_id=store_id,
            store_public_id=store_public_id,
            store_status="active",
        )
        delivery = InstagramOutboundDeliveryService(
            repository=InstagramOutboundRepository(db),
            token_cipher=_Cipher(),
            sender_factory=lambda **_kwargs: _Sender(calls),
        )
        service = InstagramOutboundReconciliationService(
            db, outbound_delivery=delivery, actor_identity_id=actor_id
        )
        detail = service.get(message_id, context=context)
        assert detail.reconciliation_status == "IN_PROGRESS"
        assert detail.allowed_actions == ()
        with pytest.raises(OutboundReconciliationConflict):
            service.reconcile(
                message_id,
                decision="CONFIRM_NOT_SENT",
                context=context,
            )
        db.rollback()
    second = Thread(target=run_retry, args=("second",))
    second.start()
    second.join(10)
    provider_release.set()
    first.join(10)
    assert not first.is_alive() and not second.is_alive()
    assert len(calls) == 1
    assert sorted(value.rsplit(":", 1)[1] for value in results) == ["blocked", "sent"]
