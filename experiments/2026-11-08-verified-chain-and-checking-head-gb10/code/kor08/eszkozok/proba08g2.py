"""08 G1 — a G2 szabályforgatókönyveinek eldobható próbája (Dani 11-03 21:40: mind a 90-en, Muse + Gemma). A `szint08`
a saját gyökerébe (`kor08/adat/G1/proba_g2`), saját seeddel (`szint06.SEED` + „:proba08g2”: más sablonok, más tervek),
forgatókönyvenként és nyelvenként 1 egységgel (1 (a) + 3 (b)): 90 × 2 × 4 = 720 item. **Nem G2-adat:** nem auditáljuk,
nem értékeljük, fejet nem tanít; a G2 a rögzítés után a saját seedjével generál. Amit mér, forgatókönyvenként:
  - a tényellenőrző: átmegy-e a (b) a `kulcs2`-n, tiszta-e az (a) (a próbálkozások és az elutasítás okai);
  - a Gemma egyezése a konstrukció címkéjével ((a): „egyik sem”, (b): a gold), a négy sorrend átlagával (`gemma06`);
  - a jel fajtája szerint: a gold költségnemének szava szó szerint a jelben vagy nem (G1-rögzítés 13.2).

  szint <szint08-parancs> [kapcsolók]          a `szint08` a próba gyökerén és seedjével (sablon / terv / gen / final)
  osszesit --gemma <kiolvasás.jsonl ...>       → kor08/eredmenyek/G1/proba_g2/osszesites.{json,md}
  diag --url U --model M [--extra J]           az angol képzés-gold (a) szövegei rögzítve (Dani 11-04: a „course” / „exam”
                                               kulcsszó okának igazolása) → kor08/eredmenyek/G1/proba_g2/diag_ken.jsonl
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor06/eszkozok")]
import szint08 as G  # noqa: E402

GY = "kor08/adat/G1/proba_g2"
OUT = EXP / "kor08/eredmenyek/G1/proba_g2"
RESZEK = ("ert_teszt", "ert_tanito")
def telepit_proba() -> None:
    if not G.S.SEED.endswith(":proba08g2"):
        G.S.SEED = f"{G.S.SEED}:proba08g2"
    for r in RESZEK:
        G.EGYSEG[r][G.SZAB] = 1


def cmd_szint(argv: list[str]) -> None:
    if "--csalad" not in argv or argv[argv.index("--csalad") + 1] != G.SZAB:
        raise SystemExit(f"a próba csak a szabálycsaládon fut (--csalad {G.SZAB})")
    if "--resz" in argv and argv[argv.index("--resz") + 1] not in RESZEK:
        raise SystemExit(f"a próba részei: {', '.join(RESZEK)}")
    telepit_proba()
    sys.argv = ["szint08.py", *argv, "--gyoker", GY]
    G.main()


def szo_szerint(f: dict) -> bool:
    return G.FK.jel_fajta(f) == "szó szerint"


def cmd_osszesit(gemma: list[str]) -> None:
    import gemma06 as GM  # noqa: PLC0415
    fk = {(f["id"], lang): f for lang, fs in G.FK.forgatokonyvek().items() for f in fs}
    t = float(json.loads(GM.TEMP_FORRAS.read_text())["tanarkapu"]["gemma"]["temp"])
    by = collections.defaultdict(list)
    for p in gemma:
        for r in GM.jl(Path(p)):
            by[r["id"]].append(r)
    sor = collections.defaultdict(lambda: {"terv": 0, "atment": 0, "probak": 0, "okok": collections.Counter(),
                                           "gemma_n": 0, "gemma_egyezik": 0, "gemma_kat": collections.Counter()})
    egyseg = collections.defaultdict(lambda: [0, 0])  # (rész, nyelv) → [teljes, terv]
    for r_ in RESZEK:
        d = EXP / GY / r_
        items = {it["id"]: it for it in G.S.jl_read(d / "items" / f"{G.SZAB}.jsonl")}
        raw = G.S.jl_read(d / "raw" / f"{G.SZAB}.jsonl")
        kesz = {it["meta"]["ertelmezes"]["egyseg"] for it in items.values()}
        for e in {(p["lang"], p["ertelmezes"]["egyseg"]) for p in G.S.jl_read(d / "terv" / f"{G.SZAB}.jsonl")}:
            egyseg[(r_, e[0])][0] += e[1] in kesz
            egyseg[(r_, e[0])][1] += 1
        for r in raw:
            p, e = r["terv"], r["terv"]["ertelmezes"]
            s = sor[(e["forgatokonyv"], p["lang"], e["alt"])]
            s["terv"] += 1
            s["probak"] += len(r["probak"]) + ("szoveg" in r)
            s["atment"] += "szoveg" in r
            s["okok"].update(r["probak"])
        for iid, it in items.items():
            e = it["meta"]["ertelmezes"]
            rows = sorted(by.get(iid, []), key=lambda x: x["perm"])
            if [x["perm"] for x in rows] != list(GM.PERMS):
                continue
            s = sor[(e["forgatokonyv"], it["lang"], e["alt"])]
            pick = GM.itelet(rows, t)["pick"]
            s["gemma_n"] += 1
            s["gemma_egyezik"] += pick == it["gold"]
            if e["alt"] == "a":  # a Gemma keretében nincs Y: az (a)-n a választás fajtája a beszédes (gold / csali / egyik sem)
                f = fk[(e["forgatokonyv"], it["lang"])]
                txt = next((o["text"].lower() for o in it["options"] if o["id"] == pick), "")
                k = next((k for k, v in G.S.SZAB_TIPUS[it["lang"]].items() if v.lower() in txt), None) if pick else None
                s["gemma_kat"]["–" if pick is None else "g" if k == f["gold"] else "c" if k == f["csali"] else "m"] += 1
    # forgatókönyvenként és a jel fajtája szerint
    fsor, fajta = [], collections.defaultdict(lambda: collections.Counter())
    for fid, sz, g, c, *_ in G.FK.F:
        x = {"id": fid, "szelet": sz, "par": f"{G.FK.NEV[g][0]} ← {G.FK.NEV[c][0]}", "javitva": fid in G.FK.JAVITVA}
        for lang in ("hu", "en"):
            x[f"szo_{lang}"] = szo_szerint(fk[(fid, lang)])
            for alt in ("a", "b"):
                s = sor[(fid, lang, alt)]
                x[f"{alt}_{lang}"] = {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in s.items()}
                if alt == "b":
                    k = fajta["szó szerint" if x[f"szo_{lang}"] else "áttételes"]
                    for kk in ("terv", "atment", "probak", "gemma_n", "gemma_egyezik"):
                        k[kk] += s[kk]
        fsor.append(x)
    okok = collections.Counter()
    for s in sor.values():
        okok.update(s["okok"])
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"egyseg": {f"{r}·{lang}": v for (r, lang), v in sorted(egyseg.items())}, "okok": dict(okok.most_common()),
           "fajta_b": {k: dict(v) for k, v in fajta.items()}, "forgatokonyvek": fsor, "gemma_temp": t}
    (OUT / "osszesites.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    def pc(a: int, b: int) -> str:
        return f"{a}/{b}" + (f" ({100 * a / b:.0f}%)" if b else "")

    o = ["# A G2 szabályforgatókönyveinek próbája (K08G1L; eldobható, nem G2-adat)", "",
         "Saját seed és gyökér, forgatókönyvenként és nyelvenként 1 egység (1 (a) + 3 (b)). „Átment” = a tényellenőrzőn "
         "legfeljebb 3 próbálkozással; Gemma = a négy sorrend átlagának választása; a (b)-n az egyezés a golddal, az (a)-n "
         "(a Gemma keretében nincs Y) a választás fajtája: g = a gold költségneme, c = a csalié, – = egyik sem.", "",
         "## Teljes egységek", "", "| rész · nyelv | teljes / terv |", "|---|---|"]
    o += [f"| {k} | {pc(*v)} |" for k, v in res["egyseg"].items()]
    o += ["", "## Az elutasítás okai (minden próbálkozás)", "", "| ok | db |", "|---|---|"]
    o += [f"| {k} | {v} |" for k, v in res["okok"].items()] or ["| — | 0 |"]
    o += ["", "## (b) a jel fajtája szerint", "", "| jel | (b) átment | próbálkozás / terv | Gemma egyezik |", "|---|---|---|---|"]
    for k, v in sorted(res["fajta_b"].items()):
        o.append(f"| {k} | {pc(v['atment'], v['terv'])} | {v['probak'] / max(v['terv'], 1):.2f} | {pc(v['gemma_egyezik'], v['gemma_n'])} |")
    akat = collections.Counter()
    for x in fsor:
        for lang in ("hu", "en"):
            akat.update(x[f"a_{lang}"]["gemma_kat"])
    o += ["", "## (a): a Gemma választása", "", " · ".join(f"{k}: {v}" for k, v in sorted(akat.items())),
          "", "## Forgatókönyvenként", "", "Jelölés: (a) átment/terv · (b) átment/terv · Gemma (a): g / c / – · Gemma (b) egyezik; "
          "„sz” = a jelben szó szerint a gold szava; ⚠ = valamelyik nyelven nem teljes egység, vagy a (b)-n a Gemma eltér.", "",
          "| id | szelet | gold ← csali | jav. | hu | en |", "|---|---|---|---|---|---|"]
    for x in fsor:
        cel, gond = [], False
        for lang in ("hu", "en"):
            a_, b_ = x[f"a_{lang}"], x[f"b_{lang}"]
            gond |= a_["atment"] < a_["terv"] or b_["atment"] < b_["terv"] or b_["gemma_egyezik"] < b_["gemma_n"]
            ak = "".join(k * v for k, v in sorted(a_["gemma_kat"].items())) or "·"
            cel.append(f"{a_['atment']}/{a_['terv']} · {b_['atment']}/{b_['terv']} · G {ak} · "
                       f"G {b_['gemma_egyezik']}/{b_['gemma_n']}" + (" · sz" if x[f"szo_{lang}"] else ""))
        o.append(f"| {x['id']}{' ⚠' if gond else ''} | {x['szelet']} | {x['par']} | {'igen' if x['javitva'] else ''} | "
                 f"{cel[0]} | {cel[1]} |")
    (OUT / "osszesites.md").write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"→ {OUT / 'osszesites.md'}")


def cmd_diag(argv: list[str]) -> None:
    """A próba angol, képzés-goldú (a) tervei a `szint08e` utasításával és tényellenőrzőjével, a szöveggel együtt: az
    első 3 próbálkozás a generálás seedjével (`gen08e:<group_id>:<k>`), a 4–5. újjal (`diag08ken`)."""
    import argparse  # noqa: PLC0415
    from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--extra", default="")
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args(argv)
    telepit_proba()
    G.E.KOR["n"] = 2
    extra = json.loads(a.extra) if a.extra else {}
    tervek = [p for r in RESZEK for p in G.S.jl_read(EXP / GY / r / "terv" / f"{G.SZAB}.jsonl")
              if p["lang"] == "en" and p["ertelmezes"]["alt"] == "a" and p["tenyek"]["tipus"] == "training"]
    feladat = [(p, k) for p in tervek for k in range(a.n)]

    def egy(pk: tuple[dict, int]) -> dict:
        p, k = pk
        seed = G.S.h(f"gen08e:{p['group_id']}:{k}" if k < 3 else f"diag08ken:{p['group_id']}:{k}") % 10**6
        out = {"group_id": p["group_id"], "forgatokonyv": p["ertelmezes"]["forgatokonyv"], "k": k, "seed": seed,
               "kulcs": p["tenyek"]["kulcs"]}
        try:
            obj = G.S.llm_json(a.url, a.model, p["lang"], G.E.gen_prompt_e(p), extra, seed)
        except RuntimeError as e:
            return out | {"hiba": str(e)}
        txt = str(obj.get("szoveg") or "").strip()
        return out | {"szoveg": txt, "hiba": "üres szöveg" if not txt else G.E.fact_check_e(p, txt)}

    with ThreadPoolExecutor(32) as ex:
        sorok = list(ex.map(egy, feladat))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "diag_ken.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in sorok), encoding="utf-8")
    print(f"{len(tervek)} terv, {len(sorok)} szöveg; elbukott: {collections.Counter(x['hiba'] for x in sorok if x['hiba'])}")


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("szint", "osszesit", "diag"):
        raise SystemExit(__doc__)
    if sys.argv[1] == "szint":
        cmd_szint(sys.argv[2:])
    elif sys.argv[1] == "diag":
        cmd_diag(sys.argv[2:])
    else:
        if sys.argv[2:3] != ["--gemma"] or len(sys.argv) < 4:
            raise SystemExit("osszesit --gemma <kiolvasás.jsonl ...>")
        cmd_osszesit(sys.argv[3:])


if __name__ == "__main__":
    main()
