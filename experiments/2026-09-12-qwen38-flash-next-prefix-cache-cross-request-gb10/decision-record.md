# Decision record — round 3: prefix caching stays on, the deterministic kernel moves to "adopt", vllm#56500 is dropped

**Date:** 2026-09-12 · **Status:** in force · **Experiment:** [README](README.md)

## Decision

1. **Prefix caching stays on in the night slot.** The measured effect lives in the logits; the
   visible answer did not move in any of the arms here. Turning it off would remove the effect but
   costs an order of magnitude in TTFT on repeated long prefixes (~14 s vs ~1.4 s on a 20k-token
   prefix, recipe README), which is the dominant pattern in our traffic. The existing safeguards stay
   as they are: three runs with an agreement check for extraction, a separate verification step for
   chat.
2. **The determinism claim is narrowed again.** Round 2 narrowed it to *sequential requests in the
   same prefix-cache state*. It now reads: *sequential requests whose shared prefix blocks were
   written by a request of the same shape*. Concretely, a second question asked on a document another
   request already cached can get different logits than the same question asked on a cold engine.
   Any regression test, A/B or cached-answer scheme resting on bit-identity remains invalid.
3. **The deterministic `persistent_topk` kernel (vllm#55122) moves from "candidate" to "adopt once
   the quality suite is re-run".** Measured here on the official v0.29.0 image: **21–28 % faster
   prefill** than the exact-`torch.topk` workaround we run in production, across six context lengths,
   at identical determinism (the same 3/4 probe result, the same failing item). The remaining
   condition is unchanged from round 2 and is *not* satisfied by this round: the 50-item suite (plus
   the hard suite and the language challenge) must be re-run with the kernel, because the two exact
   selections produce different text. Vendoring rules also stand: Dockerfile step, pinned source
   commit, `.so` built into the image, fail-closed `QSADET active` check in the deploy verification.
4. **vllm#56500 is not adopted and not back-ported.** Its main hunk targets a file that exists on
   neither shippable base (preview build, `v0.29.0`), and the symptom it fixes — reserved memory
   growing in steps with context length — does not reproduce on this recipe: 8K→64K cold prefills
   stay on a flat plateau with no preemption. A hand-rewritten back-port would be an undocumented
   divergence for no measured gain.
5. **Upstream we report, we do not claim.** A reproduction comment on vllm#54076 (referencing
   #53798) with both stacks' numbers and the explicit statement that the recipe's equivalent of both
   fixes was already active; an independent throughput data point on vllm#55122; a negative +
   packaging note on vllm#56500. None of them asserts a root cause we have not isolated.

## What this round corrected in round 2

- Round 2 wrote that "a partial prefix-cache hit is not a full one" and treated the **partial** hit as
  the faulty path. It is the other way round: the partial-hit run reproduces the cache-free result bit
  for bit, and the **full** hits on blocks written by a differently sized request are the ones that
  diverge.
- Round 2 listed vllm#53798 / #54076 as the likely fix. The recipe's two-line equivalent of both was
  already in the image being measured, so the effect observed is a **remainder** beyond the
  all-zero-state bug, not that bug.
- Round 2's "three independent server starts" adoption criterion implicitly assumed hashes are
  comparable across starts. They are not — not even for the first, entirely cold request. The
  criterion is restated as *the same pattern on three starts*, and comparisons of absolute hashes are
  confined to a single start.

## What would reopen it

- The effect moves a **value** (a date or an amount) on the 50-item suite under a cross-request cache
  pattern — then decision 1 becomes a serving-profile change (per-request isolation for extraction
  jobs), not a wording change.
- A build with the full vllm#53798 + #54076 (or a merged successor) shows the remainder closed — then
  the upstream comments get a follow-up and the recipe's two-line patch can be retired.
- The quality suite with the deterministic kernel scores below the current production fix on the same
  image across suites — then decision 3 reverts to "candidate" and the 21–28 % stays unclaimed.
- A `qsa_indexer.py`-shaped release (a v0.30 carrying the `main` indexer layout) — then vllm#56500
  becomes applicable and §5.4's flat plateau has to be re-measured against the 512 MB budget.
