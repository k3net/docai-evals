"""K01F4 — a 01-es kör végső tesztjének elemzése (01-runbook v1: 4., 6. pont), a 00 `f4_elemzes.py` építőelemeivel.

Bemenet (`--dir`, alap: kor01/eredmenyek/F4/vllm): bazis_val/test (4 perm.), bazis_test_ism (L0′, perm 0),
l3_s{1,2,3}_val/test (s1: 4 perm., s2–s3: perm 0), l0n_test, s2_test; a T-új-eszköz tagsága
(eredmenyek/F1S/uj_eszkoz.jsonl) és a T-hu közel-duplikátumai (eredmenyek/F1S/szivargas_itemek.jsonl, kérés-cos ≥ 0,95).

Karok: L1★ = `perm_avg` + a val-on illesztett temperature (az F4-példány bázis-val-kiolvasásából); L3 = `temp`
seedenként. τ@95 / τ@90 a val-on (a 00 τ-szabálya).
Bootstrap: 10 000 ismétlés, hierarchikus seed (visszatevéssel) × klaszter (`meta.klaszter`); a val minden
replikában újramintázva és τ újraválasztva. A pool klaszter-diszjunkt részei külön húzódnak: T-BFCL,
T-BFCL-live+W2C (közös klaszterek), T-hu, T-katalógus.

  H1 — pool: társ-elsődleges lef@95 (L3 > L1★) és AURC (L3 < L1★), Holm; cáfolati okok a 00 szerint.
  H2 — T-BFCL-live+W2C és T-hu: a Δ lef@95 CI-je → általánosít / nem általánosít (felső < 2 pont) / nem eldönthető.
  H3 — pool, az L0n munkapontján: (i) L3-precizitás az L0n-lefedettségen, (ii) L3-lefedettség az L0n-precizitásán;
       mindkét Δ > 0 kell (IUT: p = a nagyobbik); X-fedés külön.
  H5 — pool: Δ X-fedés > −2 pont (non-inferiority) és Δ nem-X pontosság > 0 (IUT). H3 és H5 egy Holm-család.
  Leíró: T-új-eszköz, T-katalógus, T-BFCL, T-hu a közel-duplikátumok nélkül, T-hu-maradék; X-arány-standardizált
  Δ lef@95 (25%, 10%); L3→S2; L0↔L0′ ismétlési zaj; s1 permutációs billenése; McNemar; bontások.

  python3 kor01/eszkozok/f4_elemzes01.py --out kor01/eredmenyek/F4/f4_elemzes.json [--reps 10000]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import FAIL_BELOW, TARGETS, arm_predictions, by_item, choose_tau, fit_temperature, metrics  # noqa: E402
from f4_elemzes import (CP, Arm, Resampler, holm_family, mcnemar, metrics_fast, repeat_noise, summarize,  # noqa: E402
                        tau_fast)

ROOT = Path(__file__).resolve().parents[1]
NO_GAIN = 0.02
NONINF_X = -0.02
POOL_PARTS = ["T-BFCL", "T-BFCL-live+W2C", "T-hu", "T-katalogus"]
H2_PARTS = ["T-BFCL-live+W2C", "T-hu"]
DESCR_PARTS = ["T-uj-eszkoz", "T-hu-dedup", "T-hu-maradek", "T-BFCL-live", "T-When2Call"]
X_STD = (0.25, 0.10)
UNKNOWN = "__ismeretlen__"


def load_meta01() -> dict:
    meta = {}
    for f in ("adat/items_val.jsonl", "adat/items_teszt.jsonl", "adat/f1s/items_katalogus.jsonl"):
        for it in read_jsonl(ROOT / f):
            m = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None, "forras": it["forras"],
                 "n_opcio": len(it["options"]), **it["meta"]}
            m.setdefault("klaszter", it["id"])
            meta[it["id"]] = m
    return meta


def layers(meta: dict, test_ids: list[str], uj: set, near: set) -> dict[str, list[str]]:
    f = lambda i: meta[i]["forras"]  # noqa: E731
    L = {"T-BFCL": [i for i in test_ids if f(i) in ("bfcl_simple", "bfcl_multiple", "bfcl_irrelevance")],
         "T-BFCL-live": [i for i in test_ids if f(i).startswith("bfcl_live")],
         "T-When2Call": [i for i in test_ids if f(i) == "w2c_teszt"],
         "T-hu": [i for i in test_ids if f(i) == "massive_hu" and meta[i].get("t_hu_atnezett")],
         "T-katalogus": [i for i in test_ids if f(i) == "katalogus_hu"],
         "T-hu-maradek": [i for i in test_ids if f(i) == "massive_hu" and not meta[i].get("t_hu_atnezett")]}
    L["T-BFCL-live+W2C"] = L["T-BFCL-live"] + L["T-When2Call"]
    L["pool"] = [i for p in POOL_PARTS for i in L[p]]
    L["T-uj-eszkoz"] = [i for i in test_ids if i in uj]
    L["T-hu-dedup"] = [i for i in L["T-hu"] if i not in near]
    return L


def load_arm(d: Path, val: str, test: str, meta: dict, arm: str) -> tuple[dict, float]:
    rv, rt = read_jsonl(d / f"{val}.jsonl"), read_jsonl(d / f"{test}.jsonl")
    temp = fit_temperature([r for r in rv if r["perm"] == 0], meta)
    prm = {"temp": temp}
    return {**arm_predictions(arm, by_item(rv, None), meta, prm), **arm_predictions(arm, by_item(rt, None), meta, prm)}, temp


class Native:
    """Az L0n döntései tömbökben: hívott-e, és jó eszközt-e."""

    def __init__(self, rows: dict, ids: list[str], meta: dict):
        self.call = np.array([rows[i]["pred"] is not None if i in rows else False for i in ids])
        self.ok = np.array([i in rows and rows[i]["pred"] is not None and rows[i]["pred"] == meta[i]["gold"] for i in ids])
        self.no_call = ~self.call


def native_op(N: Native, s: np.ndarray) -> tuple[float, float]:
    calls = N.call[s]
    return float(calls.mean()), float(N.ok[s][calls].mean()) if calls.any() else math.nan


def l3_ranked(A: Arm, s: np.ndarray) -> np.ndarray:
    ad = s[A.assign[s]]
    return ad[np.argsort(-A.conf[ad], kind="stable")]


def l3_prec_at_cov(A: Arm, s: np.ndarray, cov: float) -> float:
    o = l3_ranked(A, s)
    k = min(len(o), int(round(cov * len(s))))
    return float(A.correct[o[:k]].mean()) if k else math.nan


def l3_cov_at_prec(A: Arm, s: np.ndarray, prec: float) -> float:
    o = l3_ranked(A, s)
    if not len(o):
        return 0.0
    run = np.cumsum(A.correct[o]) / np.arange(1, len(o) + 1)
    ok = np.nonzero(run >= prec - 1e-12)[0]
    return float((ok[-1] + 1) / len(s)) if len(ok) else 0.0


def x_std(t: np.ndarray, xmask: np.ndarray, p: float, rng: np.random.Generator) -> np.ndarray:
    """A t index-multihalmaz ritkítása p X-arányra (csak X-et hagy el)."""
    xs, nx = t[xmask[t]], t[~xmask[t]]
    want = int(round(len(nx) * p / (1 - p)))
    if want >= len(xs):
        return t
    return np.concatenate([nx, rng.choice(xs, want, replace=False)])


def point_block(preds: dict, meta: dict, val_ids: list[str], L: dict) -> dict:
    out = {}
    for tgt, tn in TARGETS:
        tau = choose_tau(preds, meta, val_ids, tgt)
        fb = FAIL_BELOW[tn]
        out[tn] = {"tau": tau, "val": metrics(preds, meta, val_ids, tau, fb),
                   "retegek": {k: metrics(preds, meta, v, tau, fb) for k, v in L.items() if v}}
    return out


def ceiling(meta: dict, ids: list[str]) -> float:
    s = [i for i in ids if not meta[i].get("ketertelmu")]
    return sum(meta[i]["gold"] is not None for i in s) / max(1, len(s))


def s2_block(l3: dict, s2rows: dict, meta: dict, val_ids: list[str], pool: list[str]) -> dict:
    tau = choose_tau(l3, meta, val_ids, 0.95)
    s = [i for i in pool if not meta[i].get("ketertelmu")]
    auto, ok, xhit = 0, 0, 0
    s2n = s2ans = s2auto = s2ok = 0
    for i in s:
        pred, conf = l3[i][0], l3[i][1]
        if pred is not None and conf >= tau:
            final = pred
        else:
            r = s2rows.get(i)
            s2n += r is not None
            s2ans += bool(r and r["van_valasz"])
            final = r["pred"] if r and r["van_valasz"] else None
            if final is not None:
                s2auto += 1
                s2ok += final == meta[i]["gold"]
        if final is not None:
            auto += 1
            ok += final == meta[i]["gold"]
        elif meta[i]["gold"] is None:
            xhit += 1
    nx = sum(meta[i]["gold"] is None for i in s)
    lat = sorted(r["latency_s"] for r in s2rows.values())
    return {"tau95_L3": tau, "n": len(s), "lefedettseg": auto / len(s), "precizitas": ok / auto if auto else None,
            "x_fedes": xhit / nx if nx else None, "s2_kapott": s2n, "s2_valaszolt": s2ans,
            "s2_besorolt": s2auto, "s2_precizitas": s2ok / s2auto if s2auto else None,
            "s2_kesleltetes_median_s": lat[len(lat) // 2] if lat else None}


def perm_flip(rows: list[dict], meta: dict, ids: list[str]) -> float:
    top = defaultdict(set)
    for r in rows:
        top[r["id"]].add(r["order"][r["labels"].index(r["pred"])] if r["pred"] != "X" else None)
    s = [i for i in ids if not meta[i].get("ketertelmu") and i in top]
    return sum(len(top[i]) > 1 for i in s) / max(1, len(s))


def analyse(args) -> dict:
    d = Path(args.dir)
    meta = load_meta01()
    uj = {r["id"] for r in read_jsonl(Path(args.uj)) if r["t_uj_eszkoz"]} if Path(args.uj).exists() else set()
    near = {r["id"] for r in read_jsonl(ROOT / "eredmenyek/F1S/szivargas_itemek.jsonl") if r["keres_max_cos"] >= 0.95}
    l1, t_l1 = load_arm(d, "bazis_val", "bazis_test", meta, "perm_avg")
    l0, _ = load_arm(d, "bazis_val", "bazis_test", meta, "nyers")
    l3, t_l3 = {}, {}
    for k in (1, 2, 3):
        if (d / f"l3_s{k}_test.jsonl").exists():
            l3[f"s{k}"], t_l3[f"s{k}"] = load_arm(d, f"l3_s{k}_val", f"l3_s{k}_test", meta, "temp")
    val_ids = [i for i in l1 if meta[i]["split"] == "val"]
    test_ids = [i for i in l1 if meta[i]["split"] != "val"]
    for name, p in l3.items():
        miss = [i for i in val_ids + test_ids if i not in p]
        if miss:
            raise SystemExit(f"L3 {name}: {len(miss)} item hiányzik")
    L = layers(meta, test_ids, uj, near)
    res = {"n_val": len(val_ids), "n_teszt": len(test_ids), "L1_temperature": t_l1, "L3_temperature": t_l3,
           "retegmeret": {k: {"n": len(v), "pontozott": sum(not meta[i].get("ketertelmu") for i in v),
                              "plafon": ceiling(meta, v)} for k, v in L.items()},
           "pont": {"L0": point_block(l0, meta, val_ids, L), "L1csillag": point_block(l1, meta, val_ids, L),
                    **{f"L3_{k}": point_block(p, meta, val_ids, L) for k, p in l3.items()}}}
    res["mcnemar_pool"] = {f"L3_{k}_vs_L1csillag": mcnemar(p, l1, meta, L["pool"]) for k, p in l3.items()}
    if (d / "bazis_test_ism.jsonl").exists():
        r0, r0r = read_jsonl(d / "bazis_test.jsonl"), read_jsonl(d / "bazis_test_ism.jsonl")
        l0r = {**{i: l0[i] for i in val_ids}, **arm_predictions("nyers", by_item(r0r, None), meta, {})}
        res["ismetlesi_zaj_L0_L0vesszo"] = repeat_noise(l0, l0r, meta, val_ids, L["pool"], r0, r0r)
    if (d / "l3_s1_test.jsonl").exists():
        res["permutacios_billenes_L3_s1_pool"] = perm_flip(read_jsonl(d / "l3_s1_test.jsonl"), meta, L["pool"])
        res["permutacios_billenes_bazis_pool"] = perm_flip(read_jsonl(d / "bazis_test.jsonl"), meta, L["pool"])
    nat = {r["id"]: r for r in read_jsonl(d / "l0n_test.jsonl")} if (d / "l0n_test.jsonl").exists() else None
    if nat:
        s = [i for i in L["pool"] if not meta[i].get("ketertelmu")]
        calls = [i for i in s if nat[i]["pred"] is not None]
        res["L0n_pont_pool"] = {"lefedettseg": len(calls) / len(s),
                                "precizitas": sum(nat[i]["pred"] == meta[i]["gold"] for i in calls) / max(1, len(calls)),
                                "ismeretlen_nev": sum(nat[i]["pred"] == UNKNOWN for i in calls),
                                "x_fedes": sum(nat[i]["pred"] is None for i in s if meta[i]["gold"] is None)
                                / max(1, sum(meta[i]["gold"] is None for i in s))}
    if (d / "s2_test.jsonl").exists() and "s1" in l3:
        res["L3_S2"] = s2_block(l3["s1"], {r["id"]: r for r in read_jsonl(d / "s2_test.jsonl")}, meta, val_ids, L["pool"])

    # --- bootstrap -------------------------------------------------------------------------------------
    ids = val_ids + test_ids
    groups = {"val": val_ids, **{p: L[p] for p in POOL_PARTS}, **{p: L[p] for p in DESCR_PARTS if L[p]}}
    rs = Resampler(ids, meta, groups, {g: "klaszter" for g in groups})
    scored = np.array([not meta[i].get("ketertelmu") for i in ids])
    xmask = np.array([meta[i]["gold"] is None for i in ids])
    cp = CP(len(ids) + 1)
    A1 = Arm(l1, ids, meta)
    A3 = {k: Arm(p, ids, meta) for k, p in l3.items()}
    N = Native(nat, ids, meta) if nat else None
    seeds = list(A3)
    rng = np.random.default_rng(args.seed)
    acc = defaultdict(list)
    for _ in range(args.reps):
        v = rs.draw("val", rng)
        t = {g: rs.draw(g, rng) for g in groups if g != "val"}
        t["pool"] = np.concatenate([t[p] for p in POOL_PARTS])
        drawn = [seeds[k] for k in rng.integers(0, len(seeds), len(seeds))]
        tb = {tn: tau_fast(A1, v, scored, tgt, cp) for tgt, tn in TARGETS}
        ta = {tn: {k: tau_fast(A3[k], v, scored, tgt, cp) for k in set(drawn)} for tgt, tn in TARGETS}
        for part in ["pool", *POOL_PARTS, *[p for p in DESCR_PARTS if p in t]]:
            for tgt, tn in TARGETS:
                mb = metrics_fast(A1, t[part], scored, tb[tn])
                ma = [metrics_fast(A3[k], t[part], scored, ta[tn][k]) for k in drawn]
                acc[f"{part}:lef{tn}"].append(np.mean([m["lef"] for m in ma]) - mb["lef"])
                if tn == "95":
                    acc[f"{part}:aurc"].append(np.mean([m["aurc"] for m in ma]) - mb["aurc"])
                    acc[f"{part}:ece"].append(np.mean([m["ece"] for m in ma]) - mb["ece"])
        s_pool = t["pool"][scored[t["pool"]]]
        for p in X_STD:
            sx = x_std(s_pool, xmask, p, rng)
            acc[f"pool:lef95_x{int(p * 100)}"].append(
                np.mean([metrics_fast(A3[k], sx, scored, ta["95"][k])["lef"] for k in drawn])
                - metrics_fast(A1, sx, scored, tb["95"])["lef"])
        # H5: τ-független; X-fedés és nem-X pontosság
        gx, gn = s_pool[xmask[s_pool]], s_pool[~xmask[s_pool]]
        xf1 = (~A1.assign[gx]).mean()
        acc["H5:x_fedes"].append(np.mean([(~A3[k].assign[gx]).mean() for k in drawn]) - xf1)
        acc["H5:nemx_pontossag"].append(np.mean([A3[k].correct[gn].mean() for k in drawn]) - A1.correct[gn].mean())
        if N is not None:
            cov_n, prec_n = native_op(N, s_pool)
            acc["H3:prec_az_L0n_lefedettsegen"].append(np.mean([l3_prec_at_cov(A3[k], s_pool, cov_n) for k in drawn]) - prec_n)
            acc["H3:lef_az_L0n_precizitasan"].append(np.mean([l3_cov_at_prec(A3[k], s_pool, prec_n) for k in drawn]) - cov_n)
            acc["H3:x_fedes"].append(np.mean([(~A3[k].assign[gx]).mean() for k in drawn]) - N.no_call[gx].mean())
    boot = {k: summarize(x) for k, x in acc.items()}
    res["bootstrap"] = {"reps": args.reps, "seed": args.seed, "L3_minus_L1csillag": boot}

    # --- H1 ---------------------------------------------------------------------------------------------
    hf = holm_family({"lef95": (boot["pool:lef95"]["p_ketoldali"], boot["pool:lef95"]["delta_median"] > 0),
                      "aurc": (boot["pool:aurc"]["p_ketoldali"], boot["pool:aurc"]["delta_median"] < 0)})
    l1p = res["pont"]["L1csillag"]["95"]["retegek"]["pool"]
    for ep in ("lef95", "aurc"):
        reasons = []
        if not hf[ep]["szignifikans"]:
            reasons.append("nem szignifikáns a Holm-küszöbön")
        if not hf[ep]["jo_irany"]:
            reasons.append("az L1★ javára mutat")
        for k in seeds:
            s3 = res["pont"][f"L3_{k}"]["95"]["retegek"]["pool"]
            if ep == "lef95" and s3["besorolasi_lefedettseg"] <= l1p["besorolasi_lefedettseg"]:
                reasons.append(f"seed {k}: pontbecslés ≤ L1★")
            if ep == "aurc" and s3["aurc"] >= l1p["aurc"]:
                reasons.append(f"seed {k}: pontbecslés ≥ L1★")
            if ep == "lef95" and s3["precizitas_bukas"]:
                reasons.append(f"seed {k}: precizitás-bukás a poolon")
        hf[ep]["cafolat"] = reasons
        hf[ep]["all"] = not reasons
    res["H1"] = {**hf, "teljesul": hf["lef95"]["all"] or hf["aurc"]["all"], "masodlagos_lef90": boot["pool:lef90"],
                 "x_standardizalt": {f"x{int(p * 100)}": boot[f"pool:lef95_x{int(p * 100)}"] for p in X_STD}}

    # --- H2 (+ leíró rétegek ugyanígy) -----------------------------------------------------------------------
    h2 = {}
    for part in [*H2_PARTS, "T-BFCL", "T-katalogus", *[p for p in DESCR_PARTS if f"{p}:lef95" in boot]]:
        b = boot[f"{part}:lef95"]
        lo, hi = b["ci95"]
        h2[part] = {**b, "itelet": "általánosít" if lo > 0 else ("nem általánosít" if hi < NO_GAIN else "nem eldönthető"),
                    "aurc": boot[f"{part}:aurc"], "H2_reteg": part in H2_PARTS}
    res["H2"] = h2

    # --- H3, H5 (IUT, egy Holm-család) ---------------------------------------------------------------------
    def one_sided(key: str, margin: float = 0.0) -> float:
        x = np.array(acc[key])
        return float((x <= margin).mean())

    fam = {}
    a5 = acc["H5:x_fedes"]
    p5 = max(one_sided("H5:x_fedes", NONINF_X), one_sided("H5:nemx_pontossag"))
    fam["H5"] = (min(1.0, 2 * p5), bool(np.percentile(a5, 2.5) > NONINF_X))
    if N is not None:
        p3 = max(one_sided("H3:prec_az_L0n_lefedettsegen"), one_sided("H3:lef_az_L0n_precizitasan"))
        fam["H3"] = (min(1.0, 2 * p3), True)
    hh = holm_family(fam)
    res["H3_H5_holm"] = hh
    res["H5"] = {"x_fedes": boot["H5:x_fedes"], "nemx_pontossag": boot["H5:nemx_pontossag"],
                 "teljesul": hh["H5"]["szignifikans"]}
    if N is not None:
        res["H3"] = {"prec_az_L0n_lefedettsegen": boot["H3:prec_az_L0n_lefedettsegen"],
                     "lef_az_L0n_precizitasan": boot["H3:lef_az_L0n_precizitasan"],
                     "x_fedes_L3_minus_L0n": boot["H3:x_fedes"], "teljesul": hh["H3"]["szignifikans"]}
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(ROOT / "eredmenyek/F4/vllm"))
    ap.add_argument("--uj", default=str(ROOT / "eredmenyek/F1S/uj_eszkoz.jsonl"))
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = analyse(args)
    write_json(Path(args.out), res)
    short = {"H1": {k: {"szign": res["H1"][k]["szignifikans"], "cafolat": res["H1"][k]["cafolat"]} for k in ("lef95", "aurc")}
             | {"teljesul": res["H1"]["teljesul"]},
             "H2": {k: v["itelet"] for k, v in res["H2"].items()},
             "H3": res.get("H3", {}).get("teljesul"), "H5": res["H5"]["teljesul"]}
    print(json.dumps(short, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
