#!/usr/bin/env bash
# K07F2G — a Gemma 4 26B-A4B-it második ítélete a friss CAL + TESZT minden itemjén (07-runbook 3.2; a 06 D14–D15
# protokollja, a `k06f2_gemma.sh` mintájára): a 03 `kiolvaso03` ids-módja, gold és item-id nélküli prompt, négy
# opciósorrend. Triage: itemet nem töröl (D15). Az összesítés (`gemma07.py osszesit`) helyben fut, back07 után; az
# auditkulcsonkénti ítélet Dani vak exportja után nyílik meg. A Gemma kimenete nem a pecsét alá tartozik (nem az alany).
# A családtávolság-audit (tavolsag06) a 07-ben nem fut: a családok a 06-éi, csak a sablonok újak.
#   setsid nohup kor07/eszkozok/k07f2_gemma.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K07F2G
R="$EXP/logs/k07f2g"
O=kor07/eredmenyek/F2/gemma
mkdir -p "$R" "$O"
GEMMA_SNAP="/hfg/models--google--gemma-4-26B-A4B-it/snapshots/$(basename "$(ls -d "$HOME"/hf-cache-gemma4/models--google--gemma-4-26B-A4B-it/snapshots/* | head -1)")"
kpy() {  # a kiolvasó a vLLM-image-ben, a saját uid-del, a Gemma-tokenizerrel (/hfg)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -v "$HOME/hf-cache-gemma4:/hfg:ro" \
    -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() { docker logs ldh-gemma4 > "$R/ldh-gemma4.log" 2>&1 || true; docker rm -f ldh-gemma4 >/dev/null 2>&1 || true; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 80 ] && fail "kevés szabad memória a Gemma indításához"

say "Gemma indul" 1500
docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
  -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
  --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 48 --max-logprobs 64 \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Gemma docker run"
t0=$(date +%s)
until curl -fsS http://127.0.0.1:8440/health >/dev/null 2>&1; do
  [ "$(docker inspect -f '{{.State.Running}}' ldh-gemma4 2>/dev/null)" != "true" ] && fail "a Gemma kilépett"
  [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && fail "memória < 15 GB a Gemma betöltése alatt"
  [ $(( $(date +%s) - t0 )) -gt 2700 ] && fail "a Gemma 45 perc alatt sem állt fel"
  sleep 15
done
say "Gemma kész $(( $(date +%s) - t0 )) s alatt; memória $(free -g | awk 'NR==2{print $7}') GB szabad"
( while docker inspect -f '{{.State.Running}}' ldh-gemma4 2>/dev/null | grep -q true; do
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T')" >> "$R/memoria.log"; docker rm -f ldh-gemma4; }
    sleep 30
  done ) &

say "Gemma-ítélet: 4500 item × 4 sorrend" 1000
kpy kor03/eszkozok/kiolvaso03.py \
  --items kor07/adat/f2/items/penzugy.bankparositas.jsonl kor07/adat/f2/items/muszaki.hibaelharitas.jsonl \
          kor07/adat/f2/items/szabaly.koltsegelszamolas.jsonl \
  --out "$O/gemma_f2.jsonl" --mode ids --url http://127.0.0.1:8440 --model gemma4-26b --tokenizer "$GEMMA_SNAP" \
  --perms 0,1,2,3 --concurrency 48 >> "$R/olvas.log" 2>&1 || fail "Gemma-kiolvasás"
ldh_cleanup
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
