# Decision record — one serving profile, pinned and explicit

**Date:** 2026-08-04 · **Status:** in force · **Experiment:**
[vllm-prod-config-tuning-gb10](README.md)

## Decision

A single serving profile for both nodes, written into version control:

```text
--max-model-len 262144            # was 131072 on one node
--max-num-batched-tokens 8192     # was 16384 on one node — measured: the larger chunk gains nothing
--gpu-memory-utilization 0.5      # was 0.45 on one node
--max-num-seqs 8                  # was 32 on one node — production peak is 3
--no-async-scheduling             # NEW, EXPLICIT — measured: TTFT -5% overall, -28% on short prompts
--speculative-config '{"method":"mtp","num_speculative_tokens":2}'
```

Applied by a **planned restart during a maintenance window**, not left to the next unplanned one.

## Why one profile and not two

Both nodes do the same work during the day. Two profiles means two performance characteristics,
two sets of measurements, and a standing risk that the wrong one is running. The measurements gave
no reason to differentiate — every parameter that differed turned out to be either irrelevant at
this load or better at the same value on both.

## The three rules this experiment produced

### 1. A running configuration that is not in version control is not a configuration

One node had been up for months on settings that no longer existed in the repository. It was not
misconfigured — it was *unknowingly* configured, and the drift only became visible because someone
compared a boot log against a file. A restart for any reason would have changed the production
serving profile with no change record and nobody watching.

### 2. Set defaults explicitly, in both directions

Async scheduling became the upstream default between engine versions. Our older node had it off
via an explicit flag; the newer one had it on *by silence*. Same repository, opposite behaviour,
no diff.

If a parameter matters, name it — including when you agree with the current default. Otherwise the
engine version decides, and it decides at restart time, on whichever machine restarts first.

### 3. Pin base images by digest

The base image tag moves. Two machines built from the same tag months apart ran different engine
versions, and a `prune` on either would have silently pulled a third. Since the rebuild
measurement showed the version difference is worth ±1 % in performance, there is no reason to let
an unpinned tag make that choice unobserved.

## Measurement discipline this reinforced

**Measure the load before choosing the metric.** Of six proposed measurements, four were resolved
without touching a GPU: one by reading an engine log (two flag names, one implementation), two by
reading production telemetry (concurrency never exceeds 3), one by reading a boot log (KV capacity
is deterministic). Total GPU time for the remaining two: about 40 minutes.

The corollary applies to the [earlier flag sweep](../2026-07-01-qwen36-fp8-vllm-flag-sweep/), which
used aggregate throughput at concurrency 8 as its primary metric — an operating point our system
reaches 0.000 % of the time. Its rejections stand, but the async-scheduling justification was
upgraded here from "−2.4 % throughput" to "−5 % TTFT, −28 % on short prompts": same decision, and
now for a reason that describes what users experience.

## Attached note on published numbers

One of our articles benchmarked the *previous* production configuration. With this change, those
figures no longer describe the running system. The article stays accurate about what it measured —
its configuration is stated in full — but the article's high-concurrency scenario was always a
stress test rather than an operating profile, and the record says so.

## What would reopen it

- A production load shift toward batch processing at high concurrency, which would revive
  `max-num-seqs`, memory utilisation and possibly the larger prefill chunk.
- A materially newer engine build — the async-scheduling default has already moved once.
- Longer context requirements: the profile carries roughly 7× headroom at full context, but that is
  a ceiling, not a guarantee.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Related article (HU): Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)*
