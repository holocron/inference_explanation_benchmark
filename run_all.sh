#!/bin/bash
# Run the full benchmark matrix sequentially, one model at a time:
# each small model on its own llama-server (started and stopped by
# run_own.py), gpt-oss-120b last through the lemond router.
# Waits for models/download.sh to finish before starting.
set -e
cd "$(dirname "$0")"

while pgrep -f download.sh > /dev/null; do
  echo "waiting for GGUF downloads..."
  sleep 60
done

for model in "Gemma-3-4b-it-GGUF" "Llama-3.2-3B-Instruct-GGUF" "Bonsai-8B-gguf" "gpt-oss-20b-mxfp4-GGUF"; do
  echo "=== $model ==="
  python3 -u run_own.py "$model"
done

echo "=== gpt-oss-120b-GGUF (via lemond router) ==="
python3 -u run_120b.py

echo "ALL_MODELS_DONE"
