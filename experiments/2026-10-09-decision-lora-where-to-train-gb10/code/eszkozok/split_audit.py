"""Split-átfedés-audit a fagyasztás előtt (önellenőrzés, 2026-10-07; runbook 15. pont, 1. kapu).

Az F1 T-szállító rétegének szállítói a train-ben is szerepeltek (generátorhiba), és split-átfedés-audit nem
volt. Ez az eszköz egy célsplitet vet össze a referencia-splitekkel a pár- és sorfájlokból (`parok.jsonl`,
`s4_sorok.jsonl`; az itemfájlok csak a duplikátumhoz kellenek):
  * szállító: a célsplit szállítói nem szerepelhetnek a referencia-splitekben (ha `--szallito-kitartott`);
  * pár: a (szállító, cikk) párok nem szerepelhetnek a referencia-splitekben;
  * cikk: a nem-X(b) cikkeknek van train-párja (ha `--latott-cikk`);
  * X(b): az X(b)-cikkek nem szerepelnek a train-ben és a val-ban;
  * duplikátum: a train-nel azonos (normalizált sorszöveg, gold) itemek száma (jelentve, nem kapu).
A referencia több könyvtárból is jöhet (pl. a 00b-nél az F1 is), így a kivezetett splitek is ellenőrződnek.
A „látott cikk” és a duplikátum a TÉNYLEGES tanítóhalmazhoz mérendő (`--train`, alapból a `--gen`): a 00b-ben a
generátor saját `items_train.jsonl`-je a jelölt-összeállítás újrafuttatása miatt eltért az F1-étől, amin az
adapterek tanultak (Napló 2026-10-07, K00b/B).

  python3 eszkozok/split_audit.py --gen adat/k00b --ref adat/f1 --split T-ujszallito --szallito-kitartott \
      --latott-cikk --train adat/f1 --out eredmenyek/K00b/audit/split.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import read_jsonl, write_json  # noqa: E402
from elemzes import _p  # noqa: E402


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.lower()).strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True, help="a célsplitet tartalmazó könyvtár")
    ap.add_argument("--ref", action="append", default=[], help="további referencia-könyvtár (ismételhető)")
    ap.add_argument("--split", required=True)
    ap.add_argument("--szallito-kitartott", action="store_true")
    ap.add_argument("--latott-cikk", action="store_true")
    ap.add_argument("--train", help="a tényleges tanítóhalmaz könyvtára (parok.jsonl + items_train.jsonl); alap: --gen")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    gen = _p(args.gen)
    pairs = read_jsonl(gen / "parok.jsonl")
    target = [p for p in pairs if p["split"] == args.split]
    ref = [p for p in pairs if p["split"] != args.split]
    for d in args.ref:
        ref += [p for p in read_jsonl(_p(d) / "parok.jsonl") if p["split"] != args.split]
    ref_sup = {p["supplier"] for p in ref}
    ref_pair = {(p["supplier"], p["article"]) for p in ref}
    tdir = _p(args.train) if args.train else gen
    train_art = {p["article"] for p in read_jsonl(tdir / "parok.jsonl") if p["split"] == "train" and not p["xb"]}
    trval_art = {p["article"] for p in ref if p["split"] in ("train", "val-belso", "val-szallito")}
    t_sup = sorted({p["supplier"] for p in target})

    res = {"split": args.split, "train": str(tdir), "parok": len(target), "szallitok": len(t_sup),
           "szallito_a_referenciaban": sorted(s for s in t_sup if s in ref_sup),
           "par_atfedes": sum((p["supplier"], p["article"]) in ref_pair for p in target),
           "nem_xb_cikk_train_par_nelkul": sum(not p["xb"] and p["article"] not in train_art for p in target),
           "xb_cikk_train_val_ban": sum(p["xb"] and p["article"] in trval_art for p in target)}
    items_f = gen / f"items_{args.split}.jsonl"
    if items_f.exists():
        tr = {(norm(r["context"]["sor"]), r["gold"]) for r in read_jsonl(tdir / "items_train.jsonl")}
        its = read_jsonl(items_f)
        res["itemek"] = len(its)
        res["sorszoveg_gold_duplikatum_a_trainnel"] = sum(
            r["gold"] is not None and (norm(r["context"]["sor"]), r["gold"]) in tr for r in its)
    fails = []
    if args.szallito_kitartott and res["szallito_a_referenciaban"]:
        fails.append("szállító a referenciában")
    if res["par_atfedes"]:
        fails.append("pár-átfedés")
    if args.latott_cikk and res["nem_xb_cikk_train_par_nelkul"]:
        fails.append("nem látott cikk")
    if res["xb_cikk_train_val_ban"]:
        fails.append("X(b)-cikk a train/val-ban")
    res["kapu_ok"] = not fails
    res["bukas"] = fails
    write_json(_p(args.out), res)
    print(json.dumps(res, ensure_ascii=False))
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
