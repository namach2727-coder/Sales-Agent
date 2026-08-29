from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import hmac
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import uuid

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session

from app import models as registered_models  # noqa: F401
from app.config import Settings, get_settings
from app.conversation_core.models import Conversation, ConversationMessage
from app.database import Base, get_db
from app.infrastructure.integrations import build_instagram_ai_flow_coordinator
from app.instagram_channel.models import (
    InstagramConnection,
    InstagramInboundEvent,
    InstagramWebhookDelivery,
)
from app.instagram_channel.router import (
    get_instagram_ai_flow_builder,
    public_router,
)
from app.instagram_channel.security import FernetTokenCipher
from app.models import Store, Tenant
from app.observability import CorrelationIdMiddleware


APP_SECRET = "integration-app-secret"
CUSTOMER_TEXT = "CUSTOMER-TEXT-MUST-NOT-BE-LOGGED"
ASSISTANT_TEXT = "ASSISTANT-TEXT-MUST-NOT-BE-LOGGED"
PLAIN_TOKEN = "INSTAGRAM-TOKEN-MUST-NOT-BE-LOGGED"
RECIPIENT = "INSTAGRAM-RECIPIENT-MUST-NOT-BE-LOGGED"


@pytest.fixture(scope="module")
def flow_engine(tmp_path_factory: pytest.TempPathFactory):
    path = tmp_path_factory.mktemp("instagram-ai-flow") / "flow.db"
    engine = create_engine(f"sqlite:///{path.as_posix()}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


class FakeResponses:
    def __init__(
        self,
        *,
        text: str = ASSISTANT_TEXT,
        error: Exception | None = None,
    ) -> None:
        self.text = text
        self.error = error
        self.calls: list[dict[str, Any]] = []
        self.transaction_probe = None

    def create(self, **kwargs: Any) -> Any:
        if self.transaction_probe is not None:
            self.transaction_probe()
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            output_text=self.text,
            model=kwargs["model"],
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=4,
                total_tokens=14,
            ),
            _request_id="fake-provider-request",
            status="completed",
            finish_reason="completed",
            incomplete_details=None,
        )


class FakeLLMClient:
    def __init__(self, responses: FakeResponses) -> None:
        self.responses = responses

    def post(self, url: str, *, json: dict[str, Any]):
        raw = self.responses.create(**json)
        return FakeOllamaResponse(
            {
                "message": {"content": raw.output_text},
                "done": True,
                "done_reason": "stop",
                "prompt_eval_count": raw.usage.input_tokens,
                "eval_count": raw.usage.output_tokens,
            }
        )


class FakeOllamaResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.status_code = 200
        self.headers = {"x-request-id": "fake-provider-request"}

    def json(self) -> dict[str, Any]:
        return self.payload

    def raise_for_status(self) -> None:
        return None


class FakeMetaResponse:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code

    def json(self) -> dict[str, str]:
        return (
            {"message_id": "meta-message-integration"}
            if self.status_code == 200
            else {"error": "RAW-META-ERROR-MUST-NOT-LEAK"}
        )


class FakeMetaClient:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.transaction_probe = None

    def post(self, url: str, **kwargs: Any) -> FakeMetaResponse:
        if self.transaction_probe is not None:
            self.transaction_probe()
        self.calls.append((url, kwargs))
        return FakeMetaResponse(self.status_code)


def _settings(*, provider: str = "openai", send_enabled: bool = True) -> Settings:
    key = Fernet.generate_key().decode("ascii")
    return Settings(
        _env_file=None,
        app_env="test",
        meta_app_secret=APP_SECRET,
        instagram_token_encryption_key=key,
        meta_send_enabled=send_enabled,
        llm_provider=provider,
        openai_api_key="fake-openai-key",
        openai_model="fake-openai-model",
        ollama_model="fake-ollama-model",
    )


