"""06-os kör — a Gemma 4 második ítélete a friss családokon (06-runbook 3.5, D14–D15; a 05 4.3 protokollja).

A kiolvasás a 03 `kiolvaso03` ids-módja, változtatás nélkül: generikus keret, gold és item-id nélküli prompt, a négy
opciósorrend (a pozíciós torzítás ellen). Ez a script csak összesít:
  - itemenként a négy sorrend eloszlásának átlaga, opció-id-kre visszafordítva, a 03 val-on illesztett temperature-rel
    (`kor03/eredmenyek/F2/f2_elemzes.json` tanarkapu.gemma.temp); a Gemma választása az argmax;
  - egyetértés a konstrukció címkéjével (a Gemma keretében csak „egyik sem” van, ezért a NO_MATCH, a MISSING_DATA és az
    OUT_OF_SCOPE egyaránt X);
  - az auditkörök kulcsaira a Gemma ítélete a felület kódjaival (a kanonikus sorrend betűje vagy X), az adjudikációhoz.
A Gemma ítélete triage: nem szűrő és nem címke (D15). Itemet nem töröl, nem javít; az eltérés csak felülvizsgálati jel.

  python3 kor06/eszkozok/gemma06.py osszesit --olvasas kor06/eredmenyek/F2/gemma/gemma_f2.jsonl
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path.insert(0, str(EXP / "eszkozok"))
from common import labels_for, permutation  # noqa: E402

CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")
ITEMS = EXP / "kor06/adat/f2/items"
AUDIT = {1: EXP / "kor06/adat/f2/audit", 2: EXP / "kor06/adat/f2/audit/kor2"}
OUT = EXP / "kor06/eredmenyek/F2/gemma"
JELOLT = EXP / "kor06/adat/f2/gemma"
TEMP_FORRAS = EXP / "kor03/eredmenyek/F2/f2_elemzes.json"
PERMS = (0, 1, 2, 3)


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def tempered(probs: dict[str, float], t: float) -> dict[str, float]:
    lg = {k: math.log(max(v, 1e-300)) / t for k, v in probs.items()}
    m = max(lg.values())
    z = sum(math.exp(v - m) for v in lg.values())
    return {k: math.exp(v - m) / z for k, v in lg.items()}


def itelet(rows: list[dict], t: float) -> dict:
    """A négy sorrend átlaga opció-id-kre (None = egyik sem), a választás és a sorrendek egyetértése."""
    avg: dict[str | None, float] = collections.defaultdict(float)
    picks = []
    for r in rows:
        p = tempered(r["probs"], t)
        by = {oid: p[lab] for oid, lab in zip(r["order"], r["labels"])}
        picks.append(max(by, key=by.get))
        for oid, v in by.items():
            avg[oid] += v / len(rows)
    pick = max(avg, key=avg.get)
    return {"pick": pick, "p_pick": avg[pick], "avg": dict(avg), "egyetert": sum(x == pick for x in picks) / len(picks)}


def kod(it: dict, oid: str | None) -> str:
    if oid is None:
        return "X"
    order = permutation(it, 0)
    return next(lab for o, lab in zip(order, labels_for(order)) if o == oid)


def arany(xs: list[bool]) -> dict:
    return {"n": len(xs), "egyezik": sum(xs), "arany": round(sum(xs) / len(xs), 4) if xs else None}


def cmd_osszesit(a) -> None:
    t = float(json.loads(TEMP_FORRAS.read_text())["tanarkapu"]["gemma"]["temp"])
    items = {it["id"]: it for f in CSALADOK for it in jl(ITEMS / f"{f}.jsonl")}
    by: dict[str, list[dict]] = collections.defaultdict(list)
    for p in a.olvasas:
        for r in jl(Path(p)):
            by[r["id"]].append(r)
    hianyos = [i for i in items if sorted(r["perm"] for r in by.get(i, [])) != list(PERMS)]
    if len(hianyos) > a.max_hianyos:
        raise SystemExit(f"{len(hianyos)} itemnél hiányos a négy sorrend (megengedett: {a.max_hianyos})")
    eredm = {}
    for iid, it in items.items():
        if iid in hianyos:
            continue
        g = itelet(sorted(by[iid], key=lambda r: r["perm"]), t)
        eredm[iid] = {**g, "gold": it["gold"], "p_gold": g["avg"].get(it["gold"], 0.0), "egyezik": g["pick"] == it["gold"]}

    reszek: dict[str, dict[str, list[bool]]] = collections.defaultdict(lambda: collections.defaultdict(list))
    sablon: dict[str, list[bool]] = collections.defaultdict(list)
    for iid, e in eredm.items():
        it = items[iid]
        for nev, ertek in (("csalad", it["family"]), ("csalad×allapot", f"{it['family']}·{it['content_state']}"),
                           ("csalad×nyelv", f"{it['family']}·{it['lang']}"), ("csalad×szelet", f"{it['family']}·{it['split']}"),
                           ("csalad×allapot×nyelv", f"{it['family']}·{it['content_state']}·{it['lang']}")):
            reszek[nev][ertek].append(e["egyezik"])
        sablon[it["template_group_id"]].append(e["egyezik"])
    # a sabloncsoportok, ahol az eltérés aránya kiugró (legalább 10 item): rendszerszintű címkehiba gyanúja
    gyanus = sorted(((k, arany(v)) for k, v in sablon.items() if len(v) >= 10),
                    key=lambda kv: kv[1]["arany"])[: a.sablon_top]

    audit = {}
    for kor, d in AUDIT.items():
        kp = d / "atnezo_kulcsok.json"
        if not kp.exists():
            continue
        km = json.loads(kp.read_text())
        sor = {}
        for k, iid in km["kulcsok"].items():
            e = eredm.get(iid)
            if e is None:
                sor[k] = None
                continue
            sor[k] = {"gemma": kod(items[iid], e["pick"]), "p": round(e["p_pick"], 4),
                      "egyetert_sorrend": e["egyetert"], "egyezik": e["egyezik"]}
        (d / "gemma_itelet.json").write_text(json.dumps({"sig": km["sig"], "temp": t, "kulcsok": sor}, ensure_ascii=False,
                                                        indent=1) + "\n", encoding="utf-8")
        elt = sum(1 for v in sor.values() if v and not v["egyezik"])
        audit[f"kor{kor}"] = {"kulcs": len(sor), "gemma_elter": elt, "hianyzik": sum(v is None for v in sor.values())}

    JELOLT.mkdir(parents=True, exist_ok=True)
    with open(JELOLT / "eltero.jsonl", "w", encoding="utf-8") as fh:
        for iid, e in sorted(eredm.items(), key=lambda kv: kv[1]["p_gold"]):
            if not e["egyezik"]:
                fh.write(json.dumps({"id": iid, "pick": e["pick"], "p_pick": round(e["p_pick"], 4),
                                     "p_gold": round(e["p_gold"], 4), "egyetert_sorrend": e["egyetert"]},
                                    ensure_ascii=False) + "\n")
    rep = {"temp": t, "temp_forras": str(TEMP_FORRAS.relative_to(EXP)), "itemek": len(items), "kiertekelt": len(eredm),
           "hianyos": len(hianyos), "osszes": arany([e["egyezik"] for e in eredm.values()]),
           "reszek": {n: {k: arany(v) for k, v in sorted(d.items())} for n, d in reszek.items()},
           "sablon_legkisebb_egyezes": dict(gyanus), "audit": audit,
           "sorrend_egyetertes_atlag": round(sum(e["egyetert"] for e in eredm.values()) / max(1, len(eredm)), 4)}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "osszesito.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    md = ["# A Gemma második ítélete a friss családokon (06, F2)", "",
          f"Triage, nem szűrő és nem címke (D15). Temperature {t:.3f} (a 03 val-illesztése), négy opciósorrend átlaga.",
          f"Kiértékelt item: {len(eredm)} / {len(items)}; az egyezés a konstrukció címkéjével összesen "
          f"{rep['osszes']['arany']:.1%}; a négy sorrend egyetértése átlagosan {rep['sorrend_egyetertes_atlag']:.1%}.", "",
          "| család · állapot | n | egyezik | arány |", "|---|---|---|---|"]
    md += [f"| {k} | {v['n']} | {v['egyezik']} | {v['arany']:.1%} |" for k, v in rep["reszek"]["csalad×allapot"].items()]
    md += ["", "| család · nyelv | n | arány |", "|---|---|---|"]
    md += [f"| {k} | {v['n']} | {v['arany']:.1%} |" for k, v in rep["reszek"]["csalad×nyelv"].items()]
    md += ["", f"Sabloncsoportok a legkisebb egyezéssel (≥ 10 item, az első {a.sablon_top}):", "",
           "| sabloncsoport | n | arány |", "|---|---|---|"]
    md += [f"| {k} | {v['n']} | {v['arany']:.1%} |" for k, v in gyanus]
    md += ["", "Auditkörök (a kulcsonkénti ítélet a kör `gemma_itelet.json`-jában; a vak első ítélet után nyitandó):", ""]
    md += [f"- {k}: {v['kulcs']} kulcs, a Gemma {v['gemma_elter']} esetben tér el a konstrukciótól" for k, v in audit.items()]
    (OUT / "osszesito.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:5]))


def main() -> None:
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    o = sp.add_parser("osszesit")
    o.add_argument("--olvasas", nargs="+", required=True)
    o.add_argument("--max-hianyos", type=int, default=0)
    o.add_argument("--sablon-top", type=int, default=15)
    o.set_defaults(fn=cmd_osszesit)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
