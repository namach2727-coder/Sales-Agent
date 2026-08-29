from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
import re

import pytest

from app.conversation_core import (
    ASSIGNMENT_STATUSES,
    CONVERSATION_STATUSES,
    MESSAGE_CONTENT_TYPES,
    MESSAGE_DIRECTIONS,
    PARTICIPANT_TYPES,
    PROCESSING_STATUSES,
    SUPPORTED_INBOUND_EVENT_TYPES,
    AssignmentCommand,
    ConversationAssignmentError,
    ConversationConflictError,
    ConversationCoreError,
    ConversationIdentity,
    ConversationImmutableError,
    ConversationInvalidTransitionError,
    ConversationNotFoundError,
    ConversationProcessingError,
    ConversationTransitionCommand,
    ConversationValidationError,
    IncomingConversationEvent,
    MessageIdentity,
    ReadStateCommand,
    ReleaseAssignmentCommand,
    classify_incoming_message,
    deterministic_message_key,
    ensure_conversation_mutable,
    is_conversation_terminal,
    normalize_identifier,
    normalize_metadata,
    normalize_optional_text,
    validate_conversation_transition,
    validate_processing_transition,
)


def test_domain_constant_sets_are_exact_and_immutable() -> None:
    assert CONVERSATION_STATUSES == {
        "open",
        "waiting_for_customer",
        "handoff_requested",
        "human_active",
        "closed",
        "archived",
    }
    assert MESSAGE_DIRECTIONS == {"inbound", "outbound", "system"}
    assert MESSAGE_CONTENT_TYPES == {
        "text",
        "image",
        "video",
        "audio",
        "file",
        "sticker",
        "reaction",
        "unsupported",
    }
    assert PARTICIPANT_TYPES == {
        "customer",
        "instagram_business",
        "system",
        "operator",
    }
    assert ASSIGNMENT_STATUSES == {"assigned", "released"}
    assert PROCESSING_STATUSES == {"pending", "processed", "ignored", "failed"}
    assert SUPPORTED_INBOUND_EVENT_TYPES == {"messaging", "comments"}
    for values in (
        CONVERSATION_STATUSES,
        MESSAGE_DIRECTIONS,
        MESSAGE_CONTENT_TYPES,
        PARTICIPANT_TYPES,
        ASSIGNMENT_STATUSES,
        PROCESSING_STATUSES,
        SUPPORTED_INBOUND_EVENT_TYPES,
    ):
        assert isinstance(values, frozenset)


@pytest.fixture(autouse=True)
def clean_test_customers():
    """Keep this pure domain suite independent from the legacy DB fixture."""

    yield


def incoming_event(**overrides: object) -> IncomingConversationEvent:
    values: dict[str, object] = {
        "instagram_inbound_event_public_id": "event-public-id",
        "tenant_public_id": "tenant-public-id",
        "store_public_id": "store-public-id",
        "instagram_connection_public_id": "connection-public-id",
        "provider_participant_key": "customer-123",
        "provider_message_id": "mid.123",
        "idempotency_key": "event-key",
        "event_type": "messaging",
        "direction": "inbound",
        "content_type": "text",
        "text": "Hello",
        "provider_event_at": datetime(2026, 7, 28, tzinfo=UTC),
        "metadata": {"provider_message_id": "mid.123"},
    }
    values.update(overrides)
    return IncomingConversationEvent(**values)  # type: ignore[arg-type]


def message_key(**overrides: object) -> str:
    values: dict[str, object] = {
        "instagram_connection_public_id": "connection-public-id",
        "provider_participant_key": "customer-123",
        "provider_message_id": "mid.123",
        "inbound_event_idempotency_key": "event-key",
    }
    values.update(overrides)
    return deterministic_message_key(**values)  # type: ignore[arg-type]


def test_exception_hierarchy_and_codes_are_stable() -> None:
    expected = {
        ConversationValidationError: "validation_error",
        ConversationConflictError: "conflict",
        ConversationNotFoundError: "not_found",
        ConversationInvalidTransitionError: "invalid_transition",
        ConversationImmutableError: "immutable",
        ConversationAssignmentError: "assignment_error",
        ConversationProcessingError: "processing_error",
    }
    assert ConversationCoreError.code == "conversation_core_error"
    for exception_type, code in expected.items():
        assert issubclass(exception_type, ConversationCoreError)
        assert exception_type.code == code
        assert str(exception_type()) == ""


