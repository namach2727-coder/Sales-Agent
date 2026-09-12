# Integration runtime scope

- Keep Instagram on official Meta APIs and preserve the transport-neutral inbound pipeline.
- Enforce trusted tenant/store/account routing, signature validation, deduplication, and own-message echo protection before side effects.
- `META_SEND_ENABLED` stays fail-closed by default. Live sends or Meta mutations require explicit authorization and must use disposable or explicitly scoped accounts.
- Human takeover suppresses automation and AI. Deterministic automation runs before AI only when entitled; a successful rule path is zero-LLM.
- Logs contain sanitized stage/category evidence only: never tokens, secrets, request bodies, prompts, message text, participant IDs, or customer data.
- Do not replay webhooks or mutate Meta/DB during forensic diagnostics unless the user explicitly authorizes that exact mutation.
