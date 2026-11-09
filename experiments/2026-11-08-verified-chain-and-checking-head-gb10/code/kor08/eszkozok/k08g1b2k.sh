#!/usr/bin/env bash
# K08G1B2K — 08 G1b, a D7 audit utáni javítás (Dani 11-02 23:10: az angol 02. forgatókönyv javítva, nem kihagyva;
# `ertelmezes08_szab.JAVITAS2["en"][1]`, `d7`): (0) az auditált kor2j archiválása (`kor2j/arch_d7`), (1) generálás: az
# auditált rekordok betűre átvéve, csak a `d7` jelű 5 terv új (Muse, új seed), (2) őr: a nem `d7` itemek bájtra
# azonosak az auditálttal, (3) a lánc orákulum-úton, v1 blokkal, (4) kiolvasás (oERT2J), (5) mérés (`g1b_ert08`), (6) vak
# auditlap csak az új itemekre (`audit08e --kor 2 --csak-d7`, modellválasz nélkül). Megvárja a többi fázist.
#   setsid nohup kor08/eszkozok/k08g1b2k.sh >/dev/null 2>&1 < /dev/null &
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
source eszkozok/lib.sh
FAZIS="K08G1B2K"
SZ=ERT2J
K=kor08/adat/ertelmezes/kor2j
R="$EXP/logs/k08g1b/kor2k"
mkdir -p "$R"
F=szabaly.koltsegelszamolas
MUSE_REV=a4e59da52a7bc87ae7251dd5545c0dd437c44b68
MUSE=(--url http://127.0.0.1:8450/v1 --model muse-glimmer-30b
      --extra '{"chat_template_kwargs": {"reasoning_strength": "low"}, "max_tokens": 4000}')
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
lep() { echo "[$(date '+%F %T')] $*" >> "$R/lepesek.log"; }
cpy() {
  docker run --rm --network host --user "$(id -u):$(id -g)" --entrypoint python3 -v "$EXP:/exp" -w /exp \
    -e PYTHONUNBUFFERED=1 "$SUBJECT_IMAGE" "$@"
}
memoria_or() {  # memoria_or <konténer>: 15 GB alatt leállítja (vLLM; a HF-betöltésre a lib07 őre vonatkozik)
  ( while docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null | grep -q true; do
      [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && { echo "memória < 15 GB $(date '+%T') ($1)" >> "$R/memoria.log"; docker rm -f "$1"; }
      sleep 30
    done ) &
}
varj() {  # varj <konténer> <port>
  local t0; t0=$(date +%s)
  until curl -fsS "http://127.0.0.1:$2/health" >/dev/null 2>&1; do
    [ "$(docker inspect -f '{{.State.Running}}' "$1" 2>/dev/null)" != "true" ] && return 1
    [ "$(free -g | awk 'NR==2{print $7}')" -lt 15 ] && return 1
    [ $(( $(date +%s) - t0 )) -gt 2700 ] && return 1
    sleep 15
  done
}

# --- várakozás: más fázis vagy konténer ne fusson ------------------------------------------------------------------------
lep "várakozás, amíg más fázis vagy konténer fut"
t0=$(date +%s)
while [ -f AKTIV_FAZIS ] || docker ps --format '{{.Names}}' | grep -q .; do
  [ $(( $(date +%s) - t0 )) -gt 21600 ] && { echo "$FAZIS: 6 óra várakozás után sem szabad a gép" > "FAILED-$FAZIS"; exit 1; }
  sleep 60
done
sleep 30
if [ -f AKTIV_FAZIS ]; then echo "$FAZIS: fut egy fázis ($(cat AKTIV_FAZIS)), nem indul" > "FAILED-$FAZIS"; exit 1; fi
if docker ps --format '{{.Names}}' | grep -q .; then echo "$FAZIS: fut egy konténer, nem indul" > "FAILED-$FAZIS"; exit 1; fi
echo "$FAZIS $(date '+%F %T')" > AKTIV_FAZIS
heartbeat_start $$

# --- 0. a terv ellenőrzése, az auditált állapot archiválása ------------------------------------------------------------
python3 - "$K/terv/$F.jsonl" <<'PY' || fail "a terv nem a várt (5 d7 terv, 119 összesen)"
import json, sys
t = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8")]
sys.exit(0 if len(t) == 119 and sum(bool(p["ertelmezes"].get("d7")) for p in t) == 5 else 1)
PY
if [ ! -d "$K/arch_d7" ]; then
  mkdir -p "$K/arch_d7"
  cp -r "$K/raw" "$K/items" "$K/arch_d7/"
  cp -r kor08/adat/G1/orakulum_ERT2J "$K/arch_d7/orakulum_ERT2J"
  # a G1b-mappa root tulajdonú (a `py` konténer írja): a másolás is konténerből, és hibára leáll (11-03: a host-oldali
  # cp némán elbukott, a kor2j.json elveszett)
  docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c \
    'for e in md json; do cp /exp/kor08/eredmenyek/G1b/kor2j.$e /exp/kor08/eredmenyek/G1b/kor2j_d7elott.$e || exit 1; done' \
    || fail "a kor2j mentése"
fi

# --- 1. generálás (Muse) ----------------------------------------------------------------------------------------------
say "Muse indul" 900
lep "Muse indul"
docker run -d --name ldh-muse --gpus all -p 8450:8000 --ipc host \
  -v "$HOME/hf-cache-muse:/root/.cache/huggingface" -e HF_HUB_OFFLINE=1 \
  "$SUBJECT_IMAGE" --model meta-models/Muse-Glimmer-30B --revision "$MUSE_REV" --tokenizer-revision "$MUSE_REV" \
  --served-model-name muse-glimmer-30b --quantization fp8 --max-model-len 8192 --gpu-memory-utilization 0.7 \
  --max-num-seqs 64 --reasoning-parser muse_glimmer --limit-mm-per-prompt '{"image": 0}' \
  --kernel-config '{"enable_flashinfer_autotune": false}' >/dev/null || fail "a Muse nem indult"
varj ldh-muse 8450 || fail "a Muse nem állt fel"
memoria_or ldh-muse
say "generálás: az angol 02. (5 terv), a többi az auditált körből" 600
lep "gen"
rm -rf "$K/raw" "$K/items"
cpy kor08/eszkozok/szint08e.py gen --kor 2 --javitott --csalad "$F" "${MUSE[@]}" --workers 8 >> "$R/gen.log" 2>&1 || fail "gen"
cpy kor08/eszkozok/szint08e.py final --kor 2 --javitott --csalad "$F" >> "$R/gen.log" 2>&1 || fail "final"
docker logs ldh-muse > "$R/ldh-muse.log" 2>&1 || true
docker rm -f ldh-muse >/dev/null 2>&1 || true
sleep 20

# --- 2. őr: az auditált itemek bájtra azonosak ---------------------------------------------------------------------------
lep "őr"
python3 - "$K" "$F" >> "$R/or.log" 2>&1 <<'PY' || fail "őr: a nem d7 itemek eltérnek az auditálttól"
import json, sys
k, f = sys.argv[1:3]
d7 = {p["group_id"] for p in map(json.loads, open(f"{k}/terv/{f}.jsonl", encoding="utf-8")) if p["ertelmezes"].get("d7")}
sor = lambda p: {json.loads(x)["id"]: x for x in open(p, encoding="utf-8") if x.strip()}  # noqa: E731
regi, uj = sor(f"{k}/arch_d7/items/{f}.jsonl"), sor(f"{k}/items/{f}.jsonl")
r0 = {i: x for i, x in regi.items() if i not in d7}
u0 = {i: x for i, x in uj.items() if i not in d7}
elt = sorted(i for i in r0.keys() | u0.keys() if r0.get(i) != u0.get(i))
print(f"auditált, nem d7: {len(r0)}; új, nem d7: {len(u0)}; eltérő: {len(elt)} {elt[:5]}")
print(f"d7 itemek: régi {len(set(regi) & d7)}, új {len(set(uj) & d7)}")
sys.exit(1 if elt else 0)
PY

# --- 3. a lánc, 4. kiolvasás, 5. mérés ---------------------------------------------------------------------------------
say "a lánc orákulum-úton" 120
lep "lánc"
python3 kor08/eszkozok/lanc08.py futtat --forras "$SZ" --csalad "$F" --ut orakulum --blokk v1 \
  --out "kor08/adat/G1/orakulum_$SZ" >> "$R/lanc.log" 2>&1 || fail "lánc"
feladat=(--feladat "o$SZ:$F:$SZ:kanonikus" --feladat "o$SZ:$F:$SZ:b1")
source kor07/eszkozok/lib07.sh  # py07 (memóriakorlát) és memoria_or07 (őr) a HF-betöltés csúcsa miatt
say "kiolvasás, négyállapotú keret (kb. 115 item)" 1500
lep "kiolvasás"
docker run --rm -v "$EXP:/exp" --entrypoint sh "$TOOL_IMAGE" -c "rm -rf /exp/cache/k08/jellemzok/o${SZ}_*"  # a cache root tulajdonú
memoria_or07 "$R/memoria07.log"
py07 kor08/eszkozok/kiolvas08.py kivon "${feladat[@]}" --out-root cache/k08/jellemzok --status "STATUS-$FAZIS-kiolvasas" \
  >> "$R/kiolvasas.log" 2>&1 || fail "kiolvasás"
sleep 20
say "a mérés" 120
lep "mérés"
py kor08/eszkozok/g1b_ert08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1b --kor 2 --javitott --csalad "$F" \
  >> "$R/meres.log" 2>&1 || fail "mérés"

# --- 6. vak auditlap az új itemekre --------------------------------------------------------------------------------------
lep "auditlap"
python3 kor08/eszkozok/audit08e.py minta --kor 2 --csak-d7 >> "$R/audit.log" 2>&1 || fail "audit-minta"
python3 kor08/eszkozok/audit08e.py html --kor 2 >> "$R/audit.log" 2>&1 || fail "auditlap"
say "kész"
lep "kész"
date '+%F %T' > "DONE-$FAZIS"
rm -f AKTIV_FAZIS
