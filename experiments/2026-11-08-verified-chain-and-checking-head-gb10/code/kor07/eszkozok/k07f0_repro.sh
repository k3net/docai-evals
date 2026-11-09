#!/usr/bin/env bash
# K07F0R — a 06 B1-R reprodukciója (07-runbook 2.1, F0): a `friss06 tanit` újrafuttatása a 06 T500-án, ugyanazokkal a
# seedekkel, a `cache/k07/f0_repro` alá, majd a pontszámok összevetése a 06 F5 f1.json-jaival. CPU; a `py` futtató root,
# mert a 06 CAL/TESZT jellemzői a (már nyitott) pecsét alatt vannak. A 06 kódja nem módosul.
#   setsid nohup kor07/eszkozok/k07f0_repro.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K07F0R
R="$EXP/logs/k07f0"
mkdir -p "$R"
ldh_cleanup() { :; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
[ -f kor06/rogzites/v1/ROGZITES.json ] || fail "a 06 v1 nincs rögzítve (a pecsét zárva)"
for f in penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas; do
  say "reprodukció: $f" 900
  py kor06/eszkozok/friss06.py tanit --csalad "$f" --out cache/k07/f0_repro >> "$R/tanit_$f.log" 2>&1 || fail "tanítás: $f"
done
say "összevetés" 60
py kor07/eszkozok/repro07.py --regi cache/k06/f5 --uj cache/k07/f0_repro --out kor07/eredmenyek/F0 >> "$R/repro.log" 2>&1 || fail "repro07"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
