# Glossary

Terms used across this repository, in the sense we use them.

## Task and domain

**KIE — Key Information Extraction.** Extracting a fixed set of typed fields from a document into
strict JSON: invoice number, dates, tax numbers, amounts, line items. Not summarisation, not
question answering — a schema has to be filled, and empty is a valid answer.

**Header vs items.** Invoice extraction is split in two: the *header* (one object: parties, dates,
totals) and the *items* (the line-item array). They fail differently — a model can hold the header
while its line items collapse, which is exactly what one of our model comparisons found.

**Counterparty role / own-vs-partner.** On any invoice, one of the two companies is the tenant
itself and the other is the partner. Deciding which is which requires matching names and tax
numbers against the tenant's own identity. Getting it backwards flips the direction of the
transaction — incoming becomes outgoing — and corrupts tax-authority matching and bookkeeping.
This is our canonical example of a business-critical error that aggregate F1 hides.

**Business gate.** A deterministic, rule-based check for one specific failure mode, run on the
same model outputs as the F1 scoring. No LLM judge, no manual review — hence no judge bias, and
cheap enough to run on every candidate.

**Doctype classification.** Deciding what kind of document arrived (invoice, contract, payroll,
delivery note…). Type codes are per-customer, so cross-customer comparisons of classifier accuracy
are meaningless without saying whose taxonomy is in use.

**Ground truth (GT).** Human-validated expected output. In this domain it is the scarce resource:
one carefully validated Hungarian invoice corpus is worth more than ten times as many
machine-labelled ones. See the self-baseline warning in
[../evals/hu-invoice-kie/README.md](../evals/hu-invoice-kie/README.md).

## Metrics

**Precision / recall / F1.** Computed over field outcomes, with `mismatch` charged to both
precision and recall — see [methodology.md](methodology.md#field-level-extraction-kie).

**Raw vs normalised F1.** Raw counts every textual difference; normalised applies frozen cosmetic
rules (`1` vs `1.0`, collapsed whitespace, `null` vs `0.0` on named numeric fields). The gap
between them measures JSON formatting noise rather than comprehension.

**McNemar's exact test.** Paired significance test for two models scored on the same documents.
It looks only at the documents where the two disagree, which is the right question for "is
candidate B worse than baseline A" on small corpora.

**LLM judge.** A model scoring another model's answer against a written rubric. Useful for chat
quality, unreliable as a sole criterion — see the caveats in
[../evals/chat-business-scenarios/README.md](../evals/chat-business-scenarios/README.md).

## Serving and hardware

**GB10 / `sm_121a`.** The NVIDIA DGX Spark GPU and its compute capability. Kernel support differs
materially from data-centre Blackwell parts — see [hardware.md](hardware.md).

**Unified memory.** On DGX Spark, CPU and GPU share 128 GB of LPDDR5x at ~273 GB/s. Model weights,
KV cache and everything else come out of one pool, and bandwidth — not FLOPs — is the usual limit.

**MoE — Mixture of Experts.** Only a fraction of parameters is active per token (for example 3B
active out of 35B total). Cheap to compute, expensive to *read*: on a bandwidth-bound machine the
total size still dominates decode speed.

**FP8 / NVFP4.** 8-bit and 4-bit weight quantisation formats. NVFP4 halves the bytes again, which
on this hardware translates directly into decode speed — the question this repository answers is
what it costs in capability.

**Block-scaled FP8.** An FP8 scheme with per-block (128×128) scale factors. Relevant because
several kernel backends do not support it on `sm_121a`, which constrains backend choice for the
incumbent model.

**MTP — Multi-Token Prediction.** Speculative decoding where a small draft head proposes *k*
tokens and the main model verifies them in one pass. `num_speculative_tokens` is *k*.

**Acceptance rate.** The share of drafted tokens the main model accepts. Below roughly 60 % the
extra draft compute stops paying for itself; above 70 % speculative decoding is close to free
speed. Acceptance is workload-dependent — strict JSON output accepts far better than open chat.

**TTFT — time to first token.** Latency before anything appears. Dominated by prompt length and
prefill chunk size. On our load profile it matters more than steady-state decode rate.

**TPOT — time per output token.** The steady-state inverse of decode throughput.

**Chunked prefill / `max-num-batched-tokens`.** Long prompts are prefilled in chunks; the chunk
size determines how many passes a prompt takes, and therefore TTFT.

**Aggregate throughput.** Total tokens per second across all concurrent requests at a given
concurrency level. The right number for capacity questions; the wrong number for interactive
latency questions.

**Backend / kernel backend.** Which GEMM implementation serves the MoE and linear layers (Marlin,
Triton, CUTLASS, FlashInfer variants). On `sm_121a` this choice moved throughput by up to 3.3× in
our measurements — more than the quantisation format did.

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu)*
