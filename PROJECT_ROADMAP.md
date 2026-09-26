# DirectPilot Project Roadmap & Continuity Checkpoint

> **Purpose:** Canonical continuity document for DirectPilot. Read this before resuming work in a new chat/session.
>
> **Last updated:** 2026-09-26
>
> **Rule:** Update this file after every meaningful release, migration, architecture decision, commercial-policy change, or UAT milestone.

---

## 1. Product Direction

DirectPilot is evolving from Instagram automation/AI support into an **Instagram Sales Automation Platform**.

Current product pillars:

1. **Deterministic Automation**
   - Predefined rules/responses.
   - Exact deterministic matches must use **ZERO LLM**.
   - Own product family and commercial plan.

2. **AI Assistant**
   - Knowledge + AI response generation.
   - Own product family and commercial plan.
   - Independent from Automation.

3. **Commerce / Subscription**
   - Published paid plans.
   - Immutable order commercial snapshots.
   - Payment processing and subscription activation.

4. **Future Phase 2: Story Product Automation**
   - Story-specific product/offer context.
   - Price/product response tied to the exact Instagram Story.
   - This is intended to be a major differentiator.

### Runtime precedence

```text
Human Takeover
  -> Story-specific Automation   [Phase 2]
  -> General Automation
  -> AI Assistant fallback
```

Human Takeover always has highest precedence.

---

## 2. Repositories / Production

### Backend

- Local root:
  `C:\Users\q\Documents\Codex\2026-07-11\referenced-chatgpt-conversation-this-is-untrusted`
- GitHub:
  `namach2727-coder/Sales-Agent`
- Branch:
  `backend-main`
- Current remote/deployed backend baseline:
  `62e499834f173bcde9197e81b642633066ba4d1b`
- Commit message:
  `fix(commerce): snapshot order purchase terms`
- Render service:
  `directpilot-uat-api`
- Render URL:
  `https://directpilot-uat-api.onrender.com`

### Frontend

- Local root:
  `C:\Users\q\Documents\Web Site`
- GitHub:
  `namach2727-coder/directpilot-web`
- Branch:
  `main`
- Current production frontend baseline:
  `a019190f77c7a41bf8cfe78607e1fe3f760398fa`
- Production:
  `https://directpilot.ir`

### Architecture invariant

Browser API calls remain same-origin through:

```text
/api/v1/* -> Vercel rewrite -> Render /api/v1/*
```

Do **not** add:
- frontend catch-all proxy,
- unnecessary serverless functions,
- polling unless explicitly approved.

---

## 3. Core Product Invariants

These are non-negotiable unless explicitly redesigned:

- Automation exact match = **ZERO LLM / PromptBuilder / Knowledge / AI**.
- Automation and AI Assistant remain separate commercial product families.
- If both are available:
  - Automation first.
  - If deterministic match succeeds, stop.
  - Otherwise AI may handle fallback.
- Human Takeover supersedes both.
- Tenant/store isolation is mandatory.
- Commerce activation must use immutable order purchase terms.
- Never activate subscription from browser/frontend state.
- Backend is authoritative for payment and entitlement state.
- Never blindly retry an ambiguous external-provider write.
- Preserve unrelated dirty work; never reset/clean/force-push user work.

AI runtime baseline:

```text
LLM_PROVIDER=groq
GROQ_MODEL=qwen/qwen3.6-27b
GROQ_CONTEXT_LENGTH=4096
GROQ_MAX_OUTPUT_TOKENS=256
GROQ_REASONING_EFFORT=none
```

Do not increase context/output limits merely to hide defects.

---

## 4. Major Completed Milestones

### Instagram / AI / Automation foundation — COMPLETE

Completed and previously cloud-verified:

- Instagram OAuth.
- DM E2E.
- Story Reply E2E.
- Comment -> Private Reply E2E.
- Knowledge -> AI flow.
- Echo/loop prevention.
- Inbox / Human Handoff.
- Automation edit workflow.
- Deterministic Automation / AI separation.
- AI workspace.
- Admin/commercial foundation.
- Outbound delivery reconciliation.
- Admin payment review UI.
- AI request quota hard-cap enforcement.
- Admin customer endpoint N+1 timeout fix.

Important earlier backend commits include:

- `c6168e63ebf866e1052a9424f53b40cb0f0ebd88` — outbound delivery reconciliation
- `3868df07cc449292fbf607ffb0fb6676625d6252` — admin payment review backend
- `b9f0698d7715f47b80e52877c424dd31cc35c24e` — commerce quota enforcement
- `3c15c18d4bcd9c439a94c82b57174a8fbb7553a8` — admin customers N+1 fix
- `62e499834f173bcde9197e81b642633066ba4d1b` — order commercial snapshot hardening

### Frontend numeric-input drift bug — COMPLETE / RELEASED

