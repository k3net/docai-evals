"""08 G5 — K1: az értelmezési teszt elemzője (G1-rögzítés 1., 3., 6., 7., 8.).

Bemenet családonként: a pontozott szelet (`b1rel08 pontoz`: döntések és a karok megbízhatósága, nagyobb = megbízhatóbb),
az értelmezési itemek (`meta.ertelmezes`: az egység — `egyseg`, a pilotban `par` — és a változat, `alt` a / b; a
klaszter a `template_group_id`), és a lánc kimenete (`lanc_<család>.jsonl`, `items/<család>.jsonl`; valós kinyerésnél
az orákulum-út is, a döntést befolyásoló kinyerési hibához).

**Az értelmezési diagnózis (6.):** a tétel a modellhez jutott (nincs automatikus kötés, nem ment emberhez), nincs döntést
befolyásoló kinyerési hiba (a lánc kimenete, a megmaradt jelöltek, a kötés és a modellnek mutatott tétel azonos az
orákulum-útéval), és a (b)-nél a gold nincs kizárva (az (a)-nál a helyes válasz Y, nem opció). Egy egység (b)-je és
(a)-ja külön kerül be vagy marad ki.
**K1(b):** a (b) SELECT-jei; pozitív a rossz opció, negatív a gold választása. **K1(a):** pozitív az (a) SELECT-je, negatív
a (b) helyes SELECT-je. Hibapontszám = −megbízhatóság (3.); az AUROC P(pozitív hibapontszáma > negatívé), a döntetlen
fél. **SELECT-AURC** ugyanazon a halmazon, a megbízhatóság szerint csökkenő sorrendben (a kisebb a jobb).
**Statisztika (8.):** sabloncsoportos klaszteres bootstrap (a klaszterek az egész családi tesztből), replikánként a
seedek mérőinek átlaga; kétoldali bootstrap-p. **A két fő próba** (`--fo-par`, a szabálycsaládon K1(b) és K1(a)) Holm-mal:
a kisebb p-jű 0,025-ös szinten (97,5%-os intervallum), a másik 0,05-ösön (95%), ha az első elutasított, különben
0,025-ösön; a 95%-os intervallum mindig közölve. A másodlagos összevetések korrekció nélkül, 95%-kal. Olvasat a 8. pont
tábláival (karra: 0,5 és 0,60; párra: 0 és 0,05); a SELECT-AURC-ra nincs érdemi küszöb.
**Leíró:** nyelvenként; a jel fajtája szerint (a szabálycsalád G2-forgatókönyvein: a jel szó szerint kimondja-e a gold
leírásának egy szavát, `forgatokonyv08_szab.jel_fajta`; Dani 11-04); az (a) Y-aránya; a τ fölött lezárt (a)-arány, ha `--tau` adott; a lánc után legalább két
lehetséges jelölt (a strukturálisan nem szétválasztott tételek); seedenként; Brier és ECE (10 egyenlő sáv) a
kalibrált valószínűségen (`--cal`: temperature a friss CAL-on; nélküle a pilotban kalibrálatlan, jelölve).
Önellenőrzés (3.): az L-S K1(b)- és K1(a)-AUROC-ja a teljes diagnózis-halmazon kerül a kimenetbe, a pilotban a
`g1b_ert08` számával vetendő össze (`--ellenoriz`).

  python3 kor08/eszkozok/g5_k1_08.py --csalad szabaly.koltsegelszamolas:cache/k08/pontoz/G1/oERT2J_szabaly.koltsegelszamolas_ERT2J.json:kor08/adat/ertelmezes/kor2j/items:kor08/adat/G1/orakulum_ERT2J \\
      --fo-par L-R07,L-S --reps 2000 --out kor08/eredmenyek/G1/g5_k1_pilot
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE)]
import forgatokonyv08_szab as FK  # noqa: E402
import lanc08 as L  # noqa: E402

MASODLAGOS = (("L-R07", "L-S"), ("L-R", "L-S"), ("L-RN", "L-R"), ("L-RN", "L-LRN"), ("L-LRN", "L-S"))
AGAK = ("K1b", "K1a")
KAR_KUSZOB, PAR_KUSZOB = 0.60, 0.05
SAVOK = 10


# --- adat --------------------------------------------------------------------------------------------------------------

_JF: dict = {}


def jelfajta_of(fam: str, klaszter: str, lang: str) -> str:
    """A szabálycsalád G2-forgatókönyvének jelfajtája (`<család>:G2:<Fxx>`); más klaszteren „–”."""
    if not klaszter.startswith(f"{fam}:G2:"):
        return "–"
    if not _JF:
        _JF.update(FK.jel_fajtak())
    return _JF.get((klaszter.rsplit(":", 1)[-1], lang), "–")

def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def diagnozis(fam: str, ids: list[str], items: dict, lanc_dir: Path, orakulum_dir: Path | None) -> tuple[np.ndarray, Counter]:
    """A 6. pont halmaza itemenként, és a kiesés oka."""
    lanc = {r["id"]: r for r in jsonl(lanc_dir / f"lanc_{fam}.jsonl")}
    mod = {r["id"]: r for r in jsonl(lanc_dir / "items" / f"{fam}.jsonl")}
    if orakulum_dir is not None:
        o_lanc = {r["id"]: r for r in jsonl(orakulum_dir / f"lanc_{fam}.jsonl")}
        o_mod = {r["id"]: r for r in jsonl(orakulum_dir / "items" / f"{fam}.jsonl")}
    ok, ok_ok = np.zeros(len(ids), bool), Counter()
    for n, i in enumerate(ids):
        r, it = lanc[i], items[i]
        if r["kimenet"] != "modell":
            ok_ok[f"kimenet: {r['kimenet']}"] += 1
            continue
        if orakulum_dir is not None:
            o = o_lanc[i]
            kulcs = (r["kimenet"], sorted(r["megmaradt"]), r["kotes"])
            if kulcs != (o["kimenet"], sorted(o["megmaradt"]), o["kotes"]) or i not in o_mod \
                    or (mod[i]["state"], mod[i]["options"]) != (o_mod[i]["state"], o_mod[i]["options"]):
                ok_ok["döntést befolyásoló kinyerési hiba"] += 1
                continue
        if it["alt"] == "b" and it["gold"] not in r["megmaradt"]:
            ok_ok["a gold kizárva"] += 1
            continue
        ok[n] = True
    return ok, ok_ok


class Csalad:
    """Egy család értelmezési tesztje, a pontozott szelet itemsorrendjében."""

    def __init__(self, fam: str, pont: Path, items_dir: Path, lanc_dir: Path, orakulum_dir: Path | None):
        d = json.loads(pont.read_text())
        k4 = d["keret4"]
        self.fam, self.ids = fam, k4["ids"]
        raw = {it["id"]: it for it in jsonl(items_dir / f"{fam}.jsonl")}
        items = {}
        for i in self.ids:
            e = raw[i]["meta"]["ertelmezes"]
            items[i] = {"alt": e["alt"], "egyseg": e.get("egyseg", e.get("par")), "gold": raw[i]["gold"],
                        "klaszter": raw[i]["template_group_id"], "lang": raw[i]["lang"]}
        self.n = len(self.ids)
        D = k4["dontes"]
        self.alt = np.array([items[i]["alt"] for i in self.ids])
        self.lang = np.array([items[i]["lang"] for i in self.ids])
        self.jelfajta = np.array([jelfajta_of(fam, items[i]["klaszter"], items[i]["lang"]) for i in self.ids])
        self.kind = np.array([D[i]["kind"] for i in self.ids])
        self.helyes = np.array([bool(D[i]["helyes"]) for i in self.ids])
        self.diag, self.kieses = diagnozis(fam, self.ids, items, lanc_dir, orakulum_dir)
        lanc = {r["id"]: r for r in jsonl(lanc_dir / f"lanc_{fam}.jsonl")}
        self.ket_jelolt = np.array([len(lanc[i]["megmaradt"]) >= 2 for i in self.ids])
        self.valoszinuseg = d.get("valoszinuseg", {})
        self.pont: dict[str, list[np.ndarray]] = defaultdict(list)
        for k in sorted(k4["pontszam"]):
            self.pont[k.split("|")[0]].append(np.asarray(k4["pontszam"][k], float))
        self.ag = self.agak(self.diag)
        cl: dict = {}
        for n, i in enumerate(self.ids):
            cl.setdefault(items[i]["klaszter"], []).append(n)
        self.clusters = [np.array(v) for v in cl.values()]
        self.egysegek = len({items[i]["egyseg"] for i in self.ids})

    def agak(self, alap: np.ndarray) -> dict[str, tuple[np.ndarray, np.ndarray]]:
        """Ág → (halmaz, pozitív = hiba) az alaphalmazon; a SELECT-AURC helyessége = nem pozitív."""
        sel = alap & (self.kind == "SELECT")
        b, a = self.alt == "b", self.alt == "a"
        return {"K1b": (sel & b, sel & b & ~self.helyes), "K1a": ((sel & a) | (sel & b & self.helyes), sel & a)}

    def huzas(self, rng: np.random.Generator) -> np.ndarray:
        C = len(self.clusters)
        return np.concatenate([self.clusters[c] for c in rng.integers(0, C, C)])


# --- mérők -------------------------------------------------------------------------------------------------------------

def auroc(err: np.ndarray, pos: np.ndarray) -> float:
    """P(pozitív hibapontszáma > negatívé), a döntetlen fél; ismétlődő (bootstrap) indexekkel is."""
    n1 = int(pos.sum())
    n0 = len(pos) - n1
    if not n1 or not n0:
        return math.nan
    r = rankdata(err)
    return float((r[pos].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def aurc(q: np.ndarray, cor: np.ndarray) -> float:
    if not len(q):
        return math.nan
    o = np.argsort(-q, kind="stable")
    err = np.cumsum(~cor[o])
    return float((err / np.arange(1, len(q) + 1)).mean())


def merok(C: Csalad, kar: str, idx: np.ndarray) -> dict[str, float]:
    """Az ágak AUROC-ja és SELECT-AURC-ja a seedek átlagaként."""
    out = {}
    for ag in AGAK:
        halmaz, pos = C.ag[ag]
        s = idx[halmaz[idx]]
        p = pos[s]
        out[f"{ag}_auroc"] = float(np.nanmean([auroc(-q[s], p) for q in C.pont[kar]])) if len(s) else math.nan
        out[f"{ag}_aurc"] = float(np.nanmean([aurc(q[s], ~p) for q in C.pont[kar]])) if len(s) else math.nan
    return out


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def kalibral(C: Csalad, cal: dict | None) -> dict[str, list[np.ndarray] | None]:
    """A kar valószínűsége: temperature a friss CAL-on (a CAL szigorú helyességére, minden döntésen), vagy a pilotban
    kalibrálatlanul (az L-S q-ja, a fejeknél a logit szigmoidja)."""
    from scipy.optimize import minimize_scalar  # noqa: PLC0415
    out = {}
    for kar, qs in C.pont.items():
        z = [logit(q) if C.valoszinuseg.get(kar) else q for q in qs]
        if cal is None:
            out[kar] = [1 / (1 + np.exp(-x)) for x in z]
            continue
        k4 = cal["keret4"]
        y = np.array([bool(k4["dontes"][i]["helyes"]) for i in k4["ids"]])
        cz = [np.asarray(k4["pontszam"][k], float) for k in sorted(k4["pontszam"]) if k.split("|")[0] == kar]
        if not cz:
            out[kar] = None
            continue
        res = []
        for x, c in zip(z, cz):
            c = logit(c) if C.valoszinuseg.get(kar) else c

            def nll(lt: float, c=c) -> float:
                pp = np.clip(1 / (1 + np.exp(-c / math.exp(lt))), 1e-9, 1 - 1e-9)
                return float(-(y * np.log(pp) + (~y) * np.log(1 - pp)).sum())
            t = math.exp(minimize_scalar(nll, bounds=(-4, 4), method="bounded").x)  # type: ignore[attr-defined]
            res.append(1 / (1 + np.exp(-x / t)))
        out[kar] = res
    return out


def brier_ece(p: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    if not len(p):
        return math.nan, math.nan
    b = float(((p - y) ** 2).mean())
    sav = np.minimum((p * SAVOK).astype(int), SAVOK - 1)
    ece = sum(abs(p[sav == k].mean() - y[sav == k].mean()) * (sav == k).sum() for k in range(SAVOK) if (sav == k).any())
    return b, float(ece / len(p))


# --- összevetés és olvasat -------------------------------------------------------------------------------------------

def ci(x: np.ndarray, szint: float = 0.95) -> list[float]:
    x = x[~np.isnan(x)]
    a = (1 - szint) / 2
    return [float(np.quantile(x, a)), float(np.quantile(x, 1 - a))] if len(x) else [math.nan, math.nan]


def p_ketoldali(d: np.ndarray) -> float:
    d = d[~np.isnan(d)]
    return float(min(1.0, 2 * min(np.mean(d >= 0), np.mean(d <= 0)))) if len(d) else math.nan


def olvasat_kar(pont: float, iv: list[float]) -> str:
    lo, hi = iv
    if math.isnan(pont) or math.isnan(lo):
        return "nincs adat"
    if hi < 0.5:
        return "fordítva rangsorol"
    if lo > 0.5:
        return "felismeri, érdemben" if pont >= KAR_KUSZOB else "felismeri, de gyengén"
    return "nem eldönthető" if hi >= KAR_KUSZOB else "gyakorlatilag nem ismeri fel"


def olvasat_par(pont: float, iv: list[float]) -> str:
    lo, hi = iv
    if math.isnan(pont) or math.isnan(lo):
        return "nincs adat"
    if hi < 0:
        return "ront"
    if lo > 0:
        return "javít érdemben" if pont >= PAR_KUSZOB else "javít, de gyengén"
    return "nem eldönthető" if hi >= PAR_KUSZOB else "érdemben nem javít"


def holm2(p: dict[str, float]) -> dict[str, float]:
    """A két fő próba intervallumának szintje (8.): a kisebb p-jű 97,5%, a másik 95%, ha az első elutasított."""
    a, b = sorted(p, key=lambda k: (math.isnan(p[k]), p[k]))
    elso = not math.isnan(p[a]) and p[a] <= 0.025
    return {a: 0.975, b: 0.95 if elso else 0.975}


def elemez(Cs: dict[str, Csalad], fo: tuple[str, str] | None, fo_csalad: str, reps: int, seed: int,
           cal: dict[str, dict | None], tau: dict | None) -> dict:
    rng = np.random.default_rng(seed)
    res = {"reps": reps, "seed": seed, "fo_par": fo, "fo_csalad": fo_csalad, "csaladok": {}}
    for fam, C in Cs.items():
        karok = sorted(C.pont)
        full = np.arange(C.n)
        pont = {k: merok(C, k, full) for k in karok}
        rep = {k: {m: np.empty(reps) for m in pont[k]} for k in karok}
        for r in range(reps):
            idx = C.huzas(rng)
            for k in karok:
                for m, v in merok(C, k, idx).items():
                    rep[k][m][r] = v
        F: dict = {"n": C.n, "egyseg": C.egysegek, "klaszter": len(C.clusters), "kieses": dict(C.kieses),
                   "diag_arany": float(C.diag.mean()), "diag_nyelv": {ny: float(C.diag[C.lang == ny].mean()) for ny in ("hu", "en")},
                   "diag_valtozat": {v: float(C.diag[C.alt == v].mean()) for v in ("a", "b")},
                   "esemeny": {ag: {"pozitiv": int(C.ag[ag][1].sum()), "negativ": int((C.ag[ag][0] & ~C.ag[ag][1]).sum())} for ag in AGAK},
                   "ket_jelolt": {"mind": int((C.diag & C.ket_jelolt).sum()), "diag": int(C.diag.sum())},
                   "karok": {}, "parok": {}}
        for k in karok:
            F["karok"][k] = {}
            for ag in AGAK:
                iv = ci(rep[k][f"{ag}_auroc"])
                F["karok"][k][ag] = {"auroc": pont[k][f"{ag}_auroc"], "ci95": iv, "olvasat": olvasat_kar(pont[k][f"{ag}_auroc"], iv),
                                     "aurc": pont[k][f"{ag}_aurc"], "aurc_ci95": ci(rep[k][f"{ag}_aurc"]),
                                     "seedenkent": [auroc(-q[C.ag[ag][0]], C.ag[ag][1][C.ag[ag][0]]) for q in C.pont[k]]}
        # nyelvenként (pontbecslés), az (a) Y-aránya, a τ fölött lezárt (a)-arány
        F["nyelvenkent"] = {ny: {k: merok(C, k, full[C.lang == ny]) for k in karok} for ny in ("hu", "en")}
        # a jel fajtája szerint (leíró; pontbecslés és az események)
        for x in ("szó szerint", "áttételes"):
            m = C.jelfajta == x
            if m.any():
                F.setdefault("jelfajta", {})[x] = {
                    "karok": {k: merok(C, k, full[m]) for k in karok},
                    "esemeny": {ag: {"pozitiv": int((C.ag[ag][1] & m).sum()), "halmaz": int((C.ag[ag][0] & m).sum())} for ag in AGAK}}
        a_diag = C.diag & (C.alt == "a")
        F["a_y_arany"] = float((C.kind[a_diag] == "MISSING").mean()) if a_diag.any() else math.nan
        F["a_dontesek"] = dict(Counter(C.kind[a_diag].tolist()))
        if tau and fam in tau:
            F["a_lezart_tau_felett"] = {}
            for k, t in tau[fam].items():
                ts = t if isinstance(t, list) else [t] * len(C.pont[k])
                lez = np.isin(C.kind, ("SELECT", "NONE"))
                F["a_lezart_tau_felett"][k] = float(np.mean([(a_diag & lez & (q >= tt)).sum() / max(1, a_diag.sum())
                                                             for q, tt in zip(C.pont[k], ts)]))
        # Brier és ECE a kalibrált valószínűségen, ágonként (a helyesség = nem pozitív)
        P = kalibral(C, cal.get(fam))
        F["kalibracio"] = "a friss CAL-on" if cal.get(fam) else "kalibrálatlan (pilot)"
        F["brier_ece"] = {}
        for k in karok:
            if P[k] is None:
                continue
            F["brier_ece"][k] = {}
            for ag in AGAK:
                h, pos = C.ag[ag]
                be = [brier_ece(p[h], (~pos[h]).astype(float)) for p in P[k]]
                F["brier_ece"][k][ag] = {"brier": float(np.mean([x[0] for x in be])), "ece": float(np.mean([x[1] for x in be]))}
        # párok: a fő pár (Holm), a másodlagosak (95%, korrekció nélkül)
        parok = ([fo] if fo else []) + [p for p in MASODLAGOS if p != fo]
        for A, B in parok:
            if A not in C.pont or B not in C.pont:
                continue
            nev = f"{A} − {B}"
            F["parok"][nev] = {}
            for ag in AGAK:
                d = rep[A][f"{ag}_auroc"] - rep[B][f"{ag}_auroc"]
                da = rep[A][f"{ag}_aurc"] - rep[B][f"{ag}_aurc"]
                F["parok"][nev][ag] = {"delta": pont[A][f"{ag}_auroc"] - pont[B][f"{ag}_auroc"], "ci95": ci(d), "p": p_ketoldali(d),
                                       "aurc_delta": pont[A][f"{ag}_aurc"] - pont[B][f"{ag}_aurc"], "aurc_ci95": ci(da), "_d": d}
            if fo and (A, B) == fo and fam == fo_csalad:
                szint = holm2({ag: F["parok"][nev][ag]["p"] for ag in AGAK})
                for ag in AGAK:
                    x = F["parok"][nev][ag]
                    x["fo"] = True
                    x["holm_szint"] = szint[ag]
                    x["ci_holm"] = ci(x["_d"], szint[ag])
                    x["olvasat"] = olvasat_par(x["delta"], x["ci_holm"])
            else:
                for ag in AGAK:
                    x = F["parok"][nev][ag]
                    x["olvasat_leiro"] = olvasat_par(x["delta"], x["ci95"])
            for ag in AGAK:
                F["parok"][nev][ag].pop("_d")
        res["csaladok"][fam] = F
    return res


# --- lap ---------------------------------------------------------------------------------------------------------------

def f(x, d: int = 3) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}".replace(".", ",")


def fp(p: float, reps: int) -> str:
    return f"< {f(1 / reps, 4)}" if p == 0 else f(p)


def iv(v: list[float], d: int = 3) -> str:
    return f"[{f(v[0], d)}; {f(v[1], d)}]"


def lap(res: dict, cimke: str) -> str:
    o = [f"# 08 G5 — K1: az értelmezési teszt ({cimke})", "",
         f"Sabloncsoportos klaszteres bootstrap ({res['reps']} replika, seed {res['seed']}), replikánként a seedek átlaga. "
         "Hibapontszám = −megbízhatóság; AUROC: P(pozitív hibapontszáma > negatívé). K1(b): a (b) SELECT-jei, pozitív a rossz "
         "opció. K1(a): az (a) SELECT-jei (pozitív) a (b) helyes SELECT-jei ellen. A SELECT-AURC ugyanezeken (a kisebb a jobb), "
         "érdemi küszöb nélkül.", ""]
    fo = res["fo_par"]
    if fo:
        nev = f"{fo[0]} − {fo[1]}"
        F = res["csaladok"].get(res["fo_csalad"], {})
        P = F.get("parok", {}).get(nev)
        o += [f"## A két fő próba ({nev}, {res['fo_csalad']}, Holm)", "",
              "| ág | ΔAUROC | p | Holm-szint | intervallum (Holm) | 95% | olvasat |", "|---|---|---|---|---|---|---|"]
        for ag in AGAK:
            if P:
                x = P[ag]
                o.append(f"| {ag} | {f(x['delta'])} | {fp(x['p'], res['reps'])} | {f(100 * x['holm_szint'], 1)}% | {iv(x['ci_holm'])} | "
                         f"{iv(x['ci95'])} | **{x['olvasat']}** |")
        o.append("")
    for fam, F in res["csaladok"].items():
        o += [f"## {fam}", "",
              f"{F['n']} item, {F['egyseg']} egység, {F['klaszter']} sabloncsoport. Az értelmezési diagnózis aránya "
              f"{f(100 * F['diag_arany'], 1)}% (hu {f(100 * F['diag_nyelv']['hu'], 1)}%, en {f(100 * F['diag_nyelv']['en'], 1)}%; "
              f"(a) {f(100 * F['diag_valtozat']['a'], 1)}%, (b) {f(100 * F['diag_valtozat']['b'], 1)}%); kiesés: "
              + ("; ".join(f"{k} {v}" for k, v in F["kieses"].items()) or "nincs") + ".",
              f"Események: K1(b) {F['esemeny']['K1b']['pozitiv']} rossz opció / {F['esemeny']['K1b']['negativ']} gold; K1(a) "
              f"{F['esemeny']['K1a']['pozitiv']} (a)-SELECT / {F['esemeny']['K1a']['negativ']} (b) helyes SELECT. A lánc után "
              f"legalább két lehetséges jelölt: {F['ket_jelolt']['mind']} / {F['ket_jelolt']['diag']}.", "",
              "| kar | ág | AUROC | 95% | olvasat | seedenként | SELECT-AURC | 95% |", "|---|---|---|---|---|---|---|---|"]
        for k, X in F["karok"].items():
            for ag in AGAK:
                x = X[ag]
                sd = " / ".join(f(s) for s in x["seedenkent"]) if len(x["seedenkent"]) > 1 else "–"
                o.append(f"| {k} | {ag} | {f(x['auroc'])} | {iv(x['ci95'])} | {x['olvasat']} | {sd} | {f(x['aurc'])} | {iv(x['aurc_ci95'])} |")
        if F["parok"]:
            o += ["", "| pár | ág | ΔAUROC | 95% | p | olvasat | ΔSELECT-AURC | 95% |", "|---|---|---|---|---|---|---|---|"]
            for nev, X in F["parok"].items():
                for ag in AGAK:
                    x = X[ag]
                    ol = f"**{x['olvasat']}** (fő, Holm)" if x.get("fo") else f"{x['olvasat_leiro']} (másodlagos)"
                    o.append(f"| {nev} | {ag} | {f(x['delta'])} | {iv(x['ci95'])} | {fp(x['p'], res['reps'])} | {ol} | {f(x['aurc_delta'])} | "
                             f"{iv(x['aurc_ci95'])} |")
        o += ["", "Nyelvenként (pontbecslés, AUROC K1(b) / K1(a)): " + "; ".join(
            f"{ny}: " + ", ".join(f"{k} {f(v['K1b_auroc'])} / {f(v['K1a_auroc'])}" for k, v in X.items())
            for ny, X in F["nyelvenkent"].items()) + "."]
        if "jelfajta" in F:
            o.append("A jel fajtája szerint (leíró; pontbecslés, AUROC K1(b) / K1(a); zárójelben K1(b) rossz opció / (b) SELECT): "
                     + "; ".join(f"{x}: " + ", ".join(f"{k} {f(v['K1b_auroc'])} / {f(v['K1a_auroc'])}" for k, v in J["karok"].items())
                                 + f" ({J['esemeny']['K1b']['pozitiv']} / {J['esemeny']['K1b']['halmaz']})"
                                 for x, J in F["jelfajta"].items()) + ".")
        o += [
            f"Az (a) döntései a diagnózison: {', '.join(f'{k} {v}' for k, v in F['a_dontesek'].items())}; Y-arány "
            f"{f(100 * F['a_y_arany'], 1)}%."]
        if "a_lezart_tau_felett" in F:
            o.append("Az (a)-ból τ fölött lezárt arány: " + ", ".join(f"{k} {f(100 * v, 1)}%" for k, v in F["a_lezart_tau_felett"].items()) + ".")
        o.append(f"Brier / ECE ({F['kalibracio']}): " + "; ".join(
            f"{k}: " + ", ".join(f"{ag} {f(v[ag]['brier'])} / {f(v[ag]['ece'])}" for ag in AGAK) for k, v in F["brier_ece"].items()) + ".")
        o.append("")
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csalad", action="append", required=True,
                    help="<család>:<pontozott szelet .json>:<items könyvtár>:<lánc könyvtár>[:<orákulum-lánc könyvtár>]")
    ap.add_argument("--cal", action="append", default=[], help="<család>:<a friss CAL pontozott szelete> (kalibráció)")
    ap.add_argument("--tau", help="a g5_k3_08 json-ja, vagy {család: {kar: τ vagy [τ seedenként]}}")
    ap.add_argument("--fo-par", default="L-RN,L-S")
    ap.add_argument("--fo-csalad", default=L.SZAB)
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--ellenoriz", action="append", default=[],
                    help="a pilot `g1b_ert08` json-ja (több is): az L-S AUROC-ja az ő itemhalmazán egyezzen")
    ap.add_argument("--cimke", default="G1 pilot, fejlesztési szám")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    Cs = {}
    for s in a.csalad:
        fam, pont, items, lanc, *ora = s.split(":")
        Cs[fam] = Csalad(fam, EXP / pont, EXP / items, EXP / lanc, EXP / ora[0] if ora else None)
    cal = {}
    for s in a.cal:
        fam, p = s.split(":")
        cal[fam] = json.loads((EXP / p).read_text())
    tau = json.loads((EXP / a.tau).read_text()) if a.tau else None
    if tau and "csaladok" in tau:  # a `g5_k3_08` kimenete: családonként a karok τ-i a CAL-on (seedenként; munkapont nélkül None)
        tau = {fam: {k: [math.inf if t is None else t for t in v] for k, v in F["tau"].items()} for fam, F in tau["csaladok"].items()}
    fo = tuple(a.fo_par.split(",")) if a.fo_par else None
    res = elemez(Cs, fo, a.fo_csalad, a.reps, a.seed, cal, tau)
    if a.ellenoriz:  # a pontszám iránya és az AUROC: az L-S a `g1b_ert08` itemhalmazán (az ő kapujával) annak számát adja
        gs = [json.loads((EXP / x).read_text()) for x in a.ellenoriz]
        res["ellenorzes"] = {}
        for fam, C in Cs.items():
            g = next((x for x in gs if fam in x.get("csaladok", {})), None)
            if g is None:
                continue
            G = g["csaladok"][fam]
            alap = np.isin(np.array(C.ids), list(G["itemek"]))
            ag = C.agak(alap)
            res["ellenorzes"][fam] = {x: {"g5_a_g1b_halmazan": auroc(-C.pont["L-S"][0][ag[x][0]], ag[x][1][ag[x][0]]),
                                          "g1b": G["bizonyossag"][x]["auroc"], "g1b_itemek": len(G["itemek"]),
                                          "g5_itemek_a_szeletben": int(alap.sum())} for x in AGAK}
        print(json.dumps(res["ellenorzes"], ensure_ascii=False, indent=1))
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "g5_k1.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "g5_k1.md").write_text(lap(res, a.cimke), encoding="utf-8")
    print(lap(res, a.cimke))


if __name__ == "__main__":
    main()
