"""Generate a concepts-in-prompt variant of the question set.

The benchmark scores completeness against a fixed concept list per rule
(data["concepts"]) — but never shows it to the model. This variant appends
the expected concepts to the instruction, turning lexical completeness into
a specified task: if coverage jumps, the completeness failures were
underspecification, not model incapacity.

Single manipulation: original instruction + one checklist sentence.
Usage:
  python3 make_concepts_questions.py <src_dataset_dir> <dst_dataset_dir>
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
        concepts = ", ".join(data["concepts"])
        data["init_prompt"][0]["content"] += (
            f" Required concepts: the explanation must explicitly cover all of "
            f"these aspects: {concepts}."
        )
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (concepts-in-prompt) -> {dst / 'questions'}")
