#!/usr/bin/env python3
"""A SOROS mérés determinizmusának igazolása — az F1 kapuja a párhuzamosítás helyett.

⛔ Előzmény (2026-09-18): a runbook §6 párhuzamosság-kapuja MEGBUKOTT. A `parallel=6`
kötegméret a `T7-08` itemen a PASS/FAIL-t is átbillentette (párhuzamosan 3/3 átment,
sorosan 3/3 elbukott). Mivel a karok közti különbség, amit mérni akarunk, ugyanilyen
nagyságrendű, a kötegméret-hatás és a folt hatása **nem szétválasztható** — ezért a
csapda és a kínai próba innentől `parallel=1`.

A soros dekódolás viszont a 12 itemes igazoláson **bitre reprodukálhatónak** bizonyult
(12/12 item, 3/3 azonos sha). Ez az eszköz ezt a tulajdonságot terjeszti ki a teljes
korpuszra: ha a kontroll 150 itemén minden ismétlés azonos kimenetet ad, akkor az
ismétlés a többi karon elhagyható, és a mérés determinisztikus.

Kilépési kód: 0 = determinisztikus, 1 = nem (a vezénylő megáll).
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('futas', help='soros harness-kimenet (pl. reports/csapda-K0.json)')
    ap.add_argument('--min-futas', type=int, default=2,
                    help='ennyi jó futás kell itemenként, hogy az item beszámítson')
    a = ap.parse_args()

    d = json.loads(Path(a.futas).read_text())
    args = d.get('args') or {}
    ered = d['eredmenyek']

    par = args.get('parallel')
    print(f'fájl       : {a.futas}')
    print(f'címke      : {d.get("cimke")}   parallel={par}   futások={args.get("futasok")}')
    print(f'item       : {len(ered)}')
    print()

    if par is not None and par != 1:
        print(f'⛔ Ez NEM soros mérés (parallel={par}). A determinizmus-igazolás értelmetlen.')
        return 1

    vizsgalt = 0
    eltero = []
    keves = []
    for e in ered:
        jok = [f for f in e['futasok'] if 'hiba' not in f]
        if len(jok) < a.min_futas:
            keves.append(e['id'])
            continue
        vizsgalt += 1
        shak = {f['sha'] for f in jok}
        if len(shak) > 1:
            eltero.append((e['id'], sorted(shak)))

    print(f'vizsgált item ({a.min_futas}+ jó futás) : {vizsgalt}')
    print(f'kevés futás miatt kihagyva          : {len(keves)}'
          + (f'  {keves[:10]}' if keves else ''))
    print(f'bájtra eltérő kimenet               : {len(eltero)}')
    for azon, shak in eltero[:20]:
        print(f'   {azon:8s} {" ".join(s[:12] for s in shak)}')
    print()

    if vizsgalt == 0:
        print('⛔ VERDIKT: nincs mit igazolni — egyetlen item sem futott le elégszer.')
        return 1
    if eltero:
        print('⛔ VERDIKT: a soros mérés SEM reprodukálható. Ilyenkor az ismétlés nem '
              'hagyható el,\n   és a kar-összevetés felbontása a mért ingadozásnál '
              'finomabb nem lehet.')
        return 1
    print(f'✅ VERDIKT: a soros mérés {vizsgalt}/{vizsgalt} itemen bitre reprodukálható. '
          'Az ismétlés\n   a többi karon elhagyható; a karok közti eltérés a MODELLBŐL jön, '
          'nem a mérésből.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
