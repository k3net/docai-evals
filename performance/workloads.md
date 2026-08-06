# Workload definitions

The workloads used in every performance experiment in this repository. They were chosen to span
the actual production prompt distribution, not to produce impressive numbers.

## Single-stream

One request at a time. Measures what a single user feels.

| Workload | Prompt tokens | What it represents |
|---|---|---|
| `qa` | ~29 | Short conversational turn — the TTFT-sensitive case |
| `hu` | ~41 | Short Hungarian-language turn |
| `json` | ~298 | Strict-JSON extraction prompt with a schema |
| `long_rag` | ~10,700 | Retrieval-augmented answer over a handful of documents |
| `long_rag_32k` | ~39,900 | Approximates our production p99 prompt (37,036 tokens) |
| `long_rag_128k` | ~158,900 | Long-context stress: multi-document, multi-year analysis |

Reported per workload: TTFT, decode tok/s, total tokens. Averaging across workloads hides the
thing that matters — TTFT differences concentrate in the short prompts, decode differences in the
long ones.

`long_rag_32k` is the load-bearing one for production decisions: it sits where the real p99 sits.
`long_rag_128k` exists to answer capacity questions ("would this request even be accepted?") as
much as speed questions.

## Concurrent

Fixed concurrency for a fixed duration; aggregate throughput across all streams.

| Mix | Composition | Stability |
|---|---|---|
| `uniform_short` | Identical short requests | Stable — differences here are real |
| `mixed_typical` | Mixed prompt lengths approximating production traffic | **Unstable: CV 8.1 % over n=3.** Single-run differences on this mix are not effects |
| `long_only_128k` | Long-context requests only | Slow; capacity testing rather than routine benchmarking |

Default concurrency is 8 with a 60-second window per mix. Note that 8 is far above our production
peak of 3 — it is a stress point, and we say so wherever a decision leans on it.

## Metrics per run

```text
single:      TTFT, decode tok/s, output tokens, per workload
concurrent:  aggregate tok/s, completed requests, errors, speculative acceptance
both:        the exact launch command, engine build, backend read from the boot log
```

Any run with `errors > 0` is discarded rather than reported.

## Why these and not a standard suite

Public inference benchmarks mostly measure English chat at concurrency levels a GPU fleet sees.
Our load is Hungarian, document-heavy, one-to-three requests deep, with prompts two orders of
magnitude longer than a chat turn. A suite that averages over the wrong distribution optimises the
wrong thing — most visibly on prefill chunk size, where the "obvious" larger chunk lost on every
one of our six workloads while it would plausibly win on a short-prompt benchmark.

If you re-run these on other hardware, the workload shapes are the portable part. See
[../CONTRIBUTING.md](../CONTRIBUTING.md).

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
