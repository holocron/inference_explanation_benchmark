import json
import urllib.request

class LemonadeHandler:
	"""Drop-in replacement for OllamaHandler targeting a Lemonade Server
	(OpenAI-compatible) endpoint instead of Ollama.

	Same interface: call(question) -> (answer_text, duration).
	Duration is reported on the same scale as OllamaHandler
	((prompt_eval_duration + eval_duration) / 1000, i.e. microseconds).
	"""
	def __init__(self, model, base_url="http://localhost:13305/api/v1"):
		self.model_ = model
		self.base_url_ = base_url.rstrip("/")

	def call(self, question, verbose = False, full_verbose = False):
		payload = {
			"model": self.model_,
			"messages": question,
			"temperature": 0,
			"stream": False,
		}
		req = urllib.request.Request(
			self.base_url_ + "/chat/completions",
			data = json.dumps(payload).encode(),
			headers = {"Content-Type": "application/json"},
		)
		with urllib.request.urlopen(req) as resp:
			response = json.load(resp)

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
