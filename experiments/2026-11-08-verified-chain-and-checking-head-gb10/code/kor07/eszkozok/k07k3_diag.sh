#!/usr/bin/env bash
# K07K3 — a végső diagnosztikai minta (07-runbook 3.3, D6, D11; K3): a 3. kör rögzített konstrukciója a 07 friss
# TESZT-sablonjain (`szint07diag`; családonként 200 terv), egyszer. Terv és önteszt (CPU), szövegek a Muse-zal, `final`,
# majd a kiolvasás mindkét kerettel a K3 pecsétje alá (`kiolvas07diag`, `cache/k07/pecset_k3`), és a pecsét lezárása
# (`pecset07k3 lezar --fazis K07K3`). Csak a K3 elemzőjének rögzítése után indul (`kor07/rogzites/k3/ROGZITES.json`).
# A pecsét a `rogzit07k3 nyit`-tal nyílik, Dani jóváhagyásával; utána `b1rel07k3 pontoz` és `k3_07 elemez`.
#   setsid nohup kor07/eszkozok/k07k3_diag.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K07K3"
R="$EXP/logs/k07k3"
mkdir -p "$R"
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
CSALADOK=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
ldh_cleanup() {
  docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true
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

# az őrök nem a `fail`-lel lépnek ki: az törölné a másik fázis AKTIV_FAZIS-át és leállítaná a Muse-konténert
if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
if [ ! -f kor07/rogzites/k3/ROGZITES.json ]; then echo "$FAZIS: a K3 elemzője nincs rögzítve, nem indul" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

say "terv és önteszt (3 család, végső diagnosztikai minta)"
cpy kor07/eszkozok/szint07diag.py onteszt >> "$R/onteszt.log" 2>&1 || fail "a tényellenőrző öntesztje"
for f in "${CSALADOK[@]}"; do
  cpy kor07/eszkozok/szint07diag.py terv --csalad "$f" >> "$R/$f.log" 2>&1 || fail "terv: $f"
done
say "Muse indul" 900
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "Muse docker run"
varj ldh-muse 8450
memoria_or ldh-muse
for f in "${CSALADOK[@]}"; do
  say "generálás: $f" 600
  cpy kor07/eszkozok/szint07diag.py gen --csalad "$f" "${MUSE[@]}" --workers 64 >> "$R/$f.log" 2>&1 || fail "gen: $f"
  cpy kor07/eszkozok/szint07diag.py final --csalad "$f" >> "$R/$f.log" 2>&1 || fail "final: $f"
done
ldh_cleanup
sleep 20

feladat=()
for f in "${CSALADOK[@]}"; do
  for m in kanonikus b1; do feladat+=(--feladat "$f:DIAG:$m"); done
done
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
py kor07/eszkozok/pecset07k3.py nyit >> "$R/pecset.log" 2>&1 || fail "a pecsétkönyvtár"
say "kiolvasás a pecsét alá, négyállapotú keret" 2700
memoria_or07 "$R/memoria4.log"
py07 kor07/eszkozok/kiolvas07diag.py kivon "${feladat[@]}" --out-root cache/k07/pecset_k3/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas4.log" 2>&1 || fail "kiolvasás (4)"
sleep 20
say "kiolvasás a pecsét alá, 06-os kétkimenetű keret" 2700
memoria_or07 "$R/memoria2.log"
py07 kor07/eszkozok/kiolvas07diag.py kivon --keret 2 "${feladat[@]}" --out-root cache/k07/pecset_k3/jellemzok2 --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas2.log" 2>&1 || fail "kiolvasás (2)"
py kor07/eszkozok/pecset07k3.py lezar --fazis K07K3 >> "$R/pecset.log" 2>&1 || fail "a pecsét lezárása"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
