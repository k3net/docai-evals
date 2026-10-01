#!/usr/bin/env python3
"""Round4 — checkpoint-küszöb szonda (a round3 cross-request prefix-cache eltérés gyökérokához).

HIPOTÉZIS (a 2026-09-13-i külső elemzés mechanizmusából levezetve, CPU-forrásszondával 8/8-ra
illesztve a round3 méréseire): a `Scheduler._mamba_block_aligned_split` MTP (use_eagle=True)
mellett egy TELJES blokkal visszaveszi az utolsó menthető pozíciót:

    last_cache_position = N - N % 1600 ;  ha use_eagle: -= 1600

ezért egy N < 3200 tokenes kérés EGYETLEN prefill-darabban fut le, és NEM ment 1600-as
Mamba/GDN-checkpointot. Ha az A kérés nem ment, de a B (N >= 3200) igen, akkor B ISMÉTLÉSEKOR
a KV-blokkok A-tól, a Mamba-állapot B-től származik -> eltérő eredetű tenzorok egyesülnek.

JÓSLAT (2x2, azonos közös dokumentum-prefixszel, cellánként külön cache_salt):
    A<3200 & B>=3200 -> FAIL     A>=3200 & B>=3200 -> PASS
    A<3200 & B<3200  -> PASS     A>=3200 & B<3200  -> PASS   (valódi teljes hit, AZONOS eredet)

A round3-as szondákhoz képest itt rögzítjük a tényleges `cached_tokens` értéket és a nyers
top-20 listát is (a hash-en kívül), mert a puszta aláírás-hash nem mondja meg, hogy a jelöltek
numerikusan mozdultak-e el, vagy csak a sorrendjük cserélődött.
"""
from __future__ import annotations
import argparse, hashlib, json, time, urllib.request
from pathlib import Path

RENDSZERPROMPT = ("Magyar dokumentumfeldolgozó asszisztens vagy. Kizárólag a megadott dokumentum "
                  "alapján válaszolj, tömören.")

def hivas(url, ut, payload, timeout=1800):
    req = urllib.request.Request(url.rstrip("/") + ut, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), (time.monotonic() - t0) * 1000

def uzenetek(szoveg):
    return [{"role": "system", "content": RENDSZERPROMPT}, {"role": "user", "content": szoveg}]

def chat_tok(url, model, szoveg):
    """A chat-sablonnal RENDERELT prompt tokenszáma — ez az, amit a scheduler lát."""
    d, _ = hivas(url, "/tokenize", {"model": model, "messages": uzenetek(szoveg),
                                    "add_generation_prompt": True,
                                    "chat_template_kwargs": {"enable_thinking": False}}, timeout=120)
    return d["count"]

def meretez(url, model, sablon, cel):
    """round8: biszekció — a legkisebb kitöltő-elemszám, amelyre a renderelt prompt >= `cel` token.
    A kitöltő a magtól FÜGGETLEN, így ugyanaz a cella minden karon bájtra azonos promptot ad."""
    lo, hi = 0, 16
    while chat_tok(url, model, sablon(hi)) < cel:
        lo, hi = hi, hi * 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if chat_tok(url, model, sablon(mid)) >= cel:
            hi = mid
        else:
            lo = mid
    sz = sablon(hi)
    return sz, chat_tok(url, model, sz), hi

