#!/usr/bin/env python3
"""F0/3 kapu — egy kar snapshotjának igazolása a kiindulóhoz képest.

A runbook követelménye: minden karnál ELLENŐRIZVE, hogy a nem célzott súlyfájlok
sha256-a a kiindulóval azonos. Ez nem formalitás: ha a kvantálási állapot bárhol
elmozdul, a mérés elveszíti az ok-okozati erejét — nem a foltot mérnénk, hanem a
foltot ÉS egy újrakvantálást.

Három szint, egyre szigorúbb:

  1. **Fájlszint.** A karban minden fájlnak SZIMLINKNEK kell lennie a kiinduló
     snapshot ugyanazon fájljára, kivéve a foltozott shardot és a `KAR.json`-t.
     A szimlink azonos inode-ra mutat, tehát a sha256 azonossága triviális — de
     ki is számoljuk, mert az „ez triviális” mondat pont ott szokott hibázni, ahol
     számít.
  2. **Tenzorszint a foltozott shardban.** A `lm_head.weight` KIVÉTELÉVEL minden
     tenzornak bitre azonosnak kell lennie. Az `outside.safetensors` a vizuális
     tornyot és a beágyazási mátrixot is tartalmazza — ezek együtt íródnak újra,
     tehát külön kell igazolni, hogy nem változtak.
  3. **Sorszint a `lm_head`-ben.** Pontosan a célzott sorok változhattak, és pontosan
     azok is változtak. Egy nem célzott sor elmozdulása leállás; egy célzott sor
     változatlansága szintén (az azt jelentené, hogy a maszk nem érvényesült).

Használat:
    python3 ellenoriz_kar.py --alap <snapshot> --kar <karkönyvtár> \
        --celtokenek celtokenek.json
"""
import argparse, hashlib, json, os, sys
from pathlib import Path
import torch
from safetensors.torch import load_file

KEY = 'lm_head.weight'
hibak, rendben = [], []


def allit(nev, felt, reszlet=''):
    (rendben if felt else hibak).append(f'{nev}{(" — " + reszlet) if reszlet else ""}')


def sha256(p, blokk=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while (d := f.read(blokk)):
            h.update(d)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--alap', type=Path, required=True)
    ap.add_argument('--kar', type=Path, required=True)
    ap.add_argument('--celtokenek', type=Path, required=True)
    ap.add_argument('--gyors', action='store_true',
                    help='a szimlinkek sha256-ját nem számolja újra (inode-azonosság elég)')
    a = ap.parse_args()

    meta = json.loads((a.kar / 'KAR.json').read_text())
    shard = meta['ujrairt_shard']
    print(f'kar    : {meta["kar"]} ({meta["forma"]}, {meta["maszk"]} maszk, '
          f'{meta["celzott_sor"]} sor)')
    print(f'alap   : {a.alap}')
    print(f'shard  : {shard}\n')

    # ---------- 1. fájlszint ----------
    alap_fajlok = {f for f in os.listdir(a.alap)}
    kar_fajlok = {f for f in os.listdir(a.kar)} - {'KAR.json'}
    allit('a kar ugyanazokat a fájlokat tartalmazza', alap_fajlok == kar_fajlok,
          f'többlet: {sorted(kar_fajlok - alap_fajlok)}, '
          f'hiány: {sorted(alap_fajlok - kar_fajlok)}')
    for f in sorted(alap_fajlok & kar_fajlok):
        kp, ap_ = a.kar / f, a.alap / f
        if f == shard:
            allit(f'{f}: NEM szimlink (ez a foltozott shard)', not kp.is_symlink())
            allit(f'{f}: sha256 ELTÉR a kiindulótól', sha256(kp) != sha256(ap_),
                  'a foltozott shard azonos a kiindulóval — a folt nem érvényesült')
            continue
        allit(f'{f}: szimlink', kp.is_symlink())
        allit(f'{f}: ugyanarra a fájlra mutat',
              os.path.realpath(kp) == os.path.realpath(ap_),
              f'{os.path.realpath(kp)} ≠ {os.path.realpath(ap_)}')
        if not a.gyors and kp.is_file():
            allit(f'{f}: sha256 azonos', sha256(kp) == sha256(ap_))

    # ---------- 2. tenzorszint ----------
    print('a foltozott shard beolvasása…', flush=True)
    alap_t = load_file(str(a.alap / shard))
    kar_t = load_file(str(a.kar / shard))
    allit('a shard tenzorkészlete azonos', set(alap_t) == set(kar_t))
    valtozott = []
    for k in sorted(set(alap_t) & set(kar_t)):
        azonos = torch.equal(alap_t[k], kar_t[k])
        if k == KEY:
            allit(f'{k}: MEGVÁLTOZOTT (ez a cél)', not azonos)
        else:
            allit(f'{k}: bitre azonos', azonos)
            if not azonos:
                valtozott.append(k)
    if valtozott:
        print(f'  ⛔ megváltozott, pedig nem lett volna szabad: {valtozott[:5]}')

    # ---------- 3. sorszint ----------
    targets = json.loads(a.celtokenek.read_text())['maszkok'][meta['maszk']]
    cel = torch.zeros(alap_t[KEY].shape[0], dtype=torch.bool)
    cel[torch.tensor(targets, dtype=torch.long)] = True
    elteres = (alap_t[KEY] != kar_t[KEY]).any(dim=1)
    nem_celzott_valtozott = int((elteres & ~cel).sum())
    celzott_valtozatlan = int((~elteres & cel).sum())
    allit('nem célzott sor NEM változott', nem_celzott_valtozott == 0,
          f'{nem_celzott_valtozott} sor')
    allit('minden célzott sor megváltozott', celzott_valtozatlan == 0,
          f'{celzott_valtozatlan} sor változatlan')
    print(f'  célzott sor: {int(cel.sum())} · megváltozott sor: {int(elteres.sum())}')

    print(f'\n✓ {len(rendben)} ellenőrzés rendben')
    if hibak:
        print(f'\n⛔ {len(hibak)} HIBA:')
        for h in hibak:
            print(f'  · {h}')
        sys.exit(1)
    print('⛔ hiba: nincs')


if __name__ == '__main__':
    main()
