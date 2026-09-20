#!/usr/bin/env python3
"""Kapu F0 — a runbook §6 két feltételének formális kiértékelése.

    (1) a régi 50 item a kontrollon hozza a korábbi eredményt (átfedő CI)
        — különben a KÖRNYEZET változott, nem a korpusz;
    (2) az új itemek reprodukciós állapota a foltozatlan modellen.

### Az (1) feltétel: miért item-szinten párosítva

Az aggregált pontszám egyezése gyenge bizonyíték: két különböző itemhalmaz is adhat
ugyanannyi pontot. A round5 kontrollfutása ugyanazokon az 50 itemen készült, tehát a
párosítás elvégezhető — és akkor nemcsak azt látjuk, hogy a szám stimmel-e, hanem
azt is, hogy UGYANAZOK az itemek mennek-e át.

### A (2) feltétel: a 2026-09-18-i döntés szerint

A kapu szó szerinti olvasata (a K0 által ÁTMENT új itemek kimaradnak) padló-hatást
okozna, ezért **minden item marad**, és a jelentés rétegzett. Ez az eszköz ezért nem
dob ki itemet, hanem kiírja, melyik réteg mekkora, és kimondja, hogy ennek mi a
következménye a mérhetőségre:

  * ha a `K0 bukott` réteg üres, JAVULÁST nem tudunk mérni — és ezt így kell leírni;
  * ha a `K0 átment` réteg nagy, a VESZTESÉG mérésére van fejtér — ez a kör kérdése.

A futásonkénti ingadozás ugyanitt szerepel, mert az adja a felbontás alsó határát.

Használat:
    python3 kapu_f0.py --uj reports/csapda-K0.json \
        --round5 <round5 kontroll json> --items gt/items-150.jsonl
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statisztika import wilson, mcnemar, parositott_kulonbseg
from csapda_riport import atment, REGI_TESZTEK, futasonkenti_ingadozas


def betolt(p):
    d = json.loads(Path(p).read_text())
    return d.get('cimke', Path(p).stem), {e['id']: e for e in d['eredmenyek']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--uj', required=True, help='az ebben a körben mért K0')
    ap.add_argument('--round5', required=True, help='a round5 kontrollfutása')
    ap.add_argument('--items', required=True)
    a = ap.parse_args()

    uj_c, uj = betolt(a.uj)
    r5_c, r5 = betolt(a.round5)
    kozos = sorted(set(uj) & set(r5))
    csak_uj = sorted(set(uj) - set(r5))

    print('=' * 72)
    print('KAPU F0 / (1) — a kontroll hozza-e a round5 eredményét?')
    print('=' * 72)
    print(f'ez a kör : {uj_c}  ({len(uj)} item)')
    print(f'round5   : {r5_c}  ({len(r5)} item)')
    print(f'közös    : {len(kozos)} item — ezeken párosítva vetjük össze\n')

    ku = sum(1 for i in kozos if atment(uj[i]))
    kr = sum(1 for i in kozos if atment(r5[i]))
    pu, lu, hu = wilson(ku, len(kozos))
    pr, lr, hr = wilson(kr, len(kozos))
    pont_u = sum(uj[i]['pont']['pont'] for i in kozos)
    pont_r = sum(r5[i]['pont']['pont'] for i in kozos)
    maxp = sum(uj[i]['pont']['max'] for i in kozos)
    print(f'{"":<10} {"pass-rate":>28} {"pontszám":>14}')
    print(f'{uj_c:<10} {ku}/{len(kozos)} = {100*pu:.1f} % '
          f'[{100*lu:.1f}–{100*hu:.1f}] {pont_u:>10.2f}/{maxp}')
    print(f'{r5_c:<10} {kr}/{len(kozos)} = {100*pr:.1f} % '
          f'[{100*lr:.1f}–{100*hr:.1f}] {pont_r:>10.2f}/{maxp}')

    atfed = not (hu < lr or hr < lu)
    b = sum(1 for i in kozos if atment(uj[i]) and not atment(r5[i]))
    c = sum(1 for i in kozos if not atment(uj[i]) and atment(r5[i]))
    m = mcnemar(b, c)
    d, dlo, dhi = parositott_kulonbseg(b, c, len(kozos))
    print(f'\npárosított: b={b} (most átment, akkor bukott), '
          f'c={c} (most bukott, akkor átment)')
    print(f'Δ pass-rate = {100*d:+.2f} pp [{100*dlo:+.2f}; {100*dhi:+.2f}], '
          f'McNemar p = {m["p"]:.4f} ({m["mod"]})')
    if b or c:
        print('  eltérő itemek:')
        for i in kozos:
            au, ar = atment(uj[i]), atment(r5[i])
            if au != ar:
                print(f'    {i}: most {"átment" if au else "BUKOTT"}, '
                      f'akkor {"átment" if ar else "BUKOTT"} '
                      f'({uj[i]["pont"]["pont"]:.2f} vs {r5[i]["pont"]["pont"]:.2f} pont)')
    print(f'\n→ (1) VERDIKT: a CI-k {"ÁTFEDNEK" if atfed else "NEM FEDNEK ÁT"}, '
          f'a párosított különbség {"nem szignifikáns" if m["p"] > 0.05 else "SZIGNIFIKÁNS"}'
          f' → a kapu {"TELJESÜL" if atfed and m["p"] > 0.05 else "BUKIK"}')

    print('\n' + '=' * 72)
    print('KAPU F0 / (2) — az új itemek reprodukciós állapota a kontrollon')
    print('=' * 72)
    uj_ids = [i for i in uj if uj[i]['teszt'] not in REGI_TESZTEK]
    at = [i for i in uj_ids if atment(uj[i])]
    bu = [i for i in uj_ids if not atment(uj[i])]
    print(f'új item: {len(uj_ids)}')
    print(f'  K0 ÁTMENT réteg: {len(at):>3} — itt van fejtér LEFELÉ '
          f'(a folt ÁRA mérhető)')
    print(f'  K0 BUKOTT réteg: {len(bu):>3} — itt van fejtér FELFELÉ '
          f'(a JAVULÁS mérhető)')
    if bu:
        print(f'    bukott: {", ".join(bu)}')
    if not bu:
        print('  ⚠️ A bukott réteg ÜRES: ezen a korpuszon JAVULÁST nem tudunk mérni. '
              'Ezt\n     a tanulmányban ki kell mondani — nem az a helyzet, hogy nincs '
              'javulás,\n     hanem az, hogy a műszer nem tudná megmutatni.')

    ing = futasonkenti_ingadozas(uj, a.items)
    if ing:
        print(f'\nA MŰSZER SAJÁT ZAJA ({ing["vizsgalt"]} item, 3 greedy futás):')
        print(f'  nyers szöveg eltér : {ing["szoveg_ingadozas"]}')
        print(f'  pontszám eltér     : {ing["pont_ingadozas"]}')
        print(f'  PASS/FAIL eltér    : {ing["pass_ingadozas"]}  '
              f'← a felbontás alsó határa '
              f'({100*ing["pass_ingadozas"]/max(ing["vizsgalt"],1):.2f} pp)')
        margo = 100 * 2 / 150
        if ing['pass_ingadozas'] / max(ing['vizsgalt'], 1) * 100 >= margo:
            print(f'  ⚠️ A zaj ({100*ing["pass_ingadozas"]/ing["vizsgalt"]:.2f} pp) '
                  f'eléri vagy meghaladja a −{margo:.2f} pp-os nem-inferioritási '
                  f'margót:\n     a margón belüli eltérés NEM megkülönböztethető a '
                  f'műszer zajától.')


if __name__ == '__main__':
    main()
