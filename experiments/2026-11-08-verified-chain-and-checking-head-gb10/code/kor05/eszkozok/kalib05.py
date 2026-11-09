"""05-ös kör — kalibráció és döntési szabály (05-runbook 7.; forrásterv 9.), minden karra közös döntési táblával.

Karok és nyers pontszámuk:
  B0      HF perm-0, a címkékre szűkített softmax temperature-rel; X → NONE, opció → SELECT
  B1      HF L1★: a négy permutáció (0 + b1) temperature-rel számolt opció-eloszlásának átlaga (az elemzes.py
          `perm_avg` karja); X → NONE
  JEV-a   ugyanígy a JEV-35B kiolvasásából (`jev05.py`), az „egyik sem” betűje az X; JEV-b: X nélkül (csak SELECT)
  C/H/A   a tartalmi fej javaslata (SELECT / NONE / DEFER) és a megbízhatósági fej logitja (`megbizhatosag05.py dont`),
          seedenként; Platt-kalibráció
Illesztés a D_cal_prob-on: a címkekaroknál a temperature (a gold címke NLL-je a perm-0 sorokon, az elemzes.fit_temperature
módszere), a fejeknél a Platt (a, b) a szigorú helyességre és — leíróként — a tartalmi softmax temperature-je.
A τ a D_cal_policy-n (7. pont): alapesetenként (group_id) egy, hash-sel rögzített item, a kanonikus promptváltozattal; a
legkisebb küszöb, amelynél a vállalt (SELECT + NONE) döntések pontosságának egyoldali 95%-os Clopper–Pearson alsó
korlátja ≥ 0,95, és legalább 200 döntés elfogadott; ha nincs ilyen, „nincs igazolt munkapont”.
Helyesség: szigorú (elsődleges javaslat; a NONE csak NO_MATCH-en helyes) és enyhe (leíró; a NONE minden nem-MATCH
állapoton helyes). A kétértelmű itemek nem kalibrálnak és nem pontozódnak (a 03 szabálya).

  python3 kor05/eszkozok/kalib05.py --kar B0 --kar B1 --kar H --out kor05/eredmenyek/F3/kalib/kalib.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import beta

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "eszkozok")]
from allapot05 import content_state, gold_set, rows as item_rows  # noqa: E402

JELL = EXP / "cache/k05/jellemzok"
JEV = EXP / "cache/k05/jev"
DONT = EXP / "cache/k05/dontesek"
TMETA = EXP / "cache/k05/tmeta"
ITEM_FILES = ("kor03/adat/f3/mvp_train_v2.jsonl", "kor03/adat/f2/items_val.jsonl", "kor03/adat/f2/items_eval.jsonl")
TARGET, MIN_ACC, TAU_SEED = 0.95, 200, "k05-tau:20261029"
SEEDS = (17, 42, 73)
LABEL_ARMS = ("B0", "B1", "JEV-a", "JEV-b", "L1v", "G3")
# a 03 vLLM-kiolvasásai (B2 és a H6 referenciái; más motor, a HO-rétegeken a 03-ban már megnyitva, ezért pecsét nélkül)
VLLM03 = {"L1v": ["kor03/eredmenyek/F2/qwen_val.jsonl", "kor03/eredmenyek/F2/qwen_eval.jsonl"],
          **{f"G3:{n}": [f"kor03/eredmenyek/F4/k03v2_g3_s{n}/vllm_eval.jsonl"] for n in (1, 2, 3)}}
LABEL_SEEDS = {"G3": (1, 2, 3)}  # a G3 s1–s3 a seedjei; a többi címkekar egyetlen kiolvasás
HEAD_ARMS = ("C", "H", "A", "HX")
KSTAR = "H"  # v1a: a D_dev makro tartalmi NLL-je szerint (05-runbook 3. pont)
T_ARMS = ("B1-T", f"{KSTAR}-T-kal", f"{KSTAR}-T-meta")  # 05-runbook 3.3: a τ (és a Platt, ill. a fej) a célcsalád-mintán
CEL = {"teszt:ho-termek": "cel:ho-termek", "teszt:ho-routing": "cel:ho-routing", "teszt:ho-routing-hu": "cel:ho-routing",
       "teszt:ho-uj": "cel:ho-uj", "leiro:t-hu-maradek": "cel:ho-routing"}


def jsonl(p: Path):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


_META: dict | None = None


def meta() -> dict:
    """id → group_id, család, tartalmi állapot, gold_set, kétértelműség."""
    global _META
    if _META is None:
        _META = {}
        for f in ITEM_FILES:
            for it in item_rows(EXP / f):
                _META[it["id"]] = {"group_id": it["group_id"], "family": it["family"], "split": it["split"],
                                   "state": content_state(it), "gold_set": set(gold_set(it)),
                                   "ketertelmu": bool(it.get("ketertelmu"))}
    return _META


def cp_lower(k: int, n: int) -> float:
    return float(beta.ppf(0.05, k, n - k + 1)) if k > 0 else 0.0


# --- döntési sorok -----------------------------------------------------------------------------------------------------

KITARTOTT = ("teszt:", "cel:", "leiro:")


def sealed(szelet: str) -> bool:
    return szelet.startswith(KITARTOTT)


def _root(kind: str, szelet: str) -> Path:
    """A kitartott szeletek a pecsét alól jönnek, a v1a rögzítése nélkül a kapu megállítja (pecset05.kapu)."""
    base = {"jellemzok": JELL, "jev": JEV, "dontesek": DONT, "tmeta": TMETA}[kind]
    if not sealed(szelet):
        return base
    from pecset05 import PECSET, kapu  # noqa: PLC0415

    root = PECSET / kind
    kapu(root)
    return root


_VLLM_CACHE: dict = {}


def vllm03_rows(key: str) -> dict[str, list[dict]]:
    """A 03 egy vLLM-kiolvasása id → sorok; csak a kiolvasáshoz kellő mezők, egyszer beolvasva."""
    if key not in _VLLM_CACHE:
        by = defaultdict(list)
        for f in VLLM03[key]:
            for r in jsonl(EXP / f):
                by[r["id"]].append({k: r[k] for k in ("id", "perm", "order", "labels", "probs")})
        _VLLM_CACHE[key] = by
    return _VLLM_CACHE[key]


def slice_ids(szelet: str) -> list[str]:
    return json.loads((EXP / "kor05/adat/szeletek05.json").read_text())["szeletek"][szelet]["ids"]


def label_rows(arm: str, szelet: str, root: Path | None = None, seed: int | None = None) -> dict[str, list[dict]]:
    """id → a kiolvasott sorok (perm szerint), a címkekarokhoz."""
    by = defaultdict(list)
    if arm in ("L1v", "G3"):
        src = vllm03_rows("L1v" if arm == "L1v" else f"G3:{seed}")
        return {i: src[i] for i in slice_ids(szelet) if i in src}
    if arm in ("B0", "B1"):
        root = root or _root("jellemzok", szelet)
        mods = ["kanonikus"] + (["b1"] if arm == "B1" else [])
        for mod in mods:
            for f in sorted((root / f"{szelet.replace(':', '_')}__{mod}").glob("sorok_*.jsonl")):
                for r in jsonl(f):
                    by[r["id"]].append(r)
    else:
        root = root or _root("jev", szelet)
        for r in jsonl(root / f"{szelet.replace(':', '_')}.jsonl"):
            if r["arm"] == arm:
                by[r["id"]].append(r)
    if arm == "B0":
        by = {i: [r for r in rs if r["perm"] == 0] for i, rs in by.items()}
    return by


def option_scores(r: dict, temp: float) -> dict:
    """Opció-id → szűkített valószínűség (az X kulcsa None); a JEV-soroknál a log-valószínűség a bias-szal."""
    # a 03 vLLM-soraiban csak a szűkített eloszlás van: log p = logprob − konstans, a softmax(·/T) ettől független
    lp = r.get("label_logprobs") or {lab: math.log(max(v, 1e-30)) for lab, v in r["probs"].items()}
    bias = r.get("bias") or {}
    z = {lab: (v + bias.get(lab, 0.0)) / temp for lab, v in lp.items()}
    m = max(z.values())
    e = {lab: math.exp(v - m) for lab, v in z.items()}
    s = sum(e.values())
    return {(None if lab == "X" else r["order"][r["labels"].index(lab)]): e[lab] / s for lab in lp}


def fit_temperature(by: dict[str, list[dict]]) -> float:
    M = meta()
    rows0 = [r for rs in by.values() for r in rs if r["perm"] == 0 and not M[r["id"]]["ketertelmu"]]

    def nll(logt: float) -> float:
        t = math.exp(logt)
        tot = 0.0
        for r in rows0:
            sc = option_scores(r, t)
            m = M[r["id"]]
            g = sum(v for k, v in sc.items() if (k is None and m["state"] != "MATCH") or (k is not None and k in m["gold_set"]))
            if g <= 0.0:
                continue  # a gold nem érhető el a kar kimenetei közt (JEV-b az X-gold itemen): a T-tól független tag
            tot -= math.log(max(1e-12, g))
        return tot
    return float(math.exp(minimize_scalar(nll, bounds=(-3, 4), method="bounded").x))


def decide_label(rs: list[dict], temp: float) -> tuple[str, str | None, float]:
    acc = defaultdict(float)
    for r in rs:
        for k, v in option_scores(r, temp).items():
            acc[k] += v / len(rs)
    pred = max(acc, key=acc.get)
    return ("NONE" if pred is None else "SELECT"), pred, acc[pred]


def correctness(m: dict, kind: str, cand: str | None) -> tuple[bool | None, bool | None]:
    if kind == "SELECT":
        ok = cand in m["gold_set"]
        return ok, ok
    if kind == "NONE":
        return m["state"] == "NO_MATCH", m["state"] != "MATCH"
    return None, None


def label_table(arm: str, szelet: str, temp: float, root: Path | None = None, seed: int | None = None) -> list[dict]:
    M = meta()
    out = []
    for iid, rs in label_rows(arm, szelet, root, seed).items():
        if len(rs) != len({r["perm"] for r in rs}):
            raise SystemExit(f"{arm}/{szelet}: {iid} ismétlődő permutációval")
        if arm in ("B1", "JEV-a", "JEV-b", "L1v", "G3") and len({r["perm"] for r in rs}) != 4:
            raise SystemExit(f"{arm}/{szelet}: {iid} permutációi hiányosak ({sorted(r['perm'] for r in rs)})")
        kind, cand, q = decide_label(rs, temp)
        m = M[iid]
        ok, ok_l = correctness(m, kind, cand)
        out.append({"id": iid, "group_id": m["group_id"], "family": m["family"], "state": m["state"],
                    "ketertelmu": m["ketertelmu"], "javaslat": kind, "jelolt": cand, "q": q, "nyers": q,
                    "helyes": ok, "helyes_enyhe": ok_l})
    return out


def head_rows(arm: str, szelet: str, seed: int, root: Path | None = None) -> list[dict]:
    return list(jsonl((root or _root("dontesek", szelet)) / arm / szelet.replace(":", "_") / f"s{seed}.jsonl"))


def platt_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    def nll(w):
        z = w[0] * x + w[1]
        return float(np.sum(np.logaddexp(0, z) - y * z))
    r = minimize(nll, np.array([1.0, 0.0]), method="BFGS")
    return float(r.x[0]), float(r.x[1])


def head_table(arm: str, szelet: str, seed: int, platt: tuple[float, float], root: Path | None = None) -> list[dict]:
    return rows_table(head_rows(arm, szelet, seed, root), platt)


def rows_table(rows: list[dict], platt: tuple[float, float]) -> list[dict]:
    a, b = platt
    out = []
    for r in rows:
        q = 1 / (1 + math.exp(-(a * r["rel_logit"] + b))) if r["rel_logit"] is not None else None
        out.append({"id": r["id"], "group_id": r["group_id"], "family": meta()[r["id"]]["family"], "state": r["state"],
                    "ketertelmu": r["ketertelmu"], "javaslat": r["javaslat"], "jelolt": r["jelolt"],
                    "defer_ok": r["defer_ok"], "q": q, "nyers": r["rel_logit"], "helyes": r["helyes"],
                    "helyes_enyhe": r["helyes_enyhe"]})
    return out


def content_temperature(rows: list[dict]) -> dict:
    """Leíró: a tartalmi softmax temperature-je a gold-halmaz NLL-jén (a log-softmax / T újranormálva)."""
    data = [(np.array(r["logp"]), np.array([o in set(r["gold"]) for o in r["out_ids"]])) for r in rows if not r["ketertelmu"]]

    def nll(t: float) -> float:
        tot = 0.0
        for lp, g in data:
            z = lp / t
            z = z - np.logaddexp.reduce(z)
            tot -= np.logaddexp.reduce(z[g])
        return tot / len(data)
    t = float(minimize_scalar(nll, bounds=(0.05, 20), method="bounded").x)
    return {"T": t, "nll_elotte": nll(1.0), "nll_utana": nll(t)}


def tmeta_rows(arm: str, cel: str, part: str, seed: int, root: Path | None = None) -> list[dict]:
    """A T-meta sorai: part = "minta" (cross-fittelt) vagy a teszt szeletneve (az öt fold-modell átlaga)."""
    base = (root or _root("tmeta", cel)) / arm / cel.replace(":", "_")
    d = base / "minta" if part == "minta" else base / "teszt" / part.replace(":", "_")
    return list(jsonl(d / f"s{seed}.jsonl"))


def platt_on(rows: list[dict]) -> tuple[float, float]:
    cal = [r for r in rows if r["javaslat"] != "DEFER" and not r["ketertelmu"]]
    return platt_fit(np.array([r["rel_logit"] for r in cal]), np.array([float(r["helyes"]) for r in cal]))


def t_tables(arm: str, layer: str, kal: dict, cel: str | None = None) -> tuple[list[list[dict]], list[list[dict]], list[dict]]:
    """Egy T-kar (B1-T, K*-T-kal, K*-T-meta) τ-táblái a célcsalád-mintán és teszttáblái a rétegen, seedenként, az
    illesztett paraméterekkel. A temperature (B1-T) a D_cal_prob-é; a Platt a T-kal-nál és a T-meta-nál a mintán."""
    cel = cel or CEL[layer]
    if arm == "B1-T":
        T = kal["B1"]["temperature"]
        return [label_table("B1", cel, T)], [label_table("B1", layer, T)], [{"temperature": T, "cel": cel}]
    taus, tests, prm = [], [], []
    for s in SEEDS:
        if arm == f"{KSTAR}-T-kal":
            minta, teszt = head_rows(KSTAR, cel, s), head_rows(KSTAR, layer, s)
        elif arm == f"{KSTAR}-T-meta":
            minta, teszt = tmeta_rows(KSTAR, cel, "minta", s), tmeta_rows(KSTAR, cel, layer, s)
        else:
            raise ValueError(arm)
        pl = platt_on(minta)
        taus.append(rows_table(minta, pl))
        tests.append(rows_table(teszt, pl))
        prm.append({"seed": s, "platt": {"a": pl[0], "b": pl[1]}, "cel": cel})
    return taus, tests, prm


# --- τ -----------------------------------------------------------------------------------------------------------------

def one_per_group(table: list[dict]) -> list[dict]:
    best = {}
    for r in table:
        if r["ketertelmu"]:
            continue
        h = hashlib.sha256(f"{TAU_SEED}|{r['id']}".encode()).hexdigest()
        if r["group_id"] not in best or h < best[r["group_id"]][0]:
            best[r["group_id"]] = (h, r)
    return [r for _, r in best.values()]


def choose_tau(table: list[dict], key: str = "helyes") -> dict:
    """A legkisebb küszöb (a legnagyobb lefedettség), amelynél CP_alsó(k, n) ≥ 0,95 és n ≥ 200."""
    t = one_per_group(table)
    acc = sorted((r for r in t if r["javaslat"] in ("SELECT", "NONE")), key=lambda r: -r["q"])
    best = None
    k = 0
    for n, r in enumerate(acc, 1):
        k += bool(r[key])
        if n < len(acc) and acc[n]["q"] == r["q"]:
            continue  # holtversenyen belül nem vágunk
        if n >= MIN_ACC and cp_lower(k, n) >= TARGET:
            best = (r["q"], n, k)
    out = {"alapeset": len(t), "javaslat_select_none": len(acc)}
    if best is None:
        return out | {"tau": None, "munkapont": "nincs igazolt munkapont", "lefedettseg": 0.0}
    tau, n, kk = best
    return out | {"tau": tau, "elfogadott": n, "helyes": kk, "cp_also": cp_lower(kk, n), "pontossag": kk / n,
                  "lefedettseg": n / len(t)}


# --- fő ----------------------------------------------------------------------------------------------------------------

def kalibral_label(arm: str) -> dict:
    def one(seed):
        temp = fit_temperature(label_rows(arm, "D_cal_prob", seed=seed))
        tab = label_table(arm, "D_cal_policy", temp, seed=seed)
        return {"temperature": temp, "tau_szigoru": choose_tau(tab, "helyes"), "tau_enyhe": choose_tau(tab, "helyes_enyhe")}
    if arm in LABEL_SEEDS:
        return {str(s): one(s) for s in LABEL_SEEDS[arm]}
    return one(None)


def kalibral_head(arm: str) -> dict:
    out = {}
    for s in SEEDS:
        cal = [r for r in head_rows(arm, "D_cal_prob", s) if r["javaslat"] != "DEFER" and not r["ketertelmu"]]
        x = np.array([r["rel_logit"] for r in cal])
        y = np.array([float(r["helyes"]) for r in cal])
        pl = platt_fit(x, y)
        tab = head_table(arm, "D_cal_policy", s, pl)
        out[str(s)] = {"platt": {"a": pl[0], "b": pl[1]},
                       "tartalmi_temperature": content_temperature(head_rows(arm, "D_cal_prob", s)),
                       "tau_szigoru": choose_tau(tab, "helyes"), "tau_enyhe": choose_tau(tab, "helyes_enyhe")}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kar", action="append", required=True, choices=[*LABEL_ARMS, *HEAD_ARMS])
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default="", help="a cache/k05 helye, ha nem a kísérlet alatt van (a laptopon)")
    a = ap.parse_args()
    if a.cache:
        global JELL, JEV, DONT
        c = Path(a.cache)
        JELL, JEV, DONT = c / "jellemzok", c / "jev", c / "dontesek"
    out = Path(a.out)
    res = json.loads(out.read_text()) if out.exists() else {}
    for arm in a.kar:
        res[arm] = kalibral_label(arm) if arm in LABEL_ARMS else kalibral_head(arm)
        print(arm, json.dumps(res[arm], ensure_ascii=False)[:600], flush=True)
    res["_szabaly"] = {"cel": TARGET, "min_elfogadott": MIN_ACC, "tau_seed": TAU_SEED,
                       "tau_szelet": "D_cal_policy (alapesetenként egy item, perm 0)", "illesztes": "D_cal_prob"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
