"""FP8 aktiváció-fake-quant a HF-motorban (K0d-2 mérés, az F3 fake-quant karja).

A vLLM v0.30.0 GB10-es kernelútját utánozza (az alany-logból és a forrásból igazolva; CUDA-n mindkét
út a torch.ops._C.per_token_group_fp8_quant C++ kernelt hívja — fq_egyseg.py bitre ellenőrzi):
  - FP8-lineárisok — CutlassFp8BlockScaledMMKernel: dinamikus, tokenenként 128-as csoport,
    fp32 skála (cutlass.py: QuantFP8(..., use_ue8m0=False)).
  - routed expertek — TRITON fp8_w8a8 MoE: ugyanez a két GEMM bemenetén, de a skála
    kettőhatványra FELFELÉ kerekítve (UE8M0), mert a fused_moe/utils.py:243 a
    per_token_group_quant_fp8 alapértelmezését kapja, és az E8M0 a GB10-en be van kapcsolva.
Skála = max(amax, 1e-10) / 448 (pontosan kerekítve); q = clamp(x / s, ±448) → float8_e4m3fn (RNE);
visszaszorozva s-sel. Maradék eltérés: a vLLM a RMSNorm+kvantálást fuzionálja (fuse_norm_quant), ott a
normalizált érték bf16-kerekítés nélkül kvantálódik; itt a bf16 kimenet.

Bekapcsolt módban az expertek mindig az eager-úton futnak (a grouped_mm belsejébe nem lehet
kvantálást tenni), ezért a tiszta összevetéshez a modellt `experts_implementation="eager"`-rel
kell betölteni (hf_kiolvaso.load_model(..., experts="eager")); kikapcsolt módban az eredeti forward fut.

Hookot csak az FP8-forrású modulok kapnak (a forrás-snapshot `weight_scale_inv` kulcsai alapján).
A LoRA-ág a kvantálatlan bemenetet látja, ahogy a vLLM-ben: a PEFT a hookolt modult
`base_layer`-ként tartja meg. Tanításnál straight-through: x + (fq(x) − x).detach().

A mód futás közben váltható (set_mode), így egy betöltéssel több változat mérhető:
  none — kikapcsolva (az „FP8-hű BF16” bázis)
  vllm — lineáris fp32, MoE UE8M0 (a fenti kernelút)
  fp32 — mindkettő fp32 skála
  pow2 — mindkettő UE8M0 skála
  lin  — csak a lineárisok fp32 skálával; az expertek kvantálás nélkül, a gyors úton (a tréning-tartalék)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import SUBJECT_SNAPSHOT  # noqa: E402

FP8_MAX = 448.0
GROUP = 128
MODES = {"none": (None, None), "vllm": (False, True), "fp32": (False, False), "pow2": (True, True),
         "lin": (False, None)}  # lin: csak a lineárisok (fp32 skála), az expertek a betöltött (grouped_mm) úton
_CFG = {"lin": None, "moe": None}  # None = ki, False = fp32 skála, True = UE8M0 skála


def set_mode(mode: str) -> None:
    _CFG["lin"], _CFG["moe"] = MODES[mode]


def fq(x: torch.Tensor, pow2: bool) -> torch.Tensor:
    shp = x.shape
    if shp[-1] % GROUP:
        raise ValueError(f"a bemenet utolsó dimenziója ({shp[-1]}) nem osztható {GROUP}-cal")
    xf = x.float().reshape(*shp[:-1], shp[-1] // GROUP, GROUP)
    a = xf.abs().amax(-1, keepdim=True).clamp_min(1e-10)
    # tenzor/tenzor osztás = IEEE div.rn; a `tensor / skalár` CUDA-n reciprokkal szoroz, és a csoportok
    # felében 1 ulp-vel eltér a vLLM-kernel pontosan kerekített skálájától (fq_egyseg, 2026-10-03)
    s = a / torch.full_like(a, FP8_MAX)
    if pow2:
        s = torch.exp2(torch.ceil(torch.log2(s)))
    q = ((xf / s).clamp(-FP8_MAX, FP8_MAX).to(torch.float8_e4m3fn).float() * s).reshape(shp).to(x.dtype)
    return x + (q - x).detach() if x.requires_grad else q


def fp8_modules() -> tuple[set[str], set[str]]:
    """(FP8-lineárisok HF-nevei, FP8 expert-modulok HF-nevei) a forrás-indexből."""
    wmap = json.load(open(SUBJECT_SNAPSHOT / "model.safetensors.index.json"))["weight_map"]
    lin, moe = set(), set()
    for k in wmap:
        if not k.endswith(".weight_scale_inv"):
            continue
        name = k[: -len(".weight_scale_inv")]
        if name.startswith("model.language_model."):
            name = "model." + name[len("model.language_model."):]
        elif name != "lm_head":
            continue  # vizuális torony, MTP — a CausalLM-ben nincs
        m = re.fullmatch(r"(model\.layers\.\d+\.mlp\.experts)\.\d+\.(gate|up|down)_proj", name)
        if m:
            moe.add(m.group(1))
        else:
            lin.add(name)
    return lin, moe


def _lin_hook(_mod, args):
    if _CFG["lin"] is None:
        return None
    return (fq(args[0], _CFG["lin"]),) + tuple(args[1:])


def _experts_forward(mod):
    """Kikapcsolt módban az eredeti (betöltéskor választott, pl. grouped_mm) forward; bekapcsolva a
    Qwen3_5MoeExperts eager-útja a két GEMM-bemenet fake-quantjával."""
    act = mod.act_fn
    orig = mod.forward

    def forward(hidden_states, top_k_index, top_k_weights):
        pow2 = _CFG["moe"]
        if pow2 is None:
            return orig(hidden_states, top_k_index, top_k_weights)
        x = fq(hidden_states, pow2)
        final = torch.zeros_like(hidden_states)
        with torch.no_grad():
            mask = torch.nn.functional.one_hot(top_k_index, num_classes=mod.num_experts).permute(2, 1, 0)
            hit = torch.greater(mask.sum(dim=(-1, -2)), 0).nonzero()
        for e in hit:
            e = e[0]
            if e == mod.num_experts:
                continue
            pos, tok = torch.where(mask[e])
            gate, up = torch.nn.functional.linear(x[tok], mod.gate_up_proj[e]).chunk(2, dim=-1)
            h = fq(act(gate) * up, pow2)
            h = torch.nn.functional.linear(h, mod.down_proj[e]) * top_k_weights[tok, pos, None]
            final.index_add_(0, tok, h.to(final.dtype))
        return final

    return forward


def install(model, mode: str = "vllm") -> dict:
    """Hookok fel az FP8-forrású modulokra; PEFT előtt és után is hívható. Riportot ad vissza."""
    lin, moe = fp8_modules()
    mods = dict(model.named_modules())

    def find(n):
        for c in (n, "base_model.model." + n):
            if c in mods:
                m = mods[c]
                return getattr(m, "base_layer", m)
        return None

    missing, n_lin, n_moe = [], 0, 0
    for n in sorted(lin):
        m = find(n)
        if m is None:
            missing.append(n)
            continue
        m.register_forward_pre_hook(_lin_hook)
        n_lin += 1
    for n in sorted(moe):
        m = find(n)
        if m is None:
            missing.append(n)
            continue
        m.forward = _experts_forward(m)
        n_moe += 1
    if missing:
        raise SystemExit(f"FAKE-QUANT: {len(missing)} FP8-modul nem található a HF-modellben, pl. {missing[:5]}")
    set_mode(mode)
    return {"fp8_linear": n_lin, "fp8_experts": n_moe, "mode": mode}
