"""Explicit opt-in Meta smoke test; never runs in the normal suite."""

from __future__ import annotations

import os
import uuid

import pytest

from app.application.outbound import OutboundMessage
from app.infrastructure.outbound import InstagramGraphSender


@pytest.mark.skipif(
    os.getenv("RUN_INSTAGRAM_OUTBOUND_INTEGRATION_TEST") != "1",
    reason="requires explicit disposable Meta test account opt-in",
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
