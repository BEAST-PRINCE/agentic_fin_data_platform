#!/usr/bin/env bash
# Linux/macOS Startup Script for Financial Intelligence Platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

LOGS_DIR="$ROOT_DIR/logs"
mkdir -p "$LOGS_DIR"

STARTUP_LOG="$LOGS_DIR/startup.log"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"
HEALTHCHECK_LOG="$LOGS_DIR/healthcheck.log"

# Recreate fresh log files on startup
> "$STARTUP_LOG"
> "$BACKEND_LOG"
> "$FRONTEND_LOG"
> "$HEALTHCHECK_LOG"

log() {
    echo "$1"
    echo "$1" >> "$STARTUP_LOG"
}

log "=================================================="
log "  Starting Financial Intelligence Platform"
log "=================================================="
log "Logs location: $LOGS_DIR"
log ""

# Step 1 — Environment Validation
log "Checking Development Environment..."

check_tool() {
    local cmd="$1"
    local name="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        local ver
        ver=$("$cmd" --version 2>&1 | head -n 1 || echo "OK")
        printf "%-20s .... OK (%s)\n" "$name" "$ver" | tee -a "$STARTUP_LOG"
        return 0
    else
        printf "%-20s .... MISSING\n" "$name" | tee -a "$STARTUP_LOG"
        return 1
    fi
}

ENV_OK=0
check_tool "docker" "Docker" || ENV_OK=1
check_tool "docker-compose" "Docker Compose" || ENV_OK=1
check_tool "python3" "Python 3" || ENV_OK=1
check_tool "pip3" "pip" || ENV_OK=1
check_tool "node" "Node.js" || ENV_OK=1
check_tool "npm" "npm" || ENV_OK=1

if [ $ENV_OK -ne 0 ]; then
    log "[ERROR] Missing required dependencies. Please install missing tools."
    exit 1
fi

# Step 2 — Start Docker Infrastructure
log ""
log "Starting Infrastructure..."
docker-compose up -d >> "$STARTUP_LOG" 2>&1

# Step 3 & 4 — Wait for Infrastructure
log ""
log "Waiting for Infrastructure Health..."
python3 "$SCRIPT_DIR/healthcheck.py" --mode infra --wait --max-retries 6 --interval 4
log "Infrastructure is Ready!"

# Step 5 — Launch Backend
log ""
log "Launching FastAPI Backend (Port 8000)..."
(cd "$ROOT_DIR/src/serving/api" && nohup python3 -m uvicorn main:app --reload --port 8000 > "$BACKEND_LOG" 2>&1 &)
log "Backend started in background. Logging to: $BACKEND_LOG"

# Step 6 — Wait for Backend
log "Waiting for Backend to become healthy..."
python3 "$SCRIPT_DIR/healthcheck.py" --mode backend --wait --max-retries 10 --interval 2
log "Backend is Ready!"

# Step 7 — Launch Dashboard
log ""
log "Launching Dashboard (Port 5173)..."
(cd "$ROOT_DIR/dashboard" && nohup npm run dev > "$FRONTEND_LOG" 2>&1 &)
log "Dashboard started in background. Logging to: $FRONTEND_LOG"

# Step 8 — Wait for Dashboard
log "Waiting for Dashboard to become available..."
python3 "$SCRIPT_DIR/healthcheck.py" --mode frontend --wait --max-retries 10 --interval 2
log "Dashboard is Ready!"

# Step 9 — Optional Browser Launch
if [ "$1" != "--no-browser" ]; then
    if command -v xdg-open >/dev/null 2>&1; then
        xdg-open "http://localhost:5173" >/dev/null 2>&1 &
    elif command -v open >/dev/null 2>&1; then
        open "http://localhost:5173" >/dev/null 2>&1 &
    fi
fi

# Final Summary
log "
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
  Location ........... $LOGS_DIR

Status
  Platform Ready — Happy Researching!

==================================================
"
