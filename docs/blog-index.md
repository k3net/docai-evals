# Articles and their measurements

The write-ups on [docai.hu/blog](https://docai.hu/blog) are the narrative version of the
experiments in this repository. This page maps one to the other in both directions.

The articles are in Hungarian; the experiment documentation is in English.

| Article (HU) | What it argues | Experiments behind it |
|---|---|---|
| [Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk) | 4-bit weights are genuinely faster and genuinely worse at the one thing we could not afford to lose | [qwen36-fp8-vs-nvfp4-quality](../experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/) · [invoice-counterparty-role](../experiments/2026-07-16-invoice-counterparty-role/) |
| [Kövesd a gyártói doksit, és háromszor lassabb leszel](https://docai.hu/blog/backend-valasztas-gb10) | Two vendors, one machine, opposite advice — and the recommended kernel is 3.3× slower | [moe-backend-selection-gb10](../experiments/2026-07-23-moe-backend-selection-gb10/) |
| [Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36) | A model comparison that turned into a speculative-decoding finding: strict JSON drafts at ~99 % acceptance, which the global average hides | [gemma4-vs-qwen36-json-kie](../experiments/2026-04-30-gemma4-vs-qwen36-json-kie/) · [mtp-speculative-decoding-gb10](../experiments/2026-07-23-mtp-speculative-decoding-gb10/) |
| [122B-os modell egy DGX Sparkon: élesben mérve](https://docai.hu/blog/qwen35-122b-spark) | How far a 122B MoE gets on 128 GB — where it holds, and where it breaks | [qwen35-122b-nvfp4-bringup-gb10](../experiments/2026-05-22-qwen35-122b-nvfp4-bringup-gb10/) |
| [Mikor érdemes nagyobb AI-modellt használni — és mikor nem?](https://docai.hu/blog/122b-vs-35b-mikor-jobb-a-nagyobb-modell) | The four-times-larger model lost on the core task and won on multi-step analysis — so it got routed, not adopted | [35b-vs-122b-business-tasks](../experiments/2026-05-22-35b-vs-122b-business-tasks/) |
| [A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10) | Multi-token prediction measured four ways — it wins where nobody expected and loses where everyone did | [qwen36-mtp-ab-gb10](../experiments/2026-04-18-qwen36-mtp-ab-gb10/) · synthesis: [mtp-speculative-decoding-gb10](../experiments/2026-07-23-mtp-speculative-decoding-gb10/) |
| [Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning) | A pure-kernel benchmark is not a serving gain — and a routine engine update was a 5 % regression | [moe-kernel-tuning-gb10](../experiments/2026-04-14-moe-kernel-tuning-gb10/) |
| [Versel nekünk az AI — de tud-e Arany Jánosul?](https://docai.hu/blog/versel-nekunk-az-ai) | Fine-tuning lost to a deterministic best-of-8 selector on every form metric — and was the only thing that moved the voice, by 36 points | [lora-vs-reranker-hu-verse](../experiments/2026-08-14-lora-vs-reranker-hu-verse/) |

## Two experiments without an article yet

- [qwen36-fp8-vllm-flag-sweep](../experiments/2026-07-01-qwen36-fp8-vllm-flag-sweep/) — a vendor
  "agent-ready" recipe that improved nothing on our hardware.
- [vllm-prod-config-tuning-gb10](../experiments/2026-08-04-vllm-prod-config-tuning-gb10/) — six
  proposed measurements, four resolved without touching a GPU, and a serving profile that had
  silently drifted between two machines.

Both continue the thread of the kernel-tuning article: measure the load before you choose the
metric, and a benchmark number is not a serving gain. Both also re-confirmed its async-scheduling
finding on later engine builds — three independent measurements, same conclusion.

## Division of labour

**The blog** carries the story: why the question came up, what we expected, what surprised us, and
what it means for someone running a document-processing system. It is written to be read.

**This repository** carries the evidence: configurations, launch flags, engine versions, scoring
code, sample sizes, significance tests, and the limits of each measurement. It is written to be
checked.

**Decision records** — one per experiment — carry the third thing: what we actually did as a
result, who it binds, and what evidence would reopen the question. A benchmark without a decision
attached tends to get re-argued every quarter.

## If you only read one

- Interested in **document AI quality**: start with
  [invoice-counterparty-role](../experiments/2026-07-16-invoice-counterparty-role/) — the clearest
  case in this repository of an aggregate metric hiding the error that matters.
- Interested in **inference on DGX Spark**: start with
  [moe-backend-selection-gb10](../experiments/2026-07-23-moe-backend-selection-gb10/) — a 3.3×
  difference from a single flag, in the opposite direction to the published recommendation.
- Interested in **model selection**: start with
  [35b-vs-122b-business-tasks](../experiments/2026-05-22-35b-vs-122b-business-tasks/) — where a
  bigger model helps, where it hurts, and how to tell the two apart before committing.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
