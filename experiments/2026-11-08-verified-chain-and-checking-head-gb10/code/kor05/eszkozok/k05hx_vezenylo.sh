#!/usr/bin/env bash
# K05HX — a K*-X abláció (05-runbook 3. pont, H4; v1a D4): a H tartalmi feje egyetlen összevont X-állapottal
# (fej05 --kar HX), a megbízhatósági feje a D_meta-n és a döntési sorai a nem kitartott szeleteken. GPU, HF-modell
# nélkül; a kész lépés újraindításkor kimarad.
#   setsid nohup kor05/eszkozok/k05hx_vezenylo.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K05HX
LOG=logs/k05hx.log
JELL=cache/k05/jellemzok
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
log() { say "$@" >> "$LOG"; }
bukik() { log "HIBA: $*"; echo "[$(date '+%F %T')] $*" > "FAILED-$FAZIS"; exit 1; }
if [ ! -f cache/k05/fejek/HX/fej.json ]; then
  log "HX tartalmi fej (D_fit → D_dev, 2 LR × 3 seed)" 900
  py --gpu kor05/eszkozok/fej05.py tanit --kar HX --fit "$JELL/D_fit__fit" --dev "$JELL/D_dev__kanonikus" \
    --out cache/k05/fejek/HX >> "$LOG" 2>&1 || bukik "a HX tartalmi fej"
fi
if [ ! -f cache/k05/megbizhatosag/HX/rel.json ]; then
  log "HX megbízhatósági fej a D_meta-n" 600
  py --gpu kor05/eszkozok/megbizhatosag05.py tanit --kar HX --fej cache/k05/fejek/HX --meta "$JELL/D_meta__kanonikus" \
    --out cache/k05/megbizhatosag/HX >> "$LOG" 2>&1 || bukik "a HX megbízhatósági fej"
fi
for s in D_dev D_meta D_cal_prob D_cal_policy; do
  [ -f "cache/k05/dontesek/HX/$s/s73.jsonl" ] && continue
  log "HX döntési sorok → $s"
  py --gpu kor05/eszkozok/megbizhatosag05.py dont --kar HX --fej cache/k05/fejek/HX --rel cache/k05/megbizhatosag/HX \
    --be "$JELL/${s}__kanonikus" --out "cache/k05/dontesek/HX/$s" >> "$LOG" 2>&1 || bukik "HX/$s"
done
mkdir -p kor05/eredmenyek/F3/fejek/HX kor05/eredmenyek/F3/megbizhatosag/HX
cp cache/k05/fejek/HX/fej.json kor05/eredmenyek/F3/fejek/HX/
cp cache/k05/megbizhatosag/HX/rel.json kor05/eredmenyek/F3/megbizhatosag/HX/
log "kész"
date '+%F %T' > "DONE-$FAZIS"
