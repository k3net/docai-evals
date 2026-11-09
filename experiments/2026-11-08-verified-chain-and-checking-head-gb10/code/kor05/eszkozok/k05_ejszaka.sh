#!/usr/bin/env bash
# K05EJ — éjszakai lánc a laptop nélkül (05-runbook 10. pont F2–F3, Napló 2026-10-28 este):
#   párhuzamosan  a JEV-35B letöltése rögzített revízióval, méret- és sha256-ellenőrzéssel (hálózat, GPU nélkül)
#   1. megvárja a K05F2A-t; ha elbukott vagy nyom nélkül leállt, egyszer újraindítja (a kész shardok kimaradnak)
#   2. K05FEJ: a C, H és A tartalmi fej a D_fit → D_dev jellemzőin, jóslat a nem kitartott szeleteken (GPU,
#      HF-modell nélkül); a FEJ_HATARIDO után a még nem indult karok kimaradnak, hogy a K05F2B elférjen
#   3. K05F2B: a kitartott rétegek és a célcsalád-minták kivonása a pecsételt cache/k05/pecset/ alá, előbb a
#      kanonikus, aztán a b1; a végén a sha256-manifest (kor05/rogzites/pecset/K05F2B.json). A pecsétet a v1a
#      nélkül semmi nem olvassa (pecset05.kapu).
# Újraindítható: a kész fej, a kész shard és a kész letöltés kimarad.
#   setsid nohup kor05/eszkozok/k05_ejszaka.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K05EJ
LOG=logs/k05ej.log
FEJ_HATARIDO="${FEJ_HATARIDO:-01:30}"
JELL=cache/k05/jellemzok
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
log() { say "$@" >> "$LOG"; }

# gpu_job NÉV IDŐKORLÁT_S LOG args… — a py --gpu konténere, de névvel és időkorláttal: időtúllépéskor a konténer is
# leáll (a py() kliensének megölése a konténert futva hagyná). A visszatérési érték a konténeré, időtúllépésnél 124.
gpu_job() {
  local name=$1 t=$2 logf=$3 rc lp
  shift 3
  docker rm -f "$name" >/dev/null 2>&1
  docker run -d --gpus all --ipc host --network host --name "$name" \
    -v "$EXP:/exp" -v "$HOME/.cache/huggingface:/hf:ro" -v /etc/localtime:/etc/localtime:ro \
    -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e PYTHONUNBUFFERED=1 \
    -w /exp "$TOOL_IMAGE" python3 "$@" >/dev/null || return 125
  docker logs -f "$name" >> "$logf" 2>&1 &
  lp=$!
  rc=$(timeout "$t" docker wait "$name") || rc=124
  docker rm -f "$name" >/dev/null 2>&1
  wait "$lp" 2>/dev/null
  return "$rc"
}

# --- párhuzamos ág: JEV-35B --------------------------------------------------------------------------------------
jev_letoltes() {
  [ -f DONE-K05JEV ] && return 0
  rm -f FAILED-K05JEV
  mkdir -p "$HOME/hf-cache-jev"
  local n
  for n in 1 2 3; do
    echo "[$(date '+%F %T')] JEV-letöltés, $n. kísérlet" >> logs/k05ej_jev.log
    docker rm -f k05-jev-letoltes >/dev/null 2>&1
    if docker run --rm --name k05-jev-letoltes --cpus 4 --memory 12g --network host \
        -v "$EXP:/exp" -v "$HOME/hf-cache-jev:/hf" -v /etc/localtime:/etc/localtime:ro \
        -e HF_HOME=/hf -e HF_HUB_DISABLE_TELEMETRY=1 -e HF_HUB_DISABLE_PROGRESS_BARS=1 -e PYTHONUNBUFFERED=1 \
        -w /exp "$TOOL_IMAGE" python3 kor05/eszkozok/jev_letolt05.py --varhato kor05/adat/jev_varhato.json \
        --out kor05/eredmenyek/F2/jev_letoltes.json >> logs/k05ej_jev.log 2>&1; then
      date '+%F %T' > DONE-K05JEV
      return 0
    fi
    sleep 300
  done
  echo "3 kísérlet után sem sikerült $(date '+%F %T')" > FAILED-K05JEV
}
jev_letoltes &
JEV_PID=$!

# --- 1. K05F2A ---------------------------------------------------------------------------------------------------
while pgrep -f k05f2a_vezenylo.sh >/dev/null; do
  log "1/3 a K05F2A-ra várok — $(cat STATUS-K05F2A 2>/dev/null)"
  sleep 120
done
if [ ! -f DONE-K05F2A ]; then
  log "1/3 a K05F2A nem végzett ($(cat FAILED-K05F2A 2>/dev/null || echo 'nyom nélkül')); újraindítás"
  kor05/eszkozok/k05f2a_vezenylo.sh
