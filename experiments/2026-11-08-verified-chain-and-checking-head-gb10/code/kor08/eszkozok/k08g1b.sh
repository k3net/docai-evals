#!/usr/bin/env bash
# K08G1B — 08 G1b, az értelmezési konstrukció próbája (`kor08/ertelmezes-javaslat.md`; Dani 11-02 „mehet”): a 07
# CAL-sablonjain (1) a szövegek generálása (Muse, `szint08e gen` + `final`), (2) a lánc orákulum-úton (`lanc08 futtat
# --forras ERT[kör]`), (3) kiolvasás a négyállapotú kerettel (`kiolvas08`, oERT[kör]), (4) a mérés (`g1b_ert08`).
# Megvárja, hogy ne fusson más fázis és konténer (egyszerre egy nagy GPU-folyamat; legfeljebb 6 órát vár). Fejlesztési
# minta, minden adat szintetikus. A 2. kör (Dani 11-02): áttételes jel, `szint08e --kor 2`.
#   setsid nohup kor08/eszkozok/k08g1b.sh [kör] >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1B"
KOR="${1:-1}"
SZ=$([ "$KOR" = 1 ] && echo ERT || echo "ERT$KOR")
R="$EXP/logs/k08g1b/kor$KOR"
mkdir -p "$R"
CSALADOK=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
lep() { echo "[$(date '+%F %T')] $*" >> "$R/lepesek.log"; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
memoria_or() {  # memoria_or <konténer>: 15 GB alatt leállítja (vLLM; a HF-betöltésre a lib07 őre vonatkozik)
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

# --- várakozás: más fázis vagy konténer ne fusson ------------------------------------------------------------------------
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

# --- 1. generálás (Muse) ----------------------------------------------------------------------------------------------
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
for f in "${CSALADOK[@]}"; do
  say "generálás: $f (120 terv)" 1200
  lep "gen: $f"
  cpy kor08/eszkozok/szint08e.py gen --kor "$KOR" --csalad "$f" "${MUSE[@]}" --workers 64 >> "$R/gen_$f.log" 2>&1 || fail "gen $f"
  cpy kor08/eszkozok/szint08e.py final --kor "$KOR" --csalad "$f" >> "$R/gen_$f.log" 2>&1 || fail "final $f"
done
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
sleep 20

# --- 2. a lánc, 3. kiolvasás, 4. mérés ---------------------------------------------------------------------------------
say "a lánc orákulum-úton" 120
lep "lánc"
python3 kor08/eszkozok/lanc08.py futtat --forras "$SZ" --ut orakulum --out "kor08/adat/G1/orakulum_$SZ" >> "$R/lanc.log" 2>&1 \
  || fail "lánc"
feladat=()
for f in "${CSALADOK[@]}"; do
  for m in kanonikus b1; do feladat+=(--feladat "o$SZ:$f:$SZ:$m"); done
done
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás, négyállapotú keret (kb. 360 item)" 1800
lep "kiolvasás"
docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf /exp/cache/k08/jellemzok/o${SZ}_*"  # a cache root tulajdonú
memoria_or07 "$R/memoria07.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root cache/k08/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
say "a mérés" 120
lep "mérés"
py kor08/eszkozok/g1b_ert08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1b --kor "$KOR" >> "$R/meres.log" 2>&1 \
  || fail "mérés"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
