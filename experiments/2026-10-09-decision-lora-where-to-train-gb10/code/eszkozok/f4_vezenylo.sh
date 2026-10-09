#!/usr/bin/env bash
# F4 — végső teszt és „ugyanazon a példányon” (runbook 9. F4, 3. H1–H5, 6. pont, 8. pont).
# Előfeltétel: F3 megerősítés kész (eredmenyek/F3/hangolas_dontes.json → a konfig, seed 1–3).
#  1. vLLM fő példány (LORA=1), sorosan, ugyanazon a példányon: próba-ujjlenyomat → L0 (val + teszt, 4 perm.; ebből
#     az L1★) → L3 seed 1, 2, 3 (val + teszt, 4 perm.; adapterenként betöltés/eltávolítás) → L0′ (teszt, perm 0) →
#     teljesítmény (b), (c) → próba-ujjlenyomat. A val is itt olvasódik újra (user-döntés 2026-10-06), így τ és a
#     temperature ugyanabból a példányból jön, mint a teszt. Egyetlen jelölő: megszakadás után az egész blokk újrafut.
#  2. elemzés vLLM-en (H1, H2, H5) — f4_elemzes.py
#  3. HF: L0 a teszten (4 perm. + 40. réteg rejtett állapota) → L3 seedek (perm 0) → L0′ (perm 0) → L2a (apply);
#     a HF val-kiolvasások az F2/F3-ból (a HF determinisztikus).
#  4. elemzés HF-en (H1, H2, H4, H5)
#  5. H3 példányok: 5 friss `--enable-lora`-s (L0 + L3 seed 1) és 5 LoRA nélküli (L0) példány, 1000 itemes
#     teszt-részhalmaz, perm 0; az első LoRA nélküli példányon a teljesítmény (a).
#  6. H3 elemzés — f4_h3.py
#  7. eredménylap — f4_riport.py → eredmenyek/F4/eredmenylap.md (nem végzetes)
# Idempotens (lépésenkénti jelölők); leválasztva indítandó (lanc.sh F3-megerosites F4).
set -uo pipefail
FAZIS=F4
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
D=adat/f1
R="$EXP/eredmenyek/F4"
V=eredmenyek/F4/vllm
H=eredmenyek/F4/hf
P=eredmenyek/F4/h3
mkdir -p "$R/vllm" "$R/hf" "$R/h3" "$R/perf" cache/hidden
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f "$EXP/DONE-F3-megerosites" ] || fail "az F3 megerősítés nincs kész"
[ -f "$EXP/eredmenyek/F1/atnezes/FAGYASZTVA.json" ] || fail "az F1 nincs befagyasztva"
(cd $D && sha256sum -c "$EXP/eredmenyek/F1/atnezes/fagyasztas.sha256" > "$R/hash_ellenorzes.txt" 2>&1) \
  || fail "az item-fájlok eltérnek a befagyasztott hashtől"
KONFIG=$(python3 -c "import json;print(json.load(open('eredmenyek/F3/hangolas_dontes.json'))['konfig'])") \
  || fail "hiányzik: eredmenyek/F3/hangolas_dontes.json"
SEEDS=("${KONFIG}_s1" "${KONFIG}_s2" "${KONFIG}_s3")
for A in "${SEEDS[@]}"; do
  [ -d "ckpt/$A/final" ] && [ -d "ckpt/$A/vllm" ] && [ -f "eredmenyek/F3/$A/hf_val.jsonl" ] || fail "hiányzik a seed: $A"
