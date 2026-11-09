"""07-es kör — a nehéz próbaminta (07-runbook 3.3, D11): MATCH-esetek, ahol két jelölt a szövegben említett minden
jegyben egyezik, és csak egy, a szövegből kiolvasható részletben tér el. A `szint06` burkolója: a sablonok a 06 T500
sablonjai (ismertek; fejlesztési célra), a terv itt készül, a generálás, a tényellenőrzés és az item-forma a szint06-é
(a szint06 a 06 v1 manifestjében van, nem módosul).

A nehéz változat családonként:
  bank        az iker számla: ugyanaz a partner és összeg, a számlaszám egy jegyben eltér vagy két szomszédos jegye
              felcserélve; a tételben a partner és a (helyes) számlaszám is szerepel
  szabály     a költségnem másik sávja mellett az összeg a küszöb közelében (a küszöb 93–99%-a, illetve 101–107%-a)
  hiba        a jelölt pár mindkét mérése a saját küszöbe közelében (3%): a valódi ok mérése épphogy teljesíti a
              szabályt, a páré épphogy nem

A konstrukció körei (D11: a nehezítés csak a próbamintán, a végső minta a rögzített körrel készül):
  1. kör (2026-10-31 este, `kor07/adat/nehez`): a fentiek; a B1-nek nem elég nehéz (bank 0 / 117, hiba 6 / 119,
     szabály 15 / 120 rossz opció)
  2. kör (`kor07/adat/nehez2`): bank: az iker ugyanazzal a partnerrel, de az összeg két szomszédos jegye felcserélve
     vagy 0,5–3%-kal más, a tételben csak a partner és az összeg (számlaszám nincs); hiba: a mérések a küszöb 1%-os
     környezetében; szabály: az összeg a küszöb 98–99,5%-a vagy 100,5–102%-a

Kimenet: kor07/adat/nehez[<kör>]/{terv,raw,items}/<család>.jsonl; split = NEHEZ; az item-id
`<család>:NEHEZ:<nyelv>:MATCH:<n>`.
  terv  --csalad F [--per-sablon 4] [--kor 2]
  gen   --csalad F --url U --model M [--extra J] [--workers N] [--kor 2]
  final --csalad F [--kor 2]
"""

from __future__ import annotations

import argparse
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
sys.path[:0] = [str(EXP / "kor06/eszkozok")]
import szint06 as S  # noqa: E402

KOR = {"n": 1}
SZELET = "NEHEZ"
CSALADOK = ("penzugy.bankparositas", "muszaki.hibaelharitas", "szabaly.koltsegelszamolas")


def d07() -> Path:
    return EXP / f"kor07/adat/nehez{'' if KOR['n'] == 1 else KOR['n']}"


def path07(kind: str, fam: str, _proba: bool = False) -> Path:
    return d07() / kind / f"{fam}.jsonl"


