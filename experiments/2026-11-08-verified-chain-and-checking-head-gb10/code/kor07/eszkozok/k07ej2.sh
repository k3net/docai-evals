#!/usr/bin/env bash
# K07EJ2 — éjszakai sor (2026-11-01, Dani kérésére): (1) a páros diagnosztikai próba itemjei (`aug07 epit`: a K07K3
# itemjei a géppel kiszámított sorral), (2) kiolvasás mindkét kerettel a kiegészített diagnosztikai mintán és a 07B
# valódi banki tételein (`kiolvas07x`; nyitott `cache/k07/jellemzok[2]`), (3) a mentett fejek pontozása
# (`b1rel07x`: aug:<család> → cache/k07/aug, b7:penzugy.bankparositas → cache/k07/b7). Az elemzés utána helyben.
# A 07B-itemek valódi adatok (<tenant>, Dani D7-döntése: futás a spark-deven); a naplóba csak darabszám kerül.
#   setsid nohup kor07/eszkozok/k07ej2.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K07EJ2"
R="$EXP/logs/k07ej2"
mkdir -p "$R"
CSALADOK=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"

# az őrök nem a `fail`-lel lépnek ki: az törölné a másik fázis AKTIV_FAZIS-át és leállítaná a Muse-konténert
if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
if [ ! -s kor07/adat/b7/items/penzugy.bankparositas.jsonl ]; then echo "$FAZIS: hiányzik a 07B itemfájlja" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

say "a páros próba itemjei"
cpy kor07/eszkozok/aug07.py epit >> "$R/aug.log" 2>&1 || fail "aug07 epit"
feladat=()
for f in "${CSALADOK[@]}"; do
  for m in kanonikus b1; do feladat+=(--feladat "diagaug:$f:DIAG:$m"); done
done
for m in kanonikus b1; do feladat+=(--feladat "b7:penzugy.bankparositas:B7:$m"); done
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás, négyállapotú keret" 2400
memoria_or07 "$R/memoria4.log"
py07 kor07/eszkozok/kiolvas07x.py kivon "${feladat[@]}" --out-root cache/k07/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas4.log" 2>&1 || fail "kiolvasás (4)"
sleep 20
say "kiolvasás, 06-os kétkimenetű keret" 2400
memoria_or07 "$R/memoria2.log"
py07 kor07/eszkozok/kiolvas07x.py kivon --keret 2 "${feladat[@]}" --out-root cache/k07/jellemzok2 --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas2.log" 2>&1 || fail "kiolvasás (2)"
sleep 20
say "pontozás a mentett fejekkel" 600
for f in "${CSALADOK[@]}"; do
  py kor07/eszkozok/b1rel07x.py pontoz --szelet "aug:$f" --out cache/k07/aug >> "$R/pontoz.log" 2>&1 || fail "pontoz aug:$f"
done
py kor07/eszkozok/b1rel07x.py pontoz --szelet b7:penzugy.bankparositas --out cache/k07/b7 >> "$R/pontoz.log" 2>&1 || fail "pontoz b7"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
