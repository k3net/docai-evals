"""05-ös kör — a 05a elemzése (05-runbook 8.1–8.2): pontbecslés, hierarchikus bootstrap, páros kontrasztok, szűrőítélet.

Karonként (a fejeknél seedenként) a `kalib05` döntési táblája: a javaslat (SELECT / NONE / DEFER), a kalibrált
megbízhatóság (q) és a helyesség (szigorú; az enyhe leíró). A temperature és a Platt a D_cal_prob pontbecsléséből
rögzített; a τ a D_cal_policy-n (alapesetenként egy item), a bootstrapban replikánként újraválasztva.

Mérőszámok egy rétegen, a τ-nál (a kétértelmű itemek nélkül):
  sel_lef, sel_prec   SELECT-lefedettség és -precizitás (a v1a D1 óta leíró; az elsődleges a ΔAURC S+N)
  sn_lef, sn_prec     SELECT + NONE lefedettség és precizitás
  hamis_sel_nm        SELECT / gold NO_MATCH;  hamis_sel_egyeb: SELECT / gold MISSING_DATA + OUT_OF_SCOPE
  hamis_none          NONE / gold MATCH
  mtx                 elfogadott SELECT / minden nem-MATCH item (a 04 2. pontja)
  aurc_sn, aurc_sel   a risk–coverage görbe alatti terület minden itemen; a nem döntött (DEFER) itemek a rangsor végén
                      hibaként (v1a: a tartózkodás nem javítja a területet). aurc_sn_03: a 03 konvenciója (a DEFER
                      kimarad, a nevező n), leíró; defer_arany: a DEFER hányada
  lef_p95_sel/_sn     a lefedettség, ha a τ-t ugyanazzal a szabállyal magán a rétegen illesztjük (felső korlát)
T-karok (B1-T, K*-T-kal, K*-T-meta): a τ (és a Platt) a réteg célcsalád-mintáján (kalib05.CEL), a bootstrapban az is
újramintázva.
Bootstrap: replikánként a réteg és a D_cal_policy klaszteresen (család → alapeset) újramintázva, a fejeknél a seed
visszatevéssel karonként; a τ minden karnál újra. Páros Δ ugyanazon a rétegmintán; kétoldali p = 2 · min(P(Δ ≤ 0),
P(Δ ≥ 0)).

  python3 kor05/eszkozok/elemzes05.py --reteg D_dev --kar B0 --kar C --kar H --kar A \\
      --kontraszt H-B0 --kontraszt H-C --kontraszt A-H --reps 2000 --out kor05/eredmenyek/F3/proba_ddev
"""

from __future__ import annotations

import argparse
import warnings
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "eszkozok")]
import kalib05 as K  # noqa: E402

STATE_CODE = {"MATCH": 0, "NO_MATCH": 1, "MISSING_DATA": 2, "OUT_OF_SCOPE": 3}
METRICS = ("sel_lef", "sel_prec", "sn_lef", "sn_prec", "hamis_sel_nm", "hamis_sel_egyeb", "hamis_none", "mtx",
           "aurc_sn", "aurc_sel", "aurc_sn_03", "defer_arany")
SZURO_RETEGEK = ("teszt:ho-termek", "teszt:ho-routing", "teszt:ho-uj")
BUKAS = 0.93
warnings.filterwarnings("ignore", message="Mean of empty slice")


def kmin_table(nmax: int, target: float = K.TARGET) -> np.ndarray:
    """kmin[n] = a legkisebb k, amelyre a CP egyoldali 95%-os alsó korlátja ≥ target (különben n + 1); a
    f4_elemzes03.kmin_table módszere."""
    n = np.arange(nmax + 1)
    lo, hi = np.ones_like(n), n + 1
    while (lo < hi).any():
        mid = (lo + hi) // 2
        act = lo < hi
        with np.errstate(invalid="ignore", divide="ignore"):
            ok = beta.ppf(0.05, mid, np.maximum(n - mid + 1, 1)) >= target
        ok &= mid <= n
        hi = np.where(act & ok, mid, hi)
        lo = np.where(act & ~ok, mid + 1, lo)
    return hi


