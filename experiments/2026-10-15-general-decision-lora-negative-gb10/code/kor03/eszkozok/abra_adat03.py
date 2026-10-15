"""03-as kör — az ábrák adatai a kiolvasásokból (csak aggregátum; 03-runbook Napló 2026-10-15, publikálás).

Az `f4_elemzes03.Adat` predikcióival és val-τ-ival, a három kitartott rétegen (HO-termék, HO-routing, HO-új):
  görbe      kockázat–lefedettség: a kar saját nem-X döntései bizonyosság szerint csökkenő sorrendben; a k-adik
             pontban lefedettség = k / pontozott item, kockázat = hibás döntés / k (a 00 `publikacio/abrak/adat.py`
             receptje). Ez a görbe adja az AURC-t.
  munkapont  (lef, prec) a val-on választott τ@95-nél (a v1 lef@95-e és precizitása);
  lef_p95    a rétegen magán illesztett τ@95 lefedettsége (felső korlát, a feltáró elemzés mérőszáma);
  plafon     a nem-X itemek aránya a pontozottak közt.
Karok: L1★, G3 s1–s3, és ahol van, a feladatspecifikus L3 (00 a HO-terméken, 01 a HO-routingon).

  python3 kor03/eszkozok/abra_adat03.py   → eredmenyek/F4/abra_adat03.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f4_elemzes03 import F4R, G3, L3, Adat, choose_tau, kmin_table, metrics, point_taus  # noqa: E402

RETEGEK = ("ho-termek", "ho-routing", "ho-uj")


def curve(p: dict, meta: dict, ids: list[str], step: float = 0.005) -> list[list[float]]:
    sc = [i for i in ids if not meta[i]["ketertelmu"]]
    order = sorted((i for i in sc if p[i][0] is not None), key=lambda i: -p[i][1])
    n, err, pts, nxt = len(sc), 0, [], step
    for k, i in enumerate(order, 1):
        err += p[i][0] != meta[i]["gold"]
        if k / n >= nxt or k == len(order):
            pts.append([round(k / n, 4), round(err / k, 5)])
            nxt += step
    return pts


def main() -> None:
    D = Adat(SimpleNamespace(proba=False))
    meta = D.meta
    taus = point_taus(D, kmin_table(len(D.ids) + 1))
    out: dict = {"megjegyzes": "ábraadat, csak aggregátum; a v1 val-τ-ival (munkapont) és a rétegen illesztett τ-val (lef_p95)"}
    for g in RETEGEK:
        ids = D.L[g]
        sc = [i for i in ids if not meta[i]["ketertelmu"]]
        arms = ["L1", *G3, *L3.get(g, [])]
        blk = {"n": len(sc), "plafon": sum(not meta[i]["x"] for i in sc) / len(sc), "karok": {}}
        for a in arms:
            p = D.preds[a]
            m = metrics(p, meta, ids, taus[a], 0.93)
            tp = choose_tau(p, meta, sc, 0.95)
            blk["karok"][a] = {"gorbe": curve(p, meta, ids),
                               "munkapont": {"lef": m["besorolasi_lefedettseg"], "prec": m["besorolasi_precizitas"]},
                               "aurc": m["aurc"], "x_fedes": m["x_fedes"],
                               "lef_p95": metrics(p, meta, sc, tp, 0.93)["besorolasi_lefedettseg"]}
        out[g] = blk
        print(g, {a: (round(v["munkapont"]["lef"], 3), round(v["munkapont"]["prec"], 3), round(v["lef_p95"], 3))
                  for a, v in blk["karok"].items()})
    (F4R / "abra_adat03.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
