# Worked example: a flagged document

Fully synthetic. The invoice is
[synthetic-hu-domestic-invoice](../../hu-invoice-kie/samples/synthetic-hu-domestic-invoice/) from
the KIE suite: our own company is **Demó Kereskedelmi Zrt.** (`87654321-2-08`, the buyer), and the
partner is **Példa Logisztika Kft.** (`12345678-2-42`, the supplier).

## Correct extraction

```json
{
  "partner_name":        {"value": "Példa Logisztika Kft.", "confidence": 0.96},
  "partner_taxnumber":   {"value": "12345678-2-42",         "confidence": 0.97},
  "own_name_score":      {"value": 1.0},
  "own_taxnumber_score": {"value": 1.0}
}
```

Guard verdict: **not flagged.** The partner tax number does not start with `87654321`, and the
partner name contains no own-name hint.

## Confused extraction

```json
{
  "partner_name":        {"value": "Demó Kereskedelmi Zrt.", "confidence": 0.94},
  "partner_taxnumber":   {"value": "87654321-2-08",          "confidence": 0.95},
  "own_name_score":      {"value": 0.0},
  "own_taxnumber_score": {"value": 0.0}
}
```

Guard verdict: **flagged, by both signals.**

```text
partner_taxnumber -> digits "8765432108" starts with own digits "8765432108"  -> tax match
partner_name      -> "demó kereskedelmi zrt." contains hint "demó kereskedelmi" -> name match
own_name_score = 0.0                                                            -> role collapse
```

Note the confidence values: **0.94 and 0.95**. The model is not hedging. This is what makes the
failure mode dangerous in production — nothing in the output signals that anything went wrong,
which is precisely why the check has to be external and deterministic.

## Running it

```bash
python3 ../../../scripts/counterparty_guard.py \
    --own-tax 87654321-2-08 \
    --own-name-hint "demó kereskedelmi" --own-name-hint "demo kereskedelmi" \
    runs/<your-run-directory>
```

Both accented and unaccented hints are supplied on purpose: badly encoded PDFs lose diacritics,
and the guard does exact substring matching on a lowercased string.

## What follows from a flag

A flagged document is not automatically a model error — it is a document that needs the
authoritative check (see the [suite README](../README.md#second-stronger-ground-truth)). Two things
must never happen: shipping the extraction as-is, and quietly counting the flag as a false alarm
because the aggregate F1 looked fine.

---

*Part of [DocAI Evals](../../../README.md) · [docai.hu](https://docai.hu)*
