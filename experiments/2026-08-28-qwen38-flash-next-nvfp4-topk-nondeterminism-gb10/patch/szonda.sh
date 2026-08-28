#!/bin/bash
# Prefill-szonda az eppen elo szerveren (nincs restart). Csak izolacios kor UTAN futtasd.
cd .
python3 src/prefill_szonda.py --url http://localhost:18380 --model qwen3.8-flash-next \
  --ismetles 10 --top 20 --cimke "$1" --out "reports/szonda-$1.json" 2>&1 | tee ./szonda-$1.log
