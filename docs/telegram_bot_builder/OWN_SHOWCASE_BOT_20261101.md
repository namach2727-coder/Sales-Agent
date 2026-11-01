# DirectPilot own portfolio and custom-bot inquiry service — 2026-11-01

## Authoritative product pivot

Owner explicitly retired the customer-facing generic no-code builder direction and requested OUR OWN Telegram bot: show business use cases, let prospects select a category and describe a need, notify the owner, then scope/build each project with the owner. This supersedes the former next steps in the transactional-service prototype runbook and builder roadmaps. No further generic workflow designer/payment/panel engine work is the current priority. Historical code, configuration versions, acceptance records and deployments remain preserved, not deleted or rewritten.

Service name: DirectPilot Bot Studio / ساخت ربات اختصاصی. It is a custom development service, not an AI agent or instant universal bot generator. The bot itself is a working example of guided service discovery and inquiry collection. Example paths are fictional demonstrations, never actual bookings, checkout, payments or provisioning. No invented clients, case studies, prices, delivery times or fractional-second claims.

## Visitor journey and content

Public /showcase provides a Persian RTL mobile-first portfolio with a clear service proposition, 24 searchable categories, accessible category dialogs, explicit simulated interactions, process explanation and links into the Telegram bot using /start idea_<category>. The site does not accept anonymous inquiry POSTs; visitors continue in Telegram. Link is exposed only for one enabled active showcase bot. If absent, ambiguous or unavailable, request links fail closed with an honest notice.

Categories cover retail, food, beauty, clinic information/appointments (no diagnosis), education, digital services/VPN, real estate, travel, accommodation, fitness, repairs, automotive, distribution, manufacturing, consulting/legal, accounting, events, media, recruitment, logistics, pets, charity, technology and another idea. This is a curated starting catalog, not a claim to cover every possible business or API.

Telegram: /start -> home -> 4 pages of categories (6/page, 2 columns) -> relevant ideas -> interactive demo or request -> description (10–1200 characters) -> optional contact (2–120; use current Telegram instead) -> review/consent -> explicit Confirm -> durable inquiry code. No password/token collection, no payment or automatic price promise. Home/Cancel restart; Edit returns to description; session idle expiry is 24h; no inquiry saved before Confirm. At most 5 confirmed inquiries/user/bot/day. Stored state survives process restarts. Telegram reply keyboards are client-rendered; no claim of arbitrary styling inside native Telegram.

## Runtime and privacy

TELBOT_SHOWCASE_ENABLED defaults OFF. Only an explicit tenant+bot showcase_settings record can divert that bot from preserved legacy keyword replies. Tenant must be active; bot must be active with current encrypted credential; own registered owner must remain active owner. Private user==chat only, not groups/bots. Existing webhook secret/unique update receipt and bot Pause gates remain. Own showcase uses deterministic content and no LLM/external API action.

Migration 0004 is additive: showcase_settings, showcase_sessions, showcase_inquiries, showcase_deliveries with composite tenant/bot FKs, scoped uniqueness and indexes. Session state, inquiry payload and delivery payload use Fernet ciphertext and existing isolated key; do not print keys, decrypt customer content into tool output or commit real inquiries. Existing inbound_updates still stores inbound message text under prior policy; encryption of new records is NOT a claim that all historical/inbound data is encrypted. No automated deletion policy is introduced. Access review, retention policy and independent recovery remain commercial rollout work.

State, immutable confirmed inquiry and outbound reservations commit atomically BEFORE Telegram sends. Source update uniqueness and monotonic session update IDs suppress duplicates/out-of-order steps; a repeated Confirm after completion does not create another inquiry. Send outcomes are sent/rejected/unknown; unknown attempts are not blindly retried. A crash between webhook receipt and flow processing may lose that step; user can restart. A crash after inquiry commit cannot erase the inquiry, but can leave an unacknowledged notification. No exactly-once or guaranteed notification delivery claim.

Owner notification destination comes only from the bot's registered owner, never request input. Inquiry is saved even if notification is rejected/uncertain. Owner-only tenant+bot inbox lists last 30 with delivery status and no-store; editor/viewer/foreign tenant cannot read. User acknowledgment says stored, not that Telegram notification delivery was guaranteed. Native customer contact links may be constrained by Telegram privacy; provided contact and durable code remain visible to owner.

## Rollout and evidence gates

1. Local Python/domain/auth/DOM tests; actual PostgreSQL CI migration, full persistent chat flow, duplicate Confirm/webhook, notification timeout, encrypted storage and owner-only inbox.
2. Exact reviewed PR/head/tree and all required CI; merge only isolated TelBot branch. Preserve Instagram backend/site unrelated work.
3. Apply checked-in 0004 only verified Neon TelBot UAT; record baseline parity. Enable ONE verified owner test bot, keep legacy configuration snapshots unchanged. Set only own-showcase runtime flag; keep external API actions OFF.
4. Require exact UAT deployment/alias/assets, health, private inbox auth and public catalog/deep link.
5. Website /telbot content must describe custom bot development, replace proposed subscription pricing/checkout with inquiry links, and link to actual enabled showcase. Targeted website release uses its own repository/branch/review; do not merge unrelated backend or UAT history.
6. Owner native acceptance: /start, page navigation, sample, need/contact/review/edit/cancel/Confirm, acknowledgment code and owner Telegram notification + inbox. Physical phone styling/keyboard and real Telegram delivery remain unverified until reported/observed.

At source checkpoint code/local validation are separate from pending CI, schema deployment, live activation, website release and owner acceptance. Test username tetsteee1bot was observed read-only as the sole active UAT child with ready credential and active registered owner. Reusing this existing owner test bot preserves its historical keyword config; it does not create a newly named BotFather account. Professional username/profile branding must be finalized before presenting it as a finished public brand. Do not fabricate a BotFather rename or claim a new Telegram account was created.
