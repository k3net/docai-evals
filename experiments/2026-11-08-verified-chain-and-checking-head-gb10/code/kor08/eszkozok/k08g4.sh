#!/usr/bin/env bash
# K08G4 (11-05; nem rögzített) — a végrehajtás lezárása (08-runbook 8., D12): a G1 rögzítésének ellenőrzése, a pecsét
# manifestjének ellenőrzése, a kinyerés, a lánc és a fejek hash-listáinak visszaellenőrzése, és az elkészült adatok, a
# tanítóminta kiolvasása, a fejek, az image-ek és a nem rögzített eszközök hash-ei egy manifestbe. Itt már semmi nem dől
# el, és a pecsét alól csak hash kerül ki, kiolvasás nem. A manifest neve a rögzített `rogzit08 nyitas` mintájára illik
# (`kor08/rogzites/pecset/K08G3*.json`), így a nyitás a hash-ét is rögzíti. Felülírni nem lehet. Csak CPU.
#   kor08/eszkozok/k08g4.sh
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1
EXP="$(pwd)"
FAZIS="K08G4"
R=logs/k08g4
M=kor08/rogzites/pecset/K08G3.g4.json
mkdir -p "$R"
rm -f "FAILED-$FAZIS" "DONE-$FAZIS"
hiba() { echo "[$(date '+%F %T')] $FAZIS: $*" | tee "FAILED-$FAZIS"; exit 1; }

[ -f DONE-K08G3 ] || hiba "nincs DONE-K08G3"
[ -f AKTIV_FAZIS ] && hiba "fut egy fázis ($(cat AKTIV_FAZIS))"
[ -f kor08/rogzites/G5/NYITAS.json ] && hiba "a G5 már nyitva; a G4 a nyitás előtt készül"
[ -f "$M" ] && hiba "a G4 már lezárva: $M (felülírni nem lehet)"

python3 kor08/eszkozok/rogzit08.py ellenoriz > "$R/rogzites.log" 2>&1 || hiba "a rögzítés ellenőrzése nem zöld"
PATH="$EXP/kor08/eszkozok/burok_g3:$PATH" python3 kor08/eszkozok/pecset08.py ellenoriz --fazis K08G3 > "$R/pecset.log" 2>&1 \
  || hiba "a pecsét manifestje nem egyezik"
: > "$R/hashek.log"
for f in kinyeres lanc fejek08; do
  sha256sum -c --quiet "logs/k08g3/$f.sha256" >> "$R/hashek.log" 2>&1 || hiba "a $f hash-listája nem egyezik"
done

python3 - "$M" "$R" <<'PY' || hiba "a manifest írása"
import hashlib, json, subprocess, sys
from datetime import datetime
from pathlib import Path

m, r = Path(sys.argv[1]), Path(sys.argv[2])

def sha(p):
    h = hashlib.sha256()
    with Path(p).open("rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()

def fa(*gyokerek):
    return {str(p): sha(p) for g in gyokerek for p in sorted(Path(g).rglob("*")) if p.is_file()}

def kep(nev):
    return subprocess.run(["docker", "image", "inspect", nev, "--format", "{{.Id}}"], capture_output=True, text=True,
                          timeout=30).stdout.strip()

d12 = json.loads(Path("kor08/rogzites/D12/manifest.json").read_text(encoding="utf-8"))
kieg = json.loads(Path("kor08/rogzites/D12/kepek_kiegeszites.json").read_text(encoding="utf-8"))
rog = {"lora-train:2": kieg["kepek"]["lora-train:2"], "vllm/vllm-openai:v0.30.0": d12["kepek"]["vllm/vllm-openai:v0.30.0"].split()[0]}
most = {n: kep(n) for n in rog}
if most != rog:
    raise SystemExit(f"az image eltér a rögzítettől: {most} / {rog}")

det = {f: json.loads(Path("logs/k08g3", f).read_text(encoding="utf-8"))["eredmeny"]
       for f in ("det_or_zart_c1_det0.json", "det_or_nyilt_c1_det0.json", "det_or.json")}
doc = {
    "fazis": "K08G4", "lezarva": datetime.now().isoformat(timespec="seconds"),
    "d12_manifest_sha256": sha("kor08/rogzites/D12/manifest.json"),
    "rogzites_ellenorzes": (r / "rogzites.log").read_text(encoding="utf-8").strip(),
    "pecset": {"manifest": "kor08/rogzites/pecset/K08G3.json", "sha256": sha("kor08/rogzites/pecset/K08G3.json"),
               "ellenorzes": (r / "pecset.log").read_text(encoding="utf-8").strip()},
    "hash_listak": {f"logs/k08g3/{f}.sha256": sha(f"logs/k08g3/{f}.sha256") for f in ("kinyeres", "lanc", "fejek08")},
    "determinizmus_or": det,
    "kepek": most,
    "fajlok": {"G2": fa("kor08/adat/G2"), "G3": fa("kor08/adat/G3"), "tanitominta_kiolvasasa": fa("cache/k08/jellemzok_g3"),
               "fejek": fa("cache/k08/fejek08")},
    "nem_rogzitett_eszkozok": {f: sha(f) for f in (
        "kor08/eszkozok/burok_g3/python3", "kor08/eszkozok/k08g3_burok.sh", "kor08/eszkozok/k08g3diag.sh",
        "kor08/eszkozok/k08g3c.sh", "kor08/eszkozok/k08g4.sh", "kor08/eszkozok/k08g5_burok.sh")},
    "elteresek_a_rogzitett_futtatotol": [
        "a k08g3.sh a burok_g3/python3 shimmel futott: a pecset08 és a det_or08 a konténerben, mert a gazdagép python3-ja a root 700-as pecsétet nem éri el",
        "a két zárt kísérlet (A, B mód) a determinizmus-őrön megállt (G1-rögzítés 10.); a folytatásról Dani döntött (11-05 08:20, „1-es legyen”): k08g3c.sh",
        "a kinyerés és a lánc nem futott újra (hash-ellenőrzés), a kiolvasás módja a folyamat elején, a referenciaszeleten dőlt el, a kritérium nem változott",
        "a két kísérlet kiolvasása olvasatlanul a pecsét alatt: arch_zart1_A, arch_zart2_B; a pontozás és a G5 csak az R-módú jellemzok-at használja",
    ],
}
m.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"→ {m}: " + ", ".join(f"{k} {len(v)}" for k, v in doc["fajlok"].items()) + " fájl")
PY
sha256sum "$M" | tee "$R/manifest.sha256"
date '+%F %T' > "DONE-$FAZIS"
