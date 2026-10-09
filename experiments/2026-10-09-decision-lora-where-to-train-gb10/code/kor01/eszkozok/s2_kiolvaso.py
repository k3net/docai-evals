"""L3→S2 (01-runbook 5. pont, leíró kar): az L3 a τ@95 fölött dönt, a többit a bázis gondolkodó módja kapja.

A kiválasztás az L3 (`temp`, perm 0) kiolvasásából: a temperature és a τ@95 a val-on, a 00 `elemzes.py` szabályával;
S2-be megy minden teszt-item, ahol az L3 nem sorol be (X-et mond, vagy a bizalma < τ). Az S2 ugyanazt a döntési
kérdést kapja (keret, perm 0), thinkinggel, és a `</think>` utáni első címkebetű a döntés. Ha nincs ilyen (csonka
gondolkodás, más kimenet), a döntés hiányzik (`pred_label` = None); a jelentés ezt külön számolja.

  python3 kor01/eszkozok/s2_kiolvaso.py --items kor01/adat/f4_teszt.jsonl \
      --l3-val …/vllm/l3_s1_val.jsonl --l3-test …/vllm/l3_s1_test.jsonl --out …/vllm/s2_test.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import PromptTokenizer, labels_for, messages_for, permutation, read_jsonl, write_jsonl  # noqa: E402
from elemzes import arm_predictions, by_item, choose_tau, decide, fit_temperature, load_meta, option_scores  # noqa: E402
from kiolvaso import post  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ANSWER = re.compile(r"\b([A-JX])\b")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--l3-val", required=True)
    ap.add_argument("--l3-test", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8400")
    ap.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B-FP8")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--max-tokens", type=int, default=3072)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    meta = load_meta(ROOT / "adat")
    val = read_jsonl(Path(args.l3_val))
    val0 = [r for r in val if r["perm"] == 0]
    temp = fit_temperature(val0, meta)
    pv = arm_predictions("temp", by_item(val0, 0), meta, {"temp": temp})
    tau = choose_tau(pv, meta, [i for i in pv if meta[i]["split"] == "val"], 0.95)
    sel = set()
    for iid, rs in by_item(read_jsonl(Path(args.l3_test)), 0).items():
        pred, conf = decide(option_scores(rs[0], temp=temp))
        if pred is None or conf < tau:
            sel.add(iid)

    # csak a pontozott H1-pool: a kétértelműek és az át nem nézett MASSIVE-maradék kimarad (01 v1, 4. pont)
    items = [it for it in read_jsonl(Path(args.items)) if it["id"] in sel and not it["meta"].get("ketertelmu")
             and (it["forras"] != "massive_hu" or it["meta"].get("t_hu_atnezett"))]
    if args.limit:
        items = items[: args.limit]
    tok = PromptTokenizer().tok
    jobs = []
    for it in items:
        order = permutation(it, 0)
        text = tok.apply_chat_template(messages_for(it, order), tokenize=False, add_generation_prompt=True, enable_thinking=True)
        jobs.append((it, order, tok.encode(text, add_special_tokens=False)))

    def run(job):
        it, order, ids = job
        t0 = time.perf_counter()
        ch = post(args.url + "/v1/completions", {"model": args.model, "prompt": ids, "max_tokens": args.max_tokens,
                                                 "temperature": 0})["choices"][0]
        text = ch["text"]
        labs = labels_for(order)
        tail = text.split("</think>", 1)[1] if "</think>" in text else None
        m = ANSWER.search(tail) if tail is not None else None
        lab = m.group(1) if m and m.group(1) in labs else None
        pred = (order[labs.index(lab)] if lab is not None else None)
        return {"id": it["id"], "split": it.get("split"), "forras": it.get("forras"), "gold": it.get("gold"),
                "labels": labs, "order": order, "pred_label": lab, "pred": pred, "van_valasz": lab is not None,
                "finish_reason": ch.get("finish_reason"), "n_gen_tokens": ch.get("usage", {}).get("completion_tokens"),
                "tail": (tail or "")[:200], "latency_s": time.perf_counter() - t0}

    t0 = time.time()
    with ThreadPoolExecutor(args.concurrency) as ex:
        rows = list(ex.map(run, jobs))
    write_jsonl(Path(args.out), rows)
    n = len(rows)
    summary = {"temperature": temp, "tau95": tau, "kivalasztott": len(sel), "n": n,
               "van_valasz": sum(r["van_valasz"] for r in rows) / max(1, n),
               "pontossag": sum(r["van_valasz"] and r["pred"] == r["gold"] for r in rows) / max(1, n),
               "latency_median_s": sorted(r["latency_s"] for r in rows)[n // 2] if n else None,
               "wall_s": time.time() - t0, "concurrency": args.concurrency}
    Path(args.out).with_suffix(".summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
