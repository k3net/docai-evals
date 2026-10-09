#!/usr/bin/env bash
# F0/C — K0d-2: fake-quant a HF-motorban (a K0d 94,0% → 90–95%-os sáv → az F3-ban fake-quant kar).
#   fq_egyseg: a fakequant.fq bitre egyezik-e a vLLM per_token_group_quant_fp8 kerneljével (fp32 és UE8M0 skála)
#   k0d2:      eager alapvonal + vllm / fp32 / pow2 fake-quant változatok a pilot-itemeken, mind vs vLLM
# A változat választása a pilot-itemeken (eldobható adat). Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F0C
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F0/k0d2"
mkdir -p "$R"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

if ! done_marker fq_egyseg; then
  say "K0d-2: fake-quant egységteszt a vLLM-kernel ellen" 2700
  vpy eszkozok/fq_egyseg.py --out eredmenyek/F0/k0d2/fq_egyseg.json > "$R/fq_egyseg.log" 2>&1 \
    || fail "fq egységteszt (eredmenyek/F0/k0d2/fq_egyseg.log)"
  mark_ok fq_egyseg
fi

if ! done_marker k0d2; then
  say "K0d-2: HF eager + 3 fake-quant változat a pilot-itemeken (~35 perc)" 2400
  py --gpu eszkozok/k0d2_fakequant.py --out eredmenyek/F0/k0d2 > "$R/k0d2.log" 2>&1 \
    || fail "K0d-2 (eredmenyek/F0/k0d2/k0d2.log)"
  mark_ok k0d2
fi

say "F0/C kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
