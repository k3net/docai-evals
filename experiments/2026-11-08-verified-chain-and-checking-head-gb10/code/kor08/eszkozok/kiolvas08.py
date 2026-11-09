"""08 — a lánc utáni itemek kiolvasása a `kiolvas07` útján (a `kiolvas07` változatlan; négyállapotú keret). A források
a `lanc08 futtat` kimenetei (`kor08/adat/G1/<út>_<forrás>/items`), az itemek az eredeti szeletnevükkel.

  l06:<család>:<T500|CAL|TESZT>:<mód>   a 06 szeletei a lánc után (valós kinyerés)
  o06, l07, o07, lK3, oK3              ugyanez orákulum-úton (o…), a 07 CAL / TESZT-jén és a K3 diag-on
  oERT:<család>:ERT:<mód>               a G1b értelmezési konstrukciója a lánc után (orákulum-út)
  oK3v0…oK3v4, o06v0…o06v4            a K3 diag és a 06 T500 a szabálycsalád blokk-változataival (orákulum-út)
  det0, det1:szabaly.koltsegelszamolas:T500:kanonikus   a determinizmus-őr referenciaszelete (`det_or08`)

A kimeneti könyvtár `<forrás>_<család>_<szelet>__<mód>`.
  python3 kor08/eszkozok/kiolvas08.py kivon --feladat lK3:penzugy.bankparositas:DIAG:kanonikus ... --out-root cache/k08/jellemzok
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path.insert(0, str(EXP / "kor07/eszkozok"))
import kiolvas07 as KI  # noqa: E402

G1 = EXP / "kor08/adat/G1"
for ut, elo in (("kinyert", "l"), ("orakulum", "o")):
    for src, sz in (("06", ("T500", "CAL", "TESZT")), ("07", ("CAL", "TESZT")), ("K3", ("DIAG",)), ("ERT", ("ERT",)),
                    ("ERT2", ("ERT2",)), ("ERT2J", ("ERT2J",))):
        nev = f"{elo}{src}"
        KI.ITEMS[nev] = G1 / f"{ut}_{'K3diag' if src == 'K3' else src}" / "items"
        KI.SZELETEK[nev] = sz
        KI.FORRASOK = (*KI.FORRASOK, nev)
for v in ("v0", "v1", "v2", "v3", "v4"):  # a szabálycsalád blokk-változatai, orákulum-úton (`lanc08.BLOKK_VALTOZAT`):
    # a K3 diag-on (G1-próba) és a 06 T500-án (célzott próba a téves SELECT-ek ellen, Dani 11-02)
    for src, d, sz in (("K3", "K3diag", ("DIAG",)), ("06", "06", ("T500",))):
        KI.ITEMS[f"o{src}{v}"] = G1 / f"orakulum_{d}_{v}" / "items"
        KI.SZELETEK[f"o{src}{v}"] = sz
        KI.FORRASOK = (*KI.FORRASOK, f"o{src}{v}")
for nev in ("det0", "det1"):  # a determinizmus-őr referenciaszelete (`det_or08`), a kiolvasás első és utolsó feladata
    KI.ITEMS[nev] = G1 / "det_ref" / "items"
    KI.SZELETEK[nev] = ("T500",)
    KI.FORRASOK = (*KI.FORRASOK, nev)
# G3: a G2 szeletei a lánc után (l…: valós kinyerés, o…: orákulum-út; `kor08/adat/G3/<út>_<forrás>`) és lánc nélkül
# (n…: az eredeti G2-item, a banki kérdés a feladatszabállyal; a 07 karjainak összevetéséhez). A pecsét alá (`pecset08`)
# minden értékelő szelet kerül; a tanítóminta (G2N) nem.
G2_SZELET = {"G2F": ("CAL", "TESZT"), "G2K3": ("G2K3",), "G2T": ("G2T",), "G2N": ("G2N",)}
G2_RESZ = {"G2F": "friss", "G2K3": "k3", "G2T": "ert_teszt", "G2N": "ert_tanito"}
PECSETELT = set()
for src, sz in G2_SZELET.items():
    for ut, elo in (("kinyert", "l"), ("orakulum", "o"), (None, "n")):
        nev = f"{elo}{src}"
        KI.ITEMS[nev] = EXP / "kor08/adat/G2" / G2_RESZ[src] / "items" if ut is None else EXP / "kor08/adat/G3" / f"{ut}_{src}" / "items"
        KI.SZELETEK[nev] = sz
        KI.FORRASOK = (*KI.FORRASOK, nev)
        if src != "G2N":
            PECSETELT.add(nev)
PECSET = EXP / "cache/k08/pecset"


def pecset_kapu(argv: list[str]) -> None:
    """A G2 értékelő szeleteinek kiolvasása csak a pecsét alá mehet, a nyitott szeleteké nem."""
    if not argv or argv[0] != "kivon":
        return
    nevek = [f.split(":")[0] for f in KI.arg(argv, "--feladat")]
    root = (EXP / KI.arg(argv, "--out-root")[0]).resolve() if KI.arg(argv, "--out-root") else None
    alatta = root is not None and (root == PECSET.resolve() or PECSET.resolve() in root.parents)
    zart = [n for n in nevek if n in PECSETELT]
    if zart and not alatta:
        raise SystemExit(f"PECSÉT: a G2 értékelő szeletei ({', '.join(sorted(set(zart)))}) csak a {PECSET.relative_to(EXP)} alá mehetnek")
    if alatta and len(zart) != len([n for n in nevek if not n.startswith("det")]):
        raise SystemExit("a nyitott szeletek kiolvasása ne a pecsét alá kerüljön")


if __name__ == "__main__":
    pecset_kapu(sys.argv[1:])
    KI.main()
