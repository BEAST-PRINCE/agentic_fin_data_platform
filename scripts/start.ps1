# PowerShell Startup Script for Financial Intelligence Platform
param (
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Split-Path -Parent $ScriptDir
Set-Location $RootDir

$LogsDir = Join-Path $RootDir "logs"
if (-not (Test-Path $LogsDir)) {
    New-Item -ItemType Directory -Path $LogsDir | Out-Null
}

$StartupLog = Join-Path $LogsDir "startup.log"
$BackendLog = Join-Path $LogsDir "backend.log"
$FrontendLog = Join-Path $LogsDir "frontend.log"
$HealthcheckLog = Join-Path $LogsDir "healthcheck.log"

# Recreate fresh log files on startup
function Init-LogFile {
    param ([string]$Path)
    try {
        "" | Out-File -FilePath $Path -Encoding utf8 -Force -ErrorAction SilentlyContinue
    } catch {}
}

Init-LogFile $StartupLog
Init-LogFile $BackendLog
Init-LogFile $FrontendLog
Init-LogFile $HealthcheckLog

function Log-Message {
    param ([string]$Msg)
    Write-Host $Msg
    Add-Content -Path $StartupLog -Value $Msg
}

Log-Message "=================================================="
Log-Message "  Starting Financial Intelligence Platform"
Log-Message "=================================================="
Log-Message "Logs location: $LogsDir`n"

# Step 1 — Environment Validation
Log-Message "Checking Development Environment..."

function Check-Tool {
    param ([string]$CommandName, [string]$DisplayName, [string]$VersionArgs = "--version")
    try {
        $cmd = Get-Command $CommandName -ErrorAction Stop
        $ver = & $CommandName $VersionArgs 2>&1 | Select-Object -First 1
        Log-Message ("{0:<20} .... OK ({1})" -f $DisplayName, $ver.ToString().Trim())
        return $true
    } catch {
        Log-Message ("{0:<20} .... MISSING" -f $DisplayName)
        return $false
    }
}

$envOk = $true
$envOk = (Check-Tool "docker" "Docker") -and $envOk
$envOk = (Check-Tool "docker-compose" "Docker Compose") -and $envOk
$envOk = (Check-Tool "python" "Python") -and $envOk
$envOk = (Check-Tool "pip" "pip") -and $envOk
$envOk = (Check-Tool "node" "Node.js") -and $envOk
$envOk = (Check-Tool "npm" "npm") -and $envOk

if (-not $envOk) {
    Log-Message "`n[ERROR] Missing required dependencies. Please install missing tools before continuing."
    exit 1
}

# Step 2 — Start Docker Infrastructure
Log-Message "`nStarting Infrastructure..."
try {
    docker-compose up -d | Out-String | Add-Content -Path $StartupLog
    Log-Message "Docker containers initiated."
} catch {
    Log-Message "[ERROR] Failed to start Docker Compose infrastructure."
    exit 1
}

$VenvPython = Join-Path $RootDir "venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
} else {
    $PythonExe = "python"
}

# Step 3 & 4 — Wait for Infrastructure & Health Checks
Log-Message "`nWaiting for Infrastructure Health..."
$infraHealth = & $PythonExe "$ScriptDir\healthcheck.py" --mode infra --wait --max-retries 6 --interval 4
$infraHealth | Add-Content -Path $StartupLog
if ($LASTEXITCODE -ne 0) {
    Log-Message "[ERROR] Infrastructure health check failed. Check $HealthcheckLog for details."
    exit 1
}
Log-Message "Infrastructure is Ready!"

# Step 5 — Launch Backend
Log-Message "`nLaunching FastAPI Backend (Port 8000)..."
$backendApiDir = Join-Path $RootDir "src\serving\api"
$backendCmd = "/c $PythonExe -m uvicorn main:app --reload --port 8000 > $BackendLog 2>&1"
$backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList $backendCmd `
    -WorkingDirectory $backendApiDir `
    -PassThru `
    -NoNewWindow

Log-Message "Backend started with PID $($backendProcess.Id). Logging to: $BackendLog"

# Step 6 — Wait for Backend
Log-Message "Waiting for Backend to become healthy..."
& $PythonExe "$ScriptDir\healthcheck.py" --mode backend --wait --max-retries 15 --interval 2
if ($LASTEXITCODE -ne 0) {
    Log-Message "[ERROR] FastAPI Backend failed to start. Check $BackendLog for error details."
    exit 1
}
Log-Message "Backend is Ready!"

# Step 7 — Launch Dashboard
Log-Message "`nLaunching Dashboard (Port 5173)..."
$dashboardDir = Join-Path $RootDir "dashboard"
$frontendCmd = "/c npm run dev > $FrontendLog 2>&1"
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList $frontendCmd `
    -WorkingDirectory $dashboardDir `
    -PassThru `
    -NoNewWindow

Log-Message "Dashboard started with PID $($frontendProcess.Id). Logging to: $FrontendLog"

# Step 8 — Wait for Dashboard
Log-Message "Waiting for Dashboard to become available..."
& $PythonExe "$ScriptDir\healthcheck.py" --mode frontend --wait --max-retries 10 --interval 2
if ($LASTEXITCODE -ne 0) {
    Log-Message "[ERROR] Dashboard failed to start. Check $FrontendLog for error details."
    exit 1
}
Log-Message "Dashboard is Ready!"

# Step 9 — Optional Browser Launch
if (-not $NoBrowser) {
    Log-Message "`nOpening http://localhost:5173 in default browser..."
    Start-Process "http://localhost:5173"
}

# Final Startup Summary
$summary = @"

==================================================

 Financial Intelligence Platform

==================================================

Infrastructure
  Kafka .............. Running (Port 9092)
  MinIO .............. Running (Port 9000)
  Qdrant ............. Running (Port 6333)
  Prometheus ......... Running (Port 9090)
  Grafana ............ Running (Port 3000)

Backend
  FastAPI ............ http://localhost:8000

Frontend
  Dashboard .......... http://localhost:5173

Logs Directory
  Location ........... $LogsDir

Status
  Platform Ready — Happy Researching!

==================================================
"@

Log-Message $summary
