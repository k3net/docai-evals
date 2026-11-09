"""03-as kör — az F4 elemzése (03-runbook 7. pont, v1; Dani jóváhagyása és pontosításai, 2026-10-14).

Csak a technikai lezárás (`f4_teljesseg03.py`: minden szükséges karon pontos (item_id, perm) egyezés) után fut. Ami a
rögzített v1-en kívül esik, az leíró, és a kimenetben külön blokkban áll.

Karok (a kiolvasási mód és a temperature a val pontbecsléséből rögzítve; a τ@95 a bootstrapban replikánként újra):
  L1★   a bázis, F2 (`qwen_val`, `qwen_eval`), a 03 val-on választott kalibrációs karral (perm-átlag, T = 1,431).
  L0′   a bázis ismételt eval-kiolvasása új vLLM-példányon (F4 `l0r`), az L1★ kalibrációjával és τ-jával.
  G3 s1–s3, G3-kemény s1, G3-hu s1: val az F3-ból, eval az F4-ből; a 03 val-on választott kalibrációs karral (nyers /
        temperature / perm-átlag / batch, a val lef@95 szerint; az F2 L1★-szabálya, `f3_val03.kar`).
  L3-spec: a 00 adapterei (HO-termék) és a 01 L3 (HO-routing) a saját körük F4-es kalibrációjával: `temp` kar, a
        temperature és a τ@95 a saját kör val-kiolvasásán (00: `eredmenyek/F4/vllm`, 01: `kor01/eredmenyek/F4/vllm`).
Rétegek (`retegek`): HO-termék; HO-routing = a 01 megerősítő tesztje (T-BFCL, T-BFCL-live, When2Call, a T-hu átnézett
  része, T-katalógus; a T-hu-maradék leíró); HO-új. Mindegyikből kimarad a célréteg-kalibrációs minta (`adat/f4/kalib.json`;
  a HO-routingon csak a megerősítő részébe eső tagjai kalibrálnak).
Bootstrap: hierarchikus, seed (visszatevéssel) × klaszter (`group_id`; a 00 val-on cikk, a 01 val-on klaszter).
  Replikánként a val-ok és a kalibrációs minták klaszteresen újramintázva, a τ minden karnál újraválasztva; a
  tesztréteg-minta a karok közt közös. Kétoldali p = 2 · min(P(Δ ≤ 0), P(Δ ≥ 0)).

  python3 kor03/eszkozok/f4_elemzes03.py                    → eredmenyek/F4/f4_elemzes03.json + eredmenylap_gepi.md
  python3 kor03/eszkozok/f4_elemzes03.py onteszt            (a karválasztás az F3-éval, a gyors τ és mérőszámok az
                                                             elemzes.py-éval egyeznek)
  python3 kor03/eszkozok/f4_elemzes03.py --proba --reps 200 --out <könyvtár>
      vakpróba: minden F4-kiolvasás helyett az L1★ F2-es eval-kiolvasása. A csővezetéket próbálja, eredményt nem ad.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]
EXP = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(EXP / "eszkozok"))
from elemzes import VAL_STRATA, arm_predictions, choose_tau, fit_temperature, label_bias, load_meta, metrics  # noqa: E402
from f4_elemzes import Arm, Resampler, holm_family, p_two_sided  # noqa: E402

F2R, F3R, F4R = ROOT / "eredmenyek/F2", ROOT / "eredmenyek/F3", ROOT / "eredmenyek/F4"
TARGET, BUKAS, NONINF_X, L0_KUSZOB, ALPHA = 0.95, 0.93, -0.02, 0.01, 0.05
G3 = ["k03v2_g3_s1", "k03v2_g3_s2", "k03v2_g3_s3"]
KEM, HU = "k03v2_g3kemeny_s1", "k03v2_g3hu_s1"
KAROK03 = ["L1", *G3, KEM, HU]  # a 03 val-on kalibrált karok
L3 = {"ho-termek": ["l3mixse_h2_s1", "l3mixse_h2_s2", "l3mixse_h2_s3"],
      "ho-routing": ["k01_l3mixse_p30_s1", "k01_l3mixse_p30_s2", "k01_l3mixse_p30_s3"]}
L3_VAL = {"ho-termek": (EXP / "eredmenyek/F4/vllm", "v00:"), "ho-routing": (EXP / "kor01/eredmenyek/F4/vllm", "v01:")}
H1_RETEGEK = ["ho-termek", "ho-routing", "ho-uj"]
H4_RETEGEK = ["ho-termek", "ho-uj", "ho-routing-hu"]
H6_RETEGEK = ["ho-routing", "ho-termek"]
ITELET_RANG = {"nem teljesíti a követelményeket": 0, "nem eldönthető": 1, "általánosít": 2, "segít": 2}


def rows(p: Path):
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


# --- itemek és rétegek ------------------------------------------------------------------------------------------

def load_meta03() -> dict[str, dict]:
    """A 03 val- és eval-itemjei; a HO-routingon a 01-es meta (T-hu átnézés, átcímkézés) `source_ref` szerint."""
    k01 = {}
    for f in ("kor01/adat/items_teszt.jsonl", "kor01/adat/f1s/items_katalogus.jsonl"):
        for it in rows(EXP / f):
            k01[it["id"]] = it["meta"]
    meta = {}
    for name in ("val", "eval"):
        for it in rows(ROOT / f"adat/f2/items_{name}.jsonl"):
            m = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None, "ketertelmu": bool(it.get("ketertelmu")),
                 "family": it["family"], "group": it["group"], "source": it.get("source"), "x_type": it.get("x_type"),
                 "lang": it.get("lang"), "klaszter": it["group_id"], "reteg00": (it.get("meta") or {}).get("reteg")}
            if it["split"] == "ho-routing":
                m01 = k01[it["source_ref"]]
                m["t_hu_atnezett"] = bool(m01.get("t_hu_atnezett"))
                a = m01.get("atnezes") or {}
                if a.get("muvelet") == "javit":
                    m["regi_gold"] = a.get("regi_gold")
            meta[it["id"]] = m
    return meta


def load_meta_l3val() -> dict[str, dict]:
    """Az L3-spec karok saját val-itemjei, előtaggal (00: `v00:`, klaszter = cikk; 01: `v01:`, klaszter)."""
    meta = {}
    for i, m in load_meta(EXP / "adat/f1").items():
        if m["split"] in VAL_STRATA:
            meta["v00:" + i] = {"split": "val00", "gold": m["gold"], "x": m["gold"] is None,
                                "ketertelmu": bool(m.get("ketertelmu")), "klaszter": m["article"]}
    for it in rows(EXP / "kor01/adat/items_val.jsonl"):
        m = it["meta"]
        meta["v01:" + it["id"]] = {"split": "val01", "gold": it["gold"], "x": it["gold"] is None,
                                   "ketertelmu": bool(m.get("ketertelmu")), "klaszter": m.get("klaszter", it["id"])}
    return meta


def retegek(meta: dict, kalib: dict) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """(tesztrétegek, kalibrációs minták). A tesztrétegekből minden kalibrációs item kimarad (a teljes kalib.json)."""
    kal_all = {i for v in kalib.values() for i in v}
    maradek = lambda i: meta[i]["source"] == "massive_hu" and not meta[i]["t_hu_atnezett"]  # noqa: E731
    by = defaultdict(list)
    for i, m in meta.items():
        by[m["split"]].append(i)
    L = {"ho-termek": [i for i in by["ho-termek"] if i not in kal_all],
         "ho-routing": [i for i in by["ho-routing"] if i not in kal_all and not maradek(i)],
         "ho-uj": [i for i in by["ho-uj"] if i not in kal_all]}
    L["ho-routing-hu"] = [i for i in L["ho-routing"] if meta[i]["lang"] == "hu"]
    # leíró rétegek
    L["t-hu-maradek"] = [i for i in by["ho-routing"] if i not in kal_all and maradek(i)]
    L["ho-routing-tervezet"] = [i for i in by["ho-routing"] if i not in kal_all]  # a v1-tervezet rétege (érzékenység)
    L["test-id"], L["ho-forras"], L["eval-kulso"] = by["test-id"], by["ho-forras"], by["eval-kulso"]
    K = {"ho-termek": sorted(kalib["ho-termek"]), "ho-uj": sorted(kalib["ho-uj"]),
         "ho-routing": sorted(i for i in kalib["ho-routing"] if not maradek(i))}
    return L, K


def layer_sizes(meta: dict, L: dict, K: dict) -> dict:
    out = {}
    for name, ids in [*L.items(), *((f"kalib:{k}", v) for k, v in K.items())]:
        sc = [i for i in ids if not meta[i]["ketertelmu"]]
        out[name] = {"n": len(ids), "pontozott": len(sc), "klaszter": len({meta[i]["klaszter"] for i in ids}),
                     "x_arany": round(sum(meta[i]["x"] for i in sc) / max(1, len(sc)), 4)}
    return out


# --- kiolvasások és kalibráció ----------------------------------------------------------------------------------

def readout(p: Path, ids: set[str], prefix: str = "") -> dict[str, list[dict]]:
    """id → sorok (csak a kalibrációhoz kellő mezők); a jelenlegi itemekre szűrve, `label_logprobs`-szal."""
    by = defaultdict(list)
    for r in rows(p):
        iid = prefix + r["id"]
        if iid not in ids:
            continue
        lp = r.get("label_logprobs") or {lab: math.log(max(1e-12, r["probs"][lab])) for lab in r["labels"]}
        by[iid].append({"id": iid, "perm": r["perm"], "order": r["order"], "labels": r["labels"], "label_logprobs": lp})
    return by


def check_complete(by: dict, ids: list[str], perms: set[int], name: str) -> None:
    """Védőkorlát (a teljes ellenőrzés az f4_teljesseg03.py-é): minden itemre pontosan az elvárt permutációk."""
    bad = [i for i in ids if sorted(r["perm"] for r in by.get(i, [])) != sorted(perms)]
    if bad:
        raise SystemExit(f"{name}: {len(bad)} item kiolvasása hiányos vagy ismétlődő (pl. {bad[:3]})")


def kind(name: str) -> str:
    return "batch" if name.startswith("batch") else name


def kalibral(by_val: dict, meta: dict, val_ids: list[str]) -> tuple[str, dict]:
    """A val-on a lef@95 szerint legjobb kalibrációs kar, holtversenyben lef@90, majd kisebb ECE (f3_val03.kar)."""
    val0 = [r for rs in by_val.values() for r in rs if r["perm"] == 0]
    temp, bias = fit_temperature(val0, meta), label_bias(val0)
    arms = {"nyers": {}, "temp": {"temp": temp}, "perm_avg": {"temp": temp}}
    arms |= {f"batch_{lam}": {"bias": bias, "lam": lam, "temp": temp} for lam in (0.5, 0.75, 1.0)}
    score = {}
    for name, prm in arms.items():
        pv = arm_predictions(kind(name), by_val, meta, prm)
        m95 = metrics(pv, meta, val_ids, choose_tau(pv, meta, val_ids, 0.95), BUKAS)
        m90 = metrics(pv, meta, val_ids, choose_tau(pv, meta, val_ids, 0.90), 0.88)
        score[name] = (m95.get("besorolasi_lefedettseg", 0), m90.get("besorolasi_lefedettseg", 0), -m95.get("ece", 1))
    best = max(score, key=lambda k: score[k])
    return best, arms[best]


# --- gyors τ és mérőszámok a bootstraphoz -----------------------------------------------------------------------

def kmin_table(nmax: int, target: float = TARGET) -> np.ndarray:
    """kmin[n] = a legkisebb k, amelyre a Clopper–Pearson egyoldali 95%-os alsó korlát ≥ target (különben n + 1).
    A korlát k-ban monoton nő, így cp(k, n) ≥ target ⇔ k ≥ kmin[n] (az elemzes.choose_tau feltétele)."""
    n = np.arange(nmax + 1)
    lo, hi = np.ones_like(n), n + 1  # a keresett k a [lo, hi] sávban; hi = n + 1: nincs ilyen k
    while (lo < hi).any():
        mid = (lo + hi) // 2
        act = lo < hi
        with np.errstate(invalid="ignore", divide="ignore"):
            ok = beta.ppf(0.05, mid, np.maximum(n - mid + 1, 1)) >= target
        ok &= mid <= n
        hi = np.where(act & ok, mid, hi)
        lo = np.where(act & ~ok, mid + 1, lo)
    return hi


def tau_gyors(a: Arm, idx: np.ndarray, scored: np.ndarray, kmin: np.ndarray) -> float:
    sel = idx[scored[idx] & a.assign[idx]]
    if len(sel) == 0:
        return math.inf
    o = sel[np.argsort(-a.conf[sel], kind="stable")]
    c = a.conf[o]
    k = np.cumsum(a.correct[o])
    boundary = np.append(c[1:] != c[:-1], True)  # holtversenyen belül nem vágunk
    ok = boundary & (k >= kmin[1:len(o) + 1])
    return float(c[np.nonzero(ok)[0][-1]]) if ok.any() else math.inf


def mer(a: Arm, s: np.ndarray, tau: float, aurc: bool = True) -> tuple[float, float, float, int]:
    """s: pontozott indexek → (lef@τ, precizitás, AURC, elfogadott itemek). Nulla elfogadott: a precizitás NaN."""
    n = len(s)
    acc = a.assign[s] & (a.conf[s] >= tau)
    k = int(acc.sum())
    prec = float(a.correct[s][acc].mean()) if k else math.nan
    au = math.nan
    if aurc:
        ad = s[a.assign[s]]
        o = ad[np.argsort(-a.conf[ad], kind="stable")]
        err = np.cumsum(~a.correct[o])
        au = float((err / np.arange(1, len(o) + 1)).sum() / n) if len(o) else 0.0
    return k / n, prec, au, k


def xfed(a: Arm, sx: np.ndarray) -> float:
    return float((~a.assign[sx]).mean()) if len(sx) else math.nan


def osszegez(x: list[float], delta: bool = True) -> dict:
    a = np.array(x, dtype=float)
    fin = a[~np.isnan(a)]
    out = {"median": float(np.median(fin)) if len(fin) else None, "atlag": float(np.mean(fin)) if len(fin) else None,
           "ci95": [float(np.percentile(fin, 2.5)), float(np.percentile(fin, 97.5))] if len(fin) else None,
           "reps": int(len(fin)), "nan_arany": round(1 - len(fin) / max(1, len(a)), 4)}
    if delta and len(fin):
        out["p_ketoldali"] = p_two_sided(fin)
    return out


def nanmean(xs) -> float:
    return math.nan if any(math.isnan(v) for v in xs) else float(np.mean(xs))


# --- a fő elemzés -----------------------------------------------------------------------------------------------

class Adat:
    """Minden kar predikciója tömbökben, a közös index szerint (03 val + eval, a 00/01 val előtaggal)."""

    def __init__(self, args):
        self.meta = {**load_meta03(), **load_meta_l3val()}
        self.kalib = {s: v["ids"] for s, v in json.loads((ROOT / "adat/f4/kalib.json").read_text())["retegek"].items()}
        self.L, self.K = retegek(self.meta, self.kalib)
        meta = self.meta
        self.val03 = sorted(i for i, m in meta.items() if m["split"] == "val")
        self.eval03 = sorted(i for i, m in meta.items() if m["split"] not in ("val", "val00", "val01"))
        self.valown = {g: sorted(i for i in meta if i.startswith(p)) for g, (_, p) in L3_VAL.items()}
        f4 = (lambda a: F2R / "qwen_eval.jsonl") if args.proba else (lambda a: F4R / a / "vllm_eval.jsonl")
        self.preds, self.cal = {}, {}
        sv, se = set(self.val03), set(self.eval03)
        # L1★ és L0′
        bv = readout(F2R / "qwen_val.jsonl", sv)
        check_complete(bv, self.val03, {0, 1, 2, 3}, "L1★ val")
        arm, prm = kalibral(bv, meta, self.val03)
        self.cal["L1"] = {"kar": arm, **{k: v for k, v in prm.items() if k != "bias"}}
        pv = arm_predictions(kind(arm), bv, meta, prm)
        for name, path in (("L1", F2R / "qwen_eval.jsonl"), ("L0r", f4("l0r"))):
            be = readout(path, se)
            check_complete(be, self.eval03, {0, 1, 2, 3}, name)
            self.preds[name] = {**pv, **arm_predictions(kind(arm), be, meta, prm)}
        self.cal["L0r"] = self.cal["L1"]
        # G3-család
        for a in (*G3, KEM, HU):
            bv = readout(F3R / a / "vllm_val.jsonl", sv)
            check_complete(bv, self.val03, {0, 1, 2, 3}, f"{a} val")
            arm, prm = kalibral(bv, meta, self.val03)
            self.cal[a] = {"kar": arm, **{k: v for k, v in prm.items() if k != "bias"}}
            be = readout(f4(a), se)
            check_complete(be, self.eval03, {0, 1, 2, 3}, a)
            self.preds[a] = {**arm_predictions(kind(arm), bv, meta, prm), **arm_predictions(kind(arm), be, meta, prm)}
        # L3-spec: saját val, `temp` kar
        for g, names in L3.items():
            d, pre = L3_VAL[g]
            layer = set(self.L[g]) | set(self.K[g]) | {i for i in self.eval03 if meta[i]["split"] == g}
            for k, a in enumerate(names, 1):
                bv = readout(d / f"l3_s{k}_val.jsonl", set(self.valown[g]), pre)
                perms = {r["perm"] for rs in bv.values() for r in rs}
                check_complete(bv, self.valown[g], perms, f"{a} val")
                temp = fit_temperature([r for rs in bv.values() for r in rs if r["perm"] == 0], meta)
                self.cal[a] = {"kar": "temp", "temp": temp, "val": str(d / f"l3_s{k}_val.jsonl")}
                be = readout(F2R / "qwen_eval.jsonl" if args.proba else F4R / a / "vllm_eval.jsonl", layer)
                check_complete(be, sorted(layer), {0, 1, 2, 3}, a)
                prm = {"temp": temp}
                self.preds[a] = {**arm_predictions("temp", bv, meta, prm), **arm_predictions("temp", be, meta, prm)}
        self.ids = self.val03 + self.eval03 + sorted(i for v in self.valown.values() for i in v)
        self.pos = {i: n for n, i in enumerate(self.ids)}
        self.A = {k: Arm(p, self.ids, meta) for k, p in self.preds.items()}
        self.scored = np.array([not meta[i]["ketertelmu"] for i in self.ids])
        self.xgold = np.array([meta[i]["x"] for i in self.ids])

    def idx(self, ids) -> np.ndarray:
        return np.array([self.pos[i] for i in ids], dtype=int)


def val_of(arm: str) -> str:
    for g, names in L3.items():
        if arm in names:
            return g
    return "val03"


def point_taus(D: Adat, kmin: np.ndarray) -> dict:
    full = {"val03": D.idx(D.val03), **{g: D.idx(v) for g, v in D.valown.items()}}
    return {a: tau_gyors(D.A[a], full[val_of(a)], D.scored, kmin) for a in D.A}


def point_block(D: Adat, taus: dict) -> dict:
    """Rétegenként és karonként a teljes mérőszámkészlet (elemzes.metrics) a val-τ-val; X-fedés X-típusonként."""
    meta = D.meta
    out = {}
    for lname, ids in D.L.items():
        blk = {}
        for a, p in D.preds.items():
            if a in L3["ho-termek"] + L3["ho-routing"] and not lname.startswith(val_of(a)):
                continue
            m = metrics(p, meta, ids, taus[a], BUKAS)
            xt = defaultdict(list)
            for i in ids:
                if meta[i]["x"] and not meta[i]["ketertelmu"]:
                    xt[meta[i]["x_type"]].append(i)
            m["x_fedes_tipusonkent"] = {t: {"n": len(v), "x_fedes": sum(p[i][0] is None for i in v) / len(v)}
                                        for t, v in sorted(xt.items())}
            m["elfogadott"] = sum(1 for i in ids if not meta[i]["ketertelmu"] and p[i][0] is not None and p[i][1] >= taus[a])
            blk[a] = m
        out[lname] = blk
    return out


def oracle_cov(D: Adat, a: str, ids: list[str], kmin: np.ndarray) -> float:
    s = D.idx(ids)
    t = tau_gyors(D.A[a], s, D.scored, kmin)
    return mer(D.A[a], s[D.scored[s]], t, aurc=False)[0]


def analyse(args) -> dict:
    D = Adat(args)
    meta = D.meta
    kmin = kmin_table(len(D.ids) + 1)
    taus = point_taus(D, kmin)
    potolt = set()
    if not args.proba:
        tj = json.loads((F4R / "teljesseg.json").read_text())["karok"]
        n_pot = sum(tj[f"F4:{a}"].get("potolt_sorok", 0) for a in G3)
        n_hib = sum(tj[f"F4:{a}"].get("hibanaplo_sorok", 0) for a in G3)
        if (F4R / "potolt_parok.jsonl").exists():
            potolt = {r["id"] for r in rows(F4R / "potolt_parok.jsonl") if r["kar"] in G3}
        if (n_pot or n_hib) and not potolt:
            raise SystemExit(f"a G3-karokon pótlás volt ({n_pot} sor, hibanapló {n_hib}), de a pótolt párok listája üres")
    # bootstrap-csoportok: val-ok, kalibrációs minták, tesztrétegek (+ érzékenységi részhalmazok)
    tests = {g: D.L[g] for g in ("ho-termek", "ho-routing", "ho-uj", "ho-routing-hu", "ho-routing-tervezet")}
    if potolt:
        tests["ho-routing:potolt"] = [i for i in D.L["ho-routing"] if i in potolt]
        tests["ho-routing:nem-potolt"] = [i for i in D.L["ho-routing"] if i not in potolt]
    groups = {"val03": D.val03, **{f"val:{g}": v for g, v in D.valown.items()}, **{f"kal:{g}": v for g, v in D.K.items()},
              **tests}
    assert len(groups) == 1 + len(D.valown) + len(D.K) + len(tests), "ütköző bootstrap-csoportnevek"
    RS = Resampler(D.ids, meta, groups, {g: "klaszter" for g in groups})
    A, sc, xg = D.A, D.scored, D.xgold

    def layer_eval(t: np.ndarray, tv: dict, l3: list[str]) -> dict:
        s = t[sc[t]]
        sx = s[xg[s]]
        r: dict = {a: mer(A[a], s, tv[a]) for a in ("L1", "L0r", *G3, KEM, HU, *l3)}
        r["_xf"] = {a: xfed(A[a], sx) for a in ("L1", *G3, KEM)}
        r["_s"] = s
        return r

    def record(acc: dict, key: str, r: dict, g3d: list[int], l3: list[str], l3d: list[int]) -> None:
        g3l = [r[a][0] for a in G3]
        g3a = [r[a][2] for a in G3]
        g3p = [r[a][1] for a in G3]
        lef_g = np.mean([g3l[k] for k in g3d])
        aurc_g = np.mean([g3a[k] for k in g3d])
        acc[f"H1:{key}:lef"].append(lef_g - r["L1"][0])
        acc[f"H1:{key}:aurc"].append(aurc_g - r["L1"][2])
        acc[f"L0:{key}:lef"].append(lef_g - r["L0r"][0])
        acc[f"L0:{key}:aurc"].append(aurc_g - r["L0r"][2])
        acc[f"H3a:{key}:G3"].append(nanmean([g3p[k] for k in g3d]))
        acc[f"H3a:{key}:L1"].append(r["L1"][1])
        for k, a in enumerate(G3):
            acc[f"H1s:{key}:{a}:lef"].append(g3l[k] - r["L1"][0])
            acc[f"H1s:{key}:{a}:aurc"].append(g3a[k] - r["L1"][2])
            acc[f"H3a:{key}:{a}"].append(g3p[k])
        if l3:
            l3l = np.mean([r[l3[k]][0] for k in l3d])
            gain = l3l - r["L1"][0]
            acc[f"H2:{key}:l3_nyereseg"].append(gain)
            acc[f"H2:{key}:D"].append((lef_g - r["L1"][0]) - 0.5 * gain)
            acc[f"H2:{key}:arany"].append((lef_g - r["L1"][0]) / gain if gain > 0 else math.nan)
        xf = r["_xf"]
        acc[f"H6a:{key}:G3"].append(np.mean([xf[G3[k]] for k in g3d]) - xf["L1"])
        acc[f"H6a:{key}:kemeny"].append(xf[KEM] - xf["L1"])
        acc[f"H6b:{key}:x_fedes"].append(xf[G3[0]] - xf[KEM])
        acc[f"H6b:{key}:aurc"].append(r[G3[0]][2] - r[KEM][2])

    rng = np.random.default_rng(args.seed)
    acc: dict[str, list] = defaultdict(list)
    for rep in range(args.reps):
        v = {"val03": RS.draw("val03", rng), **{g: RS.draw(f"val:{g}", rng) for g in D.valown}}
        tv = {a: tau_gyors(A[a], v[val_of(a)], sc, kmin) for a in A}
        g3d = list(rng.integers(0, 3, 3))
        l3d = {g: list(rng.integers(0, 3, 3)) for g in L3}
        for g in tests:
            base = g.split(":")[0]
            l3 = L3.get(g, [])
            r = layer_eval(RS.draw(g, rng), tv, l3)
            record(acc, g, r, g3d, l3, l3d.get(g, []))
            if g in H4_RETEGEK:
                acc[f"H4:{g}:lef"].append(r[G3[0]][0] - r[HU][0])
                acc[f"H4:{g}:aurc"].append(r[G3[0]][2] - r[HU][2])
            if g in H1_RETEGEK:  # H3(b): célréteg-τ a klaszteresen újramintázott kalibrációs mintán
                c = RS.draw(f"kal:{base}", rng)
                s = r["_s"]
                for a in ("L1", *G3):
                    t_c = tau_gyors(A[a], c, sc, kmin)
                    lef, prec, _, _ = mer(A[a], s, t_c, aurc=False)
                    acc[f"H3b:{g}:{a}:prec"].append(prec)
                    acc[f"H3b:{g}:{a}:lef"].append(lef)
                    acc[f"H3b:{g}:{a}:nincs_tau"].append(float(math.isinf(t_c)))
                acc[f"H3b:{g}:G3"].append(nanmean([acc[f"H3b:{g}:{G3[k]}:prec"][-1] for k in g3d]))
        if args.progress and (rep + 1) % args.progress == 0:
            print(f"  bootstrap {rep + 1}/{args.reps}", flush=True)
    boot = {k: osszegez(x, delta=not k.startswith(("H3a", "H3b"))) for k, x in acc.items()}

    # --- pontbecslések --------------------------------------------------------------------------------------
    pont = {}
    for g in tests:
        s = D.idx(tests[g])
        s = s[sc[s]]
        sx = s[xg[s]]
        arms = ("L1", "L0r", *G3, KEM, HU, *L3.get(g, []))
        m: dict = {a: dict(zip(("lef", "prec", "aurc", "elfogadott"), mer(A[a], s, taus[a]))) for a in arms}
        for a in ("L1", *G3, KEM, HU):
            m[a]["x_fedes"] = xfed(A[a], sx)
        g3 = {k: float(np.mean([m[a][k] for a in G3])) for k in ("lef", "aurc", "x_fedes")}
        g3["prec"] = nanmean([m[a]["prec"] for a in G3])
        pont[g] = {"n_pontozott": int(len(s)), "n_x": int(len(sx)), "karok": m, "G3_atlag": g3}
        if g in H1_RETEGEK:
            c = D.idx(D.K[g])
            pont[g]["H3b"] = {}
            for a in ("L1", *G3):
                t_c = tau_gyors(A[a], c, sc, kmin)
                lef, prec, _, k = mer(A[a], s, t_c, aurc=False)
                pont[g]["H3b"][a] = {"tau": t_c, "lef": lef, "prec": prec, "elfogadott": k}
            pont[g]["oracle_lef"] = {a: oracle_cov(D, a, tests[g], kmin) for a in ("L1", *G3)}

    res = {"verzio": "v1 (2026-10-14)", "proba": bool(args.proba), "reps": args.reps, "seed": args.seed,
           "kalibracio": D.cal, "tau_val": taus, "retegmeret": layer_sizes(meta, D.L, D.K),
           "potolt_itemek_ho_routing": len(tests.get("ho-routing:potolt", [])), "pont": pont, "bootstrap": boot}
    res |= dontesek(res, pont, boot)
    res["konzisztencia_pont_a_ci_n_kivul"] = konzisztencia(res)
    res["leiro"] = leiro(D, taus)
    res["leiro"]["pont_minden_reteg"] = point_block(D, taus)
    return res


# --- döntési szabályok (03-runbook 7., v1) -----------------------------------------------------------------------

def jo(ep: str, d: float) -> bool:
    return d > 0 if ep == "lef" else d < 0


def prec_atlag(precs: list[float]) -> tuple[float, bool]:
    """(az értelmezhető seedek precizitásának átlaga, van-e nulla elfogadott itemű seed)."""
    d = [p for p in precs if not math.isnan(p)]
    return (float(np.mean(d)) if d else math.nan), len(d) < len(precs)


def h1_itelet(holm: dict, layer: str, precs: list[float], seed_d: dict[str, list[float]], siker: str) -> tuple[str, list]:
    """„nem teljesíti”: a seedekre átlagolt precizitás < 0,93, vagy egy végpont Holm után szignifikánsan a vizsgált kar
    ellen; `siker`: egyik sem, és legalább egy végpont Holm után a javára szignifikáns, ahol minden seed pontbecslése a
    kedvező oldalon vagy nulla; egyébként „nem eldönthető”. A nulla elfogadott itemű seed precizitása nem értelmezhető:
    az átlag a többi seedé, és sikert nem enged."""
    ok, why = [], []
    against = [ep for ep in ("lef", "aurc") if holm[f"{layer}:{ep}"]["szignifikans"] and not holm[f"{layer}:{ep}"]["jo_irany"]]
    prec, nan_seed = prec_atlag(precs)
    if nan_seed:
        why.append("a precizitás egy seednél nem értelmezhető (nulla elfogadott item)")
    if not math.isnan(prec) and prec < BUKAS:
        return "nem teljesíti a követelményeket", [f"precizitás {prec:.4f} < {BUKAS}"] + [f"{ep}: szignifikáns a kar ellen" for ep in against]
    if against:
        return "nem teljesíti a követelményeket", [f"{ep}: szignifikáns a kar ellen" for ep in against]
    for ep in ("lef", "aurc"):
        h = holm[f"{layer}:{ep}"]
        if h["szignifikans"] and h["jo_irany"]:
            bad = [d for d in seed_d[ep] if (d < 0 if ep == "lef" else d > 0)]
            if bad:
                why.append(f"{ep}: szignifikáns, de egy seed pontbecslése a kedvezőtlen oldalon")
            else:
                ok.append(ep)
    if ok and not nan_seed:
        return siker, [f"siker végpont: {', '.join(ok)}"]
    return "nem eldönthető", why or ["egyik végpont sem szignifikáns a Holm-küszöbön"]


def dontesek(res: dict, pont: dict, boot: dict) -> dict:
    out = {}
    # H1 (és párhuzamosan az L0′-höz mérve)
    for fam, pre in (("H1", "H1"), ("H1_L0", "L0")):
        ps = {f"{g}:{ep}": (boot[f"{pre}:{g}:{ep}"]["p_ketoldali"], jo(ep, boot[f"{pre}:{g}:{ep}"]["median"]))
              for g in H1_RETEGEK for ep in ("lef", "aurc")}
        out[f"{fam}_holm"] = holm_family(ps, ALPHA)
    h1 = {}
    for g in H1_RETEGEK:
        P = pont[g]
        ref = P["karok"]["L1"]
        seed_d = {"lef": [P["karok"][a]["lef"] - ref["lef"] for a in G3], "aurc": [P["karok"][a]["aurc"] - ref["aurc"] for a in G3]}
        precs = [P["karok"][a]["prec"] for a in G3]
        it, why = h1_itelet(out["H1_holm"], g, precs, seed_d, "általánosít")
        d0 = P["karok"]["L0r"]["lef"] - ref["lef"]
        blk = {"itelet_L1": it, "indok_L1": why, "G3_precizitas_atlag": prec_atlag(precs)[0],
               "seedenkent": {a: {"lef": P["karok"][a]["lef"], "prec": P["karok"][a]["prec"], "aurc": P["karok"][a]["aurc"],
                                  "d_lef": P["karok"][a]["lef"] - ref["lef"], "d_aurc": P["karok"][a]["aurc"] - ref["aurc"],
                                  "ci_d_lef": res["bootstrap"][f"H1s:{g}:{a}:lef"]["ci95"],
                                  "ci_d_aurc": res["bootstrap"][f"H1s:{g}:{a}:aurc"]["ci95"]} for a in G3},
               "L0_minus_L1_lef": d0, "L0_szabaly": abs(d0) > L0_KUSZOB}
        itelet = it
        if blk["L0_szabaly"]:
            ref0 = P["karok"]["L0r"]
            sd0 = {"lef": [P["karok"][a]["lef"] - ref0["lef"] for a in G3], "aurc": [P["karok"][a]["aurc"] - ref0["aurc"] for a in G3]}
            it0, why0 = h1_itelet(out["H1_L0_holm"], g, precs, sd0, "általánosít")
            blk |= {"itelet_L0": it0, "indok_L0": why0}
            itelet = min(it, it0, key=lambda x: ITELET_RANG[x])
        blk["itelet"] = itelet
        h1[g] = blk
    out["H1"] = h1
    out["H1_osszegzes"] = {"altalanosit_retegek": [g for g in H1_RETEGEK if h1[g]["itelet"] == "általánosít"],
                           "megjegyzes": "Egyetlen sikeres réteg alapján nem állítható minden feladatcsaládra általánosítás."}
    # H2
    h2 = {}
    for g in L3:
        gain, D = boot[f"H2:{g}:l3_nyereseg"], boot[f"H2:{g}:D"]
        P = pont[g]
        l3p = float(np.mean([P["karok"][a]["lef"] for a in L3[g]]))
        g3p, l1p = P["G3_atlag"]["lef"], P["karok"]["L1"]["lef"]
        blk: dict = {"L3_minus_L1": {"pont": l3p - l1p, **gain}, "D": {"pont": (g3p - l1p) - 0.5 * (l3p - l1p), **D},
               "nyeresegarany_leiro": {"pont": (g3p - l1p) / (l3p - l1p) if l3p > l1p else None, **boot[f"H2:{g}:arany"]}}
        if gain["ci95"][0] <= 0:
            blk["itelet"] = "nem értelmezhető (az L3-spec referencianyeresége nem pozitív)"
        elif D["ci95"][0] > 0:
            blk["itelet"] = "érdemi átvitel"
        elif D["ci95"][1] < 0:
            blk["itelet"] = "nem éri el az előírt 50%-os átvitelt"
        else:
            blk["itelet"] = "nem eldönthető"
        h2[g] = blk
    out["H2"] = h2
    # H3
    h3 = {}
    for g in H1_RETEGEK:
        P = pont[g]
        blk = {}
        for path in ("a", "b"):
            if path == "a":
                seeds = {a: {"prec": P["karok"][a]["prec"], "lef": P["karok"][a]["lef"], "elfogadott": P["karok"][a]["elfogadott"],
                             "ci_prec": res["bootstrap"][f"H3a:{g}:{a}"]["ci95"]} for a in G3}
                l1 = {"prec": P["karok"]["L1"]["prec"], "lef": P["karok"]["L1"]["lef"], "elfogadott": P["karok"]["L1"]["elfogadott"],
                      "ci_prec": res["bootstrap"][f"H3a:{g}:L1"]["ci95"]}
                ci = res["bootstrap"][f"H3a:{g}:G3"]
            else:
                seeds = {a: {**P["H3b"][a], "ci_prec": res["bootstrap"][f"H3b:{g}:{a}:prec"]["ci95"],
                             "ci_lef": res["bootstrap"][f"H3b:{g}:{a}:lef"]["ci95"],
                             "nincs_tau_arany": res["bootstrap"][f"H3b:{g}:{a}:nincs_tau"]["atlag"]} for a in G3}
                l1 = {**P["H3b"]["L1"], "ci_prec": res["bootstrap"][f"H3b:{g}:L1:prec"]["ci95"]}
                ci = res["bootstrap"][f"H3b:{g}:G3"]
            if path == "b" and any(math.isinf(seeds[a]["tau"]) for a in G3):
                it = "nincs megfelelő τ a kalibrációs mintán: nem siker"
            elif any(seeds[a]["elfogadott"] == 0 for a in G3):
                it = "nulla elfogadott item: a precizitás nem értelmezhető, nem siker"
            else:
                pm = float(np.mean([seeds[a]["prec"] for a in G3]))
                it = ("az előírt toleranciaküszöböt teljesítette" if pm >= BUKAS else "az előírt toleranciaküszöböt nem teljesítette")
            blk[path] = {"itelet": it, "G3_precizitas_atlag": nanmean([seeds[a]["prec"] for a in G3]),
                         "G3_ci_hierarchikus": ci, "seedenkent": seeds, "L1_leiro": l1}
        blk["oracle_lef_veszteseg_leiro"] = {a: P["oracle_lef"][a] - P["karok"][a]["lef"] for a in ("L1", *G3)}
        h3[g] = blk
    out["H3"] = h3
    # H4 (egy seed; külön Holm-család)
    ps = {f"{g}:{ep}": (boot[f"H4:{g}:{ep}"]["p_ketoldali"], jo(ep, boot[f"H4:{g}:{ep}"]["median"]))
          for g in H4_RETEGEK for ep in ("lef", "aurc")}
    out["H4_holm"] = holm_family(ps, ALPHA)
    h4 = {}
    for g in H4_RETEGEK:
        P = pont[g]
        a, b = P["karok"][G3[0]], P["karok"][HU]
        sd = {"lef": [a["lef"] - b["lef"]], "aurc": [a["aurc"] - b["aurc"]]}
        it, why = h1_itelet(out["H4_holm"], g, [a["prec"]], sd, "segít")
        h4[g] = {"itelet": it, "indok": why, "G3_s1": a, "G3_hu_s1": b, "d_lef": boot[f"H4:{g}:lef"],
                 "d_aurc": boot[f"H4:{g}:aurc"]}
    out["H4"] = h4
    # H6 (feltáró)
    h6 = {}
    for g in H6_RETEGEK:
        blk = {}
        for k in ("G3", "kemeny"):
            b = boot[f"H6a:{g}:{k}"]
            blk[f"a_{k}"] = {**b, "megorzi_minus2pont": b["ci95"][0] > NONINF_X}
        blk["b_horgony_G3s1_minus_kemeny"] = {"x_fedes": boot[f"H6b:{g}:x_fedes"], "aurc": boot[f"H6b:{g}:aurc"]}
        h6[g] = blk
    out["H6"] = h6
    return out


def konzisztencia(res: dict) -> list[str]:
    """Azok a fő kontrasztok, amelyeknek a pontbecslése a bootstrap 95%-os intervallumán kívül esik (önellenőrzés)."""
    B, P, bad = res["bootstrap"], res["pont"], []
    chk = []
    for g in H1_RETEGEK:
        l1 = P[g]["karok"]["L1"]
        chk += [(f"H1:{g}:lef", P[g]["G3_atlag"]["lef"] - l1["lef"]), (f"H1:{g}:aurc", P[g]["G3_atlag"]["aurc"] - l1["aurc"])]
    for g in L3:
        chk += [(f"H2:{g}:l3_nyereseg", res["H2"][g]["L3_minus_L1"]["pont"]), (f"H2:{g}:D", res["H2"][g]["D"]["pont"])]
    for g in H4_RETEGEK:
        a, b = P[g]["karok"][G3[0]], P[g]["karok"][HU]
        chk += [(f"H4:{g}:lef", a["lef"] - b["lef"]), (f"H4:{g}:aurc", a["aurc"] - b["aurc"])]
    for k, v in chk:
        c = B[k]["ci95"]
        if c and not c[0] <= v <= c[1]:
            bad.append(f"{k}: pont {v:.4f}, CI [{c[0]:.4f}; {c[1]:.4f}]")
    return bad


def leiro(D: Adat, taus: dict) -> dict:
    """Leíró blokkok: H5 (teszt-ID családonként), H6(c) átcímkézett routing-itemek, L0′ példányzaj."""
    meta, P = D.meta, D.preds
    out = {}
    fam = defaultdict(list)
    for i in D.L["test-id"]:
        fam[meta[i]["family"]].append(i)
    out["H5_test_id"] = {f: {a: {k: metrics(P[a], meta, ids, taus[a], BUKAS).get(k) for k in
                                 ("n", "besorolasi_lefedettseg", "besorolasi_precizitas", "aurc", "pontossag", "x_fedes")}
                             for a in ("L1", *G3)} for f, ids in sorted(fam.items())}
    rel = [i for i in meta if meta[i].get("split") == "ho-routing" and "regi_gold" in meta[i]
           and i not in {j for v in D.kalib.values() for j in v}]
    out["H6c_atcimkezett"] = {"n": len(rel), "forras": dict(Counter(meta[i]["source"] for i in rel)),
                              "karok": {a: {"regi": sum(P[a][i][0] == meta[i]["regi_gold"] for i in rel),
                                            "regi_tau_folott": sum(P[a][i][0] == meta[i]["regi_gold"] and P[a][i][0] is not None
                                                                   and P[a][i][1] >= taus[a] for i in rel),
                                            "uj": sum(P[a][i][0] == meta[i]["gold"] for i in rel)}
                                        for a in ("L1", *G3, KEM, HU, *L3["ho-routing"])}}
    zaj = {}
    for g in ("ho-termek", "ho-routing", "ho-uj", "test-id"):
        s = [i for i in D.L[g] if not meta[i]["ketertelmu"]]
        zaj[g] = {"top1_billenes": sum(P["L1"][i][0] != P["L0r"][i][0] for i in s) / len(s),
                  "lef_L0r_minus_L1": metrics(P["L0r"], meta, s, taus["L1"])["besorolasi_lefedettseg"]
                  - metrics(P["L1"], meta, s, taus["L1"])["besorolasi_lefedettseg"]}
    out["L0_peldanyzaj"] = zaj
    return out


# --- eredménylap (gépi) -----------------------------------------------------------------------------------------

def fmt(x, d=3) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "–"
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def ci(c, d=3) -> str:
    return "–" if not c else f"[{fmt(c[0], d)}; {fmt(c[1], d)}]"


def eredmenylap(res: dict) -> str:
    o = ["# 03 F4 — gépi eredménylap (v1)", ""]
    if res["proba"]:
        o += ["> **PRÓBA: minden F4-kiolvasás helyett az L1★ F2-es eval-kiolvasása. Ez nem eredmény.**", ""]
    o += [f"Bootstrap: {res['reps']} ismétlés, seed {res['seed']}. Minden előre rögzített hipotézis szerepel, a negatív és a "
          "nem eldönthető eredmény is. Az értelmezés külön, kézzel írt szakaszba kerül.", "",
          "## H1 — G3 vs. L1★", "",
          "| réteg | ítélet | G3 prec. (átlag) | Δlef@95 [CI] | p | ΔAURC [CI] | p | L0′−L1★ lef |", "|---|---|---|---|---|---|---|---|"]
    for g, b in res["H1"].items():
        B = res["bootstrap"]
        o.append(f"| {g} | **{b['itelet']}** | {fmt(b['G3_precizitas_atlag'])} | {fmt(B[f'H1:{g}:lef']['median'])} "
                 f"{ci(B[f'H1:{g}:lef']['ci95'])} | {fmt(B[f'H1:{g}:lef']['p_ketoldali'], 4)} | {fmt(B[f'H1:{g}:aurc']['median'], 4)} "
                 f"{ci(B[f'H1:{g}:aurc']['ci95'], 4)} | {fmt(B[f'H1:{g}:aurc']['p_ketoldali'], 4)} | {fmt(b['L0_minus_L1_lef'])} |")
    o.append("")
    for g, b in res["H1"].items():
        if b["L0_szabaly"]:
            o.append(f"- {g}: |L0′ − L1★| > 1 pont → az L0′-höz mérve: **{b['itelet_L0']}** ({'; '.join(b['indok_L0'])}); "
                     f"az L1★-hoz: {b['itelet_L1']}; a gyengébb számít.")
        else:
            o.append(f"- {g}: {'; '.join(b['indok_L1'])}")
    o += ["", f"Általánosít: {', '.join(res['H1_osszegzes']['altalanosit_retegek']) or 'egyik rétegen sem'}. "
          + res["H1_osszegzes"]["megjegyzes"], "", "Seedenként (pontbecslés, val-τ):", "",
          "| réteg | seed | lef@95 | prec. | AURC | Δlef [CI] | ΔAURC [CI] |", "|---|---|---|---|---|---|---|"]
    for g, b in res["H1"].items():
        for a, s in b["seedenkent"].items():
            o.append(f"| {g} | {a} | {fmt(s['lef'])} | {fmt(s['prec'])} | {fmt(s['aurc'], 4)} | {fmt(s['d_lef'])} {ci(s['ci_d_lef'])} "
                     f"| {fmt(s['d_aurc'], 4)} {ci(s['ci_d_aurc'], 4)} |")
    o += ["", "## H2 — a specifikus LoRA-hoz mérve", "", "| réteg | ítélet | L3−L1★ [CI] | D [CI] | nyereségarány (leíró) [CI] |",
          "|---|---|---|---|---|"]
    for g, b in res["H2"].items():
        o.append(f"| {g} | **{b['itelet']}** | {fmt(b['L3_minus_L1']['pont'])} {ci(b['L3_minus_L1']['ci95'])} | "
                 f"{fmt(b['D']['pont'])} {ci(b['D']['ci95'])} | {fmt(b['nyeresegarany_leiro']['pont'], 2)} "
                 f"{ci(b['nyeresegarany_leiro']['ci95'], 2)} |")
    o += ["", "Rétegenkénti 95%-os intervallumok; vizsgálatszintű, többszörösségre korrigált állítás nem következik belőlük.", "",
          "## H3 — a kalibráció átvihetősége", "", "| réteg | út | ítélet | G3 prec. (átlag) [CI] | NaN-replikák | seedenként prec. / lef / elfogadott (nincs τ) |",
          "|---|---|---|---|---|---|"]
    for g, b in res["H3"].items():
        for path in ("a", "b"):
            x = b[path]
            sd = "; ".join(f"{fmt(s['prec'])} / {fmt(s['lef'])} / {s['elfogadott']}"
                           + (f" ({fmt(s['nincs_tau_arany'])})" if "nincs_tau_arany" in s else "") for s in x["seedenkent"].values())
            o.append(f"| {g} | ({path}) | **{x['itelet']}** | {fmt(x['G3_precizitas_atlag'])} {ci(x['G3_ci_hierarchikus']['ci95'])} | "
                     f"{fmt(x['G3_ci_hierarchikus']['nan_arany'])} | {sd} |")
    o += ["", "A ≥ 0,93-as pontbecslés az előírt toleranciaküszöb teljesítése, nem a 95%-os precizitás igazolása. Az intervallumok "
          "a val-on választott kiolvasási módra és temperature-re feltételesek.", "",
          "## H4 — angol gerinc (G3 s1 vs. G3-hu s1, egy seed)", "", "| réteg | ítélet | Δlef@95 [CI] | ΔAURC [CI] |", "|---|---|---|---|"]
    for g, b in res["H4"].items():
        o.append(f"| {g} | **{b['itelet']}** | {fmt(b['d_lef']['median'])} {ci(b['d_lef']['ci95'])} | "
                 f"{fmt(b['d_aurc']['median'], 4)} {ci(b['d_aurc']['ci95'], 4)} |")
    o += ["", "Az angol adattal bővített tanítás hatása ennél a seednél; a nyelv hatása nem választható el a nagyobb "
          "adatmennyiségtől és lépésszámtól.", "", "## H6 — horgony (feltáró)", "",
          "| réteg | ΔX-fedés G3−L1★ [CI] | CI alsó > −2 pont? | ΔX-fedés kemény−L1★ [CI] | CI alsó > −2 pont? | G3 s1−kemény s1: ΔX-fedés [CI] | ΔAURC [CI] |",
          "|---|---|---|---|---|---|---|"]
    for g, b in res["H6"].items():
        hb = b["b_horgony_G3s1_minus_kemeny"]
        o.append(f"| {g} | {fmt(b['a_G3']['median'])} {ci(b['a_G3']['ci95'])} | {'igen' if b['a_G3']['megorzi_minus2pont'] else 'nem'} | "
                 f"{fmt(b['a_kemeny']['median'])} {ci(b['a_kemeny']['ci95'])} | {'igen' if b['a_kemeny']['megorzi_minus2pont'] else 'nem'} | "
                 f"{fmt(hb['x_fedes']['median'])} {ci(hb['x_fedes']['ci95'])} | {fmt(hb['aurc']['median'], 4)} {ci(hb['aurc']['ci95'], 4)} |")
    o += ["", "A G3-nál igazolható és a G3-keménynél nem igazolható non-inferiority önmagában nem bizonyít horgonyhatást.", ""]
    pm = res["leiro"]["pont_minden_reteg"]
    o += ["**X-fedés X-típusonként (leíró, H1 és H6):**", "", "| réteg | X-típus | n | L1★ | G3 (3 seed átlaga) | G3-kemény |",
          "|---|---|---|---|---|---|"]
    for g in H1_RETEGEK:
        for t, v in pm[g]["L1"]["x_fedes_tipusonkent"].items():
            g3 = np.mean([pm[g][a]["x_fedes_tipusonkent"][t]["x_fedes"] for a in G3])
            o.append(f"| {g} | {t} | {v['n']} | {fmt(v['x_fedes'])} | {fmt(float(g3))} | "
                     f"{fmt(pm[g][KEM]['x_fedes_tipusonkent'][t]['x_fedes'])} |")
    o += ["", "## H5 — eloszláson belül (teszt-ID, leíró)", "", "| család | n | L1★ lef@95 / prec. | G3 lef@95 / prec. (3 seed átlaga) |",
          "|---|---|---|---|"]
    for f, v in res["leiro"]["H5_test_id"].items():
        l1 = v["L1"]
        gl = np.mean([v[a]["besorolasi_lefedettseg"] for a in G3])
        gp = [v[a]["besorolasi_precizitas"] for a in G3]
        gp = float(np.mean(gp)) if all(x is not None for x in gp) else None
        o.append(f"| {f} | {l1['n']} | {fmt(l1['besorolasi_lefedettseg'])} / {fmt(l1['besorolasi_precizitas'])} | "
                 f"{fmt(float(gl))} / {fmt(gp)} |")
    o.append("")
    c = res["leiro"]["H6c_atcimkezett"]
    o += [f"**H6(c), leíró:** {c['n']} átcímkézett routing-item ({c['forras']}); karonként régi címke (τ fölött) / új címke: "
          + "; ".join(f"{a} {v['regi']} ({v['regi_tau_folott']}) / {v['uj']}" for a, v in c["karok"].items()), "",
          "## Technikai és érzékenységi blokkok", ""]
    for g in ("ho-routing-tervezet", "ho-routing:potolt", "ho-routing:nem-potolt"):
        if f"H1:{g}:lef" in res["bootstrap"]:
            B = res["bootstrap"]
            o.append(f"- {g}: n = {res['pont'][g]['n_pontozott']}, G3 prec. {fmt(res['pont'][g]['G3_atlag']['prec'])}, Δlef@95 "
                     f"{fmt(B[f'H1:{g}:lef']['median'])} {ci(B[f'H1:{g}:lef']['ci95'])}, ΔAURC {fmt(B[f'H1:{g}:aurc']['median'], 4)} "
                     f"{ci(B[f'H1:{g}:aurc']['ci95'], 4)}")
    o.append("- L0′ példányzaj: " + "; ".join(f"{g}: billenés {fmt(v['top1_billenes'], 4)}, Δlef {fmt(v['lef_L0r_minus_L1'])}"
                                             for g, v in res["leiro"]["L0_peldanyzaj"].items()))
    o.append("- Az L0′ a bázis példányzaját méri; az adapteres kiolvasások példány-stabilitását önmagában nem igazolja.")
    return "\n".join(o) + "\n"


# --- egységpróba -------------------------------------------------------------------------------------------------

def selftest() -> None:
    meta = load_meta03()
    val = sorted(i for i, m in meta.items() if m["split"] == "val")
    ref = json.loads((F3R / "f3_val03.json").read_text())
    kmin = kmin_table(len(val) * 2)
    rng = np.random.default_rng(1)
    for name in ("L1★", *G3, KEM, HU):
        p = F2R / "qwen_val.jsonl" if name == "L1★" else F3R / name / "vllm_val.jsonl"
        by = readout(p, set(val))
        arm, prm = kalibral(by, meta, val)
        assert arm == ref[name]["kalibracio"], (name, arm, ref[name]["kalibracio"])
        assert abs(prm.get("temp", ref[name]["temp"]) - ref[name]["temp"]) < 1e-9, (name, prm)
        pv = arm_predictions(kind(arm), by, meta, prm)
        assert choose_tau(pv, meta, val, 0.95) == ref[name]["tau95"], name
        A = Arm(pv, val, meta)
        sc = np.array([not meta[i]["ketertelmu"] for i in val])
        groups = defaultdict(list)
        for n, i in enumerate(val):
            groups[meta[i]["klaszter"]].append(n)
        keys = list(groups)
        for trial in range(6):
            sub = np.arange(len(val)) if trial == 0 else np.concatenate([groups[keys[k]] for k in rng.integers(0, len(keys), len(keys))])
            sub_ids = [val[k] for k in sub]
            t_ref, t_fast = choose_tau(pv, meta, sub_ids, 0.95), tau_gyors(A, sub, sc, kmin)
            assert t_ref == t_fast, (name, trial, t_ref, t_fast)
            m = metrics(pv, meta, sub_ids, t_ref)
            lef, prec, au, _ = mer(A, sub[sc[sub]], t_fast)
            assert abs(m["besorolasi_lefedettseg"] - lef) < 1e-12 and abs(m["aurc"] - au) < 1e-12, (name, m, lef, au)
            assert (m["besorolasi_precizitas"] is None and math.isnan(prec)) or abs(m["besorolasi_precizitas"] - prec) < 1e-12
            s = sub[sc[sub]]
            assert abs(m["x_fedes"] - xfed(A, s[np.array([meta[val[k]]["x"] for k in s])])) < 1e-12
        print(f"ok: {name} ({arm}, T = {prm.get('temp', 1.0):.4f}, τ = {ref[name]['tau95']:.4f})")
    hf = holm_family({"a": (0.2, True), "b": (0.001, True)})
    assert hf["b"]["szignifikans"] and not hf["a"]["szignifikans"]
    holm = {"x:lef": {"szignifikans": True, "jo_irany": True}, "x:aurc": {"szignifikans": False, "jo_irany": False}}
    sd = {"lef": [0.01, 0.0, 0.02], "aurc": [0, 0, 0]}
    assert h1_itelet(holm, "x", [0.95] * 3, sd, "általánosít")[0] == "általánosít"
    assert h1_itelet(holm, "x", [0.95] * 3, {"lef": [0.01, -0.001, 0.02], "aurc": [0, 0, 0]}, "általánosít")[0] == "nem eldönthető"
    assert h1_itelet(holm, "x", [0.95, 0.92, 0.91], sd, "általánosít")[0].startswith("nem telj")
    assert h1_itelet(holm, "x", [math.nan, 0.95, 0.95], sd, "általánosít")[0] == "nem eldönthető"
    assert h1_itelet(holm, "x", [math.nan, 0.80, 0.85], sd, "általánosít")[0].startswith("nem telj")
    holm["x:aurc"] = {"szignifikans": True, "jo_irany": False}
    assert h1_itelet(holm, "x", [0.95] * 3, sd, "általánosít")[0].startswith("nem telj")
    print("ok: holm, döntési szabály")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "onteszt":
        selftest()
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--proba", action="store_true", help="vakpróba: az F4-kiolvasások helyett az L1★ eval-kiolvasása")
    ap.add_argument("--progress", type=int, default=500)
    ap.add_argument("--out", default=str(F4R))
    a = ap.parse_args()
    if a.proba and Path(a.out).resolve() == F4R.resolve():
        raise SystemExit("--proba mellett az --out nem lehet a valódi eredménykönyvtár")
    if not a.proba and not (F4R / "teljesseg.json").exists():
        raise SystemExit("hiányzik a technikai lezárás (f4_teljesseg03.py → teljesseg.json)")
    if not a.proba and not json.loads((F4R / "teljesseg.json").read_text())["rendben"]:
        raise SystemExit("a technikai lezárás nem rendben (teljesseg.json): az elemzés nem fut")
    res = analyse(a)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "f4_elemzes03.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out / "eredmenylap_gepi.md").write_text(eredmenylap(res), encoding="utf-8")
    print("pont a CI-n kívül:", res["konzisztencia_pont_a_ci_n_kivul"] or "nincs")
    print(json.dumps({"H1": {g: b["itelet"] for g, b in res["H1"].items()}, "H2": {g: b["itelet"] for g, b in res["H2"].items()},
                      "H3": {g: {p: b[p]["itelet"] for p in ("a", "b")} for g, b in res["H3"].items()},
                      "H4": {g: b["itelet"] for g, b in res["H4"].items()}}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
