#!/usr/bin/env bash
# K08J — a javító kör (J-rögzítés): friss K3-típusú minta (Muse), kinyerés az alannyal (egyszer, a rögzített kinyerővel), a lánc
# három úton (javított, rögzített, orákulum), kiolvasás R-módban (a `k08g3c.sh` mintájára: a mód a folyamat elején, a
# referenciaszeleten dől el), a K2 a rögzített `g5_k2_08`-cal. Fejet nem tanít. **Csak a J rögzítése után fut**, a K08JP próba
# kivételével (`J_PROBA=1`: a meglévő K3-itemek kis másolatán, generálás nélkül, külön gyökérben).
#   setsid nohup kor08/eszkozok/k08j.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
source kor07/eszkozok/lib07.sh
export PATH="$EXP/kor08/eszkozok/burok_g3:$PATH"
if [ "${J_PROBA:-0}" = 1 ]; then
  FAZIS="K08JP"; D=kor08/adat/Jproba; C=cache/k08/jproba; O=kor08/eredmenyek/Jproba; R="$EXP/logs/k08jp"; REPS=200
else
  FAZIS="K08J"; D=kor08/adat/J; C=cache/k08/j; O=kor08/eredmenyek/J; R="$EXP/logs/k08j"; REPS=10000
fi
mkdir -p "$R"
J=(kor08/eszkozok/j08.py --gyoker "$D")
G="$D/G3"
K="$G/kinyeres"
JJ="$C/jellemzok"
PP="$C/pontoz"
ALANY=ldh-alany08
SRC=J1K3
PROBA=6
DETD=det0_szabaly.koltsegelszamolas_T500__kanonikus
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
declare -A SEMA=([penzugy.bankparositas]=1 [muszaki.hibaelharitas]=1 [szabaly.koltsegelszamolas]=2)
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
L="$R/lepesek.log"
lep() { echo "[$(date '+%F %T')] $*" >> "$L"; }
kapu() { lep "KAPU: $*"; echo "[$(date '+%F %T')] $FAZIS: $*" > "FAILED-$FAZIS"; exit 1; }
konti() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "$1"; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 -e J_GYOKER="$D" "$SUBJECT_IMAGE" "$@"
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
if [ "${J_PROBA:-0}" != 1 ]; then
  [ -f kor08/rogzites/J/manifest.json ] || kapu "nincs J-rögzítés (kor08/rogzites/J/manifest.json)"
  python3 kor08/eszkozok/j08.py ellenoriz >> "$L" 2>&1 || kapu "a J rögzítése nem zöld"
fi
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

# --- 1. a friss minta (Muse) -----------------------------------------------------------------------------------------------
if [ "${J_PROBA:-0}" != 1 ]; then
  say "Muse indul" 900
  lep "Muse indul"
  docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
    -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
    "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
    --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
    --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
    --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "a Muse nem indult"
  varj ldh-muse 8450 || fail "a Muse nem állt fel"
  memoria_or ldh-muse
  for f in "${CSALADOK_08[@]}"; do
    say "minta: $f (sablon, terv, generálás, tényellenőrzés)" 3000
    lep "minta $f"
    cpy kor08/eszkozok/szint08j.py sablon --csalad "$f" "${MUSE[@]}" --workers 16 >> "$R/minta_$f.log" 2>&1 || fail "sablon $f"
    cpy kor08/eszkozok/szint08j.py terv --csalad "$f" --resz k3 >> "$R/minta_$f.log" 2>&1 || fail "terv $f"
    cpy kor08/eszkozok/szint08j.py gen --csalad "$f" --resz k3 "${MUSE[@]}" --workers 64 >> "$R/minta_$f.log" 2>&1 || fail "gen $f"
    cpy kor08/eszkozok/szint08j.py final --csalad "$f" --resz k3 >> "$R/minta_$f.log" 2>&1 || fail "final $f"
  done
  docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
  docker rm -f ldh-muse >/dev/null 2>&1 || true
  lep "Muse leállt"
  python3 "${J[@]}" minta > "$R/minta.log" 2>&1 || fail "a minta nem diszjunkt"
  sha256sum "$D"/k3/terv/*.jsonl "$D"/k3/items/*.jsonl > "$R/minta.sha256"
  sleep 30
fi

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
  python3 "${J[@]}" lanc futtat --forras "$SRC" --csalad "$f" --ut kinyert --blokk v4 --kinyeres "$K/${SRC}_$f.mezok.jsonl" \
    --out "$G/kinyert_$SRC" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $f"
  python3 "${J[@]}" lanc0 futtat --forras "$SRC" --csalad "$f" --ut kinyert --blokk v4 --kinyeres "$K/${SRC}_$f.mezok.jsonl" \
    --out "$G/rogzitett_$SRC" >> "$R/lanc.log" 2>&1 || fail "lánc rögzített $f"
  python3 "${J[@]}" lanc0 futtat --forras "$SRC" --csalad "$f" --ut orakulum --blokk v4 \
    --out "$G/orakulum_$SRC" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $f"
done
find "$G"/kinyert_* "$G"/rogzitett_* "$G"/orakulum_* -type f | sort | xargs sha256sum > "$R/lanc.sha256"

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
  for m in kanonikus b1; do
    for e in n l r o; do fel+=(--feladat "$e$SRC:$f:$SRC:$m"); done
  done
done
say "kiolvasás R-módban" 3600
kiolvas_r "$JJ" "$C/arch" "${fel[@]}"

# --- 5. pontozás és a K2 ---------------------------------------------------------------------------------------------------------
say "pontozás" 600
lep "pontozás"
for f in "${CSALADOK_08[@]}"; do
  for e in n l r o; do
    py "${J[@]}" b1rel pontoz --szelet "$e${SRC}_${f}_$SRC" --jell "$JJ" --lanc-nelkul --out "$PP" --szalak 16 >> "$R/pontoz.log" 2>&1 \
      || fail "pontozás $e $f"
  done
done
say "K2" 600
lep "K2"
mkdir -p "$O"
for x in "kinyert:l:k2:J, a javított lánc" "rogzitett:r:k2_rogzitett:J, a rögzített lánc ugyanazon a kinyerésen"; do
  IFS=: read -r d e o c <<< "$x"
  py "${J[@]}" k2 --forras "$SRC" --nelkul "$PP/n${SRC}_{csalad}_$SRC.json" --kinyert "$G/${d}_$SRC:$PP/$e${SRC}_{csalad}_$SRC.json" \
    --orakulum "$G/orakulum_$SRC:$PP/o${SRC}_{csalad}_$SRC.json" --reps "$REPS" --cimke "$c" --out "$O/$o" >> "$R/k2.log" 2>&1 || fail "K2 $o"
done
sha256sum "$O"/*/*.json > "$R/k2.sha256"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
