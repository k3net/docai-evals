"""F1.5 — a rögzített értékelő szett. Minden feltétel EZT kapja.

Az F4-ben négy feltételt mérünk (B0 nyers / B1 few-shot / B2 few-shot+reranker
/ C LoRA). Ha a promptok feltételenként eltérnének, az összevetés semmit nem
érne — ezért a szett itt készül el egyszer, fájlba mentve, verziózva.

Három kimenet:

  * `eval_prompts.json` — a generálási feladat. A holdout versek CÍMÉBŐL és
    mért formai jellemzőiből épül, tehát a modell olyan verset ír, amit soha
    nem látott, de aminek a formai elvárása gépileg ellenőrizhető.
  * `extraction_probes.json` — a memorizáció-mérés. 50 TRAIN + 50 HOLDOUT vers
    első két sora. A holdout ág a kontroll: ami ott is előjön, az a
    pretrainingből jön, nem a mi tanításunkból. A kettő különbsége az
    `extraction_gap` — ez a LoRA tényleges hozzájárulása.
  * `fewshot.json` — a B1/B2 baseline példái, kizárólag a TRAIN szeletből.
    Holdout-példa itt szivárgás lenne.

    python3 src/build_evalset.py
"""

from __future__ import annotations

import json
import random
import sys

from build_dataset import form_spec, split_key, make_split, load_corpus, SEED
from config import DATASET, REPORTS, SOURCES

N_PROMPTS_PER_AUTHOR = 50
N_PROBES_PER_SPLIT = 50
N_FEWSHOT = 4
PROBE_LEAD_LINES = 2  # ennyi sort adunk be, a többit a modellnek kell hoznia


def main() -> int:
    corpus = load_corpus()
    out_dir = DATASET / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)

    prompts: list[dict] = []
    probes: list[dict] = []
    fewshot: dict[str, list[dict]] = {}
    report = ["# F1.5 — Rögzített értékelő szett\n",
              "| szerző | generálási prompt | extraction próba (train/holdout) | few-shot példa |",
              "|---|---:|---:|---:|"]

    for key, poems in corpus.items():
        author = SOURCES[key]["author"]
        rng = random.Random(SEED + 1)
        assign = make_split(poems, random.Random(SEED))  # UGYANAZ a split, mint az F1-ben

        holdout = [p for p in poems if assign[split_key(p)] == "test"]
        train = [p for p in poems if assign[split_key(p)] == "train"]

        # --- generálási promptok: a NEM TANÍTOTT szeletek (test + val) címeiből.
        # Csak a testből Aranynál 24 alkalmas vers jönne (a holdout nagy részét
        # a hosszú elbeszélő művek viszik), ami kevés a stabil összevetéshez.
        # A val ugyanúgy tanítás-mentes; annyi a különbség, hogy a
        # checkpoint-választás rá optimalizál — a rekord `origin_split` mezője
        # miatt ez utólag szűrhető, ha számítana.
        val = [p for p in poems if assign[split_key(p)] == "val"]
        eligible = [p for p in holdout + val if 6 <= p["n_lines"] <= 80 and p["n_stanzas"] >= 2]
        picked = rng.sample(eligible, min(N_PROMPTS_PER_AUTHOR, len(eligible)))
        origin = {p["poem_id"]: ("test" if assign[split_key(p)] == "test" else "val") for p in eligible}
        for poem in picked:
            spec_text, spec = form_spec(poem)
            prompts.append(
                {
                    "id": f"{key}/{len(prompts):03d}",
                    "source_key": key,
                    "author": author,
                    "poem_id": poem["poem_id"],
                    "origin_split": origin[poem["poem_id"]],
                    "title": poem["title"],
                    "prompt": (
                        f"Írj verset {author} modorában.\n"
                        f"Cím: {poem['title']}\n"
                        f"Forma: {spec_text}."
                    ),
                    "spec": spec,
                    "reference_lines": poem["n_lines"],
                }
            )

        # --- extraction próbák: train ÉS holdout, azonos módon
        for split_name, pool in (("train", train), ("holdout", holdout)):
            usable = [p for p in pool if p["n_lines"] >= 8]
            for poem in rng.sample(usable, min(N_PROBES_PER_SPLIT, len(usable))):
                flat = [ln for st in poem["stanzas"] for ln in st]
                probes.append(
                    {
                        "id": f"{key}/{split_name}/{poem['poem_id']}",
                        "source_key": key,
                        "author": author,
                        "split": split_name,
                        "poem_id": poem["poem_id"],
                        "lead": "\n".join(flat[:PROBE_LEAD_LINES]),
                        "continuation": "\n".join(flat[PROBE_LEAD_LINES:PROBE_LEAD_LINES + 20]),
                    }
                )

        # --- few-shot példák: rövid, szabályos formájú TRAIN versek
        fs_pool = [
            p for p in train
            if 8 <= p["n_lines"] <= 24
            and p["prosody"].get("dominant_scheme_share", 0) >= 0.8
            and p["prosody"].get("isometric_share", 0) >= 0.7
        ]
        fs = rng.sample(fs_pool, min(N_FEWSHOT, len(fs_pool)))
        fewshot[key] = [
            {
                "poem_id": p["poem_id"],
                "title": p["title"],
                "spec_text": form_spec(p)[0],
                "text": "\n\n".join("\n".join(st) for st in p["stanzas"]),
            }
            for p in fs
        ]

        n_probe_tr = sum(1 for x in probes if x["source_key"] == key and x["split"] == "train")
        n_probe_ho = sum(1 for x in probes if x["source_key"] == key and x["split"] == "holdout")
        report.append(f"| {author} | {len(picked)} | {n_probe_tr} / {n_probe_ho} | {len(fewshot[key])} |")
        print(f"[{key}] {len(picked)} generálási prompt · {n_probe_tr}+{n_probe_ho} extraction próba · "
              f"{len(fewshot[key])} few-shot példa (választható: {len(eligible)} holdout vers)")

    (out_dir / "eval_prompts.json").write_text(
        json.dumps(prompts, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (out_dir / "extraction_probes.json").write_text(
        json.dumps(probes, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (out_dir / "fewshot.json").write_text(
        json.dumps(fewshot, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    report.append(
        "\nA generálási promptok a **holdout** versek címéből és mért formai "
        "jellemzőiből épülnek — a modell soha nem látott verset ír, de az elvárás "
        "gépileg ellenőrizhető. A few-shot példák kizárólag a **train** szeletből "
        "jönnek: holdout-példa a B1 baseline-ban szivárgás lenne.\n"
    )
    (REPORTS / "05_evalset.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"\nSzett: {out_dir} · riport: {REPORTS / '05_evalset.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
