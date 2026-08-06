#!/usr/bin/env python3
"""Counterparty-role gate: did the model put OUR OWN company in the partner slot?

This is the deterministic business gate described in docs/methodology.md. It needs no LLM judge
and no manual review: take the extracted partner tax number and partner name, and check them
against the tenant's own identity. If they match, the model has confused the two parties on the
invoice — which flips the direction of the transaction downstream.

It is worth running precisely because aggregate F1 hides it. On our corpus, two models within
0.001 F1 of each other differed by more than 2x on this gate.

The tenant's own identity is a PARAMETER, never a literal in published code (see
docs/data-policy.md). Supply it on the command line:

    ./counterparty_guard.py --own-tax 87654321-2-08 \\
                            --own-name-hint "demó kereskedelmi" --own-name-hint "demo kereskedelmi" \\
                            runs/baseline runs/candidate

Name hints are lowercase substrings of the tenant's own company name — invoices spell it
inconsistently ("Demó Kereskedelmi Zrt.", "DEMO KERESKEDELMI ZRT", "Demo Kereskedelmi Ltd"), so a
substring test catches more than exact matching. Tax-number matching is digits-only and
prefix-based, which makes it insensitive to national vs EU VAT formatting.

Input format — one directory per run, containing one file per document named `*__header.json`:

    {"vllm_response": {"output_text": "<the model's strict-JSON output as a string>"}}

Output is aggregate counts only. Never print or export per-document results from a private
corpus.

Exit code is 0 unless a run directory could not be read.

Part of DocAI Evals — https://docai.hu
"""
import argparse
import glob
import json
import os
import re
import sys


def field_value(obj, key):
    """KIE output is {field: {value, confidence}}; tolerate a bare value too."""
    v = (obj or {}).get(key)
    return v.get("value") if isinstance(v, dict) else v


def load_run(run_dir):
    """doc_id -> parsed model output (or None if the output was not valid JSON)."""
    out = {}
    for path in sorted(glob.glob(os.path.join(run_dir, "*__header.json"))):
        with open(path) as fh:
            record = json.load(fh)
        doc = os.path.basename(path).split("_")[0]
        try:
            out[doc] = json.loads(record["vllm_response"]["output_text"])
        except Exception:
            out[doc] = None      # invalid JSON is not a gate hit, but it is not a pass either
    return out


def flag(pred, own_tax_digits, own_name_hints,
         tax_field="partner_taxnumber", name_field="partner_name"):
    """(flagged, matched_by_tax, matched_by_name) or None if the output was unusable."""
    if not pred:
        return None
    tax = re.sub(r"\D", "", str(field_value(pred, tax_field) or ""))
    by_tax = tax.startswith(own_tax_digits) if (tax and own_tax_digits) else False
    name = str(field_value(pred, name_field) or "").lower()
    by_name = any(hint in name for hint in own_name_hints)
    return (by_tax or by_name), by_tax, by_name


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run directories")
    ap.add_argument("--own-tax", default="", help="the tenant's own tax number (any formatting)")
    ap.add_argument("--own-name-hint", action="append", default=[], metavar="SUBSTRING",
                    help="lowercase substring of the tenant's own company name; repeatable")
    ap.add_argument("--tax-field", default="partner_taxnumber")
    ap.add_argument("--name-field", default="partner_name")
    ap.add_argument("--own-score-field", default="own_name_score",
                    help="field that should be non-zero when the model recognised our own company")
    return ap


def main():
    args = build_parser().parse_args()
    own_tax = re.sub(r"\D", "", args.own_tax)
    hints = [h.lower() for h in args.own_name_hint]
    if not own_tax and not hints:
        sys.exit("give at least one of --own-tax / --own-name-hint")

    for run in args.runs:
        preds = load_run(run)
        if not preds:
            sys.exit(f"no *__header.json files in {run}")
        results = {doc: flag(p, own_tax, hints, args.tax_field, args.name_field)
                   for doc, p in preds.items()}
        flagged = [doc for doc, r in results.items() if r and r[0]]
        both = sum(1 for doc in flagged if results[doc][1] and results[doc][2])
        collapsed = sum(1 for doc in flagged
                        if field_value(preds[doc], args.own_score_field) in (0, 0.0))
        unusable = sum(1 for r in results.values() if r is None)
        print(f"{os.path.basename(run.rstrip('/')):40s} docs={len(preds):3d}  "
              f"flagged={len(flagged):3d}  (tax and name agree: {both})  "
              f"{args.own_score_field}=0 among them: {collapsed}  unusable_output={unusable}")


if __name__ == "__main__":
    main()
