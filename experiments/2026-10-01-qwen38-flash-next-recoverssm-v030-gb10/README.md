# Qwen3.8-Flash-Next on vLLM v0.30.0, round 8: RecoverSSM (vllm#58863) on GB10, and what the v0.30 prefix-cache default costs

**Date:** 2026-10-01 · **Type:** correctness / serving / performance · **Hardware:** one DGX Spark (GB10, `sm_121`, 121 GiB unified) ·
**Reproducibility:** R2 (code, the backport patch and every run artefact; the corpus is already published, the engine builds are third-party images)

> Status: **closed 2026-10-01.** Follows
> [2026-09-18-qwen38-flash-next-qwen-parser-marker-guard-gb10](../2026-09-18-qwen38-flash-next-qwen-parser-marker-guard-gb10/)
> and the cross-request prefix-cache rounds
> ([2026-09-12](../2026-09-12-qwen38-flash-next-prefix-cache-cross-request-gb10/),
> [2026-09-14](../2026-09-14-qwen38-flash-next-prefix-cache-root-cause-gb10/)).
> Production was not changed by this round.

## 1. What was the measurement for?

Three upstream developments landed at once, and we had to decide whether the next experimental build for
our night-shift model should include them:

1. **[vllm#58863](https://github.com/vllm-project/vllm/pull/58863)** (RecoverSSM for the Qwen GDN layers and
   the PLE short conv) was rebased on 2026-10-01 (head `c84caa4739`). It now carries a startup-OOM fix,
   FULL CUDA-graph builders and a fix for a race in the align-mode commit (`3388ba1`, reported as 9 of 12
   test runs failing before the fix and 20 of 20 passing after it).
