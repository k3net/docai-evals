"""05-ös kör — utólagos, leíró diagnosztika a v1a-elemzés után. Nem része a v1a-ítéletnek (Napló, 2026-10-29).

Kérdés (Dani): a saját tartalmi fej rontja el az egyébként jó döntéseket, vagy a megbízhatósági fej nem ismeri fel a
hibákat? Az AURC (S+N; a DEFER a rangsor végén hibaként, mint az elemzes05-ben) két tag összege:
  AURC*   ugyanazokkal a javaslatokkal, tökéletes sorrend mellett: csak a javaslatok helyességétől függ (a tartalmi
          fej, illetve a címkekar választása)
  E-AURC  = AURC − AURC*: a sorrend vesztesége, a megbízhatósági pontszám minősége
A H − B1 így pontosan ΔAURC* + ΔE-AURC. A fejeknél a megbízhatósági fej hozzájárulása külön is: ugyanazok a javaslatok a
tartalmi fej saját valószínűsége (p_javaslat) szerint rendezve. A H-T-meta a H tartalmi fejét használja (azonos
javaslatok; ellenőrizve), így a nyeresége tisztán sorrend.
Továbbá: a H és a B1 helyességének itemszintű egyezése (melyik rontja el a másik jó döntését, milyen javaslattal),
családonként a legtöbb elveszített helyes döntés, és a JEV gyakorlati mérlege a munkapontnál (elfogadott itemek és
alapesetek, hibák típusonként, Clopper–Pearson).
Bootstrap: a réteg klaszteres újramintázása (család → alapeset); a seedek replikánként átlagolva; a mérőszámok
τ-függetlenek. A munkaponti mérleg a v1a-elemzés pont-τ-jánál (D_cal_policy).

  python3 kor05/eszkozok/diag05.py --reps 2000 --out kor05/eredmenyek/F3/v1a_diag
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta, rankdata

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "eszkozok")]
import elemzes05 as E  # noqa: E402
import kalib05 as K  # noqa: E402

RETEGEK = ("teszt:ho-termek", "teszt:ho-routing", "teszt:ho-uj", "teszt:ho-routing-hu")
FEJEK = ("C", "H", "A", "HX")
CIMKE = ("B1", "JEV-a", "JEV-b", "L1v", "G3")
KONTR = (("H", "B1"), ("C", "B1"), ("HX", "B1"), ("H-T-meta", "B1"), ("H-T-meta", "H"), ("JEV-a", "B1"),
         ("JEV-a", "L1v"), ("JEV-a", "G3"), ("JEV-a", "H"))
MERLEG = ("JEV-a", "JEV-b", "H", "G3")
KALIB = EXP / "kor05/eredmenyek/F3/kalib/kalib.json"


def aurc_star(k: int, n: int) -> float:
    """Az orákulum-AURC: a k helyes javaslat elöl, utánuk a hibás és a nem döntött itemek (E.aurc-kal azonos)."""
    if n == 0:
        return 0.0
    i = np.arange(k + 1, n + 1)
    return float(((i - k) / i).sum() / n)


def parts(t: E.Tab, s: np.ndarray) -> tuple[float, float, float]:
    a = E.aurc(t, s, t.acc_ok)
    a0 = aurc_star(int(t.cor[s].sum()), len(s))
    return a, a0, a - a0


def auroc(t: E.Tab, s: np.ndarray) -> float:
    a = s[t.acc_ok[s]]
    y, q = t.cor[a], t.q[a]
    n1, n0 = int(y.sum()), int((~y).sum())
    if not n1 or not n0:
        return math.nan
    r = rankdata(q)
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def p_tab(arm: str, layer: str, seed: int, ids: list[str], key: str) -> E.Tab:
    rows = K.head_rows(arm, layer, seed)
    if len(rows) != len({r["id"] for r in rows}):
        raise SystemExit(f"{arm}/{layer}/s{seed}: egy itemhez több döntési sor")
    return E.Tab([{"id": r["id"], "javaslat": r["javaslat"], "q": r["p_javaslat"], key: r[key]} for r in rows], ids, key)


def tipus(t: E.Tab, st: np.ndarray, m: np.ndarray) -> dict[str, int]:
    """A hibás javaslatok típusa egy itemhalmazon (m)."""
    d = ~t.acc_ok
    return {"SELECT, rossz opció (MATCH)": int((m & t.sel & (st == 0)).sum()),
            "SELECT nem-MATCH-en": int((m & t.sel & (st != 0)).sum()),
            "NONE MATCH-en": int((m & t.none & (st == 0)).sum()),
            "NONE MISSING/OOS-en": int((m & t.none & (st >= 2)).sum()),
            "DEFER": int((m & d).sum())}


def cp(k: int, n: int) -> list[float]:
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return [lo, hi]


def merleg(t: E.Tab, L: E.Slice, tau: float, M: dict) -> dict:
    st = L.state
    acc = t.acc_ok & (t.q >= tau)
    k, n = int((acc & t.cor).sum()), int(acc.sum())
    gid = np.array([M[i]["group_id"] for i in L.ids])
    fam = np.array(L.family)
    return {"tau": None if math.isinf(tau) else tau, "elfogadott": n, "SELECT": int((acc & t.sel).sum()),
            "NONE": int((acc & t.none).sum()), "hiba": n - k, "precizitas": k / n if n else math.nan,
            "cp95": cp(k, n) if n else None, "lefedettseg": n / len(L.ids),
            "elfogadott_alapeset": int(len(set(gid[acc]))), "alapeset_osszes": int(len(set(gid))),
            "csalad_elfogadott": int(len(set(fam[acc]))), "csalad_osszes": int(len(set(fam))),
            "MATCH_lefedve": float((acc & t.sel & t.cor & (st == 0)).sum() / max(1, (st == 0).sum())),
            "NO_MATCH_lefedve": float((acc & t.none & t.cor & (st == 1)).sum() / max(1, (st == 1).sum())),
            "allapotok": {s: int((st == c).sum()) for s, c in E.STATE_CODE.items()},
            "hibak": tipus(t, st, acc & ~t.cor)}


def summ(x: list[float]) -> dict:
    a = np.array(x, float)
    return {"ci95": [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))], "p": E.p_two(a)}


def reteg(layer: str, key: str, kal: dict, reps: int, rng: np.random.Generator, pol: E.Slice) -> dict:
    L = E.Slice(layer)
    M = K.meta()
    T = {arm: E.arm_tables(arm, kal, layer, L.ids, key) for arm in (*CIMKE, *FEJEK)}
    _, tm, _ = K.t_tables("H-T-meta", layer, kal)
    T["H-T-meta"] = [E.Tab(t, L.ids, key) for t in tm]
    P = {arm: [p_tab(arm, layer, s, L.ids, key) for s in K.SEEDS] for arm in FEJEK}
    azonos = all(np.array_equal(a.sel, b.sel) and np.array_equal(a.none, b.none) and np.array_equal(a.cor, b.cor)
                 for a, b in zip(T["H-T-meta"], T["H"]))
    s = L.full()

    def pont(tabs):
        v = np.array([parts(t, s) for t in tabs])
        return {"aurc": float(v[:, 0].mean()), "aurc_opt": float(v[:, 1].mean()), "e_aurc": float(v[:, 2].mean()),
                "helyes_arany": float(np.mean([t.cor[s].mean() for t in tabs])),
                "defer_arany": float(np.mean([(~t.acc_ok[s]).mean() for t in tabs])),
                "auroc": float(np.nanmean([auroc(t, s) for t in tabs]))}
    out = {"n": len(s), "tmeta_javaslat_azonos_H": azonos,
           "karok": {arm: pont(tabs) for arm, tabs in T.items()},
           "p_rendezes": {arm: pont(tabs) for arm, tabs in P.items()}}

    # bootstrap: a kontrasztok ΔAURC = ΔAURC* + ΔE-AURC, és a megbízhatósági fej (q) a p_javaslat-rendezéshez képest
    acc = {f"{x}-{y}|{m}": [] for x, y in KONTR for m in ("aurc", "aurc_opt", "e_aurc")}
    acc |= {f"{arm}|rel_q-p": [] for arm in FEJEK}
    for _ in range(reps):
        d = L.draw(rng)
        v = {arm: np.mean([parts(t, d) for t in tabs], axis=0) for arm, tabs in T.items()}
        for x, y in KONTR:
            for j, m in enumerate(("aurc", "aurc_opt", "e_aurc")):
                acc[f"{x}-{y}|{m}"].append(v[x][j] - v[y][j])
        for arm in FEJEK:
            acc[f"{arm}|rel_q-p"].append(v[arm][0] - np.mean([E.aurc(t, d, t.acc_ok) for t in P[arm]]))
    k = out["karok"]
    out["kontrasztok"] = {f"{x}-{y}": {m: {"pont": k[x][m] - k[y][m]} | summ(acc[f"{x}-{y}|{m}"])
                                       for m in ("aurc", "aurc_opt", "e_aurc")} for x, y in KONTR}
    out["megbizhatosagi_fej"] = {arm: {"pont": k[arm]["aurc"] - out["p_rendezes"][arm]["aurc"]}
                                 | summ(acc[f"{arm}|rel_q-p"]) for arm in FEJEK}

    # a H és a B1 itemszintű egyezése (a H seedjeinek átlaga)
    b, st = T["B1"][0], L.state
    eg = []
    for h in T["H"]:
        eg.append({"mindketto": int((b.cor & h.cor).sum()), "csak_B1": int((b.cor & ~h.cor).sum()),
                   "csak_H": int((~b.cor & h.cor).sum()), "egyik_sem": int((~b.cor & ~h.cor).sum()),
                   "csak_B1_H_javaslata": tipus(h, st, b.cor & ~h.cor),
                   "csak_H_B1_javaslata": tipus(b, st, ~b.cor & h.cor),
                   "csak_B1_MATCH": int((b.cor & ~h.cor & (st == 0)).sum()),
                   "csak_H_MATCH": int((~b.cor & h.cor & (st == 0)).sum())})
    out["egyezes_H_B1"] = {kk: (float(np.mean([e[kk] for e in eg])) if not isinstance(eg[0][kk], dict) else
                                {t: float(np.mean([e[kk][t] for e in eg])) for t in eg[0][kk]}) for kk in eg[0]}

    # családonként: hol veszít a H a legtöbb helyes döntést a B1-hez képest
    fam = np.array(L.family)
    rows = []
    for f in sorted(set(fam)):
        m = fam == f
        hb = float(np.mean([h.cor[m].mean() for h in T["H"]]))
        rows.append({"csalad": f, "n": int(m.sum()), "H_helyes": hb, "B1_helyes": float(b.cor[m].mean()),
                     "elveszett": float((b.cor[m].mean() - hb) * m.sum())})
    out["csaladok_legtobb_veszteseg"] = sorted(rows, key=lambda r: -r["elveszett"])[:8]

    # munkaponti mérleg (a v1a pont-τ-ja, D_cal_policy)
    mer = {}
    for arm in MERLEG:
        tp = E.arm_tables(arm, kal, "D_cal_policy", pol.ids, key)
        mer[arm] = [merleg(t, L, E.tau_of(p, pol.full()), M) | E.lef_p95(t, s, None) for t, p in zip(T[arm], tp)]
    out["munkapont"] = mer
    return out


def fmt(x, d=4) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def ci(c: dict, d=4) -> str:
    return f"{fmt(c['pont'], d)} [{fmt(c['ci95'][0], d)}; {fmt(c['ci95'][1], d)}]"


def lap(res: dict) -> str:
    L = ["# 05a — utólagos diagnosztika (leíró; nem része a v1a-ítéletnek)", "",
         f"Bootstrap: {res['reps']} ismétlés, klaszteres (család → alapeset), a seedek replikánként átlagolva. "
         "AURC = AURC* (a javaslatok helyessége, tökéletes sorrenddel) + E-AURC (a sorrend vesztesége).", ""]
    for key, blk in res["helyesseg"].items():
        L += [f"## {'Szigorú' if key == 'helyes' else 'Enyhe'} helyesség", ""]
        L += ["### Felbontás: ΔAURC = ΔAURC* + ΔE-AURC", "",
              "| kontraszt | réteg | ΔAURC | ΔAURC* (javaslatok) | ΔE-AURC (sorrend) |", "|---|---|---|---|---|"]
        for x, y in KONTR:
            for r, v in blk.items():
                k = v["kontrasztok"][f"{x}-{y}"]
                L.append(f"| {x} − {y} | {r.split(':')[1]} | {ci(k['aurc'])} | {ci(k['aurc_opt'])} | {ci(k['e_aurc'])} |")
        L += ["", "### Karok (pont; seedátlag)", "",
              "| réteg | kar | helyes javaslat | DEFER | AURC | AURC* | E-AURC | AUROC (q) |", "|---|---|---|---|---|---|---|---|"]
        for r, v in blk.items():
            for arm, m in v["karok"].items():
                L.append(f"| {r.split(':')[1]} | {arm} | {fmt(m['helyes_arany'], 3)} | {fmt(m['defer_arany'], 3)} | "
                         f"{fmt(m['aurc'])} | {fmt(m['aurc_opt'])} | {fmt(m['e_aurc'])} | {fmt(m['auroc'], 3)} |")
        L += ["", "### A megbízhatósági fej: q-rendezés − p_javaslat-rendezés (azonos javaslatok; negatív = a fej segít)",
              "", "| réteg | " + " | ".join(FEJEK) + " | E-AURC p-vel (H) | AUROC p-vel (H) |", "|---|" + "---|" * (len(FEJEK) + 2)]
        for r, v in blk.items():
            L.append(f"| {r.split(':')[1]} | " + " | ".join(ci(v["megbizhatosagi_fej"][a]) for a in FEJEK) +
                     f" | {fmt(v['p_rendezes']['H']['e_aurc'])} | {fmt(v['p_rendezes']['H']['auroc'], 3)} |")
        L += ["", "### H és B1 itemszinten (a H seedjeinek átlaga)", "",
              "| réteg | n | mindkettő helyes | csak B1 | ebből MATCH | csak H | ebből MATCH | egyik sem |",
              "|---|---|---|---|---|---|---|---|"]
        for r, v in blk.items():
            e = v["egyezes_H_B1"]
            L.append(f"| {r.split(':')[1]} | {v['n']} | {e['mindketto']:.0f} | {e['csak_B1']:.0f} | {e['csak_B1_MATCH']:.0f} | "
                     f"{e['csak_H']:.0f} | {e['csak_H_MATCH']:.0f} | {e['egyik_sem']:.0f} |")
        L += ["", "Ahol csak a B1 helyes, a H javaslata / ahol csak a H helyes, a B1 javaslata:", ""]
        for r, v in blk.items():
            e = v["egyezes_H_B1"]
            L.append(f"- {r.split(':')[1]}: H → " + ", ".join(f"{t} {c:.0f}" for t, c in e["csak_B1_H_javaslata"].items() if c)
                     + "; B1 → " + ", ".join(f"{t} {c:.0f}" for t, c in e["csak_H_B1_javaslata"].items() if c))
        L += ["", "### Családok, ahol a H a legtöbb helyes döntést veszíti a B1-hez képest", "",
              "| réteg | család | n | B1 helyes | H helyes | elveszett |", "|---|---|---|---|---|---|"]
        for r, v in blk.items():
            for c in v["csaladok_legtobb_veszteseg"][:5]:
                L.append(f"| {r.split(':')[1]} | {c['csalad']} | {c['n']} | {fmt(c['B1_helyes'], 3)} | {fmt(c['H_helyes'], 3)} | "
                         f"{c['elveszett']:.0f} |")
        L += ["", "### Munkaponti mérleg (a v1a pont-τ-ja; lef@p95: a τ a rétegen magán, felső korlát)", "",
              "| réteg | kar | elfogadott (SELECT / NONE) | hiba | precizitás [CP 95%] | lefedettség | elfogadott "
              "alapeset / összes | család | MATCH lefedve | lef@p95 S+N |", "|---|---|---|---|---|---|---|---|---|---|"]
        for r, v in blk.items():
            for arm, ms in v["munkapont"].items():
                for j, m in enumerate(ms):
                    nm = arm + (f" s{j + 1}" if len(ms) > 1 else "")
                    if not m["elfogadott"]:
                        L.append(f"| {r.split(':')[1]} | {nm} | 0 (nincs munkapont) | – | – | – | – | – | – | "
                                 f"{fmt(m['lef_p95_sn'], 3)} |")
                        continue
                    L.append(f"| {r.split(':')[1]} | {nm} | {m['elfogadott']} ({m['SELECT']} / {m['NONE']}) | {m['hiba']} | "
                             f"{fmt(m['precizitas'], 3)} [{fmt(m['cp95'][0], 3)}; {fmt(m['cp95'][1], 3)}] | "
                             f"{fmt(m['lefedettseg'], 3)} | {m['elfogadott_alapeset']} / {m['alapeset_osszes']} | "
                             f"{m['csalad_elfogadott']} / {m['csalad_osszes']} | {fmt(m['MATCH_lefedve'], 3)} | "
                             f"{fmt(m['lef_p95_sn'], 3)} |")
        L += [""]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    kal = json.loads(KALIB.read_text())
    pol = E.Slice("D_cal_policy", one_per_group=True)
    res = {"reps": a.reps, "helyesseg": {}}
    for key in ("helyes", "helyes_enyhe"):
        rng = np.random.default_rng(a.seed)
        res["helyesseg"][key] = {}
        for layer in RETEGEK:
            res["helyesseg"][key][layer] = reteg(layer, key, kal, a.reps, rng, pol)
            print(f"{key} {layer} kész", flush=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "diag05.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "diag05.md").write_text(lap(res), encoding="utf-8")


if __name__ == "__main__":
    main()
