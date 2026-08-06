# Speculative decoding on GB10 — the cheapest real speed-up we found

**Date:** 2026-07-23 (consolidating measurements from 2026-05 to 2026-08) · **Type:** inference
performance · **Reproducibility:** R3 ·
**Article (HU):** [A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10)

## 1. What was the measurement for?

Multi-token prediction (MTP) lets a small draft head propose *k* tokens that the main model
verifies in a single forward pass. On paper it is free speed when the draft is right and wasted
compute when it is wrong.

We wanted three things settled on our hardware: whether it pays at all, what draft length to use,
and how it interacts with weight quantisation — because on a bandwidth-bound machine, a cheaper
verify pass should make speculation *more* attractive, not less.

## 2. On what task and dataset?

[performance](../../performance/) workloads — six single-stream (29 to ~159,000 prompt tokens) plus
concurrent mixes. Measurements come from three separate rounds on DGX Spark GB10 (`sm_121a`), each
with speculative decoding as the only variable within its round.

## 3. Which configurations?

| Round | Model | Comparison |
|---|---|---|
| A | Qwen3.6-35B-A3B-FP8 | draft 2 vs off, and draft 2 vs 3 |
| B | Qwen3.6-35B-A3B NVFP4 | draft 2 vs off, on Marlin |
| C | Qwen3.5-122B-A10B-NVFP4 | draft 2 vs off |

Draft head configuration is not optional plumbing — see §7. Its MoE layer is unquantised, so it
must be pinned to a backend that can serve unquantised weights while the main model runs on
Marlin.

## 4. Which metrics?

Single-stream decode tok/s per workload, aggregate throughput at concurrency, TTFT, and
**acceptance rate** read from the engine's metrics endpoint. Acceptance is reported alongside every
throughput figure — without it a speculative-decoding number cannot be interpreted.

## 5. What was the result?

### It pays on every configuration measured

| Model | Workload | Off | Draft 2 | Δ |
|---|---|---|---|---|
| FP8 35B | single-stream JSON extraction | 53.6 | 68.3 | **+27 %** |
| FP8 35B | aggregate @ c=8 | 235.2 | 256.1 | +9 % |
| NVFP4 35B | single-stream JSON extraction | 78.2 | 115.7 | **+48 %** |
| NVFP4 35B | aggregate @ c=8 | 277.5 | 359.4 | **+30 %** |
| NVFP4 122B | average across four workloads | — | — | **+55 %** |

### It pays *more* at 4 bits — and the mechanism is visible

The gain is nearly twice as large on the 4-bit model (+48 % vs +27 % single-stream). This is what a
bandwidth-bound machine predicts: the verify pass reads the main model's weights, so a smaller
model makes each speculative step cheaper while the draft head's cost stays flat.

Acceptance rates back it up — and the *why* is in the checkpoints:

| Model | Acceptance | Draft head precision |
|---|---|---|
| FP8 35B | ~71 % | **FP8** — the checkpoint quantises the draft experts (775 tensors, 797 MiB) |
| NVFP4 35B | 73–75 % | **BF16** — all three 4-bit checkpoints leave the draft head unquantised |

A full-precision draft predicts better, so more of its proposals survive verification. The
counter-intuitive result — the *more* aggressively quantised model achieving *higher* acceptance —
comes from an asymmetry in how the checkpoints were built, not from the main model's precision.

### Acceptance is workload-dependent, and that decides the draft length

122B, per workload:

| Workload | Decode gain | Acceptance |
|---|---|---|
| JSON extraction | +78 % | **100 %** |
| Long-RAG 8k | +61 % | 82.5 % |
| Q&A | +46 % | 71.2 % |
| Hungarian short chat | +34 % | 60.8 % |

Strict JSON is nearly perfectly predictable — schema keys, quotes, delimiters — so almost every
drafted token is accepted. Free-form Hungarian chat is not.

This is exactly why raising the draft length from 2 to 3 does not help a mixed workload
([flag sweep](../2026-07-01-qwen36-fp8-vllm-flag-sweep/)):

