#!/usr/bin/env python3
"""D3 — számlacsomag generálása. Minden összeg SZÁMOLT; a beépített hiba is számolt eltérés.

Áfa-rezsimek a korpuszban: 27 % · 5 % · AAM (alanyi adómentes) · fordított adózás.
⛔ A végszámlán a feltüntetett fizetendő végösszeg SZÁNDÉKOSAN HIBAS_ELTERES-sel több.
"""
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

D = Decimal
HIBAS_ELTERES = D("27000")          # T5: ennyivel több van feltüntetve a végszámlán

def ft(x: Decimal, tizedes=False) -> str:
    """magyar formátum: szóközös ezres tagolás, tizedesvessző"""
    q = x.quantize(D("0.01") if tizedes else D("1"), rounding=ROUND_HALF_UP)
    egesz, _, tort = str(abs(q)).partition(".")
    s = f"{int(egesz):,}".replace(",", " ")
    if tizedes:
        s += "," + (tort or "00").ljust(2, "0")
    return ("-" if q < 0 else "") + s

def afa(netto: D, kulcs) -> D:
    if not isinstance(kulcs, D):
        return D("0")
    return (netto * kulcs / 100).quantize(D("0.01"), rounding=ROUND_HALF_UP)

class Tetel:
    def __init__(s, nev, mennyiseg, egyseg, egysegar, kulcs, jogcim=None):
        s.nev, s.mennyiseg, s.egyseg, s.egysegar = nev, D(mennyiseg), egyseg, D(egysegar)
        s.kulcs, s.jogcim = kulcs, jogcim
        s.netto = (s.mennyiseg * s.egysegar).quantize(D("0.01"), rounding=ROUND_HALF_UP)
        s.afa = afa(s.netto, kulcs)
        s.brutto = s.netto + s.afa
    @property
    def kulcs_szoveg(s):
        return f"{s.kulcs}%" if isinstance(s.kulcs, D) else s.jogcim

def szamla(szam, tipus, kelt, teljesites, fizetesi_hatarido, tetelek, elolegbetudas=None,
           feltuntetett_fizetendo=None, megjegyzes=""):
    netto = sum((t.netto for t in tetelek), D("0"))
    afaossz = sum((t.afa for t in tetelek), D("0"))
    brutto = netto + afaossz
    fizetendo = brutto - (elolegbetudas or D("0"))
    kiirt = feltuntetett_fizetendo if feltuntetett_fizetendo is not None else fizetendo
    L = []
    A = L.append
    A(f"## {tipus.upper()}\n")
    A(f"**Számla sorszáma:** {szam}  ")
    A(f"**Számla kelte:** {kelt}  ")
    A(f"**Teljesítés időpontja:** {teljesites}  ")
    A(f"**Fizetési határidő:** {fizetesi_hatarido}  ")
    A(f"**Fizetési mód:** átutalás\n")
    A("**Szállító:** Hegyi és Társa Építőipari Bt. · 7634 Pécs, Nagy Imre út 8. · adószám: 31415929-1-02  ")
    A("**Vevő:** Delta-Ipari Szolgáltató Zrt. · 1095 Budapest, Soroksári út 30–34. · adószám: 24681353-2-43\n")
    A("| # | Megnevezés | Mennyiség | Egység | Egységár (Ft) | Nettó (Ft) | Áfakulcs | Áfa (Ft) | Bruttó (Ft) |")
    A("|---|---|---:|---|---:|---:|---|---:|---:|")
    for i, t in enumerate(tetelek, 1):
        A(f"| {i} | {t.nev} | {ft(t.mennyiseg, t.mennyiseg % 1 != 0)} | {t.egyseg} | "
          f"{ft(t.egysegar, t.egysegar % 1 != 0)} | {ft(t.netto)} | {t.kulcs_szoveg} | "
          f"{ft(t.afa)} | {ft(t.brutto)} |")
    A("")
    A(f"**Nettó összesen:** {ft(netto)} Ft  ")
    A(f"**Áfa összesen:** {ft(afaossz)} Ft  ")
    A(f"**Bruttó összesen:** {ft(brutto)} Ft  ")
    if elolegbetudas:
        A(f"**Levonandó előleg (SZ-2026/0417 bruttó):** {ft(elolegbetudas)} Ft  ")
    A(f"**FIZETENDŐ VÉGÖSSZEG:** **{ft(kiirt)} Ft**\n")
    if megjegyzes:
        A(megjegyzes + "\n")
    return "\n".join(L), dict(netto=netto, afa=afaossz, brutto=brutto,
                              szamitott_fizetendo=fizetendo, kiirt_fizetendo=kiirt)

