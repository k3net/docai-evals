#!/usr/bin/env python3
"""Miért hal meg a forward pass? Lépésenként, faulthandlerrel.

    bash ~/lang-study/src/run_spark.sh -X faulthandler src/debug_forward.py --conv-off
"""
import argparse, faulthandler, time
faulthandler.enable()
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import gb10_patch

MODEL = "Qwen/Qwen3.5-9B-Base"
ap = argparse.ArgumentParser()
ap.add_argument("--conv-off", action="store_true")
ap.add_argument("--fla-off", action="store_true")
args = ap.parse_args()

def s(m): print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

if args.conv_off or args.fla_off:
    gb10_patch.patch(conv=args.conv_off, fla=args.fla_off)

tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16).to("cuda").eval()
s("modell betöltve")

enc = tok("Question: What is the capital of France?\nAnswer:", return_tensors="pt").to("cuda")
t0 = time.time()
with torch.no_grad():
    out = model(**enc)
s(f"1) forward OK {time.time()-t0:.1f}s — logits {tuple(out.logits.shape)}")

with torch.no_grad():
    out = model(**enc, output_hidden_states=True)
s(f"2) hidden_states OK — {len(out.hidden_states)} elem, dtype {out.hidden_states[0].dtype}")

cap = {}
h = model.model.layers[0].register_forward_hook(
    lambda m, i, o: cap.__setitem__("x", (o[0] if isinstance(o, tuple) else o).detach()))
with torch.no_grad():
    model(**enc)
h.remove()
s(f"3) hook OK — {tuple(cap['x'].shape)}")

t0 = time.time()
with torch.no_grad():
    g = model.generate(**enc, max_new_tokens=20, do_sample=False,
                       pad_token_id=tok.pad_token_id or tok.eos_token_id)
s(f"4) generate OK {time.time()-t0:.1f}s — {tok.decode(g[0][enc['input_ids'].shape[1]:], skip_special_tokens=True)!r}")
s("MINDEN LÉPÉS OK")
