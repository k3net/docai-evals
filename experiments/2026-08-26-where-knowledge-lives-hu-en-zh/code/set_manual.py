#!/usr/bin/env python3
"""Kézi ítélet beírása a pontozó CSV-kbe — a ellenőrző kör segédeszköze.

    python3 src/set_manual.py a  HU04 en helytelen           # Mérés A (162 faktuális válasz)
    python3 src/set_manual.py d  UNT-HU01 hu --native 2 --distortion 1   # D1 UNT-komponensek
    python3 src/set_manual.py c  UNT-HU01 hu rossz           # D1 kontrollszó ítélete
    python3 src/set_manual.py status                          # hol tartok?
    python3 src/set_manual.py a  HU04 en --clear              # ellenőrző ítélet visszavonása

Miért nem közvetlenül a CSV-t szerkesztjük? Mert a válasz-oszlop idézőjeleket, vesszőket és
sortöréseket tartalmaz — egy szövegszerkesztőben könnyű elrontani a sort, és a hiba némán
elronthat egy egész cellát a mátrixban. Ez a szkript csak a ellenőrző oszlophoz nyúl, mindent
validál (létező item/nyelv, engedett ítélet, komponens-szám ≤ maximum), és a fájl többi
része karakterre azonos marad.
"""
import argparse
import csv
import pathlib
import sys
import scope_paths


HERE = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(HERE)
A_CSV = RES / "scores.csv"
D_CSV = RES / "d1_scores.csv"
A_VERDICTS = ("helyes", "reszben", "helytelen", "hallucinacio")
C_VERDICTS = ("jo", "reszben", "rossz")


def load(path):
    if not path.exists():
        sys.exit(f"nincs meg: {path}")
    with path.open(encoding="utf-8") as fh:
        r = csv.DictReader(fh)
        return list(r), r.fieldnames


