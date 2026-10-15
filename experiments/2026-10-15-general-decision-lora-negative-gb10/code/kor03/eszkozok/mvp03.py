"""03-as kör — az MVP train-készlet a poolból (03-runbook 10. pont 4., 5., 10., 14., 15., 17.; 2. és 8. pont).

v2 (Dani, 2026-10-12, 10. pont 17.): a v1-ben az 50%-os típussapka 642 gold-drop X-et ugyanannak a családnak nem-X
itemjére cserélt, így a gold-drop családok X-aránya a val-énál kisebb lett (pl. NJT 8% vs. 14%), és a G3 a val-on a
gold-drop X-et rosszabbul fedte (0,850 → 0,772). A v2-ben a gold-drop családokban a jelöltkészlet X-aránya marad, és
a típussapka 60% (így nincs csere). A v1 (`*_v1`) a pilot és a tanulási görbe adata.

Szabályok:
  - méret N = 17 500 (a 15–20 ezres sáv közepe);
  - kizárva: a HuSST és a HuCommitmentBank (10. pont 15.), a gépi zajbecslés zajjelöltjei (adat/f2/zajjelolt.jsonl), és
    ami horgony nélkül maradt (a 8192-es kontextusba nem fért train-item);
  - a plafon közeli családok (eredmenyek/F2/f2_elemzes.json) együtt legfeljebb N 5%-a, egymás közt a poolbeli méretük
    arányában (10. pont 4.);
  - angol 25% (10. pont 5.), konstrukciós ≤ 15%, szintetikus ≤ 30%; a többi magyar család a poolbeli méretük arányában;
  - a gold-drop családokban (ahol a jelöltek X-e gold-drop) az X-arány a jelöltkészleté; a többi családban az X
    elsőbbséget kap, legfeljebb a családi kvóta 30%-áig (2. pont: X családonként ≤ 30%), mert a nem gold-drop X kevés;
  - egy X-típus sem több az X-ek 60%-ánál (v1: 50%): a többletet (a legrosszabb rangúakat) ugyanannak a családnak nem-X
    itemjei váltanák, mint a keverőben; a v2-ben ez nem fut le;
  - a hosszú item (> 6000 karakter) ≤ 10% (ellenőrzés);
  - tanulási görbe (8. pont, F3): családonként rang szerint az első negyed `gorbe` = 25, a második 50, a többi 100; a
    részhalmazok egymásba ágyazottak.
A választás determinisztikus (hash-rang). A végén minden szabályt ellenőriz; ha valamelyik sérül, hibával kilép.

  python3 kor03/eszkozok/mvp03.py   → adat/f3/mvp_train_v2.jsonl, eredmenyek/F3/mvp_riport_v2.json
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F1, F2A, F3A, F2R, F3R = (ROOT / p for p in ("adat/f1", "adat/f2", "adat/f3", "eredmenyek/F2", "eredmenyek/F3"))
SEED = "mvp03:2026-10-11"
VERZIO = "v2"
N = 17_500
PLAFON_MAX, ANGOL, KONSTR_MAX, SZINT_MAX, X_CSALAD_MAX, X_TIPUS_MAX, HOSSZU_MAX = 0.05, 0.25, 0.15, 0.30, 0.30, 0.60, 0.10
HOSSZU_KARAKTER = 6000
KIZART_FORRAS = ("HuSST", "HuCommitmentBank")
KONSTR = ("konstrukcios.", "jogi.njt_")
SZINT = ("level.triage", "level.dokumentumtipus", "level.szerzodesklauzula", "entitas.egyezes", "rag.relevancia",
         "rag.valaszbiralat", "jogi.hivatali_ugytipus")


def rank(iid: str) -> str:
    return hashlib.sha256(f"{SEED}:{iid}".encode()).hexdigest()


def rows(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines()]


def is_x(r: dict) -> bool:
    return r["gold"] is None and not r.get("ketertelmu")


def proportional(sizes: dict[str, int], budget: int) -> dict[str, int]:
    """A keret szétosztása a méretek arányában (legnagyobb maradék), a méretet sapkaként tartva."""
    alloc = dict.fromkeys(sizes, 0)
    open_ = {f for f, n in sizes.items() if n > 0}
    left = budget
    while left > 0 and open_:
        tot = sum(sizes[f] for f in open_)
        share = {f: left * sizes[f] / tot for f in open_}
        add = {f: min(int(share[f]), sizes[f] - alloc[f]) for f in open_}
        rem = left - sum(add.values())
        for f in sorted(open_, key=lambda f: (-(share[f] - int(share[f])), f)):
            if rem <= 0:
                break
            if alloc[f] + add[f] < sizes[f]:
                add[f] += 1
                rem -= 1
        for f in open_:
            alloc[f] += add[f]
        left = budget - sum(alloc.values())
        full = {f for f in open_ if alloc[f] >= sizes[f]}
        if not full and sum(add.values()) == 0:
            break
        open_ -= full
    return alloc


def pick(items: list[dict], k: int, gold_drop: bool) -> list[dict]:
    """k item hash-rang szerint. Gold-drop családban az X-arány a jelöltkészleté; máshol előbb az X (legfeljebb a k
    30%-a), a többi nem-X."""
    items = sorted(items, key=lambda r: rank(r["id"]))
    xs, nx = [r for r in items if is_x(r)], [r for r in items if not is_x(r)]
    if gold_drop:
        kx = min(len(xs), round(k * len(xs) / len(items)))
    else:
        kx = min(len(xs), int(X_CSALAD_MAX * k))
    knx = min(len(nx), k - kx)
    return xs[:kx] + nx[:knx]


def balance_x_types(chosen: list[dict], fams: dict[str, list[dict]]) -> tuple[list[dict], int]:
    """Ha egy X-típus az X-ek több mint X_TIPUS_MAX részét adja, a legrosszabb rangú többletet ugyanannak a családnak
    még nem választott nem-X itemjei váltják. Visszaadja a cserék számát is."""
    ids = {r["id"] for r in chosen}
    swaps = 0
    while True:
        xs = [r for r in chosen if is_x(r)]
        top, c = Counter(r["x_type"] for r in xs).most_common(1)[0]
        excess = c - int(X_TIPUS_MAX * len(xs))
        if excess <= 0:
            return chosen, swaps
        drop = sorted((r for r in xs if r["x_type"] == top), key=lambda r: rank(r["id"]), reverse=True)[:excess]
        drop_ids = {r["id"] for r in drop}
        chosen = [r for r in chosen if r["id"] not in drop_ids]
        for r in drop:
            repl = next((x for x in sorted(fams[r["family"]], key=lambda x: rank(x["id"]))
                         if x["id"] not in ids and not is_x(x)), None)
            if repl:
                chosen.append(repl)
                ids.add(repl["id"])
                swaps += 1


def main() -> None:
    pool = rows(F1 / "pool_train.jsonl")
    plafon = set(json.loads((F2R / "f2_elemzes.json").read_text(encoding="utf-8"))["csaladvalasztas"]["plafon_kozeli"])
    zaj = {r["id"] for r in rows(F2A / "zajjelolt.jsonl")}
    horgony = {json.loads(line)["id"] for line in (F2A / "horgony_qwen_L1.jsonl").open(encoding="utf-8")}
    kiz = Counter()
    cand = []
    for r in pool:
        if r["source"] in KIZART_FORRAS:
            kiz[r["source"]] += 1
        elif r["id"] in zaj:
            kiz["zajjelolt"] += 1
        elif r["id"] not in horgony:
            kiz["horgony_nelkul"] += 1
        else:
            cand.append(r)
    fams: dict[str, list[dict]] = defaultdict(list)
    for r in cand:
        fams[r["family"]].append(r)
    size = {f: len(v) for f, v in fams.items()}
    lang = {f: v[0]["lang"] for f, v in fams.items()}

    # keretek: plafon közeli → angol → magyar (konstrukciós sapkával)
    P = {f: size[f] for f in fams if f in plafon}
    a_p = proportional(P, int(PLAFON_MAX * N))
    en_p = sum(n for f, n in a_p.items() if lang[f] == "en")
    a_e = proportional({f: size[f] for f in fams if f not in plafon and lang[f] == "en"}, round(ANGOL * N) - en_p)
    H = {f: size[f] for f in fams if f not in plafon and lang[f] != "en"}
    b_h = N - sum(a_p.values()) - sum(a_e.values())
    a_h = proportional(H, b_h)
    konstr_cap = int(KONSTR_MAX * N) - sum(n for f, n in a_p.items() if f.startswith(KONSTR))
    if sum(n for f, n in a_h.items() if f.startswith(KONSTR)) > konstr_cap:
        a_k = proportional({f: n for f, n in H.items() if f.startswith(KONSTR)}, konstr_cap)
        a_h = a_k | proportional({f: n for f, n in H.items() if not f.startswith(KONSTR)}, b_h - sum(a_k.values()))
    alloc = a_p | a_e | a_h

    gd_fams = {f for f, v in fams.items() if any(is_x(r) and r["x_type"] == "gold-drop" for r in v)}
    chosen = [r for f, k in sorted(alloc.items()) for r in pick(fams[f], k, f in gd_fams)]
    chosen, swaps = balance_x_types(chosen, fams)

    # tanulási görbe: családonként rang szerint negyedek
    by_f = defaultdict(list)
    for r in chosen:
        by_f[r["family"]].append(r)
    for rs in by_f.values():
        rs.sort(key=lambda r: rank(r["id"]))
        q1, q2 = math.ceil(0.25 * len(rs)), math.ceil(0.5 * len(rs))
        for i, r in enumerate(rs):
            r["gorbe"] = 25 if i < q1 else 50 if i < q2 else 100
    chosen.sort(key=lambda r: rank(r["id"]))

    # riport és ellenőrzés
    n = len(chosen)
    xs = [r for r in chosen if is_x(r)]
    fam_n = Counter(r["family"] for r in chosen)
    fam_x = Counter(r["family"] for r in xs)
    rep = {
        "n": n, "seed": SEED, "verzio": VERZIO, "kizart": dict(kiz),
        "angol": sum(r["lang"] == "en" for r in chosen) / n,
        "konstrukcios": sum(r["family"].startswith(KONSTR) for r in chosen) / n,
        "szintetikus": sum(r["family"] in SZINT for r in chosen) / n,
        "plafon_kozeli": sum(r["family"] in plafon for r in chosen) / n,
        "x": len(xs) / n, "x_db": len(xs), "x_tipus": dict(Counter(r["x_type"] for r in xs).most_common()),
        "x_tipus_csere": swaps,
        "gold_drop_csaladok": {f: {"mvp_x": fam_x[f] / fam_n[f], "jelolt_x": sum(map(is_x, fams[f])) / size[f]}
                               for f in sorted(gd_fams) if fam_n[f]},
        "x_csalad_max": max(fam_x[f] / fam_n[f] for f in fam_n),
        "x_nelkuli_csalad": sum(1 for f in fam_n if fam_x[f] == 0),
        "hosszu": sum(len(r.get("state") or "") > HOSSZU_KARAKTER for r in chosen) / n,
        "ketertelmu": sum(bool(r.get("ketertelmu")) for r in chosen),
        "csoport": dict(Counter(r["group"] for r in chosen).most_common()),
        "gorbe": {lv: sum(r["gorbe"] <= lv for r in chosen) for lv in (25, 50, 100)},
        "csaladok": {f: {"n": fam_n[f], "x": fam_x[f], "pool": size[f], "plafon_kozeli": f in plafon}
                     for f in sorted(fam_n)},
    }
    checks = {
        "méret": n == N,
        "egyedi id": len({r["id"] for r in chosen}) == n,
        "nincs kizárt": not any(r["source"] in KIZART_FORRAS or r["id"] in zaj or r["id"] not in horgony for r in chosen),
        "angol 25%": abs(rep["angol"] - ANGOL) < 0.005,
        "konstrukciós ≤ 15%": rep["konstrukcios"] <= KONSTR_MAX + 1e-9,
        "szintetikus ≤ 30%": rep["szintetikus"] <= SZINT_MAX + 1e-9,
        "plafon közeli ≤ 5%": rep["plafon_kozeli"] <= PLAFON_MAX + 1e-9,
        "X-típus ≤ 60%": max(rep["x_tipus"].values()) <= X_TIPUS_MAX * len(xs) + 1e-9,
        "gold-drop családok X-aránya = jelöltkészlet (±1 item)": all(
            abs(v["mvp_x"] - v["jelolt_x"]) * fam_n[f] <= 1 for f, v in rep["gold_drop_csaladok"].items()),
        "X családon belül ≤ 30%": rep["x_csalad_max"] <= X_CSALAD_MAX + 1e-9,
        "legalább két X nélküli család": rep["x_nelkuli_csalad"] >= 2,
        "hosszú ≤ 10%": rep["hosszu"] <= HOSSZU_MAX,
    }
    rep["ellenorzes"] = checks
    F3A.mkdir(parents=True, exist_ok=True)
    F3R.mkdir(parents=True, exist_ok=True)
    out = F3A / f"mvp_train_{VERZIO}.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in chosen), encoding="utf-8")
    rep["sha256"] = hashlib.sha256(out.read_bytes()).hexdigest()
    (F3R / f"mvp_riport_{VERZIO}.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k != "csaladok"}, ensure_ascii=False, indent=1))
    if not all(checks.values()):
        raise SystemExit(f"sérült szabály: {[k for k, v in checks.items() if not v]}")


if __name__ == "__main__":
    main()
