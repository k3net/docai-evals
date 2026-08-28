#!/usr/bin/env python3
"""items.jsonl — az 50 mérési item előállítása.

⛔ A számolt ground truth-t a gt_szamolo / munkarend / gen_d3 modulok adják, NEM kézzel írva.
Séma (a magyarkieevalterv §4 szerint): id, teszt, dokumentum(ok), prompt, sema, gt, pontozas.
"""
import json, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from gt_szamolo import kotber, ITEM_NAPOK
from munkarend import hatarido_munkanap, hatarido_naptari, munkanap
from datetime import timedelta

I = []
def add(tid, iid, dokumentumok, prompt, sema, gt, pont, pontozas="exact", megj="",
        mezo_tipusok=None):
    I.append(dict(id=iid, teszt=tid, dokumentumok=dokumentumok, prompt=prompt,
                  sema=sema, gt=gt, pont=pont, pontozas=pontozas, megjegyzes=megj,
                  mezo_tipusok=mezo_tipusok or {}))

# ⛔ A kalibrációs kör (08-27) tanulsága: a SZABAD SZÖVEGES mezőket nem lehet exact-match-el
# pontozni — a helyes, de bőbeszédű válasz is 0-t kapott. Ahol zárt értékkészlet létezik,
# ott ÉRTÉKKÉSZLETET adunk (a csapda megmarad: melyik értéket választja), ahol pedig
# pontszám a válasz, ott `hivatkozas` mezőtípus + normalizálás.
VALASSZ = ("A felsorolt értékkészletű mezőknél PONTOSAN a megadott lehetőségek egyikét add "
           "vissza, szó szerint, kiegészítés nélkül.")

D1 = ["D1.md", "D1-M1.md", "D1-M2.md"]

# ---------------- T1 — indexálási záradék (1 nagy item, 10 pont) ----------------
add("T1", "T1-01", D1,
    "A szerződés indexálási záradéka alapján töltsd ki a JSON-t. A ténylegesen kikötött, "
    "hatályos feltételeket add meg — a mellékletben szereplő iratminta adatait ne vedd figyelembe. "
    "Az `ertelmezes` mezőben egy-két mondatban írd le, mi történik 2028. január 1-jén, "
    "ha a 2027-es éves fogyasztóiár-index −0,4 %. " + VALASSZ,
    {"index_tipusa": "KSH éves fogyasztóiár-index | MNB inflációs cél | EKB harmonizált "
                     "fogyasztóiár-index | nincs az iratban",
     "bazis_idoszak": "előző naptári év | előző 12 naptári hónap | megelőző naptári félév | "
                      "a szerződés aláírásának éve",
     "elso_indexalas": "YYYY-MM-DD",
     "plafon_szazalek": "number",
     "negativ_index_kezelese": "a díj nem csökken | a díj csökken | az irat nem rendelkezik róla",
     "kerekites": "ezer forintra | száz forintra | tíz forintra | nincs kerekítési szabály",
     "ertelmezes": "string"},
    {"index_tipusa": "KSH éves fogyasztóiár-index", "bazis_idoszak": "előző naptári év",
     "elso_indexalas": "2027-01-01", "plafon_szazalek": 6,
     "negativ_index_kezelese": "a díj nem csökken", "kerekites": "ezer forintra",
     "ertelmezes": "__BIRO__"},
    10, "exact+biro",
    "6 exakt mező × 1,5 pont + ertelmezes LLM-bíróval 0–1 pont. Csapdák: 8→6 % felülírás (M1 3. pont), "
    "csali-melléklet (5 %, 2026-01-01, száz forint), bázisidőszak vs. díjbázis.")

