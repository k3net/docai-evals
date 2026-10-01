#!/usr/bin/env bash
# C fázis lánc egy karra.  lanc_c.sh KAR PORT MOD   (MOD = teljes | perf)
set -uo pipefail
KAR=$1; PORT=$2; MOD=${3:-teljes}; U=http://localhost:$PORT; M=qwen38-flash-next-nvfp4; K=$HOME/round7/kie
cd ~/experiments/round8; E=eredmenyek; MAG=$KAR-$(date +%H%M%S)
B=$(python3 -c "import json,glob,sys; print(next(json.loads(l)[\"block_size\"] for f in glob.glob(\"trace/$KAR/*.jsonl\") for l in open(f) if json.loads(l)[\"ev\"]==\"init\"))")
PAROK=$(python3 -c "B=$B; print(\",\".join(f\"{2*B+o}:{2*B+61}\" for o in (-30,-23,-16,-9,-2,5,19)) + \",\" + \",\".join(f\"{3*B+o}:{2*B+61}\" for o in (8,15,36)))")
echo "[i] $KAR blokk=$B parok=$PAROK"
if [ "$MOD" = teljes ]; then
echo "== $KAR M1 $(date -Is)"; python3 eszkozok/prefix_reuse_szonda.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M1-$KAR.json
echo "== $KAR M2a $(date -Is)"; python3 eszkozok/checkpoint_szonda.py --url $U --model $M --korpusz $K --doc D6 --blokkmeret $B --ismetles 4 --cellak 1,2,3,4,5 --mag $MAG --cimke $KAR --out $E/M2a-$KAR.json
echo "== $KAR M2s $(date -Is)"; python3 eszkozok/checkpoint_szonda.py --url $U --model $M --korpusz $K --doc D6 --blokkmeret $B --ismetles 4 --parok $PAROK --mag ${MAG}sw --cimke $KAR-sweep --out $E/M2s-$KAR.json
echo "== $KAR M2b $(date -Is)"; python3 eszkozok/cache_vs_ujra.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M2b-$KAR.json
echo "== $KAR M3h $(date -Is)"; python3 eszkozok/hatar_sweep.py --blokk $B --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M3h-$KAR.json
echo "== $KAR M3ny $(date -Is)"; python3 eszkozok/nyelv_stressz.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M3ny-$KAR.json | tail -1
fi
if [ "$KAR" = K2off-2 ]; then echo "== $KAR M3ny $(date -Is)"; python3 eszkozok/nyelv_stressz.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M3ny-$KAR.json | tail -1; fi
echo "== $KAR M6 $(date -Is)"; python3 eszkozok/perf_szonda.py --url $U --model $M --korpusz $K --mag $MAG --cimke $KAR --out $E/M6-$KAR.json
echo "== $KAR KESZ $(date -Is)"
