#!/usr/bin/env python3
"""Mérés B / 1. rész — logit lens a mentett residualokból (spark-dev, konténer).

    bash ~/lang-study/src/run_spark.sh src/logit_lens.py

A teljes modellt NEM töltjük be: a logit lenshez két tenzor kell, azokat a
safetensorsból olvassuk ki közvetlenül (18 GB helyett 2 GB):
  * `lm_head.weight`                       [248320, 4096]  — ⛔ NEM tied az embeddinggel
  * `model.language_model.norm.weight`     [4096]          — a záró RMSNorm súlya

Rétegenként: x = RMSNorm(resid_post) → logits = x @ W_U.T → top-20.
⛔ A norm MINDEN mentett síkra kell, mert a `run.py` hookból menti a NYERS residualt (env.md);
aki a `hidden_states`-ből dolgozna, az utolsó rétegen kétszer normalizálna.

Bónusz (runbook §3): a VÁRT válasz első tokenjének rangja rétegenként — mikor „tudja"
a modell a választ, és függ-e ez a prompt nyelvétől.

Kimenet (kicsi, a laptopra szinkronizálható):
  results/lens_top.npz     ids [N,33,20] · logits [N,33,20]; a sorrend a lens_index.json-ban
  results/lens_vocab.json  a felbukkanó token-azonosítók → token-string
  results/lens_rank.json   a várt válasz első tokenjének rangja rétegenként
"""
import argparse
import glob
import json
import pathlib
import time

import numpy as np
import torch
from safetensors import safe_open
from transformers import AutoTokenizer
import scope_paths


