# FP8 vs NVFP4 — what 4-bit quantisation keeps, and what it costs

**Date:** 2026-07-16 (quality round), performance updated 2026-07-23 · **Type:** extraction and
chat quality, plus throughput · **Reproducibility:** R2 ·
**Article (HU):** [Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk)

> **Read this together with [invoice-counterparty-role](../2026-07-16-invoice-counterparty-role/).**
> This experiment concluded the candidates were quality-equivalent. That conclusion was wrong, and
> the next experiment is why. Both are published, in order, because the sequence is the lesson.

## 1. What was the measurement for?

4-bit NVFP4 weights are roughly 10 GiB smaller than FP8 for this model. On a bandwidth-bound
machine that converts directly into decode speed. The question was whether the capability cost is
acceptable for a production document pipeline.

## 2. On what task and dataset?

- [hu-invoice-kie](../../evals/hu-invoice-kie/) — 25 documents / 34 scored units, deterministic
  replay, identical 6,734-token input for every arm, `temperature = 0`.
- [chat-business-scenarios](../../evals/chat-business-scenarios/) — 16 scenarios with an LLM judge.
- [performance](../../performance/) — single-stream and concurrent workloads.

## 3. Which models and configurations?

| Arm | Checkpoint | Quantisation detail | Weights |
|---|---|---|---|
| `fp8-ref` | Qwen3.6-35B-A3B-FP8 | block-scaled FP8, production model | ~35 GiB |
| `nvfp4-a` | NVFP4, vendor toolkit | ~70 % of weights 4-bit packed, 3.1 GiB left FP8 | 21.8 GiB |
| `nvfp4-b` | NVFP4, community "dynamic" | least aggressive — 9.2 GiB (37 %) left FP8 | 24.7 GiB |
| `nvfp4-c` | NVFP4, community "fast" | most aggressive — 3.5 GiB (32 %) left FP8 | 22.0 GiB |

All arms on the same engine (`v0.24.0` container), same node, vision enabled, speculative decoding
at draft length 2 where measured.

Getting the candidates to load at all required five configuration findings, listed in §7.

## 4. Which metrics?

Raw and normalised field-level F1, JSON validity, chat scenario pass rate, decode throughput,
aggregate throughput at concurrency 8, speculative acceptance.

Normalisation rules were frozen *before* scoring:
[`kie_normalizer v1.0`](../../scripts/kie_normalizer.py).

## 5. What was the result?

### Extraction quality — a 1-point gap that was mostly formatting

| Arm | Raw F1 | **Normalised F1** | Real content errors |
|---|---|---|---|
| `fp8-ref` | 0.9790 | **0.9837** | 2 |
| `nvfp4-b` (least aggressive) | 0.9649 | **0.9836** | 3 |
| `nvfp4-a` | 0.9537 | 0.9676 | 4 |
| `nvfp4-c` (most aggressive) | 0.9488 | 0.9721 | 4 |

JSON validity: **100 % on all four**. Nothing "broke"; the differences are content-level.

Normalised, the least aggressive candidate is within **0.0001 F1** of the production model, with
one extra real error across 34 scored units. On this corpus, that is equivalence.

Raw scores did order themselves by how much of the model was left at 8 bits — which is the
intuitive dose-response story. Hold that thought until §6.

> One notable detail: the single worst content error in the round — a hallucinated partner
> person-name, replacing a real name with an unrelated one — came from the *vendor* checkpoint,
> not from either community quantisation.

### Chat — no separation

| Arm | Pass |
|---|---|
| `fp8-ref` | 7 / 16 |
| `nvfp4-b` | 7 / 16 |
| `nvfp4-a` | 6 / 16 |
| `nvfp4-c` | 9 / 16 |

**7 of the 16 scenarios failed for every candidate**, for reasons that had nothing to do with the
models: the test tenant had no financial data to answer them with, and one scenario expected a
tool that did not exist in the catalogue. On the 9 answerable scenarios the ordering was
`nvfp4-c > nvfp4-b > nvfp4-a` — a 9-item sample, reported as an observation and not as a finding.

### Speed — the candidates win clearly

Clean best-vs-best, same node, same engine, speculative decoding on both sides:

| | FP8 (Triton, its own optimum) | Best NVFP4 (Marlin) | Δ |
|---|---|---|---|
| Single-stream JSON extraction | 68.3 tok/s | **115.7** | **+69 %** |
| Aggregate @ c=8, uniform | 256.1 | **359.4** | **+40 %** |
| Aggregate @ c=8, mixed | 271.2 ⚠️ | 342.3 | +26 % |

⚠️ The mixed mix is unstable (CV 8.1 %, n=3) — treat that column with suspicion.

Decomposing quantisation from speculation, on the same engine:

| | FP8 | NVFP4 |
|---|---|---|
| Single JSON: no-MTP → draft 2 | 53.6 → 68.3 (+27 %) | 78.2 → 115.7 (**+48 %**) |
| Raw quantisation gain, no speculation | — | +46 % single, +18 % aggregate |

Both effects are real and they compound: smaller weights are faster, *and* speculative decoding
pays more when the verify pass is cheaper.

Memory: ~10 GiB freed, available for KV cache or a lower memory-utilisation setting.

## 6. What product decision followed?

At this point: **provisional go, pending a larger validation gate.**

That gate — [invoice-counterparty-role](../2026-07-16-invoice-counterparty-role/) — ran days later
on 100 real customer invoices and **failed**. The candidates roughly doubled the rate of a
business-critical error that this experiment's corpus could not see.

Final decision: **stay on FP8**. See [decision-record.md](decision-record.md).

The intuitive ordering by quantisation aggressiveness also did not survive contact with the larger
corpus: on the counterparty gate the three candidates were **statistically indistinguishable from
each other** while all being worse than FP8. The effect attaches to the format, not to a dose.

## 7. Limits of this measurement

- ⛔ **The corpus was not representative, and that is the whole story.** 25 documents from a
  generic test tenant, heavy on English SaaS invoices, without the tenant's own-company context.
  It could not exercise the capability that actually degraded. A benchmark that cannot see the
  failure will report equivalence, confidently.
- **Small.** 34 scored units; 9 answerable chat scenarios.
- **Chat pass rates are contaminated** by test-corpus gaps (7/16 fail for all arms).
- **`n=1` per performance variant**, and one concurrent mix has CV 8.1 %.
- **Three different quantisation toolchains** are compared as if "NVFP4" were one thing. Their
  bit-level layouts differ substantially — which is exactly why the later result (no
  distinguishable difference between them) was surprising.

### Configuration findings — the part that cost the most time

- The `latest`-style nightly image tag was **stale** and would not load a mixed-precision
  checkpoint; a pinned release was required.
- The 4-bit quantisation flag must name the FP4 scheme explicitly; the generic name silently
  selects an FP8 config and fails later with an unrelated error.
- **The speculative draft layer's MoE is unquantised**, so neither 4-bit MoE backend can load it.
  The speculative config needs `"moe_backend":"triton"` for the draft while the main model stays on
  Marlin — otherwise the engine will not start at all.
- Extraction prompts send an **image** alongside text, so language-model-only serving must stay
  off, or requests fail with HTTP 400.
- Three instances at 0.26 memory utilisation each OOM on 128 GB unified memory; per-service budgets
  are needed for side-by-side comparison.

## 8. The article

[Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk) —
*„egy kvantálási teszt, ami nem arról szólt, amiről indult"*

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
