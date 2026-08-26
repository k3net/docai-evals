#!/usr/bin/env python3
"""Fázis 1 — a 258 prompt egyetlen végigfuttatása, minden későbbi mérés alapja.

    bash ~/lang-study/code/run_spark.sh code/run.py                 # teljes futás (folytatható)
    bash ~/lang-study/code/run_spark.sh code/run.py --limit 6       # próbakör
    bash ~/lang-study/code/run_spark.sh code/run.py --only ZH01,HU01

Promptonként két menet ugyanazon a modellen:
  1. GENERÁLÁS — greedy, seed 0, `<think>` tiltva, stop-szekvenciával
     → results/gen/{item}_{lang}.txt  (+ .json a metaadatokkal)
  2. FORWARD — hook mind a 32 rétegen, a PROMPT tokenjeire
     → results/hidden/{item}_{lang}.npy, shape [33, T, 4096]
        [0]    = embedding-kimenet (a 0. réteg BEmenete)
        [L+1]  = resid_post(L), L = 0…31

⛔ Miért hook és nem `output_hidden_states`? Mert a HF az utolsó elemre (index 32)
   MÁR RÁENGEDTE a záró RMSNormot — a fázis 0 lemérte: a 0–30. rétegre bitre azonos
   a kettő, az utolsóra 119,875 az eltérés (env.md). A logit lens így épp az utolsó
   rétegeken normalizálna kétszer, a 31. réteg SAE-je pedig rossz tenzort kapna.
   A futás ezt az invariánst az ELSŐ prompton minden alkalommal újra ellenőrzi.

⛔ Miért fp16 a mentés? 258 × ~28 token × 33 réteg × 4096 × 4 byte ≈ 5,6 GB fp32-ben.
   Az fp16 feleennyi, de a késői rétegek „massive activation"-jei elvben kilóghatnak
   a ±65504-es tartományból, ezért promptonként ellenőrizzük, és ha kilóg, AZ A FÁJL
   fp32-ben megy ki (a betöltő a dtype-ból úgyis megtudja).
"""
import argparse
import json
import pathlib
import time

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import gb10_patch
import scope_paths

MODEL = scope_paths.MODEL
ROOT = pathlib.Path("/work")
RES = scope_paths.res(ROOT)

# A modell a válasz után gyakran SAJÁT kérdés-válasz párokkal folytat (fázis 0 smoke),
# ezért mindhárom nyelv nyitószavára megállunk — nem csak a prompt nyelvéére, mert
# nyelvet is válthat közben.
STOPS = ["\nKérdés:", "\nQuestion:", "\n问题："]

# A prompts.jsonl keret-szövege nyelvenként (build_prompts.py TEMPLATE-je). Ebből nyerjük
# ki a CSUPASZ kérdést, amikor a modell saját chat-sablonjával promptozunk, és ebből
# számoljuk a kérdés token-tartományát is.
QFRAME = {"hu": ("Kérdés: ", "\nVálasz:"),
          "en": ("Question: ", "\nAnswer:"),
          "zh": ("问题：", "\n回答：")}


def bare_question(p):
    pre, post = QFRAME[p["lang"]]
    t = p["prompt"]
    assert t.startswith(pre) and t.endswith(post), f"váratlan prompt-keret: {t[:40]!r}"
    return t[len(pre): len(t) - len(post)]


def build_prompt(p, tok):
    """A modellnek ténylegesen átadott szöveg + a csupasz kérdés (a token-tartományhoz).

    ⛔ MIÉRT KELL A KÉRDÉS TARTOMÁNYA: az instruct modellnél a prompt a chat-sablon
    burkolatát is tartalmazza (`<|im_start|>user…`), és ez a burkolat MINDEN promptnál
    és MINDEN nyelven bitre azonos. A Mérés C a prompt-tokenek SAE-jegyeit hasonlítja
    össze — a közös burkolat önmagában felnyomná az átfedést, ráadásul nyelvfüggetlenül,
    tehát pont a mért hatást hamisítaná meg. Ezért a reprezentáció-szintű méréseket a
    kérdés tokenjeire kell szűkíteni; a base kör csupasz promptjánál ugyanez a szűkítés
    a `Kérdés: ` / `\nVálasz:` címkéket veszi ki.
    """
    q = bare_question(p)
    if not scope_paths.CHAT:
        return p["prompt"], q
    text = tok.apply_chat_template([{"role": "user", "content": q}], tokenize=False,
                                   add_generation_prompt=True, enable_thinking=False)
    return text, q


