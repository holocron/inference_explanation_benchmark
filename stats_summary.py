"""Paper-style summary statistics over an evaluations directory.

Walks <eval_dir>/<model>/<condition>/*.json and prints mean/median
completeness score per model, condition and complexity level — the same
cut as the paper's analysis (statistical_tests.py), without pandas.

Usage: python3 stats_summary.py <eval_dir> [--correctness]
With --correctness, also reports correctness rate over the entries that
have a human is_correct flag (auto annotations have None and are skipped).
"""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

def load(eval_dir):
    rows = []
    for f in sorted(Path(eval_dir).rglob("*.json")):
        rel = f.relative_to(eval_dir)
        if len(rel.parts) < 3:
            continue
        model, condition = rel.parts[0], rel.parts[1]
        stem = f.stem  # e.g. a_canGrasp_easy_baseline(_evaluations)
        parts = stem.split("_")
        # question names look like a_<Rule>_<complexity>_<condition>(...)
        rule = parts[1] if len(parts) > 1 else "?"
        complexity = parts[2] if len(parts) > 2 else "?"
        for e in json.load(open(f)):
            rows.append({
                "model": model,
                "condition": condition,
                "rule": rule,
                "complexity": complexity,
                "score": e["score"],
                "is_correct": e.get("is_correct"),
            })
    return rows

def fmt(x):
    return f"{x:.3f}" if x is not None else "-"

if __name__ == '__main__':
    eval_dir = sys.argv[1]
    show_correctness = "--correctness" in sys.argv
    rows = load(eval_dir)
    if not rows:
        sys.exit(f"no evaluations found in {eval_dir}")

    # per model x condition
    groups = defaultdict(list)
    correct = defaultdict(list)
    for r in rows:
        groups[(r["model"], r["condition"])].append(r["score"])
        if r["is_correct"] is not None:
            correct[(r["model"], r["condition"])].append(r["is_correct"])

    print(f"{'model':<28} {'condition':<10} {'n':>4} {'mean':>7} {'median':>7}" + ("  correctness" if show_correctness else ""))
    for (model, condition), scores in sorted(groups.items()):
        line = f"{model:<28} {condition:<10} {len(scores):>4} {fmt(statistics.mean(scores)):>7} {fmt(statistics.median(scores)):>7}"
        if show_correctness:
            c = correct.get((model, condition))
            line += f"  {fmt(sum(c)/len(c)) if c else '-'} ({len(c)} annotated)"
        print(line)

    # per model x condition x complexity
    print()
    print(f"{'model':<28} {'condition':<10} {'complexity':<11} {'n':>4} {'mean':>7}")
    groups2 = defaultdict(list)
    for r in rows:
        groups2[(r["model"], r["condition"], r["complexity"])].append(r["score"])
    order = {"easy": 0, "medium": 1, "hard": 2}
    for (model, condition, complexity), scores in sorted(groups2.items(), key = lambda kv: (kv[0][0], kv[0][1], order.get(kv[0][2], 9))):
        print(f"{model:<28} {condition:<10} {complexity:<11} {len(scores):>4} {fmt(statistics.mean(scores)):>7}")
