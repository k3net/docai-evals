#!/usr/bin/env python3
"""Round8 M3 — hosszú-válasz stresszpróba a `night` mintavétellel (T 0,6, presence 1,5), konkurenciával.

A stevededrick-féle boundary-hiba tünete: a válasz közepén folyékony, témától eltérő, MÁS NYELVŰ
szöveg. Detektor (reasoning + content):
  * nem latin írás: Han / Kana / Hangul / cirill / arab / thai karakterek száma;
  * angol szakasz: 40 szavas csúszóablak, ahol az angol stopszavak aránya >= 35%
    (a magyar szövegben ez gyakorlatilag nem fordul elő; a kódrészlet és a tulajdonnév nem éri el).
"""
from __future__ import annotations
import argparse, json, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

FELADATOK = [
    "Írj részletes, legalább 1200 szavas elemzést magyarul a fenti dokumentumról: szerkezet, felek, kötelezettségek, kockázatok, javaslatok.",
    "Készíts részletes magyar nyelvű könyvelői feljegyzést a dokumentum alapján, pontokba szedve, indoklással, legalább 1000 szóban.",
    "Magyarázd el egy pályakezdő kollégának, lépésről lépésre, hogyan kell ezt a dokumentumot feldolgozni és ellenőrizni. Legyél nagyon részletes.",
]
DOKSIK = ["D1", "D2", "D3", "D4", "D6", "C1", "C3", "C5"]
NEMLATIN = re.compile(r"[一-鿿぀-ヿ가-힯Ѐ-ӿ؀-ۿ฀-๿]")
ANGOL = set("the of and to in is that for it with as was on be are this by an or from which at not have has but they their these will can would".split())


def hivas(url, payload, timeout=3600):
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", "Connection": "close"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r), time.monotonic() - t0


def angol_ablakok(szoveg):
    w = re.findall(r"[A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+", szoveg)
    talalat = []
    for i in range(0, max(0, len(w) - 40) + 1, 10):
        ab = w[i:i + 40]
        if ab and sum(x.lower() in ANGOL for x in ab) / len(ab) >= 0.35:
            talalat.append(" ".join(ab[:12]))
    return talalat


def egy(args, i):
    doc = DOKSIK[i % len(DOKSIK)]
    fel = FELADATOK[(i // len(DOKSIK)) % len(FELADATOK)]
    szoveg = (Path(args.korpusz) / "corpus" / f"{doc}.md").read_text()
    payload = {"model": args.model, "temperature": 0.6, "top_p": 1.0, "presence_penalty": 1.5,
               "max_tokens": args.max_tokens, "cache_salt": f"r8ny-{args.mag}-{i}",
               "messages": [{"role": "user", "content": szoveg + "\n\n" + fel}]}
    d, s = hivas(args.url, payload)
    m = d["choices"][0]["message"]
    rs = m.get("reasoning_content") or m.get("reasoning") or ""
    ct = m.get("content") or ""
    r = {"i": i, "doc": doc, "gen_tok": d["usage"]["completion_tokens"], "prompt_tok": d["usage"]["prompt_tokens"],
         "finish": d["choices"][0]["finish_reason"], "s": round(s, 1),
         "nemlatin_reasoning": len(NEMLATIN.findall(rs)), "nemlatin_content": len(NEMLATIN.findall(ct)),
         "angol_content": angol_ablakok(ct)[:3], "angol_reasoning": angol_ablakok(rs)[:3],
         "angol_reasoning_db": len(angol_ablakok(rs)), "reasoning_hossz": len(rs),
         "content_hossz": len(ct), "ures_content": not ct.strip(),
         # round8 v2: a nem latin előfordulások környezete (max 5), hogy szivárgás vs. legitim jel eldönthető legyen
         "nemlatin_kornyezet": [(rs + "\n<<C>>\n" + ct)[max(0, m.start() - 60):m.start() + 60]
                                for m in list(NEMLATIN.finditer(rs + "\n<<C>>\n" + ct))[:5]]}
    # angol reasoning önmagában NEM gyanús (a modell gyakran angolul gondolkodik); a gyanú: nem latin írás,
    # vagy angol szakasz a magyar válaszban
    r["gyanus"] = bool(r["nemlatin_content"] or r["nemlatin_reasoning"] or r["angol_content"])
    if r["gyanus"]:
        r["content_minta"] = ct[:4000]
    return r


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True); a.add_argument("--n", type=int, default=24)
    a.add_argument("--konk", type=int, default=4); a.add_argument("--max-tokens", type=int, default=6000)
    a.add_argument("--mag", required=True); a.add_argument("--cimke", default="")
    a.add_argument("--out", required=True)
    args = a.parse_args()
    t0 = time.monotonic()
    with ThreadPoolExecutor(args.konk) as ex:
        res = list(ex.map(lambda i: egy(args, i), range(args.n)))
    for r in res:
        print(f"#{r['i']:>3} {r['doc']:<3} gen={r['gen_tok']:>5} {r['finish']:<6} nemlatin r/c={r['nemlatin_reasoning']}/"
              f"{r['nemlatin_content']} angol={len(r['angol_content'])} {'GYANÚS' if r['gyanus'] else ''}")
    ossz = {"n": len(res), "gen_tok": sum(r["gen_tok"] for r in res), "gyanus": sum(r["gyanus"] for r in res),
            "nemlatin_content_db": sum(r["nemlatin_content"] > 0 for r in res),
            "nemlatin_reasoning_db": sum(r["nemlatin_reasoning"] > 0 for r in res),
            "ures_content": sum(r["ures_content"] for r in res),
            "length": sum(r["finish"] == "length" for r in res),
            "angol_reasoning_valasz_db": sum(r["angol_reasoning_db"] > 0 for r in res), "fal_s": round(time.monotonic() - t0, 1)}
    Path(args.out).write_text(json.dumps({"cimke": args.cimke, "args": vars(args), "osszeg": ossz, "valaszok": res},
                                         ensure_ascii=False, indent=2))
    print(f"[=] {ossz} -> {args.out}")


if __name__ == "__main__":
    main()
