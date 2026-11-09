"""07-es kör — a mentett fejek pontozása a végső diagnosztikai mintán (K3): a `b1rel07 pontoz` változatlanul, két új
szeletforrással.

  diag:<család>    a végső minta, a K3 pecsétje alól (`pecset07k3.kapu`: csak a `rogzit07k3 nyit` után)
  proba:<család>   a 3. kör nyitott fejlesztési mintája (`cache/k07/jellemzok[2]/nehez3_<család>_NEHEZ__*`), a
                   pontozó és a `k3_07 proba` útjának kipróbálásához; a könyvtárneveket a `cache/k07/k3_proba/` alatti
                   symlinkek igazítják a `<család>_<szelet>__<mód>` alakhoz (a `b1rel06.jell_dir` ezt várja)

  python3 kor07/eszkozok/b1rel07k3.py pontoz --szelet diag:penzugy.bankparositas --out cache/k07/k3
  python3 kor07/eszkozok/b1rel07k3.py pontoz --szelet proba:penzugy.bankparositas --out cache/k07/k3_proba/pontoz
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1rel07 as R  # noqa: E402

EXP = R.EXP
PROBA = EXP / "cache/k07/k3_proba"
ITEMS = {"diag": EXP / "kor07/adat/diag/items", "proba": EXP / "kor07/adat/nehez3/items"}


def proba_gyokerek(fam: str) -> tuple[Path, Path]:
    for kr, src in (("jellemzok", R.JELL07), ("jellemzok2", EXP / "cache/k07/jellemzok2")):
        (PROBA / kr).mkdir(parents=True, exist_ok=True)
        for mod in ("kanonikus", "b1"):
            ln = PROBA / kr / f"{fam}_NEHEZ__{mod}"
            if not ln.exists():
                os.symlink(os.path.relpath(src / f"nehez3_{fam}_NEHEZ__{mod}", ln.parent), ln)
    return PROBA / "jellemzok", PROBA / "jellemzok2"


def szelet_forras(nev: str) -> tuple[str, str, str, Path, Path]:
    p = nev.split(":")
    if len(p) != 2 or p[0] not in ITEMS or p[1] not in R.CSALADOK:
        raise SystemExit(f"ismeretlen szelet: {nev} (diag:<család> vagy proba:<család>)")
    fam = p[1]
    if p[0] == "proba":
        r4, r2 = proba_gyokerek(fam)
        return fam, "NEHEZ", f"{fam}_NEHEZ", r4, r2
    import pecset07k3  # noqa: PLC0415

    pecset07k3.kapu(pecset07k3.P.PECSET)
    return fam, "DIAG", f"{fam}_DIAG", pecset07k3.P.PECSET / "jellemzok", pecset07k3.P.PECSET / "jellemzok2"


def main() -> None:
    nev =sys.argv[sys.argv.index("--szelet") + 1] if "--szelet" in sys.argv else ""
    R.ITEMS07 = ITEMS.get(nev.split(":")[0], R.ITEMS07)  # a `meta07` innen olvassa a 06-os keret helyességéhez
    R.szelet_forras = szelet_forras
    R.main()
    out = EXP / sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    if out and out.exists():  # a konténer root-ként ír: a gazdagép felhasználója is olvashassa és törölhesse
        os.chmod(out, 0o777)
        for x in out.glob("*.json"):
            os.chmod(x, 0o666)


if __name__ == "__main__":
    main()
