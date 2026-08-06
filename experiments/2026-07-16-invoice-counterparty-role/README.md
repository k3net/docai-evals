# Who is the counterparty? — the gate that reversed a model decision

**Date:** 2026-07-16, extended 2026-07-23 · **Type:** business gate · **Reproducibility:** R2 ·
**Article (HU):** [Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk)

## 1. What was the measurement for?

Days earlier, a 4-bit quantised candidate had come within 0.0001 normalised F1 of our production
model on a 25-document benchmark
([qwen36-fp8-vs-nvfp4-quality](../2026-07-16-qwen36-fp8-vs-nvfp4-quality/)). It was also 40–69 %
faster and 10 GiB smaller. The remaining gate before adoption was a larger validation on
**representative** data — real Hungarian invoices from a live customer, where the tenant's own
company appears all over the documents.

The gate was supposed to confirm equivalence. It did the opposite.

## 2. On what task and dataset?

100 real invoice extraction requests from a production customer, replayed identically against both
models at `temperature = 0`. 1,117 field-level comparisons in total.

The corpus is private ([data policy](../../docs/data-policy.md)). Two independent ground truths
were used — see §4.

Later extended: all four models from the quantisation round scored on the same 100 documents.

## 3. Which models?

| Arm | Checkpoint | Weights |
|---|---|---|
| `fp8-ref` | Qwen3.6-35B-A3B-FP8, production | ~35 GiB |
| `nvfp4-b` | NVFP4, least aggressive | 24.7 GiB |
| `nvfp4-a` | NVFP4, vendor toolkit | 21.8 GiB |
| `nvfp4-c` | NVFP4, most aggressive | 22.0 GiB |

Identical inputs, identical sampling, deterministic replay. Any difference is a model difference.

## 4. Which metrics?

**Primary:** the [counterparty-role gate](../../evals/counterparty-role/) — how often the model
names *our own company* as the invoice partner.

Two ground truths, deliberately:

1. **Heuristic gate** ([counterparty_guard.py](../../scripts/counterparty_guard.py)) — matches the
   extracted partner tax number and name against the tenant's own. Runs on all 100 documents.
2. **Authoritative database link** — the partner company actually linked to each document. Covers
   the 82 documents where the linked partner is verifiably not our own company. This is the number
   quoted in decisions.

**Significance:** McNemar's exact test ([mcnemar.py](../../scripts/mcnemar.py)) — the models see
the same documents, so the comparison is paired.

## 5. What was the result?

### Where the two models disagree, one of them is wrong far more often

| | |
|---|---|
| Field comparisons | 1,117 |
| Exact agreement | 82.5 % |
| Cosmetic differences | 0.0 % |
| **Real content differences** | **17.5 % (195 fields)** |

Of those 195 disagreements, checked against ground truth:

| | Count |
|---|---|
| Production model right, candidate wrong | **161 (83 %)** |
| Candidate right, production model wrong | 32 (16 %) |
| Both wrong | 2 |

### The errors are not scattered — they are one failure mode

About **79 %** of the disagreements fall in the block of fields that identify who is who:

| Field | Disagreements |
|---|---|
| `own_address_score` | 25 |
| `own_taxnumber_score` | 23 |
| `partner_name` | 23 |
| `partner_taxnumber` | 23 |
| `own_name_score` | 22 |
| `partner_bank_account` | 21 |
| `partner_person_name` | 17 |

The pattern is consistent: **the candidate puts the tenant's own company in the partner slot**, and
its own-company recognition scores collapse to zero on the same document. One error, surfacing in
seven fields.

**31 of 100 documents** carried at least one such error from the candidate.

### The headline numbers

Heuristic gate, own company named as partner:

| Model | Flagged / 100 |
|---|---|
| `fp8-ref` | **7** |
| `nvfp4-b` | 18 |
| `nvfp4-a` | 16 |
| `nvfp4-c` | 12 |

Authoritative ground truth, on the 82 documents where the partner is verifiably someone else:

| Model | Wrong |
|---|---|
| `fp8-ref` | 7 / 82 (**9 %**) |
| `nvfp4-b` | 16 / 82 (**20 %**) |

**A 2.2× error rate on the most business-critical field group in the pipeline.** The production
model is not perfect either — 9 % is not a comfortable number — but the candidate makes the
problem materially worse.

### Significance — and the story that did not survive it

Against the production model:

| Comparison | Flagged | McNemar p |
|---|---|---|
| `fp8-ref` vs `nvfp4-b` | 7 vs 18 | **0.019** ✅ |
| `fp8-ref` vs `nvfp4-a` | 7 vs 16 | **0.049** ✅ |
| `fp8-ref` vs `nvfp4-c` | 7 vs 12 | 0.267 ❌ |

Between the candidates:

| Comparison | Flagged | p | Distinguishable? |
|---|---|---|---|
| `nvfp4-b` vs `nvfp4-c` (the two extremes) | 18 vs 12 | 0.238 | **no** |
| `nvfp4-a` vs `nvfp4-c` | 16 vs 12 | 0.481 | **no** |
| `nvfp4-b` vs `nvfp4-a` | 18 vs 16 | 0.832 | **no** |

We went in expecting a dose-response: more aggressive quantisation, more damage. The data does not
support it. The three candidates cannot be told apart at `n=100`, and — inconveniently for the
narrative — the *least* aggressive one has the highest point estimate.

**What we published instead:** all three 4-bit checkpoints roughly double the counterparty error
rate relative to FP8 (12–18 vs 7); differences among them are not established at this sample size.
The effect attaches to the quantisation *format*, not to a dose along aggressiveness. We did not
replace one unsupported story ("aggressive 4-bit breaks") with another ("less aggressive is worse")
— the second is equally unsupported.

### Why the heuristic gate flags 18 while the database confirms 16

The two extra documents are **foreign partners** whose tax field held a SWIFT/BIC code or nothing
at all — cases the tax-number-based authoritative check could not verify either way. Inspection
showed the model was still wrong on both: it named our own company instead of the foreign partner.

So the heuristic count is the wider number, the database-verified count is the conservative lower
bound, and both are published. Incidentally, the candidate is *more* prone to this failure on
foreign partners specifically.

## 6. What product decision followed?

**Gate failed. Stay on FP8.** The canary phase was never started. See
[decision-record.md](decision-record.md) and the
[quantisation decision record](../2026-07-16-qwen36-fp8-vs-nvfp4-quality/decision-record.md).

## 7. Limits of this measurement

- **`n = 100`, one tenant.** Enough to establish a 2× effect against the baseline; not enough to
  rank the candidates against each other, as the pairwise tests show explicitly.
- **The heuristic gate over-counts** on foreign partners; the authoritative subset is the
  conservative figure and covers 82 of the 100 documents.
- **One direction only.** Putting the *partner* into the own-company slot is a different error and
  is not measured here.
- **Deterministic, not sampled.** `temperature = 0` on identical inputs; this is a capability
  difference, not a sampling artefact — but it also means we have not measured how the gap behaves
  under production sampling settings.
- **Single ground-truth source for the authoritative check.** The database link is human-maintained
  and can itself be wrong, though it is independent of both models.

## 8. The article

[Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk) —
the article's middle section, *„a kapu, ami számított"*, is this measurement.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
