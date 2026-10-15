"""03-as kör — az angol külső evalok a közös sémára (03-runbook 3.3, 5.: csak eval, soraik nem kerülnek a publikus
készletbe).

  en.eval.localllama   LocalLLaMA/typed-decisions, test (4 munkafolyamat × 100 állapot, állapotonként több kérdés).
                       A gold valószínűség-eloszlás: a gold a legvalószínűbb címke; ha az 0,6 alatt van, az item
                       kétértelmű (nem pontozott), a forráseloszlás a `soft`. A score kérdések kimaradnak.
  en.eval.fastino      fastino/fast-decisions (17 feladatcsalád × ~100): az egycímkés osztályozási feladatok; a
                       többcímkések kimaradnak.

Split: `eval-kulso`. Csoport: angol_gerinc (a kitartás-logika szempontjából mindegy, mert csak eval).

  kor01/.venv/bin/python kor03/eszkozok/adapter_eval_en.py
"""

from __future__ import annotations

import ast
import glob
import json
import sys
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import MAX_OPTIONS, noul_options, validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
HF = ROOT / "forras/hf"
OUT = ROOT / "adat/f0"
SOFT_BELOW = 0.6


def base(fam: str, src: str, ref: str, gid: str, state: str, question: str) -> dict:
    return {"id": f"{fam}:{ref}", "family": fam, "group": "angol_gerinc", "source": src, "source_license": "Apache-2.0",
            "source_ref": ref, "split": "eval-kulso", "group_id": f"{fam}:{gid}", "lang": "en", "state": state,
            "question": question, "x_type": None, "ketertelmu": False, "soft": None, "meta": {}}


def localllama() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    f = glob.glob(str(HF / "LocalLLaMA/typed-decisions/all/test-*.parquet"))[0]
    for r in pq.read_table(f).to_pylist():
        qs, gold = json.loads(r["questions"]), json.loads(r["gold"])
        for qn, q in qs.items():
            g = gold.get(qn) or {}
            b = base("en.eval.localllama", "LocalLLaMA/typed-decisions", f"{r['id']}:{qn}", r["id"], r["state"],
                     q["instructions"]) | {"meta": {"workflow": r["workflow"]}}
            if q["type"] == "noul":
                p = float(g["probabilities"]["true"])
                it = b | {"kind": "noul", "options": noul_options("en"), "gold": "igen" if p >= 0.5 else "nem"}
                if max(p, 1 - p) < SOFT_BELOW:
                    it |= {"ketertelmu": True, "soft": {"igen": p, "nem": 1 - p}}
            elif q["type"] == "choice":
                keys = list(q["criteria"])
                if not 2 <= len(keys) <= MAX_OPTIONS:
                    why["kimarad: opciószám"] += 1
                    continue
                probs = {k: float(g["probabilities"].get(k, 0.0)) for k in keys}
                top = max(probs, key=lambda k: probs[k])
                it = b | {"kind": "choice", "options": [{"id": k, "text": q["criteria"][k]} for k in keys], "gold": top}
                if probs[top] < SOFT_BELOW:
                    it |= {"ketertelmu": True, "soft": probs}
            else:
                why["kimarad: " + q["type"]] += 1
                continue
            rows.append(it)
            why[it["kind"] + (" puha" if it["ketertelmu"] else "")] += 1
    return rows, why


def fastino() -> tuple[list[dict], Counter]:
    rows, why = [], Counter()
    for f in sorted(glob.glob(str(HF / "fastino/fast-decisions/*.jsonl"))):
        task = Path(f).stem
        for i, line in enumerate(Path(f).read_text(encoding="utf-8").splitlines()):
            r = json.loads(line)
            out = r["output"]
            out = ast.literal_eval(out) if isinstance(out, str) else out
            for c in out.get("classifications", []):
                labels, true = c["labels"], c["true_label"]
                if c.get("multi_label") or len(true) != 1 or not 2 <= len(labels) <= MAX_OPTIONS:
                    why["kimarad: többcímkés vagy opciószám"] += 1
                    continue
                b = base("en.eval.fastino", "fastino/fast-decisions", f"{task}:{i}:{c['task']}", f"{task}:{i}",
                         r["input"], f"Which {c['task'].replace('_', ' ')} applies?") | {"meta": {"task": task}}
                rows.append(b | {"kind": "choice", "options": [{"id": f"o{j + 1}", "text": t} for j, t in enumerate(labels)],
                                 "gold": f"o{labels.index(true[0]) + 1}"})
                why["choice"] += 1
    return rows, why


def main() -> None:
    rep = {}
    for fam, fn in (("en.eval.localllama", localllama), ("en.eval.fastino", fastino)):
        rows, why = fn()
        bad = [(r["id"], e) for r in rows if (e := validate(r))]
        if bad:
            raise SystemExit(f"{fam}: {len(bad)} sémahiba, pl. {bad[:3]}")
        dup = Counter(r["id"] for r in rows).most_common(1)
        if dup and dup[0][1] > 1:
            raise SystemExit(f"{fam}: ismétlődő id {dup}")
        (OUT / f"{fam}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        rep[fam] = {"n": len(rows), "ok": dict(why)}
        print(fam, json.dumps(rep[fam], ensure_ascii=False))
    (OUT / "adapter_eval_en_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
