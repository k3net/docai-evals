"""A `kiolvas07` (a 07 v1 manifestjében, nem módosul) a nehéz minta 3. körének forrásával: `nehez3:<család>:NEHEZ`
(`kor07/adat/nehez3/items/`, `szint07k3`). Nyitott, szintetikus fejlesztési minta a 06 T500-sablonjain; pecsét nincs.
  python3 kor07/eszkozok/kiolvas07k3.py kivon --feladat nehez3:<család>:NEHEZ:<kanonikus|b1> [--keret 2] …
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kiolvas07 as KI  # noqa: E402

KI.ITEMS["nehez3"] = KI.EXP / "kor07/adat/nehez3/items"
KI.SZELETEK["nehez3"] = ("NEHEZ",)
KI.FORRASOK = (*KI.FORRASOK, "nehez3")

if __name__ == "__main__":
    KI.main()
