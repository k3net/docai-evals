#!/usr/bin/env python3
"""07 — Bírálati kiegészítés: három, a bírálati jelentés által hiányolt számítás (laptop, GPU nélkül).

    python3 src/analyze_extra.py
    python3 src/analyze_extra.py --allow-missing-sae   # csak ha tudod, mit írsz felül

Kimenet:
    reports/07_biralat_kiegeszites.md           — (1) a BASE kör SAE-adatán + (2) + (3)
    reports_instruct/07_biralat_kiegeszites.md  — (1) az INSTRUCT kör SAE-adatán + (2) + (3)

⚠️ Ez a szkript EGY futásban KÉT kör riportját írja, ezért a kimeneti könyvtárak fixek: a
`SCOPE_REPORTS` környezeti változó itt nem érvényesül (egyetlen érték nem tudná a két kört
szétválasztani). Ezért van őre: ld. `guard_overwrite()`.

A három számítás (a bírálati jelentés P1/P2 tételei):

(1) SAE „púp-alak" kontraszt (Mérés C, bírálat 8. pont). A `src/analyze_c.py` a 16. réteg
    ponttesztjét adja; itt az ELŐRE RÖGZÍTETT rétegsávok kontrasztját számoljuk itemenként:
        KORAI = 0–3. réteg átlaga · KÖZÉP = 8–12. · KÉSŐI = 28–31.
        kontraszt₁ = KÖZÉP − KORAI · kontraszt₂ = KÖZÉP − KÉSŐI   (a TÖBBLETEN)
    A többlet PONTOSAN az analyze_c.py módján: a kérdés-tokenek (`prompt_q_span.json`, [a,b))
    feature-UNIÓJA rétegenként; matched = Jaccard(item_i nyelv_a, item_i nyelv_b);
    véletlen párosítás = az ugyanazon csoport ÖSSZES rendezett (i, j), i≠j itempárjának
    Jaccard-átlaga (itertools.permutations); többlet_i = matched_i − véletlen (csoport-szintű
    konstans rétegenként). Itemenként bootstrap 95 % CI (2000×, seed 0), előjelteszt (pontos
    binomiális) és Wilcoxon (scipy).

(2) Item-klaszteres párosított próba a post-training pontosság-változásra (8. fejezet, bírálat
    9. pont). Ítélet = `manual`, ha nem üres, különben `judge`; helyes = 'helyes'. Előbb a
    dolgozat (item_id, lang)-szintű McNemar-számai reprodukálódnak, majd item-blokkos
    permutáció (az item 3 nyelvi címkéje EGYÜTT cserél kört = item-szintű előjelflip, 10 000×,
    seed 0; statisztika = javult − romlott) és item-szintű bootstrap 95 % CI a nettó javulásra.

(3) Hallucinációs átmeneti mátrix a HU-csoportra (8.2, bírálat 15. pont). 45 HU-válasz
    kategóriája a három körben; teljes páros átmeneti mátrix; csonkolatlan érzékenységi
    elemzés (`truncated == 0` mindkét körben); item-blokkos permutációs próba a „kitérés
    (= helytelen) darabszám-csökkenése" statisztikára.

⛔ Minden szám a kódból jön; a dolgozatbeli célértékek CSAK reprodukciós ellenőrzésként
szerepelnek (ha nem jönnek ki, a szkript jelzi, és nem igazít).
"""
import argparse
import csv
import datetime
import itertools
import json
import math
import pathlib

import numpy as np

from check_scores import derive

try:
    import scipy
    from scipy import stats as sstats
    SCIPY = scipy.__version__
except ImportError:                       # pragma: no cover
    scipy = None
    sstats = None
    SCIPY = None

HERE = pathlib.Path(__file__).resolve().parent.parent
ROUNDS = {                     # kulcs → (eredmény-könyvtár, riport-könyvtár, emberi címke)
    "base": (HERE / "results", HERE / "reports", "1. kör — Qwen3.5-9B-Base, nyers prompt"),
    "raw": (HERE / "results_instruct_raw", HERE / "reports_instruct_raw",
            "2. kör — Qwen3.5-9B (instruct), NYERS prompt"),
    "chat": (HERE / "results_instruct", HERE / "reports_instruct",
             "3. kör — Qwen3.5-9B (instruct), chat-sablon"),
}
GROUPS = ("ZH", "HU", "UNI")
LANGS = ("hu", "en", "zh")
PAIRS = (("zh", "en"), ("zh", "hu"), ("en", "hu"))      # azonos az analyze_c.py-vel
BANDS = {"KORAI": (0, 4), "KÖZÉP": (8, 13), "KÉSŐI": (28, 32)}   # félig nyitott [a, b)
N_BOOT = 2000
N_PERM = 10_000
SEED = 0
CATS = ("helyes", "reszben", "helytelen", "hallucinacio")

# ── a dolgozat számai — CSAK reprodukciós ellenőrzésre ──────────────────────
EXPECT_ACC = {"base": {"ZH": (42, 53, 63), "HU": (7, 13, 20), "UNI": (90, 100, 100)}}   # hu, en, zh, %
EXPECT_MCNEMAR = {"base→chat": (16, 4), "base→nyers": (9, 7), "nyers→chat": (13, 3)}
EXPECT_MCNEMAR_P = {"base→chat": 0.012}
EXPECT_HU = {"hallucinacio": (23, 26, 25), "helytelen": (14, 10, 3), "helyes+reszben": (8, 9, 17)}