2. A report that on **stock vLLM v0.30.0** the align-mode prefix cache was not being reused on a hybrid
   Qwen3.8 model. Our production recipe is still on v0.29.0, and the recipe we build from
   ([blazux/qwen3.8-Flash-DGX](https://github.com/blazux/qwen3.8-Flash-DGX)) moved to v0.30 as its only base
   on 2026-09-27.
3. Whether the round-4 cross-request divergence (a repeated greedy request can differ from its own cold
   run when an earlier, shorter request wrote the shared prefix) survives on v0.30 and with RecoverSSM.

## 2. On what task and dataset?

The synthetic Hungarian document corpus already published in this repository. Documents `D1`–`D7` are in
[2026-08-28 …/dataset](../2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/dataset/), and `C1`,
`C3`, `C5` are in
[2026-09-18 …/dataset/trap-corpus](../2026-09-18-cjk-damping-dose-response-gb10/dataset/trap-corpus/).
All of them are byte-identical (sha256) to the copies used here. Nothing new is published.

Prompts are built from these documents by the probes in [code/](code/): exact-length prompts sized through
the server's own `/tokenize`, token-id prompts cut from `D7`, and chat prompts with a fixed system message.
Cache isolation between probes uses `cache_salt`.

## 3. Which models and configurations were compared?

One checkpoint (`RadixArk/Qwen3.8-Flash-Next-NVFP4`, snapshot `7b71922…`), one machine. Every arm has the
same serving flags as production: `--max-model-len 262144 --max-num-seqs 4 --gpu-memory-utilization 0.78
--enable-prefix-caching --enable-chunked-prefill --max-num-batched-tokens 8192`, `cudagraph_mode=PIECEWISE`,
MTP `num_speculative_tokens=2`, `--kv-cache-dtype auto`, the deterministic QSA top-k kernel
(`QSADET active` in every log), and the PLE table served by the recipe's out-of-tree mmap loader. Only the
column(s) below differ. The exact launch script is [code/indit_r8.sh](code/indit_r8.sh).

| arm | image | difference |
|---|---|---|
| **K0** | recipe @ `5be6637` on `vllm/vllm-openai:v0.29.0` (= production) | — (retention resolves to dense, `None`) |
| **K1a** | recipe @ `bb661c4` on `vllm/vllm-openai:v0.30.0` | v0.30.0; retention unset (`0`) |
| **K1b** | same | `--prefix-cache-retention-interval 1600` |
| **K2off** | K1 + vllm#58863 backported (`a80e41d`…`3388ba1`, [patch](code/pr58863-c84caa4-v030-backport.patch)) | flag off |
| **K2on** | same image | `--use-replayssm` |

The effective configuration was read from inside the engine, not assumed. A logging-only overlay
([code/r8trace.py](code/r8trace.py), loaded through a `.pth` file) records the scheduler's block geometry,
the effective `prefix_cache_retention_interval` and the KV-cache groups at startup
([results/boot/](results/boot/)). All arms run on the V2 runner, with four `MambaSpec` groups and no
sliding-window group.

**Backport.** The eight non-merge commits of #58863 apply to v0.30.0 in order. The one manual step was a
parameter rename in a test helper (`tests/v1/cudagraph/test_cudagraph_manager.py`). There are 23 runtime
files, all Python, and every line the commits add is present in the result. The patch went on top of the
recipe image with a fail-closed import check ([code/Dockerfile.k2](code/Dockerfile.k2)).

## 4. Which metrics?

| metric | definition |
|---|---|
| `cached_tokens` | `usage.prompt_tokens_details.cached_tokens` per request (`--enable-prompt-tokens-details`); cross-checked against the `/metrics` `prefix_cache_hits_total` delta per scenario |
| request time | wall time of a request with `max_tokens=1`, used as a TTFT proxy in the cache probes |
| cross-request PASS/FAIL | over 4 identical requests B after one request A on a shared prefix (same salt), PASS = one distinct sha256 over the per-token top-20 (token, logprob) lists |
| cache-hit vs cold | the same prompt under a shared salt (hits) vs. unique salts (always cold); PASS = identical top-20 digests |
| boundary sweep | token-id prompts of length `k·B − d`; first differing output token between cold, cache-hit and follow-up-from-cache runs |
| decode ms/token | from streaming, after the first token, 1,000 forced tokens; the prompt is primed into the cache first |
| TTFT | streaming, cold (unique salt) |
| MTP acceptance | `/metrics` `spec_decode_num_accepted_tokens / num_draft_tokens` delta per cell |
| foreign-script / language switch | Han, Kana, Hangul, Cyrillic, Arabic, Thai characters; English 40-word windows with ≥ 35 % English stop words |

## 5. What was the result?

### 5.1 The v0.30 prefix-cache default: real, but narrower than "no reuse"

On v0.30.0 the unset `prefix_cache_retention_interval` is `0` (`None` on v0.29.0 through the
release-branch override). The `MambaManager` honours it: at `0` it keeps only the replay-boundary (and
shared-prefix-junction) states and drops the intermediate checkpoints of a long prompt.

| request (one shared document, same salt) | K0 v0.29 (dense) | K1a v0.30 (`0`) | K1b v0.30 (`1600`) |
|---|---|---|---|
| A: 85,890 tokens, cold | 0 | 0 | 0 |
| B: A's first ~50K tokens + another question (50,654) | **48,000** · 1.38 s | **0** · 18.0 s | **48,000** · 1.17 s |
| B again | 48,000 | 48,000 | 48,000 |
| C: A's full document + another question | 83,200 | 83,200 | 83,200 |
| same 9,698-token prompt, repeats 2–4 | 8,000 | 8,000 | 8,000 |
| 6-turn chat, each turn extending the last | 1,600 per turn | 1,600 per turn | 1,600 per turn |
| 45,642 / 85,890-token prompt repeated | 43,200 / 83,200 | same | same |

n = 1 sequence per cell on one server start. The repeated cells are deterministic (same counts on every
repeat and across the three arms), and the `/metrics` deltas match the per-request sums in every scenario.

⚠️ **We initially missed this.** Our first four scenarios (rows 4–7) were all repeats or continuations,
so they hit on the replay boundary under every setting, and we concluded that the retention setting was
inert on this model. The partial-prefix scenario (rows 1–3) was added afterwards and contradicts that
conclusion. The internal lab note is corrected accordingly.

The multi-turn ceiling of one block (1,600 tokens per turn) is the same on every arm. It comes from MTP's
tail-block drop in the scheduler, not from retention.

### 5.2 The round-4 cross-request divergence on v0.30.0 and with RecoverSSM

The condition vllm#54076 changes is still present in v0.30.0. A CPU replay of v0.30's
`_mamba_block_aligned_split` ([code/checkpoint_szonda_cpu_v030.py](code/checkpoint_szonda_cpu_v030.py))
predicts the same threshold as on v0.29: a prompt below `2·B` tokens saves no Mamba checkpoint.

Length sweep, B = 2·block + 61, one shared document (`D6`), separate salt per pair, 4 B-repeats per pair,
distinct A lengths:

| arm (block) | A < 2·block: lengths that diverge | A ≥ 2·block |
|---|---|---|
| K0, v0.29 (1600) | 2 / 5 | 0 / 5 |
| K1a, v0.30 (1600) | 4 / 5 | 0 / 5 |
| K2off, v0.30 + #58863, flag off (1600) | 4 / 5 (identical to K1a) | 0 / 5 |
| K2on, `--use-replayssm` (1664) | 2 / 4 | 0 / 6 |

Below the threshold, whether a given A length diverges depends on its exact length. Five lengths per
arm cannot support a rate, so read the 2/5 vs. 4/5 as "present on both", not as "worse on v0.30". A
cache-hit vs. cold comparison on four real documents (6 hits + 3 cold runs each) is 4/4 PASS on every arm:
the divergence needs a second, shorter request.

A prediction we derived ourselves failed. From the CPU replay we expected a second failure pattern
(A ≥ 3·block checkpoints only at 2·block), but it produced 0 divergences in 16 pairs across four arms.
We dropped it.

### 5.3 RecoverSSM (#58863) on this recipe

**Correctness: clean.**

| | result |
|---|---|
| unit tests on GB10 (`test_recoverssm_gdn`, `_ple`, `test_recoverssm_config`, `test_gpu_model_runner_v2_cudagraph_profiling`, `test_gdn_fused_mtp`) | **121 passed** |
| `test_recoverssm_gdn.py` ×20 at `3388ba1` | **20/20** pass |
| ×12 with `recoverssm_gdn.py` reverted to before `3388ba1` | **9/12** runs fail (1–4 failing cases per run) |
| boundary sweep, k ∈ {1, 2, 4, 8}, d ∈ {0, 1, 2, 3, 5, 10}, greedy, 256 tokens, plus a follow-up prompt (prompt + output + suffix) from cache vs. cold | **24/24** identical on both arms; 10 cache hits and 13 follow-up hits per arm were exercised |
| 24 long generations (T 0.6, presence 1.5, 4 concurrent, 6,000-token limit) | no switch into fluent off-topic text. All 24 hit the limit, and 17 were still in the reasoning. Isolated CJK characters inside Hungarian sentences: 3/24 with the flag, 6/24 without, a known trait of this model and sampler |

**Performance: no gain at MTP-2 with PIECEWISE.** Two starts per arm in alternating order (off, on, on,
off), two runs per cell, medians.

| | K2off | K2on |
|---|---|---|
| decode c=1, ~1K context | 27.25 ms/tok | 27.78 (+1.9 %) |
| decode c=1, ~40K context | 30.2 ¹ | 31.5 (+4 %) |
| decode c=4, ~1K / ~40K | 53.3 / 51.2 ¹ | 50.0 / 52.3 (inside the ±10 % spread between runs) |
| TTFT 8K / 32K / 64K | 3.08 / 11.65 / 23.31 s | 3.05 / 12.01 / 24.00 s |
| MTP acceptance c=1, 1K / 40K | 0.933 / 0.821 | 0.906 / 0.766 |
| KV cache at `gpu_memory_utilization 0.78` | 288,213 / 295,455 tokens | 296,677 / 295,108 |

¹ From one start only: the first native start used a 60K context, where four streams evicted the primed
prefix. At c=4 / 40K only one of the two runs kept the prefix cached, so that cell is a single run.

The gains reported in the PR came with FULL graphs and K = 3/5. We ran neither: our PLE loader adds its own
splitting op.

**The block grows from 1600 to 1664 tokens** with `--use-replayssm`: the replay record enlarges the Mamba
page, and the attention block follows it. With the tail-block drop, prompt-cache hits come in units of that
block, so a repeated 9,698-token prompt hits **6,656** tokens instead of 8,000 (request time 0.80 → 1.22 s).
Long prompts are barely affected (85,890 tokens: 83,200 either way).

### 5.4 Other observations

- **KV capacity on v0.30.0:** at the same `gpu_memory_utilization`, the recipe's v0.30 image gets 292,558 KV
  tokens against 433,044 on v0.29 (−32 %). Its "weights + non-torch" usage is 84.4 GiB against 80.6 GiB. We
  have not found the cause.
- **Cold prefill on v0.30.0** is faster than on v0.29.0 (45,642 tokens: 16.6 vs. 19.9 s; 85,890: 30.8 vs. 38.0 s;
  n = 1 each).
- **Kernel log:** non-fatal `NVRM … NV_ERR_NO_MEMORY` lines appeared during four boots: three of the v0.29
  control (production-equivalent) and one RecoverSSM start. There was no Xid, and where MemAvailable was
  sampled it stayed ≥ 20 GiB. Every server came up and served normally. This was the first time we could
  read the kernel log on this box, so there is no baseline for how often production boots log it.
- **Stability:** no Traceback, illegal-access or worker-restart line in any container log. MemAvailable
  never fell below 17.2 GiB.

## 6. What product decision followed?

See [decision-record.md](decision-record.md). In short: production stays on v0.29.0. RecoverSSM in this
form (PIECEWISE, mmap PLE, MTP-2) does not go into the night recipe. If we move to v0.30,
`--prefix-cache-retention-interval 1600` is mandatory.

## 7. What are the limits of the measurement?

- One box, one checkpoint, MTP-2, PIECEWISE only. FULL graphs, K = 3/5 and #59366 (fused CUDA verify) were
  not run.
- The backport is #58863 on v0.30.0, not the PR head on main.
- The partial-prefix result is one sequence per arm (deterministic, but one document and one cut point).
- The cross-request sweep has five A lengths per arm below the threshold. That supports "present", not a rate.
- The long-generation probe mostly exercised reasoning text (17/24 never reached the answer), and its
  detector is a heuristic.
- c=4 decode varied by ±10 % between runs, larger than the effect being measured.
- The probe that sizes exact-length prompts was rewritten mid-round (bisection, seed-independent filler).
  One early K0 run with the old sizer is discarded and not published.
- No quality suite (KIE scoring) was run on the RecoverSSM arm.

## 8. Which DocAI article belongs to it?

None. Production did not change, so there is no user-facing story yet.

## Layout

```text
code/      probes, launch script, trace overlay, Dockerfiles, the #58863 backport patch (full, runtime, tests)
results/   M1* prefix reuse · M1e* partial prefix · M2a/M2s* cross-request cells and sweep · M2b* hit vs cold
           M3h* boundary sweep · M3ny* long generations · M6* performance
results/boot/   startup log lines and the trace overlay's init record per arm
results/logs/   unit-test runs (M4-*), probe stdout, MemAvailable samples (1 s)
```

File names use the arm labels above. `K0e`, `K1e` and `K1be` are the partial-prefix runs on fresh starts of
K0, K1a and K1b.
