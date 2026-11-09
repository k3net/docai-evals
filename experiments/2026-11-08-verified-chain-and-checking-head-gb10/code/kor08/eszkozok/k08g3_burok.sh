#!/usr/bin/env bash
# K08G3 burokkal (11-04; nem rögzített). A rögzített `k08g3.sh` változatlanul fut, a PATH elején a `burok_g3/python3`
# shimmel: a pecsét (`cache/k08/pecset`, root 700) a gazdagép python3-jából nem érhető el, ezért a `pecset08` és a
# `det_or08` a konténerben fut (az első indítás 19:00-kor a `pecset08 nyit`-on állt meg, a GPU-munka előtt). Előtte a
# rögzítés ellenőrzése és a pecsét kapuja a konténerből (a rögzített futtató `[ -d "$PJ" ]`-je a gazdagépről nem látja);
# utána a pecsét alatti fájlok száma a konténerből (a futtató `find`-ja a gazdagépről 0-t lát).
#   setsid nohup kor08/eszkozok/k08g3_burok.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
EXP="$(pwd)"
TOOL_IMAGE="${TOOL_IMAGE:-lora-train:2}"
L=logs/k08g3_burok.log
echo "[$(date '+%F %T')] burok indul" >> "$L"
python3 kor08/eszkozok/rogzit08.py ellenoriz >> "$L" 2>&1 || { echo "K08G3: a rögzítés ellenőrzése nem zöld" > FAILED-K08G3; exit 1; }
n=$(docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c 'ls -A /exp/cache/k08/pecset/jellemzok 2>/dev/null | wc -l')
echo "[$(date '+%F %T')] a pecsét alatti kiolvasás könyvtárában: $n bejegyzés" >> "$L"
[ "$n" = 0 ] || { echo "K08G3: a pecsét alatt már van kiolvasás ($n); a G3 egyszer fut" > FAILED-K08G3; exit 1; }
PATH="$EXP/kor08/eszkozok/burok_g3:$PATH" bash kor08/eszkozok/k08g3.sh
rc=$?
echo "[$(date '+%F %T')] a k08g3.sh kilépett: $rc" >> "$L"
if [ -f DONE-K08G3 ]; then
  m=$(docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c 'find /exp/cache/k08/pecset -type f | wc -l')
  echo "$(date '+%F %T') a pecsét alatt (a konténerből számolva): $m fájl" >> logs/k08g3/pecset.log
fi
exit $rc
