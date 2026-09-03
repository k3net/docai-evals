#!/usr/bin/env python3
"""Teljes-generálásos logprob-szonda — a round1 prefill-szonda vak foltjára.

A round1 `src/prefill_szonda.py` `max_tokens=1`-gyel mért, vagyis KIZÁROLAG a prefill
utáni 0. token logitvektorát. A 2026-09-02-i upstream lelet (vllm#54945) szerint a
FlashInfer CUTLASS NVFP4 MoE `use_fused_finalize=True` útja atomicokkal redukál, tehát
a nemdeterminizmus a DECODE lépésekben (és a második prefill-chunkban) is keletkezhet —
ezt a round1 mérése nem tudta látni. A szerverünk logja `Using 'FLASHINFER_CUTLASS'
NvFp4 MoE backend`, tehát az érintett kernelen futunk.

Ez a szonda a teljes generálásra hash-eli tokenenként a top-N logprob-listát:
  · minden itemre N azonos kérés, szigorúan sorosan (a köteg-összetétel is bemenet!),
  · tokenenkénti signature = sha256("token:logprob" × top-N), teljes hash = ezek hash-e,
  · külön jelenti az 1. (hideg / prefix-cache MISS) és a 2..N (cache-HIT) futásokat,
    mert prod-konfigban `--enable-prefix-caching` van, és a két út logitjai eltérhetnek,
  · megadja az első eltérő token indexét — a „szöveg azonos, logit nem" esetet is látja.

⛔ A látható válasz azonossága NEM elég: a greedy argmax akkor is stabil maradhat, ha a
   mögöttes logitok eltérnek — az élesben ez a következő tokennél billen át.

Futtatás a laptopról (a spark-dev vLLM-je HTTP-n, GPU-t nem terhelünk):
    python3 logprob_szonda.py --url http://10.10.0.5:18380 \\
        --model qwen38-flash-next-nvfp4 --korpusz /path/to/kie \\
        --cimke A-baseline-exacttopk1 --out eredmenyek/szonda-A.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# A round1 harness (src/harness.py) rendszerprompt- és üzenetépítése, bájtra azonosan —
# másik prompt más eloszlást ad, és az összevetés a round1 méréseivel elveszne.
RENDSZERPROMPT = (
    "Magyar dokumentumfeldolgozó asszisztens vagy. Kizárólag a megadott dokumentum alapján "
    "válaszolj. A választ pontosan a kért JSON-sémában add vissza, minden más szöveg nélkül. "
    "Ha egy kért adat nem szerepel a dokumentumban, az értéke legyen: \"nincs az iratban\"."
)


def dokumentum_szoveg(korpusz: Path, nevek):
    return "\n\n".join(
        f"===== {n} =====\n\n" + (korpusz / "corpus" / n).read_text() for n in nevek
    )


def felhasznaloi_uzenet(korpusz: Path, item):
    return (
        dokumentum_szoveg(korpusz, item["dokumentumok"])
        + "\n\n===== FELADAT =====\n\n"
        + item["prompt"]
        + "\n\n===== A VÁLASZ JSON-SÉMÁJA =====\n\n"
        + json.dumps(item["sema"], ensure_ascii=False, indent=2)
        + "\n\nKizárólag a fenti séma szerinti JSON-t add vissza."
    )


def hivas(url, payload, timeout):
    """Egy kérés. `Connection: close` — a round1-ben mért néma, 49 perces blokkolás ellen."""
    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Connection": "close"},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), (time.monotonic() - t0) * 1000


def token_signature(token_entry, top_n):
    """Egy generált token signature-je: a top-N jelölt (token, logprob) kanonikus alakja.

    A `%.12g` a float teljes információját viszi; a kiválasztott token maga is benne van
    a top_logprobs listában, így a rangsor-változás is látszik, nem csak az argmax.
    """
    top = (token_entry.get("top_logprobs") or [])[:top_n]
    kanon = "|".join(f"{t.get('token')!r}:{t.get('logprob'):.12g}" for t in top)
    return hashlib.sha256(kanon.encode()).hexdigest()[:12]


def elso_elteres(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return i
    return len(a) if len(a) != len(b) else None


def szonda_item(url, model, uzenet, args):
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

    futasok = []
    for i in range(args.ismetles):
        body, wall = hivas(url, payload, args.timeout)
        ch = body["choices"][0]
        tartalom = ch["message"].get("content") or ""
        gondolat = ch["message"].get("reasoning_content") or ""
        lp = (ch.get("logprobs") or {}).get("content") or []
        tokensig = [token_signature(t, args.top) for t in lp]
        futasok.append(
            {
                "futas": i + 1,
                "teljes_hash": hashlib.sha256("|".join(tokensig).encode()).hexdigest()[:16],
                "token_hashek": tokensig,
                "token_db": len(lp),
                "elso_token": lp[0].get("token") if lp else None,
                "finish": ch.get("finish_reason"),
                "tartalom_sha": hashlib.sha256(tartalom.encode()).hexdigest()[:12],
                "gondolat_sha": hashlib.sha256(gondolat.encode()).hexdigest()[:12],
                "gondolat_kar": len(gondolat),
                "ms": round(wall, 1),
                "usage": body.get("usage", {}),
            }
        )
        print(f"      #{i+1:2d}  hash={futasok[-1]['teljes_hash']}  "
              f"tok={futasok[-1]['token_db']:4d}  {futasok[-1]['ms']:8.0f} ms  "
              f"finish={futasok[-1]['finish']}", flush=True)
    return futasok


def ertekel(futasok):
    """PASS/FAIL + a hideg (1.) és a cache-melegített (2..N) futások külön bontása."""
    hashek = [f["teljes_hash"] for f in futasok]
    meleg = hashek[1:]
    elteres = None
    if len(set(hashek)) > 1:
        alap = futasok[0]["token_hashek"]
        eltero = [
            elso_elteres(alap, f["token_hashek"])
            for f in futasok[1:]
            if f["teljes_hash"] != hashek[0]
        ]
        elteres = min(x for x in eltero if x is not None) if any(
            x is not None for x in eltero) else None
    return {
        "valtozatok_mind": len(set(hashek)),
        "valtozatok_meleg": len(set(meleg)) if meleg else 0,
        "hideg_egyezik_meleggel": bool(meleg) and hashek[0] == meleg[0],
        "elso_eltero_token": elteres,
        "szoveg_valtozatok": len({f["tartalom_sha"] for f in futasok}),
        "gondolat_valtozatok": len({f["gondolat_sha"] for f in futasok}),
        "eredmeny": "PASS" if len(set(hashek)) == 1 else "FAIL",
        "ms_median": round(statistics.median(f["ms"] for f in futasok), 1),
    }


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True)
    a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True,
                   help="könyvtár items.jsonl-lel és corpus/ alkönyvtárral")
    a.add_argument("--csak", default="T3-01,T6-02,T10-05,T2-01",
                   help="item-id-k; alapból 3 round1-instabil + 1 stabil kontroll")
    a.add_argument("--ismetles", type=int, default=10)
    a.add_argument("--max-tokens", type=int, default=48)
    a.add_argument("--top", type=int, default=20)
    a.add_argument("--thinking", action="store_true",
                   help="gondolkodó mód (alapból enable_thinking=False a gyors körhöz)")
    a.add_argument("--timeout", type=int, default=1800)
    a.add_argument("--cimke", required=True)
    a.add_argument("--out", required=True)
    args = a.parse_args()

    korpusz = Path(args.korpusz)
    items = {}
    for sor in (korpusz / "items.jsonl").read_text().splitlines():
        if sor.strip():
            d = json.loads(sor)
            items[d["id"]] = d

    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "eredmenyek": []}
    print(f"[i] {args.cimke} — {args.url} / {args.model} · thinking="
          f"{'ON' if args.thinking else 'OFF'} · max_tokens={args.max_tokens} · "
          f"{args.ismetles}× ismétlés", flush=True)

    for id_ in args.csak.split(","):
        if id_ not in items:
            sys.exit(f"!! nincs ilyen item: {id_}")
        uz = felhasznaloi_uzenet(korpusz, items[id_])
        print(f"\n  {id_}  (prompt {len(uz)} kar, sha "
              f"{hashlib.sha256(uz.encode()).hexdigest()[:12]})", flush=True)
        futasok = szonda_item(args.url, args.model, uz, args)
        ert = ertekel(futasok)
        print(f"    -> {ert['eredmeny']}: {ert['valtozatok_mind']} különböző hash "
              f"{args.ismetles} futásból (melegen {ert['valtozatok_meleg']}), "
              f"első eltérő token: {ert['elso_eltero_token']}, "
              f"szövegváltozat: {ert['szoveg_valtozatok']}", flush=True)
        ki["eredmenyek"].append({"id": id_, "prompt_kar": len(uz), **ert, "futasok": futasok})

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ki, ensure_ascii=False, indent=2))

    bukott = [e["id"] for e in ki["eredmenyek"] if e["eredmeny"] == "FAIL"]
    print(f"\n=== {args.cimke}: {len(ki['eredmenyek']) - len(bukott)}/"
          f"{len(ki['eredmenyek'])} item PASS ===")
    if bukott:
        print(f"    FAIL: {', '.join(bukott)}")
    print(f"    {out}")


if __name__ == "__main__":
    main()
