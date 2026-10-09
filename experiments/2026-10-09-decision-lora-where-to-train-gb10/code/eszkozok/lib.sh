# Közös shell-függvények a measurement-host vezénylőkhöz (source-olva).
# EXP a kísérlet munkakönyvtára; minden lépés idempotens OK-jelölővel.

EXP="${EXP:-$HOME/experiments/2026-10-03-lora-decision-head}"
TOOL_IMAGE="${TOOL_IMAGE:-lora-train:2}"      # NEM :3 — a :3 causal-conv1d-je SIGSEGV-t ad sm_121-en
SUBJECT_IMAGE="${SUBJECT_IMAGE:-vllm/vllm-openai:v0.30.0}"
SUBJECT_MODEL="Qwen/Qwen3.6-35B-A3B-FP8"
SUBJECT_PORT="${SUBJECT_PORT:-8400}"
LORA_TARGETS="q_proj k_proj v_proj o_proj in_proj_qkv in_proj_z in_proj_a in_proj_b out_proj gate_proj up_proj down_proj"

mkdir -p "$EXP"/{logs,eredmenyek,cache,adat,adapters,ckpt}

# --- állapot, heartbeat, ETA ---------------------------------------------
# FAZIS: a vezénylő neve (pl. F0A). STATUS-$FAZIS: utolsó lépés + várható befejezés.
_eta() {  # $1 = hátralévő becsült másodperc
  date -d "@$(( $(date +%s) + ${1:-0} ))" +%H:%M
}
say() {  # say "<üzenet>" [hátralévő_s]
  local msg="$1" rem="${2:-}"
  local line="[$(date '+%F %T')] $msg"
  [ -n "$rem" ] && line="$line · várható befejezés: $(_eta "$rem")"
  echo "$line"
  echo "$line" > "$EXP/STATUS-$FAZIS"
}
heartbeat_start() {
  ( while kill -0 "$1" 2>/dev/null; do date '+%F %T' > "$EXP/HEARTBEAT-$FAZIS"; sleep 60; done ) &
}
done_marker() { [ -f "$EXP/eredmenyek/$FAZIS/.ok/$1" ]; }
mark_ok() { mkdir -p "$EXP/eredmenyek/$FAZIS/.ok"; date '+%F %T' > "$EXP/eredmenyek/$FAZIS/.ok/$1"; }
fail() {
  say "HIBA: $*"
  echo "[$(date '+%F %T')] $*" > "$EXP/FAILED-$FAZIS"
  rm -f "$EXP/AKTIV_FAZIS"
  ldh_cleanup
  exit 1
}

# --- futtatók ------------------------------------------------------------
# py [--gpu] script.py args... — Python a tréning-image-ben, /exp és /hf mountokkal
py() {
  local gpu=()
  if [ "${1:-}" = "--gpu" ]; then gpu=(--gpus all); shift; fi
  docker run --rm "${gpu[@]}" --ipc host --network host --name "ldh-py-$$-$RANDOM" \
    -v "$EXP:/exp" -v "$HOME/.cache/huggingface:/hf:ro" \
    -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e PYTHONUNBUFFERED=1 \
    -w /exp "$TOOL_IMAGE" python3 "$@"
}

