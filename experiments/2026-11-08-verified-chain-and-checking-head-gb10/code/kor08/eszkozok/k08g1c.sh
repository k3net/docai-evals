#!/usr/bin/env bash
# K08G1C — G1 fejlesztési próbák (Dani 11-02): (1) a kinyerés javítása (séma v2) a hibás eseteken és az előre kijelölt
# kontrollmintán (`kin2_08`; vLLM, LORA=0), (2) a szabálycsalád blokk-változatai a K3 diag-on, orákulum-úton
# (`lanc08 --blokk v1|v2`, `g1_blokk08`; HF-kiolvasás). Egyszerre egy nagy GPU-folyamat. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1c.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1C"
R="$EXP/logs/k08g1c"
mkdir -p "$R"
F=szabaly.koltsegelszamolas
ALANY=ldh-alany08
P=kor08/adat/G1/kin2_proba
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf $*"; }  # a cache root tulajdonú

if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- 1. kinyerés, séma v2, a próbamintán -------------------------------------------------------------------------------
say "az alany indítása (vLLM, LORA=0)" 900
LORA=0 PREFIX=1 subject_start "$ALANY" >> "$R/alany.log" 2>&1
subject_wait "$ALANY" 1800 || fail "az alany nem állt fel"
say "kinyerés, séma v2: 722 item (hibás + kontroll)" 900
rm -rf "$P/kinyeres"
for src in 06 07 K3diag; do
  python3 kor08/eszkozok/kinyer08.py --forras "$src" --sema 2 --idk "$P/idk.txt" --out "$P/kinyeres" >> "$R/kinyeres.log" 2>&1 \
    || fail "kinyerés $src"
done
subject_stop "$ALANY" "$R"
sleep 20
python3 kor08/eszkozok/kin2_08.py osszevet --kinyeres "$P/kinyeres" >> "$R/kin2.log" 2>&1 || fail "összevetés"

# --- 2. blokk-változatok -----------------------------------------------------------------------------------------------
say "a lánc a blokk-változatokkal" 60
for v in v1 v2; do
  python3 kor08/eszkozok/lanc08.py futtat --forras K3diag --csalad "$F" --ut orakulum --blokk "$v" \
    --out "kor08/adat/G1/orakulum_K3diag_$v" >> "$R/lanc.log" 2>&1 || fail "lánc $v"
done
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás: K3 diag, szabálycsalád, v1 + v2 (2 × 199 item)" 2400
torol "/exp/cache/k08/jellemzok/oK3v1_*" "/exp/cache/k08/jellemzok/oK3v2_*"
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon --feladat "oK3v1:$F:DIAG:kanonikus" --feladat "oK3v1:$F:DIAG:b1" \
  --feladat "oK3v2:$F:DIAG:kanonikus" --feladat "oK3v2:$F:DIAG:b1" \
  --out-root cache/k08/jellemzok --status "STATUS-$FAZIS-kiolvasas" >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
py kor08/eszkozok/g1_blokk08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1 >> "$R/blokk.log" 2>&1 \
  || fail "blokk-mérés"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
