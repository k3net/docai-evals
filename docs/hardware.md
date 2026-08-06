# Hardware and serving environment

Every performance number in this repository was measured on the same class of machine. If you are
comparing against an H100, B200 or a multi-GPU node, read this page first — several of our
conclusions are consequences of this specific hardware, and we mark them as such.

## The machine

| | |
|---|---|
| Platform | NVIDIA DGX Spark |
| GPU | GB10 (Grace Blackwell), compute capability **`sm_121a`** |
| CPU | 20-core ARM |
| Memory | **128 GB LPDDR5x coherent unified memory**, ~273 GB/s |
| Storage | 4 TB NVMe |
| Container base | the upstream vLLM OpenAI-compatible server image (nightly and tagged builds — see each experiment) |

Three such nodes are in use: one production, one that serves the production queue by day and runs
a large model at night, and one dedicated test machine. Measurements are run on the test node
unless stated otherwise; where a reference number came from a different node, the experiment says
so and — in the cases where it mattered — we re-measured to remove the confound.

## The two facts that drive most results

**1. Memory bandwidth is the bottleneck, not compute.** At 273 GB/s, decode speed on a MoE model
tracks how many bytes of weights have to be read per token. This is why 4-bit weights measured
+46 % single-stream decode over FP8 on the same engine, before any speculative decoding was
involved: smaller weights, less traffic. It is also why speculative decoding helps *more* at 4-bit
than at 8-bit — the draft forward pass is cheaper in exactly the resource that is scarce.

**2. `sm_121a` is not `sm_100`.** Kernel support is genuinely patchy, and vendor recommendations
written for B200-class hardware do not transfer. Measured on this platform:

| Backend / feature | Status on `sm_121a` |
|---|---|
| Marlin MoE | Works; fastest option measured at every concurrency level |
| Triton MoE | Works; the best functioning FP8 backend |
| `deep_gemm` | Assert-crash on the block-scaled FP8 scheme (`VLLM_USE_DEEP_GEMM=0` required on newer engines) |
| `flashinfer_cutlass` | Does not support the block-FP8 scheme (GroupShape 128×128) |
| `flashinfer_trtllm` | "kernel does not support current device cuda" |
| CUTLASS FP8 MoE | "disabled for this configuration" |
| FlashInfer `b12x` | Loads, but 2.0–3.3× slower than Marlin here — and unstable run-to-run |
| FlashInfer NVFP4 MoE (`VLLM_USE_FLASHINFER_MOE_FP4`) | `NotImplementedError` |
| `fastsafetensors` load format | mmap peak OOMs a 122B load without GDS |

"No native FP4 compute" warnings from Marlin are expected: Marlin is a weight-only kernel by
design. It is not a misconfiguration and there is nothing to patch.

## Production load profile

The serving configuration decisions in this repository are only defensible next to the load they
were made for. Measured over 30 days on the production node:

| | |
|---|---|
| Concurrent running requests, max | **3** |
| p99 / p50 running requests | 1 / 0 |
| Share of time with more than 8 running requests | **0.000 %** |
| Prompt tokens p95 / p99 | 19,359 / 37,036 |
| TTFT p50 / p95 | 0.99 s / 4.95 s |
| Prefix-cache hit rate | 1.6 % |

That is an interactive, long-prompt, low-concurrency profile — one or two large requests at a
time, almost always a full prefill. It is why we optimise for **TTFT** rather than saturated
throughput, and why a benchmark at 16 concurrent requests is a stress test for us and not an
operating point. Any of our conclusions about batching, scheduling or `max-num-seqs` should be
read as conditional on this profile.

## Models referenced

| Alias | Model | Role |
|---|---|---|
| `qwen36` | Qwen3.6-35B-A3B-FP8 | Production chat and KIE model |
| `qwen36` NVFP4 variants | Qwen3.6-35B-A3B NVFP4 checkpoints — one vendor-toolkit build and two community quantisations | Quantisation candidates — evaluated, not adopted |
| `qwen35-122b` | Qwen3.5-122B-A10B-NVFP4 | Background complex-reasoning model (night/cron) |
| `gemma4` | Gemma 4 | KIE alternative — evaluated, not adopted |
| — | bge-m3, bge-reranker-v2-m3 | Embeddings and reranking for hybrid search |

Engine builds and launch flags are in each experiment's `eval-card.yaml`. Quantised checkpoints are
identified by their construction (vendor toolkit, community dynamic, community fast) rather than by
publisher: this repository contains negative results about 4-bit quantisation, and those results
are about the format on this hardware, not about anyone's build.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu) ·
[Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi (HU)](https://docai.hu/blog/vllm-gb10-tuning)*
