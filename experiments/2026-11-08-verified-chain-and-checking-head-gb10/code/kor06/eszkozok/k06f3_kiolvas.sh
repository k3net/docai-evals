#!/usr/bin/env bash
# K06F3 — a friss családok B1-kiolvasása (06-runbook 4., 9. F3) a HF BF16 bázison, a 05 hf_jellemzo05 útján
# (kor06/eszkozok/kiolvas06.py). A hibaelhárítás teljes építése (K06F2HB) után indul; ha az hibával állt le, csak a bank-
# és a szabálycsalád fut. Sorrend: span-ellenőrzés (CPU), a T500 nyitva (cache/k06/jellemzok), majd a CAL és a TESZT a
# pecsét alá (cache/k06/pecset/jellemzok) és a pecsét manifestje (kor06/rogzites/pecset/K06F3.json).
#   setsid nohup kor06/eszkozok/k06f3_kiolvas.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="${FAZIS:-K06F3}"
LOG="logs/k06f3.log"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
ldh_cleanup() { :; }
cpu() {  # CPU-lépés a saját uid-del (a kimenet ne legyen root-é)
  docker run --rm --user "$(id -u):$(id -g)" --network host -v "$EXP:/exp" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp \
    -e PYTHONUNBUFFERED=1 -e HOME=/tmp -w /exp "$TOOL_IMAGE" python3 "$@"
}

say "vár a hibaelhárítás teljes építésére (K06F2HB)"
until [ -f DONE-K06F2HB ] || [ -f FAILED-K06F2HB ]; do sleep 60; done
CSALADOK=(penzugy.bankparositas szabaly.koltsegelszamolas)
if [ -f DONE-K06F2HB ]; then CSALADOK+=(muszaki.hibaelharitas)
else say "a K06F2HB hibával állt le ($(cat FAILED-K06F2HB)); csak a bank- és a szabálycsalád"; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"

nyitott=() pecset=() szel=()
for f in "${CSALADOK[@]}"; do
  for s in T500 CAL TESZT; do szel+=("$f:$s"); done
  for m in kanonikus b1; do
    nyitott+=(--feladat "$f:T500:$m")
    for s in CAL TESZT; do pecset+=(--feladat "$f:$s:$m"); done
  done
done
S="${szel[*]}"
say "span-ellenőrzés (${#CSALADOK[@]} család)"
cpu kor06/eszkozok/kiolvas06.py spanok --szelet "${S// /,}" --perms-is --out kor06/eredmenyek/F3/spanok >> "$LOG" 2>&1 \
  || fail "span-ellenőrzés"

say "T500 (nyitott)" 2700
py --gpu kor06/eszkozok/kiolvas06.py kivon "${nyitott[@]}" --out-root cache/k06/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$LOG" 2>&1 || fail "T500-kiolvasás"
py kor06/eszkozok/pecset06.py nyit >> "$LOG" 2>&1 || fail "pecsét nyitása"
say "CAL és TESZT (pecsét alatt)" 7800
py --gpu kor06/eszkozok/kiolvas06.py kivon "${pecset[@]}" --out-root cache/k06/pecset/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$LOG" 2>&1 || fail "pecsét alatti kiolvasás"
py kor06/eszkozok/pecset06.py lezar --fazis "$FAZIS" >> "$LOG" 2>&1 || fail "pecsét lezárása"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
