# Decision record — keep the baseline serving configuration

**Date:** 2026-07-01 · **Status:** in force, refined 2026-08-04 · **Experiment:**
[qwen36-fp8-vllm-flag-sweep](README.md)

## Decision

No flag from the vendor recipe enters the production configuration. Specifically:

| Flag | Decision | Basis |
|---|---|---|
| `--attention-backend flashinfer` | not adopted | −2.2 % aggregate throughput; the default already selects an equivalent path for this model |
| `--async-scheduling` | not adopted | −2.4 % aggregate throughput |
| `num_speculative_tokens 3` | not adopted | −3.6 % aggregate; gains only where acceptance is already high |
| Speculative decoding itself, draft = 2 | **kept** | measured separately — see [mtp-speculative-decoding-gb10](../2026-07-23-mtp-speculative-decoding-gb10/) |

## Why a published recipe did not transfer

The recipe was written for a different quantisation format on different silicon. Its gains come
from kernel paths that either do not exist on `sm_121a` or are not reachable for a block-scaled
FP8 checkpoint. Copying flags across that boundary is not a shortcut; it is an untested change with
a vendor's name on it.

The draft-length result is the one worth carrying forward as a general lesson: **speculative
decoding tuning is workload tuning**. A single `num_speculative_tokens` value is right only for a
single acceptance regime, and a model that serves both strict-JSON extraction (99.5 % acceptance)
and short chat (58–65 %) does not have one.

## Conditions attached

1. **Do not re-litigate these flags without a version change.** Each rejection is tied to an engine
   build. When the engine changes materially, the async-scheduling arm in particular is worth
   re-running — which is exactly what happened five weeks later.
2. **Any future flag change goes through the same gate:** aggregate throughput measured, boot log
   read for kernel fallbacks, launch command recorded with the result.

## What this decision revealed about the measurement itself

The primary metric was aggregate throughput at concurrency 8. Nobody had checked what production
concurrency actually was.

It is 1–3. Zero percent of the time above 8.

That does not change any rejection here — nothing was positive at any concurrency — but it means
the *decision-relevant* metric for this system is time-to-first-token, not saturated throughput.
The follow-up experiment ([vllm-prod-config-tuning-gb10](../2026-08-04-vllm-prod-config-tuning-gb10/))
re-derived the whole serving profile on that basis, and reversed the async-scheduling
justification from "−2.4 % throughput" to "−5 % TTFT, up to −28 % on short prompts" — same
decision, better reason.

**The lesson we keep:** measure the load before choosing the metric. A benchmark at an operating
point you never reach can reject the right things for the wrong reasons, and eventually it will
accept the wrong ones.

## What would reopen it

- A materially newer engine build (the async result already moved once).
- A change in the production load profile — batch document processing at high concurrency would
  make aggregate throughput primary again, and `v3_spec3` would deserve a rerun on the extraction
  workloads alone.
- Splitting extraction and chat onto separate engine instances, which would allow per-instance
  draft lengths: 3 for extraction, 2 for chat.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Related article (HU): Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning)*
