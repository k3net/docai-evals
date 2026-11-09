# 08 G5 — eredménylap: ellenőrzött számítási lánc, és a megbízhatósági fej a maradék értelmezési hibán

**Állapot:** 2026-11-05. A D12 rögzítve 11-04 10:16 (`kor08/rogzites/D12/manifest.json`, hash
`4a058dab8a681e4832346c4e977d8c75063377608e1c86bdd1ff3c8496b912f5`), a G4 lezárva 11-05 15:48
(`kor08/rogzites/pecset/K08G3.g4.json`, `dffea8d8…`), a pecsét Dani engedélyével nyitva 16:16 (`kor08/rogzites/G5/NYITAS.json`).
Minden itt közölt G5-szám a nyitás után készült, a rögzített elemzőkkel (`g5_k1_08`, `g5_k2_08`, `g5_k3_08`, 10 000 replika). A
gépi lapok: `k1/g5_k1.md`, `k2/g5_k2.md`, `k3/g5_k3.md`, `k3_rendszer/g5_k3.md`. Minden adat szintetikus. A függelékek utólagos,
leíró vizsgálatok, nem a rögzített elemzés részei.

## A mérés módja

- **Kérdés (08-runbook):** ha a kinyerést, a számítást és a szabályellenőrzést ellenőrzött kód végzi, a maradó értelmezési
  hibákból mennyit ismer fel a megbízhatósági fej, és segít-e ebben az értelmezési hibákon végzett célzott tanítás?
- **Karok:** mind a lánc után dönt az alany. L-S: az alany saját pontszáma. L-R07: a 07 B1-4R, befagyasztva. L-R: fej a láncos
  T500-on. **L-RN:** ugyanez, a T500 és az értelmezési tanítóminta 50–50% össz-súllyal. L-LR, L-LRN: logisztikus változatok, az
  L-RN-nel azonos példákon. Lánc nélkül: a 07 B1-4S és B1-4R.
- **Adat (G2):**
  - friss CAL 500 + TESZT 1000 családonként, természetes összetételben;
  - K3-típus: bank 90, hiba 91, szabály 200 item;
  - értelmezési teszt az audit után: szabály 2204 item (551 egység, 40 sabloncsoport, 1653 (b)), bank 256, hiba 248;
  - értelmezési tanítóminta: szabály 1980, bank 648, hiba 360 item.
- **Audit (Dani, vakon):** a véletlen minta címkehibaaránya alapesetenként szabály 0/30 [0,0%; 11,4%], bank 2/30 = 6,7%
  [1,8%; 21,3%], hiba 3/30 = 10,0% [3,5%; 25,6%]. 8 egység kimaradt (mind egy-egy (b) megvalósítási hibája), a K1(b) alapja
  1659-ről 1653-ra csökkent. Az audit a kiolvasás előtt lezárult, így a kezelése a modell eredményétől független.
- **K1 (az értelmezési diagnózison):** azok a tételek, amelyek a modellhez jutottak, és nincs rajtuk döntést befolyásoló
  kinyerési hiba. K1(b): rossz opció a gold választásával szemben. K1(a): az eldönthetetlen (a) SELECT-je a (b) helyes
  SELECT-jével szemben. A fő pár L-RN − L-S, a szabálycsaládon, Holm-mal.
- **K2:** a K3-típus helyes aránya lánc nélkül, valós kinyeréssel és orákulum-mezőkkel. Cél: ≥ 90% helyes és ≤ 2% hamis átengedés.
- **K3:** a friss TESZT-en a hasznos lefedettség és a lezárási hibaarány, a τ a friss CAL-on, replikánként újra (a lezárás
  precizitásának egyoldali CP-alsó határa ≥ 0,95, legalább 200 lezárttal, csak a modell lezárható döntésein).
- **Statisztika:** sabloncsoportos klaszteres bootstrap, replikánként a három seed átlaga, kétoldali p. A másodlagos
  összevetések korrekció nélkül, leíróan. Olvasat a G1-rögzítés 8. pontja szerint (AUROC 0,60, ΔAUROC 0,05).

## Önellenőrzés

- **Rögzítés:** a `rogzit08 ellenoriz` a G4-nél, a nyitásnál és a G5 után is zöld (65 fájl, 23 adatfájl).
- **Pecsét:** 480 fájl, 6,48 GB, 0 eltérés a G4-nél, a G5 indulásakor, és az utólagos próba előtt és után.
- **Determinizmus-őr:** a felhasznált zárt és nyílt kiolvasás első próbára R-módban futott, a det0 és a det1 50/50 sora bitre
  azonos a referenciával.
- **Darabszámok:** a pontozott szeletek 24/24, az értelmezési teszt tételszámai (2204 / 256 / 248) az audit kimenetével egyeznek.
- **Diszjunktság:** a szabálycsalád tanítómintája és a teszt, a friss CAL / TESZT és a K3-típus sabloncsoportjai közt 0 közös,
  a tanítóminta és a teszt közt 0 azonos szöveg (utólag ellenőrizve). A bankon és a hibán ezt nem ellenőriztem újra, ott a
  G2 terve a forrás.
