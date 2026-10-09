"""A szemantikus duplikátum-szabály kalibrálása Dani átnézett itemein (2026-10-04).

Az első 99 átnézett itemben a 12 javítás/kétértelmű jelölés nagy része katalógus-duplikátum: a valódi cikk
mellett egy másik néven, gyakran más alkategóriában ugyanaz a termék is opció („Mozzarella ball 125 g” /
„Mozzarella golyó 125 g”). Ezt sem az S1 név-dedup, sem az S8 lexikai szabálya nem látja. Jelölt szabály:
az opció duplikátuma a valódi cikknek, ha bge-m3 koszinuszuk ≥ t, ÉS a szám/mértékegység-tokenjeik nem
ütköznek (az egyik halmaza része a másikénak). Kimenet: küszöbönként a fogás az átnézett hibákon, a téves
riasztás az átnézett jókon, és az érintett itemek aránya a val/teszten.

  python3 eszkozok/duplikatum_kalibral.py --gen adat/f1 --dontesek adat/f1/atnezes/dontesek_100.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json  # noqa: E402
from duplikatum import nums  # noqa: E402
from jeloltek import Embedder  # noqa: E402

SPLITS = ["val-belso", "val-szallito", "T-belso", "T-szallito", "T-kozeli", "T-tavoli"]
KUSZOBOK = [0.80, 0.85, 0.88, 0.90, 0.93, 0.95]


def compatible(a: str, b: str) -> bool:
    na, nb = set(nums(a)), set(nums(b))
    return na <= nb or nb <= na


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default="adat/f1")
    ap.add_argument("--dontesek", default="adat/f1/atnezes/dontesek_100.json")
    ap.add_argument("--out", default="eredmenyek/F1/audit/duplikatum_kalibral.json")
    args = ap.parse_args()
    gen = EXP / args.gen
    arts = read_jsonl(gen / "s1_katalogus.jsonl")
    idx = {a["id"]: i for i, a in enumerate(arts)}
    v = Embedder()([a["name"] for a in arts], max_len=64)
    sim = (v @ v.T).float().cpu()

    def best_dup(it: dict) -> float:
        """A valódi cikkel számkompatibilis opciók legnagyobb koszinusza (0, ha nincs)."""
        a = it["meta"]["article"]
        if a not in idx:
            return 0.0
        name = arts[idx[a]]["name"]
        return max((float(sim[idx[a], idx[o["id"]]]) for o in it["options"]
                    if o["id"] is not None and o["id"] != a and o["id"] in idx and compatible(name, o["text"])),
                   default=0.0)

    items = {sp: read_jsonl(gen / f"items_{sp}.jsonl") for sp in SPLITS}
    by_id = {it["id"]: it for its in items.values() for it in its}
    dec = json.load(open(EXP / args.dontesek))["dontesek"]
    rev = []
    for i, d in dec.items():
        hiba = d.get("masodik") in ("gold_hibas", "ketertelmu") or d.get("valasz") == "K"
        if d.get("valasz") == "N" and not hiba:
            continue
        it = by_id[i]
        rev.append({"id": i, "hiba": hiba, "x": it["gold"] is None, "s": best_dup(it)})
    res = {"atnezett": len(rev), "hiba": sum(r["hiba"] for r in rev), "kuszob": {}}
    for t in KUSZOBOK:
        c = Counter()
        for sp, its in items.items():
            for it in its:
                if it["meta"].get("ketertelmu"):
                    continue
                c["pontozott"] += 1
                if best_dup(it) >= t:
                    c["erintett"] += 1
                    c["erintett_X" if it["gold"] is None else "erintett_nemX"] += 1
        res["kuszob"][str(t)] = {
            "fogott_hiba": sum(r["hiba"] and r["s"] >= t for r in rev),
            "teves_riasztas_jo": sum(not r["hiba"] and r["s"] >= t for r in rev),
            "jo": sum(not r["hiba"] for r in rev),
            **{k: c[k] for k in ("pontozott", "erintett", "erintett_X", "erintett_nemX")},
            "erintett_arany": round(c["erintett"] / max(1, c["pontozott"]), 4),
        }
    res["hiba_itemek"] = [[r["id"], round(r["s"], 3), "X" if r["x"] else "-"]
                          for r in sorted(rev, key=lambda r: -r["s"]) if r["hiba"]]
    write_json(EXP / args.out, res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
