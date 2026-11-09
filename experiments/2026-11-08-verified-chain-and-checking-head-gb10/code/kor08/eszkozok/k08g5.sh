#!/usr/bin/env bash
# K08G5 — a G5: a rögzített elemzők a G3 pecsét alatti kimenetén (G1-rögzítés 7., 8.), 10 000 replikával. **Csak a G4
# hash-lezárása után és Dani nyitási engedélyével fut** (`kor08/rogzites/G5/NYITAS.json`; a `pecset08 ellenoriz` a
# lezárt manifest ellen). Sorrend: K3 (a τ a CAL-on; a K1 τ fölötti (a)-arányához is), K1 (a két fő próba Holm-mal,
# a szabálycsaládon; a bank és a hiba leíró), K2 (a K3-típus). Csak CPU. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g5.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G5"
R="$EXP/logs/k08g5"
mkdir -p "$R"
G3=kor08/adat/G3
PP=cache/k08/pecset/pontoz
O=kor08/eredmenyek/G5
REPS=10000
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
[ -f kor08/rogzites/G5/NYITAS.json ] || { echo "$FAZIS: nincs nyitási engedély (kor08/rogzites/G5/NYITAS.json)" > "FAILED-$FAZIS"; exit 1; }
python3 kor08/eszkozok/pecset08.py ellenoriz --fazis K08G3 > "$R/pecset.log" 2>&1 || { echo "$FAZIS: a pecsét manifestje nem egyezik" > "FAILED-$FAZIS"; exit 1; }
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q "health: starting"; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
mkdir -p "$O"

say "K3 (a τ a CAL-on, replikánként újra)" 7200
py kor08/eszkozok/g5_k3_08.py --forras G2F --cal CAL --teszt TESZT --lanc "$G3/kinyert_G2F" \
  --pont "$PP/lG2F_{csalad}_{szelet}.json" --k07 "$PP/nG2F_{csalad}_{szelet}.json" \
  --szabaly "$G3/szabaly_G2F" --orakulum "$G3/orakulum_G2F" --kar-x L-RN --reps "$REPS" \
  --cimke "G5, a friss TESZT" --out "$O/k3" >> "$R/g5.log" 2>&1 || fail "g5_k3_08"
py kor08/eszkozok/g5_k3_08.py --forras G2F --cal CAL --teszt TESZT --lanc "$G3/kinyert_G2F" \
  --pont "$PP/lG2F_{csalad}_{szelet}.json" --k07 "$PP/nG2F_{csalad}_{szelet}.json" --tau-halmaz rendszer --reps "$REPS" \
  --cimke "G5, a friss TESZT; leíró: a τ a teljes lezárt halmazon" --out "$O/k3_rendszer" >> "$R/g5.log" 2>&1 || fail "g5_k3_08 (rendszer)"
say "K1 (a két fő próba Holm-mal)" 3600
args=()
for f in szabaly.koltsegelszamolas penzugy.bankparositas muszaki.hibaelharitas; do
  args+=(--csalad "$f:$PP/lG2T_${f}_G2T.json:kor08/adat/G2/ert_teszt/items:$G3/kinyert_G2T:$G3/orakulum_G2T"
         --cal "$f:$PP/lG2F_${f}_CAL.json")
done
py kor08/eszkozok/g5_k1_08.py "${args[@]}" --fo-par L-RN,L-S --tau "$O/k3/g5_k3.json" --reps "$REPS" \
  --cimke "G5, az értelmezési teszt" --out "$O/k1" >> "$R/g5.log" 2>&1 || fail "g5_k1_08"
say "K2 (a K3-típus három úton)" 1800
py kor08/eszkozok/g5_k2_08.py --forras G2K3 --nelkul "$PP/nG2K3_{csalad}_G2K3.json" \
  --kinyert "$G3/kinyert_G2K3:$PP/lG2K3_{csalad}_G2K3.json" --orakulum "$G3/orakulum_G2K3:$PP/oG2K3_{csalad}_G2K3.json" \
  --reps "$REPS" --cimke "G5, a K3-típus" --out "$O/k2" >> "$R/g5.log" 2>&1 || fail "g5_k2_08"
sha256sum "$O"/*/*.json > "$R/g5.sha256"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
