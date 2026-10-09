"""Családon kívüli, a számlasor alapján megkülönböztethetetlen opciók (az S8 kiterjesztése, 2026-10-04).

A runbook 4.2 S1 dedupot ír elő (normalizált név + bge-m3 koszinusz > 0,95); a generátor csak a pontos
normalizált nevet szűrte, így a katalógusban szórend- és ragozás-változatok maradtak („Edami sajt” /
„Sajt edami 1 kg”, „Kartonos pizzás doboz” / „Karton pizza doboz”). Az S8 csak a családon BELÜLI
testvéreket nézte. Ez a modul a családon KÍVÜLI, azonos alkategóriájú opciókra dönti el, hogy a sor
megkülönbözteti-e a goldot (X-itemnél a valódi cikket) az opciótól.

Szabály (lexikai, determinisztikus; a téves pozitív csak a pontozott itemek számát csökkenti):
  - a két név szám/mértékegység-tokenjei egyeznek;
  - a normalizált szótokenek (kisbetű, ékezet nélkül, írásjel nélkül; ragozás-ekvivalencia) Jaccard ≥ 0,5;
  - a különbség-szavak egyike sem szerepel a sorban (rövidítve, ≥ 3 karakteres előtagként sem), ÉS nem az az
    eset, hogy csak az opciónak van plusz minősítője („Sajt Gouda” vs „Rántott sajt Gouda”: a sor a goldot írja le)
    → megkülönböztethetetlen.
"""

from __future__ import annotations

import re
import unicodedata

NUM = re.compile(r"\d+(?:[.,]\d+)?\s?(?:%|kg|dkg|g|l|dl|cl|ml|db|cm|mm|m)?(?![\wáéíóöőúüű])", re.I)
WORD = re.compile(r"[a-z]+")


def fold(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def nums(s: str) -> tuple[str, ...]:
    return tuple(sorted(re.sub(r"\s", "", m.group(0)).lower().replace(".", ",") for m in NUM.finditer(s)))


# Mennyiség alapegységre váltva (2026-10-05, Dani: „Kenyér fehér 1000 g” / „Kenyér fehér 1 kg” — szövegként eltér)
# A térfogat és a tömeg 1-es sűrűséggel egyenértékű (2026-10-05, Dani: „Savanyú Tejföl 20% 2 dl” / „Tejföl 20% 200 g” =
# ugyanaz a kiszerelés): tejterméknél, italnál, tisztítószernél a gyakorlatban így; a szó-egyezés feltétele marad.
UNIT_BASE = {"kg": (1000, "g"), "dkg": (10, "g"), "g": (1, "g"), "l": (1000, "g"), "dl": (100, "g"), "cl": (10, "g"),
             "ml": (1, "g"), "db": (1, "db"), "%": (1, "%"), "m": (1000, "mm"), "cm": (10, "mm"), "mm": (1, "mm")}
QTY = re.compile(r"(\d+(?:[.,]\d+)?)\s?(%|kg|dkg|g|l|dl|cl|ml|db|cm|mm|m)?(?![\wáéíóöőúüű])", re.I)


def qtys(s: str) -> frozenset[tuple[float, str]]:
    """A név mennyiségei alapegységben: {(érték, alapegység)}; mértékegység nélküli szám: (érték, "")."""
    out = set()
    for m in QTY.finditer(s):
        v = float(m.group(1).replace(",", "."))
        f, base = UNIT_BASE.get((m.group(2) or "").lower(), (1, ""))
        out.add((round(v * f, 6), base))
    return frozenset(out)


def words(s: str) -> list[str]:
    return [w for w in WORD.findall(fold(NUM.sub(" ", s))) if len(w) >= 2]


def equiv(a: str, b: str) -> bool:
    """Azonos szó vagy ragozási változat: közös előtag ≥ 4, és mindkét maradék ≤ 3 karakter."""
    if a == b:
        return True
    k = 0
    while k < min(len(a), len(b)) and a[k] == b[k]:
        k += 1
    return k >= 4 and len(a) - k <= 3 and len(b) - k <= 3


def _diff(xs: list[str], ys: list[str]) -> list[str]:
    return [x for x in xs if not any(equiv(x, y) for y in ys)]


def indistinguishable(line: str, gold_name: str, opt_name: str) -> bool:
    if qtys(gold_name) != qtys(opt_name):  # alapegységben (1000 g = 1 kg); F1C–F1G-ben szövegként (nums)
        return False
    g, o = sorted(set(words(gold_name))), sorted(set(words(opt_name)))
    if not g or not o:
        return False
    dg, do = _diff(g, o), _diff(o, g)
    inter = len(g) - len(dg)
    if inter / (len(g) + len(do)) < 0.5:
        return False
    lw = set(words(line))
    if any(any(equiv(d, w) or (len(w) >= 3 and d.startswith(w)) for w in lw) for d in dg + do):
        return False  # a sor tartalmaz megkülönböztető szót (rövidítve is)
    # csak az opciónak van a sorban nem szereplő minősítője → a sor pontosan a goldot írja le
    return not (not dg and do)


# --- S8 kiterjesztés v2 (2026-10-05, Dani második átnézése) ---------------------------------------------------------
# Két, a duplikátum-kizárás után maradt hibaforrás: (1) ugyanaz a termék más méretben, KÜLÖN családban (a családon
# belüli méret-testvért az S8 attribútum-szabálya kezeli), és a sor nem hordozza a méretet („CheeseMaster trapipsta (”
# mellett Trappista 5 kg / 1 kg / 500 g); (2) a csonkolás után csak kód + márka maradt a sorban („209560 Pannon
# Sajtmanufaktúra”). Mindkettő kétértelmű: a termék a listán van, de nem dönthető el, melyik.

NUMV = re.compile(r"\d+(?:[.,]\d+)?")


def numvals(s: str) -> set[float]:
    return {float(m.group(0).replace(",", ".")) for m in NUMV.finditer(s)}


def same_words(a: str, b: str) -> bool:
    """A két név szótokenjei (számok nélkül) kölcsönösen ragozás-ekvivalensek."""
    wa, wb = sorted(set(words(a))), sorted(set(words(b)))
    return bool(wa) and all(any(equiv(x, y) for y in wb) for x in wa) and all(any(equiv(y, x) for x in wa) for y in wb)


def size_ambiguous(line: str, true_name: str, opt_name: str) -> bool:
    """Csak mennyiségben (méret, kiszerelés; alapegységben vetve össze) eltérő változat, és a sor a valódi cikk egyetlen
    mennyiségét sem hordozza (sem nyers számértékként, sem alapegységben)."""
    if qtys(true_name) == qtys(opt_name) or not same_words(true_name, opt_name):
        return False
    return not ((numvals(true_name) & numvals(line)) or (qtys(true_name) & qtys(line)))


def uninformative(line: str, true_name: str, brand: str | None) -> bool:
    """A sor nem nevezi meg a terméket: egyetlen szava sem illik a valódi cikk nevére, és a márka szavai (a ≥ 4 betűs
    csonkjaikkal), a számok és a kódok levétele után nem marad ≥ 3 betűs szó."""
    wl = [w for w in words(line) if len(w) >= 3]
    tw = [t for t in words(true_name) if len(t) >= 3]
    if any(equiv(w, t) or t.startswith(w) or w.startswith(t) for w in wl for t in tw):
        return False
    bw = set(words(brand or ""))
    return not [w for w in wl if not any(equiv(w, b) or (len(w) >= 4 and b.startswith(w)) for b in bw)]