def iker_osszeg(rnd: random.Random, osszeg: int, foglalt: set[int], lang: str) -> tuple[int, str]:
    """A 2. kör banki ikre: az összeg két szomszédos jegye felcserélve (ha az értéket változtatja), különben 0,5–3%-kal
    más; egyik meglévő számla összegével sem egyezik."""
    for _ in range(50):
        if rnd.random() < 0.5:
            d = list(str(osszeg))
            i = rnd.randrange(len(d) - 1)
            if d[i] == d[i + 1] or (i == 0 and d[i + 1] == "0"):
                continue
            d[i], d[i + 1] = d[i + 1], d[i]
            uj, valt = int("".join(d)), "osszeg-csere"
        else:
            uj = int(osszeg * (1 + rnd.choice([-1, 1]) * rnd.uniform(0.005, 0.03)))
            uj, valt = (uj // 10 * 10 if lang == "hu" else uj), "osszeg-kozeli"
        if uj != osszeg and uj not in foglalt and uj > 0:
            return uj, valt
    raise RuntimeError(f"nincs iker a(z) {osszeg} összeghez")


def sablonok(fam: str) -> list[dict]:
    """A 06 T500 sablonjai (a szint06 saját útján; a `path` cseréje előtt olvassuk)."""
    return [s for s in S.jl_read(S.D / "sablon" / f"{fam}.jsonl") if s["szelet"] == "T500"]


def kozel(v: float, lang: str) -> str:
    """Legfeljebb három értékes jegy, a szint06 `fmt_num` formájában (vesszővel magyarul)."""
    s = f"{float(f'{v:.3g}'):g}"
    return s.replace(".", ",") if lang == "hu" else s


def iker_szam(rnd: random.Random, szam: str, foglalt: set[str]) -> tuple[str, str]:
    """A számlaszám utolsó négy jegyének egy jegye más, vagy két szomszédos jegye felcserélve."""
    head, tail = szam[:-4], szam[-4:]
    for _ in range(50):
        d = list(tail)
        if rnd.random() < 0.5:
            i = rnd.randrange(4)
            d[i] = rnd.choice([c for c in "0123456789" if c != d[i]])
            valt = "szamlaszam-1jegy"
        else:
            i = rnd.randrange(3)
            if d[i] == d[i + 1]:
                continue
            d[i], d[i + 1] = d[i + 1], d[i]
            valt = "szamlaszam-csere"
        uj = head + "".join(d)
        if uj not in foglalt:
            return uj, valt
    raise RuntimeError(f"nincs iker a(z) {szam} számhoz")


def plan_nehez(fam: str, sab: dict, seq: int) -> dict:
    rnd = S.rnd_for("nehez", sab["sablon_id"], seq)
    lang = sab["lang"]
    p = {"csalad": fam, "sablon_id": sab["sablon_id"], "lang": lang, "allapot": "MATCH", "szelet": SZELET,
         "dim": {k: rnd.choice(v)[S.LANGS.index(lang)] for k, v in S.DIM[fam].items()}}
    k = rnd.randint(S.K["opciok"]["min"], S.K["opciok"]["max"])
    if fam == "penzugy.bankparositas":
        inv = sab["szamlak"]
        target = rnd.choice(inv)
        if KOR["n"] == 1:
            uj, valt = iker_szam(rnd, target["szamlaszam"], {s["szamlaszam"] for s in inv})
            iker = {**target, "id": "s_iker", "szamlaszam": uj}  # ugyanaz a partner, összeg és esedékesség
            azon = {"partner": target["partner"], "szamlaszam": target["szamlaszam"]}
        else:
            uj, valt = iker_osszeg(rnd, target["osszeg"], {s["osszeg"] for s in inv}, lang)
            szam, _ = iker_szam(rnd, target["szamlaszam"], {s["szamlaszam"] for s in inv})
            iker = {**target, "id": "s_iker", "osszeg": uj, "szamlaszam": szam}  # ugyanaz a partner és esedékesség
            azon = {"partner": target["partner"]}  # a tételben számlaszám nincs: az összeg dönt
        pool = [s for s in inv if s is not target]
        opts = [target, iker] + rnd.sample(pool, k - 2)
        p["tenyek"] = {"osszeg": target["osszeg"], "irany": rnd.choice(S.IRANY[lang]),
                       "datum": S.tx_date(rnd, [target["kelt"]] + [s["kelt"] for s in opts]), **azon}
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": s["id"], "text": f"{s['szamlaszam']} · {s['partner']} · {S.money(s['osszeg'], lang)} · "
                                                 f"{'esedékes' if lang == 'hu' else 'due'} {s['esedekes']}"} for s in opts]
        p["gold_sid"], p["sajat_ceg"], p["nehez"] = target["id"], sab["ceg"], {"valt": valt}
    elif fam == "szabaly.koltsegelszamolas":
        pts = sab["pontok"]
        target = rnd.choice([x for x in pts if any(y["tipus"] == x["tipus"] and y is not x for y in pts)])
        iker = next(y for y in pts if y["tipus"] == target["tipus"] and y is not target)
        rest = [x for x in pts if x not in (target, iker)]
        opts = [target, iker] + rnd.sample(rest, max(0, min(k, len(pts)) - 2))
        hatar = target["hatar"]
        osszeg = hatar - 10 if target["sav"] == 0 else hatar + 10  # ha a sorsolás százszor is a küszöbre esne
        lo, hi = ((0.93, 0.99), (1.01, 1.07)) if KOR["n"] == 1 else ((0.98, 0.995), (1.005, 1.02))
        for _ in range(100):
            v = hatar * (rnd.uniform(*lo) if target["sav"] == 0 else rnd.uniform(*hi))
            v = int(v) // 10 * 10 if lang == "hu" else int(v)
            if (v < hatar) == (target["sav"] == 0) and v != hatar:
                osszeg = v
                break
        p["tenyek"] = {"tipus": target["tipus"], "tipus_leiras": S.SZAB_TIPUS[lang][target["tipus"]],
                       "helyzet": rnd.choice(S.SZAB_HELYZET[lang][target["tipus"]]), "osszeg": osszeg}
        rnd.shuffle(opts)
        p["opciok"] = [{"sid": x["id"], "text": x["szoveg"]} for x in opts]
        p["gold_sid"], p["szervezet"] = target["id"], sab["szervezet"]
        p["nehez"] = {"valt": "kuszob-kozeli", "arany": round(osszeg / hatar, 3)}
    elif fam == "muszaki.hibaelharitas":
        groups = sab["tunetcsoportok"]
        okok = [(gi, oi, o) for gi, g in enumerate(groups) for oi, o in enumerate(g["okok"])]
        sid = lambda gi, oi: f"c{gi}{oi}"  # noqa: E731

        def kozeli(o: dict, teljesul: bool) -> dict:
            """A mérés a saját küszöbe 3%-os (2. kör: 1%-os) környezetében, a kívánt oldalon."""
            m = o["meres"]
            kus = S._num(m["kuszob"])
            lent = (m["relacio"] == "<") == teljesul  # a kívánt érték a küszöb alatt van-e
            e = 0.03 if KOR["n"] == 1 else 0.01
            v = kus * (1 - e if lent else 1 + e)
            s = kozel(v, lang)
            if S._num(s) == kus or (S._num(s) < kus) != lent:
                s = kozel(kus * (0.9 if lent else 1.1), lang)
            return {"nev": m["nev"], "ertek": s, "egyseg": m["egyseg"]}
        gi, ti = rnd.randrange(4), rnd.randrange(2)
        a_, b_ = groups[gi]["okok"]
        t, o = groups[gi]["okok"][ti], groups[gi]["okok"][1 - ti]
        others = [x for x in okok if x[0] != gi]
        zaj = [{"nev": x["meres"]["nev"], "ertek": S.fmt_num(x["meres"]["ertek_normal" if rnd.random() < 0.5 else "ertek_ha_ez"], lang),
                "egyseg": x["meres"]["egyseg"]} for _, _, x in rnd.sample(others, 1)][:rnd.choice([0, 1])]
        mer = [kozeli(t, True), kozeli(o, False)] + zaj
        rnd.shuffle(mer)
        opts = [(gi, 0, a_), (gi, 1, b_)] + rnd.sample(others, k - 2)
        rnd.shuffle(opts)
        p["berendezes"], p["modell"] = sab["berendezes"], sab["modell"]
        p["tenyek"] = {"tunet": groups[gi]["tunet"], "meresek": mer}
        p["opciok"] = [{"sid": sid(g, i), "nev": x["nev"], "text": f"{x['nev']} — {S.hiba_szabaly(x, groups[g]['tunet'], lang)}"}
                       for g, i, x in opts]
        p["gold_sid"], p["nehez"] = sid(gi, ti), {"valt": "kuszob-kozeli-meres"}
    else:
        raise SystemExit(f"ismeretlen család: {fam}")
    return p


