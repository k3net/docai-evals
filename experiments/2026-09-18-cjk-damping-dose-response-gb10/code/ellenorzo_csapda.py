#!/usr/bin/env python3
"""A bővített Csapda Korpusz konzisztencia-ellenőrzése.

⛔⛔ Ez a védelem az ellen, hogy egy GT-érték olyat állítson, ami a korpuszban nincs
benne — vagy fordítva: hogy egy „nincs az iratban” válasz mögött mégis ott legyen az
adat. A bővítésnél ez élesebb kérdés, mint az eredeti 50 itemnél, mert itt minden irat
GENERÁLT, és egy generátorhiba csendben végigfut az összes itemen.

Minden állítás MÉRT, nem feltételezett. Hiba esetén 1-es kilépési kód.

Futtatás:
    python3 src/ellenorzo_csapda.py
"""
import json, re, sys
from pathlib import Path

C = Path("corpus")
DOK = {p.name: p.read_text(encoding="utf-8") for p in C.glob("C*.md")}
# A pontozó whitespace-szabálya: a nem törhető szóköz is sima szóköz.
DOK_N = {k: v.replace(" ", " ") for k, v in DOK.items()}

hibak, rendben = [], []


def allit(nev, felt, reszlet=""):
    (rendben if felt else hibak).append(f"{nev}{(' — ' + reszlet) if reszlet else ''}")


def hu(n):
    """Magyar ezres tagolás, mindkét szóköz-változattal."""
    s = f"{int(n):,}".replace(",", " ")
    return [s, s.replace(" ", " ")]


def benne(dok, n):
    return any(x in DOK_N[dok] for x in hu(n))


T = json.loads(Path("gt/tenyek-csapda.json").read_text(encoding="utf-8"))
UJ = [json.loads(l) for l in Path("gt/items-csapda.jsonl").read_text(
    encoding="utf-8").splitlines() if l.strip()]

# ---------- 1. Szerkezeti állítások ----------
allit("9 irat", len(DOK) == 9, f"{len(DOK)} db")
allit("100 új item", len(UJ) == 100, f"{len(UJ)} db")
allit("egyedi azonosítók", len({i["id"] for i in UJ}) == len(UJ))
allit("minden osztály legalább 11 item",
      all(sum(1 for i in UJ if i["teszt"] == t) >= 11
          for t in {i["teszt"] for i in UJ}))
allit("minden item 1 pont", all(i["pont"] == 1 for i in UJ))
for i in UJ:
    allit(f"{i['id']}: a GT kulcsai a sémában vannak",
          set(i["gt"]) <= set(i["sema"]),
          f"többlet: {sorted(set(i['gt']) - set(i['sema']))}")
    allit(f"{i['id']}: van megjegyzés (hibaosztály)", bool(i["megjegyzes"]))
    allit(f"{i['id']}: létező dokumentumra hivatkozik",
          all(d in DOK for d in i["dokumentumok"]))

