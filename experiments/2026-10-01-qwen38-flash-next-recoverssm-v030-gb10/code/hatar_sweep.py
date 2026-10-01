#!/usr/bin/env python3
"""Round8 M3 — blokkhatár-sweep (a vllm#58863 `5567cc1` boundary-oszlop és a `3388ba1` race élő próbája).

Token-id promptok `k*B - d` hosszal (valódi magyar szöveg tokenjei, a D7 elejéről), greedy, `/v1/completions`.
Promptonként:
  hideg1, hideg2   egyedi salttal          -> a szerver determinisztikus-e (azonos kimenet)
  prime, hit       közös salttal           -> a cache-hitből számolt kimenet = hideg1?
  folyt_hit        prompt + prime kimenete + rövid toldás, közös salttal -> a DECODE alatt (blokkhatár
                   átlépésekor) írt állapotra épülő találat
  folyt_hideg      ugyanez egyedi salttal  -> referencia
Eltérésnél az első eltérő kimeneti pozíció és annak abszolút fázisa ((L + j) mod B) is rögzül: a
stevededrick-féle hiba blokkhatár után 0–10 tokennel kezdődik.
"""
from __future__ import annotations
import argparse, json, time, urllib.request
from pathlib import Path


def hivas(url, ut, payload, timeout=1800):
    req = urllib.request.Request(url.rstrip("/") + ut, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def gen(url, model, ids, n, salt):
    d = hivas(url, "/v1/completions", {
        "model": model, "prompt": ids, "max_tokens": n, "temperature": 0.0, "top_p": 1,
        "ignore_eos": True, "logprobs": 1, "return_tokens_as_token_ids": True, "cache_salt": salt})
    ch = d["choices"][0]
    toks = [int(t.split(":", 1)[1]) for t in ch["logprobs"]["tokens"]]
    u = d.get("usage", {})
    return toks, (u.get("prompt_tokens_details") or {}).get("cached_tokens")


def elso_elteres(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return None if len(a) == len(b) else min(len(a), len(b))


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True); a.add_argument("--blokk", type=int, default=1600)
    a.add_argument("--k", default="1,2,4,8"); a.add_argument("--d", default="0,1,2,3,5,10")
    a.add_argument("--gen", type=int, default=256); a.add_argument("--folyt-gen", type=int, default=64)
    a.add_argument("--mag", required=True); a.add_argument("--cimke", default="")
    a.add_argument("--out", required=True)
    args = a.parse_args()
    B = args.blokk
    szoveg = (Path(args.korpusz) / "corpus" / "D7.md").read_text()
    ids = hivas(args.url, "/tokenize", {"model": args.model, "prompt": szoveg, "add_special_tokens": False})["tokens"]
    toldas = hivas(args.url, "/tokenize", {"model": args.model, "add_special_tokens": False,
                                           "prompt": "\n\nFoglald össze röviden a fentieket."})["tokens"]
    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "promptok": []}
    for k in map(int, args.k.split(",")):
        for d in map(int, args.d.split(",")):
            L = k * B - d
            p = ids[:L]
            s = f"r8m3-{args.mag}-{L}"
            h1, _ = gen(args.url, args.model, p, args.gen, s + "-h1")
            h2, _ = gen(args.url, args.model, p, args.gen, s + "-h2")
            pr, c_pr = gen(args.url, args.model, p, args.gen, s)
            hi, c_hi = gen(args.url, args.model, p, args.gen, s)
            fp = p + pr + toldas
            fh, c_fh = gen(args.url, args.model, fp, args.folyt_gen, s)
            fc, _ = gen(args.url, args.model, fp, args.folyt_gen, s + "-fh")
            r = {"L": L, "k": k, "d": d, "cached": {"prime": c_pr, "hit": c_hi, "folyt_hit": c_fh},
                 "hideg_det": h1 == h2, "hideg_elso_elteres": elso_elteres(h1, h2),
                 "prime_vs_hideg": elso_elteres(pr, h1), "hit_vs_hideg": elso_elteres(hi, h1),
                 "folyt_len": len(fp), "folyt_hit_vs_hideg": elso_elteres(fh, fc)}
            for kulcs, base in (("hit_vs_hideg", L), ("folyt_hit_vs_hideg", len(fp))):
                j = r[kulcs]
                r[kulcs + "_fazis"] = None if j is None else (base + j) % B
            ki["promptok"].append(r)
            jel = "OK" if (r["hideg_det"] and r["hit_vs_hideg"] is None and r["folyt_hit_vs_hideg"] is None) else "ELTÉR"
            print(f"L={L:>6} (k={k} d={d:>2}) hideg-det={r['hideg_det']} hit≠hideg@{r['hit_vs_hideg']} "
                  f"folyt-hit≠hideg@{r['folyt_hit_vs_hideg']} cached={r['cached']} {jel}", flush=True)
            Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    P = ki["promptok"]
    ki["osszeg"] = {"n": len(P), "hideg_nemdet": sum(not r["hideg_det"] for r in P),
                    "hit_elteres": sum(r["hit_vs_hideg"] is not None for r in P),
                    "folyt_elteres": sum(r["folyt_hit_vs_hideg"] is not None for r in P),
                    "folyt_cached_pozitiv": sum((r["cached"]["folyt_hit"] or 0) > 0 for r in P)}
    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print(f"[=] {ki['osszeg']} -> {args.out}")


if __name__ == "__main__":
    main()
