#!/usr/bin/env bash
# 03 F2 — negyedik tanárjelölt: Qwen3.8-27B-FP8 (Dani, 2026-10-11: „esetleg keressünk további modellt tanárnak?
# qwen3.8-27B-FP8 esetleg?”). Apache-2.0, dense 27B: a bázis ~3B aktív paraméterének kb. kilencszerese, de a
# tokenizere és az előtanítási vonala közös vele (03-runbook 10. pont 11.). A kapu szabálya változatlan (4.4).
# Ugyanaz a kiolvasás, mint a Gemmánál: nem gondolkodó mód, címketoken-logprob, k = 4 permutáció, a teljes val-on.
#   1. letöltés (GPU nélkül, folytatható)
#   2. smoke: 40 val-item, 0-s permutáció; a címketömeg-medián ≥ 0,9 kell (különben a sablon nem a címkére kérdez)
#   3. val-kiolvasás → kor03/eredmenyek/F2/qwen38_val.jsonl
# A train-kiolvasás csak akkor jön, ha a kapun legalább egy csoportban átmegy (külön döntés).
#   nohup setsid bash kor03/eszkozok/f2_qwen38.sh > logs/f2_qwen38.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=F2T
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F2"
I=kor03/adat/f2
HFC="$HOME/hf-cache-qwen38"
MODEL=Qwen/Qwen3.8-27B-FP8
PORT=8460
mkdir -p "$R" "$HFC"

gpu_containers() {  # csak a GPU-t használó konténer számít
  for c in $(docker ps -q); do [ "$(docker inspect -f '{{len .HostConfig.DeviceRequests}}' "$c")" != "0" ] && echo "$c"; done
}
cpy() {  # CPU-lépés a vLLM-image Pythonjával, GPU nélkül, a Qwen3.8-tokenizerrel (/hfc)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HFC:/hfc:ro" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
q38_start() {
  docker rm -f ldh-qwen38 >/dev/null 2>&1 || true
  docker run -d --name ldh-qwen38 --gpus all -p "$PORT:8000" --ipc host \
    -v "$HFC:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
    "$SUBJECT_IMAGE" --model "$MODEL" --served-model-name qwen38-27b \
    --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 48 --max-logprobs 64 \
    --no-enable-prefix-caching --limit-mm-per-prompt '{"image": 0, "video": 0}' >/dev/null
  local t0; t0=$(date +%s)
  while [ $(( $(date +%s) - t0 )) -lt 2700 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-qwen38 2>/dev/null)" != "true" ] && return 1
    curl -fsS "http://127.0.0.1:$PORT/health" >/dev/null 2>&1 && return 0
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 5 ] && { docker rm -f ldh-qwen38 >/dev/null 2>&1; return 1; }
    sleep 15
  done
  return 2
}
q38_stop() { docker logs ldh-qwen38 > "$R/ldh-qwen38.log" 2>&1 || true; docker rm -f ldh-qwen38 >/dev/null 2>&1 || true; }
olvas() {  # olvas <címke> <itemek> <perms>
  done_marker "olvas-$1" && return 0
  say "kiolvasás: $1 ($(wc -l < "$2") item, perm $3)"
  cpy kor03/eszkozok/kiolvaso03.py --mode ids --items "$2" --out "kor03/eredmenyek/F2/$1.jsonl" --perms "$3" \
    --url "http://127.0.0.1:$PORT" --model qwen38-27b --tokenizer "$SNAP" --concurrency 48 2>&1 \
    | tee -a "$R/olvas-$1.log" | tail -3
  [ "${PIPESTATUS[0]}" = "0" ] || fail "kiolvasás $1"
  mark_ok "olvas-$1"
}

# 1. letöltés
if ! done_marker letoltes; then
  say "letöltés: $MODEL"
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$HFC:/hfc" \
    -e HOME=/tmp -e HF_HOME=/hfc "$SUBJECT_IMAGE" \
    -c "from huggingface_hub import snapshot_download as s; print(s('$MODEL'))" > "$R/letoltes-qwen38.log" 2>&1
  [ "$?" = "0" ] || fail "letöltés (log: $R/letoltes-qwen38.log)"
  mark_ok letoltes
fi
SNAP="/hfc/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots/$(basename "$(ls -d "$HFC"/hub/models--Qwen--Qwen3.8-27B-FP8/snapshots/* | head -1)")"
say "snapshot: $SNAP ($(du -sh "$HFC" | cut -f1))"

# GPU-őr, aztán a szerver
for i in $(seq 1 15); do [ -z "$(gpu_containers)" ] && break; sleep 60; done
for c in $(gpu_containers); do fail "FUT MÁS GPU-KONTÉNER: $(docker inspect -f '{{.Name}}' "$c")"; done
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env
say "Qwen3.8-27B indul"
q38_start || { q38_stop; fail "a Qwen3.8 nem indult (log: $R/ldh-qwen38.log)"; }
say "Qwen3.8-27B fut"

# 2. smoke: 40 item, címketömeg
head -40 "$I/items_val.jsonl" > "$I/items_q38_smoke.jsonl"
olvas qwen38_smoke "$I/items_q38_smoke.jsonl" 0
cpy -c "
import json, statistics
rows = [json.loads(l) for l in open('kor03/eredmenyek/F2/qwen38_smoke.jsonl')]
m = statistics.median(r['label_mass'] for r in rows)
print(f'smoke: {len(rows)} sor, címketömeg-medián {m:.3f}, min {min(r[\"label_mass\"] for r in rows):.3f}')
raise SystemExit(0 if m >= 0.9 else 1)
" 2>&1 | tee -a "$R/olvas-qwen38_smoke.log"
[ "${PIPESTATUS[0]}" = "0" ] || { q38_stop; fail "smoke: a címketömeg-medián 0,9 alatt (a chat-sablon vagy a gondolkodás-kapcsoló gyanús)"; }

# 3. val
olvas qwen38_val "$I/items_val.jsonl" 0,1,2,3
q38_stop
say "F2T kész"
rm -f "$EXP/AKTIV_FAZIS"
touch "$R/DONE-F2T"
