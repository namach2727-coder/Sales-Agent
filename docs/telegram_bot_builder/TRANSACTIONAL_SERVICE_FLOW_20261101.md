## Superseded product direction — 2026-11-01

Owner switched to our own portfolio/inquiry bot and project-based custom development. The generic workflow, panel and payment integration roadmap below is historical and deferred; do not continue it as the current task. See OWN_SHOWCASE_BOT_20261101.md. Existing code/evidence preserved.

---

## 2026-11-01 — CURRENT: synthetic service-sales prototype #119 LIVE in isolated UAT

PR https://github.com/namach2727-coder/Sales-Agent/pull/119 reviewed head 1f3a2a44f5af8fdee4a653a7463a71fa44db99c5 passed all 11 checks. Squash merge b18514a08e55d5c2c330eaebe263d3a7bfd83502 ONLY into feature/telegram-managed-bots-spike-20261017 has identical reviewed tree dc88b555f4ff01de6336976479234ea235ccba70. Automatic deployment dpl_45WCEywF5XqqdJVQhFcXahbNyrVv is READY on the exact merge and owns canonical https://directpilot-telbot-uat-api.vercel.app. This is the isolated TelBot UAT project; business Production was not promoted.

Verified release: /ready 200, database available, migration current; /telbot and both assets 200 and byte-identical to reviewed source, cache revision 20261101-service-flow-preview-1. New service-flow-preview POST with synthetic IDs and no authentication returns 401 missing_init_data. Read-only Neon UAT metadata: 1 active bot, 0 paused, published version 6. No schema migration, customer configuration/status change, secret retrieval, external API flag change, actual provider/payment/account or Telegram send performed for this release. Ordinary replies remain enabled; external API calls remain disabled.

CI unit job 124781995713: 150 discovered, 145 PASS + 5 PostgreSQL skips; schema job 124781995908: all 5 PASS including real UI/FastAPI/PostgreSQL sample with editor identity/focus and existing configuration counts preserved. Both DOM/editor and seven Save scenarios PASS. Initial schema fixture focus expectation was corrected after report Close deliberately focused its opener; the final reviewed head passed. Native owner phone acceptance remains PENDING.

Owner/editor can open «نمونهٔ فروش و تحویل سرویس» and explicitly run paid, unconfirmed, amount-mismatch or lost-response scenarios. Fixed fictional prices, inert checkout text and invalid DEMO account/config; simulation=true, live_actions=false. Engine is IN-MEMORY and customer Telegram runtime is NOT connected to it. This release does not deliver actual VPN/payment/checkout accounts, a generic workflow designer, or durable cross-restart idempotency. No AI is implemented. Owner chose a synthetic engine/sample because no panel exists yet; private reference-bot behavior and latency remain unverified.

NEXT: implement versioned mobile no-code steps and durable scoped orders/runs/operation ledger with encrypted sensitive data; then integrate actual documented panel and verified payment adapters with reconciliation, and private Telegram delivery. Real sandbox acceptance requires the eventual panel/gateway contract. See docs/telegram_bot_builder/TRANSACTIONAL_SERVICE_FLOW_20261101.md for gates. Do not wire this prototype to live commerce as-is.

---

# Transactional TelBot direction and synthetic prototype — 2026-11-01

## Owner decision / exact scope

The owner wants a general server/API-connected bot builder capable of service selection, checkout/payment verification, automatic account provisioning and connection configuration delivery. VPN service sales is the reference example. The owner explicitly answered «هنوز پنل نداریم»: build an engine and sample first; real connection follows later. No real VPN panel, merchant contract, gateway credentials or live provisioning was provided. The current platform does not use AI. The third-party bot's private UI/backend/performance was not inspected; do not infer its implementation from the public profile or promise fractional-second latency.

## First working prototype

ServiceFlow is a pure in-memory state machine. It chooses a trusted configured Plan, freezes amount/currency in an immutable Order, requests checkout, accepts a trusted normalized checkout receipt only for the current order and an allowlisted HTTPS host, waits for customer Check Payment, and requests verification. A paid result must match order ID, payment reference, exact integer amount and currency before a provision instruction may be produced. The prototype does not convert currency implicitly. Scope/run-derived operation IDs are intended to become provider idempotency keys.

