#!/bin/bash
# Run the benchmark sequentially, one model at a time: each small model on
# its own llama-server (started and stopped by run_own.py), gpt-oss-120b
# last through the lemond router.
# Usage: ./run_all.sh [model ...]   (default: all four small models + 120b)
# Waits for models/download.sh and any running run_own.py before starting.
set -e
cd "$(dirname "$0")"

if [ "$#" -gt 0 ]; then
  MODELS=("$@")
else
  MODELS=("Gemma-3-4b-it-GGUF" "Llama-3.2-3B-Instruct-GGUF" "Bonsai-8B-gguf" "gpt-oss-20b-mxfp4-GGUF" "gpt-oss-120b-GGUF")
fi

while pgrep -f download.sh > /dev/null; do
  echo "waiting for GGUF downloads..."
  sleep 60
done

while pgrep -f "run_own.py" > /dev/null; do
  echo "waiting for a running benchmark to finish..."
  sleep 60
done

for model in "${MODELS[@]}"; do
  echo "=== $model ==="
  if [ "$model" = "gpt-oss-120b-GGUF" ]; then
    python3 -u run_120b.py
  else
    python3 -u run_own.py "$model"
  fi
done

echo "ALL_MODELS_DONE"
