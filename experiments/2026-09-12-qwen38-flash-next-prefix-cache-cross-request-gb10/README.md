# Qwen3.8-Flash-Next NVFP4 on vLLM, round 3: cross-request prefix-cache reuse changes the greedy logits — on two independently built stacks

**Date:** 2026-09-12 · **Type:** correctness / serving · **Hardware:** one DGX Spark (GB10, `sm_121a`, 121 GiB unified) ·
**Reproducibility:** R2 (code + every run artefact; the corpus ships in the round-1 directory, the engine builds are third-party images)

> Status: **closed 2026-09-12** — the follow-up to
> [2026-09-03-qwen38-flash-next-det-topk-kernel-batch-invariance-gb10](../2026-09-03-qwen38-flash-next-det-topk-kernel-batch-invariance-gb10/).
> Round 2 left one item failing the determinism probe and explained it as "a partial prefix-cache hit
> is not a full one". **That explanation was the wrong way round**, and this round shows why.

## 1. What was the measurement for?

Three questions, in this order:

1. **Which cache path is actually wrong?** Round 2 (09-03) and round 3 (09-12) both see the same
   single probe item (one of four drawn from the fifty-item suite) fail the same way: run 1's per-token
   logprob hash differs, runs 2–10 are identical to each other. (In round 1 the stock kernel made every
   item diverge, so the pattern was not visible yet.) Round 2 assumed the *partial* hit (run 1) was the faulty path.
