"""Pre-generate reading aids for the annotation tool.

For every answer in the given answers file(s), breaks the answer into
atomic claims (numbered, English) — bridging the gap between the dense
model prose and the justification triples the annotator must check against.
The claims are a COMPREHENSION AID — the triples and the answer itself
remain the source of truth.

Usage (on holominix, model = gpt-oss-120b via lemond):
  python3 make_annotation_glosses.py <answers_file_or_dir> <out_dir>

Output mirrors the input layout with {question_id: {"claims": [...]}}.
annotate.py picks these up automatically from an "answers_glosses"
directory mirroring "answers".
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from src.OpenAIHandler import OpenAIHandler

GLOSS_PROMPT = """You help an annotator verify natural-language verbalizations of formal logical inferences.

Verbalization:
{answer}

Break the verbalization into ATOMIC CLAIMS — a numbered list of every distinct fact it states (entities, roles, properties, comparisons with their direction and values). One claim per line, short, no interpretation, no additions. Keep the original English wording of key terms.

Respond with ONLY JSON:
{{"claims": ["...", "..."]}}"""

def gloss_one(handler, answer_text, retries = 3):
    messages = [{"role": "user", "content": GLOSS_PROMPT.format(answer = answer_text)}]
    for attempt in range(retries):
        try:
            raw, _ = handler.call(messages)
            return json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        except (json.JSONDecodeError, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(5)

if __name__ == '__main__':
    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    handler = OpenAIHandler("gpt-oss-120b-GGUF", "http://localhost:13305/api/v1", load_on_missing = False)

    files = [src] if src.is_file() else sorted(src.rglob("*.json"))
    base = src if src.is_dir() else src.parent
    for answer_file in files:
        data = json.load(open(answer_file))
        glosses = {}
        for a in data["answers"]:
            glosses[a["id"]] = gloss_one(handler, a.get("answer") or "")
        rel = answer_file.relative_to(base)
        target = out_dir / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(glosses, f, indent = 2, ensure_ascii = False)
        print(f"glossed {rel} -> {target}")
