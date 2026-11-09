"""08 G5 utólag (11-06; nem rögzített; Dani: „igen, indítsd”) — a K1(a) felszíni jegyek próbája: a fej (L-RN) mennyiben a
konstrukció felszíni jegyeit tanulta. Csak a szöveget látó modellek ugyanazon a tanítómintán (`orakulum_G2N`: (a) a (b) ellen, a
sabloncsoportok diszjunktak a teszttől) és ugyanazon a K1(a)-halmazon (a `g5_k1_08` diagnózisa), ugyanazzal a klaszteres bootstrappal.
Modellek: a szöveg hossza; szó 1–2-gram és karakter 3–5-gram TF-IDF logisztikus regresszióval (C a tanítóminta sabloncsoportos
CV-jével). Mellette a fej nyeresége a felszíni pontszám kvartilisein belül és egy egységen belül ((a) és saját (b)-i), ahol a szöveg
közös része kiesik.

**Az olvasat a futás előtt rögzítve (szabálycsalád, a tanítómintán legjobb szöveges modell teszt-AUROC-ja):**
  ≥ 0,85        a K1(a) nyeresége nagyrészt felszíni jeggyel magyarázható, a fejről szóló állítás ebben a formában nem tartható
  0,70 – 0,85   részben magyarázható: csak az egységen belüli és a kvartiliseken belüli nyereség számít
  < 0,70        a TF-IDF szintű felszíni jegy nem magyarázza
Az alacsony érték a mélyebb konstrukciós jegyeket nem zárja ki. Leíró vizsgálat, a G5 számai nem változnak.

  python3 kor08/eszkozok/felszin08.py --out kor08/eredmenyek/G5_utolagos/felszin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE)]
import g5_k1_08 as K  # noqa: E402

G3 = EXP / "kor08/adat/G3"
PP = EXP / "cache/k08/pecset/pontoz"
CSALADOK = ("szabaly.koltsegelszamolas", "penzugy.bankparositas", "muszaki.hibaelharitas")
REPS, SEED = 10000, 20261106


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def szoveg(it: dict) -> str:
    return it["state"] + "\n" + " ".join(o["text"] for o in it["options"])


def pipe(tipus: str, c: float):
    v = (TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True) if tipus == "szó" else
         TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True))
    return make_pipeline(v, LogisticRegression(C=c, class_weight="balanced", max_iter=2000))


def illeszt(tipus: str, x: list[str], y: np.ndarray, g: np.ndarray) -> tuple:
    """A legjobb C a sabloncsoportos CV-vel; (modell, CV-AUROC, C)."""
    best = (-1.0, 1.0)
    for c in (0.1, 1.0, 10.0, 100.0):
        s = np.zeros(len(y))
        for tr, te in GroupKFold(5).split(x, y, g):
            s[te] = pipe(tipus, c).fit([x[i] for i in tr], y[tr]).predict_proba([x[i] for i in te])[:, 1]
        best = max(best, (float(roc_auc_score(y, s)), c))
    return pipe(tipus, best[1]).fit(x, y), best[0], best[1]


def csalad(fam: str, rng: np.random.Generator) -> dict:
    C = K.Csalad(fam, PP / f"lG2T_{fam}_G2T.json", EXP / "kor08/adat/G2/ert_teszt/items", G3 / "kinyert_G2T", G3 / "orakulum_G2T")
    tan = jl(G3 / f"orakulum_G2N/items/{fam}.jsonl")
    xt = [szoveg(i) for i in tan]
    yt = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan])
    gt = np.array([i["template_group_id"] for i in tan])
    tesz = {i["id"]: i for i in jl(G3 / f"kinyert_G2T/items/{fam}.jsonl")}
    raw = {i["id"]: i for i in jl(EXP / f"kor08/adat/G2/ert_teszt/items/{fam}.jsonl")}
    if set(gt) & {raw[i]["template_group_id"] for i in C.ids}:
        raise SystemExit(f"{fam}: közös sabloncsoport a tanító és a teszt közt")
    x = [szoveg(tesz[i]) for i in C.ids]
    halmaz, pos = C.ag["K1a"]
    err: dict[str, np.ndarray] = {}
    hossz = np.array([len(s) for s in x], float)
    irany = 1.0 if roc_auc_score(yt, [len(s) for s in xt]) >= 0.5 else -1.0
    err["hossz"] = irany * hossz
    info: dict = {"hossz": {"cv": float(max(roc_auc_score(yt, [len(s) for s in xt]), 1 - roc_auc_score(yt, [len(s) for s in xt])))}}
    modell = {}
    for t in ("szó", "karakter"):
        m, cv, c = illeszt(t, xt, yt, gt)
        modell[t] = m
        err[t] = m.predict_proba(x)[:, 1]
        info[t] = {"cv": cv, "C": c}
    legjobb = max(("szó", "karakter"), key=lambda t: info[t]["cv"])
    err["L-RN"] = -np.mean(C.pont["L-RN"], axis=0)
    err["L-S"] = -np.mean(C.pont["L-S"], axis=0)
    nevek = ("hossz", "szó", "karakter", "L-S", "L-RN")

    def au(n: str, s: np.ndarray) -> float:
        return K.auroc(err[n][s], pos[s])
    full = np.where(halmaz)[0]
    pont = {n: au(n, full) for n in nevek}
    if abs(float(np.mean([K.auroc(-q[full], pos[full]) for q in C.pont["L-RN"]])) - pont["L-RN"]) > 0.02:
        print(f"{fam}: a seed-átlag pontszám és a seedek átlaga eltér", flush=True)
    rep = {n: np.empty(REPS) for n in nevek}
    rep["L-RN − legjobb"] = np.empty(REPS)
    # egységen belül: az (a) SELECT-je a saját (b) helyes SELECT-jei ellen
    eg = {}
    for k in full:
        eg.setdefault(raw[C.ids[k]]["meta"]["ertelmezes"]["egyseg"], []).append(k)
    kl = {i: raw[i]["template_group_id"] for i in C.ids}
    parok: dict[str, list] = {}
    for tag in eg.values():
        a = [k for k in tag if pos[k]]
        b = [k for k in tag if not pos[k]]
        if a and b:
            parok.setdefault(kl[C.ids[a[0]]], []).extend((i, j) for i in a for j in b)
    pk = list(parok)

    def egyseg_au(n: str, cs: list[str]) -> float:
        p = [q for c in cs for q in parok[c]]
        if not p:
            return float("nan")
        d = np.array([err[n][i] - err[n][j] for i, j in p])
        return float(((d > 0) + 0.5 * (d == 0)).mean())
    ep = {n: egyseg_au(n, pk) for n in ("szó", "karakter", "L-S", "L-RN")}
    er = {n: np.empty(REPS) for n in ep}
    for r in range(REPS):
        idx = C.huzas(rng)
        s = idx[halmaz[idx]]
        for n in nevek:
            rep[n][r] = au(n, s)
        rep["L-RN − legjobb"][r] = rep["L-RN"][r] - rep[legjobb][r]
        if r < 2000 and pk:
            cs = [pk[i] for i in rng.integers(0, len(pk), len(pk))]
            for n in er:
                er[n][r] = egyseg_au(n, cs)
    q = np.quantile(err[legjobb][full], (0.25, 0.5, 0.75))
    sav = np.searchsorted(q, err[legjobb][full])
    retegek = []
    for b in range(4):
        s = full[sav == b]
        retegek.append({"n": int(len(s)), "a": int(pos[s].sum()), "L-RN": K.auroc(err["L-RN"][s], pos[s]), "L-S": K.auroc(err["L-S"][s], pos[s])})
    v, lr = modell["szó"].steps[0][1], modell["szó"].steps[1][1]
    o = np.argsort(lr.coef_[0])
    t = v.get_feature_names_out()
    return {"n": int(len(full)), "a": int(pos[full].sum()), "b": int((~pos[full]).sum()), "tanito": {"n": len(yt), "a": int(yt.sum()), "sablon": len(set(gt))},
            "info": info, "legjobb": legjobb, "pont": pont, "ci95": {n: K.ci(v_) for n, v_ in rep.items()},
            "delta": pont["L-RN"] - pont[legjobb], "egyseg": {"parok": sum(len(v_) for v_ in parok.values()), "pont": ep, "ci95": {n: K.ci(er[n][:2000]) for n in er}},
            "kvartilis": retegek, "szavak_a": [str(t[i]) for i in o[::-1][:15]], "szavak_b": [str(t[i]) for i in o[:15]]}


def sz(x: float) -> str:
    return "–" if x != x else f"{x:.3f}".replace(".", ",")


def lap(res: dict) -> str:
    o = ["# 08 G5 utólag — a K1(a) felszíni jegyek próbája (leíró)", "",
         "A szöveges modellek a tanítómintán tanulnak, a sabloncsoportok diszjunktak a teszttől. A halmaz a `g5_k1_08` K1(a)-ja. Az olvasati küszöbök a futás előtt rögzítve (`felszin08.py`).", ""]
    for fam, F in res.items():
        p, c = F["pont"], F["ci95"]
        o += [f"## {fam}", "", f"Teszt: {F['a']} (a)-SELECT, {F['b']} (b) helyes SELECT. Tanítóminta: {F['tanito']['n']} item ({F['tanito']['a']} (a)), {F['tanito']['sablon']} sabloncsoport. A legjobb szöveges modell a CV szerint: {F['legjobb']}.", "",
              "| pontszám | tanító CV-AUROC | teszt AUROC | 95% |", "|---|---|---|---|"]
        for n in ("hossz", "szó", "karakter"):
            o.append(f"| {n} | {sz(F['info'][n]['cv'])} | {sz(p[n])} | [{sz(c[n][0])}; {sz(c[n][1])}] |")
        for n in ("L-S", "L-RN"):
            o.append(f"| {n} | – | {sz(p[n])} | [{sz(c[n][0])}; {sz(c[n][1])}] |")
        d = c["L-RN − legjobb"]
        o += ["", f"L-RN − legjobb szöveges: {sz(F['delta'])} [{sz(d[0])}; {sz(d[1])}].", "", f"**Egységen belül** ({F['egyseg']['parok']} pár):", "", "| pontszám | AUROC | 95% |", "|---|---|---|"]
        for n, v in F["egyseg"]["pont"].items():
            ci = F["egyseg"]["ci95"][n]
            o.append(f"| {n} | {sz(v)} | [{sz(ci[0])}; {sz(ci[1])}] |")
        o += ["", "**A legjobb szöveges pontszám kvartilisein belül:**", "", "| kvartilis | n | (a) | L-RN | L-S |", "|---|---|---|---|---|"]
        o += [f"| {i + 1} | {r['n']} | {r['a']} | {sz(r['L-RN'])} | {sz(r['L-S'])} |" for i, r in enumerate(F["kvartilis"])]
        o += ["", "Az (a) felé húzó szavak: " + ", ".join(F["szavak_a"]), "", "A (b) felé húzó szavak: " + ", ".join(F["szavak_b"]), ""]
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(SEED)
    res = {f: csalad(f, rng) for f in CSALADOK}
    o = EXP / a.out
    o.mkdir(parents=True, exist_ok=True)
    (o / "felszin.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (o / "felszin.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


if __name__ == "__main__":
    main()
