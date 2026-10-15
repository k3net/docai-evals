"""03-as kör — az F0 adapterkimeneteinek összesítője: újravalidálás és családonkénti tábla (03-runbook 8. pont).

Minden `adat/f0/*.jsonl` és `adat/f1/szint/*.jsonl` (szintetikus) itemet újravalidál (kozos03.validate), ellenőrzi az id-k egyediségét a teljes készletben, és
hogy egy group_id egyetlen splitben van-e. Kimenet: `adat/f0/osszesito03.{json,md}`.

  kor01/.venv/bin/python kor03/eszkozok/osszesito03.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kozos03 import validate  # noqa: E402

F0 = Path(__file__).resolve().parents[1] / "adat/f0"


def main() -> None:
    fam: dict[str, dict] = {}
    ids, gsplit, bad = Counter(), defaultdict(set), []
    szint = F0.parent / "f1/szint"
    files = sorted(F0.glob("*.jsonl")) + ([q for q in sorted(szint.glob("*.jsonl")) if q.name != "forras_bekezdesek.jsonl"]
                                         if szint.exists() else [])
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if e := validate(r):
                bad.append((r["id"], e))
            ids[r["id"]] += 1
            gsplit[r["group_id"]].add(r["split"])
            f = fam.setdefault(r["family"], {"group": r["group"], "lang": r["lang"], "n": 0, "split": Counter(),
                                             "x": 0, "x_type": Counter(), "kind": Counter(), "licenc": Counter(),
                                             "puha": 0, "fajl": p.name})
            f["n"] += 1
            f["split"][r["split"]] += 1
            f["kind"][r["kind"]] += 1
            f["licenc"][r["source_license"]] += 1
            f["puha"] += bool(r.get("ketertelmu"))
            if r["gold"] is None and not r.get("ketertelmu"):
                f["x"] += 1
                f["x_type"][r["x_type"]] += 1
    dup = [i for i, c in ids.items() if c > 1]
    leak = [g for g, s in gsplit.items() if len(s) > 1]
    tot = Counter()
    md = ["| család | csoport | nyelv | n | train | val | teszt-ID | egyéb | X | X-típus | licenc |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, f in sorted(fam.items(), key=lambda kv: (kv[1]["lang"], kv[1]["group"], kv[0])):
        sp = f["split"]
        other = sum(v for k, v in sp.items() if k not in ("train", "val", "test-id"))
        md.append(f"| {name} | {f['group']} | {f['lang']} | {f['n']} | {sp['train']} | {sp['val']} | {sp['test-id']} | "
                  f"{other} | {f['x'] / f['n']:.0%} | {', '.join(f'{k} {v}' for k, v in f['x_type'].items()) or '—'} | "
                  f"{', '.join(sorted(f['licenc']))} |")
        tot[(f["lang"], "n")] += f["n"]
        tot[(f["lang"], "train")] += sp["train"]
    summary = {"csalad": len(fam), "item": sum(f["n"] for f in fam.values()), "semahiba": len(bad),
               "ismetlodo_id": len(dup), "tobb_splitben_levo_group": len(leak),
               "nyelv": {f"{k[0]}:{k[1]}": v for k, v in tot.items()}}
    md += ["", f"Összesen {summary['item']} item, {summary['csalad']} család; sémahiba {len(bad)}, ismétlődő id "
               f"{len(dup)}, több splitben lévő group_id {len(leak)}."]
    out = {"osszegzes": summary, "csaladok": {k: {**v, "split": dict(v["split"]), "x_type": dict(v["x_type"]),
                                                  "kind": dict(v["kind"]), "licenc": dict(v["licenc"])}
                                              for k, v in fam.items()},
           "hibak_minta": bad[:20], "ismetlodo_minta": dup[:20], "szivargo_group_minta": leak[:20]}
    (F0 / "osszesito03.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    (F0 / "osszesito03.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[-1:]))
    print(json.dumps(summary, ensure_ascii=False))
    if bad or dup or leak:
        raise SystemExit("az összesítő hibát talált")


if __name__ == "__main__":
    main()
