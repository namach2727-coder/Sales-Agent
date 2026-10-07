# DirectPilot Decisions

> Read after `AI_HANDOFF.md` and `PROJECT_ROADMAP.md`.
> Last reconciled: 2026-10-07.
> These decisions remain fixed unless new verified technical or product evidence justifies a change.

## Continuity and Evidence

- `AI_HANDOFF.md` is the primary cross-chat continuity authority.
- Chat history is not the project Source of Truth.
- Read continuity files in this order:
  1. `AI_HANDOFF.md`
  2. `PROJECT_ROADMAP.md`
  3. `DECISIONS.md`
  4. `CURRENT_STATE.md`
  5. `NEXT_ACTIONS.md`
- Evidence precedence is: verified runtime/deployment evidence > deployed commit > repository source > continuity documents > old chat history.
- Never mark PASS/DONE without evidence.
- Repository HEAD and deployed runtime commit are separate facts.
- Documentation-only commits must never be described as deployed runtime code.
- After a meaningful Production release, update the five continuity files only after Production verification passes.

## Architecture

- Backend: FastAPI + SQLAlchemy + Alembic + PostgreSQL.
- Keep a Modular Monolith for MVP; do not introduce microservices opportunistically.
- Official Meta APIs only.
- Tenant/store isolation is mandatory and server-side.
- Browser API traffic remains same-origin under `/api/v1/*`.
- Cloud backend selection remains server-side through `DIRECTPILOT_API_UPSTREAM`; never expose backend secrets through `NEXT_PUBLIC_*`.
- Public UUID-style IDs remain API boundaries; internal numeric IDs are persistence details.
- Migrations are additive/forward-only unless an explicit migration plan says otherwise.
- Do not add unnecessary frontend catch-all proxies, serverless functions, or polling.

## Runtime Precedence and AI

```text
Human Takeover
  -> Story-specific Automation [future]
  -> General Deterministic Automation
  -> AI Assistant fallback
```

- Human Takeover suppresses both automation and AI.
- Exact deterministic automation matches perform ZERO LLM, PromptBuilder, knowledge retrieval, or AI usage.
- AI execution requires entitlement.
- Preserve deduplication, echo prevention, and loop protection.
- Keep `GROQ_CONTEXT_LENGTH=4096` and `GROQ_MAX_OUTPUT_TOKENS=256` unless a separately justified change is approved.

## Authentication and Session UX

- Authentication state is server-authoritative.
- Browser auth uses the existing HttpOnly session-cookie contract; do not move auth tokens into localStorage or sessionStorage.
- A valid session must survive normal refresh/navigation and be restored through `/auth/me`; repeatedly asking for a password while the server session is valid is not an accepted UX.
- Authenticated customer routing resolves to `/dashboard`; authenticated platform administrators resolve to `/admin`.
- Unauthenticated protected customer/admin routes must redirect to `/login` without loops.
- Login CTA must not remain visible after authentication.
- Customer and platform-admin workspaces must expose a real backend logout action.
- Authenticated password change requires the current password, enforces backend policy, and revokes all sessions.
- Session-management UI must never expose raw session tokens.
- Forgot-password/self-service recovery remains BLOCKED until a verified email/SMS recovery delivery provider and secure token lifecycle exist. Do not ship a fake or UI-only reset flow.

## Frontend Release Discipline

- UX/Auth changes are accepted in UAT before Production promotion.
- Promotion should use the exact UAT-approved change set; do not insert unrelated feature changes between UAT acceptance and Production.
- The accepted Frontend UX/Auth release is `1f82494f87fe39f0fb2e22043adfd75f7735668c`.
- The accepted Backend Auth/Session release is `84b7df6196fe380fad21a3791e3160840c098602`.
- UAT and Production smoke evidence must be kept distinct; an untested criterion is NOT_TESTED/BLOCKED, not FAIL.

## Commerce

