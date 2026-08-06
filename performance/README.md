# Inference performance

How we measure serving performance, and which number answers which question.

All measurements are on NVIDIA DGX Spark (GB10, `sm_121a`) — see
[../docs/hardware.md](../docs/hardware.md). The hardware is not incidental to the conclusions;
several of them exist *because* this machine is bandwidth-bound and low-concurrency.

## The four numbers

| Metric | Question it answers | When it misleads |
|---|---|---|
| **Single-stream decode tok/s** | How fast does text stream for one user? | Says nothing about capacity |
| **TTFT** | How long before anything appears? | Dominated by prompt length — meaningless without stating it |
| **Aggregate throughput @ c** | How much total work at concurrency *c*? | A capacity number quoted at an operating point nobody reaches |
| **Speculative acceptance** | Are drafted tokens useful work or wasted compute? | Highly workload-dependent; a single average hides the spread |

Our production profile is 1–3 concurrent requests with long prompts, so **TTFT is the metric that
tracks user experience** and aggregate throughput at high concurrency is a stress test. We report
both and say which one drove each decision.

## Workloads

Defined in [workloads.md](workloads.md). Six single-stream workloads spanning the real prompt
distribution (29 tokens to ~159,000), plus two concurrent mixes. The earlier four-test suite
(single / prefill-bound / concurrent / chat) and its exact invocation are in
[harness.md](harness.md).

## Protocol

- **Warm-up first**, then a fixed number of measured runs per workload. A cold torch.compile or
  CUDA-graph capture is not a serving number.
- **One vLLM instance per measurement.** Two models sharing 128 GB of unified memory contend for
  bandwidth and invalidate both results.
- **Runs with any request error are discarded**, not reported with a footnote.
- **Every launch flag is recorded** with the result, including the ones that did not change.
  A benchmark whose exact command line was not captured is not publishable.
- **Backend verified from the boot log**, never assumed from the flag. Engines silently fall back;
  we grep the log for the kernel that actually loaded.

## Variance — the part most benchmarks skip

Unless stated otherwise, results are `n=1` per variant. That is a real limitation and we mark it.

Where we did repeat, we learned why it matters: our `mixed_typical` concurrent workload measured
271.2, 239.9 and 292.6 tok/s across three identical runs — **median 271.2, CV 8.1 %**. An earlier
+15.8 % improvement claim on that workload had been resting on a single run and sat comfortably
inside the noise. It got a caveat instead of a headline.

Rules that follow:

- Any workload above **CV 5 %** is treated as unstable, and single-run differences on it are not
  reported as effects.
- `uniform_short` is stable on our setup; `mixed_typical` is not.
- One candidate backend showed roughly **2× run-to-run variance** (44 vs 86 tok/s at c=8 on two
  clean runs). Instability is itself a result — an unpredictable backend is unshippable even at a
  good median.

## Speculative decoding acceptance

Read from the engine's own metrics endpoint rather than inferred from throughput. Acceptance is
strongly workload-dependent — in one sweep, strict-JSON extraction accepted at 99.5 % while short
Hungarian chat accepted at 58 %. This is why raising the draft length helped one workload by
+19 % and hurt another by −9 % in the same run.

Report acceptance next to every speculative-decoding throughput number, or the number cannot be
interpreted.

## Reading our numbers on your hardware

Take the *shapes*, not the values:

- bandwidth-bound decode means weight size drives speed — expect the ordering to hold on any
  memory-bound part, and to change on a compute-bound one;
- kernel availability on `sm_121a` is specific to this platform, and at least one vendor
  recommendation reversed completely here;
- our concurrency ceiling of 3 is a property of our product, not of the hardware.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu) ·
[Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi (HU)](https://docai.hu/blog/vllm-gb10-tuning)*
