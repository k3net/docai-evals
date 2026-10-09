"""H4 — két adapter egy példányon, soros és párhuzamos terhelés mellett (01 v1, 6.2).

A `k01f4_vezenylo.sh` H4-blokkjának kiolvasásai (perm 0, a val-okon) a kor01/eredmenyek/F4/h4/ alatt:
  l3_i1, l3_i2   — két friss példány, csak a 01 L3 betöltve (zaj-alap)
  ba_i3, ba_i4   — két friss példány, csak a 00 BA-adapter betöltve (zaj-alap)
  l3_i5_soros, ba_i5_soros         — egy példány mindkét adapterrel, soros (c = 1)
  l3_i5_par, ba_i5_par, bazis_i5_par — ugyanott, egyszerre futó vegyes forgalom (összesen c = 16)
Ítélet adapterenként és módonként: d = egyezés(i5, i1|i3) − egyezés(i2, i1 | i4, i3), itemenként párosított
bootstrappal; teljesül, ha d egyoldali 95%-os alsó korlátja ≥ −0,01. A H4 akkor igaz, ha mind a négy teljesül.

  python3 kor01/eszkozok/h4_egyezes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "eszkozok"))
from common import read_jsonl, write_json  # noqa: E402

H = Path(__file__).resolve().parents[1] / "eredmenyek/F4/h4"
REPS = 10000


def top(name: str) -> dict:
    return {r["id"]: r["pred"] for r in read_jsonl(H / f"{name}.jsonl") if r["perm"] == 0}


def check(ref: str, cmp: str, n1: str, n2: str, rng: np.random.Generator) -> dict:
    a, b, z1, z2 = top(ref), top(cmp), top(n1), top(n2)
    ids = sorted(set(a) & set(b) & set(z1) & set(z2))
    eq = np.array([a[i] == b[i] for i in ids], dtype=float)
    nz = np.array([z1[i] == z2[i] for i in ids], dtype=float)
    d = eq - nz
    boot = np.array([d[rng.integers(0, len(d), len(d))].mean() for _ in range(REPS)])
    lo = float(np.quantile(boot, 0.05))
    return {"n": len(ids), "egyezes": float(eq.mean()), "zaj_egyezes": float(nz.mean()), "d": float(d.mean()),
            "d_also95_egyoldali": lo, "teljesul": lo >= -0.01}


def main() -> None:
    rng = np.random.default_rng(0)
    checks = {"L3_soros": check("l3_i1", "l3_i5_soros", "l3_i1", "l3_i2", rng),
              "L3_par16": check("l3_i1", "l3_i5_par", "l3_i1", "l3_i2", rng),
              "BA_soros": check("ba_i3", "ba_i5_soros", "ba_i3", "ba_i4", rng),
              "BA_par16": check("ba_i3", "ba_i5_par", "ba_i3", "ba_i4", rng)}
    res = {**checks, "H4": all(v["teljesul"] for v in checks.values())}
    write_json(H / "h4.json", res)
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
