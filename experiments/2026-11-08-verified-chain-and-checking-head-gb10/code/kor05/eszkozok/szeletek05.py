"""05-ös kör — a 05a szeletei (05-runbook 4.1, 3.3).

  D_fit          a 03 MVP v2 train-je, teljesen
  D_dev          a `val03`, teljesen
  D_meta, D_cal_prob, D_cal_policy
                 a 03 test-id rétege (magyar) + az eval-kulso angol gerince (angol, ~25%), csoportonként
                 (`group_id`) hash-rang szerint, csoportrétegenként (a 03 `group`) arányos kvótával
  cel:<réteg>    célcsalád-minta: 500 alapeset (`group_id`) rétegenként; a 03 célréteg-kalibrációs mintáinak
                 (kalib.json) csoportjai mind benne vannak, a többi hash-rang szerint. A HO-routingon csak a megerősítő
                 rész (a T-hu-maradék nélkül) csoportjaiból
  teszt:<réteg>  a szűrő-teszt: a réteg maradéka; a HO-routingon a T-hu-maradék nélkül, a HO-routing-hu ennek magyar része
  leiro:t-hu-maradek  a 03-ban is csak leíró réteg

A minta a predikciók megnézése nélkül készül (csak id, group_id, csoport és nyelv kell hozzá). Kapu: a létrehozott
szeletek item- és csoportszinten diszjunktak egymástól és a D_fit/D_dev-től.

  python3 kor05/eszkozok/szeletek05.py          → kor05/adat/szeletek05.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path.insert(0, str(HERE))
from allapot05 import content_state, rows  # noqa: E402

SEED = "k05:20261028"
META_SIZE = {"D_meta": 6000, "D_cal_prob": 3000, "D_cal_policy": 3000}
EN_SHARE = 0.25
CEL_N = 500
SRC = {
    "mvp": EXP / "kor03/adat/f3/mvp_train_v2.jsonl",
    "val": EXP / "kor03/adat/f2/items_val.jsonl",
    "eval": EXP / "kor03/adat/f2/items_eval.jsonl",
    "kalib": EXP / "kor03/adat/f4/kalib.json",
}


def rank(gid: str) -> str:
    return hashlib.sha256(f"{SEED}|{gid}".encode()).hexdigest()


def sha_ids(ids) -> str:
    return hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()


def file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def quota_split(items: list[dict], quotas: dict[str, int]) -> dict[str, list[dict]]:
    """Csoportonként, hash-rangban: a csoport az első olyan szeletbe kerül, amelynek a kvótáját a csoport előtti
    halmozott itemszám még nem érte el; a kvóták után maradók tartalékba."""
    by = defaultdict(list)
    for it in items:
        by[it["group_id"]].append(it)
    out = {k: [] for k in quotas} | {"tartalek": []}
    bounds, acc = [], 0
    for k, q in quotas.items():
        acc += q
        bounds.append((acc, k))
    cum = 0
    for gid in sorted(by, key=rank):
        slot = next((k for b, k in bounds if cum < b), "tartalek")
        out[slot] += by[gid]
        cum += len(by[gid])
    return out


def meta_cal(eval_items: list[dict]) -> dict[str, list[dict]]:
    hu = [it for it in eval_items if it["split"] == "test-id"]
    en = [it for it in eval_items if it["split"] == "eval-kulso" and it["group"] == "angol_gerinc"]
    strata = defaultdict(list)
    for it in hu:
        strata[it["group"]].append(it)
    out = {k: [] for k in META_SIZE}
    for _, its in sorted(strata.items()):
        q = {k: round(v * (1 - EN_SHARE) * len(its) / len(hu)) for k, v in META_SIZE.items()}
        for k, v in quota_split(its, q).items():
            if k in out:
                out[k] += v
    for k, v in quota_split(en, {k: round(v * EN_SHARE) for k, v in META_SIZE.items()}).items():
        if k in out:
            out[k] += v
    return out


def cel_teszt(eval_items: list[dict]) -> dict[str, list[dict]]:
    sys.path[:0] = [str(EXP / "kor03/eszkozok"), str(EXP / "eszkozok")]
    import f4_elemzes03 as f4  # noqa: PLC0415

    meta = f4.load_meta03()
    kal = {s: v["ids"] for s, v in json.loads(SRC["kalib"].read_text())["retegek"].items()}
    by_id = {it["id"]: it for it in eval_items}
    maradek = {i for i, m in meta.items() if m["split"] == "ho-routing" and m["source"] == "massive_hu"
               and not m["t_hu_atnezett"]}
    out = {}
    for layer in ("ho-termek", "ho-routing", "ho-uj"):
        its = [it for it in eval_items if it["split"] == layer and it["id"] not in maradek]
        groups = {it["group_id"] for it in its}
        forced = {by_id[i]["group_id"] for i in kal[layer] if i in by_id and i not in maradek}
        assert forced <= groups, layer
        rest = sorted(groups - forced, key=rank)
        chosen = forced | set(rest[: max(0, CEL_N - len(forced))])
        out[f"cel:{layer}"] = [it for it in its if it["group_id"] in chosen]
        out[f"teszt:{layer}"] = [it for it in its if it["group_id"] not in chosen]
    out["teszt:ho-routing-hu"] = [it for it in out["teszt:ho-routing"] if it["lang"] == "hu"]
    out["leiro:t-hu-maradek"] = [by_id[i] for i in sorted(maradek)]
    return out


def summary(its: list[dict]) -> dict:
    sc = [it for it in its if not it.get("ketertelmu")]
    return {"n": len(its), "n_pontozott": len(sc), "n_group": len({it["group_id"] for it in its}),
            "csoportok": dict(Counter(it["group"] for it in its).most_common()),
            "nyelv": dict(Counter(it["lang"] for it in its)),
            "allapotok_pontozott": dict(Counter(content_state(it) for it in sc).most_common()),
            "sha256": sha_ids(it["id"] for it in its), "ids": sorted(it["id"] for it in its)}


def main() -> None:
    mvp, val, ev = (list(rows(SRC[k])) for k in ("mvp", "val", "eval"))
    S = {"D_fit": mvp, "D_dev": val, **meta_cal(ev), **cel_teszt(ev)}
    # kapu: a létrehozott szeletek diszjunktak egymástól és a D_fit/D_dev-től (a teszt:ho-routing-hu részhalmaz)
    own = [k for k in S if k not in ("D_fit", "D_dev", "teszt:ho-routing-hu")]
    pairs = [(a, b) for a in ("D_fit", "D_dev") for b in own] + list(combinations(own, 2))
    atfedes = {}
    for a, b in pairs:
        ia, ib = {it["id"] for it in S[a]}, {it["id"] for it in S[b]}
        ga, gb = {it["group_id"] for it in S[a]}, {it["group_id"] for it in S[b]}
        atfedes[f"{a}×{b}"] = {"item": len(ia & ib), "group": len(ga & gb)}
    bad = {k: v for k, v in atfedes.items() if v["item"] or v["group"]}
    fit_dev = {"item": len({i["id"] for i in mvp} & {i["id"] for i in val}),
               "group": len({i["group_id"] for i in mvp} & {i["group_id"] for i in val})}
    res = {"seed": SEED, "letrehozva": date.today().isoformat(), "cel_n": CEL_N, "meta_size": META_SIZE,
           "en_share": EN_SHARE, "forrasok": {k: {"path": str(p.relative_to(EXP)), "sha256": file_sha(p)}
                                             for k, p in SRC.items()},
           "atfedes_hibak": bad, "D_fit×D_dev (a 03 splitje)": fit_dev,
           "szeletek": {k: summary(v) for k, v in S.items()}}
    out = EXP / "kor05/adat/szeletek05.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1))
    for k, v in res["szeletek"].items():
        print(f"{k:22s} n={v['n']:6d} pontozott={v['n_pontozott']:6d} group={v['n_group']:6d} {v['allapotok_pontozott']}")
    print("D_fit×D_dev:", fit_dev)
    if bad:
        raise SystemExit(f"ÁTFEDÉS: {bad}")
    print("kapu: OK, a létrehozott szeletek diszjunktak")


if __name__ == "__main__":
    main()
