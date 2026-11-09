#!/usr/bin/env bash
# K08G3 — a G3 (G1-rögzítés 4., 5., 10.): a G2 adatán a kinyerés, a lánc, a kiolvasás pecsét alatt, a 08-as fejek
# tanítása és a pontozás, végül a pecsét lezárása. **Csak a D12 rögzítése és a G2 auditjának alkalmazása után fut**
# (`kor08/rogzites/D12/manifest.json`, `kor08/adat/G2/ert_teszt/audit/ALKALMAZVA.json`). A G4 előtt csak darabszám és idő
# kerül naplóba; a pecsét alatti eredmény a G5 nyitásáig (`pecset08.kapu`) nem olvasható. Minden adat szintetikus.
#   1. kinyerés: az alany vLLM-en (LORA=0), egyszer; a kimenet hash-elve (bank és hiba séma 1, szabály séma 2)
#   2. a szabályalapú kinyerés (a K3-X-hez) és a lánc: G2F, G2K3, G2T valós kinyeréssel és orákulum-úton, G2F a
#      szabályalapú kinyeréssel is, G2N orákulum-úton (a tanítóminta)
#   3. kiolvasás két HF-folyamatban, mindkettő a determinizmus-őrrel és a gép állapotnaplójával (előtte vLLM futott):
#      a pecsét alá az értékelő szeletek, nyitottan a tanítóminta. Ha az őr jelez: egy rögzített ismétlés új
#      folyamatban; ha ott is jelez, a futás megáll (10.), a folytatásról Dani dönt.
#   4. a 08-as fejek (`b1rel08 tanit`: a láncos T500 orákulum-úton + a tanítóminta, 50–50%)
#   5. pontozás a pecsét alatt (a láncos szeletek a 08-as fejekkel; a lánc nélküli szeletek a 07 karjaival)
#   6. a pecsét lezárása (`pecset08 lezar`)
#   setsid nohup kor08/eszkozok/k08g3.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
FAZIS="K08G3"
R="$EXP/logs/k08g3"
mkdir -p "$R"
G3=kor08/adat/G3
K=$G3/kinyeres
KS=$G3/kinyeres_szabaly
PJ=cache/k08/pecset/jellemzok
PP=cache/k08/pecset/pontoz
JN=cache/k08/jellemzok_g3  # a tanítóminta saját, friss gyökere (az ismétlés a gyökér tartalmát teszi félre)
F8=cache/k08/fejek08
ALANY=ldh-alany08
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
declare -A SEMA=([penzugy.bankparositas]=1 [muszaki.hibaelharitas]=1 [szabaly.koltsegelszamolas]=2)
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
allapot() {
  { echo "== $(date '+%F %T') $1"; uptime; free -g | sed -n 2,3p
    nvidia-smi --query-gpu=driver_version,clocks.sm,power.draw,temperature.gpu --format=csv,noheader
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    docker ps -a --format '{{.Names}} {{.Status}}' | head -5; } >> "$R/allapot.log" 2>&1
}

# --- kapuk ---------------------------------------------------------------------------------------------------------------
[ -f kor08/rogzites/D12/manifest.json ] || { echo "$FAZIS: nincs D12-rögzítés" > "FAILED-$FAZIS"; exit 1; }
[ -f kor08/adat/G2/ert_teszt/audit/ALKALMAZVA.json ] || { echo "$FAZIS: a G2 auditja nincs alkalmazva" > "FAILED-$FAZIS"; exit 1; }
for d in "$PJ" "$JN"; do
  [ -d "$d" ] && ls "$d" | grep -q . && { echo "$FAZIS: $d nem üres; a G3 egyszer fut" > "FAILED-$FAZIS"; exit 1; }
done
python3 kor08/eszkozok/det_or08.py ref > "$R/det_ref.log" 2>&1 || { echo "$FAZIS: a determinizmus-őr referenciája hibás" > "FAILED-$FAZIS"; exit 1; }
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
record_env
allapot indulás
python3 kor08/eszkozok/pecset08.py nyit >> "$R/pecset.log" 2>&1 || fail "a pecsét nyitása"

