# Eval suite: Hungarian invoice KIE

Field-level key information extraction from Hungarian invoices into strict JSON, scored against
human-validated ground truth.

**Suite version:** 1.0 · **Normaliser:** `kie_normalizer v1.0` · **Language:** Hungarian (with
English and mixed-language invoices from foreign suppliers)

## What it measures

Given a document — OCR text plus, for scanned originals, the page image — the model must return a
fixed JSON object. Two sub-tasks are scored separately because they fail differently:

| Sub-task | Output | Typical failure |
|---|---|---|
| `header` | One object: parties, identifiers, dates, totals | Wrong party, wrong date semantics, invented values |
| `items` | Array of line items | Whole array collapses, or line text is copied verbatim into the name field |

Splitting them matters. In one model comparison the candidate held every header field within a few
points of the baseline while **every scored line-item array failed** — an aggregate score over
both would have averaged that into something that looked survivable.

## What it does *not* measure

- **Which party is which.** Aggregate F1 spreads the own-vs-partner confusion across several
  fields and dilutes it. That failure mode has its own instrument:
  [../counterparty-role/](../counterparty-role/).
- **Downstream business validity.** Whether the extracted invoice reconciles against the tax
  authority record, matches a purchase order, or lands in the right ledger is a product concern
  measured elsewhere.
- **Anything about scanned-image quality.** OCR runs before this eval; a bad scan shows up here as
  a model error even when the model saw nothing useful.

## Field set

Roughly 25 header fields plus the line-item array. The full type map is in
[field-types.md](field-types.md); the shape is:

```json
{
  "invoice_number":     {"value": "2026/A-00184", "confidence": 0.98},
  "invoice_date":       {"value": "2026-03-14",   "confidence": 0.99},
  "partner_name":       {"value": "Példa Logisztika Kft.", "confidence": 0.95},
  "partner_taxnumber":  {"value": "12345678-2-42", "confidence": 0.97},
  "own_name_score":     {"value": 1.0, "confidence": 0.9},
  "total_gross_amount": {"value": 127000.0, "confidence": 0.99},
  "invoice_items":      {"value": [ /* line items */ ], "confidence": 0.9}
}
```

`null` is a first-class answer. A field genuinely absent from the document must be `null` in
ground truth, which is what makes an invented value scoreable as a false positive rather than
silently ignored.

## Scoring

Each field lands in one of `tp` / `fn` / `fp` / `mismatch` / `tn`, and:

```text
precision = tp / (tp + fp + mismatch)
recall    = tp / (tp + fn + mismatch)
F1        = 2PR / (P + R)
```

A `mismatch` is charged to both precision and recall — see
[../../docs/methodology.md](../../docs/methodology.md#field-level-extraction-kie). This makes the
numbers stricter than benchmarks that only score non-empty predictions against exact matches;
they are not directly comparable.

Equality is field-type aware (strict string, accent-insensitive loose string, ISO date, numeric
with epsilon, score, enum) — see [field-types.md](field-types.md).

Results are reported **raw and normalised**. Normalisation forgives exactly three cosmetic
differences, frozen before scoring: `int` vs `float`, collapsed whitespace inside `source_text`,
and `null` vs `0.0` on three named line-item numeric fields. Implementation:
[../../scripts/kie_normalizer.py](../../scripts/kie_normalizer.py).

## Ground truth, and how it can be wrong

The corpus is bootstrapped from production extraction traces and then **corrected by hand**,
field by field. This is cheap to start and has one dangerous property:

> ⚠️ **Self-baseline bias.** If the ground truth was seeded from model *A*'s output and only
> partially corrected, model *A* will score near-perfectly against it while model *B* is charged
> for every difference — including the ones where *B* is right.

We have hit this. An early comparison scored the incumbent at **F1 = 1.000**, which is not a
plausible number for this task; a later run of the same model against the *corrected* ground truth
scored **0.975**. Both numbers are in this repository, and the gap between them is a measure of
how much correction the ground truth needed, not of model improvement.

Consequences we now hold to:

- A score of 1.000 is treated as evidence of a ground-truth problem, not a model result.
- Comparisons across dates are only valid within a stated ground-truth version.
- Where a field's ground truth is genuinely disputed, it is excluded from **every** arm of the
  comparison and named in the report.

## Corpus

| | |
|---|---|
| Size | 25–34 scored units (documents split into header / items sub-runs) for model comparisons; a separate 100-document corpus for the counterparty gate |
| Language mix | Hungarian majority, plus English invoices from foreign SaaS and logistics suppliers |
| Provenance | Real customer documents — **not published** ([data policy](../../docs/data-policy.md)) |
| Sampling | Deterministic replay of stored production requests, `temperature = 0`, identical input for every arm |

Synthetic, fictional examples with the same structure are in [samples/](samples/).

## Known limits

- **Small.** 25–34 scored units resolves large differences, not small ones. Treat sub-point F1
  differences as noise unless a paired significance test says otherwise.
- **Composition.** The corpus over-represents foreign SaaS invoices relative to our production
  mix, because those are what a generic test tenant accumulates. This is precisely what hid the
  counterparty failure mode for one round.
- **Item scoring is all-or-nothing per array.** A single wrong line item fails the whole
  `invoice_items` comparison for that document. This is deliberate — a partially correct line-item
  array is not usable for bookkeeping — but it makes item F1 much more volatile than header F1.
- **Confidence values are not scored.** Models emit them; we ignore them in scoring.

## Used by

- [gemma4-vs-qwen36-json-kie](../../experiments/2026-04-30-gemma4-vs-qwen36-json-kie/)
- [qwen36-fp8-vs-nvfp4-quality](../../experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/)
- [qwen35-122b-nvfp4-bringup-gb10](../../experiments/2026-05-22-qwen35-122b-nvfp4-bringup-gb10/)

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
