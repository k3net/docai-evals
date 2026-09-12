#!/usr/bin/env python3
"""T2-01 partial-prefix-hit kísérlet — a round2/round3 A-kar egyetlen FAIL-jének izolálása.

Lelet: a determinizmus-szondában a T2-01 első futása MINDIG eltér a 2..10.-től, míg a
T3-01/T6-02/T10-05 bitre stabil. A T2-01 és a T3-01 UGYANAZT a D2.md-t használja, és a
szondában a T3-01 fut előbb → a T2-01 „hideg" futása valójában PARTIAL prefix-cache hit.

Két kar, MINDKETTŐ friss szerveren (ez a szkript egy karat futtat, a --kar kapcsolóval):

  tiszta  — T2-01 × N ELSŐKÉNT (a D2.md nincs a cache-ben): ha itt is eltér az 1. futás,
            a jelenség nem a partial hit, hanem a hideg prefill sajátja;
  szennyezett — T3-01 × 1, majd T2-01 × N: a D2 prefix a cache-ben van, MÁS suffixszel.

Ha a `tiszta` kar PASS és a `szennyezett` FAIL, akkor bizonyított, hogy a partial
prefix-cache hit út más logitokat ad, mint a teljes prefill — ez a #53798 / #54076
align-mode javítások célterülete.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, time, urllib.request
from pathlib import Path

RENDSZERPROMPT = (
    "Magyar dokumentumfeldolgozó asszisztens vagy. Kizárólag a megadott dokumentum alapján "
    "válaszolj. A választ pontosan a kért JSON-sémában add vissza, minden más szöveg nélkül. "
    "Ha egy kért adat nem szerepel a dokumentumban, az értéke legyen: \"nincs az iratban\"."
)

def uzenet(korpusz: Path, item):
    doksi = "\n\n".join(f"===== {n} =====\n\n" + (korpusz / "corpus" / n).read_text()
                        for n in item["dokumentumok"])
    return (doksi + "\n\n===== FELADAT =====\n\n" + item["prompt"]
            + "\n\n===== A VÁLASZ JSON-SÉMÁJA =====\n\n"
            + json.dumps(item["sema"], ensure_ascii=False, indent=2)
            + "\n\nKizárólag a fenti séma szerinti JSON-t add vissza.")

def sig(t, top_n):
    return "|".join(f"{x['token']}:{x['logprob']:.12g}" for x in (t.get("top_logprobs") or [])[:top_n])

def keres(url, model, uz, max_tokens, top):
    payload = {"model": model, "temperature": 0.0, "top_p": 1, "max_tokens": max_tokens,
               "logprobs": True, "top_logprobs": top,
               "messages": [{"role": "system", "content": RENDSZERPROMPT},
                            {"role": "user", "content": uz}],
               "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=1800) as r:
        body = json.load(r)
    ch = body["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    sigs = [sig(t, top) for t in lp]
    return {"teljes_hash": hashlib.sha256("|".join(sigs).encode()).hexdigest()[:16],
            "elso_token_sig_hash": hashlib.sha256((sigs[0] if sigs else "").encode()).hexdigest()[:16],
            "elso_token": lp[0].get("token") if lp else None,
            "token_db": len(lp), "prompt_tok": body.get("usage", {}).get("prompt_tokens"),
            "tartalom_sha": hashlib.sha256((ch["message"].get("content") or "").encode()).hexdigest()[:12],
            "ms": round((time.monotonic() - t0) * 1000, 1)}

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True)
    a.add_argument("--kar", choices=["tiszta", "szennyezett"], required=True)
    a.add_argument("--elo-item", default="T3-01", help="a szennyező kérés item-id-je (közös dokumentum)")
    a.add_argument("--cel-item", default="T2-01", help="a mért item-id")
    a.add_argument("--ismetles", type=int, default=10)
    a.add_argument("--max-tokens", type=int, default=48); a.add_argument("--top", type=int, default=20)
    a.add_argument("--out", required=True)
    args = a.parse_args()

    korpusz = Path(args.korpusz)
    items = {}
    for s in (korpusz / "items.jsonl").read_text().splitlines():
        if s.strip():
            d = json.loads(s); items[d["id"]] = d

    ki = {"kar": args.kar, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "elokeszites": [], "futasok": []}
    print(f"[i] kar={args.kar} · cél={args.cel_item}"
          + (f" · szennyező={args.elo_item}" if args.kar == "szennyezett" else "")
          + f" · {args.url}", flush=True)

    if args.kar == "szennyezett":
        # A D2.md prefix bekerül a cache-be egy MÁSIK feladattal (T3-01)
        r = keres(args.url, args.model, uzenet(korpusz, items[args.elo_item]), args.max_tokens, args.top)
        ki["elokeszites"].append({"item": args.elo_item, **r})
        print(f"  [elő] {args.elo_item} hash={r['teljes_hash']} prompt={r['prompt_tok']} {r['ms']:.0f} ms", flush=True)

    uz = uzenet(korpusz, items[args.cel_item])
    for i in range(args.ismetles):
        r = keres(args.url, args.model, uz, args.max_tokens, args.top)
        r["futas"] = i + 1
        ki["futasok"].append(r)
        print(f"  {args.cel_item} #{i+1:2d} hash={r['teljes_hash']} elso_tok_sig={r['elso_token_sig_hash']} "
              f"prompt={r['prompt_tok']} {r['ms']:.0f} ms", flush=True)

    hashek = [f["teljes_hash"] for f in ki["futasok"]]
    ki["ertekeles"] = {
        "valtozatok": len(set(hashek)),
        "elso_kulonbozik_a_tobbitol": hashek[0] != hashek[1] and len(set(hashek[1:])) == 1,
        "meleg_valtozatok": len(set(hashek[1:])),
        "szoveg_valtozatok": len({f["tartalom_sha"] for f in ki["futasok"]}),
        "eredmeny": "PASS" if len(set(hashek)) == 1 else "FAIL",
    }
    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    e = ki["ertekeles"]
    print(f"\n[=] {e['eredmeny']} — {e['valtozatok']} változat, az 1. eltér a többitől: "
          f"{e['elso_kulonbozik_a_tobbitol']}, meleg változatok: {e['meleg_valtozatok']}\n[>] {args.out}")

if __name__ == "__main__":
    main()
