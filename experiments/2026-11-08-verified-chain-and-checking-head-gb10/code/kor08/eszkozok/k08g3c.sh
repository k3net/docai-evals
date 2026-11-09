#!/usr/bin/env bash
# K08G3 folytatása R-módban (11-05, Dani: „1-es legyen”; nem rögzített; a G1-rögzítés 10. pontja szerinti döntés). A
# rögzített `k08g3.sh` 3–6. lépése változatlan parancsokkal, a kész és hash-elt kinyerésre és láncra (a vLLM nem fut
# újra). Az eltérés csak a kiolvasás indításában van: a K08G3DIAG szerint a HF-kiolvasás folyamatonként egy diszkrét
# numerikai módba kerül, azon belül bitre determinisztikus. Ezért minden kiolvasás friss folyamatban indul, és amint az
# első feladata, a referenciaszelet (det0) kész, a rögzített `det_or08` összeveti a referenciával:
#   - ha nem bitre azonos: a folyamat leáll, a részkimenete olvasatlanul félre (a zárt kiolvasásé a pecsét alatt), és új
#     folyamat indul (legfeljebb PROBA);
#   - ha az: a kiolvasás végigmegy, a végén a rögzített őr (det0 + det1) dönt, ahogy a `k08g3.sh`-ban.
# A mód így egyetlen értékelő item kiolvasása előtt, csak a referenciaszeleten dől el. A pecsétet érintő hívások a
# `burok_g3/python3` shimmel a konténerben. Az éjszakai két kísérlet (A és B mód) olvasatlanul a pecsét alatt marad
# (`arch_zart1_A`, `arch_zart2_B`).
#   setsid nohup kor08/eszkozok/k08g3c.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor08/eszkozok/lib08.sh
source kor07/eszkozok/lib07.sh
export PATH="$EXP/kor08/eszkozok/burok_g3:$PATH"
FAZIS="K08G3"
R="$EXP/logs/k08g3"
G3=kor08/adat/G3
PJ=cache/k08/pecset/jellemzok
PP=cache/k08/pecset/pontoz
JN=cache/k08/jellemzok_g3
F8=cache/k08/fejek08
CSALADOK_08=(penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas)
PROBA=6
DETD=det0_szabaly.koltsegelszamolas_T500__kanonikus
L="$R/folytatas.log"
lep() { echo "[$(date '+%F %T')] $*" >> "$L"; }
kapu() { lep "KAPU: $*"; echo "[$(date '+%F %T')] $FAZIS (folytatás): $*" > "FAILED-$FAZIS"; exit 1; }
konti() { docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "$1"; }
allapot() {
  { echo "== $(date '+%F %T') $1"; uptime; free -g | sed -n 2,3p
    nvidia-smi --query-gpu=driver_version,clocks.sm,power.draw,temperature.gpu --format=csv,noheader
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    docker ps -a --format '{{.Names}} {{.Status}}' | head -5; } >> "$R/allapot.log" 2>&1
}

# --- kapuk ---------------------------------------------------------------------------------------------------------------
lep "folytatás indul"
[ -f "DONE-$FAZIS" ] && kapu "a K08G3 már kész"
[ -f kor08/rogzites/D12/manifest.json ] || kapu "nincs D12-rögzítés"
[ -f kor08/adat/G2/ert_teszt/audit/ALKALMAZVA.json ] || kapu "a G2 auditja nincs alkalmazva"
[ -f AKTIV_FAZIS ] && kapu "fut egy fázis ($(cat AKTIV_FAZIS))"
docker ps --format '{{.Names}}' | grep -q . && kapu "fut egy konténer"
python3 kor08/eszkozok/rogzit08.py ellenoriz >> "$L" 2>&1 || kapu "a rögzítés ellenőrzése nem zöld"
sha256sum -c --quiet "$R/kinyeres.sha256" >> "$L" 2>&1 || kapu "a kinyerés hash-e eltér"
for d in kinyert_G2F kinyert_G2K3 kinyert_G2T orakulum_G2F orakulum_G2K3 orakulum_G2T orakulum_G2N szabaly_G2F; do
  [ -d "$G3/$d/items" ] || kapu "hiányzó lánc: $d"
