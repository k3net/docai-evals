"""03-as kör — TED-hirdetmények (HU): letöltés, CPV-nevek, PII-szűrés és a közbeszerzési család (03-runbook 3.2, 5.).

Licenc: a TED-adat szabadon újrahasznosítható (2011/833/EU), forrásmegjelöléssel. A letöltés a TED keresési API-n
(v3, bejelentkezés nélkül) megy: magyar ajánlatkérő (buyer-country=HUN), ajánlatkérési hirdetmény (form-type =
competition: ebben van leírás, és így egy eljárás csak egyszer szerepel), 2025-01-01 és 2026-09-30 között. Kérésenként
2 s szünet. A nyers válasz gzip-pel a `forras/ted/` alá kerül, a `ted03.json` rögzíti a lekérdezést és a sha256-ot.

A család (kozbeszerzes.ted_cpv): melyik CPV-főcsoportba (az első két számjegy, 45 főcsoport) tartozik a beszerzés.
  - Állapot: az eljárás címe és az első rész leírása. A `notice-title` NEM kerül bele, mert a fő CPV-kód nevét
    tartalmazza („Magyarország – Vasútépítés – …”); a szövegben előforduló 8 jegyű CPV-kódok kitakarva.
  - PII-szűrés (9. pont): ha a szövegben e-mail-cím, telefonszám, vagy kapcsolattartóra utaló szó van, a hirdetmény
    kimarad (nem kitakarjuk, hanem eldobjuk). A webcímek helyére „[hivatkozás]” kerül.
  - Duplikátum: azonos normalizált leírás csak egyszer (a legkorábbi).
  - Opciók: 2–10 főcsoportnév (a Kiadóhivatal CPV-RDF-jének magyar címkéi), 15% gold-drop X.
  - HO-forrás (5. pont): egy főcsoport kitartva. Szabály, a modelleredmények előtt rögzítve: a főcsoportok
    gyakorisági sorrendjében a 10. A gold-jú itemjei a `ho-forras` splitbe kerülnek, és a neve a train-ben
    opcióként sem fordul elő.
  - Split (a többi): a publikációs szám hash-e szerint 10% val, 10% teszt-ID, a többi train.

  python3 kor03/eszkozok/ted03.py letolt | cpv | adapter
"""

from __future__ import annotations

import gzip
import hashlib
import json
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TED = ROOT / "forras/ted"
OUT = ROOT / "adat/f0"
API = "https://api.ted.europa.eu/v3/notices/search"
QUERY = "buyer-country=HUN AND publication-date>=20250101 AND publication-date<=20260930"
FIELDS = ["publication-number", "publication-date", "form-type", "notice-type", "title-proc", "description-lot",
          "main-classification-proc", "classification-cpv"]
PAUSE_S = 2.0
SEED = "20261009"
X_SHARE = 15
HO_RANK = 10  # a gyakorisági sorrendben ennyiedik főcsoport a HO-forrás
DIVISIONS = ["03", "09", "14", "15", "16", "18", "19", "22", "24", "30", "31", "32", "33", "34", "35", "37", "38", "39",
             "41", "42", "43", "44", "45", "48", "50", "51", "55", "60", "63", "64", "65", "66", "70", "71", "72", "73",
             "75", "76", "77", "79", "80", "85", "90", "92", "98"]


