#!/usr/bin/env python3
"""D3b kiegészítés — a közelítő kifejezés HARMADIK nyelvű változata (d3b-protokoll.md, kiegészítés).

hu-forrású fogalomhoz kínai, zh-forrásúhoz magyar fordítás; a fordítás a szerzőé, itt rögzítve.
    SCOPE_RES=results_d3b_x SCOPE_PROMPTS=prompts_d3b_x.jsonl bash src/run_spark.sh src/run.py
    SCOPE_RES=results_d3b_x bash src/run_spark.sh src/run_sae.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "prompts_d3b_x.jsonl"
TEMPLATE = {"hu": "Kérdés: {q}\nVálasz:", "zh": "问题：{q}\n回答："}
# ⛔ magánhangzó előtt „az” — a kontrollszó-sablon „a” névelője itt hibás lenne (az „arc”)
Q = {"hu": ("Mit jelent {a} „{w}” szó?", "Mit jelent {a} „{w}” kifejezés?"),
     "zh": ("“{w}”一词是什么意思？", "“{w}”这个说法是什么意思？")}
# fogalom → (harmadik nyelv, a közelítő kifejezés fordítása)
THIRD = {
    "UNT-HU01": ("zh", "互助"),            # mutual aid
    "UNT-HU02": ("zh", "爱"),              # love
    "UNT-HU03": ("zh", "敬称与非敬称"),      # formal vs informal you
    "UNT-HU04": ("zh", "亲吻"),            # kiss
    "UNT-HU05": ("zh", "征服"),            # conquest
    "UNT-HU06": ("zh", "姐夫"),            # brother-in-law
    "UNT-HU07": ("zh", "命名日"),          # name day
    "UNT-HU08": ("zh", "有空"),            # to have time
    "UNT-ZH01": ("hu", "kapcsolatok"),     # connections
    "UNT-ZH02": ("hu", "arc"),             # face
    "UNT-ZH03": ("hu", "sors"),            # fate
    "UNT-ZH04": ("hu", "élénk"),           # lively
    "UNT-ZH05": ("hu", "alvilág"),         # underworld
    "UNT-ZH06": ("hu", "aranyoskodni"),    # to act cute
    "UNT-ZH07": ("hu", "belső hőség"),     # to have internal heat
    "UNT-ZH08": ("hu", "hajrá"),           # go for it
}


def main():
    items = {json.loads(l)["id"]: json.loads(l) for l in (HERE / "items.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    rows = []
    for iid, (lang, w) in THIRD.items():
        it = items[iid]
        assert it["src_lang"] != lang
        multi = " " in w or (lang == "zh" and len(w) > 4)
        art = "az" if w[0].lower() in "aáeéiíoóöőuúüű" else "a"
        q = Q[lang][1 if multi else 0].format(w=w, a=art)
        rows.append({"item_id": iid + "-approx", "group": "UNT", "kind": "approx_third", "lang": lang,
                     "prompt": TEMPLATE[lang].format(q=q), "expected": "", "max_new_tokens": 200,
                     "meta": {"concept": it["concept"], "src_lang": it["src_lang"], "en_approx": it["en_approx"],
                              "third_phrase": w}})
    with OUT.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{OUT} — {len(rows)} prompt")
    for r in rows:
        print(f"  {r['item_id']:18s} [{r['lang']}] {r['prompt'].splitlines()[0]}")


if __name__ == "__main__":
    main()
