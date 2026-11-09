"""08 illesztett kontroll (M) — az illesztés ellenőrzése, a fejek eredménye nélkül: csak a szöveget nézi, modell kimenete nem kerül ide. Az illesztett (a) a meglévő (b) ellen, nyers
szövegen (`state` + opciók):
  hossz    a szöveg hossza (0,5 felé hajtva: az irány nem számít)
  régi     a `felszin08` modelljei, a G2 tanítómintáján (a) a (b) ellen: ezt láthatta a fej. Ha ez nem esik, az illesztés nem sikerült
  friss    szó és karakter TF-IDF, az illesztett (a) a (b) ellen, sabloncsoportos ötszörös CV-vel a teszten: mit lehet még tanulni a szövegből

**Az elfogadás küszöbei a generálás előtt rögzítve (szabálycsalád):** hossz ≤ 0,60; régi ≤ 0,70; friss ≤ 0,80. A bank és a hiba leíró. Ha nem teljesül, a mondatok javíthatók,
mert fejeredmény még nincs; a körök száma a rögzítésbe kerül. Az (a) eredeti számai referenciaként.

  python3 kor08/eszkozok/felszin08m.py --out kor08/eredmenyek/M/felszin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import felszin08 as F  # noqa: E402

G2 = F.EXP / "kor08/adat/G2"
M = F.EXP / "kor08/adat/M"
HATAR = {"hossz": 0.60, "regi": 0.70, "friss": 0.80}


def sz(x: float) -> str:
    return f"{x:.3f}".replace(".", ",")


def hajtott(y: np.ndarray, s: list[float]) -> float:
    a = float(roc_auc_score(y, s))
    return max(a, 1 - a)


def friss(tipus: str, x: list[str], y: np.ndarray, g: np.ndarray) -> tuple[float, np.ndarray]:
    s = np.zeros(len(y))
    for tr, te in GroupKFold(5).split(x, y, g):
        s[te] = F.pipe(tipus, 10.0).fit([x[i] for i in tr], y[tr]).predict_proba([x[i] for i in te])[:, 1]
    return float(roc_auc_score(y, s)), s


def csalad(fam: str) -> dict:
    tan = F.jl(G2 / f"ert_tanito/items/{fam}.jsonl")
    tes = F.jl(G2 / f"ert_teszt/items/{fam}.jsonl")
    am = F.jl(M / f"items/{fam}.jsonl")
    eg = {i["meta"]["ertelmezes"]["egyseg"] for i in am}
    b = [i for i in tes if i["meta"]["ertelmezes"]["alt"] == "b" and i["meta"]["ertelmezes"]["egyseg"] in eg]
    a0 = [i for i in tes if i["meta"]["ertelmezes"]["alt"] == "a"]
    x = [F.szoveg(i) for i in am + b]
    y = np.array([True] * len(am) + [False] * len(b))
    g = np.array([i["template_group_id"] for i in am + b])
    xt = [F.szoveg(i) for i in tan]
    yt = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan])
    gt = np.array([i["template_group_id"] for i in tan])
    r: dict = {"n_a": len(am), "n_a_eredeti": len(a0), "n_b": len(b), "klaszter": len(set(g)),
               "median_hossz": {"a_eredeti": float(np.median([len(i["state"]) for i in a0])), "a_illesztett": float(np.median([len(i["state"]) for i in am])),
                                "b": float(np.median([len(i["state"]) for i in b]))},
               "hossz": hajtott(y, [len(s) for s in x])}
    y0 = np.array([True] * len(a0) + [False] * len(b))
    x0 = [F.szoveg(i) for i in a0 + b]
    for t in ("szó", "karakter"):
        m, cv, c = F.illeszt(t, xt, yt, gt)
        r[f"regi_{t}"] = float(roc_auc_score(y, m.predict_proba(x)[:, 1]))
        r[f"regi_{t}_eredeti_a"] = float(roc_auc_score(y0, m.predict_proba(x0)[:, 1]))
        r[f"friss_{t}"], s = friss(t, x, y, g)
        for ny in ("hu", "en"):
            q = np.array([i["lang"] == ny for i in am + b])
            r[f"friss_{t}_{ny}"] = float(roc_auc_score(y[q], s[q])) if y[q].any() else float("nan")
    p = F.pipe("szó", 10.0).fit(x, y)
    v, lr = p.steps[0][1], p.steps[1][1]
    o = np.argsort(lr.coef_[0])
    t = v.get_feature_names_out()
    r["szavak_a"] = [str(t[i]) for i in o[::-1][:25]]
    r["szavak_b"] = [str(t[i]) for i in o[:25]]
    r["regi"] = max(r["regi_szó"], r["regi_karakter"])
    r["friss"] = max(r["friss_szó"], r["friss_karakter"])
    return r


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {f: csalad(f) for f in F.CSALADOK}
    s = res[F.CSALADOK[0]]
    ok = {k: s[k] <= v for k, v in HATAR.items()}
    o = ["# 08 M — az illesztés ellenőrzése", "", "Csak szöveg, fejeredmény nélkül. Küszöbök a szabálycsaládon: hossz ≤ 0,60, régi ≤ 0,70, friss ≤ 0,80.", "",
         f"**Szabálycsalád: {'elfogadva' if all(ok.values()) else 'nem elfogadva'}** ({', '.join(f'{k} {sz(s[k])}' for k in HATAR)}).", ""]
    for f, r in res.items():
        m = r["median_hossz"]
        o += [f"## {f}", "", f"Illesztett (a) {r['n_a']} / {r['n_a_eredeti']}, (b) {r['n_b']}, {r['klaszter']} klaszter. Medián hossz: eredeti (a) {m['a_eredeti']:.0f}, illesztett (a) {m['a_illesztett']:.0f}, (b) {m['b']:.0f}.", "",
              "| próba | szó | karakter |", "|---|---|---|",
              f"| régi modell, az eredeti (a) | {sz(r['regi_szó_eredeti_a'])} | {sz(r['regi_karakter_eredeti_a'])} |",
              f"| régi modell, az illesztett (a) | {sz(r['regi_szó'])} | {sz(r['regi_karakter'])} |",
              f"| friss modell, CV | {sz(r['friss_szó'])} | {sz(r['friss_karakter'])} |",
              f"| friss modell, CV, magyar | {sz(r['friss_szó_hu'])} | {sz(r['friss_karakter_hu'])} |",
              f"| friss modell, CV, angol | {sz(r['friss_szó_en'])} | {sz(r['friss_karakter_en'])} |", "",
              f"Hossz: {sz(r['hossz'])}.", "", "Az (a) felé húzó szavak: " + ", ".join(r["szavak_a"]), "", "A (b) felé húzó szavak: " + ", ".join(r["szavak_b"]), ""]
    d = F.EXP / a.out
    d.mkdir(parents=True, exist_ok=True)
    (d / "illesztes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "illesztes.md").write_text("\n".join(o) + "\n", encoding="utf-8")
    print("\n".join(o))


if __name__ == "__main__":
    main()
