from datetime import UTC, datetime
from types import SimpleNamespace

from app.application.outbound import OutboundDeliveryResult
from app.application.instagram import InstagramInboundProcessingResult
from app.application.integrations.instagram_ai_flow import InstagramAIFlowCoordinator
from app.application.services.inbox_service import InboxService
from app.tenant_management.context import TenantStoreContext


def _context() -> TenantStoreContext:
    return TenantStoreContext(
        tenant_id=11,
        tenant_public_id="tenant-public",
        tenant_status="active",
        membership_id=4,
        store_id=22,
        store_public_id="store-public",
        store_status="active",
    )


class FakeConversationService:
    def __init__(self, status="open"):
        self.conversation = SimpleNamespace(
            id=7,
            public_id="conversation-public",
            status=status,
            tenant_id=11,
            store_id=22,
        )
        self.messages = SimpleNamespace(
            list_by_conversation=lambda *_args, **_kwargs: (
                SimpleNamespace(id=19, direction="inbound"),
            )
        )
        self.status_changes = []
        self.appended = []

    def get_conversation(self, public_id, *, tenant_id, store_id):
        assert public_id == self.conversation.public_id
        assert (tenant_id, store_id) == (11, 22)
        return self.conversation

    def change_status(self, public_id, target_status, **kwargs):
        self.status_changes.append((public_id, target_status, kwargs))
        self.conversation.status = target_status
        return self.conversation

    def append_message(self, public_id, **kwargs):
        self.appended.append((public_id, kwargs))
        return SimpleNamespace(id=31, public_id="manual-message-public")


class FakeOutbound:
    def __init__(self):
        self.calls = []

    def deliver(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return OutboundDeliveryResult(
            message_public_id="manual-message-public",
            conversation_public_id="conversation-public",
            channel="instagram",
            provider="instagram",
            delivered=True,
            provider_message_id="provider-message",
        )


def test_takeover_and_resume_are_idempotent_state_transitions():
    conversations = FakeConversationService()
    service = InboxService(conversations)

    service.take_over("conversation-public", context=_context())
    service.take_over("conversation-public", context=_context())
    assert [change[1] for change in conversations.status_changes] == ["human_active"]

    service.resume_ai("conversation-public", context=_context())
    service.resume_ai("conversation-public", context=_context())
    assert [change[1] for change in conversations.status_changes] == [
        "human_active",
        "open",
    ]


def test_manual_reply_requires_takeover_and_uses_existing_outbound_boundary():
    conversations = FakeConversationService(status="human_active")
    outbound = FakeOutbound()
    service = InboxService(conversations, outbound)

    result = service.send_manual_reply(
        "conversation-public",
        text="  پاسخ دستی  ",
        context=_context(),
        idempotency_key="human-reply-1",
        occurred_at=datetime.now(UTC),
    )

    assert result.message.public_id == "manual-message-public"
    assert conversations.appended[0][1]["metadata"] == {
        "author_type": "human",
        "source": "inbox_manual_reply",
    }
    assert conversations.appended[0][1]["reply_to_message_id"] == 19
    assert outbound.calls
    assert outbound.calls[0][0] == ("manual-message-public",)


def test_manual_reply_is_not_allowed_while_ai_is_active():
    conversations = FakeConversationService(status="open")
    service = InboxService(conversations, FakeOutbound())

    try:
        service.send_manual_reply(
            "conversation-public",
            text="پاسخ",
            context=_context(),
        )
    except Exception as exc:
        assert getattr(exc, "code", None) == "conversation_state_conflict"
    else:
        raise AssertionError("manual reply should require human takeover")


class _Transactions:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class _PausedAI:
    def is_ai_paused(self, *_args, **_kwargs):
        return True

    def generate_response(self, *_args, **_kwargs):
        raise AssertionError("provider must not run while human takeover is active")


def test_paused_conversation_commits_inbound_and_skips_ai():
    transactions = _Transactions()
    coordinator = InstagramAIFlowCoordinator(
        ai_orchestrator=_PausedAI(),
        outbound_delivery=FakeOutbound(),
        transactions=transactions,
        llm_provider_name="test",
    )
    result = coordinator.process(
        InstagramInboundProcessingResult(
            status="processed",
            conversation_public_id="conversation-public",
            message_public_id="inbound-message-public",
        ),
        context=_context(),
        correlation_id="inbox-test",
    )

    assert result.ai_status == "skipped"
    assert result.delivery_status == "skipped"
    assert result.safe_reason == "conversation_human_active"
    assert transactions.commits == 1
    assert transactions.rollbacks == 0
