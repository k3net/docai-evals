#!/usr/bin/env bash
# Round8 kar-indítás: a round7 indit_r7.sh prod-azonos flagjei + v0.30-as splitting-lista + opcionális
# retention-intervallum + a scheduler-trace overlay (csak naplóz, viselkedést nem módosít).
#   indit_r8.sh IMAGE NAME PORT
# env:
#   SPLIT=v029|v030       a splitting-op lista (v0.29: qwen4_exp_compute_ple_ngram_ids; v0.30: blazux bb661c4 serve.sh)
#   RETENTION=<int|None>  ha meg van adva: --prefix-cache-retention-interval RETENTION (üres = nincs flag)
#   TRACE_DIR=<host dir>  ha meg van adva: r8trace overlay (.pth) + JSONL a TRACE_DIR-be
#   CG_MODE               cudagraph mód (alap: PIECEWISE)
#   EXTRA_ARGS            további vllm argumentumok
set -euo pipefail
IMAGE="${1:?image}"; NAME="${2:?nev}"; PORT="${3:?port}"
SNAP=/hf/hub/models--RadixArk--Qwen3.8-Flash-Next-NVFP4/snapshots/7b719225242aacd3dbd3f9407468c2ee9a9d2594
HERE="$(cd "$(dirname "$0")" && pwd)"
SPLIT_V029='["vllm::unified_attention_with_output","vllm::unified_mla_attention_with_output","vllm::mamba_mixer2","vllm::mamba_mixer","vllm::short_conv","vllm::qwen4_exp_compute_ple_ngram_ids","vllm::qwen4_exp_ple_short_conv","vllm::qwen4_exp_qsa_with_output","vllm::linear_attention","vllm::qwen_gdn_attention_core","vllm::qwen_gdn_attention_core_fused_norm_packed","vllm::sparse_attn_indexer","vllm::ple_mmap_lookup_ids"]'
SPLIT_V030='["vllm::unified_attention_with_output","vllm::unified_mla_attention_with_output","vllm::mamba_mixer2","vllm::mamba_mixer","vllm::short_conv","vllm::qwen4_exp_ple_short_conv","vllm::qwen4_exp_qsa_with_output","vllm::linear_attention","vllm::qwen_gdn_attention_core","vllm::qwen_gdn_attention_core_fused_norm_packed","vllm::gdn_attention_core_xpu","vllm::olmo_hybrid_gdn_full_forward","vllm::sparse_attn_indexer","vllm::rocm_aiter_sparse_attn_indexer","vllm::deepseek_v4_attention","vllm::hpc_rope_norm_forward","vllm::unified_kv_cache_update","vllm::unified_mla_kv_cache_update","vllm::ple_mmap_lookup_ids"]'
case "${SPLIT:-v030}" in v029) SPL="$SPLIT_V029" ;; v030) SPL="$SPLIT_V030" ;; *) echo "SPLIT=v029|v030"; exit 1 ;; esac
RET=(); [ -n "${RETENTION:-}" ] && RET=(--prefix-cache-retention-interval "$RETENTION")
TR=()
if [ -n "${TRACE_DIR:-}" ]; then
  mkdir -p "$TRACE_DIR"; chmod 777 "$TRACE_DIR"
  TR=(-v "$HERE/r8trace.py:/usr/local/lib/python3.12/dist-packages/r8trace.py:ro"
      -v "$HERE/r8trace.pth:/usr/local/lib/python3.12/dist-packages/r8trace.pth:ro"
      -v "$TRACE_DIR:/r8trace" -e R8_TRACE=/r8trace)
fi
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" --gpus all --ipc=host -p "$PORT:8000" \
  -v "$HOME/.cache/huggingface:/hf" \
  -e VLLM_LOGGING_LEVEL=INFO \
  -e VLLM_QSA_DET_LIB=/opt/llm/kernel-det/_C_det.so -e VLLM_QSA_DET_TOPK=1 -e VLLM_QSA_EXACT_TOPK=0 \
  -e VLLM_PLE_MMAP=1 -e VLLM_PLE_MMAP_PREWARM=0 -e VLLM_PLE_MMAP_WORKERS=32 \
  -e VLLM_USE_FLASHINFER_SAMPLER=1 -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=0 \
  "${TR[@]}" \
  "$IMAGE" "$SNAP" \
  --served-model-name qwen38-flash-next-nvfp4 --host 0.0.0.0 --port 8000 \
  --load-format safetensors --max-model-len 262144 --max-num-seqs 4 \
  --gpu-memory-utilization 0.78 \
  --enable-prefix-caching --enable-chunked-prefill --max-num-batched-tokens 8192 \
  "${RET[@]}" \
  -cc.cudagraph_mode="${CG_MODE:-PIECEWISE}" \
  -cc.splitting_ops="$SPL" \
  --no-enable-flashinfer-autotune --kv-cache-dtype auto \
  --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
  --enable-prompt-tokens-details \
  ${EXTRA_ARGS:-} \
  --speculative-config '{"method":"mtp","num_speculative_tokens":2}'
echo "elindult: $NAME port=$PORT image=$IMAGE split=${SPLIT:-v030} retention=${RETENTION:-<nincs>} trace=${TRACE_DIR:-<nincs>} cg=${CG_MODE:-PIECEWISE} extra=${EXTRA_ARGS:-}"
