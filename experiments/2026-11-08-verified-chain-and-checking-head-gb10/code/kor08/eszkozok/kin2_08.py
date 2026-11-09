"""08 G1 — a kinyerés javításának célzott próbája (séma v2; Dani 11-02: „a hibás esetek mellett egy előre kijelölt,
korábban helyesen működő kontrollmintán is”). Csak a standard könyvtár.

  valaszt   a minták kijelölése a futás előtt, a v1 menet lánckimeneteiből (`kor08/adat/G1/kin2_proba/`):
              hibas     minden item, ahol a v1 lánckimenete (kimenet, megmaradt, kötés, blokk) eltér az orákuluméétól,
                        vagy emberhez ment
              kontroll  cellánként (forrás × család) KONTROLL item a többiből, a `SEED` hash-sorrendjében
  osszevet  a v2 kinyerés lánca a két mintán, a v1-hez és az orákulumhoz mérve → `kor08/eredmenyek/G1/kin2_proba.{json,md}`
  valaszt3  a közös kontroll (Dani 11-02, a teljes újrafuttatás mellett): cellánként KONTROLL item a bank- és a
            szabálycsaládon, a két korábbi kontrollmintán kívülről, a helyességre szűrés nélkül
  kozos     a közös kontrollon mindkét séma friss kinyerése ugyanazzal a lánckóddal és blokkal: hány korábban helyes
            item romlik el, hány javul, és van-e hamis kizárás vagy kötés → `kor08/eredmenyek/G1/kin2_kozos.{json,md}`

Az előre rögzített siker (08-runbook napló, 11-02): a hibás eseteken a javult mínusz az elromlott > 0, és a K3 diag
szabálycsaládon a döntést befolyásoló hiba és az emberhez küldés együtt legalább a felére csökken; a kontrollon
legfeljebb 1% új eltérés, hamis kizárás és hamis kötés 0.
  python3 kor08/eszkozok/kin2_08.py valaszt
  python3 kor08/eszkozok/kin2_08.py osszevet --kinyeres kor08/adat/G1/kin2_proba/kinyeres
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1_lanc08 as G  # noqa: E402
import lanc08 as L  # noqa: E402

EXP = L.EXP
G1 = EXP / "kor08/adat/G1"
D = G1 / "kin2_proba"
FORRASOK = ("06", "07", "K3diag")
KONTROLL = 40
SEED = "k08kin2"


def valaszt(a) -> None:
    D.mkdir(parents=True, exist_ok=True)
    hibas, kontroll, man = [], [], {}
    for src in FORRASOK:
        for fam in L.CSALADOK:
            parok = L.betolt(src, fam)
            kin = {it["id"]: r for (_, it), r in zip(parok, _lanc(src, fam, "kinyert", parok))}
            ora = {it["id"]: r for (_, it), r in zip(parok, _lanc(src, fam, "orakulum", parok))}
            h = [i for i in kin if kin[i]["kimenet"] == "emberhez" or G.kulcs(kin[i]) != G.kulcs(ora[i])]
            k = sorted((i for i in kin if i not in set(h)), key=lambda i: hashlib.sha256(f"{SEED}:{i}".encode()).hexdigest())
            hibas += h
            kontroll += k[:KONTROLL]
            man[f"{src}|{fam}"] = {"hibas": len(h), "kontroll": len(k[:KONTROLL])}
    (D / "hibas.txt").write_text("\n".join(hibas) + "\n", encoding="utf-8")
    (D / "kontroll.txt").write_text("\n".join(kontroll) + "\n", encoding="utf-8")
    (D / "idk.txt").write_text("\n".join(hibas + kontroll) + "\n", encoding="utf-8")
    sha = {f: hashlib.sha256((D / f).read_bytes()).hexdigest() for f in ("hibas.txt", "kontroll.txt")}
    (D / "minta.json").write_text(json.dumps({"cellak": man, "sha256": sha, "seed": SEED, "kontroll_cellankent": KONTROLL},
                                             ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False), f"\nhibás {len(hibas)}, kontroll {len(kontroll)}", sha)


def valaszt2(a) -> None:
    """A 3. próba friss kontrollmintája (a két korábbi próba a `kontroll.txt`-t már kétszer látta): cellánként KONTROLL
    item a bank- és a szabálycsaládon, a `hibas` és a `kontroll` mintán kívülről, ahol a v1 lánca (a mostani kóddal)
    az orákuluméval egyezik, egy másik hash-sorrendben."""
    regi = set((D / "hibas.txt").read_text(encoding="utf-8").split()) | set((D / "kontroll.txt").read_text(encoding="utf-8").split())
    k2, man = [], {}
    for src in FORRASOK:
        for fam in (L.BANK, L.SZAB):
            parok = L.betolt(src, fam)
            kin = _lanc(src, fam, "kinyert", parok)
            ora = _lanc(src, fam, "orakulum", parok)
            jo = [it["id"] for (_, it), x, o in zip(parok, kin, ora)
                  if it["id"] not in regi and x["kimenet"] != "emberhez" and G.kulcs(x) == G.kulcs(o)]
            jo.sort(key=lambda i: hashlib.sha256(f"{SEED}b:{i}".encode()).hexdigest())
            k2 += jo[:KONTROLL]
            man[f"{src}|{fam}"] = len(jo[:KONTROLL])
    (D / "kontroll2.txt").write_text("\n".join(k2) + "\n", encoding="utf-8")
    regi_bs = [i for i in sorted(regi) if not i.startswith(L.HIBA)]
    (D / "idk3.txt").write_text("\n".join(regi_bs + k2) + "\n", encoding="utf-8")
    kz = set((D / "kontroll.txt").read_text(encoding="utf-8").split()) | set(k2)
    (D / "idk3_v1.txt").write_text("\n".join(i for i in sorted(kz) if not i.startswith(L.HIBA)) + "\n", encoding="utf-8")
    m = json.loads((D / "minta.json").read_text(encoding="utf-8"))
    m["kontroll2"] = {"cellak": man, "seed": f"{SEED}b", "sha256": hashlib.sha256((D / "kontroll2.txt").read_bytes()).hexdigest()}
    (D / "minta.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(man, len(k2), m["kontroll2"]["sha256"])


def valaszt3(a) -> None:
    """A közös kontroll: a `kontroll` és a `kontroll2` mintán kívülről (azokat a v2 fejlesztése már látta), a hibás
    mintát nem kizárva, vagyis a v1 hibái a természetes arányukban vannak benne; egy harmadik hash-sorrendben."""
    regi = set()
    for m in ("kontroll", "kontroll2"):
        regi |= set((D / f"{m}.txt").read_text(encoding="utf-8").split())
    hibas = set((D / "hibas.txt").read_text(encoding="utf-8").split())
    k3, man = [], {}
    for src in FORRASOK:
        for fam in (L.BANK, L.SZAB):
            ids = [it["id"] for _, it in L.betolt(src, fam) if it["id"] not in regi]
            ids.sort(key=lambda i: hashlib.sha256(f"{SEED}c:{i}".encode()).hexdigest())
            k3 += ids[:KONTROLL]
            man[f"{src}|{fam}"] = {"n": len(ids[:KONTROLL]), "ebből a hibás mintából": len(set(ids[:KONTROLL]) & hibas)}
    (D / "kozos.txt").write_text("\n".join(k3) + "\n", encoding="utf-8")
    m = json.loads((D / "minta.json").read_text(encoding="utf-8"))
    m["kozos"] = {"cellak": man, "seed": f"{SEED}c", "sha256": hashlib.sha256((D / "kozos.txt").read_bytes()).hexdigest()}
    (D / "minta.json").write_text(json.dumps(m, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False), len(k3), m["kozos"]["sha256"])


def _helyes(x: dict, xo: dict) -> bool:
    return x["kimenet"] != "emberhez" and G.kulcs(x) == G.kulcs(xo)


def kozos(a) -> None:
    """A „korábban helyes” a v1 menet (G1a) kinyerése a mostani lánckóddal és a megadott blokkal, ugyanúgy, mint a két
    friss kinyerés; a mérce mindháromnál az orákulum-út lánca."""
    ids = set((D / "kozos.txt").read_text(encoding="utf-8").split())
    hibas = set((D / "hibas.txt").read_text(encoding="utf-8").split())
    utak = {"v1 újra": _ut(a.v1_ujra), "v2": _ut(a.v2)}
    res: dict = {}
    tot = Counter()
    for src in FORRASOK:
        for fam in (L.BANK, L.SZAB):
            parok = [(p, it) for p, it in L.betolt(src, fam) if it["id"] in ids]
            r0 = _lanc(src, fam, "kinyert", parok, valtozat=a.blokk)
            ro = _lanc(src, fam, "orakulum", parok, valtozat=a.blokk)
            uj = {}
            for nev, d in utak.items():
                kin = {r["id"]: r["mezok"] for r in L.jsonl(d / f"{src}_{fam}.jsonl") if r["id"] in ids}
                hiany = len(parok) - len(kin)
                if hiany:
                    raise SystemExit(f"{nev} {src} {fam}: {hiany} item kinyerése hiányzik")
                uj[nev] = _lanc(src, fam, "kinyert", parok, kin=kin, valtozat=a.blokk)
            c = Counter()
            for j, (_, it) in enumerate(parok):
                resz = "a hibás mintából" if it["id"] in hibas else "friss"
                h0 = _helyes(r0[j], ro[j])
                g = it["gold"]
                for nev in ("v1 eredeti", *utak):
                    x = r0[j] if nev == "v1 eredeti" else uj[nev][j]
                    h = _helyes(x, ro[j])
                    for rr in (resz, "összesen"):
                        c[f"{rr}|{nev}|n"] += 1
                        c[f"{rr}|{nev}|helyes"] += h
                        c[f"{rr}|{nev}|elromlott"] += h0 and not h
                        c[f"{rr}|{nev}|javult"] += (not h0) and h
                        c[f"{rr}|{nev}|emberhez"] += x["kimenet"] == "emberhez"
                        c[f"{rr}|{nev}|hamis kizárás"] += bool(g) and x["kimenet"] != "emberhez" and g not in x["megmaradt"]
                        c[f"{rr}|{nev}|hamis kötés"] += x["kimenet"] == "kotes" and x["kotes"] != g
                h1, h2 = _helyes(uj["v1 újra"][j], ro[j]), _helyes(uj["v2"][j], ro[j])
                c["összesen|csak a v1 újra helyes"] += h1 and not h2
                c["összesen|csak a v2 helyes"] += h2 and not h1
            res[f"{src}|{fam}"] = dict(c)
            tot.update(c)
    out = EXP / "kor08/eredmenyek/G1"
    (out / f"{a.nev}.json").write_text(json.dumps({"cellak": res, "osszesen": dict(tot), "blokk": a.blokk},
                                                  ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sor = ["# G1 — közös kontroll: a két séma friss kinyerése ugyanazon a mintán", "",
           f"A minta a futás előtt kijelölve (`kor08/adat/G1/kin2_proba/kozos.txt`, `minta.json`): cellánként {KONTROLL} item",
           "a bank- és a szabálycsaládon, a két korábbi kontrollmintán kívülről, a helyességre szűrés nélkül. Mindhárom",
           f"kinyerés ugyanazzal a lánckóddal és blokkal ({a.blokk}) megy. „Helyes”: a lánc kimenete (kimenet, megmaradt",
           "jelöltek, kötés, blokk) egyezik az orákulum-útéval, és nem emberhez ment. „Elromlott” és „javult” a v1 menet",
           "(G1a) kinyeréséhez képest. A „hibás mintából” sor itemjein fejlesztettük a v2-t.", "",
           "| cella | rész | kinyerés | n | helyes | elromlott | javult | emberhez | hamis kizárás / kötés |",
           "|---|---|---|---|---|---|---|---|---|"]

    def sorok(cel: str, c: Counter | dict) -> None:
        for rr in ("friss", "a hibás mintából", "összesen"):
            for nev in ("v1 eredeti", *utak):
                n = c.get(f"{rr}|{nev}|n", 0)
                if not n:
                    continue
                k = lambda x: c.get(f"{rr}|{nev}|{x}", 0)  # noqa: E731
                el = "– | –" if nev == "v1 eredeti" else f"{k('elromlott')} | {k('javult')}"
                sor.append(f"| {cel} | {rr} | {nev} | {n} | {k('helyes')} | {el} | {k('emberhez')} | "
                           f"{k('hamis kizárás')} / {k('hamis kötés')} |")

    for cel, c in res.items():
        sorok(cel, c)
    sorok("**összesen**", tot)
    sor += ["", f"A két friss kinyerés közvetlenül: csak a v1 újra helyes {tot['összesen|csak a v1 újra helyes']}, "
                f"csak a v2 helyes {tot['összesen|csak a v2 helyes']} itemen.",
            "", "Leíró mérés: a v1 újrafuttatásának zaja összehasonlítási alap, nem elfogadható hibakeret (Dani, 11-02)."]
    (out / f"{a.nev}.md").write_text("\n".join(sor) + "\n", encoding="utf-8")
    print("\n".join(sor))


def _ut(x: str) -> Path:
    return Path(x) if Path(x).is_absolute() else EXP / x


def _lanc(src: str, fam: str, ut: str, parok: list, kin: dict | None = None, valtozat: str = "v0") -> list[dict]:
    """A lánc teljes kimenete (a blokkal) itemenként; a v1 kinyert úthoz a G1 mezőfájljából."""
    if ut == "kinyert" and kin is None:
        kin = {r["id"]: r["mezok"] for r in L.jsonl(G1 / "kinyeres" / f"{src}_{fam}.mezok.jsonl")}
    kin = kin or {}
    out = []
    for p, it in parok:
        mez = L.orakulum(fam, p, it) if ut == "orakulum" else kin.get(it["id"])
        out.append(L.lanc(fam, it, mez, ures="modell", valtozat=valtozat))
    return out


def osszevet(a) -> None:
    minta = {m: set((D / f"{m}.txt").read_text(encoding="utf-8").split()) for m in ("hibas", "kontroll", "kontroll2")
             if (D / f"{m}.txt").exists()}
    kd = Path(a.kinyeres) if Path(a.kinyeres).is_absolute() else EXP / a.kinyeres
    ud = (Path(a.v1_ujra) if Path(a.v1_ujra).is_absolute() else EXP / a.v1_ujra) if a.v1_ujra else None
    res: dict = {}
    for src in FORRASOK:
        for fam in L.CSALADOK:
            f2 = kd / f"{src}_{fam}.jsonl"
            if not f2.exists():
                continue
            v2 = {r["id"]: r["mezok"] for r in L.jsonl(f2)}
            parok = [(p, it) for p, it in L.betolt(src, fam) if it["id"] in v2]
            r1 = _lanc(src, fam, "kinyert", parok)
            r2 = _lanc(src, fam, "kinyert", parok, kin=v2)
            ro = _lanc(src, fam, "orakulum", parok)
            fu = ud / f"{src}_{fam}.jsonl" if ud else None
            vu = {r["id"]: r["mezok"] for r in L.jsonl(fu)} if fu and fu.exists() else {}
            c = Counter()
            for (_, it), x1, x2, xo in zip(parok, r1, r2, ro):
                m = next((k for k, v in minta.items() if it["id"] in v), None)
                if m is None:
                    continue
                e1 = x1["kimenet"] != "emberhez" and G.kulcs(x1) == G.kulcs(xo)
                e2 = x2["kimenet"] != "emberhez" and G.kulcs(x2) == G.kulcs(xo)
                if it["id"] in vu:  # a v1 újrafuttatása ugyanazon a példányon: a zajszint
                    xu = L.lanc(fam, it, vu[it["id"]], ures="modell")
                    eu = xu["kimenet"] != "emberhez" and G.kulcs(xu) == G.kulcs(xo)
                    c[f"{m}|v1 újra n"] += 1
                    c[f"{m}|v1 újra elromlott"] += e1 and not eu
                c[f"{m}|n"] += 1
                c[f"{m}|v1 = orákulum"] += e1
                c[f"{m}|v2 = orákulum"] += e2
                c[f"{m}|javult"] += (not e1) and e2
                c[f"{m}|elromlott"] += e1 and not e2
                c[f"{m}|v1 emberhez"] += x1["kimenet"] == "emberhez"
                c[f"{m}|v2 emberhez"] += x2["kimenet"] == "emberhez"
                c[f"{m}|v2 nem értelmezhető"] += v2[it["id"]] is None
                g = it["gold"]
                c[f"{m}|v2 hamis kizárás"] += bool(g) and x2["kimenet"] != "emberhez" and g not in x2["megmaradt"]
                c[f"{m}|v2 hamis kötés"] += x2["kimenet"] == "kotes" and x2["kotes"] != g
            res[f"{src}|{fam}"] = dict(c)
    out = EXP / "kor08/eredmenyek/G1"
    (out / f"{a.nev}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sor = ["# G1 — a kinyerés javításának célzott próbája (séma v2), a lánc szintjén", "",
           "„= orákulum”: a lánc kimenete (kimenet, megmaradt jelöltek, kötés, blokk) egyezik az orákulum-útéval, és nem",
           "emberhez ment. A minták a futás előtt kijelölve (`kor08/adat/G1/kin2_proba/minta.json`).", "",
           "| cella | minta | n | v1 = orákulum | v2 = orákulum | javult | elromlott | emberhez v1 → v2 | hamis kizárás / kötés (v2) |",
           "|---|---|---|---|---|---|---|---|---|"]
    tot = Counter()
    for cel, c in res.items():
        for m in minta:
            if not c.get(f"{m}|n"):
                continue
            for k, v in c.items():
                if k.startswith(m + "|"):
                    tot[k] += v
            sor.append(f"| {cel} | {m} | {c[m + '|n']} | {c[m + '|v1 = orákulum']} | {c[m + '|v2 = orákulum']} | "
                       f"{c[m + '|javult']} | {c[m + '|elromlott']} | {c[m + '|v1 emberhez']} → {c[m + '|v2 emberhez']} | "
                       f"{c[m + '|v2 hamis kizárás']} / {c[m + '|v2 hamis kötés']} |")
    for m in minta:
        sor.append(f"| **összesen** | {m} | {tot[m + '|n']} | {tot[m + '|v1 = orákulum']} | {tot[m + '|v2 = orákulum']} | "
                   f"{tot[m + '|javult']} | {tot[m + '|elromlott']} | {tot[m + '|v1 emberhez']} → {tot[m + '|v2 emberhez']} | "
                   f"{tot[m + '|v2 hamis kizárás']} / {tot[m + '|v2 hamis kötés']} |")
    if any(tot[f"{m}|v1 újra n"] for m in minta):
        sor += ["", "## Zajszint: a v1 újrafuttatása ugyanazon a vLLM-példányon (a kontrollmintákon)", ""]
        for m in minta:
            if tot[f"{m}|v1 újra n"]:
                sor.append(f"- {m}: a v1 újra {tot[m + '|v1 újra elromlott']} / {tot[m + '|v1 újra n']} itemen tér el az "
                           f"orákulumtól (a v2: {tot[m + '|elromlott']} / {tot[m + '|n']})")
    k3 = res.get(f"K3diag|{L.SZAB}", {})
    k3_1 = k3.get("hibas|n", 0) - k3.get("hibas|v1 = orákulum", 0)
    k3_2 = k3.get("hibas|n", 0) - k3.get("hibas|v2 = orákulum", 0)
    km = a.kontroll
    kn = tot[f"{km}|n"]
    siker = {"hibas: javult − elromlott > 0": tot["hibas|javult"] - tot["hibas|elromlott"] > 0,
             "K3 diag szabály: eltérés + emberhez legalább a felére": k3_2 * 2 <= k3_1,
             f"{km}: új eltérés ≤ 1%": kn > 0 and tot[f"{km}|elromlott"] <= 0.01 * kn,
             "hamis kizárás és kötés 0": all(tot[f"{m}|v2 hamis {x}"] == 0 for m in minta for x in ("kizárás", "kötés"))}
    sor += ["", "## Az előre rögzített siker", ""] + [f"- {k}: **{'igen' if v else 'nem'}**" for k, v in siker.items()]
    sor += ["", f"K3 diag szabálycsalád, a hibás mintán az orákulumtól eltérő vagy emberhez küldött itemek: v1 {k3_1}, v2 {k3_2}."]
    (out / f"{a.nev}.md").write_text("\n".join(sor) + "\n", encoding="utf-8")
    print("\n".join(sor))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("valaszt")
    o = sub.add_parser("osszevet")
    o.add_argument("--kinyeres", required=True)
    o.add_argument("--nev", default="kin2_proba")  # a kimenet neve a `kor08/eredmenyek/G1` alatt
    o.add_argument("--v1-ujra")  # a v1 újrafuttatásának kinyerései (zajszint)
    o.add_argument("--kontroll", default="kontroll")  # melyik kontrollmintán áll a siker feltétele
    sub.add_parser("valaszt2")
    sub.add_parser("valaszt3")
    k = sub.add_parser("kozos")
    k.add_argument("--v1-ujra", required=True)  # a v1 séma friss kinyerése a közös kontrollon
    k.add_argument("--v2", required=True)  # a v2 séma kinyerése (a teljes újrafuttatásé)
    k.add_argument("--blokk", default="v1", choices=L.BLOKK_VALTOZAT)
    k.add_argument("--nev", default="kin2_kozos")
    a = ap.parse_args()
    {"valaszt": valaszt, "valaszt2": valaszt2, "valaszt3": valaszt3, "osszevet": osszevet, "kozos": kozos}[a.cmd](a)


if __name__ == "__main__":
    main()
