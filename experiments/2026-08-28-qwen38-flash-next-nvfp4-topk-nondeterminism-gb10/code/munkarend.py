#!/usr/bin/env python3
"""Munkanap-számítás a corpus/D2.md 2. sz. melléklete szerint.

⛔ A munkarend forrása a KORPUSZ, nem külső rendelet — így a ground truth
determinisztikus és a mérés reprodukálható. A 2026-os áthelyezett munkanapok
a korpuszban DEKLARÁLTAK (fiktív, de az iratban kimondott érték); az áthelyezés
a valós 2026-os miniszteri rendelettel nem feltétlenül egyezik, és nem is kell,
hogy egyezzen: a teszt azt méri, hogy a modell az IRATBAN adott naptárt alkalmazza-e.

Szabály (D2 7.2.): a kézhezvétel napja nem számít bele; a határidő a kézhezvételt
követő első munkanapon kezdődik, és az N-edik munkanap letelte a lejárat napja.
"""
from datetime import date, timedelta

MUNKASZUNETI = {
    date(2026, 1, 1), date(2026, 3, 15), date(2026, 4, 3), date(2026, 4, 6),
    date(2026, 5, 1), date(2026, 5, 25), date(2026, 8, 20), date(2026, 10, 23),
    date(2026, 11, 1), date(2026, 12, 25), date(2026, 12, 26),
    date(2027, 1, 1), date(2027, 3, 15), date(2027, 3, 26), date(2027, 3, 29),
    date(2027, 5, 1), date(2027, 5, 17), date(2027, 8, 20), date(2027, 10, 23),
    date(2027, 11, 1), date(2027, 12, 25), date(2027, 12, 26),
}
# pihenőnappá tett hétköznap -> helyette ledolgozott szombat
ATHELYEZETT_PIHENO = {date(2026, 1, 2), date(2026, 8, 21)}
ATHELYEZETT_MUNKANAP = {date(2026, 1, 10), date(2026, 8, 8)}

def munkanap(d: date) -> bool:
    if d in ATHELYEZETT_MUNKANAP:
        return True
    if d in ATHELYEZETT_PIHENO or d in MUNKASZUNETI:
        return False
    return d.weekday() < 5

def hatarido_munkanap(kezhezvetel: date, n: int) -> date:
    """N munkanap a kézhezvételtől; a kézhezvétel napja nem számít bele."""
    d = kezhezvetel
    szamlalt = 0
    while szamlalt < n:
        d += timedelta(days=1)
        if munkanap(d):
            szamlalt += 1
    return d

def hatarido_naptari(kezhezvetel: date, n: int) -> date:
    """N naptári nap a kézhezvételtől; a kézhezvétel napja nem számít bele."""
    return kezhezvetel + timedelta(days=n)

def honap_utolso_napja(d: date) -> date:
    nxt = date(d.year + (d.month == 12), (d.month % 12) + 1, 1)
    return nxt - timedelta(days=1)

if __name__ == "__main__":
    NAP = ["hétfő", "kedd", "szerda", "csütörtök", "péntek", "szombat", "vasárnap"]
    esetek = [
        ("T3-01", "számla kézhezvétel, fizetési határidő 15 munkanap (D2 3.4.)",
         date(2026, 10, 19), "munkanap", 15),
        ("T3-02", "számla kézhezvétel, fizetési határidő 15 munkanap — augusztusi áthelyezés (D2 3.4. + 2. sz. mell.)",
         date(2026, 7, 31), "munkanap", 15),
        ("T3-03", "számla kézhezvétel, kifogásolási határidő 8 NAPTÁRI nap (D2 3.5.)",
         date(2026, 10, 19), "naptári nap", 8),
        ("T3-04", "hibabejelentés kézhezvétele, javítási határidő 10 munkanap (D2 7.4.)",
         date(2026, 12, 18), "munkanap", 10),
        ("T3-05", "készre jelentés legalább 5 munkanappal a teljesítés (2026-11-30) előtt (D2 7.6.)",
         None, "különleges", 5),
    ]
    for eid, leiras, kez, mod, n in esetek:
        if eid == "T3-05":
            d = date(2026, 11, 30); c = 0
            while c < n:
                d -= timedelta(days=1)
                if munkanap(d):
                    c += 1
            print(f"{eid}  {d} {NAP[d.weekday()]:10s} | legkésőbbi készre jelentés | {leiras}")
            continue
        d = hatarido_munkanap(kez, n) if mod == "munkanap" else hatarido_naptari(kez, n)
        print(f"{eid}  {d} {NAP[d.weekday()]:10s} | {mod:11s} | kézhezvétel {kez} {NAP[kez.weekday()]} | {leiras}")
    print()
    print("ellenőrzés — a 2026-08-08 szombat munkanap:", munkanap(date(2026, 8, 8)))
    print("ellenőrzés — a 2026-08-21 péntek NEM munkanap:", not munkanap(date(2026, 8, 21)))
    print("ellenőrzés — a 2026-10-23 péntek NEM munkanap:", not munkanap(date(2026, 10, 23)))