# llama_start — Llama-3.3-70B-FP8 bíráló a v2 receptjével (a K0g-ben igazolva), port 8420.
# 0: egészséges · 1: kilépett / memória-abort · 2: időtúllépés. A logot a llama_stop menti.
# LLAMA_SEQS: párhuzamos szekvenciák (alap 4; a rövid páros duplikátum-kérésekhez 16).
llama_start() {
  docker rm -f ldh-llama >/dev/null 2>&1 || true
  mkdir -p "$HOME/.cache/vllm" "$HOME/.cache/flashinfer" "$HOME/.triton"
  docker run -d --name ldh-llama --gpus all -p 8420:8000 --ipc host \
    -v "$HOME/hf-cache-llama33:<hf-cache>" \
    -e HF_HUB_OFFLINE=1 -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False -e RUNAI_STREAMER_MEMORY_LIMIT=4294967296 \
    "$SUBJECT_IMAGE" --model nvidia/Llama-3.3-70B-Instruct-FP8 --served-model-name llama33-70b-fp8 \
    --load-format runai_streamer --kernel-config '{"enable_flashinfer_autotune": false}' --kv-cache-dtype bfloat16 \
    --max-model-len 16384 --gpu-memory-utilization 0.75 --max-num-seqs "${LLAMA_SEQS:-4}" >/dev/null
  local t0; t0=$(date +%s)
  while [ $(( $(date +%s) - t0 )) -lt 2400 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-llama 2>/dev/null)" != "true" ] && return 1
    curl -fsS http://127.0.0.1:8420/health >/dev/null 2>&1 && return 0
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 5 ] && { docker rm -f ldh-llama >/dev/null 2>&1; return 1; }
    sleep 15
  done
  return 2
}

llama_stop() {  # llama_stop <logkönyvtár>
  docker logs ldh-llama > "$1/ldh-llama.log" 2>&1 || true
  docker rm -f ldh-llama >/dev/null 2>&1 || true
}

# mistral_start — Mistral Small 4 119B-A6B NVFP4 bíráló (#2, 2026-10-04), port 8430. A modell Mistral-formátumú
# (params.json + consolidated-*.safetensors, config.json nélkül); az MLA-hoz a README TRITON_MLA-t ajánl.
# A vllm_shim/sitecustomize.py a v0.30.0 image transformers-5.17 importhibáját pótolja (PixtralRotaryEmbedding).
# 0: egészséges · 1: kilépett / memória-abort · 2: időtúllépés. A logot a mistral_stop menti.
# MISTRAL_SEQS: párhuzamos szekvenciák (alap 4).
mistral_start() {
  docker rm -f ldh-mistral >/dev/null 2>&1 || true
  mkdir -p "$HOME/.cache/vllm" "$HOME/.cache/flashinfer" "$HOME/.triton"
  docker run -d --name ldh-mistral --gpus all -p 8430:8000 --ipc host \
    -v "$HOME/hf-cache-mistral4:<hf-cache>" -e HF_HUB_OFFLINE=1 \
    -v "$EXP/eszkozok/vllm_shim:/opt/ldh_shim:ro" -e PYTHONPATH=/opt/ldh_shim \
    "$SUBJECT_IMAGE" --model mistralai/Mistral-Small-4-119B-2603-NVFP4 --served-model-name mistral-small-4 \
    --tokenizer-mode mistral --config-format mistral --load-format mistral --attention-backend TRITON_MLA \
    --reasoning-parser mistral --kernel-config '{"enable_flashinfer_autotune": false}' \
    --max-model-len 16384 --gpu-memory-utilization 0.8 --max-num-seqs "${MISTRAL_SEQS:-4}" >/dev/null
  local t0; t0=$(date +%s)
  while [ $(( $(date +%s) - t0 )) -lt 2700 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-mistral 2>/dev/null)" != "true" ] && return 1
    curl -fsS http://127.0.0.1:8430/health >/dev/null 2>&1 && return 0
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 5 ] && { docker rm -f ldh-mistral >/dev/null 2>&1; return 1; }
    sleep 15
  done
  return 2
}

mistral_stop() {  # mistral_stop <logkönyvtár>
  docker logs ldh-mistral > "$1/ldh-mistral.log" 2>&1 || true
  docker rm -f ldh-mistral >/dev/null 2>&1 || true
}

# vpy script.py args... — Python az ALANY vLLM-image-ében, GPU-val (kernel-egységtesztekhez)
vpy() {
  docker run --rm --gpus all --ipc host --network host --name "ldh-vpy-$$-$RANDOM" \
    -v "$EXP:/exp" -v "$HOME/.cache/huggingface:/hf:ro" \
    -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e PYTHONUNBUFFERED=1 \
    -w /exp --entrypoint python3 "$SUBJECT_IMAGE" "$@"
}

