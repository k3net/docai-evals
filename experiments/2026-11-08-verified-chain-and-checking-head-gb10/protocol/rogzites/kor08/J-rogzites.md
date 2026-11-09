# 08 javító kör (J) — a rögzítés

- **Verzió:** v0.1, 2026-11-05. Dani jóváhagyásával rögzítve (`kor08/rogzites/J/manifest.json`); a friss minta csak a rögzítés után készült.
- **Alapja:** a G5 eredménylapja (`kor08/eredmenyek/G5/eredmenylap.md`, 1. pont és A függelék) és Dani 11-05-i döntése: „indulhat a javító kör”.
- **Viszony a D12-höz:** a G1-rögzítés és a G5 eredményei nem változnak. Ez külön, kisebb kör; a rögzített fájlokhoz nem nyúl, minden burkolóként készül.

## 1. Kérdés

A G5-ben a lánc a hibacsaládon nem teljesítette a D9 fejlesztési célját (hamis átengedés 3,3%, cél ≤ 2%). **A kinyerés ellenőrzésének két
javításával a lánc friss K3-típusú mintán teljesíti-e a célt mindhárom családon?** A cél nem változik: a K3-típus helyes aránya ≥ 90%, a hamis
átengedés ≤ 2% (a `g5_k2_08` definíciójával).

## 2. Mi változik

Csak a kinyert mezők ellenőrzése (`lanc08j.py`, a `lanc08` burkolója):

- **J1, forrásrészlet:** a forrásrészlet helye ékezet- és kisbetű-érzéketlenül is megkereshető. A pozíció az eredeti szövegben marad, az érték
  ellenőrzése nem lazul.
- **J2, átváltott mérés:** ha a mérés értéke nincs a forrásrészletben, de pontosan egy, az egység előtt álló szám az alapegységre vagy a szabály
  egységére átváltva pontosan az érték, a mező értéke a szöveg száma lesz, és az átváltást a lánc végzi. Más hibás érték továbbra is bukik.

**Nem változik:** a kinyerő promptja és sémája, a lánc többi része, a blokk (v4), a fejek, a τ, a K2 elemzője, az orákulum-út.

## 3. Minta

- **Friss sablonok:** `k08j` azonosítókkal, családonként nyelvenként 30 sablon (`szint08j.py`). A generátor, a tényellenőrző és a Muse-revízió a G2-é.
- **A K3-típus négy változata:** B3a részfizetés 220, H3 mértékegység-váltás 220, S3a nettó 110, S3b deviza 110 terv, nyelvenként fele. Családonként
  220 terv, a G2 kihozatalával (90–100%) várhatóan 200–220 item. Utánpótlás nincs, a tényellenőrzőn elbukó terv kimarad.
- **Diszjunktság:** a futtató megáll, ha a G2 bármely részével van közös sabloncsoport vagy azonos szöveg (`j08 minta`).
- **Audit nincs,** ahogy a G2 K3-típusán sem volt: a hamis átengedés nem a címkétől függ, a gold a terv tényeiből jön.

## 4. Végrehajtás

`k08j.sh`, egy futással:

1. a minta a Muse-szal;
2. kinyerés az alannyal, egyszer, a rögzített `kinyer08`-cal, hash-elve;
3. a lánc három úton: javított, rögzített (ugyanazon a kinyerésen), orákulum;
4. kiolvasás egy HF-folyamatban, négy szelettel (lánc nélkül, javított, rögzített, orákulum), a determinizmus-őrrel. A mód a `k08g3c.sh` szerint a
   folyamat elején, a referenciaszeleten dől el, legfeljebb 6 próbával; a det1 eltérésénél leáll;
5. pontozás és a rögzített `g5_k2_08`, 10 000 replikával, a javított és a rögzített láncra külön.

Pecsét nincs: a J-ben egyetlen elemzés van, és az a rögzítés előtt áll.

## 5. Végpont és döntési szabály

- **Teljesül,** ha mindhárom családon a kinyert úton:
  1. a helyes arány pontbecslése ≥ 90%;
  2. a hamis átengedés pontbecslése ≤ 2%;
  3. **hamis kizárás és hamis kötés nincs.** Ez új feltétel: a javítás lazít az ellenőrzésen, ezért ki kell zárni, hogy veszélyes irányú hibát hoz be.
- **Ha teljesül:** a lánc a J1–J2 javítással a D9 szerint termékspecifikációba mehet.
- **Ha nem teljesül:** nem megy; a maradék tételes leírása után Dani dönt.
- **Mindig közölve:** a 95%-os intervallumok, a rögzített lánc számai ugyanazon a kinyerésen, családonként és változatonként, nyelvenként, az eldobott mezők
  száma és oka, és hány tételen tér el a két lánc.

## 6. Erő

A cél pontbecslésre vonatkozik. 200 itemnél legfeljebb 4 hamis átengedés fér bele:

| valódi arány | 0,5% | 1% | 2% | 3% | 5% |
|---|---|---|---|---|---|
| a cél teljesülésének esélye | 99,6% | 94,8% | 62,9% | 28,1% | 2,6% |

A G2 mintáján (n = 91, legfeljebb 1 eset) ugyanez 1%-nál 77%. A felső határ 200 itemnél 1%-os aránynál a 2% fölött maradhat; ezért közöljük, de a szabály a pontbecslés,
ahogy a G5-ben.

## 7. Fejlesztési számok (nem bizonyíték)

A meglévő kinyerésen, GPU nélkül (`j_replay08.py`, `kor08/eredmenyek/J/replay.md`). Ezek a szeletek nyitottak, a javítás rájuk készült.

| szelet | hamis átengedés, rögzített | javított |
|---|---|---|
| G2K3 bank | 1/90 | 1/90 |
| G2K3 hiba | 3/91 | 1/91 |
| G2K3 szabály | 0/199 | 0/199 |
| friss minta, bank | 49/1500 | 46/1500 |
| friss minta, hiba | 13/1499 | 8/1499 |
| friss minta, szabály | 39/1489 | 2/1489 |
| értelmezési teszt, szabály | 47/2204 | 1/2204 |

Új eltérés az orákulumhoz képest egyik szeleten sem keletkezett, hamis kizárás és hamis kötés nincs, a `lanc08.zavarasok` zavarópróbája minden sorban azonos. A
rögzített lánc itt a G3 tárolt kimenetét adja vissza.

**Ami megmarad:** a két nem javítható kinyerési hiba (800 helyett 80 mOhm, a „40%” összegként), a bank elmaradt kötései (a friss mintán ~3%, biztonságos irány, a K2 nem méri) és a
hibacsalád 2 NO_MATCH tétele, ahol a lánc többet zár ki az orákulumnál.

## 8. Ami nem része

A K1 és a K3 nem mérődik újra, fej nem tanul. A J a szintetikus K3-típusról szól; a valódi banki tételekről a 08B dönt. Ha a J teljesül, a javított lánc a G5 K3-számait is
kismértékben változtatná (a szabálycsalád 47 kieső tétele visszakerül), ezt nem mérjük.

## 9. Eszközök és idő

- **Burkolók:** `lanc08j.py`, `szint08j.py`, `j08.py`, `k08j.sh`; a manifest `kor08/rogzites/J/manifest.json` (a D12 hash-ével, felülírni nem lehet).
- **Becsült GPU-idő:** kb. 2,5–3 óra (minta kb. 1,25 óra, kinyerés kb. 20 perc, kiolvasás kb. 45 perc, próbánként +10 perc).
