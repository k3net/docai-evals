#!/usr/bin/env python3
"""SAE-kapu: mennyire illik a BASE-en tanult SAE a mért residualokra.

    bash src/run_spark.sh src/sae_fvu.py                                   # base kör
    SCOPE_RES=results_instruct bash src/run_spark.sh src/sae_fvu.py        # instruct kör

⛔ MIÉRT KELL: a `SAE-Res-Qwen3.5-9B-Base-W64K-L0_50` a BASE modell residualjain tanult.
A 2. körben (`Qwen/Qwen3.5-9B`, post-trainelt) ugyanezt az SAE-t használnánk — a
reprezentációtér közel van, de nem azonos. Ha a rekonstrukció érdemben romlik, akkor a
Mérés C instruct-változata nem a nyelvi szerveződést mérné, hanem azt, hogy az SAE
mennyire téved. Ezt tehát MÉRJÜK, nem feltételezzük.

Mérőszám rétegenként (a prompt-tokenek teljes halmazán):
    x̂    = TopK₅₀(x @ W_encᵀ + b_enc) @ W_decᵀ + b_dec
    FVU  = ‖x − x̂‖² / ‖x − x̄‖²      (0 = tökéletes, 1 = annyit ér, mint az átlag)
    cos  = a rekonstrukció és az eredeti átlagos koszinusz-hasonlósága

Kimenet: <SCOPE_REPORTS>/06_sae_fvu.json (+ konzol). A két kör JSON-ját a
`--compare <masik.json>` kapcsolóval hasonlítja össze.
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
OUT = scope_paths.reports(ROOT)
CHUNK = 2048


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--layers", default="", help="vesszős rétegszámok (üres = mind)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--span", action="store_true",
                    help="csak a kérdés token-tartománya (q_tok_span) — a chat-sablon "
                         "burkolata nélkül; a két kör így hasonlítható össze tisztán")
    ap.add_argument("--compare", default="", help="egy másik kör 06_sae_fvu.json-ja")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    metas = [json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limit:
        metas = metas[: args.limit]

    # ⛔ A base kör gen.jsonl-jében NINCS q_tok_span (a mező később került a run.py-ba), ott a
    # dump_tokens.py által írt prompt_q_span.json az igazságforrás. Enélkül a `--span` némán a
    # TELJES promptot (BOS + keret) mérte — 2026-08-26-án ez adta a hamis 0,44-es base FVU-t.
    span_file = RES / "prompt_q_span.json"
    spans = json.loads(span_file.read_text(encoding="utf-8")) if span_file.exists() else {}
    items, offs, total = [], [], 0
    n_fallback = 0
    for m in metas:
        f = RES / "hidden" / f"{m['item_id']}_{m['lang']}.npy"
        if not f.exists():
            raise SystemExit(f"hiányzó residual: {f}")
        T = np.load(f, mmap_mode="r").shape[1]
        if args.span:
            sp = m.get("q_tok_span") or spans.get(f"{m['item_id']}_{m['lang']}")
            if not sp:
                raise SystemExit(f"nincs kérdés-tartomány ehhez: {m['item_id']}_{m['lang']} — futtasd a dump_tokens.py-t")
            if not m.get("q_tok_span"):
                n_fallback += 1
            lo, hi = sp
        else:
            lo, hi = 0, T
        items.append({"file": f, "lo": lo, "hi": hi, "n": hi - lo, "lang": m["lang"]})
        offs.append(total)
        total += hi - lo
    n_planes = np.load(items[0]["file"], mmap_mode="r").shape[0]
    layers = [int(x) for x in args.layers.split(",") if x != ""] or list(range(n_planes - 1))
    log(f"{len(items)} prompt · {total} token · {len(layers)} réteg · "
        f"tartomány: {'kérdés' if args.span else 'teljes prompt'}"
        + (f" (prompt_q_span.json-ból: {n_fallback})" if n_fallback else ""))

    rows = []
    for L in layers:
        t0 = time.time()
        sae = torch.load(hf_hub_download(SAE_REPO, f"layer{L}.sae.pt", local_files_only=True),
                         map_location="cpu")
        W_enc, b_enc = sae["W_enc"].float().cuda(), sae["b_enc"].float().cuda()
        W_dec, b_dec = sae["W_dec"].float().cuda(), sae["b_dec"].float().cuda()
        del sae

        X = torch.empty((total, W_enc.shape[1]), dtype=torch.float32, device="cuda")
        for it, off in zip(items, offs):
            plane = np.load(it["file"], mmap_mode="r")[L + 1][it["lo"]: it["hi"]]
            X[off: off + it["n"]] = torch.from_numpy(np.asarray(plane, dtype=np.float32)).cuda()

        mean = X.mean(0, keepdim=True)
        sse = torch.zeros((), device="cuda", dtype=torch.float64)
        cos_sum = torch.zeros((), device="cuda", dtype=torch.float64)
        with torch.no_grad():
            for s in range(0, total, CHUNK):
                e = min(s + CHUNK, total)
                x = X[s:e]
                v, i = (x @ W_enc.T + b_enc).topk(K, dim=-1)
                f = torch.zeros((e - s, W_enc.shape[0]), device="cuda", dtype=torch.float32)
                f.scatter_(1, i, v)
                xh = f @ W_dec.T + b_dec
                sse += (x - xh).pow(2).sum().double()
                cos_sum += torch.nn.functional.cosine_similarity(x, xh, dim=-1).sum().double()
            sst = (X - mean).pow(2).sum().double()
        fvu = float(sse / sst)
        rows.append({"layer": L, "fvu": round(fvu, 4), "ev": round(1 - fvu, 4),
                     "cos": round(float(cos_sum / total), 4)})
        log(f"  réteg {L:2d}: FVU {fvu:.4f} · magyarázott variancia {1-fvu:.4f} · "
            f"cos {float(cos_sum/total):.4f}  ({time.time()-t0:.0f}s)")
        del X, W_enc, b_enc, W_dec, b_dec
        torch.cuda.empty_cache()

    res = {"model": scope_paths.MODEL, "res_dir": str(RES), "span_only": args.span,
           "tokens": total, "layers": rows,
           "fvu_mean": round(float(np.mean([r["fvu"] for r in rows])), 4),
           "fvu_max": round(float(max(r["fvu"] for r in rows)), 4)}
    p = OUT / ("06_sae_fvu_span.json" if args.span else "06_sae_fvu.json")
    p.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"KÉSZ — átlagos FVU {res['fvu_mean']} · legrosszabb réteg {res['fvu_max']} → {p}")

    if args.compare:
        other = json.loads(pathlib.Path(args.compare).read_text(encoding="utf-8"))
        om = {r["layer"]: r for r in other["layers"]}
        diffs = [rr["fvu"] - om[rr["layer"]]["fvu"] for rr in rows if rr["layer"] in om]
        worst = max(((rr["fvu"] - om[rr["layer"]]["fvu"], rr["layer"]) for rr in rows if rr["layer"] in om))
        log(f"összevetés {other['model']} ellen: átlagos FVU-romlás {np.mean(diffs):+.4f} · "
            f"legrosszabb {worst[0]:+.4f} a {worst[1]}. rétegen")
        log("⚠️ Ha a romlás a 0,05-öt meghaladja, a Mérés C instruct-változatát csak "
            "kvalitatívan szabad olvasni — írd bele a módszertanba.")


if __name__ == "__main__":
    main()
