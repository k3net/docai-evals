#!/usr/bin/env python3
"""Konzisztencia-ellenőrző: a ground truth és a korpusz egyezésének gépi vizsgálata.

⛔⛔ Ez a védelem az ellen, hogy egy GT-érték olyat állítson, ami a korpuszban nincs benne —
vagy fordítva: hogy egy „nincs az iratban" válasz mögött mégis ott legyen az adat.
Minden állítás MÉRT, nem feltételezett.
"""
import json, re, sys
from pathlib import Path

C = Path("corpus")
DOKOK = {p.name: p.read_text() for p in C.glob("*.md")}
D5 = DOKOK["D5.md"]
MIND = "\n".join(DOKOK.values())
MIND_N = MIND.replace("\u00a0", " ")

hibak, rendben = [], []

def allit(nev, felt, reszlet=""):
    (rendben if felt else hibak).append(f"{nev}{(' — ' + reszlet) if reszlet else ''}")

def hu(n):
    """magyar ezres tagolás — a korpusz VEGYESEN használ sima és nem törhető szóközt,
    ezért mindkét alakot elfogadjuk (ez lesz a pontozó normalizálási szabálya is)."""
    return [f"{n:,}".replace(",", " "), f"{n:,}".replace(",", "\u00a0")]

# ---------- 1. A D5 tartalmazza-e mind a négy forrásdokumentumot ----------
for n in ("D1.md", "D1-M1.md", "D1-M2.md", "D2.md", "D3.md", "D4.md"):
    minta = DOKOK[n][200:400]
    allit(f"D5 tartalmazza a(z) {n}-t", minta in D5)

# ---------- 2. A GT-értékek tényleges jelenléte / hiánya ----------
items = [json.loads(l) for l in Path("gt/items.jsonl").read_text().splitlines() if l.strip()]
allit("50 item", len(items) == 50, f"{len(items)} db")
allit("100 pont összesen", sum(i["pont"] for i in items) == 100, str(sum(i["pont"] for i in items)))
allit("egyedi item-azonosítók", len({i["id"] for i in items}) == len(items))
allit("minden teszt 10 pont", all(
    sum(i["pont"] for i in items if i["teszt"] == t) == 10
    for t in {i["teszt"] for i in items}))

# ---------- 3. Konkrét, forintban kifejezett GT-értékek a korpuszban ----------
PENZ_BENNE = {
    900_000: ("Óvadék (1. sz. mell. 2. pont)", "D1.md"),
    1_500_000: ("iratminta kaució — CSALI", "D1.md"),
    1_200_000: ("felújítási keret (1. sz. mell. 4. pont)", "D1.md"),
    1_850_000: ("alapdíj (4.1)", "D1.md"),
    1_980_000: ("M1 szerinti díj", "D1-M1.md"),
    2_100_000: ("M2 szerinti díj", "D1-M2.md"),
    12_400_000: ("nettó vállalkozói díj", "D2.md"),
    15_748_000: ("bruttó vállalkozói díj", "D2.md"),
    46_000: ("hulladékkezelési hozzájárulás (T10-3)", "D5.md"),
}
for ertek, (mit, hol) in PENZ_BENNE.items():
    alakok = hu(ertek)
    allit(f"{alakok[0]} Ft benne van ({mit})", any(a in DOKOK[hol] for a in alakok), hol)

# ---------- 4. Amit a modellnek NEM szabad megtalálnia ----------
# T9-01: a bérlő cégjegyzékszáma sehol
cegjegyzek = set(re.findall(r"\b\d{2}-\d{2}-\d{6}\b", MIND))
allit("a korpuszban pontosan 2 cégjegyzékszám van",
      cegjegyzek == {"02-09-118423", "02-06-207714"}, str(sorted(cegjegyzek)))
# a Delta-Ipari közelében ne legyen cégjegyzékszám
for d, txt in DOKOK.items():
    for m in re.finditer(r"Delta-Ipari[^\n]{0,400}", txt):
        allit(f"{d}: a Delta-Ipari blokkban nincs cégjegyzékszám",
              not re.search(r"cégjegyzékszám", m.group(0)), m.group(0)[:90])
