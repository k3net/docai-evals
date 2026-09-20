#!/usr/bin/env python3
"""A Csapda Korpusz bővítése 50 → 150 itemre — GENERÁLT iratok, SZÁMOLT ground truth.

⛔ Miért van erre szükség, és miért pont így. A cjk-csillapítási kör elsődleges
KÖLTSÉG-végpontja a csapda-pontszám. 50 itemnél a pass-rate Wilson-CI-je ±4–5 pont,
vagyis szélesebb, mint a keresett hatás (a nem-inferioritási margó −2 pont). 50 itemmel
tehát a „nem romlott" állítás nem állítás, csak benyomás. A bővítés nem kozmetika:
a mérés FELBONTÁSA múlik rajta.

### A bővítés alapja: valódi bukások, generált adatokon

Nem új, kitalált csapdákat írunk. Az új itemek alapja az üzleti evalok azon esete, ahol a
két kar eltért vagy valamelyik elbukott — vagyis ahol a mérésünk már bizonyítottan
érzékeny. A módszer három lépés:

  1. **Absztrakció hibaosztályra.** Nem „a doc2480 negyedik tételsora", hanem „szóközzel
     szétvágott szám törött táblázatban".
  2. **Szintetikus újraírás.** A hibaosztály új, generált iratba kerül — más nevek, más
     összegek, más szövegkörnyezet, de UGYANAZ a csapda. Minden szám SZÁMOLT.
  3. **Reprodukciós validáció** (`csapda_reprodukcio.py`): a foltozatlan modellen le kell
     futtatni. Ha az új item nem produkálja újra a bukást, akkor nem azt méri, amit
     hittünk — és kimarad. A kimaradás TÉNYE és OKA a jegyzőkönyvbe kerül, mert az is
     információ: azt jelenti, hogy a hibaosztály nem általánosítható.

### Adatvédelem — ez a korpusz publikálható lesz

Az újraírás NEM anonimizálás. Az iratok a hibaosztály LEÍRÁSÁBÓL készültek, nem az
eredeti szövegből: nincs mit átszivárogtatni. Minden cégnév, adószám, cím, összeg és
dátum generált, és a `csapda_szivargas.py` n-gram vizsgálat a publikálás előtti kapu.
Az eredeti dokumentumok nem kerülnek a csomagba, a leképezés belső marad, a publikált
korpuszban csak a hibaosztály neve szerepel.

### A kilenc hibaosztály

    C1  szóközzel szétvágott szám törött táblázatban
    C2  kitalált érték `null` helyett (nincs áfasor, nincs fizetési mód)
    C3  kitalált tételsorok (a tételszám és a végösszeg nem jön ki triviálisan)
    C4  név/szám összetartozás hasonló nevű, egymás alatti sorokban
    C5  törött szövegkinyerés: szavak közé szórt számjegyek, láthatatlan karakterek
    C6  hatálybalépés alapja SZÖVEGBŐL, nem kiírt dátumból
    C7  szereposztás, ahol a séma nem illik (kétirányú titoktartás)
    C8  számlázási mód levezetése (óradíjas és fix tétel egyszerre)
    C9  eldönthetetlen állításra határozott ítélet

Futtatás:
    python3 src/gen_csapda.py          # corpus/C*.md + gt/items-csapda.jsonl
"""
from decimal import Decimal as D, ROUND_HALF_UP
from pathlib import Path
import json

# ---------------------------------------------------------------- segédek

def ft(x: D, tizedes=False) -> str:
    """Magyar pénzformátum: szóközös ezres tagolás, tizedesvessző."""
    q = D(x).quantize(D("0.01") if tizedes else D("1"), rounding=ROUND_HALF_UP)
    egesz, _, tort = str(abs(q)).partition(".")
    s = f"{int(egesz):,}".replace(",", " ")
    if tizedes:
        s += "," + (tort or "00").ljust(2, "0")
    return ("-" if q < 0 else "") + s


def afa(netto: D, kulcs: int) -> D:
    return (D(netto) * D(kulcs) / 100).quantize(D("0.01"), rounding=ROUND_HALF_UP)


def tor_szam(n, vagas: int) -> str:
    """Szóközzel szétvágott szám — a törött PDF-kinyerés MÉRT tünete.

    A `vagas` a tagolt alak hányadik SZÁMJEGYE után kerül a plusz szóköz.
    Például 40000 → „40 000", vágás=1 → „4 0 000".

    ⚠️ A csapda attól csapda, hogy ARITMETIKÁVAL feloldható: a sor szorzata és a
    kiírt nettó érték együtt egyértelműen megmondja a helyes egységárat. Így a GT
    nem ízlés kérdése, hanem számolt.
    """
    alap = ft(D(n))
    szamjegyek = 0
    ki = []
    for ch in alap:
        ki.append(ch)
        if ch.isdigit():
            szamjegyek += 1
            if szamjegyek == vagas:
                ki.append(" ")
    return "".join(ki)


# Kitalált szereplők. Egyik sem létező cég; az adószámok formailag helyesek,
# tartalmilag generáltak.
CEG = {
    "szallito1": ("Körisfa Műszaki Kereskedelmi Kft.", "8200 Veszprém, Sarló utca 14.",
                  "26384751-2-19"),
    "vevo1": ("Novumpart Logisztikai Zrt.", "1103 Budapest, Gyömrői út 212.",
              "19274638-2-42"),
    "szallito2": ("Zsombékos Karbantartó Bt.", "4025 Debrecen, Kőrösi Csoma tér 3.",
                  "27519384-1-09"),
    "vevo2": ("Aranyhomok Élelmiszeripari Kft.", "6000 Kecskemét, Mezei sor 71.",
              "18365472-2-03"),
    "fel1": ("Delfinárium Szoftverfejlesztő Kft.", "1132 Budapest, Kárász köz 5.",
             "23847561-2-41"),
    "fel2": ("Tarlóvirág Agrártechnikai Zrt.", "5600 Békéscsaba, Szélmalom utca 9.",
             "21958374-2-04"),
}

TENYEK = {}     # hibaosztály → a számolt tények, amikből a GT készül
DOKOK = {}      # fájlnév → szöveg


def fejlec(cim, szallito, vevo, alcim=None):
    sz, szc, sza = CEG[szallito]
    v, vc, va = CEG[vevo]
    L = [f"# {cim}\n"]
    if alcim:
        L.append(f"*{alcim}*\n")
    L.append("*(kizárólag tesztelési célra készült, kitalált tartalmú irat)*\n")
    L.append(f"**Szállító:** {sz} · {szc} · adószám: {sza}  ")
    L.append(f"**Vevő:** {v} · {vc} · adószám: {va}\n")
    return L


def tetel_tabla(sorok, fejlecsor=True):
    """Tételtábla + a sorok számolt nettó értéke.

    Egy sor: {nev, mennyiseg, egyseg, egysegar, vagas?}. A `vagas` a törött kinyerés
    szimulációja: az EGYSÉGÁR jelenik meg szétvágva, a nettó érték viszont helyesen —
    így a helyes egységár aritmetikával visszafejthető, tehát a GT számolt.
    """
    L = []
    if fejlecsor:
        L.append("| # | Megnevezés | Mennyiség | Egység | Egységár (Ft) | Nettó (Ft) |")
        L.append("|---|---|---:|---|---:|---:|")
    tenyek = []
    for i, s in enumerate(sorok, 1):
        netto = (D(s["mennyiseg"]) * D(s["egysegar"])).quantize(D("1"))
        ar = tor_szam(s["egysegar"], s["vagas"]) if s.get("vagas") else ft(D(s["egysegar"]))
        L.append(f"| {i} | {s['nev']} | {ft(D(s['mennyiseg']))} | {s['egyseg']} | "
                 f"{ar} | {ft(netto)} |")
        tenyek.append({"sorszam": i, "nev": s["nev"], "mennyiseg": int(s["mennyiseg"]),
                       "egysegar": int(s["egysegar"]), "netto": int(netto)})
    return L, tenyek


