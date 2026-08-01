"""Automatic completeness annotation, mirroring annotate.py's scoring.

The interactive annotate.py scores each answer as
    score = matched / (len(selected_classes) + len(concepts))
by substring-matching classes/concepts against the answer, asking a human
to confirm misses. This script applies the same matching WITHOUT the human
confirmation, so scores are a lower-bound proxy of the paper's completeness.

is_correct cannot be automated and is left as None — real correctness
annotation still goes through evaluate.py (Objective 1).

Usage: python3 auto_annotate.py <answers_dir> <out_dir>
Writes <out_dir>/<model>/<condition>/<file> with the same JSON shape as the
reference evaluations: [{question_id, is_correct, score, missing_concepts}].
"""
import json
import re
import sys
from pathlib import Path

def normalize(text):
    # CamelCase class names ("TwoFingerClaw") must match their natural
    # renderings ("two-finger claw", "two finger claw") — compare on
    # alphanumerics only
    return re.sub(r"[^a-z0-9]", "", text.lower())

def auto_evaluate(answer_file):
    data = json.load(open(answer_file))
    concepts = data["concepts"]
    evaluations = []
    for answer_data in data["answers"]:
        text = normalize(answer_data.get("answer") or "")
        selected_classes = answer_data.get("selected_classes", [])
        total = len(selected_classes) + len(concepts)
        matched = 0
        missing = []
        for value in list(selected_classes) + list(concepts):
            if normalize(value) in text:
                matched += 1
            else:
                missing.append(value)
        evaluations.append({
            "question_id": answer_data["id"],
            "is_correct": None,  # needs human annotation (evaluate.py)
            "score": matched / total if total > 0 else 0,
            "missing_concepts": missing,
        })
    return evaluations

if __name__ == '__main__':
    answers_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    count = 0
    for answer_file in sorted(answers_dir.rglob("*.json")):
        rel = answer_file.relative_to(answers_dir)
        target = out_dir / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(auto_evaluate(answer_file), f, indent = 2)
        count += 1
    print(f"auto-annotated {count} files -> {out_dir}")
