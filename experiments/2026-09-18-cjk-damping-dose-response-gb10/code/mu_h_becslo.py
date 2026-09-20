#!/usr/bin/env python3
"""F0/4 — a μ_h irányvektor becslése magyar szövegen, verziózott próbahalmazon.

Mi ez a vektor és miért magyar. Az irány-alapú csere (H2) a célsorokat erre állítja:

    W_i := −α · μ_h / ‖μ_h‖²        →        logit_i(h) = −α · ⟨μ_h, h⟩ / ‖μ_h‖²

Ha a generálás pillanatában a rejtett állapot a magyar átlag közelében van (h ≈ μ_h), a
célzott tokenek logitja ≈ −α, tehát gyakorlatilag kizárva. Ha viszont a kontextus KÍNAI,
akkor ⟨μ_h, h⟩ kicsi, és a lehúzás magától elenyészik. Ez a beavatkozás egész értelme:
nem a tokent tiltja, hanem a **magyar kontextusban** tiltja. Ezért mérünk magyar szövegen
— nem azon, amit elfojtunk.

### ⛔ Miért vLLM és nem transformers — MÉRT lelet, 2026-09-18

Az első változat `AutoModelForCausalLM`-mel töltötte be a checkpointot. A betöltés
lefutott, az önteszt átment, és a szám kijött volna — **csak épp értelmetlen**: a
transformers 5.5.4 a MoE szakértőket FÚZIONÁLT alakban várja
(`mlp.experts.gate_up_proj`), a checkpoint viszont szakértőnként tárol
(`mlp.experts.0.gate_proj.weight`), ezért mind a 40 réteg összes szakértősúlya
`MISSING` lett, azaz **véletlenszerűen inicializálódott**. A logitok belső
konzisztenciáját ellenőrző önteszt ezt nem látja, mert a `lm_head` és a végső norma
rendben volt.

Ezért a becslés a vLLM `token_embed` pooling útján megy: (1) ez az a motor, amin a karok
ténylegesen futnak, tehát a mért állapot az, amit a mérés lát; (2) a checkpointot
helyesen tölti be. A pooling a modelltörzs kimenetét adja vissza pozíciónként — ez
pontosan a `lm_head` bemenete.

### Az önteszt, ami nélkül nem futunk tovább

A „helyes vektor" állítás nem hihető magától. A szkript **tanári kényszerítéssel**
ellenőrzi: a `t`-edik pozíció rejtett állapotából `h_t · lm_headᵀ` argmaxa a `t+1`-edik
TÉNYLEGES tokent kell hogy eltalálja a magyar szövegen az esetek jelentős részében.
Véletlen szakértőkkel (vagy rossz rétegből vett állapottal) ez a szám a nulla közelébe
esik. Küszöb: 30 %, alatta LEÁLLÁS.

### Hol mérünk a szekvencián belül

Nem akárhol. A releváns állapot az, AMIBŐL a következő magyar token megjósolódik
generálás közben — tehát a csevegő-sablonnal felépített kérés + magyar asszisztens-válasz,
és az átlag **csak az asszisztens-válasz pozícióira** megy. A rendszerpromptra, a
felhasználói üzenetre és a sablon vezérlőtokenjeire nem: azok nem generálási pozíciók.
Az itemenkénti átlagok EGYENLŐ súllyal kerülnek a végső átlagba, hogy egy hosszú item ne
uralja a becslést.

Használat (measurement-host, a kiszolgáló image-ében, GPU-val):
    python3 mu_h_becslo.py --model <snapshot> --proba mu-h-probahalmaz-A.json \
        --out mu-h-A.json
"""
import argparse, hashlib, json, os
from pathlib import Path


