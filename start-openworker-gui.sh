#!/usr/bin/env bash
set -euo pipefail

ROOT=/Users/john/OpenWorker/de8ccae2-dac/openworker-zh
export PATH=/Users/john/OpenWorker/de8ccae2-dac/local/miniforge3/bin:/Users/john/OpenWorker/de8ccae2-dac/local/node/bin:$PATH
export COWORKER_STATE_DIR=/Users/john/OpenWorker/de8ccae2-dac/.openworker-state

# 把 sidecar token 传给前端 Vite，让前端 API 请求能通过后端认证
export VITE_COWORKER_API_TOKEN=$(cat "$COWORKER_STATE_DIR/sidecar-8765.token")

cd "$ROOT/surfaces/gui"
npm run dev -- --host
