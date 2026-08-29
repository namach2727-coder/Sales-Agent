from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
import logging
from types import SimpleNamespace
from typing import Any

import httpx
from pydantic import ValidationError
import pytest

from app.application.outbound import (
    OutboundAuthenticationError,
    OutboundConnectionUnavailableError,
    OutboundDeliveryResult,
    OutboundInvalidMessageError,
    OutboundInvalidResponseError,
    OutboundMessage,
    OutboundRateLimitError,
    OutboundRecipientUnavailableError,
    OutboundRejectedError,
    OutboundRequestError,
    OutboundScopeError,
    OutboundTimeoutError,
    OutboundUnavailableError,
)
from app.application.services import InstagramOutboundDeliveryService
from app.config import Settings
from app.infrastructure.database.repositories.instagram_outbound_repository import (
    InstagramOutboundConnectionContext,
    InstagramOutboundMessageContext,
)
from app.infrastructure.outbound import (
    InstagramGraphSender,
    build_instagram_graph_sender,
)
from app.instagram_channel.exceptions import (
    InstagramCredentialConfigurationError,
)
from app.tenant_management.context import TenantStoreContext


TENANT_PUBLIC_ID = "00000000-0000-4000-8000-000000000201"
STORE_PUBLIC_ID = "00000000-0000-4000-8000-000000000202"
CONVERSATION_PUBLIC_ID = "00000000-0000-4000-8000-000000000203"
MESSAGE_PUBLIC_ID = "00000000-0000-4000-8000-000000000204"


class FakeRepository:
    def __init__(
        self,
        message: InstagramOutboundMessageContext | None = None,
        connections: tuple[InstagramOutboundConnectionContext, ...] | None = None,
    ) -> None:
        self.message = message if message is not None else _message()
        self.connections = connections if connections is not None else (_connection(),)
        self.get_calls: list[dict[str, Any]] = []
        self.connection_calls: list[dict[str, Any]] = []
        self.updates: list[dict[str, Any]] = []
        self.update_result = True

    def get_message_context(self, message_public_id: str, **kwargs: Any):
        self.get_calls.append({"message_public_id": message_public_id, **kwargs})
        return self.message

    def list_active_connections(self, **kwargs: Any):
        self.connection_calls.append(kwargs)
        return self.connections

    def update_delivery(self, message_public_id: str, **kwargs: Any) -> bool:
        self.updates.append({"message_public_id": message_public_id, **kwargs})
        return self.update_result


class FakeCipher:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.values: list[str] = []

    def decrypt(self, value: str) -> str:
        self.values.append(value)
        if self.error:
            raise self.error
        return "plain-secret-never-log"


class FakeSender:
    def __init__(self, result: object | None = None, error: Exception | None = None):
        self.result = result or _result()
        self.error = error
        self.calls: list[OutboundMessage] = []

    def send(self, message: OutboundMessage):
        self.calls.append(message)
        if self.error:
            raise self.error
        return self.result


class FakeFactory:
    def __init__(self, sender: FakeSender | None = None, error: Exception | None = None):
        self.sender = sender or FakeSender()
        self.error = error
        self.calls: list[dict[str, str]] = []

    def __call__(self, **kwargs: str):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.sender


def _context(**changes: Any) -> TenantStoreContext:
    values = {
        "tenant_id": 1,
        "tenant_public_id": TENANT_PUBLIC_ID,
        "tenant_status": "active",
        "membership_id": None,
        "store_id": 2,
        "store_public_id": STORE_PUBLIC_ID,
        "store_status": "active",
    }
    values.update(changes)
    return TenantStoreContext(**values)


def _message(**changes: Any) -> InstagramOutboundMessageContext:
    values = {
        "message_public_id": MESSAGE_PUBLIC_ID,
        "conversation_public_id": CONVERSATION_PUBLIC_ID,
        "conversation_id": 30,
        "instagram_connection_id": 40,
        "provider_participant_key": "customer-scoped-id",
        "direction": "outbound",
        "content_type": "text",
        "text": "Safe assistant answer",
        "provider_message_id": None,
        "metadata": {
            "author_type": "assistant",
            "source": "ai_response_orchestrator",
            "llm_provider": "fake",
            "llm_total_tokens": 12,
        },
        "reply_to_metadata": {},
    }
    values.update(changes)
    return InstagramOutboundMessageContext(**values)


