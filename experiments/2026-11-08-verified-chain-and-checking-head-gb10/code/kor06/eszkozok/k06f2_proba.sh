#!/usr/bin/env bash
# K06F2P — a friss családok generálási próbája (06-runbook 3.5, D13): családonként 24 item (4 állapot × 2 nyelv × 3),
# Muse-Glimmer-30B rögzített revízióval; a végén a Muse leáll, a próbalap Dani átnézéséhez készül.
#   setsid nohup kor06/eszkozok/k06f2_proba.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F2P
R="$EXP/logs/k06f2p"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
read -r -a CSALADOK <<< "${CSALADOK_ENV:-penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas}"
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
cpy() {  # a kliens a vLLM-image Pythonjával, GPU nélkül, a saját uid-del (a 03 f1_szint.sh mintájára)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() { docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
[ "$(free -g | awk 'NR==2{print $7}')" -lt 100 ] && fail "kevés szabad memória a Muse indításához"
say "Muse indul (revízió ${MUSE_REV:0:8})"
docker rm -f ldh-muse >/dev/null 2>&1 || true
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Muse docker run"
t0=$(date +%s)
until curl -fsS http://127.0.0.1:8450/health >/dev/null 2>&1; do
  [ "$(docker inspect -f '{{.State.Running}}' ldh-muse 2>/dev/null)" != "true" ] && fail "a Muse kilépett"
  [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && fail "memória < 15 GB a Muse betöltése alatt"
  [ $(( $(date +%s) - t0 )) -gt 2700 ] && fail "a Muse 45 perc alatt sem állt fel"
  sleep 15
done
say "Muse kész ($(( $(date +%s) - t0 )) s); próba"
for f in "${CSALADOK[@]}"; do
  if [ "$f" = muszaki.hibaelharitas ]; then
    cpy kor06/eszkozok/szint06.py sablon --csalad "$f" --proba "${MUSE[@]}" --workers 4 >> "$R/$f.log" 2>&1 || fail "sablon $f"
  else
    cpy kor06/eszkozok/szint06.py sablon --csalad "$f" --proba >> "$R/$f.log" 2>&1 || fail "sablon $f"
  fi
  cpy kor06/eszkozok/szint06.py terv --csalad "$f" --proba >> "$R/$f.log" 2>&1 || fail "terv $f"
  cpy kor06/eszkozok/szint06.py gen --csalad "$f" --proba "${MUSE[@]}" --workers 24 >> "$R/$f.log" 2>&1 || fail "gen $f"
  cpy kor06/eszkozok/szint06.py final --csalad "$f" --proba >> "$R/$f.log" 2>&1 || fail "final $f"
  say "kész: $f"
done
cpy kor06/eszkozok/szint06.py lap >> "$R/lap.log" 2>&1 || fail "lap"
ldh_cleanup
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
