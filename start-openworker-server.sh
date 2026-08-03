#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/john/OpenWorker/de8ccae2-dac/openworker-zh
STATE=/Users/john/OpenWorker/de8ccae2-dac/.openworker-state
export PATH=/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3/bin:/Users/john/OpenWorker/de8ccae2-dac/local/node/bin:$PATH
export COWORKER_STATE_DIR="$STATE"

mkdir -p "$STATE"

if [ ! -f "$STATE/sidecar-8765.token" ]; then
  openssl rand -hex 32 > "$STATE/sidecar-8765.token"
fi

export COWORKER_API_TOKEN=$(cat "$STATE/sidecar-8765.token")

cd "$ROOT"
.venv/bin/openworker-server --cwd /Users/john/OpenWorker/de8ccae2-dac --port 8765
