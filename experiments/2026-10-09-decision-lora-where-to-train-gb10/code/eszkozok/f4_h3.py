"""F4 — H3 („ugyanazon a példányon kiszolgálható”), példány-robusztusság és teljesítmény (runbook 3. H3, 6. pont).

  (a) aktiválás — a K0c kapuja (eredmenyek/F0/k0c/k0c.json), itt csak hivatkozva;
  (b) a LoRA-hatás egyezése: a címke-logprobok elmozdulása (L3 − L0) a HF-ben és a vLLM-ben, Pearson r ≥ 0,9
      (teszt, 0. permutáció, minden (item, címke) pár);
  (c) motorok közti egyezés: [L3 HF↔vLLM top-címke egyezés] − [L0 HF↔vLLM egyezés], egyoldali 95%-os alsó
      korlát (klaszterezett bootstrap, klaszter = cikk) > −2 pont;
  (d) a LoRA-t nem kérő kérések nem sérülnek: az `--enable-lora`-s friss példányok L0-ja és a LoRA nélküli friss
      példányok L0-ja közti egyezés ≥ (a LoRA nélküli példányok egymás közti egyezése) − 1 pont.
  Példány-billenés: friss példánypárok közt a top-címke eltérésének aránya; numerika-módok: a próbahalmaz
  ujjlenyomatainak és a top-címke-vektoroknak a különböző értékei.
  Teljesítmény: döntés/s és p50/p95 késleltetés concurrency 1/8/32 mellett, (a) LoRA nélküli példány, (b)
  `--enable-lora`-s példány LoRA nélküli kéréssel, (c) `lora_request`-tel.

  python3 eszkozok/f4_h3.py --dir eredmenyek/F4 --out eredmenyek/F4/h3.json
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import _p, load_meta  # noqa: E402

R_MIN, C_MARGIN, D_MARGIN = 0.9, -0.02, -0.01


def top(rows: list[dict], perm: int = 0) -> dict[str, str]:
    return {r["id"]: max(r["label_logprobs"], key=r["label_logprobs"].get) for r in rows if r["perm"] == perm}


def lp(rows: list[dict], perm: int = 0) -> dict[str, dict]:
    return {r["id"]: r["label_logprobs"] for r in rows if r["perm"] == perm}


def agree(a: dict, b: dict) -> float:
    ids = sorted(set(a) & set(b))
    return float(np.mean([a[i] == b[i] for i in ids]))


def effect_corr(v0: dict, v3: dict, h0: dict, h3: dict) -> dict:
    dv, dh = [], []
    for i in sorted(set(v0) & set(v3) & set(h0) & set(h3)):
        for lab in v0[i]:
            dv.append(v3[i][lab] - v0[i][lab])
            dh.append(h3[i][lab] - h0[i][lab])
    r = float(np.corrcoef(dv, dh)[0, 1])
    return {"pearson_r": r, "parok": len(dv), "kuszob": R_MIN, "teljesul": r >= R_MIN}


def engine_agreement(v0, v3, h0, h3, meta, reps: int, rng) -> dict:
    ids = sorted(set(v0) & set(v3) & set(h0) & set(h3))
    d = np.array([(v3[i] == h3[i]) - (v0[i] == h0[i]) for i in ids], dtype=float)
    cl = defaultdict(list)
    for k, i in enumerate(ids):
        cl[meta[i].get("article")].append(k)
    groups = [np.array(v) for v in cl.values()]
    boots = []
    for _ in range(reps):
        pick = rng.integers(0, len(groups), len(groups))
        boots.append(d[np.concatenate([groups[k] for k in pick])].mean())
    lo = float(np.percentile(boots, 5))
    return {"L3_egyezes": float(np.mean([v3[i] == h3[i] for i in ids])),
            "L0_egyezes": float(np.mean([v0[i] == h0[i] for i in ids])), "kulonbseg": float(d.mean()),
            "egyoldali_95_also": lo, "kuszob": C_MARGIN, "teljesul": lo > C_MARGIN}


def pairwise(xs: list[dict]) -> list[float]:
    return [agree(a, b) for a, b in itertools.combinations(xs, 2)]


def perf(path: Path) -> dict:
    rows = read_jsonl(path)
    s = json.loads(path.with_suffix(".summary.json").read_text())
    lat = np.array([r["latency_s"] for r in rows])
    return {"n": len(rows), "dontes_per_s": len(rows) / s["wall_s"], "p50_ms": float(np.percentile(lat, 50) * 1e3),
            "p95_ms": float(np.percentile(lat, 95) * 1e3)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="eredmenyek/F4")
    ap.add_argument("--items", default="adat/f1")
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    D = _p(args.dir)
    meta = load_meta(_p(args.items))
    rng = np.random.default_rng(0)
    res = {}

    k0c = _p("eredmenyek/F0/k0c/k0c.json")
    res["a_aktivalas_K0c"] = {"forras": "eredmenyek/F0/k0c/k0c.json",
                              "teljesul": json.loads(k0c.read_text()).get("K0c_ok") if k0c.exists() else None}

    V, H = D / "vllm", D / "hf"
    rv0, rv3 = read_jsonl(V / "l0_test.jsonl"), read_jsonl(V / "l3_s1_test.jsonl")
    rh0, rh3 = read_jsonl(H / "l0_test.jsonl"), read_jsonl(H / "l3_s1_test.jsonl")
    res["b_lora_hatas_egyezese"] = effect_corr(lp(rv0), lp(rv3), lp(rh0), lp(rh3))
    res["c_motorok_kozti_egyezes"] = engine_agreement(top(rv0), top(rv3), top(rh0), top(rh3), meta, args.reps, rng)

    P = D / "h3"
    lora_l0 = [top(read_jsonl(f)) for f in sorted(P.glob("lora_k*_l0.jsonl"))]
    lora_l3 = [top(read_jsonl(f)) for f in sorted(P.glob("lora_k*_l3.jsonl"))]
    nolora = [top(read_jsonl(f)) for f in sorted(P.glob("nolora_k*_l0.jsonl"))]
    cross = [agree(a, b) for a in lora_l0 for b in nolora]
    base = pairwise(nolora)
    res["d_lora_nelkuli_keresek"] = {
        "peldanyok": {"lora": len(lora_l0), "lora_nelkul": len(nolora)},
        "lora_vs_lora_nelkul_egyezes": float(np.mean(cross)), "lora_nelkul_egymas_kozt": float(np.mean(base)),
        "kuszob": D_MARGIN, "teljesul": float(np.mean(cross)) >= float(np.mean(base)) + D_MARGIN}
    fps = {f.name: json.loads(f.read_text())["fingerprint"] for f in sorted(P.glob("*_probe.summary.json"))}
    res["peldany_robusztussag"] = {
        "billenes": {"lora_nelkul_L0": 1 - float(np.mean(base)), "lora_L0": 1 - float(np.mean(pairwise(lora_l0))),
                     "lora_L3": 1 - float(np.mean(pairwise(lora_l3)))},
        "numerika_modok": {
            "proba_ujjlenyomat": {"lora": len({v for k, v in fps.items() if k.startswith("lora_")}),
                                  "lora_nelkul": len({v for k, v in fps.items() if k.startswith("nolora_")})},
            "top_cimke_vektor": {name: len({tuple(sorted(x.items())) for x in xs})
                                 for name, xs in [("lora_L0", lora_l0), ("lora_L3", lora_l3), ("lora_nelkul_L0", nolora)]}},
        "fo_peldany_ujjlenyomat_eleje_vege": [json.loads((V / f"probe_{w}.summary.json").read_text())["fingerprint"]
                                             for w in ("eleje", "vege")]}
    res["H3_teljesul"] = all(res[k]["teljesul"] for k in ("b_lora_hatas_egyezese", "c_motorok_kozti_egyezes",
                                                          "d_lora_nelkuli_keresek")) and res["a_aktivalas_K0c"]["teljesul"] is True

    res["teljesitmeny"] = {}
    for name, pat in [("a_lora_nelkuli_peldany", "perf_nolora_c{}"), ("b_lora_peldany_lora_nelkul", "perf_lora_l0_c{}"),
                      ("c_lora_request", "perf_lora_l3_c{}")]:
        res["teljesitmeny"][name] = {c: perf(D / "perf" / f"{pat.format(c)}.jsonl") for c in (1, 8, 32)
                                     if (D / "perf" / f"{pat.format(c)}.jsonl").exists()}
    write_json(_p(args.out), res)
    print(json.dumps({k: res[k].get("teljesul") if isinstance(res[k], dict) else res[k] for k in res
                      if k != "teljesitmeny"}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