done
printf '%s\n' "${SEEDS[@]}" > "$R/seedek.txt"
# őr (nem választási szabály): elromlott tréning ne nyissa meg a tesztet — minden seed vLLM val-lefedettsége@95 > L1★-é
python3 - "${SEEDS[@]}" > "$R/seed_or.txt" 2>&1 <<'EOF' || fail "seed-őr: egy seed a val-on nem éri el az L1★-ot ($R/seed_or.txt)"
import json, sys
f2 = json.load(open("eredmenyek/F2/L1_vllm_val.json"))
l1 = f2["karok"][f2["L1_csillag"]]["val"]["besorolasi_lefedettseg"]
bad = []
for a in sys.argv[1:]:
    v = json.load(open(f"eredmenyek/F3/{a}/L3_vllm_val.json"))["karok"]["temp"]["val"]["besorolasi_lefedettseg"]
    print(f"{a}: val lef@95 {v:.4f} (L1★ {l1:.4f})")
    bad += [a] if v <= l1 else []
sys.exit(1 if bad else 0)
EOF

# teszt-itemek: a négy réteg egy fájlban; részhalmazok seedelt mintával (H3: 1000, teljesítmény: 512)
if [ ! -f $D/f4_test.jsonl ]; then
  cat $D/items_T-belso.jsonl $D/items_T-szallito.jsonl $D/items_T-kozeli.jsonl $D/items_T-tavoli.jsonl > $D/f4_test.jsonl
  python3 - <<'EOF'
import random
rows = open("adat/f1/f4_test.jsonl").read().splitlines()
rng = random.Random(20261006)
pick = rng.sample(range(len(rows)), 1000)
open("adat/f1/f4_h3.jsonl", "w").write("\n".join(rows[k] for k in sorted(pick)) + "\n")
open("adat/f1/f4_perf.jsonl", "w").write("\n".join(rows[k] for k in sorted(pick[:512])) + "\n")
EOF
fi
sha256sum $D/f4_test.jsonl $D/f4_h3.jsonl $D/f4_perf.jsonl > "$R/f4_itemek.sha256"