# subject_start NAME — az alany-vLLM indítása a runbook 6. pontja szerint.
# Kapcsolók környezeti változóból: LORA=1 SCALEOUT=1 DEBUG=1 BI=1 AUTOTUNE_OFF=1 PREFIX=0|1
subject_start() {
  local name="$1"
  local env=(-e HF_HUB_OFFLINE=1 -e VLLM_ALLOW_RUNTIME_LORA_UPDATING=True)
  local args=(--max-model-len 8192 --gpu-memory-utilization 0.5 --max-logprobs 64)
  [ "${PREFIX:-0}" = "1" ] && args+=(--enable-prefix-caching) || args+=(--no-enable-prefix-caching)
  [ "${LORA:-1}" = "1" ] && args+=(--enable-lora --max-loras 2 --max-lora-rank 32 --lora-target-modules $LORA_TARGETS)
  [ "${SCALEOUT:-0}" = "1" ] && args+=(--enable-scale-out)
  [ "${AUTOTUNE_OFF:-0}" = "1" ] && args+=(--no-enable-flashinfer-autotune)
  [ "${ASYNC_OFF:-0}" = "1" ] && args+=(--no-async-scheduling)
  [ "${DEBUG:-0}" = "1" ] && env+=(-e VLLM_LOGGING_LEVEL=DEBUG)
  [ "${BI:-0}" = "1" ] && env+=(-e VLLM_BATCH_INVARIANT=1)
  docker rm -f "$name" >/dev/null 2>&1 || true
  docker run -d --name "$name" --gpus all --ipc host -p "$SUBJECT_PORT:8000" \
    -v "$HOME/.cache/huggingface:<hf-cache>" \
    -v "$EXP/adapters:/adapters:ro" \
    "${env[@]}" "$SUBJECT_IMAGE" "$SUBJECT_MODEL" "${args[@]}" >/dev/null
  echo "alany indítva: $name (LORA=${LORA:-1} SCALEOUT=${SCALEOUT:-0} DEBUG=${DEBUG:-0} BI=${BI:-0} AUTOTUNE_OFF=${AUTOTUNE_OFF:-0} ASYNC_OFF=${ASYNC_OFF:-0} PREFIX=${PREFIX:-0})"
}

# subject_wait NAME TIMEOUT_S — 0: egészséges; 1: a konténer kilépett; 2: időtúllépés
subject_wait() {
  local name="$1" to="${2:-1800}" t0
  t0=$(date +%s)
  while [ $(( $(date +%s) - t0 )) -lt "$to" ]; do
    if [ "$(docker inspect -f '{{.State.Running}}' "$name" 2>/dev/null)" != "true" ]; then return 1; fi
    curl -fsS "http://127.0.0.1:$SUBJECT_PORT/health" >/dev/null 2>&1 && return 0
    sleep 10
  done
  return 2
}

subject_stop() {
  local name="$1" logdir="${2:-}"
  [ -n "$logdir" ] && mkdir -p "$logdir" && docker logs "$name" > "$logdir/$name.log" 2>&1 || true
  docker rm -f "$name" >/dev/null 2>&1 || true
}

ldh_cleanup() {
  for c in $(docker ps -aq --filter name='^ldh-'); do docker rm -f "$c" >/dev/null 2>&1 || true; done
}

record_env() {  # jegyzőkönyv-sor: image digest, snapshot, idő
  {
    echo "== $(date '+%F %T') $FAZIS"
    echo "subject_image: $(docker image inspect "$SUBJECT_IMAGE" --format '{{index .RepoDigests 0}}' 2>/dev/null)"
    echo "tool_image: $(docker image inspect "$TOOL_IMAGE" --format '{{.Id}}' 2>/dev/null)"
    echo "subject_snapshot: 95a723d08a9490559dae23d0cff1d9466213d989"
  } >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
}
