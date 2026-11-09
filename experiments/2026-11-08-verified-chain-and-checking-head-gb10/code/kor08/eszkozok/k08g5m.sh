#!/usr/bin/env bash
# K08G5M (11-05; nem rögzített; Dani: „mehet mindkettő”) — leíró módérzékenységi próba a G5 után. Az éjszakai két zárt
# kiolvasás (A és B numerikai mód, `arch_zart1_A`, `arch_zart2_B`) ugyanazokkal a fejekkel, ugyanazzal a pontozással és
# ugyanazokkal a rögzített elemzőkkel, mint a G5 az R-módú kiolvasáson (a parancsok a `k08g3c.sh` 5. és a `k08g5.sh`
# lépései). A tanítás marad az R-módon, a τ és a temperature a mód saját CAL-ján áll be. A pontozás nem a pecsét alá megy
# (a manifest így nem változik; előtte és utána ellenőrizve), az eredmény `kor08/eredmenyek/G5_modszenz/`. A fő eredmény
# az R-módú G5 marad; ez csak azt mutatja, mennyit mozdul a mód miatt. Csak CPU.
#   setsid nohup kor08/eszkozok/k08g5m.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
export PATH="$EXP/kor08/eszkozok/burok_g3:$PATH"
FAZIS="K08G5M"
R="$EXP/logs/k08g5m"
mkdir -p "$R"
G3=kor08/adat/G3
F8=cache/k08/fejek08
OO=kor08/eredmenyek/G5_modszenz
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
REPS=10000
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
[ -f DONE-K08G5 ] || { echo "$FAZIS: nincs DONE-K08G5" > "FAILED-$FAZIS"; exit 1; }
[ -f AKTIV_FAZIS ] && { echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS))" > "FAILED-$FAZIS"; exit 1; }
python3 kor08/eszkozok/pecset08.py ellenoriz --fazis K08G3 > "$R/pecset_elotte.log" 2>&1 \
  || { echo "$FAZIS: a pecsét manifestje nem egyezik" > "FAILED-$FAZIS"; exit 1; }
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

for m in A:arch_zart1_A B:arch_zart2_B; do
  M="${m%%:*}"
  PJ="cache/k08/pecset/${m#*:}"
  PP="cache/k08/modszenz/$M/pontoz"
  O="$OO/$M"
  mkdir -p "$O"
  say "$M: pontozás" 600
  for f in "${CSALADOK_08[@]}"; do
    for x in "lG2F_${f}_CAL:kinyert_G2F" "lG2F_${f}_TESZT:kinyert_G2F" "lG2K3_${f}_G2K3:kinyert_G2K3" \
             "oG2K3_${f}_G2K3:orakulum_G2K3" "lG2T_${f}_G2T:kinyert_G2T"; do
      py kor08/eszkozok/b1rel08.py pontoz --szelet "${x%%:*}" --jell "$PJ" --lanc "$G3/${x#*:}" --fejek08 "$F8" --out "$PP" \
        --szalak 16 >> "$R/pontoz_$M.log" 2>&1 || fail "pontozás $M ${x%%:*}"
    done
    for s in "nG2F_${f}_CAL" "nG2F_${f}_TESZT" "nG2K3_${f}_G2K3"; do
      py kor08/eszkozok/b1rel08.py pontoz --szelet "$s" --jell "$PJ" --lanc-nelkul --out "$PP" --szalak 16 \
        >> "$R/pontoz_$M.log" 2>&1 || fail "pontozás $M $s"
    done
  done
  say "$M: K3" 600
  py kor08/eszkozok/g5_k3_08.py --forras G2F --cal CAL --teszt TESZT --lanc "$G3/kinyert_G2F" \
    --pont "$PP/lG2F_{csalad}_{szelet}.json" --k07 "$PP/nG2F_{csalad}_{szelet}.json" \
    --szabaly "$G3/szabaly_G2F" --orakulum "$G3/orakulum_G2F" --kar-x L-RN --reps "$REPS" \
    --cimke "G5 utólag, leíró: $M mód" --out "$O/k3" >> "$R/g5_$M.log" 2>&1 || fail "g5_k3_08 $M"
  say "$M: K1" 600
  args=()
  for f in "${CSALADOK_08[@]}"; do
    args+=(--csalad "$f:$PP/lG2T_${f}_G2T.json:kor08/adat/G2/ert_teszt/items:$G3/kinyert_G2T:$G3/orakulum_G2T"
           --cal "$f:$PP/lG2F_${f}_CAL.json")
  done
  py kor08/eszkozok/g5_k1_08.py "${args[@]}" --fo-par L-RN,L-S --tau "$O/k3/g5_k3.json" --reps "$REPS" \
    --cimke "G5 utólag, leíró: $M mód" --out "$O/k1" >> "$R/g5_$M.log" 2>&1 || fail "g5_k1_08 $M"
  say "$M: K2" 300
  py kor08/eszkozok/g5_k2_08.py --forras G2K3 --nelkul "$PP/nG2K3_{csalad}_G2K3.json" \
    --kinyert "$G3/kinyert_G2K3:$PP/lG2K3_{csalad}_G2K3.json" --orakulum "$G3/orakulum_G2K3:$PP/oG2K3_{csalad}_G2K3.json" \
    --reps "$REPS" --cimke "G5 utólag, leíró: $M mód" --out "$O/k2" >> "$R/g5_$M.log" 2>&1 || fail "g5_k2_08 $M"
done

say "összevetés" 120
py kor08/eszkozok/modszenz08.py --out "$OO/osszevetes.md" >> "$R/osszevetes.log" 2>&1 || fail "összevetés"
python3 kor08/eszkozok/pecset08.py ellenoriz --fazis K08G3 > "$R/pecset_utana.log" 2>&1 || fail "a pecsét manifestje a próba után nem egyezik"
sha256sum "$OO"/*/*/*.json "$OO/osszevetes.md" > "$R/g5m.sha256"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
