#!/usr/bin/env python3
"""Round8 M6 — teljesítmény egy karon (streaming, greedy).

  ttft      hideg TTFT 8K / 32K / 64K token (egyedi salt), cellánként 2x
  decode    ms/token c=1 és c=4, ~1K és ~60K kontextuson, 1000 kényszerített tokennel
            (a prefill egy priming kéréssel cache-be kerül, így a decode-cella TTFT-je kicsi;
             a ms/token a TTFT UTÁNI szakaszból számol), cellánként 2 futás
  mtp       a /metrics spec-decode számlálóinak deltája decode-cellánként (elfogadási arány)
"""
from __future__ import annotations
import argparse, json, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def stream(url, payload, timeout=3600):
    payload = dict(payload, stream=True, stream_options={"include_usage": True})
    req = urllib.request.Request(url.rstrip("/") + "/v1/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic(); t1 = None; usage = None; n_chunk = 0
    with urllib.request.urlopen(req, timeout=timeout) as r:
        for raw in r:
            line = raw.decode().strip()
            if not line.startswith("data:") or line == "data: [DONE]":
                continue
            d = json.loads(line[5:])
            if d.get("choices") and d["choices"][0].get("text"):
                n_chunk += 1
                if t1 is None:
                    t1 = time.monotonic()
            if d.get("usage"):
                usage = d["usage"]
    t2 = time.monotonic()
    gen = (usage or {}).get("completion_tokens") or 0
    return {"ttft_ms": round(((t1 or t2) - t0) * 1000, 1), "ossz_ms": round((t2 - t0) * 1000, 1), "gen_tok": gen,
            "ms_per_tok": round((t2 - (t1 or t2)) * 1000 / max(1, gen - 1), 3),
            "cached": ((usage or {}).get("prompt_tokens_details") or {}).get("cached_tokens"),
            "prompt_tok": (usage or {}).get("prompt_tokens")}


def metrikak(url):
    txt = urllib.request.urlopen(url.rstrip("/") + "/metrics", timeout=30).read().decode()
    out = {}
    for l in txt.splitlines():
        if l.startswith("vllm:spec_decode_num_") and "_total" in l.split("{")[0]:
            k = l.split("{")[0].split(" ")[0]
            out[k] = out.get(k, 0.0) + float(l.rsplit(" ", 1)[1])
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True); a.add_argument("--mag", required=True)
    a.add_argument("--cimke", default=""); a.add_argument("--out", required=True)
    a.add_argument("--reszek", default="ttft,decode"); a.add_argument("--ismetles", type=int, default=2)
    args = a.parse_args()
    U, M = args.url, args.model
    szoveg = (Path(args.korpusz) / "corpus" / "D7.md").read_text()
    ids = json.load(urllib.request.urlopen(urllib.request.Request(
        U + "/tokenize", data=json.dumps({"model": M, "prompt": szoveg, "add_special_tokens": False}).encode(),
        headers={"Content-Type": "application/json"})))["tokens"]
    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "ttft": [], "decode": []}
    base = {"model": M, "temperature": 0.0, "top_p": 1}
    if "ttft" in args.reszek:
        for n in (8192, 32768, 65536):
            for i in range(args.ismetles):
                r = stream(U, dict(base, prompt=ids[:n], max_tokens=1, cache_salt=f"r8pt-{args.mag}-{n}-{i}"))
                r.update(ctx=n, futas=i + 1); ki["ttft"].append(r)
                print(f"TTFT {n:>6}: {r['ttft_ms']:>9.1f} ms (cached={r['cached']})", flush=True)
    if "decode" in args.reszek:
        for ctx in (1000, 40000):   # v2: 60K helyett 40K, hogy c=4 mellett a prime-olt prefix bent maradjon a KV-ban
            for c in (1, 4):
                salts = [f"r8pd-{args.mag}-{ctx}-{c}-{j}" for j in range(c)]
                prompts = [ids[j * 7: j * 7 + ctx] for j in range(c)]   # streamenként külön prompt
                for s, p in zip(salts, prompts):                          # priming: prefill a cache-be
                    stream(U, dict(base, prompt=p, max_tokens=1, cache_salt=s))
                for i in range(args.ismetles):
                    m0 = metrikak(U)
                    with ThreadPoolExecutor(c) as ex:
                        rs = list(ex.map(lambda sp: stream(U, dict(base, prompt=sp[1], max_tokens=1000, min_tokens=1000,
                                                                   ignore_eos=True, cache_salt=sp[0])),
                                         zip(salts, prompts)))
                    m1 = metrikak(U)
                    dm = {k.split(":")[1]: m1.get(k, 0) - m0.get(k, 0) for k in m1}
                    acc = dm.get("spec_decode_num_accepted_tokens_total"); drf = dm.get("spec_decode_num_draft_tokens_total")
                    cel = {"ctx": ctx, "c": c, "futas": i + 1, "ms_per_tok": [r["ms_per_tok"] for r in rs],
                           "ms_per_tok_atlag": round(sum(r["ms_per_tok"] for r in rs) / c, 3),
                           "cached": [r["cached"] for r in rs], "ttft_ms": [r["ttft_ms"] for r in rs],
                           "spec": dm, "elfogadas": round(acc / drf, 4) if drf else None}
                    ki["decode"].append(cel)
                    print(f"decode ctx={ctx:>5} c={c}: {cel['ms_per_tok_atlag']:.2f} ms/tok "
                          f"(elfogadás {cel['elfogadas']}, cached {cel['cached']})", flush=True)
    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print(f"[>] {args.out}")


if __name__ == "__main__":
    main()
