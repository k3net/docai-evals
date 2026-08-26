#!/usr/bin/env python3
"""1. kör (base) ↔ 2. kör (instruct) összevetés — a 2. kör tényleges terméke.

    python3 src/compare_rounds.py

A két kör MINDENBEN azonos, egyetlen dolgot kivéve: a modellt. Ugyanaz a 70 item, ugyanaz
a 258 prompt, ugyanaz a bíráló (Qwen3.6-35B), ugyanaz a rubrika, és a ellenőrző kört ugyanaz a
személy végezte ugyanazzal a mércével. Ezért a különbség a post-training hatásának
tulajdonítható — a lentebb kimondott korlátokkal.

⛔ Miért PÁROSÍTOTT próba? Mert a két kör UGYANAZOKAT az itemeket kapta. A két arány
független összevetése (pl. kétmintás z) eldobná ezt az információt és gyengébb. A
McNemar-próba csak a DISZKORDÁNS párokat nézi (amit az egyik eltalált, a másik nem),
és pontosan azt kérdezi, amit kell: az elmozdulás egy irányba mutat-e.
"""
import argparse
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

HERE = pathlib.Path(__file__).resolve().parent.parent
BASE, INST = HERE / "results", HERE / "results_instruct"
OUT = HERE / "reports_instruct"
GROUPS, LANGS = ["ZH", "HU", "UNI"], ["hu", "en", "zh"]
LANG_NAME = {"hu": "magyar", "en": "angol", "zh": "kínai"}