done
find "$G3"/kinyert_* "$G3"/orakulum_* "$G3"/szabaly_G2F -type f | sort | xargs sha256sum > "$R/lanc.sha256"
[ -e "$JN" ] && kapu "$JN már létezik"
[ -e "$F8" ] && kapu "$F8 már létezik"
n=$(konti "ls -A /exp/$PP 2>/dev/null | wc -l; ls -d /exp/cache/k08/pecset/arch_zart1_A /exp/cache/k08/pecset/arch_zart2_B 2>/dev/null | wc -l" | paste -sd' ')
[ "$n" = "0 0" ] || kapu "a pecsét alatt már van pontozás vagy archívum ($n)"
python3 kor08/eszkozok/det_or08.py ref >> "$L" 2>&1 || kapu "a determinizmus-őr referenciája hibás"
cp "$R/det_or.json" "$R/det_or_k08g3_zart2.json" 2>/dev/null

rm -f "FAILED-$FAZIS"
echo "$FAZIS (folytatás) $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$
record_env
allapot "folytatás indul"
konti "set -e; cd /exp/cache/k08/pecset; mv jellemzok arch_zart2_B; mv jellemzok.jelzes arch_zart1_A" >> "$L" 2>&1 \
  || fail "az éjszakai kísérletek archiválása"
lep "az éjszakai két kísérlet a pecsét alatt: arch_zart1_A, arch_zart2_B (olvasatlanul)"
python3 kor08/eszkozok/pecset08.py nyit >> "$R/pecset.log" 2>&1 || fail "a pecsét újranyitása"

