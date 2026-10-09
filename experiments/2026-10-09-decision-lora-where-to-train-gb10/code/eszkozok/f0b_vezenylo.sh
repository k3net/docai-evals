#!/usr/bin/env bash
# F0/B — eldobható pilot-generálás (seed P=101) és a pilotra épülő kapuk (runbook 9. pont):
#   F0.1 generátor → S1–S4 → generátor le → OpenSearch + bge-m3 → S5–S8
#   K0b-2: címketömeg / X-kontroll / "(" prefill a pilot-itemeken (vLLM)
#   K0d:   L0 HF↔vLLM egyezés a pilot-itemeken
#   K0e:   tréning-egységteszt, 20 lépéses smoke (mix+se), kilövés + folytatás checkpointból
#   K0c:   LoRA-aktiválás csoportonként, DEBUG-loggal, negatív kontrollal
#   K0g:   Llama-3.3-70B-FP8 bíráló boot-próbája
# A pilot SOHA nem kerül a val/tesztbe. Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F0B
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F0"
P=adat/pilot
SEED_P=101
mkdir -p "$R"/{pilot,k0b,k0c,k0d,k0e,k0g}
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
trap 'ldh_cleanup' EXIT
record_env

# --- K0a-2: példányon belüli reprodukálhatóság — konfiguráció-mátrix ----------------------
# K0a: LORA=1 + alap async mellett két soros futás csak 48/50 sorban volt bájtazonos (probe-00: első
# kérés; probe-13: futás közben). Melyik kapcsoló okozza? 3 × 50 item / konfiguráció, bemelegítéssel.
if ! done_marker k0a2; then
  mkdir -p "$R/k0a2"
  for cfg in "lora0:LORA=0" "lora1_async0:LORA=1 ASYNC_OFF=1" "lora1:LORA=1"; do
    nm="${cfg%%:*}"; envs="${cfg#*:}"
    say "K0a-2: $nm — boot + 3 soros futás" 25200
    env $envs bash -c "source eszkozok/lib.sh; subject_start ldh-subject" || fail "K0a-2 indítás ($nm)"
    subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R/k0a2"; fail "K0a-2 boot ($nm)"; }
    for i in 1 2 3; do
      py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0a2/${nm}_run$i.jsonl --perms 0,1 || fail "K0a-2 kiolvasás ($nm)"
    done
    py eszkozok/osszevet.py eredmenyek/F0/k0a2/${nm}_run1.jsonl eredmenyek/F0/k0a2/${nm}_run2.jsonl --out eredmenyek/F0/k0a2/${nm}_12.json
    py eszkozok/osszevet.py eredmenyek/F0/k0a2/${nm}_run1.jsonl eredmenyek/F0/k0a2/${nm}_run3.jsonl --out eredmenyek/F0/k0a2/${nm}_13.json
    subject_stop ldh-subject "$R/k0a2"
  done
  mark_ok k0a2
fi

# --- F0.1 pilot-generálás --------------------------------------------------------
if ! done_marker gen; then
  say "F0.1: generátor boot (Qwen3.8-Flash, ~10–15 perc)" 21600
  ./eszkozok/generator_indit.sh ldh-generator 8410
  t0=$(date +%s); ok=0
  while [ $(( $(date +%s) - t0 )) -lt 2400 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-generator 2>/dev/null)" != "true" ] && break
    curl -fsS http://127.0.0.1:8410/health >/dev/null 2>&1 && { ok=1; break; }
    sleep 15
  done
  [ $ok = 1 ] || { docker logs ldh-generator > "$R/pilot/ldh-generator.log" 2>&1; fail "a generátor nem indult (eredmenyek/F0/pilot/ldh-generator.log)"; }
  echo "{\"generator_boot_s\": $(( $(date +%s) - t0 ))}" > "$R/pilot/generator_boot.json"
  say "F0.1: S1–S4 generálás (pilot, seed $SEED_P)" 18000
  py eszkozok/generator.py all --out $P --scale pilot --seed $SEED_P > "$R/pilot/generator.log" 2>&1 \
    || { docker logs ldh-generator > "$R/pilot/ldh-generator.log" 2>&1; fail "S1–S4 (eredmenyek/F0/pilot/generator.log)"; }
  docker logs ldh-generator > "$R/pilot/ldh-generator.log" 2>&1
  docker rm -f ldh-generator >/dev/null 2>&1
  mark_ok gen
fi