# ---------------- T2 — kötbér-kalkuláció (5 item × 2 pont) ----------------
for k, napok in enumerate(ITEM_NAPOK, 1):
    g = kotber(napok)
    add("T2", f"T2-{k:02d}", ["D2.md"],
        f"A vállalkozó {napok} naptári napot késett a teljesítéssel. Mekkora késedelmi kötbér "
        f"követelhető tőle? A kötbér mértékét százalékban és forintban is add meg. "
        f"Az `alkalmazott_plafon` mező akkor és csak akkor igaz, ha a szerződéses felső határ "
        f"a ténylegesen követelhető összeget CSÖKKENTETTE a napok száma alapján számított "
        f"nyers értékhez képest.",
        {"kotber_szazalek": "number", "kotber_osszeg_ft": "integer", "alkalmazott_plafon": "boolean"},
        {"kotber_szazalek": g["kotber_szazalek"], "kotber_osszeg_ft": g["kotber_osszeg_ft"],
         "alkalmazott_plafon": g["alkalmazott_plafon"]},
        2, "exact",
        "Csapda: bruttó (15 748 000) vs. nettó (12 400 000) alap; hibás teljesítési kötbér (10 %) "
        "összekeverése a késedelmivel; a 15 %-os plafon.")

# ---------------- T3 — határidő-aritmetika (5 item × 2 pont) ----------------
T3 = [
    ("T3-01", date(2026, 10, 19), 15, "munkanap",
     "A vállalkozó számláját 2026. október 19-én, hétfőn vettük kézhez. A szerződés 3.4. pontja "
     "szerinti fizetési határidő mely napon jár le?"),
    ("T3-02", date(2026, 7, 31), 15, "munkanap",
     "A vállalkozó számláját 2026. július 31-én, pénteken vettük kézhez. A szerződés 3.4. pontja "
     "szerinti fizetési határidő mely napon jár le? A 2. sz. melléklet szerinti munkarendet alkalmazd."),
    ("T3-03", date(2026, 10, 19), 8, "naptári nap",
     "A vállalkozó számláját 2026. október 19-én, hétfőn vettük kézhez. A szerződés 3.5. pontja "
     "szerinti kifogásolási határidő mely napon jár le?"),
    ("T3-04", date(2026, 12, 18), 10, "munkanap",
     "A hibabejelentést a vállalkozó 2026. december 18-án, pénteken vette kézhez. A szerződés 7.4. pontja "
     "szerinti hibajavítási határidő mely napon jár le?"),
]
for iid, kez, n, mod, prompt in T3:
    d = hatarido_munkanap(kez, n) if mod == "munkanap" else hatarido_naptari(kez, n)
    add("T3", iid, ["D2.md"], prompt,
        {"hatarido": "YYYY-MM-DD", "szamitas_alapja": "munkanap | naptári nap"},
        {"hatarido": d.isoformat(), "szamitas_alapja": mod}, 2, "exact",
        "Csapda: a 3.4. munkanap, a 3.5. naptári nap; a kézhezvétel napja nem számít bele; "
        "áthelyezett munkanap (2026-08-08 szombat munkanap, 2026-08-21 péntek pihenőnap).")
# T3-05: visszafelé számolás
d = date(2026, 11, 30); c = 0
while c < 5:
    d -= timedelta(days=1)
    if munkanap(d):
        c += 1
add("T3", "T3-05", ["D2.md"],
    "A teljesítési határidő 2026. november 30. A szerződés 7.6. pontja szerint a vállalkozónak "
    "legalább 5 munkanappal a teljesítés előtt készre jelentést kell küldenie. Legkésőbb mely napon "
    "küldheti el a készre jelentést?",
    {"hatarido": "YYYY-MM-DD", "szamitas_alapja": "munkanap | naptári nap"},
    {"hatarido": d.isoformat(), "szamitas_alapja": "munkanap"}, 2, "exact",
    "Csapda: visszafelé kell számolni.")

