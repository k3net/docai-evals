"""08 — az ellenőrzött számítási lánc (08-runbook 2.): kinyerés → ellenőrzés → számítás → szabályellenőrzés → a
modell döntése. A kinyerést az alany végzi (G1, vLLM, kötött JSON-séma), vagy az orákulum a terv tényeiből (ugyanaz a
lánc a helyes mezőkkel); az ellenőrzés, a számítás és a szabályellenőrzés kód.

A lánc minden jelöltről legfeljebb egy állítást tesz (2.1, D2):
  kizárt      bizonyított ellentmondás ellenőrzött mezőkön (a jelölt kikerül a listából)
  kötheto     az előre rögzített, elegendő kötési feltételek teljesülnek (csak a bankon)
  lehetseges  egyik sem: nincs elég információ, vagy nincs ellentmondás
Négy kimenet: `kotes` (automatikus kötés), `modell` üres listával, ha minden jelölt bizonyítottan kizárt (D2, Dani
11-02; a régi `lanc_x` csak összevetésre), `emberhez` (bukott ellenőrzés), `modell` (a megmaradt jelöltekkel). Ikrek
a modellhez mennek (D3): automatikus Y nincs.

A jelöltek szabályait a lánc a kóddal renderelt opciószövegből olvassa ki (a sablon formátumai; a K3-változatok
opciói is így készültek), nem a generátor tervéből; az `onteszt` ezt a sablonok strukturált adatával veti össze.

  python3 kor08/eszkozok/lanc08.py onteszt [--out kor08/eredmenyek/G0]
  python3 kor08/eszkozok/lanc08.py futtat --forras K3diag --ut orakulum --out <könyvtár> [--ures modell]
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
BANK, HIBA, SZAB = CSALADOK

# --- számok ------------------------------------------------------------------------------------------------------------

# a nyelv számformátuma: magyarul tizedesvessző és szóköz / pont ezres-elválasztó, angolul tizedespont és vessző
SZAM_RX = {
    "hu": re.compile(r"(?<!\d)(?<!\d[.,])(?:\d{1,3}(?:[   .]\d{3})+(?:,\d+)?|\d+(?:,\d+)?(?:[eE][-+]?\d+)?)(?!\d)"),
    "en": re.compile(r"(?<!\d)(?<!\d[.,])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?!\d)"),
}


def szam(s: str, lang: str) -> float | None:
    s = s.strip()
    if lang == "hu":
        s = re.sub(r"(?<=\d)[   .](?=\d{3}(?!\d))", "", s).replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def szamok(text: str, lang: str) -> list[tuple[int, int, float]]:
    """A szöveg számai pozícióval. Ha a nyelv formátuma nem illik (angol szövegben „4,2”), a másik nyelvé is."""
    out = []
    for lg in (lang, "en" if lang == "hu" else "hu"):
        for m in SZAM_RX[lg].finditer(text):
            v = szam(m.group(0), lg)
            if v is not None and not any(a <= m.start() < b for a, b, _ in out):
                a = m.start()
                # előjel: közvetlenül előtte mínusz, és az előtt nem számjegy (a „2026-10-08” nem negatív)
                if a > 0 and text[a - 1] in "-−" and (a == 1 or not text[a - 2].isdigit()):
                    v, a = -v, a - 1
                out.append((a, m.end(), v))
    return sorted(out)


def egyezik(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= max(tol, 1e-9 * max(abs(a), abs(b)))


def fmt(x: float, lang: str, tizedes: int | None = None) -> str:
    if tizedes is None:
        t = f"{x:,.0f}" if abs(x - round(x)) < 1e-9 else f"{x:,.2f}".rstrip("0").rstrip(".")
    else:
        t = f"{x:,.{tizedes}f}"
    return t.replace(",", " ").replace(".", ",") if lang == "hu" else t


def fmt_g(x: float, lang: str) -> str:
    """Mért érték kiírása kerekítés nélkül (legfeljebb hat értékes jegy)."""
    if abs(x) >= 1000 and abs(x - round(x)) < 1e-9:
        return fmt(x, lang)
    t = f"{x:.6g}"
    return t.replace(".", ",") if lang == "hu" else t


def penz(x: float, lang: str, deviza: str) -> str:
    if deviza == "HUF":
        return f"{fmt(round(x), lang)} Ft"
    return f"{fmt(x, lang, 2)} {deviza}" if lang == "hu" else f"{deviza} {fmt(x, lang, 2)}"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def norm_ref(s: str) -> str:
    return re.sub(r"[\s/\-_.]", "", s).upper()


def helye(text: str, resz: str) -> tuple[int, int] | None:
    """A forrásrészlet helye a szövegben, szóközökre érzéketlenül (a modell a sortörést szóközre cserélheti)."""
    toks = [re.escape(t) for t in resz.split()]
    if not toks:
        return None
    m = re.search(r"\s+".join(toks), text)
    return (m.start(), m.end()) if m else None


# --- mértékegységek (saját tábla; a K3 VALTAS-ával az onteszt veti össze) ------------------------------------------------

_EGYSEG = {  # alias → (dimenzió, szorzó az alapegységre)
    "v": ("feszultseg", 1), "volt": ("feszultseg", 1), "v dc": ("feszultseg", 1), "vdc": ("feszultseg", 1),
    "v ac": ("feszultseg", 1), "mv": ("feszultseg", 1e-3), "millivolt": ("feszultseg", 1e-3), "kv": ("feszultseg", 1e3),
    "µv": ("feszultseg", 1e-6), "uv": ("feszultseg", 1e-6),
    "a": ("aram", 1), "amper": ("aram", 1), "ampere": ("aram", 1), "a dc": ("aram", 1), "ma": ("aram", 1e-3),
    "milliamper": ("aram", 1e-3), "milliampere": ("aram", 1e-3), "µa": ("aram", 1e-6), "ua": ("aram", 1e-6),
    "bar": ("nyomas", 1e5), "mbar": ("nyomas", 100), "pa": ("nyomas", 1), "kpa": ("nyomas", 1e3), "mpa": ("nyomas", 1e6),
    "psi": ("nyomas", 6894.76),
    "m": ("hossz", 1), "mm": ("hossz", 1e-3), "millimeter": ("hossz", 1e-3), "cm": ("hossz", 1e-2), "km": ("hossz", 1e3),
    "µm": ("hossz", 1e-6), "um": ("hossz", 1e-6), "micrometer": ("hossz", 1e-6), "micron": ("hossz", 1e-6),
    "microm": ("hossz", 1e-6),
    "m/s": ("sebesseg", 1), "mm/s": ("sebesseg", 1e-3), "µm/s": ("sebesseg", 1e-6), "um/s": ("sebesseg", 1e-6),
    "km/h": ("sebesseg", 1 / 3.6),
    "s": ("ido", 1), "second": ("ido", 1), "mp": ("ido", 1), "ms": ("ido", 1e-3), "milliseconds": ("ido", 1e-3),
    "miliszekundum": ("ido", 1e-3), "µs": ("ido", 1e-6), "us": ("ido", 1e-6), "ns": ("ido", 1e-9), "min": ("ido", 60),
    "perc": ("ido", 60),
    "ohm": ("ellenallas", 1), "ω": ("ellenallas", 1), "mohm": ("ellenallas", 1e-3), "milliohm": ("ellenallas", 1e-3),
    "mω": ("ellenallas", 1e-3), "kohm": ("ellenallas", 1e3), "kω": ("ellenallas", 1e3), "megaohm": ("ellenallas", 1e6),
    "mω_mega": ("ellenallas", 1e6),
    "hz": ("frekvencia", 1), "khz": ("frekvencia", 1e3), "mhz": ("frekvencia", 1e6), "rpm": ("frekvencia", 1 / 60),
    "ford/perc": ("frekvencia", 1 / 60),
    "l/min": ("terfaram", 1 / 60000), "l/perc": ("terfaram", 1 / 60000), "l/h": ("terfaram", 1 / 3.6e6),
    "ml/min": ("terfaram", 1 / 6e7), "ml/perc": ("terfaram", 1 / 6e7), "ml/h": ("terfaram", 1 / 3.6e9),
    "m3/h": ("terfaram", 1 / 3600), "m³/h": ("terfaram", 1 / 3600), "l/s": ("terfaram", 1e-3),
    "g/s": ("tomegaram", 1e-3), "kg/h": ("tomegaram", 1 / 3600), "kg/s": ("tomegaram", 1),
    "w": ("teljesitmeny", 1), "mw": ("teljesitmeny", 1e-3), "kw": ("teljesitmeny", 1e3),
    "g": ("tomeg", 1e-3), "mg": ("tomeg", 1e-6), "kg": ("tomeg", 1), "µg": ("tomeg", 1e-9),
    "g/m3": ("koncentracio", 1e-3), "mg/m3": ("koncentracio", 1e-6), "µg/m3": ("koncentracio", 1e-9),
    "%": ("arany", 1e-2), "percent": ("arany", 1e-2), "százalék": ("arany", 1e-2), "szazalek": ("arany", 1e-2),
    "ppm": ("arany", 1e-6),
}
_EGYSEG = {unicodedata.normalize("NFKC", k): v for k, v in _EGYSEG.items()}
# a nagybetűs MΩ / MOhm a megaohm (a kisbetűsítés előtt kell eldönteni)
_MEGA = {"MΩ", "MOhm", "Mohm"}
# hőmérséklet: csak az azonos skálájú alias egyezik (a °C ↔ K eltolás a különbség-mennyiségeknél értelmetlen)
_HOFOK = {"c": "°c", "°c": "°c", "celsius": "°c", "celsius fok": "°c", "fok": "°c", "k": "k"}


def egyseg(u: str) -> tuple[str, float] | None:
    u = u.strip()
    if u in _MEGA:
        return ("ellenallas", 1e6)
    n = norm(u).replace("²", "2")
    if n in _HOFOK:
        return ("hofok:" + _HOFOK[n], 1)
    return _EGYSEG.get(n)


def valt(v: float, u_be: str, u_ki: str) -> float | None:
    """Átváltás a szabály egységére; None, ha az egység ismeretlen vagy a dimenzió eltér (nincs elég információ)."""
    a, b = egyseg(u_be), egyseg(u_ki)
    if a is None or b is None or a[0] != b[0]:
        return v if norm(u_be) == norm(u_ki) else None
    return v * a[1] / b[1]


# --- a jelöltek a renderelt opciószövegből -------------------------------------------------------------------------------

def jeloltek(fam: str, options: list[dict], lang: str) -> tuple[list[dict], list[str]]:
    """(jelöltek strukturált adattal, a nem értelmezhető opciók id-i)."""
    out, rossz = [], []
    for o in options:
        j = {BANK: _bank_opcio, HIBA: _hiba_opcio, SZAB: _szab_opcio}[fam](o["text"], lang)
        if j is None:
            rossz.append(o["id"])
        else:
            out.append({"id": o["id"], **j})
    return out, rossz


def _bank_opcio(t: str, lang: str) -> dict | None:
    p = t.split(" · ")
    if len(p) != 4:
        return None
    m = re.fullmatch(r"(?:EUR ([\d,]+\.\d{2})|([\d   ]+) Ft)", p[2].strip())
    if not m:
        return None
    osszeg = szam(m.group(1), "en") if m.group(1) else szam(m.group(2), "hu")
    dev = "EUR" if m.group(1) else "HUF"
    esed = re.sub(r"^(esedékes|due)\s+", "", p[3].strip())
    return {"szamlaszam": p[0].strip(), "partner": p[1].strip(), "osszeg": osszeg, "deviza": dev, "esedekes": esed}


_HIBA_RX = {
    "hu": re.compile(r"^(?P<nev>.+?) — igazolt, ha a tünet: (?P<tunet>.+), és az? (?P<meres>.+) (?P<rel>kisebb|nagyobb), mint "
                     r"(?P<k>[-−]?\d+(?:[.,]\d+)?(?:e[-+]?\d+)?) (?P<u>.+)$"),
    "en": re.compile(r"^(?P<nev>.+?) — confirmed if the symptom is: (?P<tunet>.+), and (?P<meres>.+) is (?P<rel>below|above) "
                     r"(?P<k>[-−]?\d+(?:[.,]\d+)?(?:e[-+]?\d+)?) (?P<u>.+)$"),
}


def _hiba_opcio(t: str, lang: str) -> dict | None:
    m = _HIBA_RX[lang].match(t.strip())
    if not m:
        return None
    k = float(m.group("k").replace(",", ".").replace("−", "-"))
    rel = "<" if m.group("rel") in ("kisebb", "below") else ">"
    return {"nev": m.group("nev"), "tunet": m.group("tunet"), "meres": m.group("meres"), "relacio": rel, "kuszob": k,
            "egyseg": m.group("u").strip()}


_SZAB_RX = {
    "hu": re.compile(r"^(?P<szam>\d+\.\d+)\. (?P<tipus>.+?), (?:(?P<lo>legfeljebb) (?P<n1>nettó )?(?P<h1>[\d   ]+) Ft|"
                     r"(?P<n2>nettó )?(?P<h2>[\d   ]+) Ft (?P<hi>felett)): (?P<jov>.+) hagyja jóvá\.$"),
    "en": re.compile(r"^(?P<szam>\d+\.\d+)\. (?P<tipus>.+?) (?:(?P<lo>up to)|(?P<hi>above)) EUR (?P<h>[\d,]+)(?P<n> net of VAT)?: "
                     r"approved by (?P<jov>.+)\.$"),
}


def _szab_opcio(t: str, lang: str) -> dict | None:
    m = _SZAB_RX[lang].match(t.strip())
    if not m:
        return None
    if lang == "hu":
        h = szam(m.group("h1") or m.group("h2"), "hu")
        netto = bool(m.group("n1") or m.group("n2"))
    else:
        h = szam(m.group("h"), "en")
        netto = bool(m.group("n"))
    return {"pont": m.group("szam"), "tipus": m.group("tipus"), "sav": 0 if m.group("lo") else 1, "hatar": h,
            "deviza": "HUF" if lang == "hu" else "EUR", "alap": "netto" if netto else None, "jovahagyo": m.group("jov")}


# --- a kinyerés sémája (a G1-ben a vLLM kötött dekódolásához) -----------------------------------------------------------

SZEREPEK = {
    BANK: ("osszeg", "reszlet_arany", "hivatkozas", "partner"),
    HIBA: ("meres",),
    SZAB: ("osszeg", "afakulcs", "arfolyam"),
}


SZOVEGES = {"hivatkozas", "partner"}


# G1 (11-02): korlát nélkül a bank 06-on a válaszok 22%-a ismétlődő partnermezőkbe futott, és 1024 tokennél csonka JSON
# lett. A valódi mezők száma itemenként legfeljebb 4 szerep, illetve 3 mérés.
MAX_MEZO = 6


def kinyero_sema(fam: str, jel: list[dict]) -> dict:
    """JSON-séma: mezőnként érték, szerep, szó szerinti forrásrészlet és kapcsolat (2.2). Szerepenként külön
    objektum (anyOf), hogy a számszerű szerepek értéke szám legyen; a vLLM kötött dekódolása miatt az uniók anyOf-fal.
    Legfeljebb `MAX_MEZO` mező."""
    valt = []
    for sz in SZEREPEK[fam]:
        props: dict = {"szerep": {"const": sz}, "ertek": {"type": "string" if sz in SZOVEGES else "number"},
                       "forras": {"type": "string"}}
        req = ["szerep", "ertek", "forras"]
        if sz == "meres":
            nevek = sorted({j["meres"] for j in jel})
            props |= {"egyseg": {"type": "string"}, "kapcsolat": {"anyOf": [{"enum": nevek}, {"type": "null"}]}}
            req += ["egyseg", "kapcsolat"]
        if sz == "osszeg":
            props |= {"deviza": {"anyOf": [{"enum": ["HUF", "EUR", "GBP"]}, {"type": "null"}]}}
            if fam == SZAB:
                props |= {"alap": {"anyOf": [{"enum": ["brutto", "netto"]}, {"type": "null"}]}}
        valt.append({"type": "object", "additionalProperties": False, "properties": props, "required": req})
    return {"type": "object", "additionalProperties": False, "required": ["mezok"],
            "properties": {"mezok": {"type": "array", "items": {"anyOf": valt}, "maxItems": MAX_MEZO}}}


# Séma v2 (G1, Dani 11-02): szerepenként külön mező; a hiányzó érték explicit (null, illetve üres lista); szerepenként
# saját keret, így egy szerep ismétlése nem foglalhatja el más szerep helyét; az árfolyam pénznempárral. A v1 (egy
# közös mezőlista, `kinyero_sema`) a G1 első menetének reprodukálásához marad.
PAROK = ("HUF/EUR", "EUR/HUF", "EUR/GBP", "GBP/EUR")
KERET2 = {"osszeg": 2, "hivatkozas": 2, "partner": 2}  # a listás szerepek kerete
# Az egyértékű szerepek lapos mezők (érték: szám vagy null, mellette `<szerep>_forras`, az árfolyamnál `arfolyam_par`):
# objektum-vagy-null alakban az alany a kulcs után puszta számot írt volna, és a kötött dekódolás szóközökkel töltötte
# ki a választ (a K3 diag bankon 13 / 41 csonka JSON, 11-02).
EGYERTEKU2 = {BANK: ("reszlet_arany",), SZAB: ("afakulcs", "arfolyam")}
# A hibacsalád a v1 sémán marad: a v2 a kontrollmintán 5 / 120 visszaesést hozott, Dani pontjai (összeg, áfakulcs,
# árfolyam, részletarány) erre a családra nem vonatkoznak.
SEMA2_CSALADOK = (BANK, SZAB)


def sema_csaladra(fam: str, sema: int) -> int:
    return sema if fam in SEMA2_CSALADOK else 1


def kinyero_sema2(fam: str, jel: list[dict]) -> dict:
    if fam not in SEMA2_CSALADOK:
        return kinyero_sema(fam, jel)

    def obj(props: dict) -> dict:
        return {"type": "object", "additionalProperties": False, "properties": props, "required": list(props)}

    def vagy_null(x: dict) -> dict:
        return {"anyOf": [x, {"type": "null"}]}

    def lista(sz: str, x: dict) -> dict:
        return {"type": "array", "items": x, "maxItems": KERET2[sz]}

    num, txt = {"type": "number"}, {"type": "string"}
    if fam == BANK:
        props = {"osszeg": lista("osszeg", obj({"ertek": num, "forras": txt, "deviza": vagy_null({"enum": ["HUF", "EUR", "GBP"]})})),
                 "reszlet_arany": vagy_null(num), "reszlet_arany_forras": vagy_null(txt),
                 "hivatkozas": lista("hivatkozas", obj({"ertek": txt, "forras": txt})),
                 "partner": lista("partner", obj({"ertek": txt, "forras": txt}))}
    else:
        props = {"osszeg": lista("osszeg", obj({"ertek": num, "forras": txt,
                                                "deviza": vagy_null({"enum": ["HUF", "EUR", "GBP"]}),
                                                "alap": vagy_null({"enum": ["brutto", "netto"]})})),
                 "afakulcs": vagy_null(num), "afakulcs_forras": vagy_null(txt),
                 "arfolyam": vagy_null(num), "arfolyam_forras": vagy_null(txt), "arfolyam_par": vagy_null({"enum": list(PAROK)})}
    return obj(props)


def lapit(fam: str, obj: dict, sema: int) -> list[dict] | None:
    """A kinyerő válasza a lánc mezőlistájaként ({"szerep", …}); None, ha nem értelmezhető."""
    if sema_csaladra(fam, sema) == 1:
        m = obj.get("mezok")
        return m if isinstance(m, list) else None
    out = []
    for sz in SZEREPEK[fam]:
        x = obj.get(sz)
        if sz in EGYERTEKU2[fam]:
            if x is not None:
                out.append({"szerep": sz, "ertek": x, "forras": obj.get(f"{sz}_forras") or "",
                            **({"par": obj.get("arfolyam_par")} if sz == "arfolyam" else {})})
            continue
        for f in (x if isinstance(x, list) else []):
            if isinstance(f, dict):
                out.append({"szerep": sz, **f})
    return out


KINYERO = {
    "hu": ("Adatkinyerés. A feladatod kizárólag az, hogy a szövegben szó szerint szereplő adatokat kigyűjtsd; nem számolsz, "
           "nem következtetsz, nem döntesz. Minden mezőhöz add meg: a szerepét, az értékét, és a forrásrészletet, vagyis azt "
           "a szövegrészt szó szerint (betűre egyezően), amelyben az érték és a szerepét jelölő szó áll. Ha egy adat nem "
           "szerepel a szövegben, hagyd ki; ne találj ki értéket. Minden adatot csak egyszer adj meg. A forrásrészlet a "
           "legrövidebb ilyen szövegrész legyen. Számot számként adj meg, ezres-elválasztó és mértékegység nélkül, "
           "tizedesponttal. Tömör, egysoros JSON-nal válaszolj, a megadott sémával."),
    "en": ("Data extraction. Your only task is to collect data that appear verbatim in the text; do not compute, infer or "
           "decide. For each field give its role, its value, and the source span: the exact text (character for character) "
           "that contains the value and the word marking its role. If a datum is not in the text, omit it; never invent a "
           "value. Give each datum only once; the source span should be the shortest such text. Give numbers as numbers, "
           "without thousands separators or units, with a decimal point. Answer with compact single-line JSON in the "
           "given schema."),
}
SZEREP_LEIRAS = {
    BANK: {"hu": "osszeg: a tétel összege; reszlet_arany: ha a szöveg a fizetést egy számla százalékában adja meg, a "
                 "százalék; hivatkozas: a szövegben szereplő számlaszám vagy hivatkozási szám, ahogy le van írva (összeg, "
                 "dátum és bankszámlaszám nem az); partner: a tétel másik felének neve, ahogy le van írva (a "
                 "számlatulajdonos nem partner). deviza: csak ha a szöveg megnevezi.",
           "en": "osszeg: the transaction amount; reszlet_arany: if the text states the payment as a percentage of an invoice, "
                 "that percentage; hivatkozas: an invoice or reference number in the text, as written (not an amount, date "
                 "or bank account number); partner: the counterparty name, as written (the account holder is not the "
                 "counterparty). deviza: only if the text names it."},
    HIBA: {"hu": "meres: minden mért érték a mértékegységével (egyseg: ahogy a szövegben áll); kapcsolat: a lenti "
                 "mérésnevek közül az, amelyikre a mért érték vonatkozik, vagy null, ha egyikre sem.",
           "en": "meres: every measured value with its unit (egyseg: as written in the text); kapcsolat: the measurement "
                 "name from the list below that the value refers to, or null if none."},
    SZAB: {"hu": "osszeg: a kért összeg (deviza: a pénzneme; alap: brutto vagy netto, ha a szöveg megmondja, különben "
                 "null); afakulcs: az áfakulcs százaléka, ha szerepel; arfolyam: az átszámítási árfolyam, ha szerepel.",
           "en": "osszeg: the claimed amount (deviza: its currency; alap: brutto or netto if the text says so, otherwise "
                 "null); afakulcs: the VAT rate in percent, if stated; arfolyam: the conversion rate, if stated."},
}


SZEREP_LEIRAS2 = {
    BANK: {"hu": "osszeg: a tétel összege (lista, rendszerint egy elem; deviza: csak ha a szöveg megnevezi, különben null); "
                 "reszlet_arany: ha a szöveg a fizetést egy számla százalékában adja meg, a százalék (reszlet_arany_forras: "
                 "a forrásrészlete), különben mindkettő null. A százalék nem összeg: a „40%-a” részlet-arány. hivatkozas: a "
                 "szövegben szereplő számlaszámok vagy hivatkozási számok, ahogy le vannak írva (összeg, dátum és "
                 "bankszámlaszám nem az); partner: a tétel másik felének neve, ahogy le van írva (a számlatulajdonos nem "
                 "partner).",
           "en": "osszeg: the transaction amount (a list, usually one element; deviza: only if the text names it, otherwise "
                 "null); reszlet_arany: if the text states the payment as a percentage of an invoice, that percentage "
                 "(reszlet_arany_forras: its source span), otherwise both null. A percentage is not an amount: \"40% of\" is "
                 "a part-payment ratio. hivatkozas: invoice or reference numbers in the text, as written (not an amount, date "
                 "or bank account number); partner: the counterparty name, as written (the account holder is not the "
                 "counterparty)."},
    SZAB: {"hu": "osszeg: a kért összeg (lista, legfeljebb két elem, például ha a szöveg nettó és bruttó összeget is ad), "
                 "mindegyik a pénznemével (deviza) és az alapjával (alap: brutto vagy netto, ha a szöveg megmondja, "
                 "különben null); afakulcs: az áfakulcs százaléka (afakulcs_forras: a forrásrészlete), különben null; "
                 "arfolyam: az átszámítási árfolyam (arfolyam_forras: a forrásrészlete; arfolyam_par: a pénznempár a szöveg "
                 "jelölése szerint, számláló/nevező), különben null. Az árfolyam nem összeg: a „405 Ft/EUR” árfolyam "
                 "(arfolyam 405, arfolyam_par HUF/EUR, vagyis hány forint egy euró).",
           "en": "osszeg: the claimed amount (a list of at most two elements, e.g. if the text gives both a net and a gross "
                 "amount), each with its currency (deviza) and basis (alap: brutto or netto if the text says so, otherwise "
                 "null); afakulcs: the VAT rate in percent (afakulcs_forras: its source span), otherwise null; arfolyam: the "
                 "conversion rate (arfolyam_forras: its source span; arfolyam_par: the currency pair as written in the text, "
                 "numerator/denominator), otherwise null. A rate is not an amount: \"1.19 EUR/GBP\" is the rate (arfolyam "
                 "1.19, arfolyam_par EUR/GBP, i.e. euros per pound)."},
}
HIANY2 = {"hu": " Ami nem szerepel a szövegben, az null, illetve üres lista. Ugyanazt az adatot ne ismételd.",
          "en": " Anything not in the text is null or an empty list. Do not repeat the same datum."}


def kinyero_prompt(fam: str, it: dict, jel: list[dict], sema: int = 1) -> list[dict]:
    """A kinyerés üzenetei (G1). A jelöltek nem látszanak, hogy a kinyerés ne előlegezze meg a döntést; a
    hibacsaládon a szabályok mérésnevei a kapcsolathoz kellenek. `sema` 1: a G1 első menete, 2: szerepenkénti mezők."""
    lang = it["lang"]
    leiras = SZEREP_LEIRAS[fam][lang] if sema_csaladra(fam, sema) == 1 else SZEREP_LEIRAS2[fam][lang] + HIANY2[lang]
    user = f"{leiras}\n\n"
    if fam == HIBA:
        nevek = sorted({j["meres"] for j in jel})
        user += ("Mérésnevek:\n" if lang == "hu" else "Measurement names:\n") + "\n".join(f"- {n}" for n in nevek) + "\n\n"
    user += ("Szöveg:\n" if lang == "hu" else "Text:\n") + it["state"]
    return [{"role": "system", "content": KINYERO[lang]}, {"role": "user", "content": user}]


# --- ellenőrzés ----------------------------------------------------------------------------------------------------------

CUE = {  # szerepjelölő szavak; az értékhez legközelebbi jelölőnek a saját szerepéhez kell tartoznia
    "reszlet_arany": {"hu": ["részlet", "%-a", "%-á", "%-os", "százalék", "előleg", "rész"],
                      "en": ["instalment", "installment", "% of", "part payment", "partial", "deposit", "portion"]},
    "afakulcs": {"hu": ["áfa", "áfá", "általános forgalmi adó"], "en": ["vat", "value added tax"]},
    "arfolyam": {"hu": ["árfolyam", "ft/eur", "huf/eur", "forint/euró"], "en": ["rate", "eur/gbp", "exchange"]},
}
VERSENGO = {"reszlet_arany": ("reszlet_arany", "afakulcs"), "afakulcs": ("reszlet_arany", "afakulcs"),
            "arfolyam": ("arfolyam",)}
AFA = {"hu": {5, 18, 27}, "en": {0, 5, 20}}
ARFOLYAM_SAV = {"hu": (250, 600), "en": (0.8, 2.0)}  # Ft/EUR, illetve EUR/GBP
ALAP_CUE = {"brutto": {"hu": ["bruttó", "áfával", "áfát tartalmaz", "áfás"], "en": ["gross", "including", "incl"]},
            "netto": {"hu": ["nettó", "áfa nélkül"], "en": ["net", "excluding", "excl"]}}
DEVIZA_CUE = {"HUF": ["ft", "huf", "forint"], "EUR": ["eur", "euró", "euro", "€"], "GBP": ["gbp", "£", "pound"]}
DEVIZA_LEX = {d: {"hu": c, "en": c} for d, c in DEVIZA_CUE.items()}
ABLAK = 60
PAR_SAV = {"HUF/EUR": (250, 600), "EUR/HUF": (1 / 600, 1 / 250), "EUR/GBP": (0.8, 2.0), "GBP/EUR": (0.5, 1.25)}
_PENZNEM = {"ft": "HUF", "huf": "HUF", "forint": "HUF", "eur": "EUR", "euró": "EUR", "euro": "EUR", "€": "EUR",
            "gbp": "GBP", "£": "GBP", "font": "GBP", "pound": "GBP"}
_PN = r"(ft|huf|forint|eur|euró|euro|€|gbp|£|font|pound)"
_PAR_RX = (re.compile(_PN + r"\s*/\s*" + _PN, re.I),                                  # 405 Ft/EUR
           re.compile(r"1\s*" + _PN + r"\s*=\s*[\d.,\s]+?\s*" + _PN, re.I))           # 1 EUR = 405 Ft


def _par_a_szovegben(text: str, pa: int, pb: int) -> str | None:
    """Az árfolyam értékéhez legközelebbi pénznempár-jelölés az ablakban, számláló/nevező alakban."""
    a0 = max(0, pa - ABLAK)
    w = text[a0:pb + ABLAK]
    best = None
    for k, rx in enumerate(_PAR_RX):
        for m in rx.finditer(w):
            x, y = _PENZNEM[m.group(1).lower()], _PENZNEM[m.group(2).lower()]
            par = f"{x}/{y}" if k == 0 else f"{y}/{x}"  # „1 EUR = 405 Ft” → HUF/EUR
            s_, e_ = a0 + m.start(), a0 + m.end()
            d = 0 if s_ <= pa and pb <= e_ else min(abs(s_ - pb), abs(pa - e_))
            if best is None or d < best[0]:
                best = (d, par)
    return best[1] if best else None
# a „Részletek:” és a „Tétel részletei:” fejléc (adatok) nem részfizetés-jel (11-03: a 06 bankon 46 tételen ez
# akadályozta az összeg-ellenőrzést)
RESZFIZETES_JEL = {"hu": re.compile(r"részlet(?!ek\b|ei\b)|részfizet|előleg|százalék|\d\s*%", re.I),
                   "en": re.compile(r"instal+ment|partial|part[- ]payment|deposit|percent|\d\s*%", re.I)}


_PENZNEM_SZO = re.compile(r"(?<![^\W\d_])(?:ft|huf|forint|eur|euró|euro|gbp|font|pound)(?![^\W\d_])|€|£", re.I)


def penznem(text: str, a: int, b: int, ablak: int = ABLAK) -> str | None:
    """Az [a, b) helyen álló érték pénzneme: a legközelebbi önálló pénznemjelölő az ablakban (szóhatárral, hogy a
    „Kft.” vagy a „software” „ft”-je ne számítson); ha nincs, None."""
    best = None
    for m in _PENZNEM_SZO.finditer(text, max(0, a - ablak), min(len(text), b + ablak)):
        d = 0 if m.start() < b and m.end() > a else min(abs(m.start() - b), abs(m.end() - a))
        if best is None or d < best[0]:
            best = (d, _PENZNEM[m.group(0).lower()])
    return best[1] if best else None


def _legkozelebbi(text: str, a: int, b: int, lex: dict[str, dict[str, list[str]]], lang: str, ablak: int) -> str | None:
    low = text.lower()
    best = None
    for szerep, cues in lex.items():
        for c in cues[lang]:
            for m in re.finditer(re.escape(c), low[max(0, a - ablak):b + ablak]):
                s = max(0, a - ablak) + m.start()
                d = 0 if s < b and s + len(c) > a else min(abs(s - b), abs(s + len(c) - a))
                if best is None or d < best[0]:
                    best = (d, szerep)
    return best[1] if best else None


def ellenoriz(fam: str, text: str, lang: str, mezok: list[dict], jel: list[dict]) -> tuple[list[dict], list[dict]]:
    """(az ellenőrzésen átment mezők a szöveg-pozícióval, a bukott mezők az okkal)."""
    jo, rossz, foglalt = [], [], set()
    rule_u = {norm(j["meres"]): j["egyseg"] for j in jel} if fam == HIBA else {}
    for f in mezok:
        def bukik(ok: str) -> None:
            rossz.append({**f, "ok": ok})
        sz, src = str(f.get("szerep")), str(f.get("forras") or "")
        if sz not in SZEREPEK[fam]:
            bukik("ismeretlen szerep")
            continue
        hely = helye(text, src)
        if hely is None:
            bukik("a forrásrészlet nincs a szövegben")
            continue
        a0, b0 = hely
        if sz in ("hivatkozas", "partner"):
            v = str(f.get("ertek") or "").strip()
            i = text.lower().find(v.lower(), a0, b0 + 1) if v else -1
            if i < 0:
                bukik("az érték nincs a forrásrészletben")
                continue
            jo.append({**f, "_pos": (i, i + len(v)), "_v": text[i:i + len(v)], "_span": (a0, b0)})
            continue
        v = _ertek(f.get("ertek"), lang)
        if v is None:
            bukik("nem szám")
            continue
        if sz == "meres":
            k = f.get("kapcsolat")
            u = str(f.get("egyseg") or "").strip()
            if k is not None:
                ru = rule_u.get(norm(k))
                if ru is None:
                    bukik("a kapcsolt mérés nincs a szabályok közt")
                    continue
                a_, b_ = egyseg(u), egyseg(ru)
                if a_ and b_ and a_[0] != b_[0]:
                    bukik("az egység dimenziója nem illik a kapcsolt méréshez")
                    continue
        # az érték minden előfordulása a forrásrészletben; az első, amely minden feltételnek megfelel. A számok a teljes
        # szövegből, és csak a részleten belül teljesen elférők számítanak (G1, 11-02: a „+1 169 690 Ft”-ból kivágott
        # „169 690 Ft” részlet hamis összeget igazolt, és kizárta a goldot)
        hely_ok = None
        elso_hiba = "az érték nincs a forrásrészletben"
        for pa, pb, x in szamok(text, lang):
            if pa < a0 or pb > b0:
                continue
            if not (egyezik(x, v) or (sz == "osszeg" and egyezik(abs(x), abs(v)))):  # banki terhelés: „-2151330”
                continue
            h = _szerep_hiba(sz, f, v, text, lang, pa, pb, a0, b0, foglalt)
            if h is None:
                hely_ok = (pa, pb)
                break
            if elso_hiba == "az érték nincs a forrásrészletben":
                elso_hiba = h
        if hely_ok is None:
            bukik(elso_hiba)
            continue
        foglalt.add(hely_ok)
        f2 = dict(f)
        pa, pb = hely_ok
        if sz == "osszeg" and f2.get("deviza") and _legkozelebbi(text, pa, pb, DEVIZA_LEX, lang, ABLAK) is None:
            f2["deviza"] = None  # nem igazolható, de nem is ellentmond: az attribútum vetődik el, a mező marad
        if sz == "osszeg" and f2.get("alap") and _legkozelebbi(text, pa, pb, ALAP_CUE, lang, ABLAK) is None:
            f2["alap"] = None
        if sz == "arfolyam" and f2.get("par") and _par_a_szovegben(text, pa, pb) is None:
            f2["par"] = None
        jo.append({**f2, "_pos": hely_ok, "_v": v, "_span": (a0, b0)})
    return jo, rossz


def _ertek(x, lang: str) -> float | None:
    """A számszerű érték; szövegnél (\"7,2 mm/s\", \"1 013 750\") az első szám a nyelv formátumával."""
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    sz_ = szamok(str(x), lang)
    return sz_[0][2] if sz_ else None


def _szerep_hiba(sz: str, f: dict, v: float, text: str, lang: str, pa: int, pb: int, a0: int, b0: int,
                 foglalt: set) -> str | None:
    """Egy számelőfordulás megfelel-e a szerepnek; None = igen, különben a bukás oka."""
    if (pa, pb) in foglalt:
        return "a szám már egy másik szerepet tölt be"
    if sz in VERSENGO:
        if _legkozelebbi(text, pa, pb, {k: CUE[k] for k in VERSENGO[sz]}, lang, ABLAK) != sz:
            return "nincs a szerepet jelölő szó az érték mellett"
        if sz == "reszlet_arany" and not (1 <= v <= 99 and re.match(r"\s*(%|százalék|percent)", text[pb:pb + 12], re.I)):
            return "a részlet-arány nem 1–99%"
        if sz == "afakulcs" and v not in AFA[lang]:
            return "az áfakulcs nem az ország kulcsa"
        pz = _par_a_szovegben(text, pa, pb) if sz == "arfolyam" and f.get("par") else None
        if pz is not None:  # a megadott pár a szöveg jelölésével; jelölés nélkül a pár elvetődik, és a régi szabály
            if pz != f["par"]:
                return "a pénznempár ellentmond a szöveg jelölésének"
            if f["par"] not in PAR_SAV or not (PAR_SAV[f["par"]][0] <= v <= PAR_SAV[f["par"]][1]):
                return "az árfolyam a pénznempár sávján kívül"
        elif sz == "arfolyam" and not (ARFOLYAM_SAV[lang][0] <= v <= ARFOLYAM_SAV[lang][1]):
            return "az árfolyam a sávon kívül"
    if sz == "osszeg":
        # G1 (11-02): a százalék és az árfolyam nem összeg („40%-a”, „405 Ft/EUR”; a K3 diag-on a kinyerő összegnek adta)
        if re.match(r"\s*(%|százalék|percent)", text[pb:pb + 12], re.I):
            return "az érték százalék, nem összeg"
        if re.match(r"\s*" + _PN + r"\s*/\s*" + _PN, text[pb:pb + 24], re.I):
            return "az érték árfolyam, nem összeg"
        # a megadott deviza és alap: ha az érték körüli ablak legközelebbi jelölője más, a mező bukik (ellentmondás); ha
        # nincs jelölő, csak az attribútum vetődik el (`ellenoriz`; G1, 11-02: a „végösszeg” mellett nincs alapjelölő)
        dev = f.get("deviza")
        nd = _legkozelebbi(text, pa, pb, DEVIZA_LEX, lang, ABLAK) if dev else None
        if dev and nd is not None and nd != dev:
            return "a deviza ellentmond az összeg melletti jelölőnek"
        al = f.get("alap")
        na = _legkozelebbi(text, pa, pb, ALAP_CUE, lang, ABLAK) if al else None
        if al and na is not None and na != al:
            return "az alap (bruttó / nettó) ellentmond a jelölőnek"
    if sz == "meres":
        u = str(f.get("egyseg") or "").strip()
        if not u or not re.match(r"\s*" + re.escape(u) + r"(?![\w/])", text[pb:pb + len(u) + 4], re.I):
            return "az egység nem az érték után áll"
    return None


# --- számítás és szabályellenőrzés ---------------------------------------------------------------------------------------

def _egy(mezok: list[dict], sz: str) -> list[dict]:
    return [f for f in mezok if f["szerep"] == sz]


def lanc(fam: str, it: dict, mezok: list[dict] | None, ures: str = "modell", valtozat: str = "v0") -> dict:
    """A lánc egy itemen. `mezok`: a kinyert mezők (None = a kinyerés nem adott választ → emberhez). `valtozat` a
    szabálycsalád blokkjának változata (G1-próba, `BLOKK_VALTOZAT`); a v0 az eredeti."""
    lang, text = it["lang"], it["state"]
    jel, rossz_opc = jeloltek(fam, it["options"], lang)
    res = {"id": it["id"], "kimenet": None, "megmaradt": [], "kizart": {}, "kotes": None, "szamitott": {},
           "blokk": "", "bukott": [], "nem_ertelmezheto_opcio": rossz_opc}
    if mezok is None:
        res["kimenet"] = "emberhez"
        res["bukott"] = [{"ok": "nincs kinyerés"}]
        return res
    jo, rossz = ellenoriz(fam, text, lang, mezok, jel)
    # a bukott mező elvetődik (G1-próba, 11-02): az elvetés csak információvesztés, kizárásra vagy kötésre nem vezet;
    # emberhez az ellentmondásos kinyerés megy (ugyanabban a szerepben két eltérő ellenőrzött érték; 2.1)
    res["elvetett"] = [{k: v for k, v in f.items() if not k.startswith("_")} for f in rossz]
    if fam == BANK:  # a számlatulajdonos nem partner
        tul = re.match(r"(?:Számlatulajdonos|Account holder): (.+)", text)
        if tul:
            jo = [f for f in jo if not (f["szerep"] == "partner" and _partner_egyezik(str(f["_v"]), tul.group(1)))]
    for sz in ("osszeg", "reszlet_arany", "afakulcs", "arfolyam"):
        ert = {round(abs(f["_v"]) if sz == "osszeg" else f["_v"], 6) for f in _egy(jo, sz)}
        if len(ert) > 1:
            res["kimenet"] = "emberhez"
            res["bukott"] = [{"ok": f"ellentmondás: több {sz}"}]
            return res
        if len(ert) == 1:  # azonos érték többször: egy marad
            jo = [f for f in jo if f["szerep"] != sz] + _egy(jo, sz)[:1]
    mer_ = defaultdict(set)
    for f in _egy(jo, "meres"):
        if f.get("kapcsolat"):
            mer_[norm(f["kapcsolat"])].add((round(f["_v"], 9), norm(str(f.get("egyseg")))))
    if any(len(v) > 1 for v in mer_.values()):
        res["kimenet"] = "emberhez"
        res["bukott"] = [{"ok": "ellentmondás: egy méréshez több érték"}]
        return res
    allit: dict[str, tuple[str, str | None]] = {j["id"]: ("lehetseges", None) for j in jel}
    blokk = []
    hu = lang == "hu"
    if fam == BANK:
        osz, rv = _egy(jo, "osszeg"), _egy(jo, "reszlet_arany")
        dev, teljes, tol, merheto = None, None, None, False
        if osz:
            a = abs(osz[0]["_v"])
            # a tétel pénzneme a szövegből (Dani 11-03: hiányzó adatból nem következik kizárás, hallgatólagos alapérték
            # nincs): a megadott és igazolt deviza, vagy az érték melletti önálló pénznemjelölő; ha egyik sincs, az összeg
            # nem zár ki és nem köt (a 11-03 előtti kód a nyelvből vette: hu → HUF, en → EUR)
            dev = osz[0].get("deviza") or penznem(text, *osz[0]["_pos"])
            unit = 1.0 if dev == "HUF" else 0.01
            r = rv[0]["_v"] if rv else None
            teljes = a * 100 / r if r else a
            tol = unit * (1 + (50 / r if r else 0))
            res["szamitott"] = {"osszeg": a, "deviza": dev, "reszlet_arany": r, "teljes": teljes, "tol": tol}
            pz = (lambda x: penz(x, lang, dev)) if dev else \
                (lambda x: f"{fmt(x, lang)} (a pénznem nem ellenőrizhető)" if hu else f"{fmt(x, lang)} (currency not verified)")
            blokk.append(f"a tétel összege: {pz(a)}" if hu else f"transaction amount: {pz(a)}")
            if r:
                blokk.append(f"részlet-arány: {fmt(r, lang)}%; a számla teljes bruttó összege ennek alapján: {pz(teljes)}"
                             if hu else f"instalment ratio: {fmt(r, lang)}%; the full gross invoice amount on this basis: "
                                        f"{pz(teljes)}")
            # a teljes fizetés feltevés: ha a szöveg részfizetésre utal, de nincs ellenőrzött arány, az összeg nem bizonyít
            # ellentmondást (nincs elég információ; 2.1)
            merheto = dev is not None and bool(r or not RESZFIZETES_JEL[lang].search(text))
            if merheto:
                for j in jel:
                    if j["deviza"] == dev and abs(j["osszeg"] - teljes) > tol:
                        allit[j["id"]] = ("kizart", "az összeg ellentmond")
            elif dev is None:
                res["szamitott"]["penznem_ismeretlen"] = True
            else:
                res["szamitott"]["reszfizetes_jel_arany_nelkul"] = True
        refs = {norm_ref(str(f["_v"])) for f in _egy(jo, "hivatkozas")}  # a hivatkozás a szövegben áll, a blokkba nem kerül
        talalt = [j for j in jel if norm_ref(j["szamlaszam"]) in refs]
        # kötés csak ténylegesen elvégzett összegegyezéssel (2.1): ugyanaz a pénznem, a számított összeg a tűrésen belül
        if (len(talalt) == 1 and merheto and allit[talalt[0]["id"]][0] != "kizart" and talalt[0]["deviza"] == dev
                and abs(talalt[0]["osszeg"] - teljes) <= tol):
            j = talalt[0]
            pnev = [norm(str(f["_v"])) for f in _egy(jo, "partner")]
            mas = [x for x in jel if x["partner"] != j["partner"] and _partner_a_szovegben(x["partner"], text)]
            if all(_partner_egyezik(p, j["partner"]) for p in pnev) and not mas:
                allit[j["id"]] = ("kotheto", "hivatkozás + összeg + partner")
    elif fam == HIBA:
        mer = {norm(f["kapcsolat"]): f for f in _egy(jo, "meres") if f.get("kapcsolat")}
        szam_ = {}
        for j in jel:
            f = mer.get(norm(j["meres"]))
            if f is None:
                continue
            v = valt(f["_v"], f["egyseg"], j["egyseg"])
            if v is None:
                continue
            szam_[j["meres"]] = (v, j["egyseg"], f["_v"], f["egyseg"])
            ok = v < j["kuszob"] if j["relacio"] == "<" else v > j["kuszob"]
            if not ok and not egyezik(v, j["kuszob"], 1e-6 * max(1, abs(j["kuszob"]))):
                allit[j["id"]] = ("kizart", "a mérés kívül esik a szabályon")
        res["szamitott"] = {k: v[0] for k, v in szam_.items()}
        for k, (v, u, v0, u0) in szam_.items():
            if norm(u) != norm(u0):
                blokk.append(f"{k}: {fmt_g(v0, lang)} {u0} = {fmt_g(_kerek(v), lang)} {u}")
    else:
        osz, afa, arf = _egy(jo, "osszeg"), _egy(jo, "afakulcs"), _egy(jo, "arfolyam")
        cel = "HUF" if hu else "EUR"
        if osz:
            f = osz[0]
            a = abs(f["_v"])
            # ha a kinyerő nem adja meg, a deviza és az alap ugyanazzal a szabállyal, amellyel a megadott értéket az
            # ellenőrzés igazolja (a legközelebbi jelölő az érték körüli ablakban; G1, 11-02: a rövid forrásrészletből a
            # K3 diag S3a-n 34 itemnél kimaradt a „27% áfával”); ismeretlen devizánál nincs kizárás (bizonytalan
            # átváltásból nem következik kizárás; 2.1)
            pa_, pb_ = f["_pos"]
            dev = f.get("deviza") or _legkozelebbi(text, pa_, pb_, DEVIZA_LEX, lang, ABLAK)
            al = f.get("alap") or _legkozelebbi(text, pa_, pb_, ALAP_CUE, lang, ABLAK)
            atsz = None
            if dev is not None and dev != cel:
                par = arf[0].get("par") if arf else None
                r_ = float(arf[0]["_v"]) if arf else 0.0
                if arf and par in (None, f"{cel}/{dev}"):  # pár nélkül (v1, orákulum): a sáv a cél/deviza irányé
                    atsz = a * r_
                    blokk.append(f"átszámítva: {penz(atsz, lang, cel)} ({fmt(a, lang)} {dev} × {fmt(r_, lang)} "
                                 f"{'Ft' if hu else 'EUR'}/{dev})" if hu else
                                 f"converted: {penz(atsz, lang, cel)} ({dev} {fmt(a, lang)} × {fmt(r_, lang)} EUR/{dev})")
                elif arf and par == f"{dev}/{cel}":
                    atsz = a / r_
                    blokk.append(f"átszámítva: {penz(atsz, lang, cel)} ({fmt(a, lang)} {dev} ÷ {fmt(r_, lang)} {dev}/"
                                 f"{'Ft' if hu else 'EUR'})" if hu else
                                 f"converted: {penz(atsz, lang, cel)} ({dev} {fmt(a, lang)} ÷ {fmt(r_, lang)} {dev}/EUR)")
            elif dev == cel:
                atsz = a
            netto = None
            if atsz is not None and al == "brutto" and afa:
                k = afa[0]["_v"]
                netto = atsz / (1 + k / 100)
                blokk.append(f"a nettó összeg: {penz(netto, lang, cel)} ({penz(atsz, lang, cel)} bruttó, {fmt(k, lang)}% áfa)" if hu else
                             f"net amount: {penz(netto, lang, cel)} ({penz(atsz, lang, cel)} gross, {fmt(k, lang)}% VAT)")
            elif atsz is not None and al == "netto":
                netto = atsz
            res["szamitott"] = {"atszamitva": atsz, "netto": netto, "alap": al}
            mert = {}
            for j in jel:
                x = netto if j["alap"] == "netto" else (atsz if al != "netto" or j["alap"] is None else None)
                if j["alap"] == "netto" and netto is None:
                    continue  # a nettó szabályhoz nincs ellenőrzött nettó: nincs elég információ
                if x is None or abs(x - j["hatar"]) <= 1:
                    continue
                mert[j["id"]] = x
                if (j["sav"] == 0 and x > j["hatar"]) or (j["sav"] == 1 and x <= j["hatar"]):
                    allit[j["id"]] = ("kizart", "az összeg a küszöb másik oldalán")
            if valtozat != "v0":
                blokk += _blokk_valtozat(valtozat, jel, allit, mert, lang)
    res["allitasok"] = {k: v[0] for k, v in allit.items()}
    res["kizart"] = {k: v[1] for k, v in allit.items() if v[0] == "kizart"}
    res["megmaradt"] = [j["id"] for j in jel if allit[j["id"]][0] != "kizart"] + rossz_opc
    kot = [k for k, v in allit.items() if v[0] == "kotheto"]
    if blokk:
        res["blokk"] = ("Ellenőrzött adatok (a rendszer számította):\n" if hu else "Verified data (computed by the system):\n") + \
            "\n".join(f"- {b}" for b in blokk)
    if kot:
        res["kimenet"], res["kotes"] = "kotes", kot[0]
    elif not res["megmaradt"]:
        res["kimenet"] = ures
    else:
        res["kimenet"] = "modell"
    return res


# G1-próba (11-02, Dani: „érthető-e a modell számára a számítási blokk és a megmaradt szabálypontok jelentése”): a K3 diag
# szabálycsaládon orákulum-úton 34 MATCH → X, mind angol nyelvű. A v0 az eredeti blokk; a változatok csak hozzáírnak.
#   v1  kimondja, melyik kiszámított értéket kell a szabálypontok összeghatárához mérni
#   v2  a megmaradt (nem kizárt) szabálypontonként: az összegfeltétel teljesül, a mért értékkel; vagy nem ellenőrizhető
# Célzott próba (Dani 11-02 23:00 után: a v1 a T500-on nettó +9 NO_MATCH → SELECT; „az összegfeltétel teljesül” könnyen
# „a jelölt helyes” jelentést kap). A blokk válassza szét a kiszámított értéket, a teljesülő részfeltételt és azt, amiről
# a rendszer nem döntött. Csak ott írnak, ahol a v1 is (van mért érték megmaradt szabályponthoz):
#   v3  összesítve: a v1 sora; az összeghatár alapján nem kizárt pontok; a költségnemet a rendszer nem ellenőrizte
#   v4  pontonként: összeghatár teljesül / nem ellenőrizhető; a költségnem nincs ellenőrizve
BLOKK_VALTOZAT = ("v0", "v1", "v2", "v3", "v4")


def _blokk_valtozat(v: str, jel: list[dict], allit: dict, mert: dict, lang: str) -> list[str]:
    hu = lang == "hu"
    dev = "HUF" if hu else "EUR"
    megm = [j for j in jel if allit[j["id"]][0] != "kizart"]
    if v in ("v3", "v4"):
        out = _blokk_valtozat("v1", jel, allit, mert, lang)
        if not out:
            return out
        if v == "v3":
            ok = [f"{j['pont']}." for j in megm if j["id"] in mert]
            nem = [f"{j['pont']}." for j in megm if j["id"] not in mert]
            if ok:
                out.append(f"az összeghatár alapján nem kizárt: {', '.join(ok)} pont" if hu else
                           f"not excluded by the amount limit: clause {', '.join(ok)}")
            if nem:
                out.append(f"az összeghatár nem ellenőrizhető: {', '.join(nem)} pont" if hu else
                           f"amount limit cannot be verified: clause {', '.join(nem)}")
            out.append("a rendszer nem ellenőrizte a tétel költségnemét (hogy melyik pont tárgyához tartozik, ha "
                       "bármelyikhez); az összeghatár egyezése önmagában nem jelenti, hogy a pont illik a tételre" if hu else
                       "the system did not check the expense category of the item (which clause's subject it belongs to, "
                       "if any); a matching amount limit alone does not mean that the clause fits the item")
            return out
        for j in megm:
            hat = penz(j["hatar"], lang, dev)
            felt = (f"{'legfeljebb' if j['sav'] == 0 else 'több mint'} {'nettó ' if j['alap'] == 'netto' else ''}{hat}" if hu
                    else f"{'up to' if j['sav'] == 0 else 'above'} {hat}{' net' if j['alap'] == 'netto' else ''}")
            if hu:
                out.append(f"{j['pont']}. pont: összeghatár ({felt}): {'teljesül' if j['id'] in mert else 'nem ellenőrizhető'}; "
                           f"a költségnem („{j['tipus'].lower()}”): nincs ellenőrizve")
            else:
                out.append(f"clause {j['pont']}: amount limit ({felt}): {'met' if j['id'] in mert else 'cannot be verified'}; "
                           f"expense category (\"{j['tipus'].lower()}\"): not checked")
        return out
    if v == "v1":
        ert = sorted({(j["alap"] == "netto", mert[j["id"]]) for j in megm if j["id"] in mert})
        out = []
        for netto, x in ert:
            if hu:
                out.append(f"a szabályzat {'nettó ' if netto else ''}összeghatárait ehhez az értékhez kell mérni: {penz(x, lang, dev)}")
            else:
                out.append(f"compare the policy's {'net ' if netto else ''}amount limits with this value: {penz(x, lang, dev)}")
        return out
    out = []
    for j in megm:
        hat = penz(j["hatar"], lang, dev)
        felt = (f"{'legfeljebb' if j['sav'] == 0 else 'több mint'} {'nettó ' if j['alap'] == 'netto' else ''}{hat}" if hu else
                f"{'up to' if j['sav'] == 0 else 'above'} {hat}{' net' if j['alap'] == 'netto' else ''}")
        if j["id"] in mert:
            out.append(f"{j['pont']}. pont: az összegfeltétel ({felt}) teljesül: {penz(mert[j['id']], lang, dev)}" if hu else
                       f"clause {j['pont']}: the amount condition ({felt}) is met: {penz(mert[j['id']], lang, dev)}")
        else:
            out.append(f"{j['pont']}. pont: az összegfeltétel ({felt}) nem ellenőrizhető" if hu else
                       f"clause {j['pont']}: the amount condition ({felt}) cannot be verified")
    return out


def _kozeli(text: str, f: dict, lex: dict, lang: str) -> str | None:
    """A mező értékéhez legközelebbi jelölő a forrásrészleten belül."""
    a0, b0 = f["_span"]
    pa, pb = f["_pos"]
    return _legkozelebbi(text[a0:b0], pa - a0, pb - a0, lex, lang, b0 - a0)


def _kerek(v: float) -> float:
    if v == 0:
        return 0.0
    return round(v, 2 - int(math.floor(math.log10(abs(v)))))


def _partner_a_szovegben(p: str, text: str) -> bool:
    elso = p.split()[0]
    return bool(re.search(rf"(?<!\w){re.escape(elso)}(?!\w)", text, re.I))


def _partner_egyezik(a: str, b: str) -> bool:
    x, y = norm(a), norm(b)
    return x == y or x.split()[0] == y.split()[0]


# A szintetikus bank feladatszabálya (Dani 11-03): minden szintetikus banki tanító- és értékelési bemenet kérdése után
# ugyanez a mondat (a lánc teljes fizetést feltételez, ha nincs részfizetés-jel, és ezt az alany is megkapja). A valódi
# 08B-re nem vonatkozik: ott a jel hiányából nem következik teljes fizetés.
BANK_FELADATSZABALY = {
    "hu": "Ebben a feladatban a részfizetést a leírás mindig jelzi; ilyen jelzés hiányában teljes kiegyenlítést feltételezz.",
    "en": "In this task, the description always indicates a partial payment; if there is no such indication, assume full "
          "settlement.",
}


def bank_kerdes(it: dict) -> str:
    """A kérdés a bank feladatszabályával (a szintetikus bankon; idempotens, a G2 generátora is ezt hívja)."""
    q = it["question"]
    if it["family"] != BANK or BANK_FELADATSZABALY[it["lang"]] in q:
        return q
    return f"{q.rstrip()} {BANK_FELADATSZABALY[it['lang']]}"


def uj_item(it: dict, res: dict) -> dict:
    """Az item a modellhez: a megmaradt jelöltek, a szöveg végén az ellenőrzött adatok blokkja, a bankon a kérdés után
    a feladatszabály."""
    keep = set(res["megmaradt"])
    opts = [o for o in it["options"] if o["id"] in keep]
    gold = it["gold"] if it["gold"] in keep else None
    state = it["state"].rstrip() + ("\n\n" + res["blokk"] if res["blokk"] else "")
    return {**it, "question": bank_kerdes(it), "state": state, "options": opts, "gold": gold,
            "meta": {**(it.get("meta") or {}), "lanc": {"kimenet": res["kimenet"], "kizart": res["kizart"]}}}


# --- az orákulum: ugyanaz a lánc a terv tényeiből vett mezőkkel (3.4) ----------------------------------------------------

def _mondat(text: str, a: int, b: int) -> str:
    """Az érték körüli szövegrész: a sor, vagy a soron belül a mondat, illetve a CSV-mező."""
    s = text.rfind("\n", 0, a) + 1
    e = text.find("\n", b)
    e = len(text) if e < 0 else e
    sor = text[s:e]
    if ";" in sor and sor.count(";") >= 3:
        return sor.strip()
    for m in re.finditer(r"[^.!?]+(?:[.!?](?!\d)|$)", sor):
        if s + m.start() <= a and b <= s + m.end():
            return m.group(0).strip()
    return sor.strip()


def _keres_szam(text: str, lang: str, v: float, utana: str | None = None, foglalt: set | None = None,
                abszolut: bool = False) -> tuple[int, int] | None:
    for a, b, x in szamok(text, lang):
        if foglalt is not None and (a, b) in foglalt:
            continue
        if (egyezik(abs(x), abs(v)) if abszolut else egyezik(x, v)) and (utana is None or re.match(r"\s*" + re.escape(utana) + r"(?![\w/])", text[b:b + len(utana) + 4], re.I)):
            if foglalt is not None:
                foglalt.add((a, b))
            return a, b
    return None


def _deviza_mellett(text: str, lang: str, v: float, dev: str, fog: set) -> tuple[int, int] | None:
    """Az érték előfordulásai közül a devizajelölőhöz legközelebbi (a dátumban álló azonos szám helyett)."""
    jel = [(a, b) for a, b, x in szamok(text, lang) if egyezik(abs(x), v) and (a, b) not in fog]
    if not jel:
        return None
    low = text.lower()

    def tav(ab):
        d = [abs(m.start() - ab[1]) if m.start() >= ab[1] else abs(ab[0] - m.end())
             for c in DEVIZA_CUE[dev] for m in re.finditer(re.escape(c), low)]
        return min(d) if d else 10**9
    best = min(jel, key=tav)
    fog.add(best)
    return best


def _bekezdes(text: str, a: int, b: int) -> str:
    s = text.rfind("\n\n", 0, a)
    e = text.find("\n\n", b)
    return text[0 if s < 0 else s + 2:len(text) if e < 0 else e].strip()


def orakulum(fam: str, p: dict, it: dict) -> list[dict]:
    """A terv tényei mezőként, csak ha a szövegben ténylegesen szerepelnek (a forrásrészlet az érték mondata)."""
    t, lang, text = p["tenyek"], p["lang"], it["state"]
    out, fog = [], set()

    def add(szerep, ertek, pos, **kw):
        if pos is not None:
            out.append({"szerep": szerep, "ertek": ertek, "forras": _mondat(text, *pos), **kw})

    if fam == BANK:
        if "osszeg" in t:
            v = t["osszeg"] if lang == "hu" else t["osszeg"] / 100
            add("osszeg", v, _keres_szam(text, lang, v, foglalt=fog, abszolut=True))  # a deviza a számla devizája
        if t.get("reszlet"):
            add("reszlet_arany", t["reszlet"], _keres_szam(text, lang, t["reszlet"], "%", fog)
                or _keres_szam(text, lang, t["reszlet"], "százalék" if lang == "hu" else "percent", fog))
        if t.get("szamlaszam"):
            i = text.find(t["szamlaszam"])
            if i >= 0:
                add("hivatkozas", t["szamlaszam"], (i, i + len(t["szamlaszam"])))
        if t.get("partner"):
            i = text.lower().find(t["partner"].lower())
            if i >= 0:
                add("partner", text[i:i + len(t["partner"])], (i, i + len(t["partner"])))
    elif fam == HIBA:
        rule = {norm(j["meres"]) for j in jeloltek(fam, it["options"], lang)[0]}
        for m in t.get("meresek", []):
            v = float(str(m["ertek"]).replace(",", "."))
            pos = _keres_szam(text, lang, v, m["egyseg"], fog)
            add("meres", v, pos, egyseg=m["egyseg"], kapcsolat=m["nev"] if norm(m["nev"]) in rule else None)
    else:
        if "osszeg" in t:
            v = t["osszeg"]
            dev = t.get("deviza") or ("HUF" if lang == "hu" else "EUR")
            al = "brutto" if "afa" in t else None
            pos = _deviza_mellett(text, lang, v, dev, fog)
            if pos is not None:
                src = _mondat(text, *pos)
                if not any(c in src.lower() for c in DEVIZA_CUE[dev]):
                    src = _bekezdes(text, *pos)
                out.append({"szerep": "osszeg", "ertek": v, "forras": src, "deviza": dev, "alap": al})
        if t.get("afa"):
            add("afakulcs", t["afa"], _keres_szam(text, lang, t["afa"], "%", fog))
        if t.get("arfolyam"):
            add("arfolyam", t["arfolyam"], _keres_szam(text, lang, t["arfolyam"], foglalt=fog))
    return out


# --- önteszt a megismert adaton (tervezési számok) ----------------------------------------------------------------------

FORRASOK = {  # név → (terv-könyvtár, item-könyvtár, sablon-könyvtár vagy None)
    "06": ("kor06/adat/f2/terv", "kor06/adat/f2/items", "kor06/adat/f2/sablon"),
    "07": ("kor07/adat/f2/terv", "kor07/adat/f2/items", "kor07/adat/f2/sablon"),
    "K3diag": ("kor07/adat/diag/terv", "kor07/adat/diag/items", None),
    "ERT": ("kor08/adat/ertelmezes/terv", "kor08/adat/ertelmezes/items", None),  # G1b, az értelmezési konstrukció
    "ERT2": ("kor08/adat/ertelmezes/kor2/terv", "kor08/adat/ertelmezes/kor2/items", None),  # G1b, 2. kör
    "ERT2J": ("kor08/adat/ertelmezes/kor2j/terv", "kor08/adat/ertelmezes/kor2j/items", None),  # 2. kör, javított címkék
    # G2 (`szint08`): a friss CAL / TESZT, a K3-típus, az értelmezési teszt és tanítóminta
    "G2F": ("kor08/adat/G2/friss/terv", "kor08/adat/G2/friss/items", "kor08/adat/G2/sablon"),
    "G2K3": ("kor08/adat/G2/k3/terv", "kor08/adat/G2/k3/items", None),
    "G2T": ("kor08/adat/G2/ert_teszt/terv", "kor08/adat/G2/ert_teszt/items", None),
    "G2N": ("kor08/adat/G2/ert_tanito/terv", "kor08/adat/G2/ert_tanito/items", None),
}
ONTESZT = ("06", "07", "K3diag")  # a G0 önteszt forrásai (az ERT a G1b saját kapuján megy át)


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def betolt(src: str, fam: str) -> list[tuple[dict, dict]]:
    td, idir, _ = FORRASOK[src]
    terv = {p["group_id"]: p for p in jsonl(EXP / td / f"{fam}.jsonl")}
    return [(terv[it["id"]], it) for it in jsonl(EXP / idir / f"{fam}.jsonl") if it["id"] in terv]


def _sablon_egyezes(src: str, fam: str, parok: list[tuple[dict, dict]]) -> dict:
    """A kiolvasott jelöltadat egyezik-e a sablon strukturált adatával (a terv sid-jein át)."""
    sd = FORRASOK[src][2]
    if sd is None:
        return {}
    sab = {s["sablon_id"]: s for s in jsonl(EXP / sd / f"{fam}.jsonl")}
    c = Counter()
    for p, it in parok:
        s = sab.get(p["sablon_id"])
        if s is None:
            c["nincs sablon"] += 1
            continue
        jel = {j["id"]: j for j in jeloltek(fam, it["options"], it["lang"])[0]}
        for o_it, o_p in zip(it["options"], p["opciok"]):
            j = jel.get(o_it["id"])
            if j is None:
                c["nem értelmezhető"] += 1
                continue
            if fam == BANK:
                ref = next((x for x in s["szamlak"] if x["id"] == o_p["sid"]), None)
                want = None if ref is None else (ref["osszeg"] if it["lang"] == "hu" else ref["osszeg"] / 100)
                ok = ref is not None and egyezik(j["osszeg"], want, 0.005) and j["szamlaszam"] == ref["szamlaszam"]
            elif fam == SZAB:
                ref = next((x for x in s["pontok"] if x["id"] == o_p["sid"]), None)
                ok = ref is not None and ref["sav"] == j["sav"] and egyezik(ref["hatar"], j["hatar"])
            else:
                okok = [o for g in s["tunetcsoportok"] for o in g["okok"]]
                ref = next((o for o in okok if o["nev"] == o_p.get("nev", j["nev"])), None)
                ok = ref is not None and ref["meres"]["relacio"] == j["relacio"] and egyezik(float(ref["meres"]["kuszob"]), j["kuszob"], 1e-6) \
                    and norm(ref["meres"]["egyseg"]) == norm(j["egyseg"])
            c["egyezik" if ok else "eltér"] += 1
    return dict(c)


def _k3_csalik(fam: str) -> dict[str, tuple[str, str]]:
    """item-id → (változat, a csali opció id-je), a K3-elemző saját azonosításával."""
    sys.path.insert(0, str(EXP / "kor07/eszkozok"))
    import k3_07  # noqa: PLC0415
    return {k: (str(v[0]), str(v[1])) for k, v in k3_07.csalik("diag", fam).items()}


def onteszt(a) -> None:
    rep: dict = {"forrasok": {}}
    for src in ONTESZT:
        rep["forrasok"][src] = {}
        for fam in CSALADOK:
            parok = betolt(src, fam)
            k3csali = _k3_csalik(fam) if src == "K3diag" else {}
            R: dict = {"n": len(parok), "opcio_ertelmezes": Counter(), "sablon": _sablon_egyezes(src, fam, parok)}
            kim = defaultdict(Counter)
            szk = defaultdict(Counter)
            k_eloszlas = defaultdict(Counter)
            sert = Counter()
            bukott = Counter()
            csali = Counter()
            for p, it in parok:
                jel, rossz = jeloltek(fam, it["options"], it["lang"])
                R["opcio_ertelmezes"]["jó" if not rossz else "rossz"] += 1
                res = lanc(fam, it, orakulum(fam, p, it))
                st = it["content_state"]
                kim[st][res["kimenet"]] += 1
                szk[f"{it['split']}|{st}"][res["kimenet"]] += 1
                for f in res["bukott"]:
                    bukott[f["ok"]] += 1
                if res["kimenet"] == "modell":
                    k_eloszlas[st][len(res["megmaradt"])] += 1
                g = it["gold"]
                if st == "MATCH":
                    if g in res["kizart"]:
                        sert["MATCH: a gold kizárva"] += 1
                    if res["kimenet"] == "kotes" and res["kotes"] != g:
                        sert["MATCH: rossz automatikus kötés"] += 1
                    if res["kimenet"] == "lanc_x":
                        sert["MATCH: X a lánctól"] += 1
                elif res["kimenet"] == "kotes":
                    sert[f"{st}: automatikus kötés"] += 1
                if src == "K3diag":
                    v, cs = k3csali[it["id"]]
                    csali[(v, "csali kizárva" if cs in res["kizart"] else "csali megmaradt")] += 1
            R.update({"kimenet": {k: dict(v) for k, v in kim.items()}, "szelet_kimenet": {k: dict(v) for k, v in sorted(szk.items())}, "k_a_modellnel": {k: dict(sorted(v.items())) for k, v in k_eloszlas.items()},
                      "serules": dict(sert), "bukott_mezok": dict(bukott), "opcio_ertelmezes": dict(R["opcio_ertelmezes"])})
            if csali:
                R["csali"] = {f"{k[0]}|{k[1]}": v for k, v in sorted(csali.items())}
            rep["forrasok"][src][fam] = R
    rep["zavarasok"] = zavarasok()
    rep["egysegtabla"] = egysegtabla()
    out = Path(a.out) if a.out else None
    txt = json.dumps(rep, ensure_ascii=False, indent=1)
    print(txt)
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / "onteszt.json").write_text(txt + "\n", encoding="utf-8")