def _connection(**changes: Any) -> InstagramOutboundConnectionContext:
    values = {
        "connection_id": 40,
        "connection_public_id": "00000000-0000-4000-8000-000000000205",
        "instagram_account_id": "business-account-id",
        "encrypted_access_token": "encrypted-token",
    }
    values.update(changes)
    return InstagramOutboundConnectionContext(**values)


def _result(**changes: Any) -> OutboundDeliveryResult:
    values = {
        "message_public_id": MESSAGE_PUBLIC_ID,
        "conversation_public_id": CONVERSATION_PUBLIC_ID,
        "channel": "instagram",
        "provider": "instagram",
        "delivered": True,
        "provider_message_id": "meta-message-1",
    }
    values.update(changes)
    return OutboundDeliveryResult(**values)


def _setup(
    *,
    repository: FakeRepository | None = None,
    cipher: FakeCipher | None = None,
    factory: FakeFactory | None = None,
):
    repo = repository or FakeRepository()
    selected_cipher = cipher or FakeCipher()
    selected_factory = factory or FakeFactory()
    service = InstagramOutboundDeliveryService(
        repository=repo,  # type: ignore[arg-type]
        token_cipher=selected_cipher,
        sender_factory=selected_factory,
    )
    return SimpleNamespace(
        service=service,
        repository=repo,
        cipher=selected_cipher,
        factory=selected_factory,
        sender=selected_factory.sender,
    )


def _deliver(setup: SimpleNamespace, **kwargs: Any):
    return setup.service.deliver(
        MESSAGE_PUBLIC_ID,
        conversation_public_id=CONVERSATION_PUBLIC_ID,
        context=kwargs.pop("context", _context()),
        **kwargs,
    )


def test_success_uses_trusted_scope_recipient_and_bound_credentials() -> None:
    setup = _setup()
    at = datetime(2026, 8, 1, 9, 30, tzinfo=UTC)

    result = _deliver(setup, delivered_at=at, correlation_id="corr-1")

    assert result.delivered and not result.already_delivered
    assert setup.repository.get_calls[0]["tenant_id"] == 1
    assert setup.repository.get_calls[0]["store_id"] == 2
    assert setup.cipher.values == ["encrypted-token"]
    assert setup.factory.calls == [{
        "access_token": "plain-secret-never-log",
        "sender_account_id": "business-account-id",
    }]
    sent = setup.sender.calls[0]
    assert sent.recipient_external_id == "customer-scoped-id"
    assert sent.text == "Safe assistant answer"
    metadata = setup.repository.updates[-1]["metadata"]
    assert metadata["delivery_status"] == "sent"
    assert metadata["delivery_attempt_count"] == 1
    assert metadata["provider_message_id"] == "meta-message-1"
    assert metadata["delivered_at"] == at.isoformat()
    assert metadata["llm_total_tokens"] == 12
    assert setup.repository.updates[-1]["provider_message_id"] == "meta-message-1"


def test_structured_logs_exclude_credentials_recipient_and_message_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    setup = _setup()
    with caplog.at_level(
        logging.INFO,
        logger="app.application.services.instagram_outbound_delivery",
    ):
        _deliver(setup, correlation_id="safe-correlation")

    rendered = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert "instagram_outbound_started" in rendered
    assert "instagram_outbound_delivered" in rendered
    assert "safe-correlation" in rendered
    for prohibited in (
        "plain-secret-never-log",
        "encrypted-token",
        "customer-scoped-id",
        "Safe assistant answer",
    ):
        assert prohibited not in rendered


def test_second_call_after_recorded_success_has_no_network_or_attempt() -> None:
    repo = FakeRepository(
        message=_message(
            provider_message_id="meta-existing",
            metadata={
                **_message().metadata,
                "delivery_status": "sent",
                "delivery_provider": "instagram",
                "delivery_attempt_count": 1,
            },
        )
    )
    setup = _setup(repository=repo)

    result = _deliver(setup)

    assert result.already_delivered
    assert result.provider_message_id == "meta-existing"
    assert setup.cipher.values == []
    assert setup.factory.calls == []
    assert setup.repository.updates == []


