#!/usr/bin/env bash
# K08G1DET — determinizmus-próba (Dani 11-03): a szabálycsalád v1 T500-kiolvasása (`o06`, K08G1A3) és a javított 2. kör
# (`oERT2J`, K08G1B2K) újraolvasva külön cache-be (`cache/k08/jellemzok_det`), bájtra azonos itemfájlokon; itemszintű
# összevetés a régivel (`g1_det08`), és a 2. kör mérése az új kiolvasáson (`G1b/det`). HF-kiolvasás, vLLM nem kell.
#   setsid nohup kor08/eszkozok/k08g1det.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1DET"
R="$EXP/logs/k08g1det"
mkdir -p "$R"
S=szabaly.koltsegelszamolas
J=cache/k08/jellemzok
JD=cache/k08/jellemzok_det
ITEMEK=(kor08/adat/G1/orakulum_06/items/$S.jsonl kor08/adat/G1/orakulum_ERT2J/items/$S.jsonl)
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf $*"; }  # a cache root tulajdonú

t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- a bemenet: az itemfájlok a régi kiolvasás óta változatlanok --------------------------------------------------------
sha256sum "${ITEMEK[@]}" > "$R/itemek_elotte.sha256"
[ "${ITEMEK[0]}" -ot "$J/o06_${S}_T500__kanonikus" ] || fail "az itemfájl újabb a régi kiolvasásnál: ${ITEMEK[0]}"
[ "${ITEMEK[1]}" -ot "$J/oERT2J_${S}_ERT2J__kanonikus" ] || fail "az itemfájl újabb a régi kiolvasásnál: ${ITEMEK[1]}"

# --- kiolvasás külön cache-be ------------------------------------------------------------------------------------------
torol "/exp/$JD/o06_${S}_*" "/exp/$JD/oERT2J_${S}_*"
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "determinizmus-próba: a T500 v1 és az ERT2J újraolvasása" 1500
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon --feladat "o06:$S:T500:kanonikus" --feladat "o06:$S:T500:b1" \
  --feladat "oERT2J:$S:ERT2J:kanonikus" --feladat "oERT2J:$S:ERT2J:b1" --out-root "$JD" \
  --status "STATUS-$FAZIS-kiolvasas" >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
sha256sum -c --quiet "$R/itemek_elotte.sha256" >> "$R/osszevetes.log" 2>&1 || fail "az itemfájlok a futás alatt változtak"

# --- összevetés ----------------------------------------------------------------------------------------------------------
say "összevetés" 120
py kor08/eszkozok/g1_det08.py --regi "$J" --uj "$JD" --out kor08/eredmenyek/G1 >> "$R/osszevetes.log" 2>&1 \
  || fail "összevetés"
py kor08/eszkozok/g1b_ert08.py --jell "$JD" --out kor08/eredmenyek/G1b/det --kor 2 --javitott --csalad "$S" \
  >> "$R/osszevetes.log" 2>&1 || fail "a 2. kör mérése az új kiolvasáson"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
