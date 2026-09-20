#!/usr/bin/env bash
# K0 ÚJ PÉLDÁNYON — a soros determinizmus KISZOLGÁLÓ-PÉLDÁNYOK KÖZÖTTI igazolása.
#
# ⛔ Miért kell (2026-09-18, menet közbeni önellenőrzés): a determinizmus-kapu azt
# igazolja, hogy EGY kiszolgáló-példányon belül a soros mérés bájtra reprodukálható.
# A karok összevetése viszont mindig KÉT PÉLDÁNY között történik (minden kar saját
# betöltés). Ha a kernelválasztás/autotuning példányonként más numerikát ad, a
# késélen ülő itemek (`T7-08` és társai) a példánytól is billenhetnek — és azt a folt
# hatásának néznénk. Ezért: a K0-t friss példányon még egyszer lemérjük, sorosan, 1×,
# és bájtra összevetjük a determinizmus-kapun átment K0-val.
#
# Ugyanezen a friss példányon a 12 igazoló itemet `parallel=6`-tal is lefuttatjuk:
# ha a `T7-08` itt is átbillen, a kötegméret-hatás UGYANAZON a példányon belül is
# bizonyított (az első mérés két példány között történt, ez rés volt a kapu logikájában).
#
# Csak az F1 lezárása UTÁN indul (a vezénylő megvárja az „F1 KÉSZ" állapotot).
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
SNAP=<base-snapshot>
IMG=vllm-openai:beta-mirror-dev328
URL=http://127.0.0.1:18355
VALID=T1-01,T2-01,T5-01,T7-08,T9-01,T10-01,C1-01,C2-02,C5-03,C6-01,C7-01,C9-02
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-UJPELDANY"; }

say "várom az F1 végét"
for i in $(seq 1 2000); do
  grep -q "^F1 KÉSZ" "$EX/STATUS-F1" 2>/dev/null && break
  grep -q "^⛔\|^HIBA" "$EX/STATUS-F1" 2>/dev/null && { say "az F1 hibával állt le, nem indulok"; exit 1; }
  sleep 60
done
[ -s "$EX/magyar-kie-eval/reports/csapda-K0.json" ] || { say "HIBA: nincs soros csapda-K0.json"; exit 1; }

# Friss példány — szándékosan NEM az ELO ág: a lényeg az újrabetöltés.
docker rm -f cjk-kiszolgalo >/dev/null 2>&1 || true
say "K0 friss példány indul"
docker run -d --name cjk-kiszolgalo --gpus all --ipc host -p 127.0.0.1:18355:8000 \
  -v "$HOME/.cache/huggingface:<hf-cache>" -v "$EX:/work" \
  -e VLLM_USAGE_SOURCE=cjk-csillapitas "$IMG" \
  "$SNAP" --host 0.0.0.0 --port 8000 --served-model-name qwen36 \
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
  [ "$i" = 240 ] && { say "HIBA: a példány nem lett kész"; exit 1; }
done
say "K0 friss példány kész"

# 1. a teljes korpusz sorosan, 1× — az összevetés alapja
say "csapda 150 × 1, sorosan, friss példányon"
( cd "$EX/magyar-kie-eval" && python3 src/harness.py --url "$URL" --model qwen36 \
    --cimke K0-ujpeldany --items gt/items-150.jsonl --futasok 1 --parallel 1 \
    --out reports/csapda-K0-ujpeldany.json ) > "$EX/naplo/csapda-K0-ujpeldany.log" 2>&1

# 2. a 12 igazoló item párhuzamosan, UGYANEZEN a példányon
say "12 item parallel=6, ugyanezen a példányon"
( cd "$EX/magyar-kie-eval" && python3 src/harness.py --url "$URL" --model qwen36 \
    --cimke K0-ujpeldany-par6 --items gt/items-150.jsonl --item-ids "$VALID" \
    --futasok 3 --parallel 6 --out reports/csapda-K0-ujpeldany-par6.json ) \
  > "$EX/naplo/csapda-K0-ujpeldany-par6.log" 2>&1

# 3. összevetések
{
  echo "### PÉLDÁNYOK KÖZÖTT: soros K0 (1. példány, 3×) vs soros K0 (friss példány, 1×)"
  python3 "$EX/eszkozok/parhuzam_ellenoriz.py" \
    "$EX/magyar-kie-eval/reports/csapda-K0.json" \
    "$EX/magyar-kie-eval/reports/csapda-K0-ujpeldany.json"
  echo; echo "### PÉLDÁNYON BELÜL: soros (friss) vs parallel=6 (friss), 12 item"
  python3 "$EX/eszkozok/parhuzam_ellenoriz.py" \
    "$EX/magyar-kie-eval/reports/csapda-K0-ujpeldany-par6.json" \
    "$EX/magyar-kie-eval/reports/csapda-K0-ujpeldany.json"
} > "$EX/eredmenyek/ujpeldany-igazolas.txt" 2>&1
tail -4 "$EX/eredmenyek/ujpeldany-igazolas.txt"
say "ÚJ PÉLDÁNY KÉSZ — eredmenyek/ujpeldany-igazolas.txt"
