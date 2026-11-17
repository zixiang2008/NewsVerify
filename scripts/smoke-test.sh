#!/usr/bin/env bash
set -euo pipefail
echo "=== smoke test ==="
curl -sS http://127.0.0.1:8080/health
echo
curl -sS http://127.0.0.1:8080/api/status
echo