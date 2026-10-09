"""L0n — natív tool calling (01-runbook 5. pont, H3): chat template + `tools`, greedy, thinking nélkül.

A parser-függés elkerülésére a promptot offline rendereljük (a modell saját chat template-je a `tools`-szal), a
nyers kimenetet a `/v1/completions` adja, és magunk parszoljuk: a Qwen3.6 formátuma
`<tool_call>\\n<function=NÉV>\\n<parameter=…>`. A döntés az első hívott függvény neve (opció-id-re képezve), vagy
None, ha nincs hívás (= X). Ismeretlen név → `__ismeretlen__` (hívás, de nem a listán lévő eszközre: hibás
besorolás). Az eszközök sémája az itemből: név, leírás, a kötelező paraméterek string típussal; ugyanaz az
információ, amit az L3 promptja kap. A sorrend a tárolt (perm 0). Diagnosztika: `p_call0`, vagyis az első pozíción a
`<tool_call>` token valószínűsége.

Párhuzamos (alap c = 16): a greedy generálás 10 ezer itemre sorosan túl lassú; a kötegfüggő numerika miatti
billenést a tanulmány jelzi. Legfeljebb 256 token: ennyi alatt hívás nélkül = szöveges válasz (csonkolás jelölve).

  python3 kor01/eszkozok/l0n_kiolvaso.py --items kor01/adat/f4_teszt.jsonl --out kor01/eredmenyek/F4/vllm/l0n_test.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import PromptTokenizer, read_jsonl, write_jsonl  # noqa: E402
from kiolvaso import post  # noqa: E402

FUNC = re.compile(r"<function=([^>\n]+)>")
UNKNOWN = "__ismeretlen__"


def tools_for(item: dict) -> list[dict]:
    out = []
    for o in item["options"]:
        req = list(o.get("required") or [])
        out.append({"type": "function", "function": {
            "name": o["name"], "description": o.get("description") or "",
            "parameters": {"type": "object", "properties": {p: {"type": "string"} for p in req}, "required": req}}})
    return out


def messages_for(item: dict) -> list[dict]:
    hist = [{"role": m["role"], "content": m["content"]} for m in item.get("history") or []
            if m.get("role") in ("system", "user", "assistant") and (m.get("content") or "").strip()]
    return hist + [{"role": "user", "content": item["request"]}]


def parse(text: str, item: dict) -> tuple[object, str | None, bool]:
    """(pred, név, hívott-e): pred = opció-id, None (nincs hívás) vagy UNKNOWN."""
    m = FUNC.search(text)
    if not m:
        return None, None, "<tool_call>" in text
    name = m.group(1).strip()
    ids = {o["name"]: o["id"] for o in item["options"]}
    return ids.get(name, UNKNOWN), name, True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--url", default="http://127.0.0.1:8400")
    ap.add_argument("--model", default="Qwen/Qwen3.6-35B-A3B-FP8")
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    items = read_jsonl(Path(args.items))
    if args.limit:
        items = items[: args.limit]
    pt = PromptTokenizer()
    call_id = pt.tok.convert_tokens_to_ids("<tool_call>")
    jobs = []
    for it in items:
        text = pt.tok.apply_chat_template(messages_for(it), tools=tools_for(it), tokenize=False, add_generation_prompt=True,
                                          enable_thinking=False)
        jobs.append((it, pt.tok.encode(text, add_special_tokens=False)))

    def run(job):
        it, ids = job
        t0 = time.perf_counter()
        body = {"model": args.model, "prompt": ids, "max_tokens": args.max_tokens, "temperature": 0, "logprobs": 1,
                "logprob_token_ids": [call_id], "return_tokens_as_token_ids": True,
                "stop": ["<parameter=", "</function>"], "include_stop_str_in_output": True}
        ch = post(args.url + "/v1/completions", body)["choices"][0]
        top0 = ch["logprobs"]["top_logprobs"][0] if ch.get("logprobs") and ch["logprobs"].get("top_logprobs") else {}
        lp = top0.get(f"token_id:{call_id}")
        pred, name, called = parse(ch["text"], it)
        return {"id": it["id"], "split": it.get("split"), "forras": it.get("forras"), "gold": it.get("gold"),
                "pred": pred, "name": name, "called": called, "finish_reason": ch.get("finish_reason"),
                "p_call0": math.exp(lp) if lp is not None else None, "text": ch["text"][:400],
                "n_prompt_tokens": len(ids), "latency_s": time.perf_counter() - t0, "model": args.model}

    for j in jobs[:3]:  # bemelegítés, nem rögzítjük
        run(j)
    t0 = time.time()
    with ThreadPoolExecutor(args.concurrency) as ex:
        rows = list(ex.map(run, jobs))
    write_jsonl(Path(args.out), rows)
    n = len(rows)
    summary = {"n": n, "hivas_arany": sum(r["pred"] is not None for r in rows) / max(1, n),
               "pontossag": sum(r["pred"] == r["gold"] for r in rows) / max(1, n),
               "ismeretlen_nev": sum(r["pred"] == UNKNOWN for r in rows),
               "csonka_hivas_nelkul": sum(r["finish_reason"] == "length" and r["pred"] is None for r in rows),
               "wall_s": time.time() - t0, "concurrency": args.concurrency, "model": args.model}
    Path(args.out).with_suffix(".summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
