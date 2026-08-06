# Gemma 4 vs Qwen3.6 — strict-JSON KIE on Hungarian invoices

**Date:** 2026-04-30 · **Type:** extraction quality · **Reproducibility:** R3 ·
**Article (HU):** [Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36)

## 1. What was the measurement for?

To find out whether an alternative open-weights model could replace the incumbent extraction model
in the document pipeline. The incumbent had been in production for months; the question was
whether a different model family would be at least as good on the task that pays the bills —
turning a Hungarian invoice into strict JSON.

## 2. On what task and dataset?

[hu-invoice-kie](../../evals/hu-invoice-kie/) — 34 scored units (invoice headers and line-item
arrays) from a mixed Hungarian and English corpus of real invoices, replayed deterministically
from stored production requests so that both models saw byte-identical input.

Corpus is private ([data policy](../../docs/data-policy.md)). Structure is illustrated by the
[synthetic samples](../../evals/hu-invoice-kie/samples/).

## 3. Which models and configurations?

| Arm | Model | Role | Sampling |
|---|---|---|---|
| `qwen36-baseline` | Qwen3.6-35B-A3B-FP8 | incumbent | `temperature=0`, `max_tokens=8192`, thinking off |
| `gemma4` | Gemma 4 | candidate | identical |

Same serving node, same engine, same prompt, greedy decoding. The only variable is the model.

## 4. Which metrics?

Field-level precision / recall / F1 with `mismatch` charged to both sides, JSON validity, latency
per scored unit, token usage. Definitions:
[methodology](../../docs/methodology.md#field-level-extraction-kie).

## 5. What was the result?

| Metric | `qwen36-baseline` | `gemma4` |
|---|---|---|
| Scored units | 34 | 34 |
| JSON validity | 100 % | 100 % |
| **Overall F1** | **1.000** ⚠️ | **0.890** |
| Precision | 1.000 | 0.888 |
| Recall | 1.000 | 0.892 |
| TP / FN / FP / mismatch | 214 / 0 / 0 / 0 | 191 / 3 / 4 / 20 |
| Avg latency per unit | 6,687 ms | 10,396 ms |
| Avg input tokens | 6,734 | 5,293 |

⚠️ **The 1.000 is not a model result.** See §7 — it is a ground-truth artefact, and the honest
reading of this table is the *shape* of the candidate's errors, not the gap between the two
numbers.

### The finding that matters: headers held, line items collapsed

Breaking the 34 units into the two sub-tasks:

| Sub-task | Units | Candidate F1 |
|---|---|---|
| `header` | 25 | 0.75 – 1.000, median ~0.96 |
| `items` | 9 | **0.000 on all nine** |

Every single line-item array failed. Meanwhile the header fields looked broadly fine — an
aggregate score over both sub-tasks averages a total failure into something that reads as
"slightly behind".

The dominant line-item failure was **name padding**: the model copied the whole document line,
billing period and customer included, into the product-name field.

```text
ground truth:  "Éves előfizetés"
prediction:    "Éves előfizetés – <ügyfél> 2026. május – 2028. május"
```

Structurally valid, semantically wrong, and it breaks per-product aggregation downstream.

### Header errors, by type

27 field-level differences on the candidate, dominated by a few recurring patterns:

| Pattern | Example (synthetic equivalent) | Why it matters |
|---|---|---|
| Tax-number format substitution | `12345678-2-42` → `HU12345678` | Different join key for tax-authority matching |
| Payment method invented | `TRANSFER` → `CARD` | Drives reconciliation logic |
| Date hallucinated where none exists | `null` → a plausible delivery date | A computed date is wrong on every invoice with different terms |
| Enum filled instead of left empty | `null` → `OTHER` | Turns "unknown" into a false assertion |
| Diacritic corruption | `ő` → `ô` | Passes loose string comparison, corrupts exact partner matching |
| Amount rounding drift | `1990` → `1990.5` | Fails invoice-total validation |
| Identifier truncation | 12-digit invoice number → first 8 digits | Duplicate-detection failure |

The incumbent produced none of these on this corpus — but see §7 before reading that as a clean
sweep.

## 6. What product decision followed?

**Keep the incumbent.** No pilot, no partial rollout. See
[decision-record.md](decision-record.md).

## 7. Limits of this measurement

- ⚠️ **Self-baseline bias, and it is severe.** The ground truth for this corpus was bootstrapped
  from the incumbent's own production output and hand-corrected only partially at this point. That
  is why the incumbent scores 1.000 — not because it is perfect, but because it was scored against
  a lightly-corrected copy of its own answers. A later run of the *same model* against the
  *corrected* ground truth scored **0.975**
  ([qwen36-fp8-vs-nvfp4-quality](../2026-07-16-qwen36-fp8-vs-nvfp4-quality/)).
  The candidate, meanwhile, was charged for every difference — including ones where it may have
  been right.
- **Therefore the gap is an upper bound, not an estimate.** The defensible claim from this run is
  qualitative: *the candidate fails on line items in a way the incumbent does not*, which is a
  structural failure visible independent of ground-truth quality. The 0.890 vs 1.000 headline is
  not a measurement of model distance.
- **Small corpus.** 34 units, 25 of them headers.
- **One prompt.** The extraction prompt was tuned over months against the incumbent. A fair
  head-to-head would re-tune it for the candidate; we did not, because the production question was
  "can we swap the model", not "which model is better in principle".
- **Latency is not comparable to later runs** — different date, different engine build.

## 8. The article

[Gemma4-et néztem, MTP-t találtam](https://docai.hu/blog/gemma4-vs-qwen36) — the candidate
evaluation is the first half; the speculative-decoding finding it turned into is the second, and
that thread continues in
[mtp-speculative-decoding-gb10](../2026-07-23-mtp-speculative-decoding-gb10/).

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
