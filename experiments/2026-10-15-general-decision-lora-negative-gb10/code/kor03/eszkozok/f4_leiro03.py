"""03-as kör — leíró bontások az F4 után (utólagos; a v1 ítéleteit nem változtatják, 03-runbook 7.10).

Az `f4_elemzes03.Adat` predikcióival és val-τ-ival, pontbecslésként (bootstrap nélkül):
  1. a precizitásesés forrása rétegenként: az elfogadott hibák X-gold itemen (magabiztos „hívás” irrelevanciára) vagy
     nem-X itemen (rossz opció); a nem-X itemek lefedettsége és precizitása; az X-gold itemek elfogadási aránya;
  2. bontás forrásonként / alrétegenként / családonként (HO-routing: forrás; HO-termék: a 00 alrétegei; HO-új: család);
  3. a hibák bizalma: az elfogadott hibák közül hány ≥ 0,95 bizalmú; a szelektív kockázat közös 0,5-ös lefedettségen;
  4. a G3 s2 a többi seed kalibrációs karjával (perm-átlag + saját val-temperature, val-τ), mert a val-on a nyers kar
     nyert nála.

  python3 kor03/eszkozok/f4_leiro03.py   → eredmenyek/F4/f4_leiro03.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f4_elemzes03 import (F3R, F4R, G3, HU, KEM, L3, Adat, arm_predictions, choose_tau, fit_temperature,  # noqa: E402
                          kmin_table, point_taus, readout)

RETEGEK = ("ho-termek", "ho-routing", "ho-uj")


def blokk(p: dict, meta: dict, ids: list[str], tau: float) -> dict:
    s = [i for i in ids if not meta[i]["ketertelmu"]]
    acc = [i for i in s if p[i][0] is not None and p[i][1] >= tau]
    wrong = [i for i in acc if p[i][0] != meta[i]["gold"]]
    xg = [i for i in s if meta[i]["x"]]
    nx = [i for i in s if not meta[i]["x"]]
    acc_nx = [i for i in acc if not meta[i]["x"]]
    acc_set = set(acc)
    out = {"n": len(s), "n_x": len(xg), "lef": len(acc) / len(s) if s else None,
           "prec": (len(acc) - len(wrong)) / len(acc) if acc else None, "elfogadott": len(acc),
           "hiba_x_goldon": sum(meta[i]["x"] for i in wrong), "hiba_rossz_opcio": sum(not meta[i]["x"] for i in wrong),
           "x_elfogadasi_arany": sum(1 for i in xg if i in acc_set) / len(xg) if xg else None,
           "x_fedes": sum(p[i][0] is None for i in xg) / len(xg) if xg else None,
           "nemx_lef": len(acc_nx) / len(nx) if nx else None,
           "nemx_prec": sum(p[i][0] == meta[i]["gold"] for i in acc_nx) / len(acc_nx) if acc_nx else None,
           "hiba_095_folott": sum(p[i][1] >= 0.95 for i in wrong)}
    # szelektív kockázat közös 0,5-ös lefedettségen: a legmagabiztosabb nem-X döntések a pontozott itemek felére
    asg = sorted((i for i in s if p[i][0] is not None), key=lambda i: -p[i][1])
    k = len(s) // 2
    out["kockazat_lef05"] = (sum(p[i][0] != meta[i]["gold"] for i in asg[:k]) / k) if len(asg) >= k > 0 else None
    return out


def atlag(bl: list[dict]) -> dict:
    out = {}
    for key in bl[0]:
        v = [b[key] for b in bl]
        out[key] = None if any(x is None for x in v) else float(np.mean(v))
    return out


def main() -> None:
    D = Adat(SimpleNamespace(proba=False))
    meta, P = D.meta, D.preds
    kmin = kmin_table(len(D.ids) + 1)
    taus = point_taus(D, kmin)

    def karok(g: str) -> dict:
        return {"L1": [("L1",)], "G3": [(a,) for a in G3], "G3-kemeny": [(KEM,)], "G3-hu": [(HU,)],
                **({"L3-spec": [(a,) for a in L3[g]]} if g in L3 else {})}

    def reteg_blokk(g: str, ids: list[str]) -> dict:
        res = {}
        for name, arms in karok(g).items():
            bl = [blokk(P[a], meta, ids, taus[a]) for (a,) in arms]
            res[name] = atlag(bl) if len(bl) > 1 else bl[0]
            if name == "G3":
                res["G3_seedenkent"] = {a: b for (a,), b in zip(arms, bl)}
        return res

    out: dict = {"megjegyzes": "utólagos, leíró; a v1 ítéleteit nem változtatja", "retegek": {}, "bontas": {}}
    for g in RETEGEK:
        out["retegek"][g] = reteg_blokk(g, D.L[g])
    key = {"ho-routing": lambda i: meta[i]["source"] + ("/atnezett" if meta[i]["source"] == "massive_hu" else ""),
           "ho-termek": lambda i: meta[i]["reteg00"], "ho-uj": lambda i: meta[i]["family"]}
    for g in RETEGEK:
        grp = defaultdict(list)
        for i in D.L[g]:
            grp[key[g](i)].append(i)
        out["bontas"][g] = {k: reteg_blokk(g, v) for k, v in sorted(grp.items())}
    # a G3 s2 a perm-átlag karral (a többi seed választása), saját val-temperature-rel és val-τ-val
    sv, se = set(D.val03), set(D.eval03)
    bv = readout(F3R / G3[1] / "vllm_val.jsonl", sv)
    temp = fit_temperature([r for rs in bv.values() for r in rs if r["perm"] == 0], meta)
    be = readout(F4R / G3[1] / "vllm_eval.jsonl", se)
    p = {**arm_predictions("perm_avg", bv, meta, {"temp": temp}), **arm_predictions("perm_avg", be, meta, {"temp": temp})}
    t = choose_tau(p, meta, D.val03, 0.95)
    out["G3_s2_perm_atlag"] = {"temp": temp, "tau": t,
                               "retegek": {g: blokk(p, meta, D.L[g], t) for g in RETEGEK},
                               "nyers_kar_retegek": {g: blokk(P[G3[1]], meta, D.L[g], taus[G3[1]]) for g in RETEGEK}}
    out["tau_val"] = taus
    (F4R / "f4_leiro03.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for g in RETEGEK:
        print(g, {k: {x: (round(v[x], 3) if isinstance(v.get(x), float) else v.get(x))
                      for x in ("lef", "prec", "hiba_x_goldon", "hiba_rossz_opcio", "nemx_prec", "x_elfogadasi_arany")}
                  for k, v in out["retegek"][g].items() if k != "G3_seedenkent"})


if __name__ == "__main__":
    main()
