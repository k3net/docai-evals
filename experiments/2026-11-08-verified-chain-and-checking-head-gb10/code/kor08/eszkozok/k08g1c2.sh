#!/usr/bin/env bash
# K08G1C2 — a kinyerés-javítás 2. próbája (séma v2 a javítások után: lapos egyértékű szerepek, az összeg nem százalék és
# nem árfolyam, a deviza az érték körüli ablakban; a hibacsalád a v1-en marad). Ugyanazok az előre kijelölt minták és
# feltételek (`kin2_08`), a bank- és a szabálycsaládon. Megvárja, hogy ne fusson más fázis és konténer.
#   setsid nohup kor08/eszkozok/k08g1c2.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1C2"
R="$EXP/logs/k08g1c2"
mkdir -p "$R"
ALANY=ldh-alany08
P=kor08/adat/G1/kin2_proba
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
say "az alany indítása (vLLM, LORA=0)" 900
LORA=0 PREFIX=1 subject_start "$ALANY" >> "$R/alany.log" 2>&1
subject_wait "$ALANY" 1800 || fail "az alany nem állt fel"
say "kinyerés, séma v2 (2. próba): bank és szabály" 600
rm -rf "$P/kinyeres2"
for src in 06 07 K3diag; do
  for f in penzugy.bankparositas szabaly.koltsegelszamolas; do
    python3 kor08/eszkozok/kinyer08.py --forras "$src" --csalad "$f" --sema 2 --idk "$P/idk.txt" --out "$P/kinyeres2" \
      >> "$R/kinyeres.log" 2>&1 || fail "kinyerés $src $f"
  done
done
subject_stop "$ALANY" "$R"
python3 kor08/eszkozok/kin2_08.py osszevet --kinyeres "$P/kinyeres2" --nev kin2_proba_2 >> "$R/kin2.log" 2>&1 || fail "összevetés"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
