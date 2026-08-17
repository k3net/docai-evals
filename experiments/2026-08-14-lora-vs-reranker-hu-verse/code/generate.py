"""F4/1 — generálás minden mérési feltételhez. A GPU-s gépen fut.

Négy feltétel, mindegyik UGYANAZT a rögzített promptszettet kapja
(`data/dataset/eval/`):

  B0 — bázismodell, egyszerű prompt
  B1 — bázismodell + few-shot stílusprompt (4 példa a TRAIN szeletből)
  B2 — B1 + determinisztikus best-of-N reranker
  C  — LoRA-adapteres modell
  C2 — C + ugyanaz a reranker (additív-e a két hatás?)

**A B2 a valódi ellenfél**, nem a B0. A formai metrikákat egy reranker
triviálisan javítja, mert pont azt optimalizálja, amit mérünk. Ha a LoRA nem
veri a B2-t, akkor nem tett hozzá semmit — ez legitim eredmény, ha méréssel
mutatjuk meg.

Két generálási mód:
  `style`      — a stílus-eval: mintavételes (T=0,8), 3 minta promptonként
  `extraction` — a memorizáció-teszt: MOHÓ (greedy), az első két sor után

A dekódolási paraméterek módonként fixek és nem keverednek — greedy a
memorizációhoz, mintavételes a stílushoz.

    python3 code/generate.py --condition B0 --model Qwen/Qwen3.5-9B
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import sys

# A prozódiai mérőeszköz a repó közös scripts/ mappájában lakik — ez pontozza a
# best-of-N rerankert is, modellhívás nélkül. Ld. annotate_corpus.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import hu_prosody as hp  # noqa: E402

SYSTEM_PROMPT = "Magyar költő vagy. A válaszod kizárólag a kért vers legyen, magyarázat nélkül."

# A dekódolási paraméterek módonként rögzítettek (runbook 6: „ne keverd”).
STYLE_DECODE = {"do_sample": True, "temperature": 0.8, "top_p": 0.9, "max_new_tokens": 420}
EXTRACT_DECODE = {"do_sample": False, "max_new_tokens": 160}

CONDITIONS = {
    #            few-shot  adapter  best-of
    "B0": {"fewshot": False, "adapter": False, "best_of": 1},
    "B1": {"fewshot": True, "adapter": False, "best_of": 1},
    "B2": {"fewshot": True, "adapter": False, "best_of": 8},
    "C": {"fewshot": False, "adapter": True, "best_of": 1},
    "C2": {"fewshot": False, "adapter": True, "best_of": 8},
}


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=sorted(CONDITIONS))
    ap.add_argument("--model", default="Qwen/Qwen3.5-9B")
    ap.add_argument("--adapter", default="", help="a LoRA checkpoint útvonala (C/C2)")
    ap.add_argument("--author", default="", help="üres = mindkét szerző (B ágakhoz)")
    ap.add_argument("--mode", default="style", choices=["style", "extraction"])
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--seed", type=int, default=1)
    # A tényleges GPU-batch = prompt × (minta × best_of), tehát feltételenként
    # más: a B2/C2 ágon egy prompt 24 szekvenciát jelent (3 minta × best-of-8),
    # a B0-n hármat. Ezért nem a promptszámot rögzítjük, hanem a párhuzamosan
    # dekódolt SZEKVENCIÁK számát — a memóriaigény ettől függ, és a GB10-en a
    # dekódolás memória-sávszélesség-korlátos: a nagy batch szinte ingyen van.
    ap.add_argument("--max-seqs", type=int, default=24)
    ap.add_argument("--data", default="/work/data")
    ap.add_argument("--out", default=str(Path.home() / "lora-study" / "generations"))
    ap.add_argument("--tag", default="", help="kimeneti fájlnév-utótag (pl. checkpoint)")
    ap.add_argument("--limit", type=int, default=0, help="csak az első N prompt (teszthez)")
    return ap.parse_args()


def build_fewshot_prefix(examples: list[dict]) -> list[dict]:
    """A few-shot példák beszélgetés-fordulókként, nem egy nagy szövegblokkban.

    Így a modell a saját chat-formátumában látja a mintát, és a B1 tényleg
    a legjobb prompt-alapú baseline, nem egy szalmabáb.
    """
    turns: list[dict] = []
    for ex in examples:
        turns.append(
            {
                "role": "user",
                "content": f"Írj verset.\nCím: {ex['title']}\nForma: {ex['spec_text']}.",
            }
        )
        turns.append({"role": "assistant", "content": ex["text"]})
    return turns


def form_score(text: str, spec: dict) -> float:
    """A reranker célfüggvénye: mennyire tartja a szöveg a KÉRT formát.

    Determinisztikus, modell nélkül — ugyanaz a `hu_prosody`, ami az
    értékelést is végzi. Ez szándékos: a B2 baseline pont azt optimalizálja,
    amit mérünk, és épp ezért erős ellenfél.
    """
    stanzas = [
        [ln.strip() for ln in block.splitlines() if ln.strip()]
        for block in text.strip().split("\n\n")
    ]
    stanzas = [s for s in stanzas if s]
    if not stanzas:
        return 0.0
    score = 0.0

    want_stanzas = spec.get("n_stanzas")
    if want_stanzas:
        score += 1.0 - min(1.0, abs(len(stanzas) - want_stanzas) / max(want_stanzas, 1))

    want_size = spec.get("stanza_size")
    if want_size:
        hits = sum(1 for s in stanzas if len(s) == want_size)
        score += hits / len(stanzas)

    want_syll = spec.get("syllables")
    if want_syll:
        lines = [ln for s in stanzas for ln in s]
        hits = sum(1 for ln in lines if hp.count_syllables(ln) == want_syll)
        score += hits / max(1, len(lines))

    want_scheme = spec.get("scheme")
    if want_scheme:
        hits = sum(1 for s in stanzas if hp.rhyme_scheme(s) == want_scheme)
        score += hits / len(stanzas)
    else:
        # Séma-előírás híján a puszta rímeltségre jutalmazunk.
        pairs = [
            (s[i], s[i + 1]) for s in stanzas for i in range(len(s) - 1)
        ]
        if pairs:
            score += sum(hp.rhyme_score(a, b) >= 0.6 for a, b in pairs) / len(pairs)
    return score


def main() -> int:
    args = parse_args()
    cond = CONDITIONS[args.condition]
    if cond["adapter"] and not args.adapter:
        print("HIBA: a C/C2 feltételhez --adapter kell")
        return 1

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    set_seed(args.seed)
    data = Path(args.data)
    eval_dir = data / "dataset" / "eval"
    prompts = json.loads((eval_dir / "eval_prompts.json").read_text(encoding="utf-8"))
    probes = json.loads((eval_dir / "extraction_probes.json").read_text(encoding="utf-8"))
    fewshot = json.loads((eval_dir / "fewshot.json").read_text(encoding="utf-8"))

    items = prompts if args.mode == "style" else probes
    if args.author:
        items = [x for x in items if x["source_key"] == args.author]
    if args.limit:
        items = items[: args.limit]

    tok = AutoTokenizer.from_pretrained(args.model, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16,
        device_map={"": torch.cuda.current_device()}, attn_implementation="sdpa",
    )
    if cond["adapter"]:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)
        print(f"    adapter betöltve: {args.adapter}")
    model.eval()

    # A Qwen3.5 chat template ALAPBÓL üres `<think>\n\n</think>` blokkot tesz a
    # generation prompt végére, tehát a gondolkodás eleve ki van kapcsolva; az
    # `enable_thinking=False` nem változtat a rendereléon (ellenőrizve). Fontos,
    # hogy a TRL a tanításnál UGYANEZT a formátumot állítja elő, így nincs
    # train/inference eltérés. A hívást azért hagyjuk benne, hogy ha egy
    # későbbi checkpoint template-je mégis thinkinget kapcsol, itt essen ki.
    tpl_kwargs = {"add_generation_prompt": True}
    try:
        tok.apply_chat_template([{"role": "user", "content": "x"}], enable_thinking=False, **tpl_kwargs)
        tpl_kwargs["enable_thinking"] = False
    except TypeError:
        pass

    decode = STYLE_DECODE if args.mode == "style" else EXTRACT_DECODE
    n_samples = args.samples if args.mode == "style" else 1
    best_of = cond["best_of"] if args.mode == "style" else 1

    def render(item: dict) -> str:
        if args.mode == "extraction":
            msgs = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Folytasd szó szerint ezt a {item['author']}-verset:\n\n{item['lead']}"
                    ),
                },
            ]
        else:
            msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
            if cond["fewshot"]:
                msgs += build_fewshot_prefix(fewshot[item["source_key"]])
            msgs.append({"role": "user", "content": item["prompt"]})
        return tok.apply_chat_template(msgs, tokenize=False, **tpl_kwargs)

    n_per_item = n_samples * best_of
    batch = max(1, args.max_seqs // n_per_item)
    print(f"    {len(items)} elem · {n_per_item} generálás/elem · "
          f"batch {batch} prompt = {batch * n_per_item} párhuzamos szekvencia")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"_{args.tag}" if args.tag else ""
    out_path = out_dir / f"{args.mode}_{args.condition}{tag}.jsonl"

    t0 = time.time()
    written = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for start in range(0, len(items), batch):
            chunk = items[start : start + batch]
            texts = [render(it) for it in chunk for _ in range(n_per_item)]
            enc = tok(texts, return_tensors="pt", padding=True, add_special_tokens=False).to(model.device)
            with torch.no_grad():
                gen = model.generate(**enc, pad_token_id=(tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id), **decode)
            new = gen[:, enc["input_ids"].shape[1]:]
            outs = tok.batch_decode(new, skip_special_tokens=True)

            for i, item in enumerate(chunk):
                block = outs[i * n_per_item : (i + 1) * n_per_item]
                for s in range(n_samples):
                    cands = block[s * best_of : (s + 1) * best_of]
                    cands = [c.strip() for c in cands]
                    if best_of > 1:
                        scored = [(form_score(c, item.get("spec", {})), c) for c in cands]
                        scored.sort(key=lambda x: -x[0])
                        chosen, chosen_score = scored[0][1], scored[0][0]
                    else:
                        chosen, chosen_score = cands[0], None
                    rec = {
                        "condition": args.condition,
                        "mode": args.mode,
                        "sample": s,
                        "seed": args.seed,
                        "model": args.model,
                        "adapter": args.adapter or None,
                        "item": {k: v for k, v in item.items() if k != "continuation"},
                        "output": chosen,
                    }
                    if best_of > 1:
                        rec["best_of"] = best_of
                        rec["form_score"] = round(chosen_score, 3)
                        rec["candidate_scores"] = [round(s_, 3) for s_, _ in scored]
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1
            done = min(start + batch, len(items))
            print(f"    {done}/{len(items)} prompt · {time.time()-t0:.0f} s", flush=True)

    meta = {
        "condition": args.condition, "mode": args.mode, "model": args.model,
        "adapter": args.adapter or None, "author": args.author or "mind",
        "items": len(items), "records": written, "samples": n_samples,
        "best_of": best_of, "decode": decode, "seed": args.seed,
        "prompt_batch": batch, "parallel_seqs": batch * n_per_item,
        "elapsed_s": round(time.time() - t0), "host": os.uname().nodename,
    }
    out_path.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[{args.condition}/{args.mode}] {written} rekord · {time.time()-t0:.0f} s → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
