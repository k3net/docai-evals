#!/usr/bin/env bash
# 03 F1 — szintetikus családok: generálás és független visszacímkézés a spark-deven (03-runbook 3.5, 8.).
# Egyszerre egy modell fut (00 szabály). Fázisok, OK-jelölővel, újraindíthatóan:
#   P1 Mistral Small 4: gen rag.relevancia
#   P2 Gemma 4 26B-A4B: gen entitas.egyezes, jogi.hivatali_ugytipus, level.triage · check (gemma) rag.relevancia
#   P3 Mistral: check (mistral) entitas.egyezes, jogi.hivatali_ugytipus, level.triage
#   P4 Muse-Glimmer-30B (Meta, Apache-2.0): gen level.dokumentumtipus, level.szerzodesklauzula, rag.valaszbiralat
#   P5 Gemma: check (gemma) level.dokumentumtipus, level.szerzodesklauzula, rag.valaszbiralat
#   P7 Gemma: a „hiányzó feltétel” X pótlása (levéltriage, hivatali ügytípus; seq 1300–MP_N-1)
#   P9 Llama: ugyanez tartalékként, ha a Muse a validáláson elbukik (2026-10-10: elbukott; a Llama is, X-en 0,45)
#   P10 Muse: a levéltriage, az entitásegyezés és a hivatali ügytípus újragenerálása (Dani döntése, 2026-10-10)
#   P11 Gemma: ezek ellenőrzése. Ezzel a szintetikus generátor: Muse 6 család, Mistral 1; ellenőrző: Gemma mind.
#   P8 Muse: ellenőrző-validálás a val-on, utána a három Gemma-család ids-módú ellenőrzése (kiolvaso03 --prefix).
#      A Mistral a val-on X-en 38%, nem-X-en 60% átmenő arányt adott (Gemma: 87% / 82%), a szintetikus X-itemek
#      84–86%-át dobta el; ezért az ellenőrzője a Muse lesz, ha a validálás szabályán átmegy.
#   A tanított alany családja (Qwen) sem generátor, sem ellenőrző (Dani, 2026-10-10): a saját szövegén a bázis
#   eleve jó, és a Qwen-ellenőrző épp a bázisnak könnyű itemeket tartaná meg. A három korábbi Qwen-családot a Muse
#   generálja (Dani választása), így a szintetikus rész három független generátorcsaládra oszlik. A Muse csak
#   generál: a sablonja minden választ címzett-fejléccel és legalább „low” erősségű gondolkodással kezd, ezért az
#   egytokenes ellenőrzés nála nem megy. (Előtte a P3 Qwen-generálás volt; a gondolkodó módja 48 szekvenciával ~245
#   token/s-ot adott összesen, 6,5 óra alatt 118 kérés végzett.)
#   Szinonimaszűrés (4.3, szinonim03.py): a Mistral-bírálat a P1 végén, a Gemma-bírálat a P2-ben. (A Llama a P6-ban
#   opcionális: 2026-10-09-én a 72 890 párra 4–6 óra lett volna, ezért a második bíráló a Gemma.)
# Kapu: ha egy család generálási hibaaránya > 30%, a vezénylő megáll (promptjavítás kell).
# Leválasztva indítandó:  N=1300 nohup setsid bash kor03/eszkozok/f1_szint.sh > logs/f1_szint.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=F1SZ
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
N="${N:-1300}"
WORKERS="${WORKERS:-48}"          # kliensoldali párhuzamosság (a 16 mellett a Mistral ~140 token/s-ot adott, 0,5% KV)
export MISTRAL_SEQS="${MISTRAL_SEQS:-48}"
GEMMA_SEQS="${GEMMA_SEQS:-48}"
ONLY="${ONLY:-P1 P2 P3 P4}"
R="$EXP/kor03/eredmenyek/F1SZ"
mkdir -p "$R" "$EXP/kor03/adat/f1/szint"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"

gpu_containers() {  # csak a GPU-t használó konténer számít (egy letöltő vagy CPU-kliens nem)
  for c in $(docker ps -q); do [ "$(docker inspect -f '{{len .HostConfig.DeviceRequests}}' "$c")" != "0" ] && echo "$c"; done
}
for c in $(gpu_containers); do say "FUT MÁS GPU-KONTÉNER: $(docker inspect -f '{{.Name}}' "$c") — leállok"; exit 3; done

cpy() {  # a kliens a vLLM-image Pythonjával, GPU nélkül, a saját uid-del
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}

