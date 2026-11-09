"""05-ös kör — a v1a rögzítése (05-runbook 8.2; a 03 7.10 mintájára) és a rögzítés ellenőrzése.

  python3 kor05/eszkozok/befagyaszt05.py manifest       # a MANIFEST.sha256 és a pillanatképek; a pecsét zárva marad
  python3 kor05/eszkozok/befagyaszt05.py rogzit --jovahagyas "Dani, 2026-10-29: …"
                                                        # a ROGZITES.json: ettől nyílik a pecsét (pecset05.kapu)
  python3 kor05/eszkozok/befagyaszt05.py ellenoriz      # az elemzés előtt: a manifest és a két pecsétmanifest

A `kor05/rogzites/v1a/` tartalma:
  05-runbook-v1a.md, v1a-vazlat.md   a runbook és a döntési vázlat pillanatképe a rögzítéskor
  K05F2B.json, K05JEV.json           a két pecsétmanifest pillanatképe (fájlnév, méret, sha256; kiolvasás nincs benne)
  MANIFEST.sha256                    sha256: az elemzőkód és az importált modulok, a szeletmanifest és az itemfájlok, a
                                     tartalmi és a megbízhatósági fejek, a kalibráció (kalib.json), a 03 vLLM-kiolvasásai
                                     (L1v, G3), a JEV várt fájllistája, a pillanatképek
  ROGZITES.json                      idő, jóváhagyás, a manifest hash-e; a meglétekor a pecsét alatti utak olvashatók
A `befagyaszt05.py` maga is a manifestben van; a manifest hash-e a ROGZITES.json-ban és a Naplóban áll.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "eszkozok")]
from pecset05 import MANIFEST_DIR, V1A, fajlok, sha256  # noqa: E402

DIR = V1A.parent
KOD = ["kor05/eszkozok/" + n for n in ("allapot05.py", "szeletek05.py", "hf_jellemzo05.py", "fej05.py", "megbizhatosag05.py",
                                        "kalib05.py", "elemzes05.py", "pecset05.py", "jev05.py", "befagyaszt05.py",
                                        "egyezes_vllm05.py")] + \
      ["eszkozok/common.py", "kor03/eszkozok/kozos03.py", "eszkozok/lib.sh"]
ADAT = ["kor05/adat/szeletek05.json", "kor05/adat/jev_varhato.json", "kor03/adat/f3/mvp_train_v2.jsonl",
        "kor03/adat/f2/items_val.jsonl", "kor03/adat/f2/items_eval.jsonl", "kor05/eredmenyek/F3/kalib/kalib.json",
        "kor03/eredmenyek/F2/qwen_val.jsonl", "kor03/eredmenyek/F2/qwen_eval.jsonl",
        *[f"kor03/eredmenyek/F4/k03v2_g3_s{n}/vllm_eval.jsonl" for n in (1, 2, 3)]]
FEJ_KAROK = ("C", "H", "A", "HX")
PECSETEK = ("K05F2B", "K05JEV")


def fej_fajlok() -> list[str]:
    out = []
    for k in FEJ_KAROK:
        for d, pat in ((f"cache/k05/fejek/{k}", "fej*"), (f"cache/k05/megbizhatosag/{k}", "rel*")):
            fs = sorted((EXP / d).glob(pat))
            if not fs:
                raise SystemExit(f"hiányzik: {d}/{pat}")
            out += [str(f.relative_to(EXP)) for f in fs]
    return out


def manifest(_a) -> None:
    if V1A.exists():
        raise SystemExit("a v1a már rögzítve; új manifest csak új verzióval (v1a.1) készülhet")
    DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(EXP / "05-runbook.md", DIR / "05-runbook-v1a.md")
    for n in PECSETEK:
        src = MANIFEST_DIR / f"{n}.json"
        if not src.exists():
            raise SystemExit(f"hiányzik a pecsétmanifest: {src.relative_to(EXP)}")
        shutil.copy(src, DIR / f"{n}.json")
    paths = [*KOD, *ADAT, *fej_fajlok(), *(str((DIR / n).relative_to(EXP)) for n in
             ("05-runbook-v1a.md", "v1a-vazlat.md", *(f"{p}.json" for p in PECSETEK)))]
    missing = [p for p in paths if not (EXP / p).exists()]
    if missing:
        raise SystemExit(f"hiányzó fájlok: {missing}")
    lines = [f"{sha256(EXP / p)}  {p}" for p in paths]
    (DIR / "MANIFEST.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"MANIFEST.sha256: {len(lines)} fájl, hash {sha256(DIR / 'MANIFEST.sha256')}")


def check_manifest() -> list[str]:
    bad = []
    for line in (DIR / "MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        h, p = line.split("  ", 1)
        if not (EXP / p).exists() or sha256(EXP / p) != h:
            bad.append(p)
    return bad


def check_pecset() -> list[str]:
    bad = []
    most = fajlok()
    for n in PECSETEK:
        doc = json.loads((DIR / f"{n}.json").read_text())
        bad += [f"{n}:{k}" for k, v in doc["fajlok"].items() if most.get(k) != v]
    return bad


def rogzit(a) -> None:
    if V1A.exists():
        raise SystemExit("a v1a már rögzítve")
    bad = check_manifest() + check_pecset()
    if bad:
        raise SystemExit(f"a manifest vagy a pecsét nem egyezik: {bad[:10]}")
    doc = {"verzio": "v1a", "rogzitve": datetime.now().isoformat(timespec="seconds"), "jovahagyas": a.jovahagyas,
           "manifest_sha256": sha256(DIR / "MANIFEST.sha256"),
           "pecset_manifestek": {n: sha256(DIR / f"{n}.json") for n in PECSETEK},
           "megjegyzes": "A HO-rétegek és a célcsalád-minták kiolvasásai a rögzítéskor nem voltak megtekintve; "
                         "a kiolvasás pecsételve futott (cache/k05/pecset/, root, 700)."}
    V1A.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(doc, ensure_ascii=False, indent=1))


def ellenoriz(_a) -> None:
    if not V1A.exists():
        raise SystemExit("nincs rögzítve (ROGZITES.json hiányzik)")
    doc = json.loads(V1A.read_text())
    bad = ([] if sha256(DIR / "MANIFEST.sha256") == doc["manifest_sha256"] else ["MANIFEST.sha256"]) + \
        check_manifest() + check_pecset()
    print(f"v1a ({doc['rogzitve']}): {'rendben' if not bad else f'ELTÉRÉS: {bad[:10]}'}")
    sys.exit(1 if bad else 0)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("manifest")
    r = sub.add_parser("rogzit")
    r.add_argument("--jovahagyas", required=True)
    sub.add_parser("ellenoriz")
    a = ap.parse_args()
    {"manifest": manifest, "rogzit": rogzit, "ellenoriz": ellenoriz}[a.cmd](a)


if __name__ == "__main__":
    main()
