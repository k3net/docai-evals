#!/usr/bin/env bash
# 03 F2g — Gemma 4 26B-A4B-it tanárjelölt smoke a spark-deven (03-runbook 8. pont, előre hozva; Dani, 2026-10-09).
# Boot (memória, időtartam) → tanar_smoke.py a vLLM-image-ben → leállítás, log. Leválasztva indítandó:
#   nohup setsid bash kor03/eszkozok/f2g_smoke.sh > logs/f2g_smoke.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
cd "$EXP"
IMAGE="vllm/vllm-openai:v0.30.0"
R="$EXP/kor03/eredmenyek/F2g"
mkdir -p "$R" "$HOME/.cache/vllm" "$HOME/.cache/flashinfer" "$HOME/.triton"
SNAP=$(ls -d "$HOME"/hf-cache-gemma4/models--google--gemma-4-26B-A4B-it/snapshots/* | head -1)
SNAP_IN="/hfg/models--google--gemma-4-26B-A4B-it/snapshots/$(basename "$SNAP")"
say() { echo "$(date '+%F %T') $*" | tee -a "$R/f2g.log"; }

for c in $(docker ps -q); do say "FUT MÁS KONTÉNER: $(docker inspect -f '{{.Name}}' "$c") — leállok"; exit 3; done
say "start; snapshot $(basename "$SNAP"); image $(docker image inspect "$IMAGE" --format '{{index .RepoDigests 0}}')"
free -g | sed -n 2p | tee -a "$R/f2g.log"
docker rm -f ldh-gemma4 >/dev/null 2>&1 || true
T0=$(date +%s)
docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
  -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
  "$IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
  --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 8 --max-logprobs 64 \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null
ok=2
while [ $(( $(date +%s) - T0 )) -lt 2700 ]; do
  [ "$(docker inspect -f '{{.State.Running}}' ldh-gemma4 2>/dev/null)" != "true" ] && { ok=1; break; }
  curl -fsS http://127.0.0.1:8440/health >/dev/null 2>&1 && { ok=0; break; }
  [ "$(free -g | awk 'NR==2{print $7}')" -lt 5 ] && { say "memória-abort"; ok=1; break; }
  sleep 15
done
say "boot: kód $ok, $(( $(date +%s) - T0 )) s"
free -g | sed -n 2p | tee -a "$R/f2g.log"
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader | tee -a "$R/f2g.log"
if [ "$ok" = "0" ]; then
  docker run --rm --network host --entrypoint python3 \
    -v "$EXP:/exp" -v "$HOME/hf-cache-gemma4:/hfg:ro" -e HF_HUB_OFFLINE=1 -e PYTHONUNBUFFERED=1 -w /exp \
    "$IMAGE" kor03/eszkozok/tanar_smoke.py --tokenizer "$SNAP_IN" --out kor03/eredmenyek/F2g/smoke.json \
    2>&1 | tee -a "$R/f2g.log"
  say "smoke vége: kód ${PIPESTATUS[0]}"
fi
docker logs ldh-gemma4 > "$R/ldh-gemma4.log" 2>&1 || true
docker rm -f ldh-gemma4 >/dev/null 2>&1 || true
say "kész"
touch "$R/DONE"
