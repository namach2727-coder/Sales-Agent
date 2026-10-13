# Production PostgreSQL backup and isolated Neon restore

Status: **tooling prepared; actual Production dump/restore NOT YET EXECUTED**. This is an operator procedure, never an automatic deployment step. Nothing here updates Render's production DATABASE_URL or connects the site to Neon.

## Preconditions

- Source: Render PostgreSQL Free, database \`directpilot_production_db\`, PostgreSQL 16, external URL from Render dashboard → Production DB → Connect. It is **not** the database's internal Render URL.
- Target: independent Neon project \`billowing-poetry-05589994\`, endpoint \`ep-super-moon-arziccng.c-4.us-west-2.aws.neon.tech\`, database \`neondb\`, PostgreSQL 18.
- Use a **trusted Windows PC**, local Python 3.10+, Docker Desktop (running) or PostgreSQL client tools v18.
- The Render database currently has an empty external IP allowlist; add **only the workstation's public IPv4 /32** temporarily through Render dashboard → Networking / Access Control. Do not enable 0.0.0.0/0. Remove the entry immediately after the operation. Do not copy URL, passwords, or dump files into chat, GitHub, terminal history or tickets.
- Use an encrypted local drive/folder for the archive; obtain owner approval for offsite encrypted copy. Keep archive strictly private: it includes PII, receipts, authorization tokens, and payment data.

## 1. Backup Render, on the operator's PC

Open PowerShell at repo root; credentials are entered locally with secure input and not pasted into shell history.

\`\`\`powershell
$secret = Read-Host "Render Production EXTERNAL database URL" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
  $env:DIRECTPILOT_RENDER_SOURCE_URL = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  Remove-Variable secret
}
python tools/production_db_transfer.py backup --client docker --folder "C:\DirectPilot-Private-Backups"
Remove-Item Env:DIRECTPILOT_RENDER_SOURCE_URL
\`\`\`

If the backup reports BLOCKED, **nothing has been restored or cut over**. Check allowlist and URL at the workstation, without sharing credentials. Retry locally only after resolving the cause.

Success requires an archive named \`directpilot-production-YYYYMMDDTHHMMSSZ.dump\`, companion \`*.manifest.json\`, SHA-256, and \`pg_restore --list\` PASS. The tool prints no credentials.

Take a second encrypted copy on storage independent of Render and the operator machine. **An unencrypted chat upload, public download link, or GitHub Actions artifact is forbidden.** Retain proof of checksum and backup creation time, but never attach the dump.

## 2. Isolated restore rehearsal — ONLY after backup is verified

The target MUST still have **0 user tables**. The script checks the exact independent Neon host and target name, insists on empty schema, and does not invoke --clean. It does not modify Render Production, UAT or live backend settings.

\`\`\`powershell
$secret = Read-Host "INDEPENDENT Neon Production DIRECT database URL" -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
  $env:DIRECTPILOT_NEON_TARGET_URL = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
} finally {
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
  Remove-Variable secret
}
python tools/production_db_transfer.py restore --client docker --archive "C:\DirectPilot-Private-Backups\directpilot-production-YYYYMMDDTHHMMSSZ.dump" --confirm-isolated-restore
Remove-Item Env:DIRECTPILOT_NEON_TARGET_URL
\`\`\`

Replace the archive filename with the actual file. Restore MAY fail when migrating PG16 → PG18 due to extension/role/compatibility differences. STOP and diagnose; do not switch the live connection or delete the source. The script uses a transaction to avoid partial DDL changes; if the target is no longer empty, a fresh isolated Neon branch/database is required for any repeat.

## 3. Post-restore acceptance criteria

- Tables, sequences, views, triggers, indexes, FK constraints and Alembic version verified.
- Independently reconcile row counts for users/tenants, subscriptions, order and receipt records, customer identities, admin payment cards, Meta account connections and idempotency references; never display secret values.
- Verify business rules including 3-day new trials, paid 30-day plans, multi-month orders, no missed invoices/receipts and no cross-tenant leakage.
- Run a separate read-only/offline backend compatibility smoke against Neon without changing the live Render environment; test version migration, SSL, connection pooling, suspend/wake behavior and CU-hour consumption.
- Plan final write freeze and last delta capture; first static backup is a DR rehearsal, **not a live synchronized replica**. Cutting over without a final consistent dump or replicated delta risks losing orders, payment approvals and Instagram events.
- Require independent encrypted backup, a tested restore, owner-approved cutover and rollback plan before switching Production DATABASE_URL.

Record only non-sensitive evidence in roadmap: timestamps, bytes, checksum prefix, row counts, PASS/FAIL, migration head, exact observed RPO and RTO. Never claim the data migration is complete until production read/write cutover has been explicitly approved and independently verified.