- **Seedek:** az L-RN a szabály K1(b)-jén 0,917 / 0,935 / 0,928, a K1(a)-ján 0,925 / 0,929 / 0,919.
- **Előzetes várakozás:** a bankon a láncos karoknak a pilot szerint nem lesz munkapontjuk; nincs (a replikák 100%-ában).
- **Eltérések a rögzített végrehajtástól** (a számokat nem érintik, a G4-manifestben hash-elve):
  1. A `pecset08` és a `det_or08` a `burok_g3/python3` shimmel a konténerben futott, mert a gazdagép python3-ja a root 700-as
     pecsétet nem éri el. A rögzített `k08g3.sh`-nak ezt a hibát 11-04-én a burok kezelte.
  2. Az első két zárt kiolvasás a determinizmus-őrön megállt (A és B numerikai mód). A folytatásról Dani döntött (11-05 08:20,
     „1-es legyen”): `k08g3c.sh`, a mód a folyamat elején, a referenciaszeleten dőlt el, a kritérium nem változott. A kinyerés
     és a lánc nem futott újra. A két kísérlet kiolvasása olvasatlanul a pecsét alatt maradt a G5-ig.
  3. A rögzített futtatók közt nem volt G4-lépés, azt a `k08g4.sh` végezte; a `k08g5.sh` a `k08g5_burok.sh`-val futott.
  4. **A K1 a teljes rendszeren** a G1-rögzítés 6. és 7. pontja szerint kötelező leíró sor, de a rögzített futtató nem írja ki.
     Utólag pótolva, ld. C függelék.

## Összefoglalás

1. **K1(a), 2. fő próba: javít érdemben.** Az L-RN az eldönthetetlen választást jobban elválasztja a helyes választástól, mint az
   alany saját pontszáma: Δ 0,186, Holm-intervallum [0,111; 0,269], p < 0,0001 (L-RN 0,924, L-S 0,738). Ehhez a célzott
   tanítás és a neurális fej is kell: az L-R 0,760, az azonos példákon tanított L-LRN 0,761. **Utólag: ez a szám áll, de az értelmezése nem. A két osztály a szöveg
   felszínéből is tökéletesen szétválasztható, ezért a K1(a) nem igazolja, hogy a fej az eldönthetetlenséget ismeri fel (E függelék).** **11-08: a minimális párokon (G függelék) a fej nyeresége 0,075 [0,028; 0,131], a szöveges modell ott 0,699; az állítás ezen a konstrukción, szűkített formában áll.**
2. **K1(b), 1. fő próba: nem eldönthető.** Δ 0,036 [-0,047; 0,086], p = 0,338 (L-RN 0,927, L-S 0,890). A fej felismeri a rossz
   értelmezést, de az alany saját pontszáma is. Az intervallum a javulást és annak hiányát sem zárja ki.
3. **A korábbi tanulás nem visz át:** az L-R és az L-R07 a K1(b)-n ront az L-S-hez képest (-0,086, -0,146), a K1(a)-n nem javít.
4. **K2: a lánc a K3-típusú tévedést szinte eltünteti:** a valós kinyeréssel 97,8 / 98,9 / 97,5% helyes (bank / hiba / szabály), lánc
   nélkül 44,4 / 59,3 / 28,0%. **A ≤ 2%-os hamis átengedés a hibacsaládon nem teljesül** (3/91 = 3,3%). A javító kör után friss mintán teljesül (D függelék).
5. **K3: a lánc + fej több ügyet zár le, mint a lánc + alany:** szabály +9,3 pont [7,4; 18,1], hiba +4,7 [0,2; 9,2], a bankon
   nincs munkapont. **De a nyereség nem a célzott tanításé:** az L-R ugyanezt hozza, és a szabálycsaládon a lánc nélküli 07 fej is.
6. **A K1(a) nyeresége a szabálycsalád munkapontján nem jelenik meg:** az (a)-ból τ fölött lezárt arány 43,5%, az L-S-é 43,0%.
   A hibacsaládon megjelenik: 11,3% a 80,6% helyett.
7. **Az olvasatok nem függnek a numerikai módtól** (B függelék), de a hibacsalád lezárási hibája igen (3,6–5,5%).

## 1. K2 — a lánc a K3-típuson

| család | n | lánc nélkül | kinyert | orákulum | a kinyerés vesztesége | hamis átengedés | cél (helyes / átengedés) |
|---|---|---|---|---|---|---|---|
| bank | 90 | 44,4% [30,8%; 58,7%] | 97,8% [94,4%; 100,0%] | 98,9% | 1,1% [0,0%; 3,5%] | 1/90: 1,1% [0,0%; 3,5%] | igen / igen (a felső határ nem) |
| hiba | 91 | 59,3% [48,0%; 71,4%] | 98,9% [96,6%; 100,0%] | 100,0% | 1,1% [0,0%; 3,4%] | **3/91: 3,3% [0,0%; 7,1%]** | igen / **nem** |
| szabály | 200 | 28,0% [19,3%; 36,7%] | 97,5% [94,8%; 99,5%] | 98,0% | 0,5% [0,0%; 1,5%] | 0/199: 0,0% | igen / igen (a felső határ is) |

- A helyes arány alsó határa mindhárom családon 90% fölött van.
- Hamis kizárás és hamis kötés egyik úton sincs. A kinyert úton a szabálycsalád 1 tétele ment emberhez.
- **Bontás:** a bank lánc nélküli aránya nyelvenként erősen eltér (hu 16,0%, en 80,0%), a szabályé fordítva (hu 47,0%, en 9,0%); a lánc
  után ezek a különbségek eltűnnek (96,0–100,0%). A szabály S3b-deviza változata a leggyengébb (95,0%).
