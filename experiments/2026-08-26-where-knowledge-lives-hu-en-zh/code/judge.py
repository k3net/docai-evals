#!/usr/bin/env python3
"""Mérés A / 1. kör — LLM-as-judge a 162 faktuális válaszra.

    python3 src/judge.py                 # a LAPTOPRÓL fut, HTTP-n hívja a prod vLLM-et
    python3 src/judge.py --limit 6       # próbakör

⚠️ A bíráló kiszolgáló (`JUDGE_URL`) **éles** kiszolgáló: csak olvasó completion-hívásokat
küldünk, kis párhuzamossággal — semmilyen tenant-adatot nem érintünk
(házirend: eval SOHA ne cselekedjen éles tenanton).

⚠️ A bíráló ugyanabból a modellcsaládból való, mint a vizsgált modell (Qwen3.6-35B vs
Qwen3.5-9B) — ezért a ZH és HU csoport MINDEN válaszát kézzel is ellenőrizni kell
(runbook §2), a bíráló ítélete csak az első kör. Az egyezést utólag mérjük.

⛔ A bírálónak megmondjuk, ha a válasz a token-keretbe ütközött vagy ismétlési hurokba
esett — enélkül a csonkolt magyar válaszokat „hiányosnak" minősítené, és a nyelvi
összehasonlítás a dekódolás műtermékét mérné (ld. flag_degenerate.py).

Kimenet: results/judge.jsonl (nyers ítéletek) + results/scores.csv (a runbook formátuma).
"""
import argparse
import csv
import json
import os
import pathlib
import re
import threading
import time
import urllib.error
import urllib.request
import scope_paths


# A bíráló vLLM végpontja. Publikált változat: a saját kiszolgálódat add meg.
URL = os.environ.get("JUDGE_URL", "http://<judge-host>:8355/v1/chat/completions")
MODEL = "qwen36"
HERE = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(HERE)

RUBRIKA = """Egy nyelvi modell válaszát kell értékelned egy tudáskérdésre. Négy ítélet közül válassz:

- "helyes": a válasz tartalmazza a várt információt (a megfogalmazás eltérhet, a nyelv is)
- "reszben": részben helyes vagy hiányos — a lényeg megvan, de pontatlan vagy nem teljes
- "helytelen": más információt ad, kitér, vagy nem válaszol a kérdésre
- "hallucinacio": magabiztosan állít KONKRÉT, kitalált tényeket (neveket, dátumokat, helyeket), amelyek tévesek

Fontos:
- A várt válasz a helyes megoldás. Ha a modell válasza ezzel egyezik, "helyes", akkor is, ha bőbeszédű.
- Ha a válasz más nyelven van, mint a kérdés, az önmagában NEM hiba.
- Ha jelezzük, hogy a válasz elvágódott vagy ismétlési hurokba esett, akkor CSAK a meglévő szövegrészt
  értékeld: ha a hiányzó rész miatt nem lehet eldönteni, azt ne rójuk fel — az addig leírtak alapján ítélj.

Válaszolj CSAK egy JSON objektummal: {"itelet": "...", "indoklas": "<egy rövid mondat>"}"""

