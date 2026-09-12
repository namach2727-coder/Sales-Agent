---
name: directpilot-cloud-uat-forensics
description: Trace a specific DirectPilot cloud UAT event using read-only evidence. Use for correlation-ID, marker, webhook, inbox, automation, AI, outbound, dedup, or loop diagnostics; not for fixes or mutations.
---

# DirectPilot cloud UAT forensics

1. Default to read-only. Record the authorized environment, tenant/store/account scope, marker or correlation ID, time window, and pre-test counters.
2. Trace one event through public ingress, signature, delivery persistence, account routing, inbound event, conversation/message, automation, AI when applicable, outbound, and inbox visibility.
3. Use scoped logs and read-only queries. Report timestamps, counts, statuses, safe categories, and boolean identity comparisons; never expose payloads, message text, participant IDs, tokens, headers, prompts, or secrets.
4. Prove deterministic zero-AI paths with absence of provider, prompt, knowledge, usage, and token activity. For AI paths, correlate provider start/completion and bounded context evidence.
5. Check deduplication, own-message echo protection, and human-takeover suppression.
6. Do not replay webhooks, send Meta messages, or mutate Meta, DB, environment, code, or subscriptions without separate explicit authorization.
7. Stop at the first proven failing stage. Distinguish missing evidence from failure and give one minimal next action.
