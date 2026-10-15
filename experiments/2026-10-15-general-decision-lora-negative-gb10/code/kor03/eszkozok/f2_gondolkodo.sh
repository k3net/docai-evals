#!/usr/bin/env bash
# 03 F2 — a Qwen3.6 gondolkodó kiolvasásai a spark-deven (03-runbook 4.2, 4.4; Dani, 2026-10-10: a teljes val 8
# mintával ~20 óra lett volna, ezért csökkentett minta):
#   1. tanárkapu-minta (items_gond_val, 600 item): itemenként 4 gondolkodó minta, mintánként más permutáció
#   2. gépi zajbecslés (items_zaj, 3215 item, 11 magyar forrás-gold forrás): itemenként 1 minta, 0-s permutáció
# A szerver LORA=0 (mintavétel, nem a G3-karokkal összevetett kalibrált kiolvasás). 128 párhuzamos kérés: a ≤ 4096
# tokenes gondolkodás így fér a KV-cache-be (192 nem gondolkodó kéréssel 82% volt). OK-jelölővel, folytatható.
#   nohup setsid bash kor03/eszkozok/f2_gondolkodo.sh > logs/f2_gondolkodo.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=F2Q
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F2"
I=kor03/adat/f2
mkdir -p "$R"
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e LDH_EXP=/exp -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
gpu_containers() {
  for c in $(docker ps -q); do [ "$(docker inspect -f '{{len .HostConfig.DeviceRequests}}' "$c")" != "0" ] && echo "$c"; done
}
olvas() {  # olvas <címke> <itemek> <perms>
  done_marker "olvas-$1" && return 0
  say "gondolkodó kiolvasás: $1 ($(wc -l < "$2") item, perm $3)"
  cpy kor03/eszkozok/kiolvaso03.py --mode think --items "$2" --out "kor03/eredmenyek/F2/$1.jsonl" --perms "$3" \
    --url http://127.0.0.1:8400 --model Qwen/Qwen3.6-35B-A3B-FP8 --frame auto --concurrency 128 2>&1 \
    | tee -a "$R/olvas-$1.log" | tail -3
  [ "${PIPESTATUS[0]}" = "0" ] || fail "gondolkodó kiolvasás $1"
  mark_ok "olvas-$1"
}

for c in $(gpu_containers); do say "FUT MÁS GPU-KONTÉNER: $(docker inspect -f '{{.Name}}' "$c") — leállok"; exit 3; done
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env
say "Qwen indul (LORA=0, gondolkodó mód)"
LORA=0 subject_start ldh-qwen
subject_wait ldh-qwen 2400 || fail "Qwen nem indult"
olvas qwen_gond_val "$I/items_gond_val.jsonl" 0,1,2,3
olvas qwen_gond_zaj "$I/items_zaj.jsonl" 0
subject_stop ldh-qwen "$R"
say "F2Q kész"
rm -f "$EXP/AKTIV_FAZIS"
touch "$R/DONE-F2Q"
