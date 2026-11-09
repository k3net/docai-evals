#!/usr/bin/env bash
# K07EJ — éjszakai sor (2026-10-31 → 11-01), a 07-runbook döntést nem kérő GPU-munkái, egymás után:
#   B. F1M: a D_meta (6000 item) kiolvasása a négyállapotú prompttal, kanonikus + b1, a cache/k07/jellemzok alá
#      (nyitott; a B1-4R előtanításához). Előtte span-ellenőrzés (CPU).                                   ~3 óra
#   C. F2: a friss CAL + TESZT generálása új sablonokkal (szint07 friss-*, Muse), 3 család.              ~3 óra
#   D. F3: a friss szeletek kiolvasása pecsét alatt, mindkét kerettel (cache/k07/pecset/jellemzok[2]),
#      pecsétmanifest K07F3.                                                                              ~5 óra
# A fázisok saját DONE/FAILED jelzőt kapnak; a C hibája a D-t kihagyja, a B hibája nem állít meg semmit. Egyszerre egy
# GPU-folyamat; a HF-betöltésnél a lib07 őre (63 GB swap mellett).
#   setsid nohup kor07/eszkozok/k07ejjel.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor07/eszkozok/lib07.sh
FAZIS=K07EJ
R="$EXP/logs/k07ejjel"
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
lep() { echo "[$(date '+%F %T')] $*" >> "$R/lepesek.log"; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS" FAILED-K07F1M DONE-K07F1M FAILED-K07F2 DONE-K07F2 FAILED-K07F3 DONE-K07F3
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"

# --- B. F1M -------------------------------------------------------------------------------------------------------------
say "F1M: span-ellenőrzés a D_meta-n (CPU)"
lep "F1M span-ellenőrzés"
if py kor07/eszkozok/kiolvas07.py spanok --szelet k05:D_meta --perms-is --out kor07/eredmenyek/F1M/spanok >> "$R/f1m.log" 2>&1; then
  say "F1M: a D_meta kiolvasása (6000 item, kanonikus + b1 = 24 000 forward)" 10800
  lep "F1M kiolvasás indul"
  memoria_or07 "$R/f1m.memoria.log"
  if py07 kor07/eszkozok/kiolvas07.py kivon --feladat k05:D_meta:kanonikus --feladat k05:D_meta:b1 \
       --out-root cache/k07/jellemzok --status STATUS-K07F1M-kiolvasas >> "$R/f1m.log" 2>&1; then
    date '+%F %T' > DONE-K07F1M; lep "F1M kész"
  else
    echo "$(date '+%F %T') kiolvasás" > FAILED-K07F1M; lep "F1M HIBA: kiolvasás"
  fi
else
  echo "$(date '+%F %T') span-ellenőrzés" > FAILED-K07F1M; lep "F1M HIBA: span-ellenőrzés"
fi
sleep 20

# --- C. F2 --------------------------------------------------------------------------------------------------------------
f2_ok=1
say "F2: Muse indul" 900
lep "F2 Muse indul"
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || f2_ok=0
if [ "$f2_ok" = 1 ] && varj ldh-muse 8450; then
  memoria_or ldh-muse
  for f in "${CSALADOK[@]}"; do
    say "F2: sablon + terv: $f" 1200
    lep "F2 sablon: $f"
    cpy kor07/eszkozok/szint07.py friss-sablon --csalad "$f" "${MUSE[@]}" --workers 16 >> "$R/f2_$f.log" 2>&1 || { f2_ok=0; lep "F2 HIBA sablon: $f"; break; }
    cpy kor07/eszkozok/szint07.py friss-terv --csalad "$f" >> "$R/f2_$f.log" 2>&1 || { f2_ok=0; lep "F2 HIBA terv: $f"; break; }
    say "F2: generálás: $f (kb. 2000 szöveg)" 3600
    lep "F2 gen: $f"
    cpy kor07/eszkozok/szint07.py friss-gen --csalad "$f" "${MUSE[@]}" --workers 64 >> "$R/f2_$f.log" 2>&1 || { f2_ok=0; lep "F2 HIBA gen: $f"; break; }
    cpy kor07/eszkozok/szint07.py friss-final --csalad "$f" >> "$R/f2_$f.log" 2>&1 || { f2_ok=0; lep "F2 HIBA final: $f"; break; }
    lep "F2 kész: $f"
  done
else
  f2_ok=0; lep "F2 HIBA: a Muse nem állt fel"
fi
ldh_cleanup
if [ "$f2_ok" = 1 ]; then date '+%F %T' > DONE-K07F2; lep "F2 kész"; else echo "$(date '+%F %T') ld. lepesek.log" > FAILED-K07F2; fi
sleep 20

# --- D. F3 --------------------------------------------------------------------------------------------------------------
if [ "$f2_ok" = 1 ]; then
  feladat=()
  for f in "${CSALADOK[@]}"; do
    for s in CAL TESZT; do
      for m in kanonikus b1; do feladat+=(--feladat "$f:$s:$m"); done
    done
  done
  f3_ok=1
  py kor07/eszkozok/pecset07.py nyit >> "$R/f3.log" 2>&1 || f3_ok=0
  if [ "$f3_ok" = 1 ]; then
    say "F3: pecsét alatti kiolvasás, négyállapotú keret (3 család × CAL + TESZT, 18 000 forward)" 9000
    lep "F3 kiolvasás (4) indul"
    memoria_or07 "$R/f3.memoria4.log"
    py07 kor07/eszkozok/kiolvas07.py kivon "${feladat[@]}" --out-root cache/k07/pecset/jellemzok --status STATUS-K07F3-kiolvasas \
      >> "$R/f3.log" 2>&1 || { f3_ok=0; lep "F3 HIBA: kiolvasás (4)"; }
  fi
  if [ "$f3_ok" = 1 ]; then
    sleep 20
    say "F3: pecsét alatti kiolvasás, 06-os kétkimenetű keret (18 000 forward)" 9000
    lep "F3 kiolvasás (2) indul"
    memoria_or07 "$R/f3.memoria2.log"
    py07 kor07/eszkozok/kiolvas07.py kivon --keret 2 "${feladat[@]}" --out-root cache/k07/pecset/jellemzok2 --status STATUS-K07F3-kiolvasas \
      >> "$R/f3.log" 2>&1 || { f3_ok=0; lep "F3 HIBA: kiolvasás (2)"; }
  fi
  py kor07/eszkozok/pecset07.py lezar --fazis K07F3 >> "$R/f3.log" 2>&1 || { f3_ok=0; lep "F3 HIBA: pecsét lezárása"; }
  if [ "$f3_ok" = 1 ]; then date '+%F %T' > DONE-K07F3; lep "F3 kész"; else echo "$(date '+%F %T') ld. lepesek.log" > FAILED-K07F3; fi
else
  lep "F3 kihagyva (az F2 nem teljes)"
fi

osszes="F1M: $([ -f DONE-K07F1M ] && echo kész || echo HIBA) · F2: $([ -f DONE-K07F2 ] && echo kész || echo HIBA) · F3: $([ -f DONE-K07F3 ] && echo kész || echo "HIBA/kihagyva")"
say "éjszakai sor vége — $osszes"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
