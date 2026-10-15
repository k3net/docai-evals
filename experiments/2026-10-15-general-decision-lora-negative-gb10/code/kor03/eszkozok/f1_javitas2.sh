#!/usr/bin/env bash
# 03 F1-javítás, 2. kör (Dani, 2026-10-10: „Muse újragenerál”): a levéltriage, az entitásegyezés és a hivatali
# ügytípus Muse-újragenerálása (P10) és Gemma-ellenőrzése (P11), utána a második lezárás (ELLENORZO=gemma), amely a
# végén az éjszakai láncot is folytatja.
#   nohup setsid bash kor03/eszkozok/f1_javitas2.sh > logs/f1_javitas2.out 2>&1 < /dev/null &
set -u
cd "$HOME/experiments/2026-10-03-lora-decision-head"
rm -f STATUS-F1SZ
if N=1300 ONLY="P10 P11" WORKERS=128 MUSE_SEQS=128 bash kor03/eszkozok/f1_szint.sh > logs/f1_szint_p10p11.out 2>&1; then
  echo "[$(date '+%F %T')] P10–P11 kész, indul a második lezárás"
  ELLENORZO=gemma OK_SZOVEG="2026-10-10: a levéltriage, az entitásegyezés és a hivatali ügytípus a Muse-szal újragenerálva, Gemma-ellenőrzéssel (a Mistral-ellenőrzés az X-itemek 84–86%-át eldobta; a Muse és a Llama az ellenőrző-validáláson elbukott), a hiányzó feltétel X-szel; elemzés előtt" \
    bash kor03/eszkozok/f1_lezaras2.sh > logs/f1_lezaras2.out 2>&1
  echo "[$(date '+%F %T')] második lezárás vége, kód $?"
else
  echo "[$(date '+%F %T')] P10–P11 hibával állt le"
fi
