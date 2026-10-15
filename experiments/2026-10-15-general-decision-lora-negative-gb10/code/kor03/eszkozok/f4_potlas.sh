#!/usr/bin/env bash
# K03F4 pótlás — a hiányos F4-kiolvasások kiegészítése (2026-10-14). A `common._keret01` szálverseny miatt (a félkész
# modul a kiolvasó szálai közt) a G3 s1 (5545) és s3 (2206) kiolvasásai a HO-routing 01-es itemein hibával elmaradtak;
# a hibás sor nem kerül a kimenetbe, így a kiolvasó újraindítva csak a hiányzókat olvassa (a javított common.py-jal).
# Megvárja az L0′ végét. Minden F4-karra: ha a kimenet sorszáma < itemek × 4, ugyanazzal az adapterrel és
# itemfájllal újraolvas. A pecsét append-only: a kiegészített fájl új sha256-ja a PECSET.sha256 végére kerül
# (útvonalanként az utolsó sor érvényes). Eredményt nem olvas, csak sorszámot. Idempotens.
#   nohup setsid bash kor03/eszkozok/f4_potlas.sh > logs/k03f4_potlas.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=K03F4-potlas
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F4"
I=kor03/adat/f2
echo "[$(date '+%F %T')] vár az L0′-re"
while [ ! -f DONE-K03F4-l0r ]; do
  for f in FAILED-K03F4-kiolvasas FAILED-K03F4-l0r; do
    [ -f "$f" ] && { echo "[$(date '+%F %T')] $f: a pótlás nem indul"; exit 1; }
  done
  [ -f STOP-K03F4 ] && { echo "[$(date '+%F %T')] STOP-K03F4: kilépek"; exit 0; }
  sleep 120
done
sleep 30
rm -f "$EXP/FAILED-$FAZIS"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env

kpy() {  # a kiolvasó a vLLM-image-ben, GPU nélkül, a bázis tokenizálójával (/hf)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}

# kar | itemfájl | a vLLM-ben a modell neve (adapter vagy a bázis)
KAROK="k03v2_g3_s1|$I/items_eval.jsonl|k03v2_g3_s1
k03v2_g3_s2|$I/items_eval.jsonl|k03v2_g3_s2
k03v2_g3_s3|$I/items_eval.jsonl|k03v2_g3_s3
l3mixse_h2_s1|kor03/adat/f4/items_ho_termek.jsonl|l3mixse_h2_s1
l3mixse_h2_s2|kor03/adat/f4/items_ho_termek.jsonl|l3mixse_h2_s2
l3mixse_h2_s3|kor03/adat/f4/items_ho_termek.jsonl|l3mixse_h2_s3
k01_l3mixse_p30_s1|kor03/adat/f4/items_ho_routing.jsonl|k01_l3mixse_p30_s1
k01_l3mixse_p30_s2|kor03/adat/f4/items_ho_routing.jsonl|k01_l3mixse_p30_s2
k01_l3mixse_p30_s3|kor03/adat/f4/items_ho_routing.jsonl|k01_l3mixse_p30_s3
k03v2_g3kemeny_s1|$I/items_eval.jsonl|k03v2_g3kemeny_s1
k03v2_g3hu_s1|$I/items_eval.jsonl|k03v2_g3hu_s1
l0r|$I/items_eval.jsonl|Qwen/Qwen3.6-35B-A3B-FP8"
while IFS='|' read -r A ITEMS M; do
  OUT="kor03/eredmenyek/F4/$A/vllm_eval.jsonl"
  want=$(( $(wc -l < "$ITEMS") * 4 ))
  have=$(wc -l < "$OUT")
  [ "$have" -ge "$want" ] && { echo "$A: teljes ($have/$want)"; continue; }
  if [ -f "$EXP/STOP-K03F4" ]; then
    say "STOP-K03F4: megállok $A pótlása előtt"
    rm -f "$EXP/AKTIV_FAZIS"
    exit 0
  fi
  say "K03F4 pótlás: $A ($have/$want sor, hiányzik $((want - have)))" 1800
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 2400 || { subject_stop ldh-subject "$R/$A"; fail "alany boot ($A pótlás)"; }
  if [ "$M" = "$A" ]; then
    curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
      -d "{\"lora_name\": \"$A\", \"lora_path\": \"/adapters/$A\"}" > "$R/$A/vllm_load_potlas.txt" 2>&1 \
      || { subject_stop ldh-subject "$R/$A"; fail "$A: a vLLM nem töltötte be az adaptert (pótlás)"; }
  fi
  echo "--- pótlás $(date '+%F %T')" >> "$R/$A/olvas.log"
  kpy kor03/eszkozok/kiolvaso03.py --mode ids --items "$ITEMS" --out "$OUT" --perms 0,1,2,3 \
    --url "http://127.0.0.1:$SUBJECT_PORT" --model "$M" --concurrency 64 2>&1 | tee -a "$R/$A/olvas.log" | tail -2
  rc="${PIPESTATUS[0]}"
  subject_stop ldh-subject "$R/$A/potlas"
  [ "$rc" = "0" ] || fail "$A pótlás"
  have=$(wc -l < "$OUT")
  [ "$have" -ge "$want" ] || fail "$A a pótlás után is hiányos ($have/$want)"
  sha256sum "$OUT" >> "$R/PECSET.sha256"
done <<< "$KAROK"

say "K03F4 pótlás kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
