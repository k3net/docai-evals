#!/usr/bin/env bash
# K07F5 — a pecsét nyitása utáni pontozás (07-runbook 7. F5; a v1-vázlat 6. pontja). Előfeltétel: a ROGZITES.json
# (`befagyaszt07 rogzit`, Dani „mehet”-je után); a `pecset07.kapu` ettől nyit. CPU, egy modellbetöltés sincs.
#   1. befagyaszt07 ellenoriz (a manifest és a pecsétmanifest változatlan)
#   2. b1rel07 pontoz a friss CAL és TESZT mindkét keretén, családonként → cache/k07/f5/<szelet>.json
# Az elemzés (elemzes07, 10 000 replika) helyben fut a back után.
#   setsid nohup bash kor07/eszkozok/k07f5.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K07F5
R="$EXP/logs/k07f5"
mkdir -p "$R"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
say "F5: a rögzítés ellenőrzése"
py kor07/eszkozok/befagyaszt07.py ellenoriz >> "$R/f5.log" 2>&1 || fail "a v1 rögzítése vagy a manifest nem egyezik"
for f in penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas; do
  for s in CAL TESZT; do
    say "F5: pontozás $f:$s (mindkét keret)" 300
    py kor07/eszkozok/b1rel07.py pontoz --szelet "$f:$s" --out cache/k07/f5 --szalak 8 >> "$R/f5.log" 2>&1 || fail "pontozás: $f:$s"
  done
done
say "F5: pontozás kész — $(ls cache/k07/f5/*.json | wc -l) fájl"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