def save(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def find(rows, item, lang, kind=None):
    hits = [r for r in rows if r["item_id"] == item and r["lang"] == lang
            and (kind is None or r["kind"] == kind)]
    if not hits:
        avail = sorted({r["item_id"] for r in rows if kind is None or r["kind"] == kind})
        sys.exit(f"nincs ilyen sor: {item}/{lang}\nlétező item_id-k: {', '.join(avail[:60])}")
    if len(hits) > 1:
        sys.exit(f"több sor illeszkedik ({len(hits)}) — ez adathiba, nézd meg a CSV-t")
    return hits[0]


def cmd_status():
    a, _ = load(A_CSV)
    d, _ = load(D_CSV)
    na = sum(1 for r in a if (r.get("manual") or "").strip())
    unt = [r for r in d if r["kind"] == "unt"]
    ctrl = [r for r in d if r["kind"] == "ctrl"]
    nd = sum(1 for r in unt if (r.get("manual_native") or "").strip()
             or (r.get("manual_distortion") or "").strip())
    nc = sum(1 for r in ctrl if (r.get("manual_ctrl") or "").strip())
    print(f"Mérés A   — az ellenőrző körben újraítélve: {na:3d} / {len(a)} válasz "
          f"({'KÉSZ' if na >= 102 else f'a kötelező 102-ből még {max(0, 102 - na)} hátra'})")
    print(f"D1 UNT    — az ellenőrző körben újraítélve: {nd:3d} / {len(unt)} válasz "
          f"({'KÉSZ' if nd >= len(unt) else f'még {len(unt) - nd} hátra'})")
    print(f"D1 kontr. — az ellenőrző körben újraítélve: {nc:3d} / {len(ctrl)} válasz (opcionális)")
    if na:
        chg = sum(1 for r in a if (r.get("manual") or "").strip()
                  and r["manual"].strip() != r["judge"].strip())
        print(f"\nA bírálótól eltérő ellenőrző ítélet: {chg} (a többi megerősítés)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="hol tartok a ellenőrző körben")

    pa = sub.add_parser("a", help="Mérés A — faktuális válasz ítélete")
    pa.add_argument("item", nargs="?"); pa.add_argument("lang", nargs="?", choices=("hu", "en", "zh"))
    pa.add_argument("verdict", nargs="?", choices=A_VERDICTS)
    pa.add_argument("--clear", action="store_true")
    pa.add_argument("--confirm-all", action="store_true",
                    help="a ZH+HU csoport MINDEN még üres sorára beírja a bíráló ítéletét, mint "
                         "megerősítést — csak akkor használd, ha tényleg végignézted őket")

    pd_ = sub.add_parser("d", help="D1 UNT — komponens-darabszámok")
    pd_.add_argument("item", nargs="?"); pd_.add_argument("lang", nargs="?", choices=("hu", "en", "zh"))
    pd_.add_argument("--native", type=int); pd_.add_argument("--distortion", type=int)
    pd_.add_argument("--clear", action="store_true")
    pd_.add_argument("--confirm-all", action="store_true",
                    help="mind a 48 UNT-sorra beírja a bíráló darabszámait, mint megerősítést")

    pc = sub.add_parser("c", help="D1 kontrollszó — jo/reszben/rossz")
    pc.add_argument("item"); pc.add_argument("lang", choices=("hu", "en", "zh"))
    pc.add_argument("verdict", nargs="?", choices=C_VERDICTS)
    pc.add_argument("--clear", action="store_true")
    args = ap.parse_args()

    if args.cmd == "status":
        return cmd_status()

    if args.cmd == "a":
        rows, fields = load(A_CSV)
        if args.confirm_all:
            # ⚠️ Ez ÁLLÍTÁST tesz: „ezt a sort megnéztem és egyetértek a bírálóval".
            # Az eltéréseket UTÁNA kell beírni, azok felülírják.
            n = 0
            for r in rows:
                if r["group"] in ("ZH", "HU") and not (r.get("manual") or "").strip():
                    r["manual"] = r["judge"]; r["final"] = r["judge"]; n += 1
            save(A_CSV, rows, fields)
            print(f"{n} sorra beírva a bíráló ítélete MEGERŐSÍTÉSKÉNT (ZH+HU csoport).")
            print("Most írd be az eltéréseket — azok felülírják. Utána: python3 src/analyze_a.py")
            return
        if not args.item or not args.lang:
            sys.exit("kell item és nyelv (vagy --confirm-all)")
        r = find(rows, args.item, args.lang)
        if args.clear:
            r["manual"] = ""
        else:
            if not args.verdict:
                sys.exit(f"ítélet kell: {' / '.join(A_VERDICTS)}")
            r["manual"] = args.verdict
        r["final"] = r["manual"].strip() or r["judge"].strip()
        save(A_CSV, rows, fields)
        print(f"{args.item}/{args.lang}: bíráló={r['judge']} → ellenőrző={r['manual'] or '(törölve)'}")
        print("futtasd: python3 src/analyze_a.py")
        return

    rows, fields = load(D_CSV)
    if getattr(args, "confirm_all", False):
        n = 0
        for r in rows:
            if r["kind"] == "unt" and not ((r.get("manual_native") or "").strip()
                                           or (r.get("manual_distortion") or "").strip()):
                r["manual_native"] = r["native_hit"]
                r["manual_distortion"] = r["distortion_hit"]
                n += 1
        save(D_CSV, rows, fields)
        print(f"{n} UNT-sorra beírva a bíráló darabszáma MEGERŐSÍTÉSKÉNT.")
        print("Az eltéréseket utána írd be. Futtasd: python3 src/analyze_d.py")
        return
    if not args.item or not args.lang:
        sys.exit("kell item és nyelv (vagy --confirm-all)")
    if args.cmd == "c":
        r = find(rows, args.item if args.item.endswith("-ctrl") else args.item + "-ctrl",
                 args.lang, kind="ctrl")
        r["manual_ctrl"] = "" if args.clear else (args.verdict or sys.exit(
            f"ítélet kell: {' / '.join(C_VERDICTS)}"))
        print(f"{r['item_id']}/{args.lang}: bíráló={r['ctrl_itelet']} → ellenőrző={r['manual_ctrl'] or '(törölve)'}")
    else:
        r = find(rows, args.item.replace("-ctrl", ""), args.lang, kind="unt")
        if args.clear:
            r["manual_native"] = r["manual_distortion"] = ""
        else:
            if args.native is None and args.distortion is None:
                sys.exit("adj meg legalább egyet: --native N / --distortion N")
            for key, val, maxkey in (("manual_native", args.native, "native_n"),
                                     ("manual_distortion", args.distortion, "distortion_n")):
                if val is None:
                    continue
                hi = int(r[maxkey])
                if not 0 <= val <= hi:
                    sys.exit(f"{key}: 0 és {hi} közé kell esnie (kapott: {val})")
                r[key] = str(val)
        print(f"{r['item_id']}/{args.lang}: bíráló native={r['native_hit']}/{r['native_n']} "
              f"distortion={r['distortion_hit']}/{r['distortion_n']} → ellenőrző "
              f"native={r['manual_native'] or '–'} distortion={r['manual_distortion'] or '–'}")
    save(D_CSV, rows, fields)
    print("futtasd: python3 src/analyze_d.py")


if __name__ == "__main__":
    main()
