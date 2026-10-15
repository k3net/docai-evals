#!/usr/bin/env bash
# 03 F1-javítás (2026-10-10, Dani: „Mehet”): megvárja, hogy az éjszakai lánc a STOP-F2E-n megálljon (a Qwen
# eval-kiolvasása után), aztán az f1_szint.sh P7 (Gemma: „hiányzó feltétel” X) és P8 (Muse: ellenőrző-validálás és a
# három Gemma-család ellenőrzése) fázisa. Utána kézi döntés (ellenorzo_valid03.py), lezárás, a lánc folytatása.
#   nohup setsid bash kor03/eszkozok/f1_javitas.sh > logs/f1_javitas.out 2>&1 < /dev/null &
set -u
cd "$HOME/experiments/2026-10-03-lora-decision-head"
while pgrep -f "^bash kor03/eszkozok/f2_ejszaka.sh" >/dev/null; do sleep 60; done
echo "[$(date '+%F %T')] a lánc megállt, indul a P7–P8"
rm -f STATUS-F1SZ
N=1300 ONLY="P7 P8" WORKERS=96 bash kor03/eszkozok/f1_szint.sh > logs/f1_szint_p7p8.out 2>&1
echo "[$(date '+%F %T')] P7–P8 vége, kód $?"
