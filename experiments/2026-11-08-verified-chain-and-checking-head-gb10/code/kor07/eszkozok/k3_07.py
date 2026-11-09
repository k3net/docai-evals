"""07-es kör — a K3 elemzője (07-runbook 1. „K3”, 3.3, 4., D6, D11, D23, D24): a mentett fejek a végső diagnosztikai
mintán. A kiolvasás előtt rögzítve (`rogzit07k3`, `kor07/rogzites/k3/`); a pecsét a `rogzit07k3 nyit`-tal nyílik.

Bemenet: `<be>/diag_<család>.json` (a `b1rel07k3 pontoz` kimenete, mindkét keret döntéseivel és pontszámaival), a
diagnosztikai itemek (sabloncsoport, nyelv) és a terv (változat, csali). Minden item MATCH: a helyes válasz a gold
opció SELECT-je, a nem-SELECT válasz is hiba.

Mérők karonként a SELECT-döntéseken (egy kereten belül a karok ugyanazokat a döntéseket rangsorolják):
  - a rossz opció felismerése: AUROC, annak a valószínűsége, hogy egy helyes SELECT pontszáma nagyobb egy rosszénál
    (holtversenyben fél);
  - SELECT-AURC: a kockázat–lefedettség görbe alatti terület a SELECT-eken (kisebb a jobb);
  - leíróan: a rossz opcióválasztások és a nem-SELECT válaszok száma, a rossz opcióból a csali, nyelvenként és
    változatonként, a karok AUROC-ja ugyanígy (pontbecslés).
Karok: négyállapotú keret B1-4S, B1-4R, B1-4LR (a K3 karjai), leíróan B1-4R0; 06-os keret leíróan B1-S, B1-R, B1-LR,
B1-R0. A B1-4R, B1-4R0, B1-R és B1-R0 a három seed (17, 42, 73) mérőinek átlaga replikánként (D24).
Összevetések: B1-4R − B1-4S, B1-4LR − B1-4S, B1-4R − B1-4LR (négyállapotú), leíróan B1-R − B1-S (06-os).
Statisztika: sabloncsoportos klaszteres bootstrap (D23) családonként, a két keret ugyanazokkal a sablonokkal
replikánként, 10 000 ismétlés, seed 20261101; a fő sor a három család egyenlő súlyú átlaga (replikánként), a családok
sorai leíróak; 95%-os percentilis-intervallum, kétoldali bootstrap-p. Ha egy replikában egy mérő nem értelmezett (nincs
helyes vagy nincs rossz SELECT), az a replika abból a mérőből kimarad, a számuk közölve.
Olvasat (előre rögzítve; a K3 leíró, semminek nem feltétele):
  - egy kar felismeri a tévedést, ha az átlagos AUROC alsó határa > 0,5; fordítva rangsorol, ha a felső < 0,5;
  - egy pár javít, ha a ΔAUROC alsó határa > 0 (SELECT-AURC-ban, ahol a kisebb a jobb: a Δ felső határa < 0); ront,
    ha fordítva; egyébként a különbség nem kimutatható.

  python3 kor07/eszkozok/k3_07.py elemez --be cache/k07/k3 --out kor07/eredmenyek/K3
  python3 kor07/eszkozok/k3_07.py proba --be cache/k07/k3_proba/pontoz    # a 3. kör nyitott mintáján: csak darabszám
  python3 kor07/eszkozok/k3_07.py onteszt                                 # mesterséges adaton
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import warnings
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path.insert(0, str(HERE))
import elemzes07 as E  # noqa: E402

CSALADOK = E.CSALADOK
SEEDS = E.SEEDS
REPS, SEED = 10_000, 20261101
KAROK = {"keret4": {"B1-4S": ("B1-4S",), "B1-4R": tuple(f"B1-4R|{s}" for s in SEEDS), "B1-4LR": ("B1-4LR",),
                    "B1-4R0": tuple(f"B1-4R0|{s}" for s in SEEDS)},
         "keret2": {"B1-S": ("B1-S",), "B1-R": tuple(f"B1-R|{s}" for s in SEEDS), "B1-LR": ("B1-LR",),
                    "B1-R0": tuple(f"B1-R0|{s}" for s in SEEDS)}}
FO = ("B1-4S", "B1-4R", "B1-4LR")
PAROK = {"keret4": (("B1-4R", "B1-4S"), ("B1-4LR", "B1-4S"), ("B1-4R", "B1-4LR")), "keret2": (("B1-R", "B1-S"),)}
MEROK = ("auroc", "select_aurc")
FORRAS = {"diag": {"adat": EXP / "kor07/adat/diag", "sablon": EXP / "kor07/adat/f2/sablon", "elotag": "diag"},
          "proba": {"adat": EXP / "kor07/adat/nehez3", "sablon": EXP / "kor06/adat/f2/sablon", "elotag": "proba"}}


# --- mérők -------------------------------------------------------------------------------------------------------------

def auroc(q: np.ndarray, c: np.ndarray) -> float:
    n1 = int(c.sum())
    n0 = len(c) - n1
    if n1 == 0 or n0 == 0:
        return math.nan
    r = rankdata(q)
    return float((r[c].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def merok(q: np.ndarray, cor: np.ndarray, sel: np.ndarray, idx: np.ndarray) -> dict[str, float]:
    s = idx[sel[idx]]
    if len(s) == 0:
        return {"auroc": math.nan, "select_aurc": math.nan}
    return {"auroc": auroc(q[s], cor[s]), "select_aurc": E.aurc(q[s], cor[s])}


def atlag(xs: list[float]) -> float:
    xs = [x for x in xs if not math.isnan(x)]
    return float(np.mean(xs)) if xs else math.nan


@dataclass
class Keret:
    ids: list[str]
    sel: np.ndarray       # SELECT-döntés
    cor: np.ndarray       # SELECT a gold opción
    csali: np.ndarray     # SELECT a csalin
    grp: np.ndarray       # sabloncsoport
    lang: np.ndarray
    valt: np.ndarray
    sc: dict[str, np.ndarray]

    def kar(self, runs: tuple[str, ...], idx: np.ndarray) -> dict[str, float]:
        ms = [merok(self.sc[r], self.cor, self.sel, idx) for r in runs]
        return {m: atlag([x[m] for x in ms]) for m in MEROK}


# --- betöltés ----------------------------------------------------------------------------------------------------------

def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def csalik(forras: str, fam: str) -> dict[str, tuple[str, str]]:
    """item-id → (változat, a csali opció-id-je a `final` sorrendjében), a `b14_07k3.terv_meta` szabályával."""
    F = FORRAS[forras]
    pontok = {}
    if fam == "szabaly.koltsegelszamolas":
        pontok = {s["sablon_id"]: s["pontok"] for s in jsonl(F["sablon"] / f"{fam}.jsonl")}
    out = {}
    for p in jsonl(F["adat"] / "terv" / f"{fam}.jsonl"):
        sids, g = [o["sid"] for o in p["opciok"]], p["gold_sid"]
        if fam == "penzugy.bankparositas":
            cs = "s_csali"
        elif fam == "szabaly.koltsegelszamolas":
            pts = pontok[p["sablon_id"]]
            tipus = next(x["tipus"] for x in pts if x["id"] == g)
            cs = next(x["id"] for x in pts if x["tipus"] == tipus and x["id"] != g)
        else:
            cs = g[:-1] + str(1 - int(g[-1]))
        out[p["group_id"]] = (p["nehez"]["valt"], f"o{sids.index(cs) + 1}")
    return out


def betolt(be: Path, forras: str, fam: str) -> dict[str, Keret]:
    F = FORRAS[forras]
    doc = json.loads((be / f"{F['elotag']}_{fam}.json").read_text())
    items = {it["id"]: it for it in jsonl(F["adat"] / "items" / f"{fam}.jsonl")}
    cs = csalik(forras, fam)
    out = {}
    for kr in ("keret4", "keret2"):
        ids, d = doc[kr]["ids"], doc[kr]["dontes"]
        if any(items[i]["content_state"] != "MATCH" for i in ids):
            raise SystemExit(f"{fam}/{kr}: nem MATCH item a diagnosztikai mintában")
        sel = np.array([d[i]["kind"] == "SELECT" for i in ids], bool)
        cor = np.array([d[i]["kind"] == "SELECT" and d[i]["cand"] == items[i]["gold"] for i in ids], bool)
        if not np.array_equal(cor, np.array([bool(d[i]["helyes"]) for i in ids])):
            raise SystemExit(f"{fam}/{kr}: a pontozó helyessége eltér a gold opciótól")
        sc = {r: np.array(doc[kr]["pontszam"][r], float) for runs in KAROK[kr].values() for r in runs}
        if any(len(v) != len(ids) for v in sc.values()):
            raise SystemExit(f"{fam}/{kr}: a pontszámsor hossza eltér")
        out[kr] = Keret(ids=ids, sel=sel, cor=cor,
                        csali=np.array([d[i]["kind"] == "SELECT" and d[i]["cand"] == cs[i][1] for i in ids], bool),
                        grp=np.array([items[i]["template_group_id"] for i in ids]),
                        lang=np.array([items[i]["lang"] for i in ids]), valt=np.array([cs[i][0] for i in ids]), sc=sc)
    return out


# --- családonként: pontbecslés, bontás, bootstrap ----------------------------------------------------------------------

def szamok(k: Keret, m: np.ndarray) -> dict:
    return {"n": int(m.sum()), "select": int((k.sel & m).sum()), "rossz_opcio": int((k.sel & ~k.cor & m).sum()),
            "ebbol_csali": int((k.csali & m).sum()), "nem_select": int((~k.sel & m).sum())}


def csalad(K: dict[str, Keret], reps: int, rng: np.random.Generator) -> dict:
    tpl = sorted(set(K["keret4"].grp) | set(K["keret2"].grp))
    tagok = {kr: [np.where(k.grp == t)[0] for t in tpl] for kr, k in K.items()}
    res: dict = {"sablon": len(tpl)}
    for kr, k in K.items():
        n = len(k.ids)
        minden = np.ones(n, bool)
        bontas = {"összes": minden, **{f"nyelv {lg}": k.lang == lg for lg in ("hu", "en")},
                  **{f"változat {v}": k.valt == v for v in sorted(set(k.valt))}}
        res[kr] = {"szamok": {b: szamok(k, m) for b, m in bontas.items()},
                   "pont": {arm: k.kar(runs, np.arange(n)) for arm, runs in KAROK[kr].items()},
                   "pont_bontas": {b: {arm: k.kar(runs, np.where(m)[0])["auroc"] for arm, runs in KAROK[kr].items()}
                                   for b, m in bontas.items() if b != "összes"},
                   "boot": {arm: {m: np.empty(reps) for m in MEROK} for arm in KAROK[kr]}}
    for r in range(reps):
        tb = rng.integers(0, len(tpl), len(tpl))
        for kr, k in K.items():
            idx = np.concatenate([tagok[kr][t] for t in tb])
            for arm, runs in KAROK[kr].items():
                v = k.kar(runs, idx)
                for m in MEROK:
                    res[kr]["boot"][arm][m][r] = v[m]
    return res


# --- összegzés ---------------------------------------------------------------------------------------------------------

def becsles(pont: float, boot: np.ndarray) -> dict:
    return {"pont": pont, "ci95": E.ci(boot), "p": E.p_ketoldali(boot), "nem_ertelmezett": int(np.isnan(boot).sum())}


def olvasat_kar(c: dict) -> str:
    lo, hi = c["ci95"]
    return "felismeri a tévedést" if lo > 0.5 else ("fordítva rangsorol" if hi < 0.5 else "nem különbözik a véletlentől")


def olvasat_par(c: dict, m: str) -> str:
    lo, hi = c["ci95"]
    jobb, rosszabb = (lo > 0, hi < 0) if m == "auroc" else (hi < 0, lo > 0)
    return "javít" if jobb else ("ront" if rosszabb else "nem kimutatható")


def osszegez(R: dict[str, dict]) -> dict:
    out: dict = {"csaladok": {}, "atlag": {}}
    for kr in KAROK:
        for fam, r in R.items():
            c = out["csaladok"].setdefault(fam, {"sablon": r["sablon"]})
            c[kr] = {"szamok": r[kr]["szamok"], "pont_bontas": r[kr]["pont_bontas"],
                     "karok": {arm: {m: becsles(r[kr]["pont"][arm][m], r[kr]["boot"][arm][m]) for m in MEROK}
                               for arm in KAROK[kr]},
                     "parok": {f"{a} − {b}": {m: becsles(r[kr]["pont"][a][m] - r[kr]["pont"][b][m],
                                                         r[kr]["boot"][a][m] - r[kr]["boot"][b][m]) for m in MEROK}
                               for a, b in PAROK[kr]}}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            av = {arm: {m: np.mean([R[f][kr]["boot"][arm][m] for f in R], axis=0) for m in MEROK} for arm in KAROK[kr]}
        ap = {arm: {m: float(np.mean([R[f][kr]["pont"][arm][m] for f in R])) for m in MEROK} for arm in KAROK[kr]}
        out["atlag"][kr] = {
            "karok": {arm: {m: becsles(ap[arm][m], av[arm][m]) for m in MEROK} for arm in KAROK[kr]},
            "parok": {f"{a} − {b}": {m: becsles(ap[a][m] - ap[b][m], av[a][m] - av[b][m]) for m in MEROK}
                      for a, b in PAROK[kr]}}
        for arm, c in out["atlag"][kr]["karok"].items():
            c["olvasat"] = olvasat_kar(c["auroc"])
        for p, c in out["atlag"][kr]["parok"].items():
            c["olvasat"] = {m: olvasat_par(c[m], m) for m in MEROK}
    return out


def f(x: float, d: int = 3) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def c95(c: dict, d: int = 3) -> str:
    return f"{f(c['pont'], d)} [{f(c['ci95'][0], d)}; {f(c['ci95'][1], d)}]"


def lap(res: dict) -> str:
    L = ["# 07 K3 — a fejek a végső diagnosztikai mintán", "",
         f"Rögzített elemző (`kor07/eszkozok/k3_07.py`, `kor07/rogzites/k3/`); {res['reps']} ismétlés, seed {res['seed']}. "
         "Minden item MATCH. A rossz opció felismerése: AUROC a SELECT-döntéseken (1 = minden helyes SELECT a rosszak "
         "fölött, 0,5 = véletlen, 0 = fordított). SELECT-AURC: kisebb a jobb. A fő sor a három család egyenlő súlyú "
         "átlaga; a családok sorai leíróak. Szögletes zárójelben a 95%-os bootstrap-intervallum.", ""]
    for kr, cim in (("keret4", "Négyállapotú keret (a K3 karjai: B1-4S, B1-4R, B1-4LR)"), ("keret2", "06-os keret (leíró)")):
        L += [f"## {cim}", "", "### Karok, a három család átlaga", "",
              "| kar | AUROC (rossz opció) | olvasat | SELECT-AURC |", "|---|---|---|---|"]
        for arm, c in res["atlag"][kr]["karok"].items():
            L.append(f"| {arm}{'' if arm in FO or kr == 'keret2' else ' (leíró)'} | {c95(c['auroc'])} | {c['olvasat']} | "
                     f"{c95(c['select_aurc'], 4)} |")
        L += ["", "### Párok, a három család átlaga", "",
              "| pár | ΔAUROC | olvasat | ΔSELECT-AURC | olvasat |", "|---|---|---|---|---|"]
        for p, c in res["atlag"][kr]["parok"].items():
            L.append(f"| {p} | {c95(c['auroc'])} | {c['olvasat']['auroc']} | {c95(c['select_aurc'], 4)} | "
                     f"{c['olvasat']['select_aurc']} |")
        L += ["", "### Családonként (leíró)", "",
              "| család | sablon | item | SELECT | rossz opció (ebből csali) | nem-SELECT | "
              + " | ".join(f"{a} AUROC" for a in KAROK[kr]) + " | " + " | ".join(f"Δ {p}" for p in res["atlag"][kr]["parok"]) + " |",
              "|---|---|---|---|---|---|" + "---|" * (len(KAROK[kr]) + len(PAROK[kr]))]
        for fam, c in res["csaladok"].items():
            s = c[kr]["szamok"]["összes"]
            L.append(f"| {fam} | {c['sablon']} | {s['n']} | {s['select']} | {s['rossz_opcio']} ({s['ebbol_csali']}) | "
                     f"{s['nem_select']} | " + " | ".join(c95(c[kr]["karok"][a]["auroc"]) for a in KAROK[kr]) + " | "
                     + " | ".join(c95(c[kr]["parok"][p]["auroc"]) for p in c[kr]["parok"]) + " |")
        L += ["", "### Bontás (pontbecslés, leíró)", "",
              "| család | bontás | item | rossz opció (ebből csali) | nem-SELECT | " + " | ".join(f"{a} AUROC" for a in KAROK[kr]) + " |",
              "|---|---|---|---|---|" + "---|" * len(KAROK[kr])]
        for fam, c in res["csaladok"].items():
            for b, pb in c[kr]["pont_bontas"].items():
                s = c[kr]["szamok"][b]
                L.append(f"| {fam} | {b} | {s['n']} | {s['rossz_opcio']} ({s['ebbol_csali']}) | {s['nem_select']} | "
                         + " | ".join(f(pb[a]) for a in KAROK[kr]) + " |")
        ne = {f"{fam}/{arm}": c[kr]["karok"][arm]["auroc"]["nem_ertelmezett"] for fam, c in res["csaladok"].items()
              for arm in KAROK[kr] if c[kr]["karok"][arm]["auroc"]["nem_ertelmezett"]}
        L += ["", f"Nem értelmezett AUROC-replikák: {ne if ne else 'nincs'}.", ""]
    return "\n".join(L)


# --- parancsok ---------------------------------------------------------------------------------------------------------

def elemez(a) -> None:
    rng = np.random.default_rng(SEED)
    R = {}
    for fam in CSALADOK:
        R[fam] = csalad(betolt(Path(a.be), "diag", fam), a.reps, rng)
        print(f"{fam} kész", flush=True)
    res = {"reps": a.reps, "seed": SEED, **osszegez(R)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "k3.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float) + "\n", encoding="utf-8")
    (out / "k3.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


def proba(a) -> None:
    """A teljes út a 3. kör nyitott mintáján, kevés ismétléssel; csak darabszám és szerkezet kerül ki, mérőérték nem."""
    rng = np.random.default_rng(SEED)
    R = {}
    for fam in CSALADOK:
        K = betolt(Path(a.be), "proba", fam)
        for kr, k in K.items():
            print(f"{fam}/{kr}: {len(k.ids)} item, {int(k.sel.sum())} SELECT, sablon {len(set(k.grp))}, "
                  f"pontszámsor {len(k.sc)}, változat {dict(Counter(map(str, k.valt)))}")
        R[fam] = csalad(K, 20, rng)
    res = {"reps": 20, "seed": SEED, **osszegez(R)}
    lap(res)
    json.dumps(res, default=float)
    print("a próba végigfutott (20 ismétlés: összegzés, lap, JSON); mérőértéket a próba nem ír ki")


def onteszt(_a) -> None:
    rng = np.random.default_rng(1)
    hibak = []
    for _ in range(200):  # AUROC: a páronkénti definícióval, holtversennyel
        n = int(rng.integers(5, 30))
        q, c = rng.integers(0, 4, n).astype(float), rng.random(n) < 0.5
        if c.all() or not c.any():
            continue
        br = np.mean([1.0 if a > b else 0.5 if a == b else 0.0 for a in q[c] for b in q[~c]])
        if abs(auroc(q, c) - br) > 1e-12:
            hibak.append("auroc ≠ páronkénti")
            break
    n, tpl = 240, np.repeat(np.arange(24), 10)
    cor = rng.random(n) < 0.4
    sel = np.ones(n, bool)
    sel[:12] = False
    cor &= sel
    jo, vel = cor + 0.01 * rng.random(n), rng.random(n)

    def keret(sc: dict) -> Keret:
        return Keret(ids=[str(i) for i in range(n)], sel=sel, cor=cor, csali=sel & ~cor, grp=tpl.astype(str),
                     lang=np.where(tpl % 2 == 0, "hu", "en"), valt=np.array(["v"] * n), sc=sc)
    k4 = keret({"B1-4S": vel, "B1-4LR": vel, **{f"B1-4R|{s}": jo for s in SEEDS}, **{f"B1-4R0|{s}": vel for s in SEEDS}})
    k2 = keret({"B1-S": 1 - jo, "B1-LR": vel, **{f"B1-R|{s}": jo for s in SEEDS}, **{f"B1-R0|{s}": vel for s in SEEDS}})
    R = {fam: csalad({"keret4": k4, "keret2": k2}, 300, np.random.default_rng(7)) for fam in CSALADOK}
    res = osszegez(R)
    A = res["atlag"]
    if abs(A["keret4"]["karok"]["B1-4R"]["auroc"]["pont"] - 1.0) > 1e-12:
        hibak.append("a tökéletes kar AUROC-ja nem 1")
    if A["keret4"]["karok"]["B1-4R"]["olvasat"] != "felismeri a tévedést":
        hibak.append("a tökéletes kar olvasata")
    if A["keret2"]["karok"]["B1-S"]["olvasat"] != "fordítva rangsorol":
        hibak.append("a fordított kar olvasata")
    if A["keret4"]["parok"]["B1-4R − B1-4S"]["olvasat"] != {"auroc": "javít", "select_aurc": "javít"}:
        hibak.append(f"a javító pár olvasata: {A['keret4']['parok']['B1-4R − B1-4S']['olvasat']}")
    d = A["keret4"]["parok"]["B1-4LR − B1-4S"]["auroc"]
    if d["pont"] != 0 or d["ci95"] != [0.0, 0.0]:
        hibak.append("azonos karok különbsége nem 0")
    sa = res["csaladok"]["penzugy.bankparositas"]["keret4"]["karok"]["B1-4R"]["select_aurc"]["pont"]
    if abs(sa - E.aurc_opt(cor[sel])) > 1e-12:
        hibak.append("a tökéletes kar SELECT-AURC-ja nem az optimum")
    lap({"reps": 300, "seed": 7, **res})
    print("önteszt: " + ("rendben" if not hibak else "HIBA: " + "; ".join(hibak)))
    raise SystemExit(1 if hibak else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("elemez")
    e.add_argument("--be", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--reps", type=int, default=REPS)
    p = sub.add_parser("proba")
    p.add_argument("--be", required=True)
    sub.add_parser("onteszt")
    a = ap.parse_args()
    {"elemez": elemez, "proba": proba, "onteszt": onteszt}[a.cmd](a)


if __name__ == "__main__":
    main()
