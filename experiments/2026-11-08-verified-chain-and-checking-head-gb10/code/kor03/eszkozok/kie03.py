"""03-as kör — a KIE/validáció HO-új-család generátora (03-runbook 3.4, 4.6, 5.; spec: kor03/spec/kie_validacio.yaml).

Szintetikus magyar számlák, három szövegformában (táblázatos, folyószöveg, OCR-szerű), dokumentumonként egy
szám- és egy dátumformával. Minden dokumentumból egy item lesz; a gold az adatszerkezetből számolódik. A meta.kie a
renderelt (megjelenített) értékeket tartja: a test_kie03.py ezekből és a renderelt szövegből, a generátor logikájától
függetlenül számolja újra a goldot. A meta nem kerül a promptba.

  kor01/.venv/bin/python kor03/eszkozok/kie03.py      # → kor03/adat/f0/kie.{osszeg,datum,mezo}.jsonl + kie03_riport.json
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import noul_options, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((ROOT / "spec/kie_validacio.yaml").read_text(encoding="utf-8"))
OUT = ROOT / "adat/f0"

# --- fiktív törzsadatok ------------------------------------------------------------------------------------------------

SURNAMES = ["Nagy", "Kovács", "Tóth", "Szabó", "Horváth", "Varga", "Kiss", "Molnár", "Németh", "Farkas", "Balogh",
            "Papp", "Takács", "Juhász", "Mészáros", "Simon", "Rácz", "Fekete", "Szilágyi", "Török"]
NAME_ROOTS = ["Tiszavirág", "Bakonyfenyő", "Mecsekalja", "Hajnalpír", "Kristálypatak", "Napfényliget", "Zöldmező",
              "Ezüstnyír", "Vértesvölgy", "Mátraalja", "Pannonkő", "Rétköz", "Kékgolyó", "Szélmalom", "Tölgyliget",
              "Fürjes", "Somlyó", "Hegyhát", "Csillagfürt", "Kőhíd"]
ACTIVITIES = ["Kereskedelmi", "Szolgáltató", "Építőipari", "Informatikai", "Logisztikai", "Ipari", "Agrár",
              "Irodatechnikai", "Vendéglátó", "Mérnöki"]
FORMS = ["Kft.", "Kft.", "Kft.", "Bt.", "Zrt."]
CITIES = [("Budapest", "1037"), ("Budapest", "1117"), ("Budapest", "1149"), ("Debrecen", "4024"), ("Szeged", "6720"),
          ("Miskolc", "3525"), ("Pécs", "7621"), ("Győr", "9021"), ("Nyíregyháza", "4400"), ("Kecskemét", "6000"),
          ("Székesfehérvár", "8000"), ("Szombathely", "9700"), ("Szolnok", "5000"), ("Tatabánya", "2800"),
          ("Kaposvár", "7400"), ("Veszprém", "8200"), ("Békéscsaba", "5600"), ("Zalaegerszeg", "8900"),
          ("Sopron", "9400"), ("Eger", "3300")]
STREETS = ["Petőfi Sándor utca", "Kossuth Lajos utca", "Rákóczi út", "Ady Endre utca", "Dózsa György út",
           "Széchenyi István tér", "Arany János utca", "Jókai Mór utca", "Bem József utca", "Fő utca",
           "Táncsics Mihály utca", "Hunyadi János utca", "Vasút utca", "Határ út", "Ipartelep utca"]
# (megnevezés, egység, egységár-tartomány, mennyiség-tartomány)
PRODUCTS = [
    ("Irodai másolópapír A4, 500 lap", "csomag", (1800, 3500), (1, 30)),
    ("Tonerkazetta, fekete", "db", (12000, 45000), (1, 6)),
    ("Rendszerkarbantartás", "óra", (8000, 18000), (1, 40)),
    ("Szállítási díj", "alkalom", (3000, 15000), (1, 3)),
    ("Csavar M8×40, horganyzott", "doboz", (1500, 6000), (1, 20)),
    ("Ipari tisztítószer, 5 l", "kanna", (4000, 12000), (1, 10)),
    ("Monitor, 27 hüvelykes", "db", (60000, 140000), (1, 5)),
    ("Szoftverlicenc, éves", "db", (30000, 300000), (1, 10)),
    ("Szakértői tanácsadás", "óra", (15000, 40000), (1, 24)),
    ("EUR raklap", "db", (3000, 7000), (5, 60)),
    ("Beltéri falfesték, 10 l", "vödör", (9000, 25000), (1, 8)),
    ("Szemes kávé, 1 kg", "csomag", (5000, 12000), (1, 12)),
    ("Munkavédelmi kesztyű", "pár", (300, 1500), (5, 100)),
    ("Irodabérleti díj", "hó", (50000, 400000), (1, 1)),
    ("Takarítási szolgáltatás", "hó", (40000, 250000), (1, 1)),
    ("Villanyszerelési anyag", "tétel", (2000, 80000), (1, 1)),
    ("Fénymásolás, fekete-fehér", "oldal", (10, 40), (100, 2000)),
    ("Laptoptáska", "db", (6000, 18000), (1, 10)),
    ("Ásványvíz, 0,5 l", "karton", (1500, 3500), (1, 40)),
    ("Hűtőközeg-utántöltés", "alkalom", (20000, 90000), (1, 2)),
]
MONTHS = ["január", "február", "március", "április", "május", "június", "július", "augusztus", "szeptember",
          "október", "november", "december"]
VAT_RATES = SPEC["dokumentum"]["afakulcsok"]

# --- azonosítók ellenőrző számjeggyel --------------------------------------------------------------------------------


def taxno_check(d7: str) -> int:
    """A törzsszám 8. számjegye: a 9,7,3,1,9,7,3 súlyú összeg kiegészítése 10-re."""
    return (10 - sum(int(c) * w for c, w in zip(d7, (9, 7, 3, 1, 9, 7, 3))) % 10) % 10


def giro_check(digits: str) -> int:
    """A GIRO-blokk ellenőrző számjegye: a 9,7,3,1 ciklikus súlyú összeg kiegészítése 10-re."""
    return (10 - sum(int(c) * (9, 7, 3, 1)[i % 4] for i, c in enumerate(digits)) % 10) % 10


def tax_number(rnd: random.Random) -> str:
    d7 = "99" + "".join(rnd.choice("0123456789") for _ in range(5))
    return f"{d7}{taxno_check(d7)}-{rnd.choice('22223')}-{rnd.choice(['41', '42', '43', '44', '02', '03', '05', '07', '08', '09', '13', '14'])}"


def bank_account(rnd: random.Random) -> str:
    b1 = "999" + "".join(rnd.choice("0123456789") for _ in range(4))
    b23 = "".join(rnd.choice("0123456789") for _ in range(15))
    full23 = b23 + str(giro_check(b23))
    return f"{b1}{giro_check(b1)}-{full23[:8]}-{full23[8:]}"


def company_reg(rnd: random.Random) -> str:
    return f"{rnd.choice(['01', '02', '05', '08', '09', '13', '14'])}-{rnd.choice(['09', '06'])}-{rnd.randint(100000, 999999)}"


def company(rnd: random.Random) -> str:
    if rnd.random() < 0.25:
        return f"{rnd.choice(SURNAMES)} és Társa {rnd.choice(['Bt.', 'Kft.'])}"
    return f"{rnd.choice(NAME_ROOTS)} {rnd.choice(ACTIVITIES)} {rnd.choice(FORMS)}"


def address(rnd: random.Random) -> str:
    city, pc = rnd.choice(CITIES)
    return f"{pc} {city}, {rnd.choice(STREETS)} {rnd.randint(1, 120)}."


def weighted(rnd: random.Random, d: dict) -> str:
    return rnd.choices(list(d), weights=list(d.values()))[0]


# --- formázás -----------------------------------------------------------------------------------------------------------

AMOUNT_FMT = {
    "szokoz_ft": lambda n: f"{n:,}".replace(",", " ") + " Ft",
    "pont_ft": lambda n: f"{n:,}".replace(",", ".") + ",- Ft",
    "huf": lambda n: f"{n} HUF",
    "szokoz_00": lambda n: f"{n:,}".replace(",", " ") + ",00",
}
DATE_FMT = {
    "pontos": lambda d: f"{d.year}.{d.month:02d}.{d.day:02d}.",
    "szoveges": lambda d: f"{d.year}. {MONTHS[d.month - 1]} {d.day}.",
    "iso": lambda d: d.isoformat(),
    "szokozos": lambda d: f"{d.year}. {d.month:02d}. {d.day:02d}.",
}


def vat_of(net: int, rate: str) -> int:
    return 0 if rate == "AAM" else (net * int(rate) + 50) // 100


def rate_txt(rate: str, ocr: bool) -> str:
    return "AAM" if rate == "AAM" else (f"{rate} %" if ocr else f"{rate}%")


# --- dokumentum ---------------------------------------------------------------------------------------------------------


def make_doc(rnd: random.Random, n_lines: tuple[int, int]) -> dict:
    lo, hi = SPEC["dokumentum"]["datum_tartomany"]
    d0, d1 = dt.date.fromisoformat(lo), dt.date.fromisoformat(hi)
    issue = d0 + dt.timedelta(days=rnd.randint(0, (d1 - d0).days))
    supply = issue - dt.timedelta(days=rnd.choice([0, 0, 1, 2, 3, 5, 7, 10]))
    days = rnd.choice(SPEC["dokumentum"]["fizetesi_napok"])
    order_date = supply - dt.timedelta(days=rnd.randint(1, 20))
    lines = []
    for desc, unit, (plo, phi), (qlo, qhi) in rnd.sample(PRODUCTS, rnd.randint(*n_lines)):
        qty, price = rnd.randint(qlo, qhi), rnd.randint(plo, phi)
        if price > 1000:
            price = price // 10 * 10
        rate = weighted(rnd, VAT_RATES)
        net = qty * price
        vat = vat_of(net, rate)
        lines.append({"desc": desc, "unit": unit, "qty": qty, "price": price, "rate": rate, "net": net, "vat": vat,
                      "gross": net + vat})
    year = issue.year
    return {
        "layout": rnd.choice(SPEC["dokumentum"]["elrendezesek"]), "amount_fmt": rnd.choice(list(AMOUNT_FMT)),
        "date_fmt": rnd.choice(list(DATE_FMT)),
        "seller": {"name": company(rnd), "addr": address(rnd), "tax": tax_number(rnd), "bank": bank_account(rnd),
                   "reg": company_reg(rnd)},
        "buyer": {"name": company(rnd), "addr": address(rnd), "tax": tax_number(rnd)},
        "invoice_no": rnd.choice([f"SZ-{year}/{rnd.randint(1, 99999):05d}", f"KV{year}-{rnd.randint(1, 9999):04d}",
                                  f"E-{rnd.randint(100, 999)}-{year}-{rnd.randint(1, 999999):06d}"]),
        "order_no": rnd.choice([f"R-{year}-{rnd.randint(1, 9999):04d}", f"MR{rnd.randint(1, 999999):06d}"]),
        "issue": issue, "supply": supply, "due": issue + dt.timedelta(days=days), "days": days, "order_date": order_date,
        "method": weighted(rnd, SPEC["dokumentum"]["fizetesi_mod"]), "lines": lines,
    }


def render(doc: dict, show: dict) -> str:
    """show: melyik elem látszik (seller_tax, buyer_tax, invoice_no, bank, supply, due, terms, vat_col, rates,
    gross_col, totals_vat, totals_gross). A `disp` a megjelenített (esetleg hibás) értékeket tartja."""
    A, D = AMOUNT_FMT[doc["amount_fmt"]], DATE_FMT[doc["date_fmt"]]
    s, b, disp, lay = doc["seller"], doc["buyer"], doc["disp"], doc["layout"]
    terms = f"átutalás, a számla keltétől számított {doc['days']} naptári napon belül"
    method = terms if show["terms"] else doc["method"]
    out = []
    if lay == "tablazatos":
        out += ["SZÁMLA"] + ([f"Sorszám: {doc['invoice_no']}"] if show["invoice_no"] else []) + [""]
        out += [f"Eladó: {s['name']}", f"Cím: {s['addr']}"] + ([f"Adószám: {s['tax']}"] if show["seller_tax"] else [])
        out += [f"Cégjegyzékszám: {s['reg']}"] + ([f"Bankszámlaszám: {s['bank']}"] if show["bank"] else []) + [""]
        out += [f"Vevő: {b['name']}", f"Cím: {b['addr']}"] + ([f"Adószám: {b['tax']}"] if show["buyer_tax"] else []) + [""]
        out += [f"Számla kelte: {D(doc['issue'])}"] + ([f"Teljesítés dátuma: {D(doc['supply'])}"] if show["supply"] else [])
        out += ([f"Fizetési határidő: {D(doc['due'])}"] if show["due"] else []) + [f"Fizetési mód: {method}"]
        out += [f"Megrendelés: {doc['order_no']} ({D(doc['order_date'])})", "", "Tételek:"]
        head = ["#", "Megnevezés", "Mennyiség", "Egységár", "Nettó"] + (["ÁFA-kulcs"] if show["rates"] else []) + \
               (["ÁFA"] if show["vat_col"] else []) + (["Bruttó"] if show["gross_col"] else [])
        out.append(" | ".join(head))
        for i, (ln, dl) in enumerate(zip(doc["lines"], disp["lines"]), 1):
            row = [str(i), ln["desc"], f"{ln['qty']} {ln['unit']}", A(ln["price"]), A(dl["net"])]
            row += ([rate_txt(ln["rate"], False)] if show["rates"] else []) + ([A(dl["vat"])] if show["vat_col"] else [])
            row += [A(dl["gross"])] if show["gross_col"] else []
            out.append(" | ".join(row))
        out += ["", f"Nettó összesen: {A(disp['net'])}"] + ([f"ÁFA összesen: {A(disp['vat'])}"] if show["totals_vat"] else [])
        out += [f"Bruttó végösszeg: {A(disp['gross'])}"] if show["totals_gross"] else []
    elif lay == "folyoszoveg":
        out.append("Számla" + (f" (sorszám: {doc['invoice_no']})" if show["invoice_no"] else ""))
        out.append(f"Kiállító: {s['name']}, {s['addr']}" + (f"; adószám: {s['tax']}" if show["seller_tax"] else "")
                   + f"; cégjegyzékszám: {s['reg']}" + (f"; bankszámla: {s['bank']}" if show["bank"] else "") + ".")
        out.append(f"Vevő: {b['name']}, {b['addr']}" + (f"; adószám: {b['tax']}" if show["buyer_tax"] else "") + ".")
        dot = lambda t: t if t.endswith(".") else t + "."  # noqa: E731  (a pontos dátumformák után nincs második pont)
        dates = [dot(f"Kelt: {D(doc['issue'])}")] + ([dot(f"Teljesítés: {D(doc['supply'])}")] if show["supply"] else [])
        dates += [dot(f"Fizetési határidő: {D(doc['due'])}")] if show["due"] else []
        out.append(" ".join(dates) + f" Fizetés módja: {method}.")
        out.append(f"Megrendelésszám: {doc['order_no']}, kelte {D(doc['order_date'])}")
        out.append("Tételek:")
        for i, (ln, dl) in enumerate(zip(doc["lines"], disp["lines"]), 1):
            t = f"{i}. {ln['desc']}: {ln['qty']} {ln['unit']} × {A(ln['price'])} = {A(dl['net'])} nettó"
            if show["rates"]:
                t += f", ÁFA-kulcs {rate_txt(ln['rate'], False)}"
            if show["vat_col"]:
                t += f", ÁFA {A(dl['vat'])}"
            if show["gross_col"]:
                t += f", bruttó {A(dl['gross'])}"
            out.append(t if t.endswith(".") else t + ".")
        tot = [f"nettó {A(disp['net'])}"] + ([f"ÁFA {A(disp['vat'])}"] if show["totals_vat"] else [])
        tot += [f"fizetendő bruttó {A(disp['gross'])}"] if show["totals_gross"] else []
        out.append("Összesen: " + ", ".join(tot) + ".")
    else:  # ocr
        out.append("SZAMLA" + (f"  SZAMLASZAM: {doc['invoice_no']}" if show["invoice_no"] else ""))
        out.append(f"SZALLITO: {s['name'].upper()}  {s['addr']}" + (f"  ADOSZ.: {s['tax']}" if show["seller_tax"] else "")
                   + f"  CG.: {s['reg']}" + (f"  BSZ: {s['bank']}" if show["bank"] else ""))
        out.append(f"VEVO: {b['name'].upper()}  {b['addr']}" + (f"  ADOSZ.: {b['tax']}" if show["buyer_tax"] else ""))
        out.append(f"KELT: {D(doc['issue'])}" + (f"  TELJ.: {D(doc['supply'])}" if show["supply"] else "")
                   + (f"  ESED.: {D(doc['due'])}" if show["due"] else "") + f"  FIZ.MOD: {method}")
        out.append(f"REND.SZ.: {doc['order_no']}  {D(doc['order_date'])}")
        for ln, dl in zip(doc["lines"], disp["lines"]):
            row = [ln["desc"], f"{ln['qty']}{ln['unit']}", A(ln["price"]), A(dl["net"])]
            row += ([rate_txt(ln["rate"], True)] if show["rates"] else []) + ([A(dl["vat"])] if show["vat_col"] else [])
            row += [A(dl["gross"])] if show["gross_col"] else []
            out.append("  ".join(row))
        tot = [f"NETTO: {A(disp['net'])}"] + ([f"AFA: {A(disp['vat'])}"] if show["totals_vat"] else [])
        tot += [f"BRUTTO: {A(disp['gross'])}"] if show["totals_gross"] else []
        out.append("  ".join(tot))
    return "\n".join(out)


FULL_SHOW = dict.fromkeys(["seller_tax", "buyer_tax", "invoice_no", "bank", "supply", "due", "rates", "vat_col",
                           "gross_col", "totals_vat", "totals_gross"], True) | {"terms": False}


def true_disp(doc: dict) -> dict:
    lines = [{k: ln[k] for k in ("net", "vat", "gross")} for ln in doc["lines"]]
    return {"lines": lines, "net": sum(x["net"] for x in lines), "vat": sum(x["vat"] for x in lines),
            "gross": sum(x["gross"] for x in lines)}


def perturb(rnd: random.Random, v: int, lo: float, hi: float) -> int:
    """v ± (lo–hi)·v, legalább 10; ha v 10-zel osztható, az eltérés is (különben az utolsó számjegy elárulná)."""
    step = 10 if v % 10 == 0 else 1
    for _ in range(100):
        d = max(10, round(v * rnd.uniform(lo, hi) / step) * step)
        w = v + d if rnd.random() < 0.5 or v - d <= 0 else v - d
        if w > 0 and w != v:
            return w
    return v + 10


def near_miss(rnd: random.Random, s: str) -> str:
    idx = [i for i, c in enumerate(s) if c.isdigit()]
    for _ in range(100):
        if rnd.random() < 0.5:
            i = rnd.choice(idx[:-1])
            j = next((k for k in idx if k > i), None)
            if j is not None and s[i] != s[j]:
                t = list(s)
                t[i], t[j] = t[j], t[i]
                return "".join(t)
        else:
            i = rnd.choice(idx)
            t = list(s)
            t[i] = rnd.choice([c for c in "0123456789" if c != s[i]])
            return "".join(t)
    raise RuntimeError("near_miss")


# --- kérdéstípusok ------------------------------------------------------------------------------------------------------


def options(rnd: random.Random, texts: list[str], gold_text: str | None) -> tuple[list[dict], str | None]:
    texts = list(dict.fromkeys(texts))
    rnd.shuffle(texts)
    opts = [{"id": f"o{i + 1}", "text": t} for i, t in enumerate(texts)]
    return opts, next((o["id"] for o in opts if o["text"] == gold_text), None)


def q_hibas_sor(rnd, doc, x):
    disp, show = true_disp(doc), dict(FULL_SHOW)
    bad = None
    if not x:
        bad = rnd.randrange(len(doc["lines"]))
        f = rnd.choice(["net", "vat", "gross"])
        v = disp["lines"][bad][f]
        disp["lines"][bad][f] = perturb(rnd, v, 0.01, 0.30) if v else rnd.choice([10, 20, 50, 100, 500])
    doc["disp"] = disp
    texts = [f"{i}. sor: {ln['desc']}" for i, ln in enumerate(doc["lines"], 1)]
    opts, gold = options(rnd, texts, None if bad is None else texts[bad])
    return show, SPEC["csaladok"]["kie.osszeg"]["kerdesek"]["hibas_sor"]["kerdes"], "choice", opts, gold, "natural"


def q_vegosszeg(rnd, doc, x):
    disp, show = true_disp(doc), dict(FULL_SHOW)
    wrong = rnd.random() < SPEC["csaladok"]["kie.osszeg"]["kerdesek"]["vegosszeg"]["hiba"]["arany"]
    if wrong:
        disp["gross"] = perturb(rnd, disp["gross"], 0.01, 0.20)
    doc["disp"] = disp
    return show, SPEC["csaladok"]["kie.osszeg"]["kerdesek"]["vegosszeg"]["kerdes"], "noul", noul_options("hu"), \
        ("nem" if wrong else "igen"), None


def q_afa_osszesen(rnd, doc, x):
    disp = true_disp(doc)
    doc["disp"] = disp
    show = dict(FULL_SHOW) | {"vat_col": False, "gross_col": False, "totals_vat": False, "totals_gross": False,
                              "rates": not x}
    A = AMOUNT_FMT[doc["amount_fmt"]]
    true_vat = disp["vat"]
    all27 = sum(vat_of(ln["net"], "27") for ln in doc["lines"])
    unrounded = int(sum(ln["net"] * (0 if ln["rate"] == "AAM" else int(ln["rate"])) / 100 for ln in doc["lines"]))
    cands = [disp["net"], disp["net"] + true_vat, all27, unrounded, round(true_vat * 1.1) + 10, max(10, round(true_vat * 0.9) - 10)]
    cands = [c for c in dict.fromkeys(cands) if c != true_vat]
    rnd.shuffle(cands)
    k = rnd.randint(2 if x else 1, min(5, len(cands)))
    texts = [A(c) for c in cands[:k]] + ([] if x else [A(true_vat)])
    opts, gold = options(rnd, texts, None if x else A(true_vat))
    return show, SPEC["csaladok"]["kie.osszeg"]["kerdesek"]["afa_osszesen"]["kerdes"], "choice", opts, gold, \
        "missing-precondition"


def q_hatarido_szamolt(rnd, doc, x):
    doc["method"] = "átutalás"
    doc["disp"] = true_disp(doc)
    show = dict(FULL_SHOW) | {"due": False, "terms": not x}
    D = DATE_FMT[doc["date_fmt"]]
    n, iss, sup = doc["days"], doc["issue"], doc["supply"]
    gold_d = iss + dt.timedelta(days=n)
    cands = [sup + dt.timedelta(days=n), gold_d + dt.timedelta(days=1), gold_d - dt.timedelta(days=1), iss, sup,
             iss + dt.timedelta(days=rnd.choice([d for d in SPEC["dokumentum"]["fizetesi_napok"] if d != n]))]
    cands = [c for c in dict.fromkeys(cands) if c != gold_d]
    if x:
        cands = [c for c in cands if c != iss + dt.timedelta(days=30)]
    rnd.shuffle(cands)
    k = rnd.randint(2 if x else 1, min(5, len(cands)))
    texts = [D(c) for c in cands[:k]] + ([] if x else [D(gold_d)])
    opts, gold = options(rnd, texts, None if x else D(gold_d))
    return show, SPEC["csaladok"]["kie.datum"]["kerdesek"]["hatarido_szamolt"]["kerdes"], "choice", opts, gold, \
        "missing-precondition"


def q_kesedelem(rnd, doc, x):
    doc["disp"] = true_disp(doc)
    show = dict(FULL_SHOW)
    k = rnd.choice([-7, -5, -3, -2, -1, 0, 0]) if rnd.random() < 0.5 else rnd.randint(1, 12)
    pay = doc["due"] + dt.timedelta(days=k)
    doc["pay"] = pay
    q = SPEC["csaladok"]["kie.datum"]["kerdesek"]["kesedelem"]["kerdes"].replace("{datum}", DATE_FMT[doc["date_fmt"]](pay))
    return show, q, "noul", noul_options("hu"), ("igen" if k > 0 else "nem"), None


def q_teljesites_datuma(rnd, doc, x):
    doc["disp"] = true_disp(doc)
    show = dict(FULL_SHOW) | {"supply": not x}
    D = DATE_FMT[doc["date_fmt"]]
    dates = [doc["issue"], doc["due"], doc["order_date"]] + ([] if x else [doc["supply"]])
    texts = [D(d) for d in dict.fromkeys(dates)]
    opts, gold = options(rnd, texts, None if x else D(doc["supply"]))
    return show, SPEC["csaladok"]["kie.datum"]["kerdesek"]["teljesites_datuma"]["kerdes"], "choice", opts, gold, \
        "missing-precondition"


# mező → (kérdésbeli alak névelővel, névelő nélküli alak, kiolvasó)
FIELDS = {"seller_tax": ("az eladó adószáma", "eladó adószáma", lambda d: d["seller"]["tax"]),
          "buyer_tax": ("a vevő adószáma", "vevő adószáma", lambda d: d["buyer"]["tax"]),
          "invoice_no": ("a számla sorszáma", "számla sorszáma", lambda d: d["invoice_no"]),
          "bank": ("az eladó bankszámlaszáma", "eladó bankszámlaszáma", lambda d: d["seller"]["bank"])}


def ids_of(doc: dict, show: dict) -> dict:
    v = {"seller_tax": doc["seller"]["tax"], "buyer_tax": doc["buyer"]["tax"], "invoice_no": doc["invoice_no"],
         "bank": doc["seller"]["bank"], "order_no": doc["order_no"], "reg": doc["seller"]["reg"]}
    return {k: x for k, x in v.items() if show.get(k, True)}


def q_mezo_valasztas(rnd, doc, x):
    doc["disp"] = true_disp(doc)
    field = rnd.choice(list(FIELDS))
    show = dict(FULL_SHOW) | {field: not x}
    doc["field"] = field
    label, _, get = FIELDS[field]
    present = ids_of(doc, show)
    others = [v for k, v in present.items() if k != field]
    rnd.shuffle(others)
    k = rnd.randint(2 if x else 1, min(5, len(others)))
    texts = others[:k]
    if not x and rnd.random() < 0.5:
        texts.append(near_miss(rnd, get(doc)))
    texts += [] if x else [get(doc)]
    opts, gold = options(rnd, texts, None if x else get(doc))
    q = SPEC["csaladok"]["kie.mezo"]["kerdesek"]["mezo_valasztas"]["kerdes"].replace("{mezo}", label)
    return show, q, "choice", opts, gold, "missing-precondition"


def q_kinyert_ertek(rnd, doc, x):
    doc["disp"] = true_disp(doc)
    field = rnd.choice(list(FIELDS))
    doc["field"] = field
    _, label, get = FIELDS[field]
    true_v = get(doc)
    wrong = rnd.random() < SPEC["csaladok"]["kie.mezo"]["kerdesek"]["kinyert_ertek"]["hiba"]["arany"]
    if wrong:
        alt = {"seller_tax": doc["buyer"]["tax"], "buyer_tax": doc["seller"]["tax"]}.get(field)
        v = alt if alt and rnd.random() < 0.3 else near_miss(rnd, true_v)
    else:
        v = true_v
    doc["claimed"] = v
    q = SPEC["csaladok"]["kie.mezo"]["kerdesek"]["kinyert_ertek"]["kerdes"].replace("{mezo}", label).replace("{ertek}", v)
    return dict(FULL_SHOW), q, "noul", noul_options("hu"), ("nem" if wrong else "igen"), None


QTYPES = {"kie.osszeg": {"hibas_sor": q_hibas_sor, "vegosszeg": q_vegosszeg, "afa_osszesen": q_afa_osszesen},
          "kie.datum": {"hatarido_szamolt": q_hatarido_szamolt, "kesedelem": q_kesedelem,
                        "teljesites_datuma": q_teljesites_datuma},
          "kie.mezo": {"mezo_valasztas": q_mezo_valasztas, "kinyert_ertek": q_kinyert_ertek}}


def meta_of(doc: dict, show: dict, qtype: str) -> dict:
    """A test_kie03 független ellenőrzéséhez: a megjelenített értékek (formázatlanul) és a láthatóság."""
    D = DATE_FMT[doc["date_fmt"]]
    m = {"qtype": qtype, "layout": doc["layout"], "amount_fmt": doc["amount_fmt"], "date_fmt": doc["date_fmt"],
         "show": show, "lines": [{"qty": ln["qty"], "price": ln["price"], "rate": ln["rate"], **dl}
                                 for ln, dl in zip(doc["lines"], doc["disp"]["lines"])],
         "totals": {k: doc["disp"][k] for k in ("net", "vat", "gross")},
         "dates": {k: D(doc[k]) for k in ("issue", "supply", "due", "order_date")}, "days": doc["days"],
         "ids": {k: v for k, v in ids_of(doc, FULL_SHOW).items()}}
    for k in ("field", "claimed"):
        if k in doc:
            m[k] = doc[k]
    if "pay" in doc:
        m["pay"] = D(doc["pay"])
    return m


def generate() -> list[dict]:
    rows = []
    for fam, fspec in SPEC["csaladok"].items():
        qspecs = fspec["kerdesek"]
        names = list(qspecs)
        for i in range(fspec["n"]):
            rnd = random.Random(f"{SPEC['seed']}:{fam}:{i}")
            qtype = rnd.choices(names, weights=[qspecs[n]["arany"] for n in names])[0]
            xspec = qspecs[qtype].get("x")
            x = bool(xspec) and rnd.random() < xspec["arany"]
            lo_lines = 2 if qtype == "hibas_sor" else 1
            doc = make_doc(rnd, (max(lo_lines, SPEC["dokumentum"]["tetelszam"][0]), SPEC["dokumentum"]["tetelszam"][1]))
            if qtype == "teljesites_datuma":  # minden dátum különbözzön: rendelés < teljesítés < kelte < határidő
                doc["supply"] = doc["issue"] - dt.timedelta(days=rnd.randint(1, 10))
                doc["order_date"] = doc["supply"] - dt.timedelta(days=rnd.randint(1, 20))
            show, question, kind, opts, gold, xt = QTYPES[fam][qtype](rnd, doc, x)
            state = render(doc, show)
            iid = f"{fam}:{qtype}:{i:04d}"
            rows.append({"id": iid, "family": fam, "group": SPEC["group"], "source": "kie03 (szintetikus)",
                         "source_license": SPEC["license"], "source_ref": f"{qtype}:{i}", "split": SPEC["split"],
                         "group_id": iid, "lang": "hu", "kind": kind, "state": state, "question": question,
                         "options": opts, "gold": gold, "x_type": xt if gold is None else None, "ketertelmu": False,
                         "soft": None, "meta": {"kie": meta_of(doc, show, qtype)}})
    order = sorted(rows, key=lambda r: hashlib.sha256(f"{SPEC['seed']}:kal:{r['id']}".encode()).hexdigest())
    calib = {r["id"] for r in order[: SPEC["kalibracio_n"]]}
    for r in rows:
        r["meta"]["kalibracio"] = r["id"] in calib
    return rows


def main() -> None:
    rows = generate()
    bad = [(r["id"], e) for r in rows if (e := validate(r))]
    if bad:
        raise SystemExit(f"{len(bad)} sémahiba, pl. {bad[:3]}")
    rep = {}
    for fam in SPEC["csaladok"]:
        rs = [r for r in rows if r["family"] == fam]
        (OUT / f"{fam}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rs), encoding="utf-8")
        rep[fam] = {"n": len(rs), "kerdes": dict(Counter(r["meta"]["kie"]["qtype"] for r in rs)),
                    "x": dict(Counter(r["x_type"] for r in rs if r["gold"] is None)),
                    "noul_igen": sum(r["gold"] == "igen" for r in rs), "noul_nem": sum(r["gold"] == "nem" for r in rs),
                    "elrendezes": dict(Counter(r["meta"]["kie"]["layout"] for r in rs)),
                    "kalibracio": sum(r["meta"]["kalibracio"] for r in rs),
                    "sha256": hashlib.sha256("".join(json.dumps(r, ensure_ascii=False) for r in rs).encode()).hexdigest()}
        print(fam, json.dumps(rep[fam], ensure_ascii=False))
    (OUT / "kie03_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
