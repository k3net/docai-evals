"""06-os kör — a CAL és a TESZT kiolvasásainak pecsétje (06-runbook 4., 12.) a 05 `pecset05` útján, 06-os
útvonalakkal: `cache/k06/pecset/` (a konténer root-jáé, 700), manifest a `kor06/rogzites/pecset/` alatt, és a
pecsét alatti út csak a 06 v1 rögzítése (`kor06/rogzites/v1/ROGZITES.json`) után olvasható (`kapu`).

  python3 kor06/eszkozok/pecset06.py nyit
  python3 kor06/eszkozok/pecset06.py lezar --fazis K06F3
  python3 kor06/eszkozok/pecset06.py ellenoriz --fazis K06F3
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok")]
import pecset05 as P  # noqa: E402

P.PECSET = EXP / "cache/k06/pecset"
P.V1A = EXP / "kor06/rogzites/v1/ROGZITES.json"
P.MANIFEST_DIR = EXP / "kor06/rogzites/pecset"
P.KOD = ("kor06/eszkozok/kiolvas06.py", "kor06/eszkozok/pecset06.py", "kor06/eszkozok/szint06.py",
         "kor06/spec/csaladok06.yaml", "kor05/eszkozok/hf_jellemzo05.py", "kor05/eszkozok/allapot05.py",
         "kor05/eszkozok/pecset05.py", "kor03/eszkozok/kozos03.py", "eszkozok/common.py",
         *(f"kor06/adat/f2/items/{f}.jsonl" for f in ("penzugy.bankparositas", "muszaki.hibaelharitas",
                                                       "szabaly.koltsegelszamolas")
           if (EXP / f"kor06/adat/f2/items/{f}.jsonl").exists()))  # a hibaelhárítás a K06F2HB után kerül be
kapu = P.kapu

if __name__ == "__main__":
    P.main()
