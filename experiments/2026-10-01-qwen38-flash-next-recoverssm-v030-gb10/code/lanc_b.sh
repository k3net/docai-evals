#!/usr/bin/env bash
# B fázis mérési lánc egy karra: M1 prefix reuse -> M2 checkpoint 4 cella -> M2 cache vs hideg
#   lanc_b.sh KAR PORT [BLOKK]
set -uo pipefail
KAR=$1; PORT=$2; B=${3:-1600}; U=http://localhost:$PORT; M=qwen38-flash-next-nvfp4; K=$HOME/round7/kie
cd ~/experiments/round8; E=eredmenyek; MAG=$KAR-$(date +%H%M%S)
echo "== $KAR M1 $(date -Is)"; python3 eszkozok/prefix_reuse_szonda.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M1-$KAR.json
echo "== $KAR M2a $(date -Is)"; python3 eszkozok/checkpoint_szonda.py --url $U --model $M --korpusz $K --doc D6 --blokkmeret $B --ismetles 4 --cellak 1,2,3,4,5 --mag $MAG --cimke $KAR --out $E/M2a-$KAR.json
echo "== $KAR M2s $(date -Is)"; python3 eszkozok/checkpoint_szonda.py --url $U --model $M --korpusz $K --doc D6 --blokkmeret $B --ismetles 4 --parok $(cat eszkozok/sweep_parok.txt) --mag ${MAG}sw --cimke $KAR-sweep --out $E/M2s-$KAR.json
echo "== $KAR M2b $(date -Is)"; python3 eszkozok/cache_vs_ujra.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M2b-$KAR.json
echo "== $KAR KESZ $(date -Is)"
