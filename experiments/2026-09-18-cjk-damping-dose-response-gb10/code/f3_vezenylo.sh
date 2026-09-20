#!/usr/bin/env bash
# F3 — a győztes megerősítése (runbook §6/F3), a 2026-09-19-i döntés szerint három fázisban:
#
#  A) A KOCKÁZATMÉRÉS IGAZOLÁSA a tényleges eloszláson. A kiszolgáló `--logprobs-mode
#     processed_logprobs` módban fut: a visszaadott top-20 a büntetések + hőmérséklet +
#     top_k + top_p UTÁNI tartó. K0 és S07, három prod-profilon (alap t=0,6; alap t=0,3 —
#     a config.py mai alapértéke; újrapróbálkozás t=0,9/top_p 1,0/pp 1,8), 5 seeddel,
#     plusz a 150 itemes csapda a prod-profilon logprobbal (≈165 000 magyar pozíció,
#     ügyféladat nélkül). Kiértékelés: han_kockazat.py --feldolgozott.
#     ⚠️ processed_logprobs CUDA-n csak seedelt kéréssel megy (a FlashInfer-ág assert-el),
#     ezért itt MINDEN kérés seedelt.
#  B) S07–K0 MEGERŐSÍTÉS a sima (prod-azonos) motoron, három friss S07-példányon és egy
#     friss K0-példányon: ugyanaz a három profil × 5 seed, egy 3-szálas PÁRHUZAMOS köteg
#     (éles terhelés), és a csapda a prod-profilon (parallel=6, 3×) a költségre.
#  C) Az új karok a felhasználó sorrendjében: S08 → S09 → S06 (a sima F2-protokoll, Han 5×).
#
# ⛔ A prod-próba (kis forgalom, visszaállítható) NEM ennek a szkriptnek a dolga: az A) és
# B) eredményének kiértékelése után a felhasználó dönt róla.
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
SNAP=<base-snapshot>
IMG=vllm-openai:beta-mirror-dev328
URL=http://127.0.0.1:18355
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-F3"; }

# a három prod-profil, a han_probe.py `cron` profiljára építve (0,6/0,95/20 + pp1,5 + rp1,05)
prof_args() {
  case "$1" in
    alap06) echo "--sampling cron" ;;
    alap03) echo "--sampling cron --set temperature=0.3" ;;
    ujra09) echo "--sampling cron --set temperature=0.9 --set top_p=1.0 --set presence_penalty=1.8" ;;
  esac
}
CSAPDA_PROD="--temperature 0.6 --top-p 0.95 --top-k 20 --presence-penalty 1.5 --repetition-penalty 1.05"

inditas() {  # <cimke> <modell> [extra vllm args...]
  local cimke="$1" modell="$2"; shift 2
  docker rm -f cjk-kiszolgalo >/dev/null 2>&1 || true
  say "$cimke — kiszolgáló indul"
  docker run -d --name cjk-kiszolgalo --gpus all --ipc host -p 127.0.0.1:18355:8000 \
    -v "$HOME/.cache/huggingface:<hf-cache>" -v "$EX:/work" \
    -e VLLM_USAGE_SOURCE=cjk-csillapitas "$IMG" \
    "$modell" --host 0.0.0.0 --port 8000 --served-model-name qwen36 \
    --tensor-parallel-size 1 --max-model-len 262144 --max-num-batched-tokens 8192 \
    --gpu-memory-utilization 0.5 --max-num-seqs 8 --kv-cache-dtype fp8_e4m3 \
    --enable-chunked-prefill --enable-prefix-caching --reasoning-parser qwen3 \
    --enable-auto-tool-choice --tool-call-parser qwen3_coder \
    --limit-mm-per-prompt '{"image":1}' --trust-remote-code --no-async-scheduling \
    --speculative-config '{"method":"mtp","num_speculative_tokens":2}' \
    --enable-prompt-tokens-details "$@" >/dev/null
  for i in $(seq 1 80); do
    curl -sf "$URL/health" >/dev/null 2>&1 && { say "$cimke — kiszolgáló kész"; return 0; }
    docker ps -q -f name=cjk-kiszolgalo | grep -q . || break
    sleep 15
  done
  say "HIBA: $cimke kiszolgálója nem lett kész"
  docker logs --tail 60 cjk-kiszolgalo > "$EX/naplo/f3-$cimke-HIBA.log" 2>&1
  return 1
}

# szonda: <cimke> <profil> <seed-lista…> — seedenként külön futás, majd egy könyvtárba gyűjtve
szonda() {
  local cimke="$1" prof="$2"; shift 2
  local cel="$EX/results/F3-$cimke-$prof"
  [ -s "$cel/summary.json" ] && return 0
  rm -rf "$cel"; mkdir -p "$cel"
  local n=0
  for seed in "$@"; do
    local d="$EX/results/F3-$cimke-$prof-s$seed"
    rm -rf "$d"
    ( cd "$EX" && python3 kit/han_probe.py --url "$URL" --cases cases/cases.jsonl \
        --arm "F3-$cimke-$prof-s$seed" --mode fresh $(prof_args "$prof") \
        --repeat 1 --seed "$seed" --out "$d" ) > "$EX/naplo/han-F3-$cimke-$prof-s$seed.log" 2>&1
    for f in "$d"/[0-9]*.json; do
      [ -e "$f" ] || continue
      cp "$f" "$cel/$(printf '%03d' $n)-$(basename "$f")"; n=$((n+1))
    done
    [ -s "$cel/summary.json" ] || cp "$d/summary.json" "$cel/summary.json" 2>/dev/null
  done
}

