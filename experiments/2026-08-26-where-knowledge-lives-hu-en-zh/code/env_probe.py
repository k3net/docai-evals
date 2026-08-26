#!/usr/bin/env python3
"""Fázis 0 — környezet-felmérés a spark-deven, konténerből futtatva.

    bash ~/lang-study/code/run_spark.sh code/env_probe.py --sae-layers 0,15,31

Amit lemér (a runbook §0 kötelező kimenete):
  1. rétegszám, hidden dim, vocab, modellosztály, a dekóder-verem elérési útja
  2. tokenhossz-tábla mind a 258 promptra, csoport x nyelv bontásban
  3. hook(resid_post) vs. output_hidden_states egyezés rétegenként
     — ⛔ ez dönti el, hogy a logit lensnél hol kell (és hol NEM szabad) a
     záró RMSNorm-ot alkalmazni; a HF a hidden_states UTOLSÓ elemére már
     ráengedi a final normot, a többire nem
  4. smoke: 3 prompt (hu/en/zh) greedy generálás
  5. SAE: kulcsok, alakok, TopK-ellenőrzés és rekonstrukciós hiba
     — a rekonstrukciós hiba a hook-pont bizonyítéka: rossz tenzoron nagy

Kimenet: reports/00_env.json + reports/00_token_lengths.csv (+ konzol).
"""
import argparse
import csv
import json
import pathlib

import scope_paths
import statistics
import sys
import time

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

import gb10_patch

MODEL = "Qwen/Qwen3.5-9B-Base"
SAE_REPO = "Qwen/SAE-Res-Qwen3.5-9B-Base-W64K-L0_50"
ROOT = pathlib.Path("/work")

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ── 1. config ────────────────────────────────────────────────────────────────
def probe_config(env):
    cfg = AutoConfig.from_pretrained(MODEL)
    text = getattr(cfg, "text_config", cfg)
    env["model"] = {
        "repo": MODEL,
        "architectures": cfg.architectures,
        "model_type": cfg.model_type,
        "num_hidden_layers": text.num_hidden_layers,
        "hidden_size": text.hidden_size,
        "vocab_size": text.vocab_size,
        "head_dim": getattr(text, "head_dim", None),
        "rms_norm_eps": getattr(text, "rms_norm_eps", None),
        "max_position_embeddings": getattr(text, "max_position_embeddings", None),
        "layer_types_unique": sorted(set(getattr(text, "layer_types", []) or [])),
        "full_attention_interval": getattr(text, "full_attention_interval", None),
    }
    log(f"config: {cfg.architectures} L={text.num_hidden_layers} d={text.hidden_size} V={text.vocab_size}")
    return cfg


