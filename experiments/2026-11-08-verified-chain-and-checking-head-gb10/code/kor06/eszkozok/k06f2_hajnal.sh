#!/usr/bin/env bash
# K06F2H — hajnali sor (Dani, 2026-10-29: „04:00 és 08:00 közt … kezdd el építeni a legvalószínűbben jó családot”):
# a K06F2 éjszakai sor után a hibaelhárítás teljes építése a szabálytáblás recepttel, Dani próbalap-döntése ELŐTT,
# fenntartással: ha Dani a próbát elveti, a teljes építés eldobandó; addig a kimenetbe senki nem néz bele, csak a
# darabszámok kerülnek a naplóba.
# Programos kapu: a K06F2 hiba nélkül végzett, és a szabálytáblás próba legalább 22/24 itemet adott.
#   setsid nohup kor06/eszkozok/k06f2_hajnal.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F2H
R="$EXP/logs/k06f2h"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
F=muszaki.hibaelharitas
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() { docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"

say "vár a K06F2 végére"
until [ -f DONE-K06F2 ] || [ -f FAILED-K06F2 ]; do sleep 60; done
[ -f FAILED-K06F2 ] && { say "a K06F2 hibával állt le, a hajnali sor nem indul"; echo "K06F2 hiba" > "FAILED-$FAZIS"; exit 1; }
n=$(wc -l < "kor06/adat/f2/items/$F.proba.jsonl" 2>/dev/null || echo 0)
[ "$n" -lt 22 ] && { say "a szabálytáblás próba $n/24 itemet adott (< 22), a teljes építés nem indul"; echo "kapu: $n/24" > "FAILED-$FAZIS"; exit 1; }
[ -e "kor06/adat/f2/raw/$F.jsonl" ] && fail "a hibaelhárítás teljes építése már létezik"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 100 ] && fail "kevés szabad memória a Muse indításához"

say "kapu rendben (próba: $n/24); Muse indul" 900
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Muse docker run"
t0=$(date +%s)
until curl -fsS http://127.0.0.1:8450/health >/dev/null 2>&1; do
  [ "$(docker inspect -f '{{.State.Running}}' ldh-muse 2>/dev/null)" != "true" ] && fail "a Muse kilépett"
  [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && fail "memória < 15 GB a Muse betöltése alatt"
  [ $(( $(date +%s) - t0 )) -gt 2700 ] && fail "a Muse 45 perc alatt sem állt fel"
  sleep 15
done
( while docker inspect -f '{{.State.Running}}' ldh-muse 2>/dev/null | grep -q true; do
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T')" >> "$R/memoria.log"; docker rm -f ldh-muse; }
    sleep 30
  done ) &

ts=$(date +%s)
say "sablonok (120 szabálytábla)" 1800
cpy kor06/eszkozok/szint06.py sablon --csalad "$F" "${MUSE[@]}" --workers 32 >> "$R/$F.log" 2>&1 || fail "sablon"
cpy kor06/eszkozok/szint06.py terv --csalad "$F" >> "$R/$F.log" 2>&1 || fail "terv"
say "generálás" 5400
cpy kor06/eszkozok/szint06.py gen --csalad "$F" "${MUSE[@]}" --workers 64 >> "$R/$F.log" 2>&1 || fail "gen"
cpy kor06/eszkozok/szint06.py final --csalad "$F" >> "$R/$F.log" 2>&1 || fail "final"
for k in 1 2; do
  python3 -c "import json,sys; r=json.load(open('kor06/adat/f2/items/$F.osszesito.json')); sys.exit(0 if r['hianyzo_cellak'] else 1)" || break
  cp "kor06/adat/f2/items/$F.osszesito.json" "kor06/adat/f2/items/$F.osszesito.kor$(( k - 1 )).json"
  cpy kor06/eszkozok/szint06.py terv --csalad "$F" --potlas "$k" >> "$R/$F.log" 2>&1 || fail "pótlás-terv $k"
  say "pótlókör $k" 1200
  cpy kor06/eszkozok/szint06.py gen --csalad "$F" "${MUSE[@]}" --workers 64 >> "$R/$F.log" 2>&1 || fail "pótlás-gen $k"
  cpy kor06/eszkozok/szint06.py final --csalad "$F" >> "$R/$F.log" 2>&1 || fail "pótlás-final $k"
done
ldh_cleanup
cpy kor06/eszkozok/szint06.py audit >> "$R/audit.log" 2>&1 || fail "audit"
python3 -c "import json; r=json.load(open('kor06/adat/f2/items/$F.osszesito.json')); print('$F', r['item'], 'item;', 'hiányzó cellák:', r['hianyzo_cellak'] or 'nincs')" \
  >> "$R/osszefoglalo.log"
say "kész ($(( ($(date +%s) - ts) / 60 )) perc; fenntartással, Dani próbalap-döntéséig)"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
