"""08B — a rögzített eszközök a valódi banki tételeken, burkolóként (a 07B 262 tétele, fejlesztési próba; a tételek csak a saját gépeinken). A forrás neve `B7`, a kimenet gyökere `kor08/adat/V`.
A parancs első szava dönt, a többi argumentum a burkolt eszközé.

  kinyer    `kinyer08`
  lanc      `lanc08 futtat` a valódi úttal (`lanc08v`)
  kiolvas   `kiolvas08`, a szelet `vB7` (a lánc utáni itemek)
  b1rel     `b1rel08`
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE)]
FORRAS = "B7"
ITEMS = EXP / "kor07/adat/b7/items"
GY = "kor08/adat/V"


def bejegyez():
    import lanc08 as L
    L.FORRASOK[FORRAS] = ("-", "kor07/adat/b7/items", None)
    regi = L.betolt
    L.betolt = lambda src, fam: [({}, it) for it in L.jsonl(ITEMS / f"{fam}.jsonl")] if src == FORRAS else regi(src, fam)
    return L


def kiolvas() -> None:
    import kiolvas08 as K8
    KI = K8.KI
    KI.ITEMS[f"v{FORRAS}"] = EXP / GY / f"G3/kinyert_{FORRAS}/items"
    KI.SZELETEK[f"v{FORRAS}"] = (FORRAS,)
    KI.FORRASOK = (*KI.FORRASOK, f"v{FORRAS}")
    KI.main()


def main() -> None:
    cmd, rest = sys.argv[1], sys.argv[2:]
    sys.argv = [f"v08 {cmd}", *rest]
    if cmd == "kinyer":
        bejegyez()
        import kinyer08
        import lanc08v
        lanc08v.kinyeres_kozlemenybol()
        kinyer08.main()
    elif cmd == "lanc":
        L = bejegyez()
        import lanc08v
        lanc08v.aktival()
        L.main()
    elif cmd == "kiolvas":
        kiolvas()
    elif cmd == "b1rel":
        import b1rel08
        b1rel08.main()
    else:
        raise SystemExit(f"ismeretlen parancs: {cmd}")


if __name__ == "__main__":
    main()
