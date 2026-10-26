#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3, 12), "Use Python 3.12 or newer"'
if [[ ! -x .venv-replit/bin/python ]]; then
  python3 -m venv .venv-replit
fi
# Replit may set pip's user-install default; the dedicated venv must own these.
PIP_USER=false .venv-replit/bin/python -m pip install -r requirements-api.txt
cd frontend
npm ci --no-audit --no-fund
npm run build
