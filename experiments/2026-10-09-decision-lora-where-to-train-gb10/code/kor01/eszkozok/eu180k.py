"""EU-180k hu (01-runbook 3.3, 9. pont 3.): az eszközlista kinyerése a system promptból, és train-kiegészítő itemek.

A forrásban nincs strukturált `tools` mező: az eszközök a system promptban szabad szövegként, vegyes formátumban
állnak. A `forras_konvertal.py` regexe csak a valahol meghívott eszközneveket találja meg (a soha nem hívottakat nem,
12 itemnél semmit), ezért a listát Mistral Small 4 nyeri ki JSON-ba. Ellenőrzés: minden név szó szerint szerepel a
system promptban, a gold (ha van) a listán van, 1–10 eszköz. A párhuzamos hívásos itemek kimaradnak (2. pont).
Az itemek a train-be csak a címke-átnézés után kerülhetnek (9. pont 3.); ez az eszköz csak előállítja őket.

  python3 kor01/eszkozok/eu180k.py --url http://127.0.0.1:8430/v1 --model mistral-small-4
      → adat/f1s/items_eu180k.jsonl + eu180k_riport.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos01 import A, F1S, llm_json, read_jsonl, write_json, write_jsonl  # noqa: E402

SEED = 20261007
SYSTEM = "Szövegből strukturált adatot nyersz ki. Kizárólag érvényes JSON-t adsz vissza, magyarázat nélkül."
PROMPT = """Az alábbi system prompt egy asszisztens eszközeit (függvényeit) írja le, szabad formában. Gyűjtsd ki az
összes eszközt: a pontos nevét (ahogy a szövegben áll), egy egymondatos leírását a szöveg alapján (magyarul), és a
kötelező paraméterei nevét, ha a szöveg megadja őket. Ne találj ki eszközt vagy paramétert.

Formátum: {{"eszkozok": [{{"name": "...", "description": "...", "required": ["..."]}}]}}

System prompt:
\"\"\"{sp}\"\"\""""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8430/v1")
    ap.add_argument("--model", default="mistral-small-4")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--extra-body", default='{"reasoning_effort": "none"}')
    args = ap.parse_args()
    extra = {"temperature": 0, "max_tokens": 2000, **json.loads(args.extra_body)}
    src = read_jsonl(A / "eu180k_hu_egyedi.jsonl")

    def run(r):
        try:
            return r, llm_json(args.url, args.model, SYSTEM, PROMPT.format(sp=r["system_prompt"]), extra, SEED), None
        except Exception as e:
            return r, None, str(e)[:200]

    with ThreadPoolExecutor(args.concurrency) as ex:
        res = list(ex.map(run, src))
    items, rep = [], Counter()
    for r, d, err in res:
        if err:
            rep["hiba"] += 1
            continue
        if "parhuzamos_hivas" in r["meta"]["jelzok"]:
            rep["kizart_parhuzamos"] += 1
            continue
        tools, seen = [], set()
        for t in (d or {}).get("eszkozok", []):
            name = str(t.get("name", "")).strip()
            if not name or name in seen or not re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", r["system_prompt"]):
                rep["eldobott_nev"] += bool(name)
                continue
            seen.add(name)
            tools.append({"id": name, "name": name, "description": str(t.get("description", "")).strip(),
                          "required": [str(p) for p in t.get("required") or [] if isinstance(p, str)]})
        if not 1 <= len(tools) <= 10:
            rep["kizart_eszkozszam"] += 1
            continue
        if r["gold"] is not None and r["gold"] not in seen:
            rep["kizart_gold_nincs_a_listan"] += 1
            continue
        rep["regex_lista_hianyos"] += len(set(r["options_nevek"]) - seen) > 0 or len(seen - set(r["options_nevek"])) > 0
        items.append({"id": r["id"], "forras": "eu180k_hu", "split": "train", "lang": "hu", "request": r["request"],
                      "history": [], "options": tools, "gold": r["gold"],
                      "meta": {"klaszter": r["meta"]["klaszter"], "x_fajta": None if r["gold"] else "eszkoz_nelkul",
                               "type": r["meta"]["type"], "domain": r["meta"]["domain"]}})
    rep["item"] = len(items)
    rep["X"] = sum(i["gold"] is None for i in items)
    write_jsonl(F1S / "items_eu180k.jsonl", items)
    write_json(F1S / "eu180k_riport.json", {"model": args.model, **dict(rep)})
    print(dict(rep))


if __name__ == "__main__":
    main()
