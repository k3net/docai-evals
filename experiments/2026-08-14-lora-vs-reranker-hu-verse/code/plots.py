"""A dolgozat ábrái. A laptopon fut, a kiértékelés eredményeiből.

Három ábra:
  1. `forma.png`        — a formai metrikák feltételenként, GOLD referenciával
  2. `memorizacio.png`  — extraction: train vs holdout (a rés a LoRA hozzájárulása)
  3. `tanulas.png`      — eval loss a checkpointokon

Vizuális elvek (a projekt data-viz konvenciója szerint):
  * **Nincs kettős tengely.** Minden metrika 0–1 arány, tehát közös skálán áll;
    ami nem, az külön ábrára megy.
  * **A GOLD nem versenyző**, hanem referencia — szaggatott vonal, nem oszlop.
  * A kategóriaszínek FIX sorrendben állnak, nem ciklikusan; a színsor
    validált (ΔE-szeparáció színtévesztésre is).
  * Minden oszlop direkt értékcímkét kap: a világos hue-k kontrasztja a
    felülethez alacsony, ezt a felirat oldja fel.

    python3 code/plots.py
"""

from __future__ import annotations

import json
import re
import statistics as st
import sys
from pathlib import Path

from config import ROOT

RESULTS = ROOT / "data" / "results"
FIGS = ROOT / "reports" / "figures"

# Kategóriapaletta, FIX sorrend — SÖTÉT alapra hangolva, a dolgozat HTML-jének
# palettájával azonosan (dolgozat.html / gyorstalpalo.html tokenjei).
# A hue-választás szemantikus is: a reranker-ágak a „select" türkizhez, a
# LoRA-ágak a „trained" pirosához közelítenek.
COLORS = {
    "B0": "#7A8496",   # frozen — nyers bázis
    "B1": "#6E9BE0",
    "B2": "#4FC7D1",   # select — reranker az ágon
    "C": "#FF6E85",    # trained — LoRA az ágon
    "C2": "#C88CF0",
}
ORDER = ["B0", "B1", "B2", "C", "C2"]
LABELS = {
    "B0": "B0 — nyers",
    "B1": "B1 — few-shot",
    "B2": "B2 — few-shot + reranker",
    "C": "C — LoRA",
    "C2": "C2 — LoRA + reranker",
}
INK = "#ECEFF4"     # elsődleges szöveg a sötét felületen
INK2 = "#8D97A6"    # másodlagos / tengelyfelirat
GRID = "#252C38"    # visszahúzódó rács
GOLD_C = "#D9B25F"  # a GOLD referenciavonal — nem versenyző, ezért saját szín
SURFACE = "#141922" # a HTML `--surface` tokenje; az ábra beleolvad a lapba

# A „↓ jobb" jelöléssel: a kitalált szó és az ismétlés HIBA, nem teljesítmény —
# az ábrán a magasabb oszlop ott rosszabb.
METRICS = [
    ("stanza_count", "strófaszám betartva"),
    ("syllable_exact", "szótagszám pontos"),
    ("rhyme_rate", "rímarány"),
    ("rhyme_quality", "rímminőség (ragrím nélkül)"),
    ("invented_rate", "kitalált szó  ↓ jobb"),
    ("repeat_rate", "ismételt sor  ↓ jobb"),
]


def mean_of(rows: list[dict], cond: str, field: str) -> float | None:
    vals = [r[field] for r in rows if r["condition"] == cond and r.get(field) is not None]
    return st.mean(vals) if vals else None


