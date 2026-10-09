"""MDE — a legkisebb kimutatható különbség a teszten (runbook F1 7. lépés, 8. pont), az F2 val-kiolvasásaiból.

A H1 párosított Δ-ja (a − b) a teszten, klaszterezett bootstrappal, a val újramintavételezésével és τ
újraválasztásával. Itt csak a val áll rendelkezésre (a teszt az F4-ig zárva), ezért a szórást két részre bontjuk:
  - τ-rész: a küszöb a val-on rögzül, a bizonytalansága NEM csökken a teszt méretével;
  - mintavételi rész: a teszt-itemek véletlensége, ~1/n szerint skálázva a teszt pontozott méretére.
Két bootstrap ugyanazon a val-on (klaszter = cikk):
  (A) teljes: független újraminta a τ-hez és az „értékeléshez” → Var_A = Var_τ + Var_minta(n_val);
  (B) rögzített τ, csak az értékelés újramintázva → Var_B = Var_minta(n_val).
Vetítés: SE_teszt² = (Var_A − Var_B) + Var_B · n_val / n_teszt; MDE (80% erő, kétoldali α = 0,05) = 2,80 · SE_teszt.
A seed-komponens (H1: 3 seed) nincs benne; az F3 megerősítő seedjei adják.

  python3 eszkozok/mde.py --items adat/f1 --a eredmenyek/F2/l2a_L40/val.jsonl:perm_avg \\
      --b eredmenyek/F2/hf_val.jsonl:perm_avg --n-test 3021 --out eredmenyek/F2/mde.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import (  # noqa: E402
    FAIL_BELOW, TARGETS, VAL_STRATA, _p, arm_predictions, by_item, choose_tau, cluster_resample, fit_temperature,
    load_meta, metrics,
)


def arm(spec: str, meta: dict) -> tuple[dict, str]:
    path, name = spec.rsplit(":", 1)
    rows = read_jsonl(_p(path))
    temp = fit_temperature([r for r in rows if r["perm"] == 0], meta)
    params = {"temp": temp}
    return arm_predictions(name, by_item(rows, None), meta, params), f"{Path(path).parent.name}/{Path(path).stem}:{name}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--a", required=True, help="fájl:kar (kar: nyers, temp, perm_avg)")
    ap.add_argument("--b", required=True)
    ap.add_argument("--n-test", type=int, required=True, help="a teszt pontozott itemszáma")
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    meta = load_meta(_p(args.items))
    pa, na = arm(args.a, meta)
    pb, nb = arm(args.b, meta)
    ids = [i for i in pa if i in pb and meta[i]["split"] in VAL_STRATA]
    n_val = sum(not meta[i].get("ketertelmu") for i in ids)
    rng = np.random.default_rng(0)
    res = {"a": na, "b": nb, "n_val": n_val, "n_teszt": args.n_test, "reps": args.reps, "celok": {}}
    for tgt, tn in TARGETS:
        fb = FAIL_BELOW[tn]
        tau_a, tau_b = choose_tau(pa, meta, ids, tgt), choose_tau(pb, meta, ids, tgt)
        obs_a, obs_b = metrics(pa, meta, ids, tau_a, fb), metrics(pb, meta, ids, tau_b, fb)
        da, db, aa, ab = [], [], [], []
        for _ in range(args.reps):
            v = cluster_resample(ids, meta, "article", rng)
            t = cluster_resample(ids, meta, "article", rng)
            ma = metrics(pa, meta, t, choose_tau(pa, meta, v, tgt), fb)
            mb = metrics(pb, meta, t, choose_tau(pb, meta, v, tgt), fb)
            da.append(ma["besorolasi_lefedettseg"] - mb["besorolasi_lefedettseg"])
            aa.append(ma["aurc"] - mb["aurc"])
            ma = metrics(pa, meta, t, tau_a, fb)
            mb = metrics(pb, meta, t, tau_b, fb)
            db.append(ma["besorolasi_lefedettseg"] - mb["besorolasi_lefedettseg"])
            ab.append(ma["aurc"] - mb["aurc"])

        def proj(full: list[float], fixed: list[float]) -> dict:
            va, vb = float(np.var(full)), float(np.var(fixed))
            se = float(np.sqrt(max(0.0, va - vb) + vb * n_val / args.n_test))
            return {"se_val_teljes": round(va ** 0.5, 4), "se_val_rogzitett_tau": round(vb ** 0.5, 4),
                    "tau_resz_aranya": round(max(0.0, va - vb) / va, 3) if va else None,
                    "se_teszt_vetitett": round(se, 4), "mde80": round(2.80 * se, 4)}

        res["celok"][tn] = {
            "megfigyelt_delta_val": round(obs_a["besorolasi_lefedettseg"] - obs_b["besorolasi_lefedettseg"], 4),
            "lefedettseg": proj(da, db),
        }
        if tn == "95":
            res["aurc"] = {"megfigyelt_delta_val": round(obs_a["aurc"] - obs_b["aurc"], 4), **proj(aa, ab)}
    write_json(_p(args.out), res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
