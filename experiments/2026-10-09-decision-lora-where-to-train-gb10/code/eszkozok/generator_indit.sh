#!/usr/bin/env bash
# A generátor (Qwen3.8-Flash-Next-NVFP4) indítása a round8-ban validált recepttel
# (docai-research/qwen3.8-flash-next/round8/eszkozok/indit_r8.sh, K1 image), két eltéréssel:
# --max-model-len 32768 (a generáláshoz elég) és saját port/név. MTP marad: a generátor
# nem az alany, a sebesség számít.
#   generator_indit.sh [NAME] [PORT]
set -euo pipefail
NAME="${1:-ldh-generator}"; PORT="${2:-8410}"
IMAGE="${GEN_IMAGE:-qwen38-flash-dgx:v030-bb661c4}"
SNAP=/hf/hub/models--RadixArk--Qwen3.8-Flash-Next-NVFP4/snapshots/7b719225242aacd3dbd3f9407468c2ee9a9d2594
SPL='["vllm::unified_attention_with_output","vllm::unified_mla_attention_with_output","vllm::mamba_mixer2","vllm::mamba_mixer","vllm::short_conv","vllm::qwen4_exp_ple_short_conv","vllm::qwen4_exp_qsa_with_output","vllm::linear_attention","vllm::qwen_gdn_attention_core","vllm::qwen_gdn_attention_core_fused_norm_packed","vllm::gdn_attention_core_xpu","vllm::olmo_hybrid_gdn_full_forward","vllm::sparse_attn_indexer","vllm::rocm_aiter_sparse_attn_indexer","vllm::deepseek_v4_attention","vllm::hpc_rope_norm_forward","vllm::unified_kv_cache_update","vllm::unified_mla_kv_cache_update","vllm::ple_mmap_lookup_ids"]'
docker rm -f "$NAME" >/dev/null 2>&1 || true
docker run -d --name "$NAME" --gpus all --ipc=host -p "$PORT:8000" \
  -v "$HOME/.cache/huggingface:/hf" \
  -e HF_HUB_OFFLINE=1 -e VLLM_LOGGING_LEVEL=INFO \
  -e VLLM_QSA_DET_LIB=/opt/llm/kernel-det/_C_det.so -e VLLM_QSA_DET_TOPK=1 -e VLLM_QSA_EXACT_TOPK=0 \
  -e VLLM_PLE_MMAP=1 -e VLLM_PLE_MMAP_PREWARM=0 -e VLLM_PLE_MMAP_WORKERS=32 \
  -e VLLM_USE_FLASHINFER_SAMPLER=1 -e VLLM_ALLOW_LONG_MAX_MODEL_LEN=0 \
  "$IMAGE" "$SNAP" \
  --served-model-name qwen38-flash-next-nvfp4 --host 0.0.0.0 --port 8000 \
  --load-format safetensors --max-model-len 32768 --max-num-seqs 4 \
  --gpu-memory-utilization 0.78 \
  --enable-prefix-caching --enable-chunked-prefill --max-num-batched-tokens 8192 \
  -cc.cudagraph_mode=PIECEWISE -cc.splitting_ops="$SPL" \
  --no-enable-flashinfer-autotune --kv-cache-dtype auto \
  --reasoning-parser qwen3 \
  --speculative-config '{"method":"mtp","num_speculative_tokens":2}' >/dev/null
echo "generátor indítva: $NAME port=$PORT image=$IMAGE"
