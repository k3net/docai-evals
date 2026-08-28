#!/usr/bin/env python3
"""Magyar KIE eval harness — OpenAI-kompatibilis endpointra.

A terv §2 metodikája szerint:
  · greedy (temperature=0), azonos max_tokens, minden item 3× (mediánra / többségi kimenetre pontozunk)
  · nincs guided/constrained decoding — a JSON-séma betartása maga is mérés
  · megengedő parser (code fence, elé/utána szöveg lehántása), de a formátumsértést külön mérjük
  · egységes magyar rendszerprompt, a feladatszöveg bájtra azonos minden modellnél

Használat:
    python3 src/harness.py --url http://DEV_SPARK:8380 --model local --cimke flash-iq4xs
"""
from __future__ import annotations
import argparse, hashlib, json, re, sys, time, urllib.request
from collections import Counter
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

    ⛔⛔ MÉRT eset (2026-08-27, qwen36 @ the dev DGX Spark): a vLLM `200 OK`-t naplózott és
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
    ap.add_argument("--out", default=None)
    ap.add_argument("--folytat", action="store_true",
                    help="a kimeneti fájlban MÁR PONTOZOTT itemeket kihagyja. ⛔ Azért kell, "
                         "mert egy 217k tokenes item ~24 perc: újraindításnál nem szabad "
                         "elölről kezdeni. Az itemenkénti mentés miatt ez mindig biztonságos.")
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
    print(f"[i] {len(items)} item × {a.futasok} futás = {len(items)*a.futasok} kérés", file=sys.stderr)

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

    for n, item in enumerate(items, 1):
        uz = felhasznaloi_uzenet(item)
        futasok = []
        for f in range(a.futasok):
            try:
                extra = {"cache_prompt": False} if a.nincs_cache else None
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
        jok = [f for f in futasok if "hiba" not in f]
        # többségi kimenet: a leggyakoribb sha; döntetlennél az első
        shak = Counter(f["sha"] for f in jok)
        fo = next((f for f in jok if shak and f["sha"] == shak.most_common(1)[0][0]), None)
        pont = pontoz_item(item, fo["pred"] if fo else None)
        instabil = len(shak) > 1
        eredmenyek.append({"id": item["id"], "teszt": item["teszt"], "pont": pont,
                           "instabil": instabil, "kulonbozo_kimenetek": len(shak),
                           "formatum_hiba": fo["formatum_hiba"] if fo else "nincs válasz",
                           "futasok": futasok})
        print(f"[{n}/{len(items)}] {item['id']:7s} {pont['pont']:5.2f}/{pont['max']} "
              f"{'⚠️instabil' if instabil else ''} {fo['formatum_hiba'] or '' if fo else 'HIBA'}",
              file=sys.stderr, flush=True)
        # ⛔ itemenként mentünk: egy megakadt futás ne vigye el az addigi munkát
        reszut = Path(a.out or f"reports/futas__{a.cimke}.json")
        reszut.parent.mkdir(exist_ok=True)
        reszut.write_text(json.dumps({"cimke": a.cimke, "args": vars(a),
                                      "kesz": len(eredmenyek), "eredmenyek": eredmenyek},
                                     ensure_ascii=False, indent=1))

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
