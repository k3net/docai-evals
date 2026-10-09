"""00b — utólagos, leíró önellenőrzés a H2-szállító′ mellé (nem előre rögzített; 2026-10-07).

A K00b/B-ben a nyereség (+19,5 pont vLLM-en) kétszerese lett a 15. pont feltáró becslésének (~+9), ezért:
  * split a TÉNYLEGES tanítóhalmaz (az F1 train) ellenében: a 00b-generátor saját `items_train.jsonl`-je a
    jelölt-összeállítás újrafuttatása miatt eltér az F1-étől (a train-párok azonosak), a split-audit a
    duplikátumot ahhoz mérte;
  * szállítónkénti nyereség (rögzített val-τ), a pozitív nyereségű szállítók száma;
  * a nyereség a train-nel azonos (normalizált sorszöveg, gold) és az azonos sorszövegű itemek nélkül;
  * X-fajtánként az X-fedés (a: kényszerített, a-természetes, b: nem látott cikk), hibaszerkezet @95;
  * összevetés az F4 rétegeivel (ugyanazok az adapterek, a fő F4-példány): L1★ és L3 lef@95 rétegenként.
Motoronként (vLLM, HF) számol; a karok és a τ-k a `k00b_elemzes.py` szerintiek.

  LDH_EXP=$PWD python3 eszkozok/k00b_onellenorzes.py --out eredmenyek/K00b/onellenorzes.json
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import TEST_STRATA, VAL_STRATA, _p, arm_predictions, by_item, choose_tau, fit_temperature, load_meta  # noqa: E402

SPLIT = "T-ujszallito"


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def load(val: Path, test: Path, meta: dict, arm: str) -> dict:
    rv, rt = read_jsonl(val), read_jsonl(test)
    t = fit_temperature([r for r in rv if r["perm"] == 0], meta)
    return {**arm_predictions(arm, by_item(rv, None), meta, {"temp": t}),
            **arm_predictions(arm, by_item(rt, None), meta, {"temp": t})}


def assigned(p: dict, i: str, tau: float) -> bool:
    return p[i][0] is not None and p[i][1] >= tau


def cov(p: dict, ids: list[str], tau: float) -> float:
    return float(np.mean([assigned(p, i, tau) for i in ids])) if ids else float("nan")


class Arms:
    """L1★ és L3 × 3 a val-on választott τ@95-tel."""

    def __init__(self, l1: dict, l3: list[dict], meta: dict, val: list[str]):
        self.l1, self.l3 = l1, l3
        self.t1 = choose_tau(l1, meta, val, 0.95)
        self.t3 = [choose_tau(p, meta, val, 0.95) for p in l3]

    def c1(self, ids: list[str]) -> float:
        return cov(self.l1, ids, self.t1)

    def c3(self, ids: list[str]) -> float:
        return float(np.mean([cov(p, ids, t) for p, t in zip(self.l3, self.t3)]))

    def gain(self, ids: list[str]) -> float:
        return self.c3(ids) - self.c1(ids)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items-val", default="adat/f1")
    ap.add_argument("--items-test", default="adat/k00b/meres")
    ap.add_argument("--k00b", default="eredmenyek/K00b")
    ap.add_argument("--f4", default="eredmenyek/F4/vllm")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    mf1 = load_meta(_p(args.items_val))
    meta = {i: m for i, m in mf1.items() if m["split"] in VAL_STRATA}
    meta |= {i: m for i, m in load_meta(_p(args.items_test)).items() if m["split"] == SPLIT}
    T = read_jsonl(_p(args.items_test) / f"items_{SPLIT}.jsonl")
    f1_train = read_jsonl(_p(args.items_val) / "items_train.jsonl")
    res: dict = {"megjegyzes": "utólagos, leíró; nem előre rögzített"}

    # --- split a tényleges tanítóhalmaz ellenében ------------------------------------------------------
    f1p = read_jsonl(_p(args.items_val) / "parok.jsonl")
    kp = read_jsonl(_p(args.items_test).parent / "parok.jsonl")
    tr_pairs_f1 = sorted((p["supplier"], p["article"]) for p in f1p if p["split"] == "train")
    tr_pairs_k = sorted((p["supplier"], p["article"]) for p in kp if p["split"] == "train")
    tr_art = {a for _, a in tr_pairs_f1}
    tr_item_art = {r["meta"]["article"] for r in f1_train}
    dup_sg = {(norm(r["context"]["sor"]), r["gold"]) for r in f1_train}
    dup_s = {norm(r["context"]["sor"]) for r in f1_train}
    is_dup_sg = {r["id"]: r["gold"] is not None and (norm(r["context"]["sor"]), r["gold"]) in dup_sg for r in T}
    is_dup_s = {r["id"]: norm(r["context"]["sor"]) in dup_s for r in T}
    no_item = {r["id"] for r in T if r["meta"]["x_fajta"] != "b" and r["meta"]["article"] not in tr_item_art}
    res["split_f1_train_ellen"] = {
        "train_parok_azonosak_f1_k00b": tr_pairs_f1 == tr_pairs_k,
        "szallito_az_f1_ben": sorted({r["meta"]["supplier"] for r in T} & {p["supplier"] for p in f1p}),
        "nem_xb_item_cikke_f1_train_par_nelkul": sum(r["meta"]["x_fajta"] != "b" and r["meta"]["article"] not in tr_art
                                                     for r in T),
        "nem_xb_item_cikke_f1_train_item_nelkul": len(no_item),
        "sorszoveg_gold_duplikatum_f1_trainnel": sum(is_dup_sg.values()),
        "sorszoveg_egyezes_f1_trainnel": sum(is_dup_s.values()),
        "x_fajta": dict(Counter(str(r["meta"]["x_fajta"]) for r in T))}

    # --- motoronként --------------------------------------------------------------------------------------
    K = _p(args.k00b)
    seeds = (K / "seedek.txt").read_text().split()
    engines = {
        "vllm": (K / "vllm/l0_val.jsonl", K / "vllm/l0_test.jsonl",
                 [(K / f"vllm/l3_s{k}_val.jsonl", K / f"vllm/l3_s{k}_test.jsonl") for k in (1, 2, 3)]),
        "hf": (_p("eredmenyek/F2/hf_val.jsonl"), K / "hf/l0_test.jsonl",
               [(_p(f"eredmenyek/F3/{s}/hf_val.jsonl"), K / f"hf/l3_s{k}_test.jsonl") for k, s in enumerate(seeds, 1)])}
    for eng, (v0, t0, l3f) in engines.items():
        l1 = load(v0, t0, meta, "perm_avg")
        l3 = [load(v, t, meta, "temp") for v, t in l3f]
        val = sorted(i for i in l1 if i in meta and meta[i]["split"] in VAL_STRATA)
        sc = sorted(i for i in l1 if i in meta and meta[i]["split"] == SPLIT and not meta[i].get("ketertelmu"))
        A = Arms(l1, l3, meta, val)
        by_sup = defaultdict(list)
        for i in sc:
            by_sup[meta[i]["supplier"]].append(i)
        rows = [{"szallito": s, "n": len(ids), "nem_X_arany": float(np.mean([meta[i]["gold"] is not None for i in ids])),
                 "L1csillag": A.c1(ids), "L3": A.c3(ids), "nyereseg": A.gain(ids)} for s, ids in sorted(by_sup.items())]
        subsets = {"mind": sc,
                   "sorszoveg_gold_duplikatum_nelkul": [i for i in sc if not is_dup_sg[i]],
                   "sorszoveg_egyezes_nelkul": [i for i in sc if not is_dup_s[i]],
                   "f1_train_item_nelkuli_cikkek_nelkul": [i for i in sc if i not in no_item]}
        xf = {}
        for kind in ("a", "a-termeszetes", "b"):
            ids = [i for i in sc if meta[i]["x_fajta"] == kind]
            xf[kind] = {"n": len(ids), "L1csillag_x_fedes": float(np.mean([l1[i][0] is None for i in ids])),
                        "L3_x_fedes": float(np.mean([np.mean([p[i][0] is None for p in l3]) for i in ids]))}
        errs = {}
        for name, p, tau in (("L1csillag", l1, A.t1), *((f"L3_s{k}", p, t) for k, (p, t) in enumerate(zip(l3, A.t3), 1))):
            asg = [i for i in sc if assigned(p, i, tau)]
            errs[name] = {"lef": len(asg) / len(sc),
                          "hiba_X_gold_besorolva": sum(meta[i]["gold"] is None for i in asg),
                          "hiba_rossz_cikk": sum(meta[i]["gold"] is not None and p[i][0] != meta[i]["gold"] for i in asg)}
        res[eng] = {"szallitonkent": rows,
                    "pozitiv_nyeresegu_szallitok": sum(r["nyereseg"] > 0 for r in rows),
                    "nyereseg_min_max": [min(r["nyereseg"] for r in rows), max(r["nyereseg"] for r in rows)],
                    "reszhalmazok": {k: {"n": len(v), "L1csillag": A.c1(v), "L3": A.c3(v), "nyereseg": A.gain(v)}
                                     for k, v in subsets.items()},
                    "x_fajtankent": xf, "hibaszerkezet_95": errs}

    # --- összevetés az F4 rétegeivel (vLLM, fő F4-példány) -----------------------------------------------
    F = _p(args.f4)
    l1 = load(F / "l0_val.jsonl", F / "l0_test.jsonl", mf1, "perm_avg")
    l3 = [load(F / f"l3_s{k}_val.jsonl", F / f"l3_s{k}_test.jsonl", mf1, "temp") for k in (1, 2, 3)]
    val = sorted(i for i in l1 if mf1[i]["split"] in VAL_STRATA)
    A = Arms(l1, l3, mf1, val)
    f4 = {}
    for s in TEST_STRATA:
        ids = [i for i in l1 if mf1[i]["split"] == s and not mf1[i].get("ketertelmu")]
        f4[s] = {"n": len(ids), "nem_X_arany": float(np.mean([mf1[i]["gold"] is not None for i in ids])),
                 "x_a_arany_X_kozt": float(np.mean([mf1[i].get("x_fajta") == "a" for i in ids if mf1[i]["gold"] is None])),
                 "L1csillag": A.c1(ids), "L3": A.c3(ids), "nyereseg": A.gain(ids)}
    v = res["vllm"]["reszhalmazok"]["mind"]
    xs = [r for r in T if r["gold"] is None and not r["meta"].get("ketertelmu")]
    f4[SPLIT + " (K00b)"] = {"n": v["n"], "x_a_arany_X_kozt": float(np.mean([r["meta"]["x_fajta"] == "a" for r in xs])),
                             "L1csillag": v["L1csillag"], "L3": v["L3"], "nyereseg": v["nyereseg"]}
    res["F4_retegek_osszevetes_vllm"] = f4

    write_json(_p(args.out), res)
    print(f"split: { {k: v for k, v in res['split_f1_train_ellen'].items() if k != 'x_fajta'} }")
    for eng in engines:
        r = res[eng]
        print(f"{eng}: pozitív szállító {r['pozitiv_nyeresegu_szallitok']}/16, min–max "
              f"{r['nyereseg_min_max'][0]:+.3f}…{r['nyereseg_min_max'][1]:+.3f}; "
              f"részhalmazok { {k: round(x['nyereseg'], 4) for k, x in r['reszhalmazok'].items()} }")
    for s, x in f4.items():
        print(f"  {s}: L1★ {x['L1csillag']:.3f}  L3 {x['L3']:.3f}  Δ {x['nyereseg']:+.4f}  X(a)-arány {x['x_a_arany_X_kozt']:.2f}")


if __name__ == "__main__":
    main()
