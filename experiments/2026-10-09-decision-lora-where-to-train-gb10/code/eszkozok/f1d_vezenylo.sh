#!/usr/bin/env bash
# F1/D — második független címke-bíráló: Mistral Small 4 119B-A6B NVFP4, lokálisan (runbook 4.8; user-döntés
# 2026-10-04, a GPT-6 Astra helyett). A modell a ~/hf-cache-mistral4-be töltődik (a letöltés külön indul).
#   boot-próba → 3 itemes logprob-próba (címketömeg a top-20-ban) → ha a logprob használható: logprobs mód,
#   különben verbal mód → a val/teszt rétegek → leállítás.
# Az F1C után fut (egyszerre egy nagy GPU-folyamat). Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F1D
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F1/biralo"
D=adat/f1
EXTRA='{"reasoning_effort": "none"}'
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

if ! done_marker letoltes; then
  say "F1D: a Mistral-letöltés megvárása" 5400
  t0=$(date +%s)
  while docker ps --format '{{.Names}}' | grep -qx dl-mistral4; do
    [ $(( $(date +%s) - t0 )) -gt 10800 ] && fail "a Mistral-letöltés 3 óra után sem végzett"
    sleep 60
  done
  n=$(find "$HOME/hf-cache-mistral4/hub/models--mistralai--Mistral-Small-4-119B-2603-NVFP4/snapshots" -name 'consolidated-*.safetensors' 2>/dev/null | wc -l)
  [ "$n" = 13 ] || fail "a Mistral-letöltés hiányos ($n/13 shard; docker logs dl-mistral4)"
  du -sh "$HOME/hf-cache-mistral4" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
  mark_ok letoltes
fi

if ! done_marker mistral; then
  say "F1D: Mistral Small 4 boot (NVFP4, TRITON_MLA)" 4200
  t0=$(date +%s)
  mistral_start || { rc=$?; mistral_stop "$R"; fail "Mistral boot (rc=$rc, eredmenyek/F1/biralo/ldh-mistral.log)"; }
  echo "{\"boot_s\": $(( $(date +%s) - t0 ))}" > "$R/mistral_boot.json"

  say "F1D: Mistral logprob-próba (3 item)" 3600
  mkdir -p "$R/proba"
  py eszkozok/biralo.py --items $D/items_val-belso.jsonl --out eredmenyek/F1/biralo/proba/mistral_proba.jsonl --limit 3 \
    --url http://127.0.0.1:8430/v1 --model mistral-small-4 --mode logprobs --concurrency 1 --extra-body "$EXTRA" \
    > "$R/mistral_proba.log" 2>&1 || true
  mode=$(py -c "
import json
rows=[json.loads(l) for l in open('eredmenyek/F1/biralo/proba/mistral_proba.jsonl')] if __import__('os').path.exists('eredmenyek/F1/biralo/proba/mistral_proba.jsonl') else []
ok=[r for r in rows if r.get('pred') and (r.get('label_mass_top20') or 0) > 0.5]
print('logprobs' if len(ok) == len(rows) == 3 else 'verbal')" 2>/dev/null || echo verbal)
  echo "{\"mode\": \"$mode\"}" > "$R/mistral_mod.json"

  for sp in val-belso val-szallito T-belso T-szallito T-kozeli T-tavoli; do
    say "F1D: Mistral-bíráló ($mode) — $sp" 2400
    py eszkozok/biralo.py --items $D/items_$sp.jsonl --out eredmenyek/F1/biralo/mistral_$sp.jsonl \
      --url http://127.0.0.1:8430/v1 --model mistral-small-4 --mode "$mode" --concurrency 4 --extra-body "$EXTRA" \
      > "$R/mistral_$sp.log" 2>&1 || { mistral_stop "$R"; fail "Mistral-bíráló $sp"; }
  done
  mistral_stop "$R"
  mark_ok mistral
fi

say "F1/D kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
