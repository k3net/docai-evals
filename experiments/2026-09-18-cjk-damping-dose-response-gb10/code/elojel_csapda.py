#!/usr/bin/env python3
"""Az előjel-csapda mérése VALÓSZÍNŰSÉGBEN, nem logitban — a round5 legvékonyabb pontja.

### A csapda

A `lm_head` sorának `0 < S < 1`-gyel való szorzása a logitot `S`-szeresére veszi. Ha a
logit POZITÍV, ez csökkenti; ha NEGATÍV, akkor **nulla felé tolja, azaz NÖVELI** a token
valószínűségét. A round5 ezt egyetlen billenési ponton mérte meg (nem volt aktív), és a
runbook §9 ezt nevezi meg a legvékonyabb pontnak.

### Miért nem elég a logitokat megszámolni

A karépítés előjel-diagnosztikája azt mondja, hogy a magyar átlagállapotban a célzott
sorok **96 %-ának negatív a logitja**, tehát a szorzás ezeket felfelé tolja. Ez önmagában
**nem jelent kockázatnövekedést**: ez az 55 424 sor jórészt olyan mélyen ül a maximum
alatt, hogy a valószínűségük elhanyagolható marad akkor is, ha megnő. A kérdés nem az,
hogy hány sor logitja nőtt, hanem hogy a **Han-tokenek összvalószínűsége** nőtt-e — és
hogy a felső jelöltek között mi történt.

Ez az eszköz ezért a tényleges mérőszámot számolja:

  * `han_tomeg`  — a célzott tokenek összvalószínűsége a softmax után, hőmérsékletenként;
  * `top20_han`  — hány célzott token van a top-20 jelölt között, és mekkora a tömegük
                   (a round5 műszere ezt látta: 8,314 % → 0,000 %);
  * `nott_e`     — a folt NÖVELTE-e a Han-tömeget az adott állapotban. Ez az előjel-csapda
                   éles kérdése.

Az állapotokat (`h`) a `mu_h_becslo.py` kimenetéből vagy egy rögzített billenési pont
rejtett állapotából kapja. Az F3 fázis több billenési ponton futtatja.

Használat:
    python3 elojel_csapda.py --alap <snapshot> --karok <kar1> <kar2> … \
        --allapotok mu-h-A.json --celtokenek celtokenek.json
"""
import argparse, json
from pathlib import Path
import torch
from safetensors import safe_open


def lm_head(snapshot):
    snapshot = Path(snapshot)
    idx = json.loads((snapshot / 'model.safetensors.index.json').read_text())['weight_map']
    with safe_open(str(snapshot / idx['lm_head.weight']), 'pt') as f:
        return f.get_tensor('lm_head.weight').float()


