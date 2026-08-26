#!/usr/bin/env bash
# Kód + korpusz + promptok a spark-devre. Modellsúlyok NEM mennek (azok a
# spark-dev ~/lang-study/hf cache-ében élnek), a results/ sem — az ott keletkezik.
set -euo pipefail
REMOTE="${1:-spark-dev}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# A távoli munkakönyvtár a repó szerkezetét tükrözi (code/ + dataset/), hogy a
# szkriptek útjai a laptopon és a konténerben azonosak legyenek.
# ⛔ A mérési munkapéldány még lapos (src/ + gyökérben az adat), ezért a forrásoldalt
# ugyanúgy visszaeséssel oldjuk fel, mint a scope_paths.data() a Python-oldalon —
# különben ez a szkript a két példány közül mindig az egyikben elhasal.
CODE="$HERE/code"; [ -d "$CODE" ] || CODE="$HERE/src"
DATA="$HERE/dataset"; [ -d "$DATA" ] || DATA="$HERE"

ssh "$REMOTE" 'mkdir -p ~/lang-study/{code,dataset,data,logs,results,reports,results_instruct,reports_instruct}'
rsync -az --delete "$CODE/" "$REMOTE:~/lang-study/code/"
rsync -az "$DATA/items.jsonl" "$DATA/prompts.jsonl" "$REMOTE:~/lang-study/dataset/"
# a tuned lens tanítókorpusza (a Wikipédia-lekérés a laptopról megy, ott van internet)
[ -d "$HERE/data" ] && rsync -az "$HERE/data/" "$REMOTE:~/lang-study/data/"
echo "szinkronizálva → $REMOTE:~/lang-study/"
