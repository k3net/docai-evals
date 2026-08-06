# Eval suite: counterparty role

On every invoice there are two companies. One of them is you. Deciding which is which is the
single most consequential extraction decision in a document-AI pipeline for accounting — and it is
the one an aggregate F1 score is worst at seeing.

**Suite version:** 1.0 · **Type:** deterministic business gate · **Significance test:** McNemar's
exact test

## The failure mode

The model fills `partner_name` and `partner_taxnumber` with the *tenant's own* company instead of
the other party. Everything downstream inherits it:

- the invoice direction flips — an incoming supplier invoice is booked as outgoing revenue;
- tax-authority matching fails, because the record it should reconcile with names a different
  counterparty;
- partner-level analytics silently attribute turnover to the wrong company;
- and the `own_*_score` fields collapse to zero, because the model no longer recognises its own
  company anywhere on the document.

None of this is caught by JSON validity, and none of it is caught by a schema check. The output is
perfectly well-formed and completely wrong.

## Why it needs its own instrument

In our own measurements, a candidate model came within **0.001 normalised F1** of the baseline on
[hu-invoice-kie](../hu-invoice-kie/) — and made **more than twice as many** counterparty errors.
The aggregate metric was not lying; it was averaging one catastrophic field group into
twenty-odd benign ones.

There is a second reason, and it is about corpus composition rather than metric design. The
failure only appears when the document is *about* companies the model has to distinguish. A test
corpus of English SaaS invoices, where the tenant's own company barely resembles anything on the
page, shows nothing. Swap in real Hungarian invoices from an actual customer — where the own
company appears in the header, the footer, the stamp, and half the line items — and the error rate
becomes measurable immediately.

> The lesson generalises: **a capability that only fails on representative data will only be
> measured on representative data.**

## How the gate works

Deterministic, no LLM judge, no manual review. For each document, take the extracted partner
fields and test them against the tenant's own identity:

| Signal | Rule |
|---|---|
| Tax number | strip non-digits from `partner_taxnumber`; flag if it starts with the tenant's own digits |
| Name | lowercase `partner_name`; flag if it contains any own-name hint substring |

A document is flagged if **either** matches. The high-confidence subset is where both match.

Implementation: [../../scripts/counterparty_guard.py](../../scripts/counterparty_guard.py). The
tenant's identity is passed on the command line and never hard-coded — see
[../../docs/data-policy.md](../../docs/data-policy.md).

```bash
python3 ../../scripts/counterparty_guard.py \
    --own-tax 87654321-2-08 --own-name-hint "demó kereskedelmi" --own-name-hint "demo kereskedelmi" \
    runs/baseline runs/candidate
```

### Substring matching, and why it is deliberately crude

Invoices spell company names inconsistently — legal form abbreviated or not, accents present or
stripped, trade name instead of registered name. A substring test over a couple of hints catches
more real confusions than exact matching, at the price of some false flags.

That price is quantified rather than assumed. On our 100-document run the guard flagged 18
documents for the candidate model, while an authoritative ground truth (the partner company
actually linked to each document in the database) confirmed 16 of them on the 82-document subset
where the partner is verifiably not our own company. The two extra flags were **foreign partners**
whose tax field held a SWIFT/BIC code or nothing at all — cases the authoritative check could not
verify either way, and where the model was in fact still wrong.

So: the guard's count is the wider number, the database-verified count is the conservative lower
bound, and both get published.

## Second, stronger ground truth

Where the document is linked in our system to a real partner company, we can verify the gate
against that link instead of against the model's own output. This removes the guard's heuristic
entirely:

```text
subset:  documents where the linked partner is NOT our own company
metric:  share of those documents where the model named our own company as the partner
```

This is the number we quote in decisions, because it cannot be argued with on heuristic grounds.

## Statistical treatment

Both models see the same documents, so comparisons are paired: **McNemar's exact test**
([../../scripts/mcnemar.py](../../scripts/mcnemar.py)). On a 100-document corpus this is what
stops a plausible-looking ordering from becoming a finding.

Worked example from our quantisation round — three candidates flagged 12, 16 and 18 documents
against a baseline of 7:

| Comparison | p | Reading |
|---|---|---|
| baseline vs candidate A (18) | 0.019 | significantly worse |
| baseline vs candidate B (16) | 0.049 | significantly worse |
| baseline vs candidate C (12) | 0.267 | not established |
| A vs C (the two extremes) | 0.238 | **not distinguishable** |
| B vs C | 0.481 | not distinguishable |
| A vs B | 0.832 | not distinguishable |

The candidates could not be told apart from each other, even though two of them were clearly worse
than the baseline. The defensible claim was therefore about the *class* of quantisation, not about
a dose-response along aggressiveness — and the tidier story we went in expecting had to be dropped.

## Known limits

- **Heuristic flagging** over-counts slightly on foreign partners; the database-verified subset is
  the conservative number.
- **One tenant.** The published run covers a single customer's document mix. Another tenant with
  different suppliers would produce different absolute rates; the *relative* model comparison is
  what transfers.
- **`n = 100`.** Enough to separate a 2× effect from noise, not enough to rank candidates that sit
  within a few documents of each other. This is stated in every result that uses it.
- **Detects one direction only.** Putting the partner into the own-company slot is a different
  error and is not measured here.

## Samples

[samples/](samples/) contains a worked, fully synthetic example of a flagged document: the same
invoice extracted correctly and incorrectly, with the guard's reasoning spelled out.

## Used by

- [invoice-counterparty-role](../../experiments/2026-07-16-invoice-counterparty-role/) — the
  measurement that produced the numbers above
- [qwen36-fp8-vs-nvfp4-quality](../../experiments/2026-07-16-qwen36-fp8-vs-nvfp4-quality/) — where
  it overruled the F1 result

Story version (Hungarian):
[Negyven százalékkal gyorsabb, és mégsem váltunk](https://docai.hu/blog/nvfp4-kvantalas-miert-nem-valtottunk)

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu) · [Blog](https://docai.hu/blog)*
