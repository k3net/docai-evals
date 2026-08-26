#!/usr/bin/env python3
"""Tanítókorpusz a tuned lenshez — háromnyelvű Wikipédia-kivonatok.

    python3 code/fetch_lens_corpus.py                              # teljes korpusz, ~2 perc
    python3 code/fetch_lens_corpus.py --append --lang en --batches 60   # utántöltés egy nyelvre

Miért Wikipédia? Mert a tuned lens fordítóit olyan szövegen kell tanítani, ami a
vizsgált promptok DOMÉNJÉHEZ közel van (enciklopédikus tényszöveg), és mind a három
nyelven elérhető ugyanabból a forrásból. A korpusz a `data/lens_corpus.jsonl`-be
mentődik, onnantól a tanítás offline és reprodukálható (a lekérés véletlen cikkeket ad).

⚠️ A vizsgált 70 item CÍMEIT szándékosan nem használjuk — a lens tanítókorpusza és a
mérőkorpusz ne fedjen át, különben a tuned lens a mi itemjeinkre lenne ráhangolva.
"""
import argparse
import json
import pathlib

import scope_paths
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "data" / "lens_corpus.jsonl"
LANGS = ("hu", "en", "zh")
# ⚠️ Nyelvenként MÁS a hozam: a kínai Wikipédia véletlen cikkei többségükben rövid csonkok,
# ezért ott több kérés és alacsonyabb küszöb kell. A KIEGYENSÚLYOZÁS nem itt történik, hanem
# a tanításban, TOKENBEN — karakterben mérve a kínai sokszorosan alul lenne reprezentálva
# (kb. 1–1,5 karakter/token, szemben a magyar ~3-mal).
BATCHES = {"hu": 45, "en": 30, "zh": 150}
MIN_CHARS_PER_LANG = {"hu": 300, "en": 300, "zh": 120}
# ⚠️ A Wikimedia API a User-Agentben kontaktot vár. A megosztott változatban a cím
# helyőrző: futtatás előtt írd be a sajátodat (különben a lekérés 403-at kaphat).
UA = "docai-research-tuned-lens/1.0 (kutatasi celu, <kontakt e-mail>)"


def fetch(lang, seen):
    url = (f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=random"
           f"&grnnamespace=0&grnlimit=20&prop=extracts&explaintext=1&exintro=0"
           f"&exchars=5000&format=json&formatversion=2")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
    out = []
    for p in d.get("query", {}).get("pages", []):
        t = (p.get("extract") or "").strip()
        if len(t) >= MIN_CHARS_PER_LANG[lang] and p["title"] not in seen:
            seen.add(p["title"])
            out.append({"lang": lang, "title": p["title"], "text": t})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--append", action="store_true", help="a meglévő korpuszhoz fűz, nem írja felül")
    ap.add_argument("--lang", action="append", help="csak ezekre a nyelvekre (többször megadható)")
    ap.add_argument("--batches", type=int, help="kérés-szám felülírása")
    args = ap.parse_args()

    # a mérőkorpusz címei — ezeket kihagyjuk, hogy ne legyen átfedés
    titles = {json.loads(l).get("title", "") for l in
              (scope_paths.data(HERE, "items.jsonl")).read_text(encoding="utf-8").splitlines() if l.strip()}
    rows = []
    if args.append and OUT.exists():
        rows = [json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"meglévő korpusz: {len(rows)} cikk", flush=True)
    have = {r["title"] for r in rows}

    for lang in (args.lang or LANGS):
        # ⚠️ a már meglévő címek is a `seen`-be kerülnek, különben az utántöltés duplikálna
        seen = set(titles) | have
        got = []
        for i in range(args.batches or BATCHES[lang]):
            try:
                got += fetch(lang, seen)
            except Exception as exc:
                print(f"  {lang} {i}. kérés hiba: {type(exc).__name__}", flush=True)
            time.sleep(0.5)
        print(f"{lang}: {len(got)} cikk, {sum(len(g['text']) for g in got):,} karakter", flush=True)
        rows += got
        have |= {g["title"] for g in got}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    print(f"→ {OUT} ({len(rows)} cikk)")


if __name__ == "__main__":
    main()
