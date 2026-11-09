#!/usr/bin/env bash
# K08G1M — a K08G1L angol képzés-goldú (a) kieséseinek diagnózisa (Dani 11-04: a „course” / „exam” kulcsszó okának
# igazolása; `proba08g2 diag`): a próba 18 tervén 5 próbálkozás, a szöveggel együtt (az első 3 a generálás seedjével).
# Nem G2-adat; a kimenet `kor08/eredmenyek/G1/proba_g2/diag_ken.jsonl`. Egy nagy GPU-folyamat (Muse). Minden adat
# szintetikus.
#   setsid nohup kor08/eszkozok/k08g1m.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1M"
R="$EXP/logs/k08g1m"
mkdir -p "$R"
F=szabaly.koltsegelszamolas
P=kor08/adat/G1/proba_g2
O=kor08/eredmenyek/G1/proba_g2
RESZEK=(ert_teszt ert_tanito)
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
lep() { echo "[$(date '+%F %T')] $*" >> "$R/lepesek.log"; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
memoria_or() {  # memoria_or <konténer>: 15 GB alatt leállítja
  ( while docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q true; do
      [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T') ($1)" >> "$R/memoria.log"; docker rm -f "$1"; }
      sleep 30
    done ) &
}
varj() {  # varj <konténer> <port>
  local t0; t0=$(date +%s)
  until curl -fsS "http://127.0.0.1:$2/health" >/dev/null 2>&1; do
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" != "true" ] && return 1
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && return 1
    [ $(( $(date +%s) - t0 )) -gt 2700 ] && return 1
    sleep 15
  done
}

# --- várakozás: más fázis vagy konténer ne fusson -------------------------------------------------------------------------
lep "várakozás, amíg más fázis vagy konténer fut"
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
[ -f "$P/ert_teszt/terv/$F.jsonl" ] && [ -f "$P/ert_tanito/terv/$F.jsonl" ] || fail "nincs meg a próba terve"

# --- Muse: a diagnózis ---------------------------------------------------------------------------------
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
say "diagnózis: 18 terv × 5" 600
lep "diag"
cpy kor08/eszkozok/proba08g2.py diag "${MUSE[@]}" >> "$R/diag.log" 2>&1 || fail "diag"
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
lep "Muse leállt"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
