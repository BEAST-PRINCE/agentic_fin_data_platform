# PowerShell Stop Script for Financial Intelligence Platform
$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

Write-Host "=================================================="
Write-Host "  Stopping Financial Intelligence Platform"
Write-Host "=================================================="

# Function to kill process by port
function Stop-ProcessByPort {
    param ([int]$Port, [string]$ServiceName)
    Write-Host "Stopping $ServiceName (Port $Port)..."
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
        if ($conns) {
            $pidsToKill = $conns | Select-Object -ExpandProperty OwningProcess -Unique
            foreach ($procId in $pidsToKill) {
                if ($procId -gt 0) {
                    try {
                        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                        Write-Host "Terminated process PID $procId on port $Port."
                    } catch {
                        # Ignore
                    }
                }
            }
        } else {
            Write-Host "No active process found on port $Port."
        }
    } catch {
        Write-Host "Could not query port $Port."
    }
}

# Stop Backend (8000) and Frontend (5173)
Stop-ProcessByPort -Port 8000 -ServiceName "FastAPI Backend"
Stop-ProcessByPort -Port 5173 -ServiceName "Dashboard Frontend"

# Stop Docker Infrastructure
Write-Host "`nStopping Docker Infrastructure..."
try {
    docker-compose down
    Write-Host "Docker containers stopped successfully."
} catch {
    Write-Host "[WARNING] docker-compose down encountered an error or containers were already stopped."
}

Write-Host "`n=================================================="
Write-Host "  Platform stopped successfully."
Write-Host "=================================================="
