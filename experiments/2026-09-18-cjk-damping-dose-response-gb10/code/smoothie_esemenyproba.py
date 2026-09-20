#!/usr/bin/env python3
"""round5 — a RÖGZÍTETT nyelvváltási esemény visszajátszása egyetlen pozícióra.

Ez a legélesebb előtte/utána teszt, ami rendelkezésre áll: a Han-pozitív felvételből
vesszük a tényleges `prompt_token_ids + token_ids[:j]` sorozatot, ahol `j` az első Han
tokent kiadó pozíció, és megkérdezzük a kiszolgálót, mi jönne ott. Nincs újratokenizálás
és nincs szabad generálás, tehát a prefix bájtra ugyanaz — az egyetlen változó a modell.

`temperature=0`, `logprobs=20`: a nyers top-20 jön vissza, amit a Smoothie-folt előtt és
után össze lehet vetni ugyanazon a pozíción.

⚠️ Korlát: a teljes tokenprefix új prefillként megy be, tehát az eredeti decode/MTP/cache
útvonal nem áll helyre. Ez a lokális kérdésre jó („ebből az állapotból mit preferál a
modell"), a jelenség reprodukciójának NEM nevezhető.
"""
import argparse, json, unicodedata, uuid
from pathlib import Path
from urllib.request import Request, urlopen


def is_han(ch):
    return unicodedata.name(ch, '').startswith(
        ('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-'))


def tid(f):
    return int(f.split(':', 1)[1]) if isinstance(f, str) and f.startswith('token_id:') else None


ap = argparse.ArgumentParser()
ap.add_argument('--record', type=Path, required=True)
ap.add_argument('--url', required=True)
ap.add_argument('--label', required=True)
ap.add_argument('--out', type=Path)
a = ap.parse_args()

rec = json.loads(a.record.read_text())
resp = rec['response']
choice = resp['choices'][0]
lp = (choice.get('logprobs') or {}).get('content') or []
prompt_ids = resp.get('prompt_token_ids') or []
out_ids = choice.get('token_ids') or []

# Az első Han tokent kiadó pozíció — a felvett logprob-listából, a `token` mező
# `token_id:N` alakú, ezért a szövegét a felvett top_logprobs nem adja meg; a
# pozíciót az out_ids-ből azonosítjuk a felvételben szereplő Han-szakasz alapján.
j = None
for i, e in enumerate(lp):
    t = tid(e.get('token'))
    if t is None:
        continue
    # a szerver /detokenize végpontja dönti el, hogy Han-e
    req = Request(a.url.rstrip('/') + '/detokenize',
                  data=json.dumps({'tokens': [t]}).encode(),
                  headers={'Content-Type': 'application/json'})
    txt = json.load(urlopen(req, timeout=60)).get('prompt', '')
    if any(is_han(c) for c in txt):
        j = i
        han_text = txt
        break
if j is None:
    raise SystemExit('nincs Han token a felvételben')

prefix = list(prompt_ids) + list(out_ids[:j])
payload = {'model': rec['response']['model'], 'prompt': prefix, 'max_tokens': 1,
           'temperature': 0, 'logprobs': 20, 'echo': False, 'stream': False,
           'cache_salt': 'smoothie-' + uuid.uuid4().hex}
req = Request(a.url.rstrip('/') + '/v1/completions',
              data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
body = json.load(urlopen(req, timeout=1800))
c0 = body['choices'][0]
tl = (c0.get('logprobs') or {}).get('top_logprobs') or [{}]
top = tl[0] if tl else {}

rows = sorted(top.items(), key=lambda kv: -kv[1])
print(f'=== {a.label}')
print(f'    felvétel : {a.record.name}, pozíció #{j}, az eredeti token: {han_text!r}')
print(f'    prefix   : {len(prefix)} token ({len(prompt_ids)} prompt + {j} generált)')
print(f'    kiválasztott (greedy): {c0.get("text")!r}')
print(f'    {"jelölt":<22} {"logprob":>10}  Han')
hanmass = 0.0
import math
mx = rows[0][1] if rows else 0.0
z = [math.exp(v - mx) for _, v in rows]
s = sum(z) or 1.0
for (t, v), zz in zip(rows, z):
    h = any(is_han(ch) for ch in t)
    if h:
        hanmass += zz / s
    print(f'    {t!r:<22} {v:>10.4f}  {"KÍNAI" if h else ""}')
print(f'    Han-tömeg a top-20-ban: {hanmass*100:.3f} %')
if a.out:
    a.out.write_text(json.dumps({'label': a.label, 'position': j,
                                 'original_token': han_text, 'response': body,
                                 'han_mass_top20': hanmass}, ensure_ascii=False, indent=1))