- A 4 hamis átengedés tételes vizsgálata az A függelékben: mind biztonságos irányú.

## 2. K1 — az értelmezési teszt

### Szabálycsalád (fő)

A diagnózis aránya 97,9%. Kiesés: 47 tétel, döntést befolyásoló kinyerési hibával; összefügg a változattal és a nyelvvel: (a) 93,3%,
(b) 99,4%, hu 95,9%, en 99,9%. Ezt az ékezet- vagy kisbetű-eltéréssel idézett forrásrészlet okozza (A függelék), a teljes rendszeren a kép ugyanaz (C függelék).

Események: K1(b) 74 rossz opció, 1567 gold; K1(a) 453 (a)-SELECT, 1567 (b) helyes SELECT. Az (a) döntései a diagnózison:
SELECT 453, MISSING 55, NONE 6 (Y-arány 10,7%). A strukturálisan szét nem választott tételek: 2157 / 2157 (a lánc után mindegyiken
legalább két lehetséges jelölt marad).

| kar | K1(b) AUROC [95%] | K1(a) AUROC [95%] | SELECT-AURC K1(b) | SELECT-AURC K1(a) |
|---|---|---|---|---|
| L-S | 0,890 [0,834; 0,981] | 0,738 [0,647; 0,822] | 0,007 | 0,123 |
| L-R07 | 0,744 [0,660; 0,908] | 0,747 [0,668; 0,819] | 0,019 | 0,119 |
| L-R | 0,805 [0,736; 0,938] | 0,760 [0,672; 0,840] | 0,014 | 0,113 |
| **L-RN** | **0,927 [0,885; 0,975]** | **0,924 [0,883; 0,957]** | 0,005 | 0,048 |
| L-LR | 0,868 [0,811; 0,967] | 0,735 [0,649; 0,814] | 0,008 | 0,121 |
| L-LRN | 0,886 [0,833; 0,970] | 0,761 [0,674; 0,841] | 0,007 | 0,117 |

| pár | K1(b) Δ [95%] | p | K1(a) Δ [95%] | p |
|---|---|---|---|---|
| **L-RN − L-S (fő)** | **0,036 [-0,047; 0,086]** | 0,338 | **0,186 [0,121; 0,258]; Holm 97,5%: [0,111; 0,269]** | < 0,0001 |
| L-R − L-S | -0,086 [-0,141; -0,041] | < 0,0001 | 0,022 [-0,002; 0,047] | 0,073 |
| L-R07 − L-S | -0,146 [-0,228; -0,065] | < 0,0001 | 0,009 [-0,018; 0,037] | 0,548 |
| L-RN − L-R | 0,122 [0,004; 0,208] | 0,035 | 0,164 [0,106; 0,227] | < 0,0001 |
| L-RN − L-LRN | 0,040 [-0,030; 0,088] | 0,262 | 0,163 [0,102; 0,231] | < 0,0001 |
| L-LRN − L-S | -0,004 [-0,020; 0,006] | 0,409 | 0,023 [0,014; 0,032] | < 0,0001 |

- **SELECT-AURC (L-RN − L-S, érdemi küszöb nélkül):** K1(b) -0,002 [-0,009; 0,001], K1(a) -0,075 [-0,109; -0,046].
- **Nyelvenként (L-RN K1(b) / K1(a)):** hu 0,899 / 0,900, en 0,971 / 0,946. L-S: hu 0,857 / 0,725, en 0,918 / 0,761.
- **A jel fajtája szerint (L-RN K1(b) / K1(a)):** szó szerint 0,936 / 0,946 (15 rossz opció, 715 SELECT), áttételes 0,915 / 0,905 (59, 926).
  L-S: 0,963 / 0,783, illetve 0,851 / 0,702. A fej előnye a K1(b)-n az áttételes jelnél látszik, a szó szerintinél nem.
- **Brier / ECE (a friss CAL temperature-ével):** L-RN K1(b) 0,054 / 0,068, K1(a) 0,084 / 0,053; L-S 0,048 / 0,075, 0,150 / 0,078.

**A K1(b) eseményei erősen koncentráltak.** A teljes rendszeren a 76 rossz opció a 40 sabloncsoportból 9-ben van, ebből kettőben 62%:
F83 30, F84 17, F17 9, F32 9, F07 4 (az első öt 91%). Az F83 a Gemma-triage leggyengébb forgatókönyveinek egyike ((b)-egyezés
30/42), de a 11 auditált F83-egységben címkehiba nem volt. A próba tehát lényegében néhány forgatókönyvről szól. Ez magyarázza,
hogy az intervallum szélesebb, mint amit az erőbecslés feltételezett: ott a várt hibaszám 111 volt, és a hibák klaszterezettsége
jóval kisebb.

### Bank és hiba (leíró)

| család | esemény K1(b) / K1(a) | L-RN K1(b) | L-S K1(b) | L-RN K1(a) | L-S K1(a) | L-RN − L-S K1(a) [95%] |
|---|---|---|---|---|---|---|
| bank | 9 / 54 | 0,847 [0,707; 0,967] | 0,875 [0,784; 0,951] | 0,993 [0,981; 1,000] | 0,857 [0,806; 0,906] | 0,135 [0,089; 0,184] |
| hiba | 4 / 62 | 0,994 [0,982; 1,000] | 0,978 [0,956; 0,995] | 0,997 [0,994; 1,000] | 0,930 [0,886; 0,967] | 0,067 [0,031; 0,111] |

