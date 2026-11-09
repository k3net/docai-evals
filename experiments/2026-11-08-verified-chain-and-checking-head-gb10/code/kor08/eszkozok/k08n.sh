#!/usr/bin/env bash
# K08N — az erősebb kontroll második fele (N-rögzítés): kinyerés az alannyal, a rögzített lánc két úton, kiolvasás R-módban (a `k08j.sh` `kiolvas_r`-je), pontozás a befagyasztott fejekkel, a rögzített
# `g5_k1_08`, a szöveges modellek a K1(a'') halmazán. Csak a szabálycsalád. Fejet nem tanít. **Csak az N rögzítése után fut.**
#   setsid nohup kor08/eszkozok/k08n.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
source kor07/eszkozok/lib07.sh
export PATH="$EXP/kor08/eszkozok/burok_g3:$PATH"
FAZIS="K08N"; D=kor08/adat/N; C=cache/k08/n; O=kor08/eredmenyek/N; R="$EXP/logs/k08n"; REPS=10000
mkdir -p "$R"
J=(kor08/eszkozok/n08.py)
G="$D/G3"
K="$G/kinyeres"
JJ="$C/jellemzok"
PP="$C/pontoz"
ALANY=ldh-alany08
SRC=N1T
PROBA=6
DETD=det0_szabaly.koltsegelszamolas_T500__kanonikus
CSALADOK_08=(szabaly.koltsegelszamolas)
declare -A SEMA=([szabaly.koltsegelszamolas]=2)
L="$R/lepesek.log"
lep() { echo "[$(date '+%F %T')] $*" >> "$L"; }
kapu() { lep "KAPU: $*"; echo "[$(date '+%F %T')] $FAZIS: $*" > "FAILED-$FAZIS"; exit 1; }
konti() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "$1"; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
allapot() {
  { echo "== $(date '+%F %T') $1"; uptime; free -g | sed -n 2,3p
    nvidia-smi --query-gpu=driver_version,clocks.sm,power.draw,temperature.gpu --format=csv,noheader
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    docker ps -a --format '{{.Names}} {{.Status}}' | head -5; } >> "$R/allapot.log" 2>&1
}
memoria_or() {  # memoria_or <konténer>: 15 GB alatt leállítja
  ( while docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q true; do
      [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T') ($1)" >> "$R/memoria.log"; docker rm -f "$1"; }
      sleep 30
    done ) &
}
varj() {  # varj <konténer> <port>
  local t0; t0=$(date +%s)
  until curl -fsS "http://127.0.0.1:$2/health" >/dev/null 2>&1; do
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" != "true" ] && return 1
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && return 1
    [ $(( $(date +%s) - t0 )) -gt 2700 ] && return 1
    sleep 15
  done
}

# --- kapuk ---------------------------------------------------------------------------------------------------------------
lep "indul"
[ -f "DONE-$FAZIS" ] && kapu "már kész ($(cat "DONE-$FAZIS"))"
[ -f kor08/rogzites/N/manifest.json ] || kapu "nincs N-rögzítés (kor08/rogzites/N/manifest.json)"
python3 kor08/eszkozok/n08.py ellenoriz >> "$L" 2>&1 || kapu "az N rögzítése nem zöld"
python3 kor08/eszkozok/rogzit08.py ellenoriz >> "$L" 2>&1 || kapu "a D12 rögzítése nem zöld"
[ -e "$C" ] && kapu "$C már létezik"
[ -f AKTIV_FAZIS ] && kapu "fut egy fázis ($(cat AKTIV_FAZIS))"
docker ps --format '{{.Names}}' | grep -q . && kapu "fut egy konténer"
python3 kor08/eszkozok/det_or08.py ref >> "$L" 2>&1 || kapu "a determinizmus-őr referenciája hibás"
rm -f "FAILED-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
record_env
allapot indulás

# --- 2. kinyerés -----------------------------------------------------------------------------------------------------------
say "az alany indítása (vLLM, LORA=0)" 900
LORA=0 PREFIX=1 subject_start "$ALANY" >> "$R/alany.log" 2>&1
subject_wait "$ALANY" 1800 || fail "az alany nem állt fel"
say "kinyerés" 1800
lep "kinyerés"
mkdir -p "$K"
for f in "${CSALADOK_08[@]}"; do
  python3 "${J[@]}" kinyer --forras "$SRC" --csalad "$f" --sema "${SEMA[$f]}" --out "$K" >> "$R/kinyeres.log" 2>&1 || fail "kinyerés $f"
done
subject_stop "$ALANY" "$R"
sha256sum "$K"/*.jsonl > "$R/kinyeres.sha256"
allapot "a kinyerés után"
sleep 30

# --- 3. a lánc három úton --------------------------------------------------------------------------------------------------
say "a lánc" 300
lep "lánc"
for f in "${CSALADOK_08[@]}"; do
  python3 - "$K" "$SRC" "$f" > "$K/${SRC}_$f.mezok.jsonl" <<'PY' || fail "mezők $f"
import json, sys
k, src, fam = sys.argv[1:4]
for x in open(f"{k}/{src}_{fam}.jsonl", encoding="utf-8"):
    r = json.loads(x)
    print(json.dumps({"id": r["id"], "mezok": r["mezok"]}, ensure_ascii=False))
PY
  python3 "${J[@]}" lanc0 futtat --forras "$SRC" --csalad "$f" --ut kinyert --blokk v4 --kinyeres "$K/${SRC}_$f.mezok.jsonl" \
    --out "$G/kinyert_$SRC" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $f"
  python3 "${J[@]}" lanc0 futtat --forras "$SRC" --csalad "$f" --ut orakulum --blokk v4 \
    --out "$G/orakulum_$SRC" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $f"
done
find "$G"/kinyert_* "$G"/orakulum_* -type f | sort | xargs sha256sum > "$R/lanc.sha256"

# --- 4. kiolvasás R-módban (a `k08g3c.sh` `kiolvas_r`-je) ----------------------------------------------------------------------
kiolvas_r() {  # kiolvas_r <out-root> <archív-előtag> <feladatok…>
  local root="$1" arch="$2"; shift 2
  local fel=("${DET_ELEJE[@]}" "$@" "${DET_VEGE[@]}") k pid t0 ok
  for k in $(seq 1 "$PROBA"); do
    if [ "$k" != 1 ]; then
      konti "set -e; mkdir -p /exp/${arch}_proba$((k - 1)); mv /exp/$root/* /exp/${arch}_proba$((k - 1))/" >> "$L" 2>&1 \
        || fail "a $((k - 1)). próba félretétele"
    fi
    allapot "kiolvasás előtt ($k. próba)"
    memoria_or07 "$R/memoria.log"
    lep "kiolvasás: $k. próba indul"
    py07 "${J[@]}" kiolvas kivon "${fel[@]}" --out-root "$root" --status "STATUS-$FAZIS-j" >> "$R/kiolvasas_c$k.log" 2>&1 &
    pid=$!
    t0=$(date +%s)
    ok=""
    while :; do
      if konti "test -f /exp/$root/$DETD/osszegzes.json"; then
        python3 kor08/eszkozok/det_or08.py ellenoriz --jell "$root" --elo det0 --out "$R/det_or_c${k}_det0.json" >> "$R/det_or.log" 2>&1
        case $? in 0) ok=1 ;; 3) ok=0 ;; *) ok=H ;; esac
        break
      fi
      kill -0 "$pid" 2>/dev/null || break
      [ $(( $(date +%s) - t0 )) -gt 2700 ] && { ok=T; break; }
      sleep 20
    done
    case "$ok" in
      1)
        lep "kiolvasás: $k. próba R-módban (a det0 bitre azonos), megy tovább"
        wait "$pid" || fail "kiolvasás"
        sleep 20
        allapot "kiolvasás után ($k. próba)"
        det_ellenoriz "$root" "$R"
        [ -f "JELZES-DET-$FAZIS" ] && fail "a det1 a folyamat végén eltért; a folytatásról Dani dönt"
        lep "kiolvasás: kész, a det0 és a det1 bitre azonos"
        return 0 ;;
      0)
        lep "kiolvasás: $k. próba nem R-mód; a folyamat leáll, a részkimenet félre"
        docker ps --format '{{.Names}}' | grep '^ldh-py07' | xargs -r docker rm -f >> "$L" 2>&1
        wait "$pid" 2>/dev/null
        sleep 20 ;;
      T) fail "45 perc alatt sem készült el a det0 ($k. próba)" ;;
      H) fail "a determinizmus-őr nem futott le a det0-n ($k. próba)" ;;
      *) wait "$pid"; fail "a kiolvasás a det0 előtt kilépett ($k. próba)" ;;
    esac
  done
  fail "$PROBA próbából egy sem került R-módba; a folytatásról Dani dönt"
}
fel=()
for f in "${CSALADOK_08[@]}"; do
  for m in kanonikus b1; do fel+=(--feladat "l$SRC:$f:$SRC:$m"); done
done
say "kiolvasás R-módban" 2400
kiolvas_r "$JJ" "$C/arch" "${fel[@]}"

# --- 5. pontozás és a K1 ---------------------------------------------------------------------------------------------------------
say "pontozás" 600
lep "pontozás"
for f in "${CSALADOK_08[@]}"; do
  py "${J[@]}" b1rel pontoz --szelet "l${SRC}_${f}_$SRC" --jell "$JJ" --lanc "$G/kinyert_$SRC" --fejek08 cache/k08/fejek08 --out "$PP" --szalak 16 >> "$R/pontoz.log" 2>&1 \
    || fail "pontozás $f"
done
say "K1" 1800
lep "K1"
f=szabaly.koltsegelszamolas
py "${J[@]}" k1 --csalad "$f:$PP/l${SRC}_${f}_$SRC.json:$D/items:$G/kinyert_$SRC:$G/orakulum_$SRC" --cal "$f:cache/k08/pecset/pontoz/lG2F_${f}_CAL.json" \
  --fo-par L-RN,L-S --tau kor08/eredmenyek/G5/k3/g5_k3.json --reps "$REPS" --cimke "N, a minimális párok" --out "$O/k1" >> "$R/k1.log" 2>&1 || fail "K1"
py "${J[@]}" szoveg >> "$R/k1.log" 2>&1 || fail "szöveges modellek"
sha256sum "$O"/k1/*.json > "$R/k1.sha256"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
