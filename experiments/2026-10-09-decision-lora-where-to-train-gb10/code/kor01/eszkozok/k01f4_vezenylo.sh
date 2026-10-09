#!/usr/bin/env bash
# K01F4 — a 01-es kör végső tesztje (01-runbook v1: 4., 6., 7. pont). Használat: k01f4_vezenylo.sh <szakasz>
#   smoke — az új utak próbája a val-on, a teszt érintése nélkül: adapter be/ki (s1, s2), L0n 40 itemen, S2 8 itemen,
#           két adapter + párhuzamos kiolvasás. Ha bukik, a teszt nem indul (lanc.sh).
#   teszt — 1. seed-őr: minden seed val-lef@95-je (`temp`) > L1★-é (nem választási szabály, csak őr);
#           2. T-új-eszköz tagság (szivargas.py --uj-eszkoz-x, a tényleges train ellen);
#           3. fő példány (LORA=1), sorosan, egy jelölővel: bázis val+teszt (4 perm.) → L3 s1 val+teszt (4 perm.) →
#              s2, s3 val+teszt (perm 0) → L0′ teszt (perm 0). A val itt olvasódik újra, így a τ és a temperature
#              ugyanabból a példányból jön, mint a teszt (a 00 F4 mintájára);
#           4. ugyanott (vagy újraindulás után friss példányon): L0n natív hívás (c = 16) és L3→S2 (c = 16) —
#              nem végzetes, hibájuk a HIBAK.txt-be kerül;
#           5. H4: öt friss példány (L3 ×2, BA ×2, mindkettő ×1: soros + c = 16 vegyes forgalom), a val-okon;
#              utána h4_egyezes.py — nem végzetes.
# Az elemzés (H1–H3, H5) a laptopon fut, a visszaszinkronizált kiolvasásokból. Idempotens; leválasztva indítandó
# (lanc.sh K01F3-megerosites K01F4-smoke; lanc.sh K01F4-smoke K01F4-teszt).
set -uo pipefail
SZAKASZ="${1:?szakasz: smoke | teszt}"
FAZIS="K01F4-$SZAKASZ"
cd "$(dirname "$0")/../.." && EXP="$(pwd)"
source eszkozok/lib.sh
K=kor01
D=$K/adat
E=$K/eszkozok
R="$EXP/$K/eredmenyek/F4"
V=$K/eredmenyek/F4/vllm
HD=$K/eredmenyek/F4/h4
mkdir -p "$R/vllm" "$R/h4" "$R/logs" "$R/smoke"
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

[ -f "$EXP/DONE-K01F3-megerosites" ] || fail "az F3 megerősítés nincs kész"
(cd $D && sha256sum -c f1s/atnezes/fagyasztas.sha256 > "$R/hash_ellenorzes_$SZAKASZ.txt" 2>&1) \
  || fail "az itemfájlok eltérnek a befagyasztott hash-től"
SEEDS=(k01_l3mixse_p30_s1 k01_l3mixse_p30_s2 k01_l3mixse_p30_s3)
BA=l3mixse_h2_s1          # a 00 publikált BA-adaptere (H4)
BA_VAL=adat/f1/f2_val.jsonl
for A in "${SEEDS[@]}"; do
  [ -f "ckpt/$A/vllm/adapter_model.safetensors" ] || fail "hiányzik a seed: $A"
  rm -rf "adapters/$A" && cp -r "ckpt/$A/vllm" "adapters/$A" || fail "$A adapter-másolás"
done
[ -f "adapters/$BA/adapter_model.safetensors" ] || fail "hiányzik a BA-adapter: adapters/$BA"
[ -f $D/f4_teszt.jsonl ] || cat $D/items_teszt.jsonl $D/f1s/items_katalogus.jsonl > $D/f4_teszt.jsonl

