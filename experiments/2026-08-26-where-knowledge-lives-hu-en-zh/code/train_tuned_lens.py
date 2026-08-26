#!/usr/bin/env python3
"""Tuned lens tanítása (spark-dev, konténer) — a Mérés B fő ábrájának rehabilitálása.

    bash ~/lang-study/code/run_spark.sh code/train_tuned_lens.py

⛔ MIÉRT: a Mérés B kimutatta, hogy a NAIV logit lens ezen a modellen a 0–23. rétegen
olvashatatlan (a top-20 84 %-a nem szó). Ez ismert jelenség: a köztes residual nem esik
egybe az unembedding terével. A megoldás (Belrose et al. 2023): rétegenként egy TANULT
affin fordító, ami a köztes residualt a végső residual terébe viszi.

    p_ℓ = softmax( RMSNorm( A_ℓ · h_ℓ + b_ℓ ) · W_Uᵀ )      cél: KL(p_végső ‖ p_ℓ) minimum

⚠️ Eltérés a cikktől, és miért: ott ~250M tokenen tanítanak TELJES rangú A-t. Nekünk
~200k tokenünk van (kiegyensúlyozott hu/en/zh Wikipédia), ezért A = I + U·V ALACSONY
RANGÚ korrekció (alapból r=256, rétegenként 2,1M paraméter a 16,7M helyett) + súlycsökkentés
+ validációs korai megállítás. A cél nem tökéletes lens, hanem annak eldöntése, hogy a
KÖZÉPSŐ rétegek olvashatóvá válnak-e.

⚠️ A fordító I-ből indul (U=0), tehát a tanítás kezdőpontja PONTOSAN a naiv lens — a
javulás így közvetlenül a tanulás érdeme, nem az inicializálásé.

Kimenet: <SCOPE_RES>/tuned_lens.pt (fordítók + rétegenkénti KL előtte/utána) + logs
"""
import argparse
import glob
import json
import pathlib
import time

import numpy as np
import torch
import torch.nn.functional as F
from safetensors import safe_open
from transformers import AutoModelForCausalLM, AutoTokenizer

import gb10_patch
import scope_paths

MODEL = scope_paths.MODEL
ROOT = pathlib.Path("/work")
RES = scope_paths.res(ROOT)
EPS = 1e-6


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def load_unembed():
    snap = glob.glob(str(ROOT / "hf/hub/models--Qwen--Qwen3.5-9B-Base/snapshots/*/model.safetensors.index.json"))[0]
    base = pathlib.Path(snap).parent
    wmap = json.load(open(snap))["weight_map"]
    out = {}
    for key in ("lm_head.weight", "model.language_model.norm.weight"):
        with safe_open(base / wmap[key], framework="pt") as f:
            out[key] = f.get_tensor(key)
    return out["lm_head.weight"], out["model.language_model.norm.weight"]


