"""08 G1-próba — a szabálycsalád blokk-változatai a K3 diag-on, orákulum-úton (`lanc08.BLOKK_VALTOZAT`; Dani 11-02:
„érthető-e a modell számára a számítási blokk és a megmaradt szabálypontok jelentése”). Az alany B1-4S döntése; a
helyesség az eredeti itemhez (`g1_dontes08.helyes`). A v0 az eredeti blokk (oK3), a v1 és a v2 csak hozzáír.
  python3 kor08/eszkozok/g1_blokk08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import b1rel07 as R  # noqa: E402
import g1_dontes08 as G  # noqa: E402
import lanc08 as L  # noqa: E402

FAM = L.SZAB
ELO = {"v0": "oK3", "v1": "oK3v1", "v2": "oK3v2"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jell", default="cache/k08/jellemzok")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    temp = json.loads((EXP / "cache/k07/fejek/temperature.json").read_text())["B1-4"]
    eredeti = {it["id"]: it for _, it in L.betolt("K3diag", FAM)}
    csali = L._k3_csalik(FAM)
    res = {}
    for v, elo in ELO.items():
        by = R.rows4(f"{elo}_{FAM}_DIAG", EXP / a.jell)
        c = Counter()
        for i, it in eredeti.items():
            d = R.decide4(by[i], temp)
            ok = G.helyes(d, it["content_state"], it["gold"])
            for k in ("mind", it["lang"], csali[i][0]):
                c[f"{k}|n"] += 1
                c[f"{k}|helyes"] += ok
                c[f"{k}|X"] += (not ok) and d["kind"] == "NONE"
        res[v] = dict(c)
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "blokk_valtozatok.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sor = ["# G1-próba: a szabálycsalád blokk-változatai (K3 diag, orákulum-út, B1-4S)", "",
           "v0 az eredeti blokk; v1 kimondja, melyik kiszámított értéket kell az összeghatárhoz mérni; v2 a megmaradt",
           "szabálypontonként kimondja, hogy az összegfeltétel teljesül. Helyes / n, zárójelben a MATCH → X hibák.", "",
           "| változat | mind | magyar | angol | S3a (nettó) | S3b (deviza) |", "|---|---|---|---|---|---|"]
    for v, c in res.items():
        cel = [f"{c.get(k + '|helyes', 0)} / {c.get(k + '|n', 0)} ({c.get(k + '|X', 0)})"
               for k in ("mind", "hu", "en", "S3a-netto", "S3b-deviza")]
        sor.append(f"| {v} | " + " | ".join(cel) + " |")
    (out / "blokk_valtozatok.md").write_text("\n".join(sor) + "\n", encoding="utf-8")
    print("\n".join(sor))


if __name__ == "__main__":
    main()
