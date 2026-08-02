"""Generate a pre-verbalized variant: justification triples are converted to
simple English facts DETERMINISTICALLY (template table, no model), and the
model is only asked to fuse the facts into a coherent explanation.

Motivation (established by manual probes): an SLM asked to rewrite triples
as sentences corrupts a stochastic 5-15% of facts per attempt (inverted
subclass/reachability, dropped comparisons, wrong entity mapping). The
conversion must therefore be code; only the fusion is delegated to the model.

Usage:
  python3 make_verbalized_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import re
import sys
from pathlib import Path

VERBALIZE_INSTRUCTION = (
    "You are an AI model specialized in explaining formal logical inferences in natural language. "
    "Below is an inference derived by a rule-based reasoner, followed by the facts that justify it. "
    "Combine the facts into a clear, coherent explanation of the inference in 2-4 short sentences. "
    "Cover EVERY fact listed, including every numeric comparison with its direction and values. "
    "Always refer to entities by their class name (e.g., write 'The human' for indiv_1|Type|Human)."
)

def _val(token):
    m = re.match(r"(integer|boolean|string)#(.+)", token)
    return m.group(2) if m else token

def fact_for(triple):
    parts = [p.strip() for p in triple.split("|")]
    if len(parts) != 3:
        return None
    s, rel, o = parts
    templates = {
        "Type":                 f"{s} is a {_val(o)}",
        "SubClassOf":           f"{s} is a type of {o}",
        "hasCapability":        f"{s} has the capability {o}",
        "isCapabilityOf":       f"{s} is the capability of {o}",
        "hasDisposition":       f"{s} has the disposition {o}",
        "isDispositionOf":      f"{s} is the disposition of {o}",
        "hasComponent":         f"{s} has the component {o}",
        "hasPart":              f"{s} has the part {o}",
        "isReachableBy":        f"{s} is reachable by {o}",
        "isTouchableBy":        f"{s} is touchable by {o}",
        "isVisibleBy":          f"{s} is visible by {o}",
        "isApproachableBy":     f"{s} is approachable by {o}",
        "isContainedIn":        f"{s} is contained in {o}",
        "isLocatedInArea":      f"{s} is located in the area {o}",
        "isWithinGraspRangeOf": f"{s} is within grasping range of {o}",
        "hasOpeningWidth":      f"the opening width of {s} is {_val(o)}",
        "hasHoldingPartWidth":  f"the holding part width of {s} is {_val(o)}",
        "hasWeight":            f"the weight of {s} is {_val(o)}",
        "hasWeightLimit":       f"the weight limit of {s} is {_val(o)}",
        "hasMaximumDistanceRange": f"the maximum distance range of {s} is {_val(o)}",
        "isAtDistance":         f"{s} is at distance {_val(o)}",
        "hasApplicableForce":   f"the applicable force of {s} is {_val(o)}",
        "requiresForce":        f"{s} requires a force of {_val(o)}",
        "isRegistered":         f"{s} is registered: {_val(o)}",
        "isVisible":            f"{s} is visible: {_val(o)}",
        "IsAlreadyInUse":       f"{s} is already in use: {_val(o)}",
        "isATouchableObject":   f"{s} is a touchable object: {_val(o)}",
        "isOnRollableSurface":  f"{s} is on a rollable surface: {_val(o)}",
        "isBlockedBySomething": f"{s} is blocked by something: {_val(o)}",
        "holdsSomething":       f"{s} is holding something: {_val(o)}",
        "canBeUsed":            f"{s} can be used: {_val(o)}",
        "isAttachedToSomething": f"{s} is attached to something: {_val(o)}",
        "isActive":             f"{s} is active: {_val(o)}",
        "hasScannableCode":     f"{s} has the scannable code {o}",
        "isInFrontOf":          f"{s} is in front of {o}",
        "isCameraOf":           f"{s} is a camera of {o}",
    }
    if rel in templates:
        return templates[rel] + "."
    if rel == "EquivalentTo":
        return f"{s} is defined as: {o}."
    if rel == "SubPropertyOf":
        return f"({s}) is a way to achieve: {o}."
    return None

def fact_for_builtin(atom):
    m = re.match(r"(greaterThan|lesserThan|equal)\((.+),(.+)\)", atom.strip())
    if not m:
        return None
    op, a, b = m.group(1), _val(m.group(2)), _val(m.group(3))
    words = {"greaterThan": "greater than", "lesserThan": "less than", "equal": "equal to"}
    return f"{a} is {words[op]} {b}."

def verbalize_question(question_text):
    out_lines = []
    # split into the inference line and the justifications blob
    m = re.match(r"\s*-Inference\s*:\s*(.+?)\n\s*-Justifications\s*:\s*(.*)", question_text, re.S)
    if not m:
        return question_text
    inference, blob = m.group(1).strip(), m.group(2)
    # drop the formal rules section entirely — in the pre-verbalized variant
    # the facts already carry everything the rule says; formal syntax here
    # is pure noise and defeats the point of the variant
    rm = re.search(r"(\n\s*-Rules\s*:.*)", blob, re.S)
    if rm:
        blob = blob[:rm.start()]

    facts = []
    for item in blob.split(", "):  # built-ins use comma without space
        item = item.strip().rstrip(".")
        if not item:
            continue
        f = fact_for(item) or fact_for_builtin(item) or f"[formal] {item}."
        facts.append(f)

    lines = [f"-Inference : {inference}", "-Facts :"]
    lines += [f"  {i+1}. {f}" for i, f in enumerate(facts)]
    return "\n".join(lines)

if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    converted = 0
    uncovered = set()
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        data["init_prompt"][0]["content"] = VERBALIZE_INSTRUCTION
        data["init_prompt"] = data["init_prompt"][:1]  # zero-shot: pure fusion task
        for question in data["questions"]:
            question["question"] = verbalize_question(question["question"])
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (pre-verbalized facts) -> {dst / 'questions'}")
