#!/usr/bin/env bash
# K08G1G — Dani 11-03 (a D12-tervezetre): „a hiányzó adatból ne következzen kizárás”. A bank lánca 11-03 előtt a tétel
# pénznemét a nyelvből vette (hu → HUF, en → EUR), és a „Részletek:” / „Tétel részletei:” fejlécet részfizetés-jelnek
# olvasta; most a pénznem a szövegből jön (igazolt deviza vagy önálló pénznemjelölő, különben nincs összegalapú kizárás és
# kötés), a kötéshez ténylegesen elvégzett összegegyezés kell (`lanc08`). Újra: a bank lánca (06, 07, K3 diag mindkét
# úton), a lánc pontossága, a szabályalapú kinyerő összevetése, a bank T500-kiolvasása mindkét úton (a K3 diag-é csak, ha
# az itemek változtak) a determinizmus-őrrel, a döntések. HF-kiolvasás, vLLM nem kell. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1g.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
FAZIS="K08G1G"
R="$EXP/logs/k08g1g"
mkdir -p "$R"
G=kor08/adat/G1
B=penzugy.bankparositas
KG=$G/kinyeres_g1
J=cache/k08/jellemzok
JA=cache/k08/jellemzok_bankdeviza_elott
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf $*"; }  # a cache root tulajdonú
gyoker() { docker run --rm -v "$EXP:/exp" -w /exp --entrypoint sh "$TOOL_IMAGE" -c "$1"; }

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

# --- archiválás: a 11-03 előtti bank-lánc --------------------------------------------------------------------------------
mkdir -p "$G/arch_bankdeviza_elott"
for d in kinyert_06 kinyert_07 kinyert_K3diag orakulum_06 orakulum_07 orakulum_K3diag; do
  mkdir -p "$G/arch_bankdeviza_elott/$d/items"
  for f in "items/$B.jsonl" "lanc_$B.jsonl"; do
    [ -f "$G/arch_bankdeviza_elott/$d/$f" ] || cp "$G/$d/$f" "$G/arch_bankdeviza_elott/$d/$f" || fail "archiválás: $d $f"
  done
done
for f in lanc_pontossag kinyero_osszevetes; do
  for e in md json; do
    [ -f "kor08/eredmenyek/G1/${f}_bankdeviza_elott.$e" ] \
      || cp "kor08/eredmenyek/G1/$f.$e" "kor08/eredmenyek/G1/${f}_bankdeviza_elott.$e" || fail "archiválás: $f"
  done
done
gyoker "set -e
  for e in md json; do
    [ -f kor08/eredmenyek/G1/dontesek_bankdeviza_elott.\$e ] || cp kor08/eredmenyek/G1/dontesek.\$e kor08/eredmenyek/G1/dontesek_bankdeviza_elott.\$e
  done
  mkdir -p $JA
  for p in l06_${B}_T500 o06_${B}_T500; do
    for m in kanonikus b1; do
      [ -d $JA/\${p}__\$m ] || mv $J/\${p}__\$m $JA/\${p}__\$m
    done
  done" >> "$R/archival.log" 2>&1 || fail "archiválás: döntések és cache"

# --- 1. a bank lánca --------------------------------------------------------------------------------------------------
say "a bank lánca (pénznem a szövegből)" 300
for src in 06 07 K3diag; do
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$B" --ut kinyert --blokk v4 \
    --kinyeres "$KG/${src}_$B.mezok.jsonl" --out "$G/kinyert_$src" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $src"
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$B" --ut orakulum --blokk v4 \
    --out "$G/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src"
done
for d in kinyert_06 kinyert_07 kinyert_K3diag orakulum_06 orakulum_07 orakulum_K3diag; do
  if cmp -s "$G/$d/items/$B.jsonl" "$G/arch_bankdeviza_elott/$d/items/$B.jsonl"; then r=azonos; else r=eltér; fi
  echo "$d ($B): $r" >> "$R/valtozott.log"
done
python3 kor08/eszkozok/g1_lanc08.py --kinyeres "$KG" --blokk v4 --out kor08/eredmenyek/G1 >> "$R/lanc.log" 2>&1 \
  || fail "a lánc pontossága"
python3 kor08/eszkozok/g1_lanc08.py --kinyeres "$G/kinyeres_szabaly" --blokk v4 --out kor08/eredmenyek/G1/szabalyalapu \
  >> "$R/lanc.log" 2>&1 || fail "a lánc pontossága a szabályalapú kinyeréssel"
python3 kor08/eszkozok/g1_kin_szab08.py --alany "$KG" --szabaly "$G/kinyeres_szabaly" --blokk v4 --out kor08/eredmenyek/G1 \
  >> "$R/lanc.log" 2>&1 || fail "a kinyerők összevetése"

# --- 2. kiolvasás a determinizmus-őrrel ----------------------------------------------------------------------------------
feladat=("${DET_ELEJE[@]}")
for m in kanonikus b1; do
  feladat+=(--feladat "l06:$B:T500:$m" --feladat "o06:$B:T500:$m")
done
for x in "kinyert_K3diag:lK3" "orakulum_K3diag:oK3"; do  # őr: a K3 diag csak, ha változott
  IFS=: read -r d e <<< "$x"
  if ! cmp -s "$G/$d/items/$B.jsonl" "$G/arch_bankdeviza_elott/$d/items/$B.jsonl"; then
    feladat+=(--feladat "$e:$B:DIAG:kanonikus" --feladat "$e:$B:DIAG:b1")
    gyoker "set -e; mkdir -p $JA; for m in kanonikus b1; do [ -d $JA/${e}_${B}_DIAG__\$m ] || mv $J/${e}_${B}_DIAG__\$m $JA/; done" \
      >> "$R/archival.log" 2>&1 || fail "archiválás: $e"
  fi
done
feladat+=("${DET_VEGE[@]}")
torol "/exp/$J/l06_${B}_T500__*" "/exp/$J/o06_${B}_T500__*"
det_torol "$J"
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás: a bank T500 mindkét úton (+ a determinizmus-őr)" 2400
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root "$J" --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
det_ellenoriz "$J" "$R"

# --- 3. döntések ---------------------------------------------------------------------------------------------------------
say "a döntések" 120
py kor08/eszkozok/g1_dontes08.py --jell "$J" --out kor08/eredmenyek/G1 >> "$R/dontes.log" 2>&1 || fail "döntések"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
