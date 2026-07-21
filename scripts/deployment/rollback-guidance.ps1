$ErrorActionPreference = "Stop"
Write-Output @"
Safe rollback procedure:
1. Remove the failed application revision from traffic.
2. Do not run an automatic Alembic downgrade.
3. Deploy the previous image only when the schema is backward compatible.
4. Otherwise deploy a forward-fix migration and image.
5. Restore into a new database and smoke-test before switching traffic when data recovery is required.
See docs/operations/deployment-runbook.md.
"@
python -m tools.check_database
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
