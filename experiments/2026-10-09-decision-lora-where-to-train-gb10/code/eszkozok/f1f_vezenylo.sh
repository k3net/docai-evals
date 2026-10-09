#!/usr/bin/env bash
# F1/F — katalógus-duplikátumok kezelése Dani első 99 átnézett iteme után (2026-10-04, Napló): a 12 problémás
# címkéből 9 duplikátum (ugyanaz a termék két cikkszámon), 2 értelmetlen cikknév.
#   1. jelölt párok (bge-m3 koszinusz vagy közös szótő, számkompatibilis) és cikkek → adat/f1/dedup
#   2. Llama-3.3-70B, majd Mistral Small 4: páros duplikátum- (mindkét sorrend) és névbírálat, logprob igen/nem
#   3. döntés + kalibrációs kapu Dani döntésein (a 9 ismert duplikátum-párból ≥ 7)
#   4. archiválás (adat/f1_v2, eredmenyek/F1_v2), S7–S8 újra a duplikátum-kizárással (S1–S6 változatlan, seed 20261005)
#   5. shortcut- és nehézség-audit (kapu), hash-jelölt, a két bíráló a val/teszten (az új átnézési mintához)
# Idempotens; leválasztva indítandó.
set -uo pipefail
FAZIS=F1F
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
SEED=20261005
D=adat/f1
DD=$D/dedup
L="$EXP/eredmenyek/F1F"
R="$EXP/eredmenyek/F1"
EXTRA='{"reasoning_effort": "none"}'
SPLITS="val-belso val-szallito T-belso T-szallito T-kozeli T-tavoli"
mkdir -p "$DD" "$L"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f "$DD/kalibracio.json" ] || fail "hiányzik: $DD/kalibracio.json"

tomeg_ok() {  # tomeg_ok <summary.json> — a próba válasz-tokenjeinek medián tömege ≥ 0,5
  python3 -c "import json,sys; s=json.load(open('$1')); sys.exit(0 if s['valasz'] == s['n'] and (s['tomeg_median'] or 0) >= 0.5 else 1)"
}

if ! done_marker parok; then
  say "F1F: jelölt párok (bge-m3)" 15000
  py --gpu eszkozok/duplikatum_llm.py parok --gen $D --dir $DD > "$L/parok.log" 2>&1 || fail "jelölt párok (eredmenyek/F1F/parok.log)"
  mark_ok parok
fi

if ! done_marker llama_dup; then
  say "F1F: Llama boot (16 szekvencia)" 14500
  LLAMA_SEQS=16 llama_start || { rc=$?; llama_stop "$L"; fail "Llama boot (rc=$rc, eredmenyek/F1F/ldh-llama.log)"; }
  py eszkozok/duplikatum_llm.py biral --gen $D --dir $DD --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 \
    --tag llama_proba --limit 64 > "$L/llama_proba.log" 2>&1
  tomeg_ok "$DD/biral_llama_proba.summary.json" || { llama_stop "$L"; fail "Llama-próba: kevés igen/nem tömeg ($DD/biral_llama_proba.summary.json)"; }
  say "F1F: Llama — páros duplikátum- és névbírálat (~55 ezer kérés)" 13500
  py eszkozok/duplikatum_llm.py biral --gen $D --dir $DD --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 \
    --tag llama --concurrency 16 > "$L/llama_biral.log" 2>&1 || { llama_stop "$L"; fail "Llama-bírálat (eredmenyek/F1F/llama_biral.log)"; }
  llama_stop "$L"
  mark_ok llama_dup
fi

if ! done_marker mistral_dup; then
  say "F1F: Mistral boot (16 szekvencia)" 8500
  MISTRAL_SEQS=16 mistral_start || { rc=$?; mistral_stop "$L"; fail "Mistral boot (rc=$rc, eredmenyek/F1F/ldh-mistral.log)"; }
  py eszkozok/duplikatum_llm.py biral --gen $D --dir $DD --url http://127.0.0.1:8430/v1 --model mistral-small-4 \
    --tag mistral_proba --limit 64 --extra-body "$EXTRA" > "$L/mistral_proba.log" 2>&1
  tomeg_ok "$DD/biral_mistral_proba.summary.json" || { mistral_stop "$L"; fail "Mistral-próba: kevés igen/nem tömeg ($DD/biral_mistral_proba.summary.json)"; }
  say "F1F: Mistral — páros duplikátum- és névbírálat (~55 ezer kérés)" 8000
  py eszkozok/duplikatum_llm.py biral --gen $D --dir $DD --url http://127.0.0.1:8430/v1 --model mistral-small-4 \
    --tag mistral --concurrency 16 --extra-body "$EXTRA" > "$L/mistral_biral.log" 2>&1 \
    || { mistral_stop "$L"; fail "Mistral-bírálat (eredmenyek/F1F/mistral_biral.log)"; }
  mistral_stop "$L"
  mark_ok mistral_dup
fi

if ! done_marker dontes; then
  say "F1F: duplikátum-döntés + kalibrációs kapu" 5200
  py eszkozok/duplikatum_llm.py dontes --gen $D --dir $DD --tags llama,mistral > "$L/dontes.log" 2>&1 \
    || fail "duplikátum-döntés / kalibrációs kapu (eredmenyek/F1F/dontes.log, $DD/dontes_riport.json)"
  cp "$DD/dontes_riport.json" "$L/"
  mark_ok dontes
