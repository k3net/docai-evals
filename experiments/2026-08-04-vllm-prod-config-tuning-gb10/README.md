# Six proposed measurements, two worth running — production serving config on GB10

**Date:** 2026-08-04 · **Type:** inference performance · **Reproducibility:** R3 ·
**Related article (HU):** [Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)
— the earlier kernel-tuning round whose async-scheduling finding this experiment re-measured on a
newer engine build. No article covers this measurement itself.

## 1. What was the measurement for?

Two nodes running the same model had drifted apart: one had been up for months on an older
configuration, the other picked up a newer one on every restart. The next unplanned restart —
a power cut would do — would have silently changed the production serving profile.

The immediate task was to pick one profile. The larger question was which of the six differing
parameters actually *matter*, because the honest answer to most of them turned out to be
"neither, and here is the evidence".

## 2. On what task and dataset?

[performance](../../performance/) workloads plus 30 days of production telemetry. The telemetry is
what makes this experiment different from the [earlier flag sweep](../2026-07-01-qwen36-fp8-vllm-flag-sweep/):
we measured the load before choosing the metric.

| Production, 30 days | Value |
|---|---|
| Concurrent running requests, max | **3** |
| p99 / p50 running | 1 / 0 |
| Time above 8 concurrent requests | **0.000 %** |
| Prompt tokens p95 / p99 | 19,359 / 37,036 |
| TTFT p50 / p95 | 0.99 s / 4.95 s |
| Prefix-cache hit rate | 1.6 % |

An interactive, long-prompt, near-serial profile. **TTFT is the user-facing metric**; saturated
throughput is not.

## 3. Which configurations?

The two drifted profiles differed in six parameters. Before running anything, we tried to
eliminate arms with evidence rather than GPU time:

| Parameter | Resolution | Basis |
|---|---|---|
| Speculative method name | **Not measurable** — both names resolve to the same implementation | Engine log shows the deprecation rewrite |
| `max-num-seqs` 8 vs 32 | **Irrelevant** at this load | 0.000 % of time above 8 concurrent |
| `gpu-memory-utilization` 0.45 vs 0.5 | **Capacity decision, not speed** | KV pool 323k vs 504k tokens, read deterministically from the boot log; demand is ~111k |
| `max-model-len` 131k vs 262k | **Functional, not performance** | A 131k ceiling rejects longer requests outright |
| `max-num-batched-tokens` 8192 vs 16384 | ⭐ **Measure** | Chunk size directly drives TTFT on long prompts |
| `--async-scheduling` | ⭐ **Re-measure** | Prior result was on an older build where it was not the default |

Six proposed measurements became two, and about 40 minutes of GPU time.

## 4. Which metrics?

TTFT per workload (primary), single-stream decode, aggregate throughput at c=4, acceptance rate.

**Decision rule, fixed before the runs:** if the TTFT gain is under 5 %, keep the current value;
adopt only at ≥10 % on p95.

## 5. What was the result?

### Prefill chunk size: no effect, slightly negative

| Metric | 8192 | 16384 | Δ |
|---|---|---|---|
| Single-stream decode | 62.16 tok/s | 62.07 | −0.1 % |
| Extraction decode | 71.60 | 71.35 | −0.3 % |
| Average TTFT | **0.803 s** | 0.812 | +1.1 % (worse) |
| Aggregate @ c=4 | **149.51** | 145.50 | −2.7 % |
| Acceptance | 72.3 % | 72.0 % | — |

TTFT by workload — the larger chunk loses on all six:

| Workload | Prompt tokens | 8192 | 16384 |
|---|---|---|---|
| Q&A | 29 | 0.120 s | 0.122 s |
| Extraction JSON | 298 | 0.189 s | 0.191 s |
| Hungarian | 41 | 0.136 s | 0.136 s |
| Long-RAG | 10,667 | 0.527 s | 0.536 s |
| Long-RAG 32k (≈ production p99) | 39,908 | **1.121 s** | 1.150 s |
| Long-RAG 128k | 158,924 | **2.728 s** | 2.736 s |

The intuition — bigger chunks mean fewer prefill passes means lower TTFT — does not hold here. At
8192 the prefill already saturates this GPU; a larger chunk only takes scheduling slots away from
decode. **Keep 8192.**

### Async scheduling: off is better, and by more than the old measurement suggested

