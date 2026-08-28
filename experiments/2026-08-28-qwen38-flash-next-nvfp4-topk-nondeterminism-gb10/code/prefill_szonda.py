#!/usr/bin/env python3
"""Prefill-szonda: azonos prompt, max_tokens=1, logprobs — a 0. token logit-szórása.

A NVFP4-instabilitás elágazása a gondolkodás 0. tokenjénél van (ld. 03-nvfp4-instabilitas.md §3.2),
vagyis a PREFILL utáni logitvektor változik. Ez a szonda a dekódolástól függetlenül méri:
  · a kiválasztott 0. token futásonként,
  · a top-2 logprob-rést (holtverseny szélessége),
  · a top-N logprobok bitre azonosságát.
Nem restartol semmit, bármelyik élő szerveren fut; NE fusson egy izolációs kör KÖZBEN (köteg-összetétel!).
"""
import argparse, json, hashlib, sys, time, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from harness import RENDSZERPROMPT, felhasznaloi_uzenet

def hivas(url, model, uz, n_top, timeout):
    payload = {"model": model, "temperature": 0.0, "top_p": 1, "max_tokens": 1,
               "logprobs": True, "top_logprobs": n_top,
               "messages": [{"role": "system", "content": RENDSZERPROMPT},
                            {"role": "user", "content": uz}]}
    req = urllib.request.Request(url + "/v1/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), (time.monotonic() - t0) * 1000

if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--items", default="gt/items.jsonl")
    a.add_argument("--csak", default="T3-01,T6-02,T1-01,T10-05,T2-01,T8-01",
                   help="item-id-k; alapból 4 instabil + 2 stabil kontroll")
    a.add_argument("--ismetles", type=int, default=10); a.add_argument("--top", type=int, default=20)
    a.add_argument("--timeout", type=int, default=300); a.add_argument("--out", required=True)
    a.add_argument("--cimke", required=True)
    a = a.parse_args()
    items = {json.loads(l)["id"]: json.loads(l) for l in open(a.items) if l.strip()}
    ki = {"cimke": a.cimke, "args": vars(a), "eredmenyek": []}
    for id_ in a.csak.split(","):
        it = items[id_]; uz = felhasznaloi_uzenet(it)
        ph = hashlib.sha256(uz.encode()).hexdigest()[:12]
        futasok = []
        for i in range(a.ismetles):
            body, wall = hivas(a.url, a.model, uz, a.top, a.timeout)
            ch = body["choices"][0]
            lp = ((ch.get("logprobs") or {}).get("content") or [{}])[0]
            top = [(t.get("token"), t.get("logprob")) for t in (lp.get("top_logprobs") or [])]
            top_sorted = sorted(top, key=lambda z: -z[1]) if top else []
            res = (top_sorted[0][1] - top_sorted[1][1]) if len(top_sorted) > 1 else None
            futasok.append({"token": lp.get("token"), "logprob": lp.get("logprob"), "top": top_sorted,
                            "res_top2": res, "top_sha": hashlib.sha256(json.dumps(top_sorted).encode()).hexdigest()[:12],
                            "wall_ms": round(wall, 1), "usage": body.get("usage")})
        toks = [f["token"] for f in futasok]; shas = {f["top_sha"] for f in futasok}
        resek = [f["res_top2"] for f in futasok if f["res_top2"] is not None]
        print(f"{id_:8s} prompt-sha={ph} | 0. token: {len(set(toks))} féle {sorted(set(map(str,toks)))} | "
              f"top{a.top} bitre azonos: {len(shas)==1} ({len(shas)} változat) | top-2 rés: "
              f"min {min(resek):.4f} max {max(resek):.4f}" if resek else f"{id_}: nincs logprob", flush=True)
        ki["eredmenyek"].append({"id": id_, "prompt_sha": ph, "futasok": futasok,
                                 "tokenek": toks, "top_valtozatok": len(shas)})
        Path(a.out).write_text(json.dumps(ki, ensure_ascii=False, indent=1))
    print("mentve:", a.out)