Only the trusted adapter method accepts external receipts; user Choose/Check/Cancel cannot assert paid status. A repeated consumed callback cannot issue a second provision. Pending payment does not provision. Unknown checkout/provision outcome stops for reconciliation rather than blind retry. A bound of 10 verification requests prevents infinite polling inside a run. Returned account fields use masked secret representations and categorical errors. These guards are process-local; there is NO durable ledger or restart recovery yet. Do not connect this module to real payments/provisioning as-is.

The private Mini App sample POST /api/v1/tenants/{tenant_id}/bots/{bot_id}/service-flow-preview uses fixed mock adapters and fictional IRT plans (10,000 / 20,000 toman), not commercial prices. Four scenario options generate an ordered trace: confirmed, not confirmed, amount mismatch and lost provisioning response. It always returns simulation=true and live_actions=false; links are inert text and demo account/config strings are invalid. No API keys are entered or retrieved. Active owner/editor membership and tenant-bound bot identity are checked; viewers/foreign bots fail closed. Validation errors cannot echo credentials. No configuration/version/order/payment/session writes or live network calls.

The existing Telegram customer-chat runtime is unchanged. This is an owner-facing demonstration, not a published customer sales flow. Existing API-action flag remains OFF; ordinary automatic replies remain ON in UAT. No actual payment, order, account, VPN subscription, file or QR is created.

## Mandatory next implementation gates

1. Versioned no-code scenario definitions: start/menu, choices, input collection/validation, variables, transitions, API connection bindings, link/file/config delivery. Mobile steps first; preserve typing and explicit Save.
2. Persistent per-tenant/bot/customer run and pinned configuration version; immutable order price/product/currency; durable operation ledger, explicit unknown state, encrypted sensitive response/context and bounded retention. Repeated Telegram update/callback/webhook must not repeat a purchase or account creation.
3. Gateway adapter: create checkout bound to the immutable order; validate authenticated provider-side verification and amount/currency/reference/merchant binding. Browser redirects or user claims are not payment proof. Track late paid/cancelled orders, refund/manual review and reconciliation; do not silently discard financial events.
4. Panel adapter from actual provider API docs: endpoint/auth, create/status/readback, product mapping and provider-supported idempotency or lookup by our operation/order reference. Reconcile unknown outcome before retry. Preserve current public-HTTPS/DNS/timeout/secret safeguards. Raw SSH/server login is not a generic API contract.
5. Customer Telegram delivery: private-chat authorization, username/password/config/subscription link/file/QR and server compatibility as actual panel contract requires. Scope each generated account to its purchaser. User-visible failure handling, expiry/renewal/support follow the service contract.
6. Real sandbox acceptance only after a chosen panel/gateway exists and secrets are entered privately; then isolated UAT review, snapshot/history checks, real end-to-end payment/provision/readback/delivery. Production and paid rollout require separate acceptance. Benchmark actual latency then.

## Validation / rollout

Local 150 Python discovered: 145 PASS and 5 PostgreSQL skips; both DOM/Save suites PASS. New tests cover exact payment gate, invalid paid types, strict prices, wrong orders/references/currency, scoped operation IDs, safe checkout URLs, duplicate suppression, bounded checks, unknown response/no retry, masked errors and all demo modes. API tests forbid writes/vault/send/provider even with live flags true, enforce auth/roles/bot scope and redact invalid credential-bearing bodies. DOM tests cover explicit simulation notice, no action on Open, manual run, duplicate-click guard, stale-result clearing, inert URL/plain text and Close before late response. Updated real UI/HTTP/PostgreSQL test runs a sample without replacing the reply editor or adding configuration versions.

No migration is introduced. CI, exact PR/head/merge, deployment assets/auth and owner mobile demo acceptance must be recorded separately. Preserve prior #108–#111 live UAT evidence. This milestone is a prototype of the new direction, not completion of generic workflow design or live transactional commerce.
