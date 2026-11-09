"""07-es kör — a v1 rögzítése (07-runbook 7. F4; a 06 `befagyaszt06` burkolása 07-es útvonalakkal) és az ellenőrzése.

  python3 kor07/eszkozok/befagyaszt07.py manifest       # a MANIFEST.sha256 és a pillanatképek; a pecsét zárva marad
  python3 kor07/eszkozok/befagyaszt07.py rogzit --jovahagyas "Dani, 2026-…: …"
                                                        # a ROGZITES.json: ettől nyílik a pecsét (pecset07.kapu)
  python3 kor07/eszkozok/befagyaszt07.py ellenoriz      # az F5 előtt: a manifest és a pecsétmanifest

A `kor07/rogzites/v1/` tartalma:
  07-runbook-v1.md, v1-vazlat.md   a runbook és a rögzített döntések pillanatképe
  K07F3.json                       a pecsétmanifest pillanatképe (fájlnév, méret, sha256; kiolvasott érték nincs benne)
  MANIFEST.sha256                  sha256: a 07 és az importált 06 / 05 / 03 kód, a friss és a 06-os itemfájlok, a
                                   családterv, a 05 kalibrációja, a mentett fejek (`cache/k07/fejek`, a 06 B1-R0, a 05 H
                                   statisztikája), az audit és a Gemma összesítője, az F3R és az F4 eredménye
  ROGZITES.json                    idő, jóváhagyás, a manifest hash-e; a meglétekor a pecsét alatti utak olvashatók
A 06 kódja nem változik: a `befagyaszt06` függvényei futnak, a modul állandói 07-esre állítva; a `pecset05` útvonalait
a `pecset07` állítja (a `befagyaszt06` importja előbb a 06-osra állítaná, ezért a sorrend számít).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor06/eszkozok"), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import befagyaszt06 as BF  # noqa: E402  (a pecset06-ot importálja: a pecset05 a 06-os útvonalakra áll)
import pecset05 as P  # noqa: E402
import pecset07  # noqa: E402,F401  (a pecset05 útvonalai innen a 07-esek)

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
PECSET = "K07F3"
KOD = ["kor07/eszkozok/" + n for n in ("kiolvas07.py", "keret07.py", "szint07.py", "b14_07.py", "b1rel07.py", "elemzes07.py",
                                        "ero07.py", "audit07.py", "gemma07.py", "pecset07.py", "befagyaszt07.py", "repro07.py",
                                        "lib07.sh")] + \
      ["kor06/eszkozok/" + n for n in ("szint06.py", "b1rel06.py", "friss06.py", "audit06.py", "gemma06.py", "pecset06.py",
                                        "befagyaszt06.py", "elemzes06.py", "kiolvas06.py")] + \
      ["kor05/eszkozok/" + n for n in ("hf_jellemzo05.py", "allapot05.py", "pecset05.py", "fej05.py", "megbizhatosag05.py",
                                        "kalib05.py", "elemzes05.py")] + \
      ["eszkozok/common.py", "kor03/eszkozok/kozos03.py", "eszkozok/lib.sh"]
ADAT = [*(f"kor07/adat/f2/items/{f}.jsonl" for f in CSALADOK), *(f"kor06/adat/f2/items/{f}.jsonl" for f in CSALADOK),
        "kor06/spec/csaladok06.yaml", "kor05/eredmenyek/F3/kalib/kalib.json",
        "kor07/eredmenyek/F2/audit/osszesito.json", "kor07/eredmenyek/F2/gemma/osszesito.json",
        "kor07/eredmenyek/F3R/f3r.json", "kor07/eredmenyek/F4/ero.json"]
PILLANAT = ("07-runbook-v1.md", "v1-vazlat.md")


def fej_fajlok() -> list[str]:
    out = []
    for d, pat in (("cache/k07/fejek", "**/*"), ("cache/k06/b1rel", "*"), ("cache/k05/fejek/H", "fej*")):
        fs = sorted(p for p in (EXP / d).glob(pat) if p.is_file())
        if not fs:
            raise SystemExit(f"hiányzik: {d}/{pat}")
        out += [str(f.relative_to(EXP)) for f in fs]
    return out


# a 06 függvényei a 07 állandóival
BF.V1A, BF.MANIFEST_DIR = P.V1A, P.MANIFEST_DIR
BF.DIR = P.V1A.parent
BF.KOD, BF.ADAT, BF.PECSET, BF.PILLANAT, BF.fej_fajlok = KOD, ADAT, PECSET, PILLANAT, fej_fajlok
DIR, V1A = BF.DIR, BF.V1A


def manifest(_a) -> None:
    """A `befagyaszt06.manifest` lépései a 07-runbook pillanatképével."""
    if V1A.exists():
        raise SystemExit("a v1 már rögzítve; új manifest csak új verzióval (v1.1) készülhet")
    if not (DIR / "v1-vazlat.md").exists():
        raise SystemExit(f"hiányzik: {(DIR / 'v1-vazlat.md').relative_to(EXP)}")
    DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(EXP / "07-runbook.md", DIR / "07-runbook-v1.md")
    src = P.MANIFEST_DIR / f"{PECSET}.json"
    if not src.exists() or not json.loads(src.read_text())["teljes"]:
        raise SystemExit(f"hiányzik vagy nem teljes a pecsétmanifest: {src.relative_to(EXP)}")
    shutil.copy(src, DIR / f"{PECSET}.json")
    paths = [*KOD, *ADAT, *fej_fajlok(), *(str((DIR / n).relative_to(EXP)) for n in (*PILLANAT, f"{PECSET}.json"))]
    missing = [p for p in paths if not (EXP / p).exists()]
    if missing:
        raise SystemExit(f"hiányzó fájlok: {missing}")
    lines = [f"{P.sha256(EXP / p)}  {p}" for p in paths]
    (DIR / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"MANIFEST.sha256: {len(lines)} fájl, hash {P.sha256(DIR / 'MANIFEST.sha256')}")


def rogzit(a) -> None:
    if V1A.exists():
        raise SystemExit("a v1 már rögzítve")
    bad = BF.check_manifest() + BF.check_pecset()
    if bad:
        raise SystemExit(f"a manifest vagy a pecsét nem egyezik: {bad[:10]}")
    doc = {"verzio": "v1", "rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas,
           "manifest_sha256": P.sha256(DIR / "MANIFEST.sha256"), "pecset_manifest": {PECSET: P.sha256(DIR / f"{PECSET}.json")},
           "megjegyzes": "A friss CAL- és TESZT-kiolvasások a rögzítéskor nem voltak megtekintve; a kiolvasás pecsételve "
                         "futott (cache/k07/pecset/, root, 700). A fejek a rögzítés előtt készültek és a manifestben vannak."}
    V1A.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("manifest")
    r = sub.add_parser("rogzit")
    r.add_argument("--jovahagyas", required=True)
    sub.add_parser("ellenoriz")
    a = ap.parse_args()
    {"manifest": manifest, "rogzit": rogzit, "ellenoriz": BF.ellenoriz}[a.cmd](a)


if __name__ == "__main__":
    main()
