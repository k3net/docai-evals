"""03-as kör — MultiEURLEX, NerKor, Belebele és SIB-200 a közös sémára (03-runbook 3.1, F0).

  MultiEURLEX (jogi.multieurlex)   choice: melyik EuroVoc-területhez tartozik a jogi aktus (21 terület, 1. szint; a
                                   magyar nevek a Kiadóhivatal RDF-jéből: forras/eurovoc/eurovoc_level1.json). Egy
                                   dokumentum több területhez is tartozhat: a listán pontosan egy van a sajátjai közül,
                                   a többi opció nem az övé. 15% gold-drop X: egyik opció sem a dokumentum területe. A
                                   címkézés nem kimerítő, ezért a „nem az övé” zajos lehet (gépi zajbecslés, 4.2). Az
                                   állapot a szöveg első 1500 karaktere (cím, keltezés, preambulum eleje).
  NerKor (entitas.nerkor)          choice: milyen típusú név a kiemelt kifejezés (személy, hely, szervezet, egyéb név),
                                   mondatonként legfeljebb két név. 12% X (hatókörön kívüli): a kiemelt kifejezés
                                   köznév, nem név.
  Belebele hun_Latn (qa.belebele)  csak külső eval (FLORES-szöveg, 3.1): négyopciós olvasásértés.
  SIB-200 hun_Latn (level.sib200)  csak külső eval (FLORES-szöveg): a mondat témája, hét kategória.

Splitek: MultiEURLEX és NerKor: a forrás train → train, a forrás validation/devel → val, a forrás test → teszt-ID.
A Belebele és a SIB-200 minden itemje `eval-kulso`.

  kor01/.venv/bin/python kor03/eszkozok/adapter_egyeb.py   # → kor03/adat/f0/*.jsonl + adapter_egyeb_riport.json
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import MAX_OPTIONS, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "forras"
OUT = ROOT / "adat/f0"
SEED = 20261009


def h100(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % 100


def shuffled_options(texts: list[tuple[str, str]], gold_id: str | None, rnd: random.Random) -> tuple[list[dict], str | None]:
    texts = list(texts)
    rnd.shuffle(texts)
    return [{"id": i, "text": t} for i, t in texts], gold_id


def base(family: str, group: str, source: str, lic: str, ref: str, split: str, gid: str) -> dict:
    return {"id": f"{family}:{ref}", "family": family, "group": group, "source": source, "source_license": lic,
            "source_ref": ref, "split": split, "group_id": gid, "lang": "hu", "ketertelmu": False, "soft": None,
            "x_type": None, "meta": {}}


# --- MultiEURLEX -----------------------------------------------------------------------------------------------------

def eurovoc_names() -> list[tuple[str, str]]:
    """(concept-id, magyar név) a parquet ClassLabel-sorrendjében."""
    ev = json.loads((SRC / "eurovoc/eurovoc_level1.json").read_text(encoding="utf-8"))
    md = json.loads(pq.read_schema(SRC / "hf/coastalcph/multi_eurlex/hu/train/0000.parquet").metadata[b"huggingface"])
    names = md["info"]["features"]["labels"]["feature"]["names"]
    out = []
    for cid in names:
        hu = re.sub(r"^\d+\s+", "", ev[cid]["hu"]).capitalize()
        out.append((cid, hu.replace("Európai unió", "Európai Unió")))
    return out


MEL_X = 15  # %


def multieurlex() -> tuple[list[dict], Counter]:
    labels = eurovoc_names()
    rows, why = [], Counter()
    for src_split, split in (("train", "train"), ("validation", "val"), ("test", "test-id")):
        for r in pq.read_table(SRC / f"hf/coastalcph/multi_eurlex/hu/{src_split}/0000.parquet").to_pylist():
            own = sorted(set(r["labels"]))
            if not own:
                why["kimarad: címke nélkül"] += 1
                continue
            ref = f"{src_split}:{r['celex_id']}"
            rnd = random.Random(f"{SEED}:mel:{ref}")
            others = [i for i in range(len(labels)) if i not in own]
            xdrop = h100(f"mel-x:{ref}") < MEL_X
            k = rnd.randint(2, min(MAX_OPTIONS, len(others))) if xdrop else rnd.randint(1, min(MAX_OPTIONS - 1, len(others)))
            dis = rnd.sample(others, k)
            gold = None if xdrop else rnd.choice(own)
            ids = dis + ([gold] if gold is not None else [])
            opts, _ = shuffled_options([(labels[i][0], labels[i][1]) for i in ids], None, rnd)
            text = re.sub(r"[ \t]+", " ", r["text"]).strip()
            it = base("jogi.multieurlex", "jogi", "MultiEURLEX", "CC-BY-SA-4.0", ref, split, f"jogi.multieurlex:{r['celex_id']}")
            rows.append({**it, "kind": "choice", "state": text[:1500] + (" […]" if len(text) > 1500 else ""),
                         "question": "Melyik EuroVoc-területhez tartozik ez a jogi aktus?", "options": opts,
                         "gold": labels[gold][0] if gold is not None else None, "x_type": "gold-drop" if xdrop else None,
                         "meta": {"celex": r["celex_id"], "sajat_teruletek": [labels[i][0] for i in own]}})
            why["choice X" if xdrop else "choice"] += 1
    return rows, why


# --- NerKor ----------------------------------------------------------------------------------------------------------

NER = [("PER", "személy"), ("LOC", "hely"), ("ORG", "szervezet"), ("MISC", "egyéb név")]
NER_X = 12  # %
NO_SPACE_BEFORE = re.compile(r" ([.,;:!?)\]”»%])")
NO_SPACE_AFTER = re.compile(r"([(\[„«]) ")


def detok(tokens: list[str]) -> str:
    s = " ".join(tokens)
    return NO_SPACE_AFTER.sub(r"\1", NO_SPACE_BEFORE.sub(r"\1", s))


def conllup_sentences(path: Path):
    toks = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            if toks:
                yield toks
            toks = []
            continue
        cols = line.split("\t")
        if len(cols) < 6:  # megjegyzéssor (# global.columns …)
            continue
        toks.append({"form": cols[0], "upos": cols[2], "ner": cols[5]})
    if toks:
        yield toks


def entities(toks: list[dict]) -> list[tuple[int, int, str]]:
    out, i = [], 0
    while i < len(toks):
        tag = toks[i]["ner"]
        if tag.startswith("B-"):
            t, j = tag[2:], i + 1
            while j < len(toks) and toks[j]["ner"] == f"I-{t}":
                j += 1
            out.append((i, j, t))
            i = j
        else:
            i += 1
    return out


def nerkor() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    for src_split, split in (("train", "train"), ("devel", "val"), ("test", "test-id")):
        for f in sorted((SRC / "gh/nytud/NYTK-NerKor/data" / src_split).rglob("*.conllup")):
            genre = f.parent.name
            for si, toks in enumerate(conllup_sentences(f)):
                ents = [e for e in entities(toks) if e[2] in dict(NER)]
                if not ents or len(toks) > 80:
                    why["kimarad: név nélkül vagy túl hosszú"] += 1
                    continue
                sref = f"{src_split}:{genre}/{f.stem}:{si}"
                rnd = random.Random(f"{SEED}:ner:{sref}")
                text = detok([t["form"] for t in toks])
                picks: list[tuple[str, str | None, str]] = []  # (kifejezés, gold, x_type)
                for i, j, t in rnd.sample(ents, min(2, len(ents))):
                    picks.append((detok([x["form"] for x in toks[i:j]]), t, ""))
                if h100(f"ner-x:{sref}") < NER_X:
                    nouns = [t["form"] for t in toks if t["upos"] == "NOUN" and t["ner"] == "O" and len(t["form"]) >= 4
                             and t["form"].isalpha()]
                    if nouns:
                        picks.append((rnd.choice(nouns), None, "out-of-scope"))
                for k, (span, gold, xt) in enumerate(picks):
                    if text.count(span) == 0:
                        why["kimarad: a kifejezés nincs a mondatban"] += 1
                        continue
                    it = base("entitas.nerkor", "entitas", "NerKor", "CC-BY-SA-4.0", f"{sref}:{k}", split,
                              f"entitas.nerkor:{sref}")
                    opts, _ = shuffled_options(NER, None, rnd)
                    rows.append({**it, "kind": "choice", "state": text,
                                 "question": f"Milyen típusú név a mondatban a(z) „{span}” kifejezés?", "options": opts,
                                 "gold": gold, "x_type": xt or None, "meta": {"mufaj": genre}})
                    why["choice X" if gold is None else "choice"] += 1
    return rows, why


# --- külső eval: Belebele, SIB-200 ------------------------------------------------------------------------------------

def belebele() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    for line in (SRC / "hf/facebook/belebele/data/hun_Latn.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        ref = f"{hashlib.sha256(r['link'].encode()).hexdigest()[:12]}:{r['question_number']}"
        it = base("qa.belebele", "qa", "Belebele", "CC-BY-SA-4.0", ref, "eval-kulso", f"qa.belebele:{r['link']}")
        opts = [{"id": str(i), "text": r[f"mc_answer{i}"]} for i in range(1, 5)]
        rows.append({**it, "kind": "choice", "state": r["flores_passage"], "question": r["question"], "options": opts,
                     "gold": str(r["correct_answer_num"])})
        why["choice"] += 1
    return rows, why


SIB = {"science/technology": "tudomány és technológia", "travel": "utazás", "politics": "politika", "sports": "sport",
       "health": "egészség", "entertainment": "szórakozás", "geography": "földrajz"}


def sib200() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    for sp in ("train", "dev", "test"):
        with open(SRC / f"hf/Davlan/sib200/data/hun_Latn/{sp}.tsv", encoding="utf-8") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                ref = f"{sp}:{r['index_id']}"
                it = base("level.sib200", "level", "SIB-200", "CC-BY-SA-4.0", ref, "eval-kulso", f"level.sib200:{ref}")
                opts = [{"id": k.replace("/", "-"), "text": v} for k, v in SIB.items()]
                rows.append({**it, "kind": "choice", "state": r["text"], "question": "Mi a mondat témája?",
                             "options": opts, "gold": r["category"].replace("/", "-")})
                why["choice"] += 1
    return rows, why


def report(rows: list[dict], why: Counter) -> dict:
    return {"n": len(rows), "ok": dict(why), "split": dict(Counter(r["split"] for r in rows)),
            "x_arany": sum(r["gold"] is None for r in rows) / max(1, len(rows)),
            "opcioszam": dict(sorted(Counter(len(r["options"]) for r in rows).items())),
            "gold": dict(Counter(str(r["gold"]) for r in rows).most_common(8))}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rep = {}
    for family, fn in (("jogi.multieurlex", multieurlex), ("entitas.nerkor", nerkor), ("qa.belebele", belebele),
                       ("level.sib200", sib200)):
        rows, why = fn()
        bad = [(r["id"], e) for r in rows if (e := validate(r))]
        if bad:
            raise SystemExit(f"{family}: {len(bad)} sémahiba, pl. {bad[:3]}")
        ids = Counter(r["id"] for r in rows)
        if ids.most_common(1)[0][1] > 1:
            raise SystemExit(f"{family}: ismétlődő id: {ids.most_common(1)}")
        (OUT / f"{family}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                                             encoding="utf-8")
        rep[family] = report(rows, why)
        print(family, json.dumps(rep[family], ensure_ascii=False))
    (OUT / "adapter_egyeb_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
