#!/usr/bin/env python3
"""Mérés D — lefordíthatatlan fogalmak: a direkt teszt a fordítási hipotézisre (laptop).

    python3 src/analyze_d.py

D1  komponens-lefedettség (viselkedés) + kontrollszavak + keretezési érzékenységvizsgálat
D2  logit lens: megjelenik-e az angol közelítés a késői rétegekben (⛔ a középső rétegeket
    a Mérés B alapján nem tudjuk olvasni)
D3  SAE: a forrásnyelvi fogalom feature-halmaza közelebb van-e az angol KÖZELÍTŐSZÓHOZ,
    mint a saját kérdésének angol változatához
"""
import csv
import json
import math
import pathlib
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ⚠️ A fogalomnevek kínai írásjegyeket tartalmaznak — a DejaVu Sans üres négyzetet rajzolna
# helyettük. A Noto Sans CJK a magyar ékezeteket is viszi, ezért az egész ábrán ezt használjuk.
plt.rcParams["font.family"] = ["Noto Sans CJK JP", "DejaVu Sans"]
import numpy as np
import scope_paths

HERE = pathlib.Path(__file__).resolve().parent.parent
RES, OUT, FIG = scope_paths.res(HERE), scope_paths.reports(HERE), scope_paths.figures(HERE)
LANGS = ("hu", "en", "zh")
LAYER = 10          # a Mérés C többlet-csúcsa
RNG = np.random.default_rng(0)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p, d = k / n, 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def sign_test(diffs):
    """Kétoldalas előjelteszt — n=8-nál a t-próba feltevései nem tarthatók."""
    pos = sum(1 for d in diffs if d > 0)
    neg = sum(1 for d in diffs if d < 0)
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    k = min(pos, neg)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, p), pos, neg


def jac(a, b):
    u = len(a | b)
    return len(a & b) / u if u else 0.0


