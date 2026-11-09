"""06-os kör — erő-szimuláció a v1 előtt (06-runbook 8.5, F4), a 03 `mde03` módszerével (MDE = 2,80 · SE, 80% erő,
kétoldali α = 0,05), a fejlesztési adat (3.3) hatásméreteivel.

Bemenet: a `b1rel06.py f1` v0.2-es kimenete (`cache/k06/f1b`), a három szűrőréteg (HO-termék, HO-routing, HO-új) mint a
friss családok helyettesítője; kar a B1-S és a B1-R a teljes tanítómintával (≈ T500). A friss családok TESZT-je
alapesetenként egy item (D12), ezért replikánként N alapeset visszatevéssel, mindegyikből egy véletlen item, és egy
véletlen seed (8.2). Rétegenként egy szintű a mintavétel: a friss család egyetlen család.
Kimenet rétegenként: az AURC szórása N-nél, az MDE abszolútan és a B1-S AURC-jéhez viszonyítva, a „javul” (B1-R − B1-S
< 0) valószínűsége a mért hatás mellett; az átlagra az átlag(AURC_R) / átlag(AURC_S) arány szórása, az MDE relatív
csökkenésként, a 8.3 szabály (két pontja és a D4) teljesülésének valószínűsége a mért hatások mellett, és a
„pontosan 10% valódi csökkenés” forgatókönyvben a D4 ereje normális közelítéssel. Csak tervezés: a friss családok
hatása ismeretlen.

  python3 kor06/eszkozok/mde06.py --be cache/k06/f1b --n 1000 --reps 4000 --out kor06/eredmenyek/F4
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import diag05 as D  # noqa: E402
import elemzes05 as E  # noqa: E402
import elemzes06 as A  # noqa: E402

KAROK = ("B1-S", "B1-R|None")
Z = 1.959964


def phi(x: float) -> float:
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def reteg(f: dict, t: str, n: int, reps: int, rng: np.random.Generator) -> dict:
    L = E.Slice(t)
    T = A.karok(f, t, "helyes", L.ids)
    bases = [g for fam in L.fams for g in fam]
    s0 = L.full()
    pont = {k: float(np.mean([D.parts(x, s0)[0] for row in T[k] for x in row])) for k in KAROK}
    out = {k: np.empty(reps) for k in KAROK}
    for r in range(reps):
        pick = rng.integers(0, len(bases), n)
        s = np.array([bases[b][rng.integers(0, len(bases[b]))] for b in pick])
        for k in KAROK:
            row = T[k][int(rng.integers(0, len(T[k])))]
            out[k][r] = D.parts(row[int(rng.integers(0, len(row)))], s)[0]
    d = out["B1-R|None"] - out["B1-S"]
    se = float(np.std(d, ddof=1))
    aS = float(np.mean(out["B1-S"]))
    return {"n_dev_item": len(L.ids), "n_dev_alapeset": len(bases), "pont_dev": pont,
            "atlag_n": {k: float(np.mean(v)) for k, v in out.items()}, "delta_atlag_n": float(np.mean(d)),
            "se_delta": se, "mde80_abs": 2.80 * se, "mde80_rel": 2.80 * se / aS if aS else None,
            "relativ_hatas_dev": float(np.mean(d)) / aS if aS else None, "p_javul": float(np.mean(d < 0)),
            "_rep": {k: v for k, v in out.items()}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--be", required=True)
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--reps", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261031)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    res = {"n_teszt_alapeset": a.n, "reps": a.reps, "seed": a.seed, "bemenet": a.be, "retegek": {}}
    for p in sorted(Path(a.be).glob("*/f1.json")):
        f = json.loads(p.read_text())
        for t in f["B1"]:
            if t in A.SZURO:
                res["retegek"][t] = reteg(f, t, a.n, a.reps, rng)
                print(t, {k: v for k, v in res["retegek"][t].items() if k != "_rep"}, flush=True)
    R = [res["retegek"][t] for t in A.SZURO]

    def arany(streams: list[dict]) -> np.ndarray:
        return np.mean([x["B1-R|None"] for x in streams], axis=0) / np.mean([x["B1-S"] for x in streams], axis=0)

    def valodi(se: float) -> dict:
        # adott valódi relatív csökkenésnél, normális közelítéssel (az 1. pont nélkül): a pontbecslés ≤ 0,90, a D4
        # (a 95%-os felső határ < 1) és a kettő együtt
        return {f"{r:.2f}": {"p_pont": phi((0.90 - (1 - r)) / se), "p_d4": phi((1 - Z * se - (1 - r)) / se),
                             "p_egyutt": phi((min(0.90, 1 - Z * se) - (1 - r)) / se)} for r in (0.10, 0.15, 0.20, 0.30)}

    ratio = arany([x["_rep"] for x in R])
    se_r = float(np.std(ratio, ddof=1))
    javul = np.sum([x["_rep"]["B1-R|None"] < x["_rep"]["B1-S"] for x in R], axis=0)
    d4 = ratio + Z * se_r < 1  # a D4, a replikák SE-jével közelítve
    res["atlag"] = {"arany_dev_hatassal": float(np.mean(ratio)), "se_arany": se_r, "mde80_rel_csokkenes": 2.80 * se_r,
                    "p_szabaly_1": float(np.mean(javul >= 2)), "p_szabaly_2_pont": float(np.mean(ratio <= 0.90)),
                    "p_d4": float(np.mean(d4)), "p_teljes_szabaly": float(np.mean((javul >= 2) & (ratio <= 0.90) & d4)),
                    "valodi": valodi(se_r)}
    # három, egymástól független, ugyanilyen szerkezetű család (a réteg replikáinak három független keverése): a
    # HO-routing magas AURC-je nélkül az átlag SE-je a friss családokra mérvadóbb
    res["harom_ilyen"] = {}
    for t, x in res["retegek"].items():
        cs = []
        for _ in range(3):
            pi = rng.permutation(a.reps)
            cs.append({k: v[pi] for k, v in x["_rep"].items()})
        se = float(np.std(arany(cs), ddof=1))
        res["harom_ilyen"][t] = {"se_arany": se, "mde80_rel_csokkenes": 2.80 * se, "valodi": valodi(se)}
    for x in R:
        x.pop("_rep")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "mde06.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    at = res["atlag"]
    md = ["# Erő-szimuláció (06, F4, 8.5)", "",
          f"Fejlesztési rétegek mint a friss családok helyettesítői; {a.n} TESZT-alapeset, alapesetenként egy item; "
          f"{a.reps} replika. B1-R a teljes tanítómintával. Csak tervezés.", "",
          "| réteg | AURC B1-S (n=N) | ΔAURC a dev hatással | relatív | SE(Δ) | MDE80 abs | MDE80 relatív | P(javul) |",
          "|---|---|---|---|---|---|---|---|"]
    for t, x in res["retegek"].items():
        md.append(f"| {t} | {x['atlag_n']['B1-S']:.4f} | {x['delta_atlag_n']:+.4f} | {x['relativ_hatas_dev']:+.1%} | "
                  f"{x['se_delta']:.4f} | {x['mde80_abs']:.4f} | {x['mde80_rel']:.1%} | {x['p_javul']:.3f} |")
    md += ["", f"**A három réteg átlaga (egyenlő súly):** arány a dev hatással {at['arany_dev_hatassal']:.3f}, SE "
               f"{at['se_arany']:.4f}, az MDE80 relatív csökkenésként {at['mde80_rel_csokkenes']:.1%}. A 8.3 szabály "
               f"valószínűsége a dev hatások mellett: 1. pont {at['p_szabaly_1']:.3f}, 2. pont {at['p_szabaly_2_pont']:.3f}, "
               f"D4 {at['p_d4']:.3f}, együtt {at['p_teljes_szabaly']:.3f}. Ezt a HO-routing nagy hatása és magas AURC-je "
               "uralja.", "",
           "**Az átlag ereje adott valódi relatív csökkenésnél** (normális közelítés, az 1. pont nélkül; P(pont) = a "
           "pontbecslés ≥ 10%, P(D4) = a 95%-os intervallum 0 felett, P(együtt) = a 2. pont a D4-gyel):", "",
           "| szerkezet | SE(arány) | MDE80 | 10%: pont / D4 / együtt | 15% | 20% | 30% |", "|---|---|---|---|---|---|---|"]

    def sor(nev: str, se: float, v: dict) -> str:
        cel = " | ".join(f"{v[r]['p_pont']:.2f} / {v[r]['p_d4']:.2f} / {v[r]['p_egyutt']:.2f}" for r in v)
        return f"| {nev} | {se:.4f} | {2.80 * se:.1%} | {cel} |"
    md.append(sor("a három dev réteg", se_r, at["valodi"]))
    md += [sor(f"3 × {t}", x["se_arany"], x["valodi"]) for t, x in res["harom_ilyen"].items()]
    md += ["", "A forgatókönyvek SE-je a dev hatások melletti SE (közelítés); a valódi csökkenés minden családban azonos."]
    (out / "mde06.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md), flush=True)


if __name__ == "__main__":
    main()
