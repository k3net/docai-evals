#!/usr/bin/env python3
"""F0/2 — a „csak-egyszerűsített" Han-karakterek listájának előállítása a Unihanból.

Miért kell. A finomított maszk (H3) a koreai munka
(`ThakiCloud/Qwen3.8-27B-ko-cjk-suppressed`) mintáját követi: az **egykarakteres**
Han-tokeneket meghagyja, mert a koreai hanja-glossza legitim nyelvi elem. A kivétel az
a karakterosztály, ami **kizárólag a szárazföldi kínai írásreformból** származik: ilyen
alak sem japán, sem koreai szövegben nem fordul elő, tehát elnyomása nem vesz el
hanja/kanji-képességet.

A definíció, változtatás nélkül, a Unihan `kTraditionalVariant` mezőjéből:

    egy karakter CSAK-EGYSZERŰSÍTETT, ha van olyan hagyományos változata,
    ami nem önmaga.

⚠️ Ismert, vállalt pontatlanság, amit nem hallgatunk el: a japán *shinjitai* reform
részben ugyanazokat az alakokat vezette be (`国`, `学`, `体`), ezek tehát a japánban is
élő karakterek, mégis erre a listára kerülnek. A hatás iránya ismert: a finomított maszk
így a japánból **többet** vesz el, mint a szigorú definíció szerint kellene — vagyis a
H3 tesztje ezen az oldalon konzervatív. A magyar végpontot ez nem érinti.

A kimenet a csomag része, hogy a mérés a Unihan letöltése nélkül reprodukálható legyen;
a forrásfájl verziója és sha256-ja a kimenetben szerepel.

Használat:
    python3 unihan_egyszerusitett.py --variants Unihan_Variants.txt \
        --out csak-egyszerusitett.json
"""
import argparse, hashlib, json, re, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--variants', type=Path, required=True,
                    help='Unihan_Variants.txt az Unihan.zip-ből')
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()

    nyers = a.variants.read_bytes()
    sha = hashlib.sha256(nyers).hexdigest()
    szoveg = nyers.decode('utf-8')

    unicode_verzio = None
    for sor in szoveg.split('\n', 40)[:40]:
        m = re.match(r'#\s*Unicode Version\s+(\S+)', sor)
        if m:
            unicode_verzio = m.group(1)
            break

    egyszerusitett, hagyomanyos = set(), set()
    for sor in szoveg.splitlines():
        if not sor or sor.startswith('#'):
            continue
        reszek = sor.split('\t')
        if len(reszek) < 3:
            continue
        kod, mezo, ertek = reszek[0], reszek[1], reszek[2]
        if not kod.startswith('U+'):
            continue
        cp = int(kod[2:], 16)
        # A célpontok "U+XXXX<forrás" alakúak is lehetnek — a forrásjelölést levágjuk.
        celok = {int(t[2:].split('<')[0], 16)
                 for t in ertek.split() if t.startswith('U+')}
        if mezo == 'kTraditionalVariant' and celok - {cp}:
            egyszerusitett.add(cp)
        elif mezo == 'kSimplifiedVariant' and celok - {cp}:
            hagyomanyos.add(cp)

    # Aki mindkét halmazban benne van, az egy egyszerűsített↔hagyományos pár mindkét
    # oldalán szerepel (körkörös vagy többes megfeleltetés). Ez nem „csak-egyszerűsített":
    # ha egy alaknak magának is van egyszerűsített változata, akkor ő a hagyományos oldal.
    csak_egyszerusitett = sorted(egyszerusitett - hagyomanyos)
    ketes = sorted(egyszerusitett & hagyomanyos)

    print(f'Unihan_Variants.txt   : {a.variants}')
    print(f'  Unicode verzió      : {unicode_verzio}')
    print(f'  sha256              : {sha}')
    print(f'kTraditionalVariant-os: {len(egyszerusitett)}')
    print(f'kSimplifiedVariant-os : {len(hagyomanyos)}')
    print(f'  mindkettő (kétes)   : {len(ketes)} — kihagyva')
    print(f'CSAK-EGYSZERŰSÍTETT   : {len(csak_egyszerusitett)}')
    print('  minta: ' + ' '.join(chr(c) for c in csak_egyszerusitett[:40]))

    a.out.write_text(json.dumps({
        'forras': 'Unihan_Variants.txt',
        'unicode_verzio': unicode_verzio,
        'forras_sha256': sha,
        'definicio': 'kTraditionalVariant ≠ önmaga ÉS nincs kSimplifiedVariant-ja',
        'csak_egyszerusitett_cp': csak_egyszerusitett,
        'ketes_cp': ketes,
        'stat': {'egyszerusitett': len(egyszerusitett), 'hagyomanyos': len(hagyomanyos),
                 'ketes': len(ketes), 'csak_egyszerusitett': len(csak_egyszerusitett)},
    }, ensure_ascii=False), encoding='utf-8')
    print(f'\nkiírva: {a.out}')


if __name__ == '__main__':
    main()
