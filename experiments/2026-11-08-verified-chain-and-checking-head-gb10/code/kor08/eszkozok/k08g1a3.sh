#!/usr/bin/env bash
# K08G1A3 — a G1a egységes újrafuttatása a javított kinyeréssel és blokkal (Dani 11-02: „siker esetén egységesen újra
# kell készíteni az érintett fejlesztési kimeneteket”; a 3. próba után Dani döntése: a v2 kinyerés és a v1 blokk megy
# tovább, a ≤ 1%-os kontrollfeltétel nem teljesült, 3 / 240):
#   kinyerés   séma v2 a bank- és a szabálycsaládon (06, 07, K3 diag); a hibacsalád a v1 kinyerését tartja; ugyanazon a
#              példányon a v1 séma a közös kontrollon (`kin2_proba/kozos.txt`, a futás előtt kijelölve)
#   lánc       minden forrás és család, mindkét út, a szabálycsalád blokkja v1 (`lanc08 --blokk v1`)
#   közös      a két séma a közös kontrollon, ugyanazzal a lánckóddal (`kin2_08 kozos`, leíró)
#   kiolvasás  a változott lánc utáni itemek (bank: valós út; szabály: mindkét út), T500 és K3 diag
# A v1 menet kimenetei: `kor08/adat/G1/arch_v1/`, `kor08/eredmenyek/G1/*_v1.{md,json}`.
#   setsid nohup kor08/eszkozok/k08g1a3.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1A3"
R="$EXP/logs/k08g1a3"
mkdir -p "$R"
CSALADOK=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
V2=(penzugy.bankparositas szabaly.koltsegelszamolas)
ALANY=ldh-alany08
G=kor08/adat/G1
K=$G/kinyeres_v2
P=$G/kin2_proba
KOZOS_SHA=d3488e6e9af8036ec64dfc0a276507b932da3d923942d01a4f24fd2f95a522d5  # a napló 11-02-i bejegyzése szerint
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
torol() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf $*"; }  # a cache root tulajdonú

if [ ! -f DONE-K08G1C3 ]; then echo "$FAZIS: a K08G1C3 nincs kész, nem indul" > "FAILED-$FAZIS"; exit 1; fi
if [ "$(sha256sum "$P/kozos.txt" | cut -d' ' -f1)" != "$KOZOS_SHA" ]; then
  echo "$FAZIS: a közös kontroll nem az előre kijelölt" > "FAILED-$FAZIS"; exit 1
fi
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- archiválás --------------------------------------------------------------------------------------------------------
mkdir -p "$G/arch_v1"
for src in 06 07 K3diag; do
  for ut in kinyert orakulum; do
    [ -d "$G/arch_v1/${ut}_$src" ] || cp -r "$G/${ut}_$src" "$G/arch_v1/${ut}_$src"
  done
done
for f in lanc_pontossag dontesek; do
  for e in md json; do
    [ -f "kor08/eredmenyek/G1/${f}_v1.$e" ] || cp "kor08/eredmenyek/G1/$f.$e" "kor08/eredmenyek/G1/${f}_v1.$e"
  done
done

# --- 1. kinyerés -------------------------------------------------------------------------------------------------------
say "az alany indítása (vLLM, LORA=0)" 900
LORA=0 PREFIX=1 subject_start "$ALANY" >> "$R/alany.log" 2>&1
subject_wait "$ALANY" 1800 || fail "az alany nem állt fel"
say "kinyerés, séma v2: bank és szabály (7385 item)" 5400
mkdir -p "$K"
for src in 06 07 K3diag; do
  for f in "${V2[@]}"; do
    python3 kor08/eszkozok/kinyer08.py --forras "$src" --csalad "$f" --sema 2 --out "$K" >> "$R/kinyeres.log" 2>&1 \
      || fail "kinyerés $src $f"
  done
  cp "$G/kinyeres/${src}_muszaki.hibaelharitas.jsonl" "$K/"  # a hibacsalád a v1-en
done
say "kinyerés, séma v1: a közös kontroll (240 item)" 600
rm -rf "$P/kinyeres_kozos_v1"
for src in 06 07 K3diag; do
  for f in "${V2[@]}"; do
    python3 kor08/eszkozok/kinyer08.py --forras "$src" --csalad "$f" --sema 1 --idk "$P/kozos.txt" \
      --out "$P/kinyeres_kozos_v1" >> "$R/kinyeres.log" 2>&1 || fail "kinyerés v1, közös $src $f"
  done