A K1(b) itt 9, illetve 4 eseményen áll, nem értelmezhető erősen. Az L-S K1(a)-ja a G1 pilotjában 0,94 és 0,97 volt, itt 0,857 és 0,930, így a
fejnek több helye maradt, mint várható volt. Az alany az (a)-n ezeken a családokon sosem mond Y-t (Y-arány 0,0%).

## 3. K3 — a gyakorlati eredmény

Lefedettség [95%] / lezárási hibaarány. A hibafeltétel: „teljesül”, ha a pontbecslés és a felső határ is ≤ 5%; „bizonytalan”, ha a felső
határ 5% fölött van; „nem teljesül”, ha a pontbecslés is.

| kar | szabály | hibafeltétel | hiba | hibafeltétel |
|---|---|---|---|---|
| L-S | 62,6% [53,6%; 65,1%] / 4,7% | bizonytalan | 62,9% [58,0%; 68,0%] / 4,1% | bizonytalan |
| L-R07 | 69,1% [63,5%; 72,9%] / 2,1% | bizonytalan | 61,7% [57,4%; 68,1%] / 5,5% | nem teljesül |
| L-R | 72,5% [70,4%; 74,5%] / 2,4% | **teljesül** | 67,6% [64,4%; 69,5%] / 4,5% | bizonytalan |
| **L-RN** | 71,9% [69,8%; 74,1%] / 3,1% [1,9%; 5,8%] | bizonytalan | 67,6% [64,5%; 69,6%] / 3,6% [1,2%; 7,1%] | bizonytalan |
| L-LR | 72,2% [69,1%; 74,0%] / 4,5% | bizonytalan | 63,6% [59,7%; 67,7%] / 4,5% | bizonytalan |
| L-LRN | 71,9% [66,0%; 73,9%] / 4,5% | bizonytalan | 66,3% [62,9%; 68,8%] / 4,6% | bizonytalan |
| B1-4S (lánc nélkül) | 53,7% [45,5%; 56,6%] / 5,0% | bizonytalan | 51,0% [48,1%; 59,5%] / 2,5% | bizonytalan |
| B1-4R (lánc nélkül) | 71,9% [67,5%; 74,4%] / 2,7% | bizonytalan | 71,2% [55,9%; 72,9%] / 5,5% | nem teljesül |

| pár | szabály Δ lefedettség [95%] | hiba Δ lefedettség [95%] | bank Δ lefedettség [95%] |
|---|---|---|---|
| L-RN − L-S | +9,3 pont [7,4; 18,1] | +4,7 pont [0,2; 9,2] | 0,0 |
| L-R − L-S | +9,9 pont [7,9; 18,5] | +4,7 pont [0,2; 9,0] | 0,0 |
| L-RN − B1-4R | -0,0 pont [-2,9; 4,7] | -3,5 pont [-6,1; 11,3] | -16,9 pont [-25,0; 21,0] |

- **Bank:** a lánc 363 tételt köt, 0 hibával, ez a 36,3% lefedettség minden láncos karnál; a modellből semmi nem zárul le, mert
  nincs munkapont (ahogy a 7. pont várta). A lánc nélküli B1-4R 53,2% [15,4%; 61,1%], 1,2% hibával, a replikák 4,5%-ában munkapont
  nélkül. A leíró rendszer-τ-val (`k3_rendszer`) az L-RN 58,8% [56,5%; 62,1%], 2,5% hibával, de a modell saját lezárásainak hibája ott 6,4%.
- **Lánc kimenetei a TESZT-en:** a hibán és a szabályon nincs kötés (1, illetve 5 tétel megy emberhez, a többi a modellhez).
- **ΔAURC (L-RN − L-S, a modell döntésein):** bank -0,0994 [-0,1235; -0,0781], hiba -0,0265 [-0,0320; -0,0211], szabály -0,0287 [-0,0347; -0,0231].
- **K3-X (a két kinyerő keresztellenőrzése, leíró):** a visszatartott hiba bank 0, hiba 2, szabály 2; az elveszett helyes lezárás 9, 15,3, 22,7
  (seed-átlag). A cserearány rossz. Egyező, de hibás kinyerés: bank 2, hiba 1, szabály 0.

**Az (a)-ból τ fölött lezárt arány (leíró):**

| család | L-S | L-R | L-RN | L-LRN |
|---|---|---|---|---|
| szabály | 43,0% | 65,1% | 43,5% | 57,6% |
| hiba | 80,6% | 47,3% | 11,3% | 33,9% |
| bank | 0,0% | 0,0% | 0,0% | 0,0% |

A szabálycsaládon az L-RN ugyanannyi eldönthetetlen esetet zár le, mint az L-S, 9 ponttal nagyobb lefedettség mellett. A jó sorrend (K1(a)
0,924) ellenére az eldönthetetlen esetek 43,5%-a a τ fölé kerül. Feltevés, nem ellenőrzött: a τ a természetes CAL-on áll be, ahol kevés az (a) típusú
tétel, ezért a küszöb ezekre nem elég szigorú.

## 4. Korlátok

- **Minden szintetikus.** A tanítóminta és a teszt ugyanabból a generátorból és konstrukcióból jön, diszjunkt sabloncsoportokkal. A K1(a)
  nyereségéről nem tudjuk, hogy valódi szövegen is megvan-e, és a konstrukció a felszíni jegyektől nem különíti el (E függelék).
