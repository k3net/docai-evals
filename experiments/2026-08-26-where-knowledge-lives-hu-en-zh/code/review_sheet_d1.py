#!/usr/bin/env python3
"""Kézi ellenőrző ív a D1 kötelező köréhez (48 UNT-válasz).

    python3 src/review_sheet_d1.py

A runbook §4b szerint mind a 48 UNT-választ kézzel is pontozni kell — ez a csoport kicsi
és fontos. Az ív komponensenként hozza a bíráló döntését; csak az ELTÉRÉST kell beírni a
`results/d1_scores.csv` `manual_native` / `manual_distortion` oszlopába (számként, 0..n).

⚠️ Két dolgot érdemes külön nézni, mert a bíráló ezekben hibázott:
  * a kínai válaszok végén lévő ÖNÉRTÉKELŐ toldalék (levágva, de a bírálat egy körben
    már rossz volt tőle — ld. 撒娇/zh);
  * a hurokba esett válaszok (kevesebb komponens fér el bennük).
"""
import argparse
import csv
import json
import pathlib
import scope_paths


HERE = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(HERE)
LANG_NAME = {"hu": "magyar", "en": "angol", "zh": "kínai"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--remaining", action="store_true",
                    help="csak a még ellenőrző ítélet nélküli UNT-sorok")
    args = ap.parse_args()
    judge = [json.loads(l) for l in (RES / "d1_judge.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    items = {json.loads(l)["id"]: json.loads(l) for l in
             (HERE / "items.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    gen = {(r["item_id"], r["lang"]): r for r in
           (json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}

    unt = [r for r in judge if r["kind"] == "unt"]
    if args.remaining:
        # ⛔ A `-ctrl` sorok a `manual_ctrl` oszlopot használják, nem a `manual_native`-ot —
        # a szűrés csak az UNT-sorokra megy, azokra viszont a native oszlop a jelző.
        done = {(r["item_id"], r["lang"]) for r in
                csv.DictReader((RES / "d1_scores.csv").open(encoding="utf-8"))
                if (r.get("manual_native") or "").strip()}
        unt = [r for r in unt if (r["item_id"], r["lang"]) not in done]
    unt.sort(key=lambda r: (r["src_lang"], r["item_id"], ["hu", "en", "zh"].index(r["lang"])))
    md = [("# Kézi ellenőrző ív — D1, A HÁTRALÉVŐ SOROK" if args.remaining
           else "# Kézi ellenőrző ív — D1 (48 UNT-válasz)"), "",
          "Komponensenként látod a bíráló döntését. Ahol egyetértesz, nincs teendő; ahol nem, add meg a",
          "`src/set_manual.py`-nak a HELYES darabszámot:",
          "`python3 src/set_manual.py d <item> <nyelv> --native N --distortion M`,",
          "majd `python3 src/analyze_d.py`.", "",
          "⛔ A `d1_scores.csv`-t **ne szerkeszd kézzel** — a 08-24-i körben így csúszott el az",
          "UNT-ZH08 `native_n` nevezője. A felvitel a `set_manual.py`-n megy; a parancsok alább,",
          "a bíráló darabszámaival előkitöltve.", "", "```bash"]
    for r in unt:
        md.append(f"python3 src/set_manual.py d {r['item_id']:9s} {r['lang']} "
                  f"--native {sum(r['native'])} --distortion {sum(r['distortion'])}")
    md += ["```", ""]
    last = None
    for r in unt:
        if r["item_id"] != last:
            last = r["item_id"]
            it = items[r["item_id"]]
            md += ["", f"## {it['concept']} (forrásnyelv: {it['src_lang']}) — angol közelítés: *{it['en_approx']}*", ""]
        g = gen[(r["item_id"], r["lang"])]
        flags = []
        if g["truncated"]:
            flags.append("csonkolt")
        if g["degenerate"]:
            flags.append("ismétlési hurok")
        if g.get("self_eval_cut") is True:
            flags.append("önértékelő toldalék levágva")
        elif g.get("self_eval_cut") == "suspect":
            flags.append("⛔ önértékelő marker a szöveg ELEJÉN — nem vágtunk, nézd meg")
        it = items[r["item_id"]]
        md += [f"### {LANG_NAME[r['lang']]}" + (f"  ⚠️ {', '.join(flags)}" if flags else ""), ""]
        for k, c in enumerate(it["native"]):
            md.append(f"- [{'x' if r['native'][k] else ' '}] **native {k+1}:** {c}")
        for k, c in enumerate(it["distortion"]):
            md.append(f"- [{'x' if r['distortion'][k] else ' '}] *distortion {k+1}:* {c}")
        md += ["", f"> {g.get('text_clean', g['text'])[:800]}", "",
               f"*Bíráló indoklása:* {r['indoklas']}", ""]

    # ⛔ scope_paths.reports(), NEM a fix `reports/` — különben az instruct kör íve a base
    # kör könyvtárába kerülne, és a két kör ívei felülírnák egymást.
    out = scope_paths.reports(HERE) / ("05_kezi_ellenorzes_d1_hatra.md" if args.remaining
                                       else "05_kezi_ellenorzes_d1.md")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"→ {out} ({len(unt)} válasz)")


if __name__ == "__main__":
    main()
