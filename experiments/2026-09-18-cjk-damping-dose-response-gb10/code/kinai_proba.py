#!/usr/bin/env python3
"""F0/5 — kínai képesség-próba: mit veszít a modell azon a nyelven, amit elfojtunk.

Miért kell. A model cardban nem lehet annyit írni, hogy „a kínai romolhat". Számot kell
írni. A round5 EGYSZER SEM mérte meg a célnyelvi költséget — ez a kör pótolja.

### A próba szerkezete és miért ilyen

36 item, hét kategóriában, **zárt értékkészletű** válaszokkal, greedy dekódolással, exact
egyezésre pontozva. Ez nem benchmark-utánzat: nem az a kérdés, hogy a modell milyen jó
kínaiul, hanem hogy a **folt** mennyit vesz el belőle. Ehhez az kell, hogy

  * minden helyes válasz **kínai írásjegyet** igényeljen — különben a próba a folt
    hatását épp nem látná (egy pinjinnel vagy angolul adott válasz „átmenne");
  * a válasz rövid és zárt legyen, hogy a pontozás determinisztikus maradjon;
  * a kategóriák a beavatkozás SZERKEZETÉRE legyenek érzékenyek: a `fanjian`
    (繁→简) kategória például pontosan azt a karakterosztályt kéri, amit a finomított
    maszk céloz (H3), a `chengyu` pedig többkarakteres tiszta Han szót, amit mindkét
    maszk elnyom.

### Két mérőszám, nem egy

`pontszam`  — a helyes válaszok aránya (Wilson 95 % CI-vel).
`han_nelkul` — azoknak az itemeknek az aránya, ahol a VÁLASZBAN egyáltalán nincs Han
               karakter. Ez a folt legközvetlenebb tünete: a modell nem rosszul válaszol
               kínaiul, hanem nem tud kínaiul válaszolni. A kettőt külön jelentjük, mert
               mást jelentenek.

A gondolkodási szakasz (`</think>` előtt) nem számít bele a pontozásba, de a Han-jelenlét
ott is rögzül: ha a gondolkodás kínai marad, a válasz viszont nem, az a parser és a folt
kölcsönhatásáról mond valamit.

Használat:
    python3 kinai_proba.py --url http://127.0.0.1:18355 --model qwen36 \
        --cimke K0 --out eredmenyek/kinai-K0.json
"""
import argparse, json, math, re, sys, threading, time, unicodedata, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# A pontozás előtti normalizálás: a modell hajlamos idézőjelet, írásjelet és
# magyarázó farkat tenni a válaszra. Ezeket levágjuk — a MÉRT dolog a tartalom.
IRASJEL = '「」『』“”‘’"\'（）()【】《》，。、；：！？,.;:!?~…—-_＿﹏ \t\n\r'


def han_e(s):
    return any(unicodedata.name(c, '').startswith(
        ('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-')) for c in s)


def norm(s):
    return s.strip().strip(IRASJEL).strip()


def wilson(k, n, z=1.959963984540054):
    """Wilson-féle 95 %-os CI — a runbook §5 előírása. Nulla és teljes találatnál is
    értelmes, ellentétben a normális közelítéssel."""
    if n == 0:
        return (0.0, 0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    kozep = (p + z * z / (2 * n)) / d
    fel = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0.0, kozep - fel), min(1.0, kozep + fel))


