#!/usr/bin/env bash
set -euo pipefail

# Ensure hatchet-sdk is installed (idempotent).
pip install --quiet --break-system-packages hatchet-sdk >/dev/null 2>&1 || true

# Run the priority-queue demonstration.
exec python3 "$(dirname "$0")/main.py"
