#!/usr/bin/env bash
# K00b/A — a 00b kiegészítés adatoldala (runbook 15. pont): valóban kitartott szállítós réteg (`T-ujszallito`).
#   generátor → `generator.py ujszallito` (az F1-ből: S1, train-párok, S3, S4 + 16 új csak-teszt szállító)
#   → OpenSearch + bge-m3 jelöltek (S5–S6) → S7–S8 (seed 20261005, mint az F1F) → split-átfedés-kapu
#   → shortcut- (csak a T-ujszallito) és nehézség-audit → fagyasztás-jelölt hash
#   → Llama-3.3-70B, majd Mistral Small 4 bíráló a T-ujszallito-n (triage, gold nélkül; 4.8)
# Utána a laptopon: Dani címke-átnézése (atnezes.py), fagyasztás; a mérés a K00b/B-ben.
# Az alany NEM fut. Az `adat/f1` csak olvasva. Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=K00bA
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
D=adat/k00b
R="$EXP/eredmenyek/K00b"
SEED_GEN=20261007
SEED_S78=20261005
EXTRA='{"reasoning_effort": "none"}'
mkdir -p "$D" "$R"/{gen,audit,biralo}
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env
[ -f "$EXP/eredmenyek/F1/atnezes/FAGYASZTVA.json" ] || fail "az F1 nincs befagyasztva"
[ -f adat/tenant_profil.json ] || fail "hiányzik az adat/tenant_profil.json (sync.sh to)"

if ! done_marker gen; then
  say "K00bA: generátor boot (Qwen3.8-Flash)" 14400
  ./eszkozok/generator_indit.sh ldh-generator 8410
  t0=$(date +%s); ok=0
  while [ $(( $(date +%s) - t0 )) -lt 2400 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-generator 2>/dev/null)" != "true" ] && break
    curl -fsS http://127.0.0.1:8410/health >/dev/null 2>&1 && { ok=1; break; }
    sleep 15
  done
  [ $ok = 1 ] || { docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1; fail "a generátor nem indult ($R/gen/ldh-generator.log)"; }
  say "K00bA: új szállítók, párok, S3 (csak az új párok), S4" 12600
  py eszkozok/generator.py ujszallito --out $D --src adat/f1 --seed $SEED_GEN --n-new 16 > "$R/gen/generator.log" 2>&1 \
    || { docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1; fail "ujszallito ($R/gen/generator.log)"; }
  docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1
  docker rm -f ldh-generator >/dev/null 2>&1
  cp $D/generator_riport.json "$R/gen/"
  mark_ok gen
fi

if ! done_marker jeloltek; then
  say "K00bA: OpenSearch + bge-m3 jelöltek, S7–S8 összeállítás" 11400
  docker rm -f ldh-opensearch >/dev/null 2>&1 || true
  docker run -d --name ldh-opensearch -p 9201:9200 -e discovery.type=single-node \
    -e DISABLE_SECURITY_PLUGIN=true -e DISABLE_INSTALL_DEMO_CONFIG=true \
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" opensearchproject/opensearch:latest >/dev/null
  py --gpu eszkozok/jeloltek.py --out $D --seed $SEED_S78 > "$R/gen/jeloltek.log" 2>&1 || fail "S5–S6 ($R/gen/jeloltek.log)"
  docker rm -f ldh-opensearch >/dev/null 2>&1
  py eszkozok/osszeallit.py --out $D --seed $SEED_S78 > "$R/gen/osszeallit.log" 2>&1 || fail "S7–S8 ($R/gen/osszeallit.log)"
  cp $D/osszeallit_riport.json "$R/gen/"
  mark_ok jeloltek
fi

if ! done_marker audit; then
  say "K00bA: split-átfedés-kapu, shortcut- és nehézség-audit" 9600
  py eszkozok/split_audit.py --gen $D --ref adat/f1 --split T-ujszallito --szallito-kitartott --latott-cikk \
    --out eredmenyek/K00b/audit/split.json > "$R/audit/split.log" 2>&1 || fail "split-átfedés-kapu bukott ($R/audit/split.json)"
  py eszkozok/auditok.py shortcut --gen $D --splits T-ujszallito --out eredmenyek/K00b/audit > "$R/audit/shortcut.log" 2>&1 \
    || fail "shortcut-audit"
  py eszkozok/auditok.py nehezseg --gen $D --out eredmenyek/K00b/audit > "$R/audit/nehezseg.log" 2>&1 || fail "nehézség-audit"
  py -c "import json,sys; sys.exit(0 if json.load(open('eredmenyek/K00b/audit/shortcut.json'))['kapu_ok'] else 1)" \
    || fail "shortcut-kapu bukott (CV AUC > 0,55; $R/audit/shortcut.json) — a 15. pont szerint egy javító kör jöhet"
  mark_ok audit
fi

if ! done_marker hash0; then
  (cd $D && sha256sum items_T-ujszallito.jsonl s2_szallitok.json parok.jsonl s4_sorok.jsonl s6_jeloltek.jsonl) \
    > "$R/fagyasztas_jelolt.sha256" || fail "hash"
  mark_ok hash0
fi

if ! done_marker llama; then
  say "K00bA: Llama-3.3-70B bíráló boot és futás" 7200
  llama_start || { rc=$?; llama_stop "$R/biralo"; fail "Llama boot (rc=$rc, $R/biralo/ldh-llama.log)"; }
  py eszkozok/biralo.py --items $D/items_T-ujszallito.jsonl --out eredmenyek/K00b/biralo/llama_T-ujszallito.jsonl \
    --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs --concurrency 4 \
    > "$R/biralo/llama_T-ujszallito.log" 2>&1 || { llama_stop "$R/biralo"; fail "Llama-bíráló"; }
  llama_stop "$R/biralo"
  mark_ok llama
fi

if ! done_marker mistral; then
  say "K00bA: Mistral Small 4 bíráló boot és futás (logprobs mód, mint az F1-ben)" 4800
  mistral_start || { rc=$?; mistral_stop "$R/biralo"; fail "Mistral boot (rc=$rc, $R/biralo/ldh-mistral.log)"; }
  py eszkozok/biralo.py --items $D/items_T-ujszallito.jsonl --out eredmenyek/K00b/biralo/mistral_T-ujszallito.jsonl \
    --url http://127.0.0.1:8430/v1 --model mistral-small-4 --mode logprobs --concurrency 4 --extra-body "$EXTRA" \
    > "$R/biralo/mistral_T-ujszallito.log" 2>&1 || { mistral_stop "$R/biralo"; fail "Mistral-bíráló"; }
  mistral_stop "$R/biralo"
  mark_ok mistral
fi

say "K00b/A kész — jöhet Dani címke-átnézése" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
