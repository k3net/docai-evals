#!/usr/bin/env python3
"""Független újraszámolás MINDEN rekordon — a `han_kockazat.py` ellenőrzése (2026-09-20).

A `han_kockazat.py` csak a VÉGSŐ VÁLASSZAL záruló rekordokat számolja (`has_final_content`),
és az azonos válaszokat egyszer. Kimaradnak tehát az eszközhívással záruló körök és az
elszabadult (végső válasz nélküli) generálások — gondolkodásostul. Ez a szkript semmit nem
hagy ki és semmit nem von össze: rekordonként a generált Han-tokenek száma, és ahol a
kiszolgáló `processed_logprobs` módban futott (`-fd-` könyvtárak), a Σp is, külön a
kihagyott rekordokra. A `normhiba` a top-20 valószínűségösszeg legnagyobb eltérése 1-től:
ha > 0, a tényleges tartó 20-nál nagyobb volt (holtverseny a top-k határán), és a Σp ott
alsó korlát.

Futtatás (a mérőgépen, a motor-image-ben): python3 han_ujraszamol_mind.py <tokenizer-út>
"""
import glob, json, math, sys, unicodedata, re
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(sys.argv[1], trust_remote_code=True)
def han(s): return any('CJK UNIFIED' in unicodedata.name(c,'') or 'CJK COMPAT' in unicodedata.name(c,'') for c in s)
ids = sorted(tok.get_vocab().values()); HAN=set()
for s in range(0,len(ids),4096):
    ch=ids[s:s+4096]
    for i,t in zip(ch,tok.batch_decode([[i] for i in ch])):
        if '�' not in t and han(t): HAN.add(i)
print('HAN ids', len(HAN))
TE=248069
def tid(f): return int(f.split(':',1)[1])
groups = {}
for d in sorted(glob.glob('/work/results/*/')):
    n=d.rstrip('/').split('/')[-1]
    if re.search(r'-s\d+$', n): continue          # a seedenkénti alkönyvtárak össze vannak gyűjtve
    groups[n]=sorted(glob.glob(d+'[0-9]*.json'))
print(f'{"könyvtár":<26}{"rek":>4}{"végs":>5}{"tool":>5}{"egyéb":>6} | MIND: poz  obsHan  Σp_feld | KIHAGYOTT(tool) poz obsHan Σp | normhiba')
for n,files in groups.items():
    fd = '-fd-' in n
    rek=veg=tool=egy=0; P=O=0; S=0.0; kP=kO=0; kS=0.0; worst=0.0
    for p in files:
        r=json.load(open(p)); ch=r['response']['choices'][0]
        lp=(ch.get('logprobs') or {}).get('content') or []; out=ch.get('token_ids') or []
        rek+=1; fin=ch.get('finish_reason'); hf=bool((r.get('stats') or {}).get('has_final_content'))
        veg+=hf; tool+=(fin=='tool_calls'); egy+=(fin not in('stop','tool_calls'))
        o=sum(1 for t in out if t in HAN); s=0.0
        if fd:
            for e in lp:
                tl=e.get('top_logprobs',[])
                s+=sum(math.exp(x['logprob']) for x in tl if x['logprob']>-1e30 and tid(x['token']) in HAN)
                tot=sum(math.exp(x['logprob']) for x in tl if x['logprob']>-1e30)
                worst=max(worst,abs(1-tot))
        P+=len(lp); O+=o; S+=s
        if not hf: kP+=len(lp); kO+=o; kS+=s
    sp=(lambda v,p: f'{1e6*v/max(p,1):>9.2f}/M') if fd else (lambda v,p: f'{"—":>11}')
    print(f'{n:<26}{rek:>4}{veg:>5}{tool:>5}{egy:>6} | {P:>8} {O:>5} {sp(S,P)} | {kP:>8} {kO:>5} {sp(kS,kP)} | {worst:.3g}' if fd else f'{n:<26}{rek:>4}{veg:>5}{tool:>5}{egy:>6} | {P:>8} {O:>5} {sp(S,P)} | {kP:>8} {kO:>5} {sp(kS,kP)} | —')
