"""MDE a 01 v1-hez — a 00 `mde.py` módszere a 01-es val-on (klaszter = `meta.klaszter`), több tesztméretre vetítve.

Két bootstrap ugyanazon a val-on: (A) a τ-hez és az értékeléshez független újraminta → Var_τ + Var_minta(n_val);
(B) rögzített τ → Var_minta(n_val). Vetítés: SE² = (Var_A − Var_B) + Var_B · n_val / n_teszt, ahol n a klaszterek
száma (a teszt klaszterezett bootstrapja ezt a hatásos mintát látja). MDE (80% erő, kétoldali α = 0,05) = 2,80 · SE.
A seed-komponens nincs benne. A val a plafonon ül (Napló 2026-10-08), ezért a val-variancia a tesztét alulbecsülheti.

  LDH_EXP=$PWD python3 kor01/eszkozok/mde01.py --a k01_l3mixse_p30_s1/vllm_val.jsonl:temp \
      --b k01_l3mixse_p30_s1/vllm_val_bazis.jsonl:perm_avg --n 553,598,1500,2183,4173
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import (FAIL_BELOW, TARGETS, arm_predictions, by_item, choose_tau, cluster_resample,  # noqa: E402
                     fit_temperature, load_meta, metrics)

ROOT = Path(__file__).resolve().parents[1]


def arm(spec: str, meta: dict) -> dict:
    path, name = spec.rsplit(":", 1)
    rows = read_jsonl(ROOT / "eredmenyek/F3" / path)
    temp = fit_temperature([r for r in rows if r["perm"] == 0], meta)
    return arm_predictions(name, by_item(rows, None), meta, {"temp": temp})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--n", required=True, help="vesszős lista: a teszt-rétegek klaszterszáma")
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--out", default=str(ROOT / "eredmenyek/F3/mde_v1.json"))
    args = ap.parse_args()
    meta = load_meta(ROOT / "adat")
    pa, pb = arm(args.a, meta), arm(args.b, meta)
    ids = [i for i in pa if i in pb and meta[i]["split"] == "val"]
    n_val = len({meta[i]["klaszter"] for i in ids if not meta[i].get("ketertelmu")})
    rng = np.random.default_rng(0)
    res = {"a": args.a, "b": args.b, "n_val_klaszter": n_val, "reps": args.reps, "celok": {}}
    for tgt, tn in TARGETS:
        fb = FAIL_BELOW[tn]
        tau_a, tau_b = choose_tau(pa, meta, ids, tgt), choose_tau(pb, meta, ids, tgt)
        oa, ob = metrics(pa, meta, ids, tau_a, fb), metrics(pb, meta, ids, tau_b, fb)
        da, db, aa, ab = [], [], [], []
        for _ in range(args.reps):
            v = cluster_resample(ids, meta, "klaszter", rng)
            t = cluster_resample(ids, meta, "klaszter", rng)
            ma, mb = metrics(pa, meta, t, choose_tau(pa, meta, v, tgt), fb), metrics(pb, meta, t, choose_tau(pb, meta, v, tgt), fb)
            da.append(ma["besorolasi_lefedettseg"] - mb["besorolasi_lefedettseg"])
            aa.append(ma["aurc"] - mb["aurc"])
            ma, mb = metrics(pa, meta, t, tau_a, fb), metrics(pb, meta, t, tau_b, fb)
            db.append(ma["besorolasi_lefedettseg"] - mb["besorolasi_lefedettseg"])
            ab.append(ma["aurc"] - mb["aurc"])

        def proj(full: list[float], fixed: list[float]) -> dict:
            va, vb = float(np.var(full)), float(np.var(fixed))
            out = {"se_val_teljes": round(va ** 0.5, 4), "tau_resz_aranya": round(max(0.0, va - vb) / va, 3) if va else None}
            for n in (int(x) for x in args.n.split(",")):
                out[f"mde80_n{n}"] = round(2.80 * float(np.sqrt(max(0.0, va - vb) + vb * n_val / n)), 4)
            return out

        res["celok"][tn] = {"delta_val": round(oa["besorolasi_lefedettseg"] - ob["besorolasi_lefedettseg"], 4),
                            "lefedettseg": proj(da, db)}
        if tn == "95":
            res["aurc"] = {"delta_val": round(oa["aurc"] - ob["aurc"], 4), **proj(aa, ab)}
    write_json(Path(args.out), res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
