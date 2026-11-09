#!/usr/bin/env bash
# K08G1H — (1) a végleges erőbecslés (`ero08`, 2000 szimuláció, a két fő próba közös Holm-döntésével; CPU, a modell
# betöltése előtt); (2) a K08G1G kiolvasásának előre rögzített újrafuttatása (G1-rögzítés v0.2, 10. pont): a K08G1G-n a
# determinizmus-őr jelzett (a referenciaszelet mind az 50 sora eltér, medián 0,47 nat, a det0 és a det1 egymással bitre
# azonos; előtte a gépen vLLM futott, mint az ERT2J-eltérésnél). A K08G1G bank-kiolvasása és döntései archívumba kerülnek
# (`*_detjelzes_k08g1g`), a kiolvasás és a döntések újra futnak; az állapotnapló a hibakereséshez kell. Minden adat
# szintetikus.
#   setsid nohup kor08/eszkozok/k08g1h.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
FAZIS="K08G1H"
R="$EXP/logs/k08g1h"
mkdir -p "$R"
B=penzugy.bankparositas
J=cache/k08/jellemzok
JD=cache/k08/jellemzok_detjelzes_k08g1g
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
gyoker() { docker run --rm -v "$EXP:/exp" -w /exp --entrypoint sh "$TOOL_IMAGE" -c "$1"; }
allapot() {  # a gép állapota a hibakereséshez
  { echo "== $(date '+%F %T') $1"; uptime; free -g | sed -n 2,3p
    nvidia-smi --query-gpu=driver_version,clocks.sm,clocks.mem,power.draw,temperature.gpu,persistence_mode,compute_mode \
      --format=csv,noheader
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    docker ps -a --format '{{.Names}} {{.Status}}' | head -5; } >> "$R/allapot.log" 2>&1
}

python3 kor08/eszkozok/det_or08.py ref > "$R/det_ref.log" 2>&1 || { echo "$FAZIS: a determinizmus-őr referenciája hibás" \
  > "FAILED-$FAZIS"; exit 1; }
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
allapot indulás

# --- 1. erőbecslés -------------------------------------------------------------------------------------------------------
say "erőbecslés (szimuláció, a két fő próba közös Holm-döntésével)" 1200
py kor08/eszkozok/ero08.py --sims 2000 --boot-sims 300 --boot 1000 --out kor08/eredmenyek/G1 >> "$R/ero.log" 2>&1 \
  || fail "erőbecslés"

# --- 2. a K08G1G kiolvasásának újrafuttatása ------------------------------------------------------------------------------
for e in md json; do
  [ -f "kor08/eredmenyek/G1/dontesek_detjelzes_k08g1g.$e" ] \
    || cp "kor08/eredmenyek/G1/dontesek.$e" "kor08/eredmenyek/G1/dontesek_detjelzes_k08g1g.$e" || fail "archiválás: döntések"
done
gyoker "set -e; mkdir -p $JD
  for p in l06_${B}_T500 o06_${B}_T500 det0_${DET_FAM}_T500 det1_${DET_FAM}_T500; do
    for m in kanonikus b1; do
      if [ -d $J/\${p}__\$m ]; then mv $J/\${p}__\$m $JD/; fi
      [ ! -e $J/\${p}__\$m ]  # a kész shardot a kiolvasás kihagyná
    done
  done" >> "$R/archival.log" 2>&1 || fail "archiválás: a K08G1G kiolvasása"
cp "JELZES-DET-K08G1G" "$R/JELZES-DET-K08G1G.masolat" 2>/dev/null || true
feladat=("${DET_ELEJE[@]}")
for m in kanonikus b1; do
  feladat+=(--feladat "l06:$B:T500:$m" --feladat "o06:$B:T500:$m")
done
feladat+=("${DET_VEGE[@]}")
source kor07/eszkozok/lib07.sh
allapot "kiolvasás előtt"
say "kiolvasás: a bank T500 mindkét úton (+ a determinizmus-őr), újrafuttatás" 1500
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root "$J" --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
allapot "kiolvasás után"
det_ellenoriz "$J" "$R"

# --- 3. döntések ---------------------------------------------------------------------------------------------------------
say "a döntések" 120
py kor08/eszkozok/g1_dontes08.py --jell "$J" --out kor08/eredmenyek/G1 >> "$R/dontes.log" 2>&1 || fail "döntések"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
