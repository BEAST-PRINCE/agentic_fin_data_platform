# PowerShell Restart Script for Financial Intelligence Platform
param (
    [switch]$NoBrowser
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "=================================================="
Write-Host "  Restarting Financial Intelligence Platform"
Write-Host "=================================================="

& "$ScriptDir\stop.ps1"
Start-Sleep -Seconds 2

if ($NoBrowser) {
    & "$ScriptDir\start.ps1" -NoBrowser
} else {
    & "$ScriptDir\start.ps1"
}
