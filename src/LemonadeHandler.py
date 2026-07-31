import json
import time
import urllib.error
import urllib.request

class LemonadeHandler:
	"""Drop-in replacement for OllamaHandler targeting a Lemonade Server
	(OpenAI-compatible) endpoint instead of Ollama.

	Same interface: call(question) -> (answer_text, duration).
	Duration is reported on the same scale as OllamaHandler
	((prompt_eval_duration + eval_duration) / 1000, i.e. microseconds).

	Lemonade evicts models from memory when another model is loaded or
	after idle time, answering chat requests with 'model_not_loaded'.
	The handler therefore (re)loads the model via /api/v1/load and
	retries transparently.
	"""
	def __init__(self, model, base_url="http://localhost:13305/api/v1"):
		self.model_ = model
		self.base_url_ = base_url.rstrip("/")

	# Some chat templates (e.g. Gemma) reject consecutive same-role
	# messages ("roles must alternate"). The benchmark's init_prompt
	# starts with two consecutive user messages, so fold them into one;
	# the content is unchanged, only joined with a newline.
	def _merge_same_role(self, messages):
		merged = []
		for m in messages:
			if merged and merged[-1]["role"] == m["role"]:
				merged[-1]["content"] += "\n" + m["content"]
			else:
				merged.append({"role": m["role"], "content": m["content"]})
		return merged

	def _post(self, path, payload, timeout = None):
		req = urllib.request.Request(
			self.base_url_ + path,
			data = json.dumps(payload).encode(),
			headers = {"Content-Type": "application/json"},
		)
		with urllib.request.urlopen(req, timeout = timeout) as resp:
			return json.load(resp)

	def _load_model(self):
		# loading a large model (gpt-oss-120b) can take several minutes
		self._post("/load", {"model_name": self.model_}, timeout = 1800)

	def _call_once(self, question):
		payload = {
			"model": self.model_,
			"messages": self._merge_same_role(question),
			"temperature": 0,
			"stream": False,
		}
		return self._post("/chat/completions", payload)

	def call(self, question, verbose = False, full_verbose = False):
		response = None
		for attempt in range(4):
			try:
				response = self._call_once(question)
				break
			except urllib.error.HTTPError as e:
				body = e.read().decode(errors = "replace")
				if "model_not_loaded" in body and attempt < 3:
					print(f"model {self.model_} not loaded, loading (attempt {attempt + 1})...")
					self._load_model()
					continue
				raise
			except (urllib.error.URLError, TimeoutError):
				if attempt < 3:
					time.sleep(10 * (attempt + 1))
					continue
				raise

		message = response["choices"][0]["message"]
		# reasoning models (gpt-oss): chain-of-thought goes to
		# 'reasoning_content', the final answer stays in 'content'
		answer = message.get("content") or ""

		if(verbose == True):
			if(full_verbose == True):
				print("question is : ")
				for elem in question:
					print("\t--", elem)
				print("answer is : ", response)
			else:
				print("question is : ", question[-2]['content'])
				print("answer is : ", answer)

		# llama.cpp reports timings in milliseconds; convert to the
		# microsecond-ish scale the Ollama handler produced
		timings = response.get("timings") or {}
		duration = (timings.get("prompt_ms", 0) + timings.get("predicted_ms", 0)) * 1000.

		return (answer, duration)
