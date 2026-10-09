"""Szemantikus duplikátum-audit a katalógusra és a val/teszt itemekre (2026-10-04).

A runbook 4.2 S1 dedupot ír elő (normalizált név ÉS bge-m3 koszinusz > 0,95); a generátor csak a
normalizált nevet szűrte. Ez a szkript megméri, mennyi a családon kívüli közeli duplikátum, és hány
itemben van a gold mellett egy tőle (családon kívül) megkülönböztethetetlen opció — ezeket az S8
attribútum-alapú kétértelműség-szabálya nem látja.

  python3 eszkozok/duplikatum_audit.py --gen adat/f1 --out eredmenyek/F1/audit
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json  # noqa: E402
from jeloltek import Embedder  # noqa: E402

SPLITS = ["val-belso", "val-szallito", "T-belso", "T-szallito", "T-kozeli", "T-tavoli"]
KUSZOBOK = [0.90, 0.93, 0.95, 0.97]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", default="adat/f1")
    ap.add_argument("--out", default="eredmenyek/F1/audit")
    args = ap.parse_args()
    gen, out = EXP / args.gen, EXP / args.out
    arts = [a for a in read_jsonl(gen / "s1_katalogus.jsonl") if not a["catchall"]]
    idx = {a["id"]: i for i, a in enumerate(arts)}
    emb = Embedder()
    v = emb([a["name"] for a in arts], max_len=64)
    sim = (v @ v.T).float().cpu()
    sub = [a["path"] for a in arts]
    fam = [a["family"] for a in arts]
    res = {"cikk": len(arts), "parok": {}, "peldak": []}
    n = len(arts)
    for t in KUSZOBOK:
        cnt, arts_with = 0, set()
        for i in range(n):
            for j in range(i + 1, n):
                if sub[i] == sub[j] and fam[i] != fam[j] and sim[i, j] > t:
                    cnt += 1
                    arts_with |= {i, j}
        res["parok"][str(t)] = {"csaladon_kivuli_par": cnt, "erintett_cikk": len(arts_with),
                                "erintett_arany": round(len(arts_with) / n, 4)}
    # példák (0,95 felett)
    seen = 0
    for i in range(n):
        for j in range(i + 1, n):
            if seen < 25 and sub[i] == sub[j] and fam[i] != fam[j] and sim[i, j] > 0.95:
                res["peldak"].append([arts[i]["name"], arts[j]["name"], round(float(sim[i, j]), 3)])
                seen += 1
    # itemek: a gold mellett van-e családon kívüli, > küszöb hasonlóságú opció (és X-itemeknél: a valódi cikkhez)
    items_rep = defaultdict(Counter)
    for sp in SPLITS:
        for it in read_jsonl(gen / f"items_{sp}.jsonl"):
            a = it["meta"]["article"]
            if a not in idx:
                continue
            c = items_rep[sp]
            c["n"] += 1
            best = max((float(sim[idx[a], idx[o["id"]]]) for o in it["options"]
                        if o["id"] != a and o["id"] in idx and fam[idx[o["id"]]] != fam[idx[a]]), default=0.0)
            for t in KUSZOBOK:
                if best > t:
                    c[f"duplikatum_opcio>{t}"] += 1
                    c[f"duplikatum_opcio>{t}_{'X' if it['gold'] is None else 'nemX'}"] += 1
    res["itemek"] = {sp: dict(c) for sp, c in items_rep.items()}
    write_json(out / "duplikatum.json", res)
    print(json.dumps({"parok": res["parok"], "itemek": res["itemek"]}, ensure_ascii=False, indent=1))
    for p in res["peldak"][:15]:
        print(p)


if __name__ == "__main__":
    main()