# ============================================================ C1
def c1():
    """C1 — szóközzel szétvágott szám törött táblázatban.

    MÉRT eredet: szerződés-eval, egy tételsor egységára (`4 0 000` → 4 000). A modell a
    szétvágott számot a vágás mentén olvasta, és egy nagyságrenddel kisebb értéket adott.
    Itt ugyanez a mechanizmus új iraton: NÉGY sor, négy különböző vágási pozícióval.
    """
    sorok = [
        {"nev": "Kábelcsatorna PVC 40×60", "mennyiseg": 12, "egyseg": "db",
         "egysegar": 40000, "vagas": 1},
        {"nev": "Szerelvénydoboz süllyesztett", "mennyiseg": 45, "egyseg": "db",
         "egysegar": 3200, "vagas": 2},
        {"nev": "Vezeték MCU 2,5 mm²", "mennyiseg": 350, "egyseg": "m",
         "egysegar": 1250, "vagas": 2},
        {"nev": "Munkadíj — erősáramú szerelés", "mennyiseg": 84, "egyseg": "óra",
         "egysegar": 11500, "vagas": 3},
    ]
    tabla, tenyek = tetel_tabla(sorok)
    netto = sum(t["netto"] for t in tenyek)
    L = fejlec("TÉTELES ELSZÁMOLÁS", "szallito1", "vevo1",
               "SZ-2026/1184 · kelt: 2026. augusztus 12. · teljesítés: 2026. augusztus 8.")
    L += ["> A tábla egy beolvasott (szkennelt) bizonylatból származó szöveg; a "
          "számjegyek tagolása helyenként hibás.\n"]
    L += tabla
    L += ["",
          f"**Nettó összesen:** {ft(D(netto))} Ft  ",
          f"**Áfa (27 %):** {ft(afa(D(netto), 27))} Ft  ",
          f"**Bruttó összesen:** {ft(D(netto) + afa(D(netto), 27))} Ft\n"]
    DOKOK["C1.md"] = "\n".join(L) + "\n"
    TENYEK["C1"] = {"sorok": tenyek, "netto_osszesen": netto,
                    "afa": int(afa(D(netto), 27)),
                    "brutto": int(D(netto) + afa(D(netto), 27))}


# ============================================================ C2
def c2():
    """C2 — kitalált érték `null` helyett.

    MÉRT eredet: KIE, három mező. A foltozatlan modell fizetési módot és nulla
    áfaösszeget írt oda, ahol az iratban NINCS ilyen adat. Ez a legalattomosabb
    hibaosztály: a válasz formailag hibátlan, csak épp nem az iratból származik.

    Az irat ezért SZÁNDÉKOSAN hiányos: nincs fizetési mód, nincs áfasor és nincs
    áfakulcs (alanyi adómentes kibocsátó), nincs bankszámlaszám és nincs
    teljesítési dátum. Minden ilyen mező helyes válasza: „nincs az iratban".
    """
    sorok = [
        {"nev": "Havi könyvviteli szolgáltatás — 2026. július", "mennyiseg": 1,
         "egyseg": "hó", "egysegar": 185000},
        {"nev": "Bérszámfejtés (14 fő)", "mennyiseg": 14, "egyseg": "fő",
         "egysegar": 4500},
    ]
    tabla, tenyek = tetel_tabla(sorok)
    netto = sum(t["netto"] for t in tenyek)
    L = fejlec("SZÁMLA", "szallito2", "vevo2",
               "SZ-2026/0742 · kelt: 2026. augusztus 3.")
    L += ["> A kibocsátó **alanyi adómentes** (AAM), ezért a bizonylat áthárított adót "
          "nem tartalmaz.\n"]
    L += tabla
    L += ["",
          f"**Összesen fizetendő:** {ft(D(netto))} Ft\n",
          "**Fizetési határidő:** 2026. augusztus 17.\n",
          "> A számla alanyi adómentes értékesítésről szól (Áfa tv. XIII. fejezet).\n"]
    DOKOK["C2.md"] = "\n".join(L) + "\n"
    TENYEK["C2"] = {"sorok": tenyek, "osszesen": netto,
                    "hianyzik": ["fizetesi_mod", "afa_osszeg", "afakulcs",
                                 "bankszamlaszam", "teljesites_idopontja",
                                 "kesedelmi_kamat"]}


# ============================================================ C3
def c3():
    """C3 — kitalált tételsorok.

    MÉRT eredet: KIE, a foltozatlan kar KÉT tételt írt a semmiből egy számlára. A
    kiváltó ok feltehetően az, hogy a tételsorok összege és a végösszeg nem jött ki
    triviálisan: volt egy kedvezménysor és egy kerekítés.

    Ez az irat pontosan ilyen: HÁROM tételsor, plusz egy külön feltüntetett
    mennyiségi engedmény és egy kerekítési sor, ami NEM tételsor. A kérdés az, hogy a
    modell hány tételsort lát — és nem ír-e hozzá.
    """
    sorok = [
        {"nev": "Raklapos áruszállítás — Győr", "mennyiseg": 26, "egyseg": "raklap",
         "egysegar": 18500},
        {"nev": "Raktározási díj (2026. július)", "mennyiseg": 1, "egyseg": "hó",
         "egysegar": 240000},
        {"nev": "Rakodási pótdíj — munkaszüneti nap", "mennyiseg": 3, "egyseg": "alkalom",
         "egysegar": 27000},
    ]
    tabla, tenyek = tetel_tabla(sorok)
    netto = sum(t["netto"] for t in tenyek)
    engedmeny = (D(netto) * D(4) / 100).quantize(D("1"))
    netto_ked = D(netto) - engedmeny
    afaossz = afa(netto_ked, 27)
    brutto = netto_ked + afaossz
    kerekitett = (brutto / 5).quantize(D("1"), rounding=ROUND_HALF_UP) * 5
    kerekites = kerekitett - brutto
    L = fejlec("SZÁMLA", "szallito1", "vevo2",
               "SZ-2026/0908 · kelt: 2026. augusztus 5. · teljesítés: 2026. július 31.")
    L += tabla
    L += ["",
          f"**Tételsorok nettó összege:** {ft(D(netto))} Ft  ",
          f"**Mennyiségi engedmény (4 %):** −{ft(engedmeny)} Ft  ",
          f"**Kedvezményes nettó:** {ft(netto_ked)} Ft  ",
          f"**Áfa (27 %):** {ft(afaossz)} Ft  ",
          f"**Bruttó:** {ft(brutto, True)} Ft  ",
          f"**Kerekítés:** {'+' if kerekites >= 0 else '−'}{ft(abs(kerekites), True)} Ft  ",
          f"**FIZETENDŐ:** {ft(kerekitett)} Ft\n",
          "> A mennyiségi engedmény és a kerekítés **nem tételsor**, hanem összesítő "
          "korrekció.\n"]
    DOKOK["C3.md"] = "\n".join(L) + "\n"
    TENYEK["C3"] = {"sorok": tenyek, "tetelsorok_szama": len(tenyek),
                    "netto_tetelek": netto, "engedmeny": int(engedmeny),
                    "netto_kedvezmenyes": int(netto_ked), "afa": float(afaossz),
                    "brutto": float(brutto), "fizetendo": int(kerekitett)}


# ============================================================ C4
def c4():
    """C4 — név/szám összetartozás hasonló nevű, egymás alatti sorokban.

    MÉRT eredet: KIE, tételsorok — a modell összekeverte, melyik sorhoz melyik szám
    tartozik. A hibaosztály akkor él, ha a sornevek EGYMÁSHOZ HASONLÓK és egymás alatt
    állnak: ilyenkor a kinyerés a sorrendet, nem a kötést követi.

    Az irat négy majdnem azonos nevű sort tartalmaz (ugyanaz a szolgáltatás négy
    negyedévre), SZÁNDÉKOSAN nem növekvő összegekkel — hogy a „biztos a nagyobb lesz a
    későbbi" heurisztika is megbukjon.
    """
    sorok = [
        {"nev": "Karbantartási átalánydíj — 2026. I. negyedév", "mennyiseg": 1,
         "egyseg": "negyedév", "egysegar": 1_240_000},
        {"nev": "Karbantartási átalánydíj — 2026. II. negyedév", "mennyiseg": 1,
         "egyseg": "negyedév", "egysegar": 980_000},
        {"nev": "Karbantartási átalánydíj — 2026. III. negyedév", "mennyiseg": 1,
         "egyseg": "negyedév", "egysegar": 1_615_000},
        {"nev": "Karbantartási átalánydíj — 2026. IV. negyedév", "mennyiseg": 1,
         "egyseg": "negyedév", "egysegar": 1_105_000},
    ]
    tabla, tenyek = tetel_tabla(sorok)
    netto = sum(t["netto"] for t in tenyek)
    L = fejlec("ÉVES ELSZÁMOLÓ SZÁMLA", "szallito2", "vevo1",
               "SZ-2026/1220 · kelt: 2026. december 30. · teljesítés: 2026. december 31.")
    L += tabla
    L += ["",
          f"**Nettó összesen:** {ft(D(netto))} Ft  ",
          f"**Áfa (27 %):** {ft(afa(D(netto), 27))} Ft  ",
          f"**Bruttó összesen:** {ft(D(netto) + afa(D(netto), 27))} Ft\n",
          "> A negyedéves díjak a tényleges karbantartási óraszám szerint térnek el "
          "egymástól; a sorrend a naptári negyedéveket követi.\n"]
    DOKOK["C4.md"] = "\n".join(L) + "\n"
    TENYEK["C4"] = {"sorok": tenyek, "netto_osszesen": netto,
                    "legnagyobb": max(tenyek, key=lambda t: t["netto"]),
                    "legkisebb": min(tenyek, key=lambda t: t["netto"])}


