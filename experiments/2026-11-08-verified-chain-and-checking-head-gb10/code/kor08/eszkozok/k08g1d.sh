#!/usr/bin/env bash
# K08G1D — Dani 11-02 (a K08G1A3 és a K08G1B2J után): (1) a bank a v1 kinyerésen, a közös ellenőrzési javításokkal (a
# hibacsalád a v1-en, a szabálycsalád a v2-n marad; `kinyeres_g1`) → lánc, pontosság, kiolvasás, döntések; (2) célzott
# blokkpróba a téves SELECT-ek ellen: a szabálycsalád blokk-változatai orákulum-úton a K3 diag-on és a 06 T500-án
# (`g1_blokk08b`; a v1 T500-kiolvasása a K08G1A3-é). HF-kiolvasás, vLLM nem kell. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1d.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1D"
R="$EXP/logs/k08g1d"
mkdir -p "$R"
G=kor08/adat/G1
B=penzugy.bankparositas
H=muszaki.hibaelharitas
S=szabaly.koltsegelszamolas
KG=$G/kinyeres_g1  # a G1 fejlesztési választása (Dani 11-02): bank és hiba v1, szabály v2
J=cache/k08/jellemzok
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf $*"; }  # a cache root tulajdonú

if [ ! -f DONE-K08G1B2J ]; then echo "$FAZIS: a K08G1B2J nincs kész, nem indul" > "FAILED-$FAZIS"; exit 1; fi
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- archiválás: a v2-es bank állapota ---------------------------------------------------------------------------------
mkdir -p "$G/arch_v2"
for src in 06 07 K3diag; do
  [ -d "$G/arch_v2/kinyert_$src" ] || cp -r "$G/kinyert_$src" "$G/arch_v2/kinyert_$src"
done
for f in lanc_pontossag dontesek; do
  for e in md json; do
    [ -f "kor08/eredmenyek/G1/${f}_v2.$e" ] || cp "kor08/eredmenyek/G1/$f.$e" "kor08/eredmenyek/G1/${f}_v2.$e"
  done
done

# --- 1. a bank lánca a v1 kinyerésen -----------------------------------------------------------------------------------
say "a bank lánca a v1 kinyerésen; a pontosság a G1 választásával" 300
mkdir -p "$KG"
for src in 06 07 K3diag; do
  cp "$G/kinyeres/${src}_$B.jsonl" "$G/kinyeres/${src}_$B.mezok.jsonl" "$G/kinyeres/${src}_$H.jsonl" "$KG/"
  cp "$G/kinyeres_v2/${src}_$S.jsonl" "$G/kinyeres_v2/${src}_$S.mezok.jsonl" "$KG/"
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$B" --ut kinyert --blokk v1 \
    --kinyeres "$KG/${src}_$B.mezok.jsonl" --out "$G/kinyert_$src" >> "$R/lanc.log" 2>&1 || fail "lánc bank $src"
done
python3 kor08/eszkozok/g1_lanc08.py --kinyeres "$KG" --blokk v1 --out kor08/eredmenyek/G1 >> "$R/lanc.log" 2>&1 \
  || fail "a lánc pontossága"

# --- 2. a blokkpróba láncai (orákulum-út) ------------------------------------------------------------------------------
say "a blokkpróba láncai: T500 v0 v2 v3 v4, K3 diag v0 v3 v4 (+ a v1, v2 őre)" 300
feladat=()
for v in v0 v2 v3 v4; do
  python3 kor08/eszkozok/lanc08.py futtat --forras 06 --csalad "$S" --ut orakulum --blokk "$v" \
    --out "$G/orakulum_06_$v" >> "$R/lanc.log" 2>&1 || fail "lánc T500 $v"
  feladat+=(--feladat "o06$v:$S:T500:kanonikus" --feladat "o06$v:$S:T500:b1")
  torol "/exp/$J/o06${v}_${S}_*"
done
for v in v0 v3 v4; do
  python3 kor08/eszkozok/lanc08.py futtat --forras K3diag --csalad "$S" --ut orakulum --blokk "$v" \
    --out "$G/orakulum_K3diag_$v" >> "$R/lanc.log" 2>&1 || fail "lánc K3 $v"
  feladat+=(--feladat "oK3$v:$S:DIAG:kanonikus" --feladat "oK3$v:$S:DIAG:b1")
  torol "/exp/$J/oK3${v}_${S}_*"
done
# őr: a K3 v1 és v2 lánca a délutáni ellenőrzési javítások előtt készült; ha az itemek változnak, azok is újra
for v in v1 v2; do
  cp "$G/orakulum_K3diag_$v/items/$S.jsonl" "$R/K3_${v}_elotte.jsonl"
  python3 kor08/eszkozok/lanc08.py futtat --forras K3diag --csalad "$S" --ut orakulum --blokk "$v" \
    --out "$G/orakulum_K3diag_$v" >> "$R/lanc.log" 2>&1 || fail "lánc K3 $v"
  if ! cmp -s "$G/orakulum_K3diag_$v/items/$S.jsonl" "$R/K3_${v}_elotte.jsonl"; then
    echo "változott: orakulum_K3diag_$v" >> "$R/valtozott.log"
    feladat+=(--feladat "oK3$v:$S:DIAG:kanonikus" --feladat "oK3$v:$S:DIAG:b1")
    torol "/exp/$J/oK3${v}_${S}_*"
  fi
done

# --- 3. kiolvasás ------------------------------------------------------------------------------------------------------
for m in kanonikus b1; do
  feladat+=(--feladat "lK3:$B:DIAG:$m" --feladat "l06:$B:T500:$m")
done
torol "/exp/$J/lK3_${B}_*" "/exp/$J/l06_${B}_*"
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás: a bank valós útja (T500, K3) és a blokkpróba (T500 × 4, K3 × 3)" 7200
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root "$J" --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20

# --- 4. döntések, blokkpróba -------------------------------------------------------------------------------------------
say "a döntések és a blokkpróba" 300
py kor08/eszkozok/g1_dontes08.py --jell "$J" --out kor08/eredmenyek/G1 >> "$R/dontes.log" 2>&1 || fail "döntések"
py kor08/eszkozok/g1_blokk08b.py --jell "$J" --out kor08/eredmenyek/G1 >> "$R/blokk.log" 2>&1 || fail "blokkpróba"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
