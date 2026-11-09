"""08 erősebb kontroll (N) — az illesztés ellenőrzése, a fejek eredménye nélkül, csak szöveg: az (a'') a (b'') ellen, a `felszin08m` próbáival. A friss modell CV-je a forgatókönyv-párok szerint csoportosít, mert a párok
mondatai a két osztályban cserélődnek. **Az elfogadás küszöbei a generálás előtt rögzítve, az M-éi:** hossz ≤ 0,60; a régi szöveges modell ≤ 0,70; a friss modell ≤ 0,80.
  python3 kor08/eszkozok/felszin08n.py --out kor08/eredmenyek/N/felszin
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import felszin08 as F  # noqa: E402
import felszin08m as M  # noqa: E402

G2 = F.EXP / "kor08/adat/G2"
N = F.EXP / "kor08/adat/N"
FAM = "szabaly.koltsegelszamolas"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    it = F.jl(N / f"items/{FAM}.jsonl")
    tan = F.jl(G2 / f"ert_tanito/items/{FAM}.jsonl")
    x = [F.szoveg(i) for i in it]
    y = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in it])
    g = np.array(["|".join(sorted((i["meta"]["ertelmezes"]["forgatokonyv"], i["meta"]["illesztes"]["par"]))) for i in it])
    xt = [F.szoveg(i) for i in tan]
    yt = np.array([i["meta"]["ertelmezes"]["alt"] == "a" for i in tan])
    gt = np.array([i["template_group_id"] for i in tan])
    r: dict = {"n_a": int(y.sum()), "n_b": int((~y).sum()), "parok": len(set(g)), "hossz": M.hajtott(y, [len(s) for s in x]),
               "median_hossz": {"a": float(np.median([len(i["state"]) for i, q in zip(it, y) if q])), "b": float(np.median([len(i["state"]) for i, q in zip(it, y) if not q]))}}
    for t in ("szó", "karakter"):
        m, _, _ = F.illeszt(t, xt, yt, gt)
        r[f"regi_{t}"] = float(roc_auc_score(y, m.predict_proba(x)[:, 1]))
        r[f"friss_{t}"], s = M.friss(t, x, y, g)
        for ny in ("hu", "en"):
            q = np.array([i["lang"] == ny for i in it])
            r[f"friss_{t}_{ny}"] = float(roc_auc_score(y[q], s[q]))
    p = F.pipe("szó", 10.0).fit(x, y)
    v, lr = p.steps[0][1], p.steps[1][1]
    o = np.argsort(lr.coef_[0])
    t = v.get_feature_names_out()
    r["szavak_a"], r["szavak_b"] = [str(t[i]) for i in o[::-1][:25]], [str(t[i]) for i in o[:25]]
    r["regi"], r["friss"] = max(r["regi_szó"], r["regi_karakter"]), max(r["friss_szó"], r["friss_karakter"])
    ok = all(r[k] <= v_ for k, v_ in M.HATAR.items())
    z = M.sz
    l = ["# 08 N — az illesztés ellenőrzése", "", f"**{'Elfogadva' if ok else 'Nem elfogadva'}** (hossz {z(r['hossz'])}, régi {z(r['regi'])}, friss {z(r['friss'])}; küszöbök 0,60 / 0,70 / 0,80).", "",
         f"(a'') {r['n_a']}, (b'') {r['n_b']}, {r['parok']} forgatókönyv-pár. Medián hossz: {r['median_hossz']['a']:.0f} / {r['median_hossz']['b']:.0f}.", "",
         "| próba | szó | karakter |", "|---|---|---|", f"| régi modell | {z(r['regi_szó'])} | {z(r['regi_karakter'])} |", f"| friss modell, CV | {z(r['friss_szó'])} | {z(r['friss_karakter'])} |",
         f"| friss, magyar | {z(r['friss_szó_hu'])} | {z(r['friss_karakter_hu'])} |", f"| friss, angol | {z(r['friss_szó_en'])} | {z(r['friss_karakter_en'])} |", "",
         "Az (a'') felé húzó szavak: " + ", ".join(r["szavak_a"]), "", "A (b'') felé húzó szavak: " + ", ".join(r["szavak_b"]), ""]
    d = F.EXP / a.out
    d.mkdir(parents=True, exist_ok=True)
    (d / "illesztes.json").write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "illesztes.md").write_text("\n".join(l) + "\n", encoding="utf-8")
    print("\n".join(l))


if __name__ == "__main__":
    main()