# ---------- 2. A 150 itemes fájl: a RÉGI 50 bájtra érintetlen ----------
regi = [l for l in Path("gt/items.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]
ossz = [l for l in Path("gt/items-150.jsonl").read_text(encoding="utf-8").splitlines()
        if l.strip()]
allit("150 item az összevont fájlban", len(ossz) == 150, f"{len(ossz)} db")
allit("a régi 50 item BÁJTRA érintetlen az összevont fájlban", ossz[:50] == regi)

# ---------- 3. C1 — a szétvágott szám csapdája tényleg csapda ----------
for s in T["C1"]["sorok"]:
    allit(f"C1: a(z) {s['sorszam']}. sor nettója szerepel az iratban",
          benne("C1.md", s["netto"]))
    # ⭐ A csapda ATTÓL csapda, hogy a helyes egységár NEM olvasható ki közvetlenül.
    allit(f"C1: a(z) {s['sorszam']}. sor egységára NEM szerepel ép alakban",
          not benne("C1.md", s["egysegar"]),
          f"{s['egysegar']} megtalálható — az item nem azt mérné, amit hiszünk")
    allit(f"C1: a(z) {s['sorszam']}. sor aritmetikája stimmel",
          s["mennyiseg"] * s["egysegar"] == s["netto"])
allit("C1: a nettó összeg a sorok összege",
      sum(s["netto"] for s in T["C1"]["sorok"]) == T["C1"]["netto_osszesen"])
allit("C1: a nettó összeg szerepel az iratban", benne("C1.md", T["C1"]["netto_osszesen"]))

# ---------- 4. C2 — a hiányzó mezők tényleg hiányoznak ----------
TILTOTT = {"fizetesi_mod": ["fizetési mód", "átutalás", "készpénz", "beszedési"],
           "afa_osszeg": ["áfa összesen", "áfa (", "27 %", "27%"],
           "bankszamlaszam": ["bankszámla", "számlaszám:"],
           "teljesites_idopontja": ["teljesítés időpontja", "teljesítés:"],
           "kesedelmi_kamat": ["késedelmi kamat", "jegybanki"]}
for mezo, mintak in TILTOTT.items():
    for m in mintak:
        allit(f"C2: a(z) „{m}” NEM szerepel ({mezo})",
              m.lower() not in DOK_N["C2.md"].lower(),
              "a „nincs az iratban” GT hamis lenne")
# A bankszámlaszám mintázatára külön: 8-8(-8) számjegycsoport. A `---`-ra való
# keresés rossz heurisztika volt — a markdown-tábla elválasztó sorát is elkapta.
allit("C2: nincs bankszámlaszám-alakú szám az iratban",
      not re.search(r"\b\d{8}-\d{8}(-\d{8})?\b", DOK["C2.md"]))

allit("C2: az összeg a két sor összege",
      sum(s["netto"] for s in T["C2"]["sorok"]) == T["C2"]["osszesen"])
allit("C2: az összeg szerepel az iratban", benne("C2.md", T["C2"]["osszesen"]))

# ---------- 5. C3 — engedmény és kerekítés, de csak 3 tételsor ----------
allit("C3: 3 tételsor", T["C3"]["tetelsorok_szama"] == 3)
tabla = [l for l in DOK["C3.md"].splitlines() if re.match(r"^\| \d+ \|", l)]
allit("C3: a tételtáblában PONTOSAN 3 számozott sor van", len(tabla) == 3,
      f"{len(tabla)} db")
allit("C3: az engedmény a nettó 4 %-a",
      round(T["C3"]["netto_tetelek"] * 0.04) == T["C3"]["engedmeny"])
allit("C3: kedvezményes nettó = nettó − engedmény",
      T["C3"]["netto_tetelek"] - T["C3"]["engedmeny"] == T["C3"]["netto_kedvezmenyes"])
allit("C3: a fizetendő 5-re kerekített", T["C3"]["fizetendo"] % 5 == 0)
allit("C3: a kerekítés kisebb, mint 5 Ft",
      abs(T["C3"]["fizetendo"] - T["C3"]["brutto"]) < 5)

# ---------- 6. C4 — a díjak NEM növekvő sorrendben állnak ----------
dijak = [s["netto"] for s in T["C4"]["sorok"]]
allit("C4: a négy díj NEM növekvő sorrendben áll", dijak != sorted(dijak),
      "a csapda enélkül nem él")
allit("C4: mind a négy díj különböző", len(set(dijak)) == 4)
for s in T["C4"]["sorok"]:
    allit(f"C4: a(z) {s['sorszam']}. díj szerepel az iratban", benne("C4.md", s["netto"]))
allit("C4: a legnagyobb a III. negyedév", T["C4"]["legnagyobb"]["sorszam"] == 3)

# ---------- 7. C5 — a törött karakterek tényleg ott vannak ----------
for nev, ch in (("NUL (U+0000)", "\x00"), ("nullaszélességű szóköz (U+200B)", "​"),
                ("feltételes kötőjel (U+00AD)", "­")):
    db = DOK["C5.md"].count(ch)
    allit(f"C5: van {nev}", db > 0, f"{db} db")
allit("C5: fogyasztás = záró − nyitó",
      T["C5"]["zaro"] - T["C5"]["nyito"] == T["C5"]["fogyasztas"])
allit("C5: energiadíj = fogyasztás × egységár",
      abs(T["C5"]["fogyasztas"] * T["C5"]["egysegar"] - T["C5"]["energiadij"]) < 0.01)
allit("C5: nettó = energiadíj + rendszerdíj + alapdíj",
      abs(T["C5"]["energiadij"] + T["C5"]["rendszerdij"] + T["C5"]["alapdij"]
          - T["C5"]["netto"]) < 0.01)
allit("C5: bruttó = nettó × 1,27",
      abs(T["C5"]["netto"] * 1.27 - T["C5"]["brutto"]) < 0.02)

# ---------- 8. C6 — van dátum az iratban, de NEM a hatálybalépésé ----------
allit("C6: van kiírt dátum az iratban",
      bool(re.search(r"20\d\d\. \w+ \d+\.", DOK["C6.md"])))
allit("C6: a hatálybalépés szövegesen van megfogalmazva",
      "aláírásának napján" in DOK["C6.md"])
allit("C6: nincs kiírt hatálybalépési dátum",
      not re.search(r"hatályba.{0,40}20\d\d[.\-]", DOK["C6.md"]))

# ---------- 9. C7 — a kölcsönösség kimondva, de van egy aszimmetria ----------
allit("C7: a kölcsönösség kimondva", "kölcsönös" in DOK["C7.md"])
allit("C7: mindkét szerep GT-je „mindkét fél”",
      T["C7"]["adatkozlo"] == T["C7"]["adatfogado"] == "mindkét fél")
allit("C7: a 4. pont aszimmetrikus",
      T["C7"]["visszaszolgaltatasra_kotelezett"] != T["C7"]["nem_kotelezett"])
allit("C7: a kötbér szerepel az iratban", benne("C7.md", T["C7"]["kotber"]))

# ---------- 10. C8 — óradíj és átalány EGYSZERRE ----------
allit("C8: van óradíj", benne("C8.md", T["C8"]["oradij"]))
allit("C8: van átalány", benne("C8.md", T["C8"]["rendelkezesre_allasi_dij"]))
allit("C8: az irat kimondja, hogy az átalány nem tartalmaz óraszámot",
      "nem tartalmaz ledolgozható óraszámot" in DOK["C8.md"])
allit("C8: márciusi munkadíj = óraszám × óradíj",
      T["C8"]["marciusi_oraszam"] * T["C8"]["oradij"] == T["C8"]["marciusi_munkadij"])
allit("C8: márciusi nettó = munkadíj + átalány",
      T["C8"]["marciusi_munkadij"] + T["C8"]["rendelkezesre_allasi_dij"]
      == T["C8"]["marciusi_netto"])
# ⭐ A csapda: a végösszeg NINCS kiírva az iratba, tehát számolni kell.
allit("C8: a márciusi nettó NINCS kiírva az iratba",
      not benne("C8.md", T["C8"]["marciusi_netto"]))

# ---------- 11. C9 — mindhárom ítélet-típus szerepel ----------
c9 = [i["gt"]["itelet"] for i in UJ if i["teszt"] == "C9" and "itelet" in i["gt"]]
for ertek in ("igaz", "hamis", "nem dönthető el"):
    allit(f"C9: van „{ertek}” item", c9.count(ertek) >= 3, f"{c9.count(ertek)} db")
allit("C9: a nyitva hagyott kérdések az iratban külön megállapodásra utalnak",
      "külön tárgyalnak" in DOK["C9.md"] and "külön állapodnak meg" in DOK["C9.md"])
allit("C9: az irat kimondja, hogy nem sorolja fel az azonnali felmondás eseteit",
      "nem sorolja fel" in DOK["C9.md"])

# ---------- 12. Minden irat jelzi, hogy tesztadat ----------
for nev, szoveg in DOK.items():
    allit(f"{nev}: jelzi, hogy kitalált tartalmú tesztirat",
          "tesztelési célra készült, kitalált tartalmú" in szoveg)

# ---------- kiírás ----------
print(f"✓ {len(rendben)} ellenőrzés rendben")
if hibak:
    print(f"\n⛔ {len(hibak)} HIBA:")
    for h in hibak:
        print(f"  · {h}")
    sys.exit(1)
print("⛔ hiba: nincs")