if ! done_marker jeloltek; then
  say "F0.1: OpenSearch + bge-m3 jelöltek, S7–S8 összeállítás" 16200
  # bge_m3_cache: a <user> HF-cache-ében a bge-m3-nak csak az onnx-része van; a teljes 5617a9f6
  # snapshot a clf-study cache-éből a kísérlet saját cache-ébe (common.BGE_M3)
  if [ ! -f "$EXP/cache/bge-m3/OK" ]; then
    src="$HOME/clf-study/hf/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181"
    [ -f "$src/pytorch_model.bin" ] || fail "bge-m3 forrás hiányzik: $src"
    rm -rf "$EXP/cache/bge-m3" && mkdir -p "$EXP/cache/bge-m3"
    cp -rL "$src/." "$EXP/cache/bge-m3/" || fail "bge-m3 másolás"
    echo "BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181 $(sha256sum "$EXP/cache/bge-m3/pytorch_model.bin" | cut -c1-16)" \
      | tee "$EXP/cache/bge-m3/OK" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
  fi
  docker rm -f ldh-opensearch >/dev/null 2>&1 || true
  docker run -d --name ldh-opensearch -p 9201:9200 -e discovery.type=single-node \
    -e DISABLE_SECURITY_PLUGIN=true -e DISABLE_INSTALL_DEMO_CONFIG=true \
    -e "OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g" opensearchproject/opensearch:latest >/dev/null
  echo "opensearch: $(docker image inspect opensearchproject/opensearch:latest --format '{{.Id}}')" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
  py --gpu eszkozok/jeloltek.py --out $P --seed $SEED_P > "$R/pilot/jeloltek.log" 2>&1 || fail "S5–S6 (eredmenyek/F0/pilot/jeloltek.log)"
  docker rm -f ldh-opensearch >/dev/null 2>&1
  py eszkozok/osszeallit.py --out $P --seed $SEED_P > "$R/pilot/osszeallit.log" 2>&1 || fail "S7–S8 (eredmenyek/F0/pilot/osszeallit.log)"
  cp $P/generator_riport.json $P/osszeallit_riport.json "$R/pilot/"
  # a pilot kiértékelő része: minden nem-train item + 300 train-item
  py -c "
import json,random,glob
rows=[]
for f in sorted(glob.glob('$P/items_*.jsonl')):
    its=[json.loads(l) for l in open(f)]
    if f.endswith('items_train.jsonl'):
        random.Random(5).shuffle(its); its=its[:300]
    rows+=its
