# Decision record — production stays on v0.29.0; RecoverSSM is not adopted in this form

**Date:** 2026-10-01 · **Status:** in force · **Experiment:** [README](README.md)

## Decision

1. **Production does not change.** The night-shift model stays on the v0.29.0 recipe (`5be6637`, MTP-2,
   PIECEWISE, mmap PLE, deterministic top-k), which resolves the prefix-cache retention to dense.

2. **RecoverSSM (vllm#58863) is not adopted in this form.** It is correct on every probe we ran, and the
   race fix it carries reproduces exactly. On our recipe, though, it is 2–4 % slower per decoded token, has
   lower MTP acceptance, gives no measurable KV gain, and coarsens prompt-cache granularity (block
   1600 → 1664). The gains reported upstream come with FULL graphs and K = 3/5. We cannot run FULL graphs
   until the PLE loader is replaced (vllm#58815 or equivalent).

3. **A move to v0.30 is a separate decision, with one hard condition.** If we move,
   `--prefix-cache-retention-interval 1600` goes into the launch command. Without it, a request that shares
   only part of a long earlier prompt gets no cache hit (0 vs. 48,000 tokens, 18 s vs. 1.2 s).
   A move also has to explain or accept the 32 % lower KV capacity of the v0.30 image.

4. **The cross-request divergence stays a known exposure.** It is present on v0.29.0, on v0.30.0 and with
   RecoverSSM, under the same condition. The existing mitigations (repeated KIE runs with agreement checks)
   stay.

## What would reopen it

- vllm#58863 merging together with a PLE path that allows FULL graphs on our recipe. That would be the
  configuration the upstream gains were measured in, so the speed question would need re-running.
- vllm#58549 (or an equivalent default) landing in a release. The retention flag would then no longer be
  needed, but the partial-prefix probe (`M1e`) must be re-run before dropping it.
- An explanation for the v0.30 KV-capacity drop.
