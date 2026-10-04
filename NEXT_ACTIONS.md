# DirectPilot Next Actions

> Execution queue. Read `AI_HANDOFF.md` first.
> Last reconciled: 2026-10-04.

## P0 — Production Regression After Environment Split

Status: **PARTIAL**

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

### Next Exact Checks

1. Verify live Production same-origin `https://directpilot.ir/api/v1/plans`.
   - Confirm the response matches the current intended public catalog.
   - Do not rely only on seed logs.
   - Do not expose credentials in chat or Git.
   - Do not create payment/subscription state just to prove auth.
2. Verify Production same-origin API routes resolve to Production, not UAT.
3. Verify observable Production data does not appear in UAT.
4. Verify observable UAT data does not appear in Production.
5. Reverify authoritative Vercel Production/UAT deployment SHAs and routing.
6. Only after the above evidence is complete, mark `PRODUCTION_REGRESSION_AFTER_ENVIRONMENT_SPLIT` PASS.

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
