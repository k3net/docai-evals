#!/usr/bin/env python3
"""A NEHÉZ suite (T11–T20) számolt ground truth-ja.

⛔⛔ Minden érték SZÁMOLT, egyetlen szám sincs beírva. A D6 dokumentumot a
`gen_d6.py` UGYANEZEKBŐL az értékekből írja ki, így a korpusz és a GT nem tud
elcsúszni egymástól.
"""
from datetime import date, timedelta
from decimal import Decimal as D, ROUND_CEILING
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from munkarend import munkanap

# ─────────────────────── T11 — kumulált indexálás ───────────────────────
INDEX_BAZIS = 2100000          # a D1 2. sz. módosítás 3. pontja szerinti hatályos Díj
INDEX_PLAFON = D("6")          # %, a D1 1. sz. módosítás 3. pontja szerinti felső határ
KEREKITES = 10000              # Ft, MINDEN lépésben felfelé (D6 7.3)
KSH_INDEX = {2026: D("7.4"), 2027: D("3.8"), 2028: D("5.1")}   # D6 7.2 táblázat

def _felfele(x: D, egyseg: int) -> int:
    return int((x / egyseg).quantize(D(1), rounding=ROUND_CEILING) * egyseg)

def indexalas_lanc():
    """Évenkénti indexálás: a KÖVETKEZŐ év alapja a KEREKÍTETT összeg (D6 7.3)."""
    ki, alap = [], D(INDEX_BAZIS)
    for ev in sorted(KSH_INDEX):                     # 2026 indexe → 2027-01-01-i emelés
        nyers_szazalek = KSH_INDEX[ev]
        alkalmazott = min(nyers_szazalek, INDEX_PLAFON)
        emelt = alap * (1 + alkalmazott / 100)
        kerekitett = _felfele(emelt, KEREKITES)
        ki.append({"hatalyos": date(ev + 1, 1, 1).isoformat(),
                   "index_eve": ev, "ksh_index": float(nyers_szazalek),
                   "alkalmazott_szazalek": float(alkalmazott),
                   "plafonozva": nyers_szazalek > INDEX_PLAFON,
                   "kerekites_elott": float(emelt), "dij_ft": kerekitett})
        alap = D(kerekitett)
    return ki

def indexalas_csak_veges_kerekitessel() -> int:
    """A CSAPDA-változat: kerekítés csak a végén (ezt NEM fogadjuk el)."""
    alap = D(INDEX_BAZIS)
    for ev in sorted(KSH_INDEX):
        alap = alap * (1 + min(KSH_INDEX[ev], INDEX_PLAFON) / 100)
    return _felfele(alap, KEREKITES)

def indexalas_plafon_nelkul() -> int:
    """A CSAPDA-változat: a 6 %-os felső határ figyelmen kívül hagyva."""
    alap = D(INDEX_BAZIS)
    for ev in sorted(KSH_INDEX):
        alap = D(_felfele(alap * (1 + KSH_INDEX[ev] / 100), KEREKITES))
    return int(alap)

# ─────────────────────── T15 — deviza-vegyes aggregáció ───────────────────────
ALAPTERULET_M2 = 1240
UZEMELTETESI_EUR_M2_HO = D("3.20")
ARFOLYAM = D("412.50")            # D6 3.4 — a Megállapodásban RÖGZÍTETT árfolyam
ARFOLYAM_CSALI = D("398.00")      # D6 3.5 — tájékoztató jellegű, NEM ezt kell alkalmazni
PARKOLO_FT_HO = 84000
BIZTONSAGI_FT_EV = 1860000
KERTESZET_FT_HO = 38000

def eves_uzemeltetesi_koltseg(arfolyam: D = ARFOLYAM) -> dict:
    eur_ho = UZEMELTETESI_EUR_M2_HO * ALAPTERULET_M2
    ft_ho = eur_ho * arfolyam
    tetelek = {
        "uzemeltetes": int(ft_ho * 12),
        "parkolo": PARKOLO_FT_HO * 12,
        "biztonsagi": BIZTONSAGI_FT_EV,
        "kerteszet": KERTESZET_FT_HO * 12,
    }
    return {"tetelek": tetelek, "eur_ho": float(eur_ho), "ft_ho": int(ft_ho),
            "osszesen": sum(tetelek.values())}

# ─────────────────────── T16 — banki nap + gördítés ───────────────────────
def ev_utolso_munkanapja(ev: int) -> date:
    d = date(ev, 12, 31)
    while not munkanap(d):
        d -= timedelta(days=1)
    return d

def banki_nap(d: date) -> bool:
    """D6 6.2: banki nap = munkanap, KIVÉVE a naptári év utolsó munkanapját."""
    return munkanap(d) and d != ev_utolso_munkanapja(d.year)

