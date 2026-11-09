"""06-os kör — a B1 változatlan javaslatainak megbízhatósága (06-runbook 2.) és az F1 fejlesztési futás a 05
HO-rétegein (3.3).

A B1 javaslata itemenként a négy opciósorrend átlagolt eloszlásának argmaxa (a 05 `kalib05.decide_label`-jével
azonos; a temperature a 05 D_cal_prob-illesztése). A célcímke a B1 konkrét javaslatának szigorú helyessége.
Karok:
  B1-S      a B1 saját pontszáma (a javasolt opció átlagolt valószínűsége)
  B1-R      neurális megbízhatósági fej (a 05 RelHead H-változata, a B1 kis jellemzőivel), a D_meta-n előtanítva a B1
            helyességére (D2 a), a célterületi mintán a 05 T-meta eljárásával finomhangolva: 5-szörös, alapesetenként
            hash-elt cross-fitting, foldonként belső 20%-os korai megállással; a tesztpontszám az öt fold-modell
            logitjának átlaga. B1-R0: az előtanított fej finomhangolás nélkül
  B1-LR     L2-regularizált logisztikus regresszió öt jellemzőn (D3): top-1 − top-2, az X valószínűsége, a sorrendek
            egyetértése, a B1 saját pontszáma és a NONE-jelző (a v0.2 óta); standardizálás és C a tanítómintán
            (5-szörös, alapesetenkénti CV)
  H-T-meta  a 05 H tartalmi és megbízhatósági feje, ugyanazzal a finomhangolással, ugyanazokon a mintákon
B1 kis jellemzők (9): NONE-jelző, a javaslat valószínűsége, a második legnagyobb valószínűség, a kettő különbsége,
az X valószínűsége, az entrópia, a sorrendek egyetértése (a javaslatot adó sorrendek aránya), 1 − X, log K. A
rejtett állapotok (kanonikus sorrend) a H tartalmi fejének D_fit-statisztikájával standardizálva.
Tanítóminták (F1): a `cel:ho-*` alapesetei; T100 ⊂ T200 ⊂ teljes, öt egymásba ágyazott húzással (`k06-minta:<d>`).

  python3 kor06/eszkozok/b1rel06.py elotanit --out cache/k06/b1rel
  python3 kor06/eszkozok/b1rel06.py f1 --reteg ho-termek --out cache/k06/f1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import torch
from torch import nn

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import fej05  # noqa: E402
import kalib05 as K  # noqa: E402
import megbizhatosag05 as M5  # noqa: E402
from common import write_json  # noqa: E402

SEEDS = M5.SEEDS
D_SMALL = 9
MINTA_SEED = "k06-minta"
HUZASOK = 5
MERETEK = (100, 200, None)  # None: a teljes célcsalád-minta
C_RACS = (0.01, 0.03, 0.1, 0.3, 1.0)
F1 = {"ho-termek": ("cel:ho-termek", ("teszt:ho-termek",)),
      "ho-routing": ("cel:ho-routing", ("teszt:ho-routing", "teszt:ho-routing-hu")),
      "ho-uj": ("cel:ho-uj", ("teszt:ho-uj",))}
FEJ_H = EXP / "cache/k05/fejek/H"
REL_H = EXP / "cache/k05/megbizhatosag/H"
KALIB = EXP / "kor05/eredmenyek/F3/kalib/kalib.json"


def jell_dir(szelet: str) -> Path:
    return K._root("jellemzok", szelet) / f"{szelet.replace(':', '_')}__kanonikus"


# --- a B1 javaslata és kis jellemzői -----------------------------------------------------------------------------------

def b1_info(szelet: str, temp: float) -> dict[str, dict]:
    M = K.meta()
    out = {}
    for iid, rs in K.label_rows("B1", szelet).items():
        if M[iid]["ketertelmu"]:
            continue
        if sorted(r["perm"] for r in rs) != [0, 1, 2, 3]:
            raise SystemExit(f"B1/{szelet}: {iid} permutációi hiányosak")
        sc = [K.option_scores(r, temp) for r in rs]
        avg = {k: sum(s[k] for s in sc) / len(sc) for k in sc[0]}
        pred = max(avg, key=avg.get)
        srt = sorted(avg.values(), reverse=True)
        kind = "NONE" if pred is None else "SELECT"
        ok, ok_l = K.correctness(M[iid], kind, pred)
        out[iid] = {"kind": kind, "cand": pred, "q": avg[pred], "top2": srt[1], "gap": srt[0] - srt[1],
                    "x": avg.get(None, 0.0), "ent": -sum(v * math.log(max(v, 1e-12)) for v in avg.values()),
                    "agree": sum(max(s, key=s.get) == pred for s in sc) / len(sc),
                    "k": sum(1 for o in avg if o is not None), "group_id": M[iid]["group_id"],
                    "helyes": ok, "helyes_enyhe": ok_l}
    return out


def lr_features(b: dict) -> list[float]:
    return [b["gap"], b["x"], b["agree"], b["q"], float(b["kind"] == "NONE")]


def b1_example(e: dict, b: dict, st: fej05.Stats) -> dict:
    sel = b["kind"] == "SELECT"
    if e["k"] != b["k"]:
        raise SystemExit(f"{e['id']}: az opciószám eltér a kanonikus jellemző és a B1 sor közt")
    j = e["cand_ids"].index(b["cand"]) if sel else None
    cf = st.z("cf", e["cf"])
    return {"small": torch.tensor([float(not sel), b["q"], b["top2"], b["gap"], b["x"], b["ent"], b["agree"],
                                   1 - b["x"], math.log(b["k"])]),
            "cf": cf[j] if sel else torch.zeros(cf.shape[1]), "gf": st.z("gf", e["gf"]),
            "q": st.z("h", e["q"]), "c": st.z("h", e["c_end"][j] if sel else e["x_end"]),
            "cm": st.z("h", e["c_mean"][j] if sel else e["x_mean"]), "y": float(bool(b["helyes"]))}


class B1RelHead(M5.RelHead):
    """A 05 RelHead H-változata, a B1 kilenc kis jellemzőjével."""

    def __init__(self, d_cf: int, d_gf: int, d_h: int, d_af: int = 0, d_ag: int = 0,
                 width: int = M5.WIDTH, dropout: float = M5.DROPOUT):
        nn.Module.__init__(self)
        self.arm = "B1"
        self.proj = nn.Linear(d_h, width)
        self.net = nn.Sequential(nn.Linear(D_SMALL + d_cf + d_gf + 5 * width, width), nn.GELU(), nn.Dropout(dropout),
                                 nn.Linear(width, 1))


def b1_set(szelet: str, temp: float, st: fej05.Stats) -> tuple[list[str], list[dict], dict]:
    """A szelet B1-példái (a kétértelmű és a B1 nélküli itemek nélkül), itemsorrendben."""
    info = b1_info(szelet, temp)
    ids, rs = [], []
    for e in M5.load_examples(jell_dir(szelet), "H"):
        if e["id"] in info:
            ids.append(e["id"])
            rs.append(b1_example(e, info[e["id"]], st))
    return ids, rs, info


def h_set(szelet: str, seed: int, st: fej05.Stats, exs: list[dict]) -> tuple[list[str], list[dict], list[dict]]:
    """A H javaslatai egy seedre (DEFER nélkül: azok nem kapnak megbízhatósági pontszámot) és a példák."""
    P = M5.content_probs(FEJ_H, seed, "H", exs, st, "cpu")
    prs = [M5.proposal(e, p) for e, p in zip(exs, P)]
    keep = [i for i, pr in enumerate(prs) if pr["kind"] != "DEFER" and not exs[i]["ketertelmu"]]
    return [exs[i]["id"] for i in keep], [M5.rel_example(exs[i], prs[i], "H", st) for i in keep], [prs[i] for i in keep]


# --- tanítás ----------------------------------------------------------------------------------------------------------

def h(tag: str, g: str) -> int:
    return int(hashlib.sha256(f"{M5.TMETA_SEED}|{tag}|{g}".encode()).hexdigest(), 16)


@torch.no_grad()
def logits(model: nn.Module, rs: list[dict], ms) -> list[float]:
    return list(M5.rel_logits(model, rs, list(range(len(rs))), ms, "cpu").values())


def finomhangol(rs: list[dict], groups: list[str], load, lr: float, seed: int, tests: dict[str, list[dict]]) -> dict:
    """A 05 T-meta eljárása egy tanítómintán: öt fold, foldonként belső 20%-os korai megállás; a teszteken az öt
    fold-modell logitjának átlaga. `load()` friss (model, ms, dims) hármast ad."""
    fold = [h("fold", g) % 5 for g in groups]
    out = {n: np.zeros(len(t)) for n, t in tests.items()}
    epochs = []
    for f in range(5):
        tr = [n for n, x in enumerate(fold) if x != f]
        iv = [n for n in tr if h("belso", groups[n]) % 5 == 0]
        it = [n for n in tr if h("belso", groups[n]) % 5 != 0]
        model, ms, dims = load()
        if not iv or not it:
            raise SystemExit("üres fold a finomhangolásban")
        model, inf = M5.train_rel("B1" if isinstance(model, B1RelHead) else "H", [rs[n] for n in it],
                                  [rs[n] for n in iv], ms, dims, lr, seed * 10 + f, "cpu", init=model)
        epochs.append(len(inf["tortenet"]))
        for n, t in tests.items():
            out[n] += np.array(logits(model, t, ms)) / 5
    return {"teszt": {n: v.tolist() for n, v in out.items()}, "epoch": epochs}


def b1_lr(X: np.ndarray, y: np.ndarray, groups: list[str], tests: dict[str, np.ndarray]) -> dict:
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

    if len(set(y.tolist())) < 2:
        return {"teszt": {n: t[:, 3].tolist() for n, t in tests.items()}, "C": None, "megjegyzes": "egyosztályú minta"}
    fold = np.array([h("lr-fold", g) % 5 for g in groups])
    best, best_c = math.inf, None
    for c in C_RACS:
        ll = 0.0
        for f in range(5):
            tr, va = fold != f, fold == f
            if len(set(y[tr].tolist())) < 2 or not va.any():
                continue
            sc = StandardScaler().fit(X[tr])
            m = LogisticRegression(C=c, max_iter=2000).fit(sc.transform(X[tr]), y[tr])
            p = np.clip(m.predict_proba(sc.transform(X[va]))[:, 1], 1e-6, 1 - 1e-6)
            ll -= float(np.sum(y[va] * np.log(p) + (1 - y[va]) * np.log(1 - p)))
        if ll < best:
            best, best_c = ll, c
    sc = StandardScaler().fit(X)
    m = LogisticRegression(C=best_c, max_iter=2000).fit(sc.transform(X), y)
    return {"teszt": {n: m.decision_function(sc.transform(t)).tolist() for n, t in tests.items()}, "C": best_c,
            "egyutthatok": m.coef_[0].tolist()}


def elotanit(a) -> None:
    st = fej05.Stats.from_state(json.loads((FEJ_H / "fej.json").read_text())["stats"])
    temp = json.loads(KALIB.read_text())["B1"]["temperature"]
    ids, rs, info = b1_set(a.szelet, temp, st)
    is_val = [int(hashlib.sha256(f"{M5.VAL_SEED}|{info[i]['group_id']}".encode()).hexdigest(), 16) % 5 == 0 for i in ids]
    fit = [r for r, v in zip(rs, is_val) if not v]
    val = [r for r, v in zip(rs, is_val) if v]
    sm = torch.stack([r["small"] for r in fit])
    ms = (sm.mean(0), sm.std(0).clamp(min=1e-6))
    dims = M5.dims_for("H", rs[0])
    dims = {k: dims[k] for k in ("d_cf", "d_gf", "d_h")}
    y_val = [r["y"] for r in val]
    q_val = [info[i]["q"] for i, v in zip(ids, is_val) if v]
    runs = {}
    for seed in SEEDS:
        for lr in M5.LRS:
            torch.manual_seed(seed)
            model, inf = M5.train_rel("B1", fit, val, ms, dims, lr, seed, "cpu", init=B1RelHead(**dims))
            runs[(lr, seed)] = (model, inf)
            best = min(inf["tortenet"], key=lambda x: x["val_bce"])
            print(f"B1-R s{seed} lr={lr}: val BCE {inf['legjobb_val_bce']:.4f}, AUROC {best['val_auroc']:.4f}", flush=True)
    mean = {lr: float(np.mean([runs[(lr, s)][1]["legjobb_val_bce"] for s in SEEDS])) for lr in M5.LRS}
    lr_best = min(mean, key=mean.get)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for s in SEEDS:
        torch.save({"state_dict": runs[(lr_best, s)][0].state_dict(), "dims": dims,
                    "kis_jellemzo_stat": [ms[0].tolist(), ms[1].tolist()], "lr": lr_best}, out / f"rel_s{s}.pt")
    write_json(out / "elotanit.json", {
        "szelet": a.szelet, "n": len(rs), "n_fit": len(fit), "n_val": len(val), "temperature": temp, "lr_valasztott": lr_best,
        "val_bce_lr_szerint": mean, "B1_helyes_arany": float(np.mean([r["y"] for r in rs])),
        "val_auroc_B1_sajat": M5.auroc(q_val, y_val),
        "val_auroc_seedenkent": {s: max(x["val_auroc"] for x in runs[(lr_best, s)][1]["tortenet"]) for s in SEEDS},
        "futasok": [runs[k][1] for k in runs]})


def load_b1(path: Path):
    def f():
        ck = torch.load(path, weights_only=False, map_location="cpu")
        m = B1RelHead(**ck["dims"])
        m.load_state_dict(ck["state_dict"])
        return m, tuple(torch.tensor(x) for x in ck["kis_jellemzo_stat"]), ck["dims"]
    return f


def load_h(path: Path):
    def f():
        m, ms, ck = M5.load_rel(path, "H", "cpu")
        return m, ms, ck["dims"]
    return f


def huzas(groups: list[str], layer: str, d: int) -> list[str]:
    return sorted(groups, key=lambda g: hashlib.sha256(f"{MINTA_SEED}:{d}|{layer}|{g}".encode()).hexdigest())


def f1(a) -> None:
    warnings.filterwarnings("ignore", category=UserWarning)
    layer = a.reteg
    cel, tesztek = F1[layer]
    st = fej05.Stats.from_state(json.loads((FEJ_H / "fej.json").read_text())["stats"])
    temp = json.loads(KALIB.read_text())["B1"]["temperature"]
    pre = Path(a.elotanitott)
    lr_b1 = json.loads((pre / "elotanit.json").read_text())["lr_valasztott"]
    lr_h = json.loads((REL_H / "rel.json").read_text())["lr_valasztott"]
    out = Path(a.out) / layer
    out.mkdir(parents=True, exist_ok=True)

    # a B1: tanítóminta és tesztek
    c_ids, c_rs, c_info = b1_set(cel, temp, st)
    T = {n: b1_set(n, temp, st) for n in tesztek}
    groups = sorted({c_info[i]["group_id"] for i in c_ids})
    cfg = [(n, d) for n in MERETEK for d in (range(HUZASOK) if n else (0,))]
    mintak = {(n, d): set(huzas(groups, layer, d)[:n] if n else groups) for n, d in cfg}
    res = {"reteg": layer, "cel": cel, "alapeset": len(groups), "lr_B1R": lr_b1, "lr_H": lr_h, "temperature": temp,
           "konfig": [[n, d] for n, d in cfg], "B1": {}, "H": {}, "pontszam": {}}
    for n, (ids, rs, info) in T.items():
        res["B1"][n] = {"ids": ids, "javaslat": [info[i]["kind"] for i in ids], "helyes": [info[i]["helyes"] for i in ids],
                        "helyes_enyhe": [info[i]["helyes_enyhe"] for i in ids], "q": [info[i]["q"] for i in ids]}

    # B1-R0 és B1-R
    for s in SEEDS:
        m, ms, _ = load_b1(pre / f"rel_s{s}.pt")()
        for n, (_, rs, _) in T.items():
            res["pontszam"][f"B1-R0|{s}|{n}"] = logits(m, rs, ms)
    for (n, d) in cfg:
        sel = [k for k, i in enumerate(c_ids) if c_info[i]["group_id"] in mintak[(n, d)]]
        g = [c_info[c_ids[k]]["group_id"] for k in sel]
        for s in SEEDS:
            r = finomhangol([c_rs[k] for k in sel], g, load_b1(pre / f"rel_s{s}.pt"), lr_b1, s,
                            {nn_: t[1] for nn_, t in T.items()})
            for nn_, v in r["teszt"].items():
                res["pontszam"][f"B1-R|{n}|{d}|{s}|{nn_}"] = v
        # B1-LR
        X = np.array([lr_features(c_info[c_ids[k]]) for k in sel])
        y = np.array([float(bool(c_info[c_ids[k]]["helyes"])) for k in sel])
        r = b1_lr(X, y, g, {nn_: np.array([lr_features(t[2][i]) for i in t[0]]) for nn_, t in T.items()})
        for nn_, v in r["teszt"].items():
            res["pontszam"][f"B1-LR|{n}|{d}|{nn_}"] = v
        res.setdefault("B1-LR_C", {})[f"{n}|{d}"] = r["C"]
        print(f"{layer}: B1-R és B1-LR kész (n={n or len(groups)}, húzás {d})", flush=True)
    del c_rs, T

    # H (05, finomhangolás nélkül) és H-T-meta, ugyanazokon a mintákon
    c_exs = M5.load_examples(jell_dir(cel), "H")
    t_exs = {n: M5.load_examples(jell_dir(n), "H") for n in tesztek}
    gid = {i: K.meta()[i]["group_id"] for i in K.meta()}
    for s in SEEDS:
        ci, crs, _ = h_set(cel, s, st, c_exs)
        th = {n: h_set(n, s, st, ex) for n, ex in t_exs.items()}
        for n, (ids, rs, prs) in th.items():
            res["H"][f"{s}|{n}"] = {"ids": ids, "javaslat": [p["kind"] for p in prs], "helyes": [p["helyes"] for p in prs],
                                    "helyes_enyhe": [p["helyes_enyhe"] for p in prs]}
            m, ms, _ = load_h(REL_H / f"rel_s{s}.pt")()
            res["pontszam"][f"H|{s}|{n}"] = logits(m, rs, ms)
        for (n, d) in cfg:
            sel = [k for k, i in enumerate(ci) if gid[i] in mintak[(n, d)]]
            r = finomhangol([crs[k] for k in sel], [gid[ci[k]] for k in sel], load_h(REL_H / f"rel_s{s}.pt"), lr_h, s,
                            {n_: t[1] for n_, t in th.items()})
            for n_, v in r["teszt"].items():
                res["pontszam"][f"H-T-meta|{n}|{d}|{s}|{n_}"] = v
        print(f"{layer}: H és H-T-meta kész (s{s})", flush=True)
    (out / "f1.json").write_text(json.dumps(res) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("elotanit")
    e.add_argument("--szelet", default="D_meta", help="csak próbához más (pl. D_cal_prob)")
    e.add_argument("--out", required=True)
    f = sub.add_parser("f1")
    f.add_argument("--reteg", required=True, choices=list(F1))
    f.add_argument("--elotanitott", default=str(EXP / "cache/k06/b1rel"))
    f.add_argument("--out", required=True)
    a = ap.parse_args()
    {"elotanit": elotanit, "f1": f1}[a.cmd](a)


if __name__ == "__main__":
    main()