soft() { say "FIGYELEM: $1 — a lánc megy tovább"; echo "[$(date '+%F %T')] $FAZIS: $1" >> "$R/HIBAK.txt"; }
api() {  # api load|unload <név>
  local body
  [ "$1" = load ] && body="{\"lora_name\": \"$2\", \"lora_path\": \"/adapters/$2\"}" || body="{\"lora_name\": \"$2\"}"
  curl -fsS -X POST "http://127.0.0.1:$SUBJECT_PORT/v1/${1}_lora_adapter" -H 'Content-Type: application/json' -d "$body" \
    >> "$R/logs/lora_api.txt" 2>&1 && echo >> "$R/logs/lora_api.txt"
}
up() {  # up <logkönyvtár> — friss LoRA-s példány
  LORA=1 subject_start ldh-subject >> "$R/logs/subject.txt"
  subject_wait ldh-subject 1800 || { subject_stop ldh-subject "$1"; return 1; }
}
healthy() { curl -fsS "http://127.0.0.1:$SUBJECT_PORT/health" >/dev/null 2>&1; }
rd() {  # rd <kimenet> <items> <perms> <modell> [concurrency]
  py eszkozok/kiolvaso.py --items "$2" --out "$1.jsonl" --perms "$3" --model "$4" --concurrency "${5:-1}" \
    > "$R/logs/$(basename "$1").log" 2>&1
}

if [ "$SZAKASZ" = smoke ]; then
  S=$K/eredmenyek/F4/smoke
  head -n 40 $D/items_val.jsonl > $D/f4_smoke_val.jsonl
  say "K01F4 smoke: példány, adapter be/ki, L0n, S2, két adapter párhuzamosan" 3000
  up "$R/smoke" || fail "smoke: alany boot"
  for A in "${SEEDS[0]}" "${SEEDS[1]}"; do
    api load "$A" || { subject_stop ldh-subject "$R/smoke"; fail "smoke: $A betöltés"; }
    rd "$S/$A" $D/f4_smoke_val.jsonl 0 "$A" || { subject_stop ldh-subject "$R/smoke"; fail "smoke: $A kiolvasás"; }
    api unload "$A" || { subject_stop ldh-subject "$R/smoke"; fail "smoke: $A eltávolítás"; }
  done
  py $E/l0n_kiolvaso.py --items $D/f4_smoke_val.jsonl --out $S/l0n.jsonl > "$R/logs/smoke_l0n.log" 2>&1 \
    || { subject_stop ldh-subject "$R/smoke"; fail "smoke: L0n ($K/eredmenyek/F4/logs/smoke_l0n.log)"; }
  py $E/s2_kiolvaso.py --items $D/items_val.jsonl --l3-val $K/eredmenyek/F3/${SEEDS[0]}/vllm_val.jsonl \
    --l3-test $K/eredmenyek/F3/${SEEDS[0]}/vllm_val.jsonl --out $S/s2.jsonl --limit 8 > "$R/logs/smoke_s2.log" 2>&1 \
    || { subject_stop ldh-subject "$R/smoke"; fail "smoke: S2 ($K/eredmenyek/F4/logs/smoke_s2.log)"; }
  api load "${SEEDS[0]}" && api load "$BA" || { subject_stop ldh-subject "$R/smoke"; fail "smoke: két adapter betöltése"; }
  rd "$S/par_l3" $D/f4_smoke_val.jsonl 0 "${SEEDS[0]}" 4 & p1=$!
  head -n 40 $BA_VAL > $D/f4_smoke_ba.jsonl
  rd "$S/par_ba" $D/f4_smoke_ba.jsonl 0 "$BA" 4 & p2=$!
  rd "$S/par_bazis" $D/f4_smoke_val.jsonl 0 "$SUBJECT_MODEL" 4 & p3=$!
  wait $p1 && wait $p2 && wait $p3 || { subject_stop ldh-subject "$R/smoke"; fail "smoke: párhuzamos kiolvasás"; }
  subject_stop ldh-subject "$R/smoke"
  python3 - "$R/smoke" > "$R/smoke/ellenorzes.txt" 2>&1 <<'EOF' || fail "smoke: az ellenőrzés bukott ($K/eredmenyek/F4/smoke/ellenorzes.txt)"
import json, sys
from pathlib import Path
S = Path(sys.argv[1])
def rows(n): return [json.loads(l) for l in open(S / f"{n}.jsonl")]
ok = True
for n in ("k01_l3mixse_p30_s1", "k01_l3mixse_p30_s2", "par_l3", "par_ba", "par_bazis"):
    r = rows(n); good = len(r) == 40 and not any(x["missing"] for x in r)
    print(n, len(r), "ok" if good else "HIBA"); ok &= good
