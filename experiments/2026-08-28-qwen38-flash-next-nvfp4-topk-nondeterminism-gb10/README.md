# Qwen3.8-Flash-Next NVFP4 on vLLM: greedy decoding was non-deterministic — root cause in the QSA top-k kernel

**Date:** 2026-08-28 · **Type:** correctness / serving · **Hardware:** one DGX Spark (GB10, `sm_121a`, 121 GiB unified) ·
**Reproducibility:** R2 (code + synthetic corpus + every run artefact; the engine build is a third-party image)

> Status: **closed 2026-08-28 21:20** — root cause confirmed and fixed (mode-3 top-k), validated on all three suites; a separate greedy-thinking repetition loop identified and shown to be independent of speculative decoding (§5.5) —
> see [decision-record.md](decision-record.md) for what is provisional.

## 1. What was the measurement for?

We wanted to know whether **Qwen3.8-Flash-Next** (177 B total / 6 B active, 51 B of it an n-gram
"PLE" table) is a candidate to replace our night-time 122B model for Hungarian key information
extraction (KIE), and whether the **NVFP4 checkpoint served by vLLM with the PLE table `mmap`-ed
from NVMe** ([blazux/qwen3.8-Flash-DGX](https://github.com/blazux/qwen3.8-Flash-DGX), commit `82ed48d`)
is better than the only other single-GB10 option, an IQ4_XS GGUF on llama.cpp.

The measurement that answers this is a 65-item Hungarian extraction/reasoning suite. **This
experiment is about what the suite found on the way:** the NVFP4/vLLM configuration returned
*different answers to identical greedy requests*, and the search for the reason is the main line
here. The four-way model comparison is context, not the headline.

## 2. On what task and dataset?

A synthetic Hungarian corpus written for this evaluation (fictional companies, contracts, invoices,
a 217 k-token document set) — it ships in [dataset/](dataset/) together with the ground truth:

| Suite | Items | Points | What it exercises |
|---|---:|---:|---|
| main (T1–T10) | 50 | 100 | strict-JSON extraction: dates, amounts, cross-references, "not decidable", enumerations |
| hard (T11–T20) | 10 | 100 | multi-step reasoning: amendment chains, counterfactuals, banking-day vs calendar-day deadlines |
| long context (T21–T25) | 5 | 100 | needles, rule overrides and a full-scan aggregation over **217 081 tokens** |

Scoring is deterministic ([code/pontozo.py](code/pontozo.py)); reference normalisation (`11.4` ≡
`11.4. pont`) and enumerated value sets were frozen **before** the second model was scored. Two
points (an LLM-judge field) are unreachable for every arm; the reachable maximum is 298/300.

Every item is sent **three times** with `temperature = 0`, `top_p = 1`, a 16 384-token answer budget,
and the **majority output** is scored ([code/harness.py](code/harness.py)). The harness stores the
raw content, the reasoning content and a SHA of each run — which is what made the finding visible.

## 3. Which models and configurations were compared?

| Label | Model | Engine | Notes |
|---|---|---|---|
| `flash-next` | Qwen3.8-Flash-Next, Unsloth UD-IQ4_XS GGUF (4.25 bpw) | llama.cpp, `-c 262144 -fa on -np 1` | the pre-existing single-GB10 path |
| `flash-nvfp4` | Qwen3.8-Flash-Next, RadixArk NVFP4 | vLLM `0.1.dev20073+g8e685d198` (blazux image on `vllm/vllm-openai:qwen38-flash-next@sha256:fc120ece…`), `VLLM_PLE_MMAP=1`, MTP=2, `cudagraph_mode=PIECEWISE` (12 splitting ops), `CTX=262144`, `max-num-seqs 2` | **the subject of this experiment** |
| `qwen36` | Qwen3.6-35B-A3B-FP8 (production) | vLLM production image, MTP=2, `reasoning-parser qwen3` | the incumbent; *different vLLM build* (limitation) |
| `qwen35-122b` | Qwen3.5-122B-NVFP4 | vLLM, night node | the model Flash-Next would replace |

Driver 580.173.02, kernel 6.17.0-1029-nvidia. Selected backends on the NVFP4 server (from the startup
log): NvFp4 MoE `FLASHINFER_CUTLASS`, attention `QWEN38_FLASH_NEXT_EXP_QSA_STATE`, FlashInfer sampler.

## 4. Which metrics?

- **Points** per suite (majority output of 3 runs).
- **Unstable items**: items whose 3 (or 5) greedy runs did not produce byte-identical content.
- **Score-changing instability**: each run scored *separately* ([code/szoras.py](code/szoras.py)) —
  the majority vote hides the operational risk, and can itself pick the wrong answer.
- **Prefill probe** ([code/prefill_szonda.py](code/prefill_szonda.py)): identical prompt, `max_tokens = 1`,
  `top_logprobs = 20`, 10 repetitions — number of distinct top-20 logprob vectors, first-token
  identity, top-2 gap. This isolates the prefill from decoding.
- Prefill and decode throughput from the same requests (wall-clock; identical formula for both engines).

## 5. What was the result?

### 5.1 The symptom

| Configuration | unstable items (main suite, 50 × 3) |
|---|---:|
| Flash-Next IQ4_XS · llama.cpp | 0 |
| 35B FP8 · vLLM · MTP=2 · thinking | 0 |
| 122B NVFP4 · vLLM · thinking | 0 |
| **Flash-Next NVFP4 · vLLM + mmap-PLE · MTP=2** | **13** — in **5** of them the extracted date or amount changes between runs |

Examples: deadline `2026-11-10` ↔ `2026-11-05`; amount `6 300 000` ↔ `5 940 000`; on one item the
majority of three runs was the *wrong* answer. Two requests spent the full 16 384-token budget
reasoning and returned empty content.

Measurement artefacts were excluded first (§2 of [docs/protocol-hu.md](docs/protocol-hu.md)):
`temperature 0.0` is explicit in the payload, the prompt is built once per item, the server log
shows `Running: 1 reqs` at most (no concurrent client), every item has exactly 3 runs, and the two
control models thought at least as long as the Flash and were run with the same harness.

### 5.2 Where it diverges

The stored reasoning content showed the divergence at the **first token**: the model starts its
reasoning in Hungarian (`A feladat…`) or in English (`We need…`) from one run to the next. The first
token is the output of the **prefill**. A deterministic prefill resolves even a 10⁻⁶ tie the same
way every time, so the prefill logits themselves were changing.

### 5.3 Isolation — one variable per arm, the 13 unstable items × 5 runs

| Arm | unstable | score-changing | decode tok/s | conclusion |
|---|---:|---:|---:|---|
| baseline (MTP=2, PIECEWISE, `persistent_topk`) | 13/50 (×3) | 5 | 26.4 | — |
| `mtp0` — speculative decoding off | 11/13 | 4 | 16.1 | not the root cause (but the empty 16 k run-away only occurs with MTP: 1/150 vs 0/65) |
| `cgnone` — `cudagraph_mode=NONE` | 13/13 | 5 | 27.4 | not the root cause |
| **`topk` — exact, canonical top-k instead of `persistent_topk`** (MTP=2 and PIECEWISE unchanged) | **0/13** | **0** | 27.3 | **root cause** |

The QSA sparse-attention indexer selects its attended blocks with a top-k kernel. On GB10
(capability family 12x) the code path is `persistent_topk`, whose output slots are assigned with
`atomicAdd` — the selected **set** is scheduling-dependent, not only its order. Upstream has an open
correctness issue on the same kernel
([vllm-project/vllm#51782](https://github.com/vllm-project/vllm/issues/51782)).

### 5.4 The prefill probe — the decisive evidence

Identical prompt, `max_tokens = 1`, 10 repetitions, 6 items (4 unstable + 2 that looked stable in
the suite):

| | `persistent_topk` | mode 1: full stable sort | mode 2: `persistent_topk` + canonical re-ordering | **mode 3: `torch.topk` + canonical ordering** |
|---|---|---|---|---|
| items with 10/10 byte-identical top-20 logprobs | **0 / 6** (every item: 10 distinct vectors — including the two "stable" ones) | 6 / 6 | 3 / 6 (2–10 variants remain) | **6 / 6** |
| first token | flips (A / We / The) | fixed | flips on 1 item | fixed |
| prefill, 3 k / 6 k / 24 k-token prompt (tok/s) | 2 180 / 2 360 / 2 381 | 792 / 820 / 822 | — | **1 645 / 1 760 / 1 769** |
| slowdown vs `persistent_topk` | 1× | 2.9× | ~0 | **1.35×** |

Mode 2 failing is informative: re-ordering the kernel's output is not enough, so the kernel changes
the selected *set*, consistent with #51782. Mode 3 (radix-select `torch.topk`, then two stable sorts
to canonicalise ties) gives logits identical to the exact sort at 74 % of the original prefill
throughput. The non-determinism was **universal** — the suite's 13/50 was only the part that
happened to land on a near-tie.

The patch is a drop-in replacement of one call in the installed `qsa.py`, switched by
`VLLM_QSA_EXACT_TOPK=1|2|3` ([patch/](patch/)); the image is `FROM` the original plus one `COPY`.

### 5.5 Validation of the fix on the full suites (in progress)

| Suite | stock `persistent_topk` | **mode 3** |
|---|---:|---:|
| main (50 × 3) | 97.00 · 13/50 unstable · 1 truncated | **98.00 · 0/50 · 0** — the only changed score is T3-05 (1 → 2), where the stock majority had been the wrong date |
| hard (10 × 3) | 100.00 | **90.00 · 0/10 unstable** — T14-01 hits the 16 384-token budget with empty content on **3/3 identical runs** |
| language challenge (10 × 1) | 1 empty (item 2) | 1 empty (item 9) |
| long (5 × 1) | 100.00 | **100.00** (5/5 items 20/20; the 217 k-token full-scan item in 449 s) |

**The empty run-away is a separate failure mode, and the fix made it reproducible rather than removing it.**
T14-01's stored reasoning (41 835 characters) ends in the same ~180-character paragraph repeated 22 times — the model
loops on the output format of one field and never closes its reasoning; only 7 % of the last 4 000 characters are
unique; all three runs share one SHA. This is the known greedy-plus-thinking repetition loop (the model vendor
recommends against greedy decoding in thinking mode). With the stock kernel the prefill noise occasionally kicked the
model out of the loop, which is why it looked random (1/150 on the main suite); with a deterministic prefill it
happens every time on the same input. A deterministic failure can be detected (repetition ratio in the reasoning)
and handled (retry above temperature 0, presence penalty, or an unambiguous field description); the random one
could not. A post-test (mode 3 with speculative decoding off, T14-01 + item 9, 3 runs each) is queued to see whether
MTP contributes. A first attempt ran on the *same* server by mistake and is kept as a replication: all 10 challenge
answers and the T14-01 reasoning stream were byte-identical to the validation run across two sessions
(`results/*-samesession.json`).

Total with mode 3: **288 / 300** (98 + 90 + 100) against 297 with the stock kernel — the whole difference is the
one deterministic loop item.

**Post-test: is speculative decoding greedy-equivalent on this model?** Mode 3 with MTP off, same suites:

| | MTP=2 | MTP=0 | outputs differ | scores differ |
|---|---:|---:|---:|---|
| main (50 × 3) | **98.00** | 97.00 | **9 / 50** | 1 (T3-01: 2 → 1, MTP=0 worse) |
| hard (10 × 3) | 90.00 | **100.00** | 1 / 10 | 1 (T14-01: the loop does not occur without MTP) |
| language challenge (10 × 1) | 1 loop (item 9) | 1 loop (**item 7**) | 9 / 10 | — |
| decode tok/s | **24.9** | 14.8 | | |

So MTP is **not** greedy-equivalent here (the trajectory diverges on ~18 % of items — on T14-01 at the 5th
reasoning token), but the effect on quality is noise-level and non-directional, and the repetition loop simply moves
to a different input when MTP is off (~1 in 10 hard inputs either way). The loop is a property of greedy thinking on
this model, not of speculation. Both runs were byte-deterministic (0 unstable, 0 truncated).

### 5.6 Context: the four-way comparison (side line)

Same 65 items, same scorer, same sampling for all four:

| Suite | Flash IQ4_XS | **Flash NVFP4** (with `persistent_topk`) | 35B FP8 | 122B NVFP4 |
|---|---:|---:|---:|---:|
| main | **98.00** | 97.00 | 96.00 | 97.00 |
| hard | 91.33 | **100.00** | 98.00 | 98.00 |
| long (217 k) | 100.00 | 100.00 | 100.00 | 80.00 |
| total / 300 | 289.33 | **297.00** | 294.00 | 275.00 |

Two things the side line settles: the IQ4_XS's single hard failure (a counterfactual over an
amendment chain, 3.33/10) is **quantisation damage** — NVFP4 scores 10/10 on it three times
identically; and the 217 k-token prompt takes 157 s on vLLM against 1 121 s on llama.cpp. Only four
of 65 items discriminate between the four systems at all, and the NVFP4 column above was produced
*with* the non-deterministic kernel — which is why the fix is being re-validated on the full suite.

## 6. What product decision followed?

See [decision-record.md](decision-record.md). Short version: the NVFP4/vLLM path is **not** an
extraction engine with `persistent_topk` (one document in ten returns a different amount or date
on re-run, and majority voting can lock in the wrong one); with the mode-3 top-k it is
deterministic, keeps MTP, and loses 26 % of prefill throughput. The production model stays the
35B FP8; the recipe becomes a candidate as mode 3 + MTP=2 + PIECEWISE **plus a reasoning-loop guard**
(repetition ratio on the reasoning stream → retry above temperature 0), because the loop exists with and without
speculation. Turning MTP off is not a mitigation: it costs 40 % of decode and moves the loop to another input.

## 7. What are the limits of the measurement?

- **The 35B control is a different vLLM build** (production image vs the third-party Flash image).
  "Same engine, same MTP, 0/50" is therefore approximate; the within-build attribution rests on
  the isolation arms and the probe, not on the control.
- **The only single-variable control that would separate "quantisation" from "kernel" — the
  FP8 Flash-Next on the same build — does not fit on one Spark** (113.7 GiB of non-PLE weights against a
  112.2 GiB budget, PLE already `mmap`-ed). The claim is about this kernel on this hardware; it is
  not a claim about NVFP4 in general.
- The probe measures 6 items × 10 repetitions; the isolation arms 13 items × 5. The full-suite
  re-run with the fix (50 × 3 + 10 × 3 + 5 × 1) is in progress and not yet in this directory.
- `n = 1` server session per arm; run-to-run prefill throughput varied by < 3 %, but no CV was
  established across sessions.
- Reported logprobs are quantised to 0.125 nat by the server; the "10 distinct vectors" count is
  therefore conservative (differences smaller than that would be invisible), and the top-2 gaps are coarse.
- The corpus is synthetic and small; the four-way ordering (297 / 294 / 289 / 275) rests on four
  discriminating items and should not be read as a ranking.
- The first NVFP4 run was scored 77/100 because `CTX=32768` rejected every request over 32 k
  tokens with HTTP 400 — an artefact we caught by its signature (`no answer` on all runs of ten
  items) and re-ran at `CTX=262144`. The 97.00 is the corrected number.

## 8. Which DocAI article belongs to it?

*(in preparation — the article's main line is §5.2–5.4; the model comparison is a side note.)*

## Layout

```text
code/      harness, deterministic scorer, per-run scorer, prefill probe, corpus/item generators, report generators
dataset/   D1–D7 synthetic Hungarian documents + items.jsonl / items-nehez.jsonl / items-hosszu.jsonl (ground truth)
results/   every run artefact as JSON (main/hard/long × 4 systems; isolation arms; probes) + generated HU reports
patch/     qsa_exact_topk.patch (the three top-k modes), patch script, Dockerfile, arm runner, probe runner
docs/      the Hungarian protocol (timeline, self-check, all tables), the literature review (sources verified 2026-08-28), the research report
```

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu)*
