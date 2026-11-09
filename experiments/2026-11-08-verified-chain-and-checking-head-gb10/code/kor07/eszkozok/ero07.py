"""07-es kör — F4: erőbecslés a tervezési próbából (07-runbook 5., D5; a 06 `mde06` módszere a 07 statisztikájával).

Bemenet: a `b1rel07 pontoz` kimenete a 06 TESZT-en (`cache/k07/f3r_proba/k06_<család>_TESZT.json`): mindkét keret
döntései és pontszámai. A 06 adata ismert, ezért ez tervezési becslés, nem állítás. A friss TESZT a 06-éval azonos
szerkezetű (családonként 1000 item, 60 sabloncsoport, ugyanaz az állapot- és nyelvösszetétel), így a próba
bootstrapja közvetlenül a friss teszt bizonytalanságát becsüli; a hatás nagysága a friss adaton ismeretlen.
Módszer: sabloncsoportos klaszteres bootstrap (D23: a sabloncsoportok visszatevéssel, ugyanannyi csoport), replikánként
a futások (seedek) mérőinek átlaga (D24). K1: AURC a négyosztályos szigorú helyességgel a négyállapotú karokon (B1-4S,
B1-4R0, B1-4R, B1-4LR), a 06 keret karjain (B1-S, B1-R0, B1-R, B1-LR) a 06 szigorú helyességével.
Kimenet párokként (fő: B1-4R − B1-4S), családonként: AURC, Δ, relatív hatás, SE(Δ), MDE80 (2,80·SE), P(javul); a három
család egyenlő súlyú átlagára: az arány, SE, MDE80 relatív csökkenésként, a 06 8.3 szabály (1. pont: ≥ 2 család javul;
2. pont: arány ≤ 0,90; D4: a 95%-os felső határ < 1) valószínűsége a próba hatásai mellett, és az erő adott valódi
relatív csökkenésnél (normális közelítés, az 1. pont nélkül). A keresztpár (B1-4S − B1-R) csak leíró (D13).

  python3 kor07/eszkozok/ero07.py --be cache/k07/f3r_proba --reps 4000 --out kor07/eredmenyek/F4
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE)]

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
ITEMS06 = EXP / "kor06/adat/f2/items"
SEEDS = (17, 42, 73)
KAROK = {"keret4": ("B1-4S", "B1-4R0", "B1-4R", "B1-4LR"), "keret2": ("B1-S", "B1-R0", "B1-R", "B1-LR")}
PAROK = {"K1: B1-4R − B1-4S": (("keret4", "B1-4R"), ("keret4", "B1-4S")),
         "B1-4LR − B1-4S": (("keret4", "B1-4LR"), ("keret4", "B1-4S")),
         "B1-4R − B1-4LR": (("keret4", "B1-4R"), ("keret4", "B1-4LR")),
         "B1-4R0 − B1-4S": (("keret4", "B1-4R0"), ("keret4", "B1-4S")),
         "06: B1-R − B1-S": (("keret2", "B1-R"), ("keret2", "B1-S")),
         "kereszt (leíró): B1-4S − B1-R": (("keret4", "B1-4S"), ("keret2", "B1-R")),
         "kereszt (leíró): B1-4R − B1-R": (("keret4", "B1-4R"), ("keret2", "B1-R"))}
Z = 1.959964


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def aurc(q: np.ndarray, cor: np.ndarray) -> float:
    o = np.argsort(-q, kind="stable")
    err = np.cumsum(~cor[o])
    return float((err / np.arange(1, len(q) + 1)).mean())


def betolt(be: Path, fam: str) -> dict:
    """Itemsorrendbe igazított pontszámok (karonként a seedek listája) és helyesség mindkét keretre, a sabloncsoport."""
    d = json.loads((be / f"k06_{fam}_TESZT.json").read_text())
    ids = d["keret4"]["ids"]
    if set(ids) != set(d["keret2"]["ids"]):
        raise SystemExit(f"{fam}: a két keret itemjei eltérnek")
    pos2 = {i: n for n, i in enumerate(d["keret2"]["ids"])}
    al = np.array([pos2[i] for i in ids])
    sablon = {it["id"]: it["template_group_id"] for it in map(json.loads, (ITEMS06 / f"{fam}.jsonl").read_text().splitlines()) if it}
    out = {"ids": ids, "sablon": [sablon[i] for i in ids], "pont": {}, "helyes": {}}
    for keret in ("keret4", "keret2"):
        P = d[keret]["pontszam"]
        for kar in KAROK[keret]:
            cols = [np.array(P[f"{kar}|{s}"]) for s in SEEDS] if f"{kar}|{SEEDS[0]}" in P else [np.array(P[kar])]
            out["pont"][(keret, kar)] = [c[al] if keret == "keret2" else c for c in cols]
        h = np.array([bool(d[keret]["dontes"][i]["helyes"]) for i in d[keret]["ids"]])
        out["helyes"][keret] = h[al] if keret == "keret2" else h
    return out


def bootstrap(f: dict, reps: int, rng: np.random.Generator) -> dict:
    cl = defaultdict(list)
    for n, s in enumerate(f["sablon"]):
        cl[s].append(n)
    clusters = [np.array(v) for v in cl.values()]
    C = len(clusters)
    out = {k: np.empty(reps) for k in f["pont"]}
    for r in range(reps):
        idx = np.concatenate([clusters[c] for c in rng.integers(0, C, C)])
        for (keret, kar), cols in f["pont"].items():
            h = f["helyes"][keret][idx]
            out[(keret, kar)][r] = float(np.mean([aurc(c[idx], h) for c in cols]))  # D24: a futások átlaga
    pont = {k: float(np.mean([aurc(c, f["helyes"][k[0]]) for c in cols])) for k, cols in f["pont"].items()}
    return {"n_item": len(f["ids"]), "n_sablon": C, "pont": pont, "_rep": out}


def valodi(se: float) -> dict:
    return {f"{r:.2f}": {"p_pont": phi((0.90 - (1 - r)) / se), "p_d4": phi((1 - Z * se - (1 - r)) / se),
                         "p_egyutt": phi((min(0.90, 1 - Z * se) - (1 - r)) / se)} for r in (0.05, 0.10, 0.15, 0.20, 0.30)}


def par(R: dict[str, dict], a: tuple, b: tuple) -> dict:
    cs = {}
    for fam, x in R.items():
        d = x["_rep"][a] - x["_rep"][b]
        se = float(np.std(d, ddof=1))
        aB = x["pont"][b]
        cs[fam] = {"aurc_A": x["pont"][a], "aurc_B": aB, "delta": x["pont"][a] - aB, "relativ": (x["pont"][a] - aB) / aB if aB else None,
                   "se_delta": se, "ci95_delta": [float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))],
                   "mde80_abs": 2.80 * se, "mde80_rel": 2.80 * se / aB if aB else None, "p_javul": float(np.mean(d < 0))}
    ratio = np.mean([x["_rep"][a] for x in R.values()], axis=0) / np.mean([x["_rep"][b] for x in R.values()], axis=0)
    se_r = float(np.std(ratio, ddof=1))
    javul = np.sum([x["_rep"][a] < x["_rep"][b] for x in R.values()], axis=0)
    d4 = ratio + Z * se_r < 1
    pont_arany = float(np.mean([x["pont"][a] for x in R.values()]) / np.mean([x["pont"][b] for x in R.values()]))
    return {"csaladok": cs,
            "atlag": {"arany_pont": pont_arany, "arany_ci95": [float(np.quantile(ratio, 0.025)), float(np.quantile(ratio, 0.975))],
                      "se_arany": se_r, "mde80_rel_csokkenes": 2.80 * se_r,
                      "p_szabaly_1": float(np.mean(javul >= 2)), "p_szabaly_2_pont": float(np.mean(ratio <= 0.90)),
                      "p_d4": float(np.mean(d4)), "p_teljes_szabaly": float(np.mean((javul >= 2) & (ratio <= 0.90) & d4)),
                      "valodi": valodi(se_r)}}


def f(x, d: int = 4, pct: bool = False) -> str:
    if x is None:
        return "–"
    return (f"{100 * x:.1f}%" if pct else f"{x:.{d}f}").replace(".", ",")


def lap(res: dict) -> str:
    L = ["# 07 F4 — erőbecslés a tervezési próbából (a 06 TESZT, ismert adat; nem állítás)", "",
         f"Sabloncsoportos klaszteres bootstrap ({res['reps']} replika, seed {res['seed']}), a futások átlaga replikánként; "
         "AURC a szigorú helyességgel (négyállapotú keret: négyosztályos). A friss TESZT azonos szerkezetű (1000 item, "
         "60 sabloncsoport családonként). MDE80 = 2,80 · SE.", ""]
    for nev, p in res["parok"].items():
        at = p["atlag"]
        L += [f"## {nev}", "", "| család | AURC A | AURC B | Δ | relatív | SE(Δ) | Δ 95% CI | MDE80 abs | MDE80 rel | P(javul) |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for fam, c in p["csaladok"].items():
            L.append(f"| {fam} | {f(c['aurc_A'])} | {f(c['aurc_B'])} | {f(c['delta'])} | {f(c['relativ'], pct=True)} | {f(c['se_delta'])} | "
                     f"[{f(c['ci95_delta'][0])}; {f(c['ci95_delta'][1])}] | {f(c['mde80_abs'])} | {f(c['mde80_rel'], pct=True)} | {f(c['p_javul'], 3)} |")
        L += ["", f"**Átlag (egyenlő súly):** arány {f(at['arany_pont'], 3)} [{f(at['arany_ci95'][0], 3)}; {f(at['arany_ci95'][1], 3)}], "
                  f"SE {f(at['se_arany'])}, MDE80 relatív csökkenésként {f(at['mde80_rel_csokkenes'], pct=True)}. A 8.3 szabály a próba "
                  f"hatásai mellett: 1. pont {f(at['p_szabaly_1'], 3)}, 2. pont {f(at['p_szabaly_2_pont'], 3)}, D4 {f(at['p_d4'], 3)}, "
                  f"együtt {f(at['p_teljes_szabaly'], 3)}.", "",
              "Erő adott valódi relatív csökkenésnél (normális közelítés; P(pont): a pontbecslés ≥ 10%; P(D4): a felső határ < 1; "
              "P(együtt)):", "", "| valódi csökkenés | P(pont) | P(D4) | P(együtt) |", "|---|---|---|---|"]
        L += [f"| {k} | {f(v['p_pont'], 3)} | {f(v['p_d4'], 3)} | {f(v['p_egyutt'], 3)} |" for k, v in at["valodi"].items()]
        L.append("")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--be", default="cache/k07/f3r_proba")
    ap.add_argument("--reps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261101)
    ap.add_argument("--out", default="kor07/eredmenyek/F4")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    R = {}
    for fam in CSALADOK:
        R[fam] = bootstrap(betolt(EXP / a.be, fam), a.reps, rng)
        print(fam, {f"{k[1]}": round(v, 4) for k, v in R[fam]["pont"].items()}, flush=True)
    res = {"reps": a.reps, "seed": a.seed, "bemenet": a.be, "klaszter": "sabloncsoport", "futasatlag": "seedek (D24)",
           "csaladok": {fam: {k: v for k, v in x.items() if k != "_rep"} | {"pont": {f"{k[0]}|{k[1]}": v for k, v in x["pont"].items()}}
                        for fam, x in R.items()},
           "parok": {nev: par(R, A, B) for nev, (A, B) in PAROK.items()}}
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "ero.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "ero.md").write_text(lap(res), encoding="utf-8")
    print((out / "ero.md").read_text())


if __name__ == "__main__":
    main()