def hatarido_banki_nap(kezhezvetel: date, n: int) -> date:
    d, c = kezhezvetel, 0
    while c < n:
        d += timedelta(days=1)
        if banki_nap(d):
            c += 1
    return d

T16_KEZHEZVETEL = date(2026, 12, 16)   # ⛔ MÉRVE: itt tér el a banki nap a munkanaptól
T16_NAPOK = 10

def hatarido_munkanapban(kezhezvetel: date, n: int) -> date:
    d, c = kezhezvetel, 0
    while c < n:
        d += timedelta(days=1)
        if munkanap(d):
            c += 1
    return d

# ─────────────────────── T13 — betűvel vs számmal ───────────────────────
BELEPESI_DIJ_SZAMMAL = 2480000
BELEPESI_DIJ_BETUVEL = 2840000        # ⛔ SZÁNDÉKOS eltérés; a D6 4.4 szerint EZ az irányadó
BELEPESI_DIJ_BETUVEL_SZOVEG = "kettőmillió-nyolcszáznegyvenezer"

# ─────────────────────── T12 — ellentmondás-feloldás ───────────────────────
FELMONDAS_TORZS_NAP = 90              # D6 5.2 törzsszöveg
FELMONDAS_MELLEKLET_NAP = 120         # D6 1. sz. melléklet 3. pont — EZ nyer (D6 2.1 sorrend)
# ⛔ Az Alapszerződés RENDES felmondást nem ismer (D1 3.3.) — nincs versengő harmadik
# érték. Csali viszont a D1 11.2. pontjában szereplő 60 nap, amely a RENDKÍVÜLI
# felmondás díjkésedelmi küszöbe, nem felmondási idő.
ALAPSZERZODES_REND_FELMONDAS = False

# ─────────────────────── T20 — eldönthetetlen ───────────────────────
UZEMELTETO_VAGYONI_PLAFON_FT = 5000000   # D6 10.2 — CSAK vagyoni kárra; személyi sérülésre NINCS

if __name__ == "__main__":
    print("── T11 kumulált indexálás ──")
    for s in indexalas_lanc():
        print(f"  {s['hatalyos']}  KSH {s['ksh_index']:>4} %  → alkalmazott {s['alkalmazott_szazalek']} % "
              f"{'(PLAFONOZVA)' if s['plafonozva'] else '':13s} kerekítés előtt {s['kerekites_elott']:>12,.2f} "
              f"→ {s['dij_ft']:,} Ft".replace(",", " "))
    print(f"  csapda — kerekítés csak a végén: {indexalas_csak_veges_kerekitessel():,} Ft".replace(",", " "))
    print(f"  csapda — plafon nélkül:          {indexalas_plafon_nelkul():,} Ft".replace(",", " "))

    print("\n── T15 éves üzemeltetési költség ──")
    e = eves_uzemeltetesi_koltseg()
    print(f"  {UZEMELTETESI_EUR_M2_HO} EUR/m²/hó × {ALAPTERULET_M2} m² = {e['eur_ho']:,.2f} EUR/hó "
          f"× {ARFOLYAM} = {e['ft_ho']:,} Ft/hó".replace(",", " "))
    for k, v in e["tetelek"].items():
        print(f"    {k:14s} {v:>12,} Ft/év".replace(",", " "))
    print(f"    {'ÖSSZESEN':14s} {e['osszesen']:>12,} Ft/év".replace(",", " "))
    print(f"  csapda — csali árfolyammal ({ARFOLYAM_CSALI}): "
          f"{eves_uzemeltetesi_koltseg(ARFOLYAM_CSALI)['osszesen']:,} Ft/év".replace(",", " "))

    print("\n── T16 banki nap ──")
    NAP = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]
    kez = T16_KEZHEZVETEL
    b = hatarido_banki_nap(kez, T16_NAPOK)
    m = hatarido_munkanapban(kez, T16_NAPOK)
    print(f"  2026 utolsó munkanapja: {ev_utolso_munkanapja(2026)} "
          f"({NAP[ev_utolso_munkanapja(2026).weekday()]}) — NEM banki nap")
    print(f"  kézhezvétel {kez} ({NAP[kez.weekday()]})")
    print(f"    {T16_NAPOK} BANKI nap → {b} ({NAP[b.weekday()]})")
    print(f"    {T16_NAPOK} MUNKAnap  → {m} ({NAP[m.weekday()]})   ← a csapda-válasz")
    assert b != m, "a banki nap és a munkanap NEM térhet el ugyanarra a napra — az item értéktelen lenne"

    print("\n── T13 betűvel vs számmal ──")
    print(f"  számmal {BELEPESI_DIJ_SZAMMAL:,} Ft · betűvel {BELEPESI_DIJ_BETUVEL:,} Ft "
          f"({BELEPESI_DIJ_BETUVEL_SZOVEG}) → a D6 4.4 szerint a BETŰVEL kiírt az irányadó"
          .replace(",", " "))
