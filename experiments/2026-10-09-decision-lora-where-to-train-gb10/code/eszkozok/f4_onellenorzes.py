"""F4 — a kör végi önellenőrzés utólagos, leíró számai (nem előre rögzítettek; 2026-10-07, Dani kérése).

Két független átnézés (kódhelyesség; tervezés és előregisztráció) leleteit teszi reprodukálhatóvá. vLLM, teszt:
  * split-szivárgás: rétegenként a szállítók, közülük a train-ben is szereplők és azok train-sorai, a (szállító,
    cikk) pár-átfedés, és a train-nel azonos (normalizált sorszöveg, gold) duplikátumok;
  * szállítói általánosítás: a T-szállító szállítónkénti nyeresége a train-sorok számának függvényében, és a
    látott / nem látott szállítós itemek a T-közeli, T-távoli, T-belső rétegen;
  * plafon és hibaszerkezet: a nem-X arány (a lef@95 plafonja), az L1★ és az L3 hibái @95/@90-en
    (X-gold besorolva vs. rossz cikk);
  * AURC-definíció: a kar saját nem-X lefedettségéig tartó görbe (a használt), közös lefedettségre vágva, a
    kockázat rögzített lefedettségen, és az X-et is döntésnek számító AURC;
  * X-arány-érzékenység: a val és a teszt X-itemjeinek ritkításával (30 ismétlés) a H1-különbség;
  * pont-Δ a bootstrap-medián mellett;
  * az L1★ temperature-illesztése: perm-0-ra (a használt), a permutáció-átlagra, T = 1 — ECE és lef@95.

  LDH_EXP=$PWD python3 eszkozok/f4_onellenorzes.py --out eredmenyek/F4/onellenorzes.json
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import (TEST_STRATA, VAL_STRATA, _p, arm_predictions, by_item, choose_tau, fit_temperature,  # noqa: E402
                     load_meta, metrics)

ALL_STRATA = VAL_STRATA + TEST_STRATA


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def load(vdir: Path, val: str, test: str, meta: dict, arm: str, temp: float | None = None) -> dict:
    rv, rt = read_jsonl(vdir / val), read_jsonl(vdir / test)
    t = temp if temp is not None else fit_temperature([r for r in rv if r["perm"] == 0], meta)
    return {**arm_predictions(arm, by_item(rv, None), meta, {"temp": t}),
            **arm_predictions(arm, by_item(rt, None), meta, {"temp": t})}


def cov(p: dict, ids: list[str], tau: float) -> float:
    return float(np.mean([p[i][0] is not None and p[i][1] >= tau for i in ids]))


def risk_curve(p: dict, ids: list[str], meta: dict) -> np.ndarray:
    order = sorted([i for i in ids if p[i][0] is not None], key=lambda i: -p[i][1])
    err, out = 0, []
    for k, i in enumerate(order, 1):
        err += p[i][0] != meta[i]["gold"]
        out.append(err / k)
    return np.array(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--vllm", default="eredmenyek/F4/vllm")
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    meta = load_meta(_p(args.items))
    V = _p(args.vllm)
    res: dict = {}

    # --- split-szivárgás ------------------------------------------------------------------------------
    items = {s: read_jsonl(_p(args.items) / f"items_{s}.jsonl") for s in ["train"] + ALL_STRATA}
    tr_sup = Counter(r["meta"]["supplier"] for r in items["train"])
    tr_pairs = {(r["meta"]["supplier"], r["meta"]["article"]) for r in items["train"]}
    tr_text = {(norm(r["context"]["sor"]), r["gold"]) for r in items["train"]}
    res["split_szivargas"] = {}
    for s in ALL_STRATA:
        sups = Counter(r["meta"]["supplier"] for r in items[s])
        seen = [x for x in sups if x in tr_sup]
        res["split_szivargas"][s] = {
            "itemek": len(items[s]), "szallitok": len(sups), "szallitok_a_trainben": len(seen),
            "e_szallitok_train_sorai": sum(tr_sup[x] for x in seen),
            "szallito_cikk_par_atfedes": sum((r["meta"]["supplier"], r["meta"]["article"]) in tr_pairs for r in items[s]),
            "sorszoveg_gold_duplikatum": sum(r["gold"] is not None and (norm(r["context"]["sor"]), r["gold"]) in tr_text
                                             for r in items[s])}

    # --- karok (vLLM, a fő F4-példány) -----------------------------------------------------------------
    l1 = load(V, "l0_val.jsonl", "l0_test.jsonl", meta, "perm_avg")
    l3 = [load(V, f"l3_s{k}_val.jsonl", f"l3_s{k}_test.jsonl", meta, "temp") for k in (1, 2, 3)]
    val = sorted(i for i in l1 if meta[i]["split"] in VAL_STRATA)
    test = sorted(i for i in l1 if meta[i]["split"] in TEST_STRATA)
    sc = [i for i in test if not meta[i].get("ketertelmu")]
    t1 = {tg: choose_tau(l1, meta, val, tg) for tg in (0.95, 0.90)}
    t3 = {tg: [choose_tau(p, meta, val, tg) for p in l3] for tg in (0.95, 0.90)}

    def gain(ids: list[str], tg: float = 0.95) -> float:
        return float(np.mean([cov(p, ids, t) for p, t in zip(l3, t3[tg])]) - cov(l1, ids, t1[tg]))

    # --- szállítói általánosítás ---------------------------------------------------------------------
    by_sup = defaultdict(list)
    for i in sc:
        if meta[i]["split"] == "T-szallito":
            by_sup[meta[i]["supplier"]].append(i)
    rows = [{"szallito": s, "train_sorok": tr_sup[s], "n": len(ids), "nyereseg_lef95": gain(ids)}
            for s, ids in sorted(by_sup.items())]
    rho = spearmanr([r["train_sorok"] for r in rows], [r["nyereseg_lef95"] for r in rows])
    seen_split = {}
    for s in ("T-belso", "T-kozeli", "T-tavoli"):
        g = defaultdict(list)
        for i in sc:
            if meta[i]["split"] == s:
                g["latott" if tr_sup[meta[i]["supplier"]] else "nem_latott"].append(i)
        seen_split[s] = {k: {"n": len(v), "L1csillag": cov(l1, v, t1[0.95]),
                             "L3": float(np.mean([cov(p, v, t) for p, t in zip(l3, t3[0.95])])), "nyereseg": gain(v)}
                         for k, v in g.items()}
    res["szallitoi_altalanositas"] = {"T_szallito_szallitonkent": rows,
                                      "spearman_train_sorok_nyereseg": float(getattr(rho, "statistic")),
                                      "spearman_p": float(getattr(rho, "pvalue")), "latott_vs_nem_latott": seen_split}

    # --- plafon, hibaszerkezet --------------------------------------------------------------------------
    errs = {}
    for name, p in (("L1csillag", l1), ("L3_s1", l3[0])):
        for tg in (0.95, 0.90):
            tau = t1[tg] if name == "L1csillag" else t3[tg][0]
            asg = [i for i in sc if p[i][0] is not None and p[i][1] >= tau]
            errs[f"{name}@{int(tg * 100)}"] = {
                "lef": len(asg) / len(sc), "precizitas": float(np.mean([p[i][0] == meta[i]["gold"] for i in asg])),
                "hiba_X_gold_besorolva": sum(meta[i]["gold"] is None for i in asg),
                "hiba_rossz_cikk": sum(meta[i]["gold"] is not None and p[i][0] != meta[i]["gold"] for i in asg)}
    res["plafon"] = {"nem_X_arany_pontozott_teszten": float(np.mean([meta[i]["gold"] is not None for i in sc])),
                     "hibaszerkezet": errs}

    # --- AURC-definíció ---------------------------------------------------------------------------------
    arms = {"L1csillag": l1, **{f"L3_s{k}": p for k, p in zip((1, 2, 3), l3)}}
    curves = {k: risk_curve(p, sc, meta) for k, p in arms.items()}
    n = len(sc)
    common = min(len(c) for c in curves.values()) / n
    res["aurc"] = {
        "sajat_gorbeig_hasznalt": {k: float(c.sum() / n) for k, c in curves.items()},
        "kar_max_lefedettsege": {k: len(c) / n for k, c in curves.items()},
        "kozos_lefedettseg": common,
        "kozos_lefedettsegig": {k: float(c[:int(common * n)].sum() / n) for k, c in curves.items()},
        "kockazat_rogzitett_lefedettsegen": {str(cv): {k: float(c[int(cv * n) - 1]) for k, c in curves.items()}
                                             for cv in (0.5, 0.6, 0.7)}}

    # --- X-arány-érzékenység ---------------------------------------------------------------------------
    rng = np.random.default_rng(1)
    vsc = [i for i in val if not meta[i].get("ketertelmu")]

    def thin(ids: list[str], prev: float) -> list[str]:
        x = [i for i in ids if meta[i]["gold"] is None]
        nx = [i for i in ids if meta[i]["gold"] is not None]
        k = min(len(x), int(round(prev / (1 - prev) * len(nx))))
        return nx + list(rng.choice(x, k, replace=False))
    sens = {}
    for prev in (0.25, 0.10, 0.05):
        d = []
        for _ in range(args.reps):
            v, t = thin(vsc, prev), thin(sc, prev)
            c1 = metrics(l1, meta, t, choose_tau(l1, meta, v, .95))["besorolasi_lefedettseg"]
            c3 = np.mean([metrics(p, meta, t, choose_tau(p, meta, v, .95))["besorolasi_lefedettseg"] for p in l3])
            d.append(c3 - c1)
        sens[str(prev)] = {"delta_atlag": float(np.mean(d)), "p5": float(np.percentile(d, 5)),
                           "p95": float(np.percentile(d, 95)), "plafon": 1 - prev}
    res["X_arany_erzekenyseg"] = sens

    # --- pont-Δ -----------------------------------------------------------------------------------------
    strata = {"pool": sc, **{s: [i for i in sc if meta[i]["split"] == s] for s in TEST_STRATA},
              "T-kategoria": [i for i in sc if meta[i]["split"] in ("T-kozeli", "T-tavoli")]}
    res["pont_delta_lef95"] = {k: gain(v) for k, v in strata.items()}

    # --- az L1★ temperature-e ------------------------------------------------------------------------------
    rv = read_jsonl(V / "l0_val.jsonl")
    bv = by_item(rv, None)
    vids = [i for i in bv if not meta[i].get("ketertelmu")]

    def nll(lt: float) -> float:
        p = arm_predictions("perm_avg", bv, meta, {"temp": math.exp(lt)})
        return -sum(math.log(max(1e-12, p[i][2].get(meta[i]["gold"], 1e-12))) for i in vids)
    temps = {"perm0_illesztes_hasznalt": fit_temperature([r for r in rv if r["perm"] == 0], meta),
             "perm_atlagra_illesztve": math.exp(getattr(minimize_scalar(nll, bounds=(-3, 4), method="bounded"), "x")), "T1": 1.0}
    res["L1csillag_temperature"] = {}
    for name, tmp in temps.items():
        p = load(V, "l0_val.jsonl", "l0_test.jsonl", meta, "perm_avg", tmp)
        m = metrics(p, meta, test, choose_tau(p, meta, val, .95))
        res["L1csillag_temperature"][name] = {"T": tmp, "ece": m["ece"], "lef95": m["besorolasi_lefedettseg"]}
    res["L3_ece_atlag"] = float(np.mean([metrics(p, meta, test, t)["ece"] for p, t in zip(l3, t3[0.95])]))

    write_json(_p(args.out), res)
    print(f"szivárgás T-szállító: {res['split_szivargas']['T-szallito']}")
    print(f"pont-Δ: { {k: round(v, 4) for k, v in res['pont_delta_lef95'].items()} }")
    print(f"X-arány: { {k: round(v['delta_atlag'], 4) for k, v in sens.items()} }")


if __name__ == "__main__":
    main()
