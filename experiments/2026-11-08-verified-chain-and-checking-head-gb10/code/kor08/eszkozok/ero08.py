"""08 G1 — erőbecslés ágankénti bontásban (08-runbook 6., D6, D9, D13): K1(b) a szabálycsaládon (fő), K1(a) mindhárom
családon. A fej még nincs, ezért szimuláció: a hatás (ΔAUROC, L-RN − L-S) feltevés, a többi a pilotból.

Modell: sabloncsoportok (klaszterek), csoportonként azonos itemszám; a (b) rossz opcióválasztása csoportonként
béta-binomiális (átlag p, csoporton belüli korreláció ICC); a két kar pontszáma binormális: s = μ·y + u_csoport + e, a két
kar e-je ρ korrelációjú, u ~ N(0, τ²) közös (μ = √(2(1 + τ²))·Φ⁻¹(AUROC)). K1(b): pozitív a rossz opció, negatív a gold
SELECT a (b)-n. K1(a): pozitív az (a) SELECT-je, negatív a (b) helyes SELECT-je, ugyanazokban a csoportokban (a párok
együtt mozognak). Az intervallum: 95%, a klaszterezett AUROC-variancia (Obuchowski 1997, Biometrics 53:567) a párra a
különbség szerkezeti komponenseivel; ellenőrzésként egy központi helyzet klaszteres bootstrappal. Olvasat a 6. pont
táblái szerint (pár: 0 és 0,05; egy kar: 0,5 és 0,60). Feltevés, nem mérés: ρ, τ², ICC és a hatás.
**A két fő próba együtt (Dani 11-03):** a szabálycsalád K1(b)-je és K1(a)-ja ugyanazon a szimulált mintán (1 (a) + 3 (b)
egységek sabloncsoportokban, a (b) hibája csoport- és egységszinten béta-binomiális; a két próba negatívjai közösek: a
(b) gold-választásai), Holm-korrekcióval (két próba, α 0,05; az első próba 97,5%-os intervallummal, a második 95%-ossal,
ha az első elutasított, különben 97,5%-ossal); ρ osztályonként (negatív / pozitív), a 07 F5 becslésével is.
  python3 kor08/eszkozok/ero08.py --sims 2000 --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np

EXP = Path(__file__).resolve().parents[2]
Z = 1.959964
ND = NormalDist()
# A pilot (megismert adat, fejlesztési számok): a szabálycsalád a javított 2. kör v4 blokkal (`G1b/kor2j.md`, 11-03,
# a hibaarány Dani döntése), a bank és a hiba a 2. kör (`G1b/kor2.md`). A K1(b) L-S AUROC-ja a szabálycsaládon 6 hibán
# áll (v1: 0,79, v4: 0,95), ezért rácson.
PILOT = {
    "szabaly.koltsegelszamolas": {"p_b": 0.069, "select_a": 28 / 28, "auc_a": 0.61},
    "penzugy.bankparositas": {"p_b": 3 / 89, "select_a": 28 / 29, "auc_a": 0.94},
    "muszaki.hibaelharitas": {"p_b": 3 / 90, "select_a": 30 / 30, "auc_a": 0.97},
}
G_CSOPORT = 40  # sabloncsoport (D6: ≥ 30)
TAU2, ICC = 0.2, 0.05
RHO = (0.3, 0.6)
DELTA = (0.0, 0.05, 0.10)
NB_SZAB = (450, 580, 650, 800, 1200, 1600)  # a (b) mérete a szabálycsaládon (Dani 11-03: 1600)
AUC_B = (0.70, 0.80, 0.90)
NA = (65, 100, 150, 200)  # az (a) mérete a banknál és a hibánál; (b) = 3 · (a)


def mu(auc: float, tau2: float) -> float:
    return math.sqrt(2 * (1 + tau2)) * ND.inv_cdf(min(auc, 0.999))


def komponensek(s: np.ndarray, y: np.ndarray) -> tuple[float, np.ndarray, np.ndarray]:
    """AUROC és a szerkezeti komponensek (V10 a pozitívokra, V01 a negatívokra); folytonos pontszám, nincs döntetlen."""
    r = np.empty(len(s))
    r[np.argsort(s, kind="stable")] = np.arange(1, len(s) + 1)
    pos, neg = y == 1, y == 0
    m, n = pos.sum(), neg.sum()
    rp = np.empty(m)
    rp[np.argsort(s[pos], kind="stable")] = np.arange(1, m + 1)
    rn = np.empty(n)
    rn[np.argsort(s[neg], kind="stable")] = np.arange(1, n + 1)
    v10 = (r[pos] - rp) / n
    v01 = 1 - (r[neg] - rn) / m
    return float(v10.mean()), v10, v01


def obu_var(v10: np.ndarray, v01: np.ndarray, cp: np.ndarray, cn: np.ndarray, k: int, auc: float) -> float:
    mk, nk = np.bincount(cp, minlength=k), np.bincount(cn, minlength=k)
    a = np.bincount(cp, weights=v10, minlength=k) - mk * auc
    b = np.bincount(cn, weights=v01, minlength=k) - nk * auc
    m, n = mk.sum(), nk.sum()
    s10 = k / ((k - 1) * m) * (a ** 2).sum()
    s01 = k / ((k - 1) * n) * (b ** 2).sum()
    s11 = k / (k - 1) * (a * b).sum()
    return float(max(s10 / m + s01 / n + 2 * s11 / (m * n), 1e-12))


def olvasat_par(lo: float, hi: float, est: float) -> str:
    if lo > 0:
        return "javít érdemben" if est >= 0.05 else "javít, de gyengén"
    if hi < 0:
        return "ront"
    return "érdemben nem javít" if hi < 0.05 else "nem eldönthető"


def olvasat_kar(lo: float, hi: float, est: float) -> str:
    if lo > 0.5:
        return "felismeri, érdemben" if est >= 0.60 else "felismeri, de gyengén"
    if hi < 0.5:
        return "fordítva rangsorol"
    return "gyakorlatilag nem ismeri fel" if hi < 0.60 else "nem eldönthető"


def adat(rng, ag: str, n_b: int, n_a: int, p_b: float, sel_a: float, g: int, icc: float):
    """Itemek: csoport, y (1 = pozitív) — K1(b): a (b) SELECT-jei; K1(a): az (a) SELECT-jei és a (b) helyes SELECT-jei."""
    nb_g = np.full(g, n_b // g) + (np.arange(g) < n_b % g)
    pg = rng.beta(p_b * (1 - icc) / icc, (1 - p_b) * (1 - icc) / icc, g) if icc > 0 else np.full(g, p_b)
    rossz = rng.binomial(nb_g, pg)
    if ag == "b":
        c = np.repeat(np.arange(g), nb_g)
        y = np.concatenate([np.r_[np.ones(r), np.zeros(n - r)] for r, n in zip(rossz, nb_g)])
        return c, y.astype(int)
    na_g = np.full(g, n_a // g) + (np.arange(g) < n_a % g)
    sel = rng.binomial(na_g, sel_a)
    c = np.concatenate([np.repeat(np.arange(g), sel), np.repeat(np.arange(g), nb_g - rossz)])
    y = np.r_[np.ones(sel.sum()), np.zeros((nb_g - rossz).sum())].astype(int)
    return c, y


def egy(rng, ag, n_b, n_a, p_b, sel_a, auc_s, delta, rho, g, icc, tau2, boot: int = 0) -> dict | None:
    c, y = adat(rng, ag, n_b, n_a, p_b, sel_a, g, icc)
    if y.sum() < 2 or (1 - y).sum() < 2:
        return None
    u = rng.normal(0, math.sqrt(tau2), g)[c]
    e1 = rng.normal(size=len(y))
    e2 = rho * e1 + math.sqrt(1 - rho ** 2) * rng.normal(size=len(y))
    s_s = mu(auc_s, tau2) * y + u + e1
    s_r = mu(min(auc_s + delta, 0.999), tau2) * y + u + e2
    a_s, v10s, v01s = komponensek(s_s, y)
    a_r, v10r, v01r = komponensek(s_r, y)
    cp, cn = c[y == 1], c[y == 0]
    d = a_r - a_s
    se_d = math.sqrt(obu_var(v10r - v10s, v01r - v01s, cp, cn, g, d))
    se_r = math.sqrt(obu_var(v10r, v01r, cp, cn, g, a_r))
    out = {"hibak": int(y.sum()) if ag == "b" else None, "d": d, "lo": d - Z * se_d, "hi": d + Z * se_d, "a_r": a_r,
           "lo_r": a_r - Z * se_r, "hi_r": a_r + Z * se_r}
    if boot:
        ds, csop = [], [np.flatnonzero(c == j) for j in range(g)]
        for _ in range(boot):
            idx = np.concatenate([csop[j] for j in rng.integers(0, g, g)])
            yy = y[idx]
            if yy.sum() < 1 or (1 - yy).sum() < 1:
                continue
            ds.append(komponensek(s_r[idx], yy)[0] - komponensek(s_s[idx], yy)[0])
        out["lo_b"], out["hi_b"] = (float(np.percentile(ds, 2.5)), float(np.percentile(ds, 97.5)))
    return out


def helyzet(rng, sims: int, **kw) -> dict:
    rs = [r for _ in range(sims) if (r := egy(rng, **kw)) is not None]
    po = {k: sum(olvasat_par(r["lo"], r["hi"], r["d"]) == k for r in rs) / len(rs)
          for k in ("javít érdemben", "javít, de gyengén", "nem eldönthető", "érdemben nem javít", "ront")}
    ko = {k: sum(olvasat_kar(r["lo_r"], r["hi_r"], r["a_r"]) == k for r in rs) / len(rs)
          for k in ("felismeri, érdemben", "felismeri, de gyengén", "nem eldönthető", "gyakorlatilag nem ismeri fel",
                    "fordítva rangsorol")}
    res = {"n_sim": len(rs), "kimaradt": sims - len(rs), "par": po, "kar": ko,
           "also_hatar_0_folott": sum(r["lo"] > 0 for r in rs) / len(rs),
           "felszelesseg": float(np.mean([(r["hi"] - r["lo"]) / 2 for r in rs]))}
    if rs[0]["hibak"] is not None:
        h = [r["hibak"] for r in rs]
        res |= {"hibak_atlag": float(np.mean(h)), "hibak_p10": float(np.percentile(h, 10)),
                "P_hibak_legalabb_40": sum(x >= 40 for x in h) / len(h)}
    if "lo_b" in rs[0]:
        res["bootstrap"] = {"also_hatar_0_folott": sum(r["lo_b"] > 0 for r in rs) / len(rs),
                            "felszelesseg": float(np.mean([(r["hi_b"] - r["lo_b"]) / 2 for r in rs]))}
    return res


def _beta(rng, m, icc: float, size=None):
    m = np.clip(m, 1e-9, 1 - 1e-9)
    return rng.beta(m * (1 - icc) / icc, (1 - m) * (1 - icc) / icc, size) if icc > 0 else np.broadcast_to(m, size or np.shape(m))


def _proba(s_s, s_r, c, pos, neg, g) -> tuple[float, float]:
    idx = pos | neg
    y, cc = pos[idx].astype(int), c[idx]
    a_s, v10s, v01s = komponensek(s_s[idx], y)
    a_r, v10r, v01r = komponensek(s_r[idx], y)
    d = a_r - a_s
    return d, math.sqrt(obu_var(v10r - v10s, v01r - v01s, cc[y == 1], cc[y == 0], g, d))


def egyutt(rng, n_egyseg, g, p_b, sel_a, auc_b, auc_a, d_b, d_a, rho_neg, rho_pos, icc, icc_e, tau2) -> dict | None:
    """Egy szimulált minta a két fő próbára: K1(b) (pozitív: a (b) rossz választása) és K1(a) (pozitív: az (a)
    SELECT-je), közös negatívokkal (a (b) gold-választásai); Holm két próbára."""
    ue = np.full(g, n_egyseg // g) + (np.arange(g) < n_egyseg % g)
    cs_e = np.repeat(np.arange(g), ue)
    pu = _beta(rng, _beta(rng, np.full(g, p_b), icc)[cs_e], icc_e)
    rossz = rng.binomial(1, np.repeat(pu, 3)).astype(bool)
    a_sel = rng.binomial(1, sel_a, n_egyseg).astype(bool)
    c = np.r_[np.repeat(cs_e, 3), cs_e[a_sel]]
    osz = np.r_[rossz.astype(int), np.full(a_sel.sum(), 2)]  # 0: (b) gold, 1: (b) rossz, 2: (a) SELECT
    if (osz == 1).sum() < 2:
        return None
    u = rng.normal(0, math.sqrt(tau2), g)[c]
    e1 = rng.normal(size=len(osz))
    rh = np.where(osz == 0, rho_neg, rho_pos)
    e2 = rh * e1 + np.sqrt(1 - rh ** 2) * rng.normal(size=len(osz))
    m_s = np.select([osz == 1, osz == 2], [mu(auc_b, tau2), mu(auc_a, tau2)], 0.0)
    m_r = np.select([osz == 1, osz == 2], [mu(min(auc_b + d_b, 0.999), tau2), mu(min(auc_a + d_a, 0.999), tau2)], 0.0)
    s_s, s_r = m_s + u + e1, m_r + u + e2
    neg = osz == 0
    res = {}
    for nev, pos in (("K1b", osz == 1), ("K1a", osz == 2)):
        d, se = _proba(s_s, s_r, c, pos, neg, g)
        res[nev] = {"d": d, "se": se, "p": 2 * (1 - ND.cdf(abs(d / se)))}
    elso, masodik = sorted(res, key=lambda k: res[k]["p"])
    z1, z95 = ND.inv_cdf(1 - 0.025 / 2), Z
    rej1 = res[elso]["p"] < 0.025 and res[elso]["d"] > 0
    for k, z in ((elso, z1), (masodik, z95 if rej1 else z1)):
        r = res[k]
        r["lo"], r["hi"] = r["d"] - z * r["se"], r["d"] + z * r["se"]
    res["hibak"] = int(rossz.sum())
    return res


def egyutt_helyzet(rng, sims: int, **kw) -> dict:
    rs = [r for _ in range(sims) if (r := egyutt(rng, **kw)) is not None]
    out = {"n_sim": len(rs), "hibak_atlag": float(np.mean([r["hibak"] for r in rs]))}
    for k in ("K1b", "K1a"):
        out[k] = {"alsó > 0": sum(r[k]["lo"] > 0 for r in rs) / len(rs),
                  "érdemben": sum(olvasat_par(r[k]["lo"], r[k]["hi"], r[k]["d"]) == "javít érdemben" for r in rs) / len(rs),
                  "nem eldönthető": sum(olvasat_par(r[k]["lo"], r[k]["hi"], r[k]["d"]) == "nem eldönthető" for r in rs) / len(rs)}
    out["mindkettő"] = sum(r["K1b"]["lo"] > 0 and r["K1a"]["lo"] > 0 for r in rs) / len(rs)
    out["legalább egy"] = sum(r["K1b"]["lo"] > 0 or r["K1a"]["lo"] > 0 for r in rs) / len(rs)
    return out


RHO_07 = (0.29, 0.46)  # a 07 F5 szabálycsaládi TESZT-je: B1-4S ↔ B1-4R (seed-átlag) Spearman → normális ρ, helyes / hibás SELECT
EGYSEG = 534  # 1 (a) + 3 (b): 1602 (b) + kb. 534 (a)
DELTA_PAR = ((0.05, 0.05), (0.05, 0.0), (0.0, 0.05), (0.0, 0.0), (0.10, 0.10))


def p(x: float) -> str:
    return f"{100 * x:.0f}%"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--boot-sims", type=int, default=300)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    sz = PILOT["szabaly.koltsegelszamolas"]
    alap = dict(g=G_CSOPORT, icc=ICC, tau2=TAU2)
    res: dict = {"feltevesek": {"pilot": PILOT, "sabloncsoport": G_CSOPORT, "tau2": TAU2, "icc": ICC, "rho": RHO,
                                "delta": DELTA, "sims": a.sims, "seed": a.seed}, "K1b": [], "K1b_erzekenyseg": [],
           "K1a": []}
    for auc in AUC_B:
        for rho in RHO:
            for nb in NB_SZAB:
                r = {"auc_s": auc, "rho": rho, "n_b": nb}
                for d in DELTA:
                    r[f"delta={d}"] = helyzet(rng, a.sims, ag="b", n_b=nb, n_a=nb // 3, p_b=sz["p_b"], sel_a=1.0,
                                              auc_s=auc, delta=d, rho=rho, **alap)
                res["K1b"].append(r)
    kozep = dict(ag="b", n_b=1600, n_a=533, p_b=sz["p_b"], sel_a=1.0, auc_s=0.80, delta=0.05, rho=0.6)
    for nev, kw in (("sabloncsoport 30", {"g": 30}), ("sabloncsoport 60", {"g": 60}), ("ICC 0", {"icc": 0.0}),
                    ("ICC 0,15", {"icc": 0.15}), ("τ² 0", {"tau2": 0.0}), ("τ² 0,5", {"tau2": 0.5})):
        res["K1b_erzekenyseg"].append({"nev": nev, **helyzet(rng, a.sims, **(kozep | alap | kw))})
    res["bootstrap_ellenorzes"] = {"helyzet": "K1(b), n_b 1600, AUROC 0,80, ρ 0,6, Δ 0,05",
                                   **helyzet(rng, a.boot_sims, **(kozep | alap), boot=a.boot)}
    for fam, pp in PILOT.items():
        nas = [nb // 3 for nb in NB_SZAB] if fam == "szabaly.koltsegelszamolas" else list(NA)
        for rho in RHO:
            for na in nas:
                r = {"csalad": fam, "auc_s": pp["auc_a"], "rho": rho, "n_a": na, "n_b": 3 * na}
                for d in DELTA:
                    r[f"delta={d}"] = helyzet(rng, a.sims, ag="a", n_b=3 * na, n_a=na, p_b=pp["p_b"], sel_a=pp["select_a"],
                                              auc_s=pp["auc_a"], delta=d, rho=rho, **alap)
                res["K1a"].append(r)
    res["egyutt"] = []
    for icc_e in (0.0, 0.3):
        for rho_neg, rho_pos in ((0.3, 0.3), RHO_07, (0.6, 0.6)):
            for auc_b in AUC_B:
                for d_b, d_a in DELTA_PAR:
                    res["egyutt"].append({"icc_e": icc_e, "rho": [rho_neg, rho_pos], "auc_b": auc_b, "auc_a": sz["auc_a"],
                                          "d_b": d_b, "d_a": d_a, **egyutt_helyzet(
                                              rng, a.sims, n_egyseg=EGYSEG, g=G_CSOPORT, p_b=sz["p_b"], sel_a=sz["select_a"],
                                              auc_b=auc_b, auc_a=sz["auc_a"], d_b=d_b, d_a=d_a, rho_neg=rho_neg,
                                              rho_pos=rho_pos, icc=ICC, icc_e=icc_e, tau2=TAU2)})
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "ero08.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "ero08.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


def lap(res: dict) -> str:
    f = res["feltevesek"]
    L_ = ["# G1 — erőbecslés ágankénti bontásban (szimuláció; a hatás feltevés, a többi a pilotból)", "",
          f"Sabloncsoport {f['sabloncsoport']}, τ² {str(f['tau2']).replace('.', ',')}, ICC {str(f['icc']).replace('.', ',')}, "
          f"{f['sims']} szimuláció helyzetenként, "
          "95%-os intervallum a klaszterezett AUROC-varianciával (Obuchowski 1997). A pár L-RN − L-S, az olvasat a "
          "runbook 6. pontja szerint (0 és 0,05). „Δ 0”: az alsó határ 0 fölött (álpozitív arány).", "",
          "## A két fő próba együtt, Holm-korrekcióval (a döntési szabály; szabálycsalád)", "",
          f"{EGYSEG} egység × (1 (a) + 3 (b)) = {3 * EGYSEG} (b) + kb. {EGYSEG} (a), {f['sabloncsoport']} sabloncsoport; a K1(a) "
          f"L-S AUROC-ja a pilotból (0,61). ρ osztályonként (helyes / hibás választás); a 07 F5 becslése "
          f"{str(RHO_07[0]).replace('.', ',')} / {str(RHO_07[1]).replace('.', ',')}. ICC_e: a (b) hibájának egységen "
          "belüli korrelációja (a három átfogalmazás együtt hibázik). Cellánként: P(alsó határ > 0) a Holm-szintű "
          "intervallummal, K1(b) / K1(a).", "",
          "| ICC_e | ρ (helyes / hibás) | K1(b) L-S AUROC | Δ 0,05 / 0,05 | Δ 0,05 / 0 | Δ 0 / 0,05 | Δ 0 / 0 | "
          "Δ 0,10 / 0,10 |", "|---|---|---|---|---|---|---|---|"]
    sor: dict = {}
    for r in res.get("egyutt", []):
        sor.setdefault((r["icc_e"], tuple(r["rho"]), r["auc_b"]), {})[(r["d_b"], r["d_a"])] = r
    for (icc_e, rho, auc_b), cells in sor.items():
        L_.append(f"| {str(icc_e).replace('.', ',')} | {str(rho[0]).replace('.', ',')} / {str(rho[1]).replace('.', ',')} | "
                  f"{auc_b:.2f} | " + " | ".join(f"{p(cells[dp]['K1b']['alsó > 0'])} / {p(cells[dp]['K1a']['alsó > 0'])}"
                                                 for dp in DELTA_PAR) + " |")
    L_ += ["", "A „Δ 0 / 0” oszlop az álpozitív arány próbánként (névlegesen ≤ 2,5% egy irányban). A K1(b) várt hibaszáma "
           f"{3 * EGYSEG} (b)-itemen kb. {round(3 * EGYSEG * PILOT['szabaly.koltsegelszamolas']['p_b'])}.", "",
           "## K1(b), szabálycsalád (fő), egyedül, Holm nélkül", "",
          f"A (b) hibaaránya {100 * f['pilot']['szabaly.koltsegelszamolas']['p_b']:.1f}".replace(".", ",") +
          "% (Dani 11-03). Az L-S AUROC-ja rácson: a pilot 6 hibán áll.", "",
          "Valódi Δ = 0,05-nél az „érdemben” olvasat (alsó határ > 0 és pontbecslés ≥ 0,05) elvből legfeljebb kb. 50%: a "
          "pontbecslés a valódi érték körül szór. Ezért mellette az alsó határ > 0 (bármilyen javulás kimutatva).", "",
          "| L-S AUROC | ρ | (b) item | hiba (átlag / P ≥ 40) | félszélesség | Δ 0: alsó > 0 | Δ 0,05: alsó > 0 | "
          "Δ 0,05: érdemben / gyengén / nem eldönthető | Δ 0,10: érdemben / alsó > 0 |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in res["K1b"]:
        d0, d5, d10 = r["delta=0.0"], r["delta=0.05"], r["delta=0.1"]
        L_.append(f"| {r['auc_s']:.2f} | {r['rho']} | {r['n_b']} | {d5['hibak_atlag']:.0f} / {p(d5['P_hibak_legalabb_40'])} | "
                  f"{d5['felszelesseg']:.3f} | {p(d0['also_hatar_0_folott'])} | {p(d5['also_hatar_0_folott'])} | "
                  f"{p(d5['par']['javít érdemben'])} / "
                  f"{p(d5['par']['javít, de gyengén'])} / {p(d5['par']['nem eldönthető'])} | "
                  f"{p(d10['par']['javít érdemben'])} / {p(d10['also_hatar_0_folott'])} |")
    L_ += ["", "**Érzékenység** (n_b 1600, L-S AUROC 0,80, ρ 0,6, Δ 0,05):", "",
           "| változás | félszélesség | érdemben | gyengén | nem eldönthető | alsó > 0 |", "|---|---|---|---|---|---|"]
    for r in res["K1b_erzekenyseg"]:
        L_.append(f"| {r['nev']} | {r['felszelesseg']:.3f} | {p(r['par']['javít érdemben'])} | "
                  f"{p(r['par']['javít, de gyengén'])} | {p(r['par']['nem eldönthető'])} | {p(r['also_hatar_0_folott'])} |")
    b = res["bootstrap_ellenorzes"]
    L_ += ["", f"**Ellenőrzés klaszteres bootstrappal** ({b['helyzet']}, {b['n_sim']} szimuláció): alsó határ 0 fölött "
           f"{p(b['bootstrap']['also_hatar_0_folott'])} (az analitikus intervallummal {p(b['also_hatar_0_folott'])}), "
           f"félszélesség {b['bootstrap']['felszelesseg']:.3f} ({b['felszelesseg']:.3f}).", "",
           "## K1(a), családonként", "",
           "Pozitív: az (a) SELECT-je; negatív: a (b) helyes SELECT-je; (b) = 3 · (a). Az L-S AUROC-ja a pilotból.", "",
           "| család | L-S AUROC | ρ | (a) item | félszélesség | Δ 0: alsó > 0 | Δ 0,05 (ténylegesen) | Δ 0,05: alsó > 0 | "
           "Δ 0,05: érdemben / gyengén / nem eldönthető | Δ 0,10: érdemben / alsó > 0 |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["K1a"]:
        d0, d5, d10 = r["delta=0.0"], r["delta=0.05"], r["delta=0.1"]
        L_.append(f"| {r['csalad']} | {r['auc_s']:.2f} | {r['rho']} | {r['n_a']} | {d5['felszelesseg']:.3f} | "
                  f"{p(d0['also_hatar_0_folott'])} | {min(r['auc_s'] + 0.05, 0.999) - r['auc_s']:.3f} | "
                  f"{p(d5['also_hatar_0_folott'])} | {p(d5['par']['javít érdemben'])} / {p(d5['par']['javít, de gyengén'])} / "
                  f"{p(d5['par']['nem eldönthető'])} | {p(d10['par']['javít érdemben'])} / {p(d10['also_hatar_0_folott'])} |")
    L_ += ["", "A bank és a hiba L-S AUROC-ja a pilotban 0,94 és 0,97: a 0,05-ös javulásnak ott a plafon szab határt "
           "(0,99 fölé a binormális modell 0,999-re vág)."]
    return "\n".join(L_) + "\n"


if __name__ == "__main__":
    main()
