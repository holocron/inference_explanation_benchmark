"""Run the benchmark for ONE model on our own llama-server instance.

lemond holds a single resident LLM slot (gpt-oss-120b, busy 24/7 with rag
gists) and must never be disturbed. Small models therefore get their own
llama-server process on port 9101, one model at a time:

    python3 run_own.py Gemma-3-4b-it-GGUF

The server is started with the same flags the box's lemond config uses
(-ngl 99 --n-cpu-moe 0 --cache-ram 0), runs all questions for the model,
and is then terminated — a clean unload before the next model starts.
For gpt-oss-120b-GGUF itself, use generate_responses.py (goes through the
lemond router; nothing is loaded or unloaded by us).
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import config
from src.AnswerGenerator import AnswerGenerator
from src.LemonadeHandler import LemonadeHandler

PORT = 9101
CTX_SIZE = 8192  # prompts are ~2-4k tokens; keep KV cache small

def wait_ready(base_url, proc, attempts = 150):
  for _ in range(attempts):
    if proc.poll() is not None:
      raise RuntimeError("llama-server exited early, see server log")
    try:
      urllib.request.urlopen(base_url + "/models", timeout = 2)
      return
    except Exception:
      time.sleep(2)
  raise RuntimeError("llama-server did not become ready in time")

if __name__ == '__main__':
  if len(sys.argv) < 2 or len(sys.argv) > 3:
    sys.exit("usage: python3 run_own.py <model_id from config.LOCAL_GGUF> [dataset_dir]")

  model = sys.argv[1]
  dataset_dir = Path(sys.argv[2]) if len(sys.argv) == 3 else config.DATASET_DIR
  gguf = config.LOCAL_GGUF[model]
  base_url = f"http://localhost:{PORT}/v1"

  log_path = config.BASE_DIR / "logs" / f"{model.replace('/', '_')}_server.log"
  log_path.parent.mkdir(exist_ok = True)
  server_log = open(log_path, "w")

  server = subprocess.Popen(
      ["llama-server",
       "-m", str(gguf),
       "--port", str(PORT),
       "--ctx-size", str(CTX_SIZE),
       "-ngl", "99",
       "--n-cpu-moe", "0",
       "--cache-ram", "0",
       "--jinja",
       "--no-webui"],
      stdout = server_log,
      stderr = subprocess.STDOUT,
  )
  print(f"llama-server started (pid {server.pid}), log: {log_path}")

  try:
    wait_ready(base_url, server)
    print("server ready, running benchmark...")
    handler = LemonadeHandler(model, base_url, load_on_missing = False)
    AnswerGenerator(dataset_dir).generate(handler, model)
  finally:
    server.terminate()
    server.wait()
    server_log.close()
    print("llama-server stopped (clean unload)")
