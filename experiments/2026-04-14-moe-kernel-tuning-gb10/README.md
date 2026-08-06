# Two days of MoE kernel tuning, and nothing to show for it

**Date:** 2026-04-13/14 · **Type:** inference performance · **Reproducibility:** R2 ·
**Article (HU):** [Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)

## 1. What was the measurement for?

The engine ships a kernel autotuner for mixture-of-experts layers. Run it against your exact model
shape and GPU, and it writes a configuration file with the best tile sizes per batch size. Six
hours of tuning on the GB10 produced one — and the question was what it buys in serving.

The honest answer, measured across nine configurations: **nothing.** Which turned out to be worth
more than a win, because two other things surfaced along the way.

## 2. On what task and dataset?

The same four synthetic workloads used throughout this repository (see
[performance/workloads.md](../../performance/workloads.md)), run through the engine's own
`bench serve` harness:

| Test | Input / output | Concurrency | Prompts |
|---|---|---|---|
| A — single decode | 512 / 512 | 1 | 20 |
| B — prefill-bound | 8,192 / 256 | 4 | 20 |
| C — concurrent contention | 2,048 / 512 | 16 | 64 |
| D — chat profile | mixed | 2 | 20 |

Repeats with different seeds on B and C where variance was suspected. Every phase captured its own
engine config, library versions and image digest.

## 3. Which configurations?

Nine phases, changed cumulatively from the production baseline. Model: Qwen3.5-35B-A3B-FP8,
FlashInfer attention, Triton FP8 MoE backend throughout.

| Phase | What changed |
|---|---|
| `baseline` | production config: 131k context, memory 0.50, batched-tokens 32,768, seqs 32 |
| `image-updated` | newer nightly engine build + memory 0.45 + batched-tokens 65,536, async scheduling **on** |
| `no-async` | async scheduling **off** |
| `no-async-no-mamba` | + state-cache mode change |
| **`tuned`** | **+ the autotuned MoE kernel config** ⭐ |
| `mem055` | + memory utilisation 0.55 |
| `eager` | + eager execution (CUDA graphs off) |
| `final` | eager off again, memory back to 0.45 |
| `prod` | + batched-tokens back to 16,384 |

Because the changes are cumulative, each row is compared to the one above it, not to the baseline.

## 4. Which metrics?

Output throughput per test (primary), median TTFT, TPOT. The kernel tuner's own benchmark reports
per-kernel gains; the point of this experiment is what survives at the serving layer.

## 5. What was the result?

| Phase | A single | B prefill | C conc-16 | C median TTFT |
|---|---|---|---|---|
| `baseline` | 48.92 | **75.88** | **208.04** | 5,013 ms |
| `image-updated` | 49.76 | 70.06 | 197.67 | 7,300 ms |
| `no-async` | 49.01 | 71.73 | 204.39 | 5,838 ms |
| `no-async-no-mamba` | — | 72.08 | — | — |
| **`tuned`** ⭐ | 48.94 | 69.96 *(n=3)* | **204.46** | 6,198 ms |
| `mem055` | 48.67 | 69.54 *(n=2)* | 204.01 | 5,884 ms |
| `eager` | **30.02** | 55.55 | — | — |
| `final` | 49.31 | 73.33 *(n=2)* | 193.24 | 5,205 ms |
| `prod` | 49.15 | 71.35 *(n=2)* | 207.91 *(n=2)* | 4,165 ms |

### The main event: the tuned kernel changed nothing

`no-async` → `tuned` is the isolated effect of six hours of autotuning:

| | Before | After | Δ |
|---|---|---|---|
| Concurrent throughput | 204.39 | 204.46 | **+0.03 %** |
| Single decode | 49.01 | 48.94 | −0.1 % |
| Prefill-bound | 71.73 | 69.96 | −2.5 % |

Zero, within noise, on every test — and slightly negative on the one workload we care most about.

**Why:** the tuner optimises the MoE GEMM in isolation, and a serving workload is not MoE-GEMM
bound. Between attention, the KV cache, scheduling and the rest of the graph, the expert matmuls
are simply not where the time goes on this hardware. A kernel benchmark can be honestly 10 % faster
while the served request is not measurably faster at all.

> **A pure-kernel benchmark is not a serving gain.** That sentence cost two days.

### The finding nobody was looking for: the engine update was a regression

`baseline` → `image-updated`, a routine nightly bump (with two config changes alongside it):

| | Baseline | Updated | Δ |
|---|---|---|---|
| Concurrent throughput | 208.04 | 197.67 | **−5.0 %** |
| Prefill-bound | 75.88 | 70.06 | **−7.7 %** |
| Median TTFT (concurrent) | 5,013 ms | 7,300 ms | **+45.6 %** |

Turning async scheduling **off** recovered most of it (197.67 → 204.39, TTFT 7,300 → 5,838 ms) —
the first evidence for a decision that has held ever since and was re-confirmed on a much later
engine build ([vllm-prod-config-tuning-gb10](../2026-08-04-vllm-prod-config-tuning-gb10/)).

Nobody would have noticed the regression without a baseline to compare against. It arrived as part
of a routine update, in the direction people assume updates never go.

### The cheap experiment that saved a bad idea

`eager` — disabling CUDA graphs, a common troubleshooting step:

| | With graphs | Eager | Δ |
|---|---|---|---|
| Single decode | 48.94 | **30.02** | **−38.7 %** |
| Prefill-bound | 69.96 | 55.55 | −20.6 % |

A 39 % collapse. Worth knowing before someone reaches for it during an incident.

### Where it ended up

The final production config (`prod`) — batched-tokens back to 16,384, async off, no tuned kernel —
lands at 207.91 concurrent, statistically the same as the baseline it started from, with the best
TTFT of the series (4,165 ms). Two days of work to return to where we began, plus three durable
findings.

## 6. What product decision followed?

Keep the autotuned kernel out of production; keep async scheduling off. See
[decision-record.md](decision-record.md).

## 7. Limits of this measurement

- **The phases are cumulative, not factorial.** Each row differs from the previous one, so only
  adjacent comparisons are clean. The `baseline` → `image-updated` step in particular bundles an
  engine update *with* two config changes — the −5 % is the combined effect, not the engine alone.
- **`n=1` on most cells**, `n=2–3` where variance was suspected. The tuning result is the
  best-supported one (three prefill seeds); the 5 % regression is single-run on each side and
  should be read as "a regression of roughly that size", not a precise figure.
- **One model, one GPU, one engine family.** The tuner may well pay on a compute-bound deployment
  or a different architecture. Our claim is narrow: on this hardware, with this serving profile, it
  did not.
- **Concurrency-16 is a stress test**, not our operating point (production peaks at 3).
- **Synthetic fixed-length workloads**, not real documents.

## 8. The article

[Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning) —
*„avagy hogyan tanultam meg, hogy a pure-kernel benchmark nem egyenlő a serving nyereséggel"*

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
