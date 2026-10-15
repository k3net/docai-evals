"""03-as kör — az F2-kiolvasások itemlistái (03-runbook 4.4, 6., 8.: L0/L1★ minden rétegen, tanárkapu a val-on).

  items_val.jsonl    a keverő pool_val-ja (L1★ temperature-fit és τ; tanárkapu; családválasztás, 10. döntés 4.)
  items_eval.jsonl   minden eval-réteg: az F0- és a szintetikus családok teszt-ID-, HO- és külső eval-splitjei, valamint
                     a 00/01 befagyasztott HO-tesztjei (from_00 / from_01, natív kerettel)
  items_train.jsonl  a keverő pool_train-je (bázis-horgony az X-gold itemeken; a tanárok soft targetjei)

  python3 kor03/eszkozok/f2_itemek03.py   → adat/f2/items_{val,eval,train}.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from kozos03 import from_00, from_01  # noqa: E402
from szivargas03 import EVAL_SPLITS, ITEMS_00, ITEMS_01  # noqa: E402

ROOT = HERE.parents[0]
F0, F1, F2 = ROOT / "adat/f0", ROOT / "adat/f1", ROOT / "adat/f2"


def rows(p: Path):
    for line in p.read_text(encoding="utf-8").splitlines():
        yield json.loads(line)


def main() -> None:
    F2.mkdir(parents=True, exist_ok=True)
    files = sorted(F0.glob("*.jsonl")) + [p for p in sorted((F1 / "szint").glob("*.jsonl"))
                                          if p.name != "forras_bekezdesek.jsonl"]
    ev = [r for p in files for r in rows(p) if r["split"] in EVAL_SPLITS]
    for paths, fn in ((ITEMS_00, from_00), (ITEMS_01, from_01)):
        for p in paths:
            if not p.exists():
                raise SystemExit(f"hiányzó HO-teszt: {p}")
            ev += [fn(r) for r in rows(p)]
    ids = Counter(r["id"] for r in ev)
    if dup := [i for i, c in ids.items() if c > 1]:
        raise SystemExit(f"ismétlődő eval-id: {len(dup)}, pl. {dup[:5]}")
    out = {"val": list(rows(F1 / "pool_val.jsonl")), "eval": ev, "train": list(rows(F1 / "pool_train.jsonl"))}
    for name, items in out.items():
        (F2 / f"items_{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items),
                                                encoding="utf-8")
    print(json.dumps({k: len(v) for k, v in out.items()} |
                     {"eval_split": dict(Counter(r["split"] for r in ev))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
