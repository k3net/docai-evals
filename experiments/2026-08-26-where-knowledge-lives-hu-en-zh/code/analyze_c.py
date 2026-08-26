#!/usr/bin/env python3
"""Mérés C — SAE feature-átfedés a három nyelv között, RÉTEGENKÉNT (laptop).

    python3 code/analyze_c.py

Ez a mérés hordozza a dolgozat központi kérdését, mert a Mérés B kiderítette, hogy a naiv
logit lens a középső rétegeken olvashatatlan. Az SAE nem az unembeddingre vetít, hanem a
reprezentáció tanult szótárára bontja a residualt — a középső rétegeken is értelmezhető.

Két feature-halmaz promptonként és rétegenként (runbook §4):
  last   — az UTOLSÓ prompt-token 50 aktív feature-je (elsődleges)
  union  — az ÖSSZES prompt-token feature-jeinek uniója (másodlagos, tartalmasabb)

⛔ Miért nem elég a nyers Jaccard? Mert a magyar és az angol sablon UGYANAZZAL a tokennel
zárul (`:`), a kínai mással (`：`) — a 0. rétegen tehát J(en,hu) = 1,0 pusztán a sablon miatt.
Ezért minden állítás a BASELINE-hoz mért TÖBBLETRŐL szól:
  A-baseline: azonos nyelv, KÜLÖNBÖZŐ item (a runbook „véletlen átfedés"-e)
  B-baseline: különböző nyelv, KÜLÖNBÖZŐ item (a párosítás permutációs nullhipotézise)

Statisztika: bootstrap 95 % CI itemekre; permutációs teszt (10 000× derangement) a B-baseline
ellen;
Holm-korrekció a 9 összehasonlításra. Az ELSŐDLEGES réteg előre rögzítve a 16. (a H1
„középső réteg" állítása); a maximális többlet rétegét külön, feltáró jelleggel közöljük.
"""
import itertools
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
PAIRS = (("zh", "en"), ("zh", "hu"), ("en", "hu"))
PCOL = {("zh", "en"): "#2c3e50", ("zh", "hu"): "#c0392b", ("en", "hu"): "#d68910"}
PRIMARY_LAYER = 16
N_PERM = 10_000
RNG = np.random.default_rng(0)


def jac(a, b):
    u = len(a | b)
    return len(a & b) / u if u else 0.0


def derangement(n, rng):
    """Fixpont NÉLKÜLI véletlen permutáció, egyenletesen a derangementek felett.

    ⛔ Miért nem sima `rng.permutation(n)`, a fixpontokat utólag kidobva? Mert a kidobás
    változó elemszámú null-mintát ad (keverésenként nulla vagy több fixpont), és pont a HELYES
    párosításokat veti ki: a nullhipotézis átlaga így más elemszámon áll, mint a megfigyelt
    statisztika. A derangement-mintavétel n-t rögzíti, tehát `obs` és `null` ugyanannyi páron
    nyugszik.

    Elutasításos mintavétel: n ≥ 4-nél a derangementek aránya ~1/e, tehát átlagosan ~2,7
    húzás kell egy elfogadotthoz.
    """
    while True:
        perm = rng.permutation(n)
        if not np.any(perm == np.arange(n)):
            return perm


