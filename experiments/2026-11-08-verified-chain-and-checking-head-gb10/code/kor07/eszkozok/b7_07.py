"""07B — a befagyasztott modellek a <tenant> 262 valódi banki tételén (D7, Dani 2026-11-01 este; `b0.md` 9. pont).

Bemenet: a `b1rel07x pontoz --szelet b7:penzugy.bankparositas` kimenete (döntések és pontszámok, szöveg nélkül), a
`b7_epit` metája (csoport, termék-állapot, jelöltszám), a címkézéshez a `b7_cimke` kulcsai. A τ a bankcsaládé az F5
CAL-járól, változatlanul (D14). Csak aggregátum kerül ki.

  ideiglenes  a termék állapotához mérve (NEM független: a termék kötése a gold helyett). A modell döntései a termék
              állapota és a csoport szerint; munkapont a változatlan τ-val: hányat zárna le, ebből hány egyezik a
              termékkel, hány tér el tőle, és hány esik a termék által nem megoldott tételekre.
  vegleges    Dani vak címkéihez (`cimkek.json`) mérve, a D7 három eredményével: (1) a jelöltválasztás lefedése,
              (2) a modell döntésének helyessége a kapott listán (szigorú négyállapotú; munkapont: lezárt, ebből
              hibás), (3) a teljes folyamatban helyesen megoldott párosítások aránya a 262 tételen; mellette a termék
              (párosító + kategorizálás) a címkékhez mérve, és hogy a termék mellett hány további ügyet old meg
              helyesen a modell, és hány új hibát okoz. A több számlát rendező tételek az egy-számlás elemzésből
              kimaradnak, a teljes folyamatban megoldatlanként szerepelnek; az ikrek alapból M (MISSING_DATA); a K és N
              válasz kimarad (számuk közölve). Az elsődleges a kiegészítő értékelés (Dani, 11-02): a modell a meglévő
              kötést és kategóriát nem írja felül, csak a megoldatlan tételre (se kötés, se kategória) tesz javaslatot;
              ahol a termék a listán kötött és a modell a munkaponton mást mond, az ütközésjelzés. A felülíró változat
              leíró.

  python3 kor07/eszkozok/b7_07.py ideiglenes --be cache/k07/b7 --out kor07/eredmenyek/B7/ideiglenes
  python3 kor07/eszkozok/b7_07.py vegleges --be cache/k07/b7 --cimkek kor07/adat/b7/cimkek.json --out kor07/eredmenyek/B7
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(HERE))
import munkapont07 as MP  # noqa: E402

FAM = "penzugy.bankparositas"
B7 = EXP / "kor07/adat/b7"
CSOPORTOK = ("teljes", "reszfizetes_jelolt", "tetel_nagyobb", "tobb_szamla", "kategorias", "nem_egyeztetett")
DONTES = ("SELECT=termék", "SELECT=más", "X", "Y", "Z")


def betolt(be: str) -> tuple[dict, dict, dict]:
    doc = json.loads((Path(be) / f"b7_{FAM}.json").read_text())
    meta = json.loads((B7 / "meta.json").read_text())
    items = {}
    for x in (B7 / "items" / f"{FAM}.jsonl").read_text(encoding="utf-8").splitlines():
        if x.strip():
            it = json.loads(x)
            items[it["id"]] = {"gold": it["gold"], "n_opt": len(it["options"])}  # a szöveg nem marad meg
    return doc, meta, items


def fajta(d: dict) -> str:
    return {"SELECT": "SELECT", "NONE": "X", "MISSING": "Y", "OOS": "Z"}[d["kind"]]


# --- ideiglenes: a termékhez mérve -------------------------------------------------------------------------------------

def ideiglenes(a) -> None:
    doc, meta, items = betolt(a.be)
    res: dict = {"n_tetel": len(meta), "ures_lista": dict(Counter(m["csoport"] for m in meta.values() if not m["modellhez"])),
                 "keretek": {}}
    for kr in ("keret4", "keret2"):
        ids, D = doc[kr]["ids"], doc[kr]["dontes"]
        tab = Counter()
        for i in ids:
            f_ = fajta(D[i])
            if f_ == "SELECT":
                f_ = "SELECT=termék" if D[i]["cand"] == items[i]["gold"] and items[i]["gold"] else "SELECT=más"
            tab[(meta[i]["termek_allapot"], meta[i]["csoport"], f_)] += 1
        egyezik = np.array([bool(D[i]["helyes"]) for i in ids])  # a pontozó „helyes”-e itt a termék állapotához mér
        nem_megoldott = np.array([meta[i]["csoport"] == "nem_egyeztetett" for i in ids])
        mp = {}
        for arm in MP.KAROK[kr]:
            taus = MP.f5()[arm]["csaladok"][FAM]["tau"]
            if all(math.isinf(t) for t in taus):
                mp[arm] = {"nincs_munkapont": True}
                continue
            kind = np.array([D[i]["kind"] for i in ids])
            lez = (kind == "SELECT") | (kind == "NONE")
            futas = []
            for run, tau in zip(MP.KAROK[kr][arm], taus):
                acc = lez & (np.array(doc[kr]["pontszam"][run], float) >= tau)
                futas.append({"lezart": int(acc.sum()), "egyezik_termekkel": int((acc & egyezik & ~nem_megoldott).sum()),
                              "elter_termektol": int((acc & ~egyezik & ~nem_megoldott).sum()),
                              "termek_nem_oldotta_meg": int((acc & nem_megoldott).sum()),
                              **{f"csoport:{c}": int((acc & np.array([meta[i]["csoport"] == c for i in ids])).sum()) for c in CSOPORTOK}})
            mp[arm] = {"nincs_munkapont": False, "tau": taus,
                       "atlag": {k: float(np.mean([x[k] for x in futas])) for k in futas[0]}, "futasok": futas}
        res["keretek"][kr] = {"n": len(ids), "tabla": {"|".join(k): v for k, v in sorted(tab.items())}, "munkapont": mp}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ideiglenes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "ideiglenes.md").write_text(lap_ideiglenes(res), encoding="utf-8")
    print(lap_ideiglenes(res))


def g(x: float) -> str:
    return (f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.1f}").replace(".", ",")


def lap_ideiglenes(res: dict) -> str:
    L = ["# 07B — ideiglenes eredmény: a befagyasztott modellek a termékhez mérve (NEM független)", "",
         "A gold helyén a termék állapota áll (a kötés, ha a kötött számla a listán van; a kategória; különben „nincs "
         "megfelelő”). A végleges szám Dani vak címkéiből lesz (`b7_07 vegleges`). A τ a bankcsaládé az F5 CAL-járól, "
         "változatlanul. A jelöltlista a D7 szerint: P pool, legfeljebb 4, feltöltés nélkül.", "",
         f"Tétel {res['n_tetel']}; a modellhez nem került (üres lista): {res['ures_lista']}.", "",
         "A munkapont oszlopai diszjunktak: „egyezik” és „eltér” a termék által megoldott tételeken (kötött vagy "
         "kategorizált), „a termék nem oldotta meg” a kötés és kategória nélküli tételeken. Egyezés: SELECT a kötött "
         "számlára; X, ha a kötött számla nincs a listán; Z a kategorizált tételen (szigorú Z, D7), ezért ott az X "
         "eltérésnek számít.", ""]
    for kr, R in res["keretek"].items():
        L += [f"## {'Négyállapotú keret' if kr == 'keret4' else '06-os keret (leíró)'} (n = {R['n']})", "",
              "### A modell döntése a termék állapota és a csoport szerint", "",
              "| termék | csoport | " + " | ".join(DONTES) + " |", "|---|---|" + "---|" * len(DONTES)]
        sorok = sorted({tuple(k.split("|")[:2]) for k in R["tabla"]})
        for ta, cs in sorok:
            L.append(f"| {ta} | {cs} | " + " | ".join(str(R["tabla"].get(f"{ta}|{cs}|{d}", 0)) for d in DONTES) + " |")
        L += ["", "### Munkapont a változatlan τ-val (seedes karon a seedek átlaga)", "",
              "| kar | lezárt | egyezik a termékkel | eltér a terméktől | a termék nem oldotta meg | ebből részfizetés-jelölt | ebből kategóriás |",
              "|---|---|---|---|---|---|---|"]
        for arm, m in R["munkapont"].items():
            if m["nincs_munkapont"]:
                L.append(f"| {arm} | nincs munkapont | – | – | – | – | – |")
                continue
            x = m["atlag"]
            L.append(f"| {arm} | {g(x['lezart'])} | {g(x['egyezik_termekkel'])} | {g(x['elter_termektol'])} | "
                     f"{g(x['termek_nem_oldotta_meg'])} | {g(x['csoport:reszfizetes_jelolt'])} | {g(x['csoport:kategorias'])} |")
        L.append("")
    return "\n".join(L)


# --- végleges: Dani címkéihez mérve ------------------------------------------------------------------------------------

def cimkek(path: str) -> dict[str, dict]:
    """item-id → {'gold': opció-id | None, 'allapot', 'jelzok', 'kihagy'} a vak címkékből."""
    exp = json.loads(Path(path).read_text())
    ku = json.loads((B7 / "cimkezo_kulcsok.json").read_text())
    if exp.get("sig") != ku["sig"]:
        raise SystemExit("a címkék exportja nem ehhez a laphoz tartozik (sig)")
    out = {}
    for k, d in exp["cimkek"].items():
        K = ku["kulcsok"][k]
        v, j = d["valasz"], d.get("jelzok", [])
        if v in K["betu"]:
            allapot, gold = "MATCH", K["betu"][v]
        else:
            allapot, gold = {"X": "NO_MATCH", "M": "MISSING_DATA", "O": "OUT_OF_SCOPE"}.get(v), None
        out[K["id"]] = {"gold": gold, "allapot": allapot, "jelzok": j, "kihagy": v in ("K", "N"),
                        "tobb_szamla": any("több számlát" in x for x in j), "nincs_a_listan": any("nincs a listán" in x for x in j),
                        "reszfizetes": any("részfizetés" in x for x in j)}
    return out


HELYES = {"SELECT": "MATCH", "X": "NO_MATCH", "Y": "MISSING_DATA", "Z": "OUT_OF_SCOPE"}


def vegleges(a) -> None:
    doc, meta, items = betolt(a.be)
    C = cimkek(a.cimkek)
    if set(C) != set(meta):
        raise SystemExit(f"nem minden tétel címkézett: {len(C)} / {len(meta)}")
    kihagy = {i for i, c in C.items() if c["kihagy"]}
    tobb = {i for i, c in C.items() if c["tobb_szamla"]}
    res: dict = {"n_tetel": len(meta), "kihagyva_K_N": len(kihagy), "tobb_szamla": len(tobb),
                 "cimke_allapot": dict(Counter(c["allapot"] for i, c in C.items() if i not in kihagy))}
    # (1) a jelöltválasztás lefedése: ahol van helyes számla (betű vagy „létezik, de nincs a listán”)
    van = [i for i, c in C.items() if i not in kihagy | tobb and (c["allapot"] == "MATCH" or c["nincs_a_listan"])]
    res["jeloltlefedes"] = {"van_helyes_szamla": len(van), "a_listan": sum(C[i]["allapot"] == "MATCH" for i in van)}
    # a termék a címkékhez mérve: helyes kötés, téves kötés, kötés nélkül maradt helyes számla, kategória vs O
    tm = Counter()
    for i, m in meta.items():
        if i in kihagy | tobb:
            continue
        c = C[i]
        if m["termek_allapot"] == "MATCH":
            if c["allapot"] == "MATCH":
                tm["kötött, helyes" if items.get(i, {}).get("gold") == c["gold"] else "kötött, téves: a címke más számla"] += 1
            else:  # az M nem téves kötés: a címkéző a látott adatból nem tudta eldönteni
                tm[{"MISSING_DATA": "kötött; címke M (a látott adatból nem dönthető el)",
                    "NO_MATCH": "kötött, téves: címke X", "OUT_OF_SCOPE": "kötött, téves: címke O"}[c["allapot"]]] += 1
        elif m["csoport"] in ("teljes", "reszfizetes_jelolt", "tetel_nagyobb"):  # a termék a listán kívüli számlát kötötte
            tm["kötött a listán kívül; címke: létezik, de nincs a listán (nem ellenőrizhető)" if c["nincs_a_listan"] else
               f"kötött a listán kívül; címke: {c['allapot']}"] += 1
        elif m["kategoria"]:
            tm["kategorizált, címke O" if c["allapot"] == "OUT_OF_SCOPE" else "kategorizált, címke más"] += 1
        else:
            tm["nem oldotta meg, címke " + str(c["allapot"])] += 1
    res["termek"] = dict(tm)
    mo = [i for i, m in meta.items() if m["csoport"] == "nem_egyeztetett" and i not in kihagy | tobb]
    res["kiegeszito_hatokor"] = {"megoldatlan": len(mo), "modellhez": sum(meta[i]["modellhez"] for i in mo),
                                 "cimkek": dict(Counter(C[i]["allapot"] for i in mo))}
    res["keretek"] = {}
    for kr in ("keret4", "keret2"):
        ids = [i for i in doc[kr]["ids"] if i not in kihagy | tobb]
        D = doc[kr]["dontes"]
        kind = np.array([fajta(D[i]) for i in ids])
        cor = np.array([(fajta(D[i]) == "SELECT" and D[i]["cand"] == C[i]["gold"]) or
                        (fajta(D[i]) != "SELECT" and HELYES[fajta(D[i])] == C[i]["allapot"]) for i in ids])
        def dk(i: str) -> tuple[str, str]:
            f_ = fajta(D[i])
            if f_ != "SELECT":
                return C[i]["allapot"], f_
            if C[i]["gold"] is None:  # a címkének nincs számlája (X, M, O): bármely kötés hiba
                return C[i]["allapot"], "SELECT"
            return C[i]["allapot"], "SELECT=helyes" if D[i]["cand"] == C[i]["gold"] else "SELECT=más"

        conf = Counter(dk(i) for i in ids)
        termek_jo = np.array([meta[i]["termek_allapot"] == "MATCH" and items[i]["gold"] == C[i]["gold"]
                              and C[i]["allapot"] == "MATCH" for i in ids])
        termek_matched = np.array([meta[i]["termek_allapot"] == "MATCH" for i in ids])
        reszf = np.array([C[i]["reszfizetes"] or meta[i]["reszfizetes_jelolt"] for i in ids])
        # kiegészítő értékelés (Dani, 11-02): a modell a meglévő kötést és kategóriát nem írja felül, csak a termék által
        # megoldatlan tételre (se kötés, se kategória) tesz javaslatot; ahol a termék a listán kötött és a modell mást
        # mond (más számla vagy X), az ütközésjelzés, nem hiba
        megold = np.array([meta[i]["csoport"] == "nem_egyeztetett" for i in ids])
        termek_szamla = np.array([fajta(D[i]) == "SELECT" and D[i]["cand"] == items[i]["gold"] for i in ids])
        cimke_termek = np.array([C[i]["allapot"] == "MATCH" and C[i]["gold"] == items[i]["gold"] for i in ids])
        cimke_m = np.array([C[i]["allapot"] == "MISSING_DATA" for i in ids])
        kieg_tabla = Counter(dk(i) for i in ids if meta[i]["csoport"] == "nem_egyeztetett")
        mp = {}
        for arm in MP.KAROK[kr]:
            taus = MP.f5()[arm]["csaladok"][FAM]["tau"]
            if all(math.isinf(t) for t in taus):
                mp[arm] = {"nincs_munkapont": True}
                continue
            lez = (kind == "SELECT") | (kind == "X")
            futas = []
            for run, tau in zip(MP.KAROK[kr][arm], taus):
                q = np.array([doc[kr]["pontszam"][run][doc[kr]["ids"].index(i)] for i in ids], float)
                acc = lez & (q >= tau)
                jo_kotes = acc & cor & (kind == "SELECT")
                futas.append({"lezart": int(acc.sum()), "hibas": int((acc & ~cor).sum()),
                              "helyes_kotes": int(jo_kotes.sum()),
                              "tobblet_helyes_kotes": int((jo_kotes & ~termek_jo).sum()),
                              "uj_hiba_ahol_a_termek_jo": int((acc & ~cor & termek_jo).sum()),
                              "uj_hiba_ahol_a_termek_nem_kotott": int((acc & ~cor & ~termek_matched).sum()),
                              "reszfizetes_lezart": int((acc & reszf).sum()), "reszfizetes_hibas": int((acc & reszf & ~cor).sum()),
                              "kieg_lezart": int((acc & megold).sum()), "kieg_helyes_kotes": int((jo_kotes & megold).sum()),
                              "kieg_helyes_x": int((acc & megold & cor & (kind == "X")).sum()),
                              "kieg_hibas": int((acc & megold & ~cor).sum()),
                              "utkozes": int((acc & termek_matched & ~termek_szamla).sum()),
                              "utkozes_modell_jo": int((acc & termek_matched & ~termek_szamla & cor).sum()),
                              "utkozes_termek_jo": int((acc & termek_matched & ~termek_szamla & cimke_termek).sum()),
                              "utkozes_cimke_m": int((acc & termek_matched & ~termek_szamla & cimke_m).sum())})
            for x in futas:  # (3) a teljes folyamat: a termék helyes kötései + a modell többlete, a 262 tételen
                x["termek_plusz_modell_helyes_kotes"] = res["termek"].get("kötött, helyes", 0) + x["tobblet_helyes_kotes"]
                x["termek_plusz_kieg_helyes_kotes"] = res["termek"].get("kötött, helyes", 0) + x["kieg_helyes_kotes"]
            mp[arm] = {"nincs_munkapont": False, "atlag": {k: float(np.mean([x[k] for x in futas])) for k in futas[0]},
                       "futasok": futas}
        res["keretek"][kr] = {"n": len(ids), "helyes_dontes": int(cor.sum()), "tevesztes": {"|".join(k): v for k, v in sorted(conf.items())},
                              "kiegeszito_dontesek": {"|".join(k): v for k, v in sorted(kieg_tabla.items())}, "munkapont": mp}
    # (3) a teljes folyamat: helyesen megoldott párosítás a 262 tételen (a modell helyes kötése, ahol van helyes számla)
    res["teljes_folyamat_nevezo"] = len(meta)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "vegleges.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "vegleges.md").write_text(lap_vegleges(res), encoding="utf-8")
    print(lap_vegleges(res))


def lap_vegleges(res: dict) -> str:
    L = ["# 07B — végleges eredmény Dani vak címkéihez mérve", "",
         f"Tétel {res['n_tetel']}; K / N válasz miatt kimaradt {res['kihagyva_K_N']}; több számlát rendező (az egy-számlás "
         f"elemzésből kimarad, a teljes folyamatban megoldatlan) {res['tobb_szamla']}. A címkék: {res['cimke_allapot']}.", "",
         "## 1. A jelöltválasztás lefedése", "",
         f"Ahol létezik helyes számla: {res['jeloltlefedes']['van_helyes_szamla']}; ebből a listán: {res['jeloltlefedes']['a_listan']}.", "",
         "## A termék a címkékhez mérve", "", "| eset | n |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in sorted(res["termek"].items())]
    H = res["kiegeszito_hatokor"]
    for kr, R in res["keretek"].items():
        L += ["", f"## 2. A modell döntése a listán — {'négyállapotú keret' if kr == 'keret4' else '06-os keret (leíró)'}", "",
              f"Helyes döntés (szigorú): {R['helyes_dontes']} / {R['n']}.", "", "| címke | modell | n |", "|---|---|---|"]
        L += [f"| {k.split('|')[0]} | {k.split('|')[1]} | {v} |" for k, v in R["tevesztes"].items()]
        L += ["", "### 3. Kiegészítő értékelés: a modell a termék mellett (Dani, 11-02)", "",
              "A modell a meglévő kötést és kategóriát nem írja felül, csak a termék által megoldatlan tételre (se kötés, se "
              f"kategória) tesz javaslatot. Megoldatlan {H['megoldatlan']} tétel, ebből a modellhez került "
              f"{H['modellhez']}; a címkéik: {H['cimkek']}. A modell döntései rajtuk (τ nélkül): "
              + ", ".join(f"{k.replace('|', ' → ')} {v}" for k, v in R["kiegeszito_dontesek"].items()) + ". "
              "Ütközés: a termék a listán kötött, a modell a munkaponton mást mond (más számla vagy X); ez jelzés, nem hiba.", "",
              "| kar | lezárt a megoldatlanokon | ebből helyes kötés / helyes X / hibás | helyes párosítás: termék → termék + modell | ütközésjelzés | ebből a címke a modellt / a terméket igazolja / M |",
              "|---|---|---|---|---|---|"]
        for arm, m in R["munkapont"].items():
            if m["nincs_munkapont"]:
                L.append(f"| {arm} | nincs munkapont | – | – | – | – |")
                continue
            x = m["atlag"]
            tj = res["termek"].get("kötött, helyes", 0)
            L.append(f"| {arm} | {g(x['kieg_lezart'])} | {g(x['kieg_helyes_kotes'])} / {g(x['kieg_helyes_x'])} / {g(x['kieg_hibas'])} | "
                     f"{tj} → {g(x['termek_plusz_kieg_helyes_kotes'])} (/ {res['teljes_folyamat_nevezo']}) | {g(x['utkozes'])} | "
                     f"{g(x['utkozes_modell_jo'])} / {g(x['utkozes_termek_jo'])} / {g(x['utkozes_cimke_m'])} |")
        L += ["", "### Felülíró változat (leíró): munkapont a változatlan τ-val, a termékhez viszonyított többlet", "",
              "| kar | lezárt | ebből hibás | helyes kötés | többlet helyes kötés (a termék nem kötötte jól) | új hiba: a termék jó volt / nem kötött | részfizetés: lezárt / hibás | helyes párosítás a teljes folyamatban: termék → termék + modell |",
              "|---|---|---|---|---|---|---|---|"]
        for arm, m in R["munkapont"].items():
            if m["nincs_munkapont"]:
                L.append(f"| {arm} | nincs munkapont | – | – | – | – | – | – |")
                continue
            x = m["atlag"]
            tj = res["termek"].get("kötött, helyes", 0)
            L.append(f"| {arm} | {g(x['lezart'])} | {g(x['hibas'])} | {g(x['helyes_kotes'])} | {g(x['tobblet_helyes_kotes'])} | "
                     f"{g(x['uj_hiba_ahol_a_termek_jo'])} / {g(x['uj_hiba_ahol_a_termek_nem_kotott'])} | "
                     f"{g(x['reszfizetes_lezart'])} / {g(x['reszfizetes_hibas'])} | "
                     f"{tj} → {g(x['termek_plusz_modell_helyes_kotes'])} (/ {res['teljes_folyamat_nevezo']}) |")
    L += ["", f"A teljes folyamat nevezője: {res['teljes_folyamat_nevezo']} tétel (az üres listájúak és a több számlát "
          "rendezők megoldatlanként)."]
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ideiglenes")
    i.add_argument("--be", required=True)
    i.add_argument("--out", required=True)
    v = sub.add_parser("vegleges")
    v.add_argument("--be", required=True)
    v.add_argument("--cimkek", required=True)
    v.add_argument("--out", required=True)
    a = ap.parse_args()
    {"ideiglenes": ideiglenes, "vegleges": vegleges}[a.cmd](a)


if __name__ == "__main__":
    main()