class Tab:
    """Egy kar (egy seed) döntései egy szelet közös itemsorrendjén; a hiányzó item DEFER."""

    def __init__(self, rows: list[dict], ids: list[str], key: str = "helyes"):
        by = {r["id"]: r for r in rows}
        n = len(ids)
        self.q = np.full(n, -np.inf)
        self.sel = np.zeros(n, bool)
        self.none = np.zeros(n, bool)
        self.cor = np.zeros(n, bool)
        for i, iid in enumerate(ids):
            r = by.get(iid)
            if r is None or r["javaslat"] == "DEFER":
                continue
            self.q[i] = r["q"]
            self.sel[i] = r["javaslat"] == "SELECT"
            self.none[i] = r["javaslat"] == "NONE"
            self.cor[i] = bool(r[key])
        self.acc_ok = self.sel | self.none


class Slice:
    """Egy szelet itemjei (kétértelmű nélkül), az állapotkódok és a klaszterszerkezet (család → alapeset)."""

    def __init__(self, name: str, one_per_group: bool = False):
        M = K.meta()
        sz = json.loads((EXP / "kor05/adat/szeletek05.json").read_text())["szeletek"][name]["ids"]
        ids = [i for i in sz if not M[i]["ketertelmu"]]
        if one_per_group:
            best = {}
            for i in ids:
                h = hashlib.sha256(f"{K.TAU_SEED}|{i}".encode()).hexdigest()
                g = M[i]["group_id"]
                if g not in best or h < best[g][0]:
                    best[g] = (h, i)
            ids = sorted(i for _, i in best.values())
        self.name, self.ids = name, ids
        self.state = np.array([STATE_CODE[M[i]["state"]] for i in ids])
        fam = defaultdict(lambda: defaultdict(list))
        for n, i in enumerate(ids):
            fam[M[i]["family"]][M[i]["group_id"]].append(n)
        self.fams = [[np.array(v) for v in g.values()] for g in fam.values()]
        self.family = [M[i]["family"] for i in ids]

    def draw(self, rng: np.random.Generator) -> np.ndarray:
        out = []
        for f in rng.integers(0, len(self.fams), len(self.fams)):
            gs = self.fams[f]
            out += [gs[g] for g in rng.integers(0, len(gs), len(gs))]
        return np.concatenate(out)

    def full(self) -> np.ndarray:
        return np.arange(len(self.ids))


_KMIN = {"t": kmin_table(1024)}


def kmin_for(n: int) -> np.ndarray:
    if n >= len(_KMIN["t"]):
        _KMIN["t"] = kmin_table(2 * n)
    return _KMIN["t"]


def tau_of(t: Tab, idx: np.ndarray, kmin: np.ndarray | None = None) -> float:
    s = idx[t.acc_ok[idx]]
    if len(s) < K.MIN_ACC:
        return math.inf
    kmin = kmin_for(len(s))
    o = s[np.argsort(-t.q[s], kind="stable")]
    c = t.q[o]
    k = np.cumsum(t.cor[o])
    n = np.arange(1, len(o) + 1)
    boundary = np.append(c[1:] != c[:-1], True)
    ok = boundary & (n >= K.MIN_ACC) & (k >= kmin[n])
    return float(c[np.nonzero(ok)[0][-1]]) if ok.any() else math.inf


def aurc(t: Tab, s: np.ndarray, mask: np.ndarray, defer_hiba: bool = True) -> float:
    """A risk–coverage görbe alatti terület a szelet minden itemjén (n). A döntések (mask) q szerint csökkenő sorban;
    a nem döntött (DEFER, illetve a SELECT-AURC-nál a nem-SELECT) itemek a rangsor végén, hibaként, hogy a tartózkodás
    ne javítsa a területet (v1a). `defer_hiba=False`: a 03 `mer()` konvenciója, a nem döntött itemek kimaradnak, a
    nevező marad n (leíró)."""
    a = s[mask[s]]
    o = a[np.argsort(-t.q[a], kind="stable")]
    cor = t.cor[o]
    if defer_hiba:
        cor = np.concatenate([cor, np.zeros(len(s) - len(a), bool)])
    if len(cor) == 0:
        return 0.0
    err = np.cumsum(~cor)
    return float((err / np.arange(1, len(cor) + 1)).sum() / len(s))