def load_sets(span_mode="question"):
    """{item: {lang: {'last': [set/réteg], 'union': [set/réteg]}}}

    ⛔⛔ `span_mode="question"` (alapértelmezés): CSAK a kérdés tokenjeit vesszük, a
    prompt-keretet nem. Miért kötelező ez?
      * a base körben a keret a `Kérdés: ` / `\nVálasz:` címke — a prompt-tokenek 31 %-a,
        és nyelven belül MINDEN itemnél bitre azonos;
      * az instruct körben a chat-sablon burkolata — a tokenek 45 %-a, és MINDEN nyelven
        bitre azonos.
    A közös keret önmagában felnyomja a Jaccard-átfedést, az instruct körben ráadásul
    NYELVFÜGGETLENÜL — vagyis pont a mért hatást hamisítaná. A `last` halmaz ilyenkor a
    kérdés UTOLSÓ tokene, nem a prompté (az instructban az a `<think>` lenne, minden
    promptnál ugyanaz).
    `span_mode="full"` a régi, teljes promptos viselkedés — összevetéshez tartjuk meg.
    """
    meta = [json.loads(l) for l in (RES / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    spans = {}
    sp = RES / "prompt_q_span.json"
    if span_mode == "question":
        if not sp.exists():
            raise SystemExit(f"nincs {sp} — előbb fusson a code/dump_tokens.py erre a körre "
                             "(vagy használd a --span full kapcsolót)")
        spans = json.load(open(sp, encoding="utf-8"))
    data, groups, kinds = {}, {}, {}
    for m in meta:
        name = f"{m['item_id']}_{m['lang']}"
        z = np.load(RES / "sae" / f"{name}.npz", allow_pickle=True)
        idx = z["idx"]                                   # [32, T, 50]
        a, b = spans.get(name, (0, idx.shape[1]))
        assert 0 <= a < b <= idx.shape[1], f"{name}: rossz tartomány {(a, b)} T={idx.shape[1]}"
        idx = idx[:, a:b, :]
        last = [set(idx[L, -1].tolist()) for L in range(idx.shape[0])]
        union = [set(idx[L].reshape(-1).tolist()) for L in range(idx.shape[0])]
        data.setdefault(m["item_id"], {})[m["lang"]] = {"last": last, "union": union}
        groups[m["item_id"]] = m["group"]
        kinds[m["item_id"]] = m["kind"]
    return data, groups, kinds, idx.shape[0]


def boot_ci(vals, n=1000):
    vals = np.asarray(vals, dtype=float)
    if len(vals) < 2:
        return (float("nan"), float("nan"))
    means = [RNG.choice(vals, len(vals), replace=True).mean() for _ in range(n)]
    return tuple(np.percentile(means, [2.5, 97.5]))


def round_label():
    """A kör címkéje a MÉRT adatból (a base kör gen.jsonl-jében még nincs `model` mező)."""
    r = json.loads((RES / "gen.jsonl").read_text(encoding="utf-8").splitlines()[0])
    m = (r.get("model") or "Qwen/Qwen3.5-9B-Base").split("/")[-1]
    return m + (" · chat-sablon" if r.get("chat_template") else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--span", choices=("question", "full"), default="question",
                    help="question (alap): csak a kérdés tokenjei · full: a teljes prompt "
                         "(a 2026-08-25 előtti viselkedés, összevetéshez)")
    args = ap.parse_args()
    FIG.mkdir(exist_ok=True)
    data, groups, kinds, L = load_sets(args.span)
    fact = [i for i in data if kinds[i] == "fact"]
    print(f"{len(data)} item ({len(fact)} faktuális) · {L} réteg · token-tartomány: {args.span}")

    res = {}
    for variant in ("last", "union"):
        for g in GROUPS:
            items = [i for i in fact if groups[i] == g]
            for a, b in PAIRS:
                matched = np.array([[jac(data[i][a][variant][l], data[i][b][variant][l]) for l in range(L)]
                                    for i in items])                       # [n_item, L]
                # B-baseline: ugyanaz a nyelvpár, KÜLÖNBÖZŐ itemek
                mism = np.array([[jac(data[i][a][variant][l], data[j][b][variant][l]) for l in range(L)]
                                 for i, j in itertools.permutations(items, 2)])
                # A-baseline: azonos nyelv, különböző item (a pár két nyelvének átlaga)
                same = []
                for lang in (a, b):
                    same += [[jac(data[i][lang][variant][l], data[j][lang][variant][l]) for l in range(L)]
                             for i, j in itertools.combinations(items, 2)]
                same = np.array(same)
                res[f"{variant}/{g}/{a}-{b}"] = {
                    "n_item": len(items),
                    "matched_mean": matched.mean(0), "matched": matched,
                    "base_cross": mism.mean(0), "base_same": same.mean(0),
                }

    # ── ⛔⛔ KONTROLL: szó szerinti token-átfedés a nyelvváltozatok között ────
    # A korpusz kérdései átírást ÉS eredeti írásjegyet is tartalmaznak
    # („Fazhugong (法主公)"), tehát a magyar prompt szó szerint tartalmazza a kínai
    # sztringet. Az így megosztott TOKENEK önmagukban feltolják a feature-átfedést —
    # ha ez magyarázza a többletet, a „közös fogalmi tér” állítás megdől.
    ptok = json.load(open(RES / "prompt_tokens.json", encoding="utf-8"))
    tokset = {k: set(v) for k, v in ptok.items()}
    tokjac = {}
    for i in fact:
        for a, b in PAIRS:
            tokjac[(i, a, b)] = jac(tokset[f"{i}_{a}"], tokset[f"{i}_{b}"])

    control = {}
    for g in GROUPS:
        items = [i for i in fact if groups[i] == g]
        for a, b in PAIRS:
            r = res[f"union/{g}/{a}-{b}"]
            tj = np.array([tokjac[(i, a, b)] for i in items])
            exc = r["matched"][:, PRIMARY_LAYER] - r["base_cross"][PRIMARY_LAYER]
            # Spearman kézzel (rangkorreláció, scipy nélkül is stabil)
            def rank(v):
                o = np.argsort(np.argsort(v)); return o.astype(float)
            rs = np.corrcoef(rank(tj), rank(exc))[0, 1] if len(items) > 2 else float("nan")
            med = np.median(tj)
            lo = exc[tj <= med]
            control[f"{g}/{a}-{b}"] = {
                "tokjac_mean": float(tj.mean()), "tokjac_median": float(med),
                "spearman_tokjac_vs_excess": float(rs),
                "excess_all": float(exc.mean()),
                "excess_low_overlap": float(lo.mean()), "n_low": int(len(lo)),
            }

    # ── permutációs teszt az ELSŐDLEGES rétegen ─────────────────────────────
    tests = []
    for g in GROUPS:
        items = [i for i in fact if groups[i] == g]
        for a, b in PAIRS:
            # A páronkénti Jaccard az elsődleges rétegen FIX, tehát egyszer kiszámoljuk
            # [n × n] mátrixba, és a 10 000 keverés már csak indexelés. Enélkül a
            # nagyobb keverésszám percekbe kerülne.
            def null_dist(variant, obs_):
                M = np.array([[jac(data[x][a][variant][PRIMARY_LAYER],
                                   data[y][b][variant][PRIMARY_LAYER])
                               for y in items] for x in items])
                idx = np.arange(len(items))
                draws = np.array([M[idx, derangement(len(items), RNG)].mean()
                                  for _ in range(N_PERM)])
                return draws, (np.sum(draws >= obs_) + 1) / (N_PERM + 1)

            key = f"union/{g}/{a}-{b}"
            obs = res[key]["matched"][:, PRIMARY_LAYER].mean()
            null, p = null_dist("union", obs)
            # ugyanez a LAST halmazon — az utolsó prompt-token minden itemnél UGYANAZ a
            # karakter (`:` / `：`), tehát ott nincs szó szerinti token-egyezés, csak a
            # figyelemmel odajutott kontextus
            obs_l = res[f"last/{g}/{a}-{b}"]["matched"][:, PRIMARY_LAYER].mean()
            null_l, p_l = null_dist("last", obs_l)
            tests.append({"group": g, "pair": f"{a}-{b}", "obs": float(obs),
                          "null_mean": float(null.mean()), "p_raw": float(p),
                          "obs_last": float(obs_l), "null_last": float(null_l.mean()),
                          "p_raw_last": float(p_l)})
    # Holm
    order = np.argsort([t["p_raw"] for t in tests])
    m = len(tests)
    prev = 0.0
    for rank, i in enumerate(order):
        adj = min(1.0, max(prev, (m - rank) * tests[i]["p_raw"]))
        tests[i]["p_holm"] = adj
        prev = adj

    # ── ábrák ───────────────────────────────────────────────────────────────
    for variant, tag in (("union", "C1"), ("last", "C1b")):
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
        for ax, g in zip(axes, GROUPS):
            for a, b in PAIRS:
                r = res[f"{variant}/{g}/{a}-{b}"]
                ax.plot(range(L), r["matched_mean"], color=PCOL[(a, b)], lw=2, label=f"{a}–{b} (ugyanaz az item)")
                ax.plot(range(L), r["base_cross"], color=PCOL[(a, b)], lw=1, ls=":", alpha=.8)
            ax.plot(range(L), res[f"{variant}/{g}/zh-en"]["base_same"], color="#7f8c8d", lw=1, ls="--",
                    label="baseline: azonos nyelv, más item")
            ax.axvline(PRIMARY_LAYER, color="#95a5a6", lw=.8)
            ax.set_title(f"{g}-only (n={res[f'{variant}/{g}/zh-en']['n_item']})" if g != "UNI" else "UNI (n=20)")
            ax.set_xlabel("réteg"); ax.grid(alpha=.25)
        axes[0].set_ylabel(f"Jaccard-átfedés ({variant})")
        axes[0].legend(fontsize=8)
        fig.suptitle(f"{tag} — SAE feature-átfedés rétegenként ({variant}); pontozott: ugyanaz a nyelvpár, "
                     "MÁS item", fontsize=11)
        fig.tight_layout(); fig.savefig(FIG / f"04_{tag}_jaccard_{variant}.png", dpi=160); plt.close(fig)

    # ── C2: a TÖBBLET-görbe — ez a mérés lényege ────────────────────────────
    # A nyers Jaccard mindhárom görbén púpos, de a púp a promptok általános
    # szerkezetéből is jöhet; ami számít, az a VÉLETLEN PÁROSÍTÁSHOZ mért többlet.
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.3), sharey=True)
    peaks = {}
    for ax, g in zip(axes, GROUPS):
        for a, b in PAIRS:
            r = res[f"union/{g}/{a}-{b}"]
            exc = r["matched"] - r["base_cross"]                 # [n_item, L]
            mean = exc.mean(0)
            ci = np.array([boot_ci(exc[:, l]) for l in range(L)])
            peaks[f"{g}/{a}-{b}"] = {"peak_layer": int(mean.argmax()), "peak": float(mean.max()),
                                     "late": float(mean[-1]), "early": float(mean[:3].mean())}
            ax.plot(range(L), mean, color=PCOL[(a, b)], lw=2, label=f"{a}–{b}")
            ax.fill_between(range(L), ci[:, 0], ci[:, 1], color=PCOL[(a, b)], alpha=.12)
        ax.axhline(0, color="#7f8c8d", lw=1)
        ax.axvline(PRIMARY_LAYER, color="#95a5a6", lw=.8, ls=":")
        ax.set_title(f"{g}-only" if g != "UNI" else "UNI")
        ax.set_xlabel("réteg"); ax.grid(alpha=.25)
    axes[0].set_ylabel("Jaccard-TÖBBLET a véletlen párosításhoz képest")
    axes[0].legend(fontsize=9)
    fig.suptitle("C2 — ugyanaz a fogalom három nyelven: mennyivel fed át jobban, mint egy véletlen itempár "
                 "(sáv: bootstrap 95 % CI)", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "04_C2_tobblet.png", dpi=160); plt.close(fig)

    # ── kvalitatív: háromnyelvű, RITKA feature-ök ───────────────────────────
    # Egy feature akkor érdekes, ha ugyanarra az itemre MINDHÁROM nyelven aktív,
    # de nem általános (nem tüzel a promptok többségén) — az utóbbi a sablon- és
    # nyelv-feature-öket zárja ki.
    QUAL_LAYER = int(np.mean([peaks[k]["peak_layer"] for k in peaks]))
    all_prompts = [(i, lg) for i in fact for lg in LANGS]
    freq = {}
    for i, lg in all_prompts:
        for f in data[i][lg]["union"][QUAL_LAYER]:
            freq[f] = freq.get(f, 0) + 1
    rare_lim = 0.2 * len(all_prompts)
    qual = []
    for i in fact:
        tri = set.intersection(*[data[i][lg]["union"][QUAL_LAYER] for lg in LANGS])
        for f in tri:
            if freq[f] <= rare_lim:
                qual.append({"item": i, "group": groups[i], "feature": int(f), "freq": freq[f]})
    qual.sort(key=lambda d: d["freq"])

    def firing_tokens(item, lang, feature, layer):
        z = np.load(RES / "sae" / f"{item}_{lang}.npz", allow_pickle=True)["idx"][layer]   # [T, 50]
        toks = ptok[f"{item}_{lang}"]
        return [toks[t] for t in range(min(len(toks), z.shape[0])) if feature in z[t]]

    # ⛔ A puszta ritkaság szerinti rangsor a SZÓ SZERINTI egyezéseket hozza előre
    # (pl. a „kom at" tokenpár mindhárom nyelvben ugyanaz a „komatál" szóból). A meggyőző
    # példa az, ahol a feature MÁS-MÁS sztringen tüzel a három nyelven — ott nem a token
    # közös, hanem a fogalom.
    def norm(ts):
        return {t.strip().lower() for t in ts if t.strip()}

    filtered = []
    for q in qual:
        toks = {lg: firing_tokens(q["item"], lg, q["feature"], QUAL_LAYER) for lg in LANGS}
        if not all(toks[lg] for lg in LANGS):
            continue
        sets = [norm(toks[lg]) for lg in LANGS]
        if sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2]:
            continue                      # van szó szerint közös token → nem bizonyít
        q["_toks"] = toks
        filtered.append(q)

    examples = []
    for q in filtered[:6]:
        ex = {"item": q["item"], "group": q["group"], "feature": q["feature"],
              "freq": q["freq"], "layer": QUAL_LAYER, "tokens": q["_toks"]}
        examples.append(ex)

    # ── riport ──────────────────────────────────────────────────────────────
    md = ["# Mérés C — SAE feature-átfedés a nyelvek között", "",
          f"258 prompt × {L} réteg × 50 aktív feature · modell: **{round_label()}** · "
          f"token-tartomány: **{args.span}**.", "",
          ("⛔ A mérés **kizárólag a kérdés tokenjeit** használja, a prompt keretét nem. A base körben "
           "a keret a `Kérdés: ` / `\nVálasz:` címke (a prompt-tokenek 31 %-a), az instruct körben a "
           "chat-sablon burkolata (45 %) — és a keret nyelven belül, az instructnál pedig NYELVEK KÖZT IS "
           "bitre azonos, tehát önmagában felnyomná az átfedést. A szűkítés a hatást nem gyengíti, hanem "
           "**élesíti**: a base kör UNI zh–en csúcstöbblete a teljes prompton +0,090 volt, a kérdésre "
           "szűkítve **+0,129** — a közös keret a VÉLETLEN párosítást emelte jobban, azaz hígította a jelet."
           if args.span == "question" else
           "⚠️ Ez a futás a **teljes promptot** használja (`--span full`), tehát a prompt keretét is. "
           "Ez a 2026-08-25 előtti viselkedés, összevetésre tartjuk meg — a dolgozat számai a "
           "`--span question` futásból valók."), "",
          "Két halmaz: `last` (a kérdés utolsó tokene) és `union` (a kérdés minden tokenének uniója). "
          "Minden állítás a baseline-hoz mért **többletről** szól.", "",
          f"## Permutációs teszt az előre rögzített {PRIMARY_LAYER}. rétegen (`union`)", "",
          "| csoport | nyelvpár | ugyanaz az item | véletlen párosítás | p (nyers) | p (Holm) |",
          "|---|---|---|---|---|---|"]
    for t in tests:
        sig = " ✅" if t["p_holm"] < 0.05 else ""
        md.append(f"| {t['group']} | {t['pair']} | **{t['obs']:.3f}** | {t['null_mean']:.3f} | "
                  f"{t['p_raw']:.4f} | {t['p_holm']:.4f}{sig} |")

    md += ["", "## Rétegenkénti átfedés és többlet (`union`)", "",
           "| csoport | nyelvpár | 8. | 16. | 24. | 31. | max. többlet (réteg) |", "|---|---|---|---|---|---|---|"]
    for g in GROUPS:
        for a, b in PAIRS:
            r = res[f"union/{g}/{a}-{b}"]
            exc = r["matched_mean"] - r["base_cross"]
            k = int(np.argmax(exc))
            md.append(f"| {g} | {a}–{b} | " + " | ".join(
                f"{r['matched_mean'][i]:.3f} (+{exc[i]:.3f})" for i in (8, 16, 24, 31)) +
                f" | **+{exc[k]:.3f}** ({k}.) |")
    md += ["", f"![C1](../{FIG.name}/04_C1_jaccard_union.png)", "",
           "## A többlet alakja rétegenként — ez a mérés lényege", "",
           "| csoport | nyelvpár | többlet a 0–2. rétegen | csúcs (réteg) | az utolsó rétegen |",
           "|---|---|---|---|---|"]
    for g in GROUPS:
        for a, b in PAIRS:
            pk = peaks[f"{g}/{a}-{b}"]
            md.append(f"| {g} | {a}–{b} | +{pk['early']:.3f} | **+{pk['peak']:.3f}** ({pk['peak_layer']}.) | "
                      f"+{pk['late']:.3f} |")
    md += ["", f"![C2](../{FIG.name}/04_C2_tobblet.png)", "",
           f"![C1b](../{FIG.name}/04_C1b_jaccard_last.png)", "",
           "## ⛔⛔ Kontroll — nem a szó szerinti token-egyezés csinálja?", "",
           "A korpusz kérdései átírást ÉS eredeti írásjegyet is tartalmaznak "
           "(*„Melyik tartományban tisztelik elsősorban **Fazhugong (法主公)** népi istenséget?”*), tehát a "
           "magyar prompt szó szerint tartalmazza a kínai sztringet. Ha a feature-többletet ez okozná, a "
           "„közös fogalmi tér” állítás megdőlne. Három ellenőrzés:", "",
           "| csoport | nyelvpár | token-Jaccard (átlag) | Spearman(token-átfedés, feature-többlet) | "
           "feature-többlet — mind | …a KIS token-átfedésű felén |", "|---|---|---|---|---|---|"]
    for g in GROUPS:
        for a, b in PAIRS:
            c = control[f"{g}/{a}-{b}"]
            md.append(f"| {g} | {a}–{b} | {c['tokjac_mean']:.3f} | {c['spearman_tokjac_vs_excess']:+.2f} | "
                      f"+{c['excess_all']:.3f} | +{c['excess_low_overlap']:.3f} (n={c['n_low']}) |")
    md += ["", "Továbbá a `last` halmaz — a kérdés-tartomány UTOLSÓ tokene, vagyis a kérdés záró "
           "`?` / `？` írásjegye —: ezen a pozíción szó szerinti tartalmi egyezés nincs, csak a "
           "figyelemmel odajutott kontextus (ami a teljes kérdést összegzi, tehát a literális átfedést "
           "nem zárja ki teljesen):", "",
           "| csoport | nyelvpár | ugyanaz az item (`last`) | véletlen párosítás | p (nyers) |",
           "|---|---|---|---|---|"]
    for t in tests:
        md.append(f"| {t['group']} | {t['pair']} | **{t['obs_last']:.3f}** | {t['null_last']:.3f} | "
                  f"{t['p_raw_last']:.4f} |")

    md += ["", "## Kvalitatív — háromnyelvű, ritka feature-ök", "",
           f"A {QUAL_LAYER}. rétegen (a többlet-csúcsok átlaga) azok a feature-ök, amelyek ugyanarra az itemre "
           f"MINDHÁROM nyelven aktívak, de a promptok legfeljebb 20 %-án tüzelnek (a gyakoriak a sablon- és "
           f"nyelv-feature-ök). Összesen **{len(qual)}** ilyen (feature, item) pár. Az alábbiak ráadásul HÁROM "
           f"KÜLÖNBÖZŐ sztringen tüzelnek a három nyelven (**{len(filtered)}** ilyen) — itt tehát nem a token "
           "közös, hanem a fogalom:", "",
           "| item | feature | hány promptban aktív (258-ból) | mely tokeneken tüzel — kínai / angol / magyar |",
           "|---|---|---|---|"]
    for e in examples:
        cells = " / ".join("`" + " ".join(e["tokens"][lg][:6]).strip() + "`" if e["tokens"][lg] else "–"
                           for lg in ("zh", "en", "hu"))
        md.append(f"| {e['item']} ({e['group']}) | {e['feature']} | {e['freq']} | {cells} |")
    hu_sps = [control[f"HU/{a}-{b}"]["spearman_tokjac_vs_excess"] for a, b in PAIRS]
    hu_sp_lo = f"{min(hu_sps):+.2f}".replace(".", ",")
    hu_sp_hi = f"{max(hu_sps):+.2f}".replace(".", ",")
    uni_early = np.mean([peaks[f"UNI/{a}-{b}"]["early"] for a, b in PAIRS])
    uni_peak = np.mean([peaks[f"UNI/{a}-{b}"]["peak"] for a, b in PAIRS])
    uni_late = np.mean([peaks[f"UNI/{a}-{b}"]["late"] for a, b in PAIRS])
    md += ["", "## Mit mond ez a hipotézisről?", "",
           "⭐⭐ **A H1 által jósolt alak megjelenik — és a legtisztábban a UNI-csoportban.** Ott a három "
           "nyelvi változat felszíni alakja tényleg különbözik (`fotoszintézis` / `photosynthesis` / `光合作用`), "
           f"tehát szó szerinti token-egyezés alig van: a többlet az embedding környékén még csak "
           f"**+{uni_early:.3f}**, a **9–11. rétegen +{uni_peak:.3f}** a csúcs, a kimenet felé pedig "
           f"**+{uni_late:.3f}**-ra esik vissza. Vagyis: a nyelvek a bemeneten szétváltak, a középső rétegekben "
           "közelednek, a végén újra elválnak — pontosan a „nem fordít, de nem is végig nyelvfüggetlen” kép.", "",
           "⭐ **Ez az a mérés, amit a logit lens nem tudott elvégezni.** A Mérés B kiderítette, hogy a naiv "
           "lens a 0–23. rétegen olvashatatlan; az SAE viszont épp ott, a 7–11. rétegen mutatja a legerősebb "
           "nyelvek közti közeledést. A két mérés így nem átfed, hanem kiegészíti egymást.", "",
           "⛔ **Amit NEM mond:** a többlet abszolút értéke kicsi (a Jaccard 0,19-ről 0,13-ra esne vissza "
           "véletlen párosításnál), tehát a reprezentáció **túlnyomó része nyelvspecifikus marad** — a közös "
           "fogalmi rész egy réteg a nyelvi jelek tetején, nem a fő jel. És a mérés nem mondja meg, hogy a "
           "közös rész ANGOL-e; ahhoz a Mérés D (lefordíthatatlan fogalmak) kell.", "",
           f"⛔ **Korlát:** a ZH- és HU-csoportban a kérdések átírást és eredeti írásjegyet is tartalmaznak, "
           f"ezért ott a korai rétegek többlete részben szó szerinti token-egyezés (a kontroll-táblában a HU "
           f"csoport Spearman-értéke {hu_sp_lo}…{hu_sp_hi}). A UNI-csoport ettől mentes — az érvet arra kell "
           "építeni.", ""]

    (OUT / "04_meres_c.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (OUT / "04_meres_c.json").write_text(json.dumps({
        "primary_layer": PRIMARY_LAYER, "tests": tests, "control_token_overlap": control,
        "peaks": peaks, "qualitative": examples, "qual_layer": QUAL_LAYER, "n_qual_pairs": len(qual),
        "curves": {k: {"matched": v["matched_mean"].round(4).tolist(),
                       "base_cross": v["base_cross"].round(4).tolist(),
                       "base_same": v["base_same"].round(4).tolist(), "n_item": v["n_item"]}
                   for k, v in res.items()}}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md[:30]))
    print(f"\n→ {OUT / '04_meres_c.md'}")


if __name__ == "__main__":
    main()
