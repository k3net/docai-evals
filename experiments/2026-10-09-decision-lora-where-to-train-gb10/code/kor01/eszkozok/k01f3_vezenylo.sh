#!/usr/bin/env bash
# K01F3 — a 01-es kör döntési LoRA-ja (01-runbook 5. L3, 7. F3). Használat: k01f3_vezenylo.sh <szakasz>
#   pilot        — a 00 győztes receptje (mix+se, ε = 0,05, r16, 1 epoch) + 30% opció-permutáció, seed 1;
#                  train = items_train + az EU-180k train-extra (a fagyasztott F1S); a bázis val-kiolvasása is.
#   megerosites  — ugyanez seed 2-vel és 3-mal (a val a pilotban a plafonon ült → nincs hangolás, 7. pont).
# Lépések: fagyasztás-ellenőrzés → tren_lora önteszt (döntési pozíció 01-es itemeken) → 2 lépéses smoke (perm-aug,
# vLLM-export) → tréning → egy LoRA-s vLLM-példányon a val kiolvasása az adapterrel ÉS a bázissal (4 permutáció,
# soros) → HF-kiolvasás az adapterrel a val-on (perm 0; motor-hűség). A teszten semmi nem fut: a 01 v1 (hipotézisek,
# végpontok) még nincs rögzítve. Idempotens (lépésenkénti jelölők, a tréning checkpointból folytat); leválasztva
# indítandó; újraindulás után a folytat.sh viszi tovább (AKTIV_FAZIS).
set -uo pipefail
SZAKASZ="${1:?szakasz: pilot}"
FAZIS="K01F3-$SZAKASZ"
cd "$(dirname "$0")/../.." && EXP="$(pwd)"
source eszkozok/lib.sh
K=kor01
D=$K/adat
R="$EXP/$K/eredmenyek/F3"
mkdir -p "$R"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f $D/f1s/atnezes/FAGYASZTVA.json ] || fail "az F1S nincs befagyasztva"
(cd $D && sha256sum -c f1s/atnezes/fagyasztas.sha256 > "$R/hash_ellenorzes_$SZAKASZ.txt" 2>&1) \
  || fail "az itemfájlok eltérnek a befagyasztott hash-től ($K/eredmenyek/F3/hash_ellenorzes_$SZAKASZ.txt)"

REC="--targets mix+se --eps 0.05 --perm-aug 0.3"
case "$SZAKASZ" in
  pilot) KAROK="k01_l3mixse_p30_s1|1"; BAZIS=1 ;;
  megerosites) [ -f "$EXP/DONE-K01F3-pilot" ] || fail "a pilot nincs kész"
    KAROK="k01_l3mixse_p30_s2|2
k01_l3mixse_p30_s3|3"; BAZIS=0 ;;
  *) fail "ismeretlen szakasz: $SZAKASZ" ;;
esac
TRAIN=$D/items_train.jsonl,$D/f1s/items_eu180k.jsonl
VAL=$D/items_val.jsonl
echo "$KAROK | $REC | train=$TRAIN" > "$R/karok_$SZAKASZ.txt"
A=$(echo "$KAROK" | head -1 | cut -d'|' -f1); O="$R/$A"; mkdir -p "$O"; KAPCSOLOK="$REC --seed 1"

if [ "$SZAKASZ" = pilot ]; then
if ! done_marker selftest; then
  say "K01F3 $SZAKASZ: tren_lora önteszt a 01-es itemeken (döntési pozíció)" 900
  py --gpu eszkozok/tren_lora.py --train $D/items_train.jsonl --out ckpt/k01_selftest --selftest \
    > "$O/selftest.log" 2>&1 || fail "önteszt ($K/eredmenyek/F3/$A/selftest.log)"
  cp ckpt/k01_selftest/selftest.json "$O/" 2>/dev/null
  mark_ok selftest
fi
if ! done_marker smoke; then
  say "K01F3 $SZAKASZ: 2 lépéses smoke (perm-aug, vLLM-export)" 900
  rm -rf ckpt/k01_smoke
  py --gpu eszkozok/tren_lora.py --train "$TRAIN" --out ckpt/k01_smoke $KAPCSOLOK --limit 64 --max-steps 2 \
    > "$O/smoke.log" 2>&1 || fail "smoke ($K/eredmenyek/F3/$A/smoke.log)"
  [ -f ckpt/k01_smoke/vllm/adapter_model.safetensors ] || fail "smoke: nincs vLLM-export"
  rm -rf ckpt/k01_smoke
  mark_ok smoke
fi
fi

N=$(echo "$KAROK" | wc -l); i=0
while IFS='|' read -r A SEED; do
i=$((i + 1)); O="$R/$A"; mkdir -p "$O"; KAPCSOLOK="$REC --seed $SEED"
if ! done_marker "train_$A"; then
  say "K01F3 $SZAKASZ ($i/$N): $A tréning (14,5 ezer item, 1 epoch)" 16500
  py --gpu eszkozok/tren_lora.py --train "$TRAIN" --out "ckpt/$A" $KAPCSOLOK > "$O/train.log" 2>&1 \
    || fail "$A tréning ($K/eredmenyek/F3/$A/train.log)"
  cp "ckpt/$A/train_log.jsonl" "ckpt/$A/config.json" "ckpt/$A/done.json" "$O/" 2>/dev/null
  mark_ok "train_$A"
fi
if ! done_marker "vllm_$A"; then
  say "K01F3 $SZAKASZ ($i/$N): $A vLLM-kiolvasás a val-on (4 permutáció; a pilotban a bázis is)" $((2700 + BAZIS * 2000))
  rm -rf "adapters/$A" && cp -r "ckpt/$A/vllm" "adapters/$A" || fail "$A adapter-másolás"
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$O"; fail "alany boot ($A)"; }
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$A\", \"lora_path\": \"/adapters/$A\"}" > "$O/vllm_load.txt" 2>&1 \
    || { subject_stop ldh-subject "$O"; fail "$A: a vLLM nem töltötte be az adaptert ($K/eredmenyek/F3/$A/vllm_load.txt)"; }
  py eszkozok/kiolvaso.py --items $VAL --out "$K/eredmenyek/F3/$A/vllm_val.jsonl" --perms 0,1,2,3 --model "$A" \
    > "$O/vllm_val.log" 2>&1 || { subject_stop ldh-subject "$O"; fail "$A vLLM-kiolvasás"; }
  if [ "$BAZIS" = 1 ]; then
    py eszkozok/kiolvaso.py --items $VAL --out "$K/eredmenyek/F3/$A/vllm_val_bazis.jsonl" --perms 0,1,2,3 \
      --model "$SUBJECT_MODEL" > "$O/vllm_val_bazis.log" 2>&1 || { subject_stop ldh-subject "$O"; fail "bázis vLLM-kiolvasás"; }
  fi
  subject_stop ldh-subject "$O"
  mark_ok "vllm_$A"
fi
if ! done_marker "hf_$A"; then
  say "K01F3 $SZAKASZ ($i/$N): $A HF-kiolvasás a val-on (perm 0, motor-hűség)" 1900
  py --gpu eszkozok/hf_kiolvaso.py --items $VAL --adapter "ckpt/$A/final" --perms 0 \
    --out "$K/eredmenyek/F3/$A/hf_val.jsonl" > "$O/hf_val.log" 2>&1 || fail "$A HF-kiolvasás"
  mark_ok "hf_$A"
fi
done <<< "$KAROK"

say "K01F3 $SZAKASZ kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