def asszisztens_tartomany(tok, item):
    """A sablonnal felépített teljes szekvencia, és benne az asszisztens-válasz
    token-tartománya.

    ⚠️ MÉRT buktató (2026-09-18): a tartományt NEM lehet token-előtag különbségből
    megkapni. A `add_generation_prompt=True` előtag sztringszinten valóban előtagja a
    teljes sablonnak (`…<|im_start|>assistant\\n<think>\\n`), tokenszinten viszont nem: a
    záró `\\n` a teljes változatban a rákövetkező `\\n</think>` darabbal EGY tokenné olvad
    össze. A naiv különbségképzés ezért minden itemen leállt.

    A megoldás karakter-eltolás: a teljes sablont EGYBEN tokenizáljuk, és azokat a
    tokeneket vesszük, amelyek karaktertartománya az asszisztens-válasz szövegébe esik.
    Ez a sablon belső szerkezetéről semmit nem feltételez.
    """
    uzenetek = [{'role': 'system', 'content': item['rendszer']},
                {'role': 'user', 'content': item['felhasznalo']}]
    valasz = item['asszisztens']
    teljes_szoveg = tok.apply_chat_template(
        uzenetek + [{'role': 'assistant', 'content': valasz}],
        tokenize=False, add_generation_prompt=False)
    kezd_ch = teljes_szoveg.rindex(valasz)
    veg_ch = kezd_ch + len(valasz)

    kod = tok(teljes_szoveg, add_special_tokens=False, return_offsets_mapping=True)
    ids, off = list(kod['input_ids']), kod['offset_mapping']
    benne = [k for k, (s0, s1) in enumerate(off)
             if s0 >= kezd_ch and s1 <= veg_ch and s1 > s0]
    if not benne:
        raise SystemExit(f'{item["id"]}: nem található az asszisztens-válasz tartománya')
    return ids, benne[0], benne[-1] + 1


