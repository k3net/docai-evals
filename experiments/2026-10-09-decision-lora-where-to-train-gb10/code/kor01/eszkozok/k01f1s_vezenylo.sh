#!/usr/bin/env bash
# K01F1S — a 01-es kör F1-ének spark-része (01-runbook 4. pont, Napló 2026-10-06 „Spark kell még”):
#  1. Mistral Small 4: T-katalógus kérések (katalogus_kerdes.py gen) → itemek; EU-180k eszközlisták (eu180k.py);
#     szinonim-párok (szinonim.py parok) és a Mistral szinonim-bírálata
#  2. Llama-3.3-70B: szinonim-bírálat → döntés (szinonim.py dontes: az itemfájlok helyben, *.pre_szinonim mentéssel)
#     → címke-előszűrés (biralo01.py) a val, a teszt, a T-katalógus és az EU-180k itemjein
#  3. Mistral Small 4 újra: címke-előszűrés ugyanezeken (a szinonim-döntés UTÁNI itemeken)
#  4. szivárgás-audit (bge-m3, a ténylegesen használt train ellen) → 5. fagyasztás-jelölt hash
# Az alany NEM fut. Idempotens (lépésenkénti jelölők); leválasztva indítandó. Utána a laptopon: Dani címke-átnézése.
set -uo pipefail
FAZIS=K01F1S
cd "$(dirname "$0")/../.." && EXP="$(pwd)"
source eszkozok/lib.sh
K=kor01
E=$K/eszkozok
R="$EXP/$K/eredmenyek/F1S"
B=$K/eredmenyek/F1S/biralo
MEXTRA='{"reasoning_effort": "none"}'
MURL=http://127.0.0.1:8430/v1
LURL=http://127.0.0.1:8420/v1
mkdir -p "$R/biralo" "$R/logs" "$K/adat/f1s"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env
for f in items_train items_val items_teszt eu180k_hu_egyedi; do
  [ -f "$K/adat/$f.jsonl" ] || fail "hiányzik: $K/adat/$f.jsonl (sync.sh to01)"
done
[ -f "$K/katalogus/eszkozok.json" ] || fail "hiányzik a katalógus"
if ! done_marker bemenet; then
  (cd $K/adat && sha256sum items_train.jsonl items_val.jsonl items_teszt.jsonl eu180k_hu_egyedi.jsonl) > "$R/bemenet.sha256"
  mark_ok bemenet
fi
EVAL=(val:$K/adat/items_val.jsonl teszt:$K/adat/items_teszt.jsonl katalogus:$K/adat/f1s/items_katalogus.jsonl
      eu180k:$K/adat/f1s/items_eu180k.jsonl)

need() { for m in "$@"; do done_marker "$m" || return 0; done; return 1; }  # 0: van még tennivaló

# --- 1. Mistral: generálás, kinyerés, szinonim-bírálat ---------------------------------------------------
if need kat_gen kat_items eu parok szin_mistral; then
  say "K01F1S (1/5): Mistral Small 4 boot" 23000
  MISTRAL_SEQS=16 mistral_start || { rc=$?; mistral_stop "$R/logs"; fail "Mistral boot (rc=$rc)"; }
  if ! done_marker kat_gen; then
    say "K01F1S (1/5): T-katalógus kérések (14 eszköz × 8 stílus)" 21000
    py $E/katalogus_kerdes.py gen --url $MURL --model mistral-small-4 > "$R/logs/kat_gen.log" 2>&1 \
      || { mistral_stop "$R/logs"; fail "T-katalógus generálás ($R/logs/kat_gen.log)"; }
    n=$(wc -l < $K/adat/f1s/katalogus_keresek.jsonl)
    [ "$n" -ge 420 ] || { mistral_stop "$R/logs"; fail "kevés T-katalógus kérés: $n (< 420)"; }
    mark_ok kat_gen
  fi
  if ! done_marker kat_items; then
    py $E/katalogus_kerdes.py items > "$R/logs/kat_items.log" 2>&1 || { mistral_stop "$R/logs"; fail "T-katalógus itemek"; }
    mark_ok kat_items
  fi
  if ! done_marker eu; then
    say "K01F1S (1/5): EU-180k eszközlisták" 20000
    py $E/eu180k.py --url $MURL --model mistral-small-4 > "$R/logs/eu180k.log" 2>&1 \
      || { mistral_stop "$R/logs"; fail "EU-180k kinyerés ($R/logs/eu180k.log)"; }
    mark_ok eu
  fi
  if ! done_marker parok; then
    py $E/szinonim.py parok > "$R/logs/szin_parok.log" 2>&1 || { mistral_stop "$R/logs"; fail "szinonim-párok"; }
    mark_ok parok
  fi
  if ! done_marker szin_mistral; then
    say "K01F1S (1/5): szinonim-bírálat, Mistral (~24 ezer pár)" 18000
    py $E/szinonim.py biral --tag mistral --url $MURL --model mistral-small-4 --concurrency 16 --extra-body "$MEXTRA" \
      > "$R/logs/szin_mistral.log" 2>&1 || { mistral_stop "$R/logs"; fail "szinonim-bírálat, Mistral"; }
    mark_ok szin_mistral
  fi
  mistral_stop "$R/logs"
  mv "$R/logs/ldh-mistral.log" "$R/logs/ldh-mistral-1.log" 2>/dev/null
