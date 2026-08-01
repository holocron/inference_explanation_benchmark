"""LLM-as-judge evaluator for the benchmark answers.

Motivation: the paper's completeness metric is lexical (substring matching of
expected concepts, human-confirmed), and correctness is a single uncalibrated
binary judgment. This judge evaluates SEMANTICALLY with a fixed rubric and
temperature 0:

  correctness  — the answer states the inference and does not contradict or
                 invent facts relative to the justification triples
  completeness — for every expected item (selected classes + concepts), is it
                 conveyed, including by paraphrase?

Output per answer mirrors the reference evaluation JSON shape
({question_id, is_correct, score, missing_concepts}) so results drop straight
into stats_summary.py / compare_annotations.py. A judge_rationale field is
added for auditability (ignored by those tools).

Validate against the 2025 human evaluations before trusting:
  python3 llm_judge.py dataset_roman_2025/answers/llama3.2:3b/baseline <outdir> --judge gpt-oss-120b-GGUF
  python3 compare_annotations.py <outdir> dataset_roman_2025/evaluations

The judge model (gpt-oss-120b via the lemond router) is NOT part of the
evaluated lineup, so there is no self-judging. Judge requests go through
LemonadeHandler with load_on_missing=False — the 120b instance is managed
by lemond, we only send requests.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.LemonadeHandler import LemonadeHandler

JUDGE_PROMPT = """You are a strict evaluator of natural-language verbalizations of formal logical inferences.

An inference was derived by a rule-based reasoner (SWRL rules over an ontology). A language model verbalized the inference and its justification. Evaluate the verbalization.

## Input
INFERENCE AND JUSTIFICATION (semantic triples):
{question}

EXPECTED ITEMS the verbalization should convey (paraphrases and rewordings count):
{items}

VERBALIZATION TO EVALUATE:
{answer}

## Rubric
1. CORRECTNESS: true if the verbalization states the inference correctly and contains NO claims that contradict or are not supported by the justification triples (wrong comparisons, swapped roles, invented facts make it false). Awkward style or omissions do NOT affect correctness.
2. COMPLETENESS: for each expected item, decide whether the verbalization conveys it, INCLUDING by paraphrase (e.g. "two-finger claw", "the claw", "its gripper" all cover the item TwoFingerClaw).

## Output
Respond with ONLY a JSON object, no other text:
{{"correct": true|false, "covered": ["item1", ...], "missing": ["item2", ...], "rationale": "one sentence"}}"""

def judge_answer(handler, question_text, items, answer_text, retries = 3):
    prompt = JUDGE_PROMPT.format(
        question = question_text,
        items = ", ".join(items),
        answer = answer_text,
    )
    messages = [{"role": "user", "content": prompt}]
    for attempt in range(retries):
        try:
            raw, _ = handler.call(messages)
            start = raw.find("{")
            end = raw.rfind("}")
            verdict = json.loads(raw[start:end + 1])
            return verdict
        except (json.JSONDecodeError, ValueError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(5)

def judge_file(handler, answer_file):
    data = json.load(open(answer_file))
    concepts = data["concepts"]
    evaluations = []
    for answer_data in data["answers"]:
        items = list(answer_data.get("selected_classes", [])) + list(concepts)
        verdict = judge_answer(
            handler,
            answer_data["question"],
            items,
            answer_data.get("answer") or "",
        )
        covered = set(verdict.get("covered", []))
        evaluations.append({
            "question_id": answer_data["id"],
            "is_correct": bool(verdict.get("correct")),
            "score": len(covered) / len(items) if items else 0,
            "missing_concepts": verdict.get("missing", []),
            "judge_rationale": verdict.get("rationale", ""),
        })
    return evaluations

if __name__ == '__main__':
    answers_path = Path(sys.argv[1])   # file or directory
    out_dir = Path(sys.argv[2])
    judge_model = "gpt-oss-120b-GGUF"
    if "--judge" in sys.argv:
        judge_model = sys.argv[sys.argv.index("--judge") + 1]

    handler = LemonadeHandler(judge_model, "http://localhost:13305/api/v1", load_on_missing = False)

    files = [answers_path] if answers_path.is_file() else sorted(answers_path.rglob("*.json"))
    base = answers_path if answers_path.is_dir() else answers_path.parent
    for answer_file in files:
        rel = answer_file.relative_to(base)
        target = out_dir / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(judge_file(handler, answer_file), f, indent = 2)
        print(f"judged {rel} -> {target}")