def post(body: dict) -> dict:
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def letolt() -> None:
    TED.mkdir(parents=True, exist_ok=True)
    body = {"query": QUERY, "fields": FIELDS, "limit": 250, "paginationMode": "ITERATION"}
    notices, pages, total = [], 0, None
    while True:
        d = post(body)
        total = d.get("totalNoticeCount", total)
        notices += d.get("notices", [])
        pages += 1
        tok = d.get("iterationNextToken")
        print(f"{pages}. lap: {len(notices)}/{total}", flush=True)
        if not tok or not d.get("notices"):
            break
        body = {"query": QUERY, "fields": FIELDS, "limit": 250, "paginationMode": "ITERATION",
                "iterationNextToken": tok}
        time.sleep(PAUSE_S)
    raw = "".join(json.dumps(n, ensure_ascii=False) + "\n" for n in notices).encode()
    (TED / "ted_hu.jsonl.gz").write_bytes(gzip.compress(raw, mtime=0))
    man = {"api": API, "query": QUERY, "fields": FIELDS, "total": total, "letoltve": len(notices),
           "form_type": dict(Counter(n.get("form-type") for n in notices)), "sha256_jsonl": hashlib.sha256(raw).hexdigest(),
           "ido": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    (TED / "ted03.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False))


def cpv() -> None:
    out = {}
    for d in DIVISIONS:
        req = urllib.request.Request(f"http://data.europa.eu/cpv/cpv/{d}000000", headers={"Accept": "application/rdf+xml"})
        with urllib.request.urlopen(req, timeout=60) as r:
            t = r.read().decode("utf-8")
        hu = re.search(r'prefLabel xml:lang="hu">([^<]*)', t)
        en = re.search(r'prefLabel xml:lang="en">([^<]*)', t)
        out[d] = {"hu": hu.group(1) if hu else None, "en": en.group(1) if en else None,
                  "rdf_sha256": hashlib.sha256(t.encode()).hexdigest()}
        print(d, out[d]["hu"])
        time.sleep(1.0)
    (TED / "cpv_fooszt.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+36|\b06)[\s\-/()]*\d{1,2}[\s\-/()]*\d{3}[\s\-]?\d{3,4}\b|\btel(?:efon)?\.?\s*:?\s*[+\d(]", re.I)
CONTACT = re.compile(r"kapcsolattart|ügyintéző|e-mail|email", re.I)
URL = re.compile(r"https?://\S+|www\.\S+", re.I)
CPV_CODE = re.compile(r"\b\d{8}(?:-\d)?\b")


def pii(text: str) -> str | None:
    for name, rx in (("email", EMAIL), ("telefon", PHONE), ("kapcsolattarto", CONTACT)):
        if rx.search(text):
            return name
    return None


def hu(v) -> str:
    if isinstance(v, dict):
        v = v.get("hun") or []
    if isinstance(v, list):
        return v[0] if v else ""
    return v or ""


def h100(s: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{s}".encode()).hexdigest(), 16) % 100


def adapter() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from kozos03 import MAX_OPTIONS, validate

    names = {k: v["hu"] for k, v in json.loads((TED / "cpv_fooszt.json").read_text(encoding="utf-8")).items()}
    notices = [json.loads(line) for line in gzip.decompress((TED / "ted_hu.jsonl.gz").read_bytes()).decode().splitlines()]
    notices.sort(key=lambda n: (n.get("publication-date") or "", n["publication-number"]))
    why, seen, items = Counter(), set(), []
    for n in notices:
        if n.get("form-type") != "competition":
            why["kimarad: nem ajánlatkérés"] += 1
            continue
        title, desc = hu(n.get("title-proc")).strip(), hu(n.get("description-lot")).strip()
        main = (n.get("main-classification-proc") or [None])[0]
        if not title or not desc or not main or main[:2] not in names:
            why["kimarad: hiányos"] += 1
            continue
        text = f"{title}\n{desc}"
        if p := pii(text):
            why[f"kimarad: PII ({p})"] += 1
            continue
        key = re.sub(r"\W+", " ", desc.lower()).strip()
        if key in seen:
            why["kimarad: duplikátum"] += 1
            continue
        seen.add(key)
        text = CPV_CODE.sub("[CPV]", URL.sub("[hivatkozás]", text))
        if len(text) > 1500:
            text = text[:1500].rsplit(" ", 1)[0] + " […]"
        items.append((n["publication-number"], main[:2], text))
    freq = Counter(d for _, d, _ in items)
    ho = freq.most_common()[HO_RANK - 1][0]
    rows = []
    for pub, div, text in items:
        rnd = random.Random(f"{SEED}:ted:{pub}")
        ho_item = div == ho
        pool = [d for d in names if d != div and (ho_item or d != ho)]
        xdrop = h100(f"x:{pub}") < X_SHARE
        k = rnd.randint(2, min(MAX_OPTIONS, len(pool))) if xdrop else rnd.randint(1, MAX_OPTIONS - 1)
        dis = rnd.sample(pool, k)
        ids = dis + ([] if xdrop else [div])
        rnd.shuffle(ids)
        v = h100(f"split:{pub}")
        split = "ho-forras" if ho_item else ("val" if v < 10 else "test-id" if v < 20 else "train")
        rows.append({"id": f"kozbeszerzes.ted_cpv:{pub}", "family": "kozbeszerzes.ted_cpv", "group": "kozbeszerzes",
                     "source": "TED", "source_license": "EU-2011/833", "source_ref": pub, "split": split,
                     "group_id": f"kozbeszerzes.ted_cpv:{pub}", "lang": "hu", "kind": "choice", "state": text,
                     "question": "Melyik CPV-főcsoportba tartozik a beszerzés tárgya?",
                     "options": [{"id": d, "text": names[d]} for d in ids], "gold": None if xdrop else div,
                     "x_type": "gold-drop" if xdrop else None, "ketertelmu": False, "soft": None,
                     "meta": {"cpv_fo": div} | ({"ho_forras": True} if ho_item else {})})
    bad = [(r["id"], e) for r in rows if (e := validate(r))]
    if bad:
        raise SystemExit(f"{len(bad)} sémahiba, pl. {bad[:3]}")
    (OUT / "kozbeszerzes.ted_cpv.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                                   encoding="utf-8")
    rep = {"n": len(rows), "szures": dict(why), "ho_forras": {"fooszt": ho, "nev": names[ho], "n": freq[ho]},
           "split": dict(Counter(r["split"] for r in rows)), "x_arany": sum(r["gold"] is None for r in rows) / len(rows),
           "fooszt_gyakorisag": {f"{d} {names[d]}": c for d, c in freq.most_common()}}
    (OUT / "adapter_ted_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k != "fooszt_gyakorisag"}, ensure_ascii=False))
    print(list(rep["fooszt_gyakorisag"].items())[:15])


if __name__ == "__main__":
    {"letolt": letolt, "cpv": cpv, "adapter": adapter}[sys.argv[1]]()
