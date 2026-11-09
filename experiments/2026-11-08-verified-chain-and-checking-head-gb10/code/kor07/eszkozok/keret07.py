"""07-es kör — a négyállapotú prompt kerete (07-runbook 2.2, D1).

A B1 a 06 keretében az opciók mellett egyetlen kiutat kapott (X „Egyik sem”); itt hármat: X „nincs megfelelő opció”,
Y „hiányzik a döntéshez szükséges adat”, Z „a kérés kívül esik a feladaton”. A három állapot mindig az opciók után,
rögzített sorrendben áll; a valódi opciók keverése a 06-é (ugyanaz a seed, ugyanaz az item-id), így a két keret
ugyanazokat a sorrendeket látja.

Megvalósítás: az Y és a Z ál-opcióként kerül az item opciói közé (`item4`, csak memóriában; az itemfájl nem
változik), ál-opció-id-vel (`::Y`, `::Z`). Így a 05 kiolvasójának spanjai, sorai és a `kalib05.option_scores` kulcsai
változtatás nélkül működnek: az X kulcsa None, az Y-é `::Y`, a Z-é `::Z`.

A gold a tartalmi állapotból: MATCH → az opció, NO_MATCH → X, MISSING_DATA → Y, OUT_OF_SCOPE → Z.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok"), str(EXP / "kor03/eszkozok"), str(EXP / "eszkozok")]
import common as C  # noqa: E402
import kozos03 as K3  # noqa: E402
from allapot05 import content_state  # noqa: E402

Y_ID, Z_ID = "::Y", "::Z"  # ál-opció-id (az itemek opció-id-i közt nem fordul elő)
Y_LABEL, Z_LABEL = "Y", "Z"
ALLAPOT = {
    "hu": {"X": "Nincs megfelelő opció", "Y": "Hiányzik a döntéshez szükséges adat", "Z": "A kérés kívül esik a feladaton"},
    "en": {"X": "No suitable option", "Y": "The data needed for the decision is missing",
           "Z": "The request is outside the task"},
}
STATE_KEY = {"NO_MATCH": None, "MISSING_DATA": Y_ID, "OUT_OF_SCOPE": Z_ID}
KIND = {None: "NONE", Y_ID: "MISSING", Z_ID: "OOS"}  # a többi kulcs: SELECT


def item4(it: dict) -> dict:
    """Az item a két ál-opcióval."""
    f = ALLAPOT[it["lang"]]
    return {**it, "options": [*it["options"], {"id": Y_ID, "text": f["Y"]}, {"id": Z_ID, "text": f["Z"]}]}


def permutation(item: dict, perm_id: int, move_none: bool = False) -> list[str | None]:
    """A valódi opciók a 06 keverésével, utána rögzítve: X (None), Y, Z."""
    real = [o for o in item["options"] if o["id"] not in (Y_ID, Z_ID)]
    return [*C.permutation({**item, "options": real}, perm_id, move_none), Y_ID, Z_ID]


def labels_for(order: list[str | None]) -> list[str]:
    out, i = [], 0
    for oid in order:
        if oid is None:
            out.append(C.NONE_LABEL)
        elif oid == Y_ID:
            out.append(Y_LABEL)
        elif oid == Z_ID:
            out.append(Z_LABEL)
        else:
            out.append(C.OPTION_LABELS[i])
            i += 1
    return out


def messages(item: dict, order: list[str | None]) -> list[dict]:
    """A 03 generikus kerete (`kozos03.generic_user`) az X új szövegével; az Y és a Z az ál-opciók szövegével."""
    f = K3.GENERIC[item["lang"]]
    opts = {o["id"]: o for o in item["options"]}
    lines = []
    if item.get("state"):
        lines += [f["state"], item["state"].strip(), ""]
    lines += [f"{f['question']}: {item['question']}", f["options"]]
    for oid, lab in zip(order, labels_for(order)):
        if oid is None:
            lines.append(f"{lab}) {ALLAPOT[item['lang']]['X']}")
            continue
        o = opts[oid]
        lines.append(f"{lab}) {o['text']}" + (f" — {o['use_when']}" if o.get("use_when") else ""))
    return [{"role": "system", "content": f["system"]}, {"role": "user", "content": "\n".join(lines)}]


def gold_key(item: dict) -> str | None:
    st = content_state(item)
    return item["gold"] if st == "MATCH" else STATE_KEY[st]


def gold_label(item: dict, order: list[str | None]) -> str:
    g = gold_key(item)
    return next(lab for oid, lab in zip(order, labels_for(order)) if oid == g)


def kind_of(key: str | None) -> str:
    return KIND.get(key, "SELECT")