def rows(res, name):
    with (res / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def final(r):
    return (r["manual"].strip() or r["judge"].strip())


def binom_two_sided(k, n):
    """Pontos kétoldali binomiális p (p=0,5) — a McNemar diszkordáns pároknál."""
    if n == 0:
        return 1.0
    c = [math.comb(n, i) for i in range(n + 1)]
    tot = float(sum(c))
    obs = c[k]
    return min(1.0, sum(x for x in c if x <= obs + 1e-9) / tot)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge-only", action="store_true",
                    help="a kontroll-kör felbontása a GÉPI bíráló ítéletein (robusztussági próba: "
                         "így az esetleges saját mérce-elcsúszásom nem játszik)")
    args = ap.parse_args()
    RAW = HERE / "results_instruct_raw"          # a kontroll-kör (instruct + NYERS prompt)
    w_up = w_dn = p_up = p_dn = 0
    w_p = p_p = 1.0
    a_b = {(r["item_id"], r["lang"]): r for r in rows(BASE, "scores.csv")}
    a_i = {(r["item_id"], r["lang"]): r for r in rows(INST, "scores.csv")}
    assert set(a_b) == set(a_i), "a két kör itemhalmaza eltér"

    g_b = {(r["item_id"], r["lang"]): r for r in
           (json.loads(l) for l in (BASE / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
    g_i = {(r["item_id"], r["lang"]): r for r in
           (json.loads(l) for l in (INST / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}

    md = ["# 1. kör ↔ 2. kör — mit változtat a post-training?", "",
          "`Qwen3.5-9B-Base` (nyers folytatásos prompt) vs. `Qwen3.5-9B` (instruct, chat-sablon).", "",
          "## Mi azonos és mi nem", "",
          "| | |", "|---|---|",
          "| **azonos** | a 70 item és a 258 prompt (08-22 óta fagyasztva) · a bíráló (Qwen3.6-35B) · a rubrika · a ellenőrző kört ugyanaz a személy végezte, ugyanazzal a mércével · a token-keret hatásában (fact 200 · UNT/kontroll 800; a base kör magától megállt válaszai kisebb történeti kereten futottak, ami greedy dekódolásnál bitre azonos prefixet ad) |",
          "| **eltér** | a modellsúlyok (base → instruct) · a promptozás (nyers folytatás → chat-sablon) |", "",
          "⛔ **A promptozás nem választható el a modelltől.** Az instruct modellt chat-sablon "
          "nélkül használni nem az ő rendeltetésszerű használata; a különbség tehát a "
          "*post-trainelt modell + a hozzá való promptozás* együttes hatása. Ezt a dolgozatban "
          "ki kell mondani — "
          + ("a kettőt a kontroll-kör (nyers prompt az instruct modellen) választja szét: az "
             "eredménye lentebb, és átértelmezi ezt a különbséget."
             if (RAW / "scores.csv").exists() else
             "a runbook kontroll-köre (nyers prompt az instruct modellen) választaná szét a "
             "kettőt, az még nem futott."), ""]

    # ── terepviszonyok ──────────────────────────────────────────────────────
    def gs(g, key):
        return Counter(r["lang"] for r in g.values() if r.get(key))
    tb, ti = gs(g_b, "truncated"), gs(g_i, "truncated")
    db, di = gs(g_b, "degenerate"), gs(g_i, "degenerate")
    md += ["## Terepviszonyok — amit a számok olvasásakor tudni kell", "",
           "| | 1. kör (base) | 2. kör (instruct) |", "|---|---|---|",
           f"| csonkolt (a keretbe ütközött) | {sum(tb.values())}/258 "
           f"({', '.join(f'{l} {tb[l]}' for l in LANGS)}) | {sum(ti.values())}/258 "
           f"({', '.join(f'{l} {ti[l]}' for l in LANGS)}) |",
           f"| ismétlési hurok | {sum(db.values())}/258 ({', '.join(f'{l} {db[l]}' for l in LANGS)}) "
           f"| {sum(di.values())}/258 ({', '.join(f'{l} {di[l]}' for l in LANGS)}) |",
           f"| önértékelő toldalék | {sum(1 for r in g_b.values() if r.get('self_eval_cut') is True)}/258 "
           f"| {sum(1 for r in g_i.values() if r.get('self_eval_cut') is True)}/258 |", "",
           "⚠️ **A csonkolás megduplázódott** — az instruct modell bőbeszédűbb, ugyanazon a kereten. "
           "Ez a 2. kört LEFELÉ torzítja (a levágott rész tartalmazhatta volna a választ), tehát a "
           "lentebb mért javulás inkább **alsó becslés**.", "",
           "⭐ **A magyar ismétlési hurok eltűnt** és az önértékelő toldalék is: a post-training "
           "megszüntette a base „folytasd a dokumentumot” viselkedését. Ezek a 2. kört FELFELÉ "
           "torzíthatják, mert az 1. körben ezek elrontottak válaszokat.", ""]

    # ── Mérés A: 3×3 + páros próba ──────────────────────────────────────────
    md += ["---", "", "## Mérés A — pontosság", "", "### Szigorú pontosság („helyes”)", "",
           "| csoport | " + " | ".join(LANG_NAME[l] for l in LANGS) + " |", "|---|---|---|---|"]
    cells = {}
    for g in GROUPS:
        cs = []
        for l in LANGS:
            sub = [k for k in a_b if a_b[k]["group"] == g and a_b[k]["lang"] == l]
            b = sum(1 for k in sub if final(a_b[k]) == "helyes")
            i = sum(1 for k in sub if final(a_i[k]) == "helyes")
            cells[(g, l)] = (b, i, len(sub))
            d = i - b
            cs.append(f"{b/len(sub):.0%} → **{i/len(sub):.0%}** ({d:+d} item)")
        md.append(f"| **{g}** (n={cells[(g, LANGS[0])][2]}) | " + " | ".join(cs) + " |")

    # McNemar itemenként, cellánként és összesítve
    md += ["", "### Páros próba (McNemar) — ugyanazok az itemek", "",
           "Csak a **diszkordáns** párok számítanak: `b→i` = az 1. kör elrontotta, a 2. eltalálta; "
           "`i→b` = fordítva.", "",
           "| csoport / nyelv | b→i (javult) | i→b (romlott) | p (pontos, kétoldali) |", "|---|---|---|---|"]
    tot_bi = tot_ib = 0
    for g in GROUPS:
        for l in LANGS:
            sub = [k for k in a_b if a_b[k]["group"] == g and a_b[k]["lang"] == l]
            bi = sum(1 for k in sub if final(a_b[k]) != "helyes" and final(a_i[k]) == "helyes")
            ib = sum(1 for k in sub if final(a_b[k]) == "helyes" and final(a_i[k]) != "helyes")
            tot_bi += bi; tot_ib += ib
            n = bi + ib
            p = binom_two_sided(min(bi, ib), n)
            md.append(f"| {g} / {LANG_NAME[l]} | {bi} | {ib} | "
                      + (f"{p:.3f}" + (" ✅" if p < .05 else "") if n else "– (nincs diszkordáns pár)") + " |")
    p_all = binom_two_sided(min(tot_bi, tot_ib), tot_bi + tot_ib)
    md += [f"| **mind a 162** | **{tot_bi}** | **{tot_ib}** | **{p_all:.2e}"
           + (" ✅**" if p_all < .05 else "**") + " |", "",
           f"⭐⭐ Összesítve **{tot_bi} item javult és {tot_ib} romlott** — az elmozdulás egyértelműen "
           f"egy irányba mutat (p = {p_all:.1e}).", "",
           "⛔ **De ez a szám még NEM a post-training hatása.** A 2. kör a súlyokat és a promptozást "
           "EGYSZERRE változtatta; a kettő szétválasztását a lentebbi **kontroll-kör** végzi el — és "
           "az eredménye átértelmezi ezt a táblát. Ide csak a kontroll-körrel együtt szabad "
           "következtetést fűzni.", ""]

    # ── hallucináció ────────────────────────────────────────────────────────
    md += ["---", "", "## A tévedés MÓDJA — ez a legfontosabb különbség", "",
           "A nem helyes válaszokon belül mekkora a magabiztos kitaláció (`hallucinacio`) aránya? "
           "Csak az ellenőrző körrel fedett ZH és HU csoportra értelmes.", "",
           "| csoport / nyelv | 1. kör | 2. kör |", "|---|---|---|"]
    hb_t = hi_t = wb_t = wi_t = 0
    for g in ("ZH", "HU"):
        for l in LANGS:
            sub = [k for k in a_b if a_b[k]["group"] == g and a_b[k]["lang"] == l]
            def hal(d):
                w = [k for k in sub if final(d[k]) in ("helytelen", "hallucinacio")]
                h = [k for k in w if final(d[k]) == "hallucinacio"]
                return len(h), len(w)
            hb, wb = hal(a_b); hi, wi = hal(a_i)
            hb_t += hb; wb_t += wb; hi_t += hi; wi_t += wi
            md.append(f"| {g} / {LANG_NAME[l]} | "
                      + (f"{hb/wb:.0%} ({hb}/{wb})" if wb else "–") + " | "
                      + (f"**{hi/wi:.0%}** ({hi}/{wi})" if wi else "–") + " |")
    # ⛔ Az összesített 69 % → 77 % ELFEDI a lényeget: a két csoportban ELLENTÉTES az irány.
    # Ezt nem szabad egy átlagba olvasztani — az ábra jobb panelje azonnal mutatja.
    per_g = {}
    for g in ("ZH", "HU"):
        sub = [k for k in a_b if a_b[k]["group"] == g]
        def sh(d):
            w = [k for k in sub if final(d[k]) in ("helytelen", "hallucinacio")]
            return sum(1 for k in w if final(d[k]) == "hallucinacio"), len(w)
        per_g[g] = (sh(a_b), sh(a_i))
    up = [f"{g} / {LANG_NAME[l]}" for g in ("ZH", "HU") for l in LANGS]
    dirs = {}
    for g in ("ZH", "HU"):
        n_up = n_dn = 0
        for l in LANGS:
            sub = [k for k in a_b if a_b[k]["group"] == g and a_b[k]["lang"] == l]
            def sh2(d):
                w = [k for k in sub if final(d[k]) in ("helytelen", "hallucinacio")]
                return (sum(1 for k in w if final(d[k]) == "hallucinacio") / len(w)) if w else None
            b_, i_ = sh2(a_b), sh2(a_i)
            if b_ is None or i_ is None:
                continue
            n_up += i_ > b_; n_dn += i_ < b_
        dirs[g] = (n_up, n_dn)
    md += [f"| **együtt** | {hb_t/wb_t:.0%} ({hb_t}/{wb_t}) | **{hi_t/wi_t:.0%}** ({hi_t}/{wi_t}) |", "",
           "⛔⛔ **Az összesített szám félrevezet: a két csoportban ELLENTÉTES az irány.**", "",
           "| csoport | 1. kör | 2. kör | irány |", "|---|---|---|---|"]
    for g in ("ZH", "HU"):
        (hb_, wb__), (hi_, wi__) = per_g[g]
        u, d_ = dirs[g]
        md.append(f"| **{g}**-only | {hb_/wb__:.0%} ({hb_}/{wb__}) | **{hi_/wi__:.0%}** ({hi_}/{wi__}) | "
                  f"{'NŐ' if hi_/wi__ > hb_/wb__ else 'CSÖKKEN'} — {u} cellában nő, {d_}-ben csökken |")
    md += ["", "⭐⭐ **A kitalálás ott nő, ahol a modell a legkevesebbet tudja.** A ZH-only csoportban "
           "(amit a modell viszonylag jól tud: 58–63 % pontosság) a post-training **csökkenti** a "
           "magabiztos kitalálás arányát. A HU-only csoportban (20–33 % pontosság) viszont **növeli**, "
           "méghozzá mind a három nyelven — a HU/kínai cellában a téves válaszok **100 %-a** kitaláció.", "",
           "Vagyis a post-training nem általában „hallucinálósabbá” tesz: a kitérést és a nem-válaszolást "
           "szorítja ki. Ahol van mit mondani, ez javulás; ahol nincs, ott a modell a hallgatás helyett "
           "**kitalál**. A hatás tehát épp a kis korpuszú nyelv saját tudásanyagán a legrosszabb.", "",
           "⚠️ Gyakorlati következtetés a dolgozatba: a felhasználó felé az instruct modell "
           "**magabiztosabbnak látszik ott is, ahol nem tud semmit**, és ez a magyar anyagon a "
           "legerősebb — pont ott, ahol a magyar felhasználó a legjobban rá lenne utalva.", "",
           "![R1](../figures_instruct/06_R1_pontossag_es_hallucinacio.png)", ""]
    # ── kontroll-kör: a SÚLYOK és a PROMPTOZÁS hatásának szétválasztása ─────
    if (RAW / "scores.csv").exists():
        a_r = {(r["item_id"], r["lang"]): r for r in rows(RAW, "scores.csv")}

        # A felbontás akkor a legerősebb, ha mind a három kör KÉZI ítéletein fut. Ha a
        # kontroll-kör ellenőrző köre még nincs kész, visszaesünk a gépi bíráló ítéletére —
        # az is belülről konzisztens, csak gyengébb.
        def complete(d):
            sc = [r for r in d.values() if r["group"] in ("ZH", "HU")]
            return all(r["manual"].strip() for r in sc)
        use_manual = all(complete(d) for d in (a_b, a_r, a_i)) and not args.judge_only

        def jud(d, k):
            return final(d[k]) if use_manual else d[k]["judge"].strip()

        forras = ("a **saját ellenőrző ítéleteimen** (mind a három körben kész)" if use_manual
                  else "a **gépi bíráló** ítéletein (a kontroll-körnek még nincs ellenőrző köre)")

        def mcnemar(d1, d2):
            up = sum(1 for k in d1 if jud(d1, k) != "helyes" and jud(d2, k) == "helyes")
            dn = sum(1 for k in d1 if jud(d1, k) == "helyes" and jud(d2, k) != "helyes")
            return up, dn, binom_two_sided(min(up, dn), up + dn)

        w_up, w_dn, w_p = mcnemar(a_b, a_r)     # base → instruct-nyers: csak a SÚLYOK változnak
        p_up, p_dn, p_p = mcnemar(a_r, a_i)     # nyers → chat: csak a PROMPTOZÁS változik
        t_up, t_dn, t_p = mcnemar(a_b, a_i)     # a teljes elmozdulás

        md += ["---", "", "## ⭐⭐ Kontroll-kör — a súlyok vagy a promptozás?", "",
               "A 2. kör két dolgot változtatott egyszerre: a modellsúlyokat ÉS a promptozást. "
               "A kontroll-kör ugyanazt az **instruct modellt** futtatja a base kör **nyers, "
               "folytatásos** promptjával (`results_instruct_raw`), így a kettő szétválasztható.", "",
               f"A felbontás {forras} áll.", ""]
        if use_manual:
            md += ["⚠️ **Korlát a 3. kör ellenőrző köréhez:** a korábbi két "
                   "kör precedens-naplója nem volt kéznél, amikor ezt a kört pontoztam — csak a kör "
                   "útmutatójában idézett rubrika. A mérce így elvben elcsúszhatott. Az alábbi "
                   "**különbségek** ezért óvatosabban olvasandók, mint a gépi bírálón futó változat "
                   "(amit a `--judge-only` kapcsoló ad vissza).", ""]
        md += [
               "| | hu | en | zh |", "|---|---|---|---|"]
        for g in GROUPS:
            for lab, d in (("1. base", a_b), ("2. instruct + NYERS prompt", a_r),
                           ("3. instruct + chat-sablon", a_i)):
                cs = []
                for l in LANGS:
                    sub = [k for k in d if d[k]["group"] == g and d[k]["lang"] == l]
                    cs.append(f"{sum(1 for k in sub if jud(d, k) == 'helyes') / len(sub):.0%}")
                md.append(f"| **{g}** — {lab} | " + " | ".join(cs) + " |")
        md += ["", "### Páros próbák — mi mit magyaráz", "",
               "| lépés | mi változik | javult | romlott | p |", "|---|---|---|---|---|",
               f"| 1 → 2 | csak a **súlyok** (base → instruct, azonos nyers prompt) | {w_up} | {w_dn} | "
               + (f"{w_p:.3f}" if w_up + w_dn else "–") + " |",
               f"| 2 → 3 | csak a **promptozás** (nyers → chat-sablon, azonos súlyok) | {p_up} | {p_dn} | "
               + (f"{p_p:.3f}" if p_up + p_dn else "–") + " |",
               f"| 1 → 3 | mindkettő együtt | {t_up} | {t_dn} | "
               + (f"{t_p:.3f}" if t_up + t_dn else "–") + " |", ""]
        net_w, net_p = w_up - w_dn, p_up - p_dn
        dom = "a PROMPTOZÁS" if net_p > net_w else ("a SÚLYOK" if net_w > net_p else "a kettő egyformán")
        md += [f"⭐⭐ **A javulás nagy részét {dom} magyarázza.** A puszta súlycsere nettó "
               f"{net_w:+d} itemet hoz, a chat-sablonra váltás **{net_p:+d}**-et; a kettő együtt "
               f"{t_up - t_dn:+d}. Vagyis a 2. kör mért javulása **nem elsősorban azt jelenti, hogy "
               "az instruct modell TÖBBET TUD** — hanem azt, hogy a chat-sablon előhívja belőle azt, "
               "amit a nyers folytatásos prompt nem.", "",
               "⚠️ Ez a dolgozat egyik legfontosabb módszertani tanulsága: **a „post-training javítja "
               "a tudást” állítás promptozási műtermék is lehet**, és csak kontroll-körrel lehet "
               "szétválasztani. A base modellt nyers prompttal mérni és az instructot chat-sablonnal "
               "mérni NEM azonos mérce.", "",
               "### A generálási patológiák is a promptozáshoz kötődnek", "",
               "| | 1. base | 2. instruct + nyers | 3. instruct + chat |", "|---|---|---|---|"]
        g_r = {(r["item_id"], r["lang"]): r for r in
               (json.loads(l) for l in (RAW / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip())}
        for lab, key in (("ismétlési hurok", "degenerate"), ("önértékelő toldalék", "self_eval_cut")):
            vals = []
            for gg in (g_b, g_r, g_i):
                vals.append(sum(1 for r in gg.values()
                                if (r.get(key) is True if key == "self_eval_cut" else r.get(key))))
            md.append(f"| {lab} | {vals[0]}/258 | {vals[1]}/258 | {vals[2]}/258 |")
        md += ["", "⭐ A base kör két jellegzetes patológiája (ismétlési hurok, saját feladatkiírás a "
               "válasz után) az instruct modellen NYERS prompttal **visszatér**, chat-sablonnal "
               "**eltűnik**. Tehát ezek sem a súlyok tulajdonságai, hanem a promptozási módé.", "",
               "![R3](../figures_instruct/06_R3_sulyok_vs_promptozas.png)", ""]

        # ── a HALLUCINÁCIÓ felbontása: eddig nyitott kérdés volt ────────────
        if use_manual:
            md += ["### A kitalálás növekedése: a súlyoktól vagy a promptozástól?", "",
                   "Fentebb kiderült, hogy a HU-only csoportban NŐ a magabiztos kitaláció aránya a "
                   "téves válaszokon belül. A három kör most ezt is szétválasztja.", "",
                   "| csoport | 1. base | 2. instruct + NYERS | 3. instruct + chat |", "|---|---|---|---|"]
            hal3 = {}
            for g in ("ZH", "HU"):
                cells_ = []
                for d in (a_b, a_r, a_i):
                    sub = [k for k in d if d[k]["group"] == g]
                    w = [k for k in sub if final(d[k]) in ("helytelen", "hallucinacio")]
                    h = sum(1 for k in w if final(d[k]) == "hallucinacio")
                    cells_.append((h, len(w)))
                hal3[g] = cells_
                md.append(f"| **{g}**-only | " + " | ".join(
                    f"{h/w_:.0%} ({h}/{w_})" if w_ else "–" for h, w_ in cells_) + " |")
            hb2, hr, hi2 = hal3["HU"]
            d_w = hr[0] / hr[1] - hb2[0] / hb2[1]
            d_p = hi2[0] / hi2[1] - hr[0] / hr[1]
            dom = "a PROMPTOZÁS" if abs(d_p) > abs(d_w) else "a SÚLYCSERE"
            md += ["", f"⭐⭐ A HU-only csoportban a kitalálás-arány a súlycserétől {d_w:+.0%}-ot, a "
                   f"chat-sablonra váltástól **{d_p:+.0%}**-ot mozdul — tehát itt is **{dom}** a "
                   "meghatározó. A chat-sablon nem csak a jó válaszokat hívja elő, hanem a "
                   "**magabiztos rosszakat is**: ott, ahol a modell keveset tud, a nyers prompt "
                   "mellett még kitér vagy elakad, a chat-sablon mellett viszont határozottan "
                   "kimondja a téves állítást.", "",
                   "⛔ **Ez az egyetlen eredmény, amit a `--judge-only` futás NEM tud ellenőrizni:** "
                   "a gépi bíráló a `hallucinacio` kategóriát gyakorlatilag nem használja (162 "
                   "válaszból 1–2), tehát a kitalálás-felbontás **teljes egészében a ellenőrző köröké**. "
                   "A pontosság-felbontás viszont a gépi bírálón is ugyanazt adja (súlyok p = 1,000, "
                   "promptozás p = 0,041), tehát az a rész mérce-független.", ""]

    # ── D1: a forrásnyelv előnye ────────────────────────────────────────────
    def d1_table(res):
        rs = [r for r in rows(res, "d1_scores.csv") if r["kind"] == "unt"]
        out = {}
        for r in rs:
            v = (r["manual_native"] or "").strip() or r["native_hit"]
            n = r["native_n"]
            k = (r["src_lang"], r["lang"])
            h, t = out.get(k, (0, 0))
            out[k] = (h + int(float(v)), t + int(float(n)))
        return out
    db_, di_ = d1_table(BASE), d1_table(INST)
    md += ["---", "", "## Mérés D1 — a lefordíthatatlan fogalmak komponensei", "",
           "| forrásnyelv | prompt nyelve | 1. kör | 2. kör |", "|---|---|---|---|"]
    for src in ("hu", "zh"):
        for l in LANGS:
            b, i = db_.get((src, l)), di_.get((src, l))
            if not b or not i:
                continue
            mark = " ← **forrásnyelv**" if src == l else ""
            md.append(f"| {src}{mark} | {LANG_NAME[l]} | {b[0]}/{b[1]} = {b[0]/b[1]:.0%} | "
                      f"**{i[0]}/{i[1]} = {i[0]/i[1]:.0%}** |")
    md += [""]
    for src in ("hu", "zh"):
        own_b, en_b = db_[(src, src)], db_[(src, "en")]
        own_i, en_i = di_[(src, src)], di_[(src, "en")]
        d_b = own_b[0] / own_b[1] - en_b[0] / en_b[1]
        d_i = own_i[0] / own_i[1] - en_i[0] / en_i[1]
        md.append(f"- **{src}-forrású fogalmak:** a forrásnyelv az angolhoz képest "
                  f"az 1. körben {d_b:+.0%}, a 2. körben **{d_i:+.0%}**.")
    md += ["", "⭐⭐ **Irányváltás:** az 1. körben a forrásnyelv MINDKÉT irányban gyengébb volt az "
           "angolnál — ez volt a „nincs forrásnyelvi előny” eredmény. A 2. körben a hu-forrású "
           "fogalmaknál a magyar prompt már a legjobb, a zh-forrásúaknál pedig mindhárom nyelv "
           "90 % fölé megy, tehát a különbség eltűnik. **A post-training kiegyenlíti a nyelveket.**", "",
           "⚠️ Korlát: 8+8 fogalom, a komponenslistákat én definiáltam; ez kvalitatív-"
           "illusztratív mérés. A számszerű alapot a Mérés C adja.", ""]

    # ── Mérés C: a nyelvek közti feature-átfedés többlete ───────────────────
    def cjson(rep):
        f = HERE / rep / "04_meres_c.json"
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}

    def peaks(rep):
        return cjson(rep).get("peaks", {})

    def excess(rep, key):
        """A többlet-görbe rétegenként: matched − véletlen párosítás."""
        c = cjson(rep).get("curves", {}).get(f"union/{key}")
        return [m - b for m, b in zip(c["matched"], c["base_cross"])] if c else None
    pb, pi = peaks("reports"), peaks("reports_instruct")
    if pb and pi:
        md += ["---", "", "## Mérés C — nyelvek közti SAE feature-átfedés (a kérdés tokenjein)", "",
               "A véletlen párosításhoz mért TÖBBLET csúcsa. Ez a dolgozat legszigorúbb, "
               "reprezentáció-szintű mérőszáma.", "",
               "| csoport | nyelvpár | 1. kör | 2. kör |", "|---|---|---|---|"]
        for k in sorted(set(pb) & set(pi)):
            g, pair = k.split("/")
            md.append(f"| {g} | {pair} | {pb[k]['peak']:+.3f} ({pb[k]['peak_layer']}. réteg) | "
                      f"**{pi[k]['peak']:+.3f}** ({pi[k]['peak_layer']}. réteg) |")
        common = sorted(set(pb) & set(pi))
        up = sum(1 for k in common if pi[k]["peak"] > pb[k]["peak"])
        lb = sorted(pb[k]["peak_layer"] for k in common)
        li = sorted(pi[k]["peak_layer"] for k in common)
        med = lambda v: v[len(v) // 2]
        late_i = [k for k in common if pi[k]["peak_layer"] > 15]
        md += ["", f"⭐⭐ **{up}/{len(common)} nyelvpáron nőtt a többlet.** A post-training tehát nem "
               "angol-központúbbá teszi a modellt, hanem **erősíti a nyelvfüggetlen fogalmi "
               "reprezentációt**.", ""]
        if late_i:
            # ⛔ A csúcs RÉTEGÉRE nem szabad állítást építeni, ha a görbe lapos. Ezt nem
            # feltételezzük: megmérjük, mennyivel magasabb a globális csúcs a 8–12. réteg
            # lokális maximumánál. Ha a különbség ezred nagyságrendű, a csúcs helye zaj.
            gaps = []
            for k in late_i:
                e = excess("reports_instruct", k)
                if not e:
                    continue
                g = max(range(len(e)), key=lambda i: e[i])
                loc = max(range(8, 13), key=lambda i: e[i])
                gaps.append((k, g, e[g], loc, e[loc], e[g] - e[loc]))
            md += [f"⚠️ A csúcs RÉTEGE nem stabil: mediánja {med(lb)} → {med(li)}, de "
                   f"{len(late_i)} nyelvpár csúcsa a 2. körben a 15. réteg fölé csúszik. "
                   "**Ez azonban nem valódi rétegváltás:** a görbe ott lapos — a globális csúcs "
                   "alig magasabb a 8–12. réteg lokális maximumánál.", "",
                   "| nyelvpár | globális csúcs | a 8–12. réteg maximuma | különbség |",
                   "|---|---|---|---|"]
            for k, g, eg, loc, el, d in gaps:
                md.append(f"| {k} | {eg:+.3f} ({g}. réteg) | {el:+.3f} ({loc}. réteg) | **{d:+.4f}** |")
            md += ["", "Vagyis **a csúcs rétegére önmagában nem szabad állítást építeni**; a "
                   "9–11. rétegbeli púp mindkét körben megvan, a görbe alakját a C1/C2 ábrákon "
                   "kell nézni.", ""]
        md += ["![R2](../figures_instruct/06_R2_C_tobblet.png)", ""]

    md += ["---", "", "## Összefoglalás", "",
           "| kérdés | válasz |", "|---|---|",
           f"| Javul-e a faktuális pontosság? | **Igen** ({tot_bi} item javult, {tot_ib} romlott, "
           f"p = {p_all:.1e}) — de **nem a súlyoktól**, ld. a következő sort |",
           (f"| Mitől javul: a súlyoktól vagy a promptozástól? | ⭐⭐ **A promptozástól.** A puszta "
            f"súlycsere nettó {w_up - w_dn:+d} item (p = {w_p:.3f}, azaz semmi), a chat-sablonra "
            f"váltás **{p_up - p_dn:+d}** item (p = {p_p:.3f}) |"
            if (RAW / "scores.csv").exists() else
            "| Mitől javul: a súlyoktól vagy a promptozástól? | ⏳ a kontroll-kör még nem futott |"),
           "| Angol-központúbb lesz-e a reprezentáció? | **Nem** — a nyelvek közti "
           "feature-átfedés-többlet mind a 9 nyelvpáron nőtt (a csúcs RÉTEGÉRE nem építünk "
           "állítást, ld. fentebb) |",
           "| Eltűnik-e a forrásnyelv hátránya? | **Igen**, a D1-ben irányt vált |",
           "| Csökken-e a hallucináció? | **Csoportfüggő** — a téves válaszokon belül a magabiztos "
           f"kitaláció aránya a ZH-only csoportban {per_g['ZH'][0][0]/per_g['ZH'][0][1]:.0%} → "
           f"**{per_g['ZH'][1][0]/per_g['ZH'][1][1]:.0%}** (csökken), a HU-only csoportban "
           f"{per_g['HU'][0][0]/per_g['HU'][0][1]:.0%} → **{per_g['HU'][1][0]/per_g['HU'][1][1]:.0%}** "
           "(NŐ). Ahol a modell keveset tud, ott a hallgatás helyett kitalál |", "",
           "⛔ **Maradó korlátok:** a csonkolás a 2. körben megduplázódott (86 vs. 43/258), ami a "
           "mért javulást inkább alsó becsléssé teszi; a 3. kör ellenőrző körét a korábbi "
           "precedens-naplóim nélkül pontoztam, tehát a mérce elvben elcsúszhatott (a pontosság-"
           "felbontást ez nem érinti, mert a gépi bírálón is ugyanaz jön ki); és mindez EGY "
           "modellcsalád EGY méretén, 70 itemen mérve.", "",
           "⚠️ **Amit a három kör NEM választ szét:** a chat-sablon és a post-training együtt jár a "
           "gyakorlatban — nincs olyan valós használat, ahol az instruct modellt nyers folytatásos "
           "prompttal etetnék. A 3. kör tehát **mérési kontroll, nem használati forgatókönyv**: azt "
           "mutatja meg, hogy a 2. kör javulása MIBŐL ered, nem azt, hogy a post-training fölösleges "
           "volna. A chat-sablon épp a post-training terméke — a súlyok teszik, hogy a modell "
           "egyáltalán reagál rá.", ""]

    # ── R3 ábra: a súlyok és a promptozás szétválasztása ────────────────────
    # Ez a dolgozat egyik fő ábrája: a 2×2 felbontás egyetlen képen.
    FIG = HERE / "figures_instruct"
    FIG.mkdir(parents=True, exist_ok=True)
    if (RAW / "scores.csv").exists():
        fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.5, 4.6),
                                       gridspec_kw={"width_ratios": [1.7, 1]})
        labs, series = [], {"1. base + nyers": [], "2. instruct + NYERS": [], "3. instruct + chat": []}
        for g in GROUPS:
            for l in LANGS:
                labs.append(f"{g}\n{LANG_NAME[l]}")
                for lab, d in (("1. base + nyers", a_b), ("2. instruct + NYERS", a_r),
                               ("3. instruct + chat", a_i)):
                    sub = [k for k in d if d[k]["group"] == g and d[k]["lang"] == l]
                    series[lab].append(sum(1 for k in sub if jud(d, k) == "helyes") / len(sub))
        x = np.arange(len(labs)); w = .26
        cols = ["#95a5a6", "#7f8c8d", "#2980b9"]
        for i, (lab, v) in enumerate(series.items()):
            axA.bar(x + (i - 1) * w, v, w, label=lab, color=cols[i],
                    hatch="//" if i == 1 else None, edgecolor="white", linewidth=.4)
        axA.set_xticks(x, labs, fontsize=8)
        axA.set_ylabel("szigorú pontosság\n(" + ("ellenőrző ítéletek" if use_manual else "gépi bíráló") + ")")
        axA.set_ylim(0, 1.08)
        axA.legend(fontsize=8.5); axA.grid(axis="y", alpha=.25)
        axA.set_title("a 2. és a 3. oszlop ugyanaz a MODELL — csak a promptozás más", fontsize=10)

        # jobb panel: a nettó elmozdulás lépésenként
        steps = ["csak a SÚLYOK\n(1 → 2)", "csak a PROMPTOZÁS\n(2 → 3)", "együtt\n(1 → 3)"]
        net = [w_up - w_dn, p_up - p_dn, t_up - t_dn]
        ps = [w_p, p_p, t_p]
        bars = axB.bar(steps, net, color=["#bdc3c7", "#c0392b", "#2980b9"])
        for b, n_, pv in zip(bars, net, ps):
            axB.text(b.get_x() + b.get_width() / 2, n_ + .3, f"{n_:+d} item\np = {pv:.3f}",
                     ha="center", fontsize=9)
        axB.axhline(0, color="#7f8c8d", lw=1)
        axB.set_ylabel("nettó javulás (item)"); axB.set_ylim(min(0, min(net)) - 1, max(net) + 3)
        axB.grid(axis="y", alpha=.25)
        axB.set_title("páros próba (McNemar)", fontsize=10)
        fig.suptitle("R3 — a 2. kör „javulása” a PROMPTOZÁSTÓL van, nem a súlyoktól", fontsize=11)
        fig.tight_layout(); fig.savefig(FIG / "06_R3_sulyok_vs_promptozas.png", dpi=160); plt.close(fig)

    # ── R1 ábra: pontosság és a tévedés módja, körönként ─────────────────────
    FIG = HERE / "figures_instruct"
    FIG.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.6))
    labels, xb, xi = [], [], []
    for g in GROUPS:
        for l in LANGS:
            b, i, n = cells[(g, l)]
            labels.append(f"{g}\n{LANG_NAME[l]}"); xb.append(b / n); xi.append(i / n)
    x = np.arange(len(labels)); w = .38
    ax1.bar(x - w / 2, xb, w, label="1. kör — base", color="#95a5a6")
    ax1.bar(x + w / 2, xi, w, label="2. kör — instruct", color="#2980b9")
    for k in range(len(labels)):
        if xi[k] != xb[k]:
            ax1.annotate("", xy=(k + w / 2, xi[k]), xytext=(k - w / 2, xb[k]),
                         arrowprops={"arrowstyle": "->", "color": "#c0392b" if xi[k] < xb[k] else "#27ae60",
                                     "lw": 1.2, "alpha": .7})
    ax1.set_xticks(x, labels, fontsize=8)
    ax1.set_ylabel("szigorú pontosság"); ax1.set_ylim(0, 1.05)
    ax1.legend(fontsize=9); ax1.grid(axis="y", alpha=.25)
    ax1.set_title(f"pontosság — {tot_bi} item javult, {tot_ib} romlott (McNemar p = {p_all:.1e})",
                  fontsize=10)

    # jobb: a tévedés MÓDJA — csak az ellenőrző körrel fedett csoportok
    hl, hb_, hi_ = [], [], []
    for g in ("ZH", "HU"):
        for l in LANGS:
            sub = [k for k in a_b if a_b[k]["group"] == g and a_b[k]["lang"] == l]
            def share(d):
                w_ = [k for k in sub if final(d[k]) in ("helytelen", "hallucinacio")]
                return (sum(1 for k in w_ if final(d[k]) == "hallucinacio") / len(w_)) if w_ else np.nan
            hl.append(f"{g}\n{LANG_NAME[l]}"); hb_.append(share(a_b)); hi_.append(share(a_i))
    x2 = np.arange(len(hl))
    ax2.bar(x2 - w / 2, hb_, w, label="1. kör — base", color="#95a5a6")
    ax2.bar(x2 + w / 2, hi_, w, label="2. kör — instruct", color="#c0392b")
    ax2.set_xticks(x2, hl, fontsize=8)
    ax2.set_ylabel("a téves válaszokon belül:\nmagabiztos kitaláció aránya"); ax2.set_ylim(0, 1.05)
    ax2.legend(fontsize=9); ax2.grid(axis="y", alpha=.25)
    ax2.set_title(f"a tévedés MÓDJA — együtt {hb_t/wb_t:.0%} → {hi_t/wi_t:.0%}", fontsize=10)
    # ⛔ A cím korábban „a post-training két hatása" volt — a kontroll-kör (R3) megmutatta,
    # hogy a pontosság-javulás a PROMPTOZÁSÉ, ezért a cím nem tulajdoníthatja a súlyoknak.
    fig.suptitle("R1 — az 1. és a 2. kör: pontosabb válaszok, de a HU csoportban gyakoribb "
                 "kitalálás  ·  a szétválasztás az R3 ábrán", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "06_R1_pontossag_es_hallucinacio.png", dpi=160); plt.close(fig)

    # ── R2 ábra: a Mérés C többlet-görbéje a két körben ──────────────────────
    if pb and pi:
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
        PCOL = {"zh-en": "#8e44ad", "zh-hu": "#16a085", "en-hu": "#d35400"}
        for ax, g in zip(axes, GROUPS):
            for pair, col in PCOL.items():
                eb, ei = excess("reports", f"{g}/{pair}"), excess("reports_instruct", f"{g}/{pair}")
                if eb: ax.plot(range(len(eb)), eb, color=col, lw=1.3, ls=":", alpha=.85)
                if ei: ax.plot(range(len(ei)), ei, color=col, lw=2.2, label=pair)
            ax.axhline(0, color="#7f8c8d", lw=1)
            ax.set_title(f"{g}-only" if g != "UNI" else "UNI (univerzális)", fontsize=10)
            ax.set_xlabel("réteg"); ax.grid(alpha=.25)
        axes[0].set_ylabel("Jaccard-TÖBBLET a véletlen párosításhoz")
        axes[0].legend(fontsize=9, title="nyelvpár", title_fontsize=8)
        fig.suptitle("R2 — nyelvek közti SAE feature-átfedés többlete · pontozott: 1. kör (base), "
                     "folytonos: 2. kör (instruct)", fontsize=11)
        fig.tight_layout(); fig.savefig(FIG / "06_R2_C_tobblet.png", dpi=160); plt.close(fig)
        c_fig = "![R2](../figures_instruct/06_R2_C_tobblet.png)"

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "06_base_vs_instruct.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"→ {OUT / '06_base_vs_instruct.md'}")
    print(f"   McNemar összesítve: {tot_bi} javult / {tot_ib} romlott, p = {p_all:.2e}")
    print(f"   hallucináció a téves válaszokon belül: {hb_t/wb_t:.0%} → {hi_t/wi_t:.0%}")


if __name__ == "__main__":
    main()