def cmd_terv(a) -> None:
    fam = a.csalad
    rows = []
    for lang in S.LANGS:
        sabs = sorted((s for s in sablonok(fam) if s["lang"] == lang), key=lambda s: s["sablon_id"])
        i = 0
        for sab in sabs:
            for _ in range(a.per_sablon):
                gid = f"{fam}:{SZELET}:{lang}:MATCH:{i:04d}"
                rows.append(plan_nehez(fam, sab, i) | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:nehez:{gid}") % 10**12})
                i += 1
    S.jl_write(path07("terv", fam), rows)
    print(f"{fam}: {len(rows)} nehéz terv; " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(r["nehez"]["valt"] for r in rows).items())))


# --- a friss CAL és TESZT (07-runbook 3.2, D4): új sablonok, a 06 generátora ----------------------------------------
# A T500 a 06-os marad; családonként CAL 500 + TESZT 1000 (a 06 kvótája), nyelvenként 15 + 30 új sablon. A sablon-id
# `<család>:k07:<nyelv>:<n>`, az item-id `<család>:<CAL|TESZT>:<nyelv>:<állapot>:k07-<n>` (a 06-os id-ktől eltér; az
# állapot a 4. mező marad). Kimenet: kor07/adat/f2/{sablon,terv,raw,items}/<család>.jsonl.
#   friss-sablon --csalad F [--url U --model M]   friss-terv --csalad F   friss-gen --csalad F --url U --model M
#   friss-final --csalad F

F2 = EXP / "kor07/adat/f2"
SPLITS07 = ("CAL", "TESZT")


def path_f2(kind: str, fam: str, _proba: bool = False) -> Path:
    return F2 / kind / f"{fam}.jsonl"


