"""Compare two evaluation trees (e.g. a student's annotations vs the paper's
reference evaluations) and report inter-annotator agreement.

Pairs entries by (model, condition, question-file, variation-id suffix) and
computes:
  - Cohen's kappa on is_correct (boolean)
  - Pearson and Spearman correlations on the completeness score
  - mean score on both sides

Usage: python3 compare_annotations.py <eval_dir_A> <eval_dir_B>
(pure stdlib)
"""
import json
import statistics
import sys
from pathlib import Path

def load(eval_dir):
    entries = {}
    for f in Path(eval_dir).rglob("*.json"):
        rel = f.relative_to(eval_dir)
        if len(rel.parts) < 3:
            continue
        key_prefix = (rel.parts[0], rel.parts[1], f.stem.replace("_evaluations", ""))
        for e in json.load(open(f)):
            entries[key_prefix + (e["question_id"].split("_")[-1],)] = e
    return entries

def cohens_kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa = sum(a) / n
    pb = sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")

def pearson(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")

def ranks(xs):
    order = sorted(range(len(xs)), key = lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        mean_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[order[k]] = mean_rank
        i = j + 1
    return r

def spearman(a, b):
    return pearson(ranks(a), ranks(b))

if __name__ == '__main__':
    dir_a, dir_b = sys.argv[1], sys.argv[2]
    A, B = load(dir_a), load(dir_b)
    keys = sorted(set(A) & set(B))
    if not keys:
        sys.exit(f"no paired entries between {dir_a} and {dir_b}")

    sa = [A[k]["score"] for k in keys]
    sb = [B[k]["score"] for k in keys]
    ca = [A[k]["is_correct"] for k in keys if A[k]["is_correct"] is not None and B[k]["is_correct"] is not None]
    cb = [B[k]["is_correct"] for k in keys if A[k]["is_correct"] is not None and B[k]["is_correct"] is not None]

    print(f"paired answers: {len(keys)}")
    print(f"completeness score:  A mean {statistics.mean(sa):.3f}   B mean {statistics.mean(sb):.3f}")
    print(f"  pearson r  = {pearson(sa, sb):.3f}")
    print(f"  spearman r = {spearman(sa, sb):.3f}")
    if ca:
        print(f"correctness:  n {len(ca)}   A rate {sum(ca)/len(ca):.3f}   B rate {sum(cb)/len(cb):.3f}")
        print(f"  cohen's kappa = {cohens_kappa(ca, cb):.3f}")
    else:
        print("correctness: no paired human annotations (is_correct missing)")
