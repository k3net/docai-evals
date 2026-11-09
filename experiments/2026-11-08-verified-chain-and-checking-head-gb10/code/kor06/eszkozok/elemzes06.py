"""06-os kör — az F1 fejlesztési futás elemzése a 05 HO-rétegein (06-runbook 3.3, 8.). Csak tervezést szolgál: a
HO-rétegek a 05a-ban már nyitva voltak, a friss családok tesztje a v1 után jön.

Rétegenként (a `b1rel06.py f1` kimenetéből) és helyességenként (szigorú: az elsődleges; enyhe: leíró, a szigorúra
tanított pontszámokkal):
  AURC (S+N; a DEFER a rangsor végén hibaként, a 05 v1a-definíciója) karonként és tanítóméretenként:
    B1-S, B1-N (NONE-javaslatok utoljára, v0.2 D8), B1-R0, B1-R|n, B1-LR|n, H (05, célterület nélkül), H-T-meta|n;
    n ∈ {100, 200, teljes}
  SELECT-AURC (v0.2 D7): ugyanez minden karnál ugyanazokon az itemeken, amelyekre a B1 SELECT-et javasolt
  NONE-on belüli AUROC (leíró, a B1-karoknál): a B1 NONE-javaslatain
  Δ a B1-S-hez; a H-karoknál ΔAURC* (a javaslatok) + ΔE-AURC (a sorrend) felbontással (diag05)
  Bootstrap: a teszt alapesetei klaszteresen, replikánként egy seed és egy húzás visszatevéssel (a pont a seedek és a
  húzások átlaga)
A 8.3 szabály próbája a három szűrőrétegen (HO-termék, HO-routing, HO-új) a teljes mintával: legalább kettőn
B1-R − B1-S < 0, és átlag(AURC_B1-R) / átlag(AURC_B1-S) ≤ 0,90, az arány CI-jével; mellette az abszolút javulás
rétegenkénti megoszlása (v0.2 D11).

  python3 kor06/eszkozok/elemzes06.py --be cache/k06/f1 --reps 2000 --out kor06/eredmenyek/F1
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
sys.path[:0] = [str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import diag05 as D  # noqa: E402
import elemzes05 as E  # noqa: E402

SZURO = ("teszt:ho-termek", "teszt:ho-routing", "teszt:ho-uj")
SEEDS = (17, 42, 73)
KULCSOK = ("helyes", "helyes_enyhe")
MEROK = ("aurc", "aurc_opt", "e_aurc", "sel_aurc", "sel_aurc_opt", "sel_e_aurc", "none_auroc")
PAROK = (("B1-R|None", "B1-N"), ("B1-R|None", "B1-LR|None"), ("B1-R|None", "B1-R0"), ("H-T-meta|None", "B1-R|None"))


def tab(ids: list[str], javaslat: list[str], cor: list, q: list[float], all_ids: list[str], key: str) -> E.Tab:
    return E.Tab([{"id": i, "javaslat": j, "q": s, key: c} for i, j, c, s in zip(ids, javaslat, cor, q)], all_ids, key)


def karok(f: dict, teszt: str, key: str, all_ids: list[str]) -> dict[str, list[list[E.Tab]]]:
    """Kar → [húzás][seed] táblák (a determinisztikus karoknál egy seed, a húzás nélkülieknél egy húzás)."""
    b = f["B1"][teszt]
    B = lambda q: tab(b["ids"], b["javaslat"], b[key], q, all_ids, key)  # noqa: E731
    P = f["pontszam"]
    q = np.array(b["q"])
    out = {"B1-S": [[B(b["q"])]], "B1-N": [[B(np.where(np.array(b["javaslat"]) == "NONE", q - 10, q).tolist())]],
           "B1-R0": [[B(P[f"B1-R0|{s}|{teszt}"]) for s in SEEDS]]}

    def H(s, q):
        hh = f["H"][f"{s}|{teszt}"]
        return tab(hh["ids"], hh["javaslat"], hh[key], q, all_ids, key)
    out["H"] = [[H(s, P[f"H|{s}|{teszt}"]) for s in SEEDS]]
    for n in ("100", "200", "None"):
        ds = sorted({d for (nn, d) in f["konfig"] if str(nn) == n})
        out[f"B1-R|{n}"] = [[B(P[f"B1-R|{n}|{d}|{s}|{teszt}"]) for s in SEEDS] for d in ds]
        out[f"B1-LR|{n}"] = [[B(P[f"B1-LR|{n}|{d}|{teszt}"])] for d in ds]
        out[f"H-T-meta|{n}"] = [[H(s, P[f"H-T-meta|{n}|{d}|{s}|{teszt}"]) for s in SEEDS] for d in ds]
    return out


def merok(t: E.Tab, s: np.ndarray, sel: np.ndarray, none: np.ndarray) -> list[float]:
    """A MEROK sorrendjében; sel/none: a B1 SELECT-, illetve NONE-javaslatai a szelet itemsorrendjén."""
    return [*D.parts(t, s), *D.parts(t, s[sel[s]]), D.auroc(t, s[none[s]])]


def pont(tabs: list[list[E.Tab]], s, sel, none) -> np.ndarray:
    return np.mean([merok(t, s, sel, none) for row in tabs for t in row], axis=0)


def rep(tabs: list[list[E.Tab]], s, sel, none, rng: np.random.Generator) -> np.ndarray:
    row = tabs[int(rng.integers(0, len(tabs)))]
    return np.array(merok(row[int(rng.integers(0, len(row)))], s, sel, none))


def summ(v: list[float], p: float) -> dict:
    a = np.array(v, float)
    a = a[~np.isnan(a)]
    if not len(a):  # nem értelmezhető mérő (pl. a NONE-on belüli AUROC, ha a NONE-javaslatok mind helyesek; a 06 F5-ben)
        return {"pont": p, "ci95": None, "p": math.nan}
    return {"pont": p, "ci95": [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))], "p": E.p_two(a)}


def elemez(f: dict, teszt: str, key: str, reps: int, rng: np.random.Generator) -> dict:
    L = E.Slice(teszt)
    T = karok(f, teszt, key, L.ids)
    s0 = L.full()
    b1 = T["B1-S"][0][0]
    sel, none = b1.sel, b1.none
    pt = {k: pont(v, s0, sel, none) for k, v in T.items()}
    acc = {k: [] for k in T}
    for _ in range(reps):
        d = L.draw(rng)
        for k, v in T.items():
            acc[k].append(rep(v, d, sel, none, rng))
    acc = {k: np.array(v) for k, v in acc.items()}
    J = {m: j for j, m in enumerate(MEROK)}
    res = {"n": len(L.ids), "n_select": int(sel.sum()), "n_none": int(none.sum()),
           "karok": {k: {m: float(v[j]) for m, j in J.items()} for k, v in pt.items()}, "delta_B1S": {},
           "none_auroc_ci": {k: summ(acc[k][:, J["none_auroc"]].tolist(), float(pt[k][J["none_auroc"]]))["ci95"]
                             for k in T if k.startswith("B1-")},
           "_rep_aurc": {k: v[:, 0].tolist() for k, v in acc.items()}}
    D_MEROK = ("aurc", "aurc_opt", "e_aurc", "sel_aurc", "sel_e_aurc")
    for k in T:
        if k == "B1-S":
            continue
        res["delta_B1S"][k] = {m: summ((acc[k][:, J[m]] - acc["B1-S"][:, J[m]]).tolist(), float(pt[k][J[m]] - pt["B1-S"][J[m]]))
                               for m in D_MEROK}
    for x, y in PAROK:
        res["delta_B1S"][f"{x}−{y}"] = {m: summ((acc[x][:, J[m]] - acc[y][:, J[m]]).tolist(), float(pt[x][J[m]] - pt[y][J[m]]))
                                        for m in ("aurc", "sel_aurc")}
    return res


def kapu(blk: dict) -> dict:
    """A 8.3 szabály próbája a teljes mintával: rétegszám és az átlagos AURC aránya (replikánként, a rétegek
    replikái függetlenek)."""
    r = [blk[t] for t in SZURO if t in blk]
    if len(r) < 3:
        return {}
    javul = sum(x["karok"]["B1-R|None"]["aurc"] < x["karok"]["B1-S"]["aurc"] for x in r)
    arany = np.mean([x["karok"]["B1-R|None"]["aurc"] for x in r]) / np.mean([x["karok"]["B1-S"]["aurc"] for x in r])
    ra = np.mean([x["_rep_aurc"]["B1-R|None"] for x in r], axis=0) / np.mean([x["_rep_aurc"]["B1-S"] for x in r], axis=0)
    delta = {t: blk[t]["karok"]["B1-R|None"]["aurc"] - blk[t]["karok"]["B1-S"]["aurc"] for t in SZURO}
    ossz = sum(delta.values())
    return {"javulo_retegek": int(javul), "arany": float(arany), "arany_ci95": [float(np.percentile(ra, 2.5)),
                                                                                float(np.percentile(ra, 97.5))],
            "teljesul": bool(javul >= 2 and arany <= 0.90), "delta": delta,
            "reszesedes": {t: (d / ossz if ossz else None) for t, d in delta.items()}}


def fmt(x, d=4) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def ci(c: dict, d=4) -> str:
    return f"{fmt(c['pont'], d)} [{fmt(c['ci95'][0], d)}; {fmt(c['ci95'][1], d)}]"


NEV = {"None": "teljes"}


def knev(k: str) -> str:
    a, _, n = k.partition("|")
    return f"{a} ({NEV.get(n, n)})" if n else a


def lap(res: dict) -> str:
    L = ["# 06 F1 — fejlesztési futás a 05 HO-rétegein (csak tervezéshez; a HO-rétegek nem érintetlenek)", "",
         f"Rétegenként: n item, ebből a B1 SELECT- / NONE-javaslata: " +
         "; ".join(f"{t.split(':')[1]} {v['n']} ({v['n_select']} / {v['n_none']})" for t, v in res["helyesseg"]["helyes"].items()) +
         ". A SELECT-AURC minden karnál a B1 SELECT-javaslatainak itemjein; a B1-N a B1 sorrendje, a NONE-javaslatok "
         "a SELECT-ek mögött.", "",
         f"Bootstrap: {res['reps']} ismétlés, a teszt alapesetei klaszteresen; replikánként egy seed és egy húzás. "
         "A pont a seedek és a húzások átlaga. A tanítóminta a `cel:ho-*` (alapesetek: " +
         ", ".join(f"{k} {v}" for k, v in res["alapeset"].items()) + ").", ""]
    for key in KULCSOK:
        blk = res["helyesseg"][key]
        L += [f"## {'Szigorú' if key == 'helyes' else 'Enyhe (leíró; a szigorúra tanított pontszámokkal)'} helyesség", ""]
        g = res["kapu"].get(key)
        if g:
            L += [f"**A 8.3 szabály próbája (teljes minta, három szűrőréteg):** javuló rétegek {g['javulo_retegek']}/3; "
                  f"átlag(AURC B1-R) / átlag(AURC B1-S) = {fmt(g['arany'], 3)} [{fmt(g['arany_ci95'][0], 3)}; "
                  f"{fmt(g['arany_ci95'][1], 3)}] → {'teljesülne' if g['teljesul'] else 'nem teljesülne'}. "
                  "Az abszolút ΔAURC rétegenként (részesedés): " +
                  "; ".join(f"{t.split(':')[1]} {fmt(g['delta'][t])} ({fmt(g['reszesedes'][t], 2)})" for t in SZURO) + ".", ""]
        L += ["**A K1 három szintje (teljes minta):**", "",
              "| réteg | 1. B1-R − B1-S | 2. B1-R − B1-N | 2. B1-R − B1-LR | 3. SELECT: B1-R − B1-S | NONE-on belüli AUROC B1-S / B1-R |",
              "|---|---|---|---|---|---|"]
        for t, v in blk.items():
            dd, K_ = v["delta_B1S"], v["karok"]
            L.append(f"| {t.split(':')[1]} | {ci(dd['B1-R|None']['aurc'])} | {ci(dd['B1-R|None−B1-N']['aurc'])} | "
                     f"{ci(dd['B1-R|None−B1-LR|None']['aurc'])} | {ci(dd['B1-R|None']['sel_aurc'])} | "
                     f"{fmt(K_['B1-S']['none_auroc'], 3)} / {fmt(K_['B1-R|None']['none_auroc'], 3)} |")
        L += ["", "| réteg | kar | AURC | Δ a B1-S-hez [CI] | ΔAURC* (javaslatok) | ΔE-AURC (sorrend) | SELECT-AURC | "
              "ΔSELECT-AURC [CI] | NONE-on belüli AUROC [CI] |", "|---|---|---|---|---|---|---|---|---|"]
        for t, v in blk.items():
            for k, m in v["karok"].items():
                d = v["delta_B1S"].get(k)
                nc = v["none_auroc_ci"].get(k)
                na = f"{fmt(m['none_auroc'], 3)} [{fmt(nc[0], 3)}; {fmt(nc[1], 3)}]" if nc else "—"
                L.append(f"| {t.split(':')[1]} | {knev(k)} | {fmt(m['aurc'])} | {ci(d['aurc']) if d else '—'} | "
                         f"{ci(d['aurc_opt']) if d else '—'} | {ci(d['e_aurc']) if d else '—'} | {fmt(m['sel_aurc'])} | "
                         f"{ci(d['sel_aurc']) if d else '—'} | {na} |")
        L += ["", "| réteg | összevetés | ΔAURC [CI] | ΔSELECT-AURC [CI] |", "|---|---|---|---|"]
        for t, v in blk.items():
            for k, d in v["delta_B1S"].items():
                if "−" in k:
                    x, y = k.split("−")
                    L.append(f"| {t.split(':')[1]} | {knev(x)} − {knev(y)} | {ci(d['aurc'])} | {ci(d['sel_aurc'])} |")
        L += [""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--be", required=True)
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {"reps": a.reps, "alapeset": {}, "helyesseg": {}, "kapu": {}}
    files = sorted(Path(a.be).glob("*/f1.json"))
    for key in KULCSOK:
        rng = np.random.default_rng(a.seed)
        blk = {}
        for p in files:
            f = json.loads(p.read_text())
            res["alapeset"][f["cel"]] = f["alapeset"]
            for t in f["B1"]:
                blk[t] = elemez(f, t, key, a.reps, rng)
                print(f"{key} {t} kész", flush=True)
        res["helyesseg"][key] = blk
        res["kapu"][key] = kapu(blk)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "f1_elemzes.md").write_text(lap(res), encoding="utf-8")
    for blk in res["helyesseg"].values():
        for v in blk.values():
            v.pop("_rep_aurc", None)
    (out / "f1_elemzes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
