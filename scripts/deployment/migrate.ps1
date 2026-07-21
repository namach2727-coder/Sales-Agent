$ErrorActionPreference = "Stop"
python -m tools.run_migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
