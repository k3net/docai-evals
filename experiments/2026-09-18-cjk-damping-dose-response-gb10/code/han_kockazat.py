#!/usr/bin/env python3
"""round5 — Han-KOCKÁZAT minden generált pozícióban, a már felvett logprobokból.

Miért kell ez: a nyelvváltás ritka esemény. 10–30 ismétléssel karonként 0–2 találat jön,
amiből arányt becsülni nem lehet, és két kar között különbséget kimutatni még kevésbé. A
felvételben viszont MINDEN generált pozícióra ott van a nyers top-20 — pozíciónként egy
mérés, válaszonként több ezer, karonként több tízezer.

A mérőszám a VÁRHATÓ Han-tokenszám egy válaszban:

    E[Han] = Σ_pozíció  p_Han(pozíció)

ahol p_Han a Han jelöltek összvalószínűsége a tényleges mintavételezési lánc után
(presence_penalty → repetition_penalty jelzés → temperature → top_k → top_p).
Mivel a kiszolgáló `raw_logprobs` módban ad logprobot, a nyers eloszlás ismert, és a
mintavételezési lánc ELLENKONTRAFAKTUÁLISAN is átszámolható: „mennyi lett volna
presence_penalty nélkül", „mennyi 0,3-as hőmérsékleten".

⚠️ Korlátok, amiket nem szabad elhallgatni:
  * A kontrafaktuál LOKÁLIS: azt mondja meg, mekkora volt a kockázat a TÉNYLEGESEN
    bejárt pozíciókban. Más samplinggel a modell más úton menne, tehát ez nem
    ugyanaz, mint egy tényleges B-kar — a rács empirikus ellenőrzése nem kiváltható.
  * Csak a top-20 látszik. A top-20-on kívüli Han tokenek valószínűsége nem nulla,
    csak ismeretlen — a becslés tehát ALSÓ korlát.
  * A `repetition_penalty` hatása a logit előjelétől függ, amit a felvételből nem tudunk;
    a szkript ezt jelzi, de nem számolja bele. rp=1,05 mellett ez kis korrekció.
"""
import argparse, glob, json, math, unicodedata
from pathlib import Path
from transformers import AutoTokenizer

ap = argparse.ArgumentParser()
ap.add_argument('--results', default='results')
ap.add_argument('--tokenizer', required=True)
ap.add_argument('--arms', nargs='*', help='csak ezek a kar-könyvtárak')
# ⭐ 2026-09-18 (cjk-csillapítás): gépi kimenet az eredménylaphoz. A szöveges kiírás
# BÁJTRA változatlan marad — a round5 számai így összevethetők maradnak.
ap.add_argument('--json', dest='json_ut', default=None,
                help='a számolt értékek JSON-ba is, a szöveges kiírás változtatása nélkül')
ap.add_argument('--bootstrap', type=int, default=2000,
                help='⭐ 2026-09-18 döntés (runbook §5 pontosítás): az elsődleges '
                     'HASZON-végpont a POZÍCIÓNKÉNTI E[Han] = Σp, nem a megfigyelt '
                     'eseményszám. Ez exact 0 tud lenni (a mintavételezési lánc '
                     'csonkolása után minden p_i = 0), és a megfigyelt eseményekre '
                     'épített Poisson-korlát ezen a mintanagyságon használhatatlan '
                     '(~220/M). A bizonytalanságot ezért VÁLASZONKÉNTI bootstrap adja: '
                     'a válaszok az egymástól független megfigyelési egységek.')
ap.add_argument('--feldolgozott', action='store_true',
                help='⭐ 2026-09-19 (a felhasználó lelete): a kiszolgáló `--logprobs-mode '
                     'processed_logprobs` módban futott, tehát a rögzített top-20 MÁR a '
                     'büntetések + hőmérséklet + top_k + top_p UTÁNI eloszlás (a tartón '
                     'kívül −inf). Ilyenkor nincs mit átszámolni: E[Han] = Σ exp(logprob) a '
                     'Han jelöltekre, a TÉNYLEGES beállításon. A kontrafaktuális rács itt '
                     'értelmetlen, ezért egyetlen sor jelenik meg. Ez a mód szünteti meg a '
                     'nyers-top-20 korlátot: a presence_penalty által kinyitott helyekre '
                     'bejutó (nyersen 21+.) tokenek itt már látszanak.')
