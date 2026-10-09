"""Mérőszámok, kalibráció és statisztika (runbook 2., 5. és 8. pont).

Bemenet: kiolvasás-fájlok (kiolvaso.py / hf_kiolvaso.py formátum) + az item-fájlok (meta).

Mérőszámok (rétegenként; a kétértelmű itemek nem pontozottak, külön jelentve):
  besorolási lefedettség@95 — a réteg itemjeinek hányada, amely τ fölötti NEM-X döntést kap;
      τ a val-on: a legkisebb küszöb, amely fölött a besorolások precizitásának egyoldali 95%-os
      Clopper–Pearson alsó korlátja ≥ 0,95. Teszt-precizitás < 0,93 → precizitás-bukás.
  besorolási lefedettség@90 — előre rögzített másodlagos (2026-10-05): ugyanez 0,90-es céllal, saját τ-val;
      teszt-precizitás < 0,88 → precizitás-bukás. A bootstrap a Δ@95 mellett a Δ@90-et és a ΔAURC-t is adja.
  AURC (besorolásokra), döntési lefedettség@95 (X is automatikus), ECE (15 egyenlő tömegű bin),
  X-precizitás / X-fedés, kétértelmű-átlépés, érték-súlyozott lefedettség (99. pc winsorizálva).
Kalibrációs karok (L1): nyers, temperature, contextual (content-free futásból), batch (val-on
  befagyasztott címke-bias, λ∈{0,5;0,75;1}), permutáció-átlag (+temperature).
Bootstrap: klaszterezett (klaszter = cikk; T-szállító: szállító), a val is újramintavételezve és
  τ replikánként újraválasztva; párosított különbségek karok között.

Példa:
  python3 eszkozok/elemzes.py --items adat/f1 --val eredmenyek/F2/vllm_val.jsonl --test eredmenyek/F2/vllm_test.jsonl \
      --out eredmenyek/F2/L1_vllm.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json  # noqa: E402

LABELS = list("ABCDEFGHIJ") + ["X"]
# (célprecizitás, név, precizitás-bukás határa): @95 elsődleges; @90 előre rögzített másodlagos (user-döntés, 2026-10-05)
TARGETS = [(0.95, "95"), (0.90, "90")]
FAIL_BELOW = {"95": 0.93, "90": 0.88}
TEST_STRATA = ["T-belso", "T-szallito", "T-kozeli", "T-tavoli"]
VAL_STRATA = ["val-belso", "val-szallito"]


def _p(p: str) -> Path:
    q = Path(p)
    return q if q.is_absolute() else EXP / q


# --- adatelőkészítés --------------------------------------------------------------

def load_meta(items_dir: Path) -> dict[str, dict]:
    meta = {}
    for f in sorted(items_dir.glob("items_*.jsonl")):
        if ".pre_atnezes" in f.name:  # az átnézés előtti mentés (atnezes.py alkalmaz) — régi gold
            continue
        for it in read_jsonl(f):
            meta[it["id"]] = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None, **it["meta"]}
    return meta


def by_item(rows: list[dict], perm: int | None = 0) -> dict[str, list[dict]]:
    g = defaultdict(list)
    for r in rows:
        if perm is None or r["perm"] == perm:
            g[r["id"]].append(r)
    return g


def option_scores(r: dict, bias: dict | None = None, lam: float = 0.0, temp: float = 1.0) -> dict:
    """Opció-id → szűkített valószínűség (az X kulcsa None) egy kiolvasott sorból."""
    lp = {lab: v for lab, v in r["label_logprobs"].items()}
    z = {lab: (v - (lam * bias.get(lab, 0.0) if bias else 0.0)) / temp for lab, v in lp.items()}
    m = max(z.values())
    e = {lab: math.exp(v - m) for lab, v in z.items()}
    s = sum(e.values())
    return {(None if lab == "X" else r["order"][r["labels"].index(lab)]): e[lab] / s for lab in lp}


def decide(scores: dict) -> tuple[object, float]:
    pred = max(scores, key=lambda k: scores[k])
    return pred, scores[pred]


# --- kalibrációs karok ------------------------------------------------------------

def fit_temperature(val_rows: list[dict], meta: dict) -> float:
    def nll(logt: float) -> float:
        t = math.exp(logt)
        tot = 0.0
        for r in val_rows:
            if meta[r["id"]].get("ketertelmu"):
                continue
            sc = option_scores(r, temp=t)
            tot -= math.log(max(1e-12, sc.get(meta[r["id"]]["gold"], 1e-12)))
        return tot
    return float(math.exp(minimize_scalar(nll, bounds=(-3, 4), method="bounded").x))


def label_bias(val_rows: list[dict]) -> dict:
    """Batch calibration: címke-pozíciónkénti átlagos szűkített log-valószínűség a val-on (befagyasztva)."""
    acc = defaultdict(list)
    for r in val_rows:
        sc = option_scores(r)
        for lab in r["labels"]:
            oid = None if lab == "X" else r["order"][r["labels"].index(lab)]
            acc[lab].append(math.log(max(1e-12, sc[oid])))
    return {lab: float(np.mean(v)) for lab, v in acc.items()}


def contextual_bias(cf_rows: list[dict]) -> dict[str, dict]:
    """Contextual calibration: itemenként a content-free futás címke-logprobjai (bias = log p_cf)."""
    return {r["id"]: {lab: v for lab, v in r["label_logprobs"].items()} for r in cf_rows if r["perm"] == 0}


def arm_predictions(arm: str, rows_by: dict, meta: dict, params: dict) -> dict[str, tuple]:
    """Itemenként (pred, conf, scores) az adott kalibrációs karral."""
    out = {}
    for iid, rs in rows_by.items():
        if arm == "perm_avg":
            acc = defaultdict(float)
            for r in rs:
                for k, v in option_scores(r, temp=params.get("temp", 1.0)).items():
                    acc[k] += v / len(rs)
            sc = dict(acc)
        else:
            r0 = next((r for r in rs if r["perm"] == 0), rs[0])
            if arm == "nyers":
                sc = option_scores(r0)
            elif arm == "temp":
                sc = option_scores(r0, temp=params["temp"])
            elif arm == "batch":
                sc = option_scores(r0, bias=params["bias"], lam=params["lam"], temp=params.get("temp", 1.0))
            elif arm == "contextual":
                b = params["cf"].get(iid)
                sc = option_scores(r0, bias=b, lam=1.0) if b else option_scores(r0)
            else:
                raise ValueError(arm)
        out[iid] = (*decide(sc), sc)
    return out


# --- mérőszámok -------------------------------------------------------------------

def cp_lower(k: int, n: int, alpha: float = 0.05) -> float:
    return float(beta.ppf(alpha, k, n - k + 1)) if k > 0 else 0.0


def choose_tau(preds: dict, meta: dict, ids: list[str], target: float = 0.95) -> float:
    """A legkisebb küszöb, amely fölött a besorolások CP-alsó korlátja ≥ target (különben +∞)."""
    asg = sorted(((preds[i][1], preds[i][0] == meta[i]["gold"]) for i in ids
                  if not meta[i].get("ketertelmu") and preds[i][0] is not None), key=lambda t: -t[0])
    best = math.inf
    k = 0
    for n, (conf, ok) in enumerate(asg, 1):
        k += ok
        if n < len(asg) and asg[n][0] == conf:
            continue  # holtverseny: a küszöb csak konf-határon vágható
        if cp_lower(k, n) >= target:
            best = conf
    return best


def metrics(preds: dict, meta: dict, ids: list[str], tau: float, fail_below: float = 0.93) -> dict:
    scored = [i for i in ids if not meta[i].get("ketertelmu")]
    amb = [i for i in ids if meta[i].get("ketertelmu")]
    n = len(scored)
    if n == 0:
        return {}
    asg = [i for i in scored if preds[i][0] is not None and preds[i][1] >= tau]
    corr = sum(preds[i][0] == meta[i]["gold"] for i in asg)
    vals = np.array([meta[i].get("value", 0.0) for i in scored], dtype=float)
    cap = np.percentile(vals, 99) if len(vals) else 0
    vmap = {i: min(meta[i].get("value", 0.0), cap) for i in scored}
    # AURC a besorolásokon
    order = sorted([i for i in scored if preds[i][0] is not None], key=lambda i: -preds[i][1])
    err, aurc = 0, 0.0
    for k, i in enumerate(order, 1):
        err += preds[i][0] != meta[i]["gold"]
        aurc += (err / k) / n
    # ECE (egyenlő tömegű binek), top-címke helyessége
    confs = np.array([preds[i][1] for i in scored])
    okv = np.array([preds[i][0] == meta[i]["gold"] for i in scored], dtype=float)
    idx = np.argsort(confs)
    ece = sum(abs(okv[b].mean() - confs[b].mean()) * len(b) / n for b in np.array_split(idx, 15) if len(b))
    # döntési lefedettség (X is automatikus)
    dec = [i for i in scored if preds[i][1] >= tau]
    dec_ok = sum(preds[i][0] == meta[i]["gold"] for i in dec)
    xp = [i for i in scored if preds[i][0] is None]
    xg = [i for i in scored if meta[i]["gold"] is None]
    return {
        "n": n, "kétértelmű_n": len(amb),
        "besorolasi_lefedettseg": len(asg) / n, "besorolasi_precizitas": corr / len(asg) if asg else None,
        "precizitas_bukas": bool(asg) and corr / len(asg) < fail_below,
        "ertek_sulyozott_lefedettseg": sum(vmap[i] for i in asg) / max(1e-9, sum(vmap.values())),
        "aurc": aurc, "ece": float(ece), "pontossag": float(okv.mean()),
        "dontesi_lefedettseg": len(dec) / n, "dontesi_precizitas": dec_ok / len(dec) if dec else None,
        "x_precizitas": sum(meta[i]["gold"] is None for i in xp) / len(xp) if xp else None,
        "x_fedes": sum(preds[i][0] is None for i in xg) / len(xg) if xg else None,
        "ketertelmu_atlepes": (sum(preds[i][0] is not None and preds[i][1] >= tau for i in amb) / len(amb)) if amb else None,
    }


# --- klaszterezett bootstrap --------------------------------------------------------

def cluster_resample(ids: list[str], meta: dict, key: str, rng: np.random.Generator) -> list[str]:
    cl = defaultdict(list)
    for i in ids:
        cl[meta[i].get(key)].append(i)
    keys = list(cl)
    pick = rng.integers(0, len(keys), len(keys))
    return [i for k in pick for i in cl[keys[k]]]


def bootstrap_diff(pa: dict, pb: dict, meta: dict, val_ids: list[str], test_ids: list[str], key: str,
                   reps: int = 2000, seed: int = 0) -> dict:
    """Párosított Δ (a − b), val-újraküszöböléssel, klaszterezett bootstrap, ugyanazokon az újramintákon:
    besorolási lefedettség@95 (elsődleges), @90 és AURC (előre rögzített másodlagosak, 2026-10-05)."""
    rng = np.random.default_rng(seed)
    d = defaultdict(list)
    for _ in range(reps):
        v = cluster_resample(val_ids, meta, "article", rng)
        t = cluster_resample(test_ids, meta, key, rng)
        for tgt, name in TARGETS:
            ma = metrics(pa, meta, t, choose_tau(pa, meta, v, tgt))
            mb = metrics(pb, meta, t, choose_tau(pb, meta, v, tgt))
            if ma and mb:
                d[f"lef{name}"].append(ma["besorolasi_lefedettseg"] - mb["besorolasi_lefedettseg"])
                if name == "95":
                    d["aurc"].append(ma["aurc"] - mb["aurc"])
    out = {}
    for k, xs in d.items():
        a = np.array(xs)
        # kétoldali bootstrap p: 2 · min(P(Δ ≤ 0), P(Δ ≥ 0)), legfeljebb 1
        p = min(1.0, 2 * min(float((a <= 0).mean()), float((a >= 0).mean())))
        out[k] = {"delta_median": float(np.median(a)), "ci95": [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))],
                  "p_ketoldali": p, "reps": len(a)}
    return out


def holm(boot: dict, alpha: float = 0.05) -> dict:
    """H1 (2026-10-05): társ-elsődleges @95 (a > b jó) és AURC (a < b jó), Holm-korrekcióval. A végpont akkor
    szignifikáns az a javára, ha a Holm-küszöb alatt van ÉS a medián Δ a jó irányba mutat."""
    ends = {"lef95": (boot["lef95"], +1), "aurc": (boot["aurc"], -1)}
    order = sorted(ends, key=lambda k: ends[k][0]["p_ketoldali"])
    res, still = {}, True
    for rank, k in enumerate(order):
        b, sign = ends[k]
        thr = alpha / (len(order) - rank)
        sig = still and b["p_ketoldali"] <= thr
        still = sig
        res[k] = {"p": b["p_ketoldali"], "holm_kuszob": thr, "szignifikans": sig,
                  "javara": "a" if sign * b["delta_median"] > 0 else "b"}
    res["H1_teljesul"] = any(v["szignifikans"] and v["javara"] == "a" for v in res.values() if isinstance(v, dict))
    return res


# --- fő -----------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True, help="az item-fájlok könyvtára (items_*.jsonl)")
    ap.add_argument("--val", required=True)
    ap.add_argument("--test", default="", help="üres = csak val (F2: kar- és küszöbválasztás, a teszt az F4-ben)")
    ap.add_argument("--cf-val", default="")
    ap.add_argument("--cf-test", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=0, help="bootstrap ismétlés a karok párosított összevetéséhez (0 = nincs)")
    args = ap.parse_args()
    meta = load_meta(_p(args.items))
    val_rows = read_jsonl(_p(args.val))
    test_rows = read_jsonl(_p(args.test)) if args.test else []
    val_by, test_by = by_item(val_rows, None), by_item(test_rows, None)
    val0 = [r for r in val_rows if r["perm"] == 0]
    val_ids = [i for i in val_by if meta[i]["split"] in VAL_STRATA]
    has_perms = len({r["perm"] for r in val_rows}) > 1

    temp = fit_temperature(val0, meta)
    bias = label_bias(val0)
    arms = {"nyers": {}, "temp": {"temp": temp}}
    for lam in (0.5, 0.75, 1.0):
        arms[f"batch_{lam}"] = {"bias": bias, "lam": lam, "temp": temp}
    if args.cf_val and args.cf_test:
        cf = {**contextual_bias(read_jsonl(_p(args.cf_val))), **contextual_bias(read_jsonl(_p(args.cf_test)))}
        arms["contextual"] = {"cf": cf}
    elif args.cf_val and not args.test:
        cf = contextual_bias(read_jsonl(_p(args.cf_val)))
        arms["contextual"] = {"cf": cf}
    if has_perms:
        arms["perm_avg"] = {"temp": temp}

    res = {"temperature": temp, "label_bias": bias, "karok": {}}
    preds_val, preds_test = {}, {}
    for name, prm in arms.items():
        kind = name.split("_")[0] if name.startswith("batch") else name
        pv = arm_predictions("batch" if kind == "batch" else name, val_by, meta, prm)
        pt = arm_predictions("batch" if kind == "batch" else name, test_by, meta, prm)
        preds_val[name], preds_test[name] = pv, pt
        for tgt, tn in TARGETS:
            tau = choose_tau(pv, meta, val_ids, tgt)
            fb = FAIL_BELOW[tn]
            blk = {
                "tau": tau, "val": metrics(pv, meta, val_ids, tau, fb),
                "teszt": {sp: metrics(pt, meta, [i for i in test_by if meta[i]["split"] == sp], tau, fb) for sp in TEST_STRATA},
                "teszt_pool": metrics(pt, meta, [i for i in test_by if meta[i]["split"] in TEST_STRATA], tau, fb),
            }
            if tn == "95":
                res["karok"][name] = blk
            else:
                res["karok"][name][f"at{tn}"] = blk
    # L1★: a val-on a legnagyobb lefedettség@95; holtversenyben (a pilot szerint ~0 minden karon) a @90, majd az ECE
    best = max(res["karok"], key=lambda k: (res["karok"][k]["val"].get("besorolasi_lefedettseg", 0),
                                           res["karok"][k]["at90"]["val"].get("besorolasi_lefedettseg", 0),
                                           -res["karok"][k]["val"].get("ece", 1)))
    res["L1_csillag"] = best
    if args.reps and test_rows:
        test_ids = [i for i in test_by if meta[i]["split"] in TEST_STRATA]
        # a bootstrap a val-on újraküszöböl → a kar val- ÉS teszt-predikciói kellenek (2026-10-04, pilot-próbafutás)
        pa, pb = {**preds_val[best], **preds_test[best]}, {**preds_val["nyers"], **preds_test["nyers"]}
        res["bootstrap_L1csillag_vs_nyers"] = bootstrap_diff(pa, pb, meta, val_ids, test_ids, "article", reps=args.reps)
    if not test_rows:
        g = res["karok"][best]["val"].get("besorolasi_lefedettseg", 0)
        res["F2_kapu"] = {"L1_csillag_val_lefedettseg95": g, "kevés_ter_a_LoRA_nak": g >= 0.90,
                          "L1_csillag_val_lefedettseg90": res["karok"][best]["at90"]["val"].get("besorolasi_lefedettseg", 0)}
    write_json(_p(args.out), res)
    print(json.dumps({k: {"tau": v["tau"], "val_lef": v["val"].get("besorolasi_lefedettseg"),
                          "val_lef90": v["at90"]["val"].get("besorolasi_lefedettseg"), "val_aurc": v["val"].get("aurc"),
                          "pool_lef": v["teszt_pool"].get("besorolasi_lefedettseg"), "pool_prec": v["teszt_pool"].get("besorolasi_precizitas"),
                          "pool_ece": v["teszt_pool"].get("ece")} for k, v in res["karok"].items()} | {"L1*": best}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