@pytest.mark.parametrize(
    ("changes", "error_type"),
    [
        ({"direction": "inbound"}, OutboundInvalidMessageError),
        ({"content_type": "image"}, OutboundInvalidMessageError),
        ({"text": "  "}, OutboundInvalidMessageError),
        ({"metadata": {"source": "ai_response_orchestrator"}}, OutboundInvalidMessageError),
        ({"metadata": {"author_type": "assistant"}}, OutboundInvalidMessageError),
        ({"provider_participant_key": " "}, OutboundRecipientUnavailableError),
    ],
)
def test_invalid_or_unaddressable_message_stops_before_network(
    changes: dict[str, Any], error_type: type[Exception]
) -> None:
    setup = _setup(repository=FakeRepository(message=_message(**changes)))
    with pytest.raises(error_type):
        _deliver(setup)
    assert setup.factory.calls == []
    assert setup.repository.updates == []


@pytest.mark.parametrize(
    "context",
    [
        _context(tenant_status="suspended"),
        _context(store_status="inactive"),
        _context(store_id=None),
        _context(store_public_id=None),
    ],
)
def test_inactive_or_incomplete_scope_is_rejected(context: TenantStoreContext) -> None:
    setup = _setup()
    with pytest.raises(OutboundScopeError):
        _deliver(setup, context=context)
    assert setup.repository.get_calls == []


def test_missing_or_cross_scope_message_is_safe_not_found() -> None:
    setup = _setup(repository=FakeRepository(message=None))
    setup.repository.message = None
    with pytest.raises(OutboundInvalidMessageError, match="not found"):
        _deliver(setup)
    assert setup.factory.calls == []


@pytest.mark.parametrize(
    "connections",
    [
        (),
        (_connection(connection_id=999),),
        (_connection(), _connection(connection_id=41)),
        (_connection(encrypted_access_token=None),),
    ],
)
def test_connection_must_be_unique_active_matching_and_credentialed(
    connections: tuple[InstagramOutboundConnectionContext, ...],
) -> None:
    setup = _setup(repository=FakeRepository(connections=connections))
    with pytest.raises(OutboundConnectionUnavailableError):
        _deliver(setup)
    assert setup.factory.calls == []


@pytest.mark.parametrize(
    "failure",
    [
        OutboundAuthenticationError("safe"),
        OutboundRecipientUnavailableError("safe"),
        OutboundRateLimitError("safe"),
        OutboundTimeoutError("safe"),
        OutboundUnavailableError("safe"),
        OutboundRejectedError("safe"),
        OutboundRequestError("safe"),
        OutboundInvalidResponseError("safe"),
    ],
)
def test_known_delivery_failure_is_persisted_and_remains_retryable(
    failure: Exception,
) -> None:
    setup = _setup(factory=FakeFactory(sender=FakeSender(error=failure)))
    with pytest.raises(type(failure)):
        _deliver(setup)
    failed = setup.repository.updates[-1]["metadata"]
    assert failed["delivery_status"] == "failed"
    assert failed["delivery_attempt_count"] == 1
    assert failed["last_failure_category"] == failure.category


def test_failed_message_manual_retry_increments_attempt_and_clears_failure() -> None:
    repo = FakeRepository(
        message=_message(
            metadata={
                **_message().metadata,
                "delivery_status": "failed",
                "delivery_provider": "instagram",
                "delivery_attempt_count": 2,
                "last_failure_category": "timeout",
            }
        )
    )
    setup = _setup(repository=repo)
    _deliver(setup)
    metadata = setup.repository.updates[-1]["metadata"]
    assert metadata["delivery_attempt_count"] == 3
    assert "last_failure_category" not in metadata


def test_corrupt_encrypted_token_fails_closed_and_records_failure() -> None:
    cipher_error = InstagramCredentialConfigurationError("raw detail")
    setup = _setup(cipher=FakeCipher(cipher_error))
    with pytest.raises(OutboundConnectionUnavailableError) as raised:
        _deliver(setup)
    assert raised.value.__cause__ is cipher_error
    assert setup.factory.calls == []
    assert setup.repository.updates[-1]["metadata"]["last_failure_category"] == (
        "connection_unavailable"
    )


