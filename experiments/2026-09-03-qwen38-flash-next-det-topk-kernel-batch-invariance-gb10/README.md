# Qwen3.8-Flash-Next NVFP4 on vLLM, round 2: the determinism is serial-only, and the deterministic top-k kernel (vllm#55122) removes its cost

**Date:** 2026-09-03 · **Type:** correctness / serving · **Hardware:** one DGX Spark (GB10, `sm_121a`, 121 GiB unified) ·
**Reproducibility:** R2 (code + the round-1 synthetic corpus + every run artefact; the engine build is a third-party image)

> Status: **measurement closed 2026-09-03; the full-suite score with the new kernel is being added
> as it lands** (see §5.6). The follow-up to
> [2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10](../2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/).

## 1. What was the measurement for?

Round 1 found that the recipe's greedy output was non-deterministic, traced it to the QSA indexer's
`persistent_topk` kernel, and fixed it with a Python-level exact `torch.topk`
(`VLLM_QSA_EXACT_TOPK=1`) at **74 % of the stock prefill throughput**. That fix has been in the
night-time serving slot since 2026-08-31.

Two things changed upstream in the meantime, and both target our build directly:

- **vllm#55122** — a deterministic `persistent_topk` CUDA kernel (radix select with index-ordered
  tie-breaking), shipped as a standalone build in
  [jschmied/qwen38-flash-next-gb10](https://github.com/jschmied/qwen38-flash-next-gb10)
  `patches/kernel-det/`, with an explicit "validators on another box" path.
- **vllm#54945 / PR #54948** — the FlashInfer CUTLASS NVFP4 MoE's fused finalize reduces expert
  outputs with atomics; identical requests get different logits. Our server log names exactly that
  backend (`Using 'FLASHINFER_CUTLASS' NvFp4 MoE backend`).

Round 1 also had two blind spots we only saw when reading the upstream notes: its probe used
`max_tokens = 1` (prefill only — the MoE effect lives in decode), and its isolation arms ran with
`--no-enable-prefix-caching`, while production runs with prefix caching on. **This experiment
measures the production configuration itself**, then A/B-tests the new kernel against our fix.

## 2. On what task and dataset?

The round-1 synthetic Hungarian KIE corpus (`D1–D7`, `items.jsonl`; it ships in the round-1
directory and is not duplicated here). Probes use four to six items chosen for prompt length and
for their round-1 behaviour (three that were unstable with the stock kernel, one that was stable):

| item | prompt tokens | round 1 |
|---|---:|---|
| T3-01 | 3 169 | unstable |
| T2-01 | 3 227 | stable (control) — shares the `D2.md` document with T3-01, see §5.2 |
| T6-02 | 6 082 | unstable |
| T10-05 | 24 416 | unstable |
| T1-01, T8-01 | 5 000 / 4 800 | unstable / stable (256-token round only) |

The full-suite score (§5.6) uses the same 50-item main suite × 3 runs as round 1.

## 3. Which models and configurations were compared?

One checkpoint (`RadixArk/Qwen3.8-Flash-Next-NVFP4`, snapshot `7b71922…`), one engine
(vLLM `0.1.dev20073+g8e685d198`, `vllm/vllm-openai:qwen38-flash-next@sha256:fc120ece…`,
FlashInfer 0.6.17, driver 580.173.02), **the production launch flags of the night slot**
(`--max-model-len 262144 --max-num-seqs 4 --gpu-memory-utilization 0.78 --enable-prefix-caching
--enable-chunked-prefill --max-num-batched-tokens 8192`, `cudagraph_mode=PIECEWISE` with 12
splitting ops, MTP=2, `--kv-cache-dtype auto`, `--no-enable-flashinfer-autotune`). Verified from
the startup log: `enable_prefix_caching: True`, `Mamba cache mode is set to 'align'`,
`FLASHINFER_CUTLASS` NvFp4 MoE.

| Arm | QSA block selection | Image | Env |
|---|---|---|---|
| **A** (production) | Python `torch.topk` (blazux `patch_qsa_exact_topk.py`, mode 1) | `qwen38-flash-dgx-up:e655b7d` (blazux `e655b7d` on the official image) | `VLLM_QSA_EXACT_TOPK=1` |
| **B** (control) | stock `persistent_topk` | same image + `qsadet_patch.py` applied (inert) | neither variable |
| **C** (candidate) | deterministic kernel `_C_det.persistent_topk` (vllm#55122) | same as B | `VLLM_QSA_EXACT_TOPK=0 VLLM_QSA_DET_TOPK=1 VLLM_QSA_DET_LIB=…/_C_det.so` |

The two patches compose: the blazux patch replaces the *call* (`topk_op(...)` → if/elif/else), the
jschmied patch replaces the *assignment* `topk_op = (...)`, so with `EXACT_TOPK=0` the `else`
branch runs and `topk_op` is already the deterministic kernel. Every arm printed its own activation
evidence and was checked in the log before measuring (`QSADET active: …` present in C, absent in
A and B) — the upstream post-mortem's rule, not ours.

The kernel was compiled **inside our image** (`build_det.py`, nvcc `sm_121a`, torch 2.13/cu130;
jschmied repo @ `0c5598782b33bbfc9acb46acd57b495ca0eb01b7`); the arm-C image was produced by
applying the patch in a throw-away container and `docker commit`. That is fine for measurement and
**not** a deployable recipe (decision record).

## 4. Which metrics?

- **Per-token logprob signature** ([code/logprob_szonda.py](code/logprob_szonda.py)): for every
  generated token, `sha256` of the top-20 `(token, logprob %.12g)` list; the run hash is the hash
  of the sequence. `N` identical requests are sent **strictly sequentially** (`Running: 1 reqs` in
  the server log throughout); the report separates the first (cold / cache-miss) request from the
  rest (cache-hit), because production runs with prefix caching on. Visible-text SHA is recorded
  next to it — "same text, different logits" is still a FAIL.
- **Batch invariance** ([code/parhuzamos_szonda.py](code/parhuzamos_szonda.py)): the same item as
  a serial reference, then 2 and 4 *identical* concurrent requests, then the item inside a *mixed*
  batch with three other prompt lengths; every hash compared with the serial reference. All prompts
  are warmed into the prefix cache first so that a difference is attributable to the batch, not to
  the cache path.
- **Prefill throughput**: `prompt_tokens / (cold-run wall time − median warm-run wall time)` on the
  48-token round, where the generated token count is identical across arms. Warm runs are
  cache hits, so the difference is the prefill. The measurement sequence (smoke request, item order,
  repetition count) is byte-identical across arms — the cache state would otherwise shift the cold
  numbers.
- **Kernel correctness**: the PR author's `test_det.py` (bit-identity over 20 calls, equality with an
  exact reference, tie-heavy and adversarial pivot populations) run against the `.so` built here.
- **Suite points**: the round-1 harness, main suite 50 × 3, majority output scored (§5.6).

## 5. What was the result?

### 5.1 Arm A (production): reproducible token-by-token, as long as the cache state is the same

| round | mode | max_tokens | items | reps | result |
|---|---|---:|---|---:|---|
| P1 | thinking off | 48 | T3-01, T6-02, T10-05, T2-01 | 10 | **3/4 PASS** (T2-01 fails, §5.2) |
| P2 | thinking off | 256 | T3-01, T2-01, T1-01, T8-01 | 8 | **4/4 PASS** |
| P3 | **thinking on** | 512 | T3-01, T2-01, T6-02, T10-05 | 5 | **4/4 PASS** (incl. the 24 416-token prompt) |

**0 differences across 80 warm runs.** The MoE fused-finalize pattern reported in vllm#54945
(3 distinct signatures out of 3 identical requests, from token 2) did not appear once. The upstream
reproduction uses a 55-token prompt, `--enforce-eager`, no speculation, no prefix cache; its own
notes locate the divergence on the MoE's small-M path. Our production shapes (3–24 k-token prefills
in 8 192-token chunks, MTP=2 verify shapes) evidently do not exercise it. This does not refute
#54945; it says the defect is shape-dependent and PR #54948 is not urgent for this deployment.

