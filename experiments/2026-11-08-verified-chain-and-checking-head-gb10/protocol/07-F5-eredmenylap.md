# 07 F5 — eredménylap: az állapotjelző B1 és a rá tanított fej friss, érintetlen teszten

**Állapot:** 2026-11-01. A v1 rögzítve 09:42:44 (Dani „mehet”-je 09:43; `kor07/rogzites/v1/ROGZITES.json`, a 157
fájlos manifest hash-e `725078096d240660c42cef5a55737ce17602c8d2c61d91321d2f76e8afb52686`). A pecsét alatti
kiolvasások megtekintése és minden itt közölt szám a rögzítés után készült. A gépi lap: `lap.md`, `elemzes.json`.

## A mérés módja

- **Kérdés (07-runbook 1.):** a négyállapotú prompt (opciók + „nincs megfelelő opció” / „hiányzik a döntéshez
  szükséges adat” / „a kérés kívül esik a feladaton”) önmagában behozza-e a 06 fejének nyereségét, és a rá tanított fej
  (B1-4R) javít-e mellette; a gyakorlati végpont: az előre kiválasztott hibaszint mellett hány ügyet zár le helyesen a
  rendszer (Geifman–El-Yaniv 2017 szelektív előrejelzése a mi döntéshelyzetünkre).
- **Adat:** családonként friss CAL 500 + TESZT 1000, új sablonokkal (nyelvenként 15 + 30), a 06 T500-ának 120–124
  sabloncsoportjától diszjunktan (közös sabloncsoport: 0); MATCH 60% / NO_MATCH 20% / MISSING_DATA 10% /
  OUT_OF_SCOPE 10%, fele magyar, fele angol. A címkeaudit (300 item, vakon, Dani): 300 / 300, 0 hiba, a felső korlát
  0,99% ≤ 2%. A Gemma második ítélete triage: 89,6% egyezés, itemet nem töröltünk.
- **Karok:** B1-S és B1-R (a 06 prompt és a 06 fej, a 06 receptjével újratanítva, a fold-modellek elmentve; a 06
  TESZT-en bitre azonos az F0 reprodukcióval); B1-4S (az új prompt saját pontszáma) és B1-4R (a D_meta-n előtanított,
  a 06 T500-án finomhangolt fej, 15 kis jellemző, a választott válasz sorának rejtett állapotai); referenciák B1-N,
  B1-LR, B1-4LR, B1-R0, B1-4R0. A fejek a rögzítés előtt készültek (F3R), a friss adatot nem látták.
- **Helyesség:** szigorú; a négyállapotú kereten négyosztályos (SELECT csak a gold opción, X csak NO_MATCH-en, Y csak
  MISSING_DATA-n, Z csak OUT_OF_SCOPE-on).
- **K1:** ΔAURC (B1-4R − B1-4S) a TESZT-en; a 06 8.3 szabálya a D4-gyel (≥ 2 család javul; az átlag aránya ≤ 0,90; a
  95%-os felső határ < 1).
- **K2:** a τ a CAL-on, csak a lezárható javaslatokon (SELECT és X / NONE), a lezárás precizitásának CP-alsó határa
  ≥ 0,95 és ≥ 200 lezárt ügy; a TESZT-en a hasznos lefedettség (helyesen lezárt / összes) és a lezárási hibaarány
  (hibásan lezárt / összes lezárt). Következtetés a három család egyenlő súlyú átlagán (D10): „behozza” = a B1-4S −
  B1-R alsó határa > −0,03 és mindkét kar hibaaránya ≤ 5%; „javít mellette” = a B1-4R − B1-4S alsó határa > 0 és a
  B1-4R hibaaránya ≤ 5% (ha a felső határ 5% fölött: „bizonytalan”). Munkapont nélkül a kar semmit nem zár le.
- **Statisztika:** sabloncsoportos klaszteres bootstrap (10 000 replika, seed 20261101), a CAL és a TESZT külön, a τ
  replikánként újra, a három seed mérőinek átlaga replikánként; kétoldali bootstrap-p, Holm a családokra leíróan.

## Önellenőrzés

