"""07-es kör, F0 — a 06 B1-R reprodukciójának ellenőrzése (07-runbook 2.1).

A 06 F5 a finomhangolt fejeket nem mentette, csak a pontszámokat (`cache/k06/f5/<család>/f1.json`). A 07 a B1-R-t
friss teszten újratanítja, ezért itt azt mérjük, hogy a `friss06 tanit` újrafuttatása (ugyanaz a T500, ugyanazok a
seedek) ugyanazokat a pontszámokat adja-e: kulcsonként a legnagyobb abszolút eltérés, a Pearson-korreláció és az
AURC (S+N) különbsége a teszten. A B1 saját sorai (id, javaslat, helyesség, q) bájtra azonosak kell legyenek.

  python3 kor07/eszkozok/repro07.py --regi cache/k06/f5 --uj cache/k07/f0_repro --out kor07/eredmenyek/F0
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")


def aurc(q: np.ndarray, cor: np.ndarray) -> float:
    """A 05 `aurc`-ja a teljes rangsoron: a csökkenő pontszám szerinti kumulált hibaarány átlaga."""
    o = np.argsort(-q, kind="stable")
    err = np.cumsum(~cor[o])
    return float((err / np.arange(1, len(q) + 1)).mean())


def osszevet(regi: dict, uj: dict) -> dict:
    out = {"b1_azonos": {}, "pontszam": {}}
    for t, b in regi["B1"].items():
        out["b1_azonos"][t] = all(b[k] == uj["B1"][t][k] for k in ("ids", "javaslat", "helyes", "helyes_enyhe", "q"))
    for k, v in regi["pontszam"].items():
        if k not in uj["pontszam"]:
            out["pontszam"][k] = {"hianyzik": True}
            continue
        a, b = np.array(v, float), np.array(uj["pontszam"][k], float)
        t = k.rsplit("|", 1)[1]
        cor = np.array(regi["B1"][t]["helyes"], bool)
        out["pontszam"][k] = {"max_elteres": float(np.abs(a - b).max()), "pearson": float(np.corrcoef(a, b)[0, 1]),
                              "aurc_regi": aurc(a, cor), "aurc_uj": aurc(b, cor), "d_aurc": aurc(b, cor) - aurc(a, cor)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regi", required=True)
    ap.add_argument("--uj", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {}
    for fam in CSALADOK:
        p = Path(a.uj) / fam / "f1.json"
        if not p.exists():
            res[fam] = {"hianyzik": True}
            continue
        res[fam] = osszevet(json.loads((Path(a.regi) / fam / "f1.json").read_text()), json.loads(p.read_text()))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "repro.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = ["# 07 F0 — a 06 B1-R reprodukciója", "",
             "| család | kulcs | max |Δpontszám| | Pearson | AURC régi | AURC új | ΔAURC |", "|---|---|---|---|---|---|---|"]
    for fam, r in res.items():
        if r.get("hianyzik"):
            lines.append(f"| {fam} | hiányzik | | | | | |")
            continue
        for k, v in r["pontszam"].items():
            if not k.startswith("B1-R|None") or not k.endswith("TESZT"):
                continue
            lines.append(f"| {fam} | {k} | {v['max_elteres']:.2e} | {v['pearson']:.6f} | {v['aurc_regi']:.4f} | "
                         f"{v['aurc_uj']:.4f} | {v['d_aurc']:+.5f} |")
        lines.append(f"| {fam} | a B1 sorai azonosak | {all(r['b1_azonos'].values())} | | | | |")
        worst = max(r["pontszam"].values(), key=lambda v: abs(v.get("d_aurc", 0)))
        lines.append(f"| {fam} | a legnagyobb ΔAURC bármely kulcson | | | | | {worst.get('d_aurc', 0):+.5f} |")
    (out / "repro.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
