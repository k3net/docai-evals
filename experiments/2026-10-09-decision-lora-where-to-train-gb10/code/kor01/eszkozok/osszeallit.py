"""01-es kör — az itemek összeállítása (F1, CPU-rész; 01-runbook 2–4. pont).

Bemenet: kor01/adat/*.jsonl (forras_konvertal.py) + kor01/katalogus/eszkozok.json. Kimenet: kor01/adat/items_{train,val,
teszt}.jsonl + osszeallit_riport.json (méretek, X-arány, opciószám-eloszlás, shortcut-audit).

Paraméterek (a 01-runbook 4. pontjában rögzítendők; a 00 tanulságai szerint):
- train-keverék: forrásonként felső korlát (TRAIN_MIX), hogy egy epoch egy éjszakába férjen (a 00: 5593 item ≈ 2 óra);
- kitartott eszközök: az xLAM-eszköznevek HOLDOUT_FRAC része csak a val-ban szerepel (T-új-eszköz jellegű val);
  ha egy item bármely opciója kitartott, az item nem lehet train;
- MASSIVE-listák a katalógusból: opciószám a 00 empirikus eloszlásával (2–10, medián 7); a gold közeli párjai
  NEAR_P valószínűséggel kerülnek be; gold-drop (X(a)) a tool-itemek GOLD_DROP részén, a gold helyére pótlással
  (az opciószám ne árulja el az X-et), és ilyenkor a gold `felulvizsgal` párjai sem kerülhetnek a listára (hamis X);
- xlam-irrelevance: csak a párosított (az xLAM-párja is bent van) itemek, és a kivett gold helyére egy véletlen, nem
  rokon eszköz kerül (pótlás); az xLAM eszközös itemei ugyanerre az opciószám-eloszlásra pótolva (az 1 opciós
  xLAM-itemeknek nincs X-párja, különben az 1 opció elárulná, hogy nem X);
- When2Call-train: az X-arány W2C_X-re állítva; az egyeszközös (visszakérdezés → gold) itemek véletlen eszközökkel
  pótolva az X-itemek opciószám-eloszlására (különben az 1 opció elárulja, hogy nem X);
- a kitartott eszközök közé katalógusnév nem kerülhet (a MASSIVE-itemek a trainben azonos nevet hordoznak);
- a val a 00 plafon-leletéből nehezített: MASSIVE dev 6–10 opcióval, több közeli párral.
"""

from __future__ import annotations

import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
A = ROOT / "adat"
SEED = 20261006
TRAIN_MIX = {"xlam": 6000, "xlam_irrel": 2000, "w2c_train": 2000, "massive_hu": 4500}
W2C_X = 0.25  # a When2Call-train X-aránya a keverékben (a forrás 67%-a helyett; a családok X-aránya egyezzen)
HOLDOUT_FRAC = 0.08
VAL_XLAM = 1500
GOLD_DROP = 0.25
NEAR_P = 0.6
# a 00-ás adat opciószám-eloszlása (2..10)
N_OPT_W = {2: 150, 3: 242, 4: 379, 5: 879, 6: 1340, 7: 2248, 8: 2429, 9: 1844, 10: 622}
N_OPT_VAL = {k: v for k, v in N_OPT_W.items() if k >= 6}


def jl(name: str) -> list[dict]:
    return [json.loads(line) for line in open(A / name)]


def draw(weights: dict, rng: random.Random) -> int:
    ks = list(weights)
    return rng.choices(ks, weights=[weights[k] for k in ks])[0]


def catalog() -> tuple[dict, list[str]]:
    cat = json.loads((ROOT / "katalogus/eszkozok.json").read_text())
    tools = {t["name"]: t for t in cat}
    return tools, sorted(tools)


def cat_opt(t: dict) -> dict:
    return {"id": t["name"], "name": t["name"], "description": t["leiras"],
            "required": [p["name"] for p in t["params"] if p["required"]]}


def massive_items(rows: list[dict], split: str, rng: random.Random, n_w: dict, near_p: float,
                  forras: str = "massive_hu") -> list[dict]:
    tools, names = catalog()
    out = []
    for r in rows:
        g = r["gold_eszkoz"]
        n = draw(n_w, rng)
        meta = {**r["meta"], "x_fajta": None, "felulvizsgal_jelen": False}
        if g is None:  # csevegés: természetes X, bármilyen lista
            pool = names[:]
            rng.shuffle(pool)
            opts, gold, meta["x_fajta"] = pool[:n], None, "csevegés"
        else:
            drop = rng.random() < GOLD_DROP
            banned = {g} | (set(tools[g]["felulvizsgal"]) if drop else set())
            near = [k for k in tools[g]["kozeli"] if k not in banned and rng.random() < near_p]
            rest = [k for k in names if k not in banned and k not in near]
            rng.shuffle(rest)
            body = near + rest
            if drop:
                opts, gold, meta["x_fajta"] = body[:n], None, "gold-drop"
            else:
                opts, gold = [g] + body[: n - 1], g
                meta["felulvizsgal_jelen"] = any(k in opts for k in tools[g]["felulvizsgal"])
        rng.shuffle(opts)
        out.append({"id": r["id"], "forras": forras, "split": split, "lang": "hu", "request": r["request"], "history": [],
                    "options": [cat_opt(tools[k]) for k in opts], "gold": gold, "meta": meta})
    return out


