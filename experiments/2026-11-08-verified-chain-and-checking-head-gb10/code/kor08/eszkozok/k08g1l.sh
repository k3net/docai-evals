#!/usr/bin/env bash
# K08G1L — a G2 szabályforgatókönyveinek eldobható próbája (Dani 11-03 21:40: mind a 90-en, Muse + Gemma; `proba08g2`):
# a K08G1K után (1) a próba sablonjai és tervei saját seeddel (CPU), (2) Muse-generálás és tényellenőrzés, (3) Gemma-
# triage (a 03 `kiolvaso03` ids-módja, gold és item-id nélkül, négy sorrend), (4) összesítés forgatókönyvenként. **Nem
# G2-adat:** a kimenet `kor08/adat/G1/proba_g2` és `kor08/eredmenyek/G1/proba_g2`; nem auditáljuk, nem értékeljük.
# Egyszerre egy nagy GPU-folyamat: előbb a Muse, utána a Gemma. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1l.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1L"
R="$EXP/logs/k08g1l"
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

# --- várakozás: előbb a K08G1K vége, utána szabad gép (a `fail` itt még nem hívható: más fázis ldh-konténereit is leállítaná)
lep "várakozás a K08G1K végére"
t0=$(date +%s)
until [ -f DONE-K08G1K ] || [ -f FAILED-K08G1K ]; do
  [ $(( $(date +%s) - t0 )) -gt 36000 ] && { echo "$FAZIS: 10 óra után sincs vége a K08G1K-nak" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
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

# --- 1. a próba sablonjai és tervei (CPU) ---------------------------------------------------------------------------------
say "a próba sablonjai és tervei" 120
lep "sablon, terv"
python3 kor08/eszkozok/forgatokonyv08_szab.py ellenoriz > "$R/forgatokonyv.log" 2>&1 || fail "a forgatókönyvek szerkezeti ellenőrzése"
[ -f "$P/sablon/$F.jsonl" ] || cpy kor08/eszkozok/proba08g2.py szint sablon --csalad "$F" >> "$R/terv.log" 2>&1 || fail "sablon"
for r in "${RESZEK[@]}"; do
  cpy kor08/eszkozok/proba08g2.py szint terv --csalad "$F" --resz "$r" >> "$R/terv.log" 2>&1 || fail "terv $r"
done
python3 - "$P" <<'PY' >> "$R/terv.log" 2>&1 || fail "a terv nem a várt (320 + 400)"
import sys
n = [sum(1 for _ in open(f"{sys.argv[1]}/{r}/terv/szabaly.koltsegelszamolas.jsonl", encoding="utf-8")) for r in ("ert_teszt", "ert_tanito")]
print("tervek:", n)
sys.exit(0 if n == [320, 400] else 1)
PY

# --- 2. Muse: generálás és tényellenőrzés ---------------------------------------------------------------------------------
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
for r in "${RESZEK[@]}"; do
  say "generálás: $r" 1800
  lep "gen $r"
  cpy kor08/eszkozok/proba08g2.py szint gen --csalad "$F" --resz "$r" "${MUSE[@]}" --workers 64 >> "$R/gen_$r.log" 2>&1 || fail "gen $r"
  cpy kor08/eszkozok/proba08g2.py szint final --csalad "$F" --resz "$r" >> "$R/gen_$r.log" 2>&1 || fail "final $r"
done
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
lep "Muse leállt"
sleep 30

# --- 3. Gemma-triage, négy sorrend ----------------------------------------------------------------------------------------
GEMMA_SNAP="/hfg/models--google--gemma-4-26B-A4B-it/snapshots/$(basename "$(ls -d "$HOME"/hf-cache-gemma4/models--google--gemma-4-26B-A4B-it/snapshots/* | head -1)")"
kpy() {  # a kiolvasó a vLLM-image-ben, a saját uid-del, a Gemma-tokenizerrel (/hfg)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -v "$HOME/hf-cache-gemma4:/hfg:ro" \
    -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
mkdir -p "$O/gemma"
say "Gemma indul" 1500
lep "Gemma indul"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 80 ] && fail "kevés szabad memória a Gemma indításához"
docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
  -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
  --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 48 --max-logprobs 64 \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Gemma docker run"
varj ldh-gemma4 8440 || fail "a Gemma nem állt fel"
memoria_or ldh-gemma4
for r in "${RESZEK[@]}"; do
  say "Gemma-ítélet: $r" 1200
  lep "Gemma $r"
  kpy kor03/eszkozok/kiolvaso03.py --items "$P/$r/items/$F.jsonl" --out "$O/gemma/$r.jsonl" --mode ids \
      --url http://127.0.0.1:8440 --model gemma4-26b --tokenizer "$GEMMA_SNAP" --perms 0,1,2,3 --concurrency 48 \
      >> "$R/gemma.log" 2>&1 || fail "Gemma $r"
done
docker logs ldh-gemma4 > "$R/ldh-gemma4.log" 2>&1 || true
docker rm -f ldh-gemma4 >/dev/null 2>&1 || true
sleep 20

# --- 4. összesítés ----------------------------------------------------------------------------------------------------------
say "összesítés" 60
lep "összesítés"
cpy kor08/eszkozok/proba08g2.py osszesit --gemma "$O/gemma/ert_teszt.jsonl" "$O/gemma/ert_tanito.jsonl" >> "$R/osszesit.log" 2>&1 \
  || fail "összesítés"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