fi

# --- 2. Llama: szinonim-bírálat, döntés, címke-előszűrés ------------------------------------------------
if need szin_llama dontes bir_llama_val bir_llama_teszt bir_llama_katalogus bir_llama_eu180k; then
  say "K01F1S (2/5): Llama-3.3-70B boot" 15000
  LLAMA_SEQS=16 llama_start || { rc=$?; llama_stop "$R/logs"; fail "Llama boot (rc=$rc)"; }
  if ! done_marker szin_llama; then
    say "K01F1S (2/5): szinonim-bírálat, Llama (~24 ezer pár)" 13500
    py $E/szinonim.py biral --tag llama --url $LURL --model llama33-70b-fp8 --concurrency 16 \
      > "$R/logs/szin_llama.log" 2>&1 || { llama_stop "$R/logs"; fail "szinonim-bírálat, Llama"; }
    mark_ok szin_llama
  fi
  if ! done_marker dontes; then
    py $E/szinonim.py dontes --tags mistral,llama --max-hiany 50 > "$R/logs/szin_dontes.log" 2>&1 \
      || { llama_stop "$R/logs"; fail "szinonim-döntés ($R/logs/szin_dontes.log)"; }
    mark_ok dontes
  fi
  for spec in "${EVAL[@]}"; do
    nm=${spec%%:*}; f=${spec#*:}
    if ! done_marker bir_llama_$nm; then
      say "K01F1S (2/5): címke-előszűrés, Llama — $nm" 9000
      py $E/biralo01.py --items $f --out $B/llama_$nm.jsonl --url $LURL --model llama33-70b-fp8 --concurrency 16 \
        > "$R/logs/bir_llama_$nm.log" 2>&1 || { llama_stop "$R/logs"; fail "Llama-bíráló: $nm"; }
      mark_ok bir_llama_$nm
    fi
  done
  llama_stop "$R/logs"
fi

# --- 3. Mistral újra: címke-előszűrés -------------------------------------------------------------------
if need bir_mistral_val bir_mistral_teszt bir_mistral_katalogus bir_mistral_eu180k; then
  say "K01F1S (3/5): Mistral Small 4 boot (címke-előszűrés)" 6000
  MISTRAL_SEQS=16 mistral_start || { rc=$?; mistral_stop "$R/logs"; fail "Mistral boot 2 (rc=$rc)"; }
  for spec in "${EVAL[@]}"; do
    nm=${spec%%:*}; f=${spec#*:}
    if ! done_marker bir_mistral_$nm; then
      say "K01F1S (3/5): címke-előszűrés, Mistral — $nm" 3500
      py $E/biralo01.py --items $f --out $B/mistral_$nm.jsonl --url $MURL --model mistral-small-4 --concurrency 16 \
        --extra-body "$MEXTRA" > "$R/logs/bir_mistral_$nm.log" 2>&1 || { mistral_stop "$R/logs"; fail "Mistral-bíráló: $nm"; }
      mark_ok bir_mistral_$nm
    fi
  done
  mistral_stop "$R/logs"
  mv "$R/logs/ldh-mistral.log" "$R/logs/ldh-mistral-2.log" 2>/dev/null
fi

# --- 4. szivárgás-audit ---------------------------------------------------------------------------------
if ! done_marker szivargas; then
  say "K01F1S (4/5): szivárgás-audit (bge-m3)" 900
  py --gpu $E/szivargas.py > "$R/logs/szivargas.log" 2>&1 || fail "szivárgás-audit ($R/logs/szivargas.log)"
  mark_ok szivargas
fi

# --- 5. fagyasztás-jelölt hash --------------------------------------------------------------------------
if ! done_marker hash0; then
  (cd $K/adat && sha256sum items_train.jsonl items_val.jsonl items_teszt.jsonl f1s/items_katalogus.jsonl \
    f1s/items_eu180k.jsonl f1s/katalogus_keresek.jsonl) > "$R/fagyasztas_jelolt.sha256" || fail "hash"
  mark_ok hash0
fi

say "K01F1S kész — jöhet Dani címke-átnézése" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
