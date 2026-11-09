"""08 G5 utólag (11-06; nem rögzített) — a `felszin08` ellenőrzése: nem a próba hibája-e a szinte tökéletes szöveges elválasztás. Csak a nyers
G2-szöveg (lánc-blokk és opciók nélkül), átalakítások után, sabloncsoport-diszjunkt tanítással: kisbetű + ékezet és számok nélkül, a szöveg eleje és
vége külön, nyelvenként, és címke-keverés kontrollként (a tanítócímkék véletlen sorrendben: 0,5 körül kell lennie). Mellette páros minta és a
leghasznosabb karakter-n-gramok.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import felszin08 as F  # noqa: E402

G2 = F.EXP / "kor08/adat/G2"


def sima(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFD", s.lower()) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"\d+", "0", s))


def auc(tip: str, xa: list, ya, xb: list, yb, c: float = 10.0) -> float:
    return float(roc_auc_score(yb, F.pipe(tip, c).fit(xa, ya).predict_proba(xb)[:, 1]))


for fam in F.CSALADOK:
    tan = F.jl(G2 / f"ert_tanito/items/{fam}.jsonl")
    tes = F.jl(G2 / f"ert_teszt/items/{fam}.jsonl")
    ya = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan])
    yb = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tes])
    xa, xb = [i["state"] for i in tan], [i["state"] for i in tes]
    print(f"\n== {fam}: tanító {len(tan)}, teszt {len(tes)}, (a) {int(yb.sum())}")
    print("nyers szöveg  char", round(auc("karakter", xa, ya, xb, yb), 4), " szó", round(auc("szó", xa, ya, xb, yb), 4))
    sa, sb = [sima(x) for x in xa], [sima(x) for x in xb]
    print("kisbetű, ékezet és szám nélkül  char", round(auc("karakter", sa, ya, sb, yb), 4), " szó", round(auc("szó", sa, ya, sb, yb), 4))
    print("csak az első 80 kar", round(auc("karakter", [x[:80] for x in sa], ya, [x[:80] for x in sb], yb), 4),
          " csak az utolsó 80 kar", round(auc("karakter", [x[-80:] for x in sa], ya, [x[-80:] for x in sb], yb), 4))
    for ny in ("hu", "en"):
        ma = np.array([i["lang"] == ny for i in tan])
        mb = np.array([i["lang"] == ny for i in tes])
        print(ny, "szó", round(auc("szó", [x for x, m in zip(sa, ma) if m], ya[ma], [x for x, m in zip(sb, mb) if m], yb[mb]), 4))
    r = np.random.default_rng(1)
    print("keverés-kontroll char", round(auc("karakter", sa, r.permutation(ya), sb, yb), 4))
    la, lb = np.array([len(x) for x, y in zip(xb, yb) if y]), np.array([len(x) for x, y in zip(xb, yb) if not y])
    print("hossz medián (a)", int(np.median(la)), "(b)", int(np.median(lb)))
    pv = {}
    for i in tes:
        e = i["meta"]["ertelmezes"]
        pv.setdefault(e["egyseg"], {})[e["alt"] + str(e.get("valtozat", ""))] = i["state"]
    u = next(v for k, v in pv.items() if ":hu:" in k and len(v) >= 2)
    for k in sorted(u)[:3]:
        print(f"  [{k}] {u[k][:420]!r}")
