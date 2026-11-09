#!/usr/bin/env bash
# K05F2A — a nem kitartott 05a-szeletek HF-jellemzői (05-runbook 10. pont F2). A HO-rétegek és a célcsalád-minták
# kivonása (K05F2B) csak a v1a rögzítése után indul. Egy modellbetöltés, feladatonként 1000-es shardok; újraindítva
# a kész shardok kimaradnak (reboot után elég újra futtatni).
#   setsid nohup kor05/eszkozok/k05f2a_vezenylo.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K05F2A
rm -f "FAILED-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
py --gpu kor05/eszkozok/hf_jellemzo05.py kivon \
  --feladat D_dev:kanonikus --feladat D_fit:fit --feladat D_meta:kanonikus \
  --feladat D_cal_prob:kanonikus --feladat D_cal_policy:kanonikus \
  --feladat D_cal_prob:b1 --feladat D_cal_policy:b1 \
  --out-root cache/k05/jellemzok --status "STATUS-$FAZIS" > "logs/k05f2a.log" 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then date '+%F %T' > "DONE-$FAZIS"; else echo "rc=$rc $(date '+%F %T')" > "FAILED-$FAZIS"; fi
rm -f AKTIV_FAZIS
