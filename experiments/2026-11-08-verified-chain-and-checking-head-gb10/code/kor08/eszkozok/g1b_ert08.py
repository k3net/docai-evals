"""08 G1b — az értelmezési konstrukció próbája (`kor08/ertelmezes-javaslat.md`; 08-runbook 3.3, D6). A 07 CAL-sablonjain
generált párok a lánc után (orákulum-út, `lanc08 futtat --forras ERT`), az alany döntése a négyállapotú kerettel
(B1-4S, `b1rel07.decide4`, a 07 B1-4 temperature-jével). Fejlesztési minta, tervezési számok.

A kapu (a javaslat tényellenőrzőjének utolsó pontja): a lánc a goldot és a csalit is lehetségesnek hagyja, és egyiket sem
köti automatikusan. Az (a) tagnál a gold a (b) párjáé. A pár, amelynek bármelyik tagja elbukik, mindkét tagjával
kimarad (a párok együtt mozognak).
Mérés: a (b)-n a rossz opcióválasztás aránya (SELECT, de nem a gold; cél ≥ 20%), ebből a csali, és a nem-SELECT
döntések; az (a)-n az Y-arány és az opcióválasztás (SELECT eldönthetetlen esetben).
  python3 kor08/eszkozok/g1b_ert08.py --jell cache/k08/jellemzok --out kor08/eredmenyek/G1b --kor 1
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(HERE), str(EXP / "kor07/eszkozok")]
import b1rel07 as R  # noqa: E402
import lanc08 as L  # noqa: E402

ERT = EXP / "kor08/adat/ertelmezes"
UT = {"D": ERT, "LANC": EXP / "kor08/adat/G1/orakulum_ERT", "SZ": "ERT"}  # a `--kor` állítja (`kor_utak`)
CEL = 0.20  # D6
STOP = set("a az és vagy de nem is egy után előtt alatt közben the and or of to in on after before with when is are be not "
           "does do".split())


def kor_utak(kor: int, javitott: bool = False) -> None:
    j = "j" if javitott else ""
    sz = "ERT" if kor == 1 else f"ERT{kor}{j.upper()}"
    UT.update(D=ERT if kor == 1 else ERT / f"kor{kor}{j}", LANC=EXP / f"kor08/adat/G1/orakulum_{sz}", SZ=sz)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return 0.0, 0.0
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def oid(p: dict, sid: str | None) -> str | None:
    """A terv sid-je az item opció-azonosítójaként (`szint06.to_item`: o1, o2, … a terv sorrendjében)."""
    return next((f"o{i + 1}" for i, o in enumerate(p["opciok"]) if o["sid"] == sid), None)


def generalas(fam: str) -> dict:
    raw = L.jsonl(UT["D"] / "raw" / f"{fam}.jsonl")
    ok = [r for r in raw if "szoveg" in r]
    return {"terv": len(L.jsonl(UT["D"] / "terv" / f"{fam}.jsonl")), "atment": len(ok),
            "elveszett": dict(Counter(r.get("hiba") for r in raw if "szoveg" not in r)),
            "probak_eloszlasa": dict(Counter(len(r["probak"]) for r in ok))}


def csalad(fam: str, jell: Path, temp: float) -> dict:
    terv = {p["group_id"]: p for p in L.jsonl(UT["D"] / "terv" / f"{fam}.jsonl")}
    b_par = {p["ertelmezes"]["par"]: p for p in terv.values() if p["ertelmezes"]["alt"] == "b"}
    lanc = {r["id"]: r for r in L.jsonl(UT["LANC"] / f"lanc_{fam}.jsonl")}
    items = L.jsonl(UT["D"] / "items" / f"{fam}.jsonl")

    kapu, bukas = {}, Counter()
    for it in items:
        p, r = terv[it["id"]], lanc[it["id"]]
        g, cs = oid(b_par[p["ertelmezes"]["par"]], b_par[p["ertelmezes"]["par"]]["gold_sid"]), oid(p, p["csali_sid"])
        ok = ("automatikus kötés" if r["kimenet"] == "kotes" else "a gold kizárva" if g not in r["megmaradt"]
              else "a csali kizárva" if cs not in r["megmaradt"] else f"kimenet: {r['kimenet']}" if r["kimenet"] != "modell"
              else None)
        kapu[it["id"]] = (ok is None, g, cs)
        if ok is not None:
            bukas[f"({p['ertelmezes']['alt']}) {ok}"] += 1
    par_ok = defaultdict(lambda: True)
    for it in items:
        par_ok[terv[it["id"]]["ertelmezes"]["par"]] &= kapu[it["id"]][0]

    by = R.rows4(f"o{UT['SZ']}_{fam}_{UT['SZ']}", jell)
    c: dict = {alt: defaultdict(Counter) for alt in ("b", "a")}
    par_kep = Counter()
    dont, bizt = {}, []
    for it in items:
        p = terv[it["id"]]
        e = p["ertelmezes"]
        if not par_ok[e["par"]]:
            continue
        _, g, cs = kapu[it["id"]]
        d = R.decide4(by[it["id"]], temp)
        if d["kind"] == "SELECT":
            k = "gold" if d["cand"] == g else "csali" if d["cand"] == cs else "más opció"
        else:
            k = {"NONE": "X", "MISSING": "Y", "OOS": "Z"}[d["kind"]]
        dont[it["id"]] = k
        bizt.append((d["q"], k, e["alt"]))
        for nyelv in ("mind", p["lang"]):
            c[e["alt"]][nyelv]["n"] += 1
            c[e["alt"]][nyelv][k] += 1
    for it in items:
        e = terv[it["id"]]["ertelmezes"]
        if e["alt"] == "a" and it["id"] in dont:
            b_id = next(i for i, p in terv.items() if p["ertelmezes"]["par"] == e["par"] and p["ertelmezes"]["alt"] == "b")
            par_kep[f"(b) {dont[b_id]} · (a) {dont[it['id']]}"] += 1
    fk = defaultdict(Counter)  # a szabálycsaládon forgatókönyvenként (a javított kör a javítottakat külön jelöli)
    if fam == L.SZAB:
        import ertelmezes08_szab as SZ  # noqa: PLC0415
        for i, k in dont.items():
            p = terv[i]
            x = next(n for n, f in enumerate(SZ.FORGATOKONYV[p["lang"]]) if f["helyzet"] == p["tenyek"]["helyzet"])
            cel = fk[f"{p['lang']} {x + 1:02d}{' (javítva)' if p['ertelmezes'].get('javitott') else ''}"]
            cel[f"{p['ertelmezes']['alt']} n"] += 1
            cel[f"{p['ertelmezes']['alt']} {k}"] += 1
    return {"generalas": generalas(fam), "item": len(items), "kapu_bukas": dict(bukas),
            "forgatokonyv": {k: dict(v) for k, v in sorted(fk.items())},
            "par_kimarad": sum(not v for v in par_ok.values()),
            "dontesek": {alt: {ny: dict(x) for ny, x in v.items()} for alt, v in c.items()},
            "parok": dict(par_kep.most_common()), "bizonyossag": bizonyossag(bizt),
            "atfedes": atfedes(fam, items, terv),
            "itemek": {i: [k, round(q, 4)] for (i, k), (q, _, _) in zip(dont.items(), bizt)}}


def atfedes(fam: str, items: list[dict], terv: dict) -> dict:
    """Ellenőrző adat, nem kapu (Dani 11-02): a (b) szövegekben mennyire nyílt a jel. Bank: az 1. kör viszonyszavai
    (`szint08e.VISZONY`); szabály: az 1. kör kulcsszavai; hiba: a gold tünetének tartalmi szótövei (5 betű)."""
    import szint08e as E  # noqa: PLC0415
    b = [it for it in items if terv[it["id"]]["ertelmezes"]["alt"] == "b"]
    if not b:
        return {}
    if fam == L.BANK:
        k = sum(bool(E.VISZONY[it["lang"]].search(it["state"])) for it in b)
        return {"mérőszám": "az 1. kör viszonyszava a (b)-ben", "arany": k / len(b)}
    if fam == L.SZAB:
        k = sum(any(x.lower() in it["state"].lower() for x in terv[it["id"]]["tenyek"]["kulcs"]) for it in b)
        return {"mérőszám": "az 1. kör kulcsszava a (b)-ben", "arany": k / len(b)}
    ar = []
    for it in b:
        w = [x for x in re.findall(r"\w+", terv[it["id"]]["tenyek"]["tunet"].lower()) if x not in STOP and len(x) > 3]
        ar.append(sum(x[:5] in it["state"].lower() for x in w) / max(1, len(w)))
    ar.sort()
    return {"mérőszám": "a gold tünetének szótövei a (b)-ben, medián", "arany": ar[len(ar) // 2]}


def auroc(pos: list[float], neg: list[float]) -> float | None:
    """P(pos > neg), a döntetlen fél (rangalapú, a standard könyvtárral)."""
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def bizonyossag(b: list[tuple[float, str, str]]) -> dict:
    """Feltáró, a két vizsgálati ág szerint külön (Dani, 11-02): az alany saját bizonyossága (a négy sorrend átlagolt
    valószínűsége a választott válaszon).
      K1(b)  a (b) SELECT-jei: a gold választása a rossz opció választásától
      K1(a)  az (a) SELECT-jei (eldönthetetlen választás, mind hibás) a (b) helyes SELECT-jeitől
    A K1(a) száma nem helyes–hibás összevetés ugyanazon a feladaton, és a K1(b)-t nem helyettesíti."""
    def med(x: list[float]) -> float | None:
        return sorted(x)[len(x) // 2] if x else None
    b_jo = [q for q, k, alt in b if alt == "b" and k == "gold"]
    b_rossz = [q for q, k, alt in b if alt == "b" and k in ("csali", "más opció")]
    a_sel = [q for q, k, alt in b if alt == "a" and k in ("gold", "csali", "más opció")]
    return {"K1b": {"n_gold": len(b_jo), "n_rossz": len(b_rossz), "auroc": auroc(b_jo, b_rossz),
                    "median_q": [med(b_jo), med(b_rossz)]},
            "K1a": {"n_b_helyes": len(b_jo), "n_a_select": len(a_sel), "auroc": auroc(b_jo, a_sel),
                    "median_q": [med(b_jo), med(a_sel)]}}


def pct(k: int, n: int) -> str:
    return f"{k} / {n} ({100 * k / n:.0f}%)" if n else "–"


def lap(res: dict) -> str:
    kor = str(res["kor"])
    kor = f"{kor[:-1]}. kör, javított címkék" if kor.endswith("j") else f"{kor}. kör"
    out = [f"# 08 G1b, {kor} — az értelmezési konstrukció próbája (fejlesztési minta, a 07 CAL-sablonjain)", "",
           "Az alany (B1-4S) döntése a lánc után, orákulum-úton. A (b)-ben a jel a bemenetben, a helyes válasz a gold; az",
           "(a) ugyanaz a jel nélkül, a helyes válasz Y. A cél a (b)-n legalább 20% rossz opcióválasztás (D6).", "",
           "## A (b) változat: rossz opcióválasztás", "",
           "| család | n | gold | rossz opció | ebből csali | 95% Wilson | X | Y | Z | eléri a 20%-ot |", "|---|---|---|---|---|---|---|---|---|---|"]
    for fam, F in res["csaladok"].items():
        b = F["dontesek"]["b"].get("mind", {})
        n, rossz = b.get("n", 0), b.get("csali", 0) + b.get("más opció", 0)
        lo, hi = wilson(rossz, n)
        out.append(f"| {fam} | {n} | {b.get('gold', 0)} | {pct(rossz, n)} | {b.get('csali', 0)} | {100 * lo:.0f}–{100 * hi:.0f}% | "
                   f"{b.get('X', 0)} | {b.get('Y', 0)} | {b.get('Z', 0)} | {'igen' if n and rossz / n >= CEL else 'nem'} |")
    out += ["", "## Az (a) változat: Y-arány", "",
            "| család | n | Y | SELECT (gold / csali / más) | X | Z |", "|---|---|---|---|---|---|"]
    for fam, F in res["csaladok"].items():
        a = F["dontesek"]["a"].get("mind", {})
        n = a.get("n", 0)
        out.append(f"| {fam} | {n} | {pct(a.get('Y', 0), n)} | {a.get('gold', 0)} / {a.get('csali', 0)} / {a.get('más opció', 0)} | "
                   f"{a.get('X', 0)} | {a.get('Z', 0)} |")
    out += ["", "## Nyelvenként (b: rossz opció; a: Y)", ""]
    for fam, F in res["csaladok"].items():
        r = []
        for ny in ("hu", "en"):
            b, a = F["dontesek"]["b"].get(ny, {}), F["dontesek"]["a"].get(ny, {})
            r.append(f"{ny}: (b) {pct(b.get('csali', 0) + b.get('más opció', 0), b.get('n', 0))}, (a) Y {pct(a.get('Y', 0), a.get('n', 0))}")
        out.append(f"- {fam}: " + "; ".join(r))
    out += ["", "## A párok képe (a (b) és az (a) döntése együtt)", ""]
    for fam, F in res["csaladok"].items():
        out.append(f"- {fam}: " + "; ".join(f"{k}: {v}" for k, v in F["parok"].items()))
    out += ["", "## Feltáró: az alany saját bizonyossága (fej nélkül), a két ág külön", "",
            "A választott válasz átlagolt valószínűsége (négy sorrend) mint pontszám. Fejlesztési minta, nem állítás.",
            "- **K1(b):** a (b) SELECT-jei; a gold választása vs. a rossz opció választása.",
            "- **K1(a):** az eldönthetetlen választások (az (a) SELECT-jei, mind hibásak) vs. az eldönthető, helyes választások",
            "  (a (b) gold-választásai). Ez nem helyes–hibás összevetés ugyanazon a feladaton, és a K1(b)-t nem helyettesíti.", "",
            "| család | K1(b): gold / rossz opció | K1(b) AUROC | K1(b) medián q | K1(a): (b) helyes / (a) SELECT | K1(a) AUROC | K1(a) medián q |",
            "|---|---|---|---|---|---|---|"]
    f2 = lambda x: "–" if x is None else f"{x:.2f}"  # noqa: E731
    for fam, F in res["csaladok"].items():
        b1, a1 = F["bizonyossag"]["K1b"], F["bizonyossag"]["K1a"]
        out.append(f"| {fam} | {b1['n_gold']} / {b1['n_rossz']} | {f2(b1['auroc'])} | {f2(b1['median_q'][0])} / {f2(b1['median_q'][1])} | "
                   f"{a1['n_b_helyes']} / {a1['n_a_select']} | {f2(a1['auroc'])} | {f2(a1['median_q'][0])} / {f2(a1['median_q'][1])} |")
    out += ["", "## Ellenőrző adat: mennyire nyílt a jel a (b)-ben (nem kapu)", ""]
    for fam, F in res["csaladok"].items():
        x = F.get("atfedes") or {}
        if x:
            out.append(f"- {fam}: {x['mérőszám']}: {100 * x['arany']:.0f}%")
    for fam, F in res["csaladok"].items():
        if F.get("forgatokonyv"):
            out += ["", f"## Forgatókönyvenként ({fam})", "", "| forgatókönyv | (b) n | (b) rossz opció | (a) n | (a) Y |",
                    "|---|---|---|---|---|"]
            for k, c in F["forgatokonyv"].items():
                out.append(f"| {k} | {c.get('b n', 0)} | {c.get('b csali', 0) + c.get('b más opció', 0)} | {c.get('a n', 0)} | "
                           f"{c.get('a Y', 0)} |")
    out += ["", "## Generálás és kapu", "",
            "| család | terv | a tényellenőrzőn átment | item (teljes pár) | a lánc-kapun elbukott | kimaradt pár |",
            "|---|---|---|---|---|---|"]
    for fam, F in res["csaladok"].items():
        g = F["generalas"]
        out.append(f"| {fam} | {g['terv']} | {g['atment']} | {F['item']} | "
                   f"{'; '.join(f'{k} {v}' for k, v in F['kapu_bukas'].items()) or '0'} | {F['par_kimarad']} |")
    out += ["", "A generálásban elveszett tervek oka:", ""]
    for fam, F in res["csaladok"].items():
        out.append(f"- {fam}: " + ("; ".join(f"{k}: {v}" for k, v in F["generalas"]["elveszett"].items()) or "–"))
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jell", default="cache/k08/jellemzok")
    ap.add_argument("--out", required=True)
    ap.add_argument("--kor", type=int, default=1)
    ap.add_argument("--javitott", action="store_true")  # a 2. kör javított címkéi (szabálycsalád, `kor2j`)
    ap.add_argument("--csalad", action="append", choices=L.CSALADOK)
    a = ap.parse_args()
    kor_utak(a.kor, a.javitott)
    if a.javitott:
        import ertelmezes08_szab as SZ  # noqa: PLC0415
        SZ.alkalmaz_javitas()
    nev = f"{a.kor}{'j' if a.javitott else ''}"
    temp = json.loads((EXP / "cache/k07/fejek/temperature.json").read_text())["B1-4"]
    res = {"kor": nev, "temperature": temp,
           "csaladok": {fam: csalad(fam, EXP / a.jell, temp) for fam in (a.csalad or L.CSALADOK)}}
    out = EXP / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / f"kor{nev}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (out / f"kor{nev}.md").write_text(lap(res), encoding="utf-8")
    print(lap(res))


if __name__ == "__main__":
    main()
