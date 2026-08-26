#!/usr/bin/env python3
"""A pontozó CSV-k invariánsainak őre — a `final` oszlop SZÁRMAZTATOTT, nem önálló adat.

    python3 code/check_scores.py            # ellenőrzés; hiba esetén 1-es kilépőkód
    python3 code/check_scores.py --fix      # a `final` oszlop újraszámolása, majd ellenőrzés

⛔ Miért kell ez? A `scores.csv`-ben három ítélet-oszlop van, és KETTŐ közülük forrás:

    judge   — a gépi bíráló (Qwen3.6-35B) ítélete
    manual  — az ellenőrző kör (GPT-5.6 Sol) ítélete, üres ott, ahol nem volt újraítélve
    final   — SZÁRMAZTATOTT: `manual`, ha nem üres, különben `judge`

Az elemzők (`analyze_a.py`, `compare_rounds.py`) a `final`-t menet közben újraszámolják, ezért
a riportok akkor is helyesek voltak, amikor a lemezre írt oszlop elavult. Aki viszont a
publikált CSV-t olvassa és a `final` oszlopra csoportosít, MÁS számokat kap, mint a riportok:
pontosan ez történt, 45-45 soron a `results` és a `results_instruct` körben, ahol az
ellenőrző kör eltért a bírálótól, de a `final` a bíráló ítéletén maradt.

Ez a szkript az egyetlen hely, ahol a származtatás szabálya ki van mondva; a `--fix` ezt írja
vissza a fájlba, ellenőrzés nélküli futás pedig némán SOSE javít.
"""
import argparse
import csv
import pathlib
import sys

csv.field_size_limit(10 ** 7)

HERE = pathlib.Path(__file__).resolve().parent.parent
VARIANTS = ("results", "results_instruct", "results_instruct_raw")
VERDICTS = ("helyes", "reszben", "helytelen", "hallucinacio")
REQUIRED = ("item_id", "group", "lang", "judge", "manual", "final")


def derive(row):
    """A `final` egyetlen érvényes definíciója. Minden más hely ezt hivatkozza."""
    return (row.get("manual") or "").strip() or (row.get("judge") or "").strip()


def check(path, fix=False):
    """Visszaadja a hibák listáját; `fix` esetén előbb újraírja a származtatott oszlopot."""
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows, fields = list(reader), reader.fieldnames
    problems = []

    for col in REQUIRED:
        if col not in (fields or []):
            problems.append(f"hiányzó oszlop: {col}")
    if problems:
        return problems, 0

    if fix:
        changed = 0
        for r in rows:
            want = derive(r)
            if (r.get("final") or "").strip() != want:
                r["final"] = want
                changed += 1
        if changed:
            with path.open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                w.writerows(rows)
    else:
        changed = 0

    seen = set()
    for r in rows:
        key = (r["item_id"], r["lang"])
        if key in seen:
            problems.append(f"kettőzött sor: {key[0]}/{key[1]}")
        seen.add(key)
        for col in ("judge", "final"):
            v = (r.get(col) or "").strip()
            if v not in VERDICTS:
                problems.append(f"{key[0]}/{key[1]}: ismeretlen {col} ítélet: {v!r}")
        man = (r.get("manual") or "").strip()
        if man and man not in VERDICTS:
            problems.append(f"{key[0]}/{key[1]}: ismeretlen manual ítélet: {man!r}")
        if (r.get("final") or "").strip() != derive(r):
            problems.append(f"{key[0]}/{key[1]}: final={r['final']!r}, "
                            f"pedig manual={man!r} / judge={r['judge']!r} → {derive(r)!r}")
    return problems, changed


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix", action="store_true",
                    help="a származtatott `final` oszlop újraírása a fájlokban")
    args = ap.parse_args()

    total = 0
    for name in VARIANTS:
        path = HERE / name / "scores.csv"
        if not path.exists():
            print(f"⚠️  {name}/scores.csv — nincs meg, kihagyva")
            continue
        problems, changed = check(path, fix=args.fix)
        total += len(problems)
        tag = f" ({changed} sor újraírva)" if changed else ""
        if problems:
            print(f"❌ {name}/scores.csv — {len(problems)} hiba{tag}")
            for p in problems[:20]:
                print(f"     {p}")
            if len(problems) > 20:
                print(f"     … és további {len(problems) - 20}")
        else:
            print(f"✅ {name}/scores.csv — final == (manual or judge) minden soron{tag}")

    if total:
        print("\nA `final` oszlop származtatott: futtasd `--fix`-szel, majd az elemzőket újra.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
