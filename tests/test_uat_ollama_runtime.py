from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_uat_ollama_runtime_preloads_without_downloading_models() -> None:
    compose = (ROOT / "compose.uat.yaml").read_text(encoding="utf-8")

    assert 'OLLAMA_KEEP_ALIVE: "-1"' in compose
    assert 'ollama ps | grep -F -- "$${OLLAMA_MODEL}"' in compose
    assert 'ollama run "$${OLLAMA_MODEL}" ""' in compose
    assert "ollama pull" not in compose
    assert "ollama rm" not in compose


def test_uat_application_services_bound_ollama_generation() -> None:
    compose = (ROOT / "compose.uat.yaml").read_text(encoding="utf-8")

    # DirectPilot and the public Instagram gateway both execute the AI flow;
    # Ollama itself also preloads the same bounded context.
    assert compose.count('OLLAMA_CONTEXT_LENGTH: "1024"') == 3
    assert compose.count('OLLAMA_MAX_OUTPUT_TOKENS: "16"') == 2
    assert compose.count('OLLAMA_THINKING_ENABLED: "false"') == 2