- Backend is authoritative for plan, entitlement, payment, subscription, and activation state.
- Frontend/browser state must never activate a subscription.
- Activation uses immutable purchase/order snapshots.
- Never blindly retry an ambiguous external-provider write.
- Current verified V1 sale scope is `AUTOMATION_V1`.
- `AUTOMATION_TRIAL` and `AI_ASSISTANT_TRIAL` are trials and are not purchasable.
- Legacy FREE/TRIAL/START/PRO plans are not public purchasable plans.
- Do not publish a paid AI Assistant plan unless a new explicit product decision and verified source/runtime change establishes it.
- Payment-provider source/routes are not equivalent to real provider acceptance.

## Environment and Infrastructure

- UAT/Production environment separation is complete and must not be rebuilt without regression evidence.
- Production and UAT use independent runtime configuration/secrets.
- Render backend auto-deploy remains OFF.
- No paid infrastructure/resource may be created without explicit owner approval.
- Current Free Production PostgreSQL is pilot infrastructure only; real-customer durability requires replacement/upgrade plus backup/restore acceptance.
- Production database external access controls must not be weakened merely for inspection.

## Security and Operations

- Never write secret values to Git, chat, logs, screenshots, or frontend public variables.
- Credential documentation records names, locations, and verification status only.
- Production administrator bootstrap/reset credentials remain outside Git and logs.
- Preserve unrelated local dirty work. Never reset, clean, auto-stash, force-push, rebase published history, or rewrite history automatically.
- A Git push is not deployment acceptance; correlate each deployed runtime with its exact commit SHA and verify runtime evidence.

## Shared Meta App Pilot Decision

- For the current pilot, Production and UAT may use the same Meta App credentials.
- Meta Developer settings are currently inaccessible to the owner; therefore the approved pilot workaround is a guarded UAT -> Production relay bridge.
- The provider-facing OAuth redirect intentionally remains the already-registered UAT callback:
  `https://directpilot-uat-api.onrender.com/api/v1/integrations/instagram/callback`.
- Production OAuth requests use that same provider redirect but prefix newly generated state with `production.`.
- UAT may relay only callbacks whose state matches the configured `production.` prefix to:
  `https://directpilot-api.onrender.com/api/v1/integrations/instagram/callback`.
- Production owns and consumes its own OAuth state and stores its own encrypted token/connection; UAT must never consume/copy Production OAuth state or encrypted connection rows.
- UAT webhook relay may be enabled only after Production OAuth has established the matching Production connection.
- Webhook relay must validate the original Meta HMAC signature before forwarding, preserve exact raw bytes/signature/delivery identifiers, avoid internal retries, and fail closed so Meta can retry.
- Production must not have relay targets configured; validated Production settings reject that topology to prevent relay loops.
- Production `META_SEND_ENABLED` remains false until inbound routing is proven and the pilot account allowlist is explicitly restricted.
- Secret values stay outside Git/chat/logs/docs. Production and UAT retain independent `INSTAGRAM_TOKEN_ENCRYPTION_KEY` values.
- If the owner later regains Meta Developer access, the preferred steady-state design is direct Production callback/webhook registration; the relay is a controlled pilot bridge, not a permanent architectural requirement.
- If simultaneous independent live webhook delivery is required in both environments, use separate Meta Apps rather than broad relay/multiplexing.

## SEO and Search Indexing

- Production `https://directpilot.ir` is the only indexable DirectPilot web environment.
- Vercel Preview/UAT must remain `noindex, nofollow`; preview robots must block crawling and preview sitemap output must remain empty.
- SEO copy must match backend-authoritative product facts. Do not advertise “Free Forever” while the active Automation trial is 14 days with up to 3 automations and one Instagram account.
- Prefer optimizing pages already receiving Search Console impressions before creating large volumes of new content.
- Keep one primary commercial owner per important keyword cluster to reduce cannibalization.
- Search Console deployment acceptance and ranking acceptance are separate: successful deployment does not imply immediate recrawl or ranking improvement.
- The baseline for SEO Phase 1 is the settled 28-day period through 2026-10-04: 14 clicks, 315 impressions, 4.44% CTR, average position 40.30.
- SEO Phase 2 accepted SHA is `4a1f8bb1812ce942e055c7f2c810f7d719939ab8`; live Production audit is clean on the five priority SEO pages.
