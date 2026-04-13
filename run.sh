#!/bin/bash

CONFIG_PATH=/data/options.json

# Load config
if [ -f "$CONFIG_PATH" ]; then
    export SYNC_INTERVAL=$(jq -r '.sync_interval // 360' "$CONFIG_PATH")
    export LOG_LEVEL=$(jq -r '.log_level // "info"' "$CONFIG_PATH")
    export MAX_CACHE_AGE=$(jq -r '.max_cache_age // 86400' "$CONFIG_PATH")
    export GITHUB_TOKEN=$(jq -r '.github_token // ""' "$CONFIG_PATH")
else
    export SYNC_INTERVAL=360
    export LOG_LEVEL=info
    export MAX_CACHE_AGE=86400
    export GITHUB_TOKEN=""
fi

echo "Starting HA YAML Corrector"
echo "Sync interval: ${SYNC_INTERVAL} minutes"
echo "Log level: ${LOG_LEVEL}"

cd /app
python3 app.py