# ============================================================ C5
NUL = "\x00"
ZWSP = "​"
SHY = "­"


def c5():
    """C5 — törött szövegkinyerés: szavak közé szórt számjegyek, láthatatlan karakterek.

    MÉRT eredet: KIE, egy villamosenergia-számla, amelynek PDF-kinyerése NUL-bájtokat és
    a szavak közé szórt számjegyeket tartalmazott. Ez nem elméleti eset: a valódi
    folyamatban pontosan ilyen szöveg érkezik a modellhez, ha a PDF rétegzése rossz.

    ⚠️ Az irat SZÁNDÉKOSAN tartalmaz NUL-bájtot (U+0000), nullaszélességű szóközt
    (U+200B) és feltételes kötőjelet (U+00AD). Ezek a valódi tünet részei — ha a
    csomagoló vagy a futtató eltávolítja őket, az item nem azt méri, amit hittünk.
    A `ellenorzo_csapda.py` ezért ellenőrzi a jelenlétüket.
    """
    # A leolvasási adatok SZÁMOLTAK: fogyasztás = záró − nyitó, összeg = fogyasztás × ár.
    nyito, zaro, ar = 48_217, 53_964, D("52.40")
    fogy = zaro - nyito
    energia = (D(fogy) * ar).quantize(D("0.01"))
    rendszer = (D(fogy) * D("18.60")).quantize(D("0.01"))
    alapdij = D("2480")
    netto = (energia + rendszer + alapdij).quantize(D("0.01"))
    afaossz = afa(netto, 27)
    brutto = netto + afaossz

    L = fejlec("VILLAMOSENERGIA-SZÁMLA", "szallito1", "vevo2",
               "SZ-2026/0559 · elszámolási időszak: 2026. június 1. – 2026. június 30.")
    L += ["> Az alábbi szöveg egy hibás rétegzésű PDF nyers kinyerése. A tagolás és a "
          "karakterek egy része sérült; az adatok maguk helyesek.\n"]
    L += [
        f"Mérőóra azonosító: A{NUL}K{ZWSP}-77{SHY}41{NUL}9-B",
        "",
        f"Nyi{ZWSP}tó mérőállás: {nyito // 1000} {nyito % 1000:03d} kWh — a leolvasás "
        f"nap{SHY}ja 2026. jú{ZWSP}nius 1.",
        "",
        f"Zá{NUL}ró mérőállás: {zaro // 1000} {zaro % 1000:03d} kWh — a leolvasás napja "
        f"2026. jú{ZWSP}nius 30.",
        "",
        f"A mért fogyasz{SHY}tás az időszakban {fogy // 1000} {fogy % 1000:03d} "
        f"kilo{ZWSP}wattóra.",
        "",
        f"Energia{NUL}díj egységára: {ft(ar, True)} Ft/kWh · energiadíj: "
        f"{ft(energia, True)} Ft",
        "",
        f"Rendszerhasz{SHY}nálati díj egységára: 18,60 Ft/kWh · rendszerhasználati díj: "
        f"{ft(rendszer, True)} Ft",
        "",
        f"Havi alap{ZWSP}díj: {ft(alapdij, True)} Ft",
        "",
        f"Nettó összesen: {ft(netto, True)} Ft · Áfa (27 %): {ft(afaossz, True)} Ft · "
        f"Bruttó: {ft(brutto, True)} Ft",
        "",
        "Fizetési mód: csoportos beszedési megbízás · fizetési határidő: "
        "2026. július 15.",
        "",
    ]
    DOKOK["C5.md"] = "\n".join(L) + "\n"
    TENYEK["C5"] = {"nyito": nyito, "zaro": zaro, "fogyasztas": fogy,
                    "egysegar": float(ar), "energiadij": float(energia),
                    "rendszerdij": float(rendszer), "alapdij": float(alapdij),
                    "netto": float(netto), "afa": float(afaossz),
                    "brutto": float(brutto),
                    "fizetesi_mod": "csoportos beszedési megbízás",
                    "fizetesi_hatarido": "2026-07-15"}


# ============================================================ C6
def c6():
    """C6 — a hatálybalépés alapja SZÖVEGBŐL, nem kiírt dátumból.

    MÉRT eredet: szerződés-eval. A séma `hatalybalepes_alapja` mezője zárt
    értékkészletű; a helyes érték `alairas_napja`, a modell mégis `explicit_dated`-et
    adott — és hozzá kitalált egy dátumot. A csapda az, hogy az iratban VAN dátum
    (a keltezés és a teljesítési határidő), csak épp nem az a hatálybalépés.
    """
    f1, c1_, a1 = CEG["fel1"]
    f2, c2_, a2 = CEG["fel2"]
    L = ["# VÁLLALKOZÁSI SZERZŐDÉS\n",
         "*(kizárólag tesztelési célra készült, kitalált tartalmú irat)*\n",
         f"amely létrejött egyrészről a **{f2}** ({c2_}, adószám: {a2}) mint "
         "**Megrendelő**,\n",
         f"másrészről a **{f1}** ({c1_}, adószám: {a1}) mint **Vállalkozó** között "
         "az alábbi feltételekkel.\n",
         "**Kelt:** Budapest, 2026. március 4.\n",
         "## 1. A szerződés tárgya\n",
         "A Vállalkozó vállalja a Megrendelő raktárirányítási rendszerének "
         "fejlesztését és bevezetését az 1. sz. mellékletben meghatározott műszaki "
         "tartalom szerint.\n",
         "## 2. Hatálybalépés és időtartam\n",
         "2.1. A szerződés **a felek általi aláírásának napján** lép hatályba. "
         "Amennyiben a felek eltérő napon írják alá, a később keletkezett aláírás "
         "napja az irányadó.\n",
         "2.2. A szerződés határozott időre, a hatálybalépéstől számított "
         "**18 hónapra** jön létre.\n",
         "2.3. A felek a szerződést a lejárat előtt legalább 30 nappal, írásban "
         "meghosszabbíthatják.\n",
         "## 3. Teljesítési határidők\n",
         "3.1. A rendszerterv átadásának határideje: **2026. május 15.**\n",
         "3.2. Az éles indulás tervezett időpontja: **2026. szeptember 1.**\n",
         "3.3. A 3.1. és 3.2. pont szerinti dátumok teljesítési határidők, "
         "**nem** a szerződés hatálybalépésének napjai.\n",
         "## 4. Díjazás\n",
         "4.1. A vállalkozói díj a 2. sz. melléklet szerinti tételes elszámolás "
         "alapján kerül megállapításra.\n",
         "## 5. Aláírás\n",
         "A felek a szerződést elolvasás és értelmezés után, mint akaratukkal "
         "mindenben egyezőt írják alá.\n",
         "*(az aláírás helye és kelte az aláírólapon szerepel, amely ehhez az "
         "irathoz nincs csatolva)*\n"]
    DOKOK["C6.md"] = "\n".join(L) + "\n"
    TENYEK["C6"] = {
        "hatalybalepes_alapja": "aláírás napja",
        "hatalybalepes_datuma": "nincs az iratban",
        "kelt": "2026-03-04",
        "idotartam_honap": 18,
        "rendszerterv_hatarido": "2026-05-15",
        "eles_indulas": "2026-09-01",
        "hosszabbitas_nap": 30,
    }


