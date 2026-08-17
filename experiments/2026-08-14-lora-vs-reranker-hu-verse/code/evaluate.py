"""F4/2 — a generálások kiértékelése. Ez a laptopon fut, az eredmény itt marad.

Minden metrika determinisztikus: ugyanaz a `hu_prosody` méri a modell
kimenetét, ami a tanító-instrukciókat előállította. Nincs LLM-bíró.

Tengely A — a szándékolt hatás:
  `stanza_count`   a kért strófaszámot tartja-e (bináris)
  `stanza_size`    a kért strófaméretet tartja-e (soronkénti arány)
  `syllable_exact` a kért szótagszámú sorok aránya
  `scheme_match`   a kért rímséma aránya a strófákban
  `rhyme_rate`     rímelő sorpárok aránya (asszonánc-küszöb)
  `rhyme_quality`  **ugyanez ragrím nélkül** — ezt nem lehet trükkel megnyerni
  `distinct_2/3`   lexikai diverzitás (kollapszus-detektor)

Tengely C — az ár:
  `extraction`     a leghosszabb szó-n-gram egyezés az eredeti verssel,
                   TRAIN és HOLDOUT bontásban. A kettő különbsége az
                   `extraction_gap`: a holdout ág a pretraining-memorizációt
                   fogja, tehát csak a RÉS írható a LoRA számlájára.

    python3 src/evaluate.py                    # minden generations/*.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

from config import RHYME_THRESHOLD, ROOT, REPORTS

# A mérőeszköz a repó közös scripts/ mappájában lakik — ld. annotate_corpus.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import hu_prosody as hp  # noqa: E402

GENERATIONS = ROOT / "data" / "generations"
RESULTS = ROOT / "data" / "results"

# Zajszűrés a modell kimenetén: kódblokk-jelölők és a szokásos bevezető
# udvariaskodás. NEM javítjuk a verset — csak a keretet vesszük le, hogy a
# formai metrika ne a „Íme a vers:” soron bukjon el. Minden feltételen ugyanez.
RE_FENCE = re.compile(r"^\s*```[a-z]*\s*$", re.M)
RE_PREAMBLE = re.compile(
    r"^\s*(?:íme|itt (?:van|a)|tessék|a vers|kész|remélem|megjegyzés)[^\n]{0,80}:\s*$",
    re.I | re.M,
)
# Chat-artefakt: a modell néha nem áll meg a versnél, hanem új beszélgetési
# fordulót kezd (visszaköszön a rendszerprompt vagy egy `<|im_…|>` marker).
# A LoRA-ágon 2%-ot érint, a bázison 0%-ot — a levágás MINDEN feltételre
# egyformán fut, hogy az összevetés ne ezen múljon.
RE_CHAT_ARTIFACT = re.compile(
    r"^.*(?:Magyar költő vagy|<\|im_(?:start|end)\|>|^Írj verset).*$", re.M
)


def parse_poem(text: str) -> list[list[str]]:
    """Generált szöveg → strófák (üres sorral tagolt blokkok)."""
    text = RE_FENCE.sub("", text)
    text = RE_PREAMBLE.sub("", text)
    m = RE_CHAT_ARTIFACT.search(text)
    if m:
        text = text[: m.start()]
    blocks = [b for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    stanzas = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if lines:
            stanzas.append(lines)
    return stanzas


def rhyme_pairs(stanzas: list[list[str]], scheme: str | None) -> list[tuple[str, str]]:
    """Mely sorpároknak KELL rímelniük.

    Ha van kért séma, akkor az abból következő párok; ha nincs, akkor a
    szomszédos sorpárok (ez a magyar vers alapesete).
    """
    pairs: list[tuple[str, str]] = []
    for stanza in stanzas:
        if scheme and len(stanza) == len(scheme):
            groups: dict[str, list[str]] = {}
            for label, line in zip(scheme, stanza):
                groups.setdefault(label, []).append(line)
            for lines in groups.values():
                for i in range(len(lines) - 1):
                    pairs.append((lines[i], lines[i + 1]))
        else:
            for i in range(len(stanza) - 1):
                pairs.append((stanza[i], stanza[i + 1]))
    return pairs


# Szótár-ellenőrzés a KITALÁLT SZAVAK méréséhez. A megfigyelt hibamód: a modell
# a rím kikényszerítéséhez nem létező szót ír („sose legyünk bunta”, „egy kis
# babra”) — és ezt a formai metrikák JUTALMAZZÁK, mert a „bunta” tökéletesen
# rímel a „mondta”-ra. A magyar hunspell megengedő az összetételekre, ezért az
# abszolút szám felfelé torzít; a GOLD-hoz mérve viszont értelmezhető: az
# archaikus, de valódi Arany-szókincs adja a viszonyítási alapot.
_SPELL = None
_SPELL_CACHE: dict[str, bool] = {}


def _known_word(word: str) -> bool | None:
    """True/False, vagy None, ha nincs szótár (a metrika ilyenkor kimarad)."""
    global _SPELL
    if _SPELL is None:
        try:
            from spylls.hunspell import Dictionary
            _SPELL = Dictionary.from_files("/usr/share/hunspell/hu_HU")
        except Exception:
            _SPELL = False
    if _SPELL is False:
        return None
    if word not in _SPELL_CACHE:
        _SPELL_CACHE[word] = bool(_SPELL.lookup(word))
    return _SPELL_CACHE[word]


_CORPUS_VOCAB: set[str] | None = None


def _corpus_vocab() -> set[str]:
    """A korpusz teljes szóalak-készlete (73 ezer alak).

    Ez választja szét a két esetet, amit a szótár önmagában nem tud:
      * a szótárnak ismeretlen, de a korpuszban SZEREPLŐ szó → archaikus,
        valódi (a modell jól tanulta el Arany szókincsét);
      * a szótárnak ÉS a korpusznak is ismeretlen szó → **kitalált**, azaz a
        rím kikényszerítésére gyártott alak („bunta”).
    A GOLD-on az `invented_rate` definíció szerint 0 (a versek magából a
    korpuszból valók), ezért ott nem referencia, hanem tautológia.
    """
    global _CORPUS_VOCAB
    if _CORPUS_VOCAB is None:
        vocab: set[str] = set()
        for path in (ROOT / "data" / "corpus").glob("*/*.json"):
            poem = json.loads(path.read_text(encoding="utf-8"))
            if poem.get("kind") != "poem":
                continue
            for stanza in poem["stanzas"]:
                for line in stanza:
                    vocab.update(hp.normalize(line).split())
        _CORPUS_VOCAB = vocab
    return _CORPUS_VOCAB


def distinct_n(tokens: list[str], n: int) -> float:
    if len(tokens) < n:
        return 0.0
    grams = [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]
    return len(set(grams)) / len(grams)


def eval_style_record(rec: dict) -> dict:
    spec = rec["item"].get("spec", {})
    stanzas = parse_poem(rec["output"])
    lines = [ln for s in stanzas for ln in s]
    out: dict = {
        "condition": rec["condition"],
        "source_key": rec["item"]["source_key"],
        "poem_id": rec["item"]["poem_id"],
        "sample": rec["sample"],
        "n_stanzas": len(stanzas),
        "n_lines": len(lines),
        "empty": not lines,
    }
    if not lines:
        return out

    want_st = spec.get("n_stanzas")
    if want_st:
        out["stanza_count"] = float(len(stanzas) == want_st)
    want_size = spec.get("stanza_size")
    if want_size:
        out["stanza_size"] = sum(len(s) == want_size for s in stanzas) / len(stanzas)
    want_syll = spec.get("syllables")
    if want_syll:
        counts = [hp.count_syllables(ln) for ln in lines]
        out["syllable_exact"] = sum(c == want_syll for c in counts) / len(counts)
        out["syllable_near"] = sum(abs(c - want_syll) <= 1 for c in counts) / len(counts)
    scheme = spec.get("scheme")
    if scheme:
        matching = [s for s in stanzas if len(s) == len(scheme)]
        if matching:
            out["scheme_match"] = sum(
                hp.rhyme_scheme(s) == scheme for s in matching
            ) / len(matching)

    pairs = rhyme_pairs(stanzas, scheme)
    if pairs:
        rhyming = [(a, b) for a, b in pairs if hp.rhyme_score(a, b) >= RHYME_THRESHOLD]
        out["rhyme_rate"] = len(rhyming) / len(pairs)
        rich = [1 for a, b in rhyming if hp.inflectional_suffix(a, b) is None]
        out["rhyme_quality"] = len(rich) / len(pairs)
        out["rag_share"] = 1 - len(rich) / len(rhyming) if rhyming else 0.0

    # Degenerált ismétlés: a modell néha szó szerint megismétel egy strófát,
    # és attól a rímarány akár 1,0 is lehet — a forma „stimmel”, a vers nem.
    # A distinct-2 ezt csak részben fogja meg, ezért külön mérjük.
    norm_lines = [hp.normalize(ln) for ln in lines if hp.normalize(ln)]
    if norm_lines:
        out["repeat_rate"] = 1 - len(set(norm_lines)) / len(norm_lines)

    tokens = hp.normalize(" ".join(lines)).split()
    words = [w for w in tokens if len(w) > 2]
    checked = [(w, _known_word(w)) for w in words]
    checked = [(w, c) for w, c in checked if c is not None]
    if checked:
        out["oov_rate"] = 1 - sum(c for _, c in checked) / len(checked)
        vocab = _corpus_vocab()
        invented = [w for w, c in checked if not c and w not in vocab]
        out["invented_rate"] = len(invented) / len(checked)

    out["distinct_2"] = distinct_n(tokens, 2)
    out["distinct_3"] = distinct_n(tokens, 3)
    out["tokens"] = len(tokens)
    return out


def gold_rows() -> list[dict]:
    """GOLD referencia: az EREDETI versek ugyanazokkal a metrikákkal.

    Enélkül a modell számai lebegnek: nem tudjuk, hogy egy 0,62-es rímarány
    közel van-e a lehetségeshez vagy sem. A gold sor azt mutatja, mit ér el
    ugyanezen a mérőléccel maga Arany és Petőfi — ez a feladat gyakorlati
    felső korlátja, nem elméleti 1,0.

    A `stanza_count` a goldon triviálisan 1,0 (a specifikáció belőle készült),
    ezért azt a riport nem is értelmezi; a rím-, szótag- és diverzitás-értékek
    viszont valódi referenciák.
    """
    prompts = json.loads(
        (ROOT / "data" / "dataset" / "eval" / "eval_prompts.json").read_text(encoding="utf-8")
    )
    by_id = {}
    for key in ("arany", "petofi"):
        for path in (ROOT / "data" / "corpus" / key).glob("*.json"):
            poem = json.loads(path.read_text(encoding="utf-8"))
            by_id[poem["poem_id"]] = poem

    rows = []
    for item in prompts:
        poem = by_id.get(item["poem_id"])
        if not poem:
            continue
        text = "\n\n".join("\n".join(st) for st in poem["stanzas"])
        rows.append(
            eval_style_record(
                {
                    "condition": "GOLD",
                    "item": item,
                    "sample": 0,
                    "output": text,
                }
            )
        )
    return rows


def longest_common_ngram(a: str, b: str) -> int:
    """A leghosszabb közös SZÓ-n-gram hossza — a memorizáció mérőszáma."""
    wa = hp.normalize(a).split()
    wb = set()
    words_b = hp.normalize(b).split()
    best = 0
    # klasszikus DP, de csak a hosszra van szükség
    prev = [0] * (len(words_b) + 1)
    for i in range(1, len(wa) + 1):
        cur = [0] * (len(words_b) + 1)
        for j in range(1, len(words_b) + 1):
            if wa[i - 1] == words_b[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def eval_extraction_record(rec: dict, references: dict[str, str]) -> dict:
    item = rec["item"]
    ref = references.get(item["id"], "")
    n = longest_common_ngram(rec["output"], ref) if ref else 0
    return {
        "condition": rec["condition"],
        "source_key": item["source_key"],
        "split": item["split"],
        "poem_id": item["poem_id"],
        "longest_ngram": n,
        "reproduced_8": float(n >= 8),
    }


def agg(rows: list[dict], field: str) -> float | None:
    vals = [r[field] for r in rows if field in r and r[field] is not None]
    return round(st.mean(vals), 4) if vals else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--generations", default=str(GENERATIONS))
    args = ap.parse_args()
    gen_dir = Path(args.generations)
    if not gen_dir.exists():
        print(f"Nincs generálás: {gen_dir}\nFuttasd a sparkon a generate.py-t, majd szinkronizálj vissza.")
        return 1

    RESULTS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    # A memorizáció-mérés referenciái
    probes = json.loads(
        (ROOT / "data" / "dataset" / "eval" / "extraction_probes.json").read_text(encoding="utf-8")
    )
    references = {p["id"]: p["continuation"] for p in probes}

    style_rows: list[dict] = []
    extract_rows: list[dict] = []
    for path in sorted(gen_dir.glob("*.jsonl")):
        # A feltétel NEVE a fájlnévből jön, nem a rekordból: ugyanaz a generate.py
        # `--condition C`-vel fut a 3-epochos és az 1-epochos adapterrel is, csak a
        # kimeneti fájl neve különbözteti meg őket (style_C.jsonl vs style_C_ep1.jsonl).
        # Rekord-mező alapján a kettő egy sorba olvadna össze.
        condition = path.stem.split("_", 1)[1]
        for line in path.open(encoding="utf-8"):
            rec = json.loads(line)
            rec["condition"] = condition
            if rec["mode"] == "style":
                style_rows.append(eval_style_record(rec))
            else:
                extract_rows.append(eval_extraction_record(rec, references))
    style_rows += gold_rows()   # az eredeti versek ugyanazon a mérőléccel
    print(f"Betöltve: {len(style_rows)} stílus-, {len(extract_rows)} memorizáció-rekord "
          f"(ebből GOLD: {sum(1 for r in style_rows if r['condition'] == 'GOLD')})")

    (RESULTS / "style_rows.json").write_text(
        json.dumps(style_rows, ensure_ascii=False), encoding="utf-8"
    )
    (RESULTS / "extraction_rows.json").write_text(
        json.dumps(extract_rows, ensure_ascii=False), encoding="utf-8"
    )

    report = ["# F4 — Eval-gate\n"]
    metrics = [
        ("stanza_count", "strófaszám"), ("stanza_size", "strófaméret"),
        ("syllable_exact", "szótag pontos"), ("syllable_near", "szótag ±1"),
        ("scheme_match", "rímséma"), ("rhyme_rate", "rímarány"),
        ("rhyme_quality", "**rímminőség**"), ("rag_share", "ebből ragrím"),
        ("repeat_rate", "ismételt sor"), ("oov_rate", "szótáron kívüli"),
        ("invented_rate", "**kitalált szó**"), ("distinct_2", "distinct-2"),
    ]

    for key in sorted({r["source_key"] for r in style_rows}):
        rows = [r for r in style_rows if r["source_key"] == key]
        # A GOLD sor legyen legalul: ő a referencia, nem versenyző.
        conds = sorted({r["condition"] for r in rows if r["condition"] != "GOLD"})
        conds += ["GOLD"] if any(r["condition"] == "GOLD" for r in rows) else []
        report.append(f"\n## Tengely A — stílus és forma ({key})\n")
        report.append("| feltétel | n | üres | " + " | ".join(l for _, l in metrics) + " |")
        report.append("|---|---:|---:|" + "---:|" * len(metrics))
        for cond in conds:
            sub = [r for r in rows if r["condition"] == cond]
            cells = [f"{agg(sub, f):.3f}" if agg(sub, f) is not None else "—" for f, _ in metrics]
            empty = sum(r["empty"] for r in sub) / len(sub)
            report.append(f"| {cond} | {len(sub)} | {empty:.0%} | " + " | ".join(cells) + " |")

    if any(r["condition"] == "GOLD" for r in style_rows):
        report.append(
            "\nA **GOLD** sor az eredeti Arany/Petőfi versek mért értéke ugyanezzel a "
            "mérőléccel — ez a feladat gyakorlati felső korlátja. (A `strófaszám` ott "
            "értelemszerűen 1,000: a specifikáció magából a versből készült.)\n"
        )

    # --- A döntési tábla: megérte-e a LoRA?
    for key in sorted({r["source_key"] for r in style_rows}):
        rows = [r for r in style_rows if r["source_key"] == key]
        have = {r["condition"] for r in rows}
        if not {"B2", "C"} <= have:
            continue
        report.append(f"\n### Megérte-e? — C (LoRA) a baseline-okhoz mérve ({key})\n")
        report.append("| metrika | B1 (few-shot) | **B2 (few-shot+reranker)** | **C (LoRA)** | C − B2 | GOLD |")
        report.append("|---|---:|---:|---:|---:|---:|")
        for field, label in metrics:
            vals = {
                c: agg([r for r in rows if r["condition"] == c], field)
                for c in ("B1", "B2", "C", "GOLD")
            }
            if vals["C"] is None or vals["B2"] is None:
                continue
            delta = vals["C"] - vals["B2"]
            fmt = lambda v: f"{v:.3f}" if v is not None else "—"
            report.append(
                f"| {label} | {fmt(vals['B1'])} | {fmt(vals['B2'])} | {fmt(vals['C'])} | "
                f"**{delta:+.3f}** | {fmt(vals['GOLD'])} |"
            )
        report.append(
            "\nA **B2 a valódi ellenfél**: a determinisztikus reranker pontosan azokat a "
            "formai metrikákat optimalizálja, amelyeket mérünk. A `C − B2` oszlop mutatja, "
            "mit tesz hozzá a LoRA azon felül, amit egy jó prompt és egy olcsó utószűrő "
            "önmagában is tud. A **rímminőség** (ragrím nélküli rím) az a metrika, amit a "
            "reranker nem tud trükkel megnyerni.\n"
        )

    if extract_rows:
        report.append("\n## Tengely C — memorizáció (`extraction_gap`)\n")
        report.append("| feltétel | szerző | train n-gram | holdout n-gram | **gap** | train ≥8 szó | holdout ≥8 szó |")
        report.append("|---|---|---:|---:|---:|---:|---:|")
        for cond in sorted({r["condition"] for r in extract_rows}):
            for key in sorted({r["source_key"] for r in extract_rows}):
                sub = [r for r in extract_rows if r["condition"] == cond and r["source_key"] == key]
                tr = [r for r in sub if r["split"] == "train"]
                ho = [r for r in sub if r["split"] == "holdout"]
                if not tr or not ho:
                    continue
                gap = st.mean([r["longest_ngram"] for r in tr]) - st.mean([r["longest_ngram"] for r in ho])
                report.append(
                    f"| {cond} | {key} | {st.mean([r['longest_ngram'] for r in tr]):.2f} | "
                    f"{st.mean([r['longest_ngram'] for r in ho]):.2f} | **{gap:+.2f}** | "
                    f"{st.mean([r['reproduced_8'] for r in tr]):.0%} | "
                    f"{st.mean([r['reproduced_8'] for r in ho]):.0%} |"
                )
        report.append(
            "\nA **holdout** oszlop a kontroll: azt méri, mennyit reprodukál a modell "
            "olyan versből, amit MI nem tanítottunk — ez a pretrainingből jön. "
            "Csak a **gap** írható a LoRA számlájára.\n"
        )

    (REPORTS / "06_eval.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Riport: {REPORTS / '06_eval.md'}")
    print("\n".join(l for l in report if l.startswith("|")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
