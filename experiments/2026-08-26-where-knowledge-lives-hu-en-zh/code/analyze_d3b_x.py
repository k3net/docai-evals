#!/usr/bin/env python3
"""D3b kiegészítés — ANGOL-specifikus-e a közelítő felé húzó jel? (d3b-protokoll.md, kiegészítés)

    python3 src/analyze_d3b_x.py                    # base: results/ + results_d3b/ + results_d3b_x/

Páros összevetés fogalmanként: J(forrás, ANGOL közelítő) − J(forrás, HARMADIK nyelvű közelítő).
  H_R2 (angol pivot):     a különbség pozitív.
  H_R3 (nyelvfüggetlen):  a különbség 0 körül.
Torzítás-kontroll (különbség a különbségben): ugyanez a meglévő KONTROLLSZÓ-promptokkal
(`-ctrl` en vs. `-ctrl` harmadik nyelv) — ha a kínai/magyar prompt pusztán a rövidebb
kérdés vagy a nyelv miatt ad más Jaccard-ot, az a kontrollpáron is megjelenik.

⚠️ FELTÁRÓ elemzés: a protokollnak ez a része az elsődleges eredmény megtekintése UTÁN íródott.
Minden szám a kódból jön.
"""
import json
import os
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import scope_paths
from analyze_d3b import boot_ci, feat_union, hn, jac, load_spans, sign_test, wilcoxon_p

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = scope_paths.res(ROOT)
D3B = ROOT / (os.environ.get("SCOPE_D3B") or "results_d3b")
D3BX = ROOT / (os.environ.get("SCOPE_D3BX") or "results_d3b_x")
OUT = scope_paths.reports(ROOT)
LAYERS = (10, 16)
SESOI = 0.02