- A szeletek: CAL 500 (30 sabloncsoport), TESZT 1000 (60) mindhárom családon; a 07 sablonok és a 06 sablonjai
  diszjunktak. A K07F3 pecsétmanifest 78 fájl, teljes; a `befagyaszt07 ellenoriz` az F5 előtt rendben.
- A pontozó út a 06 TESZT-en 0 eltéréssel adta vissza a tanítás közben mért pontszámokat és az F0 reprodukciót.
- A próba (06 CAL / TESZT, F4) 0,503-as K1-arányt és „nem hozza be” / „javít mellette” ítéletet jósolt; a friss
  adat ugyanezt adta (0,507). A 06-os pár aránya friss adaton 0,204, a 06 F5-é 0,205.
- A seedek közti eltérés a TESZT-AURC-ban ≤ 0,0011 (B1-4R), ≤ 0,0008 (B1-R).
- A banki B1-4R munkapontja törékeny: a pontbecslésnél van τ (2,72–3,09 logit), de a replikák 18%-ában nincs; ez a
  K2 banki intervallumát szélesíti (ld. 5.).
- **Az elemző eredete (2026-11-01 13:00, utólagos ellenőrzés):** a magyar bontást 09:44–09:45-kor, a rögzítés után
  közvetlenül a manifestelt `elemzes07.py`-ba írtam, burkoló helyett; a `befagyaszt07 ellenoriz` ezt később eltérésként
  jelezte. A rögzített változatot a szerkesztések visszafordításával helyreállítottam (a hash a manifesttel egyezik), a
  nyelvi bontás az új `elemzes07n.py`-ban él. A rögzített elemző újrafuttatása (`kor07/eredmenyek/F5/ellenorzes_rogzitett/`)
  a közzétett `elemzes.json` mind az 1308 közös számát bitre visszaadja; a többlet csak a 7. pont.

## Összefoglalás

1. **A K1 szabály teljesül:** a fej a négyállapotú prompton is felezi az AURC-t (arány 0,507 [0,459; 0,562]), mindhárom
   családon, Holm-p < 0,001.
2. **A prompt önmagában nem hozza be a 06 fejet:** AURC-ban 45%-kal rosszabb nála (arány 1,45 [1,34; 1,57]), a K2-ben a
   bankon nincs munkapontja, az átlagos hasznos lefedettsége 36,9% a B1-R 66,6%-a ellen (−29,6 pont [−34,2; −15,2]).
3. **A fej a prompt mellett javít** a K2-ben is: +27,9 pont [7,8; 33,5] hasznos lefedettség, a lezárási hiba 2,5%
   [1,7; 4,1] (a hibafeltétel teljesül).
4. **A B1-4R a lezárásban a 06 B1-R-rel egyenértékű** (−1,7 pont [−21,4; 2,0]), a többlete az állapotjelzés: a
   hibaelhárításon a hiányzó adatok 67%-át és a hatókörön kívüli kérések 61%-át, a szabálycsaládon 51%-át és 16%-át
   helyesen jelzi; a bankon egyiket sem (0% / 0%). A 06-os prompt ezt nem tudja.
5. **A 06 eredménye friss sablonokon is áll:** B1-R − B1-S aránya 0,204 [0,186; 0,222].

## 1. K1 — AURC a TESZT-en (szigorú helyesség)

| család | B1-S | B1-N | B1-LR | B1-R | B1-4S | B1-4LR | B1-4R | B1-4R0 |
|---|---|---|---|---|---|---|---|---|
| bank | 0,1397 | 0,1002 | 0,0643 | 0,0503 | 0,0952 | 0,0707 | **0,0491** | 0,1072 |
| hibaelhárítás | 0,2277 | 0,0841 | 0,0555 | 0,0427 | 0,0406 | 0,0374 | **0,0229** | 0,1049 |
| szabálycsalád | 0,3044 | 0,1126 | 0,0675 | 0,0438 | 0,0629 | 0,0326 | **0,0287** | 0,0643 |
| átlag | 0,2239 | 0,0990 | 0,0624 | 0,0456 | 0,0662 | 0,0469 | **0,0336** | 0,0921 |

