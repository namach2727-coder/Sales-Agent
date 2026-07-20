$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$examplePath = Join-Path $projectRoot ".env.example"
$envPath = Join-Path $projectRoot ".env"

if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath $examplePath -Destination $envPath
}

$secureToken = Read-Host "Paste the BotFather token (the value will stay hidden)" -AsSecureString
$tokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
try {
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPointer)
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPointer)
}

if ([string]::IsNullOrWhiteSpace($token) -or $token -notmatch "^[0-9]+:[A-Za-z0-9_-]+$") {
    throw "The token format is invalid. Copy it directly from BotFather."
}

$randomBytes = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $rng.GetBytes($randomBytes)
}
finally {
    $rng.Dispose()
}
$webhookSecret = [Convert]::ToBase64String($randomBytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")

$content = [IO.File]::ReadAllText($envPath)
function Set-DotEnvValue {
    param(
        [string]$Content,
        [string]$Key,
        [string]$Value
    )
    $pattern = "(?m)^" + [regex]::Escape($Key) + "=.*$"
    if ([regex]::IsMatch($Content, $pattern)) {
        return [regex]::Replace(
            $Content,
            $pattern,
            [Text.RegularExpressions.MatchEvaluator]{ param($match) "$Key=$Value" }
        )
    }
    return $Content.TrimEnd() + [Environment]::NewLine + "$Key=$Value" + [Environment]::NewLine
}

$content = Set-DotEnvValue $content "TELEGRAM_BOT_TOKEN" $token
$content = Set-DotEnvValue $content "TELEGRAM_WEBHOOK_SECRET" $webhookSecret
$content = Set-DotEnvValue $content "TELEGRAM_SEND_ENABLED" "true"
$content = Set-DotEnvValue $content "TELEGRAM_POLLING_ENABLED" "true"
[IO.File]::WriteAllText($envPath, $content, [Text.UTF8Encoding]::new($false))

$token = $null
Write-Host "Telegram settings were saved locally in .env without displaying the token."
Write-Host "Restart the main app once, then run scripts\start_telegram.ps1."