2. **Does the current release image fix it?** `blazux/qwen3.8-Flash-DGX` now has a `v0.29` profile
   built on the **official** `vllm/vllm-openai:v0.29.0` instead of the preview build we run, and it
   ships the deterministic top-k kernel (vllm#55122) compiled in.
3. **Is [vllm#56500](https://github.com/vllm-project/vllm/pull/56500) (bounded QSA prefill logits
   workspace) worth adopting**, and does its symptom — reserved memory growing in steps with context
   length — reproduce on this recipe at all?

## 2. On what task and dataset?

The round-1 synthetic Hungarian KIE corpus (`D1–D7`, `items.jsonl`), which ships in the round-1
directory and is **not duplicated here**. Probe items are the same four as round 2 (prompt lengths
3 169 – 24 416 tokens), plus three further document pairs and two documents used only as
block-boundary prefixes (`D6`, `D1`).

The memory sweep uses synthetic filler sized to an exact token count through the server's own
`/tokenize` endpoint, with a **unique seed per step**, so every step is a genuine cold prefill
(`vllm:prefix_cache_hits_total` stays flat across the sweep).

## 3. Which models and configurations were compared?

One checkpoint (`RadixArk/Qwen3.8-Flash-Next-NVFP4`, snapshot `7b71922…`), one machine, **two
independently built engines**:

| | **arm A** | **arm B** |
|---|---|---|
| base image | pinned preview build, vLLM `0.1.dev20073+g8e685d198` (blazux `e655b7d`) | official `vllm/vllm-openai:v0.29.0`, `VLLM_BUILD_COMMIT=98dff2a81d74` |
| recipe | vendored into our serving repo | `blazux/qwen3.8-Flash-DGX` @ `c578815`, `Dockerfile.v0.29` |
| model package in the engine | `vllm/models/qwen3_8_flash_next` | `vllm/models/qwen4_exp` |
| QSA block selection | exact `torch.topk` (`VLLM_QSA_EXACT_TOPK=1`) | **deterministic kernel** (vllm#55122), `QSADET active: …/_C_det.so` in the log |
| det-kernel source | — | `jschmied/qwen38-flash-next-gb10` @ `e0ef69d4f557…`, sha256-pinned files, `DET_ARCH=121a` |

Everything else identical and verified from the startup log: `--max-model-len 262144 --max-num-seqs 4
--gpu-memory-utilization 0.78 --enable-prefix-caching --enable-chunked-prefill
--max-num-batched-tokens 8192`, `cudagraph_mode=PIECEWISE`, MTP=2, `--kv-cache-dtype auto`,
`--no-enable-flashinfer-autotune`, `Mamba cache mode … 'align'`, `attention block size … 1600 tokens`.

⚠️ **One parameter could not be identical**: the `-cc.splitting_ops` names changed with the package
rename. Starting arm B with arm A's list fails during CUDA graph capture, because the disk-backed PLE
lookup then lands *inside* the graph:

```
vllm_ple_mmap.py:289  ids.detach().to("cpu", non_blocking=False)
RuntimeError: Cannot copy between CPU and CUDA tensors during CUDA graph capture …
```

The recipe handles this through an image label (`qwen38.base`) that `scripts/serve.sh` reads; a
direct `docker run` has to carry the right list by hand.

## 4. Which metrics?

- **Per-token logprob signature** ([code/t201_partial_hit.py](code/t201_partial_hit.py),
  [code/blokkhatar_szonda.py](code/blokkhatar_szonda.py), and round 2's `logprob_szonda.py`):
  `sha256` over the top-20 `(token, logprob %.12g)` list of every generated token. Visible-text SHA is
  recorded beside it — **same text, different logits is still a FAIL**.
- **Arm design** — each arm on its **own fresh server start** where the cache state is the variable:
  *clean* (`B × 10`, nothing else), *contaminated* (`A × 1`, then `B × 10`, sharing a long prefix),
  *control* (the contaminated sequence with `--no-enable-prefix-caching`).
- **Block-boundary probe** ([code/blokkhatar_szonda.py](code/blokkhatar_szonda.py)): the shared prefix
  and both tails are sized through `/tokenize` so that the two requests seal a **different** or an
  **equal** number of full 1 600-token blocks.
- **Memory / prefill sweep** ([code/qsa_memoria_timeline.py](code/qsa_memoria_timeline.py)):
  8K→16K→24K→32K→48K→64K cold prefills, with host memory (`free -m`) and `/metrics` before and after
  each step.

## 5. What was the result?

### 5.1 The failing path is the *full* cache hit, not the partial one

Same target request `B`, three arms, each on a fresh server start:

| arm | sequence | prefix cache | result (full logprob hash) |
|---|---|---|---|
| clean | `B` × 10 | on | `fdc948fbf8f7698f` × 10 — **stable** |
| contaminated | `A` × 1, then `B` × 10 | on | `B#1` = `fdc948fbf8f7698f`, `B#2–10` = `dabe443eeea90df5` |
| control | `A` × 1, then `B` × 10 | **off** | `c1dc6688b1004f2f` × 10 — **stable** |

`B#1` — the run that gets a *partial* hit on `A`'s blocks and prefills its own tail — reproduces the
fully cache-free clean arm **bit for bit**. The runs that diverge are the **full** hits, from token 0.
In the clean arm runs 2–10 are also full hits and nothing goes wrong. The variable is therefore
**which request wrote the shared blocks**, not "cold vs. cached".

Turning prefix caching off removes the divergence. (Its absolute hash necessarily differs: without
prefix caching the engine never switches to `align` Mamba mode — the log line is simply absent — so a
different numeric path runs. The metric is stability, not the value.)

⚠️ **This is not the already-fixed all-zero-state bug.** The recipe's two-line
`patch_mamba_block_size.py` — which touches exactly the files of vllm#53798
(`v1/worker/gpu/model_states/mamba_hybrid.py`) and vllm#54076 (`v1/core/sched/scheduler.py`) — is
present and verified in **both** images. What remains is a subtler, cross-request effect.

### 5.2 It reproduces on a completely different stack

Arm B — official release image, different vLLM version, different model package name, deterministic
CUDA kernel instead of the `torch.topk` fallback — gives **the same 3/4 pass, the same failing item,
the same shape** ([results/round3-B-szonda-48tok.json](results/round3-B-szonda-48tok.json)).

So the effect is not a property of our preview build, of the older package version, or of the
exact-topk workaround.

### 5.3 A prediction that held on one document and failed on another

The log gives the cache block size (`Setting attention block size to 1600 tokens …`). Among the pairs
measured, the failing one is the only one where the two requests seal a **different** number of full
blocks:

| pair | A prompt | B prompt | full blocks | result |
|---|---:|---:|---|---|
| the failing pair (`D2`) | 3 169 | 3 227 | **1 vs 2** | ⛔ diverges |
| `D3` pair | 2 155 | 2 182 | 1 vs 1 | ✅ stable |
| `D5` pair | 24 384 | 24 404 | 15 vs 15 | ✅ stable |

Sizing two tails onto either side of a boundary, on documents never used on that server start:

| # | prefix | A / B prompt | full blocks | arm | result |
|---|---|---:|---|---|---|
| 1 | synthetic filler, 1 680 tok | 3 091 / 3 308 | 1 vs 2 | A | ✅ stable |
| 2 | synthetic filler | 3 307 / 3 371 | 2 vs 2 | A | ✅ stable |
| 3 | **real document `D6`, 3 002 tok** | 3 086 / 3 267 | **1 vs 2** | A | ⛔ **diverges** |
| 4 | `D6` (fresh start) | 3 307 / 3 371 | 2 vs 2 | A | ✅ stable |
| 5 | real document `D1`, 3 696 tok — **same start as #4** | 4 689 / 4 870 | 2 vs 3 | A | ✅ stable |
| 6 | `D6` | 3 086 / 3 267 | **1 vs 2** | **B** | ⛔ **diverges** |
| 7 | `D3` — **same start as #6** | 3 264 / 3 346 | 2 vs 2 | **B** | ✅ stable |

Row 3 is the strongest single result of the round: the effect was **produced on demand**, on a
document that had never been used, by arithmetic alone. Rows 6–7 repeat that on the other stack
**within one server start**.

Rows 1 and 5 are the honest other half: synthetic low-entropy filler never triggers it, and a
different real document with the same block-count asymmetry stays stable. **Crossing a block boundary
looks necessary but is not sufficient**; length or content matters too. The QSA sparse block
selection — which itself depends on context length and content — is the leading remaining suspect,
and this round does not separate it out.

### 5.4 Memory: no step function, and the deterministic kernel is 21–28 % faster

Cold prefills, unique filler seed per step, `vllm:prefix_cache_hits_total` flat throughout:

| prompt tokens | arm A prefill | **arm B prefill** | A tok/s | **B tok/s** | speedup |
|---:|---:|---:|---:|---:|---:|
| 8 024 | 4 622 ms | **3 827 ms** | 1 736 | **2 097** | **+21 %** |
| 16 019 | 8 776 ms | **7 021 ms** | 1 825 | **2 282** | **+25 %** |
| 24 027 | 12 876 ms | **10 478 ms** | 1 866 | **2 293** | **+23 %** |
| 32 022 | 17 062 ms | **13 652 ms** | 1 877 | **2 346** | **+25 %** |
| 48 025 | 25 491 ms | **20 473 ms** | 1 884 | **2 346** | **+25 %** |
| 64 028 | 35 271 ms | **27 654 ms** | 1 815 | **2 315** | **+28 %** |

Host memory stays on a flat plateau on both arms (before-step readings 107 557–107 570 MB on A and
106 382–106 427 MB on B; the only larger move is a 425 MB *drop* after A's 64K step); no step per
context length, no preemption, no worker restart, no OOM in any of the seven container logs.

⚠️ **Measurement limit:** on GB10 the memory is unified, `nvidia-smi --query-compute-apps=used_memory`
returns `[N/A]`, and the torch caching allocator's `reserved` value is not readable from outside the
engine process. The figures are a host-level proxy: they show the growing prefills do not force new
host/unified allocations, not that the in-process `reserved` number is byte-stable.

### 5.5 vllm#56500 cannot be applied to either shippable base

Its main hunk rewrites `vllm/models/qwen4_exp/nvidia/ops/qsa_indexer.py`, created on 2026-09-02 by
vllm#54513. Verified inside the running containers:

| base | model package | `nvidia/ops/` | `qsa_indexer.py` |
|---|---|---|---|
| preview (arm A) | `qwen3_8_flash_next` | `qsa.py`, `qsa_pre_indexer.py`, `hc.py` | ⛔ absent |
| `v0.29.0` (arm B) | `qwen4_exp` | `qsa.py`, `qsa_pre_indexer.py`, `hc.py` | ⛔ absent |
| `main` | `qwen4_exp` | `qsa_indexer.py`, … | ✅ present |

Both shippable bases carry the older shape, where the chunk budget is a module constant
(`_LOGITS_WORKSPACE_BYTES = 128 * 1024 * 1024`) rather than `envs.VLLM_SPARSE_INDEXER_MAX_LOGITS_MB`
(512 MB). `vllm.v1.worker.workspace.current_workspace_manager` *does* import on both, so the receiving
infrastructure exists — but `qsa_select_paged_prefill` / `_prefill_logits` do not, so the diff has
nothing to attach to. Combined with §5.4 (the symptom does not reproduce here at all), the PR is not
adopted and not back-ported.

## 6. What product decision followed?

See [decision-record.md](decision-record.md). Short version: prefix caching **stays on** in the night
slot; the claim "deterministic at temperature 0" is narrowed once more; the deterministic kernel's
measured 21–28 % prefill win moves it from "candidate" to "adopt once the quality suite is re-run";
vllm#56500 is not adopted.

## 7. What are the limits of the measurement?

- **The mechanism is not identified.** The block-count asymmetry reproduces the effect on two
  documents and fails to on a third; no kernel-level instrumentation was done.
- **The upstream PRs were not tested in their full form.** Only the recipe's two-line equivalent of
  vllm#53798 / #54076 was present. Whether the full PRs close the remainder is open.
- **Absolute hashes are not stable across server starts** — not even for the very first, entirely
  cold request (the same preparatory request hashed `a11bda…`, `4851c3…`, `4851c3…` on three starts).
  Only the *pattern* reproduces. Comparisons are therefore valid within a start, not across starts.
- The quality suite (50 items × 3) was **not** re-run in this round; §5.4's speedup says nothing about
  extraction accuracy, and round 2 showed the two top-k paths produce different text.
- No multi-hour soak, no 128K/262K context step.
- Top-20 served logprobs only, server-quantised; distinct-vector counts are conservative.

## 8. Which DocAI article belongs to it?

[docai.hu/blog/prefix-cache-megvaltoztatja-a-valaszt](https://docai.hu/blog/prefix-cache-megvaltoztatja-a-valaszt)
(HU) / [docai.hu/en/blog/prefix-cache-changes-the-answer](https://docai.hu/en/blog/prefix-cache-changes-the-answer) (EN).
Upstream: a reproduction comment on vllm#54076 (with #53798 referenced), an independent
throughput data point on vllm#55122, and a negative/packaging note on vllm#56500.

## Layout

```text
code/      t201_partial_hit.py (clean/contaminated arms), blokkhatar_szonda.py (block-boundary probe),
           prefix_cache_szonda.py (cold/partial/full on an untouched prefix), qsa_memoria_timeline.py (8K→64K sweep)
results/   round3-A-* (preview build), round3-B-* (v0.29.0 build), C-pr-files.txt (files touched by each upstream PR)
docs/      Hungarian lab notes: summary, arm A, the isolation experiment, the PR compatibility gate, arm B
```

Host names and local paths in `results/` are replaced with `SPARK-DEV` / `WORKDIR` / `/home/USER`.
The corpus, harness and scorer live in the round-1 directory
([../2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/](../2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/)).

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu)*