- **A K1(b) néhány forgatókönyvön áll** (2. pont), ezért a „nem eldönthető” nem a hatás hiánya.
- **Az erőbecslés optimista volt:** a K1(b)-re Δ 0,05-nél 69%-os erőt adott, L-S 0,80-at és 111 hibát feltételezve; a hibák száma kevesebb lett, és sokkal klaszterezettebb.
- **A K3-típus kis minta:** a hibacsaládon egy tétel 1,1 pont, a cél körüli eltérés néhány tételen múlik.
- **A lezárási hiba a hibacsaládon módfüggő** (B függelék), az 5%-os szint tartását ott nem állítjuk.
- **A címkehiba** a bankon és a hibán a véletlen mintában 6,7% és 10,0% volt az audit előtt. A hibás egységek kimaradtak, de csak az
  auditált itemeket néztük át.
- **Ismert generálási mintázat:** a „felé fennálló” fordulat, amely a banki kizárt cella oka volt, még 1 nem auditált teszt-itemben
  (`k08:hu:068`) és 3 tanító-itemben (045, 091, 093) szerepel. Dani döntése szerint változatlanok maradtak.
- **A hibaelhárítási szabályok** itt strukturáltak, a termékben nem feltétlenül azok (08-runbook 2.3).
- **A fejek csak az R-módú kiolvasáson tanultak.**

## 5. Értelmezés és a döntési kapcsolás (D9)

- **A lánc működőképessége (K2):** a helyes arányra vonatkozó cél teljesül, a hamis átengedésé a hibacsaládon nem, ezért a lánc nem megy
  automatikusan a termékspecifikációba. A hibák biztonságos irányúak és jól körülhatárolhatók (A függelék). **Dani 11-05: javító kör** a
  kinyerésen, friss K3-típusú mintán újramérve; a cél nem változik. **11-06: a javított lánc a rögzített szabály szerint teljesíti a célt, a D9 szerint
  termékspecifikációba mehet (D függelék).** [Szerkesztői megjegyzés, 2026-11-08: a tulajdonos döntése szerint ez a lépés szintetikus eredmény alapján nem történik meg; a következő lépés egy friss, kb. 150 tételes valódi minta rögzített küszöbbel, ld. a decision-record.md-t.]
- **Kutatási jel (K1):**
  - K1(b): az L-RN felismeri a rossz értelmezést, de kimutathatóan nem javít az L-S-en. Ez a „nem eldönthető” ág, a következő lépés a hatás
    nagysága alapján dől el; 0,036-os pontbecslésnél és néhány forgatókönyvre koncentrált eseményeknél önmagában nem indokol nagyobb kört.
  - K1(a): a rögzített olvasat „javít érdemben”, és az alany bizonyossága egyedül nem hozza. **De a felszíni próba rögzített olvasata szerint az állítás ebben a formában nem tartható
    (E függelék):** a szöveg alapján az (a) és a (b) a fej nélkül is szétválik. A fej fejlesztése erre az eredményre nem alapozható.
  - Az L-R és az L-R07 nem javít, tehát a korábbi tanulás nem visz át.
- **Gyakorlati haszon (K3):** a lánc + fej a szabályon és a hibán több ügyet zár le a lánc + alanynál, a bankon nem. Ezt a T500-as fej
  (L-R) is hozza, ezért a célzott tanítás gyakorlati haszna ebben a mérésben nem igazolt. A szabálycsaládon a lánc nélküli B1-4R
  ugyanennyit zár le; a lánc haszna a K3-típuson mutatkozik meg, amely a természetes összetételben ritka.

## Lezárás

- A 08A kérdései megválaszolva a friss teszten; a szabály és a végpontok a rögzítés előtt álltak, utólag nem módosultak.
- **Következő:** a javító kör kész (D függelék), a K1(a) felszíni próbája kész (E függelék). Az illesztett kontroll (F függelék) és a minimális párok (G függelék) készen vannak: **a K1(a) állítása szűkített formában áll** (a szabálycsalád, a minimális pár konstrukciója, ezek a fejek; L-RN − L-S 0,075 [0,028; 0,131]), a fej kérdése ezzel lezárult. A G5 0,186-os száma továbbra sem ezt méri. Nyitott: a 08B friss mintája.
  Nyitott kérdés a következő körökre: a τ kezelése az eldönthetetlen eseteken.

## A függelék: a K2 hamis átengedései tételenként (utólag, leíró)

Részletek: `kor08/eredmenyek/G5_utolagos/k2_atengedes.md`. Az eszköz: `kor08/eszkozok/k2_atengedes08.py`.

[kihagyva: tételszintű kinyerések és pontszámok; a csomag nem közöl itemszintű kimenetet, a tételes jegyzék (`kor08/eredmenyek/G5_utolagos/k2_atengedes.md`) nincs publikálva]

- **Mind a 4 kinyerési hiba, és az ellenőrzés mind a 4-et elkapta.** A tétel blokk és kizárás nélkül ment a modellhez, gold nem esett ki, rossz
  kötés nincs. A definíció szerint ez hamis átengedés (a kimenet eltér az orákulumtól, az ellenőrzés átment), de a lánc itt kevesebbet tudott, nem
  tévedett. Az ok mind a négy esetben az, hogy a tétel elveszíti a lánc segítségét.
