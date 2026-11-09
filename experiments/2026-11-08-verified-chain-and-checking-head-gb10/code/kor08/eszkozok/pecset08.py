"""08 — a G3 értékelő kiolvasásainak és pontozásainak pecsétje (G1-rögzítés 10.) a 05 `pecset05` útján, 08-as
útvonalakkal (a 07 `pecset07` mintájára): `cache/k08/pecset/` (a konténer root-jáé, 700), manifest a
`kor08/rogzites/pecset/` alatt. A pecsét alatti út **csak a G5 nyitása után olvasható**: a G4 hash-lezárása és Dani
engedélye (`kor08/rogzites/G5/NYITAS.json`) nélkül a `kapu` megállít. A pecsét alá a G2 értékelő szeletei kerülnek
(a friss CAL / TESZT, a K3-típus, az értelmezési teszt, a lánc nélküli összehasonlító bemenetek); a tanítóminta
kiolvasása nem (a fejek a G4 előtt tanulnak rajta). A G4 előtt csak darabszám és idő kerül naplóba.

  python3 kor08/eszkozok/pecset08.py nyit
  python3 kor08/eszkozok/pecset08.py lezar --fazis K08G3
  python3 kor08/eszkozok/pecset08.py ellenoriz --fazis K08G3
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok")]
import pecset05 as P  # noqa: E402

P.PECSET = EXP / "cache/k08/pecset"
P.V1A = EXP / "kor08/rogzites/G5/NYITAS.json"
P.MANIFEST_DIR = EXP / "kor08/rogzites/pecset"
_G2 = [f"kor08/adat/G2/{r}/items/{f}.jsonl" for r in ("friss", "k3", "ert_teszt", "ert_tanito")
       for f in ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")]
P.KOD = ("kor08/eszkozok/kiolvas08.py", "kor08/eszkozok/lanc08.py", "kor08/eszkozok/kinyer08.py", "kor08/eszkozok/b1rel08.py",
         "kor08/eszkozok/szint08.py", "kor08/eszkozok/forgatokonyv08_szab.py", "kor08/eszkozok/pecset08.py",
         "kor08/eszkozok/det_or08.py", "kor08/eszkozok/lib08.sh", "kor07/eszkozok/kiolvas07.py", "kor07/eszkozok/keret07.py",
         "kor07/eszkozok/b1rel07.py", "kor05/eszkozok/hf_jellemzo05.py", "kor05/eszkozok/pecset05.py", "eszkozok/common.py",
         *(x for x in _G2 if (EXP / x).exists()))
kapu = P.kapu

if __name__ == "__main__":
    P.main()