def hivas(ep, model, rendszer, prompt, max_tokens, timeout, ujraprobak=2):
    """⛔ `Connection: close` + valóban eldurranó timeout: a round5-ben mért beragadt
    kapcsolat (200 OK a kiszolgálón, a kliens mégis vár) némán vitte volna el a mérést."""
    payload = {'model': model, 'temperature': 0.0, 'top_p': 1, 'max_tokens': max_tokens,
               'messages': [{'role': 'system', 'content': rendszer},
                            {'role': 'user', 'content': prompt}]}
    utolso = None
    for proba in range(ujraprobak + 1):
        req = urllib.request.Request(ep, data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json',
                                              'Connection': 'close'})
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode()), (time.monotonic() - t0) * 1000
        except Exception as e:
            utolso = e
            print(f'    ⚠️ kérés-hiba ({proba+1}/{ujraprobak+1}): {type(e).__name__}: '
                  f'{str(e)[:120]}', file=sys.stderr, flush=True)
            time.sleep(5)
    raise utolso


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True)
    ap.add_argument('--model', default='qwen36')
    ap.add_argument('--cimke', required=True)
    ap.add_argument('--items', default='items-kinai.jsonl')
    ap.add_argument('--futasok', type=int, default=3,
                    help='itemenkénti ismétlés; greedy mellett is mérjük, mert a '
                         'round5 szabálya: egy futásból nincs regresszió')
    ap.add_argument('--max-tokens', type=int, default=2048)
    ap.add_argument('--timeout', type=float, default=300)
    ap.add_argument('--parallel', type=int, default=1,
                    help='egyszerre ennyi item fut. A csapda-harnesszel AZONOS értéket '
                         'kell adni, hogy a két műszer ugyanolyan kötegelési '
                         'körülmények között mérjen.')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    base = a.url.rstrip('/')
    if not re.search(r'/v\d+$', base):
        base += '/v1'
    ep = base + '/chat/completions'

    items = [json.loads(l) for l in Path(a.items).read_text().splitlines() if l.strip()]
    print(f'[i] {len(items)} item × {a.futasok} futás', file=sys.stderr)

    eredmenyek = []
    lakat = threading.Lock()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)

    def dolgozik(nit):
        n, it = nit
        futasok = []
        for _ in range(a.futasok):
            try:
                body, wall = hivas(ep, a.model, it['rendszer'], it['prompt'],
                                   a.max_tokens, a.timeout)
            except Exception as e:
                futasok.append({'hiba': f'{type(e).__name__}: {str(e)[:200]}'})
                continue
            ch = body['choices'][0]
            nyers = ch['message'].get('content') or ''
            gond = (ch['message'].get('reasoning_content')
                    or ch['message'].get('reasoning') or '')
            valasz = nyers.split('</think>')[-1] if '</think>' in nyers else nyers
            futasok.append({
                'nyers': nyers[:600], 'valasz': norm(valasz),
                'han_a_valaszban': han_e(valasz),
                'han_a_gondolkodasban': han_e(gond),
                'gondolkodas_hossz': len(gond),
                'finish': ch.get('finish_reason'),
                'usage': body.get('usage') or {}, 'wall_ms': round(wall, 1)})
        jok = [f for f in futasok if 'hiba' not in f]
        # Többségi válasz; döntetlennél az első. A greedy elvben determinisztikus,
        # de a round5 mérte, hogy nem mindig az — ezért mérjük.
        szamlalo = Counter(f['valasz'] for f in jok)
        fo = szamlalo.most_common(1)[0][0] if szamlalo else None
        helyes = fo is not None and any(norm(g) == fo for g in it['gt'])
        han = bool(jok) and jok[0]['han_a_valaszban']
        sor = {'id': it['id'], 'kategoria': it['kategoria'],
               'valasz': fo, 'gt': it['gt'], 'helyes': helyes,
               'han_a_valaszban': han, 'instabil': len(szamlalo) > 1,
               'futasok': futasok}
        with lakat:
            eredmenyek.append(sor)
            print(f'[{len(eredmenyek)}/{len(items)}] {it["id"]:7s} '
                  f'{"✓" if helyes else "✗"} {"" if han else "⚠️nincs Han"} '
                  f'{(fo or "")[:24]!r} (gt: {it["gt"][0]})',
                  file=sys.stderr, flush=True)
            Path(a.out).write_text(json.dumps({'cimke': a.cimke, 'args': vars(a),
                                               'kesz': len(eredmenyek),
                                               'eredmenyek': eredmenyek},
                                              ensure_ascii=False, indent=1))

    if a.parallel > 1:
        print(f'[i] párhuzamosság: {a.parallel}', file=sys.stderr)
        with ThreadPoolExecutor(max_workers=a.parallel) as pool:
            list(pool.map(dolgozik, enumerate(items, 1)))
    else:
        for nit in enumerate(items, 1):
            dolgozik(nit)
    sorrend = {it['id']: k for k, it in enumerate(items)}
    eredmenyek.sort(key=lambda e: sorrend.get(e['id'], 1 << 30))

    k = sum(1 for e in eredmenyek if e['helyes'])
    nh = sum(1 for e in eredmenyek if not e['han_a_valaszban'])
    p, lo, hi = wilson(k, len(eredmenyek))
    ph, hlo, hhi = wilson(nh, len(eredmenyek))
    kat = {}
    for e in eredmenyek:
        d = kat.setdefault(e['kategoria'], [0, 0])
        d[0] += e['helyes']; d[1] += 1
    osszegzes = {'pontszam': {'helyes': k, 'ossz': len(eredmenyek), 'arany': p,
                              'wilson95': [lo, hi]},
                 'han_nelkul': {'db': nh, 'ossz': len(eredmenyek), 'arany': ph,
                                'wilson95': [hlo, hhi]},
                 'instabil': sum(1 for e in eredmenyek if e['instabil']),
                 'kategoriank': {k2: {'helyes': v[0], 'ossz': v[1]}
                                 for k2, v in sorted(kat.items())}}
    Path(a.out).write_text(json.dumps({'cimke': a.cimke, 'args': vars(a),
                                       'osszegzes': osszegzes,
                                       'eredmenyek': eredmenyek},
                                      ensure_ascii=False, indent=1))
    print(f'\n=== {a.cimke}: {k}/{len(eredmenyek)} = {100*p:.1f} % '
          f'[{100*lo:.1f}–{100*hi:.1f}] ===', file=sys.stderr)
    print(f'Han NÉLKÜLI válasz: {nh}/{len(eredmenyek)} = {100*ph:.1f} % '
          f'[{100*hlo:.1f}–{100*hhi:.1f}]', file=sys.stderr)
    for k2, v in sorted(kat.items()):
        print(f'  {k2:<10} {v[0]}/{v[1]}', file=sys.stderr)
    print(f'mentve: {a.out}', file=sys.stderr)


if __name__ == '__main__':
    main()
