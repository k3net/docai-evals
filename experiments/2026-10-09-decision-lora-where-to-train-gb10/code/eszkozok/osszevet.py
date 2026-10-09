"""Két kiolvasás-fájl soronkénti összevetése ((id, perm) párosítással).

Kimenet: top-címke egyezés, bájtra azonos címke-logprob sorok aránya, a címke-
logprobok max/átlagos abszolút eltérése, a goldra jutó szűkített valószínűség
átlagos eltérése, és ugyanez külön az X-itemeken. Ugyanaz a szkript szolgál a
példányon belüli reprodukálhatóságra (K0a), a HF↔vLLM egyezésre (K0d) és a
LoRA-hatás mérésére (K0c: alap vs. adapter).

Példa: python3 eszkozok/osszevet.py a.jsonl b.jsonl --out c.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402


def compare(a_rows: list[dict], b_rows: list[dict]) -> dict:
    b = {(r["id"], r["perm"]): r for r in b_rows}
    n = agree = same_bytes = 0
    max_abs = sum_abs = sum_gold = 0.0
    n_lab = 0
    x_n = x_agree = 0
    a_acc = b_acc = 0
    for ra in a_rows:
        rb = b.get((ra["id"], ra["perm"]))
        if rb is None:
            continue
        n += 1
        agree += ra["pred"] == rb["pred"]
        a_acc += ra["pred"] == ra["gold_label"]
        b_acc += rb["pred"] == rb["gold_label"]
        same_bytes += all(repr(ra["label_logprobs"][k]) == repr(rb["label_logprobs"].get(k)) for k in ra["label_logprobs"])
        for k, v in ra["label_logprobs"].items():
            d = abs(v - rb["label_logprobs"][k])
            max_abs = max(max_abs, d)
            sum_abs += d
            n_lab += 1
        g = ra["gold_label"]
        sum_gold += abs(ra["probs"][g] - rb["probs"][g])
        if g == "X":
            x_n += 1
            x_agree += ra["pred"] == rb["pred"]
    return {
        "n_paired": n,
        "top_label_agreement": agree / n if n else None,
        "rows_bytewise_identical": same_bytes / n if n else None,
        "label_logprob_max_abs_diff": max_abs,
        "label_logprob_mean_abs_diff": sum_abs / n_lab if n_lab else None,
        "gold_prob_mean_abs_diff": sum_gold / n if n else None,
        "x_items": x_n, "x_top_label_agreement": x_agree / x_n if x_n else None,
        "acc_a": a_acc / n if n else None, "acc_b": b_acc / n if n else None,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = compare(read_jsonl(Path(args.a)), read_jsonl(Path(args.b)))
    res.update({"a": args.a, "b": args.b})
    write_json(Path(args.out), res)
    print(json.dumps(res))


if __name__ == "__main__":
    main()
