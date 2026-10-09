#!/usr/bin/env bash
# K00b/B — a 00b kiegészítés mérése (runbook 15. pont): a MEGLÉVŐ adapterek a befagyasztott `T-ujszallito`-n.
# Előfeltétel: K00b/A kész, Dani címke-átnézése alkalmazva, a réteg befagyasztva
# (adat/k00b/meres/items_T-ujszallito.jsonl + eredmenyek/K00b/fagyasztas.sha256 + eredmenyek/K00b/FAGYASZTVA.json).
#  1. vLLM, egyetlen friss példány (LORA=1), sorosan: próba → L0 val + réteg (4 perm.; az L1★-hoz) → L3 seed 1–3
#     val + réteg (perm 0; a `temp` kar csak ezt használja) → L0′ (réteg, perm 0) → próba. A τ és a temperature
#     ugyanebből a példányból jön, mint a réteg kiolvasása (mint az F4-ben).
#  2. elemzés vLLM-en — k00b_elemzes.py (H2-szállító′)
#  3. HF: L0 a rétegen (4 perm.) → L3 seed 1–3 (perm 0); a HF val az F2/F3-ból
#  4. elemzés HF-en
# Idempotens (lépésenkénti jelölők); leválasztva indítandó.
set -uo pipefail
FAZIS=K00bB
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
D=adat/k00b/meres
T=$D/items_T-ujszallito.jsonl
VAL=adat/f1/f2_val.jsonl
R="$EXP/eredmenyek/K00b"
V=eredmenyek/K00b/vllm
H=eredmenyek/K00b/hf
mkdir -p "$R/vllm" "$R/hf"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f "$EXP/DONE-K00bA" ] || fail "a K00b/A nincs kész"
[ -f "$R/FAGYASZTVA.json" ] || fail "a T-ujszallito nincs befagyasztva ($R/FAGYASZTVA.json)"
(cd $D && sha256sum -c "$R/fagyasztas.sha256" > "$R/hash_ellenorzes.txt" 2>&1) || fail "a réteg eltér a befagyasztott hashtől"
(cd adat/f1 && sha256sum -c "$EXP/eredmenyek/F1/atnezes/fagyasztas.sha256" >> "$R/hash_ellenorzes.txt" 2>&1) \
  || fail "az F1 item-fájlok eltérnek a befagyasztott hashtől"
KONFIG=$(python3 -c "import json;print(json.load(open('eredmenyek/F3/hangolas_dontes.json'))['konfig'])") \
  || fail "hiányzik: eredmenyek/F3/hangolas_dontes.json"
SEEDS=("${KONFIG}_s1" "${KONFIG}_s2" "${KONFIG}_s3")
for A in "${SEEDS[@]}"; do
  [ -d "ckpt/$A/final" ] && [ -d "ckpt/$A/vllm" ] && [ -f "eredmenyek/F3/$A/hf_val.jsonl" ] || fail "hiányzik a seed: $A"
done
printf '%s\n' "${SEEDS[@]}" > "$R/seedek.txt"

lora_load() {  # lora_load <név> <logkönyvtár>
  rm -rf "adapters/$1" && cp -r "ckpt/$1/vllm" "adapters/$1" || return 1
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$1\", \"lora_path\": \"/adapters/$1\"}" >> "$2/lora_load.txt" 2>&1
}
lora_unload() {
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/unload_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$1\"}" >> "$2/lora_load.txt" 2>&1
}
rd() {  # rd <kimenet> <log> kiolvaso-kapcsolók... — hiba esetén leállítja az alanyt és bukik
  local out="$1" log="$2"; shift 2
  py eszkozok/kiolvaso.py --out "$out" "$@" > "$log" 2>&1 || { subject_stop ldh-subject "$R/vllm"; fail "kiolvasás: $out ($log)"; }
}