def measure(t: Tab, st: np.ndarray, s: np.ndarray, tau: float) -> dict:
    n = len(s)
    acc = t.acc_ok[s] & (t.q[s] >= tau)
    sel, none, cor, state = acc & t.sel[s], acc & t.none[s], t.cor[s], st[s]
    nm, eg, ma, nx = state == 1, (state == 2) | (state == 3), state == 0, state != 0

    def rate(a, b):
        return float(a.sum() / b.sum()) if b.sum() else math.nan
    return {"sel_lef": float(sel.sum() / n), "sel_prec": float(cor[sel].mean()) if sel.any() else math.nan,
            "sn_lef": float(acc.sum() / n), "sn_prec": float(cor[acc].mean()) if acc.any() else math.nan,
            "hamis_sel_nm": rate(sel & nm, nm), "hamis_sel_egyeb": rate(sel & eg, eg), "hamis_none": rate(none & ma, ma),
            "mtx": rate(sel & nx, nx), "aurc_sn": aurc(t, s, t.acc_ok), "aurc_sel": aurc(t, s, t.sel),
            "aurc_sn_03": aurc(t, s, t.acc_ok, defer_hiba=False), "defer_arany": float((~t.acc_ok[s]).mean())}


def lef_p95(t: Tab, s: np.ndarray, kmin: np.ndarray) -> dict:
    tau = tau_of(t, s, kmin)
    m = measure(t, np.zeros(len(t.q), int), s, tau)
    return {"lef_p95_sel": m["sel_lef"], "lef_p95_sn": m["sn_lef"], "tau_reteg": None if math.isinf(tau) else tau}


# --- karok -------------------------------------------------------------------------------------------------------------

def arm_tables(arm: str, kal: dict, szelet: str, ids: list[str], key: str) -> list[Tab]:
    if arm in K.LABEL_SEEDS:
        return [Tab(K.label_table(arm, szelet, kal[arm][str(n)]["temperature"], seed=n), ids, key) for n in K.LABEL_SEEDS[arm]]
    if arm in K.LABEL_ARMS:
        return [Tab(K.label_table(arm, szelet, kal[arm]["temperature"]), ids, key)]
    out = []
    for s in K.SEEDS:
        p = kal[arm][str(s)]["platt"]
        out.append(Tab(K.head_table(arm, szelet, s, (p["a"], p["b"])), ids, key))
    return out


def p_two(x: np.ndarray) -> float:
    x = x[~np.isnan(x)]
    if not len(x):
        return math.nan
    return float(min(1.0, 2 * min((x <= 0).mean(), (x >= 0).mean())))


def summ(x: list[float]) -> dict:
    a = np.array(x, float)
    f = a[~np.isnan(a)]
    if not len(f):
        return {"reps": 0}
    return {"median": float(np.median(f)), "ci95": [float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))],
            "p": p_two(f), "reps": int(len(f)), "nan_arany": round(1 - len(f) / len(a), 4)}


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted((p, k) for k, p in ps.items() if not math.isnan(p))
    out, run = {}, 0.0
    for r, (p, k) in enumerate(items):
        run = max(run, min(1.0, (len(items) - r) * p))
        out[k] = run
    return out


def pair(c: str) -> tuple[str, str]:
    x, y = c.split("~") if "~" in c else c.split("-", 1)
    return x, y