| pár | bank Δ [95%] | hibaelhárítás Δ [95%] | szabálycsalád Δ [95%] | átlag arány [95%] | 8.3 + D4 |
|---|---|---|---|---|---|
| **K1: B1-4R − B1-4S** | −0,046 [−0,055; −0,038] | −0,018 [−0,026; −0,009] | −0,034 [−0,042; −0,026] | **0,507 [0,459; 0,562]** | **teljesül** (3/3, Holm-p < 0,001) |
| 06: B1-R − B1-S | −0,090 [−0,105; −0,076] | −0,185 [−0,212; −0,159] | −0,261 [−0,285; −0,237] | 0,204 [0,186; 0,222] | teljesül |
| B1-4LR − B1-4S | −0,024 [−0,031; −0,018] | −0,003 [−0,018; 0,015] | −0,030 [−0,041; −0,015] | 0,708 [0,608; 0,826] | teljesül (hiba p = 0,64) |
| B1-4R − B1-4LR | −0,022 [−0,033; −0,012] | −0,014 [−0,029; −0,002] | −0,004 [−0,014; 0,003] | 0,716 [0,630; 0,823] | leíró |
| kereszt: B1-4S − B1-R | +0,045 [0,036; 0,054] | −0,002 [−0,010; 0,005] | +0,019 [0,012; 0,026] | 1,453 [1,341; 1,565] | leíró (D13) |
| kereszt: B1-4R − B1-R | −0,001 [−0,006; 0,003] | −0,020 [−0,027; −0,012] | −0,015 [−0,022; −0,008] | 0,737 [0,665; 0,814] | leíró (D13) |

- A finomhangolás nélküli B1-4R0 rosszabb a B1-4S-nél (bank, hiba): a T500 finomhangolása lényeges, mint a 06-ban.
- A B1-4LR (tíz jellemző, D12) a bankon és a szabálycsaládon a fej közelében jár, a hibaelhárításon nem javít a
  prompton; a fej többlete a B1-4LR felett a bankon és a hibaelhárításon van.
- **E-AURC (leíró, promptok között nem összevethető):** B1-4S 0,055 / 0,029 / 0,042, B1-4R 0,009 / 0,011 / 0,008; B1-S
  0,098 / 0,192 / 0,267, B1-R 0,009 / 0,007 / 0,006.

## 2. A döntések (prompttulajdonság)

| család | helyes döntés 4 / 06 | OOS → | MISSING → | NO_MATCH SELECT 4 / 06 | MATCH-en nem opció 4 / 06 |
|---|---|---|---|---|---|
| bank | 0,732 / 0,726 | X 100 | SELECT 99, X 1 | 66 / 74 | 0 / 0 |
| hibaelhárítás | 0,850 / 0,746 | Z 61, Y 37, X 2 | Y 67, X 18, SELECT 15 | 61 / 37 | 2 / 14 |
| szabálycsalád | 0,805 / 0,739 | X 80, Z 16, Y 4 | Y 51, SELECT 49 | 51 / 53 | 0 / 0 |

- A négy állapot megkülönböztetése **családfüggő**: a hibaelhárításon és a szabálycsaládon a hiányzó adatot a B1 az
  esetek felében–kétharmadában jelzi, a bankon soha (az azonos összegű ikerpárnál választ); a hatókörön kívüli kérést
  a bankon és a szabálycsaládon főként X-nek mondja (ami a lezárható ágon marad, és a τ szűri), Z-nek csak a
  hibaelhárításon.
- A NO_MATCH-on a hibaelhárítás SELECT-je 37 → 61: az új prompt itt többször választ rossz okot, mint a régi.

## 3. D20 — a nyereség bontása

| család | B1-4S SELECT / nem-SELECT | B1-4R SELECT / nem-SELECT | B1-S SELECT / NONE | B1-R SELECT / NONE |
|---|---|---|---|---|
| bank | 0,052 / 0,731 | 0,035 / 0,118 | 0,047 / 0,777 | 0,036 / 0,135 |
| hibaelhárítás | 0,016 / 0,170 | 0,012 / 0,091 | 0,016 / 0,729 | 0,009 / 0,217 |
| szabálycsalád | 0,021 / 0,436 | 0,020 / 0,057 | 0,060 / 0,764 | 0,034 / 0,096 |

