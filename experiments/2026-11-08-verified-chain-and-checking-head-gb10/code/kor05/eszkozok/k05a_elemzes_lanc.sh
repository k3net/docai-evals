#!/usr/bin/env bash
# K05A — a 05a elemzése a v1a rögzítése után (05-runbook 8.2–8.3; v1a-vazlat.md). Csak akkor indul, ha a ROGZITES.json
# megvan, és a befagyaszt05 ellenoriz átmegy (a manifest és a két pecsétmanifest egyezik).
#   1. a C, H, A és HX döntési sorai a kitartott szeleteken (a pecsét alatti jellemzőkön, GPU)
#   2. a K*-T-meta (H): a célcsalád-mintákon cross-fittelve, a hozzájuk tartozó teszteken az öt fold átlaga
#   3. az elemzés: szigorú helyességgel (az ítélet), majd enyhével (leíró); 10 000 replika
#   setsid nohup kor05/eszkozok/k05a_elemzes_lanc.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K05A
LOG=logs/k05a.log
P=cache/k05/pecset
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
log() { say "$@" >> "$LOG"; }
bukik() { log "HIBA: $*"; echo "[$(date '+%F %T')] $*" > "FAILED-$FAZIS"; rm -f AKTIV_FAZIS; exit 1; }
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
py kor05/eszkozok/befagyaszt05.py ellenoriz >> "$LOG" 2>&1 || bukik "a v1a ellenőrzése"
SZEL=(teszt:ho-termek teszt:ho-routing teszt:ho-uj teszt:ho-routing-hu leiro:t-hu-maradek cel:ho-termek cel:ho-routing cel:ho-uj)
for k in C H A HX; do
  for s in "${SZEL[@]}"; do
    o="$P/dontesek/$k/${s/:/_}"
    [ -f "$o/s73.jsonl" ] && continue
    log "1/3 döntési sorok: $k → $s"
    py --gpu kor05/eszkozok/megbizhatosag05.py dont --kar "$k" --fej "cache/k05/fejek/$k" --rel "cache/k05/megbizhatosag/$k" \
      --be "$P/jellemzok/${s/:/_}__kanonikus" --out "$o" >> "$LOG" 2>&1 || bukik "$k/$s"
  done
done
tmeta() {  # tmeta CÉL TESZT…
  local cel=$1; shift
  local o="$P/tmeta/H/${cel/:/_}" args=()
  [ -f "$o/tmeta.json" ] && return 0
  for t in "$@"; do args+=(--teszt "$P/jellemzok/${t/:/_}__kanonikus"); done
  log "2/3 T-meta: $cel → $*"
  py --gpu kor05/eszkozok/megbizhatosag05.py tmeta --kar H --fej cache/k05/fejek/H --rel cache/k05/megbizhatosag/H \
    --minta "$P/jellemzok/${cel/:/_}__kanonikus" "${args[@]}" --out "$o" >> "$LOG" 2>&1 || bukik "T-meta $cel"
}
tmeta cel:ho-termek teszt:ho-termek
tmeta cel:ho-routing teszt:ho-routing teszt:ho-routing-hu leiro:t-hu-maradek
tmeta cel:ho-uj teszt:ho-uj
KAR=(B0 B1 C H A HX B1-T H-T-kal H-T-meta JEV-a JEV-b L1v G3)
KONTR=(H-B1 "H-T-meta~B1-T" "H-T-kal~B1-T" H-C A-H H-HX "JEV-a~L1v" "JEV-a~G3" "JEV-a~B1" "JEV-b~L1v")
elemez() {  # elemez KIMENET "RÉTEGEK" "KAROK" "KONTRASZTOK" [--enyhe]
  local out=$1 args=() r k c
  for r in $2; do args+=(--reteg "$r"); done
  for k in $3; do args+=(--kar "$k"); done
  for c in $4; do args+=(--kontraszt "$c"); done
  py kor05/eszkozok/elemzes05.py "${args[@]}" --reps 10000 ${5:-} --out "kor05/eredmenyek/F3/$out" >> "$LOG" 2>&1
}
FO="teszt:ho-termek teszt:ho-routing teszt:ho-uj teszt:ho-routing-hu"
# a T-hu-maradék leíró réteg; a JEV-et nem olvastuk ki rajta, ezért JEV-karok nélkül fut
KAR_LEIRO="B0 B1 C H A HX B1-T H-T-kal H-T-meta L1v G3"
KONTR_LEIRO="H-B1 H-T-meta~B1-T H-T-kal~B1-T H-C A-H H-HX"
log "3/3 elemzés, szigorú helyesség (az ítélet), 10 000 replika" 3600
elemez v1a "$FO" "${KAR[*]}" "${KONTR[*]}" || bukik "elemzés"
elemez v1a_t-hu-maradek "leiro:t-hu-maradek" "$KAR_LEIRO" "$KONTR_LEIRO" || bukik "elemzés (T-hu-maradék)"
log "3/3 elemzés, enyhe helyesség (leíró)" 3600
elemez v1a_enyhe "$FO" "${KAR[*]}" "${KONTR[*]}" --enyhe || bukik "elemzés (enyhe)"
log "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
