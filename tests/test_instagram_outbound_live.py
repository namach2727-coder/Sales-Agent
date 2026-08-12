"""Explicit opt-in Meta smoke test; never runs in the normal suite."""

from __future__ import annotations

import os
import uuid

import pytest

from app.application.outbound import OutboundMessage
from app.infrastructure.outbound import InstagramGraphSender


def _live_send_opted_in() -> bool:
    return (
        os.getenv("RUN_INSTAGRAM_OUTBOUND_INTEGRATION_TEST") == "1"
        and os.getenv("META_SEND_ENABLED", "").strip().casefold() == "true"
    )


def test_live_send_policy_requires_runtime_and_test_opt_ins(monkeypatch) -> None:
    monkeypatch.setenv("INSTAGRAM_OUTBOUND_TEST_ACCESS_TOKEN", "credential")
    monkeypatch.setenv("INSTAGRAM_OUTBOUND_TEST_ACCOUNT_ID", "account")
    monkeypatch.setenv("INSTAGRAM_OUTBOUND_TEST_RECIPIENT_ID", "recipient")
    monkeypatch.delenv("RUN_INSTAGRAM_OUTBOUND_INTEGRATION_TEST", raising=False)
    monkeypatch.delenv("META_SEND_ENABLED", raising=False)
    assert _live_send_opted_in() is False

    monkeypatch.setenv("RUN_INSTAGRAM_OUTBOUND_INTEGRATION_TEST", "1")
    assert _live_send_opted_in() is False

    monkeypatch.setenv("META_SEND_ENABLED", "true")
    assert _live_send_opted_in() is True


@pytest.mark.skipif(
    not _live_send_opted_in(),
    reason="requires explicit disposable Meta test account and live-send opt-ins",
)
def test_live_instagram_text_delivery() -> None:
    token = os.environ["INSTAGRAM_OUTBOUND_TEST_ACCESS_TOKEN"]
    account = os.environ["INSTAGRAM_OUTBOUND_TEST_ACCOUNT_ID"]
    recipient = os.environ["INSTAGRAM_OUTBOUND_TEST_RECIPIENT_ID"]
    marker = str(uuid.uuid4())
    result = InstagramGraphSender(
        base_url=os.getenv(
            "META_GRAPH_BASE_URL", "https://graph.instagram.com"
        ),
        api_version=os.getenv("META_API_VERSION", "v24.0"),
        timeout_seconds=20,
        access_token=token,
        sender_account_id=account,
        send_enabled=(
            os.getenv("META_SEND_ENABLED", "").strip().casefold() == "true"
        ),
    ).send(
        OutboundMessage(
            message_public_id=str(uuid.uuid4()),
            conversation_public_id=str(uuid.uuid4()),
            tenant_public_id=str(uuid.uuid4()),
            store_public_id=str(uuid.uuid4()),
            channel="instagram",
            recipient_external_id=recipient,
            text=f"DirectPilot outbound integration test {marker}",
        )
    )
    assert result.delivered
    assert result.provider_message_id
