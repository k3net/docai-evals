#!/usr/bin/env bash
# KE2 — E irány: az adatkészlet alapmérései (publikacio/E-adatkeszlet-terv.md 10.). Csak szintetikus tételek.
#   0. füstpróba (20 tétel, direct és think)   1. direct: 4 konfiguráció × 2 keret   2. think: 3 konfiguráció, négyállapotú keret
#   setsid nohup publikacio/eszkozok/ke2.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=KE2
R="$EXP/logs/ke2"; D=publikacio/E/data; O=publikacio/E/baseline/raw; B=publikacio/E/code/baseline.py
mkdir -p "$R" "$O"
L="$R/lepesek.log"
lep() { echo "[$(date '+%F %T')] $*" >> "$L"; }
[ -f AKTIV_FAZIS ] && { echo "[$(date '+%F %T')] fut egy fázis: $(cat AKTIV_FAZIS)" > "FAILED-$FAZIS"; exit 1; }
docker ps --format '{{.Names}}' | grep -q . && { echo "[$(date '+%F %T')] fut egy konténer" > "FAILED-$FAZIS"; exit 1; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
record_env
lep "indul; az alany (vLLM, LoRA nélkül, 16 384 token)"
say "az alany indítása" 600
docker rm -f ldh-qwen >/dev/null 2>&1 || true
docker run -d --name ldh-qwen --gpus all --ipc host -p "$SUBJECT_PORT:8000" -v "$HOME/.cache/huggingface:/root/.cache/huggingface" \
  -e HF_HUB_OFFLINE=1 "$SUBJECT_IMAGE" "$SUBJECT_MODEL" --max-model-len 16384 --gpu-memory-utilization 0.5 >> "$R/alany.log" 2>&1
subject_wait ldh-qwen 2400 || fail "az alany nem állt fel"
U="http://127.0.0.1:$SUBJECT_PORT"
lep "0. füstpróba"
head -n 20 "$D/calc_traps/test.jsonl" > "$R/fust.jsonl"
python3 $B run --items "$R/fust.jsonl" --out "$R/fust.direct.jsonl" --frame 4 --mode direct --url "$U" --model "$SUBJECT_MODEL" > "$R/fust.log" 2>&1 || fail "füstpróba (direct)"
python3 $B run --items "$R/fust.jsonl" --out "$R/fust.think.jsonl" --frame 4 --mode think --url "$U" --model "$SUBJECT_MODEL" --concurrency 20 >> "$R/fust.log" 2>&1 || fail "füstpróba (think)"
python3 - "$R" <<'PY' || fail "füstpróba: a válaszok nem értelmezhetők ($R/fust.*.jsonl)"
import json, sys
for m in ("direct", "think"):
    r = [json.loads(x) for x in open(f"{sys.argv[1]}/fust.{m}.jsonl")]
    n = sum(x["pred"] is not None for x in r)
    print(m, n, len(r))
    if n < 15:
        sys.exit(1)
PY
lep "1. direct"
for k in calc_traps minimal_pairs interpretation natural; do for f in 2 4; do
  say "direct: $k, $f állapot" 1200
  python3 $B run --items "$D/$k/test.jsonl" --out "$O/$k.f$f.direct.jsonl" --frame $f --mode direct --url "$U" --model "$SUBJECT_MODEL" --concurrency 32 > "$R/direct.$k.f$f.log" 2>&1 || fail "direct $k f$f"
done; done
lep "2. think"
say "think: calc_traps" 7200
python3 $B run --items "$D/calc_traps/test.jsonl" --out "$O/calc_traps.f4.think.jsonl" --frame 4 --mode think --url "$U" --model "$SUBJECT_MODEL" --concurrency 48 > "$R/think.calc_traps.log" 2>&1 || fail "think calc_traps"
lep "2b. think: minimal_pairs"
say "think: minimal_pairs" 7200
python3 $B run --items "$D/minimal_pairs/test.jsonl" --out "$O/minimal_pairs.f4.think.jsonl" --frame 4 --mode think --url "$U" --model "$SUBJECT_MODEL" --concurrency 48 > "$R/think.minimal_pairs.log" 2>&1 || fail "think minimal_pairs"
lep "2c. think: interpretation (minta)"
say "think: interpretation" 7200
python3 $B run --items "$D/interpretation/test.jsonl" --sample publikacio/E/think_sample_interpretation.json --out "$O/interpretation.f4.think.jsonl" --frame 4 --mode think --url "$U" --model "$SUBJECT_MODEL" --concurrency 48 > "$R/think.interpretation.log" 2>&1 || fail "think interpretation"
subject_stop ldh-qwen "$R"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
