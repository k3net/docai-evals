#!/usr/bin/env python3
"""Függelék-ábra: prompt-tokenhossz csoport × nyelv (runbook §5, 7. ábra).

    python3 code/analyze_tokens.py

⛔ Miért kell ez az ábra a dolgozatba? Mert a 3×3 mátrix magyar oszlopa NEM csak tudást
mér: ugyanaz a kérdés magyarul több tokenre bomlik, tehát fix token-keret mellett a magyar
válaszba kevesebb TARTALOM fér. A korlát-fejezet erre az ábrára hivatkozik.

⚠️ Két KÜLÖNBÖZŐ szorzó kering, ne keverd őket:
  * **hu/zh = 1,87×** — ezt idézi az env.md és a runbook, ez a szélső eset;
  * **hu/en = 1,43×** — ez az, ami a 3×3 mátrix angol oszlopával való összevetésre vonatkozik.
A kettő ugyanabból az adatból jön (zh/en = 0,77×, és 1,43 / 0,77 = 1,86).
A `reports/00_token_lengths.csv` a fázis 0 mérése (`dump_tokens.py`).
"""
import csv
import json
import pathlib
import statistics as st
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT, FIG = scope_paths.reports(HERE), scope_paths.figures(HERE)
LANGS = ["hu", "en", "zh"]
LANG_NAME = {"hu": "magyar", "en": "angol", "zh": "kínai"}
LCOL = {"hu": "#c0392b", "en": "#2980b9", "zh": "#27ae60"}


def main():
    rows = list(csv.DictReader((OUT / "00_token_lengths.csv").open(encoding="utf-8")))
    groups = sorted({r["group"] for r in rows})
    by = defaultdict(list)
    for r in rows:
        by[(r["group"], r["lang"])].append(int(r["n_tokens"]))

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.3),
                                  gridspec_kw={"width_ratios": [2.2, 1]})

    # bal: csoportonkénti bokszdiagram, nyelvenként eltolva
    width, pos, ticks = .26, [], []
    for i, g in enumerate(groups):
        for j, l in enumerate(LANGS):
            b = ax.boxplot([by[(g, l)]], positions=[i + (j - 1) * width], widths=width * .85,
                           patch_artist=True, medianprops={"color": "#222"},
                           flierprops={"marker": ".", "ms": 3, "mfc": "#555", "mec": "none"})
            b["boxes"][0].set(facecolor=LCOL[l], alpha=.65, edgecolor=LCOL[l])
        ticks.append(i)
    ax.set_xticks(ticks, groups)
    ax.set_xlabel("csoport"); ax.set_ylabel("prompt-tokenhossz")
    ax.grid(axis="y", alpha=.25)
    ax.legend(handles=[plt.Line2D([], [], color=LCOL[l], lw=6, alpha=.65, label=LANG_NAME[l])
                       for l in LANGS], fontsize=9)
    ax.set_title("prompt-tokenhossz csoportonként", fontsize=10)

    # jobb: az angolhoz mért szorzó — ez a szám kerül a korlát-fejezetbe
    ratios = {}
    for l in LANGS:
        pairs = [(int(r["n_tokens"]), r["item_id"]) for r in rows if r["lang"] == l]
        en = {r["item_id"]: int(r["n_tokens"]) for r in rows if r["lang"] == "en"}
        # ⛔ PÁROSÍTVA, itemenként — a csoportátlagok hányadosa mást ad, mert az itemek
        # hossza nagyon szór (a ZH-csoport kérdései rövidebbek).
        ratios[l] = [n / en[i] for n, i in pairs if en.get(i)]
    ax2.bar([LANG_NAME[l] for l in LANGS], [st.mean(ratios[l]) for l in LANGS],
            color=[LCOL[l] for l in LANGS], alpha=.75)
    for i, l in enumerate(LANGS):
        ax2.text(i, st.mean(ratios[l]) + .03, f"{st.mean(ratios[l]):.2f}×", ha="center", fontsize=10)
    ax2.axhline(1, color="#7f8c8d", lw=1, ls="--")
    ax2.set_ylabel("tokenhossz az angolhoz képest"); ax2.grid(axis="y", alpha=.25)
    ax2.set_title("itemenként párosított szorzó", fontsize=10)

    fig.suptitle("T1 — tokenizációs aszimmetria: ugyanaz a kérdés, más tokenszám", fontsize=11)
    fig.tight_layout()
    fig.savefig(FIG / "00_T1_tokenhossz.png", dpi=160)
    plt.close(fig)

    stats = {f"{g}/{l}": {"n": len(by[(g, l)]), "median": st.median(by[(g, l)]),
                          "mean": round(st.mean(by[(g, l)]), 1)}
             for g in groups for l in LANGS}
    stats["ratio_vs_en"] = {l: round(st.mean(ratios[l]), 3) for l in LANGS}
    stats["ratio_hu_zh"] = round(st.mean(ratios["hu"]) / st.mean(ratios["zh"]), 3)
    (OUT / "00_token_lengths.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2),
                                               encoding="utf-8")
    print(f"→ {FIG / '00_T1_tokenhossz.png'}")
    print("  szorzó az angolhoz (itemenként párosítva): "
          + ", ".join(f"{LANG_NAME[l]} {st.mean(ratios[l]):.2f}×" for l in LANGS))
    print(f"  ebből hu/zh = {st.mean(ratios['hu']) / st.mean(ratios['zh']):.2f}× "
          "(ezt idézi az env.md és a runbook)")


if __name__ == "__main__":
    main()
