"""Szintetikus BA-adat — S1–S4 (runbook 4.2): katalógus, szállítók, párok + split,
szállítói megnevezés, tételsorok. Az S5–S8 a jeloltek.py és az osszeallit.py.

`ujszallito` (00b kiegészítés, runbook 15. pont, 2026-10-07): a befagyasztott F1-ből (S1, train-párok, S3, S4)
új, valóban csak-teszt szállítós réteget (`T-ujszallito`) épít egy külön könyvtárba. A régi T-szállító párjai és
sorai kimaradnak (a réteg kivezetve, X(b)-cikkei az új rétegbe kerülnek); a többi pár és sor változatlan, így a
train-aliasok és a jelöltgenerálás az F1-ével azonos.

A generátor-LLM a Qwen3.8-Flash (OpenAI-kompatibilis végpont), NEM az alany.
Minden LLM-kimenet strukturált JSON; a CJK-írásjegyet tartalmazó választ eldobjuk
és új seeddel újrakérjük (docai-0117: a generátor magyar szövegbe kínai jelet szivárogtathat).

Futtatás (lora-train:2, a generátor-vLLM a 8410-es porton):
  python3 eszkozok/generator.py all --out adat/pilot --scale pilot --seed 101
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import shutil
import sys
import threading
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json, write_jsonl  # noqa: E402

GEN_URL = "http://127.0.0.1:8410/v1/chat/completions"
GEN_MODEL = "qwen38-flash-next-nvfp4"
CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯＀-￯]")

SERVICE_ROOTS = {"Szolgáltatás", "Energia és közüzem", "Ingatlan, beruházás, eszköz", "Jármű és szállítás"}
HELDOUT_ROOTS = {"Élelmiszer – hús, hal": "T-kozeli", "Konyhaüzemi anyag": "T-tavoli"}

SCALES = {
    # cikkek, szállítók (train/val/test), X(b)-arány, megtartott pár-arány
    "pilot": {"articles": 420, "suppliers": (8, 3, 4), "xb_frac": 0.08, "rows_train": 2},
    # F1 (2026-10-03, a pilot + meretezes_szim.py alapján): több cikk, cikkenként 1–4 szállító, a ≥2
    # train-szállítós cikkeknél mindig egy kitartott pár (val:T = 1:2), 16 csak-teszt szállító, a kitartott
    # gyökerek külön cikkszámmal, gyökérenként rétegzett X(b), LLM-ár. A valós S1-hozam ~1,1×.
    "full": {"articles": 4600, "heldout_n": 460, "suppliers": (24, 8, 16), "xb_frac": 0.08, "rows_train": 2,
             "n_sup_w": [0.25, 0.35, 0.25, 0.15], "p_hold": 1.0, "hold_splits": ["val-belso", "T-belso", "T-belso"],
             "xb_strat": True, "llm_price": True},
}

UNIT_ABBR = {
    "darab": "db", "kilogramm": "kg", "liter": "l", "karton": "krt", "csomag": "csom", "doboz": "dob",
    "üveg": "üv", "zsák": "zsák", "tekercs": "tek", "hónap": "hó", "alkalom": "alk", "óra": "óra",
    "kilowattóra": "kWh", "köbméter": "m3", "méter": "m", "év": "év", "nap": "nap", "adag": "adag",
}


# --- LLM ------------------------------------------------------------------

def llm_json(system: str, user: str, seed: int, max_tokens: int = 3000, tries: int = 4) -> dict:
    last = None
    for k in range(tries):
        body = {
            "model": GEN_MODEL, "temperature": 0.7, "top_p": 0.95, "seed": seed * 10 + k, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "chat_template_kwargs": {"enable_thinking": False},
        }
        try:
            req = urllib.request.Request(GEN_URL, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=900) as r:
                txt = json.loads(r.read())["choices"][0]["message"]["content"] or ""
        except Exception as e:  # hálózati / szerverhiba → újrapróba
            last = f"http: {e}"
            time.sleep(5)
            continue
        if CJK.search(txt):
            last = "CJK"
            continue
        txt = re.sub(r"^```(?:json)?|```$", "", txt.strip(), flags=re.M).strip()
        start = min([i for i in (txt.find("{"), txt.find("[")) if i >= 0], default=-1)
        try:
            return json.loads(txt[start:]) if start >= 0 else json.loads(txt)
        except json.JSONDecodeError:
            # a lezáratlan farok levágása az utolsó teljes objektumig
            end = txt.rfind("}")
            try:
                return json.loads(txt[start:end + 1])
            except Exception:
                last = "JSON"
    raise RuntimeError(f"LLM-hívás sikertelen ({last})")


# --- S1 katalógus -----------------------------------------------------------

SYS_KAT = ("Kitalált, de valószerű magyar beszerzési cikktörzset állítasz össze egy szálloda és étterem számára. "
           "Kizárólag érvényes JSON-t adsz vissza, magyarázat nélkül.")

PROMPT_TERMEK = """Kategória: {path}
Készíts {k} termékcsaládot. A családok kb. fele egyetlen változatból álljon; a többiben 2–3 változat legyen,
amelyek PONTOSAN EGY tulajdonságban különböznek: méret/kiszerelés, változat (pl. zsírtartalom, íz, fajta),
vagy márka. A márkanevek legyenek kitaláltak, ne létező márkák. A nevek a cikktörzsben szokásos, rendezett
alakúak legyenek (pl. "Tej 2,8% 1 l", "Csirkemell filé friss").
Formátum:
{{"csaladok":[{{"alap":"rövid általános név","valtozatok":[{{"nev":"teljes cikknév","marka":"kitalált márka vagy null",
"valtozat":"pl. 2,8% vagy null","meret":"pl. 1 l / 500 g vagy null","egyseg":"darab|kilogramm|liter|karton|csomag|doboz|üveg|zsák|tekercs",
"kulonbseg":"meret|valtozat|marka|null","ar_ft":"becsült nettó nagykereskedelmi ár forintban EGY egységre (szám)"}}]}}]}}"""

PROMPT_SZOLG = """Kategória: {path}
Készíts {k} szolgáltatás- vagy díjtétel-családot egy szálloda és étterem beszerzéseihez. A családok kb. fele
egyetlen tételből álljon; a többiben 2–3 tétel legyen, amelyek PONTOSAN EGY tulajdonságban különböznek:
időszak (havi, negyedéves, eseti), helyszín (pl. konyha, szállodaépület, parkoló), vagy típus/szerződés.
Szolgáltató- és márkanevet ne írj.
Formátum:
{{"csaladok":[{{"alap":"rövid általános név","valtozatok":[{{"nev":"teljes tételnév","tipus":"vagy null","idoszak":"vagy null",
"helyszin":"vagy null","egyseg":"hónap|alkalom|óra|darab|kilowattóra|köbméter|év","kulonbseg":"idoszak|helyszin|tipus|null",
"ar_ft":"becsült nettó ár forintban EGY egységre (szám)"}}]}}]}}"""

ATTRS_TERMEK = ["marka", "valtozat", "meret"]
ATTRS_SZOLG = ["tipus", "idoszak", "helyszin"]


def llm_price(profile: dict, path: str, v: dict) -> float | None:
    """F1: a generátor-LLM ára (Ft / egység), a profil q10/3 – q90·3 sávjára csonkolva. A profil
    kvantilisei alkategóriánként keverik a mennyiségi egységeket, ezért csak durva korlát."""
    try:
        x = float(str(v.get("ar_ft")).replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None
    if not (x > 0 and math.isfinite(x)):
        return None
    q = profile["egysegar_kvantilis_ft"].get(path)
    if q and len(q) >= 5 and q[0] > 0:
        x = min(max(x, q[0] / 3), q[4] * 3)
    return round(x, 2)


def price_for(profile: dict, path: str, rng: random.Random) -> float:
    q = profile["egysegar_kvantilis_ft"].get(path)
    if not q or len(q) < 4 or q[1] <= 0:
        lo, hi = 300.0, 5000.0
    else:
        lo, hi = sorted([q[1], q[3]])
        lo, hi = max(lo, 1.0), max(hi, lo * 1.5)
    return round(math.exp(rng.uniform(math.log(lo), math.log(hi))), 2)


def size_value(s: str | None) -> tuple[float, str] | None:
    if not s:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*(kg|g|dkg|l|dl|cl|ml|db)\b", s, re.I)
    if not m:
        return None
    v = float(m.group(1).replace(",", "."))
    u = m.group(2).lower()
    conv = {"kg": (1000, "g"), "g": (1, "g"), "dkg": (10, "g"), "l": (1000, "ml"), "dl": (100, "ml"), "cl": (10, "ml"), "ml": (1, "ml"), "db": (1, "db")}
    f, base = conv[u]
    return v * f, base


def s1_katalogus(profile: dict, n_articles: int, seed: int, out: Path, heldout_n: int | None = None,
                 use_llm_price: bool = False) -> list[dict]:
    path = out / "s1_katalogus.jsonl"
    if path.exists():
        return read_jsonl(path)
    rng = random.Random(seed)
    jobs = []
    for root, rp in profile["gyokerek"].items():
        n_root = heldout_n if (heldout_n and root in HELDOUT_ROOTS) else max(6, round(n_articles * rp["cikk_arany"]))
        for sub, sp in rp["alkategoria_arany"].items():
            n_sub = max(3, round(n_root * sp))
            fam = max(2, round(n_sub / 1.8))
            for b in range(0, fam, 8):
                jobs.append((root, sub, min(8, fam - b), len(jobs)))

    def run(job):
        root, sub, k, j = job
        p = f"{root} › {sub}"
        tmpl = PROMPT_SZOLG if root in SERVICE_ROOTS else PROMPT_TERMEK
        data = llm_json(SYS_KAT, tmpl.format(path=p, k=k), seed=seed * 1000 + j)
        fams_ = data.get("csaladok", []) if isinstance(data, dict) else data
        return root, sub, [f for f in (fams_ if isinstance(fams_, list) else []) if isinstance(f, dict)]

    with ThreadPoolExecutor(4) as ex:
        results = list(ex.map(run, jobs))

    arts, seen = [], set()
    for root, sub, fams in results:
        p = f"{root} › {sub}"
        attrs = ATTRS_SZOLG if root in SERVICE_ROOTS else ATTRS_TERMEK
        for fam in fams:
            fid = f"f{len(arts):05d}"
            base_price, base_size = None, None
            for v in [v for v in (fam.get("valtozatok") or []) if isinstance(v, dict)][:3]:
                name = str(v.get("nev") or "").strip()
                key = re.sub(r"\W+", "", name.lower())
                if not (3 <= len(name) <= 80) or key in seen or CJK.search(name):
                    continue
                seen.add(key)
                a = {k: (str(v[k]).strip() if v.get(k) not in (None, "", "null") else None) for k in attrs}
                sv = size_value(a.get("meret"))
                if base_price is None:
                    price = (llm_price(profile, p, v) if use_llm_price else None) or price_for(profile, p, rng)
                    base_price, base_size = price, sv
                elif sv and base_size and sv[1] == base_size[1] and base_size[0] > 0:
                    price = round(base_price * (sv[0] / base_size[0]) ** 0.85 * rng.uniform(0.95, 1.05), 2)
                else:
                    price = round(base_price * rng.uniform(0.85, 1.15), 2)
                unit = str(v.get("egyseg") or "darab")
                nsv = size_value(name)
                if use_llm_price and nsv and unit in ("kilogramm", "liter") and nsv[1] in ("g", "ml") and nsv[0] != 1000:
                    unit = "darab"  # „Péksütemény 100 g” nem kilogrammos egység (pilot-megfigyelés)
                arts.append({
                    "id": f"a{len(arts):05d}", "family": fid, "name": name, "root": root, "sub": sub, "path": p,
                    "unit": unit, "attrs": a, "diff": v.get("kulonbseg"),
                    "price": price, "catchall": False, "kind": "szolg" if root in SERVICE_ROOTS else "termek",
                })
    # gyűjtőcikkek: gyökerenként egy, a gyűjtő-arányos gyökerekben alkategóriánként is
    for root, rp in profile["gyokerek"].items():
        subs = list(rp["alkategoria_arany"]) if rp["gyujto_arany"] > 0.05 else []
        for name, p in [(f"Egyéb – {root}", f"{root} › Egyéb")] + [(s if s.lower().startswith("egyéb") else f"Egyéb {s.lower()}", f"{root} › {s}") for s in subs]:
            arts.append({"id": f"a{len(arts):05d}", "family": f"g{len(arts):05d}", "name": name, "root": root,
                         "sub": p.split(" › ")[1], "path": p, "unit": "darab", "attrs": {}, "diff": None,
                         "price": 0.0, "catchall": True, "kind": "gyujto"})
    write_jsonl(path, arts)
    return arts


# --- S2 szállítók ------------------------------------------------------------

ELO = ["Alföld", "Bakony", "Balaton", "Duna", "Tisza", "Mátra", "Zemplén", "Kiskun", "Rába", "Dráva", "Somló", "Pilis",
       "Bükk", "Hegyalja", "Sárrét", "Nyírség", "Őrség", "Hanság", "Mecsek", "Kőszeg", "Vértes", "Gerecse", "Cserhát",
       "Börzsöny", "Jászság", "Sárköz", "Ormánság", "Hajdúság", "Nagykunság", "Bácska"]
KOZEP = {
    "Élelmiszer – növényi, tej": ["Friss", "Agro", "Tej", "Pék", "Zöldség"], "Élelmiszer – hús, hal": ["Hús", "Hal", "Vágóhíd"],
    "Élelmiszer – feldolgozott": ["Gasztro", "Élelmiszer", "Konzerv"], "Ital": ["Ital", "Pince", "Forrás"],
    "Konyhaüzemi anyag": ["Higiénia", "Gasztro", "Csomagolás"], "Energia és közüzem": ["Energia", "Közmű", "Hő"],
    "Ingatlan, beruházás, eszköz": ["Építő", "Technika", "Berendezés"], "Jármű és szállítás": ["Autó", "Flotta", "Fuvar"],
    "Szolgáltatás": ["Szerviz", "Partner", "Szolgáltató", "Consulting"],
}
JOGI = ["Kft.", "Kft.", "Kft.", "Zrt.", "Bt."]


def s2_szallitok(profile: dict, groups: tuple[int, int, int], seed: int, out: Path) -> list[dict]:
    path = out / "s2_szallitok.json"
    if path.exists():
        return json.load(open(path))
    rng = random.Random(seed + 2)
    roots = list(profile["gyokerek"])
    weights = [profile["gyokerek"][r]["cikk_arany"] for r in roots]
    sups, names = [], set()
    roles = ["train"] * groups[0] + ["val"] * groups[1] + ["test"] * groups[2]
    for i, role in enumerate(roles):
        nroot = rng.choices([1, 2, 3], weights=[0.68, 0.18, 0.14])[0]
        rs = set()
        while len(rs) < nroot:
            rs.add(rng.choices(roots, weights=weights)[0])
        prim = sorted(rs, key=lambda r: -profile["gyokerek"][r]["cikk_arany"])[0]
        while True:
            nm = f"{rng.choice(ELO)} {rng.choice(KOZEP[prim])} {rng.choice(JOGI)}"
            if nm not in names:
                names.add(nm)
                break
        pat = profile["gyokerek"][prim]["tetelszoveg"]["mintazat_arany"]
        sups.append({
            "id": f"s{i:03d}", "name": nm, "role": role, "roots": sorted(rs), "primary": prim,
            "style": {
                "nagybetu": rng.random() < max(0.05, pat["nagybetus"]),
                "rovidites": rng.choices([0, 1, 2, 3], weights=[0.25, 0.3, 0.25, 0.2])[0],
                "kodelotag": rng.random() < 0.12,
                "kiszereles": rng.random() < 0.4,
                "zarojel": rng.random() < 0.35,
                "szorend": rng.choice(["marka_elol", "marka_hatul", "marka_nelkul"]),
                "mezohossz": rng.choice([24, 30, 40, 60, 80]),
                "eliras": rng.choice([0.0, 0.0, 0.005, 0.01, 0.02]),
            },
        })
    # minden kitartott gyökeret legalább két train-szállító szolgáljon ki (T-kategória: látott stílus)
    for r in HELDOUT_ROOTS:
        tr = [s for s in sups if s["role"] == "train" and r in s["roots"]]
        for s in [s for s in sups if s["role"] == "train" and r not in s["roots"]][: max(0, 2 - len(tr))]:
            s["roots"] = sorted(set(s["roots"]) | {r})
    write_json(path, sups)
    return sups


# --- párok és split ------------------------------------------------------------

def parok_split(arts: list[dict], sups: list[dict], scale: dict, seed: int, out: Path) -> list[dict]:
    """(szállító, cikk) párok és a split-hozzárendelés — a split EGYSÉGE a pár."""
    path = out / "parok.jsonl"
    if path.exists():
        return read_jsonl(path)
    rng = random.Random(seed + 3)
    by_root = defaultdict(lambda: {"train": [], "val": [], "test": []})
    for s in sups:
        for r in s["roots"]:
            by_root[r][s["role"]].append(s)
    real = [a for a in arts if not a["catchall"]]
    # X(b): a katalógusból kihagyott „új termékek”, splitenként diszjunktan. F1-től gyökérenként
    # rétegzett húzás (a pilotban egyenletes húzásnál a „hús, hal” gyökérbe 0 jutott; P ≈ 1%).
    if scale.get("xb_strat"):
        by_r = defaultdict(list)
        for a in real:
            by_r[a["root"]].append(a)
        xb = set()
        for r in sorted(by_r):
            xb |= {a["id"] for a in rng.sample(by_r[r], max(1, round(len(by_r[r]) * scale["xb_frac"])))}
    else:
        xb = set(a["id"] for a in rng.sample(real, round(len(real) * scale["xb_frac"])))
    n_sup_w = scale.get("n_sup_w", [0.55, 0.3, 0.15])
    p_hold = scale.get("p_hold", 0.5)
    hold_splits = scale.get("hold_splits", ["val-belso", "T-belso", "T-belso"])
    pairs = []
    for a in real:
        r = a["root"]
        pool = by_root[r]
        heldout = r in HELDOUT_ROOTS
        if a["id"] in xb:
            stratum = rng.choices(["train", "val-belso", "val-szallito", "T-belso", "T-szallito"] + (["heldout"] if heldout else []),
                                  weights=[0.55, 0.08, 0.07, 0.15, 0.15] + ([0.3] if heldout else []))[0]
            if heldout:
                stratum = HELDOUT_ROOTS[r] if stratum in ("heldout", "T-belso", "T-szallito") else stratum
                if stratum in ("train", "val-belso", "val-szallito"):
                    stratum = HELDOUT_ROOTS[r]  # a kitartott gyökér sorai csak a tesztben élnek
            role = {"val-szallito": "val", "T-szallito": "test"}.get(stratum, "train")
            cands = pool[role] or pool["train"] or [s for s in sups if s["role"] == role]
            s = rng.choice(cands)
            pairs.append({"supplier": s["id"], "article": a["id"], "split": stratum, "xb": True})
            continue
        n_sup = rng.choices(list(range(1, len(n_sup_w) + 1)), weights=n_sup_w)[0]
        if heldout:
            chosen = rng.sample(pool["train"], min(n_sup, len(pool["train"])))
            for s in chosen:
                pairs.append({"supplier": s["id"], "article": a["id"], "split": HELDOUT_ROOTS[r], "xb": False})
            continue
        cand = pool["train"] + pool["val"] + pool["test"]
        if not cand:
            continue
        chosen = rng.sample(cand, min(n_sup, len(cand)))
        tr = [s for s in chosen if s["role"] == "train"]
        hold = None
        if len(tr) >= 2 and rng.random() < p_hold:
            hold = tr[-1]["id"]  # látott szállító × látott cikk, NEM látott pár
        for s in chosen:
            if s["role"] == "val":
                split = "val-szallito"
            elif s["role"] == "test":
                split = "T-szallito"
            elif s["id"] == hold:
                split = rng.choice(hold_splits)
            else:
                split = "train"
            pairs.append({"supplier": s["id"], "article": a["id"], "split": split, "xb": False})
    # a val-szállító / T-szállító cikkeinek „láthatónak” kell lenniük: legyen train-párjuk is
    has_train = {p["article"] for p in pairs if p["split"] == "train"}
    for p in pairs:
        if p["split"] in ("val-szallito", "T-szallito", "val-belso", "T-belso") and not p["xb"] and p["article"] not in has_train:
            p["split"] = "train"
            has_train.add(p["article"])
    write_jsonl(path, pairs)
    return pairs


# --- S3 szállítói megnevezés ---------------------------------------------------

SYS_MEGN = ("Egy beszállító számlázó rendszerének tételmegnevezéseit írod. Kizárólag érvényes JSON-t adsz vissza, "
            "magyarázat nélkül.")
PROMPT_MEGN = """Beszállító: {name}
Írásmód: rövidítési szint {rov} (0 = teljes szavak; 3 = erősen rövidített, pl. "Cs.mell", "Napr.olaj", "Pap.zsebk."),
márkanév helye: {szorend}. A kis- és nagybetűket a szokásos módon használd; csupa nagybetűt ne írj (betűszó,
pl. "UHT", "SZSV" kivétel).
Add meg, hogyan szerepelnének az alábbi cikkek ennek a beszállítónak a számláján. A megnevezés a beszállító
saját szóhasználata legyen (szinonima, más szórend, rövidítés megengedett), de a "megorzendo" tulajdonságok értéke
maradjon felismerhető (rövidítve is). Mennyiséget, árat, kódot ne írj hozzá.
Cikkek: {cikkek}
Formátum: {{"tetelek":[{{"cikk_id":"...","megnevezes":"..."}}]}}"""


def keep_attrs(a: dict, fam: list[dict]) -> dict:
    """A cikket a testvéreitől megkülönböztető tulajdonságok (+ márka)."""
    keep = {}
    for k, v in a["attrs"].items():
        if v is None:
            continue
        if k == "marka" or any(o["id"] != a["id"] and o["attrs"].get(k) != v for o in fam):
            keep[k] = v
    return keep


def s3_megnevezes(arts: list[dict], sups: list[dict], pairs: list[dict], seed: int, out: Path) -> dict:
    path = out / "s3_megnevezes.json"
    if path.exists():
        return json.load(open(path))
    A = {a["id"]: a for a in arts}
    fams = defaultdict(list)
    for a in arts:
        fams[a["family"]].append(a)
    by_sup = defaultdict(list)
    for p in pairs:
        by_sup[p["supplier"]].append(p["article"])
    S = {s["id"]: s for s in sups}
    jobs = []
    for sid, aids in by_sup.items():
        for b in range(0, len(aids), 15):
            jobs.append((sid, aids[b:b + 15], len(jobs)))
    szorend = {"marka_elol": "a márkanév elöl", "marka_hatul": "a márkanév a végén", "marka_nelkul": "márkanév nélkül, ha a cikk enélkül is egyértelmű"}

    def ask(sid: str, aids: list[str], seed_k: int) -> dict[str, str]:
        s = S[sid]
        cikkek = [{"cikk_id": aid, "nev": A[aid]["name"], "megorzendo": keep_attrs(A[aid], fams[A[aid]["family"]])} for aid in aids]
        try:
            data = llm_json(SYS_MEGN, PROMPT_MEGN.format(name=s["name"], rov=s["style"]["rovidites"], szorend=szorend[s["style"]["szorend"]],
                                                          cikkek=json.dumps(cikkek, ensure_ascii=False)), seed=seed_k)
        except RuntimeError:
            return {}
        # a modell néha listát vagy beágyazott listát ad vissza (F1C, 2026-10-04) — csak a dict-tételek számítanak
        tet = data.get("tetelek", []) if isinstance(data, dict) else data
        out_ = {}
        for t in tet if isinstance(tet, list) else []:
            if isinstance(t, dict) and t.get("cikk_id") is not None:
                out_[str(t["cikk_id"])] = str(t.get("megnevezes") or "").strip()
        return out_

    # hívásonkénti cache: egy későbbi hiba után a futás innen folytatódik
    cache_path = out / "s3_cache.jsonl"
    cache = {r["j"]: r for r in read_jsonl(cache_path)} if cache_path.exists() else {}
    lock = threading.Lock()

    def run(job):
        sid, aids, j = job
        if j in cache:
            return sid, cache[j]["names"]
        got = ask(sid, aids, seed * 7000 + j)
        miss = [a for a in aids if not got.get(a)]
        if miss:  # egy újrakérés a hiányzókra, más seeddel
            got.update({k: v for k, v in ask(sid, miss, seed * 7000 + j + 500000).items() if k in miss})
        names_j = {aid: got.get(aid) for aid in aids}
        with lock:
            with open(cache_path, "a") as f:
                f.write(json.dumps({"j": j, "sid": sid, "names": names_j}, ensure_ascii=False) + "\n")
        return sid, names_j

    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(run, jobs))
    names: dict[str, str] = {}
    for sid, d in res:
        for aid, n in d.items():
            if n and not CJK.search(n) and 2 <= len(n) <= 120:
                names[f"{sid}|{aid}"] = n
    write_json(path, names)
    return names


# --- S4 tételsorok ----------------------------------------------------------------

def typo(s: str, rate: float, rng: random.Random) -> str:
    if rate <= 0:
        return s
    cs = list(s)
    for i in range(len(cs) - 1):
        if cs[i].isalpha() and cs[i + 1].isalpha() and rng.random() < rate:
            cs[i], cs[i + 1] = cs[i + 1], cs[i]
    return "".join(cs)


ZAROJEL_TOKEN = re.compile(r"\d+(?:[.,]\d+)?\s?(?:%|kg|dkg|g|l|dl|cl|ml|db)(?![\wáéíóöőúüű])", re.I)


def render_line(base: str, a: dict, s: dict, rng: random.Random) -> tuple[str, str, float, float]:
    st = s["style"]
    t = base
    unit = UNIT_ABBR.get(a["unit"], a["unit"])
    qty = rng.choice([1, 1, 2, 3, 5, 6, 10, 12, 20, 24]) if a["kind"] != "szolg" else rng.choice([1, 1, 1, 2, 3, 12])
    price = a["price"] * rng.uniform(0.9, 1.15)
    if st["kiszereles"] and a["kind"] == "termek" and rng.random() < 0.5:
        pack = rng.choice([6, 10, 12, 20])
        t += rng.choice([f" {pack}/KRT", f" {pack}x", f" ({pack} db/karton)"])
        if rng.random() < 0.5:  # kartonban számlázva
            unit, qty, price = "krt", max(1, qty // pack), price * pack
    if st.get("zarojel"):  # „Tej 2,8% 1 l” → „Tej (2,8%) 1 l” / „Tej 2,8% (1 l)”
        m = list(ZAROJEL_TOKEN.finditer(t))
        if m:
            g = rng.choice(m)
            t = f"{t[:g.start()]}({g.group(0)}){t[g.end():]}"
        elif rng.random() < 0.5:
            t += f" ({unit})"
    t = typo(t, st["eliras"], rng)
    if st["kodelotag"]:
        t = f"{rng.randint(10000, 999999)} {t}"
    if st["nagybetu"]:
        t = t.upper()
    t = t[: st["mezohossz"]].rstrip()
    return t, unit, float(qty), round(price, 2)


def s4_sorok(arts, sups, pairs, names, scale, seed, out: Path) -> list[dict]:
    path = out / "s4_sorok.jsonl"
    if path.exists():
        return read_jsonl(path)
    rng = random.Random(seed + 4)
    A = {a["id"]: a for a in arts}
    S = {s["id"]: s for s in sups}
    rows = []
    for p in pairs:
        base = names.get(f"{p['supplier']}|{p['article']}")
        if not base:
            continue
        n = scale["rows_train"] if p["split"] == "train" else 1
        for k in range(n):
            t, unit, qty, price = render_line(base, A[p["article"]], S[p["supplier"]], rng)
            rows.append({"row": f"r{len(rows):06d}", **p, "text": t, "base_name": base, "unit": unit, "qty": qty, "unit_price": price})
    write_jsonl(path, rows)
    return rows


def ujszallito(profile: dict, src: Path, out: Path, n_new: int, seed: int) -> dict:
    """00b: `T-ujszallito` — n_new új csak-teszt szállító, csak látott (train-párral bíró) cikkekre (runbook 15. pont)."""
    for f in ("s1_katalogus.jsonl",):
        if not (out / f).exists():
            shutil.copy(src / f, out / f)
    if (src / "dedup").is_dir() and not (out / "dedup").exists():
        shutil.copytree(src / "dedup", out / "dedup")
    arts = read_jsonl(out / "s1_katalogus.jsonl")
    sups_old = json.load(open(src / "s2_szallitok.json"))
    pairs_old = read_jsonl(src / "parok.jsonl")
    rows_old = read_jsonl(src / "s4_sorok.jsonl")
    names_old = json.load(open(src / "s3_megnevezes.json"))

    # S2′: új szállítók az S2 receptjével, új seeddel; id a meglévők után, név ütközés nélkül
    path = out / "s2_szallitok.json"
    if path.exists():
        sups = json.load(open(path))
    else:
        tmp = out / "s2_uj"
        tmp.mkdir(exist_ok=True)
        # a csak kitartott gyökeret kiszolgáló szállító nem kaphat látott cikket (az F1-ben így lett 16-ból 14):
        # az S2 receptjével háromszor annyi jelölt, ezekből az első n_new, amely nem kitartott gyökeret is kiszolgál
        cands = s2_szallitok(profile, (0, 0, 3 * n_new), seed, tmp)
        new = [s for s in cands if set(s["roots"]) - set(HELDOUT_ROOTS)][:n_new]
        if len(new) < n_new:
            raise RuntimeError(f"csak {len(new)} alkalmas új szállító")
        used = {s["name"] for s in sups_old}
        rng = random.Random(seed + 22)
        base = 1 + max(int(s["id"][1:]) for s in sups_old)
        for k, s in enumerate(new):
            s["id"] = f"s{base + k:03d}"
            while s["name"] in used:
                s["name"] = f"{rng.choice(ELO)} {rng.choice(KOZEP[s['primary']])} {rng.choice(JOGI)}"
            used.add(s["name"])
        sups = sups_old + new
        write_json(path, sups)
    new_ids = {s["id"] for s in sups} - {s["id"] for s in sups_old}

    # párok: az F1 párjai a régi T-szállító nélkül + az új réteg
    path = out / "parok.jsonl"
    if path.exists():
        pairs = read_jsonl(path)
    else:
        rng = random.Random(seed + 3)
        seen = {p["article"] for p in pairs_old if p["split"] == "train" and not p["xb"]}
        xb_old = [p for p in pairs_old if p["split"] == "T-szallito" and p["xb"]]
        by_root = defaultdict(lambda: {"train": [], "val": [], "test": []})
        for s in sups:
            if s["role"] == "test" and s["id"] not in new_ids:
                continue  # a régi teszt-szállítók kivezetve
            for r in s["roots"]:
                by_root[r][s["role"]].append(s)
        n_sup_w = SCALES["full"]["n_sup_w"]
        new_pairs = []
        for a in arts:
            if a["catchall"] or a["root"] in HELDOUT_ROOTS or a["id"] not in seen:
                continue
            pool = by_root[a["root"]]
            cand = pool["train"] + pool["val"] + pool["test"]
            n_sup = rng.choices(list(range(1, len(n_sup_w) + 1)), weights=n_sup_w)[0]
            for s in rng.sample(cand, min(n_sup, len(cand))):
                if s["id"] in new_ids:
                    new_pairs.append({"supplier": s["id"], "article": a["id"], "split": "T-ujszallito", "xb": False})
        all_new = [s for s in sups if s["id"] in new_ids]
        A = {a["id"]: a for a in arts}
        for p in xb_old:
            s = rng.choice(by_root[A[p["article"]]["root"]]["test"] or all_new)
            new_pairs.append({"supplier": s["id"], "article": p["article"], "split": "T-ujszallito", "xb": True})
        pairs = [p for p in pairs_old if p["split"] != "T-szallito"] + new_pairs
        write_jsonl(path, pairs)
    new_pairs = [p for p in pairs if p["split"] == "T-ujszallito"]

    # S3: megnevezés csak az új párokra (saját cache az s3_uj alatt), az F1 nevei változatlanok
    path = out / "s3_megnevezes.json"
    if path.exists():
        names = json.load(open(path))
    else:
        tmp = out / "s3_uj"
        tmp.mkdir(exist_ok=True)
        names = {**names_old, **s3_megnevezes(arts, sups, new_pairs, seed, tmp)}
        write_json(path, names)

    # S4: a régi sorok a régi T-szállító nélkül + az új réteg sorai; a sor-id a meglévők után folytatódik
    path = out / "s4_sorok.jsonl"
    if path.exists():
        rows = read_jsonl(path)
    else:
        rng = random.Random(seed + 4)
        A = {a["id"]: a for a in arts}
        S = {s["id"]: s for s in sups}
        nxt = 1 + max(int(r["row"][1:]) for r in rows_old)
        rows = [r for r in rows_old if r["split"] != "T-szallito"]
        for p in new_pairs:
            base_name = names.get(f"{p['supplier']}|{p['article']}")
            if not base_name:
                continue
            t, unit, qty, price = render_line(base_name, A[p["article"]], S[p["supplier"]], rng)
            rows.append({"row": f"r{nxt:06d}", **p, "text": t, "base_name": base_name, "unit": unit, "qty": qty,
                         "unit_price": price})
            nxt += 1
        write_jsonl(path, rows)
    new_rows = [r for r in rows if r["split"] == "T-ujszallito"]
    rep = {"seed": seed, "uj_szallitok": sorted(new_ids), "uj_parok": len(new_pairs),
           "uj_parok_xb": sum(p["xb"] for p in new_pairs), "uj_sorok": len(new_rows),
           "uj_sorok_szallitonkent": dict(Counter(r["supplier"] for r in new_rows)),
           "kimaradt_regi_T_szallito_sorok": sum(r["split"] == "T-szallito" for r in rows_old)}
    write_json(out / "generator_riport.json", rep)
    return rep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["all", "ujszallito"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--scale", default="pilot", choices=sorted(SCALES))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--profile", default=str(EXP / "adat/tenant_profil.json"))
    ap.add_argument("--src", default="adat/f1", help="ujszallito: a befagyasztott F1-könyvtár")
    ap.add_argument("--n-new", type=int, default=16, help="ujszallito: az új csak-teszt szállítók száma")
    args = ap.parse_args()
    out = Path(args.out)
    if not out.is_absolute():
        out = EXP / out
    out.mkdir(parents=True, exist_ok=True)
    profile = json.load(open(args.profile))
    if args.cmd == "ujszallito":
        src = Path(args.src) if Path(args.src).is_absolute() else EXP / args.src
        print(json.dumps(ujszallito(profile, src, out, args.n_new, args.seed), ensure_ascii=False), flush=True)
        return
    sc = SCALES[args.scale]
    t0 = time.time()
    arts = s1_katalogus(profile, sc["articles"], args.seed, out, sc.get("heldout_n"), sc.get("llm_price", False))
    print(f"[{time.time() - t0:6.0f}s] S1: {len(arts)} cikk", flush=True)
    sups = s2_szallitok(profile, sc["suppliers"], args.seed, out)
    pairs = parok_split(arts, sups, sc, args.seed, out)
    print(f"[{time.time() - t0:6.0f}s] S2+párok: {len(sups)} szállító, {len(pairs)} pár {dict(Counter(p['split'] for p in pairs))}", flush=True)
    names = s3_megnevezes(arts, sups, pairs, args.seed, out)
    print(f"[{time.time() - t0:6.0f}s] S3: {len(names)} megnevezés", flush=True)
    rows = s4_sorok(arts, sups, pairs, names, sc, args.seed, out)
    print(f"[{time.time() - t0:6.0f}s] S4: {len(rows)} sor {dict(Counter(r['split'] for r in rows))}", flush=True)
    write_json(out / "generator_riport.json", {
        "seed": args.seed, "scale": args.scale, "articles": len(arts), "catchall": sum(a["catchall"] for a in arts),
        "families_with_siblings": sum(1 for f, n in Counter(a["family"] for a in arts if not a["catchall"]).items() if n > 1),
        "suppliers": len(sups), "pairs": len(pairs), "names": len(names), "rows": len(rows),
        "rows_by_split": dict(Counter(r["split"] for r in rows)), "wall_s": round(time.time() - t0),
    })


if __name__ == "__main__":
    main()