def test_unknown_adapter_error_is_normalized_without_raw_detail() -> None:
    setup = _setup(factory=FakeFactory(error=RuntimeError("SECRET raw failure")))
    with pytest.raises(OutboundUnavailableError) as raised:
        _deliver(setup)
    assert "SECRET" not in str(raised.value)
    assert isinstance(raised.value.__cause__, RuntimeError)


@pytest.mark.parametrize(
    "result",
    [
        object(),
        _result(delivered=False),
        _result(message_public_id="different"),
        _result(conversation_public_id="different"),
        _result(channel="email"),
        _result(provider="other"),
        _result(provider_message_id=None),
    ],
)
def test_malformed_sender_result_is_rejected_and_recorded(result: object) -> None:
    setup = _setup(factory=FakeFactory(sender=FakeSender(result=result)))
    with pytest.raises(OutboundInvalidResponseError):
        _deliver(setup)
    assert setup.repository.updates[-1]["metadata"]["last_failure_category"] == (
        "invalid_response"
    )


def test_contracts_are_immutable_and_reject_secret_fields() -> None:
    message = OutboundMessage(
        message_public_id=MESSAGE_PUBLIC_ID,
        conversation_public_id=CONVERSATION_PUBLIC_ID,
        tenant_public_id=TENANT_PUBLIC_ID,
        store_public_id=STORE_PUBLIC_ID,
        channel="instagram",
        recipient_external_id="recipient",
        text="answer",
    )
    with pytest.raises(FrozenInstanceError):
        message.text = "changed"
    assert not hasattr(message, "access_token")
    assert not hasattr(_result(), "raw_response")


def test_outbound_settings_have_safe_defaults_and_validate_base_url() -> None:
    settings = Settings(_env_file=None)
    assert settings.meta_graph_base_url == "https://graph.instagram.com"
    assert settings.instagram_outbound_timeout_seconds == 15.0
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            meta_graph_base_url="https://user:password@example.test/path",
        )


class FakeHttpResponse:
    def __init__(self, status_code: int, payload: object = None, json_error: Exception | None = None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeHttpClient:
    def __init__(self, response: object | None = None, error: Exception | None = None):
        self.response = response
        self.error = error
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, **kwargs: Any):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self.response


def _graph_sender(client: FakeHttpClient) -> InstagramGraphSender:
    return InstagramGraphSender(
        base_url="https://graph.instagram.com/",
        api_version="v24.0",
        timeout_seconds=9,
        access_token="test-secret-token",
        sender_account_id="business-1",
        send_enabled=True,
        client=client,
    )


def _outbound_message() -> OutboundMessage:
    return OutboundMessage(
        message_public_id=MESSAGE_PUBLIC_ID,
        conversation_public_id=CONVERSATION_PUBLIC_ID,
        tenant_public_id=TENANT_PUBLIC_ID,
        store_public_id=STORE_PUBLIC_ID,
        channel="instagram",
        recipient_external_id="customer-1",
        text="answer",
    )


def test_graph_adapter_fails_closed_before_network_when_send_is_disabled() -> None:
    client = FakeHttpClient(FakeHttpResponse(200, {"message_id": "must-not-send"}))
    sender = InstagramGraphSender(
        base_url="https://graph.instagram.com",
        api_version="v24.0",
        timeout_seconds=9,
        access_token="test-secret-token",
        sender_account_id="business-1",
        send_enabled=False,
        client=client,
    )

    with pytest.raises(OutboundConnectionUnavailableError) as raised:
        sender.send(_outbound_message())

    assert raised.value.category == "connection_unavailable"
    assert client.calls == []


def test_graph_adapter_fails_closed_for_account_outside_send_allowlist() -> None:
    client = FakeHttpClient(FakeHttpResponse(200, {"message_id": "must-not-send"}))
    settings = Settings(
        meta_send_enabled=True,
        meta_send_allowed_account_ids=["uat-target-account"],
    )
    sender = build_instagram_graph_sender(
        settings,
        access_token="test-secret-token",
        sender_account_id="other-account",
        client=client,
    )

    with pytest.raises(OutboundConnectionUnavailableError):
        sender.send(_outbound_message())

    assert client.calls == []


