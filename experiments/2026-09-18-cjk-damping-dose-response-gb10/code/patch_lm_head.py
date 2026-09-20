#!/usr/bin/env python3
"""F0/3 — egytenzoros beavatkozás a `lm_head.weight`-en, KÉT formában.

A round5 `patch_lm_head.py` kiterjesztése. Ami változatlan: a beavatkozás sebészi, csak
az a shard íródik újra, amelyben a `lm_head.weight` van, a többi fájl SZIMLINKET kap, és
a teljes FP8 kvantálási állapot bitre érintetlen marad. Ez nem kényelmi kérdés: ha a
kvantálás változik, a mérés elveszíti az ok-okozati erejét.

Ami új: a **forma** mint mért változó (H2).

    szorzas    W_i := S · W_i                      (dnotitia/smoothie-qwen)
    irany      W_i := −α · μ_h / ‖μ_h‖²            (ThakiCloud/…-ko-cjk-suppressed)

A `szorzas` a logitot arányosan zsugorítja: `logit = W·h`, tehát sor × S = logit × S.
⚠️ Ennek ismert előjel-csapdája van: ha egy token logitja NEGATÍV, a 0 < S < 1 szorzó a
logitot NULLA FELÉ tolja, azaz NÖVELI a valószínűségét. A round5 ezt egyetlen billenési
ponton mérte meg (nem volt aktív) — ez a kör több ponton ellenőrzi.

Az `irany` ezzel szemben a sort KICSERÉLI, nem szorozza, tehát az előjel-csapda fogalmilag
nem áll fenn. A kapott logit `−α · ⟨μ_h, h⟩ / ‖μ_h‖²`: magyar kontextusban (h ≈ μ_h)
nagyjából `−α`, kínai kontextusban viszont magától elenyészik. Ez a kontextusérzékenység
a H4 tárgya.

A `--mu-h` megadásakor a szkript MINDKÉT formánál kiírja az előjel-diagnosztikát: hány
célzott sor logitja negatív a magyar átlagállapotban, és mennyi lesz belőle a folt után.
Ez a legolcsóbb pont, ahol az előjel-csapda egyáltalán látszik — nem helyettesíti az F3
célzott mérését, de ingyen van.

Használat:
    # szorzás, nyers maszk, S=0,5
    python3 patch_lm_head.py --snapshot <alap> --celtokenek celtokenek.json \
        --maszk nyers --forma szorzas --skala 0.5 --out <ki> --kar S05
    # irány-csere, finomított maszk, α=200
    python3 patch_lm_head.py --snapshot <alap> --celtokenek celtokenek.json \
        --maszk finomitott --forma irany --alpha 200 --mu-h mu-h-A.json \
        --out <ki> --kar A200F
"""
import argparse, hashlib, json, os
from pathlib import Path
import torch
from safetensors.torch import load_file, save_file

KEY = 'lm_head.weight'