# T9-04: létszámadat nincs
allit("nincs létszámadat a korpuszban",
      not re.search(r"\b\d+\s*(fő|munkavállalót foglalkoztat)", MIND))
# T6-04: a 11.4. pont nem létezik
allit("a 11.4. pont NEM létezik a D1-ben (csak hivatkozásként)",
      DOKOK["D1.md"].count("11.4") == 1 and "**11.4.**" not in DOKOK["D1.md"],
      f"11.4 előfordulás: {DOKOK['D1.md'].count('11.4')}")
allit("a D1 11. pontja csak 11.1–11.3-at tartalmaz",
      all(f"**11.{k}.**" in DOKOK["D1.md"] for k in (1, 2, 3)))
# T4-04: az Arany János csak utcanévként
for m in re.finditer(r".{0,40}Arany János.{0,40}", MIND):
    allit("az Arany János csak utcanévként fordul elő", "utcai" in m.group(0) or "utca" in m.group(0),
          m.group(0).strip())

# ---------- 5. Indexálási plafon: három érték, három helyen ----------
allit("8 % plafon a D1 törzsszövegében", "évi 8 %-ot nem haladhatja meg" in DOKOK["D1.md"])
allit("6 % plafon az M1 3. pontjában", "évi 6 %-ot nem haladhatja meg" in DOKOK["D1-M1.md"])
allit("5 % plafon az iratmintában (CSALI)", "évi **5 %**-ot nem haladhatja meg" in DOKOK["D1.md"]
      or "**5 %**-ot nem haladhatja meg" in DOKOK["D1.md"])
allit("az M2 kimondja, hogy az indexálást nem érinti",
      "az indexálás egyetlen paraméterét sem érinti" in DOKOK["D1-M2.md"])

# ---------- 6. T10 near-miss csapdák tényleg ott vannak ----------
for kw, hol in (("emelés", "teheremelő"), ("befejezése", "takarítás"), ("szállítása", "3-as kapun")):
    allit(f"near-miss: a(z) „{kw}” szó más jelentésben is szerepel", kw in D5 and hol in D5)
allit("a T10-1 célmondat „korrekció”-t mond, nem „emelés”-t",
      "éves korrekciója**" in D5 or "**éves korrekciója**" in D5)
allit("a T10-2 célmondat „zárónap”-ot mond", "**zárónapja**" in D5)

# ---------- 7. Számla-konzisztencia ----------
allit("a végszámla feltüntetett végösszege 2 962 666 Ft",
      any(f"**{a} Ft**" in DOKOK["D3.md"] for a in hu(2962666)))
allit("a fordított adózásos tétel jelölve van", "fordított adózás" in DOKOK["D3.md"])
allit("az AAM tétel jelölve van", "AAM" in DOKOK["D3.md"])
allit("van 5 %-os tétel", "| 5% |" in DOKOK["D3.md"])
allit("magyar tizedes formátum (1 234 567,50)",
      any(a + ",50" in DOKOK["D3.md"] for a in hu(1234567)))

# ---------- 8. T3 munkarend a korpuszban ----------
allit("a 2. sz. melléklet tartalmazza a munkarendet", "2. SZ. MELLÉKLET" in DOKOK["D2.md"])
allit("az áthelyezett munkanapok deklaráltak",
      "2026. augusztus 8." in DOKOK["D2.md"] and "2026. január 10." in DOKOK["D2.md"])
allit("a határidőszámítás szabálya kimondott",
      "a kézhezvétel napja nem számít bele" in DOKOK["D2.md"])

# ---------- 9. D5 méret és pozíciók ----------
allit("D5 mérete 60 000–90 000 karakter", 60000 <= len(D5) <= 90000, f"{len(D5)} karakter")

# ---------- eredmény ----------
print(f"✅ RENDBEN: {len(rendben)}")
if hibak:
    print(f"\n⛔ HIBA: {len(hibak)}")
    for h in hibak:
        print("   " + h)
    sys.exit(1)
print("\nMinden ellenőrzés lefutott, eltérés nincs.")
