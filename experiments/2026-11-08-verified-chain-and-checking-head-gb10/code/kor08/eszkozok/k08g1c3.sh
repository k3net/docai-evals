#!/usr/bin/env bash
# K08G1C3 — a kinyerés-javítás 3. próbája (11-02): a 2. próba után két ellenőrzési javítás (a szám a teljes szövegből, a
# részleten belül; a nem igazolható, de nem ellentmondó attribútum elvetődik). A siker feltétele a 2. próbáé, a friss
# `kontroll2` mintán (a `kontroll`-t két próba már látta); mellette a zajszint: a v1 séma újrafuttatása ugyanazon a
# vLLM-példányon a két kontrollmintán. A bank- és a szabálycsaládon. Megvárja, hogy ne fusson más fázis és konténer.
#   setsid nohup kor08/eszkozok/k08g1c3.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1C3"
R="$EXP/logs/k08g1c3"
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
say "kinyerés: v2 a hibás + két kontrollmintán, v1 a két kontrollmintán (zajszint)" 900
rm -rf "$P/kinyeres3" "$P/kinyeres3_v1"
for src in 06 07 K3diag; do
  for f in penzugy.bankparositas szabaly.koltsegelszamolas; do
    python3 kor08/eszkozok/kinyer08.py --forras "$src" --csalad "$f" --sema 2 --idk "$P/idk3.txt" --out "$P/kinyeres3" \
      >> "$R/kinyeres.log" 2>&1 || fail "kinyerés v2 $src $f"
    python3 kor08/eszkozok/kinyer08.py --forras "$src" --csalad "$f" --sema 1 --idk "$P/idk3_v1.txt" --out "$P/kinyeres3_v1" \
      >> "$R/kinyeres.log" 2>&1 || fail "kinyerés v1 $src $f"
  done
done
subject_stop "$ALANY" "$R"
python3 kor08/eszkozok/kin2_08.py osszevet --kinyeres "$P/kinyeres3" --v1-ujra "$P/kinyeres3_v1" --kontroll kontroll2 \
  --nev kin2_proba_3 >> "$R/kin2.log" 2>&1 || fail "összevetés"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
