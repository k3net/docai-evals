#!/usr/bin/env python3
"""F0/2 — céltokenek meghatározása KÉT maszkkal: `nyers` és `finomitott`.

A round5 `smoothie_celtokenek.py` kiterjesztése. Az ottani (nyers) maszk változatlanul
megmarad — a round5 számai csak így vethetők össze az ittenivel —, és mellé kerül a
koreai mintájú finomított maszk, ami a H3 vizsgálati tárgya.

`nyers`      — a `dnotitia/smoothie-qwen` `config.yaml` Unicode-tartományai, változtatás
               nélkül. Minden token, aminek a DEKÓDOLT szövege tartalmaz a tartományokba
               eső, nem-ascii, nem-szám, nem-whitespace karaktert.

`finomitott` — a `ThakiCloud/Qwen3.8-27B-ko-cjk-suppressed` mintája. Három diszjunkció:
                 (a) tartalmaz **kana** karaktert (hiragana/katakana, félszéles is),
                 (b) tartalmaz **csak-egyszerűsített** Han karaktert
                     (ld. `unihan_egyszerusitett.py`),
                 (c) **tiszta Han és legalább 2 Han karakter** — azaz kínai szó, nem glossza.
               Amit szándékosan MEGHAGY: az egykarakteres, megosztott (hagyományos vagy
               közös) Han token, mert a koreai hanja- és a japán kanji-glossza ilyen.

⚠️ A finomított maszk NEM részhalmaza a nyersnek. A kana nincs benne a smoothie
tartományokban, a CJK-írásjelek (U+3000–303F) viszont igen, és azokat a finomított
elengedi. A két maszk tehát két KÜLÖNBÖZŐ beavatkozás, nem „erős" és „gyenge" változata
ugyanannak — a kimenet ezért a szimmetrikus különbséget is kiírja.

Magyar vonatkozás, amiért a H3 egyáltalán kérdés: a magyarban nincs legitim Han-használat,
tehát elvben a nyers maszk ingyen van. Ez azonban FELTEVÉS: ha a finomított magyar oldalon
is mérhetően jobb, akkor van olyan Han-token, ami a magyar folyamatban hasznos. Az
`elhagyott_tokenek` blokk épp ennek a keresésnek az anyaga.

Használat (measurement-host, a kiszolgáló image-ében):
    python3 celtokenek.py --tokenizer <base-snapshot> \
        --egyszerusitett csak-egyszerusitett.json --out celtokenek.json
"""
import argparse, json, unicodedata
from pathlib import Path
from transformers import AutoTokenizer

# A dnotitia/smoothie-qwen config.yaml tartományai, változtatás nélkül.
UNICODE_TARGETS = [
    ('CJK Unified Ideographs', 0x4E00, 0x9FFF),
    ('CJK Unified Ideographs Extension A', 0x3400, 0x4DBF),
    ('CJK Unified Ideographs Extension B', 0x20000, 0x2A6DF),
    ('CJK Compatibility Ideographs', 0xF900, 0xFAFF),
    ('CJK Radicals Supplement', 0x2E80, 0x2EFF),
    ('Kangxi Radicals', 0x2F00, 0x2FDF),
    ('Ideographic Description Characters', 0x2FF0, 0x2FFF),
    ('CJK Symbols and Punctuation', 0x3000, 0x303F),
    ('CJK Strokes', 0x31C0, 0x31EF),
    ('Enclosed CJK Letters and Months', 0x3200, 0x32FF),
    ('CJK Compatibility', 0x3300, 0x33FF),
]
KANA = [('Hiragana', 0x3040, 0x309F), ('Katakana', 0x30A0, 0x30FF),
        ('Katakana Phonetic Extensions', 0x31F0, 0x31FF),
        ('Halfwidth Katakana', 0xFF66, 0xFF9D)]
BROKEN = '�'


def is_target_char(ch):
    """Az eredeti `identify.py:is_target_char` logikája: az ascii, a szám és a
    whitespace sosem cél, még ha tartományba esne is."""
    if not ch or ch.isspace() or ch.isdigit() or ch.isascii():
        return False
    cp = ord(ch)
    return any(lo <= cp <= hi for _, lo, hi in UNICODE_TARGETS)


def is_kana(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for _, lo, hi in KANA)


