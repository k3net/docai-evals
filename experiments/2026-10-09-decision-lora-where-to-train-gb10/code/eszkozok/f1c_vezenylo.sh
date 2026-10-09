#!/usr/bin/env bash
# F1/C — az F1 javító iterációja után az újragenerálás friss seeddel (runbook 9. pont, F1 2. lépés).
# A javító iteráció két auditra válaszol:
#   - shortcut (4.6): a kényszerített X(a) metaadat-rétegenként (osszeallit.py; F1B-ben igazolva: AUC 0,530);
#   - valószerűség (4.7, CV AUC 0,974 > 0,95): stílusprofil v2 — S3-prompt vegyes betűs példákkal,
#     zárójel-stílus, több pontos rövidítés, kiszerelés-jelölés, kódelőtag (generator.py).
# Az S1-katalógus marad (seed 20261003); S2–S8 seed 20261005. A v1 adat és eredmény *_v1 néven marad.
# Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F1C
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
SEED=20261005
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

if ! done_marker archiv; then
  [ -d adat/f1 ] && [ ! -d adat/f1_v1 ] && mv adat/f1 adat/f1_v1
  [ -d eredmenyek/F1 ] && [ ! -d eredmenyek/F1_v1 ] && mv eredmenyek/F1 eredmenyek/F1_v1
  mkdir -p adat/f1 eredmenyek/F1/{gen,audit,biralo}
  cp adat/f1_v1/s1_katalogus.jsonl adat/f1/ || fail "S1 másolás"
  echo "F1C: S1 = F1A (seed 20261003), S2–S8 seed $SEED, stílusprofil v2" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
  mark_ok archiv
fi
R="$EXP/eredmenyek/F1"
D=adat/f1

if ! done_marker gen; then
  say "F1C: generátor boot (Qwen3.8-Flash)" 7200
  ./eszkozok/generator_indit.sh ldh-generator 8410
  t0=$(date +%s); ok=0
  while [ $(( $(date +%s) - t0 )) -lt 2400 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-generator 2>/dev/null)" != "true" ] && break
    curl -fsS http://127.0.0.1:8410/health >/dev/null 2>&1 && { ok=1; break; }
    sleep 15
  done
  [ $ok = 1 ] || { docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1; fail "a generátor nem indult (eredmenyek/F1/gen/ldh-generator.log)"; }
  say "F1C: S2–S4 (S1 megtartva, seed $SEED, ~1 óra)" 6600
  py eszkozok/generator.py all --out $D --scale full --seed $SEED > "$R/gen/generator.log" 2>&1 \
    || { docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1; fail "S2–S4 (eredmenyek/F1/gen/generator.log)"; }
  docker logs ldh-generator > "$R/gen/ldh-generator.log" 2>&1
  docker rm -f ldh-generator >/dev/null 2>&1
  cp $D/generator_riport.json "$R/gen/"
  mark_ok gen
fi

if ! done_marker jeloltek; then
  say "F1C: OpenSearch + bge-m3 jelöltek, S7–S8 összeállítás" 3000
  docker rm -f ldh-opensearch >/dev/null 2>&1 || true
  docker run -d --name ldh-opensearch -p 9201:9200 -e discovery.type=single-node \
    -e DISABLE_SECURITY_PLUGIN=true -e DISABLE_INSTALL_DEMO_CONFIG=true \
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" opensearchproject/opensearch:latest >/dev/null
  py --gpu eszkozok/jeloltek.py --out $D --seed $SEED > "$R/gen/jeloltek.log" 2>&1 || fail "S5–S6 (eredmenyek/F1/gen/jeloltek.log)"
  docker rm -f ldh-opensearch >/dev/null 2>&1
  py eszkozok/osszeallit.py --out $D --seed $SEED > "$R/gen/osszeallit.log" 2>&1 || fail "S7–S8 (eredmenyek/F1/gen/osszeallit.log)"
  cp $D/osszeallit_riport.json "$R/gen/"
  mark_ok jeloltek
fi

if ! done_marker audit; then
  say "F1C: shortcut- és nehézség-audit" 2400
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
  say "F1C: Llama-3.3-70B bíráló boot" 2100
  llama_start || { rc=$?; llama_stop "$R/biralo"; fail "Llama boot (rc=$rc, eredmenyek/F1/biralo/ldh-llama.log)"; }
  for sp in val-belso val-szallito T-belso T-szallito T-kozeli T-tavoli; do
    say "F1C: Llama-bíráló — $sp" 1500
    py eszkozok/biralo.py --items $D/items_$sp.jsonl --out eredmenyek/F1/biralo/llama_$sp.jsonl \
      --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs --concurrency 4 \
      > "$R/biralo/llama_$sp.log" 2>&1 || { llama_stop "$R/biralo"; fail "Llama-bíráló $sp"; }
  done
  llama_stop "$R/biralo"
  mark_ok llama
fi

say "F1/C kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
