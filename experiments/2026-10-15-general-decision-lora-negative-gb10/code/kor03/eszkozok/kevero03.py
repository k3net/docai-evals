"""03-as kör — keverő v0: a jelöltkészlet (pool) összeállítása az F0 (és az F1 szintetikus) itemjeiből (spec:
kor03/spec/kevero.yaml).

Családonként a kvóta szerinti számú train-item (és a val-arányú val-item) a család saját splitjéből, hash-alapú,
determinisztikus mintavétellel. X-kezelés: a családon belüli X-arány legfeljebb `x_csaladon_belul_max` (a forrás
arányánál nem több); utána, ha egy X-típus az összes X több mint `x_tipus_max` részét adja, a többletet ugyanannak a
családnak nem-X itemjei váltják. Ami hiányzik (pl. a szintetikus családok a generálás előtt), azt a riport jelzi.

Kimenet: kor03/adat/f1/pool_{train,val}.jsonl, pool_riport.json, és a szinonimaszűrés céljai
(szinonim_celok.jsonl: a szűrendő családokban a kvóta 1,3-szereséig vett jelöltek, kiegyensúlyozás előtt; így a
szintetikus családok hozzáadása és a kiesők pótlása után sem kell újraszűrni). Kizárva: a szivárgás-audit találatai
(szivargas_kizart.jsonl); ha már van szinonim_dontes.json, a szűrendő családokból csak a szűrt itemek jöhetnek, a
kivett opciók nélkül.

  python3 kor03/eszkozok/kevero03.py
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((ROOT / "spec/kevero.yaml").read_text(encoding="utf-8"))
F0, F1 = ROOT / "adat/f0", ROOT / "adat/f1"
KONSTR = ("konstrukcios.", "jogi.njt_")
SZINT = ("level.triage", "level.dokumentumtipus", "level.szerzodesklauzula", "entitas.egyezes", "rag.relevancia",
         "rag.valaszbiralat", "jogi.hivatali_ugytipus")


def rank(iid: str) -> str:
    return hashlib.sha256(f"{SPEC['seed']}:{iid}".encode()).hexdigest()


SZINONIM_CSALADOK = ("qa.hurc", "qa.milqa", "jogi.multieurlex", "kozbeszerzes.ted_cpv", "konstrukcios.wiki_szakaszcim",
                     "konstrukcios.wiki_folytatas", "jogi.njt_torveny", "jogi.njt_fejezet", "jogi.njt_cim")
TARTALEK = 1.3  # a szinonimaszűrés céljai a kvóta ennyiszereséig: a kiesők pótlása is szűrt itemből jöjjön


def exclusions() -> tuple[set[str], dict | None]:
    """A szivárgás-audit kizártjai, és ha már megvan, a szinonimaszűrés döntései."""
    kiz = set()
    p = F1 / "szivargas_kizart.jsonl"
    if p.exists():
        kiz = {json.loads(line)["id"] for line in p.read_text(encoding="utf-8").splitlines()}
    d = F1 / "szinonim_dontes.json"
    return kiz, (json.loads(d.read_text(encoding="utf-8"))["itemek"] if d.exists() else None)


def load() -> dict[str, list[dict]]:
    kiz, szin = exclusions()
    fams: dict[str, list[dict]] = defaultdict(list)
    files = sorted(F0.glob("*.jsonl")) + [F1 / "szint" / f"{f}.jsonl" for f in SZINT if (F1 / "szint" / f"{f}.jsonl").exists()]
    for p in files:
        for line in p.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r["split"] not in ("train", "val") or r["id"] in kiz:
                continue
            if szin is not None and r["family"] in SZINONIM_CSALADOK:
                d = szin.get(r["id"])
                if d is None or d["kizart"]:  # szűretlen vagy a szűrő után nem maradt elég opció
                    continue
                if d["kivett"]:
                    r = r | {"options": [o for o in r["options"] if o["id"] not in d["kivett"]],
                             "meta": (r.get("meta") or {}) | {"szinonim_kivett": d["kivett"]}}
            fams[r["family"]].append(r)
    return fams


def quotas(fams: dict[str, list[dict]]) -> tuple[dict[str, int], list[str]]:
    q, missing = {}, []
    for key, v in SPEC["kvota"].items():
        if "*" not in key:
            if key in fams:
                q[key] = v
            else:
                missing.append(key)
            continue
        match = sorted(f for f in fams if fnmatch.fnmatch(f, key))
        total, per = (v["osszes"], v.get("forrasonkent")) if isinstance(v, dict) else (v, None)
        avail = {f: sum(r["split"] == "train" for r in fams[f]) for f in match}
        cap = {f: min(avail[f], per or avail[f]) for f in match}
        # egyenletes elosztás a családok közt (vízszint-töltés), a sapkákat tartva
        alloc, left, open_ = dict.fromkeys(match, 0), total, set(match)
        while left > 0 and open_:
            share = max(1, left // len(open_))
            for f in sorted(open_):
                add = min(share, cap[f] - alloc[f], left)
                alloc[f] += add
                left -= add
                if alloc[f] >= cap[f]:
                    open_.discard(f)
                if left == 0:
                    break
        q |= {f: n for f, n in alloc.items() if n}
    return q, missing


def pick(items: list[dict], n: int) -> list[dict]:
    """n item; X legfeljebb a forrásarány és x_csaladon_belul_max közül a kisebb."""
    if n <= 0 or not items:
        return []
    items = sorted(items, key=lambda r: rank(r["id"]))
    xs = [r for r in items if r["gold"] is None and not r.get("ketertelmu")]
    nx = [r for r in items if not (r["gold"] is None and not r.get("ketertelmu"))]
    n = min(n, len(items))
    x_share = min(len(xs) / len(items), SPEC["x_csaladon_belul_max"])
    k_x = min(len(xs), round(n * x_share))
    k_nx = min(len(nx), n - k_x)
    k_x = min(len(xs), n - k_nx)
    return nx[:k_nx] + xs[:k_x]


def balance_x_types(pool: list[dict], fams: dict[str, list[dict]], split: str) -> list[dict]:
    """Ha egy X-típus az X-ek több mint x_tipus_max részét adja, a legrosszabb rangú többletet ugyanannak a családnak
    még nem választott nem-X itemjei váltják."""
    chosen = {r["id"] for r in pool}
    while True:
        xs = [r for r in pool if r["gold"] is None and not r.get("ketertelmu")]
        if not xs:
            return pool
        cnt = Counter(r["x_type"] for r in xs)
        top, c = cnt.most_common(1)[0]
        excess = c - int(SPEC["x_tipus_max"] * len(xs))
        if excess <= 0:
            return pool
        drop = sorted((r for r in xs if r["x_type"] == top), key=lambda r: rank(r["id"]), reverse=True)[:excess]
        drop_ids = {r["id"] for r in drop}
        pool = [r for r in pool if r["id"] not in drop_ids]
        for r in drop:
            repl = next((x for x in sorted(fams[r["family"]], key=lambda x: rank(x["id"]))
                         if x["split"] == split and x["id"] not in chosen and x["gold"] is not None), None)
            if repl:
                pool.append(repl)
                chosen.add(repl["id"])
        # a cserék nem hoznak új X-et, tehát a ciklus véges


def riport(pool: list[dict]) -> dict:
    n = len(pool)
    xs = [r for r in pool if r["gold"] is None and not r.get("ketertelmu")]
    fam = Counter(r["family"] for r in pool)
    return {"n": n, "angol": sum(r["lang"] == "en" for r in pool) / n,
            "konstrukcios": sum(r["family"].startswith(KONSTR) for r in pool) / n,
            "szintetikus": sum(r["family"] in SZINT for r in pool) / n,
            "x": len(xs) / n, "x_tipus": {k: v / max(1, len(xs)) for k, v in Counter(r["x_type"] for r in xs).items()},
            "hosszu": sum(len(r.get("state") or "") > SPEC["hosszu_karakter"] for r in pool) / n,
            "puha": sum(bool(r.get("ketertelmu")) for r in pool),
            "csalad": len(fam), "csaladok": dict(sorted(fam.items()))}


def main() -> None:
    fams = load()
    q, missing = quotas(fams)
    out: dict[str, list[dict]] = {}
    rep: dict = {"hianyzik": missing}
    superset = []  # a szinonimaszűrés céljai: a szűrendő családokban a kvóta TARTALEK-szorosa, kiegyensúlyozás előtt
    for split, mult in (("train", 1.0), ("val", SPEC["val_arany"])):
        pool = []
        for f, n in q.items():
            cand = [r for r in fams[f] if r["split"] == split]
            pool += pick(cand, max(1, round(n * mult)))
            if f in SZINONIM_CSALADOK:
                superset += [r for r in pick(cand, max(1, round(n * mult * TARTALEK))) if r["kind"] == "choice"]
        pool = balance_x_types(pool, fams, split)
        pool.sort(key=lambda r: rank(r["id"]))
        out[split] = pool
        rep[split] = riport(pool)
    F1.mkdir(parents=True, exist_ok=True)
    for split, pool in out.items():
        (F1 / f"pool_{split}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in pool),
                                               encoding="utf-8")
    celok = [{"id": r["id"], "family": r["family"], "split": r["split"]} for r in superset]
    (F1 / "szinonim_celok.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in celok),
                                            encoding="utf-8")
    rep["szinonim_celok"] = dict(Counter(c["family"] for c in celok))
    (F1 / "pool_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    for s in ("train", "val"):
        print(s, json.dumps({k: v for k, v in rep[s].items() if k != "csaladok"}, ensure_ascii=False))
    print("hiányzik:", missing)
    print("szinonimaszűrés céljai:", len(celok), rep["szinonim_celok"])
    if any(v > SPEC["x_tipus_max"] + 1e-9 for v in rep["train"]["x_tipus"].values()):
        print("FIGYELEM: egy X-típus aránya a küszöb fölött maradt (a szintetikus családok hozzák a többi típust)",
              file=sys.stderr)


if __name__ == "__main__":
    main()
