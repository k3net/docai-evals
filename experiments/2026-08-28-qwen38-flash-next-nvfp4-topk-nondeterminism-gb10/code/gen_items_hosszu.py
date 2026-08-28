#!/usr/bin/env python3
"""gt/items-hosszu.jsonl — a HOSSZU KONTEXTUS suite (T21-T25), 5 item x 20 pont.

A D7 merve ~217 000 token. Ez a suite nem „tu a szenakazalban”: azt meri, hogy a modell
a 200k+ ablakban KEPES-E GONDOLKODNI — tavoli tenyeket osszefuzni, teljes koru
aggregaciot vegezni, kesoi felulirast eszrevenni, es osszetett feltetellel szurni.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gt_hosszu as G

I = []
def add(tid, iid, prompt, sema, gt, pont=20, megj="", mezo_tipusok=None):
    I.append(dict(id=iid, teszt=tid, dokumentumok=["D7.md"], prompt=prompt, sema=sema, gt=gt,
                  pont=pont, pontozas="exact", megjegyzes=megj,
                  mezo_tipusok=mezo_tipusok or {}))

L = G.t21_lanc()
NY = G.t24_nyertes()

# ── T21 — harom tavoli teny osszefuzese (0,2 % · 50 % · 99,9 %) ──
add("T21", "T21-01",
    "Az iratarchívum alapján mekkora rezsióradíjjal kellett elszámolni 2024-ben, 2025-ben és "
    "2026-ban, és mennyi a 2026. évi rendkívüli munkaórák együttes munkadíja? Az óradíjak "
    "évről évre az iratban megadott mértékben változnak; a 2026. évi óraszám az iratban "
    "szerepel.",
    {"oradij_2024_ft": "integer", "oradij_2025_ft": "integer", "oradij_2026_ft": "integer",
     "munkadij_2026_ft": "integer"},
    {"oradij_2024_ft": L["oradij_2024"], "oradij_2025_ft": L["oradij_2025"],
     "oradij_2026_ft": L["oradij_2026"], "munkadij_2026_ft": L["munkadij_2026"]},
    megj=f"⛔ A három tény MÉRT mélysége: 0,24 % · 49,85 % · 99,90 %. Hop-hibák (mérve): a 2024-es "
         f"óradíjjal {L['csapda_2024_oradij']}, a 2025-össel {L['csapda_2025_oradij']}, "
         f"összeadott százalékkal {L['csapda_osszeadott_szazalek']} Ft — mind eltér a helyes "
         f"{L['munkadij_2026']} Ft-tól. A lánc szándékosan EGÉSZ értékekre jön ki, hogy a hiba "
         "ne kerekítési műtermék legyen.")

# ── T22 — teljes koru aggregacio: az egesz iratot at kell nezni ──
add("T22", "T22-01",
    f"Hány {G.T22_JELOLO} történt az archívum teljes időszakában, és mennyi ezek együttes "
    "elszámolt költsége forintban? A fogalommeghatározás pontosan megmondja, mi számít ide és "
    "mi nem.",
    {"esemenyek_szama": "integer", "osszkoltseg_ft": "integer"},
    {"esemenyek_szama": G.T22_DARAB, "osszkoltseg_ft": G.t22_ossz()},
    megj=f"⛔ {G.T22_DARAB} valódi esemény szóródik szét a 217k tokenes iraton, mellettük "
         f"{G.T22_ALHANG_DARAB} near-miss tétel (\u201erendkívüli karbantartási igény bejelentése\u201d), "
         "amelyet az 1.2. fogalommeghatározás KIZÁR. Mintavételezéssel ez nem oldható meg.")

# ── T23 — kesoi felulirás: a korai szabály 0,4 %-nál, a felulirás 99,95 %-nál ──
add("T23", "T23-01",
    "Hány munkanapon belül kell kivizsgálni a bejelentett meghibásodást az irat szerint "
    "jelenleg hatályosan? Add meg az eredetileg megállapított határidőt is, továbbá azt a pontot, "
    "amely a változást megállapítja.",
    {"hatalyos_munkanap": "integer", "eredeti_munkanap": "integer",
     "feluliro_pont": "pontszám"},
    {"hatalyos_munkanap": G.T23_KESOI_NAP, "eredeti_munkanap": G.T23_KORAI_NAP,
     "feluliro_pont": G.T23_KESOI_PONT},
    megj="⛔ A 3.4. pont az irat ELEJÉN (0,39 %) mondja ki az 5 munkanapot; a Z.7. pont a "
         "legvégén (99,95 %) helyezi hatályon kívül. Aki csak az elejét olvassa, 5-öt válaszol.",
    mezo_tipusok={"feluliro_pont": "hivatkozas"})

# ── T24 — osszetett feltetel 40 hasonmas rekordon ──
add("T24", "T24-01",
    "A hibajegy-nyilvántartásban pontosan egyetlen olyan hibajegy szerepel, amely EGYSZERRE "
    "kiemelt prioritású ÉS lezáratlan állapotú. Melyik ez? Add meg az azonosítóját, a területét "
    "és a bejelentés napját.",
    {"azonosito": "string", "terulet": "string", "bejelentve": "YYYY-MM-DD"},
    {"azonosito": NY["azonosito"], "terulet": NY["terulet"], "bejelentve": NY["bejelentve"]},
    megj=f"⛔ 40 rekord, ebből több `kiemelt`+`lezárt` és több `normál/emelt`+`lezáratlan` — "
         "csak a KÉT feltétel EGYÜTTES teljesülése azonosít. A tábla a 60,2 %-os mélységben áll.")

# ── T25 — melysegprofil: 5 tu, 5 kontrollalt melysegben ──
add("T25", "T25-01",
    "Add meg az iratarchívumból az alábbi öt adatot. Mindegyik pontosan egyszer szerepel az "
    "iratban; hasonló alakú, de MÁS adatok többször is előfordulnak, ezeket ne keverd össze.",
    {"tetoszigeteles_garancia_lejar": "YYYY-MM-DD", "aggregat_tipusjel": "string",
     "vizora_gyari_szam": "string", "liftkarbantarto_szerzodesszam": "string",
     "tuzjelzo_felulvizsgalat": "YYYY-MM-DD"},
    G.t25_gt(),
    megj="⛔ MÉRT mélységek: 5,03 % · 24,85 % · 49,88 % · 74,91 % · 94,51 %. Mezőnként 4 pont, "
         "tehát ez az item EGYMAGÁBAN mélységprofilt ad. Minden tűhöz van azonos alakú "
         "near-miss zaj az iratban (más garanciadátumok, típusjelek, gyári számok, "
         "szerződésszámok, felülvizsgálati dátumok).")

Path("gt").mkdir(exist_ok=True)
Path("gt/items-hosszu.jsonl").write_text(
    "\n".join(json.dumps(x, ensure_ascii=False) for x in I) + "\n")
print(f"ÖSSZESEN: {len(I)} item, {sum(x['pont'] for x in I)} pont")
for x in I:
    print(f"  {x['id']:8s} {x['pont']:2d} pont · {len(x['gt'])} pontozott mező")
