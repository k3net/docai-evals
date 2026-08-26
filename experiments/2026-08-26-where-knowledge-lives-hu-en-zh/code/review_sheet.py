#!/usr/bin/env python3
"""Kézi ellenőrző ív a Mérés A kötelező köréhez (ZH + HU csoport, 102 válasz).

    python3 src/review_sheet.py

A runbook §2 szerint a ZH és HU csoport MINDEN válaszát kézzel is értékelni kell — a bíráló
ugyanabból a modellcsaládból való, mint a vizsgált modell. Ez az ív úgy készül, hogy csak az
ELTÉRÉST kelljen bejelölni: ahol egyetértesz a bírálóval, nem kell semmit tenni.

Menete:
  1. olvasd végig a `reports/02_kezi_ellenorzes.md`-t
  2. ahol MÁS ítéletet adnál, írd be a `results/scores.csv` `manual` oszlopába
     (helyes / reszben / helytelen / hallucinacio)
  3. futtasd újra: `python3 src/analyze_a.py` — a `final` oszlop a kézit veszi elsőnek
"""
import argparse
import csv
import json
import pathlib
import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent
LANG_NAME = {"hu": "magyar", "en": "angol", "zh": "kínai"}


def strip_label(prompt):
    """A sablon nyitósorából a puszta kérdés. ⛔ A kínainál a kettőspont TELJES SZÉLESSÉGŰ
    (`问题：`), ezért az ASCII `": "` szerinti vágás ott bennhagyná a címkét."""
    first = prompt.split("\n")[0]
    for label in ("Kérdés: ", "Question: ", "问题："):
        if first.startswith(label):
            return first[len(label):]
    return first

