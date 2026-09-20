#!/usr/bin/env python3
"""Magyar KIE eval harness — OpenAI-kompatibilis endpointra.

A terv §2 metodikája szerint:
  · greedy (temperature=0), azonos max_tokens, minden item 3× (mediánra / többségi kimenetre pontozunk)
  · nincs guided/constrained decoding — a JSON-séma betartása maga is mérés
  · megengedő parser (code fence, elé/utána szöveg lehántása), de a formátumsértést külön mérjük
  · egységes magyar rendszerprompt, a feladatszöveg bájtra azonos minden modellnél

Használat:
    python3 src/harness.py --url http://<remote-host> --model local --cimke flash-iq4xs
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, threading, time, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pontozo import pontoz_item, norm_szoveg

RENDSZERPROMPT = (
    "Magyar dokumentumfeldolgozó asszisztens vagy. Kizárólag a megadott dokumentum alapján "
    "válaszolj. A választ pontosan a kért JSON-sémában add vissza, minden más szöveg nélkül. "
    "Ha egy kért adat nem szerepel a dokumentumban, az értéke legyen: \"nincs az iratban\"."
)

def dokumentum_szoveg(nevek):
    C = Path("corpus")
    return "\n\n".join(f"===== {n} =====\n\n" + (C / n).read_text() for n in nevek)

def felhasznaloi_uzenet(item):
    return (
        dokumentum_szoveg(item["dokumentumok"])
        + "\n\n===== FELADAT =====\n\n"
        + item["prompt"]
        + "\n\n===== A VÁLASZ JSON-SÉMÁJA =====\n\n"
        + json.dumps(item["sema"], ensure_ascii=False, indent=2)
        + "\n\nKizárólag a fenti séma szerinti JSON-t add vissza."
    )

def kinyer_json(txt):
    if not txt:
        return None, "üres válasz"
    t = txt.strip()
    if "</think>" in t:
        t = t.split("</think>")[-1].strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    tiszta = fence.group(1).strip() if fence else t
    try:
        return json.loads(tiszta), None
    except Exception:
        pass
    m = re.search(r"\{.*\}", tiszta, re.S)
    if m:
        try:
            return json.loads(m.group(0)), "elé/utána szöveg"
        except Exception as e:
            return None, f"parse-hiba: {type(e).__name__}"
    return None, "nincs JSON a válaszban"

def hivas(url, model, uzenet, max_tokens, timeout, extra=None, ujraprobak=2):
    """Egy chat/completions kérés.

    ⛔⛔ MÉRT eset (2026-08-27, qwen36 @ measurement-host): a vLLM `200 OK`-t naplózott és
    `Running: 0 reqs`-re állt, a kliens TCP-kapcsolata mégis ESTAB maradt 0 bájt
    sorral — a harness 49 percig BLOKKOLT egy már befejezett kérésen. A `Connection:
    close` + rövid, valóban eldurranó timeout + újrapróba ellene véd. NÉMA leállás
    helyett hangos hiba kell.
    """
    payload = {"model": model, "temperature": 0.0, "top_p": 1, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": RENDSZERPROMPT},
                            {"role": "user", "content": uzenet}]}
    if extra:
        payload.update(extra)
    if extra and extra.get("_logprobs_ki"):
        # a szonda formátuma: logprobs + token_id-k; a kulcs magát nem küldjük el
        payload.pop("_logprobs_ki", None)
        payload.update(logprobs=True, top_logprobs=20, return_tokens_as_token_ids=True,
                       return_token_ids=True)
    utolso = None
    for proba in range(ujraprobak + 1):
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json",
                                              "Connection": "close"})
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = json.loads(r.read().decode())
            return body, (time.monotonic() - t0) * 1000
        except Exception as e:
            utolso = e
            print(f"    ⚠️ kérés-hiba ({proba+1}/{ujraprobak+1}): {type(e).__name__}: "
                  f"{str(e)[:120]}", file=sys.stderr, flush=True)
            time.sleep(5)
    raise utolso

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", default="local")
    ap.add_argument("--cimke", required=True, help="a futás címkéje (riportokhoz)")
    ap.add_argument("--futasok", type=int, default=3, help="itemenkénti ismétlés (terv §2)")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--timeout", type=float, default=300,
                help="⛔ a leghosszabb mért valós kérés 89,6 s — a 300 s bőven elég, "
                     "és a beragadt kapcsolat így ELDURRAN, nem csendben áll")
    ap.add_argument("--csak", default=None, help="csak ezek a tesztek, pl. T1,T5")
    ap.add_argument("--items", default="gt/items.jsonl")
    ap.add_argument("--parallel", type=int, default=1,
                    help="egyszerre ennyi ITEM fut (az itemen belüli ismétlések "
                         "továbbra is sorosak). ⛔ MÉRT (2026-09-18, qwen36 @ measurement-host): "
                         "sorosan 40 s/kérés, azaz 150×3 = 450 kérés ~5 ÓRA karonként — "
                         "kilenc karral kivihetetlen. A párhuzamosítás nem ingyen van: "
                         "a kötegméret befolyásolhatja a greedy kimenetet, ezért az "
                         "értékét a jegyzőkönyvbe kell írni, és a sorossal való "
                         "egyezést item-szinten IGAZOLNI kell (ld. csapda_parhuzam_teszt).")
    ap.add_argument("--item-ids", default=None,
                    help="vesszős lista: csak ezek az item-azonosítók futnak "
                         "(a párhuzamosítás validálásához kell egy részhalmaz)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--folytat", action="store_true",
                    help="a kimeneti fájlban MÁR PONTOZOTT itemeket kihagyja. ⛔ Azért kell, "
                         "mert egy 217k tokenes item ~24 perc: újraindításnál nem szabad "
                         "elölről kezdeni. Az itemenkénti mentés miatt ez mindig biztonságos.")
    # ⭐ 2026-09-19 (cjk-csillapítás F3): a csapda a TERMELÉSI mintavételi profilon is
    # fusson, és rögzítse a top-20 logprobot a Han-szonda rekordformátumában — így a 150
    # generált magyar irat Han-kockázat-bemenet lesz (ügyféladat nélkül, ~165 000 pozíció).
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--top-p", type=float, default=1.0)
    ap.add_argument("--top-k", type=int, default=None)
    ap.add_argument("--presence-penalty", type=float, default=None)
    ap.add_argument("--repetition-penalty", type=float, default=None)
    ap.add_argument("--seed", type=int, default=None, help="kérésenként küldött seed (+futásindex)")
    ap.add_argument("--logprobs-ki", default=None,
                    help="könyvtár: ide ír kérésenként egy JSON-t a han_probe.py rekordformátumában "
                         "(logprobs=True, top_logprobs=20, token_ids) — a han_kockazat.py bemenete")
    ap.add_argument("--nincs-cache", action="store_true",
                    help="⛔ llama.cpp: `cache_prompt: false` minden kérésnél. A runbook MÉRT "
                         "leletje szerint a greedy kimenet MEGVÁLTOZIK a prompt-cache állapotától "
                         "nagy prompton (14 716 token: hideg 6 174 token érvényes JSON, "
                         "cache-elt 8 192 token ÜRES) — hosszú kontextusban ezt ki kell zárni.")
    a = ap.parse_args()

    base = a.url.rstrip("/")
    if not re.search(r"/v\d+$", base):
        base += "/v1"
    ep = base + "/chat/completions"

    items = [json.loads(l) for l in Path(a.items).read_text().splitlines() if l.strip()]
    if a.csak:
        szuro = set(a.csak.split(","))
        items = [i for i in items if i["teszt"] in szuro]
    if a.item_ids:
        kert = set(a.item_ids.split(","))
        items = [i for i in items if i["id"] in kert]
    print(f"[i] {len(items)} item × {a.futasok} futás = {len(items)*a.futasok} kérés", file=sys.stderr)
    if a.logprobs_ki:
        Path(a.logprobs_ki).mkdir(parents=True, exist_ok=True)
        (Path(a.logprobs_ki) / "summary.json").write_text(json.dumps(
            {"arm": a.cimke, "mode": "csapda", "sampling_profile": "harness",
             "overrides": {"temperature": a.temperature, "top_p": a.top_p, "top_k": a.top_k,
                           "presence_penalty": a.presence_penalty,
                           "repetition_penalty": a.repetition_penalty, "seed": a.seed},
             "instrumented": True}, ensure_ascii=False))

    eredmenyek = []
    if a.folytat:
        korabbi = Path(a.out or f"reports/futas__{a.cimke}.json")
        if korabbi.exists():
            eredmenyek = json.loads(korabbi.read_text()).get("eredmenyek", [])
            kesz = {e["id"] for e in eredmenyek}
            elotte = len(items)
            items = [i for i in items if i["id"] not in kesz]
            print(f"[i] folytatás: {len(kesz)} item már kész, {len(items)} van hátra "
                  f"({elotte} összesen)", file=sys.stderr)

    lakat = threading.Lock()
    reszut = Path(a.out or f"reports/futas__{a.cimke}.json")
    reszut.parent.mkdir(exist_ok=True)

    def dolgozik(nitem):
        n, item = nitem
        uz = felhasznaloi_uzenet(item)
        futasok = []
        for f in range(a.futasok):
            try:
                extra = {"cache_prompt": False} if a.nincs_cache else {}
                # mintavételi profil (alapértelmezés: greedy, ahogy eddig)
                if a.temperature > 0:
                    extra.update(temperature=a.temperature, top_p=a.top_p)
                    if a.top_k is not None: extra["top_k"] = a.top_k
                    if a.presence_penalty is not None: extra["presence_penalty"] = a.presence_penalty
                    if a.repetition_penalty is not None: extra["repetition_penalty"] = a.repetition_penalty
                if a.seed is not None:
                    extra["seed"] = a.seed + f
                if a.logprobs_ki:
                    extra["_logprobs_ki"] = True
                extra = extra or None
                body, wall = hivas(ep, a.model, uz, a.max_tokens, a.timeout, extra=extra)
            except Exception as e:
                futasok.append({"hiba": f"{type(e).__name__}: {str(e)[:200]}"})
                print(f"    ⛔ {item['id']} {f+1}. futás VÉGLEG elbukott: {type(e).__name__}",
                      file=sys.stderr, flush=True)
                continue
            ch = body["choices"][0]
            txt = ch["message"].get("content") or ""
            # ⭐ MÉRT (2026-08-28, NVFP4): az instabil itemeknél a `content` hossza azonos, a
            # kimeneti tokenszám mégis 765/570/1069 → az elágazás a GONDOLKODÁSBAN történik.
            # A reasoning-parser leválasztja; tároljuk, hogy az első eltérő token megtalálható legyen.
            gond = ch["message"].get("reasoning_content") or ch["message"].get("reasoning") or ""
            pred, formhiba = kinyer_json(txt)
            futasok.append({
                "nyers": txt[:2000], "pred": pred, "formatum_hiba": formhiba,
                "gondolkodas": gond, "gondolkodas_sha": hashlib.sha256(gond.encode()).hexdigest()[:12],
                "finish": ch.get("finish_reason"), "usage": body.get("usage") or {},
                "timings": body.get("timings") or {}, "wall_ms": round(wall, 1),
                "sha": hashlib.sha256(txt.encode()).hexdigest()[:12],
            })
            if a.logprobs_ki:
                # A han_probe.py rekordformátuma, hogy a han_kockazat.py változatlanul olvassa.
                # A fájlnév számmal kezdődik (a kockázatszámító `[0-9]*.json`-t keres).
                kd = Path(a.logprobs_ki); kd.mkdir(parents=True, exist_ok=True)
                minta = {k: extra[k] for k in ("temperature", "top_p", "top_k", "presence_penalty",
                                               "repetition_penalty", "seed") if extra and k in extra}
                eff = {k: minta.get(k, "<server default>") for k in
                       ("temperature", "top_p", "top_k", "min_p", "presence_penalty",
                        "repetition_penalty", "frequency_penalty", "seed")}
                rek = {"arm": a.cimke, "mode": "csapda", "case_id": item["id"], "role": "csapda",
                       "sampling_profile": "harness", "instrumented": True,
                       "effective_sampling": eff, "request": dict(minta, model=a.model,
                                                                   max_tokens=a.max_tokens),
                       "response": body, "seconds": wall / 1000,
                       "stats": {"has_final_content": bool(txt),
                                 "final_han": re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff]+", txt),
                                 "content_sha256": hashlib.sha256(txt.encode()).hexdigest()}}
                (kd / f"{n:03d}-{f:03d}__{item['id']}.json").write_text(
                    json.dumps(rek, ensure_ascii=False))
        jok = [f for f in futasok if "hiba" not in f]
        # többségi kimenet: a leggyakoribb sha; döntetlennél az első
        shak = Counter(f["sha"] for f in jok)
        fo = next((f for f in jok if shak and f["sha"] == shak.most_common(1)[0][0]), None)
        pont = pontoz_item(item, fo["pred"] if fo else None)
        instabil = len(shak) > 1
        sor = {"id": item["id"], "teszt": item["teszt"], "pont": pont,
               "instabil": instabil, "kulonbozo_kimenetek": len(shak),
               "formatum_hiba": fo["formatum_hiba"] if fo else "nincs válasz",
               "futasok": futasok}
        # ⛔ itemenként mentünk: egy megakadt futás ne vigye el az addigi munkát
        with lakat:
            eredmenyek.append(sor)
            print(f"[{len(eredmenyek)}/{len(items)}] {item['id']:7s} "
                  f"{pont['pont']:5.2f}/{pont['max']} "
                  f"{'⚠️instabil' if instabil else ''} "
                  f"{fo['formatum_hiba'] or '' if fo else 'HIBA'}",
                  file=sys.stderr, flush=True)
            reszut.write_text(json.dumps({"cimke": a.cimke, "args": vars(a),
                                          "kesz": len(eredmenyek), "eredmenyek": eredmenyek},
                                         ensure_ascii=False, indent=1))

    if a.parallel > 1:
        print(f"[i] párhuzamosság: {a.parallel} item egyszerre", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=a.parallel) as pool:
            list(pool.map(dolgozik, enumerate(items, 1)))
    else:
        for ni in enumerate(items, 1):
            dolgozik(ni)

    # A párhuzamos befejezési sorrend nem determinisztikus — az item-sorrendet
    # visszaállítjuk, hogy két futás kimenete összehasonlítható maradjon.
    sorrend = {it["id"]: k for k, it in enumerate(items)}
    eredmenyek.sort(key=lambda e: sorrend.get(e["id"], 1 << 30))

    out = a.out or f"reports/futas__{a.cimke}.json"
    Path(out).parent.mkdir(exist_ok=True)
    Path(out).write_text(json.dumps({"cimke": a.cimke, "args": vars(a),
                                     "eredmenyek": eredmenyek}, ensure_ascii=False, indent=1))
    ossz = sum(e["pont"]["pont"] for e in eredmenyek)
    maxi = sum(e["pont"]["max"] for e in eredmenyek)
    print(f"\n=== {a.cimke}: {ossz:.2f} / {maxi} pont ===", file=sys.stderr)
    print(f"formátumsértés: {sum(1 for e in eredmenyek if e['formatum_hiba'])}/{len(eredmenyek)} · "
          f"instabil: {sum(1 for e in eredmenyek if e['instabil'])}/{len(eredmenyek)}", file=sys.stderr)
    print(f"mentve: {out}", file=sys.stderr)

if __name__ == "__main__":
    main()
