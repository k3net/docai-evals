# Decision record — no tuned kernel config, async scheduling off

**Date:** 2026-04-14 · **Status:** in force · **Experiment:**
[moe-kernel-tuning-gb10](README.md)

## Decisions

| Change | Decision | Basis |
|---|---|---|
| Autotuned MoE kernel configuration | **not adopted** | +0.03 % concurrent, −2.5 % prefill-bound — nothing, and slightly negative where it matters |
| Async scheduling | **off** | recovered a −5 % throughput / +46 % TTFT regression |
| Eager execution | **never** | −38.7 % single-stream decode |
| `max-num-batched-tokens` | back to 16,384 | best TTFT of the series at equal throughput |

Net effect of two days: the production configuration is where it started, plus three findings that
have been in force ever since.

## Why the tuner did not pay

The kernel autotuner optimises one operation — the expert matmul — in isolation, and it does make
that operation faster. A served request spends its time across attention, KV-cache traffic,
scheduling and the rest of the graph; on this hardware the expert matmuls are not the bottleneck,
so the improvement has nothing to propagate into.

**The general rule we keep:** a component benchmark bounds the possible gain; it does not predict
the delivered one. Before spending time on a kernel-level optimisation, measure whether that
component is on the critical path of the workload you actually serve.

## The findings we did not go looking for

1. **A routine engine update was a 5 % regression** — and 46 % worse TTFT. It would have shipped
   unnoticed without a baseline to compare against. Updates are assumed to be improvements; this
   one was not, and the only reason we know is that someone measured before and after.
2. **Async scheduling was the cause**, and turning it off recovered most of it. That decision has
   now survived two independent re-measurements on later engine builds
   ([flag sweep](../2026-07-01-qwen36-fp8-vllm-flag-sweep/),
   [prod config](../2026-08-04-vllm-prod-config-tuning-gb10/)) — the second one showing it costs up
   to 28 % of TTFT on short prompts.
3. **Eager execution costs 39 % of single-stream decode.** Worth knowing *before* someone disables
   CUDA graphs while debugging a production incident.

## Standing practice this produced

- **Benchmark before and after every engine update.** Four tests, under an hour. This experiment is
  the reason it is not optional.
- **Snapshot the environment with the result** — engine config, library versions, image digest.
  Every phase here has its own; without them, none of these comparisons would be defensible months
  later.
- **Record the negative results.** The tuned kernel config still exists in the archive with its
  measurement attached, so the next person who finds the tuner does not spend the same two days.

## What would reopen it

- **A compute-bound serving profile** — large batches, short prompts — where the expert matmuls do
  land on the critical path.
- **A different MoE kernel backend.** This measured the Triton path; the backend question was
  settled separately and differently for 4-bit weights
  ([moe-backend-selection-gb10](../2026-07-23-moe-backend-selection-gb10/)).
- **An engine version that changes MoE dispatch**, which would invalidate the tuned configuration
  anyway.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)*
