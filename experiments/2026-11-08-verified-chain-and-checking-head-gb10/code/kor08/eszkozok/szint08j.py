"""08 javító kör (J) — a friss K3-típusú minta generátora: a rögzített `szint08` változatlanul, friss sablon-id-kkal (`k08j`, a
korábbi készletektől diszjunkt), családonként nyelvenként 30 sablonon, és nagyobb darabszámmal (J-rögzítés 3.). A parancsok a
`szint08`-éi, a rész mindig `k3`; a kimenet `kor08/adat/J/` (`J_GYOKER`). Az item-id és a szelet `J1K3`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import szint08 as T  # noqa: E402

SABLON = 30  # nyelvenként
N = {T.BANK: 220, T.HIBA: 220, T.SZAB: 110}  # változatonként
T.GYOKER["d"] = T.EXP / os.environ.get("J_GYOKER", "kor08/adat/J")
_TERV = T.terv_k3


def sablon_ids(fam: str, _proba: bool = False) -> list[tuple[str, str, str]]:
    return [(f"{fam}:k08j:{lang}:{i:03d}", lang, "K3") for lang in T.S.LANGS for i in range(SABLON)]


def terv_k3(fam: str) -> list[dict]:
    T.K3_N = N[fam]
    return [{**p, "szelet": "J1K3", "group_id": p["group_id"].replace(":G2K3:", ":J1K3:")} for p in _TERV(fam)]


T.sablon_ids08 = sablon_ids
T.terv_k3 = terv_k3

if __name__ == "__main__":
    T.main()
