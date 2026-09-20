#!/usr/bin/env bash
# Egy KAR végigmérése: kiszolgáló + a három publikálható műszer.
#
# A kiszolgáló profilja BÁJTRA a round5 beta-build profilja (beta-build-eval.sh), mert a
# runbook §9 kockázata szerint a motorbuild-eltérés konfundál: a beta-build önmagában
# +3 csapdapontot és hibátlan KIE-t hozott, foltozatlanul is. Címke szerinti
# image-hivatkozás TILOS; az alap-image digestje: sha256:10c361c5…
#
# Használat: kar_futtat.sh <KAR> <MODELL|ELO> [futasok] [parhuzam] [han_ismetles]
#   MODELL=ELO → a MÁR FUTÓ kiszolgálót használja (egy betöltés ~6 perc, ne fizessük ki kétszer)
#
# ⛔ 2026-09-18: a két GREEDY műszer (csapda, kínai próba) SOROSAN fut, `--parallel 1`.
# A runbook §6 párhuzamosság-kapuja megbukott: a `parallel=6` kötegméret a `T7-08`
# itemen a PASS/FAIL-t is átbillentette. A kötegméret-hatás ugyanakkora, mint a mérni
# kívánt hatás, tehát konfundál. Sorosan a dekódolás bitre reprodukálható, ezért az
# ismétlés a kontrollon kívül elhagyható — a soros 1× ugyanannyi GPU-idő, mint a
# korábbi párhuzamos 3×, csak nincs benne köteg-zaj.
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
IMG=vllm-openai:beta-mirror-dev328
URL=http://127.0.0.1:18355
SNAP=<base-snapshot>
KAR="${1:?kar neve, pl. K0}"
MODELL="${2:?modell útvonala a konténerben, vagy ELO}"
CSAPDA_ISM="${3:-1}"   # csapda-ismétlés; a kontrollon 3 (determinizmus-igazolás), máshol 1
KINAI_ISM="${4:-1}"    # kínai próba ismétlés; ugyanaz a logika
HAN_ISM="${5:-3}"      # Han-szonda: MINTAVÉTELEZETT, itt az ismétlés valódi információ
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-KAR"; }

if [ "$MODELL" = "ELO" ]; then
  curl -sf "$URL/health" >/dev/null 2>&1 || { say "HIBA: nem fut kiszolgáló"; exit 1; }
  say "$KAR — a MÁR FUTÓ kiszolgálót használjuk"
else
  docker rm -f cjk-kiszolgalo >/dev/null 2>&1 || true
  say "$KAR — kiszolgáló indul"
  docker run -d --name cjk-kiszolgalo --gpus all --ipc host -p 127.0.0.1:18355:8000 \
    -v "$HOME/.cache/huggingface:<hf-cache>" -v "$EX:/work" \
    -e VLLM_USAGE_SOURCE=cjk-csillapitas "$IMG" \
    "$MODELL" --host 0.0.0.0 --port 8000 --served-model-name qwen36 \
    --tensor-parallel-size 1 --max-model-len 262144 --max-num-batched-tokens 8192 \
    --gpu-memory-utilization 0.5 --max-num-seqs 8 --kv-cache-dtype fp8_e4m3 \
    --enable-chunked-prefill --enable-prefix-caching --reasoning-parser qwen3 \
    --enable-auto-tool-choice --tool-call-parser qwen3_coder \
    --limit-mm-per-prompt '{"image":1}' --trust-remote-code --no-async-scheduling \
    --speculative-config '{"method":"mtp","num_speculative_tokens":2}' \
    --enable-prompt-tokens-details >/dev/null
  for i in $(seq 1 240); do
    curl -sf "$URL/health" >/dev/null 2>&1 && break
    sleep 15
    [ "$i" = 240 ] && { say "HIBA: $KAR kiszolgálója nem lett kész"; exit 1; }
  done
  say "$KAR — kiszolgáló kész"
fi

# ---------- 1. csapda korpusz (elsődleges KÖLTSÉG-végpont) ----------
if [ ! -s "$EX/magyar-kie-eval/reports/csapda-$KAR.json" ]; then
  say "$KAR — csapda (150 item × $CSAPDA_ISM, SOROSAN)"
  ( cd "$EX/magyar-kie-eval" && python3 src/harness.py --url "$URL" --model qwen36 \
      --cimke "$KAR" --items gt/items-150.jsonl --futasok "$CSAPDA_ISM" \
      --parallel 1 --out "reports/csapda-$KAR.json" ) \
    > "$EX/naplo/csapda-$KAR.log" 2>&1
  echo "  → csapda rc=$?"
fi

# ---------- 2. kínai képesség-próba ----------
if [ ! -s "$EX/eredmenyek/kinai-$KAR.json" ]; then
  say "$KAR — kínai próba"
  ( cd "$EX/kinai-proba" && python3 kinai_proba.py --url "$URL" --model qwen36 \
      --cimke "$KAR" --futasok "$KINAI_ISM" --parallel 1 \
      --out "$EX/eredmenyek/kinai-$KAR.json" ) > "$EX/naplo/kinai-$KAR.log" 2>&1
  echo "  → kínai rc=$?"
fi