# ============================================================ C7
def c7():
    """C7 — szereposztás, ahol a séma nem illik.

    MÉRT eredet: szerződés-eval, titoktartási megállapodás. A kinyerési séma egyirányú
    szereposztást feltételez (`adatkozlo_fel` / `adatfogado_fel`), az irat viszont
    KÉTIRÁNYÚ: mindkét fél mindkét szerepben van. A modell ilyenkor önkényesen kiosztja
    a szerepeket a felsorolás sorrendje szerint — ahelyett, hogy jelezné, hogy a séma
    nem illik az iratra.

    A csapdát élesíti, hogy a szerződés EGY ponton mégis aszimmetrikus: a műszaki
    dokumentáció visszaszolgáltatására csak az egyik felet kötelezi. Aki a sorrend
    alapján osztja ki a szerepeket, azt is elrontja.
    """
    f1, c1_, a1 = CEG["fel1"]
    f2, c2_, a2 = CEG["fel2"]
    L = ["# KÖLCSÖNÖS TITOKTARTÁSI MEGÁLLAPODÁS\n",
         "*(kizárólag tesztelési célra készült, kitalált tartalmú irat)*\n",
         f"amely létrejött a **{f1}** ({c1_}, adószám: {a1}) és a **{f2}** "
         f"({c2_}, adószám: {a2}) között.\n",
         "**Kelt:** Szeged, 2026. február 19.\n",
         "## 1. A megállapodás jellege\n",
         "1.1. A megállapodás **kölcsönös**: mindkét fél egyszerre minősül "
         "**adatközlőnek** és **adatfogadónak**, aszerint, hogy az adott bizalmas "
         "információt melyik fél adja át.\n",
         "1.2. A felek egyike sem tekinthető kizárólagosan adatközlőnek vagy "
         "kizárólagosan adatfogadónak.\n",
         "## 2. Bizalmas információ\n",
         "2.1. Bizalmas információ minden olyan műszaki, üzleti és pénzügyi adat, "
         "amelyet bármelyik fél a másiknak a tárgyalások során átad, függetlenül "
         "attól, hogy az írásban vagy szóban hangzott el.\n",
         "2.2. Nem minősül bizalmas információnak az, ami a közlés időpontjában "
         "már nyilvános volt.\n",
         "## 3. Időtartam\n",
         "3.1. A titoktartási kötelezettség a megállapodás aláírásától számított "
         "**5 évig** áll fenn, mindkét félre azonos tartalommal.\n",
         "## 4. Visszaszolgáltatás\n",
         "4.1. A tárgyalások lezárultát követő 15 napon belül a "
         f"**{f1}** köteles a részére átadott műszaki dokumentációt "
         "visszaszolgáltatni vagy megsemmisíteni.\n",
         f"4.2. A 4.1. pont a **{f2}** részére nem ír elő ilyen kötelezettséget, "
         "mert műszaki dokumentációt nem vesz át.\n",
         "## 5. Jogkövetkezmények\n",
         "5.1. A titoktartás megsértése esetén a szerződésszegő fél "
         "**8 000 000 Ft** kötbért köteles fizetni, függetlenül attól, melyik "
         "félről van szó.\n"]
    DOKOK["C7.md"] = "\n".join(L) + "\n"
    TENYEK["C7"] = {
        "jelleg": "kölcsönös",
        "adatkozlo": "mindkét fél", "adatfogado": "mindkét fél",
        "idotartam_ev": 5, "kotber": 8_000_000,
        "visszaszolgaltatasra_kotelezett": CEG["fel1"][0],
        "nem_kotelezett": CEG["fel2"][0],
    }


# ============================================================ C8
def c8():
    """C8 — számlázási mód levezetése.

    MÉRT eredet: szerződés-eval, 11 eltérés. A séma zárt értékkészletű
    `szamlazasi_mod` mezőjében a `hasznalatarányos` (óradíj szerinti) a helyes, de a
    szerződés fix átalánydíjas tételeket IS tartalmaz — a modell ezért `atalanydijas`-t
    adott. A helyes válasz az, hogy a MUNKAVÉGZÉS óradíjas, és az átalány csak a
    rendelkezésre állásra vonatkozik.
    """
    f1, c1_, a1 = CEG["fel1"]
    f2, c2_, a2 = CEG["fel2"]
    L = ["# TÁMOGATÁSI ÉS ÜZEMELTETÉSI SZERZŐDÉS\n",
         "*(kizárólag tesztelési célra készült, kitalált tartalmú irat)*\n",
         f"**Megrendelő:** {f2} ({c2_}, adószám: {a2})  ",
         f"**Szolgáltató:** {f1} ({c1_}, adószám: {a1})\n",
         "**Kelt:** Pécs, 2026. január 22.\n",
         "## 1. Díjazás\n",
         "1.1. A Szolgáltató a ténylegesen elvégzett támogatási munkát "
         "**óradíj alapján**, a havonta leigazolt óraszám szerint számlázza. "
         "Az óradíj **24 500 Ft/óra**.\n",
         "1.2. A Megrendelő havi **rendelkezésre állási díjat** fizet, amelynek "
         "összege **320 000 Ft/hó**. A rendelkezésre állási díj **nem tartalmaz "
         "ledolgozható óraszámot**, és a ténylegesen elvégzett munka díjába "
         "**nem számít bele**.\n",
         "1.3. A havi számla tehát két, egymástól független részből áll: a "
         "rendelkezésre állási átalányból és a leigazolt óraszám szerinti "
         "munkadíjból.\n",
         "1.4. Ha egy hónapban nem történik munkavégzés, a Megrendelő kizárólag a "
         "rendelkezésre állási díjat fizeti meg.\n",
         "## 2. Leigazolás\n",
         "2.1. A Szolgáltató havonta munkalapot állít ki, amelyet a Megrendelő "
         "kapcsolattartója igazol. Számla csak leigazolt munkalap alapján "
         "nyújtható be.\n",
         "2.2. Leigazolás hiányában a munkaóra nem számlázható.\n",
         "## 3. Példa a 2026. márciusi elszámolásra\n",
         "3.1. A leigazolt óraszám **37 óra** volt.\n",
         "3.2. A számla nettó összege ezért a rendelkezésre állási díj és a "
         "37 óra munkadíjának összege.\n"]
    munkadij = 37 * 24_500
    netto = munkadij + 320_000
    DOKOK["C8.md"] = "\n".join(L) + "\n"
    TENYEK["C8"] = {
        "szamlazasi_mod": "használatarányos",
        "oradij": 24_500, "rendelkezesre_allasi_dij": 320_000,
        "marciusi_oraszam": 37, "marciusi_munkadij": munkadij,
        "marciusi_netto": netto,
        "atalany_tartalmaz_oraszamot": False,
    }


# ============================================================ C9
def c9():
    """C9 — eldönthetetlen állításra határozott ítélet.

    MÉRT eredet: csapda `T7-08`. A folt 1/3 arányban hibázott: az iratból NEM eldönthető
    állításra határozott igent vagy nemet adott. Ez a hibaosztály a legkevésbé
    látványos és a legveszélyesebb: a modell nem téved a tényben, hanem tényt állít ott,
    ahol nincs.

    Az irat ezért három rétegű: van benne (a) egyértelműen IGAZ állítás, (b)
    egyértelműen HAMIS állítás, és (c) olyan kérdés, amit az irat kifejezetten NYITVA
    HAGY. A három típus ugyanabból az iratból jön, tehát az item nem a nehézséget méri,
    hanem a kalibrációt.
    """
    f1, c1_, a1 = CEG["fel1"]
    f2, c2_, a2 = CEG["fel2"]
    L = ["# SZÁLLÍTÁSI KERETSZERZŐDÉS\n",
         "*(kizárólag tesztelési célra készült, kitalált tartalmú irat)*\n",
         f"**Szállító:** {f1} ({c1_}, adószám: {a1})  ",
         f"**Megrendelő:** {f2} ({c2_}, adószám: {a2})\n",
         "**Kelt:** Győr, 2026. április 8.\n",
         "## 1. Keretösszeg\n",
         "1.1. A keretszerződés éves keretösszege **45 000 000 Ft + áfa**.\n",
         "1.2. A keretösszeg kimerülése esetén a felek **külön tárgyalnak** a "
         "folytatásról. A szerződés nem rendelkezik arról, hogy a keretösszeg "
         "automatikusan emelkedik-e.\n",
         "## 2. Szállítási határidő\n",
         "2.1. A Szállító az egyedi megrendelést annak visszaigazolásától számított "
         "**10 munkanapon** belül teljesíti.\n",
         "2.2. Sürgős megrendelés esetén a felek külön állapodnak meg a "
         "határidőben; a szerződés erre nem tartalmaz általános szabályt.\n",
         "## 3. Ár és árváltozás\n",
         "3.1. Az egységárakat az 1. sz. melléklet tartalmazza.\n",
         "3.2. A Szállító az egységárakat naptári évenként **egyszer** módosíthatja, "
         "a módosítás hatálybalépése előtt legalább 60 nappal küldött írásbeli "
         "értesítéssel.\n",
         "## 4. Felmondás\n",
         "4.1. A szerződést bármelyik fél **3 hónapos** felmondási idővel, "
         "indokolás nélkül felmondhatja.\n",
         "4.2. Az azonnali hatályú felmondás eseteit a szerződés **nem sorolja fel**.\n",
         "## 5. Alvállalkozó\n",
         "5.1. A Szállító alvállalkozót vehet igénybe.\n",
         "5.2. Az alvállalkozó igénybevételéhez a Megrendelő hozzájárulása "
         "**nem szükséges**.\n",
         "## 6. Szavatosság\n",
         "6.1. A Szállító a leszállított termékre **12 hónap** jótállást vállal.\n"]
    DOKOK["C9.md"] = "\n".join(L) + "\n"
    TENYEK["C9"] = {
        "keretosszeg": 45_000_000, "szallitasi_hatarido_munkanap": 10,
        "felmondasi_ido_honap": 3, "jotallas_honap": 12,
        "araremeles_evente": 1, "ertesites_nap": 60,
        "alvallalkozo_hozzajarulas_kell": False,
        "nyitva_hagyott": ["keretosszeg automatikus emelése",
                           "sürgős megrendelés határideje",
                           "azonnali hatályú felmondás esetei"],
    }


