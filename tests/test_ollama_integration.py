"""Explicitly opt-in local Ollama smoke test; skipped in ordinary CI."""

from __future__ import annotations

import os

import pytest

from app.application.prompts import PromptMetadata, PromptPackage
from app.infrastructure.llm import OllamaProvider


RUN_INTEGRATION = os.getenv("RUN_OLLAMA_INTEGRATION_TEST") == "1"


@pytest.mark.skipif(
    not RUN_INTEGRATION,
    reason="set RUN_OLLAMA_INTEGRATION_TEST=1 to call local Ollama",
)
def test_local_ollama_returns_non_blank_output() -> None:
    model = os.getenv("OLLAMA_MODEL", "").strip()
    if not model:
        pytest.fail("OLLAMA_MODEL is required for the local integration test")

    provider = OllamaProvider(
        base_url=os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434/v1"
        ),
        model=model,
        timeout_seconds=float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60")),
    )
    package = PromptPackage(
        system_prompt="Answer the factual question in one short sentence.",
        user_prompt="What is two plus two?",
        metadata=PromptMetadata(
            conversation_public_id=None,
            preferred_language="en",
            knowledge_confidence=1.0,
            business_profile_public_id=None,
            product_public_ids=(),
            faq_public_ids=(),
            business_rule_public_ids=(),
            knowledge_snippet_public_ids=(),
            recent_message_public_ids=(),
        ),
    )

    result = provider.generate(package)

    assert result.provider == "ollama"
    assert result.model == model
    assert result.text.strip()