### 5.2 The one failure: a partial prefix-cache hit is not a full one

T2-01's **first** request differed from requests 2–10 (which were identical to each other) in
**all 46 tokens'** top-20 lists, while the selected tokens — the visible answer — were the same.
Cause, measured: T2-01 and T3-01 (the first item of the round) share the `D2.md` document; their
prompts are identical for **6 982 characters (≈ 2 182 tokens, 68 % of T2-01)**. T2-01's "cold" request
therefore got a *partial* hit (one full 1 616-token block from T3-01), requests 2–10 a *full* hit —
two cache paths, two logit vectors. In P2, where T2-01 ran in a different cache state, it passed.

This is the align-resume family targeted upstream by vllm#53798 / #54076 and reported
independently on the same model and GPU in vllm#54173. It is **not** a top-k effect: it reproduced
identically on arms A and C (§5.4), with the same item and the same pattern. In production, a
shared system prompt, several questions on the same document and multi-turn chat produce partial
hits continuously.

### 5.3 Batch invariance: none — and two identical concurrent requests differ from each other

[results/f2c-koteg.json](results/f2c-koteg.json), target T3-01, 128 tokens, everything pre-warmed:

| arrangement | distinct hashes | equal to the serial reference |
|---|---:|---|
| serial reference, 3× | 1 | — |
| 2 identical concurrent requests, 3 rounds | 2 | **0 / 6** |
| 4 identical concurrent requests, 3 rounds | 3 | **0 / 12** |
| mixed batch (target + T6-02 + T10-05 + T1-01), 3 rounds | 1 | **0 / 3** |

