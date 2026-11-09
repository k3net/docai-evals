#!/usr/bin/env bash
# K08G1F — a G1 hátralévő számításai (Dani 11-03): (1) erőbecslés ágankénti bontásban (`ero08`: K1(b) a szabálycsaládon,
# K1(a) mindhárom családon; szimuláció, numpy a `py` konténerben, GPU nélkül); (2) a szabályalapú kinyerő (D1, leíró):
# kinyerés a megismert szeleteken (`szabkin08`), a lánc pontossága vele (`g1_lanc08`, blokk v4), és itemszintű összevetés
# az alany kinyerésével (`g1_kin_szab08`). Csak CPU, néhány perc: nem várja meg más konténer leállását, csak azt, hogy ne
# fusson fázis, ne töltsön be modellt konténer, és legyen ≥ 15 GB elérhető memória. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1f.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1F"
R="$EXP/logs/k08g1f"
mkdir -p "$R"
G=kor08/adat/G1
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
szabad() { [ "$(free -g | awk 'NR==2{print $7}')" -ge 15 ]; }
betolt() { docker ps --format '{{.Status}}' | grep -q "health: starting"; }

t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || betolt || ! szabad; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
{ date '+%F %T'; docker ps --format '{{.Names}} {{.Status}}'; free -g | sed -n 2p; } > "$R/indulas.log"

say "erőbecslés (szimuláció)" 600
py kor08/eszkozok/ero08.py --sims 2000 --boot-sims 300 --boot 1000 --out kor08/eredmenyek/G1 >> "$R/ero.log" 2>&1 \
  || fail "erőbecslés"
say "a szabályalapú kinyerő és a lánc" 300
python3 kor08/eszkozok/szabkin08.py --out "$G/kinyeres_szabaly" >> "$R/kinyeres.log" 2>&1 || fail "szabályalapú kinyerés"
python3 kor08/eszkozok/g1_lanc08.py --kinyeres "$G/kinyeres_szabaly" --blokk v4 --out kor08/eredmenyek/G1/szabalyalapu \
  >> "$R/lanc.log" 2>&1 || fail "a lánc pontossága a szabályalapú kinyeréssel"
python3 kor08/eszkozok/g1_kin_szab08.py --alany "$G/kinyeres_g1" --szabaly "$G/kinyeres_szabaly" --blokk v4 \
  --out kor08/eredmenyek/G1 >> "$R/osszevetes.log" 2>&1 || fail "a kinyerők összevetése"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