fi
# az AKTIV_FAZIS-t a K05F2A vége törli, ezért csak utána írjuk
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
[ -f DONE-K05F2A ] && log "1/3 K05F2A kész ($(cat DONE-K05F2A))" || log "1/3 a K05F2A másodszor sem végzett — a fejek csak a kész szeleteken"

# --- 2. K05FEJ ---------------------------------------------------------------------------------------------------
lejart() { [ "$(date +%H%M)" -ge "${FEJ_HATARIDO/:/}" ] && [ "$(date +%H%M)" -lt 1200 ]; }
for k in C H A; do
  out=cache/k05/fejek/$k
  if [ ! -f "$out/fej.json" ]; then
    if lejart; then log "2/3 fej $k: a határidő ($FEJ_HATARIDO) után nem indul"; continue; fi
    if [ ! -f "$JELL/D_fit__fit/osszegzes.json" ] || [ ! -f "$JELL/D_dev__kanonikus/osszegzes.json" ]; then
      log "2/3 fej $k: a D_fit vagy a D_dev jellemzői hiányosak"; continue
    fi
    log "2/3 fej $k tanítása (D_fit → D_dev, 2 LR × 3 seed)" 3600
    gpu_job ldh-k05-fej-$k 3600 logs/k05fej.log kor05/eszkozok/fej05.py tanit --kar "$k" \
      --fit "$JELL/D_fit__fit" --dev "$JELL/D_dev__kanonikus" --out "$out"
    rc=$?
    if [ "$rc" -ne 0 ] || [ ! -f "$out/fej.json" ]; then log "2/3 fej $k: HIBA (rc=$rc)"; continue; fi
  fi
  for s in D_dev D_meta D_cal_prob D_cal_policy; do
    p=cache/k05/predikciok/$k/$s
    [ -f "$p/fej_s73.jsonl" ] && continue
    [ -f "$JELL/${s}__kanonikus/osszegzes.json" ] || { log "2/3 jóslat $k/$s: a jellemzők hiányosak"; continue; }
    log "2/3 jóslat $k → $s"
    gpu_job ldh-k05-josol-$k 1800 logs/k05fej.log kor05/eszkozok/fej05.py josol --fej "$out" \
      --be "$JELL/${s}__kanonikus" --out "$p" || log "2/3 jóslat $k/$s: HIBA"
  done
  mkdir -p "kor05/eredmenyek/F3/fejek/$k" "kor05/eredmenyek/F3/predikciok/$k"
  cp "$out/fej.json" "kor05/eredmenyek/F3/fejek/$k/" 2>/dev/null
  [ -d "cache/k05/predikciok/$k/D_dev" ] && cp -r "cache/k05/predikciok/$k/D_dev" "kor05/eredmenyek/F3/predikciok/$k/"
done

# --- 3. K05F2B (pecsételve) --------------------------------------------------------------------------------------
FEL=(teszt:ho-termek:kanonikus teszt:ho-routing:kanonikus teszt:ho-routing-hu:kanonikus teszt:ho-uj:kanonikus
     cel:ho-termek:kanonikus cel:ho-routing:kanonikus cel:ho-uj:kanonikus
     cel:ho-termek:b1 cel:ho-routing:b1 cel:ho-uj:b1
     teszt:ho-termek:b1 teszt:ho-routing:b1 teszt:ho-routing-hu:b1 teszt:ho-uj:b1
     leiro:t-hu-maradek:kanonikus leiro:t-hu-maradek:b1)
args=()
for f in "${FEL[@]}"; do args+=(--feladat "$f"); done
py kor05/eszkozok/pecset05.py nyit >> "$LOG" 2>&1
rm -f FAILED-K05F2B DONE-K05F2B
for n in 1 2; do
  log "3/3 K05F2B, $n. futás (76 536 forward; az állapot: STATUS-K05F2B)"
  gpu_job ldh-k05-f2b 43200 logs/k05f2b.log kor05/eszkozok/hf_jellemzo05.py kivon "${args[@]}" \
    --out-root cache/k05/pecset/jellemzok --status STATUS-K05F2B
  rc=$?
  [ "$rc" -eq 0 ] && { date '+%F %T' > DONE-K05F2B; break; }
  echo "rc=$rc $(date '+%F %T')" > FAILED-K05F2B
done
py kor05/eszkozok/pecset05.py lezar --fazis K05F2B >> "$LOG" 2>&1
log "3/3 K05F2B: $( [ -f DONE-K05F2B ] && echo kész || echo "nem teljes ($(cat FAILED-K05F2B))"), pecsét lezárva"

log "a JEV-letöltésre várok"
wait "$JEV_PID"
log "lánc vége — F2A: $( [ -f DONE-K05F2A ] && echo kész || echo HIBA) · fejek: $(ls kor05/eredmenyek/F3/fejek/*/fej.json 2>/dev/null | wc -l)/3 · F2B: $( [ -f DONE-K05F2B ] && echo kész || echo HIBA) · JEV: $( [ -f DONE-K05JEV ] && echo kész || echo HIBA)"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
