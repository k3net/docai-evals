#!/usr/bin/env python3
"""McNemar's exact test on the counterparty-role gate, for two runs over the same documents.

Why this and not a difference of proportions: the two models see the *same* documents, so the
comparison is paired. McNemar looks only at the documents where the two disagree — the ones where
both are right or both are wrong carry no information about which model is better.

    n10 = baseline wrong, candidate right
    n01 = baseline right, candidate wrong
    two-sided exact p = 2 * P(X <= min(n01, n10)) under X ~ Binomial(n01 + n10, 0.5)

On a 100-document corpus this routinely turns a confident-looking ordering into "not
distinguishable". That is the point. In our own quantisation comparison, three candidates ranked
12 / 16 / 18 errors — and every pairwise test came back p >> 0.05, so the ranking was noise even
though all three were significantly worse than the baseline.

Usage:
    ./mcnemar.py --own-tax 87654321-2-08 --own-name-hint "demó kereskedelmi" \\
                 runs/baseline runs/candidate

Options are shared with counterparty_guard.py, which supplies the per-document verdicts.

Part of DocAI Evals — https://docai.hu
"""
import os
import sys
from math import comb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import counterparty_guard as guard  # noqa: E402


def exact_two_sided_p(n01, n10):
    n = n01 + n10
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(0, min(n01, n10) + 1))
    return min(2 * tail / 2 ** n, 1.0)


def main():
    ap = guard.build_parser()
    ap.description = __doc__
    args = ap.parse_args()
    if len(args.runs) != 2:
        sys.exit("give exactly two run directories: baseline candidate")

    import re
    own_tax = re.sub(r"\D", "", args.own_tax)
    hints = [h.lower() for h in args.own_name_hint]

    base, cand = (guard.load_run(r) for r in args.runs)
    docs = sorted(set(base) & set(cand))
    if not docs:
        sys.exit("the two runs share no documents")

    n11 = n10 = n01 = n00 = 0
    for doc in docs:
        a = guard.flag(base[doc], own_tax, hints, args.tax_field, args.name_field)
        b = guard.flag(cand[doc], own_tax, hints, args.tax_field, args.name_field)
        a = bool(a[0]) if a else False
        b = bool(b[0]) if b else False
        n11 += a and b
        n10 += a and not b
        n01 += b and not a
        n00 += not a and not b

    p = exact_two_sided_p(n01, n10)
    n = n01 + n10
    chi2 = ((abs(n01 - n10) - 1) ** 2 / n) if n else 0.0

    print(f"n={len(docs)}   baseline errors: {n11 + n10}   candidate errors: {n11 + n01}")
    print(f"  both: {n11}   baseline only: {n10}   candidate only: {n01}   neither: {n00}")
    print(f"McNemar exact two-sided p = {p:.5f}   (continuity-corrected chi2 ~ {chi2:.2f})")
    print("  p < 0.05 -> the difference is unlikely to be sampling noise;"
          " p >= 0.05 -> report the point estimates, not an ordering.")


if __name__ == "__main__":
    main()
