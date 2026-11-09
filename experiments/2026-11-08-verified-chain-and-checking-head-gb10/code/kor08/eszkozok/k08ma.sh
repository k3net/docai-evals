#!/usr/bin/env bash
# K08MA — az illesztett kontroll első fele: az illesztett (a) generálása a Muse-szal és az illesztés szöveges ellenőrzése. Fejet, kiolvasást és modellkimenetet nem érint; a második fele
# (kinyerés, lánc, kiolvasás, pontozás) csak a rögzítés után fut. Újrafuttatás előtt a `kor08/adat/M` félreteendő.
#   setsid nohup kor08/eszkozok/k08ma.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08MA"
D=kor08/adat/M
R="$EXP/logs/k08ma"
SEED="${M_SEED:-1}"
mkdir -p "$R"
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
L="$R/lepesek.log"
lep() { echo "[$(date '+%F %T')] $*" >> "$L"; }
kapu() { lep "KAPU: $*"; echo "[$(date '+%F %T')] $FAZIS: $*" > "FAILED-$FAZIS"; exit 1; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 -e M_GYOKER="$D" "$SUBJECT_IMAGE" "$@"
}
memoria_or() {
  ( while docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q true; do
      [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T') ($1)" >> "$R/memoria.log"; docker rm -f "$1"; }
      sleep 30
    done ) &
}
varj() {
  local t0; t0=$(date +%s)
  until curl -fsS "http://127.0.0.1:$2/health" >/dev/null 2>&1; do
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" != "true" ] && return 1
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && return 1
    [ $(( $(date +%s) - t0 )) -gt 2700 ] && return 1
    sleep 15
  done
}
lep "indul"
[ -e "$D" ] && kapu "$D már létezik"
[ -f AKTIV_FAZIS ] && kapu "fut egy fázis ($(cat AKTIV_FAZIS))"
docker ps --format '{{.Names}}' | grep -q . && kapu "fut egy konténer"
python3 kor08/eszkozok/illeszt08m.py >> "$L" 2>&1 || kapu "a mondatok ellenőrzése nem zöld"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
record_env
say "Muse indul" 900
lep "Muse indul"
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "a Muse nem indult"
varj ldh-muse 8450 || fail "a Muse nem állt fel"
memoria_or ldh-muse
for f in "${CSALADOK_08[@]}"; do
  say "illesztett (a): $f" 2400
  lep "minta $f"
  cpy kor08/eszkozok/szint08m.py terv --csalad "$f" >> "$R/minta_$f.log" 2>&1 || fail "terv $f"
  cpy kor08/eszkozok/szint08m.py gen --csalad "$f" "${MUSE[@]}" --workers 64 --seed "$SEED" >> "$R/minta_$f.log" 2>&1 || fail "gen $f"
  cpy kor08/eszkozok/szint08m.py final --csalad "$f" >> "$R/minta_$f.log" 2>&1 || fail "final $f"
done
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
lep "Muse leállt"
sleep 30
say "az illesztés szöveges ellenőrzése" 1800
lep "felszín"
py kor08/eszkozok/felszin08m.py --out kor08/eredmenyek/M/felszin >> "$R/felszin.log" 2>&1 || fail "felszin08m"
sha256sum "$D"/items/*.jsonl > "$R/minta.sha256"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
