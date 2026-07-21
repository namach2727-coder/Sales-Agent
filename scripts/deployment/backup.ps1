param([string]$BackupDirectory = ".\backups")
$ErrorActionPreference = "Stop"
if (-not $env:DATABASE_URL) { throw "DATABASE_URL is required" }
New-Item -ItemType Directory -Force -Path $BackupDirectory | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$target = Join-Path $BackupDirectory "sales-agent-$stamp.dump"
& pg_dump --format=custom --compress=9 --no-owner --no-privileges --file=$target $env:DATABASE_URL
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& pg_restore --list $target | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "Backup created and validated: $target"