gemma_start() {
  docker rm -f ldh-gemma4 >/dev/null 2>&1 || true
  docker run -d --name ldh-gemma4 --gpus all -p 8440:8000 --ipc host \
    -v "$HOME/hf-cache-gemma4:/root/.cache/huggingface/hub" -e HF_HUB_OFFLINE=1 \
    "$SUBJECT_IMAGE" --model google/gemma-4-26B-A4B-it --served-model-name gemma4-26b \
    --max-model-len 8192 --gpu-memory-utilization 0.6 --max-num-seqs "$GEMMA_SEQS" --max-logprobs 64 \
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
gemma_stop() { docker logs ldh-gemma4 > "$1/ldh-gemma4.log" 2>&1 || true; docker rm -f ldh-gemma4 >/dev/null 2>&1 || true; }

# Muse-Glimmer-30B: a BF16 súlyokból dinamikus FP8 (dense 30B, a lépésenkénti súlyolvasás a korlát), a reasoning-parser
# leválasztja a to=self csatornát, így a content csak a válasz; képbemenet nincs
MUSE_SEQS="${MUSE_SEQS:-128}"
muse_start() {
  docker rm -f ldh-muse >/dev/null 2>&1 || true
  docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
    -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
    "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --served-model-name muse-glimmer-30b \
    --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 --max-num-seqs "$MUSE_SEQS" \
    --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
    --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null
  local t0; t0=$(date +%s)
  while [ $(( $(date +%s) - t0 )) -lt 2700 ]; do
    [ "$(docker inspect -f '{{.State.Running}}' ldh-muse 2>/dev/null)" != "true" ] && return 1
    curl -fsS http://127.0.0.1:8450/health >/dev/null 2>&1 && return 0
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 5 ] && { docker rm -f ldh-muse >/dev/null 2>&1; return 1; }
    sleep 15
  done
  return 2
}
muse_stop() { docker logs ldh-muse > "$1/ldh-muse.log" 2>&1 || true; docker rm -f ldh-muse >/dev/null 2>&1 || true; }

