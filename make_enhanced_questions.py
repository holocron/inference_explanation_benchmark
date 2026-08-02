"""Generate an enhanced-prompt variant of the question set.

Three instruction edits vs the paper's prompt (message 0 only — CoT examples
and prefill untouched, single manipulation):
  1. STRUCTURE: "a single, fluent sentence" -> "2-4 short, simple sentences"
     (the one-sentence rule produced overloaded sentences and comparison
     inversions; short sentences are verifiable)
  2. COMPLETENESS: "Include all justifications" -> explicit checklist
     (every entity+class, every relationship, every numeric comparison with
     direction and values, no skipped chain steps)
  3. NAMING: negative "Don't refer to individual names" -> positive
     "Always refer to entities by their class name" (LLMs follow positive
     instructions more reliably; zero-shot run showed the negation ignored)

Usage:
  python3 make_enhanced_questions.py <src_dataset_dir> <dst_dataset_dir>
  # then: python3 run_own.py <model> <dst_dataset_dir>
"""
import json
import sys
from pathlib import Path

ENHANCED_INSTRUCTION = (
    "You are an AI model specialized in explaining formal logical inferences and their "
    "justifications in natural language. Task Overview: Convert inferences and justifications "
    "from rules into clear, natural language explanations. Rules infer new facts in ontologies "
    "based on known facts and logical conditions. "
    "Input: Inference: A statement derived from the rules. Justifications: Triples specifying "
    "semantic relationships between entities or concepts. Rules: The rules used to make such "
    "an inference. "
    "Output Requirements: "
    "Structure: Write 2-4 short, simple sentences; do not pack multiple facts into one long "
    "sentence, and do not use bullet points. "
    "Completeness: Mention EVERY fact from the justification triples — every entity and its "
    "class, every relationship, and every numeric comparison with its direction and values. "
    "Do not skip steps of the reasoning chain. "
    "Concept-Driven: Always refer to entities by their class name (e.g., write 'The human' "
    "for indiv_1|Type|Human). "
    "Edge Case: For inferences involving chains, equivalent concepts, subclasses or "
    "subproperties, explicitly reflect these relationships in the explanation."
)

if __name__ == '__main__':
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2])

    converted = 0
    for question_file in sorted((src / "questions").rglob("*.json")):
        data = json.load(open(question_file))
        assert len(data["init_prompt"][0]["content"]) > 0
        data["init_prompt"][0]["content"] = ENHANCED_INSTRUCTION
        rel = question_file.relative_to(src / "questions")
        target = dst / "questions" / rel
        target.parent.mkdir(parents = True, exist_ok = True)
        with open(target, "w") as f:
            json.dump(data, f, indent = 2)
        converted += 1
    print(f"converted {converted} question files (enhanced prompt) -> {dst / 'questions'}")
