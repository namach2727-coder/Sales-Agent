$ErrorActionPreference = "Stop"
python -m tools.validate_environment
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m tools.check_database
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
python -m tools.run_migrations
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$hostAddress = if ($env:HOST) { $env:HOST } else { "0.0.0.0" }
$portNumber = if ($env:PORT) { $env:PORT } else { "8000" }
$workers = if ($env:WEB_CONCURRENCY) { $env:WEB_CONCURRENCY } else { "2" }
$forwarded = if ($env:FORWARDED_ALLOW_IPS) { $env:FORWARDED_ALLOW_IPS } else { "127.0.0.1" }
python -m uvicorn app.main:app --host $hostAddress --port $portNumber --workers $workers --proxy-headers --forwarded-allow-ips $forwarded --no-access-log