def zavarasok() -> dict:
    """Az ellenőrzés próbája az orákulum-mezők szándékos rontásával; mindet meg kell fognia."""
    c = defaultdict(Counter)
    for src in ("K3diag", "07"):
        for fam in CSALADOK:
            for p, it in betolt(src, fam):
                f0 = orakulum(fam, p, it)
                if not f0:
                    continue
                jel = jeloltek(fam, it["options"], it["lang"])[0]
                text, lang = it["state"], it["lang"]
                probak = []
                afa = [f for f in f0 if f["szerep"] == "afakulcs"]
                if fam == SZAB and afa:  # Dani példája: az áfakulcs részlet-aránynak olvasva (itt a szabálycsalád szerepeivel:
                    probak.append(("áfakulcs → árfolyam", [{**f, "szerep": "arfolyam"} if f is afa[0] else f for f in f0]))
                rv = [f for f in f0 if f["szerep"] == "reszlet_arany"]
                if fam == BANK and rv:
                    probak.append(("részlet-arány más szereppel (áfakulcs-szerű szövegrész nélkül)",
                                   [{**f, "forras": f["forras"].replace("%", " százalék")} if f is rv[0] else f for f in f0]))
                f = f0[0]
                try:
                    v = float(f["ertek"])
                    probak.append(("rossz érték, jó forrásrészlet", [{**f, "ertek": v * 10 + 1}] + f0[1:]))
                except (TypeError, ValueError):
                    pass
                probak.append(("kitalált forrásrészlet", [{**f, "forras": f["forras"] + " XYZ-kitalalt"}] + f0[1:]))
                if len(f0) >= 1 and f["szerep"] != "hivatkozas" and f["szerep"] != "partner":
                    probak.append(("ugyanaz a szám két szerepben", f0 + [{**f}]))
                me = [x for x in f0 if x["szerep"] == "meres" and x.get("kapcsolat")]
                if me:
                    probak.append(("rossz egység", [{**x, "egyseg": "kg"} if x is me[0] else x for x in f0]))
                osz = [x for x in f0 if x["szerep"] == "osszeg" and x.get("alap") == "brutto"]
                if osz:
                    probak.append(("bruttó nettónak jelölve", [{**x, "alap": "netto"} if x is osz[0] else x for x in f0]))
                for nev, mez in probak:
                    _, rossz = ellenoriz(fam, text, lang, mez, jel)
                    c[nev]["megfogta" if rossz else "átengedte"] += 1
    # Dani példája szó szerint: a 27%-os áfakulcs részlet-aránynak olvasva, egy banki szövegben
    t = "2026-10-08;KIMENŐ;117843;Ft;Számla kiegyenlítése, bruttó összeg 27% áfával"
    jo, rossz = ellenoriz(BANK, t, "hu", [{"szerep": "reszlet_arany", "ertek": 27, "forras": "bruttó összeg 27% áfával"}], [])
    c["27% áfa részlet-aránynak (Dani példája)"]["megfogta" if rossz else "átengedte"] += 1
    return {k: dict(v) for k, v in c.items()}


