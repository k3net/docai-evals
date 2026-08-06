# Speculative decoding A/B on the production model — where MTP wins and where it costs

**Date:** 2026-04-18 · **Type:** inference performance · **Reproducibility:** R2 ·
**Article (HU):** [A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10)

## 1. What was the measurement for?

To decide whether multi-token prediction (MTP) should be enabled on the production model. The
expectation going in was a modest single-stream speed-up and a possible penalty under load — the
usual speculative-decoding trade.

The result was the opposite shape, which is why it got an article.

## 2. On what task and dataset?

Four synthetic workloads through the engine's own `bench serve` harness. No customer data — fixed
prompt and output lengths, so the numbers are portable and the runs are repeatable.

| Test | Input / output tokens | Concurrency | Prompts | Repeats | What it represents |
|---|---|---|---|---|---|
| **A — single decode** | 512 / 512 | 1 | 20 | 1 | one user, streaming |
| **B — prefill-bound** | 8,192 / 256 | 4 | 20 | 2 seeds | long prompt, short answer — document extraction |
| **C — concurrent contention** | 2,048 / 512 | 16 | 64 | 2 seeds | saturation stress test |
| **D — chat profile** | mixed | 2 | 16 | 2 seeds | realistic interactive load |

Three warm-up requests before each measurement; `--ignore-eos` so output lengths are exact; fixed
seeds; every run recorded `errors = 0`.

## 3. Which configurations?

One variable: speculative decoding off vs on. Everything else identical — same container, same
model, same flags, same machine, back-to-back.

| Arm | Model | Speculative decoding |
|---|---|---|
| `phase8` | Qwen3.6-35B-A3B-FP8 | off |
| `phase8-mtp` | Qwen3.6-35B-A3B-FP8 | MTP, `num_speculative_tokens = 2` |

Serving: FlashInfer attention, Triton FP8 MoE backend, 131,072 context, FP8 KV cache, prefix
caching on. Each run captured its own `vllm-config.txt`, `lib-versions.txt`, `vllm-version.txt` and
image digest — the environment is pinned to the result, not remembered.

## 4. Which metrics?

Output throughput (tok/s), mean TTFT, mean TPOT, and speculative acceptance read from the engine's
metrics endpoint. Where a test has two seeds, the reported figure is their mean.

## 5. What was the result?

| Test | Off | MTP=2 | Δ throughput | Δ mean TTFT | Δ mean TPOT |
|---|---|---|---|---|---|
| **A — single decode** | 50.51 tok/s | 54.92 | **+8.7 %** | +8.3 % | −8.4 % |
| **B — prefill-bound** | 73.98 | 68.68 | **−7.2 %** | −39.0 % | **+30.7 %** |
| **C — concurrent (16)** | 214.28 | 266.24 | **+24.2 %** | **−56.7 %** | −17.1 % |
| **D — chat profile** | 73.88 | 77.60 | **+5.0 %** | −30.1 % | −3.4 % |

### The surprise: the biggest win is under contention

The textbook expectation is that speculative decoding helps a lonely stream and hurts a saturated
GPU — the draft pass competes with real work. Here it is backwards: **+8.7 % single-stream but
+24.2 % at 16 concurrent, with time-to-first-token more than halved.**

The mechanism is scheduling, not arithmetic. Each accepted draft token is a token that does not
need its own scheduler slot, so at saturation the queue drains faster; requests start sooner
(TTFT −56.7 %) and the whole batch finishes earlier. On a single stream there is no queue to drain,
so only the raw decode gain shows.

### Where it genuinely costs: prefill-bound work

The one negative column is the workload that matters most for document extraction: long prompt,
short answer. Throughput −7.2 % and **TPOT +30.7 %**, because the GPU is busy with prefill and the
draft pass takes compute away from it rather than filling idle capacity.

TTFT still improves 39 % there — the first token arrives sooner and then each subsequent one takes
longer. Which of those a user notices depends entirely on what they are waiting for.

### Acceptance, from the engine's own counters

```text
drafts:              41,568
draft tokens:        83,136   (2 per draft)
accepted tokens:     60,298
```

| Metric | Value |
|---|---|
| Overall acceptance | **72.53 %** |
| Position 0 (first draft token) | **81.57 %** |
| Position 1 (second draft token) | 63.48 % |
| Accepted tokens per draft | 1.451 |

The position split is the useful part: the first drafted token is accepted four times out of five,
the second only two times out of three. A single averaged acceptance number hides that, and it is
exactly the shape that decides whether a longer draft would pay — here, a third token would be
starting from below 63 % and falling.

## 6. What product decision followed?

**MTP on, draft length 2**, on the production model. See [decision-record.md](decision-record.md).

The draft length question was settled separately, in a later sweep that tried 3 and found it loses
3.6 % aggregate on a mixed profile:
[qwen36-fp8-vllm-flag-sweep](../2026-07-01-qwen36-fp8-vllm-flag-sweep/).

## 7. Limits of this measurement

- **`n=1` for test A**, `n=2` for the rest. The four tests agree in direction with the mechanism
  described above, which is why we trust the shape; individual percentages carry a run-to-run
  uncertainty we did not quantify at the time.
- **The concurrency-16 scenario is a stress test, not our operating point.** Production peaks at 3
  concurrent requests ([hardware.md](../../docs/hardware.md#production-load-profile)). The +24.2 %
  headline describes a load we do not run — the decision-relevant rows are A and D.
- **Synthetic workloads.** Fixed-length random prompts, not real documents. Acceptance on real
  Hungarian invoice extraction is *higher* (strict JSON drafts extremely well), which later
  measurements confirmed — so this acceptance figure is conservative for our actual mix.
- **One engine build, one day.** Speculative-decoding behaviour is engine-version sensitive.
- **`--ignore-eos`** forces exact output lengths, which makes runs comparable but slightly
  unrealistic: real responses stop when the model decides to.

## 8. The article

[A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10) —
*„avagy hogyan lett a »sima A/B benchmark« a mai legmeglepőbb eredménye"*

The cross-model synthesis — how this compares to 4-bit and to the 122B model — is
[mtp-speculative-decoding-gb10](../2026-07-23-mtp-speculative-decoding-gb10/).

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
