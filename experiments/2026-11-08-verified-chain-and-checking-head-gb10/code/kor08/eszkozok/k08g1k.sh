#!/usr/bin/env bash
# K08G1K — a 08-as fejtanító próbája a G1 pilotján (G1-rögzítés 11.), a K08G1J után. **Csak a kód próbája, a számok
# nem értelmezhetők:** az értelmezési tanítóminta helyén a G1b 1. köre áll (`oERT`), amely ugyanazokra a 07 CAL-sablonokra
# épül, mint a K1 pilot tesztje (a G1b 2. köre). Lépések (csak CPU): `b1rel08 tanit` (L-R, L-RN, L-LR, L-LRN; a láncos
# T500 orákulum-úton), pontozás a 08-as karokkal a K1 pilot szeletein és a 06 CAL / TESZT-en, `g5_k1_08` a fő párral
# (L-RN − L-S), `g5_k3_08` (K3-X az L-RN-nel). Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1k.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1K"
R="$EXP/logs/k08g1k"
mkdir -p "$R"
G=kor08/adat/G1
F8=cache/k08/fejek_g1pilot
P=cache/k08/pontoz/G1_08fejek
O=kor08/eredmenyek/G1/g5_pilot
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
szabad() { [ "$(free -g | awk 'NR==2{print $7}')" -ge 15 ]; }

t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q . || ! szabad; do
  [ $(( $(date +%s) - t0 )) -gt 28800 ] && { echo "$FAZIS: 8 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

say "a 08-as fejek tanítása (pilot)" 1800
py kor08/eszkozok/b1rel08.py tanit --ert "oERT_{csalad}_ERT" --ert-lanc "$G/orakulum_ERT" --out "$F8" --szalak 16 \
  >> "$R/tanit.log" 2>&1 || fail "tanítás"
say "pontozás a 08-as karokkal" 900
for x in "oERT2J_szabaly.koltsegelszamolas_ERT2J:$G/orakulum_ERT2J" "oERT2_penzugy.bankparositas_ERT2:$G/orakulum_ERT2" \
         "oERT2_muszaki.hibaelharitas_ERT2:$G/orakulum_ERT2"; do
  py kor08/eszkozok/b1rel08.py pontoz --szelet "${x%%:*}" --lanc "${x#*:}" --fejek08 "$F8" --out "$P" --szalak 16 \
    >> "$R/pontoz.log" 2>&1 || fail "pontozás ${x%%:*}"
done
for fam in "${CSALADOK_08[@]}"; do
  for sz in CAL TESZT; do
    py kor08/eszkozok/b1rel08.py pontoz --szelet "l06_${fam}_$sz" --lanc "$G/kinyert_06" --fejek08 "$F8" --out "$P" \
      --szalak 16 >> "$R/pontoz.log" 2>&1 || fail "pontozás l06 $fam $sz"
  done
done
say "g5_k1_08 és g5_k3_08 a 08-as karokkal" 1500
py kor08/eszkozok/g5_k1_08.py \
  --csalad "szabaly.koltsegelszamolas:$P/oERT2J_szabaly.koltsegelszamolas_ERT2J.json:kor08/adat/ertelmezes/kor2j/items:$G/orakulum_ERT2J" \
  --csalad "penzugy.bankparositas:$P/oERT2_penzugy.bankparositas_ERT2.json:kor08/adat/ertelmezes/kor2/items:$G/orakulum_ERT2" \
  --csalad "muszaki.hibaelharitas:$P/oERT2_muszaki.hibaelharitas_ERT2.json:kor08/adat/ertelmezes/kor2/items:$G/orakulum_ERT2" \
  --cal "penzugy.bankparositas:$P/l06_penzugy.bankparositas_CAL.json" --cal "muszaki.hibaelharitas:$P/l06_muszaki.hibaelharitas_CAL.json" \
  --cal "szabaly.koltsegelszamolas:$P/l06_szabaly.koltsegelszamolas_CAL.json" \
  --fo-par L-RN,L-S --reps 2000 --ellenoriz kor08/eredmenyek/G1b/kor2j.json --ellenoriz kor08/eredmenyek/G1b/kor2.json \
  --cimke "G1 pilot, a 08-as fejekkel; a kód próbája, a számok nem értelmezhetők" --out "$O/k1_08fejek" \
  >> "$R/g5.log" 2>&1 || fail "g5_k1_08"
py kor08/eszkozok/g5_k3_08.py --forras 06 --cal CAL --teszt TESZT --lanc "$G/kinyert_06" \
  --pont "$P/l06_{csalad}_{szelet}.json" --k07 "cache/k07/f3r_proba/k06_{csalad}_{szelet}.json" \
  --szabaly "$G/szabaly_06" --orakulum "$G/orakulum_06" --kar-x L-RN --reps 2000 \
  --cimke "G1 pilot, a 08-as fejekkel; a kód próbája" --out "$O/k3_08fejek" >> "$R/g5.log" 2>&1 || fail "g5_k3_08"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
