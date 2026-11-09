#!/usr/bin/env bash
# K08G2 — a G2 generálása (G1-rögzítés 5.; `szint08`): a friss sablonok (a hibaelhárítás okkatalógusai a Muse-tól),
# a tervek, a generálás és a tényellenőrzés a négy részre (friss CAL / TESZT, K3-típus, értelmezési teszt és
# tanítóminta), utána a Gemma-triage kiolvasása (a 03 `kiolvaso03` ids-módja, gold és item-id nélkül, négy sorrend).
# **Csak a rögzítés után és Dani jóváhagyásával indul:** a D12 manifestje (`kor08/rogzites/D12/manifest.json`) és a
# forgatókönyvek jóváhagyása (`kor08/adat/G2/FORGATOKONYV-JOVAHAGYVA`, Dani átnézése után) nélkül nem fut. A G2 egyszer
# készül: a kész G2 (`DONE-K08G2`) után nem indul újra; technikai megszakadás után ugyanazt folytatja (11-04): a hiba
# katalógusa a részeredményből, a terv determinisztikus, a `gen` a kész terveket, a Gemma-kiolvasó a kész item–sorrend
# párokat kihagyja, a `final` ugyanazt írja. Egyszerre egy nagy GPU-folyamat: előbb a Muse, utána a Gemma. Az
# összesítés (`gemma08`) és az auditlap (`audit08g2`) helyben, a back08 után. Minden adat szintetikus.
#   setsid nohup kor08/eszkozok/k08g2.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G2"
R="$EXP/logs/k08g2"
mkdir -p "$R"
G2=kor08/adat/G2
O=kor08/eredmenyek/G2/gemma
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
RESZEK=(friss k3 ert_teszt ert_tanito)
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
[ -f "DONE-$FAZIS" ] && { echo "$FAZIS: a G2 már elkészült ($(cat "DONE-$FAZIS")); a G2 egyszer készül" > "FAILED-$FAZIS"; exit 1; }
rm -f "FAILED-$FAZIS"
lep() { echo "[$(date '+%F %T')] $*" >> "$R/lepesek.log"; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
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
[ -f kor08/rogzites/D12/manifest.json ] || { echo "$FAZIS: nincs D12-rögzítés (kor08/rogzites/D12/manifest.json)" > "FAILED-$FAZIS"; exit 1; }
[ -f "$G2/FORGATOKONYV-JOVAHAGYVA" ] || { echo "$FAZIS: a forgatókönyvek nincsenek jóváhagyva ($G2/FORGATOKONYV-JOVAHAGYVA)" > "FAILED-$FAZIS"; exit 1; }
for r in "${RESZEK[@]}"; do
  ls "$G2/$r/raw/"*.jsonl >/dev/null 2>&1 && lep "folytatás: $r-ben már van nyers generálás (a kész tervek kimaradnak)"
done
python3 kor08/eszkozok/forgatokonyv08_szab.py ellenoriz > "$R/forgatokonyv.log" 2>&1 || fail "a forgatókönyvek szerkezeti ellenőrzése"
lep "várakozás, amíg más fázis vagy konténer fut"
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- 1. Muse: a sablonok, a tervek és a generálás ----------------------------------------------------------------------
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
  say "sablonok: $f" 1800
  lep "sablon $f"
  cpy kor08/eszkozok/szint08.py sablon --csalad "$f" "${MUSE[@]}" --workers 16 >> "$R/sablon_$f.log" 2>&1 || fail "sablon $f"
  for r in "${RESZEK[@]}"; do
    say "$r: $f (terv, generálás, tényellenőrzés)" 3600
    lep "$r $f"
    cpy kor08/eszkozok/szint08.py terv --csalad "$f" --resz "$r" >> "$R/${r}_$f.log" 2>&1 || fail "terv $r $f"
    cpy kor08/eszkozok/szint08.py gen --csalad "$f" --resz "$r" "${MUSE[@]}" --workers 64 >> "$R/${r}_$f.log" 2>&1 || fail "gen $r $f"
    cpy kor08/eszkozok/szint08.py final --csalad "$f" --resz "$r" >> "$R/${r}_$f.log" 2>&1 || fail "final $r $f"
  done
done
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
lep "Muse leállt"
sleep 30

# --- 2. Gemma-triage: minden G2-item, négy sorrend ------------------------------------------------------------------------
GEMMA_SNAP="/hfg/models--google--gemma-4-26B-A4B-it/snapshots/$(basename "$(ls -d "$HOME"/hf-cache-gemma4/models--google--gemma-4-26B-A4B-it/snapshots/* | head -1)")"
kpy() {  # a kiolvasó a vLLM-image-ben, a saját uid-del, a Gemma-tokenizerrel (/hfg)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -v "$HOME/hf-cache-gemma4:/hfg:ro" \
    -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
mkdir -p "$O"
say "Gemma indul" 1500
lep "Gemma indul"
[ "$(free -g | awk 'NR==2{print $7}')" -lt 80 ] && fail "kevés szabad memória a Gemma indításához"
docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
  -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
  --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 48 --max-logprobs 64 \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Gemma docker run"
varj ldh-gemma4 8440 || fail "a Gemma nem állt fel"
memoria_or ldh-gemma4
for r in "${RESZEK[@]}"; do
  say "Gemma-ítélet: $r" 2400
  lep "Gemma $r"
  kpy kor03/eszkozok/kiolvaso03.py --items "$G2/$r/items/penzugy.bankparositas.jsonl" "$G2/$r/items/muszaki.hibaelharitas.jsonl" \
      "$G2/$r/items/szabaly.koltsegelszamolas.jsonl" --out "$O/$r.jsonl" --mode ids --url http://127.0.0.1:8440 \
      --model gemma4-26b --tokenizer "$GEMMA_SNAP" --perms 0,1,2,3 --concurrency 48 >> "$R/gemma.log" 2>&1 || fail "Gemma $r"
done
docker logs ldh-gemma4 > "$R/ldh-gemma4.log" 2>&1 || true
docker rm -f ldh-gemma4 >/dev/null 2>&1 || true
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
