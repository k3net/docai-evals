# Decision record — round 4: the root cause is named, the fix goes upstream, nothing changes in production yet

**Date:** 2026-09-14 · **Status:** in force · **Experiment:** [README](README.md)

## Decision

1. **Prefix caching stays on in the night slot, unchanged.** Round 3's reasoning is untouched: the
   effect lives in the logits, and the safeguards (three runs with an agreement check for extraction,
   a separate verification step for chat) stay as they are. What changes is that we can now state the
   exposure precisely instead of as a length heuristic, see 3 below.

2. **The one-line patch is *not* adopted locally.** It removed the divergence on the test build, but
   it is one condition lifted out of an open pull request that touches four files. Hand-carrying a
   fragment of someone else's fix into our serving image is exactly the undocumented divergence we
   refused for vllm#56500 in round 3. We wait for
   [vllm#54076](https://github.com/vllm-project/vllm/pull/54076) to land, and re-measure then, with
   throughput and the quality suite included.

3. **The determinism claim is narrowed a third time, and now has a formula.** It previously read
   *"sequential requests whose shared prefix blocks were written by a request of the same shape"*.
   It now reads: **a repeated request can diverge from its own cold run when an earlier request over
   the same prefix was shorter than `2 × block_size` while the repeated one is not.** With the block
   size at 1600 tokens, the exposed window is a first request under 3200 tokens followed by a longer
   one on the same document. Any regression test, A/B or cached-answer scheme resting on bit-identity
   remains invalid, but the affected traffic pattern can now be identified rather than guessed at.

4. **The finding goes upstream to #54076, not into a separate write-up.** The PR already contains the
   fix and the correct rationale; what it lacks is an independent GB10 reproduction showing the
   user-visible consequence and a case where the fix is verified to remove it. That is what we send.

5. **Recipe consumers are told.** The two-line patch in
   `blazux/qwen3.8-Flash-DGX` fixes the block *size* but not the boundary *stop*, so every deployment
   built from that recipe with MTP enabled carries this behaviour. We report it there as well, as a
   finding, not as a patch request.

## What would reopen this

- `#54076` landing (or changing shape): re-run the threshold matrix and the original item pair on a
  build carrying the full PR, and add the 8K–64K prefill sweep and the 50-item suite.
- Any measurement locating the first numerically differing operation; that would tell us whether the
  chunk-shape dependence is a kernel bug in its own right rather than an accepted numerical
  difference.
- A change in block size (1600 today) moves the threshold with it; the formula, not the number, is
  what we carry forward.
- Evidence that the effect can move an argmax, not only the logit tail. Nothing here shows that, and
  the visible text was stable in every arm of rounds 3 and 4.
