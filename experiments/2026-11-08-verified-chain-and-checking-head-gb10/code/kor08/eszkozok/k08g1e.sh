#!/usr/bin/env bash
# K08G1E — Dani 11-03: a szabálycsalád blokkja v4 (a blokkpróba és a determinizmus-próba után). A szabálycsalád lánca
# v4-gyel (06, 07, K3 diag mindkét úton, a G1 kinyerés-választásával; ERT2J orákulum-úton); a v1-es kimenetek archiválva
# (`G1/arch_blokkv1`, `cache/k08/jellemzok_blokkv1`, `*_blokkv1.{md,json}`), a v1 T500-kiolvasása a blokkpróbához
# `o06v1` néven marad. Kiolvasás (T500 és K3 diag mindkét úton, ERT2J) a determinizmus-őrrel (`lib08.sh`: első és
# utolsó feladat), majd lánc-pontosság, döntések, a 2. kör mérése, a blokkpróba újra (változatlan kell legyen). A 07
# CAL / TESZT kiolvasása pecsét alatt van, itt nem fut. HF-kiolvasás, vLLM nem kell. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1e.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
FAZIS="K08G1E"
R="$EXP/logs/k08g1e"
mkdir -p "$R"
G=kor08/adat/G1
S=szabaly.koltsegelszamolas
KG=$G/kinyeres_g1  # a G1 kinyerés-választása (Dani 11-02): bank és hiba v1, szabály v2
J=cache/k08/jellemzok
JA=cache/k08/jellemzok_blokkv1
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf $*"; }  # a cache root tulajdonú
gyoker() { docker run --rm -v "$EXP:/exp" -w /exp --entrypoint sh "$TOOL_IMAGE" -c "$1"; }  # root tulajdonú helyekre

python3 kor08/eszkozok/det_or08.py ref > "$R/det_ref.log" 2>&1 || { echo "$FAZIS: a determinizmus-őr referenciája hibás" \
  > "FAILED-$FAZIS"; exit 1; }
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- archiválás: a v1 blokk állapota ------------------------------------------------------------------------------------
mkdir -p "$G/arch_blokkv1"
for d in kinyert_06 kinyert_07 kinyert_K3diag orakulum_06 orakulum_07 orakulum_K3diag orakulum_ERT2J; do
  [ -d "$G/arch_blokkv1/$d" ] || cp -r "$G/$d" "$G/arch_blokkv1/$d" || fail "archiválás: $d"
done
if [ ! -f "$G/orakulum_06_v1/items/$S.jsonl" ]; then  # a blokkpróba v1-e (`g1_blokk08b`, `o06v1`)
  mkdir -p "$G/orakulum_06_v1/items" && cp "$G/orakulum_06/items/$S.jsonl" "$G/orakulum_06_v1/items/" \
    || fail "archiválás: orakulum_06_v1"
fi
for e in md json; do
  [ -f "kor08/eredmenyek/G1/lanc_pontossag_blokkv1.$e" ] \
    || cp "kor08/eredmenyek/G1/lanc_pontossag.$e" "kor08/eredmenyek/G1/lanc_pontossag_blokkv1.$e" || fail "archiválás: lanc_pontossag"
done
gyoker "set -e
  for e in md json; do
    [ -f kor08/eredmenyek/G1/dontesek_blokkv1.\$e ] || cp kor08/eredmenyek/G1/dontesek.\$e kor08/eredmenyek/G1/dontesek_blokkv1.\$e
    [ -f kor08/eredmenyek/G1b/kor2j_blokkv1.\$e ] || cp kor08/eredmenyek/G1b/kor2j.\$e kor08/eredmenyek/G1b/kor2j_blokkv1.\$e
  done
  mkdir -p $JA
  for p in l06_${S}_T500 lK3_${S}_DIAG oK3_${S}_DIAG oERT2J_${S}_ERT2J; do
    for m in kanonikus b1; do
      [ -d $JA/\${p}__\$m ] || mv $J/\${p}__\$m $JA/\${p}__\$m
    done
  done
  for m in kanonikus b1; do
    [ -d $J/o06v1_${S}_T500__\$m ] || mv $J/o06_${S}_T500__\$m $J/o06v1_${S}_T500__\$m
  done" >> "$R/archival.log" 2>&1 || fail "archiválás: eredmények és cache"

# --- 1. a szabálycsalád lánca, blokk v4 --------------------------------------------------------------------------------
say "a szabálycsalád lánca, blokk v4" 300
for src in 06 07 K3diag; do
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$S" --ut kinyert --blokk v4 \
    --kinyeres "$KG/${src}_$S.mezok.jsonl" --out "$G/kinyert_$src" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $src"
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$S" --ut orakulum --blokk v4 \
    --out "$G/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src"
done
python3 kor08/eszkozok/lanc08.py futtat --forras ERT2J --csalad "$S" --ut orakulum --blokk v4 \
  --out "$G/orakulum_ERT2J" >> "$R/lanc.log" 2>&1 || fail "lánc ERT2J"
python3 kor08/eszkozok/g1_lanc08.py --kinyeres "$KG" --blokk v4 --out kor08/eredmenyek/G1 >> "$R/lanc.log" 2>&1 \
  || fail "a lánc pontossága"
# ellenőrző adat (nem kapu): az orákulum-út v4 itemjei a blokkpróba v4-ével bájtra azonosak-e
for d in 06 K3diag; do
  if cmp -s "$G/orakulum_$d/items/$S.jsonl" "$G/orakulum_${d}_v4/items/$S.jsonl"; then r=azonos; else r=eltér; fi
  echo "orakulum_$d ↔ orakulum_${d}_v4 ($S): $r" >> "$R/lanc.log"
done

# --- 2. kiolvasás a determinizmus-őrrel ----------------------------------------------------------------------------------
feladat=("${DET_ELEJE[@]}")
for m in kanonikus b1; do
  feladat+=(--feladat "l06:$S:T500:$m" --feladat "o06:$S:T500:$m" --feladat "lK3:$S:DIAG:$m" --feladat "oK3:$S:DIAG:$m"
            --feladat "oERT2J:$S:ERT2J:$m")
done
feladat+=("${DET_VEGE[@]}")
torol "/exp/$J/l06_${S}_T500__*" "/exp/$J/o06_${S}_T500__*" "/exp/$J/lK3_${S}_DIAG__*" "/exp/$J/oK3_${S}_DIAG__*" \
      "/exp/$J/oERT2J_${S}_ERT2J__*"
det_torol "$J"
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás, blokk v4: T500 és K3 diag mindkét úton, ERT2J (+ a determinizmus-őr)" 3300
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root "$J" --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
det_ellenoriz "$J" "$R"

# --- 3. döntések, a 2. kör mérése, a blokkpróba --------------------------------------------------------------------------
say "döntések, a 2. kör mérése, a blokkpróba" 300
py kor08/eszkozok/g1_dontes08.py --jell "$J" --out kor08/eredmenyek/G1 >> "$R/dontes.log" 2>&1 || fail "döntések"
py kor08/eszkozok/g1b_ert08.py --jell "$J" --out kor08/eredmenyek/G1b --kor 2 --javitott --csalad "$S" \
  >> "$R/meres.log" 2>&1 || fail "a 2. kör mérése"
py kor08/eszkozok/g1_blokk08b.py --jell "$J" --out kor08/eredmenyek/G1 >> "$R/blokk.log" 2>&1 || fail "blokkpróba"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
