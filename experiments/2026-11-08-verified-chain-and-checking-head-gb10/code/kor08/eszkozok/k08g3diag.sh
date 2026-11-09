#!/usr/bin/env bash
# K08G3DIAG (11-05; nem rögzített) — a K08G3 determinizmus-jelzésének hibakeresése a G1-rögzítés 10. pontja szerint: csak a
# referenciaszeleten, a teszteredmények felnyitása nélkül. Két friss HF-folyamat a tiszta gépen (órák óta nincs vLLM),
# mindegyik csak a referenciaszeletet (det0) olvassa, a K08G3-mal azonos hívással (`py07 kiolvas08 kivon`, nyitott
# könyvtárba); utána az őr mindkettőn. A K08G3 két kísérletének (zárt 1., 2.) det0/det1 sorai a pecsét alól a
# diagnosztikai könyvtárba másolva (csak a det-könyvtárak, értékelő szelet nem), és minden kiolvasás páronként összevetve.
#   setsid nohup kor08/eszkozok/k08g3diag.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
source kor07/eszkozok/lib07.sh
FAZIS="K08G3DIAG"
R="$EXP/logs/k08g3diag"
D=cache/k08/detdiag_g3
DET=det0_szabaly.koltsegelszamolas_T500__kanonikus
mkdir -p "$R"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
allapot() {
  { echo "== $(date '+%F %T') $1"; uptime; free -g | sed -n 2,3p
    nvidia-smi --query-gpu=driver_version,clocks.sm,power.draw,temperature.gpu --format=csv,noheader
    nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv,noheader
    docker ps --format '{{.Names}} {{.Status}}'; } >> "$R/allapot.log" 2>&1
}
[ -f AKTIV_FAZIS ] && { echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS))" > "FAILED-$FAZIS"; exit 1; }
docker ps --format '{{.Names}}' | grep -q . && { echo "$FAZIS: fut egy konténer" > "FAILED-$FAZIS"; exit 1; }
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

for p in p1 p2; do
  allapot "kiolvasás előtt ($p)"
  memoria_or07 "$R/memoria.log"
  say "referenciaszelet, friss folyamat ($p)" 900
  py07 kor08/eszkozok/kiolvas08.py kivon --feladat "det0:szabaly.koltsegelszamolas:T500:kanonikus" --out-root "$D/$p" \
    --status "STATUS-$FAZIS-$p" >> "$R/kiolvasas_$p.log" 2>&1 || fail "kiolvasás $p"
  allapot "kiolvasás után ($p)"
  python3 kor08/eszkozok/det_or08.py ellenoriz --jell "$D/$p" --elo det0 --out "logs/k08g3diag/det_or_$p.json" \
    >> "$R/det_or.log" 2>&1
  sleep 20
done

docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "
  set -e
  mkdir -p /exp/$D/zart1 /exp/$D/zart2
  cp -r /exp/cache/k08/pecset/jellemzok.jelzes/det0_* /exp/cache/k08/pecset/jellemzok.jelzes/det1_* /exp/$D/zart1/
  cp -r /exp/cache/k08/pecset/jellemzok/det0_* /exp/cache/k08/pecset/jellemzok/det1_* /exp/$D/zart2/
  chmod -R a+rX /exp/$D" >> "$R/masolas.log" 2>&1 || fail "a det-sorok kimásolása"

python3 - "$D" "$DET" > "$R/osszevetes.md" 2>&1 <<'PY' || fail "összevetés"
import json, sys
from pathlib import Path
d, det = Path(sys.argv[1]), sys.argv[2]
def sorok(p):
    return {r["id"]: r for f in sorted(p.glob("sorok_*.jsonl")) for r in map(json.loads, f.read_text().splitlines()) if r}
k = {"ref": {r["id"]: r for r in map(json.loads, Path("kor08/adat/G1/det_ref/sorok_ref.jsonl").read_text().splitlines())},
     "zart1.det0": sorok(d / "zart1" / det), "zart1.det1": sorok(d / "zart1" / det.replace("det0", "det1")),
     "zart2.det0": sorok(d / "zart2" / det), "zart2.det1": sorok(d / "zart2" / det.replace("det0", "det1")),
     "p1": sorok(d / "p1" / det), "p2": sorok(d / "p2" / det)}
nev = list(k)
print("# K08G3DIAG — a referenciaszelet kiolvasásai páronként (bitre azonos sor / eltérő pred / max |Δ logprob|)\n")
print("| | " + " | ".join(nev) + " |")
print("|---|" + "---|" * len(nev))
for a in nev:
    cel = []
    for b in nev:
        ids = k[a].keys() & k[b].keys()
        azon = sum(k[a][i]["label_logprobs"] == k[b][i]["label_logprobs"] for i in ids)
        pred = sum(k[a][i]["pred"] != k[b][i]["pred"] for i in ids)
        dm = max((abs(k[a][i]["label_logprobs"][c] - k[b][i]["label_logprobs"].get(c, float("inf")))
                  for i in ids for c in k[a][i]["label_logprobs"]), default=0.0)
        cel.append(f"{azon}/{len(ids)} · {pred} · {dm:.3f}")
    print(f"| {a} | " + " | ".join(cel) + " |")
PY
say "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