def question_token_span(tok, text, q):
    """A csupasz kérdés token-indexei a promptban — [start, end) félig nyílt."""
    c0 = text.rindex(q)
    c1 = c0 + len(q)
    offs = tok(text, return_offsets_mapping=True, add_special_tokens=False)["offset_mapping"]
    hit = [i for i, (a, b) in enumerate(offs) if b > c0 and a < c1]
    return [hit[0], hit[-1] + 1] if hit else [0, len(offs)]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def cut_at_stop(text):
    """A legkorábbi stop-szekvencia előtti rész. Visszaadja a szöveget és hogy vágtunk-e."""
    idx = [text.find(s) for s in STOPS]
    idx = [i for i in idx if i >= 0]
    if not idx:
        return text.strip(), False
    return text[: min(idx)].strip(), True


def load_prompts(args):
    rows = [json.loads(l) for l in scope_paths.prompts(ROOT).read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.only_truncated:
        prev = RES / "gen.jsonl"
        if not prev.exists():
            raise SystemExit("nincs korábbi results/gen.jsonl — előbb egy teljes futás kell")
        prev_rows = [json.loads(l) for l in prev.read_text(encoding="utf-8").splitlines() if l.strip()]
        trunc = {(m["item_id"], m["lang"]) for m in prev_rows
                 if m["truncated"] and not (args.skip_degenerate and m.get("degenerate"))}
        rows = [r for r in rows if (r["item_id"], r["lang"]) in trunc]
        args.force = True
    if args.only:
        want = {x.strip() for x in args.only.split(",")}
        rows = [r for r in rows if r["item_id"] in want]
    if args.lang:
        rows = [r for r in rows if r["lang"] == args.lang]
    if args.limit:
        rows = rows[: args.limit]
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="vesszős item_id lista")
    ap.add_argument("--lang", default="", help="csak egy nyelv (hu/en/zh)")
    ap.add_argument("--force", action="store_true", help="a kész fájlokat is újraszámolja")
    ap.add_argument("--only-truncated", action="store_true",
                    help="csak azokat, amelyek egy korábbi futásban a token-keretbe ütköztek "
                         "(nagyobb kerettel; greedy mellett a magától megállt válaszok bitre ugyanazok maradnának)")
    ap.add_argument("--skip-degenerate", action="store_true",
                    help="az ismétlési hurokba esett válaszokat NE futtassa újra — a hurok nagyobb "
                         "kerettel sem bomlik fel, csak tovább ismételne (flag_degenerate.py jelöli)")
    args = ap.parse_args()

    for sub in ("gen", "hidden"):
        (RES / sub).mkdir(parents=True, exist_ok=True)

    gb10_patch.patch(conv=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    think_id = tok.convert_tokens_to_ids("<think>")
    assert think_id == 248068, f"váratlan <think> token-azonosító: {think_id}"
    pad_id = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda").eval()
    n_layers = model.config.text_config.num_hidden_layers if hasattr(model.config, "text_config") \
        else model.config.num_hidden_layers
    stack = model.model.layers
    assert len(stack) == n_layers, f"{len(stack)} != {n_layers}"
    log(f"modell kész — {MODEL} / {type(model).__name__}, {n_layers} réteg, "
        f"<think> tiltva (id {think_id}), prompt: {'chat-sablon' if scope_paths.CHAT else 'nyers folytatás'}"
        f" → {RES}")

    captured = {}
    hooks = [layer.register_forward_hook(
        lambda m, inp, out, i=i: captured.__setitem__(i, (out[0] if isinstance(out, tuple) else out).detach()))
        for i, layer in enumerate(stack)]
    for h in hooks:                       # a generáláshoz NEM kellenek, csak a forwardhoz
        h.remove()
    hooks = []

    prompts = load_prompts(args)
    log(f"{len(prompts)} prompt a sorban")
    t_start = time.time()
    done = skipped = 0
    invariant_checked = False

    for k, p in enumerate(prompts, 1):
        base = f"{p['item_id']}_{p['lang']}"
        f_txt, f_meta, f_npy = RES / "gen" / f"{base}.txt", RES / "gen" / f"{base}.json", RES / "hidden" / f"{base}.npy"
        if not args.force and f_txt.exists() and f_meta.exists() and f_npy.exists():
            skipped += 1
            continue

        torch.manual_seed(0)              # greedy mellett is: legyen bitre reprodukálható
        prompt_text, bare_q = build_prompt(p, tok)
        enc = tok(prompt_text, return_tensors="pt").to("cuda")
        n_prompt = int(enc["input_ids"].shape[1])
        q_span = question_token_span(tok, prompt_text, bare_q)

        # ── 1. generálás ────────────────────────────────────────────────────
        t0 = time.time()
        with torch.no_grad():
            g = model.generate(**enc, max_new_tokens=p["max_new_tokens"], do_sample=False,
                               bad_words_ids=[[think_id]], stop_strings=STOPS, tokenizer=tok,
                               pad_token_id=pad_id)
        n_new = int(g.shape[1] - n_prompt)
        raw = tok.decode(g[0][n_prompt:], skip_special_tokens=True)
        text, stopped = cut_at_stop(raw)
        t_gen = time.time() - t0

        # ── 2. forward hookkal, csak a promptra ─────────────────────────────
        hooks = [layer.register_forward_hook(
            lambda m, inp, out, i=i: captured.__setitem__(i, (out[0] if isinstance(out, tuple) else out).detach()))
            for i, layer in enumerate(stack)]
        with torch.no_grad():
            out = model(**enc, output_hidden_states=True)
        for h in hooks:
            h.remove()
        hooks = []

        # [0] = embedding-kimenet, [L+1] = resid_post(L)
        planes = [out.hidden_states[0][0].float()] + [captured[i][0].float() for i in range(n_layers)]
        arr = torch.stack(planes).cpu().numpy()          # [33, T, 4096], fp32

        if not invariant_checked:
            # a fázis 0 invariánsa: hook(i) == hidden_states[i+1] az utolsó KIVÉTELÉVEL
            hs = [h[0].float().cpu() for h in out.hidden_states]
            mid = max(abs(float((captured[i][0].float().cpu() - hs[i + 1]).abs().max())) for i in range(n_layers - 1))
            last = float((captured[n_layers - 1][0].float().cpu() - hs[n_layers]).abs().max())
            assert mid < 1e-2, f"a hook és a hidden_states eltér a KÖZÉPSŐ rétegeken is ({mid}) — állj meg"
            assert last > 1e-2, f"a hidden_states utolsó eleme NEM normalizált ({last}) — a transformers változott, nézd át"
            log(f"invariáns OK — középső rétegek eltérése {mid:.2e}, az utolsóé {last:.3f} (normalizált)")
            invariant_checked = True

        amax = float(np.abs(arr).max())
        dtype = np.float16 if amax < 60000 else np.float32   # fp16-túlcsordulás ellen
        np.save(f_npy, arr.astype(dtype))

        f_txt.write_text(text, encoding="utf-8")
        f_meta.write_text(json.dumps({
            "item_id": p["item_id"], "group": p["group"], "kind": p["kind"], "lang": p["lang"],
            "expected": p["expected"], "n_prompt_tokens": n_prompt, "n_new_tokens": n_new,
            "model": MODEL, "chat_template": scope_paths.CHAT,
            "prompt_text": prompt_text, "q_tok_span": q_span,
            "max_new_tokens": p["max_new_tokens"],
            "truncated": n_new >= p["max_new_tokens"],       # a keretbe ütközött → az elemzésben jelezni kell
            "stopped_at_marker": stopped, "raw": raw, "text": text,
            "hidden_dtype": str(np.dtype(dtype)), "hidden_absmax": round(amax, 2),
            "gen_seconds": round(t_gen, 1),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        done += 1

        if k % 10 == 0 or k == len(prompts):
            el = time.time() - t_start
            log(f"{k}/{len(prompts)} — kész {done}, kihagyva {skipped}, eltelt {el/60:.1f} perc"
                f"{f', becsült hátralévő {el/max(done,1)*(len(prompts)-k)/60:.0f} perc' if done else ''}")

    # ── összesítés + a runbook §1 ellenőrzései ──────────────────────────────
    metas = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((RES / "gen").glob("*.json"))]
    (RES / "gen.jsonl").write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in metas) + "\n", encoding="utf-8")

    n_txt = len(list((RES / "gen").glob("*.txt")))
    n_npy = len(list((RES / "hidden").glob("*.npy")))
    log(f"KÉSZ — új {done}, kihagyva {skipped} · gen {n_txt} fájl · hidden {n_npy} fájl")
    trunc = [m["item_id"] + "/" + m["lang"] for m in metas if m["truncated"]]
    log(f"a token-keretbe ütközött: {len(trunc)}/{len(metas)}" + (f" — pl. {trunc[:5]}" if trunc else ""))

    # ⛔ a klasszikus indexelési hiba: mindhárom nyelv ugyanazt a vektort kapná
    probe = next((m for m in metas if m["kind"] == "fact"), None)
    if probe:
        vecs = {}
        for lang in ("hu", "en", "zh"):
            f = RES / "hidden" / f"{probe['item_id']}_{lang}.npy"
            if f.exists():
                v = np.load(f)[16, -1].astype(np.float32)
                vecs[lang] = v / (np.linalg.norm(v) + 1e-9)
        if len(vecs) == 3:
            log(f"{probe['item_id']} 16. réteg, utolsó token — cos(hu,en)={float(vecs['hu'] @ vecs['en']):.3f} "
                f"cos(hu,zh)={float(vecs['hu'] @ vecs['zh']):.3f} "
                f"(azonos: {np.array_equal(vecs['hu'], vecs['en']) or np.array_equal(vecs['hu'], vecs['zh'])})")


if __name__ == "__main__":
    main()
