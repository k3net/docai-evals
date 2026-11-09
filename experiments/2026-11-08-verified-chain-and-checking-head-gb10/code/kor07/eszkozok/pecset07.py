"""07-es kör — a friss CAL és TESZT kiolvasásainak pecsétje (07-runbook 3.2) a 05 `pecset05` útján, 07-es útvonalakkal
(a 06 `pecset06` mintájára): `cache/k07/pecset/` (a konténer root-jáé, 700), manifest a `kor07/rogzites/pecset/` alatt,
és a pecsét alatti út csak a 07 v1 rögzítése (`kor07/rogzites/v1/ROGZITES.json`) után olvasható (`kapu`).

  python3 kor07/eszkozok/pecset07.py nyit
  python3 kor07/eszkozok/pecset07.py lezar --fazis K07F3
  python3 kor07/eszkozok/pecset07.py ellenoriz --fazis K07F3
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok")]
import pecset05 as P  # noqa: E402

P.PECSET = EXP / "cache/k07/pecset"
P.V1A = EXP / "kor07/rogzites/v1/ROGZITES.json"
P.MANIFEST_DIR = EXP / "kor07/rogzites/pecset"
P.KOD = ("kor07/eszkozok/kiolvas07.py", "kor07/eszkozok/keret07.py", "kor07/eszkozok/pecset07.py",
         "kor07/eszkozok/szint07.py", "kor06/eszkozok/szint06.py", "kor06/spec/csaladok06.yaml",
         "kor05/eszkozok/hf_jellemzo05.py", "kor05/eszkozok/allapot05.py", "kor05/eszkozok/pecset05.py",
         "kor03/eszkozok/kozos03.py", "eszkozok/common.py",
         *(f"kor07/adat/f2/items/{f}.jsonl" for f in ("penzugy.bankparositas", "muszaki.hibaelharitas",
                                                       "szabaly.koltsegelszamolas")
           if (EXP / f"kor07/adat/f2/items/{f}.jsonl").exists()))
kapu = P.kapu

if __name__ == "__main__":
    P.main()
