#!/usr/bin/env python3
"""⛔ GB10 (sm_121a) — a Qwen3.5 gyors útjának kikapcsolása betöltés ELŐTT.

MÉRT TÉNY (2026-08-24, spark-dev, lora-train:3 image, transformers 5.6.0):
a `causal_conv1d` CUDA-kernel SZEGMENSHIBÁVAL leállítja a folyamatot a legelső
forward passnál — traceback nélkül, csak `Fatal Python error: Segmentation fault`
(modeling_qwen3_5.py:466 → causal_conv1d/cpp_functions.py:104). A wheel nem erre
az architektúrára készült. A python-szintű fallback (`F.silu(conv1d(x))`)
matematikailag azonos, csak lassabb.

A transformers a modul globálisaiból veszi a gyors utat a rétegek __init__-jében
(modeling_qwen3_5.py:405-408), ezért a patch-nek a `from_pretrained` ELŐTT kell
lefutnia — utólag a rétegek már eltárolták a kernel-referenciát.
"""

def patch(conv=True, fla=False, verbose=True):
    """conv=True: causal_conv1d ki (KÖTELEZŐ a GB10-en).
    fla=True: a flash-linear-attention triton-kerneljei is ki (lassabb, csak ha kell)."""
    import transformers.models.qwen3_5.modeling_qwen3_5 as M
    off = []
    if conv:
        M.causal_conv1d_fn = None
        M.causal_conv1d_update = None      # → torch_causal_conv1d_update
        off += ["causal_conv1d_fn", "causal_conv1d_update"]
    if fla:
        M.chunk_gated_delta_rule = None    # → torch_chunk_gated_delta_rule
        M.fused_recurrent_gated_delta_rule = None
        M.FusedRMSNormGated = None
        off += ["chunk_gated_delta_rule", "fused_recurrent_gated_delta_rule", "FusedRMSNormGated"]
    M.is_fast_path_available = False
    if verbose:
        print(f"[gb10_patch] kikapcsolva: {', '.join(off)}", flush=True)
    return off