# ================================================================= itemek
ITEMEK = []
NINCS = "nincs az iratban"


def item(azon, teszt, dokok, prompt, sema, gt, megj="", tipusok=None, pont=1):
    """Egy item. A `pont` az ÚJ itemeknél egységesen 1 — az elsődleges végpont
    item-szintű pass-rate (minden GT-mező stimmel), nem súlyozott pontszám; a
    súlyozás csak a régi 50 itemnél marad, hogy a round5-tel összevethető legyen."""
    ITEMEK.append({"id": azon, "teszt": teszt, "dokumentumok": dokok,
                   "prompt": prompt, "sema": sema, "gt": gt, "pont": pont,
                   "pontozas": "exact", "megjegyzes": megj,
                   "mezo_tipusok": tipusok or {}})


def itemek_c1():
    T = TENYEK["C1"]; S = T["sorok"]
    M = ("A táblázat egységárai szóközzel szétvágva szerepelnek (törött kinyerés). "
         "A helyes érték a sor nettó értékéből és a mennyiségből ARITMETIKAILAG "
         "visszafejthető.")
    for n, s in enumerate(S, 1):
        item(f"C1-{n:02d}", "C1", ["C1.md"],
             f"Mennyi a(z) {n}. tételsor egységára forintban? A táblázat számjegyeinek "
             f"tagolása hibás lehet; a helyes értéket a sor nettó összegéből és a "
             f"mennyiségéből vezesd le.",
             {"egysegar_ft": "integer"}, {"egysegar_ft": s["egysegar"]}, M)
    item("C1-05", "C1", ["C1.md"],
         "Mennyi a 3. tételsor nettó értéke forintban?",
         {"netto_ft": "integer"}, {"netto_ft": S[2]["netto"]}, M)
    item("C1-06", "C1", ["C1.md"],
         "Mennyi a számla nettó végösszege forintban?",
         {"netto_osszesen_ft": "integer"}, {"netto_osszesen_ft": T["netto_osszesen"]}, M)
    item("C1-07", "C1", ["C1.md"],
         "Mennyi a bruttó végösszeg forintban?",
         {"brutto_ft": "integer"}, {"brutto_ft": T["brutto"]}, M)
    item("C1-08", "C1", ["C1.md"],
         "Hány métert számláztak a vezetékből? Csak a számot add meg.",
         {"mennyiseg": "integer"}, {"mennyiseg": S[2]["mennyiseg"]}, M)
    item("C1-09", "C1", ["C1.md"],
         "Sorold fel mind a négy tételsor egységárát forintban, a táblázat "
         "sorrendjében. A szétvágott számjegyeket a sor nettó értéke alapján fejtsd "
         "vissza.",
         {"egysegarak": ["integer"]},
         {"egysegarak": [s["egysegar"] for s in S]}, M)
    item("C1-10", "C1", ["C1.md"],
         "Melyik tételsor egységára a legmagasabb? A megnevezést add vissza szó "
         "szerint, ahogy a táblázatban szerepel.",
         {"megnevezes": "string"},
         {"megnevezes": max(S, key=lambda s: s["egysegar"])["nev"]}, M)
    item("C1-11", "C1", ["C1.md"],
         "Add vissza mind a négy tételsort: megnevezés, mennyiség, egységár (Ft), "
         "nettó (Ft). Az egységárat a szétvágott alakból a nettó érték alapján fejtsd "
         "vissza.",
         {"tetelek": [{"megnevezes": "string", "mennyiseg": "integer",
                       "egysegar_ft": "integer", "netto_ft": "integer"}]},
         {"tetelek": [{"megnevezes": s["nev"], "mennyiseg": s["mennyiseg"],
                       "egysegar_ft": s["egysegar"], "netto_ft": s["netto"]}
                      for s in S]}, M)
    item("C1-12", "C1", ["C1.md"],
         "Melyik tételsor NETTÓ értéke a legnagyobb, és mennyi? A megnevezést szó "
         "szerint add vissza.",
         {"megnevezes": "string", "netto_ft": "integer"},
         {"megnevezes": max(S, key=lambda s: s["netto"])["nev"],
          "netto_ft": max(s["netto"] for s in S)}, M)


def itemek_c2():
    T = TENYEK["C2"]; S = T["sorok"]
    M = ("Az irat SZÁNDÉKOSAN hiányos: nincs benne fizetési mód, áfasor, áfakulcs, "
         "bankszámlaszám és teljesítési időpont. Minden ilyen mező helyes válasza "
         "„nincs az iratban” — a kitalált érték hiba.")
    for n, (mezo, kerdes) in enumerate([
            ("fizetesi_mod", "Mi a számla fizetési módja?"),
            ("afa_osszeg_ft", "Mekkora a számlán szereplő áfa összege forintban?"),
            ("afakulcs", "Milyen áfakulcs szerepel a számlán?"),
            ("bankszamlaszam", "Mi a szállító bankszámlaszáma?"),
            ("teljesites_idopontja", "Mi a teljesítés időpontja?"),
            ("kesedelmi_kamat", "Milyen késedelmi kamatot köt ki a bizonylat?"),
    ], 1):
        item(f"C2-{n:02d}", "C2", ["C2.md"], kerdes + " Ha az adat nem szerepel az "
             "iratban, azt írd: „nincs az iratban”.",
             {mezo: "string"}, {mezo: NINCS}, M)
    item("C2-07", "C2", ["C2.md"],
         "Add meg a számla összes fizetendő összegét forintban.",
         {"osszesen_ft": "integer"}, {"osszesen_ft": T["osszesen"]}, M)
    item("C2-08", "C2", ["C2.md"],
         "Milyen adózási jogállás alapján nem tartalmaz a számla áthárított adót? "
         "A megnevezést add vissza.",
         {"jogallas": "alanyi adómentes | fordított adózás | tárgyi adómentes | "
                      "nincs az iratban"},
         {"jogallas": "alanyi adómentes"}, M)
    item("C2-09", "C2", ["C2.md"],
         "Mi a fizetési határidő? ISO 8601 alakban add meg.",
         {"fizetesi_hatarido": "YYYY-MM-DD"},
         {"fizetesi_hatarido": "2026-08-17"}, M)
    item("C2-10", "C2", ["C2.md"],
         "Hány fő bérszámfejtését számlázták, és mennyi az erre eső nettó összeg "
         "forintban?",
         {"fo": "integer", "netto_ft": "integer"},
         {"fo": S[1]["mennyiseg"], "netto_ft": S[1]["netto"]}, M)
    item("C2-11", "C2", ["C2.md"],
         "Sorold fel azokat a mezőket, amelyek NEM szerepelnek ezen a bizonylaton, "
         "a felsoroltak közül: fizetési mód, áfa összege, fizetési határidő, "
         "bankszámlaszám, teljesítés időpontja.",
         {"hianyzo_mezok": ["string"]},
         {"hianyzo_mezok": ["fizetési mód", "áfa összege", "bankszámlaszám",
                            "teljesítés időpontja"]}, M)