def main():
    items = {}
    for l in (ROOT / "items.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            it = json.loads(l)
            if it["group"] == "UNT":
                items[it["id"]] = it
    ids = sorted(items)
    sp_src, sp_en, sp_x = load_spans(RES), load_spans(D3B), load_spans(D3BX)
    xmeta = {}
    for l in (D3BX / "gen.jsonl").read_text(encoding="utf-8").splitlines():
        if l.strip():
            m = json.loads(l)
            xmeta[m["item_id"]] = m

    md = [f"# D3b kiegészítés — angol-specifikus a vonzás? ({scope_paths.tag()})", "",
          "Páros különbség fogalmanként: J(forrás, ANGOL közelítő) − J(forrás, HARMADIK nyelvű közelítő); "
          "kontroll-pár: ugyanez a kontrollszó-promptokkal. ⚠️ Feltáró (a protokoll kiegészítése az elsődleges "
          f"eredmény után). SESOI = {hn(SESOI, 2)}.", ""]
    summary = {}
    for span_only in (True, False):
        for L in LAYERS:
            rows = []
            for i in ids:
                src = items[i]["src_lang"]
                third = xmeta[f"{i}-approx"]["lang"]
                assert third != src and third != "en"
                s_src, _ = feat_union(RES, sp_src, i, src, L, span_only)
                j_en, n_en = feat_union(D3B, sp_en, f"{i}-approx", "en", L, span_only)
                j_x, n_x = feat_union(D3BX, sp_x, f"{i}-approx", third, L, span_only)
                c_en, _ = feat_union(RES, sp_src, f"{i}-ctrl", "en", L, span_only)
                c_x, _ = feat_union(RES, sp_src, f"{i}-ctrl", third, L, span_only)
                d_approx = jac(s_src, j_en) - jac(s_src, j_x)
                d_ctrl = jac(s_src, c_en) - jac(s_src, c_x)
                # a HARMADIK nyelvű közelítőn belüli „saját − mások” többlet: csak az azonos nyelvű
                # (ugyanabba a harmadik nyelvbe fordított) többi fogalom közelítőjével összevetve
                others_x = [jac(s_src, feat_union(D3BX, sp_x, f"{j}-approx", third, L, span_only)[0])
                            for j in ids if j != i and xmeta[f"{j}-approx"]["lang"] == third]
                excess_x = jac(s_src, j_x) - float(np.mean(others_x))
                rows.append({"concept": items[i]["concept"], "src": src, "third": third,
                             "phrase": xmeta[f"{i}-approx"]["meta"].get("third_phrase", "") if isinstance(xmeta[f"{i}-approx"].get("meta"), dict) else "",
                             "n_en": n_en, "n_x": n_x,
                             "j_en": jac(s_src, j_en), "j_x": jac(s_src, j_x), "d_approx": d_approx,
                             "c_en": jac(s_src, c_en), "c_x": jac(s_src, c_x), "d_ctrl": d_ctrl,
                             "dd": d_approx - d_ctrl, "excess_x": excess_x, "n_others_x": len(others_x)})
            da = [r["d_approx"] for r in rows]
            dc = [r["d_ctrl"] for r in rows]
            dd = [r["dd"] for r in rows]
            pa, posa, nega = sign_test(da)
            pc, posc, negc = sign_test(dc)
            pd_, posd, negd = sign_test(dd)
            loa, hia = boot_ci(da)
            lod, hid = boot_ci(dd)
            ex = [r["excess_x"] for r in rows]
            pex, posex, negex = sign_test(ex)
            loex, hiex = boot_ci(ex)
            key = f"{'kérdés' if span_only else 'teljes prompt'} · {L}. réteg"
            verdict = ("az angol közelítő felé ERŐSEBB a vonzás (angol-specifikus jel)" if (pd_ < 0.05 and float(np.mean(dd)) >= SESOI)
                       else ("a vonzás NEM angol-specifikus (a különbség-a-különbségben a SESOI alatt)" if hid < SESOI
                             else "eldöntetlen (a CI a nullát és a SESOI-t is tartalmazza)"))
            summary[key] = {"mean_d_approx": float(np.mean(da)), "ci_approx": [loa, hia], "sign_approx": [posa, nega], "p_approx": pa,
                            "wilcoxon_approx": wilcoxon_p(da),
                            "mean_d_ctrl": float(np.mean(dc)), "sign_ctrl": [posc, negc], "p_ctrl": pc,
                            "mean_dd": float(np.mean(dd)), "ci_dd": [lod, hid], "sign_dd": [posd, negd], "p_dd": pd_,
                            "mean_excess_x": float(np.mean(ex)), "ci_excess_x": [loex, hiex], "sign_excess_x": [posex, negex], "p_excess_x": pex,
                            "verdict": verdict, "rows": rows}
            primary = " **(ELSŐDLEGES)**" if (span_only and L == LAYERS[0]) else ""
            md += [f"## {key}{primary}", "",
                   "| fogalom | forrás | harmadik | token en/3. | J(en közelítő) | J(3. nyelvű közelítő) | Δ közelítő | Δ kontrollszó | Δ−Δ |",
                   "|---|---|---|---|---|---|---|---|---|"]
            for r in rows:
                md.append(f"| {r['concept']} | {r['src']} | {r['third']} | {r['n_en']}/{r['n_x']} | {r['j_en']:.3f} | {r['j_x']:.3f} | "
                          f"**{hn(r['d_approx'])}** | {hn(r['d_ctrl'])} | {hn(r['dd'])} |")
            md += ["",
                   f"- Δ közelítő (angol − harmadik): átlag **{hn(float(np.mean(da)))}** [{hn(loa)}; {hn(hia)}], előjel {posa}/{nega}, p = {pa:.3f}"
                   + (f", Wilcoxon p = {summary[key]['wilcoxon_approx']:.3f}" if summary[key]['wilcoxon_approx'] is not None else "") + ".",
                   f"- Δ kontrollszó (angol − harmadik, meglévő `-ctrl` promptok): átlag {hn(float(np.mean(dc)))}, előjel {posc}/{negc}, p = {pc:.3f} "
                   "(ez a nyelv/hossz miatti alap-eltolódás).",
                   f"- **Különbség a különbségben:** átlag **{hn(float(np.mean(dd)))}** [{hn(lod)}; {hn(hid)}], előjel {posd}/{negd}, p = {pd_:.3f}.",
                   f"- A HARMADIK nyelvű közelítőn belül a „saját − a többi (azonos nyelvű, n = {rows[0]['n_others_x']}) közelítő” többlet: "
                   f"átlag **{hn(float(np.mean(ex)))}** [{hn(loex)}; {hn(hiex)}], előjel {posex}/{negex}, p = {pex:.3f} "
                   "(ha ez is pozitív, a fogalom a saját közelítője felé húz a harmadik nyelven is).",
                   f"- **Olvasat: {verdict}.**", ""]
    prim = summary[f"kérdés · {LAYERS[0]}. réteg"]
    md += ["## Összegzés", "",
           f"Harmadik nyelvű saját-többlet (kérdés, {LAYERS[0]}. réteg): {hn(prim['mean_excess_x'])} "
           f"[{hn(prim['ci_excess_x'][0])}; {hn(prim['ci_excess_x'][1])}], p = {prim['p_excess_x']:.3f}.", "",
           f"Elsődleges (kérdés, {LAYERS[0]}. réteg): Δ közelítő {hn(prim['mean_d_approx'])} "
           f"[{hn(prim['ci_approx'][0])}; {hn(prim['ci_approx'][1])}] (p = {prim['p_approx']:.3f}); "
           f"a kontrollszó-pár alap-eltolódása {hn(prim['mean_d_ctrl'])}; különbség a különbségben "
           f"{hn(prim['mean_dd'])} [{hn(prim['ci_dd'][0])}; {hn(prim['ci_dd'][1])}] (p = {prim['p_dd']:.3f}) → **{prim['verdict']}**.", ""]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "05_d3b_x_angol_specifikus.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "05_d3b_x_angol_specifikus.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"→ {OUT / '05_d3b_x_angol_specifikus.md'}")
    for k, v in summary.items():
        print(f"  {k:26s} Δapprox {hn(v['mean_d_approx'])} p={v['p_approx']:.3f} · Δctrl {hn(v['mean_d_ctrl'])} · 3.ny-többlet {hn(v['mean_excess_x'])} p={v['p_excess_x']:.3f} · "
              f"Δ−Δ {hn(v['mean_dd'])} [{hn(v['ci_dd'][0])}; {hn(v['ci_dd'][1])}] p={v['p_dd']:.3f} → {v['verdict']}")


if __name__ == "__main__":
    main()
