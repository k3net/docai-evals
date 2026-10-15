"""03-as kör — tanárjelölt smoke: Gemma 4 26B-A4B-it a vLLM v0.30.0-n (03-runbook 8. pont, F2; előre hozva).

Amit néz:
  1. a címkék (A–J, X) egytokenesek-e a tanár tokenizerében, és mik az id-k;
  2. a chat-sablon ismeri-e a gondolkodás kikapcsolását (`enable_thinking`);
  3. a 00 és a 01 val-ján (120–120 item, perm 0, a natív prompt) a címketömeg (a címkékre jutó valószínűség), a
     top-1 találat, az X-felismerés és a késleltetés.
A pontosság csak irányjelzés, nem a tanárkapu (4.4 pont): ahhoz temperature-fit, permutáció-átlag és zajauditált
gold kell.

  python3 kor03/eszkozok/tanar_smoke.py --url http://127.0.0.1:8440 --model gemma4-26b \\
      --tokenizer /hfg/hub/models--google--gemma-4-26B-A4B-it/snapshots/<sha> --out kor03/eredmenyek/F2g/smoke.json
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "eszkozok"))
from common import gold_label, labels_for, messages_for, permutation, read_jsonl  # noqa: E402

LABELS = list("ABCDEFGHIJ") + ["X"]
SETS = {"00_val": [ROOT / "adat/f1/items_val-belso.jsonl", ROOT / "adat/f1/items_val-szallito.jsonl"],
        "01_val": [ROOT / "kor01/adat/items_val.jsonl"]}


def post(url: str, body: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8440")
    ap.add_argument("--model", default="gemma4-26b")
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(args.tokenizer)
    label_ids = {lab: tok.encode(lab, add_special_tokens=False) for lab in LABELS}
    single = all(len(v) == 1 for v in label_ids.values())
    tmpl = tok.chat_template if isinstance(tok.chat_template, str) else json.dumps(tok.chat_template)
    res = {"tokenizer": args.tokenizer, "label_ids": label_ids, "labels_single_token": single,
           "template_has_enable_thinking": "enable_thinking" in (tmpl or ""), "sets": {}}
    if not single:
        Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))
        raise SystemExit("a címkék nem egytokenesek")
    lid = {lab: v[0] for lab, v in label_ids.items()}
    example = None
    for name, paths in SETS.items():
        items = [it for p in paths for it in read_jsonl(p)]
        random.Random(20261009).shuffle(items)
        rows = []
        for it in items[: args.n]:
            order = permutation(it, 0)
            labs = labels_for(order)
            text = tok.apply_chat_template(messages_for(it, order), tokenize=False, add_generation_prompt=True,
                                           enable_thinking=False)
            example = example or text
            ids = tok.encode(text, add_special_tokens=False)
            t0 = time.time()
            out = post(args.url + "/v1/completions",
                       {"model": args.model, "prompt": ids, "max_tokens": 1, "temperature": 0, "logprobs": 1,
                        "logprob_token_ids": [lid[lab] for lab in labs], "return_tokens_as_token_ids": True})
            dt = time.time() - t0
            lp = out["choices"][0]["logprobs"]
            by_id = {int(k.split(":", 1)[1]): v for k, v in lp["top_logprobs"][0].items()}
            ll = {lab: by_id.get(lid[lab], -9999.0) for lab in labs}
            mass = sum(math.exp(v) for v in ll.values())
            top = max(ll, key=ll.get)
            m = it.get("meta") or {}
            rows.append({"id": it["id"], "gold": gold_label(it, order), "top": top, "mass": mass,
                         "sampled_is_label": int(lp["tokens"][0].split(":", 1)[1]) in lid.values(),
                         "ketertelmu": bool(m.get("ketertelmu")), "latency_s": dt})
        sc = [r for r in rows if not r["ketertelmu"]]
        xs = [r for r in sc if r["gold"] == "X"]
        nx = [r for r in sc if r["gold"] != "X"]
        res["sets"][name] = {
            "n": len(rows), "n_scored": len(sc),
            "label_mass_median": statistics.median(r["mass"] for r in rows),
            "label_mass_min": min(r["mass"] for r in rows),
            "sampled_is_label": sum(r["sampled_is_label"] for r in rows) / len(rows),
            "top1_accuracy": sum(r["top"] == r["gold"] for r in sc) / len(sc),
            "x_recall": sum(r["top"] == "X" for r in xs) / len(xs) if xs else None, "n_x": len(xs),
            "nonx_accuracy": sum(r["top"] == r["gold"] for r in nx) / len(nx) if nx else None,
            "latency_p50_s": statistics.median(r["latency_s"] for r in rows)}
        print(name, json.dumps(res["sets"][name], ensure_ascii=False))
    res["example_prompt_tail"] = (example or "")[-400:]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
