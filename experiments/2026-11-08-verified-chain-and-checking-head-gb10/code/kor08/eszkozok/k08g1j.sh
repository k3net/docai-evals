#!/usr/bin/env bash
# K08G1J — a G5 elemzők próbája a G1 pilotján (G1-rögzítés 11.: a kód a rögzítés előtt a megismert adaton lefut).
# Fejlesztési számok, nem állítás; minden adat szintetikus. A karok a pilotban: L-S és a befagyasztott 07 fej (L-R07);
# az L-R07 − L-S pár a fő pár helyén áll, hogy a Holm-út is lefusson.
#   A (CPU)  a szabályalapú kinyerés lánca a 06-on (a K3-X-hez); pontozás (`b1rel08 pontoz`) a G1b 2. körén (K1) és a
#            K3 diag két útján (K2); `g5_k1_08`, `g5_k2_08`
#   B (GPU)  a 06 CAL és TESZT kiolvasása a valós kinyerés lánca után (mindhárom család), a determinizmus-őrrel
#   C (CPU)  pontozás a 06 CAL / TESZT-en; `g5_k3_08` (a τ a modell döntésein, és összevetésként a teljes lezárt halmazon)
#   setsid nohup kor08/eszkozok/k08g1j.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
FAZIS="K08G1J"
R="$EXP/logs/k08g1j"
mkdir -p "$R"
G=kor08/adat/G1
J=cache/k08/jellemzok
JA=cache/k08/jellemzok_g1j_elott
P=cache/k08/pontoz/G1
O=kor08/eredmenyek/G1/g5_pilot
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
gyoker() { docker run --rm -v "$EXP:/exp" -w /exp --entrypoint sh "$TOOL_IMAGE" -c "$1"; }

python3 kor08/eszkozok/det_or08.py ref > "$R/det_ref.log" 2>&1 || { echo "$FAZIS: a determinizmus-őr referenciája hibás" \
  > "FAILED-$FAZIS"; exit 1; }
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
mkdir -p "$O"

# --- A: a K1 és a K2 próbája ---------------------------------------------------------------------------------------------
say "A: a szabályalapú kinyerés lánca a 06-on, pontozás (K1, K2)" 900
for fam in "${CSALADOK_08[@]}"; do
  python3 kor08/eszkozok/lanc08.py futtat --forras 06 --csalad "$fam" --ut kinyert --blokk v4 \
    --kinyeres "$G/kinyeres_szabaly/06_$fam.jsonl" --out "$G/szabaly_06" >> "$R/lanc.log" 2>&1 || fail "lánc szabályalapú $fam"
done
for s in oERT2J_szabaly.koltsegelszamolas_ERT2J oERT2_penzugy.bankparositas_ERT2 oERT2_muszaki.hibaelharitas_ERT2 \
         lK3_penzugy.bankparositas_DIAG oK3_penzugy.bankparositas_DIAG lK3_muszaki.hibaelharitas_DIAG \
         oK3_muszaki.hibaelharitas_DIAG lK3_szabaly.koltsegelszamolas_DIAG oK3_szabaly.koltsegelszamolas_DIAG; do
  py kor08/eszkozok/b1rel08.py pontoz --szelet "$s" --out "$P" --szalak 8 >> "$R/pontoz.log" 2>&1 || fail "pontozás $s"
done
say "A: g5_k1_08, g5_k2_08" 600
py kor08/eszkozok/g5_k1_08.py \
  --csalad "szabaly.koltsegelszamolas:$P/oERT2J_szabaly.koltsegelszamolas_ERT2J.json:kor08/adat/ertelmezes/kor2j/items:$G/orakulum_ERT2J" \
  --csalad "penzugy.bankparositas:$P/oERT2_penzugy.bankparositas_ERT2.json:kor08/adat/ertelmezes/kor2/items:$G/orakulum_ERT2" \
  --csalad "muszaki.hibaelharitas:$P/oERT2_muszaki.hibaelharitas_ERT2.json:kor08/adat/ertelmezes/kor2/items:$G/orakulum_ERT2" \
  --fo-par L-R07,L-S --reps 2000 --ellenoriz kor08/eredmenyek/G1b/kor2j.json --ellenoriz kor08/eredmenyek/G1b/kor2.json \
  --cimke "G1 pilot: a G1b 2. köre (a szabálycsalád javítva), orákulum-út; fejlesztési szám" --out "$O/k1" \
  >> "$R/g5.log" 2>&1 || fail "g5_k1_08"
py kor08/eszkozok/g5_k2_08.py --forras K3diag --nelkul "cache/k07/k3/diag_{csalad}.json" \
  --kinyert "$G/kinyert_K3diag:$P/lK3_{csalad}_DIAG.json" --orakulum "$G/orakulum_K3diag:$P/oK3_{csalad}_DIAG.json" \
  --reps 2000 --cimke "G1 pilot: a K3 diag; fejlesztési szám" --out "$O/k2" >> "$R/g5.log" 2>&1 || fail "g5_k2_08"
date '+%F %T' > "$R/A-kesz"

# --- B: a 06 CAL és TESZT kiolvasása a lánc után ------------------------------------------------------------------------
feladat=("${DET_ELEJE[@]}")
for fam in "${CSALADOK_08[@]}"; do
  for sz in CAL TESZT; do
    for m in kanonikus b1; do feladat+=(--feladat "l06:$fam:$sz:$m"); done
  done
done
feladat+=("${DET_VEGE[@]}")
gyoker "set -e; mkdir -p $JA
  for d in $J/l06_*_CAL__* $J/l06_*_TESZT__*; do [ -d \"\$d\" ] && mv \"\$d\" $JA/ || true; done
  ! ls -d $J/l06_*_CAL__* $J/l06_*_TESZT__* 2>/dev/null | grep -q ." >> "$R/archival.log" 2>&1 \
  || fail "archiválás: a korábbi 06 CAL / TESZT-kiolvasás"
det_torol "$J"
source kor07/eszkozok/lib07.sh
say "B: kiolvasás: a 06 CAL és TESZT a lánc után (+ a determinizmus-őr)" 7800
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root "$J" --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
det_ellenoriz "$J" "$R"

# --- C: a K3 próbája ---------------------------------------------------------------------------------------------------
say "C: pontozás a 06 CAL / TESZT-en, g5_k3_08" 1500
for fam in "${CSALADOK_08[@]}"; do
  for sz in CAL TESZT; do
    py kor08/eszkozok/b1rel08.py pontoz --szelet "l06_${fam}_$sz" --out "$P" --szalak 8 >> "$R/pontoz.log" 2>&1 \
      || fail "pontozás l06 $fam $sz"
  done
done
for th in modell rendszer; do
  py kor08/eszkozok/g5_k3_08.py --forras 06 --cal CAL --teszt TESZT --lanc "$G/kinyert_06" \
    --pont "$P/l06_{csalad}_{szelet}.json" --k07 "cache/k07/f3r_proba/k06_{csalad}_{szelet}.json" \
    --szabaly "$G/szabaly_06" --orakulum "$G/orakulum_06" --kar-x L-S --tau-halmaz "$th" --reps 2000 \
    --cimke "G1 pilot: a 06 CAL / TESZT (megismert adat), τ: $th; fejlesztési szám" --out "$O/k3_$th" \
    >> "$R/g5.log" 2>&1 || fail "g5_k3_08 ($th)"
done
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
