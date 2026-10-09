"""Független címke-bírálók (runbook 4.8): a bíráló a feladat-promptot GOLD NÉLKÜL kapja,
és választ + bizalmat ad. A kimenete csak TRIAGE (mit nézzen meg Dani), soha nem címke.

Két mód:
  logprobs — egyetlen kimeneti token, a címke-betűk logprobjaiból szűkített softmax
             (pl. a lokális Llama-3.3 vLLM-en, vagy bármely logprobot adó API)
  verbal   — JSON-válasz {"valasz": "A", "bizalom": 0-100} (ha az API nem ad logprobot)

Példák:
  # Llama a measurement-hosten (vLLM, OpenAI-kompatibilis)
  python3 eszkozok/biralo.py --items adat/f1/items_T-belso.jsonl --out eredmenyek/F1/biralo/llama_T-belso.jsonl \
      --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs
  # Mistral Small 4 lokálisan (f1d_vezenylo.sh); API-n a kulcs környezeti változóból jön, a NEVÉT kapja a --key-env
  python3 eszkozok/biralo.py --items ... --out ... --url https://openrouter.ai/api/v1 --model mistralai/mistral-small-2603 \
      --mode verbal --key-env <VÁLTOZÓ>
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import labels_for, messages_for, permutation, read_jsonl, write_json, write_jsonl  # noqa: E402

VERBAL_SUFFIX = ('\n\nVálaszolj kizárólag JSON-nal: {"valasz": "<betű>", "bizalom": <0–100 egész>}, '
                 'ahol a bizalom azt fejezi ki, mennyire vagy biztos a válaszodban.')


def chat(url: str, model: str, messages: list[dict], extra: dict, key: str | None, timeout: float = 300) -> dict:
    body = {"model": model, "messages": messages, **extra}
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(), headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 5:
                time.sleep(2 ** attempt * 3)
                continue
            raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
        except (urllib.error.URLError, TimeoutError):
            if attempt < 5:
                time.sleep(2 ** attempt * 3)
                continue
            raise
    raise RuntimeError("elfogytak az újrapróbák")


def review_one(item: dict, args, key: str | None) -> dict:
    order = permutation(item, 0)
    labs = labels_for(order)
    msgs = messages_for(item, order)
    if args.mode == "logprobs":
        r = chat(args.url, args.model, msgs, {"max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20, **args.extra}, key)
        top = r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]
        lp = {}
        for t in top:
            tok = t["token"].strip()
            if tok in labs and tok not in lp:
                lp[tok] = t["logprob"]
        if not lp:
            return {"id": item["id"], "labels": labs, "pred": None, "conf": None, "hiba": "nincs címke a top-20-ban"}
        m = max(lp.values())
        z = sum(math.exp(v - m) for v in lp.values())
        probs = {k: math.exp(v - m) / z for k, v in lp.items()}
        pred = max(probs, key=probs.get)
        return {"id": item["id"], "labels": labs, "pred": pred, "conf": probs[pred], "probs": probs,
                "label_mass_top20": sum(math.exp(v) for v in lp.values())}
    msgs = [msgs[0], {"role": "user", "content": msgs[1]["content"] + VERBAL_SUFFIX}]
    r = chat(args.url, args.model, msgs, {"temperature": 0, "max_completion_tokens": args.max_tokens, **args.extra}, key)
    txt = r["choices"][0]["message"]["content"] or ""
    m = re.search(r"\{.*\}", txt, re.S)
    try:
        d = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        d = {}
    pred = str(d.get("valasz", "")).strip().upper()[:1] or None
    conf = d.get("bizalom")
    return {"id": item["id"], "labels": labs, "pred": pred if pred in labs else None,
            "conf": (float(conf) / 100 if isinstance(conf, (int, float)) else None), "raw": txt[:300]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--mode", default="logprobs", choices=["logprobs", "verbal"])
    ap.add_argument("--key-env", default="", help="a kulcsot tartalmazó KÖRNYEZETI VÁLTOZÓ neve (pl. OPENAI_API_KEY)")
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--max-tokens", type=int, default=200)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--extra-body", default="{}", help='további kérés-mezők JSON-ban, pl. {"reasoning_effort": "none"} (Mistral Small 4)')
    args = ap.parse_args()
    args.extra = json.loads(args.extra_body)
    key = os.environ.get(args.key_env) if args.key_env else None
    if args.key_env and not key:
        raise SystemExit(f"a {args.key_env} környezeti változó üres")
    items = read_jsonl(Path(args.items))
    if args.limit:
        items = items[: args.limit]
    out = Path(args.out)
    done = {r["id"]: r for r in read_jsonl(out)} if out.exists() else {}
    todo = [it for it in items if it["id"] not in done or done[it["id"]].get("pred") is None]

    def run(it):
        try:
            res = review_one(it, args, key)
        except Exception as e:  # egy item hibája ne állítsa le a kört; a None-t a triage kezeli
            res = {"id": it["id"], "pred": None, "conf": None, "hiba": str(e)[:300]}
        res.update({"model": args.model, "mode": args.mode})
        return res

    with ThreadPoolExecutor(args.concurrency) as ex:
        for res in ex.map(run, todo):
            done[res["id"]] = res
    rows = [done[it["id"]] for it in items if it["id"] in done]
    write_jsonl(out, rows)
    ok = [r for r in rows if r.get("pred")]
    write_json(out.with_suffix(".summary.json"), {"n": len(rows), "valaszolt": len(ok), "model": args.model, "mode": args.mode,
                                                  "hibak": sum(1 for r in rows if r.get("hiba"))})
    print(f"{out}: {len(ok)}/{len(rows)} válasz")


if __name__ == "__main__":
    main()
