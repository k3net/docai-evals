"""vLLM-kiolvasás: a döntési pozíció címke-logprobjai `logprob_token_ids`-szel.

Minden (item, permutáció) párra egy `/v1/completions` hívás megy offline
tokenizált prompttal, `max_tokens=1`, `temperature=0`. A válasz a jelen lévő
címkék teljes szótárra normált logprobja + a mintavételezett token. Alapból
SOROS (concurrency 1): a GB10-en a kötegméret a numerikát billenti, így csak
a soros mérés hasonlítható össze futások között.

Példa:
  python3 eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0a/run1.jsonl \
      --url http://127.0.0.1:8400 --model Qwen/Qwen3.6-35B-A3B-FP8 --perms 0
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    NONE_TEXT, PromptTokenizer, gold_label, label_mass, labels_for, permutation, read_jsonl,
    restricted, write_jsonl,
)


def post(url: str, body: dict, timeout: float = 600) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def wait_health(base: str, timeout_s: int = 1800) -> None:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(base + "/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception:
            pass
        time.sleep(10)
    raise TimeoutError(f"{base} nem lett egészséges {timeout_s} s alatt")


def read_one(base: str, model: str, ids: list[int], label_tok: dict[str, int]) -> dict:
    body = {
        "model": model,
        "prompt": ids,
        "max_tokens": 1,
        "temperature": 0,
        "logprobs": 1,
        "logprob_token_ids": list(label_tok.values()),
        "return_tokens_as_token_ids": True,
    }
    resp = post(base + "/v1/completions", body)
    ch = resp["choices"][0]
    lp = ch["logprobs"]
    top = lp["top_logprobs"][0]  # {"token_id:32": -0.1, ...}
    by_id = {int(k.split(":", 1)[1]): v for k, v in top.items()}
    missing = [lab for lab, tid in label_tok.items() if tid not in by_id]
    sampled = int(lp["tokens"][0].split(":", 1)[1])
    return {
        "label_logprobs": {lab: by_id.get(tid, -9999.0) for lab, tid in label_tok.items()},
        "missing": missing,
        "sampled_id": sampled,
        "sampled_logprob": lp["token_logprobs"][0],
    }


def fingerprint(rows: list[dict]) -> str:
    """A numerika-mód ujjlenyomata: a címke-logprobok pontos (repr) értékeiből."""
    h = hashlib.sha256()
    for r in sorted(rows, key=lambda r: (r["id"], r["perm"])):
        for lab in sorted(r["label_logprobs"]):
            h.update(f"{r['id']}|{r['perm']}|{lab}|{r['label_logprobs'][lab]!r}\n".encode())
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8400")
    ap.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B-FP8")
    ap.add_argument("--perms", default="0", help="vesszős lista, pl. 0,1,2,3")
    ap.add_argument("--move-none-frac", type=float, default=0.0, help="az itemek ekkora hányadán az X is mozog")
    ap.add_argument("--prefill", default="")
    ap.add_argument("--none-text", default="alap", choices=sorted(NONE_TEXT))
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--warmup", type=int, default=3, help="ennyi el nem mentett bemelegítő kérés a mérés előtt")
    ap.add_argument("--content-free", action="store_true", help="L1(b) contextual calibration: a számlasor helyett „N/A”")
    args = ap.parse_args()

    items = read_jsonl(Path(args.items))
    if args.limit:
        items = items[: args.limit]
    if args.content_free:
        items = [{**it, "context": {**it["context"], "sor": "N/A", "mennyiseg": "N/A", "egysegar": "N/A"}} for it in items]
    pt = PromptTokenizer()
    perms = [int(p) for p in args.perms.split(",")]
    jobs = []
    for it in items:
        move = (int(hashlib.sha256(it["id"].encode()).hexdigest(), 16) % 1000) < args.move_none_frac * 1000
        for p in perms:
            order = permutation(it, p, move_none=move)
            labs = labels_for(order)
            ids = pt.encode_item(it, order, args.prefill, NONE_TEXT[args.none_text])
            label_tok = {lab: pt.label_ids[lab] for lab in labs}
            jobs.append((it, p, move, order, labs, ids, label_tok))

    def run(job):
        it, p, move, order, labs, ids, label_tok = job
        t0 = time.perf_counter()
        r = read_one(args.url, args.model, ids, label_tok)
        probs = restricted(r["label_logprobs"])
        pred = max(probs, key=probs.get)
        return {
            "id": it["id"], "split": it.get("split"), "perm": p, "move_none": move,
            "order": order, "labels": labs, "gold_label": gold_label(it, order),
            "pred": pred, "conf": probs[pred], "probs": probs,
            "label_mass": label_mass(r["label_logprobs"]), **r,
            "n_prompt_tokens": len(ids), "latency_s": time.perf_counter() - t0,
            "model": args.model, "prefill": args.prefill, "none_text": args.none_text, "content_free": args.content_free,
        }

    # bemelegítés: az első kérések más numerikai úton futhatnak (K0a: probe-00) — nem rögzítjük
    for j in jobs[: args.warmup]:
        read_one(args.url, args.model, j[5], j[6])
    t0 = time.time()
    if args.concurrency == 1:
        rows = [run(j) for j in jobs]
    else:
        with ThreadPoolExecutor(args.concurrency) as ex:
            rows = list(ex.map(run, jobs))
    write_jsonl(Path(args.out), rows)
    acc = sum(r["pred"] == r["gold_label"] for r in rows) / max(1, len(rows))
    miss = sum(bool(r["missing"]) for r in rows)
    summary = {
        "n": len(rows), "acc": acc, "missing_rows": miss, "fingerprint": fingerprint(rows),
        "wall_s": time.time() - t0, "model": args.model, "perms": perms,
    }
    Path(args.out).with_suffix(".summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
