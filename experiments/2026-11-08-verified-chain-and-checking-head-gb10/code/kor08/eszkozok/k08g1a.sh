#!/usr/bin/env bash
# K08G1A — 08 G1, első rész (08-runbook 8.; Dani 11-02 „indulhat”): a megismert szeleteken (06 T500 / CAL / TESZT,
# 07 CAL / TESZT, K3 diag) (1) valós kinyerés az alannyal (vLLM, LORA=0, `kinyer08`), (2) a lánc valós és
# orákulum-kinyeréssel (`lanc08 futtat`, üres lista a modellnek), (3) a lánc pontossága (`g1_lanc08`), (4) kiolvasás a
# négyállapotú kerettel a 06 T500 és a K3 diag lánc utáni itemjein mindkét úton (`kiolvas08`), (5) a döntések
# (`g1_dontes08`). Tervezési számok, nem állítások; minden adat szintetikus és megismert.
#   setsid nohup kor08/eszkozok/k08g1a.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1A"
R="$EXP/logs/k08g1a"
mkdir -p "$R"
CSALADOK=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
ALANY=ldh-alany08
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"

# az őrök nem a `fail`-lel lépnek ki (az leállítaná a konténereket); a próbából futó alanyt átvesszük
if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -v "^$ALANY\$" | grep -q .; then
  echo "$FAZIS: fut egy másik konténer, nem indul" > "FAILED-$FAZIS"; exit 1
fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

if ! docker ps --format '{{.Names}}' | grep -q "^$ALANY\$"; then
  say "az alany indítása (vLLM, LORA=0)" 900
  LORA=0 PREFIX=1 subject_start "$ALANY" >> "$R/alany.log" 2>&1
  subject_wait "$ALANY" 1800 || fail "az alany nem állt fel"
fi
say "valós kinyerés: 06, 07, K3 diag" 3000
for src in 06 07 K3diag; do
  python3 kor08/eszkozok/kinyer08.py --forras "$src" --out kor08/adat/G1/kinyeres >> "$R/kinyeres.log" 2>&1 \
    || fail "kinyerés $src"
done
subject_stop "$ALANY" "$R"
sleep 20

say "a lánc valós és orákulum-kinyeréssel" 300
for src in 06 07 K3diag; do
  for f in "${CSALADOK[@]}"; do
    python3 - "$src" "$f" > "kor08/adat/G1/kinyeres/${src}_${f}.mezok.jsonl" <<'EOF' || fail "mezők $src $f"
import json, sys
src, fam = sys.argv[1], sys.argv[2]
for x in open(f"kor08/adat/G1/kinyeres/{src}_{fam}.jsonl", encoding="utf-8"):
    r = json.loads(x)
    print(json.dumps({"id": r["id"], "mezok": r["mezok"]}, ensure_ascii=False))
EOF
    python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$f" --ut kinyert \
      --kinyeres "kor08/adat/G1/kinyeres/${src}_${f}.mezok.jsonl" --out "kor08/adat/G1/kinyert_$src" >> "$R/lanc.log" 2>&1 \
      || fail "lánc kinyert $src $f"
    python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$f" --ut orakulum \
      --out "kor08/adat/G1/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src $f"
  done
done
python3 kor08/eszkozok/g1_lanc08.py --kinyeres kor08/adat/G1/kinyeres --out kor08/eredmenyek/G1 >> "$R/lanc.log" 2>&1 \
  || fail "a lánc pontossága"

feladat=()
for f in "${CSALADOK[@]}"; do
  for m in kanonikus b1; do
    feladat+=(--feladat "lK3:$f:DIAG:$m" --feladat "oK3:$f:DIAG:$m" --feladat "l06:$f:T500:$m" --feladat "o06:$f:T500:$m")
  done
done
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás, négyállapotú keret (T500 és K3 diag, mindkét út)" 4200
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
