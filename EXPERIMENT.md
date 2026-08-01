# Experiment lineup decisions (2026 dataset)

## Final lineup (in the analysis)

| Model | Tier | Serving | Notes |
|---|---|---|---|
| Gemma-3-4b-it (Q4_K_M) | SLM | own llama-server | prefill OK after merging consecutive user messages |
| Llama-3.2-3B-Instruct (UD-Q4_K_XL) | SLM | own llama-server | prefill OK |
| Bonsai-8B 1.58-bit ternary (Q4_0 lossless repack) | SLM | own llama-server | native ternary files need PrismML's llama.cpp fork; repack runs on stock; `enable_thinking=false` fallback |
| Qwen3-32B (Q4_K_M) | large | own llama-server | `enable_thinking=false` fallback, paper prompt incl. CoT prefill used verbatim |

## Excluded (data kept in `dataset_2026/answers/` as archive, NOT in the analysis)

| Model | Reason |
|---|---|
| gpt-oss-20b, gpt-oss-120b | harmony chat template rejects the paper's CoT prefill ("assistant prefill is incompatible with enable_thinking"); `enable_thinking=false` not supported by the template (500 parse error) → cannot run under the paper's exact prompt conditions |
| Bonsai-8B 1-bit Q1_0 (LM Studio), Bonsai-27B 1-bit Q1_0 (LM Studio) | initially mistaken for the same model as the ternary repack; they are DIFFERENT PrismML products (1-bit vs 1.58-bit). 1-bit underperforms the ternary tier (0.528 vs 0.617 auto-completeness baseline), matching PrismML's own whitepaper (76.1 vs 80.5 avg). Out of scope |

## Conditions

`baseline` and `labeled` (the 2026 dataset ships these two; the paper's
`shuffle` / `rule` conditions are not generated for 2026 — candidate for the
robustness extension).

## Identifier experiment (in progress)

`dataset_2026_nonce/` — same questions with gibberish identifiers (v, yo, onq)
replaced by pronounceable nonce words (wug, dax, ...), seed 42. Tests whether
scores are depressed by token noise rather than verbalisation skill.
