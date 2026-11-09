"""07-es kör — a K3 elemzőjének rögzítése a végső diagnosztikai minta kiolvasása előtt, és a K3 pecsétjének nyitása
(07-runbook 3.3; Dani 2026-11-01: „a K3 elemzője a végső minta kiolvasása előtt rögzüljön, a kiolvasás pecsét alatt”).

  python3 kor07/eszkozok/rogzit07k3.py manifest                    # MANIFEST.sha256 és a pillanatképek
  python3 kor07/eszkozok/rogzit07k3.py rogzit --jovahagyas "…"     # ROGZITES.json, a kiolvasás előtt
  python3 kor07/eszkozok/rogzit07k3.py ellenoriz                   # a K3 és a v1 manifestje, és a K07K3 pecsét, ha van
  python3 kor07/eszkozok/rogzit07k3.py nyit --jovahagyas "…"       # NYITAS.json: ettől olvasható a pecsét alatti út

A `kor07/rogzites/k3/` tartalma: MANIFEST.sha256 (a K3 kódja, a v1 manifestje és rögzítése, a pillanatképek),
07-runbook-k3.md és nehez3-javaslat-k3.md (a runbook és a döntések pillanatképe), ROGZITES.json, majd a nyitáskor
NYITAS.json és a K07K3 pecsétmanifest pillanatképe. A pecsét alatti fájlok root-éi: az `ellenoriz` és a `nyit` `py`-val
fut.
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
sys.path.insert(0, str(HERE))
import pecset07k3  # noqa: E402

P = pecset07k3.P
DIR = EXP / "kor07/rogzites/k3"
ROGZITES, NYITAS, PECSET = DIR / "ROGZITES.json", P.V1A, "K07K3"
KOD = ["kor07/eszkozok/" + n for n in ("k3_07.py", "b1rel07k3.py", "kiolvas07diag.py", "szint07diag.py", "szint07k3.py",
                                        "pecset07k3.py", "rogzit07k3.py", "k07k3_diag.sh", "b14_07k3.py")]
V1 = ("kor07/rogzites/v1/MANIFEST.sha256", "kor07/rogzites/v1/ROGZITES.json")
PILLANAT = {"07-runbook.md": "07-runbook-k3.md", "kor07/nehez3-javaslat.md": "nehez3-javaslat-k3.md"}


def sorok(path: Path) -> list[tuple[str, str]]:
    return [(x[:64], x[66:]) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def elteres(path: Path) -> list[str]:
    return [p for h, p in sorok(path) if not (EXP / p).exists() or P.sha256(EXP / p) != h]


def manifest(_a) -> None:
    if ROGZITES.exists():
        raise SystemExit("a K3 már rögzítve")
    DIR.mkdir(parents=True, exist_ok=True)
    for src, dst in PILLANAT.items():
        shutil.copy(EXP / src, DIR / dst)
    paths = [*KOD, *V1, *(str((DIR / d).relative_to(EXP)) for d in PILLANAT.values())]
    missing = [p for p in paths if not (EXP / p).exists()]
    if missing:
        raise SystemExit(f"hiányzó fájlok: {missing}")
    (DIR / "MANIFEST.sha256").write_text("".join(f"{P.sha256(EXP / p)}  {p}\n" for p in paths), encoding="utf-8")
    print(f"MANIFEST.sha256: {len(paths)} fájl, hash {P.sha256(DIR / 'MANIFEST.sha256')}")


def rogzit(a) -> None:
    if ROGZITES.exists():
        raise SystemExit("a K3 már rögzítve")
    if (P.MANIFEST_DIR / f"{PECSET}.json").exists() or (P.PECSET / "jellemzok").exists():
        raise SystemExit("a diagnosztikai minta kiolvasása már elkezdődött: a K3 csak előtte rögzíthető")
    bad = elteres(DIR / "MANIFEST.sha256")
    if bad:
        raise SystemExit(f"a manifest nem egyezik: {bad}")
    doc = {"verzio": "v1-K3", "rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas,
           "manifest_sha256": P.sha256(DIR / "MANIFEST.sha256"), "v1_manifest_sha256": P.sha256(EXP / V1[0]),
           "megjegyzes": "A K3 elemzője a végső diagnosztikai minta generálása és kiolvasása előtt rögzítve; a kiolvasás "
                         "a cache/k07/pecset_k3 alá megy (root, 700), és csak a NYITAS.json után olvasható."}
    ROGZITES.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=1))


def ellenoriz_lista() -> list[str]:
    bad = [f"k3: {p}" for p in elteres(DIR / "MANIFEST.sha256")]
    bad += [f"v1: {p}" for p in elteres(EXP / V1[0])]
    pm = P.MANIFEST_DIR / f"{PECSET}.json"
    if pm.exists():
        doc = json.loads(pm.read_text())
        most = P.fajlok()
        bad += [f"pecsét: {k}" for k in sorted(set(doc["fajlok"]) | set(most)) if doc["fajlok"].get(k) != most.get(k)]
        bad += [f"pecsét-kód: {k}" for k, h in doc["kod_sha256"].items() if P.sha256(EXP / k) != h]
    return bad


def ellenoriz(_a) -> None:
    bad = ellenoriz_lista()
    allapot = "rögzítve" if ROGZITES.exists() else "NINCS rögzítve"
    print(f"K3 ({allapot}), v1, pecsét: " + ("rendben" if not bad else f"ELTÉRÉS: {bad[:20]}"))
    sys.exit(1 if bad else 0)


def nyit(a) -> None:
    if not ROGZITES.exists():
        raise SystemExit("a K3 nincs rögzítve")
    if NYITAS.exists():
        raise SystemExit("a pecsét már nyitva")
    pm = P.MANIFEST_DIR / f"{PECSET}.json"
    if not pm.exists() or not json.loads(pm.read_text())["teljes"]:
        raise SystemExit(f"hiányzik vagy nem teljes a pecsétmanifest: {pm.relative_to(EXP)}")
    bad = ellenoriz_lista()
    if bad:
        raise SystemExit(f"eltérés, a pecsét nem nyílik: {bad[:20]}")
    shutil.copy(pm, DIR / f"{PECSET}.json")
    doc = {"nyitva": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas,
           "rogzites_sha256": P.sha256(ROGZITES), "pecset_manifest_sha256": P.sha256(pm)}
    NYITAS.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("manifest")
    sub.add_parser("ellenoriz")
    for n in ("rogzit", "nyit"):
        sub.add_parser(n).add_argument("--jovahagyas", required=True)
    a = ap.parse_args()
    {"manifest": manifest, "rogzit": rogzit, "ellenoriz": ellenoriz, "nyit": nyit}[a.cmd](a)


if __name__ == "__main__":
    main()