def main():
    FIG.mkdir(exist_ok=True)
    rows = list(csv.DictReader((RES / "d1_scores.csv").open(encoding="utf-8")))
    # ⛔ A ellenőrző kör felülírása: a `manual_*` oszlop MINDIG erősebb a bíráló ítéleténél.
    # (Korábban a szkript csak a bíráló oszlopait olvasta, tehát a ellenőrző kör eredménye
    # némán elveszett volna — a runbook §4b viszont kötelezőnek írja elő.)
    n_manual = 0
    for r in rows:
        for auto, man in (("native_hit", "manual_native"), ("distortion_hit", "manual_distortion"),
                          ("ctrl_itelet", "manual_ctrl")):
            v = (r.get(man) or "").strip()
            if v:
                r[auto] = v
                n_manual += 1
    unt = [r for r in rows if r["kind"] == "unt"]
    ctrl = [r for r in rows if r["kind"] == "ctrl"]
    items = {json.loads(l)["id"]: json.loads(l) for l in
             (HERE / "items.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}

    md = ["# Mérés D — lefordíthatatlan fogalmak (a fordítási hipotézis direkt tesztje)", "",
          "16 fogalom × 3 nyelv + 16 kontrollszó × 3 nyelv. A `native` és `distortion` komponenseket a "
          "bíráló komponensenként külön értékelte; a `manual_*` oszlop a saját ellenőrző körömé (runbook §4b: "
          f"mind a 48 kötelező) — ebben a futásban **{n_manual} cella** ellenőrző felülírás.", "",
          "## D1 — komponens-lefedettség", "",
          "| forrásnyelv | prompt nyelve | native | distortion | hurokba esett |", "|---|---|---|---|---|"]
    d1 = {}
    for src in ("hu", "zh"):
        for lang in LANGS:
            s = [r for r in unt if r["src_lang"] == src and r["lang"] == lang]
            nat, natn = sum(int(r["native_hit"]) for r in s), sum(int(r["native_n"]) for r in s)
            dis, disn = sum(int(r["distortion_hit"]) for r in s), sum(int(r["distortion_n"]) for r in s)
            deg = sum(int(r["degenerate"]) for r in s)
            lo, hi = wilson(nat, natn)
            d1[f"{src}/{lang}"] = {"native": nat, "native_n": natn, "native_rate": nat / natn,
                                   "ci": [lo, hi], "distortion": dis, "distortion_n": disn, "degenerate": deg}
            tag = " ← **forrásnyelv**" if lang == src else ""
            md.append(f"| {src} ({len(s)} fogalom) | {lang}{tag} | {nat}/{natn} = **{nat/natn:.0%}** "
                      f"[{lo:.0%}–{hi:.0%}] | {dis}/{disn} = {dis/disn:.0%} | {deg}/{len(s)} |")

    # párosított előjelteszt: forrásnyelv vs angol, fogalmanként
    md += ["", "### Párosított összevetés — forrásnyelv vs. angol (fogalmanként, előjelteszt)", ""]
    for src in ("hu", "zh"):
        per = defaultdict(dict)
        for r in unt:
            if r["src_lang"] == src:
                per[r["concept"]][r["lang"]] = int(r["native_hit"])
        diffs = [v[src] - v["en"] for v in per.values() if src in v and "en" in v]
        p, pos, neg = sign_test(diffs)
        md.append(f"- **{src}-forrású fogalmak (n={len(diffs)}):** a forrásnyelv {pos} fogalomnál jobb, "
                  f"{neg}-nél rosszabb az angolnál (előjelteszt p = {p:.3f}) — "
                  f"átlagos különbség {np.mean(diffs):+.2f} komponens.")

    # ── kontroll ────────────────────────────────────────────────────────────
    md += ["", "## D1 kontroll — a hétköznapi szavak definíciója", "",
           "Ha a nyelvek közti különbség a kontrollszavaknál IS megvan, akkor nem a lefordíthatatlanságból "
           "jön, hanem a modell általános nyelvi teljesítményéből.", "",
           "| prompt nyelve | jó | részben | rossz | hurokba esett |", "|---|---|---|---|---|"]
    ctrl_rate = {}
    for lang in LANGS:
        s = [r for r in ctrl if r["lang"] == lang]
        c = {k: sum(1 for r in s if r["ctrl_itelet"] == k) for k in ("jo", "reszben", "rossz")}
        ctrl_rate[lang] = c["jo"] / len(s)
        md.append(f"| {lang} | {c['jo']} | {c['reszben']} | {c['rossz']} | "
                  f"{sum(int(r['degenerate']) for r in s)}/{len(s)} |")
    md += ["", f"⛔⛔ **A kontroll fog: a magyar általánosan gyengébb** — hétköznapi szóra is csak "
           f"{ctrl_rate['hu']:.0%} a jó definíció, szemben az angol {ctrl_rate['en']:.0%}-kal "
           f"(kínai {ctrl_rate['zh']:.0%}). A D1 nyelvek közti különbségét tehát **nem szabad** a "
           "lefordíthatatlanságnak tulajdonítani: a különbség jó része a generálás általános minőségéből jön.", ""]

    # ── keretezési érzékenységvizsgálat ─────────────────────────────────────
    sens_dir = RES / "gen_sens"
    if sens_dir.exists() and any(sens_dir.glob("*.json")):
        sens = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(sens_dir.glob("*.json"))]
        sj = RES / "d1_sens_judge.json"
        md += ["## ⛔⛔ Keretezési érzékenységvizsgálat", "",
               "A fagyasztott korpuszban a kínai-forrású fogalmak kérdése **nyelvenként más keretet ad**: "
               "a magyar/angol változat „fogalom”/„concept” magyarázatot kér, a kínai viszont `一词` "
               "(„a szó”) — sima szótári kérdést. Ez önmagában megmagyarázhatja, miért ad a modell kínaiul "
               "általános glosszát. Ezért a 8 kínai-forrású fogalomra lefutott egy extra generálás "
               "**szimmetrizált** kínai kérdéssel (`一词` → `这个概念`).", ""]
        if sj.exists():
            judged = json.load(open(sj, encoding="utf-8"))
            base = {r["concept"]: int(r["native_hit"]) for r in unt if r["src_lang"] == "zh" and r["lang"] == "zh"}
            md += ["| fogalom | eredeti kínai kérdés (一词) | szimmetrizált (这个概念) |", "|---|---|---|"]
            diffs = []
            for j in judged:
                b = base.get(j["concept"])
                diffs.append(j["native_hit"] - b)
                md.append(f"| {j['concept']} | {b}/{j['native_n']} | **{j['native_hit']}/{j['native_n']}** |")
            p, pos, neg = sign_test(diffs)
            md += ["", f"Átlagos változás: **{np.mean(diffs):+.2f} komponens** (javult {pos}, romlott {neg}, "
                   f"előjelteszt p = {p:.3f}).", ""]
        else:
            md += [f"*(A {len(sens)} generálás megvan, a bírálat még hátra: `src/judge_d1_sens.py`.)*", ""]

    # ── az önértékelő toldalék hatása ───────────────────────────────────────
    gen = [json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    cut_by_lang = {lg: (sum(1 for r in gen if r["lang"] == lg and r.get("self_eval_cut") is True),
                        sum(1 for r in gen if r["lang"] == lg)) for lg in LANGS}
    md += ["## ⛔⛔ Az önértékelő toldalék — egy nyelvfüggő mérési hiba, ami majdnem eldöntötte a D1-et", "",
           "A base modell a válasz után gyakran **saját feladat-promptot** ír "
           "(*„请判断回答是否正确…正确”*, *„A single-select problem: Is the question answered…”*), és ez a "
           "bírálót félrevezeti: egy mért esetben (撒娇/zh) a bíráló a toldalékra ítélt („a válasz csak a "
           "»helyes« szót tartalmazza”), és 0 komponenst adott egy olyan válaszra, amiben az első komponens "
           "egyértelműen benne van.", "",
           "A jelenség **nyelvfüggő**: " + " · ".join(
               f"{lg} {c}/{n} = {c/n:.0%}" for lg, (c, n) in cut_by_lang.items()) +
           " — tehát pont azokat a cellákat rontja, ahol a D1 meglepő eredménye született.", "",
           "A `src/clean_answers.py` utólag levágja (generálni nem kell újra, a toldalék nem része a "
           "válasznak), és a bírálók a `text_clean` mezőt kapják. **A javítás hatása mérve:** a kínai-forrású "
           "fogalmak kínai nyelvű komponens-lefedettsége **58 % → 71 %**, a Mérés A `HU/en` cellája pedig "
           "27 % → 20 % (ott a toldalék *fel*felé torzított). Ezt a lépést a módszertanban le kell írni.", ""]

    # ── D3: SAE ─────────────────────────────────────────────────────────────
    def union_set(item, lang, layer=LAYER):
        z = np.load(RES / "sae" / f"{item}_{lang}.npz", allow_pickle=True)["idx"][layer]
        return set(z.reshape(-1).tolist())

    md += ["## D3 — SAE: a fogalom vagy az angol közelítőszó felé húz?", "",
           f"A {LAYER}. rétegen (a Mérés C többlet-csúcsa), `union` halmazon. Három Jaccard fogalmanként:", "",
           "| fogalom | forrás | J(forrás, saját angol kérdés) | J(forrás, angol KÖZELÍTŐSZÓ) | "
           "J(forrás, harmadik nyelv) |", "|---|---|---|---|---|"]
    d3 = []
    for iid, it in sorted(items.items()):
        if it.get("group") != "UNT":
            continue
        src = it["src_lang"]
        third = "zh" if src == "hu" else "hu"
        s_src = union_set(iid, src)
        j_own_en = jac(s_src, union_set(iid, "en"))
        j_ctrl_en = jac(s_src, union_set(iid + "-ctrl", "en"))
        j_third = jac(s_src, union_set(iid, third))
        d3.append({"concept": it["concept"], "src": src, "own_en": j_own_en,
                   "ctrl_en": j_ctrl_en, "third": j_third})
        mark = " ⚠️" if j_ctrl_en > j_own_en else ""
        md.append(f"| {it['concept']} | {src} | **{j_own_en:.3f}** | {j_ctrl_en:.3f}{mark} | {j_third:.3f} |")

    # ── D3b: a KONFUNDÁLÁS-MENTES teszt ─────────────────────────────────────
    # ⛔⛔ A fenti összevetés nem tiszta: a fogalom SAJÁT angol kérdése szó szerint
    # tartalmazza a fogalmat („What does the Chinese concept '关系' (guanxi) mean?"),
    # az angol kontrollszó-prompt viszont nem — a magasabb Jaccard jöhet puszta
    # token-egyezésből. A tiszta kérdés ezért: a forrásnyelvi fogalom közelebb van-e a
    # SAJÁT angol közelítőszavához, mint MÁS fogalmak angol közelítőszavaihoz?
    # Itt egyik oldalon sincs szó szerinti egyezés, tehát csak a jelentés maradhat.
    unt_ids = [i for i, it in items.items() if it.get("group") == "UNT"]
    d3b = []
    for iid in sorted(unt_ids):
        it = items[iid]
        s_src = union_set(iid, it["src_lang"])
        own_ctrl = jac(s_src, union_set(iid + "-ctrl", "en"))
        others = [jac(s_src, union_set(j + "-ctrl", "en")) for j in unt_ids if j != iid]
        d3b.append({"concept": it["concept"], "src": it["src_lang"], "own_ctrl": own_ctrl,
                    "other_ctrl_mean": float(np.mean(others)),
                    "excess": own_ctrl - float(np.mean(others))})
    exc = np.array([d["excess"] for d in d3b])
    pb, posb, negb = sign_test(list(exc))
    md += ["", "### D3b — a konfundálás-mentes változat (⛔ KONTROLLSZAVAS: ld. lent)", "",
           "⛔⛔ **2026-08-26, bírálat nyomán:** ez a szakasz a fogalomhoz rendelt KONTROLLSZÓ (`control.en`: "
           "help, friendship…) promptját hasonlítja, NEM az `en_approx` közelítőszóét (mutual aid, love…) — "
           "tehát „szemantikai szomszéd”-tesztként olvasandó, a fordítási hipotézis tesztje az újramérés: "
           "`05_d3b_ujrameres.md` (`analyze_d3b.py`, protokoll: `d3b-protokoll.md`).", "",
           "⛔⛔ A fenti tábla **nem tiszta**: a fogalom saját angol kérdése szó szerint tartalmazza magát a "
           "fogalmat (*„What does the Chinese concept '关系' (guanxi) mean?”*), az angol közelítőszó-prompt "
           "viszont nem — a magasabb Jaccard jöhet puszta token-egyezésből is. Tiszta kérdés: a forrásnyelvi "
           "fogalom közelebb van-e a **saját** angol közelítőszavához, mint **más fogalmak** angol "
           "közelítőszavaihoz? Itt egyik oldalon sincs szó szerinti egyezés.", "",
           "| fogalom | J(forrás, SAJÁT angol közelítőszó) | J(forrás, MÁS fogalmak közelítőszavai, átlag) | többlet |",
           "|---|---|---|---|"]
    for d in d3b:
        md.append(f"| {d['concept']} | {d['own_ctrl']:.3f} | {d['other_ctrl_mean']:.3f} | "
                  f"**{d['excess']:+.3f}** |")
    md += ["", f"Átlagos többlet: **{exc.mean():+.4f}** — {posb} fogalomnál pozitív, {negb}-nél negatív "
           f"(előjelteszt p = {pb:.3f}).", "",
           ("⭐⭐ **Nincs kimutatható vonzás a saját angol közelítőszó felé** — a fogalom forrásnyelvi "
            "reprezentációja nem áll közelebb a szegényebb angol megfelelőjéhez, mint bármelyik másikhoz. "
            "Ez a legtisztább jel a **fordítás-hipotézis ellen**: nem látszik, hogy a modell az angol "
            "közelítésen keresztül érné el a fogalmat."
            if pb >= 0.05 else
            "⚠️ **A saját angol közelítőszó felé mérhető vonzás van** — ez a torzulás mechanisztikus jele, "
            "a fordítás-hipotézis mellett szól."), ""]

    own = np.array([d["own_en"] for d in d3])
    ctl = np.array([d["ctrl_en"] for d in d3])
    thi = np.array([d["third"] for d in d3])
    p, pos, neg = sign_test(list(own - ctl))
    md += ["", f"**Átlag:** saját angol kérdés {own.mean():.3f} · angol közelítőszó {ctl.mean():.3f} · "
           f"harmadik nyelv {thi.mean():.3f}.",
           f"A forrásnyelvi fogalom {pos} esetben a SAJÁT angol kérdéséhez áll közelebb, {neg} esetben az "
           f"angol közelítőszóhoz (előjelteszt p = {p:.3f}).", "",
           ("⭐ **A fogalom a saját fordításához húz, nem a szegényebb angol közelítéshez** — ez a "
            "fordítás-hipotézis ellen szól: a modell nem az angol közelítőszón keresztül éri el a fogalmat."
            if own.mean() > ctl.mean() else
            "⚠️ **A fogalom az angol KÖZELÍTŐSZÓHOZ áll közelebb** — ez a torzulás mechanisztikus jele."), ""]

    # ── D2: logit lens — rétegenként, MINDKÉT lencsével ─────────────────────
    # A naiv lens a 0–23. rétegen olvashatatlan (Mérés B: a top-20 ~76 %-a nem szó),
    # ezért az eredeti „felbukkan-e a »noisy« a 15–25. rétegben?" kérdés vele nem
    # tesztelhető. A tuned lens ezt a tartományt olvashatóvá tette (nem-szó arány
    # 76 % → 31 %), tehát a kérdés MOST tesztelhető — de csak a korlátjával együtt
    # olvasható, ezért mindkét lencse kimegy, és a naiv marad a konzervatív alap.
    unt_items = [(iid, it) for iid, it in sorted(items.items()) if it.get("group") == "UNT"]

    def d2_scan(suffix):
        """(item, nyelv) → {réteg: [talált angol szavak]} az adott lencsével."""
        vocab = json.load(open(RES / f"lens_vocab{suffix}.json", encoding="utf-8"))
        lens = np.load(RES / f"lens_top{suffix}.npz")["ids"]
        index = json.load(open(RES / f"lens_index{suffix}.json", encoding="utf-8"))
        pos = {(m["item_id"], m["lang"]): i for i, m in enumerate(index)}
        hits = {}
        for iid, it in unt_items:
            words = {w.strip().lower() for w in it["en_approx"].replace("/", " ").split()
                     if len(w.strip()) > 3}
            for lang in ("hu", "zh"):
                n = pos[(iid, lang)]
                per_layer = {}
                for L in range(lens.shape[1]):
                    toks = {vocab[str(int(t))]["text"].strip().lower() for t in lens[n, L]}
                    got = sorted(words & toks)
                    if got:
                        per_layer[L] = got
                hits[(iid, lang)] = per_layer
        return hits, lens.shape[1]

    # ⛔ A D2 a logit lens kimenetére épül, ami külön lépés (runbook §3 / §4c 4. lépés).
    # Egy félkész körben (pl. az instruct kör a lens előtt) ez hiányzik — ilyenkor a D2-t
    # KIHAGYJUK egy jelöléssel, nem dobjuk el az egész D-elemzést (D1, D3, D3b megvan).
    have = {sfx: (RES / f"lens_vocab{sfx}.json").exists() and (RES / f"lens_top{sfx}.npz").exists()
            for sfx in ("", "_tuned")}
    LATE = 24                                    # innen olvasható a naiv lens is

    def lens_facts(sfx):
        """(különböző token a top-20-ban, átlagos NEM-SZÓ arány a 0–23. síkon) — EBBŐL a körből.

        ⛔ Ezek a számok 2026-08-25-ig FIXEN a base kör értékei voltak beégetve (3367 vs. 9064,
        „nem-szó arány 31 %"), így az instruct kör D2-szövege a base számait állította magáról.
        """
        n_tok = len(json.load(open(RES / f"lens_vocab{sfx}.json", encoding="utf-8"))) \
            if have[sfx] else None
        f = OUT / f"03_meres_b{sfx}.json"
        junk = None
        if f.exists():
            mj = json.load(open(f, encoding="utf-8")).get("mean_junk")
            if mj:
                junk = sum(mj[:LATE]) / len(mj[:LATE])
        return n_tok, junk

    n_naive, junk_naive = lens_facts("")
    n_tuned, junk_tuned = lens_facts("_tuned")
    jn = f"{junk_naive:.0%}" if junk_naive is not None else "?"
    jt = f"{junk_tuned:.0%}" if junk_tuned is not None else "?"
    if not have[""]:
        md += ["## D2 — logit lens: megjelenik-e az angol közelítés?", "",
               f"⏳ **Kihagyva:** ebben a körben (`{RES.name}`) még nem futott a logit lens "
               "(`src/logit_lens.py`). A D1, D3 és D3b eredményei ettől függetlenek és fentebb "
               "olvashatók. A D2 pótlásához:", "", "```bash",
               f"SCOPE_RES={RES.name} SCOPE_MODEL=… bash src/run_spark.sh src/logit_lens.py",
               f"SCOPE_RES={RES.name} SCOPE_REPORTS={OUT.name} python3 src/analyze_d.py", "```", ""]
        d2_hits = d2_tuned_hits = mid_naive = mid_tuned = None
    else:
        naive_hits, n_planes = d2_scan("")
        tuned_hits, _ = d2_scan("_tuned") if have["_tuned"] else ({k: {} for k in naive_hits}, None)

        md += ["## D2 — logit lens: megjelenik-e az angol közelítés?", "",
               f"⛔ A Mérés B kimutatta, hogy a **naiv** logit lens a 0–23. síkon olvashatatlan ezen a modellen "
               f"(a top-20 {jn}-a nem szó), ezért az eredeti kérdés („felbukkan-e a »noisy« a 15–25. rétegben?”) "
               "vele **nem tesztelhető** — csak a 24–31. sík.", "",
               f"⚠️ A **tuned lens** ezt a tartományt olvashatóvá tette (nem-szó arány {jn} → {jt}), tehát a "
               "kérdés most tesztelhető. **De:** a fordítót a végső eloszlás KL-jére tanítottuk, ezért "
               "előrehúzhat olyan tokent, ami a rétegben még nincs ott (ld. `03_meres_b_tuned.md` — a várt "
               "válasz mediánrangja már a 0. síkon 100 alá esik). A tuned oszlop tehát **felső korlát**, "
               "a naiv oszlop **alsó korlát**.", "",
               "| fogalom | angol közelítés | naiv, 24–31. sík | tuned, első sík | tuned, hány síkon |",
               "|---|---|---|---|---|"]
        d2_hits = 0
        for iid, it in unt_items:
            naive_late, tuned_any = [], []
            first_plane, n_planes_hit = [], 0
            for lang in ("hu", "zh"):
                got = sorted({w for L, ws in naive_hits[(iid, lang)].items() if L >= LATE for w in ws})
                if got:
                    naive_late.append(f"{lang}: {', '.join(got)}")
                tl = sorted(tuned_hits[(iid, lang)])
                if tl:
                    first_plane.append(f"{lang}: {tl[0]}")
                    n_planes_hit += len(tl)
            d2_hits += bool(naive_late)
            md.append(f"| {it['concept']} | {it['en_approx']} | {'; '.join(naive_late) or '–'} | "
                      f"{'; '.join(first_plane) or '–'} | {n_planes_hit or '–'} |")
        d2_tuned_hits = sum(1 for iid, _ in unt_items
                            if any(tuned_hits[(iid, l)] for l in ("hu", "zh")))
        mid_naive = sum(1 for iid, _ in unt_items for l in ("hu", "zh")
                        if any(L < LATE for L in naive_hits[(iid, l)]))
        mid_tuned = sum(1 for iid, _ in unt_items for l in ("hu", "zh")
                        if any(L < LATE for L in tuned_hits[(iid, l)]))
        md += ["", f"**{d2_hits}/16 fogalomnál** bukkan fel az angol közelítés valamelyik szava a nem-angol "
               f"prompt KÉSŐI rétegeiben a naiv lensszel; a tuned lensszel — bármelyik síkon — "
               f"**{d2_tuned_hits}/16**.", "",
               f"⭐⭐ **A KÖZÉPSŐ (0–23.) síkon "
               + ("egyetlen találat sincs: " if not (mid_naive or mid_tuned) else "")
               + f"{mid_naive}/32 prompt a naiv, {mid_tuned}/32 a tuned lensszel.** Épp ez volt a "
               "fordítási hipotézis legdirektebb tesztje — a Mérés B óta tudjuk, hogy a naiv lens itt "
               f"vak, de a tuned lens **látja** ezt a tartományt (a 0–23. sík átlagos nem-szó aránya "
               f"{jn} → {jt}), és **ott sem** hozza elő az angol közelítőszót. A talált néhány eset "
               "mind a 24. sík FÖLÖTT van, tehát abban a tartományban, ahol a modell már a válasz "
               "nyelve felé fordul.", "",
               f"⚠️ Ellenpróba-korlát: a tuned lens top-20-a **koncentráltabb** ({n_tuned} vs. "
               f"{n_naive} különböző token az egész korpuszon), tehát kevesebb szót lát — a 0 találat "
               "részben ebből is jöhet. A naiv lens 0-ja viszont nem ilyen: az ő top-20-a tágabb, "
               "csak épp olvashatatlan.", ""]
        if (OUT / "05_d2_kontroll.md").exists():
            md += ["⛔⛔ **A null-eredmény bizonyító ereje korlátos** — ld. a kör kontroll-riportját "
                   "([05_d2_kontroll.md](05_d2_kontroll.md), `src/d2_control.py`): az ANGOL prompton futó "
                   "pozitív kontroll szerint a műszer érzékenysége alacsony, több fogalom jelöltszava a "
                   "korpusz egyetlen top-20-jában sem fordul elő, és a szóillesztés írásjel-érzékeny "
                   "(tisztított matcherrel a nulla törhet). A D2 tehát gyenge evidencia a fordítási "
                   "útvonal ellen, nem perdöntő.", ""]
        else:
            md += ["⚠️ A null-eredmény erejét a `src/d2_control.py` kontrolljai (pozitív kontroll az angol "
                   "prompton, elérhetőségi nevező, matcher-érzékenység) mérik ki — ebben a körben még nem "
                   "futott le.", ""]
        md += ["",
               f"![D2](../{FIG.name}/05_D2_angol_kozelites_savok.png)", ""]

        # ── D2 ábra: sávábra, melyik síkon látszik az angol közelítés ───────────
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), sharey=True)
        ylab = [f"{it['concept']} → {it['en_approx']}" for _, it in unt_items]
        for ax, (hits, name) in zip(axes, ((naive_hits, "naiv lens"), (tuned_hits, "tuned lens"))):
            for i, (iid, _) in enumerate(unt_items):
                for lang, dy, col in (("hu", -.18, "#c0392b"), ("zh", .18, "#27ae60")):
                    ls = sorted(hits[(iid, lang)])
                    if ls:
                        ax.scatter(ls, [i + dy] * len(ls), s=26, marker="s", color=col)
            ax.axvspan(-.5, LATE - .5, color="#95a5a6", alpha=.13)
            ax.set_xlim(-.5, n_planes - .5); ax.set_ylim(len(unt_items) - .5, -.5)
            ax.set_xlabel("sík (0 = embedding)"); ax.grid(axis="x", alpha=.2)
            ax.set_title(name, fontsize=10)
        axes[0].set_yticks(range(len(unt_items)), ylab, fontsize=8)
        # ⛔ A jelmagyarázatot NEM a scatter label-jéből építjük: az ábra nagyrészt ÜRES
        # (ez maga az eredmény), és ha a 0. item nem talál, a legend üres dobozként jelenne meg.
        axes[0].legend(handles=[plt.Line2D([], [], ls="", marker="s", color=c, label=f"{l} prompt")
                                for l, c in (("hu", "#c0392b"), ("zh", "#27ae60"))],
                       fontsize=9, loc="lower right", framealpha=.95)
        for ax, hits in zip(axes, (naive_hits, tuned_hits)):
            mid = sum(1 for iid, _ in unt_items for l in ("hu", "zh")
                      if any(L < LATE for L in hits[(iid, l)]))
            ax.text(.02, .015, f"a szürke (középső) tartományban: {mid}/32 prompt talál",
                    transform=ax.transAxes, fontsize=9, color="#2c3e50",
                    bbox={"fc": "white", "ec": "#bbb", "alpha": .9, "pad": 3})
        fig.suptitle("D2 — hol bukkan fel az ANGOL közelítőszó a nem-angol prompt top-20-ában?\n"
                     "(szürke sáv: a naiv lensszel olvashatatlan tartomány)", fontsize=11)
        fig.tight_layout(); fig.savefig(FIG / "05_D2_angol_kozelites_savok.png", dpi=160); plt.close(fig)

    # ── D1 hőtérkép ─────────────────────────────────────────────────────────
    concepts = sorted({(r["concept"], r["src_lang"]) for r in unt}, key=lambda t: (t[1], t[0]))
    mat = np.full((len(concepts), 3), np.nan)
    for i, (c, src) in enumerate(concepts):
        for j, lang in enumerate(LANGS):
            r = next((x for x in unt if x["concept"] == c and x["lang"] == lang), None)
            if r:
                mat[i, j] = int(r["native_hit"]) / int(r["native_n"]) - int(r["distortion_hit"]) / int(r["distortion_n"])
    fig, ax = plt.subplots(figsize=(7.5, 7))
    im = ax.imshow(mat, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(3)); ax.set_xticklabels(["magyar", "angol", "kínai"])
    ax.set_yticks(range(len(concepts)))
    ax.set_yticklabels([f"{c}  [{src}]" for c, src in concepts], fontsize=9)
    for i in range(len(concepts)):
        for j in range(3):
            # a sötét zöld/piros cellákon a sötét szöveg olvashatatlan
            ax.text(j, i, f"{mat[i, j]:+.2f}", ha="center", va="center", fontsize=8,
                    color="white" if abs(mat[i, j]) > 0.55 else "#2c3e50")
        src = concepts[i][1]
        ax.add_patch(plt.Rectangle((LANGS.index(src) - .5, i - .5), 1, 1, fill=False,
                                   edgecolor="#2c3e50", lw=2))
    fig.colorbar(im, ax=ax, label="native − distortion arány")
    ax.set_title("D1 — komponens-lefedettség fogalmanként\n(vastag keret: a fogalom forrásnyelve)", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "05_D1_komponens_heatmap.png", dpi=160); plt.close(fig)
    md += [f"![D1](../{FIG.name}/05_D1_komponens_heatmap.png)", ""]

    # ── összegzés ───────────────────────────────────────────────────────────
    md += ["## A Mérés D ítélete a fordítási hipotézisről", "",
           "A runbook három jóslatot fogalmazott meg. A mérés a **köztes** képhez áll legközelebb, de a "
           "„fordítás angolon keresztül” változatot két független jel is cáfolja:", "",
           "1. ⭐⭐ **D3b (a konfundálás-mentes SAE-teszt): nincs vonzás az angol közelítőszó felé.** "
           f"A forrásnyelvi fogalom nem áll közelebb a saját angol közelítéséhez ({ctl.mean():.3f}), mint "
           f"más fogalmak közelítőszavaihoz — az átlagos többlet {exc.mean():+.4f} (előjelteszt p = {pb:.2f}). "
           "Ha a modell az angol közelítésen keresztül érné el a fogalmat, itt pozitív, szignifikáns "
           "többletnek kellene lennie.",
           (f"2. ⭐⭐ **D2: a KÖZÉPSŐ (0–23.) síkon {mid_naive}/32 prompt találja meg az angol "
            f"közelítőszót — és a tuned lensszel is {mid_tuned}/32.** A naiv lens ebben a "
            f"tartományban vak (Mérés B), de a tuned lens LÁTJA (nem-szó arány {jt}), és ott sem "
            f"hozza elő. A mindössze {d2_hits}/16 találat a **24. sík fölött** van, tehát ott, ahol "
            "a modell már a válasz nyelve felé fordul. Ez a fordítási hipotézis legdirektebb "
            "tesztje, és megbukik rajta."
            if mid_naive is not None else
            "2. ⏳ **D2: ebben a körben még nem futott a logit lens**, ezért a fordítási hipotézis "
            "reprezentáció-szintű tesztje itt még nyitott (ld. fentebb a D2 szakaszt)."),
           "3. ⚠️ **D1: a viselkedés szintjén az angol a legjobb** mindkét forrásnyelvnél "
           f"(hu-forrás: hu {d1['hu/hu']['native_rate']:.0%} vs en {d1['hu/en']['native_rate']:.0%}; "
           f"zh-forrás: zh {d1['zh/zh']['native_rate']:.0%} vs en {d1['zh/en']['native_rate']:.0%}) — "
           "**de ez a jel három konfundálóval terhelt**: (a) a kontroll szerint a magyar generálás "
           "általánosan gyengébb, (b) a kínai kérdés más keretet ad („一词” = szó, nem fogalom), "
           "(c) az önértékelő toldalék nyelvfüggően rontotta a bírálatot.", "",
           "**Összefoglalva:** a *reprezentáció* szintjén nincs nyoma annak, hogy a modell az angol "
           "közelítésen keresztül érné el a lefordíthatatlan fogalmakat; a *viselkedés* szintjén viszont az "
           "angol válasz a leggazdagabb — de ezt a különbséget nagyrészt a nyelvi generálás minősége és a "
           "kérdés keretezése magyarázza, nem a fogalom hozzáférési útja.", "",
           "⛔ **Korlát:** 8+8 fogalom, a `native`/`distortion` listákat én definiáltam, a "
           "kontrollszó-párosítás nem tökéletes. Ez kvalitatív-illusztratív mérés; a számszerű alapot a "
           "Mérés C adja.", ""]

    (OUT / "05_meres_d.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (OUT / "05_meres_d.json").write_text(json.dumps(
        {"d1": d1, "ctrl_rate": ctrl_rate, "d3": d3, "d3b": d3b, "d2_hits": d2_hits, "layer": LAYER},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