def _connection(engine, settings: Settings, *, status: str = "active"):
    suffix = uuid.uuid4().hex
    with Session(engine, expire_on_commit=False) as db:
        tenant = Tenant(
            name=f"Tenant {suffix}",
            slug=f"tenant-{suffix}",
            status="active",
        )
        db.add(tenant)
        db.flush()
        store = Store(
            tenant_id=tenant.id,
            name="Main",
            slug=f"store-{suffix}",
            status="active",
            currency_code="IRR",
        )
        db.add(store)
        db.flush()
        connection = InstagramConnection(
            tenant_id=tenant.id,
            store_id=store.id,
            instagram_account_id=f"ig-{suffix}",
            status=status,
            encrypted_access_token=FernetTokenCipher.from_settings(
                settings
            ).encrypt(PLAIN_TOKEN),
            token_scopes=[],
        )
        db.add(connection)
        db.commit()
        return SimpleNamespace(
            tenant=tenant,
            store=store,
            connection=connection,
        )


def _payload(account_id: str, *, message_id: str | None = None) -> dict[str, Any]:
    return {
        "object": "instagram",
        "tenant_id": 999999,
        "store_id": 999999,
        "entry": [
            {
                "id": account_id,
                "tenant_id": 999999,
                "store_id": 999999,
                "messaging": [
                    {
                        "sender": {"id": RECIPIENT},
                        "recipient": {"id": account_id},
                        "timestamp": 1720000000000,
                        "message": {
                            "mid": message_id or f"mid-{uuid.uuid4().hex}",
                            "text": CUSTOMER_TEXT,
                        },
                    }
                ],
            }
        ],
    }


def _story_reply_payload(account_id: str) -> dict[str, Any]:
    payload = _payload(account_id)
    payload["entry"][0]["messaging"][0]["message"]["reply_to"] = {
        "story": {"id": "story-id", "url": "https://example.test/story"}
    }
    return payload


def _comment_payload(
    account_id: str,
    *,
    comment_id: str | None = None,
    sender_id: str = RECIPIENT,
) -> dict[str, Any]:
    return {
        "object": "instagram",
        "entry": [
            {
                "id": account_id,
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "id": comment_id or f"comment-{uuid.uuid4().hex}",
                            "from": {"id": sender_id},
                            "text": CUSTOMER_TEXT,
                            "media_id": "media-for-comment",
                        },
                    }
                ],
            }
        ],
    }


def _body(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def _signature(body: bytes) -> str:
    digest = hmac.new(
        APP_SECRET.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()
    return f"sha256={digest}"


def _client(
    engine,
    settings: Settings,
    llm: FakeLLMClient,
    meta: FakeMetaClient,
) -> TestClient:
    application = FastAPI()
    application.add_middleware(CorrelationIdMiddleware)
    application.include_router(public_router)

    def database_override():
        with Session(engine) as db:
            yield db

    def builder(db: Session, selected_settings: Settings):
        def assert_no_open_transaction() -> None:
            assert not db.in_transaction()

        llm.responses.transaction_probe = assert_no_open_transaction
        meta.transaction_probe = assert_no_open_transaction
        return build_instagram_ai_flow_coordinator(
            db,
            selected_settings,
            llm_client=llm,
            instagram_client=meta,
        )

    application.dependency_overrides[get_db] = database_override
    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[
        get_instagram_ai_flow_builder
    ] = lambda: builder
    return TestClient(application)


def _post(client: TestClient, payload: dict[str, Any], *, valid=True):
    body = _body(payload)
    signature = _signature(body) if valid else "sha256=" + ("0" * 64)
    return client.post(
        "/api/v1/integrations/instagram/webhook",
        content=body,
        headers={
            "x-hub-signature-256": signature,
            "x-request-id": "public-flow-correlation",
        },
    )


@pytest.mark.parametrize("provider", ["openai", "ollama"])
def test_supported_webhook_completes_full_flow_with_configured_fake_provider(
    flow_engine,
    provider: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = _settings(provider=provider)
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()
    client = _client(flow_engine, settings, FakeLLMClient(responses), meta)
    payload = _payload(scope.connection.instagram_account_id)

    with caplog.at_level(logging.INFO):
        response = _post(client, payload)

    assert response.status_code == 200
    receipt = response.json()
    assert receipt["status"] == "accepted"
    assert receipt["duplicate"] is False
    assert len(receipt["flows"]) == 1
    flow = receipt["flows"][0]
    assert flow["acknowledged"] is True
    assert flow["inbound_status"] == "processed"
    assert flow["ai_status"] == "completed"
    assert flow["delivery_status"] == "sent"
    assert flow["correlation_id"] == "public-flow-correlation"
    assert not any(
        key.endswith("_id") and not key.endswith("public_id")
        for key in flow
        if key != "correlation_id"
    )
    assert responses.calls and len(meta.calls) == 1

    with Session(flow_engine) as db:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.public_id == flow["conversation_public_id"]
            )
        )
        messages = tuple(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation.id)
                .order_by(ConversationMessage.id)
            ).all()
        )
        assert conversation is not None
        assert conversation.tenant_id == scope.tenant.id
        assert conversation.store_id == scope.store.id
        assert len(messages) == 2
        assert messages[0].public_id == flow["inbound_message_public_id"]
        assert messages[0].direction == "inbound"
        assert messages[1].public_id == flow["assistant_message_public_id"]
        assert messages[1].direction == "outbound"
        assert messages[1].metadata_json["llm_provider"] == provider
        assert messages[1].metadata_json["delivery_status"] == "sent"
        assert messages[1].metadata_json["provider_message_id"] == (
            "meta-message-integration"
        )

    rendered_logs = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert "public-flow-correlation" in rendered_logs
    for prohibited in (
        CUSTOMER_TEXT,
        ASSISTANT_TEXT,
        PLAIN_TOKEN,
        RECIPIENT,
        "fake-openai-key",
    ):
        assert prohibited not in rendered_logs