@pytest.mark.parametrize("value", [None, " ", "\t"])
def test_required_identifier_rejects_missing_or_blank(value: str | None) -> None:
    with pytest.raises(ConversationValidationError, match="field_name"):
        normalize_identifier(value, field="field_name", required=True)


def test_optional_blank_identifier_returns_none() -> None:
    assert normalize_identifier(" \t ", field="optional") is None


def test_identifier_applies_nfkc_and_trims() -> None:
    assert normalize_identifier("  ＡＢＣ  ", field="identifier") == "ABC"


def test_identifier_rejects_excessive_length_and_control_characters() -> None:
    with pytest.raises(ConversationValidationError):
        normalize_identifier("x" * 4, field="identifier", maximum=3)
    with pytest.raises(ConversationValidationError):
        normalize_identifier("safe\x00unsafe", field="identifier")


def test_optional_text_preserves_lines_tabs_and_normalizes_crlf() -> None:
    assert (
        normalize_optional_text(
            "  first\r\nsecond\rthird\tvalue  ",
            field="message",
            maximum=100,
        )
        == "first\nsecond\nthird\tvalue"
    )


def test_optional_text_rejects_invalid_values() -> None:
    assert normalize_optional_text(" \r\n\t ", field="message", maximum=100) is None
    with pytest.raises(ConversationValidationError):
        normalize_optional_text("hello\x00", field="message", maximum=100)
    with pytest.raises(ConversationValidationError):
        normalize_optional_text("long", field="message", maximum=3)


def test_metadata_returns_defensive_deep_copy() -> None:
    source: dict[str, object] = {"nested": {"items": [1, 2]}}
    result = normalize_metadata(source)
    assert result == source
    assert result is not source
    assert result["nested"] is not source["nested"]
    source["nested"] = {"changed": True}
    assert result == {"nested": {"items": [1, 2]}}


@pytest.mark.parametrize(
    "value",
    [
        {"invalid": object()},
        {"invalid": {1, 2}},
        {"invalid": float("nan")},
    ],
)
def test_metadata_must_be_strictly_json_serializable(
    value: dict[str, object],
) -> None:
    with pytest.raises(ConversationValidationError):
        normalize_metadata(value)


def test_metadata_validates_type_and_utf8_byte_size() -> None:
    with pytest.raises(ConversationValidationError):
        normalize_metadata(["not", "a", "dict"])  # type: ignore[arg-type]
    assert normalize_metadata(None) == {}
    with pytest.raises(ConversationValidationError):
        normalize_metadata({"value": "😀"}, maximum_bytes=10)


_ALLOWED_CONVERSATION_TRANSITIONS = {
    "open": {
        "waiting_for_customer",
        "handoff_requested",
        "human_active",
        "closed",
    },
    "waiting_for_customer": {
        "open",
        "handoff_requested",
        "human_active",
        "closed",
    },
    "handoff_requested": {"open", "human_active", "closed"},
    "human_active": {"waiting_for_customer", "open", "closed"},
    "closed": {"open", "archived"},
}


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (current, target)
        for current, targets in _ALLOWED_CONVERSATION_TRANSITIONS.items()
        for target in targets
    ],
)
def test_every_allowed_conversation_transition(
    current: str,
    target: str,
) -> None:
    assert validate_conversation_transition(current, target) == target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("open", "archived"),
        ("waiting_for_customer", "archived"),
        ("handoff_requested", "waiting_for_customer"),
        ("human_active", "archived"),
        ("archived", "open"),
    ],
)
def test_invalid_conversation_transitions_are_rejected(
    current: str,
    target: str,
) -> None:
    with pytest.raises(ConversationInvalidTransitionError):
        validate_conversation_transition(current, target)


def test_same_conversation_state_is_rejected() -> None:
    with pytest.raises(ConversationInvalidTransitionError):
        validate_conversation_transition("open", "open")


def test_archived_is_the_only_terminal_and_immutable_status() -> None:
    assert is_conversation_terminal("archived") is True
    with pytest.raises(ConversationImmutableError):
        ensure_conversation_mutable("archived")
    for status in _ALLOWED_CONVERSATION_TRANSITIONS:
        assert is_conversation_terminal(status) is False
        ensure_conversation_mutable(status)