def keres(url, model, szoveg, max_tokens, top, salt, nyers_top_db):
    payload = {"model": model, "temperature": 0.0, "top_p": 1, "max_tokens": max_tokens,
               "logprobs": True, "top_logprobs": top, "messages": uzenetek(szoveg),
               "chat_template_kwargs": {"enable_thinking": False},
               "return_tokens_as_token_ids": True, "cache_salt": salt}
    body, ms = hivas(url, "/v1/chat/completions", payload)
    ch = body["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") or []
    def sor(t): return (t.get("top_logprobs") or [])[:top]
    api_sig = ["|".join(f"{x['token']}:{x['logprob']:.12g}" for x in sor(t)) for t in lp]
    # kanonizált: token-azonosító szerint rendezve -> a puszta sorrendcsere nem számít eltérésnek
    kan_sig = ["|".join(f"{x['token']}:{x['logprob']:.12g}" for x in sorted(sor(t), key=lambda x: x["token"]))
               for t in lp]
    u = body.get("usage", {})
    return {
        "api_hash": hashlib.sha256("|".join(api_sig).encode()).hexdigest()[:16],
        "kanon_hash": hashlib.sha256("|".join(kan_sig).encode()).hexdigest()[:16],
        "elso_token_api_hash": hashlib.sha256((api_sig[0] if api_sig else "").encode()).hexdigest()[:16],
        "prompt_tok": u.get("prompt_tokens"),
        "cached_tok": (u.get("prompt_tokens_details") or {}).get("cached_tokens"),
        "tartalom_sha": hashlib.sha256((ch["message"].get("content") or "").encode()).hexdigest()[:12],
        "nyers_top": [sor(t) for t in lp[:nyers_top_db]],
        "ms": round(ms, 1),
    }