def test_story_reply_reuses_messaging_ai_and_outbound_pipeline(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()

    response = _post(
        _client(flow_engine, settings, FakeLLMClient(responses), meta),
        _story_reply_payload(scope.connection.instagram_account_id),
    )

    assert response.status_code == 200
    assert response.json()["flows"][0]["delivery_status"] == "sent"
    assert len(responses.calls) == len(meta.calls) == 1
    assert meta.calls[0][1]["json"]["recipient"] == {"id": RECIPIENT}
    with Session(flow_engine) as db:
        inbound = db.scalar(
            select(ConversationMessage).where(
                ConversationMessage.tenant_id == scope.tenant.id,
                ConversationMessage.direction == "inbound",
            )
        )
        assert inbound is not None
        assert inbound.metadata_json["instagram_event_kind"] == "story_reply"


def test_comment_reuses_ai_and_sends_one_private_reply(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()
    client = _client(flow_engine, settings, FakeLLMClient(responses), meta)
    comment_id = f"comment-{uuid.uuid4().hex}"
    payload = _comment_payload(
        scope.connection.instagram_account_id,
        comment_id=comment_id,
    )

    first = _post(client, payload)
    duplicate = _post(client, payload)

    assert first.status_code == duplicate.status_code == 200
    assert first.json()["flows"][0]["ai_status"] == "completed"
    assert first.json()["flows"][0]["delivery_status"] == "sent"
    assert duplicate.json()["duplicate"] is True
    assert len(responses.calls) == len(meta.calls) == 1
    assert meta.calls[0][1]["json"]["recipient"] == {
        "comment_id": comment_id
    }
    with Session(flow_engine) as db:
        messages = tuple(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.tenant_id == scope.tenant.id)
                .order_by(ConversationMessage.id)
            )
        )
        assert [message.direction for message in messages] == [
            "inbound",
            "outbound",
        ]
        assert messages[0].metadata_json["instagram_comment_id"] == comment_id
        assert "instagram_comment_id" not in messages[1].metadata_json


