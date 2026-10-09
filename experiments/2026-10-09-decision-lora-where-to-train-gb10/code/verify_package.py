#!/usr/bin/env python3
"""Re-compute the point estimates of both rounds from what is published here, and check the dataset hashes.

What it does, CPU only, in about a minute:
  1. every file under dataset/ against corpus_manifest.json (sha256 of the file and of its uncompressed content);
  2. round 1 (invoice line -> catalogue article), vLLM: L0, L1* and L3 (3 seeds) on the four-layer test, from
     results/r00/readouts/vllm and dataset/r00 -> compared with results/r00/vllm_f4.json, every numeric field
     of the @95 and @90 test blocks;
  3. round 1, the 16-new-supplier layer (00b): the same arms from results/r00/readouts/k00b-vllm -> compared
     with results/r00/k00b/vllm_k00b.json, and the headline delta (+19.5 points);
  4. round 2 (tool selection): L0, L1* and L3 (3 seeds) on every reported layer, from results/r01/readouts and
     dataset/r01 -> compared with results/r01/f4_elemzes.json.

The scoring functions are the ones the measurement used (code/eszkozok/elemzes.py, code/kor01/eszkozok/
f4_elemzes01.py), unchanged. Reference rows of round 2 carry pseudonymised tool names; the read-outs use the same
pseudonyms, so every metric is invariant (see corpus_manifest.json, "pseudonym").

Not re-computed here: the bootstrap confidence intervals (10 000 replicates; run the original analysis scripts),
the HF-engine read-outs, the serving measurements, and the JEV comparison (results/f5b; needs the upstream
results file, see code/kor01/eszkozok/f5b_jev.py).

    pip install -r code/requirements.txt
    python3 code/verify_package.py

Part of DocAI Evals - https://docai.hu
"""
from __future__ import annotations

import gzip
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code/eszkozok"))
sys.path.insert(0, str(ROOT / "code/kor01/eszkozok"))

from elemzes import TARGETS, TEST_STRATA, VAL_STRATA, arm_predictions, by_item, choose_tau, fit_temperature, metrics  # noqa: E402
from f4_elemzes01 import layers  # noqa: E402

TOL = 1e-9
SEEDS = ("s1", "s2", "s3")


def jl(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_arm(d: Path, val: str, test: str, meta: dict, arm: str) -> dict:
    rv, rt = jl(d / f"{val}.jsonl.gz"), jl(d / f"{test}.jsonl.gz")
    prm = {"temp": fit_temperature([r for r in rv if r["perm"] == 0], meta)}
    return {**arm_predictions(arm, by_item(rv, None), meta, prm), **arm_predictions(arm, by_item(rt, None), meta, prm)}


class Tally:
    def __init__(self) -> None:
        self.n = 0
        self.bad: list[str] = []

    def compare(self, where: str, ours: dict, ref: dict) -> None:
        for k, v in ref.items():
            if isinstance(v, bool) or not isinstance(v, (int, float)) or k not in ours:
                continue
            self.n += 1
            w = ours[k]
            if v != v and w != w:  # NaN on both sides
                continue
            if abs(w - v) > TOL:
                self.bad.append(f"{where}.{k}: published {v!r}, recomputed {w!r}")


def check_manifest() -> int:
    man = json.loads((ROOT / "corpus_manifest.json").read_text())
    bad = 0
    for rel, e in man["dataset"].items():
        b = (ROOT / rel).read_bytes()
        ok = hashlib.sha256(b).hexdigest() == e["sha256"]
        if "sha256_uncompressed" in e:
            ok &= hashlib.sha256(gzip.decompress(b)).hexdigest() == e["sha256_uncompressed"]
        if not ok:
            print(f"  hash mismatch: {rel}")
            bad += 1
    for split, h in man["r00_hugging_face"]["hf_manifest"].items():
        p = ROOT / "dataset/r00" / (Path(split).name + ".gz")
        if p.exists() and hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest() != h:
            print(f"  differs from the Hugging Face manifest: {split}")
            bad += 1
    print(f"manifest: {len(man['dataset'])} files, {bad} mismatches")
    return bad


def meta_r00(*files: str) -> dict:
    meta = {}
    for f in files:
        for it in jl(ROOT / "dataset/r00" / f):
            meta[it["id"]] = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None, **it["meta"]}
    return meta


def round1(t: Tally) -> None:
    meta = meta_r00("validation.jsonl.gz", "test.jsonl.gz")
    d = ROOT / "results/r00/readouts/vllm"
    arms = {"L0": load_arm(d, "l0_val", "l0_test", meta, "nyers"),
            "L1csillag": load_arm(d, "l0_val", "l0_test", meta, "perm_avg"),
            **{f"L3_{s}": load_arm(d, f"l3_{s}_val", f"l3_{s}_test", meta, "temp") for s in SEEDS}}
    ref = json.loads((ROOT / "results/r00/vllm_f4.json").read_text())["pont"]
    val_ids = [i for i in arms["L1csillag"] if meta[i]["split"] in VAL_STRATA]
    test_ids = [i for i in arms["L1csillag"] if meta[i]["split"] in TEST_STRATA]
    for name, p in arms.items():
        for tgt, tn in TARGETS:
            tau = choose_tau(p, meta, val_ids, tgt)
            t.compare(f"r00.{name}.{tn}", {"tau": tau}, {"tau": ref[name][tn]["tau"]})
            t.compare(f"r00.{name}.{tn}.teszt", metrics(p, meta, test_ids, tau), ref[name][tn]["teszt"])
    lef = {k: metrics(p, meta, test_ids, choose_tau(p, meta, val_ids, 0.95))["besorolasi_lefedettseg"]
           for k, p in arms.items()}
    gain = sum(lef[f"L3_{s}"] for s in SEEDS) / 3 - lef["L1csillag"]
    print(f"round 1, test (n = {len(test_ids)}): L1* lef@95 {lef['L1csillag']:.3f}, L3 mean "
          f"{sum(lef[f'L3_{s}'] for s in SEEDS) / 3:.3f}, gain {100 * gain:+.1f} points")


