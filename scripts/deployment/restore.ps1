param(
    [Parameter(Mandatory=$true)][string]$BackupFile,
    [switch]$ConfirmDestructiveRestore
)
$ErrorActionPreference = "Stop"
if (-not $ConfirmDestructiveRestore) { throw "Use -ConfirmDestructiveRestore to acknowledge destructive restore" }
if (-not $env:RESTORE_DATABASE_URL) { throw "RESTORE_DATABASE_URL is required" }
& pg_restore --list $BackupFile | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& pg_restore --exit-on-error --clean --if-exists --no-owner --no-privileges --dbname=$env:RESTORE_DATABASE_URL $BackupFile
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
$previousDatabaseUrl = $env:DATABASE_URL
$env:DATABASE_URL = $env:RESTORE_DATABASE_URL
python -m tools.check_database
$env:DATABASE_URL = $previousDatabaseUrl
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "Restore completed; run migrations and deployment smoke tests before traffic is enabled."
