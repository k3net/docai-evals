"""03-as kör — MDE a kitartott rétegekre (03-runbook 7., v1), a 00 `eszkozok/mde.py` módszerével, a val-ról vetítve.

Két klaszteres bootstrap a val-on (klaszter: `group_id`): (A) a τ is újraválasztva → Var_A = Var_τ + Var_minta(n_val);
(B) rögzített τ → Var_B = Var_minta(n_val). Vetítés a réteg pontozott tesztméretére (a v1 rétegei,
`f4_elemzes03.retegek`: a kalibrációs minta és a HO-routingon a T-hu-maradék nélkül; a H4-hez a HO-routing magyar része is):
SE² = (Var_A − Var_B) + Var_B · n_val / n_teszt; MDE (80% erő, kétoldali α = 0,05) = 2,80 · SE. A seed-komponens nincs
benne. A karok a perm-átlag kiolvasással, saját val-temperature-rel. Csak val-kiolvasást használ.

  python3 kor03/eszkozok/mde03.py [--reps 1000]   → eredmenyek/F4/mde03.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f2_elemzes03 import F2R, arm_predictions, choose_tau, fit_temperature, load_items, metrics, rows  # noqa: E402
from f3_val03 import F3R, readout  # noqa: E402
from f4_elemzes03 import load_meta03, retegek  # noqa: E402

sys.path.insert(0, str(HERE.parents[1] / "eszkozok"))
from elemzes import cluster_resample  # noqa: E402

ROOT = HERE.parents[0]
PAROK = {"H1: G3 s1 − L1★": ("k03v2_g3_s1", "L1★"), "H4: G3 s1 − G3-hu s1": ("k03v2_g3_s1", "k03v2_g3hu_s1"),
         "H6: G3 s1 − G3-kemény s1": ("k03v2_g3_s1", "k03v2_g3kemeny_s1")}


def arm(name: str, meta: dict, ids: set[str]) -> dict:
    p = F2R / "qwen_val.jsonl" if name == "L1★" else F3R / name / "vllm_val.jsonl"
    by = readout(p, ids)
    t = fit_temperature([r for rs in by.values() for r in rs if r["perm"] == 0], meta)
    return arm_predictions("perm_avg", by, meta, {"temp": t})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=1000)
    a = ap.parse_args()
    meta = load_items("val")
    for r in rows(ROOT / "adat/f2/items_val.jsonl"):
        meta[r["id"]]["group_id"] = r["group_id"]
    ids = sorted(meta)
    n_val = sum(not meta[i]["ketertelmu"] for i in ids)
    kalib = {s: v["ids"] for s, v in json.loads((ROOT / "adat/f4/kalib.json").read_text())["retegek"].items()}
    m03 = load_meta03()
    L, _ = retegek(m03, kalib)
    n_test = {s: sum(not m03[i]["ketertelmu"] for i in L[s]) for s in ("ho-termek", "ho-routing", "ho-routing-hu", "ho-uj")}
    preds = {k: arm(k, meta, set(ids)) for k in {x for p in PAROK.values() for x in p}}
    rng = np.random.default_rng(0)
    out = {"n_val": n_val, "n_teszt": n_test, "reps": a.reps, "parok": {}}
    for label, (ka, kb) in PAROK.items():
        pa, pb = preds[ka], preds[kb]
        ta, tb = choose_tau(pa, meta, ids, 0.95), choose_tau(pb, meta, ids, 0.95)
        oa, ob = metrics(pa, meta, ids, ta, 0.93), metrics(pb, meta, ids, tb, 0.93)
        full = {"lef95": [], "aurc": []}
        fixed = {"lef95": [], "aurc": []}
        for _ in range(a.reps):
            v = cluster_resample(ids, meta, "group_id", rng)
            t = cluster_resample(ids, meta, "group_id", rng)
            for store, (tau_a, tau_b) in ((full, (choose_tau(pa, meta, v, 0.95), choose_tau(pb, meta, v, 0.95))),
                                          (fixed, (ta, tb))):
                ma, mb = metrics(pa, meta, t, tau_a, 0.93), metrics(pb, meta, t, tau_b, 0.93)
                store["lef95"].append(ma["besorolasi_lefedettseg"] - mb["besorolasi_lefedettseg"])
                store["aurc"].append(ma["aurc"] - mb["aurc"])
        res = {"megfigyelt_val": {"lef95": oa["besorolasi_lefedettseg"] - ob["besorolasi_lefedettseg"],
                                  "aurc": oa["aurc"] - ob["aurc"]}}
        for m in ("lef95", "aurc"):
            va, vb = float(np.var(full[m])), float(np.var(fixed[m]))
            res[m] = {"tau_resz_aranya": round(max(0.0, va - vb) / va, 3) if va else None,
                      "mde80": {s: round(2.80 * float(np.sqrt(max(0.0, va - vb) + vb * n_val / n)), 4)
                                for s, n in sorted(n_test.items())}}
        out["parok"][label] = res
        print(label, json.dumps(res, ensure_ascii=False))
    (ROOT / "eredmenyek/F4").mkdir(parents=True, exist_ok=True)
    (ROOT / "eredmenyek/F4/mde03.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
