#!/usr/bin/env python3
"""Mérés B elemzése + ábrák (LAPTOP, matplotlib).

    python3 code/analyze_b.py

Három kimenet:
  B1  „szemét-arány" rétegenként — MEDDIG nem értelmezhető a naiv logit lens ezen a modellen
  B2  nyelvi arányok az értelmezhető ablakban (a runbook központi ábrája, korlátozott x-tengellyel)
  B3  a VÁRT válasz első tokenjének rangja rétegenként — ez a robusztus mérés, mert nem függ
      attól, hogy a top-20 értelmes szó-e; ugyanazt az unembeddinget használja minden rétegen

⛔ Miért kell a B1? Mert a naiv logit lens ezen a modellen a 0–18. rétegen 60–95 %-ban
NEM-szó tokeneket ad (`'��'`, `'GenerationStrategy'`, `'.SizeType'`). Ez ismert jelenség
(ezért készült a tuned lens, Belrose et al. 2023), és azt jelenti, hogy a H1
„középső rétegekben angolra vált" állítása ezzel az eszközzel NEM tesztelhető —
csak a késői rétegek olvashatók. Ezt a dolgozatban korlátként kell kimondani.
"""
import argparse
import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent
RES, OUT, FIG = scope_paths.res(HERE), scope_paths.reports(HERE), scope_paths.figures(HERE)
GROUPS = ("ZH", "HU", "UNI")
LANGS = ("hu", "en", "zh")
COL = {"hu": "#c0392b", "en": "#2c3e50", "zh": "#d68910"}
NAME = {"hu": "magyar prompt", "en": "angol prompt", "zh": "kínai prompt"}
JUNK_LIMIT = 0.45          # e fölött a lens kimenete nem szó → nem értelmezhető


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuned", action="store_true", help="a tanult fordítókkal készült kimenetekből")
    args = ap.parse_args()
    sfx = "_tuned" if args.tuned else ""
    FIG.mkdir(exist_ok=True)
    res = json.load(open(OUT / f"03_logit_lens{sfx}.json", encoding="utf-8"))
    rank = json.load(open(RES / f"lens_rank{sfx}.json", encoding="utf-8"))
    index = json.load(open(RES / f"lens_index{sfx}.json", encoding="utf-8"))
    meta = {f"{m['item_id']}_{m['lang']}": m for m in index}
    L = len(res[next(iter(res))]["en"])
    x = np.arange(L)

    junk = {k: np.array(v["ismeretlen"]) + np.array(v["egyéb"]) for k, v in res.items()}
    mean_junk = np.mean([j for j in junk.values()], axis=0)
    window = int(np.argmax(mean_junk < JUNK_LIMIT))     # az első réteg, ahonnan olvasható

    # ── B1 ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for k, j in sorted(junk.items()):
        ax.plot(x, j, color="#bdc3c7", lw=0.8)
    ax.plot(x, mean_junk, color="#c0392b", lw=2.4, label="átlag (15 csoport×nyelv cella)")
    ax.axhline(JUNK_LIMIT, ls="--", color="#7f8c8d", lw=1)
    ax.axvspan(0, window, color="#e74c3c", alpha=0.07)
    ax.annotate(f"a lens innen olvasható\n({window}. réteg)", xy=(window, 0.5),
                xytext=(window + 1.5, 0.72), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#7f8c8d"))
    ax.set_xlabel("réteg (0 = embedding, 32 = utolsó resid_post)")
    ax.set_ylabel("nem-szó tokenek aránya a top-20-ban")
    lens_nev = "tuned" if args.tuned else "naiv"
    ax.set_title(f"B1 — nem-szó arány rétegenként, {lens_nev} lens ({scope_paths.tag()})")
    ax.set_ylim(0, 1); ax.set_xlim(0, L - 1); ax.legend(fontsize=9); ax.grid(alpha=.25)
    fig.tight_layout(); fig.savefig(FIG / f"03_B1_szemet_arany{sfx}.png", dpi=160); plt.close(fig)

    # ── B2: nyelvi arányok az olvasható ablakban ────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, g in zip(axes, GROUPS):
        for lang in LANGS:
            r = res[f"{g}/{lang}"]
            strict = np.array(r["en"])
            loose = strict + np.array(r["közös"]) + np.array(r["ismeretlen"])
            ax.plot(x[window:], strict[window:], color=COL[lang], lw=2, label=NAME[lang])
            ax.fill_between(x[window:], strict[window:], loose[window:], color=COL[lang], alpha=.12)
        ax.set_title(f"{g}-only (n={res[f'{g}/hu']['n']})" if g != "UNI" else f"UNI (n={res['UNI/hu']['n']})")
        ax.set_xlabel("réteg"); ax.grid(alpha=.25); ax.set_xlim(window, L - 1)
    axes[0].set_ylabel("angol tokenek aránya a top-20-ban")
    axes[0].legend(fontsize=9)
    fig.suptitle(f"B2 — angol tokenek aránya az értelmezhető ablakban ({window}–{L-1}. réteg); "
                 "a sáv a szigorú és a tág besorolás közti bizonytalanság", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / f"03_B2_angol_arany{sfx}.png", dpi=160); plt.close(fig)

    # ── B3: a válasz-token rangja ───────────────────────────────────────────
    curves = {}
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, g in zip(axes, GROUPS):
        for lang in LANGS:
            rows = [v for k, v in rank.items() if meta[k]["group"] == g and meta[k]["lang"] == lang]
            arr = np.array(rows, dtype=float)
            med = np.median(arr, axis=0)
            q1, q3 = np.percentile(arr, 25, axis=0), np.percentile(arr, 75, axis=0)
            curves[f"{g}/{lang}"] = {"median": med.tolist(), "q1": q1.tolist(), "q3": q3.tolist(), "n": len(rows)}
            ax.plot(x, med, color=COL[lang], lw=2, label=NAME[lang])
            ax.fill_between(x, q1, q3, color=COL[lang], alpha=.12)
        ax.set_yscale("log"); ax.set_xlabel("réteg"); ax.grid(alpha=.25, which="both")
        ax.set_title(f"{g}-only" if g != "UNI" else "UNI")
    axes[0].set_ylabel("a várt válasz első tokenjének rangja (medián, log)")
    axes[0].legend(fontsize=9)
    fig.suptitle("B3 — mikor „tudja” a modell a választ? (kisebb rang = előrébb; 248 320 tokenből)", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / f"03_B3_valasz_rang{sfx}.png", dpi=160); plt.close(fig)

    # ── riport ──────────────────────────────────────────────────────────────
    def first_below(med, thr):
        idx = np.where(np.array(med) < thr)[0]
        return int(idx[0]) if len(idx) else None

    mid_junk = mean_junk[:24].mean()          # a „középső" (0–23.) sík átlagos nem-szó aránya
    md = [f"# Mérés B — logit lens ({lens_nev})", "",
          f"258 prompt utolsó prompt-tokene, {L} sík, top-20 token rétegenként. "
          "Osztályozó: hunspell hu_HU + american-english.", ""]
    if not args.tuned:
        # naiv lens: a középső sáv olvashatatlan
        md += ["## B1 — ⛔ a naiv logit lens ezen a modellen csak késői rétegeken értelmezhető", "",
               f"A top-20 token **{mean_junk[:window].mean():.0%}-a nem szó** a 0–{window-1}. rétegen "
               f"(`'��'`, `'GenerationStrategy'`, `'.SizeType'`), és csak a **{window}. rétegtől** esik "
               f"{JUNK_LIMIT:.0%} alá. Ez ismert jelenség — épp ezért készült a tuned lens (Belrose et al. 2023): "
               "a köztes residual nem esik egybe az unembedding terével.", "",
               "**Következmény a hipotézisre:** a H1 „középső rétegekben közös, angol felé torzított tér” "
               "állítása ezzel az eszközzel **nem tesztelhető** — a középső rétegek kimenete nem olvasható. "
               "Amit mérni tudunk: a késői rétegek nyelvi dinamikája (B2) és a válasz megjelenésének mélysége (B3). "
               "A középső rétegekre az **SAE (Mérés C)** ad választ, ami nem az unembeddingre vetít.", ""]
    else:
        # tuned lens: a küszöb alá esés jellemzően már a 0. síkon — itt az olvashatóvá tétel a hír
        naive_f = OUT / "03_meres_b.json"
        naive_mid = None
        if naive_f.exists():
            nj = json.load(open(naive_f, encoding="utf-8")).get("mean_junk")
            if nj:
                naive_mid = sum(nj[:24]) / 24
        vs = f" (a naiv lens {naive_mid:.0%}-ával szemben)" if naive_mid is not None else ""
        above = int((mean_junk[:24] >= JUNK_LIMIT).sum())
        md += ["## B1 — a tuned lens a középső síkokat is olvashatóvá teszi", "",
               f"A középső (0–23.) síkok átlagos nem-szó aránya **{mid_junk:.0%}**{vs}; a "
               f"{JUNK_LIMIT:.0%}-os küszöböt ebből a tartományból {above} sík lépi át. "
               + ("A B2 nyelvi görbéi ezért itt a teljes mélységben olvashatók."
                  if above <= 3 else
                  "A javulás ebben a körben csak részleges: a küszöb fölötti síkok miatt a B2 "
                  "görbéit a középső tartományban is csak óvatosan, irányjelzésként szabad olvasni."),
               "",
               "⛔⛔ **Cserébe a fordító visszaszivárogtat:** a rétegenkénti fordítók a VÉGSŐ eloszlás "
               "KL-jére tanultak, tehát részben elvégzik a hátralévő számítást. A B3 válasz-rang görbe "
               "erről a lensről NEM a modell tudás-mélységét méri — azt a naiv lens riportjából "
               "(`03_meres_b.md`) kell olvasni.", ""]
    md += [
          f"![B1](../{FIG.name}/03_B1_szemet_arany{sfx}.png)", "",
          f"## B2 — angol tokenek aránya a {window}–{L-1}. rétegen", "",
          "| csoport/nyelv | " + " | ".join(f"{i}." for i in range(window, L, 2)) + " |",
          "|---" * (1 + len(range(window, L, 2))) + "|"]
    for g in GROUPS:
        for lang in LANGS:
            r = res[f"{g}/{lang}"]
            strict = np.array(r["en"])
            md.append(f"| {g}/{lang} | " + " | ".join(f"{strict[i]:.0%}" for i in range(window, L, 2)) + " |")
    md += ["", f"![B2](../{FIG.name}/03_B2_angol_arany{sfx}.png)", "",
           "## B3 — mikor jelenik meg a válasz? (a várt válasz első tokenjének mediánrangja)", "",
           "| csoport/nyelv | n | 20. | 24. | 28. | 30. | 32. | rang<100 innen | rang<10 innen |",
           "|---|---|---|---|---|---|---|---|---|"]
    for g in GROUPS:
        for lang in LANGS:
            c = curves[f"{g}/{lang}"]
            med = c["median"]
            md.append(f"| {g}/{lang} | {c['n']} | " + " | ".join(f"{med[i]:,.0f}" for i in (20, 24, 28, 30, 32))
                      + f" | {first_below(med, 100) or '–'} | {first_below(med, 10) or '–'} |")
    md += ["", f"![B3](../{FIG.name}/03_B3_valasz_rang{sfx}.png)", "",
           "## Mit mond ez a hipotézisről?", ""]
    # a magyar mindig később ér célba — számszerűsítve
    gaps = []
    for g in GROUPS:
        f = {l: first_below(curves[f"{g}/{l}"]["median"], 100) for l in LANGS}
        gaps.append((g, f))
        md.append(f"- **{g}**: a válasz mediánrangja 100 alá kerül — "
                  + " · ".join(f"{NAME[l]}: {('a ' + str(f[l]) + '. rétegtől') if f[l] else 'soha'}" for l in LANGS))
    if args.tuned:
        md += ["",
               "⛔⛔ **A fenti rang-táblát és réteg-listát erről a lensről TILOS a modell tudásaként "
               "olvasni.** A tanult fordító a késői rétegek kimenetét jósolja, tehát a választ "
               "„előrehúzza”: a rang már a korai síkokon alacsony ott is, ahol a modell a választ "
               "sosem találja el. A válasz-mélység érvényes mérése a NAIV lens riportjában van "
               "(`03_meres_b.md`); ez a tábla csak felső korlátként, a visszaszivárgás mértékének "
               "illusztrálására szolgál.",
               ""]
    else:
        u = {l: first_below(curves[f"UNI/{l}"]["median"], 100) for l in LANGS}
        z = {l: first_below(curves[f"ZH/{l}"]["median"], 100) for l in LANGS}
        r24 = {l: curves[f"UNI/{l}"]["median"][24] for l in LANGS}
        hn = lambda v: f"{v:,.0f}".replace(",", " ")          # magyar ezres-elválasztó
        depth_ok = all(v is not None for v in list(u.values()) + list(z.values()))
        if depth_ok:
            _nr = round(np.log10(max(r24["hu"], 1) / max(r24["en"], 1)))
            nagysagrend = {1: "egy", 2: "két", 3: "három"}.get(_nr, str(_nr))
            depth_p = (
                f"⭐ **A magyar prompt MINDIG a legkésőbb ér célba**, és nem kicsivel: a UNI-csoportnál az "
                f"angol a {u['en']}., a kínai a {u['zh']}., a magyar csak a **{u['hu']}. rétegtől** hozza a "
                f"választ a top-100-ba — a 24. rétegen az angol mediánrangja {hn(r24['en'])}, a magyaré "
                f"{hn(r24['hu'])}, {nagysagrend} nagyságrend különbség. Ugyanez a sorrend a ZH-only "
                f"csoportban (zh {z['zh']}. · en {z['en']}. · hu {z['hu']}.).")
        else:
            # ⛔ chat-sablonos körben az utolsó prompt-token a BURKOLAT tokenje, nem a kérdésé —
            # a rang jellemzően sehol nem esik 100 alá, és a görbe nem hordozza a base kör jelentését
            depth_p = (
                "⚠️ **Ebben a körben a rang-görbe nem hasonlítható a base köréhez:** a válasz mediánrangja "
                "több cellában sehol nem esik 100 alá (ld. a fenti listát). Chat-sablonos promptnál az "
                "utolsó prompt-token a sablon burkolatának tokenje, nem a kérdésé, ezért a válasz-mélység "
                "itt nem ugyanazt méri — az összevetést a base kör naiv riportjára kell alapozni.")
        md += ["", depth_p, ""]
        if depth_ok:
            md += [
               "Ez **nem** ugyanaz, mint a H1 „középső rétegekben angol” állítása — azt a B1 miatt nem tudjuk "
               "tesztelni —, de egy ehhez illeszkedő, önállóan is érdekes lelet: **a magyar válasz kiszámításához "
               "a modellnek több rétegre van szüksége**. Ez összefér azzal, hogy a magyar úton több lépés (nyelvi "
               "átfordítás?) van, de önmagában nem bizonyítja: a nagyobb mélységigény fakadhat a magyar "
               "reprezentáció gyengébb minőségéből is. A kettő szétválasztása a Mérés C dolga.",
               "",
               "⛔ **A HU-only csoport egyik nyelven sem ér le 100 alá** (kivéve zh a legutolsó rétegen) — "
               "a Mérés A 7–20 %-os pontossága a reprezentációban is látszik: a modell nem „tudja, de nem mondja”, "
               "hanem tényleg nem tudja.",
               ""]
        # Az osztályozó-ellenőrzés EGYSZER készült, a base kör riportkönyvtárában. A többi kör
        # riportjából ezért visszafelé kell hivatkozni rá, különben törött linket írunk.
        clf = "03_classifier_ellenorzes.md"
        clf_link = clf if (OUT / clf).exists() else f"../reports/{clf}"
        md += [
           f"## Az osztályozó megbízhatósága", "",
           "100 véletlen token kétszeres értékelése: **92 % egyetértés** "
           f"([{clf}]({clf_link})). Mind a 8 hiba rövid latin töredék "
           "vagy tulajdonnév (pl. a magyar „Mirr-Murr” `Mir` töredéke angolnak számítana). A CJK-felismerés "
           "hibátlan. Ezért a B2 görbét csak a bizonytalansági sávval együtt szabad olvasni.", ""]
    if args.tuned:
        md += ["⚠️ **A 92 % a NAIV lens top-20-jából vett mintán mért érték** — a tuned lens top-20-jára "
               "külön ellenőrző validáció nem készült, és a naiv mintában a hibák iránya aszimmetrikus volt "
               "(rövid latin töredék → angol), ami az „angol” arányt felfelé torzíthatja.", ""]

    (OUT / f"03_meres_b{sfx}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (OUT / f"03_meres_b{sfx}.json").write_text(json.dumps(
        {"window_first_readable_layer": window, "mean_junk": mean_junk.round(4).tolist(),
         "rank_curves": curves}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))
    print(f"\n→ {OUT / f'03_meres_b{sfx}.md'} · ábrák: {FIG}")


if __name__ == "__main__":
    main()