A fej nyeresége mindkét prompton főként a nem-SELECT (X / Y / Z, illetve NONE) javaslatok rendezéséből jön; a
SELECT-javaslatokon a B1-4R a bankon és a hibaelhárításon javít, a szabálycsaládon nem.

## 4. K2 — hasznos lefedettség és lezárási hibaarány (τ a CAL-on)

| kar | bank lef. [95%] / hiba | hibaelhárítás lef. / hiba | szabálycsalád lef. / hiba | **átlag lef. [95%]** | **átlag hiba [95%]** | munkapont nélkül (replika) |
|---|---|---|---|---|---|---|
| B1-S | 0 / – | 0 / – | 0 / – | 0,0% | – | 100% |
| B1-N | 0 / – | 45,7% / 1,5% | 0 / – | 15,2% [0; 46,8] | – | 44% |
| B1-LR | 53,7% / 3,4% | 49,4% / 2,4% | 50,6% / 3,3% | 51,2% [19,1; 58,0] | 3,0% [2,2; 5,0] | 12% |
| **B1-R** | 64,2% [58,9; 68,5] / 2,8% | 66,1% [60,2; 72,5] / 2,6% | 69,3% [65,0; 72,8] / 3,2% | **66,6% [63,7; 69,5]** | **2,9% [2,1; 4,4]** | 0% |
| **B1-4S** | 0 [0; 44,3] / – | 59,2% [44,6; 69,7] / 4,7% | 51,6% [46,0; 55,0] / 2,8% | **36,9% [31,6; 52,4]** | – [2,3; 5,7] | 31% (bank 90%) |
| B1-4LR | 0 [0; 55,2] / – | 60,6% / 2,7% | 69,9% / 3,2% | 43,5% [23,8; 63,4] | – [2,4; 4,8] | 23% |
| **B1-4R** | 59,4% [0; 68,0] / 2,5% | 62,9% [55,3; 72,8] / 1,3% | 72,2% [69,5; 74,6] / 3,8% | **64,8% [44,4; 69,8]** | **2,5% [1,7; 4,1]** | 6% (bank 18%) |

| összevetés (hasznos lefedettség, pont) | átlag Δ [95%] | bank | hibaelhárítás | szabálycsalád | ítélet (D10) |
|---|---|---|---|---|---|
| behozza? B1-4S − B1-R | **−29,6 [−34,2; −15,2]** | −64,2 [−68,1; −22,1] | −6,9 [−18,5; 2,1] | −17,7 [−23,0; −13,4] | **nem hozza be** |
| javít mellette? B1-4R − B1-4S | **+27,9 [7,8; 33,5]** | +59,4 [0; 67,4] | +3,7 [−5,5; 16,3] | +20,6 [17,2; 25,8] | **javít mellette** (hiba 2,5% ≤ 5%) |
| B1-4R − B1-R (leíró) | −1,7 [−21,4; 2,0] | −4,8 [−63,8; 1,5] | −3,2 [−9,8; 4,7] | +2,8 [0,6; 5,9] | egyenértékű; a bankon törékeny |
| B1-R − B1-S (06) | +66,6 [63,7; 69,5] | +64,2 | +66,1 | +69,3 | a 06 D20-sora friss adaton |

**Külön sor — a nem lezárt ügyek és a helyes jelzés (B1-4R):**

| család | lezárt | nem lezárt: adatbekérés / továbbítás / τ alatt | helyes adatbekérés (Y a MISSING_DATA-n) | helyes továbbítás (Z az OOS-on) |
|---|---|---|---|---|
| bank | 60,9% | 0,2% / 0,0% / 38,9% | 0% | 0% |
| hibaelhárítás | 63,7% | 11,2% / 6,3% / 18,8% | 67% | 61% |
| szabálycsalád | 75,0% | 5,5% / 1,6% / 17,9% | 51% | 16% |

A 06-os prompton mindkét arány 0: ott a B1 nem tudja jelezni. A felső korlát az összetételből 80% (MATCH + NO_MATCH).

## 5. Korlátok

