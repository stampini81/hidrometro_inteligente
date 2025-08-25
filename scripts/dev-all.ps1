<#
Start full dev environment:
- Docker services (flask, mosquitto, postgres)
- PlatformIO build (ESP32 firmware)
- Wokwi simulation (headless)
Usage:
  ./scripts/dev-all.ps1        # defaults
Optional params:
  -Rebuild (forces docker rebuild)
  -Headless (default) or -GUI (omit --headless)
#>
param(
  [switch]$Rebuild,
  [switch]$GUI
)
$ErrorActionPreference = 'Stop'
Write-Host "[dev-all] Starting environment..." -ForegroundColor Cyan

# 1. Docker compose
$composeCmd = 'docker compose up -d'
if ($Rebuild) { $composeCmd += ' --build' }
Write-Host "[dev-all] Docker: $composeCmd"
Invoke-Expression $composeCmd


# 2. Verificar arquivo .env
if (-not (Test-Path "$PSScriptRoot/../.env")) {
  Write-Warning "Arquivo .env não encontrado na raiz do projeto. Crie manualmente ou copie de .env.example."
}

# 3. PlatformIO build
if (-not (Get-Command pio -ErrorAction SilentlyContinue)) {
  Write-Warning 'PlatformIO (pio) não encontrado no PATH. Instale com: python -m pip install platformio'
} else {
  Write-Host '[dev-all] Building firmware (pio run)...'
  $p = Start-Process pio -ArgumentList 'run' -NoNewWindow -PassThru -Wait
  if ($p.ExitCode -ne 0) { Write-Error 'Falha no build do firmware'; exit 1 }
}

# 4. Wokwi simulation
if (-not (Get-Command wokwi -ErrorAction SilentlyContinue)) {
  Write-Warning 'Wokwi CLI não encontrado. O pacote wokwi não está disponível no npm registry público. Consulte https://docs.wokwi.com/cli para alternativas.'
} else {
  $wokwiArgs = 'server'
  if (-not $GUI) { $wokwiArgs += ' --headless' }
  Write-Host "[dev-all] Iniciando Wokwi ($wokwiArgs)..."
  Start-Process wokwi -ArgumentList $wokwiArgs -NoNewWindow
}

Write-Host '[dev-all] Ambiente iniciado. URLs:' -ForegroundColor Green
Write-Host '  API Flask:       http://localhost:5000'
Write-Host '  Dashboard:       http://localhost:5000/dashboard'
Write-Host '  Firmware HTTP:   http://localhost:8180 (após simulação iniciar)'
Write-Host '  Wokwi UI porta:  (se GUI) ver terminal / output'
