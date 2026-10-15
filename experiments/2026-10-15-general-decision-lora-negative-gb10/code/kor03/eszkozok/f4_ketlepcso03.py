"""03-as kör — kétlépcsős döntés a meglévő F4-kiolvasásokon (FELTÁRÓ, utólagos; a tesztrétegek már elhasználtak, ezért
megerősítő állítás nem épülhet rá, csak egy új kör tervéhez ad irányt; 03-runbook 7.10).

Az X-döntést a kalibrált bázis (L1★), az opcióválasztást a G3 adja. Két változat, seedenként:
  szorzat: p(X) = p_L1★(X); p(o) = (1 − p_L1★(X)) · p_G3(o | nem X), ahol p_G3(o | nem X) = p_G3(o) / (1 − p_G3(X));
           a top-1 és a bizalom ebből az eloszlásból.
  kapu:    ha az L1★ top-1-e X, a döntés X; különben a G3 legjobb nem-X opciója, a bizalom a szorzat szerinti.
A τ@95 a val-on, ugyanazzal a szabállyal (a kombinált eloszlás val-predikcióin). Rétegenként a v1 mérőszámai, az
azonos (95%-os) precizitáson elérhető lefedettség (a saját tesztjén illesztett τ, felső korlát), és egy klaszteres
bootstrap (2000 ismétlés, seed × klaszter, τ replikánként újra) a Δ-kra az L1★-hoz.

  python3 kor03/eszkozok/f4_ketlepcso03.py   → eredmenyek/F4/f4_ketlepcso03.json
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from f4_elemzes03 import (F4R, G3, Adat, Arm, Resampler, choose_tau, kmin_table, mer, metrics, osszegez,  # noqa: E402
                          point_taus, tau_gyors, xfed)

RETEGEK = ("ho-termek", "ho-routing", "ho-uj", "ho-routing-hu")
REPS = 2000


def kombinal(base: tuple, g3: tuple, mod: str) -> tuple:
    bx = base[2].get(None, 0.0)
    gs = g3[2]
    rest = max(1e-12, 1.0 - gs.get(None, 0.0))
    opts = {o: (1.0 - bx) * p / rest for o, p in gs.items() if o is not None}
    if mod == "kapu":
        if base[0] is None:
            return None, bx, {None: bx, **opts}
        o = max(opts, key=lambda k: opts[k])
        return o, opts[o], {None: bx, **opts}
    sc = {None: bx, **opts}
    pred = max(sc, key=lambda k: sc[k])
    return pred, sc[pred], sc


def main() -> None:
    D = Adat(SimpleNamespace(proba=False))
    meta = D.meta
    ids = D.val03 + D.eval03
    kmin = kmin_table(len(D.ids) + 1)
    taus = point_taus(D, kmin)
    karok = {}
    for mod in ("szorzat", "kapu"):
        for a in G3:
            karok[f"{mod}:{a}"] = {i: kombinal(D.preds["L1"][i], D.preds[a][i], mod) for i in ids}
    ktau = {k: choose_tau(p, meta, D.val03, 0.95) for k, p in karok.items()}
    out: dict = {"megjegyzes": "feltáró, utólagos; a tesztrétegek már elhasználtak", "tau_val": ktau, "pont": {}, "bootstrap": {}}
    for g in RETEGEK:
        blk = {}
        s = [i for i in D.L[g] if not meta[i]["ketertelmu"]]
        for name, p, t in [("L1", D.preds["L1"], taus["L1"]), *[(a, D.preds[a], taus[a]) for a in G3],
                           *[(k, p, ktau[k]) for k, p in karok.items()]]:
            m = metrics(p, meta, D.L[g], t, 0.93)
            to = choose_tau(p, meta, s, 0.95)
            blk[name] = {"lef": m["besorolasi_lefedettseg"], "prec": m["besorolasi_precizitas"], "aurc": m["aurc"],
                         "x_fedes": m["x_fedes"], "lef_azonos_95_precizitason": metrics(p, meta, s, to, 0.93)["besorolasi_lefedettseg"]}
        for pre in ("G3", "szorzat", "kapu"):
            names = G3 if pre == "G3" else [f"{pre}:{a}" for a in G3]
            blk[f"{pre}_atlag"] = {k: float(np.mean([blk[n][k] for n in names])) if all(blk[n][k] is not None for n in names) else None
                                   for k in blk[names[0]]}
        out["pont"][g] = blk
    # bootstrap: Δ (kombinált, 3 seed hierarchikusan) − L1★, és a precizitás
    A = {k: Arm(p, D.ids, meta) for k, p in karok.items()}
    A["L1"] = D.A["L1"]
    sc = D.scored
    groups = {"val03": D.val03, **{g: D.L[g] for g in RETEGEK}}
    RS = Resampler(D.ids, meta, groups, {g: "klaszter" for g in groups})
    rng = np.random.default_rng(1)
    acc = defaultdict(list)
    for _ in range(REPS):
        v = RS.draw("val03", rng)
        tv = {k: tau_gyors(a, v, sc, kmin) for k, a in A.items()}
        sd = list(rng.integers(0, 3, 3))
        for g in RETEGEK:
            t = RS.draw(g, rng)
            s = t[sc[t]]
            sx = s[D.xgold[s]]
            b = mer(A["L1"], s, tv["L1"])
            for mod in ("szorzat", "kapu"):
                r = [mer(A[f"{mod}:{G3[k]}"], s, tv[f"{mod}:{G3[k]}"]) for k in sd]
                acc[f"{mod}:{g}:lef"].append(float(np.mean([x[0] for x in r])) - b[0])
                acc[f"{mod}:{g}:aurc"].append(float(np.mean([x[2] for x in r])) - b[2])
                acc[f"{mod}:{g}:prec"].append(float(np.mean([x[1] for x in r])))
                acc[f"{mod}:{g}:x_fedes"].append(float(np.mean([xfed(A[f"{mod}:{G3[k]}"], sx) for k in sd])) - xfed(A["L1"], sx))
    out["bootstrap"] = {k: osszegez(x, delta=not k.endswith(":prec")) for k, x in acc.items()}
    (F4R / "f4_ketlepcso03.json").write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for g in RETEGEK:
        P = out["pont"][g]
        print(g, {k: {x: round(v, 4) if isinstance(v, float) else v for x, v in P[k].items()}
                  for k in ("L1", "G3_atlag", "szorzat_atlag", "kapu_atlag")})


if __name__ == "__main__":
    main()
