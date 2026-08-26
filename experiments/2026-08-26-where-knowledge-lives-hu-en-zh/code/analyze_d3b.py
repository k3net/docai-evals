#!/usr/bin/env python3
"""D3b ÚJRAMÉRÉS — a forrásnyelvi fogalom húz-e a SAJÁT angol közelítőszava felé?

    python3 src/analyze_d3b.py                       # base kör: results/ + results_d3b/
    SCOPE_RES=results_instruct SCOPE_REPORTS=reports_instruct SCOPE_D3B=results_d3b_instruct \\
        python3 src/analyze_d3b.py                   # instruct kör

A protokoll (d3b-protokoll.md, a futtatás ELŐTT rögzítve) minden döntést előír: réteg 10
(elsődleges) és 16 (másodlagos), a kérdés-tartomány feature-uniója (elsődleges) és a teljes
prompté (másodlagos), Jaccard, fogalmankénti többlet = J(saját közelítő) − átlag J(15 másik
közelítő), exakt kétoldali előjelteszt (elsődleges), Wilcoxon + fogalom-bootstrap CI
(másodlagos), hossz-illesztett változat (|Δ kérdés-token| ≤ 1, min. 3 pár), SESOI = +0,02.

⛔⛔ MIÉRT VAN EZ A SZKRIPT: az eredeti `analyze_d.py` D3b-je a KONTROLLSZÓ (`-ctrl`: help,
friendship…) promptját használta a közelítőszó helyett (2026-08-25-i bírálat, 1. blokkoló
pont). Az a számítás itt „szemantikai szomszéd” néven, összehasonlításul marad meg.

Minden szám a kódból jön; a riport szövegébe kézzel írt szám nem kerülhet.
"""
import json
import math
import os
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scope_paths

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(ROOT)
D3B = ROOT / (os.environ.get("SCOPE_D3B") or "results_d3b")
OUT = scope_paths.reports(ROOT)
LAYERS = (10, 16)
SESOI = 0.02
B_BOOT = 2000


def hn(x, nd=3):
    return f"{x:+.{nd}f}".replace(".", ",")


def sign_test(vals):
    pos = sum(1 for v in vals if v > 0)
    neg = sum(1 for v in vals if v < 0)
    n = pos + neg
    if n == 0:
        return 1.0, pos, neg
    k = min(pos, neg)
    p = 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, p), pos, neg


def wilcoxon_p(vals):
    try:
        from scipy.stats import wilcoxon
        v = [x for x in vals if x != 0]
        if len(v) < 6:
            return None
        return float(wilcoxon(v, zero_method="wilcox", alternative="two-sided").pvalue)
    except Exception:
        return None


def boot_ci(vals, seed=0):
    rng = np.random.default_rng(seed)
    a = np.asarray(vals)
    m = np.array([rng.choice(a, len(a), replace=True).mean() for _ in range(B_BOOT)])
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def jac(a, b):
    return len(a & b) / len(a | b) if (a | b) else 0.0


def load_spans(res):
    spans = {}
    f = res / "prompt_q_span.json"
    if f.exists():
        spans.update(json.loads(f.read_text(encoding="utf-8")))
    g = res / "gen.jsonl"
    if g.exists():
        for l in g.read_text(encoding="utf-8").splitlines():
            if l.strip():
                m = json.loads(l)
                if m.get("q_tok_span"):
                    spans[f"{m['item_id']}_{m['lang']}"] = m["q_tok_span"]
    return spans


def feat_union(res, spans, iid, lang, layer, span_only):
    z = np.load(res / "sae" / f"{iid}_{lang}.npz", allow_pickle=True)
    idx = z["idx"][layer]                    # [T, 50]
    T = idx.shape[0]
    if span_only:
        key = f"{iid}_{lang}"
        if key not in spans:
            raise SystemExit(f"nincs kérdés-tartomány: {key}")
        lo, hi = spans[key]
        idx = idx[lo:hi]
    return set(idx.reshape(-1).tolist()), (hi - lo if span_only else T)


