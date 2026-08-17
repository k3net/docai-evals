"""F0.2 — MEK HTML → vers-szintű, tisztított korpusz.

A MEK 1996–2013-as FrontPage-csomagjai szerencsés szerkezetűek: a verscím
`<h3><a name="NN">CÍM</a></h3>`, a strófa egy `<p>` blokk, a sorhatár `<br>`.
Ez azt jelenti, hogy a **strófahatárt nem kell találgatni** — a forrásban
explicit. Ez fontos: a strófahatár jelentéshordozó (a rímséma egysége), nem
whitespace-zaj, és egy plain-text forrásból (PDF/RTF) sokkal zajosabban jönne.

⚠️ A legfontosabb parse-tanulság: a versszöveg is gyakran `<table>`-be van
csomagolva (tördelési okból), ugyanúgy, mint a navigáció. Aki a táblákat
egyben dobja ki, annak némán eltűnik a versek egy része — az első futáson
a PÁZMÁN LOVAG-ból egyetlen sor („Víg ballada”) maradt. Ezért a navigációt
KÉP- és LINK-szinten távolítjuk el, a táblákat pedig kibontjuk.

Amit a parse csinál, sorrendben:
  1. dekódolás ISO-8859-2-ből + „kalapos” ô/û → ő/ű javítás (mérve)
  2. Unicode NFC normalizálás
  3. vers-szeletelés a <h3><a name> horgonyokra; a mű-kontextus a szülő
     horgonyból (`01_07` → `01` = „TOLDI”), mert 9 különböző „Első ének” van
  4. navigációs képek/linkek törlése, tábla-kibontás
  5. strófa/sor szerkezet; szakaszjelölő (I., *), keltezés és szerkesztői
     megjegyzés külön mezőbe
  6. dedup: vers-szintű normalizált hash
  7. **sor-visszanyerési arány**: a forrás <br>-einek száma vs. a kinyert
     sorok — a néma szövegvesztés így nem marad rejtve

Kimenet: `data/corpus/<author>/<poem_id>.json` + `reports/01_korpusz.md`.

    python3 code/build_corpus.py
"""

from __future__ import annotations

import hashlib
import html as html_mod
import json
import re
import sys
import unicodedata
from collections import Counter

from config import CORPUS, HAT_FIX, RAW, REPORTS, SOURCES

# --------------------------------------------------------------- minták

RE_H3 = re.compile(r"<h([1-4])[^>]*>(.*?)</h\1>", re.S | re.I)
RE_ANCHOR = re.compile(r'<a\s+name\s*=\s*"?([^">\s]+)"?[^>]*>(.*?)</a>', re.S | re.I)
RE_IMG = re.compile(r"<img[^>]*>", re.I)
RE_LINK = re.compile(r"<a\s+href[^>]*>(.*?)</a>", re.S | re.I)
RE_LAYOUT = re.compile(r"</?(?:table|tr|td|th|tbody|thead|center|div|blockquote)[^>]*>", re.I)
RE_P = re.compile(r"<p[^>]*>(.*?)(?=<p[^>]*>|</p>|<hr|<h[1-6]|\Z)", re.S | re.I)
RE_BR = re.compile(r"<br\s*/?>", re.I)
RE_TAG = re.compile(r"<[^>]+>")
RE_WS = re.compile(r"[ \t\r\f\v  ]+")

# Szakaszjelölő: római/arab szám, csillag(sor), gondolatjel-sor.
RE_SECTION = re.compile(r"^(?:[IVXLC]+|\d+)\.?$|^[*·]+$|^[-–—]{2,}$")
# Elhallgatás-jelölő: a MEK a hiányzó/kihagyott sorokat pont- vagy
# gondolatjel-sorral jelöli („. . . . .” / „- - - - -”). Ezek nem verssorok,
# és a tanítópéldába kerülve a modell megtanulná őket utánozni.
RE_DOTS = re.compile(r"^[.\-–—·\s]{5,}$")
# Keltezés: 1 soros, rövid, tartalmaz 17xx/18xx évszámot („Pest, 1847. március”).
RE_YEAR = re.compile(r"\b1[5-9]\d\d\b")
# Szerkesztői megjegyzés: teljes egészében zárójelben álló, egyetlen sor.
RE_EDITORIAL = re.compile(r"^\(.{3,120}\)\.?$")


