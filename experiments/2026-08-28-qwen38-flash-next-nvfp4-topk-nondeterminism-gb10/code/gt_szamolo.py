#!/usr/bin/env python3
"""T2 — késedelmi kötbér ground truth. Minden érték SZÁMOLT, egyik sincs beírva.

Forrás: corpus/D2.md 3.1, 5.2, 5.3 pont.
  nettó Vállalkozói Díj = 12 400 000 Ft
  napi kötbér           = a nettó díj 0,5 %-a, minden MEGKEZDETT késedelmes naptári napra
  plafon                = a nettó díj 15 %-a
"""
from decimal import Decimal

NETTO = Decimal("12400000")
NAPI_SZAZALEK = Decimal("0.5")
PLAFON_SZAZALEK = Decimal("15")

def kotber(napok: int) -> dict:
    nyers = NAPI_SZAZALEK * napok                      # % -ban
    plafonos = min(nyers, PLAFON_SZAZALEK)
    osszeg = NETTO * plafonos / Decimal(100)
    assert osszeg == osszeg.to_integral_value(), f"nem egész forint: {osszeg}"
    return {
        "kesedelmes_napok": napok,
        "kotber_szazalek": float(plafonos) if plafonos % 1 else int(plafonos),
        "kotber_osszeg_ft": int(osszeg),
        "alkalmazott_plafon": nyers > PLAFON_SZAZALEK,
    }

ITEM_NAPOK = [8, 12, 30, 40, 55]        # 2 plafon alatt, 1 pont a határon, 2 fölötte

if __name__ == "__main__":
    import json
    print(f"nettó díj: {NETTO:,.0f} Ft · plafon {PLAFON_SZAZALEK} % = "
          f"{NETTO*PLAFON_SZAZALEK/100:,.0f} Ft".replace(",", " "))
    for n in ITEM_NAPOK:
        r = kotber(n)
        print(f"  {n:3d} nap → nyers {NAPI_SZAZALEK*n:5}% → "
              f"{r['kotber_szazalek']:>5}% = {r['kotber_osszeg_ft']:>10,} Ft  "
              f"plafon={r['alkalmazott_plafon']}".replace(",", " "))
    print()
    print(json.dumps([kotber(n) for n in ITEM_NAPOK], ensure_ascii=False, indent=1))
