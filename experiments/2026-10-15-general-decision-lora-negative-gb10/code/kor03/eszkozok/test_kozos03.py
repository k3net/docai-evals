"""03-as kör — a közös séma és a promptkeret egységtesztje (03-runbook 2. pont), CPU-n, a laptopon.

  1. a 00 és a 01 minden kiértékelő itemje (val, teszt, 00b, T-katalógus) átalakítva a közös sémára érvényes;
  2. a natív keret ugyanazt a chat-üzenetet adja, mint a 00/01 eredeti promptépítője (`common.messages_for`),
     a tárolt sorrendben és három permutációban;
  3. a natív keret tokenszáma minden tárolt kiolvasási rekordon egyezik a mért `n_prompt_tokens`-szel (00 F4, 00b,
     01 F4; a Qwen3.6 tokenizerével, a chat-sablon kikapcsolt gondolkodással). Ez a mért prompttal való
     egyezés bizonyítéka, nem csak a két kódé. Ismert kivétel: thai és dévanágari kombináló jeleket a laptop
     `tokenizers` 0.23.2-je másképp darabolja, mint a mérőkonténeré (a 01 tesztjében 14 item); ezek külön sorban;
  4. a generikus keret minden átalakított itemen renderel: X az utolsó, a címkék egytokenesek.

  kor01/.venv/bin/python kor03/eszkozok/test_kozos03.py
"""

from __future__ import annotations

import sys
import unicodedata
from collections import Counter
from pathlib import Path

from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import default_order, from_00, from_01, messages, validate  # noqa: E402
from common import labels_for, messages_for, permutation, read_jsonl  # noqa: E402

EXP = Path(__file__).resolve().parents[2]
TOK = next(Path.home().glob(".cache/huggingface/hub/models--Qwen--Qwen3.6-35B-A3B/snapshots/*/tokenizer.json"))
ITEMS_00 = [EXP / "adat/f1" / f"items_{s}.jsonl" for s in ("val-belso", "val-szallito", "T-belso", "T-szallito",
                                                            "T-kozeli", "T-tavoli")] + [EXP / "adat/k00b/meres/items_T-ujszallito.jsonl"]
ITEMS_01 = [EXP / "kor01/adat/items_val.jsonl", EXP / "kor01/adat/items_teszt.jsonl",
            EXP / "kor01/adat/f1s/items_katalogus.jsonl"]
READOUTS = [EXP / "eredmenyek/F4/vllm/l0_val.jsonl", EXP / "eredmenyek/F4/vllm/l0_test.jsonl",
            EXP / "eredmenyek/K00b/vllm/l0_test.jsonl", EXP / "kor01/eredmenyek/F4/vllm/bazis_val.jsonl",
            EXP / "kor01/eredmenyek/F4/vllm/bazis_test.jsonl"]


def thai_or_devanagari(text: str) -> bool:
    return any(unicodedata.category(ch) == "Mn" and unicodedata.name(ch, "").startswith(("THAI", "DEVANAGARI"))
               for ch in text)


def chat_text(msgs: list[dict]) -> str:
    """A Qwen3.6 chat-sablonja system + user üzenetre, enable_thinking=False, generálási előtaggal."""
    (s, u) = msgs
    return (f"<|im_start|>system\n{s['content']}<|im_end|>\n<|im_start|>user\n{u['content']}<|im_end|>\n"
            f"<|im_start|>assistant\n<think>\n\n</think>\n\n")


def main() -> int:
    fail = Counter()
    conv = {}
    for paths, fn in ((ITEMS_00, from_00), (ITEMS_01, from_01)):
        for p in paths:
            for it in read_jsonl(p):
                c = fn(it)
                conv[it["id"]] = (c, it)
                if validate(c):
                    fail["1 séma"] += 1
                    if fail["1 séma"] <= 3:
                        print("séma:", c["id"], validate(c))
    print(f"1 · {len(conv)} item átalakítva, sémahiba: {fail['1 séma']}")

    n2 = 0
    for c, it in conv.values():
        for k in range(4):
            order = permutation(it, k)
            n2 += 1
            if messages(c, order, "native") != messages_for(it, order):
                fail["2 natív"] += 1
    print(f"2 · natív keret == eredeti promptépítő: {n2} eset, eltérés: {fail['2 natív']}")

    tok = Tokenizer.from_file(str(TOK))
    n3 = Counter()
    for p in READOUTS:
        for r in read_jsonl(p):
            assert r.get("none_text", "alap") == "alap" and not r.get("prefill")
            c, _ = conv[r["id"]]
            n = len(tok.encode(chat_text(messages(c, r["order"], "native")), add_special_tokens=False).ids)
            n3[p.name] += 1
            if n != r["n_prompt_tokens"] and thai_or_devanagari(c["state"]):
                n3["ismert kivétel (thai/dévanágari)"] += 1
            elif n != r["n_prompt_tokens"]:
                fail["3 token"] += 1
                if fail["3 token"] <= 3:
                    print("tokenszám:", p.name, r["id"], r["perm"], n, r["n_prompt_tokens"])
    kiv = n3.pop("ismert kivétel (thai/dévanágari)", 0)
    print(f"3 · tokenszám == mért n_prompt_tokens: {sum(n3.values())} rekord ({dict(n3)}), eltérés: {fail['3 token']}; "
          f"ismert tokenizer-kivétel (thai/dévanágari): {kiv}")

    label_ids = {lab: tok.encode(lab, add_special_tokens=False).ids for lab in list("ABCDEFGHIJ") + ["X"]}
    if any(len(v) != 1 for v in label_ids.values()):
        fail["4 címke"] += 1
    for c, _ in conv.values():
        order = default_order(c)
        user = messages(c, order, "generic")[1]["content"]
        labs = labels_for(order)
        if labs[-1] != "X" or not user.endswith(("X) Egyik sem", "X) None of these")):
            fail["4 generikus"] += 1
    print(f"4 · generikus keret: {len(conv)} item, hiba: {fail['4 generikus']}; címketokenek egytokenesek: "
          f"{'igen' if not fail['4 címke'] else 'NEM'}")
    ex00 = next(c for c, _ in conv.values() if c["family"].startswith("termek"))
    ex01 = next(c for c, _ in conv.values() if c["family"].startswith("routing") and c["lang"] == "hu")
    for ex in (ex00, ex01):
        print(f"\n--- generikus példa ({ex['id']}) ---\n{messages(ex, default_order(ex), 'generic')[1]['content']}")
    x = Counter((c["family"].split(".")[0], c["x_type"]) for c, _ in conv.values() if c["gold"] is None and not c["ketertelmu"])
    print("\nX-típusok:", dict(sorted(x.items())))
    print("\nEREDMÉNY:", "OK" if not fail else f"HIBA {dict(fail)}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
