#!/usr/bin/env bash
# ⛔ Az elso kor CTX=32768-cal ment: a 24 440 tokenes D5-itemek + 16 384 valaszkeret
# = 40 824 token > 32 768 → a vLLM HTTP 400-zal dobta mind a 30 kerest (T9, T10).
# Most CTX=262144, KV 444 311 token. A --folytat csak a hianyzokat futtatja.
set -x
cd .
U="http://localhost:18380"; M="qwen3.8-flash-next"
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --cimke flash-nvfp4 --futasok 3 --folytat --out reports/meres-flash-nvfp4.json
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --items gt/items-nehez.jsonl --cimke nehez-flash-nvfp4 --futasok 3 --folytat \
  --out reports/nehez-flash-nvfp4.json
python3 src/challenge_hu.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --cimke flash-nvfp4 --folytat --forras ./magyar_nyelvertes_challenge_eval_v0.1.md \
  --out reports/challenge__flash-nvfp4.json
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 5400 \
  --items gt/items-hosszu.jsonl --cimke hosszu-flash-nvfp4 --futasok 1 --folytat \
  --out reports/hosszu-flash-nvfp4.json
echo "=== NVFP4 MIND A NEGY SUITE LEFUTOTT ==="