# ---------------- T4 — ragozott entitások (5 item × 2 pont) ----------------
add("T4", "T4-01", ["D4.md"],
    "Sorold fel a jegyzőkönyvben és az e-mail-láncban szereplő TERMÉSZETES SZEMÉLYEKET, "
    "mindegyiket alanyesetben, a dokumentumban előforduló legteljesebb névalakjukkal. "
    "Csak valódi szereplőket sorolj fel.",
    {"szemelyek": "string[]"},
    {"szemelyek": ["Kovácsné Tóth Ilona", "Szabó Márton", "Hegyi Ambrus", "dr. Szalay Bertalan"]},
    2, "lista",
    "Csapda: az Arany Janos utcanevben rejlo szemelynev NEM szereplo. A Kovacsne ragozva szerepel, "
    "a teljes alak a jegyzokonyv alairasanal. A dr. Szalayt targyesetben all.")
add("T4", "T4-02", ["D4.md"],
    "Sorold fel a dokumentumban szereplő CÉGEKET, alanyesetben, a dokumentumban előforduló "
    "legteljesebb cégnévvel.",
    {"cegek": "string[]"},
    {"cegek": ["Delta-Ipari Szolgáltató Zrt.", "Hegyi és Társa Építőipari Bt."]},
    2, "lista", "Csapda: a Hegyi es Tarsa Bt.-vel ragozott, roviditett alak.")
add("T4", "T4-03", ["D4.md"],
    "Ki az átadó és ki az átvevő az átadás-átvételi jegyzőkönyv szerint? "
    "A természetes személy nevét alanyesetben, teljes alakban add meg.",
    {"atado": "string", "atvevo": "string"},
    {"atado": "Hegyi Ambrus", "atvevo": "Kovácsné Tóth Ilona"}, 2, "exact",
    "Az aláírás-blokkból olvasható ki.")
add("T4", "T4-04", ["D4.md"],
    "Szerepel-e a dokumentumban olyan személy, akinek a neve „Arany János”? Válaszolj a JSON szerint.",
    {"szerepel": "boolean", "indok": "string"},
    {"szerepel": False, "indok": "__BIRO_NEM_PONTOZOTT__"}, 2, "exact",
    "Csapda: az „Arany János utcai telephely” utcanév, nem személy.")
add("T4", "T4-05", ["D4.md"],
    "A dokumentumban a „szabó” szó két különböző jelentésben fordul elő. Add meg, hogy melyik "
    "előfordulás vezetéknév és melyik köznév. A vezetéknévi előfordulásnál add meg a teljes nevet.",
    {"vezeteknev_teljes_alak": "string", "koznevi_elofordulas_kontextusa": "string"},
    {"vezeteknev_teljes_alak": "Szabó Márton",
     "koznevi_elofordulas_kontextusa": "__BIRO_NEM_PONTOZOTT__"}, 2, "exact",
    "Csak a vezeteknev_teljes_alak pontozott.")

# ================= T5 — számla-KIE (5 item × 2 pont) =================
add("T5", "T5-01", ["D3.md"],
    "A végszámlán (SZ-2026/0912) ellenőrizd, hogy a feltüntetett fizetendő végösszeg megegyezik-e "
    "a tételekből és a levonandó előlegből számított értékkel. Ha nem, add meg az eltérés forintban "
    "kifejezett nagyságát és az irányát.",
    {"vegosszeg_egyezik": "boolean", "elteres_ft": "integer",
     "iranya": "több van feltüntetve | kevesebb van feltüntetve | nincs eltérés"},
    {"vegosszeg_egyezik": False, "elteres_ft": 27000, "iranya": "több van feltüntetve"},
    2, "exact", "A tételek bruttó összege 6 872 666, ebből a levonandó előleg 3 937 000, "
    "a számított fizetendő 2 935 666, a feltüntetett 2 962 666.")