def test_own_comment_is_ignored_without_ai_or_private_reply(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()

    response = _post(
        _client(flow_engine, settings, FakeLLMClient(responses), meta),
        _comment_payload(
            scope.connection.instagram_account_id,
            sender_id=scope.connection.instagram_account_id,
        ),
    )

    assert response.status_code == 200
    assert response.json()["flows"][0]["ignored"] is True
    assert responses.calls == []
    assert meta.calls == []


def test_disabled_automation_persists_inbound_without_ai_send_or_replay(
    flow_engine,
) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    with Session(flow_engine) as db, db.begin():
        store = db.get(Store, scope.store.id)
        assert store is not None
        store.automation_enabled = False
        store.automation_revision += 1
    responses = FakeResponses()
    meta = FakeMetaClient()
    client = _client(flow_engine, settings, FakeLLMClient(responses), meta)
    first_payload = _payload(scope.connection.instagram_account_id)

    disabled = _post(client, first_payload)
    assert disabled.status_code == 200
    assert disabled.json()["flows"][0]["ai_status"] == "skipped"
    assert responses.calls == []
    assert meta.calls == []
    with Session(flow_engine) as db:
        conversation = db.scalar(
            select(Conversation).where(
                Conversation.public_id
                == disabled.json()["flows"][0]["conversation_public_id"]
            )
        )
        assert conversation is not None
        assert conversation.inbound_message_count == 1
        assert conversation.outbound_message_count == 0

    duplicate = _post(client, first_payload)
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    with Session(flow_engine) as db, db.begin():
        store = db.get(Store, scope.store.id)
        assert store is not None
        store.automation_enabled = True
        store.automation_revision += 1

    enabled = _post(
        client,
        _payload(scope.connection.instagram_account_id),
    )
    assert enabled.status_code == 200
    assert enabled.json()["flows"][0]["ai_status"] == "completed"
    assert len(responses.calls) == 1
    assert len(meta.calls) == 1
    with Session(flow_engine) as db:
        messages = tuple(
            db.scalars(
                select(ConversationMessage).where(
                    ConversationMessage.conversation_id == conversation.id
                )
            ).all()
        )
    assert len(messages) == 3


def test_disabled_meta_send_persists_ai_result_without_calling_sender(
    flow_engine,
    caplog: pytest.LogCaptureFixture,
) -> None:
    settings = _settings(send_enabled=False)
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()

    with caplog.at_level(logging.INFO):
        response = _post(
            _client(flow_engine, settings, FakeLLMClient(responses), meta),
            _payload(scope.connection.instagram_account_id),
        )

    assert response.status_code == 200
    flow = response.json()["flows"][0]
    assert flow["ai_status"] == "completed"
    assert flow["delivery_status"] == "failed"
    assert flow["safe_reason"] == "connection_unavailable"
    assert len(responses.calls) == 1
    assert meta.calls == []
    rendered_logs = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    for prohibited in (
        CUSTOMER_TEXT,
        ASSISTANT_TEXT,
        PLAIN_TOKEN,
        RECIPIENT,
        "fake-openai-key",
    ):
        assert prohibited not in rendered_logs

    with Session(flow_engine) as db:
        messages = tuple(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.tenant_id == scope.tenant.id)
                .order_by(ConversationMessage.id)
            ).all()
        )
        assert len(messages) == 2
        assert messages[0].direction == "inbound"
        assert messages[1].direction == "outbound"
        assert messages[1].metadata_json["delivery_status"] == "failed"
        assert messages[1].metadata_json["last_failure_category"] == (
            "connection_unavailable"
        )


def test_duplicate_webhook_skips_second_message_ai_and_meta_call(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()
    client = _client(flow_engine, settings, FakeLLMClient(responses), meta)
    payload = _payload(scope.connection.instagram_account_id)

    first = _post(client, payload)
    second = _post(client, payload)

    assert first.status_code == second.status_code == 200
    assert second.json() == {
        "status": "duplicate",
        "duplicate": True,
        "event_count": 0,
        "flows": [],
    }
    assert len(responses.calls) == 1
    assert len(meta.calls) == 1
    with Session(flow_engine) as db:
        assert db.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.tenant_id == scope.tenant.id)
        ) == 2