- **A banki munkapont törékeny** a négyállapotú kereten: a B1-4R τ-ja a CAL-on a replikák 18%-ában nem éri el a
  95%-os CP-feltételt (a B1-R-é mindig), ezért a bank K2-intervalluma [0; 68] széles, és az átlag alsó határa (44,4%)
  ezt viszi. A pontbecslés (59,4%) és a lezárási hiba (2,5%) rendben; a következtetés a bankon „bizonytalan” lenne, ha
  csak a bankot néznénk. A bankon a B1-4 a MISSING_DATA-t egyszer sem jelzi (ikerpár), így a négyállapotú promptnak
  ott nincs többlete a 06-os felett.
- **A K2 „javít mellette” ítélet** az átlagon áll; családonként a hibaelhárításon nem szignifikáns (+3,7 [−5,5;
  16,3]), mert ott a B1-4S önmagában is lezár 62%-ot.
- **Az állapotjelzés részleges:** a hatókörön kívüli kérést a bankon és a szabálycsaládon a B1 X-nek mondja, nem
  Z-nek; a termékfunkcióhoz („továbbítom”) ez a bankon 0%, a szabálycsaládon 16% találatot jelent. A hibaelhárításon
  működik (61%).
- **Szintetikus adat:** a 07A a 06 családtervének friss sablonjain mér; a valódi átvitel a 07B dolga. A B0 szerint a
  valódi banki forgalomban a hatókörön kívüli tétel ≈ 24%, a NO_MATCH ritkább, az ikerjelölt gyakori.
- **A B1-R − B1-S 06-os pár** itt a fő eredmény mellett leíró; a 06 szabálya friss sablonokon is teljesül, de ez nem
  új állítás, hanem a 06 megerősítése új sablonokon.
- **E-AURC** csak leíró; az optimum levonása után is az alapmodell hibaarányától függ (D13).

## 6. Értelmezés és a döntési kapcsolás

- **1. ág (a prompt önmagában behozza a fejet): nem.** A négyállapotú prompt a saját pontszámával gyengébb a 06
  fejnél, és a bankon munkapont nélkül marad.
- **2. ág (a fej a prompt mellett is javít): igen.** A K1 szabály teljesül, a K2-ben +27,9 pont hasznos lefedettség az
  5%-os hibafeltétel mellett. A fej fejlesztése a négyállapotú prompton indokolt.
- **3. ág (a többlet főként az állapotjelzés): a fej többlete a 06 B1-R-hez képest ez.** A lezárásban a kettő
  egyenértékű; amit a B1-4R hozzátesz, az a hiányzó adat és a hatókör jelzése a hibaelhárításon és a szabálycsaládon, és
  a kisebb AURC ugyanott. A bankon ez a többlet nincs meg. **A termékfunkció (megalapozott döntés / adatbekérés /
  továbbítás) a hibaelhárítás és a szabálycsalád típusú feladatokon indokolt; a banki párosításnál a 06 fej marad.**
- A 06 eredménye friss sablonokon változatlan: a tanított megbízhatósági fej a B1 saját pontszámánál ötödére csökkenti
  az AURC-t.

## 7. Magyar bontás

(a τ a teljes CAL-on, a TESZT nyelvi részén mérve; 500 item nyelvenként és családonként; rögzítés utáni kiegészítés,
`elemzes07n.py`, ld. Önellenőrzés)

