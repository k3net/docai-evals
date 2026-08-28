#!/usr/bin/env python3
"""A HOSSZU KONTEXTUS suite (T21-T25) gepi konzisztencia-ellenorzese.

⛔⛔ A T22 osszeget a KIGENERALT IRATBOL parszoljuk vissza — nem a GT-modulbol.
Igy kizarhato, hogy a generator es a GT elcsusszon egymastol.

Kilepesi kod: 1, ha barmelyik ellenorzes bukik.
"""
import json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gt_hosszu as G

HIBA, OK = [], 0
def ell(felt, uzenet):
    global OK
    if felt: OK += 1
    else: HIBA.append(uzenet)

D7 = Path("corpus/D7.md").read_text()
N = len(D7)
def melyseg(jel):
    i = D7.find(jel)
    return None if i < 0 else i / N

# ── meret ──
ell(N > 400_000, f"a D7 tul rovid: {N} karakter")
ell(D7.count("### ") > 100, "kevés a heti jelentés — gyanúsan rövid irat")

# ── T21: harom teny, harom tavoli melysegben, EGESZ ertekekre jovo lanccal ──
L = G.t21_lanc()
m24 = melyseg(f"{L['oradij_2024']:,}".replace(",", " ") + " Ft / óra")
m25 = melyseg(f"{G.T21_EMELES_2025} %-kal emelkedett")
m26 = melyseg(f"{G.T21_EMELES_2026} %-kal magasabb")
mora = melyseg(f"{G.T21_ORASZAM_2026} rendkívüli munkaóra")
for nev, m in (("2024. évi óradíj", m24), ("2025. évi emelés", m25),
               ("2026. évi emelés", m26), ("2026. évi óraszám", mora)):
    ell(m is not None, f"T21: a(z) {nev} NEM található a D7-ben")
if None not in (m24, m25, m26):
    ell(m24 < 0.05, f"T21: a 2024-es tény nem az irat elején van ({m24:.1%})")
    ell(0.40 < m25 < 0.60, f"T21: a 2025-ös tény nem a közepén van ({m25:.1%})")
    ell(m26 > 0.95, f"T21: a 2026-os tény nem a végén van ({m26:.1%})")
ell(L["oradij_2025"] * 100 % 100 == 0 and L["oradij_2026"] * 100 % 100 == 0,
    "T21: a lánc nem egész értékekre jön ki")
for nev in ("csapda_2024_oradij", "csapda_2025_oradij", "csapda_osszeadott_szazalek"):
    ell(L[nev] != L["munkadij_2026"], f"T21: a(z) {nev} csapda egybeesik a helyes válasszal")
ell(str(L["munkadij_2026"]) not in D7.replace(" ", "")
    and f"{L['munkadij_2026']:,}".replace(",", " ") not in D7,
    "⛔ T21: a helyes munkadíj SZÓ SZERINT szerepel az iratban — másolható lenne")

# ── T22: a jelolok szama ES az osszeg a KIGENERALT iratbol ──
sorok = re.findall(r"\*\*" + re.escape(G.T22_JELOLO) + r"\*\* — .*?\*\*([\d  ]+) Ft\*\*", D7)
ell(len(sorok) == G.T22_DARAB,
    f"⛔ T22: a D7-ben {len(sorok)} jelölt esemény van, a GT {G.T22_DARAB}-at vár")
parszolt = sum(int(x.replace(" ", "").replace(" ", "")) for x in sorok)
ell(parszolt == G.t22_ossz(),
    f"⛔ T22: az iratból parszolt összeg {parszolt}, a GT {G.t22_ossz()}")
alhang = D7.count("Rendkívüli karbantartási igény bejelentése")
ell(alhang == G.T22_ALHANG_DARAB,
    f"T22: {alhang} near-miss tétel van, {G.T22_ALHANG_DARAB} helyett")
ell("nem minősül rendkívüli beavatkozásnak" in D7,
    "T22: az 1.2. fogalommeghatározás nem zárja ki a near-miss tételeket")
ell(D7.count(G.T22_JELOLO) == G.T22_DARAB + 1,
    "T22: a jelölő előfordulásainak száma nem esemény+fogalommeghatározás")

