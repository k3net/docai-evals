#!/usr/bin/env python3
"""A párhuzamosítás igazolása: befolyásolja-e a kötegméret a greedy kimenetet?

### Miért kell ez egyáltalán

A csapda-korpusz `temperature=0`-val fut, tehát elvben determinisztikus, és a
kötegméret nem számíthat. A gyakorlatban **számíthat**: a kötegelt GEMM-ek és a
MoE-útválasztás numerikája kötegméret-függő lehet, és egy hajszálnyi eltérés a
logitokban átbillentheti az argmaxot ott, ahol két jelölt közel van. A round5 azt is
mérte, hogy a greedy kimenet a prompt-gyorstár állapotától is megváltozhatott.

Ha ez itt is így van, akkor a párhuzamosítás nem gyorsítás, hanem **a mérési
körülmény megváltoztatása**, és a round5-tel való összevetés (Kapu F0) érvénytelen.
Ezért a párhuzamosság bevezetése előtt ugyanazokat az itemeket sorosan is le kell
futtatni, és a kimeneteket BÁJTRA össze kell vetni.

### Mit hasonlítunk

Elsődlegesen a válasz `sha256`-ját futásonként, mert az a legszigorúbb. Mellette a
pontozás kimenetét is, mert végső soron az a mérőszám: ha a sha eltér, de a pontszám
és a pass/fail nem, az gyengébb, de még használható eredmény — ezt külön jelentjük,
nem mossuk össze.

Használat:
    python3 parhuzam_ellenoriz.py reports/csapda-K0.json reports/csapda-K0-soros.json
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from csapda_riport import atment


def betolt(ut):
    d = json.loads(Path(ut).read_text())
    return d, {e['id']: e for e in d['eredmenyek']}


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    dp, par = betolt(sys.argv[1])
    ds, sor = betolt(sys.argv[2])
    kozos = sorted(set(par) & set(sor))
    if not kozos:
        raise SystemExit('nincs közös item a két futásban')
    print(f'párhuzamos : {sys.argv[1]}  (parallel='
          f'{dp["args"].get("parallel")})')
    print(f'soros      : {sys.argv[2]}  (parallel='
          f'{ds["args"].get("parallel")})')
    print(f'közös item : {len(kozos)}\n')

    sha_egyez = sha_elter = 0
    pont_elter, passz_elter = [], []
    print(f'{"item":<9} {"sha (1. futás)":<30} {"pont":<18} {"pass"}')
    for i in kozos:
        p, s = par[i], sor[i]
        def sha(e):
            j = [f for f in e['futasok'] if 'hiba' not in f]
            return j[0]['sha'] if j else '—'
        sp, ss = sha(p), sha(s)
        ok = sp == ss
        sha_egyez += ok
        sha_elter += (not ok)
        pp, ps = p['pont']['pont'], s['pont']['pont']
        ap, asz = atment(p), atment(s)
        if abs(pp - ps) > 1e-9:
            pont_elter.append(i)
        if ap != asz:
            passz_elter.append(i)
        print(f'{i:<9} {sp}/{ss} {"✓" if ok else "✗":<10} '
              f'{pp:>6.2f}/{ps:<6.2f} {"✓" if abs(pp-ps)<1e-9 else "✗":<4} '
              f'{"✓" if ap == asz else "✗"}')

    print(f'\nsha egyezés   : {sha_egyez}/{len(kozos)}')
    print(f'pont eltérés  : {len(pont_elter)} {pont_elter}')
    print(f'pass eltérés  : {len(passz_elter)} {passz_elter}')
    print()
    if sha_elter == 0:
        print('✅ VERDIKT: a kötegméret nem befolyásolja a kimenetet — a párhuzamosítás '
              'a mérési körülményt nem változtatja meg, a round5-összevetés érvényes.')
    elif not passz_elter:
        print('⚠️ VERDIKT: a nyers kimenet eltér, de a PASS/FAIL nem. A párhuzamosítás '
              'használható, de a kötegméretet a jegyzőkönyvbe kell írni, és minden kart '
              'AZONOS kötegmérettel kell mérni.')
    else:
        print('⛔ VERDIKT: a kötegméret a PASS/FAIL-t is átbillenti. A párhuzamosítás '
              'ebben a formában NEM használható: vagy soros mérés kell, vagy a '
              'párhuzamosságot a mért változók közé kell venni.')
        sys.exit(1)


if __name__ == '__main__':
    main()