def main():
    ap = argparse.ArgumentParser()
    # ⛔ A 08-24-i kör azért veszett el, mert a ellenőrző ítéletek KÉZZEL szerkesztett CSV-ben
    # jöttek vissza (törött idézőjelezés + kicserélt válaszszövegek). Azóta a felvitel
    # kizárólag a `set_manual.py`-n megy — ez az ív mostantól KI IS ÍRJA a parancsokat,
    # a bíráló ítéletével előkitöltve, hogy csak a vitatottakat kelljen átírni.
    ap.add_argument("--remaining", action="store_true",
                    help="csak a még ellenőrző ítélet nélküli sorok (a kör befejezéséhez)")
    args = ap.parse_args()
    scores = {(r["item_id"], r["lang"]): r for r in csv.DictReader((scope_paths.res(HERE) / "scores.csv").open(encoding="utf-8"))}
    gen = {(r["item_id"], r["lang"]): r for r in
           (json.loads(l) for l in (scope_paths.res(HERE) / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    prompts = {(p["item_id"], p["lang"]): p for p in
               (json.loads(l) for l in (HERE / "prompts.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    items = {json.loads(l)["id"]: json.loads(l) for l in
             (HERE / "items.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

    rows = [r for r in scores.values() if r["group"] in ("ZH", "HU")]
    if args.remaining:
        rows = [r for r in rows if not (r.get("manual") or "").strip()]
    rows.sort(key=lambda r: (r["group"], r["item_id"], ["hu", "en", "zh"].index(r["lang"])))

    title = ("# Kézi ellenőrző ív — Mérés A, A HÁTRALÉVŐ SOROK" if args.remaining
             else "# Kézi ellenőrző ív — Mérés A (ZH + HU csoport)")
    md = [title, "",
          f"**{len(rows)} válasz.** Ahol egyetértesz a bíráló ítéletével, nincs teendő. Ahol nem, add meg a",
          "`src/set_manual.py`-nak: `python3 src/set_manual.py a <item> <nyelv> <ítélet>`",
          "(`helyes` / `reszben` / `helytelen` / `hallucinacio`), majd `python3 src/analyze_a.py`.", "",
          "⚠️ Két dolgot érdemes külön figyelni, mert a bíráló ezekben gyenge volt:",
          "1. **hallucináció vs. helytelen** — a bíráló 162 válaszból csak 2-t nevezett hallucinációnak, pedig",
          "   a magabiztosan kitalált konkrétumok (pl. *„A nagy ho-ho-ho-horgászt József Attila írta”*) ide tartoznak;",
          "2. **részben helyes** — a bíráló egyetlen `reszben` ítéletet sem adott, tehát ezt a kategóriát gyakorlatilag",
          "   nem használta.", ""]

    # ── beírásra kész parancsblokk ─────────────────────────────────────────
    md += ["---", "", "## Beírásra kész parancsok", "",
           "A sorok a **bíráló ítéletével** vannak előkitöltve. Töröld azokat, amelyekkel egyetértesz",
           "(a megerősítéshez elég a `--confirm-all`), a vitatottakon írd át az utolsó szót, majd",
           "futtasd a maradékot egyben. ⛔ A `scores.csv`-t **ne szerkeszd kézzel** — a 08-24-i kör",
           "így veszett el.", "", "```bash"]
    for r in rows:
        md.append(f"python3 src/set_manual.py a {r['item_id']:6s} {r['lang']}  {r['judge']}")
    md += ["```", ""]

    # ── vitás tételek előre: itt a leggyorsabb a megtérülés ─────────────────
    rc_path = scope_paths.res(HERE) / "review_claude.csv"
    if rc_path.exists():
        rc = [r for r in csv.DictReader(rc_path.open(encoding="utf-8")) if not int(r["egyetert"])]
        flip = [r for r in rc if (r["judge"] == "helyes") != (r["review_claude"] == "helyes")]
        rest = [r for r in rc if r not in flip]
        md += ["---", "", "## ⚠️ Vitás tételek — ezekkel kezdd", "",
               f"A második, független bíráló (Claude) {len(rc)} ponton tért el az elsőtől; ebből "
               f"**{len(flip)} változtatja meg a pontosságot**. A többi csak átsorolás "
               "(„helytelen” → „hallucináció”), a 3×3 mátrixot nem érinti.", "",
               "### A pontosságot módosító eltérések", "",
               "| item | nyelv | 35B bíráló | második bíráló | miért |", "|---|---|---|---|---|"]
        for r in flip:
            md.append(f"| {r['item_id']} | {LANG_NAME[r['lang']]} | {r['judge']} | **{r['review_claude']}** | {r['indoklas']} |")
        md += ["", "### Egyéb átsorolás — a 3×3 mátrixot nem érinti (hallucináció / részben)", "",
               "| item | nyelv | második bíráló | miért |", "|---|---|---|---|"]
        for r in rest:
            md.append(f"| {r['item_id']} | {LANG_NAME[r['lang']]} | **{r['review_claude']}** | {r['indoklas']} |")
        md += ["", "---", ""]

    last_group = None
    for r in rows:
        if r["group"] != last_group:
            last_group = r["group"]
            md += ["", f"## {last_group} csoport", ""]
        key = (r["item_id"], r["lang"])
        it = items[r["item_id"]]
        q = strip_label(prompts[key]["prompt"])
        g = gen[key]
        flags = []
        if g["truncated"]:
            flags.append("csonkolt")
        if g["degenerate"]:
            flags.append(f"ismétlési hurok ({g['repeat_ratio']})")
        if g.get("self_eval_cut") is True:
            flags.append("önértékelő toldalék levágva")
        elif g.get("self_eval_cut") == "suspect":
            flags.append("⛔ önértékelő marker a szöveg ELEJÉN — nem vágtunk, nézd meg")
        md += [f"### {r['item_id']} / {LANG_NAME[r['lang']]} — bíráló: **{r['judge']}**"
               + (f"  ⚠️ {', '.join(flags)}" if flags else ""),
               "",
               f"- **Kérdés:** {q}",
               f"- **Várt:** {r['expected']}   *(forrás: {it.get('source', '?')}, {it.get('title', '')})*",
               f"- **Kapott:** {g.get('text_clean', g['text'])[:700]}"
               + ("…" if len(g.get("text_clean", g["text"])) > 700 else ""),
               f"- **Bíráló indoklása:** {r['judge_reason']}", ""]

    out = scope_paths.reports(HERE) / ("02_kezi_ellenorzes_hatra.md" if args.remaining
                                       else "02_kezi_ellenorzes.md")
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"→ {out} ({len(rows)} válasz)")


if __name__ == "__main__":
    main()
