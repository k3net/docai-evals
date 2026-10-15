"""03-as kör — ellenőrző-jelöltek összevetése a val-on, forrás-golddal (2026-10-10, a Mistral X-gyengesége után).

A szintetikus családok ellenőrzője akkor enged át egy itemet, ha a top-1 a szándékolt címke, legalább 0,6 bizalommal
(szint03 final). Itt ugyanezt a szabályt alkalmazzuk a val forrás-gold itemjein, a 0-s permutáción (a tárolt sorrend,
X utolsó, generikus keret: ugyanaz a prompt, mint a szint03 ellenőrzőjéé):

  átmenő arány (saját mérőszám) = a pontozott itemek közül hány esetben top-1 = gold és bizalom ≥ 0,6;
  X-en: top-1 = X és bizalom ≥ 0,6.

Döntési szabály (előre rögzítve, a mérés előtt; minden jelöltre): a jelölt akkor ellenőriz, ha (1) a címketömeg mediánja ≥ 0,9, (2) az
X-itemek átmenő aránya ≥ 0,5, (3) a nem-X átmenő aránya legfeljebb 10 ponttal marad el a Gemmáétól.

  python3 kor03/eszkozok/ellenorzo_valid03.py muse=kor03/eredmenyek/F2/muse_val0.jsonl \\
      gemma=kor03/eredmenyek/F2/gemma_val.jsonl mistral=kor03/eredmenyek/F2/mistral_val.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

MIN_CONF = 0.6


def stats(path: str) -> dict:
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]
    rows = [r for r in rows if r["perm"] == 0 and not r["ketertelmu"]]
    c = defaultdict(lambda: [0, 0, 0])  # n, átment, top-1 talált
    mass = sorted(r["label_mass"] for r in rows)
    for r in rows:
        ok = r["pred"] == r["gold_label"]
        key = "nem-X" if r["gold_label"] != "X" else f"X:{r['x_type']}"
        for k in (key, "X" if key.startswith("X:") else None, "nyelv:en" if r["family"].startswith("en.") else "nyelv:hu"):
            if k:
                c[k][0] += 1
                c[k][1] += ok and r["conf"] >= MIN_CONF
                c[k][2] += ok
    return {"n": len(rows), "tomeg_median": mass[len(mass) // 2] if mass else None,
            "retegek": {k: {"n": n, "atmeno": round(p / n, 3), "top1": round(t / n, 3)} for k, (n, p, t) in sorted(c.items())}}


def main() -> None:
    res = {name: stats(path) for name, path in (a.split("=", 1) for a in sys.argv[1:])}
    for name, s in res.items():
        print(f"== {name}: n {s['n']}, címketömeg medián {s['tomeg_median']:.3f}")
        for k, v in s["retegek"].items():
            print(f"   {k:28s} n {v['n']:5d}  átmenő {v['atmeno']:.3f}  top-1 {v['top1']:.3f}")
    g = res.get("gemma")
    for name in [n for n in res if n not in ("gemma", "mistral", "qwen")] if g else []:
        m = res[name]
        feltetel = {"tomeg": m["tomeg_median"] >= 0.9,
                    "x_atmeno": m["retegek"].get("X", {}).get("atmeno", 0) >= 0.5,
                    "nemx_vs_gemma": m["retegek"]["nem-X"]["atmeno"] >= g["retegek"]["nem-X"]["atmeno"] - 0.10}
        print(f"döntés ({name}):", "ellenőrizhet" if all(feltetel.values()) else "NEM ellenőriz", feltetel)
        res[f"dontes_{name}"] = feltetel
    out = Path("kor03/eredmenyek/F2/ellenorzo_valid03.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
