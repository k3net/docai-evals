# Decision record — Flash-Next NVFP4 on vLLM: not until the top-k is deterministic

**Date:** 2026-08-28 · **Status:** in force (validated on all three suites, 21:20) ·
**Experiment:** [README](README.md)

## Decision

1. **The Flash-Next NVFP4 / vLLM recipe with the stock `persistent_topk` is not used for extraction.**
   13/50 items change between identical greedy requests, 5 of them in the extracted value; the
   majority of three runs picked the wrong answer on one item. A KIE engine that returns a different
   amount on re-run is not a KIE engine, whatever its score.
2. **The fix is the mode-3 top-k** (`VLLM_QSA_EXACT_TOPK=3`: `torch.topk` + canonical tie ordering) —
   0/50 unstable on the main suite (98/100, the reachable maximum), 100/100 on the 217 k-token suite, 6/6 probe
   items byte-identical over 10 repetitions, MTP and CUDA graphs unchanged, decode 25 tok/s, prefill at 74 %.
   **MTP=2 stays on**: it is not greedy-equivalent on this model (9/50 items take a different path) but the
   quality effect is noise-level and non-directional, and switching it off costs 40 % of decode without removing
   the repetition loop (which moves to a different input).
3. **Production stays on the 35B FP8** (0/50 unstable, 294/300 on the same suite, already deployed)
   until the fix has passed the full 65-item suite and the Hungarian language challenge.
4. The 122B replacement question is not decided by this experiment; the four-way comparison rests
   on four discriminating items.

## What the validation added (2026-08-28, 16:10 → 21:20)

Main suite with mode 3: **98/100, 0/50 unstable, 0 truncated** — the reachable maximum, one point above the stock
kernel. Hard suite: **90/100** because one item (T14-01) now falls into a **deterministic repetition loop** in its
reasoning on every run. That loop is not caused by the top-k kernel; the kernel's noise used to break it by accident.
Decision 2 stands (the fix is the right fix); decision 3 gains a condition: **a reasoning-loop guard** (repetition
ratio on the reasoning stream, retry with temperature > 0 or a presence penalty) has to be part of the serving
profile before the recipe is a candidate. A guard is possible precisely because the failure is now deterministic. The MTP-off post-test showed the loop is
not a speculation artefact: without MTP it disappears on T14-01 and appears on language-challenge item 7 instead.

## Why the majority vote is not a mitigation

The harness scores the majority of three runs. In production there is one request. Scoring each
run separately turned "13 unstable items" into "5 items where the value changes" — and on T3-05 the
majority (`[1, 1, 2]`) was the wrong answer. Voting on a non-deterministic engine can *lock in* the
error; it does not average it out.

## Operational conditions

- **Every new serving recipe gets the prefill probe before any quality number is quoted**:
  identical prompt, `max_tokens = 1`, `top_logprobs = 20`, 10 repetitions, on at least 6 items.
  Ten identical top-20 vectors or the recipe is not measured further. This is cheaper than any
  suite and would have found this in two minutes.
- `CTX` must be ≥ longest prompt + `max_tokens` for the measurement phase (the 77/100 artefact).
- Store the reasoning content, not only the answer; the divergence was invisible without it.
- The determinism patch is a one-file overlay on a third-party image; it must be re-applied and
  re-probed on every image update.

## What would reopen it

- The full-suite validation with mode 3 finishing at ≥ the 297/300 measured with the stock kernel
  **and** zero unstable items **and** no empty 16 k-token run-aways → the recipe becomes a candidate
  for the night-time slot.
- An upstream deterministic `persistent_topk` (index-ordered tie-break, as FlashInfer did for its
  sparse-attention top-k in [flashinfer#2661](https://github.com/flashinfer-ai/flashinfer/pull/2661))
  → the 26 % prefill cost disappears.
- A resolution of [vllm#51782](https://github.com/vllm-project/vllm/issues/51782) that also
  addresses ordering.
- Evidence that the GB10 code-path selection (`persistent_topk` on capability family 12x) changes.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu)*
