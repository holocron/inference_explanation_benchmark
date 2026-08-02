"""Generate the scaffolded variant (v3): DeepSeek-style hardcoded paragraph
structure over deterministically pre-verbalized facts.

Manual probes showed: at maximal prompt specification, coverage hits 100%
and inter-model variance collapses to zero (Bonsai/Llama/Qwen produced
byte-identical paragraphs). This variant generalises that scaffold to the
whole benchmark: the 5-sentence paragraph skeleton is BUILT PER QUESTION
from the triples themselves (capability, component hierarchy, object part
hierarchy, accessibility, numeric comparison, conclusion).

Usage:
  python3 make_scaffolded_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_verbalized_questions import verbalize_question, _val

INSTRUCTION = (
    "You are an AI that writes natural-language explanations for logical inferences.\n"
    "OUTPUT REQUIREMENT: A single, coherent paragraph.\n"
    "CRITICAL – FORBIDDEN STRINGS: under NO circumstances may you write the entity "
    "identifiers ({ids}) in your output. Always refer to entities by their class name.\n"
    "Follow the REQUIRED PARAGRAPH STRUCTURE exactly, covering every listed fact, "
    "then pass the SELF-CHECK."
)

def split_camel(name):
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).lower()

def parse_items(blob):
    triples, builtins = [], []
    for item in blob.split(", "):
        item = item.strip().rstrip(".")
        if not item:
            continue
        parts = [p.strip() for p in item.split("|")]
        if len(parts) == 3:
            triples.append(parts)
        else:
            builtins.append(item)
    return triples, builtins

def build_scaffold(inference, triples, builtins):
    # inference: subj pred obj
    m = re.match(r"(\S+)\|(\S+)\|(\S+)", inference)
    subj, pred, obj = m.groups()
    verb = split_camel(pred).replace("can ", "")  # canGrasp -> grasp

    def type_of(name):
        for s, r, o in triples:
            if s == name and r == "Type":
                return o
        return None

    def subclasses(name):
        for s, r, o in triples:
            if s == name and r == "SubClassOf":
                return o
        return None

    agent_cls = type_of(subj) or "Agent"
    obj_cls = type_of(obj) or "Object"

    # component of agent (hasComponent) and its hierarchy
    comp = next((o for s, r, o in triples if s == subj and r == "hasComponent"), None)
    comp_cls = type_of(comp) if comp else None
    comp_parent = subclasses(comp_cls) if comp_cls else None
    comp_grand = subclasses(comp_parent) if comp_parent else None

    # object's part and hierarchy
    part = next((o for s, r, o in triples if s == obj and r == "hasPart"), None)
    part_cls = type_of(part) if part else None
    part_parent = subclasses(part_cls) if part_cls else None

    # accessibility
    acc_rel = next((r for s, r, o in triples
                    if s == obj and r in ("isReachableBy", "isTouchableBy", "isVisibleBy", "isApproachableBy")), None)
    acc_word = {"isReachableBy": "reachable", "isTouchableBy": "touchable",
                "isVisibleBy": "visible", "isApproachableBy": "approachable"}.get(acc_rel, "reachable")

    # numeric facts and comparison (render with class names, strip "has")
    def cls_of(name):
        return type_of(name) or name
    num_facts = [(cls_of(s), split_camel(r).removeprefix("has "), _val(o)) for s, r, o in triples if r.startswith("has") and "#" in o]
    comp_m = re.match(r"(greaterThan|lesserThan|equal)\((.+),(.+)\)", builtins[0]) if builtins else None

    # boolean flags (medium/hard)
    flags = [f"{s} is {split_camel(r)}: {_val(o)}" for s, r, o in triples if r[:2] == "is" and "#" in o and r not in ("isActive",)]

    sentences = []
    sentences.append(
        f'Sentence 1: Start with "The {agent_cls}, which is an Agent, can {verb} the {obj_cls} because it has a capability."')
    if comp and comp_cls:
        chain = f"The {agent_cls} has a component that is a {comp_cls}"
        if comp_parent:
            chain += f", which is a type of {comp_parent}"
        if comp_grand:
            chain += f", and {comp_parent} is a type of {comp_grand}"
        sentences.append(f'Sentence 2: State the component and its hierarchy: "{chain}."')
    if part and part_cls:
        p = f"The {obj_cls}, which is an Object, has a disposition and has a part that is a {part_cls}"
        if part_parent:
            p += f", which is a type of {part_parent}"
        sentences.append(f'Sentence 3: State the object and its properties: "{p}."')
    # accessibility + numbers + comparison
    s4 = f"The {obj_cls} is {acc_word} by the {agent_cls}"
    if num_facts:
        nums = "; ".join(f"the {r} of the {a} is {v}" for a, r, v in num_facts)
        s4 += f", and {nums}"
    if comp_m:
        op, a, b = comp_m.group(1), _val(comp_m.group(2)), _val(comp_m.group(3))
        words = {"greaterThan": "greater than", "lesserThan": "less than", "equal": "equal to"}
        s4 += f", so {a} is {words[op]} {b}"
    sentences.append(f'Sentence 4: State reachability and the numeric comparison: "{s4}."')
    if flags:
        sentences.append("Also include: " + "; ".join(flags) + ".")
    sentences.append(f'Sentence 5 (conclusion): "Therefore, the {agent_cls} can {verb} the {obj_cls}."')

    ids = {subj, obj, comp, part}
    ids |= {o for s, r, o in triples if r in ("hasCapability", "hasDisposition")}
    ids |= {s for s, r, o in triples if r in ("isCapabilityOf", "isDispositionOf")}
    return sentences, sorted(i for i in ids if i)

def subj_of(inference):
    m = re.match(r"(\S+)\|(\S+)\|(\S+)", inference)
    subj, pred, obj = m.groups()
    return f"{subj} {split_camel(pred)} {obj}"

def main():
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    converted = 0
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        for question in data["questions"]:
            qtext = question["question"]
            m = re.match(r"\s*-Inference\s*:\s*(.+?)\n\s*-Justifications\s*:\s*(.*)", qtext, re.S)
            inference, blob = m.group(1).strip(), m.group(2)
            rm = re.search(r"(\n\s*-Rules\s*:.*)", blob, re.S)
            if rm:
                blob = blob[:rm.start()]
            triples, builtins = parse_items(blob)
            scaffold, ids = build_scaffold(inference, triples, builtins)
            ids = sorted({i for i in ids if i})

            facts_text = verbalize_question(qtext)
            facts_text = facts_text[facts_text.find("-Facts :"):].replace("-Facts :", "FACTS:")

            prompt_parts = [
                INSTRUCTION.replace("{ids}", ", ".join(f'"{i}"' for i in ids)),
                "",
                "REQUIRED PARAGRAPH STRUCTURE:",
                *scaffold,
                "",
                "SELF-CHECK before outputting:",
                "[ ] No forbidden identifiers used.",
                "[ ] Reachability stated in the correct direction.",
                "[ ] Both numbers and the comparison direction stated.",
                "[ ] Disposition and the part hierarchy mentioned exactly once.",
                "",
                f"INFERENCE: {subj_of(inference)}",
                "",
                facts_text,
                "",
                "Write your paragraph below, following the structure precisely.",
            ]
            question["question"] = "\n".join(prompt_parts)

        data["init_prompt"] = data["init_prompt"][:1]  # zero-shot: scaffold carries everything
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (scaffolded v3) -> {dst / 'questions'}")

if __name__ == '__main__':
    main()