# --- 1. kinyerés ---------------------------------------------------------------------------------------------------------
say "az alany indítása (vLLM, LORA=0)" 900
LORA=0 PREFIX=1 subject_start "$ALANY" >> "$R/alany.log" 2>&1
subject_wait "$ALANY" 1800 || fail "az alany nem állt fel"
say "kinyerés: G2F, G2K3, G2T" 10800
mkdir -p "$K"
for src in G2F G2K3 G2T; do
  for f in "${CSALADOK_08[@]}"; do
    python3 kor08/eszkozok/kinyer08.py --forras "$src" --csalad "$f" --sema "${SEMA[$f]}" --out "$K" >> "$R/kinyeres.log" 2>&1 \
      || fail "kinyerés $src $f"
  done
done
subject_stop "$ALANY" "$R"
sha256sum "$K"/*.jsonl > "$R/kinyeres.sha256"
allapot "a kinyerés után"
sleep 30

# --- 2. a szabályalapú kinyerés és a lánc ----------------------------------------------------------------------------------
say "a szabályalapú kinyerés és a lánc" 1800
python3 kor08/eszkozok/szabkin08.py --forras G2F --out "$KS" >> "$R/kinyeres.log" 2>&1 || fail "szabályalapú kinyerés"
mezok() {  # mezok <könyvtár> <forrás> <család>: a kinyerés a lánc bemenetévé
  python3 - "$1" "$2" "$3" > "$1/${2}_${3}.mezok.jsonl" <<'PY'
import json, sys
k, src, fam = sys.argv[1:4]
for x in open(f"{k}/{src}_{fam}.jsonl", encoding="utf-8"):
    r = json.loads(x)
    print(json.dumps({"id": r["id"], "mezok": r["mezok"]}, ensure_ascii=False))
PY
}
for f in "${CSALADOK_08[@]}"; do
  for src in G2F G2K3 G2T; do
    mezok "$K" "$src" "$f" || fail "mezők $src $f"
    python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$f" --ut kinyert --blokk v4 \
      --kinyeres "$K/${src}_$f.mezok.jsonl" --out "$G3/kinyert_$src" >> "$R/lanc.log" 2>&1 || fail "lánc kinyert $src $f"
    python3 kor08/eszkozok/lanc08.py futtat --forras "$src" --csalad "$f" --ut orakulum --blokk v4 \
      --out "$G3/orakulum_$src" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum $src $f"
  done
  mezok "$KS" G2F "$f" || fail "mezők szabályalapú $f"
  python3 kor08/eszkozok/lanc08.py futtat --forras G2F --csalad "$f" --ut kinyert --blokk v4 \
    --kinyeres "$KS/G2F_$f.mezok.jsonl" --out "$G3/szabaly_G2F" >> "$R/lanc.log" 2>&1 || fail "lánc szabályalapú $f"
  python3 kor08/eszkozok/lanc08.py futtat --forras G2N --csalad "$f" --ut orakulum --blokk v4 \
    --out "$G3/orakulum_G2N" >> "$R/lanc.log" 2>&1 || fail "lánc orákulum G2N $f"
done

# --- 3. kiolvasás a determinizmus-őrrel ------------------------------------------------------------------------------------
source kor07/eszkozok/lib07.sh
kiolvas() {  # kiolvas <címke> <out-root> <feladatok…>: egy HF-folyamat az őrrel; jelzésnél egy rögzített ismétlés
  local cimke="$1" root="$2"; shift 2
  local fel=("${DET_ELEJE[@]}" "$@" "${DET_VEGE[@]}") k
  for k in 1 2; do
    det_torol "$root"
    allapot "kiolvasás előtt ($cimke, $k.)"
    memoria_or07 "$R/memoria.log"
    py07 kor08/eszkozok/kiolvas08.py kivon "${fel[@]}" --out-root "$root" --status "STATUS-$FAZIS-$cimke" \
      >> "$R/kiolvasas_$cimke.log" 2>&1 || fail "kiolvasás $cimke"
    sleep 20
    allapot "kiolvasás után ($cimke, $k.)"
    det_ellenoriz "$root" "$R"
    [ -f "JELZES-DET-$FAZIS" ] || return 0
    cp "JELZES-DET-$FAZIS" "$R/JELZES-DET-$cimke-$k"
    [ "$k" = 2 ] && fail "a determinizmus-őr az ismétlésen is jelzett ($cimke); a folytatásról Dani dönt (10.)"
    say "a determinizmus-őr jelzett ($cimke): egy rögzített ismétlés új folyamatban" 60
    docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "mkdir -p /exp/$root.jelzes && mv /exp/$root/* /exp/$root.jelzes/" \
      >> "$R/archival.log" 2>&1 || fail "az eltérő kiolvasás félretétele ($cimke)"
  done
}
zart=()
for f in "${CSALADOK_08[@]}"; do
  for m in kanonikus b1; do
    zart+=(--feladat "lG2F:$f:CAL:$m" --feladat "lG2F:$f:TESZT:$m" --feladat "nG2F:$f:CAL:$m" --feladat "nG2F:$f:TESZT:$m"
           --feladat "lG2K3:$f:G2K3:$m" --feladat "oG2K3:$f:G2K3:$m" --feladat "nG2K3:$f:G2K3:$m" --feladat "lG2T:$f:G2T:$m")
  done
done
say "kiolvasás a pecsét alá (az értékelő szeletek)" 28800
kiolvas zart "$PJ" "${zart[@]}"
nyilt=()
for f in "${CSALADOK_08[@]}"; do
  for m in kanonikus b1; do nyilt+=(--feladat "oG2N:$f:G2N:$m"); done
done
say "kiolvasás: a tanítóminta (nyitott)" 7200
kiolvas nyilt "$JN" "${nyilt[@]}"

# --- 4. a 08-as fejek ------------------------------------------------------------------------------------------------------
say "a 08-as fejek tanítása" 3600
py kor08/eszkozok/b1rel08.py tanit --ert "oG2N_{csalad}_G2N" --ert-lanc "$G3/orakulum_G2N" --ert-jell "$JN" --out "$F8" --szalak 16 \
  >> "$R/tanit.log" 2>&1 || fail "a fejek tanítása"
sha256sum "$F8"/*/* "$F8"/fejek08.json > "$R/fejek08.sha256" 2>/dev/null

