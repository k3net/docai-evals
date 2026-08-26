#!/usr/bin/env python3
"""A nyelvosztályozó pontossága 100 véletlen tokenen (runbook §3 előírása).

    python3 code/classifier_check.py            # a NAIV lens top-20-jának mintája
    python3 code/classifier_check.py --tuned    # a TUNED lens top-20-jának mintája (2026-08-26)

A minta a `reports/03_classifier_minta{,_tuned}.md`-ben áll (seed 0). Az alábbi listák a
második értékelő (Claude, gépi másodvélemény — nem emberi) eltérései — ami nincs benne,
ott egyetértés van. A hibás besorolások mind EGY mintázatot mutatnak: rövid latin betűs
TÖREDÉKEK és TULAJDONNEVEK, amelyek véletlenül szerepelnek valamelyik szótárban.

⛔ A bírálat (2026-08-25, 11. pont) jogosan kérte: a tuned lens kimenetét KÜLÖN kell
validálni, mert a hibák aszimmetrikusak (töredék → `en`), és ez épp a dolgozat „a magyar
prompt köztes olvasata 58 %-ban angol" számát tolhatja fölfelé. Ezért a riport az `en`
osztály PRECÍZIÓJÁT is kiírja (a mintában `en`-nek jelöltek közül hány valóban angol szó),
és ezzel egy egyszerű aránykorrekciót ad a görbéhez.
"""
import argparse
import json
import pathlib
import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent

# token → (gépi osztály, helyes osztály, miért)
ELTERES = {
    " Eb": ("hu", "ismeretlen", "az „eb” benne van a magyar szótárban, de itt latin betűs TÖREDÉK, nem magyar szó"),
    " telem": ("hu", "ismeretlen", "ragozott alakként a szótárban van, tokenként viszont töredék"),
    " Ir": ("en", "ismeretlen", "kétbetűs töredék; angol szóként is kétes"),
    " Mir": ("en", "ismeretlen", "⚠️ épp a magyar „Mirr-Murr” töredéke — a HU11 itemnél ANGOLNAK számolná"),
    " Wei": ("en", "ismeretlen", "kínai átírás latin betűkkel, nem angol szó"),
    " Jana": ("en", "ismeretlen", "tulajdonnév, nem nyelvi jel"),
    "*pi": ("közös", "egyéb", "kódtöredék, nem szó"),
    "\tTokenName": ("ismeretlen", "egyéb", "kódazonosító, nem természetes nyelv"),
}

