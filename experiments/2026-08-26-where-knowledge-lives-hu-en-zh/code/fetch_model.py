#!/usr/bin/env python3
"""Modell előtöltése a HF gyorsítótárba (spark-dev, konténer).

    bash ~/lang-study/code/run_spark.sh code/fetch_model.py Qwen/Qwen3.5-9B

Külön szkript, hogy a letöltés a méréstől FÜGGETLENÜL, előre elvégezhető legyen —
a `from_pretrained` első hívása különben a mérés óráján töltene 19 GB-ot.
A vision-ágat nem hagyjuk ki: a Qwen3.5 config `text_config`-ot használ, és a
`AutoModelForCausalLM` a teljes súlytérképet várja.
"""
import sys
from huggingface_hub import snapshot_download

repo = sys.argv[1] if len(sys.argv) > 1 else "Qwen/Qwen3.5-9B"
p = snapshot_download(repo, allow_patterns=["*.json", "*.safetensors", "*.jinja", "*.txt", "*.model"],
                      max_workers=4)
print(f"kész → {p}")
