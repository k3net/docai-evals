#!/usr/bin/env bash
# K06F2J — az első címkeaudit (D14) leleteinek javítása (D18–D19, Dani, 2026-10-30), utána a bank- és a szabálycsalád
# újrakiolvasása (K06F3B) és a második audit mintája (a két családra friss 100-100 item). A K06F3H után indul.
#   1. szabálycsalád: sablon + terv az új szövegekkel (D18: „domestic”, „client” ki; D19: a szerverbeszerzés helyett
#      lakcímváltozás), `ujraterv` (a meglévő szöveg marad, ahol csak az opciószöveg változott), a 65 új OUT_OF_SCOPE
#      szöveg generálása a Muse-zal, `final`
#   2. bank: `final` (D19: „Számlatulajdonos: …” első sor; a szöveg és a válogatás nem változik)
#   3. a két család régi kiolvasása archívumba (a pecsét alatti a pecsét alatt marad), a második audit mintája
#   4. K06F3B: a két család kiolvasása elölről (a hibaelhárítás kész shardjai kimaradnak), a manifest
#   setsid nohup kor06/eszkozok/k06f2_javitas.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K06F2J
R="$EXP/logs/k06f2j"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
F=szabaly.koltsegelszamolas
B=penzugy.bankparositas
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() { docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true; }
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"

say "vár a hibaelhárítás kiolvasására (K06F3H)"
until [ -f DONE-K06F3H ] || [ -f FAILED-K06F3H ]; do sleep 30; done
[ -f FAILED-K06F3H ] && echo "a K06F3H hibával állt le: $(cat FAILED-K06F3H)" >> "$R/osszefoglalo.log"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
docker ps --format '{{.Names}}' | grep -q . && fail "fut egy konténer; egyszerre egy nagy GPU-folyamat"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 100 ] && fail "kevés szabad memória a Muse indításához"

say "szabálycsalád: új sablon, terv, újratervezés"
cpy kor06/eszkozok/szint06.py sablon --csalad "$F" >> "$R/$F.log" 2>&1 || fail "sablon"
cpy kor06/eszkozok/szint06.py terv --csalad "$F" >> "$R/$F.log" 2>&1 || fail "terv"
cpy kor06/eszkozok/szint06.py ujraterv --csalad "$F" >> "$R/$F.log" 2>&1 || fail "ujraterv"

say "Muse indul (a szabálycsalád új szövegeihez)" 1500
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
( while docker inspect -f '{{.State.Running}}' ldh-muse 2>/dev/null | grep -q true; do
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T')" >> "$R/memoria.log"; docker rm -f ldh-muse; }
    sleep 30
  done ) &
say "szabálycsalád: generálás"
cpy kor06/eszkozok/szint06.py gen --csalad "$F" "${MUSE[@]}" --workers 64 >> "$R/$F.log" 2>&1 || fail "gen"
cpy kor06/eszkozok/szint06.py final --csalad "$F" >> "$R/$F.log" 2>&1 || fail "final"
for k in 1 2; do
  python3 -c "import json,sys; r=json.load(open('kor06/adat/f2/items/$F.osszesito.json')); sys.exit(0 if r['hianyzo_cellak'] else 1)" || break
  cp "kor06/adat/f2/items/$F.osszesito.json" "kor06/adat/f2/items/$F.osszesito.javitas$(( k - 1 )).json"
  cpy kor06/eszkozok/szint06.py terv --csalad "$F" --potlas "$k" >> "$R/$F.log" 2>&1 || fail "pótlás-terv $k"
  say "pótlókör $k" 900
  cpy kor06/eszkozok/szint06.py gen --csalad "$F" "${MUSE[@]}" --workers 64 >> "$R/$F.log" 2>&1 || fail "pótlás-gen $k"
  cpy kor06/eszkozok/szint06.py final --csalad "$F" >> "$R/$F.log" 2>&1 || fail "pótlás-final $k"
done
ldh_cleanup

say "bank: számlatulajdonos-sor"
cpy kor06/eszkozok/szint06.py final --csalad "$B" >> "$R/$B.log" 2>&1 || fail "bank final"
for f in "$B" "$F"; do
  python3 -c "import json; r=json.load(open('kor06/adat/f2/items/$f.osszesito.json')); print('$f', r['item'], 'item;', 'hiányzó cellák:', r['hianyzo_cellak'] or 'nincs')" \
    >> "$R/osszefoglalo.log"
done

say "a régi kiolvasás archívumba; a második audit mintája"
py -c "
import shutil
from pathlib import Path
for src, dst in (('cache/k06/jellemzok', 'cache/k06/archiv_v1/jellemzok'), ('cache/k06/pecset/jellemzok', 'cache/k06/pecset/archiv_v1/jellemzok')):
    Path(dst).mkdir(parents=True, exist_ok=True)
    for d in sorted(Path(src).glob('*')):
        if d.name.startswith(('$B', '$F')):
            shutil.move(str(d), str(Path(dst) / d.name))
            print('archívum:', d, '->', dst)
" >> "$R/archiv.log" 2>&1 || fail "archiválás"
cpy kor06/eszkozok/szint06.py audit --kor 2 --csalad "$B" "$F" >> "$R/audit.log" 2>&1 || fail "audit (2. kör)"

say "K06F3B: a bank- és a szabálycsalád újrakiolvasása" 6600
FAZIS=K06F3B kor06/eszkozok/k06f3_kiolvas.sh
[ -f DONE-K06F3B ] || fail "K06F3B: $(cat FAILED-K06F3B 2>/dev/null)"
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
