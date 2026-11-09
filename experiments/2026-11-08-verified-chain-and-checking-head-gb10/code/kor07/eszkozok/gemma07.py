"""07-es kör — a Gemma 4 második ítéletének összesítése a friss CAL + TESZT-en (07-runbook 3.2; a 06 D14–D15 protokollja),
a 06 `gemma06` burkolása 07-es útvonalakkal (a 06 kódja változatlan). A kiolvasás a spark-deven fut (`k07f2_gemma.sh`,
a 03 `kiolvaso03` ids-módja), ez a script helyben összesít (a 03 val-temperature és az auditkulcsok itt vannak):
  - itemenként a négy sorrend átlaga, a Gemma választása és az egyezés a konstrukció címkéjével (a Gemma keretében csak
    „egyik sem” van: a NO_MATCH, a MISSING_DATA és az OUT_OF_SCOPE egyaránt X);
  - bontás család × állapot × nyelv × szelet szerint, a legkisebb egyezésű sabloncsoportok (rendszerszintű hiba gyanúja);
  - az audit kulcsaira a Gemma ítélete (`kor07/adat/f2/audit/gemma_itelet.json`) — **Dani vak exportja után nyitandó**.
Triage: itemet nem töröl, nem javít (D15).

  python3 kor07/eszkozok/gemma07.py osszesit --olvasas kor07/eredmenyek/F2/gemma/gemma_f2.jsonl
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor06/eszkozok")]
import gemma06 as G  # noqa: E402

G.ITEMS = EXP / "kor07/adat/f2/items"
G.AUDIT = {1: EXP / "kor07/adat/f2/audit", 2: EXP / "kor07/adat/f2/audit/kor2"}
G.OUT = EXP / "kor07/eredmenyek/F2/gemma"
G.JELOLT = EXP / "kor07/adat/f2/gemma"


def main() -> None:
    G.main()
    md = G.OUT / "osszesito.md"
    if md.exists():
        md.write_text(md.read_text(encoding="utf-8").replace("# A Gemma második ítélete a friss családokon (06, F2)",
                                                             "# A Gemma második ítélete a friss CAL + TESZT-en (07, F2)"),
                      encoding="utf-8")


if __name__ == "__main__":
    main()
