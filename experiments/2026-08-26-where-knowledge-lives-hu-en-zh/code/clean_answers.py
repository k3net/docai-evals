#!/usr/bin/env python3
"""A generált válaszok tisztítása az ÖNÉRTÉKELŐ toldaléktól.

    python3 src/clean_answers.py

⛔⛔ MÉRT PROBLÉMA: a base modell a válasz után gyakran SAJÁT feladat-promptot ír
(*„请判断回答是否正确…正确"*, *„A single-select problem: Is the question answered…"*),
és ez a bírálót félrevezeti — egy mért esetben (撒娇/zh) a bíráló a toldalékra ítélt
(„a válasz csak a »helyes« szót tartalmazza"), és 0 komponenst adott egy olyan válaszra,
ami az első komponenst egyértelműen tartalmazza.

A jelenség NYELVFÜGGŐ: kínaiul 17 %, angolul 3 %, magyarul 0 % — tehát pont azokat a
cellákat rontja, ahol a D1 meglepő eredménye született (a forrásnyelv a leggyengébb).
A `run.py` stop-szekvenciái csak a következő KÉRDÉST vágták le, ezt nem.

A vágás utólagos: a toldalék nem része a válasznak, generálni nem kell újra.
A `text` mező érintetlen marad, a bírálók a `text_clean`-t használják.
"""
import json
import pathlib
import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent
GEN = scope_paths.res(HERE) / "gen.jsonl"

MARKERS = ["请判断", "请分析", "请根据", "请回答", "请选择", "请评估", "以上回答", "请问以上",
           "A single-select problem", "Is the question answered", "正确答案是",
           "请你判断", "请给出", "请指出"]


# ⛔⛔ ŐR (2026-08-25, az instruct kör előtt): a marker a TOLDALÉK elejét jelöli, de néhány
# marker (`正确答案是`, `请回答`) egy INSTRUCT válasz ELEJÉN is állhat jogosan. Ha a vágás
# után gyakorlatilag semmi nem marad, akkor nem toldalékot vágtunk, hanem a VÁLASZT — és a
# bíráló egy üres szövegre néma „helytelen"-t mondana. Ilyenkor NEM vágunk, csak jelölünk.
MIN_KEEP = 15


def clean(text):
    idx = [text.find(m) for m in MARKERS]
    idx = [i for i in idx if i >= 0]
    if not idx:
        return text, False
    head = text[: min(idx)].strip()
    if len(head) < MIN_KEEP:
        return text, "suspect"
    return head, True


def main():
    rows = [json.loads(l) for l in GEN.read_text(encoding="utf-8").splitlines() if l.strip()]
    n_cut = 0
    lost = []
    for r in rows:
        c, cut = clean(r["text"])
        r["text_clean"], r["self_eval_cut"] = c, cut
        if cut is True:
            n_cut += 1
            lost.append((r["item_id"], r["lang"], len(r["text"]) - len(c)))
    GEN.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")

    from collections import Counter
    per_lang = Counter(r["lang"] for r in rows if r["self_eval_cut"] is True)
    per_kind = Counter(r["kind"] for r in rows if r["self_eval_cut"] is True)
    print(f"{n_cut}/{len(rows)} válaszból vágtunk önértékelő toldalékot")
    print("  nyelvenként:", dict(per_lang), "· fajtánként:", dict(per_kind))
    print("  a legtöbb levágott karakter:", sorted(lost, key=lambda t: -t[2])[:5])
    empty = [r["item_id"] + "/" + r["lang"] for r in rows
             if r["self_eval_cut"] is True and not r["text_clean"]]
    if empty:
        print(f"  ⚠️ {len(empty)} válasz a vágás után ÜRES lett: {empty}")
    suspect = [r["item_id"] + "/" + r["lang"] for r in rows if r["self_eval_cut"] == "suspect"]
    if suspect:
        print(f"  ⛔ {len(suspect)} válaszban a marker a szöveg ELEJÉN áll — NEM vágtunk, "
              f"mert a válasz veszett volna el: {suspect}")
        print("     nézd meg kézzel: lehet, hogy ott a marker a válasz része "
              "(pl. az instruct modell így vezeti fel a megoldást).")


if __name__ == "__main__":
    main()