def gold_drop(items: list[dict], frac: float, pool: list[dict], rng: random.Random) -> None:
    """X(a) a 00 S7 receptjével: a gold helyére véletlen, más nevű eszköz — az opciószám és a kérés-populáció egyezik."""
    for it in rng.sample(items, int(len(items) * frac)):
        have = {o["id"] for o in it["options"]}
        while True:
            cand = rng.choice(pool)
            if cand["id"] not in have:
                break
        k = next(n for n, o in enumerate(it["options"]) if o["id"] == it["gold"])
        it["meta"].update({"x_fajta": "gold-drop", "kivett_gold": it["gold"], "potlas": cand["id"], "felulvizsgal_jelen": True})
        it["options"][k] = cand
        it["gold"] = None


def match_len(xs: list[dict], ts: list[dict], n: int, rng: random.Random, bins: int = 10) -> list[dict]:
    """n X-item a tool-itemek kéréshossz-eloszlásához illesztve (decilisenként arányos mintavétel)."""
    lt = np.array([len(i["request"]) for i in ts])
    edges = np.quantile(lt, np.linspace(0, 1, bins + 1)[1:-1])
    cell = defaultdict(list)
    for i in xs:
        cell[int(np.searchsorted(edges, len(i["request"])))].append(i)
    out = []
    for b in range(bins):
        rng.shuffle(cell[b])
        out += cell[b][: n // bins]
    return out


def pad_irrel(items: list[dict], pool: list[dict], rng: random.Random, pair_gold: dict) -> None:
    """xlam-irrelevance: a kivett gold helyére egy véletlen, más nevű eszköz — az opciószám ne árulja el az X-et."""
    for it in items:
        have = {o["id"] for o in it["options"]} | {pair_gold.get(it["meta"]["klaszter"])}
        while True:
            cand = rng.choice(pool)
            if cand["id"] not in have:
                break
        pos = rng.randrange(len(it["options"]) + 1)
        it["options"].insert(pos, cand)
        it["meta"]["potlas"] = cand["id"]
        it["meta"]["x_fajta"] = "gold-drop"


def pad_to_dist(items: list[dict], dist: Counter, pool: list[dict], rng: random.Random) -> None:
    """Véletlen, más nevű eszközökkel pótol a megadott opciószám-eloszlásra (a gold változatlan)."""
    ks, ws = list(dist), [dist[k] for k in dist]
    for it in items:
        target = max(len(it["options"]), rng.choices(ks, weights=ws)[0])
        have = {o["id"] for o in it["options"]}
        while len(it["options"]) < target:
            cand = rng.choice(pool)
            if cand["id"] not in have:
                it["options"].insert(rng.randrange(len(it["options"]) + 1), cand)
                have.add(cand["id"])
        it["meta"]["potlas_db"] = target - it["meta"]["n_tools"]


def auc(score: np.ndarray, y: np.ndarray) -> float:
    pos, neg = score[y == 1], score[y == 0]
    if not len(pos) or not len(neg):
        return float("nan")
    ranks = rankdata(np.concatenate([pos, neg]))  # holtversenyben átlagrang (az opciószámnál sok a holtverseny)
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def shortcut(items: list[dict]) -> dict:
    """Egyváltozós AUC az X-re (0,5 = nincs szivárgás): opciószám, kéréshossz, átlagos leíráshossz."""
    y = np.array([i["gold"] is None for i in items], dtype=int)
    feats = {"opcioszam": [len(i["options"]) for i in items], "kereshossz": [len(i["request"]) for i in items],
             "leirashossz": [np.mean([len(o["description"]) for o in i["options"]]) for i in items]}
    return {k: round(max(a := auc(np.array(v, dtype=float), y), 1 - a), 3) for k, v in feats.items()}


def families(items: list[dict]) -> dict[str, list[dict]]:
    fam = defaultdict(list)
    for i in items:
        f = i["forras"]
        fam["xlam" if f.startswith("xlam") else "bfcl" if f.startswith("bfcl") else f].append(i)
    return {k: v for k, v in fam.items() if any(x["gold"] is None for x in v) and any(x["gold"] is not None for x in v)}


def main() -> None:
    rng = random.Random(SEED)
    xl, xi, wt = jl("xlam_train.jsonl"), jl("xlam_irrel_train.jsonl"), jl("w2c_train.jsonl")
    ms = jl("massive_hu.jsonl")

    # kitartott xLAM-eszközök → val
    cat_names = set(catalog()[1])
    names = sorted({o["id"] for i in xl for o in i["options"]} - cat_names)
    held = set(rng.sample(names, int(len(names) * HOLDOUT_FRAC)))
    touches = lambda it: any(o["id"] in held for o in it["options"])  # noqa: E731
    by_cl = defaultdict(list)
    for it in xl + xi:
        by_cl[it["meta"]["klaszter"]].append(it)
    val_cl = {c for c, its in by_cl.items() if any(i["gold"] in held for i in its if i["gold"])}
    pair_gold = {i["meta"]["klaszter"]: i["gold"] for i in xl}
    pool = [o for i in xl for o in i["options"] if o["id"] not in held]

    def train_ok(it):
        return it["meta"]["klaszter"] not in val_cl and not touches(it)
    xl_cl = {i["meta"]["klaszter"] for i in xl}
    xi = [i for i in xi if i["meta"]["klaszter"] in xl_cl]  # csak párosított: a kéréshossz-eloszlás egyezzen
    tr_xl = [i for i in xl if train_ok(i)]
    tr_xi = [i for i in xi if train_ok(i)]
    tr_wt = [i for i in wt if not touches(i)]
    for src in (tr_xl, tr_xi, tr_wt):
        rng.shuffle(src)
    # az xLAM-család X-e saját gold-drop pótlással (a 00 S7 receptje): így az opciószám és a kérés-populáció
    # azonos az X és a nem-X között; az xlam-irrelevance (Hammer) ugyanez a recept pótlás nélkül, és a többhívásos
    # kérésekből is merít → csak hivatkozási forrás, az itemek nem kerülnek be
    tr_xl = tr_xl[: TRAIN_MIX["xlam"] + TRAIN_MIX["xlam_irrel"]]
    gold_drop(tr_xl, TRAIN_MIX["xlam_irrel"] / len(tr_xl), pool, rng)
    tr_xi = []
    n_x = int(TRAIN_MIX["w2c_train"] * W2C_X)
    w_t = [i for i in tr_wt if i["gold"] is not None][: TRAIN_MIX["w2c_train"] - n_x]
    w_x = match_len([i for i in tr_wt if i["gold"] is None], w_t, n_x, rng)
    pad_to_dist(w_t, Counter(len(i["options"]) for i in w_x), pool, rng)
    tr_wt = w_x + w_t
    ms_tr = [r for r in ms if r["split"] == "train"]
    rng.shuffle(ms_tr)
    train = (tr_xl + tr_xi + tr_wt
             + massive_items(ms_tr[: TRAIN_MIX["massive_hu"]], "train", rng, N_OPT_W, NEAR_P))

    va_xl = [i for i in xl if i["meta"]["klaszter"] in val_cl]
    va_xi = [i for i in xi if i["meta"]["klaszter"] in val_cl]
    pad_irrel(va_xi, [o for i in xl for o in i["options"]], rng, pair_gold)
    rng.shuffle(va_xl)
    va_xl = va_xl[: VAL_XLAM]
    gold_drop(va_xl, 0.25, [o for i in xl for o in i["options"]], rng)
    va = va_xl
    for it in va:
        it["split"] = "val"
    val = va + massive_items([r for r in ms if r["split"] == "val"], "val", rng, N_OPT_VAL, 0.9)

    teszt = jl("bfcl_teszt.jsonl") + jl("w2c_teszt.jsonl") + massive_items(
        [r for r in ms if r["split"] == "teszt"], "teszt", rng, N_OPT_W, NEAR_P)

    rep = {"parameterek": {"seed": SEED, "train_mix": TRAIN_MIX, "holdout_frac": HOLDOUT_FRAC, "val_xlam": VAL_XLAM,
                           "gold_drop": GOLD_DROP, "near_p": NEAR_P, "kitartott_eszkoz": len(held)}}
    for name, items in (("train", train), ("val", val), ("teszt", teszt)):
        with open(A / f"items_{name}.jsonl", "w") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        src = Counter(i["forras"] for i in items)
        xr = {s: round(sum(i["gold"] is None for i in items if i["forras"] == s) / n, 3) for s, n in src.items()}
        rep[name] = {"n": len(items), "forrasok": dict(src), "x_arany": xr,
                     "x_arany_osszes": round(sum(i["gold"] is None for i in items) / len(items), 3),
                     "opcioszam": dict(sorted(Counter(len(i["options"]) for i in items).items())),
                     "felulvizsgalando": sum(bool(i["meta"].get("felulvizsgal_jelen")) for i in items),
                     "shortcut_auc": shortcut(items),
                     "shortcut_auc_csaladonkent": {fam: shortcut(its) for fam, its in families(items).items()}}
    leak = [i for i in val if i["forras"] in ("xlam", "xlam_irrel") and any(o["id"] in {p["id"] for t in train for p in t["options"]}
                                                                           for o in i["options"] if o["id"] in held)]
    rep["ellenorzes"] = {"val_kitartott_eszkoz_a_trainben": len(leak),
                         "train_klaszter_a_valban": len({i["meta"]["klaszter"] for i in train} & {i["meta"]["klaszter"] for i in val})}
    (A / "osszeallit_riport.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))
    print(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
