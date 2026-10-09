"""A 00-ás kör HF-kiadásának összeállítása (Napló 2026-10-07: kiadás most, CC-BY-4.0, `k3dani`, mindhárom seed).

  dataset — a fagyasztott itemek a HF-splitekre: train; validation (val-belső + val-szállító); test (a négy F4-réteg);
            test_new_suppliers (a 00b `T-ujszallito`). A `meta.atnezes` (belső átnézési napló) kimarad; minden más mező
            marad. Kártya: hf-release/dataset/README.md. Ellenőrzés: egyedi id-k, a tenant neve sehol, a fagyasztott
            hash-ek egyeznek.
  adapter — a három seed (l3mixse_h2_s1..s3): a gyökérben az s1 peft-változata, `vllm/` az s1 vLLM-változata,
            `seed2/`, `seed3/` ugyanígy. Az adapter_config.json `base_model_name_or_path`-ja a helyi útvonal helyett a
            publikus modell. Mellé: calibration.json (a val-on illesztett temperature és τ, vLLM), decision_prompt.py,
            README.md (hf-release/adapter/).
  Kimenet: hf-release-00/{dataset,adapter} + MANIFEST.sha256 mindkettőben. Feltöltés külön, Dani jóváhagyása után.

  LDH_EXP=$PWD python3 eszkozok/hf_export.py dataset --out hf-release-00/dataset
  LDH_EXP=$PWD python3 eszkozok/hf_export.py adapter --out hf-release-00/adapter
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json, write_jsonl  # noqa: E402
from elemzes import _p  # noqa: E402

SPLITS = {"train": [("adat/f1", "train")],
          "validation": [("adat/f1", "val-belso"), ("adat/f1", "val-szallito")],
          "test": [("adat/f1", s) for s in ("T-belso", "T-szallito", "T-kozeli", "T-tavoli")],
          "test_new_suppliers": [("adat/k00b/meres", "T-ujszallito")]}
FREEZE = {"adat/f1": "eredmenyek/F1/atnezes/fagyasztas.sha256", "adat/k00b/meres": "eredmenyek/K00b/fagyasztas.sha256"}
FORBIDDEN = re.compile(r"<tenant>|_belso|/exp/|<user>", re.I)
SEEDS = ["l3mixse_h2_s1", "l3mixse_h2_s2", "l3mixse_h2_s3"]
CARD_STRIP = re.compile(r"^# VÁZ.*?(?=^[a-z_]+:)", re.S | re.M)
# a val-on illesztett temperature (perm 0) és τ@95/τ@90, vLLM, a fő F4-példány (eredmenyek/F4/vllm_f4.json)
CAL = {"seed1": {"temperature": 0.6572647826205814, "tau_95": 0.2748952545190677, "tau_90": 0.2748952545190677},
       "seed2": {"temperature": 0.631058784496602, "tau_95": 0.3364250174613652, "tau_90": 0.16471789187139887},
       "seed3": {"temperature": 0.6731161121018304, "tau_95": 0.34332694239039263, "tau_90": 0.34332694239039263}}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_freeze() -> None:
    for d, f in FREEZE.items():
        for line in _p(f).read_text().split("\n"):
            if line.strip():
                h, name = line.split()
                p = _p(d) / name
                if p.exists() and sha(p) != h:
                    raise SystemExit(f"{p}: eltér a fagyasztott hash-től")


def manifest(out: Path) -> None:
    lines = [f"{sha(p)}  {p.relative_to(out)}" for p in sorted(out.rglob("*")) if p.is_file() and p.name != "MANIFEST.sha256"]
    (out / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")


def card(src: Path, dst: Path) -> None:
    txt = CARD_STRIP.sub("", src.read_text())
    if "# VÁZ" in txt or "[kitöltendő" in txt:
        raise SystemExit(f"{src}: a kártyában maradt VÁZ- vagy kitöltendő-jelölés")
    dst.write_text(txt)


def cmd_dataset(args) -> None:
    check_freeze()
    out = _p(args.out)
    (out / "data").mkdir(parents=True, exist_ok=True)
    seen, rep = set(), {}
    for split, srcs in SPLITS.items():
        rows = []
        for d, stratum in srcs:
            for r in read_jsonl(_p(d) / f"items_{stratum}.jsonl"):
                r["meta"].pop("atnezes", None)
                if r["id"] in seen:
                    raise SystemExit(f"ismétlődő id: {r['id']}")
                seen.add(r["id"])
                rows.append(r)
        bad = [r["id"] for r in rows if FORBIDDEN.search(json.dumps(r, ensure_ascii=False))]
        if bad:
            raise SystemExit(f"{split}: tiltott minta {len(bad)} itemben, pl. {bad[:3]}")
        write_jsonl(out / "data" / f"{split}.jsonl", rows)
        rep[split] = {"items": len(rows), "scored": sum(not r["meta"].get("ketertelmu") for r in rows),
                      "x_gold": sum(r["gold"] is None for r in rows),
                      "strata": {s: sum(r["split"] == s for r in rows) for _, s in srcs}}
    card(_p("hf-release/dataset/README.md"), out / "README.md")
    manifest(out)
    write_json(out.parent / "dataset_export_riport.json", rep)
    print(json.dumps(rep, ensure_ascii=False))


def cmd_adapter(args) -> None:
    out = _p(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for k, seed in enumerate(SEEDS, 1):
        base = out if k == 1 else out / f"seed{k}"
        for variant, sub, model in (("final", "", "Qwen/Qwen3.6-35B-A3B"), ("vllm", "vllm", "Qwen/Qwen3.6-35B-A3B-FP8")):
            dst = base / sub
            dst.mkdir(parents=True, exist_ok=True)
            src = _p("ckpt") / seed / variant
            shutil.copy(src / "adapter_model.safetensors", dst / "adapter_model.safetensors")
            cfg = json.loads((src / "adapter_config.json").read_text())
            cfg["base_model_name_or_path"] = model
            cfg["task_type"] = cfg.get("task_type") or "CAUSAL_LM"  # a HF-kártya null-ra figyelmeztet; a betöltést nem érinti
            (dst / "adapter_config.json").write_text(json.dumps(cfg, indent=2) + "\n")
    write_json(out / "calibration.json", {
        "note": ("Fitted on the synthetic validation split (1,006 items), vLLM v0.30.0, one LoRA-enabled instance, "
                 "permutation 0 (stored option order, X last). Divide the label log-probabilities by `temperature`, "
                 "softmax over the labels present, and act when the top label is not X and its probability >= tau. "
                 "tau_95 / tau_90: the smallest threshold whose one-sided 95% Clopper-Pearson lower bound on the "
                 "precision of non-X decisions is >= 0.95 / 0.90. Refit both on your own labelled data."),
        **CAL})
    shutil.copy(_p("hf-release/adapter/decision_prompt.py"), out / "decision_prompt.py")
    card(_p("hf-release/adapter/README.md"), out / "README.md")
    bad = [p for p in out.rglob("*.json") if FORBIDDEN.search(p.read_text())]
    if bad:
        raise SystemExit(f"tiltott minta: {bad}")
    manifest(out)
    print(f"{out}: {sum(1 for p in out.rglob('*') if p.is_file())} fájl")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dataset", "adapter"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    {"dataset": cmd_dataset, "adapter": cmd_adapter}[args.cmd](args)


if __name__ == "__main__":
    main()
