#!/usr/bin/env bash
# K05JEV — a JEV-35B smoke-ja és kiolvasása (05-runbook 3.4, 8.3; 04-runbook 3.1):
#   0. megvárja az éjszakai láncot (k05_ejszaka.sh): a HF-bázis mellett nem fut vLLM (12. pont)
#   1. a JEV a repó saját szerverével (serve_decide.py, a serve.sh kapcsolóival; max-model-len 16384, GPU-memória 0,65 (mellette CPU-n a fejek),
#      kép nélkül), port 8410
#   2. smoke (`jev05.py smoke`): a címketokenek, a repó /v1/decide-ja és a mi kiolvasásunk egyezése, a két kiolvasási út,
#      a README példája; ha elbukik, a kiolvasás nem indul
#   3. kiolvasás, JEV-a és JEV-b, perm 0–3: a D_dev, a D_cal_prob és a D_cal_policy (cache/k05/jev/), majd a négy
#      HO-teszt a pecsét alá (cache/k05/pecset/jev/), a végén a pecsét manifestje (K05JEV.json)
#   setsid nohup kor05/eszkozok/k05jev_vezenylo.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K05JEV
LOG=logs/k05jev.log
PORT=8410
SNAP=/hfjev/hub/models--autotrust--JEV-35B/snapshots/a5d0d580bb9324f0f4c07dcba5c5ca91e813e7c9
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
log() { say "$@" >> "$LOG"; }
bukik() { log "HIBA: $*"; echo "[$(date '+%F %T')] $*" > "FAILED-$FAZIS"; jev_stop; rm -f AKTIV_FAZIS; exit 1; }
jev_stop() { docker logs ldh-jev > logs/k05jev_vllm.log 2>&1; docker rm -f ldh-jev >/dev/null 2>&1; }
# a kliens a tréning-image-ben: /exp, a JEV-cache csak olvasásra (a tokenizerhez és a fej bias-ához)
cpy() {
  docker run --rm --network host --name "ldh-jevc-$$-$RANDOM" -v "$EXP:/exp" -v "$HOME/hf-cache-jev:/hfjev:ro" \
    -v /etc/localtime:/etc/localtime:ro -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e PYTHONUNBUFFERED=1 -w /exp \
    "$TOOL_IMAGE" python3 "$@"
}

while pgrep -f k05_ejszaka.sh >/dev/null; do
  log "0/3 az éjszakai láncra várok — $(cat STATUS-K05F2B 2>/dev/null)"
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
[ -f DONE-K05F2B ] || log "0/3 figyelem: a K05F2B nem teljes ($(cat FAILED-K05F2B 2>/dev/null))"

log "1/3 a JEV indul (vLLM v0.30.0, serve_decide.py)" 900
docker rm -f ldh-jev >/dev/null 2>&1
docker run -d --name ldh-jev --gpus all --ipc host -p "$PORT:8000" -v "$HOME/hf-cache-jev:/hfjev:ro" \
  -e HF_HUB_OFFLINE=1 -e JEV_DECIDE_MERGED_HEAD="$SNAP/adapter_vllm/decision_head.json" -e JEV_DECIDE_SYSTEM2=0 \
  --entrypoint python3 "$SUBJECT_IMAGE" "$SNAP/serve_decide.py" --model "$SNAP" --served-model-name autotrust/JEV-35B \
  --logprobs-mode processed_logprobs --max-logprobs 256 --max-model-len 16384 --enable-prefix-caching \
  --mamba-cache-mode align --max-num-seqs 64 --trust-request-chat-template --limit-mm-per-prompt '{"image": 0}' \
  --gpu-memory-utilization 0.65 --port 8000 >/dev/null || bukik "a konténer nem indult"
SUBJECT_PORT=$PORT subject_wait ldh-jev 1800
case $? in 1) bukik "a vLLM kilépett (logs/k05jev_vllm.log)";; 2) bukik "a vLLM 30 perc alatt sem lett egészséges";; esac
log "1/3 a JEV fut; szabad memória: $(free -g | awk '/Mem/ {print $7}') GB"

log "2/3 smoke"
cpy kor05/eszkozok/jev05.py smoke --url "http://127.0.0.1:$PORT" --out kor05/eredmenyek/F0/jev_smoke >> "$LOG" 2>&1 \
  || bukik "a smoke elbukott (kor05/eredmenyek/F0/jev_smoke/smoke.json)"
log "2/3 a smoke átment"

for s in D_dev D_cal_prob D_cal_policy; do
  log "3/3 kiolvasás: $s (JEV-a/b × perm 0–3)"
  cpy kor05/eszkozok/jev05.py kiolvas --url "http://127.0.0.1:$PORT" --feladat "$s" --out "cache/k05/jev/$s.jsonl" \
    --status "STATUS-$FAZIS-kiolvasas" >> "$LOG" 2>&1 || bukik "kiolvasás: $s"
done
py kor05/eszkozok/pecset05.py nyit >> "$LOG" 2>&1
for s in teszt:ho-termek teszt:ho-routing teszt:ho-routing-hu teszt:ho-uj; do
  log "3/3 kiolvasás a pecsét alá: $s"
  cpy kor05/eszkozok/jev05.py kiolvas --url "http://127.0.0.1:$PORT" --feladat "$s" \
    --out "cache/k05/pecset/jev/${s/:/_}.jsonl" --status "STATUS-$FAZIS-kiolvasas" >> "$LOG" 2>&1 \
    || bukik "kiolvasás: $s"
done
jev_stop
py kor05/eszkozok/pecset05.py lezar --fazis K05JEV >> "$LOG" 2>&1
log "kész; a pecsét lezárva (kor05/rogzites/pecset/K05JEV.json)"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