def plot_form(rows: list[dict], key: str) -> None:
    import matplotlib.pyplot as plt

    sub = [r for r in rows if r["source_key"] == key]
    present = [c for c in ORDER if any(r["condition"] == c for r in sub)]
    if not present:
        return

    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.8))
    fig.patch.set_facecolor(SURFACE)
    for ax, (field, title) in zip(axes.flat, METRICS):
        ax.set_facecolor(SURFACE)
        vals = [mean_of(sub, c, field) or 0.0 for c in present]
        bars = ax.bar(
            range(len(present)), vals,
            color=[COLORS[c] for c in present], width=0.68, zorder=3,
        )
        gold = mean_of(sub, "GOLD", field)
        top = max(vals + ([gold] if gold is not None else [0.0]))
        # Panelenkénti skála: a hibametrikák (kitalált szó, ismétlés) 0,02–0,12
        # tartományban mozognak, egy közös 0–1 tengelyen a különbségük eltűnne.
        # A small multiples formánál ez megengedett — minden panel saját
        # tengelyfelirattal áll.
        ax.set_ylim(0, max(0.18, top * 1.3))
        if gold is not None:
            ax.axhline(gold, color=GOLD_C, ls=(0, (4, 3)), lw=1.6, zorder=4)
            # A felirat a vonal fölé kerül, kivéve ha a vonal a panel alján
            # van — ott alá, hogy ne írjon rá az oszlopokra.
            above = gold < max(0.18, top * 1.3) * 0.55
            ax.text(0.985, gold, "GOLD", va="top" if not above else "bottom",
                    ha="right", fontsize=8, color=GOLD_C,
                    transform=ax.get_yaxis_transform(), zorder=5)
        # Direkt értékcímke: a paletta világos hue-inak kontrasztja alacsony,
        # a szám teszi egyértelművé az olvasatot.
        head = ax.get_ylim()[1] * 0.03
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + head, f"{v:.3f}".rstrip("0"),
                    ha="center", va="bottom", fontsize=8, color=INK)
        ax.set_title(title, fontsize=9.5, color=INK, pad=8)
        ax.set_xticks(range(len(present)))
        ax.set_xticklabels(present, fontsize=8.5, color=INK2)
        ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(length=0, labelsize=8, colors=INK2)

    handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[c]) for c in present]
    fig.legend(handles, [LABELS[c] for c in present], loc="lower center",
               ncol=min(5, len(present)), frameon=False, fontsize=8.5,
               labelcolor=INK2, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle(f"Formai metrikák feltételenként — {key}", fontsize=12, color=INK, y=0.98)
    fig.tight_layout(rect=(0, 0.06, 1, 0.94), h_pad=2.4, w_pad=1.6)
    out = FIGS / f"forma_{key}.png"
    fig.savefig(out, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  {out}")


def plot_extraction(rows: list[dict], key: str) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    sub = [r for r in rows if r["source_key"] == key]
    conds = [c for c in ORDER if any(r["condition"] == c for r in sub)]
    if not conds:
        return

    tr = [st.mean([r["longest_ngram"] for r in sub if r["condition"] == c and r["split"] == "train"] or [0]) for c in conds]
    ho = [st.mean([r["longest_ngram"] for r in sub if r["condition"] == c and r["split"] == "holdout"] or [0]) for c in conds]

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    x = np.arange(len(conds))
    w = 0.36
    # Szemantikus színezés: a tanított oldal a „trained" piros, a KONTROLL a
    # visszahúzódó szürke — a rés (a kettő különbsége) így vizuálisan is olvasható.
    b1 = ax.bar(x - w / 2 - 0.01, tr, w, label="tréningben látott vers",
                color=COLORS["C"], zorder=3)
    b2 = ax.bar(x + w / 2 + 0.01, ho, w, label="holdout (kontroll)",
                color=COLORS["B0"], zorder=3)
    for bars, vals in ((b1, tr), (b2, ho)):
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.06, f"{v:.1f}",
                    ha="center", va="bottom", fontsize=8.5, color=INK)
    ax.set_ylabel("leghosszabb szó szerinti egyezés (szó)", fontsize=9, color=INK2)
    ax.set_xticks(x)
    ax.set_xticklabels([LABELS[c] for c in conds], fontsize=8.5, color=INK2)
    ax.grid(axis="y", color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0, labelsize=8.5, colors=INK2)
    # A jelmagyarázat a tengely FÖLÉ kerül: az oszlopok mindkét oldalon
    # magasak, belül bármelyik sarokban takarna.
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2,
              loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    top = max(tr + ho)
    ax.set_ylim(0, top * 1.35)
    ax.text(
        0.5, 0.90,
        "a kill-küszöb 8 szó — egyik ág sem közelíti meg (0% a reprodukció)",
        transform=ax.transAxes, ha="center", fontsize=8.5, color=INK2,
    )
    ax.set_title(
        "Memorizáció: a holdout ág a pretrainingből jövő rész,\n"
        "a két oszlop különbsége a LoRA hozzájárulása",
        fontsize=10.5, color=INK, pad=26,
    )
    fig.tight_layout()
    out = FIGS / f"memorizacio_{key}.png"
    fig.savefig(out, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  {out}")


def plot_training() -> None:
    """Eval loss a checkpointokon — a trainer_state.json-ból."""
    import matplotlib.pyplot as plt

    if not (RESULTS / "runs").exists():
        print("  (nincs futásnapló — kimarad)")
        return
    # ⚠️ Lépésszám szerint, NEM ábécésorrendben: a `checkpoint-83` ábécében
    # a `checkpoint-501` után jön, és így a görbe 0,5 epochnál csonkulna.
    states = sorted(
        (RESULTS / "runs").rglob("trainer_state.json"),
        key=lambda q: int(m.group(1)) if (m := re.search(r"checkpoint-(\d+)", str(q))) else 0,
    )
    if not states:
        print("  (nincs trainer_state.json — kimarad)")
        return
    state = json.loads(states[-1].read_text(encoding="utf-8"))
    hist = state.get("log_history", [])
    ev = [(h["epoch"], h["eval_loss"]) for h in hist if "eval_loss" in h]
    trn = [(h["epoch"], h["loss"]) for h in hist if "loss" in h]
    if not ev:
        print("  (nincs eval_loss a naplóban — kimarad)")
        return

    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    if trn:
        ax.plot([e for e, _ in trn], [v for _, v in trn], color=COLORS["B0"], lw=2,
                label="tanítási veszteség", zorder=3)
    ax.plot([e for e, _ in ev], [v for _, v in ev], color=COLORS["C"], lw=2,
            marker="o", ms=5, label="validációs veszteség", zorder=4)
    # Csak akkor címkézünk, ha az előző címke óta elég nagy a lépés — a
    # 2,967 / 2,968 pár különben egymásra írna.
    last_x = -9.0
    for e, v in ev:
        if e - last_x >= 0.45:
            ax.text(e, v + 0.022, f"{v:.3f}", ha="center", fontsize=8, color=INK)
            last_x = e
    lo = min(ev, key=lambda t: t[1])
    # SZÁNDÉKOSAN nem „optimum": a 8.2 szerint a veszteség-minimum NEM
    # stílus-optimum — a 3 epochos adapter minden mért tengelyen jobb.
    # Egy „optimum" felirat itt a dolgozat fő megállapítását mondaná az ellenkezőjére.
    ax.annotate("val-loss minimum (1,0 epoch)", xy=lo, xytext=(lo[0] + 0.25, lo[1] - 0.16),
                fontsize=8.5, color=INK,
                arrowprops=dict(arrowstyle="->", color=INK2, lw=1.1))
    ax.set_xlabel("epoch", fontsize=9, color=INK2)
    ax.set_ylabel("veszteség", fontsize=9, color=INK2)
    ax.grid(color=GRID, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(labelsize=8.5, colors=INK2, length=0)
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2)
    ax.set_title("A LoRA tanulási görbéje (Qwen3.5-9B, Arany)", fontsize=11, color=INK, pad=10)
    fig.tight_layout()
    out = FIGS / "tanulas.png"
    fig.savefig(out, dpi=160, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  {out}")


def main() -> int:
    FIGS.mkdir(parents=True, exist_ok=True)
    style_path = RESULTS / "style_rows.json"
    if not style_path.exists():
        print("Nincs kiértékelés — futtasd előbb az evaluate.py-t")
        return 1
    style = json.loads(style_path.read_text(encoding="utf-8"))
    extract_path = RESULTS / "extraction_rows.json"
    extract = json.loads(extract_path.read_text(encoding="utf-8")) if extract_path.exists() else []

    print("Ábrák:")
    for key in sorted({r["source_key"] for r in style}):
        plot_form(style, key)
    for key in sorted({r["source_key"] for r in extract}):
        plot_extraction(extract, key)
    plot_training()
    return 0


if __name__ == "__main__":
    sys.exit(main())
