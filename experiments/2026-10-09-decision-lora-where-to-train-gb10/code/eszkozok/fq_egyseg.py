"""A fakequant.fq egységtesztje a vLLM saját per_token_group_quant_fp8 kernelje ellen
(a vLLM v0.30.0 image-ben, GPU-n; lib.sh: vpy).

Mindkét skálázásra (fp32 = a CUTLASS-lineárisok, UE8M0 = a Triton MoE útja) a vLLM
kvantált×skála értéke BF16-ra kerekítve bitre egyezzen a fq() kimenetével. Kiugró
értékeket is teszünk a bemenetbe, mert a valódi aktivációkban vannak.

  python3 eszkozok/fq_egyseg.py --out eredmenyek/F0/k0d2/fq_egyseg.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fakequant import fq  # noqa: E402

from vllm.model_executor.layers.quantization.utils.fp8_utils import per_token_group_quant_fp8  # noqa: E402

ESETEK = [((7, 2048), 1.0), ((513, 512), 30.0), ((64, 4096), 1e-3), ((3, 2048), 1e3), ((1, 6144), 0.05)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    torch.manual_seed(0)
    res = {}
    for pow2 in (False, True):
        tot = bad = 0
        worst = 0.0
        for shape, scale in ESETEK:
            x = (torch.randn(shape, device="cuda") * scale)
            x[..., ::97] *= 20  # kiugró csatornák
            x = x.to(torch.bfloat16)
            q, s = per_token_group_quant_fp8(x, 128, use_ue8m0=pow2)
            ref = (q.float().reshape(*shape[:-1], -1, 128) * s.float().reshape(*shape[:-1], -1, 1)).reshape(shape).to(torch.bfloat16)
            ours = fq(x, pow2)
            diff = (ours.float() - ref.float()).abs()
            tot += x.numel()
            bad += int((diff > 0).sum())
            worst = max(worst, float((diff / ref.float().abs().clamp_min(1e-30)).max()))
        res["ue8m0" if pow2 else "fp32"] = {"elem": tot, "elteres": bad, "max_rel": worst}
    res["ok"] = all(v["elteres"] == 0 for v in res.values() if isinstance(v, dict))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(res, indent=2))
    print(json.dumps(res))
    if not res["ok"]:
        raise SystemExit("fq ≠ vLLM per_token_group_quant_fp8")


if __name__ == "__main__":
    main()