# ═════════════════════════════════════════════════════════════════════════════
# közös segédek
# ═════════════════════════════════════════════════════════════════════════════
def binom_two_sided(k, n):
    """Pontos kétoldali binomiális p (p₀ = 0,5) — azonos a compare_rounds.py definíciójával."""
    if n == 0:
        return 1.0
    c = [math.comb(n, i) for i in range(n + 1)]
    tot = float(sum(c))
    obs = c[k]
    return min(1.0, sum(x for x in c if x <= obs + 1e-9) / tot)


def sign_test(vals):
    """Előjelteszt: a nullákat kihagyjuk; (n_pos, n_neg, p kétoldali)."""
    v = np.asarray(vals, dtype=float)
    pos, neg = int((v > 0).sum()), int((v < 0).sum())
    return pos, neg, binom_two_sided(min(pos, neg), pos + neg)


def wilcoxon_p(vals):
    v = np.asarray(vals, dtype=float)
    v = v[v != 0]
    if sstats is None or len(v) < 2:
        return float("nan")
    try:
        return float(sstats.wilcoxon(v, alternative="two-sided").pvalue)
    except ValueError:
        return float("nan")


def boot_ci_mean(vals, n=N_BOOT, seed=SEED):
    """Item-szintű bootstrap 95 % CI az átlagra — minden cellához FRISS, 0-seedelt RNG,
    hogy az eredmény a cellák sorrendjétől független legyen."""
    v = np.asarray(vals, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(v), size=(n, len(v)))
    means = v[idx].mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def boot_ci_sum(vals, n=N_BOOT, seed=SEED):
    lo, hi = boot_ci_mean(vals, n, seed)
    return lo * len(vals), hi * len(vals)


def perm_signflip(vals, n=N_PERM, seed=SEED):
    """Item-blokkos permutáció: minden item nettó értékének előjelét függetlenül flippeljük
    (= az item ÖSSZES nyelvi változata együtt cserél kört). Visszaad: (T_obs, p_kétoldali,
    p_egyoldali[T ≥ T_obs])."""
    v = np.asarray(vals, dtype=float)
    t_obs = float(v.sum())
    rng = np.random.default_rng(seed)
    signs = rng.choice(np.array([-1.0, 1.0]), size=(n, len(v)))
    t_perm = signs @ v
    p2 = (np.sum(np.abs(t_perm) >= abs(t_obs) - 1e-12) + 1) / (n + 1)
    p1 = (np.sum(t_perm >= t_obs - 1e-12) + 1) / (n + 1)
    return t_obs, float(p2), float(p1)


def holm(ps):
    ps = np.asarray(ps, dtype=float)
    m = len(ps)
    order = np.argsort(ps)
    adj = np.empty(m)
    prev = 0.0
    for rank, i in enumerate(order):
        a = min(1.0, max(prev, (m - rank) * ps[i]))
        adj[i] = a
        prev = a
    return adj


def fp(p):
    if p != p:
        return "n/a"
    return f"{p:.1e}" if p < 0.001 else f"{p:.3f}"


def mark(p):
    return " ✅" if p == p and p < 0.05 else ""


# ═════════════════════════════════════════════════════════════════════════════
# (1) SAE púp-kontraszt
# ═════════════════════════════════════════════════════════════════════════════
def jac(a, b):
    u = len(a | b)
    return len(a & b) / u if u else 0.0


