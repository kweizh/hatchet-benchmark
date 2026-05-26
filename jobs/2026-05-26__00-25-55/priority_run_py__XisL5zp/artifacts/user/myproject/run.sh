#!/bin/bash
set -e

# Ensure ZEALT_RUN_ID is set, otherwise use a default for local testing
export ZEALT_RUN_ID=${ZEALT_RUN_ID:-local_test}

# Navigate to the project directory
cd /home/user/myproject

# Run the runner script which handles starting the worker and enqueuing tasks
python3 runner.py
