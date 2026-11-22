"""Reference baseline for the hu-decision-trap-items dataset: one model, one read per item, OpenAI-compatible endpoint.

Standard library only. Two answer frames and two modes:
  --frame 2   options + one exit:    X "none of the above"
  --frame 4   options + three exits: X "no suitable option", Y "data needed for the decision is missing",
                                     Z "the request is outside the task"
  --mode direct   thinking off, temperature 0, the first generated token is the answer; the confidence is the
                  probability of that letter among the answer letters (from top_logprobs)
  --mode think    thinking on (Qwen3.6 model-card sampling: temperature 0.6, top_p 0.95, top_k 20, seed from the
                  item id), the last "Answer: <letter>" line is the answer; no confidence

Gold: MATCH -> the letter of `answer`; frame 2: every other label -> X;
frame 4: NO_MATCH -> X, MISSING_DATA -> Y, OUT_OF_SCOPE -> Z. Options keep the order stored in the item.

  python3 baseline.py run   --items data/calc_traps/test.jsonl --out out/calc_traps.f4.direct.jsonl --frame 4 --mode direct \
                            --url http://127.0.0.1:8400 --model Qwen/Qwen3.6-35B-A3B-FP8
  python3 baseline.py score --items data/calc_traps/test.jsonl --pred out/calc_traps.f4.direct.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

LETTERS = "ABCDEFGH"
TEXT = {
    "hu": {"system": "Döntési feladatot kapsz. Olvasd el a szöveget, és válaszd ki a kérdésre illő választ a felsoroltak közül.",
           "text": "Szöveg:", "question": "Kérdés", "options": "Válaszlehetőségek:",
           "X2": "Egyik sem", "X": "Nincs megfelelő opció", "Y": "Hiányzik a döntéshez szükséges adat", "Z": "A kérés kívül esik a feladaton",
           "direct": "Csak a választott betűvel válaszolj.", "think": "A válaszod utolsó sora ez legyen: „Answer: <betű>”."},
    "en": {"system": "You are given a decision task. Read the text and choose the answer to the question from the list.",
           "text": "Text:", "question": "Question", "options": "Options:",
           "X2": "None of the above", "X": "No suitable option", "Y": "The data needed for the decision is missing", "Z": "The request is outside the task",
           "direct": "Answer with the chosen letter only.", "think": 'The last line of your reply must be: "Answer: <letter>".'},
}
THINK = {"max_tokens": 4096, "temperature": 0.6, "top_p": 0.95, "top_k": 20}


def jsonl(p: str) -> list[dict]:
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def labels(item: dict, frame: int) -> list[str]:
    return [*LETTERS[: len(item["options"])], *("X" if frame == 2 else "XYZ")]


def gold(item: dict, frame: int) -> str:
    if item["label"] == "MATCH":
        return LETTERS[[o["id"] for o in item["options"]].index(item["answer"])]
    return "X" if frame == 2 else {"NO_MATCH": "X", "MISSING_DATA": "Y", "OUT_OF_SCOPE": "Z"}[item["label"]]


def messages(item: dict, frame: int, mode: str) -> list[dict]:
    t = TEXT[item["lang"]]
    lines = [t["text"], item["text"].strip(), "", f"{t['question']}: {item['question']}", t["options"]]
    lines += [f"{LETTERS[i]}) {o['text']}" for i, o in enumerate(item["options"])]
    lines += [f"X) {t['X2']}"] if frame == 2 else [f"X) {t['X']}", f"Y) {t['Y']}", f"Z) {t['Z']}"]
    lines += ["", t[mode]]
    return [{"role": "system", "content": t["system"]}, {"role": "user", "content": "\n".join(lines)}]


def post(url: str, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(url + "/v1/chat/completions", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def one(item: dict, a) -> dict:
    labs = labels(item, a.frame)
    base, err = {"model": a.model, "messages": messages(item, a.frame, a.mode)}, ""
    for _ in range(3):
        try:
            if a.mode == "direct":
                r = post(a.url, {**base, "max_tokens": 1, "temperature": 0, "logprobs": True, "top_logprobs": 20,
                                 "chat_template_kwargs": {"enable_thinking": False}}, 600)
                ch = r["choices"][0]
                mass = {}
                for t in ch["logprobs"]["content"][0]["top_logprobs"]:
                    k = t["token"].strip()
                    if k in labs:
                        mass[k] = mass.get(k, 0.0) + math.exp(t["logprob"])
                pred = max(mass, key=mass.get) if mass else None
                return {"id": item["id"], "pred": pred, "conf": (mass[pred] / sum(mass.values())) if pred else 0.0, "label_mass": sum(mass.values()), "ok": True}
            seed = int(hashlib.sha256(item["id"].encode()).hexdigest()[:8], 16)
            r = post(a.url, {**base, **THINK, "seed": seed, "chat_template_kwargs": {"enable_thinking": True}}, 3600)
            ch = r["choices"][0]
            txt = (ch["message"].get("content") or "").split("</think>")[-1]
            m = re.findall(r"Answer:\s*\**\s*([A-HXYZ])\b", txt)
            return {"id": item["id"], "pred": m[-1] if m and m[-1] in labs else None, "finish": ch.get("finish_reason"),
                    "completion_tokens": r.get("usage", {}).get("completion_tokens"), "ok": True}
        except Exception as e:  # noqa: BLE001
            err = type(e).__name__
    return {"id": item["id"], "pred": None, "ok": False, "error": err}


def run(a) -> None:
    items = jsonl(a.items)
    if a.sample:
        ids = set(json.loads(Path(a.sample).read_text()))
        items = [it for it in items if it["id"] in ids]
    done = {r["id"] for r in jsonl(a.out)} if Path(a.out).exists() else set()
    todo = [it for it in items if it["id"] not in done]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    n = Counter()
    with open(a.out, "a", encoding="utf-8") as fh, ThreadPoolExecutor(a.concurrency) as ex:
        for i, r in enumerate(ex.map(lambda it: one(it, a), todo), 1):
            fh.write(json.dumps({**r, "frame": a.frame, "mode": a.mode}) + "\n")
            n["ok" if r["ok"] else "error"] += 1
            if i % 200 == 0:
                fh.flush()
                print(f"{i}/{len(todo)} errors {n['error']}", flush=True)
    print(json.dumps({"items": len(items), "already_done": len(done), **n}))


def wilson(k: int, n: int) -> list[float]:
    if not n:
        return [float("nan")] * 2
    z, p = 1.959964, k / n
    c, h = (p + z * z / (2 * n)) / (1 + z * z / n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [max(0.0, c - h), min(1.0, c + h)]


def score(a) -> dict:
    items = {it["id"]: it for it in jsonl(a.items)}
    preds = [r for r in jsonl(a.pred) if r["id"] in items]  # answers for items not in the file are ignored
    frame = preds[0]["frame"]
    out = {"n": len(preds), "frame": frame, "mode": preds[0]["mode"], "no_answer": sum(r["pred"] is None for r in preds), "by": {}}
    cells = {}
    for r in preds:
        it = items[r["id"]]
        g = gold(it, frame)
        kind = "correct" if r["pred"] == g else "no_answer" if r["pred"] is None else "wrong_option" if r["pred"] in LETTERS else "wrong_exit"
        for key in ("all", f"label={it['label']}", f"family={it['family']}", f"lang={it['lang']}", *([f"trap={it['trap_type']}"] if "trap_type" in it else [])):
            cells.setdefault(key, Counter())[kind] += 1
    for key, c in sorted(cells.items()):
        n = sum(c.values())
        out["by"][key] = {"n": n, "accuracy": c["correct"] / n, "accuracy_ci95": wilson(c["correct"], n), "wrong_option": c["wrong_option"] / n,
                          "wrong_option_ci95": wilson(c["wrong_option"], n), "wrong_exit": c["wrong_exit"] / n, "no_answer": c["no_answer"] / n}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--items", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--frame", type=int, choices=(2, 4), required=True)
    r.add_argument("--mode", choices=("direct", "think"), required=True)
    r.add_argument("--url", default="http://127.0.0.1:8400")
    r.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B-FP8")
    r.add_argument("--concurrency", type=int, default=32)
    r.add_argument("--sample", default="", help="JSON list of item ids to restrict the run to")
    s = sub.add_parser("score")
    s.add_argument("--items", required=True)
    s.add_argument("--pred", required=True)
    a = ap.parse_args()
    {"run": run, "score": score}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
