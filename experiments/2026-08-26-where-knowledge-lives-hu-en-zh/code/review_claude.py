#!/usr/bin/env python3
"""Második, FÜGGETLEN gépi bírálat a ZH + HU csoportra (Claude, más modellcsalád).

    python3 code/review_claude.py

⚠️ Ez NEM a runbook §2 ellenőrző köre — az az én dolgom, és a `manual` oszlop az enyém marad.
Ez egy második vélemény attól a modelltől, amelyik nem rokona sem a vizsgált modellnek
(Qwen3.5-9B), sem az első bírálónak (Qwen3.6-35B). Haszna kettős:
  * mérhető egyetértés → a bíráló megbízhatóságának becslése,
  * a ellenőrző körömet a VITÁS tételekre szűkíti (102 helyett néhány darab).

Az alábbi lista a teljes 102 válasz átolvasása után készült; ahol nem szerepel tétel,
ott a második bíráló egyetért az elsővel.
"""
import csv
import json
import pathlib
from collections import Counter
import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent

# (item, lang): (eltérő ítélet, indoklás)
# ⛔ VISSZAVONVA 2026-08-24 este, a bíráló-szigorítási kísérlet során (mindhárom az ÉN hibám volt):
#   ZH10/hu — a válasz IGENIS dönt: „A helyes válasz: C. A Duanwu-fesztivál", és a várt válasz épp Duanwu.
#             A feleletválasztós felsorolás önértékelő műtermék, nem határozatlanság.
#   HU07/zh — a NYERS szövegre ítéltem; a `clean_answers.py` utáni válasz egyetlen mondat
#             („kőttes是一种用酵母面团制作的匈牙利点心"), amiben nincs önellentmondás. 酵母面团 ≈ 发酵面团.
#   HU04/en — elavult: a bíráló a `clean_answers.py` utáni újrafuttatásban már „helytelen"-t mond,
#             tehát nincs eltérés. (Az őr most ki is írja, ha ilyen bejegyzés marad bent.)
# Tanulság: a második bírálói kört UGYANARRA a szövegre kell futtatni, amit a bíráló látott —
# ezért mutatja a `review_sheet.py` mostantól a `text_clean`-t.
ELTERES = {
    ("ZH08", "en"): ("reszben",
                     "Két alapanyagból az egyik (glutinous rice) helyes, a másik (red beans) téves — "
                     "a várt: vörös datolya."),
    ("HU08", "en"): ("reszben",
                     "„Christmas (during the Christmas season)” — a várt válasz karácsony ÉS újév KÖZÖTT; "
                     "az időszak nagyjából stimmel, a pontos ablak nem."),
    ("HU13", "hu"): ("reszben",
                     "„magyar juhász” — a puli valóban magyar juhászkutya, tehát a kategória helyes, "
                     "de a kérdés a fajtára ment, és azt nem nevezi meg."),
    # hallucináció-átminősítések: a tartalom ugyanúgy téves, de a KATEGÓRIA más
    ("HU12", "hu"): ("hallucinacio", "„A nagy ho-ho-ho-horgász meséit József Attila írta” — magabiztos, konkrét kitaláció."),
    ("HU12", "en"): ("hallucinacio", "Miklós Radnóti + kitalált 1934-es kiadás — konkrét, téves adatok."),
    ("HU14", "hu"): ("hallucinacio", "Juhász Gyula + 1937-es megjelenés — mindkettő kitalált."),
    ("HU14", "en"): ("hallucinacio", "Mór Jókai + 1872 — kitalált szerző és évszám."),
    ("HU14", "zh"): ("hallucinacio", "„Ferenczy Ilona” — nem létező szerző erre a műre."),
    ("HU01", "en"): ("hallucinacio", "Részletes, magabiztos leírás egy kitalált szokásról (esküvői ajándékkosár)."),
    ("HU15", "en"): ("hallucinacio", "„Okleveles Kereskedő Jogi” — kitalált feloldás."),
    ("HU13", "en"): ("hallucinacio", "„Borz, a Hungarian sighthound” — nem létező fajta."),
    ("ZH07", "en"): ("hallucinacio", "Wuyi Mountain mint fő szentély, magabiztos részletekkel — kitalált."),
    ("ZH03", "en"): ("hallucinacio", "„Panda, Giant Panda, Giant Panda” — értelmetlen, kitalált felsorolás."),
}


def main():
    rows = [r for r in csv.DictReader((scope_paths.res(HERE) / "scores.csv").open(encoding="utf-8"))
            if r["group"] in ("ZH", "HU")]
    out = []
    for r in rows:
        key = (r["item_id"], r["lang"])
        verdict, why = ELTERES.get(key, (r["judge"], ""))
        out.append({"item_id": r["item_id"], "group": r["group"], "lang": r["lang"],
                    "judge": r["judge"], "review_claude": verdict,
                    "egyetert": int(verdict == r["judge"]), "indoklas": why})

    # ⛔ ŐR: ha egy ELTERES-bejegyzésre a bíráló IDŐKÖZBEN ugyanazt kezdte mondani (pl. a
    # clean_answers.py utáni újrafuttatás miatt), az már nem eltérés — a listát frissíteni kell,
    # különben egy elavult ELTERES-bejegyzés a riportban eltérésként jelenne meg.
    stale = [k for k, (v, _) in ELTERES.items()
             if k in {(r["item_id"], r["lang"]): r for r in rows} and
             {(r["item_id"], r["lang"]): r for r in rows}[k]["judge"] == v]
    if stale:
        print("⚠️ elavult ELTERES-bejegyzés (a bíráló már ugyanazt mondja): "
              + ", ".join(f"{a}/{b}" for a, b in stale))

    p = scope_paths.res(HERE) / "review_claude.csv"
    with p.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["item_id", "group", "lang", "judge", "review_claude", "egyetert", "indoklas"])
        w.writeheader()
        w.writerows(out)

    agree = sum(r["egyetert"] for r in out)
    print(f"{len(out)} válasz · egyetértés a 35B bírálóval: {agree}/{len(out)} = {agree/len(out):.1%}")
    # a pontosságot ténylegesen módosító eltérések (helyes ↔ nem helyes)
    flip = [r for r in out if (r["judge"] == "helyes") != (r["review_claude"] == "helyes")]
    print(f"a pontosságot MÓDOSÍTÓ eltérés: {len(flip)}")
    for r in flip:
        print(f"  ⚠️ {r['item_id']}/{r['lang']}: bíráló={r['judge']} → második bíráló={r['review_claude']}")
    print(f"\ncsak kategória-átsorolás (helytelen → hallucináció): "
          f"{sum(1 for r in out if not r['egyetert'] and r not in flip and r['review_claude']=='hallucinacio')}")
    print("második bíráló eloszlása:", dict(Counter(r["review_claude"] for r in out)))
    print(f"→ {p}")


if __name__ == "__main__":
    main()
