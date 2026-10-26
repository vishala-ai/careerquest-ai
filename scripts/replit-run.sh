#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
careerquest_python="${CAREERQUEST_PYTHON:-.venv-replit/bin/python}"
if [[ ! -x "$careerquest_python" || ! -f frontend/dist/index.html ]]; then
  echo "Run bash scripts/replit-setup.sh before starting CareerQuest." >&2
  exit 1
fi
# Keep local invocations private; .replit explicitly selects the preview interface.
exec "$careerquest_python" -m uvicorn careerquest.api:app \
  --host "${CAREERQUEST_HOST:-127.0.0.1}" --port "${PORT:-8000}" --no-proxy-headers