| Metric | Async on | Async off | Δ |
|---|---|---|---|
| **Average TTFT** | 0.803 s | **0.763 s** | **−5.0 %** |
| Aggregate @ c=4 | 149.51 | 149.66 | +0.1 % |
| Single-stream decode | 62.16 | 61.25 | −1.5 % |
| Extraction decode | 71.60 | 70.62 | −1.4 % |
| Acceptance | 72.3 % | 72.7 % | +0.4 pp |

TTFT by workload — **same direction on all six**, and largest where it is most visible:

| Workload | On | Off | Δ |
|---|---|---|---|
| Q&A | 0.120 s | 0.086 s | **−28 %** |
| Hungarian | 0.136 s | 0.099 s | **−27 %** |
| Extraction JSON | 0.189 s | 0.155 s | **−18 %** |
| Long-RAG 10.7k | 0.527 s | 0.491 s | −6.8 % |
| Long-RAG 32k | 1.121 s | 1.080 s | −3.7 % |
| Long-RAG 128k | 2.728 s | 2.667 s | −2.2 % |

Async scheduling overlaps scheduling with the forward pass — a win on a saturated GPU, a loss on
ours, where it delays the first token of a mostly-idle request by up to 28 % on short prompts. The
1–4 % decode cost is smaller in weight, and concurrent throughput is unchanged.

Consistent with the [earlier round](../2026-07-01-qwen36-fp8-vllm-flag-sweep/), which measured
−2.4 % aggregate throughput on an older build. **Same conclusion, better reason, and now an
explicit flag** — because in newer builds this became the upstream default, so silence means "on".

### Capacity, decided rather than measured

Boot log, at the chosen profile:

| Profile | Max length | GPU util | KV cache | Max concurrency at full context |
|---|---|---|---|---|
| Old node A | 131,072 | 0.45 | 323,456 | 2.47× |
| Old node B | 262,144 | 0.5 | 504,336 | 6.99× |
| **Chosen** | **245,760+** | **0.5** | **491,568** | **7.24×** |

Against a measured peak demand of 3 concurrent requests at ~37k tokens (~111k tokens), that is
ample. Cold boot: 8.5 minutes, torch.compile and CUDA-graph capture included.

A concrete consequence: the 128k-token workload — a real 158,924-token request — completes in
2.73 s TTFT on the new profile and **would have been rejected outright** by the old 131,072 ceiling.

### Bonus: what a container rebuild would cost

The production image had been pinned to a base from months earlier. We pulled that exact base
digest onto the test node, rebuilt it identically, and benchmarked old against new:

| Metric | Old build (= production) | New build | Δ |
|---|---|---|---|
| Single-stream decode | 60.86 tok/s | 61.25 | +0.6 % |
| Extraction decode | 69.92 | 70.62 | +1.0 % |
| Average TTFT | 0.764 s | 0.763 s | −0.1 % |
| Aggregate @ c=4 | 148.65 | 149.66 | +0.7 % |
| Acceptance | 72.5 % | 72.7 % | +0.2 pp |

**Three months of engine development is performance-neutral on this model and this hardware** —
everything within ±1 %, marginally in favour of the newer build. Useful in both directions: no
upgrade urgency, and no upgrade risk.

The real risk was never performance. It was that the base image tag **moves**, so "when did you
last build" silently decides what runs in production. Two builds of the same tag on two machines
were different engine versions. The fix is to pin the base by digest.

## 6. What product decision followed?

One unified serving profile, written into version control, applied by a planned restart. See
[decision-record.md](decision-record.md).

## 7. Limits of this measurement

- **`n=1` per variant.** The TTFT direction agrees on 6 of 6 workloads, which is the reason we
  trust it; the 1–4 % decode differences are within noise and are not load-bearing.
- **One node, one model.** Conclusions are specific to this checkpoint on GB10.
- **Telemetry is 30 days of one production tenant.** A different customer mix would move the
  concurrency and prompt-length distributions, and several "irrelevant" verdicts above are
  conditional on them.
- **The eliminated parameters were eliminated on evidence, not measured.** If the load profile
  changes, `max-num-seqs` and memory utilisation come back into play.
- **The chunk-size result may be specific to this GPU's prefill saturation point.** On hardware
  where 8192 does not saturate prefill, the larger chunk plausibly wins.

## 8. The article

No article covers this round yet. Its ancestor is
[Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning),
which investigated async scheduling on an earlier engine build; here it was re-measured after the
setting became the upstream default, and the conclusion held — with a better reason attached.

The speculative-decoding side of this configuration is
[A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10), which
benchmarked the *previous* production profile — see the note in
[decision-record.md](decision-record.md).

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