def egysegtabla() -> dict:
    """A saját egységtábla a K3 VALTAS-ával és a K3 diag mért értékeivel összevetve."""
    sys.path.insert(0, str(EXP / "kor07/eszkozok"))
    import szint07k3 as K3  # noqa: PLC0415
    c = Counter()
    for u1, lst in K3.VALTAS.items():
        for u2, (f, _fi) in lst:
            v = valt(1.0, u1, u2)
            c["egyezik" if v is not None and egyezik(v, f(1.0), 1e-6) else f"eltér: {u1}→{u2}"] += 1
    for p, it in betolt("K3diag", HIBA):
        jel = {norm(j["meres"]): j for j in jeloltek(HIBA, it["options"], it["lang"])[0]}
        for m in p["tenyek"]["meresek"]:
            j = jel.get(norm(m["nev"]))
            if j is None or not m.get("eredeti"):
                continue
            v = valt(float(str(m["ertek"]).replace(",", ".")), m["egyseg"], j["egyseg"])
            c["K3 diag mérés átváltható" if v is not None else f"K3 diag nem váltható: {m['egyseg']}→{j['egyseg']}"] += 1
    return dict(c)


def futtat(a) -> None:
    """A lánc egy forráson: `lanc_<család>.jsonl` (minden item kimenete) és `items/<család>.jsonl` (a modellhez menők).
    `--ut orakulum`: a terv tényeiből; `--ut kinyert`: a `--kinyeres` fájlból (soronként {"id", "mezok"}; hiányzó
    vagy null mezők → emberhez)."""
    out = Path(a.out) if Path(a.out).is_absolute() else EXP / a.out
    (out / "items").mkdir(parents=True, exist_ok=True)
    kin = {}
    if a.ut == "kinyert":
        kin = {r["id"]: r.get("mezok") for r in jsonl(Path(a.kinyeres))}
    for fam in (a.csalad,) if a.csalad else CSALADOK:
        sorok, items = [], []
        for p, it in betolt(a.forras, fam):
            mez = orakulum(fam, p, it) if a.ut == "orakulum" else kin.get(it["id"])
            res = lanc(fam, it, mez, ures=a.ures, valtozat=a.blokk)
            sorok.append({k: v for k, v in res.items() if k != "blokk"} | {"van_blokk": bool(res["blokk"]),
                                                                           "allapot": it["content_state"], "gold": it["gold"]})
            if res["kimenet"] == "modell" or (res["kimenet"] == "lanc_x" and a.ures == "modell"):
                items.append(uj_item(it, res))
        (out / f"lanc_{fam}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sorok), encoding="utf-8")
        (out / "items" / f"{fam}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items), encoding="utf-8")
        print(f"{fam}: {len(sorok)} item, a modellhez {len(items)}; kimenet {dict(Counter(r['kimenet'] for r in sorok))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("onteszt")
    o.add_argument("--out")
    f = sub.add_parser("futtat")
    f.add_argument("--forras", required=True, choices=list(FORRASOK))
    f.add_argument("--csalad", choices=CSALADOK)
    f.add_argument("--ut", required=True, choices=("orakulum", "kinyert"))
    f.add_argument("--kinyeres")
    f.add_argument("--ures", default="modell", choices=("lanc_x", "modell"))  # D2 (Dani, 11-02): üres lista a modellnek
    f.add_argument("--blokk", default="v0", choices=BLOKK_VALTOZAT)  # a szabálycsalád blokkjának változata (G1-próba)
    f.add_argument("--out", required=True)
    a = ap.parse_args()
    {"onteszt": onteszt, "futtat": futtat}[a.cmd](a)


if __name__ == "__main__":
    main()
