#!/usr/bin/env python3
"""Mérés D1 — komponens-lefedettség a lefordíthatatlan fogalmakra (laptop → prod 35B).

    python3 src/judge_d1.py

48 UNT-válasz (16 fogalom × 3 nyelv) + 48 kontrollszó-válasz. A bíráló minden
`native` és `distortion` komponensre KÜLÖN mond igent/nemet — nem összbenyomást ad,
mert a D1 pont a komponensek megjelenéséről szól.

⛔ A bírálónak megmondjuk, ha a válasz ismétlési hurokba esett vagy elvágódott: a
hurokba esett válaszban kevesebb komponens fér el, és ezek NYELVFÜGGŐEN oszlanak el
(hu 14 · zh 9 · en 2 az egész korpuszon) — enélkül a D1 a dekódolást mérné.

⛔ `enable_thinking=false` — a qwen36 alapból gondolkodik, és a `content` None-ként jön vissza.

Kimenet: results/d1_judge.jsonl + results/d1_scores.csv
"""
import argparse
import csv
import json
import os
import pathlib
import re
import threading
import time
import urllib.request
import scope_paths


# A bíráló vLLM végpontja. Publikált változat: a saját kiszolgálódat add meg.
URL = os.environ.get("JUDGE_URL", "http://<judge-host>:8355/v1/chat/completions")
MODEL = "qwen36"
HERE = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(HERE)

RUBRIKA_UNT = """Egy nyelvi modell definíciós válaszát kell elemezned egy nehezen fordítható fogalomról.
Megadok egy listát KÖTELEZŐ JELENTÉSKOMPONENSEKRŐL és egy listát TORZÍTÁS-JELEKRŐL.

Minden komponensre külön döntsd el, megjelenik-e a válaszban — tartalmilag, nem szó szerint.
Ha a válasz más nyelven van, az nem számít: a jelentés számít.
Ha a válasz elvágódott vagy ismétlési hurokba esett, csak a meglévő szövegrészt értékeld.

Válaszolj CSAK egy JSON objektummal:
{"native": [true/false, ...], "distortion": [true/false, ...], "indoklas": "<egy rövid mondat>"}
A tömbök hossza pontosan annyi legyen, ahány elemet megadtam."""

RUBRIKA_CTRL = """Egy nyelvi modell szótári definícióját kell értékelned egy hétköznapi szóról.
Kérdés: elfogadható, pontos definíciót ad-e?

- "jo": pontos, a szó fő jelentését megadja
- "reszben": nagyjából stimmel, de pontatlan, zavaros vagy önellentmondó
- "rossz": téves jelentést ad, vagy nem definiál

Ha a válasz ismétlési hurokba esett vagy elvágódott, csak a meglévő szövegrészt értékeld.
Válaszolj CSAK egy JSON objektummal: {"itelet": "...", "indoklas": "<egy rövid mondat>"}"""


