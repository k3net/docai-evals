#!/usr/bin/env python3
"""A runbook §10 eredménylapja — minden lefuttatott karral, kivétel nélkül.

A §5 kikötése: „nem választunk utólag végpontot, nem hagyunk el kart a végső
táblázatból, és nem összevonunk hőmérsékleteket, ha a részletek nem tetszenek. Minden
lefuttatott kar bekerül." Ez az eszköz ezért NEM szűr: amit a lemezen talál, azt
kiírja, és ami hiányzik, azt hiányzóként jelöli — nem hagyja ki csendben.

A lap oszlopai a runbook §10 vázából:

    kar | maszk | Han-kockázat t=0,6 / 0,8 / 1,0 [95 % bootstrap CI]
        | csapda 150×3 [Wilson CI] | kínai próba [CI]
        | KIE F1 | contract F1 | latencia

⭐ A Han-kockázat oszlopa a 2026-09-18-i döntés szerint a POZÍCIÓNKÉNTI E[Han] becslés,
válaszonkénti bootstrap CI-vel — nem a megfigyelt eseményszám. Az „exact nulla" és a
„nem láttunk eseményt" két különböző állítás, és a lap megkülönbözteti őket.

Használat:
    python3 eredmenylap.py --gyoker <kísérlet-könyvtár> --karok K0 S05 A200 …
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from statisztika import wilson
from csapda_riport import atment, REGI_TESZTEK

HIANY = '—'


def olvas_json(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def kie_f1(p):
    """A KIE-futtató összegző sorából: `Overall:  F1=1.000  P=… R=…`"""
    try:
        szoveg = Path(p).read_text(errors='replace')
    except Exception:
        return None
    m = re.search(r'Overall:\s+F1=([\d.]+)\s+P=([\d.]+)\s+R=([\d.]+)', szoveg)
    lat = re.search(r'Latencia avg:\s+(\d+) ms', szoveg)
    if not m:
        return None
    return {'f1': float(m[1]), 'p': float(m[2]), 'r': float(m[3]),
            'latencia_ms': int(lat[1]) if lat else None}


def contract_f1(p):
    """A contract-futtató összegző sorából: `== <cimke>: 30 doksi, acc=… F1=…`"""
    try:
        szoveg = Path(p).read_text(errors='replace')
    except Exception:
        return None
    m = re.search(r'==\s+\S+:\s+(\d+) doksi, acc=([\d.]+) P=([\d.]+) R=([\d.]+) '
                  r'F1=([\d.]+)', szoveg)
    lat = re.search(r'lat átl ([\d.]+)s', szoveg)
    if not m:
        return None
    return {'doksi': int(m[1]), 'acc': float(m[2]), 'f1': float(m[5]),
            'latencia_s': float(lat[1]) if lat else None}


def han_sor(kock, kar, hom):
    """A `han_kockazat.py --json` kimenetéből a VÁLASZ-szegmens értéke egy
    hőmérsékletre. A kar-könyvtárak `<KAR>-t<hőm>` alakúak, és mindegyikben a
    `pp1.5 t<hőm>` beállítás a TÉNYLEGESEN futtatott profil."""
    kulcs = f'{kar}-t{hom}'
    if not kock or kulcs not in kock:
        return None
    b = kock[kulcs]['beallitasok']
    # a ténylegesen futtatott cella neve a SCEN listából
    nev = {'0.6': 'A pp1.5 t0.6 (prod)', '0.8': 'pp1.5 t0.8',
           '1.0': 'K pp1.5 t1.0'}[hom]
    if nev not in b:
        return None
    d = b[nev]
    return {'per_M': d['valasz_per_M'], 'ci': d.get('bootstrap95'),
            'poziciok': kock[kulcs]['poziciok'],
            'valaszok': kock[kulcs]['valaszok'],
            'megfigyelt': kock[kulcs].get('poisson', {}).get('válasz', {})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--gyoker', type=Path, required=True)
    ap.add_argument('--karok', nargs='+', required=True)
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()
    G = a.gyoker

    lap = {}
    for kar in a.karok:
        meta = olvas_json(G / 'karok' / kar / 'KAR.json') or {}
        csapda = olvas_json(G / 'magyar-kie-eval' / 'reports' / f'csapda-{kar}.json')
        kinai = olvas_json(G / 'eredmenyek' / f'kinai-{kar}.json')
        kock = olvas_json(G / 'eredmenyek' / f'kockazat-{kar}.json')
        s = {'forma': meta.get('forma', 'kontroll'),
             'maszk': meta.get('maszk', '—'),
             'param': meta.get('skala') if meta.get('skala') is not None
                      else meta.get('alpha'),
             'han': {t: han_sor(kock, kar, t) for t in ('0.6', '0.8', '1.0')},
             'kie': kie_f1(G / 'eredmenyek' / f'kie-{kar}.log'),
             'contract': contract_f1(G / 'eredmenyek' / f'contract-{kar}.log')}
        if csapda:
            e = {x['id']: x for x in csapda['eredmenyek']}
            regi = [i for i in e if e[i]['teszt'] in REGI_TESZTEK]
            uj = [i for i in e if e[i]['teszt'] not in REGI_TESZTEK]
            def blk(ids):
                k = sum(1 for i in ids if atment(e[i]))
                p, lo, hi = wilson(k, len(ids)) if ids else (0, 0, 1)
                return {'atment': k, 'ossz': len(ids), 'arany': p, 'ci': [lo, hi]}
            s['csapda'] = {'mind': blk(list(e)), 'regi': blk(regi), 'uj': blk(uj),
                           'kesz': csapda.get('kesz', len(e)),
                           'parallel': csapda['args'].get('parallel')}
        if kinai:
            o = kinai.get('osszegzes')
            if o:
                s['kinai'] = {'arany': o['pontszam']['arany'],
                              'ci': o['pontszam']['wilson95'],
                              'han_nelkul': o['han_nelkul']['arany']}
        lap[kar] = s

    def h(x, jel='%'):
        return HIANY if x is None else f'{100*x:.1f}{jel}'

    print('=== EREDMÉNYLAP (runbook §10) ===\n')
    print('Han-kockázat: pozíciónkénti E[Han], VÁLASZ-szegmens, /M, '
          '[95 % válaszonkénti bootstrap CI]\n')
    fej = (f'{"kar":<7} {"forma":<8} {"maszk":<11} {"par":>5} '
           f'{"Han t=0,6":>22} {"Han t=0,8":>22} {"Han t=1,0":>22} '
           f'{"csapda 150":>22} {"kínai":>18} {"KIE":>7} {"contract":>9}')
    print(fej)
    print('-' * len(fej))
    for kar, s in lap.items():
        def hancell(t):
            d = s['han'][t]
            if not d:
                return f'{HIANY:>22}'
            ci = d['ci']
            if ci and ci[1] == 0 and d['per_M'] == 0:
                return f'{"0,00 ⭐exact":>22}'
            c = f'[{ci[0]:.1f};{ci[1]:.1f}]' if ci else ''
            return f'{d["per_M"]:>8.2f} {c:>13}'
        cs = s.get('csapda')
        cscell = (f'{cs["mind"]["atment"]}/{cs["mind"]["ossz"]} '
                  f'{100*cs["mind"]["arany"]:.1f}% '
                  f'[{100*cs["mind"]["ci"][0]:.0f}-{100*cs["mind"]["ci"][1]:.0f}]'
                  if cs else HIANY)
        ki = s.get('kinai')
        kicell = (f'{100*ki["arany"]:.1f}% '
                  f'[{100*ki["ci"][0]:.0f}-{100*ki["ci"][1]:.0f}]' if ki else HIANY)
        par = s['param']
        print(f'{kar:<7} {s["forma"]:<8} {s["maszk"]:<11} '
              f'{(f"{par:g}" if par is not None else "—"):>5} '
              f'{hancell("0.6")} {hancell("0.8")} {hancell("1.0")} '
              f'{cscell:>22} {kicell:>18} '
              f'{(f"{s["kie"]["f1"]:.3f}" if s["kie"] else HIANY):>7} '
              f'{(f"{s["contract"]["f1"]:.3f}" if s["contract"] else HIANY):>9}')

    print('\n— RÉSZLETEK —')
    for kar, s in lap.items():
        cs = s.get('csapda')
        if not cs:
            print(f'{kar}: csapda HIÁNYZIK')
            continue
        print(f'{kar}: csapda régi 50 → {cs["regi"]["atment"]}/{cs["regi"]["ossz"]} '
              f'({100*cs["regi"]["arany"]:.1f} %) · új 100 → '
              f'{cs["uj"]["atment"]}/{cs["uj"]["ossz"]} '
              f'({100*cs["uj"]["arany"]:.1f} %) · párhuzam={cs["parallel"]}'
              + (f' · kínai Han nélkül {100*s["kinai"]["han_nelkul"]:.1f} %'
                 if s.get('kinai') else ''))
        for t in ('0.6', '0.8', '1.0'):
            d = s['han'][t]
            if d:
                mf = d['megfigyelt']
                print(f'    t={t}: {d["per_M"]:.2f}/M, {d["valaszok"]} válasz / '
                      f'{d["poziciok"]} pozíció'
                      + (f' · megfigyelt {mf.get("esemeny")} esemény, '
                         f'Poisson felső korlát < {mf.get("felso_korlat_per_M", 0):.0f}/M'
                         if mf else ''))

    hianyzo = [k for k, s in lap.items()
               if not s.get('csapda') or not s.get('kinai')
               or any(s['han'][t] is None for t in ('0.6', '0.8', '1.0'))]
    if hianyzo:
        print(f'\n⚠️ HIÁNYOS kar(ok): {", ".join(hianyzo)} — a §5 szerint ezek is '
              f'bekerülnek a végső táblázatba, hiányként megjelölve.')

    if a.out:
        a.out.write_text(json.dumps(lap, ensure_ascii=False, indent=1))
        print(f'\nkiírva: {a.out}')


if __name__ == '__main__':
    main()
