#!/usr/bin/env bash
# K03F3 — a 03-as kör G3-karjai (03-runbook 6., 8., 10. pont 14.). Használat: f3_vezenylo.sh <szakasz>
#   smoke  — tren03 önteszt (döntési pozíció, cél, horgony, a kiolvasóval azonos prompt); 2 lépés a 32 leghosszabb
#            itemen (memória-csúcs); 4 lépés 64 itemen (sebesség); az adapter a vLLM-be töltve, 40 val-item kiolvasása
#            (címketömeg-medián ≥ 0,9: a teljes lánc működik).
#   pilot  — G3 (β = 0,5) és G3-kemény (β = 0), seed 1, a teljes MVP-n (17 500 item, 1 epoch); mindkettő után a
#            val-kiolvasás az adapterrel (4 permutáció) egy LORA=1-es Qwen-példányon.
#   gorbe  — tanulási görbe (8. pont, F3): G3 az MVP 25%-án (4476 item) és 50%-án (8771 item), seed 1, mindkettő után
#            val-kiolvasás; a 100%-os pont a pilot G3-ja.
#   (a smoke, a pilot és a görbe az MVP v1-en futott: adat/f3/mvp_train_v1.jsonl)
#   v2     — az MVP v2-n (10. pont 17.): G3 s1, G3-kemény s1, G3 s2, G3 s3, G3-hu s1, mindegyik után val-kiolvasás.
#            Karok közt STOP-K03F3 a kísérleti gyökérben: megáll a következő kar előtt.
# Idempotens (lépésenkénti jelölők; a tréning checkpointból folytat). Leválasztva indítandó:
#   nohup setsid bash kor03/eszkozok/f3_vezenylo.sh smoke > logs/k03f3_smoke.out 2>&1 < /dev/null &
set -u
SZAKASZ="${1:?szakasz: smoke|pilot|gorbe|v2}"
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS="K03F3-$SZAKASZ"
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F3"
MVP=kor03/adat/f3/mvp_train_v1.jsonl
[ "$SZAKASZ" = v2 ] && MVP=kor03/adat/f3/mvp_train_v2.jsonl
VAL=kor03/adat/f2/items_val.jsonl
T=kor03/eszkozok/tren03.py
mkdir -p "$R" adapters
rm -f "$EXP/FAILED-$FAZIS"

gpu_containers() {  # csak a GPU-t használó konténer számít
  for c in $(docker ps -q); do [ "$(docker inspect -f '{{len .HostConfig.DeviceRequests}}' "$c")" != "0" ] && echo "$c"; done
}
kpy() {  # a kiolvasó a vLLM-image-ben, GPU nélkül, a bázis tokenizálójával (/hf)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
vllm_olvas() {  # vllm_olvas <adapter> <itemek> <perms> <kimenet> — LORA=1-es alany, az adapter betöltve
  local A="$1" items="$2" perms="$3" outf="$4"
  rm -rf "adapters/$A" && cp -r "ckpt/$A/vllm" "adapters/$A" || fail "$A adapter-másolás"
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 2400 || { subject_stop ldh-subject "$R/$A"; fail "alany boot ($A)"; }
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$A\", \"lora_path\": \"/adapters/$A\"}" > "$R/$A/vllm_load.txt" 2>&1 \
    || { subject_stop ldh-subject "$R/$A"; fail "$A: a vLLM nem töltötte be az adaptert"; }
  kpy kor03/eszkozok/kiolvaso03.py --mode ids --items "$items" --out "$outf" --perms "$perms" \
    --url "http://127.0.0.1:$SUBJECT_PORT" --model "$A" --concurrency 64 2>&1 | tee -a "$R/$A/vllm_olvas.log" | tail -2
  local rc="${PIPESTATUS[0]}"
  subject_stop ldh-subject "$R/$A"
  [ "$rc" = "0" ] || fail "$A vLLM-kiolvasás"
}
ckpt_rm() {  # a tanító konténere rootként ír: a checkpointot is a tanító image-ével kell törölni
  py -c "import shutil, sys; [shutil.rmtree(p, ignore_errors=True) for p in sys.argv[1:]]" "$@"
}
tren() {  # tren <arm> <szöveges ETA s> <tren03-argok...>
  local A="$1" eta="$2"; shift 2
  mkdir -p "$R/$A"
  say "K03F3 $SZAKASZ: $A tréning" "$eta"
  py --gpu "$T" --train "$MVP" --out "ckpt/$A" "$@" > "$R/$A/train.log" 2>&1 || fail "$A tréning (kor03/eredmenyek/F3/$A/train.log)"
  cp "ckpt/$A/train_log.jsonl" "ckpt/$A/config.json" "ckpt/$A/done.json" "$R/$A/" 2>/dev/null
}

for i in $(seq 1 15); do [ -z "$(gpu_containers)" ] && break; sleep 60; done
for c in $(gpu_containers); do fail "FUT MÁS GPU-KONTÉNER: $(docker inspect -f '{{.Name}}' "$c")"; done
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env
sha256sum "$MVP" kor03/adat/f2/horgony_qwen_L1.jsonl > "$R/bemenet_sha256_$SZAKASZ.txt"

case "$SZAKASZ" in
smoke)
  A=k03_smoke; mkdir -p "$R/$A"
  if ! done_marker selftest; then
    say "K03F3 smoke: tren03 önteszt" 900
    py --gpu "$T" --train "$MVP" --out ckpt/k03_selftest --beta 0.5 --selftest > "$R/$A/selftest.log" 2>&1 \
      || fail "önteszt (kor03/eredmenyek/F3/$A/selftest.log)"
    cp ckpt/k03_selftest/selftest.json "$R/$A/"
    mark_ok selftest
  fi
  if ! done_marker hosszu; then
    say "K03F3 smoke: 2 lépés a 32 leghosszabb itemen (memória)" 1800
    ckpt_rm ckpt/k03_smoke_hosszu
    py --gpu "$T" --train "$MVP" --out ckpt/k03_smoke_hosszu --beta 0.5 --longest 32 --max-steps 2 \
      > "$R/$A/hosszu.log" 2>&1 || fail "smoke, hosszú itemek (kor03/eredmenyek/F3/$A/hosszu.log)"
    cp ckpt/k03_smoke_hosszu/train_log.jsonl "$R/$A/hosszu_train_log.jsonl"
    mark_ok hosszu
  fi
  if ! done_marker sebesseg; then
    say "K03F3 smoke: 4 lépés 64 itemen (sebesség, vLLM-export)" 1800
    ckpt_rm "ckpt/$A"
    py --gpu "$T" --train "$MVP" --out "ckpt/$A" --beta 0.5 --limit 64 --max-steps 4 \
      > "$R/$A/sebesseg.log" 2>&1 || fail "smoke, sebesség (kor03/eredmenyek/F3/$A/sebesseg.log)"
    [ -f "ckpt/$A/vllm/adapter_model.safetensors" ] || fail "smoke: nincs vLLM-export"
    cp "ckpt/$A/train_log.jsonl" "$R/$A/sebesseg_train_log.jsonl"
    mark_ok sebesseg
  fi
  if ! done_marker vllm; then
    say "K03F3 smoke: az adapter a vLLM-ben, 40 val-item" 2400
    head -40 "$VAL" > kor03/adat/f3/items_smoke_val.jsonl
    vllm_olvas "$A" kor03/adat/f3/items_smoke_val.jsonl 0 "kor03/eredmenyek/F3/$A/vllm_smoke.jsonl"
    kpy -c "
