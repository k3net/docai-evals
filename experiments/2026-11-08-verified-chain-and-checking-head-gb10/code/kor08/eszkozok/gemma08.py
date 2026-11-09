"""08 G2 — a Gemma 4 második ítéletének összesítése a G2 minden itemjén (G1-rögzítés 5.4: Gemma-triage mind az itemen),
a 06 `gemma06` burkolása 08-as útvonalakkal (a 06 kódja változatlan; mint a `gemma07`). A kiolvasás a spark-deven fut (a
03 `kiolvaso03` ids-módja: gold és item-id nélküli prompt, négy opciósorrend), ez a script részenként összesít:
  - itemenként a négy sorrend átlaga, a Gemma választása és az egyezés a konstrukció címkéjével (a Gemma keretében csak
    „egyik sem” van: a NO_MATCH, a MISSING_DATA és az OUT_OF_SCOPE egyaránt X; az értelmezési (a) goldja is X);
  - bontás család × állapot × nyelv × szelet szerint, a legkisebb egyezésű sabloncsoportok;
  - az eltérő itemek listája (`kor08/adat/G2/<rész>/gemma/eltero.jsonl`): ebből a jelzett auditminta (`audit08g2`; csak
    a (b) eltérése jelöl, Dani 11-04);
  - az értelmezési részeken leíróan: az (a)-n a Gemma választása (egyik sem / a gold költségneme / a csalié / más; a
    Gemma keretében nincs Y, ezért az (a) „eltérése” nem címkehiba-jel), és a (b) egyezése a jel fajtája szerint
    (`forgatokonyv08_szab.jel_fajta`), a szabálycsaládon forgatókönyvenként.
Triage: itemet nem töröl, nem javít (D15).

  python3 kor08/eszkozok/gemma08.py --resz ert_teszt --olvasas kor08/eredmenyek/G2/gemma/ert_teszt.jsonl
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor06/eszkozok")]
import forgatokonyv08_szab as FK  # noqa: E402
import gemma06 as G  # noqa: E402
import szint06 as S6  # noqa: E402

RESZEK = ("friss", "k3", "ert_teszt", "ert_tanito")


def ertelmezes_leiro(a) -> list[str]:
    """Az (a) Gemma-választása és a (b) egyezése jelfajta szerint (leíró); a sorok az összesítő végére."""
    t = float(json.loads(G.TEMP_FORRAS.read_text())["tanarkapu"]["gemma"]["temp"])
    by = collections.defaultdict(list)
    for p in a.olvasas:
        for r in G.jl(Path(p)):
            by[r["id"]].append(r)
    fk = {(f["id"], lang): f for lang, fs in FK.forgatokonyvek().items() for f in fs}
    fajta = FK.jel_fajtak()
    av, bv, fsor = collections.Counter(), collections.defaultdict(list), collections.defaultdict(collections.Counter)
    for fam in G.CSALADOK:
        for it in G.jl(G.ITEMS / f"{fam}.jsonl"):
            rows = sorted(by.get(it["id"], []), key=lambda r: r["perm"])
            if [r["perm"] for r in rows] != list(G.PERMS):
                continue
            e, pick = it["meta"]["ertelmezes"], G.itelet(rows, t)["pick"]
            f = fk.get((e.get("forgatokonyv"), it["lang"])) if fam == "szabaly.koltsegelszamolas" else None
            if e["alt"] == "a":
                kat = "egyik sem" if pick is None else "opció"
                if f and pick is not None:
                    txt = next(o["text"] for o in it["options"] if o["id"] == pick).lower()
                    k = next((k for k, v in S6.SZAB_TIPUS[it["lang"]].items() if v.lower() in txt), None)
                    kat = "gold" if k == f["gold"] else "csali" if k == f["csali"] else "más"
                av[(fam, it["lang"], kat)] += 1
                if f:
                    fsor[e["forgatokonyv"]][f"a:{kat}"] += 1
            else:
                jf = fajta[(e["forgatokonyv"], it["lang"])] if f else "–"
                bv[(fam, jf)].append(pick == it["gold"])
                if f:
                    fsor[e["forgatokonyv"]]["b:n"] += 1
                    fsor[e["forgatokonyv"]]["b:egyezik"] += pick == it["gold"]
    o = ["", "## Értelmezési változatok (leíró; Dani 11-04)", "",
         "Az (a)-n a Gemma választása (a keretében nincs Y, ezért az (a) eltérése nem jelöl auditra):", "",
         "| család | nyelv | választás | db |", "|---|---|---|---|"]
    o += [f"| {fam} | {lang} | {kat} | {n} |" for (fam, lang, kat), n in sorted(av.items())]
    o += ["", "A (b) egyezése a jel fajtája szerint:", "", "| család | jel | egyezik |", "|---|---|---|"]
    o += [f"| {fam} | {jf} | {sum(x)}/{len(x)} ({100 * sum(x) / len(x):.0f}%) |" for (fam, jf), x in sorted(bv.items())]
    if fsor:
        o += ["", "A szabálycsaládon forgatókönyvenként ((a): gold / csali / egyik sem; (b): egyezik / n):", "",
              "| forgatókönyv | (a) gold | (a) csali | (a) egyik sem | (b) egyezik |", "|---|---|---|---|---|"]
        o += [f"| {k} | {c['a:gold']} | {c['a:csali']} | {c['a:egyik sem']} | {c['b:egyezik']}/{c['b:n']} |"
              for k, c in sorted(fsor.items())]
    (G.OUT / "ertelmezes_leiro.json").write_text(json.dumps(
        {"a": {"|".join(k): v for k, v in av.items()}, "b_jelfajta": {"|".join(k): [sum(x), len(x)] for k, x in bv.items()},
         "forgatokonyv": {k: dict(c) for k, c in fsor.items()}}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return o


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--resz", required=True, choices=RESZEK)
    ap.add_argument("--olvasas", nargs="+", required=True)
    ap.add_argument("--max-hianyos", type=int, default=0)
    ap.add_argument("--sablon-top", type=int, default=15)
    a = ap.parse_args()
    G.ITEMS = EXP / "kor08/adat/G2" / a.resz / "items"
    G.AUDIT = {}  # a 08 auditja a saját kulcsaival dolgozik (`audit08g2`); a Gemma ítélete az eltero.jsonl-ből
    G.OUT = EXP / "kor08/eredmenyek/G2/gemma" / a.resz
    G.JELOLT = EXP / "kor08/adat/G2" / a.resz / "gemma"
    G.cmd_osszesit(a)
    md = G.OUT / "osszesito.md"
    szoveg = md.read_text(encoding="utf-8").replace("# A Gemma második ítélete a friss családokon (06, F2)",
                                                     f"# A Gemma második ítélete a G2-n (08, {a.resz})")
    if a.resz.startswith("ert"):
        szoveg += "\n".join(ertelmezes_leiro(a)) + "\n"
    md.write_text(szoveg, encoding="utf-8")


if __name__ == "__main__":
    main()
