# Which MoE kernel backend wins on GB10 — and why the vendor recommendation lost

**Date:** 2026-07-23 · **Type:** inference performance · **Reproducibility:** R3 ·
**Article (HU):** [Kövesd a gyártói doksit, és háromszor lassabb leszel](https://docai.hu/blog/backend-valasztas-gb10)

## 1. What was the measurement for?

Two credible sources gave opposite advice for the same hardware. The publisher of one 4-bit
checkpoint states plainly that you *must* use their recommended FlashInfer kernel or suffer 2×
slower inference. The GPU vendor's own path is Marlin. Both claims are about mixture-of-experts
serving; only one can be right on our machine.

Secondary question, and the one that protects the headline: what is the *incumbent* FP8 model's
best backend? Comparing a tuned candidate against an untuned baseline is how benchmarks lie.

## 2. On what task and dataset?

[performance](../../performance/) workloads. Single-stream and concurrent (c=8, 60 s) on DGX Spark
GB10 (`sm_121a`), one engine instance per measurement, every run verified error-free and the
loaded backend read from the boot log rather than assumed from the flag.

## 3. Which configurations?

**4-bit candidates:** the publisher-recommended FlashInfer MoE kernel vs Marlin, on the same
checkpoints, with and without speculative decoding.

**FP8 incumbent:** all five selectable MoE backends plus the current default, speculative decoding
at draft 2, with the draft head pinned to Triton (its MoE is unquantised, so no quantised backend
can load it).

## 4. Which metrics?

Aggregate throughput at concurrency 8 (primary), single-stream decode, and — added after the first
sweep produced implausible numbers — **run-to-run variance**.

## 5. What was the result?

### The recommendation is backwards on this hardware

Most aggressive 4-bit checkpoint, concurrent throughput at c=8:

| Backend | tok/s |
|---|---|
| Publisher-recommended FlashInfer | **84.8** ⚠️ |
| Marlin | **282.4** |

**Marlin is 3.3× faster.** Reproduced twice (84.85 / 84.89) — not an artefact.

The recommendation is not wrong in general; it is wrong *here*. It was written for a data-centre
part with far more streaming multiprocessors and far more bandwidth, at concurrency 128. On a
273 GB/s unified-memory GB10 at concurrency 8, it does not transfer.

### There is no crossover point

We expected FlashInfer to win single-stream and lose under load. It does not win anywhere:

| Concurrency | FlashInfer | Marlin | Marlin advantage |
|---|---|---|---|
| 1 | 35.3 | 70.6 | 2.0× |
| 2 | 53.3 | 114.1 | 2.1× |
| 4 | 67.8 | 178.8 | 2.6× |
| 8 | 86.2 | 283.0 | **3.3×** |
| 16 | 149.7 | 383.9 | 2.6× |

An earlier apparent single-stream win for FlashInfer (73.7 tok/s) came from a per-token decode
measurement; on sustained throughput at c=1 Marlin is already 2× ahead.

### The tidy explanation was also wrong

Our hypothesis was a FlashInfer autotuner cliff — falling out of a tuning bucket under load.
Grepping both backends' logs for every cliff and fallback marker: **zero hits**. JIT latency
warnings were identical on both (5 each, from shared kernels).

There is no cliff. The kernel is simply slower on this architecture, and we published that instead
of the better story.

### And it is unstable

FlashInfer showed roughly **2× run-to-run variance** — 44 vs 86 tok/s at c=8 across two clean
sweeps — while Marlin stayed within a few percent (276 vs 283). An unpredictable backend is
unshippable even at a good median. Two full sweeps were needed to establish this, which is itself
the finding.

### The incumbent's backend sweep — the control that protects the headline

Before claiming a 4-bit candidate beat FP8 on throughput, we gave FP8 its own sweep. Five
selectable backends plus the default:

| Backend | Concurrent uniform | Concurrent mixed | Status |
|---|---|---|---|
| **Triton** (current default) | **256.1** | 271.2 | ✅ best working |
| Marlin | 232.0 | 232.6 | ✅ works, −9 % |
| CUTLASS | — | — | ❌ "disabled for this configuration" |
| FlashInfer CUTLASS | — | — | ❌ does not support the block-FP8 scheme |
| FlashInfer TRT-LLM | — | — | ❌ "kernel does not support current device" |
| `deep_gemm` (auto default on newer builds) | — | — | ❌ assert-crash on `sm_121a` |

Only two of six run at all. Triton — what production already used — is genuinely the optimum, not
a leftover. The 4-bit advantage therefore stands on a best-vs-best comparison: **+40 % aggregate,
+69 % single-stream extraction**, unchanged by the control sweep.

Note the asymmetry worth remembering: **Marlin is best for 4-bit and second-best for FP8.** Kernel
choice is per-quantisation, not per-machine.

## 6. What product decision followed?

**Marlin for 4-bit MoE on GB10; Triton stays for the FP8 production model.** See
[decision-record.md](decision-record.md).

Note that this experiment settles *speed*. The quality question was settled separately, and
against the 4-bit candidates —
[invoice-counterparty-role](../2026-07-16-invoice-counterparty-role/). Winning the backend
argument did not win the deployment.

## 7. Limits of this measurement

- **`n=1` per configuration** except where variance was explicitly investigated. The 3.3 × gap is
  far outside any plausible noise; the 9 % FP8 Marlin-vs-Triton difference is closer to it.
- **The concurrency sweep used a different `max-num-seqs`** (16) than the main matrix (8),
  deliberately, so those rows compare only with each other.
- **One engine version.** Kernel support on `sm_121a` is actively changing; every ❌ above is a
  statement about a specific build, not a permanent property.
- **The mixed concurrent workload is unstable** (CV 8.1 %) and is not load-bearing for any
  conclusion here.
- **Nothing here transfers to data-centre Blackwell.** That is the point of the experiment, not a
  caveat to it.

## 8. The article

[Kövesd a gyártói doksit, és háromszor lassabb leszel](https://docai.hu/blog/backend-valasztas-gb10) —
*„két gyártó, ugyanaz a gép, ellentétes ajánlás — 10 mérési pont, 0 keresztezés"*

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
