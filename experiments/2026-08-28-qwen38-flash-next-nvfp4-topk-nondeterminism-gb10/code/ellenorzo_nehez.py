#!/usr/bin/env python3
"""A NEHÉZ suite (T11–T20) gépi konzisztencia-ellenőrzése.

⛔⛔ Ugyanaz az elv, mint az `ellenorzo.py`-nál: a ground truth NEM ér semmit,
ha a korpusz nem támasztja alá. Külön ellenőrizzük, hogy a SZÁMOLT válaszok
NEM szerepelnek szó szerint az iratban (különben másolható lenne), és hogy a
csapda-értékek VISZONT ott vannak.

Kilépési kód: 1, ha bármelyik ellenőrzés bukik.
"""
import json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gt_nehez as G

HIBA, OK = [], 0

def ell(felt, uzenet):
    global OK
    if felt:
        OK += 1
    else:
        HIBA.append(uzenet)

C = Path("corpus")
D6 = (C / "D6.md").read_text()
D1 = "\n".join((C / n).read_text() for n in ("D1.md", "D1-M1.md", "D1-M2.md"))
D2 = (C / "D2.md").read_text()
MIND = D6 + D1 + D2 + (C / "D3.md").read_text() + (C / "D4.md").read_text()

def norm(s):
    return s.replace(" ", " ")

def van(hol, mit):
    return norm(mit) in norm(hol)

def szam_van(hol, n):
    """Az összeg magyar (szóközös) és tagolatlan alakját is elfogadja."""
    n = int(n)
    alakok = [f"{n:,}".replace(",", " "), f"{n:,}".replace(",", " "), str(n)]
    return any(a in hol for a in alakok)

# ── D6 megléte és mérete ──
ell(len(D6) > 5000, f"a D6 túl rövid ({len(D6)} karakter)")

# ── T11: indexálás bemenetei OTT vannak, az EREDMÉNY viszont NINCS ott ──
ell(szam_van(D6, G.INDEX_BAZIS), "a D6 nem tartalmazza az indexálás bázisát")
ell(f"{G.INDEX_PLAFON} %" in D6, "a D6 nem mondja ki a 6 %-os felső határt")
for ev, idx in G.KSH_INDEX.items():
    ell(f"| {ev} | {idx} % |" in D6, f"a KSH-index táblázatból hiányzik a {ev}-os sor")
ell(szam_van(D6, G.KEREKITES), "a D6 nem mondja ki a kerekítés egységét")
ell("minden egyes lépésben" in D6, "a D6 nem mondja ki a LÉPÉSENKÉNTI kerekítést")
for s in G.indexalas_lanc():
    ell(not szam_van(MIND, s["dij_ft"]),
        f"⛔ az indexált díj ({s['dij_ft']}) SZÓ SZERINT szerepel a korpuszban — másolható lenne")
ell(not szam_van(MIND, G.indexalas_csak_veges_kerekitessel()),
    "a csapda-érték (végén kerekítve) szerepel a korpuszban")
ell(G.indexalas_lanc()[-1]["dij_ft"] != G.indexalas_csak_veges_kerekitessel(),
    "⛔ a helyes és a csapda-válasz AZONOS — az item nem diszkriminál")
ell(G.indexalas_lanc()[-1]["dij_ft"] != G.indexalas_plafon_nelkul(),
    "⛔ a helyes és a plafon nélküli válasz AZONOS")

# ── T12: két versengő felmondási idő + a sorrend-szabály ──
ell(f"**{G.FELMONDAS_TORZS_NAP} napos**" in D6, "a törzsszövegi felmondási idő hiányzik")
ell(f"{G.FELMONDAS_MELLEKLET_NAP} nap" in D6, "a mellékleti felmondási idő hiányzik")
ell(G.FELMONDAS_TORZS_NAP != G.FELMONDAS_MELLEKLET_NAP, "a két felmondási idő azonos")
ell(D6.index("1. sz. melléklete**,") < D6.index("**törzsszövege**,"),
    "a 2.1. sorrendben a melléklet nem előzi meg a törzsszöveget")
