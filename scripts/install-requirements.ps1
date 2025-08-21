param(
  [switch]$SkipPlatformIO
)

Write-Host "==> Hidrometro: instalando dependências do projeto" -ForegroundColor Cyan

function Test-Command($name) {
  $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $repoRoot

# 1) Backend (Node.js)
if (Test-Command node) {
  Write-Host "[Node] Versão: $(node -v)" -ForegroundColor Green
} else {
  Write-Warning "Node.js não encontrado. Instale Node LTS (https://nodejs.org/) e execute novamente."
}

if (Test-Path "$repoRoot/backend/package.json") {
  Write-Host "[Backend] Instalando dependências npm..." -ForegroundColor Cyan
  Push-Location "$repoRoot/backend"
  if (Test-Command npm) { npm ci 2>$null; if ($LASTEXITCODE -ne 0) { npm install } }
  Pop-Location
} else {
  Write-Warning "[Backend] package.json não encontrado em backend/"
}

# 2) .env padrão
$envPath = Join-Path $repoRoot ".env"
if (-not (Test-Path $envPath)) {
  Write-Host "[.env] Criando .env padrão" -ForegroundColor Cyan
  @(
    'PORT=3000'
    'MQTT_URL=mqtt://broker.hivemq.com:1883'
    'MQTT_TOPIC=hidrometro/leandro/dados'
    'MQTT_CMD_TOPIC=hidrometro/leandro/cmd'
  ) | Out-File -Encoding ASCII -FilePath $envPath
} else {
  Write-Host "[.env] Já existe (mantido)" -ForegroundColor DarkGray
}

# 3) PlatformIO (opcional para Wokwi)
if (-not $SkipPlatformIO) {
  $py = $null
  if (Test-Command py) { $py = 'py' } elseif (Test-Command python) { $py = 'python' }
  if ($py) {
    Write-Host "[PlatformIO] Instalando via pip do usuário..." -ForegroundColor Cyan
    & $py -m pip install --user platformio | Out-Null
    if ($LASTEXITCODE -eq 0) {
      Write-Host "[PlatformIO] Instalado com sucesso." -ForegroundColor Green
    } else {
      Write-Warning "[PlatformIO] Falha ao instalar. Instale manualmente a extensão PlatformIO IDE no VS Code."
    }
  } else {
    Write-Warning "Python não encontrado. Para compilar firmware, instale Python 3 e/ou a extensão PlatformIO IDE no VS Code."
  }
} else {
  Write-Host "[PlatformIO] Ignorado por parâmetro." -ForegroundColor DarkGray
}

Write-Host "==> Pronto. Próximos passos sugeridos:" -ForegroundColor Cyan
Write-Host " - (Wokwi) Compile o firmware: PlatformIO: Build (gera .pio/build/esp32dev/firmware.bin)"
Write-Host " - (Backend) Suba com Docker: docker compose up --build -d backend"
Write-Host " - Acesse dashboard: http://localhost:3000/dashboard"
