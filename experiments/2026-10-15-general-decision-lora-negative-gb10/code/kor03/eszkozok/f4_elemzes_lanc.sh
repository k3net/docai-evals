#!/usr/bin/env bash
# K03F4 elemzés — a v1 szerint (03-runbook 7.; Dani, 2026-10-14: „a pontosítások rögzítése és a technikai teljesség
# ellenőrzése után az F4 elemzése elindítható; ehhez újabb jóváhagyási kör nem szükséges”). Várakozó lánc:
#   1. megvárja a pótlás végét (DONE-K03F4-potlas); kilép, ha a kiolvasás, az L0′ vagy a pótlás elbukott, vagy STOP-K03F4;
#   2. a rögzített v1-manifest ellenőrzése: a manifest saját hash-e (MANIFEST_SHA, a rögzítéskor ide írva; a lánc maga
#      ezért nincs a manifestben, a hash-e a runbook naplójában), majd `sha256sum --strict -c` a tartalmára (kód,
#      runbook-pillanatkép, itemek, kalibrációs minták, val-kiolvasások, a PECSET rögzítéskori pillanatképe);
#   3. a technikai lezárás (f4_teljesseg03.py; pontos (id, perm)-egyezés, érvényesség, pecsét-előtagok);
#   4. az elemzés (f4_elemzes03.py, 10 000 ismétlés) a lora-train:2 image-ben, GPU nélkül.
# Bármely lépés hibájánál megáll (FAILED-K03F4-elemzes), az elemzés nem fut. Konténert nem állít le (a GPU-t nem
# használja), ezért a lib.sh `fail`-je helyett saját hibakezelővel.
#   nohup setsid bash kor03/eszkozok/f4_elemzes_lanc.sh > logs/k03f4_elemzes.out 2>&1 < /dev/null &
set -u
EXP="$HOME/experiments/2026-10-03-lora-decision-head"
FAZIS=K03F4-elemzes
source "$EXP/eszkozok/lib.sh"
cd "$EXP"
R=kor03/eredmenyek/F4
MANIFEST=kor03/rogzites/v1/MANIFEST.sha256
MANIFEST_SHA=86e5e9ac1f54caaa5c7d432a4dc486fb75146ece13baad2239994ce1f6716abb
hiba() {
  say "HIBA: $*"
  echo "[$(date '+%F %T')] $*" > "$EXP/FAILED-$FAZIS"
  exit 1
}
echo "[$(date '+%F %T')] vár a pótlásra"
while [ ! -f DONE-K03F4-potlas ]; do
  for f in FAILED-K03F4-kiolvasas FAILED-K03F4-l0r FAILED-K03F4-potlas; do
    [ -f "$f" ] && hiba "$f: az elemzés nem indul"
  done
  [ -f STOP-K03F4 ] && { echo "[$(date '+%F %T')] STOP-K03F4: kilépek"; exit 0; }
  sleep 120
done
rm -f "$EXP/FAILED-$FAZIS" "$EXP/DONE-$FAZIS"

say "K03F4 elemzés: a v1-manifest ellenőrzése"
[ "$(sha256sum "$MANIFEST" | cut -d' ' -f1)" = "$MANIFEST_SHA" ] || hiba "a v1-manifest maga megváltozott ($MANIFEST)"
sha256sum --strict -c "$MANIFEST" > "$R/v1_manifest_ellenorzes.txt" 2>&1 \
  || hiba "a v1-manifest nem egyezik ($R/v1_manifest_ellenorzes.txt)"

say "K03F4 elemzés: technikai lezárás"
python3 kor03/eszkozok/f4_teljesseg03.py > "$R/teljesseg.log" 2>&1 || hiba "a technikai lezárás nem rendben ($R/teljesseg.log)"
sha256sum "$R/teljesseg.json" "$R/potolt_parok.jsonl" "$R/V1-MANIFEST-kiolvasasok.sha256" > "$R/teljesseg.sha256"

say "K03F4 elemzés: bootstrap (10 000 ismétlés)" 3600
docker run --rm --name ldh-elemzes --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
  -e HOME=/tmp -e PYTHONUNBUFFERED=1 "$TOOL_IMAGE" kor03/eszkozok/f4_elemzes03.py --progress 1000 > "$R/elemzes.log" 2>&1 \
  || hiba "az elemzés elhasalt ($R/elemzes.log)"
sha256sum "$R/f4_elemzes03.json" "$R/eredmenylap_gepi.md" > "$R/elemzes.sha256"

say "K03F4 elemzés kész" 0
date '+%F %T' > "$EXP/DONE-$FAZIS"
