"""07-es kör — a négyállapotú B1-kiolvasás a 05 `hf_jellemzo05` útján (07-runbook 2.2, F1, F3).

A 05 kiolvasója a v1a-manifest része, nem módosítjuk; ez a burkoló a betöltőjét, a keverését, a címkézését és a
promptját cseréli a `keret07`-re (a spanok, a jellemzők, a shardolás és a sorformátum a 05-é), és a tokenizert a két
új címkével (Y, Z) egészíti ki. Szeletnevek:
  k06:<család>:<T500|CAL|TESZT>   a 06 itemjei (a 06 v1 rögzítése óta nyitottak: tervezési próba, F1)
  nehez:<család>:NEHEZ            a nehéz próbaminta (`kor07/adat/nehez/items/`, `szint07`; F1)
  <család>:<T500|CAL|TESZT>       a 07 friss itemjei (`kor07/adat/items/`); a CAL és a TESZT pecsét alatt (F3)

`--keret 2`: a 06 kétkimenetű kerete (opciók + X „Egyik sem”, a 05 promptja változatlanul), csak a betöltő cserélve; a
kimenet külön könyvtárba menjen (`--out-root cache/k07/jellemzok2`). Alapból a négyállapotú keret.

Pecsét: a 07 CAL és TESZT kiolvasása csak a `cache/k07/pecset/` alá mehet, és rajtuk az `egyezes` nem fut.

  python3 kor07/eszkozok/kiolvas07.py spanok --szelet k06:penzugy.bankparositas:T500 --perms-is --out kor07/eredmenyek/F0/spanok
  python3 kor07/eszkozok/kiolvas07.py kivon --feladat k06:penzugy.bankparositas:T500:kanonikus \\
      --feladat k06:penzugy.bankparositas:T500:b1 --out-root cache/k07/jellemzok --status STATUS-K07F1
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import common as C  # noqa: E402
import hf_jellemzo05 as H  # noqa: E402
import keret07 as K7  # noqa: E402

ITEMS = {"k06": EXP / "kor06/adat/f2/items", "nehez": EXP / "kor07/adat/nehez/items",
         "nehez2": EXP / "kor07/adat/nehez2/items", "": EXP / "kor07/adat/f2/items"}
PECSET = EXP / "cache/k07/pecset"
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
SZELETEK = {"k06": ("T500", "CAL", "TESZT"), "nehez": ("NEHEZ",), "nehez2": ("NEHEZ",), "": ("CAL", "TESZT")}
FORRASOK = ("k06", "nehez", "nehez2", "k05")
K05_SZELETEK = ("D_meta",)  # a 05 szeletei a 05 betöltőjével (szeletek05.json + a 03 itemfájljai); nyitottak
PECSETELT = ("CAL", "TESZT")  # csak a 07 friss szeleteinél
KERET = {"n": 4}  # a `--keret` kapcsoló
_load05 = H.load_items


def szelet(n: str) -> tuple[str, str, bool]:
    """(család vagy 05-szelet, szelet, pecsételt-e)."""
    p = n.split(":")
    src = p[0] if p[0] in FORRASOK else ""
    if src == "k05":
        if len(p) != 2 or p[1] not in K05_SZELETEK:
            raise SystemExit(f"ismeretlen 05-szelet: {n}")
        return p[1], p[1], False
    q = p[1:] if src else p
    if len(q) != 2 or q[0] not in CSALADOK or q[1] not in SZELETEK[src]:
        raise SystemExit(f"ismeretlen szelet: {n}")
    return q[0], q[1], src == "" and q[1] in PECSETELT


def load_items(names: list[str]) -> list[dict]:
    out = []
    for n in names:
        fam, sz, _ = szelet(n)
        src = n.split(":")[0] if n.split(":")[0] in FORRASOK else ""
        if src == "k05":
            items = _load05([sz])
            if any("native" in it for it in items):
                raise SystemExit(f"{n}: natív keretű item a szeletben; a keret07 csak generikus")
        else:
            items = [it for it in H.rows(ITEMS[src] / f"{fam}.jsonl") if it["split"] == sz]
        if KERET["n"] == 4:
            items = [K7.item4(it) for it in items]
        if not items:
            raise SystemExit(f"{n}: nincs item")
        out += items
    return out


class PromptTokenizer07(C.PromptTokenizer):
    def __init__(self, path=C.SUBJECT_SNAPSHOT):
        super().__init__(path)
        for lab in (K7.Y_LABEL, K7.Z_LABEL):
            self.label_ids[lab] = self._single_id(lab)


_forward = H.forward


def forward(model, pt, sp, item: dict, perm: int, features: bool):
    """A 05 forwardja; a gold-címke a négy állapot szerint (a 05-é minden X-goldra X-et írna)."""
    row, feat = _forward(model, pt, sp, item, perm, features)
    row["gold_label"] = K7.gold_label(item, row["order"])
    row["gold_key"] = K7.gold_key(item)
    row["keret"] = "4allapot"
    return row, feat


def arg(argv: list[str], name: str) -> list[str]:
    return [argv[i + 1] for i, x in enumerate(argv[:-1]) if x == name]


def pecset_kapu(argv: list[str]) -> None:
    cmd = argv[0] if argv else ""
    if cmd == "kivon":
        sealed = [szelet(f.rsplit(":", 1)[0])[2] for f in arg(argv, "--feladat")]
        root = (EXP / arg(argv, "--out-root")[0]).resolve() if arg(argv, "--out-root") else None
        under = root is not None and (root == PECSET.resolve() or PECSET.resolve() in root.parents)
        if any(sealed) and not under:
            raise SystemExit(f"PECSÉT: a 07 CAL és TESZT kiolvasása csak a {PECSET.relative_to(EXP)} alá mehet")
        if not all(sealed) and under:
            raise SystemExit("a nyitott szeletek kiolvasása ne a pecsét alá kerüljön")
    if cmd == "egyezes" and any(szelet(n)[2] for x in arg(argv, "--szelet") for n in x.split(",")):
        raise SystemExit("PECSÉT: az egyezés-ellenőrzés modellkimenet, a 07 CAL-on és TESZT-en nem fut")


def main() -> None:
    argv = sys.argv[1:]
    if "--keret" in argv:
        i = argv.index("--keret")
        KERET["n"] = int(argv[i + 1])
        if KERET["n"] not in (2, 4):
            raise SystemExit("--keret 2 vagy 4")
        sys.argv[1:] = argv[:i] + argv[i + 2:]
    pecset_kapu(sys.argv[1:])
    H.load_items = load_items
    if KERET["n"] == 4:
        H.permutation = K7.permutation
        H.labels_for = K7.labels_for
        H.messages = K7.messages
        H.forward = forward
        C.PromptTokenizer = PromptTokenizer07
    H.main()


if __name__ == "__main__":
    main()
