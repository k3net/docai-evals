#!/usr/bin/env python3
"""A csapda-korpusz elsődleges KÖLTSÉG-végpontja, karonként és karok között.

### Miért item-szintű pass-rate, és nem a pontszám

A round5 a 100 pontos, súlyozott pontszámot használta. Az arra épített „nem romlott”
állítás viszont nem tesztelhető: a súlyozott, részpontos skálán nincs értelmes
párosított próba, és a CI sem számolható zárt alakban. A runbook §5 ezért arányokat ír
elő — tehát kell egy BINÁRIS itemszintű kimenet.

    egy item ÁTMEGY, ha MINDEN ground-truth mezője pontosan stimmel (arány = 1,0).

A részpont nem tűnik el: a súlyozott pontszám másodlagos végpontként ott marad, és a
RÉGI 50 itemre külön is jelentjük — enélkül a round5-tel való összevetés (Kapu F0)
nem lenne elvégezhető.

### Amit külön jelentünk, és miért kötelező

A bővítés szándékosan NEHEZEBB, mint az eredeti 50 item: valódi bukásokból épült. A
pass-rate ezért ESNI FOG, és ez nem regresszió. A régi és az új blokk ezért mindig
külön is szerepel, a kar-összevetés pedig mindig PÁROSÍTOTT, ugyanazokon az itemeken.

Használat:
    python3 csapda_riport.py reports/csapda-K0.json                    # egy kar
    python3 csapda_riport.py reports/csapda-K0.json reports/csapda-S05.json  # összevetés
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statisztika import wilson, mcnemar, parositott_kulonbseg, holm

REGI_TESZTEK = {f'T{i}' for i in range(1, 11)}

# ⭐ 2026-09-18 döntés (a runbook §5 „−2 pont a 150 itemes csapda-pontszámon"
# egyértelműsítése): a margó SZÓ SZERINT −2 pont a 150-es skálán, azaz −2/150 =
# −1,333 százalékpont, nem −2 százalékpont. Ez a szigorúbb olvasat.
NI_MARGO = -2 / 150


def atment(e):
    """Bináris kimenet: minden GT-mező stimmel. A bírói mezők nem számítanak (azokat
    az exact réteg nem pontozza), a JSON-hiba viszont bukás."""
    p = e['pont']
    if p.get('json_hiba') or not p.get('reszletek'):
        return False
    return all(r['arany'] >= 1.0 - 1e-9 for r in p['reszletek'].values())


def betolt(ut):
    d = json.loads(Path(ut).read_text())
    return d['cimke'], {e['id']: e for e in d['eredmenyek']}


def futasonkenti_ingadozas(ered, items_ut):
    """⛔ „Egy futásból nincs regresszió" (runbook §4) — de mekkora az ingadozás?

    A harness a HÁROM futás közül a többségi kimenetet pontozza, és `instabil`-nak
    jelöli az itemet, ha a nyers szövegek sha256-ja eltér. Ez azonban túlérzékeny:
    egy záró szóköz is eltérést ad, miközben a pontszám ugyanaz. A MÉRÉS
    szempontjából az a kérdés, hogy a PASS/FAIL ingadozik-e futásról futásra —
    mert a végpont azon áll.

    Ez a függvény ezért minden futást KÜLÖN pontoz, és megmondja, hány itemnél
    fordul elő, hogy az egyik futás átmegy, a másik nem. Ez a mérőműszer saját
    zaja, és a jegyzőkönyvbe akkor is bekerül, ha nem érdekes.
    """
    sys.path.insert(0, str(Path(items_ut).parent.parent / 'src'))
    try:
        from pontozo import pontoz_item
    except Exception:
        return None
    defs = {}
    for sor in Path(items_ut).read_text().splitlines():
        if sor.strip():
            it = json.loads(sor)
            defs[it['id']] = it
    szoveg_ing = pont_ing = passz_ing = vizsgalt = 0
    for azon, e in ered.items():
        it = defs.get(azon)
        if not it:
            continue
        jok = [f for f in e['futasok'] if 'hiba' not in f]
        if len(jok) < 2:
            continue
        vizsgalt += 1
        pontok, passzok = [], []
        for f in jok:
            pr = pontoz_item(it, f.get('pred'))
            pontok.append(round(pr['pont'], 6))
            passzok.append(bool(pr.get('reszletek')) and not pr.get('json_hiba')
                           and all(r['arany'] >= 1.0 - 1e-9
                                   for r in pr['reszletek'].values()))
        szoveg_ing += len({f['sha'] for f in jok}) > 1
        pont_ing += len(set(pontok)) > 1
        passz_ing += len(set(passzok)) > 1
    if vizsgalt == 0:
        # Soros mérés, ismétlés nélkül: nincs mit összevetni. A determinizmust a
        # `determinizmus_ellenoriz.py` igazolja a kontrollon, nem ez a függvény.
        return None
    return {'vizsgalt': vizsgalt, 'szoveg_ingadozas': szoveg_ing,
            'pont_ingadozas': pont_ing, 'pass_ingadozas': passz_ing}


def blokk(nev, ids, ered):
    k = sum(1 for i in ids if atment(ered[i]))
    n = len(ids)
    p, lo, hi = wilson(k, n)
    pont = sum(ered[i]['pont']['pont'] for i in ids)
    maxp = sum(ered[i]['pont']['max'] for i in ids)
    print(f'  {nev:<16} {k:>3}/{n:<3} = {100*p:>5.1f} % '
          f'[{100*lo:>5.1f}–{100*hi:>5.1f}]   pont {pont:>7.2f}/{maxp}')
    return {'nev': nev, 'atment': k, 'ossz': n, 'arany': p, 'wilson95': [lo, hi],
            'pont': round(pont, 4), 'max_pont': maxp}


def egy_kar(ut):
    cimke, ered = betolt(ut)
    regi = [i for i in ered if ered[i]['teszt'] in REGI_TESZTEK]
    uj = [i for i in ered if ered[i]['teszt'] not in REGI_TESZTEK]
    print(f'\n=== {cimke} ===')
    osszes = blokk('MIND', list(ered), ered)
    r = blokk('régi 50', regi, ered) if regi else None
    u = blokk('új 100', uj, ered) if uj else None
    print('  — hibaosztályonként —')
    oszt = {}
    for t in sorted({ered[i]['teszt'] for i in uj}):
        ids = [i for i in uj if ered[i]['teszt'] == t]
        oszt[t] = blokk(f'    {t}', ids, ered)
    instabil = sum(1 for e in ered.values() if e.get('instabil'))
    formhiba = sum(1 for e in ered.values() if e.get('formatum_hiba'))
    print(f'  instabil (nem determinisztikus greedy): {instabil}/{len(ered)} · '
          f'formátumsértés: {formhiba}/{len(ered)}')
    return {'cimke': cimke, 'mind': osszes, 'regi': r, 'uj': u, 'osztalyok': oszt,
            'instabil': instabil, 'formatum_hiba': formhiba, 'ered': ered}


def retegzett(alap, kar):
    """⭐ 2026-09-18 döntés az F0-kapu alkalmazásáról.

    A runbook §4.1 kapuja szó szerint azt írná, hogy a K0 által ÁTMENT új itemek
    maradjanak ki (mert „nem reprodukálják a bukást"). Ez viszont padló-hatást okoz:
    ha a kontroll elbukja az itemet, a foltozott kar is elbukja, és a VESZTESÉG — ami
    ennek a körnek az elsődleges kérdése — épp nem látszik. A döntés ezért: minden
    item marad, de a jelentés RÉTEGZETT, és mindkét réteget kimondjuk:

      * `K0 átment`  — ezeken van fejtér LEFELÉ: itt mérhető a folt ÁRA;
      * `K0 bukott`  — ezeken van fejtér FELFELÉ: itt mérhető a JAVULÁS (a round5
                       visszavont javulás-állítása pontosan ilyen rétegből jött).

    A kapu így nem itemeket dob ki, hanem azt köti ki, hogy melyik réteg melyik
    állítást hordozhatja. Egyik réteg sem tűnik el a végső táblázatból (§5).
    """
    kozos = sorted(set(alap['ered']) & set(kar['ered']))
    uj = [i for i in kozos if alap['ered'][i]['teszt'] not in REGI_TESZTEK]
    ki = {}
    for nev, ids in (('K0 átment', [i for i in uj if atment(alap['ered'][i])]),
                     ('K0 bukott', [i for i in uj if not atment(alap['ered'][i])])):
        if not ids:
            continue
        k = sum(1 for i in ids if atment(kar['ered'][i]))
        p, lo, hi = wilson(k, len(ids))
        ki[nev] = {'atment': k, 'ossz': len(ids), 'arany': p, 'wilson95': [lo, hi]}
    return ki


def osszevetes(alap, karok):
    """Minden kar a KONTROLL ellen, párosítva, Holm-korrekcióval."""
    print(f'\n\n=== PÁROSÍTOTT ÖSSZEVETÉS a(z) {alap["cimke"]} kontroll ellen ===')
    print('   (b = a kar átment, a kontroll bukott; c = fordítva)\n')
    p_ertekek, sorok = {}, []
    for k in karok:
        kozos = sorted(set(alap['ered']) & set(k['ered']))
        b = sum(1 for i in kozos if atment(k['ered'][i]) and not atment(alap['ered'][i]))
        c = sum(1 for i in kozos if not atment(k['ered'][i]) and atment(alap['ered'][i]))
        m = mcnemar(b, c)
        d, lo, hi = parositott_kulonbseg(b, c, len(kozos))
        p_ertekek[k['cimke']] = m['p']
        sorok.append((k['cimke'], len(kozos), b, c, m, d, lo, hi))
    kor = holm(p_ertekek)
    print(f'{"kar":<8} {"n":>4} {"b":>4} {"c":>4} {"Δ pass-rate":>14} '
          f'{"95% CI":>18} {"p":>9} {"p(Holm)":>9}  mód')
    ki = []
    for nev, n, b, c, m, d, lo, hi in sorok:
        print(f'{nev:<8} {n:>4} {b:>4} {c:>4} {100*d:>+13.2f} % '
              f'[{100*lo:>+6.2f}; {100*hi:>+6.2f}] {m["p"]:>9.4f} '
              f'{kor[nev]:>9.4f}  {m["mod"]}')
        ki.append({'kar': nev, 'n': n, 'b': b, 'c': c, 'delta': d,
                   'ci95': [lo, hi], 'p': m['p'], 'p_holm': kor[nev],
                   'mod': m['mod']})
    print(f'\n⛔ Nem-inferioritás (margó: −2 pont a 150-es skálán = '
          f'{100*NI_MARGO:+.3f} pp):')
    for s in ki:
        if s['ci95'][0] > NI_MARGO:
            v = 'NEM-INFERIOR (a CI alsó vége a margó fölött)'
        elif s['delta'] < NI_MARGO:
            v = 'ROMLÁS a margón túl'
        else:
            v = 'NEM DÖNTHETŐ EL (a CI átlép a margón — a felbontásunk alatt)'
        print(f'   {s["kar"]:<8} Δ={100*s["delta"]:+.3f} pp, '
              f'CI alsó {100*s["ci95"][0]:+.3f} pp → {v}')
    return ki


def main():
    utak = [x for x in sys.argv[1:] if not x.startswith('--')]
    items_ut = None
    for x in sys.argv[1:]:
        if x.startswith('--items='):
            items_ut = x.split('=', 1)[1]
    if not utak:
        raise SystemExit(__doc__)
    karok = [egy_kar(u) for u in utak]
    if items_ut:
        print('\n=== A MŰSZER SAJÁT ZAJA (futásonkénti ingadozás) ===')
        print(f'{"kar":<8} {"vizsgált":>9} {"szöveg eltér":>13} {"pont eltér":>11} '
              f'{"PASS eltér":>11}')
        for k in karok:
            ing = futasonkenti_ingadozas(k['ered'], items_ut)
            if ing:
                print(f'{k["cimke"]:<8} {ing["vizsgalt"]:>9} '
                      f'{ing["szoveg_ingadozas"]:>13} {ing["pont_ingadozas"]:>11} '
                      f'{ing["pass_ingadozas"]:>11}')
        print('   A „PASS eltér" oszlop a mérés zaja: ennyi itemnél fordul elő, hogy '
              'az\n   egyik greedy futás átmegy, a másik nem. A kar-összevetés '
              'felbontása\n   ennél finomabb nem lehet.')
    if len(karok) > 1:
        osszevetes(karok[0], karok[1:])


if __name__ == '__main__':
    main()
