"""Run the benchmark against models served by LM Studio on this machine
(http://localhost:1234/v1, OpenAI-compatible).

Used for the NATIVE ternary (Q1_0) Bonsai models, which stock llama.cpp
builds reject (ggml type 41) but LM Studio's bundled llama.cpp runs:
  - bonsai-8b   (prism-ml/Bonsai-8B-gguf, Q1_0)          -> Bonsai-8B-1bit-Q1_0-LMStudio
  - bonsai-27b  (lmstudio-community/Bonsai-27B-GGUF, Q1_0) -> Bonsai-27B-1bit-Q1_0-LMStudio

The answer directory name differs from the payload model id so these runs
do not collide with the server-side results (Q4_0 lossless repack).
LM Studio returns no llama.cpp `timings`, so `duration` will be 0 —
durations are not used in the analysis.

Run with caffeinate to keep the Mac awake:
  caffeinate -i python3 -u run_lmstudio.py
"""
import config
from src.AnswerGenerator import AnswerGenerator
from src.LemonadeHandler import LemonadeHandler

LMSTUDIO_URL = "http://localhost:1234/v1"

# (payload model id in LM Studio, answer directory name)
MODELS = [
    ("bonsai-8b", "Bonsai-8B-1bit-Q1_0-LMStudio"),
    ("bonsai-27b", "Bonsai-27B-1bit-Q1_0-LMStudio"),
]

if __name__ == '__main__':
    generator = AnswerGenerator(config.DATASET_DIR)
    for payload_id, dir_name in MODELS:
        print(f"=== {dir_name} (payload id: {payload_id}) ===")
        handler = LemonadeHandler(payload_id, LMSTUDIO_URL, load_on_missing = False)
        generator.generate(handler, dir_name)
    print("LM_STUDIO_MODELS_DONE")
