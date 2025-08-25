<#
Stop dev environment: docker services, Wokwi (headless) processes.
#>
Write-Host '[stop-all] Stopping docker compose...' -ForegroundColor Cyan
try { docker compose down } catch { Write-Warning 'docker compose down falhou. Verifique se o Docker está instalado e configurado corretamente.' }

# Verificar arquivo .env
if (-not (Test-Path "$PSScriptRoot/../.env")) {
	Write-Warning "Arquivo .env não encontrado na raiz do projeto. Algumas variáveis de ambiente podem não ser carregadas."
}

# Kill wokwi server if running
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*@wokwi*' } | ForEach-Object { Write-Host "[stop-all] Matando processo Wokwi PID=$($_.Id)"; $_ | Stop-Process -Force }
if (-not (Get-Command wokwi -ErrorAction SilentlyContinue)) {
	Write-Warning 'Wokwi CLI não encontrado. Nenhum processo wokwi será finalizado.'
}

Write-Host '[stop-all] Done.' -ForegroundColor Green
