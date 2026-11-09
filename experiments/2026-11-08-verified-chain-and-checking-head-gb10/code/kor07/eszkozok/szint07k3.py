"""07 — a nehéz próbaminta 3. köre (07-runbook 3.3, D11). JAVASLAT: a konstrukció Dani döntése; GPU-s generálás csak
az ő jóváhagyása után. A `szint07` és a `szint06` burkolója (mindkettő a 07 v1 manifestjében, nem módosul).

Az 1–2. kör tanulsága: a B1 a számokat pontosan olvassa, a számszerű közelség (egy jegy, 1–3%) nem nehezít. A 3. körben
a döntő részlet a szövegben van, de egy következtetési lépés kell hozzá (váltás, arány, áfa, árfolyam); a csali az a
jelölt, amelyet a felszíni egyezés (pontos összeg, nyers számösszevetés) adna. A gold a tervből gépileg következik.

Változatok (családonként 120 terv, a sablonon belüli sorszám párossága szerint 60–60):
  bank  B3a részfizetés  a tétel a cél számla bruttójának 30, 40 vagy 50%-a; a szövegben a partner és az arány
                         (számlaszám nincs); csali: ugyanannál a partnernél, ugyanazzal az esedékességgel az a számla,
                         amelynek bruttója pontosan a tétel összege
        B3b betűvel      az összeg csak betűvel szerepel, a partnerrel; csali: ugyanannál a partnernél a 2. kör
                         összeg-ikre (két szomszédos jegy felcserélve vagy 0,5–3%)
  hiba  H3 váltás        a két jelölt ok mérése más egységben szerepel, mint a szabályban (szorzós váltás: V ↔ mV,
                         bar ↔ kPa, mm ↔ µm …; hőmérséklet nincs, mert a sablonokban sok a különbség-mérés);
                         az egység úgy választva, hogy a nyers számösszevetés a csalit adja: a valódi ok mérése felszínen
                         nem teljesül, a páré felszínen igen; zajmérés nincs
  szab. S3a nettó        minden szabálypont küszöbe nettó; a kérelemben a bruttó összeg az áfakulccsal (hu 27%, en 20%);
                         a nettó a küszöb alatt, a bruttó fölötte (gold: alsó sáv; a felszíni olvasás a felsőt adja)
        S3b deviza       az összeg devizában az árfolyammal (hu: EUR, Ft/EUR; en: GBP, EUR/GBP); az átszámított érték a
                         küszöb fölött, a devizás szám alatta (gold: felső sáv; a felszíni olvasás az alsót adja)
A S3a és a S3b goldja ellentétes sávban van, így a sáv önmagában nem árulja el a választ.

Kimenet: kor07/adat/nehez3/{terv,raw,items}/<család>.jsonl (split NEHEZ), mint a szint07 1–2. köre.
  terv   --csalad F            a tervek (CPU)
  minta  [--n 2]               változatonként n hu + n en mintaprompt → kor07/adat/nehez3/minta_promptok.md (CPU)
  onteszt                      a tényellenőrző önellenőrzése kézzel írt jó / rossz szövegeken (CPU)
  gen    --csalad F --url U --model M [--extra J] [--workers N]     (GPU: Muse; csak Dani jóváhagyása után)
  final  --csalad F
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor06/eszkozok")]
import szint06 as S  # noqa: E402
import szint07 as S7  # noqa: E402

ORIG_GEN, ORIG_FC = S.gen_prompt, S.fact_check
AFA = {"hu": 27, "en": 20}

# --- számok betűvel ------------------------------------------------------------------------------------------------

HU_E = ["", "egy", "kettő", "három", "négy", "öt", "hat", "hét", "nyolc", "kilenc"]
HU_EK = ["", "egy", "két", "három", "négy", "öt", "hat", "hét", "nyolc", "kilenc"]  # összetételben (kétezer, kétszáz)
HU_T = ["", "tíz", "húsz", "harminc", "negyven", "ötven", "hatvan", "hetven", "nyolcvan", "kilencven"]
HU_TP = ["", "tizen", "huszon", "harminc", "negyven", "ötven", "hatvan", "hetven", "nyolcvan", "kilencven"]


def _hu999(n: int, osszetett: bool) -> str:
    sz, r = divmod(n, 100)
    t, e = divmod(r, 10)
    s = ("" if sz == 0 else ("" if sz == 1 else HU_EK[sz]) + "száz")
    s += HU_T[t] if e == 0 else HU_TP[t]
    return s + (HU_EK[e] if osszetett else HU_E[e])


def hu_betuvel(n: int) -> str:
    """Magyar helyesírás: 2000-ig egybe, fölötte a hármas csoportok közt kötőjel (ötvennyolcezer-kilencszázötven)."""
    if n == 0:
        return "nulla"
    m, r = divmod(n, 10 ** 6)
    e, r = divmod(r, 1000)
    reszek = ([_hu999(m, True) + "millió"] if m else []) + ([("" if e == 1 else _hu999(e, True)) + "ezer"] if e else []) + (
        [_hu999(r, False)] if r else [])
    return ("" if n <= 2000 else "-").join(reszek)


EN_E = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen",
        "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
EN_T = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _en999(n: int) -> str:
    sz, r = divmod(n, 100)
    out = [f"{EN_E[sz]} hundred"] if sz else []
    if r:
        out.append(EN_E[r] if r < 20 else EN_T[r // 10] + (f"-{EN_E[r % 10]}" if r % 10 else ""))
    return " ".join(out)


def en_betuvel(n: int) -> str:
    if n == 0:
        return "zero"
    m, r = divmod(n, 10 ** 6)
    e, r = divmod(r, 1000)
    return " ".join([f"{_en999(m)} million"] * bool(m) + [f"{_en999(e)} thousand"] * bool(e) + [_en999(r)] * bool(r))


def osszeg_betuvel(osszeg: int, lang: str) -> str:
    """hu: egész forint; en: centben tárolt euró."""
    if lang == "hu":
        return f"{hu_betuvel(osszeg)} forint"
    eu, c = divmod(osszeg, 100)
    return f"{en_betuvel(eu)} euros" + (f" and {en_betuvel(c)} cents" if c else "")


def _szo_norm(s: str) -> str:
    return re.sub(r"[\s\-‐‑–]+", "", s.lower())


# --- mértékegység-váltás (H3) --------------------------------------------------------------------------------------

def _sk(f: float):
    return (lambda v: v * f), (lambda v: v / f)


VALTAS: dict[str, list[tuple[str, tuple]]] = {
    "V": [("mV", _sk(1000)), ("kV", _sk(0.001))], "volt": [("mV", _sk(1000)), ("kV", _sk(0.001))],
    "mV": [("V", _sk(0.001)), ("µV", _sk(1000))],
    "A": [("mA", _sk(1000))], "mA": [("A", _sk(0.001)), ("µA", _sk(1000))],
    "bar": [("mbar", _sk(1000)), ("kPa", _sk(100)), ("MPa", _sk(0.1))],
    "mbar": [("bar", _sk(0.001)), ("Pa", _sk(100))],
    "kPa": [("Pa", _sk(1000)), ("bar", _sk(0.01)), ("MPa", _sk(0.001))],
    "Pa": [("kPa", _sk(0.001)), ("mbar", _sk(0.01))],
    "mm": [("µm", _sk(1000)), ("m", _sk(0.001))],
    "mm/s": [("µm/s", _sk(1000)), ("m/s", _sk(0.001))],
    "m/s": [("mm/s", _sk(1000)), ("km/h", _sk(3.6))],
    "ms": [("µs", _sk(1000)), ("s", _sk(0.001))],
    "s": [("ms", _sk(1000)), ("min", _sk(1 / 60))],
    "ohm": [("mOhm", _sk(1000)), ("kOhm", _sk(0.001))], "Ω": [("mΩ", _sk(1000)), ("kΩ", _sk(0.001))],
    "mOhm": [("ohm", _sk(0.001))], "mΩ": [("Ω", _sk(0.001))],
    "Hz": [("kHz", _sk(0.001)), ("rpm", _sk(60))], "rpm": [("Hz", _sk(1 / 60))],
    "L/min": [("L/h", _sk(60)), ("m3/h", _sk(0.06))], "l/min": [("l/h", _sk(60)), ("m3/h", _sk(0.06))],
    "m3/h": [("L/min", _sk(1000 / 60)), ("L/s", _sk(1000 / 3600))],
    "g/s": [("kg/h", _sk(3.6)), ("kg/s", _sk(0.001))],
    "RPM": [("Hz", _sk(1 / 60))], "Ohm": [("mOhm", _sk(1000)), ("kOhm", _sk(0.001))],
    "kΩ": [("Ω", _sk(1000)), ("MΩ", _sk(0.001))], "MΩ": [("kΩ", _sk(1000))],
    "m": [("mm", _sk(1000)), ("km", _sk(0.001))], "millivolt": [("volt", _sk(0.001))],
    "ampere": [("milliampere", _sk(1000))], "milliamper": [("amper", _sk(0.001))],
    "ml/min": [("l/h", _sk(0.06))], "second": [("milliseconds", _sk(1000))],
    "psi": [("bar", _sk(0.0689476)), ("kPa", _sk(6.89476))], "W": [("mW", _sk(1000)), ("kW", _sk(0.001))],
    "g": [("mg", _sk(1000)), ("kg", _sk(0.001))], "mg": [("g", _sk(0.001)), ("µg", _sk(1000))],
    "g/m3": [("mg/m3", _sk(1000))], "mg/m3": [("g/m3", _sk(0.001)), ("µg/m3", _sk(1000))],
    "ppm": [("%", _sk(0.0001))],
    # hőmérséklet szándékosan nincs: a sablonok mérései közt sok a különbség (túlhevülés, emelkedés, eltérés), ahol a
    # °C ↔ K eltolás értelmetlen, a szorzós váltásnál pedig a szám nem változik
}


def kerekit(v: float) -> float:
    """Három értékes jegy."""
    if v == 0:
        return 0.0
    return round(v, 2 - int(math.floor(math.log10(abs(v)))))


def teljesul(v: float, m: dict) -> bool:
    k = S._num(m["kuszob"])
    return v < k if m["relacio"] == "<" else v > k


def valtas(rnd: random.Random, m: dict, v: float, kell_valodi: bool) -> tuple[str, float] | None:
    """Egység, amelyben a v érték valódi teljesülése `kell_valodi`, a nyers (felszíni) összevetésé az ellenkezője."""
    jo = []
    for u2, (f, fi) in VALTAS.get(m["egyseg"].strip(), []):
        v2 = kerekit(f(v))
        if teljesul(fi(v2), m) == kell_valodi and teljesul(v2, m) != kell_valodi and v2 != S._num(m["kuszob"]):
            jo.append((u2, v2))
    return rnd.choice(jo) if jo else None


# --- tervek --------------------------------------------------------------------------------------------------------

def valtozat(fam: str, seq: int) -> str:
    return {"penzugy.bankparositas": ("B3a-reszfizetes", "B3b-betuvel"), "muszaki.hibaelharitas": ("H3-valtas", "H3-valtas"),
            "szabaly.koltsegelszamolas": ("S3a-netto", "S3b-deviza")}[fam][seq % 2]


def plan3(fam: str, sab: dict, seq: int) -> dict:
    rnd = S.rnd_for("nehez3", sab["sablon_id"], seq)
    lang = sab["lang"]
    v = valtozat(fam, seq)
    p = {"csalad": fam, "sablon_id": sab["sablon_id"], "lang": lang, "allapot": "MATCH", "szelet": S7.SZELET,
         "dim": {k: rnd.choice(x)[S.LANGS.index(lang)] for k, x in S.DIM[fam].items()}}
    k = rnd.randint(S.K["opciok"]["min"], S.K["opciok"]["max"])
    if fam == "penzugy.bankparositas":
        inv = sab["szamlak"]
        foglalt = {s["osszeg"] for s in inv}
        szamok = {s["szamlaszam"] for s in inv}
        if v == "B3a-reszfizetes":
            target, arany, a = inv[0], 0, 0
            for _ in range(100):
                target, arany = rnd.choice(inv), rnd.choice((30, 40, 50))
                a = round(target["osszeg"] * arany / 100)
                masik = [s for s in inv if s is not target]
                # egyértelmű: a tétel összege más számla bruttójával és más számla 30 / 40 / 50%-ával sem egyezik
                if a not in foglalt and not any(abs(s["osszeg"] * r / 100 - a) < 1 for s in masik for r in (30, 40, 50)):
                    break
            else:
                raise SystemExit(f"{sab['sablon_id']}: nincs egyértelmű részfizetés")
            uj, _ = S7.iker_szam(rnd, target["szamlaszam"], szamok)
            csali = {**target, "id": "s_csali", "szamlaszam": uj, "osszeg": a}
            p["nehez"] = {"valt": v, "arany": arany, "teljes": target["osszeg"]}
            tenyek = {"osszeg": a, "partner": target["partner"], "reszlet": arany}
        else:
            target = rnd.choice(inv)
            uj_o, valt = S7.iker_osszeg(rnd, target["osszeg"], foglalt, lang)
            uj, _ = S7.iker_szam(rnd, target["szamlaszam"], szamok)
            csali = {**target, "id": "s_csali", "szamlaszam": uj, "osszeg": uj_o}
            p["nehez"] = {"valt": v, "iker": valt}
            tenyek = {"osszeg": target["osszeg"], "partner": target["partner"],
                      "betuvel": osszeg_betuvel(target["osszeg"], lang)}
        pool = [s for s in inv if s is not target]
        opts = [target, csali] + rnd.sample(pool, k - 2)
        p["tenyek"] = {**tenyek, "irany": rnd.choice(S.IRANY[lang]),
                       "datum": S.tx_date(rnd, [target["kelt"]] + [s["kelt"] for s in opts])}
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": s["id"], "text": f"{s['szamlaszam']} · {s['partner']} · {S.money(s['osszeg'], lang)} · "
                                                 f"{'esedékes' if lang == 'hu' else 'due'} {s['esedekes']}"} for s in opts]
        p["gold_sid"], p["sajat_ceg"] = target["id"], sab["ceg"]
    elif fam == "szabaly.koltsegelszamolas":
        pts = sab["pontok"]
        sav = 0 if v == "S3a-netto" else 1
        cel = [x for x in pts if x["sav"] == sav and any(y["tipus"] == x["tipus"] and y is not x for y in pts)]
        target = rnd.choice(cel)
        iker = next(y for y in pts if y["tipus"] == target["tipus"] and y is not target)
        rest = [x for x in pts if x not in (target, iker)]
        opts = [target, iker] + rnd.sample(rest, max(0, min(k, len(pts)) - 2))
        hatar = target["hatar"]
        if v == "S3a-netto":
            r = AFA[lang] / 100
            netto = brutto = 0
            for _ in range(100):
                netto = int(hatar * rnd.uniform(1 / (1 + r) + 0.02, 0.97))
                netto = netto // 10 * 10 if lang == "hu" else netto
                brutto = round(netto * (1 + r))
                if netto < hatar < brutto:
                    break
            else:
                raise SystemExit(f"{sab['sablon_id']}: nincs nettó / bruttó összeg a küszöb két oldalán")
            tenyek = {"osszeg": brutto, "netto": netto, "afa": AFA[lang]}
            szoveg = {x["id"]: netto_szoveg(x["szoveg"], lang) for x in opts}
        else:
            arf = rnd.randint(385, 410) if lang == "hu" else round(rnd.uniform(1.14, 1.19), 2)
            dev = 0
            for _ in range(100):
                dev = int(hatar / arf * rnd.uniform(1.04, 1.45)) if lang == "hu" else int(hatar / arf * rnd.uniform(1.02, arf * 0.97))
                if dev * arf > hatar and dev < hatar:
                    break
            else:
                raise SystemExit(f"{sab['sablon_id']}: nincs devizás összeg a küszöb két oldalán")
            tenyek = {"osszeg": dev, "arfolyam": arf, "deviza": "EUR" if lang == "hu" else "GBP", "atszamitva": dev * arf}
            szoveg = {x["id"]: x["szoveg"] for x in opts}
        p["tenyek"] = {"tipus": target["tipus"], "tipus_leiras": S.SZAB_TIPUS[lang][target["tipus"]],
                       "helyzet": rnd.choice(S.SZAB_HELYZET[lang][target["tipus"]]), **tenyek}
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": x["id"], "text": szoveg[x["id"]]} for x in opts]
        p["gold_sid"], p["szervezet"] = target["id"], sab["szervezet"]
        p["nehez"] = {"valt": v, "sav": sav}
    elif fam == "muszaki.hibaelharitas":
        groups = sab["tunetcsoportok"]
        okok = [(gi, oi, o) for gi, g in enumerate(groups) for oi, o in enumerate(g["okok"])]
        sid = lambda gi, oi: f"c{gi}{oi}"  # noqa: E731
        jelolt = [(gi, ti) for gi in range(4) for ti in range(2)]
        rnd.shuffle(jelolt)
        valasztas = None
        for gi, ti in jelolt:
            t, o = groups[gi]["okok"][ti], groups[gi]["okok"][1 - ti]
            vt = valtas(rnd, t["meres"], S._num(t["meres"]["ertek_ha_ez"]), True)
            vo = valtas(rnd, o["meres"], S._num(o["meres"]["ertek_normal"]), False)
            if vt and vo:
                valasztas = (gi, ti, t, o, vt, vo)
                break
        if valasztas is None:  # nincs alkalmas egység a sablonban: közölt kiesés, a terv nem készül
            return {"kimarad": True, "csalad": fam, "sablon_id": sab["sablon_id"], "lang": lang,
                    "nehez": {"valt": "H3-nincs-valtas"}}
        gi, ti, t, o, vt, vo = valasztas
        mer = [{"nev": t["meres"]["nev"], "ertek": S.fmt_num(vt[1], lang), "egyseg": vt[0], "eredeti": t["meres"]["egyseg"]},
               {"nev": o["meres"]["nev"], "ertek": S.fmt_num(vo[1], lang), "egyseg": vo[0], "eredeti": o["meres"]["egyseg"]}]
        rnd.shuffle(mer)
        a_, b_ = groups[gi]["okok"]
        others = [x for x in okok if x[0] != gi]
        opts = [(gi, 0, a_), (gi, 1, b_)] + rnd.sample(others, k - 2)
        rnd.shuffle(opts)
        p["berendezes"], p["modell"] = sab["berendezes"], sab["modell"]
        p["tenyek"] = {"tunet": groups[gi]["tunet"], "meresek": mer}
        p["opciok"] = [{"sid": sid(g, i), "nev": x["nev"], "text": f"{x['nev']} — {S.hiba_szabaly(x, groups[g]['tunet'], lang)}"}
                       for g, i, x in opts]
        p["gold_sid"], p["nehez"] = sid(gi, ti), {"valt": v, "egysegek": [vt[0], vo[0]]}
    else:
        raise SystemExit(f"ismeretlen család: {fam}")
    return p


NETTO_HU = [(re.compile(r"legfeljebb (\d[\d  ]*\s?Ft)"), r"legfeljebb nettó \1"),
            (re.compile(r"(\d[\d  ]*\s?Ft) felett"), r"nettó \1 felett")]
NETTO_EN = [(re.compile(r"(up to|above) (EUR [\d,]+)"), r"\1 \2 net of VAT")]


def netto_szoveg(s: str, lang: str) -> str:
    out = s
    for rx, rep in NETTO_HU if lang == "hu" else NETTO_EN:
        out = rx.sub(rep, out)
    if out == s:
        raise SystemExit(f"a szabálypont küszöbe nem jelölhető nettónak: {s}")
    return out


def cmd_terv(a) -> None:
    fam = a.csalad
    rows, kimarad = [], Counter()
    for lang in S.LANGS:
        sabs = sorted((s for s in S7.sablonok(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"])
        i = 0
        for sab in sabs:
            for j in range(a.per_sablon):
                p = plan3(fam, sab, j)
                if p.get("kimarad"):
                    kimarad[lang] += 1
                    continue
                gid = f"{fam}:{S7.SZELET}:{lang}:MATCH:{i:04d}"
                rows.append(p | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:nehez3:{gid}") % 10**12})
                i += 1
    S.jl_write(S7.path07("terv", fam), rows)
    print(f"{fam}: {len(rows)} nehéz terv (3. kör); " + ", ".join(f"{k}={n}" for k, n in sorted(Counter(r["nehez"]["valt"] for r in rows).items()))
          + (f"; egység híján kimaradt: {dict(kimarad)}" if kimarad else ""))


# --- generátor-utasítás és tényellenőrzés --------------------------------------------------------------------------

def _csere(s: str, regi: str, uj: str) -> str:
    if regi not in s:
        raise SystemExit(f"a szint06 utasítása nem a várt alakú (hiányzik: {regi!r})")
    return s.replace(regi, uj, 1)


def gen_prompt3(p: dict) -> str:
    s = ORIG_GEN(p)
    v, lang, t = p["nehez"]["valt"], p["lang"], p["tenyek"]
    hu = lang == "hu"
    if v == "B3a-reszfizetes":
        r = t["reszlet"]
        s = _csere(s, " A tétel egy számla kiegyenlítése." if hu else " It settles an invoice.",
                   (f" A tétel egy számla bruttó összegének {r}%-os részlete (részletfizetés vagy előleg); a szöveg mondja ki, "
                    f"hogy ez a számla {r}%-a. A számla teljes összegét ne írd le." if hu else
                    f" It is a {r}% instalment of one invoice's gross amount (part payment or advance); the text must state that "
                    f"it is {r}% of the invoice. Do not state the invoice's full amount."))
    elif v == "B3b-betuvel":
        m = S.money(t["osszeg"], lang)
        s = _csere(s, f"Összeg: {m}." if hu else f"Amount: {m}.",
                   (f"Összeg: csak betűvel, pontosan így: „{t['betuvel']}”; számjegyekkel ne írd le." if hu else
                    f"Amount: in words only, exactly: \"{t['betuvel']}\"; do not write it in digits."))
    elif v == "H3-valtas":
        s = _csere(s, " A hiba okát ne nevezd meg" if hu else " Do not name or guess the cause",
                   (" Minden értéket pontosan a megadott mértékegységben írj, átváltás és zárójeles átszámítás nélkül."
                    " A hiba okát ne nevezd meg" if hu else
                    " Give every value exactly in the stated unit, without converting it or adding a converted value in"
                    " brackets. Do not name or guess the cause"))
    elif v == "S3a-netto":
        m = S.money(t["osszeg"], lang)
        s = _csere(s, f" Összeg: {m}." if hu else f" Amount: EUR {t['osszeg']:,}.",
                   (f" Összeg: {m} bruttó, {t['afa']}% áfával; a szöveg mondja ki, hogy ez bruttó összeg, és az áfakulcsot. "
                    f"A nettó összeget ne számold ki és ne írd le." if hu else
                    f" Amount: EUR {t['osszeg']:,} gross, including {t['afa']}% VAT; the text must say that it is a gross amount "
                    f"and state the VAT rate. Do not compute or state the net amount."))
    elif v == "S3b-deviza":
        arf = f"{t['arfolyam']}" if hu else f"{t['arfolyam']:.2f}"
        s = _csere(s, f" Összeg: {S.money(t['osszeg'], lang)}." if hu else f" Amount: EUR {t['osszeg']:,}.",
                   (f" Összeg: {t['osszeg']} EUR (euróban fizetve); az elszámolási árfolyam {arf} Ft/EUR, ezt is írd bele. "
                    f"A forintösszeget ne számold ki és ne írd le." if hu else
                    f" Amount: GBP {t['osszeg']:,} (paid in pounds); the settlement rate is {arf} EUR/GBP, state it as well. "
                    f"Do not compute or state the euro amount."))
    return s


def _altalanos(p: dict, text: str) -> str | None:
    """A szint06 családfüggetlen ellenőrzései (nyelv, címkét kimondó fordulat, „a(z)”)."""
    if not S.lang_ok(text, p["lang"]):
        return "rossz nyelv"
    if any(x in text.lower() for x in S.LEAK[p["lang"]]):
        return "címkét kimondó fordulat"
    if "a(z)" in text.lower():
        return "„a(z)” a szövegben"
    return None


def _szam_jelen(text: str, n: float) -> bool:
    return any(x in S.norm_digits(text) for x in {str(int(n)), str(n).replace(".", ""), f"{n:.2f}".replace(".", "")})


def fact_check3(p: dict, text: str) -> str | None:
    v, t, lang = p["nehez"]["valt"], p["tenyek"], p["lang"]
    if v == "B3b-betuvel":  # a szint06 összeg-ellenőrzése számjegyet keres; itt a betűs alak a kötelező
        if (err := _altalanos(p, text)):
            return err
        if _szo_norm(t["betuvel"].rsplit(" ", 1)[0] if lang == "hu" else t["betuvel"]) not in _szo_norm(text):
            return "hiányzó betűs összeg"
        if any(x in S.norm_digits(text) for x in S.amount_forms(t["osszeg"], lang, cents=True)):
            return "az összeg számjegyekkel is szerepel"
        if t["datum"].replace("-", "") not in S.norm_date(text):
            return "hiányzó vagy eltérő dátum"
        if t["partner"].split()[0].lower() not in text.lower():
            return "hiányzó partner"
        return S.bank_idegen(p, text)
    if (err := ORIG_FC(p, text)):
        return err
    low = text.lower()
    if v == "B3a-reszfizetes":
        r = t["reszlet"]
        if not re.search(rf"(?<![\d,.]){r}\s?(%|százalék|percent|per cent)", low):
            return "hiányzó részlet-arány"
        if any(x in S.norm_digits(text) for x in S.amount_forms(p["nehez"]["teljes"], lang, cents=True)):
            return "a számla teljes összege a szövegben"
    elif v == "H3-valtas":
        for m in t["meresek"]:
            if not S.reading_present(text, m["ertek"], m["egyseg"]):
                return f"a mért érték nem a megadott egységgel: {m['nev']}"
            if m["eredeti"].strip() != m["egyseg"] and re.search(r"\d\s*" + re.escape(m["eredeti"].strip()) + r"(?![\w/])", text):
                return f"átváltott érték az eredeti egységben is: {m['nev']}"
    elif v == "S3a-netto":
        if not re.search(r"bruttó|gross", low):
            return "hiányzik, hogy bruttó"
        if not re.search(rf"(?<!\d){t['afa']}\s?(%|százalék|percent)", low):
            return "hiányzó áfakulcs"
        if _szam_jelen(text, t["netto"]):
            return "a nettó összeg a szövegben"
    elif v == "S3b-deviza":
        if not S.value_present(text, f"{t['arfolyam']}".replace(".", "," if lang == "hu" else ".")):
            return "hiányzó árfolyam"
        if not re.search(r"eur|euró|€" if lang == "hu" else r"gbp|£|pound", low):
            return "hiányzó deviza"
        if _szam_jelen(text, round(t["atszamitva"])) or _szam_jelen(text, t["atszamitva"]):
            return "az átszámított összeg a szövegben"
    return None


# --- minta és önteszt ----------------------------------------------------------------------------------------------

def cmd_minta(a) -> None:
    out = ["# A 3. kör mintapromptjai (szint07k3 minta) — változatonként hu + en; a terv a 06 T500-sablonokon\n"]
    for fam in S7.CSALADOK:
        for lang in S.LANGS:
            sabs = sorted((s for s in S7.sablonok(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"])
            lattam = Counter()
            for sab in sabs:
                for j in range(4):
                    p = plan3(fam, sab, j)
                    if p.get("kimarad") or lattam[p["nehez"]["valt"]] >= a.n:
                        continue
                    lattam[p["nehez"]["valt"]] += 1
                    gold = next(o["text"] for o in p["opciok"] if o["sid"] == p["gold_sid"])
                    out += [f"## {p['nehez']['valt']} · {lang} · {sab['sablon_id']}\n", "Opciók:"]
                    out += [f"- {'**' if o['sid'] == p['gold_sid'] else ''}{o['text']}{'** (gold)' if o['sid'] == p['gold_sid'] else ''}"
                            for o in p["opciok"]]
                    out += ["", f"Tények: `{ {k: x for k, x in p['tenyek'].items() if k not in ('tipus_leiras',)} }`", "",
                            "Generátor-utasítás:", "", "> " + gen_prompt3(p).replace("\n", " "), ""]
                    assert gold
    o = S7.d07() / "minta_promptok.md"
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"→ {o.relative_to(EXP)}")


def cmd_onteszt(_a) -> None:
    """Minden változatra egy jó szöveg (átmegy) és egy-két rossz (a várt hibával bukik), az első alkalmas terven."""
    hibak = 0
    for fam in S7.CSALADOK:
        for lang in S.LANGS:
            sab = sorted((s for s in S7.sablonok(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"])
            for j in range(2):
                p = next(q for q in (plan3(fam, s, j) for s in sab) if not q.get("kimarad"))
                for nev, szoveg, varhato in onteszt_szovegek(p):
                    kap = fact_check3(p, szoveg)
                    ok = (kap is None) if varhato is None else (kap is not None and varhato in kap)
                    hibak += not ok
                    print(f"{'OK ' if ok else 'HIBA'} {p['nehez']['valt']:16} {lang} {nev:22} várt: {varhato} · kapott: {kap}")
    raise SystemExit(1 if hibak else 0)


def onteszt_szovegek(p: dict) -> list[tuple[str, str, str | None]]:
    v, t, lang = p["nehez"]["valt"], p["tenyek"], p["lang"]
    hu = lang == "hu"
    if p["csalad"] == "penzugy.bankparositas":
        d, partner = t["datum"], t["partner"]
        if v == "B3a-reszfizetes":
            m = S.money(t["osszeg"], lang)
            jo = (f"A {partner} felé {d} napon kimenő terhelés történt {m} összegben; ez a számla {t['reszlet']}%-os részlete."
                  if hu else f"On {d} an outgoing debit of {m} was made to {partner}; it is a {t['reszlet']}% instalment of the invoice.")
            return [("jó", jo, None), ("arány nélkül", jo.replace(f"{t['reszlet']}%", "egy"), "részlet-arány")]
        jo = (f"A {partner} felé {d} napon kimenő terhelés történt, összege {t['betuvel']}."
              if hu else f"On {d} an outgoing debit to {partner} was made, amounting to {t['betuvel']}.")
        return [("jó", jo, None), ("számjeggyel is", jo + f" ({S.money(t['osszeg'], lang)})", "számjegyekkel"),
                ("betűs nélkül", jo.replace(t["betuvel"], "valamennyi"), "betűs összeg")]
    if p["csalad"] == "muszaki.hibaelharitas":
        mer = "; ".join(f"{m['nev']}: {m['ertek']} {m['egyseg']}" for m in t["meresek"])
        jo = (f"Jó napot! A berendezésnél ezt tapasztaljuk: {t['tunet']} Mértük: {mer}."
              if hu else f"Hello, we see this on the unit: {t['tunet']} We measured: {mer}.")
        m0 = t["meresek"][0]
        rossz = jo.replace(f"{m0['ertek']} {m0['egyseg']}", f"{m0['ertek']} {m0['egyseg']} (12 {m0['eredeti']})")
        return [("jó", jo, None), ("eredeti egységgel is", rossz, "eredeti egységben")]
    helyzet = t["helyzet"]
    if v == "S3a-netto":
        m = S.money(t["osszeg"], lang) if hu else f"EUR {t['osszeg']:,}"
        jo = (f"Kérem a költség elszámolását: {helyzet}. Összeg: {m} bruttó, {t['afa']}% áfával."
              if hu else f"Please reimburse: {helyzet}. Amount: {m} gross, including {t['afa']}% VAT.")
        return [("jó", jo, None), ("áfakulcs nélkül", jo.replace(f", {t['afa']}% áfával", "").replace(f", including {t['afa']}% VAT", ""), "áfakulcs"),
                ("nettóval", jo + (f" Nettó: {S.money(t['netto'], lang)}." if hu else f" Net: EUR {t['netto']:,}."), "nettó összeg")]
    arf = f"{t['arfolyam']}" if hu else f"{t['arfolyam']:.2f}"
    jo = (f"Kérem a költség elszámolását: {helyzet}. Összeg: {t['osszeg']} EUR, {arf} Ft/EUR árfolyamon."
          if hu else f"Please reimburse: {helyzet}. Amount: GBP {t['osszeg']:,} at {arf} EUR/GBP.")
    atsz = (f" ({S.money(round(t['atszamitva']), lang)})" if hu else f" (EUR {round(t['atszamitva']):,})")
    return [("jó", jo, None), ("árfolyam nélkül", jo.replace(arf, "napi"), "árfolyam"), ("átszámítva", jo + atsz, "átszámított")]


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("terv")
    t.add_argument("--csalad", required=True, choices=S7.CSALADOK)
    t.add_argument("--per-sablon", type=int, default=4)
    m = sub.add_parser("minta")
    m.add_argument("--n", type=int, default=2)
    sub.add_parser("onteszt")
    g = sub.add_parser("gen")
    g.add_argument("--csalad", required=True, choices=S7.CSALADOK)
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=32)
    f = sub.add_parser("final")
    f.add_argument("--csalad", required=True, choices=S7.CSALADOK)
    a = ap.parse_args()
    S7.KOR["n"] = 3
    S.path = S7.path07
    S7.plan_nehez = plan3
    S.gen_prompt, S.fact_check = gen_prompt3, fact_check3
    a.proba = True  # a szint06 `final`-ja: minden túlélő marad, cellakvóta nélkül
    {"terv": cmd_terv, "minta": cmd_minta, "onteszt": cmd_onteszt, "gen": S.cmd_gen, "final": S.cmd_final}[a.cmd](a)


if __name__ == "__main__":
    main()