add("T5", "T5-02", ["D3.md"],
    "A végszámla (SZ-2026/0912) 3. tétele nulla áfát tartalmaz. Milyen jogcímen? "
    "Add meg a jogcímet és azt, hogy alanyi adómentességről van-e szó. " + VALASSZ,
    {"jogcim": "fordított adózás | alanyi adómentesség | tárgyi adómentesség | "
               "Közösségen belüli adómentes értékesítés | nincs az iratban",
     "alanyi_adomentes": "boolean"},
    {"jogcim": "fordított adózás", "alanyi_adomentes": False},
    2, "exact", "Csapda: a részszámla 4. tétele AAM, a végszámla 3. tétele fordított adózás. "
    "A kettő nem ugyanaz.")

add("T5", "T5-03", ["D3.md"],
    "Sorold fel a részszámla (SZ-2026/0631) tételeit az alkalmazott áfakulcs vagy jogcím szerint. "
    "Minden tételnél add meg a nettó összeget forintban, egész számként.",
    {"tetelek": "[{megnevezes, netto_ft, afakulcs_vagy_jogcim}]"},
    {"tetelek": [
        {"netto_ft": 3100000, "afakulcs_vagy_jogcim": "27%"},
        {"netto_ft": 1200000, "afakulcs_vagy_jogcim": "27%"},
        {"netto_ft": 100000, "afakulcs_vagy_jogcim": "5%"},
        {"netto_ft": 250000, "afakulcs_vagy_jogcim": "AAM"}]},
    2, "lista", "Négy áfa-rezsim: 27 %, 27 %, 5 %, AAM. A megnevezést nem pontozzuk.")

add("T5", "T5-04", ["D3.md"],
    "Mekkora a végszámla (SZ-2026/0912) 2. tételének egységára és mennyisége? "
    "Az egységárat számként add meg, tizedesponttal.",
    {"egysegar": "number", "mennyiseg": "number"},
    {"egysegar": 1234567.5, "mennyiseg": 2},
    2, "exact", "Magyar formátum: 1 234 567,50 — szóközös ezres tagolás, tizedesvessző.")

add("T5", "T5-05", ["D3.md"],
    "Mekkora az előlegszámla (SZ-2026/0417) bruttó összege, és a nettó vállalkozói díj hány "
    "százalékának felel meg a nettó előleg? A nettó vállalkozói díj 12 400 000 Ft.",
    {"eloleg_brutto_ft": "integer", "eloleg_szazalek": "number"},
    {"eloleg_brutto_ft": 3937000, "eloleg_szazalek": 25},
    2, "exact", "3 100 000 / 12 400 000 = 25 %.")

# ================= T6 — kereszthivatkozás (5 item × 2 pont) =================
add("T6", "T6-01", D1,
    "Pontosan mekkora összeg a szerződés 9.4. pontjában hivatkozott Óvadék, és mely pontok láncán "
    "jutottál el hozzá? A láncot a hivatkozott pontok sorrendjében add meg.",
    {"ertek_ft": "integer", "hivatkozasi_lanc": "string[]"},
    {"ertek_ft": 900000, "hivatkozasi_lanc": ["9.4", "4.5", "1. sz. melléklet 2. pont"]},
    2, "exact+lista", "Csapda: az iratmintában 1 500 000 Ft kaució szerepel — az nem ez.",
    {"hivatkozasi_lanc": "hivatkozas"})

add("T6", "T6-02", D1,
    "Mekkora a szerződés 9.2. pontja szerinti bankgarancia összege a jelenleg hatályos bérleti díj "
    "alapján? Add meg a számítás alapját is. " + VALASSZ,
    {"ertek_ft": "integer",
     "szamitas_alapja": "a 4.1. pont szerinti Díj háromszorosa | a 4.1. pont szerinti Díj "
                        "kétszerese | a 4.5. pont szerinti Óvadék háromszorosa | "
                        "az éves díj huszonöt százaléka"},
    {"ertek_ft": 6300000, "szamitas_alapja": "a 4.1. pont szerinti Díj háromszorosa"},
    2, "exact", "A 9.2. a mindenkor hatályos Díj háromszorosa; a hatályos Díj a 2. sz. módosítás "
    "3. pontja szerint 2 100 000 Ft, tehát 3 × 2 100 000 = 6 300 000.")

