#!/usr/bin/env bash
# F3 — a három új kar (2026-09-19, a felhasználó prioritása szerint):
#   S08  elég-e kisebb beavatkozás ugyanahhoz a csillapításhoz?   → mérendő
#   S09  még közelebb maradhatunk-e az eredeti modellhez?          → ha S08 jó
#   S06  hol kezd összeomlani a kínai; mekkora a tartalék S07 alatt → a tanulmányhoz
# Ugyanaz az építő és igazoló, mint a nyolc eredeti karé (karok_epit.sh).
# F0/3 — a nyolc foltozott snapshot előállítása és igazolása.
#
# A K0 a foltozatlan modell, azt nem kell előállítani. Minden kar EGYTENZOROS
# beavatkozás: csak a `lm_head.weight` célzott sorai változnak, minden más fájl
# szimlink marad, tehát az FP8 kvantálási állapot bitre érintetlen.
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
SNAP=<base-snapshot>
IMG=vllm-openai:beta-mirror-dev328
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-KAROK"; }

fut() {   # $1=kar  $2...=a patch_lm_head kapcsolói
  local kar=$1; shift
  say "kar építése: $kar"
  docker run --rm \
    -v "$HOME/.cache/huggingface:<hf-cache>:ro" \
    -v "$EX:/work" -w /work/eszkozok \
    --entrypoint python3 "$IMG" \
    patch_lm_head.py --snapshot "$SNAP" --celtokenek /work/eredmenyek/celtokenek.json \
      --out "/work/karok/$kar" --kar "$kar" "$@" \
    > "$EX/naplo/kar-epites-$kar.log" 2>&1
  local rc=$?
  [ $rc -ne 0 ] && { say "HIBA: $kar építése (rc=$rc)"; return $rc; }

  say "kar igazolása: $kar"
  docker run --rm \
    -v "$HOME/.cache/huggingface:<hf-cache>:ro" \
    -v "$EX:/work" -w /work/eszkozok \
    --entrypoint python3 "$IMG" \
    ellenoriz_kar.py --alap "$SNAP" --kar "/work/karok/$kar" \
      --celtokenek /work/eredmenyek/celtokenek.json \
    >> "$EX/naplo/kar-epites-$kar.log" 2>&1
  rc=$?
  [ $rc -ne 0 ] && { say "HIBA: $kar IGAZOLÁSA bukott (rc=$rc)"; return $rc; }
  say "$kar kész és igazolva"
}

MU=/work/eredmenyek/mu-h-A.json
fut S08   --maszk nyers      --forma szorzas --skala 0.8  --mu-h "$MU" || exit 1
fut S09   --maszk nyers      --forma szorzas --skala 0.9  --mu-h "$MU" || exit 1
fut S06   --maszk nyers      --forma szorzas --skala 0.6  --mu-h "$MU" || exit 1
say "MIND A HÁROM F3-KAR KÉSZ ÉS IGAZOLVA"