MODEL = scope_paths.MODEL
ROOT = pathlib.Path("/work")
RES = scope_paths.res(ROOT)
TOPK = 20
CHUNK = 256          # [chunk, 248320] fp32 puffer miatt


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def load_weights():
    repo = "models--" + MODEL.replace("/", "--")
    snap = glob.glob(str(ROOT / f"hf/hub/{repo}/snapshots/*/model.safetensors.index.json"))[0]
    base = pathlib.Path(snap).parent
    wmap = json.load(open(snap))["weight_map"]
    want = {"lm_head.weight": None, "model.language_model.norm.weight": None}
    for key in want:
        with safe_open(base / wmap[key], framework="pt") as f:
            want[key] = f.get_tensor(key)
    return want["lm_head.weight"], want["model.language_model.norm.weight"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuned", action="store_true",
                    help="a tanult fordítókkal (results/tuned_lens.pt) — a NAIV lens ezen a modellen "
                         "a 0–23. rétegen olvashatatlan volt (Mérés B), ez annak a javítása")
    args = ap.parse_args()
    sfx = "_tuned" if args.tuned else ""
    metas = [json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    tok = AutoTokenizer.from_pretrained(MODEL)
    eps = 1e-6

    W_U, norm_w = load_weights()
    log(f"súlyok: lm_head {tuple(W_U.shape)} · norm {tuple(norm_w.shape)}")
    W_U = W_U.to("cuda", torch.float32).T.contiguous()          # [4096, vocab]
    norm_w = norm_w.to("cuda", torch.float32)

    X, order = [], []
    for m in metas:
        h = np.load(RES / "hidden" / f"{m['item_id']}_{m['lang']}.npy", mmap_mode="r")
        X.append(np.asarray(h[:, -1, :], dtype=np.float32))       # [33, 4096] — utolsó prompt-token
        order.append({"item_id": m["item_id"], "lang": m["lang"], "group": m["group"], "kind": m["kind"]})
    n_planes = X[0].shape[0]
    X = torch.from_numpy(np.stack(X)).cuda()
    N = X.shape[0]
    log(f"{N} prompt × {n_planes} sík betöltve")

    targets = []
    for m in metas:
        ids = []
        if m["kind"] == "fact" and m["expected"]:
            for variant in (" " + m["expected"], m["expected"]):
                t = tok(variant, add_special_tokens=False)["input_ids"]
                if t:
                    ids.append(t[0])
        targets.append(sorted(set(ids)))

    # ── tanult fordítók: h → A·h + b, ahol A = I + U·V (Belrose et al. 2023) ──────
    trans = None
    if args.tuned:
        ck = torch.load(RES / "tuned_lens.pt", map_location="cuda")
        U, V, B = ck["U"], ck["V"], ck["b"]
        assert U.shape[0] == n_planes - 1, f"{U.shape[0]} fordító {n_planes} síkra"
        trans = (U.cuda().float(), None if V is None else V.cuda().float(), B.cuda().float())
        log(f"tuned lens betöltve: {U.shape[0]} fordító, rang {ck['rank']} · "
            f"átlagos val-KL {np.mean([l['kl_identity'] for l in ck['meta']['layers']]):.3f} → "
            f"{np.mean([l['kl_tuned'] for l in ck['meta']['layers']]):.3f}")
        # ⛔ Az UTOLSÓ sík önmaga a cél, oda nincs fordító — azt érintetlenül hagyjuk.
        for L in range(n_planes - 1):
            h = X[:, L, :].float()
            d = (h @ trans[0][L]) @ trans[1][L] if trans[1] is not None else h @ trans[0][L]
            X[:, L, :] = h + d + trans[2][L]

    flat = X.reshape(N * n_planes, -1)
    top_ids = torch.empty((N * n_planes, TOPK), dtype=torch.int32)
    top_val = torch.empty((N * n_planes, TOPK), dtype=torch.float16)
    ranks = {}
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, flat.shape[0], CHUNK):
            e = min(s + CHUNK, flat.shape[0])
            x = flat[s:e]
            x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + eps) * norm_w   # RMSNorm
            logits = x @ W_U
            v, i = logits.topk(TOPK, dim=-1)
            top_ids[s:e], top_val[s:e] = i.to(torch.int32).cpu(), v.to(torch.float16).cpu()
            for row in range(s, e):
                p, L = divmod(row, n_planes)
                if not targets[p]:
                    continue
                lg = logits[row - s]
                best = min(int((lg > lg[t]).sum().item()) for t in targets[p])
                key = f"{order[p]['item_id']}_{order[p]['lang']}"
                ranks.setdefault(key, [None] * n_planes)[L] = best
    log(f"logit lens kész {time.time() - t0:.0f}s alatt")

    top_ids = top_ids.reshape(N, n_planes, TOPK).numpy()
    top_val = top_val.reshape(N, n_planes, TOPK).numpy()
    np.savez_compressed(RES / f"lens_top{sfx}.npz", ids=top_ids, logits=top_val)
    (RES / f"lens_index{sfx}.json").write_text(json.dumps(order, ensure_ascii=False), encoding="utf-8")

    # ⛔ BYTE-SZINTŰ BPE: a `convert_ids_to_tokens` a NYERS BPE-alakot adja, amiben a nem-ASCII
    # karakterek Latin-1 helyettesítőkként jelennek meg (`ä¸Ń` = 中, `ĠWÃ¼nsche` = " Wünsche").
    # Erre a nyelvosztályozó vak lenne — 0 CJK tokent találna. A `decode` adja a valódi szöveget;
    # a nyers alakot is megtartjuk, mert a szóköz-jelölő (Ġ) abból látszik.
    uniq = sorted({int(x) for x in np.unique(top_ids)})
    (RES / f"lens_vocab{sfx}.json").write_text(json.dumps(
        {str(i): {"piece": tok.convert_ids_to_tokens(i), "text": tok.decode([i])} for i in uniq},
        ensure_ascii=False), encoding="utf-8")
    (RES / f"lens_rank{sfx}.json").write_text(json.dumps(ranks, ensure_ascii=False), encoding="utf-8")
    log(f"KÉSZ — {N} prompt · {len(uniq)} különböző token a top-{TOPK}-ban · rang {len(ranks)} promptra")

    hits = 0
    for p, m in enumerate(metas):
        first_gen = tok(m["text"][:20], add_special_tokens=False)["input_ids"]
        if first_gen and int(top_ids[p, -1, 0]) == first_gen[0]:
            hits += 1
    log(f"józansági jel: az utolsó réteg top-1 tokene {hits}/{N} promptnál egyezik a generált szöveg elejével "
        f"(a generálás előtt whitespace/újsor is jöhet, ezért ez nem 100%)")


if __name__ == "__main__":
    main()
