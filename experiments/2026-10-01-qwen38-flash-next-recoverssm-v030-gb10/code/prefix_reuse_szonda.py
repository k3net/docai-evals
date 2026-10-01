#!/usr/bin/env python3
"""Round8 M1 — történik-e TÉNYLEGES prefix reuse (nem csak engedélyezett cache).

Négy DocIT-szerű minta, kérésenként `usage.prompt_tokens_details.cached_tokens` + a kérés ideje
(max_tokens=1 mellett ≈ TTFT) + a /metrics prefix-cache számlálóinak deltája mintánként:
  a) azonos ~8K prompt ×4                       (KIE háromszori futtatása)
  b) közös dokumentum, 3 különböző kérdés ×2    (chat/KIE közös iratprefix)
  c) többkörös chat, 6 kör, valódi modellválasszal (decode alatt írt állapot újrahasznosítása)
  d) hosszú: ~32K és ~60K token ×2
Mintánként és futásonként egyedi `cache_salt` -> a minták nem szennyezik egymást, és ugyanazon
a szerveren újrafuttatva is hidegről indul. A hiányzó `cached_tokens` mező STOP (nem 0 találat).
"""
from __future__ import annotations
import argparse, json, time, urllib.request
from pathlib import Path

RENDSZER = "Magyar dokumentumfeldolgozó asszisztens vagy. Kizárólag a megadott dokumentum alapján válaszolj, tömören."
KERDESEK = ["Ki a kiállító és mi a dokumentum típusa?",
            "Sorold fel a dokumentumban szereplő dátumokat.",
            "Mi a dokumentumban szereplő legnagyobb összeg?"]
CHAT_KOROK = ["Foglald össze a dokumentumot öt mondatban.",
              "Melyik szakasz a legfontosabb egy könyvelő számára, és miért?",
              "Írd le részletesen a második legfontosabb szakaszt.",
              "Milyen kockázatokat látsz a dokumentumban?",
              "Készíts egy rövid teendőlistát a dokumentum alapján.",
              "Foglald össze egy mondatban az eddigi beszélgetést."]


def hivas(url, ut, payload, timeout=1800):
    req = urllib.request.Request(url.rstrip("/") + ut, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), (time.monotonic() - t0) * 1000


def metrikak(url):
    txt = urllib.request.urlopen(url.rstrip("/") + "/metrics", timeout=30).read().decode()
    out = {}
    for name in ("vllm:prefix_cache_queries_total", "vllm:prefix_cache_hits_total"):
        m = [float(l.rsplit(" ", 1)[1]) for l in txt.splitlines() if l.startswith(name)]
        out[name.split(":")[1]] = sum(m) if m else None
    return out


def chat(url, model, uzenetek, salt, max_tokens):
    payload = {"model": model, "messages": uzenetek, "temperature": 0.0, "top_p": 1,
               "max_tokens": max_tokens, "cache_salt": salt,
               "chat_template_kwargs": {"enable_thinking": False}}
    body, ms = hivas(url, "/v1/chat/completions", payload)
    u = body.get("usage", {})
    det = u.get("prompt_tokens_details")
    if det is None or "cached_tokens" not in det:
        raise SystemExit("STOP: nincs usage.prompt_tokens_details.cached_tokens (--enable-prompt-tokens-details?)")
    return {"prompt_tok": u.get("prompt_tokens"), "cached_tok": det["cached_tokens"],
            "gen_tok": u.get("completion_tokens"), "ms": round(ms, 1),
            "valasz": body["choices"][0]["message"].get("content") or ""}


def doksi(korpusz, nev, max_char=None):
    s = (Path(korpusz) / "corpus" / f"{nev}.md").read_text()
    return s[:max_char] if max_char else s


def minta(nev, url, fn):
    m0 = metrikak(url)
    sorok = fn()
    m1 = metrikak(url)
    d = {k: (m1[k] - m0[k]) if m0[k] is not None and m1[k] is not None else None for k in m0}
    print(f"  [{nev}] /metrics delta: queries={d['prefix_cache_queries_total']} hits={d['prefix_cache_hits_total']}",
          flush=True)
    return {"minta": nev, "sorok": sorok, "metrics_delta": d}


