"""05-ös kör — a JEV munkaponti mérlege, alapesetszintű függőséggel (utólagos, leíró; Napló, 2026-10-29).

Item- és alapesetszinten, a v1a pont-τ-jánál (D_cal_policy):
  item         elfogadott, hiba, precizitás, lefedettség; a CI két módon: Clopper–Pearson az itemeken (a függőséget
               figyelmen kívül hagyja) és klaszteres bootstrap az alapeseteken, rögzített τ-val
  alapeset     legalább egy itemje elfogadva; minden itemje elfogadva; minden itemje elfogadva és helyes (teljesen
               átvett, hibátlan munka); legalább egy elfogadott hiba
A τ-újraválasztással: a D_cal_policy és a réteg együtt újramintázva (mint a v1a-ban); a replikák hányadában nincs
munkapont, és a mérőszámok CI-je ezzel együtt.

  python3 kor05/eszkozok/jev_merleg05.py --reps 10000 --out kor05/eredmenyek/F3/v1a_diag
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "eszkozok")]
import diag05 as D  # noqa: E402
import elemzes05 as E  # noqa: E402
import kalib05 as K  # noqa: E402

RETEGEK = ("teszt:ho-termek", "teszt:ho-uj", "teszt:ho-routing", "teszt:ho-routing-hu")
KAROK = ("JEV-a", "JEV-b")


def csoport(t: E.Tab, tau: float, gid: np.ndarray, G: int) -> dict[str, np.ndarray]:
    """Alapesetenkénti darabszámok egy τ-nál: item, elfogadott, elfogadott hibás, helyes."""
    acc = t.acc_ok & (t.q >= tau)
    return {"n": np.bincount(gid, minlength=G), "acc": np.bincount(gid, weights=acc, minlength=G),
            "err": np.bincount(gid, weights=acc & ~t.cor, minlength=G), "cor": np.bincount(gid, weights=t.cor, minlength=G)}


def merok(c: dict[str, np.ndarray], g: np.ndarray) -> dict:
    """A mérőszámok a kiválasztott alapeseteken (g: alapesetindexek, ismétléssel)."""
    n, acc, err, cor = c["n"][g], c["acc"][g], c["err"][g], c["cor"][g]
    n_acc, n_err = float(acc.sum()), float(err.sum())
    teljes = acc == n
    return {"elfogadott": int(n_acc), "hiba": int(n_err), "precizitas": (n_acc - n_err) / n_acc if n_acc else math.nan,
            "lefedettseg": n_acc / n.sum(), "alapeset_legalabb_egy": float((acc > 0).mean()),
            "alapeset_mind": float(teljes.mean()), "alapeset_mind_helyes": float((teljes & (cor == n)).mean()),
            "alapeset_hibaval": float((err > 0).mean())}


def ci(v: list[float]) -> list[float] | None:
    a = np.array(v, float)
    a = a[~np.isnan(a)]
    return [float(np.percentile(a, 2.5)), float(np.percentile(a, 97.5))] if len(a) else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261029)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    kal = json.loads(D.KALIB.read_text())
    M = K.meta()
    pol = E.Slice("D_cal_policy", one_per_group=True)
    res = {"reps": a.reps, "retegek": {}}
    for layer in RETEGEK:
        L = E.Slice(layer)
        gmap: dict[str, int] = {}
        gid = np.array([gmap.setdefault(M[i]["group_id"], len(gmap)) for i in L.ids])
        G = len(gmap)
        blk = {"item": len(L.ids), "alapeset": G, "karok": {}}
        for arm in KAROK:
            t = E.arm_tables(arm, kal, layer, L.ids, "helyes")[0]
            tp = E.arm_tables(arm, kal, "D_cal_policy", pol.ids, "helyes")[0]
            tau = E.tau_of(tp, pol.full())
            c0 = csoport(t, tau, gid, G)
            pont = merok(c0, np.arange(G))
            pont["cp95_item"] = D.cp(pont["elfogadott"] - pont["hiba"], pont["elfogadott"]) if pont["elfogadott"] else None
            rng = np.random.default_rng(a.seed)
            fix, ujra, nincs, cache = defaultdict(list), defaultdict(list), 0, {}
            for _ in range(a.reps):
                g = rng.integers(0, G, G)
                for k, v in merok(c0, g).items():
                    fix[k].append(v)
                tau_r = E.tau_of(tp, pol.draw(rng))
                if math.isinf(tau_r):
                    nincs += 1
                if tau_r not in cache:
                    cache[tau_r] = csoport(t, tau_r, gid, G)
                for k, v in merok(cache[tau_r], g).items():
                    ujra[k].append(v)
            blk["karok"][arm] = {"tau": None if math.isinf(tau) else tau, "pont": pont,
                                 "ci_rogzitett_tau": {k: ci(v) for k, v in fix.items()},
                                 "ci_ujravalasztott_tau": {k: ci(v) for k, v in ujra.items()},
                                 "nincs_munkapont_arany": nincs / a.reps}
            print(f"{layer} {arm} kész", flush=True)
        res["retegek"][layer] = blk
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "jev_merleg05.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
