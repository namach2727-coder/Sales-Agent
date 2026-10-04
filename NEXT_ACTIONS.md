# DirectPilot Next Actions

> Execution queue. Read `AI_HANDOFF.md` first.
> Last reconciled: 2026-10-04.

## P0 — Production Regression After Environment Split

Status: **PASS**

### Already Verified — Do Not Repeat Without Regression Evidence

- Production Render backend: LIVE.
- Production deployed runtime SHA: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`.
- Production `APP_ENV=production`.
- Production PostgreSQL connectivity.
- Production migration startup/current-head verification.
- Production application startup.
- UAT Render backend: LIVE.
- UAT deployed runtime SHA: `8bce8aee595c3b3f21bb69ecf47a082a19d11498`.
- UAT `APP_ENV=uat`.
- UAT database connectivity/startup.
- UAT/Production environment-separation milestone: PASS.
- GitHub access to backend and frontend repositories: PASS.
- One-shot Production Super Admin password reset/unlock: PASS; reset flag disabled and temporary values cleared.
- Production Super Admin browser login and `/admin` access: PASS.
- Production same-origin `/api/v1/plans`: PASS; current public response exposes only intended `AUTOMATION_V1` catalog.
- Production/UAT observable data isolation: PASS; catalogs differ and use different public IDs, proving they do not resolve to the same catalog/database.

### Completed Acceptance

- Production Super Admin login and `/admin`: PASS.
- Production same-origin public plans: PASS.
- Production/UAT observable data isolation: PASS.
- Vercel Production/UAT deployment branches and SHA: PASS.
- Vercel environment-scoped upstream configuration: PASS without decrypting secret values.

P0 is complete. Do not repeat unless a related deployment/configuration change or regression evidence requires it.

## P1 — Integration Credential Separation

After P0:

- `META_OAUTH_ENVIRONMENT_SPLIT`
  - verify Production vs UAT callback URLs,
  - verify environment-specific Meta credentials/configuration without printing values,
  - reaccept OAuth/webhook behavior only where environment changes can affect it.

- `LLM_ENVIRONMENT_VERIFICATION`
  - verify selected provider/model configuration by environment,
  - verify keys remain backend-only,
  - preserve AI guardrails.

- `PAYMENT_PROVIDER_ENVIRONMENT_SPLIT`
  - verify UAT sandbox vs Production provider base URLs,
  - verify callback bases,
  - verify provider credentials/configuration without printing values,
  - keep real provider transaction acceptance as a separate gate.

## P1 — Production Durability Before Real Customers

- `PRODUCTION_DATABASE_DURABILITY`
- `BACKUP_RESTORE_ACCEPTANCE`

Constraints:

- Current Free Render Production PostgreSQL expires 2026-11-02.
- Do not onboard real customers before durability is solved.
- Do not create/upgrade paid infrastructure without explicit owner approval.
- Establish backup/restore acceptance before durable customer use.

## P2 — Payment Acceptance

- Run controlled provider acceptance only after environment configuration is verified.
- Source route presence is not provider acceptance.
- Never blindly retry ambiguous external-provider writes.
- Review high-risk card/payment data handling before real-customer launch.

## P2 — Future Product Work

Story Product Automation remains deferred until the current Production/integration/payment readiness gates are closed.

Do not implement Story Product Automation opportunistically during readiness work.