| család | nyelv | AURC B1-S / B1-R / B1-4S / B1-4R | Δ B1-4R − B1-4S [95%] | Δ B1-R − B1-S [95%] | K2 B1-R lef. [95%], hiba [95%] | K2 B1-4R lef. [95%], hiba [95%] | K2 B1-4S lef. |
|---|---|---|---|---|---|---|---|
| bank | hu | 0,124 / 0,047 / 0,085 / 0,045 | −0,040 [−0,053; −0,028] | −0,077 [−0,088; −0,067] | 67,7% [62,8; 71,2], 2,7% [1,0; 5,1] | 60,9% [0; 69,9], 1,9% [0,2; 4,9] | 0% |
| bank | en | 0,156 / 0,054 / 0,103 / 0,054 | −0,049 [−0,061; −0,039] | −0,102 [−0,131; −0,076] | 60,7% [54,6; 66,9], 3,0% [1,4; 5,2] | 57,9% [0; 66,4], 3,0% [0,5; 5,4] | 0% |
| hibaelhárítás | hu | 0,199 / 0,048 / 0,040 / 0,022 | −0,017 [−0,028; −0,008] | −0,151 [−0,185; −0,118] | 60,1% [53,2; 70,0], 2,8% [0,9; 7,0] | 63,0% [53,7; 75,3], 1,9% [0,6; 7,1] | 60,0% |
| hibaelhárítás | en | 0,252 / 0,039 / 0,040 / 0,024 | −0,016 [−0,028; −0,003] | −0,213 [−0,252; −0,175] | 72,2% [66,8; 76,2], 2,4% [0,8; 4,9] | 62,8% [55,8; 71,7], 0,6% [0,0; 2,5] | 58,4% |
| szabálycsalád | hu | 0,335 / 0,062 / 0,074 / 0,035 | −0,039 [−0,050; −0,027] | −0,272 [−0,308; −0,236] | 63,1% [57,7; 67,8], 4,5% [2,4; 8,1] | 67,7% [64,0; 71,2], **5,6% [3,2; 8,2]** | 47,6% |
| szabálycsalád | en | 0,306 / 0,029 / 0,053 / 0,025 | −0,029 [−0,041; −0,012] | −0,277 [−0,312; −0,241] | 75,6% [71,8; 78,3], 2,0% [0,6; 4,8] | 76,6% [74,1; 78,9], 2,2% [0,7; 4,2] | 55,6% |

- A K1 nyereség mindkét nyelven, mindhárom családon 0 alatt van; magyarul a bankon és a szabálycsaládon nagyobb.
- A magyar részszelet nehezebb: a B1-R és a B1-4R AURC-ja magyarul a szabálycsaládon kétszerese az angolnak, a
  bankon fordítva (az angol a nehezebb).
- **K2 magyarul a szabálycsaládon:** a B1-4R lezárási hibája 5,6% [3,2; 8,2], a B1-R-é 4,5% [2,4; 8,1] — a τ a teljes
  (kétnyelvű) CAL-on készül, és a magyar részen mindkét kar a hibafeltétel határán jár. A nyelvenkénti τ nem része a
  tervnek; a rögzítés után nem módosítjuk, de a 07B-nek (csak magyar) ez figyelmeztetés.

## Lezárás

- A 07A kérdései megválaszolva a friss teszten; a szabály és a végpontok a rögzítés előtt álltak, utólag nem
  módosultak. A döntési kapcsolás: a 2. ág (a fej fejlesztése) és a 3. ág (termékfunkció a hibaelhárítás / szabály
  típusú feladatokon) együtt.
- **Következő:** a 07B (valódi banki adat a <tenant> tükrén, befagyasztott eljárással: B0 kész, D7 Danié); a
  diagnosztikai minta 3. köre (konstrukció Danié); a banki MISSING_DATA-jelzés hiánya külön kérdés (a 06 D21
  ikerpárja: azonos összeg, azonos esedékesség).

## Függelék: utólagos feltáró elemzés (2026-11-01, nem a rögzített elemzés része)

A kérdés: miért nem jelez a B1-4 a bankon. **Feltáró:** a CAL és a TESZT az F5-ben elköltve, az itt választott küszöb
csak friss adaton igazolható. Gépi lap és script: `kor07/eredmenyek/F5/feltaro/bank_jelzes.{md,json}`,
`kor07/eszkozok/feltaro07.py` (a kérdések és a küszöbválasztás a futás előtt a fejlécben).

**A hiányzó adat jele megvan, csak a döntés nem használja.** A bank MISSING_DATA itemein a B1-4 99%-ban a két
azonos összegű iker egyikét teszi első helyre, és a valószínűség megoszlik köztük. Az ikerarány (a top-1 azonos
összegű párjának valószínűsége a top-1-éhez képest, gold nélkül számolható) a MISSING itemeken medián 0,68, a gold-ikres
MATCH itemeken 0,02. A szétválasztás:

