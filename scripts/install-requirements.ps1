param(
  [switch]$SkipVenv,
  [switch]$NoMigrate,
  [switch]$Start,
  [string]$PythonVersion = 'python'
)

Write-Host "==> Setup Hidrômetro (Flask Unificado)" -ForegroundColor Cyan


function Test-Command($name){ $null -ne (Get-Command $name -ErrorAction SilentlyContinue) }

# Verificar Python
if (-not (Test-Command $PythonVersion)) {
  Write-Warning "Python não encontrado no PATH. Baixando instalador..."
  $pythonInstaller = "$env:TEMP\python-installer.exe"
  Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe" -OutFile $pythonInstaller
  Start-Process $pythonInstaller
  Write-Error "Instale o Python manualmente e adicione ao PATH do sistema. Depois execute novamente este script."; exit 1
}

# Verificar pip
if (-not (Test-Command 'pip')) {
  Write-Error "pip não encontrado no PATH. Instale o pip e adicione ao PATH do sistema."; exit 1
}

# Instalar PlatformIO se não estiver disponível
if (-not (Test-Command 'pio')) {
  Write-Host "[PIP] Instalando PlatformIO..." -ForegroundColor Cyan
  pip install platformio
  if (-not (Test-Command 'pio')) {
    Write-Warning "PlatformIO não foi instalado corretamente. Verifique o PATH ou instale manualmente: python -m pip install platformio"
  } else {
    Write-Host "PlatformIO instalado com sucesso." -ForegroundColor Green
  }
}

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
Set-Location $repoRoot

# Caminhos
$venvPath = Join-Path $repoRoot '.venv'
$reqFile = 'MVC_sistema_leitura_hidrometros/requirements.txt'
$flaskApp = 'MVC_sistema_leitura_hidrometros/app'

if (-not (Test-Path $reqFile)) { Write-Error "Arquivo requirements não encontrado em $reqFile"; exit 1 }

# 1) Ambiente virtual
if (-not $SkipVenv) {
  if (-not (Test-Path $venvPath)) {
    Write-Host "[VENV] Criando ambiente virtual" -ForegroundColor Cyan
    & $PythonVersion -m venv .venv
  } else { Write-Host "[VENV] Já existe (reutilizando)" -ForegroundColor DarkGray }
  $activate = Join-Path $venvPath 'Scripts/Activate.ps1'
  if (Test-Path $activate) { . $activate } else { Write-Warning "Não foi possível ativar venv (arquivo não encontrado)." }
} else { Write-Host "[VENV] Ignorado por parâmetro" -ForegroundColor DarkGray }

# 2) Dependências
Write-Host "[PIP] Instalando dependências" -ForegroundColor Cyan
pip install --upgrade pip | Out-Null
pip install -r $reqFile

if ($LASTEXITCODE -ne 0) { Write-Error "Falha ao instalar dependências"; exit 1 }



# 3) .env
if (-not (Test-Path '.env')) {
  if (Test-Path '.env.example') {
    Copy-Item .env.example .env
    Write-Host "[.env] Criado a partir de .env.example" -ForegroundColor Green
  } else {
    @(
      'DB_ENGINE=sqlite'
      'MQTT_URL=mqtt://broker.hivemq.com:1883'
      'MQTT_TOPIC_DADOS=hidrometro/dados'
      'MQTT_TOPIC_CMD=hidrometro/cmd'
      'SECRET_KEY=changeme'
      'HISTORY_LIMIT=1000'
    ) | Out-File -Encoding ASCII .env
    Write-Host "[.env] Criado básico (editar depois)" -ForegroundColor Yellow
  }
} else { Write-Host "[.env] Já existe (mantido)" -ForegroundColor DarkGray }

# 4) Migrações
if (-not $NoMigrate) {
  Write-Host "[DB] Executando migrações" -ForegroundColor Cyan
  $flaskCmd = "python -m flask --app $flaskApp"
  if (-not (Test-Path 'migrations')) { Invoke-Expression "$flaskCmd db init" }
  Invoke-Expression "$flaskCmd db migrate -m 'auto'" 2>$null | Out-Null
  Invoke-Expression "$flaskCmd db upgrade"
} else { Write-Host "[DB] Migrações puladas (--NoMigrate)" -ForegroundColor DarkGray }

# 5) Resumo
Write-Host "==> Concluído." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:5000/dashboard" -ForegroundColor Cyan

if ($Start) {
  Write-Host "[RUN] Iniciando servidor (Ctrl+C para parar)" -ForegroundColor Cyan
  python MVC_sistema_leitura_hidrometros/MVC_sistema_leitura_hidrometros/run.py
}

Write-Host "Dicas:" -ForegroundColor Cyan
Write-Host "  .\\scripts\\install-requirements.ps1 -Start" -ForegroundColor DarkGray
Write-Host "  .\\scripts\\install-requirements.ps1 -SkipVenv -NoMigrate" -ForegroundColor DarkGray
# Fim