# 3-szálas párhuzamos köteg: három szonda egyszerre, három seeddel (éles terhelés)
szonda_par() {
  local cimke="$1" prof="$2"
  local cel="$EX/results/F3-$cimke-$prof-par"
  [ -s "$cel/summary.json" ] && return 0
  rm -rf "$cel"; mkdir -p "$cel"
  local pids=()
  for seed in 11 12 13; do
    local d="$EX/results/F3-$cimke-$prof-par-s$seed"; rm -rf "$d"
    ( cd "$EX" && python3 kit/han_probe.py --url "$URL" --cases cases/cases.jsonl \
        --arm "F3-$cimke-$prof-par-s$seed" --mode fresh $(prof_args "$prof") \
        --repeat 1 --seed "$seed" --out "$d" ) > "$EX/naplo/han-F3-$cimke-$prof-par-s$seed.log" 2>&1 &
    pids+=($!)
  done
  wait "${pids[@]}"
  local n=0
  for seed in 11 12 13; do
    local d="$EX/results/F3-$cimke-$prof-par-s$seed"
    for f in "$d"/[0-9]*.json; do [ -e "$f" ] && { cp "$f" "$cel/$(printf '%03d' $n)-$(basename "$f")"; n=$((n+1)); }; done
    [ -s "$cel/summary.json" ] || cp "$d/summary.json" "$cel/summary.json" 2>/dev/null
  done
}

# csapda a prod-profilon, logprobbal, parallel=6 (a mintavételezett út alatt a köteg a prod feltétele)
csapda_prod() {  # <cimke>
  local cimke="$1"
  [ -s "$EX/magyar-kie-eval/reports/csapda-F3-$cimke-prod.json" ] && return 0
  say "$cimke — csapda a prod-profilon (150 × 3, parallel=6, logprobbal)"
  rm -rf "$EX/results/F3-$cimke-csapda06"
  ( cd "$EX/magyar-kie-eval" && python3 src/harness.py --url "$URL" --model qwen36 \
      --cimke "F3-$cimke-prod" --items gt/items-150.jsonl --futasok 3 --parallel 6 \
      $CSAPDA_PROD --seed 100 --logprobs-ki "$EX/results/F3-$cimke-csapda06" \
      --out "reports/csapda-F3-$cimke-prod.json" ) > "$EX/naplo/csapda-F3-$cimke-prod.log" 2>&1
}

kockazat() {  # <ki-fájl> [--feldolgozott] -- <kar-könyvtárak…>
  local ki="$1"; shift
  local mod=""; [ "$1" = "--feldolgozott" ] && { mod="--feldolgozott"; shift; }
  docker run --rm -v "$EX:/work" -w /work \
    -v "$HOME/.cache/huggingface:<hf-cache>:ro" \
    -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 --entrypoint python3 "$IMG" \
    eszkozok/han_kockazat.py --results /work/results --tokenizer "$SNAP" $mod --poisson \
      --arms "$@" --json "/work/eredmenyek/$ki.json" > "$EX/eredmenyek/$ki.txt" 2>&1
}

# =============================== A) a mérés igazolása ===============================
for KAR in K0 S07; do
  MOD=$SNAP; [ "$KAR" != K0 ] && MOD=/work/karok/$KAR
  C="$KAR-fd"
  if [ ! -s "$EX/eredmenyek/kockazat-F3-$C.txt" ]; then
    inditas "$C" "$MOD" --logprobs-mode processed_logprobs || exit 1
    for prof in alap06 alap03 ujra09; do
      say "$C — szonda $prof, 5 seed (feldolgozott logprob)"
      szonda "$C" "$prof" 1 2 3 4 5
    done
    csapda_prod "$C"
    say "$C — kockázat (feldolgozott)"
    kockazat "kockazat-F3-$C" --feldolgozott \
      "F3-$C-alap06" "F3-$C-alap03" "F3-$C-ujra09" "F3-$C-csapda06"
  fi
done
say "A) KÉSZ — eredmenyek/kockazat-F3-K0-fd.txt, kockazat-F3-S07-fd.txt"

# =============================== B) S07–K0 megerősítés, sima motor ===============================
for C in K0-p1 S07-p1 S07-p2 S07-p3; do
  KAR=${C%-p*}; MOD=$SNAP; [ "$KAR" != K0 ] && MOD=/work/karok/$KAR
  [ -s "$EX/eredmenyek/kockazat-F3-$C.txt" ] && continue
  inditas "$C" "$MOD" || exit 1
  for prof in alap06 alap03 ujra09; do
    say "$C — szonda $prof, 5 seed"
    szonda "$C" "$prof" 1 2 3 4 5
  done
  say "$C — szonda alap06, 3-szálas párhuzamos köteg"
  szonda_par "$C" alap06
  ARMS=("F3-$C-alap06" "F3-$C-alap03" "F3-$C-ujra09" "F3-$C-alap06-par")
  if [ "${C#*-p}" = 1 ]; then csapda_prod "$C"; ARMS+=("F3-$C-csapda06"); fi
  say "$C — kockázat (nyers, a korábbi módszerrel)"
  kockazat "kockazat-F3-$C" "${ARMS[@]}"
done
say "B) KÉSZ — eredmenyek/kockazat-F3-{K0-p1,S07-p1,S07-p2,S07-p3}.txt"

# =============================== C) az új karok ===============================
[ -d "$EX/karok/S06" ] || "$EX/eszkozok/karok_epit_f3.sh" || { say "HIBA: karok építése"; exit 1; }
for KAR in S08 S09 S06; do
  "$EX/eszkozok/kar_futtat.sh" "$KAR" "/work/karok/$KAR" 1 1 5 || { say "HIBA: $KAR"; exit 1; }
done
say "F3 KÉSZ — A) mérés-igazolás, B) S07 megerősítés, C) S08/S09/S06 lemérve; a prod-próba a te döntésed"
