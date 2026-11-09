"""08 — a D12 előzetes rögzítése és a G5 nyitása (G1-rögzítés 14., 10.). Mindkettő csak Dani kifejezett jóváhagyására
fut; a jóváhagyás időpontja és szövege a manifestbe kerül.

  rogzit   a rögzített fájlok sha256-ja (a tervezet, a lánc, a kinyerő, a kiolvasó, a fejtanító és a pontozó, az elemzők,
           a generátor és a forgatókönyvek, az audit, a determinizmus-őr és a referenciaszelet, a pecsét, és mindezek
           közvetett függőségei a 03–07-ből), a G3 tanítás G1-es bemenetei fájlonként (`ADATOK`: a láncos T500 orákulum-
           útja és reprezentációi) és a modellrevíziók → `kor08/rogzites/D12/manifest.json` (felülírni nem lehet); utána a
           G2 indulhat. Nem fut, ha a rögzített Python-fájlok importjainak zárt halmazában vagy a futtatók
           hivatkozásaiban rögzítetlen fájl van (`fuggosegek`).
  nyitas   a G5 nyitása: a G4 manifestje (`kor08/rogzites/pecset/K08G3*.json`) megvan és egyezik → `kor08/rogzites/G5/NYITAS.json`
  ellenoriz  a rögzített fájlok a manifesthez képest változatlanok-e

  python3 kor08/eszkozok/rogzit08.py rogzit --jovahagyas "Dani 2026-11-04 09:10: a v0.3 rögzíthető"
  python3 kor08/eszkozok/rogzit08.py ellenoriz
  python3 kor08/eszkozok/rogzit08.py nyitas --jovahagyas "Dani …: a G5 nyitható"
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
D12 = EXP / "kor08/rogzites/D12/manifest.json"
NYITAS = EXP / "kor08/rogzites/G5/NYITAS.json"
E8 = "kor08/eszkozok/"
FAJLOK = (
    "kor08/G1-rogzites.md",  # a runbook élő napló, nem rögzül
    *(E8 + f for f in ("lanc08.py", "kinyer08.py", "szabkin08.py", "g1_lanc08.py", "g1_dontes08.py", "kiolvas08.py",
                       "det_or08.py", "lib08.sh", "b1rel08.py", "g5_k1_08.py", "g5_k2_08.py", "g5_k3_08.py", "szint08.py",
                       "szint08e.py", "ertelmezes08_szab.py", "forgatokonyv08_szab.py", "gemma08.py", "audit08g2.py",
                       "pecset08.py", "rogzit08.py", "k08g2.sh", "k08g3.sh", "k08g5.sh")),
    "kor08/adat/G1/det_ref/meta.json", "kor08/adat/G1/det_ref/sorok_ref.jsonl",
    "kor08/adat/G1/det_ref/items/szabaly.koltsegelszamolas.jsonl",
    "kor07/eszkozok/b1rel07.py", "kor07/eszkozok/kiolvas07.py", "kor07/eszkozok/keret07.py", "kor07/eszkozok/elemzes07.py",
    "kor07/eszkozok/szint07.py", "kor07/eszkozok/szint07k3.py", "kor06/eszkozok/szint06.py", "kor06/eszkozok/gemma06.py",
    "kor05/eszkozok/hf_jellemzo05.py", "kor05/eszkozok/megbizhatosag05.py", "kor05/eszkozok/pecset05.py", "eszkozok/common.py",
    "eszkozok/lib.sh", "cache/k07/fejek/fejek.json", "cache/k07/fejek/temperature.json", "cache/k07/fejek/elotanit4.json",
    # a közvetett függőségek (az importok zárt halmaza és a futtatók hivatkozásai; 11-04) és a Gemma temperature-e
    "eszkozok/biralo.py", "eszkozok/elemzes.py", "eszkozok/f4_elemzes.py", "kor03/eszkozok/f4_elemzes03.py",
    "kor03/eszkozok/kie03.py", "kor03/eszkozok/kiolvaso03.py", "kor03/eszkozok/kozos03.py", "kor05/eszkozok/allapot05.py",
    "kor05/eszkozok/diag05.py", "kor05/eszkozok/elemzes05.py", "kor05/eszkozok/fej05.py", "kor05/eszkozok/kalib05.py",
    "kor06/eszkozok/b1rel06.py", "kor06/eszkozok/bontas06.py", "kor06/eszkozok/elemzes06.py", "kor06/eszkozok/friss06.py",
    "kor06/eszkozok/pecset06.py", "kor07/eszkozok/b14_07.py", "kor07/eszkozok/k3_07.py", "kor07/eszkozok/lib07.sh",
    "kor07/eszkozok/pecset07.py", "kor03/eredmenyek/F2/f2_elemzes.json",
)
# a G3 tanítás G1-es bemenetei (`b1rel08 tanit`: a láncos T500 orákulum-úton), fájlonként
ADATOK = ("kor08/adat/G1/orakulum_06", "cache/k08/jellemzok/o06_*_T500__*")
FUTTATOK = ("kor08/eszkozok/k08g2.sh", "kor08/eszkozok/k08g3.sh", "kor08/eszkozok/k08g5.sh", "kor08/eszkozok/lib08.sh")
MODELLEK = {"alany": {"repo": "Qwen/Qwen3.6-35B-A3B-FP8", "snapshot": "95a723d08a9490559dae23d0cff1d9466213d989"},
            "hf_bf16_bazis": "cache/qwen36-fp8hu-bf16 (a 00 K0f konverterének kimenete)",
            "generator": {"repo": "meta-models/Muse-Glimmer-30B", "revizio": "a4e59da52a7bc87ae7251dd5545c0dd437c44b68"},
            "triage": {"repo": "google/gemma-4-26B-A4B-it"}}


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def hashek() -> dict[str, str]:
    out = {}
    for f in FAJLOK:
        p = EXP / f
        if not p.exists():
            raise SystemExit(f"hiányzik a rögzítendő fájl: {f}")
        out[f] = sha(p)
    return out


def adat_hashek() -> dict[str, str]:
    out = {}
    for minta in ADATOK:
        ds = sorted(EXP.glob(minta))
        if not ds:
            raise SystemExit(f"hiányzik a rögzítendő adat: {minta}")
        for d in ds:
            for p in sorted(x for x in d.rglob("*") if x.is_file()):
                out[str(p.relative_to(EXP))] = sha(p)
    return out


def fuggosegek() -> list[str]:
    """A rögzített Python-fájlok importjainak zárt halmaza (a 03–08 eszközei közt) és a futtatók hivatkozásai, amelyek
    nincsenek a `FAJLOK`-ban."""
    mods = {p.stem: str(p.relative_to(EXP)) for d in ("kor03", "kor05", "kor06", "kor07", "kor08") for p in (EXP / d / "eszkozok").glob("*.py")}
    mods |= {p.stem: str(p.relative_to(EXP)) for p in (EXP / "eszkozok").glob("*.py")}
    ref, todo, seen = set(), [f for f in FAJLOK if f.endswith(".py")], set()
    for sh in FUTTATOK:
        ref |= {r for r in re.findall(r"((?:kor0\d/|eszkozok/)[\w/.-]+\.(?:py|sh))", (EXP / sh).read_text(encoding="utf-8"))
                if (EXP / r).exists()}
    while todo:
        f = todo.pop()
        if f in seen or not (EXP / f).exists():
            continue
        seen.add(f)
        for n in ast.walk(ast.parse((EXP / f).read_text(encoding="utf-8"))):
            nevek = [x.name for x in n.names] if isinstance(n, ast.Import) else [n.module] if isinstance(n, ast.ImportFrom) and n.module else []
            for m in (x.split(".")[0] for x in nevek):
                if m in mods:
                    ref.add(mods[m])
                    todo.append(mods[m])
    return sorted(r for r in ref if r not in FAJLOK)


def kepek() -> dict:
    """A tool- és a vLLM-image digestje (a spark-deven; helyben üres)."""
    out = {}
    for nev in ("lora-train:2", "vllm/vllm-openai:v0.30.0"):
        try:
            r = subprocess.run(["docker", "image", "inspect", nev, "--format", "{{.Id}} {{index .RepoDigests 0}}"],
                               capture_output=True, text=True, timeout=30)
            out[nev] = r.stdout.strip() or None
        except (OSError, subprocess.TimeoutExpired):
            out[nev] = None
    return out


def cmd_rogzit(a) -> None:
    if D12.exists():
        raise SystemExit(f"a D12 már rögzítve: {D12.relative_to(EXP)} (felülírni nem lehet)")
    hiany = fuggosegek()
    if hiany:
        raise SystemExit("rögzítetlen függőség: " + ", ".join(hiany))
    m = {"rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas, "fajlok": hashek(),
         "adatok": adat_hashek(), "modellek": MODELLEK, "kepek": kepek()}
    D12.parent.mkdir(parents=True, exist_ok=True)
    D12.write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"→ {D12.relative_to(EXP)}: {len(m['fajlok'])} fájl, {len(m['adatok'])} adatfájl")


def cmd_ellenoriz(_a) -> None:
    m = json.loads(D12.read_text(encoding="utf-8"))
    most, adat = hashek(), adat_hashek()
    elt = [f for f, h in m["fajlok"].items() if most.get(f) != h]
    elt += [f for f, h in m.get("adatok", {}).items() if adat.get(f) != h]
    elt += [f"új adatfájl: {f}" for f in adat if f not in m.get("adatok", {})]
    if elt:
        raise SystemExit("a rögzítés óta változott: " + ", ".join(elt[:20]))
    print(f"rendben: {len(m['fajlok'])} rögzített fájl és {len(m.get('adatok', {}))} adatfájl változatlan")


def cmd_nyitas(a) -> None:
    if NYITAS.exists():
        raise SystemExit("a G5 már nyitva")
    cmd_ellenoriz(a)
    man = sorted((EXP / "kor08/rogzites/pecset").glob("K08G3*.json"))
    if not man:
        raise SystemExit("nincs G4-manifest (a K08G3 pecsétje)")
    NYITAS.parent.mkdir(parents=True, exist_ok=True)
    NYITAS.write_text(json.dumps({"nyitva": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas,
                                  "g4_manifest": {str(p.relative_to(EXP)): sha(p) for p in man}}, ensure_ascii=False, indent=1) + "\n",
                      encoding="utf-8")
    print(f"→ {NYITAS.relative_to(EXP)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rogzit")
    r.add_argument("--jovahagyas", required=True, help="Dani jóváhagyásának időpontja és szövege")
    sub.add_parser("ellenoriz")
    n = sub.add_parser("nyitas")
    n.add_argument("--jovahagyas", required=True)
    a = ap.parse_args()
    {"rogzit": cmd_rogzit, "ellenoriz": cmd_ellenoriz, "nyitas": cmd_nyitas}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
