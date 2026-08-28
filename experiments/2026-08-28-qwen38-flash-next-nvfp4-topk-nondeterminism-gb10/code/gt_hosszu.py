#!/usr/bin/env python3
"""A HOSSZÚ KONTEXTUS suite (T21-T25) telepitett tenyei es szamolt ground truth-ja.

A `gen_d7.py` EBBOL a modulbol veszi a beultetett tenyeket, es az item-generator is
ugyaninnen — igy a korpusz es a GT nem tud elcsuszni.

Melysegek: a tenyeket a generator SZAMOLT karakterpoziciora illeszti be, a tenyleges
melyseget pedig visszameri es kiirja (nem becsuli).
"""
import random
from decimal import Decimal as D, ROUND_HALF_UP

MAG = 20260827                      # rogzitett mag — a korpusz reprodukalhato
CEL_KARAKTER = 453_800              # ⛔ MERVE: a D7 tablazatos szovege 1,973 karakter/token
                                    # (NEM 2,535, mint a prozai D1/D5) → ~230 000 token.
                                    # A 262 144-es ablakba a valasznak is be kell ferni.

# ─────────── T21 — haromugrasos szamitas, harom tavoli ponton ───────────
# ⛔ SZANDEKOSAN egesz ertekre jovo lanc: ez az item a HAROM TAVOLI TENY
# osszefuzeset meri, nem a kerekitesi fegyelmet (azt a T11 meri a nehez suite-ban).
# A csapdak igy tiszta „hop-hibak”: rossz evi oradij vagy osszeadott szazalekok.
T21_ORADIJ_2024 = 10000             # Ft/ora — a preambulumban (~3 %)
T21_EMELES_2025 = D("7.5")          # % — a korpusz kozepen (~50 %)
T21_EMELES_2026 = D("4.0")          # % — a korpusz vegen (~97 %)
T21_ORASZAM_2026 = 412              # ora — a korpusz vegen (~97 %)

def _ker(x: D) -> int:
    return int(x.quantize(D(1), rounding=ROUND_HALF_UP))

def t21_lanc() -> dict:
    o24 = D(T21_ORADIJ_2024)
    o25 = o24 * (1 + T21_EMELES_2025 / 100)
    o26 = o25 * (1 + T21_EMELES_2026 / 100)
    assert o25 == int(o25) and o26 == int(o26), "a lancnak egesz ertekekre kell jonnie"
    return {
        "oradij_2024": int(o24), "oradij_2025": int(o25), "oradij_2026": int(o26),
        "munkadij_2026": int(o26) * T21_ORASZAM_2026,
        # hop-hibak: melyik evi oradijjal szamolt, illetve osszeadta-e a szazalekokat
        "csapda_2024_oradij": int(o24) * T21_ORASZAM_2026,
        "csapda_2025_oradij": int(o25) * T21_ORASZAM_2026,
        "csapda_osszeadott_szazalek": _ker(o24 * (1 + (T21_EMELES_2025 + T21_EMELES_2026) / 100))
                                      * T21_ORASZAM_2026,
    }

# ─────────── T22 — teljes koru aggregacio ───────────
T22_JELOLO = "RENDKÍVÜLI BEAVATKOZÁS"
T22_DARAB = 43                      # ennyi valodi esemeny szorodik szet
T22_ALHANG_DARAB = 31               # near-miss: „rendkivuli karbantartasi igeny” jelolo NELKUL

def t22_esemenyek():
    """Determinisztikus koltseglista — a generator ES a GT ugyanezt hasznalja."""
    r = random.Random(MAG + 22)
    return [r.randrange(40, 260) * 1000 for _ in range(T22_DARAB)]

def t22_ossz() -> int:
    return sum(t22_esemenyek())

# ─────────── T23 — kesoi felulirás ───────────
T23_KORAI_NAP = 5                   # a preambulum 3.4. pontja (~2 %)
T23_KESOI_NAP = 3                   # a zaro rendelkezes Z.7. pontja (~99,5 %)
T23_KESOI_PONT = "Z.7"
T23_HATALY = "2026-12-01"

# ─────────── T24 — 40 hasonmas hibajegy ───────────
T24_DARAB = 40
T24_PRIORITASOK = ["normál", "emelt", "kiemelt"]
T24_ALLAPOTOK = ["lezárt", "lezáratlan"]

