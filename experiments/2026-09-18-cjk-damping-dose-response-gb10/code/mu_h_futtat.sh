#!/usr/bin/env bash
# F0/4 — a μ_h becslése mindkét próbahalmazon, leválasztva, vLLM token_embed poolinggal.
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
SNAP=<base-snapshot>
IMG=vllm-openai:beta-mirror-dev328
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-MUH"; }

for H in "$@"; do
  say "μ_h becslés: $H halmaz"
  docker run --rm --gpus all --ipc host \
    -v "$HOME/.cache/huggingface:<hf-cache>:ro" \
    -v "$EX:/work" -w /work/eszkozok \
    -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 -e VLLM_USAGE_SOURCE=cjk-f0 \
    --entrypoint python3 "$IMG" \
    mu_h_becslo.py --model "$SNAP" \
      --proba "mu-h-probahalmaz-$H.json" \
      --out "/work/eredmenyek/mu-h-$H.json" > "$EX/naplo/mu-h-$H.log" 2>&1
  rc=$?
  if [ $rc -ne 0 ]; then say "HIBA a $H halmazon (rc=$rc) — leállás"; exit $rc; fi
  say "μ_h $H kész"
done
say "μ_h KÉSZ: $*"
