# Decision record — speculative decoding on for the production model

**Date:** 2026-04-18 · **Status:** in force · **Experiment:**
[qwen36-mtp-ab-gb10](README.md)

## Decision

Multi-token prediction is enabled on the production model at `num_speculative_tokens = 2`.

The trade accepted, explicitly: **+8.7 % single-stream, +5.0 % on the chat profile, −7.2 % on
prefill-bound extraction.** Extraction runs as background queue work where a 7 % throughput loss is
invisible; chat is the interactive path where the gain is felt.

## What made this decision easy — and what almost made it wrong

The number that looked most impressive was the concurrency-16 result: +24.2 % throughput,
TTFT more than halved. It is also the number that should have carried the least weight, because
our production load peaks at **3** concurrent requests.

Had the decision rested on it, we would have been optimising for a load we never see. It happened
to point the same way as the single-stream and chat results, so the conclusion survived — but the
practice that came out of this round is the one that matters:

> **Decide from the workload you actually run, not from the one that produces the biggest
> percentage.**

That principle got applied properly three months later, when the production serving profile was
re-derived from 30 days of telemetry rather than from benchmark defaults
([vllm-prod-config-tuning-gb10](../2026-08-04-vllm-prod-config-tuning-gb10/)).

## Conditions attached

1. **Monitor acceptance in production.** 72.5 % overall here; a drop signals that a checkpoint or
   engine change disabled the draft path. Zero means the draft weights are not loaded at all, not
   that the feature stopped helping.
2. **Watch the position split, not just the average.** 81.6 % at the first draft position, 63.5 %
   at the second. That gradient is what determines whether a longer draft could ever pay — and here
   it says no, which a later sweep confirmed
   ([qwen36-fp8-vllm-flag-sweep](../2026-07-01-qwen36-fp8-vllm-flag-sweep/): draft 3 costs 3.6 %
   aggregate).
3. **Batch extraction is the workload to re-check** if document volume grows enough that a 7 %
   prefill-bound throughput loss becomes a queue-length problem. The fix would be a separate engine
   instance for extraction rather than turning the feature off.

## What would reopen it

- **A shift toward batch document processing** — the prefill-bound penalty is the only measured
  cost, and it would grow in weight.
- **Separate engine instances for chat and extraction**, which would allow per-instance draft
  lengths: 3 for extraction (high acceptance), 2 for chat.
- **A materially newer engine build**, since speculative-decoding scheduling behaviour has moved
  before.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10)*
