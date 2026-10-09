#!/usr/bin/env bash
# Fázislánc: megvárja, hogy az ELŐZŐ fázis DONE legyen, és indítja a KÖVETKEZŐT.
# FAILED esetén nem indít semmit.   lanc.sh F0A F0B · szakaszos vezénylőnél: lanc.sh F3-pilot F3-hangolas
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
prev="$1"; next="$2"
while true; do
  [ -f "FAILED-$prev" ] && { echo "[$(date '+%F %T')] $prev FAILED — $next nem indul" >> logs/lanc.log; exit 1; }
  [ -f "DONE-$prev" ] && break
  sleep 60
done
echo "[$(date '+%F %T')] $prev kész → $next indul" >> logs/lanc.log
lc=$(echo "$next" | tr 'A-Z' 'a-z')
args=()
case "$lc" in *-*) args=("${lc#*-}"); v="eszkozok/${lc%%-*}_vezenylo.sh" ;;  # F3-hangolas → f3_vezenylo.sh hangolas
  *) v="eszkozok/${lc}_vezenylo.sh" ;; esac
[ -x "$v" ] || v="kor01/$v"   # a 01-es kör vezénylői a kor01/eszkozok alatt (mint a folytat.sh-ban)
exec "./$v" "${args[@]}" >> "logs/${lc/-/_}.log" 2>&1
