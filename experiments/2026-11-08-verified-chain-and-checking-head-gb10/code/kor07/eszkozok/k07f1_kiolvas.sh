#!/usr/bin/env bash
# K07F1 — tervezési próba (07-runbook 3.1, 7. F1): a 06 három családjának T500 / CAL / TESZT szelete a négyállapotú
# prompttal (kor07/eszkozok/kiolvas07.py), kanonikus (jellemzőkkel) és b1 (3 permutáció) módban, a HF BF16 bázison.
# A 06 szeletei a 06 v1 rögzítése óta nyitottak, ezért nincs pecsét: a kimenet a cache/k07/jellemzok alá megy. A
# reprodukció (K07F0R, CPU) végét megvárja: modellbetöltés mellett nem fut CPU-feladat.
#   setsid nohup kor07/eszkozok/k07f1_kiolvas.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K07F1
LOG="logs/k07f1.log"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
ldh_cleanup() { :; }
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt

say "vár a reprodukció (K07F0R) végére"
until [ -f DONE-K07F0R ] || [ -f FAILED-K07F0R ]; do sleep 30; done
[ -f FAILED-K07F0R ] && say "a K07F0R hibával állt le ($(cat FAILED-K07F0R)); a kiolvasás ettől független, indul"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"

feladat=()
for f in penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas; do
  for s in T500 CAL TESZT; do
    for m in kanonikus b1; do feladat+=(--feladat "k06:$f:$s:$m"); done
  done
done
say "kiolvasás: 3 család × 3 szelet × (kanonikus + b1) = 24 000 forward" 10800
memoria_or07 "logs/k07f1.memoria.log"
py07 kor07/eszkozok/kiolvas07.py kivon "${feladat[@]}" --out-root cache/k07/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$LOG" 2>&1 || fail "kiolvasás"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