- **A friss mintán (K2-n kívül):** 101 / 4488 átment tételen tér el a két út (2,3%; bank 49, hiba 13, szabály 39), a gold sosem esik ki. A bank
  eltéréseiből 45 elmaradt kötés (az orákulum kötött volna). **A hibacsaládon 2 NO_MATCH tételnél a lánc többet zár ki, mint az orákulum:** ez
  az egyetlen rossz irányú eltérés.
- **Az eldobott mezők okai a friss mintán:** a szabálycsaládon 38-ból 37-et csak az ékezet- vagy kisbetű-eltérés buktatott („osszeg 75 370 Ft”). A
  hibán főként az érték nincs a forrásrészletben (16/27, ide tartozik az átváltás), a bankon is ez a leggyakoribb (35/63).
- **Az értelmezési teszten** a 47 eldobott mezőből 46 ugyanez a magyar tételeken, és a 47 kiesésből 37 (a)-hu tétel; ezért függ össze a kiesés a
  változattal és a nyelvvel.

## B függelék: módérzékenység (utólag, leíró)

Dani 11-05-i engedélyével (`k08g5m.sh`, `modszenz08.py`; `kor08/eredmenyek/G5_modszenz/osszevetes.md`). A két korábbi zárt kiolvasás (A és B
numerikai mód) ugyanazokkal az R-módon tanított fejekkel és rögzített elemzőkkel; a τ és a temperature a mód saját CAL-ján áll be.

| mérőszám | R | A | B |
|---|---|---|---|
| K1(a) Δ (olvasat: javít érdemben) | 0,186 | 0,188 | 0,190 |
| K1(b) Δ (olvasat: nem eldönthető) | 0,036 | 0,030 | 0,040 |
| K2 helyes, bank / hiba / szabály | 97,8 / 98,9 / 97,5% | ugyanaz | ugyanaz |
| K3 szabály, L-RN − L-S | +9,3 | +9,8 | +10,1 |
| K3 hiba, L-RN − L-S (alsó határ) | +4,7 (0,2) | +5,0 (0,0) | +4,7 (0,0) |
| L-RN lezárási hibája, hiba | 3,6% | 4,1% | **5,5%** |
| L-RN lezárási hibája, szabály | 3,1% | 3,8% | 3,7% |
| (a)-ból lezárt, szabály, L-RN / L-S | 43,5 / 43,0% | 46,6 / 42,2% | 47,9 / 41,4% |
| (a)-ból lezárt, hiba, L-RN / L-S | 11,3 / 80,6% | 12,9 / 87,1% | 18,8 / 83,9% |
| eltérő döntés R-hez képest (8719 item) | – | 186 (2,1%) | 156 (1,8%) |

A láncos K3-típuson egy döntés sem fordul. A fő olvasatok tehát nem a módon múlnak. Az 5%-hoz közeli lezárási hiba viszont átbillenhet, és a K3 hiba
különbségének alsó határa határeset.

## C függelék: a K1 a teljes rendszeren (a G1-rögzítés kötelező leíró sora, utólag pótolva)

A rögzített `g5_k1_08` változatlanul, a diagnózis szűrője nélkül (`g5_k1t_08.py`; `kor08/eredmenyek/G5_utolagos/k1_teljes/g5_k1.md`): a modellhez jutott
minden tétel bent marad, a kinyerési hibásak is.

| szabálycsalád | K1(b) esemény | K1(b) Δ [95%] | K1(a) esemény | K1(a) Δ [95%] |
|---|---|---|---|---|
| diagnózis (fő) | 74 / 1567 | 0,036 [-0,047; 0,086] | 453 / 1567 | 0,186 [0,121; 0,258] |
| teljes rendszer | 76 / 1575 | 0,037 [-0,046; 0,086] | 488 / 1575 | 0,187 [0,122; 0,259] |

A bank és a hiba számai sem változnak érdemben (bank K1(a) Δ 0,136, hiba 0,067). A 47 kiesett tétel tehát a fő eredményt nem mozdítja.

## D függelék: a javító kör (J; külön rögzítés, 11-05 22:10)

Rögzítés: `kor08/J-rogzites.md`, `kor08/rogzites/J/manifest.json`, Dani jóváhagyásával, a friss minta generálása előtt. Gépi lapok: `kor08/eredmenyek/J/k2/g5_k2.md`, `k2_rogzitett/g5_k2.md`.
Csak a kinyert mezők ellenőrzése változott: J1 a forrásrészlet ékezet- és kisbetű-érzéketlen keresése, J2 az átváltott mérés visszavezetése a szöveg számára. A rögzített `g5_k2_08`
változatlan, 10 000 replika, a kiolvasás első próbára R-módban, a det0 és a det1 bitre azonos.

| család | n (sabloncsoport) | lánc nélkül | kinyert, javított | hamis átengedés, javított | rögzített lánc, ugyanazon a kinyerésen |
|---|---|---|---|---|---|
| bank | 197 (60) | 42,6% | 100,0% | 0/197 | 0/197 |
| hiba | 210 (46) | 50,0% | 98,6% [96,1%; 100,0%] | 0/210 | **5/210 = 2,4% [0,5%; 4,9%]** |
| szabály | 220 (60) | 27,3% | 100,0% | 1/220 = 0,5% [0,0%; 1,4%] | 1/220 |

