#!/usr/bin/env bash
# K08G5 burokkal (11-05; nem rögzített). A rögzített `k08g5.sh` változatlanul fut, a PATH elején a `burok_g3/python3`
# shimmel: a `pecset08 ellenoriz` a gazdagép python3-jából nem éri el a pecsétet (root 700), a konténerből igen. Az
# elemzők a `py`-jal amúgy is a konténerben futnak. Előtte a rögzítés ellenőrzése és a G4 manifestje; a nyitási engedélyt
# (`kor08/rogzites/G5/NYITAS.json`) a `k08g5.sh` maga nézi. **Csak Dani nyitási engedélye után indítható.**
#   setsid nohup kor08/eszkozok/k08g5_burok.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
EXP="$(pwd)"
L=logs/k08g5_burok.log
echo "[$(date '+%F %T')] burok indul" >> "$L"
python3 kor08/eszkozok/rogzit08.py ellenoriz >> "$L" 2>&1 || { echo "K08G5: a rögzítés ellenőrzése nem zöld" > FAILED-K08G5; exit 1; }
[ -f kor08/rogzites/pecset/K08G3.g4.json ] || { echo "K08G5: nincs G4-manifest" > FAILED-K08G5; exit 1; }
PATH="$EXP/kor08/eszkozok/burok_g3:$PATH" bash kor08/eszkozok/k08g5.sh
rc=$?
echo "[$(date '+%F %T')] a k08g5.sh kilépett: $rc" >> "$L"
exit $rc
