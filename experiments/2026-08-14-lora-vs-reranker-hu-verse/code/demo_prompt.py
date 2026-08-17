"""Egyetlen szabad prompt lefuttatása a cikk demójához — adapterrel és nélküle.

A mérési ágaktól CSAK a prompt tér el: a rendszerprompt, a chat-template, a
dekódolási paraméterek (T=0,8 · top_p=0,9) és a `form_score()` reranker
mindenben azonos a `generate.py`-val. Így a két kimenet közti különbség
egyetlen dologra vezethető vissza: van-e LoRA-adapter vagy nincs.

Few-shot példát SZÁNDÉKOSAN nem adunk egyik ágnak sem — a demó lényege, hogy
ugyanaz a prompt megy be mindkétszer, ahogy egy valódi felhasználó írná.

    python3 code/demo_prompt.py --prompt "..." --best-of 8 --seed 7
    python3 code/demo_prompt.py --prompt "..." --best-of 8 --seed 7 \
        --adapter /work/runs/arany_9b_mixer_r32_e3_s1/final
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# A mérőeszköz a repó közös scripts/ mappájában lakik — ld. annotate_corpus.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import hu_prosody as hp  # noqa: E402
from generate import SYSTEM_PROMPT, STYLE_DECODE, form_score  # noqa: E402


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="Qwen/Qwen3.5-9B")
    ap.add_argument("--adapter", default="", help="üres = nyers bázismodell")
    ap.add_argument("--best-of", type=int, default=8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--stanzas", type=int, default=1, help="a reranker spec-je")
    ap.add_argument("--stanza-size", type=int, default=4)
    ap.add_argument("--label", default="demo")
    ap.add_argument("--out", default="/work/generations")
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    set_seed(args.seed)
    tok = AutoTokenizer.from_pretrained(args.model, padding_side="left")
    model = AutoModelForCausalLM.from_pretrained(
        args.model, dtype=torch.bfloat16,
        device_map={"": torch.cuda.current_device()}, attn_implementation="sdpa",
    )
    if args.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, args.adapter)
        print(f"adapter: {args.adapter}")
    else:
        print("adapter: NINCS (nyers bázismodell)")
    model.eval()

    tpl_kwargs = {"add_generation_prompt": True}
    try:
        tok.apply_chat_template([{"role": "user", "content": "x"}],
                                enable_thinking=False, **tpl_kwargs)
        tpl_kwargs["enable_thinking"] = False
    except TypeError:
        pass

    msgs = [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": args.prompt}]
    text = tok.apply_chat_template(msgs, tokenize=False, **tpl_kwargs)

    # A spec a prompt szövegéből adódik: „4 soros, szépen rímelő” = egy strófa,
    # négy sor, rímeljen. Szótagszám nincs előírva, ezért a reranker a puszta
    # rímeltségre jutalmaz (ld. `form_score` else-ága).
    spec = {"n_stanzas": args.stanzas, "stanza_size": args.stanza_size}

    t0 = time.time()
    enc = tok([text] * args.best_of, return_tensors="pt", padding=True,
              add_special_tokens=False).to(model.device)
    with torch.no_grad():
        gen = model.generate(
            **enc,
            pad_token_id=(tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id),
            **STYLE_DECODE,
        )
    outs = tok.batch_decode(gen[:, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    elapsed = time.time() - t0

    cands = []
    for c in outs:
        c = c.strip()
        lines = [ln.strip() for ln in c.splitlines() if ln.strip()]
        cands.append({
            "text": c,
            "form_score": round(form_score(c, spec), 4),
            "n_lines": len(lines),
            "syllables": [hp.count_syllables(ln) for ln in lines],
            "rhyme_scheme": hp.rhyme_scheme(lines) if len(lines) >= 2 else "",
            "rhyme_pairs": [
                {
                    "a": lines[i].split()[-1] if lines[i].split() else "",
                    "b": lines[i + 1].split()[-1] if lines[i + 1].split() else "",
                    "score": round(hp.rhyme_score(lines[i], lines[i + 1]), 3),
                    "inflectional": hp.inflectional_suffix(lines[i], lines[i + 1]),
                }
                for i in range(len(lines) - 1)
            ],
        })

    # Determinisztikus rangsor: pontszám szerint csökkenőben, döntetlennél a
    # generálási sorrend dönt (a `max` az elsőt tartja meg, ld. generate.py).
    order = sorted(range(len(cands)), key=lambda i: (-cands[i]["form_score"], i))
    winner = order[0]

    print(f"\n{'='*70}\nPROMPT: {args.prompt}")
    print(f"best-of {args.best_of} · seed {args.seed} · {elapsed:.1f}s\n{'='*70}")
    for rank, i in enumerate(order, start=1):
        c = cands[i]
        mark = "★ GYŐZTES" if i == winner else f"  #{rank}"
        print(f"\n{mark}  form_score={c['form_score']:.3f}  "
              f"sor={c['n_lines']}  szótag={c['syllables']}  séma={c['rhyme_scheme']}")
        for ln in c["text"].splitlines():
            if ln.strip():
                print(f"      {ln}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"demo_{args.label}.json"
    out_path.write_text(json.dumps({
        "prompt": args.prompt,
        "system_prompt": SYSTEM_PROMPT,
        "model": args.model,
        "adapter": args.adapter or None,
        "best_of": args.best_of,
        "seed": args.seed,
        "decode": STYLE_DECODE,
        "spec": spec,
        "elapsed_seconds": round(elapsed, 1),
        "winner_index": winner,
        "candidates": cands,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n→ {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
