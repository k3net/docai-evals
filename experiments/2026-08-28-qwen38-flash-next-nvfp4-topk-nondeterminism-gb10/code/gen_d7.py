#!/usr/bin/env python3
"""corpus/D7.md — a HOSSZU KONTEXTUS suite (T21-T25) irata, ~200 000 token.

Merve: 2,535 karakter/token magyar szovegre a Qwen tokenizerrel (D5 es D1 alapjan),
ezert a celmeret 532 000 karakter.

⛔ A beultetett tenyeket a `gt_hosszu.py` adja; a generator SZAMOLT karakterpoziciora
illeszti be oket, majd a TENYLEGES melyseget visszameri es kiirja — nem becsuli.
"""
import random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gt_hosszu as G

R = random.Random(G.MAG)
NY, ZA = "„", "”"          # magyar nyito es zaro idezojel

TERULET = ["gépészet", "elektromos hálózat", "épületszerkezet", "informatika", "vízellátás",
           "hűtés-fűtés", "beléptetőrendszer", "tűzvédelem", "kertészet", "takarítás",
           "liftüzem", "hulladékkezelés", "parkolóüzem", "biztonsági szolgálat"]
MUNKA = ["szűrőcsere", "tömítéscsere", "szelepállítás", "kalibrálás", "nyomáspróba",
         "érintésvédelmi felülvizsgálat", "csapágycsere", "szíjfeszítés", "légtelenítés",
         "vezérlésfrissítés", "akkumulátorteszt", "szivattyúkarbantartás", "csatornatisztítás",
         "világítótest-csere", "ajtóvasalat-állítás", "hőkamerás vizsgálat"]
ESZLELES = ["a berendezés a névleges paramétereken belül üzemelt",
            "a mért érték a tűréshatár felső szélén mozgott",
            "a naplózás hiánytalan volt", "az előző havi észrevétel megszűnt",
            "a szolgáltató a határidőt tartotta", "a hibajelenség nem volt reprodukálható",
            "a beavatkozás után a rendszer stabilan üzemelt",
            "a fogyasztás az előző év azonos időszakához képest mérsékelten alakult",
            "a helyszíni bejárás rendellenességet nem tárt fel",
            "a dokumentáció pótlása megtörtént"]
INTEZKEDES = ["Intézkedés nem volt szükséges.", "A szolgáltatót értesítettük.",
              "A javítást a következő ciklusra ütemeztük.", "A tételt a nyilvántartásban rögzítettük.",
              "A felelős területvezető tájékoztatást kapott.", "Az észrevételt lezártuk.",
              "A pótlólagos mérést elvégeztük.", "A karbantartási tervet nem módosítottuk."]

def penz(n):
    return f"{int(n):,}".replace(",", " ") + " Ft"

def het_datumai(sorszam):
    """2024-01-01-tol indulo heti bontas — determinisztikus, kulso naptar nelkul."""
    from datetime import date, timedelta
    kezd = date(2024, 1, 1) + timedelta(weeks=sorszam)
    return kezd, kezd + timedelta(days=6)

# ── a T22 esemenyek es a near-miss tetelek szetszorasa a hetek kozott ──
HETEK = 156
t22_koltsegek = G.t22_esemenyek()
t22_hetek = sorted(R.sample(range(HETEK), G.T22_DARAB))
t22_map = dict(zip(t22_hetek, t22_koltsegek))
alhang_hetek = set(R.sample([h for h in range(HETEK) if h not in t22_map], G.T22_ALHANG_DARAB))

