"""Generate the v2 pre-verbalized variant: essential-prerequisites framing.

v1 established the deterministic triple->fact conversion. v2 changes the
instruction based on the manual-probe finding: models filter out
"background" facts (reachability, disposition) by their own relevance
theory — but reframing them as essential prerequisites lifts the filter
("Additionally, the Lunchbox is reachable by the Tiago, which is
necessary..."). Also adds one worked example demonstrating the
identifier -> class-name mapping.

Usage:
  python3 make_verbalized2_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_verbalized_questions import verbalize_question

INSTRUCTION = (
    "You are an AI model specialized in explaining logical inferences in natural language. "
    "Below is an inference derived by a rule-based reasoner, followed by the facts that justify it. "
    "Combine the facts into a clear, coherent explanation of the inference in sentences. "
    "Cover all facts and prerequisites listed, including every numeric comparison with its "
    "direction and values, and every entity's capability and disposition. "
    "Prerequisites listed are important and are essential part of inference. "
    "Always refer to entities by their class name (e.g., write \"The Pr2 robot\" instead of its identifier)."
)

EXAMPLE_QUESTION = (
    "Inference: gu canSpeakWith zvk.\n"
    "Facts:\n"
    "  1. gu is a Robot.\n"
    "  2. gu has the capability kitw, a VerbalCommunicationCapability.\n"
    "  3. zvk is a Human.\n"
    "  4. zvk has the disposition roro, a VerbalCommunicationDisposition.\n"
    "  5. zvk is available: true.\n"
    "  6. gu is facing zvk."
)
EXAMPLE_ANSWER = (
    "The robot can speak with the human because it has a verbal communication capability, "
    "the human has a verbal communication disposition and is available, and the robot is "
    "facing the human."
)

def to_plain(text):
    """'-Inference : xudxay|canGrasp|mbdj\n-Facts :' -> human sentence form,
    matching the manual-probe prompt exactly."""
    def repl(m):
        pred = re.sub(r"(?<!^)(?=[A-Z])", " ", m.group(2)).lower()
        return f"Inference: {m.group(1)} {pred} {m.group(3)}."
    text = re.sub(r"-Inference : (\S+)\|(\S+)\|(\S+)", repl, text)
    return text.replace("-Facts :", "Facts:")

if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    converted = 0
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        data["init_prompt"] = [
            {"role": "user", "content": INSTRUCTION},
            {"role": "user", "content": EXAMPLE_QUESTION},
            {"role": "assistant", "content": EXAMPLE_ANSWER},
        ]
        for question in data["questions"]:
            question["question"] = to_plain(verbalize_question(question["question"]))
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (verbalized-v2, essential prerequisites) -> {dst / 'questions'}")
