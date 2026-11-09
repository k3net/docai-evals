"""07-es kör — munkapont a változatlan τ-val (rögzítés utáni, feltáró kiegészítés; Dani, 2026-11-01 este): egy
`b1rel07 pontoz`-alakú kimeneten hány tételt zárna le a kar (a lezárható javaslat, SELECT vagy X, és a pontszám ≥ τ), és
ebből hány hibás. A τ az F5 CAL-on kapott értéke (`kor07/eredmenyek/F5/elemzes.json`, k2 → karok → családok → tau),
karonként és családonként; a seedes karoknál seedenként (17, 42, 73), a számok a seedek átlaga, mellette a tartomány.
Munkapont nélküli karon (τ = ∞) semmi nem záródik le. Viszonyításul az F5 TESZT lezárási hibaaránya.

  python3 kor07/eszkozok/munkapont07.py k3 --be cache/k07/k3 --out kor07/eredmenyek/K3/munkapont
  python3 kor07/eszkozok/munkapont07.py k3 --be cache/k07/aug --elotag aug --out kor07/eredmenyek/K3/aug/munkapont
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
F5 = EXP / "kor07/eredmenyek/F5/elemzes.json"
SEEDS = (17, 42, 73)
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
KAROK = {"keret4": {"B1-4S": ("B1-4S",), "B1-4R": tuple(f"B1-4R|{s}" for s in SEEDS), "B1-4LR": ("B1-4LR",)},
         "keret2": {"B1-S": ("B1-S",), "B1-R": tuple(f"B1-R|{s}" for s in SEEDS), "B1-LR": ("B1-LR",)}}


def f5() -> dict:
    return json.loads(F5.read_text())["k2"]["karok"]


def lezaras(doc: dict, kr: str, arm: str, fam: str, cor: np.ndarray | None = None, csali: np.ndarray | None = None,
            maszk: np.ndarray | None = None) -> dict:
    """A kar lezárásai a változatlan τ-val. `cor`: a helyesség (alapból a pontozó szigorú helyessége); `csali`: a SELECT a
    csalin; `maszk`: a részhalmaz."""
    K = f5()[arm]["csaladok"][fam]
    taus = K["tau"]
    ids, D, P = doc[kr]["ids"], doc[kr]["dontes"], doc[kr]["pontszam"]
    kind = np.array([D[i]["kind"] for i in ids])
    cor = np.array([bool(D[i]["helyes"]) for i in ids]) if cor is None else cor
    m = np.ones(len(ids), bool) if maszk is None else maszk
    lez = ((kind == "SELECT") | (kind == "NONE")) & m
    futas = []
    for run, tau in zip(KAROK[kr][arm], taus):
        q = np.array(P[run], float)
        acc = lez & (q >= tau)
        futas.append({"lezart": int(acc.sum()), "hibas": int((acc & ~cor).sum()), "helyes": int((acc & cor).sum()),
                      "hibas_x": int((acc & ~cor & (kind == "NONE")).sum()),
                      "csali": int((acc & csali).sum()) if csali is not None else None})
    atl = {k: float(np.mean([x[k] for x in futas])) for k in ("lezart", "hibas", "helyes", "hibas_x")}
    if csali is not None:
        atl["csali"] = float(np.mean([x["csali"] for x in futas]))
    return {"n": int(m.sum()), "tau": taus, "f5_teszt_lezarasi_hiba": K.get("lezarasi_hiba"), "atlag": atl, "futasok": futas}


def jsonl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def csali_es_valtozat(fam: str, ids: list[str], D: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import k3_07  # noqa: PLC0415

    cs = k3_07.csalik("diag", fam)
    items = {it["id"]: it for it in jsonl(EXP / "kor07/adat/diag/items" / f"{fam}.jsonl")}
    csali = np.array([D[i]["kind"] == "SELECT" and D[i]["cand"] == cs[i][1] for i in ids], bool)
    return csali, np.array([cs[i][0] for i in ids]), np.array([items[i]["lang"] for i in ids])


def k3(a) -> None:
    res: dict = {"forras": a.be, "csaladok": {}}
    for fam in CSALADOK:
        doc = json.loads((Path(a.be) / f"{a.elotag}_{fam}.json").read_text())
        res["csaladok"][fam] = {}
        for kr in KAROK:
            ids, D = doc[kr]["ids"], doc[kr]["dontes"]
            csali, valt, lang = csali_es_valtozat(fam, ids, D)
            bontas = {"összes": None, **{f"változat {v}": valt == v for v in sorted(set(valt))},
                      **{f"nyelv {lg}": lang == lg for lg in ("hu", "en")}}
            res["csaladok"][fam][kr] = {b: {arm: lezaras(doc, kr, arm, fam, csali=csali, maszk=m) for arm in KAROK[kr]}
                                        for b, m in bontas.items()}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "munkapont.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "munkapont.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


def sz(x: float) -> str:
    return (f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.1f}").replace(".", ",")


def tart(futas: list[dict], k: str) -> str:
    v = [x[k] for x in futas]
    return "" if len(v) == 1 or min(v) == max(v) else f" ({min(v)}–{max(v)})"


def lap(res: dict) -> str:
    L = ["# Munkapont a változatlan τ-val (rögzítés utáni, feltáró kiegészítés)", "",
         f"Forrás: `{res['forras']}`. A τ az F5 CAL-on kapott értéke karonként és családonként; lezárva a SELECT vagy X "
         "javaslat, ha a pontszám ≥ τ. Minden item MATCH, ezért az X-lezárás is hiba. A seedes karoknál (B1-4R, B1-R) a "
         "három seed átlaga, zárójelben a tartomány. Viszonyításul az F5 TESZT lezárási hibaaránya (a természetes "
         "összetételű friss mintán). „Nincs munkapont”: a CAL-on nem volt τ a CP-feltétellel, a kar semmit nem zár le.", ""]
    for fam, R in res["csaladok"].items():
        L += [f"## {fam}", "",
              "| keret | kar | lezárt / n | ebből hibás | hibás arány a lezártakon | ebből csali | ebből X | F5 TESZT lezárási hiba |",
              "|---|---|---|---|---|---|---|---|"]
        for kr, B in R.items():
            for arm, c in B["összes"].items():
                a, fu = c["atlag"], c["futasok"]
                if all(math.isinf(t) for t in c["tau"]):
                    L.append(f"| {kr} | {arm} | nincs munkapont | – | – | – | – | – |")
                    continue
                arany = f"{100 * a['hibas'] / a['lezart']:.0f}%" if a["lezart"] else "–"
                ref = c["f5_teszt_lezarasi_hiba"]
                L.append(f"| {kr} | {arm} | {sz(a['lezart'])}{tart(fu, 'lezart')} / {c['n']} | {sz(a['hibas'])}{tart(fu, 'hibas')} | "
                         f"{arany} | {sz(a['csali'])} | {sz(a['hibas_x'])} | "
                         f"{'–' if ref is None or (isinstance(ref, float) and math.isnan(ref)) else f'{100 * ref:.1f}%'.replace('.', ',')} |")
        L += ["", "Bontás (négyállapotú keret, lezárt / n, ebből hibás):", "",
              "| bontás | " + " | ".join(KAROK["keret4"]) + " |", "|---|" + "---|" * len(KAROK["keret4"])]
        for b, A in R["keret4"].items():
            if b == "összes":
                continue
            cells = []
            for arm in KAROK["keret4"]:
                c = A[arm]
                cells.append("nincs munkapont" if all(math.isinf(t) for t in c["tau"]) else
                             f"{sz(c['atlag']['lezart'])} / {c['n']}, hibás {sz(c['atlag']['hibas'])}")
            L.append(f"| {b} | " + " | ".join(cells) + " |")
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    k = sub.add_parser("k3")
    k.add_argument("--be", required=True)
    k.add_argument("--elotag", default="diag")
    k.add_argument("--out", required=True)
    a = ap.parse_args()
    {"k3": k3}[a.cmd](a)


if __name__ == "__main__":
    main()
