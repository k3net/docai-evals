#!/usr/bin/env python3
"""Prefix-cache helyességi szonda (runbook §10) — cold / partial hit / full hit.

A kérdés: a prefix-cache-ből visszaolvasott állapot (Mamba/QSA) BITRE ugyanazt a
logit-eloszlást adja-e, mint a hideg út. A round2 §3.1-ben látott T2-01-mintázat
(az 1. futás eltér, a 2..N egymással azonos) pont ezt a gyanút veti fel, ezért itt
a három útvonalat KÜLÖN, szándékosan előidézve mérjük:

  cold   — hosszú P prefix + A suffix, ELSŐ megjelenés (cache MISS)
  partial— ugyanaz a P prefix + B suffix (a prefix blokkjai HIT-elnek, a suffix nem)
  full   — a partial kérés PONTOS ismétlése (teljes HIT)

Kérésenként rögzítjük: prompt tok, cached tok, TTFT (első SSE-esemény),
első token + top-N logprob, teljes válasz SHA, tokenenkénti logprob-hash,
MTP elfogadási hossz (ha a /metrics adja), finish_reason.

⛔ A szöveg-azonosság NEM bizonyíték (round2 §3.4): a hash a logprob-listákra megy.
"""
from __future__ import annotations
import argparse, hashlib, json, statistics, sys, time, urllib.request
from pathlib import Path

RENDSZERPROMPT = (
    "Magyar dokumentumfeldolgozó asszisztens vagy. Kizárólag a megadott dokumentum alapján "
    "válaszolj. A választ pontosan a kért JSON-sémában add vissza, minden más szöveg nélkül. "
    "Ha egy kért adat nem szerepel a dokumentumban, az értéke legyen: \"nincs az iratban\"."
)

def token_signature(t, top_n):
    top = t.get("top_logprobs") or []
    return "|".join(f"{x['token']}:{x['logprob']:.12g}" for x in top[:top_n])

def hivas(url, payload, timeout):
    req = urllib.request.Request(
        url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Connection": "close"},
    )
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = json.load(r)
    return body, (time.monotonic() - t0) * 1000

def egy_keres(url, model, uzenet, args, cimke):
    payload = {
        "model": model, "temperature": 0.0, "top_p": 1,
        "max_tokens": args.max_tokens, "logprobs": True, "top_logprobs": args.top,
        "messages": [{"role": "system", "content": RENDSZERPROMPT},
                     {"role": "user", "content": uzenet}],
        "chat_template_kwargs": {"enable_thinking": False},
    }
    body, wall = hivas(url, payload, args.timeout)
    ch = body["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    sigs = [token_signature(t, args.top) for t in lp]
    usage = body.get("usage", {})
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
    return {
        "ut": cimke,
        "teljes_hash": hashlib.sha256("|".join(sigs).encode()).hexdigest()[:16],
        "elso_token": lp[0].get("token") if lp else None,
        "elso_token_top": sigs[0][:200] if sigs else None,
        "elso_token_top_hash": hashlib.sha256((sigs[0] if sigs else "").encode()).hexdigest()[:16],
        "token_db": len(lp),
        "tartalom_sha": hashlib.sha256((ch["message"].get("content") or "").encode()).hexdigest()[:12],
        "prompt_tok": usage.get("prompt_tokens"),
        "cached_tok": cached,
        "completion_tok": usage.get("completion_tokens"),
        "finish": ch.get("finish_reason"),
        "ms": round(wall, 1),
    }

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True)
    a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True)
    a.add_argument("--prefix-doc", default="D6,D3,D4",
                   help="a hosszú közös prefixet adó dokumentumok (vesszős lista, corpus/<név>.md)")
    a.add_argument("--ismetles", type=int, default=10, help="a partial+full pár ismétlésszáma")
    a.add_argument("--max-tokens", type=int, default=48)
    a.add_argument("--top", type=int, default=20)
    a.add_argument("--timeout", type=int, default=1800)
    a.add_argument("--cimke", required=True)
    a.add_argument("--out", required=True)
    args = a.parse_args()

    korpusz = Path(args.korpusz)
    prefix = "\n\n".join(
        f"===== {n}.md =====\n\n" + (korpusz / "corpus" / f"{n}.md").read_text()
        for n in args.prefix_doc.split(",")
    )
    # Két KÜLÖNBÖZŐ suffix ugyanarra a prefixre: a blokk-határ utáni rész tér el.
    suffix_a = "\n\n===== FELADAT =====\n\nSorold fel a dokumentum három legfontosabb dátumát JSON-tömbként."
    suffix_b = "\n\n===== FELADAT =====\n\nSorold fel a dokumentumban szereplő összes összeget JSON-tömbként."
    uz_a, uz_b = prefix + suffix_a, prefix + suffix_b

    ki = {"cimke": args.cimke, "args": vars(args),
          "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "prefix_kar": len(prefix), "keresek": []}
    print(f"[i] {args.cimke} — {args.url} · prefix {args.prefix_doc} ({len(prefix)} kar) · "
          f"{args.ismetles}× partial/full", flush=True)

    # 1) COLD: a P prefix ELSŐ megjelenése (suffix A)
    r = egy_keres(args.url, args.model, uz_a, args, "cold")
    ki["keresek"].append(r)
    print(f"  cold    hash={r['teljes_hash']} prompt={r['prompt_tok']} cached={r['cached_tok']} {r['ms']:.0f} ms", flush=True)

    # 2) PARTIAL + 3) FULL, ismételve
    for i in range(args.ismetles):
        ut = "partial" if i == 0 else "full"
        r = egy_keres(args.url, args.model, uz_b, args, ut)
        r["kor"] = i + 1
        ki["keresek"].append(r)
        print(f"  {ut:7s} #{i+1:2d} hash={r['teljes_hash']} prompt={r['prompt_tok']} "
              f"cached={r['cached_tok']} {r['ms']:.0f} ms", flush=True)

    # Értékelés
    part = [r for r in ki["keresek"] if r["ut"] == "partial"]
    full = [r for r in ki["keresek"] if r["ut"] == "full"]
    ki["ertekeles"] = {
        "partial_full_hash_egyezik": bool(part and full) and len({r["teljes_hash"] for r in part + full}) == 1,
        "full_valtozatok": len({r["teljes_hash"] for r in full}),
        "partial_elso_token_top_hash": part[0]["elso_token_top_hash"] if part else None,
        "full_elso_token_top_hash_valtozatok": len({r["elso_token_top_hash"] for r in full}),
        "cold_cached_tok": ki["keresek"][0]["cached_tok"],
        "eredmeny": None,
    }
    ki["ertekeles"]["eredmeny"] = "PASS" if (
        ki["ertekeles"]["partial_full_hash_egyezik"] and ki["ertekeles"]["full_valtozatok"] == 1
    ) else "FAIL"
    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print(f"\n[=] {ki['ertekeles']['eredmeny']} — partial/full hash egyezik: "
          f"{ki['ertekeles']['partial_full_hash_egyezik']}, full változatok: "
          f"{ki['ertekeles']['full_valtozatok']}\n[>] {args.out}")

if __name__ == "__main__":
    main()
