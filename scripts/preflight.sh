#!/usr/bin/env bash
set -euo pipefail
echo "=== NewsVerify preflight ==="
echo "Python: $(python3 --version)"
echo "Docker: $(docker --version 2>/dev/null || echo 'not found')"
echo "Compose: $(docker compose version 2>/dev/null || echo 'not found')"
echo "Checking .env..."
if [ ! -f .env ]; then echo "MISSING .env"; exit 1; fi
echo "OK"