- **A szabály teljesül mindhárom családon:** helyes ≥ 90%, hamis átengedés ≤ 2%, hamis kizárás és hamis kötés nincs.
- **A javítás hatása a hibacsaládon látszik:** ott a rögzített lánc a célt nem érte volna el, az eldobott mezők száma 9-ről 0-ra csökkent. A bankon és a szabályon a két lánc itt azonos.
- **A G5 banki esete** (a „40%” összegként) a J-re nem hat, ezen a mintán nem fordult elő; a két tényleges kinyerési tévedés típusa továbbra is lehetséges.
- **Korlát:** ugyanaz a generátor és konstrukció, szintetikus adat; a K1 és a K3 nem mérődött újra, a bank elmaradt kötéseit a K2 nem méri.

## E függelék: a K1(a) felszíni jegyek próbája (utólag, leíró)

Dani 11-06-i engedélyével (`felszin08.py`, `felszin08b.py`; `kor08/eredmenyek/G5_utolagos/felszin/felszin.md`). Csak a szöveget látó modellek a tanítómintán tanulnak, ugyanazon a K1(a)-halmazon mérve, a
sabloncsoportok diszjunktak. **Az olvasat a futás előtt rögzítve:** a legjobb szöveges modell teszt-AUROC-ja a szabálycsaládon ≥ 0,85 esetén a nyereség nagyrészt felszíni jeggyel magyarázható, és
az állítás ebben a formában nem tartható.

| család | hossz | szó TF-IDF | karakter TF-IDF | L-S | L-RN |
|---|---|---|---|---|---|
| szabály | 0,731 | 0,987 [0,982; 0,992] | **1,000** | 0,738 | 0,926 |
| bank | 0,802 | 1,000 | 1,000 | 0,857 | 0,994 |
| hiba | 0,860 | 1,000 | 1,000 | 0,930 | 0,998 |

(Az L-RN itt a seedek pontszámainak átlagából számolt AUROC, ezért tér el kicsit a seedenkénti AUROC-ok átlagától.)

- **Az olvasat: az első sáv. A K1(a) nyeresége felszíni jeggyel magyarázható, az állítás ebben a formában nem tartható.** A G5 száma helyes, a jelentése más: a fej ezen a konstrukción nem jobb egy szövegosztályozónál (L-RN − karakter: -0,074 [-0,115; -0,041]).
- **Nem a próba hibája** (`logs/felszin/ellenorzes.log`): a nyers G2-szövegen, lánc-blokk és opciók nélkül, kisbetűsítve, ékezet és számok nélkül is 0,99–1,00; nyelvenként is 0,99–1,00; összekevert tanítócímkékkel 0,47–0,55.
- **Az ok a konstrukció:** az (a) ugyanaz az eset a jel nélkül, ezért rövid, tőmondatos szöveg (medián hossz szabály 251 / 412, hiba 362 / 765 karakter), a (b) pedig elbeszélő mondatot is tartalmaz. Az elválasztáshoz elég észrevenni, hogy van-e ilyen mondat; ehhez nem kell megérteni, hogy eldönti-e a kérdést.
- **Amit ez nem érint:** a K1(b) (a rossz opció és a gold ugyanabból a (b)-ből jön) és a K2, valamint a J. A K3 nem az (a)-(b) különbségre épül. Az (a)-ból lezárt arány a hibacsaládon (11,3% a 80,6% ellen) viszont ugyanezzel a jeggyel is magyarázható.
- **Tanulság:** a szöveges alapmodellt a rögzítés előtt kellett volna lefuttatni a konstrukción. Ez a próba percek alatt megvan, és a G1-ben kiszűrte volna a hibát.
- **Eldöntő kísérlet:** illesztett (a), azonos stílusú és hosszúságú, de a kérdést el nem döntő elbeszélő mondattal; a fejek változatlanok.

## F függelék: illesztett kontroll a K1(a)-hoz (M, 11-06)

