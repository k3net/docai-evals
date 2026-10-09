"""Független címke-bírálók a 01-es itemeken (a 00 runbook 4.8 protokollja): a bíráló a döntési kérdést GOLD
NÉLKÜL kapja (a `keret.py` keretével, a tárolt opciósorrendben, X az utolsó), és egyetlen címketokent ad. A címke-
betűk logprobjaiból szűkített softmax adja a választ és a bizalmat. A kimenet csak TRIAGE (mit nézzen meg Dani),
soha nem címke.

  python3 kor01/eszkozok/biralo01.py --items kor01/adat/items_val.jsonl \\
      --out kor01/eredmenyek/F1S/biralo/llama_val.jsonl --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from keret import LABELS, NONE_LABEL, messages_for  # noqa: E402
from kozos01 import chat, read_jsonl, write_json, write_jsonl  # noqa: E402


def review_one(item: dict, args) -> dict:
    order = [o["id"] for o in item["options"]] + [None]
    labs = LABELS[: len(item["options"])] + [NONE_LABEL]
    r = chat(args.url, args.model, messages_for(item, order),
             {"max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20, **args.extra}, None)
    lp = {}
    for t in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
        tok = t["token"].strip()
        if tok in labs and tok not in lp:
            lp[tok] = t["logprob"]
    if not lp:
        return {"id": item["id"], "pred": None, "conf": None, "hiba": "nincs címke a top-20-ban"}
    m = max(lp.values())
    z = sum(math.exp(v - m) for v in lp.values())
    probs = {k: math.exp(v - m) / z for k, v in lp.items()}
    pred = max(probs, key=lambda k: probs[k])
    pred_id = None if pred == NONE_LABEL else order[labs.index(pred)]
    return {"id": item["id"], "pred": pred, "pred_id": pred_id, "conf": probs[pred], "probs": probs,
            "label_mass_top20": sum(math.exp(v) for v in lp.values())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--extra-body", default="{}")
    args = ap.parse_args()
    args.extra = json.loads(args.extra_body)
    items = read_jsonl(Path(args.items))
    if args.limit:
        items = items[: args.limit]
    out = Path(args.out)
    done = {r["id"]: r for r in read_jsonl(out)} if out.exists() else {}
    todo = [it for it in items if it["id"] not in done or done[it["id"]].get("pred") is None]

    def run(it):
        try:
            res = review_one(it, args)
        except Exception as e:  # egy item hibája ne állítsa le a kört; a None-t a triage kezeli
            res = {"id": it["id"], "pred": None, "conf": None, "hiba": str(e)[:300]}
        res["model"] = args.model
        return res

    with ThreadPoolExecutor(args.concurrency) as ex:
        for res in ex.map(run, todo):
            done[res["id"]] = res
    rows = [done[it["id"]] for it in items if it["id"] in done]
    write_jsonl(out, rows)
    ok = [r for r in rows if r.get("pred")]
    write_json(out.with_suffix(".summary.json"), {"n": len(rows), "valaszolt": len(ok), "model": args.model,
                                                  "hibak": sum(1 for r in rows if r.get("hiba"))})
    print(f"{out}: {len(ok)}/{len(rows)} válasz")


if __name__ == "__main__":
    main()
