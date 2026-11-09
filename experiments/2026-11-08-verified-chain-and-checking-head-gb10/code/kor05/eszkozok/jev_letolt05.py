"""JEV-35B letöltése rögzített revízióval, méret- és LFS-sha256-ellenőrzéssel (05-runbook 3.4, 10. pont F2).

A várt fájllista (`kor05/adat/jev_varhato.json`) a HF API-ból, a letöltés előtt rögzítve: revízió, fájlonként méret és
az LFS-fájlok sha256-ja. A konténerben a HF_HOME a gazdagép ~/hf-cache-jev könyvtára (írható; a Xet írható cache-t
kér). Újraindítva a kész fájlokat nem tölti le újra.

  python3 kor05/eszkozok/jev_letolt05.py --varhato kor05/adat/jev_varhato.json --out kor05/eredmenyek/F2/jev_letoltes.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--varhato", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from huggingface_hub import snapshot_download  # noqa: PLC0415

    v = json.loads(Path(a.varhato).read_text())
    t0 = time.time()
    snap = Path(snapshot_download(v["repo"], revision=v["revision"]))
    t1 = time.time()
    hibak = []
    for name, exp in v["fajlok"].items():
        p = snap / name
        if not p.exists():
            hibak.append({"fajl": name, "hiba": "hiányzik"})
        elif exp["size"] is not None and p.stat().st_size != exp["size"]:
            hibak.append({"fajl": name, "hiba": f"méret {p.stat().st_size} ≠ {exp['size']}"})
        elif exp["sha256"] and sha256(p) != exp["sha256"]:
            hibak.append({"fajl": name, "hiba": "sha256 eltér"})
    out = {"repo": v["repo"], "revision": v["revision"], "snapshot": str(snap).replace("/hf/", "~/hf-cache-jev/", 1),
           "fajlok": len(v["fajlok"]), "osszmeret_GB": round(v["osszmeret"] / 1e9, 2),
           "letoltes_perc": round((t1 - t0) / 60, 1), "ellenorzes_perc": round((time.time() - t1) / 60, 1),
           "sha256_ellenorizve": sum(1 for e in v["fajlok"].values() if e["sha256"]), "hibak": hibak,
           "kesz": datetime.now().isoformat(timespec="seconds")}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("revision", "letoltes_perc", "ellenorzes_perc", "hibak")}, ensure_ascii=False))
    sys.exit(1 if hibak else 0)


if __name__ == "__main__":
    main()
