"""F4 — a H3(d) bukásának utólagos, leíró mélyfúrása (nem előre rögzített; Dani kérése, 2026-10-07).

A kérdés: a ~6%-os top-címke-eltérés (LoRA-t nem kérő kérések egy `--enable-lora`-s és egy LoRA nélküli példányon)
mérési hiba-e, a LoRA „szivárgása”-e, vagy a kiszolgálás numerikájának változása. A H3-részhalmazon (1000 item,
perm 0) összeveti:
  * a friss példányokat páronként: top-címke-billenés, bájtazonos sorok; a numerika-módok = azon példányok
    csoportjai, amelyek páronként ≤ 1% billenéssel egyeznek (összefüggő komponensek);
  * a fő F4-példány L0 / L0′ sorait (ugyanazon a példányon az adapterek be- és kitöltése előtt és után) és a HF-L0-t
    mint független referenciát;
  * a rendszeres eltolódást: módonként az átlagos szűkített entrópia, p(top), és az átlagos Δ log p(A) a LoRA nélküli
    módhoz képest (az A pozíció a legérzékenyebb);
  * a billenő itemek top-2 margóját (szűkített valószínűség, LoRA nélküli mód);
  * a H1 módérzékenységét: a fő példány val-ján illesztett temperature és τ@95 (perm 0, `temp` kar — az L1★
    permutáció-átlaga itt nem számolható, mert a H3-példányok csak a perm 0-t olvasták) minden példány soraira;
  * a MoE FP8-backendet a példány-logokból (`Using … Fp8 MoE backend`).

  LDH_EXP=$PWD python3 eszkozok/f4_h3_modok.py --out eredmenyek/F4/h3_modok.json
"""

from __future__ import annotations

import argparse
import itertools
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import _p, arm_predictions, by_item, choose_tau, fit_temperature, load_meta, metrics  # noqa: E402

SAME_MODE = 0.01  # páronkénti top-címke-billenés, amely alatt két példány egy módba tartozik


def restricted(r: dict) -> dict[str, float]:
    lp = r["label_logprobs"]
    m = max(lp.values())
    e = {k: np.exp(v - m) for k, v in lp.items()}
    s = sum(e.values())
    return {k: v / s for k, v in e.items()}


def top(r: dict) -> str:
    return max(r["label_logprobs"], key=r["label_logprobs"].get)


def keyed(path: Path, ids: set | None = None) -> dict:
    return {(r["id"], r["perm"]): r for r in read_jsonl(path) if r["perm"] == 0 and (ids is None or r["id"] in ids)}


def modes(names: list[str], runs: dict, keys: list) -> list[list[str]]:
    parent = {n: n for n in names}

    def find(n):
        while parent[n] != n:
            n = parent[n]
        return n
    for a, b in itertools.combinations(names, 2):
        if np.mean([top(runs[a][k]) != top(runs[b][k]) for k in keys]) <= SAME_MODE:
            parent[find(a)] = find(b)
    groups = defaultdict(list)
    for n in names:
        groups[find(n)].append(n)
    return sorted(groups.values())


