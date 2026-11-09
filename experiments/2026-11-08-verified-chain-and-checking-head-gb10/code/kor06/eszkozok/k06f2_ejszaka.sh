#!/usr/bin/env bash
# K06F2 — éjszakai sor (06-runbook 3.4–3.5, 9. F2; Dani, 2026-10-29): Muse-Glimmer-30B rögzített revízióval.
#   1. a hibaelhárítás új, szabálytáblás próbája (családonként 24 item, Dani reggel nézi át; hibája nem állítja le a sort)
#   2. a bank- és a szabálycsalád teljes építése: sablon → terv → generálás → végső összeállítás; legfeljebb két
#      pótlókör a hiányos cellákra (az előző összesítő körönként megmarad)
#   3. a címkeaudit mintája e két családra (D14)
# Modellszűrő nincs (D15). A hibaelhárítás teljes építése Dani próbalap-döntése után. A laptoptól független.
#   setsid nohup kor06/eszkozok/k06f2_ejszaka.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F2
R="$EXP/logs/k06f2"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
CSALADOK=(penzugy.bankparositas szabaly.koltsegelszamolas)
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() { docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true; }
heartbeat_start $$
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
[ -e kor06/adat/f2 ] && fail "a kor06/adat/f2 már létezik (előbb archiváld)"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 100 ] && fail "kevés szabad memória a Muse indításához"
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"

say "Muse indul (revízió ${MUSE_REV:0:8})" 900
docker rm -f ldh-muse >/dev/null 2>&1 || true
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
say "Muse kész ($(( $(date +%s) - t0 )) s)"

# figyelő: a generálás alatt is legalább 15 GB szabad memória kell (spark-dev OOM-fagyás, memória)
( while docker inspect -f '{{.State.Running}}' ldh-muse 2>/dev/null | grep -q true; do
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T')" >> "$R/memoria.log"; docker rm -f ldh-muse; }
    sleep 30
  done ) &

gen_csalad() {  # gen_csalad <család> — a hátralévő tervek generálása, majd az összeállítás
  local f="$1" n0 n1
  n0=$(wc -l < "kor06/adat/f2/raw/$f.jsonl" 2>/dev/null || echo 0)
  cpy kor06/eszkozok/szint06.py gen --csalad "$f" "${MUSE[@]}" --workers 64 >> "$R/$f.log" 2>&1 || fail "gen $f"
  n1=$(wc -l < "kor06/adat/f2/raw/$f.jsonl")
  cpy kor06/eszkozok/szint06.py final --csalad "$f" >> "$R/$f.log" 2>&1 || fail "final $f"
  echo "$f: $(( n1 - n0 )) új generálás" >> "$R/osszefoglalo.log"
}

hiba_proba() {  # a szabálytáblás hibaelhárítás próbája; hiba esetén csak naplóz
  local f=muszaki.hibaelharitas
  cpy kor06/eszkozok/szint06.py sablon --csalad "$f" --proba "${MUSE[@]}" --workers 4 >> "$R/$f.proba.log" 2>&1 || return 1
  cpy kor06/eszkozok/szint06.py terv --csalad "$f" --proba >> "$R/$f.proba.log" 2>&1 || return 1
  cpy kor06/eszkozok/szint06.py gen --csalad "$f" --proba "${MUSE[@]}" --workers 24 >> "$R/$f.proba.log" 2>&1 || return 1
  cpy kor06/eszkozok/szint06.py final --csalad "$f" --proba >> "$R/$f.proba.log" 2>&1 || return 1
  cpy kor06/eszkozok/szint06.py lap >> "$R/$f.proba.log" 2>&1 || return 1
}
say "hibaelhárítás: szabálytáblás próba" 900
if hiba_proba; then echo "hibaelhárítás-próba: kész ($(grep -h 'item /' "$R/muszaki.hibaelharitas.proba.log" | tail -1))" >> "$R/osszefoglalo.log"
else echo "hibaelhárítás-próba: HIBA (lásd muszaki.hibaelharitas.proba.log)" >> "$R/osszefoglalo.log"; fi

for f in "${CSALADOK[@]}"; do
  ts=$(date +%s)
  cpy kor06/eszkozok/szint06.py sablon --csalad "$f" >> "$R/$f.log" 2>&1 || fail "sablon $f"
  cpy kor06/eszkozok/szint06.py terv --csalad "$f" >> "$R/$f.log" 2>&1 || fail "terv $f"
  say "generálás: $f" 4800
  gen_csalad "$f"
  say "kész: $f ($(( ($(date +%s) - ts) / 60 )) perc)"
done

for k in 1 2; do
  hiany=0
  for f in "${CSALADOK[@]}"; do
    python3 -c "import json,sys; r=json.load(open('kor06/adat/f2/items/$f.osszesito.json')); sys.exit(0 if r['hianyzo_cellak'] else 1)" \
      && hiany=1 && {
        cp "kor06/adat/f2/items/$f.osszesito.json" "kor06/adat/f2/items/$f.osszesito.kor$(( k - 1 )).json"
        cpy kor06/eszkozok/szint06.py terv --csalad "$f" --potlas "$k" >> "$R/$f.log" 2>&1 || fail "pótlás-terv $k $f"
        say "pótlókör $k: $f" 1200
        gen_csalad "$f"
      }
  done
  [ "$hiany" = 0 ] && break
done

ldh_cleanup
cpy kor06/eszkozok/szint06.py audit >> "$R/audit.log" 2>&1 || fail "audit"
for f in "${CSALADOK[@]}"; do
  python3 -c "import json; r=json.load(open('kor06/adat/f2/items/$f.osszesito.json')); print('$f', r['item'], 'item;', 'hiányzó cellák:', r['hianyzo_cellak'] or 'nincs')" \
    >> "$R/osszefoglalo.log"
done
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
