"""07-es kör — F3R: a fejek tanítása és mentése (07-runbook 2., 7. F3R, D2, D3, D12, D23).

A 06 `b1rel06` útja, a fejek elmentésével, hogy az F5 (és a 07B) a mentett fejeket pontozza:
  B1-4R0   a négyállapotú B1 megbízhatósági feje a D_meta-n előtanítva (a D_meta a négyállapotú prompttal, F1M), a B1-4
           döntés szigorú (négyosztályos) helyességére; validáció a 05 VAL_SEED-jével (alapesetenként 20%); seedenként
           egy fej, a tanulási ráta a seedek átlagos val-BCE-je szerint
  B1-4R    a B1-4R0 a család 06-os T500-án finomhangolva: öt fold a sabloncsoport szerint (D23), foldonként belső 20%-os
           korai megállás; seedenként öt fold-modell, a pontszám az öt logit átlaga
  B1-R     a 06 recept változatlanul (05 D_meta-előtanítás `cache/k06/b1rel`, 06 T500-finomhangolás, ugyanazok a
           seedek és foldok), a fold-modellek elmentve; önellenőrzés: a mentett modellek átlaga a 06 TESZT-en bitre
           egyezik az F0 reprodukció pontszámaival (`cache/k07/f0_repro`)
  B1-LR    a 06 öt jellemzője (top-1 − top-2, p(X), egyetértés, q, NONE-jelző); L2-logisztikus regresszió, C a 06
           rácsán sablonos ötszörös CV-vel; a standardizálás és az együtthatók elmentve
  B1-4LR   D12 (rögzítve 2026-11-01): top-1 − top-2, q, egyetértés, p(X), p(Y), p(Z), a válasz típusa (opció / X / Y / Z
           indikátor) — 10 jellemző, ugyanazzal az eljárással
Temperature: a B1-4-é a 06 T500-án (3 család, perm 0, a gold válasz NLL-je; D2), a B1-é a 05-é (`kalib.json`).

A B1-4R példája: 15 kis jellemző (a 06 kilence: nem-SELECT, q, top-2, gap, p(X), entrópia, egyetértés, 1 − p(X), log k;
és hat új: p(Y), p(Z), az opciókra jutó tömeg, X-, Y-, Z-jelző); a jelölt-jellemző (cf) és a rejtett állapotok a
választott válasz sorából: opciónál a 06 szerint, X-nél az X sora (cf nulla, mint a 06-ban), Y-nál és Z-nél a saját
sor (cf a `c_features` Y / Z sora). A rejtett állapotok és a cf / gf z-skálázása a 05 H fejének statisztikájával.
A négyállapotú spanok sorrendje: opciók, X, Y, Z (a `keret07` rögzített sorrendje); a 05 `to_example` az X-et az utolsó
spannak hiszi, ezért itt saját példaépítés van (`to_example4`).

Kimenet: `cache/k07/fejek/<család>/B1-4R_s<seed>_f<fold>.pt`, `B1-R_s<seed>_f<fold>.pt`, `B1-LR.json`, `B1-4LR.json`;
`cache/k07/fejek/B1-4R0_s<seed>.pt`, `elotanit4.json`, `temperature.json`, `fejek.json` (fájllista sha256-tal);
összegzés `kor07/eredmenyek/F3R/f3r.{json,md}` (a 06 TESZT-en mért AURC csak tervezési próba: a 06 adata ismert).

  python3 kor07/eszkozok/b1rel07.py tanit [--out cache/k07/fejek] [--csak B1-4R0,B1-4R,B1-R,B1-LR,B1-4LR] [--limit N]

Pontozás (F5, 07B): a mentett fejek egy szeleten, mindkét kerettel; a 07 CAL / TESZT csak a pecsét kapuja után
(`pecset07.kapu`: a v1 rögzítése), a 06 szeletei nyitottak (önellenőrzés: `--ellenoriz` a k06 TESZT-en a tanítás közben
mért pontszámokkal és az F0 reprodukcióval veti össze a pontozó utat).
  python3 kor07/eszkozok/b1rel07.py pontoz --szelet k06:penzugy.bankparositas:TESZT --out cache/k07/f3r_proba \\
      --ellenoriz kor07/eredmenyek/F3R/f3r.json
  python3 kor07/eszkozok/b1rel07.py pontoz --szelet penzugy.bankparositas:TESZT --out cache/k07/f5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import torch
from scipy.optimize import minimize_scalar
from torch import nn

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor06/eszkozok"), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import b14_07 as B4  # noqa: E402
import b1rel06 as B  # noqa: E402
import fej05  # noqa: E402
import friss06 as F6  # noqa: E402
import kalib05 as K  # noqa: E402
import keret07 as K7  # noqa: E402
import megbizhatosag05 as M5  # noqa: E402
from common import write_json  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
JELL07 = EXP / "cache/k07/jellemzok"
B1REL06 = EXP / "cache/k06/b1rel"
FEJ_H = EXP / "cache/k05/fejek/H"
KALIB = EXP / "kor05/eredmenyek/F3/kalib/kalib.json"
F0_REPRO = EXP / "cache/k07/f0_repro"
SEEDS, LRS = fej05.SEEDS, fej05.LRS
D_SMALL4 = 15
KAROK = ("B1-4R0", "B1-4R", "B1-R", "B1-LR", "B1-4LR")
LR_JELLEMZOK = ("gap", "x", "agree", "q", "none")
LR4_JELLEMZOK = ("gap", "q", "agree", "x", "y", "z", "opcio", "X", "Y", "Z")


# --- a négyállapotú sorok és döntések ----------------------------------------------------------------------------------

def rows4(prefix: str, root: Path = JELL07) -> dict[str, list[dict]]:
    by = defaultdict(list)
    for mod in ("kanonikus", "b1"):
        d = root / f"{prefix}__{mod}"
        if not d.exists():
            raise SystemExit(f"hiányzik: {d.relative_to(EXP)}")
        for f in sorted(d.glob("sorok_*.jsonl")):
            for r in K.jsonl(f):
                by[r["id"]].append(r)
    for i, rs in by.items():
        if sorted(r["perm"] for r in rs) != [0, 1, 2, 3]:
            raise SystemExit(f"{prefix}: {i} permutációi hiányosak")
        if any("gold_key" not in r for r in rs):
            raise SystemExit(f"{prefix}: {i} sorában nincs gold_key (nem a kiolvas07 írta?)")
    return by


def fit_temp4(by: dict[str, list[dict]]) -> float:
    """D2: a gold válasz NLL-je a perm 0 sorokon (a `b14_07.fit_temp` a sor saját gold_key-ével, meta nélkül)."""
    rows0 = [r for rs in by.values() for r in rs if r["perm"] == 0 and not r["ketertelmu"]]

    def nll(logt: float) -> float:
        t, tot = math.exp(logt), 0.0
        for r in rows0:
            tot -= math.log(max(1e-12, K.option_scores(r, t)[r["gold_key"]]))
        return tot
    return float(math.exp(minimize_scalar(nll, bounds=(-3, 4), method="bounded").x))  # type: ignore[attr-defined]


def decide4(rs: list[dict], temp: float) -> dict:
    """A négy sorrend átlagolt eloszlása, az argmax és a kis jellemzők; a helyesség a sor gold_key-éhez (szigorú: a kulcs
    egyezik; enyhe: nem-SELECT a nem-MATCH itemen)."""
    sc = [K.option_scores(r, temp) for r in rs]
    avg = {k: sum(s[k] for s in sc) / len(sc) for k in sc[0]}
    pred = max(avg, key=avg.get)
    srt = sorted(avg.values(), reverse=True)
    gold = rs[0]["gold_key"]
    kind = K7.kind_of(pred)
    return {"kind": kind, "cand": pred, "q": avg[pred], "top2": srt[1], "gap": srt[0] - srt[1],
            "x": avg.get(None, 0.0), "y": avg.get(K7.Y_ID, 0.0), "z": avg.get(K7.Z_ID, 0.0),
            "ent": -sum(v * math.log(max(v, 1e-12)) for v in avg.values()),
            "agree": sum(max(s, key=s.get) == pred for s in sc) / len(sc),
            "k": sum(1 for o in avg if o not in (None, K7.Y_ID, K7.Z_ID)),
            "helyes": pred == gold, "helyes_enyhe": (pred == gold) if kind == "SELECT" else (K7.kind_of(gold) != "SELECT")}


def to_example4(e: dict) -> dict:
    """A kanonikus (perm 0) sor és jellemzői négyállapotú példává: opciók, majd X, Y, Z (span-sorrend = order)."""
    r, f = e["row"], e["feat"]
    labs, order = r["labels"], r["order"]
    if labs[-3:] != ["X", K7.Y_LABEL, K7.Z_LABEL] or order[-3:] != [None, K7.Y_ID, K7.Z_ID]:
        raise SystemExit(f"{r['id']}: nem négyállapotú sorrend ({labs})")
    k = len(labs) - 3
    cf, gf = fej05.c_features(r)  # cf: k + 2 sor (opciók, Y, Z); gf-ben a jelöltszám k + 2
    if len(cf) != k + 2 or f["h_opt_end"].shape[1] != k + 3:
        raise SystemExit(f"{r['id']}: span- vagy jellemzőszám eltér (k={k}, cf={len(cf)}, span={f['h_opt_end'].shape[1]})")
    he, hm = f["h_opt_end"], f["h_opt_mean"]
    return {"id": r["id"], "k": k, "cand_ids": order[:k], "ketertelmu": bool(r["ketertelmu"]),
            "cf": torch.tensor(cf), "gf": torch.tensor(gf), "q": f["h_last"].reshape(-1),
            "c_end": he[:, :k].permute(1, 0, 2).reshape(k, -1), "c_mean": hm[:, :k].permute(1, 0, 2).reshape(k, -1),
            "s_end": {None: he[:, k].reshape(-1), K7.Y_ID: he[:, k + 1].reshape(-1), K7.Z_ID: he[:, k + 2].reshape(-1)},
            "s_mean": {None: hm[:, k].reshape(-1), K7.Y_ID: hm[:, k + 1].reshape(-1), K7.Z_ID: hm[:, k + 2].reshape(-1)}}


def rel_example4(e: dict, d: dict, st: fej05.Stats) -> dict:
    sel = d["kind"] == "SELECT"
    if e["k"] != d["k"]:
        raise SystemExit(f"{e['id']}: az opciószám eltér a jellemző és a döntés közt")
    cf = st.z("cf", e["cf"])
    if sel:
        j = e["cand_ids"].index(d["cand"])
        cfj, c, cm = cf[j], e["c_end"][j], e["c_mean"][j]
    else:
        key = d["cand"]
        cfj = torch.zeros(cf.shape[1]) if key is None else cf[e["k"] + (0 if key == K7.Y_ID else 1)]
        c, cm = e["s_end"][key], e["s_mean"][key]
    x, y, z = d["x"], d["y"], d["z"]
    small = [float(not sel), d["q"], d["top2"], d["gap"], x, d["ent"], d["agree"], 1 - x, math.log(e["k"]),
             y, z, max(0.0, 1 - x - y - z), float(d["kind"] == "NONE"), float(d["kind"] == "MISSING"), float(d["kind"] == "OOS")]
    return {"small": torch.tensor(small), "cf": cfj, "gf": st.z("gf", e["gf"]), "q": st.z("h", e["q"]),
            "c": st.z("h", c), "cm": st.z("h", cm), "y": float(bool(d["helyes"]))}


def lr4_features(d: dict) -> list[float]:
    return [d["gap"], d["q"], d["agree"], d["x"], d["y"], d["z"], float(d["kind"] == "SELECT"),
            float(d["kind"] == "NONE"), float(d["kind"] == "MISSING"), float(d["kind"] == "OOS")]


def set4(prefix: str, temp: float, st: fej05.Stats, root: Path = JELL07) -> tuple[list[str], list[dict], dict]:
    """Egy szelet négyállapotú példái (a kétértelmű itemek nélkül), itemsorrendben: (id-k, példák, döntések)."""
    by = rows4(prefix, root)
    ids, rs, info = [], [], {}
    for e in (to_example4(x) for x in fej05.load_dir(root / f"{prefix}__kanonikus")):
        if e["ketertelmu"] or e["id"] not in by:
            continue
        d = decide4(by[e["id"]], temp)
        ids.append(e["id"])
        info[e["id"]] = d
        rs.append(rel_example4(e, d, st))
    return ids, rs, info


class B1Rel4Head(M5.RelHead):
    """A 06 `B1RelHead` a 15 kis jellemzővel."""

    def __init__(self, d_cf: int, d_gf: int, d_h: int, width: int = M5.WIDTH, dropout: float = M5.DROPOUT):
        nn.Module.__init__(self)
        self.arm = "B1-4"
        self.proj = nn.Linear(d_h, width)
        self.net = nn.Sequential(nn.Linear(D_SMALL4 + d_cf + d_gf + 5 * width, width), nn.GELU(), nn.Dropout(dropout),
                                 nn.Linear(width, 1))


def load_b14(path: Path):
    def f():
        ck = torch.load(path, weights_only=False, map_location="cpu")
        m = B1Rel4Head(**ck["dims"])
        m.load_state_dict(ck["state_dict"])
        return m, tuple(torch.tensor(x) for x in ck["kis_jellemzo_stat"]), ck["dims"]
    return f


# --- tanítás (a 06 `b1rel06` lépései, a modellek megtartásával) --------------------------------------------------------

def finomhangol(rs: list[dict], groups: list[str], load, lr: float, seed: int, tests: dict[str, list[dict]]):
    """A `b1rel06.finomhangol` lépésről lépésre (ugyanaz a fold-hash, belső megállás és seed), de a fold-modellek is
    visszajönnek. A fold-hash a `b1rel06.h`, ami a `friss06.telepit` után a sabloncsoportra mutat (D23)."""
    fold = [B.h("fold", g) % 5 for g in groups]
    out = {n: np.zeros(len(t)) for n, t in tests.items()}
    models, epochs = [], []
    for f in range(5):
        tr = [n for n, x in enumerate(fold) if x != f]
        iv = [n for n in tr if B.h("belso", groups[n]) % 5 == 0]
        it = [n for n in tr if B.h("belso", groups[n]) % 5 != 0]
        model, ms, dims = load()
        if not iv or not it:
            raise SystemExit("üres fold a finomhangolásban")
        model, inf = M5.train_rel("B1", [rs[n] for n in it], [rs[n] for n in iv], ms, dims, lr, seed * 10 + f, "cpu",
                                  init=model)
        models.append((model, ms, dims))
        epochs.append(len(inf["tortenet"]))
        for n, t in tests.items():
            out[n] += np.array(B.logits(model, t, ms)) / 5
    return models, epochs, {n: v.tolist() for n, v in out.items()}


def lr_illesztes(X: np.ndarray, y: np.ndarray, groups: list[str], nevek: tuple[str, ...]) -> dict:
    """A `b1rel06.b1_lr` eljárása (C a rácson, ötszörös CV a fold-hash szerint, végül a teljes mintán), a standardizálás
    és az együtthatók elmentésével."""
    from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
    from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

    if len(set(y.tolist())) < 2:
        return {"C": None, "megjegyzes": "egyosztályú minta", "jellemzok": list(nevek), "n": int(len(y))}
    fold = np.array([B.h("lr-fold", g) % 5 for g in groups])
    best, best_c = math.inf, None
    for c in B.C_RACS:
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
    return {"C": best_c, "jellemzok": list(nevek), "n": int(len(y)), "pozitiv_arany": float(y.mean()),
            "standardizalas": {"mean": sc.mean_.tolist(), "scale": sc.scale_.tolist()},
            "egyutthatok": m.coef_[0].tolist(), "konstans": float(m.intercept_[0])}


def lr_pontszam(ill: dict, X: np.ndarray) -> np.ndarray:
    if ill.get("C") is None:
        return X[:, 3] if X.shape[1] > 3 else X[:, 0]
    z = (X - np.array(ill["standardizalas"]["mean"])) / np.array(ill["standardizalas"]["scale"])
    return z @ np.array(ill["egyutthatok"]) + ill["konstans"]


def mentes(path: Path, model: nn.Module, ms, dims: dict, **meta) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"state_dict": model.state_dict(), "dims": dims, "kis_jellemzo_stat": [ms[0].tolist(), ms[1].tolist()],
                **meta}, path)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# --- az egyes karok -----------------------------------------------------------------------------------------------------

def elotanit4(out: Path, temp4: float, st: fej05.Stats, limit: int | None) -> dict:
    t0 = time.time()
    ids, rs, info = set4("k05_D_meta", temp4, st)
    if limit:
        ids, rs = ids[:limit], rs[:limit]
    gid = M5.group_ids()
    is_val = [int(hashlib.sha256(f"{M5.VAL_SEED}|{gid[i]}".encode()).hexdigest(), 16) % 5 == 0 for i in ids]
    fit = [r for r, v in zip(rs, is_val) if not v]
    val = [r for r, v in zip(rs, is_val) if v]
    sm = torch.stack([r["small"] for r in fit])
    ms = (sm.mean(0), sm.std(0).clamp(min=1e-6))
    dims = {"d_cf": rs[0]["cf"].shape[0], "d_gf": rs[0]["gf"].shape[0], "d_h": rs[0]["q"].shape[0]}
    runs = {}
    for seed in SEEDS:
        for lr in LRS:
            torch.manual_seed(seed)
            model, inf = M5.train_rel("B1", fit, val, ms, dims, lr, seed, "cpu", init=B1Rel4Head(**dims))
            runs[(lr, seed)] = (model, inf)
            best = min(inf["tortenet"], key=lambda x: x["val_bce"])
            print(f"B1-4R0 s{seed} lr={lr}: val BCE {inf['legjobb_val_bce']:.4f}, AUROC {best['val_auroc']:.4f}", flush=True)
    mean = {lr: float(np.mean([runs[(lr, s)][1]["legjobb_val_bce"] for s in SEEDS])) for lr in LRS}
    lr_best = min(mean, key=mean.get)
    for s in SEEDS:
        mentes(out / f"B1-4R0_s{s}.pt", runs[(lr_best, s)][0], ms, dims, kar="B1-4R0", seed=s, lr=lr_best, temperature=temp4)
    kinds = Counter(info[i]["kind"] for i in ids)
    rep = {"szelet": "k05:D_meta (négyállapotú)", "n": len(rs), "n_fit": len(fit), "n_val": len(val), "temperature": temp4,
           "lr_valasztott": lr_best, "val_bce_lr_szerint": mean, "B1-4_helyes_arany": float(np.mean([r["y"] for r in rs])),
           "dontesek": dict(kinds), "dims": dims, "kis_jellemzo": D_SMALL4,
           "val_auroc_B1-4_sajat": M5.auroc([info[i]["q"] for i, v in zip(ids, is_val) if v], [r["y"] for r in val]),
           "val_auroc_seedenkent": {s: max(x["val_auroc"] for x in runs[(lr_best, s)][1]["tortenet"]) for s in SEEDS},
           "futasok": [runs[k][1] for k in runs], "ido_s": round(time.time() - t0)}
    write_json(out / "elotanit4.json", rep)
    return rep


def b14r_csalad(out: Path, fam: str, temp4: float, st: fej05.Stats, limit: int | None) -> dict:
    """B1-4R: a B1-4R0 finomhangolása a család 06-os T500-án; a 06 TESZT (négyállapotú, ismert adat) csak próba."""
    t0 = time.time()
    lr = json.loads((out / "elotanit4.json").read_text())["lr_valasztott"]
    c_ids, c_rs, c_info = set4(f"k06_{fam}_T500", temp4, st)
    if limit:
        c_ids, c_rs = c_ids[:limit], c_rs[:limit]
    t_ids, t_rs, t_info = set4(f"k06_{fam}_TESZT", temp4, st)
    y_t = np.array([t_info[i]["helyes"] for i in t_ids], bool)
    q_t = np.array([t_info[i]["q"] for i in t_ids])
    rep = {"n_T500": len(c_rs), "n_TESZT": len(t_rs), "lr": lr, "dontesek_T500": dict(Counter(c_info[i]["kind"] for i in c_ids)),
           "helyes_T500": float(np.mean([c_info[i]["helyes"] for i in c_ids])),
           "proba_06_TESZT": {"aurc_B1-4S": B4.aurc(q_t, y_t), "helyes": float(y_t.mean())}, "seedek": {}}
    for s in SEEDS:
        models, epochs, pont = finomhangol(c_rs, c_ids, load_b14(out / f"B1-4R0_s{s}.pt"), lr, s, {"TESZT": t_rs})
        for f, (m, ms, dims) in enumerate(models):
            mentes(out / fam / f"B1-4R_s{s}_f{f}.pt", m, ms, dims, kar="B1-4R", csalad=fam, seed=s, fold=f, lr=lr, temperature=temp4)
        rep["seedek"][s] = {"epoch": epochs, "proba_06_TESZT_aurc_B1-4R": B4.aurc(np.array(pont["TESZT"]), y_t)}
        print(f"{fam}: B1-4R s{s} kész (epoch {epochs}; próba 06 TESZT AURC {rep['seedek'][s]['proba_06_TESZT_aurc_B1-4R']:.4f} "
              f"vs B1-4S {rep['proba_06_TESZT']['aurc_B1-4S']:.4f})", flush=True)
    # B1-4LR (D12) ugyanezen a T500-on
    X = np.array([lr4_features(c_info[i]) for i in c_ids])
    y = np.array([float(bool(c_info[i]["helyes"])) for i in c_ids])
    ill = lr_illesztes(X, y, c_ids, LR4_JELLEMZOK)
    write_json(out / fam / "B1-4LR.json", {"kar": "B1-4LR", "csalad": fam, "temperature": temp4, **ill})
    Xt = np.array([lr4_features(t_info[i]) for i in t_ids])
    rep["B1-4LR"] = {"C": ill.get("C"), "proba_06_TESZT_aurc": B4.aurc(lr_pontszam(ill, Xt), y_t)}
    rep["ido_s"] = round(time.time() - t0)
    return rep


def b1r_csalad(out: Path, fam: str, temp06: float, st: fej05.Stats, limit: int | None) -> dict:
    """B1-R és B1-LR a 06 receptjével (a `friss06.telepit` betöltőivel); a mentett fold-modellek átlaga a 06 TESZT-en
    az F0 reprodukció pontszámaival összevetve (bitre azonosnak kell lennie)."""
    t0 = time.time()
    lr = json.loads((B1REL06 / "elotanit.json").read_text())["lr_valasztott"]
    c_ids, c_rs, c_info = B.b1_set(f"{fam}:T500", temp06, st)
    if limit:
        c_ids, c_rs = c_ids[:limit], c_rs[:limit]
    t_ids, t_rs, t_info = B.b1_set(f"{fam}:TESZT", temp06, st)
    groups = [c_info[i]["group_id"] for i in c_ids]
    repro = json.loads((F0_REPRO / fam / "f1.json").read_text())["pontszam"] if (F0_REPRO / fam / "f1.json").exists() else None
    rep = {"n_T500": len(c_rs), "n_TESZT": len(t_rs), "lr": lr, "seedek": {}, "repro_forras": str(F0_REPRO.relative_to(EXP)) if repro else None}
    for s in SEEDS:
        models, epochs, pont = finomhangol(c_rs, groups, B.load_b1(B1REL06 / f"rel_s{s}.pt"), lr, s, {"TESZT": t_rs})
        for f, (m, ms, dims) in enumerate(models):
            mentes(out / fam / f"B1-R_s{s}_f{f}.pt", m, ms, dims, kar="B1-R", csalad=fam, seed=s, fold=f, lr=lr, temperature=temp06)
        d = None
        if repro and not limit:
            regi = np.array(repro[f"B1-R|None|0|{s}|{fam}:TESZT"])
            d = float(np.max(np.abs(regi - np.array(pont["TESZT"])))) if len(regi) == len(pont["TESZT"]) else "eltérő hossz"
        rep["seedek"][s] = {"epoch": epochs, "repro_max_elteres_06_TESZT": d}
        print(f"{fam}: B1-R s{s} kész (epoch {epochs}; repro max|Δ| {d})", flush=True)
    X = np.array([B.lr_features(c_info[i]) for i in c_ids])
    y = np.array([float(bool(c_info[i]["helyes"])) for i in c_ids])
    ill = lr_illesztes(X, y, groups, LR_JELLEMZOK)
    write_json(out / fam / "B1-LR.json", {"kar": "B1-LR", "csalad": fam, "temperature": temp06, **ill})
    if repro and not limit and ill.get("C") is not None:
        regi = np.array(repro[f"B1-LR|None|0|{fam}:TESZT"])
        uj = lr_pontszam(ill, np.array([B.lr_features(t_info[i]) for i in t_ids]))
        rep["B1-LR"] = {"C": ill["C"], "repro_max_elteres_06_TESZT": float(np.max(np.abs(regi - uj)))}
    else:
        rep["B1-LR"] = {"C": ill.get("C")}
    rep["ido_s"] = round(time.time() - t0)
    return rep


# --- a lap és a főprogram ----------------------------------------------------------------------------------------------

def f(x, d: int = 4) -> str:
    return "–" if x is None else (x if isinstance(x, str) else f"{x:.{d}f}".replace(".", ","))


def lap(res: dict) -> str:
    L = ["# 07 F3R — a fejek tanítása és mentése", "",
         f"Temperature: B1-4 {f(res['temperature']['B1-4'])} (06 T500, 3 család, perm 0; D2), B1 {f(res['temperature']['B1'])} (05). "
         f"Seedek {SEEDS}; fold: sabloncsoport (D23). Limit: {res['limit'] or 'nincs'}.", ""]
    if "B1-4R0" in res:
        e = res["B1-4R0"]
        L += ["## B1-4R0 (D_meta, négyállapotú)", "",
              f"n {e['n']} (fit {e['n_fit']}, val {e['n_val']}); a B1-4 helyes {f(e['B1-4_helyes_arany'], 3)}; döntések {e['dontesek']}; "
              f"lr {e['lr_valasztott']} (val BCE lr szerint {', '.join(f'{k}: {f(v)}' for k, v in e['val_bce_lr_szerint'].items())}); "
              f"val AUROC seedenként {', '.join(f'{k}: {f(v, 3)}' for k, v in e['val_auroc_seedenkent'].items())}, a B1-4 saját pontszáma "
              f"{f(e['val_auroc_B1-4_sajat'], 3)}; {e['ido_s']} s.", ""]
    if res.get("csaladok"):
        L += ["## Családonként", "", "| család | kar | n T500 | lr | epoch (fold) seedenként | ellenőrzés |", "|---|---|---|---|---|---|"]
        for fam, c in res["csaladok"].items():
            if "B1-4R" in c:
                r = c["B1-4R"]
                ep = "; ".join(f"s{s}: {v['epoch']}" for s, v in r["seedek"].items())
                pr = ", ".join(f"s{s} {f(v['proba_06_TESZT_aurc_B1-4R'])}" for s, v in r["seedek"].items())
                L.append(f"| {fam} | B1-4R | {r['n_T500']} | {r['lr']} | {ep} | próba 06 TESZT AURC: B1-4R {pr}; B1-4S "
                         f"{f(r['proba_06_TESZT']['aurc_B1-4S'])}; B1-4LR {f(r['B1-4LR']['proba_06_TESZT_aurc'])} (C {r['B1-4LR']['C']}) |")
            if "B1-R" in c:
                r = c["B1-R"]
                ep = "; ".join(f"s{s}: {v['epoch']}" for s, v in r["seedek"].items())
                rp = ", ".join(f"s{s} {f(v['repro_max_elteres_06_TESZT'], 6)}" for s, v in r["seedek"].items())
                L.append(f"| {fam} | B1-R | {r['n_T500']} | {r['lr']} | {ep} | repro max\\|Δ\\| a 06 TESZT-en: {rp}; B1-LR C {r['B1-LR'].get('C')}, "
                         f"max\\|Δ\\| {f(r['B1-LR'].get('repro_max_elteres_06_TESZT'), 6)} |")
        L += ["", "A „próba 06 TESZT” a 06 ismert adata (tervezési próba, nem állítás); a B1-R repro-eltérésnek 0-nak kell lennie."]
    if "fajlok" in res:
        L += ["", f"Mentett fájlok: {len(res['fajlok'])} (`{res['out']}`; lista és sha256: `fejek.json`)."]
    return "\n".join(L) + "\n"


def tanit(a) -> None:
    t0 = time.time()
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    karok = a.csak.split(",") if a.csak else list(KAROK)
    st = fej05.Stats.from_state(json.loads((FEJ_H / "fej.json").read_text())["stats"])
    temp06 = json.loads(KALIB.read_text())["B1"]["temperature"]
    temp4 = fit_temp4({i: rs for fam in CSALADOK for i, rs in rows4(f"k06_{fam}_T500").items()})
    write_json(out / "temperature.json", {"B1-4": temp4, "B1-4_forras": "06 T500, 3 család, perm 0, a gold válasz NLL-je (D2)",
                                          "B1": temp06, "B1_forras": "05 kalib.json (D_cal_prob)"})
    print(f"temperature: B1-4 {temp4:.4f}, B1 {temp06:.4f}", flush=True)
    res = {"temperature": {"B1-4": temp4, "B1": temp06}, "limit": a.limit, "out": a.out, "csaladok": {}}
    if "B1-4R0" in karok:
        res["B1-4R0"] = elotanit4(out, temp4, st, a.limit)
    F6.telepit()  # a 06 betöltői (K.meta, K._root) és a sablonos fold-hash (B.h); a D_meta-ág ezek előtt futott
    for fam in CSALADOK:
        c = {}
        if "B1-4R" in karok or "B1-4LR" in karok:
            c["B1-4R"] = b14r_csalad(out, fam, temp4, st, a.limit)
        if "B1-R" in karok or "B1-LR" in karok:
            c["B1-R"] = b1r_csalad(out, fam, temp06, st, a.limit)
        res["csaladok"][fam] = c
    fajlok = sorted(p for p in out.rglob("*") if p.is_file() and p.name != "fejek.json")
    res["fajlok"] = {str(p.relative_to(out)): sha(p) for p in fajlok}
    write_json(out / "fejek.json", {"keszult": time.strftime("%Y-%m-%dT%H:%M:%S"), "limit": a.limit, "karok": karok,
                                   "temperature": res["temperature"], "fajlok": res["fajlok"]})
    res["ido_s"] = round(time.time() - t0)
    er = EXP / a.eredmeny
    er.mkdir(parents=True, exist_ok=True)
    write_json(er / "f3r.json", res)
    (er / "f3r.md").write_text(lap(res), encoding="utf-8")
    print((er / "f3r.md").read_text())


# --- pontozás (F5 és 07B): a mentett fejek egy szeleten, mindkét kerettel ----------------------------------------------

PECSET07 = EXP / "cache/k07/pecset"
ITEMS07 = EXP / "kor07/adat/f2/items"


def meta07() -> dict:
    """A 07 friss itemjei a 06 `friss06._META` alakjában (a 06 B1-útjának `K.meta`-ja a 07 szeletein)."""
    out = {}
    for fam in CSALADOK:
        for it in K.jsonl(ITEMS07 / f"{fam}.jsonl"):
            out[it["id"]] = {"group_id": it["group_id"], "family": fam, "split": it["split"], "state": it["content_state"],
                             "gold_set": {it["gold"]} if it["gold"] is not None else set(),
                             "ketertelmu": bool(it.get("ketertelmu")), "lang": it["lang"]}
    return out


def szelet_forras(nev: str) -> tuple[str, str, str, Path, Path]:
    """`<család>:<CAL|TESZT>` (07 friss, csak a pecsét kapuja után) vagy `k06:<család>:<T500|CAL|TESZT>` (06, nyitott):
    (család, szelet, a négyállapotú könyvtárak előtagja, négyállapotú gyökér, 06-keretű gyökér)."""
    p = nev.split(":")
    if p[0] == "k06":
        fam, sz = p[1], p[2]
        return fam, sz, f"k06_{fam}_{sz}", JELL07, F6.root("jellemzok", f"{fam}:{sz}")
    fam, sz = p
    if fam not in CSALADOK or sz not in ("CAL", "TESZT"):
        raise SystemExit(f"ismeretlen szelet: {nev}")
    import pecset07  # noqa: PLC0415

    pecset07.kapu(PECSET07)
    return fam, sz, f"{fam}_{sz}", PECSET07 / "jellemzok", PECSET07 / "jellemzok2"


def fold_atlag(load, paths: list[Path], rs: list[dict]) -> list[float]:
    acc = np.zeros(len(rs))
    for p in paths:
        m, ms, _ = load(p)()
        acc += np.array(B.logits(m, rs, ms)) / len(paths)
    return acc.tolist()


def pontoz(a) -> None:
    fejek = EXP / a.fejek
    temps = json.loads((fejek / "temperature.json").read_text())
    st = fej05.Stats.from_state(json.loads((FEJ_H / "fej.json").read_text())["stats"])
    fam, sz, prefix, root4, root2 = szelet_forras(a.szelet)
    F6.telepit()
    if not a.szelet.startswith("k06:"):
        K.meta = meta07
    K._root = lambda kind, szelet: root2  # type: ignore[assignment]
    out = {"szelet": a.szelet, "fejek": a.fejek, "temperature": temps}
    # négyállapotú keret: B1-4S, B1-4R0, B1-4R, B1-4LR
    ids, rs, info = set4(prefix, temps["B1-4"], st, root4)
    p4 = {"B1-4S": [info[i]["q"] for i in ids]}
    for s in SEEDS:
        p4[f"B1-4R0|{s}"] = fold_atlag(load_b14, [fejek / f"B1-4R0_s{s}.pt"], rs)
        p4[f"B1-4R|{s}"] = fold_atlag(load_b14, [fejek / fam / f"B1-4R_s{s}_f{f}.pt" for f in range(5)], rs)
    ill = json.loads((fejek / fam / "B1-4LR.json").read_text())
    p4["B1-4LR"] = lr_pontszam(ill, np.array([lr4_features(info[i]) for i in ids])).tolist()
    out["keret4"] = {"ids": ids, "dontes": {i: info[i] for i in ids}, "pontszam": p4}
    print(f"{a.szelet}: négyállapotú keret {len(ids)} item, {len(p4)} pontszámsor", flush=True)
    # 06-os keret: B1-S, B1-R0, B1-R, B1-LR (a 06 útja, a mentett fold-modellekkel)
    ids2, rs2, info2 = B.b1_set(f"{fam}:{sz}", temps["B1"], st)
    p2 = {"B1-S": [info2[i]["q"] for i in ids2]}
    for s in SEEDS:
        p2[f"B1-R0|{s}"] = fold_atlag(B.load_b1, [B1REL06 / f"rel_s{s}.pt"], rs2)
        p2[f"B1-R|{s}"] = fold_atlag(B.load_b1, [fejek / fam / f"B1-R_s{s}_f{f}.pt" for f in range(5)], rs2)
    ill2 = json.loads((fejek / fam / "B1-LR.json").read_text())
    p2["B1-LR"] = lr_pontszam(ill2, np.array([B.lr_features(info2[i]) for i in ids2])).tolist()
    out["keret2"] = {"ids": ids2, "dontes": {i: info2[i] for i in ids2}, "pontszam": p2}
    print(f"{a.szelet}: 06-os keret {len(ids2)} item, {len(p2)} pontszámsor", flush=True)
    if a.ellenoriz:  # k06 TESZT: a pontozó út a tanítás közben mért pontszámokat és az F0 reprodukciót adja vissza
        f3r = json.loads((EXP / a.ellenoriz).read_text())
        y4 = np.array([info[i]["helyes"] for i in ids], bool)
        out["ellenorzes"] = {f"B1-4R|{s}": {"aurc_pontoz": B4.aurc(np.array(p4[f"B1-4R|{s}"]), y4),
                                            "aurc_tanitas": f3r["csaladok"][fam]["B1-4R"]["seedek"][str(s)]["proba_06_TESZT_aurc_B1-4R"]}
                             for s in SEEDS}
        rp = F0_REPRO / fam / "f1.json"
        if rp.exists() and sz == "TESZT":
            regi = json.loads(rp.read_text())["pontszam"]
            out["ellenorzes"]["B1-R_repro_max_elteres"] = {s: float(np.max(np.abs(np.array(regi[f"B1-R|None|0|{s}|{fam}:TESZT"]) - np.array(p2[f"B1-R|{s}"]))))
                                                           for s in SEEDS}
        print(json.dumps(out["ellenorzes"], indent=1), flush=True)
    o = EXP / a.out
    o.mkdir(parents=True, exist_ok=True)
    (o / f"{a.szelet.replace(':', '_')}.json").write_text(json.dumps(out) + "\n", encoding="utf-8")
    print(f"→ {o.relative_to(EXP) / (a.szelet.replace(':', '_') + '.json')}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pontoz")
    p.add_argument("--szelet", required=True, help="<család>:<CAL|TESZT> (pecsét alatt) vagy k06:<család>:<T500|CAL|TESZT>")
    p.add_argument("--fejek", default="cache/k07/fejek")
    p.add_argument("--out", required=True)
    p.add_argument("--ellenoriz", help="az F3R f3r.json-ja: a pontozó út összevetése a tanítás közben mért pontszámokkal (k06 TESZT)")
    p.add_argument("--szalak", type=int)
    t = sub.add_parser("tanit")
    t.add_argument("--out", default="cache/k07/fejek")
    t.add_argument("--eredmeny", default="kor07/eredmenyek/F3R")
    t.add_argument("--csak", help="karok vesszővel: " + ",".join(KAROK))
    t.add_argument("--limit", type=int, help="füstteszt: ennyi item a tanítómintákból (az eredmény nem érvényes)")
    t.add_argument("--szalak", type=int, help="torch CPU-szálak (más GPU-munka mellett korlátozva)")
    a = ap.parse_args()
    if a.szalak:
        torch.set_num_threads(a.szalak)
    {"tanit": tanit, "pontoz": pontoz}[a.cmd](a)


if __name__ == "__main__":
    main()