# ---- a három számla ----
eloleg = [Tetel("Előleg — technológiai gépészeti felújítás", 1, "db", "3100000", D(27))]
resz = [
    Tetel("Gépészeti szerelés I. ütem", 1, "db", "3100000", D(27)),
    Tetel("Anyagköltség — csővezeték és idomok", 1, "db", "1200000", D(27)),
    Tetel("Műszaki dokumentáció (nyomtatott kiadvány)", 1, "db", "100000", D(5)),
    Tetel("Szakértői vizsgálat", 1, "db", "250000", None, "AAM"),
]
veg = [
    Tetel("Gépészeti szerelés II. ütem", 1, "db", "2800000", D(27)),
    Tetel("Szerelvénycsomag", 2, "db", "1234567.50", D(27)),
    Tetel("Építési-szerelési munka (Áfa tv. 142. § (1) b))", 1, "db", "180865", None, "fordított adózás"),
]

if __name__ == "__main__":
    out = ["# SZÁMLACSOMAG\n",
           "*(tesztelési célra készült, kitalált tartalmú iratok — "
           "a Hegyi és Társa Építőipari Bt. és a Delta-Ipari Szolgáltató Zrt. "
           "2026. június 4-i vállalkozási szerződéséhez)*\n", "---\n"]
    t1, i1 = szamla("SZ-2026/0417", "Előlegszámla", "2026. június 10.", "2026. június 10.",
                    "2026. június 25.", eloleg,
                    megjegyzes="> Az előleg a nettó vállalkozói díj 25 %-a.")
    out += [t1, "---\n"]
    t2, i2 = szamla("SZ-2026/0631", "Részszámla", "2026. szeptember 2.", "2026. augusztus 31.",
                    "2026. szeptember 23.", resz,
                    megjegyzes="> A 4. tétel alanyi adómentes (AAM), nem fordított adózásos.")
    out += [t2, "---\n"]
    fizet_helyes = i1 and None
    netto_v = sum((t.netto for t in veg), D("0"))
    afa_v = sum((t.afa for t in veg), D("0"))
    helyes_fizetendo = netto_v + afa_v - i1["brutto"]
    t3, i3 = szamla("SZ-2026/0912", "Végszámla", "2026. december 3.", "2026. november 30.",
                    "2026. december 24.", veg, elolegbetudas=i1["brutto"],
                    feltuntetett_fizetendo=helyes_fizetendo + HIBAS_ELTERES,
                    megjegyzes="> A 3. tétel a fordított adózás szabálya alá esik (Áfa tv. 142. §), "
                               "az adót a vevő fizeti meg. Ez **nem** alanyi adómentesség.\n>\n"
                               "> Az összegek forintra kerekítve szerepelnek.")
    out += [t3]
    Path("corpus/D3.md").write_text("\n".join(out))
    print("=== ELLENŐRZŐ SZÁMOK (a GT ebből készül) ===")
    for nev, i in (("előleg", i1), ("rész", i2), ("vég", i3)):
        print(f"{nev:8s} nettó={ft(i['netto']):>12s} áfa={ft(i['afa']):>12s} "
              f"bruttó={ft(i['brutto']):>12s} számított fizetendő={ft(i['szamitott_fizetendo']):>12s} "
              f"kiírt={ft(i['kiirt_fizetendo']):>12s}")
    elteres = i3["kiirt_fizetendo"] - i3["szamitott_fizetendo"]
    print(f"\nvégszámla eltérés = {ft(elteres)} Ft ({'több' if elteres>0 else 'kevesebb'} van feltüntetve)")
    assert elteres == HIBAS_ELTERES, elteres
    assert sum((t.netto for t in resz), D("0")) == D("4650000")
    print("nettó ellenőrzés: részszámla 4 650 000 ✓ · végszámla", ft(netto_v))
