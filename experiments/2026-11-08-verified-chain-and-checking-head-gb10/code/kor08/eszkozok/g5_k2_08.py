"""08 G5 — K2: a lánc a K3-típuson (G1-rögzítés 1., 4., 7.; 08-runbook 2.2, D9).

Családonként a K3-típus itemjei (`lanc08.betolt(<forrás>, <család>)`: a terv `nehez.valt`-ja a változat) három úton:
  lánc nélkül   az alany döntése az eredeti itemen (pontozott szelet, `keret4`)
  kinyert       a lánc a valós kinyeréssel (`lanc_<család>.jsonl` + a modellhez ment itemek pontozott szelete)
  orákulum      ugyanaz a lánc a terv tényeiből vett mezőkkel
**A helyes arány** az eredeti itemhez (`g1_dontes08.helyes`): a lánc automatikus kötése a saját helyességével, az
emberhez küldött tétel nem lezárt (nem helyes, külön sor), a modellhez ment tétel a B1-4S döntésével.
**A lánc hibái (2.2):** a döntést befolyásoló kinyerési hiba (a kimenet, a megmaradt jelöltek, a kötés vagy a modellnek
mutatott tétel a két úton eltér) a valós kinyerés útján; a hamis átengedés = ezek aránya azokon, ahol az ellenőrzés
átment (nem emberhez); hamis kizárás (a gold kizárva) és hamis kötés (a kötés nem a goldra) mindkét úton.
**Bizonytalanság:** sabloncsoportos klaszteres bootstrap (95%), a kinyerés vesztesége (orákulum − kinyert) is.
A D9 fejlesztési célja (a K3-típus helyes aránya ≥ 90% minden családon, a hamis átengedés ≤ 2%) a pontbecslésen és az
intervallumon közölve; változatonként és nyelvenként pontbecslés.

  python3 kor08/eszkozok/g5_k2_08.py --forras K3diag --nelkul cache/k07/k3/diag_{csalad}.json \\
      --kinyert kor08/adat/G1/kinyert_K3diag:cache/k08/pontoz/G1/lK3_{csalad}_DIAG.json \\
      --orakulum kor08/adat/G1/orakulum_K3diag:cache/k08/pontoz/G1/oK3_{csalad}_DIAG.json --out kor08/eredmenyek/G1/g5_k2_pilot
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE)]
import g1_dontes08 as GD  # noqa: E402
import lanc08 as L  # noqa: E402

UTAK = ("nelkul", "kinyert", "orakulum")
CEL_HELYES, CEL_ATENGEDES = 0.90, 0.02


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def pontozott(p: Path) -> dict[str, dict]:
    k4 = json.loads(p.read_text())["keret4"]
    return {i: k4["dontes"][i] for i in k4["ids"]}


def lanc_ut(d: Path, fam: str) -> tuple[dict, dict]:
    return ({r["id"]: r for r in jsonl(d / f"lanc_{fam}.jsonl")}, {r["id"]: r for r in jsonl(d / "items" / f"{fam}.jsonl")})


def csalad(src: str, fam: str, nelkul: Path, kin: tuple[Path, Path], ora: tuple[Path, Path], reps: int,
           rng: np.random.Generator) -> dict:
    pars = [(p, it) for p, it in L.betolt(src, fam)]
    ids = [it["id"] for _, it in pars]
    D = {"nelkul": pontozott(nelkul), "kinyert": pontozott(kin[1]), "orakulum": pontozott(ora[1])}
    lk, mk = lanc_ut(kin[0], fam)
    lo, mo = lanc_ut(ora[0], fam)
    ut_lanc = {"kinyert": lk, "orakulum": lo}
    n = len(ids)
    helyes = {u: np.zeros(n, bool) for u in UTAK}
    kimenet = {u: Counter() for u in UTAK}
    hiba = Counter()
    valt = np.array([p.get("nehez", {}).get("valt", "–") for p, _ in pars])
    lang = np.array([it["lang"] for _, it in pars])
    atment, dbh = np.zeros(n, bool), np.zeros(n, bool)
    for k, (p, it) in enumerate(pars):
        i, st, g = it["id"], it["content_state"], it["gold"]
        if i in D["nelkul"]:
            helyes["nelkul"][k] = GD.helyes(D["nelkul"][i], st, g)
            kimenet["nelkul"]["a modellhez"] += 1
        else:
            kimenet["nelkul"]["nincs kiolvasás (kétértelmű?)"] += 1
        for u in ("kinyert", "orakulum"):
            r = ut_lanc[u][i]
            if r["kimenet"] == "kotes":
                kimenet[u]["automatikus kötés"] += 1
                helyes[u][k] = st == "MATCH" and r["kotes"] == g
                if not helyes[u][k]:
                    hiba[f"{u}: hamis kötés"] += 1
            elif r["kimenet"] == "emberhez":
                kimenet[u]["emberhez"] += 1
            elif i in D[u]:
                kimenet[u]["a modellhez"] += 1
                helyes[u][k] = GD.helyes(D[u][i], st, g)
            else:
                kimenet[u]["nincs kiolvasás"] += 1
            if st == "MATCH" and g in r["kizart"]:
                hiba[f"{u}: hamis kizárás"] += 1
        r, o = lk[i], lo[i]
        atment[k] = r["kimenet"] != "emberhez"
        mut = (mk[i]["state"], mk[i]["options"]) if i in mk else None
        mut_o = (mo[i]["state"], mo[i]["options"]) if i in mo else None
        dbh[k] = atment[k] and ((r["kimenet"], sorted(r["megmaradt"]), r["kotes"], mut)
                                != (o["kimenet"], sorted(o["megmaradt"]), o["kotes"], mut_o))
    cl = defaultdict(list)
    for k, (_, it) in enumerate(pars):
        cl[it["template_group_id"]].append(k)
    clusters = [np.array(v) for v in cl.values()]

    def merok(idx: np.ndarray) -> dict[str, float]:
        m = {u: float(helyes[u][idx].mean()) for u in UTAK}
        m["veszteseg"] = m["orakulum"] - m["kinyert"]
        m["lanc_nyereseg"] = m["kinyert"] - m["nelkul"]
        a = atment[idx]
        m["hamis_atengedes"] = float(dbh[idx][a].mean()) if a.any() else math.nan
        return m
    full = np.arange(n)
    pont = merok(full)
    rep = defaultdict(list)
    for _ in range(reps):
        idx = np.concatenate([clusters[c] for c in rng.integers(0, len(clusters), len(clusters))])
        for k, v in merok(idx).items():
            rep[k].append(v)
    ci = {k: [float(np.nanquantile(v, 0.025)), float(np.nanquantile(v, 0.975))] for k, v in rep.items()}
    bontas = {}
    for nev, kulcs in (("valtozat", valt), ("nyelv", lang)):
        bontas[nev] = {str(x): {**{u: float(helyes[u][kulcs == x].mean()) for u in UTAK}, "n": int((kulcs == x).sum())}
                       for x in sorted(set(kulcs.tolist()))}
    return {"n": n, "sablon": len(clusters), "pont": pont, "ci95": ci, "kimenet": {u: dict(c) for u, c in kimenet.items()},
            "lanc_hibak": dict(hiba), "dbh": int(dbh.sum()), "atment": int(atment.sum()), "bontas": bontas,
            "cel": {"helyes_kinyert_pont": pont["kinyert"] >= CEL_HELYES, "helyes_kinyert_also": ci["kinyert"][0] >= CEL_HELYES,
                    "atengedes_pont": pont["hamis_atengedes"] <= CEL_ATENGEDES,
                    "atengedes_felso": ci["hamis_atengedes"][1] <= CEL_ATENGEDES}}


def f(x, pct: bool = True) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{100 * x:.1f}%".replace(".", ",") if pct else f"{x}"


def lap(res: dict) -> str:
    o = [f"# 08 G5 — K2: a lánc a K3-típuson ({res['cimke']})", "",
         f"Forrás `{res['forras']}`; sabloncsoportos klaszteres bootstrap ({res['reps']} replika), 95%. A helyes arány az eredeti "
         "itemhez; a lánc kötése a saját helyességével; az emberhez küldött tétel nem lezárt. A D9 célja: a valós kinyerés "
         "útján ≥ 90% helyes, a hamis átengedés ≤ 2%.", "",
         "| család | n | lánc nélkül | kinyert | orákulum | a kinyerés vesztesége | hamis átengedés | cél (helyes / átengedés) |",
         "|---|---|---|---|---|---|---|---|"]
    for fam, F in res["csaladok"].items():
        p, c = F["pont"], F["ci95"]

        def x(k: str) -> str:
            return f"{f(p[k])} [{f(c[k][0])}; {f(c[k][1])}]"
        cel = F["cel"]
        o.append(f"| {fam} | {F['n']} | {x('nelkul')} | {x('kinyert')} | {x('orakulum')} | {x('veszteseg')} | "
                 f"{F['dbh']} / {F['atment']}: {x('hamis_atengedes')} | "
                 f"{'igen' if cel['helyes_kinyert_pont'] else 'nem'}{' (az alsó határ is)' if cel['helyes_kinyert_also'] else ''} / "
                 f"{'igen' if cel['atengedes_pont'] else 'nem'}{' (a felső határ is)' if cel['atengedes_felso'] else ''} |")
    for fam, F in res["csaladok"].items():
        o += ["", f"## {fam}", "",
              "Kimenetek: " + "; ".join(f"{u}: " + ", ".join(f"{k} {v}" for k, v in F["kimenet"][u].items()) for u in UTAK) + ".",
              "A lánc hibái: " + (", ".join(f"{k} {v}" for k, v in F["lanc_hibak"].items()) or "nincs") + ".", "",
              "| bontás | n | lánc nélkül | kinyert | orákulum |", "|---|---|---|---|---|"]
        for nev, B in F["bontas"].items():
            for k, v in B.items():
                o.append(f"| {nev}: {k} | {v['n']} | {f(v['nelkul'])} | {f(v['kinyert'])} | {f(v['orakulum'])} |")
    return "\n".join(o) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forras", required=True, choices=list(L.FORRASOK))
    ap.add_argument("--nelkul", required=True, help="a lánc nélküli pontozott szelet, `{csalad}` helyőrzővel")
    ap.add_argument("--kinyert", required=True, help="<lánc könyvtár>:<pontozott szelet>, `{csalad}` helyőrzővel")
    ap.add_argument("--orakulum", required=True, help="<lánc könyvtár>:<pontozott szelet>, `{csalad}` helyőrzővel")
    ap.add_argument("--csalad", action="append", choices=L.CSALADOK)
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--cimke", default="G1 pilot, fejlesztési szám")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    res = {"forras": a.forras, "reps": a.reps, "seed": a.seed, "cimke": a.cimke, "csaladok": {}}
    for fam in a.csalad or L.CSALADOK:
        def pp(s: str) -> tuple[Path, Path]:
            d, p = s.format(csalad=fam).split(":")
            return EXP / d, EXP / p
        res["csaladok"][fam] = csalad(a.forras, fam, EXP / a.nelkul.format(csalad=fam), pp(a.kinyert), pp(a.orakulum), a.reps, rng)
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "g5_k2.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "g5_k2.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


if __name__ == "__main__":
    main()
