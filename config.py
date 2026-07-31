from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset_2026"

# Backend: "lemonade" (Lemonade Server, OpenAI-compatible) or "ollama"
BACKEND = "lemonade"
LEMONADE_BASE_URL = "http://localhost:13305/api/v1"

# Model ids as served by Lemonade (see /api/v1/models on the server)
MODELS = [
  "Gemma-3-4b-it-GGUF",
  "Llama-3.2-3B-Instruct-GGUF",
  "Bonsai-8B-gguf",
  "gpt-oss-20b-mxfp4-GGUF",
  "gpt-oss-120b-GGUF",
]
# Ollama ids used by the original paper's setup:
# MODELS = ["llama3.2:3b", "gemma3:4b"] #, "llama3.1:8b", "gemma2:2b", "gemma2:9b", "mistral-nemo:12b", "mistral-small:22b"]
