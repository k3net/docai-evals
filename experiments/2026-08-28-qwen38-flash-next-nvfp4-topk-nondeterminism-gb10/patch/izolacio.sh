#!/bin/bash
# NVFP4 nemdeterminizmus-izolacio a the dev DGX Spark-en.
#
# Alaphelyzet (MERT): a fo suite 50 itemjebol 13 ingadozik temperature 0-n,
# 3 futas mellett. Referenciak ugyanezen az itemsoron: IQ4_XS/llama.cpp 0/50,
# prod 35B/vLLM ugyanilyen MTP=2-vel 0/50.
#
# A kiserlet CSAK a 13 ismerten instabil itemet futtatja, de 5 futassal --
# vagyis a kezelt ag NAGYOBB eszlelesi erovel bir, mint a baseline. Egy 0/13
# eredmeny igy konzervativ bizonyitek, nem kisebb mintabol jovo hamis nyugalom.
#
# Egyszerre EGY valtozo mozdul. Minden mas bitre azonos a baseline-nal.
#   ARM=mtp0    -> nincs --speculative-config      (1. gyanusitott)
#   ARM=cgnone  -> -cc.cudagraph_mode=NONE         (2. gyanusitott)
#   ARM=w1      -> VLLM_PLE_MMAP_WORKERS=1         (3. gyanusitott, leggyengebb)
#   ARM=topk    -> qwen38-flash-dgx-topk image + VLLM_QSA_EXACT_TOPK=1: a QSA persistent_topk
#                  (atomicAdd, GB10-en ez fut) helyett egzakt, kanonikus torch top-k (4. gyanusitott)
set -euo pipefail
ARM="${ARM:?adj meg ARM-et: mtp0 | cgnone | w1}"
PORT=18380
EVAL=.
BASE=$EVAL/reports/meres-flash-nvfp4.json
OUT=$EVAL/reports/izo-$ARM.json
ITEMS=$EVAL/gt/items-izo.jsonl

cd "$EVAL"

# --- 1. A 13 instabil item kiszurese a baseline riportbol -------------------
python3 - "$BASE" "$ITEMS" <<'PY'
import json, sys
base, ki = sys.argv[1], sys.argv[2]
d = json.load(open(base))
ids = [e["id"] for e in d["eredmenyek"] if e.get("instabil")]
assert ids, "nincs instabil item a baseline-ban - rossz fajl?"
sor = {json.loads(l)["id"]: l for l in open("gt/items.jsonl") if l.strip()}
hiany = [i for i in ids if i not in sor]
assert not hiany, f"nem talalt item: {hiany}"
with open(ki, "w") as f:
    for i in ids:
        f.write(sor[i])
print(f"[i] {len(ids)} instabil item: {', '.join(ids)}")
PY

# --- 2. Szerver ujrainditasa az adott aggal ---------------------------------
SPLIT='["vllm::unified_attention_with_output","vllm::unified_mla_attention_with_output","vllm::mamba_mixer2","vllm::mamba_mixer","vllm::short_conv","vllm::qwen3_8_flash_next_ple_short_conv","vllm::qwen3_8_flash_next_qsa_with_output","vllm::linear_attention","vllm::qwen_gdn_attention_core","vllm::qwen_gdn_attention_core_fused_norm_packed","vllm::sparse_attn_indexer","vllm::ple_mmap_lookup"]'
CC="-cc.cudagraph_mode=PIECEWISE -cc.splitting_ops=$SPLIT"
SPEC='--speculative-config {"method":"mtp","num_speculative_tokens":2}'
WORKERS=32
IMAGE=qwen38-flash-dgx
EXACT=0
case "$ARM" in
  topk)   IMAGE=qwen38-flash-dgx-topk; EXACT=1 ;;
  topk2)  IMAGE=qwen38-flash-dgx-topk; EXACT=2 ;;
  topk3)  IMAGE=qwen38-flash-dgx-topk; EXACT=3 ;;
  mtp0)   SPEC="" ;;
  cgnone) CC="-cc.cudagraph_mode=NONE" ;;
  w1)     WORKERS=1 ;;
  *) echo "ismeretlen ARM: $ARM" >&2; exit 1 ;;
esac

SNAP=$(ls -d ~/.cache/huggingface/hub/models--RadixArk--Qwen3.8-Flash-Next-NVFP4/snapshots/*/ | head -1)
SNAP_IN="/hf/hub/models--RadixArk--Qwen3.8-Flash-Next-NVFP4/snapshots/$(basename "$SNAP")"

docker rm -f qwen38-flash >/dev/null 2>&1 || true
# shellcheck disable=SC2086
docker run -d --name qwen38-flash --gpus all --ipc=host --shm-size 16g -p "${PORT}:8000" \
  -v ~/.cache/huggingface:/hf -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 \
  -e VLLM_PLE_MMAP=1 -e VLLM_PLE_MMAP_WORKERS=$WORKERS -e VLLM_PLE_MMAP_PREWARM=1 \
  -e VLLM_USE_FLASHINFER_SAMPLER=1 -e VLLM_QSA_EXACT_TOPK=$EXACT \
  "$IMAGE" \
  "$SNAP_IN" --served-model-name qwen3.8-flash-next \
    --host 0.0.0.0 --port 8000 --load-format safetensors \
    --max-model-len 262144 --max-num-seqs 2 --gpu-memory-utilization 0.78 \
    --no-enable-prefix-caching --enable-chunked-prefill --max-num-batched-tokens 8192 \
    $CC --no-enable-flashinfer-autotune \
    --enable-auto-tool-choice --tool-call-parser qwen3_coder --reasoning-parser qwen3 \
    $SPEC

# --- 3. Varakozas keszenletre -- `curl -sf`, mert a 503 NEM siker -----------
echo "[i] $ARM: varakozas a szerverre..."
for i in $(seq 1 90); do
  if curl -sf "http://localhost:$PORT/v1/models" >/dev/null 2>&1; then
    echo "[i] kesz $((i*20)) mp utan"; break
  fi
  [ "$i" = 90 ] && { echo "!! nem indult el 30 perc alatt"; docker logs --tail 40 qwen38-flash; exit 1; }
  sleep 20
done

# --- 4. Meres: 13 item x 5 futas (SKIP_EVAL=1 -> csak a szerver indul) ----------
if [ "${SKIP_EVAL:-0}" = 1 ]; then echo "=== IZOLACIO KESZ: $ARM (csak szerver) ==="; exit 0; fi
python3 src/harness.py --url "http://localhost:$PORT" --model qwen3.8-flash-next \
  --max-tokens 16384 --timeout 3600 --items "$ITEMS" \
  --cimke "izo-$ARM" --futasok 5 --out "$OUT"

echo "=== IZOLACIO KESZ: $ARM ==="
