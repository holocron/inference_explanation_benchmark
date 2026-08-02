"""Run the benchmark against locally served models on this machine.

Two serving stacks:
  - LM Studio (http://localhost:1234/v1): native 1-bit Bonsai models
    (Q1_0 GGUF needs PrismML's type-41 support, which LM Studio ships)
  - mlx_lm.server (http://localhost:1235/v1): Ternary-Bonsai-27B (2-bit MLX)
    — LM Studio's MLX runtime 1.11.0 hides the qwen3_5 hybrid arch, so we
    serve it directly with mlx-lm from ~/.venvs/mlx:
      caffeinate -i ~/.venvs/mlx/bin/python -m mlx_lm.server \
        --model ~/.lmstudio/models/prism-ml/Ternary-Bonsai-27B-mlx-2bit --port 1235

The answer directory name differs from the payload model id so these runs
do not collide with the server-side results.
LM Studio / mlx_lm return no llama.cpp `timings`, so `duration` is 0 —
durations are not used in the analysis.

Run with caffeinate to keep the Mac awake:
  caffeinate -i python3 -u run_lmstudio.py [entry_index ...]
"""
import sys

import config
from src.AnswerGenerator import AnswerGenerator
from src.OpenAIHandler import OpenAIHandler

LMSTUDIO_URL = "http://localhost:1234/v1"
MLX_URL = "http://localhost:1235/v1"

# (payload model id, answer directory name, base url)
MODELS = [
    ("bonsai-8b", "Bonsai-8B-1bit-Q1_0-LMStudio", LMSTUDIO_URL),
    ("bonsai-27b", "Bonsai-27B-1bit-Q1_0-LMStudio", LMSTUDIO_URL),
    ("/Users/holocron/.lmstudio/models/prism-ml/Ternary-Bonsai-27B-mlx-2bit",
     "Ternary-Bonsai-27B-2bit-MLX", MLX_URL),
]

if __name__ == '__main__':
    selected = [MODELS[int(i)] for i in sys.argv[1:]] if len(sys.argv) > 1 else MODELS
    generator = None
    for payload_id, dir_name, base_url in selected:
        print(f"=== {dir_name} (payload id: {payload_id}, via {base_url}) ===")
        handler = OpenAIHandler(payload_id, base_url, load_on_missing = False)
        if generator is None:
            generator = AnswerGenerator(config.DATASET_DIR)
        generator.generate(handler, dir_name)
    print("LOCAL_MODELS_DONE")
