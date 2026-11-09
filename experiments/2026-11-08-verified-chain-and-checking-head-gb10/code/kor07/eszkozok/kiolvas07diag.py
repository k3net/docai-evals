"""07-es kör — a végső diagnosztikai minta kiolvasása (K3) a `kiolvas07` útján, a K3 pecsétje alá.

A feladat `<család>:DIAG:<kanonikus|b1>`, a kimeneti könyvtár így `<család>_DIAG__<mód>`, mint az F3-é. A
`kiolvas07` forrás nélküli ága itt a diagnosztikai itemekre áll (`kor07/adat/diag/items`, csak DIAG), és a kiolvasás
csak a `cache/k07/pecset_k3` alá mehet (a pecsét: `pecset07k3`).

  python3 kor07/eszkozok/kiolvas07diag.py kivon --feladat penzugy.bankparositas:DIAG:kanonikus ... \
      --out-root cache/k07/pecset_k3/jellemzok [--keret 2]
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kiolvas07 as KI  # noqa: E402

PECSET_K3 = KI.EXP / "cache/k07/pecset_k3"
KI.ITEMS[""] = KI.EXP / "kor07/adat/diag/items"
KI.SZELETEK[""] = ("DIAG",)


def kapu(argv: list[str]) -> None:
    if (argv[0] if argv else "") != "kivon":
        raise SystemExit("csak a `kivon` parancs")
    root = KI.arg(argv, "--out-root")
    under = bool(root) and PECSET_K3.resolve() in (KI.EXP / root[0]).resolve().parents
    if not under:
        raise SystemExit(f"PECSÉT: a diagnosztikai minta kiolvasása csak a {PECSET_K3.relative_to(KI.EXP)} alá mehet")


if __name__ == "__main__":
    kapu(sys.argv[1:])
    KI.main()
