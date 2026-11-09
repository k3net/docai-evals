"""08 G5 utólag (11-05; nem rögzített) — a módérzékenységi próba összevetése: a G5 fő számai az R-módú kiolvasáson és az
A, B módú kiolvasásokon (`k08g5m.sh`), és szeletenként, hány item döntése fordul R-hez képest. Leíró; a fő eredmény az
R-módú G5.

  python3 kor08/eszkozok/modszenz08.py --out kor08/eredmenyek/G5_modszenz/osszevetes.md
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
MODOK = {"R": ("kor08/eredmenyek/G5", "cache/k08/pecset/pontoz"),
         "A": ("kor08/eredmenyek/G5_modszenz/A", "cache/k08/modszenz/A/pontoz"),
         "B": ("kor08/eredmenyek/G5_modszenz/B", "cache/k08/modszenz/B/pontoz")}
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
SZAB = "szabaly.koltsegelszamolas"
FO = "L-RN − L-S"


def sz(x: float, d: int = 3) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def pc(x: float) -> str:
    return "–" if x != x else f"{100 * x:.1f}%".replace(".", ",")


def iv(c: list, f=sz) -> str:
    return f"[{f(c[0])}; {f(c[1])}]"


def g(mod: str, k: str) -> dict:
    return json.loads((EXP / MODOK[mod][0] / k / f"g5_{k}.json").read_text(encoding="utf-8"))


def dontes(mod: str, szelet: str) -> dict:
    return json.loads((EXP / MODOK[mod][1] / f"{szelet}.json").read_text())["keret4"]["dontes"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    K1, K2, K3 = ({m: g(m, k) for m in MODOK} for k in ("k1", "k2", "k3"))
    o = ["# 08 G5 utólag — módérzékenység (leíró)", "",
         "Ugyanazok a fejek (R-módon tanítva), a pontozás és a rögzített elemzők, csak a zárt kiolvasás módja más. A τ és a "
         "temperature a mód saját CAL-ján áll be. A fő eredmény az R-módú G5.", "",
         "## A két fő próba (L-RN − L-S, szabálycsalád)", "",
         "| mód | ág | ΔAUROC | 95% | olvasat | L-RN | L-S | esemény |", "|---|---|---|---|---|---|---|---|"]
    for m in MODOK:
        c = K1[m]["csaladok"][SZAB]
        for ag in ("K1a", "K1b"):
            p = c["parok"][FO][ag]
            o.append(f"| {m} | {ag} | {sz(p['delta'])} | {iv(p['ci95'])} | {p['olvasat']} | {sz(c['karok']['L-RN'][ag]['auroc'])} | "
                     f"{sz(c['karok']['L-S'][ag]['auroc'])} | {c['esemeny'][ag]['pozitiv']} / {c['esemeny'][ag]['negativ']} |")
    o += ["", "## K2: a helyes arány a kinyert úton", "", "| mód | " + " | ".join(CSALADOK) + " |", "|---|---|---|---|"]
    for m in MODOK:
        o.append(f"| {m} | " + " | ".join(f"{pc(K2[m]['csaladok'][f]['pont']['kinyert'])} (lánc nélkül {pc(K2[m]['csaladok'][f]['pont']['nelkul'])})"
                                          for f in CSALADOK) + " |")
    o += ["", "## K3: hasznos lefedettség és lezárási hiba", "",
          "| család | mód | L-RN | L-RN hiba | L-S | L-S hiba | B1-4R | B1-4R hiba | L-RN − L-S | 95% | L-RN − B1-4R | 95% | hibafeltétel (L-RN) |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in CSALADOK:
        for m in MODOK:
            c = K3[m]["csaladok"][f]
            p = {k: c["pont"][k] for k in ("L-RN", "L-S", "B1-4R")}
            d, e = c["parok"][FO]["hasznos_lef"], c["parok"]["L-RN − B1-4R"]["hasznos_lef"]
            o.append(f"| {f} | {m} | {pc(p['L-RN']['hasznos_lef'])} | {pc(p['L-RN']['lezarasi_hiba'])} | {pc(p['L-S']['hasznos_lef'])} | "
                     f"{pc(p['L-S']['lezarasi_hiba'])} | {pc(p['B1-4R']['hasznos_lef'])} | {pc(p['B1-4R']['lezarasi_hiba'])} | {pc(d['delta'])} | "
                     f"{iv(d['ci95'], pc)} | {pc(e['delta'])} | {iv(e['ci95'], pc)} | {c['hibafeltetel']['L-RN']} |")
    o += ["", "## Az (a)-ból τ fölött lezárt arány", "", "| család | mód | L-RN | L-S |", "|---|---|---|---|"]
    for f in CSALADOK:
        for m in MODOK:
            t = K1[m]["csaladok"][f]["a_lezart_tau_felett"]
            o.append(f"| {f} | {m} | {pc(t['L-RN'])} | {pc(t['L-S'])} |")
    o += ["", "## Döntésfordulás R-hez képest (a modell döntése: fajta és jelölt)", "",
          "| szelet | n | A: eltér | A: helyesség eltér | B: eltér | B: helyesség eltér |", "|---|---|---|---|---|---|"]
    ossz = {m: [0, 0, 0] for m in ("A", "B")}
    for f in CSALADOK:
        for s in (f"lG2F_{f}_TESZT", f"nG2F_{f}_TESZT", f"lG2K3_{f}_G2K3", f"lG2T_{f}_G2T"):
            r = dontes("R", s)
            sor = [s, str(len(r))]
            for m in ("A", "B"):
                d = dontes(m, s)
                el = sum((r[i]["kind"], r[i]["cand"]) != (d[i]["kind"], d[i]["cand"]) for i in r)
                he = sum(bool(r[i]["helyes"]) != bool(d[i]["helyes"]) for i in r)
                sor += [str(el), str(he)]
                ossz[m] = [ossz[m][0] + len(r), ossz[m][1] + el, ossz[m][2] + he]
            o.append("| " + " | ".join(sor) + " |")
    o.append("| **összesen** | " + f"{ossz['A'][0]} | {ossz['A'][1]} | {ossz['A'][2]} | {ossz['B'][1]} | {ossz['B'][2]} |")
    p = EXP / a.out
    p.write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"→ {a.out}")


if __name__ == "__main__":
    main()
