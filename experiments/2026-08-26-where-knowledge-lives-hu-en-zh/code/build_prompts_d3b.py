#!/usr/bin/env python3
"""D3b újramérés — items.jsonl → prompts_d3b.jsonl (16 angol közelítőszó-prompt).

⛔⛔ MIÉRT: a 2026-08-25-i bírálat kimutatta, hogy az `analyze_d.py` D3b-je az
`iid-ctrl` SAE-fájlokat hasonlítja (kaláka → *help*), nem az `en_approx` mezőt
(kaláka → *mutual aid*). A dolgozat 7. fejezete tehát mást mért, mint amit állított.
Ez a szkript az `en_approx` közelítőszavakhoz gyárt promptot, a kontrollszó-prompt
sablonjával (build_prompts.CTRL_Q["en"]), hogy a keret bitre azonos legyen.

Rögzített szabály a közelítőszó kiválasztására (a d3b-protokoll.md-ben előre leírva):
  * az `en_approx` ELSŐ, `/` előtti alternatívája;
  * zárójeles rész és belső idézőjel elhagyva;
  * egyszavas → "the word '…'", többszavas → "the expression '…'".

Futtatás (spark-dev, KÜLÖN eredmény-könyvtárba, hogy a fő kört ne szennyezze):
    SCOPE_RES=results_d3b SCOPE_PROMPTS=prompts_d3b.jsonl bash src/run_spark.sh src/run.py
    SCOPE_RES=results_d3b bash src/run_spark.sh src/run_sae.py
"""
import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent.parent
ITEMS = HERE / "items.jsonl"
OUT = HERE / "prompts_d3b.jsonl"
TEMPLATE = "Question: {q}\nAnswer:"
Q_WORD = "What does the word '{w}' mean?"
Q_EXPR = "What does the expression '{w}' mean?"
MAX_NEW = 200          # a generált szöveg a D3b-ben nem kell, csak a residual


def approx_phrase(en_approx):
    first = en_approx.split("/")[0]
    first = re.sub(r"\([^)]*\)", "", first)
    first = first.replace("'", "").replace("’", "")
    return re.sub(r"\s+", " ", first).strip()


def main():
    rows = []
    for line in ITEMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        it = json.loads(line)
        if it["group"] != "UNT":
            continue
        w = approx_phrase(it["en_approx"])
        q = (Q_WORD if " " not in w else Q_EXPR).format(w=w)
        rows.append({
            "item_id": it["id"] + "-approx", "group": "UNT", "kind": "approx", "lang": "en",
            "prompt": TEMPLATE.format(q=q), "expected": "", "max_new_tokens": MAX_NEW,
            "meta": {"concept": it["concept"], "src_lang": it["src_lang"],
                     "en_approx": it["en_approx"], "approx_phrase": w,
                     "control": it["control"]},
        })
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{OUT} — {len(rows)} prompt")
    for r in rows:
        print(f"  {r['item_id']:18s} {r['meta']['concept']:22s} → {r['prompt'].splitlines()[0]}")


if __name__ == "__main__":
    main()
