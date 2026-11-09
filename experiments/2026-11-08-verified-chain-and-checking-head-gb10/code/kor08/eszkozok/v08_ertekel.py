"""08B fejlesztési próba — a lépcsők Dani vak címkéihez mérve (D10, Dani 11-06: fő végpont a lezárások hibaaránya, cél ≤ 2%; az új lezárások száma leíró). Helyben fut, csak aggregátum kerül ki.
**Ez a 262 ismert tétel: fejlesztési szám, nem megerősítő.** A τ-t itt választjuk ki a friss mintához; a bankon a G5-ben a láncos karoknak nincs munkapontja, ezért itt nincs előre adott τ.

Hatókör: a 262 tétel, a K / N és a több számlás nélkül. Lezárás: a lánc kötése; a modell SELECT-je vagy X-e a τ fölött. Helyes: a címke ugyanaz (MATCH: ugyanaz a számla, X: NO_MATCH). Az M és az O címke
lezárása hiba. Y és Z nem lezárás. A termék „kötött, címke M” tételei nem hibák (a termék több adatot látott), ezért a termék sora leíró.
Iker-kapu (leíró): a modell SELECT-je nem zár le, ha legalább két jelölt összege pontos.

  python3 kor08/eszkozok/v08_ertekel.py --pont <pontoz.json> --lanc <lanc.jsonl> --cimkek kor07/adat/b7/cimkek.json --out kor08/eredmenyek/V
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor07/eszkozok")]
import b7_07 as B  # noqa: E402

CEL, REPS, SEED = 0.02, 10000, 20261106
HELYES = {"NONE": "NO_MATCH", "MISSING": "MISSING_DATA", "OOS": "OUT_OF_SCOPE"}


def sz(x: float, n: int = 1) -> str:
    return f"{x:.{n}f}".replace(".", ",")


def auroc(jo: np.ndarray, rossz: np.ndarray) -> float:
    if not len(jo) or not len(rossz):
        return float("nan")
    d = jo[:, None] - rossz[None, :]
    return float(((d > 0) + 0.5 * (d == 0)).mean())


class Adat:
    def __init__(self, a):
        self.doc = json.loads(Path(a.pont).read_text())["keret4"]
        self.lanc = {r["id"]: r for r in map(json.loads, Path(a.lanc).read_text(encoding="utf-8").splitlines())}
        self.meta = json.loads((B.B7 / "meta.json").read_text())
        self.C = B.cimkek(a.cimkek)
        self.E = [i for i, c in self.C.items() if not c["kihagy"] and not c["tobb_szamla"]]
        self.kl = {i: self.meta[i]["klaszter"] for i in self.meta}
        self.megoldatlan = {i for i, m in self.meta.items() if m["csoport"] == "nem_egyeztetett" and not m["kategoria"]}
        self.D = self.doc["dontes"]
        self.pont: dict[str, dict] = {}
        p: dict = defaultdict(list)
        for k, v in self.doc["pontszam"].items():
            p[k.split("|")[0]].append(np.asarray(v, float))
        for arm, vs in p.items():
            self.pont[arm] = dict(zip(self.doc["ids"], np.mean(vs, axis=0)))

    def helyes_d(self, i: str) -> bool:
        d, c = self.D[i], self.C[i]
        if d["kind"] == "SELECT":
            return c["allapot"] == "MATCH" and d["cand"] == c["gold"]
        return c["allapot"] == HELYES[d["kind"]]

    def helyes_kotes(self, i: str) -> bool:
        return self.C[i]["allapot"] == "MATCH" and self.lanc[i]["kotes"] == self.C[i]["gold"]

    def iker(self, i: str) -> bool:
        return len(self.lanc[i].get("szamitott", {}).get("osszegben", [])) >= 2


def lezartak(A: Adat, arm: str | None, tau: float, kapu: bool = False) -> tuple[list[str], list[str]]:
    """(lezárt id-k, ebből hibás) a lánc kötéseivel és a modell τ fölötti SELECT / X döntéseivel."""
    lez, hib = [], []
    for i in A.E:
        r = A.lanc.get(i)
        if r and r["kimenet"] == "kotes":
            lez.append(i)
            hib += [] if A.helyes_kotes(i) else [i]
        elif arm and i in A.pont[arm] and A.D[i]["kind"] in ("SELECT", "NONE") and A.pont[arm][i] >= tau:
            if kapu and A.D[i]["kind"] == "SELECT" and A.iker(i):
                continue
            lez.append(i)
            hib += [] if A.helyes_d(i) else [i]
    return lez, hib


def ci(A: Adat, lez: list[str], hib: list[str], rng: np.random.Generator) -> tuple[float, float]:
    kl = defaultdict(lambda: [0, 0])
    h = set(hib)
    for i in lez:
        kl[A.kl[i]][0] += 1
        kl[A.kl[i]][1] += i in h
    if not kl:
        return float("nan"), float("nan")
    v = np.array(list(kl.values()), float)
    r = rng.integers(0, len(v), (REPS, len(v)))
    s = v[r].sum(axis=1)
    q = s[:, 1] / np.maximum(s[:, 0], 1)
    return float(np.quantile(q, 0.025)), float(np.quantile(q, 0.975))


def legjobb_tau(A: Adat, arm: str, kapu: bool) -> float | None:
    """A legtöbb lezárást adó τ, ahol a hibaarány ≤ 2% (a fejlesztési mintán választva: optimista)."""
    best, bt = -1, None
    for t in sorted({A.pont[arm][i] for i in A.pont[arm]}):
        lez, hib = lezartak(A, arm, t, kapu)
        if lez and len(hib) / len(lez) <= CEL and len(lez) > best:
            best, bt = len(lez), t
    return bt


def sor(A: Adat, nev: str, arm: str | None, tau: float, kapu: bool, rng) -> tuple[str, dict]:
    lez, hib = lezartak(A, arm, tau, kapu)
    lo, hi = ci(A, lez, hib, rng)
    uj = [i for i in lez if i in A.megoldatlan]
    ujh = [i for i in uj if i in set(hib)]
    r = {"lezart": len(lez), "hibas": len(hib), "arany": len(hib) / max(len(lez), 1), "ci95": [lo, hi], "uj": len(uj), "uj_hibas": len(ujh),
         "hiba_cimke": dict(Counter(A.C[i]["allapot"] for i in hib)), "tau": None if tau == float("inf") else tau}
    return (f"| {nev} | {len(lez)} | {len(hib)} | {sz(100 * r['arany'])}% [{sz(100 * lo)}; {sz(100 * hi)}] | {len(uj)} / {len(ujh)} | {dict(r['hiba_cimke']) or '–'} |", r)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pont", required=True)
    ap.add_argument("--lanc", required=True)
    ap.add_argument("--cimkek", default="kor07/adat/b7/cimkek.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A = Adat(a)
    rng = np.random.default_rng(SEED)
    res: dict = {"n_tetel": len(A.meta), "hatokor": len(A.E), "cimkek": dict(Counter(A.C[i]["allapot"] for i in A.E)), "lanc_kimenet": dict(Counter(r["kimenet"] for r in A.lanc.values()))}
    sz_ = [r.get("szamitott", {}) for r in A.lanc.values()]
    res["fedes"] = {"kozvetlen_egy": sum(len(s.get("kozvetlen", [])) == 1 for s in sz_), "kinyert_egy": sum(len(s.get("talalt", [])) == 1 for s in sz_),
                    "elvetett_mezo": sum(len(r.get("elvetett", [])) for r in A.lanc.values()), "kizart_jelolt": sum(len(r["kizart"]) for r in A.lanc.values())}
    keszt = Counter((A.C[i]["allapot"], {"SELECT": "SELECT", "NONE": "X", "MISSING": "Y", "OOS": "Z"}[A.D[i]["kind"]]) for i in A.doc["ids"] if i in set(A.E))
    res["dontesek"] = {f"{k[0]}|{k[1]}": v for k, v in sorted(keszt.items())}
    o = ["# 08B fejlesztési próba: a lépcsők a 262 tételen", "", "**Fejlesztési szám, nem megerősítő:** a minta és a címkék ismertek, a τ itt választott, ezért a modell-lépcsők hibaaránya optimista. Csak aggregátum.", "",
         f"Hatókör {res['hatokor']} / {res['n_tetel']} tétel (K / N és több számlás nélkül). Címkék: {res['cimkek']}. A lánc kimenete: {res['lanc_kimenet']}.", "",
         f"Hivatkozás: a közleményben pontosan egy jelölt számlaszáma {res['fedes']['kozvetlen_egy']} tételen, a kinyerés ebből {res['fedes']['kinyert_egy']}-et hozott; eldobott mező {res['fedes']['elvetett_mezo']}, kizárt jelölt {res['fedes']['kizart_jelolt']}.", "",
         "| lépcső | lezárt | hibás | hibaarány [95%] | új a termékhez / ebből hibás | a hibák címkéje |", "|---|---|---|---|---|---|"]
    res["lepcsok"] = {}
    s, r = sor(A, "lánc (csak kötés)", None, float("inf"), False, rng)
    o.append(s)
    res["lepcsok"]["lánc"] = r
    for arm in A.pont:
        for kapu in (False, True):
            t = legjobb_tau(A, arm, kapu)
            nev = f"lánc + {arm}{' + iker-kapu' if kapu else ''}"
            if t is None:
                o.append(f"| {nev} | nincs ≤ 2%-os munkapont | | | | |")
                res["lepcsok"][nev] = None
                continue
            s, r = sor(A, nev, arm, t, kapu, rng)
            o.append(s)
            res["lepcsok"][nev] = r
    o += ["", "**A modell döntései a címkék szerint (a modellhez ment tételek):**", "", "| címke | döntés | n |", "|---|---|---|"] + [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(keszt.items())]
    sel = [i for i in A.doc["ids"] if i in set(A.E) and A.D[i]["kind"] == "SELECT"]
    o += ["", "**A SELECT-ek rangsora (helyes a nem helyes ellen):**", "", "| kar | AUROC | helyes / nem helyes |", "|---|---|---|"]
    res["auroc"] = {}
    for arm in A.pont:
        j = np.array([A.pont[arm][i] for i in sel if A.helyes_d(i)])
        h = np.array([A.pont[arm][i] for i in sel if not A.helyes_d(i)])
        res["auroc"][arm] = auroc(j, h)
        o.append(f"| {arm} | {sz(res['auroc'][arm], 3)} | {len(j)} / {len(h)} |")
    d = EXP / a.out
    d.mkdir(parents=True, exist_ok=True)
    (d / "v_ertekeles.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "v_ertekeles.md").write_text("\n".join(o) + "\n", encoding="utf-8")
    print("\n".join(o))


if __name__ == "__main__":
    main()
