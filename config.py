from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset_2026"

# Endpoints.
# Small models are served by our own llama-server instances (run_own.py),
# one at a time on port 9101, so lemond's single resident-LLM slot stays
# with gpt-oss-120b (rag gists run on it around the clock — never evict it).
# gpt-oss-120b itself is queried through the lemond router, where it is
# already loaded; we never issue load/unload for it.
LEMONADE_BASE_URL = "http://localhost:13305/api/v1"
OWN_SERVER_URL = "http://localhost:9101/v1"

MODELS = [
  "Gemma-3-4b-it-GGUF",
  "Llama-3.2-3B-Instruct-GGUF",
  "Bonsai-8B-1.58bit-Q4_0",
  "Qwen3-32B-GGUF",
]

MODEL_ENDPOINTS = {model: OWN_SERVER_URL for model in MODELS}

# Models we must never load/unload ourselves — managed elsewhere (lemond).
NEVER_LOAD = {"gpt-oss-120b-GGUF"}

# Local GGUF files for our own llama-server instances — same checkpoints
# (repo + quant) that lemond serves, downloaded to ./models.
# (Bonsai: lossless Q4_0 repack of the ternary weights — the native Q1_0
# needs PrismML's llama.cpp fork, stock builds reject ggml type 41.)
LOCAL_GGUF = {
  "Gemma-3-4b-it-GGUF":        BASE_DIR / "models/gemma-3-4b-it-Q4_K_M.gguf",
  "Llama-3.2-3B-Instruct-GGUF": BASE_DIR / "models/Llama-3.2-3B-Instruct-UD-Q4_K_XL.gguf",
  "Bonsai-8B-1.58bit-Q4_0":            BASE_DIR / "models/Ternary-Bonsai-8B-Q4_0-lossless.gguf",
  "Qwen3-32B-GGUF":            BASE_DIR / "models/Qwen3-32B-Q4_K_M.gguf",
}
