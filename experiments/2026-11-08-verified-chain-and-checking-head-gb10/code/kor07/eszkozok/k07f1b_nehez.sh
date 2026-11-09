#!/usr/bin/env bash
# K07F1B — a nehéz próbaminta (07-runbook 3.3, D11; F1 második fele): a terv (szint07, a 06 T500-sablonjain), a szövegek a
# Muse-zal (mint a 06 F2-ben), `final`, majd a kiolvasás mindkét kerettel: a négyállapotú (cache/k07/jellemzok) és a
# 06-os kétkimenetű (cache/k07/jellemzok2). Nyitott adat, pecsét nélkül. A K07F1 végét megvárja (egy GPU-folyamat).
#   setsid nohup kor07/eszkozok/k07f1b_nehez.sh >/dev/null 2>&1 < /dev/null &
#   KOR=2 setsid nohup kor07/eszkozok/k07f1b_nehez.sh … — a konstrukció 2. köre (szint07 --kor 2, kor07/adat/nehez2,
#   a kiolvasás `nehez2:` szeletekkel, K07F1B2)
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
KOR="${KOR:-1}"
SUF=$([ "$KOR" = 1 ] || echo "$KOR")
FAZIS="K07F1B$SUF"
SRC="nehez$SUF"
R="$EXP/logs/k07f1b$SUF"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
CSALADOK=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() {
  docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true
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
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" != "true" ] && fail "$1 kilépett"
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && fail "memória < 15 GB a(z) $1 betöltése alatt"
    [ $(( $(date +%s) - t0 )) -gt 2700 ] && fail "$1 45 perc alatt sem állt fel"
    sleep 15
  done
}
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"

say "vár a K07F1 végére"
until [ -f DONE-K07F1 ] || [ -f FAILED-K07F1 ]; do sleep 60; done
[ -f FAILED-K07F1 ] && say "a K07F1 hibával állt le ($(cat FAILED-K07F1)); a nehéz minta ettől független, indul"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"

say "terv (3 család, $KOR. kör)"
for f in "${CSALADOK[@]}"; do
  cpy kor07/eszkozok/szint07.py terv --csalad "$f" --kor "$KOR" >> "$R/$f.log" 2>&1 || fail "terv: $f"
done
say "Muse indul" 900
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Muse docker run"
varj ldh-muse 8450
memoria_or ldh-muse
for f in "${CSALADOK[@]}"; do
  say "generálás: $f" 600
  cpy kor07/eszkozok/szint07.py gen --csalad "$f" --kor "$KOR" "${MUSE[@]}" --workers 64 >> "$R/$f.log" 2>&1 || fail "gen: $f"
  cpy kor07/eszkozok/szint07.py final --csalad "$f" --kor "$KOR" >> "$R/$f.log" 2>&1 || fail "final: $f"
done
ldh_cleanup
sleep 20

feladat=()
for f in "${CSALADOK[@]}"; do
  for m in kanonikus b1; do feladat+=(--feladat "$SRC:$f:NEHEZ:$m"); done
done
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás, négyállapotú keret" 1500
memoria_or07 "$R/memoria4.log"
py07 kor07/eszkozok/kiolvas07.py kivon "${feladat[@]}" --out-root cache/k07/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas4.log" 2>&1 || fail "kiolvasás (4)"
sleep 20
say "kiolvasás, 06-os kétkimenetű keret" 1500
memoria_or07 "$R/memoria2.log"
py07 kor07/eszkozok/kiolvas07.py kivon --keret 2 "${feladat[@]}" --out-root cache/k07/jellemzok2 --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas2.log" 2>&1 || fail "kiolvasás (2)"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
