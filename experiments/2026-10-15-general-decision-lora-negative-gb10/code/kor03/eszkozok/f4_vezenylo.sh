#!/usr/bin/env bash
# K03F4 — a kitartott és eval-rétegek kiolvasása (03-runbook 6., 7., 8.; Dani, 2026-10-13: „lepecsételt kiolvasás
# most”). A kiolvasás a v1 (hipotézisek, küszöbök, MDE, célréteg-kalibrációs minták) rögzítése ELŐTT fut, az elemzés
# csak a jóváhagyás után: az eredményfájlok a Sparkon maradnak, mindegyik sha256-ja a PECSET.sha256-ba kerül.
#   G3 s1–s3, G3-kemény, G3-hu (MVP v2): az összes eval-item (items_eval, 45 965 item: teszt-ID, HO-termék,
#     HO-routing, HO-új, HO-forrás, külső eval), 4 permutáció. Az L1★ eval-kiolvasása az F2-ből kész (qwen_eval).
#   L3-spec: a 00 adapterei (l3mixse_h2_s1..s3) a HO-terméken, a 01 L3 (k01_l3mixse_p30_s1..s3) a HO-routingon.
# Ugyanaz a LORA=1-es alany és kiolvasó, mint az F2 L1★-jánál és az F3 val-kiolvasásainál. Karok közt STOP-K03F4 a
# kísérleti gyökérben: megáll a következő kar előtt. Idempotens.
#   nohup setsid bash kor03/eszkozok/f4_vezenylo.sh > logs/k03f4.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=K03F4-kiolvasas
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F4"
I=kor03/adat/f2
mkdir -p "$R" adapters kor03/adat/f4
rm -f "$EXP/FAILED-$FAZIS"

gpu_containers() {  # csak a GPU-t használó konténer számít
  for c in $(docker ps -q); do [ "$(docker inspect -f '{{len .HostConfig.DeviceRequests}}' "$c")" != "0" ] && echo "$c"; done
}
kpy() {  # a kiolvasó a vLLM-image-ben, GPU nélkül, a bázis tokenizálójával (/hf)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
olvas() {  # olvas <adapter> <itemek> — LORA=1-es alany, az adapter betöltve, 4 permutáció
  local A="$1" items="$2" outf="kor03/eredmenyek/F4/$1/vllm_eval.jsonl"
  mkdir -p "$R/$A"
  if [ ! -f "adapters/$A/adapter_model.safetensors" ]; then
    cp -r "ckpt/$A/vllm" "adapters/$A" || fail "$A adapter-másolás"
  fi
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 2400 || { subject_stop ldh-subject "$R/$A"; fail "alany boot ($A)"; }
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$A\", \"lora_path\": \"/adapters/$A\"}" > "$R/$A/vllm_load.txt" 2>&1 \
    || { subject_stop ldh-subject "$R/$A"; fail "$A: a vLLM nem töltötte be az adaptert"; }
  kpy kor03/eszkozok/kiolvaso03.py --mode ids --items "$items" --out "$outf" --perms 0,1,2,3 \
    --url "http://127.0.0.1:$SUBJECT_PORT" --model "$A" --concurrency 64 2>&1 | tee -a "$R/$A/olvas.log" | tail -2
  local rc="${PIPESTATUS[0]}"
  subject_stop ldh-subject "$R/$A"
  [ "$rc" = "0" ] || fail "$A kiolvasás"
  sha256sum "$outf" >> "$R/PECSET.sha256"
}

for i in $(seq 1 15); do [ -z "$(gpu_containers)" ] && break; sleep 60; done
for c in $(gpu_containers); do fail "FUT MÁS GPU-KONTÉNER: $(docker inspect -f '{{.Name}}' "$c")"; done
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env

# a két L3-spec réteg részhalmaza az eval-itemekből
python3 - <<'EOF'
import json
out = {"ho-termek": open("kor03/adat/f4/items_ho_termek.jsonl", "w"), "ho-routing": open("kor03/adat/f4/items_ho_routing.jsonl", "w")}
for line in open("kor03/adat/f2/items_eval.jsonl", encoding="utf-8"):
    s = json.loads(line)["split"]
    if s in out:
        out[s].write(line)
EOF
sha256sum "$I/items_eval.jsonl" kor03/adat/f4/items_ho_termek.jsonl kor03/adat/f4/items_ho_routing.jsonl > "$R/bemenet_sha256.txt"

# kar | itemfájl | ETA (s)
KAROK="k03v2_g3_s1|$I/items_eval.jsonl|13500
k03v2_g3_s2|$I/items_eval.jsonl|13500
k03v2_g3_s3|$I/items_eval.jsonl|13500
l3mixse_h2_s1|kor03/adat/f4/items_ho_termek.jsonl|2200
l3mixse_h2_s2|kor03/adat/f4/items_ho_termek.jsonl|2200
l3mixse_h2_s3|kor03/adat/f4/items_ho_termek.jsonl|2200
k01_l3mixse_p30_s1|kor03/adat/f4/items_ho_routing.jsonl|3400
k01_l3mixse_p30_s2|kor03/adat/f4/items_ho_routing.jsonl|3400
k01_l3mixse_p30_s3|kor03/adat/f4/items_ho_routing.jsonl|3400
k03v2_g3kemeny_s1|$I/items_eval.jsonl|13500
k03v2_g3hu_s1|$I/items_eval.jsonl|13500"
while IFS='|' read -r A ITEMS ETA; do
  if [ -f "$EXP/STOP-K03F4" ]; then
    say "STOP-K03F4: megállok $A előtt"
    rm -f "$EXP/AKTIV_FAZIS"
    exit 0
  fi
  if ! done_marker "olvas_$A"; then
    say "K03F4: $A kiolvasása ($(wc -l < "$ITEMS") item × 4 permutáció)" "$ETA"
    olvas "$A" "$ITEMS"
    mark_ok "olvas_$A"
  fi
done <<< "$KAROK"

say "K03F4 kiolvasás kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