| Workload | Δ, draft 2 → 3 | Acceptance, draft 2 → 3 |
|---|---|---|
| JSON extraction | **+19 %** | 99.5 % → 98.3 % |
| Long-RAG 32k | +17 % | high → high |
| Q&A | **−9 %** | 64.6 % → **43.8 %** |
| Hungarian chat | −3 % | 58.2 % → **43.2 %** |
| Aggregate @ c=8 | **−3.6 %** | 70.6 % → 61.2 % |

Where acceptance is already near-perfect, a longer draft is nearly free. Where it is marginal, the
third token is usually discarded and — under concurrency — it competes with real requests.

### TTFT is the price

Speculative decoding adds a draft forward pass before the first token. On the 122B this cost +31 %
to +156 % TTFT depending on workload. For a background model that is irrelevant; for an interactive
one it is the metric that matters most, and it is why the trade has to be evaluated per use case
rather than as a global switch.

### On the production model, at production settings

The original A/B on the production model is its own experiment —
[qwen36-mtp-ab-gb10](../2026-04-18-qwen36-mtp-ab-gb10/) (R2, raw artefacts recovered and
aggregated). Its four scenarios:

| Scenario | Result |
|---|---|
| A — single decode | +8.7 % |
| D — chat profile | +5.0 % |
| C — 16 concurrent | **+24.2 % tok/s, −56.7 % TTFT** |
| B — prefill-bound | **−7.2 % tok/s, +30.7 % TPOT** |
| Acceptance | 72.53 % overall — 81.57 % at draft position 0, 63.48 % at position 1 |

The prefill-bound row is the honest one: when the GPU is already saturated by prefill work, the
draft pass takes compute from it and speculation loses. Speculative decoding is a **decode-phase**
optimisation.

## 6. What product decision followed?

**Speculative decoding on, draft length 2, on every model.** See
[decision-record.md](decision-record.md).

## 7. Limits of this measurement

- **Rounds are not directly comparable.** Different models, engine builds and dates. Each Δ is
  valid within its round; the cross-round comparison (+48 % vs +27 %) is a like-for-like within a
  single round and is the one we lean on.
- **`n=1` per variant** in rounds A and B; n=3 for the 122B workloads.
- **The production-model numbers in §5 come from a separate experiment**
  ([qwen36-mtp-ab-gb10](../2026-04-18-qwen36-mtp-ab-gb10/)) with its own limitations — n=1 on the
  single-decode test, n=2 elsewhere.
- **Acceptance is an average.** Position-wise acceptance (81.57 % at draft position 0, 63.48 % at
  position 1, 72.53 % overall) shows the spread that a single number hides — and that gradient is
  what rules out a longer draft.
- **The 16-concurrent scenario is a stress test**, not our operating point — production peaks at 3
  concurrent requests. The interactive case is carried by the single-stream and TTFT rows.

### Configuration findings — where the time actually went

- **A missing draft head reads as 0 % acceptance, not as an error.** One published 122B checkpoint
  simply did not ship draft weights; a different build of the same model did, and acceptance went
  from 0 % to 74 %. If you see zero, check the weights before concluding anything about the method.
- **The draft layer's MoE is unquantised.** Neither Marlin nor the FlashInfer path can load it, so
  the engine refuses to start with a bare quantised backend flag. Pin the draft to Triton in the
  speculative config while the main model stays on Marlin.
- **A deprecated method alias is silently rewritten.** Two of our nodes appeared to run different
  speculative methods; the engine log showed both resolving to the same implementation. What looked
  like a configuration difference worth A/B testing was a naming difference — always confirm from
  the engine's own resolved config, not from the flag you passed.
- **Acceptance belongs on a dashboard.** It is the early-warning signal that a checkpoint or engine
  change has silently disabled the draft path; throughput alone degrades too gently to notice.

## 8. The articles

- [A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10) — the
  four-scenario production round, *„avagy hogyan lett a »sima A/B benchmark« a mai legmeglepőbb
  eredménye"*
- [Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36) — where the
  workload-dependence of acceptance first surfaced: strict JSON drafts at ~99 %, and why a global
  average of 72.5 % hides it

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
