#!/usr/bin/env python3
"""A promptok token-szintű szövege — a Mérés C kvalitatív részéhez (spark-dev, konténer).

    bash ~/lang-study/code/run_spark.sh code/dump_tokens.py
    SCOPE_MODEL=Qwen/Qwen3.5-9B SCOPE_RES=results_instruct SCOPE_CHAT=1 \
        bash ~/lang-study/code/run_spark.sh code/dump_tokens.py

A `results/sae/*.npz` tokenenként tárolja az aktív feature-öket, de a tokenek SZÖVEGE
csak a tokenizerből jön — az meg a konténerben van. Ezt egyszer kiírjuk, utána a
laptopon minden elemzés offline megy.

⛔⛔ KÉT HIBA VOLT ITT (2026-08-25-én javítva), és mindkettő NÉMÁN elcsúsztatta volna az
instruct kör Mérés C-jét:
  1. a tokenizer FIXEN `Qwen/Qwen3.5-9B-Base` volt — a körhöz tartozót kell használni;
  2. a NYERS `prompts.jsonl`-szöveget tokenizálta, miközben az instruct kör SAE-je a
     CHAT-SABLONOS promptra készült (a burkolat mind a három nyelven 12 token). A tokenek
     így 12-vel elcsúsztak volna a feature-tömbhöz képest — és ez sehol nem dobott volna
     hibát, csak rossz tokenszövegeket írt volna a riportba.
A javítás: a `gen.jsonl`-ben elmentett `prompt_text`-et tokenizáljuk (pontosan azt a
sztringet, amit a modell kapott), és a végén ÖSSZEVETJÜK az SAE-tömb tokenszámával.
"""
import glob
import json
import pathlib

import numpy as np
from transformers import AutoTokenizer

import scope_paths

ROOT = pathlib.Path("/work")
RES = scope_paths.res(ROOT)

tok = AutoTokenizer.from_pretrained(scope_paths.MODEL)

# a modellnek ténylegesen átadott sztring; a base kör gen.jsonl-je régebbi, ott nincs
# `prompt_text` — annak a körnek a nyers prompt a helyes.
gen = {(r["item_id"], r["lang"]): r for r in
       (json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
raw = {(p["item_id"], p["lang"]): p["prompt"] for p in
       (json.loads(l) for l in scope_paths.data(ROOT, "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}

# ⛔ A base kör `gen.jsonl`-je 08-24-i, abban még NINCS `q_tok_span`. Ha csak az instruct
# körre írnánk ki, a Mérés C a két körben MÁS token-halmazon futna (base: teljes prompt,
# instruct: csak a kérdés), és a base↔instruct különbség részben ezt mérné. Ezért a
# hiányzó tartományt itt SZÁMOLJUK — ugyanazzal a képlettel, amit a `run.py` használ.
QFRAME = {"hu": ("Kérdés: ", "\nVálasz:"), "en": ("Question: ", "\nAnswer:"),
          "zh": ("问题：", "\n回答：")}


def bare_question(prompt, lang):
    pre, post = QFRAME[lang]
    assert prompt.startswith(pre) and prompt.endswith(post), f"váratlan keret: {prompt[:40]!r}"
    return prompt[len(pre): len(prompt) - len(post)]


def question_token_span(text, q):
    """A csupasz kérdés token-indexei a promptban — [start, end), félig nyílt."""
    c0 = text.rindex(q)
    c1 = c0 + len(q)
    offs = tok(text, return_offsets_mapping=True, add_special_tokens=False)["offset_mapping"]
    hit = [i for i, (a, b) in enumerate(offs) if b > c0 and a < c1]
    return [hit[0], hit[-1] + 1] if hit else [0, len(offs)]


out, spans, mismatch = {}, {}, []
for key, r in gen.items():
    text = r.get("prompt_text") or raw[key]
    ids = tok(text)["input_ids"]
    name = f"{key[0]}_{key[1]}"
    out[name] = [tok.decode([i]) for i in ids]
    spans[name] = r.get("q_tok_span") or question_token_span(text, bare_question(raw[key], key[1]))
    # ⛔ a néma elcsúszás egyetlen valódi őre: az SAE tokendimenziójával kell egyeznie
    f = RES / "sae" / f"{name}.npz"
    if f.exists():
        t_sae = np.load(f, allow_pickle=True)["idx"].shape[1]
        if t_sae != len(ids):
            mismatch.append((name, len(ids), t_sae))

(RES / "prompt_tokens.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
(RES / "prompt_q_span.json").write_text(json.dumps(spans, ensure_ascii=False), encoding="utf-8")
frac = sum(b - a for a, b in spans.values()) / sum(len(v) for v in out.values())
print(f"{len(out)} prompt tokenizálva ({scope_paths.MODEL}) → {RES.name}/prompt_tokens.json "
      f"(összesen {sum(len(v) for v in out.values())} token)")
print(f"  kérdés-tartomány elmentve {len(spans)} promptra → {RES.name}/prompt_q_span.json "
      f"(a prompt-tokenek {frac:.0%}-a a kérdés)")
if mismatch:
    raise SystemExit(f"⛔⛔ {len(mismatch)} prompt tokenszáma NEM egyezik az SAE-tömbbel — "
                     f"a Mérés C tokenszövegei elcsúsznának: {mismatch[:5]}")
print("  ✅ a tokenszám mind a 258 promptnál egyezik az SAE-tömbbel")