Root cause:
focused native `input[type=number]` fields changed on mouse wheel.

Fix:
reusable controlled NumericInput prevents wheel mutation while preserving keyboard editing.

Released frontend commit:

`1e7eb6456710b93801aafb1fff433a721a0ba790`

---

## 5. Commercial Policy V1

### AUTOMATION_V1

```text
product_family = AUTOMATION
price = 4,900,000 IRR
duration = 30 days
display_order = 10
instagram_account_limit = 1
automation_limit = 20 TOTAL persisted rules
ai_reply_limit = 0
ai_request_limit = null
ai_token_limit = null
trial = false
active = true
purchasable = true
```

### AI_ASSISTANT_V1

```text
product_family = AI_ASSISTANT
price = 6,900,000 IRR
duration = 30 days
display_order = 20
instagram_account_limit = 1
automation_limit = 0
ai_reply_limit = 1000
ai_request_limit = 1000 per effective subscription period
ai_token_limit = null / unlimited
trial = false
active = true
purchasable = true
```

### Public catalog status

Production `GET /api/v1/plans` has been verified to expose exactly:

- `AUTOMATION_V1`
- `AI_ASSISTANT_V1`

Legacy plans remain non-purchasable and must not appear publicly.

Legacy/historical examples:

- START
- TRIAL
- PRO
- FREE / Forever Free
- AUTOMATION_TRIAL
- AI_ASSISTANT_TRIAL

Do not alter START or legacy compatibility behavior casually.

---

## 6. Commerce Snapshot Hardening — COMPLETE / RELEASED

### Problem found during controlled order UAT

Originally `SubscriptionOrder` stored only:

- plan relation
- price_amount
- currency

Checkout and payment activation reread mutable `SaasPlan` fields.

That meant later plan edits could alter historical purchase semantics.

### Fix

Migration:

`0018_order_commercial_snapshot.py`

New orders snapshot immutable purchase terms:

- plan_code
- plan_name
- product_family
- duration_days
- instagram_account_limit
- automation_limit
- ai_reply_limit
- ai_request_limit
- ai_token_limit
- price_amount
- currency

Payment/subscription activation for new orders uses these immutable order snapshots.

Backend release:

`62e499834f173bcde9197e81b642633066ba4d1b`

Frontend release:

`a019190f77c7a41bf8cfe78607e1fe3f760398fa`

Migration 0018 is deployed/current.

---

## 7. Controlled Commerce UAT Order

There is one intentional owner-controlled order used for UAT:

```text
Store: Iran Insurance
Plan: AUTOMATION_V1
Amount: 4,900,000 IRR
Status: pending
Payment: none
Subscription effect: none
```

This order was created before migration 0018, then safely remediated one-row-only.

Persisted snapshot now matches policy:

```text
plan_code = AUTOMATION_V1
plan_name = Automation
product_family = AUTOMATION
duration_days = 30
instagram_account_limit = 1
automation_limit = 20
ai_reply_limit = 0
ai_request_limit = null
ai_token_limit = null
price_amount = 4900000
currency = IRR
```

Do **not** create a replacement order unless there is a proven need.

This order is intended to be reused for the first controlled KPay UAT.

---

## 8. Manual Payment Flow

Current released manual flow:

```text
Order
 -> ManualPayment/card-transfer
 -> private receipt upload
 -> Admin review
 -> approve/reject with revision protection
 -> backend atomically activates subscription from order snapshot
```

Manual flow remains as fallback after KPay integration.

KPay payments must never:
- enter the manual approval queue,
- accept manual receipt upload,
- be manually approved/rejected.

---

## 9. KPay Integration — CURRENT ACTIVE WORK

### Business decision

KPay will become the **primary automated Rial payment path**.

Manual receipt/card-transfer remains explicit fallback.

### IMPLEMENT_KPAY_PAYMENT_GATEWAY_V1 status

Current local implementation status:

`PASS`

`KPAY_PROVIDER_CONTRACT_HARDENING = PASS`

Important: these KPay changes are currently local development work and are **not yet the production baseline**.

Implemented locally:

- additive KPay fields on existing `ManualPayment`
- migration:
  `alembic/versions/0019_kpay_payment_gateway.py`
- isolated KPay provider adapter
- documented transaction check adapter:
  `GET /transactions/check/{authority}`
- authenticated create endpoint:
  `POST /api/v1/payments/kpay`
- callback endpoint:
  `GET /api/v1/payments/kpay/callback/{payment_public_id}`
- status endpoint:
  `GET /api/v1/payments/kpay/{payment_public_id}`
- one local payment per order
- unique provider authority / provider transaction constraints
- ambiguous create state
- no blind retry after ambiguous timeout
- callback idempotency
- `is_paid` is the authoritative provider paid discriminator
- verify authority must match the persisted authority
- verify amount must equal immutable `SubscriptionOrder.price_amount`
- no dependency on `KPAY_PAID_STATUSES`
- immutable snapshot-based activation
- manual/KPay isolation
- frontend KPay payment action/result page