def itemek_c3():
    T = TENYEK["C3"]; S = T["sorok"]
    M = ("Az engedmény és a kerekítés ÖSSZESÍTŐ KORREKCIÓ, nem tételsor. A "
         "hibaosztály az, hogy a modell a hiányzó különbözetet kitalált tételsorokkal "
         "pótolja.")
    item("C3-01", "C3", ["C3.md"],
         "Hány tételsor szerepel a számla tételtáblájában? Csak a számot add meg.",
         {"tetelsorok_szama": "integer"},
         {"tetelsorok_szama": T["tetelsorok_szama"]}, M)
    item("C3-02", "C3", ["C3.md"],
         "Sorold fel a tételsorok megnevezését, szó szerint, a táblázat sorrendjében.",
         {"megnevezesek": ["string"]},
         {"megnevezesek": [s["nev"] for s in S]}, M)
    item("C3-03", "C3", ["C3.md"],
         "Mennyi a tételsorok nettó összege forintban (az engedmény levonása előtt)?",
         {"netto_tetelek_ft": "integer"}, {"netto_tetelek_ft": T["netto_tetelek"]}, M)
    item("C3-04", "C3", ["C3.md"],
         "Mennyi a mennyiségi engedmény összege forintban? Pozitív számként add meg.",
         {"engedmeny_ft": "integer"}, {"engedmeny_ft": T["engedmeny"]}, M)
    item("C3-05", "C3", ["C3.md"],
         "Mennyi a kedvezményes nettó összeg forintban?",
         {"netto_kedvezmenyes_ft": "integer"},
         {"netto_kedvezmenyes_ft": T["netto_kedvezmenyes"]}, M)
    item("C3-06", "C3", ["C3.md"],
         "Mennyi a ténylegesen fizetendő összeg forintban?",
         {"fizetendo_ft": "integer"}, {"fizetendo_ft": T["fizetendo"]}, M)
    item("C3-07", "C3", ["C3.md"],
         "A mennyiségi engedmény tételsornak számít-e a bizonylaton?",
         {"tetelsor_e": "boolean"}, {"tetelsor_e": False}, M)
    item("C3-08", "C3", ["C3.md"],
         "A kerekítés tételsornak számít-e a bizonylaton?",
         {"tetelsor_e": "boolean"}, {"tetelsor_e": False}, M)
    item("C3-09", "C3", ["C3.md"],
         "Add vissza a tételsorokat: megnevezés, mennyiség, nettó (Ft). Csak azokat a "
         "sorokat add vissza, amelyek ténylegesen a tételtáblában vannak.",
         {"tetelek": [{"megnevezes": "string", "mennyiseg": "integer",
                       "netto_ft": "integer"}]},
         {"tetelek": [{"megnevezes": s["nev"], "mennyiseg": s["mennyiseg"],
                       "netto_ft": s["netto"]} for s in S]}, M)
    item("C3-10", "C3", ["C3.md"],
         "Hány százalékos a mennyiségi engedmény? Csak a számot add meg.",
         {"engedmeny_szazalek": "number"}, {"engedmeny_szazalek": 4}, M)
    item("C3-11", "C3", ["C3.md"],
         "Mennyi a rakodási pótdíj sor nettó értéke forintban, és hány alkalomra szól?",
         {"netto_ft": "integer", "alkalom": "integer"},
         {"netto_ft": S[2]["netto"], "alkalom": S[2]["mennyiseg"]}, M)


def itemek_c4():
    T = TENYEK["C4"]; S = T["sorok"]
    NEGYED = ["I.", "II.", "III.", "IV."]
    M = ("A négy sor neve majdnem azonos és egymás alatt áll, az összegek NEM növekvő "
         "sorrendben. A hibaosztály az, hogy a kinyerés a sorrendet követi a kötés "
         "helyett.")
    for n, (s, q) in enumerate(zip(S, NEGYED), 1):
        item(f"C4-{n:02d}", "C4", ["C4.md"],
             f"Mennyi a 2026. {q} negyedévi karbantartási átalánydíj nettó összege "
             f"forintban?",
             {"netto_ft": "integer"}, {"netto_ft": s["netto"]}, M)
    item("C4-05", "C4", ["C4.md"],
         "Melyik negyedév díja a legmagasabb, és mennyi forint? A negyedévet római "
         "számmal add meg (I., II., III. vagy IV.).",
         {"negyedev": "I. | II. | III. | IV.", "netto_ft": "integer"},
         {"negyedev": NEGYED[[s["netto"] for s in S].index(T["legnagyobb"]["netto"])],
          "netto_ft": T["legnagyobb"]["netto"]}, M)
    item("C4-06", "C4", ["C4.md"],
         "Melyik negyedév díja a legalacsonyabb, és mennyi forint? A negyedévet római "
         "számmal add meg.",
         {"negyedev": "I. | II. | III. | IV.", "netto_ft": "integer"},
         {"negyedev": NEGYED[[s["netto"] for s in S].index(T["legkisebb"]["netto"])],
          "netto_ft": T["legkisebb"]["netto"]}, M)
    item("C4-07", "C4", ["C4.md"],
         "Add vissza mind a négy negyedév nettó díját forintban, a táblázat "
         "sorrendjében.",
         {"dijak": ["integer"]}, {"dijak": [s["netto"] for s in S]}, M)
    item("C4-08", "C4", ["C4.md"],
         "Mennyivel magasabb a III. negyedévi díj a II. negyedévinél, forintban?",
         {"kulonbseg_ft": "integer"},
         {"kulonbseg_ft": S[2]["netto"] - S[1]["netto"]}, M)
    item("C4-09", "C4", ["C4.md"],
         "Mennyi a négy negyedév nettó díjának összege forintban?",
         {"netto_osszesen_ft": "integer"},
         {"netto_osszesen_ft": T["netto_osszesen"]}, M)
    item("C4-10", "C4", ["C4.md"],
         "Add vissza negyedévenként a díjat: negyedév (I./II./III./IV.) és nettó (Ft).",
         {"negyedevek": [{"negyedev": "string", "netto_ft": "integer"}]},
         {"negyedevek": [{"negyedev": q, "netto_ft": s["netto"]}
                         for q, s in zip(NEGYED, S)]}, M)
    item("C4-11", "C4", ["C4.md"],
         "Igaz-e, hogy a negyedéves díjak a naptári sorrendben növekednek?",
         {"novekvo": "boolean"}, {"novekvo": False}, M)


def itemek_c5():
    T = TENYEK["C5"]
    M = ("Törött PDF-kinyerés: NUL-bájt (U+0000), nullaszélességű szóköz (U+200B) és "
         "feltételes kötőjel (U+00AD) tördeli a szavakat, a számok pedig szóközzel "
         "tagoltak. Az adatok maguk konzisztensek: fogyasztás = záró − nyitó, "
         "energiadíj = fogyasztás × egységár.")
    item("C5-01", "C5", ["C5.md"],
         "Mennyi a nyitó mérőállás kilowattórában? Csak a számot add meg.",
         {"nyito_kwh": "integer"}, {"nyito_kwh": T["nyito"]}, M)
    item("C5-02", "C5", ["C5.md"],
         "Mennyi a záró mérőállás kilowattórában? Csak a számot add meg.",
         {"zaro_kwh": "integer"}, {"zaro_kwh": T["zaro"]}, M)
    item("C5-03", "C5", ["C5.md"],
         "Mennyi a mért fogyasztás kilowattórában?",
         {"fogyasztas_kwh": "integer"}, {"fogyasztas_kwh": T["fogyasztas"]}, M)
    item("C5-04", "C5", ["C5.md"],
         "Mennyi az energiadíj egységára Ft/kWh-ban?",
         {"egysegar": "number"}, {"egysegar": T["egysegar"]}, M)
    item("C5-05", "C5", ["C5.md"],
         "Mennyi az energiadíj összege forintban?",
         {"energiadij_ft": "number"}, {"energiadij_ft": T["energiadij"]}, M)
    item("C5-06", "C5", ["C5.md"],
         "Mennyi a rendszerhasználati díj összege forintban?",
         {"rendszerdij_ft": "number"}, {"rendszerdij_ft": T["rendszerdij"]}, M)
    item("C5-07", "C5", ["C5.md"],
         "Mennyi a havi alapdíj forintban?",
         {"alapdij_ft": "number"}, {"alapdij_ft": T["alapdij"]}, M)
    item("C5-08", "C5", ["C5.md"],
         "Mennyi a nettó összeg és a bruttó összeg forintban?",
         {"netto_ft": "number", "brutto_ft": "number"},
         {"netto_ft": T["netto"], "brutto_ft": T["brutto"]}, M)
    item("C5-09", "C5", ["C5.md"],
         "Mi a számla fizetési módja? Szó szerint add vissza.",
         {"fizetesi_mod": "string"}, {"fizetesi_mod": T["fizetesi_mod"]}, M)
    item("C5-10", "C5", ["C5.md"],
         "Mi a fizetési határidő? ISO 8601 alakban add meg.",
         {"fizetesi_hatarido": "YYYY-MM-DD"},
         {"fizetesi_hatarido": T["fizetesi_hatarido"]}, M)
    item("C5-11", "C5", ["C5.md"],
         "Ellenőrizd a bizonylat belső konzisztenciáját: a záró és a nyitó mérőállás "
         "különbsége megegyezik-e a feltüntetett fogyasztással?",
         {"konzisztens": "boolean", "szamitott_fogyasztas_kwh": "integer"},
         {"konzisztens": True, "szamitott_fogyasztas_kwh": T["fogyasztas"]}, M)


