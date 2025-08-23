<#
Stop dev environment: docker services, Wokwi (headless) processes.
#>
Write-Host '[stop-all] Stopping docker compose...' -ForegroundColor Cyan
try { docker compose down } catch { Write-Warning 'docker compose down falhou' }

# Kill wokwi server if running
Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*@wokwi*' } | ForEach-Object { Write-Host "[stop-all] Matando processo Wokwi PID=$($_.Id)"; $_ | Stop-Process -Force }

Write-Host '[stop-all] Done.' -ForegroundColor Green