add("T6", "T6-03", D1,
    "A szerződés 4.4. pontja szerint mi a késedelmi kamat alapja: a nettó vagy a bruttó havi díj? "
    "A `tovabb_hivatkozott_pont` mezőben azt a MÁSIK pontot add meg, amelyre a 4.4. pont a kamat "
    "alapjának meghatározásakor továbbutal — nem magát a 4.4. pontot.",
    {"kamat_alapja": "nettó | bruttó", "tovabb_hivatkozott_pont": "pontszám"},
    {"kamat_alapja": "nettó", "tovabb_hivatkozott_pont": "4.2"},
    2, "exact", "A 4.4. a 4.2. pont szerinti Díjra utal, ami nettó. ⛔ A kalibrációban a "
    "`hivatkozott_pont` név félreérthető volt: a modell a kérdésben szereplő 4.4-et adta vissza.",
    {"tovabb_hivatkozott_pont": "hivatkozas"})

add("T6", "T6-04", D1,
    "A szerződés 9.6. pontja hivatkozik egy másik pontra. Létezik-e az a pont a szerződésben? "
    "Ha nem, jelezd a hivatkozási hibát.",
    {"hivatkozott_pont": "string", "letezik": "boolean", "eszrevetel": "string"},
    {"hivatkozott_pont": "11.4", "letezik": False, "eszrevetel": "__BIRO_NEM_PONTOZOTT__"},
    2, "exact", "A 11. pont csak 11.1–11.3 alpontokat tartalmaz.",
    {"hivatkozott_pont": "hivatkozas"})

add("T6", "T6-05", D1,
    "Mekkora a szerződés 8.3. pontja szerinti éves felújítási keretösszeg, és melyik dokumentumrész "
    "tartalmazza a konkrét értéket?",
    {"ertek_ft": "integer", "forras": "string"},
    {"ertek_ft": 1200000, "forras": "1. sz. melléklet 4. pont"},
    2, "exact", "", {"forras": "hivatkozas"})


# ================= T7 — tagadás, kivétel, hatókör (8 állítás × 1 pont + indoklás 2 pont) =================
T7_ALLITASOK = [
    ("T7-01", "A bérbeadó felel a bérlő ingóságaiban esett kárért, ha a kárt a bérlő szándékos "
              "magatartása okozta.", "HAMIS", "10.2"),
    ("T7-02", "Ha a kárt a bérbeadó súlyos gondatlansága okozta, a bérbeadó felel a bérlő "
              "ingóságaiban esett kárért.", "IGAZ", "10.2"),
    ("T7-03", "A bérlő a bérlemény használatának szüneteltetése alatt minden esetben mentesül "
              "a díjfizetés alól.", "HAMIS", "10.3"),
    ("T7-04", "Ha a szünetelés a bérbeadónak felróható okból 20 napig tart, a bérlő mentesül "
              "a díjfizetés alól.", "IGAZ", "10.3"),
    ("T7-05", "A felek utóbb nem korlátozhatják a kártérítés összegét.", "HAMIS", "10.4"),
    ("T7-06", "A bérbeadó felel a bérlő elmaradt üzleti hasznáért.", "HAMIS", "10.5"),
    ("T7-07", "A bérlő köteles vagyonbiztosítást kötni a bérleményben tárolt saját ingóságaira.",
              "IGAZ", "10.6"),
    ("T7-08", "A bérbeadó felel a bérlő alvállalkozója által okozott kárért.",
              "NEM DÖNTHETŐ EL", "a 10. pont az alvállalkozóról nem rendelkezik"),
]
for iid, allitas, valasz, alap in T7_ALLITASOK:
    add("T7", iid, D1,
        "A szerződés 10. pontja (Felelősség és kártérítés) alapján döntsd el az alábbi állítást. "
        "Ha az irat alapján nem dönthető el, azt jelöld — ne találgass.\n\n"
        f"ÁLLÍTÁS: „{allitas}”",
        {"itelet": "IGAZ | HAMIS | NEM DÖNTHETŐ EL"},
        {"itelet": valasz}, 1, "exact",
        f"Alap: {alap}. A NEM DÖNTHETŐ EL kategória a csapda: a túl magabiztos modell itt bukik.")