MISTRAL=(--url http://127.0.0.1:8430/v1 --model mistral-small-4 --extra '{"reasoning_effort": "none"}')
GEMMA=(--url http://127.0.0.1:8440/v1 --model gemma4-26b --extra '{"chat_template_kwargs": {"enable_thinking": false}}')
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
# ids-módú Muse-kiolvasás (P8): a válaszcsatorna kényszerítve, gondolkodás nélkül (kiolvaso03 --prefix)
MUSE_TOK="/hfm/hub/models--meta-models--Muse-Glimmer-30B/snapshots/$(basename "$(ls -d "$HOME"/hf-cache-muse/hub/models--meta-models--Muse-Glimmer-30B/snapshots/* 2>/dev/null | head -1)")"
MUSE_R=(--mode ids --url http://127.0.0.1:8450 --model muse-glimmer-30b --tokenizer "$MUSE_TOK" --perms 0
        --prefix " to=user<|message|>" --chat-kwargs '{"reasoning_strength": "low"}' --concurrency 64)
MP_N="${MP_N:-1430}"   # P7: a „hiányzó feltétel” tervek a seq 1300…MP_N-1 tartományban (szint03 MP_START)
kpy() {  # a kiolvasó a vLLM-image-ben, GPU nélkül, a Muse-tokenizerrel (/hfm)
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -v "$HOME/hf-cache-muse:/hfm:ro" -e HF_HUB_OFFLINE=1 -e LDH_EXP=/exp -e HOME=/tmp -e PYTHONUNBUFFERED=1 \
    "$SUBJECT_IMAGE" "$@"
}
muse_olvas() {  # muse_olvas <címke> <itemek> <kimenet>
  done_marker "muse-$1" && return 0
  say "Muse-kiolvasás: $1"
  kpy kor03/eszkozok/kiolvaso03.py --items "$2" --out "$3" "${MUSE_R[@]}" 2>&1 | tee -a "$R/muse-$1.log" | tail -2
  [ "${PIPESTATUS[0]}" = "0" ] || fail "Muse-kiolvasás $1"
  mark_ok "muse-$1"
}

gen() {  # gen <család> <modell-argok...>
  local fam="$1"; shift
  done_marker "gen-$fam-$N" && return 0
  say "gen $fam (N=$N)"
  cpy kor03/eszkozok/szint03.py gen --csalad "$fam" --n "$N" --workers "$WORKERS" "$@" 2>&1 | tee -a "$R/gen-$fam.log" | tail -3
  local hiba
  hiba=$(python3 -c "
import json
rs=[json.loads(l) for l in open('$EXP/kor03/adat/f1/szint/raw/$fam.jsonl')]
print(f'{sum(\"hiba\" in r for r in rs)/max(1,len(rs)):.3f}')")
  say "gen $fam kész, hibaarány $hiba"
  python3 -c "import sys; sys.exit(0 if float('$hiba') <= 0.30 else 1)" || fail "gen $fam: hibaarány $hiba > 0,30"
  mark_ok "gen-$fam-$N"
}

szinonim() {  # szinonim <tag> <modell-argok...>
  local tag="$1"; shift
  done_marker "szinonim-$tag" && return 0
  [ -f "$EXP/kor03/adat/f1/szinonim/parok.jsonl" ] || { say "szinonim: nincs parok.jsonl, kimarad"; return 0; }
  say "szinonimaszűrés ($tag)"
  cpy kor03/eszkozok/szinonim03.py biral --tag "$tag" --workers "$WORKERS" "$@" 2>&1 | tee -a "$R/szinonim-$tag.log" | tail -2
  mark_ok "szinonim-$tag"
}

check() {  # check <család> <tag> <modell-argok...>
  local fam="$1" tag="$2"; shift 2
  done_marker "check-$fam-$tag-$N" && return 0
  say "check $fam ($tag)"
  cpy kor03/eszkozok/szint03.py check --csalad "$fam" --tag "$tag" --workers "$WORKERS" "$@" 2>&1 | tee -a "$R/check-$fam-$tag.log" | tail -2
  mark_ok "check-$fam-$tag-$N"
}

record_env
if [[ " $ONLY " == *" P1 "* ]]; then
  say "P1: Mistral indul"
  mistral_start || fail "Mistral nem indult"
  gen rag.relevancia "${MISTRAL[@]}"
  [ "$N" -ge 1000 ] && szinonim mistral "${MISTRAL[@]}"
  mistral_stop "$R"
fi
if [[ " $ONLY " == *" P2 "* ]]; then
  say "P2: Gemma indul"
  gemma_start || fail "Gemma nem indult"
  gen entitas.egyezes "${GEMMA[@]}"
  gen jogi.hivatali_ugytipus "${GEMMA[@]}"
  gen level.triage "${GEMMA[@]}"
  check rag.relevancia gemma "${GEMMA[@]}"
  szinonim gemma "${GEMMA[@]}"
  gemma_stop "$R"
fi
if [[ " $ONLY " == *" P3 "* ]]; then
  say "P3: Mistral indul (ellenőrzés)"
  mistral_start || fail "Mistral nem indult"
  check entitas.egyezes mistral "${MISTRAL[@]}"
  check jogi.hivatali_ugytipus mistral "${MISTRAL[@]}"
  check level.triage mistral "${MISTRAL[@]}"
  mistral_stop "$R"
fi
if [[ " $ONLY " == *" P4 "* ]]; then
  t0=$(date +%s)  # a letöltés (logs/muse_letoltes.out) a végén „KÉSZ”-t ír
  until grep -q "^KÉSZ" "$EXP/logs/muse_letoltes.out" 2>/dev/null; do
    [ $(( $(date +%s) - t0 )) -gt 7200 ] && fail "a Muse letöltése 2 órán belül nem készült el"
    say "P4: vár a Muse letöltésére"; sleep 60
  done
  say "P4: Muse indul (generálás)"
  muse_start || fail "Muse nem indult"
  gen level.dokumentumtipus "${MUSE[@]}"
  gen level.szerzodesklauzula "${MUSE[@]}"
  gen rag.valaszbiralat "${MUSE[@]}"
  muse_stop "$R"
fi
if [[ " $ONLY " == *" P5 "* ]]; then
  say "P5: Gemma indul (ellenőrzés)"
  gemma_start || fail "Gemma nem indult"
  check level.dokumentumtipus gemma "${GEMMA[@]}"
  check level.szerzodesklauzula gemma "${GEMMA[@]}"
  check rag.valaszbiralat gemma "${GEMMA[@]}"
  gemma_stop "$R"
fi
if [[ " $ONLY " == *" P7 "* ]]; then
  say "P7: Gemma indul (hiányzó feltétel X, seq 1300–$((MP_N - 1)))"
  gemma_start || fail "Gemma nem indult"
  N_ALAP=$N; N=$MP_N
  gen level.triage "${GEMMA[@]}"
  gen jogi.hivatali_ugytipus "${GEMMA[@]}"
  N=$N_ALAP
  gemma_stop "$R"
fi
if [[ " $ONLY " == *" P8 "* ]]; then
  # a Muse mint ellenőrző (2026-10-10): előbb validálás a val forrás-goldján (ellenorzo_valid03.py), utána a három
  # Gemma-család minden iteme; a check_muse/ a döntés után kerül a check/-be (a Mistral-ellenőrzés helyére)
  say "P8: Muse indul (ellenőrző-validálás és ids-ellenőrzés)"
  muse_start || fail "Muse nem indult"
  muse_olvas val kor03/adat/f2/items_val.jsonl kor03/eredmenyek/F2/muse_val0.jsonl
  mkdir -p "$EXP/kor03/adat/f1/szint/check_raw"
  for fam in entitas.egyezes jogi.hivatali_ugytipus level.triage; do
    cpy kor03/eszkozok/szint03.py check_export --csalad "$fam" || fail "check_export $fam"
    muse_olvas "$fam" "kor03/adat/f1/szint/check_items/$fam.jsonl" "kor03/adat/f1/szint/check_raw/$fam.muse.jsonl"
    cpy kor03/eszkozok/szint03.py check_import --csalad "$fam" --tag muse \
      --src "kor03/adat/f1/szint/check_raw/$fam.muse.jsonl" || fail "check_import $fam"
  done
  muse_stop "$R"
fi
if [[ " $ONLY " == *" P9 "* ]]; then
  # tartalék ellenőrző (2026-10-10): a Muse a validálás szabályán elbukott (címketömeg 0,87, nem-X átmenő 0,53 a
  # Gemma 0,82-jével szemben). A Llama szűrhet (10. pont 1.): az ellenőrzés szűrés, a címke a tervből jön.
  say "P9: Llama indul (ellenőrző-validálás és ellenőrzés)"
  LLAMA_SEQS=32 llama_start || fail "Llama nem indult"
  LLAMA_R=(--mode chat --url http://127.0.0.1:8420 --model llama33-70b-fp8 --perms 0 --concurrency 32)
  llama_olvas() {  # llama_olvas <címke> <itemek> <kimenet>
    done_marker "llama-$1" && return 0
    say "Llama-kiolvasás: $1"
    cpy kor03/eszkozok/kiolvaso03.py --items "$2" --out "$3" "${LLAMA_R[@]}" 2>&1 | tee -a "$R/llama-$1.log" | tail -2
    [ "${PIPESTATUS[0]}" = "0" ] || fail "Llama-kiolvasás $1"
    mark_ok "llama-$1"
  }
  llama_olvas val kor03/adat/f2/items_val.jsonl kor03/eredmenyek/F2/llama_val0.jsonl
  for fam in entitas.egyezes jogi.hivatali_ugytipus level.triage; do
    llama_olvas "$fam" "kor03/adat/f1/szint/check_items/$fam.jsonl" "kor03/adat/f1/szint/check_raw/$fam.llama.jsonl"
    cpy kor03/eszkozok/szint03.py check_import --csalad "$fam" --tag llama \
      --src "kor03/adat/f1/szint/check_raw/$fam.llama.jsonl" || fail "check_import $fam"
  done
  llama_stop "$R"
fi
if [[ " $ONLY " == *" P10 "* ]]; then
  # Dani, 2026-10-10: a Muse és a Llama is elbukott az ellenőrző-validáláson, ezért a három Gemma-családot a Muse
  # generálja újra (a „hiányzó feltétel” tervekkel), és a Gemma ellenőrzi (P11), mint a többi Muse-családot
  say "P10: Muse indul (levéltriage, entitásegyezés, hivatali ügytípus újragenerálása)"
  muse_start || fail "Muse nem indult"
  gen entitas.egyezes "${MUSE[@]}"
  N_ALAP=$N; N=$MP_N
  gen level.triage "${MUSE[@]}"
  gen jogi.hivatali_ugytipus "${MUSE[@]}"
  N=$N_ALAP
  muse_stop "$R"
fi
if [[ " $ONLY " == *" P11 "* ]]; then
  say "P11: Gemma indul (a Muse-újragenerálás ellenőrzése)"
  gemma_start || fail "Gemma nem indult"
  check entitas.egyezes gemma "${GEMMA[@]}"
  N_ALAP=$N; N=$MP_N
  check level.triage gemma "${GEMMA[@]}"
  check jogi.hivatali_ugytipus gemma "${GEMMA[@]}"
  N=$N_ALAP
  gemma_stop "$R"
fi
if [[ " $ONLY " == *" P6 "* ]]; then
  say "P6: Llama indul (szinonimaszűrés)"
  LLAMA_SEQS=48 llama_start || fail "Llama nem indult"
  szinonim llama --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8
  llama_stop "$R"
fi
say "F1SZ kész ($ONLY)"
rm -f "$EXP/AKTIV_FAZIS"
touch "$R/DONE-$(echo "$ONLY" | tr ' ' '_')-$N"