# ⭐ SZIGORÍTOTT rubrika (2026-08-25-én kódba véve; a 08-24-i bírálókísérlet nyerteseként).
# A 6 legnehezebb (vitás) tételen mérve: EREDETI rubrikával 35B 0/6 · 122B 2/6;
# ezzel a rubrikával 35B **3/6** · 122B 4/6 — vagyis a szűk keresztmetszet a RUBRIKA volt,
# nem a modellméret, ezért maradt a bíráló a 35B (runbook §4c „Amit NEM kell újracsinálni").
# ⛔ Bírálócsere/rubrikacsere CSAK MINDKÉT körre értelmes, különben a base↔instruct különbség
# a rubrikaváltást méri, nem a post-trainingét. Ezért az alapértelmezés az EREDETI marad.
RUBRIKA_HARD = """Egy nyelvi modell válaszát kell értékelned egy tudáskérdésre.

ELSŐ LÉPÉS (magadban): mondd ki egy mondatban, MIT ÁLLÍT KONKRÉTAN a modell válasza.
Ha a válasz nem állít semmi konkrétat (csak felsorolja a lehetőségeket, körülír, vagy a
kérdést ismétli), az NEM válasz → "helytelen".

Négy ítélet közül válassz:

- "helyes": a válasz konkrétan megnevezi a várt információt (a megfogalmazás és a nyelv eltérhet)
- "reszben": a válasz konkrét, és a lényeg irányába mutat, de NEM pontosan a várt érték —
  ide tartozik a „nagyjából stimmel" (jó kategória, rossz elem; jó időszak, rossz ablak;
  a két elemből az egyik jó). Ha azon gondolkodsz, hogy „majdnem", az "reszben", nem "helyes".
- "helytelen": mást állít, kitér, felsorol, vagy nem válaszol
- "hallucinacio": magabiztosan állít KONKRÉT, kitalált tényeket (nevet, dátumot, helyet, címet),
  amelyek tévesek. Ha a válasz konkrét és téves, ez az ítélet, nem a "helytelen".

Fontos:
- A várt válasz a helyes megoldás. Bőbeszédűség nem hiba.
- Más nyelvű válasz önmagában NEM hiba.
- Ha jelezzük, hogy a válasz elvágódott vagy ismétlési hurokba esett, CSAK a meglévő szövegrészt
  értékeld: amit leírt, az alapján ítélj, a hiányzót ne rójuk fel.
- A válasz VÉGÉN álló önértékelő/feladatkiíró toldalék (ha maradt) nem része a válasznak.

Válaszolj CSAK egy JSON objektummal: {"itelet": "...", "indoklas": "<egy rövid mondat>"}"""

RUBRIKAK = {"orig": RUBRIKA, "hard": RUBRIKA_HARD}


def call(messages, timeout=120, retries=3):
    # ⛔ A qwen36 ALAPBÓL gondolkodik: `enable_thinking` nélkül a teljes token-keret a belső
    # monológra megy, a `content` pedig None-ként jön vissza (mérve: finish_reason="length",
    # content=None). A bírálat egyszerű egyeztetés, nem kell hozzá lánc — kikapcsoljuk.
    body = json.dumps({"model": MODEL, "messages": messages, "temperature": 0,
                       "max_tokens": 300,
                       "chat_template_kwargs": {"enable_thinking": False}}).encode("utf-8")
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                content = json.loads(r.read())["choices"][0]["message"]["content"]
            if not content:
                raise ValueError("üres content a bírálótól")
            return content
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
            last = exc
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"a bíráló nem válaszolt {retries} próbálkozásra: {last}")


def parse(text):
    """A modell néha kódblokkba teszi vagy magyaráz mellé — a JSON-t kell kinyerni."""
    m = re.search(r"\{[^{}]*\"itelet\"[^{}]*\}", text, re.S)
    if not m:
        return None, text.strip()[:200]
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, text.strip()[:200]
    it = str(d.get("itelet", "")).lower().strip()
    it = {"helyes": "helyes", "reszben": "reszben", "részben": "reszben", "helytelen": "helytelen",
          "hallucinacio": "hallucinacio", "hallucináció": "hallucinacio"}.get(it)
    return it, str(d.get("indoklas", ""))[:300]