fi

if ! done_marker archiv; then
  [ -d adat/f1_v2 ] || cp -a $D adat/f1_v2 || fail "adat/f1 → adat/f1_v2 másolás"
  [ "$(ls adat/f1_v2/items_*.jsonl 2>/dev/null | wc -l)" = 7 ] || fail "adat/f1_v2 hiányos"
  mkdir -p eredmenyek/F1_v2
  for x in biralo audit; do  # a biralo.py id szerint folytat → a régi bírálat NEM maradhat a helyén
    if [ -d "eredmenyek/F1/$x" ] && [ ! -e "eredmenyek/F1_v2/$x" ]; then
      mv "eredmenyek/F1/$x" "eredmenyek/F1_v2/$x" || fail "eredmenyek/F1/$x archiválás"
    fi
  done
  [ -e eredmenyek/F1_v2/gen ] || cp -a eredmenyek/F1/gen eredmenyek/F1_v2/gen || fail "eredmenyek/F1/gen másolás"
  cp -a eredmenyek/F1/fagyasztas_jelolt.sha256 eredmenyek/F1_v2/ 2>/dev/null || true
  [ -e "eredmenyek/F1/biralo" ] && fail "eredmenyek/F1/biralo a helyén maradt"
  mkdir -p eredmenyek/F1/{biralo,audit,gen}
  echo "F1F: S7–S8 újra duplikátum-kizárással (seed $SEED); az F1C adat: adat/f1_v2, eredmenyek/F1_v2" >> "$EXP/eredmenyek/jegyzokonyv-spark.txt"
  mark_ok archiv
fi

if ! done_marker osszeallit; then
  say "F1F: S7–S8 újra (duplikátum-kizárás)" 4900
  py eszkozok/osszeallit.py --out $D --seed $SEED > "$R/gen/osszeallit.log" 2>&1 || fail "S7–S8 (eredmenyek/F1/gen/osszeallit.log)"
  cp $D/osszeallit_riport.json "$R/gen/"
  mark_ok osszeallit
fi

if ! done_marker audit; then
  say "F1F: shortcut- és nehézség-audit" 4600
  py eszkozok/auditok.py shortcut --gen $D --out eredmenyek/F1/audit > "$R/audit/shortcut.log" 2>&1 || fail "shortcut-audit"
  py eszkozok/auditok.py nehezseg --gen $D --out eredmenyek/F1/audit > "$R/audit/nehezseg.log" 2>&1 || fail "nehézség-audit"
  python3 -c "import json,sys; a=json.load(open('$R/audit/shortcut.json')); b=json.load(open('$R/audit/nehezseg.json')); sys.exit(0 if a['kapu_ok'] and b['kapu_ok_val_teszt'] else 1)" \
    || fail "audit-kapu nem teljesül (eredmenyek/F1/audit/shortcut.json, nehezseg.json)"
  mark_ok audit
fi

if ! done_marker hash0; then
  (cd $D && sha256sum items_*.jsonl s1_katalogus.jsonl s2_szallitok.json parok.jsonl s4_sorok.jsonl s6_jeloltek.jsonl dedup/duplikatumok.json) \
    > "$R/fagyasztas_jelolt.sha256" || fail "hash"
  mark_ok hash0
fi

if ! done_marker llama_vt; then
  say "F1F: Llama boot (val/teszt-bírálat)" 3600
  LLAMA_SEQS=16 llama_start || { rc=$?; llama_stop "$R/biralo"; fail "Llama boot (rc=$rc, eredmenyek/F1/biralo/ldh-llama.log)"; }
  for sp in $SPLITS; do
    say "F1F: Llama-bíráló — $sp" 2700
    py eszkozok/biralo.py --items $D/items_$sp.jsonl --out eredmenyek/F1/biralo/llama_$sp.jsonl \
      --url http://127.0.0.1:8420/v1 --model llama33-70b-fp8 --mode logprobs --concurrency 16 \
      > "$R/biralo/llama_$sp.log" 2>&1 || { llama_stop "$R/biralo"; fail "Llama-bíráló $sp"; }
  done
  llama_stop "$R/biralo"
  mark_ok llama_vt
fi

if ! done_marker mistral_vt; then
  say "F1F: Mistral boot (val/teszt-bírálat)" 1500
  MISTRAL_SEQS=16 mistral_start || { rc=$?; mistral_stop "$R/biralo"; fail "Mistral boot (rc=$rc, eredmenyek/F1/biralo/ldh-mistral.log)"; }
  for sp in $SPLITS; do
    say "F1F: Mistral-bíráló — $sp" 900
    py eszkozok/biralo.py --items $D/items_$sp.jsonl --out eredmenyek/F1/biralo/mistral_$sp.jsonl \
      --url http://127.0.0.1:8430/v1 --model mistral-small-4 --mode logprobs --concurrency 16 --extra-body "$EXTRA" \
      > "$R/biralo/mistral_$sp.log" 2>&1 || { mistral_stop "$R/biralo"; fail "Mistral-bíráló $sp"; }
  done
  mistral_stop "$R/biralo"
  mark_ok mistral_vt
fi

say "F1/F kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
