$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "The project Python environment was not found. Set up the project first."
}

Push-Location $projectRoot
try {
    & $pythonPath -m app.telegram_polling
}
finally {
    Pop-Location
}
