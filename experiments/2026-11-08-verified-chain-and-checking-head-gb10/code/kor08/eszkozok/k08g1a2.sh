#!/usr/bin/env bash
# K08G1A2 — a G1a utómunkája az alap-javítás után (`lanc08`: ha a kinyerő nem adja meg, a bruttó / nettó alap az
# ellenőrzés szabályával, az érték körüli ablakból; 08-runbook napló 11-02). A kinyerés nem fut újra: (1) a
# szabálycsalád lánca mindhárom forráson, mindkét úton, (2) a lánc pontossága, (3) a változott lánc utáni itemek
# (K3 diag, valós kinyerés) kiolvasása, (4) a döntések. A többi kiolvasás változatlan (az itemfájlok bájtra azonosak).
#   setsid nohup kor08/eszkozok/k08g1a2.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1A2"
R="$EXP/logs/k08g1a2"
mkdir -p "$R"
F=szabaly.koltsegelszamolas
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint rm "$TOOL_IMAGE" -rf "$@"; }  # a cache root tulajdonú

if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

say "a szabálycsalád lánca, három forrás, két út" 120
for src in 06 07 K3diag; do
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$F" --ut kinyert \
    --kinyeres "kor08/adat/G1/kinyeres/${src}_$F.mezok.jsonl" --out "kor08/adat/G1/kinyert_$src" >> "$R/lanc.log" 2>&1 \
    || fail "lánc kinyert $src"
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$F" --ut orakulum \
    --out "kor08/adat/G1/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src"
done
python3 kor08/eszkozok/g1_lanc08.py --kinyeres kor08/adat/G1/kinyeres --out kor08/eredmenyek/G1 >> "$R/lanc.log" 2>&1 \
  || fail "a lánc pontossága"

source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás: K3 diag, szabálycsalád, valós kinyerés (199 item)" 1500
torol "/exp/cache/k08/jellemzok/lK3_${F}_DIAG__kanonikus" "/exp/cache/k08/jellemzok/lK3_${F}_DIAG__b1"
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon --feladat "lK3:$F:DIAG:kanonikus" --feladat "lK3:$F:DIAG:b1" \
  --out-root cache/k08/jellemzok --status "STATUS-$FAZIS-kiolvasas" >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
say "a döntések" 300
py kor08/eszkozok/g1_dontes08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1 >> "$R/dontes.log" 2>&1 \
  || fail "döntések"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
