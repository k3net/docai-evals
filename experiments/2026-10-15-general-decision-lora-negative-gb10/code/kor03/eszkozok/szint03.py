"""03-as kör — szintetikus családok: generálás, független visszacímkézés, összeállítás (03-runbook 3.5, F1; spec:
kor03/spec/szintetikus_csaladok.yaml).

A szándékolt címkét (és az X-et, az opció-részhalmazt, a szcenárió-dimenziókat) a terv adja, determinisztikusan; a
generátor csak a szöveget írja. Az ellenőrző egy másik modellcsalád, vakon: a közös generikus keretben (kozos03) az
opciók címkéire kiolvasott valószínűség. Csak az az item marad, ahol az ellenőrző top-1-e a szándékolt címke, legalább
0,6 bizalommal; az ellentényes pár csak akkor, ha mindkét tagja átmegy. Puha célt az ellenőrző nem ad (4.1).

  forras   (laptopon) a RAG- és a válaszbírálat-családok forrásbekezdései: Wikipédia-szócikkek és NJT-egységek,
           amelyeket más család nem használ → adat/f1/szint/forras_bekezdesek.jsonl
  gen      --csalad F --url U --model M [--extra JSON] [--n N] [--workers W]  → adat/f1/szint/raw/F.jsonl
  check    --csalad F --url U --model M --tag T [--extra JSON]              → adat/f1/szint/check/F.T.jsonl
  final    [--csalad F]                                                     → adat/f1/szint/F.jsonl + riport

Generátor és ellenőrző (spec): Mistral → Gemma, Gemma → Qwen, Qwen → Mistral. A levéltriage generátora a Mistral-
próba után Gemma lett (a Mistral NVFP4 a Sparkon ~225 token/s-ot ad 48 szekvenciával, és helykitöltőket írt).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
sys.path.insert(0, str(HERE))
sys.path.append(str(ROOT.parent / "eszkozok"))
from biralo import chat  # noqa: E402
from kozos03 import MAX_OPTIONS, messages, noul_options, validate  # noqa: E402
from common import labels_for  # noqa: E402

SPEC = yaml.safe_load((ROOT / "spec/szintetikus_csaladok.yaml").read_text(encoding="utf-8"))
D = ROOT / "adat/f1/szint"
SEED = "szint03:2026-10-09"
CJK = re.compile(r"[぀-ヿ㐀-鿿가-힯]")
EMAIL = re.compile(r"[\w.+-]+@([\w-]+\.)+[\w-]+")
URL = re.compile(r"https?://|www\.", re.I)
PLACEHOLDER = re.compile(r"\[[^\]\n]{2,40}\]")  # szögletes zárójeles helykitöltő ([Cégnév], [Név] …)
FIRST = ["Péter", "Anna", "Gábor", "Katalin", "Zoltán", "Eszter", "László", "Judit", "Tamás", "Réka", "Balázs",
         "Krisztina", "Attila", "Nóra", "Csaba", "Zsófia"]
MIN_CONF = SPEC["kozos"]["ellenorzo_min_bizalom"]
N_GEN = 1300  # családonként; a keverő kvótája 1000, a különbség az ellenőrzés vesztesége

GEN_SYSTEM = ("Magyar nyelvű szintetikus tanítóadatot írsz egy döntési modellhez. Csak a kért JSON-objektumot add "
              "vissza, magyarázat és kódblokk nélkül. Kitalált személy- és cégneveket használj, valós személyre ne "
              "utalj. E-mail-cím csak a pelda.example tartományban, telefonszám csak +36 1 555 xxxx alakban szerepelhet. "
              "Szögletes zárójeles helykitöltőt ([Cégnév], [Név] stb.) ne használj: mindenhová konkrét, kitalált adat kerüljön.")

# --- receptek --------------------------------------------------------------------------------------------------------

LEIRAS = {
    "level.triage": "beérkező üzleti levél (e-mail) egy magyar kis- vagy középvállalkozáshoz",
    "level.dokumentumtipus": "üzleti vagy hivatali dokumentum eleje (az első 1–3 bekezdés, fejléccel vagy anélkül)",
    "level.szerzodesklauzula": "egyetlen szerződési pont (1–4 mondat) egy magyar szerződésből",
    "jogi.hivatali_ugytipus": "hivatalnak (önkormányzatnak, kormányhivatalnak vagy adóhatóságnak) címzett beadvány",
}
X_KATEG = {
    "level.triage": ["álláspályázat", "magánjellegű, baráti üzenet", "automatikus távollét-értesítés",
                     "nyilvánvalóan más cégnek szóló, tévesen címzett levél"],
    "level.dokumentumtipus": ["regényrészlet", "főzőrecept", "menetrend", "termék használati útmutatója"],
    "level.szerzodesklauzula": ["a szerződő felek adatainak felsorolása", "aláírási blokk dátummal",
                                "a szerződés tárgyának műszaki leírása"],
    "jogi.hivatali_ugytipus": ["köszönőlevél egy rendezvényért", "kereskedelmi ajánlat", "magánlevél egy rokonnak"],
}
DIM = {
    "hossz": ["rövid (2–4 mondat)", "közepes (5–8 mondat)", "hosszabb (két-három bekezdés)"],
    "hangnem": ["hivatalos", "udvarias, köznapi", "tömör, kapkodó", "bőbeszédű", "ingerült", "néhány elírással"],
}
# típus → (rekordnév, „-ra/-re” alak a kérdésben és a promptban)
ENT_TIPUS = {"cég": ("cég", "cégre"), "személy": ("személy", "személyre"), "cím": ("postai cím", "címre")}
ENT_VALTOZAT = ["rövidítés vagy cégforma-eltérés", "ékezet hiánya", "szórend vagy névsorrend", "egy betűs elírás",
                "kiegészítő adat (pl. emelet, fióktelep) az egyikben", "régi és új név"]
ENT_NEGATIV = ["nagyon hasonló név, de más szereplő", "ugyanaz a név más településen", "ugyanaz az utca más házszámmal",
               "anyavállalat és leányvállalat"]
BIRALAT = ["helyes és teljes", "helyes, de hiányos", "a forrással ellentétes", "a forrásban nem szereplő állítást tesz",
           "nem válaszol a kérdésre"]


def h(s: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{s}".encode()).hexdigest(), 16)


def questions(fam: str) -> list[dict]:
    return SPEC["csaladok"][fam]["kerdesek"]


def x_share(fam: str) -> float:
    return sum((SPEC["csaladok"][fam].get("x") or {}).values())


def source_paragraphs() -> list[dict]:
    p = D / "forras_bekezdesek.jsonl"
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()] if p.exists() else []


def plan(fam: str, seq: int, src: list[dict]) -> dict:
    """A seq-edik item terve: kérdés, szándékolt címke, opciók, X, dimenziók, ellentényes-e."""
    rnd = random.Random(f"{SEED}:{fam}:{seq}")
    qs = questions(fam)
    qi = rnd.randrange(len(qs))
    q = qs[qi]
    p = {"fam": fam, "seq": seq, "qi": qi, "kind": q["kind"], "kerdes": q["kerdes"],
         "dim": {k: rnd.choice(v) for k, v in DIM.items()}, "cf": rnd.random() < SPEC["kozos"]["ellenteny_arany"]}
    allow_x = q["kind"] == "choice" and not (fam == "level.triage" and qi == 1)
    p["x"] = allow_x and rnd.random() < x_share(fam) / max(1e-9, sum(1 for x in qs if x["kind"] == "choice") / len(qs))
    if fam in LEIRAS:
        if q["kind"] == "choice":
            full = list(q["opciok"])
            k = rnd.randint(2, min(MAX_OPTIONS, len(full)))
            if p["x"]:
                p |= {"opciok": rnd.sample(full, k), "cel": None, "x_type": "out-of-scope", "x_kat": rnd.choice(X_KATEG[fam])}
            else:
                cel = full[seq % len(full)]  # kiegyensúlyozott címkék
                rest = [o for o in full if o != cel]
                opts = rnd.sample(rest, k - 1) + [cel]
                rnd.shuffle(opts)
                p |= {"opciok": opts, "cel": cel}
        else:
            p |= {"opciok": ["igen", "nem"], "cel": "igen" if seq % 2 == 0 else "nem"}
        p["recept"] = "osztaly"
        # konkrét, kitalált szereplők: a generátor különben helykitöltőket ír ([Cégnév]); a kie03 szólistáiból
        from kie03 import SURNAMES, company  # noqa: PLC0415
        p["szereplok"] = {"felado": f"{rnd.choice(SURNAMES)} {rnd.choice(FIRST)}", "felado_ceg": company(rnd),
                          "cimzett_ceg": company(rnd)}
    elif fam == "entitas.egyezes":
        from kie03 import CITIES, STREETS, SURNAMES, company  # noqa: PLC0415
        city, pc = rnd.choice(CITIES)
        # konkrét, változatos alapszereplő: anélkül a generátor szinte mindig „Kovács László”-t írt
        p["alap"] = {"szemely": f"{rnd.choice(SURNAMES)} {rnd.choice(FIRST)}", "ceg": company(rnd),
                     "cim": f"{pc} {city}, {rnd.choice(STREETS)} {rnd.randint(1, 120)}.",
                     "telefon": f"+36 1 555 {rnd.randint(1000, 9999)}"}
        p["tipus"] = rnd.choice(list(ENT_TIPUS))
        p["valtozat"], p["negativ"] = rnd.choice(ENT_VALTOZAT), rnd.choice(ENT_NEGATIV)
        if q["kind"] == "noul":
            p |= {"recept": "egyezes_par", "kerdes": q["kerdes"].replace("{tipusra}", ENT_TIPUS[p["tipus"]][1]),
                  "opciok": ["igen", "nem"], "cel": "igen" if seq % 2 == 0 else "nem"}
        else:
            n = rnd.randint(2, 6)
            p |= {"recept": "egyezes_lista", "n_jelolt": n, "cel": None if p["x"] else rnd.randrange(n),
                  "x_type": "gold-drop" if p["x"] else None}
    elif fam == "rag.relevancia":
        multi = [s for s in src if s["tipus"] == "szocikk"]
        single = [s for s in src if s["tipus"] == "bekezdes"]
        if q["kind"] == "choice":
            s = multi[h(f"{fam}:{seq}") % len(multi)]
            n = rnd.randint(2, min(6, len(s["bekezdesek"])))
            idx = sorted(rnd.sample(range(len(s["bekezdesek"])), n))
            p |= {"recept": "rag_valasztas", "forras_id": s["id"], "bekezdesek": [s["bekezdesek"][i] for i in idx],
                  "cel": None if p["x"] else rnd.randrange(n), "x_type": "natural" if p["x"] else None}
        else:
            s = single[h(f"{fam}:{seq}") % len(single)]
            p |= {"recept": "rag_alatamasztas", "forras_id": s["id"], "bekezdes": s["szoveg"], "opciok": ["igen", "nem"],
                  "cel": "igen" if seq % 2 == 0 else "nem", "nem_mod": rnd.choice(["ellentmond", "nem szerepel"])}
    elif fam == "rag.valaszbiralat":
        single = [s for s in src if s["tipus"] == "bekezdes"]
        s = single[h(f"{fam}:{seq}") % len(single)]
        cel = BIRALAT[seq % len(BIRALAT)]
        rest = [b for b in BIRALAT if b != cel]
        opts = rnd.sample(rest, rnd.randint(1, len(rest))) + [cel]
        rnd.shuffle(opts)
        p |= {"recept": "valaszbiralat", "forras_id": s["id"], "bekezdes": s["szoveg"], "opciok": opts, "cel": cel,
              "x": False}
    else:
        raise SystemExit(f"ismeretlen család: {fam}")
    if seq >= MP_START and fam in MP_CSALADOK:
        p = mp_plan(p, fam, seq)
    return p


# „Hiányzó feltétel” X (runbook 2. pont, 4. típus): az opció illene, de az állapotból hiányzik a döntéshez szükséges
# adat. A 2026-10-10 előtti tervezőből kimaradt (minden X out-of-scope lett); a pótlás a seq ≥ MP_START terveken fut,
# saját véletlenforrással, így a korábbi tervek bájtra változatlanok.
MP_START = 1300
MP_CSALADOK = [f for f, c in SPEC["csaladok"].items() if (c.get("x") or {}).get("missing-precondition")]


def mp_plan(p: dict, fam: str, seq: int) -> dict:
    rnd = random.Random(f"{SEED}:{fam}:{seq}:mp")
    qs = questions(fam)
    choice = [i for i, q in enumerate(qs) if q["kind"] == "choice" and not (fam == "level.triage" and i == 1)]
    qi = rnd.choice(choice)
    full = list(qs[qi]["opciok"])
    opts = rnd.sample(full, rnd.randint(3, min(MAX_OPTIONS, len(full))))
    base = {k: v for k, v in p.items() if k != "x_kat"}
    return base | {"qi": qi, "kind": "choice", "kerdes": qs[qi]["kerdes"], "x": True, "cf": False, "opciok": opts,
                   "cel": None, "x_type": "missing-precondition", "mp_jeloltek": rnd.sample(opts, 2)}


def prompt(p: dict) -> str:
    dim = f"Terjedelem: {p['dim']['hossz']}; hangnem: {p['dim']['hangnem']}."
    r = p["recept"]
    if r == "osztaly":
        what = LEIRAS[p["fam"]]
        sz = p["szereplok"]
        dim += (f" Szereplők, ezeket használd: {sz['felado']} ({sz['felado_ceg']}) és a(z) {sz['cimzett_ceg']}; "
                "helykitöltőt ([Név], [Cégnév]) ne írj.")
        if p["kind"] == "noul":
            return (f"Írj egy {what} szöveget. {dim} A szöveg alapján erre a kérdésre egyértelműen „{p['cel']}” a "
                    f"helyes válasz: „{p['kerdes']}” A szöveg maga a levél vagy dokumentum legyen: ne kezdődjön "
                    f"igennel vagy nemmel, ne válaszoljon a kérdésre, és ne ismételje meg. A kérdezett tulajdonságot "
                    f"ne mondja ki és ne tagadja kifejezetten (pl. „nem keletkeztet egyoldalú jogot”, „ez nem jelent "
                    f"…”): a válasz a rendelkezés tartalmából következzen. Magyarázatot ne írj. "
                    'Válasz: {"szoveg": "..."}')
        if p.get("x_type") == "missing-precondition":
            a, b = p["mp_jeloltek"]
            return (f"Írj egy {what} szöveget. {dim} A szöveg alapján ne legyen eldönthető, hogy ezek közül melyik "
                    f"kategóriába tartozik: {', '.join(p['opciok'])}. Lehetne például „{a}” vagy „{b}” is, de a "
                    f"döntéshez szükséges adat hiányozzon: a lényeget a szöveg csak utalással közli (pl. egy csatolmányra, "
                    f"egy korábbi egyeztetésre vagy egy meg nem nevezett ügyre hivatkozik). Ettől még természetes, "
                    f"valószerű szöveg legyen, és ne mondja ki, hogy hiányos. A kategóriák nevét szó szerint ne használd, "
                    'és ne írj magyarázatot. Válasz: {"szoveg": "..."}')
        if p["cel"] is None:
            return (f"Írj egy szöveget, amely formájában {what}, de valójában ez: {p['x_kat']}. {dim} Egyik következő "
                    f"kategóriába se tartozzon: {', '.join(p['opciok'])}. Magyarázatot ne írj. "
                    'Válasz: {"szoveg": "..."}')
        return (f"Írj egy {what} szöveget. {dim} A szöveg egyértelműen ebbe a kategóriába tartozzon: „{p['cel']}”, és "
                f"ne ezekbe: {', '.join(o for o in p['opciok'] if o != p['cel'])}. A kategória nevét („{p['cel']}”) "
                'szó szerint ne használd, és ne írj magyarázatot. Válasz: {"szoveg": "..."}')
    if r == "egyezes_par":
        how = (f"ugyanarra a {ENT_TIPUS[p['tipus']][1]} vonatkoznak, eltérés: {p['valtozat']}" if p["cel"] == "igen"
               else f"nem ugyanarra a {ENT_TIPUS[p['tipus']][1]} vonatkoznak (két különböző {ENT_TIPUS[p['tipus']][0]}), "
                    f"nehéz eset: {p['negativ']}")
        return (f"Írj két rövid nyilvántartási rekordot (egy-egy szöveges sor, névvel és néhány azonosító adattal), "
                f"amelyek {how}. {ent_alap(p)} Magyarázatot ne írj. Válasz: {{\"rekord1\": \"...\", \"rekord2\": \"...\"}}")
    if r == "egyezes_lista":
        cel = ("egyik jelölt sem azonos a keresettel (mind nehéz negatív: "
               f"{p['negativ']})" if p["cel"] is None else
               f"pontosan a(z) {p['cel'] + 1}. jelölt azonos a keresettel (eltérés: {p['valtozat']}), a többi nehéz "
               f"negatív ({p['negativ']})")
        return (f"Írj egy keresett {ENT_TIPUS[p['tipus']][0]}-rekordot és {p['n_jelolt']} jelölt rekordot (egy-egy szöveges "
                f"sor, névvel és néhány azonosító adattal), úgy, hogy {cel}. {ent_alap(p)} Magyarázatot ne írj. "
                f'Válasz: {{"keresett": "...", "jeloltek": [{p["n_jelolt"]} szöveg]}}')
    if r == "rag_valasztas":
        parts = "\n".join(f"{i + 1}. részlet: {b}" for i, b in enumerate(p["bekezdesek"]))
        cel = ("olyan, a részletek témájához illő kérdést, amelyre egyik részlet sem ad választ" if p["cel"] is None
               else f"olyan kérdést, amelyre csak a(z) {p['cel'] + 1}. részlet ad választ, a többi nem")
        return (f"Az alábbi részletekhez írj {cel}. A kérdés ne idézzen szó szerint a részletekből. Magyarázatot ne írj.\n\n"
                f'{parts}\n\nVálasz: {{"kerdes": "..."}}')
    if r == "rag_alatamasztas":
        cel = ("a részlet alátámasztja (következik belőle)" if p["cel"] == "igen" else
               "a részlet ellentmond neki" if p["nem_mod"] == "ellentmond" else
               "a részlet témájához illik, de a részlet nem mond róla semmit")
        return (f"Az alábbi részlethez írj egyetlen állítást, amelyet {cel}. Ne másold szó szerint a részletet. "
                f'Magyarázatot ne írj.\n\nRészlet: {p["bekezdes"]}\n\nVálasz: {{"allitas": "..."}}')
    if r == "valaszbiralat":
        return (f"Az alábbi forrásrészlethez írj egy kérdést, amelyre a részlet választ ad, és egy választ, amely a "
                f"forráshoz képest ilyen: „{p['cel']}”. A válasz ne jelezze, hogy hibás vagy hiányos. Magyarázatot ne "
                f'írj.\n\nForrás: {p["bekezdes"]}\n\nVálasz: {{"kerdes": "...", "valasz": "..."}}')
    raise ValueError(r)


def ent_alap(p: dict) -> str:
    a = p["alap"]
    return (f"Ebből az alapszereplőből indulj ki: {a['szemely']}, {a['ceg']}, {a['cim']}, {a['telefon']}; a többi "
            "rekordhoz találj ki hasonló, de saját neveket és adatokat. Minden rekord egyetlen szöveges sor legyen, ne "
            "JSON-objektum.")


def rec2str(x) -> str:
    """A rekord szöveges sorként; ha a generátor mégis objektumot adott, „kulcs: érték” párokként."""
    if isinstance(x, dict):
        return "; ".join(f"{str(k).replace('_', ' ')}: {v}" for k, v in x.items())
    return str(x)


def cf_prompt(p: dict, text: dict, c2: str) -> str:
    if p["recept"] == "osztaly":
        return (f"Az alábbi szövegről ezt a kérdést teszik fel: „{p['kerdes']}” Most a helyes válasz nem „{c2}”. Írd át "
                f"a szöveget a lehető legkisebb módosítással (egy-két szó, legfeljebb egy mondat), hogy a helyes válasz "
                f"„{c2}” legyen. A kérdést és a választ ne írd bele a szövegbe: csak a teljes, módosított szöveget add "
                f'vissza, minden mást változatlanul.\n\nSzöveg: {text["szoveg"]}\n\nVálasz: {{"szoveg": "..."}}')
    if p["recept"] == "egyezes_par":
        return (f"Módosítsd a második rekordot a lehető legkisebb mértékben (egy adat), úgy, hogy a két rekord "
                f"{'ugyanarra' if c2 == 'igen' else 'két különböző szereplőre'} vonatkozzon. Magyarázatot ne írj.\n\n"
                f'1. rekord: {text["rekord1"]}\n2. rekord: {text["rekord2"]}\n\n'
                'Válasz: {"rekord1": "...", "rekord2": "..."}')
    if p["recept"] == "rag_alatamasztas":
        return (f"Módosítsd az állítást a lehető legkisebb mértékben (egy-két szó), úgy, hogy a részlet "
                f"{'alátámassza' if c2 == 'igen' else 'ellentmondjon neki'}. Magyarázatot ne írj.\n\n"
                f'Részlet: {p["bekezdes"]}\nÁllítás: {text["allitas"]}\n\nVálasz: {{"allitas": "..."}}')
    return ""


def cf_ok(p: dict, obj: dict, cobj: dict) -> bool:
    """Az ellentényes változat valódi, kis módosítás-e: nem azonos, nem tartalmazza a kérdést, és a hossza az eredeti
    70–130%-a (különben a generátor nem átírt, hanem mást adott vissza)."""
    a, b = json.dumps(obj, ensure_ascii=False), json.dumps(cobj, ensure_ascii=False)
    if a == b or p["kerdes"].rstrip("?").lower() in b.lower():
        return False
    return 0.7 <= len(b) / max(1, len(a)) <= 1.3


def counter_label(p: dict) -> str | None:
    if not p["cf"] or p.get("cel") is None or p["recept"] not in ("osztaly", "egyezes_par", "rag_alatamasztas"):
        return None
    if p["kind"] == "noul" or p["recept"] in ("egyezes_par", "rag_alatamasztas"):
        return "nem" if p["cel"] == "igen" else "igen"
    others = [o for o in p["opciok"] if o != p["cel"]]
    return others[h(f"cf:{p['fam']}:{p['seq']}") % len(others)]


# --- LLM-hívás -------------------------------------------------------------------------------------------------------

def llm_json(url: str, model: str, user: str, extra: dict, seed: int, need: tuple[str, ...], tries: int = 4) -> dict:
    last = None
    for k in range(tries):
        try:
            r = chat(url, model, [{"role": "system", "content": GEN_SYSTEM}, {"role": "user", "content": user}],
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
            obj = json.loads(txt[s:e + 1], strict=False)  # a szövegmezőben nyers sortörés is lehet
        except Exception:  # noqa: BLE001
            last = "JSON"
            continue
        if not all(obj.get(k2) for k2 in need):
            last = "hiányos JSON"
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


NEED = {"osztaly": ("szoveg",), "egyezes_par": ("rekord1", "rekord2"), "egyezes_lista": ("keresett", "jeloltek"),
        "rag_valasztas": ("kerdes",), "rag_alatamasztas": ("allitas",), "valaszbiralat": ("kerdes", "valasz")}


def label_leak(p: dict, obj: dict) -> bool:
    """A kategória neve szó szerint a szövegben, vagy az igen/nem válasz a szöveg elején: shortcut lenne, újra."""
    if p["recept"] != "osztaly":
        return False
    if p["kind"] == "noul":
        return obj["szoveg"].lstrip(" „\"'").lower().startswith(("igen", "nem"))
    return bool(p.get("cel") and p["cel"].lower() in obj["szoveg"].lower())


def gen_one(p: dict, a) -> dict:
    extra = json.loads(a.extra) if a.extra else {}
    out = {"seq": p["seq"], "plan": p}
    try:
        for k in range(3):
            obj = llm_json(a.url, a.model, prompt(p), extra, h(f"gen:{p['fam']}:{p['seq']}:{k}") % 10**6, NEED[p["recept"]])
            if p["recept"] == "egyezes_lista" and len(obj["jeloltek"]) != p["n_jelolt"]:
                continue
            if not label_leak(p, obj):
                break
        else:
            return out | {"hiba": "címkeszivárgás vagy jelöltszám"}
        out["szoveg"] = obj
        c2 = counter_label(p)
        if c2:
            cobj = llm_json(a.url, a.model, cf_prompt(p, obj, c2), extra, h(f"cf:{p['fam']}:{p['seq']}") % 10**6,
                            NEED[p["recept"]])
            if cf_ok(p, obj, cobj):
                out["cf"] = {"cel": c2, "szoveg": cobj}
            else:
                out["cf_elvetve"] = True
    except RuntimeError as e:
        out["hiba"] = str(e)
    return out


def cmd_gen(a) -> None:
    (D / "raw").mkdir(parents=True, exist_ok=True)
    path = D / "raw" / f"{a.csalad}.jsonl"
    done = {json.loads(line)["seq"] for line in path.read_text(encoding="utf-8").splitlines()} if path.exists() else set()
    src = source_paragraphs()
    todo = [plan(a.csalad, i, src) for i in range(a.n) if i not in done]
    print(f"{a.csalad}: {len(done)} kész, {len(todo)} hátra", flush=True)
    with open(path, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(lambda p: gen_one(p, a), todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


# --- itemmé alakítás --------------------------------------------------------------------------------------------------

def to_item(p: dict, obj: dict, cel, cf: bool) -> dict:
    fam, seq, r = p["fam"], p["seq"], p["recept"]
    gid = f"{fam}:{seq:05d}"
    v = h(f"split:{gid}") % 100
    base = {"id": gid + (":cf" if cf else ""), "family": fam, "group": fam.split(".")[0], "source": "szint03",
            "source_license": "konstrukcio", "source_ref": f"{seq}{':cf' if cf else ''}",
            "split": "val" if v < 10 else "test-id" if v < 20 else "train", "group_id": gid, "lang": "hu",
            "x_type": None, "ketertelmu": False, "soft": None,
            "meta": {"recept": r, "kerdes_index": p["qi"], "ellenteny": cf} | ({"forras_id": p["forras_id"]} if "forras_id" in p else {})}
    if r in ("osztaly", "egyezes_par", "rag_alatamasztas", "valaszbiralat") and p["kind"] == "noul":
        state = {"osztaly": lambda: obj["szoveg"],
                 "egyezes_par": lambda: f"1. rekord: {rec2str(obj['rekord1'])}\n2. rekord: {rec2str(obj['rekord2'])}",
                 "rag_alatamasztas": lambda: f"Részlet: {p['bekezdes']}\nÁllítás: {obj['allitas']}"}[r]()
        return base | {"kind": "noul", "state": state, "question": p["kerdes"], "options": noul_options("hu"), "gold": cel}
    if r == "osztaly":
        opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(p["opciok"])]
        gold = next((o["id"] for o in opts if o["text"] == cel), None)
        return base | {"kind": "choice", "state": obj["szoveg"], "question": p["kerdes"], "options": opts, "gold": gold,
                       "x_type": p.get("x_type") if gold is None else None}
    if r == "egyezes_lista":
        opts = [{"id": f"o{i + 1}", "text": rec2str(t)} for i, t in enumerate(obj["jeloltek"])]
        return base | {"kind": "choice", "state": f"Keresett: {rec2str(obj['keresett'])}", "question": p["kerdes"], "options": opts,
                       "gold": None if cel is None else f"o{cel + 1}", "x_type": p.get("x_type") if cel is None else None}
    if r == "rag_valasztas":
        opts = [{"id": f"o{i + 1}", "text": b} for i, b in enumerate(p["bekezdesek"])]
        return base | {"kind": "choice", "state": f"Kérdés: {obj['kerdes']}", "question": p["kerdes"], "options": opts,
                       "gold": None if cel is None else f"o{cel + 1}", "x_type": p.get("x_type") if cel is None else None}
    if r == "valaszbiralat":
        opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(p["opciok"])]
        return base | {"kind": "choice", "state": f"Forrás: {p['bekezdes']}\nKérdés: {obj['kerdes']}\nVálasz: {obj['valasz']}",
                       "question": p["kerdes"], "options": opts, "gold": next(o["id"] for o in opts if o["text"] == cel)}
    raise ValueError(r)


def generated_items(fam: str) -> list[dict]:
    out = []
    for line in (D / "raw" / f"{fam}.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if "szoveg" not in r:
            continue
        p = r["plan"]
        out.append(to_item(p, r["szoveg"], p.get("cel"), False))
        if "cf" in r:
            out.append(to_item(p, r["cf"]["szoveg"], r["cf"]["cel"], True))
    return out


# --- ellenőrzés -------------------------------------------------------------------------------------------------------

def readout(it: dict, a) -> dict:
    extra = json.loads(a.extra) if a.extra else {}
    order = [o["id"] for o in it["options"]] + [None]
    labs = labels_for(order)
    r = chat(a.url, a.model, messages(it, order, "generic"),
             {"max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20, **extra}, None, timeout=600)
    mass = {}
    for t in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
        tok = t["token"].strip()
        if tok in labs:
            mass[tok] = mass.get(tok, 0.0) + math.exp(t["logprob"])
    s = sum(mass.values())
    probs = {oid: mass.get(lab, 0.0) / s if s else 0.0 for oid, lab in zip(order, labs)}
    return {"id": it["id"], "probs": {str(k): v for k, v in probs.items()}, "tomeg": s}


def cmd_check(a) -> None:
    (D / "check").mkdir(parents=True, exist_ok=True)
    path = D / "check" / f"{a.csalad}.{a.tag}.jsonl"
    done = {json.loads(line)["id"] for line in path.read_text(encoding="utf-8").splitlines()} if path.exists() else set()
    todo = [it for it in generated_items(a.csalad) if it["id"] not in done]
    print(f"{a.csalad}/{a.tag}: {len(done)} kész, {len(todo)} hátra", flush=True)
    with open(path, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(lambda it: readout(it, a), todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 200 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


def cmd_check_export(a) -> None:
    """Az ids-módú ellenőrzés (kiolvaso03, pl. a Muse kényszerített válaszcsatornával) bemenete: a család itemjei."""
    (D / "check_items").mkdir(parents=True, exist_ok=True)
    items = generated_items(a.csalad)
    (D / "check_items" / f"{a.csalad}.jsonl").write_text(
        "".join(json.dumps(it, ensure_ascii=False) + "\n" for it in items), encoding="utf-8")
    print(f"{a.csalad}: {len(items)} item exportálva")


def cmd_check_import(a) -> None:
    """A kiolvaso03 0-s permutációs kimenete ellenőrző-formátumba (`check_<tag>/F.<tag>.jsonl`): a címkék helyett
    opció-id-k, a tömeg a címkék valószínűség-összege. A `check/`-be csak a döntés után kerül át."""
    rows = [json.loads(line) for line in Path(a.src).read_text(encoding="utf-8").splitlines()]
    out = D / f"check_{a.tag}"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(out / f"{a.csalad}.{a.tag}.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            if r["perm"] != 0:
                continue
            probs = {str(oid): r["probs"][lab] for oid, lab in zip(r["order"], r["labels"])}
            fh.write(json.dumps({"id": r["id"], "probs": probs, "tomeg": r["label_mass"]}, ensure_ascii=False) + "\n")
            n += 1
    print(f"{a.csalad}: {n} ellenőrző-sor → {out}")


def cmd_final(a) -> None:
    rep = {}
    fams = [a.csalad] if a.csalad else list(SPEC["csaladok"])
    for fam in fams:
        checks = list((D / "check").glob(f"{fam}.*.jsonl"))
        if not (D / "raw" / f"{fam}.jsonl").exists() or not checks:
            rep[fam] = "hiányzik"
            continue
        if len(checks) > 1:  # pontosan egy ellenőrző lehet; egy régi kiolvasás nem keveredhet be
            raise SystemExit(f"{fam}: több ellenőrző-fájl: {[c.name for c in checks]}")
        ck = {json.loads(line)["id"]: json.loads(line) for line in checks[0].read_text(encoding="utf-8").splitlines()}
        items = generated_items(fam)
        ok, why = {}, Counter()
        for it in items:
            c = ck.get(it["id"])
            if not c or c["tomeg"] < 0.5:
                why["nincs vagy gyenge kiolvasás"] += 1
                continue
            top = max(c["probs"], key=lambda k: c["probs"][k])
            want = str(it["gold"])
            if top != want:
                why["az ellenőrző mást választ"] += 1
                continue
            if c["probs"][top] < MIN_CONF:
                why["az ellenőrző bizonytalan"] += 1
                continue
            ok[it["id"]] = it
        keep = []
        for it in ok.values():  # az ellentényes változat csak az eredetivel együtt marad; az eredeti egyedül is
            if it["meta"]["ellenteny"] and it["group_id"] not in ok:
                why["a pár eredeti tagja kiesett"] += 1
                continue
            keep.append(it)
        bad = [(i["id"], e) for i in keep if (e := validate(i))]
        if bad:
            raise SystemExit(f"{fam}: {len(bad)} sémahiba, pl. {bad[:3]}")
        (D / f"{fam}.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in keep), encoding="utf-8")
        raw = [json.loads(line) for line in (D / "raw" / f"{fam}.jsonl").read_text(encoding="utf-8").splitlines()]
        rep[fam] = {"terv": len(raw), "generalasi_hiba": sum("hiba" in r for r in raw), "item": len(items),
                    "megtartva": len(keep), "kiesett": dict(why), "ellenorzo": checks[0].name,
                    "x": sum(i["gold"] is None for i in keep), "split": dict(Counter(i["split"] for i in keep))}
        print(fam, json.dumps(rep[fam], ensure_ascii=False))
    old = json.loads((D / "szint_riport.json").read_text()) if (D / "szint_riport.json").exists() else {}
    (D / "szint_riport.json").write_text(json.dumps(old | rep, ensure_ascii=False, indent=1), encoding="utf-8")


# --- forrásbekezdések (laptopon) ---------------------------------------------------------------------------------------

def cmd_forras(a) -> None:
    import glob

    import pyarrow.parquet as pq

    sys.path.insert(0, str(HERE))
    from adapter_wiki import sections  # noqa: E402

    f0 = ROOT / "adat/f0"
    used_titles = {json.loads(line)["meta"]["wiki_cim"] for fam in ("konstrukcios.wiki_szakaszcim", "konstrukcios.wiki_folytatas")
                   for line in (f0 / f"{fam}.jsonl").read_text(encoding="utf-8").splitlines()}
    used_titles |= {json.loads(line)["meta"]["milqa_cim"] for line in (f0 / "qa.milqa.jsonl").read_text(encoding="utf-8").splitlines()}
    arts = [r for f in sorted(glob.glob(str(ROOT / "forras/hf/wikimedia/wikipedia/20231101.hu/*.parquet")))
            for r in pq.read_table(f).to_pylist()]
    arts.sort(key=lambda r: h(f"forras:{r['id']}"))
    out, n_multi, n_single = [], 0, 0
    for art in arts:
        if art["title"] in used_titles:
            continue
        pars = [p for _, ps in sections(art["text"]) for p in ps if 250 <= len(p) <= 700 and not URL.search(p)]
        if n_multi < 1500 and len(pars) >= 4:
            out.append({"id": f"wiki:{art['id']}", "tipus": "szocikk", "cim": art["title"], "bekezdesek": pars[:6]})
            n_multi += 1
        elif n_single < 2500 and pars:
            out.append({"id": f"wiki:{art['id']}", "tipus": "bekezdes", "cim": art["title"], "szoveg": pars[0]})
            n_single += 1
        if n_multi >= 1500 and n_single >= 2500:
            break
    used_njt = {json.loads(line)["source_ref"].rsplit(":", 1)[0] for fam in ("jogi.njt_torveny", "jogi.njt_fejezet", "jogi.njt_cim")
                for line in (f0 / f"{fam}.jsonl").read_text(encoding="utf-8").splitlines()}
    units = [json.loads(line) for line in (ROOT / "forras/njt/njt_egysegek.jsonl").read_text(encoding="utf-8").splitlines()]
    units = [u for u in units if 250 <= len(u["szoveg"]) <= 900
             and f"{u['law']}:{u['szakasz']}:{u['bekezdes'] or '-'}" not in used_njt]
    units.sort(key=lambda u: h(f"njt:{u['law']}:{u['szakasz']}:{u['bekezdes']}"))
    for u in units[:1000]:
        out.append({"id": f"njt:{u['law']}:{u['szakasz']}:{u['bekezdes'] or '-'}", "tipus": "bekezdes", "cim": u["cim"],
                    "szoveg": f"{u['szakasz']}{' ' + u['bekezdes'] if u['bekezdes'] else ''} {u['szoveg']}"})
    D.mkdir(parents=True, exist_ok=True)
    (D / "forras_bekezdesek.jsonl").write_text("".join(json.dumps(o, ensure_ascii=False) + "\n" for o in out), encoding="utf-8")
    print(len(out), Counter(o["tipus"] for o in out), Counter(o["id"].split(":")[0] for o in out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["forras", "gen", "check", "final", "terv", "check_export", "check_import"])
    ap.add_argument("--src", help="check_import: a kiolvaso03 kimenete")
    ap.add_argument("--csalad")
    ap.add_argument("--url")
    ap.add_argument("--model")
    ap.add_argument("--extra", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--n", type=int, default=N_GEN)
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    if a.cmd == "terv":  # a terv megtekintése (próba)
        src = source_paragraphs()
        for i in range(a.n):
            p = plan(a.csalad, i, src)
            print(json.dumps({k: v for k, v in p.items() if k not in ("bekezdesek", "bekezdes")}, ensure_ascii=False))
            print("   PROMPT:", prompt(p)[:400].replace("\n", " "))
        return
    {"forras": cmd_forras, "gen": cmd_gen, "check": cmd_check, "final": cmd_final, "check_export": cmd_check_export,
     "check_import": cmd_check_import}[a.cmd](a)


if __name__ == "__main__":
    main()
