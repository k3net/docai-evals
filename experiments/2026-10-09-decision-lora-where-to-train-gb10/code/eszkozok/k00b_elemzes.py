"""00b — H2-szállító′ elemzése (runbook 15. pont, előre rögzítve 2026-10-07).

Egyetlen tesztréteg (alapból `T-ujszallito`) az F4 karjaival és kalibrációjával:
  * L1★ = permutáció-átlag + a perm-0 val-kiolvasásra illesztett temperature (mint az F4-ben); érzékenységként a
    permutáció-átlagra illesztett temperature is;
  * L3 = `temp` kar (perm 0), seedenként; τ@95 / τ@90 a val-on;
  * Δ = L3 (seedek átlaga) − L1★ besorolási lefedettség; a közölt Δ a pontkülönbség, a CI a bootstrap percentilise;
  * bootstrap: 10 000 ismétlés, a val (klaszter = cikk) és a réteg (klaszter = szállító) újramintavételezésével,
    τ újraválasztással, seed-újramintavételezéssel (mint az F4);
  * ítélet: CI alsó határa > 0 → általánosít; CI felső határa < 2 pont → nem általánosít; egyébként nem eldönthető;
  * mellékes: egzakt szállító-permutáció (rögzített val-τ), AURC a saját görbéig és közös lefedettségen, nem-X arány
    (a lef@95 plafonja), kockázat 0,7-es lefedettségen, X-fedés, precizitás-bukás.
A meta a val-rétegekhez az F1-ből (`--items-val`), a réteghez a fagyasztott 00b-könyvtárból (`--items-test`) jön.

  python3 eszkozok/k00b_elemzes.py --motor vllm --items-val adat/f1 --items-test adat/k00b/meres \\
      --l0-val eredmenyek/K00b/vllm/l0_val.jsonl --l0-test eredmenyek/K00b/vllm/l0_test.jsonl \\
      --l3 s1:<val>:<teszt> --l3 s2:... --l3 s3:... --out eredmenyek/K00b/vllm_k00b.json
Önteszt az F4 T-szállító rétegén (az F4-gyel egyező pont-Δ-t és permutációs p-t kell adnia):
  python3 eszkozok/k00b_elemzes.py --split T-szallito --items-test adat/f1 ... (F4-fájlokkal)
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import (VAL_STRATA, _p, arm_predictions, by_item, choose_tau, fit_temperature, load_meta,  # noqa: E402
                     metrics)
from f4_elemzes import CP, Arm, Resampler, metrics_fast, summarize, supplier_permutation, tau_fast  # noqa: E402

TARGETS = [(0.95, "95"), (0.90, "90")]


def preds(val: str, test: str, meta: dict, arm: str, temp: float | None = None) -> tuple[dict, float]:
    rv, rt = read_jsonl(_p(val)), read_jsonl(_p(test))
    t = temp if temp is not None else fit_temperature([r for r in rv if r["perm"] == 0], meta)
    return ({**arm_predictions(arm, by_item(rv, None), meta, {"temp": t}),
             **arm_predictions(arm, by_item(rt, None), meta, {"temp": t})}, t)


def permavg_temperature(val: str, meta: dict) -> float:
    bv = by_item(read_jsonl(_p(val)), None)
    vids = [i for i in bv if not meta[i].get("ketertelmu")]

    def nll(lt: float) -> float:
        p = arm_predictions("perm_avg", bv, meta, {"temp": math.exp(lt)})
        return -sum(math.log(max(1e-12, p[i][2].get(meta[i]["gold"], 1e-12))) for i in vids)
    return math.exp(getattr(minimize_scalar(nll, bounds=(-3, 4), method="bounded"), "x"))


def risk_curve(p: dict, ids: list[str], meta: dict) -> np.ndarray:
    order = sorted([i for i in ids if p[i][0] is not None], key=lambda i: -p[i][1])
    err, out = 0, []
    for k, i in enumerate(order, 1):
        err += p[i][0] != meta[i]["gold"]
        out.append(err / k)
    return np.array(out)


def verdict(ci: list[float]) -> str:
    if ci[0] > 0:
        return "általánosít"
    if ci[1] < 0.02:
        return "nem általánosít"
    return "nem eldönthető"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", required=True, choices=["vllm", "hf"])
    ap.add_argument("--split", default="T-ujszallito")
    ap.add_argument("--items-val", default="adat/f1")
    ap.add_argument("--items-test", default="adat/k00b/meres")
    ap.add_argument("--l0-val", required=True)
    ap.add_argument("--l0-test", required=True)
    ap.add_argument("--l3", action="append", required=True, help="név:val.jsonl:teszt.jsonl")
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    mv = load_meta(_p(args.items_val))
    mt = load_meta(_p(args.items_test))
    meta = {i: m for i, m in mv.items() if m["split"] in VAL_STRATA}
    clash = [i for i, m in mt.items() if m["split"] == args.split and i in meta]
    if clash:
        raise SystemExit(f"{len(clash)} item-id ütközik a val-lal")
    meta |= {i: m for i, m in mt.items() if m["split"] == args.split}

    l1, t1 = preds(args.l0_val, args.l0_test, meta, "perm_avg")
    l0, _ = preds(args.l0_val, args.l0_test, meta, "nyers")
    t1_alt = permavg_temperature(args.l0_val, meta)
    l1_alt, _ = preds(args.l0_val, args.l0_test, meta, "perm_avg", t1_alt)
    l3 = {}
    for spec in args.l3:
        name, v, t = spec.split(":")
        l3[name] = preds(v, t, meta, "temp")[0]
    val_ids = sorted(i for i in l1 if i in meta and meta[i]["split"] in VAL_STRATA)
    test_ids = sorted(i for i in l1 if i in meta and meta[i]["split"] == args.split)
    for name, p in l3.items():
        miss = [i for i in val_ids + test_ids if i not in p]
        if miss:
            raise SystemExit(f"{name}: {len(miss)} item hiányzik a kiolvasásból")
    sc = [i for i in test_ids if not meta[i].get("ketertelmu")]

    res: dict = {"motor": args.motor, "split": args.split, "bemenetek": vars(args), "n_val": len(val_ids),
                 "n_teszt": len(test_ids), "n_pontozott": len(sc),
                 "szallitok": len({meta[i]["supplier"] for i in sc}),
                 "nem_X_arany": float(np.mean([meta[i]["gold"] is not None for i in sc])),
                 "temperature": {"L1csillag_perm0_illesztes": t1, "L1csillag_perm_atlagra": t1_alt}}
    arms = {"L0": l0, "L1csillag": l1, "L1csillag_perm_atlag_T": l1_alt, **{f"L3_{k}": p for k, p in l3.items()}}
    pont = {}
    for name, p in arms.items():
        pont[name] = {}
        for tgt, tn in TARGETS:
            tau = choose_tau(p, meta, val_ids, tgt)
            m = metrics(p, meta, test_ids, tau)
            pont[name][tn] = {"tau": tau, **{k: m.get(k) for k in (
                "besorolasi_lefedettseg", "besorolasi_precizitas", "precizitas_bukas", "aurc", "ece", "pontossag",
                "dontesi_lefedettseg", "x_precizitas", "x_fedes")}}
    res["pont"] = pont
    seeds = list(l3)

    def mean3(key: str, tn: str = "95") -> float:
        return float(np.mean([pont[f"L3_{k}"][tn][key] for k in seeds]))
    res["pont_delta"] = {f"lef{tn}": mean3("besorolasi_lefedettseg", tn) - pont["L1csillag"][tn]["besorolasi_lefedettseg"]
                         for _, tn in TARGETS}
    res["pont_delta"]["aurc"] = mean3("aurc") - pont["L1csillag"]["95"]["aurc"]
    res["pont_delta"]["lef95_perm_atlag_T"] = (mean3("besorolasi_lefedettseg")
                                               - pont["L1csillag_perm_atlag_T"]["95"]["besorolasi_lefedettseg"])

    curves = {k: risk_curve(arms[k], sc, meta) for k in ["L1csillag", *[f"L3_{s}" for s in seeds]]}
    common = min(len(c) for c in curves.values())
    n = len(sc)
    res["aurc_kozos_lefedettsegen"] = {"lefedettseg": common / n,
                                       **{k: float(c[:common].sum() / n) for k, c in curves.items()}}
    res["kockazat_0_7_lefedettsegen"] = {k: (float(c[int(0.7 * n) - 1]) if len(c) >= int(0.7 * n) else None)
                                         for k, c in curves.items()}

    # --- bootstrap ---------------------------------------------------------------------------------------
    ids = val_ids + test_ids
    rs = Resampler(ids, meta, {"val": val_ids, "teszt": test_ids}, {"teszt": "supplier"})
    scored = np.array([not meta[i].get("ketertelmu") for i in ids])
    cp = CP(len(ids) + 1)
    A1 = Arm(l1, ids, meta)
    A3 = {k: Arm(p, ids, meta) for k, p in l3.items()}
    rng = np.random.default_rng(args.seed)
    acc: dict[str, list] = {"lef95": [], "lef90": [], "aurc": []}
    for _ in range(args.reps):
        v, t = rs.draw("val", rng), rs.draw("teszt", rng)
        drawn = [seeds[k] for k in rng.integers(0, len(seeds), len(seeds))]
        for tgt, tn in TARGETS:
            tb = tau_fast(A1, v, scored, tgt, cp)
            ta = {k: tau_fast(A3[k], v, scored, tgt, cp) for k in set(drawn)}
            mb = metrics_fast(A1, t, scored, tb)
            ma = [metrics_fast(A3[k], t, scored, ta[k]) for k in drawn]
            acc[f"lef{tn}"].append(np.mean([m["lef"] for m in ma]) - mb["lef"])
            if tn == "95":
                acc["aurc"].append(np.mean([m["aurc"] for m in ma]) - mb["aurc"])
    boot = {k: summarize(x) for k, x in acc.items()}
    res["bootstrap"] = {"reps": args.reps, "seed": args.seed, "klaszter": {"val": "cikk", "teszt": "szállító"},
                        "L3_minus_L1csillag": boot}
    res["H2_szallito_vesszo"] = {"delta_pont": res["pont_delta"]["lef95"], "ci95": boot["lef95"]["ci95"],
                                 "p_ketoldali": boot["lef95"]["p_ketoldali"], "itelet": verdict(boot["lef95"]["ci95"])}
    res["szallito_permutacio"] = supplier_permutation(list(l3.values()), l1, meta, val_ids, test_ids, args.reps, rng)
    write_json(_p(args.out), res)
    h = res["H2_szallito_vesszo"]
    print(f"{args.motor} {args.split}: n = {len(sc)} pontozott, {res['szallitok']} szállító; Δlef95 = {h['delta_pont']:+.4f} "
          f"[{h['ci95'][0]:+.4f}; {h['ci95'][1]:+.4f}] → {h['itelet']}; permutáció p = "
          f"{res['szallito_permutacio']['p_ketoldali']:.5f}")


if __name__ == "__main__":
    main()