# ---------- 3. Han-kockázat (elsődleges HASZON-végpont) ----------
# Három hőmérséklet TÉNYLEGESEN is lefut, nem csak kontrafaktuálisan: a
# `han_kockazat.py` átszámolása LOKÁLIS, a ténylegesen bejárt pozíciókra vonatkozik,
# a H5 viszont a teljes eloszlásra állít.
for T in 0.6 0.8 1.0; do
  CIMKE="$KAR-t$T"
  [ -s "$EX/results/$CIMKE/summary.json" ] && continue
  say "$KAR — Han-szonda t=$T (×$HAN_ISM)"
  rm -rf "$EX/results/$CIMKE"
  ( cd "$EX" && python3 kit/han_probe.py --url "$URL" --cases cases/cases.jsonl \
      --arm "$CIMKE" --mode fresh --sampling cron --set "temperature=$T" \
      --repeat "$HAN_ISM" --out "results/$CIMKE" ) > "$EX/naplo/han-$CIMKE.log" 2>&1
  echo "  → $CIMKE rc=$?"
done

# ---------- 4. belső, MEGERŐSÍTŐ műszerek: KIE és contract ----------
# ⛔ Ügyféladat, NEM publikálható — a tanulmányban és a model cardban nem szerepelhet.
# A publikálási döntési szabály 3. feltétele (§7) viszont ezekre épül: „a belső KIE és
# contract nem mutat romlást". Ezért a karonkénti futás kötelező, az eredmény belső.
# Az eval-futtatók a prod-tükörben mennek (azok csak HTTP-klienskód, a modellhez semmi
# közük); a kiszolgáló változatlanul a beta-build.
# ⚠️ Korlát: a contract-runner `--parallel 3`-mal megy, tehát rá is vonatkozik a fent
# leírt kötegméret-hatás. MINDEN karon azonos, így az összevetés önmagában áll, de
# item-szintű állítás belőle nem tehető. Megerősítő műszer, nem publikálható — ezért
# maradhat így; a tanulmány korlát-szakaszába bekerül.
EV=$HOME/experiments/2026-09-15-smoothie-eval
CLI=vllm-openai:prod-mirror-0.19.1rc1
UG="$(id -u):$(id -g)"
if [ -d "$EV/spark/tools/eval_harness/kie" ] && [ ! -s "$EX/eredmenyek/kie-$KAR.log" ]; then
  say "$KAR — KIE (belső)"
  docker run --rm --network host --user "$UG" -v "$EV:/eval"     -w /eval/spark/tools/eval_harness/kie --entrypoint python3 "$CLI"     runner.py --corpus corpus --vllm-url "$URL" --label "cjk-$KAR"     > "$EX/eredmenyek/kie-$KAR.log" 2>&1
  echo "  → KIE rc=$?"
  say "$KAR — contract (belső)"
  docker run --rm --network host --user "$UG" -v "$EV:/eval"     -w /eval/spark/tools/eval_harness/contract --entrypoint python3 "$CLI"     runner.py --corpus corpus --vllm-url "$URL" --model qwen36 --parallel 3     --label "cjk-$KAR" > "$EX/eredmenyek/contract-$KAR.log" 2>&1
  echo "  → contract rc=$?"
fi

# ---------- 5. eseménypróba: a rögzített billenési pont ----------
# A legélesebb előtte/utána, amit ismerünk: a round5-ben RÖGZÍTETT nyelvváltás pontos
# tokenprefixe (`results/cron/002-000.json`, a `继续` szakasz), egyetlen pozícióra,
# `temperature=0`, `logprobs=20`. A prefix bájtra ugyanaz, az egyetlen változó a modell —
# innen jött a round5 `8,314 % → 0,000 %` top-20 Han-tömege.
# ⚠️ Korlát (a szonda saját doksijából): a teljes prefix ÚJ prefillként megy be, tehát
# az eredeti decode/MTP/cache útvonal nem áll helyre. Lokális kérdésre jó, a jelenség
# reprodukciójának NEM nevezhető.
R5=$HOME/experiments/2026-09-14-qwen36-hu-han
if [ -f "$R5/results/cron/002-000.json" ] && [ ! -s "$EX/eredmenyek/esemenyproba-$KAR.json" ]; then
  say "$KAR — eseménypróba (rögzített billenési pont)"
  docker run --rm --network host -v "$EX:/work" -v "$R5:/r5" -w /work     --entrypoint python3 "$IMG"     kit/smoothie_esemenyproba.py --record /r5/results/cron/002-000.json       --url "$URL" --label "$KAR" --out "/work/eredmenyek/esemenyproba-$KAR.json"     > "$EX/naplo/esemenyproba-$KAR.log" 2>&1
  echo "  → eseménypróba rc=$?"
fi

say "$KAR — kockázat-számítás"
docker run --rm -v "$EX:/work" -w /work \
  -v "$HOME/.cache/huggingface:<hf-cache>:ro" \
  -e HF_HUB_OFFLINE=1 -e TRANSFORMERS_OFFLINE=1 --entrypoint python3 "$IMG" \
  eszkozok/han_kockazat.py --results /work/results --tokenizer "$SNAP" \
    --arms "$KAR-t0.6" "$KAR-t0.8" "$KAR-t1.0" --poisson \
    --json "/work/eredmenyek/kockazat-$KAR.json" \
  > "$EX/eredmenyek/kockazat-$KAR.txt" 2>&1
echo "  → kockázat rc=$?"

say "$KAR — KÉSZ"