Rögzítés: `kor08/M-rogzites.md`, `kor08/rogzites/M/manifest.json` (Dani: „indulhat”). A fejek befagyasztva, az (a') a G2 tervein, a (b) a G3 kiolvasása. A kiolvasás R-módban, a det0 és a det1 bitre azonos. Eredmény: `kor08/eredmenyek/M/k1/g5_k1.md`.

**Az illesztés nem érte el a küszöböt:** hossz 0,582 (teljesül), a régi szöveges modell 0,841 (nem), friss sabloncsoportos CV 0,998 (nem). Ezért a rögzített olvasat aszimmetrikus.

| szabálycsalád, K1(a) | G5, eredeti (a) | M, illesztett (a) |
|---|---|---|
| L-RN | 0,924 | 0,882 [0,832; 0,925] |
| L-S | 0,738 | 0,739 [0,652; 0,820] |
| L-RN − L-S | 0,186 | 0,144 [0,085; 0,211] |
| L-R | 0,760 | 0,758 |
| L-LRN | 0,761 | 0,763 |

**Olvasat a rögzítés szerint:** „javít érdemben”, ez a megmaradt szöveges jegyek miatt **nem bizonyíték**, a kérdés nyitva marad. A fej nem parkol, az állítás nem áll helyre.

**Mellette, leíró:**
- A K1(b) változatlan (0,036), ahogy kell: a (b) ugyanaz.
- A τ fölött lezárt (a') aránya a szabálycsaládon L-RN 54,6%, L-S 43,9% (G5: 43,5 / 43,0). A rangsor tart, de a munkaponton a fej több eldönthetetlen tételt enged át, mint az L-S. A hibacsaládon 20,4 / 77,4% (G5: 11,3 / 80,6).
- Utólag, nem rögzítve (`kor08/eredmenyek/M/utolagos/utolagos.json`, seed-átlag pontszámmal): az ugyanazon a tanítómintán tanult legjobb szöveges modell ezen a halmazon 0,827, az L-RN 0,885. A szöveges pontszám kvartilisein belül az L-RN 0,85–0,88, az L-S 0,62–0,75; egységen belül az L-RN 0,880, a szöveges modell 0,865, az L-S 0,768. Az L-RN és a szöveges pontszám rangkorrelációja 0,36.
- A bank (L-RN 0,993, L-S 0,873) és a hiba (0,990, 0,922) nem illesztett, következtetés nincs.

**Ami hiányzik:** a friss szöveges modell 0,998-ja azt mutatja, hogy a témabeli különbség a szövegben megvan, és a rejtett állapotokból is elérhető lehet. Ezt csak olyan kontroll zárja ki, ahol az (a) és a (b) is tartalmaz jel jellegű mondatot.

## G függelék: minimális párok (N, 11-08), a fej utolsó kontrollja

Rögzítés: `kor08/N-rogzites.md` v0.2, `kor08/rogzites/N/manifest.json` (Dani: „elfogadom, mehet”). A fejek befagyasztva, mindkét tag új szöveg, csak a szabálycsalád. A kiolvasás R-módban, a det0 és a det1 bitre azonos. Eredmény: `kor08/eredmenyek/N/k1/g5_k1.md`, `kor08/eredmenyek/N/szoveg.json`.

**A konstrukció:** egy egységből két szöveg, mindkettőben egy döntő jellegű mondat (J), egy nem döntő (L) és egy „korábbi, másik kérelem” jelölés. A (b'')-ben J szól a kért összegről, az (a'')-ban L, a J a másik kérelemről. A szókincs, a hossz és a szerkezet a két osztályban azonos, csak a hivatkozás más. Minta: 348 egység, 33 forgatókönyv. Az első címkeellenőrzés a kapun elbukott (3 / 30, mind generálási hiba), a szerkezeti szűrő után a friss, vak 30-on 0 eltérés. A szűrő a fejek eredménye előtt készült.

| szabálycsalád, K1(a) | G5, eredeti (a) | M, illesztett (a) | N, minimális pár |
|---|---|---|---|
| L-RN | 0,924 | 0,882 | 0,872 [0,823; 0,914] |
| L-S | 0,738 | 0,739 | 0,797 [0,734; 0,855] |
| L-RN − L-S | 0,186 | 0,144 | **0,075 [0,028; 0,131]** |
| L-R | 0,760 | 0,758 | 0,817 |
| L-LRN | 0,761 | 0,763 | 0,807 |
| régi szöveges modell, a K1(a) halmazán | 1,000 | 0,827 | 0,515 |
| friss szöveges modell, CV | – | 0,998 (a teljes mintán) | 0,699 (a K1(a) halmazán) |
| τ fölött lezárt (a), L-RN / L-S | 43,5 / 43,0% | 54,6 / 43,9% | 77,7 / 37,9% |

**Olvasat a rögzítés szerint: az állítás szűkített formában áll.** Mindkét feltétel teljesül: az L-RN − L-S „javít érdemben” (alsó határ > 0, pontbecslés ≥ 0,05), és az L-RN 0,872-je nagyobb a legjobb szöveges modell 0,699-énél. A hatókör: a szabálycsalád, ez a konstrukció, ezek a fejek. A fej kérdése ezzel lezárult, további kontroll nincs.

**Ami az eredményt szűkíti:**
- **A hatás harmadára-felére csökkent** a G5-höz képest, mert az L-S itt erősebb, és az L-RN egy kicsit gyengébb.
- **A munkaponton a fej használhatatlan ezen a konstrukción:** a τ fölött lezárt (a'') aránya L-RN 77,7%, L-S 37,9%. A rangsor elválaszt, a τ nem illik rá, ezért termékhasznosság ebből nem következik. Az alany itt szinte sosem mond Y-t (2,3%).
- **Csak az L-RN hozza,** az L-R +0,020 és az L-LRN +0,011 gyenge. A K1(b) továbbra sem eldönthető (0,025, itt csak 9 rossz opció).
- **A valódi banki tételeken a fej nem jobb az L-S-nél** (K08V, AUROC 0,910 és 0,911; fejlesztési szám).
- Szintetikus adat, egy generátor, egy család; a szűrő miatt 33 forgatókönyv maradt 40-ből, és csak azok a szövegek, ahol a Muse betartotta a szerkezetet.

**Utólag, leíró (önellenőrzés 11-08, `kor08/eredmenyek/onellenorzes-11-08.md`):**
- **Érzékenység a klaszterezésre:** a párok tagjai megosztják a mondatokat, ezért a klaszter a forgatókönyv-pár (17) is lehet: Δ 0,075 [0,021; 0,148], az olvasat ugyanaz (`N/erzekenyseg_parklaszter/`).
- **Mit ismer fel a fej:** az (a'')-ben az alany 183-szor a másik kérelem J(f')-je által sugallt gold-kategóriát választja, 139-szer a csalit. A fej mindkét részesetet elválasztja a (b'') helyes döntéseitől: gold-kategória L-RN 0,844 / L-S 0,760, csali 0,906 / 0,844. Tehát nem csak a rossz kategóriát ismeri fel, hanem azt is, hogy a döntő mondat nem a kért összegről szól.
