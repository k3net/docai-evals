#!/usr/bin/env bash
# K07F1B3 — a nehéz próbaminta 3. köre (07-runbook 3.3, D11; `szint07k3`): JAVASLAT, csak Dani jóváhagyása után indul.
# Terv (CPU), szövegek a Muse-zal, `final`, majd a kiolvasás mindkét kerettel (`kiolvas07k3`, `nehez3:` szeletek), mint a
# K07F1B / K07F1B2. Nyitott, szintetikus fejlesztési minta a 06 T500-sablonjain. Egy GPU-folyamat egyszerre.
#   setsid nohup kor07/eszkozok/k07f1b3_nehez.sh >/dev/null 2>&1 < /dev/null &
# Utána helyben: python3 kor07/eszkozok/b14_07.py --nehez --nehez-kor 3 (→ kor07/eredmenyek/F1/b14_nehez3.md)
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K07F1B3"
SRC="nehez3"
R="$EXP/logs/k07f1b3"
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

# az őrök nem a `fail`-lel lépnek ki: az törölné a másik fázis AKTIV_FAZIS-át és leállítaná a Muse-konténert
if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

say "terv és önteszt (3 család, 3. kör)"
cpy kor07/eszkozok/szint07k3.py onteszt >> "$R/onteszt.log" 2>&1 || fail "a tényellenőrző öntesztje"
for f in "${CSALADOK[@]}"; do
  cpy kor07/eszkozok/szint07k3.py terv --csalad "$f" >> "$R/$f.log" 2>&1 || fail "terv: $f"
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
  cpy kor07/eszkozok/szint07k3.py gen --csalad "$f" "${MUSE[@]}" --workers 64 >> "$R/$f.log" 2>&1 || fail "gen: $f"
  cpy kor07/eszkozok/szint07k3.py final --csalad "$f" >> "$R/$f.log" 2>&1 || fail "final: $f"
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
py07 kor07/eszkozok/kiolvas07k3.py kivon "${feladat[@]}" --out-root cache/k07/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas4.log" 2>&1 || fail "kiolvasás (4)"
sleep 20
say "kiolvasás, 06-os kétkimenetű keret" 1500
memoria_or07 "$R/memoria2.log"
py07 kor07/eszkozok/kiolvas07k3.py kivon --keret 2 "${feladat[@]}" --out-root cache/k07/jellemzok2 --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas2.log" 2>&1 || fail "kiolvasás (2)"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