def elemez(W, h, cel_maszk, hom, top_k=20, top_p=0.95):
    """Han-tömeg egy állapotban, NYERSEN és a TERMELÉSI mintavételezés után.

    ⛔ A kettő nem ugyanaz, és a különbség dönti el, mit jelent az előjel-csapda. A
    prod cron-profil `top_k=20`, `top_p=0,95` — a farkat levágja. A nyers eloszlásban
    megnőtt Han-tömeg tehát csak akkor számít, ha a csonkolás UTÁN is ott van. Ha a
    csonkolt tömeg mindkét karon nulla, a csapda a gyakorlatban nem aktív — de a
    model cardba akkor is bele kell írni, mert aki `top_k` nélkül mintavételez, más
    modellt kap, mint amit mértünk.
    """
    logit = W @ h
    ki = {}
    for t in hom:
        p = torch.softmax(logit / t, dim=0)
        tomeg = float(p[cel_maszk].sum())
        rend = torch.topk(logit, 20).indices
        top_han = int(cel_maszk[rend].sum())
        top_tomeg = float(p[rend][cel_maszk[rend]].sum())
        # --- a tényleges mintavételezési lánc: top_k → top_p → újranormálás ---
        k_ert, k_idx = torch.topk(p, top_k)
        k_ert = k_ert / k_ert.sum()
        halm = torch.cumsum(k_ert, 0)
        tart = int((halm >= top_p).nonzero()[0]) + 1 if float(halm[-1]) >= top_p else top_k
        marad = k_ert[:tart] / k_ert[:tart].sum()
        csonkolt = float(marad[cel_maszk[k_idx[:tart]]].sum())
        ki[f't={t}'] = {'han_tomeg': tomeg, 'top20_han_db': top_han,
                        'top20_han_tomeg': top_tomeg,
                        'han_tomeg_csonkolt': csonkolt, 'megtartott_jelolt': tart}
    ki['logit'] = {'max': float(logit.max()),
                   'cel_atlag': float(logit[cel_maszk].mean()),
                   'cel_max': float(logit[cel_maszk].max()),
                   'cel_negativ_arany': float((logit[cel_maszk] < 0).float().mean())}
    return ki


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--alap', type=Path, required=True)
    ap.add_argument('--karok', type=Path, nargs='+', required=True)
    ap.add_argument('--allapotok', type=Path, nargs='+', required=True,
                    help='mu_h_becslo.py kimenete(i), vagy {"nev":…,"h":[…]} fájlok')
    ap.add_argument('--celtokenek', type=Path, required=True)
    ap.add_argument('--homersekletek', type=float, nargs='+', default=[0.6, 0.8, 1.0])
    ap.add_argument('--out', type=Path)
    a = ap.parse_args()

    ct = json.loads(a.celtokenek.read_text())
    allapotok = []
    for p in a.allapotok:
        d = json.loads(p.read_text())
        vek = d.get('mu_h') or d.get('h')
        allapotok.append((d.get('nev') or p.stem, torch.tensor(vek, dtype=torch.float32)))

    W0 = lm_head(a.alap)
    n = W0.shape[0]
    print(f'lm_head: {tuple(W0.shape)}\n')

    eredmeny = {}
    for karut in [a.alap] + list(a.karok):
        kar = 'K0'
        maszk_nev = 'nyers'
        km = karut / 'KAR.json'
        if km.exists():
            meta = json.loads(km.read_text())
            kar, maszk_nev = meta['kar'], meta['maszk']
        cel = torch.zeros(n, dtype=torch.bool)
        cel[torch.tensor(ct['maszkok'][maszk_nev], dtype=torch.long)] = True
        W = W0 if karut == a.alap else lm_head(karut)
        for nev, h in allapotok:
            r = elemez(W, h, cel, a.homersekletek)
            eredmeny.setdefault(nev, {})[kar] = r
        del W

    for nev in eredmeny:
        print(f'=== állapot: {nev} ===')
        print(f'{"kar":<7} {"max logit":>10} {"cél átlag":>10} {"cél<0":>7} '
              + ' '.join(f'{"nyers/csonkolt t=" + str(t):>22}' for t in a.homersekletek)
              + f' {"top20 Han":>12}')
        alap_ertek = None
        for kar, r in eredmeny[nev].items():
            L = r['logit']
            sor = (f'{kar:<7} {L["max"]:>10.3f} {L["cel_atlag"]:>10.3f} '
                   f'{100*L["cel_negativ_arany"]:>6.1f}%')
            for t in a.homersekletek:
                sor += (f' {100*r[f"t={t}"]["han_tomeg"]:>11.6f}%/'
                        f'{100*r[f"t={t}"]["han_tomeg_csonkolt"]:<9.6f}%')
            r0 = r[f't={a.homersekletek[0]}']
            sor += f' {r0["top20_han_db"]:>4} db / {100*r0["top20_han_tomeg"]:.3f}%'
            print(sor)
            if kar == 'K0':
                alap_ertek = r
        if alap_ertek:
            print('\n  ⚠️ ELŐJEL-CSAPDA — nőtt-e a Han-tömeg a folttól?')
            for kar, r in eredmeny[nev].items():
                if kar == 'K0':
                    continue
                for t in a.homersekletek:
                    for cimke, kulcs in (('nyers    ', 'han_tomeg'),
                                         ('csonkolt ', 'han_tomeg_csonkolt')):
                        e = alap_ertek[f't={t}'][kulcs]
                        u = r[f't={t}'][kulcs]
                        jel = 'NŐTT ⛔' if u > e + 1e-12 else (
                            'csökkent' if u < e - 1e-12 else 'változatlan')
                        arany = f'{u/e:.4g}×' if e > 1e-12 else '—'
                        print(f'    {kar:<7} t={t} {cimke}: {100*e:.6f}% → '
                              f'{100*u:.6f}% ({arany}) {jel}')
        print()

    if a.out:
        a.out.write_text(json.dumps(eredmeny, ensure_ascii=False, indent=1))
        print(f'kiírva: {a.out}')


if __name__ == '__main__':
    main()