def backends(root: Path) -> dict:
    """A MoE-backend a megmaradt példány-logokból. A H3 tíz példányának logja egymást írta felül (`subject_stop`),
    csak az utolsóé (nolora_k5) maradt meg; a LoRA-s H3-példányokra a backend a többi LoRA-s indításból következtetés."""
    out = defaultdict(lambda: defaultdict(list))
    for f in sorted(root.rglob("ldh-subject*.log")):
        txt = f.read_text(errors="replace")
        lora = "'enable_lora': True" in txt
        for b in set(re.findall(r"Using (\w+) Fp8 MoE backend", txt)):
            out["enable_lora" if lora else "lora_nelkul"][b].append(str(f.relative_to(root)))
    return {k: {b: {"db": len(v), "logok": v} for b, v in d.items()} for k, d in out.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="eredmenyek/F4")
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    D, P = _p(args.dir), _p(args.dir) / "h3"
    meta = load_meta(_p(args.items))

    inst = {f"lora_k{k}": keyed(P / f"lora_k{k}_l0.jsonl") for k in range(1, 6)}
    inst |= {f"nolora_k{k}": keyed(P / f"nolora_k{k}_l0.jsonl") for k in range(1, 6)}
    keys = sorted(inst["nolora_k1"])
    ids = {k[0] for k in keys}
    ref = {"fo_L0": keyed(D / "vllm" / "l0_test.jsonl", ids), "fo_L0vesszo": keyed(D / "vllm" / "l0r_test.jsonl", ids),
           "HF_L0": keyed(D / "hf" / "l0_test.jsonl", ids)}
    runs = inst | ref
    names = list(runs)
    res: dict = {"n": len(keys), "modkuszob_billenes": SAME_MODE}

    res["billenes_db"] = {a: {b: int(sum(top(runs[a][k]) != top(runs[b][k]) for k in keys)) for b in names} for a in names}
    res["bajtazonos_db"] = {a: {b: int(sum(runs[a][k]["label_logprobs"] == runs[b][k]["label_logprobs"] for k in keys))
                                for b in names} for a in names}
    res["pontossag"] = {n: float(np.mean([runs[n][k]["pred"] == runs[n][k]["gold_label"] for k in keys])) for n in names}
    groups = modes(list(inst) + ["fo_L0"], runs, keys)
    res["modok"] = groups

    # pontosság a pontozott (nem kétértelmű) itemeken: módonként a LoRA nélküli módhoz képest, cikk-klaszteres
    # bootstrap CI-vel; a billenések iránya módonként (a módon belüli példányok nem független ismétlések)
    scored = [k for k in keys if not meta[k[0]].get("ketertelmu")]
    ok = {n: np.array([runs[n][k]["pred"] == runs[n][k]["gold_label"] for k in scored], dtype=float) for n in names}
    cl = defaultdict(list)
    for j, k in enumerate(scored):
        cl[meta[k[0]].get("article")].append(j)
    cls = [np.array(v) for v in cl.values()]
    rng = np.random.default_rng(0)
    nolora_rep = next(g for g in groups if "nolora_k1" in g)[0]
    per_mode = {}
    for g in groups:
        rep = g[0]
        if rep == nolora_rep:
            continue
        d = ok[rep] - ok[nolora_rep]
        boots = [d[np.concatenate([cls[c] for c in rng.integers(0, len(cls), len(cls))])].mean() for _ in range(2000)]
        flip = [j for j, k in enumerate(scored) if runs[rep][k]["pred"] != runs[nolora_rep][k]["pred"]]
        jo = sum(ok[rep][j] == 1 for j in flip)
        rossz = sum(ok[nolora_rep][j] == 1 for j in flip)
        per_mode[rep] = {"tagok": g, "delta_pontossag": float(d.mean()), "ci95": [float(np.percentile(boots, 2.5)),
                                                                                  float(np.percentile(boots, 97.5))],
                         "billenes_jora": int(jo), "billenes_rosszra": int(rossz),
                         "elojelproba_p": float(binomtest(int(jo), int(jo + rossz)).pvalue) if jo + rossz else None}
    res["pontossag_pontozott"] = {"n": len(scored), "lora_nelkuli_mod": float(ok[nolora_rep].mean()),
                                  "modonkent_a_lora_nelkulihez": per_mode}

    base = next(g for g in groups if "nolora_k1" in g)[0]
    lora_modes = [g[0] for g in groups if not any(n.startswith("nolora") for n in g)]
    shift = {}
    for g in groups:
        rep = g[0]
        shift[rep] = {
            "tagok": g,
            "entropia": float(np.mean([-sum(p * np.log(p + 1e-12) for p in restricted(runs[rep][k]).values()) for k in keys])),
            "p_top": float(np.mean([max(restricted(runs[rep][k]).values()) for k in keys])),
            "dlogpA_a_lora_nelkulihez": float(np.mean([np.log(restricted(runs[rep][k])["A"]) -
                                                       np.log(restricted(runs[base][k])["A"]) for k in keys])),
            "billenes_HF_hez": res["billenes_db"][rep]["HF_L0"]}
    shift["HF_L0"] = {"entropia": float(np.mean([-sum(p * np.log(p + 1e-12) for p in restricted(runs["HF_L0"][k]).values())
                                                 for k in keys])),
                      "p_top": float(np.mean([max(restricted(runs["HF_L0"][k]).values()) for k in keys])),
                      "dlogpA_a_lora_nelkulihez": float(np.mean([np.log(restricted(runs["HF_L0"][k])["A"]) -
                                                                 np.log(restricted(runs[base][k])["A"]) for k in keys]))}
    res["eltolodas"] = shift

    mg = {k: (lambda p: p[0] - p[1])(sorted(restricted(runs[base][k]).values(), reverse=True)) for k in keys}
    flipped = [k for k in keys if any(top(runs[m][k]) != top(runs[base][k]) for m in lora_modes)]
    res["margo"] = {"lora_nelkuli_mod_aranya_margo_alatt": {str(t): float(np.mean([mg[k] < t for k in keys]))
                                                             for t in (0.05, 0.1, 0.2)},
                    "billeno_itemek": len(flipped), "billeno_median": float(np.median([mg[k] for k in flipped])),
                    "billeno_max": float(max(mg[k] for k in flipped)),
                    "nem_billeno_median": float(np.median([mg[k] for k in keys if k not in set(flipped)]))}

    # H1 módérzékenysége: a fő példány val-ján rögzített temperature és τ@95, perm 0, `temp` kar
    v0 = [r for r in read_jsonl(D / "vllm" / "l0_val.jsonl") if r["perm"] == 0]
    v3 = [r for r in read_jsonl(D / "vllm" / "l3_s1_val.jsonl") if r["perm"] == 0]
    t0, t3 = fit_temperature(v0, meta), fit_temperature(v3, meta)
    tau0 = choose_tau(arm_predictions("temp", by_item(v0), meta, {"temp": t0}), meta, sorted({r["id"] for r in v0}), .95)
    tau3 = choose_tau(arm_predictions("temp", by_item(v3), meta, {"temp": t3}), meta, sorted({r["id"] for r in v3}), .95)
    sid = sorted(ids)

    def m(rows: dict, temp: float, tau: float) -> dict:
        x = metrics(arm_predictions("temp", by_item(list(rows.values())), meta, {"temp": temp}), meta, sid, tau)
        return {"lef95": x["besorolasi_lefedettseg"], "precizitas": x["besorolasi_precizitas"], "aurc": x["aurc"]}
    h1 = {"temperature": {"L0": t0, "L3_s1": t3}, "tau95": {"L0": tau0, "L3_s1": tau3}, "peldanyok": {}}
    pairs = [("fo", ref["fo_L0"], keyed(D / "vllm" / "l3_s1_test.jsonl", ids))]
    pairs += [(f"lora_k{k}", inst[f"lora_k{k}"], keyed(P / f"lora_k{k}_l3.jsonl")) for k in range(1, 6)]
    pairs += [(f"nolora_k{k}", inst[f"nolora_k{k}"], None) for k in range(1, 6)]
    for name, r0, r3 in pairs:
        row = {"L0": m(r0, t0, tau0)}
        if r3:
            row["L3_s1"] = m(r3, t3, tau3)
            row["delta_lef95"] = row["L3_s1"]["lef95"] - row["L0"]["lef95"]
        h1["peldanyok"][name] = row
    res["H1_modérzékenység"] = h1
    res["moe_backend_logokbol"] = backends(_p("eredmenyek"))
    write_json(_p(args.out), res)
    print(f"módok: {groups}")
    print(f"backend: {res['moe_backend_logokbol']}")
    for name, row in h1["peldanyok"].items():
        print(f"{name:11s} L0 {row['L0']['lef95']:.3f}" + (f"  L3 {row['L3_s1']['lef95']:.3f}  Δ {row['delta_lef95']:+.3f}"
                                                          if "L3_s1" in row else ""))


if __name__ == "__main__":
    main()
