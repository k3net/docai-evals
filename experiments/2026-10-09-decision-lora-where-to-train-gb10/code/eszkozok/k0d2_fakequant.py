"""K0d-2 — fake-quant változatok HF↔vLLM egyezése a pilot-itemeken (egy modellbetöltéssel).

A K0d 94,0%-ot adott (90–95%-os sáv → az F3-ban fake-quant kar). Ez a mérés azt dönti el,
melyik fake-quant változat közelíti legjobban a vLLM-et; az lesz az F3 fake-quant karja.
A választás a pilot-itemeken történik (eldobható adat), a val/teszt érintetlen.

A modell eager expertekkel töltődik (a fake-quant expert-útja eager), ezért:
  1. kontroll: az első 50 item a hookok felrakása előtt és után (`none` mód) bájtra egyezik
     — kikapcsolva a fake-quant valóban semmit nem csinál;
  2. `eager` alapvonal (fake-quant nélkül) a teljes pilot_eval-on: vs vLLM, és vs a K0d
     grouped_mm-es HF-sorai (az implementációváltás saját hatása);
  3. `vllm`, `fp32`, `pow2` módok a teljes pilot_eval-on, mindegyik vs vLLM.

Példa:
  python3 eszkozok/k0d2_fakequant.py --out eredmenyek/F0/k0d2
"""

from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fakequant  # noqa: E402
from common import BF16_BASE, EXP, PromptTokenizer, read_jsonl, write_json, write_jsonl  # noqa: E402
from hf_kiolvaso import load_model, readout  # noqa: E402
from osszevet import compare  # noqa: E402

SAVOK = [(0, 0.1), (0.1, 0.3), (0.3, 0.6), (0.6, 1.01)]


def margin(r: dict) -> float:
    p = sorted(r["probs"].values(), reverse=True)
    return p[0] - p[1]


def extra(vllm: list[dict], hf: list[dict]) -> dict:
    V = {(r["id"], r["perm"]): r for r in vllm}
    H = {(r["id"], r["perm"]): r for r in hf}
    keys = [k for k in V if k in H]
    dx = [math.log(max(H[k]["probs"].get("X", 1e-12), 1e-12)) - math.log(max(V[k]["probs"].get("X", 1e-12), 1e-12)) for k in keys]
    savok = {}
    for lo, hi in SAVOK:
        ks = [k for k in keys if lo <= margin(V[k]) < hi]
        savok[f"{lo}-{hi}"] = {"n": len(ks), "egyezes": round(st.mean(V[k]["pred"] == H[k]["pred"] for k in ks), 4) if ks else None}
    return {"logPX_hf_minus_vllm_median": round(st.median(dx), 4), "logPX_hf_minus_vllm_mean": round(st.mean(dx), 4),
            "x_pred_arany_hf": round(st.mean(H[k]["pred"] == "X" for k in keys), 4),
            "x_pred_arany_vllm": round(st.mean(V[k]["pred"] == "X" for k in keys), 4), "margo_savok": savok}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default="adat/pilot/pilot_eval.jsonl")
    ap.add_argument("--vllm", default="eredmenyek/F0/k0d/pilot_vllm.jsonl")
    ap.add_argument("--hf-none", default="eredmenyek/F0/k0d/pilot_hf.jsonl")
    ap.add_argument("--out", default="eredmenyek/F0/k0d2")
    ap.add_argument("--modes", default="vllm,fp32,pow2")
    args = ap.parse_args()
    out = EXP / args.out
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    model, _ = load_model(BF16_BASE, experts="eager")
    pt = PromptTokenizer(str(BF16_BASE))
    items = read_jsonl(EXP / args.items)
    vllm = read_jsonl(EXP / args.vllm)
    res = {"load_s": round(time.time() - t0, 1), "experts_implementation": model.config._experts_implementation,
           "n_items": len(items), "modok": {}}

    # 1. kontroll: hookok előtt és után (none mód) bájtazonos
    pre, _ = readout(model, pt, items[:50], [0], "", "alap", [], None)
    res["install"] = fakequant.install(model, "none")
    post, _ = readout(model, pt, items[:50], [0], "", "alap", [], None)
    same = sum(json.dumps(a["label_logprobs"], sort_keys=True) == json.dumps(b["label_logprobs"], sort_keys=True) for a, b in zip(pre, post))
    res["none_kontroll"] = {"n": len(pre), "bajtazonos": same}
    print(f"none-kontroll: {same}/{len(pre)} bájtazonos", flush=True)
    if same != len(pre):
        write_json(out / "k0d2.json", res)
        raise SystemExit("a none-kontroll bukott: a kikapcsolt fake-quant is változtat, vagy a HF nem determinisztikus")

    # 2. eager alapvonal (fake-quant nélkül)
    t1 = time.time()
    eager, _ = readout(model, pt, items, [0], "", "alap", [], None)
    write_jsonl(out / "pilot_hf_eager.jsonl", eager)
    ce, cg = compare(vllm, eager), compare(read_jsonl(EXP / args.hf_none), eager)
    res["eager"] = {**{k: ce[k] for k in ("top_label_agreement", "x_top_label_agreement", "label_logprob_mean_abs_diff",
                                          "gold_prob_mean_abs_diff", "acc_b")}, **extra(vllm, eager),
                    "vs_grouped_mm": {k: cg[k] for k in ("top_label_agreement", "label_logprob_mean_abs_diff")},
                    "wall_s": round(time.time() - t1, 1)}
    print("eager", json.dumps(res["eager"], ensure_ascii=False), flush=True)

    # 2. változatok
    for mode in args.modes.split(","):
        fakequant.set_mode(mode)
        t1 = time.time()
        rows, _ = readout(model, pt, items, [0], "", "alap", [], None)
        for r in rows:
            r["fakequant"] = mode
        write_jsonl(out / f"pilot_hf_fq_{mode}.jsonl", rows)
        c = compare(vllm, rows)
        res["modok"][mode] = {**{k: c[k] for k in ("n_paired", "top_label_agreement", "x_top_label_agreement",
                                                    "label_logprob_mean_abs_diff", "gold_prob_mean_abs_diff", "acc_a", "acc_b")},
                              **extra(vllm, rows), "wall_s": round(time.time() - t1, 1)}
        print(mode, json.dumps(res["modok"][mode], ensure_ascii=False), flush=True)
        write_json(out / "k0d2.json", res)
    fakequant.set_mode("none")
    hf_none = read_jsonl(EXP / args.hf_none)
    base = compare(vllm, hf_none)
    res["grouped_mm_k0d"] = {**{k: base[k] for k in ("top_label_agreement", "x_top_label_agreement", "label_logprob_mean_abs_diff",
                                                      "gold_prob_mean_abs_diff")}, **extra(vllm, hf_none)}
    # a választás: top-címke egyezés, döntetlennél a kisebb átlagos log-prob eltérés
    best = max(res["modok"], key=lambda m: (res["modok"][m]["top_label_agreement"], -res["modok"][m]["label_logprob_mean_abs_diff"]))
    res["legjobb"] = best
    write_json(out / "k0d2.json", res)
    print(json.dumps({"legjobb": best, "grouped_mm": base["top_label_agreement"], "eager": res["eager"]["top_label_agreement"],
                      best: res["modok"][best]["top_label_agreement"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