def main():
    items = {}
    for l in (ROOT / "items.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            it = json.loads(l)
            if it["group"] == "UNT":
                items[it["id"]] = it
    ids = sorted(items)
    spans_src = load_spans(RES)
    spans_d3b = load_spans(D3B)
    approx_meta = {}
    for l in (D3B / "gen.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            m = json.loads(l)
            approx_meta[m["item_id"]] = m
    missing = [i for i in ids if f"{i}-approx" not in approx_meta]
    if missing:
        raise SystemExit(f"hiányzó közelítőszó-prompt: {missing}")

    md = [f"# D3b újramérés — a fogalom a SAJÁT angol közelítőszava felé húz? ({scope_paths.tag()})", "",
          f"Forrás-SAE: `{RES.name}/sae/` · közelítőszó-SAE: `{D3B.name}/sae/` · protokoll: `d3b-protokoll.md` "
          f"(a futtatás előtt rögzítve). Fogalmak: {len(ids)}. SESOI = {hn(SESOI, 2)} Jaccard.", "",
          "A 16 angol közelítőszó-prompt (a kontrollszó-prompt sablonjával):", ""]
    for i in ids:
        m = approx_meta[f"{i}-approx"]
        md.append(f"- `{i}` {items[i]['concept']} → *{m['prompt_text'].splitlines()[0]}*")
    md.append("")

    summary = {}
    for span_only in (True, False):
        for L in LAYERS:
            rows = []
            for i in ids:
                src = items[i]["src_lang"]
                s_src, _ = feat_union(RES, spans_src, i, src, L, span_only)
                own, n_own = feat_union(D3B, spans_d3b, f"{i}-approx", "en", L, span_only)
                j_own = jac(s_src, own)
                others, others_len = [], []
                for j in ids:
                    if j == i:
                        continue
                    o, n_o = feat_union(D3B, spans_d3b, f"{j}-approx", "en", L, span_only)
                    others.append(jac(s_src, o))
                    others_len.append(n_o)
                matched = [jo for jo, n_o in zip(others, others_len) if abs(n_o - n_own) <= 1]
                # az EREDETI (kontrollszavas) változat, összehasonlításul
                ctrl_own = jac(s_src, feat_union(RES, spans_src, f"{i}-ctrl", "en", L, span_only)[0])
                ctrl_oth = [jac(s_src, feat_union(RES, spans_src, f"{j}-ctrl", "en", L, span_only)[0])
                            for j in ids if j != i]
                # felső referencia: a fogalom SAJÁT angol kérdése (szó szerinti egyezéssel!)
                j_ownq = jac(s_src, feat_union(RES, spans_src, i, "en", L, span_only)[0])
                rows.append({"id": i, "concept": items[i]["concept"], "src": src, "n_tok": n_own,
                             "j_own": j_own, "j_oth": float(np.mean(others)), "excess": j_own - float(np.mean(others)),
                             "n_matched": len(matched),
                             "excess_matched": (j_own - float(np.mean(matched))) if len(matched) >= 3 else None,
                             "ctrl_excess": ctrl_own - float(np.mean(ctrl_oth)), "j_ownq": j_ownq})
            exc = [r["excess"] for r in rows]
            p_sign, pos, neg = sign_test(exc)
            p_w = wilcoxon_p(exc)
            lo, hi = boot_ci(exc)
            mean_exc = float(np.mean(exc))
            exm = [r["excess_matched"] for r in rows if r["excess_matched"] is not None]
            p_sign_m, pos_m, neg_m = sign_test(exm) if exm else (None, 0, 0)
            cexc = [r["ctrl_excess"] for r in rows]
            p_sign_c, pos_c, neg_c = sign_test(cexc)
            verdict = ("POZITÍV eredmény a protokoll szabálya szerint (a jel angol-specifikussága külön: 05_d3b_x_angol_specifikus.md)" if (p_sign < 0.05 and mean_exc >= SESOI)
                       else ("a mért pivot-hatás kisebb, mint a SESOI" if hi < SESOI
                             else "nincs pozitív evidencia (a CI a SESOI-t is tartalmazza)"))
            key = f"{'kérdés' if span_only else 'teljes prompt'} · {L}. réteg"
            summary[key] = {"layer": L, "span_only": span_only, "mean_excess": mean_exc, "ci": [lo, hi],
                            "sign_p": p_sign, "pos": pos, "neg": neg, "wilcoxon_p": p_w,
                            "matched_n": len(exm), "matched_sign_p": p_sign_m, "matched_pos": pos_m, "matched_neg": neg_m,
                            "matched_mean": float(np.mean(exm)) if exm else None,
                            "ctrl_mean_excess": float(np.mean(cexc)), "ctrl_sign_p": p_sign_c,
                            "ownq_mean": float(np.mean([r["j_ownq"] for r in rows])),
                            "own_mean": float(np.mean([r["j_own"] for r in rows])),
                            "verdict": verdict, "rows": rows}
            primary = " **(ELSŐDLEGES)**" if (span_only and L == LAYERS[0]) else ""
            md += [f"## {key}{primary}", "",
                   "| fogalom | forrás | kérdés-token | J(saját közelítő) | J(más közelítők, átlag) | többlet | "
                   "hossz-illesztett többlet (n) | kontrollszavas többlet (régi D3b) |",
                   "|---|---|---|---|---|---|---|---|"]
            for r in rows:
                em = (f"{hn(r['excess_matched'])} ({r['n_matched']})" if r["excess_matched"] is not None
                      else f"— ({r['n_matched']})")
                md.append(f"| {r['concept']} | {r['src']} | {r['n_tok']} | {r['j_own']:.3f} | {r['j_oth']:.3f} | "
                          f"**{hn(r['excess'])}** | {em} | {hn(r['ctrl_excess'])} |")
            md += ["",
                   f"- **Átlagos többlet: {hn(mean_exc)}**, fogalom-bootstrap 95% CI [{hn(lo)}; {hn(hi)}] · "
                   f"előjelteszt {pos} pozitív / {neg} negatív, p = {p_sign:.3f}"
                   + (f" · Wilcoxon p = {p_w:.3f}" if p_w is not None else "") + ".",
                   f"- Hossz-illesztett (|Δtoken| ≤ 1, ≥ 3 pár): n = {len(exm)} fogalom, átlag "
                   + (f"{hn(float(np.mean(exm)))}, előjelteszt {pos_m}/{neg_m}, p = {p_sign_m:.3f}." if exm else "—."),
                   f"- Ugyanez a RÉGI, kontrollszavas változattal (szemantikai szomszéd): átlag {hn(float(np.mean(cexc)))}, "
                   f"előjelteszt {pos_c}/{neg_c}, p = {p_sign_c:.3f}.",
                   f"- Műszer-referencia: J(forrás, saját angol KÉRDÉS) átlag {summary[key]['ownq_mean']:.3f} "
                   f"(szó szerinti egyezéssel), J(forrás, saját közelítő) átlag {summary[key]['own_mean']:.3f}.",
                   f"- **Döntés a protokoll szerint: {verdict}.**", ""]

    prim = summary[f"kérdés · {LAYERS[0]}. réteg"]
    md += ["## Összegzés", "",
           f"Az elsődleges elemzésben (kérdés-tartomány, {LAYERS[0]}. réteg) az átlagos többlet {hn(prim['mean_excess'])} "
           f"[{hn(prim['ci'][0])}; {hn(prim['ci'][1])}], előjelteszt p = {prim['sign_p']:.3f} → **{prim['verdict']}**. "
           "A többi (réteg × tartomány) változat fent; ha az irányuk eltér, az elsődleges dönt, a többi érzékenységi elemzés.", "",
           "⛔ Amit ez a teszt sem mér: elosztott, nem lexikális angol pivotot. A közelítőszó-prompt egyetlen "
           "angol megfogalmazás; a „nincs pozitív evidencia” nem a pivot hiányának bizonyítéka.", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "05_d3b_ujrameres.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "05_d3b_ujrameres.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {OUT / '05_d3b_ujrameres.md'}")
    for k, v in summary.items():
        print(f"  {k:26s} többlet {hn(v['mean_excess'])} CI [{hn(v['ci'][0])}; {hn(v['ci'][1])}] "
              f"sign {v['pos']}/{v['neg']} p={v['sign_p']:.3f} · régi(ctrl) {hn(v['ctrl_mean_excess'])} → {v['verdict']}")


if __name__ == "__main__":
    main()
