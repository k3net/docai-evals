#!/usr/bin/env bash
# Újraindulás utáni folytatás: a crontab @reboot sora hívja (reboot_hook.sh install).
# Ha van AKTIV_FAZIS, az ahhoz tartozó vezénylő újraindul — a lépések idempotensek,
# a tréning checkpointból folytat.
cd "$(dirname "$0")/.." || exit 1
sleep 120   # docker + GPU-meghajtó felállása
f=$(cat AKTIV_FAZIS 2>/dev/null) || exit 0
[ -z "$f" ] && exit 0
lc=$(echo "$f" | tr 'A-Z' 'a-z')
args=()
case "$lc" in *-*) args=("${lc#*-}"); v="eszkozok/${lc%%-*}_vezenylo.sh" ;;  # F3-pilot → f3_vezenylo.sh pilot
  *) v="eszkozok/${lc}_vezenylo.sh" ;; esac
[ -x "$v" ] || v="kor01/$v"   # a 01-es kör vezénylői a kor01/eszkozok alatt
[ -x "$v" ] || { echo "[$(date '+%F %T')] ismeretlen fázis: $f" >> logs/reboot.log; exit 1; }
echo "[$(date '+%F %T')] újraindulás után folytatom: $f" >> logs/reboot.log
setsid nohup "$v" "${args[@]}" >> "logs/${lc/-/_}.log" 2>&1 < /dev/null &
