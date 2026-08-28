#!/usr/bin/env python3
"""gt/items-nehez.jsonl — a NEHÉZ suite (T11–T20), 10 item × 10 pont.

Cél: HIBÁT KIKÉNYSZERÍTENI. A fő korpuszt a Qwen3.8-Flash-Next 98/98-ra megoldotta,
tehát ott nincs fejtér. Ez a suite minden itemnél olyan műveletet kér, amelynél
egy kézenfekvő, de HIBÁS levezetés is létezik — és a hibás út eredménye MÉRT
módon eltér a helyestől (ld. a gt_nehez.py csapda-változatait).

⛔ Minden GT számolt (`gt_nehez.py`), egyetlen érték sincs beírva.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import gt_nehez as G

I = []
def add(tid, iid, dok, prompt, sema, gt, pont=10, megj="", mezo_tipusok=None):
    I.append(dict(id=iid, teszt=tid, dokumentumok=dok, prompt=prompt, sema=sema, gt=gt,
                  pont=pont, pontozas="exact", megjegyzes=megj,
                  mezo_tipusok=mezo_tipusok or {}))

VALASSZ = ("A felsorolt értékkészletű mezőknél PONTOSAN a megadott lehetőségek egyikét add "
           "vissza, szó szerint, kiegészítés nélkül.")
D1 = ["D1.md", "D1-M1.md", "D1-M2.md"]
IDX = G.indexalas_lanc()

# ───────────── T11 — kumulált indexálás lépésenkénti kerekítéssel ─────────────
add("T11", "T11-01", D1 + ["D6.md"],
    "A Megállapodás 7. pontja szerint indexáld a havi nettó bérleti díjat. Add meg a díjat "
    "mindhárom indexálási időpontban, továbbá azt, hogy melyik naptári év indexét kellett a "
    "felső határra levágni. " + VALASSZ,
    {"dij_2027_01_01_ft": "integer", "dij_2028_01_01_ft": "integer",
     "dij_2029_01_01_ft": "integer", "plafonozott_ev": "integer",
     "kerekites_modja": "minden lépésben, és a kerekített összeg a következő évi alap | "
                        "csak a lánc végén, egyetlen alkalommal | nincs kerekítési szabály"},
    {"dij_2027_01_01_ft": IDX[0]["dij_ft"], "dij_2028_01_01_ft": IDX[1]["dij_ft"],
     "dij_2029_01_01_ft": IDX[2]["dij_ft"],
     "plafonozott_ev": next(s["index_eve"] for s in IDX if s["plafonozva"]),
     "kerekites_modja": "minden lépésben, és a kerekített összeg a következő évi alap"},
    megj=f"⛔ MÉRT csapdák: csak a végén kerekítve {G.indexalas_csak_veges_kerekitessel()} Ft, "
         f"plafon nélkül {G.indexalas_plafon_nelkul()} Ft — mindkettő ELTÉR a helyes "
         f"{IDX[-1]['dij_ft']} Ft-tól. A bázis a 2. sz. módosításé, nem az alapszerződésé.")

# ───────────── T12 — ellentmondás feloldása értelmezési sorrenddel ─────────────
add("T12", "T12-01", D1 + ["D6.md"],
    "Hány napos a Bérlő felmondási ideje a Megállapodás szerint? A Megállapodás két helyen is "
    "rendelkezik erről, egymástól eltérően. Add meg a ténylegesen irányadó értéket, azt az iratot, "
    "amely az ellentmondást eldönti, és azt, hogy az Alapszerződés megállapít-e rendes felmondási "
    "időt. " + VALASSZ,
    {"felmondasi_ido_nap": "integer",
     "donto_irat": "a Megállapodás 1. sz. melléklete | a Megállapodás törzsszövege | "
                   "az Alapszerződés",
     "alapszerzodes_megallapit_e": "boolean"},
    {"felmondasi_ido_nap": G.FELMONDAS_MELLEKLET_NAP,
     "donto_irat": "a Megállapodás 1. sz. melléklete",
     "alapszerzodes_megallapit_e": G.ALAPSZERZODES_REND_FELMONDAS},
    megj=f"⛔ A 2.1. sorrend a MELLÉKLETET teszi a törzsszöveg ELÉ — a kézenfekvő feltevés "
         f"({G.FELMONDAS_TORZS_NAP} nap) rossz. Csali: a D1 11.2. pontjának 60 napja a "
         "RENDKÍVÜLI felmondás díjkésedelmi küszöbe, nem felmondási idő.")

# ───────────── T13 — számmal és betűvel eltérő összeg ─────────────
add("T13", "T13-01", ["D6.md"],
    "Mekkora belépési díjat köteles a Bérlő megfizetni? Az iratban az összeg számmal és betűvel "
    "is szerepel. Add meg a ténylegesen fizetendő összeget, a számmal kiírt összeget, és azt, "
    "hogy a kettő eltér-e egymástól. " + VALASSZ,
    {"fizetendo_ft": "integer", "szammal_kiirt_ft": "integer", "elter_e": "boolean",
     "iranyado": "a betűvel kiírt összeg | a számmal kiírt összeg | a kettő átlaga"},
    {"fizetendo_ft": G.BELEPESI_DIJ_BETUVEL, "szammal_kiirt_ft": G.BELEPESI_DIJ_SZAMMAL,
     "elter_e": True, "iranyado": "a betűvel kiírt összeg"},
    megj="⛔ A modellek a SZÁMOT olvassák; a 4.4. pont a betűvel kiírtat teszi irányadóvá. "
         "A betűvel kiírt alak magyarul kötőjeles összetétel, ezt is helyesen kell értelmezni.")

# ───────────── T14 — négyszintű, egymásba ágyazott kivétel ─────────────
add("T14", "T14-01", ["D6.md"],
    "A bérlemény tartószerkezete megrepedt a Bérlő présgépének rezgésétől. Az irat alapján kit "
    "terhel a javítás költsége? Add meg azt a pontot is, amely a kérdést eldönti, és az előzetes "
    "írásbeli engedély keltét. " + VALASSZ,
    {"koltseget_viseli": "Bérbeadó | Bérlő | a Felek megosztva",
     "donto_pont": "pontszám", "engedely_datuma": "YYYY-MM-DD"},
    {"koltseget_viseli": "Bérbeadó", "donto_pont": "5.4", "engedely_datuma": "2026-05-04"},
    megj="⛔ Négy szint: (1) főszabály Bérlő → (2) tartószerkezet: Bérbeadó → (3) a Bérlő "
         "technológiája okozta: Bérlő → (4) a Bérbeadó írásban engedélyezte: MÉGSEM a Bérlő. "
         "Aki a 3. szinten megáll, „Bérlő”-t válaszol. Az engedély tényét az 5.5. pont adja.",
    mezo_tipusok={"donto_pont": "hivatkozas"})

# ───────────── T15 — vegyes devizás aggregáció rögzített árfolyammal ─────────────
K = G.eves_uzemeltetesi_koltseg()
add("T15", "T15-01", ["D6.md"],
    "Mennyi az üzemeltetési díjak együttes ÉVES nettó összege forintban? Add meg az alkalmazott "
    "árfolyamot és az üzemeltetési alapdíj havi forintösszegét is.",
    {"eves_osszeg_ft": "integer", "alkalmazott_arfolyam": "number",
     "uzemeltetesi_alapdij_ft_ho": "integer"},
    {"eves_osszeg_ft": K["osszesen"], "alkalmazott_arfolyam": float(G.ARFOLYAM),
     "uzemeltetesi_alapdij_ft_ho": K["ft_ho"]},
    megj=f"⛔ MÉRT csapdák: a 3.5. pont tájékoztató árfolyamával "
         f"{G.eves_uzemeltetesi_koltseg(G.ARFOLYAM_CSALI)['osszesen']} Ft jön ki; a biztonsági "
         f"szolgálat díja ÉVES, nem havi; az alapdíj m²-re ÉS hónapra vetített.")

# ───────────── T16 — banki nap ≠ munkanap ─────────────
b = G.hatarido_banki_nap(G.T16_KEZHEZVETEL, G.T16_NAPOK)
m = G.hatarido_munkanapban(G.T16_KEZHEZVETEL, G.T16_NAPOK)
add("T16", "T16-01", ["D2.md", "D6.md"],
    f"Az Üzemeltető elszámolását a Bérlő {G.T16_KEZHEZVETEL.year}. "
    f"{['január','február','március','április','május','június','július','augusztus','szeptember','október','november','december'][G.T16_KEZHEZVETEL.month-1]} "
    f"{G.T16_KEZHEZVETEL.day}-én vette kézhez. Mely napon jár le a fizetési határidő? "
    "Add meg azt is, hogy MUNKANAPBAN számolva mely napra esne a határidő, és mi okozza az "
    "eltérést. " + VALASSZ,
    {"hatarido": "YYYY-MM-DD", "munkanapban_szamolva": "YYYY-MM-DD",
     "elteres_oka": "a naptári év utolsó munkanapja nem banki nap | "
                    "az áthelyezett munkanap nem banki nap | "
                    "a két számítás nem tér el egymástól"},
    {"hatarido": b.isoformat(), "munkanapban_szamolva": m.isoformat(),
     "elteres_oka": "a naptári év utolsó munkanapja nem banki nap"},
    megj=f"⛔ MÉRVE: banki nap szerint {b}, munkanap szerint {m} — a kettő ÉVHATÁRT lép át. "
         "A munkarend a D2 2. sz. mellékletéből jön, a banki nap fogalma a D6 6.2-ből: "
         "két külön iratból kell összerakni.")

# ───────────── T17 — anafora három fél között ─────────────
add("T17", "T17-01", ["D6.md"],
    "Melyik Felet terheli a tűzvédelmi felülvizsgálat megrendelése és költségviselése? "
    "Add meg a fél teljes nevét és a Megállapodás szerinti szerepét. " + VALASSZ,
    {"fel_neve": "string", "szerepe": "Bérbeadó | Bérlő | Üzemeltető"},
    {"fel_neve": "Delta-Ipari Szolgáltató Zrt.", "szerepe": "Bérlő"},
    megj="⛔ A 8.2. pont nem nevezi meg a felet, hanem az 1.1. pont felsorolási SORRENDJÉRE "
         "utal vissza („másodikként nevez meg”). A közvetlenül utána álló 8.3. pont az "
         "Üzemeltetőről szól — ez a legközelebbi, de HIBÁS előzmény.")

# ───────────── T18 — irányt jelölő esetragok ─────────────
add("T18", "T18-01", ["D6.md"],
    "Az elszámolási rendben ki állítja ki az elszámolást, ki a címzettje, és a Bérbeadó melyik "
    "Félnél élhet vele szemben észrevétellel? " + VALASSZ,
    {"kiallitja": "Bérbeadó | Bérlő | Üzemeltető",
     "cimzettje": "Bérbeadó | Bérlő | Üzemeltető",
     "berbeado_eszrevetel_cimzettje": "Bérbeadó | Bérlő | Üzemeltető"},
    {"kiallitja": "Üzemeltető", "cimzettje": "Bérlő",
     "berbeado_eszrevetel_cimzettje": "Üzemeltető"},
    megj="⛔ A 9.1. mondat KÖZBEVETÉSSEL fordított szórendű („Az elszámolást — a Bérlő részére — "
         "az Üzemeltető állítja ki”), a 9.2. pedig „az Üzemeltetőnél — és nem a Bérlőnél” "
         "szerkezettel tagad. A -nál/-nél és a -t tárgyrag dönti el az irányt, nem a szórend.")

# ───────────── T19 — kontrafaktuális a verzióláncon ─────────────
add("T19", "T19-01", D1,
    "Tegyük fel, hogy a felek az 1. sz. módosítást NEM kötötték volna meg, minden más irat "
    "változatlan. Mekkora lenne a havi nettó bérleti díj 2026. augusztus 31-én, illetve "
    "2026. szeptember 15-én? Add meg azt is, hogy a 2. sz. módosítás hatálybalépését érinti-e "
    "az 1. sz. módosítás hiánya.",
    {"dij_2026_08_31_ft": "integer", "dij_2026_09_15_ft": "integer",
     "m2_hatalyat_erinti_e": "boolean"},
    {"dij_2026_08_31_ft": 1850000, "dij_2026_09_15_ft": 2100000,
     "m2_hatalyat_erinti_e": False},
    megj="⛔ A tényleges (nem kontrafaktuális) válasz augusztus 31-re 1 980 000 Ft — aki a "
         "T8-at „bemagolta”, ezt adja. Az M2 3. pontja önállóan, 2026-09-01-től hatályos, "
         "az M1 hiánya nem érinti; az M2 5. pontja az M1 4. pontját (rezsi) helyezi hatályon "
         "kívül, a díjat nem.")

# ───────────── T20 — eldönthetetlen, csábító szomszéddal ─────────────
add("T20", "T20-01", ["D6.md"],
    "Mekkora az Üzemeltető felelősségének felső határa a bérleményben bekövetkezett SZEMÉLYI "
    "SÉRÜLÉSBŐL eredő károk esetén? Ha az irat erről nem rendelkezik, azt jelöld — ne találgass. "
    "Add meg azt is, hogy vagyoni károkra van-e felső határ, és ha igen, mekkora.",
    {"szemelyi_serules_plafon": "string", "vagyoni_karra_van_plafon": "boolean",
     "vagyoni_plafon_ft": "integer"},
    {"szemelyi_serules_plafon": "nincs az iratban", "vagyoni_karra_van_plafon": True,
     "vagyoni_plafon_ft": G.UZEMELTETO_VAGYONI_PLAFON_FT},
    megj="⛔ A 10.2. pont KIFEJEZETTEN a vagyoni károkra korlátoz. A személyi sérülésről az "
         "irat hallgat — de a plafon értéke ott van két sorral feljebb. Ez a suite "
         "kitalálás-mérője.")

Path("gt").mkdir(exist_ok=True)
Path("gt/items-nehez.jsonl").write_text(
    "\n".join(json.dumps(x, ensure_ascii=False) for x in I) + "\n")
print(f"ÖSSZESEN: {len(I)} item, {sum(x['pont'] for x in I)} pont")
for x in I:
    print(f"  {x['id']:8s} {x['pont']:2d} pont · {len(x['gt']):d} pontozott mező · "
          f"dokumentumok: {', '.join(x['dokumentumok'])}")
