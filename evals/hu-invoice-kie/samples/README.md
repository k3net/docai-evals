# Synthetic samples

Fictional invoices written for this repository. No real company, person, tax number, bank account
or transaction appears here — the tax numbers are structurally valid but unallocated, and the
company names are invented.

They exist so that the **shape** of the task is inspectable without any customer data: the field
set, the JSON structure, Hungarian formatting conventions, and the own-vs-partner distinction that
the [counterparty-role](../../counterparty-role/) gate is built around.

They are **not** a benchmark. Two documents cannot rank models, and results on them are not
comparable to anything in [experiments/](../../../experiments/).

| Sample | What it exercises |
|---|---|
| [synthetic-hu-domestic-invoice](synthetic-hu-domestic-invoice/) | Incoming domestic invoice, 27 % VAT, two line items, our company is the buyer |
| [synthetic-eu-supplier-invoice](synthetic-eu-supplier-invoice/) | EU supplier, reverse charge (0 % VAT), foreign currency, EU VAT number format, no payment deadline stated |

Each directory contains:

```text
document.txt         # what the OCR stage would hand to the model
ground_truth.json    # the expected extraction, per schemas/ground-truth.schema.json
```

## Things these two samples deliberately cover

- **`null` as a correct answer.** The EU sample has no stated payment deadline. The correct
  `payment_date` is `null`; a computed date is a false positive
  ([why](../field-types.md#why-dates-are-normalised-but-never-computed)).
- **Two tax-number formats.** National (`12345678-2-42`) and EU VAT (`DE812345678`). They are
  different strings and are scored strictly.
- **Reverse charge.** `total_vat_amount` is `0.0`, not `null`, and `vat_percentage` on the line is
  `0.0` — the invoice states it.
- **Own-company recognition.** In both samples our own company appears on the document, in the
  buyer block. `own_name_score` and `own_taxnumber_score` are non-zero and `partner_*` holds the
  *other* company. A model that swaps them scores badly on several fields at once and trips the
  counterparty gate.
- **Line-item name padding.** The domestic sample has a line whose document text carries a period
  suffix; `name` in ground truth is the product name only, `source_text` keeps the raw line.

---

*Part of [DocAI Evals](../../../README.md) · [docai.hu](https://docai.hu)*
