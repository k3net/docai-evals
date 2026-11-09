"""03-as kör — címke-kiolvasás a közös sémájú itemekre (F2: L0/L1★, tanárkapu, gépi zajbecslés; 03-runbook 4.4, 6.).

Két út:
  ids   (Qwen3.6, Gemma 4): a prompt offline tokenizálva, a model saját chat-sablonjával, gondolkodás nélkül;
        `/v1/completions` `max_tokens=1`, `logprob_token_ids` = a jelen lévő címkék. A címkékre szűkített softmax
        pontos (a 00/01 kiolvasása, a publikált `decision_prompt.py` útja).
  chat  (Mistral Small 4, mistral-tokenizer): `/v1/chat/completions` top-20 logprob; ami a top-20-ból kimarad, az
        hiányzó címke (`missing`), a `label_mass` jelzi a kiolvasás épségét.
Muse-Glimmer (03, 2026-10-10): a sablon minden választ címzett-fejléccel és gondolkodással kezd, ezért ids-módban a
        `--prefix ' to=user<|message|>'` a válaszcsatornát kényszeríti (a sablon a gondolkodás nélküli korábbi
        válaszokat is így írja), `--chat-kwargs '{"reasoning_strength": "low"}'`.
Permutáció: a 00/01 `permutation`-je (0 = tárolt sorrend, az X mindig utolsó). Keret: kozos03.messages (`auto`: a
00/01 itemekre a natív, a többire a generikus).

  python3 kor03/eszkozok/kiolvaso03.py --items kor03/adat/f1/pool_val.jsonl --out kor03/eredmenyek/F2/qwen_val.jsonl \\
      --mode ids --url http://127.0.0.1:8400 --model Qwen/Qwen3.6-35B-A3B-FP8 --perms 0,1,2,3 --concurrency 32
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parents[1] / "eszkozok"))
from common import SUBJECT_SNAPSHOT, gold_label, labels_for, permutation  # noqa: E402
from kozos03 import messages  # noqa: E402

LABELS = list("ABCDEFGHIJ") + ["X"]
# think-mód (03, 2026-10-10): a Qwen3.6 gondolkodó mintavétele a modellkártya ajánlásával; a 4096 token a gondolkodás és
# a válasz együtt. A Sparkon nagy batch-nél ~3 token/s jut egy szekvenciára, ezért az időkorlát egy óra (a 900 s-os
# korláton 2026-10-09 éjjel a gondolkodó generálás elhalt).
THINK_DEFAULTS = {"max_tokens": 4096, "temperature": 0.6, "top_p": 0.95, "top_k": 20,
                  "chat_template_kwargs": {"enable_thinking": True}}


def post(url: str, body: dict, timeout: float = 600, tries: int = 5) -> dict:
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except Exception:  # noqa: BLE001
            if attempt == tries - 1:
                raise
            time.sleep(3 * 2 ** attempt)
    raise RuntimeError("unreachable")


def parse_label(ans: str, labs: list[str]) -> str | None:
    """A gondolkodás utáni válaszból a címke. Elfogadott: a teljes válasz egy betű („B”, „**B**”), vagy betűvel és
    zárójellel / ponttal kezdődik („B)”, „X) Egyik sem”, „D.”), vagy pontosan egy „B)” alakú említés van benne. A
    magyar „A” névelő („A válasz: …”) nem címke. Több különböző említés vagy egyik sem: None (hiányzó válasz)."""
    t = ans.strip()
    found = {x for x in re.findall(r"(?:^|[\s(*])([A-J]|X)\)", t) if x in labs}
    if len(found) > 1:
        return None
    for pat in (r"^\**\s*([A-J]|X)\s*\**$", r"^\**\s*\(?([A-J]|X)\)", r"^\**\s*([A-J]|X)\**\s*[.:]"):
        m = re.match(pat, t)
        if m and m.group(1) in labs:
            return m.group(1)
    return found.pop() if found else None


class Tok:
    def __init__(self, path: str, prefix: str = "", chat_kwargs: dict | None = None):
        from transformers import AutoTokenizer

        self.tok = AutoTokenizer.from_pretrained(path)
        self.prefix = prefix
        self.chat_kwargs = {"enable_thinking": False} if chat_kwargs is None else chat_kwargs
        self.ids = {}
        for lab in LABELS:
            t = self.tok.encode(lab, add_special_tokens=False)
            if len(t) != 1:
                raise SystemExit(f"a(z) {lab} címke nem egytokenes ebben a tokenizerben: {t}")
            self.ids[lab] = t[0]

    def encode(self, msgs: list[dict]) -> list[int]:
        text = self.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True, **self.chat_kwargs)
        return self.tok.encode(text + self.prefix, add_special_tokens=False)


def restricted(lp: dict[str, float]) -> dict[str, float]:
    m = max(lp.values())
    z = sum(math.exp(v - m) for v in lp.values())
    return {k: math.exp(v - m) / z for k, v in lp.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["ids", "chat", "think"], default="ids")
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--tokenizer", default=str(SUBJECT_SNAPSHOT))
    ap.add_argument("--frame", default="auto", choices=["auto", "native", "generic"])
    ap.add_argument("--perms", default="0")
    ap.add_argument("--tokenizer-only", action="store_true", help="csak a címketokenek ellenőrzése (szerver nélkül)")
    ap.add_argument("--prefix", default="", help="ids-módban a generálási prompt után fűzött szöveg (Muse: ' to=user<|message|>')")
    ap.add_argument("--chat-kwargs", default="", help="ids-módban a chat-sablon paraméterei (JSON); alap: enable_thinking=false")
    ap.add_argument("--extra", default="", help="chat-módban a kérés extra mezői (JSON)")
    ap.add_argument("--concurrency", type=int, default=32)
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()

    items = [json.loads(line) for p in a.items for line in Path(p).read_text(encoding="utf-8").splitlines()]
    if a.limit:
        items = items[: a.limit]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {(r["id"], r["perm"]) for r in map(json.loads, out.read_text(encoding="utf-8").splitlines())}
    perms = [int(p) for p in a.perms.split(",")]
    tok = Tok(a.tokenizer, a.prefix, json.loads(a.chat_kwargs) if a.chat_kwargs else None) if a.mode == "ids" else None
    extra = json.loads(a.extra) if a.extra else {}
    jobs = [(it, p) for it in items for p in perms if (it["id"], p) not in done]
    print(f"{len(items)} item × {len(perms)} perm; {len(done)} kész, {len(jobs)} hátra", flush=True)
    if a.tokenizer_only:
        # előellenőrzés: minden item renderelhető-e, és hány prompt lóg túl a 8192-es max-model-len-en
        lens = []
        for it in items:
            order = permutation(it, perms[0])
            msgs = messages(it, order, a.frame)
            lens.append(len(tok.encode(msgs)) if tok else sum(len(m["content"]) for m in msgs) // 3)
        lens.sort()
        print(json.dumps({"n": len(lens), "median": lens[len(lens) // 2], "p99": lens[int(len(lens) * 0.99)],
                          "max": lens[-1], "over_8000": sum(x > 8000 for x in lens)}), flush=True)
        return

    def run(job):
        it, p = job
        order = permutation(it, p)
        labs = labels_for(order)
        msgs = messages(it, order, a.frame)
        t0 = time.perf_counter()
        if a.mode == "ids":
            ids = tok.encode(msgs)
            r = post(a.url + "/v1/completions", {"model": a.model, "prompt": ids, "max_tokens": 1, "temperature": 0,
                                                 "logprobs": 1, "logprob_token_ids": [tok.ids[x] for x in labs],
                                                 "return_tokens_as_token_ids": True})
            top = {int(k.split(":", 1)[1]): v for k, v in r["choices"][0]["logprobs"]["top_logprobs"][0].items()}
            lp = {x: top.get(tok.ids[x], -9999.0) for x in labs}
            n_tok = len(ids)
        elif a.mode == "think":
            seed = int(hashlib.sha256(f"{it['id']}:{p}".encode()).hexdigest()[:8], 16)
            r = post(a.url + "/v1/chat/completions", {"model": a.model, "messages": msgs, "seed": seed,
                                                      **THINK_DEFAULTS, **extra}, timeout=3600, tries=2)
            ch = r["choices"][0]
            txt = ch["message"].get("content") or ""
            ans = txt.split("</think>")[-1] if "</think>" in txt or ch["message"].get("reasoning_content") else ""
            lab = parse_label(ans, labs)
            return {"id": it["id"], "family": it["family"], "split": it["split"], "perm": p, "order": order, "labels": labs,
                    "gold_label": gold_label(it, order), "ketertelmu": bool(it.get("ketertelmu")),
                    "x_type": it.get("x_type"), "pred": lab, "conf": 1.0 if lab else 0.0,
                    "probs": {x: float(x == lab) for x in labs}, "label_mass": 1.0 if lab else 0.0,
                    "valasz": ans.strip()[:60], "finish": ch.get("finish_reason"),
                    "gond_tokens": r.get("usage", {}).get("completion_tokens"),
                    "n_prompt_tokens": r.get("usage", {}).get("prompt_tokens"),
                    "latency_s": round(time.perf_counter() - t0, 2), "model": a.model, "frame": a.frame, "mode": "think"}
        else:
            r = post(a.url + "/v1/chat/completions", {"model": a.model, "messages": msgs, "max_tokens": 1, "temperature": 0,
                                                      "logprobs": True, "top_logprobs": 20, **extra})
            lp = {x: -9999.0 for x in labs}
            for t in r["choices"][0]["logprobs"]["content"][0]["top_logprobs"]:
                tt = t["token"].strip()
                if tt in lp:
                    lp[tt] = max(lp[tt], t["logprob"])
            n_tok = r.get("usage", {}).get("prompt_tokens")
        probs = restricted(lp)
        pred = max(probs, key=lambda k: probs[k])
        return {"id": it["id"], "family": it["family"], "split": it["split"], "perm": p, "order": order, "labels": labs,
                "gold_label": gold_label(it, order), "ketertelmu": bool(it.get("ketertelmu")), "x_type": it.get("x_type"),
                "pred": pred, "conf": probs[pred], "probs": probs, "label_mass": sum(math.exp(v) for v in lp.values()),
                "missing": [x for x, v in lp.items() if v <= -9999.0], "n_prompt_tokens": n_tok,
                "latency_s": round(time.perf_counter() - t0, 4), "model": a.model, "frame": a.frame}

    def safe(job):
        # egy hibás kérés (pl. a max-model-len fölötti prompt) ne állítsa le a futást: a hibák külön fájlba mennek, és
        # nem számítanak késznek, így újraindításkor újra próbálkozik velük
        try:
            return run(job), None
        except Exception as e:  # noqa: BLE001
            return None, {"id": job[0]["id"], "family": job[0]["family"], "perm": job[1], "hiba": str(e)[:300]}

    t0 = time.time()
    n_err = 0
    with open(out, "a", encoding="utf-8") as fh, open(out.with_suffix(".hibak.jsonl"), "a", encoding="utf-8") as eh, \
            ThreadPoolExecutor(a.concurrency) as ex:
        for i, (r, err) in enumerate(ex.map(safe, jobs), 1):
            if err:
                n_err += 1
                eh.write(json.dumps(err, ensure_ascii=False) + "\n")
            else:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
            if i % 2000 == 0:
                fh.flush()
                eh.flush()
                el = time.time() - t0
                print(f"  {i}/{len(jobs)} · {i / el:.1f}/s · hiba {n_err} · hátra ~{(len(jobs) - i) / (i / el) / 60:.0f} perc",
                      flush=True)
    print(f"kész: {len(jobs)} kiolvasás, ebből hiba {n_err}, {time.time() - t0:.0f} s", flush=True)
    if n_err > 0.05 * max(1, len(jobs)):
        raise SystemExit(f"a hibaarány {n_err / len(jobs):.1%} > 5%")


if __name__ == "__main__":
    main()
