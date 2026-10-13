# DirectPilot restored Neon — read-only application preflight

> **Status: the source-code tool is prepared, but the workstation execution against restored Neon has not yet been performed.** This is NOT a cutover.

## Safety contract

- **Allowed source of data:** ONLY Neon project `billowing-poetry-05589994`, host `ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech`, database `neondb`.
- **Never connect:** Render Production Postgres or isolated Neon UAT; no application routing/environment/credentials are changed.
- This tool performs schema, revision, SQLAlchemy psycopg connection and aggregate business-integrity checks under **server-enforced default read-only transactions**; it does **not** start FastAPI, Meta, payment integrations, scheduler or migration/seed scripts.
- Do **not** run the full `pytest` suite against restored Neon: its test fixtures delete/insert records and target a dedicated database named `*_test`. Use the disposable PostgreSQL 18 GitHub CI workflow for write-path tests instead.
- Actual restore was a snapshot captured 2026-10-13 10:42:36 UTC. Subsequent Render Production writes are not replicated. Passing this preflight DOES NOT prove current-data parity or authorize live cutover.

## On a trusted operator workstation

1. Obtain the Neon **direct (not pooled)** connection URL from the `directpilot-production` project and keep it private. Do not put it in code, chat, GitHub, saved shell history or CI. Requires access to the repository branch containing `tools/neon_readonly_preflight.py`.
2. Make sure the project's Python environment has the repository `requirements.txt` packages installed.
3. From the repository root in PowerShell, execute:

```powershell
python -m tools.neon_readonly_preflight
```

4. The script prompts privately for the direct connection URL (hidden). If non-interactive, set `DIRECTPILOT_NEON_READONLY_URL` securely **only in the current operator process**, execute the script, then remove the variable. Do not print the variable or the URL.
5. Only share the sanitized PASS/FAIL report. No raw records, access tokens, email addresses, full URLs or customer content should be exported.

Expected known objects: 82 tables, 76 sequences, 522 indexes, 427 non-NOT-NULL constraints, Alembic `0025_trial_three_days`. Critical FK/index integrity, 3-day trial policy, orphan order/payment/tenant references and subscription-period sanity must PASS.

## Caveats / remaining gates

- The target is an isolated sensitive Production copy; use SQL reads only. Session is read-only; it is NOT an authorization to try payment approvals, user logins, or other stateful app actions.
- Running this script does not enable Neon usage monitoring, configure pooling, validate cold-start under traffic or prove the backed-up encrypted tokens are decryptable using intended production keys.
- After this preflight, independently measure Free-plan CU-hour usage via Neon Console; current project API returns `compute_time_seconds=0` despite observed queries, so not enough for capacity acceptance.
- Maintain an offsite encrypted recoverable backup and prepare maintenance-window final snapshot/delta, rollback/split-brain strategy, webhook replay and monitored cutover before modifying live DATABASE_URL.