done
subject_stop "$ALANY" "$R"
sleep 20

# --- 2. lánc ------------------------------------------------------------------------------------------------------------
say "a lánc, blokk v1" 600
for src in 06 07 K3diag; do
  for f in "${CSALADOK[@]}"; do
    python3 - "$K" "$src" "$f" > "$K/${src}_${f}.mezok.jsonl" <<'PY' || fail "mezők $src $f"
import json, sys
k, src, fam = sys.argv[1:4]
for x in open(f"{k}/{src}_{fam}.jsonl", encoding="utf-8"):
    r = json.loads(x)
    print(json.dumps({"id": r["id"], "mezok": r["mezok"]}, ensure_ascii=False))
PY
    python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$f" --ut kinyert --blokk v1 \
      --kinyeres "$K/${src}_${f}.mezok.jsonl" --out "$G/kinyert_$src" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $src $f"
    python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$f" --ut orakulum --blokk v1 \
      --out "$G/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src $f"
  done
done
python3 kor08/eszkozok/g1_lanc08.py --kinyeres "$K" --blokk v1 --out kor08/eredmenyek/G1 >> "$R/lanc.log" 2>&1 \
  || fail "a lánc pontossága"
python3 kor08/eszkozok/kin2_08.py kozos --v1-ujra "$P/kinyeres_kozos_v1" --v2 "$K" --blokk v1 --nev kin2_kozos \
  >> "$R/kozos.log" 2>&1 || fail "a közös kontroll"

# --- 3. kiolvasás, 4. döntések ----------------------------------------------------------------------------------------
# a változott lánc utáni itemek: a bank valós útja (v2 kinyerés) és a szabálycsalád mindkét útja (v2 kinyerés, blokk v1);
# a bank orákulum-útja és a hibacsalád itemjei bájtra azonosak, azok kiolvasása marad
B=penzugy.bankparositas
S=szabaly.koltsegelszamolas
feladat=()
for m in kanonikus b1; do
  feladat+=(--feladat "lK3:$B:DIAG:$m" --feladat "l06:$B:T500:$m"
            --feladat "lK3:$S:DIAG:$m" --feladat "oK3:$S:DIAG:$m" --feladat "l06:$S:T500:$m" --feladat "o06:$S:T500:$m")
done
# őr: ha a bank orákulum-útjának vagy a hibacsaládnak a lánc utáni itemjei mégis változtak, azok is újra
for x in "orakulum_06:o06:$B:T500" "orakulum_K3diag:oK3:$B:DIAG" "kinyert_06:l06:muszaki.hibaelharitas:T500" \
         "orakulum_06:o06:muszaki.hibaelharitas:T500" "kinyert_K3diag:lK3:muszaki.hibaelharitas:DIAG" \
         "orakulum_K3diag:oK3:muszaki.hibaelharitas:DIAG"; do
  IFS=: read -r d e f sz <<< "$x"
  if ! cmp -s "$G/$d/items/$f.jsonl" "$G/arch_v1/$d/items/$f.jsonl"; then
    echo "változott: $d $f" >> "$R/valtozott.log"
    feladat+=(--feladat "$e:$f:$sz:kanonikus" --feladat "$e:$f:$sz:b1")
    torol "/exp/cache/k08/jellemzok/${e}_${f}_*"
  fi
done
torol "/exp/cache/k08/jellemzok/lK3_${B}_*" "/exp/cache/k08/jellemzok/l06_${B}_*" \
      "/exp/cache/k08/jellemzok/lK3_${S}_*" "/exp/cache/k08/jellemzok/oK3_${S}_*" \
      "/exp/cache/k08/jellemzok/l06_${S}_*" "/exp/cache/k08/jellemzok/o06_${S}_*"
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás: a változott itemek (bank valós út, szabály mindkét út), T500 és K3 diag" 4200
memoria_or07 "$R/memoria.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root cache/k08/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
say "a döntések" 300
py kor08/eszkozok/g1_dontes08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1 >> "$R/dontes.log" 2>&1 \
  || fail "döntések"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
