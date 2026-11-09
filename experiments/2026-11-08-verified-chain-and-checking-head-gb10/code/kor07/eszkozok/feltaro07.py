"""07 F5 utáni FELTÁRÓ elemzés — miért nem jelez a B1-4 a bankon (nem megerősítő: a 07 CAL és TESZT az F5-ben elköltve,
az itt talált szabály csak egy következő kör friss adatán igazolható).

A kérdések és az eljárás a futás előtt rögzítve (2026-11-01):
 1. A bank MISSING_DATA itemein (azonos összegű ikerpár, a partner hiányzik) hová kerül a B1-4 tömege: a két iker közt
    megoszlik-e, és mennyi jut Y-ra. Összevetés: a MATCH itemek, ahol a gold opciónak azonos összegű ikre van.
 2. Szétválasztja-e a MISSING-et a MATCH-tól a SELECT döntéseken az ikerarány, a p(Y) és a gap (AUROC; CAL, TESZT külön).
    Ikerarány (megfigyelhető, gold nélkül): r = max p(o) / p(top-1) azokon az o ≠ top-1 opciókon, amelyek összege a
    top-1 összegével egyezik (az opciószöveg 3. mezője); 0, ha a top-1-nek nincs ikre.
 3. Ikerszabály: ha a döntés SELECT és r ≥ r*, a válasz Y. Az r* a CAL-on a legkisebb érték, amelynél a MATCH itemek
    legfeljebb 5%-a fordul Y-ra; a TESZT-en: a MISSING itemek hány %-a kap Y-t, a MATCH-ek hány %-a fordul át, és hogyan
    változik a szigorú (négyosztályos) helyesség.
 4. Hatókörön kívüli kérés: az X-döntéseken (NONE) a s = p(Z) / (p(X) + p(Z)) arány, OOS vs NO_MATCH (AUROC); szabály:
    s ≥ s* → Z, az s* a CAL-on úgy, hogy a NO_MATCH itemek legfeljebb 5%-a forduljon Z-re.
 Kontroll: a hibaelhárítás és a szabálycsalád p(Y) / p(Z) AUROC-ja ugyanígy (ott a B1-4 jelez); ikerarány csak a
 bankon van (a többi családnak nincs összegmezője).
A fej (B1-4R) itt nem szerepel: a szabály a B1-4 döntését változtatná, a fej e döntésre tanult.

Kimenet: kor07/eredmenyek/F5/feltaro/bank_jelzes.{json,md}; csak aggregátum, item-azonosító nem.
  py kor07/eszkozok/feltaro07.py
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1rel07 as R  # noqa: E402
import elemzes07 as E  # noqa: E402

EXP = R.EXP
OUT = EXP / "kor07/eredmenyek/F5/feltaro"
ITEMS = EXP / "kor07/adat/f2/items"
SZELETEK = ("CAL", "TESZT")
MAX_ATFORDITAS = 0.05
REPS, SEED = 2000, 20261101


def auroc(pos: np.ndarray, neg: np.ndarray) -> float | None:
    if len(pos) == 0 or len(neg) == 0:
        return None
    allv = np.concatenate([pos, neg])
    order = allv.argsort(kind="mergesort")
    ranks = np.empty(len(allv))
    ranks[order] = np.arange(1, len(allv) + 1)
    for v in np.unique(allv):  # holtverseny: átlagrang
        m = allv == v
        ranks[m] = ranks[m].mean()
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def osszeg(text: str) -> str | None:
    p = text.split(" · ")
    return p[2] if len(p) == 4 else None


def betolt(fam: str, sz: str, temp: float) -> list[dict]:
    _, _, prefix, root4, _ = R.szelet_forras(f"{fam}:{sz}")
    by = R.rows4(prefix, root4)
    items = {it["id"]: it for it in map(json.loads, (ITEMS / f"{fam}.jsonl").read_text().splitlines()) if it}
    out = []
    for i, rs in by.items():
        sc = [R.K.option_scores(r, temp) for r in rs]
        avg = {k: sum(s[k] for s in sc) / len(sc) for k in sc[0]}
        d = R.decide4(rs, temp)
        it = items[i]
        am = {o["id"]: osszeg(o["text"]) for o in it["options"]}
        top = d["cand"]
        r = 0.0
        if d["kind"] == "SELECT" and am.get(top):
            ikrek = [o for o in am if o != top and am[o] == am[top]]
            r = max((avg.get(o, 0.0) / avg[top] for o in ikrek), default=0.0)
        out.append({"id": i, "state": it["content_state"], "kind": d["kind"], "helyes": bool(d["helyes"]), "y": d["y"],
                    "x": d["x"], "z": d["z"], "gap": d["gap"], "r": r, "lang": it["lang"],
                    "gold_iker": bool(it["gold"] and am.get(it["gold"]) and
                                      sum(1 for o in am if am[o] == am[it["gold"]]) >= 2)})
    return out


def kuszob(ertek: np.ndarray, neg_mask: np.ndarray) -> float:
    """A legkisebb küszöb, amelynél a negatívok legfeljebb MAX_ATFORDITAS-a esik fölé (a pozitívak ≥ küszöb)."""
    cand = np.unique(ertek[ertek > 0])
    n_neg = max(1, int(neg_mask.sum()))
    for c in cand:  # növekvő
        if ((ertek >= c) & neg_mask).sum() / n_neg <= MAX_ATFORDITAS:
            return float(c)
    return float("inf")


def csalad(fam: str, temp: float) -> dict:
    res = {}
    data = {sz: betolt(fam, sz, temp) for sz in SZELETEK}
    for sz, rows in data.items():
        st = np.array([r["state"] for r in rows])
        kind = np.array([r["kind"] for r in rows])
        y, x, z, gap, rr = (np.array([r[k] for r in rows]) for k in ("y", "x", "z", "gap", "r"))
        sel = kind == "SELECT"
        e = {"n": len(rows), "allapot": dict(Counter(st.tolist())),
             "dontes_allapotonkent": {s: dict(Counter(kind[st == s].tolist())) for s in sorted(set(st.tolist()))}}
        for s in ("MATCH", "MISSING_DATA"):
            m = st == s
            e[f"{s}_py_median"] = float(np.median(y[m])) if m.any() else None
            e[f"{s}_py_p90"] = float(np.quantile(y[m], 0.9)) if m.any() else None
        e["AUROC_MISSING_vs_MATCH_SELECT"] = {
            "p(Y)": auroc(y[sel & (st == "MISSING_DATA")], y[sel & (st == "MATCH")]),
            "-gap": auroc(-gap[sel & (st == "MISSING_DATA")], -gap[sel & (st == "MATCH")])}
        nonem = kind == "NONE"
        s_arany = z / np.maximum(x + z, 1e-12)
        e["AUROC_OOS_vs_NO_MATCH_NONE"] = {"p(Z)/(p(X)+p(Z))": auroc(s_arany[nonem & (st == "OUT_OF_SCOPE")],
                                                                    s_arany[nonem & (st == "NO_MATCH")])}
        e["OOS_s_median"] = float(np.median(s_arany[st == "OUT_OF_SCOPE"])) if (st == "OUT_OF_SCOPE").any() else None
        if fam == "penzugy.bankparositas":
            mi, ma = st == "MISSING_DATA", st == "MATCH"
            gi = np.array([r["gold_iker"] for r in rows])
            e["iker"] = {
                "MISSING_top1_ikres": float(((rr > 0) & mi).sum() / max(1, mi.sum())),
                "MISSING_r_median": float(np.median(rr[mi])) if mi.any() else None,
                "MATCH_goldikres_n": int((ma & gi).sum()),
                "MATCH_goldikres_r_median": float(np.median(rr[ma & gi])) if (ma & gi).any() else None,
                "AUROC_r_MISSING_vs_MATCH_SELECT": auroc(rr[sel & mi], rr[sel & ma]),
                "AUROC_r_MISSING_vs_MATCHgoldikres_SELECT": auroc(rr[sel & mi], rr[sel & ma & gi]),
            }
        res[sz] = e
    # szabályok: küszöb a CAL-on, mérés a TESZT-en
    cal, tes = data["CAL"], data["TESZT"]

    def arr(rows, k):
        return np.array([r[k] for r in rows])

    szab = {}
    if fam == "penzugy.bankparositas":
        rc = np.where(arr(cal, "kind") == "SELECT", arr(cal, "r"), 0.0)
        r_star = kuszob(rc, arr(cal, "state") == "MATCH")
        szab["iker"] = {"r_csillag": r_star, **hatas(tes, lambda r: r["kind"] == "SELECT" and r["r"] >= r_star, "Y",
                                                       "MISSING_DATA", "MATCH")}
        # változat: az ikerszabály p(Y)-küszöbbel is (Y, ha p(Y) ≥ y*), ugyanígy választva
        yc = np.where(arr(cal, "kind") == "SELECT", arr(cal, "y"), 0.0)
        y_star = kuszob(yc, arr(cal, "state") == "MATCH")
        szab["py"] = {"y_csillag": y_star, **hatas(tes, lambda r: r["kind"] == "SELECT" and r["y"] >= y_star, "Y",
                                                     "MISSING_DATA", "MATCH")}
    xc, zc, kc = arr(cal, "x"), arr(cal, "z"), arr(cal, "kind")
    sc = np.where(kc == "NONE", zc / np.maximum(xc + zc, 1e-12), 0.0)
    s_star = kuszob(sc, arr(cal, "state") == "NO_MATCH")
    szab["oos"] = {"s_csillag": s_star, **hatas(tes, lambda r: r["kind"] == "NONE" and r["z"] / max(r["x"] + r["z"], 1e-12) >= s_star,
                                                 "Z", "OUT_OF_SCOPE", "NO_MATCH")}
    res["szabaly_CAL_to_TESZT"] = szab
    if fam == "penzugy.bankparositas":
        res["k2_ikerszabaly"] = k2_iker(fam, szab["iker"]["r_csillag"], {r["id"]: r["r"] for r in cal},
                                        {r["id"]: r["r"] for r in tes})
    return res


def k2_iker(fam: str, r_star: float, rc: dict, rt: dict) -> dict:
    """Az ikerszabály hatása a K2-re az F5 elemzőjének függvényeivel (τ a CAL-on, mérés a TESZT-en, sabloncsoportos
    bootstrap, futásátlag): a szabály által Y-ra fordított item nem lezárható, helyes, ha MISSING_DATA. Az r* rögzített
    (a teljes CAL-on választva), replikánként nem választódik újra. Önellenőrzés: az „eredeti” az F5 számait adja."""
    import math  # noqa: PLC0415

    be = EXP / "cache/k07/f5"
    C, T = E.Szelet(be, "k07", fam, "CAL"), E.Szelet(be, "k07", fam, "TESZT")
    kmin = E.kmin_tabla(2000)  # mint az elemzes07 main-je (a bootstrap-húzás nagyobb lehet a szeletnél)
    kr = "keret4"

    def valtozat(S, rmap, szabaly):
        kind, cor = S.kind[kr].copy(), S.cor[kr].copy()
        if szabaly:
            fire = np.array([kind[n] == "SELECT" and rmap[i] >= r_star for n, i in enumerate(S.ids)])
            kind[fire] = "MISSING"
            cor[fire] = S.state[fire] == 2
        return kind, cor

    rng = np.random.default_rng(SEED)
    huzasok = [(C.huzas(rng), T.huzas(rng)) for _ in range(REPS)]
    merok = ("hasznos_lef", "lezarasi_hiba", "lezart", "helyes_adatbekeres", "nem_lezart_tau_alatt")
    out, rep = {}, {}
    for kar in ("B1-4S", "B1-4R"):
        for nev, szab in (("eredeti", False), ("ikerszabaly", True)):
            kc, cc = valtozat(C, rc, szab)
            kt, ct = valtozat(T, rt, szab)
            lezc = np.isin(kc, ("SELECT", "NONE"))

            def egy(ic, it):
                ms, nincs = [], 0
                for qc, qt in zip(C.pont[kar], T.pont[kar]):
                    tau = E.tau_of(qc, cc, lezc, ic, kmin)
                    nincs += math.isinf(tau)
                    ms.append(E.k2_merok(qt, ct, kt, T.state, it, tau))
                return E.futas_atlag(ms), nincs, len(C.pont[kar])

            pont, _, _ = egy(C.teljes(), T.teljes())
            arr = {m: np.empty(REPS) for m in merok}
            nincs = ossz = 0
            for n, (ic, it) in enumerate(huzasok):
                m, ni, o = egy(ic, it)
                nincs, ossz = nincs + ni, ossz + o
                for mm in merok:
                    arr[mm][n] = m[mm]
            rep[(kar, nev)] = arr
            out[f"{kar}|{nev}"] = {"pont": {m: pont[m] for m in merok},
                                   "ci95": {m: E.ci(arr[m]) for m in merok},
                                   "nincs_munkapont_replika": nincs / max(1, ossz)}
        d = rep[(kar, "ikerszabaly")]["hasznos_lef"] - rep[(kar, "eredeti")]["hasznos_lef"]
        out[f"{kar}|delta_hasznos_lef"] = {"pont": out[f"{kar}|ikerszabaly"]["pont"]["hasznos_lef"]
                                           - out[f"{kar}|eredeti"]["pont"]["hasznos_lef"], "ci95": E.ci(d)}
    out["r_csillag"], out["reps"], out["seed"] = r_star, REPS, SEED
    return out


GOLD_KIND = {"MATCH": "SELECT", "NO_MATCH": "NONE", "MISSING_DATA": "MISSING", "OUT_OF_SCOPE": "OOS"}
UJ_KIND = {"Y": "MISSING", "Z": "OOS"}


def hatas(rows: list[dict], fires, uj: str, cel: str, vedett: str) -> dict:
    """A szabály hatása: a cél-állapot hány %-a kapja az új választ, a védett állapot hány %-a fordul át, és a szigorú
    helyesség (a négyosztályos kulcs) előtte / utána. A SELECT→Y / NONE→Z fordítás akkor helyes, ha a gold állapot a cél."""
    n_cel = sum(r["state"] == cel for r in rows)
    n_ved = sum(r["state"] == vedett for r in rows)
    talal = sum(1 for r in rows if r["state"] == cel and fires(r))
    fordit = sum(1 for r in rows if r["state"] == vedett and fires(r))
    elotte = sum(r["helyes"] for r in rows)
    utana = sum((GOLD_KIND[r["state"]] == UJ_KIND[uj]) if fires(r) else r["helyes"] for r in rows)
    egyeb = Counter(r["state"] for r in rows if fires(r) and r["state"] not in (cel, vedett))
    jelzett_elotte = sum(1 for r in rows if r["state"] == cel and r["kind"] == UJ_KIND[uj])
    return {"cel_n": n_cel, "cel_jelzett_elotte": jelzett_elotte, "cel_talalat": talal,
            "vedett_n": n_ved, "vedett_atfordul": fordit, "mas_allapot_atfordul": dict(egyeb),
            "szigoru_helyes_elotte": elotte, "szigoru_helyes_utana": utana, "n": len(rows)}


def lap(e: dict) -> str:
    f = lambda v: "–" if v is None else (f"{v:.3f}" if isinstance(v, float) else str(v))  # noqa: E731
    s = ["# 07 F5 utáni feltáró elemzés: az állapotjelzés a bankon (gépi lap, `feltaro07.py`)\n",
         "**Feltáró, nem megerősítő:** a CAL és a TESZT az F5-ben elköltve; az itt választott küszöb csak friss adaton "
         "igazolható. Temperature: a B1-4-é (D2).\n",
         "## Döntések állapotonként (TESZT)\n", "| család | állapot | SELECT | NONE | MISSING | OOS |", "|---|---|---|---|---|---|"]
    for fam, r in e.items():
        for st, c in r["TESZT"]["dontes_allapotonkent"].items():
            s.append(f"| {fam} | {st} | " + " | ".join(str(c.get(k, 0)) for k in ("SELECT", "NONE", "MISSING", "OOS")) + " |")
    s += ["", "## Szétválasztás (AUROC; CAL / TESZT)\n",
          "| család | MISSING vs MATCH, SELECT-en: p(Y) | −gap | ikerarány r | OOS vs NO_MATCH, X-en: p(Z)/(p(X)+p(Z)) |",
          "|---|---|---|---|---|"]
    for fam, r in e.items():
        c, t = r["CAL"], r["TESZT"]
        ik = lambda q: q.get("iker", {}).get("AUROC_r_MISSING_vs_MATCH_SELECT")  # noqa: E731
        s.append(f"| {fam} | {f(c['AUROC_MISSING_vs_MATCH_SELECT']['p(Y)'])} / {f(t['AUROC_MISSING_vs_MATCH_SELECT']['p(Y)'])} | "
                 f"{f(c['AUROC_MISSING_vs_MATCH_SELECT']['-gap'])} / {f(t['AUROC_MISSING_vs_MATCH_SELECT']['-gap'])} | "
                 f"{f(ik(c))} / {f(ik(t))} | "
                 f"{f(c['AUROC_OOS_vs_NO_MATCH_NONE']['p(Z)/(p(X)+p(Z))'])} / {f(t['AUROC_OOS_vs_NO_MATCH_NONE']['p(Z)/(p(X)+p(Z))'])} |")
    b = e.get("penzugy.bankparositas")
    if b:
        s += ["", "## A bank ikerpárja (TESZT)\n"]
        for k, v in b["TESZT"]["iker"].items():
            s.append(f"- {k}: {f(v)}")
        s += [f"- MISSING p(Y) medián / p90: {f(b['TESZT']['MISSING_DATA_py_median'])} / {f(b['TESZT']['MISSING_DATA_py_p90'])}; "
              f"MATCH: {f(b['TESZT']['MATCH_py_median'])} / {f(b['TESZT']['MATCH_py_p90'])}"]
    s += ["", "## Szabályok: küszöb a CAL-on (a védett állapot ≤ 5%-a fordulhat), hatás a TESZT-en\n",
          "| család | szabály | küszöb | cél: jelzett előtte → utána / n | védett átfordul / n | más állapot átfordul | szigorú helyes előtte → utána / n |",
          "|---|---|---|---|---|---|---|"]
    for fam, r in e.items():
        for nev, h in r["szabaly_CAL_to_TESZT"].items():
            kus = next(v for k, v in h.items() if k.endswith("_csillag"))
            s.append(f"| {fam} | {nev} | {f(kus)} | {h['cel_jelzett_elotte']} → {h['cel_jelzett_elotte'] + h['cel_talalat']} / {h['cel_n']} | "
                     f"{h['vedett_atfordul']} / {h['vedett_n']} | {h['mas_allapot_atfordul'] or '–'} | "
                     f"{h['szigoru_helyes_elotte']} → {h['szigoru_helyes_utana']} / {h['n']} |")
    k = e.get("penzugy.bankparositas", {}).get("k2_ikerszabaly")
    if k:
        s += ["", f"## Az ikerszabály hatása a banki K2-re (r* = {k['r_csillag']:.3f}, {k['reps']} replika, TESZT)\n",
              "| kar | változat | hasznos lefedettség [95%] | lezárási hiba [95%] | lezárt | helyes adatbekérés | τ alatt | munkapont nélküli replika |",
              "|---|---|---|---|---|---|---|---|"]
        for kar in ("B1-4S", "B1-4R"):
            for nev in ("eredeti", "ikerszabaly"):
                x = k[f"{kar}|{nev}"]
                p, c = x["pont"], x["ci95"]
                s.append(f"| {kar} | {nev} | {100*p['hasznos_lef']:.1f} [{100*c['hasznos_lef'][0]:.1f}; {100*c['hasznos_lef'][1]:.1f}] | "
                         f"{100*p['lezarasi_hiba']:.1f} [{100*c['lezarasi_hiba'][0]:.1f}; {100*c['lezarasi_hiba'][1]:.1f}] | "
                         f"{100*p['lezart']:.1f} | {100*p['helyes_adatbekeres']:.0f}% | {100*p['nem_lezart_tau_alatt']:.1f} | "
                         f"{100*x['nincs_munkapont_replika']:.0f}% |")
            dd = k[f"{kar}|delta_hasznos_lef"]
            s.append(f"| {kar} | Δ hasznos lef. | {100*dd['pont']:+.1f} [{100*dd['ci95'][0]:+.1f}; {100*dd['ci95'][1]:+.1f}] | | | | | |")
    return "\n".join(s) + "\n"


def main() -> None:
    temps = json.loads((EXP / "cache/k07/fejek/temperature.json").read_text())
    e = {fam: csalad(fam, temps["B1-4"]) for fam in R.CSALADOK}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "bank_jelzes.json").write_text(json.dumps(e, ensure_ascii=False, indent=1) + "\n")
    (OUT / "bank_jelzes.md").write_text(lap(e))
    for p in (OUT, OUT / "bank_jelzes.json", OUT / "bank_jelzes.md"):
        os.chmod(p, 0o777 if p.is_dir() else 0o666)
    print(lap(e))


if __name__ == "__main__":
    main()
