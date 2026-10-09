"""01-es kör — a döntési prompt tokenhossza forrásonként, a Qwen3.6 tokenizerével (CPU, a laptopon).

A chat-sablon kerete (system/user/assistant jelölők, kikapcsolt thinking) egyszer mérve, fix többletként adódik
hozzá; a többi a `keret.messages_for` szövege. A MASSIVE-itemekhez a katalógusból véletlen 2–10 eszközös listák
(a végleges listaépítés az F1-ben). Kimenet: percentilisek és a 1024 / 1536 / 2048 tokent meghaladó arány
leíráshossz-korlátonként.

  kor01/.venv/bin/python kor01/eszkozok/tokenhossz.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import numpy as np
from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent))
from keret import messages_for  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TOK = next(Path.home().glob(".cache/huggingface/hub/models--Qwen--Qwen3.6-35B-A3B/snapshots/*/tokenizer.json"))
# a chat-sablon többlete (Qwen3.6, enable_thinking=False): <|im_start|>system\n…<|im_end|>\n<|im_start|>user\n…<|im_end|>\n
# <|im_start|>assistant\n<think>\n\n</think>\n\n — a jelölők egytokenesek, a sortörések és a szerepnevek kb. 15 token
TEMPLATE_OVERHEAD = 15
SAMPLE = 3000


def load(name: str) -> list[dict]:
    rows = [json.loads(line) for line in open(ROOT / "adat" / name)]
    random.Random(0).shuffle(rows)
    return rows[:SAMPLE]


def massive_items() -> list[dict]:
    cat = json.loads((ROOT / "katalogus/eszkozok.json").read_text())
    tools = [{"id": t["name"], "name": t["name"], "description": t["leiras"],
              "required": [p["name"] for p in t["params"] if p["required"]]} for t in cat]
    rng = random.Random(1)
    rows = [json.loads(line) for line in open(ROOT / "adat/massive_hu.jsonl")]
    rng.shuffle(rows)
    return [{"lang": "hu", "request": r["request"], "history": [], "options": rng.sample(tools, rng.randint(2, 10))}
            for r in rows[:SAMPLE]]


def main() -> None:
    tok = Tokenizer.from_file(str(TOK))
    sources = {"bfcl_teszt": load("bfcl_teszt.jsonl"), "w2c_teszt": load("w2c_teszt.jsonl"),
               "xlam_train": load("xlam_train.jsonl"), "xlam_irrel": load("xlam_irrel_train.jsonl"),
               "w2c_train": load("w2c_train.jsonl"), "massive_hu (katalógus)": massive_items()}
    res = {}
    for dmax in (150, 300, 600):
        for name, items in sources.items():
            lens = []
            for it in items:
                order = [o["id"] for o in it["options"]] + [None]
                msgs = messages_for(it, order, desc_max=dmax)
                n = sum(len(tok.encode(m["content"], add_special_tokens=False).ids) for m in msgs) + TEMPLATE_OVERHEAD
                lens.append(n)
            a = np.array(lens)
            res[f"{name} @ leírás≤{dmax}"] = {
                "n": len(a), "p50": int(np.percentile(a, 50)), "p95": int(np.percentile(a, 95)), "max": int(a.max()),
                ">1024": round(float((a > 1024).mean()), 4), ">1536": round(float((a > 1536).mean()), 4),
                ">2048": round(float((a > 2048).mean()), 4)}
    (ROOT / "adat/tokenhossz.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in res.items():
        print(f"{k:42s} p50 {v['p50']:5d} p95 {v['p95']:5d} max {v['max']:5d}  >1024 {v['>1024']:.3f}  >1536 {v['>1536']:.3f}")
    it = sources["massive_hu (katalógus)"][0]
    print("\n--- minta (magyar) ---\n" + messages_for(it, [o["id"] for o in it["options"]] + [None])[1]["content"])


if __name__ == "__main__":
    main()
