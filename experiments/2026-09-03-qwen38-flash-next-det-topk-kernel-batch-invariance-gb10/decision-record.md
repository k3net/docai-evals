# Decision record — round 2: keep the production fix, adopt the deterministic kernel only through the recipe

**Date:** 2026-09-03 · **Status:** in force · **Experiment:** [README](README.md)

## Decision

1. **The night-slot configuration stays as it is** (`VLLM_QSA_EXACT_TOPK=1`, prefix cache on,
   MTP=2). Nothing in this round shows a regression in it; the MoE fused-finalize defect (vllm#54945)
   does not surface on our shapes, and PR #54948 is not adopted.
2. **We stop describing the night slot as "deterministic".** The supportable claim is
   *deterministic for sequential requests in the same prefix-cache state*. With concurrent requests
   (`--max-num-seqs 4`) identical prompts receive different logits from the serial case and from each
   other; a partial prefix-cache hit produces different logits than a full one. Any evaluation,
   regression test, A/B or cached-answer scheme built on bit-identity of this model's output is
   invalid; value-level comparison over repeated runs is the tool (round-1 `szoras.py`).
3. **The deterministic `persistent_topk` kernel (vllm#55122) is the candidate to replace the
   Python-level fix**: same determinism, 96–100 % of the stock prefill throughput against 76–90 % today.
   The main suite 50 × 3 with the kernel: **95.00/100, 0/50 unstable**, against 96.00 (one run) for
   the production fix on the same image — one reasoning item lands on the other side of a tie
   (T3-04); the other differing item scores 0 on both arms for an image-level serialisation reason.
   It goes to production **only** when all of the following hold:
   - the hard suite (10 × 3), the language challenge and a repeated main run-set show the T3-04 gap
     is a tie, not a direction — i.e. the kernel scores no worse than the current fix on the same
     image across suites (the adoption criterion was "no worse than 98/100"; that number belongs to
     the round-1 image and is not the right reference on `e655b7d`, where the fix itself scores 96);
   - the logprob probe passes on three independent server starts;
   - the recipe is vendored into the serving repository as a Dockerfile step with the kernel
     source at a pinned commit and the `.so` built into the image — the measurement image here was a
     `docker commit` of a patched container and is not a deployable artefact;
   - the server prints and the deploy check greps the activation line (`QSADET active`), fail-closed.
4. **Upstream**: a validation comment on vllm#55122 (another box, the official image, `FAILS: 0`,
   the throughput table) and a shape-dependence data point on vllm#54945. Production switches to a
   merged commit or to a pinned one, not to a moving branch.

## What this round corrected in round 1

- Round 1's probe measured the prefill only (`max_tokens = 1`) and its isolation arms ran with prefix
  caching off; the production claim was extrapolated. This round measured the production
  configuration itself: 91/92 sequential requests identical, and the one exception explained.
- Round 1 attributed the 1.35× prefill cost to determinism. It was the cost of a Python-level
  `torch.topk`; the kernel-level fix is essentially free.
- Round 1's "prefix-cache hit = cold, bit-identical" statement holds for a *full* hit; a *partial*
  hit differs. That distinction was not measured then.

## Why the batch result does not reverse decision 1

The stock kernel's damage (13/50 items flipping between runs, 5 in the extracted value) was
measured on sequential requests, and the fix removes it there. Concurrent requests move the logits
but, in every batch arrangement measured, did not move the visible answer. Whether they move a
*value* on the 13 round-1 items under load is the open question this record does not answer (F2d in
the lab notes); until it is measured, the operational assumption is value-level stability, not
bit-level.

## What would reopen it

- The arm-C main suite scores below the round-1 reference, or is unstable (> 0/50) — the kernel is
  not adopted.
- vllm#55122 changes shape before merging (the standalone build no longer matches) — rebuild and
  re-measure before any deployment step.
- A value-level flip on the round-1 unstable items under concurrent load (F2d) — decision 2 becomes a
  serving-profile change (per-request isolation for extraction jobs), not a wording change.
- A CUBLAS/illegal-memory-access crash of the vllm#54173 kind in the night-slot logs (0 in 14 142
  lines since 2026-08-31 at the time of writing) — prefix caching goes off in production until the
  align patches are in the image.
