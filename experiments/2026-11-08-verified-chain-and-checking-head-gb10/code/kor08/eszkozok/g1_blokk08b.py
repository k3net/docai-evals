"""08 G1 — célzott blokkpróba a téves SELECT-ek ellen (Dani 11-02: a v1 blokk a T500-on nettó +9 NO_MATCH → SELECT;
„az összegfeltétel teljesül” könnyen „a jelölt helyes” jelentést kap). A szabálycsalád blokk-változatai
(`lanc08.BLOKK_VALTOZAT`) orákulum-úton, két megismert mintán: a K3 diag (199 MATCH, a v1 itt vitte el a 34 MATCH → X
hibát) és a 06 T500 (természetes összetétel, 300 MATCH, 100 NO_MATCH, 50–50 MISSING_DATA / OUT_OF_SCOPE). Az alany B1-4S
döntése; a helyesség az eredeti itemhez (`g1_dontes08.helyes`). A választás Dani döntése a két minta együtt alapján.

A v1 T500-kiolvasása a K08G1A3-é (a K08G1E-ben `o06`-ról `o06v1`-re átnevezve, mert az `o06` azóta a v4 blokké), a
többi változaté külön (`o06v0`, `o06v2`…). A v0 újraolvasása
determinizmus-ellenőrzés is: a K3-on 164, a T500-on 409 helyes volt (`blokk_valtozatok.json`, `dontesek_v1.json`).
  python3 kor08/eszkozok/g1_blokk08b.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import b1rel07 as R  # noqa: E402
import g1_dontes08 as G  # noqa: E402
import lanc08 as L  # noqa: E402

FAM = L.SZAB
MINTAK = {  # minta → (forrás, szelet, {változat: kiolvasási előtag})
    "K3 diag": ("K3diag", "DIAG", {"v0": "oK3v0", "v1": "oK3v1", "v2": "oK3v2", "v3": "oK3v3", "v4": "oK3v4"}),
    "T500": ("06", "T500", {"v0": "o06v0", "v1": "o06v1", "v2": "o06v2", "v3": "o06v3", "v4": "o06v4"}),
}
KORABBI = {("K3 diag", "v0"): 164, ("T500", "v0"): 409}  # a korábbi kiolvasás helyes száma (determinizmus)
HOZ = {"v0": "a v0-hoz", "v1": "a v1-hez"}


def dontesek(src: str, szelet: str, elo: str, jell: Path, temp: float) -> dict[str, tuple[bool, str]]:
    by = R.rows4(f"{elo}_{FAM}_{szelet}", jell)
    out = {}
    for _, it in L.betolt(src, FAM):
        if it["split"] != szelet:
            continue
        d = R.decide4(by[it["id"]], temp)
        out[it["id"]] = (G.helyes(d, it["content_state"], it["gold"]), f"{it['content_state']}→{d['kind']}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jell", default="cache/k08/jellemzok")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    temp = json.loads((EXP / "cache/k07/fejek/temperature.json").read_text())["B1-4"]
    res: dict = {}
    sor = ["# G1 — célzott blokkpróba a téves SELECT-ek ellen (szabálycsalád, orákulum-út, B1-4S)", "",
           "v0 az eredeti blokk; v1 kimondja, melyik kiszámított értéket kell az összeghatárhoz mérni; v2 pontonként: az",
           "összegfeltétel teljesül; v3 a v1 + az összeghatár alapján nem kizárt pontok + a költségnemet a rendszer nem",
           "ellenőrizte; v4 a v1 + pontonként: összeghatár teljesül, a költségnem nincs ellenőrizve. Megismert adat,",
           "fejlesztési számok; a választás Dani döntése a két minta együtt alapján.", ""]
    for minta, (src, szelet, elok) in MINTAK.items():
        d = {v: dontesek(src, szelet, elo, EXP / a.jell, temp) for v, elo in elok.items()}
        allapot = Counter(k.split("→")[0] for _, k in d["v0"].values())
        r = {}
        for v, dv in d.items():
            hibak = Counter(k for ok, k in dv.values() if not ok)
            r[v] = {"n": len(dv), "helyes": sum(ok for ok, _ in dv.values()), "hibak": dict(hibak.most_common()),
                    "allapotonkent": {s: sum(ok for ok, k in dv.values() if k.startswith(s + "→")) for s in allapot},
                    **{f"{HOZ[b]}: javult": sum(dv[i][0] and not d[b][i][0] for i in dv) for b in HOZ},
                    **{f"{HOZ[b]}: romlott": sum(d[b][i][0] and not dv[i][0] for i in dv) for b in HOZ},
                    "romlott_a_v0-hoz": sorted(i for i in dv if d["v0"][i][0] and not dv[i][0])}
        res[minta] = {"allapotok": dict(allapot), "valtozatok": r,
                      "determinizmus": {f"{v}: korábban {k}, most": r[v]["helyes"]
                                        for (m, v), k in KORABBI.items() if m == minta}}
        sor += [f"## {minta} (n = {len(d['v0'])}; " + ", ".join(f"{s} {n}" for s, n in allapot.most_common()) + ")", "",
                "| változat | helyes | " + " | ".join(f"{s} helyes" for s, _ in allapot.most_common()) +
                " | a v0-hoz: javult / romlott | a v1-hez: javult / romlott | hibák |",
                "|---|---|" + "---|" * len(allapot) + "---|---|---|"]
        for v, x in r.items():
            sor.append(f"| {v} | {x['helyes']} / {x['n']} | " +
                       " | ".join(f"{x['allapotonkent'][s]} / {allapot[s]}" for s, _ in allapot.most_common()) +
                       f" | {x['a v0-hoz: javult']} / {x['a v0-hoz: romlott']} | {x['a v1-hez: javult']} / "
                       f"{x['a v1-hez: romlott']} | " + "; ".join(f"{k} {n}" for k, n in x["hibak"].items()) + " |")
        for k, v in res[minta]["determinizmus"].items():
            sor.append(f"\nDeterminizmus, v0 újraolvasva: {k} {v}.")
        sor.append("")
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "blokk_proba2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "blokk_proba2.md").write_text("\n".join(sor) + "\n", encoding="utf-8")
    print("\n".join(sor))


if __name__ == "__main__":
    main()
