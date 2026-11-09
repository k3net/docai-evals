"""07-es kör — páros diagnosztikai próba a K3 végső mintáján (feltáró; a K3 rögzítése és a pecsét nyitása után, Dani
2026-11-01 esti kérésére): ugyanaz az item és ugyanazok a jelöltek, egyszer az eredeti szöveggel (K07K3), egyszer a
szöveg végén egy géppel, a terv tényeiből kiszámított sorral. A sor a hiányzó következtetési lépés eredménye:

  részfizetés        a számla teljes bruttója = a tétel összege / az arány
  mértékegység-váltás mindkét mérés a szabály egységére átváltva
  nettó / bruttó     a nettó összeg = bruttó / (1 + áfakulcs)
  deviza             az átszámított összeg = devizaösszeg × árfolyam

A sort nem nyelvi modell írja (a Qwen-család csak alany), hanem ez a kód; a kiszámított érték a szöveg tényeiből jön,
ezért kerekítésben eltérhet a gold opció számától (például 4 125,30 / 0,5 = 8 250,60 a 8 250,61 helyett).

  python3 kor07/eszkozok/aug07.py epit                    → kor07/adat/diagaug/items/<család>.jsonl (azonos id-k)
  python3 kor07/eszkozok/aug07.py elemez --orig cache/k07/k3 --aug cache/k07/aug --out kor07/eredmenyek/K3/aug
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path.insert(0, str(HERE))
import szint07k3 as K3  # noqa: E402

S = K3.S
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
DIAG = EXP / "kor07/adat/diag"
AUG = EXP / "kor07/adat/diagaug"


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def eredeti_ertek(m: dict, lang: str) -> str:
    """A váltott mérés a szabály egységében (a `szint07k3.VALTAS` inverze, három értékes jegyre)."""
    for u2, (_f, fi) in K3.VALTAS[m["eredeti"].strip()]:
        if u2 == m["egyseg"]:
            return S.fmt_num(K3.kerekit(fi(S._num(m["ertek"]))), lang)
    raise SystemExit(f"nincs váltás: {m['eredeti']} → {m['egyseg']}")


def szamitott_sor(p: dict) -> str:
    v, t, lang = p["nehez"]["valt"], p["tenyek"], p["lang"]
    hu = lang == "hu"
    if v == "B3a-reszfizetes":
        teljes = round(t["osszeg"] * 100 / t["reszlet"])
        m = S.money(teljes, lang)
        return (f"Ellenőrzött számítás: a tétel a számla bruttó összegének {t['reszlet']}%-a, a számla teljes bruttó összege "
                f"tehát {m}." if hu else
                f"Verified calculation: the amount is {t['reszlet']}% of the invoice gross amount, so the full invoice gross "
                f"amount is {m}.")
    if v == "H3-valtas":
        r = "; ".join(f"{m['nev']}: {m['ertek']} {m['egyseg']} = {eredeti_ertek(m, lang)} {m['eredeti'].strip()}"
                      for m in t["meresek"])
        return (f"Ellenőrzött átváltás a szabályok egységére: {r}." if hu else f"Verified conversion to the units of the rules: {r}.")
    if v == "S3a-netto":
        netto = round(t["osszeg"] / (1 + t["afa"] / 100))
        return (f"Ellenőrzött számítás: a nettó összeg {S.money(netto, lang)} ({S.money(t['osszeg'], lang)} bruttó, "
                f"{t['afa']}% áfa)." if hu else
                f"Verified calculation: the net amount is EUR {netto:,} (EUR {t['osszeg']:,} gross, {t['afa']}% VAT).")
    if v == "S3b-deviza":
        if hu:
            return (f"Ellenőrzött átszámítás: {t['osszeg']} EUR × {t['arfolyam']} Ft/EUR = "
                    f"{S.money(round(t['osszeg'] * t['arfolyam']), lang)}.")
        return (f"Verified conversion: GBP {t['osszeg']:,} × {t['arfolyam']:.2f} EUR/GBP = "
                f"EUR {t['osszeg'] * t['arfolyam']:,.2f}.")
    raise SystemExit(f"ismeretlen változat: {v}")


def epit(_a) -> None:
    for fam in CSALADOK:
        terv = {p["group_id"]: p for p in jsonl(DIAG / "terv" / f"{fam}.jsonl")}
        out = []
        for it in jsonl(DIAG / "items" / f"{fam}.jsonl"):
            out.append({**it, "state": it["state"].rstrip() + "\n\n" + szamitott_sor(terv[it["id"]]),
                        "meta": {**it.get("meta", {}), "aug": True}})
        (AUG / "items").mkdir(parents=True, exist_ok=True)
        (AUG / "items" / f"{fam}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out),
                                                     encoding="utf-8")
        print(f"{fam}: {len(out)} item, változat {dict(Counter(terv[x['id']]['nehez']['valt'] for x in out))}")


# --- elemzés (feltáró) --------------------------------------------------------------------------------------------

def dontesek(doc: dict, kr: str, ids: list[str], gold: dict[str, str]) -> tuple[np.ndarray, np.ndarray]:
    D = doc[kr]["dontes"]
    sel = np.array([D[i]["kind"] == "SELECT" for i in ids], bool)
    cor = np.array([D[i]["kind"] == "SELECT" and D[i]["cand"] == gold[i] for i in ids], bool)
    return sel, cor


def mcnemar(b: int, c: int) -> float:
    """Kétoldali egzakt McNemar-p a diszkordáns párokon (binomiális, p = 0,5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return float(min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n))


