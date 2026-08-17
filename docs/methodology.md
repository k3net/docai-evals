# Methodology

How a measurement gets from "we should check this" to a published number.

## 1. The eight questions

Every experiment README in this repository answers the same eight questions, in the same order:

1. **What was the measurement for?** — the decision it was supposed to inform.
2. **On what task and dataset?** — size, language, document types, provenance.
3. **Which models and configurations were compared?** — checkpoints, engine, launch flags.
4. **Which metrics?** — and how each one is computed.
5. **What was the result?**
6. **What product decision followed?**
7. **What are the limits of the measurement?**
8. **Which DocAI article belongs to it?** — the story version on [docai.hu/blog](https://docai.hu/blog).

Question 7 is not a formality. Most of what makes a benchmark misleading is invisible in the
result table: a corpus that is too small, a variance nobody measured, a ground truth derived from
one of the models under test.

## 2. Rules we hold ourselves to

### Fix the scoring before you look at the scores

Normalisation rules — what counts as a "cosmetic" difference — are written down and frozen
*before* the comparison is scored, and the version is recorded (for example
`kie_normalizer v1.0`). Otherwise every normalisation step becomes an opportunity to make the
preferred model look better.

The same code scores every arm of a comparison. If a field has to be excluded (disputed ground
truth, for instance), it is excluded for **all** models and named in the report.

### Compare like with like, then say what was not alike

An A/B where the two arms differ in machine *and* engine version measures nothing in particular.
When we discovered our FP8 reference point sat on both boundaries at once (different node,
different vLLM build), we re-ran it cleanly on the same machine and engine as the candidates —
and only then compared. The difference turned out to be ±5 % and non-directional, which is itself
a publishable result: it showed the effect we were chasing was not an engine artefact.

### Best-vs-best, not best-vs-default

When comparing two serving configurations, each side gets its own optimum. We ran the full
kernel-backend sweep for the *incumbent* FP8 model before claiming a 4-bit candidate was faster —
specifically so the headline could not be "we beat a badly configured baseline". In that case the
incumbent's default backend really was its optimum, and the headline survived.

The same rule applies to *training* proposals, and there it bites harder: the baseline is not the
raw model, it is **the best result obtainable without training**. Any fine-tuning proposal has to
name that opponent before the GPU is booked. When we did this on
[verse style transfer](../experiments/2026-08-14-lora-vs-reranker-hu-verse/), a deterministic
best-of-8 selector beat the fine-tuned adapter on every form metric — which is also what made the
one axis where training *did* win interpretable. Against the raw model alone, the adapter would
have "won convincingly" and we would have learned nothing.

A weak baseline does not give you a weaker result. It gives you an uninterpretable one.

### Statistical significance on small samples

Point estimates on 100 documents look precise and usually are not. For paired model comparisons on
the same documents we use **McNemar's exact test** ([scripts/mcnemar.py](../scripts/mcnemar.py)).
Where the test says the difference between two candidates is not distinguishable, we say exactly
that, rather than reporting the ordering as a finding — even when the ordering supports a nicer
story.

### A failed hypothesis is a result

Several conclusions in this repository are the opposite of what we expected going in:

- The "aggressiveness dose-response" framing for 4-bit quantisation **did not hold** — the three
  checkpoints were statistically indistinguishable from each other while all being worse than
  FP8. We published the negative version of the claim rather than swapping in a different
  unsupported one.
- The FlashInfer "performance cliff" hypothesis for a slow kernel produced **zero** log hits. The
  backend was simply slower on this architecture; we said so instead of keeping the tidier
  explanation.

### Anonymisation is part of scoring, not a post-processing step

Guards and scorers that reference tenant-specific constants (own tax number, own company name)
take them as **parameters**, never as literals in published code. Only aggregate counts leave the
machine. See [data-policy.md](data-policy.md).

## 3. Quality metrics

### Field-level extraction (KIE)

Each extracted field is compared to human-validated ground truth and lands in one of five buckets:

| Outcome | Meaning |
|---|---|
| `tp` | ground truth has a value, prediction matches |
| `fn` | ground truth has a value, prediction is empty |
| `fp` | ground truth is empty, prediction invents a value |
| `mismatch` | both have values, and they differ |
| `tn` | both empty |

```text
precision = tp / (tp + fp + mismatch)
recall    = tp / (tp + fn + mismatch)
F1        = 2PR / (P + R)
```

A `mismatch` is deliberately charged to **both** precision and recall: a wrong tax number is
simultaneously a false claim and a missed fact. This makes our F1 stricter than the usual
formulation — numbers here are not directly comparable to benchmarks that only count exact
matches against non-empty predictions.

Comparison is field-type aware (strict string, loose string, ISO date, number with epsilon,
score, enum) — see [../evals/hu-invoice-kie/field-types.md](../evals/hu-invoice-kie/field-types.md).

We report **raw** and **normalised** F1 side by side. Raw counts every difference; normalised
applies the frozen cosmetic-normalisation rules. The gap between the two is itself informative:
when a 1-point raw difference disappears entirely under normalisation, the models were
substantively equivalent on that corpus and the raw number was measuring JSON formatting.

### Business gates

An aggregate F1 can hide the error that actually costs money. Alongside F1 we run **deterministic
gates** on the same outputs: rule-based checks for a specific, business-critical failure mode.

The one published here is the **counterparty-role gate** — did the model put *our own* company in
the partner slot? It needs no LLM judge and no manual review: match the extracted partner tax
number and name against the tenant's own, count the hits. On our corpus, models that were
equivalent on aggregate F1 differed by 2× on this gate.

### Chat and tool use

For multi-step scenarios we score: required tool calls made (and forbidden ones avoided),
argument sub-matching, iteration count, and an LLM-judge score against a per-scenario rubric.
Judge caveats are in [../evals/chat-business-scenarios/README.md](../evals/chat-business-scenarios/README.md).

## 4. Performance metrics

See [../performance/](../performance/) for workload definitions. In short:

| Metric | Why |
|---|---|
| Single-stream decode tok/s | What one user feels while text streams |
| TTFT | What one user feels before anything appears — dominated by prompt length and chunk size |
| Aggregate throughput at concurrency *c* | The production number when several requests overlap |
| Speculative-decoding acceptance | Whether draft tokens are useful work or wasted compute |

Runs with any request error are discarded rather than reported. Where a measurement is repeated,
we report the median and the coefficient of variation, and we treat any workload above CV 5 % as
unstable — including our own `mixed_typical`, which came in at **8.1 %**.

## 5. Provenance

The evaluation harnesses that produced these results live inside the DocAI codebase and are not
themselves published; what is published is the scoring logic, the normalisation rules, the
configurations and the outputs. Every experiment states its reproducibility level — see
[reproducibility.md](reproducibility.md).

---

*Part of [DocAI Evals](../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
