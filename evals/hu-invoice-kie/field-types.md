# Field types and equality rules

Every scored field has a type, and the type decides what "equal" means. Getting this wrong in
either direction is expensive: too strict and you spend review time on formatting noise, too loose
and you stop noticing real errors.

| Type | Example fields | Equality rule |
|---|---|---|
| `string_strict` | `invoice_number`, `partner_taxnumber`, `partner_bank_account`, `basenumber` | trim, then exact match |
| `string_loose` | `partner_name`, `partner_address`, `partner_person_name` | trim, lowercase, accent-insensitive |
| `number_strict` | `total_net_amount`, `total_vat_amount`, `total_gross_amount` | float comparison, epsilon 0.01 |
| `date_iso` | `invoice_date`, `payment_date`, `delivery_date`, `fulfillment_date` | normalised to ISO 8601, then exact |
| `score` | `own_name_score`, `own_taxnumber_score`, `own_address_score` | treated as boolean: 0.0 vs non-zero |
| `enum` | `currency`, `language`, `payment_method` | exact match against the allowed set |
| `array_object` | `invoice_items` | element-wise comparison of the whole array; any difference fails the field |

## Why identifiers are strict

Tax numbers, bank accounts and invoice numbers are join keys. `12345678-2-42` and `HU12345678`
identify the same company to a human and are *different values* to every downstream system — the
tax-authority matcher, the ledger, the partner deduplicator. Scoring them as equal would hide a
class of error that costs real reconciliation work.

Where both forms are legitimately acceptable, the ground truth says so explicitly via
`alternatives` (see [../../schemas/ground-truth.schema.json](../../schemas/ground-truth.schema.json))
rather than by loosening the type.

## Why names are loose

`Példa Logisztika Kft.` and `PELDA LOGISZTIKA KFT` are the same company, and Hungarian documents
are inconsistent about case and — in badly encoded PDFs — about accents. Accent-insensitive
comparison is the pragmatic choice.

It has a cost worth naming: it will not catch a model that quietly drops a diacritic. One of our
comparisons found a model returning a company name with `ő` rendered as `ô` — the wrong character,
still valid Unicode, and a `string_loose` pass. We accept this, because the alternative — charging
every encoding artefact as a content error — produced worse signal.

## Why `score` fields are booleans

`own_*_score` fields express how strongly the document's *own-company* block matches the tenant's
registered identity. Models disagree about calibration (0.8 vs 1.0) far more than about direction,
and only the direction drives product behaviour. Scoring the exact value would measure calibration
noise; scoring zero-vs-non-zero measures the decision.

## Why dates are normalised but never computed

Date fields are extracted, **never derived**. If a payment deadline is not written on the invoice,
the correct answer is `null` — not the invoice date plus the usual terms, and not "today". A
computed date that happens to be right is still a hallucination, and it will be wrong on the
invoice where the terms differ.

This is a hard product rule in DocAI, and the eval enforces it: an invented date scores as a false
positive against a `null` ground truth.

## Line items

`invoice_items` is an array of objects:

```json
{
  "name": "Szállítási díj — Budapest / Győr",
  "quantity": 2.0,
  "unit": "db",
  "unit_price": 25000.0,
  "line_netto_total": 50000.0,
  "line_vat_total": 13500.0,
  "vat_percentage": 27.0,
  "source_text": "Szállítási díj Budapest / Győr   2 db   25 000 Ft"
}
```

Two cosmetic rules apply here and nowhere else, both frozen in
[../../scripts/kie_normalizer.py](../../scripts/kie_normalizer.py):

- `source_text` whitespace is collapsed before comparison — line-layout whitespace is an OCR
  artefact, not a model decision;
- `null` and `0.0` are equal on `line_netto_total`, `line_vat_total` and `vat_percentage` — "no
  VAT stated" and "VAT is zero" are the same economic fact on a line item.

Neither rule applies to `name`, and neither applies to header fields.

The most common real failure in this field is **name padding**: the model copies the whole
document line, including the billing period and the customer, into `name` — for example
`"Éves előfizetés – <ügyfél> 2026. május – 2028. május"` instead of `"Éves előfizetés"`. It is a
mismatch, and it should be: the padded name breaks per-product aggregation downstream.

---

*Part of [DocAI Evals](../../README.md) · [docai.hu](https://docai.hu)*
