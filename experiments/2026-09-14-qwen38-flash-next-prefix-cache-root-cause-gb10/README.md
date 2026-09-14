# Qwen3.8-Flash-Next NVFP4 on vLLM, round 4: the root cause is a Mamba checkpoint the scheduler skips, and one line removes it

Round 3 established *that* a full prefix-cache hit changes the greedy logits when the shared prefix
was written by a differently sized request, on two independently built stacks. It did not establish
*why*, and one of its predictions failed on a third document.

This round identifies the mechanism in the scheduler source, derives a sharp numeric threshold from
it, confirms the threshold on the GPU, and shows that a one-line backport of the boundary stop from
[vllm#54076](https://github.com/vllm-project/vllm/pull/54076) eliminates the divergence, including
the original failing item.

## 1. What was the measurement for?

Three questions, in order:

1. Does the missing `Scheduler._mamba_block_aligned_split` boundary stop explain the round-3
   pass/fail pattern, including the D1 pair that **broke** round 3's "different block count" rule?
2. Does the threshold it implies (prompt length vs `2 × block_size`) hold on the GPU, on documents
   and lengths chosen in advance?
3. Does the narrow backport of that one condition remove the divergence on the same build?

The starting point was an external source review of our published round-3 package, which pointed at
the condition below. We verified every claim of it against the source of the **running** image, not
against an upstream checkout.

## 2. On what task and dataset?

Same synthetic Hungarian corpus as rounds 1–3 (`D1`–`D7`, shipped in the round-1 experiment
directory). Two probe designs:

- **threshold matrix** — shared prefix `D6.md` (3052 tokens including the chat template), then a
  per-cell deterministic filler sized to an exact total prompt length through the server's own
  `/tokenize` endpoint, one `cache_salt` and one filler seed per cell so cells cannot contaminate
  one another within a single server start;
- **the original round-3 item pair** — `T3-01` ×1 then `T2-01` ×10 over the shared `D2.md`
  (3169 / 3227 tokens), run with the unchanged round-3 probe.

No ground truth is involved: every comparison is the engine against itself.

## 3. Which models and configurations were compared?

| arm | build | scheduler |
|---|---|---|
| control | `vllm/vllm-openai:v0.29.0` image built from the recipe (round-3 arm B, byte-identical), det top-k kernel active | recipe's two-line patch only |
| patched | the **same image**, same flags, same container | + the `#54076` boundary stop, applied to the source at container start |

Both arms add `--enable-prompt-tokens-details`, which round 3 lacked.

The patch, in full:

```diff
-            next_block_boundary if start % block_size != 0 else 0,
+            0 if use_internal_checkpoint else next_block_boundary,
```

This is the narrow semantic backport of one condition from `#54076` (an open PR touching 4 files,
+287/−17), **not** the whole PR.

## 4. Which metrics?

- **`full_logprob_hash_variants`** (primary): distinct sha256 digests over the per-token top-20
  `(token, logprob %.12g)` lists across N identical sequential requests. PASS = 1 variant.
- **`canonical_hash_variants`**: the same digest over candidate lists sorted by token id, so a pure
  reordering of tied candidates cannot produce a difference on its own. *New in this round.*
- **`cached_prompt_tokens`**: `usage.prompt_tokens_details.cached_tokens` per request, as reported by
  the server. *New in this round; round 3 inferred hit lengths instead of measuring them.*
- **`shared_candidate_logprob_delta`**: max |Δ logprob| over candidates present in both runs, from
  the stored raw top-20 lists. *New in this round.*
- **`checkpoint_rule_agreement`** (source probe, CPU): does "A checkpoints at the shared boundary"
  predict the measured PASS/FAIL?

## 5. What was the result?

### 5.1 The rule explains all eight round-3 pairs, including the counterexample

With MTP the scheduler backs the last cacheable position off by one full block:

```python
last_cache_position = request.num_tokens - request.num_tokens % block_size
if self.use_eagle:
    last_cache_position = max(last_cache_position - block_size, 0)
```

so a request shorter than `2 × block_size` (3200 tokens here) prefills as a single chunk and stores
**no** Mamba/GDN state at 1600, while still publishing its KV blocks there.

| pair | A | A checkpoints | B | B checkpoints | rule | round-3 measurement |
|---|---:|---|---:|---|---|---|
| T2-01 (D2) | 3169 | **no** | 3227 | yes | diverge | **diverged** |
| D6 unequal | 3086 | **no** | 3267 | yes | diverge | **diverged** |
| D6 equal | 3307 | yes | 3371 | yes | stable | stable |
| D3 equal (arm B) | 3264 | yes | 3346 | yes | stable | stable |
| **D1 unequal** | 4689 | yes | 4870 | yes | **stable** | **stable** |
| T5-01 | 2155 | no | 2182 | **no** | stable | stable |
| T4-01 clean | 1859 | no | 1859 | **no** | stable | stable |
| T9-01 / D5 | 24384 | yes | 24404 | yes | stable | stable |

**8/8.** The D1 pair, which round 3 recorded as a failed prediction, is explained: A is far above the
threshold and does write the checkpoint. Round 3's variable (difference in block count) was a
symptom; the causal variable is whether the *first* request checkpoints.

### 5.2 Nine tokens flip determinism (control arm, one server start)

| cell | A | B | prediction | measured | B `cached_tokens` |
|---|---:|---:|---|---|---|
| A below, B above | **3196** | 3259 | FAIL | **FAIL** | `[0, 1600, 1600, 1600]` |
| A above, B above | **3205** | 3259 | PASS | **PASS** | `[0, 1600, 1600, 1600]` |
| both below | 3097 | 3160 | PASS | **PASS** | `[0, 0, 0, 0]` |
| A above, B below | 3205 | 3160 | PASS | **PASS** | `[0, 0, 0, 0]` |

4/4. The first two rows share the same document and the same `B`; `A` differs by nine tokens.

### 5.3 The first B run is a *zero* hit, not a partial one

`cached_tokens` for `B#1` is **0** in every cell, including the failing one, although `A` had already
written the identical first 1600 tokens. Without the matching state the hybrid lookup cannot use the
KV blocks at all. This corrects round 3's "partial hit" reading and explains why `B#1` is
bit-identical to the cache-free arm: it really is cold. The divergence appears exactly at the run
where `cached_tokens` jumps to 1600.

### 5.4 The logprobs move numerically

First three generated tokens of the failing cell, `B#1` vs `B#2`:

| token | shared candidates | argmax | max \|Δ logprob\| | shared candidates with a different value |
|---|---|---|---:|---|
| #0 | 19/20 | same | 0.745 | 19/19 |
| #1 | 19/20 | same | 0.664 | 19/19 |
| #2 | 18/20 | same | 1.062 | 18/18 |

The candidate set itself changes and the canonical (token-id-sorted) digest also has two variants,
so this is not a tie-reordering artefact. The argmax is stable here, which is why the visible text
was identical across all runs in round 3 as well.

### 5.5 The one-line backport removes it

| case | control | patched |
|---|---|---|
| A below (3196), B above (3259) | **FAIL** | **PASS** |
| the other three cells | PASS | PASS |
| **the original round-3 item pair, ×10** | **FAIL** (3 rounds, 2 stacks) | **PASS, 10/10 identical** |

### 5.6 Mixed origin alone is not the defect

On the patched arm the `cached_tokens` pattern is **unchanged** (`B#1` = 0, `B#2+` = 1600): block
origin is still mixed, yet the result is bit-identical. The reading this supports is that the missing
checkpoint is what allowed the shared block's KV to be written by a single 3196-token chunk while the
state came from a 1600-token chunk, and that the same tokens under a different chunk shape produce
different numbers. That is an inference from behaviour; no tensor-level comparison was made.

## 6. What product decision followed?

None yet, deliberately. See `decision-record.md`: prefix caching stays on in production, the patch is
**not** adopted locally, and the finding goes upstream instead.

## 7. What are the limits of the measurement?

- No kernel-level instrumentation: the first numerically differing operation is still unlocated.
- The logprob digest is **not stable across server starts** (round-3 finding), so the control and
  patched arms cannot be compared to each other; every conclusion here is within a single start.
- One line, not the whole PR. `#54076` changes 4 files; the rest is untested here.
- No performance measurement of the patched arm: stopping at every block boundary adds scheduler
  steps and kernel launches, and the 8K–64K prefill sweep was not re-run.
- The 50-item quality suite was not re-run on the patched arm.
- 4 repetitions per cell in the matrix (10 for the original item pair).
- Container logs are not published; the launch arguments are reproduced in this README instead.

## 8. Which DocAI article belongs to it?

[A gyorsítótár megváltoztatta a választ](https://docai.hu/blog/prefix-cache-megvaltoztatja-a-valaszt) ·
[The prefix cache changed the answer](https://docai.hu/en/blog/prefix-cache-changes-the-answer)
(the "Update, 14 September" section).

Predecessor: [2026-09-12-qwen38-flash-next-prefix-cache-cross-request-gb10](../2026-09-12-qwen38-flash-next-prefix-cache-cross-request-gb10/).

## Layout

```text
code/checkpoint_probe.py          # GPU: threshold matrix, cached_tokens + raw top-20
code/scheduler_source_probe.py    # CPU: AST-extracts the running image's scheduler and replays the split
results/round4-ctrl-cell1.json    # control arm, failing cell
results/round4-ctrl-cells234.json # control arm, cells 2-4
results/round4-fix-cells1234.json # patched arm, all four cells
results/round4-fix-t201-contaminated.json  # patched arm, the original round-3 item pair x10
docs/                             # Hungarian lab note
```

The original item-pair probe (`t201_partial_hit.py`) is unchanged from the
[round-3 package](../2026-09-12-qwen38-flash-next-prefix-cache-cross-request-gb10/code/t201_partial_hit.py)
and is not duplicated here.
