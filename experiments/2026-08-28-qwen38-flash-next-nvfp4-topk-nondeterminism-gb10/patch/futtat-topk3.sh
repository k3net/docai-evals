#!/usr/bin/env bash
# Teljes validacio a 3. moddal (torch.topk + kanonikus rendezes, VLLM_QSA_EXACT_TOPK=3):
# fo suite 50x3 FRISSEN (nem --folytat!), nehez 10x3, HU-CH challenge, hosszu 5x1.
# Cel: a 297/300 validalasa determinisztikus prefillel + az MTP-s ures elszallas (16 384 tok) eltunese.
set -x
cd .
U="http://localhost:18380"; M="qwen3.8-flash-next"; C="flash-nvfp4-topk3"
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --cimke $C --futasok 3 --out reports/meres-$C.json
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --items gt/items-nehez.jsonl --cimke nehez-$C --futasok 3 --out reports/nehez-$C.json
python3 src/challenge_hu.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --cimke $C --forras ./magyar_nyelvertes_challenge_eval_v0.1.md --out reports/challenge__$C.json
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 5400 \
  --items gt/items-hosszu.jsonl --cimke hosszu-$C --futasok 1 --out reports/hosszu-$C.json
echo "=== TOPK3 MIND A NEGY SUITE LEFUTOTT ==="