def analyse(a) -> dict:
    kal = json.loads(Path(a.kalib).read_text())
    key = "helyes_enyhe" if a.enyhe else "helyes"
    cel_map = dict(K.CEL) | dict(x.split("=", 1) for x in a.cel)
    pol = Slice("D_cal_policy", one_per_group=True)
    layers = [Slice(n) for n in a.reteg]
    arms = sorted(set(a.kar))
    tau_slices = {"D_cal_policy": pol}
    T_pol = {arm: arm_tables(arm, kal, "D_cal_policy", pol.ids, key) for arm in arms if arm not in K.T_ARMS}
    TT, TS, SRC, t_params = {}, {}, {}, {}
    for L in layers:
        TT[L.name], TS[L.name], SRC[L.name] = {}, {}, {}
        for arm in arms:
            if arm in K.T_ARMS:
                cel = cel_map[L.name]
                cs = tau_slices.setdefault(cel, Slice(cel, one_per_group=True))
                taus, tests, prm = K.t_tables(arm, L.name, kal, cel)
                TT[L.name][arm] = [Tab(t, cs.ids, key) for t in taus]
                TS[L.name][arm] = [Tab(t, L.ids, key) for t in tests]
                SRC[L.name][arm] = cel
                t_params[f"{arm}|{L.name}"] = prm
            else:
                TT[L.name][arm] = T_pol[arm]
                TS[L.name][arm] = arm_tables(arm, kal, L.name, L.ids, key)
                SRC[L.name][arm] = "D_cal_policy"
    res = {"helyesseg": key, "retegek": {L.name: len(L.ids) for L in layers},
           "tau_szeletek": {n: len(sl.ids) for n, sl in tau_slices.items()}, "t_parameterek": t_params,
           "pont": {}, "bootstrap": {}}
    # pontbecslés
    for L in layers:
        s = L.full()
        blk = {}
        for arm in arms:
            per = []
            for tp, tl in zip(TT[L.name][arm], TS[L.name][arm]):
                tau = tau_of(tp, tau_slices[SRC[L.name][arm]].full())
                m = measure(tl, L.state, s, tau) | lef_p95(tl, s, None)
                m["tau"] = None if math.isinf(tau) else tau
                per.append(m)
            blk[arm] = {"tau_szelet": SRC[L.name][arm], "seedenkent" if len(per) > 1 else "egy": per,
                        "munkapont_seedenkent": [p["tau"] is not None for p in per],
                        "atlag": {k: float(np.nanmean([p[k] if p[k] is not None else np.nan for p in per]))
                                  for k in per[0] if k != "tau_reteg"}}
        # családonként (leíró, a seedek átlaga, a pont-τ-nál)
        fam = defaultdict(dict)
        for arm in arms:
            for f in sorted(set(L.family)):
                idx = np.array([n for n, x in enumerate(L.family) if x == f])
                vals = [measure(tl, L.state, idx, tau_of(tp, tau_slices[SRC[L.name][arm]].full()))
                        for tp, tl in zip(TT[L.name][arm], TS[L.name][arm])]
                fam[f][arm] = {k: float(np.nanmean([v[k] for v in vals]))
                               for k in ("sel_lef", "sel_prec", "sn_lef", "sn_prec", "aurc_sn")}
                fam[f]["n"] = int(len(idx))
        res["pont"][L.name] = {"karok": blk, "csaladonkent": fam}
    # bootstrap: replikánként minden τ-szelet és minden réteg klaszteresen újramintázva, a seed karonként visszatevéssel
    rng = np.random.default_rng(a.seed)
    acc = {L.name: defaultdict(list) for L in layers}
    n_seed = {arm: len(TS[layers[0].name][arm]) for arm in arms}
    for rep in range(a.reps):
        draws = {n: sl.draw(rng) for n, sl in tau_slices.items()}
        pick = {arm: int(rng.integers(0, n_seed[arm])) for arm in arms}
        cache = {}
        for L in layers:
            tau = {}
            for arm in arms:
                ck = (arm, SRC[L.name][arm], id(TT[L.name][arm][pick[arm]]))
                if ck not in cache:
                    cache[ck] = tau_of(TT[L.name][arm][pick[arm]], draws[SRC[L.name][arm]])
                tau[arm] = cache[ck]
            s = L.draw(rng)
            m = {arm: measure(TS[L.name][arm][pick[arm]], L.state, s, tau[arm]) for arm in arms}
            for arm in arms:
                for k in METRICS:
                    acc[L.name][f"{arm}|{k}"].append(m[arm][k])
            for c in a.kontraszt:
                x, y = pair(c)
                for k in METRICS:
                    acc[L.name][f"{c}|{k}"].append(m[x][k] - m[y][k])
        if (rep + 1) % 1000 == 0:
            print(f"  bootstrap {rep + 1}/{a.reps}", flush=True)
    for L in layers:
        res["bootstrap"][L.name] = {k: summ(v) for k, v in acc[L.name].items()}
    # kontrasztok — a v1a D1 (b) szabálya rétegenként: a ΔAURC (S+N) negatív, a CI-je nem tartalmazza a 0-t; az X kar
    # precizitásának (S+N) pontbecslése a saját τ-jánál ≥ 0,93, ha van munkapontja; az MTX nem szignifikánsan nagyobb.
    # A Δ SELECT-lef@95 és a lef@p95 leíró. Ítélet a három szűrőrétegen: legalább kettőn teljesül → továbblép.
    res["kontrasztok"] = {}
    for c in a.kontraszt:
        x = pair(c)[0]
        per = {}
        for L in layers:
            b = res["bootstrap"][L.name]
            au = b[f"{c}|aurc_sn"]
            px = res["pont"][L.name]["karok"][x]
            prec = px["atlag"]["sn_prec"]
            van = any(px["munkapont_seedenkent"])
            ok = {"delta_aurc_negativ": bool(au.get("reps") and au["ci95"][1] < 0),
                  "precizitas_legalabb_093": bool((not van) or (not math.isnan(prec) and prec >= BUKAS)),
                  "mtx_nem_nagyobb": not (b[f"{c}|mtx"].get("reps") and b[f"{c}|mtx"]["ci95"][0] > 0)}
            per[L.name] = ok | {"teljesul": all(ok.values()), "munkapont": van,
                                "leiro_delta_sel_lef": b[f"{c}|sel_lef"]}
        szuro = [n for n in SZURO_RETEGEK if n in per]
        holm_p = holm({n: res["bootstrap"][n][f"{c}|aurc_sn"].get("p", math.nan) for n in (szuro or per)})
        res["kontrasztok"][c] = {"retegenkent": per, "holm_p_aurc_sn": holm_p,
                                 "itelet": (("továbblép" if sum(per[n]["teljesul"] for n in szuro) >= 2 else "nem lép tovább")
                                            if len(szuro) == 3 else "nem szűrőrétegek (próba)")}
    # H6 (05-runbook 8.3; 04 5.1): Holm a 2 × 3 összevetésre (JEV-a − L1★ és JEV-a − G3 a három szűrőrétegen)
    h6 = [c for c in ("JEV-a~L1v", "JEV-a~G3") if c in res["kontrasztok"]]
    if len(h6) == 2:
        res["h6_holm_aurc_sn"] = holm({f"{c}|{n}": res["bootstrap"][n][f"{c}|aurc_sn"].get("p", math.nan)
                                       for c in h6 for n in SZURO_RETEGEK if n in res["bootstrap"]})
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reteg", action="append", required=True)
    ap.add_argument("--kar", action="append", required=True)
    ap.add_argument("--kontraszt", action="append", default=[], help="X-Y vagy X~Y: X − Y (kötőjeles karnévnél, pl. JEV-a~B1, a ~ kötelező)")
    ap.add_argument("--kalib", default="kor05/eredmenyek/F3/kalib/kalib.json")
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--enyhe", action="store_true", help="az enyhe helyességgel (leíró változat)")
    ap.add_argument("--cel", action="append", default=[],
                    help="RÉTEG=CÉLMINTA: a T-karok τ-szelete a próbán (alap: kalib05.CEL)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = analyse(a)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "elemzes05.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for L, blk in res["pont"].items():
        print(f"== {L} (n={res['retegek'][L]})")
        for arm, v in blk["karok"].items():
            m = v["atlag"]
            print(f"  {arm:6s} sel_lef={m['sel_lef']:.3f} sel_prec={m['sel_prec']:.3f} sn_lef={m['sn_lef']:.3f} "
                  f"sn_prec={m['sn_prec']:.3f} mtx={m['mtx']:.3f} aurc_sn={m['aurc_sn']:.4f} "
                  f"(03-konv. {m['aurc_sn_03']:.4f}, DEFER {m['defer_arany']:.3f}) lef_p95_sel={m['lef_p95_sel']:.3f}")
    for c, v in res["kontrasztok"].items():
        for L, ok in v["retegenkent"].items():
            b = res["bootstrap"][L][f"{c}|aurc_sn"]
            bad = [k for k in ("delta_aurc_negativ", "precizitas_legalabb_093", "mtx_nem_nagyobb") if not ok[k]]
            print(f"  {c} @ {L}: ΔAURC(S+N) median={b.get('median', math.nan):+.4f} CI={b.get('ci95')} p={b.get('p')} "
                  f"→ {'teljesül' if ok['teljesul'] else 'nem teljesül'}{' (' + ', '.join(bad) + ')' if bad else ''}")
        print(f"  {c}: {v['itelet']}")


if __name__ == "__main__":
    main()
