#!/usr/bin/env bash
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

MU=/work/eredmenyek/mu-h-A.json    # a termékközeli halmaz az elsődleges; a B az érzékenység-ellenőrzés

fut S07   --maszk nyers      --forma szorzas --skala 0.7  --mu-h "$MU" || exit 1
fut S05   --maszk nyers      --forma szorzas --skala 0.5  --mu-h "$MU" || exit 1
fut S03   --maszk nyers      --forma szorzas --skala 0.3  --mu-h "$MU" || exit 1
fut S01   --maszk nyers      --forma szorzas --skala 0.1  --mu-h "$MU" || exit 1
fut A200  --maszk nyers      --forma irany   --alpha 200  --mu-h "$MU" || exit 1
fut A050  --maszk nyers      --forma irany   --alpha 50   --mu-h "$MU" || exit 1
fut S05F  --maszk finomitott --forma szorzas --skala 0.5  --mu-h "$MU" || exit 1
fut A200F --maszk finomitott --forma irany   --alpha 200  --mu-h "$MU" || exit 1

say "MIND A NYOLC KAR KÉSZ ÉS IGAZOLVA"
