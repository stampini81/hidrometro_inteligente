<#
Helper PowerShell functions to interact with the Flask API using Invoke-RestMethod.
Usage (PowerShell):
  . ./scripts/invoke_rest.ps1   # dot-source to load functions
  $t = Get-Token -User admin -Password admin
  Get-History -Token $t -Limit 10
  Post-Data -Token $t -TotalLiters 123.4 -FlowLmin 5.6 -Serial ABC123
  Send-Cmd -Token $t -Action reset
#>
param()
$Global:BaseUrl = $env:BASE_URL
if (-not $Global:BaseUrl) { $Global:BaseUrl = 'http://localhost:5000' }

function Get-Token {
    [CmdletBinding()] param(
        [string]$User='admin',
        [string]$Password='admin',
        [string]$BaseUrl=$Global:BaseUrl
    )
    $body = @{ username=$User; password=$Password } | ConvertTo-Json
    $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/login" -ContentType 'application/json' -Body $body
    return $resp.token
}

function Get-History {
    [CmdletBinding()] param(
        [Parameter(Mandatory)][string]$Token,
        [int]$Limit=50,
        [string]$BaseUrl=$Global:BaseUrl
    )
    Invoke-RestMethod -Uri "$BaseUrl/api/history?limit=$Limit" -Headers @{Authorization = "Bearer $Token"}
}

function Get-Current {
    [CmdletBinding()] param(
        [Parameter(Mandatory)][string]$Token,
        [string]$BaseUrl=$Global:BaseUrl
    )
    Invoke-RestMethod -Uri "$BaseUrl/api/current" -Headers @{Authorization = "Bearer $Token"}
}

function Post-Data {
    [CmdletBinding()] param(
        [Parameter(Mandatory)][string]$Token,
        [double]$TotalLiters = 0,
        [double]$FlowLmin = 0,
        [string]$Serial = 'TEST123',
        [string]$BaseUrl=$Global:BaseUrl
    )
    $body = @{ totalLiters=$TotalLiters; flowLmin=$FlowLmin; numeroSerie=$Serial } | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/data" -ContentType 'application/json' -Headers @{Authorization = "Bearer $Token"} -Body $body
}

function Send-Cmd {
    [CmdletBinding()] param(
        [Parameter(Mandatory)][string]$Token,
        [Parameter(Mandatory)][string]$Action,
        [string]$Value,
        [string]$BaseUrl=$Global:BaseUrl
    )
    $bodyHash = @{ action=$Action }
    if ($PSBoundParameters.ContainsKey('Value')) { $bodyHash.value = $Value }
    $body = $bodyHash | ConvertTo-Json
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/cmd" -ContentType 'application/json' -Headers @{Authorization = "Bearer $Token"} -Body $body
}

Write-Host "[invoke_rest.ps1] Funções carregadas: Get-Token, Get-History, Get-Current, Post-Data, Send-Cmd. Use Get-Help <Nome> -Full para detalhes."