def lm_head_betolt(snapshot):
    """A `lm_head.weight` beolvasása az indexből, a modell betöltése nélkül."""
    import torch
    from safetensors.torch import load_file
    snapshot = Path(snapshot)
    idx = json.loads((snapshot / 'model.safetensors.index.json').read_text())['weight_map']
    shard = idx['lm_head.weight']
    from safetensors import safe_open
    with safe_open(str(snapshot / shard), 'pt') as f:
        return f.get_tensor('lm_head.weight')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--model', required=True, help='snapshot könyvtár')
    ap.add_argument('--proba', type=Path, required=True, help='a verziózott próbahalmaz')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--min-itemek', type=int, default=30)
    ap.add_argument('--gpu-mem', type=float, default=0.80)
    ap.add_argument('--max-len', type=int, default=4096)
    ap.add_argument('--onteszt-kuszob', type=float, default=0.30,
                    help='tanári kényszerítés top-1 találati arány alsó korlátja')
    a = ap.parse_args()

    import torch
    from transformers import AutoTokenizer
    from vllm import LLM
    from vllm.config import PoolerConfig
    from vllm.inputs import TokensPrompt

    nyers = a.proba.read_bytes()
    proba = json.loads(nyers)
    items = proba['itemek']
    proba_sha = hashlib.sha256(nyers).hexdigest()
    print(f'próbahalmaz : {proba["nev"]} v{proba["verzio"]} — {len(items)} item')
    print(f'  sha256    : {proba_sha}')
    if len(items) < a.min_itemek:
        raise SystemExit(f'csak {len(items)} item — a runbook legalább '
                         f'{a.min_itemek}-at ír elő')

    tok = AutoTokenizer.from_pretrained(a.model, trust_remote_code=True)
    szekvenciak = [asszisztens_tartomany(tok, it) for it in items]

    print('lm_head beolvasása (a modell betöltése nélkül)…', flush=True)
    W = lm_head_betolt(a.model).float()
    print(f'  lm_head.weight: {tuple(W.shape)}')

    print('vLLM betöltés (pooling / token_embed)…', flush=True)
    # ⚠️ MÉRT (2026-09-18): alapbeállításokkal a motor `No available memory for the
    # cache blocks`-szal elhasal. Az ok nem a súly (33,3 GiB), hanem a VIZUÁLIS torony
    # profilozása: a kiszolgáló a legnagyobb képméretre foglal kódoló-gyorstárat. Nekünk
    # kép sosem megy be, ezért a multimodális keretet nullázzuk, és a kötegméretet a
    # round5 kiszolgálóprofiljára húzzuk.
    llm = LLM(model=a.model, runner='pooling', convert='embed',
              trust_remote_code=True, enforce_eager=True,
              gpu_memory_utilization=a.gpu_mem, max_model_len=a.max_len,
              max_num_batched_tokens=8192, max_num_seqs=8,
              limit_mm_per_prompt={'image': 0, 'video': 0},
              pooler_config=PoolerConfig(pooling_type='ALL', use_activation=False))

    kimenetek = llm.encode([TokensPrompt(prompt_token_ids=ids)
                            for ids, _, _ in szekvenciak],
                           pooling_task='token_embed')

    hid = W.shape[1]
    ossz = torch.zeros(hid, dtype=torch.float64)
    reszletek, atlagok = [], []
    talalat = poz_ossz = 0
    for item, (ids, kezd, veg), ki in zip(items, szekvenciak, kimenetek):
        h = ki.outputs.data.float().cpu()
        if h.shape[0] != len(ids):
            raise SystemExit(f'{item["id"]}: {h.shape[0]} pozíció {len(ids)} token helyett '
                             f'— a pooling nem ALL')
        if h.shape[1] != hid:
            raise SystemExit(f'{item["id"]}: rejtett dimenzió {h.shape[1]}, '
                             f'a lm_head szerint {hid}')
        # A pozíció, AMIBŐL a k-adik válasz-token megjósolódik, a k−1-edik.
        szelet = h[kezd - 1:veg - 1]

        # --- önteszt: tanári kényszerítés a válasz-tartományon ---
        jos = (szelet @ W.T).argmax(dim=1)
        val = torch.tensor(ids[kezd:veg])
        talalat += int((jos == val).sum())
        poz_ossz += len(val)

        atlag = szelet.double().mean(0)
        ossz += atlag
        atlagok.append(atlag)
        reszletek.append({'id': item['id'], 'tokenek': len(ids),
                          'valasz_pozicio': veg - kezd,
                          'norma': round(atlag.norm().item(), 4),
                          'top1_talalat': int((jos == val).sum()),
                          'top1_ossz': len(val)})
        print(f'{item["id"]:<10} {len(ids):>5} token, {veg - kezd:>4} válasz-pozíció, '
              f'‖átlag‖={atlag.norm():>8.3f}, top-1 {int((jos==val).sum()):>3}/{len(val)}',
              flush=True)

    arany = talalat / poz_ossz
    print(f'\nönteszt (tanári kényszerítés): top-1 {talalat}/{poz_ossz} = {100*arany:.1f} %')
    if arany < a.onteszt_kuszob:
        raise SystemExit(f'a top-1 találat {100*arany:.1f} %, a küszöb '
                         f'{100*a.onteszt_kuszob:.0f} % — a rejtett állapotok NEM a '
                         f'lm_head bemenete (vagy a modell rosszul töltődött be); leállás')
    print('  ✓ a rejtett állapotok a lm_head bemenetei')

    mu = (ossz / len(items)).float()
    print(f'\nμ_h: ‖μ_h‖ = {mu.norm():.4f}, dim = {mu.numel()}')

    # Mennyire egyirányúak az itemek? Ha a szórás nagy, a μ_h nem „a magyar irány",
    # hanem egy esetleges átlag, és a H2/H4 értelmezése is más. A jegyzőkönyvbe kerül
    # akkor is, ha nem érdekes.
    mud = mu.double()
    koszinuszok = []
    for r, h in zip(reszletek, atlagok):
        cos = (torch.dot(h, mud) / (h.norm() * mud.norm())).item()
        r['koszinusz_mu_h'] = round(cos, 4)
        koszinuszok.append(cos)
    kmin, kmax = min(koszinuszok), max(koszinuszok)
    katlag = sum(koszinuszok) / len(koszinuszok)
    print(f'item↔μ_h koszinusz: átlag {katlag:.4f}, min {kmin:.4f}, max {kmax:.4f}')

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps({
        'nev': proba['nev'], 'verzio': proba['verzio'], 'proba_sha256': proba_sha,
        'model': a.model, 'motor': 'vllm token_embed pooling', 'hidden_size': hid,
        'itemek': len(items),
        'onteszt_top1': {'talalat': talalat, 'ossz': poz_ossz, 'arany': arany,
                         'kuszob': a.onteszt_kuszob},
        'mu_h': [round(x, 8) for x in mu.tolist()],
        'mu_h_norma': mu.norm().item(),
        'koszinusz': {'atlag': katlag, 'min': kmin, 'max': kmax},
        'reszletek': reszletek,
    }, ensure_ascii=False), encoding='utf-8')
    print(f'kiírva: {a.out}', flush=True)
    # ⚠️ MÉRT (2026-09-18): a vLLM motor lebontása `terminate called without an active
    # exception`-nel beragad, és a konténer a kész eredmény után is fut tovább. Az
    # eredmény ekkor már lemezen van, tehát a kilépés biztonságos — de a vezénylő
    # enélkül soha nem lépne a következő karra.
    os._exit(0)


if __name__ == '__main__':
    main()
