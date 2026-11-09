"""06-os kör — a v1 rögzítése (06-runbook 9. F4; a 05 `befagyaszt05` mintájára) és a rögzítés ellenőrzése.

  python3 kor06/eszkozok/befagyaszt06.py manifest       # a MANIFEST.sha256 és a pillanatképek; a pecsét zárva marad
  python3 kor06/eszkozok/befagyaszt06.py rogzit --jovahagyas "Dani, 2026-…: …"
                                                        # a ROGZITES.json: ettől nyílik a pecsét (pecset06.kapu)
  python3 kor06/eszkozok/befagyaszt06.py ellenoriz      # az F5 előtt: a manifest és a pecsétmanifest

A `kor06/rogzites/v1/` tartalma:
  06-runbook-v1.md, v1-vazlat.md   a runbook és a rögzített döntések pillanatképe
  <PECSET>.json                    a pecsétmanifest pillanatképe (fájlnév, méret, sha256; kiolvasott érték nincs benne)
  MANIFEST.sha256                  sha256: az elemző- és tanítókód az importált 05-ös modulokkal, az itemfájlok és a
                                   családterv, a 05 kalibrációja és fejei, az előtanított B1-R, a pillanatképek
  ROGZITES.json                    idő, jóváhagyás, a manifest hash-e; a meglétekor a pecsét alatti utak olvashatók
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
sys.path[:0] = [str(HERE), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import pecset06  # noqa: E402,F401  (a pecset05 útvonalait a 06-osra állítja)
from pecset05 import MANIFEST_DIR, V1A, fajlok, sha256  # noqa: E402

DIR = V1A.parent
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
KOD = ["kor06/eszkozok/" + n for n in ("friss06.py", "b1rel06.py", "elemzes06.py", "bontas06.py", "kiolvas06.py",
                                        "pecset06.py", "befagyaszt06.py", "szint06.py", "mde06.py")] + \
      ["kor05/eszkozok/" + n for n in ("hf_jellemzo05.py", "allapot05.py", "pecset05.py", "fej05.py", "megbizhatosag05.py",
                                       "kalib05.py", "elemzes05.py", "diag05.py")] + \
      ["eszkozok/common.py", "kor03/eszkozok/kozos03.py", "eszkozok/lib.sh"]
ADAT = [*(f"kor06/adat/f2/items/{f}.jsonl" for f in CSALADOK), "kor06/spec/csaladok06.yaml",
        "kor05/eredmenyek/F3/kalib/kalib.json", "kor06/eredmenyek/F2/audit/kor2/osszesito.json"]
PECSET = "K06F3C"  # az utolsó, mindhárom családra teljes pecsétmanifest
PILLANAT = ("06-runbook-v1.md", "v1-vazlat.md")


def fej_fajlok() -> list[str]:
    out = []
    for d, pat in (("cache/k05/fejek/H", "fej*"), ("cache/k05/megbizhatosag/H", "rel*"), ("cache/k06/b1rel", "*")):
        fs = sorted((EXP / d).glob(pat))
        if not fs:
            raise SystemExit(f"hiányzik: {d}/{pat}")
        out += [str(f.relative_to(EXP)) for f in fs]
    return out


def manifest(_a) -> None:
    if V1A.exists():
        raise SystemExit("a v1 már rögzítve; új manifest csak új verzióval (v1.1) készülhet")
    if not (DIR / "v1-vazlat.md").exists():
        raise SystemExit(f"hiányzik: {(DIR / 'v1-vazlat.md').relative_to(EXP)}")
    shutil.copy(EXP / "06-runbook.md", DIR / "06-runbook-v1.md")
    src = MANIFEST_DIR / f"{PECSET}.json"
    if not src.exists() or not json.loads(src.read_text())["teljes"]:
        raise SystemExit(f"hiányzik vagy nem teljes a pecsétmanifest: {src.relative_to(EXP)}")
    shutil.copy(src, DIR / f"{PECSET}.json")
    paths = [*KOD, *ADAT, *fej_fajlok(), *(str((DIR / n).relative_to(EXP)) for n in (*PILLANAT, f"{PECSET}.json"))]
    missing = [p for p in paths if not (EXP / p).exists()]
    if missing:
        raise SystemExit(f"hiányzó fájlok: {missing}")
    lines = [f"{sha256(EXP / p)}  {p}" for p in paths]
    (DIR / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"MANIFEST.sha256: {len(lines)} fájl, hash {sha256(DIR / 'MANIFEST.sha256')}")


def check_manifest() -> list[str]:
    bad = []
    for line in (DIR / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, p = line.split("  ", 1)
        if not (EXP / p).exists() or sha256(EXP / p) != h:
            bad.append(p)
    return bad


def check_pecset() -> list[str]:
    most = fajlok()
    doc = json.loads((DIR / f"{PECSET}.json").read_text())
    return [f"{PECSET}:{k}" for k, v in doc["fajlok"].items() if most.get(k) != v]


def rogzit(a) -> None:
    if V1A.exists():
        raise SystemExit("a v1 már rögzítve")
    bad = check_manifest() + check_pecset()
    if bad:
        raise SystemExit(f"a manifest vagy a pecsét nem egyezik: {bad[:10]}")
    doc = {"verzio": "v1", "rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas,
           "manifest_sha256": sha256(DIR / "MANIFEST.sha256"), "pecset_manifest": {PECSET: sha256(DIR / f"{PECSET}.json")},
           "megjegyzes": "A friss családok CAL- és TESZT-kiolvasásai a rögzítéskor nem voltak megtekintve; a kiolvasás "
                         "pecsételve futott (cache/k06/pecset/, root, 700)."}
    V1A.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=1))


def ellenoriz(_a) -> None:
    if not V1A.exists():
        raise SystemExit("nincs rögzítve (ROGZITES.json hiányzik)")
    doc = json.loads(V1A.read_text())
    bad = ([] if sha256(DIR / "MANIFEST.sha256") == doc["manifest_sha256"] else ["MANIFEST.sha256"]) + \
        check_manifest() + check_pecset()
    print(f"v1 ({doc['rogzitve']}): {'rendben' if not bad else f'ELTÉRÉS: {bad[:10]}'}")
    sys.exit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("manifest")
    r = sub.add_parser("rogzit")
    r.add_argument("--jovahagyas", required=True)
    sub.add_parser("ellenoriz")
    a = ap.parse_args()
    {"manifest": manifest, "rogzit": rogzit, "ellenoriz": ellenoriz}[a.cmd](a)


if __name__ == "__main__":
    main()