| mérő (SELECT-döntéseken, MISSING vs MATCH, TESZT) | AUROC |
|---|---|
| ikerarány | 0,998 |
| top-1 − top-2 (fordítva) | 0,998 |
| p(Y) | 0,959 |

A p(Y) medián 0,03, ezért az argmax sosem Y. Ezért marad a fej munkája annyi, hogy ezeket τ alá tolja.

**Ikerszabály** (Y, ha a top-1-nek azonos összegű párja legalább r* = 0,10 arányú; r* a CAL-on, a MATCH legfeljebb 5%-a
fordulhat), hatás a TESZT-en:

| B1-4R a bankon | szabály nélkül (= F5) | ikerszabállyal |
|---|---|---|
| helyes adatbekérés a MISSING_DATA-n | 0% | 99% |
| MATCH átfordul Y-ra | – | 24 / 600 |
| szigorú helyesség (négyosztályos) | 73,2% | 80,7% |
| hasznos lefedettség [95%] | 59,4 [0; 68,0] | 57,5 [0; 66,4] |
| lezárási hiba [95%] | 2,5 [0,7; 4,9] | 2,2 [0,7; 4,3] |
| τ alatt | 38,9% | 28,7% |
| munkapont nélküli replika | 18% | 23% |

A hasznos lefedettség különbsége −1,9 pont [−23,4; 0]. A szabály tehát **nem zár le többet**, hanem a döntésképtelen
banki esetek negyedét helyes adatbekéréssé alakítja, a lezárási hiba romlása nélkül. Ez a 3. ág termékfunkciója a
bankon, döntési szabályként.

**A hatókörön kívüli kérés a bankon konstrukciós kérdés, nem küszöbkérdés.** A banki OOS itemek bér-, adó- vagy díj
jellegű tételek a „melyik számlát egyenlíti ki” kérdéssel. A B1-4 mind a 100-ra X-et mond, ami az enyhe mérce szerint
helyes. A Z-arány p(Z) / (p(X) + p(Z)) az OOS-on kisebb, mint a NO_MATCH-en (AUROC 0,23), küszöbbel nem javítható: a
CAL-on választott szabály a TESZT-en rontana (73,2% → 71,6%). A Z szövege („A kérés kívül esik a feladaton”) erre a
tételre nem illik, mert a kérés a feladaton belül van, csak a tétel nem számlakiegyenlítés. A szabálycsaládon a
Z-arány-szabály segít (helyes továbbítás 16% → 49%, 7 / 200 NO_MATCH fordul, szigorú helyesség 80,5% → 83,1%), a
hibaelhárításon nincs mit javítania.

**Javaslat a következő körre** (döntés Danié):
1. Ikerszabály a döntési rétegben az azonos összegű jelöltes feladatokra, friss adaton igazolva.
2. A banki OOS újragondolása: családspecifikus Z-szöveg („a tétel nem számlakiegyenlítés: bér, adó, díj, kamat”), vagy
   az X elfogadása ezeken a tételeken.
3. A 07B-re ez közvetlenül vonatkozik: a B0 szerint a valódi <tenant>-forgalom ≈ 24%-a ilyen tétel. Előre rögzíteni kell,
   hogy ott az X helyes lezárásnak számít-e (b0.md 6. pont, 6. kérdés).

## Függelék: K3, a diagnosztikai minta (2026-11-01 este, külön közölt)

A K3 a fő szabálynak nem része; a teljes lap: `kor07/eredmenyek/K3/eredmenylap.md`. Röviden: a valóban összetéveszthető
jelöltek közti tévedést (részfizetés, mértékegység-váltás, nettó / bruttó, deviza; a B1 a SELECT-ek 46–76%-ában a
csalit választja) egyik kar sem ismeri fel a három család átlagában. A B1 bizonyossága fordított (AUROC 0,41), a
B1-4R a véletlen szintjére húzza (0,45 [0,39; 0,51]; SELECT-AURC −0,053 [−0,091; −0,013]). A bankon a B1-4R a
legerősebben fordított (0,21). Ezekre a termékben determinisztikus ellenőrzés kell, nem megbízhatósági fej.
