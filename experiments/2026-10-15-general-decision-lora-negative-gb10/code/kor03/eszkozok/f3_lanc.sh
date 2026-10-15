#!/usr/bin/env bash
# K03F3 lánc (2026-10-11 este): megvárja a pilot végét, utána a javított vezénylőt a helyére teszi (a futó szkriptet
# nem írjuk felül, ezért addig f3_vezenylo.sh.uj néven vár), és indítja a tanulási görbét.
#   nohup setsid bash kor03/eszkozok/f3_lanc.sh > logs/k03f3_lanc.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
cd "$EXP"
echo "[$(date '+%F %T')] vár a pilotra"
while [ ! -f DONE-K03F3-pilot ]; do
  [ -f FAILED-K03F3-pilot ] && { echo "[$(date '+%F %T')] a pilot hibával állt le, a görbe nem indul"; exit 1; }
  [ -f STOP-K03F3 ] && { echo "[$(date '+%F %T')] STOP-K03F3: kilépek"; exit 0; }
  sleep 120
done
sleep 30  # a pilot vezénylője a DONE után még takarít
pgrep -f "f3_vezenylo.sh pilot" >/dev/null && { echo "[$(date '+%F %T')] a pilot vezénylője még fut, kilépek"; exit 1; }
mv kor03/eszkozok/f3_vezenylo.sh.uj kor03/eszkozok/f3_vezenylo.sh
echo "[$(date '+%F %T')] vezénylő frissítve, a görbe indul"
exec bash kor03/eszkozok/f3_vezenylo.sh gorbe
