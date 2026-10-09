#!/usr/bin/env bash
# F0/A — környezet-kapuk a pilot-adat előtt (runbook 9. pont):
#   probe → K0f konverzió → K0a (BI-próba, boot, soros reprodukálhatóság, ujjlenyomat)
#   → K0b (render-egyezés, címkék, címketömeg, X-kontroll, "(" prefill) + vLLM-perplexitás
#   → alany le → K0f betöltési kapu + HF-kiolvasás a próbahalmazon → K0d (próbahalmaz)
# Idempotens: a kész lépéseket kihagyja. Leválasztva indítandó (setsid nohup).
set -uo pipefail
FAZIS=F0A
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F0"
mkdir -p "$R"/{k0a,k0b,k0d,k0f}
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
trap 'ldh_cleanup' EXIT
record_env

# --- probe ---------------------------------------------------------------
if ! done_marker probe; then
  say "probe: ujjlenyomat-próbahalmaz" 7200
  py eszkozok/probe_keszlet.py > "$R/probe.log" 2>&1 || fail "probe_keszlet"
  mark_ok probe
fi

# --- K0f: konverzió (CPU) -----------------------------------------------
if ! done_marker k0f_conv; then
  say "K0f: FP8 → BF16 konverzió (~30–60 perc)" 6600
  py eszkozok/konvertal_fp8_bf16.py --out cache/qwen36-fp8hu-bf16 > "$R/k0f/konverzio.log" 2>&1 \
    || fail "K0f konverzió (ld. eredmenyek/F0/k0f/konverzio.log)"
  cp cache/qwen36-fp8hu-bf16/konverzio_riport.json "$R/k0f/"
  mark_ok k0f_conv
fi

# --- K0a: BI-próba (várhatóan RuntimeError a GDN miatt) -------------------
if ! done_marker k0a_bi; then
  say "K0a: batch-invariáns mód próbája" 4200
  BI=1 LORA=1 subject_start ldh-subject-bi
  subject_wait ldh-subject-bi 1200; rc=$?
  subject_stop ldh-subject-bi "$R/k0a"
  case $rc in
    0) echo '{"bi_mode": "ELINDULT (váratlan) — a reprodukálható út v0.30.0-n is él"}' > "$R/k0a/bi.json" ;;
    1) err=$(grep -m1 -E "batch_invariant mode is not supported|RuntimeError" "$R/k0a/ldh-subject-bi.log" | head -c 400)
       python3 -c 'import json,sys; print(json.dumps({"bi_mode":"NEM INDUL","hiba":sys.argv[1]},ensure_ascii=False))' "$err" > "$R/k0a/bi.json" ;;
    2) echo '{"bi_mode": "IDŐTÚLLÉPÉS"}' > "$R/k0a/bi.json" ;;
  esac
  mark_ok k0a_bi
fi

# --- K0a/K0b: alany boot (scale-out a renderhez) ---------------------------
need_subject=0
for s in k0a_repro k0b_render k0b_labels k0d_vllm_ppl; do done_marker $s || need_subject=1; done
if [ $need_subject = 1 ]; then
  say "K0a: alany boot (LORA=1, scale-out, prefix cache ki)" 3600
  t0=$(date +%s)
  LORA=1 SCALEOUT=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R/k0a"; fail "K0a: az alany nem indult (ld. eredmenyek/F0/k0a/ldh-subject.log)"; }
  echo "{\"boot_s\": $(( $(date +%s) - t0 ))}" > "$R/k0a/boot.json"

  if ! done_marker k0a_repro; then
    say "K0a: soros reprodukálhatóság (2 × 50 item)" 3000
    py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0a/run1.jsonl --perms 0 || fail "kiolvasás run1"
    py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0a/run2.jsonl --perms 0 || fail "kiolvasás run2"
    py eszkozok/osszevet.py eredmenyek/F0/k0a/run1.jsonl eredmenyek/F0/k0a/run2.jsonl --out eredmenyek/F0/k0a/repro.json || fail "összevetés"
    mark_ok k0a_repro
  fi
  if ! done_marker k0b_render; then
    say "K0b: offline tokenizálás vs render" 2700
    py eszkozok/vllm_ellenor.py render --out eredmenyek/F0/k0b/render.json || fail "K0b render-egyezés"
    mark_ok k0b_render
  fi
  if ! done_marker k0b_labels; then
    say "K0b: címketömeg, X-kontroll, ( prefill, 4 permutáció + mozgó X" 2400
    py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0b/kontroll.jsonl --perms 0 --none-text kontroll || fail "kontroll"
    py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0b/prefill.jsonl --perms 0 --prefill "(" || fail "prefill"
    py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0b/perm4.jsonl --perms 0,1,2,3 --move-none-frac 0.5 || fail "perm4"
    mark_ok k0b_labels
  fi
  if ! done_marker k0d_vllm_ppl; then
    say "K0d: vLLM perplexitás" 2100
    py eszkozok/vllm_ellenor.py ppl --out eredmenyek/F0/k0d/vllm_ppl.json || fail "vLLM ppl"
    mark_ok k0d_vllm_ppl
  fi
  subject_stop ldh-subject "$R/k0a"
fi

# --- K0f betöltési kapu + HF-kiolvasás + K0d a próbahalmazon --------------
if ! done_marker k0f_load; then
  say "K0f: HF betöltési kapu + HF-kiolvasás (próbahalmaz) + perplexitás" 1800
  py --gpu eszkozok/hf_kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0f/hf_probe.jsonl --perms 0 --ppl \
    > "$R/k0f/hf_kiolvaso.log" 2>&1 || fail "K0f betöltési kapu / HF-kiolvasás (ld. eredmenyek/F0/k0f/hf_kiolvaso.log)"
  py eszkozok/osszevet.py eredmenyek/F0/k0a/run1.jsonl eredmenyek/F0/k0f/hf_probe.jsonl --out eredmenyek/F0/k0d/probe_vllm_vs_hf.json || fail "K0d összevetés"
  mark_ok k0f_load
fi

say "F0/A kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