@pytest.mark.parametrize("llm_text", ["", "   \n"])
def test_invalid_llm_response_preserves_inbound_and_skips_outbound(
    flow_engine,
    llm_text: str,
) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses(text=llm_text)
    meta = FakeMetaClient()
    response = _post(
        _client(flow_engine, settings, FakeLLMClient(responses), meta),
        _payload(scope.connection.instagram_account_id),
    )

    assert response.status_code == 200
    flow = response.json()["flows"][0]
    assert flow["ai_status"] == "failed"
    assert flow["delivery_status"] == "not_started"
    assert flow["safe_reason"] == "llm_provider_invalid_response"
    assert meta.calls == []
    with Session(flow_engine) as db:
        messages = tuple(
            db.scalars(
                select(ConversationMessage).where(
                    ConversationMessage.tenant_id == scope.tenant.id
                )
            ).all()
        )
        assert len(messages) == 1
        assert messages[0].direction == "inbound"


def test_provider_failure_preserves_inbound_and_returns_safe_status(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses(error=RuntimeError("RAW LLM SECRET"))
    meta = FakeMetaClient()
    response = _post(
        _client(flow_engine, settings, FakeLLMClient(responses), meta),
        _payload(scope.connection.instagram_account_id),
    )

    flow = response.json()["flows"][0]
    assert response.status_code == 200
    assert flow["ai_status"] == "failed"
    assert flow["safe_reason"] == "llm_provider_error"
    assert "RAW" not in json.dumps(flow)
    assert meta.calls == []
    with Session(flow_engine) as db:
        assert db.scalar(
            select(func.count())
            .select_from(ConversationMessage)
            .where(ConversationMessage.tenant_id == scope.tenant.id)
        ) == 1


def test_outbound_failure_keeps_assistant_and_failed_metadata(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient(status_code=503)
    response = _post(
        _client(flow_engine, settings, FakeLLMClient(responses), meta),
        _payload(scope.connection.instagram_account_id),
    )

    flow = response.json()["flows"][0]
    assert response.status_code == 200
    assert flow["ai_status"] == "completed"
    assert flow["delivery_status"] == "failed"
    assert flow["safe_reason"] == "unavailable"
    with Session(flow_engine) as db:
        messages = tuple(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.tenant_id == scope.tenant.id)
                .order_by(ConversationMessage.id)
            ).all()
        )
        assert len(messages) == 2
        assistant = messages[1]
        assert assistant.metadata_json["delivery_status"] == "failed"
        assert assistant.metadata_json["last_failure_category"] == "unavailable"
        assert assistant.provider_message_id is None


def test_unsupported_empty_invalid_signature_and_unknown_scope_make_no_calls(
    flow_engine,
) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings)
    responses = FakeResponses()
    meta = FakeMetaClient()
    client = _client(flow_engine, settings, FakeLLMClient(responses), meta)

    unsupported = _payload(scope.connection.instagram_account_id)
    unsupported["entry"][0]["messaging"][0]["message"] = {
        "mid": f"mid-{uuid.uuid4().hex}",
        "text": "   ",
    }
    unsupported_response = _post(client, unsupported)
    invalid_response = _post(
        client,
        _payload(scope.connection.instagram_account_id),
        valid=False,
    )
    unknown_response = _post(client, _payload("unknown-instagram-account"))

    assert unsupported_response.status_code == 200
    assert unsupported_response.json()["flows"][0]["ignored"] is True
    assert invalid_response.status_code == 401
    assert unknown_response.status_code == 200
    assert unknown_response.json()["status"] == "ignored"
    assert responses.calls == []
    assert meta.calls == []


def test_inactive_connection_is_not_routed_to_ai_or_meta(flow_engine) -> None:
    settings = _settings()
    scope = _connection(flow_engine, settings, status="disconnected")
    responses = FakeResponses()
    meta = FakeMetaClient()
    response = _post(
        _client(flow_engine, settings, FakeLLMClient(responses), meta),
        _payload(scope.connection.instagram_account_id),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert response.json()["flows"] == []
    assert responses.calls == []
    assert meta.calls == []