# --- 5. pontozás a pecsét alatt --------------------------------------------------------------------------------------------
say "pontozás a pecsét alatt" 3600
for f in "${CSALADOK_08[@]}"; do
  for x in "lG2F_${f}_CAL:kinyert_G2F" "lG2F_${f}_TESZT:kinyert_G2F" "lG2K3_${f}_G2K3:kinyert_G2K3" \
           "oG2K3_${f}_G2K3:orakulum_G2K3" "lG2T_${f}_G2T:kinyert_G2T"; do
    py kor08/eszkozok/b1rel08.py pontoz --szelet "${x%%:*}" --jell "$PJ" --lanc "$G3/${x#*:}" --fejek08 "$F8" --out "$PP" \
      --szalak 16 >> "$R/pontoz.log" 2>&1 || fail "pontozás ${x%%:*}"
  done
  for s in "nG2F_${f}_CAL" "nG2F_${f}_TESZT" "nG2K3_${f}_G2K3"; do
    py kor08/eszkozok/b1rel08.py pontoz --szelet "$s" --jell "$PJ" --lanc-nelkul --out "$PP" --szalak 16 \
      >> "$R/pontoz.log" 2>&1 || fail "pontozás $s"
  done
done

# --- 6. a pecsét lezárása --------------------------------------------------------------------------------------------------
python3 kor08/eszkozok/pecset08.py lezar --fazis "$FAZIS" >> "$R/pecset.log" 2>&1 || fail "a pecsét lezárása"
{ echo "$(date '+%F %T') a pecsét alatt:"; find cache/k08/pecset -type f | wc -l; } >> "$R/pecset.log"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
