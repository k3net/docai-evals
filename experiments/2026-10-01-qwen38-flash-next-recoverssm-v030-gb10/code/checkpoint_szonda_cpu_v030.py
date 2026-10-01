#!/usr/bin/env python3
"""Round8 A fázis — a round4 CPU-szonda v0.30-ra: a K1 image TÉNYLEGES scheduler-forrásából kiemelt
_mamba_block_aligned_split, a modul saját segédfüggvényeivel, a K1-trace futásidejű attribútumaival.
Kérdés: v0.30-on melyik A/B hossznál marad ki a közös 1600-as checkpoint (a round4 hiba feltétele)?
Futtatás a K1 image-ben (GPU nem kell):  python3 checkpoint_szonda_cpu_v030.py [scheduler.py] [attr.json]"""
import ast, copy, json, sys
from types import SimpleNamespace as NS
from pathlib import Path
import vllm.v1.core.sched.scheduler as S

SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(S.__file__)
ATTR = json.loads(Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else {}
BS = ATTR.get("block_size", 1600)

tree = ast.parse(SRC.read_text())
c = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Scheduler")
f = copy.deepcopy(next(n for n in c.body if isinstance(n, ast.FunctionDef) and n.name == "_mamba_block_aligned_split"))
f.decorator_list = []
env = dict(vars(S))
exec(compile(ast.Module(body=[f], type_ignores=[]), str(SRC), "exec"), env)
split = env["_mamba_block_aligned_split"]

def sched():
    return NS(cache_config=NS(block_size=BS), block_size=BS,
              hash_block_size=ATTR.get("hash_block_size", BS),
              use_eagle=True, use_eagle_block_drop=ATTR.get("use_eagle_block_drop", True),
              max_num_scheduled_tokens=ATTR.get("max_num_scheduled_tokens", 8192),
              scheduler_config=NS(long_prefill_token_threshold=0),
              mamba_has_prefill_checkpoint_blocks=ATTR.get("mamba_has_prefill_checkpoint_blocks", False),
              mamba_prefill_checkpoint_alignment=ATTR.get("mamba_prefill_checkpoint_alignment"),
              mamba_partial_cache_hit=ATTR.get("mamba_partial_cache_hit", False),
              mamba_fine_grained_prefix_cache=ATTR.get("mamba_fine_grained_prefix_cache", False))

def trace(n, budget=8192):
    s = sched()
    r = NS(num_computed_tokens=0, num_tokens=n, num_prompt_tokens=n, shared_prefix_boundary=0, request_id="x")
    steps = [0]
    while r.num_computed_tokens < n:
        k = split(s, r, min(budget, n - r.num_computed_tokens), 0, 0)
        assert k > 0, (n, steps)
        r.num_computed_tokens += k; steps.append(r.num_computed_tokens)
    return steps

ckpts = lambda st: [p for p in st[1:-1] if p % BS == 0]
print(f"[i] forrás: {SRC}  BS={BS}  attr={ATTR}")
ESETEK = [("T2-01 (D2)", 3169, 3227, "FAIL"), ("D6 eltérő", 3086, 3267, "FAIL"), ("D6 azonos", 3307, 3371, "PASS"),
          ("D3 azonos", 3264, 3346, "PASS"), ("D1 eltérő", 4689, 4870, "PASS"), ("T5-01", 2155, 2182, "PASS"),
          ("T9-01/D5", 24384, 24404, "PASS"),
          ("r8 cella1", 2*BS-19, 2*BS+49, "?"), ("r8 cella2", 2*BS+19, 2*BS+49, "?"),
          ("r8 cella3", 2*BS-101, 2*BS-31, "?"), ("r8 cella4", 2*BS+19, 2*BS-31, "?")]
for cimke, a, b, v029 in ESETEK:
    ta, tb = trace(a), trace(b); ca, cb = ckpts(ta), ckpts(tb)
    j = "FAIL" if (not ca and cb) else "PASS"
    print(f"{cimke:<12} A={a:>6} {str(ta):<28} ckpt={str(ca):<10} B={b:>6} {str(tb):<28} ckpt={str(cb):<12} "
          f"jóslat v030={j:<5} (v029 mért: {v029})")
print("\n--- küszöb ---")
for n in (1600, 3100, 3199, 3200, 3201, 4799, 4800, 4801):
    print(f"  N={n:>5} darabok={trace(n)} ckpt={ckpts(trace(n))}")
