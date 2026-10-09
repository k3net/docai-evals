#!/usr/bin/env bash
# F3 — döntési LoRA (runbook 5. „Az L3 tréningje”, 9. F3). Használat: f3_vezenylo.sh <szakasz>
#   pilot        — L3-mix, L3-mix+se, L3-mix fp32 fake-quanttal; 1 seed (1), 1 epoch
#   hangolas     — a pilot-győztes célmodul-készletén (h1) lr 2e-4, (h2) ε = 0,05, (h3) 2 epoch; 1 seed
#   megerosites  — a val-on győztes konfig seed 2-vel és 3-mal
# A hangolás és a megerősítés karjait az f3_dontes.py adja az előre rögzített győztes-választással
# (eredmenyek/F3/pilot_dontes.json, hangolas_dontes.json).
# Karonként: tréning (lora-train:2, BF16-bázis) → HF-kiolvasás a val-on (4 permutáció, adapterrel) → vLLM-kiolvasás a
# val-on (LORA=1, futásidőben betöltött adapter, 4 permutáció) → elemzés (L1-karok az L3 kiolvasásán; H1-hez a `temp`).
# A teszten semmi nem fut (F4). Idempotens (karonkénti jelölők); leválasztva indítandó.
set -uo pipefail
SZAKASZ="${1:?szakasz: pilot}"
FAZIS="F3-$SZAKASZ"
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
D=adat/f1
R="$EXP/eredmenyek/F3"
mkdir -p "$R"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f "$EXP/eredmenyek/F1/atnezes/FAGYASZTVA.json" ] || fail "az F1 nincs befagyasztva"
(cd $D && sha256sum -c "$EXP/eredmenyek/F1/atnezes/fagyasztas.sha256" > "$R/hash_ellenorzes_$SZAKASZ.txt" 2>&1) \
  || fail "az item-fájlok eltérnek a befagyasztott hashtől"
[ -f $D/f2_val.jsonl ] || fail "hiányzik: $D/f2_val.jsonl (az F2 állítja elő)"

# kar: név | célmodulok | fake-quant | további tréning-kapcsolók   (seed a névben: _s<N>)
case "$SZAKASZ" in
  pilot) KAROK="l3mix_s1|mix|none|--seed 1
l3mixse_s1|mix+se|none|--seed 1
l3mixfq_s1|mix|fp32|--seed 1" ;;
  hangolas) [ -f "$EXP/DONE-F3-pilot" ] || fail "a pilot nincs kész"
    KAROK=$(py eszkozok/f3_dontes.py karok hangolas) || fail "győztes-választás (pilot)" ;;
  megerosites) [ -f "$EXP/DONE-F3-hangolas" ] || fail "a hangolás nincs kész"
    KAROK=$(py eszkozok/f3_dontes.py karok megerosites) || fail "győztes-választás (hangolás)" ;;
  *) fail "ismeretlen szakasz: $SZAKASZ" ;;
esac
echo "$KAROK" > "$R/karok_$SZAKASZ.txt"
N=$(echo "$KAROK" | wc -l)

i=0
while IFS='|' read -r A TG FQ EXTRA; do
  i=$((i + 1))
  O="$R/$A"; mkdir -p "$O"
  if ! done_marker "train_$A"; then
    rem=$([ "$FQ" = none ] && echo 8000 || echo 39000)
    case "$EXTRA" in *"--epochs 2"*) rem=$((rem * 2)) ;; esac
    say "F3 $SZAKASZ ($i/$N): $A tréning (célmodulok $TG, fake-quant $FQ)" "$rem"
    py --gpu eszkozok/tren_lora.py --train $D/items_train.jsonl --out "ckpt/$A" --targets "$TG" --fakequant "$FQ" $EXTRA \
      > "$O/train.log" 2>&1 || fail "$A tréning (eredmenyek/F3/$A/train.log)"
    cp "ckpt/$A/train_log.jsonl" "ckpt/$A/config.json" "ckpt/$A/done.json" "$O/" 2>/dev/null
    mark_ok "train_$A"
  fi
  if ! done_marker "hf_$A"; then
    say "F3 $SZAKASZ ($i/$N): $A — HF-kiolvasás a val-on (4 permutáció)" 3000
    py --gpu eszkozok/hf_kiolvaso.py --items $D/f2_val.jsonl --adapter "ckpt/$A/final" --perms 0,1,2,3 \
      --out "eredmenyek/F3/$A/hf_val.jsonl" > "$O/hf_val.log" 2>&1 || fail "$A HF-kiolvasás"
    mark_ok "hf_$A"
  fi
  if ! done_marker "vllm_$A"; then
    say "F3 $SZAKASZ ($i/$N): $A — vLLM-kiolvasás a val-on (futásidejű adapter)" 1800
    rm -rf "adapters/$A" && cp -r "ckpt/$A/vllm" "adapters/$A" || fail "$A adapter-másolás"
    LORA=1 subject_start ldh-subject
    subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$O"; fail "alany boot ($A)"; }
    curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
      -d "{\"lora_name\": \"$A\", \"lora_path\": \"/adapters/$A\"}" > "$O/vllm_load.txt" 2>&1 \
      || { subject_stop ldh-subject "$O"; fail "$A: a vLLM nem töltötte be az adaptert (eredmenyek/F3/$A/vllm_load.txt)"; }
    py eszkozok/kiolvaso.py --items $D/f2_val.jsonl --out "eredmenyek/F3/$A/vllm_val.jsonl" --perms 0,1,2,3 --model "$A" \
      > "$O/vllm_val.log" 2>&1 || { subject_stop ldh-subject "$O"; fail "$A vLLM-kiolvasás"; }
    subject_stop ldh-subject "$O"
    mark_ok "vllm_$A"
  fi
  if ! done_marker "elemzes_$A"; then
    for M in hf vllm; do
      py eszkozok/elemzes.py --items $D --val "eredmenyek/F3/$A/${M}_val.jsonl" --out "eredmenyek/F3/$A/L3_${M}_val.json" \
        > "$O/elemzes_$M.log" 2>&1 || fail "$A elemzés ($M)"
    done
    mark_ok "elemzes_$A"
  fi
done <<< "$KAROK"

say "F3 $SZAKASZ kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
