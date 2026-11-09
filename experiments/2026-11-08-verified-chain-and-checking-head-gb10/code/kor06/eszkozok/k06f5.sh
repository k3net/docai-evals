#!/usr/bin/env bash
# K06F5 — a pecsét nyitása utáni elemzés (06-runbook 9. F5; `kor06/rogzites/v1/v1-vazlat.md` 6.). Csak a v1 rögzítése
# (ROGZITES.json) és Dani „mehet”-je után: a manifest ellenőrzése, a tanítás családonként (a CAL és a TESZT a pecsét
# alól), az értékelés (8.1–8.3), a bontás (D20) és a munkapont (8.4). CPU; a `py` futtató root, mert a pecsét 700.
#   setsid nohup kor06/eszkozok/k06f5.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F5
R="$EXP/logs/k06f5"
mkdir -p "$R"
ldh_cleanup() { :; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
[ -f kor06/rogzites/v1/ROGZITES.json ] || fail "a v1 nincs rögzítve"
py kor06/eszkozok/befagyaszt06.py ellenoriz >> "$R/ellenoriz.log" 2>&1 || fail "a v1 manifestje vagy a pecsét nem egyezik"
for f in penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas; do
  say "tanítás: $f" 900
  py kor06/eszkozok/friss06.py tanit --csalad "$f" --out cache/k06/f5 >> "$R/tanit_$f.log" 2>&1 || fail "tanítás: $f"
done
say "értékelés (8.1–8.3)" 1200
py kor06/eszkozok/friss06.py elemez --be cache/k06/f5 --out kor06/eredmenyek/F5 >> "$R/elemez.log" 2>&1 || fail "elemez"
say "bontás (D20)" 600
py kor06/eszkozok/friss06.py bontas --be cache/k06/f5 --out kor06/eredmenyek/F5 >> "$R/bontas.log" 2>&1 || fail "bontas"
say "munkapont (8.4)" 900
py kor06/eszkozok/friss06.py munkapont --be cache/k06/f5 --out kor06/eredmenyek/F5 >> "$R/munkapont.log" 2>&1 || fail "munkapont"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