Migration 0019 has **not** been released/applied in production yet.

Final local validation:

- backend targeted: 46 passed
- backend full regression: 818 passed, 7 skipped
- frontend targeted: 6 passed
- frontend full regression: 136 passed
- frontend typecheck, lint, build, and backend/frontend diff checks: PASS
- implementation: **NOT DEPLOYED**
- real KPay secrets: **NOT CONFIGURED**
- controlled Iran Insurance order: **UNCHANGED**

### Current KPay architecture

Target flow:

```text
Published Plan
 -> SubscriptionOrder
 -> DirectPilot backend creates/reuses one local KPay payment
 -> POST KPay /transactions/create
 -> persist authority/provider metadata
 -> browser redirects to provider payment_url
 -> KPay returns to DirectPilot callback
 -> DirectPilot checks documented is_paid server-side
 -> DirectPilot verifies authority and amount server-side
 -> validate authority + exact amount + local ownership/invariants
 -> atomic payment finalization
 -> subscription activation from immutable order snapshot
 -> DirectPilot result page
```

Backend remains authoritative.

### Security

KPay secrets are backend-only.

Expected configuration family:

```text
KPAY_BASE_URL
KPAY_ACCESS_TOKEN
KPAY_SHOP_ID
KPAY_CARD_ID
KPAY_CALLBACK_BASE_URL
KPAY_FEE_SIDE
KPAY_TIMEOUT_SECONDS
KPAY_VERIFY_SEND_AUTH
KPAY_CHECK_SEND_AUTH
```

Do not place secrets in:
- chat,
- Codex prompts/output,
- Git,
- frontend,
- `NEXT_PUBLIC_*`,
- logs.

---

## 10. KPay Safety / Idempotency Rules

These rules must remain intact:

### Create

- Lock owned pending order/payment.
- One payment per order.
- Create local payment identity before external create.
- Repeated click after authority exists returns existing state.
- Do not call KPay create again after authority is persisted.

### Ambiguous create

If external create may have reached KPay but response is unavailable:

```text
CREATE_UNKNOWN
```

Then:

- no automatic recreate,
- no blind retry,
- no second local payment,
- require reconciliation.

Do not assume KPay factor_number is idempotent unless provider contract proves it.

### Callback

Callback is only a trigger.

Never trust callback-supplied:
- status,
- amount,
- order identity,
- tenant/store.

Resolve local payment first and verify server-side.

### Finalization

Subscription activation must be:
- backend-only,
- atomic,
- idempotent,
- based on immutable order snapshot,
- protected against repeated callback/verify.

---

## 11. Exact Current Next Step

The **next task** is:

`KPAY_V1_RELEASE_AND_DEPLOY`

Reason:

The provider contract hardening and all local validation gates have passed.
The reviewed backend and frontend changes must now be committed and pushed,
then migration 0019 and the exact revisions can be deployed and verified in a
separate authorized release task.

### Gate

Do **not** configure real KPay credentials until:

```text
READY_FOR_KPAY_CONFIGURATION = YES
```

After that:

1. configure real KPay secrets directly in Render,
2. do a provider contract probe,
3. perform controlled KPay UAT using the existing Iran Insurance / AUTOMATION_V1 order,
4. verify create -> payment_url -> check/verify -> activation,
5. only then release/declare KPay complete.

---

## 12. Known KPay Provider Questions

Do not silently invent answers if still unresolved:

- whether verify requires Bearer auth in the real account behavior,
- whether check requires auth,
- exact real create/verify response behavior,
- transaction expiry behavior,
- ambiguous-create recovery/lookup support,
- duplicate-create behavior,
- error/retry contract,
- callback signature/authenticity support.

Provider uncertainty must remain isolated inside the KPay adapter.

---

## 13. Customer-Reality Audit / Market-Signal Note

Do not interpret current UAT database accounts as proven traction.

Known ground truth:

- `Iran Insurance` is owner-controlled/internal test.
- One repository-matched account was proven automated/test.
- One additional account was strongly likely test.
- Most remaining historical UAT registrations could not be proven external or test because creator provenance was not retained sufficiently.

Therefore:
- do not claim UAT store count as real market demand,
- future production signup analytics should record better provenance.

This is a product analytics issue, not a blocker for current engineering work.

---

# Phase 2 — Story Product Automation

This feature is deliberately deferred until current Commerce/KPay Phase 1 is closed.

## Product concept

A page owner should be able to tell DirectPilot:

> For this exact Instagram Story, this is the product/offer and this is the price/response.

Examples:

- Story A -> refrigerator model X -> price A
- Story B -> Sony TV model Y -> price B
- Story C -> another product -> its own offer