a, b = rows("k01_l3mixse_p30_s1"), rows("k01_l3mixse_p30_s2")
diff = sum(x["label_logprobs"] != y["label_logprobs"] for x, y in zip(a, b))
print("s1 ≠ s2 logprob (az unload/load tényleg cserél):", diff); ok &= diff > 0
l = rows("l0n"); nonx = [x for x in l if x["gold"] is not None]
known = sum(x["pred"] not in (None, "__ismeretlen__") for x in nonx) / max(1, len(nonx))
print("L0n: nem-X itemeken ismert névvel hívott:", round(known, 3)); ok &= len(l) == 40 and known >= 0.5
s = rows("s2"); va = sum(x["van_valasz"] for x in s) / max(1, len(s))
print("S2: válaszarány", round(va, 3), "n", len(s)); ok &= va >= 0.6
sys.exit(0 if ok else 1)
EOF
  say "K01F4 smoke kész" 0
  date '+%F %T' > "$EXP/DONE-$FAZIS"
  rm -f "$EXP/AKTIV_FAZIS"
  exit 0
fi
[ "$SZAKASZ" = teszt ] || fail "ismeretlen szakasz: $SZAKASZ"
[ -f "$EXP/DONE-K01F4-smoke" ] || fail "a smoke nincs kész"

# 1. seed-őr
if ! done_marker seed_or; then
  for A in "${SEEDS[@]}"; do
    [ -f $K/eredmenyek/F3/$A/val_elemzes.json ] || py $E/f3_val01.py --kar "$A" > "$R/logs/val_elemzes_$A.log" 2>&1 \
      || fail "val-elemzés: $A"
  done
  python3 - "${SEEDS[@]}" > "$R/seed_or.txt" 2>&1 <<'EOF' || fail "seed-őr: egy seed a val-on nem éri el az L1★-ot ($K/eredmenyek/F4/seed_or.txt)"
import json, sys
bad = []
for a in sys.argv[1:]:
    v = json.load(open(f"kor01/eredmenyek/F3/{a}/val_elemzes.json"))
    l1 = v["bazis"]["karok"][v["bazis"]["L1_csillag"]]["95"]["osszes"]["lef"]
    l3 = v["L3"]["karok"]["temp"]["95"]["osszes"]["lef"]
    print(f"{a}: L3 val lef@95 {l3:.4f} vs L1★ {l1:.4f}")
    bad += [a] if l3 <= l1 else []
sys.exit(1 if bad else 0)
EOF
  mark_ok seed_or
fi

# 2. T-új-eszköz
if ! done_marker uj_eszkoz; then
  say "K01F4 teszt: T-új-eszköz tagság (bge-m3)" 900
  py --gpu $E/szivargas.py --train-extra $D/f1s/items_eu180k.jsonl --uj-eszkoz-x > "$R/logs/uj_eszkoz.log" 2>&1 \
    || fail "T-új-eszköz ($K/eredmenyek/F4/logs/uj_eszkoz.log)"
  mark_ok uj_eszkoz
fi

# 3. fő példány
if ! done_marker fo; then
  say "K01F4 teszt: fő példány — bázis, L3 s1–s3 (val + teszt), L0′" 23000
  up "$R/logs" || fail "alany boot (fő)"
  rd $V/bazis_val $D/items_val.jsonl 0,1,2,3 "$SUBJECT_MODEL" || { subject_stop ldh-subject "$R/logs"; fail "bázis val"; }
  rd $V/bazis_test $D/f4_teszt.jsonl 0,1,2,3 "$SUBJECT_MODEL" || { subject_stop ldh-subject "$R/logs"; fail "bázis teszt"; }
  for k in 1 2 3; do
    A=${SEEDS[$((k - 1))]}; P=$([ $k = 1 ] && echo 0,1,2,3 || echo 0)
    say "K01F4 teszt: fő példány — L3 s$k (perm $P)" $(( (4 - k) * 5000 ))
    api load "$A" || { subject_stop ldh-subject "$R/logs"; fail "$A betöltés"; }
    rd $V/l3_s${k}_val $D/items_val.jsonl "$P" "$A" || { subject_stop ldh-subject "$R/logs"; fail "$A val"; }
    rd $V/l3_s${k}_test $D/f4_teszt.jsonl "$P" "$A" || { subject_stop ldh-subject "$R/logs"; fail "$A teszt"; }
    api unload "$A" || { subject_stop ldh-subject "$R/logs"; fail "$A eltávolítás"; }
  done
  rd $V/bazis_test_ism $D/f4_teszt.jsonl 0 "$SUBJECT_MODEL" || { subject_stop ldh-subject "$R/logs"; fail "L0′"; }
  mark_ok fo