@pytest.mark.parametrize("operation", ["transition", "terminal", "mutable"])
def test_unknown_conversation_status_is_rejected(operation: str) -> None:
    with pytest.raises(ConversationValidationError):
        if operation == "transition":
            validate_conversation_transition("unknown", "open")
        elif operation == "terminal":
            is_conversation_terminal("unknown")
        else:
            ensure_conversation_mutable("unknown")


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("pending", "processed"),
        ("pending", "ignored"),
        ("pending", "failed"),
        ("failed", "pending"),
        ("failed", "ignored"),
    ],
)
def test_allowed_processing_transitions(current: str, target: str) -> None:
    assert validate_processing_transition(current, target) == target


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("processed", "pending"),
        ("processed", "ignored"),
        ("ignored", "pending"),
        ("failed", "processed"),
    ],
)
def test_terminal_or_invalid_processing_transitions_are_rejected(
    current: str,
    target: str,
) -> None:
    with pytest.raises(ConversationInvalidTransitionError):
        validate_processing_transition(current, target)


def test_processing_same_state_and_unknown_status_are_rejected() -> None:
    with pytest.raises(ConversationInvalidTransitionError):
        validate_processing_transition("pending", "pending")
    with pytest.raises(ConversationValidationError):
        validate_processing_transition("unknown", "processed")


def test_incoming_event_validates_and_normalizes_text_message() -> None:
    event = incoming_event(
        instagram_inbound_event_public_id="  event-public-id  ",
        provider_participant_key="  customer-123  ",
        text="  Hello\r\nworld  ",
        metadata={"nested": {"safe": True}},
    )
    assert event.instagram_inbound_event_public_id == "event-public-id"
    assert event.provider_participant_key == "customer-123"
    assert event.text == "Hello\nworld"
    assert event.metadata == {"nested": {"safe": True}}


def test_incoming_event_is_frozen() -> None:
    event = incoming_event()
    with pytest.raises(FrozenInstanceError):
        event.text = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("override", "value"),
    [
        ("event_type", "unsupported"),
        ("direction", "outbound"),
        ("content_type", "unknown"),
    ],
)
def test_incoming_event_rejects_invalid_classification(
    override: str,
    value: str,
) -> None:
    with pytest.raises(ConversationValidationError):
        incoming_event(**{override: value})


@pytest.mark.parametrize("text", [None, " ", "\r\n"])
def test_text_event_requires_non_blank_text(text: str | None) -> None:
    with pytest.raises(ConversationValidationError):
        incoming_event(text=text)


def test_unsupported_content_may_omit_text() -> None:
    event = incoming_event(content_type="unsupported", text=None)
    assert event.text is None


def test_incoming_event_rejects_naive_provider_timestamp() -> None:
    with pytest.raises(ConversationValidationError):
        incoming_event(provider_event_at=datetime(2026, 7, 28))
    assert incoming_event().provider_event_at == datetime(2026, 7, 28, tzinfo=UTC)


def test_incoming_event_metadata_is_normalized_and_detached() -> None:
    metadata: dict[str, object] = {"nested": {"value": 1}}
    event = incoming_event(metadata=metadata)
    metadata["nested"] = {"value": 2}
    assert event.metadata == {"nested": {"value": 1}}


def test_conversation_identity_validates_values() -> None:
    identity = ConversationIdentity(" connection ", " customer ")
    assert identity.instagram_connection_public_id == "connection"
    assert identity.provider_participant_key == "customer"
    with pytest.raises(ConversationValidationError):
        ConversationIdentity("connection", " ")


def test_message_identity_allows_missing_provider_message_id() -> None:
    identity = MessageIdentity(
        tenant_public_id="tenant",
        idempotency_key="event-key",
        instagram_connection_public_id="connection",
        provider_message_id=None,
    )
    assert identity.provider_message_id is None
    with pytest.raises(ConversationValidationError):
        MessageIdentity("", "event-key", "connection", None)


