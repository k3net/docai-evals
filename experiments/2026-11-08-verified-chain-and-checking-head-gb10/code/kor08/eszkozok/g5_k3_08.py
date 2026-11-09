"""08 G5 — K3: a gyakorlati eredmény a természetes összetételű friss teszten, és a K3-X (G1-rögzítés 1., 4.1, 7., 8.).

**A rendszer** a lánc + az alany döntése + a kar megbízhatósága. Lezárt: a lánc automatikus kötése (küszöb nélkül, D4) és
a modell τ fölötti SELECT-je és X-e (07 D9); az emberhez küldött tétel, az Y, a Z és a τ alatti nem lezárt. A helyesség az
eredeti itemhez (`g1_dontes08.helyes`).
**A τ** karonként és seedenként a CAL-on, a 07 D9 szabályával (`elemzes07.tau_of`: a legnagyobb elfogadott halmaz, ahol a
lezárás precizitásának egyoldali 95%-os CP-alsó határa ≥ 0,95, és legalább 200 lezárt), **csak a modell lezárható
döntésein** (a modellhez jutott tételek SELECT-je és X-e); a lánc kötései ezután adódnak a lezártakhoz, így a pontos
kötések nem engednek több modellhibát. Munkapont nélkül a kar a modellből semmit nem zár le (a kötések maradnak).
**A TESZT-en:** hasznos lefedettség = helyesen lezárt / összes; lezárási hibaarány = hibásan lezárt / összes lezárt (a
kötésekkel együtt); a lánc kimeneteinek eloszlása saját hibaarányukkal; a hibafeltétel (07 D10): a lezárási hibaarány
pontbecslése ≤ 0,05, „bizonytalan”, ha a felső határ 0,05 fölött van. ΔAURC a modell döntésein (szigorú helyesség).
**Ugyanezen itemeken** a 07 B1-4S és B1-4R lánc nélkül (a 07 pontozott szeletei), ugyanazzal a τ-szabállyal.
**Bootstrap (8.):** sabloncsoportos, a CAL-on és a TESZT-en külön; a τ replikánként **kizárólag az újramintázott CAL-on**
választódik újra, és a TESZT-replikán alkalmazódik; a seedek mérőinek átlaga replikánként; 95%.
**K3-X (leíró, Dani 11-03):** ha a lánc kimenete (kimenet, megmaradt jelöltek, kötés, a modellnek mutatott tétel) az
alany kinyerésével és a szabályalapú kinyerővel eltér, a tétel emberhez megy; ugyanaz a τ. A fő rendszerhez képest: a
visszatartott hibák, az elveszített helyes lezárások, a hasznos lefedettség és a lezárási hibaarány; külön sor az egyező,
de hibás kinyerés (a két kinyerés egyezik, az orákulum-úttól eltér).

  python3 kor08/eszkozok/g5_k3_08.py --forras 06 --cal CAL --teszt TESZT \\
      --lanc kor08/adat/G1/kinyert_06 --pont cache/k08/pontoz/G1/l06_{csalad}_{szelet}.json \\
      --k07 cache/k07/f3r_proba/k06_{csalad}_{szelet}.json \\
      --szabaly kor08/adat/G1/szabaly_06 --orakulum kor08/adat/G1/orakulum_06 --kar-x L-S --reps 2000 --out ...
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import elemzes07 as E7  # noqa: E402
import g1_dontes08 as GD  # noqa: E402
import lanc08 as L  # noqa: E402

TAU_HALMAZ = {"rendszer": False}  # `--tau-halmaz`; alapból a modell döntésein (a fenti docstring)
MEROK = ("hasznos_lef", "lezarasi_hiba", "lezart", "kotes", "kotes_hiba", "modell_lezart", "modell_lezart_hiba",
         "emberhez", "adatbekeres", "tovabbitas", "tau_alatt", "aurc")
HIBA_CEL = 0.05
PAROK = (("L-RN", "L-S"), ("L-S", "B1-4S"), ("L-RN", "B1-4R"), ("L-R07", "L-S"), ("L-R", "L-S"))


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def kulcs(lanc: dict, mod: dict, i: str) -> tuple:
    r = lanc[i]
    m = (mod[i]["state"], mod[i]["options"]) if i in mod else None
    return r["kimenet"], tuple(sorted(r["megmaradt"])), r["kotes"], json.dumps(m, ensure_ascii=False)


class Szelet:
    """Egy család egy szelete (CAL vagy TESZT): a lánc kimenete és a karok pontszámai minden itemen (a modellhez nem jutott
    tételen NaN), valamint a 07 lánc nélküli karjai ugyanezeken az itemeken."""

    def __init__(self, src: str, fam: str, sz: str, lanc_dir: Path, pont: Path, k07: Path | None):
        items = [it for _, it in L.betolt(src, fam) if it["split"] == sz]
        self.ids = [it["id"] for it in items]
        self.n = len(items)
        st, gold = [it["content_state"] for it in items], [it["gold"] for it in items]
        self.state = np.array([E7.ALLAPOT[s] for s in st])
        self.lanc = {r["id"]: r for r in jsonl(lanc_dir / f"lanc_{fam}.jsonl")}
        self.mod = {r["id"]: r for r in jsonl(lanc_dir / "items" / f"{fam}.jsonl")}
        kim = [self.lanc[i]["kimenet"] for i in self.ids]
        self.kotes = np.array([k == "kotes" for k in kim])
        self.emberhez = np.array([k == "emberhez" for k in kim])
        self.kotes_jo = np.array([k == "kotes" and s == "MATCH" and self.lanc[i]["kotes"] == g
                                  for k, s, g, i in zip(kim, st, gold, self.ids)])
        d = json.loads(pont.read_text())["keret4"]
        pos = {i: n for n, i in enumerate(d["ids"])}
        self.modell = np.array([k == "modell" and i in pos for k, i in zip(kim, self.ids)])
        self.kind = np.array([d["dontes"][i]["kind"] if m else "–" for i, m in zip(self.ids, self.modell)])
        self.cor = np.array([GD.helyes(d["dontes"][i], s, g) if m else False for i, m, s, g in zip(self.ids, self.modell, st, gold)])
        self.pont = self._karok(d, pos, self.modell)
        self.k07 = None
        if k07 is not None:
            d7 = json.loads(k07.read_text())["keret4"]
            p7 = {i: n for n, i in enumerate(d7["ids"])}
            van = np.array([i in p7 for i in self.ids])
            self.k07 = {"van": van,
                        "kind": np.array([d7["dontes"][i]["kind"] if v else "–" for i, v in zip(self.ids, van)]),
                        "cor": np.array([GD.helyes(d7["dontes"][i], s, g) if v else False
                                         for i, v, s, g in zip(self.ids, van, st, gold)]),
                        "pont": self._karok(d7, p7, van)}
        cl = defaultdict(list)
        for n, it in enumerate(items):
            cl[it["template_group_id"]].append(n)
        self.clusters = [np.array(v) for v in cl.values()]

    def _karok(self, d: dict, pos: dict, maszk: np.ndarray) -> dict[str, list[np.ndarray]]:
        out: dict[str, list[np.ndarray]] = defaultdict(list)
        for k in sorted(d["pontszam"]):
            v = np.asarray(d["pontszam"][k], float)
            out[k.split("|")[0]].append(np.array([v[pos[i]] if m else np.nan for i, m in zip(self.ids, maszk)]))
        return out

    def huzas(self, rng: np.random.Generator) -> np.ndarray:
        return np.concatenate([self.clusters[c] for c in rng.integers(0, len(self.clusters), len(self.clusters))])


def rendszer(S: Szelet, q: np.ndarray, tau: float, idx: np.ndarray, lanc_nelkul: bool = False,
             maszk: np.ndarray | None = None) -> dict[str, float]:
    """A TESZT-mérők egy τ-val. `lanc_nelkul`: a 07 kar (nincs kötés, minden item a modellhez). `maszk`: a K3-X — csak
    ezek a tételek zárhatók le (a többi emberhez)."""
    n = len(idx)
    if lanc_nelkul:
        K = S.k07
        mod, kind, cor = K["van"][idx], K["kind"][idx], K["cor"][idx]
        kotes, kotes_jo, emb = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    else:
        mod, kind, cor = S.modell[idx], S.kind[idx], S.cor[idx]
        kotes, kotes_jo, emb = S.kotes[idx], S.kotes_jo[idx], S.emberhez[idx]
    qs = q[idx]
    if maszk is not None:  # K3-X: a két kinyerés eltér → emberhez
        m = maszk[idx]
        emb, mod, kotes, kotes_jo = emb | ~m, mod & m, kotes & m, kotes_jo & m
    lez_m = mod & np.isin(kind, ("SELECT", "NONE")) & (np.nan_to_num(qs, nan=-np.inf) >= tau)
    lez = kotes | lez_m
    jo = kotes_jo | (lez_m & cor)

    def rate(a: np.ndarray, b: np.ndarray) -> float:
        return float(a.sum() / b.sum()) if b.sum() else math.nan
    mm = mod & ~np.isnan(qs)
    return {"hasznos_lef": float(jo.sum() / n), "lezarasi_hiba": rate(lez & ~jo, lez), "lezart": float(lez.sum() / n),
            "kotes": float(kotes.sum() / n), "kotes_hiba": rate(kotes & ~kotes_jo, kotes),
            "modell_lezart": float(lez_m.sum() / n), "modell_lezart_hiba": rate(lez_m & ~cor, lez_m),
            "emberhez": float(emb.sum() / n), "adatbekeres": float((mod & (kind == "MISSING")).sum() / n),
            "tovabbitas": float((mod & (kind == "OOS")).sum() / n),
            "tau_alatt": float((mod & np.isin(kind, ("SELECT", "NONE")) & ~lez_m & ~emb).sum() / n),
            "aurc": E7.aurc(qs[mm], cor[mm]) if mm.any() else math.nan}


def kar_merok(C: Szelet, T: Szelet, kar: str, ic: np.ndarray, it: np.ndarray, kmin: np.ndarray, nelkul: bool,
              maszk: np.ndarray | None = None) -> tuple[dict[str, float], int, list[float]]:
    """A τ seedenként a CAL-on (csak a modell lezárható döntésein), a mérők a TESZT-en, a seedek átlaga."""
    Kc = C.k07 if nelkul else None
    qc_l = (Kc["pont"][kar] if nelkul else C.pont[kar])
    qt_l = (T.k07["pont"][kar] if nelkul else T.pont[kar])
    mod_c = Kc["van"] if nelkul else C.modell
    kind_c = Kc["kind"] if nelkul else C.kind
    cor_c = Kc["cor"] if nelkul else C.cor
    lezarhato = mod_c & np.isin(kind_c, ("SELECT", "NONE"))
    ms, nincs, taus = [], 0, []
    for qc, qt in zip(qc_l, qt_l):
        qc = np.nan_to_num(qc, nan=-np.inf)
        if TAU_HALMAZ["rendszer"] and not nelkul:
            tau = tau_rendszer(qc, cor_c, lezarhato, C.kotes, C.kotes_jo, ic, kmin)
        else:
            tau = E7.tau_of(qc, cor_c, lezarhato, ic, kmin)
        nincs += math.isinf(tau)
        taus.append(tau)
        ms.append(rendszer(T, qt, tau, it, nelkul, maszk))
    return {k: float(np.nanmean([m[k] for m in ms])) for k in MEROK}, nincs, taus


def tau_rendszer(q: np.ndarray, cor: np.ndarray, lezarhato: np.ndarray, kotes: np.ndarray, kotes_jo: np.ndarray,
                 idx: np.ndarray, kmin: np.ndarray) -> float:
    """A `--tau-halmaz rendszer` változat: a CP-feltétel és a 200-as minimum a teljes lezárt halmazon (a kötések mindig
    benne, utánuk a modell lezárható döntései csökkenő pontszámmal)."""
    nk, kk = int(kotes[idx].sum()), int(kotes_jo[idx].sum())
    s = idx[lezarhato[idx]]
    if nk + len(s) < E7.MIN_ACC or not len(s):
        return math.inf
    o = s[np.argsort(-q[s], kind="stable")]
    c = q[o]
    k = kk + np.cumsum(cor[o])
    n = nk + np.arange(1, len(o) + 1)
    boundary = np.append(c[1:] != c[:-1], True)
    ok = boundary & (n >= E7.MIN_ACC) & (k >= kmin[n])
    return float(c[np.nonzero(ok)[0][-1]]) if ok.any() else math.inf


def k3x_maszk(T: Szelet, szab_dir: Path, ora_dir: Path, fam: str) -> tuple[np.ndarray, np.ndarray]:
    """(a két kinyerés egyezik, az egyező kinyerés hibás: egyezik, de az orákulum-úttól eltér)."""
    sl, sm = {r["id"]: r for r in jsonl(szab_dir / f"lanc_{fam}.jsonl")}, {r["id"]: r for r in jsonl(szab_dir / "items" / f"{fam}.jsonl")}
    ol, om = {r["id"]: r for r in jsonl(ora_dir / f"lanc_{fam}.jsonl")}, {r["id"]: r for r in jsonl(ora_dir / "items" / f"{fam}.jsonl")}
    egyezik = np.array([kulcs(T.lanc, T.mod, i) == kulcs(sl, sm, i) for i in T.ids])
    hibas = np.array([e and kulcs(T.lanc, T.mod, i) != kulcs(ol, om, i) for e, i in zip(egyezik, T.ids)])
    return egyezik, hibas


def csalad(a, fam: str, rng: np.random.Generator, kmin: np.ndarray) -> dict:
    def p(s: str, sz: str) -> Path:
        return EXP / s.format(csalad=fam, szelet=sz)
    C = Szelet(a.forras, fam, a.cal, EXP / a.lanc, p(a.pont, a.cal), p(a.k07, a.cal) if a.k07 else None)
    T = Szelet(a.forras, fam, a.teszt, EXP / a.lanc, p(a.pont, a.teszt), p(a.k07, a.teszt) if a.k07 else None)
    karok = [(k, False) for k in sorted(T.pont)] + ([(k, True) for k in sorted(T.k07["pont"])] if T.k07 else [])
    full_c, full_t = np.arange(C.n), np.arange(T.n)
    x = None
    if a.szabaly and a.kar_x in T.pont:
        egy, hib = k3x_maszk(T, EXP / a.szabaly, EXP / a.orakulum, fam)
        x = {"egyezik": egy, "hibas": hib}
    pont, tau, nincs = {}, {}, {}
    for k, nl in karok:
        pont[k], nincs[k], tau[k] = kar_merok(C, T, k, full_c, full_t, kmin, nl)
    if x is not None:
        pont["K3-X"], _, _ = kar_merok(C, T, a.kar_x, full_c, full_t, kmin, False, x["egyezik"])
        # a fő rendszerhez képest itemszinten (a teljes mintán, seedenként a saját τ-val, átlag)
        vissz, elv = [], []
        for qc, qt, t in zip(C.pont[a.kar_x], T.pont[a.kar_x], tau[a.kar_x]):
            lez_m = T.modell & np.isin(T.kind, ("SELECT", "NONE")) & (np.nan_to_num(qt, nan=-np.inf) >= t)
            lez, jo = T.kotes | lez_m, T.kotes_jo | (lez_m & T.cor)
            vissz.append(int((lez & ~jo & ~x["egyezik"]).sum()))
            elv.append(int((lez & jo & ~x["egyezik"]).sum()))
        x_leiro = {"kar": a.kar_x, "visszatartott_hiba": float(np.mean(vissz)), "elveszett_helyes": float(np.mean(elv)),
                   "egyezo_de_hibas": int(x["hibas"].sum()), "nem_egyezik": int((~x["egyezik"]).sum()), "n": T.n}
    rep = {k: {m: [] for m in MEROK} for k in pont}
    rep_nincs = Counter()
    nseed = {k: len(T.k07["pont"][k] if nl else T.pont[k]) for k, nl in karok}
    for _ in range(a.reps):
        ic, it = C.huzas(rng), T.huzas(rng)
        for k, nl in karok:
            m, ni, _ = kar_merok(C, T, k, ic, it, kmin, nl)
            rep_nincs[k] += ni
            for mm in MEROK:
                rep[k][mm].append(m[mm])
        if x is not None:
            m, _, _ = kar_merok(C, T, a.kar_x, ic, it, kmin, False, x["egyezik"])
            for mm in MEROK:
                rep["K3-X"][mm].append(m[mm])
    R = {k: {m: np.array(v) for m, v in d.items()} for k, d in rep.items()}
    ci = {k: {m: E7.ci(v) for m, v in d.items()} for k, d in R.items()}
    hibafelt = {}
    for k in pont:
        e, hi = pont[k]["lezarasi_hiba"], ci[k]["lezarasi_hiba"][1]
        hibafelt[k] = ("nincs lezárás" if math.isnan(e) else "nem teljesül" if e > HIBA_CEL else
                       "bizonytalan" if hi > HIBA_CEL else "teljesül")
    parok = {}
    for A, B in PAROK + ((a.kar_x, "K3-X"),) if x is not None else PAROK:
        if A not in R or B not in R:
            continue
        parok[f"{A} − {B}"] = {m: {"delta": pont[A][m] - pont[B][m], "ci95": E7.ci(R[A][m] - R[B][m]),
                                   "p": E7.p_ketoldali(R[A][m] - R[B][m])} for m in ("hasznos_lef", "lezarasi_hiba", "aurc")}
    lanc_kimenet = {"kotes": int(T.kotes.sum()), "kotes_hibas": int((T.kotes & ~T.kotes_jo).sum()),
                    "emberhez": int(T.emberhez.sum()), "modellhez": int(T.modell.sum()), "n": T.n}
    return {"n_cal": C.n, "n_teszt": T.n, "sablon_cal": len(C.clusters), "sablon_teszt": len(T.clusters), "pont": pont,
            "ci95": ci, "tau": {k: [None if math.isinf(t) else t for t in v] for k, v in tau.items()},
            "nincs_munkapont": nincs, "nincs_munkapont_replika": {k: v / max(1, a.reps * nseed[k]) for k, v in rep_nincs.items()},
            "hibafeltetel": hibafelt, "parok": parok, "lanc_kimenet": lanc_kimenet, "k3x": x_leiro if x is not None else None}


def f(x, pct: bool = True, d: int = 1) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return (f"{100 * x:.{d}f}%" if pct else f"{x:.4f}").replace(".", ",")


def lap(res: dict) -> str:
    o = [f"# 08 G5 — K3: a gyakorlati eredmény ({res['cimke']})", "",
         f"Forrás `{res['forras']}`, CAL `{res['cal']}`, TESZT `{res['teszt']}`; sabloncsoportos bootstrap ({res['reps']} replika), "
         "a τ replikánként csak az újramintázott CAL-on, a modell lezárható döntésein; a lánc kötései küszöb nélkül lezártak.", ""]
    for fam, F in res["csaladok"].items():
        lk = F["lanc_kimenet"]
        o += [f"## {fam}", "",
              f"CAL {F['n_cal']}, TESZT {F['n_teszt']} item ({F['sablon_teszt']} sabloncsoport). A lánc a TESZT-en: {lk['kotes']} kötés "
              f"({lk['kotes_hibas']} hibás), {lk['emberhez']} emberhez, {lk['modellhez']} a modellhez.", "",
              "| kar | hasznos lefedettség | lezárási hibaarány | hibafeltétel | lezárt | ebből kötés (hiba) | modell lezárt (hiba) | "
              "emberhez | Y / Z | τ alatt | AURC (modell) | munkapont nélkül |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for k, p in F["pont"].items():
            c = F["ci95"][k]
            o.append(f"| {k} | {f(p['hasznos_lef'])} [{f(c['hasznos_lef'][0])}; {f(c['hasznos_lef'][1])}] | "
                     f"{f(p['lezarasi_hiba'])} [{f(c['lezarasi_hiba'][0])}; {f(c['lezarasi_hiba'][1])}] | {F['hibafeltetel'][k]} | "
                     f"{f(p['lezart'])} | {f(p['kotes'])} ({f(p['kotes_hiba'])}) | {f(p['modell_lezart'])} ({f(p['modell_lezart_hiba'])}) | "
                     f"{f(p['emberhez'])} | {f(p['adatbekeres'])} / {f(p['tovabbitas'])} | {f(p['tau_alatt'])} | {f(p['aurc'], False)} | "
                     f"{F['nincs_munkapont'].get(k, '–')} |")
        if F["parok"]:
            o += ["", "| pár | Δ hasznos lefedettség | 95% | Δ lezárási hibaarány | 95% | ΔAURC | 95% |", "|---|---|---|---|---|---|---|"]
            for nev, P in F["parok"].items():
                h, e, u = P["hasznos_lef"], P["lezarasi_hiba"], P["aurc"]
                o.append(f"| {nev} | {f(h['delta'])} | [{f(h['ci95'][0])}; {f(h['ci95'][1])}] | {f(e['delta'])} | "
                         f"[{f(e['ci95'][0])}; {f(e['ci95'][1])}] | {f(u['delta'], False)} | [{f(u['ci95'][0], False)}; {f(u['ci95'][1], False)}] |")
        if F["k3x"]:
            x = F["k3x"]
            o += ["", f"**K3-X** ({x['kar']}, leíró): {x['nem_egyezik']} / {x['n']} tételen a két kinyerés lánc-kimenete eltér "
                  f"(emberhez); a fő rendszerhez képest visszatartott hiba {f(x['visszatartott_hiba'], False)}, elveszett helyes "
                  f"lezárás {f(x['elveszett_helyes'], False)} (seed-átlag); egyező, de hibás kinyerés: {x['egyezo_de_hibas']}."]
        o.append("")
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forras", required=True, choices=list(L.FORRASOK))
    ap.add_argument("--cal", required=True)
    ap.add_argument("--teszt", required=True)
    ap.add_argument("--lanc", required=True, help="a valós kinyerés láncának könyvtára")
    ap.add_argument("--pont", required=True, help="a láncos pontozott szelet, `{csalad}` és `{szelet}` helyőrzővel")
    ap.add_argument("--k07", help="a 07 lánc nélküli pontozott szelete, `{csalad}` és `{szelet}` helyőrzővel")
    ap.add_argument("--szabaly", help="K3-X: a lánc a szabályalapú kinyeréssel (könyvtár)")
    ap.add_argument("--orakulum", help="K3-X: a lánc orákulum-úton (az egyező, de hibás kinyeréshez)")
    ap.add_argument("--kar-x", default="L-RN")
    ap.add_argument("--tau-halmaz", default="modell", choices=("modell", "rendszer"))
    ap.add_argument("--csalad", action="append", choices=L.CSALADOK)
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--cimke", default="G1 pilot, fejlesztési szám")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    TAU_HALMAZ["rendszer"] = a.tau_halmaz == "rendszer"
    kmin = E7.kmin_tabla(5000)
    res = {"forras": a.forras, "cal": a.cal, "teszt": a.teszt, "reps": a.reps, "seed": a.seed, "cimke": a.cimke,
           "tau_halmaz": a.tau_halmaz,
           "kar_x": a.kar_x, "csaladok": {fam: csalad(a, fam, rng, kmin) for fam in a.csalad or L.CSALADOK}}
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "g5_k3.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "g5_k3.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


if __name__ == "__main__":
    main()
