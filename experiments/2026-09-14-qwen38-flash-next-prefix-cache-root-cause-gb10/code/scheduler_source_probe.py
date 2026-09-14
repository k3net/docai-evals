#!/usr/bin/env python3
"""CPU-forrásszonda (round4): a SPARK-DEV-en FUTÓ v0.29 image scheduler-forrásából kiemelt
_mamba_block_aligned_split lefuttatása a round3-ban ténylegesen mért prompt-hosszakra.
Kérdés: melyik kérés ír 1600-as Mamba-checkpointot, és ez megjósolja-e a PASS/FAIL-t?"""
import ast, copy, sys
from types import SimpleNamespace as NS
from pathlib import Path

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "v029/scheduler.py")
BS = 1600

def extract(path, cls, name):
    tree = ast.parse(path.read_text())
    c = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    f = copy.deepcopy(next(n for n in c.body if isinstance(n, ast.FunctionDef) and n.name == name))
    f.decorator_list = []
    return f

node = extract(SRC, "Scheduler", "_mamba_block_aligned_split")
src = ast.unparse(node)
# a #54076 szűk szemantikai backportja (a doksi 8/C szerint)
fixed_src = src.replace("next_block_boundary if start % block_size != 0 else 0",
                        "0 if use_internal_checkpoint else next_block_boundary")
assert fixed_src != src, "a javítandó sor nem található — a forrás eltér"

def compile_fn(s):
    env = {}
    exec(compile(ast.parse("from __future__ import annotations\n" + s), "<image-source>", "exec"), env)
    return env["_mamba_block_aligned_split"]

base, fixed = compile_fn(src), compile_fn(fixed_src)

def trace(n, fn, start=0, budget=8192):
    s = NS(cache_config=NS(block_size=16), block_size=BS, use_eagle=True,
           max_num_scheduled_tokens=budget,
           scheduler_config=NS(long_prefill_token_threshold=0),
           mamba_has_prefill_checkpoint_blocks=False, mamba_partial_cache_hit=False,
           hash_block_size=BS)
    r = NS(num_computed_tokens=start, num_tokens=n, num_prompt_tokens=n, shared_prefix_boundary=0)
    steps = [start]
    while r.num_computed_tokens < n:
        c = fn(s, r, min(budget, n - r.num_computed_tokens))
        assert c > 0
        r.num_computed_tokens += c
        steps.append(r.num_computed_tokens)
    return steps

def ckpts(steps):  # blokkhatáron végződő darabok = menthető állapot
    return [p for p in steps[1:-1] if p % BS == 0]

ESETEK = [  # (címke, A prompt_tok, B prompt_tok, mért eredmény)
    ("T2-01 (D2)",        3169, 3227, "FAIL"),
    ("D6 eltérő",         3086, 3267, "FAIL"),
    ("D6 azonos",         3307, 3371, "PASS"),
    ("D3 azonos (B kar)", 3264, 3346, "PASS"),
    ("D1 eltérő",         4689, 4870, "PASS"),
    ("T5-01",             2155, 2182, "PASS"),
    ("T4-01 (tiszta)",    1859, 1859, "PASS"),
    ("T9-01/D5",         24384, 24404, "PASS"),
]

print(f"{'eset':<20} {'A':>6} {'A-darabok':<22} {'A-ckpt':<8} {'B':>6} {'B-darabok':<22} {'B-ckpt':<8} "
      f"{'jóslat':<6} {'mért':<5} egyezik")
hit = 0
for cimke, a, b, mert in ESETEK:
    ta, tb = trace(a, base), trace(b, base)
    ca, cb = ckpts(ta), ckpts(tb)
    # hipotézis: FAIL <=> A NEM ír közös checkpointot, de B igen (vegyes eredetű visszaolvasás)
    joslat = "FAIL" if (not ca and cb) else "PASS"
    ok = joslat == mert
    hit += ok
    print(f"{cimke:<20} {a:>6} {str(ta):<22} {str(ca):<8} {b:>6} {str(tb):<22} {str(cb):<8} "
          f"{joslat:<6} {mert:<5} {'IGEN' if ok else '**NEM**'}")
print(f"\nEgyezés: {hit}/{len(ESETEK)}")

print("\n--- Ugyanez a HATÁRMEGÁLLÍTÁSOS javítással (#54076 szűk backport) ---")
for cimke, a, b, mert in ESETEK:
    ta, tb = trace(a, fixed), trace(b, fixed)
    ca, cb = ckpts(ta), ckpts(tb)
    joslat = "FAIL" if (not ca and cb) else "PASS"
    print(f"{cimke:<20} {a:>6} {str(ta):<30} {str(ca):<20} B-ckpt={str(cb):<20} jóslat={joslat}")

print("\n--- Küszöb: mekkora A-hossztól születik közös checkpoint? ---")
for n in (1600, 3100, 3199, 3200, 3201, 3300, 4800):
    print(f"  A={n:>6}  darabok={trace(n, base)}  ckpt={ckpts(trace(n, base))}")
