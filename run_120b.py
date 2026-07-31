"""Run the benchmark for gpt-oss-120b through the lemond router.

The 120b instance is permanently loaded and managed by lemond (rag gists
run on it 24/7) — this script only SENDS REQUESTS, it never loads or
unloads anything (see config.NEVER_LOAD and LemonadeHandler's
load_on_missing=False path).
"""
import config
config.MODELS = ["gpt-oss-120b-GGUF"]
exec(open("generate_responses.py").read())
