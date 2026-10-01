#!/usr/bin/env bash
# egy C-fázisú kar: indítás, várakozás, boot-napló, lánc, leállítás.   kar_c.sh KAR PORT MOD [EXTRA_ARGS...]
set -uo pipefail
KAR=$1; PORT=$2; MOD=$3; shift 3
cd ~/experiments/round8
EXTRA_ARGS="$*" SPLIT=v030 TRACE_DIR=$HOME/experiments/round8/trace/$KAR ./eszkozok/indit_r8.sh qwen38-flash-dgx:v030-bb661c4-rssm58863 r8-$KAR $PORT
T0=$(date +%s)
for i in $(seq 1 180); do
  curl -sf localhost:$PORT/v1/models >/dev/null && break
  docker ps --format "{{.Names}}" | grep -q "^r8-$KAR\$" || { echo "HALOTT"; docker logs --tail 80 r8-$KAR > eredmenyek/naplok/$KAR-container.log 2>&1; exit 1; }
  sleep 5
done
echo "boot: $(( $(date +%s) - T0 )) s"
docker logs r8-$KAR 2>&1 | grep -i -e "Model Runner" -e QSADET -e "block size" -e "GPU KV cache size" -e "Graph capturing finished" -e "Available KV cache memory" -e "Actual usage is" -e recoverssm -e replayssm -e "cudagraph_mode\|CUDAGraphMode" -e "draft model" | cut -c1-400 > eredmenyek/$KAR-boot.txt
./eszkozok/lanc_c.sh $KAR $PORT $MOD
docker logs r8-$KAR > eredmenyek/naplok/$KAR-container.log 2>&1
docker stop r8-$KAR >/dev/null; docker rm r8-$KAR >/dev/null
