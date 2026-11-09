"""07-es kör — a mentett fejek pontozása a K3 utáni nyitott mintákon: a `b1rel07 pontoz` változatlanul, két új
szeletforrással (a `b1rel07k3` a K3 manifestjében van, ezért külön burkoló).

  aug:<család>   a végső diagnosztikai minta a kiszámított sorral (`kiolvas07x` diagaug kimenete)
  b7:<család>    a 07B valódi banki tételei (`kiolvas07x` b7 kimenete; a fejek a család sajátjai)

A kiolvasás könyvtárait (`<forrás>_<család>_<szelet>__<mód>`) a `cache/k07/x_link/<forrás>/` alatti symlinkek
igazítják a `<család>_<szelet>__<mód>` alakhoz (a `b1rel06.jell_dir` ezt várja).
  python3 kor07/eszkozok/b1rel07x.py pontoz --szelet b7:penzugy.bankparositas --out cache/k07/b7
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1rel07 as R  # noqa: E402

EXP = R.EXP
LINK = EXP / "cache/k07/x_link"
FORRAS = {"aug": ("diagaug", "DIAG", EXP / "kor07/adat/diagaug/items"),
          "b7": ("b7", "B7", EXP / "kor07/adat/b7/items")}


def gyokerek(src: str, fam: str, sz: str) -> tuple[Path, Path]:
    for kr, root in (("jellemzok", R.JELL07), ("jellemzok2", EXP / "cache/k07/jellemzok2")):
        d = LINK / src / kr
        d.mkdir(parents=True, exist_ok=True)
        for mod in ("kanonikus", "b1"):
            ln = d / f"{fam}_{sz}__{mod}"
            if not ln.exists():
                os.symlink(os.path.relpath(root / f"{src}_{fam}_{sz}__{mod}", d), ln)
    return LINK / src / "jellemzok", LINK / src / "jellemzok2"


def szelet_forras(nev: str) -> tuple[str, str, str, Path, Path]:
    p = nev.split(":")
    if len(p) != 2 or p[0] not in FORRAS or p[1] not in R.CSALADOK:
        raise SystemExit(f"ismeretlen szelet: {nev} (aug:<család> vagy b7:<család>)")
    src, sz, _ = FORRAS[p[0]]
    r4, r2 = gyokerek(src, p[1], sz)
    return p[1], sz, f"{p[1]}_{sz}", r4, r2


def meta07_reszleges() -> dict:
    """A `b1rel07.meta07` a forrás meglévő családfájljain (a 07B-nek csak bankcsaládja van)."""
    csaladok = R.CSALADOK
    try:
        R.CSALADOK = tuple(f for f in csaladok if (R.ITEMS07 / f"{f}.jsonl").exists())
        return META07()
    finally:
        R.CSALADOK = csaladok


META07 = R.meta07


def main() -> None:
    nev = sys.argv[sys.argv.index("--szelet") + 1] if "--szelet" in sys.argv else ""
    if nev.split(":")[0] in FORRAS:
        R.ITEMS07 = FORRAS[nev.split(":")[0]][2]  # a `meta07` innen olvassa a 06-os keret helyességéhez
        R.meta07 = meta07_reszleges
    R.szelet_forras = szelet_forras
    R.main()
    out = EXP / sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out and out.exists():
        os.chmod(out, 0o777)
        for x in out.glob("*.json"):
            os.chmod(x, 0o666)


if __name__ == "__main__":
    main()