# A TUNED lens mintája (reports/03_classifier_minta_tuned.md, seed 0) — ugyanaz a szabályrendszer,
# mint fent: tulajdonnév és kínai átírás → `ismeretlen`; latin betűs töredék → `ismeretlen`.
ELTERES_TUNED = {
    "-ra": ("en", "ismeretlen", "⚠️ magyar RAG (-ra), az angol szótár miatt angolnak számolva"),
    " Er": ("en", "ismeretlen", "kétbetűs töredék"),
    "nev": ("en", "ismeretlen", "⚠️ a magyar „név” ékezet nélküli töredéke, angolnak számolva"),
    "v": ("en", "ismeretlen", "egybetűs token, nem nyelvi jel"),
    "pus": ("en", "ismeretlen", "töredék (pl. „campus”, „puszi”), nem angol szó"),
    " Min": ("en", "ismeretlen", "töredék vagy kínai átírás (Min-folyó, Fujian), nem angol szó"),
    "Fe": ("en", "ismeretlen", "töredék / vegyjel"),
    " Shanghai": ("en", "ismeretlen", "kínai tulajdonnév latin átírásban — a naiv mintában a „Wei” ugyanígy"),
    " Hab": ("hu", "ismeretlen", "a „hab” szótári szó, itt tulajdonnév-töredék (Habsburg)"),
    " Vér": ("ékezetes?", "hu", "valódi magyar szó (vér), a nagy kezdőbetű miatt nem találta a szótárban"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuned", action="store_true")
    args = ap.parse_args()
    sfx = "_tuned" if args.tuned else ""
    elt = ELTERES_TUNED if args.tuned else ELTERES
    minta = (scope_paths.reports(HERE) / f"03_classifier_minta{sfx}.md").read_text(encoding="utf-8")
    rows = [l for l in minta.splitlines() if l.startswith("| ") and "`" in l]
    n = len(rows)
    hib = len(elt)
    acc = (n - hib) / n
    # az `en` osztály precíziója: a gépileg `en`-nek jelöltek közül hány maradt `en` a második értékelőnél
    gepi = {}
    for l in rows:
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if len(cells) < 4:          # a ` \n` token sortörése két sorra vágja a táblasort
            continue
        tok = cells[1].strip("`")
        gepi[tok] = cells[3]
    n_en = sum(1 for v in gepi.values() if v == "en")
    false_en = sum(1 for t, (auto, good, _) in elt.items() if auto == "en" and good != "en")
    prec_en = (n_en - false_en) / n_en if n_en else float("nan")
    n_hu = sum(1 for v in gepi.values() if v == "hu")
    false_hu = sum(1 for t, (auto, good, _) in elt.items() if auto == "hu" and good != "hu")
    miss_hu = sum(1 for t, (auto, good, _) in elt.items() if auto != "hu" and good == "hu")

    cim = "tuned lens" if args.tuned else "naiv lens"
    md = [f"# Nyelvosztályozó — mért pontosság ({cim})", "",
          f"**{n} véletlen token** (seed 0) a {cim} top-20-jából, kétszeres értékeléssel "
          "(gépi osztályozó + Claude másodvélemény, nem emberi ellenőrző bírálat). "
          f"Egyetértés: **{n - hib}/{n} = {acc:.0%}**.", "",
          f"**Az `en` osztály precíziója:** a mintában {n_en} tokent jelölt a gép angolnak, ebből "
          f"{false_en} nem angol szó → precízió **{prec_en:.0%}**. A `hu` osztály: {n_hu} jelölt, "
          f"{false_hu} téves, {miss_hu} elmaradt találat.", "",
          "## Az eltérések és a mintázatuk", "",
          "| token | gépi | helyes | miért |", "|---|---|---|---|"]
    for t, (auto, good, why) in elt.items():
        md.append(f"| `{t}` | {auto} | **{good}** | {why} |")
    md += ["", f"⛔ **A hibák egy irányba mutatnak: rövid latin betűs töredék vagy tulajdonnév → `en`** "
           f"({false_en} a {hib} hibából). Ez pont az a zaj, amire a runbook figyelmeztetett "
           "(„az angol–magyar közös tokenek zajt adnak”) — a mérés ezt számszerűsíti.", "",
           "**Következmény:** a `hu`/`en` megkülönböztetés SZAVAKRA megbízható, TÖREDÉKEKRE nem. "
           "A nyelvi arány-görbét csak a `közös`+`ismeretlen` sávval együtt szabad olvasni, és az "
           f"„angol arány” számokat a fenti precízióval korrigálva ({prec_en:.0%} szorzó) érdemes "
           "alsó becslésként is közölni. A CJK-detektálás (zh) Unicode-alapú és a mintában **hibátlan**.", ""]
    out = scope_paths.reports(HERE) / f"03_classifier_ellenorzes{sfx}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    (scope_paths.reports(HERE) / f"03_classifier_ellenorzes{sfx}.json").write_text(
        json.dumps({"n": n, "hibak": hib, "pontossag": round(acc, 3),
                    "en_jelolt": n_en, "en_teves": false_en, "en_precizio": round(prec_en, 3),
                    "hu_jelolt": n_hu, "hu_teves": false_hu, "hu_elmaradt": miss_hu,
                    "eltoresek": {k: {"gepi": v[0], "helyes": v[1], "miert": v[2]} for k, v in elt.items()}},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
