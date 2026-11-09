"""06-os kör — a B1 saját szintje a friss családok nyitott T500-án (06-runbook 13. pont: ha egy család B1-AURC-je
< 0,01, a v1 előtt cseréljük; 8.5: a relatív MDE a B1-S AURC-jétől függ).

Csak a T500 (pecsét nélkül). A B1 javaslata a négy sorrend átlagolt eloszlásának argmaxa, a 05 D_cal_prob-temperature-rel
(`kalib05.option_scores`, mint a `b1rel06.b1_info`-ban); szigorú helyesség (7.). Mérők: pontosság, AURC (S+N, a B1 nem
DEFER-el), AURC* (orákulum) és E-AURC, a javaslatfajták aránya és pontossága állapotonként, nyelvenként.

  python3 kor06/eszkozok/b1t500_06.py --out kor06/eredmenyek/F3/b1_t500
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor05/eszkozok"), str(EXP / "eszkozok")]
import kalib05 as K  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
JELL = EXP / "cache/k06/jellemzok"
KALIB = EXP / "kor05/eredmenyek/F3/kalib/kalib.json"
KUSZOB = 0.01


def aurc(q: np.ndarray, cor: np.ndarray) -> float:
    c = cor[np.argsort(-q, kind="stable")]
    return float((np.cumsum(~c) / np.arange(1, len(c) + 1)).mean()) if len(c) else 0.0


def aurc_star(k: int, n: int) -> float:
    i = np.arange(k + 1, n + 1)
    return float(((i - k) / i).sum() / n) if n else 0.0


def merok(rs: list[dict]) -> dict:
    q = np.array([r["q"] for r in rs])
    cor = np.array([r["helyes"] for r in rs])
    a, a0 = aurc(q, cor), aurc_star(int(cor.sum()), len(cor))
    return {"n": len(rs), "pontossag": round(float(cor.mean()), 4), "aurc": round(a, 4), "aurc_opt": round(a0, 4),
            "e_aurc": round(a - a0, 4), "select": sum(r["kind"] == "SELECT" for r in rs)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    temp = json.loads(KALIB.read_text())["B1"]["temperature"]
    res = {"temperature": temp, "kuszob": KUSZOB, "csaladok": {}}
    for f in CSALADOK:
        by = collections.defaultdict(list)
        for mod in ("kanonikus", "b1"):
            for p in sorted((JELL / f"{f}_T500__{mod}").glob("sorok_*.jsonl")):
                for line in p.read_text(encoding="utf-8").splitlines():
                    r = json.loads(line)
                    by[r["id"]].append(r)
        rs = []
        for iid, rows in by.items():
            if sorted(r["perm"] for r in rows) != [0, 1, 2, 3]:
                raise SystemExit(f"{iid}: a négy sorrend hiányos")
            if rows[0]["ketertelmu"]:
                continue
            kind, cand, qv = K.decide_label(rows, temp)
            st = rows[0]["content_state"]
            ok = cand in set(rows[0]["gold_set"]) if kind == "SELECT" else st == "NO_MATCH"
            rs.append({"q": qv, "helyes": bool(ok), "kind": kind, "state": st, "lang": iid.split(":")[2]})
        blk = {"osszes": merok(rs),
               "nyelv": {l: merok([r for r in rs if r["lang"] == l]) for l in ("hu", "en")},
               "allapot": {s: {**merok([r for r in rs if r["state"] == s]),
                               "none_javaslat": sum(r["kind"] == "NONE" for r in rs if r["state"] == s)}
                           for s in ("MATCH", "NO_MATCH", "MISSING_DATA", "OUT_OF_SCOPE")}}
        blk["cserelendo"] = blk["osszes"]["aurc"] < KUSZOB
        res["csaladok"][f] = blk
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "b1_t500.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = ["# A B1 a friss családok T500-án (06, F3; 13. pont)", "",
          f"Nyitott szelet; temperature {temp:.4f} (a 05 D_cal_prob-illesztése); szigorú helyesség. Küszöb: AURC < {KUSZOB} → "
          "a család cserélendő a v1 előtt.", "",
          "| család | n | pontosság | AURC | AURC* | E-AURC | SELECT | hu AURC | en AURC | cserélendő |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for f, b in res["csaladok"].items():
        o = b["osszes"]
        md.append(f"| {f} | {o['n']} | {o['pontossag']:.3f} | {o['aurc']:.4f} | {o['aurc_opt']:.4f} | {o['e_aurc']:.4f} | "
                  f"{o['select']} | {b['nyelv']['hu']['aurc']:.4f} | {b['nyelv']['en']['aurc']:.4f} | "
                  f"{'igen' if b['cserelendo'] else 'nem'} |")
    md += ["", "| család · állapot | n | pontosság | NONE-javaslat |", "|---|---|---|---|"]
    for f, b in res["csaladok"].items():
        md += [f"| {f} · {s} | {v['n']} | {v['pontossag']:.3f} | {v['none_javaslat']} |" for s, v in b["allapot"].items()]
    (out / "b1_t500.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md), flush=True)


if __name__ == "__main__":
    main()
