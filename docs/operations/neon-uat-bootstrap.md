# Neon UAT database schema bootstrap (2026-10-12)

## Scope

Target: Neon project `directpilot-uat-v2`, DB `neondb`, role `neondb_owner`, approved direct Oregon endpoint.
This first run creates **schema only** using the current backend Alembic head. It does not copy Production user accounts, payment transactions, receipts, sessions, or Meta integration records. It does not change either Render service.

## Before execution

1. Keep Render UAT API connected to its old URL, but **do not use UAT for write tests** while it shares the Production database.
2. Keep Production database, the UAT-to-Production Meta OAuth/Webhook relay endpoints, and all Render settings untouched.
3. Copy the **non-pooled** Neon database connection from the Connect dialog. Do **not** paste it in chat, PRs, issues or logs.
4. Add it directly to the GitHub Actions repository secret named `NEON_UAT_DIRECT_DATABASE_URL` in repository Settings > Secrets and variables > Actions.
5. On GitHub Actions, select workflow **Initialize dedicated Neon UAT schema** and enter confirmation `directpilot-uat-v2`.
6. Run action **preflight** first. Verify it reports target `neondb`, `tables=0`, and `PREFLIGHT PASS`.
7. Only after preflight passes, run **migrate** and check `MIGRATION PASS` with Alembic head.

The runner hard-blocks any host other than the exact known Neon UAT direct endpoint; it also rejects any other database, role, unencrypted TLS, pooled endpoint, or non-empty target. Credentials are never printed.

## Follow-up gates (not covered by this workflow)

- Seed only public/system reference catalog into Neon; adjust UAT trial/AI plan metadata after isolation.
- Set up a separate UAT administrator by a secure one-shot action, not by copying Production password/session records.
- Decide which actual Production business data are required and sanitize them before import. An unfiltered full Production dump must **not** become a live UAT database.
- On migration cutover, change `DATABASE_URL` of **`directpilot-uat-api` only**, confirm unique DB identity, migrations, app readiness, login and plan operation.
- Meta OAuth/Webhook requests currently arrive at the UAT Render service and are relayed to Production. **Do not switch UAT database until relay continuity and token state have been assessed.** The URL of the UAT relay and its keys should not change.
- Collect evidence Production database remains untouched; do not claim environment isolation before runtime verification.
