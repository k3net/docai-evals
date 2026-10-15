#!/usr/bin/env bash
# K03F4 L0′ — az L1★ eval-kiolvasásának ismétlése egy új vLLM-példányon (a 00 F4 L0′-jének mintájára): a példányok
# közti nemdeterminizmus (memória: ±2–5 item/150) mérése, mert minden G3-kar saját példányon olvasott, az L1★ pedig
# az F2-ben. Ugyanaz a beállítás, mint az F2 qwen_eval-ja (LORA=1-es szerver, adapter nélkül, a bázis neve).
# Megvárja a lepecsételt F4-kiolvasás végét; a kimenet is a pecsétbe kerül.
#   nohup setsid bash kor03/eszkozok/f4_l0r.sh > logs/k03f4_l0r.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=K03F4-l0r
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R="$EXP/kor03/eredmenyek/F4"
echo "[$(date '+%F %T')] vár a K03F4-kiolvasásra"
while [ ! -f DONE-K03F4-kiolvasas ]; do
  [ -f FAILED-K03F4-kiolvasas ] && { echo "[$(date '+%F %T')] a kiolvasás hibával állt le, az L0′ nem indul"; exit 1; }
  [ -f STOP-K03F4 ] && { echo "[$(date '+%F %T')] STOP-K03F4: kilépek"; exit 0; }
  sleep 120
done
sleep 30
rm -f "$EXP/FAILED-$FAZIS"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
record_env
mkdir -p "$R/l0r"
OUT=kor03/eredmenyek/F4/l0r/vllm_eval.jsonl
if ! done_marker olvas_l0r; then
  say "K03F4: L0′ (az L1★ eval-kiolvasásának ismétlése, 45 965 item × 4 permutáció)" 13500
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 2400 || { subject_stop ldh-subject "$R/l0r"; fail "alany boot (L0′)"; }
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/.cache/huggingface:/hf:ro" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e LDH_HF=/hf -e HOME=/tmp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" kor03/eszkozok/kiolvaso03.py --mode ids \
    --items kor03/adat/f2/items_eval.jsonl --out "$OUT" --perms 0,1,2,3 --url "http://127.0.0.1:$SUBJECT_PORT" \
    --model Qwen/Qwen3.6-35B-A3B-FP8 --concurrency 64 2>&1 | tee -a "$R/l0r/olvas.log" | tail -2
  rc="${PIPESTATUS[0]}"
  subject_stop ldh-subject "$R/l0r"
  [ "$rc" = "0" ] || fail "L0′ kiolvasás"
  sha256sum "$OUT" >> "$R/PECSET.sha256"
  mark_ok olvas_l0r
fi
say "K03F4 L0′ kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