def heti_jelentes(i, jelolok=True):
    kezd, veg = het_datumai(i)
    s = [f"\n\n### {i+1}. heti üzemeltetési jelentés — {kezd.isoformat()} … {veg.isoformat()}\n"]
    s.append("\n| Közmű | Fogyasztás | Egységár | Költség |\n|---|---|---|---|\n")
    for kozmu, egys, ar in (("villamos energia", "kWh", 78), ("földgáz", "m³", 214),
                            ("ivóvíz", "m³", 692), ("távhő", "GJ", 5840)):
        mennyi = R.randrange(120, 4200)
        s.append(f"| {kozmu} | {mennyi} {egys} | {penz(ar)} / {egys} | {penz(mennyi*ar)} |\n")
    s.append(f"\nA héten a létesítményben {R.randrange(28, 94)} fő dolgozott; a belépések száma "
             f"{R.randrange(180, 640)}, a rendkívüli nyitások száma {R.randrange(0, 5)}.\n")
    s.append("\n**Karbantartási napló**\n\n| Nap | Terület | Munka | Óra | Költség |\n|---|---|---|---|---|\n")
    for _ in range(R.randrange(9, 16)):
        from datetime import timedelta
        nap = kezd + timedelta(days=R.randrange(0, 7))
        ora = R.randrange(1, 13)
        s.append(f"| {nap.isoformat()} | {R.choice(TERULET)} | {R.choice(MUNKA)} | {ora} | "
                 f"{penz(ora * R.randrange(7200, 12800))} |\n")
    if jelolok and i in t22_map:
        s.append(f"\n> **{G.T22_JELOLO}** — a {R.choice(TERULET)} területén, "
                 f"elszámolt költség: **{penz(t22_map[i])}**.\n")
    if jelolok and i in alhang_hetek:
        s.append(f"\n> *Rendkívüli karbantartási igény bejelentése* érkezett a "
                 f"{R.choice(TERULET)} területére; a bejelentés kivizsgálás alatt áll, "
                 f"elszámolt költség nem merült fel.\n")
    s.append("\n**Észrevételek.** ")
    for _ in range(R.randrange(3, 7)):
        s.append(f"A(z) {R.choice(TERULET)} területén {R.choice(ESZLELES)}. "
                 f"{R.choice(INTEZKEDES)} ")
    s.append("\n")
    # near-miss zaj a T25 tuihez: hasonlo alaku adatok, mas ertekkel
    if i % 7 == 3:
        s.append(f"\nA(z) {R.choice(MUNKA)} kivitelezői garanciája "
                 f"{R.randrange(2027, 2032)}. {R.choice(['február','június','szeptember','november'])} "
                 f"{R.randrange(1, 28)}-án jár le.\n")
    if i % 11 == 5:
        s.append(f"\nA tartalék szivattyú típusjele: "
                 f"{R.choice('ABCDEFGHJKLMNPRSTVZ')}{R.choice('ABCDEFGHJKLMNPRSTVZ')}-"
                 f"{R.randrange(1000, 9999)}/{R.choice('ABCD')}.\n")
    if i % 13 == 7:
        s.append(f"\nAz almérő gyári száma: HU-{R.randrange(1000, 9999)}-{R.randrange(100, 999)}.\n")
    if i % 9 == 4:
        s.append(f"\nA(z) {R.choice(['takarítási','kertészeti','portaszolgálati','hulladékkezelési'])} "
                 f"szerződés száma: {R.choice(['TK','KT','PS','HK'])}-{R.randrange(2023, 2027)}/"
                 f"{R.randrange(100, 999)}.\n")
    if i % 17 == 9:
        s.append(f"\nA(z) {R.choice(['villámvédelmi','érintésvédelmi','kéményseprő-ipari'])} "
                 f"felülvizsgálat {R.randrange(2024, 2027)}. "
                 f"{R.choice(['január','március','május','július','december'])} "
                 f"{R.randrange(1, 28)}-án történt.\n")
    return "".join(s)

# ── 1. blokkok legyartasa ──
blokkok = [heti_jelentes(i) for i in range(HETEK)]

# ha kell, tovabbi hetekkel toltjuk fel a celmeretig
i = HETEK
while sum(len(b) for b in blokkok) < G.CEL_KARAKTER * 0.93:
    # ⛔ a feltöltő hetek NEM hordozhatnak T22-jelölőt, különben elszáll a darabszám
    blokkok.append(heti_jelentes(i % HETEK, jelolok=False))
    i += 1

