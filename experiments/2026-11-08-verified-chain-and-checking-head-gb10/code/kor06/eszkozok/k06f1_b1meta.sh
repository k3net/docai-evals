#!/usr/bin/env bash
# K06F1M — a D_meta 1–3. sorrendjének B1-kiolvasása (06-runbook 4., D2 a): a B1-R előtanításához kell a B1 helyessége
# a D_meta-n. A 05 hf_jellemzo05 változatlanul, a kimenet a 05 nem kitartott jellemzői mellé kerül.
#   setsid nohup kor06/eszkozok/k06f1_b1meta.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F1M
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
py --gpu kor05/eszkozok/hf_jellemzo05.py kivon --feladat D_meta:b1 \
  --out-root cache/k05/jellemzok --status "STATUS-$FAZIS" > "logs/k06f1m.log" 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then date '+%F %T' > "DONE-$FAZIS"; else echo "rc=$rc $(date '+%F %T')" > "FAILED-$FAZIS"; fi
rm -f AKTIV_FAZIS