open('$P/pilot_eval.jsonl','w').write(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
print(len(rows))" > "$R/pilot/pilot_eval_n.txt" || fail "pilot_eval"
  mark_ok jeloltek
fi

# --- K0b-2 + K0d (vLLM-oldal) ------------------------------------------------------
need=0; for s in k0b2 k0d_vllm; do done_marker $s || need=1; done
if [ $need = 1 ]; then
  say "K0b-2/K0d: alany boot" 12600
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R/k0d"; fail "alany boot (K0b-2/K0d)"; }
  if ! done_marker k0b2; then
    say "K0b-2: címketömeg / X-kontroll / ( prefill a pilot-itemeken" 11400
    py eszkozok/kiolvaso.py --items $P/pilot_eval.jsonl --out eredmenyek/F0/k0b/pilot_alap.jsonl --perms 0 || fail "K0b-2 alap"
    py eszkozok/kiolvaso.py --items $P/pilot_eval.jsonl --out eredmenyek/F0/k0b/pilot_alap2.jsonl --perms 0 || fail "K0b-2 alap2"
    py eszkozok/osszevet.py eredmenyek/F0/k0b/pilot_alap.jsonl eredmenyek/F0/k0b/pilot_alap2.jsonl --out eredmenyek/F0/k0b/pilot_repro.json
    py eszkozok/kiolvaso.py --items $P/pilot_eval.jsonl --out eredmenyek/F0/k0b/pilot_kontroll.jsonl --perms 0 --none-text kontroll || fail "K0b-2 kontroll"
    py eszkozok/kiolvaso.py --items $P/pilot_eval.jsonl --out eredmenyek/F0/k0b/pilot_prefill.jsonl --perms 0 --prefill "(" || fail "K0b-2 prefill"
    mark_ok k0b2
  fi
  if ! done_marker k0d_vllm; then
    cp eredmenyek/F0/k0b/pilot_alap.jsonl eredmenyek/F0/k0d/pilot_vllm.jsonl
    mark_ok k0d_vllm
  fi
  subject_stop ldh-subject "$R/k0d"
fi
if ! done_marker k0d_hf; then
  say "K0d: HF-kiolvasás a pilot-itemeken" 9600
  py --gpu eszkozok/hf_kiolvaso.py --items $P/pilot_eval.jsonl --out eredmenyek/F0/k0d/pilot_hf.jsonl --perms 0 \
    > "$R/k0d/hf.log" 2>&1 || fail "K0d HF (eredmenyek/F0/k0d/hf.log)"
  py eszkozok/osszevet.py eredmenyek/F0/k0d/pilot_vllm.jsonl eredmenyek/F0/k0d/pilot_hf.jsonl --out eredmenyek/F0/k0d/pilot_vllm_vs_hf.json || fail "K0d összevetés"
  mark_ok k0d_hf
fi

# --- K0e: tréning-egységteszt, smoke, kilövés + folytatás ------------------------------
if ! done_marker k0e; then
  say "K0e: döntési pozíció egységteszt" 8400
  py --gpu eszkozok/tren_lora.py --train $P/items_train.jsonl --out ckpt/k0e --selftest > "$R/k0e/selftest.log" 2>&1 \
    || fail "K0e egységteszt (eredmenyek/F0/k0e/selftest.log)"
  say "K0e: 20 lépéses smoke (mix+se, grad-accum 8), kilövés a 7. lépés után" 7800
  rm -rf ckpt/k0e/last ckpt/k0e/final ckpt/k0e/train_log.jsonl
  docker run -d --gpus all --ipc host --network host --name ldh-tren-k0e \
    -v "$EXP:/exp" -v "$HOME/.cache/huggingface:/hf:ro" -e HF_HOME=/hf -e HF_HUB_OFFLINE=1 \
    -e LDH_EXP=/exp -e LDH_HF=/hf -e PYTHONUNBUFFERED=1 -w /exp "$TOOL_IMAGE" \
    python3 eszkozok/tren_lora.py --train $P/items_train.jsonl --out ckpt/k0e --targets mix+se \
      --max-steps 20 --grad-accum 8 --save-every 5 >/dev/null
  t0=$(date +%s)
  until [ "$(wc -l < ckpt/k0e/train_log.jsonl 2>/dev/null || echo 0)" -ge 7 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-tren-k0e 2>/dev/null)" != "true" ] && { docker logs ldh-tren-k0e > "$R/k0e/smoke1.log" 2>&1; fail "K0e smoke elhalt (eredmenyek/F0/k0e/smoke1.log)"; }
    [ $(( $(date +%s) - t0 )) -gt 7200 ] && fail "K0e smoke: 2 óra alatt sem ért el 7 lépést"
    sleep 20
  done
  docker logs ldh-tren-k0e > "$R/k0e/smoke1.log" 2>&1
  docker kill ldh-tren-k0e >/dev/null; docker rm -f ldh-tren-k0e >/dev/null 2>&1
  saved=$(python3 -c "import json;print(json.load(open('ckpt/k0e/last/state.json'))['step'])" 2>/dev/null || echo none)
  echo "{\"killed_after_log_lines\": $(wc -l < ckpt/k0e/train_log.jsonl), \"checkpoint_step\": \"$saved\"}" > "$R/k0e/kill.json"
  say "K0e: folytatás checkpointból (mentett lépés: $saved)" 6600
  py --gpu eszkozok/tren_lora.py --train $P/items_train.jsonl --out ckpt/k0e --targets mix+se \
    --max-steps 20 --grad-accum 8 --save-every 5 > "$R/k0e/smoke2.log" 2>&1 || fail "K0e folytatás (eredmenyek/F0/k0e/smoke2.log)"
  grep -q "folytatás: lépés $saved" "$R/k0e/smoke2.log" || fail "K0e: a második futás nem a checkpointból folytatott"
  cp ckpt/k0e/train_log.jsonl ckpt/k0e/config.json ckpt/k0e/done.json "$R/k0e/"
  mark_ok k0e
fi

# --- K0c: LoRA-aktiválás csoportonként ---------------------------------------------------
if ! done_marker k0c; then
  say "K0c: próba-adapterek + alany DEBUG-gal" 4800
  py eszkozok/k0c_adapterek.py --src ckpt/k0e/final --out adapters > "$R/k0c/adapterek.log" 2>&1 || fail "K0c adapterek"
  DEBUG=1 LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R/k0c"; fail "alany boot (K0c)"; }
  py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0c/base.jsonl --perms 0 || fail "K0c alap"
  for a in k0c_attn k0c_gdn k0c_se k0c_all k0c_all_norename; do
    n0=$(docker logs ldh-subject 2>&1 | wc -l)
    curl -fsS -X POST http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter -H 'Content-Type: application/json' \
      -d "{\"lora_name\": \"$a\", \"lora_path\": \"/adapters/$a\"}" > "$R/k0c/$a.load.txt" 2>&1 || echo "betöltési hiba" >> "$R/k0c/$a.load.txt"
    py eszkozok/kiolvaso.py --items adat/probe50.jsonl --out eredmenyek/F0/k0c/$a.jsonl --perms 0 --model $a > "$R/k0c/$a.kiolvas.log" 2>&1 || true
    docker logs ldh-subject 2>&1 | tail -n +$((n0 + 1)) > "$R/k0c/$a.log"
    curl -fsS -X POST http://127.0.0.1:$SUBJECT_PORT/v1/unload_lora_adapter -H 'Content-Type: application/json' -d "{\"lora_name\": \"$a\"}" >/dev/null 2>&1 || true
  done
  docker logs ldh-subject 2>&1 | grep -iE "MoE model detected|FusedMoE|fused moe lora|experts" | head -20 > "$R/k0c/moe_lora_log.txt"
  subject_stop ldh-subject
  py eszkozok/k0c_elemez.py --dir eredmenyek/F0/k0c > "$R/k0c/elemez.log" 2>&1
  echo "K0c kapu kódja: $?" >> "$R/k0c/elemez.log"
  mark_ok k0c   # a kapu eredménye a k0c.json-ban; döntés a Naplóba (nem állítja le az F0-t)
fi

# --- K0g: Llama-bíráló boot-próba (v2 recept, v0.30.0 image) -------------------------------
if ! done_marker k0g; then
  say "K0g: Llama-3.3-70B-FP8 boot-próba" 1800
  docker rm -f ldh-llama >/dev/null 2>&1 || true
  mkdir -p "$HOME/.cache/vllm" "$HOME/.cache/flashinfer" "$HOME/.triton"
  t0=$(date +%s)
  docker run -d --name ldh-llama --gpus all -p 8420:8000 --ipc host \
    -v "$HOME/hf-cache-llama33:<hf-cache>" \
    -e HF_HUB_OFFLINE=1 -e PYTORCH_CUDA_ALLOC_CONF=expandable_segments:False -e RUNAI_STREAMER_MEMORY_LIMIT=4294967296 \
    "$SUBJECT_IMAGE" --model nvidia/Llama-3.3-70B-Instruct-FP8 --served-model-name llama33-70b-fp8 \
    --load-format runai_streamer --kernel-config '{"enable_flashinfer_autotune": false}' --kv-cache-dtype bfloat16 \
    --max-model-len 16384 --gpu-memory-utilization 0.75 --max-num-seqs 4 >/dev/null
  ok=0
  while [ $(( $(date +%s) - t0 )) -lt 2400 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-llama 2>/dev/null)" != "true" ] && break
    curl -fsS http://127.0.0.1:8420/health >/dev/null 2>&1 && { ok=1; break; }
    avail=$(free -g | awk 'NR==2{print $7}')
    [ "$avail" -lt 5 ] && { echo "memória < 5 GB, leállítva" > "$R/k0g/abort.txt"; break; }
    sleep 15
  done
  if [ $ok = 1 ]; then
    curl -fsS http://127.0.0.1:8420/v1/chat/completions -H 'Content-Type: application/json' -d '{"model":"llama33-70b-fp8","max_tokens":20,"temperature":0,"messages":[{"role":"user","content":"Válaszolj egyetlen betűvel: melyik a nagyobb szám? A) 7 B) 12"}]}' > "$R/k0g/proba.json" 2>&1
    echo "{\"boot_s\": $(( $(date +%s) - t0 )), \"ok\": true}" > "$R/k0g/k0g.json"
  else
    echo "{\"ok\": false}" > "$R/k0g/k0g.json"
  fi
  docker logs ldh-llama > "$R/k0g/ldh-llama.log" 2>&1
  docker rm -f ldh-llama >/dev/null 2>&1
  mark_ok k0g
fi

say "F0/B kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