def is_han(ch):
    """Han ideogram — a Unicode NÉV alapján, nem tartománnyal. Így a gyökök, a
    CJK-írásjelek és a körülzárt alakok nem számítanak Han-nak."""
    return unicodedata.name(ch, '').startswith(
        ('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tokenizer', required=True)
    ap.add_argument('--egyszerusitett', type=Path, required=True,
                    help='unihan_egyszerusitett.py kimenete')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--vocab-rows', type=int, default=None,
                    help='a lm_head sorainak száma (padding miatt > vocab)')
    a = ap.parse_args()

    egysz_meta = json.loads(a.egyszerusitett.read_text())
    EGYSZ = set(egysz_meta['csak_egyszerusitett_cp'])
    print(f'csak-egyszerűsített karakter: {len(EGYSZ)} '
          f'(Unihan {egysz_meta["unicode_verzio"]})')

    tok = AutoTokenizer.from_pretrained(a.tokenizer, trust_remote_code=True)
    ids = sorted(tok.get_vocab().values())
    # ⚠️ Egyenkénti `decode`, NEM `convert_tokens_to_string`: a Qwen bájt-szintű BPE-t
    # használ, és a többbájtos sorozatok töredékei önálló tokenek. A `decode` a csonka
    # sorozatra U+FFFD-t ad, a `convert_tokens_to_string` tetszőleges bájtsorozatot.
    texts = {}
    for st in range(0, len(ids), 4096):
        chunk = ids[st:st + 4096]
        for i, t in zip(chunk, tok.batch_decode([[i] for i in chunk])):
            texts[i] = t

    nyers, finom, broken = [], [], []
    per_range = {n: 0 for n, _, _ in UNICODE_TARGETS}
    pure = mixed = 0
    finom_ok = {'kana': 0, 'csak_egyszerusitett': 0, 'tobbkarakteres_han': 0}

    for i, txt in texts.items():
        if BROKEN in txt:
            broken.append(i)
            continue
        latszo = [c for c in txt if not c.isspace()]

        # --- nyers maszk (round5-tel bitre azonos szabály) ---
        hits = [c for c in txt if is_target_char(c)]
        if hits:
            nyers.append(i)
            if latszo and len(hits) == len(latszo):
                pure += 1
            else:
                mixed += 1
            for c in hits:
                cp = ord(c)
                for n, lo, hi in UNICODE_TARGETS:
                    if lo <= cp <= hi:
                        per_range[n] += 1
                        break

        # --- finomított maszk ---
        han = [c for c in latszo if is_han(c)]
        okok = []
        if any(is_kana(c) for c in latszo):
            okok.append('kana')
        if any(ord(c) in EGYSZ for c in han):
            okok.append('csak_egyszerusitett')
        if han and len(han) == len(latszo) and len(han) >= 2:
            okok.append('tobbkarakteres_han')
        if okok:
            finom.append(i)
            for o in okok:
                finom_ok[o] += 1

    ny, fi = set(nyers), set(finom)
    csak_nyers = sorted(ny - fi)     # a finomított MEGHAGYJA — a H3 vizsgálati tárgya
    csak_finom = sorted(fi - ny)     # döntően kana

    print(f'\nvocab (tokenizer)      : {len(ids)}')
    print(f'lm_head sorok          : {a.vocab_rows or "?"}')
    print(f'törött (U+FFFD) token  : {len(broken)} — egyik maszk sem skálázza')
    print(f'\nNYERS maszk            : {len(nyers)}  ({100*len(nyers)/len(ids):.2f} %)')
    print(f'  tisztán CJK          : {pure}')
    print(f'  vegyes (latin is)    : {mixed}')
    print(f'FINOMÍTOTT maszk       : {len(finom)}  ({100*len(finom)/len(ids):.2f} %)')
    for k, v in finom_ok.items():
        print(f'  {k:<22} {v}')
    print(f'\ncsak a NYERSBEN        : {len(csak_nyers)}  ← ezeket a finomított meghagyja')
    print(f'csak a FINOMÍTOTTBAN   : {len(csak_finom)}  ← döntően kana')
    print('\nkarakter-találatok tartományonként (nyers):')
    for n, c in sorted(per_range.items(), key=lambda x: -x[1]):
        if c:
            print(f'  {n:<40} {c}')
    print('\npélda: csak a nyersben (a finomított meghagyja):')
    for i in csak_nyers[:14]:
        print(f'  {i:<8} {texts[i]!r}')
    print('példa: csak a finomítottban:')
    for i in csak_finom[:8]:
        print(f'  {i:<8} {texts[i]!r}')

    a.out.write_text(json.dumps({
        'maszkok': {'nyers': nyers, 'finomitott': finom},
        'broken_tokens': broken,
        'elhagyott_tokenek': {
            'csak_nyers': csak_nyers,
            'csak_nyers_szoveg': {str(i): texts[i] for i in csak_nyers},
            'csak_finomitott': csak_finom,
        },
        'stats': {'vocab': len(ids), 'nyers': len(nyers), 'finomitott': len(finom),
                  'pure': pure, 'mixed': mixed, 'broken': len(broken),
                  'csak_nyers': len(csak_nyers), 'csak_finomitott': len(csak_finom),
                  'finomitott_okok': finom_ok},
        'unicode_targets': [[n, lo, hi] for n, lo, hi in UNICODE_TARGETS],
        'kana_ranges': [[n, lo, hi] for n, lo, hi in KANA],
        'egyszerusitett_forras': {k: egysz_meta[k]
                                  for k in ('unicode_verzio', 'forras_sha256', 'definicio')},
    }, ensure_ascii=False), encoding='utf-8')
    print(f'\nkiírva: {a.out}')


if __name__ == '__main__':
    main()
