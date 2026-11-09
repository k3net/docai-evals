"""06-os kör — a három friss család építése (06-runbook 3.1, 3.4–3.5; spec: kor06/spec/csaladok06.yaml).

A terv (sablon → alapeset-terv) determinisztikus: az adja az állapotot, a gold-ot, az opciókat és a döntő tényeket. A
generátor csak a helyzetleírást (az item `state` mezőjét) írja a megadott tényekből. A generált szövegen programból
ellenőrizzük, hogy a döntő tények benne vannak, MISSING_DATA-nál pedig, hogy a hiányzó adat nincs benne; ami elbukik,
újragenerálódik, végül elvész (a szűrési arányt állapotonként közöljük). A generátor önálló válasza soha nem címke (D13).

  sablon --csalad F [--proba] [--url U --model M]   → kor06/adat/f2/sablon/F[.proba].jsonl
         a bank- és a szabálycsalád sablonja programból, a hibaelhárításé (okkatalógus) a generátortól
  terv   --csalad F [--proba]                        → kor06/adat/f2/terv/F[.proba].jsonl
  gen    --csalad F [--proba] --url U --model M      → kor06/adat/f2/raw/F[.proba].jsonl
  final  --csalad F [--proba]                        → kor06/adat/f2/items/F[.proba].jsonl + összesítő
  lap                                                → kor06/adat/f2/proba/proba_lap.md (a próba Dani átnézéséhez)

Szétválasztás (D12): a sabloncsoport (cég, berendezésmodell, szabályzat) egészében kerül a T500, a CAL vagy a TESZT
részbe; nyelvenként külön sablonok, így fordításpár nincs (D9). A szeleten belül az állapot × nyelv kvóta pontos; a
tartalékból a szűrés után a terv hash-sorrendjének első N túlélője marad (3.4).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import re
import shutil
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor03/eszkozok"), str(EXP / "eszkozok")]
from biralo import chat  # noqa: E402
from kie03 import company  # noqa: E402

SPEC = yaml.safe_load((EXP / "kor06/spec/csaladok06.yaml").read_text(encoding="utf-8"))
K = SPEC["kozos"]
D = EXP / "kor06/adat/f2"
SEED = "szint06:2026-10-29"
STATES = ("MATCH", "NO_MATCH", "MISSING_DATA", "OUT_OF_SCOPE")
X_TYPE = {"NO_MATCH": "gold-drop", "MISSING_DATA": "missing-precondition", "OUT_OF_SCOPE": "out-of-scope"}
LANGS = ("hu", "en")
SPLITS = ("T500", "CAL", "TESZT")

CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[\w-]+")
URL = re.compile(r"https?://|www\.", re.I)
PLACEHOLDER = re.compile(r"\[[^\]\n]{2,40}\]|<[A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű _]{2,30}>|\{[^}\n]{2,30}\}")
# a címkét vagy az állapotot kimondó fordulatok: ha a szövegben vannak, újragenerálunk
LEAK = {"hu": ["egyik sem", "nincs a listán", "nem szerepel a listán", "nem állapítható meg", "nem dönthető el",
               "nem eldönthető", "nem tartozik ide", "nem ehhez a feladathoz"],
        "en": ["none of the", "not on the list", "not listed", "cannot be determined", "can't be determined",
               "not possible to determine", "out of scope", "not relevant to"]}
FIRST_EN = ["Emma", "James", "Olivia", "Noah", "Sophie", "Liam", "Grace", "Oliver", "Chloe", "Henry", "Lucy", "Jack"]
SURN_EN = ["Walker", "Bennett", "Hughes", "Carter", "Fletcher", "Morgan", "Turner", "Hayes", "Palmer", "Reid",
           "Lawson", "Brooks", "Foster", "Graham", "Holt", "Marsh"]
ROOT_EN = ["Northgate", "Bluefield", "Harbourline", "Redstone", "Kestrel", "Ashford", "Brightwater", "Copperleaf",
           "Driftwood", "Elmbridge", "Foxglove", "Granite Peak", "Hollowmere", "Ironbark", "Juniper", "Lakeside",
           "Meadowcroft", "Oakhurst", "Pinecrest", "Silverline", "Thornbury", "Westbrook", "Willowdale", "Yarrow"]
ACT_EN = ["Logistics", "Supplies", "Engineering", "Foods", "Print", "Facilities", "Software", "Electrical", "Packaging",
          "Consulting", "Hardware", "Catering"]
FORM_EN = ["Ltd", "LLC", "Inc.", "plc", "Ltd."]

GEN_SYSTEM = {
    "hu": ("Magyar nyelvű szintetikus adatot írsz egy döntési modell kiértékeléséhez. Csak a kért JSON-objektumot add "
           "vissza, magyarázat és kódblokk nélkül. Kizárólag kitalált neveket használj. E-mail-cím csak a pelda.example "
           "tartományban, telefonszám csak +36 1 555 xxxx alakban szerepelhet. Szögletes zárójeles helykitöltőt ne "
           "használj: mindenhová konkrét adat kerüljön."),
    "en": ("You write synthetic English data for evaluating a decision model. Return only the requested JSON object, "
           "without explanation or code fences. Use invented names only. E-mail addresses only in the pelda.example "
           "domain, phone numbers only as +36 1 555 xxxx. No bracketed placeholders: always write concrete data."),
}


def h(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def rnd_for(*parts) -> random.Random:
    return random.Random(":".join(map(str, (SEED, *parts))))


def path(kind: str, fam: str, proba: bool) -> Path:
    return D / kind / f"{fam}{'.proba' if proba else ''}.jsonl"


def jl_read(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def jl_write(p: Path, rows: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


HU_CHARS = re.compile(r"[áéíóöőúüűÁÉÍÓÖŐÚÜŰ]")


HU_SW = {"és", "hogy", "nem", "van", "egy", "az", "nincs", "kérem", "köszönöm", "vagy", "mert", "ezt", "azt", "volt", "lesz",
         "már", "még", "csak", "kell", "vagyok", "szia", "sziasztok", "üdvözlettel", "tisztelt", "kérlek", "ma", "után"}
EN_SW = {"the", "and", "of", "to", "with", "for", "please", "thank", "thanks", "are", "was", "this", "that", "from", "on", "we",
         "you", "regards", "dear", "hi", "have", "our"}  # a "be" és a "has" magyar szó is


def lang_ok(text: str, lang: str, katalogus: bool = False) -> bool:
    """Durva nyelvellenőrzés. A szövegen a magyar (funkciószó vagy ékezetes) és az angol funkciószavak arányából; a
    puszta ékezetarány a magyar nevű aláírást is magyarnak vette (próba v2). A katalóguson, ahol nincs név és kevés a
    funkciószó, az ékezetarányból. A két próba itemjein bemérve (Napló, 2026-10-29)."""
    if katalogus:
        r = len(HU_CHARS.findall(text)) / max(1, len(text))
        return (not re.search(r"[őűŐŰ]", text) and r < 0.005) if lang == "en" else r > 0.01
    toks = re.findall(r"[a-záéíóöőúüű]+", text.lower())
    if len(toks) < 8:  # egy CSV-sor vagy egy rövid értesítő: nincs miből
        return True
    huw = sum(t in HU_SW or bool(HU_CHARS.search(t)) for t in toks) / len(toks)
    en = sum(t in EN_SW for t in toks) / len(toks)
    return huw < 0.08 if lang == "en" else (en < 0.03 and huw > 0.10)


def num_re(v: str) -> str | None:
    """Egy számérték mintája önálló számként (tizedesvessző vagy -pont, opcionális előjel); None, ha nem szám."""
    m = re.fullmatch(r"([-−]?)(\d+)(?:[.,](\d+))?", v.strip())
    if not m:
        return None
    return rf"(?<![\d.,])[-−]?{m.group(2)}" + (rf"[.,]{m.group(3)}" if m.group(3) else "") + r"(?![\d]|[.,]\d)"


def value_present(text: str, v) -> bool:
    r = num_re(str(v))
    return bool(re.search(r, text)) if r else str(v).strip().lower() in text.lower()


def reading_present(text: str, v, unit: str) -> bool:
    """Mért érték a mértékegységével (MISSING_DATA-nál ez a tiltott: egy önálló szám a dátumban még nem mérés)."""
    r = num_re(str(v))
    if not r:
        return str(v).strip().lower() in text.lower()
    return bool(re.search(r + r"\s*" + re.escape(unit.strip()), text, re.I))


def norm_date(text: str) -> str:
    return re.sub(r"(?<=\d)[-./\s](?=\d)", "", text)


def norm_digits(text: str) -> str:
    """A számjegyek közti ezres- és tizedes-elválasztók nélkül (az összeg-ellenőrzéshez)."""
    return re.sub(r"(?<=\d)[\s.,  '](?=\d)", "", text)


def norm_ref(text: str) -> str:
    return re.sub(r"[\s/\-_.]", "", text).upper()


# --- sablonok -----------------------------------------------------------------------------------------------------------

def partner(rnd: random.Random, lang: str) -> str:
    if lang == "hu":
        return company(rnd)
    if rnd.random() < 0.25:
        return f"{rnd.choice(SURN_EN)} & {rnd.choice(SURN_EN)} {rnd.choice(FORM_EN)}"
    return f"{rnd.choice(ROOT_EN)} {rnd.choice(ACT_EN)} {rnd.choice(FORM_EN)}"


def money(amount: int, lang: str) -> str:
    """HUF egész forintban, EUR centben tárolva."""
    if lang == "hu":
        return f"{amount:,} Ft".replace(",", " ")
    return f"EUR {amount // 100:,}.{amount % 100:02d}"


def bank_sablon(tid: str, lang: str) -> dict:
    """Egy szintetikus cég nyitott számlái: 8 partner, 14 számla; három összeg két partnernél is előfordul (a
    MISSING_DATA és a nehéz negatívok alapja), és minden partnernek legalább egy másik számlája is van."""
    rnd = rnd_for("bank", tid)
    partners = []
    while len(partners) < 8:
        p = partner(rnd, lang)
        if p.split()[0] not in {x.split()[0] for x in partners}:
            partners.append(p)
    pref = rnd.choice(["SZ", "KH", "VSZ", "E", "BV"] if lang == "hu" else ["INV", "IN", "SI", "BL", "AR"])
    year = 2026
    nums = rnd.sample(range(100, 9999), 14)
    amounts = []
    for _ in range(11):
        a = rnd.randint(18_000, 2_400_000) // 10 * 10 if lang == "hu" else rnd.randint(4_500, 2_500_000)
        amounts.append(a)
    amounts += [amounts[0], amounts[1], amounts[2]]  # a három közös összeg
    owner = [partners[i % 8] for i in range(14)]
    for k, j in ((11, 0), (12, 1), (13, 2)):  # a közös összeg másik partnernél
        owner[k] = partners[(partners.index(owner[j]) + 3) % 8]
    inv = []
    for i in range(14):
        issued = f"{year}-{rnd.randint(6, 9):02d}-{rnd.randint(1, 28):02d}"
        inv.append({"id": f"s{i + 1}", "szamlaszam": f"{pref}-{year}/{nums[i]:04d}" if lang == "hu" else f"{pref}-{year}-{nums[i]:04d}",
                    "partner": owner[i], "osszeg": amounts[i], "kelt": issued,
                    "esedekes": f"{year}-{min(int(issued[5:7]) + 1, 12):02d}-{issued[8:]}"})
    # D21 (Dani, 2026-10-31): a közös összegű pár azonos esedékességgel, különben a MISSING_DATA-n az esedékesség szerinti
    # választás elfogadható döntés. A kelte (nem látszik, a tranzakció dátuma ebből jön) és a véletlensorozat változatlan.
    for k, j in ((11, 0), (12, 1), (13, 2)):
        inv[k]["esedekes"] = inv[j]["esedekes"]
    ceg = partner(rnd, lang)
    while ceg.split()[0] in {x.split()[0] for x in partners}:  # a saját cég neve ne egyezzen egy partnerével
        ceg = partner(rnd, lang)
    return {"sablon_id": tid, "lang": lang, "ceg": ceg, "szamlak": inv}


SZAB_TIPUS = {
    "hu": {"utazás": "belföldi kiküldetés utazási és szállásköltsége", "reprezentáció": "üzleti vendéglátás és ajándék",
           "képzés": "szakmai képzés, tanfolyam, konferencia-részvétel", "eszköz": "munkaeszköz-beszerzés (számítástechnika, szerszám)",
           "előfizetés": "szoftver- és szakmai előfizetés"},
    # D18 (Dani, 2026-10-30): a „domestic” és a „client” kikerült; a helyzetek (Leeds, Bristol, EUR, beszállítói ebéd)
    # ezeket nem alapozták meg, az auditon a belföldiség hiánya címkehibát adott (a077, a124)
    "en": {"travel": "business travel and accommodation", "entertainment": "business entertainment and gifts",
           "training": "professional training, courses and conference fees", "equipment": "work equipment purchases (IT, tools)",
           "subscription": "software and professional subscriptions"},
}
SZAB_JOVAHAGY = {"hu": ["a közvetlen vezető", "a részlegvezető", "a pénzügyi igazgató", "az ügyvezető"],
                 "en": ["the line manager", "the department head", "the finance director", "the managing director"]}


def szabaly_sablon(tid: str, lang: str) -> dict:
    """Egy szintetikus költségszabályzat: három költségnem × két értéksáv = hat pont, nemenként saját értékhatárral."""
    rnd = rnd_for("szabaly", tid)
    tipusok = rnd.sample(list(SZAB_TIPUS[lang]), 3)
    fej = rnd.randint(3, 9)
    pontok = []
    for i, t in enumerate(tipusok):
        hatar = rnd.choice([30_000, 50_000, 80_000, 100_000, 150_000, 200_000]) if lang == "hu" else rnd.choice([100, 150, 250, 400, 500, 750])
        lo, hi = rnd.sample(SZAB_JOVAHAGY[lang][:2], 1)[0], rnd.sample(SZAB_JOVAHAGY[lang][2:], 1)[0]
        hstr = f"{hatar:,} Ft".replace(",", " ") if lang == "hu" else f"EUR {hatar:,}"
        for b, jov in enumerate((lo, hi)):
            szam = f"{fej}.{2 * i + b + 1}"
            hu_sav = f"legfeljebb {hstr}" if b == 0 else f"{hstr} felett"
            en_sav = f"up to {hstr}" if b == 0 else f"above {hstr}"
            szoveg = (f"{szam}. {SZAB_TIPUS[lang][t].capitalize()}, {hu_sav}: {jov} hagyja jóvá." if lang == "hu" else
                      f"{szam}. {SZAB_TIPUS[lang][t].capitalize()} {en_sav}: approved by {jov}.")
            pontok.append({"id": f"p{2 * i + b + 1}", "tipus": t, "sav": b, "hatar": hatar, "szoveg": szoveg})
    return {"sablon_id": tid, "lang": lang, "szervezet": partner(rnd, lang), "pontok": pontok}


HIBA_BERENDEZES = {"hu": ["ipari légkondicionáló", "irodai lézernyomtató", "vállalati Wi-Fi hozzáférési pont",
                          "kisteherautó dízelmotorja", "ipari centrifugálszivattyú", "hűtőkamra", "ipari kompresszor",
                          "szünetmentes tápegység"],
                   "en": ["industrial air conditioner", "office laser printer", "enterprise Wi-Fi access point",
                          "light van diesel engine", "industrial centrifugal pump", "walk-in cold room",
                          "industrial air compressor", "uninterruptible power supply"]}


def hiba_sablon_prompt(lang: str, berendezes: str, modell: str) -> str:
    """A diagnosztikai szabálytábla (Dani, 2026-10-29): okonként egy szabály, „igazolt, ha a tünet X és a mérés M a
    küszöb alatt/felett”; a megoldó a szabályt az opcióval együtt megkapja. A két ok egy tünetcsoportban ugyanazt a
    tünetet adja, és csak a saját mérésével igazolható."""
    if lang == "hu":
        return (f"Készíts diagnosztikai szabálytáblát egy kitalált berendezéshez: {berendezes}, típus: {modell}.\n"
                "Pontosan 4 tünetcsoport legyen; mindegyikben pontosan 2 különböző ok, amelyek ugyanazt a tünetet "
                "okozzák. Minden okhoz egy saját mérés tartozik, amely önmagában, közvetlenül igazolja az okot (például "
                "referencia-műszerrel mért eltérés, ne olyan mennyiség, amelyet a csoport másik oka is magyarázna). "
                "Minden mérésnek legyen neve, mértékegysége, relációja (\"<\" vagy \">\"), számszerű küszöbe, egy "
                "jellemző értéke, ha az ok fennáll (teljesíti a relációt), és egy normál értéke (nem teljesíti). A "
                "nyolc mérés neve mind különböző legyen. Minden szöveges érték magyarul legyen.\n"
                'Formátum: {"tunetcsoportok": [{"tunet": "...", "okok": [{"nev": "...", "meres": {"nev": "...", '
                '"egyseg": "...", "relacio": ">", "kuszob": 0, "ertek_ha_ez": 0, "ertek_normal": 0}}, {...}]}, ...]}')
    return (f"Create a diagnostic rule table for an invented device: {berendezes}, model: {modell}.\n"
            "Exactly 4 symptom groups; each with exactly 2 different causes that produce the same symptom. Each cause has "
            "its own measurement that directly confirms that cause on its own (e.g. a deviation measured against a "
            "reference instrument, not a quantity the other cause in the group could also explain). Each measurement "
            "has a name, unit, relation (\"<\" or \">\"), numeric threshold, a typical value if the cause is present "
            "(satisfies the relation) and a normal value (does not satisfy it). All eight measurement names must be "
            "different. All text values must be in English.\n"
            'Format: {"tunetcsoportok": [{"tunet": "...", "okok": [{"nev": "...", "meres": {"nev": "...", '
            '"egyseg": "...", "relacio": ">", "kuszob": 0, "ertek_ha_ez": 0, "ertek_normal": 0}}, {...}]}, ...]}')


def _num(x) -> float | None:
    try:
        return float(str(x).replace(",", ".").replace("−", "-"))
    except ValueError:
        return None


# programazonosító-szerű név: aláhúzás vagy CamelCase („dob_tengely_zaj”, „GlowPlugResistance”); a „PoE”, „SoC”, „WiFi”
# típusú szakszó nem az (a 10-30-i K06F2HB-n a szigorúbb `[a-z][A-Z]` egy hálózati katalógust hat próbán át elutasított)
AZONOSITO_RX = re.compile(r"_|[a-záéíóöőúüű]{2}[A-ZÁÉÍÓÖŐÚÜŰ][a-záéíóöőúüű]")
SABLON_PROBA = 12


def hiba_sablon_ok(obj: dict) -> str | None:
    """A szabálytábla programos ellenőrzése: a hibás érték teljesíti a relációt, a normál nem; nevek egyediek."""
    g = obj.get("tunetcsoportok")
    if not isinstance(g, list) or len(g) != 4:
        return "nem 4 tünetcsoport"
    names, mer = set(), set()
    for c in g:
        if not c.get("tunet") or not isinstance(c.get("okok"), list) or len(c["okok"]) != 2:
            return "hiányos tünetcsoport"
        for o in c["okok"]:
            m = o.get("meres") or {}
            if not (o.get("nev") and m.get("nev") and m.get("egyseg") and m.get("relacio") in ("<", ">")):
                return "hiányos ok"
            k, a, n = _num(m.get("kuszob")), _num(m.get("ertek_ha_ez")), _num(m.get("ertek_normal"))
            if None in (k, a, n):
                return "nem számszerű küszöb vagy érték"
            sat = (lambda v: v < k) if m["relacio"] == "<" else (lambda v: v > k)
            if not sat(a) or sat(n) or a == k or n == k:
                return "a szabály és az értékek ellentmondanak"
            if any(AZONOSITO_RX.search(x) for x in (o["nev"], m["nev"], c["tunet"])):
                return "programazonosító-szerű név"
            names.add(o["nev"].lower())
            mer.add(m["nev"].lower())
    if len(names) != 8 or len(mer) != 8:
        return "ismétlődő ok vagy mérés"
    return None


def fmt_num(x, lang: str) -> str:
    v = _num(x)
    t = f"{v:g}" if v is not None else str(x)
    return t.replace(".", ",") if lang == "hu" else t


def hiba_szabaly(o: dict, tunet: str, lang: str) -> str:
    m = o["meres"]
    kus = f"{fmt_num(m['kuszob'], lang)} {m['egyseg']}"
    if lang == "hu":
        return f"igazolt, ha a tünet: {tunet.rstrip('.')}, és {nevelo(m['nev'])} {m['nev']} {'kisebb, mint' if m['relacio'] == '<' else 'nagyobb, mint'} {kus}"
    return f"confirmed if the symptom is: {tunet.rstrip('.')}, and {m['nev']} is {'below' if m['relacio'] == '<' else 'above'} {kus}"


def llm_json(url: str, model: str, lang: str, user: str, extra: dict, seed: int, tries: int = 4) -> dict:
    last = None
    for k in range(tries):
        try:
            r = chat(url, model, [{"role": "system", "content": GEN_SYSTEM[lang]}, {"role": "user", "content": user}],
                     {"temperature": 0.8, "max_tokens": 4000, **extra, "seed": seed * 10 + k}, None, timeout=900)
            txt = r["choices"][0]["message"]["content"] or ""
        except Exception as e:  # noqa: BLE001
            last = f"http: {e}"
            continue
        txt = txt.split("</think>")[-1]
        if CJK.search(txt):
            last = "CJK"
            continue
        txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
        s, e = txt.find("{"), txt.rfind("}")
        try:
            obj = json.loads(txt[s:e + 1], strict=False)
        except Exception:  # noqa: BLE001
            last = "JSON"
            continue
        flat = json.dumps(obj, ensure_ascii=False)
        if URL.search(flat) or any(not m.group(0).endswith("pelda.example") for m in EMAIL.finditer(flat)):
            last = "PII/URL"
            continue
        if PLACEHOLDER.search(flat):
            last = "helykitöltő"
            continue
        return obj
    raise RuntimeError(f"LLM-hívás sikertelen ({last})")


def sablon_ids(fam: str, proba: bool) -> list[tuple[str, str, str]]:
    """(sablon_id, nyelv, szelet); a szelet a sablon hash-rangja szerint, nyelvenként pontos darabszámmal."""
    if proba:
        return [(f"{fam}:proba:{lang}:{i}", lang, "proba") for lang in LANGS for i in range(2)]
    n = K["sablon_per_nyelv"]
    out = []
    for lang in LANGS:
        ids = sorted((f"{fam}:{lang}:{i:03d}" for i in range(sum(n.values()))), key=lambda t: h(f"{SEED}:szelet:{t}"))
        k = 0
        for sz in SPLITS:
            out += [(t, lang, sz) for t in ids[k:k + n[sz]]]
            k += n[sz]
    return out


def cmd_sablon(a) -> None:
    fam, rows = a.csalad, []
    todo = sablon_ids(fam, a.proba)
    if fam == "penzugy.bankparositas":
        rows = [bank_sablon(t, lang) | {"szelet": sz} for t, lang, sz in todo]
    elif fam == "szabaly.koltsegelszamolas":
        rows = [szabaly_sablon(t, lang) | {"szelet": sz} for t, lang, sz in todo]
    elif fam == "muszaki.hibaelharitas":
        extra = json.loads(a.extra) if a.extra else {}
        # részeredmény: a kész katalógus azonnal a `.reszleges` fájlba kerül, újraindításkor onnan folytatódik; az
        # elutasítások oka próbálkozásonként a `.elutasitas` fájlba
        part = path("sablon", fam, a.proba).with_suffix(".reszleges.jsonl")
        rej = path("sablon", fam, a.proba).with_suffix(".elutasitas.jsonl")
        kesz = {r["sablon_id"]: r for r in jl_read(part)}
        part.parent.mkdir(parents=True, exist_ok=True)
        lock = threading.Lock()

        def one(x):
            t, lang, sz = x
            if t in kesz:
                return kesz[t]
            rnd = rnd_for("hiba", t)
            ber = rnd.choice(HIBA_BERENDEZES[lang])
            modell = f"{rnd.choice(['TX', 'KM', 'Aero', 'Vento', 'PX', 'Nord', 'Helix'])}-{rnd.randint(100, 990)}"
            for k in range(SABLON_PROBA):
                try:
                    obj = llm_json(a.url, a.model, lang, hiba_sablon_prompt(lang, ber, modell), extra, h(f"sablon:{t}:{k}") % 10**6)
                    err = hiba_sablon_ok(obj) or (None if lang_ok(json.dumps(obj["tunetcsoportok"], ensure_ascii=False), lang,
                                                                  katalogus=True) else "rossz nyelv")
                except RuntimeError as e:
                    err = str(e)
                if err is None:
                    r = {"sablon_id": t, "lang": lang, "szelet": sz, "berendezes": ber, "modell": modell,
                         "tunetcsoportok": obj["tunetcsoportok"]}
                    with lock, open(part, "a", encoding="utf-8") as fh:
                        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
                    return r
                with lock, open(rej, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"sablon_id": t, "proba": k, "ok": err}, ensure_ascii=False) + "\n")
            return None
        with ThreadPoolExecutor(a.workers) as ex:
            rows = list(ex.map(one, todo))
        if None in rows:
            bad = [t for (t, _, _), r in zip(todo, rows) if r is None]
            raise SystemExit(f"{fam}: {len(bad)} katalógus {SABLON_PROBA} próbálkozásra sem érvényes: {', '.join(bad)} "
                             f"(a többi a {part.name}-ban; újraindítva csak ezek futnak)")
    else:
        raise SystemExit(f"ismeretlen család: {fam}")
    jl_write(path("sablon", fam, a.proba), rows)
    print(f"{fam}: {len(rows)} sablon", flush=True)


# --- alapeset-tervek ----------------------------------------------------------------------------------------------------

def quotas(proba: bool) -> dict[tuple[str, str, str], int]:
    """(szelet, nyelv, állapot) → tervezett darabszám (a kvóta + tartalék; a próbán cellánként rögzített)."""
    if proba:
        return {("proba", lang, st): K["proba"]["cellankent"] for lang in LANGS for st in STATES}
    out = {}
    for sz in SPLITS:
        for lang in LANGS:
            for st in STATES:
                q = round(K["alapeset"][sz] * K["nyelv_arany"][lang] * K["allapot_arany"][st])
                out[(sz, lang, st)] = q + max(2, round(q * K["tartalek"]))
    return out


def kvota(sz: str, lang: str, st: str) -> int:
    return round(K["alapeset"][sz] * K["nyelv_arany"][lang] * K["allapot_arany"][st])


DIM = {  # (magyar, angol) párok; a prompt a cél nyelvén kapja
    "penzugy.bankparositas": {"forma": [("netbankos értesítő", "online banking notification"),
                                        ("CSV-kivonat egy sora", "one line of a CSV bank statement"),
                                        ("könyvelő e-mailje a tételről", "an accountant's e-mail about the entry"),
                                        ("PDF-kivonatból kimásolt sor", "a line copied from a PDF bank statement")]},
    "muszaki.hibaelharitas": {"bejelento": [("laikus felhasználó", "non-technical user"), ("karbantartó technikus", "maintenance technician"),
                                            ("üzemvezető", "plant manager")],
                              "forma": [("e-mail", "e-mail"), ("hibajegy", "support ticket"),
                                        ("telefonos bejelentés jegyzete", "notes taken during a phone call"), ("csevegőüzenet", "chat message")],
                              "hossz": [("rövid", "short"), ("közepes", "medium length")]},
    "szabaly.koltsegelszamolas": {"forma": [("e-mail a pénzügynek", "e-mail to the finance team"),
                                            ("költségtérítési kérelem", "expense reimbursement form"), ("csevegőüzenet", "chat message")],
                                  "regiszter": [("hivatalos", "formal"), ("köznapi", "casual"), ("tömör", "terse")]},
}
IRANY = {"hu": ("bejövő jóváírás", "kimenő terhelés"), "en": ("incoming credit", "outgoing debit")}
OOS = {"penzugy.bankparositas": {"hu": ["munkabér-átutalás egy munkavállalónak", "adó- vagy járulékfizetés a NAV-nak",
                                        "számlavezetési díj", "átvezetés a cég saját megtakarítási számlájára"],
                                 "en": ["salary payment to an employee", "tax or social contribution payment to the tax authority",
                                        "bank account maintenance fee", "transfer to the company's own savings account"]},
       "muszaki.hibaelharitas": {"hu": ["új funkció kérése", "használati kérdés (hogyan kell beállítani valamit)",
                                        "számlázási vagy szerződéses kérdés a szervizszerződésről", "időpontegyeztetés a rendszeres karbantartásra"],
                                 "en": ["feature request", "how-to question about a setting", "billing or contract question about the service agreement",
                                        "scheduling a routine maintenance visit"]},
       # D19 (Dani, 2026-10-30): a „beszerzési igény egy új szerverre” átfedett a munkaeszköz-beszerzés pontjával (a093, a106,
       # a135, a178: O helyett M is védhető), helyette lakcímváltozás
       "szabaly.koltsegelszamolas": {"hu": ["szabadságkérelem", "informatikai hibabejelentés", "lakcímváltozás bejelentése a HR-nek",
                                            "kérdés a munkaidő-nyilvántartásról"],
                                     "en": ["annual leave request", "IT support ticket", "notification of a change of home address to HR",
                                            "question about timesheets"]}}
# a költségnem konkrét helyzetként jut a generátorhoz, hogy a kérelem ne a szabálypont szövegét ismételje
SZAB_HELYZET = {
    "hu": {"utazás": ["vonatjegy és egy éjszakai szállás egy debreceni ügyféllátogatáshoz",
                      "autópálya-matrica és üzemanyag egy győri telephelyi bejáráshoz",
                      "buszjegy és két éjszaka szállás egy pécsi kiküldetéshez", "taxi és szállodai szoba egy szegedi tárgyaláshoz"],
           "reprezentáció": ["üzleti vacsora két ügyfélpartnerrel egy étteremben", "karácsonyi ajándékcsomagok a kulcsügyfeleknek",
                             "ebéd egy beszállítói tárgyalás után", "borkóstoló egy új partner fogadására"],
           "képzés": ["egy kétnapos projektmenedzsment-tanfolyam díja", "részvételi díj egy szakmai konferencián",
                      "online adatbiztonsági tréning", "a munkakörhöz szükséges nyelvi kurzus"],
           "eszköz": ["új laptop egy fejlesztő kollégának", "akkus fúrógép és bitkészlet a karbantartóknak",
                      "két külső monitor az irodába", "vonalkódolvasó a raktárba"],
           "előfizetés": ["éves tervezőszoftver-licenc", "egy szakmai folyóirat egyéves előfizetése",
                          "felhőtárhely-előfizetés a csapatnak", "havidíjas jogszabályfigyelő szolgáltatás"]},
    "en": {"travel": ["train ticket and one night in a hotel for a client visit in Leeds", "fuel and motorway tolls for a site inspection",
                      "coach fare and two nights' accommodation for a trip to the regional office", "taxi and a hotel room for a negotiation in Bristol"],
           "entertainment": ["business dinner with two client representatives", "holiday gift baskets for key customers",
                             "lunch after a supplier negotiation", "wine tasting to welcome a new partner"],
           "training": ["fee for a two-day project management course", "registration fee for an industry conference",
                        "online data security training", "a language course required for the role"],
           "equipment": ["a new laptop for a developer", "a cordless drill and bit set for the maintenance team",
                         "two external monitors for the office", "a barcode scanner for the warehouse"],
           "subscription": ["annual licence for design software", "one-year subscription to a professional journal",
                            "cloud storage subscription for the team", "monthly legal update service"]},
}


def nevelo(nev: str, nagy: bool = False) -> str:
    """A magyar határozott névelő a név kezdőhangja szerint (a próba v4-ben a „a(z)” utasítás szó szerint a szövegbe
    került: a bank 19%-ában, a szabálycsalád 30%-ában, a hibaelhárítás 93%-ában)."""
    a = "az" if nev.strip()[:1].lower() in "aáeéiíoóöőuúüű" else "a"
    return a.capitalize() if nagy else a


def tx_date(rnd: random.Random, kelt: list[str]) -> str:
    """A tranzakció dátuma a legkésőbbi érintett számlakelte után (hogy a dátum ne zárjon ki opciót)."""
    d = max(dt.date.fromisoformat(x) for x in kelt) + dt.timedelta(days=rnd.randint(3, 40))
    return min(d, dt.date(2026, 12, 20)).isoformat()


def plan_case(fam: str, sab: dict, st: str, seq: int) -> dict:
    """Egy alapeset terve: opciók (3–6), gold, a szövegbe kerülő és a kizárt tények."""
    rnd = rnd_for("terv", sab["sablon_id"], st, seq)
    lang = sab["lang"]
    p = {"csalad": fam, "sablon_id": sab["sablon_id"], "lang": lang, "allapot": st, "szelet": sab["szelet"],
         "dim": {k: rnd.choice(v)[LANGS.index(lang)] for k, v in DIM[fam].items()}}
    k = rnd.randint(K["opciok"]["min"], K["opciok"]["max"])
    if fam == "penzugy.bankparositas":
        inv = sab["szamlak"]
        by_amt = defaultdict(list)
        for s in inv:
            by_amt[s["osszeg"]].append(s)
        if st == "MISSING_DATA":
            a1, a2 = rnd.choice([v for v in by_amt.values() if len(v) == 2])
            rest = rnd.sample([s for s in inv if s["osszeg"] != a1["osszeg"]], k - 2)
            opts, gold = [a1, a2, *rest], None
            p["tenyek"] = {"osszeg": a1["osszeg"], "irany": rnd.choice(IRANY[lang]), "datum": tx_date(rnd, [a1["kelt"], a2["kelt"]])}
            p["tilos"] = {"partner": [s["partner"] for s in opts], "szamlaszam": [s["szamlaszam"] for s in opts]}
        else:
            target = rnd.choice(inv)
            # nehéz negatívok: ugyanaz a partner más összeggel, ugyanaz az összeg más partnernél
            hard = [s for s in inv if s is not target and (s["partner"] == target["partner"] or s["osszeg"] == target["osszeg"])]
            pool = [s for s in inv if s is not target and s not in hard]
            neg = hard[:2] + rnd.sample(pool, max(0, k - 1 - len(hard[:2])))
            opts = ([target] if st == "MATCH" else []) + neg
            opts = opts[:k] if st == "MATCH" else (neg + rnd.sample([s for s in pool if s not in neg], 1))[:k]
            gold = target["id"] if st == "MATCH" else None
            if st == "OUT_OF_SCOPE":  # mind a négy jelleg kimenő tétel
                p["tenyek"] = {"tetel_jellege": rnd.choice(OOS[fam][lang]), "irany": IRANY[lang][1],
                               "osszeg": rnd.randint(18_000, 900_000) // 10 * 10 if lang == "hu" else rnd.randint(4_500, 900_000),
                               "datum": tx_date(rnd, [s["kelt"] for s in opts])}
            else:
                # MATCH és NO_MATCH: az összeg és a partner vagy a számlaszám közül legalább egy (a döntéshez kettő kell)
                azon = rnd.choice(["partner", "szamlaszam", "mindketto"])
                p["tenyek"] = {"osszeg": target["osszeg"], "irany": rnd.choice(IRANY[lang]),
                               "datum": tx_date(rnd, [target["kelt"]] + [s["kelt"] for s in opts])} | (
                    {"partner": target["partner"]} if azon in ("partner", "mindketto") else {}) | (
                    {"szamlaszam": target["szamlaszam"]} if azon in ("szamlaszam", "mindketto") else {})
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": s["id"], "text": f"{s['szamlaszam']} · {s['partner']} · {money(s['osszeg'], lang)} · "
                                                 f"{'esedékes' if lang == 'hu' else 'due'} {s['esedekes']}"} for s in opts]
        p["gold_sid"] = gold
        p["sajat_ceg"] = sab["ceg"]
    elif fam == "szabaly.koltsegelszamolas":
        pts = sab["pontok"]
        if st == "MISSING_DATA":
            t = rnd.choice(sorted({x["tipus"] for x in pts}))
            pair = [x for x in pts if x["tipus"] == t]
            rest = rnd.sample([x for x in pts if x["tipus"] != t], min(k - 2, 4))
            opts, gold = pair + rest, None
            p["tenyek"] = {"tipus": t, "tipus_leiras": SZAB_TIPUS[lang][t], "helyzet": rnd.choice(SZAB_HELYZET[lang][t])}
        elif st == "OUT_OF_SCOPE":
            opts, gold = rnd.sample(pts, min(k, len(pts))), None
            p["tenyek"] = {"kerelem_jellege": rnd.choice(OOS[fam][lang])}
        else:
            target = rnd.choice(pts)
            # a legnehezebb negatív elöl: ugyanaz a költségnem a másik értéksávban, utána az azonos sáv más nemei
            szomsz = sorted((x for x in pts if x is not target and (x["tipus"] == target["tipus"] or x["sav"] == target["sav"])),
                            key=lambda x: x["tipus"] != target["tipus"])
            rest = [x for x in pts if x is not target and x not in szomsz]
            neg = szomsz + rnd.sample(rest, max(0, min(k, len(pts)) - 1 - len(szomsz)))
            opts = ([target] + neg)[:k] if st == "MATCH" else neg[:k]
            gold = target["id"] if st == "MATCH" else None
            hatar = target["hatar"]
            osszeg = (rnd.randint(int(hatar * 0.2), int(hatar * 0.95)) if target["sav"] == 0 else
                      rnd.randint(int(hatar * 1.1), int(hatar * 3)))
            osszeg = osszeg // 10 * 10 if lang == "hu" else osszeg
            p["tenyek"] = {"tipus": target["tipus"], "tipus_leiras": SZAB_TIPUS[lang][target["tipus"]],
                           "helyzet": rnd.choice(SZAB_HELYZET[lang][target["tipus"]]), "osszeg": osszeg}
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": x["id"], "text": x["szoveg"]} for x in opts]
        p["gold_sid"] = gold
        p["szervezet"] = sab["szervezet"]
    elif fam == "muszaki.hibaelharitas":
        groups = sab["tunetcsoportok"]
        okok = [(gi, oi, o) for gi, g in enumerate(groups) for oi, o in enumerate(g["okok"])]
        sid = lambda gi, oi: f"c{gi}{oi}"  # noqa: E731
        p["berendezes"], p["modell"] = sab["berendezes"], sab["modell"]

        def olv(o, hibas: bool) -> dict:
            m = o["meres"]
            return {"nev": m["nev"], "ertek": fmt_num(m["ertek_ha_ez" if hibas else "ertek_normal"], lang), "egyseg": m["egyseg"]}
        if st == "OUT_OF_SCOPE":
            opts, gold = rnd.sample(okok, min(k, 8)), None
            p["tenyek"] = {"bejelentes_jellege": rnd.choice(OOS[fam][lang])}
        else:
            gi = rnd.randrange(4)
            a_, b_ = groups[gi]["okok"]
            others = [x for x in okok if x[0] != gi]
            # irreleváns mérés(ek) más tünetcsoport okaitól: a mérések száma ne árulja el az állapotot
            zaj = [olv(o, rnd.random() < 0.5) for _, _, o in rnd.sample(others, 2 if st == "MISSING_DATA" else 1)]
            zaj = zaj[:rnd.choice([1, 2])] if st == "MISSING_DATA" else zaj[:rnd.choice([0, 1])]
            ti = rnd.randrange(2)
            t, o = groups[gi]["okok"][ti], groups[gi]["okok"][1 - ti]
            if st == "MATCH":
                opts = [(gi, 0, a_), (gi, 1, b_)] + rnd.sample(others, k - 2)
                gold = sid(gi, ti)
                mer = [olv(t, True), olv(o, False)] + zaj
            elif st == "NO_MATCH":  # a valódi ok nincs a listán; a listán lévő párját a normál mérés kizárja
                opts = [(gi, 1 - ti, o)] + rnd.sample(others, k - 1)
                gold = None
                mer = [olv(t, True), olv(o, False)] + zaj
            else:  # MISSING_DATA: a két jelölt közül csak a hiányzó saját mérésük döntene
                opts = [(gi, 0, a_), (gi, 1, b_)] + rnd.sample(others, k - 2)
                gold = None
                mer = zaj
                p["tilos"] = {"meres": [a_["meres"]["nev"], b_["meres"]["nev"]],
                              "leolvasas": [(fmt_num(x["meres"][v], lang), x["meres"]["egyseg"]) for x in (a_, b_)
                                            for v in ("ertek_ha_ez", "ertek_normal")]}
            rnd.shuffle(mer)
            p["tenyek"] = {"tunet": groups[gi]["tunet"], "meresek": mer}
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": sid(g, i), "nev": o["nev"], "text": f"{o['nev']} — {hiba_szabaly(o, groups[g]['tunet'], lang)}"}
                       for g, i, o in opts]
        p["gold_sid"] = gold
    else:
        raise SystemExit(f"ismeretlen család: {fam}")
    return p


def cmd_terv(a) -> None:
    """A tervek. `--potlas K`: a K. pótlókör; a hiányos cellákra (az előző `final` összesítője szerint) a hiány kétszerese
    + 2 új terv, ugyanazzal a szabállyal, az indexet folytatva; a sorrendjük a korábbiak mögé kerül (3.4)."""
    fam = a.csalad
    sabs = jl_read(path("sablon", fam, a.proba))
    by = defaultdict(list)
    for s in sabs:
        by[(s["szelet"], s["lang"])].append(s)
    old = jl_read(path("terv", fam, a.proba)) if a.potlas else []
    if a.potlas:
        rep = json.loads(path("items", fam, False).with_suffix(".osszesito.json").read_text(encoding="utf-8"))
        kell = {tuple(k.split("|")): 2 * v + 2 for k, v in rep["hianyzo_cellak"].items()}
        have = Counter((r["szelet"], r["lang"], r["allapot"]) for r in old)
    else:
        kell, have = quotas(a.proba), Counter()
    rows = list(old)
    for (sz, lang, st), n in kell.items():
        pool = sorted(by[(sz, lang)], key=lambda s: h(f"{SEED}:kiosztas:{s['sablon_id']}:{st}"))
        for i in range(have[(sz, lang, st)], have[(sz, lang, st)] + n):
            sab = pool[i % len(pool)]
            gid = f"{fam}:{sz}:{lang}:{st}:{i:04d}"
            p = plan_case(fam, sab, st, i) | {"group_id": gid, "sorrend": a.potlas * 10**12 + h(f"{SEED}:sorrend:{gid}") % 10**12}
            rows.append(p)
    jl_write(path("terv", fam, a.proba), rows)
    print(f"{fam}: {len(rows)} terv; " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(r['allapot'] for r in rows).items())))


# --- generálás ----------------------------------------------------------------------------------------------------------

def gen_prompt(p: dict) -> str:
    """A generátor utasítása teljesen a cél nyelvén (a próbán a magyar utasítás angol nyelvsorral magyar szöveget adott)."""
    fam, lang, st, t, d = p["csalad"], p["lang"], p["allapot"], p["tenyek"], p["dim"]
    hu = lang == "hu"
    if fam == "penzugy.bankparositas":
        base = (f"Írj egy banki tételt {nevelo(p['sajat_ceg'])} {p['sajat_ceg']} cég bankszámlájáról. Forma: {d['forma']}. Irány: {t['irany']}. "
                f"Dátum: {t['datum']} (csak ezt az egy dátumot használd). Összeg: {money(t['osszeg'], lang)}." if hu else
                f"Write one bank transaction on the account of {p['sajat_ceg']}. Format: {d['forma']}. Direction: {t['irany']}. "
                f"Date: {t['datum']} (use only this one date). Amount: {money(t['osszeg'], lang)}.")
        if st == "OUT_OF_SCOPE":
            core = base + (f" A tétel jellege: {t['tetel_jellege']}. Számlára vagy számlaszámra ne utaljon." if hu else
                           f" The transaction is a {t['tetel_jellege']}. It must not refer to any invoice or invoice number.")
        elif st == "MISSING_DATA":
            core = base + (" A közlemény üres vagy semmitmondó (például „utalás”). A partner neve és számlaszám nem szerepelhet." if hu else
                           " The payment reference is empty or uninformative (e.g. \"transfer\"). No counterparty name and no invoice number.")
        else:
            add = ([(f"Partner: {t['partner']}." if hu else f"Counterparty: {t['partner']}.")] if "partner" in t else []) + (
                [(f"A közleményben a számlaszám: {t['szamlaszam']}." if hu else f"The payment reference contains the invoice number {t['szamlaszam']}.")]
                if "szamlaszam" in t else [])
            nincs = ([] if "partner" in t else [("a partner neve" if hu else "the counterparty name")]) + (
                [] if "szamlaszam" in t else [("számlaszám" if hu else "an invoice number")])
            core = base + " " + " ".join(add) + (" A tétel egy számla kiegyenlítése." if hu else " It settles an invoice.") + (
                (f" Nem szerepelhet: {', '.join(nincs)}." if hu else f" Do not include: {', '.join(nincs)}.") if nincs else "")
        if st != "OUT_OF_SCOPE":  # D22
            core += (" Más számlaszámot, hivatkozási számot vagy dátumot ne írj bele." if hu else
                     " Do not add any other invoice number, reference number or date.")
    elif fam == "szabaly.koltsegelszamolas":
        forma = d["forma"]
        if st == "OUT_OF_SCOPE" and forma in ("költségtérítési kérelem", "expense reimbursement form"):
            forma = "e-mail" if hu else "e-mail"  # a nem költség tárgyú üzenet nem lehet költségtérítési űrlap
        base = (f"Írj {forma} formájú, {d['regiszter']} hangvételű üzenetet {nevelo(p['szervezet'])} {p['szervezet']} egyik munkatársától." if hu else
                f"Write a {d['regiszter']} {forma} from an employee of {p['szervezet']}.")
        if st == "OUT_OF_SCOPE":
            core = base + (f" Az üzenet tárgya: {t['kerelem_jellege']}. Költség elszámolását ne kérje." if hu else
                           f" Topic: {t['kerelem_jellege']}. It must not ask for any expense reimbursement.")
        else:
            core = base + (f" Az üzenet költségelszámolási kérelem. A költség: {t['helyzet']}." if hu else
                           f" It is an expense claim. The expense: {t['helyzet']}.")
            if st == "MISSING_DATA":
                core += (" Az összeget és a költség nagyságát ne írd bele, semmilyen számmal." if hu else
                         " Do not state the amount or the size of the expense, in any form.")
            else:
                core += (f" Összeg: {money(t['osszeg'], lang)}." if hu else f" Amount: EUR {t['osszeg']:,}.")
            core += (" Szabálypontra, költségkategóriára vagy jóváhagyóra ne hivatkozz." if hu else
                     " Do not refer to policy clauses, expense categories or approvers.")
    else:
        base = (f"Írj a szervizhez beérkező, {d['forma']} formájú, {d['hossz']} üzenetet; a bejelentő a berendezés "
                f"felhasználói oldaláról ír ({d['bejelento']}). Berendezés: {p['modell']} típusú {p['berendezes']}." if hu else
                f"Write a {d['hossz']} {d['forma']} sent to the service desk by the device's user side ({d['bejelento']}). "
                f"Device: {p['berendezes']}, model {p['modell']}.")
        if st == "OUT_OF_SCOPE":
            core = base + (f" Az üzenet tárgya: {t['bejelentes_jellege']}. Hibát, rendellenességet vagy tünetet ne írj le." if hu else
                           f" Topic: {t['bejelentes_jellege']}. Do not describe any fault, malfunction or symptom.")
        else:
            core = base + (f" Tünet: {t['tunet']}." if hu else f" Symptom: {t['tunet']}.")
            if t["meresek"]:
                mer = "; ".join(f"{m['nev']}: {m['ertek']} {m['egyseg']}" for m in t["meresek"])
                core += (f" Pontosan ezek a mért értékek szerepeljenek, más mérés ne: {mer}." if hu else
                         f" Include exactly these measured values and no other measurement: {mer}.")
            else:
                core += (" Mérési eredményt, mért értéket vagy vizsgálatot ne írj bele." if hu else
                         " Do not include any measurement, measured value or test result.")
            core += (" A hiba okát ne nevezd meg, és ne találgass." if hu else " Do not name or guess the cause.")
    tail = (" A szöveg nyelve magyar. A cég nem személy: ne azt írd, hogy „… Kft. vagyok”, hanem hogy a cégtől ír (például "
            "„A Kristály Kft.-től írok”, „Az Ezüst Kft.-től írok”), vagy a munkatárs a saját nevével mutatkozik be. A névelő "
            "mindig „a” vagy „az”, soha nem „a(z)”. Ne írd le, mi a helyes döntés, ne értékeld a tételt, és a formát ne magyarázd. "
            'Csak ezt a JSON-t add vissza: {"szoveg": "..."}' if hu else
            " Write in English. Do not state the correct decision, do not evaluate the item, and do not explain the format. "
            'Return only this JSON: {"szoveg": "..."}')
    return core + tail


def amount_forms(osszeg: int, lang: str, cents: bool) -> set[str]:
    """Az összeg elválasztók nélküli alakjai a szövegben (EUR-nál centben, kerek összegnél egész euróban is)."""
    if lang == "hu" or not cents:
        return {str(osszeg)}
    return {str(osszeg)} | ({str(osszeg // 100)} if osszeg % 100 == 0 else set())


CURRENCY_NUM = re.compile(r"\d[\d\s]*\s*(ft\b|huf|forint|eur|euró|euro|€)|(€|eur)\s*\d")
# D22 (a 2. audit b136-ja, 2026-10-31): a banki szövegbe a generátor saját számlaszámot, hivatkozást vagy dátumot írt
# („Számla kiegyenlítés 2026/1845”, holott a terv szerint számlaszám nincs). A bankszámlaszám és a hosszú
# tranzakcióazonosító (≥ 8 jegy) természetes, ezek előbb kikerülnek; az OUT_OF_SCOPE saját hivatkozásai (SAL-…) maradhatnak.
BANK_KIVESZ = re.compile(r"\d{8}-\d{8}(?:-\d{8})?|\S*\d{8,}\S*")
BANK_DATUM = re.compile(r"(?<!\d)(\d{4})\s?[-./]\s?(\d{1,2})\s?[-./]\s?(\d{1,2})(?!\d)|(?<!\d)(\d{1,2})[./](\d{1,2})[./](\d{4})(?!\d)")
BANK_HONAP = re.compile(r"(?<![\d/-])20\d{2}/\d{2}(?![\d/])")
BANK_HIV = re.compile(r"(?<![\w/-])(?:[A-Za-z]{1,5}[-/ ]?)?\d{4}[/-]\d{3,5}(?![\d/-])"
                      r"|(?i:\b(?:sz[áa]mla(?:sz[áa]m)?|invoice|inv|ref|reference|hivatkoz[áa]s|bizonylat)\b\.?"
                      r"(?:\s*(?:sz\.|sz[áa]m|no\.?|nr\.?|#))?[\s:#.-]*)([A-Z]{0,5}-?\d{3,}[\w/-]*)")


def bank_idegen(p: dict, text: str) -> str | None:
    """D22: a tranzakció dátumán és a terv számlaszámán kívül nincs más dátum, hónap- vagy számlahivatkozás."""
    t = p["tenyek"]
    text = BANK_KIVESZ.sub(" ", text)
    for m in BANK_DATUM.finditer(text):
        y, mo, d = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(6), m.group(5), m.group(4))
        if f"{y}-{int(mo):02d}-{int(d):02d}" != t["datum"]:
            return "idegen dátum a szövegben"
    if BANK_HONAP.search(text):
        return "hónap-hivatkozás a szövegben"
    want = norm_ref(t.get("szamlaszam", ""))
    for m in BANK_HIV.finditer(text):
        n = norm_ref(m.group(1) or m.group(0))
        if not want or not (n == want or want.endswith(n) or n.endswith(want)):
            return "idegen számlaszám vagy hivatkozás a szövegben"
    return None


def fact_check(p: dict, text: str) -> str | None:
    """A döntő tények jelenléte, illetve MISSING_DATA-nál hiánya; None = rendben."""
    low, nd, nr = text.lower(), norm_digits(text), norm_ref(text)
    if not lang_ok(text, p["lang"]):
        return "rossz nyelv"
    if any(x in low for x in LEAK[p["lang"]]):
        return "címkét kimondó fordulat"
    if "a(z)" in low:
        return "„a(z)” a szövegben"
    fam, st, t = p["csalad"], p["allapot"], p["tenyek"]
    if fam == "penzugy.bankparositas":
        if not any(x in nd for x in amount_forms(t["osszeg"], p["lang"], cents=True)):
            return "hiányzó összeg"
        if t["datum"].replace("-", "") not in norm_date(text):
            return "hiányzó vagy eltérő dátum"
        if "partner" in t and t["partner"].split()[0].lower() not in low:
            return "hiányzó partner"
        if "szamlaszam" in t and norm_ref(t["szamlaszam"]) not in nr:
            return "hiányzó számlaszám"
        if st == "MISSING_DATA":
            if any(x.split()[0].lower() in low for x in p["tilos"]["partner"]):
                return "a hiányzónak szánt partner a szövegben"
            if any(norm_ref(x) in nr for x in p["tilos"]["szamlaszam"]):
                return "a hiányzónak szánt számlaszám a szövegben"
        if st in ("MATCH", "NO_MATCH") and "partner" not in t:
            others = [o["text"].split(" · ")[1].split()[0].lower() for o in p["opciok"]]
            if any(x in low for x in others):
                return "opció-partner a szövegben, holott a terv szerint nincs benne"
        if st != "OUT_OF_SCOPE" and (err := bank_idegen(p, text)):
            return err
    elif fam == "szabaly.koltsegelszamolas":
        if t.get("tipus_leiras") and t["tipus_leiras"].lower() in low:
            return "a költségnem leírása szó szerint"
        if st == "MISSING_DATA" and CURRENCY_NUM.search(nd.lower()):
            return "összeg a hiányzó összeg helyén"
        if st in ("MATCH", "NO_MATCH") and not any(x in nd for x in amount_forms(t["osszeg"], p["lang"], cents=False)):
            return "hiányzó összeg"
        for o in p["opciok"]:
            if re.search(rf"(?<![\d.]){re.escape(o['text'].split('.')[0] + '.' + o['text'].split('.')[1])}(?![\d])", text):
                return "szabálypont-hivatkozás a szövegben"
    else:
        if any(o["nev"].strip().lower() in low for o in p["opciok"]):
            return "ok megnevezve a szövegben"
        if st == "MISSING_DATA":
            tunet = t["tunet"].lower()
            if any(x.lower() in low for x in p["tilos"]["meres"] if x.lower() not in tunet):
                return "a hiányzónak szánt mérés a szövegben"
            if any(reading_present(text, v, u) for v, u in p["tilos"]["leolvasas"]):
                return "a hiányzónak szánt mért érték a szövegben"
        for m in t.get("meresek", []):
            if not value_present(text, m["ertek"]):
                return f"hiányzó mért érték: {m['nev']}"
    return None


def gen_one(p: dict, a, extra: dict) -> dict:
    out = {"group_id": p["group_id"], "terv": p, "probak": []}
    for k in range(3):
        try:
            obj = llm_json(a.url, a.model, p["lang"], gen_prompt(p), extra, h(f"gen:{p['group_id']}:{k}") % 10**6)
        except RuntimeError as e:
            out["probak"].append(str(e))
            continue
        txt = str(obj.get("szoveg") or "").strip()
        err = "üres szöveg" if not txt else fact_check(p, txt)
        if err is None:
            return out | {"szoveg": txt}
        out["probak"].append(err)
    return out | {"hiba": out["probak"][-1] if out["probak"] else "ismeretlen"}


def cmd_gen(a) -> None:
    fam = a.csalad
    out = path("raw", fam, a.proba)
    done = {r["group_id"] for r in jl_read(out)}
    todo = [p for p in jl_read(path("terv", fam, a.proba)) if p["group_id"] not in done]
    extra = json.loads(a.extra) if a.extra else {}
    print(f"{fam}: {len(done)} kész, {len(todo)} hátra", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(lambda p: gen_one(p, a, extra), todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


# --- itemek -------------------------------------------------------------------------------------------------------------

KERDES = {"penzugy.bankparositas": ("penzugy", {"hu": "Melyik nyitott számlát egyenlíti ki ez a tétel?",
                                               "en": "Which open invoice does this transaction settle?"}),
          "muszaki.hibaelharitas": ("muszaki", {"hu": "A diagnosztikai szabályok szerint melyik hibát igazolják a megadott adatok?",
                                                "en": "According to the diagnostic rules, which fault do the given data confirm?"}),
          "szabaly.koltsegelszamolas": ("szabaly", {"hu": "A szabályzat melyik pontja alá esik ez a tétel?",
                                                    "en": "Which policy clause does this item fall under?"})}


SZAMLATULAJDONOS = {"hu": "Számlatulajdonos: {}", "en": "Account holder: {}"}


def to_item(r: dict) -> dict:
    """A banki tétel elé rögzített első sor kerül a számlatulajdonossal (D19, Dani, 2026-10-30: a címkézetlen cégnévről
    nem dönthető el, hogy partner vagy számlatulajdonos; a055, a071, a098, a108, a120, a256)."""
    p = r["terv"]
    group, q = KERDES[p["csalad"]]
    state = r["szoveg"]
    if p["csalad"] == "penzugy.bankparositas":
        state = SZAMLATULAJDONOS[p["lang"]].format(p["sajat_ceg"]) + "\n\n" + state
    opts = [{"id": f"o{i + 1}", "text": o["text"]} for i, o in enumerate(p["opciok"])]
    gold = next((f"o{i + 1}" for i, o in enumerate(p["opciok"]) if o["sid"] == p["gold_sid"]), None)
    if (gold is None) != (p["allapot"] != "MATCH"):
        raise SystemExit(f"{p['group_id']}: a gold és az állapot ellentmond")
    return {"id": p["group_id"], "family": p["csalad"], "group": group, "source": "szint06", "source_license": "konstrukcio",
            "split": p["szelet"], "group_id": p["group_id"], "template_group_id": p["sablon_id"], "lang": p["lang"],
            "x_type": X_TYPE.get(p["allapot"]), "content_state": p["allapot"], "ketertelmu": False, "soft": None,
            "kind": "choice", "state": state, "question": q[p["lang"]], "options": opts, "gold": gold,
            "sorrend": p["sorrend"], "meta": {"dim": p["dim"]}}


def cmd_final(a) -> None:
    """A próbán minden túlélő marad. A teljes építésben cellánként (szelet × nyelv × állapot) a terv hash-sorrendjében
    az első N túlélő (N a kvóta; 3.4); modellkimenet a válogatásban nem szerepel. A hiányzó cellák az összesítőbe
    kerülnek (pótlás: új tervek ugyanazzal a szabállyal, reggel)."""
    fam = a.csalad
    raw = jl_read(path("raw", fam, a.proba))
    ok = [r for r in raw if "szoveg" in r]
    if a.proba:
        items = [to_item(r) for r in ok]
        cells = {}
    else:
        by = defaultdict(list)
        for r in ok:
            t = r["terv"]
            by[(t["szelet"], t["lang"], t["allapot"])].append(r)
        items, cells = [], {}
        for sz in SPLITS:
            for lang in LANGS:
                for st in STATES:
                    n = kvota(sz, lang, st)
                    surv = sorted(by[(sz, lang, st)], key=lambda r: r["terv"]["sorrend"])
                    items += [to_item(r) for r in surv[:n]]
                    planned = sum(1 for r in raw if (r["terv"]["szelet"], r["terv"]["lang"], r["terv"]["allapot"]) == (sz, lang, st))
                    cells[f"{sz}|{lang}|{st}"] = {"kvota": n, "terv": planned, "tulelo": len(surv), "kivalasztva": min(n, len(surv)),
                                                  "hiany": max(0, n - len(surv))}
    jl_write(path("items", fam, a.proba), items)
    lost = Counter(f"{r['terv']['allapot']}|{r.get('hiba')}" for r in raw if "szoveg" not in r)
    retry = Counter(f"{r['terv']['allapot']}|{e}" for r in raw for e in r["probak"])
    rep = {"csalad": fam, "terv": len(raw), "tulelo": len(ok), "item": len(items),
           "allapot": dict(Counter(it["content_state"] for it in items)), "szelet": dict(Counter(it["split"] for it in items)),
           "nyelv": dict(Counter(it["lang"] for it in items)), "elveszett": dict(lost), "ujrageneralas": dict(retry),
           "cellak": cells, "hianyzo_cellak": {k: v["hiany"] for k, v in cells.items() if v["hiany"]},
           "sablon": len({it["template_group_id"] for it in items})}
    out = path("items", fam, a.proba).with_suffix(".osszesito.json")
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{fam}: {len(items)} item / {len(raw)} terv ({len(ok)} túlélő); állapotonként {rep['allapot']}; "
          f"hiányzó cellák: {rep['hianyzo_cellak'] or 'nincs'}")
    for k, n in sorted(lost.items()):
        print(f"  elveszett: {k}: {n}")


NEVELO_RX = re.compile(r"\b([Aa])\(z\)(\s+)(\S)")


def cmd_nevelo(a) -> None:
    """D17 (Dani, 2026-10-30): a bank- és a szabálycsalád teljes építésében a promptpélda „a(z)” alakja a Muse szövegeibe
    szó szerint bekerült. Gépies javítás a következő szó kezdőhangja szerint („a” vagy „az”); a tények, az állapot és a
    válogatás nem változik. Az eredeti szöveg a `szoveg_eredeti` mezőben marad, a raw fájl előtte mentésre kerül; utána
    a `final` újra összeállítja az itemeket."""
    fam = a.csalad
    p = path("raw", fam, False)
    bak = p.with_name(f"{fam}.elotte-nevelo.jsonl")
    if not bak.exists():
        shutil.copy2(p, bak)
    raw = jl_read(p)
    n, bad = 0, []
    for r in raw:
        if "szoveg" not in r:
            continue
        txt = NEVELO_RX.sub(lambda m: nevelo(m.group(3), m.group(1) == "A") + m.group(2) + m.group(3), r["szoveg"])
        if txt == r["szoveg"]:
            continue
        r.setdefault("szoveg_eredeti", r["szoveg"])
        r["szoveg"], r["javitas"] = txt, "nevelo"
        n += 1
        if (err := fact_check(r["terv"], txt)) is not None:
            bad.append(f"{r['group_id']}: {err}")
    jl_write(p, raw)
    print(f"{fam}: {n} szöveg javítva; a javított szövegből {len(bad)} nem menne át a mai tényellenőrzésen")
    for b in bad:
        print(f"  {b}")


TERV_SZABAD = {"tipus_leiras", "kerelem_jellege"}  # a tényekből csak ezek változhatnak; a szövegbe a kerelem_jellege kerül


def cmd_ujraterv(a) -> None:
    """D18–D19: a `sablon` és a `terv` újrafuttatása után a raw rekordok az új tervet kapják. Megengedett eltérés: az
    opciók szövege és a `TERV_SZABAD` tények; minden más eltérésnél leáll. Ahol a szövegbe kerülő tény (a kérelem
    jellege) változott, vagy a meglévő szöveg a mai tényellenőrzésen nem megy át, a rekord kikerül, és a `gen`
    újragenerálja. A korábbi raw a `raw/<család>.elotte-ujraterv.jsonl`-ben."""
    fam = a.csalad
    plans = {p["group_id"]: p for p in jl_read(path("terv", fam, False))}
    p_raw = path("raw", fam, False)
    bak = p_raw.with_name(f"{fam}.elotte-ujraterv.jsonl")
    if not bak.exists():
        shutil.copy2(p_raw, bak)
    keep, ok = [], Counter()
    for r in jl_read(bak):
        old, new = r["terv"], plans[r["group_id"]]
        diff = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
        if diff - {"opciok", "tenyek"}:
            raise SystemExit(f"{r['group_id']}: váratlan eltérés a tervben: {sorted(diff)}")
        if [o["sid"] for o in old["opciok"]] != [o["sid"] for o in new["opciok"]]:
            raise SystemExit(f"{r['group_id']}: az opciók köre vagy sorrendje változott")
        td = {k for k in set(old["tenyek"]) | set(new["tenyek"]) if old["tenyek"].get(k) != new["tenyek"].get(k)}
        if td - TERV_SZABAD:
            raise SystemExit(f"{r['group_id']}: váratlan eltérés a tényekben: {sorted(td)}")
        if "kerelem_jellege" in td:
            ok["újragenerálás: a kérelem jellege változott"] += 1
            continue
        r = r | {"terv": new}
        if "szoveg" in r and (err := fact_check(new, r["szoveg"])) is not None:
            ok[f"újragenerálás: a meglévő szöveg most nem megy át ({err})"] += 1
            continue
        ok["marad" + (" (új opciószöveg)" if "opciok" in diff else "")] += 1
        keep.append(r)
    jl_write(p_raw, keep)
    print(f"{fam}: {len(keep)} rekord marad; " + "; ".join(f"{k}: {v}" for k, v in sorted(ok.items())))


def cmd_ellenoriz(a) -> None:
    """A hibaelhárítás programos, tervhez kötött ellenőrzése (D15, D16): a terv mérései és a sablon szabálytáblája
    szerint MATCH-nél pontosan a gold opció igazolódik, a többi állapotnál egyik sem; a szövegben és az opciókban nincs
    „a(z)”; a katalógus nevei nem programazonosító-szerűek. Hiba esetén nem nulla a kilépési kód."""
    fam = "muszaki.hibaelharitas"
    sab = {s["sablon_id"]: s for s in jl_read(path("sablon", fam, a.proba))}
    raw = {r["group_id"]: r for r in jl_read(path("raw", fam, a.proba))}
    items = jl_read(path("items", fam, a.proba))
    if not items:
        raise SystemExit(f"{fam}: nincs item")
    hibak, n = [], Counter()
    for it in items:
        p = raw[it["id"]]["terv"]
        groups = sab[p["sablon_id"]]["tunetcsoportok"]
        mer = {m["nev"]: _num(m["ertek"]) for m in p["tenyek"].get("meresek", [])}
        igaz = set()
        for o in p["opciok"]:
            gi, oi = int(o["sid"][1]), int(o["sid"][2])
            m = groups[gi]["okok"][oi]["meres"]
            v = mer.get(m["nev"])
            if groups[gi]["tunet"] == p["tenyek"].get("tunet") and v is not None and \
                    (v < _num(m["kuszob"]) if m["relacio"] == "<" else v > _num(m["kuszob"])):
                igaz.add(o["sid"])
        if igaz != ({p["gold_sid"]} if p["allapot"] == "MATCH" else set()):
            hibak.append(f"{it['id']}: a szabályok szerint igazolt {sorted(igaz)}, a terv szerint {p['gold_sid']}")
        if "(z)" in it["state"] or any("(z)" in o["text"] for o in it["options"]):
            hibak.append(f"{it['id']}: „a(z)” a szövegben vagy az opciókban")
        n[p["allapot"]] += 1
    for t, s_ in sab.items():
        for g in s_["tunetcsoportok"]:
            for o in g["okok"]:
                if any(AZONOSITO_RX.search(x) for x in (o["nev"], o["meres"]["nev"], g["tunet"])):
                    hibak.append(f"{t}: programazonosító-szerű név ({o['nev']} / {o['meres']['nev']})")
    print(f"{fam}{' (próba)' if a.proba else ''}: {len(items)} item ({dict(n)}), {len(sab)} sablon; "
          f"hiba: {len(hibak) or 'nincs'}")
    for x in hibak:
        print(f"  {x}")
    if hibak:
        sys.exit(1)


def audit_dir(kor: int) -> Path:
    return D / "audit" if kor == 1 else D / f"audit/kor{kor}"


def cmd_audit(a) -> None:
    """A címkeaudit mintája (D14): családonként 100 item, állapot × nyelv szerint rétegezve (cellánként 12 vagy 13), a
    három szeletből a terv hash-sorrendje szerint; a mintához sem a gold, sem a terv nem kerül (az az adjudikációhoz
    külön fájlban). `--kor K` (K ≥ 2): friss minta a `--csalad` családokra, a korábbi körök itemei nélkül."""
    rows, keys = [], []
    korabbi = {k["id"] for j in range(1, a.kor) for k in jl_read(audit_dir(j) / "kulcs.jsonl")}
    for fam in (a.csalad or list(KERDES)):
        items = [it for it in jl_read(path("items", fam, False)) if it["id"] not in korabbi]
        cells = [(lang, st) for lang in LANGS for st in STATES]
        per = {c: 12 + (i < 4) for i, c in enumerate(sorted(cells, key=lambda c: h(f"{SEED}:audit:{fam}:{c}")))}
        for (lang, st), n in per.items():
            pool = sorted((it for it in items if it["lang"] == lang and it["content_state"] == st),
                          key=lambda it: h(f"{SEED}:audit{'' if a.kor == 1 else a.kor}:{it['id']}"))
            for it in pool[:n]:
                rows.append({k: it[k] for k in ("id", "family", "lang", "kind", "state", "question", "options")})
                keys.append({"id": it["id"], "gold": it["gold"], "content_state": st, "split": it["split"]})
    order = sorted(range(len(rows)), key=lambda i: h(f"{SEED}:audit-sorrend:{rows[i]['id']}"))
    jl_write(audit_dir(a.kor) / "minta.jsonl", [rows[i] for i in order])
    jl_write(audit_dir(a.kor) / "kulcs.jsonl", [keys[i] for i in order])
    print(f"audit: {len(rows)} item ({dict(Counter(r['family'] for r in rows))})")


def cmd_lap(a) -> None:
    L = ["# 06 F2 — generálási próba (Dani átnézéséhez)", "",
         "Családonként 24 item: 4 állapot × 2 nyelv × 3. Minden itemnél: a szándékolt állapot és a helyes opció "
         "(a konstrukcióból), a terv tényei, a generált szöveg és az opciók. A szempontok (D13): természetes-e a magyar "
         "szöveg; nincs-e helykitöltő vagy címkét kimondó mondat; a konstrukció egyértelműen meghatározza-e az állapotot "
         "és a helyes opciót.", ""]
    for fam in KERDES:
        items = jl_read(path("items", fam, True))
        if not items:
            continue
        raw = {r["group_id"]: r for r in jl_read(path("raw", fam, True))}
        lost = Counter((r["terv"]["allapot"], r.get("hiba")) for r in raw.values() if "szoveg" not in r)
        retry = Counter(e for r in raw.values() for e in r["probak"])
        L += [f"## {fam}", "", f"**{len(items)} item / {len(raw)} terv.** Elveszett: " +
              ("; ".join(f"{st} — {e}: {n}" for (st, e), n in sorted(lost.items())) or "nincs") +
              ". Újragenerálás oka (minden próbálkozás): " + ("; ".join(f"{e}: {n}" for e, n in retry.most_common()) or "nincs") + ".", ""]
        for it in sorted(items, key=lambda x: (x["lang"], STATES.index(x["content_state"]), x["id"])):
            p = raw[it["id"]]["terv"]
            gold = next((o["text"] for o in it["options"] if o["id"] == it["gold"]), "— (egyik sem)")
            L += [f"### {it['id']}", "", f"- **Állapot:** {it['content_state']} · **helyes:** {gold}",
                  f"- **Tények (terv):** `{json.dumps(p['tenyek'], ensure_ascii=False)}`",
                  f"- **Forma:** {'; '.join(f'{k}: {v}' for k, v in p['dim'].items())}", "",
                  "> " + it["state"].replace("\n", "\n> "), "", f"**{it['question']}**", ""]
            L += [f"{i + 1}. {o['text']}" for i, o in enumerate(it["options"])] + [""]
    out = D / "proba/proba_lap.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("sablon", "terv", "gen", "final"):
        s = sub.add_parser(name)
        s.add_argument("--csalad", required=True, choices=list(KERDES))
        s.add_argument("--proba", action="store_true")
        if name == "terv":
            s.add_argument("--potlas", type=int, default=0, help="a pótlókör sorszáma (1, 2, …)")
        if name in ("sablon", "gen"):
            s.add_argument("--url")
            s.add_argument("--model")
            s.add_argument("--extra")
            s.add_argument("--workers", type=int, default=32)
    sub.add_parser("lap")
    au = sub.add_parser("audit")
    au.add_argument("--kor", type=int, default=1)
    au.add_argument("--csalad", nargs="*", choices=list(KERDES))
    sub.add_parser("ujraterv").add_argument("--csalad", required=True, choices=list(KERDES))
    sub.add_parser("nevelo").add_argument("--csalad", required=True, choices=list(KERDES))
    sub.add_parser("ellenoriz").add_argument("--proba", action="store_true")
    a = ap.parse_args()
    {"sablon": cmd_sablon, "terv": cmd_terv, "gen": cmd_gen, "final": cmd_final, "lap": cmd_lap, "audit": cmd_audit,
     "nevelo": cmd_nevelo, "ellenoriz": cmd_ellenoriz, "ujraterv": cmd_ujraterv}[a.cmd](a)


if __name__ == "__main__":
    main()