ell("rendes felmondással megszüntetni nem lehet" in D1,
    "a D1 nem zárja ki a rendes felmondást — a T12 harmadik mezője értelmetlen")

# ── T13: számmal és betűvel ELTÉRŐ összeg + a betű elsőbbsége ──
ell(szam_van(D6, G.BELEPESI_DIJ_SZAMMAL), "a számmal kiírt belépési díj hiányzik")
ell(G.BELEPESI_DIJ_BETUVEL_SZOVEG in D6, "a betűvel kiírt belépési díj hiányzik")
ell(G.BELEPESI_DIJ_SZAMMAL != G.BELEPESI_DIJ_BETUVEL, "a számmal és betűvel írt összeg azonos")
ell(not szam_van(D6, G.BELEPESI_DIJ_BETUVEL),
    "⛔ a betűvel kiírt összeg SZÁMMAL is szerepel — nincs mit feloldani")
ell("betűvel kiírt** összeg az irányadó" in D6, "a 4.4. elsőbbségi szabály hiányzik")

# ── T14: négyszintű kivétel + az engedély ténye ──
for reszlet in ("kivéve", "tartószerkezet", "írásban engedélyezte",
                "Nem terheli a Bérlőt a költség akkor sem"):
    ell(reszlet in D6, f"az 5.4. kivétellánc hiányos: „{reszlet}” nincs meg")
ell(D6.count("kivéve") >= 2, "az 5.4-ben nincs KÉT egymásba ágyazott kivétel")
ell("2026. május 4-én" in D6, "az engedély kelte hiányzik")

# ── T15: devizás tábla + rögzített és csali árfolyam ──
ell(f"{G.UZEMELTETESI_EUR_M2_HO} EUR" in D6, "az EUR-alapú alapdíj hiányzik")
ell(f"{G.ARFOLYAM} Ft/EUR" in D6, "a rögzített árfolyam hiányzik")
ell(f"{G.ARFOLYAM_CSALI} Ft/EUR" in D6, "a csali árfolyam hiányzik")
ell("elszámolási alapként nem alkalmazható" in D6, "a csali árfolyam nincs kizárva")
ell(szam_van(D6, G.ALAPTERULET_M2), "az alapterület hiányzik")
K = G.eves_uzemeltetesi_koltseg()
ell(not szam_van(MIND, K["osszesen"]),
    f"⛔ az éves összeg ({K['osszesen']}) szó szerint szerepel a korpuszban")
ell(K["osszesen"] != G.eves_uzemeltetesi_koltseg(G.ARFOLYAM_CSALI)["osszesen"],
    "a helyes és a csali árfolyamos összeg azonos")
ell("**/ év**" in D6, "a biztonsági szolgálat ÉVES mértékegysége nincs kiemelve")

# ── T16: banki nap fogalma két iratból ──
ell("banki nap" in D6, "a banki nap fogalma hiányzik a D6-ból")
ell("naptári év utolsó munkanapjára" in D6, "a banki nap kivétele nincs kimondva")
ell("2. sz. melléklete szerinti munkarend" in D6, "a D6 nem utal a D2 munkarendjére")
ell("2. SZ. MELLÉKLET" in D2.upper(), "a D2-ben nincs munkarend-melléklet")
b = G.hatarido_banki_nap(G.T16_KEZHEZVETEL, G.T16_NAPOK)
m = G.hatarido_munkanapban(G.T16_KEZHEZVETEL, G.T16_NAPOK)
ell(b != m, "⛔ a banki nap és a munkanap szerinti határidő azonos — az item nem diszkriminál")
ell(b.year != m.year, "a két határidő nem lép évhatárt — gyengébb csapda")

