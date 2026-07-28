#!/usr/bin/env bash
# Linux/macOS Restart Script for Financial Intelligence Platform

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=================================================="
echo "  Restarting Financial Intelligence Platform"
echo "=================================================="

"$SCRIPT_DIR/stop.sh"
sleep 2
"$SCRIPT_DIR/start.sh" "$@"
