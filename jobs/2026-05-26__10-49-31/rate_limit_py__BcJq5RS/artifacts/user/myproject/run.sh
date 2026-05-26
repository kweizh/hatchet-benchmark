#!/usr/bin/env bash
# run.sh – Full end-to-end orchestration entrypoint.
#
# Usage:
#   bash /home/user/myproject/run.sh
#
# Required environment variables:
#   HATCHET_CLIENT_TOKEN  – Hatchet Cloud API token
#   ZEALT_RUN_ID          – unique identifier for this trial

set -euo pipefail

# ---------------------------------------------------------------------------
# Validate required environment variables
# ---------------------------------------------------------------------------

if [[ -z "${HATCHET_CLIENT_TOKEN:-}" ]]; then
  echo "[run.sh] ERROR: HATCHET_CLIENT_TOKEN is not set" >&2
  exit 1
fi

if [[ -z "${ZEALT_RUN_ID:-}" ]]; then
  echo "[run.sh] ERROR: ZEALT_RUN_ID is not set" >&2
  exit 1
fi

echo "[run.sh] ZEALT_RUN_ID=${ZEALT_RUN_ID}"
echo "[run.sh] rate-limit key: ext-api-${ZEALT_RUN_ID}"

# ---------------------------------------------------------------------------
# Ensure hatchet-sdk is installed
# ---------------------------------------------------------------------------

if ! python3 -c "import hatchet_sdk" 2>/dev/null; then
  echo "[run.sh] installing hatchet-sdk …"
  pip install --quiet hatchet-sdk
fi

# ---------------------------------------------------------------------------
# Move to the project directory so relative imports work
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

# ---------------------------------------------------------------------------
# Run the orchestration
# ---------------------------------------------------------------------------

echo "[run.sh] starting orchestration …"
exec python3 main.py
