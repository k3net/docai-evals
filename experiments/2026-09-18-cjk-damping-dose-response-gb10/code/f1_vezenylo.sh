#!/usr/bin/env bash
# F1 — pilot három karon: K0, S05, A200, mind az öt műszeren.
#
# ⛔ A pilot NEM eredmény, hanem a protokoll validálása (runbook §6/F1). Utána a Kapu F1
# következik, és ott EL LEHET ELEGÁNSAN ÁLLNI. Ez a vezénylő ezért az F1 után
# SZÁNDÉKOSAN megáll — a maradék hat kart külön kell indítani, a kapu kiértékelése után.
#
# ⛔ 2026-09-18, MÁSODIK INDÍTÁS. Az első futás a párhuzamosság-kapun elhasalt
# (`eredmenyek/parhuzam-igazolas.txt`): a `parallel=6` kötegméret a `T7-08` itemen a
# PASS/FAIL-t is átbillentette. A remedy a runbook §6-ban megnevezett első ág: SOROS
# mérés. A kapu helyére a soros determinizmus igazolása lép — az olcsóbb és erősebb
# állítás, mert nem két mérés egyezését kéri, hanem azt, hogy a mérés önmagában
# reprodukálható legyen.
set -u
EX=$HOME/experiments/2026-09-18-cjk-csillapitas
SNAP=<base-snapshot>
URL=http://127.0.0.1:18355
say() { echo "[$(date +%H:%M:%S)] $*"; echo "$*" > "$EX/STATUS-F1"; }

# 0. Ha még fut egy korábbi kar-mérés, megvárjuk. A GPU-n egyszerre EGY kiszolgáló van.
say "várom az esetleg futó mérés végét"
for i in $(seq 1 600); do
  pgrep -f "kar_futtat.sh" | grep -qv "^$$\$" && { sleep 30; continue; }
  pgrep -f "src/harness.py" >/dev/null && { sleep 30; continue; }
  pgrep -f "kinai_proba.py" >/dev/null && { sleep 30; continue; }
  break
done
say "gép szabad"

# 1. K0 — a kontroll. Itt a csapda és a kínai próba 3× megy: ez a determinizmus
# bizonyítéka, nem zajátlagolás. Ha a kiszolgáló már fut, NEM töltjük be újra
# (egy betöltés ~6 perc, és a súlyok bitre ugyanazok).
if curl -sf "$URL/health" >/dev/null 2>&1; then K0MOD=ELO; else K0MOD="$SNAP"; fi
"$EX/eszkozok/kar_futtat.sh" K0 "$K0MOD" 3 3 5 || { say "HIBA: K0"; exit 1; }

# 2. ⛔ KAPU: a SOROS mérés determinizmusa, a kontroll teljes 150 itemén.
# Ha egy soros ismétlés sem tér el bájtra, akkor a további karokon az ismétlés
# elhagyható, és minden mért eltérés a MODELLBŐL jön. Ha eltér, megállunk: akkor a
# mérés felbontása az ingadozásnál finomabb nem lehet, és a §5 margóját újra kell
# gondolni, MIELŐTT nyolc kar lefutna.
say "determinizmus-igazolás: K0, 150 item × 3, sorosan"
python3 "$EX/eszkozok/determinizmus_ellenoriz.py" \
  "$EX/magyar-kie-eval/reports/csapda-K0.json" \
  > "$EX/eredmenyek/determinizmus-igazolas.txt" 2>&1
DRC=$?
tail -4 "$EX/eredmenyek/determinizmus-igazolas.txt"
if [ $DRC -ne 0 ]; then
  say "⛔ KAPU BUKOTT: a soros mérés sem reprodukálható — F1 LEÁLL"
  exit 1
fi
say "soros determinizmus igazolva"

# 3. A két további pilot kar — sorosan, ismétlés nélkül (a determinizmus igazolt)
"$EX/eszkozok/kar_futtat.sh" S05  /work/karok/S05  1 1 5 || { say "HIBA: S05";  exit 1; }
"$EX/eszkozok/kar_futtat.sh" A200 /work/karok/A200 1 1 5 || { say "HIBA: A200"; exit 1; }

say "F1 KÉSZ — most a Kapu F1 kiértékelése jön, F2 addig NEM indul"
