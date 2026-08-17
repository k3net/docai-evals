# DocAI Evals

**Reproducible evaluations for Hungarian document AI:** extraction quality, business-critical
error gates, model comparisons and DGX Spark (GB10) inference performance.

This repository is the *evidence layer* behind the engineering write-ups published on
**[docai.hu/blog](https://docai.hu/blog)**. The blog tells the story; this repository holds the
method, the configuration, the raw numbers and — deliberately — the negative results.

> DocAI is a Hungarian document-processing and document-AI platform: OCR → classification →
> key information extraction (KIE) → business validation → chat over your own documents.
> Product site: **[docai.hu](https://docai.hu)**

---

## Why this repository exists

Most published LLM benchmarks measure English, generic tasks, on data centre GPUs. We run a
production system that does something narrower and harder to fake:

- **Hungarian business documents** — invoices, payroll records, contracts, bank statements;
- **strict JSON key information extraction**, where a single wrong tax number is a real
  accounting error, not a lost benchmark point;
- **on a single 128 GB DGX Spark (GB10, `sm_121a`)**, not on an H100/B200 fleet.

Every conclusion we publish has to survive that setting. Several of the results here are
*negative* — a quantisation format we did not adopt, a vendor-recommended kernel backend that
turned out to be 3× slower on our hardware, a bigger model that lost to a smaller one on the task
that mattered. Those are the most useful ones.

One experiment deliberately steps outside business documents:
[lora-vs-reranker-hu-verse](experiments/2026-08-14-lora-vs-reranker-hu-verse/) measures fine-tuning
against a training-free baseline on Hungarian public-domain poetry. The question — does a LoRA earn
its cost, or would a deterministic scorer do the same job — is one we face on production text we
cannot publish. Public-domain verse lets us answer it at **R1**: fully reproducible, exact numbers,
nothing withheld.

## What is here — and what is not

| Published | Not published |
|---|---|
| Evaluation methodology and scoring code | Real customer documents |
| Run configurations, launch flags, engine versions | Any personal or company-confidential data |
| Synthetic sample documents and ground truth | Internal APIs, infrastructure, production secrets |
| Aggregated results, plots, negative findings | Undocumented or non-comparable numbers |
| The product decision each measurement produced | The DocAI application source code |

The full rule set is in **[docs/data-policy.md](docs/data-policy.md)**.

## Repository layout

```text
docai-evals/
├── docs/           # methodology, reproducibility levels, hardware, data policy, glossary
├── evals/          # task definitions: what we measure and how it is scored
├── performance/    # inference benchmark definitions (workloads, metrics)
├── experiments/    # one directory per measurement: README + eval-card + decision record
├── results/        # aggregated, cross-experiment result tables
├── schemas/        # JSON Schemas for eval cards, ground truth, chat scenarios
└── scripts/        # scoring, normalisation and significance-testing tools
```

## Experiments

| Experiment | Question | Outcome | Repro |
|---|---|---|---|
| [moe-kernel-tuning-gb10](experiments/2026-04-14-moe-kernel-tuning-gb10/) | Does an autotuned MoE kernel help real serving? | No — and a routine engine update turned out to be a 5 % regression | R2 |
| [qwen36-mtp-ab-gb10](experiments/2026-04-18-qwen36-mtp-ab-gb10/) | Is speculative decoding worth enabling in production? | Yes — and it helps most where theory says it should help least | R2 |
| [gemma4-vs-qwen36-json-kie](experiments/2026-04-30-gemma4-vs-qwen36-json-kie/) | Can an alternative open model replace the KIE model on Hungarian invoices? | No — line-item extraction collapses while header fields stay plausible | R3 |
| [qwen35-122b-nvfp4-bringup-gb10](experiments/2026-05-22-qwen35-122b-nvfp4-bringup-gb10/) | What does it cost to serve a 122B MoE on one 128 GB machine? | It fits, and speculative decoding is what makes it viable | R3 |
| [35b-vs-122b-business-tasks](experiments/2026-05-22-35b-vs-122b-business-tasks/) | When is a four-times-larger model actually worth it? | Not for extraction — it is worse. Yes for multi-step analysis: 5× fewer tool calls | R3 |
| [qwen36-fp8-vllm-flag-sweep](experiments/2026-07-01-qwen36-fp8-vllm-flag-sweep/) | Do vendor "agent-ready" recipe flags help an FP8 MoE on GB10? | No — every flag is neutral or negative on our load | R3 |
| [qwen36-fp8-vs-nvfp4-quality](experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/) | Does 4-bit NVFP4 keep extraction quality? | Field extraction survives; multi-entity reasoning does not | R2 |
| [invoice-counterparty-role](experiments/2026-07-16-invoice-counterparty-role/) | Who is the counterparty — us or them? | The business-critical gate: NVFP4 roughly doubles the error rate | R2 |
| [moe-backend-selection-gb10](experiments/2026-07-23-moe-backend-selection-gb10/) | Which vLLM MoE kernel backend wins on GB10? | Marlin, by up to 3.3× — against the model publisher's own recommendation | R3 |
| [mtp-speculative-decoding-gb10](experiments/2026-07-23-mtp-speculative-decoding-gb10/) | Is multi-token prediction worth it on GB10? | Yes, on every configuration measured — and more so at 4-bit | R3 |
| [vllm-prod-config-tuning-gb10](experiments/2026-08-04-vllm-prod-config-tuning-gb10/) | Which serving flags actually matter in production? | Two of six proposed measurements were worth running; async scheduling stays off | R3 |
| [lora-vs-reranker-hu-verse](experiments/2026-08-14-lora-vs-reranker-hu-verse/) | Does fine-tuning beat a deterministic best-of-8 selector? | On form, no — the untrained selector wins every metric. On voice, only training works: +36 points | **R1** |

`R1/R2/R3` are reproducibility levels — see **[docs/reproducibility.md](docs/reproducibility.md)**.
The verse experiment is the only **R1** entry: it runs on a public-domain corpus, so you can re-run
it end to end and land on our exact numbers.

## Evaluation suites

| Suite | What it measures |
|---|---|
| [hu-invoice-kie](evals/hu-invoice-kie/) | Field-level precision / recall / F1 for strict-JSON extraction from Hungarian invoices |
| [counterparty-role](evals/counterparty-role/) | Whether the model puts the *other* company in the partner slot — a deterministic, business-critical gate |
| [chat-business-scenarios](evals/chat-business-scenarios/) | Tool selection and multi-step financial reasoning over a document corpus |
| [hu-verse-prosody](evals/hu-verse-prosody/) | A deterministic ruler for Hungarian verse form — syllable count, rhyme, scheme — validated against external truth and a control group |
| [performance](performance/) | Decode throughput, TTFT, aggregate throughput under concurrency, speculative-decoding acceptance |

## Related write-ups on docai.hu

Each experiment links back to the article that tells its story. The articles are in Hungarian.

- [Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk) — the quantisation decision, and the gate that reversed it
- [Kövesd a gyártói doksit, és háromszor lassabb leszel](https://docai.hu/blog/backend-valasztas-gb10) — two vendors, one machine, opposite advice
- [Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36) — a model comparison that turned into a speculative-decoding finding
- [122B-os modell egy DGX Sparkon: élesben mérve](https://docai.hu/blog/qwen35-122b-spark) — how far a 122B MoE gets on 128 GB
- [Mikor érdemes nagyobb AI-modellt használni — és mikor nem?](https://docai.hu/blog/122b-vs-35b-mikor-jobb-a-nagyobb-modell) — 35B vs 122B on real business tasks
- [A Qwen3.6 ott hozott, ahol nem kellett volna](https://docai.hu/blog/qwen36-mtp-gb10) — multi-token prediction, measured four ways
- [Két nap, hat óra Triton tuning, egy GB10, és egy nagy semmi](https://docai.hu/blog/vllm-gb10-tuning) — why a kernel benchmark is not a serving gain
- [Versel nekünk az AI — de tud-e Arany Jánosul?](https://docai.hu/blog/versel-nekunk-az-ai) — a fine-tune that lost to a few dozen lines of scoring code, and won on the one axis the scorer cannot see
- All articles: **[docai.hu/blog](https://docai.hu/blog)**

## Reading a result honestly

Every experiment README answers the same eight questions, and the last one is always *"what are
the limits of this measurement?"*. Known weaknesses that recur across this repository:

- **Small corpora.** Human-validated Hungarian ground truth is expensive; several experiments run
  on 25–100 documents. Where the sample cannot support a claim, we say so and run McNemar's exact
  test instead of eyeballing point estimates.
- **Single-run performance numbers.** Unless a run count is stated, `n=1` per variant. One of our
  own workloads turned out to have a **CV of 8.1 %** run-to-run — we flag it wherever it is used.
- **Our hardware, our load.** GB10 has 273 GB/s unified memory bandwidth and a production
  concurrency of 1–3 requests. Conclusions about kernels and batch sizes are *not* portable to
  B200-class hardware, and we mark where a vendor recommendation failed precisely for that reason.

## Who runs this

**DocAI** is built and operated by **[K3Net Kft.](https://k3.hu)**, a Hungarian software company.
The measurements in this repository come from the production system we run for our customers — on
our own hardware, against their real documents, with results published in aggregate.

## Licence

- Code in `scripts/` — [MIT](LICENSE)
- Documentation, evaluation definitions and results — [CC BY 4.0](LICENSE-DATA.md)

Attribution: *DocAI by K3Net Kft. — [docai.hu](https://docai.hu)*.

## Contact

Questions about the methodology, or a Hungarian document set you want evaluated?

**[docai.hu](https://docai.hu)** — the product · [Blog](https://docai.hu/blog) — the write-ups ·
**[k3.hu](https://k3.hu)** — the company

Magyar nyelvű összefoglaló: **[README.hu.md](README.hu.md)**