def load_union_sets(res):
    """{item: {lang: [set/réteg]}} + {item: group} — a kérdés-tartomány feature-UNIÓJA,
    bitre az analyze_c.load_sets(span_mode='question') módján."""
    meta = [json.loads(l) for l in (res / "gen.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    spans = json.load(open(res / "prompt_q_span.json", encoding="utf-8"))
    data, groups, n_layers = {}, {}, None
    for m in meta:
        if m["kind"] != "fact":
            continue
        name = f"{m['item_id']}_{m['lang']}"
        z = np.load(res / "sae" / f"{name}.npz", allow_pickle=True)
        idx = z["idx"]                                   # [32, T, 50]
        layers = z["layers"]
        assert list(layers) == list(range(idx.shape[0])), f"{name}: a rétegindex nem 0..{idx.shape[0]-1}"
        a, b = spans[name]
        assert 0 <= a < b <= idx.shape[1], f"{name}: rossz tartomány {(a, b)} T={idx.shape[1]}"
        idx = idx[:, a:b, :]
        data.setdefault(m["item_id"], {})[m["lang"]] = [set(idx[L].reshape(-1).tolist())
                                                        for L in range(idx.shape[0])]
        groups[m["item_id"]] = m["group"]
        n_layers = idx.shape[0]
    return data, groups, n_layers


def hump_contrast(res, reports_dir):
    data, groups, L = load_union_sets(res)
    assert L >= 32, f"csak {L} réteg — a sávok 0..31-re vannak rögzítve"
    cjson = reports_dir / "04_meres_c.json"
    peaks_ref = json.loads(cjson.read_text(encoding="utf-8")).get("peaks", {}) if cjson.exists() else {}
    cells, repro = [], []
    for g in GROUPS:
        items = sorted(i for i in data if groups[i] == g)
        for a, b in PAIRS:
            matched = np.array([[jac(data[i][a][l], data[i][b][l]) for l in range(L)] for i in items])
            cross = np.array([[jac(data[i][a][l], data[j][b][l]) for l in range(L)]
                              for i, j in itertools.permutations(items, 2)]).mean(0)
            exc = matched - cross[None, :]                      # [n_item, L] — a TÖBBLET itemenként
            band = {k: exc[:, s:e].mean(1) for k, (s, e) in BANDS.items()}
            c1 = band["KÖZÉP"] - band["KORAI"]
            c2 = band["KÖZÉP"] - band["KÉSŐI"]
            row = {"group": g, "pair": f"{a}–{b}", "n": len(items),
                   "band_mean": {k: float(v.mean()) for k, v in band.items()}}
            for name, c in (("c1", c1), ("c2", c2)):
                lo, hi = boot_ci_mean(c)
                pos, neg, p_sign = sign_test(c)
                row[name] = {"mean": float(c.mean()), "ci": (lo, hi), "pos": pos, "neg": neg,
                             "p_sign": p_sign, "p_wilcoxon": wilcoxon_p(c)}
            cells.append(row)
            # reprodukció az analyze_c.py peaks-blokkjával (early = 0–2. réteg átlaga, peak = max)
            ref = peaks_ref.get(f"{g}/{a}-{b}")
            if ref:
                m = exc.mean(0)
                repro.append({"key": f"{g}/{a}-{b}", "early_ok": abs(m[:3].mean() - ref["early"]) < 1e-6,
                              "peak_ok": abs(m.max() - ref["peak"]) < 1e-6,
                              "early": float(m[:3].mean()), "early_ref": ref["early"],
                              "peak": float(m.max()), "peak_ref": ref["peak"]})
    for name in ("c1", "c2"):
        adj = holm([r[name]["p_wilcoxon"] for r in cells])
        for r, a in zip(cells, adj):
            r[name]["p_wilcoxon_holm"] = float(a)
    return cells, repro


def hump_md(label, cells, repro):
    md = [f"## (1) SAE púp-alak kontraszt — {label}", "",
          "**Képlet.** Rétegenként (0..31) a kérdés-tokenek feature-UNIÓJA; matchedᵢ(ℓ) = Jaccard az "
          "item két nyelvi változata között; véletlen(ℓ) = az ugyanazon csoport összes rendezett (i, j), "
          "i ≠ j itempárjának Jaccard-átlaga ugyanazon a nyelvpáron (`itertools.permutations`, mint az "
          "`analyze_c.py`-ben); többletᵢ(ℓ) = matchedᵢ(ℓ) − véletlen(ℓ). Sávok: KORAI = 0–3., KÖZÉP = 8–12., "
          "KÉSŐI = 28–31. réteg átlaga; kontraszt₁ = KÖZÉP − KORAI, kontraszt₂ = KÖZÉP − KÉSŐI itemenként. "
          f"CI: item-szintű bootstrap ({N_BOOT}×, seed {SEED}); előjelteszt: pontos kétoldali binomiális a "
          "nem-nulla különbségeken; Wilcoxon: `scipy.stats.wilcoxon` (kétoldali), Holm a 9 cellára "
          "kontrasztonként. ⛔ A 9 cella nem független replikáció (azonos itemek, modell, SAE).", ""]
    if repro:
        ok = all(r["early_ok"] and r["peak_ok"] for r in repro)
        md += [f"Reprodukció az `analyze_c.py` `peaks` blokkjával (early = 0–2. réteg, peak = max): "
               f"**{'OK — mind a ' + str(len(repro)) + ' cella bitre egyezik' if ok else '⛔ ELTÉRÉS'}**"
               + ("" if ok else " — " + "; ".join(
                   f"{r['key']}: early {r['early']:.4f} vs {r['early_ref']:.4f}, peak {r['peak']:.4f} vs "
                   f"{r['peak_ref']:.4f}" for r in repro if not (r["early_ok"] and r["peak_ok"]))), ""]
    md += ["### Sáv-átlagok a többleten", "",
           "| csoport | nyelvpár | n item | KORAI (0–3.) | KÖZÉP (8–12.) | KÉSŐI (28–31.) |",
           "|---|---|---|---|---|---|"]
    for r in cells:
        bm = r["band_mean"]
        md.append(f"| {r['group']} | {r['pair']} | {r['n']} | {bm['KORAI']:+.4f} | **{bm['KÖZÉP']:+.4f}** | "
                  f"{bm['KÉSŐI']:+.4f} |")
    for name, title in (("c1", "kontraszt₁ = KÖZÉP − KORAI"), ("c2", "kontraszt₂ = KÖZÉP − KÉSŐI")):
        md += ["", f"### {title}", "",
               "| csoport | nyelvpár | átlag | bootstrap 95 % CI | előjel (+/−) | p (előjel) | p (Wilcoxon) | p (Holm) |",
               "|---|---|---|---|---|---|---|---|"]
        for r in cells:
            c = r[name]
            lo, hi = c["ci"]
            star = " ✅" if lo > 0 else ""
            md.append(f"| {r['group']} | {r['pair']} | {c['mean']:+.4f} | [{lo:+.4f}, {hi:+.4f}]{star} | "
                      f"{c['pos']}/{c['neg']} | {fp(c['p_sign'])}{mark(c['p_sign'])} | "
                      f"{fp(c['p_wilcoxon'])}{mark(c['p_wilcoxon'])} | {fp(c['p_wilcoxon_holm'])}"
                      f"{mark(c['p_wilcoxon_holm'])} |")
    both = [r for r in cells if r["c1"]["ci"][0] > 0 and r["c2"]["ci"][0] > 0]
    only1 = [r for r in cells if r["c1"]["ci"][0] > 0 and not r["c2"]["ci"][0] > 0]
    only2 = [r for r in cells if r["c2"]["ci"][0] > 0 and not r["c1"]["ci"][0] > 0]
    neither = [r for r in cells if not r["c1"]["ci"][0] > 0 and not r["c2"]["ci"][0] > 0]
    both_holm = [r for r in cells if r["c1"]["p_wilcoxon_holm"] < 0.05 and r["c2"]["p_wilcoxon_holm"] < 0.05]
    fmt = lambda rs: ", ".join(f"{r['group']} {r['pair']}" for r in rs) or "–"
    md += ["", "### Összegzés — hány cellában „púp”?", "",
           f"- **Mindkét kontraszt CI-je pozitív (CI alsó széle > 0): {len(both)}/{len(cells)} cella** — {fmt(both)}.",
           f"- Csak KÖZÉP > KORAI: {len(only1)} — {fmt(only1)}.",
           f"- Csak KÖZÉP > KÉSŐI: {len(only2)} — {fmt(only2)}.",
           f"- Egyik sem: {len(neither)} — {fmt(neither)}.",
           f"- Holm-korrigált Wilcoxon p < 0,05 MINDKÉT kontrasztra: {len(both_holm)}/{len(cells)} — {fmt(both_holm)}.",
           "", "Olvasat: a „púp” állítás (a többlet a középső sávban nagyobb, mint a korai ÉS a késői sávban) "
           "csak abban a cellában áll, ahol mindkét kontraszt CI-je a nulla fölött van. Ahol csak a "
           "KÖZÉP − KÉSŐI pozitív, ott a görbe monoton csökkenő is lehet (a korai többlet már magas, pl. "
           "szó szerinti token-egyezés miatt), nem púp.", ""]
    return md


# ═════════════════════════════════════════════════════════════════════════════
# (2) item-klaszteres párosított próbák
# ═════════════════════════════════════════════════════════════════════════════
def load_scores(res):
    with (res / "scores.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {(r["item_id"], r["lang"]): r for r in rows}


def verdict(r):
    # A `final` származtatott oszlop; a forrás a `manual` és a `judge` (ld. check_scores.py).
    return derive(r)


def acc_matrix(S):
    out = {}
    for g in GROUPS:
        for l in LANGS:
            sub = [k for k in S if S[k]["group"] == g and S[k]["lang"] == l]
            out[(g, l)] = (sum(1 for k in sub if verdict(S[k]) == "helyes"), len(sub))
    return out


def paired_tests(S1, S2, keys):
    """Klaszterezetlen McNemar + item-blokkos permutáció + item-bootstrap."""
    up = {k: int(verdict(S1[k]) != "helyes" and verdict(S2[k]) == "helyes") for k in keys}
    dn = {k: int(verdict(S1[k]) == "helyes" and verdict(S2[k]) != "helyes") for k in keys}
    n_up, n_dn = sum(up.values()), sum(dn.values())
    p_mc = binom_two_sided(min(n_up, n_dn), n_up + n_dn)
    items = sorted({k[0] for k in keys})
    net = np.array([sum(up[k] - dn[k] for k in keys if k[0] == i) for i in items], dtype=float)
    t_obs, p2, p1 = perm_signflip(net)
    lo, hi = boot_ci_sum(net)
    n_disc_items = int((net != 0).sum())
    return {"n": len(keys), "n_items": len(items), "up": n_up, "dn": n_dn, "p_mcnemar": p_mc,
            "net": int(t_obs), "p_perm2": p2, "p_perm1": p1, "ci_net": (lo, hi),
            "ci_pp": (100 * lo / len(keys), 100 * hi / len(keys)), "n_disc_items": n_disc_items,
            "net_dist": {int(v): int((net == v).sum()) for v in sorted(set(net.tolist()))}}


def part2():
    S = {k: load_scores(ROUNDS[k][0]) for k in ("base", "raw", "chat")}
    keys = sorted(k for k in S["base"] if S["base"][k]["group"] in GROUPS)
    assert set(S["base"]) == set(S["raw"]) == set(S["chat"]), "a három kör itemhalmaza eltér"
    # ── reprodukció: pontossági mátrix ──
    acc = {k: acc_matrix(S[k]) for k in S}
    acc_ok = True
    acc_lines = []
    for g in GROUPS:
        got = tuple(round(100 * acc["base"][(g, l)][0] / acc["base"][(g, l)][1]) for l in LANGS)
        exp = EXPECT_ACC["base"][g]
        acc_ok &= got == exp
        acc_lines.append(f"| base **{g}** | " + " | ".join(f"{v} %" for v in got)
                         + f" | {' / '.join(str(v) + ' %' for v in exp)} | {'OK' if got == exp else '⛔ ELTÉR'} |")
    if not acc_ok:
        raise SystemExit("⛔ a base pontossági mátrix NEM reprodukálja a dolgozatot — megállok:\n"
                         + "\n".join(acc_lines))
    steps = (("base→chat", "base", "chat", "súlyok + promptozás együtt"),
             ("base→nyers", "base", "raw", "csak a súlyok (azonos nyers prompt)"),
             ("nyers→chat", "raw", "chat", "csak a promptozás (azonos súlyok)"))
    res = {}
    for name, a, b, what in steps:
        res[name] = {"all": paired_tests(S[a], S[b], keys), "what": what}
        for g in GROUPS:
            res[name][g] = paired_tests(S[a], S[b], [k for k in keys if S[a][k]["group"] == g])
    mc_ok = all((res[n]["all"]["up"], res[n]["all"]["dn"]) == EXPECT_MCNEMAR[n] for n in EXPECT_MCNEMAR)
    p_ok = all(round(res[n]["all"]["p_mcnemar"], 3) == EXPECT_MCNEMAR_P[n] for n in EXPECT_MCNEMAR_P)
    return S, keys, acc, acc_lines, res, mc_ok, p_ok


def part2_md(acc, acc_lines, res, mc_ok, p_ok):
    md = ["## (2) Item-klaszteres párosított próba a post-training pontosság-változásra", "",
          "**Képlet.** Ítélet = `manual`, ha nem üres, különben `judge`; helyes = `helyes`. "
          "Klaszterezetlen: McNemar a diszkordáns (item_id, lang) párokon, pontos kétoldali binomiális p "
          "(azonos a `compare_rounds.py`-vel). Klaszteres: itemenként nettó = javult − romlott a 3 nyelven "
          f"együtt; (a) item-blokkos permutáció — az item nettójának előjelét flippeljük ({N_PERM}×, seed "
          f"{SEED}), statisztika T = Σ nettó, p kétoldali = P(|T*| ≥ |T|); (b) item-szintű bootstrap "
          f"({N_BOOT}×, seed {SEED}) 95 % CI a nettó javulásra (darab és százalékpont a válaszok számára vetítve).", "",
          "### Reprodukció — pontossági mátrix (base kör, `manual`→`final`)", "",
          "| kör / csoport | hu | en | zh | dolgozat (hu / en / zh) | |", "|---|---|---|---|---|---|"]
    md += acc_lines
    md += ["", "A másik két kör (nem ellenőrzési cél, tájékoztatásul):", "",
           "| kör / csoport | hu | en | zh |", "|---|---|---|---|"]
    for rk, lab in (("raw", "instruct + nyers"), ("chat", "instruct + chat")):
        for g in GROUPS:
            md.append(f"| {lab} **{g}** | " + " | ".join(
                f"{100 * acc[rk][(g, l)][0] / acc[rk][(g, l)][1]:.0f} % ({acc[rk][(g, l)][0]}/{acc[rk][(g, l)][1]})"
                for l in LANGS) + " |")
    md += ["", "### Reprodukció — McNemar (item_id, lang) egységen", "",
           "| lépés | mi változik | javult | romlott | p (McNemar) | dolgozat |", "|---|---|---|---|---|---|"]
    for n in ("base→chat", "base→nyers", "nyers→chat"):
        r = res[n]["all"]
        exp = EXPECT_MCNEMAR[n]
        ok = (r["up"], r["dn"]) == exp
        md.append(f"| {n} | {res[n]['what']} | {r['up']} | {r['dn']} | {fp(r['p_mcnemar'])} | "
                  f"{exp[0]} / {exp[1]}" + (f", p = {EXPECT_MCNEMAR_P[n]:.3f}" if n in EXPECT_MCNEMAR_P else "")
                  + f" → {'OK' if ok else '⛔ ELTÉR'} |")
    md += ["", f"Reprodukció: javult/romlott **{'OK mindhárom lépésre' if mc_ok else '⛔ ELTÉRÉS'}**; "
           f"a dolgozat p = 0,012 értéke **{'OK' if p_ok else '⛔ ELTÉR'}**.", "",
           "### Klaszterezetlen és klaszteres p egymás mellett (mind a 162 válasz, 54 item)", "",
           "| lépés | javult | romlott | nettó | p McNemar (162 pár) | p permutáció (54 item-blokk) | "
           "bootstrap 95 % CI nettó (db) | CI (százalékpont) | itemek nettó ≠ 0 |",
           "|---|---|---|---|---|---|---|---|---|"]
    for n in ("base→chat", "base→nyers", "nyers→chat"):
        r = res[n]["all"]
        lo, hi = r["ci_net"]
        plo, phi = r["ci_pp"]
        md.append(f"| **{n}** | {r['up']} | {r['dn']} | {r['net']:+d} | {fp(r['p_mcnemar'])}{mark(r['p_mcnemar'])} | "
                  f"**{fp(r['p_perm2'])}**{mark(r['p_perm2'])} | [{lo:+.1f}, {hi:+.1f}] | [{plo:+.1f}, {phi:+.1f}] | "
                  f"{r['n_disc_items']}/{r['n_items']} |")
    md += ["", "Csoportonként (a klaszteres p itt még kisebb blokkszámon áll: ZH 19, HU 15, UNI 20 item):", "",
           "| lépés | csoport | javult | romlott | p McNemar | p permutáció | bootstrap CI nettó (db) |",
           "|---|---|---|---|---|---|---|"]
    for n in ("base→chat", "base→nyers", "nyers→chat"):
        for g in GROUPS:
            r = res[n][g]
            lo, hi = r["ci_net"]
            md.append(f"| {n} | {g} | {r['up']} | {r['dn']} | {fp(r['p_mcnemar'])}{mark(r['p_mcnemar'])} | "
                      f"{fp(r['p_perm2'])}{mark(r['p_perm2'])} | [{lo:+.1f}, {hi:+.1f}] |")
    md += ["", "Az itemenkénti nettó eloszlása (hány item mozdult ennyit a 3 nyelvén együtt):", "",
           "| lépés | " + " | ".join(f"nettó {v:+d}" for v in range(-3, 4)) + " |", "|---|" + "---|" * 7]
    for n in ("base→chat", "base→nyers", "nyers→chat"):
        d = res[n]["all"]["net_dist"]
        md.append(f"| {n} | " + " | ".join(str(d.get(v, 0)) for v in range(-3, 4)) + " |")
    md += ["", "Olvasat: a klaszteres p a bírálat 9. pontjának válasza — az item 3 nyelvi változata nem "
           "független megfigyelés. Ha a permutációs p is 0,05 alatt marad, az irány a pszeudoreplikáció "
           "kiszűrése után is áll; ha fölé megy, a dolgozat állítását ennek megfelelően kell gyengíteni.", ""]
    return md


# ═════════════════════════════════════════════════════════════════════════════
# (3) HU hallucinációs átmeneti mátrix
# ═════════════════════════════════════════════════════════════════════════════
def cat_counts(S, keys):
    c = {}
    for k in keys:
        v = verdict(S[k])
        c[v] = c.get(v, 0) + 1
    return c


def transition(S1, S2, keys, cats):
    M = {a: {b: 0 for b in cats} for a in cats}
    for k in keys:
        M[verdict(S1[k])][verdict(S2[k])] += 1
    return M


def kiteres_test(S1, S2, keys, cat="helytelen"):
    """Item-blokkos permutáció a „kategória darabszám-csökkenése" statisztikára:
    dᵢ = #cat(kör1, item i) − #cat(kör2, item i); T = Σ dᵢ; flip itemenként."""
    items = sorted({k[0] for k in keys})
    d = np.array([sum((verdict(S1[k]) == cat) - (verdict(S2[k]) == cat) for k in keys if k[0] == i)
                  for i in items], dtype=float)
    t_obs, p2, p1 = perm_signflip(d)
    lo, hi = boot_ci_sum(d)
    return {"t": int(t_obs), "p2": p2, "p1": p1, "ci": (lo, hi), "n_items": len(items),
            "n": len(keys)}


def part3(S):
    keys = sorted(k for k in S["base"] if S["base"][k]["group"] == "HU")
    cats = list(CATS) + sorted({verdict(S[r][k]) for r in S for k in keys} - set(CATS))
    counts = {r: cat_counts(S[r], keys) for r in ("base", "raw", "chat")}
    got = {"hallucinacio": tuple(counts[r].get("hallucinacio", 0) for r in ("base", "raw", "chat")),
           "helytelen": tuple(counts[r].get("helytelen", 0) for r in ("base", "raw", "chat")),
           "helyes+reszben": tuple(counts[r].get("helyes", 0) + counts[r].get("reszben", 0)
                                   for r in ("base", "raw", "chat"))}
    hu_ok = all(got[k] == EXPECT_HU[k] for k in EXPECT_HU)
    pairs = (("base→chat", "base", "chat"), ("nyers→chat", "raw", "chat"), ("base→nyers", "base", "raw"))
    out = {}
    for name, a, b in pairs:
        untr = [k for k in keys if S[a][k]["truncated"].strip() == "0" and S[b][k]["truncated"].strip() == "0"]
        out[name] = {
            "full": {"n": len(keys), "M": transition(S[a], S[b], keys, cats),
                     "c1": cat_counts(S[a], keys), "c2": cat_counts(S[b], keys),
                     "test_helytelen": kiteres_test(S[a], S[b], keys, "helytelen"),
                     "test_halluc": kiteres_test(S[a], S[b], keys, "hallucinacio")},
            "untr": {"n": len(untr), "n_items": len({k[0] for k in untr}), "M": transition(S[a], S[b], untr, cats),
                     "c1": cat_counts(S[a], untr), "c2": cat_counts(S[b], untr),
                     "test_helytelen": kiteres_test(S[a], S[b], untr, "helytelen") if untr else None,
                     "test_halluc": kiteres_test(S[a], S[b], untr, "hallucinacio") if untr else None},
        }
    trunc = {r: sum(1 for k in keys if S[r][k]["truncated"].strip() == "1") for r in ("base", "raw", "chat")}
    return keys, cats, counts, got, hu_ok, out, trunc


def matrix_md(M, cats, title):
    md = [f"**{title}** (sor: kiinduló kategória → oszlop: új kategória)", "",
          "| ↓ ebből \\ ebbe → | " + " | ".join(cats) + " | Σ sor |", "|---|" + "---|" * (len(cats) + 1)]
    for a in cats:
        row = [M[a][b] for b in cats]
        md.append(f"| **{a}** | " + " | ".join(f"**{v}**" if (a == b and v) else str(v) for v, b in zip(row, cats))
                  + f" | {sum(row)} |")
    md.append("| Σ oszlop | " + " | ".join(str(sum(M[a][b] for a in cats)) for b in cats)
              + f" | {sum(M[a][b] for a in cats for b in cats)} |")
    return md


def part3_md(keys, cats, counts, got, hu_ok, out, trunc):
    md = ["## (3) Hallucinációs átmeneti mátrix — HU-csoport (8.2)", "",
          "**Képlet.** A 45 HU-válasz (15 item × 3 nyelv) kategóriája körönként (ítélet = `manual`, "
          "különben `judge`). A dolgozat szótára: „magabiztos kitaláció” = `hallucinacio`; „kitérés / "
          "nem-válasz” = `helytelen`; „helyes vagy részben” = `helyes` + `reszben`. Átmeneti mátrix: "
          "ugyanazon válasz kategóriája a két körben. Csonkolatlan érzékenység: csak azok a válaszok, ahol "
          "`truncated == 0` MINDKÉT körben. Item-blokkos permutáció: dᵢ = #kategória(1. kör) − "
          f"#kategória(2. kör) az item 3 nyelvén együtt, T = Σ dᵢ, az item előjele flippel ({N_PERM}×, seed "
          f"{SEED}); p egyoldali = P(T* ≥ T) (a „csökken” irány), p kétoldali = P(|T*| ≥ |T|); bootstrap 95 % CI "
          f"a T-re ({N_BOOT}×, seed {SEED}).", "",
          "### Reprodukció — kategória-darabszámok a három körben", "",
          "| kategória | base + nyers | instruct + nyers | instruct + chat | dolgozat | |", "|---|---|---|---|---|---|"]
    for c in cats:
        md.append(f"| {c} | " + " | ".join(str(counts[r].get(c, 0)) for r in ("base", "raw", "chat")) + " | | |")
    for k in ("hallucinacio", "helytelen", "helyes+reszben"):
        lab = {"hallucinacio": "magabiztos kitaláció (= hallucinacio)", "helytelen": "kitérés / nem-válasz (= helytelen)",
               "helyes+reszben": "helyes vagy részben"}[k]
        ok = got[k] == EXPECT_HU[k]
        md.append(f"| **{lab}** | " + " | ".join(str(v) for v in got[k]) + " | "
                  + " → ".join(str(v) for v in EXPECT_HU[k]) + f" | {'OK' if ok else '⛔ ELTÉR'} |")
    md += [f"| csonkolt (`truncated = 1`) a 45-ből | " + " | ".join(str(trunc[r]) for r in ("base", "raw", "chat")) + " | | |",
           "", f"Reprodukció: **{'OK — a dolgozat mindhárom sora kijön' if hu_ok else '⛔ ELTÉRÉS — nem igazítottam, ld. a táblát'}**.", ""]
    for name in ("base→chat", "nyers→chat", "base→nyers"):
        o = out[name]
        md += [f"### {name}", ""]
        md += matrix_md(o["full"]["M"], cats, f"Teljes (n = {o['full']['n']})") + [""]
        u = o["untr"]
        md += matrix_md(u["M"], cats, f"Csonkolatlan érzékenység — `truncated = 0` mindkét körben "
                                       f"(n = {u['n']} válasz, {u['n_items']} item)") + [""]
        md += ["| statisztika | minta | T = Σ dᵢ (csökkenés) | p egyoldali (csökken) | p kétoldali | bootstrap 95 % CI |",
               "|---|---|---|---|---|---|"]
        for cat, lab in (("test_helytelen", "kitérés (`helytelen`) darabszám-csökkenése"),
                         ("test_halluc", "kitaláció (`hallucinacio`) darabszám-csökkenése")):
            for samp, slab in (("full", "teljes"), ("untr", "csonkolatlan")):
                t = o[samp][cat]
                if t is None:
                    md.append(f"| {lab} | {slab} | – | – | – | – |")
                    continue
                lo, hi = t["ci"]
                small = " ⚠️" if t["n_items"] < 10 else ""
                md.append(f"| {lab} | {slab} (n = {t['n']}, {t['n_items']} item){small} | {t['t']:+d} | "
                          f"{fp(t['p1'])}{mark(t['p1'])} | {fp(t['p2'])}{mark(t['p2'])} | [{lo:+.1f}, {hi:+.1f}] |")
        smalls = [o[s]["test_helytelen"]["n_items"] for s in ("full", "untr") if o[s]["test_helytelen"]]
        if any(n < 10 for n in smalls):
            n_min = min(n for n in smalls if n < 10)
            md.append(f"\n⚠️ {n_min} item-blokk mellett az előjelflip-permutációnak csak 2^{n_min} = {2 ** n_min} "
                      "különböző mintázata van, a percentilis bootstrap pedig durva: a CI és a p ott "
                      "egymásnak ellent is mondhat — a kis részmintán a mátrix iránya olvasandó, nem a próba.")
        md.append("")
    bc = out["base→chat"]
    md += ["Olvasat: a mátrix mutatja, hova KERÜLT a base kör kitérése (a `helytelen` sor oszlopai) — ha "
           "zöme a `hallucinacio` oszlopba, a „kitérés → magabiztos kitaláció” átalakulás; ha a `helyes`/"
           "`reszben` oszlopba, valódi javulás. A csonkolatlan részminta a bírálat felvetését teszteli: "
           "a kitérés eltűnése nem a levágott bizonytalankodó folytatás műterméke-e. ⛔ A csonkolatlan "
           f"részminta kicsi (base→chat: {bc['untr']['n']} válasz), ezért ott a p-érték ereje korlátozott; "
           "a mátrix-irány az informatív.", ""]
    return md


# ═════════════════════════════════════════════════════════════════════════════
STUB_MARK = "Nem értelmezhető: ehhez a körhöz nincs SAE-futás"


def guard_overwrite(path, has_sae, allow):
    """⛔⛔ Néma riport-rombolás elleni őr.

    Az (1) szakaszhoz a kör SAE-kimenete kell (`sae/*.npz` + `prompt_q_span.json`). Ez a
    publikált másolatban SZÁNDÉKOSAN nincs benne (78 MB, a promptokból regenerálható), a
    szkript viszont ilyenkor is lefutott, és a teljes (1) szakasz helyére egyetlen
    „Nem értelmezhető” sort írt — a meglévő, ÉRVÉNYES riportot felülírva. 2026-08-26-án
    élesben megtörtént: két riport 58 sora veszett el egy ártatlan futásból.

    Az őr csak akkor enged, ha az adat megvan, vagy ha nincs mit elveszíteni (a fájl nem
    létezik, vagy a meglévő is stub). A `--allow-missing-sae` a szándékos kivétel.
    """
    if has_sae or allow or not path.exists():
        return
    if STUB_MARK in path.read_text(encoding="utf-8"):
        return                      # a meglévő is stub → a felülírás nem veszít semmit
    raise SystemExit(
        f"⛔ {path} — a meglévő riport TELJES (1) szakaszt tartalmaz, ez a futás viszont csak\n"
        f"   stubot tudna írni: hiányzik a kör SAE-kimenete (`sae/` + `prompt_q_span.json`).\n"
        f"   A futás megszakadt, a fájl érintetlen.\n\n"
        f"   Vagy futtasd ott, ahol az SAE-adat megvan (a mérési munkapéldány), vagy ha tényleg\n"
        f"   stubra akarod cserélni: python3 src/analyze_extra.py --allow-missing-sae")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--allow-missing-sae", action="store_true",
                    help="engedi, hogy SAE-adat híján a teljes (1) szakasz stubra cserélődjön")
    args = ap.parse_args()

    # ⛔ FAIL-FAST: az őr MINDEN érintett kimenetre lefut, mielőtt bármit számolnánk —
    # így egy elutasított futás nem hagy félig frissített riport-párt sem.
    targets = []
    for rk, rep_dir in (("base", HERE / "reports"), ("chat", HERE / "reports_instruct")):
        res_dir = ROUNDS[rk][0]
        has_sae = (res_dir / "sae").exists() and (res_dir / "prompt_q_span.json").exists()
        guard_overwrite(rep_dir / "07_biralat_kiegeszites.md", has_sae, args.allow_missing_sae)
        targets.append((rk, rep_dir, ROUNDS[rk][2], has_sae))

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    S, keys, acc, acc_lines, res2, mc_ok, p_ok = part2()
    hu_keys, cats, counts, got, hu_ok, out3, trunc = part3(S)
    md2 = part2_md(acc, acc_lines, res2, mc_ok, p_ok)
    md3 = part3_md(hu_keys, cats, counts, got, hu_ok, out3, trunc)

    summary = {}
    for rk, rep_dir, label, has_sae in targets:
        res_dir = ROUNDS[rk][0]
        head = ["# 07 — Bírálati kiegészítés: púp-kontraszt · item-klaszteres próbák · HU átmeneti mátrix", "",
                f"Futás: **{now}** (rendszeridő) · `src/analyze_extra.py` · numpy {np.__version__}"
                f"{' · scipy ' + SCIPY if SCIPY else ' · scipy NINCS (előjelteszt kézzel, Wilcoxon n/a)'}. "
                "Kizárólag a meglévő mérési adatból (GPU nélkül); minden szám a kódból jön, a dolgozat "
                "értékei csak reprodukciós ellenőrzésként szerepelnek.", "",
                f"Ez a fájl: az (1) mérés **ezen kör** SAE-adatán ({label}); a (2)–(3) mérés a három kört "
                "együtt veti össze, ezért mindkét riportban azonos.", "", "---", ""]
        if has_sae:
            cells, repro = hump_contrast(res_dir, rep_dir)
            md1 = hump_md(label, cells, repro)
            summary[rk] = cells
        else:
            md1 = [f"## (1) SAE púp-alak kontraszt — {label}", "",
                   "Nem értelmezhető: ehhez a körhöz nincs SAE-futás (`sae/` + `prompt_q_span.json`).", ""]
        text = "\n".join(head + md1 + ["---", ""] + md2 + ["---", ""] + md3) + "\n"
        rep_dir.mkdir(exist_ok=True)
        (rep_dir / "07_biralat_kiegeszites.md").write_text(text, encoding="utf-8")
        print(f"→ {rep_dir / '07_biralat_kiegeszites.md'}")

    # ── kulcsszámok a konzolra ──
    print("\n== Reprodukció ==")
    print(f"pontossági mátrix (base): OK · McNemar javult/romlott: {'OK' if mc_ok else 'ELTÉR'} · "
          f"p=0,012: {'OK' if p_ok else 'ELTÉR'} · HU kategóriák: {'OK' if hu_ok else 'ELTÉR'} {got}")
    print("\n== (1) púp-kontraszt: cellánként [c1 CI] [c2 CI] ==")
    for rk, cells in summary.items():
        both = sum(1 for r in cells if r["c1"]["ci"][0] > 0 and r["c2"]["ci"][0] > 0)
        print(f"-- {rk}: mindkét CI > 0: {both}/{len(cells)}")
        for r in cells:
            c1, c2 = r["c1"], r["c2"]
            print(f"  {r['group']:3} {r['pair']:5} c1 {c1['mean']:+.4f} [{c1['ci'][0]:+.4f},{c1['ci'][1]:+.4f}] "
                  f"pW={fp(c1['p_wilcoxon'])} | c2 {c2['mean']:+.4f} [{c2['ci'][0]:+.4f},{c2['ci'][1]:+.4f}] "
                  f"pW={fp(c2['p_wilcoxon'])}")
    print("\n== (2) klaszterezetlen vs klaszteres ==")
    for n in ("base→chat", "base→nyers", "nyers→chat"):
        r = res2[n]["all"]
        print(f"  {n:11} {r['up']:2d}/{r['dn']:2d} nettó {r['net']:+d}  McNemar p={fp(r['p_mcnemar'])}  "
              f"perm p={fp(r['p_perm2'])}  boot CI [{r['ci_net'][0]:+.1f},{r['ci_net'][1]:+.1f}]")
    print("\n== (3) HU átmeneti mátrixok ==")
    for n in ("base→chat", "nyers→chat"):
        o = out3[n]
        print(f"-- {n} (teljes n={o['full']['n']}; csonkolatlan n={o['untr']['n']})")
        for a in cats:
            print(f"  {a:12} → " + "  ".join(f"{b}:{o['full']['M'][a][b]}" for b in cats)
                  + "   | csonkolatlan: " + "  ".join(f"{b}:{o['untr']['M'][a][b]}" for b in cats))
        t, tu = o["full"]["test_helytelen"], o["untr"]["test_helytelen"]
        print(f"  kitérés-csökkenés T={t['t']:+d} p1={fp(t['p1'])} p2={fp(t['p2'])} CI [{t['ci'][0]:+.1f},{t['ci'][1]:+.1f}]"
              + (f" | csonkolatlan T={tu['t']:+d} p1={fp(tu['p1'])} p2={fp(tu['p2'])}" if tu else ""))


if __name__ == "__main__":
    main()
