#!/usr/bin/env bash
# K06F1 — az F1 fejlesztési futás (06-runbook 3.3, 9.): a három HO-réteg (CPU), majd az elemzés. Az előtanított B1-R
# (cache/k06/b1rel) a K06F1M kiolvasása után kézzel készült: b1rel06.py elotanit --out cache/k06/b1rel
#   setsid nohup kor06/eszkozok/k06f1_futas.sh >/dev/null 2>&1 < /dev/null &
# A v0.2 kódjával (B1-LR NONE-jelzővel, B1-N, SELECT-AURC) új kimenetre:
#   FAZIS=K06F1B F1_OUT=cache/k06/f1b RES_OUT=kor06/eredmenyek/F1b setsid nohup kor06/eszkozok/k06f1_futas.sh ...
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="${FAZIS:-K06F1}"
F1_OUT="${F1_OUT:-cache/k06/f1}"
RES_OUT="${RES_OUT:-kor06/eredmenyek/F1}"
LOG="logs/$(echo "$FAZIS" | tr "[:upper:]" "[:lower:]")"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
fail() { echo "$1 $(date '+%F %T')" > "FAILED-$FAZIS"; rm -f AKTIV_FAZIS; exit 1; }
for r in ho-termek ho-routing ho-uj; do
  echo "$r $(date '+%T')" > "STATUS-$FAZIS"
  py kor06/eszkozok/b1rel06.py f1 --reteg "$r" --out "$F1_OUT" > "${LOG}_$r.log" 2>&1 || fail "f1 $r"
done
echo "elemzés $(date '+%T')" > "STATUS-$FAZIS"
py kor06/eszkozok/elemzes06.py --be "$F1_OUT" --reps 2000 --out "$RES_OUT" > "${LOG}_elemzes.log" 2>&1 \
  || fail elemzes
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
