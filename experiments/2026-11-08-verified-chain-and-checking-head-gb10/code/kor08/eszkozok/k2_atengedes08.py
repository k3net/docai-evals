"""08 G5 utólag (11-05; nem rögzített; Dani: „mehet mindkettő”) — a K2 hamis átengedései tételenként: a `g5_k2_08`
definíciójával (a lánc kimenete, a megmaradt jelöltek, a kötés vagy a modellnek mutatott tétel a valós és az orákulumos
kinyeréssel eltér, az ellenőrzés átment) kikeresi az eltérő itemeket, és megmutatja, mi tért el: a két lánc-rekord, a
blokk sorai, a kinyert mezők és a modell döntése a két úton. Leíró, a K2 számát nem változtatja.

  python3 kor08/eszkozok/k2_atengedes08.py --out kor08/eredmenyek/G5_utolagos/k2_atengedes.md
"""

from __future__ import annotations

import argparse
import difflib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
G3 = EXP / "kor08/adat/G3"
PP = EXP / "cache/k08/pecset/pontoz"
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
MEZOK = ("kimenet", "megmaradt", "kizart", "kotes", "szamitott", "bukott", "elvetett", "allitasok")


def jsonl(p: Path) -> dict[str, dict]:
    return {r["id"]: r for r in map(json.loads, p.read_text(encoding="utf-8").splitlines()) if r}


def dontes(szelet: str) -> dict:
    return json.loads((PP / f"{szelet}.json").read_text())["keret4"]["dontes"]


def csalad(fam: str) -> list[str]:
    lk, lo = jsonl(G3 / f"kinyert_G2K3/lanc_{fam}.jsonl"), jsonl(G3 / f"orakulum_G2K3/lanc_{fam}.jsonl")
    mk, mo = jsonl(G3 / f"kinyert_G2K3/items/{fam}.jsonl"), jsonl(G3 / f"orakulum_G2K3/items/{fam}.jsonl")
    kin = jsonl(G3 / f"kinyeres/G2K3_{fam}.jsonl")
    dk, do = dontes(f"lG2K3_{fam}_G2K3"), dontes(f"oG2K3_{fam}_G2K3")
    ki = [f"## {fam}", ""]
    db = 0
    for i, r in lk.items():
        o = lo[i]
        if r["kimenet"] == "emberhez":
            continue
        m = (mk[i]["state"], mk[i]["options"]) if i in mk else None
        n = (mo[i]["state"], mo[i]["options"]) if i in mo else None
        if (r["kimenet"], sorted(r["megmaradt"]), r["kotes"], m) == (o["kimenet"], sorted(o["megmaradt"]), o["kotes"], n):
            continue
        db += 1
        ki += [f"### {i}", "", f"sablon `{mk[i]['template_group_id'] if i in mk else '–'}`, gold `{r['gold']}`, állapot {r['allapot']}", ""]
        ki += [f"- **{x}:** kinyert `{r[x]}` / orákulum `{o[x]}`" for x in MEZOK if r[x] != o[x]]
        ki += [f"- **döntés:** kinyert `{ {k: dk.get(i, {}).get(k) for k in ('valasz', 'pred', 'q')} }` / orákulum `{ {k: do.get(i, {}).get(k) for k in ('valasz', 'pred', 'q')} }`"]
        if m and n and m != n:
            d = [x for x in difflib.unified_diff(n[0].splitlines(), m[0].splitlines(), "orakulum", "kinyert", lineterm="", n=0)
                 if not x.startswith(("---", "+++", "@@"))]
            ki += ["", "A modellnek mutatott tétel eltérése:", "", "```", *d, "```"]
            if m[1] != n[1]:
                ki += ["", f"opciók: kinyert {m[1]} / orákulum {n[1]}"]
        ki += ["", "Kinyert mezők:", "", "```json", json.dumps(kin[i].get("mezok"), ensure_ascii=False, indent=0)[:1500], "```", ""]
        ki += ["A forrástétel:", "", "```", (mk.get(i) or mo[i])["state"][:1200], "```", ""]
    ki.insert(2, f"Hamis átengedés: {db}\n")
    return ki


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ki = ["# 08 G5 utólag — a K2 hamis átengedései tételenként (leíró)", ""]
    for f in CSALADOK:
        ki += csalad(f)
    o = EXP / a.out
    o.parent.mkdir(parents=True, exist_ok=True)
    o.write_text("\n".join(ki) + "\n", encoding="utf-8")
    print(f"→ {a.out}")


if __name__ == "__main__":
    main()
