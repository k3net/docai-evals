"""T-katalógus (01-runbook 3.5 és 4. pont): magyar kérések a katalógus 14, MASSIVE-pár nélküli eszközére, és belőlük
teszt-itemek.

A generátor Mistral Small 4 (Apache-2.0): a 8. pont szerint saját generálás csak Apache-2.0 modellel mehet, és az
alany (Qwen3.6) nem írhatja a saját tesztjét. A kérések nem nevezhetik meg az eszközt, és a közeli eszközökkel nem
lehetnek teljesíthetők (a szomszédok leírását a prompt ellenpéldaként kapja).

  gen   — eszközönként len(STILUSOK) hívás, hívásonként N_PER_HIVAS kérés (JSON); szűrés (hossz, eszköznév, CJK) és
          normalizált dedup; eszközönként legfeljebb N_PER_ESZKOZ marad (seedelt mintavétel)
          → adat/f1s/katalogus_keresek.jsonl + katalogus_gen_riport.json
  items — teszt-itemek a MASSIVE-receptjével (`osszeallit.massive_items`: opciószám a 00 eloszlásával, közeli párok
          NEAR_P valószínűséggel, GOLD_DROP gold-drop a `felulvizsgal` párok kizárásával) → adat/f1s/items_katalogus.jsonl

  python3 kor01/eszkozok/katalogus_kerdes.py gen --url http://127.0.0.1:8430/v1 --model mistral-small-4
  python3 kor01/eszkozok/katalogus_kerdes.py items
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos01 import CJK, F1S, catalog, llm_json, norm, read_jsonl, write_json, write_jsonl  # noqa: E402
from osszeallit import N_OPT_W, NEAR_P, massive_items  # noqa: E402

SEED = 20261007
N_PER_HIVAS = 8
N_PER_ESZKOZ = 50
STILUSOK = [
    "hétköznapi, tegező, rövid",
    "udvarias, magázó, teljes mondat",
    "címszavas, nagyon tömör (2–6 szó)",
    "hosszabb, körülményes, a kéréshez tartozó háttérrel",
    "sietős, elírásokkal vagy ékezetek nélkül",
    "kérdő formában",
    "konkrét adatokkal (időpont, összeg, hely, azonosító — kitalált értékekkel)",
    "közvetett: a szükségletet írja le, nem a műveletet nevezi meg",
]
SYSTEM = ("Magyar nyelvű felhasználói kéréseket írsz egy digitális asszisztens teszteléséhez. Kizárólag érvényes "
          "JSON-t adsz vissza, magyarázat nélkül.")
PROMPT = """Az asszisztens egyik eszköze:
{tool}
Paraméterek:
{params}

Írj {n} különböző, valószerű magyar felhasználói kérést, amelyet pontosan ezzel az eszközzel kell teljesíteni.
Stílus: {stilus}.

Szabályok:
- A kérés ne nevezze meg az eszközt, és ne használjon angol azonosítót (például „{name}”).
- Az alábbi, hasonló eszközökkel NE legyen teljesíthető, mert azok mást csinálnak:
{szomszedok}
- Valós személy, cég vagy márka neve ne szerepeljen; kitalált vagy általános nevek és adatok mehetnek.
- Mindegyik kérés más helyzetet írjon le, és ne ismételd a mondatszerkezetet.

Formátum: {{"keresek": ["...", "..."]}}"""


def targets(cat: dict) -> list[str]:
    return sorted(n for n, t in cat.items() if not t["massive"])


def neighbours(cat: dict, name: str) -> list[str]:
    t = cat[name]
    rev = [n for n, u in cat.items() if name in u["kozeli"] or name in u["felulvizsgal"]]
    return sorted((set(t["kozeli"]) | set(t["felulvizsgal"]) | set(rev)) - {name})


def valid(req: str, name: str) -> bool:
    low = req.lower()
    return (5 <= len(req) <= 300 and not CJK.search(req) and name.lower() not in low
            and name.replace("_", " ").lower() not in low)


def cmd_gen(args) -> None:
    cat = catalog()
    extra = {"temperature": 0.9, "top_p": 0.95, "max_tokens": 1500, **(args.extra or {})}
    tasks = []
    for ti, name in enumerate(targets(cat)):
        t = cat[name]
        params = "\n".join(f"- {p['name']} ({'kötelező' if p['required'] else 'opcionális'}): {p['leiras']}" for p in t["params"])
        nb = "\n".join(f"- {cat[n]['name']}: {cat[n]['leiras']}" for n in neighbours(cat, name)) or "- (nincs)"
        for si, st in enumerate(STILUSOK):
            tasks.append((name, st, SEED + 100 * ti + si, PROMPT.format(tool=f"{name}: {t['leiras']}", params=params, n=N_PER_HIVAS,
                                                                        stilus=st, name=name, szomszedok=nb)))

    def run(task):
        name, st, seed, prompt = task
        try:
            d = llm_json(args.url, args.model, SYSTEM, prompt, extra, seed)
            reqs = d.get("keresek", []) if isinstance(d, dict) else d
            return name, st, [str(x).strip() for x in reqs if isinstance(x, str)], None
        except Exception as e:
            return name, st, [], str(e)[:200]

    rows, rep = [], Counter()
    with ThreadPoolExecutor(args.concurrency) as ex:
        res = list(ex.map(run, tasks))
    rng = random.Random(SEED)
    for name in targets(cat):
        seen, cand = set(), []
        for n, st, reqs, err in res:
            if n != name:
                continue
            rep["hivas_hiba"] += err is not None
            for q in reqs:
                rep["nyers"] += 1
                if not valid(q, name):
                    rep["szurt_ervenytelen"] += 1
                    continue
                k = norm(q)
                if k in seen:
                    rep["szurt_duplikatum"] += 1
                    continue
                seen.add(k)
                cand.append({"request": q, "gold_eszkoz": name, "stilus": st})
        rng.shuffle(cand)
        rep[f"eszkoz:{name}"] = min(len(cand), N_PER_ESZKOZ)
        rows += cand[:N_PER_ESZKOZ]
    for k, r in enumerate(rows):
        r["id"] = f"kat-{k:04d}"
    write_jsonl(F1S / "katalogus_keresek.jsonl", rows)
    write_json(F1S / "katalogus_gen_riport.json", {"seed": SEED, "model": args.model, "n": len(rows), **dict(rep)})
    print(f"{len(rows)} kérés; {dict(rep)}")


def cmd_items(args) -> None:
    rows = [{"id": r["id"], "request": r["request"], "gold_eszkoz": r["gold_eszkoz"],
             "meta": {"klaszter": r["id"], "eszkoz": r["gold_eszkoz"], "stilus": r["stilus"]}}
            for r in read_jsonl(F1S / "katalogus_keresek.jsonl")]
    items = massive_items(rows, "teszt", random.Random(SEED + 1), N_OPT_W, NEAR_P, forras="katalogus_hu")
    for it in items:
        if it["gold"] is None:
            it["meta"]["kivett_gold"] = it["meta"]["eszkoz"]
    write_jsonl(F1S / "items_katalogus.jsonl", items)
    print(f"{len(items)} item, X {sum(i['gold'] is None for i in items)}")


def main() -> None:
    import json
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "items"])
    ap.add_argument("--url", default="http://127.0.0.1:8430/v1")
    ap.add_argument("--model", default="mistral-small-4")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--extra-body", default='{"reasoning_effort": "none"}')
    args = ap.parse_args()
    args.extra = json.loads(args.extra_body)
    {"gen": cmd_gen, "items": cmd_items}[args.cmd](args)


if __name__ == "__main__":
    main()
