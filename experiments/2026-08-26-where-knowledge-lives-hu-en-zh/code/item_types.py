#!/usr/bin/env python3
"""Kérdéstípus-annotáció és a belőle számolt érzékenységi bontás.

    python3 code/item_types.py            # a besorolás és a típusonkénti pontosság
    python3 code/item_types.py --ids      # csak az itemazonosítók típusonként

Miért van erre külön szkript: a ZH-csoportban a kérdések nagy része „melyik tartományban
van X" alakú, a HU- és a UNI-csoportban viszont EGY SEM. Ez a fő aszimmetria-állítás
(ZH-only → magyarul vs. HU-only → kínaiul) mellé odakívánkozó zavaró tényező.

⛔⛔ A szabály SZÁNDÉKOSAN eredményfüggetlen: kizárólag a MAGYAR kérdés kezdetére illeszt,
a válaszok, a pontszámok és a találatok ismerete nélkül. Egy utólag, a találatok láttán
összeállított „tisztított részhalmaz" konzervatív irányba is torzíthat, de akkor sem
reprodukálható — és ami nem reprodukálható, azt nem szabad arányként közölni. Ha a szabályt
módosítod, MINDEN azonos típusú itemre alkalmazd, ne csak azokra, ahol volt találat.

⚠️ A típusonkénti pontosság-bontás UTÓLAGOS, feltáró elemzés. Nem előregisztrált, és a
részcsoportok kicsik (n = 8 és n = 11), tehát irányt mutat, nem dönt el.
"""
import argparse
import csv
import json
import pathlib
import re

import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent

# A kérdés egy helyhez tartozó közigazgatási egységet kér — a legáltalánosabb,
# leginkább „köztudás" jellegű kérdésforma a korpuszban.
GEO_RULE = re.compile(r"^Melyik (tartomány|város|nagyváros)", re.I)
ROUNDS = (("base", "results"), ("instruct+chat", "results_instruct"),
          ("instruct+nyers", "results_instruct_raw"))


def classify():
    items = {}
    for line in scope_paths.data(HERE, "items.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            items[r["id"]] = (r["group"], bool(GEO_RULE.match(r["q"]["hu"])))
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", action="store_true", help="csak az itemazonosítók")
    args = ap.parse_args()
    items = classify()

    print(f"Szabály: a magyar kérdés illeszkedik-e erre: {GEO_RULE.pattern!r}\n")
    for g in ("ZH", "HU", "UNI", "UNT"):
        ids = [i for i, (grp, _) in items.items() if grp == g]
        geo = [i for i in ids if items[i][1]]
        if not ids:
            continue
        print(f"{g}: {len(geo)}/{len(ids)} hely→közigazgatási egység"
              + (f" — {', '.join(sorted(geo))}" if geo else ""))
    if args.ids:
        return

    print("\nÉrzékenységi bontás — szigorú pontosság a ZH-csoportban (UTÓLAGOS elemzés):\n")
    print(f"  {'kör':16s} {'nyelv':6s} {'hely→közig.':>14s} {'egyéb':>12s}")
    for label, res in ROUNDS:
        path = HERE / res / "scores.csv"
        if not path.exists():
            print(f"  {label:16s} — nincs scores.csv, kihagyva")
            continue
        rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
        for lang in ("hu", "en", "zh"):
            cells = []
            for want_geo in (True, False):
                sub = [r for r in rows if r["group"] == "ZH" and r["lang"] == lang
                       and items.get(r["item_id"], (None, None))[1] is want_geo]
                k = sum(r["final"].strip() == "helyes" for r in sub)
                cells.append(f"{k}/{len(sub)} = {100 * k / len(sub):.0f} %" if sub else "—")
            print(f"  {label:16s} {lang:6s} {cells[0]:>14s} {cells[1]:>12s}")
    print("\n⚠️ n = 11 és n = 8 — irányt mutat, nem dönt el. A HU- és a UNI-csoportban")
    print("   nincs ilyen típusú kérdés, tehát a ZH↔HU összevetés típusban sem kiegyensúlyozott.")


if __name__ == "__main__":
    main()
