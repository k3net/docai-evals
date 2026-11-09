#!/usr/bin/env bash
# K08G1I — a szintetikus bank feladatszabálya (Dani 11-03): minden szintetikus banki tanító- és értékelési bemenet
# kérdése után ugyanaz a mondat („Ebben a feladatban a részfizetést a leírás mindig jelzi; ilyen jelzés hiányában teljes
# kiegyenlítést feltételezz.”; `lanc08.bank_kerdes`), mert a lánc ezt a feltevést alkalmazza, és az alanynak is meg kell
# kapnia. Újra: a bank lánca (06, 07, K3 diag mindkét úton; a lánc döntései nem változnak, csak a kérdés: ellenőrizve),
# a bank T500- és K3 diag-kiolvasása mindkét úton a determinizmus-őrrel, a döntések. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g1i.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
FAZIS="K08G1I"
R="$EXP/logs/k08g1i"
mkdir -p "$R"
G=kor08/adat/G1
A=$G/arch_bankszabaly_elott
B=penzugy.bankparositas
KG=$G/kinyeres_g1
J=cache/k08/jellemzok
JA=cache/k08/jellemzok_bankszabaly_elott
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
gyoker() { docker run --rm -v "$EXP:/exp" -w /exp --entrypoint sh "$TOOL_IMAGE" -c "$1"; }
allapot() {  # a gép állapota (a determinizmus-őr jelzéseinek hibakereséséhez, mint a K08G1H-ban)
  { echo "== $(date '+%F %T') $1"; free -g | sed -n 2,3p
    nvidia-smi --query-gpu=clocks.sm,power.draw,temperature.gpu --format=csv,noheader
    docker ps -a --format '{{.Names}} {{.Status}}' | head -3; } >> "$R/allapot.log" 2>&1
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

# --- archiválás: a feladatszabály előtti bank-lánc, kiolvasás és döntések -------------------------------------------------
for d in kinyert_06 kinyert_07 kinyert_K3diag orakulum_06 orakulum_07 orakulum_K3diag; do
  mkdir -p "$A/$d/items"
  for f in "items/$B.jsonl" "lanc_$B.jsonl"; do
    [ -f "$A/$d/$f" ] || cp "$G/$d/$f" "$A/$d/$f" || fail "archiválás: $d $f"
  done
done
for e in md json; do
  [ -f "kor08/eredmenyek/G1/dontesek_bankszabaly_elott.$e" ] \
    || cp "kor08/eredmenyek/G1/dontesek.$e" "kor08/eredmenyek/G1/dontesek_bankszabaly_elott.$e" || fail "archiválás: döntések"
done
gyoker "set -e; mkdir -p $JA
  for p in l06_${B}_T500 o06_${B}_T500 lK3_${B}_DIAG oK3_${B}_DIAG; do
    for m in kanonikus b1; do
      if [ -d $J/\${p}__\$m ]; then mv $J/\${p}__\$m $JA/; fi
      [ ! -e $J/\${p}__\$m ]  # a kész shardot a kiolvasás kihagyná
    done
  done" >> "$R/archival.log" 2>&1 || fail "archiválás: a kiolvasás"

# --- 1. a bank lánca a feladatszabállyal --------------------------------------------------------------------------------
say "a bank lánca (a kérdés után a feladatszabály)" 300
for src in 06 07 K3diag; do
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$B" --ut kinyert --blokk v4 \
    --kinyeres "$KG/${src}_$B.mezok.jsonl" --out "$G/kinyert_$src" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $src"
  python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$B" --ut orakulum --blokk v4 \
    --out "$G/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src"
done
python3 - "$G" "$A" "$B" > "$R/ellenorzes.log" 2>&1 <<'EOF' || fail "a lánc a feladatszabállyal nem csak a kérdésben tér el"
import json, sys
from pathlib import Path
sys.path.insert(0, "kor08/eszkozok")
import lanc08 as L
G, A, B = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
hiba = 0
for d in ("kinyert_06", "kinyert_07", "kinyert_K3diag", "orakulum_06", "orakulum_07", "orakulum_K3diag"):
    regi = {r["id"]: r for r in map(json.loads, (A / d / "items" / f"{B}.jsonl").read_text(encoding="utf-8").splitlines())}
    uj = {r["id"]: r for r in map(json.loads, (G / d / "items" / f"{B}.jsonl").read_text(encoding="utf-8").splitlines())}
    lanc_azonos = (A / d / f"lanc_{B}.jsonl").read_bytes() == (G / d / f"lanc_{B}.jsonl").read_bytes()
    rossz = [i for i in uj if i not in regi or {**regi[i], "question": L.bank_kerdes(regi[i])} != uj[i]]
    hiba += bool(rossz) or uj.keys() != regi.keys() or not lanc_azonos
    print(f"{d}: {len(uj)} item, csak a kérdés tér el: {not rossz and uj.keys() == regi.keys()}, a lánc kimenete azonos: {lanc_azonos}")
sys.exit(1 if hiba else 0)
EOF

# --- 2. kiolvasás a determinizmus-őrrel ----------------------------------------------------------------------------------
feladat=("${DET_ELEJE[@]}")
for m in kanonikus b1; do
  feladat+=(--feladat "l06:$B:T500:$m" --feladat "o06:$B:T500:$m" --feladat "lK3:$B:DIAG:$m" --feladat "oK3:$B:DIAG:$m")
done
feladat+=("${DET_VEGE[@]}")
det_torol "$J"
source kor07/eszkozok/lib07.sh
say "kiolvasás: a bank T500 és K3 diag mindkét úton (+ a determinizmus-őr)" 2100
allapot "kiolvasás előtt"
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
