"""06-os kör — az F1 javulásának bontása NONE- és SELECT-javaslatokra (utólagos, leíró; Napló, 2026-10-29).

Rétegenként (a `b1rel06.py f1` kimenetéből), a teljes tanítómintás B1-R-rel:
  javaslatfajtánként   arány, szigorú és enyhe helyesség, AUROC (B1-S, B1-R0, B1-R, B1-LR)
  AURC (szigorú)       B1-S; B1-S·NONE-utolsó (a B1 saját sorrendje, de minden NONE-javaslat a SELECT-ek mögött; utólagos
                       viszonyítás, nem kar); B1-R0; B1-R; csak a SELECT-javaslatokon B1-S és B1-R
  CI                   a 05 v1a kétszintű húzása (család, azon belül alapeset; elemzes05.Slice), replikánként egy seed

  python3 kor06/eszkozok/bontas06.py --be cache/k06/f1 --reps 2000 --out kor06/eredmenyek/F1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import elemzes05 as E  # noqa: E402

SEEDS = (17, 42, 73)


def aurc(s: np.ndarray, err: np.ndarray) -> float:
    o = np.argsort(-s, kind="stable")
    return float(np.mean(np.cumsum(err[o]) / np.arange(1, len(o) + 1)))


def auroc(s: np.ndarray, y: np.ndarray) -> float | None:
    n1, n0 = int(y.sum()), int((~y).sum())
    if not n1 or not n0:
        return None
    r = rankdata(s)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def merok(q, r0, rf, err, none) -> dict[str, float]:
    sel = ~none
    return {"B1-S": aurc(q, err), "B1-S·NONE-utolsó": aurc(np.where(none, q - 10, q), err), "B1-R0": aurc(r0, err),
            "B1-R": aurc(rf, err), "SELECT: B1-S": aurc(q[sel], err[sel]), "SELECT: B1-R": aurc(rf[sel], err[sel])}


KONTR = (("B1-R", "B1-S"), ("B1-R", "B1-S·NONE-utolsó"), ("SELECT: B1-R", "SELECT: B1-S"))


def reteg(f: dict, t: str, reps: int, rng: np.random.Generator, seed_atlag: bool = False) -> dict:
    """`seed_atlag` (a 06 F5, D24): replikánként a három seed mérőjének átlaga; alapból (F1) replikánként egy seed."""
    b, P = f["B1"][t], f["pontszam"]
    L = E.Slice(t)
    pos = {i: n for n, i in enumerate(b["ids"])}
    if set(pos) != set(L.ids):
        raise SystemExit(f"{t}: a B1 itemjei eltérnek a szelettől")
    o = np.array([pos[i] for i in L.ids])
    b = {k: [b[k][n] for n in o] for k in ("javaslat", "helyes", "helyes_enyhe", "q")}
    P = {k: [v[n] for n in o] for k, v in P.items() if k.startswith("B1-") and k.endswith(f"|{t}")}
    kind = np.array(b["javaslat"])
    y = np.array([bool(x) for x in b["helyes"]])
    yl = np.array([bool(x) for x in b["helyes_enyhe"]])
    q = np.array(b["q"])
    none = kind == "NONE"
    R0 = {s: np.array(P[f"B1-R0|{s}|{t}"]) for s in SEEDS}
    RF = {s: np.array(P[f"B1-R|None|0|{s}|{t}"]) for s in SEEDS}
    lr = np.array(P[f"B1-LR|None|0|{t}"])
    fajta = {}
    for k in ("SELECT", "NONE"):
        m = kind == k
        fajta[k] = {"n": int(m.sum()), "arany": float(m.mean()), "szigoru": float(y[m].mean()), "enyhe": float(yl[m].mean()),
                    "auroc": {"B1-S": auroc(q[m], y[m]), "B1-R0": auroc(np.mean([R0[s] for s in SEEDS], 0)[m], y[m]),
                              "B1-R": auroc(np.mean([RF[s] for s in SEEDS], 0)[m], y[m]), "B1-LR": auroc(lr[m], y[m])}}
    err = ~y
    pont = {k: float(np.mean([merok(q, R0[s], RF[s], err, none)[k] for s in SEEDS])) for k in merok(q, R0[17], RF[17], err, none)}
    acc = {f"{x} − {z}": [] for x, z in KONTR}
    for _ in range(reps):
        it = L.draw(rng)
        if seed_atlag:
            ms = [merok(q[it], R0[s][it], RF[s][it], err[it], none[it]) for s in SEEDS]
            m = {k: float(np.mean([x[k] for x in ms])) for k in ms[0]}
        else:
            s = SEEDS[int(rng.integers(0, len(SEEDS)))]
            m = merok(q[it], R0[s][it], RF[s][it], err[it], none[it])
        for x, z in KONTR:
            acc[f"{x} − {z}"].append(m[x] - m[z])
    kontr = {k: {"pont": pont[k.split(" − ")[0]] - pont[k.split(" − ")[1]],
                 "ci95": [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]} for k, v in acc.items()}
    return {"n": len(y), "alapeset": sum(len(g) for g in L.fams), "csalad": len(L.fams), "fajta": fajta, "aurc": pont,
            "kontraszt": kontr}


def f(x: float | None, d: int = 3) -> str:
    return "–" if x is None else f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def lap(res: dict) -> str:
    L = ["# 06 F1 — a javulás bontása NONE- és SELECT-javaslatokra (utólagos, leíró)", "",
         f"Szigorú helyesség, a teljes tanítómintás B1-R; bootstrap {res['reps']} ismétlés, a 05 v1a kétszintű húzásával "
         "(család, azon belül alapeset). "
         "A B1-S·NONE-utolsó utólagos viszonyítás (a B1 sorrendje, a NONE-javaslatok a SELECT-ek mögött), nem kar.", "",
         "| réteg | fajta | arány | szigorú | enyhe | AUROC B1-S | B1-R0 | B1-R | B1-LR |", "|---|---|---|---|---|---|---|---|---|"]
    for t, v in res["retegek"].items():
        for k, x in v["fajta"].items():
            a = x["auroc"]
            L.append(f"| {t.split(':')[1]} | {k} | {f(x['arany'], 2)} | {f(x['szigoru'])} | {f(x['enyhe'])} | "
                     f"{f(a['B1-S'])} | {f(a['B1-R0'])} | {f(a['B1-R'])} | {f(a['B1-LR'])} |")
    L += ["", "| réteg | B1-S | B1-S·NONE-utolsó | B1-R0 | B1-R | SELECT: B1-S | SELECT: B1-R |", "|---|---|---|---|---|---|---|"]
    for t, v in res["retegek"].items():
        a = v["aurc"]
        L.append(f"| {t.split(':')[1]} | " + " | ".join(f(a[k], 4) for k in ("B1-S", "B1-S·NONE-utolsó", "B1-R0", "B1-R",
                                                                           "SELECT: B1-S", "SELECT: B1-R")) + " |")
    L += ["", "| réteg | összevetés | ΔAURC [CI] |", "|---|---|---|"]
    for t, v in res["retegek"].items():
        for k, c in v["kontraszt"].items():
            L.append(f"| {t.split(':')[1]} | {k} | {f(c['pont'], 4)} [{f(c['ci95'][0], 4)}; {f(c['ci95'][1], 4)}] |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--be", required=True)
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    res = {"reps": a.reps, "retegek": {}}
    for p in sorted(Path(a.be).glob("*/f1.json")):
        fj = json.loads(p.read_text())
        for t in fj["B1"]:
            res["retegek"][t] = reteg(fj, t, a.reps, rng)
            print(f"{t} kész", flush=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "bontas06.md").write_text(lap(res), encoding="utf-8")
    (out / "bontas06.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
