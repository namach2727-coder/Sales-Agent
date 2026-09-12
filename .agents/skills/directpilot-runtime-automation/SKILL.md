---
name: directpilot-runtime-automation
description: Implement or review DirectPilot automation-versus-AI routing for Instagram inbound events. Use for deterministic rules, AI fallback, human takeover, dedup, echo protection, or usage accounting.
---

# DirectPilot runtime automation

1. Trace the existing single inbound pipeline before editing; do not introduce a parallel AI or automation path.
2. Enforce tenant/store/account isolation, event idempotency, duplicate protection, and own-message echo/loop protection before processing.
3. Give `human_active` precedence over deterministic automation and AI.
4. Evaluate Automation only when `instagram_automation` is entitled. A successful deterministic action must stop routing and produce zero LLM/provider calls, PromptBuilder calls, knowledge retrieval, AI usage, and tokens.
5. Preserve the entitlement matrix: Automation-only evaluates deterministic rules and stops on no-match without AI; AI-only invokes AI without requiring Automation; with both entitlements, Automation runs first, a match stops with zero AI, and only a no-match may fall through to AI.
6. Invoke AI only when `ai_assistant` is entitled; knowledge remains approved, provenance-aware, and non-fabricating. Do not couple the two product entitlements.
7. Keep context/output budgets bounded; drop oldest history first while preserving system/safety, relevant knowledge, latest customer message, and recent useful turns.
8. Test human takeover, matched/no-match routes, duplicate delivery, echo suppression, quota/usage, and outbound fail-closed behavior.