add("T7", "T7-09", D1,
    "A szerződés 10. pontja alapján indokold meg egy-két mondatban, miért nem felel a bérbeadó "
    "a bérlő elmaradt üzleti hasznáért, és van-e ez alól kivétel. Hivatkozz a konkrét pontra.",
    {"indoklas": "string", "hivatkozott_pont": "string"},
    {"indoklas": "__BIRO__", "hivatkozott_pont": "10.5"},
    2, "biro", "LLM-bíró 0-5 rubrika, 2 pontra skálázva. A hivatkozott_pont hivatkozás-egyezéssel.",
    {"hivatkozott_pont": "hivatkozas"})

# ================= T8 — időbeli hatály és verziólánc (5 item × 2 pont) =================
T8 = [
    ("T8-01", "2025. június 1.", 1850000, "alapszerződés 4.1. pont"),
    ("T8-02", "2026. március 15.", 1850000, "alapszerződés 4.1. pont"),
    ("T8-03", "2026. május 20.", 1980000, "1. sz. módosítás 2. pont"),
    ("T8-04", "2026. augusztus 31.", 1980000, "1. sz. módosítás 2. pont"),
    ("T8-05", "2026. szeptember 15.", 2100000, "2. sz. módosítás 3. pont"),
]
for iid, nap, ertek, forras in T8:
    add("T8", iid, D1,
        f"Mekkora a havi nettó bérleti díj {nap} napján? Az alapszerződést és mindkét módosítást "
        "együtt kell olvasni. Add meg azt a dokumentumrészt is, amely az adott napon hatályos "
        "összeget megállapítja. " + VALASSZ,
        {"ertek_ft": "integer",
         "hatalyos_forras": "alapszerződés 4.1. pont | 1. sz. módosítás 2. pont | "
                            "2. sz. módosítás 3. pont"},
        {"ertek_ft": ertek, "hatalyos_forras": forras}, 2, "exact",
        "Csavar: a 2. sz. módosítást 2026-10-05-én írták alá, de a 3. pontja 2026-09-01-től "
        "visszamenőleges hatályú.")

# ================= T9 — csali-rezisztencia (5 item × 2 pont) =================
NINCS = "nincs az iratban"
add("T9", "T9-01", ["D5.md"],
    "Mennyi a bérlő (Delta-Ipari Szolgáltató Zrt.) cégjegyzékszáma?",
    {"valasz": "string"}, {"valasz": NINCS}, 2, "exact",
    "⛔ A bérlő cégjegyzékszáma SEHOL nem szerepel az iratcsomagban. A bérbeadóé (02-09-118423) "
    "és a vállalkozóé (02-06-207714) igen — ezek a csalik.")
add("T9", "T9-02", ["D5.md"],
    "Mekkora a kaució összege az 1. sz. mellékletben szereplő iratminta szerint?",
    {"valasz_ft": "integer"}, {"valasz_ft": 1500000}, 2, "exact",
    "Az iratminta értéke — itt EZT kérjük, tehát a helyes válasz a csali-érték.")
add("T9", "T9-03", ["D5.md"],
    "Mekkora a felek között ténylegesen kikötött Óvadék összege?",
    {"valasz_ft": "integer"}, {"valasz_ft": 900000}, 2, "exact",
    "⛔ A T9-02 párja: ugyanaz a fogalom két értékkel. Aki a T9-02-re 900 000-t vagy a T9-03-ra "
    "1 500 000-t ad, összekeverte az iratmintát a szerződéssel.")
