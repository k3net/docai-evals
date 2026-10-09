"""K0c — LoRA-aktiválási próba-adapterek egy VALÓDI PEFT-mentésből (runbook 9. pont).

A forrás egy rövid pilot-tréning `final` adaptere (mix+se célmodulokkal). A B-mátrixokat
seedelt, nem nulla zajra cseréljük, hogy a hatás biztosan mérhető legyen, és
csoportonként külön adaptert készítünk:
  k0c_attn / k0c_gdn / k0c_se / k0c_all — átnevezett (vLLM-) kulcsokkal
  k0c_all_norename                        — NEGATÍV KONTROLL: az eredeti PEFT-kulcsokkal
A vLLM-ben várt betöltött modulszám (csomagolt modulokkal számolva):
  attn: 10 réteg × (qkv_proj, o_proj) = 20 · gdn: 30 × (in_proj_qkvz, in_proj_ba, out_proj) = 90
  se: 40 × (gate_up_proj, down_proj) = 80 · all: 190 · norename: 0

Futtatás: python3 eszkozok/k0c_adapterek.py --src ckpt/k0e/final --out adapters
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import torch
from safetensors.torch import load_file, save_file

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, write_json  # noqa: E402
from tren_lora import HF_PREFIX, SHORT_NAMES, VLLM_PREFIX  # noqa: E402

GROUP_RE = {
    "attn": re.compile(r"\.self_attn\.(q|k|v|o)_proj\."),
    "gdn": re.compile(r"\.linear_attn\.(in_proj_qkv|in_proj_z|in_proj_a|in_proj_b|out_proj)\."),
    "se": re.compile(r"\.mlp\.shared_expert\.(gate|up|down)_proj\."),
}
EXPECTED = {"k0c_attn": 20, "k0c_gdn": 90, "k0c_se": 80, "k0c_all": 190, "k0c_all_norename": 0}


def make(sd: dict, groups: list[str], rename: bool, seed: int) -> dict:
    g = torch.Generator().manual_seed(seed)
    out = {}
    for k, v in sd.items():
        if not any(GROUP_RE[x].search(k) for x in groups):
            continue
        if ".lora_B." in k:
            v = (torch.randn(v.shape, generator=g) * 0.01).to(v.dtype)
        if rename and k.startswith(HF_PREFIX):
            k = VLLM_PREFIX + k[len(HF_PREFIX):]
        out[k] = v.contiguous()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", default="adapters")
    args = ap.parse_args()
    src = Path(args.src) if Path(args.src).is_absolute() else EXP / args.src
    out = Path(args.out) if Path(args.out).is_absolute() else EXP / args.out
    sd = load_file(str(src / "adapter_model.safetensors"))
    cfg = json.load(open(src / "adapter_config.json"))
    plan = {"k0c_attn": (["attn"], True), "k0c_gdn": (["gdn"], True), "k0c_se": (["se"], True),
            "k0c_all": (["attn", "gdn", "se"], True), "k0c_all_norename": (["attn", "gdn", "se"], False)}
    rep = {}
    for i, (name, (groups, rename)) in enumerate(plan.items()):
        d = out / name
        d.mkdir(parents=True, exist_ok=True)
        t = make(sd, groups, rename, seed=1000 + i)
        save_file(t, str(d / "adapter_model.safetensors"))
        c = {k: v for k, v in cfg.items() if not k.startswith("_ldh")}
        c["target_modules"] = sorted({n for g in groups for n in SHORT_NAMES[g]})
        json.dump(c, open(d / "adapter_config.json", "w"), indent=2)
        rep[name] = {"tensors": len(t), "lora_A": sum(".lora_A." in k for k in t), "expected_vllm_modules": EXPECTED[name],
                     "key_sample": sorted(t)[:2]}
    write_json(out / "k0c_adapterek.json", rep)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