ap.add_argument('--poisson', action='store_true',
                help='Poisson exact 95%% FELSŐ KORLÁT a ténylegesen megfigyelt Han '
                     'tokenekre. ⛔ A runbook §5: a 0/M önmagában NEM eredmény.')
a = ap.parse_args()

tok = AutoTokenizer.from_pretrained(a.tokenizer, trust_remote_code=True)


def is_han_text(s):
    return any(unicodedata.name(c, '').startswith(
        ('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-')) for c in s)


# A Han-tokenek ID-halmaza EGYSZER, a vocabból — pozíciónkénti dekódolás helyett.
#
# ⚠️ NEM `convert_tokens_to_string`-gel. A Qwen bájt-szintű BPE-t használ: a többbájtos
# UTF-8 sorozatok TÖREDÉKEI önálló tokenek, és egy töredéket magában „stringgé alakítva"
# tetszőleges bájtsorozat jön ki, ami gyakran érvényes CJK karakterré dekódolódik. Így a
# magyar ékezetes betűk darabjai is Han-találatnak látszottak, és a mérés ~20-szorosan
# felülbecsülte a kockázatot. A `decode` ezzel szemben a hibás sorozatra U+FFFD-t ad.
print('Han-tokenek gyűjtése a vocabból…', flush=True)
_ids = sorted(tok.get_vocab().values())
HAN_IDS = set()
for start in range(0, len(_ids), 4096):
    chunk = _ids[start:start + 4096]
    for i, txt in zip(chunk, tok.batch_decode([[i] for i in chunk])):
        if '\ufffd' in txt:          # csonka bájtsorozat — nem önálló karakter
            continue
        if is_han_text(txt):
            HAN_IDS.add(i)
print(f'  {len(HAN_IDS)} Han-tartalmú token a {len(_ids)} elemű vocabban '
      f'({100*len(HAN_IDS)/len(_ids):.1f} %)\n', flush=True)


def tid(f):
    return int(f.split(':', 1)[1]) if isinstance(f, str) and f.startswith('token_id:') else None


def han_mass(entry, prefix, pp, temp, top_p):
    """A Han jelöltek összvalószínűsége EGY pozícióban, a sampling lánc után.

    temp == 0 → greedy: a büntetett eloszlás argmaxa nyer, tehát a Han-tömeg 1 vagy 0.
    (Korábbi hiba: a `... or 1` a nullát 1,0-ra fordította, és a greedy kar „tényleges"
    sora valójában t=1,0-t mutatott.)"""
    cand = []
    if pp is None:
        # --feldolgozott: a logprob már a teljes lánc utáni; a tartón kívüli jelölt −inf.
        return sum(math.exp(x['logprob']) for x in entry.get('top_logprobs', [])
                   if tid(x['token']) in HAN_IDS and x['logprob'] > -1e30)
    for x in entry.get('top_logprobs', []):
        t = tid(x['token'])
        if t is None:
            continue
        eff = x['logprob'] - (pp if t in prefix else 0.0)
        cand.append((t, eff))
    if not cand:
        return 0.0
    cand.sort(key=lambda c: c[1], reverse=True)
    if temp <= 0:
        return 1.0 if cand[0][0] in HAN_IDS else 0.0
    mx = cand[0][1]
    z = [math.exp((e - mx) / temp) for _, e in cand]
    s = sum(z)
    probs = [v / s for v in z]
    cum, keep = 0.0, []
    for (t, _), pr in zip(cand, probs):
        keep.append((t, pr)); cum += pr
        if cum >= top_p:
            break
    s2 = sum(pr for _, pr in keep) or 1.0
    return sum(pr / s2 for t, pr in keep if t in HAN_IDS)


# Rögzített cellák: a 2b rács NÉGY karja + a greedy + a prod-hőmérséklet fölötti eset.
# Így ugyanaz a pálya mind a hat mintavételezéssel átszámolható, és a rács jóslata
# összevethető lesz a ténylegesen mért karokkal.
THINK_END = 248069      # `</think>` — itt válik el a gondolkodás a válaszól

