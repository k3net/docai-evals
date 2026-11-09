"""07-es kör — a végső diagnosztikai minta kiolvasásainak pecsétje (K3) a 05 `pecset05` útján: `cache/k07/pecset_k3/`
(a konténer root-jáé, 700), manifest a `kor07/rogzites/pecset/K07K3.json`-ban.

A K3 elemzője a kiolvasás előtt rögzül (`rogzit07k3`, `kor07/rogzites/k3/ROGZITES.json`), ezért a kapu itt nem a
rögzítéshez, hanem a pecsét nyitásához kötött: a pecsét alatti út csak a `kor07/rogzites/k3/NYITAS.json` után
olvasható, amelyet a `rogzit07k3 nyit` ír Dani jóváhagyásával.

  python3 kor07/eszkozok/pecset07k3.py nyit
  python3 kor07/eszkozok/pecset07k3.py lezar --fazis K07K3
  python3 kor07/eszkozok/pecset07k3.py ellenoriz --fazis K07K3
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok")]
import pecset05 as P  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
P.PECSET = EXP / "cache/k07/pecset_k3"
P.V1A = EXP / "kor07/rogzites/k3/NYITAS.json"
P.MANIFEST_DIR = EXP / "kor07/rogzites/pecset"
P.KOD = ("kor07/eszkozok/kiolvas07diag.py", "kor07/eszkozok/kiolvas07.py", "kor07/eszkozok/keret07.py",
         "kor07/eszkozok/szint07diag.py", "kor07/eszkozok/szint07k3.py", "kor07/eszkozok/szint07.py",
         "kor07/eszkozok/pecset07k3.py", "kor06/eszkozok/szint06.py", "kor06/spec/csaladok06.yaml",
         "kor05/eszkozok/hf_jellemzo05.py", "kor05/eszkozok/allapot05.py", "kor05/eszkozok/pecset05.py",
         "kor03/eszkozok/kozos03.py", "eszkozok/common.py",
         *(f"kor07/adat/diag/{k}/{f}.jsonl" for k in ("terv", "items") for f in CSALADOK
           if (EXP / f"kor07/adat/diag/{k}/{f}.jsonl").exists()))
kapu = P.kapu

if __name__ == "__main__":
    P.main()
