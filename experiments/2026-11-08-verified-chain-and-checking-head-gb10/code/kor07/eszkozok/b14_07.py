"""07-es kör, F1 — a B1-4 döntései a négyállapotú prompton (07-runbook 3.1, 4., D2).

A `kiolvas07` soraiból (kanonikus perm 0 + b1 perm 1–3) itemenként a négy sorrend átlagolt, temperature-rel skálázott
eloszlása; a döntés az argmax: SELECT (egy opció), NONE (X), MISSING (Y) vagy OOS (Z). A temperature a 06 T500-án
illesztve (D2), a három család együtt, a perm 0 sorokon, a gold válasz NLL-jével (a 05 `fit_temperature` módszere).
Helyesség: a szigorú a négyosztályos (SELECT csak a gold opción, NONE csak NO_MATCH-en, MISSING csak MISSING_DATA-n,
OOS csak OUT_OF_SCOPE-on); az enyhe a nem-SELECT válaszokat minden nem-MATCH itemen elfogadja.

Mellette ugyanazokon az itemeken a 06 B1 (kétkimenetű prompt, a 05 temperature-jével; `kalib05.decide_label`), hogy
a prompt hatása a döntésekre látsszon: tévesztési mátrixok, kereszttábla, a MATCH-en rossz opció száma, és az AURC a
saját pontszámmal (minden javaslat; szigorú helyesség). Ez tervezési próba a 06 megismert szeletein, nem állítás.

  python3 kor07/eszkozok/b14_07.py --out kor07/eredmenyek/F1
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import kalib05 as K  # noqa: E402
import keret07 as K7  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
SZELETEK = ("T500", "CAL", "TESZT")
ITEMS06 = EXP / "kor06/adat/f2/items"
JELL07 = EXP / "cache/k07/jellemzok"
JELL06 = EXP / "cache/k06/jellemzok"
PECSET06 = EXP / "cache/k06/pecset/jellemzok"
KALIB = EXP / "kor05/eredmenyek/F3/kalib/kalib.json"
ALLAPOTOK = ("MATCH", "NO_MATCH", "MISSING_DATA", "OUT_OF_SCOPE")
FAJTAK = ("SELECT", "NONE", "MISSING", "OOS")
HELYES_FAJTA = {"NONE": "NO_MATCH", "MISSING": "MISSING_DATA", "OOS": "OUT_OF_SCOPE"}


def meta() -> dict:
    out = {}
    for fam in CSALADOK:
        for it in K.jsonl(ITEMS06 / f"{fam}.jsonl"):
            out[it["id"]] = {"family": fam, "split": it["split"], "state": it["content_state"], "gold": it["gold"],
                             "gold_set": {it["gold"]} if it["gold"] is not None else set(), "lang": it["lang"],
                             "sablon": it["template_group_id"], "ketertelmu": bool(it.get("ketertelmu"))}
    return out


def rows_by_id(root: Path, prefix: str) -> dict[str, list[dict]]:
    by = defaultdict(list)
    for mod in ("kanonikus", "b1"):
        d = root / f"{prefix}__{mod}"
        if not d.exists():
            raise SystemExit(f"hiányzik: {d.relative_to(EXP)}")
        for f in sorted(d.glob("sorok_*.jsonl")):
            for r in K.jsonl(f):
                by[r["id"]].append(r)
    for i, rs in by.items():
        if sorted(r["perm"] for r in rs) != [0, 1, 2, 3]:
            raise SystemExit(f"{prefix}: {i} permutációi hiányosak")
    return by


def rows07(fam: str, sz: str) -> dict[str, list[dict]]:
    return rows_by_id(JELL07, f"k06_{fam}_{sz}")


def rows06(fam: str, sz: str) -> dict[str, list[dict]]:
    return rows_by_id(JELL06 if sz == "T500" else PECSET06, f"{fam}_{sz}")


def gold_kulcs(m: dict) -> str | None:
    """A gold válasz kulcsa az `option_scores` szótárában: MATCH → az opció, NO_MATCH → None (X), MISSING_DATA → ::Y,
    OUT_OF_SCOPE → ::Z (a `keret07.gold_key` a metából)."""
    return m["gold"] if m["state"] == "MATCH" else K7.STATE_KEY[m["state"]]


def fit_temp(by: dict[str, list[dict]], M: dict) -> float:
    rows0 = [r for rs in by.values() for r in rs if r["perm"] == 0 and not M[r["id"]]["ketertelmu"]]

    def nll(logt: float) -> float:
        t, tot = math.exp(logt), 0.0
        for r in rows0:
            tot -= math.log(max(1e-12, K.option_scores(r, t)[gold_kulcs(M[r["id"]])]))
        return tot
    return float(math.exp(minimize_scalar(nll, bounds=(-3, 4), method="bounded").x))  # type: ignore[attr-defined]


def decide4(rs: list[dict], temp: float) -> dict:
    sc = [K.option_scores(r, temp) for r in rs]
    avg = {k: sum(s[k] for s in sc) / len(sc) for k in sc[0]}
    pred = max(avg, key=avg.get)
    srt = sorted(avg.values(), reverse=True)
    return {"kind": K7.kind_of(pred), "cand": pred, "q": avg[pred], "gap": srt[0] - srt[1],
            "x": avg.get(None, 0.0), "y": avg.get(K7.Y_ID, 0.0), "z": avg.get(K7.Z_ID, 0.0),
            "agree": sum(max(s, key=s.get) == pred for s in sc) / len(sc)}


def helyes4(m: dict, d: dict) -> tuple[bool, bool]:
    if d["kind"] == "SELECT":
        ok = d["cand"] in m["gold_set"]
        return ok, ok
    return m["state"] == HELYES_FAJTA[d["kind"]], m["state"] != "MATCH"


def aurc(q: np.ndarray, cor: np.ndarray) -> float:
    o = np.argsort(-q, kind="stable")
    err = np.cumsum(~cor[o])
    return float((err / np.arange(1, len(q) + 1)).mean())


def szelet(fam: str, sz: str, temp4: float, temp6: float, M: dict) -> dict:
    r7, r6 = rows07(fam, sz), rows06(fam, sz)
    ids = sorted(i for i in r7 if not M[i]["ketertelmu"])
    if set(ids) != {i for i in r6 if not M[i]["ketertelmu"]}:
        raise SystemExit(f"{fam}:{sz}: a 06 és a 07 itemjei eltérnek")
    d4 = {i: decide4(r7[i], temp4) for i in ids}
    d6 = {}
    for i in ids:
        kind, cand, q = K.decide_label(r6[i], temp6)
        ok, ok_l = K.correctness(M[i], kind, cand)
        d6[i] = {"kind": kind, "cand": cand, "q": q, "helyes": ok, "helyes_enyhe": ok_l}
    for i in ids:
        d4[i]["helyes"], d4[i]["helyes_enyhe"] = helyes4(M[i], d4[i])
    conf4 = {s: Counter(d4[i]["kind"] for i in ids if M[i]["state"] == s) for s in ALLAPOTOK}
    conf6 = {s: Counter(d6[i]["kind"] for i in ids if M[i]["state"] == s) for s in ALLAPOTOK}
    kereszt = Counter((d6[i]["kind"], d4[i]["kind"]) for i in ids)
    q4, c4 = np.array([d4[i]["q"] for i in ids]), np.array([d4[i]["helyes"] for i in ids], bool)
    q6, c6 = np.array([d6[i]["q"] for i in ids]), np.array([bool(d6[i]["helyes"]) for i in ids])
    rossz = lambda d: sum(1 for i in ids if M[i]["state"] == "MATCH" and d[i]["kind"] == "SELECT" and not d[i]["helyes"])  # noqa: E731
    nyelv = {}
    for lg in ("hu", "en"):
        sel = [i for i in ids if M[i]["lang"] == lg]
        nyelv[lg] = {"n": len(sel), "helyes4": float(np.mean([d4[i]["helyes"] for i in sel])),
                     "helyes6": float(np.mean([bool(d6[i]["helyes"]) for i in sel])),
                     "aurc4": aurc(np.array([d4[i]["q"] for i in sel]), np.array([d4[i]["helyes"] for i in sel], bool)),
                     "aurc6": aurc(np.array([d6[i]["q"] for i in sel]), np.array([bool(d6[i]["helyes"]) for i in sel]))}
    return {"n": len(ids), "temperature4": temp4, "temperature6": temp6,
            "helyes4": float(c4.mean()), "helyes4_enyhe": float(np.mean([d4[i]["helyes_enyhe"] for i in ids])),
            "helyes6": float(c6.mean()), "helyes6_enyhe": float(np.mean([bool(d6[i]["helyes_enyhe"]) for i in ids])),
            "aurc4": aurc(q4, c4), "aurc6": aurc(q6, c6),
            "aurc4_enyhe": aurc(q4, np.array([d4[i]["helyes_enyhe"] for i in ids], bool)),
            "fajta4": dict(Counter(d4[i]["kind"] for i in ids)), "fajta6": dict(Counter(d6[i]["kind"] for i in ids)),
            "tevesztes4": {s: {f: conf4[s][f] for f in FAJTAK} for s in ALLAPOTOK},
            "tevesztes6": {s: {f: conf6[s][f] for f in ("SELECT", "NONE")} for s in ALLAPOTOK},
            "kereszt_06_07": {f"{a}→{b}": kereszt[(a, b)] for a in ("SELECT", "NONE") for b in FAJTAK if kereszt[(a, b)]},
            "match_rossz_opcio4": rossz(d4), "match_rossz_opcio6": rossz(d6),
            "egyetertes4_atlag": float(np.mean([d4[i]["agree"] for i in ids])), "nyelv": nyelv,
            "dontesek": {i: {k: v for k, v in d4[i].items()} for i in ids}}


def f(x: float, d: int = 3) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def lap(res: dict) -> str:
    L = ["# 07 F1 — a B1-4 döntései a négyállapotú prompton (tervezési próba a 06 szeletein)", "",
         f"Temperature a 06 T500-án (3 család, perm 0): **{f(res['temperature4'], 4)}**; családonként "
         + ", ".join(f"{k.split('.')[1]} {f(v, 4)}" for k, v in res["temperature4_csaladonkent"].items())
         + f". A 06 B1 temperature-je {f(res['temperature6'], 4)} (05 D_cal_prob).", "",
         "| család | szelet | n | B1-4 helyes (szigorú / enyhe) | B1 (06) helyes (szigorú / enyhe) | AURC B1-4S | AURC B1-S (06) | "
         "AURC B1-4S enyhe | MATCH-en rossz opció 4 / 6 | 4-perm egyetértés |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for fam, szs in res["csaladok"].items():
        for sz, r in szs.items():
            L.append(f"| {fam} | {sz} | {r['n']} | {f(r['helyes4'])} / {f(r['helyes4_enyhe'])} | {f(r['helyes6'])} / "
                     f"{f(r['helyes6_enyhe'])} | {f(r['aurc4'], 4)} | {f(r['aurc6'], 4)} | {f(r['aurc4_enyhe'], 4)} | "
                     f"{r['match_rossz_opcio4']} / {r['match_rossz_opcio6']} | {f(r['egyetertes4_atlag'])} |")
    L += ["", "## Tévesztési mátrixok (sor: gold-állapot; oszlop: a B1-4 válasza)", ""]
    for fam, szs in res["csaladok"].items():
        for sz, r in szs.items():
            L += [f"**{fam} : {sz}**", "", "| gold | SELECT | NONE (X) | MISSING (Y) | OOS (Z) | · | 06: SELECT | 06: NONE |",
                  "|---|---|---|---|---|---|---|---|"]
            for s in ALLAPOTOK:
                t, u = r["tevesztes4"][s], r["tevesztes6"][s]
                L.append(f"| {s} | {t['SELECT']} | {t['NONE']} | {t['MISSING']} | {t['OOS']} | · | {u['SELECT']} | {u['NONE']} |")
            L += ["", "06 → 07 kereszttábla: " + ", ".join(f"{k} {v}" for k, v in r["kereszt_06_07"].items()), ""]
    L += ["## Nyelvenként (szigorú helyesség, AURC)", "", "| család | szelet | nyelv | n | B1-4 helyes | B1 (06) helyes | AURC B1-4S | AURC B1-S |",
          "|---|---|---|---|---|---|---|---|"]
    for fam, szs in res["csaladok"].items():
        for sz, r in szs.items():
            for lg, v in r["nyelv"].items():
                L.append(f"| {fam} | {sz} | {lg} | {v['n']} | {f(v['helyes4'])} | {f(v['helyes6'])} | {f(v['aurc4'], 4)} | {f(v['aurc6'], 4)} |")
    return "\n".join(L) + "\n"


# --- a nehéz próbaminta (3.3, D11): a két keret B1-je ugyanazokon a MATCH-itemeken ------------------------------------

JELL07_2 = EXP / "cache/k07/jellemzok2"
NEHEZ_KOR = {"n": 1}


def nehez_dir() -> Path:
    return EXP / f"kor07/adat/nehez{'' if NEHEZ_KOR['n'] == 1 else NEHEZ_KOR['n']}"


def nehez_src() -> str:
    return "nehez" if NEHEZ_KOR["n"] == 1 else f"nehez{NEHEZ_KOR['n']}"


def meta_nehez() -> dict:
    out = {}
    for fam in CSALADOK:
        valt = {r["group_id"]: r["nehez"]["valt"] for r in K.jsonl(nehez_dir() / "terv" / f"{fam}.jsonl")}
        for it in K.jsonl(nehez_dir() / "items" / f"{fam}.jsonl"):
            out[it["id"]] = {"family": fam, "split": it["split"], "state": it["content_state"], "gold": it["gold"],
                             "gold_set": {it["gold"]}, "lang": it["lang"], "sablon": it["template_group_id"],
                             "ketertelmu": bool(it.get("ketertelmu")), "valt": valt[it["id"]]}
    return out


def auroc(score: np.ndarray, y: np.ndarray) -> float | None:
    """A helyes (y) és a hibás válaszok szétválasztása a pontszámmal (rangalapú); None, ha csak egyféle van."""
    if y.all() or not y.any():
        return None
    from scipy.stats import rankdata  # noqa: PLC0415

    r = rankdata(score)
    n1 = int(y.sum())
    return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * (len(y) - n1)))


def nehez_csalad(fam: str, temp4: float, temp6: float, M: dict) -> dict:
    r4, r2 = rows_by_id(JELL07, f"{nehez_src()}_{fam}_NEHEZ"), rows_by_id(JELL07_2, f"{nehez_src()}_{fam}_NEHEZ")
    ids = sorted(set(r4) & set(r2))
    if len(ids) != len(r4) or len(ids) != len(r2):
        raise SystemExit(f"{fam}: a két keret itemjei eltérnek ({len(r4)} / {len(r2)})")
    d4 = {i: decide4(r4[i], temp4) for i in ids}
    d2 = {}
    for i in ids:
        kind, cand, q = K.decide_label(r2[i], temp6)
        d2[i] = {"kind": kind, "cand": cand, "q": q, "helyes": bool(K.correctness(M[i], kind, cand)[0])}
    for i in ids:
        d4[i]["helyes"] = helyes4(M[i], d4[i])[0]

    def blokk(sel: list[str]) -> dict:
        s4 = [i for i in sel if d4[i]["kind"] == "SELECT"]
        s2 = [i for i in sel if d2[i]["kind"] == "SELECT"]
        return {"n": len(sel),
                "fajta4": dict(Counter(d4[i]["kind"] for i in sel)), "fajta2": dict(Counter(d2[i]["kind"] for i in sel)),
                "rossz_opcio4": sum(not d4[i]["helyes"] for i in s4), "rossz_opcio2": sum(not d2[i]["helyes"] for i in s2),
                "helyes4": float(np.mean([d4[i]["helyes"] for i in sel])), "helyes2": float(np.mean([d2[i]["helyes"] for i in sel])),
                "select_auroc4": auroc(np.array([d4[i]["q"] for i in s4]), np.array([d4[i]["helyes"] for i in s4], bool)) if s4 else None,
                "select_auroc2": auroc(np.array([d2[i]["q"] for i in s2]), np.array([d2[i]["helyes"] for i in s2], bool)) if s2 else None,
                "aurc4": aurc(np.array([d4[i]["q"] for i in sel]), np.array([d4[i]["helyes"] for i in sel], bool)),
                "aurc2": aurc(np.array([d2[i]["q"] for i in sel]), np.array([d2[i]["helyes"] for i in sel], bool))}
    return {"osszes": blokk(ids),
            "nyelv": {lg: blokk([i for i in ids if M[i]["lang"] == lg]) for lg in ("hu", "en")},
            "valtozat": {v: blokk([i for i in ids if M[i]["valt"] == v]) for v in sorted({M[i]["valt"] for i in ids})},
            "dontesek": {i: {"k4": d4[i]["kind"], "h4": d4[i]["helyes"], "q4": d4[i]["q"], "k2": d2[i]["kind"],
                             "h2": d2[i]["helyes"], "q2": d2[i]["q"]} for i in ids}}


def g(x: float | None, d: int = 3) -> str:
    return "–" if x is None else f(x, d)


def lap_nehez(res: dict) -> str:
    L = ["# 07 F1 — a nehéz próbaminta: a két keret B1-je (MATCH-itemek, a 06 T500-sablonjain)", "",
         f"Temperature: négyállapotú {f(res['temperature4'], 4)} (06 T500), kétkimenetű {f(res['temperature6'], 4)} (05).",
         "Rossz opció: SELECT a nem-gold opción. SELECT-AUROC: a saját pontszám szétválasztja-e a helyes és a rossz "
         "SELECT-et. A nem-SELECT itt mind hiba (minden item MATCH).", "",
         "| család | bontás | n | 4: SELECT / X / Y / Z | 2: SELECT / X | rossz opció 4 / 2 | helyes 4 / 2 | SELECT-AUROC 4 / 2 | AURC 4 / 2 |",
         "|---|---|---|---|---|---|---|---|---|"]
    for fam, r in res["csaladok"].items():
        rows = [("összes", r["osszes"])] + [(f"nyelv {k}", v) for k, v in r["nyelv"].items()] + \
               [(f"változat {k}", v) for k, v in r["valtozat"].items()]
        for nev, b in rows:
            f4, f2 = b["fajta4"], b["fajta2"]
            L.append(f"| {fam} | {nev} | {b['n']} | {f4.get('SELECT', 0)} / {f4.get('NONE', 0)} / {f4.get('MISSING', 0)} / "
                     f"{f4.get('OOS', 0)} | {f2.get('SELECT', 0)} / {f2.get('NONE', 0)} | {b['rossz_opcio4']} / {b['rossz_opcio2']} | "
                     f"{f(b['helyes4'])} / {f(b['helyes2'])} | {g(b['select_auroc4'])} / {g(b['select_auroc2'])} | "
                     f"{f(b['aurc4'], 4)} / {f(b['aurc2'], 4)} |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--szeletek", default=",".join(SZELETEK))
    ap.add_argument("--nehez", action="store_true", help="a nehéz próbaminta (a K07F1B után); a temperature a 06 T500-ról")
    ap.add_argument("--nehez-kor", type=int, default=1, help="a nehéz konstrukció köre (1 vagy 2)")
    a = ap.parse_args()
    NEHEZ_KOR["n"] = a.nehez_kor
    M = meta()
    temp6 = json.loads(KALIB.read_text())["B1"]["temperature"]
    t500 = {fam: rows07(fam, "T500") for fam in CSALADOK}
    temp4 = fit_temp({i: rs for by in t500.values() for i, rs in by.items()}, M)
    print(f"temperature (T500, 3 család): {temp4:.4f}", flush=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if a.nehez:
        MN = meta_nehez()
        res = {"temperature4": temp4, "temperature6": temp6,
               "csaladok": {fam: nehez_csalad(fam, temp4, temp6, MN) for fam in CSALADOK}}
        nev = f"b14_{nehez_src()}"
        (out / f"{nev}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (out / f"{nev}.md").write_text(lap_nehez(res), encoding="utf-8")
        print((out / f"{nev}.md").read_text())
        return
    res = {"temperature4": temp4, "temperature4_csaladonkent": {fam: fit_temp(by, M) for fam, by in t500.items()},
           "temperature6": temp6, "csaladok": {}}
    for fam in CSALADOK:
        res["csaladok"][fam] = {}
        for sz in a.szeletek.split(","):
            res["csaladok"][fam][sz] = szelet(fam, sz, temp4, temp6, M)
            print(f"{fam}:{sz} kész", flush=True)
    (out / "b14.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "b14.md").write_text(lap(res), encoding="utf-8")
    print((out / "b14.md").read_text())


if __name__ == "__main__":
    main()
