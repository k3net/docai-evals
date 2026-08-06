# Decision record — speculative decoding on, draft length 2

**Date:** 2026-07-23 · **Status:** in force · **Experiment:**
[mtp-speculative-decoding-gb10](README.md)

## Decision

Multi-token prediction is enabled on **every** served model, at **`num_speculative_tokens = 2`**.

| Model | Speculative decoding | Draft backend |
|---|---|---|
| 35B FP8 (production) | on, draft 2 | Triton (draft MoE is unquantised) |
| 122B NVFP4 (background) | on, draft 2 | Triton draft, CUTLASS main |

Draft length 3 is rejected: it gains up to +19 % on high-acceptance workloads and loses 9 % on
short chat, netting **−3.6 % aggregate** on our mixed profile.

## Why draft 2 and not per-workload tuning

Because one engine instance serves both extraction and chat. The optimal draft length is a function
of acceptance rate, and our two workloads sit at opposite ends of it — 99.5 % for strict JSON,
58 % for short Hungarian chat. A single value has to serve both, and 2 is the one that never
loses.

The alternative — separate instances with separate draft lengths — is real, and it is the condition
under which this decision reopens. On 128 GB of unified memory it costs more than it currently
returns.

## Operational conditions

1. **Acceptance rate is monitored.** It is the leading indicator: a checkpoint or engine change
   that silently disables the draft path shows up as acceptance collapsing long before anyone
   notices the throughput. Zero acceptance means the draft weights are not loaded, not that the
   method failed.
2. **The draft head is pinned to a backend that can serve unquantised weights.** Its MoE layer is
   BF16 in every checkpoint we run; a bare quantised backend flag prevents the engine from starting
   at all.
3. **Verify the resolved config, not the flag.** A deprecated method name is silently rewritten by
   the engine — we nearly A/B tested two nodes that were running the identical implementation under
   different names.
4. **Do not expect gains on prefill-bound work.** Speculation optimises the decode phase; on
   prefill-saturated workloads it costs throughput. Batch document processing should be evaluated
   separately rather than assumed to inherit these numbers.

## What this measurement changed in how we read checkpoints

The most useful finding was structural rather than numeric: **the 4-bit checkpoints achieve higher
acceptance than the FP8 one because they leave the draft head at full precision, while the FP8
checkpoint quantises it.**

That is a property of how the checkpoints were built, not of the quantisation format — and it is
invisible unless you inspect the tensor precision map. It is now part of our checkpoint intake:
before benchmarking, dump the per-module precision and check what happened to the draft head.

## What would reopen it

- **Separate engine instances for chat and extraction** — then draft 3 for extraction and draft 2
  for chat becomes available, worth roughly +19 % on the extraction path.
- **A production load shift toward batch processing**, which would make the prefill-bound
  regression relevant.
- **An FP8 checkpoint with a BF16 draft head** — by the mechanism above, it should reach the
  acceptance rate the 4-bit models get, for free.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10)*