# ── T23: korai szabaly az elejen, felulirás a vegen ──
mk = melyseg(f"**{G.T23_KORAI_NAP} munkanapon**")
mv = melyseg(f"**{G.T23_KESOI_NAP} munkanap**")
ell(mk is not None and mk < 0.02, f"T23: a korai szabály nem az irat elején van ({mk})")
ell(mv is not None and mv > 0.98, f"T23: a felülírás nem az irat végén van ({mv})")
ell(G.T23_KORAI_NAP != G.T23_KESOI_NAP, "T23: a két határidő azonos")
ell(f"**{G.T23_KESOI_PONT}.**" in D7, "T23: a felülíró pont jelölése hiányzik")
ell("3.4. pont a továbbiakban ezzel az" in D7, "T23: a felülírás nem hivatkozik vissza a 3.4-re")

# ── T24: pontosan EGY rekord felel meg a ket feltetelnek — a RENDERELT tablabol ──
tabla = re.findall(r"\| (HJ-2026-\d{4}) \| (\d{4}-\d{2}-\d{2}) \| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|", D7)
ell(len(tabla) == G.T24_DARAB, f"T24: {len(tabla)} rekord a táblában, {G.T24_DARAB} helyett")
talalatok = [t for t in tabla if t[3].strip() == "kiemelt" and t[4].strip() == "lezáratlan"]
ell(len(talalatok) == 1, f"⛔ T24: {len(talalatok)} rekord felel meg mindkét feltételnek, nem 1")
if len(talalatok) == 1:
    ny = G.t24_nyertes()
    ell(talalatok[0][0] == ny["azonosito"], "T24: a táblabeli nyertes ≠ a GT nyertese")
    ell(talalatok[0][1] == ny["bejelentve"], "T24: a bejelentés napja eltér")
    ell(talalatok[0][2].strip() == ny["terulet"], "T24: a terület eltér")
kiemelt = sum(1 for t in tabla if t[3].strip() == "kiemelt")
lezaratlan = sum(1 for t in tabla if t[4].strip() == "lezáratlan")
ell(kiemelt >= 6, f"T24: csak {kiemelt} kiemelt rekord — túl könnyű a szűrés")
ell(lezaratlan >= 8, f"T24: csak {lezaratlan} lezáratlan rekord — túl könnyű a szűrés")
mt = melyseg("HIBAJEGY-NYILVÁNTARTÁS")
ell(mt is not None and 0.5 < mt < 0.7, f"T24: a tábla nem a középső harmadban van ({mt})")

# ── T25: minden tu PONTOSAN EGYSZER, es van azonos alaku zaj ──
for arany, mezo, mondat, ertek in G.T25_TUK:
    jel = mondat.split("**")[1]
    ell(D7.count(jel) == 1, f"⛔ T25/{mezo}: a keresett érték {D7.count(jel)}-szer szerepel, nem 1-szer")
    m = melyseg(jel)
    ell(m is not None and abs(m - arany) < 0.03,
        f"T25/{mezo}: a mélység {m if m is None else f'{m:.1%}'}, a cél {arany:.0%}")
zaj = [("garanciája", 8, "garancia-dátum"), ("típusjele:", 5, "típusjel"),
       ("gyári száma:", 5, "gyári szám"), ("szerződés száma:", 5, "szerződésszám"),
       ("felülvizsgálat", 5, "felülvizsgálati dátum")]
for jel, minimum, nev in zaj:
    ell(D7.count(jel) >= minimum,
        f"T25: kevés az azonos alakú {nev}-zaj ({D7.count(jel)} < {minimum}) — a tű túl feltűnő")

# ── itemfajl ──
IT = [json.loads(l) for l in Path("gt/items-hosszu.jsonl").read_text().splitlines() if l.strip()]
ell(len(IT) == 5, f"nem 5 item van, hanem {len(IT)}")
ell(sum(i["pont"] for i in IT) == 100, "nem 100 pont az összeg")
for i in IT:
    ell(i["dokumentumok"] == ["D7.md"], f"{i['id']}: nem a D7-re hivatkozik")
    ell(set(i["gt"]) <= set(i["sema"]), f"{i['id']}: GT-mező, amely nincs a sémában")
    for k in list(i["gt"]) + list(i["sema"]):
        for c in k:
            ell(ord(c) < 128 or "LATIN" in unicodedata.name(c, "LATIN"),
                f"⛔ {i['id']}: NEM LATIN karakter a(z) {k!r} mezőnévben — néma nullpontozás")

if HIBA:
    print(f"❌ {len(HIBA)} ELTÉRÉS ({OK} rendben):")
    for h in HIBA: print("  ·", h)
    sys.exit(1)
print(f"✅ RENDBEN: {OK}\n\nMinden ellenőrzés lefutott, eltérés nincs.")
