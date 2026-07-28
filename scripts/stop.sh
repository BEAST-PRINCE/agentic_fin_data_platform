#!/usr/bin/env bash
# Linux/macOS Stop Script for Financial Intelligence Platform

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

echo "=================================================="
echo "  Stopping Financial Intelligence Platform"
echo "=================================================="

kill_port() {
    local port="$1"
    local name="$2"
    echo "Stopping $name (Port $port)..."
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -t -i:"$port" 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            echo "Terminated process(es) on port $port."
        else
            echo "No active process found on port $port."
        fi
    elif command -v fuser >/dev/null 2>&1; then
        fuser -k "$port/tcp" >/dev/null 2>&1 || true
    fi
}

kill_port 8000 "FastAPI Backend"
kill_port 5173 "Dashboard Frontend"

echo ""
echo "Stopping Docker Infrastructure..."
docker-compose down || true

echo ""
echo "=================================================="
echo "  Platform stopped successfully."
echo "=================================================="