# ── 2. hibajegy-nyilvantartas (T24) a ~60 %-nal ──
hj = ["\n\n## HIBAJEGY-NYILVÁNTARTÁS — 2026\n\n"
      "| Azonosító | Bejelentve | Terület | Prioritás | Állapot |\n|---|---|---|---|---|\n"]
for h in G.t24_hibajegyek():
    hj.append(f"| {h['azonosito']} | {h['bejelentve']} | {h['terulet']} | "
              f"{h['prioritas']} | {h['allapot']} |\n")
hj = "".join(hj)
blokkok.insert(int(len(blokkok) * 0.60), hj)

# ── 3. preambulum es zaro rendelkezesek ──
L = G.t21_lanc()
PREAMBULUM = f"""# LÉTESÍTMÉNYGAZDÁLKODÁSI IRATARCHÍVUM — 2024–2026

*Kavicspart Ingatlanhasznosító Kft. — Pécs, Munkácsy Mihály utca 14. szám alatti telephely*

Az archívum a 2024. január 1. és 2026. december 31. közötti időszak heti üzemeltetési
jelentéseit, karbantartási naplóit, hibajegy-nyilvántartását és záró rendelkezéseit
tartalmazza egyetlen iratban.

## 1. FOGALOMMEGHATÁROZÁSOK

**1.1.** {NY}Üzemeltető{ZA}: a telephely műszaki üzemeltetésével megbízott vállalkozás.

**1.2.** {NY}Rendkívüli beavatkozás{ZA}: az éves karbantartási tervben nem szereplő, a
folyamatos üzem fenntartásához szükséges munkavégzés. A rendkívüli beavatkozásokat a heti
jelentésben a **{G.T22_JELOLO}** megjelöléssel, az elszámolt költséggel együtt kell rögzíteni.
A kivizsgálás alatt álló, elszámolt költséggel nem járó *rendkívüli karbantartási igény
bejelentése* nem minősül rendkívüli beavatkozásnak.

**1.3.** {NY}Rezsióradíj{ZA}: a rendkívüli beavatkozások elszámolásának órabér-alapja.

## 2. AZ ELSZÁMOLÁS ALAPJAI

**2.1.** A **2024. évi rezsióradíj: {penz(L['oradij_2024'])} / óra.** Ez az összeg a 2024. naptári
évben elvégzett rendkívüli beavatkozások elszámolásának alapja.

**2.2.** A rezsióradíj évente, január 1-jén változik; a változás mértékét a Felek az adott évet
megelőzően rögzítik. A mindenkori mértéket a jelen archívum vonatkozó szakasza tartalmazza.

## 3. BEJELENTÉSI ÉS KIVIZSGÁLÁSI REND

**3.1.** A meghibásodást a felfedezéstől számított egy munkanapon belül be kell jelenteni.

**3.2.** A bejelentést az üzemeltetési naplóban rögzíteni kell.

**3.3.** A bejelentő a kivizsgálás eredményéről írásban tájékoztatást kap.

**3.4.** A bejelentett meghibásodást a bejelentéstől számított **{G.T23_KORAI_NAP} munkanapon**
belül ki kell vizsgálni.

**3.5.** A kivizsgálás elmaradása esetén a területvezető intézkedik.

---
"""

ZARO = f"""

---

## ZÁRÓ RENDELKEZÉSEK

**Z.1.** A jelen archívum a 2024–2026. közötti időszak üzemeltetési iratait hiánytalanul
tartalmazza.

**Z.2.** Az archívumot a Felek 2026. december 31-én lezárták.

**Z.3.** Az archívum tartalmáért az Üzemeltető felel.

**Z.5.** A **2026. évi rezsióradíj a 2025. évihez képest {G.T21_EMELES_2026} %-kal magasabb.**

**Z.6.** A 2026. évi elszámolásban **{G.T21_ORASZAM_2026} rendkívüli munkaóra** szerepel.

**{G.T23_KESOI_PONT}.** A Felek rögzítik, hogy a jelen archívum **3.4. pontja szerinti
{G.T23_KORAI_NAP} munkanapos** kivizsgálási határidő helyébe **{G.T23_KESOI_NAP} munkanap**
lép, {G.T23_HATALY[:4]}. december 1-jei hatállyal. A 3.4. pont a továbbiakban ezzel az
eltéréssel alkalmazandó.

**Z.8.** A jelen záró rendelkezések az archívum elválaszthatatlan részét képezik.
"""

