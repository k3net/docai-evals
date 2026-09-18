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
| 2026-08-28 | [qwen38-flash-next-nvfp4-topk-nondeterminism-gb10](2026-08-28-qwen38-flash-next-nvfp4-topk-nondeterminism-gb10/) | Correctness / serving | Greedy output was non-deterministic; root cause the QSA `persistent_topk` kernel, fixed by a canonical `torch.topk` at 74 % prefill; not adopted until the full suite passes | R2 |
| 2026-09-03 | [qwen38-flash-next-det-topk-kernel-batch-invariance-gb10](2026-09-03-qwen38-flash-next-det-topk-kernel-batch-invariance-gb10/) | Correctness / serving | The fix is deterministic only for sequential requests in the same cache state (no batch invariance; partial ≠ full prefix hit); the vllm#55122 kernel gives the same determinism at 96–100 % of stock prefill — candidate, pending the suite score | R2 |
| 2026-09-12 | [qwen38-flash-next-prefix-cache-cross-request-gb10](2026-09-12-qwen38-flash-next-prefix-cache-cross-request-gb10/) | Correctness / serving | The failing path is the **full** prefix-cache hit on blocks written by a differently sized request, not the partial one; reproduced on the official v0.29.0 image with the deterministic kernel, and produced on demand across a 1600-token block boundary; vllm#56500 inapplicable, the det kernel 21–28 % faster | R2 |
| 2026-09-14 | [qwen38-flash-next-prefix-cache-root-cause-gb10](2026-09-14-qwen38-flash-next-prefix-cache-root-cause-gb10/) | Correctness / serving | Root cause found: under MTP the scheduler backs the last cacheable position off by one block, so a request below 2×block_size stores no Mamba state at the shared boundary while still publishing its KV there; the rule explains all eight round-3 pairs including the counterexample, a nine-token change in the first request flips determinism, and the one-line boundary stop from vllm#54076 turns the original failing pair green at 10/10 | R2 |
| 2026-09-18 | [qwen38-flash-next-qwen-parser-marker-guard-gb10](2026-09-18-qwen38-flash-next-qwen-parser-marker-guard-gb10/) | Correctness / serving | The literal-marker guard does reach a `qwen3_coder` deployment (`Qwen3Parser.CONFIG_NAME` is `"qwen3"`); the two downstream patches fix disjoint cases — vllm#56661 (draft) recovers text lost around a marker quoted in prose and leaves the fenced-code-block case untouched, the still downstream-only fence guard is what removes the phantom call and the `content: null`; adoption perturbs nothing, the deterministic kernel binary is byte-identical; and 8 of 9 empty responses were already truncated in raw generation, a failure outside the scope of either parser because the model emits EOS itself after writing `<tool_call>` into its own reasoning. Negative result alongside: an apparent streaming/non-streaming divergence did not survive replaying the identical raw text through both parse paths (0/12) | R2 |

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
