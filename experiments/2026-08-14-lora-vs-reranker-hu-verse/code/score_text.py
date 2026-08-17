"""Kézzel bemásolt versek bemérése UGYANAZZAL a mérőléccel, mint a mérési ágak.

Miért kell: a cikkbe olyan versek is bekerülnek, amiket nem a mérési pipeline
generált (külső szolgáltatás webes felületén született kimenetek). Ha ezeket
szemre ítélnénk meg, az egész mérés hitelét vinné el. Ez a script az
`evaluate.eval_style_record()`-ot hívja — bit szerint ugyanazt a rímküszöböt,
ragrím-detektort és kétlépcsős kitalált-szó mérést kapják.

⚠️ A first-shot és a best-of-8 kimenetek NEM egyenrangúak: a reranker 8 jelölt
közül válogat. Ezért az `arm` mezőben rögzítjük, melyik ág mit kapott, és a
táblázat is így jelöli.

    python3 code/score_text.py --input data/demo_external.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# A mérőeszköz a repó közös scripts/ mappájában lakik — ld. annotate_corpus.py.
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))

import hu_prosody as hp  # noqa: E402
from evaluate import _corpus_vocab, eval_style_record  # noqa: E402
from generate import form_score  # noqa: E402

# ⛔ CSENDES HIBA, amit itt elfogunk: a kitalált-szó mérés kétlépcsős — szótár
# ÉS korpusz. Ha a korpusz nincs letöltve (a repóban nincs benne, a
# `fetch_corpus.py` hozza le a MEK-ről), a szókészlet ÜRES, és akkor minden
# szótáron kívüli alak „kitaláltnak” minősül. A szám hihetőnek látszana.
MIN_VOCAB = 50_000

FIELDS = [
    ("form_score", "form_score"),
    ("n_lines", "sor"),
    ("rhyme_rate", "rímarány"),
    ("rhyme_quality", "rímminőség"),
    ("rag_share", "ragrím-arány"),
    ("invented_rate", "kitalált szó"),
    ("oov_rate", "szótáron kívül"),
    ("distinct_2", "distinct-2"),
]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="",
                    help="JSON lista: [{label, text, arm, note}]")
    ap.add_argument("--from-demo", default="",
                    help="glob a demo_*.json futásokra — a GYŐZTES jelöltet veszi")
    ap.add_argument("--stanzas", type=int, default=1, help="a reranker spec-je")
    ap.add_argument("--stanza-size", type=int, default=4)
    ap.add_argument("--out", default="")
    ap.add_argument("--skip-vocab-check", action="store_true",
                    help="csak ha a kitalált-szó oszlopot NEM használod")
    return ap.parse_args()


def score_one(entry: dict, spec: dict) -> dict:
    text = entry["text"].strip()
    rec = {
        "condition": entry["label"],
        "sample": 0,
        "output": text,
        "item": {"spec": spec, "source_key": "demo", "poem_id": entry["label"]},
    }
    row = eval_style_record(rec)
    row["form_score"] = round(form_score(text, spec), 4)
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    row["syllables"] = [hp.count_syllables(ln) for ln in lines]
    row["rhyme_scheme"] = hp.rhyme_scheme(lines) if len(lines) >= 2 else ""
    row["rhyme_pairs"] = [
        {
            "a": lines[i].split()[-1] if lines[i].split() else "",
            "b": lines[i + 1].split()[-1] if lines[i + 1].split() else "",
            "score": round(hp.rhyme_score(lines[i], lines[i + 1]), 3),
            "inflectional": hp.inflectional_suffix(lines[i], lines[i + 1]),
        }
        for i in range(len(lines) - 1)
    ]
    row["arm"] = entry.get("arm", "")
    row["note"] = entry.get("note", "")
    row["text"] = text
    return row


def entries_from_demo(pattern: str) -> list[dict]:
    """A demó-futások győztesei ugyanabba a táblázatba, mint a külső versek.

    A győztest a lementett `winner_index` adja — NEM újraszámoljuk, hogy a
    táblázat azt a verset mérje, amit a reranker akkor valóban kiválasztott.
    """
    out = []
    for path in sorted(Path().glob(pattern)):
        data = json.loads(path.read_text(encoding="utf-8"))
        winner = data["candidates"][data["winner_index"]]
        arm = "LoRA" if data.get("adapter") else "nyers"
        if data.get("thinking"):
            arm += "+thinking"
        out.append({
            "label": f"{path.stem.replace('demo_', '')}",
            "text": winner["text"],
            "arm": f"{arm} · best-of-{data['best_of']} · seed {data['seed']}",
            "note": data.get("model", ""),
        })
    return out


def fmt(value) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def main() -> int:
    args = parse_args()
    spec = {"n_stanzas": args.stanzas, "stanza_size": args.stanza_size}

    if not args.skip_vocab_check:
        n_vocab = len(_corpus_vocab())
        if n_vocab < MIN_VOCAB:
            print(f"⛔ A korpusz-szókészlet {n_vocab} alak (< {MIN_VOCAB}) — a "
                  f"kitalált-szó mérés így FELÜLBECSÜLNE. Futtasd előbb:\n"
                  f"   python3 code/fetch_corpus.py && python3 code/build_corpus.py\n"
                  f"   (vagy --skip-vocab-check, ha a kitalált-szó oszlop nem kell)")
            return 2
        print(f"korpusz-szókészlet: {n_vocab} szóalak")
    entries: list[dict] = []
    if args.from_demo:
        entries += entries_from_demo(args.from_demo)
    if args.input:
        entries += json.loads(Path(args.input).read_text(encoding="utf-8"))
    if not entries:
        print("Nincs bemenet: adj meg --input és/vagy --from-demo értéket.")
        return 1
    rows = [score_one(e, spec) for e in entries]

    head = ["ág"] + [label for _, label in FIELDS]
    print("| " + " | ".join(head) + " |")
    print("|" + "|".join(["---"] * len(head)) + "|")
    for row in rows:
        cells = [row["condition"]] + [fmt(row.get(key)) for key, _ in FIELDS]
        print("| " + " | ".join(cells) + " |")

    print()
    for row in rows:
        print(f"--- {row['condition']} ({row['arm']}) · szótag={row['syllables']} "
              f"· séma={row['rhyme_scheme']}")
        for pair in row["rhyme_pairs"]:
            tag = f" RAGRÍM(-{pair['inflectional']})" if pair["inflectional"] else ""
            hit = "✓" if pair["score"] >= 0.6 else "·"
            print(f"    {hit} {pair['a']} / {pair['b']}  {pair['score']:.3f}{tag}")

    if args.out:
        Path(args.out).write_text(
            json.dumps({"spec": spec, "rows": rows}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"\n→ {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
