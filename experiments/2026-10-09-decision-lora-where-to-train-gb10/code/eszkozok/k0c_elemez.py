"""K0c kiértékelés: adapterenként a vLLM DEBUG-log szegmenséből a ténylegesen betöltött
LoRA-modulok, és a próbahalmazon a címke-logitok elmozdulása az alaphoz képest.

Kapu (runbook H3/a): a betöltött modulok száma = a várt; a logitok elmozdulnak; a
negatív kontroll (átnevezés nélkül) 0 modult tölt be; routed expertre LoRA nem kerül.

„Elmozdulás” valószínűség-szinten, a példányzaj fölött: átl. |Δp(gold)| az alaphoz képest.
  - elmozdult: ≥ ZAJ_MAX és ≥ 3 × a negatív kontrollé;
  - nem mozdult (negatív kontroll): < ZAJ_MAX.
ZAJ_MAX = 0,01: a K0a-2-ben mért példányon belüli zaj (átl. |Δp(gold)| ≤ 0,0006 LoRA-val)
~16-szorosa. Az első változat a címke-log-prob max eltérését 1e-3-mal vágta; ezt a kis
valószínűségű címkék zaja (K0a-2: max 0,87 nat) önmagában átlépi, így a negatív kontroll
hamisan „mozdult” (2026-10-03, Napló).

Futtatás: python3 eszkozok/k0c_elemez.py --dir eredmenyek/F0/k0c
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import EXP, read_jsonl, write_json  # noqa: E402
from k0c_adapterek import EXPECTED  # noqa: E402
from osszevet import compare  # noqa: E402

ZAJ_MAX = 0.01
LOADED = re.compile(r"Successfully loaded LoRA weights for module (\S+?)\.?\s*$")
MISSING = re.compile(r"No LoRA weights found for module (\S+?),")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="eredmenyek/F0/k0c")
    args = ap.parse_args()
    d = Path(args.dir) if Path(args.dir).is_absolute() else EXP / args.dir
    base = read_jsonl(d / "base.jsonl")
    B = {(r["id"], r["perm"]): r for r in base}

    def dgold(name: str) -> float | None:
        f = d / f"{name}.jsonl"
        if not f.exists():
            return None
        A = {(r["id"], r["perm"]): r for r in read_jsonl(f)}
        ks = [k for k in B if k in A]
        return sum(abs(A[k]["probs"].get(B[k]["gold_label"], 0.0) - B[k]["probs"].get(B[k]["gold_label"], 0.0)) for k in ks) / max(1, len(ks))

    ctrl = [n for n, e in EXPECTED.items() if e == 0]
    ctrl_d = max((dgold(n) or 0.0) for n in ctrl) if ctrl else 0.0
    rep, ok_all = {"zaj_max": ZAJ_MAX, "negativ_kontroll_dgold": ctrl_d}, True
    for name, exp in EXPECTED.items():
        seg = d / f"{name}.log"
        if not seg.exists():
            rep[name] = {"hiba": "nincs log-szegmens"}
            ok_all = False
            continue
        loaded, missing = set(), set()
        for line in seg.read_text(errors="replace").splitlines():
            m = LOADED.search(line)
            if m:
                loaded.add(m.group(1))
            m = MISSING.search(line)
            if m:
                missing.add(m.group(1))
        kinds = sorted({re.sub(r"\.\d+\.", ".N.", x) for x in loaded})
        experts = [x for x in loaded if ".experts" in x]
        cmp = compare(base, read_jsonl(d / f"{name}.jsonl")) if (d / f"{name}.jsonl").exists() else {}
        dg = dgold(name)
        if exp > 0:
            moved = dg is not None and dg >= ZAJ_MAX and dg >= 3 * ctrl_d
        else:
            moved = dg is None or dg >= ZAJ_MAX
        ok = len(loaded) == exp and not experts and (moved if exp > 0 else not moved)
        ok_all &= ok
        rep[name] = {"loaded_modules": len(loaded), "expected": exp, "kinds": kinds, "expert_modules": len(experts),
                     "no_weights_reported": len(missing), "logits_moved": moved, "mean_abs_dprob_gold": dg,
                     "label_logprob_max_abs_diff": cmp.get("label_logprob_max_abs_diff"),
                     "top_label_agreement_vs_base": cmp.get("top_label_agreement"), "ok": ok}
    rep["K0c_ok"] = ok_all
    write_json(d / "k0c.json", rep)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    raise SystemExit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
