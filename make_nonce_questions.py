"""Generate a nonce-word variant of the question set (Wug-test style).

The benchmark anonymises individuals as random gibberish (v, yo, onq, gjqb),
which conflates verbalisation skill with robustness to token noise. This
script rewrites each question variation, replacing every gibberish name with
a pronounceable nonce word (wug, dax, ...) — consistent within a variation,
fresh per variation, exactly like the original generator.

Output mirrors the dataset layout so run_own.py can point at it:
  python3 make_nonce_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import random
import re
import sys
from pathlib import Path

# Wug-test style: phonotactically natural, no meaning, no collisions with
# class names or English words used in the dataset
NONCE_POOL = [
    "wug", "dax", "fep", "tov", "gip", "rif", "bose", "han",
    "mep", "sig", "lorn", "tame", "zek", "nulf", "pab", "jex",
]

def nonce_names(names, rng):
    return rng.sample(NONCE_POOL, len(names))

def replace_names(text, mapping):
    for old, new in mapping.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    return text

if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])
    rng = random.Random(42)  # reproducible mappings

    converted = 0
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        for question in data["questions"]:
            names = question.get("selected_names", [])
            if not names:
                continue
            mapping = dict(zip(names, nonce_names(names, rng)))
            question["question"] = replace_names(question["question"], mapping)
            question["selected_names"] = [mapping[n] for n in names]

        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files -> {dst / 'questions'}")