# ── T17: anafora — az 1.1-ben MÁSODIKKÉNT megnevezett fél ──
ell("másodikként nevez meg" in D6, "a 8.2. visszautalás hiányzik")
elso = D6.index("Kavicspart Ingatlanhasznosító Kft.**")
masodik = D6.index("Delta-Ipari Szolgáltató Zrt.**")
harmadik = D6.index("Hegyi és Társa Építőipari Bt.**")
ell(elso < masodik < harmadik, "az 1.1. felsorolás sorrendje nem a várt")
ell("Delta-Ipari Szolgáltató Zrt." in D6, "a T17 helyes válasza nem szerepel a D6-ban")
ell(D6.index("az Üzemeltető a felülvizsgálat") > D6.index("másodikként nevez meg")
    if "az Üzemeltető a felülvizsgálat" in D6 else True,
    "a 8.3. csali nem a 8.2. UTÁN áll")

# ── T18: irányt jelölő esetragok ──
ell("— a Bérlő részére — negyedévente **az Üzemeltető** állítja ki" in D6,
    "a 9.1. közbevetéses szórend nincs meg")
ell("**Bérbeadó az Üzemeltetőnél**" in D6, "a 9.2. iránymegjelölés hiányzik")
ell("és nem a\nBérlőnél" in D6 or "és nem a Bérlőnél" in D6, "a 9.2. tagadás hiányzik")

# ── T19: a verziólánc a kontrafaktuálishoz ──
ell(szam_van(D1, 1850000) and szam_van(D1, 1980000) and szam_van(D1, 2100000),
    "a D1-láncból hiányzik valamelyik díjverzió")
ell("2026. szeptember 1" in D1, "az M2 visszamenőleges hatálya nincs kimondva")

# ── T20: a hallgatás ELLENŐRZÉSE ──
ell(szam_van(D6, G.UZEMELTETO_VAGYONI_PLAFON_FT), "a vagyoni kárplafon hiányzik")
ell("**vagyoni károk**" in D6, "a 10.2. nem szűkít kifejezetten vagyoni kárra")
ell("személyi sérülés" not in MIND.lower(),
    "⛔ a SZEMÉLYI SÉRÜLÉS szerepel a korpuszban — a T20 helyes válasza már nem „nincs az iratban”")

# ── az itemfájl ──
IT = [json.loads(l) for l in Path("gt/items-nehez.jsonl").read_text().splitlines() if l.strip()]
ell(len(IT) == 10, f"nem 10 item van, hanem {len(IT)}")
ell(sum(i["pont"] for i in IT) == 100, "nem 100 pont az összeg")
ell(len({i["id"] for i in IT}) == len(IT), "ismétlődő item-azonosító")
ell(len({i["teszt"] for i in IT}) == 10, "nem 10 külön teszt")
for i in IT:
    for d in i["dokumentumok"]:
        ell((C / d).exists(), f"{i['id']}: hiányzó dokumentum {d}")
    ell(set(i["gt"]) <= set(i["sema"]), f"{i['id']}: GT-mező, amely nincs a sémában")
    ell(len(i["gt"]) >= 2, f"{i['id']}: kevesebb mint 2 pontozott mező")

# ── a séma értékkészletei tényleg tartalmazzák a helyes választ ──
for i in IT:
    for k, v in i["gt"].items():
        sema = i["sema"].get(k, "")
        if isinstance(sema, str) and " | " in sema and isinstance(v, str):
            ell(v in [x.strip() for x in sema.split("|")],
                f"{i['id']}.{k}: a GT nincs benne a séma értékkészletében")

if HIBA:
    print(f"❌ {len(HIBA)} ELTÉRÉS ({OK} rendben):")
    for h in HIBA:
        print("  ·", h)
    sys.exit(1)
print(f"✅ RENDBEN: {OK}\n\nMinden ellenőrzés lefutott, eltérés nincs.")
