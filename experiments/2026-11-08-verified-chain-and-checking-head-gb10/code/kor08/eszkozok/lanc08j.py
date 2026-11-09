"""08 javító kör (J; 11-05, Dani: „indulhat a javító kör”; nem rögzített) — a lánc ellenőrzésének két javítása burkolóként: a
rögzített `lanc08` nem változik, az `aktival()` a modul `helye` és `ellenoriz` nevét cseréli (a lánc ezeken át hívja).

  J1  a forrásrészlet helye ékezet- és kisbetű-érzéketlenül is (a G5 friss mintáján a szabálycsalád 38 eldobott mezőjéből 37
      csak ezen bukott). A pozíció az eredeti szövegben marad, az érték ellenőrzése nem lazul.
  J2  a mérés átváltott értéke (az alany az „1,2 kOhm”-ból 1200-at ír, a forrásrészletben pedig nincs 1200): ha az érték a
      forrásrészletben nincs, de pontosan egy, az egység előtt álló szám az alapegységre vagy a szabály egységére átváltva
      pontosan az érték, a mező értéke a szöveg száma lesz. Az átváltás innen a lánc dolga. A más hibás érték továbbra is bukik.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent)]
import lanc08 as L  # noqa: E402

_HELYE, _ELLENORIZ = L.helye, L.ellenoriz


def _fold(text: str) -> tuple[str, list[int]]:
    """A szöveg ékezet és kisbetű nélkül, karakterenként az eredeti pozícióval."""
    ki, poz = [], []
    for i, c in enumerate(text):
        for d in "".join(x for x in unicodedata.normalize("NFD", c) if not unicodedata.combining(x)).lower():
            ki.append(d)
            poz.append(i)
    return "".join(ki), poz


def helye(text: str, resz: str) -> tuple[int, int] | None:
    h = _HELYE(text, resz)
    if h is not None:
        return h
    toks = [re.escape(t) for t in _fold(resz)[0].split()]
    if not toks:
        return None
    t, poz = _fold(text)
    m = re.search(r"\s+".join(toks), t)
    return (poz[m.start()], poz[m.end() - 1] + 1) if m else None


def _visszavalt(fam: str, text: str, lang: str, f: dict, rule_u: dict) -> dict:
    """A mérés átváltott értéke helyett a szöveg száma (J2); ha nem egyértelmű, a mező változatlan."""
    if f.get("szerep") != "meres":
        return f
    v, u = L._ertek(f.get("ertek"), lang), str(f.get("egyseg") or "").strip()
    h = helye(text, str(f.get("forras") or ""))
    if v is None or not u or h is None or L.egyseg(u) is None:
        return f
    bent = [(a, b, x) for a, b, x in L.szamok(text, lang) if h[0] <= a and b <= h[1]]
    if any(L.egyezik(x, v) for _, _, x in bent):
        return f
    ru = rule_u.get(L.norm(str(f.get("kapcsolat") or "")))
    alap = L.egyseg(u)[1]
    jo = [x for a, b, x in bent if re.match(r"\s*" + re.escape(u) + r"(?![\w/])", text[b:b + len(u) + 4], re.I)
          and (L.egyezik(x * alap, v) or (ru is not None and L.valt(x, u, ru) is not None and L.egyezik(L.valt(x, u, ru), v)))]
    return {**f, "ertek": jo[0], "ertek_alany": v} if len(jo) == 1 else f


def ellenoriz(fam: str, text: str, lang: str, mezok: list[dict], jel: list[dict]) -> tuple[list[dict], list[dict]]:
    rule_u = {L.norm(j["meres"]): j["egyseg"] for j in jel} if fam == L.HIBA else {}
    return _ELLENORIZ(fam, text, lang, [_visszavalt(fam, text, lang, f, rule_u) if isinstance(f, dict) else f for f in mezok], jel)


def aktival() -> None:
    L.helye, L.ellenoriz = helye, ellenoriz


def kikapcsol() -> None:
    L.helye, L.ellenoriz = _HELYE, _ELLENORIZ
