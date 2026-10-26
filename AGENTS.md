> **2026-10-26 TelBot UAT release blocker:** PR #89 native Telegram managed-creation deep link fix merged into isolated branch as `274fa3a70fe2c37428a55084af6d6466c044b39f` with 3/3 CI PASS. Vercel status for `directpilot-telbot-uat-api` returned FAILURE with `upgradeToPro=build-rate-limit` (team build rate limit), so **DO NOT report deployed**, ready, or UAT accepted. Existing UAT remains on preceding deployed commit until a verifiable successful deploy of exact SHA. Do not retry builds in a loop or change Production. Next: after build capacity is available, redeploy and verify exact GitHub commit status/alias; then owner opens Mini App and tests creation native Telegram link. Telegram Bot Management Mode and live managed bot creation remain unverified. Prior customer screenshot documented generic bot preview instead of creation prompt. No bot tokens exposed.


> **2026-10-25 / TELBOT STATUS UPDATE — current checkpoint**

## TelBot UAT — verified progress snapshot (2026-10-25)

- **Scope:** isolated `feature/telegram-managed-bots-spike-20261017` / `directpilot-telbot-uat-api`; no approval or release of Instagram DirectPilot Production, no Neon schema change, no bot-token rotation.
- **User-observed evidence:** Mini App launched via the `Open TelBot` button in `@DirectPilotManagerBot`; menu URL `https://directpilot-telbot-uat-api.vercel.app/telbot`. Identity endpoint returned `status: match` (getMe bot identity, not signed-login success).
- **Defects and resolutions:** blank/invalid login surfaced as `invalid_signature` (PR #76/#77). PR #78 diagnostic metadata caused HTTP 500 via missing standalone fallback import `safe_initdata_shape`; Vercel ASGI traceback at Oct 25 18:03:29 established root cause, PR #80 fixed; user later confirmed original 401 returned with `q1_c0_s1_u1_a1`.
- **Strong authentication evidence:** user-reported `Ed25519: valid` (PR #81); Telegram data is authentically signed for configured manager bot ID, but bot-token HMAC still fails. This does **not** authorize login. `chat_instance` absence in `q1_c0_s1_u1_a1` is not itself failure.
- **PR lineage (TelBot isolated branch, no Instagram Production promotion):** #76 `aa7f5139` safe auth error categories; #77 `da094da4` preserve signature detail; #78 `bb9c0ed8` safe envelope shape; #79 `53f80cbd` HTTP categorization; #80 `5cfb8f3c` Vercel fallback import hotfix; #81 `a22a1e86` independent Ed25519 diagnosis; #82 `7cf35fe3` safe HMAC mismatch categorization. All associated PR CI gates observed PASS before merging each.
- **PR #82 release status as checked:** 3/3 GitHub Actions PASS; merged to isolated TelBot branch at `7cf35fe37f5e5cb1775d145b5c8de32eb68f6438`; Vercel `directpilot-telbot-uat-api` status **PENDING** at documentation time: https://vercel.com/mohcenp-9857s-projects/directpilot-telbot-uat-api/3fYUjWZ3Loen3dtTVPEBtxTZYhNb . Do not claim UAT READY, auth PASS, or PROD deployed from CI/merge alone.
- **Next gates:** verify this exact SHA is READY on TelBot UAT domain; user launches fresh Mini App and supplies safe HMAC category (`token_whitespace`, `signature_field_included`, `key_or_payload_mismatch`, or `unavailable`). Then identify real bot-token revision vs HMAC input divergence; correct cause without bypassing HMAC. Require protected `/api/v1/me/tenants` HTTP 200, session/navigation and tenant flow PASS before further rollout.
- **Risks:** Vercel connector runtime logs and project details returned 403/404 despite visible GitHub-linked deployments. Owner supplied ASGI traceback; do not treat missing logs as clean. Do not expose `initData`, bot tokens, signature bytes, user IDs, or connection strings.

**Governance note:** This progress snapshot is non-authoritative until Release Register and deployment SHA checks agree. Never convert diagnostic Ed25519 results into authentication permission.

---

# DirectPilot development instructions

## Canonical release documentation / cross-chat continuity (2026-10-15)

- Before modifying DirectPilot or suggesting promotion, read the **current** five concise files `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md`; then `docs/releases/RELEASE_REGISTER.md` and relevant dated runbook. Do not rely on an earlier chronological heading or require owner to re-explain signed-off documentation decisions.
- For EVERY new PR/deployment, update the matching Release Register row with PR number, exact Git ref/SHA, deployed alias/environment, UAT status, Production status, customer acceptance, and evidence. No `CI PASS`/`READY` implies real UAT end-to-end or Production business signoff.
- Never merge the entire Frontend UAT branch to Production main. Two live frontend aliases are separate; backend Vercel UAT/Neon UAT is separate from authoritative Production Render DB/API.
- Neon UAT currently has eight `saas_plans`; only `AUTOMATION_V1`/`AI_ASSISTANT_V1` are purchasable, only `AUTOMATION_TRIAL`/`AI_ASSISTANT_TRIAL` are newly trial eligible (three days). UAT prices do not establish Production DB values. Frontend multi-source DM/Story/Comment makes a separate backend automation rule per selected source, each consuming capacity.
- Owner mandates PostgreSQL BYTEA for all product images and receipt versions, **no R2/S3**, four-month or longer customer-level traceability, obvious mobile Back/Close. Do not misrepresent schema/CI as browser acceptance or independent backup guarantee.
- **Preserve evidence:** original full five canonical docs and supporting AGENTS/PAYMENT_FLOW are archived byte-for-byte at `docs/runbooks/history/20261015_pre_release_register/` and in Git; never remove. Current docs are intentionally concise and supersede chronological status notes in those archives.
- For this **documentation-only** release, Render Production API autodeploy is verified `no` and autoDeployTrigger `off`; nonetheless do not trigger Render deployment, modify production env, data, DNS, Meta, pricing, customer subscriptions, or payments. Production cutover requires separate explicit owner GO.

## Working method

- Inspect `git status` first. Preserve unrelated dirty work and stage intended paths explicitly.
- Search narrowly with `rg` before opening files; read only relevant ranges and follow callers/imports only as needed.
- During implementation, run focused tests. Run the full backend suite once before release when the change or release gate requires it.
- Ignore generated and dependency trees such as `.git`, virtual environments, caches, build output, and temporary test databases during searches.
- Keep final reports concise and preserve verified findings when context becomes tight.

## Git and release safety

- Never use `git reset`, `git clean`, automatic stashing, force push, or published-history rewrites.
- Do not mutate Git state unless the user explicitly authorizes it. A release authorization applies only to the reviewed files and named branch.
- Distinguish local validation, pushed state, deployed state, and cloud UAT. Correlate releases with the exact commit SHA and runtime version evidence.

## Security and authorization

- Never print, persist in the repository, or place in logs/tests/docs any credential, bearer/session token, Meta token or secret, LLM API key, database credential, encryption key, or customer content.
- Tenant/store isolation is mandatory. Derive tenant context from trusted authentication and enforce authorization server-side; fail closed when context or entitlement is absent.

## Runtime invariants

- Keep `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256`; do not raise them to mask prompt or context defects.
- A successful deterministic automation rule performs zero LLM calls, PromptBuilder calls, knowledge retrieval, AI usage, and token usage.
- Run AI only when the `ai_assistant` entitlement permits it. Human takeover (`human_active`) suppresses both automation and AI.
- Preserve deduplication and echo/loop protection on every inbound and outbound path.

## Migration safety

- Prefer additive, forward-only migrations. Preserve historical orders, subscriptions, automation rules, knowledge, and AI usage.
- Never perform a destructive migration without explicit approval. Validate migrations on a fresh temporary database, never `sales_assistant.db`.


## Non-negotiable customer receipt traceability (2026-10-14)

Every manual payment receipt must remain attached to customer identity and its original tenant, store, order, payment, timestamp, checksum and admin event sequence. Must permit privileged search and recovery even after four months and preserve previous uploads when rejected receipts are replaced. Pending UAT PR #36 / Alembic 0027 implements append-only receipt-version evidence within PostgreSQL BYTEA; **NOT yet deployed**. No age-based purge or silent overwrite; backup/restore verification, permission tests and admin UI are acceptance requirements. Proposed 12-month operating retention is subject to valid privacy policy and recoverable backups. Do NOT choose R2/S3 or ask user to repeat this requirement.

## Current owner-approved media architecture (2026-10-14)

- DirectPilot payment receipts ALREADY use PostgreSQL `manual_payments.receipt_data` (BYTEA). Product JPEG media MUST also use durable PostgreSQL `product_media_assets.image_data` (BYTEA) once UAT feature PR #34 and additive Alembic 0026 pass review/migration. No R2/S3 provider is approved: experimental PR #33 was closed WITHOUT MERGE. Do not recreate buckets, suggest cloud storage, require credentials or route images to ephemeral Vercel disk unless the owner explicitly changes the decision.
- Media quotas for new JPEGs: 2 MiB decoded per image and 50 MiB active images/store. UAT and Production Neon projects are separate; never apply 0026 to real database or deploy ORM before approved UAT backup/migration/test. Rendering receipts or static HMAC links must preserve authorization and expiry; no real Meta sends during UAT.
- For cross-chat continuity, read `AI_HANDOFF.md`, `PROJECT_ROADMAP.md`, `DECISIONS.md`, `CURRENT_STATE.md`, `NEXT_ACTIONS.md` IN THAT ORDER. If they conflict with verified deployments/DB state, verify reality; keep docs updated. The owner should never have to repeat this storage or separation policy.

## DirectPilot Product and Architecture Guardrails

These rules apply to every repository task:

1. DirectPilot is an AI Sales Assistant, not a generic Instagram bot.
2. Instagram through official Meta APIs is the only MVP communication channel.
3. Preserve Python, FastAPI, SQLAlchemy, Alembic, PostgreSQL, REST, and the Modular Monolith.
4. Do not introduce microservices during MVP; keep module boundaries extractable.
5. Enforce trusted tenant context and isolation on every tenant-bound operation.
6. Prefer configuration for business variation while keeping domain invariants explicit.
7. Stay cloud-ready without adding cloud services or machine-specific assumptions prematurely.
8. Redis, RabbitMQ, and S3-compatible storage are possible future providers, not mandatory current dependencies.
9. Do not implement marketing engines, CRM, other channels, or future Foundations early.
10. Forever Free means 20 successful automatic replies per tenant calendar day, reset in the tenant timezone; failed/manual/unapproved Shadow Mode replies do not consume quota.
11. AI answers only from approved business knowledge and must not fabricate.
12. The canonical [DirectPilot blueprint](docs/blueprint/AI-Commerce-Platform-Blueprint.md) overrides external prompts and generic architecture recommendations.
13. Every implementation stays inside its active Foundation; FOUNDATION-06 covers only the Lean Business Catalog.
14. Do not claim scalability, test success, or provider support without evidence.
15. Preserve foundation boundaries and do not implement future capability merely because its architecture is documented.
16. Treat public UUID-style identifiers as API boundaries and internal numeric identifiers as persistence details.
