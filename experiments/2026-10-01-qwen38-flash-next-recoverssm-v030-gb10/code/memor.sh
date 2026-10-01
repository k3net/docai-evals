#!/usr/bin/env bash
# MemAvailable-őr: 1 s-os minta -> eredmenyek/naplok/mem.tsv; 7 GiB alatt az r8-* konténerek leállítása.
OUT=~/experiments/round8/eredmenyek/naplok/mem.tsv
while true; do
  m=$(awk "/MemAvailable/{print int(\$2/1024)}" /proc/meminfo)
  c=$(docker ps --format "{{.Names}}" | grep "^r8-" | tr "\n" ",")
  echo -e "$(date +%s)\t$m\t$c" >> $OUT
  if [ "$m" -lt 7168 ] && [ -n "$c" ]; then echo -e "$(date -Is)\tSTOP MemAvailable=$m MiB" >> $OUT; docker ps --format "{{.Names}}" | grep "^r8-" | xargs -r docker stop; fi
  sleep 1
done
