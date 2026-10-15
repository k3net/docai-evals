#!/usr/bin/env bash
# 03 F1 — második lezárás az ellenőrző-csere és a „hiányzó feltétel” pótlása után (2026-10-10), a spark-deven:
#   1. a három Gemma-család Mistral-ellenőrzése archívumba (check_elvetett/), helyére a validáláson átment ellenőrző
#      (ELLENORZO=llama|muse: check_<tag>/ → check/; gemma: a szint03 check már a check/-be írt)
#   2. szint03 final, szivárgás-audit, keverő
#   3. a megváltozott szintetikus rétegek újrafagyasztása (csak szintetikus, indokkal; elemzés előtt), ellenőrzés
#   4. összesítő, F2-itemlisták
#   5. az éjszakai lánc folytatása: a Qwen val/eval és a Gemma val jelölője törölve, hogy az új itemeket is olvassák
#      (a kiolvasó folytatható, a meglévő (id, perm) párokat nem olvassa újra); a Mistral val-kiolvasása nem fut újra
#   ELLENORZO=llama|muse|gemma [OK_SZOVEG="…"] nohup setsid bash kor03/eszkozok/f1_lezaras2.sh > logs/f1_lezaras2.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=F1L2
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
T="${ELLENORZO:?ELLENORZO=llama|muse|gemma kell}"
S=kor03/adat/f1/szint
R="$EXP/kor03/eredmenyek/F2"
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
lep() {  # lep <név> <szkript-argok...>
  say "lezárás 2: $1"; local n="$1"; shift
  cpy "$@" 2>&1 | tee -a "$R/zaras2.log" | tail -25
  [ "${PIPESTATUS[0]}" = "0" ] || fail "lezárás 2: $n"
}

mkdir -p "$S/check_elvetett"
for fam in entitas.egyezes jogi.hivatali_ugytipus level.triage; do
  [ -f "$S/check/$fam.mistral.jsonl" ] && mv "$S/check/$fam.mistral.jsonl" "$S/check_elvetett/"
  if [ "$T" = "gemma" ]; then  # a szint03 check közvetlenül a check/-be ír
    [ -f "$S/check/$fam.gemma.jsonl" ] || fail "hiányzik: $S/check/$fam.gemma.jsonl"
  else
    [ -f "$S/check_$T/$fam.$T.jsonl" ] || fail "hiányzik: $S/check_$T/$fam.$T.jsonl"
    cp "$S/check_$T/$fam.$T.jsonl" "$S/check/"
  fi
done
lep final kor03/eszkozok/szint03.py final
lep szivargas kor03/eszkozok/szivargas03.py
lep kevero kor03/eszkozok/kevero03.py
lep ujrafagyaszt kor03/eszkozok/befagyaszt03.py ujrafagyaszt --ok "${OK_SZOVEG:-2026-10-10: a Gemma-családok ellenőrzője Mistral helyett $T (a Mistral az X-itemek 84–86%-át eldobta), és a hiányzó feltétel X pótlása; elemzés előtt}"
lep ellenoriz kor03/eszkozok/befagyaszt03.py ellenoriz
cpy kor03/eszkozok/osszesito03.py 2>&1 | tee -a "$R/zaras2.log" | tail -3
[ "${PIPESTATUS[0]}" = "0" ] || echo "[$(date '+%F %T')] az összesítő hibát talált (zaras2.log)" >> "$R/HIBAK.txt"
lep itemek kor03/eszkozok/f2_itemek03.py
rm -f eredmenyek/F2E/.ok/olvas-qwen_val eredmenyek/F2E/.ok/olvas-qwen_eval eredmenyek/F2E/.ok/olvas-gemma_val STOP-F2E STATUS-F2E
touch "$R/DONE-zaras2"
say "lezárás 2 kész; az éjszakai lánc folytatása"
WAIT_FOR=kor03/eredmenyek/F2/DONE-zaras2 nohup setsid bash kor03/eszkozok/f2_ejszaka.sh > logs/f2_ejszaka2.out 2>&1 < /dev/null &
