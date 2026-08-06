# Bringing a 122B MoE up on a single DGX Spark — capacity, speed, and where it breaks

**Type:** bring-up and inference performance · **Reproducibility:** R3 ·
**Article (HU):** [122B-os modell egy DGX Sparkon: élesben mérve](https://docai.hu/blog/qwen35-122b-spark)

> The companion measurement — *what the model is actually good at* — is
> [35b-vs-122b-business-tasks](../2026-05-22-35b-vs-122b-business-tasks/).

## 1. What was the measurement for?

A 122B-parameter mixture-of-experts model fits in 128 GB of unified memory at 4 bits. Before asking
whether it is *useful*, we had to establish what it costs to run: how much KV cache is left after
the weights, how fast it decodes, how long a cold start takes, and which parts of the serving stack
refuse to cooperate on this architecture.

## 2. On what task and dataset?

[performance](../../performance/) workloads — four single-stream profiles (`qa`, `json`, `hu`,
`long_rag`), three runs each, plus long-context capacity probing up to 240k tokens. No document
corpus; this is a serving measurement.

## 3. Which configuration?

| | |
|---|---|
| Model | Qwen3.5-122B-A10B-NVFP4 — 76 GB on disk, 62 layers + a 1-layer draft head |
| Quantisation | 4-bit packed main path, **BF16 draft head** shipped as separate weights |
| Architecture | Hybrid transformer + state-space layers |
| Hardware | DGX Spark GB10 (`sm_121a`), 128 GB unified memory |
| MoE backend | Engine auto-selection: CUTLASS for the 4-bit main path, Triton for the BF16 draft |

```text
--max-model-len 262144
--gpu-memory-utilization 0.75
--max-num-batched-tokens 16384  --max-num-seqs 4
--attention-backend FLASHINFER
--kv-cache-dtype fp8_e4m3
--enable-prefix-caching
--speculative-config '{"method":"mtp","num_speculative_tokens":2}'
```

## 4. Which metrics?

KV-cache capacity and maximum concurrency from the boot log; decode tok/s and TTFT per workload;
speculative acceptance from the engine metrics endpoint; cold- and warm-start time.

## 5. What was the result?

### It fits, and FP8 KV cache is what makes it comfortable

| Configuration | Max length | Seqs | KV tokens | Concurrency at full context |
|---|---|---|---|---|
| Baseline, FP16 KV | 65k | 16 | 437k | 6.68× |
| **FP8 KV** | 65k | 16 | **849k** | 12.95× |
| 131k context | 131k | 8 | 973k | 7.42× |
| **262k context (final)** | **262k** | **4** | **1.05M** | **4.00×** |

FP8 KV cache roughly **doubles** the pool with no measurable quality cost on this workload
(uncalibrated per-token dynamic scaling).

Two counter-intuitive findings:

- **Total KV tokens go up as max context goes up.** The engine captures smaller CUDA graphs at
  longer contexts, leaving more memory for the cache. KV capacity does not scale inversely with
  context length the way one expects.
- **This 122B holds roughly the same concurrency as the 35B** despite being ~4× larger, because the
  hybrid architecture costs only ~28 KiB of KV per token.

Restricting the model to text-only input, expecting to save memory, returned **nothing** (4.06× →
4.00×, noise): the vision tower's weights load from the main file regardless. We kept the
restriction anyway — it makes the configuration explicit and returns a clear error instead of a
confusing one.

### Speed — speculative decoding is what makes it viable

Decode throughput, four workloads, three runs each:

| Workload | Without MTP | With MTP (draft 2) | Δ | Acceptance |
|---|---|---|---|---|
| Q&A | 17.09 tok/s | **25.02** | +46 % | 71.2 % |
| JSON extraction | 16.98 | **30.25** | +78 % | **100 %** |
| Hungarian | 16.93 | **22.61** | +34 % | 60.8 % |
| Long-RAG 8k | 16.81 | **27.03** | +61 % | 82.5 % |

**+55 % average decode.** TTFT gets worse in exchange, by +31 % to +156 % — the trade a background
model can afford and an interactive one cannot.

Against the 35B production model (54 / 69 / 52 tok/s on Q&A / JSON / Hungarian), the 122B is
**~2.0–2.5× slower** — down from ~3.3× before speculative decoding, and close to the ratio of
active parameters.

Earlier kernel experiments on the same model: Marlin gave +2.3 % decode over the default, and FP8
KV cache alone caused a **+223 % TTFT regression** in one configuration before the final flag set
settled.

### Cold start is an operational fact, not a footnote

**~22 minutes** cold, ~5 minutes warm. Health checks need a startup window measured in tens of
minutes, and an unplanned restart during working hours is a visible outage for anything scheduled.

## 6. What product decision followed?

The model is deployable on one GB10 with this configuration. Whether it should be *used* — and for
what — is the [companion experiment](../2026-05-22-35b-vs-122b-business-tasks/); the operational
conditions are in [decision-record.md](decision-record.md).

## 7. Limits of this measurement

- **n=3** per performance workload; capacity figures are deterministic reads from the boot log.
- **One checkpoint, one engine build.** Every backend failure below is a statement about that
  build.
- **Long-context capacity above 128k was probed, not stress-tested** — 128k verified, 240k+
  plausible from the KV arithmetic but not run to completion under load.
- **Not compared against multi-GPU serving.** The question was "does it work on one Spark", not
  "is one Spark the right way to serve a 122B".

### Bring-up findings — where the wall-clock actually went

- **A missing draft head reads as 0 % acceptance, not as an error.** One published checkpoint
  simply did not ship draft weights; another build of the same model did, and acceptance went from
  0 % to 74 %. If you see zero, check the weights before concluding anything about the method.
- **The draft layer's MoE is unquantised**, so a quantised MoE backend cannot load it. Forcing one
  globally fails at startup; the engine's mixed auto-selection is the correct configuration, not a
  fallback.
- **The 4-bit FlashInfer MoE path is unavailable on `sm_121a`** — all four variants raise
  `NotImplementedError`.
- **The `fastsafetensors` load format OOMs** without GDS: the mmap peak during a 122B load kills
  the process at 0.85 memory utilisation. Default loader at 0.75 is stable.
- **"No native FP4" warnings from Marlin are expected** — it is a weight-only kernel by design.
  There is no check to patch and nothing is misconfigured.
- **The container entrypoint already includes the serve command.** Repeating it produces an
  unhelpful argument error.

## 8. The article

[122B-os modell egy DGX Sparkon: élesben mérve](https://docai.hu/blog/qwen35-122b-spark) —
*„meddig bírja, hol törik el, és érdemes-e DocAI-be tenni"*

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