SCEN = [('A pp1.5 t0.6 (prod)', 1.5, 0.6),
        ('B pp0   t0.6',        0.0, 0.6),
        ('C pp1.5 t0.3',        1.5, 0.3),
        ('D pp0   t0.3',        0.0, 0.3),
        ('K pp1.5 t1.0',        1.5, 1.0),
        ('L pp0   t1.0',        0.0, 1.0),
        ('  pp1.5 t0.8',        1.5, 0.8),
        ('  greedy',            0.0, 0.0)]
if a.feldolgozott:
    SCEN = [('  TÉNYLEGES (feldolgozott logprob)', None, None)]

GYUJTO = {}
dirs = a.arms or sorted({Path(p).parent.name for p in glob.glob(f'{a.results}/*/summary.json')})
for arm in dirs:
    files = sorted(glob.glob(f'{a.results}/{arm}/[0-9]*.json'))
    tot = {n: 0.0 for n, _, _ in SCEN}
    positions = answers = observed = 0
    seen_answers = set()          # a greedy determinisztikus: az azonos válasz EGYSZER számít
    skipped = spans = han_answers = 0
    seg_tot = {'gondolkodás': {n: 0.0 for n, _, _ in SCEN},
               'válasz': {n: 0.0 for n, _, _ in SCEN}}
    seg_pos = {'gondolkodás': 0, 'válasz': 0}
    seg_obs = {'gondolkodás': 0, 'válasz': 0}
    # Válaszonkénti bontás a bootstraphöz: (válasz-pozíciók, {beállítás: Σp})
    per_valasz = []
    for path in files:
        rec = json.load(open(path))
        ch = rec['response']['choices'][0]
        lp = (ch.get('logprobs') or {}).get('content') or []
        if not lp or not (rec.get('stats') or {}).get('has_final_content'):
            continue
        key = (rec['case_id'], rec['stats']['content_sha256'])
        if key in seen_answers:
            skipped += 1
            continue
        seen_answers.add(key)
        answers += 1
        out_ids = ch.get('token_ids') or []
        samp = rec['effective_sampling']
        topp = float(samp.get('top_p') or 1)
        if topp <= 0:
            topp = 1.0
        observed += sum(1 for t in out_ids if t in HAN_IDS)
        fh = (rec.get('stats') or {}).get('final_han') or []
        spans += len(fh)
        han_answers += 1 if fh else 0
        cut = out_ids.index(THINK_END) if THINK_END in out_ids else -1
        prefix = set()
        v_tot = {n: 0.0 for n, _, _ in SCEN}
        v_poz = 0
        for i, e in enumerate(lp):
            seg = 'gondolkodás' if (cut >= 0 and i <= cut) else 'válasz'
            for name, ppx, tx in SCEN:
                m = han_mass(e, prefix, ppx, tx, topp)
                tot[name] += m
                seg_tot[seg][name] += m
                if seg == 'válasz':
                    v_tot[name] += m
            if seg == 'válasz':
                v_poz += 1
            if i < len(out_ids):
                if out_ids[i] in HAN_IDS:
                    seg_obs[seg] += 1
                prefix.add(out_ids[i])
            positions += 1
            seg_pos[seg] += 1
        per_valasz.append((v_poz, v_tot))
    if not answers:
        print(f'=== {arm}: nincs logprobos végső válasz (instrumentálás nélküli kar?)\n')
        continue
    print(f'=== {arm}: {answers} KÜLÖNBÖZŐ végső válasz'
          f'{f" (+{skipped} ismétlődő kihagyva)" if skipped else ""}, '
          f'{positions} pozíció, {observed} ténylegesen generált Han token')
    print(f'      ebből gondolkodás: {seg_pos["gondolkodás"]} pozíció, '
          f'{seg_obs["gondolkodás"]} Han token | '
          f'válasz: {seg_pos["válasz"]} pozíció, {seg_obs["válasz"]} Han token')
    print(f'      a szonda {spans} Han-szakaszt talált a VÁLASZOKBAN '
          f'({han_answers} válasz érintett)')
    GYUJTO[arm] = {'valaszok': answers, 'poziciok': positions,
                   'megfigyelt_han': observed, 'szakaszok': spans,
                   'erintett_valasz': han_answers,
                   'szegmens_poziciok': dict(seg_pos), 'szegmens_han': dict(seg_obs),
                   'beallitasok': {}}
    print(f'      {"beállítás":<20} {"gondolkodás":>16} {"VÁLASZ":>16}   '
          f'{"E[Han]/válasz":>13}')
    for name, _, _ in SCEN:
        g = 1e6 * seg_tot['gondolkodás'][name] / max(seg_pos['gondolkodás'], 1)
        v = 1e6 * seg_tot['válasz'][name] / max(seg_pos['válasz'], 1)
        print(f'      {name:<20} {g:>13.1f}/M {v:>13.1f}/M   '
              f'{seg_tot["válasz"][name]/answers:>13.4f}')
        GYUJTO[arm]['beallitasok'][name.strip()] = {
            'gondolkodas_per_M': g, 'valasz_per_M': v,
            'E_han_per_valasz': seg_tot['válasz'][name] / answers}
    # ⭐ 2026-09-18 döntés: az elsődleges HASZON-végpont bizonytalansága VÁLASZONKÉNTI
    # bootstrappal. A válasz a független megfigyelési egység: egy válaszon belül a
    # pozíciók erősen korreláltak (ugyanaz a kontextus viszi őket), a válaszok között
    # viszont nem. A poziciónkénti Σp exact 0 tud lenni; ilyenkor a bootstrap CI is
    # [0; 0], és ezt KI KELL MONDANI, mert az „exact nulla" más állítás, mint a
    # „nem láttunk eseményt".
    if a.bootstrap > 0 and per_valasz:
        import random
        rng = random.Random(20260918)
        n_v = len(per_valasz)
        print(f'      — válaszonkénti bootstrap ({a.bootstrap} újramintavétel, '
              f'{n_v} válasz) —')
        for name, _, _ in SCEN:
            minta = []
            for _ in range(a.bootstrap):
                ind = [rng.randrange(n_v) for _ in range(n_v)]
                sp = sum(per_valasz[j][0] for j in ind)
                st = sum(per_valasz[j][1][name] for j in ind)
                minta.append(1e6 * st / sp if sp else 0.0)
            minta.sort()
            lo = minta[int(0.025 * len(minta))]
            hi = minta[min(len(minta) - 1, int(0.975 * len(minta)))]
            pont = 1e6 * seg_tot['válasz'][name] / max(seg_pos['válasz'], 1)
            jel = '  ⭐ EXACT NULLA' if hi == 0.0 and pont == 0.0 else ''
            print(f'      {name:<20} VÁLASZ {pont:>9.2f}/M  '
                  f'95 % bootstrap CI [{lo:.2f}; {hi:.2f}]/M{jel}')
            GYUJTO[arm]['beallitasok'][name.strip()]['bootstrap95'] = [lo, hi]
    if a.poisson:
        # A tényleges eseményszám felső korlátja — ez megy a „< X/M" állításba.
        import math
        def poisson_felso(k, alfa=0.05):
            if k == 0:
                return -math.log(alfa)
            def cdf(lam):
                return sum(math.exp(-lam + i*math.log(lam) - math.lgamma(i+1))
                           for i in range(k+1))
            lo, hi = 0.0, max(10.0, 2.0*(k+10))
            while cdf(hi) > alfa:
                hi *= 2
            for _ in range(200):
                m = (lo+hi)/2
                if cdf(m) > alfa: lo = m
                else: hi = m
            return (lo+hi)/2
        for szeg in ('gondolkodás', 'válasz'):
            k, n = seg_obs[szeg], max(seg_pos[szeg], 1)
            fk = 1e6 * poisson_felso(k) / n
            print(f'      MEGFIGYELT {szeg:<14} {k} esemény / {n} pozíció '
                  f'= {1e6*k/n:.1f}/M  ·  Poisson 95 % felső korlát: < {fk:.2f}/M')
            GYUJTO[arm].setdefault('poisson', {})[szeg] = {
                'esemeny': k, 'pozicio': n, 'megfigyelt_per_M': 1e6*k/n,
                'felso_korlat_per_M': fk}
    print()

if a.json_ut:
    Path(a.json_ut).write_text(json.dumps(GYUJTO, ensure_ascii=False, indent=1))
    print(f'gépi kimenet: {a.json_ut}')
