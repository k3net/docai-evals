#!/usr/bin/env python3
"""Mérés A elemzése — a 3×3 pontossági mátrix a runbook szerint.

    python3 code/analyze_a.py            # a scores.csv-ből, LLM nélkül; a ellenőrző kör után újrafuttatható

A `final` oszlop az igazságforrás: a bíráló ítélete, felülírva a `manual` oszloppal ott,
ahol az ellenőrző kör újraítélte (runbook §2: a ZH és HU csoportnál ez KÖTELEZŐ). A `final`
SZÁRMAZTATOTT oszlop, a szabálya egy helyen él: `check_scores.derive()`.
Kimenet: reports/02_meres_a.md + reports/02_meres_a.json.
"""
import csv
import json
import math
import pathlib
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import scope_paths
from check_scores import derive

HERE = pathlib.Path(__file__).resolve().parent.parent
FIG = scope_paths.figures(HERE)
SC = scope_paths.res(HERE) / "scores.csv"
OUT = scope_paths.reports(HERE)
LANGS = ("hu", "en", "zh")
GROUPS = ("ZH", "HU", "UNI")
VERDICTS = ("helyes", "reszben", "helytelen", "hallucinacio")


def wilson(k, n, z=1.96):
    """Wilson-intervallum — kis n-nél (15–20) a normál közelítés félrevezető lenne."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))


def main():
    rows = list(csv.DictReader(SC.open(encoding="utf-8")))
    for r in rows:
        # ⛔ Korábban itt NÉMÁN újraszámoltuk a `final`-t. Emiatt a riportok akkor is helyesek
        # maradtak, amikor a lemezre írt oszlop elavult volt — aki viszont a publikált CSV-t
        # olvasta, más számokat kapott (a HU-csoport kitalálás-aránya 62% helyett 3%-ot).
        # Most hangosan elhasal; a javítás: python3 code/check_scores.py --fix
        want = derive(r)
        if r["final"].strip() != want:
            raise SystemExit(
                f"{SC}: {r['item_id']}/{r['lang']} final={r['final']!r}, pedig {want!r} — "
                f"a `final` származtatott oszlop elavult. Javítás: python3 code/check_scores.py --fix")
        r["final"] = want
        r["truncated"], r["degenerate"] = int(r["truncated"]), int(r["degenerate"])
    n_manual = sum(1 for r in rows if r["manual"].strip())

    cells, lines = {}, []
    for g in GROUPS:
        for lang in LANGS:
            sub = [r for r in rows if r["group"] == g and r["lang"] == lang]
            c = Counter(r["final"] for r in sub)
            n = len(sub)
            strict, lenient = c["helyes"], c["helyes"] + c["reszben"]
            cells[f"{g}/{lang}"] = {
                "n": n, "helyes": c["helyes"], "reszben": c["reszben"],
                "helytelen": c["helytelen"], "hallucinacio": c["hallucinacio"],
                "acc_strict": round(strict / n, 3), "ci_strict": [round(x, 3) for x in wilson(strict, n)],
                "acc_lenient": round(lenient / n, 3),
                "truncated": sum(r["truncated"] for r in sub),
                "degenerate": sum(r["degenerate"] for r in sub),
            }

    def table(key, fmt=lambda v: f"{v:.0%}"):
        out = ["| csoport | hu | en | zh |", "|---|---|---|---|"]
        for g in GROUPS:
            out.append(f"| **{g}** (n={cells[f'{g}/hu']['n']}) | " +
                       " | ".join(fmt(cells[f"{g}/{l}"][key]) for l in LANGS) + " |")
        return "\n".join(out)

    md = [f"# Mérés A — válaszminőség (3×3 pontossági mátrix)", ""]
    md.append(f"Forrás: `results/scores.csv` ({len(rows)} faktuális válasz) · "
              f"az ellenőrző körben újraítélve: **{n_manual}/{len(rows)}**"
              + ("  ⛔ **a kötelező ellenőrző kör (ZH+HU, 102 válasz) még hátravan** — az alábbi számok a "
                 "bíráló (Qwen3.6-35B) első köre" if n_manual < 102 else "") + "\n")
    md += ["## Szigorú pontosság (csak „helyes”)", "", table("acc_strict"), "",
           "## Megengedő pontosság („helyes” + „részben”)", "", table("acc_lenient"), "",
           "## Ítélet-eloszlás cellánként", "",
           "| csoport / nyelv | n | helyes | részben | helytelen | halluc. | csonkolt | degenerált |",
           "|---|---|---|---|---|---|---|---|"]
    for g in GROUPS:
        for lang in LANGS:
            c = cells[f"{g}/{lang}"]
            md.append(f"| {g} / {lang} | {c['n']} | {c['helyes']} | {c['reszben']} | {c['helytelen']} | "
                      f"{c['hallucinacio']} | {c['truncated']} | {c['degenerate']} |")

    # ── kontroll: a dekódolási zaj nélküli részhalmaz ───────────────────────
    # ⛔ A magyar oszlopban a legtöbb a csonkolt/degenerált válasz. Ha a pontosság-különbség
    # ezek nélkül IS megmarad, akkor nem a dekódolás műterméke — ezt ki kell számolni,
    # nem elég figyelmeztetni rá.
    clean = {}
    for g in GROUPS:
        for lang in LANGS:
            sub = [r for r in rows if r["group"] == g and r["lang"] == lang
                   and not r["truncated"] and not r["degenerate"]]
            k = sum(1 for r in sub if r["final"] == "helyes")
            clean[f"{g}/{lang}"] = {"n": len(sub), "helyes": k,
                                    "acc": round(k / len(sub), 3) if sub else None}
    md += ["", "## Kontroll — csak a csonkolatlan, nem degenerált válaszok", "",
           "| csoport | hu | en | zh |", "|---|---|---|---|"]
    for g in GROUPS:
        cs = [clean[f"{g}/{l}"] for l in LANGS]
        md.append(f"| **{g}** | " + " | ".join(
            (f"{c['acc']:.0%} (n={c['n']})" if c["acc"] is not None else "– (n=0)") for c in cs) + " |")
    md += ["", "Ha ez a tábla ugyanazt a mintázatot mutatja, mint a teljes mátrix, akkor a nyelvek közti "
           "különbség **nem** a token-keretből és nem az ismétlési hurkokból jön."]

    # ── a runbook két kulcskérdése ──────────────────────────────────────────
    zh_hu, hu_zh = cells["ZH/hu"], cells["HU/zh"]
    zh_zh, hu_hu = cells["ZH/zh"], cells["HU/hu"]
    # ── hallucináció: a ellenőrző kör fő hatása, ezért külön táblát kap ──────────
    # ⛔ A gépi bíráló a 162 válaszból alig 2-t nevezett hallucinációnak, a ellenőrző kör 43
    # átsorolást hozott — a hallucinációs arány tehát CSAK a kézzel nézett cellákban
    # (ZH + HU) értelmes szám. A UNI csoport nem volt a kötelező körben, ezért kimarad.
    hal_scope = [g for g in GROUPS if all(
        r["manual"].strip() for r in rows if r["group"] == g)]
    if hal_scope:
        md += ["", "## Hallucináció — magabiztosan állított, kitalált konkrétum", "",
               "A `hallucinacio` ítélet akkor jár, ha a válasz KONKRÉT tényt állít (nevet, helyet, "
               "dátumot, intézményt), és az téves — szemben a `helytelen`-nel, ami kitérés, rossz "
               "kategória vagy nem-válasz. ⛔ A gépi bíráló ezt a kategóriát gyakorlatilag nem "
               "használta, ezért az alábbi arányok **csak az ellenőrző körrel fedett csoportokra** "
               f"({', '.join(hal_scope)}) érvényesek.", "",
               "| csoport | hu | en | zh |", "|---|---|---|---|"]
        for g in hal_scope:
            md.append(f"| **{g}** (n={cells[f'{g}/hu']['n']}) | " + " | ".join(
                f"{cells[f'{g}/{l}']['hallucinacio'] / cells[f'{g}/{l}']['n']:.0%} "
                f"({cells[f'{g}/{l}']['hallucinacio']}/{cells[f'{g}/{l}']['n']})" for l in LANGS) + " |")
        # a téves válaszok közül HÁNY a magabiztos kitaláció — ez a valódi kérdés
        md += ["", "A tévedés MÓDJA: a nem helyes válaszokon belül mekkora a magabiztos kitaláció aránya.", "",
               "| csoport | hu | en | zh |", "|---|---|---|---|"]
        for g in hal_scope:
            cs = []
            for l in LANGS:
                c = cells[f"{g}/{l}"]
                wrong = c["helytelen"] + c["hallucinacio"]
                cs.append(f"{c['hallucinacio'] / wrong:.0%} ({c['hallucinacio']}/{wrong})"
                          if wrong else "–")
            md.append(f"| **{g}** | " + " | ".join(cs) + " |")
        md += ["", "⭐ Ha a modell egy nyelven nem tudja a választ, az látszik-e rajta? A második tábla "
               "erre felel: minél magasabb a szám, annál gyakrabban **talál ki** ahelyett, hogy "
               "kitérne — vagyis annál kevésbé jelzi a saját tudatlanságát.", ""]

    md += ["", "## A runbook két kérdése", "",
           f"**1. Átmegy-e a tudás a nyelvhatáron?** A ZH-only csoport magyar promptra "
           f"**{zh_hu['acc_strict']:.0%}** (n={zh_hu['n']}, 95% CI {zh_hu['ci_strict'][0]:.0%}–{zh_hu['ci_strict'][1]:.0%}), "
           f"kínai promptra {zh_zh['acc_strict']:.0%}. "
           + ("Nem nulla → a tudás átmegy, nem csak a forrásnyelven érhető el."
              if zh_hu["acc_strict"] > 0 else "**Nulla** → ez a H0 felé mutató jel."),
           "",
           f"**2. Aszimmetria.** ZH-only → hu: **{zh_hu['acc_strict']:.0%}** · HU-only → zh: **{hu_zh['acc_strict']:.0%}** "
           f"(a saját forrásnyelvén: ZH/zh {zh_zh['acc_strict']:.0%} · HU/hu {hu_hu['acc_strict']:.0%}). "
           + ("A kínai tudás könnyebben megy magyarra, mint fordítva — korpuszméret-hatás."
              if zh_hu["acc_strict"] > hu_zh["acc_strict"] else
              "A magyar tudás megy könnyebben kínaira — a korpuszméret-hipotézissel ELLENTÉTES irány."
              if hu_zh["acc_strict"] > zh_hu["acc_strict"] else "A két irány egyforma."),
           "",
           "⛔ **Olvasási figyelmeztetés:** a csonkolt és a degenerált válaszok cellánkénti számát a fenti tábla "
           "külön hozza. Ahol ezek aránya magas (jellemzően a magyar oszlop), ott a pontosság a dekódolás "
           "műtermékét is méri, nem csak a tudást — a következtetést erre a sorra is rá kell építeni."]

    # ── megbízhatóság: három értékelő ugyanazon a 102 válaszon ──────────────
    # A ellenőrző kör 2026-08-25-én ELKÉSZÜLT, ezért a kérdés már nem az, hogy „mit szűrjek én", hanem hogy MENNYIT SZÁMÍTOTT a ellenőrző kör — ezt egy bírálótól elsőként kérdezik.
    # Három értékelő: (1) a 35B bíráló, (2) egy másik modellcsalád (Claude, `review_claude.py`),
    # (3) a saját ellenőrző köröm (`manual`). A (3) az igazságforrás, a másik kettő ehhez mérve.
    rc_path = scope_paths.res(HERE) / "review_claude.csv"
    sens = None
    scope = [r for r in rows if r["group"] in ("ZH", "HU")]
    n_scope = len(scope)
    has_manual = sum(1 for r in scope if r["manual"].strip())
    if has_manual == n_scope:
        rc = ({(r["item_id"], r["lang"]): r for r in csv.DictReader(rc_path.open(encoding="utf-8"))}
              if rc_path.exists() else {})

        def agree_with_manual(get):
            ok = same = 0
            for r in scope:
                v = get(r)
                if v:
                    ok += 1
                    same += int(v == r["manual"].strip())
            return same, ok

        j_same, j_n = agree_with_manual(lambda r: r["judge"].strip())
        c_same, c_n = agree_with_manual(
            lambda r: (rc.get((r["item_id"], r["lang"])) or {}).get("review_claude", ""))

        # a mátrix a ellenőrző kör NÉLKÜL — csak a gépi bírálóval
        judge_cells = {}
        for g in GROUPS:
            for lang in LANGS:
                sub = [r for r in rows if r["group"] == g and r["lang"] == lang]
                judge_cells[f"{g}/{lang}"] = round(
                    sum(1 for r in sub if r["judge"].strip() == "helyes") / len(sub), 3)

        # a pontosságot ténylegesen módosító kézi korrekciók, és az IRÁNYUK
        flips = [r for r in scope
                 if (r["judge"].strip() == "helyes") != (r["manual"].strip() == "helyes")]
        lenient = [r for r in flips if r["judge"].strip() == "helyes"]
        nonsrc = [r for r in flips if r["lang"] != r["group"].lower()]
        recat = [r for r in scope if r["judge"].strip() != r["manual"].strip() and r not in flips]

        sens = {"judge_vs_manual": [j_same, j_n], "claude_vs_manual": [c_same, c_n],
                "judge_only_cells": judge_cells, "n_flip": len(flips),
                "n_flip_lenient": len(lenient), "n_recat": len(recat)}

        md += ["", "## Megbízhatóság — három értékelő ugyanazon a 102 válaszon", "",
               "A kötelező ellenőrző kör (ZH + HU, 102 válasz) **elkészült**, ezért a `final` oszlop a "
               "ellenőrző ítéleteimet használja. Az alábbi tábla azt méri, mennyire estek ehhez közel a "
               "gépi értékelők.", "",
               "| értékelő | egyetértés a ellenőrző ítéleteimmel |", "|---|---|",
               f"| Qwen3.6-35B bíráló (a mérés bírálója) | **{j_same}/{j_n} = {j_same/j_n:.0%}** |",
               f"| Claude, második gépi vélemény (más modellcsalád) | **{c_same}/{c_n} = "
               f"{c_same/c_n:.0%}** |" if c_n else "| Claude, második gépi vélemény | – |", "",
               f"A {n_scope - j_same} eltérésből **{len(flips)} változtatja meg a pontosságot** "
               f"(helyes ↔ nem helyes), a többi **{len(recat)} kategória-átsorolás** — jellemzően "
               "`helytelen` → `hallucinacio`, amit a bíráló szinte soha nem használt.", "",
               "### A 3×3 mátrix a ellenőrző kör nélkül és vele", "",
               "| csoport | hu | en | zh |", "|---|---|---|---|"]
        for g in GROUPS:
            md.append(f"| **{g}** | " + " | ".join(
                (f"**{cells[f'{g}/{l}']['acc_strict']:.0%}**"
                 + (f" *(gépi: {judge_cells[f'{g}/{l}']:.0%})*"
                    if judge_cells[f"{g}/{l}"] != cells[f"{g}/{l}"]["acc_strict"] else ""))
                for l in LANGS) + " |")
        md += ["", "*(vastagon a végleges, ellenőrző ítéletekre épülő érték; zárójelben a gépi bíráló "
               "egyedüli értéke, ahol eltér — a UNI csoport nem volt a kötelező körben)*", ""]
        if flips:
            names = ", ".join(f"{r['item_id']}/{r['lang']}" for r in flips)
            md.append(
                f"⭐ **A pontosságot módosító korrekció {len(flips)} darab** ({names})"
                + (f", és **mind a {len(flips)} egy irányba mutat: a gépi bíráló ENGEDÉKENYEBB volt**"
                   if len(lenient) == len(flips) else
                   f", ebből {len(lenient)} a gépi bíráló engedékenységéből")
                + (f"; {len(nonsrc)} a **NEM forrásnyelvi** cellában áll" if nonsrc else "")
                + ". A gépi bíráló hibája tehát a nyelvhatáron átmenő tudást inkább FELÜLbecsli — "
                  "vagyis a ellenőrző kör nélkül a dolgozat fő állítása (a tudás átmegy) **erősebbnek** "
                  "látszana, mint amilyen.")
        md += ["", "⛔ **Korlát:** a ellenőrző kört én pontoztam, és a korpuszt is én állítottam össze, tehát nem vagyok vak értékelő. "
               "A ellenőrző kör ítéleteinek tételes indoklása a `reports/kezi_validacio_naplo.md`-ben "
               "olvasható; a gépi bírálók ítéletei a `results/judge.jsonl`-ben és a "
               "`results/review_claude.csv`-ben maradtak meg, tehát a korrekciók visszakereshetők.", ""]
    elif rc_path.exists():
        rc = {(r["item_id"], r["lang"]): r for r in csv.DictReader(rc_path.open(encoding="utf-8"))}
        agree = sum(int(r["egyetert"]) for r in rc.values())
        md += ["", "## Érzékenységvizsgálat — második, független bíráló", "",
               f"A ZH és HU csoport 102 válaszát egy másik modellcsalád (Claude) is végigértékelte. "
               f"Egyetértés az első bírálóval: **{agree}/102 = {agree/102:.0%}**. "
               f"⚠️ A kötelező ellenőrző kör még hiányos ({has_manual}/{n_scope}), ezért ez csak a bíráló "
               "megbízhatóságának becslése.", ""]

    OUT.mkdir(exist_ok=True)
    # ── A1 ábra: a 3×3 pontossági heatmap (runbook §5 első kötelező ábrája) ──
    # A forrásnyelvi átló KERETET kap: a dolgozat állítása épp az, hogy a modell a
    # forrásnyelven NEM erősebb — ez akkor olvasható le, ha a szem megtalálja az átlót.
    FIG.mkdir(exist_ok=True)
    mat = np.array([[cells[f"{g}/{l}"]["acc_strict"] for l in LANGS] for g in GROUPS])
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    im = ax.imshow(mat, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(LANGS)), [{"hu": "magyar", "en": "angol", "zh": "kínai"}[l] for l in LANGS])
    ax.set_yticks(range(len(GROUPS)), [f"{g}-only\n(n={cells[f'{g}/hu']['n']})" if g != "UNI"
                                       else f"UNI (univerzális)\n(n={cells['UNI/hu']['n']})" for g in GROUPS])
    ax.set_xlabel("a kérdés nyelve")
    for i, g in enumerate(GROUPS):
        for j, l in enumerate(LANGS):
            c = cells[f"{g}/{l}"]
            lo, hi = c["ci_strict"]
            ax.text(j, i, f"{c['acc_strict']:.0%}\n{c['helyes']}/{c['n']}\n[{lo:.0%}–{hi:.0%}]",
                    ha="center", va="center", fontsize=9,
                    color="#111" if .25 < c["acc_strict"] < .8 else "#111")
    # a forrásnyelv cellája (a UNI-nak nincs egy forrásnyelve)
    for g, src in (("ZH", "zh"), ("HU", "hu")):
        ax.add_patch(plt.Rectangle((LANGS.index(src) - .5, GROUPS.index(g) - .5), 1, 1,
                                   fill=False, ec="#2c3e50", lw=2.5))
    fig.colorbar(im, ax=ax, label="szigorú pontosság", fraction=.046)
    ax.set_title("A1 — pontosság csoport × kérdésnyelv\n(keret: a csoport saját forrásnyelve)",
                 fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "02_A1_pontossag_heatmap.png", dpi=160); plt.close(fig)

    (OUT / "02_meres_a.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (OUT / "02_meres_a.json").write_text(json.dumps({"cells": cells, "clean": clean, "n_manual": n_manual, "sensitivity_second_rater": sens,
                                                     "verdict_counts": dict(Counter(r["final"] for r in rows))},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))
    print(f"\n→ {OUT / '02_meres_a.md'}")


if __name__ == "__main__":
    main()