lora_load() {  # lora_load <név> <logkönyvtár>
  rm -rf "adapters/$1" && cp -r "ckpt/$1/vllm" "adapters/$1" || return 1
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/load_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$1\", \"lora_path\": \"/adapters/$1\"}" >> "$2/lora_load.txt" 2>&1
}
lora_unload() {
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/unload_lora_adapter" -H 'Content-Type: application/json' \
    -d "{\"lora_name\": \"$1\"}" >> "$2/lora_load.txt" 2>&1
}
rd() {  # rd <kimenet> <log> kiolvaso-kapcsolók... — hiba esetén leállítja az alanyt és bukik
  local out="$1" log="$2"; shift 2
  py eszkozok/kiolvaso.py --out "$out" "$@" > "$log" 2>&1 || { subject_stop ldh-subject "$R"; fail "kiolvasás: $out ($log)"; }
}

# --- 1. vLLM fő példány ----------------------------------------------------------------------------------
if ! done_marker vllm_fo; then
  say "F4 (1/6): vLLM fő példány — L0, L3 × 3, L0′, teljesítmény" 15000
  rm -f "$R/lora_load.txt"
  LORA=1 subject_start ldh-subject
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R"; fail "alany boot (fő példány)"; }
  rd $V/probe_eleje.jsonl "$R/vllm_probe_eleje.log" --items adat/probe50.jsonl
  rd $V/l0_val.jsonl "$R/vllm_l0_val.log" --items $D/f2_val.jsonl --perms 0,1,2,3
  rd $V/l0_test.jsonl "$R/vllm_l0_test.log" --items $D/f4_test.jsonl --perms 0,1,2,3
  n=0
  for A in "${SEEDS[@]}"; do
    n=$((n + 1))
    lora_load "$A" "$R" || { subject_stop ldh-subject "$R"; fail "adapter-betöltés: $A ($R/lora_load.txt)"; }
    rd $V/l3_s${n}_val.jsonl "$R/vllm_l3_s${n}_val.log" --items $D/f2_val.jsonl --perms 0,1,2,3 --model "$A"
    rd $V/l3_s${n}_test.jsonl "$R/vllm_l3_s${n}_test.log" --items $D/f4_test.jsonl --perms 0,1,2,3 --model "$A"
    [ $n -lt 3 ] && { lora_unload "$A" "$R" || { subject_stop ldh-subject "$R"; fail "adapter-eltávolítás: $A"; }; }
  done
  rd $V/l0r_test.jsonl "$R/vllm_l0r_test.log" --items $D/f4_test.jsonl --perms 0
  # teljesítmény (b) LoRA-s példány, LoRA nélküli kérés; (c) lora_request (a 3. seed még betöltve)
  for c in 1 8 32; do
    rd eredmenyek/F4/perf/perf_lora_l0_c$c.jsonl "$R/perf_lora_l0_c$c.log" --items $D/f4_perf.jsonl --concurrency $c
    rd eredmenyek/F4/perf/perf_lora_l3_c$c.jsonl "$R/perf_lora_l3_c$c.log" --items $D/f4_perf.jsonl --concurrency $c \
      --model "${SEEDS[2]}"
  done
  rd $V/probe_vege.jsonl "$R/vllm_probe_vege.log" --items adat/probe50.jsonl
  subject_stop ldh-subject "$R"
  mark_ok vllm_fo
fi

# --- 2. elemzés vLLM-en -------------------------------------------------------------------------------
if ! done_marker elemzes_vllm; then
  say "F4 (2/6): elemzés vLLM-en (H1, H2, H5; 10 000 bootstrap)" 1500
  py eszkozok/f4_elemzes.py --motor vllm --l0-val $V/l0_val.jsonl --l0-test $V/l0_test.jsonl --l0r-test $V/l0r_test.jsonl \
    --l3 s1:$V/l3_s1_val.jsonl:$V/l3_s1_test.jsonl --l3 s2:$V/l3_s2_val.jsonl:$V/l3_s2_test.jsonl \
    --l3 s3:$V/l3_s3_val.jsonl:$V/l3_s3_test.jsonl --out eredmenyek/F4/vllm_f4.json \
    > "$R/elemzes_vllm.log" 2>&1 || fail "elemzés vLLM ($R/elemzes_vllm.log)"
  mark_ok elemzes_vllm
fi

# --- 3. HF -------------------------------------------------------------------------------------------
if ! done_marker hf_l0; then
  say "F4 (3/6): HF L0 a teszten (4 perm. + 40. réteg)" 6500
  py --gpu eszkozok/hf_kiolvaso.py --items $D/f4_test.jsonl --out $H/l0_test.jsonl --perms 0,1,2,3 \
    --hidden-layers 40 --hidden-out cache/hidden/test > "$R/hf_l0_test.log" 2>&1 || fail "HF L0 teszt"
  mark_ok hf_l0
fi
n=0
for A in "${SEEDS[@]}"; do
  n=$((n + 1))
  if ! done_marker hf_l3_s$n; then
    say "F4 (3/6): HF L3 seed $n ($A) a teszten" 2000
    py --gpu eszkozok/hf_kiolvaso.py --items $D/f4_test.jsonl --adapter "ckpt/$A/final" --perms 0 \
      --out $H/l3_s${n}_test.jsonl > "$R/hf_l3_s${n}_test.log" 2>&1 || fail "HF L3 seed $n"
    mark_ok hf_l3_s$n
  fi
done
if ! done_marker hf_l0r; then
  say "F4 (3/6): HF L0′ a teszten (perm 0)" 2000
  py --gpu eszkozok/hf_kiolvaso.py --items $D/f4_test.jsonl --perms 0 --out $H/l0r_test.jsonl \
    > "$R/hf_l0r_test.log" 2>&1 || fail "HF L0′"
  mark_ok hf_l0r
fi
if ! done_marker l2a; then
  py eszkozok/l2a_szonda.py apply --head eredmenyek/F2/l2a_L40/fej.pt --rows $H/l0_test.jsonl --hidden cache/hidden/test \
    --out $H/l2a_L40_test.jsonl > "$R/l2a_apply.log" 2>&1 || fail "L2a apply"
  mark_ok l2a
fi

# --- 4. elemzés HF-en ---------------------------------------------------------------------------------
if ! done_marker elemzes_hf; then
  say "F4 (4/6): elemzés HF-en (H1, H2, H4, H5)" 1500
  py eszkozok/f4_elemzes.py --motor hf --l0-val eredmenyek/F2/hf_val.jsonl --l0-test $H/l0_test.jsonl \
    --l0r-test $H/l0r_test.jsonl --l3 "s1:eredmenyek/F3/${SEEDS[0]}/hf_val.jsonl:$H/l3_s1_test.jsonl" \
    --l3 "s2:eredmenyek/F3/${SEEDS[1]}/hf_val.jsonl:$H/l3_s2_test.jsonl" \
    --l3 "s3:eredmenyek/F3/${SEEDS[2]}/hf_val.jsonl:$H/l3_s3_test.jsonl" \
    --l2a eredmenyek/F2/l2a_L40/val.jsonl:$H/l2a_L40_test.jsonl --out eredmenyek/F4/hf_f4.json \
    > "$R/elemzes_hf.log" 2>&1 || fail "elemzés HF ($R/elemzes_hf.log)"
  mark_ok elemzes_hf
fi

# --- 5. H3: friss példányok -----------------------------------------------------------------------------
for k in 1 2 3 4 5; do
  if ! done_marker h3_lora_k$k; then
    say "F4 (5/6): H3 friss példány $k/5 LoRA-val" 900
    LORA=1 subject_start ldh-subject
    subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R"; fail "alany boot (H3 lora $k)"; }
    rd $P/lora_k${k}_probe.jsonl "$R/h3_lora_k${k}_probe.log" --items adat/probe50.jsonl
    rd $P/lora_k${k}_l0.jsonl "$R/h3_lora_k${k}_l0.log" --items $D/f4_h3.jsonl
    lora_load "${SEEDS[0]}" "$R" || { subject_stop ldh-subject "$R"; fail "adapter-betöltés (H3 $k)"; }
    rd $P/lora_k${k}_l3.jsonl "$R/h3_lora_k${k}_l3.log" --items $D/f4_h3.jsonl --model "${SEEDS[0]}"
    subject_stop ldh-subject "$R"
    mark_ok h3_lora_k$k
  fi
done
for k in 1 2 3 4 5; do
  if ! done_marker h3_nolora_k$k; then
    say "F4 (5/6): H3 friss példány $k/5 LoRA nélkül" 900
    LORA=0 subject_start ldh-subject
    subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$R"; fail "alany boot (H3 LoRA nélkül $k)"; }
    rd $P/nolora_k${k}_probe.jsonl "$R/h3_nolora_k${k}_probe.log" --items adat/probe50.jsonl
    rd $P/nolora_k${k}_l0.jsonl "$R/h3_nolora_k${k}_l0.log" --items $D/f4_h3.jsonl
    if [ $k = 1 ]; then  # teljesítmény (a): LoRA nélküli példány
      for c in 1 8 32; do
        rd eredmenyek/F4/perf/perf_nolora_c$c.jsonl "$R/perf_nolora_c$c.log" --items $D/f4_perf.jsonl --concurrency $c
      done
    fi
    subject_stop ldh-subject "$R"
    mark_ok h3_nolora_k$k
  fi
done

# --- 6. H3 elemzés ------------------------------------------------------------------------------------
if ! done_marker h3; then
  py eszkozok/f4_h3.py --dir eredmenyek/F4 --out eredmenyek/F4/h3.json > "$R/h3.log" 2>&1 || fail "H3 elemzés ($R/h3.log)"
  mark_ok h3
fi

# --- 7. eredménylap (runbook 14. pont); nem végzetes: a mérések ettől érvényesek ---------------------------
if ! done_marker riport; then
  if py eszkozok/f4_riport.py --dir eredmenyek/F4 > "$R/riport.log" 2>&1; then
    mark_ok riport
  else
    say "figyelmeztetés: az eredménylap nem készült el ($R/riport.log); a mérések rendben"
  fi
fi

say "F4 kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