def decode(raw: bytes, encoding: str) -> tuple[str, int]:
    """Dekódolás + kalapos ő/ű javítás. Visszaadja a cserék számát is."""
    text = raw.decode(encoding, errors="replace")
    fixes = sum(text.count(bad) for bad in HAT_FIX)
    for bad, good in HAT_FIX.items():
        text = text.replace(bad, good)
    return text, fixes


def clean_text(fragment: str) -> str:
    """HTML-töredék → sima szöveg, NFC-normalizálva, szóközök összevonva."""
    txt = RE_TAG.sub("", fragment)
    txt = html_mod.unescape(txt)
    txt = unicodedata.normalize("NFC", txt)
    txt = RE_WS.sub(" ", txt.replace("\n", " ").replace("­", ""))
    return txt.strip()


def strip_navigation(body: str) -> str:
    """Navigáció eltávolítása KÉP/LINK szinten, majd tábla-kibontás.

    A táblát nem dobjuk ki, mert a versszöveg is táblában lehet — csak a
    tördelő tageket vesszük le róla.
    """
    body = RE_IMG.sub(" ", body)
    body = RE_LINK.sub(lambda m: m.group(1), body)  # a linkszöveg maradhat
    body = RE_LAYOUT.sub(" ", body)
    return body


def split_stanza(fragment: str) -> list[str]:
    """Egy <p> blokk → sorok listája a <br>-ek mentén."""
    marked = RE_BR.sub("\x00", fragment)
    lines = [clean_text(part) for part in marked.split("\x00")]
    return [ln for ln in lines if ln and not RE_DOTS.match(ln)]


def parse_file(text: str, source_key: str, filename: str) -> tuple[list[dict], dict[str, str]]:
    """Egy MEK HTML-fájl → (versek, horgony→cím index).

    A horgony-index a mű-kontextushoz kell: a `01_07` ének szülője a `01`
    horgonyú mű. A szülő gyakran MÁSIK fájlban van (`toldi02#01_07` →
    `toldi01#01`), ezért az indexet a hívó gyűjti össze forrásonként, és a
    mű-hozzárendelés utólag történik.
    """
    heads: list[tuple[int, int, str | None, str]] = []  # start, end, anchor, cím
    for m in RE_H3.finditer(text):
        inner = m.group(2)
        am = RE_ANCHOR.search(inner)
        anchor = am.group(1) if am else None
        title = clean_text(am.group(2) if am else inner)
        if title:
            heads.append((m.start(), m.end(), anchor, title))

    anchor_index = {a: t for _, _, a, t in heads if a}

    poems: list[dict] = []
    for idx, (h_start, h_end, anchor, title) in enumerate(heads):
        if anchor is None:
            continue  # alcím, nem verskezdet — a törzs része lesz
        end = len(text)
        subtitles: list[str] = []
        for j in range(idx + 1, len(heads)):
            if heads[j][2] is not None:
                end = heads[j][0]
                break
            subtitles.append(heads[j][3])
        body = text[h_end:end]

        # A <hr> a versek elválasztója: ami utána jön, navigáció.
        hr = re.search(r"<hr[^>]*>", body, re.I)
        if hr:
            body = body[: hr.start()]
        body = strip_navigation(body)

        blocks: list[list[str]] = []
        for pm in RE_P.finditer(body):
            lines = split_stanza(pm.group(1))
            if lines:
                blocks.append(lines)

        stanzas: list[list[str]] = []
        sections: list[dict] = []
        editorial: list[str] = []
        dateline: str | None = None
        for pos, lines in enumerate(blocks):
            if len(lines) == 1:
                single = lines[0]
                if RE_SECTION.match(single):
                    sections.append({"after_stanza": len(stanzas), "label": single})
                    continue
                if single in subtitles:
                    continue
                # Keltezés csak a vers VÉGÉN, rövid soron, évszámmal.
                is_last = pos >= len(blocks) - 2
                if is_last and len(single) <= 70 and RE_YEAR.search(single):
                    dateline = single
                    continue
                if RE_EDITORIAL.match(single):
                    editorial.append(single)
                    continue
            stanzas.append(lines)

        # Alcím-heurisztika: ha az ELSŐ blokk egysoros, de a többi strófa
        # hosszabb, az nem strófa, hanem műfaji alcím („Víg ballada”,
        # „Alkalmi szesszenés”). Strófaként hagyva elrontaná a strófaszám-
        # előírást az F1 tanítópéldákban.
        # (A küszöb 2 blokk, nem 3: a „Moore után angolból” típusú fordítás-
        # jelölés gyakran egyetlen 8 soros törzs előtt áll, és 3-as küszöbbel
        # bent maradt volna — strófának számítva, a szótagszám-előírást is
        # rontva.)
        if len(stanzas) >= 2 and len(stanzas[0]) == 1 and all(len(s_) >= 2 for s_ in stanzas[1:]):
            subtitles = subtitles + [stanzas[0][0]]
            stanzas = stanzas[1:]

        if not stanzas:
            continue  # tartalomjegyzék-bejegyzés vagy csak fejezetcím

        poems.append(
            {
                "poem_id": f"{source_key}/{filename.rsplit('.', 1)[0]}#{anchor}",
                "source_file": filename,
                "anchor": anchor,
                "title": title,
                "subtitles": subtitles,
                "dateline": dateline,
                "editorial": editorial,
                "sections": sections,
                "stanzas": stanzas,
            }
        )
    return poems, anchor_index


