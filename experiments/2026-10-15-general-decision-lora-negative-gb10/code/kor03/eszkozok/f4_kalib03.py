"""03-as kör — a H3 második útjának célréteg-kalibrációs mintái (03-runbook 7. H3, v1).

Rétegenként ~200 item a teszt eloszlásából, egész klaszterekben (`group_id`), hash-rang szerint, hogy a kalibrációs
minta és a maradék teszt közt ne legyen klaszter-átfedés. A HO-terméken és a HO-routingon a gold a 00/01 emberileg
átnézett tesztjéből jön; a HO-új-családon a minta már az itemekben jelölt (`meta.kalibracio`, 200 item, a
konstrukcióból). A mintát a predikciók megnézése nélkül húzzuk; a kalibrációs itemek MINDEN 03-as hipotézis
tesztjéből kimaradnak.

  python3 kor03/eszkozok/f4_kalib03.py   → adat/f4/kalib.json (rétegenként az id-k és a sha256)
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = "f4_kalib03:2026-10-13"
N_MIN = 200
RETEGEK = ("ho-termek", "ho-routing")


def rank(key: str) -> str:
    return hashlib.sha256(f"{SEED}:{key}".encode()).hexdigest()


def main() -> None:
    by = defaultdict(lambda: defaultdict(list))
    hoje = []
    with open(ROOT / "adat/f2/items_eval.jsonl", encoding="utf-8") as fh:
        for line in fh:
            r = json.loads(line)
            if r["split"] in RETEGEK:
                by[r["split"]][r["group_id"]].append(r["id"])
            elif r["split"] == "ho-uj" and (r.get("meta") or {}).get("kalibracio"):
                hoje.append(r["id"])
    out = {"seed": SEED, "retegek": {}}
    for s in RETEGEK:
        ids = []
        for g in sorted(by[s], key=rank):
            if len(ids) >= N_MIN:
                break
            ids += by[s][g]
        n_total = sum(len(v) for v in by[s].values())
        out["retegek"][s] = {"n": len(ids), "n_klaszter": sum(1 for g in by[s] if by[s][g][0] in set(ids)),
                             "n_reteg": n_total, "ids": sorted(ids)}
    out["retegek"]["ho-uj"] = {"n": len(hoje), "n_reteg": 2400, "ids": sorted(hoje), "forras": "meta.kalibracio"}
    for s, v in out["retegek"].items():
        v["sha256"] = hashlib.sha256("\n".join(v["ids"]).encode()).hexdigest()
    (ROOT / "adat/f4").mkdir(parents=True, exist_ok=True)
    (ROOT / "adat/f4/kalib.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({s: {k: v for k, v in d.items() if k != "ids"} for s, d in out["retegek"].items()},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