fi

# 4. L0n és L3→S2 (nem végzetes)
if ! done_marker l0n || ! done_marker s2; then
  healthy || up "$R/logs" || fail "alany boot (L0n/S2)"
  if ! done_marker l0n; then
    say "K01F4 teszt: L0n natív hívás (c = 16)" 2400
    py $E/l0n_kiolvaso.py --items $D/f4_teszt.jsonl --out $V/l0n_test.jsonl > "$R/logs/l0n_test.log" 2>&1 \
      && mark_ok l0n || soft "L0n ($K/eredmenyek/F4/logs/l0n_test.log)"
  fi
  if ! done_marker s2; then
    say "K01F4 teszt: L3→S2 (bázis gondolkodó mód a τ alatti pool-itemeken, c = 16)" 7200
    py $E/s2_kiolvaso.py --items $D/f4_teszt.jsonl --l3-val $V/l3_s1_val.jsonl --l3-test $V/l3_s1_test.jsonl \
      --out $V/s2_test.jsonl > "$R/logs/s2_test.log" 2>&1 && mark_ok s2 || soft "S2 ($K/eredmenyek/F4/logs/s2_test.log)"
  fi
  subject_stop ldh-subject "$R/logs"
fi

# 5. H4 (nem végzetes)
h4() {
  local L3=${SEEDS[0]}
  for i in 1 2; do
    done_marker h4_l3_i$i && continue
    up "$R/h4" && api load "$L3" && rd $HD/l3_i$i $D/items_val.jsonl 0 "$L3" || { subject_stop ldh-subject "$R/h4"; return 1; }
    subject_stop ldh-subject "$R/h4"; mark_ok h4_l3_i$i
  done
  for i in 3 4; do
    done_marker h4_ba_i$i && continue
    up "$R/h4" && api load "$BA" && rd $HD/ba_i$i $BA_VAL 0 "$BA" || { subject_stop ldh-subject "$R/h4"; return 1; }
    subject_stop ldh-subject "$R/h4"; mark_ok h4_ba_i$i
  done
  if ! done_marker h4_i5; then
    up "$R/h4" && api load "$L3" && api load "$BA" || { subject_stop ldh-subject "$R/h4"; return 1; }
    rd $HD/l3_i5_soros $D/items_val.jsonl 0 "$L3" && rd $HD/ba_i5_soros $BA_VAL 0 "$BA" \
      || { subject_stop ldh-subject "$R/h4"; return 1; }
    rd $HD/l3_i5_par $D/items_val.jsonl 0 "$L3" 7 & p1=$!
    rd $HD/ba_i5_par $BA_VAL 0 "$BA" 4 & p2=$!
    rd $HD/bazis_i5_par $D/items_val.jsonl 0 "$SUBJECT_MODEL" 5 & p3=$!
    wait $p1 && wait $p2 && wait $p3 || { subject_stop ldh-subject "$R/h4"; return 1; }
    subject_stop ldh-subject "$R/h4"; mark_ok h4_i5
  fi
  py $E/h4_egyezes.py > "$R/logs/h4_egyezes.log" 2>&1
}
if ! done_marker h4; then
  say "K01F4 teszt: H4 — öt friss példány a val-okon (soros + c = 16)" 5400
  h4 && mark_ok h4 || soft "H4 ($K/eredmenyek/F4/h4/, logs/h4_egyezes.log)"
fi

say "K01F4 teszt kész$([ -f "$R/HIBAK.txt" ] && echo ' (figyelmeztetésekkel: HIBAK.txt)')" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
