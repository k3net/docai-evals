"""E irány — a publikus csapdatétel-adatkészlet összeállítása (publikacio/E-adatkeszlet-terv.md; Dani 2026-11-20).

Csak szintetikus tételfájlokból dolgozik (06–08-as kör); valódi adatból származó könyvtárat nem olvas.

  epit     → publikacio/E/data/<konfig>/<split>.jsonl, publikacio/E/_belso_terkep.jsonl (eredeti id → új id; nem megy ki),
             publikacio/E/export_riport.json
  ellenor  a kész fájlokon: egyedi azonosítók, a párok és egységek épsége, tiltott minták, számlaszámok → ellenor_riport.json

Konfigurációk (Dani döntései: az `interpretation` csak a költségelszámolás-család; a 08 M és a 08 J kimarad):
  calc_traps      07 K3diag + 08 G2 k3 + 07 nehez3, mind MATCH, test
  minimal_pairs   08 N, test
  interpretation  08 G2 ert_teszt (test) + ert_tanito (train), csak szabaly.koltsegelszamolas
  natural         06 + 07 + 08 friss; T500 és CAL → train, TESZT → test
Névcsere: a generáló prompt példájából beszivárgott „Kristály Kft.” / „Ezüst Kft.” a magyar szövegekben (zömmel a
hibaelhárítás-családban) a kódbeli névlistából képzett névre cserélődik, a tétel eredeti azonosítójából képzett seeddel (determinisztikus).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXP = Path(__file__).resolve().parents[2]
OUT = EXP / "publikacio/E"
SALT = "hu-decision-trap-items:v1:"
FAMILY = {"penzugy.bankparositas": "finance.bank_matching", "muszaki.hibaelharitas": "technical.troubleshooting", "szabaly.koltsegelszamolas": "policy.expense_claims"}
CSALADOK = list(FAMILY)
TRAP = {"B3a-reszfizetes": "partial_payment", "B3b-betuvel": "amount_in_words", "H3-valtas": "unit_conversion", "S3a-netto": "net_vs_gross", "S3b-deviza": "currency"}
# a kor03 `kie03.py` névlistájából a mássalhangzóval kezdődő gyökök (a névelő „A” marad), a két beszivárgott szóra hasonlítók nélkül
ROOTS = ["Tiszavirág", "Bakonyfenyő", "Mecsekalja", "Hajnalpír", "Napfényliget", "Zöldmező", "Vértesvölgy", "Mátraalja", "Pannonkő", "Rétköz",
         "Kékgolyó", "Szélmalom", "Tölgyliget", "Fürjes", "Somlyó", "Hegyhát", "Csillagfürt", "Kőhíd"]
ACTIVITIES = ["Kereskedelmi", "Szolgáltató", "Építőipari", "Informatikai", "Logisztikai", "Ipari", "Agrár", "Irodatechnikai", "Vendéglátó", "Mérnöki"]
NEV_RE = re.compile(r"(?:\b(A|a|Az|az)\s+)?(Kristály|Ezüst) Kft\b\.?")
FORRASOK = [  # (konfig, kör, könyvtár, családok, split-leképezés)
    ("calc_traps", "07-k3diag", "kor07/adat/diag", CSALADOK, {"DIAG": "test"}),
    ("calc_traps", "08-k3", "kor08/adat/G2/k3", CSALADOK, {"G2K3": "test"}),
    ("calc_traps", "07-pilot3", "kor07/adat/nehez3", CSALADOK, {"NEHEZ": "test"}),
    ("minimal_pairs", "08-n", "kor08/adat/N", CSALADOK[2:], {"N1T": "test"}),
    ("interpretation", "08-interp", "kor08/adat/G2/ert_teszt", CSALADOK[2:], {"G2T": "test"}),
    ("interpretation", "08-interp", "kor08/adat/G2/ert_tanito", CSALADOK[2:], {"G2N": "train"}),
    ("natural", "06", "kor06/adat/f2", CSALADOK, {"T500": "train", "CAL": "train", "TESZT": "test"}),
    ("natural", "07", "kor07/adat/f2", CSALADOK, {"CAL": "train", "TESZT": "test"}),
    ("natural", "08", "kor08/adat/G2/friss", CSALADOK, {"CAL": "train", "TESZT": "test"}),
]
# Kizárás a kiadásból (a független tényellenőrzés lelete, 2026-11-22): valódi bank neve, nem példa-domaines vagy törött
# e-mail-cím, valódi domain, valós személy neve. Páros vagy egységes konfigurációban az egész egység kiesik.
KIZAR = {"valodi_bank": r"\b(OTP|UniCredit|Raiffeisen|Takarék\w*|Erste|K&H|CIB|MKB|MBH|Gránit Bank|Budapest Bank|Barclays|HSBC|Lloyds|NatWest|Santander|Revolut|Citibank|Wells Fargo|JPMorgan|Chase Bank|Bank of America|Monzo|Starling)\b",
         "email_nem_pelda_vagy_torott": r"@(?![\w.-]*pelda\.example)", "valodi_domain": r"\b(?!pelda\.example)[\w-]+\.(?:hu|com|net|org|io|eu|co\.uk)\b",
         "valos_szemely": r"Arany János",
         # a névösszevetés (e_nevek.py, 2026-11-22) nyomán: ismert valódi szervezet, vagy a modell kitalálta, de valódi cég neve
         "valodi_szervezet": r"(?i)dunapack|nemzeti adó.{0,3}és vámhivatal|pannon egyetem|project management institute|riverside hotel|hotel tisza|zöldfény kft|\bfény kft"}
MANIFESTEK = ["kor06/rogzites/v1/MANIFEST.sha256", "kor07/rogzites/v1/MANIFEST.sha256", "kor07/rogzites/pecset/K07K3.json", "kor08/rogzites/pecset/K08G3.g4.json"]


def h(s: str, n: int = 16) -> str:
    return hashlib.sha256((SALT + s).encode()).hexdigest()[:n]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def nevcsere(text: str, oid: str, kerul: str) -> tuple[str, int]:
    """`kerul`: a tétel teljes szövege az opciókkal; az új név gyöke ebben nem szerepelhet (ne ütközzön a tétel más cégével)."""
    uj, n = {}, 0
    roots = [r for r in ROOTS if r not in kerul]

    def csere(m):
        nonlocal n
        n += 1
        k = m.group(2)
        if k not in uj:
            d = hashlib.sha256(f"{SALT}nev:{oid}:{k}".encode()).digest()
            uj[k] = f"{roots[d[0] % len(roots)]} {ACTIVITIES[d[1] % len(ACTIVITIES)]} Kft."
            if len(uj) == 2 and len(set(uj.values())) == 1:  # a két név ne essen egybe
                uj[k] = f"{roots[(d[0] + 1) % len(roots)]} {ACTIVITIES[d[1] % len(ACTIVITIES)]} Kft."
        nevelo = {"A": "A ", "Az": "A ", "a": "a ", "az": "a "}.get(m.group(1) or "", "")
        return nevelo + uj[k]

    return NEV_RE.sub(csere, text), n


def epit(_a) -> None:
    manifest_szoveg = "".join((EXP / m).read_text(encoding="utf-8") for m in MANIFESTEK)
    manifest_szoveg += "".join(p.read_text(encoding="utf-8") for p in (EXP / "kor08/rogzites").rglob("*") if p.is_file() and p.suffix in (".json", ".sha256") and p.stat().st_size < 2_000_000)
    ki, terkep, rip = defaultdict(list), [], {"forrasok": [], "nevcsere": Counter()}
    for konfig, kor, d, csaladok, splitek in FORRASOK:
        for cs in csaladok:
            p = EXP / d / "items" / f"{cs}.jsonl"
            its = jsonl(p)
            s = sha(p)
            terv = {t["group_id"]: t for t in jsonl(EXP / d / "terv" / f"{cs}.jsonl")} if konfig == "calc_traps" else {}
            rip["forrasok"].append({"konfig": konfig, "kor": kor, "fajl": str(p.relative_to(EXP)), "n": len(its), "sha256": s, "manifestben": s in manifest_szoveg})
            for it in its:
                kerul = "\n".join([it["state"], *[o["text"] for o in it["options"]]])
                text, n = nevcsere(it["state"], it["id"], kerul) if it["lang"] == "hu" else (it["state"], 0)
                rip["nevcsere"][f"{konfig}:{'cserelt' if n else 'valtozatlan'}"] += 1
                e = it["meta"].get("ertelmezes") or {}
                sor = {"id": "dti-" + h(it["id"]), "config": konfig, "split": splitek[it["split"]], "family": FAMILY[cs], "lang": it["lang"], "text": text,
                       "question": it["question"], "options": it["options"], "answer": it["gold"], "label": it["content_state"],
                       "template_group": "tg-" + h(it["template_group_id"], 12), "source_round": kor, "name_replaced": bool(n),
                       "original_text_sha256": hashlib.sha256(it["state"].encode()).hexdigest()}
                if konfig == "calc_traps":
                    sor["trap_type"] = TRAP[terv[it["group_id"]]["nehez"]["valt"]]
                if konfig in ("minimal_pairs", "interpretation"):
                    sor["unit_id"] = "u-" + h(f"{konfig}:{e['egyseg']}", 12)
                    sor["has_deciding_signal"] = e["alt"] == "b"
                    sor["scenario"] = "sc-" + h(str(e.get("forgatokonyv")), 8)
                if konfig == "minimal_pairs":
                    sor["pair_id"] = "p-" + h(f"{e['egyseg']}:{it['meta']['illesztes']}", 12)
                    # a forgatókönyvek párban állnak (az egyik döntő mondata a másik semleges mondata): keresztvalidációhoz ezt kell csoportnak venni
                    sor["scenario_group"] = "sg-" + h("|".join(sorted([str(e["forgatokonyv"]), str(it["meta"]["illesztes"]["par"])])), 8)
                if (it["gold"] is None) != (it["content_state"] != "MATCH"):
                    raise SystemExit(f"gold és állapot ellentmond: {it['id']}")
                ki[(konfig, sor["split"])].append(sor)
                terkep.append({"id": sor["id"], "eredeti": it["id"], "forras": str(p.relative_to(EXP))})
    kizart, rossz_egyseg = Counter(), set()
    for (konfig, split), sorok in ki.items():
        for r in sorok:
            t = "\n".join([r["text"], r["question"], *[o["text"] for o in r["options"]]])
            r["_ok"] = next((k for k, rx in KIZAR.items() if re.search(rx, t)), None)
            if r["_ok"] and "unit_id" in r:
                rossz_egyseg.add((konfig, r["unit_id"]))
    for kulcs, sorok in ki.items():
        marad = []
        for r in sorok:
            ok = r.pop("_ok")
            if ok or (kulcs[0], r.get("unit_id")) in rossz_egyseg:
                kizart[f"{kulcs[0]}/{kulcs[1]}:{ok or 'az_egyseg_tarsa'}"] += 1
            else:
                marad.append(r)
        ki[kulcs] = marad
    megy = {r["id"] for v in ki.values() for r in v}
    terkep = [t for t in terkep if t["id"] in megy]
    rip["kizart"] = dict(sorted(kizart.items()))
    for (konfig, split), sorok in ki.items():
        sorok.sort(key=lambda r: r["id"])
        f = OUT / "data" / konfig / f"{split}.jsonl"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in sorok), encoding="utf-8")
    (OUT / "_belso_terkep.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in terkep), encoding="utf-8")
    rip["nevcsere"] = dict(sorted(rip["nevcsere"].items()))
    rip["kimenet"] = {f"{k}/{s}": {"n": len(v), "sha256": sha(OUT / "data" / k / f"{s}.jsonl"), "label": dict(sorted(Counter(r["label"] for r in v).items())),
                                   "lang": dict(sorted(Counter(r["lang"] for r in v).items())), "family": dict(sorted(Counter(r["family"] for r in v).items()))}
                      for (k, s), v in sorted(ki.items())}
    rip["trap_type"] = dict(sorted(Counter(f"{r['family']}:{r['trap_type']}" for r in ki[("calc_traps", "test")]).items()))
    (OUT / "export_riport.json").write_text(json.dumps(rip, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"kimenet": {k: v["n"] for k, v in rip["kimenet"].items()}, "nevcsere": rip["nevcsere"], "kizart": rip["kizart"], "trap_type": rip["trap_type"],
                      "nincs_manifestben": [f["fajl"] for f in rip["forrasok"] if not f["manifestben"]]}, ensure_ascii=False, indent=1))


def iban_ervenyes(s: str) -> bool:
    s = re.sub(r"\s", "", s).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}", s):
        return False
    return int("".join(str(int(c, 36)) for c in s[4:] + s[:4])) % 97 == 1


def giro_ervenyes(s: str) -> bool:
    """Magyar belföldi számlaszám (2 vagy 3 × 8 jegy): az első 8 és a maradék külön 9-7-3-1 súlyozású ellenőrzőösszege."""
    d = re.sub(r"\D", "", s)
    if len(d) not in (16, 24):
        return False
    ok = lambda x: sum(int(c) * w for c, w in zip(x, [9, 7, 3, 1] * 6)) % 10 == 0  # noqa: E731
    return ok(d[:8]) and ok(d[8:])


def ellenor(_a) -> None:
    sorok = [r for p in sorted((OUT / "data").rglob("*.jsonl")) for r in jsonl(p)]
    rip = {"n": len(sorok), "egyedi_id": len({r["id"] for r in sorok}) == len(sorok)}
    szoveg = lambda r: "\n".join([r["text"], r["question"], *[o["text"] for o in r["options"]]])  # noqa: E731
    mintak = {"kristaly_ezust_kft": r"(Kristály|Ezüst) Kft", "url": r"https?://|www\.", "email_nem_pelda": r"[\w.+-]+@(?![\w.-]*\.example\b)[\w-]+\.[\w.-]+",
              "telefon_nem_555": r"\+36[ -]?(?!1[ -]?555)\d[\d -]{6,}", "eredeti_id_minta": r":(MATCH|NO_MATCH|MISSING_DATA|OUT_OF_SCOPE):"}
    rip["mintak"] = {k: sum(bool(re.search(v, szoveg(r))) for r in sorok) for k, v in mintak.items()}
    rip["id_allapotot_arul_el"] = sum(any(s in r["id"] or s in r["template_group"] for s in ("MATCH", "MISSING", "SCOPE")) for r in sorok)
    iban, giro = Counter(), Counter()
    for r in sorok:
        t = szoveg(r)
        for m in re.finditer(r"\b[A-Z]{2}\d{2}(?:[ -]?[A-Z0-9]{4}){3,7}(?:[ -]?[A-Z0-9]{1,4})?\b", t):
            iban["ervenyes" if iban_ervenyes(m.group(0)) else "ervenytelen"] += 1
        for m in re.finditer(r"\b\d{8}-\d{8}(?:-\d{8})?\b", t):
            giro["ervenyes" if giro_ervenyes(m.group(0)) else "ervenytelen"] += 1
    rip["iban_alaku"], rip["belfoldi_szamlaszam_alaku"] = dict(iban), dict(giro)
    par = defaultdict(list)
    for r in sorok:
        if r["config"] == "minimal_pairs":
            par[r["pair_id"]].append(r)
    rip["minimal_pairs"] = {"par": len(par), "ep": sum(len(v) == 2 and {x["label"] for x in v} == {"MATCH", "MISSING_DATA"} and len({x["lang"] for x in v}) == 1 for v in par.values())}
    egys = defaultdict(list)
    for r in sorok:
        if r["config"] == "interpretation":
            egys[r["unit_id"]].append(r["label"])
    rip["interpretation"] = {"egyseg": len(egys), "szerkezet": {str(k): v for k, v in Counter(tuple(sorted(Counter(v).items())) for v in egys.values()).items()}}
    tg = defaultdict(set)
    for r in sorok:
        tg[(r["config"], r["template_group"])].add(r["split"])
    rip["sabloncsoport_tobb_splitben"] = sum(len(v) > 1 for v in tg.values())
    dup = Counter(hashlib.sha256(szoveg(r).encode()).hexdigest() for r in sorok)
    rip["azonos_szoveg_es_opciok"] = sum(v - 1 for v in dup.values() if v > 1)
    hu = [r for r in sorok if r["family"] == "technical.troubleshooting" and r["lang"] == "hu"]
    nev = Counter(m.group(0) for r in hu for m in re.finditer(r"[A-ZÁÉÍÓÖŐÚÜŰ][\wáéíóöőúüű]+(?: [A-ZÁÉÍÓÖŐÚÜŰ][\wáéíóöőúüű]+)? Kft\.", r["text"]))
    rip["hibaelharitas_hu"] = {"n": len(hu), "kulonbozo_cegnev": len(nev), "leggyakoribb": nev.most_common(3)}
    en = [r for r in sorok if r["family"] == "technical.troubleshooting" and r["lang"] == "en"]
    nev_en = Counter(m.group(0) for r in en for m in re.finditer(r"[A-Z][\w&-]+(?: [A-Z][\w&-]+)? (?:Ltd|LLC|Inc|Corp|GmbH|Co)\b\.?", r["text"]))
    rip["hibaelharitas_en"] = {"n": len(en), "kulonbozo_cegnev": len(nev_en), "leggyakoribb": nev_en.most_common(3)}
    (OUT / "ellenor_riport.json").write_text(json.dumps(rip, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(rip, ensure_ascii=False, indent=1))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("epit")
    sub.add_parser("ellenor")
    a = ap.parse_args()
    {"epit": epit, "ellenor": ellenor}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
