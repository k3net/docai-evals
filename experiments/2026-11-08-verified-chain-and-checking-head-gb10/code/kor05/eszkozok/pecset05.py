"""05-ös kör — a kitartott rétegek kiolvasásainak pecsétje (05-runbook 8.2, 10. pont F2–F3, 12. pont).

A HO-rétegek és a célcsalád-minták HF-kiolvasásai a `cache/k05/pecset/` alá kerülnek. A könyvtár a konténer
root-jáé, 700-as joggal: a gazdagép felhasználója nem látja. A `kapu()` minden elemző betöltőjében ott van: a pecsét
alatti utat a v1a rögzítése (`kor05/rogzites/v1a/ROGZITES.json`) nélkül nem olvassa.

  python3 kor05/eszkozok/pecset05.py nyit                  # a pecsétkönyvtár létrehozása 700-as joggal
  python3 kor05/eszkozok/pecset05.py lezar --fazis K05F2B  # sha256-manifest → kor05/rogzites/pecset/K05F2B.json
  python3 kor05/eszkozok/pecset05.py ellenoriz --fazis K05F2B   # a pecsét feloldásakor: a fájlok változatlanok-e

A manifest csak fájlneveket, méreteket, sha256-okat és darabszámokat tartalmaz, kiolvasást nem; szinkronizálható.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
PECSET = EXP / "cache/k05/pecset"
V1A = EXP / "kor05/rogzites/v1a/ROGZITES.json"
MANIFEST_DIR = EXP / "kor05/rogzites/pecset"
KOD = ("kor05/eszkozok/hf_jellemzo05.py", "kor05/eszkozok/allapot05.py", "kor05/eszkozok/pecset05.py",
       "kor05/adat/szeletek05.json", "kor03/eszkozok/kozos03.py", "eszkozok/common.py")


def kapu(path: Path | str) -> None:
    """A pecsét alatti út olvasása csak a v1a rögzítése után."""
    p = Path(path).resolve()
    if (p == PECSET.resolve() or PECSET.resolve() in p.parents) and not V1A.exists():
        raise SystemExit(f"PECSÉT: {p} a v1a rögzítéséig nem olvasható ({V1A.relative_to(EXP)} hiányzik)")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def nyit(_a) -> None:
    (PECSET / "jellemzok").mkdir(parents=True, exist_ok=True)
    os.chmod(PECSET, 0o700)
    print(f"pecsétkönyvtár: {PECSET} (700)")


def fajlok() -> dict[str, dict]:
    return {str(p.relative_to(PECSET)): {"meret": p.stat().st_size, "sha256": sha256(p)}
            for p in sorted(PECSET.rglob("*")) if p.is_file()}


def lezar(a) -> None:
    ff = fajlok()
    feladatok = {}
    for d in sorted((PECSET / "jellemzok").iterdir()) if (PECSET / "jellemzok").exists() else []:
        o = d / "osszegzes.json"
        feladatok[d.name] = {"kesz": o.exists(), "n": json.loads(o.read_text())["n"] if o.exists() else None,
                             "shardok": len(list(d.glob("sorok_*.jsonl")))}
    for root, dirs, files in os.walk(PECSET):
        for n in dirs + files:
            os.chmod(Path(root) / n, 0o700 if n in dirs else 0o600)
    os.chmod(PECSET, 0o700)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    out = MANIFEST_DIR / f"{a.fazis}.json"
    doc = {"fazis": a.fazis, "lezarva": datetime.now().isoformat(timespec="seconds"),
           "v1a_rogzitve": V1A.exists(), "teljes": bool(feladatok) and all(v["kesz"] for v in feladatok.values()),
           "feladatok": feladatok, "kod_sha256": {k: sha256(EXP / k) for k in KOD}, "fajlok": ff}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pecsét: {len(ff)} fájl, {sum(v['meret'] for v in ff.values()) / 1e9:.2f} GB → {out.relative_to(EXP)}")


def ellenoriz(a) -> None:
    doc = json.loads((MANIFEST_DIR / f"{a.fazis}.json").read_text())
    most = fajlok()
    rossz = sorted(k for k in set(doc["fajlok"]) | set(most) if doc["fajlok"].get(k) != most.get(k))
    print(f"{len(doc['fajlok'])} fájl a manifestben, eltérés: {len(rossz)}")
    for k in rossz[:20]:
        print("  ", k)
    sys.exit(1 if rossz else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("nyit")
    for n in ("lezar", "ellenoriz"):
        sub.add_parser(n).add_argument("--fazis", required=True)
    a = ap.parse_args()
    {"nyit": nyit, "lezar": lezar, "ellenoriz": ellenoriz}[a.cmd](a)


if __name__ == "__main__":
    main()
