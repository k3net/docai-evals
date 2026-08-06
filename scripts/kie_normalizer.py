#!/usr/bin/env python3
"""Cosmetic normaliser for KIE comparison — v1.0.

The rule set is exactly this, and nothing more. It was frozen BEFORE the comparison it was
written for was scored, which is the only reason the normalised numbers are worth anything:

  1. int -> float:            1.0 == 1,  0.0 == 0     (every numeric value becomes float)
  2. source_text whitespace:  \\s+ -> single space, trimmed   (ONLY on the 'source_text' key)
  3. null -> 0.0:             ONLY on these numeric fields:
                              line_netto_total, line_vat_total, vat_percentage

Every other field is compared with strict equality (the harness default).
The normaliser is idempotent and deterministic.

Why the third rule is scoped so narrowly: on a line item, "no VAT stated" and "VAT is zero" are
the same economic fact, and models legitimately disagree about how to express it. On a partner
name, null and "" are not the same fact at all — so the rule does not apply there.

Usage as a library:
    from kie_normalizer import normalize, equal_after_norm
    equal_after_norm(gt_value, pred_value, field_name)

Part of DocAI Evals — https://docai.hu
"""
import re

VERSION = "1.0"
NULL_TO_ZERO_FIELDS = {"line_netto_total", "line_vat_total", "vat_percentage"}


def _norm_scalar(v):
    # int -> float, so that 1 == 1.0; booleans are left alone (bool is a subclass of int)
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    return v


def normalize(value, field_name=None):
    """Recursive normalisation. field_name drives the null -> 0.0 rule."""
    if isinstance(value, list):
        return [normalize(x, field_name) for x in value]
    if isinstance(value, dict):
        # inside a dict, each key is the field_name for its own value
        return {k: normalize(x, k) for k, x in value.items()}
    # whitespace collapse, only on source_text
    if field_name == "source_text" and isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    # null -> 0.0, only on the named numeric fields
    if value is None and field_name in NULL_TO_ZERO_FIELDS:
        return 0.0
    return _norm_scalar(value)


def equal_after_norm(gt, pred, field_name=None):
    """True if the two values are equal once cosmetic differences are normalised away."""
    return normalize(gt, field_name) == normalize(pred, field_name)


if __name__ == "__main__":
    assert normalize(1) == 1.0
    assert normalize([{"quantity": 1, "source_text": "a\n b"}]) == [{"quantity": 1.0, "source_text": "a b"}]
    assert normalize(None, "line_vat_total") == 0.0
    assert normalize(None, "partner_name") is None      # not a named numeric field -> stays null
    assert equal_after_norm("12345678-2-42", "12345678-2-42", "partner_taxnumber")
    assert not equal_after_norm("12345678-2-42", "HU12345678", "partner_taxnumber")
    print(f"kie_normalizer v{VERSION} — self-test OK")