# --- 1. vLLM -------------------------------------------------------------------------------------------
if ! done_marker vllm; then
  say "K00bB (1/4): vLLM — L0 val + réteg (4 perm.), L3 × 3 (perm 0), L0′" 11000
  rm -f "$R/vllm/lora_load.txt"
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R/vllm"; fail "alany boot"; }
  rd $V/probe_eleje.jsonl "$R/vllm/probe_eleje.log" --items adat/probe50.jsonl
  rd $V/l0_val.jsonl "$R/vllm/l0_val.log" --items $VAL --perms 0,1,2,3
  rd $V/l0_test.jsonl "$R/vllm/l0_test.log" --items $T --perms 0,1,2,3
  n=0
  for A in "${SEEDS[@]}"; do
    n=$((n + 1))
    lora_load "$A" "$R/vllm" || { subject_stop ldh-subject "$R/vllm"; fail "adapter-betöltés: $A"; }
    rd $V/l3_s${n}_val.jsonl "$R/vllm/l3_s${n}_val.log" --items $VAL --perms 0 --model "$A"
    rd $V/l3_s${n}_test.jsonl "$R/vllm/l3_s${n}_test.log" --items $T --perms 0 --model "$A"
    [ $n -lt 3 ] && { lora_unload "$A" "$R/vllm" || { subject_stop ldh-subject "$R/vllm"; fail "adapter-eltávolítás: $A"; }; }
  done
  rd $V/l0r_test.jsonl "$R/vllm/l0r_test.log" --items $T --perms 0
  rd $V/probe_vege.jsonl "$R/vllm/probe_vege.log" --items adat/probe50.jsonl
  subject_stop ldh-subject "$R/vllm"
  mark_ok vllm
fi

# --- 2. elemzés vLLM-en -------------------------------------------------------------------------------
if ! done_marker elemzes_vllm; then
  say "K00bB (2/4): elemzés vLLM-en (10 000 bootstrap)" 8000
  py eszkozok/k00b_elemzes.py --motor vllm --items-val adat/f1 --items-test $D --l0-val $V/l0_val.jsonl \
    --l0-test $V/l0_test.jsonl --l3 s1:$V/l3_s1_val.jsonl:$V/l3_s1_test.jsonl \
    --l3 s2:$V/l3_s2_val.jsonl:$V/l3_s2_test.jsonl --l3 s3:$V/l3_s3_val.jsonl:$V/l3_s3_test.jsonl \
    --out eredmenyek/K00b/vllm_k00b.json > "$R/elemzes_vllm.log" 2>&1 || fail "elemzés vLLM ($R/elemzes_vllm.log)"
  mark_ok elemzes_vllm
fi

# --- 3. HF ---------------------------------------------------------------------------------------------
if ! done_marker hf_l0; then
  say "K00bB (3/4): HF L0 a rétegen (4 perm.)" 7000
  py --gpu eszkozok/hf_kiolvaso.py --items $T --out $H/l0_test.jsonl --perms 0,1,2,3 > "$R/hf/l0_test.log" 2>&1 \
    || fail "HF L0"
  mark_ok hf_l0
fi
n=0
for A in "${SEEDS[@]}"; do
  n=$((n + 1))
  if ! done_marker hf_l3_s$n; then
    say "K00bB (3/4): HF L3 seed $n ($A) a rétegen" $(( 4000 - 1000 * n ))
    py --gpu eszkozok/hf_kiolvaso.py --items $T --adapter "ckpt/$A/final" --perms 0 --out $H/l3_s${n}_test.jsonl \
      > "$R/hf/l3_s${n}_test.log" 2>&1 || fail "HF L3 seed $n"
    mark_ok hf_l3_s$n
  fi
done

# --- 4. elemzés HF-en ---------------------------------------------------------------------------------
if ! done_marker elemzes_hf; then
  say "K00bB (4/4): elemzés HF-en" 900
  py eszkozok/k00b_elemzes.py --motor hf --items-val adat/f1 --items-test $D --l0-val eredmenyek/F2/hf_val.jsonl \
    --l0-test $H/l0_test.jsonl --l3 "s1:eredmenyek/F3/${SEEDS[0]}/hf_val.jsonl:$H/l3_s1_test.jsonl" \
    --l3 "s2:eredmenyek/F3/${SEEDS[1]}/hf_val.jsonl:$H/l3_s2_test.jsonl" \
    --l3 "s3:eredmenyek/F3/${SEEDS[2]}/hf_val.jsonl:$H/l3_s3_test.jsonl" \
    --out eredmenyek/K00b/hf_k00b.json > "$R/elemzes_hf.log" 2>&1 || fail "elemzés HF ($R/elemzes_hf.log)"
  mark_ok elemzes_hf
fi

say "K00b/B kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
