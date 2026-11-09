#!/usr/bin/env bash
# 08-as kör — a futtatók közös kiegészítése (a lib.sh és a lib07.sh változatlan; ezek után source-olandó).
# Determinizmus-őr (Dani 11-03, `det_or08`): minden kiolvasás a rögzített referenciaszelettel indul és zárul, és a
# sorainak bitre egyezniük kell a referenciával; eltéréskor a futás jelez (`JELZES-DET-$FAZIS`), de nem áll le.
#   DET_ELEJE / DET_VEGE           a kiolvasás első és utolsó feladata (`kiolvas08 kivon "${DET_ELEJE[@]}" … "${DET_VEGE[@]}"`)
#   det_torol <jell>               az őr korábbi kimenete törlendő (a kész shardot a kiolvasás kihagyná; a cache root tulajdonú)
#   det_ellenoriz <jell> <napló>   összevetés a referenciával; eltéréskor jelzőfájl, a visszatérési érték mindig 0

DET_FAM=szabaly.koltsegelszamolas
DET_ELEJE=(--feladat "det0:$DET_FAM:T500:kanonikus")
DET_VEGE=(--feladat "det1:$DET_FAM:T500:kanonikus")

det_torol() {
  docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf /exp/$1/det0_* /exp/$1/det1_*"
}

det_ellenoriz() {
  rm -f "JELZES-DET-$FAZIS"
  if python3 kor08/eszkozok/det_or08.py ellenoriz --jell "$1" --out "$2/det_or.json" >> "$2/det_or.log" 2>&1; then
    echo "[$(date '+%F %T')] determinizmus-őr: bitre azonos" >> "$2/det_or.log"
    return 0
  fi
  { echo "$FAZIS $(date '+%F %T'): a kiolvasás a referenciaszeleten nem bitre azonos ($2/det_or.json)"
    tail -2 "$2/det_or.log"; } > "JELZES-DET-$FAZIS"
  return 0
}
