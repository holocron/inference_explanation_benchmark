"""Generate a zero-shot (no-CoT) variant of the question set.

The benchmark's init_prompt = instructions + 4 few-shot (user/assistant)
example pairs. The examples model a LACONIC style, which may trade off
against the completeness instruction. This ablation strips the examples,
keeping only the instruction (message 0); the trailing CoT prefill appended
by AnswerGenerator is part of the paper's setup and is kept.

Usage:
  python3 make_nocot_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import sys
from pathlib import Path

if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    converted = 0
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        data["init_prompt"] = data["init_prompt"][:1]  # instructions only
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (zero-shot) -> {dst / 'questions'}")
