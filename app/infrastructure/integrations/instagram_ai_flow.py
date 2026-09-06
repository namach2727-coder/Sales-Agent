"""Dependency construction for the synchronous Instagram AI MVP flow."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.application.integrations import InstagramAIFlowCoordinator
from app.application.knowledge import KnowledgeEngine
from app.application.llm import LLMProvider, LLMResponse
from app.application.prompts import (
    PromptBuilder,
    PromptContextBudget,
    PromptPackage,
)
from app.application.services import (
    AIResponseOrchestrator,
    ConversationService,
    InstagramOutboundDeliveryService,
)
from app.config import Settings
from app.infrastructure.database.repositories import (
    ConversationRepository,
    InstagramOutboundRepository,
    KnowledgeRepository,
    MessageRepository,
)
from app.infrastructure.llm import build_llm_provider
from app.infrastructure.outbound import build_instagram_graph_sender
from app.instagram_channel.security import FernetTokenCipher


class SQLAlchemyTransactionPhaseBoundary:
    def __init__(self, session: Session) -> None:
        self.session = session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()


class ConfiguredLLMProvider:
    """Delay provider construction until the committed AI provider phase."""

    def __init__(self, settings: Settings, *, client: Any | None = None) -> None:
        self.settings = settings
        self.client = client

    @property
    def context_budget(self) -> PromptContextBudget | None:
        if self.settings.llm_provider == "groq":
            return PromptContextBudget(
                context_limit=self.settings.groq_context_length,
                reserved_output_tokens=self.settings.groq_max_output_tokens,
            )
        if self.settings.llm_provider == "ollama":
            return PromptContextBudget(
                context_limit=self.settings.ollama_context_length,
                reserved_output_tokens=self.settings.ollama_max_output_tokens,
            )
        return None

    def generate(self, prompt_package: PromptPackage) -> LLMResponse:
        provider: LLMProvider = build_llm_provider(
            self.settings,
            client=self.client,
        )
        return provider.generate(prompt_package)


class ConfiguredTokenCipher:
    """Resolve the existing Fernet implementation only at credential use."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def encrypt(self, plaintext: str) -> str:
        return FernetTokenCipher.from_settings(self.settings).encrypt(plaintext)

    def decrypt(self, ciphertext: str) -> str:
        return FernetTokenCipher.from_settings(self.settings).decrypt(ciphertext)


def build_instagram_ai_flow_coordinator(
    session: Session,
    settings: Settings,
    *,
    llm_client: Any | None = None,
    instagram_client: Any | None = None,
) -> InstagramAIFlowCoordinator:
    conversations = ConversationRepository(session)
    messages = MessageRepository(session)
    conversation_service = ConversationService(conversations, messages)
    ai = AIResponseOrchestrator(
        conversation_service=conversation_service,
        message_repository=messages,
        knowledge_engine=KnowledgeEngine(KnowledgeRepository(session)),
        prompt_builder=PromptBuilder(),
        llm_provider=ConfiguredLLMProvider(settings, client=llm_client),
    )
    outbound = InstagramOutboundDeliveryService(
        repository=InstagramOutboundRepository(session),
        token_cipher=ConfiguredTokenCipher(settings),
        sender_factory=lambda *, access_token, sender_account_id: (
            build_instagram_graph_sender(
                settings,
                access_token=access_token,
                sender_account_id=sender_account_id,
                client=instagram_client,
            )
        ),
    )
    return InstagramAIFlowCoordinator(
        ai_orchestrator=ai,
        outbound_delivery=outbound,
        transactions=SQLAlchemyTransactionPhaseBoundary(session),
        llm_provider_name=settings.llm_provider,
    )