def call(messages, timeout=120, retries=3):
    body = json.dumps({"model": MODEL, "messages": messages, "temperature": 0, "max_tokens": 400,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode("utf-8")
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                c = json.loads(r.read())["choices"][0]["message"]["content"]
            if not c:
                raise ValueError("üres content")
            return c
        except Exception as exc:
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"a bíráló nem válaszolt: {last}")


def parse(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    gen = {(r["item_id"], r["lang"]): r for r in
           (json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    prompts = {(p["item_id"], p["lang"]): p for p in
               (json.loads(l) for l in (HERE / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    todo_all = [p for p in prompts.values() if p["kind"] in ("unt", "ctrl")]

    out_path = RES / "d1_judge.jsonl"
    done = {}
    if out_path.exists() and not args.force:
        done = {(d["item_id"], d["lang"]): d for d in
                (json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip())}
    todo = [p for p in todo_all if (p["item_id"], p["lang"]) not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(todo_all)} válasz (48 UNT + 48 kontroll) · kész {len(done)} · most {len(todo)}", flush=True)

    lock, results, errors = threading.Lock(), [], []

    def work(p):
        g = gen[(p["item_id"], p["lang"])]
        note = []
        if g["truncated"]:
            note.append("elvágódott a token-keretnél")
        if g["degenerate"]:
            note.append("ismétlési hurokba esett")
        meta = p["meta"]
        if p["kind"] == "unt":
            user = (f"Fogalom: {meta['concept']} (forrásnyelv: {meta['src_lang']})\n"
                    f"Kötelező jelentéskomponensek:\n"
                    + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(meta["native"])) + "\n"
                    f"Torzítás-jelek:\n"
                    + "\n".join(f"  {i+1}. {c}" for i, c in enumerate(meta["distortion"])) + "\n\n"
                    f"A modell válasza ({p['lang']}):\n{g.get('text_clean', g['text'])}\n"
                    + (f"\nMegjegyzés: a válasz {', '.join(note)}.\n" if note else ""))
            d = parse(call([{"role": "system", "content": RUBRIKA_UNT}, {"role": "user", "content": user}]))
            ok = d and isinstance(d.get("native"), list) and isinstance(d.get("distortion"), list)
            rec = {"item_id": p["item_id"], "lang": p["lang"], "kind": "unt",
                   "concept": meta["concept"], "src_lang": meta["src_lang"],
                   "native_n": len(meta["native"]), "distortion_n": len(meta["distortion"]),
                   "native": [bool(x) for x in d["native"][:len(meta["native"])]] if ok else None,
                   "distortion": [bool(x) for x in d["distortion"][:len(meta["distortion"])]] if ok else None,
                   "indoklas": (d.get("indoklas") if d else "")[:300],
                   "truncated": g["truncated"], "degenerate": g["degenerate"], "answer": g["text"]}
        else:
            user = (f"Szó: {meta['control_word']} ({p['lang']})\n\nA modell válasza:\n"
                    f"{g.get('text_clean', g['text'])}\n"
                    + (f"\nMegjegyzés: a válasz {', '.join(note)}.\n" if note else ""))
            d = parse(call([{"role": "system", "content": RUBRIKA_CTRL}, {"role": "user", "content": user}]))
            it = str(d.get("itelet", "")).lower().strip() if d else ""
            it = {"jo": "jo", "jó": "jo", "reszben": "reszben", "részben": "reszben",
                  "rossz": "rossz"}.get(it)
            rec = {"item_id": p["item_id"], "lang": p["lang"], "kind": "ctrl",
                   "concept": meta["concept"], "control_word": meta["control_word"],
                   "itelet": it, "indoklas": (d.get("indoklas") if d else "")[:300],
                   "truncated": g["truncated"], "degenerate": g["degenerate"], "answer": g["text"]}
        with lock:
            results.append(rec)
            if rec.get("native") is None and rec.get("itelet") is None:
                errors.append((p["item_id"], p["lang"]))
            if len(results) % 20 == 0:
                print(f"  {len(results)}/{len(todo)} …", flush=True)

    queue, qlock = list(todo), threading.Lock()

    def loop():
        while True:
            with qlock:
                if not queue:
                    return
                p = queue.pop()
            try:
                work(p)
            except Exception as exc:
                with lock:
                    errors.append((p["item_id"], p["lang"], str(exc)[:120]))

    threads = [threading.Thread(target=loop, daemon=True) for _ in range(args.threads)]
    [t.start() for t in threads]
    [t.join() for t in threads]

    allrecs = list(done.values()) + results
    allrecs.sort(key=lambda d: (d["kind"], d["item_id"], d["lang"]))
    out_path.write_text("\n".join(json.dumps(d, ensure_ascii=False) for d in allrecs) + "\n", encoding="utf-8")
    print(f"kész — {len(allrecs)} ítélet, hibás: {len(errors)}")
    if errors:
        print("  ", errors[:5])

    # ⛔ Ugyanaz a védelem, mint a judge.py-ban: a ellenőrző oszlopok túlélik az újrafuttatást.
    d1_path = RES / "d1_scores.csv"
    keep = {}
    if d1_path.exists():
        for r in csv.DictReader(d1_path.open(encoding="utf-8")):
            vals = [(r.get(k) or "").strip() for k in ("manual_ctrl", "manual_native", "manual_distortion")]
            if any(vals):
                keep[(r["item_id"], r["lang"])] = vals
        if keep:
            print(f"megőrzött ellenőrző ítéletek: {len(keep)} sor")
    with d1_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["kind", "item_id", "concept", "src_lang", "lang", "native_hit", "native_n",
                    "distortion_hit", "distortion_n", "ctrl_itelet", "manual_ctrl", "manual_native", "manual_distortion",
                    "truncated", "degenerate", "indoklas"])
        for d in allrecs:
            if d["kind"] == "unt":
                w.writerow(["unt", d["item_id"], d["concept"], d["src_lang"], d["lang"],
                            sum(d["native"]) if d["native"] else "", d["native_n"],
                            sum(d["distortion"]) if d["distortion"] else "", d["distortion_n"], "",
                            *keep.get((d["item_id"], d["lang"]), ["", "", ""]),
                            int(d["truncated"]), int(d["degenerate"]), d["indoklas"]])
            else:
                w.writerow(["ctrl", d["item_id"], d["concept"], "", d["lang"], "", "", "", "",
                            d["itelet"], *keep.get((d["item_id"], d["lang"]), ["", "", ""]),
                            int(d["truncated"]), int(d["degenerate"]), d["indoklas"]])
    print(f"→ {RES / 'd1_scores.csv'}")


if __name__ == "__main__":
    main()
