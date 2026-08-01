import json
import re
import time
import urllib.error
import urllib.request

class LemonadeHandler:
	"""Drop-in replacement for OllamaHandler targeting OpenAI-compatible
	endpoints (Lemonade Server router or a raw llama-server instance).

	Same interface: call(question) -> (answer_text, duration).
	Duration is reported on the same scale as OllamaHandler
	((prompt_eval_duration + eval_duration) / 1000, i.e. microseconds).

	Backend quirks handled here:
	- Lemonade evicts models and answers 'model_not_loaded' -> (re)load via
	  /api/v1/load and retry (only when load_on_missing=True; for the
	  lemond-resident gpt-oss-120b we wait and retry instead).
	- Strict chat templates (Gemma) reject consecutive same-role messages
	  -> merged in _merge_same_role.
	- Thinking templates (Bonsai, gpt-oss) reject the benchmark's trailing
	  assistant prefill ("prefill is incompatible with enable_thinking").
	  Fallback chain per request: (1) as-is, (2) chat_template_kwargs
	  enable_thinking=false, (3) drop the trailing assistant message.
	  (2) keeps the paper's prompt intact for models whose template
	  supports the switch (Bonsai); (3) is the last resort for gpt-oss,
	  whose harmony template has no such switch — noted for the report.
	- <think>...</think> blocks (emitted even when thinking is disabled)
	  are stripped from the answer.
	"""
	def __init__(self, model, base_url="http://localhost:13305/api/v1", load_on_missing=True):
		self.model_ = model
		self.base_url_ = base_url.rstrip("/")
		# False for models managed elsewhere (e.g. gpt-oss-120b in lemond):
		# wait-and-retry instead of issuing /load ourselves
		self.load_on_missing_ = load_on_missing
		# learned per model after the first fallback: 0 = as-is,
		# 1 = enable_thinking=false, 2 = drop assistant prefill
		self.prefill_mode_ = 0

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

	def _call_once(self, messages):
		payload = {
			"model": self.model_,
			"messages": messages,
			"temperature": 0,
			"stream": False,
		}
		if self.prefill_mode_ == 1:
			payload["chat_template_kwargs"] = {"enable_thinking": False}
		if self.prefill_mode_ == 2 and messages and messages[-1]["role"] == "assistant":
			payload["messages"] = messages[:-1]
		return self._post("/chat/completions", payload)

	@staticmethod
	def _strip_think(text):
		return re.sub(r"<think>.*?</think>", "", text, flags = re.S).strip()

	def call(self, question, verbose = False, full_verbose = False):
		messages = self._merge_same_role(question)
		response = None
		for attempt in range(6):
			try:
				response = self._call_once(messages)
				break
			except urllib.error.HTTPError as e:
				body = e.read().decode(errors = "replace")
				if "prefill is incompatible with enable_thinking" in body:
					if self.prefill_mode_ == 0:
						print(f"{self.model_}: thinking template, retrying with enable_thinking=false")
						self.prefill_mode_ = 1
						continue
					if self.prefill_mode_ == 1:
						print(f"{self.model_}: enable_thinking=false failed, dropping assistant prefill")
						self.prefill_mode_ = 2
						continue
				# gpt-oss (harmony template): enable_thinking=false is not
				# supported and the request fails with a 400/500 parse error
				# instead of the prefill message above -> drop the prefill
				if self.prefill_mode_ == 1 and e.code in (400, 500) and "model_not_loaded" not in body:
					print(f"{self.model_}: enable_thinking=false rejected (HTTP {e.code}), dropping assistant prefill")
					self.prefill_mode_ = 2
					continue
				if "model_not_loaded" in body and attempt < 3:
					if self.load_on_missing_:
						print(f"model {self.model_} not loaded, loading (attempt {attempt + 1})...")
						self._load_model()
					else:
						print(f"model {self.model_} temporarily unavailable, waiting (attempt {attempt + 1})...")
						time.sleep(60)
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
		answer = self._strip_think(message.get("content") or "")

		if(verbose == True):
			if(full_verbose == True):
				print("question is : ")
				for elem in question:
					print("\t--", elem)
				print("answer is : ", response)
			else:
				print("question is : ", messages[-1]['content'] if self.prefill_mode_ != 2 else messages[-2]['content'])
				print("answer is : ", answer)

		# llama.cpp reports timings in milliseconds; convert to the
		# microsecond-ish scale the Ollama handler produced
		timings = response.get("timings") or {}
		duration = (timings.get("prompt_ms", 0) + timings.get("predicted_ms", 0)) * 1000.

		return (answer, duration)