def count_source_lines(text: str) -> int:
    """A forrásban ténylegesen jelen lévő verssorok becslése.

    Minden <br> egy sortörés, és minden nem üres <p> blokk egy záró sort ad.
    Ez felső becslés (a navigációs blokkokat is beleszámolja), de a
    NAGYSÁGRENDET pontosan adja — a néma szövegvesztés kiderül belőle.
    """
    body = strip_navigation(text)
    brs = len(RE_BR.findall(body))
    ps = sum(1 for pm in RE_P.finditer(body) if clean_text(RE_BR.sub(" ", pm.group(1))))
    return brs + ps


def norm_line(line: str) -> str:
    """Sor normalizálása dedup/összevetés céljára: kisbetű, írásjel nélkül."""
    s = unicodedata.normalize("NFC", line).lower()
    s = re.sub(r"[^\wáéíóöőúüű ]+", "", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def main() -> int:
    CORPUS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    per_source: dict[str, dict] = {}

    for key, spec in SOURCES.items():
        html_dir = RAW / key / "html"
        if not html_dir.exists():
            print(f"[{key}] hiányzik a letöltés — futtasd előbb a fetch_corpus.py-t")
            return 1

        out_dir = CORPUS / key
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("*.json"):
            old.unlink()

        hat_fixes = 0
        source_line_estimate = 0
        poems: list[dict] = []
        # (fájlcsoport, horgony) → {(fájl, cím)} — a mű-kontextushoz.
        # A horgonyok a köteten belül NEM egyediek (a `01` 30+ fájlban él),
        # ezért a névtér a fájlnév számjegyek nélküli töve („toldi01” → „toldi”).
        anchor_map: dict[tuple[str, str], set[tuple[str, str]]] = {}
        child_prefixes: set[tuple[str, str]] = set()  # (fájl, szülő-horgony)
        files = sorted(p for p in html_dir.iterdir() if p.suffix.lower() in (".htm", ".html"))
        for path in files:
            text, fixes = decode(path.read_bytes(), spec["encoding"])
            hat_fixes += fixes
            source_line_estimate += count_source_lines(text)
            file_poems, file_anchors = parse_file(text, key, path.name)
            poems.extend(file_poems)
            stem = path.stem
            base = re.sub(r"\d+$", "", stem)
            for anchor, title in file_anchors.items():
                anchor_map.setdefault((base, anchor), set()).add((stem, title))
                if "_" in anchor:
                    # Fájl-szinten gyűjtjük: a `vs*` fájlok horgonyai ütköznek,
                    # csoport-szinten hamis mű-fejléceket jelölnénk meg.
                    child_prefixes.add((stem, anchor.split("_")[0]))

        # ---- mű-kontextus: a `01_07` ének szülője a `01` horgonyú mű.
        # Kétlépcsős, hogy a `vs*` fájlok ütköző horgonyai ne adjanak hamis
        # találatot: (1) szülő ugyanabban a fájlban, (2) ha ott nincs, csak
        # akkor fogadjuk el, ha a csoportban EGYÉRTELMŰ.
        for poem in poems:
            stem = poem["source_file"].rsplit(".", 1)[0]
            base = re.sub(r"\d+$", "", stem)
            work = None
            if "_" in poem["anchor"]:
                parent = poem["anchor"].split("_")[0]
                candidates = anchor_map.get((base, parent), set())
                same_file = [t for s, t in candidates if s == stem]
                if same_file:
                    work = same_file[0]
                elif len(candidates) == 1:
                    work = next(iter(candidates))[1]
            poem["work"] = work
            poem["display_title"] = f"{work}: {poem['title']}" if work else poem["title"]
            # Mű-fejléc: van gyerek-horgonya (`19` → `19_01`), tehát a szöveg
            # nem itt van, hanem az énekekben. Ez általában cím + mottó + év —
            # nem vers, az F1 kizárja, de a `work` címét ő adja.
            poem["kind"] = (
                "work_header" if (stem, poem["anchor"]) in child_prefixes else "poem"
            )

        # ---- dedup (vers-szinten: azonos normalizált törzs = ugyanaz a vers)
        seen: dict[str, str] = {}
        unique: list[dict] = []
        duplicates: list[tuple[str, str]] = []
        for poem in poems:
            body = "\n".join(norm_line(ln) for st in poem["stanzas"] for ln in st)
            digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if digest in seen:
                duplicates.append((poem["poem_id"], seen[digest]))
                continue
            seen[digest] = poem["poem_id"]
            poem["body_sha256"] = digest
            unique.append(poem)

        # ---- statisztika
        line_counts = [sum(len(st) for st in p["stanzas"]) for p in unique]
        all_lines = [ln for p in unique for st in p["stanzas"] for ln in st]
        norm_counter = Counter(norm_line(ln) for ln in all_lines)
        repeated_lines = sum(c - 1 for c in norm_counter.values() if c > 1)

        for poem in unique:
            poem["author"] = spec["author"]
            poem["source_key"] = key
            poem["n_lines"] = sum(len(st) for st in poem["stanzas"])
            poem["n_stanzas"] = len(poem["stanzas"])
            fname = poem["poem_id"].split("/", 1)[1].replace("#", "__") + ".json"
            (out_dir / fname).write_text(
                json.dumps(poem, ensure_ascii=False, indent=1), encoding="utf-8"
            )

        extracted = sum(line_counts)
        per_source[key] = {
            "author": spec["author"],
            "files": len(files),
            "poems_raw": len(poems),
            "poems_unique": len(unique),
            "duplicates_dropped": len(duplicates),
            "duplicate_examples": duplicates[:5],
            "hat_fixes": hat_fixes,
            "lines": extracted,
            "stanzas": sum(len(p["stanzas"]) for p in unique),
            "source_line_estimate": source_line_estimate,
            "recovery_rate": round(extracted / source_line_estimate, 4) if source_line_estimate else 0.0,
            "repeated_lines": repeated_lines,
            "median_lines": sorted(line_counts)[len(line_counts) // 2] if line_counts else 0,
            "max_lines": max(line_counts) if line_counts else 0,
            "chars": sum(len(ln) for ln in all_lines),
            "words": sum(len(ln.split()) for ln in all_lines),
        }
        s = per_source[key]
        print(f"[{key}] {s['poems_unique']} vers · {s['lines']:,} sor · {s['stanzas']:,} strófa · "
              f"visszanyerés {s['recovery_rate']:.1%} · {hat_fixes} kalapos-fix · "
              f"{s['duplicates_dropped']} duplikátum")

    (CORPUS / "stats.json").write_text(
        json.dumps(per_source, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    report = ["# F0 — Korpusz (MEK, közkincs)\n",
              "Forrás és jogi állapot: `data/corpus_manifest.json`.\n",
              "| szerző | fájl | vers | sor | strófa | medián sor/vers | leghosszabb | szó | visszanyerés | dedup | kalapos-fix |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key, s in per_source.items():
        report.append(
            f"| {s['author']} | {s['files']} | {s['poems_unique']} | {s['lines']:,} | "
            f"{s['stanzas']:,} | {s['median_lines']} | {s['max_lines']:,} | {s['words']:,} | "
            f"{s['recovery_rate']:.1%} | {s['duplicates_dropped']} | {s['hat_fixes']:,} |"
        )
    report.append(
        "\n**Visszanyerés** = kinyert verssor / a forrás `<br>`+`<p>` alapú felső becslése. "
        "A 100% alatti maradék a navigációs és tartalomjegyzék-blokkokból jön; a mutató arra "
        "való, hogy a néma szövegvesztés (pl. a tábláktól elveszett versek) kiderüljön.\n"
    )
    (REPORTS / "01_korpusz.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nRiport: {REPORTS / '01_korpusz.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
