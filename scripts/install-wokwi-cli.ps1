<#
Instala o Wokwi CLI globalmente (requer Node.js instalado). Execute em PowerShell:
  ./scripts/install-wokwi-cli.ps1
#>
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Error "npm não encontrado. Instale Node.js primeiro (https://nodejs.org)."; exit 1
}
Write-Host "Instalando @wokwi/cli globalmente..."
npm install -g @wokwi/cli
if ($LASTEXITCODE -ne 0) { Write-Error "Falha na instalação do Wokwi CLI"; exit 1 }
Write-Host "Wokwi CLI instalado. Versão:" (wokwi --version)