# --- 3. kiolvasás R-módban -------------------------------------------------------------------------------------------------
kiolvas_r() {  # kiolvas_r <címke> <out-root> <archív-előtag> <feladatok…>
  local cimke="$1" root="$2" arch="$3"; shift 3
  local fel=("${DET_ELEJE[@]}" "$@" "${DET_VEGE[@]}") k pid t0 ok
  for k in $(seq 1 "$PROBA"); do
    # a gyökér üres legyen (a kész shardot a kiolvasó kihagyná): az előző próba részkimenete olvasatlanul félre
    if [ "$k" = 1 ]; then
      n=$(konti "ls -A /exp/$root 2>/dev/null | wc -l")
      [ "$n" = 0 ] || fail "a $root nem üres a kiolvasás előtt ($cimke)"
    else
      konti "set -e; mkdir -p /exp/${arch}_proba$((k - 1)); mv /exp/$root/* /exp/${arch}_proba$((k - 1))/" >> "$L" 2>&1 \
        || fail "a $((k - 1)). próba félretétele ($cimke)"
    fi
    allapot "kiolvasás előtt ($cimke, $k. próba)"
    memoria_or07 "$R/memoria.log"
    lep "$cimke: $k. próba indul"
    py07 kor08/eszkozok/kiolvas08.py kivon "${fel[@]}" --out-root "$root" --status "STATUS-$FAZIS-$cimke" \
      >> "$R/kiolvasas_${cimke}_c$k.log" 2>&1 &
    pid=$!
    t0=$(date +%s)
    ok=""
    while :; do
      if konti "test -f /exp/$root/$DETD/osszegzes.json"; then
        python3 kor08/eszkozok/det_or08.py ellenoriz --jell "$root" --elo det0 \
          --out "logs/k08g3/det_or_${cimke}_c${k}_det0.json" >> "$R/det_or.log" 2>&1
        case $? in 0) ok=1 ;; 3) ok=0 ;; *) ok=H ;; esac  # 3: a det0 eltér a referenciától; más: az őr nem futott le
        break
      fi
      kill -0 "$pid" 2>/dev/null || break
      [ $(( $(date +%s) - t0 )) -gt 2700 ] && { ok=T; break; }
      sleep 20
    done
    case "$ok" in
      1)
        lep "$cimke: $k. próba R-módban (a det0 bitre azonos), a kiolvasás megy tovább"
        wait "$pid" || fail "kiolvasás $cimke"
        sleep 20
        allapot "kiolvasás után ($cimke, $k. próba)"
        det_ellenoriz "$root" "$R"
        if [ -f "JELZES-DET-$FAZIS" ]; then
          cp "JELZES-DET-$FAZIS" "$R/JELZES-DET-$cimke-c$k"
          fail "a det1 a folyamat végén eltért ($cimke); a folytatásról Dani dönt (10.)"
        fi
        lep "$cimke: kész, a det0 és a det1 bitre azonos"
        return 0 ;;
      0)
        lep "$cimke: $k. próba nem R-mód (a det0 eltér); a folyamat leáll, a részkimenet olvasatlanul félre"
        docker ps --format '{{.Names}}' | grep '^ldh-py07' | xargs -r docker rm -f >> "$L" 2>&1
        wait "$pid" 2>/dev/null
        sleep 20 ;;
      T) fail "45 perc alatt sem készült el a det0 ($cimke, $k. próba)" ;;
      H) fail "a determinizmus-őr nem futott le a det0-n ($cimke, $k. próba)" ;;
      *) wait "$pid"; fail "a kiolvasás a det0 előtt kilépett ($cimke, $k. próba)" ;;
    esac
  done
  fail "$PROBA próbából egy sem került R-módba ($cimke); a folytatásról Dani dönt (10.)"
}
zart=()
for f in "${CSALADOK_08[@]}"; do
  for m in kanonikus b1; do
    zart+=(--feladat "lG2F:$f:CAL:$m" --feladat "lG2F:$f:TESZT:$m" --feladat "nG2F:$f:CAL:$m" --feladat "nG2F:$f:TESZT:$m"
           --feladat "lG2K3:$f:G2K3:$m" --feladat "oG2K3:$f:G2K3:$m" --feladat "nG2K3:$f:G2K3:$m" --feladat "lG2T:$f:G2T:$m")
  done
done
say "kiolvasás a pecsét alá (az értékelő szeletek), R-módban" 22000
kiolvas_r zart "$PJ" cache/k08/pecset/arch_c "${zart[@]}"
nyilt=()
for f in "${CSALADOK_08[@]}"; do
  for m in kanonikus b1; do nyilt+=(--feladat "oG2N:$f:G2N:$m"); done
done
say "kiolvasás: a tanítóminta (nyitott), R-módban" 7200
kiolvas_r nyilt "$JN" cache/k08/arch_g3n_c "${nyilt[@]}"

# --- 4. a 08-as fejek (a k08g3.sh 4. lépése) -------------------------------------------------------------------------------
say "a 08-as fejek tanítása" 3600
py kor08/eszkozok/b1rel08.py tanit --ert "oG2N_{csalad}_G2N" --ert-lanc "$G3/orakulum_G2N" --ert-jell "$JN" --out "$F8" --szalak 16 \
  >> "$R/tanit.log" 2>&1 || fail "a fejek tanítása"
sha256sum "$F8"/*/* "$F8"/fejek08.json > "$R/fejek08.sha256" 2>/dev/null

# --- 5. pontozás a pecsét alatt (a k08g3.sh 5. lépése) ---------------------------------------------------------------------
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
m=$(konti "find /exp/cache/k08/pecset -type f | wc -l; find /exp/$PJ -type f | wc -l" | paste -sd' ')
echo "$(date '+%F %T') a pecsét alatt (a konténerből számolva; összes / az R-módú kiolvasás): $m fájl" >> "$R/pecset.log"
lep "kész"
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
