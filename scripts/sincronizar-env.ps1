#Requires -Version 5.1
<#
.SYNOPSIS
  Propaga o .env mestre da raiz para bot/, web/ e engine/zairyx/.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$Master = Join-Path $Root ".env"

if (-not (Test-Path $Master)) {
    throw "Arquivo mestre ausente: $Master. Copie .env.example para .env e preencha."
}

function Read-EnvMap([string]$path) {
    $map = [ordered]@{}
    foreach ($line in Get-Content $path -Encoding UTF8) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith("#")) { continue }
        $eq = $t.IndexOf("=")
        if ($eq -lt 1) { continue }
        $k = $t.Substring(0, $eq)
        $v = $t.Substring($eq + 1)
        if ($k -match "^[A-Za-z0-9_]+$") {
            $map[$k] = $v
        }
    }
    return $map
}

function Write-EnvFile([string]$path, $pairs, [string[]]$order) {
    $dir = Split-Path $path -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $lines = @(
        "# Gerado por scripts/sincronizar-env.ps1",
        "# Nao editar a mao; edite o .env da raiz.",
        ""
    )
    foreach ($k in $order) {
        $v = $pairs[$k]
        if ($null -ne $v -and "$v" -ne "") {
            $lines += "$k=$v"
        }
    }
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllLines($path, $lines, $utf8)
}

$m = Read-EnvMap $Master

Write-EnvFile (Join-Path $Root "bot\.env") $m @(
    "GROQ_API_KEY", "GROQ_MODEL",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "LEXROCHA_BASE_URL", "ZAIRYX_BASE_URL",
    "POLL_INTERVAL_MINUTES", "MIN_SCORE", "MAX_ALERTS_PER_DAY", "DEDUP_DB_PATH"
)

Write-EnvFile (Join-Path $Root "web\.env.local") $m @(
    "GROQ_API_KEY", "GROQ_MODEL",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    "NEXT_PUBLIC_SITE_URL"
)

Write-EnvFile (Join-Path $Root "engine\zairyx\.env") $m @(
    "GROQ_API_KEY", "GROQ_MODEL",
    "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "REDDIT_SUBREDDITS", "REDDIT_LIMIT",
    "SCAN_INTERVAL_SECONDS", "MAX_ALERTAS_POR_HORA"
)

Write-Host "Credenciais sincronizadas: bot/.env, web/.env.local, engine/zairyx/.env" -ForegroundColor Green
