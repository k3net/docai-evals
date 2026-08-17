"""F1 — SFT dataset a vers-korpuszból, teljesen determinisztikusan.

A nyers vers NEM SFT-adat: abból csak nyelvi modellezés lenne, nem
irányítható generálás. Instrukció→válasz párokká alakítjuk, ahol az
**instrukció is mérésből származik** (`prosody` annotáció), nem kézi
címkézésből. Ennek két következménye van:

  * nincs LLM az adatépítésben — az eredeti runbook a témacímkézést egy
    `qwen36`-hívásra bízta volna; helyette a **verscím a téma**, ami
    determinisztikus, reprodukálható és nem terheli a prod stacket;
  * az F4-ben ugyanaz a `hu_prosody` ellenőrzi a modell kimenetét, ami az
    instrukciót előállította — a formakövetés így objektíven mérhető.

Három feladattípus:
  1. `write`    — cím + formai előírás → teljes vers (a fő feladat)
  2. `continue` — első strófa + előírás → a vers folytatása
  3. `couplet`  — egy sor → a rá rímelő következő sor

**Split: MŰ-szintű, nem vers-szintű.** A Toldi tizenkét éneke tizenkét
külön rekord, de egyetlen mű: ha a 4. ének tanításban van, a 7. pedig
holdoutban, akkor a memorizáció-mérés halott — ugyanaz a történet, ugyanazok
a szereplők, ugyanaz a rímkészlet. Ezért a split kulcsa a `work`, ha van.

    python3 src/build_dataset.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter

from pathlib import Path

from config import CORPUS, DATASET, REPORTS, SOURCES

# A prozódiai mérőeszköz a repó közös scripts/ mappájában lakik — ld.
# annotate_corpus.py. (Itt függvényen belül importáljuk, lentebb.)
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

SEED = 20260814
SPLIT = (0.80, 0.10, 0.10)  # train / val / test(holdout)

# Egy tanítópéldába beférő legnagyobb vers. A 2048 tokenes ablakba egy ~25
# strófás vers belefér; a Toldi 900+ soros énekei nem — azokból `continue` és
# `couplet` példák készülnek, `write` nem.
MAX_WRITE_STANZAS = 25
MAX_WRITE_LINES = 100

# Versenkénti kvóták. A `couplet` kvóta nélkül elnyomná a datasetet: egy
# 8 strófás versből 8 rímpár lenne, és a tanítás gradiens-lépéseinek ~80%-át
# egysoros válaszok vinnék, miközben a token-tömegnek csak ~15%-át adják.
# A `continue` kvóta ugyanezt teszi a hosszú művek ablakaival.
MAX_CONTINUE_PER_POEM = 3
MAX_COUPLET_PER_POEM = 2
# Formai előírást csak akkor teszünk a promptba, ha a vers tényleg tartja.
SCHEME_MIN_SHARE = 0.6
ISO_MIN_SHARE = 0.7
SIZE_MIN_SHARE = 0.7

SCHEME_NAMES = {
    "AABB": "AABB (páros rím)",
    "ABAB": "ABAB (keresztrím)",
    "ABBA": "ABBA (ölelkező rím)",
    "ABCB": "ABCB (félrím: csak a páros sorok rímelnek)",
    "AABA": "AABA",
    "AAAA": "AAAA (bokorrím)",
    "AABBCC": "AABBCC (páros rím)",
    "AABBCCDD": "AABBCCDD (páros rím)",
}


def load_corpus() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for key in SOURCES:
        poems = []
        for path in sorted((CORPUS / key).glob("*.json")):
            poem = json.loads(path.read_text(encoding="utf-8"))
            if poem.get("kind") != "poem" or "prosody" not in poem:
                continue
            if poem["n_lines"] < 4:
                continue
            poems.append(poem)
        out[key] = poems
    return out


def split_key(poem: dict) -> str:
    """A split egysége: a mű, ha többrészes; különben maga a vers."""
    return f"{poem['source_key']}::{poem['work']}" if poem.get("work") else poem["poem_id"]


def make_split(poems: list[dict], rng: random.Random) -> dict[str, str]:
    """Mű-szintű, determinisztikus felosztás. Visszaad: split_key → szelet."""
    keys = sorted({split_key(p) for p in poems})
    rng.shuffle(keys)
    n = len(keys)
    n_train = int(n * SPLIT[0])
    n_val = int(n * (SPLIT[0] + SPLIT[1]))
    assign = {}
    for i, k in enumerate(keys):
        assign[k] = "train" if i < n_train else ("val" if i < n_val else "test")
    return assign


def form_spec(poem: dict) -> tuple[str, dict]:
    """Formai előírás szövege + a gépi ellenőrzéshez való mezők.

    Csak azt írjuk elő, amit a vers TÉNYLEG tart — különben olyan formára
    tanítanánk, amit a példa maga sem követ.
    """
    pr = poem["prosody"]
    # Strófázatlan vers (egyetlen hosszú blokk): a strófaszám nem informatív,
    # helyette a sorszámot írjuk elő.
    if poem["n_stanzas"] == 1 and poem["n_lines"] > 12:
        parts = [f"{poem['n_lines']} sor, strófatagolás nélkül"]
        spec: dict = {"n_lines": poem["n_lines"]}
    else:
        parts = [f"{poem['n_stanzas']} strófa"]
        spec = {"n_stanzas": poem["n_stanzas"]}

    size, size_share = pr.get("dominant_stanza_size"), pr.get("regular_stanza_size")
    # Csak ésszerű strófaméretet írunk elő: a MEK-ben a strófázatlan versek
    # (hexameteres levelek) egyetlen 90+ soros blokkban állnak, és a
    # „strófánként 91 sor” előírás értelmetlen — a modell sem tudná betartani,
    # és az F4 formakövetés-metrikát is elrontaná.
    if size and size_share and size_share >= SIZE_MIN_SHARE and 2 <= size <= 12:
        parts.append(f"strófánként {size} sor")
        spec["stanza_size"] = size

    scheme, share = pr.get("dominant_scheme"), pr.get("dominant_scheme_share")
    if scheme and share and share >= SCHEME_MIN_SHARE and scheme in SCHEME_NAMES:
        parts.append(f"rímséma {SCHEME_NAMES[scheme]}")
        spec["scheme"] = scheme

    iso, mode = pr.get("isometric_share"), pr.get("syllables_mode")
    if iso and mode and iso >= ISO_MIN_SHARE:
        parts.append(f"soronként {mode} szótag")
        spec["syllables"] = mode

    return ", ".join(parts), spec


def render_poem(stanzas: list[list[str]]) -> str:
    return "\n\n".join("\n".join(st) for st in stanzas)


def build_examples(poem: dict, author: str) -> list[dict]:
    """Egy versből az összes tanítópélda."""
    spec_text, spec = form_spec(poem)
    title = poem["title"]
    stanzas = poem["stanzas"]
    base_meta = {
        "poem_id": poem["poem_id"],
        "author": author,
        "source_key": poem["source_key"],
        "work": poem.get("work"),
        "spec": spec,
    }
    out: list[dict] = []

    # 1) write — a fő feladat
    if len(stanzas) <= MAX_WRITE_STANZAS and poem["n_lines"] <= MAX_WRITE_LINES:
        out.append(
            {
                "task": "write",
                "prompt": (
                    f"Írj verset {author} modorában.\n"
                    f"Cím: {title}\n"
                    f"Forma: {spec_text}."
                ),
                "completion": render_poem(stanzas),
                "meta": base_meta,
            }
        )

    # 2) continue — a hosszú műveket is használja, ablakokban
    if len(stanzas) >= 3:
        windows = [(0, min(len(stanzas), 6))]
        if len(stanzas) > 8:  # hosszú mű: több ablak, átfedés nélkül
            windows = [(i, min(i + 6, len(stanzas))) for i in range(0, len(stanzas) - 1, 6)]
            windows = windows[:MAX_CONTINUE_PER_POEM]
        for start, end in windows:
            if end - start < 3:
                continue
            head, rest = stanzas[start], stanzas[start + 1 : end]
            if not rest:
                continue
            out.append(
                {
                    "task": "continue",
                    "prompt": (
                        f"Folytasd a verset {author} modorában, ugyanebben a formában "
                        f"({len(rest)} további strófa):\n\n" + "\n".join(head)
                    ),
                    "completion": render_poem(rest),
                    "meta": {**base_meta, "window": [start, end]},
                }
            )

    # 3) couplet — rímpár: a strófa egymást követő, RÍMELŐ sorpárjaiból
    from hu_prosody import count_syllables, rhyme_score

    couplets = 0
    for si, stanza in enumerate(poem["prosody"]["stanzas"]):
        if couplets >= MAX_COUPLET_PER_POEM:
            break
        if not stanza["syllables_reliable"] or stanza["n_lines"] < 2:
            continue
        lines = stanzas[si]
        for i in range(len(lines) - 1):
            if rhyme_score(lines[i], lines[i + 1]) >= 0.8:
                out.append(
                    {
                        "task": "couplet",
                        "prompt": (
                            f"Írj egy rímelő sorpárt {author} modorában. "
                            f"Az első sor adott, a második rímeljen rá és legyen "
                            f"{count_syllables(lines[i + 1])} szótagos.\n\n{lines[i]}"
                        ),
                        "completion": lines[i + 1],
                        "meta": {**base_meta, "stanza": si, "line": i},
                    }
                )
                couplets += 1
                break  # strófánként legfeljebb egy pár
    return out


def main() -> int:
    DATASET.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    corpus = load_corpus()
    report: list[str] = ["# F1 — SFT dataset\n"]

    for key, poems in corpus.items():
        author = SOURCES[key]["author"]
        rng = random.Random(SEED)
        assign = make_split(poems, rng)

        buckets: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
        for poem in poems:
            part = assign[split_key(poem)]
            for ex in build_examples(poem, author):
                ex["split"] = part
                buckets[part].append(ex)

        out_dir = DATASET / key
        out_dir.mkdir(parents=True, exist_ok=True)
        for part, rows in buckets.items():
            rng.shuffle(rows)
            path = out_dir / f"{part}.jsonl"
            with path.open("w", encoding="utf-8") as fh:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")

        # A holdout VERSEK külön is kellenek: az F4 memorizáció-mérés és az
        # eval-promptszett innen épül.
        holdout = [p for p in poems if assign[split_key(p)] == "test"]
        train_poems = [p for p in poems if assign[split_key(p)] == "train"]
        (out_dir / "holdout_poems.json").write_text(
            json.dumps(holdout, ensure_ascii=False), encoding="utf-8"
        )

        # Korpusz-hash: a naplóban ez azonosítja, MELYIK adaton tanítottunk.
        digest = hashlib.sha256()
        for row in sorted(buckets["train"], key=lambda r: (r["task"], r["meta"]["poem_id"])):
            digest.update((row["prompt"] + row["completion"]).encode("utf-8"))
        corpus_hash = digest.hexdigest()[:16]

        stats = {
            "author": author,
            "poems_total": len(poems),
            "poems_train": len(train_poems),
            "poems_holdout": len(holdout),
            "split_units": len(assign),
            "train": len(buckets["train"]),
            "val": len(buckets["val"]),
            "test": len(buckets["test"]),
            "tasks_train": dict(Counter(r["task"] for r in buckets["train"])),
            "corpus_hash": corpus_hash,
            "seed": SEED,
        }
        (out_dir / "stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"[{key}] {stats['train']} train / {stats['val']} val / {stats['test']} test példa "
              f"· {len(poems)} vers ({len(assign)} split-egység) · hash {corpus_hash}")
        print(f"        feladatok: {stats['tasks_train']}")

        report.append(f"\n## {author}\n")
        report.append("| szelet | példa | vers | `write` | `continue` | `couplet` |")
        report.append("|---|---:|---:|---:|---:|---:|")
        for part in ("train", "val", "test"):
            tasks = Counter(r["task"] for r in buckets[part])
            n_poems = sum(1 for p in poems if assign[split_key(p)] == part)
            report.append(
                f"| {part} | {len(buckets[part]):,} | {n_poems} | "
                f"{tasks.get('write', 0):,} | {tasks.get('continue', 0):,} | {tasks.get('couplet', 0):,} |"
            )
        report.append(f"\nKorpusz-hash (train): `{corpus_hash}` · seed `{SEED}` · "
                      f"split-egység: mű-szintű ({len(assign)} egység {len(poems)} versre).\n")

    (REPORTS / "04_dataset.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nRiport: {REPORTS / '04_dataset.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
