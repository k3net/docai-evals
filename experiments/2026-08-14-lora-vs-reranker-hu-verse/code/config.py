"""Központi konfiguráció — korpuszforrások, útvonalak, futási paraméterek.

⚖️ JOGI ALAP (a runbook D0 döntése): a teljes pipeline **közkincs** korpuszon
fut. Magyarországon a szerzői jogi védelem a szerző halálát követő 70. év végéig
tart (Szjt. 31. §), tehát az **1955 előtt elhunyt** szerzők művei közkincsek.
Az itt felsorolt források mindegyike ezt teljesíti; a MEK-cédula jogi állapotát
a letöltéskor a `fetch_corpus.py` a manifestbe menti.

A forrásokat SZERZŐNKÉNT külön tartjuk (`corpus/<author>/`), mert ez a döntés
később szabadon marad: lehet belőlük egy kevert adapter vagy szerzőnként külön.
Ezt a döntést az F1 hozza meg, mért adatok alapján — nem itt.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------- útvonalak

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"  # letöltött, érintetlen forráscsomagok
CORPUS = DATA / "corpus"  # vers-szintű, tisztított JSON
DATASET = DATA / "dataset"  # SFT jsonl
REPORTS = ROOT / "reports"

MANIFEST = DATA / "corpus_manifest.json"


# ---------------------------------------------------------------- források
#
# `encoding`: a MEK 1996–2013 közötti HTML-csomagjai ISO-8859-2-esek, de a
#   magyar ő/ű helyén gyakran a régi „kalapos” ô/û áll (CWI/Mac örökség).
#   Ezt a `build_corpus.py` méri és javítja — ld. `HAT_FIX`.
# `layout`: melyik parse-profil kell (jelenleg mind `mek_frontpage`: a
#   verscím <h3><a name>, a strófa <p>, a sorhatár <br>).
#
SOURCES: dict[str, dict] = {
    "arany": {
        "author": "Arany János",
        "died": 1882,
        "title": "Arany János összes költeményei",
        "mek_id": "MEK-00597",
        "landing": "https://mek.oszk.hu/00500/00597/",
        "zip_url": "https://mek.oszk.hu/00500/00597/00597html.zip",
        "cedula": "https://mek.oszk.hu/00500/00597/cedula.html",
        "encoding": "iso-8859-2",
        "layout": "mek_frontpage",
        "note": (
            "Elbeszélő költemények, balladák, Toldi-trilógia, zsengék. "
            "A legnagyobb magyar rímregiszter; a humoros vonulat is benne "
            "(A fülemile, Jóka ördöge, A nagyidai cigányok)."
        ),
    },
    "petofi": {
        "author": "Petőfi Sándor",
        "died": 1849,
        "title": "Petőfi Sándor összes költeményei",
        "mek_id": "MEK-01006",
        "landing": "https://mek.oszk.hu/01000/01006/",
        "zip_url": "https://mek.oszk.hu/01000/01006/01006html.zip",
        "cedula": "https://mek.oszk.hu/01000/01006/cedula.html",
        "encoding": "iso-8859-2",
        "layout": "mek_frontpage",
        "note": (
            "Népies-dalos és komikus eposzi regiszter (A helység kalapácsa, "
            "János vitéz). A MEK-cédula kifejezetten kiírja: „Nem jogvédett”."
        ),
    },
}

# Elvetett források — a döntés indoklása maradjon a kódban, ne csak a fejben:
#
#   Romhányi József (†1983)  → 2053-ig védett, licenc nélkül KIZÁRVA (D0).
#   Karinthy: Így írtok ti   → a szerző (†1938) közkincs, de a kötet vegyes
#                              próza+vers, egységes strófaszerkezet nélkül;
#                              a parse-nyereség nem érné meg a zajt.
#   Weöres Sándor (†1989)    → védett.


# ---------------------------------------------------------- HTML → szöveg
#
# A „kalapos ő/ű” a régi magyar 8-bites kódolások öröksége: az ISO-8859-2-ben
# 0xF5 (ő) helyett 0xF4 (ô) áll. Karakter-szinten javítható, de CSAK magyar
# szövegben — ezért mérjük is, hány cserét végeztünk (riportba kerül).
HAT_FIX = {"ô": "ő", "Ô": "Ő", "û": "ű", "Û": "Ű"}


# ------------------------------------------------------------- prozódia
#
# A prozódiai konstansok EGYETLEN forrása a mérőeszköz maga:
# `docai-evals/scripts/hu_prosody.py` (önálló, self-testtel). Itt csak
# újraexportáljuk őket, hogy a meglévő `from config import RHYME_THRESHOLD`
# importok változatlanul működjenek. Két külön másolat néma inkonzisztenciát
# okozna: az `evaluate.py` a config küszöbét használná, a pontozó a magáét.

import sys  # noqa: E402

sys.path.insert(0, str(ROOT.parent.parent / "scripts"))

from hu_prosody import (  # noqa: E402,F401
    DIGRAPHS,
    RHYME_THRESHOLD,
    STRICT_RHYME_THRESHOLD,
    VOWELS,
)