import json, statistics
rows = [json.loads(l) for l in open('kor03/eredmenyek/F3/$A/vllm_smoke.jsonl')]
m = statistics.median(r['label_mass'] for r in rows)
print(f'vLLM-smoke: {len(rows)} sor, címketömeg-medián {m:.3f}')
raise SystemExit(0 if len(rows) == 40 and m >= 0.9 else 1)
" 2>&1 | tee -a "$R/$A/vllm_olvas.log" | tail -1
    [ "${PIPESTATUS[0]}" = "0" ] || fail "vLLM-smoke: hiányzó sor vagy a címketömeg 0,9 alatt"
    mark_ok vllm
  fi
  ckpt_rm ckpt/k03_smoke_hosszu
  rm -rf "adapters/$A"
  ;;
pilot)
  [ -f "$EXP/DONE-K03F3-smoke" ] || fail "a smoke nincs kész"
  for arm in "k03_g3_s1|0.5" "k03_g3kemeny_s1|0"; do
    A="${arm%%|*}"; B="${arm##*|}"
    if ! done_marker "train_$A"; then
      tren "$A" 43000 --beta "$B" --seed 1
      mark_ok "train_$A"
    fi
    if ! done_marker "vllm_$A"; then
      say "K03F3 pilot: $A val-kiolvasás (3122 item × 4 permutáció)" 1800
      vllm_olvas "$A" "$VAL" 0,1,2,3 "kor03/eredmenyek/F3/$A/vllm_val.jsonl"
      mark_ok "vllm_$A"
    fi
  done
  ;;
gorbe)
  [ -f "$EXP/DONE-K03F3-pilot" ] || fail "a pilot nincs kész"
  for arm in "k03_g3_g25_s1|25|7000" "k03_g3_g50_s1|50|13000"; do
    IFS='|' read -r A G ETA <<< "$arm"
    if ! done_marker "train_$A"; then
      tren "$A" "$ETA" --beta 0.5 --seed 1 --gorbe "$G"
      mark_ok "train_$A"
    fi
    if ! done_marker "vllm_$A"; then
      say "K03F3 gorbe: $A val-kiolvasás (3122 item × 4 permutáció)" 1800
      vllm_olvas "$A" "$VAL" 0,1,2,3 "kor03/eredmenyek/F3/$A/vllm_val.jsonl"
      mark_ok "vllm_$A"
    fi
  done
  ;;
v2)
  for arm in "k03v2_g3_s1|--beta 0.5 --seed 1|24000" "k03v2_g3kemeny_s1|--beta 0 --seed 1|24000" \
             "k03v2_g3_s2|--beta 0.5 --seed 2|24000" "k03v2_g3_s3|--beta 0.5 --seed 3|24000" \
             "k03v2_g3hu_s1|--beta 0.5 --seed 1 --csak-hu|18000"; do
    IFS='|' read -r A ARGS ETA <<< "$arm"
    if [ -f "$EXP/STOP-K03F3" ]; then
      say "STOP-K03F3: megállok $A előtt"
      rm -f "$EXP/AKTIV_FAZIS"
      exit 0
    fi
    if ! done_marker "train_$A"; then
      # shellcheck disable=SC2086
      tren "$A" "$ETA" $ARGS
      mark_ok "train_$A"
    fi
    if ! done_marker "vllm_$A"; then
      say "K03F3 v2: $A val-kiolvasás (3122 item × 4 permutáció)" 1800
      vllm_olvas "$A" "$VAL" 0,1,2,3 "kor03/eredmenyek/F3/$A/vllm_val.jsonl"
      mark_ok "vllm_$A"
    fi
  done
  ;;
*) fail "ismeretlen szakasz: $SZAKASZ" ;;
esac

say "K03F3 $SZAKASZ kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
