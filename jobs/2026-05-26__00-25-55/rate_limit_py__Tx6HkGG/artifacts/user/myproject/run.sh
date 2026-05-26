#!/bin/bash
set -e

# Navigate to the project directory
cd /home/user/myproject

# Run the Python script
python3 main.py

# Check if the log file exists and has 15 lines
if [ -f /tmp/rate_log.txt ]; then
    LINE_COUNT=$(grep -c '^' /tmp/rate_log.txt)
    if [ "$LINE_COUNT" -eq 15 ]; then
        echo "Success: Found 15 timestamp lines in /tmp/rate_log.txt"
        exit 0
    else
        echo "Failure: Found $LINE_COUNT lines in /tmp/rate_log.txt, expected 15"
        exit 1
    fi
else
    echo "Failure: /tmp/rate_log.txt does not exist"
    exit 1
fi
