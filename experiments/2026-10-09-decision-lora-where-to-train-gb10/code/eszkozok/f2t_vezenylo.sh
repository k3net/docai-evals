#!/usr/bin/env bash
# F2/T — az F2 train-része előre, a val/teszt-átnézés alatt (2026-10-05): HF-kiolvasás a train-en (perm 0) +
# rejtett állapot (27., 40. réteg) az L2a-hoz. A train-itemeket az átnézés nem érinti (az `atnezes.py alkalmaz`
# csak a val/teszt fájlokat írja), ezért ez nem sérti a „befagyasztás előtt alany nem fut a val/teszten” szabályt.
# Az F2 vezénylő `hf_train` jelölőjét állítja be, így az F2 ezt a lépést kihagyja. Leválasztva indítandó.
set -uo pipefail
FAZIS=F2T
cd "$(dirname "$0")/.." && EXP="$(pwd)"
source eszkozok/lib.sh
R="$EXP/eredmenyek/F2"
D=adat/f1
mkdir -p "$R" cache/hidden
echo "$FAZIS" > "$EXP/AKTIV_FAZIS"
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"
heartbeat_start $$
record_env

if [ ! -f "$EXP/eredmenyek/F2/.ok/hf_train" ]; then
  sha256sum $D/items_train.jsonl > "$R/hf_train_items.sha256"
  say "F2T: HF a train-en (perm 0) + rejtett állapot az L2a-hoz" 5400
  py --gpu eszkozok/hf_kiolvaso.py --items $D/items_train.jsonl --out eredmenyek/F2/hf_train.jsonl --perms 0 \
    --hidden-layers 27,40 --hidden-out cache/hidden/train > "$R/hf_train.log" 2>&1 || fail "HF train (eredmenyek/F2/hf_train.log)"
  mkdir -p "$EXP/eredmenyek/F2/.ok" && date '+%F %T' > "$EXP/eredmenyek/F2/.ok/hf_train"
fi

say "F2T kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
rm -f "$EXP/AKTIV_FAZIS"
