# Decision record — damp at S = 0.7, canary at t = 0.6, keep the sampler truncating

**Date:** 2026-09-20 · **Status:** proposed (canary pending) ·
**Experiment:** [cjk-damping-dose-response-gb10](README.md)

## Decision

1. The production cron path may return from the `t = 0.3` firefight to `t = 0.6` **only** with
   the damped checkpoint `Qwen3.6-35B-A3B-FP8-cjk-damped-S07`, and only through a small,
   reversible canary with CJK occurrence and task quality monitored. The base checkpoint at
   `t = 0.3` is **not** a safe state: on the actual sampling support it carries 392/M expected
   CJK positions and produced real CJK tokens in answers.
2. Dose S = 0.7, multiplicative form, raw mask. Not S = 0.8 (zero on the production path but
   not verified on the actual support and no cheaper in Chinese), not S = 0.9 (leaks at
   `t = 0.8`), not the direction form, not the refined mask.
3. The sampler must keep `top_k`/`top_p` truncation. The patch's zeros are a property of the
   truncated support; the raw CJK mass is higher than the base's.
4. The Hungarian trap corpus is retained as a **negative control**, not as a cost instrument, for
   any future `lm_head` intervention.

## The rule that produced it (fixed before the F3 data)

Canary is recommended if (1) `E[Han]` of `S07 @ 0.6` on the actual support ≤ that of the current
production state `K0 @ 0.3`; (2) the trap corpus under the production sampler for `S07 @ 0.6` is
not worse than `K0 @ 0.6` within instance noise; (3) no observed CJK token in any answer over
three fresh `S07` instances, 15 seeds and a concurrent batch. Measured: exact 0 vs 392/M;
146/150 vs 146/150 (score 194.5 vs 191.0); zero events. All three hold. Stated exception: on
the retry path (`t = 0.9`, `presence_penalty 1.8`) `S07` is 0.45/M [0.04; 1.17], not exactly
zero — no event observed; that figure is a lower bound (top-k ties under `top_p = 1.0`).

Post-closure self-check (2026-09-20): recounting every record, including those the risk
calculator skips because they never reach a final answer, leaves condition (3) intact — `S07`
generated no CJK token over ~1.09 M distinct positions — and adds two facts for the canary: the
base produced a 6 593-CJK-token runaway on the retry profile, and `S07` ran away on the same seed
without CJK. The patch does not cure degenerate generations on the retry profile (2 of 15 runs);
the loop guard remains necessary.

## What would reopen it

- Any CJK token in a canary answer at `t = 0.6` (a single one reopens the dose question toward
  S = 0.6, which costs 45 % of the Chinese probe).
- A sampler change that removes `top_k`/`top_p`.
- A base-model or engine change: the mask is vocabulary-specific and the instance-mode noise is
  engine-specific; both must be re-measured (`code/kar_futtat.sh`, ~1.5 h per arm).
- A need for CJK output anywhere on the path served by this checkpoint.
