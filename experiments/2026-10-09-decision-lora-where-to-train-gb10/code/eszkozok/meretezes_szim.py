"""F1 méretezés-szimuláció (LLM nélkül, laptopon is fut): a generator.s2_szallitok + parok_split
valódi kódját futtatja álcikkekkel, és rétegenként megszámolja a sorokat.

  python3 eszkozok/meretezes_szim.py --profile _belso/tenant_profil.json

A célok a runbook 4.4-ből; a kitartott gyökerek cikkszáma külön állítható (heldout_n), mert a
T-kategória réteg mérete a <tenant>-arányból nem jönne ki ésszerű katalógusméretnél.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generator as g  # noqa: E402

CEL = {"train": 16000, "val-belso": 1500, "val-szallito": 1000, "T-belso": 1500, "T-szallito": 1500,
       "T-kozeli": 800, "T-tavoli": 800}


def fake_arts(profile: dict, n: int, heldout_n: int | None) -> list[dict]:
    arts = []
    for root, rp in profile["gyokerek"].items():
        k = heldout_n if (heldout_n and root in g.HELDOUT_ROOTS) else round(n * rp["cikk_arany"])
        for _ in range(k):
            arts.append({"id": f"a{len(arts):05d}", "root": root, "catchall": False})
    return arts


def sim(profile: dict, scale: dict, seed: int, heldout_n: int | None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        sups = g.s2_szallitok(profile, scale["suppliers"], seed, out)
        arts = fake_arts(profile, scale["articles"], heldout_n)
        pairs = g.parok_split(arts, sups, scale, seed, out)
    rows = Counter()
    for p in pairs:
        rows[p["split"]] += scale["rows_train"] if p["split"] == "train" else 1
    return {"cikk": len(arts), "sorok": dict(rows)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="_belso/tenant_profil.json")
    args = ap.parse_args()
    profile = json.load(open(args.profile))
    base = dict(g.SCALES["full"])
    print("cél:", CEL)
    grid = itertools.product([3000, 4000], [(28, 8, 12), (24, 8, 16)], [[0.55, 0.3, 0.15], [0.3, 0.4, 0.3]],
                             [0.5, 1.0], [None, 400], [2, 3])
    for n, sup, w, ph, hn, rt in grid:
        sc = {**base, "articles": n, "suppliers": sup, "n_sup_w": w, "p_hold": ph, "xb_strat": True, "rows_train": rt}
        r = sim(profile, sc, 202, hn)
        hiany = {k: r["sorok"].get(k, 0) for k in CEL if r["sorok"].get(k, 0) < 0.8 * CEL[k]}
        print(f"N={n} szall={sup} w={w} p_hold={ph} heldout_n={hn} rows_train={rt} → cikk={r['cikk']} "
              f"{json.dumps(r['sorok'], ensure_ascii=False)} | <80%: {list(hiany)}")


if __name__ == "__main__":
    main()