def sablon_ids07(fam: str, _proba: bool = False) -> list[tuple[str, str, str]]:
    n = {sz: S.K["sablon_per_nyelv"][sz] for sz in SPLITS07}
    out = []
    for lang in S.LANGS:
        ids = sorted((f"{fam}:k07:{lang}:{i:03d}" for i in range(sum(n.values()))), key=lambda t: S.h(f"{S.SEED}:k07:szelet:{t}"))
        k = 0
        for sz in SPLITS07:
            out += [(t, lang, sz) for t in ids[k:k + n[sz]]]
            k += n[sz]
    return out


def quotas07(_proba: bool = False) -> dict[tuple[str, str, str], int]:
    out = {}
    for sz in SPLITS07:
        for lang in S.LANGS:
            for st in S.STATES:
                q = round(S.K["alapeset"][sz] * S.K["nyelv_arany"][lang] * S.K["allapot_arany"][st])
                out[(sz, lang, st)] = q + max(2, round(q * S.K["tartalek"]))
    return out


def cmd_friss_terv(a) -> None:
    """A szint06 `cmd_terv`-je pótlás nélkül, 07-es id-kkal."""
    fam = a.csalad
    by = defaultdict(list)
    for s in S.jl_read(path_f2("sablon", fam)):
        by[(s["szelet"], s["lang"])].append(s)
    rows = []
    for (sz, lang, st), n in quotas07().items():
        pool = sorted(by[(sz, lang)], key=lambda s: S.h(f"{S.SEED}:kiosztas:{s['sablon_id']}:{st}"))
        if not pool:
            raise SystemExit(f"{fam}: nincs sablon a(z) {sz}/{lang} cellához")
        for i in range(n):
            sab = pool[i % len(pool)]
            gid = f"{fam}:{sz}:{lang}:{st}:k07-{i:04d}"
            rows.append(S.plan_case(fam, sab, st, i) | {"group_id": gid, "sorrend": S.h(f"{S.SEED}:sorrend:{gid}") % 10**12})
    S.jl_write(path_f2("terv", fam), rows)
    print(f"{fam}: {len(rows)} friss terv; " + ", ".join(f"{k}={v}" for k, v in sorted(Counter(r["allapot"] for r in rows).items())))


def friss(a) -> None:
    S.path = path_f2
    S.sablon_ids = sablon_ids07
    S.quotas = quotas07
    S.SPLITS = SPLITS07
    a.proba = False
    if a.cmd == "friss-sablon":
        S.cmd_sablon(a)
    elif a.cmd == "friss-terv":
        cmd_friss_terv(a)
    elif a.cmd == "friss-gen":
        S.cmd_gen(a)
    else:
        S.cmd_final(a)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("terv")
    t.add_argument("--csalad", required=True, choices=CSALADOK)
    t.add_argument("--per-sablon", type=int, default=4)
    g = sub.add_parser("gen")
    g.add_argument("--csalad", required=True, choices=CSALADOK)
    g.add_argument("--url", required=True)
    g.add_argument("--model", required=True)
    g.add_argument("--extra", default="")
    g.add_argument("--workers", type=int, default=32)
    f = sub.add_parser("final")
    f.add_argument("--csalad", required=True, choices=CSALADOK)
    for sp in (t, g, f):
        sp.add_argument("--kor", type=int, default=1, help="a konstrukció köre (1 vagy 2)")
    fs = sub.add_parser("friss-sablon")
    fs.add_argument("--url", default="")
    fs.add_argument("--model", default="")
    ft = sub.add_parser("friss-terv")
    fg = sub.add_parser("friss-gen")
    fg.add_argument("--url", required=True)
    fg.add_argument("--model", required=True)
    ff = sub.add_parser("friss-final")
    for sp in (fs, ft, fg, ff):
        sp.add_argument("--csalad", required=True, choices=CSALADOK)
    for sp in (fs, fg):
        sp.add_argument("--extra", default="")
        sp.add_argument("--workers", type=int, default=32)
    a = ap.parse_args()
    if a.cmd.startswith("friss-"):
        friss(a)
        return
    KOR["n"] = a.kor
    a.proba = True  # a szint06 `final`-ja: minden túlélő marad, cellakvóta nélkül
    S.path = path07
    if a.cmd == "terv":
        cmd_terv(a)
    elif a.cmd == "gen":
        S.cmd_gen(a)
    else:
        S.cmd_final(a)
        items = S.jl_read(path07("items", fam := a.csalad))
        print(f"{fam}: {len(items)} nehéz item, sablon {len({it['template_group_id'] for it in items})}, "
              f"nyelv {dict(Counter(it['lang'] for it in items))}")


if __name__ == "__main__":
    main()
