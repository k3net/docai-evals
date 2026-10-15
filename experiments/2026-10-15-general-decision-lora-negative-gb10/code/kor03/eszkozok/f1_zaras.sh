#!/usr/bin/env bash
# 03 F1 — lezárás a laptopon, a spark-dev F1SZ-futása után (03-runbook 8.):
#   1. a szintetikus nyers és ellenőrző kimenetek és a szinonim-bírálatok lehúzása;
#   2. szint03 final (az ellenőrzőn átment itemek), szinonim03 dontes (Mistral + Gemma);
#   3. szivárgás-audit az új itemekkel, keverő (a szinonim-döntésekkel és a kizárásokkal), befagyasztás (a
#      szintetikus teszt-ID is), összesítő.
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=kor01/.venv/bin/python
REMOTE=spark-dev:experiments/2026-10-03-lora-decision-head
rsync -a "$REMOTE/kor03/adat/f1/szint/raw/" kor03/adat/f1/szint/raw/
rsync -a "$REMOTE/kor03/adat/f1/szint/check/" kor03/adat/f1/szint/check/
rsync -a "$REMOTE/kor03/adat/f1/szinonim/" kor03/adat/f1/szinonim/ --exclude parok.jsonl
rsync -a "$REMOTE/kor03/eredmenyek/F1SZ/" kor03/eredmenyek/F1SZ/
$PY kor03/eszkozok/szint03.py final
$PY kor03/eszkozok/szinonim03.py dontes --tags mistral,gemma
$PY kor03/eszkozok/szivargas03.py | head -8
$PY kor03/eszkozok/kevero03.py
$PY kor03/eszkozok/befagyaszt03.py fagyaszt --szint
$PY kor03/eszkozok/befagyaszt03.py ellenoriz
$PY kor03/eszkozok/osszesito03.py
