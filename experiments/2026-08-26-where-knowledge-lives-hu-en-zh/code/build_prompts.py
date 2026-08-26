#!/usr/bin/env python3
"""items.jsonl -> prompts.jsonl (258 sor) — a futtatás egyetlen inputja.

Négy prompt-fajta:
  fact  54 item x 3 nyelv = 162   ZH/HU/UNI faktuális kérdés, rövid válasz (200 token)
  unt   16 item x 3 nyelv =  48   lefordíthatatlan fogalom definíciója (500 token)
  ctrl  16 item x 3 nyelv =  48   a fogalomhoz rendelt kontrollszó definíciója (500 token)
                          = 258

A base modellnek NINCS chat template-je: nyers completion-sablont adunk neki,
nyelvenként a saját írásjeleivel (a kínainál teljes szélességű kettőspont — ha
ASCII kettőspontot adnánk, az önmagában nyelvi jel lenne a promptban).
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
ITEMS = HERE / "items.jsonl"
OUT = HERE / "prompts.jsonl"

LANGS = ("hu", "en", "zh")

# {q} helyére a kérdés kerül; a válasz-előtag után a modell folytat
TEMPLATE = {
    "hu": "Kérdés: {q}\nVálasz:",
    "en": "Question: {q}\nAnswer:",
    "zh": "问题：{q}\n回答：",
}

# A kontrollszó kérdése — ugyanaz a forma minden nyelven, a saját nyelvi
# idézőjeleivel. A szó nyelvenként a maga fordítása (control.{hu,en,zh}).
CTRL_Q = {
    "hu": "Mit jelent a „{w}” szó?",
    "en": "What does the word '{w}' mean?",
    "zh": "“{w}”一词是什么意思？",
}

# ⛔ MÉRVE KÉTSZER (reports/00_smoke_think.json, majd a teljes futás results/gen.jsonl-je),
# nem a runbook eredeti 40/120-a:
#   * 40 token kevés — a modell teljes mondattal válaszol;
#   * 60/300 mellett a teljes futás 91/258 válasza a KERETBE ütközött, és a csonkolás
#     NYELVFÜGGŐ volt: faktuálisnál hu 54 % · zh 30 % · en 24 % (a magyar tokenéhesebb),
#     az UNT/kontroll 300-as keretén pedig a zh 44 %. Csonkolt válaszra a bíráló
#     „hiányos/rossz" ítéletet ad → a „magyarul rosszabb" eredmény a token-keret
#     műterméke lenne, nem a reprezentációé.
#   * Ezért bőkezű keret. A generálás greedy, tehát a keret NÖVELÉSE a magától megállt
#     válaszokon semmit nem változtat (azonos determinisztikus prefix) — csak a csonkoltak
#     folytatódnak. Ezért elég azokat újrafuttatni (`run.py --only-truncated`), ez nem
#     szemezgetés: a protokoll végig „generálj a stop-jelig vagy a keretig".
#   * Harmadik kör: a 200/500 mellett maradt 48 csonkolt válasz KÉT jelenség — 23 ismétlési
#     HUROK (greedy degeneráció, hu 13 · zh 8 · en 2; ezen a keret nem segít) és 29 valódi
#     keret-ütközés. Az UNT/kontroll valódi ütközései (7 db) 800-as kerettel újrafutottak;
#     a hurokba esetteket szándékosan nem futtattuk újra (`--skip-degenerate`).
MAX_NEW = {"fact": 200, "unt": 800, "ctrl": 800}


def rows():
    for line in ITEMS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        it = json.loads(line)
        group = it["group"]
        for lang in LANGS:
            if group == "UNT":
                yield {
                    "item_id": it["id"],
                    "group": "UNT",
                    "kind": "unt",
                    "lang": lang,
                    "prompt": TEMPLATE[lang].format(q=it["q"][lang]),
                    "expected": "",
                    "max_new_tokens": MAX_NEW["unt"],
                    "meta": {
                        "concept": it["concept"],
                        "src_lang": it["src_lang"],
                        "native": it["native"],
                        "distortion": it["distortion"],
                        "en_approx": it["en_approx"],
                        "control": it["control"],
                    },
                }
                yield {
                    "item_id": it["id"] + "-ctrl",
                    "group": "UNT",
                    "kind": "ctrl",
                    "lang": lang,
                    "prompt": TEMPLATE[lang].format(q=CTRL_Q[lang].format(w=it["control"][lang])),
                    "expected": "",
                    "max_new_tokens": MAX_NEW["ctrl"],
                    "meta": {
                        "concept": it["concept"],
                        "src_lang": it["src_lang"],
                        "control_word": it["control"][lang],
                        "control": it["control"],
                    },
                }
            else:
                yield {
                    "item_id": it["id"],
                    "group": group,
                    "kind": "fact",
                    "lang": lang,
                    "prompt": TEMPLATE[lang].format(q=it["q"][lang]),
                    "expected": it["answer"][lang],
                    "max_new_tokens": MAX_NEW["fact"],
                    "meta": {"title": it["title"], "qid": it["qid"], "source": it["source"]},
                }


def main():
    out = list(rows())
    seen = set()
    for r in out:
        key = (r["item_id"], r["lang"])
        assert key not in seen, f"duplikált prompt-kulcs: {key}"
        seen.add(key)
        assert r["prompt"].strip(), f"üres prompt: {key}"
    with OUT.open("w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    from collections import Counter
    c = Counter((r["group"], r["kind"]) for r in out)
    print(f"{OUT} — {len(out)} prompt")
    for k in sorted(c):
        print(f"   {k[0]:4s} {k[1]:5s} {c[k]:4d}")


if __name__ == "__main__":
    main()