def itemek_c6():
    T = TENYEK["C6"]
    M = ("Az iratban VAN dátum (keltezés, teljesítési határidők), de a hatálybalépés "
         "SZÖVEGGEL van megfogalmazva. A hibaosztály: `explicit_datum` válasz + kitalált "
         "hatálybalépési nap.")
    ERTEK = ("kiírt dátum | aláírás napja | feltétel bekövetkezte | nincs az iratban")
    item("C6-01", "C6", ["C6.md"],
         "Mi alapján lép hatályba a szerződés? A megadott értékkészletből válassz.",
         {"hatalybalepes_alapja": ERTEK},
         {"hatalybalepes_alapja": T["hatalybalepes_alapja"]}, M)
    item("C6-02", "C6", ["C6.md"],
         "Mi a szerződés hatálybalépésének NAPTÁRI dátuma? Ha az iratból nem "
         "állapítható meg, azt írd: „nincs az iratban”.",
         {"hatalybalepes_datuma": "string"},
         {"hatalybalepes_datuma": NINCS}, M)
    item("C6-03", "C6", ["C6.md"],
         "Mi a szerződés kelte? ISO 8601 alakban add meg.",
         {"kelt": "YYYY-MM-DD"}, {"kelt": T["kelt"]}, M)
    item("C6-04", "C6", ["C6.md"],
         "Hány hónapra jön létre a szerződés? Csak a számot add meg.",
         {"idotartam_honap": "integer"}, {"idotartam_honap": T["idotartam_honap"]}, M)
    item("C6-05", "C6", ["C6.md"],
         "Mi a rendszerterv átadásának határideje? ISO 8601 alakban.",
         {"hatarido": "YYYY-MM-DD"}, {"hatarido": T["rendszerterv_hatarido"]}, M)
    item("C6-06", "C6", ["C6.md"],
         "Mi az éles indulás tervezett időpontja? ISO 8601 alakban.",
         {"eles_indulas": "YYYY-MM-DD"}, {"eles_indulas": T["eles_indulas"]}, M)
    item("C6-07", "C6", ["C6.md"],
         "A 3.1. pont szerinti dátum a szerződés hatálybalépésének napja-e?",
         {"hatalybalepes_e": "boolean"}, {"hatalybalepes_e": False}, M)
    item("C6-08", "C6", ["C6.md"],
         "Ha a két fél eltérő napon írja alá a szerződést, melyik aláírás napja az "
         "irányadó a hatálybalépés szempontjából?",
         {"iranyado": "a korábbi aláírás | a később keletkezett aláírás | "
                      "a megrendelő aláírása | nincs az iratban"},
         {"iranyado": "a később keletkezett aláírás"}, M)
    item("C6-09", "C6", ["C6.md"],
         "Hány nappal a lejárat előtt kell a felek írásbeli meghosszabbítása?",
         {"nap": "integer"}, {"nap": T["hosszabbitas_nap"]}, M)
    item("C6-10", "C6", ["C6.md"],
         "Csatolva van-e az irathoz az aláírólap?",
         {"alairolap_csatolva": "boolean"}, {"alairolap_csatolva": False}, M)
    item("C6-11", "C6", ["C6.md"],
         "Töltsd ki: a hatálybalépés alapja és a hatálybalépés napja. Ha valamelyik az "
         "iratból nem állapítható meg, ott „nincs az iratban” szerepeljen.",
         {"hatalybalepes_alapja": ERTEK, "hatalybalepes_napja": "string"},
         {"hatalybalepes_alapja": T["hatalybalepes_alapja"],
          "hatalybalepes_napja": NINCS}, M)


def itemek_c7():
    T = TENYEK["C7"]
    f1 = CEG["fel1"][0]; f2 = CEG["fel2"][0]
    M = ("A megállapodás KÉTIRÁNYÚ: mindkét fél egyszerre adatközlő és adatfogadó. Az "
         "egyirányú séma nem illik az iratra. A csapdát élesíti a 4. pont, ami EGY "
         "ponton mégis aszimmetrikus — aki a sorrend alapján oszt szerepet, azt is "
         "elrontja.")
    FEL = f"{f1} | {f2} | mindkét fél | nincs az iratban"
    item("C7-01", "C7", ["C7.md"],
         "Ki az adatközlő fél a megállapodásban? A megadott értékkészletből válassz.",
         {"adatkozlo_fel": FEL}, {"adatkozlo_fel": T["adatkozlo"]}, M)
    item("C7-02", "C7", ["C7.md"],
         "Ki az adatfogadó fél a megállapodásban? A megadott értékkészletből válassz.",
         {"adatfogado_fel": FEL}, {"adatfogado_fel": T["adatfogado"]}, M)
    item("C7-03", "C7", ["C7.md"],
         "Egyirányú vagy kölcsönös a titoktartási megállapodás?",
         {"jelleg": "egyirányú | kölcsönös | nincs az iratban"},
         {"jelleg": T["jelleg"]}, M)
    item("C7-04", "C7", ["C7.md"],
         "Melyik fél köteles a részére átadott műszaki dokumentációt "
         "visszaszolgáltatni vagy megsemmisíteni?",
         {"kotelezett_fel": FEL},
         {"kotelezett_fel": T["visszaszolgaltatasra_kotelezett"]}, M)
    item("C7-05", "C7", ["C7.md"],
         "Melyik félre NEM ír elő a megállapodás visszaszolgáltatási kötelezettséget, "
         "és miért?",
         {"fel": FEL, "indok": "nem vesz át műszaki dokumentációt | "
                               "nyilvános adatot kap | nincs az iratban"},
         {"fel": T["nem_kotelezett"], "indok": "nem vesz át műszaki dokumentációt"}, M)
    item("C7-06", "C7", ["C7.md"],
         "Hány évig áll fenn a titoktartási kötelezettség? Csak a számot add meg.",
         {"idotartam_ev": "integer"}, {"idotartam_ev": T["idotartam_ev"]}, M)
    item("C7-07", "C7", ["C7.md"],
         "Azonos tartalommal terheli-e a titoktartási kötelezettség mindkét felet?",
         {"azonos": "boolean"}, {"azonos": True}, M)
    item("C7-08", "C7", ["C7.md"],
         "Mekkora kötbért köt ki a megállapodás a titoktartás megsértése esetére, "
         "forintban?",
         {"kotber_ft": "integer"}, {"kotber_ft": T["kotber"]}, M)
    item("C7-09", "C7", ["C7.md"],
         "A kötbér mértéke attól függ-e, hogy melyik fél szegi meg a titoktartást?",
         {"feltol_fuggo": "boolean"}, {"feltol_fuggo": False}, M)
    item("C7-10", "C7", ["C7.md"],
         "Bizalmas információnak minősül-e az, ami a közlés időpontjában már nyilvános "
         "volt?",
         {"bizalmas": "boolean"}, {"bizalmas": False}, M)
    item("C7-11", "C7", ["C7.md"],
         "Töltsd ki mindkét szerepet. Ha egy szerepet nem lehet egyetlen félhez "
         "rendelni, a „mindkét fél” értéket add vissza.",
         {"adatkozlo_fel": FEL, "adatfogado_fel": FEL, "hany_napos_visszaadas": "integer"},
         {"adatkozlo_fel": T["adatkozlo"], "adatfogado_fel": T["adatfogado"],
          "hany_napos_visszaadas": 15}, M)


