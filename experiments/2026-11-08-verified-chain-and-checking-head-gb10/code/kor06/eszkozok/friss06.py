"""06-os kör — a B1-R, a B1-LR és a H-T-meta tanítása és értékelése a friss családokon (06-runbook 5., 8., F5).

A tanítás a `b1rel06.f1` útja változtatás nélkül, a `kiolvas06` mintájára csak a betöltők cserélődnek:
  - meta és szeletek a 06-os itemekből (`kor06/adat/f2/items`); szeletnév `<család>:<szelet>`; az alapeset az item
    (D12: alapesetenként egy item), a T100 ⊂ T200 ⊂ T500 húzásai alapesetenként (3.2);
  - jellemzők: a T500 a `cache/k06/jellemzok`, a CAL és a TESZT a `cache/k06/pecset/jellemzok` alól, a pecsét kapujával
    (csak a v1 rögzítése után olvasható);
  - a fold-egység a sabloncsoport (D23): a finomhangolás öt foldja, a belső korai megállás és a B1-LR C-jének
    keresztvalidációja a `template_group_id` szerint, hogy egy sablon ne legyen egyszerre tanító- és validációs oldalon.
Az értékelés az `elemzes06` mérőivel a TESZT-en, családonként és nyelvenként; a bootstrap klasztere a sabloncsoport
(D23; a 8.2 „alapesete” a 06-ban maga az item), 10 000 ismétlés, seed 20261029; a pont és a replika is a futások
(seed × húzás) mérőinek átlaga, a futások közti eltérés külön (D24); a 8.3 szabály a D4-gyel (az átlagos arány 95%-os
felső határa < 1); a családonkénti p-k Holm-korrekcióval (leíró); a T100 / T200 húzásainak sablonszáma.

  python3 kor06/eszkozok/friss06.py tanit --csalad penzugy.bankparositas --out cache/k06/f5
  python3 kor06/eszkozok/friss06.py elemez --be cache/k06/f5 --out kor06/eredmenyek/F5
  python3 kor06/eszkozok/friss06.py munkapont --be cache/k06/f5 --out kor06/eredmenyek/F5   (8.4, leíró)
  python3 kor06/eszkozok/friss06.py bontas --be cache/k06/f5 --out kor06/eredmenyek/F5      (D20, NONE / SELECT)
  python3 kor06/eszkozok/friss06.py fusteszt --out cache/k06/f5_fust   (a T500-on, a pecsét nélkül; értéket nem ír ki)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import b1rel06 as B  # noqa: E402
import elemzes05 as E  # noqa: E402
import elemzes06 as A  # noqa: E402
import kalib05 as K  # noqa: E402
import pecset06  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
ITEMS = EXP / "kor06/adat/f2/items"
JELL = EXP / "cache/k06/jellemzok"
PECSET_JELL = EXP / "cache/k06/pecset/jellemzok"
PECSETELT = ("CAL", "TESZT")
NYELVEK = ("hu", "en")


# --- a 06-os betöltők -------------------------------------------------------------------------------------------------

def _items() -> dict[str, dict]:
    return {it["id"]: it for f in CSALADOK for it in K.jsonl(ITEMS / f"{f}.jsonl")}


ITEM = _items()
SABLON = {i: it["template_group_id"] for i, it in ITEM.items()}
_META = {i: {"group_id": it["group_id"], "family": it["family"], "split": it["split"], "state": it["content_state"],
             "gold_set": {it["gold"]} if it["gold"] is not None else set(), "ketertelmu": bool(it.get("ketertelmu")),
             "lang": it["lang"]} for i, it in ITEM.items()}


def meta() -> dict:
    return _META


def szelet_ids(name: str) -> list[str]:
    """`<család>:<szelet>` vagy `<család>:<szelet>:<nyelv>` (a magyar bontáshoz)."""
    fam, sz, *lang = name.split(":")
    if fam not in CSALADOK:
        raise SystemExit(f"ismeretlen szelet: {name}")
    return [i for i, m in _META.items() if m["family"] == fam and m["split"] == sz and (not lang or m["lang"] == lang[0])]


def root(kind: str, szelet: str) -> Path:
    if kind != "jellemzok":
        raise SystemExit(f"a 06-ban nincs {kind}")
    if szelet.split(":")[1] in PECSETELT:
        pecset06.kapu(PECSET_JELL)
        return PECSET_JELL
    return JELL


class Slice06(E.Slice):
    """A 05 `Slice`-a a 06-os szeletekre: a bootstrap klasztere (család → sabloncsoport) a sablon (D23)."""

    def __init__(self, name: str, one_per_group: bool = False):
        ids = sorted(i for i in szelet_ids(name) if not _META[i]["ketertelmu"])  # alapesetenként egy item: one_per_group = mind
        self.name, self.ids = name, ids
        self.state = np.array([E.STATE_CODE[_META[i]["state"]] for i in ids])
        fam = defaultdict(lambda: defaultdict(list))
        for n, i in enumerate(ids):
            fam[_META[i]["family"]][SABLON[i]].append(n)
        self.fams = [[np.array(v) for v in g.values()] for g in fam.values()]
        self.family = [_META[i]["family"] for i in ids]


_h = B.h


def h_sablon(tag: str, g: str) -> int:
    """A fold-hash az alapeset sablonjára (D23); a T100/T200-húzás (`b1rel06.huzas`) alapesetenként marad."""
    return _h(tag, SABLON.get(g, g))


def rep_atlag(tabs: list[list[E.Tab]], s, sel, none, rng: np.random.Generator) -> np.ndarray:
    """D24: replikánként ugyanazokon a sabloncsoportokon minden futás (seed × húzás) mérője, és ezek átlaga, ahogy a
    pontbecslés is a futások átlaga (az `elemzes06.rep` replikánként egy seedet és egy húzást sorsolt)."""
    return np.mean([A.merok(t, s, sel, none) for row in tabs for t in row], axis=0)


def telepit() -> None:
    K.meta = meta
    K._root = root
    E.Slice = Slice06
    B.h = h_sablon
    A.rep = rep_atlag


# --- tanítás ----------------------------------------------------------------------------------------------------------

def tanit(a) -> None:
    telepit()
    tesztek = tuple(f"{a.csalad}:{s}" for s in a.tesztek.split(","))
    B.F1 = {a.csalad: (f"{a.csalad}:T500", tesztek)}
    B.f1(argparse.Namespace(reteg=a.csalad, elotanitott=a.elotanitott, out=a.out))


# --- értékelés --------------------------------------------------------------------------------------------------------

def holm(ps: dict[str, float]) -> dict[str, float]:
    k = sorted(ps, key=ps.get)
    out, prev = {}, 0.0
    for r, name in enumerate(k):
        prev = max(prev, min(1.0, (len(k) - r) * ps[name]))
        out[name] = prev
    return out


def futasok(f: dict, t: str, key: str) -> dict:
    """D24: a futások (seed × húzás) közti eltérés a teljes szeleten: karonként a futásonkénti AURC és ΔAURC (B1-S-hez)."""
    L = Slice06(t)
    T = A.karok(f, t, key, L.ids)
    s0 = L.full()
    b1 = T["B1-S"][0][0]
    a0 = A.merok(b1, s0, b1.sel, b1.none)[0]
    out = {}
    for k, v in T.items():
        x = [A.merok(tab, s0, b1.sel, b1.none)[0] for row in v for tab in row]
        if len(x) > 1:
            d = [y - a0 for y in x]
            out[k] = {"aurc": x, "delta_B1S": d, "delta_min": min(d), "delta_max": max(d), "delta_sd": float(np.std(d, ddof=1))}
    return out


def minta_sablonok() -> dict:
    """A T100 / T200 húzásainak sablonszáma családonként (a `b1rel06.f1` húzásával: alapesetenként, `k06-minta:<d>`)."""
    out = {}
    for fam in CSALADOK:
        groups = sorted(i for i in szelet_ids(f"{fam}:T500") if not _META[i]["ketertelmu"])
        out[fam] = {"T500": len({SABLON[i] for i in groups}),
                    **{f"T{n}": [len({SABLON[i] for i in B.huzas(groups, fam, d)[:n]}) for d in range(B.HUZASOK)]
                       for n in (100, 200)}}
    return out


def elemez(a) -> None:
    telepit()
    tesz = a.teszt_szelet
    res = {"reps": a.reps, "seed": a.seed, "teszt_szelet": tesz, "klaszter": "sabloncsoport", "helyesseg": {}, "kapu": {},
           "holm_p": {}, "nyelv": {}}
    files = {f: Path(a.be) / f / "f1.json" for f in CSALADOK}
    for key in A.KULCSOK:
        rng = np.random.default_rng(a.seed)
        blk, lang_blk = {}, {}
        for fam, p in files.items():
            f = json.loads(p.read_text())
            t = f"{fam}:{tesz}"
            blk[t] = A.elemez(f, t, key, a.reps, rng)
            for lg in NYELVEK:
                # a nyelvi részszelet a teljes szelet soraiból: a `karok` az itemsorrendet a részszeletre illeszti
                lang_blk[f"{t}:{lg}"] = A.elemez({**f, "B1": {f"{t}:{lg}": f["B1"][t]},
                                                  "H": {k.replace(f"|{t}", f"|{t}:{lg}"): v for k, v in f["H"].items()},
                                                  "pontszam": {k.replace(f"|{t}", f"|{t}:{lg}"): v
                                                               for k, v in f["pontszam"].items() if k.endswith(f"|{t}")}},
                                                 f"{t}:{lg}", key, a.reps, rng)
            print(f"{key} {fam} kész", flush=True)
        res.setdefault("futasok", {})[key] = {t: futasok(json.loads(files[t.split(":")[0]].read_text()), t, key)
                                               for t in blk}
        A.SZURO = tuple(f"{fam}:{tesz}" for fam in CSALADOK)
        kp = A.kapu(blk)
        kp["d4"] = bool(kp["arany_ci95"][1] < 1.0)
        kp["teljesul_d4"] = bool(kp["teljesul"] and kp["d4"])
        res["kapu"][key] = kp
        res["holm_p"][key] = holm({t: blk[t]["delta_B1S"]["B1-R|None"]["aurc"]["p"] for t in blk})
        for v in (*blk.values(), *lang_blk.values()):
            v.pop("_rep_aurc", None)
        res["helyesseg"][key] = blk
        res["nyelv"][key] = lang_blk
    res["minta_sablonok"] = minta_sablonok()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "f5_elemzes.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not a.vak:
        print(json.dumps(res["kapu"], ensure_ascii=False, indent=1))


MP_KAROK = ("B1-S", "B1-N", "B1-LR|None", "B1-R|None")
MP_MEROK = ("sn_lef", "sn_prec", "sel_lef", "sel_prec", "hamis_sel_nm", "hamis_sel_egyeb", "hamis_none", "defer_arany")


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    b = np.minimum((p * bins).astype(int), bins - 1)
    return float(sum(abs(p[b == k].mean() - y[b == k].mean()) * (b == k).sum() for k in range(bins) if (b == k).any()) / len(p))


def prob(t: E.Tab, kar: str) -> np.ndarray:
    """A kar pontszáma valószínűségként: a B1-S és a B1-N a B1 saját valószínűsége, a tanult karoké a logit szigmoidja."""
    q = t.q.copy()
    if kar == "B1-N":
        q = np.where(t.none, q + 10, q)  # a B1-N a NONE-javaslatokat −10-zel tolta hátra (elemzes06.karok)
    return np.clip(q if kar in ("B1-S", "B1-N") else 1 / (1 + np.exp(-q)), 1e-6, 1 - 1e-6)


def munkapont(a) -> None:
    """8.4: a τ a CAL-on (a 05 szabálya: CP-alsó ≥ 0,95, ≥ 200 elfogadott; alapesetenként egy item = minden item), a
    munkapont a TESZT-en; a bootstrapban a CAL és a TESZT sablonklaszterenként újramintázva, a τ replikánként újra
    (a 05 módszere), replikánként egy seed és egy húzás. Mellette a Brier és az ECE a TESZT-en, Platt nélkül és a CAL-on
    illesztett Platt-tal (diagnosztika; seedátlag)."""
    telepit()
    rng = np.random.default_rng(a.seed)
    res = {"reps": a.reps, "seed": a.seed, "cal_szelet": a.cal_szelet, "teszt_szelet": a.teszt_szelet,
           "szabaly": {"cel": K.TARGET, "min_elfogadott": K.MIN_ACC}, "csaladok": {}}
    for fam in CSALADOK:
        f = json.loads((Path(a.be) / fam / "f1.json").read_text())
        cn, tn = f"{fam}:{a.cal_szelet}", f"{fam}:{a.teszt_szelet}"
        Lc, Lt = Slice06(cn), Slice06(tn)
        C, T = A.karok(f, cn, "helyes", Lc.ids), A.karok(f, tn, "helyes", Lt.ids)
        blk = {}
        for kar in MP_KAROK:
            pont, kal = [], []
            for rc, rt in zip(C[kar], T[kar]):
                for tc, tt in zip(rc, rt):
                    tau = E.tau_of(tc, Lc.full())
                    m = E.measure(tt, Lt.state, Lt.full(), tau)
                    pont.append({"tau_inf": math.isinf(tau), **{k: m[k] for k in MP_MEROK}})
                    pc, pt = prob(tc, kar), prob(tt, kar)
                    w = K.platt_fit(np.log(pc / (1 - pc)), tc.cor.astype(float))
                    pp = 1 / (1 + np.exp(-(w[0] * np.log(pt / (1 - pt)) + w[1])))
                    y = tt.cor.astype(float)
                    kal.append({"brier": float(np.mean((pt - y) ** 2)), "ece": ece(pt, y),
                                "brier_platt": float(np.mean((pp - y) ** 2)), "ece_platt": ece(pp, y)})
            # D24: replikánként ugyanazokon a CAL- és TESZT-csoportokon minden futás, a mérők a futások átlaga (a
            # munkapont nélküli futások nélkül); a munkapont nélküli futások aránya külön
            reps = {k: [] for k in MP_MEROK}
            nincs, ossz = 0, 0
            for _ in range(a.reps):
                sc, st_ = Lc.draw(rng), Lt.draw(rng)
                ms = []
                for rc, rt in zip(C[kar], T[kar]):
                    for tc, tt in zip(rc, rt):
                        ossz += 1
                        tau = E.tau_of(tc, sc)
                        if math.isinf(tau):
                            nincs += 1
                            continue
                        ms.append(E.measure(tt, Lt.state, st_, tau))
                for k in MP_MEROK:
                    reps[k].append(float(np.nanmean([m[k] for m in ms])) if ms else math.nan)
            blk[kar] = {"pont": {k: float(np.nanmean([p[k] for p in pont])) for k in MP_MEROK},
                        "nincs_munkapont_pont": float(np.mean([p["tau_inf"] for p in pont])),
                        "nincs_munkapont_replika": nincs / ossz,
                        "ci95": {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))]
                                 if not np.isnan(v).all() else None for k, v in reps.items()},
                        "kalibracio": {k: float(np.mean([x[k] for x in kal])) for k in kal[0]}}
        res["csaladok"][fam] = blk
        print(f"munkapont {fam} kész", flush=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "f5_munkapont.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def bontas(a) -> None:
    """D20: a nyereség bontása NONE- és SELECT-javaslatokra (`bontas06.reteg`) a TESZT-en, családonként; kötelező sor."""
    telepit()
    import bontas06 as BT  # noqa: PLC0415

    rng = np.random.default_rng(a.seed)
    res = {"reps": a.reps, "retegek": {}}
    for fam in CSALADOK:
        f = json.loads((Path(a.be) / fam / "f1.json").read_text())
        res["retegek"][f"{fam}:{a.teszt_szelet}"] = BT.reteg(f, f"{fam}:{a.teszt_szelet}", a.reps, rng, seed_atlag=True)
        print(f"bontás {fam} kész", flush=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "f5_bontas.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not a.vak:
        (out / "f5_bontas.md").write_text(BT.lap(res), encoding="utf-8")


def fusteszt(a) -> None:
    """A teljes út a nyitott T500-on (tanítóminta = teszt), a pecsét nélkül. Csak a szerkezetet ellenőrzi: karonként a
    pontszámok száma, az elemzés kulcsai; mérőszámot nem ír ki (a T500-on a saját mintáján mérne)."""
    out = Path(a.out)
    for fam in CSALADOK:
        if not a.tanitas_nelkul:
            tanit(argparse.Namespace(csalad=fam, tesztek="T500", elotanitott=a.elotanitott, out=str(out)))
        f = json.loads((out / fam / "f1.json").read_text())
        t = f"{fam}:T500"
        n = len(f["B1"][t]["ids"])
        bad = {k: len(v) for k, v in f["pontszam"].items() if k.endswith(t) and not k.startswith(("H|", "H-T-meta|")) and len(v) != n}
        print(f"{fam}: B1 {n} item, {len(f['pontszam'])} pontszámsor, eltérő hosszú B1-sor: {bad or 'nincs'}", flush=True)
    import time  # noqa: PLC0415

    t0 = time.time()
    elemez(argparse.Namespace(be=str(out), out=str(out / "elemzes"), reps=50, seed=1, teszt_szelet="T500", vak=True))
    print(f"elemzés 50 ismétléssel: {time.time() - t0:.0f} s", flush=True)
    r = json.loads((out / "elemzes/f5_elemzes.json").read_text())
    print("elemzés kulcsai:", sorted(r["helyesseg"]["helyes"]), "· nyelvi szeletek:", len(r["nyelv"]["helyes"]),
          "· kapu-kulcsok:", sorted(r["kapu"]["helyes"]), flush=True)
    print("futások (karonként a futásszám):", {t: {k: len(v["aurc"]) for k, v in x.items()}
                                               for t, x in r["futasok"]["helyes"].items()}, flush=True)
    print("a T100 / T200 sablonszáma:", r["minta_sablonok"], flush=True)
    munkapont(argparse.Namespace(be=str(out), out=str(out / "elemzes"), reps=50, seed=1, cal_szelet="T500",
                                 teszt_szelet="T500"))
    r = json.loads((out / "elemzes/f5_munkapont.json").read_text())
    print("munkapont-kulcsok:", {f: sorted(v) for f, v in r["csaladok"].items()}, flush=True)
    bontas(argparse.Namespace(be=str(out), out=str(out / "elemzes"), reps=50, seed=1, teszt_szelet="T500", vak=True))
    r = json.loads((out / "elemzes/f5_bontas.json").read_text())
    print("bontás-kulcsok:", {t: sorted(v) for t, v in r["retegek"].items()}, flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tanit")
    t.add_argument("--csalad", required=True, choices=CSALADOK)
    t.add_argument("--tesztek", default="CAL,TESZT")
    t.add_argument("--elotanitott", default=str(EXP / "cache/k06/b1rel"))
    t.add_argument("--out", required=True)
    e = sub.add_parser("elemez")
    e.add_argument("--be", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--reps", type=int, default=10000)
    e.add_argument("--seed", type=int, default=20261029)
    e.add_argument("--teszt-szelet", default="TESZT")
    e.add_argument("--vak", action="store_true")
    m = sub.add_parser("munkapont")
    m.add_argument("--be", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--reps", type=int, default=10000)
    m.add_argument("--seed", type=int, default=20261029)
    m.add_argument("--cal-szelet", default="CAL")
    m.add_argument("--teszt-szelet", default="TESZT")
    b = sub.add_parser("bontas")
    b.add_argument("--be", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--reps", type=int, default=10000)
    b.add_argument("--seed", type=int, default=20261029)
    b.add_argument("--teszt-szelet", default="TESZT")
    b.add_argument("--vak", action="store_true")
    f = sub.add_parser("fusteszt")
    f.add_argument("--elotanitott", default=str(EXP / "cache/k06/b1rel"))
    f.add_argument("--out", required=True)
    f.add_argument("--tanitas-nelkul", action="store_true", help="a meglévő f1.json-okkal (csak az értékelés)")
    a = ap.parse_args()
    {"tanit": tanit, "elemez": elemez, "munkapont": munkapont, "bontas": bontas, "fusteszt": fusteszt}[a.cmd](a)


if __name__ == "__main__":
    main()