# ── 4. a T21 kozepso tenye es a T25 tui: SZAMOLT melysegre illesztve ──
def beszur(blokkok, cel_arany, szoveg):
    """A megadott melysegnek megfelelo blokkhatarra szur be egy kulon blokkot."""
    ossz = sum(len(b) for b in blokkok)
    cel = ossz * cel_arany
    fut = 0
    for idx, b in enumerate(blokkok):
        if fut + len(b) >= cel:
            blokkok.insert(idx, szoveg)
            return
        fut += len(b)
    blokkok.append(szoveg)

T21_KOZEP = f"""

### Az elszámolás felülvizsgálata

A Felek a 2025. naptári évre vonatkozóan rögzítik, hogy **a 2025. évi rezsióradíj a 2024. évihez
képest {G.T21_EMELES_2025} %-kal emelkedett.** A 2025. évi rendkívüli beavatkozások elszámolása
ezen az óradíjon történt.

"""
beszur(blokkok, 0.50, T21_KOZEP)

for arany, mezo, mondat, _ in G.T25_TUK:
    beszur(blokkok, arany, f"\n\n> {mondat}\n\n")

D7 = PREAMBULUM + "".join(blokkok) + ZARO
Path("corpus/D7.md").write_text(D7)

# ── 5. a TENYLEGES melysegek visszamerese ──
# ⛔ A tokenszamot MERNI kell, nem becsulni: a D7 tablazatos szovege 1,973 kar/token,
# a prozai D1/D5 viszont 2,535 — a prozai aranyra alapozott becsles 26 %-ot tevedett.
print(f"corpus/D7.md — {len(D7):,} karakter · becsult tokenszam a MERT 1,973 kar/token aranyon: "
      f"{len(D7)/1.973:,.0f}".replace(",", " "))
print("  ⚠️ a tenyleges tokenszamot a /tokenize vegponttal kell visszamerni MINDKET modellen")
print("\nA beültetett tények TÉNYLEGES mélysége:")
def melyseg(jel):
    i = D7.find(jel)
    return None if i < 0 else i / len(D7)
tenyek = [("T21 · 2024. évi óradíj", penz(L["oradij_2024"]) + " / óra"),
          ("T21 · 2025. évi emelés", f"{G.T21_EMELES_2025} %-kal emelkedett"),
          ("T21 · 2026. évi emelés", f"{G.T21_EMELES_2026} %-kal magasabb"),
          ("T21 · 2026. évi óraszám", f"{G.T21_ORASZAM_2026} rendkívüli munkaóra"),
          ("T23 · korai szabály (3.4.)", f"{G.T23_KORAI_NAP} munkanapon**"),
          ("T23 · késői felülírás (Z.7.)", f"**{G.T23_KESOI_NAP} munkanap**"),
          ("T24 · hibajegy-nyilvántartás", "HIBAJEGY-NYILVÁNTARTÁS")]
for arany, mezo, mondat, ertek in G.T25_TUK:
    tenyek.append((f"T25 · {mezo} (cél {arany*100:.0f} %)", mondat.split("**")[1]))
for nev, jel in tenyek:
    m = melyseg(jel)
    print(f"  {nev:44s} {'—' if m is None else f'{m*100:6.2f} %'}"
          + ("   ⛔ NEM TALÁLHATÓ" if m is None else ""))
print(f"\nA(z) {G.T22_JELOLO} jelölő előfordulása: {D7.count(G.T22_JELOLO)} "
      f"(ebből 1 a fogalommeghatározásban) → esemény: {D7.count(G.T22_JELOLO) - 1}")