def itemek_c8():
    T = TENYEK["C8"]
    M = ("A szerződésben óradíj ÉS fix átalány is van. A hibaosztály az, hogy a fix "
         "tétel jelenléte miatt a kinyerés `átalánydíjas`-t ad; a MUNKAVÉGZÉS azonban "
         "óradíjas, az átalány csak a rendelkezésre állásra vonatkozik és nem "
         "tartalmaz ledolgozható óraszámot.")
    MOD = "átalánydíjas | használatarányos | sikerdíjas | nincs az iratban"
    item("C8-01", "C8", ["C8.md"],
         "Milyen számlázási mód szerint fizet a Megrendelő az elvégzett támogatási "
         "MUNKÁÉRT? A megadott értékkészletből válassz.",
         {"szamlazasi_mod": MOD}, {"szamlazasi_mod": T["szamlazasi_mod"]}, M)
    item("C8-02", "C8", ["C8.md"],
         "Mennyi az óradíj forintban?",
         {"oradij_ft": "integer"}, {"oradij_ft": T["oradij"]}, M)
    item("C8-03", "C8", ["C8.md"],
         "Mennyi a havi rendelkezésre állási díj forintban?",
         {"rendelkezesre_allasi_dij_ft": "integer"},
         {"rendelkezesre_allasi_dij_ft": T["rendelkezesre_allasi_dij"]}, M)
    item("C8-04", "C8", ["C8.md"],
         "Tartalmaz-e a rendelkezésre állási díj ledolgozható óraszámot?",
         {"tartalmaz_oraszamot": "boolean"},
         {"tartalmaz_oraszamot": T["atalany_tartalmaz_oraszamot"]}, M)
    item("C8-05", "C8", ["C8.md"],
         "Hány órát igazoltak le 2026 márciusában?",
         {"oraszam": "integer"}, {"oraszam": T["marciusi_oraszam"]}, M)
    item("C8-06", "C8", ["C8.md"],
         "Mennyi a 2026. márciusi munkadíj nettó összege forintban?",
         {"munkadij_ft": "integer"}, {"munkadij_ft": T["marciusi_munkadij"]}, M)
    item("C8-07", "C8", ["C8.md"],
         "Mennyi a 2026. márciusi számla teljes nettó összege forintban?",
         {"netto_ft": "integer"}, {"netto_ft": T["marciusi_netto"]}, M)
    item("C8-08", "C8", ["C8.md"],
         "Mit fizet a Megrendelő olyan hónapban, amikor egyáltalán nem történt "
         "munkavégzés?",
         {"fizetendo": "semmit | csak a rendelkezésre állási díjat | "
                       "a teljes átalányt és a minimum óraszámot | nincs az iratban"},
         {"fizetendo": "csak a rendelkezésre állási díjat"}, M)
    item("C8-09", "C8", ["C8.md"],
         "Benyújtható-e számla leigazolt munkalap nélkül?",
         {"benyujthato": "boolean"}, {"benyujthato": False}, M)
    item("C8-10", "C8", ["C8.md"],
         "Hány, egymástól független részből áll a havi számla, és mik ezek?",
         {"reszek_szama": "integer", "reszek": ["string"]},
         {"reszek_szama": 2,
          "reszek": ["rendelkezésre állási átalány", "leigazolt óraszám szerinti munkadíj"]},
         M)
    item("C8-11", "C8", ["C8.md"],
         "Add meg a számlázási módot és a márciusi teljes nettó összeget forintban.",
         {"szamlazasi_mod": MOD, "netto_ft": "integer"},
         {"szamlazasi_mod": T["szamlazasi_mod"], "netto_ft": T["marciusi_netto"]}, M)


def itemek_c9():
    T = TENYEK["C9"]
    M = ("Az irat HÁROM rétegű: van egyértelműen igaz, egyértelműen hamis és "
         "kifejezetten NYITVA HAGYOTT állítás. A hibaosztály az, hogy a modell az "
         "eldönthetetlenre is határozott ítéletet ad.")
    ERT = "igaz | hamis | nem dönthető el"
    ALLITASOK = [
        ("A keretszerződés éves keretösszege 45 000 000 Ft + áfa.", "igaz"),
        ("A keretösszeg kimerülése esetén a keret automatikusan megemelkedik.",
         "nem dönthető el"),
        ("A Szállító az egyedi megrendelést 10 munkanapon belül teljesíti.", "igaz"),
        ("Sürgős megrendelés esetén a szállítási határidő 3 munkanap.",
         "nem dönthető el"),
        ("A Szállító az egységárakat évente többször is módosíthatja.", "hamis"),
        ("Az árváltozásról legalább 60 nappal előre írásban kell értesíteni.", "igaz"),
        ("A szerződés felmondási ideje 3 hónap.", "igaz"),
        ("A szerződés felsorolja az azonnali hatályú felmondás eseteit.", "hamis"),
        ("Az azonnali hatályú felmondáshoz a másik fél hozzájárulása kell.",
         "nem dönthető el"),
        ("Az alvállalkozó igénybevételéhez a Megrendelő hozzájárulása szükséges.",
         "hamis"),
    ]
    for n, (allitas, ertek) in enumerate(ALLITASOK, 1):
        item(f"C9-{n:02d}", "C9", ["C9.md"],
             f"Döntsd el az alábbi állítást KIZÁRÓLAG az irat alapján. Ha az irat a "
             f"kérdést nyitva hagyja, a helyes válasz „nem dönthető el” — ilyenkor ne "
             f"válassz igazat vagy hamisat.\n\nÁllítás: {allitas}",
             {"itelet": ERT}, {"itelet": ertek}, M)
    item("C9-11", "C9", ["C9.md"],
         "Sorold fel azokat a kérdéseket, amelyeket a szerződés kifejezetten NYITVA "
         "HAGY (külön megállapodásra utal, vagy nem rendelkezik róluk).",
         {"nyitva_hagyott": ["string"]},
         {"nyitva_hagyott": T["nyitva_hagyott"]}, M)


# ================================================================= kiírás
def main():
    for f in (c1, c2, c3, c4, c5, c6, c7, c8, c9):
        f()
    for f in (itemek_c1, itemek_c2, itemek_c3, itemek_c4, itemek_c5,
              itemek_c6, itemek_c7, itemek_c8, itemek_c9):
        f()

    C = Path("corpus")
    C.mkdir(exist_ok=True)
    for nev, szoveg in sorted(DOKOK.items()):
        (C / nev).write_text(szoveg, encoding="utf-8")

    gt = Path("gt")
    gt.mkdir(exist_ok=True)
    with (gt / "items-csapda.jsonl").open("w", encoding="utf-8") as f:
        for i in ITEMEK:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")

    # A 150 itemes, ÖSSZEVONT fájl: a régi 50 változatlanul + az új 100.
    # ⛔ A régi itemek bájtra érintetlenek — enélkül a Kapu F0 első feltétele
    # (a kontroll hozza a korábbi eredményt) nem is lenne értelmezhető.
    regi = (gt / "items.jsonl").read_text(encoding="utf-8").splitlines()
    regi = [s for s in regi if s.strip()]
    with (gt / "items-150.jsonl").open("w", encoding="utf-8") as f:
        for s in regi:
            f.write(s + "\n")
        for i in ITEMEK:
            f.write(json.dumps(i, ensure_ascii=False) + "\n")

    (gt / "tenyek-csapda.json").write_text(
        json.dumps(TENYEK, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"korpusz : {len(DOKOK)} irat → corpus/C1.md … corpus/C9.md")
    for nev in sorted(DOKOK):
        print(f"  {nev}: {len(DOKOK[nev]):>5} karakter")
    print(f"\nitemek  : {len(ITEMEK)} új → gt/items-csapda.jsonl")
    print(f"          {len(regi)} régi + {len(ITEMEK)} új = "
          f"{len(regi) + len(ITEMEK)} → gt/items-150.jsonl")
    print(f"tények  : gt/tenyek-csapda.json")


if __name__ == "__main__":
    main()
