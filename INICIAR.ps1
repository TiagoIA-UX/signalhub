#Requires -Version 5.1
<#
.SYNOPSIS
  SignalHub — menu local (bot legado, engine, web qualify).
#>
param(
    [ValidateSet("menu", "sync", "bot", "engine", "web", "tudo")]
    [string]$Modo = "menu",
    [switch]$Instalar
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

function Sync-Env {
    & (Join-Path $Root "scripts\sincronizar-env.ps1")
}

function Ensure-BotVenv {
    $venv = Join-Path $Root "bot\.venv"
    if (-not (Test-Path $venv)) {
        Write-Host "Criando venv do bot..." -ForegroundColor Yellow
        Push-Location (Join-Path $Root "bot")
        try {
            python -m venv .venv
            & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
        } finally { Pop-Location }
    }
}

function Ensure-EngineVenv {
    $venv = Join-Path $Root "engine\.venv"
    if (-not (Test-Path $venv)) {
        Write-Host "Criando venv do engine..." -ForegroundColor Yellow
        Push-Location (Join-Path $Root "engine")
        try {
            python -m venv .venv
            & ".\.venv\Scripts\python.exe" -m pip install -r requirements.txt
        } finally { Pop-Location }
    }
}

function Ensure-WebDeps {
    $nm = Join-Path $Root "web\node_modules"
    if (-not (Test-Path $nm)) {
        Write-Host "Instalando dependencias do web..." -ForegroundColor Yellow
        Push-Location (Join-Path $Root "web")
        try { npm install } finally { Pop-Location }
    }
}

function Start-Bot {
    Sync-Env
    if ($Instalar) { Ensure-BotVenv }
    Ensure-BotVenv
    Write-Host "Bot legado (Reddit + Telegram)" -ForegroundColor Cyan
    Push-Location (Join-Path $Root "bot")
    try {
        & ".\.venv\Scripts\python.exe" run_once.py
    } finally { Pop-Location }
}

function Start-Engine {
    Sync-Env
    if ($Instalar) { Ensure-EngineVenv }
    Ensure-EngineVenv
    Write-Host "Engine v2 (tenant zairyx)" -ForegroundColor Cyan
    Push-Location (Join-Path $Root "engine")
    try {
        if (Test-Path ".\zairyx\bot.py") {
            & ".\.venv\Scripts\python.exe" ".\zairyx\bot.py"
        } else {
            Write-Host "Entrypoint engine/zairyx/bot.py nao encontrado. Use o core conforme README." -ForegroundColor Yellow
        }
    } finally { Pop-Location }
}

function Start-Web {
    Sync-Env
    if ($Instalar) { Ensure-WebDeps }
    Ensure-WebDeps
    Write-Host "Web qualify (Vortexia) — http://localhost:3000" -ForegroundColor Cyan
    Push-Location (Join-Path $Root "web")
    try {
        Start-Process "http://localhost:3000"
        npm run dev
    } finally { Pop-Location }
}

function Show-Menu {
    Write-Host ""
    Write-Host " SignalHub — $Root" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  1  Sincronizar credenciais (.env -> bot/web/engine)"
    Write-Host "  2  Bot legado (Reddit + alertas Telegram)"
    Write-Host "  3  Engine v2 (scan)"
    Write-Host "  4  Web qualify (porta 3000)"
    Write-Host "  0  Sair"
    Write-Host ""
    $opcao = Read-Host "Opcao"
    switch ($opcao) {
        "1" { Sync-Env }
        "2" { Start-Bot }
        "3" { Start-Engine }
        "4" { Start-Web }
        "0" { return }
        default { Write-Host "Opcao invalida." }
    }
}

if ($Instalar) {
    Sync-Env
    Ensure-BotVenv
    Ensure-EngineVenv
    Ensure-WebDeps
    Write-Host "Instalacao concluida." -ForegroundColor Green
}

switch ($Modo) {
    "sync" { Sync-Env }
    "bot" { Start-Bot }
    "engine" { Start-Engine }
    "web" { Start-Web }
    "tudo" {
        Sync-Env
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$Root'; .\INICIAR.ps1 -Modo bot"
        Start-Web
    }
    "menu" { Show-Menu }
}