def kiir(cimke, r):
    print(f"    {cimke:<14} prompt={r['prompt_tok']:>6} cached={r['cached_tok']:>6} "
          f"({100 * r['cached_tok'] / max(1, r['prompt_tok']):5.1f}%) {r['ms']:>8.0f} ms", flush=True)


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True); a.add_argument("--mag", required=True)
    a.add_argument("--mintak", default="a,b,c,d"); a.add_argument("--cimke", default="")
    a.add_argument("--chat-max-tokens", type=int, default=160)
    a.add_argument("--out", required=True)
    args = a.parse_args()
    url, model, K = args.url, args.model, args.korpusz
    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "mintak": []}

    def ment():
        Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))

    doc8k = doksi(K, "D1") + "\n\n" + doksi(K, "D2") + "\n\n" + doksi(K, "D6")
    for m in args.mintak.split(","):
        m = m.strip()
        print(f"\n[{m}] {args.cimke}", flush=True)
        if m == "a":
            def fa():
                salt, rows = f"r8m1a-{args.mag}", []
                msg = [{"role": "system", "content": RENDSZER},
                       {"role": "user", "content": doc8k + "\n\n" + KERDESEK[0]}]
                for i in range(4):
                    r = chat(url, model, msg, salt, 1); r["futas"] = i + 1; rows.append(r); kiir(f"#{i+1}", r)
                return rows
            ki["mintak"].append(minta("a_azonos_prompt", url, fa))
        elif m == "b":
            def fb():
                salt, rows = f"r8m1b-{args.mag}", []
                for rnd in range(2):
                    for qi, q in enumerate(KERDESEK):
                        msg = [{"role": "system", "content": RENDSZER},
                               {"role": "user", "content": doc8k + "\n\n" + q}]
                        r = chat(url, model, msg, salt, 1); r.update(kor=rnd + 1, kerdes=qi + 1)
                        rows.append(r); kiir(f"k{rnd+1}/q{qi+1}", r)
                return rows
            ki["mintak"].append(minta("b_kozos_doksi_mas_kerdes", url, fb))
        elif m == "c":
            def fc():
                salt, rows = f"r8m1c-{args.mag}", []
                msg = [{"role": "system", "content": RENDSZER},
                       {"role": "user", "content": doksi(K, "D1") + "\n\n" + CHAT_KOROK[0]}]
                for i in range(len(CHAT_KOROK)):
                    r = chat(url, model, msg, salt, args.chat_max_tokens); r["kor"] = i + 1
                    rows.append({k: v for k, v in r.items() if k != "valasz"} | {"valasz_hossz": len(r["valasz"])})
                    kiir(f"kör {i+1}", r)
                    if i + 1 < len(CHAT_KOROK):
                        msg = msg + [{"role": "assistant", "content": r["valasz"]},
                                     {"role": "user", "content": CHAT_KOROK[i + 1]}]
                return rows
            ki["mintak"].append(minta("c_tobbkoros_chat", url, fc))
        elif m == "d":
            def fd():
                rows = []
                for cel, nchar in (("32K", 90000), ("60K", 170000)):
                    salt = f"r8m1d{cel}-{args.mag}"
                    msg = [{"role": "system", "content": RENDSZER},
                           {"role": "user", "content": doksi(K, "D7", nchar) + "\n\n" + KERDESEK[0]}]
                    for i in range(2):
                        r = chat(url, model, msg, salt, 1); r.update(cel=cel, futas=i + 1)
                        rows.append(r); kiir(f"{cel} #{i+1}", r)
                return rows
            ki["mintak"].append(minta("d_hosszu", url, fd))
        elif m == "e":
            # round8 kiegészítés: RÉSZLEGES közös prefix. Egy hosszú prompt (A, ~86K) után egy olyan kérés,
            # amely A elejéből csak ~50K-t oszt meg (B), majd A más kérdéssel (C). retention=0 mellett a Mamba
            # csak a replay-határ állapotát tartja meg -> B-nek nincs közbenső checkpointja; dense mellett van.
            def fe():
                salt, rows = f"r8m1e-{args.mag}", []
                for cimke, nchar, q in (("A_86K", 170000, KERDESEK[0]), ("B_50K_resz", 100000, KERDESEK[1]),
                                        ("B_50K_resz#2", 100000, KERDESEK[1]), ("C_86K_mas_kerdes", 170000, KERDESEK[2])):
                    msg = [{"role": "system", "content": RENDSZER},
                           {"role": "user", "content": doksi(K, "D7", nchar) + "\n\n" + q}]
                    r = chat(url, model, msg, salt, 1); r["cimke"] = cimke; rows.append(r); kiir(cimke, r)
                return rows
            ki["mintak"].append(minta("e_reszleges_prefix", url, fe))
        else:
            raise SystemExit(f"ismeretlen minta: {m}")
        for s in ki["mintak"][-1]["sorok"]:
            s.pop("valasz", None)
        ment()
    print(f"\n[>] {args.out}")


if __name__ == "__main__":
    main()
