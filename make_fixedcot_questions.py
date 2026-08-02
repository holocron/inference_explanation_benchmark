"""Generate a fixed-examples variant: ORIGINAL instruction + CoT examples
rewritten for FULL coverage.

Ablation arm complementary to the enhanced-instruction variant. The paper's
CoT examples model laconic translations (numeric values and comparison
directions omitted). Hypothesis: examples carry the target behaviour more
than the instruction text (zero-shot collapse already showed they are
load-bearing). Only the 4 assistant example messages are replaced;
instruction, example questions, and prefill are identical to the paper.

Usage:
  python3 make_fixedcot_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import sys
from pathlib import Path

# rewritten assistant examples: every entity+class, every relationship,
# every numeric comparison with direction and values, chain steps made
# explicit — same fluent style as the originals
FIXED_EXAMPLES = {
    2: "Let's translate. Translation is the robot can speak with the human because the robot "
       "has a verbal communication capability, the human has a verbal communication disposition "
       "and is available, and the robot is facing the human: the robot is in front of an object "
       "that has the human seated on it, and being in front of an object with the human seated "
       "on it is a way of facing the human.",
    4: "Let's translate. Translation is the car can be towed by the vehicle because the vehicle "
       "has a towing capability, the car is a towable object, and the vehicle's towing capacity "
       "of 3000 is greater than the car's weight of 2000.",
    6: "Let's translate. Translation is the drone can inspect the bridge because it has an "
       "aerial inspection capability, which means it has at least one security camera and the "
       "capability to fly, the bridge is inspectable, and the drone's maximum inspection height "
       "of 200 is greater than the bridge's height of 100.",
    8: "Let's translate. Translation is the delivery robot can charge at the station because it "
       "has a charging capability through its exactly one charging connector, the station is "
       "powered and has a port that is a charging connector, both the robot's connector and the "
       "station's port are of type USB Type-C, and the robot's battery level of 15 is below its "
       "charging threshold of 20.",
}

if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    converted = 0
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        for idx, text in FIXED_EXAMPLES.items():
            assert data["init_prompt"][idx]["role"] == "assistant"
            data["init_prompt"][idx]["content"] = text
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (fixed CoT examples) -> {dst / 'questions'}")
