"""08 G1 — az alany döntései a lánc utáni itemeken (B1-4S, a négy sorrend átlagának argmaxa; a 07 `b1rel07.decide4`
útja a 07 B1-4 temperature-jével). Tervezési számok a megismert adaton:

  T500 (06)   a lánc után hány tanítható modelldöntés marad, és köztük hány helyes és hibás (08-runbook 3.1, Dani 3.)
  K3 diag     a helyes arány lánc nélkül (K07K3), orákulumsorral (a páros próba), lánccal valós és orákulum-kinyeréssel

A helyesség az eredeti itemhez: SELECT a goldon (MATCH), X a NO_MATCH-en, Y a MISSING_DATA-n, Z az OUT_OF_SCOPE-on.
A lánc automatikus kötése a saját helyességével számít, az emberhez küldött tétel nem lezárt.
  python3 kor08/eszkozok/g1_dontes08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import b1rel07 as R  # noqa: E402
import lanc08 as L  # noqa: E402

G1 = EXP / "kor08/adat/G1"
HELYES_FAJTA = {"MATCH": "SELECT", "NO_MATCH": "NONE", "MISSING_DATA": "MISSING", "OUT_OF_SCOPE": "OOS"}


def helyes(d: dict, st: str, gold: str | None) -> bool:
    if d["kind"] == "SELECT":
        return st == "MATCH" and d["cand"] == gold
    return HELYES_FAJTA[st] == d["kind"]


def ut_eredmeny(ut: str, src: str, elo: str, fam: str, szelet: str, jell: Path, temp: float) -> dict:
    """Egy út (kinyert / orákulum) egy szeletén: a lánc kimenetei és a modell döntései az eredeti itemhez mérve."""
    lanc = [r for r in L.jsonl(G1 / f"{ut}_{src}" / f"lanc_{fam}.jsonl")]
    eredeti = {it["id"]: it for _, it in L.betolt(src, fam) if it["split"] == szelet}
    lanc = [r for r in lanc if r["id"] in eredeti]
    by = R.rows4(f"{elo}_{fam}_{szelet}", jell)
    c, rossz = Counter(), Counter()
    for r in lanc:
        it = eredeti[r["id"]]
        st, g = it["content_state"], it["gold"]
        c["n"] += 1
        if r["kimenet"] == "kotes":
            c["automatikus kötés"] += 1
            c["helyes" if (st == "MATCH" and r["kotes"] == g) else "hibás"] += 1
            continue
        if r["kimenet"] == "emberhez":
            c["emberhez"] += 1
            continue
        if r["id"] not in by:
            c["nincs kiolvasás"] += 1
            continue
        d = R.decide4(by[r["id"]], temp)
        c["a modellhez"] += 1
        ok = helyes(d, st, g)
        c["modell helyes" if ok else "modell hibás"] += 1
        c["helyes" if ok else "hibás"] += 1
        if not ok:
            rossz[f"{st}→{d['kind']}"] += 1
        if len(r["megmaradt"]) == 0:
            c["üres lista"] += 1
            c["üres lista, modell helyes" if ok else "üres lista, modell hibás"] += 1
    return {"szamok": dict(c), "tevesztes": dict(rossz.most_common())}


def k07(fam: str, kind: str) -> dict:
    """A K3 diag lánc nélkül (K07K3) és az orákulumsoros páros próba (B1-4S döntései a pontozó kimenetéből)."""
    p = EXP / ("cache/k07/k3" if kind == "k3" else "cache/k07/aug") / f"{'diag' if kind == 'k3' else 'aug'}_{fam}.json"
    if not p.exists():
        return {}
    d = json.loads(p.read_text())["keret4"]
    h = sum(bool(d["dontes"][i]["helyes"]) for i in d["ids"])
    return {"n": len(d["ids"]), "helyes": h}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jell", default="cache/k08/jellemzok")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    jell = EXP / a.jell
    temp = json.loads((EXP / "cache/k07/fejek/temperature.json").read_text())["B1-4"]
    res: dict = {"temperature": temp, "T500": {}, "K3diag": {}}
    for fam in L.CSALADOK:
        res["T500"][fam] = {ut: ut_eredmeny(ut, "06", elo, fam, "T500", jell, temp)
                            for ut, elo in (("kinyert", "l06"), ("orakulum", "o06"))}
        res["K3diag"][fam] = {ut: ut_eredmeny(ut, "K3diag", elo, fam, "DIAG", jell, temp)
                              for ut, elo in (("kinyert", "lK3"), ("orakulum", "oK3"))}
        res["K3diag"][fam]["lanc_nelkul_K07K3"] = k07(fam, "k3")
        res["K3diag"][fam]["orakulumsor_paros_proba"] = k07(fam, "aug")
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "dontesek.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "dontesek.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


def pct(a: int, n: int) -> str:
    return f"{a} / {n} ({100 * a / n:.0f}%)" if n else "–"


def lap(res: dict) -> str:
    L_ = ["# G1 — az alany döntései a lánc után (B1-4S; tervezési számok, megismert adat)", "",
          "## T500 (06): tanítható modelldöntések a lánc után", "",
          "| család | út | n | automatikus kötés | emberhez | a modellhez | ebből helyes | ebből hibás | ebből üres lista |",
          "|---|---|---|---|---|---|---|---|---|"]
    for fam, U in res["T500"].items():
        for ut, X in U.items():
            s = X["szamok"]
            L_.append(f"| {fam} | {ut} | {s.get('n', 0)} | {s.get('automatikus kötés', 0)} | {s.get('emberhez', 0)} | "
                      f"{s.get('a modellhez', 0)} | {s.get('modell helyes', 0)} | {s.get('modell hibás', 0)} | {s.get('üres lista', 0)} |")
    L_ += ["", "A hibás modelldöntések állapot → döntés szerint:", ""]
    for fam, U in res["T500"].items():
        for ut, X in U.items():
            L_.append(f"- {fam}, {ut}: " + "; ".join(f"{k} {v}" for k, v in X["tevesztes"].items()))
    L_ += ["", "## K3 diag: a helyes arány négy úton", "",
           "| család | lánc nélkül (K07K3) | orákulumsor, kizárás nélkül (páros próba) | lánc, orákulum-kinyerés | lánc, valós kinyerés |",
           "|---|---|---|---|---|"]
    for fam, U in res["K3diag"].items():
        a_, b_ = U["lanc_nelkul_K07K3"], U["orakulumsor_paros_proba"]
        o, k = U["orakulum"]["szamok"], U["kinyert"]["szamok"]
        L_.append(f"| {fam} | {pct(a_.get('helyes', 0), a_.get('n', 0))} | {pct(b_.get('helyes', 0), b_.get('n', 0))} | "
                  f"{pct(o.get('helyes', 0), o.get('n', 0))} | {pct(k.get('helyes', 0), k.get('n', 0))} |")
    L_ += ["", "A lánc útjain a nevező az összes item; az emberhez küldött tétel nem helyes. A téves döntések:", ""]
    for fam, U in res["K3diag"].items():
        for ut in ("orakulum", "kinyert"):
            s = U[ut]["szamok"]
            L_.append(f"- {fam}, {ut}: emberhez {s.get('emberhez', 0)}; " + "; ".join(f"{k} {v}" for k, v in U[ut]["tevesztes"].items()))
    return "\n".join(L_) + "\n"


if __name__ == "__main__":
    main()
