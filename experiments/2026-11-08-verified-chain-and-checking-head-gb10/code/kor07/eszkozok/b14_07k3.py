"""07-es kör, a nehéz minta 3. köre — a `b14_07 --nehez --nehez-kor 3` kiegészítő bontása (a `b14_07` a v1 manifest
része, ezért burkoló, nem módosítás).

Változatonként a MATCH-en a rossz opcióválasztásból mennyi a csali: bank az `s_csali` (részfizetésnél a tétel összegével
egyező bruttó, betűvel írt összegnél az összeg-iker), szabály az azonos típusú, másik sávú pont (a generátor `iker`-e),
hibaelhárítás az azonos tünetcsoport másik oka. Bontás nyelvenként és a váltás részlete szerint: B3a az arány
(30 / 40 / 50%), B3b az iker fajtája, H3 aszerint, hogy a két váltásból hány a javaslat természetes párja
(`kor07/nehez3-javaslat.md`). Fejlesztési próba, nem állítás; csak aggregátum kerül a kimenetbe.

  python3 kor07/eszkozok/b14_07k3.py --out kor07/eredmenyek/F1   (→ b14_nehez3_bontas.{md,json})
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b14_07 as B  # noqa: E402

K = B.K
SABLON06 = B.EXP / "kor06/adat/f2/sablon"
# a javaslat természetes párjai (rendezetlenül); a sablonok írásmód-változatai kisbetűsítve és egységesítve
TERMESZETES = {frozenset(p) for p in (("v", "mv"), ("bar", "kpa"), ("bar", "mbar"), ("ms", "s"), ("mm", "µm"),
                                     ("a", "ma"), ("hz", "rpm"), ("l/min", "l/h"))}
IRASMOD = {"volt": "v", "millivolt": "mv", "ampere": "a", "amper": "a", "milliampere": "ma", "milliamper": "ma",
           "second": "s", "milliseconds": "ms"}


def egyseg(u: str) -> str:
    u = u.strip().lower()
    return IRASMOD.get(u, u)


def termeszetes(meresek: list[dict]) -> int:
    """A két váltott mérésből hány a javaslat természetes párja szerinti."""
    return sum(frozenset((egyseg(m["eredeti"]), egyseg(m["egyseg"]))) in TERMESZETES for m in meresek)


def terv_meta(fam: str) -> dict[str, dict]:
    """group_id → változat, nyelv, a csali opció-id-je (a `final` sorrendjében `o1…`) és a váltás részlete."""
    pontok = {}
    if fam == "szabaly.koltsegelszamolas":
        pontok = {s["sablon_id"]: s["pontok"] for s in K.jsonl(SABLON06 / f"{fam}.jsonl")}
    out = {}
    for p in K.jsonl(B.nehez_dir() / "terv" / f"{fam}.jsonl"):
        sids, g, v = [o["sid"] for o in p["opciok"]], p["gold_sid"], p["nehez"]["valt"]
        if fam == "penzugy.bankparositas":
            csali = "s_csali"
            reszlet = f"{p['nehez']['arany']}%" if v == "B3a-reszfizetes" else p["nehez"]["iker"]
        elif fam == "szabaly.koltsegelszamolas":
            pts = pontok[p["sablon_id"]]
            tipus = next(x["tipus"] for x in pts if x["id"] == g)
            csali = next(x["id"] for x in pts if x["tipus"] == tipus and x["id"] != g)  # a generátor `iker`-e
            reszlet = None
        else:
            csali = g[:-1] + str(1 - int(g[-1]))  # sid = c<csoport><ok>
            reszlet = f"természetes váltás {termeszetes(p['tenyek']['meresek'])} / 2"
        if csali not in sids or g not in sids:
            raise SystemExit(f"{p['group_id']}: a gold vagy a csali nincs az opciók közt")
        out[p["group_id"]] = {"valt": v, "lang": p["lang"], "gold": f"o{sids.index(g) + 1}",
                              "csali": f"o{sids.index(csali) + 1}", "reszlet": reszlet}
    return out


def dontesek(fam: str, temp4: float, temp6: float) -> dict[str, dict]:
    src = B.nehez_src()
    r4 = B.rows_by_id(B.JELL07, f"{src}_{fam}_NEHEZ")
    r2 = B.rows_by_id(B.JELL07_2, f"{src}_{fam}_NEHEZ")
    if set(r4) != set(r2):
        raise SystemExit(f"{fam}: a két keret itemjei eltérnek ({len(r4)} / {len(r2)})")
    out = {}
    for i in sorted(r4):
        d4 = B.decide4(r4[i], temp4)
        k2, c2, _ = K.decide_label(r2[i], temp6)
        out[i] = {"k4": d4["kind"], "c4": d4["cand"], "k2": k2, "c2": c2}
    return out


def blokk(sel: list[str], D: dict, T: dict) -> dict:
    r: dict = {"n": len(sel)}
    for k in ("4", "2"):
        s = [i for i in sel if D[i]["k" + k] == "SELECT"]
        rossz = [i for i in s if D[i]["c" + k] != T[i]["gold"]]
        r[k] = {"select": len(s), "rossz": len(rossz), "csali": sum(D[i]["c" + k] == T[i]["csali"] for i in rossz),
                "nem_select": len(sel) - len(s)}
    return r


def csalad(fam: str, temp4: float, temp6: float, MN: dict) -> dict:
    T, D = terv_meta(fam), dontesek(fam, temp4, temp6)
    ids = sorted(D)
    for i in ids:  # a terv és a `final` itemje ugyanazt a goldot mondja
        if MN[i]["gold"] != T[i]["gold"]:
            raise SystemExit(f"{i}: a terv goldja ({T[i]['gold']}) eltér az itemétől ({MN[i]['gold']})")
    sorok = [("összes", ids)]
    for v in sorted({T[i]["valt"] for i in ids}):
        vi = [i for i in ids if T[i]["valt"] == v]
        sorok.append((v, vi))
        sorok += [(f"{v} · {lg}", [i for i in vi if T[i]["lang"] == lg]) for lg in ("hu", "en")]
        sorok += [(f"{v} · {r}", [i for i in vi if T[i]["reszlet"] == r])
                  for r in sorted({T[i]["reszlet"] for i in vi if T[i]["reszlet"] is not None})]
    return {"terv": len(T), "item": len(ids), "kiesett": len(set(T) - set(ids)),
            "reszlet": dict(Counter(f"{T[i]['valt']} · {T[i]['reszlet']}" for i in ids if T[i]["reszlet"] is not None)),
            "sorok": [{"bontas": nev, **blokk(sel, D, T)} for nev, sel in sorok if sel]}


def szazalek(a: int, n: int) -> str:
    return f"{a} / {n} ({100 * a / n:.0f}%)".replace(".", ",") if n else "–"


def lap(res: dict) -> str:
    L = ["# 07 F1 — a nehéz minta 3. köre: rossz opció és csali változatonként", "",
         f"Temperature: négyállapotú {B.f(res['temperature4'], 4)} (06 T500), kétkimenetű {B.f(res['temperature6'], 4)} "
         "(05). Minden item MATCH. A rossz opció a SELECT a nem-gold opción, az n arányában (D11 célja: 20%); "
         "zárójelben, hányszor volt ez a csali. A nem-SELECT itt is hiba. Fejlesztési próba, nem állítás.", ""]
    for fam, r in res["csaladok"].items():
        L += [f"## {fam}", "", f"Terv {r['terv']}, item {r['item']} (a tényellenőrzőn kiesett: {r['kiesett']}).", "",
              "| bontás | n | rossz opció, 4 | ebből csali | nem-SELECT, 4 | rossz opció, 2 | ebből csali | nem-SELECT, 2 |",
              "|---|---|---|---|---|---|---|---|"]
        for s in r["sorok"]:
            a, b = s["4"], s["2"]
            L.append(f"| {s['bontas']} | {s['n']} | {szazalek(a['rossz'], s['n'])} | {a['csali']} | {a['nem_select']} | "
                     f"{szazalek(b['rossz'], s['n'])} | {b['csali']} | {b['nem_select']} |")
        L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    B.NEHEZ_KOR["n"] = 3
    temp6 = json.loads(B.KALIB.read_text())["B1"]["temperature"]
    temp4 = B.fit_temp({i: rs for fam in B.CSALADOK for i, rs in B.rows07(fam, "T500").items()}, B.meta())
    MN = B.meta_nehez()
    res = {"temperature4": temp4, "temperature6": temp6,
           "csaladok": {fam: csalad(fam, temp4, temp6, MN) for fam in B.CSALADOK}}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "b14_nehez3_bontas.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / "b14_nehez3_bontas.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


if __name__ == "__main__":
    main()
