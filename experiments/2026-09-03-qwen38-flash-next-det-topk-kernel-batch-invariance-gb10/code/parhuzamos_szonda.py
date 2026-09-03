#!/usr/bin/env python3
"""Köteg-invariancia szonda — a soros determinizmus élesre fordítható-e.

A `logprob_szonda.py` soros kérésekkel mér (`Running: 1 reqs`). Élesben viszont a `night`-slot
cronjai és a chat párhuzamosan kérnek (`--max-num-seqs 4`), a vLLM kerneljei pedig NEM
batch-invariánsak: a köteg-összetétel megváltoztatja a redukciós alakokat, és így a logitokat is.
Ez a szonda azt méri, hogy a KÖTEGBEN futó kérés ugyanazt adja-e, mint ugyanaz a kérés egyedül.

Három elrendezés (mind ugyanazzal a cél-itemmel, ugyanazon a szerveren, azonos cache-állapotban):
  · REF   — soros referencia, a kötegek nélkül,
  · AZONOS — K darab BITRE AZONOS kérés egyszerre (a köteg homogén),
  · VEGYES — a cél-kérés + K-1 más hosszúságú kérés egyszerre (ez az éles helyzet).

⛔ A cél-item hash-ét mindhárom elrendezésben ugyanahhoz a REF hash-hez mérjük. Egy eltérés itt
   NEM „a modell hibája": a kernelek nem batch-invariánsak, ezt a vLLM sem ígéri. A kérdés az,
   hogy MEKKORA a hatás a mi shape-jeinken, mert ez szabja meg, mennyit ér a soros determinizmus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from logprob_szonda import RENDSZERPROMPT, felhasznaloi_uzenet, hivas, token_signature


def keres(url, model, uzenet, args):
    payload = {
        "model": model,
        "temperature": 0.0,
        "top_p": 1,
        "max_tokens": args.max_tokens,
        "logprobs": True,
        "top_logprobs": args.top,
        "messages": [
            {"role": "system", "content": RENDSZERPROMPT},
            {"role": "user", "content": uzenet},
        ],
    }
    if not args.thinking:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    body, wall = hivas(url, payload, args.timeout)
    ch = body["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    sig = [token_signature(t, args.top) for t in lp]
    return {
        "hash": hashlib.sha256("|".join(sig).encode()).hexdigest()[:16],
        "token_db": len(lp),
        "tartalom_sha": hashlib.sha256((ch["message"].get("content") or "").encode()).hexdigest()[:12],
        "ms": round(wall, 1),
    }


def koteg(url, model, uzenetek, args):
    """Egyszerre indított kérések — a szerver oldalán egy kötegbe kerülnek."""
    with ThreadPoolExecutor(max_workers=len(uzenetek)) as ex:
        jovok = [ex.submit(keres, url, model, u, args) for u in uzenetek]
        return [j.result() for j in jovok]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True)
    a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True)
    a.add_argument("--cel", default="T3-01", help="a cél-item, amit minden elrendezésben mérünk")
    a.add_argument("--zaj", default="T6-02,T10-05,T1-01",
                   help="a VEGYES köteg többi itemje (más prompt-hosszak)")
    a.add_argument("--korok", type=int, default=3)
    a.add_argument("--max-tokens", type=int, default=128)
    a.add_argument("--top", type=int, default=20)
    a.add_argument("--thinking", action="store_true")
    a.add_argument("--timeout", type=int, default=1800)
    a.add_argument("--cimke", required=True)
    a.add_argument("--out", required=True)
    args = a.parse_args()

    K = Path(args.korpusz)
    items = {}
    for sor in (K / "items.jsonl").read_text().splitlines():
        if sor.strip():
            d = json.loads(sor)
            items[d["id"]] = d
    cel = felhasznaloi_uzenet(K, items[args.cel])
    zajok = [felhasznaloi_uzenet(K, items[i]) for i in args.zaj.split(",")]

    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S")}
    print(f"[i] {args.cimke} — cél={args.cel}, zaj={args.zaj}, max_tokens={args.max_tokens}, "
          f"thinking={'ON' if args.thinking else 'OFF'}", flush=True)

    # --- 0. Bemelegítés: a cél és a zaj promptjai bekerülnek a prefix cache-be, hogy a
    #        későbbi eltérés a KÖTEGRE legyen visszavezethető, ne a cache-útra.
    print("  [bemelegítés]", flush=True)
    for u in [cel] + zajok:
        keres(args.url, args.model, u, args)

    # --- 1. Soros referencia
    ref = [keres(args.url, args.model, cel, args) for _ in range(args.korok)]
    ref_hash = ref[0]["hash"]
    ref_stabil = len({r["hash"] for r in ref}) == 1
    print(f"  REF (soros, {args.korok}×): hash={ref_hash} stabil={ref_stabil} "
          f"({ref[0]['ms']:.0f} ms)", flush=True)
    ki["ref"] = {"hash": ref_hash, "stabil": ref_stabil, "futasok": ref}

    # --- 2. AZONOS kötegek: K bitre azonos kérés egyszerre
    ki["azonos"] = {}
    for k in (2, 4):
        talalatok = []
        for kor in range(args.korok):
            e = koteg(args.url, args.model, [cel] * k, args)
            talalatok.extend(e)
            print(f"  AZONOS k={k} kör {kor+1}: " +
                  " ".join(f"{x['hash'][:8]}{'=' if x['hash'] == ref_hash else '≠'}" for x in e) +
                  f"  ({max(x['ms'] for x in e):.0f} ms)", flush=True)
        egyezik = sum(1 for x in talalatok if x["hash"] == ref_hash)
        ki["azonos"][f"k{k}"] = {"egyezik_reffel": egyezik, "osszes": len(talalatok),
                                 "valtozatok": len({x['hash'] for x in talalatok}),
                                 "futasok": talalatok}
        print(f"    -> k={k}: {egyezik}/{len(talalatok)} egyezik a soros referenciával, "
              f"{len({x['hash'] for x in talalatok})} különböző hash", flush=True)

    # --- 3. VEGYES köteg: cél + más hosszúságú kérések egyszerre
    talalatok = []
    for kor in range(args.korok):
        e = koteg(args.url, args.model, [cel] + zajok, args)
        talalatok.append(e[0])  # csak a cél-kérés eredménye vethető össze a reffel
        print(f"  VEGYES kör {kor+1}: cél={e[0]['hash'][:8]}"
              f"{'=' if e[0]['hash'] == ref_hash else '≠'}  "
              f"(köteg {len(e)} kérés, {max(x['ms'] for x in e):.0f} ms)", flush=True)
    egyezik = sum(1 for x in talalatok if x["hash"] == ref_hash)
    ki["vegyes"] = {"egyezik_reffel": egyezik, "osszes": len(talalatok),
                    "valtozatok": len({x['hash'] for x in talalatok}), "futasok": talalatok}
    print(f"    -> VEGYES: {egyezik}/{len(talalatok)} egyezik a soros referenciával, "
          f"{len({x['hash'] for x in talalatok})} különböző hash", flush=True)

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print(f"\n=== {args.cimke} kész — {args.out} ===")


if __name__ == "__main__":
    main()