The effect is not noise: a given batch shape is deterministic (the mixed batch returned the same
hash three times), just different from the serial one. Two byte-identical requests in the same
batch receive different logits, and which one gets which changes with arrival order. The visible
text was identical in all 21 runs. vLLM does not promise batch invariance, and its official
`VLLM_BATCH_INVARIANT` path is closed on this model's GDN layers (vllm#42960).

**Consequence:** the exact top-k buys *serial* bit-determinism. The night slot serves cron jobs
and chat concurrently (`--max-num-seqs 4`), so bit-level reproducibility in production does not
exist and cannot. What the fix buys there is the *value-level* stability round 1 measured (13/50
items flipping, 5 of them in the extracted date or amount, with the stock kernel).

### 5.4 Arm C (deterministic kernel): same determinism, same failure, same pattern

`test_det.py` against the `.so` built in our image: **`FAILS: 0`** — and every row reports
`stock identical x3=False`, `stock set==ref=False`: the stock kernel does not reproduce itself on
this GB10 either, and the *selected set* differs from the exact reference. That is round 1's root
cause confirmed at kernel level, independently of our suite.

| round | A | C |
|---|---|---|
| 4 items × 10 × 48 tok, thinking off | 3/4 PASS | **3/4 PASS** — same item (T2-01), same partial-hit pattern |
| 4 items × 5 × 512 tok, thinking on | 4/4 PASS | **4/4 PASS** |

### 5.5 Arm B (stock kernel): the probe is sensitive, and the speed reference

**0/4 PASS — 10 distinct hashes out of 10 on every item, diverging at token 0.** This is the
negative control that makes the A/C PASS results meaningful, and it reproduces round 1's finding in
the production configuration (prefix cache on). The visible text was again identical in all 40 runs
at 48 tokens — text identity is not evidence.

Prefill throughput, byte-identical sequence on all three arms
([results/szonda-{A,B,C}-48tok.json](results/)):

| item | prompt tok | B stock | A exact `torch.topk` | **C det kernel** | A/B | **C/B** |
|---|---:|---:|---:|---:|---:|---:|
| T6-02 | 6 082 | 2 246 tok/s | 1 952 | **2 253** | 0.87 | **1.00** |
| T10-05 | 24 416 | 1 943 tok/s | 1 756 | **1 932** | 0.90 | **0.99** |
| T2-01 | 3 227 | 3 163 tok/s | 2 417 | **3 049** | 0.76 | **0.96** |
| ~~T3-01~~ | 3 169 | excluded: the smoke request had already warmed it (cold − warm = 153 ms) | | | | |

