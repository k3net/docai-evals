"""07-es kör — az F5 elemzője (07-runbook 4., 5., D5, D9, D10, D13, D20) a `b1rel07 pontoz` kimenetein.

Bemenet: családonként a CAL és a TESZT pontozása (`<be>/<szelet>.json`, mindkét keret döntéseivel és pontszámaival).
A próbához a 06 CAL / TESZT (`k06:<család>:<szelet>`, ismert adat, nem állítás), az F5-höz a 07 friss szeletei.
Karok: négyállapotú keret B1-4S, B1-4R, B1-4LR, B1-4R0; 06-os keret B1-S, B1-N (a NONE hátra), B1-R, B1-LR, B1-R0.
A fő négy kar (D9): B1-S, B1-R, B1-4S, B1-4R.

K1 (elsődleges): AURC a TESZT-en a szigorú helyességgel (négyállapotú keret: négyosztályos), B1-4R − B1-4S; a 06 8.3
   szabálya a D4-gyel a három család egyenlő súlyú átlagán (D5). Mellette a 06-os pár és a keresztpárok leíróan (D13),
   az E-AURC leíróan, a D20 bontása (SELECT- és nem-SELECT javaslatok külön).
K2 (gyakorlati, D9–D10): a τ a CAL-on, csak a lezárható javaslatokon (SELECT és X / NONE): a legnagyobb elfogadott
   halmaz, ahol a lezárás precizitásának CP-alsó határa ≥ 0,95 és legalább 200 lezárt ügy van (a 05 szabálya).
   A TESZT-en: hasznos lefedettség = helyesen lezárt / összes; lezárási hibaarány = hibásan lezárt / összes lezárt;
   külön sor: a helyes adatbekérés (Y a MISSING_DATA-n) és a helyes továbbítás (Z az OUT_OF_SCOPE-on) aránya, és a nem
   lezárt ügyek bontása (adatbekérés, továbbítás, τ alatt). Felső korlát: a MATCH + NO_MATCH arány (80%).
   Következtetés a három család egyenlő súlyú átlagán (D10): „behozza” = (B1-4S − B1-R) alsó határa > −0,03 és mindkét
   kar teljesíti a hibafeltételt; „javít mellette” = (B1-4R − B1-4S) alsó határa > 0 és a B1-4R teljesíti. Hibafeltétel:
   a lezárási hibaarány pontbecslése ≤ 0,05 a TESZT-en; ha a felső határa 0,05 fölött van: „bizonytalan”.
   Munkapont nélkül (nincs τ a CP-feltétellel) a kar semmit nem zár le: hasznos lefedettség 0, a hibaarány nincs
   értelmezve; a munkapont nélküli futások és replikák aránya külön sor.
Statisztika (5.): sabloncsoportos klaszteres bootstrap (D23) a CAL-on és a TESZT-en külön, a τ replikánként újra; a
   futások (seedek) mérőinek átlaga replikánként (D24); kétoldali bootstrap-p; Holm a családokra leíróan; a munkapont
   nélküli replikák aránya külön.

  python3 kor07/eszkozok/elemzes07.py --be cache/k07/f3r_proba --forras k06 --reps 2000 --out kor07/eredmenyek/F4/proba
  python3 kor07/eszkozok/elemzes07.py --be cache/k07/f5 --forras k07 --reps 10000 --out kor07/eredmenyek/F5
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
ITEMS = {"k06": EXP / "kor06/adat/f2/items", "k07": EXP / "kor07/adat/f2/items"}
ALLAPOT = {"MATCH": 0, "NO_MATCH": 1, "MISSING_DATA": 2, "OUT_OF_SCOPE": 3}
FAJTAK = ("SELECT", "NONE", "MISSING", "OOS")
KAROK = {"keret4": ("B1-4S", "B1-4R", "B1-4LR", "B1-4R0"), "keret2": ("B1-S", "B1-N", "B1-R", "B1-LR", "B1-R0")}
KERET = {k: kr for kr, ks in KAROK.items() for k in ks}
FO = ("B1-S", "B1-R", "B1-4S", "B1-4R")
SEEDS = (17, 42, 73)
TARGET, MIN_ACC = 0.95, 200
HIBA_FELTETEL, BEHOZZA = 0.05, -0.03
Z = 1.959964
K1_PAROK = {"K1: B1-4R − B1-4S": ("B1-4R", "B1-4S"), "B1-4LR − B1-4S": ("B1-4LR", "B1-4S"), "B1-4R − B1-4LR": ("B1-4R", "B1-4LR"),
            "06: B1-R − B1-S": ("B1-R", "B1-S"), "kereszt (leíró): B1-4S − B1-R": ("B1-4S", "B1-R"),
            "kereszt (leíró): B1-4R − B1-R": ("B1-4R", "B1-R")}
K2_MEROK = ("hasznos_lef", "lezarasi_hiba", "lezart", "helyes_adatbekeres", "helyes_tovabbitas", "nem_lezart_adatbekeres",
            "nem_lezart_tovabbitas", "nem_lezart_tau_alatt")


# --- betöltés ----------------------------------------------------------------------------------------------------------

def kmin_tabla(n_max: int) -> np.ndarray:
    """n elfogadottnál a legkisebb k helyes, amelynél a precizitás egyoldali 95%-os CP-alsó határa ≥ TARGET."""
    out = np.full(n_max + 1, 10 ** 9)
    for n in range(1, n_max + 1):
        lo, hi = 0, n
        while lo < hi:
            mid = (lo + hi) // 2
            if mid > 0 and beta.ppf(0.05, mid, n - mid + 1) >= TARGET:
                hi = mid
            else:
                lo = mid + 1
        out[n] = lo if lo > 0 and beta.ppf(0.05, lo, n - lo + 1) >= TARGET else n + 1
    return out


class Szelet:
    """Egy család egy szelete (CAL vagy TESZT), mindkét kerettel, itemsorrendben a négyállapotú keret id-i szerint."""

    def __init__(self, be: Path, forras: str, fam: str, sz: str):
        nev = f"{'k06_' if forras == 'k06' else ''}{fam}_{sz}"
        d = json.loads((be / f"{nev}.json").read_text())
        items = {it["id"]: it for it in map(json.loads, (ITEMS[forras] / f"{fam}.jsonl").read_text().splitlines()) if it}
        self.ids = d["keret4"]["ids"]
        if set(self.ids) != set(d["keret2"]["ids"]):
            raise SystemExit(f"{nev}: a két keret itemjei eltérnek")
        al = np.array([{i: n for n, i in enumerate(d["keret2"]["ids"])}[i] for i in self.ids])
        self.n = len(self.ids)
        self.sablon = [items[i]["template_group_id"] for i in self.ids]
        self.state = np.array([ALLAPOT[items[i]["content_state"]] for i in self.ids])
        self.kind, self.cor, self.cor_enyhe, self.pont = {}, {}, {}, {}
        for keret in ("keret4", "keret2"):
            D = d[keret]["dontes"]
            order = d[keret]["ids"]
            kind = np.array([D[i]["kind"] for i in order])
            cor = np.array([bool(D[i]["helyes"]) for i in order])
            eny = np.array([bool(D[i]["helyes_enyhe"]) for i in order])
            if keret == "keret2":
                kind, cor, eny = kind[al], cor[al], eny[al]
            self.kind[keret], self.cor[keret], self.cor_enyhe[keret] = kind, cor, eny
            P = d[keret]["pontszam"]
            for kar in KAROK[keret]:
                if kar == "B1-N":
                    q = np.array(P["B1-S"])
                    cols = [np.where(np.array([D[i]["kind"] for i in order]) == "NONE", q - 10, q)]
                else:
                    cols = [np.array(P[f"{kar}|{s}"]) for s in SEEDS] if f"{kar}|{SEEDS[0]}" in P else [np.array(P[kar])]
                self.pont[kar] = [c[al] if keret == "keret2" else c for c in cols]
        cl = {}
        for n, s in enumerate(self.sablon):
            cl.setdefault(s, []).append(n)
        self.clusters = [np.array(v) for v in cl.values()]

    def huzas(self, rng: np.random.Generator) -> np.ndarray:
        C = len(self.clusters)
        return np.concatenate([self.clusters[c] for c in rng.integers(0, C, C)])

    def teljes(self) -> np.ndarray:
        return np.arange(self.n)


# --- mérők -------------------------------------------------------------------------------------------------------------

def aurc(q: np.ndarray, cor: np.ndarray) -> float:
    o = np.argsort(-q, kind="stable")
    err = np.cumsum(~cor[o])
    return float((err / np.arange(1, len(q) + 1)).mean())


def aurc_opt(cor: np.ndarray) -> float:
    n, nc = len(cor), int(cor.sum())
    k = np.arange(1, n + 1)
    return float((np.maximum(0, k - nc) / k).mean())


def tau_of(q: np.ndarray, cor: np.ndarray, lezarhato: np.ndarray, idx: np.ndarray, kmin: np.ndarray) -> float:
    s = idx[lezarhato[idx]]
    if len(s) < MIN_ACC:
        return math.inf
    o = s[np.argsort(-q[s], kind="stable")]
    c = q[o]
    k = np.cumsum(cor[o])
    n = np.arange(1, len(o) + 1)
    boundary = np.append(c[1:] != c[:-1], True)
    ok = boundary & (n >= MIN_ACC) & (k >= kmin[n])
    return float(c[np.nonzero(ok)[0][-1]]) if ok.any() else math.inf


def k2_merok(q: np.ndarray, cor: np.ndarray, kind: np.ndarray, state: np.ndarray, idx: np.ndarray, tau: float) -> dict:
    n = len(idx)
    qs, cs, ks, ss = q[idx], cor[idx], kind[idx], state[idx]
    lez = (ks == "SELECT") | (ks == "NONE")
    acc = lez & (qs >= tau)

    def rate(a, b):
        return float(a.sum() / b.sum()) if b.sum() else math.nan
    return {"hasznos_lef": float((acc & cs).sum() / n), "lezarasi_hiba": rate(acc & ~cs, acc), "lezart": float(acc.sum() / n),
            "helyes_adatbekeres": rate((ks == "MISSING") & (ss == 2), ss == 2),
            "helyes_tovabbitas": rate((ks == "OOS") & (ss == 3), ss == 3),
            "nem_lezart_adatbekeres": float((ks == "MISSING").sum() / n), "nem_lezart_tovabbitas": float((ks == "OOS").sum() / n),
            "nem_lezart_tau_alatt": float((lez & ~acc).sum() / n)}


def futas_atlag(ms: list[dict]) -> dict:
    return {k: float(np.nanmean([m[k] for m in ms])) if ms else math.nan for k in K2_MEROK}


def csalad(be: Path, forras: str, fam: str, reps: int, rng: np.random.Generator, kmin: np.ndarray) -> dict:
    C, T = Szelet(be, forras, fam, "CAL"), Szelet(be, forras, fam, "TESZT")
    karok = [k for ks in KAROK.values() for k in ks]
    lez = {kr: np.isin(T.kind[kr], ("SELECT", "NONE")) for kr in KAROK}
    lezc = {kr: np.isin(C.kind[kr], ("SELECT", "NONE")) for kr in KAROK}

    def k1(kar: str, idx: np.ndarray, enyhe: bool = False) -> float:
        kr = KERET[kar]
        cor = (T.cor_enyhe if enyhe else T.cor)[kr]
        return float(np.mean([aurc(c[idx], cor[idx]) for c in T.pont[kar]]))

    def k1_reszek(kar: str, idx: np.ndarray) -> dict:  # D20: SELECT és nem-SELECT javaslatok külön
        kr = KERET[kar]
        sel = T.kind[kr][idx] == "SELECT"
        return {"select": float(np.mean([aurc(c[idx][sel], T.cor[kr][idx][sel]) for c in T.pont[kar]])) if sel.any() else math.nan,
                "nem_select": float(np.mean([aurc(c[idx][~sel], T.cor[kr][idx][~sel]) for c in T.pont[kar]])) if (~sel).any() else math.nan}

    def k2(kar: str, ic: np.ndarray, it: np.ndarray) -> tuple[dict, int, int]:
        """Munkapont nélkül (τ = ∞) a kar semmit nem zár le: a hasznos lefedettség 0, a lezárási hibaarány nincs
        értelmezve (NaN); a munkapont nélküli futások aránya külön sor. Így a karok összevetése minden replikán
        értelmezett (a K2 gyakorlati végpont: hány ügyet zár le helyesen a rendszer)."""
        kr = KERET[kar]
        ms, nincs = [], 0
        for qc, qt in zip(C.pont[kar], T.pont[kar]):
            tau = tau_of(qc, C.cor[kr], lezc[kr], ic, kmin)
            nincs += math.isinf(tau)
            ms.append(k2_merok(qt, T.cor[kr], T.kind[kr], T.state, it, tau))
        return futas_atlag(ms), nincs, len(T.pont[kar])

    full_c, full_t = C.teljes(), T.teljes()
    pont = {"k1": {k: k1(k, full_t) for k in karok}, "k1_enyhe": {k: k1(k, full_t, True) for k in karok},
            "eaurc": {k: k1(k, full_t) - aurc_opt(T.cor[KERET[k]]) for k in karok},
            "k1_d20": {k: k1_reszek(k, full_t) for k in karok}, "k2": {}, "k2_nincs_munkapont": {}, "tau": {}}
    for k in karok:
        m, nincs, ossz = k2(k, full_c, full_t)
        pont["k2"][k], pont["k2_nincs_munkapont"][k] = m, nincs / ossz
        pont["tau"][k] = [tau_of(qc, C.cor[KERET[k]], lezc[KERET[k]], full_c, kmin) for qc in C.pont[k]]
    rep = {"k1": {k: np.empty(reps) for k in karok}, "k2": {k: {m: np.empty(reps) for m in K2_MEROK} for k in karok},
           "nincs": {k: 0 for k in karok}, "ossz": {k: 0 for k in karok}}
    for r in range(reps):
        ic, it = C.huzas(rng), T.huzas(rng)
        for k in karok:
            rep["k1"][k][r] = k1(k, it)
            m, nincs, ossz = k2(k, ic, it)
            rep["nincs"][k] += nincs
            rep["ossz"][k] += ossz
            for mm in K2_MEROK:
                rep["k2"][k][mm][r] = m[mm]
    tev = {kr: {s: {f: int(((T.kind[kr] == f) & (T.state == ALLAPOT[s])).sum()) for f in FAJTAK if (kr == "keret4" or f in ("SELECT", "NONE"))}
                for s in ALLAPOT} for kr in KAROK}
    pont["k2_nincs_munkapont_replika"] = {k: rep["nincs"][k] / max(1, rep["ossz"][k]) for k in karok}
    return {"n_cal": C.n, "n_teszt": T.n, "n_sablon_cal": len(C.clusters), "n_sablon_teszt": len(T.clusters),
            "felso_korlat": float(np.isin(T.state, (0, 1)).mean()), "lezarhato_arany": {kr: float(lez[kr].mean()) for kr in KAROK},
            "helyes_dontes": {kr: float(T.cor[kr].mean()) for kr in KAROK}, "tevesztes": tev, "pont": pont, "_rep": rep}


# --- összevetések -----------------------------------------------------------------------------------------------------

def ci(x: np.ndarray) -> list[float]:
    x = x[~np.isnan(x)]
    return [float(np.quantile(x, 0.025)), float(np.quantile(x, 0.975))] if len(x) else [math.nan, math.nan]


def p_ketoldali(d: np.ndarray) -> float:
    d = d[~np.isnan(d)]
    return float(min(1.0, 2 * min(np.mean(d >= 0), np.mean(d <= 0)))) if len(d) else math.nan


def holm(ps: dict[str, float]) -> dict[str, float]:
    k = sorted(ps, key=lambda name: ps[name])
    out, prev = {}, 0.0
    for r, name in enumerate(k):
        prev = max(prev, min(1.0, (len(k) - r) * ps[name]))
        out[name] = prev
    return out


def k1_par(R: dict, a: str, b: str) -> dict:
    cs = {}
    for fam, x in R.items():
        d = x["_rep"]["k1"][a] - x["_rep"]["k1"][b]
        cs[fam] = {"aurc_A": x["pont"]["k1"][a], "aurc_B": x["pont"]["k1"][b], "delta": x["pont"]["k1"][a] - x["pont"]["k1"][b],
                   "ci95": ci(d), "p": p_ketoldali(d)}
    ratio = np.mean([x["_rep"]["k1"][a] for x in R.values()], axis=0) / np.mean([x["_rep"]["k1"][b] for x in R.values()], axis=0)
    pa, pb = np.mean([x["pont"]["k1"][a] for x in R.values()]), np.mean([x["pont"]["k1"][b] for x in R.values()])
    javul = sum(c["delta"] < 0 for c in cs.values())
    r_ci = ci(ratio)
    return {"csaladok": cs, "holm_p": holm({f: c["p"] for f, c in cs.items()}),
            "atlag": {"aurc_A": float(pa), "aurc_B": float(pb), "arany": float(pa / pb) if pb else math.nan, "arany_ci95": r_ci,
                      "szabaly_1_javul": int(javul), "szabaly_2_pont": bool(pa / pb <= 0.90) if pb else False, "d4": bool(r_ci[1] < 1.0),
                      "teljesul": bool(javul >= 2 and pb and pa / pb <= 0.90 and r_ci[1] < 1.0)}}


def k2_atlag(R: dict, kar: str, mero: str) -> tuple[float, np.ndarray]:
    return (float(np.mean([x["pont"]["k2"][kar][mero] for x in R.values()])),
            np.mean([x["_rep"]["k2"][kar][mero] for x in R.values()], axis=0))


def k2_osszegzes(R: dict) -> dict:
    karok = [k for ks in KAROK.values() for k in ks]
    out = {"karok": {}, "kovetkeztetes": {}}
    for k in karok:
        hl, hl_r = k2_atlag(R, k, "hasznos_lef")
        hb, hb_r = k2_atlag(R, k, "lezarasi_hiba")
        hb_ci = ci(hb_r)
        out["karok"][k] = {"hasznos_lef": hl, "hasznos_lef_ci95": ci(hl_r), "lezarasi_hiba": hb, "lezarasi_hiba_ci95": hb_ci,
                           "hibafeltetel_pont": bool(hb <= HIBA_FELTETEL), "hibafeltetel_bizonytalan": bool(hb <= HIBA_FELTETEL < hb_ci[1]),
                           "nincs_munkapont_replika": float(np.mean([x["_rep"]["nincs"][k] / max(1, x["_rep"]["ossz"][k]) for x in R.values()])),
                           "csaladok": {fam: {m: x["pont"]["k2"][k][m] for m in K2_MEROK} | {
                               "hasznos_lef_ci95": ci(x["_rep"]["k2"][k]["hasznos_lef"]), "lezarasi_hiba_ci95": ci(x["_rep"]["k2"][k]["lezarasi_hiba"]),
                               "nincs_munkapont": x["pont"]["k2_nincs_munkapont"][k],
                               "nincs_munkapont_replika": x["pont"]["k2_nincs_munkapont_replika"][k], "tau": x["pont"]["tau"][k]}
                               for fam, x in R.items()}}

    def kul(a: str, b: str) -> dict:
        da, dr = k2_atlag(R, a, "hasznos_lef")
        db, dr2 = k2_atlag(R, b, "hasznos_lef")
        d = dr - dr2
        return {"delta": da - db, "ci95": ci(d), "p": p_ketoldali(d),
                "csaladok": {fam: {"delta": x["pont"]["k2"][a]["hasznos_lef"] - x["pont"]["k2"][b]["hasznos_lef"],
                                   "ci95": ci(x["_rep"]["k2"][a]["hasznos_lef"] - x["_rep"]["k2"][b]["hasznos_lef"])} for fam, x in R.items()}}
    K = out["karok"]
    b = kul("B1-4S", "B1-R")
    felt = K["B1-4S"]["hibafeltetel_pont"] and K["B1-R"]["hibafeltetel_pont"]
    biz = K["B1-4S"]["hibafeltetel_bizonytalan"] or K["B1-R"]["hibafeltetel_bizonytalan"]
    b["itelet"] = ("behozza" if b["ci95"][0] > BEHOZZA and felt and not biz else
                   "bizonytalan" if b["ci95"][0] > BEHOZZA and felt else "nem hozza be")
    j = kul("B1-4R", "B1-4S")
    j["itelet"] = ("javít mellette" if j["ci95"][0] > 0 and K["B1-4R"]["hibafeltetel_pont"] and not K["B1-4R"]["hibafeltetel_bizonytalan"] else
                   "bizonytalan" if j["ci95"][0] > 0 and K["B1-4R"]["hibafeltetel_pont"] else "nem javít")
    out["kovetkeztetes"] = {"behozza (B1-4S − B1-R)": b, "javít mellette (B1-4R − B1-4S)": j,
                            "B1-4R − B1-R (leíró)": kul("B1-4R", "B1-R"), "B1-R − B1-S (06)": kul("B1-R", "B1-S")}
    return out


# --- lap ----------------------------------------------------------------------------------------------------------------

def f(x, d: int = 4, pct: bool = False) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "igen" if x else "nem"
    return (f"{100 * x:.1f}%" if pct else f"{x:.{d}f}").replace(".", ",")


def c95(v: list[float], d: int = 4, pct: bool = False) -> str:
    return f"[{f(v[0], d, pct)}; {f(v[1], d, pct)}]"


def lap(res: dict, cimke: str) -> str:
    R = res["csaladok"]
    karok = [k for ks in KAROK.values() for k in ks]
    L = [f"# 07 — K1 és K2 elemzés: {cimke}", "",
         f"Sabloncsoportos klaszteres bootstrap ({res['reps']} replika, seed {res['seed']}), a τ replikánként újra a CAL-on, a "
         "futások (seedek) átlaga replikánként (D24). Szigorú helyesség (négyállapotú keret: négyosztályos). "
         f"K2: τ a lezárható javaslatokon (SELECT és X / NONE), CP-alsó ≥ {TARGET}, ≥ {MIN_ACC} lezárt ügy; hibafeltétel: "
         f"lezárási hibaarány ≤ {HIBA_FELTETEL} a TESZT-en; „behozza”: a hasznos lefedettség különbségének alsó határa > {BEHOZZA}.", "",
         "## K1 — AURC a TESZT-en", "", "| család | " + " | ".join(karok) + " |", "|---|" + "---|" * len(karok)]
    for fam, x in R.items():
        L.append(f"| {fam} | " + " | ".join(f(x["pont"]["k1"][k]) for k in karok) + " |")
    L.append("| **átlag** | " + " | ".join(f(float(np.mean([x["pont"]["k1"][k] for x in R.values()]))) for k in karok) + " |")
    for nev, p in res["k1"].items():
        at = p["atlag"]
        L += ["", f"**{nev}:** " + "; ".join(f"{fam.split('.')[1]} Δ {f(c['delta'])} {c95(c['ci95'])} p={f(c['p'], 3)}" for fam, c in p["csaladok"].items())
              + f". Átlag arány **{f(at['arany'], 3)}** {c95(at['arany_ci95'], 3)}; 8.3: javul {at['szabaly_1_javul']}/3, "
              f"arány ≤ 0,90: {f(at['szabaly_2_pont'])}, D4: {f(at['d4'])} → **{'teljesül' if at['teljesul'] else 'nem teljesül'}**. "
              f"Holm-p: " + ", ".join(f"{k.split('.')[1]} {f(v, 3)}" for k, v in p["holm_p"].items())]
    L += ["", "### E-AURC (leíró, D13; promptok között nem összevethető)", "", "| család | " + " | ".join(karok) + " |", "|---|" + "---|" * len(karok)]
    for fam, x in R.items():
        L.append(f"| {fam} | " + " | ".join(f(x["pont"]["eaurc"][k]) for k in karok) + " |")
    L += ["", "### D20 — AURC a SELECT- és a nem-SELECT javaslatokon (B1-4R vs B1-4S; B1-R vs B1-S)", "",
          "| család | B1-4S sel / nem-sel | B1-4R sel / nem-sel | B1-S sel / nem-sel | B1-R sel / nem-sel |", "|---|---|---|---|---|"]
    for fam, x in R.items():
        d = x["pont"]["k1_d20"]
        L.append(f"| {fam} | " + " | ".join(f"{f(d[k]['select'])} / {f(d[k]['nem_select'])}" for k in ("B1-4S", "B1-4R", "B1-S", "B1-R")) + " |")
    L += ["", "### A döntések helyessége és a tévesztési mátrix (prompttulajdonság)", ""]
    for fam, x in R.items():
        L += [f"**{fam}:** helyes döntés négyállapotú {f(x['helyes_dontes']['keret4'], 3)}, 06-os {f(x['helyes_dontes']['keret2'], 3)}; "
              f"lezárható javaslat {f(x['lezarhato_arany']['keret4'], 3)} / {f(x['lezarhato_arany']['keret2'], 3)}; felső korlát {f(x['felso_korlat'], 3)}.", "",
              "| gold | 4: SELECT | X | Y | Z | · | 06: SELECT | NONE |", "|---|---|---|---|---|---|---|---|"]
        for s in ALLAPOT:
            t4, t2 = x["tevesztes"]["keret4"][s], x["tevesztes"]["keret2"][s]
            L.append(f"| {s} | {t4['SELECT']} | {t4['NONE']} | {t4['MISSING']} | {t4['OOS']} | · | {t2['SELECT']} | {t2['NONE']} |")
        L.append("")
    K = res["k2"]["karok"]
    L += ["## K2 — hasznos lefedettség és lezárási hibaarány a TESZT-en (τ a CAL-on)", "",
          "| kar | család | lezárt | hasznos lefedettség [95%] | lezárási hibaarány [95%] | helyes adatbekérés | helyes továbbítás | nem lezárt: adatbekérés / továbbítás / τ alatt | nincs munkapont (pont / replika) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for k in karok:
        for fam, c in K[k]["csaladok"].items():
            L.append(f"| {k} | {fam.split('.')[1]} | {f(c['lezart'], pct=True)} | {f(c['hasznos_lef'], pct=True)} {c95(c['hasznos_lef_ci95'], pct=True)} | "
                     f"{f(c['lezarasi_hiba'], pct=True)} {c95(c['lezarasi_hiba_ci95'], pct=True)} | {f(c['helyes_adatbekeres'], pct=True)} | "
                     f"{f(c['helyes_tovabbitas'], pct=True)} | {f(c['nem_lezart_adatbekeres'], pct=True)} / {f(c['nem_lezart_tovabbitas'], pct=True)} / "
                     f"{f(c['nem_lezart_tau_alatt'], pct=True)} | {f(c['nincs_munkapont'], 2)} / {f(c['nincs_munkapont_replika'], 3)} |")
        L.append(f"| **{k}** | **átlag** | | **{f(K[k]['hasznos_lef'], pct=True)}** {c95(K[k]['hasznos_lef_ci95'], pct=True)} | "
                 f"**{f(K[k]['lezarasi_hiba'], pct=True)}** {c95(K[k]['lezarasi_hiba_ci95'], pct=True)} | | | | – / {f(K[k]['nincs_munkapont_replika'], 3)} |")
    L += ["", "### Következtetés (D10, a három család egyenlő súlyú átlagán)", ""]
    for nev, v in res["k2"]["kovetkeztetes"].items():
        L.append(f"- **{nev}:** Δ hasznos lefedettség {f(v['delta'], pct=True)} {c95(v['ci95'], pct=True)}, p={f(v['p'], 3)}"
                 + (f" → **{v['itelet']}**" if "itelet" in v else "") + "; családonként "
                 + ", ".join(f"{fam.split('.')[1]} {f(c['delta'], pct=True)} {c95(c['ci95'], pct=True)}" for fam, c in v["csaladok"].items()) + ".")
    L += ["", "Hibafeltétel karonként (átlag; pont ≤ 5% / bizonytalan): " + ", ".join(
        f"{k} {f(K[k]['lezarasi_hiba'], pct=True)} ({f(K[k]['hibafeltetel_pont'])}{' / bizonytalan' if K[k]['hibafeltetel_bizonytalan'] else ''})" for k in FO) + "."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--be", required=True)
    ap.add_argument("--forras", choices=("k06", "k07"), required=True)
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261101)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cimke", default=None)
    a = ap.parse_args()
    cimke = a.cimke or ("tervezési próba a 06 CAL / TESZT-en (ismert adat, nem állítás)" if a.forras == "k06" else "F5, friss CAL / TESZT")
    rng = np.random.default_rng(a.seed)
    kmin = kmin_tabla(2000)
    R = {}
    for fam in CSALADOK:
        R[fam] = csalad(EXP / a.be, a.forras, fam, a.reps, rng, kmin)
        print(fam, "kész:", {k: round(v, 4) for k, v in R[fam]["pont"]["k1"].items() if k in FO}, flush=True)
    res = {"reps": a.reps, "seed": a.seed, "be": a.be, "forras": a.forras, "cimke": cimke,
           "szabaly": {"target": TARGET, "min_lezart": MIN_ACC, "hibafeltetel": HIBA_FELTETEL, "behozza": BEHOZZA},
           "k1": {nev: k1_par(R, A, B) for nev, (A, B) in K1_PAROK.items()}, "k2": k2_osszegzes(R),
           "csaladok": {fam: {k: v for k, v in x.items() if k != "_rep"} for fam, x in R.items()}}
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "elemzes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "lap.md").write_text(lap(res, cimke), encoding="utf-8")
    print((out / "lap.md").read_text())


if __name__ == "__main__":
    main()
