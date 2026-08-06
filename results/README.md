# Aggregated results

Cross-experiment result tables in CSV, for anyone who would rather read the numbers than the prose.
Each row names the experiment it came from; the experiment README is where the caveats live, and
several of these numbers are meaningless without them.

| File | Contents |
|---|---|
| [kie-f1.csv](kie-f1.csv) | Field-level extraction F1 by model and corpus |
| [counterparty-role.csv](counterparty-role.csv) | Business-gate error rates and McNemar p-values |
| [throughput-gb10.csv](throughput-gb10.csv) | Decode and aggregate throughput by model, backend and speculative setting |
| [speculative-decoding.csv](speculative-decoding.csv) | Acceptance rates and gains by workload |

## Three warnings before you use these

1. **Not all rows are comparable.** Different corpora, different ground-truth versions, different
   engine builds. The `experiment` and `notes` columns say which; rows from different experiments
   should not be put in the same chart without reading both.
2. **`F1 = 1.000` is a ground-truth artefact**, not a model result — see
   [gemma4-vs-qwen36-json-kie](../experiments/2026-04-30-gemma4-vs-qwen36-json-kie/#7-limits-of-this-measurement).
3. **Unless stated, `n=1` per performance variant**, and one concurrent workload has a run-to-run
   CV of 8.1 %. Differences of a few percent on a single run are not effects.

## Headline findings

| Finding | Number | Source |
|---|---|---|
| 4-bit quantisation cost on the counterparty gate | **9 % → 20 %** error rate (2.2×) | [invoice-counterparty-role](../experiments/2026-07-16-invoice-counterparty-role/) |
| …while extraction F1 was equivalent | 0.9837 vs 0.9836 | [qwen36-fp8-vs-nvfp4-quality](../experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/) |
| Publisher-recommended kernel vs Marlin on GB10 | **3.3× slower** | [moe-backend-selection-gb10](../experiments/2026-07-23-moe-backend-selection-gb10/) |
| Speculative decoding gain, 4-bit vs FP8 | +48 % vs +27 % single-stream | [mtp-speculative-decoding-gb10](../experiments/2026-07-23-mtp-speculative-decoding-gb10/) |
| A 4× larger model on multi-step analysis | same answers, **5× fewer tool calls** — and worse at extraction | [35b-vs-122b-business-tasks](../experiments/2026-05-22-35b-vs-122b-business-tasks/) |
| Async scheduling off, short-prompt TTFT | **−28 %** | [vllm-prod-config-tuning-gb10](../experiments/2026-08-04-vllm-prod-config-tuning-gb10/) |
| Three months of engine development | ±1 %, neutral | [vllm-prod-config-tuning-gb10](../experiments/2026-08-04-vllm-prod-config-tuning-gb10/) |

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
