#!/usr/bin/env bash
# F1/E — a befagyasztástól független előkészítés, amíg Dani a val/teszt mintát nézi át (2026-10-04):
#   1. a két bíráló (Mistral Small 4, Llama-3.3-70B) a TRAIN itemeken (runbook 4.8/8: a train-ből legfeljebb
#      a ≥ 2 bíráló által magabiztosan vitatott itemek hagyhatók el, dokumentálva);
#   2. F3-időmérés az F1 train-adaton: 12 lépés `mix+se`, három fake-quant móddal (none / lin / fp32) →
#      token/s, csúcsmemória, epochidő; a fake-quant kar költsége (runbook 5., „smoke az F3 előtt”).
# Az alany a val/teszten NEM fut. Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F1E
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
B="$EXP/eredmenyek/F1/biralo_train"
T="$EXP/eredmenyek/F1/f3_ido"
D=adat/f1
EXTRA='{"reasoning_effort": "none"}'
mkdir -p "$B" "$T"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

if ! done_marker mistral_train; then
  say "F1E: Mistral boot (train-bírálathoz)" 5400
  mistral_start || { rc=$?; mistral_stop "$B"; fail "Mistral boot (rc=$rc)"; }
  say "F1E: Mistral-bíráló — train" 4800
  py eszkozok/biralo.py --items $D/items_train.jsonl --out eredmenyek/F1/biralo_train/mistral_train.jsonl \
    --url http://127.0.0.1:8430/v1 --model mistral-small-4 --mode logprobs --concurrency 4 --extra-body "$EXTRA" \
    > "$B/mistral_train.log" 2>&1 || { mistral_stop "$B"; fail "Mistral-bíráló train"; }
  mistral_stop "$B"
  mark_ok mistral_train
fi

if ! done_marker llama_train; then
  say "F1E: Llama boot (train-bírálathoz)" 4200
  llama_start || { rc=$?; llama_stop "$B"; fail "Llama boot (rc=$rc)"; }
  say "F1E: Llama-bíráló — train" 3600
  py eszkozok/biralo.py --items $D/items_train.jsonl --out eredmenyek/F1/biralo_train/llama_train.jsonl \
    --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs --concurrency 4 \
    > "$B/llama_train.log" 2>&1 || { llama_stop "$B"; fail "Llama-bíráló train"; }
  llama_stop "$B"
  mark_ok llama_train
fi

for mode in none lin fp32; do
  if ! done_marker "ido_$mode"; then
    say "F1E: F3-időmérés — fake-quant $mode (12 lépés)" 2400
    rm -rf "ckpt/f3ido_$mode"
    py --gpu eszkozok/tren_lora.py --train $D/items_train.jsonl --out "ckpt/f3ido_$mode" --targets mix+se \
      --max-steps 12 --grad-accum 8 --save-every 1000 --fakequant "$mode" > "$T/$mode.log" 2>&1 \
      || fail "F3-időmérés $mode (eredmenyek/F1/f3_ido/$mode.log)"
    mkdir -p "$T/$mode"
    cp "ckpt/f3ido_$mode/train_log.jsonl" "ckpt/f3ido_$mode/config.json" "$T/$mode/" 2>/dev/null
    rm -rf "ckpt/f3ido_$mode"
    mark_ok "ido_$mode"
  fi
done

say "F1/E kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
