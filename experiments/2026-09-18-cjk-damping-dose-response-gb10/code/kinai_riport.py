#!/usr/bin/env python3
"""A kínai képesség-próba karonként és karok között — a model card kötelező száma.

A runbook 7. pontja szerint modellt csak akkor publikálunk, ha „a kínai veszteség
SZÁMMAL megadható a model cardban". Ez az eszköz állítja elő azt a számot, és nem
egyet, hanem kettőt:

  `pontszam`   — a helyes válaszok aránya (Wilson 95 % CI).
  `han_nelkul` — hány itemnél nincs a válaszban EGYÁLTALÁN Han karakter.

A kettő mást jelent, és a model cardba mindkettő kell. Ha a pontszám esik, de a
Han-arány nem, a modell rosszabbul tud kínaiul. Ha a Han-arány is esik, a modell
nem tud kínaiul MEGSZÓLALNI — ez a folt közvetlen tünete, és a felhasználó számára
minőségileg más kártétel.

A kontroll-ellenes összevetés párosított (ugyanazok az itemek), McNemar-próbával és
Holm-korrekcióval, a runbook §5 szerint.

Használat:
    python3 kinai_riport.py eredmenyek/kinai-K0.json eredmenyek/kinai-S05.json …
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statisztika import wilson, mcnemar, parositott_kulonbseg, holm


def betolt(ut):
    d = json.loads(Path(ut).read_text())
    return d['cimke'], {e['id']: e for e in d['eredmenyek']}


def egy_kar(ut):
    cimke, ered = betolt(ut)
    n = len(ered)
    k = sum(1 for e in ered.values() if e['helyes'])
    nh = sum(1 for e in ered.values() if not e['han_a_valaszban'])
    p, lo, hi = wilson(k, n)
    ph, hlo, hhi = wilson(nh, n)
    print(f'\n=== {cimke} ===')
    print(f'  pontszám    : {k}/{n} = {100*p:5.1f} % [{100*lo:.1f}–{100*hi:.1f}]')
    print(f'  Han NÉLKÜLI : {nh}/{n} = {100*ph:5.1f} % [{100*hlo:.1f}–{100*hhi:.1f}]')
    kat = {}
    for e in ered.values():
        d = kat.setdefault(e['kategoria'], [0, 0, 0])
        d[0] += e['helyes']; d[1] += 1; d[2] += (not e['han_a_valaszban'])
    print(f'  {"kategória":<12} {"helyes":>8} {"Han nélkül":>12}')
    for k2, v in sorted(kat.items()):
        print(f'  {k2:<12} {v[0]:>4}/{v[1]:<3} {v[2]:>8}/{v[1]:<3}')
    instabil = sum(1 for e in ered.values() if e.get('instabil'))
    print(f'  instabil (greedy mellett): {instabil}/{n}')
    return {'cimke': cimke, 'ered': ered, 'helyes': k, 'ossz': n,
            'arany': p, 'wilson95': [lo, hi], 'han_nelkul': nh,
            'han_nelkul_arany': ph, 'kategoriank': kat, 'instabil': instabil}


def osszevetes(alap, karok):
    print(f'\n\n=== PÁROSÍTOTT ÖSSZEVETÉS a(z) {alap["cimke"]} kontroll ellen ===')
    p_ertekek, sorok = {}, []
    for k in karok:
        kozos = sorted(set(alap['ered']) & set(k['ered']))
        b = sum(1 for i in kozos
                if k['ered'][i]['helyes'] and not alap['ered'][i]['helyes'])
        c = sum(1 for i in kozos
                if not k['ered'][i]['helyes'] and alap['ered'][i]['helyes'])
        m = mcnemar(b, c)
        d, lo, hi = parositott_kulonbseg(b, c, len(kozos))
        # a Han-vesztés külön: hány itemnél TŰNT EL a Han a válaszból
        hb = sum(1 for i in kozos if not k['ered'][i]['han_a_valaszban']
                 and alap['ered'][i]['han_a_valaszban'])
        p_ertekek[k['cimke']] = m['p']
        sorok.append((k['cimke'], len(kozos), b, c, m, d, lo, hi, hb))
    kor = holm(p_ertekek)
    print(f'{"kar":<8} {"n":>4} {"b":>3} {"c":>3} {"Δ pontszám":>13} '
          f'{"95% CI":>18} {"p(Holm)":>9} {"Han eltűnt":>11}')
    ki = []
    for nev, n, b, c, m, d, lo, hi, hb in sorok:
        print(f'{nev:<8} {n:>4} {b:>3} {c:>3} {100*d:>+12.2f} % '
              f'[{100*lo:>+6.2f}; {100*hi:>+6.2f}] {kor[nev]:>9.4f} {hb:>8} db')
        ki.append({'kar': nev, 'b': b, 'c': c, 'delta': d, 'ci95': [lo, hi],
                   'p': m['p'], 'p_holm': kor[nev], 'han_eltunt': hb})
    print('\nA model cardba írandó mondat mintája:')
    for s in ki:
        k = next(x for x in karok if x['cimke'] == s['kar'])
        print(f'   {s["kar"]}: a kínai próbán {100*k["arany"]:.1f} % '
              f'(kontroll: {100*alap["arany"]:.1f} %), '
              f'a válaszok {100*k["han_nelkul_arany"]:.1f} %-ában nincs kínai írásjegy '
              f'(kontroll: {100*alap["han_nelkul_arany"]:.1f} %).')
    return ki


def main():
    utak = sys.argv[1:]
    if not utak:
        raise SystemExit(__doc__)
    karok = [egy_kar(u) for u in utak]
    if len(karok) > 1:
        osszevetes(karok[0], karok[1:])


if __name__ == '__main__':
    main()
