"""07-es kör — kiolvasás a K3 utáni nyitott mintákra a `kiolvas07` útján (a `kiolvas07` változatlan):

  diagaug:<család>:DIAG:<mód>   a végső diagnosztikai minta a kiszámított sorral (`aug07 epit`, kor07/adat/diagaug)
  b7:<család>:B7:<mód>          a 07B valódi banki tételei (`b7_epit`, kor07/adat/b7; csak a saját gépeinken)

A kimeneti könyvtár `<forrás>_<család>_<szelet>__<mód>`, a nyitott `cache/k07/jellemzok[2]` alatt.
  python3 kor07/eszkozok/kiolvas07x.py kivon --feladat b7:penzugy.bankparositas:B7:kanonikus ... --out-root cache/k07/jellemzok
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kiolvas07 as KI  # noqa: E402

KI.ITEMS["diagaug"] = KI.EXP / "kor07/adat/diagaug/items"
KI.ITEMS["b7"] = KI.EXP / "kor07/adat/b7/items"
KI.SZELETEK["diagaug"] = ("DIAG",)
KI.SZELETEK["b7"] = ("B7",)
KI.FORRASOK = (*KI.FORRASOK, "diagaug", "b7")

if __name__ == "__main__":
    KI.main()
