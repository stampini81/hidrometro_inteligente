<#
Instala o Wokwi CLI globalmente (requer Node.js instalado). Execute em PowerShell:
  ./scripts/install-wokwi-cli.ps1
#>
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Error "npm não encontrado. Instale Node.js primeiro (https://nodejs.org)."; exit 1
}
Write-Warning "O pacote wokwi CLI não está disponível no npm registry público. Consulte https://docs.wokwi.com/cli para alternativas de instalação ou uso."