add("T9", "T9-04", ["D5.md"],
    "Hány munkavállalót foglalkoztat a bérlő a bérleményben?",
    {"valasz": "string"}, {"valasz": NINCS}, 2, "exact",
    "⛔ Az iratcsomag létszámadatot nem tartalmaz.")
add("T9", "T9-05", ["D5.md"],
    "Mekkora a bérleti díj indexálásának felső határa a felek között hatályos szerződés szerint?",
    {"plafon_szazalek": "number"}, {"plafon_szazalek": 6}, 2, "exact",
    "⛔ Három érték versenyez: 8 % (törzsszöveg, felülírva), 6 % (M1 3. pont, HATÁLYOS), "
    "5 % (iratminta, csali).")

# ================= T10 — szinonim tű a szénakazalban (5 item × 2 pont) =================
add("T10", "T10-01", ["D5.md"],
    "Az iratcsomag alapján: mennyivel és mely nappal emelkedik évente a parkolóhely-használati "
    "hozzájárulás?",
    {"emeles_szazalek": "number", "idopont": "string"},
    {"emeles_szazalek": 4, "idopont": "március 1."}, 2, "exact",
    "A szöveg „éves korrekció”-t mond, nem „emelés”-t. Near-miss: az „emelés” szó a házirend "
    "teheremelő-szabályában szerepel. Pozíció: a csomag elején (~2,5 %).")
add("T10", "T10-02", ["D5.md"],
    "Mikor van a gépészeti karbantartási ciklus befejezésének végső napja?",
    {"idopont": "string"}, {"idopont": "szeptember 15."}, 2, "exact",
    "A szöveg „zárónap”-ot mond. Near-miss: a „befejezés” szó a takarítási rendben szerepel. "
    "Pozíció: a csomag negyedénél (~25 %).")
add("T10", "T10-03", ["D5.md"],
    "Mennyit kell havonta fizetni a szemétszállításért?",
    {"osszeg_ft": "integer"}, {"osszeg_ft": 46000}, 2, "exact",
    "A szöveg „hulladékkezelési hozzájárulás”-t mond. Near-miss: a „szállítás” szó a beléptetési "
    "szabályzatban szerepel. Pozíció: a csomag legvégén (~99,5 %).")
add("T10", "T10-04", ["D5.md"],
    "Az iratcsomag alapján mekkora pénzösszeget kell a bérlőnek letétbe helyeznie a szerződés "
    "biztosítékául, és hogyan nevezi ezt a szerződés?",
    {"osszeg_ft": "integer", "megnevezes": "string"},
    {"osszeg_ft": 900000, "megnevezes": "Óvadék"}, 2, "exact",
    "A kérdés „letét”-et mond; a szerződés „Óvadék”-ot. Near-miss: a „letét” szó az iratkezelési "
    "tájékoztatóban szerepel, más jelentésben.")
add("T10", "T10-05", ["D5.md"],
    "Az iratcsomag alapján hol találom meg azt a szabályt, amely a sűrített levegős hálózat "
    "cseréjének műszaki paramétereit rögzíti? Add meg a szakasz címét vagy pontszámát.",
    {"forras_szakasz": "string"},
    {"forras_szakasz": "M1"}, 2, "exact",
    "A műszaki tartalom melléklete. A kérdés nem használja a „műszaki tartalom” kifejezést.",
    {"forras_szakasz": "hivatkozas"})

# ================= KIÍRÁS =================
from pathlib import Path as _P
_P("gt").mkdir(exist_ok=True)
_P("gt/items.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in I) + "\n")
print(f"ÖSSZESEN: {len(I)} item, {sum(x['pont'] for x in I)} pont")
for t in sorted({x['teszt'] for x in I}, key=lambda z: int(z[1:])):
    sub = [x for x in I if x['teszt'] == t]
    print(f"  {t:4s}: {len(sub):2d} item, {sum(x['pont'] for x in sub):3d} pont")
