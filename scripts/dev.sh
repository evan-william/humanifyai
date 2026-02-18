#!/usr/bin/env bash
# dev.sh — start the development server with hot-reload.
# Usage: ./scripts/dev.sh [port]

set -euo pipefail

PORT="${1:-8000}"

if [[ ! -f ".env" ]]; then
  echo "No .env found — copying .env.example..."
  cp .env.example .env
fi

echo "Starting HumanifyAI on http://localhost:${PORT}"
uvicorn main:app --host 0.0.0.0 --port "$PORT" --reload --reload-dir api --reload-dir core