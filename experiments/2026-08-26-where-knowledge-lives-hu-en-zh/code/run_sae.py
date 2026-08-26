#!/usr/bin/env python3
"""Fázis 1/b — SAE-kódolás a mentett residualokból, RÉTEGENKÉNT STREAMELVE.

    bash ~/lang-study/src/run_spark.sh src/run_sae.py              # mind a 32 réteg
    bash ~/lang-study/src/run_spark.sh src/run_sae.py --layers 0,15,31

Miért külön script és miért rétegenként? Mert az SAE **mind a 32 rétegre** létezik
(fázis 0 lelete), és egy checkpoint 2,15 GB fp32 — a 32 együtt 68,7 GB, ami se GPU-ra,
se kényelmesen RAM-ba nem fér. Ezért a külső ciklus a RÉTEG, a belső a 258 prompt:
egyszerre egy `layer{L}.sae.pt` van betöltve, és egyetlen mátrixszorzás fut a réteg
ÖSSZES tokenjére.

Képlet (a hivatalos SAE-README szerint, fázis 0-ban ellenőrizve):
    f = TopK₅₀(x @ W_enc.T + b_enc)          — `x − b_dec` kivonás NINCS benne

Kimenet promptonként: results/sae/{item}_{lang}.npz
    idx  [32, T, 50] int32   — az aktív feature-ök indexei rétegenként, tokenenként
    val  [32, T, 50] float16 — a hozzájuk tartozó aktivációk
    layers [32] int32, n_tokens, item_id, lang
Az „utolsó prompt-token" (elsődleges elemzés) = idx[:, -1, :]; a token-unió (másodlagos)
ugyanebből a tömbből jön, külön futás nélkül.

⚠️ A residualokat fp16-ban mentettük (run.py) — a TopK kiválasztás holtversenynél
elvben billenhet. A kvantálási hiba nagyságrendekkel kisebb, mint a feature-értékek
szórása, de a módszertanban ezt egy mondattal jelezni kell.
"""
import argparse
import json
import pathlib
import time

import numpy as np
import torch
from huggingface_hub import hf_hub_download
import scope_paths


SAE_REPO = "Qwen/SAE-Res-Qwen3.5-9B-Base-W64K-L0_50"
K = 50
ROOT = pathlib.Path("/work")
RES = scope_paths.res(ROOT)
CHUNK = 2048          # tokenek egy mátrixszorzásban — a [chunk, 65536] fp32 puffer miatt


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="", help="vesszős rétegszámok (üres = mind a 32)")
    ap.add_argument("--limit", type=int, default=0, help="csak az első N prompt (próbakör)")
    args = ap.parse_args()

    (RES / "sae").mkdir(parents=True, exist_ok=True)
    metas = [json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        metas = metas[: args.limit]

    # ── a promptok tokenjeinek egyetlen közös indexe ─────────────────────────
    items, offs, total = [], [], 0
    for m in metas:
        f = RES / "hidden" / f"{m['item_id']}_{m['lang']}.npy"
        if not f.exists():
            raise SystemExit(f"hiányzó residual: {f} — előbb a run.py")
        shape = np.load(f, mmap_mode="r").shape          # [33, T, d]
        items.append({"meta": m, "file": f, "T": shape[1]})
        offs.append(total)
        total += shape[1]
    n_planes = np.load(items[0]["file"], mmap_mode="r").shape[0]
    layers = [int(x) for x in args.layers.split(",") if x != ""] or list(range(n_planes - 1))
    log(f"{len(items)} prompt · {total} token összesen · {len(layers)} réteg · "
        f"kimenet {len(items)} db .npz")

    # promptonkénti gyűjtő: [n_layer, T, K]
    lay_pos = {L: i for i, L in enumerate(layers)}
    buf_idx = [np.zeros((len(layers), it["T"], K), dtype=np.int32) for it in items]
    buf_val = [np.zeros((len(layers), it["T"], K), dtype=np.float16) for it in items]

    for L in layers:
        t0 = time.time()
        path = hf_hub_download(SAE_REPO, f"layer{L}.sae.pt", local_files_only=True)
        sae = torch.load(path, map_location="cpu")
        W_enc = sae["W_enc"].float().cuda()               # [65536, 4096]
        b_enc = sae["b_enc"].float().cuda()
        del sae

        # a réteg összes tokenje egy tenzorban: [total, 4096]
        X = torch.empty((total, W_enc.shape[1]), dtype=torch.float32, device="cuda")
        for it, off in zip(items, offs):
            plane = np.load(it["file"], mmap_mode="r")[L + 1]     # [0]=embedding, [L+1]=resid_post(L)
            X[off: off + it["T"]] = torch.from_numpy(np.asarray(plane, dtype=np.float32)).cuda()

        all_idx = torch.empty((total, K), dtype=torch.int32, device="cuda")
        all_val = torch.empty((total, K), dtype=torch.float32, device="cuda")
        with torch.no_grad():
            for s in range(0, total, CHUNK):
                e = min(s + CHUNK, total)
                pre = X[s:e] @ W_enc.T + b_enc
                v, i = pre.topk(K, dim=-1)
                all_val[s:e], all_idx[s:e] = v, i.to(torch.int32)
        idx_cpu, val_cpu = all_idx.cpu().numpy(), all_val.cpu().numpy()

        pos = lay_pos[L]
        for j, (it, off) in enumerate(zip(items, offs)):
            buf_idx[j][pos] = idx_cpu[off: off + it["T"]]
            buf_val[j][pos] = val_cpu[off: off + it["T"]].astype(np.float16)

        del X, W_enc, b_enc, all_idx, all_val
        torch.cuda.empty_cache()
        log(f"réteg {L:2d} kész — {time.time() - t0:.1f}s (aktív/token = {K})")

    for j, it in enumerate(items):
        m = it["meta"]
        np.savez_compressed(RES / "sae" / f"{m['item_id']}_{m['lang']}.npz",
                            idx=buf_idx[j], val=buf_val[j], layers=np.array(layers, dtype=np.int32),
                            n_tokens=np.int32(it["T"]), item_id=m["item_id"], lang=m["lang"], k=np.int32(K))
    log(f"KÉSZ — {len(items)} .npz a results/sae/-ben")

    # gyors józansági ellenőrzés: az utolsó token feature-halmaza nyelvenként ne legyen azonos
    probe = next((m for m in metas if m["kind"] == "fact"), None)
    if probe:
        sets = {}
        for lang in ("hu", "en", "zh"):
            f = RES / "sae" / f"{probe['item_id']}_{lang}.npz"
            if f.exists():
                z = np.load(f, allow_pickle=True)
                mid = len(layers) // 2
                sets[lang] = set(z["idx"][mid, -1].tolist())
        if len(sets) == 3:
            jac = lambda a, b: len(a & b) / len(a | b)
            log(f"{probe['item_id']} középső réteg, utolsó token — J(zh,en)={jac(sets['zh'], sets['en']):.3f} "
                f"J(zh,hu)={jac(sets['zh'], sets['hu']):.3f} J(en,hu)={jac(sets['en'], sets['hu']):.3f}")


if __name__ == "__main__":
    main()
