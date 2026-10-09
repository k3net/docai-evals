"""K0b/K0d segédmérések egy futó vLLM-alanyon.

  render  — az offline (HF-tokenizer) token-id-k egyeznek-e a vLLM render-végpontjáéval
            (a példánynak --enable-scale-out kell)
  ppl     — perplexitás a közös épség-szövegeken (prompt_logprobs), a HF-fel összevethető

Példa:
  python3 eszkozok/vllm_ellenor.py render --items adat/probe50.jsonl --out eredmenyek/F0/k0b/render.json
  python3 eszkozok/vllm_ellenor.py ppl --out eredmenyek/F0/k0d/vllm_ppl.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import PPL_SZOVEGEK, PromptTokenizer, messages_for, permutation, read_jsonl, write_json  # noqa: E402
from kiolvaso import post  # noqa: E402


def cmd_render(args, pt: PromptTokenizer) -> dict:
    items = read_jsonl(Path(args.items))
    eq, diffs = 0, []
    for it in items:
        order = permutation(it, 0)
        msgs = messages_for(it, order)
        offline = pt.encode(msgs)
        r = post(args.url + "/v1/chat/completions/render", {
            "model": args.model, "messages": msgs, "add_generation_prompt": True,
            "chat_template_kwargs": {"enable_thinking": False},
        })
        server = list(r.get("token_ids") or [])
        if server == offline:
            eq += 1
        elif len(diffs) < 5:
            k = next((i for i, (a, b) in enumerate(zip(offline, server)) if a != b), min(len(offline), len(server)))
            diffs.append({"id": it["id"], "first_diff": k, "offline_tail": offline[k:k + 8], "server_tail": server[k:k + 8],
                          "len_offline": len(offline), "len_server": len(server)})
    return {"n": len(items), "equal": eq, "diffs": diffs, "label_ids": pt.label_ids, "ok": eq == len(items)}


def cmd_ppl(args, pt: PromptTokenizer) -> dict:
    out = []
    for s in PPL_SZOVEGEK:
        ids = pt.tok.encode(s, add_special_tokens=False)
        r = post(args.url + "/v1/completions", {
            "model": args.model, "prompt": ids, "max_tokens": 1, "temperature": 0, "prompt_logprobs": 0,
        })
        pl = r["choices"][0]["prompt_logprobs"]
        nll = []
        for i in range(1, len(ids)):
            d = pl[i] or {}
            e = d.get(str(ids[i])) or d.get(ids[i])
            if e is None:
                raise SystemExit(f"prompt_logprobs: hiányzik a {i}. token ({ids[i]})")
            nll.append(-(e["logprob"] if isinstance(e, dict) else e))
        out.append(math.exp(sum(nll) / len(nll)))
    return {"ppl": out}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["render", "ppl"])
    ap.add_argument("--items", default="adat/probe50.jsonl")
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8400")
    ap.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B-FP8")
    args = ap.parse_args()
    pt = PromptTokenizer()
    res = cmd_render(args, pt) if args.cmd == "render" else cmd_ppl(args, pt)
    write_json(Path(args.out), res)
    print(json.dumps(res, ensure_ascii=False))
    if args.cmd == "render" and not res["ok"]:
        raise SystemExit("K0b: az offline tokenizálás eltér a render-végponttól")


if __name__ == "__main__":
    main()
