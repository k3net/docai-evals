"""F4/3 — szerző-klasszifikátor: objektív stílus-metrika LLM-bíró nélkül.

Ha egy Petőfi-promptra generált szöveget egy FÜGGETLENÜL tanított
klasszifikátor Petőfinek osztályoz, az stílus-transzfer bizonyíték. Nem
ízlés, nem LLM-vélemény: mérés.

A klasszifikátor karakter- és szó-n-gramokon dolgozik (TF-IDF + logisztikus
regresszió). Két dolgot mér egyszerre:

  * **stílus-transzfer** — a generált szöveget a célszerzőnek osztályozza-e;
  * **irányíthatóság** — a két szerző között tud-e váltani a modell.

Fontos részletek, amelyek nélkül a szám nem érne semmit:

  * a klasszifikátor a korpusz **train** szeletén tanul, és a **holdout**
    szeleten validálódik — ugyanaz a mű-szintű split, mint az F1-ben;
  * a tanító egységek hossza a generált versekéhez igazodik (8–16 sor),
    különben a hosszkülönbség önmagában elárulná az osztályt;
  * a mérés csak akkor értelmezhető, ha a holdout-pontosság érdemben jobb a
    véletlennél — ezt a riport kiírja.

    python3 code/author_clf.py            # tanítás + validálás
    python3 code/author_clf.py --score    # a generálások osztályozása is
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from build_dataset import load_corpus, make_split, split_key, SEED
from config import REPORTS, ROOT, SOURCES

RESULTS = ROOT / "data" / "results"
BLOCK_MIN, BLOCK_MAX = 8, 16  # sor — a generált versek nagyságrendje


def blocks_from_poem(poem: dict, rng: random.Random) -> list[str]:
    """Vers → 8–16 soros szövegblokkok, strófahatáron vágva."""
    out: list[str] = []
    buf: list[str] = []
    for stanza in poem["stanzas"]:
        buf.extend(stanza)
        if len(buf) >= BLOCK_MIN:
            out.append("\n".join(buf[:BLOCK_MAX]))
            buf = []
    if len(buf) >= BLOCK_MIN:
        out.append("\n".join(buf[:BLOCK_MAX]))
    return out


def build_sets() -> tuple[list[str], list[str], list[str], list[str]]:
    rng = random.Random(SEED)
    corpus = load_corpus()
    Xtr, ytr, Xte, yte = [], [], [], []
    for key, poems in corpus.items():
        assign = make_split(poems, random.Random(SEED))
        for poem in poems:
            part = assign[split_key(poem)]
            if part == "val":
                continue
            for block in blocks_from_poem(poem, rng):
                if part == "train":
                    Xtr.append(block)
                    ytr.append(key)
                else:
                    Xte.append(block)
                    yte.append(key)
    return Xtr, ytr, Xte, yte


def make_pipeline():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import FeatureUnion, Pipeline

    return Pipeline(
        [
            (
                "feat",
                FeatureUnion(
                    [
                        ("word", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
                        # A karakter-n-gram a magyar toldalékolást és a régies
                        # helyesírást fogja meg — ez a stílus egyik hordozója.
                        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                                                 min_df=3, sublinear_tf=True)),
                    ]
                ),
            ),
            ("clf", LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")),
        ]
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true", help="a generált szövegek osztályozása is")
    # A publikált generálások a repóban az experiment `generations/` mappájában
    # vannak, nem a pipeline `data/generations/` alatt — ezért paraméter.
    ap.add_argument("--generations", default=str(ROOT / "data" / "generations"),
                    help="a style_*.jsonl fájlok könyvtára")
    args = ap.parse_args()

    from sklearn.metrics import accuracy_score, classification_report

    Xtr, ytr, Xte, yte = build_sets()
    print(f"Tanító blokkok: {len(Xtr)} · holdout blokkok: {len(Xte)}")
    pipe = make_pipeline()
    pipe.fit(Xtr, ytr)
    pred = pipe.predict(Xte)
    acc = accuracy_score(yte, pred)
    majority = max(yte.count(k) for k in set(yte)) / len(yte)
    print(f"Holdout pontosság: {acc:.1%} (többségi alaplap: {majority:.1%})")

    report = ["# F4/3 — Szerző-klasszifikátor\n",
              f"TF-IDF (szó 1–2-gram + karakter 3–5-gram) + logisztikus regresszió. "
              f"Tanítva {len(Xtr)} blokkon a **train** szeletből, validálva {len(Xte)} "
              f"**holdout** blokkon.\n",
              f"| | érték |", "|---|---:|",
              f"| holdout pontosság | **{acc:.1%}** |",
              f"| többségi alaplap | {majority:.1%} |"]
    rep = classification_report(yte, pred, output_dict=True, zero_division=0)
    for key in SOURCES:
        if key in rep:
            report.append(f"| {SOURCES[key]['author']} F1 | {rep[key]['f1-score']:.3f} |")

    if acc < 0.75:
        report.append(
            "\n⚠️ A holdout-pontosság alacsony: a klasszifikátor nem elég erős ahhoz, "
            "hogy a generált szövegek stílusáról bármit kijelentsünk. A `author_clf_acc` "
            "metrikát ilyenkor NEM szabad értelmezni.\n"
        )

    if args.score:
        gen_rows = []
        gen_dir = Path(args.generations)
        for path in sorted(gen_dir.glob("style_*.jsonl")):
            # A feltétel neve a FÁJLNÉVBŐL jön — ld. evaluate.py: a 3-epochos és az
            # 1-epochos adapter is `--condition C`-vel generál, csak a fájlnév eltérő.
            condition = path.stem.split("_", 1)[1]
            for line in path.open(encoding="utf-8"):
                rec = json.loads(line)
                text = rec["output"].strip()
                if len(text.splitlines()) >= 4:
                    gen_rows.append(
                        {"condition": condition, "target": rec["item"]["source_key"], "text": text}
                    )
        if gen_rows:
            preds = pipe.predict([r["text"] for r in gen_rows])
            for row, p in zip(gen_rows, preds):
                row["predicted"] = p
            report.append("\n## A generált szövegek osztályozása\n")
            report.append("| feltétel | célszerző | n | eltalálva (`author_clf_acc`) |")
            report.append("|---|---|---:|---:|")
            for cond in sorted({r["condition"] for r in gen_rows}):
                for target in sorted({r["target"] for r in gen_rows}):
                    sub = [r for r in gen_rows if r["condition"] == cond and r["target"] == target]
                    if not sub:
                        continue
                    hit = sum(r["predicted"] == r["target"] for r in sub) / len(sub)
                    report.append(f"| {cond} | {SOURCES[target]['author']} | {len(sub)} | {hit:.1%} |")
            RESULTS.mkdir(parents=True, exist_ok=True)
            (RESULTS / "author_clf.json").write_text(
                json.dumps({"holdout_accuracy": acc, "rows": gen_rows}, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            print("Nincs osztályozható generálás (data/generations/style_*.jsonl)")

    (REPORTS / "07_szerzo_klasszifikator.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Riport: {REPORTS / '07_szerzo_klasszifikator.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
