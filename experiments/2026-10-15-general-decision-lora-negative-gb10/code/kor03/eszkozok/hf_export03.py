"""03-as kör — a tanító- és a val-adat HF-exportja (03-runbook 9. pont; Dani, 2026-10-15: a negatív eredmény publikálása).

Licenccsoportonként két konfiguráció (a 9. pont (a) és (b) része; (c), azaz nem továbbadható forrás az MVP-ben nincs):
  permissive  — Apache-2.0, MIT, CC0, CC-BY-4.0, BSD, ODC-BY, a jogszabályszöveg (Szjt. 1. § (4)), a TED (2011/833/EU)
                és a saját szintetikus családok (`konstrukcio` → CC-BY-4.0);
  sharealike  — CC-BY-SA-3.0 és CC-BY-SA-4.0.
A splitek: train = az MVP v2 (a G3 tanítóhalmaza), validation = a `val03` (a kalibráció és a τ halmaza).

A `meta`-ból csak a forrásazonosítók maradnak (FORRAS_META); a szinonimaszűrés, a gold-drop eredeti goldja és a
tanulási görbe jelölése kimarad. A kimenet minden mezőneve angol.

  python3 kor03/eszkozok/hf_export03.py --out kor03/hf-release/dataset
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPLITS = {"train": ROOT / "kor03/adat/f3/mvp_train_v2.jsonl", "validation": ROOT / "kor03/adat/f1/pool_val.jsonl"}
PERMISSIVE = {"Apache-2.0", "MIT", "CC0-1.0", "CC-BY-4.0", "BSD-2-Clause", "BSD-3-Clause", "ODC-BY-1.0", "HU-Szjt-1-4",
              "EU-2011/833", "konstrukcio"}
SHAREALIKE = {"CC-BY-SA-3.0", "CC-BY-SA-4.0"}
# a sor licence a kiadásban: a saját szintetikus családok CC-BY-4.0 alatt jelennek meg, a többi a forrásé
ROW_LICENSE = {"konstrukcio": "CC-BY-4.0", "HU-Szjt-1-4": "public-domain-HU-Szjt-1-4",
               "EU-2011/833": "EU-reuse-2011-833"}
FORRAS_META = {"ts_source": "tasksource_subset", "celex": "celex", "njt": "njt_id", "wiki_cim": "wikipedia_title",
               "milqa_cim": "milqa_title", "cpv_fo": "cpv_division", "recept": "recipe", "ellenteny": "counterfactual",
               "proc_level": "procedural_level", "mufaj": "nerkor_genre"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?:\+36|06)[ -/]?\d{1,2}[ -/]?\d{3}[ -/]?\d{3,4}")


def convert(r: dict) -> dict:
    lic = r["source_license"]
    prov = {new: r["meta"][old] for old, new in FORRAS_META.items() if old in (r.get("meta") or {})}
    return {"id": r["id"], "family": r["family"], "group": r["group"], "lang": r["lang"], "kind": r["kind"],
            "state": r["state"], "question": r["question"], "options": r["options"], "gold": r["gold"],
            "x_type": r["x_type"], "ambiguous": bool(r["ketertelmu"]), "soft": r["soft"], "group_id": r["group_id"],
            "source": r["source"], "source_ref": r["source_ref"], "source_license": lic,
            "license": ROW_LICENSE.get(lic, lic), "provenance": prov}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    stats: dict = {"configs": {}, "pii_scan": {}}
    seen: set[str] = set()
    for split, fn in SPLITS.items():
        rows = [json.loads(line) for line in fn.open(encoding="utf-8")]
        out = defaultdict(list)
        for r in rows:
            lic = r["source_license"]
            assert lic in PERMISSIVE | SHAREALIKE, f"ismeretlen licenc: {lic} ({r['id']})"
            assert r["id"] not in seen, f"ismétlődő id: {r['id']}"
            seen.add(r["id"])
            out["permissive" if lic in PERMISSIVE else "sharealike"].append(convert(r))
        for cfg, items in out.items():
            p = args.out / "data" / cfg / f"{split}.jsonl"
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8") as f:
                for it in items:
                    f.write(json.dumps(it, ensure_ascii=False) + "\n")
            st = stats["configs"].setdefault(cfg, {}).setdefault(split, {})
            st["n"] = len(items)
            st["scored"] = sum(not it["ambiguous"] for it in items)
            st["x_gold"] = sum(it["gold"] is None and not it["ambiguous"] for it in items)
            st["lang"] = dict(Counter(it["lang"] for it in items))
            st["group"] = dict(Counter(it["group"] for it in items).most_common())
            st["x_type"] = dict(Counter(it["x_type"] for it in items if it["x_type"]).most_common())
            st["source"] = dict(Counter(it["source"].split(":")[0] for it in items).most_common())
            st["license"] = dict(Counter(it["license"] for it in items).most_common())
            st["sha256"] = hashlib.sha256(p.read_bytes()).hexdigest()
            # PII-mintakeresés: csak darabszám és forráscsalád, szöveg nem kerül ki
            hits = Counter()
            for it in items:
                txt = " ".join([it["state"] or "", it["question"] or "", *(o["text"] for o in it["options"])])
                if EMAIL.search(txt):
                    hits[("email", it["source"].split(":")[0])] += 1
                if PHONE.search(txt):
                    hits[("phone", it["source"].split(":")[0])] += 1
            stats["pii_scan"][f"{cfg}/{split}"] = {f"{k}:{s}": n for (k, s), n in hits.most_common()}
    (args.out / "export_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({c: {s: {k: v for k, v in d.items() if k in ("n", "scored", "x_gold", "lang")}
                          for s, d in v.items()} for c, v in stats["configs"].items()}, ensure_ascii=False))
    print("pii", json.dumps(stats["pii_scan"], ensure_ascii=False))


if __name__ == "__main__":
    main()
