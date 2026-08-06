# Decision record — Marlin for 4-bit, Triton for FP8

**Date:** 2026-07-23 · **Status:** in force · **Experiment:**
[moe-backend-selection-gb10](README.md)

## Decision

| Quantisation | Backend | Basis |
|---|---|---|
| NVFP4 (4-bit) MoE on GB10 | **Marlin** | 2.0–3.3× faster than the publisher-recommended alternative at every concurrency level, and stable |
| Block-scaled FP8 MoE on GB10 | **Triton** | The best of only two backends that load at all; the alternative is 9 % slower |
| Speculative draft head (any) | **Triton** | Its MoE is unquantised — no quantised backend can load it |

The kernel choice is a property of the **checkpoint format**, not of the machine. Marlin is first
for 4-bit and second for FP8 on the same GPU.

## Standing rules that follow

1. **Read the backend from the boot log, never from the flag.** Engines fall back silently. Every
   performance result in this repository records the kernel that actually loaded.
2. **A vendor recommendation is a hypothesis.** Publisher guidance is written for the hardware the
   publisher tested. Ours is a 128 GB unified-memory part at concurrency 1–3; most published
   guidance targets data-centre parts at concurrency 128. Test before adopting.
3. **Measure the incumbent's optimum before claiming a candidate beats it.** The FP8 backend sweep
   existed solely so the headline could not be "we beat a badly configured baseline". It cost a
   morning and it made the result defensible. (It also could have gone the other way — that was
   the point of running it.)
4. **Instability is a rejection reason on its own.** A backend with 2× run-to-run variance is
   unshippable regardless of its median.

## Scope — what this decision does not do

It settles speed only. The 4-bit checkpoints won the backend argument and still did not ship,
because they failed the [counterparty-role gate](../2026-07-16-invoice-counterparty-role/).
Winning on throughput is necessary and nowhere near sufficient.

## What would reopen it

- **A newer engine build.** Four of six FP8 backends currently fail to load on `sm_121a`; each
  fix is a candidate re-measurement. In particular, if the auto-selected default becomes usable
  here, the `VLLM_USE_DEEP_GEMM=0` workaround should be revisited.
- **Native FP4 compute on this architecture.** Marlin is a weight-only kernel by design; if the
  platform gains FP4 tensor-core dispatch, the whole matrix changes.
- **A different concurrency profile.** Every conclusion is at c ≤ 16 on a bandwidth-bound part. A
  batch-processing workload at high concurrency deserves its own sweep.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) ·
[Article (HU): Kövesd a gyártói doksit, és háromszor lassabb leszel](https://docai.hu/blog/backend-valasztas-gb10)*
