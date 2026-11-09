"""08 G1b — az értelmezési konstrukció generátora (`kor08/ertelmezes-javaslat.md`; 08-runbook 3.3). JAVASLAT: a
konstrukció Dani döntése; a GPU-s generálás (Muse) csak az ő jóváhagyása után. A `szint06` és a `szint07` burkolója
(mindkettő manifestelt, nem módosul).

A próba a 07 ismert CAL-sablonjain fut (családonként 30), így diszjunkt az L-RN tanítómintájától (a 06 T500
sablonjai) és a friss szeletektől. Sablononként `--per-sablon` eset; minden eset (b) változata (a jel a bemenetben,
gold MATCH), és az első esete az (a) párja is (ugyanaz a terv a jel nélkül, gold Y = MISSING_DATA). A pár közös
`meta.par` kulccsal, ugyanabban a sabloncsoportban.

Változatok:
  E-bank-1     két azonos összegű számla két partnertől (ikrek, hivatkozás nélkül); (b) a közlemény kimondja, hogy B
               fizeti A számláját (A a gold, B az első és feltűnőbb név); (a) mindkét név a viszony nélkül
  E-hiba-1     két ok két tünetcsoportból, mindkettő mérése szerepel és teljesíti a saját szabályát (a csali mérése az
               első); (b) a tünet a saját szavaival, csak a gold csoportjára illik; (a) a tünet általános
  E-szabaly-1  a kiadás két kategória határán (`ertelmezes08_szab.FORGATOKONYV`); a felszíni szó a csalié; (b) a cél
               kimondva (a gold kategóriája); (a) a cél nélkül. A küszöb oldalát a lánc dönti el.

Kimenet: kor08/adat/ertelmezes/{terv,raw,items}/<család>.jsonl (split ERT).
  terv   --csalad F [--per-sablon 3]       (CPU)
  minta  [--n 2]                           változatonként n (b) + n (a) mintaprompt → kor08/adat/ertelmezes/minta_promptok.md
  gen    --csalad F --url U --model M [--extra J] [--workers N]     (GPU: Muse; Dani jóváhagyta 11-02)
  final  --csalad F
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok"), str(EXP / "kor06/eszkozok")]
import ertelmezes08_szab as SZ  # noqa: E402
import szint06 as S  # noqa: E402

ORIG_GEN = S.gen_prompt
BANK, HIBA, SZAB = "penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas"
CSALADOK = (BANK, HIBA, SZAB)
D = EXP / "kor08/adat/ertelmezes"
KOR = {"n": 1, "j": False}  # a `--kor` kapcsoló; az 1. kör a `D` alatt, a többi a `D / kor<n>` alatt, saját szeletnévvel;
# a `--javitott` (2. kör, szabálycsalád, Dani 11-02): a `ertelmezes08_szab.JAVITAS2` forgatókönyveivel, `kor2j` / ERT2J


def szelet() -> str:
    return "ERT" if KOR["n"] == 1 else f"ERT{KOR['n']}{'J' if KOR['j'] else ''}"
VALTOZAT = {BANK: "E-bank-1", HIBA: "E-hiba-1", SZAB: "E-szabaly-1"}
VISZONY = {"hu": re.compile(r"nevében|megbízás|helyett|számláját|számlájának|számláit|részére fizet|fizeti", re.I),
           "en": re.compile(r"on behalf|behalf of|instead of|'s invoice|invoice of|pays for|paying for|on the instruction", re.I)}


def kor_dir() -> Path:
    return D if KOR["n"] == 1 else D / f"kor{KOR['n']}{'j' if KOR['j'] else ''}"


def path(kind: str, fam: str) -> Path:
    return kor_dir() / kind / f"{fam}.jsonl"


def sablonok07(fam: str, szelet: str = "CAL") -> list[dict]:
    return [s for s in S.jl_read(EXP / "kor07/adat/f2/sablon" / f"{fam}.jsonl") if s["szelet"] == szelet]


def _elso(nev: str) -> str:
    return nev.split()[0].lower()


# --- tervek ------------------------------------------------------------------------------------------------------------

def plan_e(fam: str, sab: dict, seq: int) -> dict | None:
    """Egy eset terve (a (b) változat); None, ha a sablonban nincs alkalmas konstrukció."""
    rnd = S.rnd_for("ertelmezes08", sab["sablon_id"], seq)
    lang = sab["lang"]
    p = {"csalad": fam, "sablon_id": sab["sablon_id"], "lang": lang, "allapot": "MATCH", "szelet": szelet(),
         "dim": {k: rnd.choice(x)[S.LANGS.index(lang)] for k, x in S.DIM[fam].items()},
         "ertelmezes": {"valt": VALTOZAT[fam], "seq": seq}}
    k = rnd.randint(S.K["opciok"]["min"], S.K["opciok"]["max"])
    if fam == BANK:
        inv = sab["szamlak"]
        for _ in range(100):
            a_, b_ = rnd.sample(inv, 2)
            if a_["partner"] != b_["partner"] and _elso(a_["partner"]) != _elso(b_["partner"]):
                break
        else:
            return None
        csali = {**b_, "id": "s_csali", "osszeg": a_["osszeg"]}
        pool = [s for s in inv if s["osszeg"] != a_["osszeg"] and s["id"] not in (a_["id"], b_["id"])
                and _elso(s["partner"]) not in (_elso(a_["partner"]), _elso(b_["partner"]))]
        if len(pool) < k - 2:
            return None
        opts = [a_, csali] + rnd.sample(pool, k - 2)
        rnd.shuffle(opts)
        p["tenyek"] = {"osszeg": a_["osszeg"], "irany": S.IRANY[lang][0], "datum": S.tx_date(rnd, [s["kelt"] for s in opts]),
                       "szamla_partnere": a_["partner"], "fizeto": b_["partner"]}
        p["opciok"] = [{"sid": s["id"], "text": f"{s['szamlaszam']} · {s['partner']} · {S.money(s['osszeg'], lang)} · "
                                                 f"{'esedékes' if lang == 'hu' else 'due'} {s['esedekes']}"} for s in opts]
        p["gold_sid"], p["csali_sid"], p["sajat_ceg"] = a_["id"], "s_csali", sab["ceg"]
    elif fam == HIBA:
        g = sab["tunetcsoportok"]
        gi, gj = rnd.sample(range(len(g)), 2)
        ti, tj = rnd.randrange(2), rnd.randrange(2)
        t, o = g[gi]["okok"][ti], g[gj]["okok"][tj]
        if t["meres"]["nev"].lower() == o["meres"]["nev"].lower():
            return None
        sid = lambda a, b: f"c{a}{b}"  # noqa: E731
        mas = [(x, y) for x in range(len(g)) for y in range(2) if x not in (gi, gj)]
        valasztott = [(gi, ti), (gj, tj)] + rnd.sample(mas, min(len(mas), k - 2))
        rnd.shuffle(valasztott)
        mer = [{"nev": o["meres"]["nev"], "ertek": S.fmt_num(o["meres"]["ertek_ha_ez"], lang), "egyseg": o["meres"]["egyseg"]},
               {"nev": t["meres"]["nev"], "ertek": S.fmt_num(t["meres"]["ertek_ha_ez"], lang), "egyseg": t["meres"]["egyseg"]}]
        p["berendezes"], p["modell"] = sab["berendezes"], sab["modell"]
        p["tenyek"] = {"tunet": g[gi]["tunet"], "csali_tunet": g[gj]["tunet"], "meresek": mer}
        p["opciok"] = [{"sid": sid(a, b), "nev": g[a]["okok"][b]["nev"],
                        "text": f"{g[a]['okok'][b]['nev']} — {S.hiba_szabaly(g[a]['okok'][b], g[a]['tunet'], lang)}"}
                       for a, b in valasztott]
        p["gold_sid"], p["csali_sid"] = sid(gi, ti), sid(gj, tj)
    else:
        pts = sab["pontok"]
        tipusok = {x["tipus"] for x in pts}
        fk = [f for f in SZ.FORGATOKONYV[lang] if f["gold"] in tipusok and f["csali"] in tipusok]
        if not fk:
            return None
        f = rnd.choice(fk)
        sav = rnd.randrange(2)
        gold = next(x for x in pts if x["tipus"] == f["gold"] and x["sav"] == sav)
        hatarok = {x["tipus"]: x["hatar"] for x in pts}
        osszeg = 0
        for _ in range(200):
            h = gold["hatar"]
            osszeg = h * (rnd.uniform(0.35, 0.85) if sav == 0 else rnd.uniform(1.2, 2.2))
            osszeg = int(osszeg) // 10 * 10 if lang == "hu" else int(osszeg)
            if all(abs(osszeg - hh) / hh > 0.08 for hh in hatarok.values()):
                break
        else:
            return None
        harmadik = [x for x in pts if x["tipus"] not in (f["gold"], f["csali"])]
        opts = [x for x in pts if x["tipus"] in (f["gold"], f["csali"])] + rnd.sample(harmadik, max(0, min(k - 4, len(harmadik))))
        rnd.shuffle(opts)
        p["tenyek"] = {"tipus": f["gold"], "csali_tipus": f["csali"], "helyzet": f["helyzet"], "jel": f["jel"],
                       "kulcs": f["kulcs"], "osszeg": osszeg,
                       "tipus_leirasok": [S.SZAB_TIPUS[lang][f["gold"]], S.SZAB_TIPUS[lang][f["csali"]]]}
        p["opciok"] = [{"sid": x["id"], "text": x["szoveg"]} for x in opts]
        csali = next(x for x in pts if x["tipus"] == f["csali"] and x["sav"] == (0 if osszeg < hatarok[f["csali"]] else 1))
        p["gold_sid"], p["csali_sid"], p["szervezet"] = gold["id"], csali["id"], sab["szervezet"]
    return p


def kieg2(fam: str, sab: dict, p: dict, seq: int) -> dict:
    """A 2. kör (Dani 11-02, áttételes jel): ugyanaz a terv, a (b) jelének új adataival. Bank: a fizető szerepe a számla
    partneréhez; hiba: a többi opció tünetcsoportja (a megfigyelés ezekre nem illhet); szabály: a `JEL2` jele."""
    t = dict(p["tenyek"])
    if fam == BANK:
        t["szerep2"] = S.rnd_for("ertelmezes08-kor2", sab["sablon_id"], seq).choice(SZ.BANK_SZEREP2[p["lang"]])[0]
    elif fam == HIBA:
        g = sab["tunetcsoportok"]
        gi = int(p["gold_sid"][1])
        t["tobbi_tunet"] = [g[a]["tunet"] for a in sorted({int(o["sid"][1]) for o in p["opciok"]}) if a != gi]
    else:
        k = next(i for i, f in enumerate(SZ.FORGATOKONYV[p["lang"]]) if f["helyzet"] == t["helyzet"])
        t |= SZ.JEL2[p["lang"]][k]
    return {**p, "tenyek": t, "ertelmezes": {**p["ertelmezes"], "kor": KOR["n"]}}


def a_valtozat(p: dict) -> dict:
    """Az (a) pár: ugyanaz a terv a jel nélkül, gold Y."""
    return {**p, "allapot": "MISSING_DATA", "gold_sid": None, "ertelmezes": {**p["ertelmezes"], "alt": "a"}}


def cmd_terv(a) -> None:
    fam = a.csalad
    rows, kimarad = [], Counter()
    for lang in S.LANGS:
        i = 0
        for sab in sorted((s for s in sablonok07(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"]):
            for j in range(a.per_sablon):
                p = plan_e(fam, sab, j)
                if p is None:
                    kimarad[lang] += 1
                    continue
                if KOR["n"] >= 2:
                    p = kieg2(fam, sab, p, j)
                if KOR["j"]:
                    k = next(x for x, f in enumerate(SZ.FORGATOKONYV[lang]) if f["helyzet"] == p["tenyek"]["helyzet"])
                    if SZ.kihagyott(lang, k):
                        kimarad[f"{lang}: kihagyott forgatókönyv"] += 1
                        i += 1 + (j == 0)  # a többi terv azonosítója a 2. köré marad
                        continue
                    p["ertelmezes"] |= {"javitott": k in SZ.JAVITAS2[lang]}
                    if SZ.d7_javitott(lang, k):  # a D7 audit után javított forgatókönyv: minden terve újra generálódik
                        p["ertelmezes"] |= {"d7": True}
                par = f"{sab['sablon_id']}:{j}"
                p["ertelmezes"] |= {"alt": "b", "par": par}
                valtok = [p] + ([a_valtozat(p)] if j == 0 else [])
                for q in valtok:
                    gid = f"{fam}:{szelet()}:{lang}:{q['allapot']}:{i:04d}"
                    g0 = gid.replace(f":{szelet()}:", f":ERT{KOR['n']}:")  # a javított kör a 2. kör opciósorrendjét tartja
                    rows.append(q | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:ertelmezes08:{g0}") % 10**12})
                    i += 1
    S.jl_write(path("terv", fam), rows)
    print(f"{fam}: {len(rows)} terv; " + ", ".join(f"{k}={n}" for k, n in sorted(Counter(r["ertelmezes"]["alt"] for r in rows).items()))
          + (f"; alkalmas konstrukció híján kimaradt: {dict(kimarad)}" if kimarad else ""))


# --- generátor-utasítás és tényellenőrzés --------------------------------------------------------------------------

def _farok(p: dict) -> str:
    s = ORIG_GEN(p)
    jel = " A szöveg nyelve magyar." if p["lang"] == "hu" else " Write in English."
    if jel not in s:
        raise SystemExit("a szint06 utasítása nem a várt alakú")
    return s[s.index(jel):]


def gen_prompt_e(p: dict) -> str:
    fam, lang, t, d = p["csalad"], p["lang"], p["tenyek"], p["dim"]
    hu, alt = lang == "hu", p["ertelmezes"]["alt"]
    nv = S.nevelo
    if fam == BANK:
        A, B = t["szamla_partnere"], t["fizeto"]
        core = (f"Írj egy banki tételt {nv(p['sajat_ceg'])} {p['sajat_ceg']} cég bankszámlájáról. Forma: {d['forma']}. "
                f"Irány: {t['irany']}. Dátum: {t['datum']} (csak ezt az egy dátumot használd). Összeg: {S.money(t['osszeg'], lang)}. "
                "A tétel egy számla kiegyenlítése." if hu else
                f"Write one bank transaction on the account of {p['sajat_ceg']}. Format: {d['forma']}. Direction: {t['irany']}. "
                f"Date: {t['datum']} (use only this one date). Amount: {S.money(t['osszeg'], lang)}. It settles an invoice.")
        if alt == "b" and KOR["n"] >= 2:
            _, pelda, _ = next(x for x in SZ.BANK_SZEREP2[lang] if x[0] == t["szerep2"])
            pelda = pelda.format(A=A, B=B)
            szerep = {"jogutód": f"{nv(A)} {A} jogutódjaként", "kezes": f"{nv(A)} {A} kezeseként",
                      "átvállalás": f"{nv(A)} {A} tartozásának átvállalójaként",
                      "successor": f"as the legal successor of {A}", "guarantor": f"as guarantor for {A}",
                      "assumption": f"as the party that assumed the debt of {A}"}[t["szerep2"]]
            core += (f" A közleményből derüljön ki egyértelműen, hogy ez a fizetés {nv(A)} {A} kötelezettségét rendezi, "
                     f"mert {nv(B)} {B} {szerep} fizet. Például: „{pelda}” (a saját "
                     f"szavaiddal). Ne írd azt, hogy „{B} fizeti {nv(A)} {A} számláját”, és ne használd a „nevében” vagy "
                     f"„megbízásából” fordulatot. Mindkét cégnév szerepeljen, elsőként {nv(B)} {B} neve." if hu else
                     f" The payment details must make it unambiguous that this payment settles the obligation of {A}, "
                     f"because {B} pays {szerep}. For example: \"{pelda}\" (in your own words). Do not "
                     f"write \"{B} paying the invoice of {A}\", and do not use \"on behalf of\". Both company names must "
                     f"appear, {B} first.")
        elif alt == "b":
            core += (f" A közleményből derüljön ki egyértelműen, hogy {nv(B)} {B} fizeti {nv(A)} {A} számláját (például: "
                     f"„{B} fizeti {nv(A)} {A} számláját” vagy „{nv(A)} {A} megbízásából”). Mindkét cégnév szerepeljen, "
                     f"elsőként {nv(B)} {B} neve." if hu else
                     f" The payment details must make it unambiguous that {B} is paying the invoice of {A} (for example "
                     f"\"{B} paying the invoice of {A}\" or \"on behalf of {A}\"). Both company names must appear, {B} first.")
        else:
            core += (f" A közleményben mindkét cégnév szerepeljen, ebben a sorrendben: {B}, {A}; de ne derüljön ki, melyik "
                     "cég számlájáról van szó, és az sem, hogy ki fizet kinek a nevében." if hu else
                     f" Both company names must appear in the payment details, in this order: {B}, {A}; but it must not be "
                     "clear whose invoice is being paid, nor who pays on whose behalf.")
        core += (" Külön partnermezőt ne írj. Számlaszámot, hivatkozási számot vagy más dátumot ne írj bele." if hu else
                 " Do not add a separate counterparty field. Do not add any invoice number, reference number or other date.")
    elif fam == HIBA:
        mer = "; ".join(f"{m['nev']}: {m['ertek']} {m['egyseg']}" for m in t["meresek"])
        core = (f"Írj a szervizhez beérkező, {d['forma']} formájú, {d['hossz']} üzenetet; a bejelentő a berendezés "
                f"felhasználói oldaláról ír ({d['bejelento']}). Berendezés: {p['modell']} típusú {p['berendezes']}." if hu else
                f"Write a {d['hossz']} {d['forma']} sent to the service desk by the device's user side ({d['bejelento']}). "
                f"Device: {p['berendezes']}, model {p['modell']}.")
        if alt == "b" and KOR["n"] >= 2:
            tobbi = "; ".join(t["tobbi_tunet"])
            core += (f" Írd le, mit tapasztal a bejelentő: konkrét megfigyeléseket és körülményeket (mikor, mi történik, mi "
                     f"nem történik), amelyekből egyértelműen ez a jelenség következik: {t['tunet']}. Magát a jelenséget ne "
                     f"ezzel a megfogalmazással nevezd meg. A leírás ezekre a jelenségekre ne illjen: {tobbi}." if hu else
                     f" Describe what the reporter observes: concrete observations and circumstances (when, what happens, "
                     f"what does not happen) from which this symptom clearly follows: {t['tunet']}. Do not name the symptom "
                     f"with this wording. The description must not fit these symptoms: {tobbi}.")
        elif alt == "b":
            core += (f" A jelenséget írd le konkrétan, a saját szavaiddal (ne szó szerint ezzel a mondattal): {t['tunet']}." if hu else
                     f" Describe the symptom concretely, in your own words (not verbatim with this sentence): {t['tunet']}.")
        else:
            core += (" A jelenséget ne írd le konkrétan: csak annyit írj, hogy a berendezés nem működik rendesen; hogy pontosan "
                     "mi a gond, ne derüljön ki." if hu else
                     " Do not describe the symptom concretely: only say that the device is not working properly; it must not "
                     "be clear what exactly is wrong.")
        core += (f" Pontosan ezek a mért értékek szerepeljenek, ebben a sorrendben, más mérés ne: {mer}. A hiba okát ne "
                 "nevezd meg, és ne találgass." if hu else
                 f" Include exactly these measured values, in this order, and no other measurement: {mer}. Do not name or "
                 "guess the cause.")
    else:
        core = (f"Írj {d['forma']} formájú, {d['regiszter']} hangvételű üzenetet {nv(p['szervezet'])} {p['szervezet']} egyik "
                f"munkatársától. Az üzenet költségelszámolási kérelem. A költség: {t['helyzet']}." if hu else
                f"Write a {d['regiszter']} {d['forma']} from an employee of {p['szervezet']}. It is an expense claim. The "
                f"expense: {t['helyzet']}.")
        if alt == "b" and KOR["n"] >= 2:
            core += (f" A szöveg mondja ki ezt a tényt is, a saját szavaiddal, de a költség kategóriáját ne nevezd meg: "
                     f"{t['jel2']}." if hu else
                     f" The text must also state this fact, in your own words, without naming the expense category: "
                     f"{t['jel2']}.")
        elif alt == "b":
            core += (f" A szöveg mondja ki ezt is, a saját szavaiddal: {t['jel']}." if hu else
                     f" The text must also state this, in your own words: {t['jel']}.")
        else:
            core += (" A költség céljáról vagy jellegéről ezen túl semmit ne írj." if hu else
                     " Do not say anything more about the purpose or nature of the expense.")
        core += (f" Összeg: {S.money(t['osszeg'], lang)}. Szabálypontra, költségkategóriára vagy jóváhagyóra ne hivatkozz." if hu else
                 f" Amount: EUR {t['osszeg']:,}. Do not refer to policy clauses, expense categories or approvers.")
    return core + _farok({**p, "tenyek": {**t, "osszeg": t.get("osszeg", 0), "irany": t.get("irany", ""),
                                          "datum": t.get("datum", ""), "meresek": t.get("meresek", [])}})


def _altalanos(p: dict, text: str) -> str | None:
    if not S.lang_ok(text, p["lang"]):
        return "rossz nyelv"
    if any(x in text.lower() for x in S.LEAK[p["lang"]]):
        return "címkét kimondó fordulat"
    if "a(z)" in text.lower():
        return "„a(z)” a szövegben"
    return None


def fact_check_e(p: dict, text: str) -> str | None:
    if (err := _altalanos(p, text)):
        return err
    fam, t, lang, alt = p["csalad"], p["tenyek"], p["lang"], p["ertelmezes"]["alt"]
    low, nd = text.lower(), S.norm_digits(text)
    if fam == BANK:
        if not any(x in nd for x in S.amount_forms(t["osszeg"], lang, cents=True)):
            return "hiányzó összeg"
        if t["datum"].replace("-", "") not in S.norm_date(text):
            return "hiányzó vagy eltérő dátum"
        for nev in (t["szamla_partnere"], t["fizeto"]):
            if _elso(nev) not in low:
                return "hiányzó cégnév"
        tobbi = {_elso(o["text"].split(" · ")[1]) for o in p["opciok"]} - {_elso(t["szamla_partnere"]), _elso(t["fizeto"])}
        if any(re.search(rf"(?<!\w){re.escape(x)}(?!\w)", low) for x in tobbi):
            return "más opció partnere a szövegben"
        if (err := S.bank_idegen(p, text)):
            return err
        van = bool(VISZONY[lang].search(text))
        if KOR["n"] >= 2:
            szerep = {x[0]: x[2] for x in SZ.BANK_SZEREP2[lang]}
            van2 = any(re.search(rx, low) for rx in szerep.values())
            if alt == "b" and not re.search(szerep[t["szerep2"]], low):
                return "(b): hiányzik a fizető szerepe"
            if alt == "a" and (van or van2):
                return "(a): a viszony vagy a fizető szerepe a szövegben"
            if alt == "b" and low.find(_elso(t["fizeto"])) > low.find(_elso(t["szamla_partnere"])):
                return "(b): a számla partnere áll elöl"
            return None
        if alt == "b" and not van:
            return "(b): hiányzik a fizető és a számla partnere közti viszony"
        if alt == "a" and van:
            return "(a): a viszony a szövegben"
    elif fam == HIBA:
        for m in t["meresek"]:
            if not S.reading_present(text, m["ertek"], m["egyseg"]):
                return f"hiányzó mért érték: {m['nev']}"
        if any(o["nev"].strip().lower() in low for o in p["opciok"]):
            return "ok megnevezve a szövegben"
        if t["csali_tunet"].lower().rstrip(".") in low:
            return "a csali tünete szó szerint"
        if t["tunet"].lower().rstrip(".") in low:
            return "a gold tünete szó szerint"
        if any(x.lower().rstrip(".") in low for x in t.get("tobbi_tunet", [])):
            return "egy másik opció tünete szó szerint"
    else:
        if not any(x in nd for x in S.amount_forms(t["osszeg"], lang, cents=False)):
            return "hiányzó összeg"
        if any(x.lower() in low for x in t["tipus_leirasok"]):
            return "a költségnem leírása szó szerint"
        for o in p["opciok"]:
            if re.search(rf"(?<![\d.]){re.escape(o['text'].split('.')[0] + '.' + o['text'].split('.')[1])}(?![\d])", text):
                return "szabálypont-hivatkozás a szövegben"
        van = any(k.lower() in low for k in t["kulcs"])
        if KOR["n"] >= 2:
            van2 = any(k.lower() in low for k in t["kulcs2"])
            if alt == "b" and not van2:
                return "(b): hiányzik az áttételes jel (a kulcs2 szavai)"
            if alt == "a" and (van or van2):
                return "(a): a jel kulcsszava a szövegben"
            return None
        if alt == "b" and not van:
            return "(b): hiányzik a cél (a jel kulcsszava)"
        if alt == "a" and van:
            return "(a): a jel kulcsszava a szövegben"
    return None


# --- minta, generálás, itemek ----------------------------------------------------------------------------------------

def cmd_minta(a) -> None:
    out = ["# 08 G1b — az értelmezési konstrukció mintapromptjai (szint08e minta); a terv a 07 CAL-sablonokon\n"]
    for fam in CSALADOK:
        rows = S.jl_read(path("terv", fam))
        for lang in S.LANGS:
            for alt in ("b", "a"):
                for p in [r for r in rows if r["lang"] == lang and r["ertelmezes"]["alt"] == alt][:a.n]:
                    gold = next((o["text"] for o in p["opciok"] if o["sid"] == p["gold_sid"]), "— (Y)")
                    out += [f"## {fam} · {lang} · ({alt}) · {p['group_id']}", "", "**Utasítás:**", "", gen_prompt_e(p), "",
                            "**Opciók:**", ""] + [f"- `{o['sid']}` {o['text']}" for o in p["opciok"]] + ["", f"**Gold:** {gold}", ""]
    (kor_dir() / "minta_promptok.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"→ {(kor_dir() / 'minta_promptok.md').relative_to(EXP)}")


def gen_one(p: dict, a, extra: dict) -> dict:
    out = {"group_id": p["group_id"], "terv": p, "probak": []}
    for k in range(3):
        try:
            so = ":d7" if p["ertelmezes"].get("d7") else ""  # a D7 utáni javítás új seedet kap (az (a) utasítása azonos)
            obj = S.llm_json(a.url, a.model, p["lang"], gen_prompt_e(p), extra,
                             S.h(f"gen08e:{p['group_id']}{so}:{k}") % 10**6)
        except RuntimeError as e:
            out["probak"].append(str(e))
            continue
        txt = str(obj.get("szoveg") or "").strip()
        err = "üres szöveg" if not txt else fact_check_e(p, txt)
        if err is None:
            return out | {"szoveg": txt}
        out["probak"].append(err)
    return out | {"hiba": out["probak"][-1] if out["probak"] else "ismeretlen"}


def cmd_gen(a) -> None:
    fam = a.csalad
    out = path("raw", fam)
    done = {r["group_id"] for r in S.jl_read(out)} if out.exists() else set()
    todo = [p for p in S.jl_read(path("terv", fam)) if p["group_id"] not in done]
    extra = json.loads(a.extra) if a.extra else {}
    print(f"{fam}: {len(done)} kész, {len(todo)} hátra", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    if KOR["j"]:
        todo = _atvesz(fam, todo, out)
    with open(out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, r in enumerate(ex.map(lambda p: gen_one(p, a, extra), todo), 1):
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            fh.flush()
            if i % 50 == 0:
                print(f"  {i}/{len(todo)}", flush=True)


def _atvesz(fam: str, todo: list[dict], out: Path) -> list[dict]:
    """A javított körben a 2. kör generálása marad, ahol a generátor-utasítás betűre azonos (a változatlan forgatókönyvek
    és a csak (b)-jelükben javítottak (a) tagja); a sikertelen generálás is, hogy a változatlan rész a 2. körrel egyezzen.
    A D7 audit után (`kor2j/arch_d7`) előbb az auditált javított kör generálása marad, ugyanígy; a `d7` jelű forgatókönyv
    minden terve újra generálódik. A többi terv újra generálódik."""
    regi = {r["group_id"]: r for r in S.jl_read(D / f"kor{KOR['n']}" / "raw" / f"{fam}.jsonl")}
    arch = kor_dir() / "arch_d7" / "raw" / f"{fam}.jsonl"
    auditalt = {r["group_id"]: r for r in S.jl_read(arch)} if arch.exists() else {}
    marad, n, na = [], 0, 0
    with open(out, "a", encoding="utf-8") as fh:
        for p in todo:
            if p["ertelmezes"].get("d7"):
                marad.append(p)
                continue
            r0 = auditalt.get(p["group_id"])
            if r0 is not None and gen_prompt_e(p) == gen_prompt_e(r0["terv"]) and r0["terv"] == p:
                fh.write(json.dumps(r0, ensure_ascii=False) + "\n")  # az auditált rekord betűre
                na += 1
                continue
            r0 = regi.get(p["group_id"].replace(f":{szelet()}:", f":ERT{KOR['n']}:"))
            if r0 is None or gen_prompt_e(p) != gen_prompt_e(r0["terv"]) or ("szoveg" in r0 and fact_check_e(p, r0["szoveg"])):
                marad.append(p)
                continue
            fh.write(json.dumps({**r0, "group_id": p["group_id"], "terv": p, "atveve": r0["group_id"]}, ensure_ascii=False) + "\n")
            n += 1
    print(f"{fam}: az auditált javított körből átvéve {na}, a 2. körből {n}, újra generálandó {len(marad)}", flush=True)
    return marad


def cmd_final(a) -> None:
    """Minden túlélő marad; a pár, amelynek (b) vagy (a) tagja elveszett, mindkét tagjával kimarad (a párok együtt
    mozognak)."""
    fam = a.csalad
    raw = [r for r in S.jl_read(path("raw", fam)) if "szoveg" in r]
    par_ok = Counter(r["terv"]["ertelmezes"]["par"] for r in raw)
    tervek = S.jl_read(path("terv", fam))
    par_kell = Counter(p["ertelmezes"]["par"] for p in tervek)
    items = []
    for r in raw:
        par = r["terv"]["ertelmezes"]["par"]
        if par_ok[par] != par_kell[par]:
            continue
        it = S.to_item(r)
        it["meta"] |= {"ertelmezes": r["terv"]["ertelmezes"]}
        items.append(it)
    S.jl_write(path("items", fam), items)
    elv = Counter(r.get("hiba") for r in S.jl_read(path("raw", fam)) if "szoveg" not in r)
    print(f"{fam}: {len(items)} item ({dict(Counter(i['meta']['ertelmezes']['alt'] for i in items))}); "
          f"a generálásban elveszett: {dict(elv)}; hiányos pár miatt kimaradt: {len(raw) - len(items)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("terv")
    t.add_argument("--csalad", required=True, choices=CSALADOK)
    t.add_argument("--per-sablon", type=int, default=3)
    m = sub.add_parser("minta")
    m.add_argument("--n", type=int, default=2)
    g = sub.add_parser("gen")
    g.add_argument("--csalad", required=True, choices=CSALADOK)
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=8)
    f = sub.add_parser("final")
    f.add_argument("--csalad", required=True, choices=CSALADOK)
    for x in (t, m, g, f):
        x.add_argument("--kor", type=int, default=1)
        x.add_argument("--javitott", action="store_true")
    a = ap.parse_args()
    KOR["n"] = a.kor
    if a.javitott:
        if a.kor != 2 or getattr(a, "csalad", SZAB) != SZAB:
            raise SystemExit("a --javitott csak a 2. kör szabálycsaládjára vonatkozik")
        SZ.alkalmaz_javitas()
        KOR["j"] = True
    {"terv": cmd_terv, "minta": cmd_minta, "gen": cmd_gen, "final": cmd_final}[a.cmd](a)


if __name__ == "__main__":
    main()
