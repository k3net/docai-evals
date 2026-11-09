"""05-ös kör — F1: HF ↔ vLLM egyezés (05-runbook 3. pont „az összevetés motorja”, 10. pont F1; a K0d megismétlése).

A HF-út (BF16 bázis, `hf_jellemzo05 kivon`) címkeeloszlását veti össze a 03 F2 vLLM-kiolvasásaival (FP8, vLLM
v0.30.0, `kor03/eredmenyek/F2/qwen_{val,eval}.jsonl`) ugyanazon az (item, perm) páron. Új vLLM-futás nem kell: a
D_dev a 03 val-ja, a D_meta és a D_cal a test-id-ből jön, ezeket a 03 mind a négy permutációval kiolvasta. A
kitartott rétegeket nem érinti.

  python3 kor05/eszkozok/egyezes_vllm05.py --hf-root cache/k05/jellemzok --out kor05/eredmenyek/F1/hf_vllm/egyezes.json
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
F2R = EXP / "kor03/eredmenyek/F2"
FELADATOK = ("D_dev__kanonikus", "D_meta__kanonikus", "D_cal_prob__kanonikus", "D_cal_policy__kanonikus",
             "D_cal_prob__b1", "D_cal_policy__b1")


def jsonl(p: Path):
    with p.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hf-root", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    hf = {}
    for t in FELADATOK:
        for f in sorted((Path(a.hf_root) / t).glob("sorok_*.jsonl")):
            for r in jsonl(f):
                hf[(r["id"], r["perm"])] = (t, r)
    stat = defaultdict(lambda: defaultdict(list))
    hianyos = 0
    for src in ("qwen_val.jsonl", "qwen_eval.jsonl"):
        for v in jsonl(F2R / src):
            key = (v["id"], v["perm"])
            if key not in hf:
                continue
            t, h = hf.pop(key)
            if h["order"] != v["order"]:
                raise SystemExit(f"{key}: eltérő opciósorrend")
            hianyos += bool(v.get("missing"))
            labs = h["labels"]
            ph, pv = np.array([h["probs"][x] for x in labs]), np.array([v["probs"][x] for x in labs])
            for grp in (t, f"perm{h['perm']}", "osszes"):
                s = stat[grp]
                s["top1_egyezik"].append(h["pred"] == v["pred"])
                s["x_egyezik"].append((h["pred"] == "X") == (v["pred"] == "X"))
                s["tv"].append(0.5 * float(np.abs(ph - pv).sum()))
                s["d_conf_hf_top"].append(abs(h["probs"][h["pred"]] - v["probs"][h["pred"]]))
                s["hf_helyes"].append(h["pred"] == h["gold_label"])
                s["vllm_helyes"].append(v["pred"] == v["gold_label"])
                s["magabiztos_billen"].append(h["pred"] != v["pred"] and max(h["conf"], v["conf"]) >= 0.9)
    out = {"vllm_forras": "kor03/eredmenyek/F2 (Qwen3.6-35B-A3B-FP8, vLLM v0.30.0)", "hf_forras": a.hf_root,
           "parositatlan_hf_sor": len(hf), "vllm_hianyzo_cimkes_sor": hianyos, "csoportok": {}}
    for grp, s in stat.items():
        tv = np.array(s["tv"])
        out["csoportok"][grp] = {
            "n": len(tv), "top1_egyezes": round(float(np.mean(s["top1_egyezik"])), 4),
            "x_dontes_egyezes": round(float(np.mean(s["x_egyezik"])), 4),
            "magabiztos_billenes": round(float(np.mean(s["magabiztos_billen"])), 4),
            "tv_atlag": round(float(tv.mean()), 4), "tv_p95": round(float(np.percentile(tv, 95)), 4),
            "tv_max": round(float(tv.max()), 4),
            "pontossag_hf": round(float(np.mean(s["hf_helyes"])), 4),
            "pontossag_vllm": round(float(np.mean(s["vllm_helyes"])), 4)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for grp, c in out["csoportok"].items():
        print(f"{grp:24s} n={c['n']:6d} top1={c['top1_egyezes']:.4f} X={c['x_dontes_egyezes']:.4f} "
              f"magabiztos-billenés={c['magabiztos_billenes']:.4f} TV átlag={c['tv_atlag']:.4f} p95={c['tv_p95']:.4f} "
              f"pontosság HF/vLLM={c['pontossag_hf']:.4f}/{c['pontossag_vllm']:.4f}")
    print(f"párosítatlan HF-sor: {len(hf)}, a vLLM-ben hiányzó címkés sor: {hianyos}")


if __name__ == "__main__":
    main()