def cella(url, model, args, cimke, doksi, cel_a, cel_b, mag):
    kit = lambda pre: (lambda db: f"{doksi}\n\n===== KIEGÉSZÍTÉS =====\n\n"
                                  + " ".join(f"{pre}{i:06d}" for i in range(db))
                                  + "\n\n===== FELADAT =====\n\nFoglald össze egy mondatban.")
    sa, na, dba = meretez(url, model, kit("a"), cel_a)
    sb, nb, dbb = meretez(url, model, kit("b"), cel_b)
    salt = f"round4-{mag}"  # round8: a mag futásonként egyedi
    ki = {"cella": cimke, "cel": {"A": cel_a, "B": cel_b}, "tenyleges": {"A": na, "B": nb},
          "kitolto_elem": {"A": dba, "B": dbb}, "cache_salt": salt, "futasok": []}
    # round8: általánosított jóslat. Hidegen, 0-ról, MTP (eagle block drop) mellett az első darab
    # L = floor(N/B)*B - B-ig fut, és csak L-ben ment állapotot (a CPU-szonda szerint v0.29 és v0.30 is).
    # FAIL, ha B olyan p checkpointot ment, amelyet A nem, de A KV-ja lefedi (p < A hossza):
    # B ismétlésekor a KV A-tól, az állapot B-től jön.
    B_ = args.blokkmeret
    ck = lambda n: [n // B_ * B_ - B_] if n // B_ * B_ - B_ > 0 else []
    ca_, cb_ = ck(na), ck(nb)
    j_a, j_b = bool(ca_), bool(cb_)
    ki["joslat"] = "FAIL" if any(p not in ca_ and p < na for p in cb_) else "PASS"
    ki["ckpt"] = {"A_ir_checkpointot": j_a, "B_ir_checkpointot": j_b, "A_ckpt": ca_, "B_ckpt": cb_}
    print(f"\n[{cimke}] A={na} tok (ckpt: {ca_}) · B={nb} tok (ckpt: {cb_}) · jóslat: {ki['joslat']}", flush=True)

    ra = keres(url, model, sa, args.max_tokens, args.top, salt, args.nyers_top)
    ki["A"] = ra
    print(f"  A     prompt={ra['prompt_tok']} cached={ra['cached_tok']} {ra['ms']:.0f} ms", flush=True)
    for i in range(args.ismetles):
        rb = keres(url, model, sb, args.max_tokens, args.top, salt, args.nyers_top)
        rb["futas"] = i + 1
        ki["futasok"].append(rb)
        print(f"  B#{i+1:<2d} prompt={rb['prompt_tok']} cached={rb['cached_tok']:<6} "
              f"api={rb['api_hash']} kanon={rb['kanon_hash']} {rb['ms']:.0f} ms", flush=True)
    api = [f["api_hash"] for f in ki["futasok"]]
    kan = [f["kanon_hash"] for f in ki["futasok"]]
    ki["ertekeles"] = {
        "api_valtozatok": len(set(api)), "kanon_valtozatok": len(set(kan)),
        "elso_kulonbozik": len(api) > 1 and api[0] != api[1] and len(set(api[1:])) == 1,
        "szoveg_valtozatok": len({f["tartalom_sha"] for f in ki["futasok"]}),
        "cached_tok_B": [f["cached_tok"] for f in ki["futasok"]],
        "eredmeny": "PASS" if len(set(api)) == 1 else "FAIL",
    }
    e = ki["ertekeles"]
    print(f"  => {e['eredmeny']} (jóslat: {ki['joslat']}, {'EGYEZIK' if e['eredmeny']==ki['joslat'] else '**NEM EGYEZIK**'}) · "
          f"api-változat: {e['api_valtozatok']} · kanon-változat: {e['kanon_valtozatok']} · "
          f"szöveg-változat: {e['szoveg_valtozatok']}", flush=True)
    return ki

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True); a.add_argument("--doc", default="D6")
    a.add_argument("--blokkmeret", type=int, default=1600)
    a.add_argument("--ismetles", type=int, default=6)
    a.add_argument("--max-tokens", type=int, default=48); a.add_argument("--top", type=int, default=20)
    a.add_argument("--nyers-top", type=int, default=3, help="hány token nyers top-20 listája kerüljön a JSON-be")
    a.add_argument("--mag", default="r4", help="egyedi mag — MINDEN futásnál más (cache-izoláció)")
    a.add_argument("--cellak", default="1,2,3,4")
    a.add_argument("--parok", default="", help="round8: egyedi A:B hosszpárok (pl. 3184:3261,3198:3261); a --cellak helyett")
    a.add_argument("--cimke", default=""); a.add_argument("--out", required=True)
    args = a.parse_args()
    B = args.blokkmeret
    doksi = (Path(args.korpusz) / "corpus" / f"{args.doc}.md").read_text()
    alap = chat_tok(args.url, args.model, doksi)
    print(f"[i] {args.doc}.md + sablon = {alap} tok · blokkméret={B} · küszöb={2*B} · {args.url}")
    assert alap < 2 * B - 40, f"a dokumentum ({alap} tok) túl hosszú a küszöb alatti A-cellához"

    # (címke, A cél, B cél) — a küszöb 2*blokkméret
    C = {
        "1": ("1-A_alatt_B_felett", 2 * B - 20, 2 * B + 60),   # jóslat: FAIL
        "2": ("2-A_felett_B_felett", 2 * B + 10, 2 * B + 60),  # jóslat: PASS (A 20 tokennel hosszabb!)
        "3": ("3-A_alatt_B_alatt", 2 * B - 100, 2 * B - 50),   # jóslat: PASS
        "4": ("4-A_felett_B_alatt", 2 * B + 10, 2 * B - 50),   # jóslat: PASS (valódi hit, azonos eredet)
        # round8: A >= 3B csak a 2B-s checkpointot menti, az 1B-set nem; B (2B..3B) az 1B-set -> FAIL
        "5": ("5-A_3B_felett_B_2B_felett", 3 * B + 10, 2 * B + 60),
    }
    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S"),
          "doc_tok": alap, "cellak": []}
    lista = ([(f"p{a_}-{b_}", int(a_), int(b_)) for a_, b_ in (x.split(":") for x in args.parok.split(","))]
             if args.parok else [C[c.strip()] for c in args.cellak.split(",")])
    for n, (cimke, ca, cb) in enumerate(lista):
        c = str(n + 1)
        ki["cellak"].append(cella(args.url, args.model, args, cimke, doksi, ca, cb,
                                  mag=f"{args.mag}{c.strip()}"))
        Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print("\n[=] összegzés")
    egyez = 0
    for c in ki["cellak"]:
        ok = c["ertekeles"]["eredmeny"] == c["joslat"]
        egyez += ok
        print(f"  {c['cella']:<22} A={c['tenyleges']['A']:>5} B={c['tenyleges']['B']:>5} "
              f"jóslat={c['joslat']:<5} mért={c['ertekeles']['eredmeny']:<5} "
              f"{'EGYEZIK' if ok else '**NEM**'} · B cached_tok={c['ertekeles']['cached_tok_B']}")
    print(f"[=] jóslat-egyezés: {egyez}/{len(ki['cellak'])}\n[>] {args.out}")

if __name__ == "__main__":
    main()
