#!/usr/bin/env bash
# F1/A — végleges szintetikus adatkészlet a measurement-hosten (runbook 9. pont, F1 1–2. és 4. lépés eleje):
#   generátor → S1–S4 (scale full, friss seed) → OpenSearch + bge-m3 → S5–S8
#   → shortcut- és nehézség-audit → előzetes hash (fagyasztás-jelölt)
#   → Llama-3.3-70B bíráló a val/teszt itemeken (triage, gold nélkül; 4.8)
# A valószerűség-audit (4.7) és a GPT-6 Astra bíráló a laptopon fut, utána a minta és Dani átnézése.
# Alany a val/teszten NEM fut. Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F1A
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F1"
D=adat/f1
SEED_F1=20261003
mkdir -p "$R"/{gen,audit,biralo}
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env
echo "F1 seed: $SEED_F1" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"

# --- S1–S4 ------------------------------------------------------------------------
if ! done_marker gen; then
  say "F1: generátor boot (Qwen3.8-Flash)" 16200
  ./eszkozok/generator_indit.sh ldh-generator 8410
  t0=$(date +%s); ok=0
  while [ $(( $(date +%s) - t0 )) -lt 2400 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-generator 2>/dev/null)" != "true" ] && break
    curl -fsS http://127.0.0.1:8410/health >/dev/null 2>&1 && { ok=1; break; }
    sleep 15
  done
  [ $ok = 1 ] || { docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1; fail "a generátor nem indult (eredmenyek/F1/gen/ldh-generator.log)"; }
  say "F1: S1–S4 generálás (full, seed $SEED_F1, ~3,5 óra)" 15600
  py eszkozok/generator.py all --out $D --scale full --seed $SEED_F1 > "$R/gen/generator.log" 2>&1 \
    || { docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1; fail "S1–S4 (eredmenyek/F1/gen/generator.log)"; }
  docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1
  docker rm -f ldh-generator >/dev/null 2>&1
  cp $D/generator_riport.json "$R/gen/"
  mark_ok gen
fi

# --- S5–S8 ------------------------------------------------------------------------
if ! done_marker jeloltek; then
  say "F1: OpenSearch + bge-m3 jelöltek, S7–S8 összeállítás" 3600
  docker rm -f ldh-opensearch >/dev/null 2>&1 || true
  docker run -d --name ldh-opensearch -p 9201:9200 -e discovery.type=single-node \
    -e DISABLE_SECURITY_PLUGIN=true -e DISABLE_INSTALL_DEMO_CONFIG=true \
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" opensearchproject/opensearch:latest >/dev/null
  echo "opensearch: $(docker image inspect opensearchproject/opensearch:latest --format '{{.Id}}')" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
  py --gpu eszkozok/jeloltek.py --out $D --seed $SEED_F1 > "$R/gen/jeloltek.log" 2>&1 || fail "S5–S6 (eredmenyek/F1/gen/jeloltek.log)"
  docker rm -f ldh-opensearch >/dev/null 2>&1
  py eszkozok/osszeallit.py --out $D --seed $SEED_F1 > "$R/gen/osszeallit.log" 2>&1 || fail "S7–S8 (eredmenyek/F1/gen/osszeallit.log)"
  cp $D/osszeallit_riport.json "$R/gen/"
  mark_ok jeloltek
fi

# --- auditok (4.5, 4.6) — az eredmény nem állítja le a fázist; a döntés a Naplóba ---------------
if ! done_marker audit; then
  say "F1: shortcut- és nehézség-audit" 3000
  py eszkozok/auditok.py shortcut --gen $D --out eredmenyek/F1/audit > "$R/audit/shortcut.log" 2>&1 || fail "shortcut-audit"
  py eszkozok/auditok.py nehezseg --gen $D --out eredmenyek/F1/audit > "$R/audit/nehezseg.log" 2>&1 || fail "nehézség-audit"
  mark_ok audit
fi

# --- előzetes hash (a bírálat ezen a változaton fut; a végleges hash a javítások után) ----------
if ! done_marker hash0; then
  (cd $D && sha256sum items_*.jsonl s1_katalogus.jsonl s2_szallitok.json parok.jsonl s4_sorok.jsonl s6_jeloltek.jsonl) \
    > "$R/fagyasztas_jelolt.sha256" || fail "hash"
  mark_ok hash0
fi

# --- Llama-3.3-70B bíráló a val/teszt itemeken -------------------------------------------
if ! done_marker llama; then
  say "F1: Llama-3.3-70B bíráló boot" 2700
  llama_start || { rc=$?; llama_stop "$R/biralo"; fail "Llama boot (rc=$rc, eredmenyek/F1/biralo/ldh-llama.log)"; }
  for sp in val-belso val-szallito T-belso T-szallito T-kozeli T-tavoli; do
    say "F1: Llama-bíráló — $sp" 2400
    py eszkozok/biralo.py --items $D/items_$sp.jsonl --out eredmenyek/F1/biralo/llama_$sp.jsonl \
      --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs --concurrency 4 \
      > "$R/biralo/llama_$sp.log" 2>&1 || { llama_stop "$R/biralo"; fail "Llama-bíráló $sp"; }
  done
  llama_stop "$R/biralo"
  mark_ok llama
fi

say "F1/A kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