def sha256_fajl(p, blokk=1 << 22):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while (d := f.read(blokk)):
            h.update(d)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--snapshot', type=Path, required=True, help='eredeti snapshot könyvtár')
    ap.add_argument('--celtokenek', type=Path, required=True, help='celtokenek.py kimenete')
    ap.add_argument('--maszk', choices=['nyers', 'finomitott'], required=True)
    ap.add_argument('--forma', choices=['szorzas', 'irany'], required=True)
    ap.add_argument('--skala', type=float, help='szorzás: S (0..1)')
    ap.add_argument('--alpha', type=float, help='irány: α')
    ap.add_argument('--mu-h', type=Path, help='mu_h_becslo.py kimenete (irányhoz kötelező)')
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--kar', required=True, help='a kar neve a jegyzőkönyvhöz, pl. S05')
    a = ap.parse_args()

    if a.forma == 'szorzas' and a.skala is None:
        raise SystemExit('a szorzás formához --skala kell')
    if a.forma == 'irany' and (a.alpha is None or a.mu_h is None):
        raise SystemExit('az irány formához --alpha és --mu-h kell')

    ct = json.loads(a.celtokenek.read_text())
    targets = ct['maszkok'][a.maszk]
    idx = json.loads((a.snapshot / 'model.safetensors.index.json').read_text())['weight_map']
    if KEY not in idx:
        raise SystemExit(f'nincs {KEY} az indexben')
    shard = idx[KEY]

    print(f'kar          : {a.kar}')
    print(f'forma        : {a.forma}')
    print(f'maszk        : {a.maszk}  ({len(targets)} sor)')
    print(f'shard        : {shard}')

    src = a.snapshot / shard
    tensors = load_file(str(src))
    eredeti = {k: v.clone() for k, v in tensors.items()}
    w = tensors[KEY]
    print(f'{KEY}: alak={tuple(w.shape)} dtype={w.dtype}')
    rossz = [t for t in targets if t >= w.shape[0]]
    if rossz:
        raise SystemExit(f'{len(rossz)} cél-ID a mátrixon kívül (max {w.shape[0]-1})')

    ix = torch.tensor(targets, dtype=torch.long)
    w32 = w.to(torch.float32)
    elotte = w32.index_select(0, ix)
    norm_elotte = elotte.norm(dim=1)

    mu = None
    if a.mu_h:
        muj = json.loads(a.mu_h.read_text())
        mu = torch.tensor(muj['mu_h'], dtype=torch.float32)
        if mu.numel() != w.shape[1]:
            raise SystemExit(f'μ_h dimenziója {mu.numel()}, a mátrixé {w.shape[1]}')
        print(f'μ_h          : {muj["nev"]} v{muj["verzio"]}, ‖μ_h‖={mu.norm():.4f}')

    # --- előjel-diagnosztika a magyar átlagállapotban, a folt ELŐTT ---
    diag = {}
    if mu is not None:
        logit_elotte = elotte @ mu
        diag['celzott_logit_mu_h_elotte'] = {
            'atlag': logit_elotte.mean().item(), 'min': logit_elotte.min().item(),
            'max': logit_elotte.max().item(),
            'negativ_sor': int((logit_elotte < 0).sum().item()),
            'negativ_arany': (logit_elotte < 0).float().mean().item()}
        print(f'előjel-diagnosztika (folt előtt, h=μ_h): '
              f'{diag["celzott_logit_mu_h_elotte"]["negativ_sor"]} / {len(targets)} '
              f'célzott sor logitja NEGATÍV '
              f'({100*diag["celzott_logit_mu_h_elotte"]["negativ_arany"]:.2f} %)')

    # --- a beavatkozás ---
    if a.forma == 'szorzas':
        w32[ix] *= a.skala
        print(f'skála        : {a.skala}')
    else:
        uj_sor = (-a.alpha / (mu.norm() ** 2)) * mu           # W_i := −α·μ_h/‖μ_h‖²
        w32[ix] = uj_sor.to(w32.dtype).expand(len(targets), -1)
        print(f'alpha        : {a.alpha}  → logit(h=μ_h) = {(uj_sor @ mu).item():.3f}')

    tensors[KEY] = w32.to(w.dtype)
    utana = tensors[KEY].index_select(0, ix).float()
    norm_utana = utana.norm(dim=1)
    print(f'sornorma átlag: {norm_elotte.mean():.4f} → {norm_utana.mean():.4f} '
          f'(arány {(norm_utana.mean()/norm_elotte.mean()):.4f})')

    if mu is not None:
        logit_utana = utana @ mu
        diag['celzott_logit_mu_h_utana'] = {
            'atlag': logit_utana.mean().item(), 'min': logit_utana.min().item(),
            'max': logit_utana.max().item(),
            'negativ_sor': int((logit_utana < 0).sum().item())}
        # ⚠️ Az előjel-csapda MÉRÉSE: hány sor logitja NŐTT a folttól?
        nott = int((logit_utana > logit_elotte + 1e-6).sum().item())
        diag['logit_nott_sor'] = nott
        print(f'előjel-csapda: {nott} / {len(targets)} célzott sor logitja NŐTT '
              f'a folttól (h=μ_h mellett)')
        print(f'  célzott logit átlag: {logit_elotte.mean():.3f} → '
              f'{logit_utana.mean():.3f}')

    # --- kontroll: a NEM célzott sorok és a shard többi tenzora bitre azonos ---
    celhalmaz = set(targets)
    kontroll = [i for i in range(min(w.shape[0], 5000)) if i not in celhalmaz][:512]
    ki = torch.tensor(kontroll, dtype=torch.long)
    if not torch.equal(eredeti[KEY].index_select(0, ki), tensors[KEY].index_select(0, ki)):
        raise SystemExit('nem célzott SOR változott meg — leállás')
    print(f'kontroll: {len(kontroll)} nem célzott sor bitre azonos ✓')
    for k, v in eredeti.items():
        if k == KEY:
            continue
        if not torch.equal(v, tensors[k]):
            raise SystemExit(f'a(z) {k} tenzor megváltozott — leállás')
    print(f'kontroll: a shard {len(eredeti)-1} egyéb tenzora bitre azonos ✓')

    # --- kiírás: minden fájl szimlink, KIVÉVE a foltozott shardot ---
    a.out.mkdir(parents=True, exist_ok=True)
    szimlink = 0
    for item in sorted(os.listdir(a.snapshot)):
        dst = a.out / item
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        if item == shard:
            continue
        dst.symlink_to(os.path.realpath(a.snapshot / item))
        szimlink += 1
    save_file(tensors, str(a.out / shard), metadata={'format': 'pt'})
    uj_sha = sha256_fajl(a.out / shard)
    print(f'\nfoltozott snapshot: {a.out}')
    print(f'  újraírt shard : {shard} '
          f'({(a.out / shard).stat().st_size / 1e9:.2f} GB)')
    print(f'  sha256        : {uj_sha}')
    print(f'  szimlink      : {szimlink} fájl')

    (a.out / 'KAR.json').write_text(json.dumps({
        'kar': a.kar, 'forma': a.forma, 'maszk': a.maszk,
        'skala': a.skala, 'alpha': a.alpha,
        'mu_h': (json.loads(a.mu_h.read_text())['nev'] + ' v'
                 + json.loads(a.mu_h.read_text())['verzio']) if a.mu_h else None,
        'celzott_sor': len(targets),
        'forras_snapshot': str(a.snapshot),
        'ujrairt_shard': shard, 'ujrairt_shard_sha256': uj_sha,
        'szimlink_fajl': szimlink,
        'celtokenek_forras': str(a.celtokenek),
        'celtokenek_stat': ct['stats'],
        'elojel_diagnosztika': diag,
        'megjegyzes': ('csak a lm_head.weight célzott sorai módosultak; az FP8 súlyok '
                       'és a shard minden egyéb tenzora bitre érintetlen'),
    }, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'  KAR.json      : kiírva')


if __name__ == '__main__':
    main()
