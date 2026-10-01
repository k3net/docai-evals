#!/usr/bin/env python3
"""Round8 M2/3 — cache-hit vs. újraszámolás, ugyanazon a szerverindításon belül.

Itemenként (korpusz-dokumentum + összefoglaló kérdés, greedy, top-20 logprob):
  * HIT-sor:   `--hit` kérés közös salttal  -> az 1. hideg, a 2..n. (ha a cache talál) cache-ből;
  * HIDEG-sor: `--hideg` kérés, mindegyik egyedi salttal -> mindig teljes újraszámolás.
A jó állapot: minden HIDEG azonos (a szerver determinisztikus), és a HIT-sor minden tagja = HIDEG.
A round4 `checkpoint_szonda.keres` függvényét használja (api- és token-id szerint kanonizált hash,
cached_tokens, nyers top-20 az első tokenekre).
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_szonda import keres  # noqa: E402

KERDES = "\n\n===== FELADAT =====\n\nFoglald össze egy mondatban."

def main():
    a = argparse.ArgumentParser()
    a.add_argument("--url", required=True); a.add_argument("--model", required=True)
    a.add_argument("--korpusz", required=True); a.add_argument("--itemek", default="D1,D2,D3,D6")
    a.add_argument("--hit", type=int, default=6); a.add_argument("--hideg", type=int, default=3)
    a.add_argument("--max-tokens", type=int, default=48); a.add_argument("--top", type=int, default=20)
    a.add_argument("--mag", required=True); a.add_argument("--cimke", default="")
    a.add_argument("--out", required=True)
    args = a.parse_args()
    ki = {"cimke": args.cimke, "args": vars(args), "kezdet": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "itemek": []}
    for it in args.itemek.split(","):
        szoveg = (Path(args.korpusz) / "corpus" / f"{it}.md").read_text() + KERDES
        hit = [keres(args.url, args.model, szoveg, args.max_tokens, args.top, f"r8cv-{args.mag}-{it}", 2)
               for _ in range(args.hit)]
        hideg = [keres(args.url, args.model, szoveg, args.max_tokens, args.top, f"r8cv-{args.mag}-{it}-h{i}", 2)
                 for i in range(args.hideg)]
        hideg_api = {h["api_hash"] for h in hideg}
        ref = hideg[0]["api_hash"]
        e = {"item": it, "prompt_tok": hit[0]["prompt_tok"],
             "hit_cached": [h["cached_tok"] for h in hit], "hit_api": [h["api_hash"] for h in hit],
             "hideg_cached": [h["cached_tok"] for h in hideg], "hideg_api": sorted(hideg_api),
             "hideg_determinisztikus": len(hideg_api) == 1,
             "hit_elteres_db": sum(h["api_hash"] != ref for h in hit),
             "hit_kanon_elteres_db": sum(h["kanon_hash"] != hideg[0]["kanon_hash"] for h in hit),
             "hit_szoveg_elteres_db": sum(h["tartalom_sha"] != hideg[0]["tartalom_sha"] for h in hit),
             "nyers": {"hit": hit, "hideg": hideg}}
        e["eredmeny"] = "PASS" if e["hideg_determinisztikus"] and e["hit_elteres_db"] == 0 else "FAIL"
        ki["itemek"].append(e)
        print(f"[{it}] prompt={e['prompt_tok']} hit_cached={e['hit_cached']} hideg_cached={e['hideg_cached']} "
              f"hideg-változat={len(hideg_api)} hit≠hideg: api {e['hit_elteres_db']}/{args.hit} "
              f"kanon {e['hit_kanon_elteres_db']} szöveg {e['hit_szoveg_elteres_db']} => {e['eredmeny']}", flush=True)
        Path(args.out).write_text(json.dumps(ki, ensure_ascii=False, indent=2))
    print(f"[=] {sum(i['eredmeny']=='PASS' for i in ki['itemek'])}/{len(ki['itemek'])} PASS -> {args.out}")

if __name__ == "__main__":
    main()
