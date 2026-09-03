#!/usr/bin/env bash
# GDN FP32-beta kiserlet, MTP=0 fazis (a packed_decode kernel CSAK spec-decode nelkul fut):
#  restart beta image MTP=0 -> T14-01 3x + challenge 3x -> fo suite 50x1 (referencia: meres-flash-nvfp4-topk3-mtp0.json 97 pont).
set -x
cd ~/eval && ARM=topk3mtp0 SKIP_EVAL=1 ./izolacio-beta.sh > ~/eval/beta-restart-mtp0.log 2>&1
cd ~/eval/magyar-kie-eval
U="http://localhost:18380"; M="qwen3.8-flash-next"
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --items gt/items-runaway.jsonl --cimke runaway-beta-mtp0 --futasok 3 --out reports/runaway-beta-mtp0.json
python3 src/challenge_hu.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --cimke runaway-beta-mtp0 --forras ~/eval/magyar_nyelvertes_challenge_eval_v0.1.md \
  --out reports/challenge__runaway-beta-mtp0.json
python3 src/harness.py --url $U --model $M --max-tokens 16384 --timeout 3600 \
  --cimke flash-nvfp4-topk3-beta-mtp0 --futasok 1 --out reports/meres-flash-nvfp4-topk3-beta-mtp0.json
echo "=== BETA MTP0 KESZ ==="
