"""06-os kör — a friss családok B1-kiolvasása (06-runbook 4., 9. F3) a 05 `hf_jellemzo05` útján.

A 05-ös kiolvasó a 03-as itemfájlokat és a `szeletek05.json`-t ismeri, és a v1a-manifest része, ezért nem módosítjuk:
ez a burkoló csak a betöltőjét (`load_items`) cseréli a 06-os itemekre (`kor06/adat/f2/items/<család>.jsonl`); a prompt,
a permutációk, a spanok, a rétegek és a sorformátum a 05-é. Szeletnév: `<család>:<szelet>`, például
`penzugy.bankparositas:T500`. A B1 a kanonikus sorrend jellemzőkkel, az 1–3. sorrend jellemzők nélkül (`b1` mód).

Pecsét (06-runbook 4.): a CAL és a TESZT kiolvasása csak a `cache/k06/pecset/` alá mehet, és rajtuk az `egyezes`
(modellkimenet) nem fut. Az itemszövegek nem pecsételtek, a `spanok` mindhárom szeleten futhat.

  python3 kor06/eszkozok/kiolvas06.py spanok --szelet penzugy.bankparositas:T500,… --out kor06/eredmenyek/F3/spanok
  python3 kor06/eszkozok/kiolvas06.py kivon --feladat penzugy.bankparositas:T500:kanonikus \\
      --feladat penzugy.bankparositas:T500:b1 --out-root cache/k06/jellemzok --status STATUS-K06F3
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok")]
import hf_jellemzo05 as H  # noqa: E402

ITEMS = EXP / "kor06/adat/f2/items"
PECSET = EXP / "cache/k06/pecset"
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
SZELETEK = ("T500", "CAL", "TESZT")
PECSETELT = ("CAL", "TESZT")


def load_items(names: list[str]) -> list[dict]:
    out = []
    for n in names:
        fam, sz = n.split(":")
        if fam not in CSALADOK or sz not in SZELETEK:
            raise SystemExit(f"ismeretlen szelet: {n}")
        items = [it for it in H.rows(ITEMS / f"{fam}.jsonl") if it["split"] == sz]
        if not items:
            raise SystemExit(f"{n}: nincs item")
        out += items
    return out


def arg(argv: list[str], name: str) -> list[str]:
    return [argv[i + 1] for i, x in enumerate(argv[:-1]) if x == name]


def pecset_kapu(argv: list[str]) -> None:
    cmd = argv[0] if argv else ""
    if cmd == "kivon":
        szel = [f.rsplit(":", 1)[0].split(":")[1] for f in arg(argv, "--feladat")]
        root = (EXP / arg(argv, "--out-root")[0]).resolve() if arg(argv, "--out-root") else None
        if any(s in PECSETELT for s in szel) and (root is None or not (root == PECSET.resolve() or PECSET.resolve() in root.parents)):
            raise SystemExit(f"PECSÉT: a CAL és a TESZT kiolvasása csak a {PECSET.relative_to(EXP)} alá mehet")
        if any(s not in PECSETELT for s in szel) and root is not None and PECSET.resolve() in (root, *root.parents):
            raise SystemExit("a T500 kiolvasása nyitott, ne a pecsét alá kerüljön")
    if cmd == "egyezes" and any(n.split(":")[1] in PECSETELT for x in arg(argv, "--szelet") for n in x.split(",")):
        raise SystemExit("PECSÉT: az egyezés-ellenőrzés modellkimenet, a CAL-on és a TESZT-en nem fut")


def main() -> None:
    pecset_kapu(sys.argv[1:])
    H.load_items = load_items
    H.main()


if __name__ == "__main__":
    main()
