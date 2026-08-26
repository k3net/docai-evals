#!/usr/bin/env python3
"""Fázis 0 döntés #2: a `<think>` blokk elnyomása.

MÉRT PROBLÉMA (00_smoke_template.json): a definíciós (UNT) promptoknál a modell
a hat zero-shot esetből NÉGYSZER `<think>` blokkot nyit, és a 120 tokenes
keret teljesen elmegy a belső monológra — a válasz meg sem jelenik. A few-shot
sablon ezt javítja, de a rövid mintaválaszok a definíció HOSSZÁT is levágják,
ami pont a D1 komponens-lefedettséget rontaná el.

Tisztább beavatkozás: a `<think>` token tiltása (`bad_words_ids`) — a sablon
marad a runbook szerinti, nyelvek között szimmetrikus, és a beavatkozás egy
sorban dokumentálható a módszertanban.

    bash ~/lang-study/src/run_spark.sh src/smoke_think.py
"""
import json, pathlib, time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import gb10_patch

MODEL = "Qwen/Qwen3.5-9B-Base"
ROOT = pathlib.Path("/work")
STOP = {"hu": "\nKérdés:", "en": "\nQuestion:", "zh": "\n问题："}


def main():
    gb10_patch.patch(conv=True)
    tok = AutoTokenizer.from_pretrained(MODEL)
    ids = {t: tok.convert_tokens_to_ids(t) for t in ("<think>", "</think>")}
    print("token-azonosítók:", ids, flush=True)
    bad = [[i] for t, i in ids.items() if t == "<think>" and i is not None and i >= 0]
    print("tiltott tokenek:", bad, flush=True)

    model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda").eval()
    torch.manual_seed(0)

    prompts = [json.loads(l) for l in (ROOT / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    pick = [p for p in prompts if p["item_id"] in ("UNT-HU01", "UNT-HU02", "UNT-ZH01", "UNT-HU01-ctrl")]
    pick += [p for p in prompts if p["item_id"] in ("ZH01", "HU01")]

    out = []
    for p in pick:
        budget = 200 if p["kind"] in ("unt", "ctrl") else 60
        enc = tok(p["prompt"], return_tensors="pt").to("cuda")
        with torch.no_grad():
            g = model.generate(**enc, max_new_tokens=budget, do_sample=False, bad_words_ids=bad,
                               pad_token_id=tok.pad_token_id or tok.eos_token_id)
        raw = tok.decode(g[0][enc["input_ids"].shape[1]:], skip_special_tokens=True)
        cut = raw.split(STOP[p["lang"]])[0].strip()
        rec = {"item_id": p["item_id"], "kind": p["kind"], "lang": p["lang"], "budget": budget,
               "n_new": int(g.shape[1] - enc["input_ids"].shape[1]), "raw": raw, "cut": cut,
               "opens_think": "<think>" in raw[:60], "cut_chars": len(cut)}
        out.append(rec)
        print(f"[{p['item_id']:15s}/{p['lang']}] think={rec['opens_think']} új_token={rec['n_new']} "
              f"karakter={rec['cut_chars']}\n    {cut[:260]!r}\n", flush=True)

    (ROOT / "reports" / "00_smoke_think.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"=== <think>-nyitás tiltás mellett: {sum(r['opens_think'] for r in out)}/{len(out)} ===")


if __name__ == "__main__":
    main()
