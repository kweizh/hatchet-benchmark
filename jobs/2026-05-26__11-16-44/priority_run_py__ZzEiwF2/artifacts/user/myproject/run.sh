#!/usr/bin/env bash
set -euo pipefail

: "${ZEALT_RUN_ID:?ZEALT_RUN_ID must be set}"

python3 -m pip install --quiet --break-system-packages hatchet-sdk
python3 /home/user/myproject/prio_runner.py