When a customer replies to that exact Story, DirectPilot should return the correct commercial response for that Story.

## Phase 2 V1 scope

Create a Story-specific mapping such as:

```text
Instagram Story
 -> internal product/offer title
 -> price
 -> deterministic response
 -> optional CTA
 -> enabled/disabled
 -> expiry aligned with Story lifecycle where practical
```

### Runtime rule

Story-specific commercial data must be deterministic.

Prices must **not** be hallucinated or inferred by LLM.

Preferred execution:

```text
Human Takeover
 -> Story-specific Automation
 -> General Automation
 -> AI Assistant
```

Story-specific deterministic match = ZERO LLM.

## Phase 2 later expansion

- Product Catalog
- SKU
- centralized current price
- inventory/availability
- reusable product across multiple Stories
- offer/version history
- Story analytics
- conversion analytics

Target long-term sales flow:

```text
Story Reply
 -> Product/Offer context
 -> Price / CTA
 -> Order
 -> KPay
 -> Payment
 -> Subscription/order fulfillment logic as applicable
```

This is a strategic differentiator: DirectPilot should evolve from a reply bot into an Instagram sales automation system.

---

# Phase 3 — Possible Future Expansion

Not approved for implementation yet:

- Full product catalog / inventory sync
- SKU-level offer management
- Story-to-checkout purchase flow
- richer sales attribution
- conversion funnel analytics
- external commerce/inventory integrations

Do not implement Phase 3 opportunistically during Phase 1 or 2 fixes.

---

## 14. Release / Development Discipline

For every substantial task:

1. Read repository `AGENTS.md` and relevant scoped AGENTS.
2. Search narrowly with `rg` / `git grep`.
3. Do not scan generated/build/cache/venv/node_modules.
4. Preserve dirty user work.
5. Targeted tests first.
6. Full regression once at release gate.
7. Do not deploy before local validation passes.
8. Backend/migrations before frontend when API compatibility requires it.
9. Verify exact deployed revision.
10. Verify `/live` and `/ready`.
11. Update this roadmap/checkpoint after successful release.

Known unrelated frontend dirty files to preserve:

- `components/instagram-callback.tsx`
- `lib/api/instagram.ts`
- `tests/profile-instagram-timeout.test.mjs`

Known unrelated backend dirty paths to preserve:

- `tests/test_customer_final_uat_api.py`
- `.uat-temp/`

---

## 15. How to Resume in a New Chat / Codex Session

Start with:

> Read PROJECT_ROADMAP.md first. Treat it as the current DirectPilot continuity checkpoint. Inspect the real repository before making changes. Do not repeat completed work. Resume from the section **Exact Current Next Step** unless the repository proves the roadmap is stale.

Then verify:

- backend branch/HEAD,
- frontend branch/HEAD,
- deployed Render revision,
- deployed Vercel revision,
- migration head,
- local dirty work.

If repository reality conflicts with this document, repository/runtime evidence wins and this file must be updated.

---

## 16. Immediate Resume Marker

```text
CURRENT_PHASE:
Phase 1 — Commerce / KPay

CURRENT_TASK:
KPAY_V1_RELEASE_AND_DEPLOY

PRODUCTION_BACKEND_BASELINE:
62e499834f173bcde9197e81b642633066ba4d1b

PRODUCTION_FRONTEND_BASELINE:
a019190f77c7a41bf8cfe78607e1fe3f760398fa

LATEST_PRODUCTION_MIGRATION:
0018_order_commercial_snapshot

LOCAL_UNRELEASED_MIGRATION:
0019_kpay_payment_gateway

KPAY PRODUCTION STATUS:
NOT RELEASED

REAL KPAY CREDENTIALS:
NOT YET CONFIGURED FOR THIS IMPLEMENTATION

CONTROLLED UAT ORDER:
Iran Insurance / AUTOMATION_V1 / 4,900,000 IRR / pending / no payment

PHASE 2:
Story Product Automation — defined, not started
```

---

## 17. Completion Definition for Current Phase

Phase 1 Commerce/KPay is complete only when all of the following are true:

- KPay provider contract hardening PASS.
- Full backend/frontend test gates PASS.
- KPay code committed and pushed cleanly.
- Migration 0019 safely deployed/current.
- Real Render KPay configuration added without secret exposure.
- Controlled create contract verified.
- Existing controlled Automation order enters KPay exactly once.
- Payment URL works.
- Provider paid state is verified server-side.
- Amount exactly matches immutable order.
- Callback replay is idempotent.
- Subscription activates exactly once from immutable order snapshot.
- Manual payment fallback remains intact.
- No KPay payment can enter manual admin approval.
- Production health and customer UI smoke PASS.
- This roadmap is updated with final commits/releases.

Only after this should implementation focus move to Phase 2.
