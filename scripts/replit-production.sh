#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export CAREERQUEST_ENV=production
export CAREERQUEST_DEV_TOOLS=0
export CAREERQUEST_HOST=0.0.0.0
# Startup validates HTTPS origin and persistent PostgreSQL; never fall back to
# ephemeral SQLite in a published app. Replit terminates HTTPS at its proxy.
exec bash scripts/replit-run.sh
