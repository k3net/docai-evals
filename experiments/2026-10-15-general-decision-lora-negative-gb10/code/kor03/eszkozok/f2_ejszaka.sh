#!/usr/bin/env bash
# 03 — az F1 lezárása és az F2 első kiolvasásai a spark-deven, a laptop nélkül (03-runbook 8.; Dani, 2026-10-09
# éjjel: „fűzzél fel még feladatokat”). Egyszerre egy modell fut (00 szabály). Lépések, OK-jelölővel, újraindíthatóan:
#   0. vár, amíg az F1SZ (P2–P4) kész; ha az F1SZ hibával állt le, nem indul
#   Z. a laptopos f1_zaras.sh lépései itt (rsync nélkül): szint03 final, szinonim03 dontes, szivárgás-audit, keverő,
#      befagyasztás a szintetikus rétegekkel + ellenőrzés, összesítő, az F2-itemlisták (f2_itemek03.py)
#   M. Mistral Small 4 (chat, top-20, k = 4) a val-on: tanárkapu (4.4)
#   Q. Qwen3.6 L0 (ids, gondolkodás nélkül, k = 4) a val-on → az eval-rétegeken → a train-en (L1★, családválasztás,
#      bázis-horgony). A szerver LORA=1-gyel fut, mint a 00/01 L0-ja és a későbbi G3-karok: az --enable-lora
#      MoE-kernelt vált, a LoRA nélküli szerver eloszlásai ~6%-ban eltérnének.
#   G. Gemma 4 26B-A4B (ids, k = 4) a val-on (tanárkapu) és a train-en (soft target, gépi zajbecslés; csak ha a
#      tanárkapun átmegy). 2026-10-10-ig a val-kiolvasás az M előtt futott, külön bootban.
# A kiolvasó folytatható: egy újrakevert poolon csak az új (id, perm) párokat olvassa (a lezárás újrafuttatása után
# a megfelelő olvas-* jelölőt kell törölni).
# A kiolvasási lépések hibája nem állítja meg a láncot (a HIBAK.txt-be kerül), a lezárásé igen.
# Megállítás a következő lépéshatáron: touch STOP-F2E. Leválasztva indítandó:
#   nohup setsid bash kor03/eszkozok/f2_ejszaka.sh > logs/f2_ejszaka.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=F2E
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F2"
I=kor03/adat/f2
O=kor03/eredmenyek/F2
WAIT_FOR="${WAIT_FOR:-kor03/eredmenyek/F1SZ/DONE-P2_P3_P4-1300}"
GEMMA_SNAP="/hfg/models--google--gemma-4-26B-A4B-it/snapshots/$(basename "$(ls -d "$HOME"/hf-cache-gemma4/models--google--gemma-4-26B-A4B-it/snapshots/* | head -1)")"
mkdir -p "$R"

cpy() {  # CPU-lépés a vLLM-image Pythonjával, GPU nélkül, a saját uid-del
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
kpy() {  # a kiolvasó: mint a cpy, a Qwen- (/hf) és a Gemma-tokenizerrel (/hfg)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -v "$HOME/hf-cache-gemma4:/hfg:ro" \
    -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
stop_check() {
  [ -f "$EXP/STOP-F2E" ] || return 0
  say "STOP-F2E: megállok a lépéshatáron"
  ldh_cleanup
  rm -f "$EXP/AKTIV_FAZIS"
  exit 0
}
gemma_start() {
  docker rm -f ldh-gemma4 >/dev/null 2>&1 || true
  docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
    -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
    "$SUBJECT_IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
    --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs 48 --max-logprobs 64 \
    --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null
  local t0; t0=$(date +%s)
  while [ $(( $(date +%s) - t0 )) -lt 2700 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-gemma4 2>/dev/null)" != "true" ] && return 1
    curl -fsS http://127.0.0.1:8440/health >/dev/null 2>&1 && return 0
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 5 ] && { docker rm -f ldh-gemma4 >/dev/null 2>&1; return 1; }
    sleep 15
  done
  return 2
}
gemma_stop() { docker logs ldh-gemma4 > "$R/ldh-gemma4-$1.log" 2>&1 || true; docker rm -f ldh-gemma4 >/dev/null 2>&1 || true; }

lep() {  # lep <név> <szkript-argok...> — lezárási lépés; a hibája megállítja a láncot
  local name="$1"; shift
  done_marker "$name" && return 0
  say "lezárás: $name"
  cpy "$@" 2>&1 | tee -a "$R/zaras.log" | tail -25
  [ "${PIPESTATUS[0]}" = "0" ] || return 1
  mark_ok "$name"
}
olvas() {  # olvas <címke> <itemek> <kiolvasó-argok...> — a hibája csak a HIBAK.txt-be kerül
  local tag="$1" items="$2"; shift 2
  done_marker "olvas-$tag" && return 0
  stop_check
  say "kiolvasás: $tag ($(wc -l < "$items") item × 4 perm)"
  kpy kor03/eszkozok/kiolvaso03.py --items "$items" --out "$O/$tag.jsonl" --perms 0,1,2,3 "$@" 2>&1 \
    | tee -a "$R/olvas-$tag.log" | tail -3
  if [ "${PIPESTATUS[0]}" = "0" ]; then mark_ok "olvas-$tag"; else
    echo "[$(date '+%F %T')] kiolvasás $tag: hibával állt le (log: $R/olvas-$tag.log)" >> "$R/HIBAK.txt"; return 1; fi
}

# --- 0. várakozás az F1SZ-re -------------------------------------------------
say "vár az F1SZ-re ($WAIT_FOR)"
while [ ! -f "$EXP/$WAIT_FOR" ]; do
  if [ -f "$EXP/FAILED-F1SZ" ]; then
    say "az F1SZ hibával állt le, az F2E nem indul: $(cat "$EXP/FAILED-F1SZ")"
    echo "[$(date '+%F %T')] az F1SZ hibával állt le" > "$EXP/FAILED-F2E"
    exit 1
  fi
  stop_check
  sleep 120
done
gpu_containers() {  # csak a GPU-t használó konténer számít (egy letöltő vagy CPU-kliens nem)
  for c in $(docker ps -q); do [ "$(docker inspect -f '{{len .HostConfig.DeviceRequests}}' "$c")" != "0" ] && echo "$c"; done
}
for i in $(seq 1 15); do [ -z "$(gpu_containers)" ] && break; sleep 60; done
for c in $(gpu_containers); do fail "FUT MÁS GPU-KONTÉNER: $(docker inspect -f '{{.Name}}' "$c")"; done
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env

# --- Z. az F1 lezárása --------------------------------------------------------
lep final kor03/eszkozok/szint03.py final || fail "szint03 final"
lep dontes kor03/eszkozok/szinonim03.py dontes --tags mistral,gemma || fail "szinonim03 dontes"
lep szivargas kor03/eszkozok/szivargas03.py || fail "szivargas03"
lep kevero kor03/eszkozok/kevero03.py || fail "kevero03"
lep fagyaszt kor03/eszkozok/befagyaszt03.py fagyaszt --szint || fail "befagyasztás"
cpy kor03/eszkozok/befagyaszt03.py ellenoriz 2>&1 | tee -a "$R/zaras.log" | tail -2
[ "${PIPESTATUS[0]}" = "0" ] || fail "a befagyasztott rétegek megváltoztak"
lep osszesito kor03/eszkozok/osszesito03.py \
  || echo "[$(date '+%F %T')] az összesítő hibát talált (zaras.log); a lánc megy tovább" >> "$R/HIBAK.txt"
lep itemek kor03/eszkozok/f2_itemek03.py || fail "f2_itemek03"
touch "$R/DONE-zaras"

GEMMA_R=(--mode ids --url http://127.0.0.1:8440 --model gemma4-26b --tokenizer "$GEMMA_SNAP" --concurrency 48)

# --- M. Mistral a val-on --------------------------------------------------------
stop_check
if ! done_marker olvas-mistral_val; then
  say "Mistral indul"
  if MISTRAL_SEQS=48 mistral_start; then
    olvas mistral_val "$I/items_val.jsonl" --mode chat --url http://127.0.0.1:8430 --model mistral-small-4 \
      --extra '{"reasoning_effort": "none"}' --concurrency 48
  else echo "[$(date '+%F %T')] a Mistral nem indult" >> "$R/HIBAK.txt"; fi
  mistral_stop "$R"
fi

# --- Q. Qwen3.6 L0: val → eval → train ----------------------------------------
QWEN_R=(--mode ids --url http://127.0.0.1:8400 --model Qwen/Qwen3.6-35B-A3B-FP8 --concurrency 64)
stop_check
if ! { done_marker olvas-qwen_val && done_marker olvas-qwen_eval && done_marker olvas-qwen_train; }; then
  say "Qwen indul (LORA=1, adapter nélkül)"
  LORA=1 subject_start ldh-qwen
  if subject_wait ldh-qwen 2400; then
    olvas qwen_val "$I/items_val.jsonl" "${QWEN_R[@]}"
    olvas qwen_eval "$I/items_eval.jsonl" "${QWEN_R[@]}"
    olvas qwen_train "$I/items_train.jsonl" "${QWEN_R[@]}"
  else echo "[$(date '+%F %T')] a Qwen nem indult" >> "$R/HIBAK.txt"; fi
  subject_stop ldh-qwen "$R"
fi

# --- G. Gemma a val-on és a train-en (egy bootban; 2026-10-10 óta a lánc végén) ---------------------------------
stop_check
if ! { done_marker olvas-gemma_val && done_marker olvas-gemma_train; }; then
  say "Gemma indul (val, train)"
  if gemma_start; then
    olvas gemma_val "$I/items_val.jsonl" "${GEMMA_R[@]}"
    olvas gemma_train "$I/items_train.jsonl" "${GEMMA_R[@]}"
  else echo "[$(date '+%F %T')] a Gemma nem indult" >> "$R/HIBAK.txt"; fi
  gemma_stop train
fi

say "F2E kész$([ -f "$R/HIBAK.txt" ] && echo ", hibákkal: $R/HIBAK.txt")"
rm -f "$EXP/AKTIV_FAZIS"
touch "$R/DONE-F2E"
