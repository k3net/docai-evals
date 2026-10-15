"""03-as kör — minták a Qwen3.6 gondolkodó kiolvasásaihoz (Dani, 2026-10-10: a teljes val 8 mintával ~20 óra Spark
lett volna, ezért csökkentve; 03-runbook 4.2, 4.4).

  items_gond_val.jsonl  a tanárkapu mintája: a val forrás- vagy konstrukciós goldú itemjeiből (a szintetikus
                        családok nélkül, mert a kapu szintetikus golddal nem mér) csoportonként 75, a kisebb csoportból
                        mind. A gondolkodó tanár itemenként 4 mintát kap, mintánként más permutációval.
  items_zaj.jsonl       a gépi zajbecslés mintája: a train magyar forrás-gold forrásaiból forrásonként 300 (a kisebb
                        forrásból mind). Itemenként egy gondolkodó minta (0-s permutáció); a második olvasó a Gemma
                        (a train-en kész, k = 4).

A választás determinisztikus: az id sha256-ja szerinti sorrend eleje.

  python3 kor03/eszkozok/f2_minta03.py   → adat/f2/items_{gond_val,zaj}.jsonl
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F1, F2 = ROOT / "adat/f1", ROOT / "adat/f2"
GOND_PER_GROUP = 75
ZAJ_PER_SOURCE = 300
# a train magyar forrás-gold forrásai (a NerKor, a MultiEURLEX és a TED is forrás-gold; az NJT és a Wikipédia
# konstrukciós, a szint03 szintetikus, az angol gerinc a keretbe nem fért)
ZAJ_FORRASOK = ["HuCommitmentBank", "HuRTE", "HuWNLI", "HuCoPA", "HuRC", "MILQA", "HuCOLA", "HuSST", "NerKor",
                "MultiEURLEX", "TED"]


def key(r: dict) -> str:
    return hashlib.sha256(r["id"].encode()).hexdigest()


def rows(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]


def main() -> None:
    val = [r for r in rows(F1 / "pool_val.jsonl") if r["source"] != "szint03" and not r.get("ketertelmu")]
    by_g = defaultdict(list)
    for r in sorted(val, key=key):
        by_g[r["group"]].append(r)
    gond = [r for g in sorted(by_g) for r in by_g[g][:GOND_PER_GROUP]]
    train = rows(F1 / "pool_train.jsonl")
    if miss := set(ZAJ_FORRASOK) - {r["source"] for r in train}:
        raise SystemExit(f"hiányzó forrás a train-ben: {miss}")
    by_s = defaultdict(list)
    for r in sorted(train, key=key):
        if r["source"] in ZAJ_FORRASOK and not r.get("ketertelmu"):
            by_s[r["source"]].append(r)
    zaj = [r for s in ZAJ_FORRASOK for r in by_s[s][:ZAJ_PER_SOURCE]]
    for name, items in (("gond_val", gond), ("zaj", zaj)):
        (F2 / f"items_{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in items),
                                                encoding="utf-8")
    print(json.dumps({"gond_val": len(gond), "gond_csoport": dict(Counter(r["group"] for r in gond)),
                      "zaj": len(zaj), "zaj_forras": dict(Counter(r["source"] for r in zaj))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