def round1_new_suppliers(t: Tally) -> None:
    meta = {i: m for i, m in meta_r00("validation.jsonl.gz").items() if m["split"] in VAL_STRATA}
    meta |= {i: m for i, m in meta_r00("test_new_suppliers.jsonl.gz").items() if m["split"] == "T-ujszallito"}
    d = ROOT / "results/r00/readouts/k00b-vllm"
    arms = {"L0": load_arm(d, "l0_val", "l0_test", meta, "nyers"),
            "L1csillag": load_arm(d, "l0_val", "l0_test", meta, "perm_avg"),
            **{f"L3_{s}": load_arm(d, f"l3_{s}_val", f"l3_{s}_test", meta, "temp") for s in SEEDS}}
    ref = json.loads((ROOT / "results/r00/k00b/vllm_k00b.json").read_text())
    val_ids = sorted(i for i in arms["L1csillag"] if i in meta and meta[i]["split"] in VAL_STRATA)
    test_ids = sorted(i for i in arms["L1csillag"] if i in meta and meta[i]["split"] == "T-ujszallito")
    lef = {}
    for name, p in arms.items():
        for tgt, tn in TARGETS:
            tau = choose_tau(p, meta, val_ids, tgt)
            m = metrics(p, meta, test_ids, tau)
            t.compare(f"r00b.{name}.{tn}", {"tau": tau, **m}, ref["pont"][name][tn])
            lef[(name, tn)] = m["besorolasi_lefedettseg"]
    gain = sum(lef[(f"L3_{s}", "95")] for s in SEEDS) / 3 - lef[("L1csillag", "95")]
    t.compare("r00b.pont_delta", {"lef95": gain}, {"lef95": ref["pont_delta"]["lef95"]})
    print(f"round 1, 16 new suppliers (n = {len(test_ids)}): gain {100 * gain:+.1f} points")


def meta_r01() -> dict:
    meta = {}
    rows = jl(ROOT / "dataset/r01/items_hu.jsonl.gz") + jl(ROOT / "dataset/r01/items_ref.jsonl.gz")
    for it in rows:
        if it["split"] == "train":
            continue
        m = {"split": it["split"], "gold": it["gold"], "x": it["gold"] is None, "forras": it["forras"],
             "n_opcio": len(it["options"]), **it["meta"]}
        m.setdefault("klaszter", it["id"])
        meta[it["id"]] = m
    return meta


def round2(t: Tally) -> None:
    meta = meta_r01()
    lay = json.loads((ROOT / "dataset/r01/layers.json").read_text())
    d = ROOT / "results/r01/readouts"
    arms = {"L0": load_arm(d, "bazis_val", "bazis_test", meta, "nyers"),
            "L1csillag": load_arm(d, "bazis_val", "bazis_test", meta, "perm_avg"),
            **{f"L3_{s}": load_arm(d, f"l3_{s}_val", f"l3_{s}_test", meta, "temp") for s in SEEDS}}
    val_ids = [i for i in arms["L1csillag"] if meta[i]["split"] == "val"]
    test_ids = [i for i in arms["L1csillag"] if meta[i]["split"] != "val"]
    L = layers(meta, test_ids, set(lay["T-uj-eszkoz"]), set(lay["near_duplicate_requests"]))
    ref = json.loads((ROOT / "results/r01/f4_elemzes.json").read_text())["pont"]
    for name, p in arms.items():
        for tgt, tn in TARGETS:
            tau = choose_tau(p, meta, val_ids, tgt)
            t.compare(f"r01.{name}.{tn}", {"tau": tau}, {"tau": ref[name][tn]["tau"]})
            for layer, ids in L.items():
                if ids and layer in ref[name][tn]["retegek"]:
                    t.compare(f"r01.{name}.{tn}.{layer}", metrics(p, meta, ids, tau), ref[name][tn]["retegek"][layer])
    pool = {k: metrics(p, meta, L["pool"], choose_tau(p, meta, val_ids, 0.95)) for k, p in arms.items()}
    print(f"round 2, pool (n = {len(L['pool'])}): L1* lef@95 {pool['L1csillag']['besorolasi_lefedettseg']:.3f} "
          f"precision {pool['L1csillag']['besorolasi_precizitas']:.3f}; L3 s1-s3 precision "
          + " / ".join(f"{pool[f'L3_{s}']['besorolasi_precizitas']:.3f}" for s in SEEDS))


def main() -> int:
    bad = check_manifest()
    t = Tally()
    round1(t)
    round1_new_suppliers(t)
    round2(t)
    print(f"compared {t.n} published numbers, {len(t.bad)} differ by more than {TOL}")
    for line in t.bad[:30]:
        print("  " + line)
    return 1 if bad or t.bad else 0


if __name__ == "__main__":
    sys.exit(main())