def elemez(a) -> None:
    import k3_07  # noqa: PLC0415
    import munkapont07 as MP  # noqa: PLC0415

    rng = np.random.default_rng(20261102)
    res: dict = {"orig": a.orig, "aug": a.aug, "reps": a.reps, "csaladok": {}}
    for fam in CSALADOK:
        O = json.loads((Path(a.orig) / f"diag_{fam}.json").read_text())
        A = json.loads((Path(a.aug) / f"aug_{fam}.json").read_text())
        items = {it["id"]: it for it in jsonl(DIAG / "items" / f"{fam}.jsonl")}
        cs = k3_07.csalik("diag", fam)
        R: dict = {}
        for kr in ("keret4", "keret2"):
            ids = O[kr]["ids"]
            if ids != A[kr]["ids"]:
                raise SystemExit(f"{fam}/{kr}: az eredeti és a kiegészített itemek eltérnek")
            gold = {i: items[i]["gold"] for i in ids}
            so, co = dontesek(O, kr, ids, gold)
            sa, ca = dontesek(A, kr, ids, gold)
            valt = np.array([cs[i][0] for i in ids])
            lang = np.array([items[i]["lang"] for i in ids])
            grp = np.array([items[i]["template_group_id"] for i in ids])
            tpl = sorted(set(grp))
            tag = [np.where(grp == t)[0] for t in tpl]
            boot = np.empty(a.reps)
            for r in range(a.reps):
                idx = np.concatenate([tag[t] for t in rng.integers(0, len(tpl), len(tpl))])
                boot[r] = ca[idx].mean() - co[idx].mean()
            bontas = {"összes": np.ones(len(ids), bool), **{f"változat {v}": valt == v for v in sorted(set(valt))},
                      **{f"nyelv {lg}": lang == lg for lg in ("hu", "en")}}
            sor = {}
            for bn, m in bontas.items():
                b_, c_ = int((~co & ca & m).sum()), int((co & ~ca & m).sum())
                sor[bn] = {"n": int(m.sum()), "helyes_eredeti": int((co & m).sum()), "helyes_kiegeszitett": int((ca & m).sum()),
                           "rossz_opcio_eredeti": int((so & ~co & m).sum()), "rossz_opcio_kiegeszitett": int((sa & ~ca & m).sum()),
                           "nem_select_eredeti": int((~so & m).sum()), "nem_select_kiegeszitett": int((~sa & m).sum()),
                           "javult": b_, "romlott": c_, "mcnemar_p": mcnemar(b_, c_)}
            karok = {}
            for arm, runs in k3_07.KAROK[kr].items():
                au = []
                for D_, s_, c_ in ((O, so, co), (A, sa, ca)):
                    vals = [k3_07.auroc(np.array(D_[kr]["pontszam"][run], float)[s_], c_[s_]) for run in runs]
                    au.append(k3_07.atlag(vals))
                karok[arm] = {"auroc_eredeti": au[0], "auroc_kiegeszitett": au[1]}
            mp = {}
            for arm in MP.KAROK[kr]:
                cso = np.array([O[kr]["dontes"][i]["kind"] == "SELECT" and O[kr]["dontes"][i]["cand"] == cs[i][1] for i in ids])
                csa = np.array([A[kr]["dontes"][i]["kind"] == "SELECT" and A[kr]["dontes"][i]["cand"] == cs[i][1] for i in ids])
                mp[arm] = {"eredeti": MP.lezaras(O, kr, arm, fam, cor=co, csali=cso)["atlag"],
                           "kiegeszitett": MP.lezaras(A, kr, arm, fam, cor=ca, csali=csa)["atlag"],
                           "nincs_munkapont": all(math.isinf(t) for t in MP.f5()[arm]["csaladok"][fam]["tau"])}
            R[kr] = {"sorok": sor, "delta_helyes": {"pont": float(ca.mean() - co.mean()), "ci95": k3_07.E.ci(boot)},
                     "karok": karok, "munkapont": mp, "sablon": len(tpl)}
        res["csaladok"][fam] = R
        print(f"{fam} kész", flush=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "aug.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "aug.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


def pct(a: int, n: int) -> str:
    return f"{a} ({100 * a / n:.0f}%)" if n else "–"


def g(x: float, d: int = 3) -> str:
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def lap(res: dict) -> str:
    L = ["# Páros diagnosztikai próba: eredeti szöveg vs. a géppel kiszámított sorral kiegészítve (feltáró)", "",
         "A K3 végső mintája (K07K3), ugyanazok az itemek és jelöltek; a kiegészített változatban a szöveg végén egy sor a "
         "hiányzó lépés eredményével (`kor07/eszkozok/aug07.py`). Feltáró elemzés a már megismert K3-mintán, nem "
         "megerősítő. Helyes = SELECT a gold opción; a nem-SELECT is hiba (minden item MATCH). A különbség "
         f"intervalluma sabloncsoportos klaszteres bootstrap ({res['reps']} ismétlés). McNemar: egzakt, kétoldali.", ""]
    for kr, cim in (("keret4", "Négyállapotú keret"), ("keret2", "06-os keret (leíró)")):
        L += [f"## {cim}", "", "| család | bontás | n | helyes: eredeti → kiegészített | rossz opció | nem-SELECT | javult / romlott | McNemar p |",
              "|---|---|---|---|---|---|---|---|"]
        for fam, R in res["csaladok"].items():
            for bn, x in R[kr]["sorok"].items():
                L.append(f"| {fam} | {bn} | {x['n']} | {pct(x['helyes_eredeti'], x['n'])} → {pct(x['helyes_kiegeszitett'], x['n'])} | "
                         f"{x['rossz_opcio_eredeti']} → {x['rossz_opcio_kiegeszitett']} | {x['nem_select_eredeti']} → "
                         f"{x['nem_select_kiegeszitett']} | {x['javult']} / {x['romlott']} | {g(x['mcnemar_p'], 4)} |")
        L += ["", "| család | Δ helyes arány [95%] | " + " | ".join(f"{a} AUROC: eredeti → kieg." for a in res["csaladok"][CSALADOK[0]][kr]["karok"]) + " |",
              "|---|---|" + "---|" * len(res["csaladok"][CSALADOK[0]][kr]["karok"])]
        for fam, R in res["csaladok"].items():
            d = R[kr]["delta_helyes"]
            L.append(f"| {fam} | {g(d['pont'])} [{g(d['ci95'][0])}; {g(d['ci95'][1])}] | "
                     + " | ".join(f"{g(v['auroc_eredeti'])} → {g(v['auroc_kiegeszitett'])}" for v in R[kr]["karok"].values()) + " |")
        L += ["", "Munkapont a változatlan τ-val (lezárt, ebből hibás; seedes karon a seedek átlaga):", "",
              "| család | kar | eredeti | kiegészített |", "|---|---|---|---|"]
        for fam, R in res["csaladok"].items():
            for arm, m in R[kr]["munkapont"].items():
                if m["nincs_munkapont"]:
                    L.append(f"| {fam} | {arm} | nincs munkapont | nincs munkapont |")
                    continue
                e, k = m["eredeti"], m["kiegeszitett"]
                L.append(f"| {fam} | {arm} | {g(e['lezart'], 1)}, hibás {g(e['hibas'], 1)} | {g(k['lezart'], 1)}, hibás {g(k['hibas'], 1)} |")
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("epit")
    e = sub.add_parser("elemez")
    e.add_argument("--orig", required=True)
    e.add_argument("--aug", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--reps", type=int, default=2000)
    a = ap.parse_args()
    {"epit": epit, "elemez": elemez}[a.cmd](a)


if __name__ == "__main__":
    main()
