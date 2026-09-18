# Decision record — the parser rebuild is adopted; the model-side termination is carried as a known exposure

**Date:** 2026-09-18 · **Status:** in force · **Experiment:** [README](README.md)

## Decision

1. **The rebuilt image is adopted** in place of the pinned one. Unusually for us, this needed no
   judgement call about blast radius: 8 of 28,459 Python files differ, the deterministic top-k
   `.so` is byte-identical, and each of the five non-parser differences was checked to be inert on
   this checkpoint and these launch flags. The regression gate reproduces the pre-patch pattern
   cell for cell. There is nothing here to weigh against the benefit.

2. **Nothing else in the recipe moves with it.** The upstream recipe changed its default
   checkpoint to NVIDIA's NVFP4, switched `FAST_ROWS` to 0 and began rewriting the chat template
   for `reasoning_effort`. All three live in `serve.sh` or in defaults we override explicitly, so
   none of them reached us — but only because we launch from a pinned `docker run` rather than
   from the recipe's script. That remains the right arrangement and is the reason this A/B was
   one variable at all.

3. **The determinism claim is unchanged.** The round-4 formula still holds verbatim: a repeated
   request can diverge from its own cold run when an earlier request over the same prefix was
   shorter than `2 × block_size`. This image does not carry the boundary stop and the failing cell
   still fails. Nothing about the parser work touches that, and we have now confirmed rather than
   assumed it.

4. **`--tool-call-parser qwen3_coder` stays.** We checked the alternative reading — that the
   `name == "qwen3"` gate excludes the coder parser — and it is wrong. Switching parsers would
   have been a real configuration change made for no reason.

5. **The model-side termination is carried as a known exposure, not fixed.** With tools in the
   request, a prompt that leads the model to write `<tool_call>` into its own reasoning can end
   the turn with EOS and no answer. No serving-layer guard can reach this: with the parsers
   bypassed, the raw generation is already truncated. We do not have a workaround we are willing
   to run — suppressing the token, or forbidding tool definitions on prompts about tool syntax,
   both cost more than the failure does at the rate we have seen.

6. **What goes upstream, and where.** Three separate posts, because they are three separate
   findings: a new vLLM issue for the fenced-code-block case (none exists; vllm#56658 is
   specifically the prose case); a comment on vllm#56661 with the patch-12-in-isolation result,
   since the author cannot see from their own tests that their patch leaves the fenced case
   untouched; and a note to the recipe repository that its "not covered" bullet has a second
   failure mode underneath it. The DocAI article is not written and is not a prerequisite.

## What we deliberately did not do

- **Did not swap the deterministic top-k `.so`** for vllm#55122's current head. The PR has been
  carried across the upstream kernel refactor and compiles for `sm_121`, but the full `_C` build,
  the kernel tests and a serving A/B are missing, and the earlier 21–28% advantage cannot be
  assumed to survive the new base. The `.so` in the adopted image is the same validated binary,
  byte for byte.
- **Did not touch vllm#52244** (hybrid GDN + MTP prefix-cache hits). It is still `needs-rebase`,
  and it is a TTFT change rather than a determinism fix.
- **Did not re-run the quality suite, the soak or the throughput sweep.** This was scoped as a
  maintenance validation and is labelled as one.

## What would reopen this

- Any measurement of how often the model-side termination fires on production traffic. That is the
  number that decides whether 5 above stays "carry it" or becomes a mitigation task, and it is the
  obvious next piece of work.
- ~~A streaming-versus-non-streaming divergence on the same generation.~~ **Settled, negative.**
  The live probe showed different answer lengths across the two modes for the same prompt, which
  looked like vllm#47903. Replaying the identical captured raw text through both parse paths gives
  zero divergences over twelve generations and three chunk sizes, so the difference was the model
  generating different text on two separate calls. We report nothing to that issue. It would
  reopen only on a divergence that survives the replay.
- vllm#56661 landing, or changing shape, on `main` — at which point the patch-12 measurement here
  is about a backport that no longer matches.
- An upstream fix for the fenced-code-block case, which would let us drop a locally carried patch.
- A block size other than 1600, which moves the round-4 threshold and therefore the regression
  gate's cell boundaries.
