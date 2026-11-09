#!/usr/bin/env bash
# K06F2K — a bankcsalád javítása a 2. audit után (D21–D22, Dani, 2026-10-31), utána a bank újrakiolvasása (K06F3C) és a
# Gemma-ítélet a bankon:
#   1. sablon + terv (D21: a közös összegű számlapár azonos esedékességgel), `ujraterv` (D22: a szigorúbb
#      tényellenőrzésen elbukó szövegek kiesnek), a Muse csak ezekhez, `final`
#   2. a bank régi kiolvasása archívumba (`archiv_v2`; a pecsét alatti a pecsét alatt marad)
#   3. K06F3C: a kiolvasás (a kész hibaelhárítási és szabálycsaládi shardok kimaradnak), új manifest
#   4. a Gemma a bank 2000 itemjén, négy sorrendben (az összesítés helyben)
#   setsid nohup kor06/eszkozok/k06f2_bank.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F2K
R="$EXP/logs/k06f2k"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
B=penzugy.bankparositas
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
GEMMA_SNAP="/hfg/models--google--gemma-4-26B-A4B-it/snapshots/$(basename "$(ls -d "$HOME"/hf-cache-gemma4/models--google--gemma-4-26B-A4B-it/snapshots/* | head -1)")"
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
kpy() {  # a kiolvasó a Gemma-tokenizerrel (/hfg)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -v "$HOME/hf-cache-gemma4:/hfg:ro" \
    -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() {
  for c in ldh-muse ldh-gemma4; do docker logs "$c" > "$R/$c.log" 2>&1 || true; docker rm -f "$c" >/dev/null 2>&1 || true; done
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
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" != "true" ] && fail "$1 kilépett"
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && fail "memória < 15 GB a(z) $1 betöltése alatt"
    [ $(( $(date +%s) - t0 )) -gt 2700 ] && fail "$1 45 perc alatt sem állt fel"
    sleep 15
  done
}
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 100 ] && fail "kevés szabad memória a Muse indításához"
cp "kor06/adat/f2/items/$B.jsonl" "$R/$B.items-elotte.jsonl"

say "bank: sablon, terv, újratervezés (D21–D22)"
cpy kor06/eszkozok/szint06.py sablon --csalad "$B" >> "$R/$B.log" 2>&1 || fail "sablon"
cpy kor06/eszkozok/szint06.py terv --csalad "$B" >> "$R/$B.log" 2>&1 || fail "terv"
cpy kor06/eszkozok/szint06.py ujraterv --csalad "$B" >> "$R/$B.log" 2>&1 || fail "ujraterv"

say "Muse indul (a kiesett banki szövegekhez)" 1500
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Muse docker run"
varj ldh-muse 8450
memoria_or ldh-muse
say "bank: generálás, final"
cpy kor06/eszkozok/szint06.py gen --csalad "$B" "${MUSE[@]}" --workers 64 >> "$R/$B.log" 2>&1 || fail "gen"
cpy kor06/eszkozok/szint06.py final --csalad "$B" >> "$R/$B.log" 2>&1 || fail "final"
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
python3 - "$R/$B.items-elotte.jsonl" "kor06/adat/f2/items/$B.jsonl" >> "$R/osszefoglalo.log" 2>&1 <<'EOF' || fail "az összevetés hibát adott"
import json, sys
a = {json.loads(l)["id"]: json.loads(l) for l in open(sys.argv[1])}
b = {json.loads(l)["id"]: json.loads(l) for l in open(sys.argv[2])}
print("item:", len(b), "· azonos id-k:", set(a) == set(b), "· új szöveg:", sum(a[i]["state"] != b[i]["state"] for i in a if i in b),
      "· új opciószöveg:", sum(a[i]["options"] != b[i]["options"] for i in a if i in b))
EOF

say "a bank régi kiolvasása archívumba"
py -c "
import shutil
from pathlib import Path
for src, dst in (('cache/k06/jellemzok', 'cache/k06/archiv_v2/jellemzok'), ('cache/k06/pecset/jellemzok', 'cache/k06/pecset/archiv_v2/jellemzok')):
    Path(dst).mkdir(parents=True, exist_ok=True)
    for d in sorted(Path(src).glob('$B*')):
        shutil.move(str(d), str(Path(dst) / d.name))
        print('archívum:', d, '->', dst)
" >> "$R/archiv.log" 2>&1 || fail "archiválás"

say "K06F3C: a bank újrakiolvasása" 4200
FAZIS=K06F3C kor06/eszkozok/k06f3_kiolvas.sh
[ -f DONE-K06F3C ] || fail "K06F3C: $(cat FAILED-K06F3C 2>/dev/null)"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS

say "Gemma indul (a bank 2000 itemje)" 1500
docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
  -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
  --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 48 --max-logprobs 64 \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Gemma docker run"
varj ldh-gemma4 8440
memoria_or ldh-gemma4
kpy kor03/eszkozok/kiolvaso03.py --items "kor06/adat/f2/items/$B.jsonl" --out kor06/eredmenyek/F2/gemma/gemma_f2_bank_v2.jsonl \
  --mode ids --url http://127.0.0.1:8440 --model gemma4-26b --tokenizer "$GEMMA_SNAP" --perms 0,1,2,3 --concurrency 48 \
  >> "$R/gemma.log" 2>&1 || fail "Gemma-kiolvasás"
ldh_cleanup
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
