#!/usr/bin/env bash
# F2 — tréning nélküli alapvonal (runbook 9. pont), CSAK a befagyasztás után (eredmenyek/F1/atnezes/FAGYASZTVA.json):
#   vLLM (LORA=1, ugyanaz a kernelút, mint az F4-ben): L0 a val-on 4 permutációval + tartalom nélküli futás
#   HF: L0 a val-on 4 permutációval + rejtett állapot (27., 40. réteg); a train-en perm 0 + rejtett állapot
#   L2a: logisztikus fej a rejtett állapoton (train → λ a val-on), 27. és 40. réteg (l2a_szonda.py)
#   elemzés a val-on, motoronként: L1-karok, τ, L1★, F2-kapu (L1★ besorolási lefedettség@95 ≥ 0,90?); L2a ugyanígy
# A teszt-itemeken az F2-ben SEMMI nem fut (a teszt egyszer, az F4-ben; a teszt rejtett állapotai is ott).
# Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F2
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F2"
D=adat/f1
mkdir -p "$R" cache/hidden
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f "$EXP/eredmenyek/F1/atnezes/FAGYASZTVA.json" ] || fail "az F1 nincs befagyasztva (eredmenyek/F1/atnezes/FAGYASZTVA.json hiányzik)"
(cd $D && sha256sum -c "$EXP/eredmenyek/F1/atnezes/fagyasztas.sha256" > "$R/hash_ellenorzes.txt" 2>&1) \
  || fail "az item-fájlok eltérnek a befagyasztott hashtől (eredmenyek/F2/hash_ellenorzes.txt)"

if ! done_marker val_fajl; then
  cat $D/items_val-belso.jsonl $D/items_val-szallito.jsonl > $D/f2_val.jsonl
  mark_ok val_fajl
fi

if ! done_marker vllm_val; then
  say "F2: alany boot (vLLM, LORA=1)" 9000
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R"; fail "alany boot"; }
  say "F2: vLLM L0 a val-on (4 permutáció)" 8400
  py eszkozok/kiolvaso.py --items $D/f2_val.jsonl --out eredmenyek/F2/vllm_val.jsonl --perms 0,1,2,3 \
    > "$R/vllm_val.log" 2>&1 || { subject_stop ldh-subject "$R"; fail "vLLM val"; }
  say "F2: vLLM tartalom nélküli futás (contextual kar)" 7800
  py eszkozok/kiolvaso.py --items $D/f2_val.jsonl --out eredmenyek/F2/vllm_val_cf.jsonl --perms 0 --content-free \
    > "$R/vllm_val_cf.log" 2>&1 || { subject_stop ldh-subject "$R"; fail "vLLM val content-free"; }
  subject_stop ldh-subject "$R"
  mark_ok vllm_val
fi

if ! done_marker hf_val; then
  say "F2: HF L0 a val-on (4 permutáció) + rejtett állapot" 7200
  py --gpu eszkozok/hf_kiolvaso.py --items $D/f2_val.jsonl --out eredmenyek/F2/hf_val.jsonl --perms 0,1,2,3 \
    --hidden-layers 27,40 --hidden-out cache/hidden/val > "$R/hf_val.log" 2>&1 || fail "HF val"
  mark_ok hf_val
fi

if ! done_marker hf_train; then
  say "F2: HF a train-en (perm 0) + rejtett állapot az L2a-hoz" 5400
  py --gpu eszkozok/hf_kiolvaso.py --items $D/items_train.jsonl --out eredmenyek/F2/hf_train.jsonl --perms 0 \
    --hidden-layers 27,40 --hidden-out cache/hidden/train > "$R/hf_train.log" 2>&1 || fail "HF train"
  mark_ok hf_train
fi

if ! done_marker l2a; then
  say "F2: L2a-szonda a rejtett állapoton (27. és 40. réteg)" 1500
  for L in 27 40; do
    py eszkozok/l2a_szonda.py fit --layer $L --items $D --train-rows eredmenyek/F2/hf_train.jsonl \
      --train-hidden cache/hidden/train --val-rows eredmenyek/F2/hf_val.jsonl --val-hidden cache/hidden/val \
      --out eredmenyek/F2/l2a_L$L > "$R/l2a_L$L.log" 2>&1 || fail "L2a, $L. réteg (eredmenyek/F2/l2a_L$L.log)"
  done
  mark_ok l2a
fi

if ! done_marker elemzes; then
  say "F2: L1-karok és F2-kapu a val-on (vLLM, HF)" 600
  py eszkozok/elemzes.py --items $D --val eredmenyek/F2/vllm_val.jsonl --cf-val eredmenyek/F2/vllm_val_cf.jsonl \
    --out eredmenyek/F2/L1_vllm_val.json > "$R/elemzes_vllm.log" 2>&1 || fail "elemzés vLLM"
  py eszkozok/elemzes.py --items $D --val eredmenyek/F2/hf_val.jsonl \
    --out eredmenyek/F2/L1_hf_val.json > "$R/elemzes_hf.log" 2>&1 || fail "elemzés HF"
  for L in 27 40; do
    py eszkozok/elemzes.py --items $D --val eredmenyek/F2/l2a_L$L/val.jsonl \
      --out eredmenyek/F2/L2a_L${L}_val.json > "$R/elemzes_l2a_L$L.log" 2>&1 || fail "elemzés L2a $L"
  done
  mark_ok elemzes
fi

say "F2 kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
