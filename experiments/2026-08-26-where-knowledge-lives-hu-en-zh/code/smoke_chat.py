#!/usr/bin/env python3
"""Füstteszt a 2. körhöz (instruct): chat-sablon + kérdés-token-tartomány.

    SCOPE_MODEL=Qwen/Qwen3.5-9B SCOPE_CHAT=1 bash code/run_spark.sh code/smoke_chat.py

Csak a tokenizert tölti be (nincs GPU-igény). Azt ellenőrzi, hogy
  * a chat-sablon `enable_thinking=False`-szal NEM nyit `<think>`-et,
  * a burkolat mérete nyelvenként mekkora (ez a Mérés C-t hamisítaná meg, ha bent maradna),
  * a kérdés token-tartománya pontosan a kérdés tokenjeit fedi-e (dekódolással ellenőrizve),
  * a base és az instruct tokenizer ugyanazt az id-sorozatot adja-e a csupasz kérdésre.
"""
import json
import pathlib

from transformers import AutoTokenizer

import scope_paths
from run import QFRAME, bare_question, build_prompt, question_token_span

ROOT = pathlib.Path("/work")


def main():
    tok = AutoTokenizer.from_pretrained(scope_paths.MODEL)
    rows = [json.loads(l) for l in scope_paths.data(ROOT, "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"modell: {scope_paths.MODEL} · chat-sablon: {scope_paths.CHAT}\n")
    for lang in ("hu", "en", "zh"):
        p = next(r for r in rows if r["lang"] == lang and r["kind"] == "fact")
        text, q = build_prompt(p, tok)
        ids = tok(text, add_special_tokens=False)["input_ids"]
        span = question_token_span(tok, text, q)
        inside = tok.decode(ids[span[0]: span[1]])
        print(f"── {lang} · {p['item_id']}")
        print(f"   teljes prompt ({len(ids)} token): {text!r}"[:300])
        print(f"   kérdés-tartomány {span} ({span[1]-span[0]} token) → {inside!r}")
        print(f"   burkolat: {len(ids) - (span[1]-span[0])} token")
        print(f"   egyezik a csupasz kérdéssel: {inside.strip() == q.strip()}")
        print(f"   <think> a promptban: {'<think>' in text}")
        # a csupasz kérdés id-sorozata — ennek a base körrel AZONOSNAK kell lennie
        bare_ids = tok(q, add_special_tokens=False)["input_ids"]
        print(f"   csupasz kérdés id-k [:8]: {bare_ids[:8]} … ({len(bare_ids)} token)\n")


if __name__ == "__main__":
    main()