def build_cache(args, tok):
    """[33, N, d] fp16 memmap a korpusz tokenjeinek residualjaiból."""
    cache_f = RES / "lens_cache.npy"
    meta_f = RES / "lens_cache.json"
    if cache_f.exists() and meta_f.exists() and not args.rebuild:
        meta = json.load(open(meta_f))
        log(f"cache megvan: {meta['shape']} ({meta['tokens']:,} token)")
        return np.load(cache_f, mmap_mode="r"), meta

    gb10_patch.patch(conv=True)
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda").eval()
    stack = model.model.layers
    n_layers = len(stack)
    d = model.config.text_config.hidden_size if hasattr(model.config, "text_config") else model.config.hidden_size

    docs = [json.loads(l) for l in (ROOT / "data" / "lens_corpus.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    # ⛔ A minimális szakaszhossz NYELVFÜGGŐ SZŰRŐ volt, amíg seqlen//2 (=256 token) volt:
    # a Wikipédia-API 1200 karakterben vágja a kivonatot, és ugyanaz az 1200 karakter angolul
    # ~300, magyarul ~460, kínaiul ~800 token. Így az angol cikkek nagy része kiesett, és a
    # tanítókorpusz 15 % angol / 40 % magyar / 44 % kínai lett — pont abban a dimenzióban
    # elfogult, amit a dolgozat mér. Az alacsony, MINDEN nyelv által elért küszöb ezt megszünteti.
    seqs, langs = [], []
    drop = {}
    for doc in docs:
        ids = tok(doc["text"], add_special_tokens=False)["input_ids"]
        kept = 0
        for s in range(0, len(ids), args.seqlen):
            chunk = ids[s: s + args.seqlen]
            if len(chunk) >= args.min_chunk:
                seqs.append(chunk)
                langs.append(doc["lang"])
                kept += 1
        if not kept:
            drop[doc["lang"]] = drop.get(doc["lang"], 0) + 1
    log(f"{len(docs)} cikk → {len(seqs)} szakasz ({sum(len(s) for s in seqs):,} token) "
        f"· min_chunk={args.min_chunk} · kiesett cikk {drop}")
    avail = {}
    for sq, lg in zip(seqs, langs):
        avail[lg] = avail.get(lg, 0) + len(sq)
    log("elérhető token/nyelv: " + " · ".join(f"{k} {v:,}" for k, v in sorted(avail.items())))

    # ⛔ TOKEN-alapú kiegyensúlyozás: a korpuszban a nyelvek egymás után állnak, és a
    # magyar/angol cikkek hosszabbak — sorrendben feltöltve a cache szinte csak magyar lenne.
    # Körbejárva vesszük a nyelveket, és mindegyik legfeljebb N/3 tokent adhat, különben a
    # tuned lens fordítói maguk lennének nyelvileg elfogultak.
    by_lang = {}
    for sq, lg in zip(seqs, langs):
        by_lang.setdefault(lg, []).append(sq)
    order, budget = [], {lg: 0 for lg in by_lang}
    N = min(args.tokens, sum(len(s) for s in seqs))
    cap = N // len(by_lang)
    pos_in = {lg: 0 for lg in by_lang}
    while sum(budget.values()) < N:
        progressed = False
        for lg in sorted(by_lang):
            if budget[lg] >= cap or pos_in[lg] >= len(by_lang[lg]):
                continue
            sq = by_lang[lg][pos_in[lg]]
            pos_in[lg] += 1
            order.append((sq, lg))
            budget[lg] += len(sq)
            progressed = True
        if not progressed:
            break
    seqs = [o[0] for o in order]
    langs = [o[1] for o in order]
    log(f"kiegyensúlyozva: " + " · ".join(f"{lg} {b:,} token" for lg, b in sorted(budget.items())))
    share = {lg: b / max(1, sum(budget.values())) for lg, b in budget.items()}
    if max(share.values()) - min(share.values()) > 0.05:
        log(f"⚠️  A nyelvi arányok NEM kiegyensúlyozottak ({share}) — valamelyik nyelv kifogyott. "
            f"Tölts utána: python3 code/fetch_lens_corpus.py --append --lang <nyelv> --batches 60")
    N = min(N, sum(len(s) for s in seqs))
    arr = np.lib.format.open_memmap(cache_f, mode="w+", dtype=np.float16, shape=(n_layers + 1, N, d))
    captured = {}
    hooks = [l.register_forward_hook(
        lambda m, i, o, k=k: captured.__setitem__(k, (o[0] if isinstance(o, tuple) else o).detach()))
        for k, l in enumerate(stack)]

    pos, used_langs = 0, []
    t0 = time.time()
    for si, seq in enumerate(seqs):
        if pos >= N:
            break
        ids = torch.tensor([seq], device="cuda")
        with torch.no_grad():
            out = model(input_ids=ids, output_hidden_states=True)
        planes = [out.hidden_states[0][0]] + [captured[i][0] for i in range(n_layers)]
        block = torch.stack(planes).to(torch.float16).cpu().numpy()          # [33, T, d]
        take = min(block.shape[1], N - pos)
        arr[:, pos: pos + take] = block[:, :take]
        used_langs += [langs[si]] * take
        pos += take
        if si % 25 == 0:
            log(f"  cache {pos:,}/{N:,} token ({time.time() - t0:.0f}s)")
    for h in hooks:
        h.remove()
    arr.flush()
    from collections import Counter
    meta = {"tokens": int(pos), "shape": list(arr.shape), "langs": dict(Counter(used_langs)),
            "seqlen": args.seqlen, "min_chunk": args.min_chunk, "langs_per_pos": used_langs}
    json.dump(meta, open(meta_f, "w"), ensure_ascii=False, indent=1)
    log(f"cache kész: {pos:,} token · nyelvi eloszlás {meta['langs']}")
    del model
    torch.cuda.empty_cache()
    return np.load(cache_f, mmap_mode="r"), meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tokens", type=int, default=200_000)
    ap.add_argument("--seqlen", type=int, default=512)
    ap.add_argument("--min-chunk", type=int, default=128,
                    help="minimális szakaszhossz tokenben — MINDEN nyelv érje el, különben nyelvfüggő szűrő")
    ap.add_argument("--rank", type=int, default=256, help="0 = teljes rangú A")
    ap.add_argument("--steps", type=int, default=400)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--val-frac", type=float, default=0.1)
    ap.add_argument("--rebuild", action="store_true")
    args = ap.parse_args()

    torch.manual_seed(0)
    tok = AutoTokenizer.from_pretrained(MODEL)
    cache, meta = build_cache(args, tok)
    n_planes, N, d = cache.shape

    W_U, norm_w = load_unembed()
    W_U = W_U.to("cuda", torch.bfloat16).T.contiguous()
    norm_w = norm_w.to("cuda", torch.float32)

    def lens_logits(h):
        x = h.float()
        x = x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + EPS) * norm_w
        return (x.to(torch.bfloat16) @ W_U).float()

    # ⛔ A val-halmaz NEM lehet a cache vége: a nyelvek körbejárva töltődnek, és amelyik
    # nyelv előbb kifogy, az a farokból hiányzik — a validáció így nyelvileg torz lenne.
    # Rögzített magú permutáció: a val-halmaz nyelvi összetétele a teljes cache-t követi.
    perm = torch.randperm(N, generator=torch.Generator().manual_seed(0))
    n_val = int(N * args.val_frac)
    idx_val, idx_tr = perm[:n_val], perm[n_val:]
    cl = meta.get("langs_per_pos")
    if cl:
        from collections import Counter
        vc = Counter(cl[i] for i in idx_val.tolist())
        log("val-halmaz nyelvi eloszlása: " + " · ".join(f"{k} {v:,}" for k, v in sorted(vc.items())))

    final = torch.from_numpy(np.asarray(cache[n_planes - 1])).cuda()          # [N, d]
    log(f"tanítás: {len(idx_tr):,} train / {len(idx_val):,} val token · rang {args.rank or 'teljes'}")

    result = {"rank": args.rank, "steps": args.steps, "tokens": int(N),
              "langs": meta["langs"], "layers": []}
    U_all, V_all, B_all = [], [], []

    for L in range(n_planes - 1):                    # az utolsó sík önmaga = identitás
        h_all = torch.from_numpy(np.asarray(cache[L])).cuda()
        if args.rank:
            U = torch.zeros(d, args.rank, device="cuda", requires_grad=True)
            V = torch.zeros(args.rank, d, device="cuda")
            torch.nn.init.normal_(V, std=0.02)
            V.requires_grad_(True)
        else:
            U = torch.zeros(d, d, device="cuda", requires_grad=True)
            V = None
        b = torch.zeros(d, device="cuda", requires_grad=True)
        params = [U, b] + ([V] if V is not None else [])
        opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=args.wd)

        def translate(h):
            delta = (h.float() @ U) @ V if V is not None else h.float() @ U
            return h.float() + delta + b

        @torch.no_grad()
        def val_kl(use_translator):
            tot, n = 0.0, 0
            for s in range(0, len(idx_val), args.batch):
                ii = idx_val[s: s + args.batch].cuda()
                h = h_all[ii]
                lg = lens_logits(translate(h) if use_translator else h)
                tgt = lens_logits(final[ii])
                tot += F.kl_div(F.log_softmax(lg, -1), F.log_softmax(tgt, -1),
                                reduction="batchmean", log_target=True).item() * len(ii)
                n += len(ii)
            return tot / n

        kl0 = val_kl(False)
        best, best_state, patience = float("inf"), None, 0
        for step in range(args.steps):
            ii = idx_tr[torch.randint(0, len(idx_tr), (args.batch,))].cuda()
            h = h_all[ii]
            lg = lens_logits(translate(h))
            with torch.no_grad():
                tgt = F.log_softmax(lens_logits(final[ii]), -1)
            loss = F.kl_div(F.log_softmax(lg, -1), tgt, reduction="batchmean", log_target=True)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            if (step + 1) % 100 == 0:
                v = val_kl(True)
                if v < best - 1e-4:
                    best, patience = v, 0
                    best_state = [p.detach().clone() for p in params]
                else:
                    patience += 1
                    if patience >= 2:
                        break
        if best_state is not None:
            with torch.no_grad():
                for p, q in zip(params, best_state):
                    p.copy_(q)
        kl1 = val_kl(True)
        result["layers"].append({"layer": L, "kl_identity": round(kl0, 4), "kl_tuned": round(kl1, 4),
                                 "javulas": round(kl0 - kl1, 4)})
        log(f"  sík {L:2d}: KL {kl0:.3f} → {kl1:.3f}  (−{kl0 - kl1:.3f})")
        U_all.append(U.detach().cpu())
        V_all.append(V.detach().cpu() if V is not None else torch.empty(0))
        B_all.append(b.detach().cpu())
        del h_all
        torch.cuda.empty_cache()

    torch.save({"U": torch.stack(U_all), "V": torch.stack(V_all) if args.rank else None,
                "b": torch.stack(B_all), "rank": args.rank, "meta": result}, RES / "tuned_lens.pt")
    (RES / "tuned_lens_report.json").write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    mean0 = np.mean([l["kl_identity"] for l in result["layers"]])
    mean1 = np.mean([l["kl_tuned"] for l in result["layers"]])
    log(f"KÉSZ — átlagos KL {mean0:.3f} → {mean1:.3f} · → {RES.name}/tuned_lens.pt "
        f"(modell: {MODEL})")


if __name__ == "__main__":
    main()
