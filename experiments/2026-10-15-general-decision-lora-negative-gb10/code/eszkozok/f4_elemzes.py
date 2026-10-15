"""F4 — a végső teszt elemzése (runbook 3. H1, H2, H4, H5; 8. statisztikai protokoll).

Egy motoron belül (vLLM a vLLM-mel, HF a HF-fel). Bemenet: az L0 kiolvasása a val-on és a teszten (4 permutáció;
ebből az L1★ = perm_avg + val-temperature), az L0′ (az L0 ismétlése a sor végén, ugyanazon a példányon), az L3
seedek val- és teszt-kiolvasása (H1-hez a `temp` kar), HF-en opcionálisan az L2a (H4).

Bootstrap (8. pont): 10 000 ismétlés, hierarchikus: seed (visszatevéssel) × klaszter. A val klaszterezve (cikk)
újramintavételeződik, és τ minden replikában újraválasztódik; a teszt rétegenként, saját klaszterkulccsal
(T-szállító: szállító, a többi: cikk). A replikánkénti Δ a kihúzott seedek átlaga.

  H1 — L3 vs. L1★ a teljes teszten: társ-elsődleges @95 (L3 > L1★) és AURC (L3 < L1★), Holm (α = 0,05);
       végpontonkénti cáfolat: nem szignifikáns / az L1★ javára / (@95) precizitás-bukás / egy seed pontbecslése
       rossz oldalon. A H1 teljesül, ha legalább egy végpont megáll.
  H2 — rétegenként (T-szállító; T-kategória = közeli + távoli; külön is), a @95 Δ CI-ja: alsó > 0 → általánosít;
       felső < 2 pont → nem általánosít; egyébként nem eldönthető. A T-szállítón szállító-szintű előjelcserés
       permutációs teszt is (rögzített val-τ).
  H4 — L2a vs. L1★ (HF), @95; H5 — L3 vs. L1★ ECE. H4 és H5 egy Holm-család.
  Ismétlési zaj — L0 ↔ L0′: top-címke billenés, |Δp|, a lefedettség@95 különbsége rögzített τ-val.
  Bontások — réteg, X / nem-X, listahossz, x_fajta; kétértelmű sorok: átlépés és a soft-gold találati arány.
  McNemar a pontosságra (másodlagos).

A gyors bootstrap vektorizált mérőszámokat használ; ezek az `elemzes.choose_tau`/`metrics` értékeivel egyeznek
(`onteszt` alparancs, valós F3 val-kiolvasásokon).

  python3 eszkozok/f4_elemzes.py --motor vllm --l0-val eredmenyek/F4/vllm/l0_val.jsonl \\
      --l0-test eredmenyek/F4/vllm/l0_test.jsonl --l0r-test eredmenyek/F4/vllm/l0r_test.jsonl \\
      --l3 s1:eredmenyek/F4/vllm/l3_s1_val.jsonl:eredmenyek/F4/vllm/l3_s1_test.jsonl --l3 s2:... --l3 s3:... \\
      --out eredmenyek/F4/vllm_f4.json
  python3 eszkozok/f4_elemzes.py onteszt
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta, binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import (  # noqa: E402
    FAIL_BELOW, TARGETS, TEST_STRATA, VAL_STRATA, _p, arm_predictions, by_item, choose_tau, fit_temperature,
    load_meta, metrics,
)

H2_STRATA = {"T-szallito": ["T-szallito"], "T-kategoria": ["T-kozeli", "T-tavoli"],
             "T-kozeli": ["T-kozeli"], "T-tavoli": ["T-tavoli"], "T-belso": ["T-belso"]}
CLUSTER_KEY = {"T-szallito": "supplier"}  # a többi rétegen: cikk
NO_GAIN = 0.02  # H2: a CI felső határa ez alatt → „nem általánosít”


# --- vektorizált mérőszámok a bootstraphoz --------------------------------------------------------------

class Arm:
    """Egy kar predikciói tömbökben, a közös item-index szerint."""

    def __init__(self, preds: dict, ids: list[str], meta: dict):
        self.conf = np.array([preds[i][1] if i in preds else np.nan for i in ids])
        self.assign = np.array([i in preds and preds[i][0] is not None for i in ids])
        self.correct = np.array([i in preds and preds[i][0] == meta[i]["gold"] for i in ids])


class CP:
    """Clopper–Pearson egyoldali 95%-os alsó korlátok táblája (k, n) szerint."""

    def __init__(self, nmax: int):
        n = np.arange(nmax + 1)[:, None]
        k = np.arange(nmax + 1)[None, :]
        with np.errstate(invalid="ignore"):
            t = beta.ppf(0.05, k, n - k + 1)
        t[:, 0] = 0.0
        self.t = np.where(k <= n, t, np.nan)

    def __call__(self, k: np.ndarray, n: np.ndarray) -> np.ndarray:
        return self.t[n, k]


def tau_fast(a: Arm, idx: np.ndarray, scored: np.ndarray, target: float, cp: CP) -> float:
    sel = idx[scored[idx] & a.assign[idx]]
    if len(sel) == 0:
        return math.inf
    o = sel[np.argsort(-a.conf[sel], kind="stable")]
    c = a.conf[o]
    k = np.cumsum(a.correct[o])
    n = np.arange(1, len(o) + 1)
    boundary = np.append(c[1:] != c[:-1], True)  # holtversenyen belül nem vágunk
    ok = boundary & (cp(k, n) >= target)
    return float(c[np.nonzero(ok)[0][-1]]) if ok.any() else math.inf


def metrics_fast(a: Arm, idx: np.ndarray, scored: np.ndarray, tau: float) -> dict:
    s = idx[scored[idx]]
    n = len(s)
    if n == 0:
        return {}
    asg = a.assign[s] & (a.conf[s] >= tau)
    cov = asg.sum() / n
    prec = a.correct[s][asg].mean() if asg.any() else math.nan
    ad = s[a.assign[s]]
    o = ad[np.argsort(-a.conf[ad], kind="stable")]
    err = np.cumsum(~a.correct[o])
    aurc = float((err / np.arange(1, len(o) + 1)).sum() / n) if len(o) else 0.0
    confs, okv = a.conf[s], a.correct[s].astype(float)
    order = np.argsort(confs)
    ece = sum(abs(okv[b].mean() - confs[b].mean()) * len(b) / n for b in np.array_split(order, 15) if len(b))
    return {"lef": float(cov), "prec": float(prec), "aurc": aurc, "ece": float(ece), "acc": float(okv.mean())}


# --- újramintavételezés -------------------------------------------------------------------------------

class Resampler:
    def __init__(self, ids: list[str], meta: dict, groups: dict[str, list[str]], keys: dict[str, str]):
        pos = {i: n for n, i in enumerate(ids)}
        self.groups = {}
        for g, members in groups.items():
            cl = defaultdict(list)
            for i in members:
                cl[meta[i].get(keys.get(g, "article"))].append(pos[i])
            self.groups[g] = [np.array(v) for v in cl.values()]

    def draw(self, g: str, rng: np.random.Generator) -> np.ndarray:
        cl = self.groups[g]
        pick = rng.integers(0, len(cl), len(cl))
        return np.concatenate([cl[k] for k in pick])

    def full(self, g: str) -> np.ndarray:
        return np.concatenate(self.groups[g])


def p_two_sided(x: np.ndarray) -> float:
    return min(1.0, 2 * min(float((x <= 0).mean()), float((x >= 0).mean())))


def summarize(x: list[float]) -> dict:
    a = np.array([v for v in x if not math.isnan(v)])
    return {"delta_median": float(np.median(a)), "ci95": [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))],
            "p_ketoldali": p_two_sided(a), "reps": int(len(a))}


def holm_family(ps: dict[str, tuple[float, bool]], alpha: float = 0.05) -> dict:
    """ps: név → (kétoldali p, a jó irányba mutat-e). Holm lépcsős eljárás."""
    order = sorted(ps, key=lambda k: ps[k][0])
    res, still = {}, True
    for rank, k in enumerate(order):
        p, good = ps[k]
        thr = alpha / (len(order) - rank)
        sig = still and p <= thr
        still = sig
        res[k] = {"p": p, "holm_kuszob": thr, "szignifikans": sig, "jo_irany": good}
    return res


# --- a fő elemzés -------------------------------------------------------------------------------------

def load_arm(val_path: str, test_path: str, meta: dict, arm: str) -> tuple[dict, float]:
    rv, rt = read_jsonl(_p(val_path)), read_jsonl(_p(test_path))
    temp = fit_temperature([r for r in rv if r["perm"] == 0], meta)
    prm = {"temp": temp}
    preds = {**arm_predictions(arm, by_item(rv, None), meta, prm), **arm_predictions(arm, by_item(rt, None), meta, prm)}
    return preds, temp


def point_block(preds: dict, meta: dict, val_ids: list[str], test_ids: list[str]) -> dict:
    out = {}
    for tgt, tn in TARGETS:
        tau = choose_tau(preds, meta, val_ids, tgt)
        fb = FAIL_BELOW[tn]
        out[tn] = {"tau": tau, "val": metrics(preds, meta, val_ids, tau, fb),
                   "teszt": metrics(preds, meta, test_ids, tau, fb),
                   "retegek": {s: metrics(preds, meta, [i for i in test_ids if meta[i]["split"] == s], tau, fb)
                               for s in TEST_STRATA}}
    return out


def breakdowns(preds: dict, meta: dict, test_ids: list[str], tau: float) -> dict:
    def grp(f):
        g = defaultdict(list)
        for i in test_ids:
            g[str(f(i))].append(i)
        return {k: metrics(preds, meta, v, tau) for k, v in sorted(g.items())}
    amb = [i for i in test_ids if meta[i].get("ketertelmu")]
    crossed = [i for i in amb if preds[i][0] is not None and preds[i][1] >= tau]
    soft_hit = sum(preds[i][0] in (meta[i].get("soft") or [meta[i]["gold"]]) for i in crossed)
    return {"x_vs_nemx": grp(lambda i: "X" if meta[i]["gold"] is None else "nem-X"),
            "listahossz": grp(lambda i: meta[i].get("n_options")),
            "x_fajta": grp(lambda i: meta[i].get("x_fajta") or "-"),
            "ketertelmu": {"n": len(amb), "atlepes": len(crossed) / len(amb) if amb else None,
                           "soft_gold_talalat_az_atlepokon": soft_hit / len(crossed) if crossed else None}}


def mcnemar(pa: dict, pb: dict, meta: dict, ids: list[str]) -> dict:
    s = [i for i in ids if not meta[i].get("ketertelmu")]
    b = sum(pa[i][0] == meta[i]["gold"] and pb[i][0] != meta[i]["gold"] for i in s)
    c = sum(pa[i][0] != meta[i]["gold"] and pb[i][0] == meta[i]["gold"] for i in s)
    return {"csak_a_jo": b, "csak_b_jo": c, "p_egzakt": binomtest(b, b + c).pvalue if b + c else 1.0}


def repeat_noise(p0: dict, p0r: dict, meta: dict, val_ids: list[str], test_ids: list[str], r0: list, r0r: list) -> dict:
    s = [i for i in test_ids if not meta[i].get("ketertelmu")]
    flip = sum(p0[i][0] != p0r[i][0] for i in s) / len(s)
    tau = choose_tau(p0, meta, val_ids, 0.95)
    lp = {(r["id"], r["perm"]): r["label_logprobs"] for r in r0}
    dp = [abs(math.exp(v) - math.exp(lp[(r["id"], r["perm"])][k])) for r in r0r if (r["id"], r["perm"]) in lp
          for k, v in r["label_logprobs"].items()]
    return {"top_cimke_billenes": flip, "abs_dp_atlag": float(np.mean(dp)), "abs_dp_max": float(np.max(dp)),
            "lef95_kulonbseg_rogzitett_tau": metrics(p0r, meta, test_ids, tau)["besorolasi_lefedettseg"]
            - metrics(p0, meta, test_ids, tau)["besorolasi_lefedettseg"]}


def supplier_permutation(pa_list: list[dict], pb: dict, meta: dict, val_ids: list[str], ids: list[str],
                         reps: int, rng: np.random.Generator) -> dict:
    """H2, T-szállító: szállítónkénti előjelcsere a lefedettség@95-különbségen, rögzített val-τ-val."""
    taus = [choose_tau(p, meta, val_ids, 0.95) for p in pa_list]
    tb = choose_tau(pb, meta, val_ids, 0.95)
    by_s = defaultdict(list)
    for i in ids:
        if not meta[i].get("ketertelmu"):
            by_s[meta[i]["supplier"]].append(i)
    n = sum(len(v) for v in by_s.values())
    d = []
    for v in by_s.values():
        a = np.mean([sum(p[i][0] is not None and p[i][1] >= t for i in v) for p, t in zip(pa_list, taus)])
        b = sum(pb[i][0] is not None and pb[i][1] >= tb for i in v)
        d.append((a - b) / n)
    d = np.array(d)
    obs = d.sum()
    exact = len(d) <= 16  # a teszten 14 szállító: mind a 2^14 előjel-kombináció végigszámolható
    if exact:
        signs = 1.0 - 2.0 * ((np.arange(2 ** len(d))[:, None] >> np.arange(len(d))) & 1)
    else:
        signs = rng.choice([-1.0, 1.0], size=(reps, len(d)))
    null = (signs * d).sum(axis=1)
    return {"szallitok": len(d), "delta": float(obs), "egzakt": exact,
            "p_ketoldali": float((np.abs(null) >= abs(obs) - 1e-12).mean())}


def analyse(args) -> dict:
    meta = load_meta(_p(args.items))
    l1, t_l1 = load_arm(args.l0_val, args.l0_test, meta, "perm_avg")
    l0, _ = load_arm(args.l0_val, args.l0_test, meta, "nyers")
    l3 = {}
    for spec in args.l3:
        name, v, t = spec.split(":")
        l3[name] = load_arm(v, t, meta, "temp")[0]
    val_ids = [i for i in l1 if meta[i]["split"] in VAL_STRATA]
    test_ids = [i for i in l1 if meta[i]["split"] in TEST_STRATA]
    for name, p in l3.items():
        miss = [i for i in val_ids + test_ids if i not in p]
        if miss:
            raise SystemExit(f"{name}: {len(miss)} item hiányzik a kiolvasásból")

    res = {"motor": args.motor, "bemenetek": {k: v for k, v in vars(args).items()},
           "n_val": len(val_ids), "n_teszt": len(test_ids), "L1_temperature": t_l1,
           "pont": {"L0": point_block(l0, meta, val_ids, test_ids), "L1csillag": point_block(l1, meta, val_ids, test_ids),
                    **{f"L3_{k}": point_block(p, meta, val_ids, test_ids) for k, p in l3.items()}}}
    tau_l3 = {k: choose_tau(p, meta, val_ids, 0.95) for k, p in l3.items()}
    res["bontasok"] = {"L1csillag": breakdowns(l1, meta, test_ids, choose_tau(l1, meta, val_ids, 0.95)),
                       **{f"L3_{k}": breakdowns(p, meta, test_ids, tau_l3[k]) for k, p in l3.items()}}
    res["mcnemar_pontossag"] = {f"L3_{k}_vs_L1csillag": mcnemar(p, l1, meta, test_ids) for k, p in l3.items()}

    l2a = None
    if args.l2a:
        v, t = args.l2a.split(":")
        l2a = load_arm(v, t, meta, "perm_avg")[0]
        res["pont"]["L2a"] = point_block(l2a, meta, val_ids, test_ids)
    if args.l0r_test:
        r0, r0r = read_jsonl(_p(args.l0_test)), read_jsonl(_p(args.l0r_test))
        l0r = {**{i: l0[i] for i in val_ids},
               **arm_predictions("nyers", by_item(r0r, None), meta, {})}
        res["ismetlesi_zaj_L0_L0vesszo"] = repeat_noise(l0, l0r, meta, val_ids, test_ids, r0, r0r)

    # --- bootstrap ---------------------------------------------------------------------------------
    ids = val_ids + test_ids
    groups = {"val": val_ids, **{s: [i for i in test_ids if meta[i]["split"] == s] for s in TEST_STRATA}}
    rs = Resampler(ids, meta, groups, CLUSTER_KEY)
    scored = np.array([not meta[i].get("ketertelmu") for i in ids])
    cp = CP(len(ids) + 1)
    A1 = Arm(l1, ids, meta)
    A3 = {k: Arm(p, ids, meta) for k, p in l3.items()}
    A2 = Arm(l2a, ids, meta) if l2a else None
    seeds = list(A3)
    rng = np.random.default_rng(args.seed)
    acc = defaultdict(list)
    for _ in range(args.reps):
        v = rs.draw("val", rng)
        t = {s: rs.draw(s, rng) for s in TEST_STRATA}
        t["teszt"] = np.concatenate([t[s] for s in TEST_STRATA])
        for h2, members in H2_STRATA.items():
            t[h2] = np.concatenate([t[s] for s in members]) if len(members) > 1 else t[members[0]]
        drawn = [seeds[k] for k in rng.integers(0, len(seeds), len(seeds))]
        for tgt, tn in TARGETS:
            tb = tau_fast(A1, v, scored, tgt, cp)
            ta = {k: tau_fast(A3[k], v, scored, tgt, cp) for k in set(drawn)}
            for part in ["teszt", *H2_STRATA]:
                mb = metrics_fast(A1, t[part], scored, tb)
                ma = [metrics_fast(A3[k], t[part], scored, ta[k]) for k in drawn]
                acc[f"{part}:lef{tn}"].append(np.mean([m["lef"] for m in ma]) - mb["lef"])
                if tn == "95":
                    acc[f"{part}:aurc"].append(np.mean([m["aurc"] for m in ma]) - mb["aurc"])
                    acc[f"{part}:ece"].append(np.mean([m["ece"] for m in ma]) - mb["ece"])
            if A2 is not None and tn == "95":
                m2 = metrics_fast(A2, t["teszt"], scored, tau_fast(A2, v, scored, tgt, cp))
                acc["L2a:lef95"].append(m2["lef"] - metrics_fast(A1, t["teszt"], scored, tb)["lef"])
    boot = {k: summarize(x) for k, x in acc.items()}
    res["bootstrap"] = {"reps": args.reps, "seed": args.seed, "L3_minus_L1csillag": boot}

    # --- H1 ----------------------------------------------------------------------------------------
    hf = holm_family({"lef95": (boot["teszt:lef95"]["p_ketoldali"], boot["teszt:lef95"]["delta_median"] > 0),
                      "aurc": (boot["teszt:aurc"]["p_ketoldali"], boot["teszt:aurc"]["delta_median"] < 0)})
    pt = res["pont"]
    l1p = pt["L1csillag"]["95"]["teszt"]
    for ep in ("lef95", "aurc"):
        reasons = []
        if not hf[ep]["szignifikans"]:
            reasons.append("nem szignifikáns a Holm-küszöbön")
        if not hf[ep]["jo_irany"]:
            reasons.append("az L1★ javára mutat")
        for k in seeds:
            s3 = pt[f"L3_{k}"]["95"]["teszt"]
            if ep == "lef95" and s3["besorolasi_lefedettseg"] <= l1p["besorolasi_lefedettseg"]:
                reasons.append(f"seed {k}: pontbecslés ≤ L1★")
            if ep == "aurc" and s3["aurc"] >= l1p["aurc"]:
                reasons.append(f"seed {k}: pontbecslés ≥ L1★")
            if ep == "lef95" and s3["precizitas_bukas"]:
                reasons.append(f"seed {k}: precizitás-bukás a teljes teszten")
        hf[ep]["cafolat"] = reasons
        hf[ep]["all"] = not reasons
    res["H1"] = {**hf, "teljesul": hf["lef95"]["all"] or hf["aurc"]["all"],
                 "masodlagos_lef90": boot["teszt:lef90"]}

    # --- H2 ----------------------------------------------------------------------------------------
    h2 = {}
    for part in H2_STRATA:
        b = boot[f"{part}:lef95"]
        lo, hi = b["ci95"]
        h2[part] = {**b, "itelet": "általánosít" if lo > 0 else ("nem általánosít" if hi < NO_GAIN else "nem eldönthető"),
                    "aurc": boot[f"{part}:aurc"]}
    st = [i for i in test_ids if meta[i]["split"] == "T-szallito"]
    h2["T-szallito"]["szallito_permutacio"] = supplier_permutation(list(l3.values()), l1, meta, val_ids, st,
                                                                   args.reps, rng)
    res["H2"] = h2

    # --- H4, H5 (egy Holm-család) ----------------------------------------------------------------------
    fam = {"H5_ece": (boot["teszt:ece"]["p_ketoldali"], boot["teszt:ece"]["delta_median"] < 0)}
    if A2 is not None:
        fam["H4_L2a_lef95"] = (boot["L2a:lef95"]["p_ketoldali"], boot["L2a:lef95"]["delta_median"] > 0)
    res["H4_H5_holm"] = holm_family(fam)
    res["H5_ece"] = boot["teszt:ece"]
    if A2 is not None:
        res["H4_L2a"] = boot["L2a:lef95"]
    return res


# --- egységpróba ---------------------------------------------------------------------------------------

def selftest(items: str) -> None:
    """A vektorizált τ és mérőszámok egyezése az elemzes.py-éval, valós F3 val-kiolvasásokon."""
    meta = load_meta(_p(items))
    for path, arm in [("eredmenyek/F3/l3mixse_s1/vllm_val.jsonl", "temp"), ("eredmenyek/F2/vllm_val.jsonl", "perm_avg"),
                      ("eredmenyek/F2/vllm_val.jsonl", "nyers")]:
        rows = read_jsonl(_p(path))
        prm = {"temp": fit_temperature([r for r in rows if r["perm"] == 0], meta)}
        p = arm_predictions(arm, by_item(rows, None), meta, prm)
        ids = [i for i in p if meta[i]["split"] in VAL_STRATA]
        A = Arm(p, ids, meta)
        sc = np.array([not meta[i].get("ketertelmu") for i in ids])
        cp = CP(len(ids) + 1)
        idx = np.arange(len(ids))
        rng = np.random.default_rng(1)
        for trial in range(4):
            sub = idx if trial == 0 else rng.choice(idx, len(idx))  # visszatevéses minta: duplikátumok is
            sub_ids = [ids[k] for k in sub]
            for tgt, tn in TARGETS:
                t_ref, t_fast = choose_tau(p, meta, sub_ids, tgt), tau_fast(A, sub, sc, tgt, cp)
                assert t_ref == t_fast, (path, arm, tn, trial, t_ref, t_fast)
                m_ref, m_fast = metrics(p, meta, sub_ids, t_ref), metrics_fast(A, sub, sc, t_fast)
                for a, b in [("besorolasi_lefedettseg", "lef"), ("aurc", "aurc"), ("ece", "ece"), ("pontossag", "acc")]:
                    assert abs(m_ref[a] - m_fast[b]) < 1e-12, (path, arm, a, m_ref[a], m_fast[b])
        print(f"ok: {path} {arm}")
    hf = holm_family({"a": (0.2, True), "b": (0.001, True)})
    assert hf["b"]["szignifikans"] and not hf["a"]["szignifikans"]
    hf = holm_family({"a": (0.03, True), "b": (0.04, True)})
    assert not hf["a"]["szignifikans"] and not hf["b"]["szignifikans"]
    print("ok: holm")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "onteszt":
        selftest(sys.argv[2] if len(sys.argv) > 2 else "adat/f1")
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--motor", required=True, choices=["vllm", "hf"])
    ap.add_argument("--l0-val", required=True)
    ap.add_argument("--l0-test", required=True)
    ap.add_argument("--l0r-test", default="", help="az L0 ismétlése a sor végén (ismétlési zaj)")
    ap.add_argument("--l3", action="append", required=True, help="név:val-kiolvasás:teszt-kiolvasás (seedenként)")
    ap.add_argument("--l2a", default="", help="val:teszt (HF; H4)")
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    res = analyse(args)
    write_json(_p(args.out), res)
    print(json.dumps({"H1": {k: res["H1"][k] for k in ("lef95", "aurc", "teljesul")},
                      "H2": {k: v["itelet"] for k, v in res["H2"].items()}}, ensure_ascii=False, indent=1, default=str))


if __name__ == "__main__":
    main()