# ── 2. tokenhossz-tábla ──────────────────────────────────────────────────────
def probe_tokens(env, tok):
    prompts = [json.loads(l) for l in scope_paths.data(ROOT, "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = []
    for p in prompts:
        n = len(tok(p["prompt"])["input_ids"])
        rows.append({"item_id": p["item_id"], "group": p["group"], "kind": p["kind"],
                     "lang": p["lang"], "n_tokens": n})
    out = ROOT / "reports" / "00_token_lengths.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["item_id", "group", "kind", "lang", "n_tokens"])
        w.writeheader()
        w.writerows(rows)

    table = {}
    for kind_key in sorted({(r["group"], r["kind"]) for r in rows}):
        for lang in ("hu", "en", "zh"):
            ns = [r["n_tokens"] for r in rows
                  if (r["group"], r["kind"]) == kind_key and r["lang"] == lang]
            table[f"{kind_key[0]}/{kind_key[1]}/{lang}"] = {
                "n": len(ns), "mean": round(statistics.mean(ns), 1),
                "median": statistics.median(ns), "max": max(ns),
            }
    env["prompts"] = {"count": len(prompts), "token_lengths": table}
    log(f"tokenhossz-tábla kész: {len(prompts)} prompt → {out}")

    print("\n  csoport/fajta      hu      en      zh    (átlag tokenszám)")
    for gk in sorted({f"{r['group']}/{r['kind']}" for r in rows}):
        vals = [table[f"{gk}/{lg}"]["mean"] for lg in ("hu", "en", "zh")]
        print(f"  {gk:14s} {vals[0]:7.1f} {vals[1]:7.1f} {vals[2]:7.1f}")
    print()
    return prompts


# ── 3. modell + a dekóder-verem megtalálása ──────────────────────────────────
def find_stack(model, n_layers):
    """A rétegverem a multimodális wrapper alatt máshol van, mint a README-ben
    (`model.model.layers`). Nem tippelünk: megkeressük azt a ModuleList-et,
    aminek pont annyi eleme van, ahány réteg."""
    for name, mod in model.named_modules():
        if isinstance(mod, torch.nn.ModuleList) and len(mod) == n_layers:
            return name, mod
    raise RuntimeError(f"nem találom a {n_layers} elemű rétegvermet")


def probe_model(env, tok, prompts, args):
    # ⛔ GB10: a causal_conv1d kernel szegmenshibával megöli a folyamatot — ld. gb10_patch
    env["gb10_patch"] = gb10_patch.patch(conv=True, fla=False)
    log("modell betöltése (bf16, cuda) …")
    t0 = time.time()
    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map="cuda")
    model.eval()
    log(f"betöltve {time.time() - t0:.0f}s alatt — {type(model).__name__}")

    n_layers = env["model"]["num_hidden_layers"]
    stack_name, stack = find_stack(model, n_layers)
    parent = model.get_submodule(stack_name.rsplit(".", 1)[0])
    norm_name = next((f"{stack_name.rsplit('.', 1)[0]}.{a}" for a in ("norm", "final_layernorm")
                      if hasattr(parent, a)), None)
    head = model.get_output_embeddings()
    env["paths"] = {
        "class": type(model).__name__,
        "layer_stack": stack_name,
        "final_norm": norm_name,
        "lm_head_shape": list(head.weight.shape) if head is not None else None,
        "tied_embeddings": bool(getattr(model.config, "tie_word_embeddings", False)),
    }
    log(f"rétegverem: {stack_name} | final norm: {norm_name} | lm_head: {env['paths']['lm_head_shape']}")

    # ── 3/a. hook vs hidden_states ───────────────────────────────────────────
    probe = next(p for p in prompts if p["lang"] == "en" and p["kind"] == "fact")
    enc = tok(probe["prompt"], return_tensors="pt").to(model.device)

    captured = {}
    hooks = []
    for i, layer in enumerate(stack):
        hooks.append(layer.register_forward_hook(
            lambda m, inp, out, i=i: captured.__setitem__(
                i, (out[0] if isinstance(out, tuple) else out).detach().float().cpu())))
    with torch.no_grad():
        out = model(**enc, output_hidden_states=True)
    for h in hooks:
        h.remove()

    hs = [h.detach().float().cpu() for h in out.hidden_states]
    diffs = []
    for i in range(n_layers):
        if i + 1 < len(hs):
            d = (captured[i] - hs[i + 1]).abs().max().item()
            diffs.append({"layer": i, "max_abs_diff_hook_vs_hidden": round(d, 6)})
    env["hidden_states"] = {
        "len": len(hs),
        "expected_len": n_layers + 1,
        "per_layer": diffs,
        "last_entry_is_normed": diffs[-1]["max_abs_diff_hook_vs_hidden"] > 1e-2 if diffs else None,
        "note": ("hidden_states[i+1] == resid_post(i) az utolsó kivételével; az "
                 "utolsóra a HF már ráengedte a záró RMSNormot"),
    }
    bad = [d for d in diffs[:-1] if d["max_abs_diff_hook_vs_hidden"] > 1e-2]
    log(f"hook vs hidden_states: {len(hs)} elem, eltérő rétegek (utolsó nélkül): {len(bad)}, "
        f"utolsó eltérés = {diffs[-1]['max_abs_diff_hook_vs_hidden']}")

    # ⛔ a klasszikus indexelési hiba: mindhárom nyelv ugyanazt a vektort adja
    tri = {}
    for lang in ("hu", "en", "zh"):
        p = next(x for x in prompts if x["item_id"] == probe["item_id"] and x["lang"] == lang)
        e = tok(p["prompt"], return_tensors="pt").to(model.device)
        with torch.no_grad():
            o = model(**e, output_hidden_states=True)
        tri[lang] = o.hidden_states[16][0, -1].float().cpu()
    env["sanity_three_langs"] = {
        "item": probe["item_id"],
        "cos_hu_en": round(torch.nn.functional.cosine_similarity(tri["hu"], tri["en"], dim=0).item(), 4),
        "cos_hu_zh": round(torch.nn.functional.cosine_similarity(tri["hu"], tri["zh"], dim=0).item(), 4),
        "identical": bool(torch.equal(tri["hu"], tri["en"]) or torch.equal(tri["hu"], tri["zh"])),
    }
    log(f"három nyelv 16. réteg cos: hu-en {env['sanity_three_langs']['cos_hu_en']} "
        f"hu-zh {env['sanity_three_langs']['cos_hu_zh']} (azonos: {env['sanity_three_langs']['identical']})")

    # ── 3/b. smoke generálás ─────────────────────────────────────────────────
    torch.manual_seed(0)
    smoke = []
    for lang in ("hu", "en", "zh"):
        p = next(x for x in prompts if x["lang"] == lang and x["kind"] == "fact")
        e = tok(p["prompt"], return_tensors="pt").to(model.device)
        with torch.no_grad():
            g = model.generate(**e, max_new_tokens=60, do_sample=False,
                               pad_token_id=tok.pad_token_id or tok.eos_token_id)
        txt = tok.decode(g[0][e["input_ids"].shape[1]:], skip_special_tokens=True)
        smoke.append({"item_id": p["item_id"], "lang": lang, "expected": p["expected"], "generated": txt})
        print(f"\n  [{lang}] {p['item_id']} (várt: {p['expected']})\n  → {txt.strip()[:400]!r}")
    env["smoke"] = smoke
    print()
    return model, stack, enc


# ── 4. SAE ───────────────────────────────────────────────────────────────────
def probe_sae(env, model, stack, enc, layers):
    from huggingface_hub import hf_hub_download
    res = []
    for L in layers:
        try:
            path = hf_hub_download(SAE_REPO, f"layer{L}.sae.pt", local_files_only=True)
        except Exception as exc:  # a letöltés még futhat
            log(f"SAE layer{L}: NINCS MEG ({type(exc).__name__}) — kihagyva")
            res.append({"layer": L, "status": "missing"})
            continue
        sae = torch.load(path, map_location="cpu")
        W_enc, b_enc = sae["W_enc"].float(), sae["b_enc"].float()
        W_dec, b_dec = sae["W_dec"].float(), sae["b_dec"].float()

        captured = {}
        h = stack[L].register_forward_hook(
            lambda m, i, o: captured.__setitem__("x", (o[0] if isinstance(o, tuple) else o).detach().float().cpu()))
        with torch.no_grad():
            model(**enc)
        h.remove()
        x = captured["x"][0, -1]                       # utolsó prompt-token resid_post
        pre = x @ W_enc.T + b_enc                      # a hivatalos README képlete
        vals, idx = pre.topk(50)
        acts = torch.zeros_like(pre).scatter_(-1, idx, vals)
        recon = W_dec @ acts + b_dec
        fvu = ((x - recon).pow(2).sum() / x.pow(2).sum()).item()
        res.append({
            "layer": L, "status": "ok",
            "keys": sorted(sae.keys()),
            "W_enc": list(W_enc.shape), "W_dec": list(W_dec.shape),
            "b_enc": list(b_enc.shape), "b_dec": list(b_dec.shape),
            "n_active": int((acts != 0).sum()),
            "top5_features": [[int(i), round(float(v), 3)] for i, v in zip(idx[:5], vals[:5])],
            "recon_rel_error": round(fvu, 4),
        })
        log(f"SAE layer{L}: aktív={res[-1]['n_active']} rekonstrukciós rel. hiba={fvu:.4f} "
            f"top5={res[-1]['top5_features'][:3]}")
        del sae, W_enc, W_dec
    env["sae"] = {
        "repo": SAE_REPO, "type": "topk_sae", "d_model": 4096, "d_sae": 65536, "k": 50,
        "layers_available": "0-31 (mind a 32)", "hook_point": "resid_post",
        "encoder_formula": "f = TopK_50(x @ W_enc.T + b_enc)  — b_dec-kivonás NINCS benne",
        "checked": res,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sae-layers", default="0,15,31")
    ap.add_argument("--skip-model", action="store_true", help="csak config + tokenhossz")
    args = ap.parse_args()

    env = {"probed_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "torch": torch.__version__, "cuda": torch.version.cuda,
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "capability": list(torch.cuda.get_device_capability(0)) if torch.cuda.is_available() else None}
    import transformers
    env["transformers"] = transformers.__version__
    log(f"torch {torch.__version__} / transformers {transformers.__version__} / GPU {env['gpu']} {env['capability']}")

    probe_config(env)
    tok = AutoTokenizer.from_pretrained(MODEL)
    env["tokenizer"] = {"class": type(tok).__name__, "vocab_size": tok.vocab_size,
                        "eos": tok.eos_token, "pad": tok.pad_token}
    prompts = probe_tokens(env, tok)

    if not args.skip_model:
        model, stack, enc = probe_model(env, tok, prompts, args)
        probe_sae(env, model, stack, enc, [int(x) for x in args.sae_layers.split(",") if x != ""])

    out = ROOT / "reports" / "00_env.json"
    out.write_text(json.dumps(env, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"KÉSZ → {out}")


if __name__ == "__main__":
    sys.exit(main())
