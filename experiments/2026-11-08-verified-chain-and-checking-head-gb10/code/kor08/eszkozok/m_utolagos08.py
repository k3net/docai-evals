"""08 M utólag (11-06; nem rögzített, leíró): az illesztett K1(a)-halmazon mennyit magyaráz a régi szöveges modell (a `felszin08` modelljei, a G2 tanítómintáján) az L-RN nyereségéből. A halmaz a `g5_k1_08`-é, az
`m08 egyesit` bemenetén. Egységen belül: az (a') a saját (b)-i ellen; a szöveges pontszám kvartilisein belül: az L-RN és az L-S. A rögzített olvasatot nem érinti.
  python3 kor08/eszkozok/m_utolagos08.py --out kor08/eredmenyek/M/utolagos
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import felszin08 as F  # noqa: E402

K = F.K
E = F.EXP / "cache/k08/m/egyesitett"
G2 = F.EXP / "kor08/adat/G2"
FAM = "szabaly.koltsegelszamolas"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    C = K.Csalad(FAM, E / f"pont_{FAM}.json", E / "items", E / "kinyert", E / "orakulum")
    raw = {i["id"]: i for i in F.jl(E / f"items/{FAM}.jsonl")}
    tan = F.jl(G2 / f"ert_tanito/items/{FAM}.jsonl")
    xt = [F.szoveg(i) for i in tan]
    yt = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan])
    gt = np.array([i["template_group_id"] for i in tan])
    x = [F.szoveg(raw[i]) for i in C.ids]
    halmaz, pos = C.ag["K1a"]
    full = np.where(halmaz)[0]
    err = {"L-RN": -np.mean(C.pont["L-RN"], axis=0), "L-S": -np.mean(C.pont["L-S"], axis=0)}
    for t in ("szó", "karakter"):
        err[t] = F.illeszt(t, xt, yt, gt)[0].predict_proba(x)[:, 1]
    res: dict = {"n": int(len(full)), "a": int(pos[full].sum()), "auroc": {k: K.auroc(v[full], pos[full]) for k, v in err.items()}}
    legjobb = "karakter" if res["auroc"]["karakter"] >= res["auroc"]["szó"] else "szó"
    res["legjobb"] = legjobb
    res["spearman_L-RN_szoveg"] = float(np.corrcoef(np.argsort(np.argsort(err["L-RN"][full])), np.argsort(np.argsort(err[legjobb][full])))[0, 1])
    q = np.quantile(err[legjobb][full], (0.25, 0.5, 0.75))
    sav = np.searchsorted(q, err[legjobb][full])
    res["kvartilis"] = []
    for b in range(4):
        s = full[sav == b]
        res["kvartilis"].append({"n": int(len(s)), "a": int(pos[s].sum()), "L-RN": K.auroc(err["L-RN"][s], pos[s]), "L-S": K.auroc(err["L-S"][s], pos[s])})
    eg: dict = {}
    for k in full:
        eg.setdefault(raw[C.ids[k]]["meta"]["ertelmezes"]["egyseg"], []).append(k)
    p = [(i, j) for t in eg.values() for i in t if pos[i] for j in t if not pos[j]]
    res["egyseg"] = {"parok": len(p), **{n: float(np.mean([(err[n][i] > err[n][j]) + 0.5 * (err[n][i] == err[n][j]) for i, j in p])) for n in ("L-RN", "L-S", legjobb)}}
    o = F.EXP / a.out
    o.mkdir(parents=True, exist_ok=True)
    (o / "utolagos.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
