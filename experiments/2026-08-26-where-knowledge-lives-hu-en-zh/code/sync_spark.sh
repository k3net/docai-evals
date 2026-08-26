#!/usr/bin/env bash
# Kód + korpusz + promptok a spark-devre. Modellsúlyok NEM mennek (azok a
# spark-dev ~/lang-study/hf cache-ében élnek), a results/ sem — az ott keletkezik.
set -euo pipefail
REMOTE="${1:-spark-dev}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ssh "$REMOTE" 'mkdir -p ~/lang-study/{src,data,logs,results,reports,results_instruct,reports_instruct}'
rsync -az --delete "$HERE/src/" "$REMOTE:~/lang-study/src/"
rsync -az "$HERE/items.jsonl" "$HERE/prompts.jsonl" "$REMOTE:~/lang-study/"
# a tuned lens tanítókorpusza (a Wikipédia-lekérés a laptopról megy, ott van internet)
[ -d "$HERE/data" ] && rsync -az "$HERE/data/" "$REMOTE:~/lang-study/data/"
echo "szinkronizálva → $REMOTE:~/lang-study/"
