# The benchmark harness

Every performance number in this repository comes from the inference engine's own `bench serve`
tool, driven by a wrapper script. Nothing custom measures the timings — which is deliberate: a
home-made load generator is one more thing a reader would have to trust.

This page documents the invocation exactly, so the runs are reproducible on other hardware.

## The four tests

```bash
# A — single decode: one user, streaming
vllm bench serve --dataset-name random \
  --random-input-len 512  --random-output-len 512 \
  --num-prompts 20 --max-concurrency 1  --seed 42

# B — prefill-bound: long prompt, short answer (document extraction shape)
vllm bench serve --dataset-name random \
  --random-input-len 8192 --random-output-len 256 \
  --num-prompts 20 --max-concurrency 4  --seed 42     # repeated with --seed 123

# C — concurrent contention: saturation stress test
vllm bench serve --dataset-name random \
  --random-input-len 2048 --random-output-len 512 \
  --num-prompts 64 --max-concurrency 16 --seed 42     # repeated with --seed 123

# D — chat profile: realistic interactive load
vllm bench serve --dataset-name random \
  --num-prompts 16 --max-concurrency 2  --seed 42     # repeated with --seed 123
```

Common flags on every run:

```bash
--backend openai-chat --endpoint /v1/chat/completions \
--num-warmups 3 \
--ignore-eos \
--percentile-metrics "ttft,tpot,itl,e2el" --metric-percentiles "50,95,99" \
--save-result --save-detailed \
--metadata "phase=<phase>" --metadata "test=<test>" --metadata "seed=<seed>"
```

Notes on the choices:

- **`--num-warmups 3`** — a cold engine is not a serving number. Compilation and graph capture must
  be out of the way before the first measured request.
- **`--ignore-eos`** — forces exact output lengths so runs are comparable. Slightly unrealistic
  (real responses stop when the model decides to), and we say so in every experiment that uses it.
- **`--dataset-name random`** — synthetic prompts, no customer data. It is why these numbers can be
  published at all.
- **Fixed seeds, plus a second seed on B and C** — the two workloads where we found run-to-run
  variance worth quantifying.
- **`--save-detailed`** — keeps per-request TTFT and inter-token latency arrays, not just the
  summary. Medians and percentiles are recomputed from those rather than trusted from a single
  summary line.

## Environment snapshot — the part that makes a result citable

After every phase, the wrapper writes alongside the results:

| File | Contents |
|---|---|
| `vllm-version.txt` | the engine version string, from inside the container |
| `lib-versions.txt` | engine, attention-kernel, Triton and framework versions |
| `image-sha.txt` | the container image digest |
| `docker-compose.yml.final` | the exact service definition used |
| `vllm-config.txt` | grepped boot log: resolved non-default args, selected MoE and attention backends, KV-cache size, max concurrency, scheduling mode, eager/graph state |

That last file is the important one. **The backend is read from the boot log, never assumed from
the flag** — engines fall back silently, and more than one result in this repository turned on
discovering that the kernel which loaded was not the one requested.

A pre-flight health check waits up to six minutes for the engine before any measurement starts, and
the wrapper refuses to overwrite a non-empty output directory.

## Output format

One JSON file per test, from the engine's own writer:

```text
phase, test, model_id, image_sha, max_concurrency, num_prompts, completed, failed,
output_throughput, total_token_throughput,
mean/median/p95/p99_ttft_ms, mean/median_tpot_ms,
ttfts[], itls[], input_lens[], output_lens[]
```

Any run with `failed > 0` is discarded rather than reported.

## Speculative-decoding acceptance

Read from the engine's Prometheus endpoint after the run, not inferred from throughput:

```text
vllm:spec_decode_num_drafts_total
vllm:spec_decode_num_draft_tokens_total
vllm:spec_decode_num_accepted_tokens_total
vllm:spec_decode_num_accepted_tokens_per_pos_total{position="0"}   # and position="1", ...
```

Overall acceptance is `accepted / draft_tokens`. The **per-position** counters are the ones worth
plotting: on our production model the first drafted token is accepted 81.6 % of the time and the
second only 63.5 %, which a single 72.5 % average completely hides — and that gradient is what
decides whether a longer draft could ever pay.

## Reproducing on other hardware

The four test definitions above are the portable part. Run them against your own engine and model,
capture the same environment snapshot, and the *shapes* become comparable even though the absolute
numbers will not be. If you do, we would like to hear about it — see
[../CONTRIBUTING.md](../CONTRIBUTING.md).

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
