#!/usr/bin/env python3
"""Blokkhatár-szonda — a cross-request prefix-cache eltérés HIPOTÉZISÉNEK tesztje.

Megfigyelés (round3, spark-dev): a szennyezett kar (A×1, majd B×10 ugyanarra a közös
prefixre) csak EGY itempáron bukott el ötből. A log szerint a cache blokkmérete 1600 token
(„Setting attention block size to 1600 tokens to ensure that attention page size is >= mamba
page size"), és a bukó pár az EGYETLEN, ahol a két kérés **eltérő számú teljes blokkot** zár le:

    bukó (D2):  A = 3169 tok → 1 teljes blokk   |  B = 3227 tok → 2 teljes blokk
    passzoló (D3): 2155 / 2182 → 1 és 1          |  (D5): 24384 / 24404 → 15 és 15

Hipotézis: az eltérés akkor keletkezik, ha az A kérés KEVESEBB teljes blokkot ír be a közös
prefixből, mint amennyit a B kérés visszaolvasna — vagyis a B utolsó, részben közös blokkja
egy olyan Mamba-állapotra épül, amit egy más hosszúságú kérés hagyott hátra.

A szonda ezt szintetikusan állítja elő: a közös prefix és a két suffix hosszát a szerver
/tokenize endpointjával méretezi pontosra, és két kart futtat:

  ELTERO   — A és B eltérő számú teljes blokkot zár le  → a hipotézis szerint FAIL
  AZONOS   — A és B ugyanannyit                         → a hipotézis szerint PASS

Mindkét kar saját, egyedi magvú kitöltő szöveget kap, így egy szerverindításon belül is
futtatható: a cache-ben semmi nem illeszkedik rájuk előzőleg.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.request
from pathlib import Path

RENDSZERPROMPT = "Válaszolj magyarul, tömören, pontosan egy mondatban."

def hivas(url, utvonal, payload, timeout=1800):
    req = urllib.request.Request(url.rstrip("/") + utvonal, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), (time.monotonic() - t0) * 1000

def tok_szam(url, model, szoveg):
    d, _ = hivas(url, "/tokenize", {"model": model, "prompt": szoveg}, timeout=120)
    return d["count"]

def keres(url, model, uzenet, max_tokens, top):
    payload = {"model": model, "temperature": 0.0, "top_p": 1, "max_tokens": max_tokens,
               "logprobs": True, "top_logprobs": top,
               "messages": [{"role": "system", "content": RENDSZERPROMPT},
                            {"role": "user", "content": uzenet}],
               "chat_template_kwargs": {"enable_thinking": False}}
    body, ms = hivas(url, "/v1/chat/completions", payload)
    ch = body["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    sigs = ["|".join(f"{x['token']}:{x['logprob']:.12g}" for x in (t.get("top_logprobs") or [])[:top])
            for t in lp]
    return {"teljes_hash": hashlib.sha256("|".join(sigs).encode()).hexdigest()[:16],
            "elso_token_sig_hash": hashlib.sha256((sigs[0] if sigs else "").encode()).hexdigest()[:16],
            "prompt_tok": body.get("usage", {}).get("prompt_tokens"), "ms": round(ms, 1)}

def kitolto(url, model, cel_tok, mag):
    """Determinisztikus kitöltő szöveg, a /tokenize-zal ±0,5 %-ra méretezve."""
    minta = " ".join(f"{mag}{i:06d}" for i in range(200))
    per_elem = tok_szam(url, model, minta) / 200
    db = max(1, int(cel_tok / per_elem))
    for _ in range(4):
        szoveg = " ".join(f"{mag}{i:06d}" for i in range(db))
        n = tok_szam(url, model, szoveg)
        if abs(n - cel_tok) / cel_tok <= 0.005:
            return szoveg
        db = max(1, int(db * cel_tok / n))
    return szoveg

def kar(url, model, args, cimke, prefix_tok, a_tok, b_tok, mag, valodi_prefix=None):
    # valódi dokumentum-prefix esetén a prefix_tok-ot a dokumentum adja (a szintetikus kitöltő
    # nagyon ismétlődő, és a QSA blokk-választása ott degenerált lehet)
    prefix = valodi_prefix if valodi_prefix is not None else kitolto(url, model, prefix_tok, f"p{mag}")
    # a suffixek a KÖZÖS prefix után jönnek — a teljes hossz az, ami a blokkszámot eldönti
    sa = kitolto(url, model, max(30, a_tok - prefix_tok), f"a{mag}")
    sb = kitolto(url, model, max(30, b_tok - prefix_tok), f"b{mag}")
    uz_a = f"Napló A:\n\n{prefix}\n\nKiegészítés:\n\n{sa}\n\nHány szakasz van a naplóban?"
    uz_b = f"Napló A:\n\n{prefix}\n\nKiegészítés:\n\n{sb}\n\nMi a napló utolsó azonosítója?"

    ki = {"kar": cimke, "cel": {"prefix": prefix_tok, "A": a_tok, "B": b_tok}, "futasok": []}
    ra = keres(url, model, uz_a, args.max_tokens, args.top)
    ki["A"] = ra
    blokk = args.blokkmeret
    print(f"  [{cimke}] A: prompt={ra['prompt_tok']} tok → {ra['prompt_tok']//blokk} teljes blokk "
          f"({ra['ms']:.0f} ms)", flush=True)
    for i in range(args.ismetles):
        rb = keres(url, model, uz_b, args.max_tokens, args.top)
        rb["futas"] = i + 1
        ki["futasok"].append(rb)
        if i == 0:
            print(f"  [{cimke}] B: prompt={rb['prompt_tok']} tok → {rb['prompt_tok']//blokk} teljes blokk", flush=True)
        print(f"      B#{i+1:2d} hash={rb['teljes_hash']} {rb['ms']:.0f} ms", flush=True)
    hashek = [f["teljes_hash"] for f in ki["futasok"]]
    ki["ertekeles"] = {"valtozatok": len(set(hashek)),
                       "elso_kulonbozik": hashek[0] != hashek[1] and len(set(hashek[1:])) == 1,
                       "A_blokk": ra["prompt_tok"] // blokk,
                       "B_blokk": ki["futasok"][0]["prompt_tok"] // blokk,
                       "eredmeny": "PASS" if len(set(hashek)) == 1 else "FAIL"}
    print(f"  [{cimke}] => {ki['ertekeles']['eredmeny']} "
          f"(A {ki['ertekeles']['A_blokk']} blokk vs B {ki['ertekeles']['B_blokk']} blokk, "
          f"{ki['ertekeles']['valtozatok']} változat)\n", flush=True)
    return ki

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--blokkmeret", type=int, default=1600)
    a.add_argument("--ismetles", type=int, default=6)
    a.add_argument("--max-tokens", type=int, default=32); a.add_argument("--top", type=int, default=20)
    a.add_argument("--mag", default="x1", help="egyedi mag — ugyanazon a szerveren minden futásnál MÁS")
    a.add_argument("--prefix-doc", help="valódi dokumentum a közös prefixhez (corpus/<név>.md)")
    a.add_argument("--valodi-kar", choices=["eltero", "azonos"], default="eltero",
                   help="valódi prefixnél: A és B eltérő vagy azonos teljes blokkszámmal")
    a.add_argument("--korpusz", help="a korpusz könyvtára (--prefix-doc mellé)")
    a.add_argument("--out", required=True)
    args = a.parse_args()
    B = args.blokkmeret

    valodi = None
    if args.prefix_doc:
        valodi = (Path(args.korpusz) / "corpus" / f"{args.prefix_doc}.md").read_text()
        pt = tok_szam(args.url, args.model, valodi)
        # a valódi prefix után a suffixeket úgy méretezzük, hogy A a következő blokkhatár ALATT,
        # B FELETTE legyen (a ~48 tokenes sablon-overheadet is beszámítva)
        kov = ((pt + 48) // B + 1) * B
        if args.valodi_kar == "eltero":
            args._a, args._b = kov - 120 - 48, kov + 60 - 48      # A: határ alatt, B: felette
        else:
            args._a, args._b = kov + 60 - 48, kov + 140 - 48      # mindkettő a határ felett
        print(f"[i] valódi prefix: {args.prefix_doc}.md = {pt} tok · következő blokkhatár: {kov} "
              f"→ A cél {args._a}, B cél {args._b}", flush=True)
    print(f"[i] blokkhatár-szonda · blokkméret={B} · {args.url}", flush=True)
    ki = {"args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S"), "karok": []}
    # ELTÉRŐ: A a 2. blokkhatár ALATT, B FELETTE (a D2-eset szintetikus mása).
    # ⚠️ A chat-sablon + rendszerprompt ~48 tokennel told el a tényleges prompt-hosszt a
    # kitöltő célhosszhoz képest — ezért az A célja bőven a határ alatt van.
    if valodi is not None:
        pt = tok_szam(args.url, args.model, valodi)
        ki["karok"].append(kar(args.url, args.model, args, f"{args.valodi_kar.upper()}-VALODI",
                              prefix_tok=pt, a_tok=args._a, b_tok=args._b,
                              mag=args.mag + "e", valodi_prefix=valodi))
        Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
        e = ki["karok"][0]["ertekeles"]
        print(f"[=] {args.valodi_kar.upper()}-VALODI: {e['eredmeny']}\n[>] {args.out}")
        return
    ki["karok"].append(kar(args.url, args.model, args, "ELTERO",
                          prefix_tok=int(B * 1.05), a_tok=int(B * 2) - 160, b_tok=int(B * 2) + 60,
                          mag=args.mag + "e"))
    # AZONOS: mindkettő ugyanabban a blokk-sávban (kontroll)
    ki["karok"].append(kar(args.url, args.model, args, "AZONOS",
                          prefix_tok=int(B * 1.05), a_tok=int(B * 2) + 60, b_tok=int(B * 2) + 120,
                          mag=args.mag + "n"))
    Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    e = [k["ertekeles"] for k in ki["karok"]]
    print(f"[=] ELTERO: {e[0]['eredmeny']} · AZONOS: {e[1]['eredmeny']}\n[>] {args.out}")

if __name__ == "__main__":
    main()
