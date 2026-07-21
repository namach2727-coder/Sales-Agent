$ErrorActionPreference = "Stop"
python -m tools.validate_environment
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
