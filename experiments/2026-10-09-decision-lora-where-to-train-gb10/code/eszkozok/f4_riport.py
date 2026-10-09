"""F4 — az eredménylap kitöltése (runbook 14. pont) az f4_elemzes.py és az f4_h3.py kimenetéből.

Bemenet: eredmenyek/F4/{vllm_f4.json, hf_f4.json, h3.json}, a bennük rögzített kiolvasás-fájlok (pozíció-billenés,
címketömeg), az F1 címke-átnézés összesítése (címkezaj rétegenként) és a K0c kapuja.
Kimenet: eredmenyek/F4/eredmenylap.md (+ eredmenylap.json a javítatlan teszten mért érzékenységgel).

Az L3 sorai a három seed átlagát mutatják, zárójelben a seedek tartományával. A hipotézis-ítéletek az előre rögzített
szabályok szerint (runbook 3. pont); a H6 nem tesztelhető, mert az F5 nem futott.

  python3 eszkozok/f4_riport.py --dir eredmenyek/F4
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import FAIL_BELOW, TEST_STRATA, VAL_STRATA, _p  # noqa: E402
from f4_elemzes import load_arm, point_block  # noqa: E402

STRATA = [("T-belso", "T-belső"), ("T-szallito", "T-szállító"), ("T-kozeli", "T-közeli"), ("T-tavoli", "T-távoli"),
          ("pool", "pool")]


def fmt(x, nd: int = 3) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:.{nd}f}".replace(".", ",")


def block(pt: dict, stratum: str) -> dict:
    b = pt["95"]
    return b["teszt"] if stratum == "pool" else b["retegek"].get(stratum, {})


def readout_diag(path: str, meta_split: dict) -> dict:
    """Rétegenként: pozíció-billenés (a 4 permutáció közt a döntött opció változik-e) és átlagos címketömeg (perm 0)."""
    rows = read_jsonl(_p(path))
    by = defaultdict(dict)
    for r in rows:
        lab = max(r["label_logprobs"], key=r["label_logprobs"].get)
        by[r["id"]][r["perm"]] = (None if lab == "X" else r["order"][r["labels"].index(lab)], r.get("label_mass"))
    out = {}
    for s, _ in STRATA:
        ids = [i for i in by if (s == "pool" and meta_split.get(i) in TEST_STRATA) or meta_split.get(i) == s]
        multi = [i for i in ids if len(by[i]) > 1]
        flip = np.mean([len({v[0] for v in by[i].values()}) > 1 for i in multi]) if multi else None
        mass = [by[i][0][1] for i in ids if 0 in by[i] and by[i][0][1] is not None]
        out[s] = {"billenes": float(flip) if flip is not None else None, "cimketomeg": float(np.mean(mass)) if mass else None}
    return out


def load_meta_pre(items_dir: Path) -> dict:
    """Mint az elemzes.load_meta, de ahol van átnézés előtti mentés, azt olvassa (javítatlan gold)."""
    meta = {}
    files = sorted(items_dir.glob("items_*.jsonl"))
    for f in files:
        if ".pre_atnezes" in f.name:
            continue
        pre = f.with_name(f.stem + ".pre_atnezes.jsonl")
        for it in read_jsonl(pre if pre.exists() else f):
            meta[it["id"]] = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None, **it["meta"]}
    return meta


def sensitivity(res: dict, items: str) -> dict:
    """Javítatlan teszten (érzékenység): pontbecslés az átnézés előtti goldokkal, ugyanazokkal a kiolvasásokkal."""
    meta = load_meta_pre(_p(items))
    a = res["bemenetek"]
    l1, _ = load_arm(a["l0_val"], a["l0_test"], meta, "perm_avg")
    val_ids = [i for i in l1 if meta[i]["split"] in VAL_STRATA]
    test_ids = [i for i in l1 if meta[i]["split"] in TEST_STRATA]
    out = {"L1csillag": point_block(l1, meta, val_ids, test_ids)["95"]["teszt"]}
    for spec in a["l3"]:
        name, v, t = spec.split(":")
        p, _ = load_arm(v, t, meta, "temp")
        out[f"L3_{name}"] = point_block(p, meta, val_ids, test_ids)["95"]["teszt"]
    return {k: {m: v.get(m) for m in ("besorolasi_lefedettseg", "besorolasi_precizitas", "aurc")} for k, v in out.items()}


def engine_table(res: dict, h3: dict | None, items: str) -> list[str]:
    from elemzes import load_meta
    meta = load_meta(_p(items))
    split = {i: m["split"] for i, m in meta.items()}
    a = res["bemenetek"]
    pt = res["pont"]
    seeds = [k for k in pt if k.startswith("L3_")]
    diag_l0 = readout_diag(a["l0_test"], split)
    diag_l3 = [readout_diag(spec.split(":")[2], split) for spec in a["l3"]]
    perf = (h3 or {}).get("teljesitmeny", {})
    dps = {"L0": perf.get("b_lora_peldany_lora_nelkul", {}).get("1", {}).get("dontes_per_s"),
           "L3": perf.get("c_lora_request", {}).get("1", {}).get("dontes_per_s")} if res["motor"] == "vllm" else {}
    lines = []
    for s, sname in STRATA:
        lines += [f"**{sname}**", "",
                  "| fok / kar | besorolási lef@95 | elért precizitás | AURC | döntési lef@95 | X-prec / X-fedés | ECE "
                  "| kétértelmű-átlépés | pozíció-billenés | címketömeg | döntés/s |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]

        def row(label, b, diag, d_s):
            prec = b.get("besorolasi_precizitas")
            bukas = " ⚠" if prec is not None and prec < FAIL_BELOW["95"] else ""
            return (f"| {label} | {fmt(b.get('besorolasi_lefedettseg'))} | {fmt(prec)}{bukas} "
                    f"| {fmt(b.get('aurc'), 4)} | {fmt(b.get('dontesi_lefedettseg'))} "
                    f"| {fmt(b.get('x_precizitas'))} / {fmt(b.get('x_fedes'))} | {fmt(b.get('ece'))} "
                    f"| {fmt(b.get('ketertelmu_atlepes'))} | {fmt(diag.get('billenes') if diag else None)} "
                    f"| {fmt(diag.get('cimketomeg') if diag else None)} | {fmt(d_s, 1)} |")
        lines.append(row("L0", block(pt["L0"], s), diag_l0[s], dps.get("L0")))
        # a permutáció-átlag a pozíciófüggést definíció szerint kiátlagolja: billenése nincs, csak a címketömeg
        lines.append(row("L1★ (perm. átlag + temperature)", block(pt["L1csillag"], s),
                         {"billenes": None, "cimketomeg": diag_l0[s]["cimketomeg"]},
                         dps["L0"] / 4 if dps.get("L0") else None))
        if "L2a" in pt:
            lines.append(row("L2a (40. réteg)", block(pt["L2a"], s), None, None))
        bs = [block(pt[k], s) for k in seeds]
        keys = ["besorolasi_lefedettseg", "besorolasi_precizitas", "aurc", "dontesi_lefedettseg", "x_precizitas", "x_fedes",
                "ece", "ketertelmu_atlepes"]
        mean = {k: float(np.mean([b[k] for b in bs if b.get(k) is not None])) if any(b.get(k) is not None for b in bs)
                else None for k in keys}
        dmean = {"billenes": np.mean([d[s]["billenes"] for d in diag_l3 if d[s]["billenes"] is not None])
                 if any(d[s]["billenes"] is not None for d in diag_l3) else None,
                 "cimketomeg": np.mean([d[s]["cimketomeg"] for d in diag_l3 if d[s]["cimketomeg"] is not None])
                 if any(d[s]["cimketomeg"] is not None for d in diag_l3) else None}
        lef = [x for x in (b.get("besorolasi_lefedettseg") for b in bs) if x is not None]
        rng = f" [{fmt(min(lef))}–{fmt(max(lef))}]" if len(lef) == len(bs) else ""
        lines.append(row(f"L3 (`temp`, {len(bs)} seed átlaga; lef@95{rng})", mean, dmean, dps.get("L3")))
        lines.append("")
    lines += ["⚠ = precizitás-bukás (a teszten elért precizitás < 0,93). Az AURC a kar saját nem-X döntéseinek görbéjén "
              "számolódik, így a több X-et mondó kar rövidebb görbét kap; a közös lefedettségre vágott változat az "
              "önellenőrzés szakaszban. Az L1★ döntés/s-e az L0-é negyede, mert a permutáció-átlag 4 kérés.", ""]
    return lines


def verdicts(res: dict, h3: dict | None, engine: str = "vllm") -> list[str]:
    h1, h2 = res["H1"], res["H2"]
    out = ["| hipotézis | ítélet | részletek |", "|---|---|---|"]

    pt = res["pont"]
    seeds = [k for k in pt if k.startswith("L3_")]

    def pv(p: float) -> str:  # 10 000 ismétlésnél a 0 azt jelenti: < 1/10 000
        return "p < 0,0001" if p == 0 else f"p = {fmt(p, 4)}"

    def ci(b, point=None):
        pe = f"Δ = {fmt(point, 4)} (bootstrap-medián {fmt(b['delta_median'], 4)})" if point is not None \
            else f"Δ (bootstrap-medián) = {fmt(b['delta_median'], 4)}"
        return f"{pe}, 95% CI [{fmt(b['ci95'][0], 4)}; {fmt(b['ci95'][1], 4)}], {pv(b['p_ketoldali'])}"

    def val(arm, key, stratum="pool", tgt="95"):
        def one(k):
            b = pt[k][tgt]
            if stratum == "pool":
                return b["teszt"][key]
            parts = ["T-kozeli", "T-tavoli"] if stratum == "T-kategoria" else [stratum]
            r = [b["retegek"][q] for q in parts]
            return sum(x[key] * x["n"] for x in r) / sum(x["n"] for x in r)
        return float(np.mean([one(k) for k in seeds])) if arm == "L3" else one(arm)

    def dpt(key, stratum="pool", tgt="95", arm="L3"):
        return val(arm, key, stratum, tgt) - val("L1csillag", key, stratum, tgt)
    boot = res["bootstrap"]["L3_minus_L1csillag"]
    det = "; ".join(f"{nm}: {'megáll' if h1[ep]['all'] else 'cáfolt (' + ', '.join(h1[ep]['cafolat']) + ')'}"
                    for ep, nm in (("lef95", "@95"), ("aurc", "AURC")))
    out.append(f"| H1 (L3 vs. L1★, Holm) | **{'igaz' if h1['teljesul'] else 'cáfolt'}** | "
               f"@95: {ci(boot['teszt:lef95'], dpt('besorolasi_lefedettseg'))}; "
               f"AURC: {ci(boot['teszt:aurc'], dpt('aurc'))}; {det}; másodlagos @90: "
               f"{ci(h1['masodlagos_lef90'], dpt('besorolasi_lefedettseg', tgt='90'))} |")
    for part in ("T-szallito", "T-kategoria", "T-kozeli", "T-tavoli"):
        b = h2[part]
        extra = ""
        if "szallito_permutacio" in b:
            sp = b["szallito_permutacio"]
            extra = (f"; szállító-permutáció ({sp['szallitok']} szállító, rögzített val-τ, egzakt): "
                     f"p = {fmt(sp['p_ketoldali'], 5)}")
        verdict = f"**{b['itelet']}**"
        if part == "T-szallito":  # önellenőrzés, 2026-10-07: a réteg nem a rögzített definíció szerint épült
            verdict = ("**nem tesztelhető** (a számolt ítélet „" + b["itelet"] + "”, de a 14 szállító mind szerepel a "
                       "train-ben — generátorhiba, lásd Napló 2026-10-07; a számok leírók)")
        out.append(f"| H2 — {part} | {verdict} | @95: {ci(b, dpt('besorolasi_lefedettseg', part))}{extra} |")
    if h3:
        parts = ["a_aktivalas_K0c", "b_lora_hatas_egyezese", "c_motorok_kozti_egyezes", "d_lora_nelkuli_keresek"]
        out.append(f"| H3 (négy feltétel) | **{'igaz' if h3.get('H3_teljesul') else 'cáfolt'}** | "
                   + "; ".join(f"{p[0]}: {'✓' if h3[p]['teljesul'] else '✗'}" for p in parts)
                   + f"; r = {fmt(h3['b_lora_hatas_egyezese']['pearson_r'])}; (c) alsó korlát "
                   f"{fmt(h3['c_motorok_kozti_egyezes']['egyoldali_95_also'], 4)}; (d) LoRA-s ↔ LoRA nélküli példány "
                   f"{fmt(h3['d_lora_nelkuli_keresek']['lora_vs_lora_nelkul_egyezes'], 4)}, LoRA nélküliek egymás közt "
                   f"{fmt(h3['d_lora_nelkuli_keresek']['lora_nelkul_egymas_kozt'], 4)} (küszöb −1 pont) |")
    elif engine == "hf":
        out.append("| H3 | — | motorközi feltétel, lásd a vLLM-szakaszt |")
    else:
        out.append("| H3 | nem tesztelhető | a h3.json hiányzik |")
    fam = res.get("H4_H5_holm", {})
    if "H4_L2a" in res:
        h4 = res["H4_L2a"]
        ok = fam.get("H4_L2a_lef95", {})
        out.append(f"| H4 (L2a vs. L1★, HF) | **{'igaz' if ok.get('szignifikans') and ok.get('jo_irany') else 'cáfolt'}** | "
                   f"{ci(h4, dpt('besorolasi_lefedettseg', arm='L2a'))}; Holm-küszöb {fmt(ok.get('holm_kuszob'), 3)} |")
    h5 = res["H5_ece"]
    ok = fam.get("H5_ece", {})
    out.append(f"| H5 (ECE, {res['motor']}) | **{'igaz' if ok.get('szignifikans') and ok.get('jo_irany') else 'cáfolt'}** | "
               f"{ci(h5, dpt('ece'))}; Holm-küszöb {fmt(ok.get('holm_kuszob'), 3)}; az L1★ temperature-e a perm-0 "
               "kiolvasásra illesztett, ez az L1★ ECE-jét felfelé torzítja (önellenőrzés) |")
    out.append("| H6 (külön fej) | nem tesztelhető | az F5 nem futott |")
    return out


def h3_modes(path: Path) -> list[str]:
    """Az f4_h3_modok.py mélyfúrása (utólagos, leíró; 2026-10-07, az önellenőrzés után pontosítva)."""
    if not path.exists():
        return []
    o = json.loads(path.read_text())
    sg = lambda x: ("+" if x >= 0 else "−") + fmt(abs(x))  # noqa: E731
    fl, sh, mg, h1 = o["billenes_db"], o["eltolodas"], o["margo"], o["H1_modérzékenység"]["peldanyok"]
    groups = o["modok"]
    lora = [g for g in groups if not any(n.startswith("nolora") for n in g)]
    reps = [g[0] for g in lora]
    cross = [fl[a][b] for i, a in enumerate(reps) for b in reps[i + 1:]]
    vs_nolora = [fl[r]["nolora_k1"] for r in reps]
    nol = [n for g in groups for n in g if n.startswith("nolora")]
    byte = [o["bajtazonos_db"][a][b] for i, a in enumerate(nol) for b in nol[i + 1:]]
    be = o["moe_backend_logokbol"]
    acc = o["pontossag_pontozott"]
    pm = acc["modonkent_a_lora_nelkulihez"]
    l0 = [v["L0"]["lef95"] for v in h1.values()]
    dl = [v["delta_lef95"] for v in h1.values() if "delta_lef95" in v]
    nlora = sum(v["db"] for v in be.get("enable_lora", {}).values())
    return [
        "- **Mélyfúrás (utólagos, leíró; `h3_modok.json`).**",
        f"  - *Számítási út.* A megmaradt logok szerint `--enable-lora` mellett a MoE FP8-backend "
        f"{'/'.join(be.get('enable_lora', {}))} ({nlora} korábbi indítás, F0–F3), nélküle "
        f"{'/'.join(be.get('lora_nelkul', {}))} (az egyetlen megmaradt LoRA nélküli H3-log). A H3 LoRA-s példányainak "
        "logja felülíródott, rájuk ez következtetés. Az `--enable-lora` a lefordított gráfot is megváltoztatja (más "
        "torch.compile-kulcs, `PunicaWrapperGPU`), így az eltérés a számítási út egészéből jön; hogy ebből mennyi a "
        "MoE-backend, azt egy kényszerített Triton-backendes LoRA nélküli kontroll döntené el (nem futott).",
        f"  - *Numerika-módok* (utólagos definíció: páronként ≤ {o['modkuszob_billenes']:.0%} top-címke-billenés; 5 "
        "példányból alsó becslés): " + "; ".join("{" + ", ".join(g) + "}" for g in groups) + ". A LoRA nélküli "
        f"példányok egymás közt 0 billenéssel, de nem bitazonosan ({min(byte)}–{max(byte)}/{o['n']} bájtazonos sor) "
        f"egyeznek. A LoRA-s módok egymás közt {min(cross)}–{max(cross)}, a LoRA nélkülitől {min(vs_nolora)}–"
        f"{max(vs_nolora)} billenésre vannak; a HF-referencia mindegyiktől "
        f"{min(v['billenes_HF_hez'] for k, v in sh.items() if k != 'HF_L0')}–"
        f"{max(v['billenes_HF_hez'] for k, v in sh.items() if k != 'HF_L0')} billenésre ({o['n']} itemből).",
        f"  - *Rendszeres eltolódás:* a LoRA-s módok átl. Δ log p(A)-ja a LoRA nélkülihez képest "
        f"{sg(min(sh[r]['dlogpA_a_lora_nelkulihez'] for r in reps))}…{sg(max(sh[r]['dlogpA_a_lora_nelkulihez'] for r in reps))}, "
        f"egymás közt ≈ 0; a HF {sg(sh['HF_L0']['dlogpA_a_lora_nelkulihez'])}. Szűkített entrópia: LoRA-s módok "
        f"{fmt(min(sh[r]['entropia'] for r in reps))}–{fmt(max(sh[r]['entropia'] for r in reps))}, LoRA nélkül "
        f"{fmt(sh[groups[-1][0]]['entropia'])}, HF {fmt(sh['HF_L0']['entropia'])}.",
        f"  - *Pontosság a pontozott itemeken* (n = {acc['n']}): a LoRA-s módok Δ-ja a LoRA nélkülihez képest "
        + "; ".join(f"{sg(v['delta_pontossag'])} [{sg(v['ci95'][0])}; {sg(v['ci95'][1])}], billenés jóra/rosszra "
                    f"{v['billenes_jora']}/{v['billenes_rosszra']}" for v in pm.values())
        + ". Kb. ±1,3 pontos felbontással nincs kimutatható romlás. A billenő itemek top-2 margója medián "
        f"{fmt(mg['billeno_median'])} (max {fmt(mg['billeno_max'])}), a nem billenőké {fmt(mg['nem_billeno_median'])}.",
        f"  - *A (d) bukása bázisfüggetlen:* a LoRA-s példányok egymás közti egyezése is csak "
        f"{fmt(1 - float(np.mean([fl[a][b] for i, a in enumerate([n for g in lora for n in g if n.startswith('lora')]) for b in [n for g in lora for n in g if n.startswith('lora')][i + 1:]])) / o['n'], 3)}, "
        "a keresztegyezés ennél is kisebb.",
        f"  - *H1 módonként* (a fő példány val-ján rögzített temperature és τ@95, perm 0, `temp` kar): L0 lef@95 "
        f"{fmt(min(l0))}–{fmt(max(l0))} (LoRA nélküli példányokon is), L3 − L0 = {sg(min(dl))}…{sg(max(dl))}.",
        "  - *Nem mért:* csak soros forgalom volt, vegyes köteg (LoRA-s és LoRA nélküli kérés együtt) és a chat-decode "
        "ára (runbook 6. pont) nem."]


def self_check(path: Path) -> list[str]:
    """A kör végi önellenőrzés utólagos számai (`f4_onellenorzes.py`)."""
    if not path.exists():
        return []
    o = json.loads(path.read_text())
    sz, sa, pl, au = o["split_szivargas"], o["szallitoi_altalanositas"], o["plafon"], o["aurc"]
    lines = ["## Önellenőrzés (utólagos, leíró; 2026-10-07, `onellenorzes.json`)", "",
             "**Split-szivárgás.** A T-szállító réteg szállítóinak a terv szerint csak a tesztben kellett volna "
             "szerepelniük. A generátor (`generator.py`, S-párosítás) a train-pár nélküli cikkek tesztpárját a train-be "
             "tette, így ezek a szállítók a train-ben is megjelentek. A H2 T-szállító ítélete ezért nem tesztelhető.", "",
             "| réteg | itemek | szállítók | ebből a train-ben | azok train-sorai | (szállító, cikk) átfedés | sorszöveg + gold duplikátum |",
             "|---|---|---|---|---|---|---|"]
    for s, v in sz.items():
        lines.append(f"| {s} | {v['itemek']} | {v['szallitok']} | {v['szallitok_a_trainben']} | {v['e_szallitok_train_sorai']} "
                     f"| {v['szallito_cikk_par_atfedes']} | {v['sorszoveg_gold_duplikatum']} |")
    ls = sa["latott_vs_nem_latott"]
    lines += ["", f"- **Nem látott szállítók (feltáró):** T-közeli: nem látott {fmt(ls['T-kozeli']['nem_latott']['nyereseg'])} "
              f"(n = {ls['T-kozeli']['nem_latott']['n']}), látott {fmt(ls['T-kozeli']['latott']['nyereseg'])} "
              f"(n = {ls['T-kozeli']['latott']['n']}); T-távoli (mind nem látott) {fmt(ls['T-tavoli']['nem_latott']['nyereseg'])}; "
              f"T-belső (mind látott) {fmt(ls['T-belso']['latott']['nyereseg'])}. A kategóriaváltással keveredik. A T-szállítón a "
              f"szállítónkénti nyereség és a train-sorok száma: Spearman ρ = {fmt(sa['spearman_train_sorok_nyereseg'], 2)} "
              f"(p = {fmt(sa['spearman_p'], 2)}).",
              f"- **Plafon és hibaszerkezet:** a pontozott teszt nem-X aránya {fmt(pl['nem_X_arany_pontozott_teszten'])}, ez a "
              "lef@95 felső korlátja. " + "; ".join(
                  f"{k}: lef {fmt(v['lef'])}, precizitás {fmt(v['precizitas'])}, hibák: X-gold besorolva {v['hiba_X_gold_besorolva']}, "
                  f"rossz cikk {v['hiba_rossz_cikk']}" for k, v in pl["hibaszerkezet"].items()) + ".",
              f"- **AURC közös lefedettségen ({fmt(au['kozos_lefedettseg'])}):** " + "; ".join(
                  f"{k} {fmt(v, 4)}" for k, v in au["kozos_lefedettsegig"].items()) + ". Kockázat 0,7-es lefedettségen: "
              + "; ".join(f"{k} {fmt(v, 4)}" for k, v in au["kockazat_rogzitett_lefedettsegen"]["0.7"].items()) + ".",
              "- **X-arány-érzékenység** (a val és a teszt X-itemjeinek ritkítása, L3 − L1★ lef@95): " + "; ".join(
                  f"X {fmt(float(k), 2)} → {fmt(v['delta_atlag'] * 100, 1)} pont [{fmt(v['p5'] * 100, 1)}; {fmt(v['p95'] * 100, 1)}]"
                  for k, v in o["X_arany_erzekenyseg"].items()) + ".",
              "- **Az L1★ temperature-e:** " + "; ".join(
                  f"{k}: T = {fmt(v['T'], 3)}, ECE {fmt(v['ece'])}, lef@95 {fmt(v['lef95'])}" for k, v in o["L1csillag_temperature"].items())
              + f". Az L3 ECE-je {fmt(o['L3_ece_atlag'])}.", ""]
    return lines


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="eredmenyek/F4")
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--atnezes", default="eredmenyek/F1/atnezes/osszesites.json")
    ap.add_argument("--k0c", default="eredmenyek/F0/k0c/k0c.json")
    args = ap.parse_args()
    D = _p(args.dir)
    res = {m: json.loads((D / f"{m}_f4.json").read_text()) for m in ("vllm", "hf") if (D / f"{m}_f4.json").exists()}
    h3 = json.loads((D / "h3.json").read_text()) if (D / "h3.json").exists() else None
    md = ["# F4 eredménylap (runbook 14. pont)", "",
          "A számok a teszten; τ és a temperature a val-on rögzítve. Az L3 a három seed átlaga.", ""]
    extra = {}
    for m, r in res.items():
        md += [f"## {'vLLM' if m == 'vllm' else 'HF'}", "", f"n(val) = {r['n_val']}, n(teszt) = {r['n_teszt']}; az L1★ temperature-e "
               f"{fmt(r['L1_temperature'])}.", ""]
        md += engine_table(r, h3 if m == "vllm" else None, args.items)
        md += ["### Hipotézisek", ""] + verdicts(r, h3 if m == "vllm" else None, m) + [""]
        if "ismetlesi_zaj_L0_L0vesszo" in r:
            z = r["ismetlesi_zaj_L0_L0vesszo"]
            md += [f"- **Ismétlési zaj (L0 ↔ L0′):** top-címke billenés {fmt(z['top_cimke_billenes'], 4)}, átl. |Δp| "
                   f"{fmt(z['abs_dp_atlag'], 5)} (max {fmt(z['abs_dp_max'], 4)}), lef@95-különbség rögzített τ-val "
                   f"{fmt(z['lef95_kulonbseg_rogzitett_tau'], 4)}."]
        sens = sensitivity(r, args.items)
        extra[m] = sens
        md += ["- **Javítatlan teszten (érzékenység, pontbecslés):** "
               + "; ".join(f"{k}: lef@95 {fmt(v['besorolasi_lefedettseg'])}, AURC {fmt(v['aurc'], 4)}" for k, v in sens.items())
               + "."]
        amb = r["bontasok"]
        md += ["- **Kétértelmű sorok (L3):** " + "; ".join(
            f"{k}: átlépés {fmt(v['ketertelmu']['atlepes'])}, soft-gold találat az átlépőkön "
            f"{fmt(v['ketertelmu']['soft_gold_talalat_az_atlepokon'])}" for k, v in amb.items() if k.startswith("L3_")) + ".", ""]
    atn = _p(args.atnezes)
    if atn.exists():
        o = json.loads(atn.read_text())
        md += ["## Címkezaj (F1 átnézés)", "",
               f"- Teszt: pont {fmt(o['teszt']['teszt']['pont'], 4)}, felső95 {fmt(o['teszt']['teszt']['felso95'], 4)} "
               f"(n = {o['teszt']['teszt']['n']}).",
               "- Rétegenként (becsült maradék a javítás után): " + "; ".join(
                   f"{s}: {fmt(o['retegek'][s].get('becsult_maradek_javitas_utan'), 4)}" for s in TEST_STRATA if s in o["retegek"]) + ".", ""]
    k0c = _p(args.k0c)
    md += ["## Kiszolgálás", ""]
    if k0c.exists():
        md += [f"- **K0c:** kapu {'átment' if json.loads(k0c.read_text()).get('K0c_ok') else 'bukott'} "
               f"(részletek: {args.k0c})."]
    if h3:
        rb = h3["peldany_robusztussag"]
        md += [f"- **Példány-billenés (≥ 5 friss példány):** LoRA nélkül L0 {fmt(rb['billenes']['lora_nelkul_L0'], 4)}, "
               f"LoRA-s példány L0 {fmt(rb['billenes']['lora_L0'], 4)}, L3 {fmt(rb['billenes']['lora_L3'], 4)}; "
               f"numerika-módok (próba-ujjlenyomat): LoRA-val {rb['numerika_modok']['proba_ujjlenyomat']['lora']}, "
               f"nélküle {rb['numerika_modok']['proba_ujjlenyomat']['lora_nelkul']}."]
        md += h3_modes(_p(args.dir) / "h3_modok.json")
        md += ["", "A (b) és a (c) ugyanazon a, órák óta futó fő példányon mért, ezért a LoRA-kérés többletköltsége a "
               "kettő különbsége. Az (a) egy másik, frissen indított H3-példányon futott, és ott a MoE-kernel is más "
               "(DEEPGEMM a TRITON helyett), ezért az (a)–(b) különbség a backendet és a példányt együtt méri, "
               "nem a LoRA-támogatás költségét.", "",
               "| konfiguráció | concurrency | döntés/s | p50 (ms) | p95 (ms) |", "|---|---|---|---|---|"]
        names = {"a_lora_nelkuli_peldany": "(a) LoRA nélküli példány", "b_lora_peldany_lora_nelkul": "(b) LoRA-s példány, LoRA nélküli kérés",
                 "c_lora_request": "(c) `lora_request`"}
        for k, v in h3["teljesitmeny"].items():
            for c, p in v.items():
                md.append(f"| {names[k]} | {c} | {fmt(p['dontes_per_s'], 1)} | {fmt(p['p50_ms'], 0)} | {fmt(p['p95_ms'], 0)} |")
        md.append("")
    md += ["- **MTP nélküli chat decode:** nem mérve ebben a körben (eltérés a runbook 6. pontjától).", ""]
    md += self_check(D / "onellenorzes.json")
    (D / "eredmenylap.md").write_text("\n".join(md))
    write_json(D / "eredmenylap.json", {"erzekenyseg_javitatlan_teszten": extra})
    print(f"kész: {D / 'eredmenylap.md'}")


if __name__ == "__main__":
    main()
