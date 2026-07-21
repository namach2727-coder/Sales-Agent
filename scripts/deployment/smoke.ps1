$ErrorActionPreference = "Stop"
python -m tools.deployment_smoke @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