def t24_hibajegyek():
    """Pontosan EGY rekord `kiemelt` + `lezáratlan`; a tobbi kozelito talalat."""
    r = random.Random(MAG + 24)
    teruletek = ["gépészet", "elektromos hálózat", "épületszerkezet", "informatika",
                 "vízellátás", "hűtés-fűtés", "beléptetés", "tűzvédelem"]
    ki = []
    nyertes_idx = 27                        # rogzitett, hogy a GT ne fusson el
    for i in range(T24_DARAB):
        az = f"HJ-2026-{i+1:04d}"
        if i == nyertes_idx:
            pri, all_ = "kiemelt", "lezáratlan"
        else:
            # kozelito talalatok: kiemelt+lezart ES normal/emelt+lezaratlan is legyen
            pri = r.choice(T24_PRIORITASOK)
            all_ = r.choice(T24_ALLAPOTOK)
            if pri == "kiemelt" and all_ == "lezáratlan":
                all_ = "lezárt"             # csak a nyertes lehet kiemelt+lezaratlan
        ki.append({"azonosito": az, "prioritas": pri, "allapot": all_,
                   "terulet": r.choice(teruletek),
                   "bejelentve": f"2026-{r.randrange(1,13):02d}-{r.randrange(1,29):02d}"})
    return ki

def t24_nyertes() -> dict:
    return next(h for h in t24_hibajegyek()
                if h["prioritas"] == "kiemelt" and h["allapot"] == "lezáratlan")

# ─────────── T25 — melysegprofil: 5 tu, 5 kontrollalt melysegben ───────────
# (cel_melyseg, mezonev, a beultetett mondat, a helyes ertek)
T25_TUK = [
    (0.05, "tetoszigeteles_garancia_lejar",
     "A tetőszigetelés kivitelezői garanciája **2029. április 30-án** jár le.",
     "2029-04-30"),
    (0.25, "aggregat_tipusjel",
     "A tartalék dízelaggregát típusjele: **GX-7420/B**.",
     "GX-7420/B"),
    (0.50, "vizora_gyari_szam",
     "A főmérő vízóra gyári száma: **HU-3391-882**.",
     "HU-3391-882"),
    (0.75, "liftkarbantarto_szerzodesszam",
     "A liftkarbantartási szerződés száma: **LK-2025/117**.",
     "LK-2025/117"),
    (0.95, "tuzjelzo_felulvizsgalat",
     "A tűzjelző központ utolsó felülvizsgálata **2026. október 8-án** történt.",
     "2026-10-08"),
]

def t25_gt() -> dict:
    return {mezo: ertek for _, mezo, _, ertek in T25_TUK}

if __name__ == "__main__":
    l = t21_lanc()
    print("── T21 ──")
    print(f"  2024: {l['oradij_2024']} Ft/óra")
    print(f"  2025: {l['oradij_2025']} Ft/óra  (+{T21_EMELES_2025} %)")
    print(f"  2026: {l['oradij_2026']} Ft/óra  (+{T21_EMELES_2026} %)")
    print(f"  2026. évi munkadíj: {l['oradij_2026']} × {T21_ORASZAM_2026} = "
          f"{l['munkadij_2026']:,} Ft".replace(",", " "))
    for nev in ("csapda_2024_oradij", "csapda_2025_oradij", "csapda_osszeadott_szazalek"):
        print(f"  {nev:28s}: {l[nev]:,} Ft".replace(",", " "))
        assert l[nev] != l["munkadij_2026"], f"a(z) {nev} csapda egybeesik a helyes válasszal"

    print("\n── T22 ──")
    e = t22_esemenyek()
    print(f"  {len(e)} esemény, összesen {t22_ossz():,} Ft".replace(",", " "))
    print(f"  near-miss (jelölő nélküli) tételek: {T22_ALHANG_DARAB}")
    assert len(e) == T22_DARAB

    print("\n── T24 ──")
    h = t24_hibajegyek()
    ny = t24_nyertes()
    kiemelt = sum(1 for x in h if x["prioritas"] == "kiemelt")
    lezaratlan = sum(1 for x in h if x["allapot"] == "lezáratlan")
    egyuttes = [x for x in h if x["prioritas"] == "kiemelt" and x["allapot"] == "lezáratlan"]
    print(f"  {len(h)} hibajegy · kiemelt: {kiemelt} · lezáratlan: {lezaratlan} · "
          f"MINDKETTŐ: {len(egyuttes)}")
    print(f"  nyertes: {ny['azonosito']} ({ny['terulet']}, bejelentve {ny['bejelentve']})")
    assert len(egyuttes) == 1, "nem pontosan egy rekord felel meg a két feltételnek"
    assert kiemelt >= 6 and lezaratlan >= 10, "kevés a közelítő találat — túl könnyű az item"

    print("\n── T25 ──")
    for m, mezo, _, ertek in T25_TUK:
        print(f"  {m*100:5.1f} %  {mezo:32s} → {ertek}")
