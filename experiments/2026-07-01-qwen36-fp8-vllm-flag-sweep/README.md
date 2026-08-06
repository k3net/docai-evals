# Vendor "agent-ready" recipe flags on an FP8 MoE — a sweep that changed nothing

**Date:** 2026-07-01 · **Type:** inference performance · **Reproducibility:** R3 ·
**Related article (HU):** [Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)
— an earlier kernel-tuning round on the same machine, which this experiment continues. No article
covers this measurement itself.

## 1. What was the measurement for?

A hardware vendor publishes an "agent-ready" serving recipe for a model in the same family as our
production model. It differs from our configuration in several flags. The question: do those flags
help *our* model, on *our* hardware, under *our* load — or is the recipe tuned for a setup that is
not ours?

This is the boring kind of experiment that saves the most time. Adopting a published recipe
wholesale is cheap; discovering six months later that one flag costs 3 % throughput is not.

## 2. On what task and dataset?

[performance](../../performance/) workloads — six single-stream (29 to ~159,000 prompt tokens) and
two concurrent mixes at concurrency 8, 60 seconds each. No document corpus involved; this is a
serving measurement.

## 3. Which configurations?

Cumulative ladder from the production baseline. Each variant requires its own engine start, so
each is a cold boot plus a measurement pass — roughly 20 minutes per arm.

| Variant | Added to baseline | Hypothesis |
|---|---|---|
| `v0_baseline` | — (current production) | reference |
| `v1_flashinfer` | `--attention-backend flashinfer` | explicit FlashInfer attention helps |
| `v2_async` | `+ --async-scheduling` | overlapping scheduling with the forward pass raises throughput |
| `v3_spec3` | `num_speculative_tokens 2 → 3` | a longer draft raises accepted tokens per step |

Model: Qwen3.6-35B-A3B-FP8 on DGX Spark GB10 (`sm_121a`).

### Deliberately not tested, and why

- **4-bit weights with a Marlin MoE backend** — the recipe's headline pairing. It belongs to a
  different checkpoint format; the FP8 model stays on the more mature kernel path. This got its
  own measurement later ([qwen36-fp8-vs-nvfp4-quality](../2026-07-16-qwen36-fp8-vs-nvfp4-quality/)).
- **`fastsafetensors` load format** — known to OOM on this platform without GDS during a large
  model load.
- **A different tool-call parser** — a functional change, not a performance one. Our agent's
  streaming path is coupled to the current parser; swapping it blind would break tool-argument
  streaming. It needs a functional test, not a benchmark.

Naming what you *did not* test, and why, is part of the result. A sweep that quietly skips the
inconvenient arm is not a sweep.

## 4. Which metrics?

**Aggregate throughput at concurrency 8** is the primary decision metric. Secondary: single-stream
decode per workload, TTFT, speculative acceptance from the engine metrics endpoint.

**Decision rule, fixed before the run:** adopt a flag only if aggregate throughput improves
materially *and* the boot log is clean of kernel fallback warnings.

## 5. What was the result?

Nothing survived.

| Variant | Aggregate throughput @ c=8 | Single stream | Verdict |
|---|---|---|---|
| `v1_flashinfer` | **−2.2 %** | neutral | rejected |
| `v2_async` | **−2.4 %** | neutral | rejected |
| `v3_spec3` | **−3.6 %** | +8.9 % average | rejected — see below |

### The one interesting arm: draft length 2 → 3

`v3_spec3` is not a flat loss; it is a textbook speculative-decoding trade-off, and the split is
along **baseline acceptance rate**:

| Workload | Single-stream Δ | Acceptance, draft 2 → 3 |
|---|---|---|
| JSON extraction | **+19 %** | 99.5 % → 98.3 % |
| Long-RAG 32k | +17 % | high → high |
| Code | +13 % | high → high |
| Q&A (short chat) | **−9 %** | 64.6 % → **43.8 %** |
| Hungarian (short chat) | −3 % | 58.2 % → **43.2 %** |
| Overall, aggregate @ c=8 | **−3.6 %** | 70.6 % → 61.2 % |

Where the model already predicts its own next tokens well — strict JSON, long-context
continuation — a longer draft is nearly free extra speed. Where it does not, the extra draft token
is discarded work, and at concurrency it competes with real requests for compute.

Our production model serves both chat and extraction, so the mixed profile decides: **draft length
stays at 2**.

## 6. What product decision followed?

Keep the production baseline unchanged. See [decision-record.md](decision-record.md).

The measurement also produced the question that drove the
[next experiment](../2026-08-04-vllm-prod-config-tuning-gb10/): *what is production concurrency
actually?* Every number here is at c=8, and if real traffic never approaches that, the wrong
metric was primary.

## 7. Limits of this measurement

- **n=1 per variant.** Each arm is a ~20-minute cold boot; a full repeat sweep was not run. The
  differences (−2 % to −4 %) are small enough that individually they sit near the noise floor —
  the finding is that *no arm showed a gain*, which is more robust than any single delta.
- **Concurrency 8 was the primary metric, and it was the wrong operating point.** Corrected five
  weeks later: production peaks at 3 concurrent requests. The rejections stand — nothing was
  positive at either concurrency — but the *reasoning* about `v3_spec3` deserved a low-concurrency
  crossover sweep that was not run here.
- **One engine build.** The async-scheduling result was later re-measured on a newer build, where
  it had become the upstream default. The direction held; see
  [vllm-prod-config-tuning-gb10](../2026-08-04-vllm-prod-config-tuning-gb10/).
- **The recipe was written for different hardware and a different quantisation.** This experiment
  says the flags do not transfer to our setup; it says nothing about whether they work in theirs.

## 8. The article

No article covers this round. It continues the thread of
[Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)
— *„avagy hogyan tanultam meg, hogy a pure-kernel benchmark nem egyenlő a serving nyereséggel"* —
which measured MoE kernel tuning and async scheduling on an earlier engine build, and reached the
same conclusion from a different direction: the benchmark gain did not survive contact with real
serving.

The follow-up, which re-derived the whole serving profile from production telemetry, is
[vllm-prod-config-tuning-gb10](../2026-08-04-vllm-prod-config-tuning-gb10/).

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
