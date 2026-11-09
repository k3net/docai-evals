#!/usr/bin/env bash
# K05REL — a C, H és A kar megbízhatósági feje a D_meta-n, majd a döntési soraik a nem kitartott szeleteken
# (05-runbook 3.2, 7.). CPU-n (8 mag, 20 GB), hogy a GPU-n közben futhasson a JEV (k05jev_vezenylo.sh); a kész kar
# újraindításkor kimarad.
#   setsid nohup kor05/eszkozok/k05rel_vezenylo.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS=K05REL
LOG=logs/k05rel.log
JELL=cache/k05/jellemzok
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
log() { say "$@" >> "$LOG"; }
cpu() {
  docker run --rm --cpus 8 --memory 20g --network none --name "ldh-rel-$$-$RANDOM" -v "$EXP:/exp" \
    -v /etc/localtime:/etc/localtime:ro -e LDH_EXP=/exp -e OMP_NUM_THREADS=8 -e PYTHONUNBUFFERED=1 -e CUDA_VISIBLE_DEVICES= \
    -w /exp "$TOOL_IMAGE" python3 "$@"
}
hiba=0
for k in C H A; do
  rel=cache/k05/megbizhatosag/$k
  if [ ! -f "$rel/rel.json" ]; then
    log "$k: megbízhatósági fej a D_meta-n (3 seed × 2 LR)"
    cpu kor05/eszkozok/megbizhatosag05.py tanit --kar "$k" --fej "cache/k05/fejek/$k" --meta "$JELL/D_meta__kanonikus" \
      --out "$rel" >> "$LOG" 2>&1 || { log "$k: HIBA a tanításban"; hiba=1; continue; }
  fi
  for s in D_dev D_meta D_cal_prob D_cal_policy; do
    o=cache/k05/dontesek/$k/$s
    [ -f "$o/s73.jsonl" ] && continue
    log "$k: döntési sorok → $s"
    cpu kor05/eszkozok/megbizhatosag05.py dont --kar "$k" --fej "cache/k05/fejek/$k" --rel "$rel" \
      --be "$JELL/${s}__kanonikus" --out "$o" >> "$LOG" 2>&1 || { log "$k/$s: HIBA"; hiba=1; }
  done
  mkdir -p "kor05/eredmenyek/F3/megbizhatosag/$k"
  cp "$rel/rel.json" "kor05/eredmenyek/F3/megbizhatosag/$k/" 2>/dev/null
done
[ "$hiba" -eq 0 ] && date '+%F %T' > "DONE-$FAZIS" || echo "$(date '+%F %T')" > "FAILED-$FAZIS"
log "vége (hiba: $hiba)"