def test_graph_adapter_allows_account_inside_send_allowlist() -> None:
    client = FakeHttpClient(FakeHttpResponse(200, {"message_id": "mid-allowed"}))
    settings = Settings(
        meta_send_enabled=True,
        meta_send_allowed_account_ids=["business-1"],
    )
    sender = build_instagram_graph_sender(
        settings,
        access_token="test-secret-token",
        sender_account_id="business-1",
        client=client,
    )

    result = sender.send(_outbound_message())

    assert result.provider_message_id == "mid-allowed"
    assert len(client.calls) == 1


def test_graph_adapter_builds_documented_text_request_and_normalizes_success() -> None:
    client = FakeHttpClient(FakeHttpResponse(200, {"message_id": "mid-1"}))
    result = _graph_sender(client).send(_outbound_message())
    url, request = client.calls[0]
    assert url == "https://graph.instagram.com/v24.0/business-1/messages"
    assert request["json"] == {
        "recipient": {"id": "customer-1"},
        "message": {"text": "answer"},
    }
    assert request["timeout"] == 9
    assert request["headers"]["Authorization"] == "Bearer test-secret-token"
    assert result.provider_message_id == "mid-1"


def test_graph_adapter_builds_documented_comment_private_reply() -> None:
    client = FakeHttpClient(FakeHttpResponse(200, {"message_id": "mid-comment"}))
    sender = _graph_sender(client)
    message = OutboundMessage(
        message_public_id=MESSAGE_PUBLIC_ID,
        conversation_public_id=CONVERSATION_PUBLIC_ID,
        tenant_public_id=TENANT_PUBLIC_ID,
        store_public_id=STORE_PUBLIC_ID,
        channel="instagram",
        recipient_external_id="comment-1",
        recipient_type="comment",
        text="answer",
    )

    result = sender.send(message)

    assert client.calls[0][1]["json"]["recipient"] == {
        "comment_id": "comment-1"
    }
    assert result.provider_message_id == "mid-comment"


@pytest.mark.parametrize(
    ("status", "error_type"),
    [
        (400, OutboundRequestError),
        (401, OutboundAuthenticationError),
        (403, OutboundAuthenticationError),
        (404, OutboundRecipientUnavailableError),
        (429, OutboundRateLimitError),
        (500, OutboundUnavailableError),
        (503, OutboundUnavailableError),
        (418, OutboundRequestError),
    ],
)
def test_graph_statuses_map_to_safe_errors(status: int, error_type: type[Exception]) -> None:
    client = FakeHttpClient(FakeHttpResponse(status, {"error": "raw secret"}))
    with pytest.raises(error_type) as raised:
        _graph_sender(client).send(_outbound_message())
    assert "raw secret" not in str(raised.value)


@pytest.mark.parametrize(
    ("error", "error_type"),
    [
        (
            httpx.ReadTimeout(
                "raw", request=httpx.Request("POST", "https://example.test")
            ),
            OutboundTimeoutError,
        ),
        (
            httpx.ConnectError(
                "raw", request=httpx.Request("POST", "https://example.test")
            ),
            OutboundUnavailableError,
        ),
    ],
)
def test_graph_transport_errors_are_normalized(error: Exception, error_type: type[Exception]) -> None:
    with pytest.raises(error_type) as raised:
        _graph_sender(FakeHttpClient(error=error)).send(_outbound_message())
    assert raised.value.__cause__ is error


@pytest.mark.parametrize(
    "response",
    [
        FakeHttpResponse(200, None),
        FakeHttpResponse(200, []),
        FakeHttpResponse(200, {}),
        FakeHttpResponse(200, {"message_id": " "}),
        FakeHttpResponse(200, json_error=ValueError("raw")),
    ],
)
def test_graph_success_requires_safe_message_identifier(response: FakeHttpResponse) -> None:
    with pytest.raises(OutboundInvalidResponseError):
        _graph_sender(FakeHttpClient(response)).send(_outbound_message())
