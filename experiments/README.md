# Experiments

One directory per measurement. Directory names are technical and searchable — the editorial
headline stays on [docai.hu/blog](https://docai.hu/blog).

```text
<YYYY-MM-DD>-<technical-name>/
├── README.md            # the eight questions (docs/methodology.md)
├── eval-card.yaml       # machine-readable summary, validated in CI
└── decision-record.md   # what we did about it, and what would reopen it
```

| Date | Experiment | Type | Verdict | Repro |
|---|---|---|---|---|
| 2026-04-14 | [moe-kernel-tuning-gb10](2026-04-14-moe-kernel-tuning-gb10/) | Performance | Autotuned kernel gains nothing at the serving layer | R2 |
| 2026-04-18 | [qwen36-mtp-ab-gb10](2026-04-18-qwen36-mtp-ab-gb10/) | Performance | Speculative decoding on, draft 2 | R2 |
| 2026-04-30 | [gemma4-vs-qwen36-json-kie](2026-04-30-gemma4-vs-qwen36-json-kie/) | KIE | Keep the incumbent — line items collapse | R3 |
| 2026-05-22 | [qwen35-122b-nvfp4-bringup-gb10](2026-05-22-qwen35-122b-nvfp4-bringup-gb10/) | Bring-up + perf | Runs on one GB10; speculative decoding makes it viable | R3 |
| 2026-05-22 | [35b-vs-122b-business-tasks](2026-05-22-35b-vs-122b-business-tasks/) | KIE + tool use | Route by task: worse at extraction, 5× more efficient at analysis | R3 |
| 2026-07-01 | [qwen36-fp8-vllm-flag-sweep](2026-07-01-qwen36-fp8-vllm-flag-sweep/) | Performance | Reject every candidate flag | R3 |
| 2026-07-16 | [qwen36-fp8-vs-nvfp4-quality](2026-07-16-qwen36-fp8-vs-nvfp4-quality/) | KIE + chat | Quality equivalent on a small corpus — which turned out to be the wrong corpus | R2 |
| 2026-07-16 | [invoice-counterparty-role](2026-07-16-invoice-counterparty-role/) | Business gate | Blocking: 4-bit roughly doubles the error | R2 |
| 2026-07-23 | [moe-backend-selection-gb10](2026-07-23-moe-backend-selection-gb10/) | Performance | Marlin everywhere on GB10 | R3 |
| 2026-07-23 | [mtp-speculative-decoding-gb10](2026-07-23-mtp-speculative-decoding-gb10/) | Performance | Keep speculative decoding on, at draft length 2 | R3 |
| 2026-08-04 | [vllm-prod-config-tuning-gb10](2026-08-04-vllm-prod-config-tuning-gb10/) | Performance | One unified serving profile; async scheduling off | R3 |
| 2026-08-26 | [where-knowledge-lives-hu-en-zh](2026-08-26-where-knowledge-lives-hu-en-zh/) | Multilingual + interpretability | No lexical English pivot; the shared middle layer is real but thin; English is never the best prompt language | **R1** |

Reproducibility levels: [../docs/reproducibility.md](../docs/reproducibility.md).

## How to read a pair of these

The July experiments are best read together and in order. `qwen36-fp8-vs-nvfp4-quality` concluded
that a 4-bit quantisation was quality-equivalent to the incumbent. `invoice-counterparty-role`,
run days later on a representative corpus, showed that it was not — and reversed the decision.

We publish both, in that order, including the intermediate conclusion that turned out to be wrong.
The sequence is the useful artefact: it is a worked example of a small generic benchmark hiding a
business-critical regression, which is the most common way a model evaluation goes wrong in this
domain.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
