#!/usr/bin/env python3
"""Raw and normalised KIE F1 for one or more runs, scored by identical code.

Both numbers are reported side by side on purpose:

  * raw        — every difference counts, including JSON formatting noise
  * normalised — cosmetic differences (kie_normalizer v1.0) are forgiven

The gap between them tells you how much of an apparent quality difference was really about
formatting. In one of our own comparisons a full point of raw F1 difference turned out to be
entirely cosmetic; in another, most of it survived normalisation and was real.

F1 definition (see docs/methodology.md):

    precision = tp / (tp + fp + mismatch)
    recall    = tp / (tp + fn + mismatch)

A mismatch is charged to both sides: a wrong tax number is both a false claim and a missed fact.

Input format — one directory per run, containing one JSON file per scored document:

    {
      "compare": {
        "fields": [
          {"field": "partner_name", "outcome": "tp|fp|fn|mismatch|tn",
           "gt_value": ..., "pred_value": ...},
          ...
        ]
      }
    }

`summary.json` in a run directory is skipped. Document identity is taken from the filename up to
the first underscore, which is what --exclude matches against.

Usage:
    ./score_kie.py runs/20260716__baseline runs/20260716__candidate
    ./score_kie.py --exclude doc70:own_taxnumber_score runs/*

Excluding a field is legitimate when its ground truth is genuinely disputed — but it must be
excluded for EVERY run in the comparison (this script enforces that) and named in the report.

Part of DocAI Evals — https://docai.hu
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kie_normalizer import VERSION, normalize  # noqa: E402

OUTCOME_INDEX = {"tp": 0, "fp": 1, "fn": 2, "mismatch": 3}


def f1(tp, fp, fn, mm):
    p = tp / (tp + fp + mm) if (tp + fp + mm) else 0.0
    r = tp / (tp + fn + mm) if (tp + fn + mm) else 0.0
    return 2 * p * r / (p + r) if (p + r) else 0.0


def score(run, exclude):
    """Returns (raw_f1, normalised_f1, raw_counts, normalised_counts, n_reclassified)."""
    raw = [0, 0, 0, 0]   # tp, fp, fn, mismatch
    nrm = [0, 0, 0, 0]
    reclassified = 0
    for path in sorted(glob.glob(os.path.join(run, "*.json"))):
        if os.path.basename(path) == "summary.json":
            continue
        with open(path) as fh:
            doc_result = json.load(fh)
        doc = os.path.basename(path).split("_")[0]
        for fld in doc_result["compare"]["fields"]:
            if (doc, fld["field"]) in exclude:
                continue
            idx = OUTCOME_INDEX.get(fld["outcome"])
            if idx is None:
                continue  # tn and anything unknown are not scored
            raw[idx] += 1
            if fld["outcome"] == "mismatch":
                # a mismatch may be purely cosmetic — re-evaluate it after normalisation
                if normalize(fld.get("gt_value"), fld["field"]) == normalize(fld.get("pred_value"), fld["field"]):
                    nrm[0] += 1
                    reclassified += 1
                else:
                    nrm[3] += 1
            else:
                nrm[idx] += 1
    return f1(*raw), f1(*nrm), raw, nrm, reclassified


def parse_exclude(values):
    out = set()
    for item in values or []:
        if ":" not in item:
            raise SystemExit(f"--exclude expects doc:field, got {item!r}")
        doc, field = item.split(":", 1)
        out.add((doc, field))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run directories")
    ap.add_argument("--exclude", action="append", metavar="DOC:FIELD",
                    help="exclude a field from scoring in ALL runs (disputed ground truth)")
    args = ap.parse_args()

    exclude = parse_exclude(args.exclude)
    print(f"# normaliser: kie_normalizer v{VERSION}")
    if exclude:
        print("# excluded from every run: " + ", ".join(f"{d}/{f}" for d, f in sorted(exclude)))
    print()
    print(f"{'run':32s} {'raw F1':>9s} {'norm F1':>9s}  {'raw mm':>8s} {'real mm':>9s} {'cosmetic':>10s}")
    for run in args.runs:
        raw_f1, nrm_f1, raw, nrm, reclassified = score(run, exclude)
        label = os.path.basename(run.rstrip("/")).split("__")[-1]
        print(f"{label:32s} {raw_f1:9.4f} {nrm_f1:9.4f}  {raw[3]:8d} {nrm[3]:9d} {reclassified:10d}")


if __name__ == "__main__":
    main()