def test_assignment_commands_validate_and_normalize_reason() -> None:
    assignment = AssignmentCommand(
        "conversation",
        "assignee",
        "actor",
        "  customer requested help\r\nurgent  ",
    )
    assert assignment.reason == "customer requested help\nurgent"
    release = ReleaseAssignmentCommand("conversation", "actor", "  resolved  ")
    assert release.reason == "resolved"
    with pytest.raises(ConversationValidationError):
        AssignmentCommand("conversation", " ", "actor")
    with pytest.raises(ConversationValidationError):
        ReleaseAssignmentCommand("", "actor")


@pytest.mark.parametrize(
    "values",
    [
        ("", "user", "message"),
        ("conversation", "", "message"),
        ("conversation", "user", ""),
    ],
)
def test_read_state_requires_all_public_ids(values: tuple[str, str, str]) -> None:
    with pytest.raises(ConversationValidationError):
        ReadStateCommand(*values)
    valid = ReadStateCommand("conversation", "user", "message")
    assert valid.last_read_message_public_id == "message"


def test_transition_command_validates_transition_during_construction() -> None:
    command = ConversationTransitionCommand(
        "conversation",
        "open",
        "human_active",
        "actor",
        "  operator joined  ",
    )
    assert command.target_status == "human_active"
    assert command.reason == "operator joined"
    with pytest.raises(ConversationInvalidTransitionError):
        ConversationTransitionCommand(
            "conversation",
            "archived",
            "open",
            "actor",
        )


def test_classifies_supported_text_without_mutating_payload() -> None:
    payload: dict[str, object] = {
        "message": {
            "id": "mid.123",
            "text": "  Hello\r\nworld  ",
            "access_token": "must-not-survive",
        },
        "authorization": "must-not-survive",
    }
    before = {
        "message": {
            "id": "mid.123",
            "text": "  Hello\r\nworld  ",
            "access_token": "must-not-survive",
        },
        "authorization": "must-not-survive",
    }
    content_type, text, metadata = classify_incoming_message(
        event_type="messaging",
        normalized_payload=payload,
    )
    assert (content_type, text) == ("text", "Hello\nworld")
    assert metadata == {"provider_message_id": "mid.123"}
    assert payload == before


@pytest.mark.parametrize(
    "message",
    [
        {"id": "mid.123", "text": " \r\n "},
        {"id": "mid.123", "attachments": [{"type": "image"}]},
    ],
)
def test_blank_or_unsupported_message_uses_minimal_metadata(
    message: dict[str, object],
) -> None:
    content_type, text, metadata = classify_incoming_message(
        event_type="messaging",
        normalized_payload={
            "message": {
                **message,
                "secret": "excluded",
                "credentials": {"password": "excluded"},
            }
        },
    )
    assert (content_type, text) == ("unsupported", None)
    assert metadata == {
        "classification": "unsupported",
        "provider_message_id": "mid.123",
    }


def test_classifier_rejects_missing_message_and_unsupported_event() -> None:
    with pytest.raises(ConversationValidationError):
        classify_incoming_message(
            event_type="messaging",
            normalized_payload={},
        )
    with pytest.raises(ConversationValidationError):
        classify_incoming_message(
            event_type="comments",
            normalized_payload={"message": {}},
        )


def test_deterministic_message_key_is_stable_lowercase_sha256() -> None:
    first = message_key()
    second = message_key()
    assert first == second
    assert len(first) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", first)


@pytest.mark.parametrize(
    "override",
    [
        {"provider_participant_key": "customer-456"},
        {"instagram_connection_public_id": "other-connection"},
        {"provider_message_id": "mid.456"},
    ],
)
def test_deterministic_message_key_changes_with_logical_identity(
    override: dict[str, object],
) -> None:
    assert message_key(**override) != message_key()


def test_provider_message_id_is_stable_across_delivery_variations() -> None:
    assert message_key(
        inbound_event_idempotency_key="first-delivery"
    ) == message_key(
        inbound_event_idempotency_key="second-delivery"
    )


def test_deterministic_message_key_supports_missing_provider_message_id() -> None:
    first = message_key(
        provider_message_id=None,
        inbound_event_idempotency_key="first-delivery",
    )
    second = message_key(
        provider_message_id=None,
        inbound_event_idempotency_key="second-delivery",
    )
    assert re.fullmatch(r"[0-9a-f]{64}", first)
    assert first != second