def strip_label(prompt):
    """A sablon nyitósorából a puszta kérdés. ⛔ A kínainál a kettőspont TELJES SZÉLESSÉGŰ
    (`问题：`), ezért az ASCII `": "` szerinti vágás ott bennhagyná a címkét."""
    first = prompt.split("\n")[0]
    for label in ("Kérdés: ", "Question: ", "问题："):
        if first.startswith(label):
            return first[len(label):]
    return first

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--threads", type=int, default=4, help="a prod kiszolgálót ne terheljük túl")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--rubric", choices=sorted(RUBRIKAK), default="orig",
                    help="orig = a mért körök rubrikája (alapértelmezés); hard = szigorított. "
                         "⛔ Váltani CSAK mindkét körön egyszerre szabad.")
    args = ap.parse_args()
    rubrika = RUBRIKAK[args.rubric]

    rows = [json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    facts = [r for r in rows if r["kind"] == "fact"]
    out_path = RES / "judge.jsonl"
    done = {}
    if out_path.exists() and not args.force:
        done = {(d["item_id"], d["lang"]): d for d in
                (json.loads(l) for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip())}
    todo = [r for r in facts if (r["item_id"], r["lang"]) not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(facts)} faktuális válasz · kész {len(done)} · most {len(todo)}", flush=True)

    lock = threading.Lock()
    results, errors = [], []

    def work(r):
        note = []
        if r["truncated"]:
            note.append("a válasz a token-keretbe ütközött (elvágódott)")
        if r["degenerate"]:
            note.append("a válasz ismétlési hurokba esett")
        user = (f"Kérdés ({r['lang']}): {r['q']}\n"
                f"Várt válasz: {r['expected']}\n"
                f"A modell válasza: {r.get('text_clean', r['text'])}\n"
                + (f"Megjegyzés: {', '.join(note)}.\n" if note else ""))
        text = call([{"role": "system", "content": rubrika}, {"role": "user", "content": user}])
        verdict, reason = parse(text)
        rec = {"item_id": r["item_id"], "group": r["group"], "lang": r["lang"],
               "expected": r["expected"], "answer": r["text"],
               "truncated": r["truncated"], "degenerate": r["degenerate"],
               "judge": verdict, "judge_reason": reason, "judge_raw": None if verdict else text[:500],
               "rubric": args.rubric}
        with lock:
            results.append(rec)
            if verdict is None:
                errors.append((r["item_id"], r["lang"]))
            n = len(results)
            if n % 20 == 0 or n == len(todo):
                print(f"  {n}/{len(todo)} …", flush=True)

    # a kérdés szövege a prompts.jsonl-ből (a gen.jsonl csak a választ tárolja)
    prompts = {(p["item_id"], p["lang"]): p for p in
               (json.loads(l) for l in (HERE / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    for r in todo:
        r["q"] = strip_label(prompts[(r["item_id"], r["lang"])]["prompt"])

    t0 = time.time()
    threads = []
    queue = list(todo)
    qlock = threading.Lock()

    def loop():
        while True:
            with qlock:
                if not queue:
                    return
                r = queue.pop()
            try:
                work(r)
            except Exception as exc:                      # egy elszállt hívás ne vigye el a kört
                with lock:
                    errors.append((r["item_id"], r["lang"], str(exc)[:120]))

    for _ in range(args.threads):
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    allrecs = list(done.values()) + results
    allrecs.sort(key=lambda d: (d["item_id"], d["lang"]))
    out_path.write_text("\n".join(json.dumps(d, ensure_ascii=False) for d in allrecs) + "\n", encoding="utf-8")
    print(f"bírálat kész {time.time() - t0:.0f}s alatt — {len(allrecs)} ítélet, hibás/olvashatatlan: {len(errors)}")
    if errors:
        print("  ", errors[:5])

    # ── scores.csv — a ellenőrző oszlopot én töltöm ki ─────────────────────
    # ⛔ Az újrafuttatás NEM veszítheti el a ellenőrző kört: a meglévő `manual` értékeket
    # (item_id, lang) kulcson átmentjük. Enélkül egy ártatlan `python3 src/judge.py`
    # némán kinullázná a több órás ellenőrző bírálatt.
    sc_path = RES / "scores.csv"
    keep = {}
    if sc_path.exists():
        for r in csv.DictReader(sc_path.open(encoding="utf-8")):
            v = (r.get("manual") or "").strip()
            if v:
                keep[(r["item_id"], r["lang"])] = v
        if keep:
            print(f"megőrzött ellenőrző ítéletek: {len(keep)}")
    with sc_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "group", "lang", "expected", "judge", "manual", "final",
                    "truncated", "degenerate", "judge_reason", "answer"])
        for d in allrecs:
            man = keep.get((d["item_id"], d["lang"]), "")
            w.writerow([d["item_id"], d["group"], d["lang"], d["expected"], d["judge"], man,
                        man or d["judge"],
                        int(d["truncated"]), int(d["degenerate"]), d["judge_reason"],
                        d["answer"].replace("\n", " ")[:400]])
    print(f"→ {sc_path} ({len(allrecs)} sor; a `manual` oszlop kitöltésre vár, {len(keep)} már kitöltve)")


if __name__ == "__main__":
    main()
