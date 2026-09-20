#!/usr/bin/env bash
# PÉLDÁNY-SOROZAT / BI — a batch-invariáns mód TRITON_ATTN backenddel.
#
# Az első sorozat (peldany_sorozat.sh) eredménye: 4 sima példány → 3 különböző
# kimenet-mintázat a 17 itemen; a VLLM_BATCH_INVARIANT=1 példányok el sem indultak,
# mert a mód explicit FLASH_ATTN/TRITON_ATTN backendet követel (a FlashInfer-t nem
# támogatja). Itt: két BI példány `--attention-backend TRITON_ATTN`-nel, a másodikon a
# 12 igazoló item parallel=6-tal is — a mód épp a kötegfüggetlenséget ígéri.
# ⚠️ Ez MOTORVÁLTÁS (attention backend + kernelrögzítés): ha beválik, a K0-t és az F1
# karokat ezen az úton újra kell mérni, mielőtt az F2 rá épül (runbook §9).
# Eredeti fejléc:
#
# ⛔ 2026-09-19: a friss-példányos igazolás MEGBUKOTT: két soros K0-példány között
# 5/150 item PASS/FAIL-je eltér (C9-09, T3-02, T3-03, T3-05, T7-08), miközben egy
# példányon belül 150/150 (és meleg cache-sel 17/17) bájtra azonos. A karok
# összevetése mindig két példány között történik, tehát ez a zaj a mérésben benne
# van, és nem a modellből jön. Mielőtt a §5 margóját újragondolnánk: mekkora, és
# megszüntethető-e?
#
# Négy friss példány, mindegyiken ugyanaz a 17 item sorosan (a 12 igazoló + az 5 billenő):
#   inst3, inst4: sima beta-build (mint eddig)           → mekkora a példány-zaj?
#   inst5, inst6: VLLM_BATCH_INVARIANT=1                  → megszünteti-e?
# A batch-invariant mód a kernelválasztást rögzíti (autotuning ki, köteg-invariáns
# redukciók). Ha inst5 ≡ inst6 bájtra, VAN determinisztikus mérési út — de az ENGINE
# más, tehát a round5-összevetés hozzá újra kell (runbook §9: a motorbuild konfundál).
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
SNAP=<base-snapshot>
IMG=vllm-openai:beta-mirror-dev328
URL=http://127.0.0.1:18355
ITEMS=T1-01,T2-01,T5-01,T7-08,T9-01,T10-01,C1-01,C2-02,C5-03,C6-01,C7-01,C9-02,C9-09,C9-11,T3-02,T3-03,T3-05
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-PELDANY"; }
VLLM_EXTRA="--attention-backend TRITON_ATTN"
VALID=T1-01,T2-01,T5-01,T7-08,T9-01,T10-01,C1-01,C2-02,C5-03,C6-01,C7-01,C9-02

inditas() {  # <cimke> <extra docker env...>
  local cimke="$1"; shift
  docker rm -f cjk-kiszolgalo >/dev/null 2>&1 || true
  say "$cimke — példány indul"
  docker run -d --name cjk-kiszolgalo --gpus all --ipc host -p 127.0.0.1:18355:8000 \
    -v "$HOME/.cache/huggingface:<hf-cache>" -v "$EX:/work" \
    -e VLLM_USAGE_SOURCE=cjk-csillapitas "$@" "$IMG" \
    "$SNAP" --host 0.0.0.0 --port 8000 --served-model-name qwen36 \
    --tensor-parallel-size 1 --max-model-len 262144 --max-num-batched-tokens 8192 \
    --gpu-memory-utilization 0.5 --max-num-seqs 8 --kv-cache-dtype fp8_e4m3 \
    --enable-chunked-prefill --enable-prefix-caching --reasoning-parser qwen3 \
    --enable-auto-tool-choice --tool-call-parser qwen3_coder \
    --limit-mm-per-prompt '{"image":1}' --trust-remote-code --no-async-scheduling \
    --speculative-config '{"method":"mtp","num_speculative_tokens":2}' \
    --enable-prompt-tokens-details $VLLM_EXTRA >/dev/null
  for i in $(seq 1 80); do
    curl -sf "$URL/health" >/dev/null 2>&1 && return 0
    docker ps -q -f name=cjk-kiszolgalo | grep -q . || break
    sleep 15
  done
  say "HIBA: $cimke példánya nem lett kész"
  docker logs --tail 40 cjk-kiszolgalo > "$EX/naplo/peldany-$cimke-HIBA.log" 2>&1
  return 1
}

meres() {  # <cimke>
  say "$1 — 17 item sorosan"
  ( cd "$EX/magyar-kie-eval" && python3 src/harness.py --url "$URL" --model qwen36 \
      --cimke "K0-$1" --items gt/items-150.jsonl --item-ids "$ITEMS" \
      --futasok 1 --parallel 1 --out "reports/csapda-K0-$1.json" ) \
    > "$EX/naplo/csapda-K0-$1.log" 2>&1
}

for c in inst7-bi inst8-bi; do
  inditas "$c" -e VLLM_BATCH_INVARIANT=1 && meres "$c"
done
# a második BI példányon: kötegteszt
if curl -sf "$URL/health" >/dev/null 2>&1; then
  say "inst8-bi — 12 item parallel=6"
  ( cd "$EX/magyar-kie-eval" && python3 src/harness.py --url "$URL" --model qwen36 \
      --cimke K0-inst8-bi-par6 --items gt/items-150.jsonl --item-ids "$VALID" \
      --futasok 1 --parallel 6 --out reports/csapda-K0-inst8-bi-par6.json ) \
    > "$EX/naplo/csapda-K0-inst8-bi-par6.log" 2>&1
fi

# Összevetés: minden pár, csak a számokat
{
  echo "példány-sorozat BI (TRITON_ATTN) · $(date +%F' '%H:%M) · 17 item: 12 igazoló + 5 billenő"
  echo
  for a in K0 K0-ujpeldany K0-inst3 K0-inst4 K0-inst7-bi K0-inst8-bi K0-inst8-bi-par6; do
    for b in K0 K0-ujpeldany K0-inst3 K0-inst4 K0-inst7-bi K0-inst8-bi K0-inst8-bi-par6; do
      [[ "$a" < "$b" ]] || continue
      fa="$EX/magyar-kie-eval/reports/csapda-$a.json"; fb="$EX/magyar-kie-eval/reports/csapda-$b.json"
      [ -s "$fa" ] && [ -s "$fb" ] || continue
      printf '%-14s vs %-14s : ' "$a" "$b"
      python3 "$EX/eszkozok/parhuzam_ellenoriz.py" "$fa" "$fb" 2>/dev/null \
        | grep -E "^(sha egyezés|pass eltérés)" | tr '\n' ' '
      echo
    done
  done
} > "$EX/eredmenyek/peldany-sorozat-bi.txt" 2>&1
cat "$EX/eredmenyek/peldany-sorozat-bi.txt"
say "BI-SOROZAT KÉSZ — eredmenyek/peldany-sorozat-bi.txt"
