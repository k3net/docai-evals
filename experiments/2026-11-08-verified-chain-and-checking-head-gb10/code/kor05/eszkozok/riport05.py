"""05-ös kör — a 05a gépi eredménylapja (05-runbook 8.2–8.3; v1a-vazlat 4.) az `elemzes05` kimenetéből.

  python3 kor05/eszkozok/riport05.py          → kor05/eredmenyek/F3/v1a/eredmenylap_gepi.md + itelet05.json

Bemenet (a `k05a_elemzes_lanc.sh` kimenetei): F3/v1a (szigorú helyesség, az ítélet), F3/v1a_t-hu-maradek (leíró réteg,
JEV nélkül), F3/v1a_enyhe (enyhe helyesség, leíró), és a kor05/rogzites/v1a/ROGZITES.json. Csak a standard könyvtár.

Ítélet:
  S3, S5  az `elemzes05` D1 (b) ítélete változatlanul (a ΔAURC S+N CI-je 0 alatt, az X kar S+N precizitása a saját
          τ-jánál ≥ 0,93, ha van munkapontja, az MTX nem szignifikánsan nagyobb; legalább két szűrőrétegen). Az S3 és az
          S5 külön ítéletet kap („T nélkül továbblép” / „csak T-vel továbblép”); a 05b-kapu nyitva, ha legalább egy
          kontraszt továbblép.
  H6      a 04 5.1 kategóriái a ΔAURC (S+N) elsődleges végponttal (v1a D5), rétegenként és referenciánként, ebben a
          sorrendben:
            „JEV jobb”       a ΔAURC Holm után (2 × 3) szignifikánsan negatív, a JEV-a S+N precizitása ≥ 0,93 (ha van
                             munkapontja), és a ΔMTX nem szignifikánsan nagyobb;
            „nem teljesíti”  a ΔAURC pontbecslése negatív, de a precizitás- vagy az MTX-feltétel bukik;
            „JEV rosszabb”   a ΔAURC 95%-os CI-je 0 fölött. A 04 két ága (az elsődleges végpont szignifikánsan rossz,
                             vagy az AURC-feltétel szignifikánsan rossz nem szignifikáns javulás mellett) azonos
                             végponton ebbe esik össze; a feltétel a 04 szerint Holm nélküli;
            egyébként        „nem eldönthető”.
          Az AURC-feltétel („nem szignifikánsan rosszabb”) a negatív pontbecslésnél mindig teljesül, ezért a két első
          kategóriában csak a precizitás és az MTX dönt. A HO-routing-hu érzékenységi réteg: ugyanez Holm nélkül.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[1]
F3 = EXP / "kor05/eredmenyek/F3"
ROGZITES = EXP / "kor05/rogzites/v1a/ROGZITES.json"

SZURO = ("teszt:ho-termek", "teszt:ho-routing", "teszt:ho-uj")
ERZEKENY = "teszt:ho-routing-hu"
RETEG_NEV = {"teszt:ho-termek": "HO-termék", "teszt:ho-routing": "HO-routing", "teszt:ho-uj": "HO-új",
             "teszt:ho-routing-hu": "HO-routing-hu", "leiro:t-hu-maradek": "T-hu-maradék"}
SZURO_KONTR = (("S3", "H-B1"), ("S5", "H-T-meta~B1-T"), ("S5", "H-T-kal~B1-T"))
H6_KONTR = ("JEV-a~L1v", "JEV-a~G3")
LEIRO_KONTR = (("S1", "H-C"), ("S2", "A-H"), ("S4", "H-HX"), ("—", "JEV-a~B1"), ("—", "JEV-b~L1v"))
KIEMELT_CSALAD = ("kie.osszeg",)  # 05-runbook 8.1: a HO-új kie.osszeg családja külön sorban
ALFA = 0.05
BUKAS = 0.93
FELTETEL = {"delta_aurc_negativ": "a ΔAURC CI-je nem 0 alatt", "precizitas_legalabb_093": "precizitás < 0,93",
            "mtx_nem_nagyobb": "az MTX szignifikánsan nagyobb"}


def pair(c: str) -> tuple[str, str]:
    x, y = c.split("~") if "~" in c else c.split("-", 1)
    return x, y


def knev(c: str) -> str:
    return " − ".join(pair(c))


def rnev(r: str) -> str:
    return RETEG_NEV.get(r, r)


def szam(x, d: int = 3) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:.{d}f}".replace(".", ",").replace("-", "−")


def pval(p) -> str:
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "–"
    return "< 0,0001" if p < 1e-4 else szam(p, 4)


def ci(b: dict, d: int = 4) -> str:
    if not b or not b.get("reps"):
        return "–"
    return f"[{szam(b['ci95'][0], d)}; {szam(b['ci95'][1], d)}]"


def atlag(res: dict, reteg: str, kar: str, m: str):
    return res["pont"][reteg]["karok"][kar]["atlag"].get(m)


def delta(res: dict, reteg: str, c: str, m: str):
    x, y = pair(c)
    a, b = atlag(res, reteg, x, m), atlag(res, reteg, y, m)
    return None if a is None or b is None else a - b


def munkapont(res: dict, reteg: str, kar: str) -> str:
    mp = res["pont"][reteg]["karok"][kar]["munkapont_seedenkent"]
    return f"{sum(mp)}/{len(mp)}" if len(mp) > 1 else ("van" if mp[0] else "nincs")


def betolt(p: Path) -> dict | None:
    f = p / "elemzes05.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def ismetles(res: dict) -> int:
    return max((v.get("reps", 0) for b in res["bootstrap"].values() for v in b.values()), default=0)


def kontraszt_tabla(res: dict, c: str, retegek: list[str]) -> list[str]:
    x = pair(c)[0]
    v = res["kontrasztok"][c]
    out = ["| réteg | D1 (b) | ΔAURC S+N [CI] | p | Holm-p | " + x + " S+N prec. | munkapont | ΔMTX [CI] | "
           "Δ SEL-lef@95 [CI] (leíró) |", "|---|---|---|---|---|---|---|---|---|"]
    for r in retegek:
        ok, b = v["retegenkent"][r], res["bootstrap"][r]
        au = b[f"{c}|aurc_sn"]
        out.append(f"| {rnev(r)}{'' if r in SZURO else ' (leíró)'} | {'teljesül' if ok['teljesul'] else 'nem'} | "
                   f"{szam(delta(res, r, c, 'aurc_sn'), 4)} {ci(au)} | {pval(au.get('p'))} | "
                   f"{pval(v['holm_p_aurc_sn'].get(r))} | {szam(atlag(res, r, x, 'sn_prec'))} | "
                   f"{munkapont(res, r, x)} | {szam(delta(res, r, c, 'mtx'))} {ci(b[f'{c}|mtx'], 3)} | "
                   f"{szam(delta(res, r, c, 'sel_lef'))} {ci(b[f'{c}|sel_lef'], 3)} |")
    okok = [f"- {rnev(r)}: " + "; ".join(FELTETEL[k] for k in FELTETEL if not v["retegenkent"][r][k])
            for r in retegek if not v["retegenkent"][r]["teljesul"]]
    return out + ([""] + okok if okok else [])


def h6_itelet(res: dict, reteg: str, c: str, holm_p) -> tuple[str, list[str]]:
    ok, b = res["kontrasztok"][c]["retegenkent"][reteg], res["bootstrap"][reteg]
    d = delta(res, reteg, c, "aurc_sn")
    au = b[f"{c}|aurc_sn"]
    felt = [FELTETEL[k] for k in ("precizitas_legalabb_093", "mtx_nem_nagyobb") if not ok[k]]
    sig = holm_p is not None and not math.isnan(holm_p) and holm_p < ALFA
    if d is not None and d < 0 and sig and not felt:
        return "JEV jobb", []
    if d is not None and d < 0 and felt:
        return "nem teljesíti", felt
    if au.get("reps") and au["ci95"][0] > 0:
        return "JEV rosszabb", ["a ΔAURC CI-je 0 fölött"]
    return "nem eldönthető", felt


def h6_tabla(res: dict, retegek: list[str], holm: bool) -> tuple[list[str], dict]:
    out = ["| réteg | referencia | ítélet | ΔAURC S+N [CI] | " + ("Holm-p (2 × 3)" if holm else "p (Holm nélkül)") +
           " | JEV-a S+N prec. | ΔMTX [CI] | Δ SEL-lef@95 [CI] (leíró) |", "|---|---|---|---|---|---|---|---|"]
    it, okok = {}, []
    for r in retegek:
        for c in H6_KONTR:
            b = res["bootstrap"][r]
            au = b[f"{c}|aurc_sn"]
            p = res.get("h6_holm_aurc_sn", {}).get(f"{c}|{r}") if holm else au.get("p")
            v, why = h6_itelet(res, r, c, p)
            it.setdefault(r, {})[pair(c)[1]] = v
            out.append(f"| {rnev(r)} | {pair(c)[1]} | **{v}** | {szam(delta(res, r, c, 'aurc_sn'), 4)} {ci(au)} | "
                       f"{pval(p)} | {szam(atlag(res, r, 'JEV-a', 'sn_prec'))} | "
                       f"{szam(delta(res, r, c, 'mtx'))} {ci(b[f'{c}|mtx'], 3)} | "
                       f"{szam(delta(res, r, c, 'sel_lef'))} {ci(b[f'{c}|sel_lef'], 3)} |")
            if why:
                okok.append(f"- {rnev(r)}, {pair(c)[1]}: " + "; ".join(why))
    return out + ([""] + okok if okok else []), it


def kar_tabla(res: dict, reteg: str) -> list[str]:
    out = ["| kar | τ-szelet | munkapont | SEL lef | SEL prec | S+N lef | S+N prec | MTX | hamis SEL (NM) | "
           "hamis NONE | AURC S+N | AURC (03) | DEFER | lef@p95 SEL |", "|---|---|---|---|---|---|---|---|---|---|---|---|"
           "---|---|"]
    for kar, v in res["pont"][reteg]["karok"].items():
        m = v["atlag"]
        out.append(f"| {kar} | {v['tau_szelet']} | {munkapont(res, reteg, kar)} | {szam(m['sel_lef'])} | "
                   f"{szam(m['sel_prec'])} | {szam(m['sn_lef'])} | {szam(m['sn_prec'])} | {szam(m['mtx'])} | "
                   f"{szam(m['hamis_sel_nm'])} | {szam(m['hamis_none'])} | {szam(m['aurc_sn'], 4)} | "
                   f"{szam(m['aurc_sn_03'], 4)} | {szam(m['defer_arany'])} | {szam(m['lef_p95_sel'])} |")
    return out


def leiro_tabla(res: dict, kontr, retegek: list[str]) -> list[str]:
    out = ["| | kontraszt | réteg | D1 (b) | ΔAURC S+N [CI] | p | ΔMTX [CI] | Δ SEL-lef@95 [CI] |",
           "|---|---|---|---|---|---|---|---|"]
    for nev, c in kontr:
        if c not in res["kontrasztok"]:
            continue
        for r in retegek:
            ok, b = res["kontrasztok"][c]["retegenkent"][r], res["bootstrap"][r]
            au = b[f"{c}|aurc_sn"]
            out.append(f"| {nev} | {knev(c)} | {rnev(r)} | {'teljesül' if ok['teljesul'] else 'nem'} | "
                       f"{szam(delta(res, r, c, 'aurc_sn'), 4)} {ci(au)} | {pval(au.get('p'))} | "
                       f"{szam(delta(res, r, c, 'mtx'))} {ci(b[f'{c}|mtx'], 3)} | "
                       f"{szam(delta(res, r, c, 'sel_lef'))} {ci(b[f'{c}|sel_lef'], 3)} |")
    return out


def csalad_tabla(res: dict) -> list[str]:
    out = []
    for r, blk in res["pont"].items():
        for f, v in sorted(blk["csaladonkent"].items()):
            if not any(k in f for k in KIEMELT_CSALAD):
                continue
            if not out:
                out = ["| réteg | család | n | kar | S+N lef | S+N prec | AURC S+N |", "|---|---|---|---|---|---|---|"]
            for kar in ("H", "B1", "C", "JEV-a", "L1v", "G3"):
                if kar in v:
                    m = v[kar]
                    out.append(f"| {rnev(r)} | {f} | {v['n']} | {kar} | {szam(m['sn_lef'])} | {szam(m['sn_prec'])} | "
                               f"{szam(m['aurc_sn'], 4)} |")
    return out or ["(a kiemelt család egyik rétegen sem szerepel)"]


def lap(sz: dict, leiro: dict | None, enyhe: dict | None, rog: dict | None) -> tuple[str, dict]:
    retegek = list(sz["retegek"])
    szuro = [r for r in SZURO if r in retegek]
    L = ["# 05a — gépi eredménylap (v1a)", ""]
    if rog:
        L += [f"Rögzítve: {rog['rogzitve']} ({rog['jovahagyas']}). A `MANIFEST.sha256` hash-e: "
              f"`{rog['manifest_sha256']}`.", ""]
    L += [f"Bootstrap: {ismetles(sz)} ismétlés. Helyesség: {sz['helyesseg']} (az ítélet a szigorún). Rétegek: " +
          ", ".join(f"{rnev(r)} (n = {n})" for r, n in sz["retegek"].items()) + "; τ-szeletek: " +
          ", ".join(f"{k} ({n})" for k, n in sz["tau_szeletek"].items()) + ".",
          "", "Minden előre rögzített kontraszt szerepel, a negatív és a nem eldönthető eredmény is. Az értelmezés "
          "külön, kézzel írt szakaszba kerül.", ""]
    itelet = {"helyesseg": sz["helyesseg"]}

    # 05a szűrő
    L += ["## 05a szűrő — S3 és S5 (D1 b)", ""]
    for nev, c in SZURO_KONTR:
        v = sz["kontrasztok"][c]
        n_ok = sum(v["retegenkent"][r]["teljesul"] for r in szuro)
        L += [f"### {nev}: {knev(c)} — **{v['itelet']}** (teljesül: {n_ok}/{len(szuro)} szűrőrétegen)", ""]
        L += kontraszt_tabla(sz, c, retegek) + [""]
        itelet[c] = {"itelet": v["itelet"], "teljesul_retegek": [r for r in szuro if v["retegenkent"][r]["teljesul"]]}
    s3 = sz["kontrasztok"]["H-B1"]["itelet"] == "továbblép"
    s5 = [c for _, c in SZURO_KONTR[1:] if sz["kontrasztok"][c]["itelet"] == "továbblép"]
    if len(szuro) == 3:
        osszeg = "T nélkül továbblép" if s3 else ("csak T-vel továbblép" if s5 else "nem lép tovább")
        itelet |= {"S3_S5": osszeg, "kapu_05b": bool(s3 or s5)}
        L += [f"**Összegzés:** {osszeg}" + (f" ({', '.join(knev(c) for c in s5)})" if s5 and not s3 else "") +
              f". A 05b-kapu {'nyitva' if s3 or s5 else 'zárva: a 05 a 05a-val lezárul (8.2)'}.", ""]
    else:
        L += ["**Összegzés:** nem a három szűrőrétegen futott (próba); ítélet nincs.", ""]
    L += ["A Holm-p a három szűrőréteg p-értékein leíró; az ítéletszabály a „legalább kettő a háromból” (v1a 3.). "
          "Az S5 T-kal változata az AURC-ban azonos az S3-mal (a Platt monoton, a τ nem hat az AURC-ra): saját "
          "hozzájárulása csak a precizitás- és a munkapont-feltételben van.", ""]

    # H6
    L += ["## H6 — JEV-35B (megerősítő; 04 5.1 kategóriák, ΔAURC S+N elsődleges, v1a D5)", ""]
    if all(c in sz["kontrasztok"] for c in H6_KONTR) and szuro:
        t, it = h6_tabla(sz, szuro, holm=True)
        L += t + [""]
        itelet["H6"] = it
        if ERZEKENY in retegek:
            t, it = h6_tabla(sz, [ERZEKENY], holm=False)
            L += ["Érzékenység (HO-routing-hu, a szennyezés miatt; Holm nélkül):", ""] + t + [""]
            itelet["H6_erzekenyseg"] = it
        L += ["A „nem teljesíti”-hez elég a negatív pontbecslés bukó feltétellel; a „JEV rosszabb” a Holm nélküli CI-n "
              "dől el (a 04 feltételei nem Holm-családban). A modul fejkommentje a kategóriák pontos sorrendjét adja.",
              ""]
    else:
        L += ["(a H6 kontrasztjai nem futottak ezen a kimeneten)", ""]

    # leíró
    L += ["## Leíró kontrasztok (S1, S2, S4, JEV-a − B1, JEV-b − L1v)", ""] + leiro_tabla(sz, LEIRO_KONTR, retegek) + [""]

    L += ["## Karok rétegenként (pontbecslés a τ-nál; a fejeknél és a G3-nál a seedek átlaga)", ""]
    for r in retegek:
        L += [f"### {rnev(r)} (n = {sz['retegek'][r]})", ""] + kar_tabla(sz, r) + [""]

    L += ["## Kiemelt családok (8.1)", ""] + csalad_tabla(sz) + [""]

    if leiro:
        lr = list(leiro["retegek"])
        L += ["## T-hu-maradék (leíró réteg, JEV nélkül)", ""]
        L += leiro_tabla(leiro, [(n, c) for n, c in (*SZURO_KONTR, *LEIRO_KONTR)], lr) + [""]
        for r in lr:
            L += [f"### {rnev(r)} (n = {leiro['retegek'][r]})", ""] + kar_tabla(leiro, r) + [""]
    else:
        L += ["## T-hu-maradék", "", "(nincs meg a kimenet)", ""]

    if enyhe:
        L += ["## Enyhe helyesség (leíró: a NONE minden nem-MATCH állapoton helyes)", ""]
        L += ["| kontraszt | ítélet (D1 b, leíró) | " + " | ".join(f"ΔAURC {rnev(r)}" for r in retegek) + " |",
              "|---|---|" + "---|" * len(retegek)]
        for _, c in (*SZURO_KONTR, *LEIRO_KONTR, ("H6", H6_KONTR[0]), ("H6", H6_KONTR[1])):
            if c in enyhe["kontrasztok"]:
                v = enyhe["kontrasztok"][c]
                L.append(f"| {knev(c)} | {v['itelet']} | " + " | ".join(
                    f"{szam(delta(enyhe, r, c, 'aurc_sn'), 4)} {ci(enyhe['bootstrap'][r][f'{c}|aurc_sn'])}"
                    + ("" if v["retegenkent"][r]["teljesul"] else " ✗") for r in retegek) + " |")
        L += ["", "✗: a D1 (b) feltétele azon a rétegen nem teljesül.", ""]
    else:
        L += ["## Enyhe helyesség", "", "(nincs meg a kimenet)", ""]

    L += ["## Tudott gyengeségek (a rögzítés változatlanul hagyta; v1a-vazlat 4.)", "",
          "- **Az MTX-őr gyenge.** Az MTX a τ-nál mérődik, így a τ-zajt örökli: egy replikában munkapont nélkül 0, "
          "ezért ritkán bukik. A τ-tól független kiegészítés (az elfogadott SELECT-ek nem-MATCH aránya az AURC-görbe "
          "mentén, családonként) leíró, külön készül.",
          "- **Az S5 T-kal változata az AURC-ban azonos az S3-mal**; az érdemi célcsalád-változat a T-meta.", ""]
    return "\n".join(L) + "\n", itelet


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--szigoru", default=str(F3 / "v1a"))
    ap.add_argument("--leiro", default=str(F3 / "v1a_t-hu-maradek"))
    ap.add_argument("--enyhe", default=str(F3 / "v1a_enyhe"))
    ap.add_argument("--out", default=str(F3 / "v1a"))
    a = ap.parse_args()
    sz = betolt(Path(a.szigoru))
    if sz is None:
        raise SystemExit(f"hiányzik: {a.szigoru}/elemzes05.json")
    rog = json.loads(ROGZITES.read_text(encoding="utf-8")) if ROGZITES.exists() else None
    md, itelet = lap(sz, betolt(Path(a.leiro)), betolt(Path(a.enyhe)), rog)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "eredmenylap_gepi.md").write_text(md, encoding="utf-8")
    (out / "itelet05.json").write_text(json.dumps(itelet, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(itelet, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