T2-01 was partially cached on every arm (§5.2), so its absolute numbers are inflated the same way on
all three; the two clean cells are T6-02 and T10-05. **The deterministic kernel runs at 96–100 % of
the stock kernel; our production fix at 76–90 %.** The PR's own estimate is ≈ +1.8 % TTFT. Round 1's
"1.35× slower" was the price of a Python-level `torch.topk`, not of determinism. Pure decode is
unchanged (512-token thinking runs: T3-01 16 805–17 125 ms on A vs 17 074 ms on C).

**The two deterministic arms produce different text.** T2-01's reasoning is 273 tokens on A and 294
on C; T10-05's 376 vs 501. Two different exact block selections choose different sets under ties,
hence different logits. The switch is therefore not quality-neutral by construction, and the suite
score does not carry over.

### 5.6 Full-suite score with the deterministic kernel (in progress)

Main suite 50 × 3 with arm C, same harness as round 1. References on this corpus: stock kernel
97.00/100 (13/50 unstable), round-1 mode-3 image 98.00/100 (0/50), the production upstream image
96.00/100 (1 run). *Result to be added to this section and to the eval card when the run completes.*

## 6. What product decision followed?

See [decision-record.md](decision-record.md). Short version: the production configuration stays as
it is; the deterministic kernel is the **candidate** to replace `VLLM_QSA_EXACT_TOPK=1`, conditional
on the suite score, on three independent server starts, and on the recipe being vendored into the
serving repository (Dockerfile step, pinned source commit, `.so` built into the image — no
`docker commit`). Nothing in this repository is to be described as "deterministic in production"
any more; the claim is "deterministic for sequential requests in the same cache state".

## 7. What are the limits of the measurement?

- **One server start per arm.** The upstream post-mortem's "no call from three runs" rule is not met
  here; JIT/autotune/allocator differences between starts are unmeasured.
- **Top-20 logprobs only**, as served; logits outside the top 20 may differ unseen. Reported
  logprobs are server-quantised, so distinct-vector counts are conservative.
- **At most 512 generated tokens** in the probes; production KIE runs with a 16 384-token budget.
- **The cold path's own reproducibility is open**: two genuinely cold runs of one prompt need a
  server restart or prefix caching off, neither of which was done.
- The prefill figure is `cold − warm` on one cold request per item; cross-session CV is not
  established. Same-arm warm-run spread was 1–3 %.
- The "MoE does not trigger" statement rests on 0 divergences in 80 warm runs on four prompts; it is
  a bound on our shapes, not a general statement about the kernel.
- The suite score for arm C (§5.6) was not available when this README was written.

## 8. Which DocAI article belongs to it?

None yet. The round-1 article
([docai.hu/blog/qwen38-flash-next-nondeterministic-vllm-kernel](https://docai.hu/en/blog/qwen38-flash-next-nondeterministic-vllm-kernel))
states the determinism result more broadly than this round supports; the correction (serial-only,
cache-state-dependent) and the cost-free kernel are a short follow-up once §5.6 and the three-start
rule are done. The immediate outputs are a validation comment on vllm#55122 (another box, the
official image, `FAILS: 0`, the throughput table) and a shape-dependence data point on vllm#54945.

## Layout

```text
code/      logprob_szonda.py (per-token logprob probe, cold/warm split), parhuzamos_szonda.py (batch-invariance probe)
results/   szonda-A-{48tok,256tok,thinking-512tok}.json, szonda-B-48tok.json, szonda-C-{48tok,thinking-512tok}.json, f2c-koteg.json
docs/      Hungarian lab notes: phase 1 (production-config probe + batch invariance), phase 3 (kernel A/B/C), and the input runbook
```

The corpus, the harness and the scorer are in the round-1 directory
([../2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/](../2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/)).
The kernel source is upstream (vllm#55122; standalone build in the jschmied repository at the pinned
commit) and is not vendored here.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu)*
