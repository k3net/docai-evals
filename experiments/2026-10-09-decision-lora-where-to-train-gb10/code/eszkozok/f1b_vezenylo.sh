#!/usr/bin/env bash
# F1/B — az F1 egyetlen javító iterációja (runbook 9. pont, F1 2. lépés): a shortcut-audit bukott
# (CV AUC 0,584 > 0,55; forrás: a természetes X(a) metaadat-mintázata). Javítás: a kényszerített X(a)
# splitenként ÉS metaadat-rétegenként (osszeallit.py). Az S1–S6 változatlan; az S7–S8 friss seeddel fut újra.
# Utána auditok, előzetes hash, Llama-bíráló újra (a kényszerített X(a)-k listája megváltozott).
# A v1 kimenetek *_v1 néven megmaradnak. Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F1B
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F1"
D=adat/f1
SEED_S7=20261004
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env
echo "F1B: S7 seed $SEED_S7 (javító iteráció)" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"

if ! done_marker archiv; then
  for x in audit biralo; do [ -d "$R/$x" ] && [ ! -d "$R/${x}_v1" ] && mv "$R/$x" "$R/${x}_v1"; done
  [ -f "$R/gen/osszeallit_riport.json" ] && mv "$R/gen/osszeallit_riport.json" "$R/gen/osszeallit_riport_v1.json"
  [ -f "$R/fagyasztas_jelolt.sha256" ] && mv "$R/fagyasztas_jelolt.sha256" "$R/fagyasztas_jelolt_v1.sha256"
  mkdir -p "$D/v1" && cp $D/items_*.jsonl $D/osszeallit_riport.json "$D/v1/" 2>/dev/null
  mkdir -p "$R"/{audit,biralo}
  mark_ok archiv
fi

if ! done_marker s7; then
  say "F1B: S7–S8 rétegzett X(a)-kényszerítéssel (seed $SEED_S7)" 3600
  py eszkozok/osszeallit.py --out $D --seed $SEED_S7 > "$R/gen/osszeallit_v2.log" 2>&1 || fail "S7–S8 (eredmenyek/F1/gen/osszeallit_v2.log)"
  cp $D/osszeallit_riport.json "$R/gen/"
  mark_ok s7
fi

if ! done_marker audit; then
  say "F1B: shortcut- és nehézség-audit" 3300
  py eszkozok/auditok.py shortcut --gen $D --out eredmenyek/F1/audit > "$R/audit/shortcut.log" 2>&1 || fail "shortcut-audit"
  py eszkozok/auditok.py nehezseg --gen $D --out eredmenyek/F1/audit > "$R/audit/nehezseg.log" 2>&1 || fail "nehézség-audit"
  mark_ok audit
fi

if ! done_marker hash0; then
  (cd $D && sha256sum items_*.jsonl s1_katalogus.jsonl s2_szallitok.json parok.jsonl s4_sorok.jsonl s6_jeloltek.jsonl) \
    > "$R/fagyasztas_jelolt.sha256" || fail "hash"
  mark_ok hash0
fi

if ! done_marker llama; then
  say "F1B: Llama-3.3-70B bíráló boot" 3000
  llama_start || { rc=$?; llama_stop "$R/biralo"; fail "Llama boot (rc=$rc, eredmenyek/F1/biralo/ldh-llama.log)"; }
  for sp in val-belso val-szallito T-belso T-szallito T-kozeli T-tavoli; do
    say "F1B: Llama-bíráló — $sp" 2400
    py eszkozok/biralo.py --items $D/items_$sp.jsonl --out eredmenyek/F1/biralo/llama_$sp.jsonl \
      --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs --concurrency 4 \
      > "$R/biralo/llama_$sp.log" 2>&1 || { llama_stop "$R/biralo"; fail "Llama-bíráló $sp"; }
  done
  llama_stop "$R/biralo"
  mark_ok llama
fi

say "F1/B kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
