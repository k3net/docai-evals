# Runbook 07: állapotjelző B1 és a megbízhatósági fej; átvitel valódi adatra

**Megmarad-e a célterületen tanított megbízhatósági fej előnye, ha a B1 maga is jelezheti, hogy nincs megfelelő opció,
hiányzik az adat, vagy a kérés kívül esik a feladaton? És mi visz át ebből valódi magyar adatra?**

- **Verzió:** v0.2 vázlat, 2026-10-31. Dani iránya a 06 eredménylapja után és a hat pontosítása (D9–D14); a nyitott
  döntések a 9. pontban.
  **Státusz:** Dani az F0–F1 tervezési próbát elindította (2026-10-31). A v1 rögzítése előtt a D1–D8 véglegesítendő.
- **Előzmény:** a [06-runbook](06-runbook.md) F5-je (`kor06/eredmenyek/F5/eredmenylap.md`).
  - **Az előre rögzített szabály teljesült:** a B1-R/B1-S átlagos AURC-aránya 0,205 [0,187; 0,224].
  - **A nyereség 72%-át azonban a NONE-javaslatok hátrasorolása is elhozza.** A B1 mind a 100 OUT_OF_SCOPE-itemre NONE-t
    mond, biztosan, és ezt a szigorú helyesség hibának számítja.
  - **A B1 SELECT-hibáinak 92–99%-a állapothiba:** hiányzó adat vagy nem-egyezés mögött választott opció. Rossz opció
    MATCH-en családonként csak 1–7 van.
  - **Dani (2026-10-31):**
    - a 06 sikeres a vállalt kérdésben, a sikerkritériumot utólag nem módosítjuk;
    - a fej jelenleg főleg azt ismeri fel, hogy egyáltalán indokolt-e dönteni.
- **Két rész:**
  - **07A:** az állapotjelző B1 a szintetikus családokon;
  - **07B:** egy család valódi magyar adaton, feltáró jelleggel, automatikus végrehajtás nélkül.
  - A 07B a 07A befagyasztott modelljeit értékeli, ezért utána jön.
- **Adatelv:** mint a 06-ban.
  - Tanítás csak publikus és szintetikus adaton.
  - Valós tenantadat csak értékelésre (Dani, 2026-10-28), csak aggregátum publikálható.
- **A H tartalmi fej hátrébb sorolva** (Dani): a 07-ben nincs H-kar.
- **Gép és szabályok:** mint a 06-ban.
  - spark-dev, egyszerre egy nagy GPU-folyamat;
  - ≥ 15 GB szabad memória terhelés alatt, modellbetöltés mellett nincs CPU-feladat;
  - a Qwen-család csak alany;
  - a pecsét alatti kimenetekről a rögzítés előtt csak darabszám és idő kerül naplóba.

---

## 1. Kérdések

- **K1 (07A, fő):** az állapotjelző B1 változatlan döntésein javít-e a rangsoron az új bemenetekre tanított fej
  (B1-4R − B1-4S)?
  - Ez ugyanaz a kérdés, mint a 06 K1-e, csak most a B1 válaszlehetőségei illeszkednek a feladathoz.
  - Ugyanazon a prompton a két kar ugyanazokat a döntéseket rangsorolja, ezért a ΔAURC itt is tisztán sorrendjavulás.
- **K2 (07A, gyakorlati):** az előre rögzített hibaszint mellett hány ügyet zár le helyesen a négy kar?
  - **Lezárt ügy:** a τ fölött elfogadott SELECT, vagy a τ fölött elfogadott „nincs megfelelő opció”.
  - **Nem lezárt ügy:** az adatbekérés („hiányzó adat”), az emberhez továbbítás („kívül esik”) és a τ alatti item.
  - **A precizitás csak a lezárt ügyeken számolódik (D9):** a helyes adatbekérés és továbbítás nem javítja.
  - A két prompt közti különbség itt már nem tisztán sorrend, mert a prompt a döntéseket is megváltoztatja. Ezért a
    döntések helyességét (3.1), a sorrendet és a lezárt ügyeket külön közöljük (Geifman–El-Yaniv 2017: szelektív
    osztályozás).
- **K3 (07A, diagnosztikai):** felismeri-e a fej a valóban összetéveszthető jelöltek közti tévedést? Erre van külön
  minta (3.3), mert a természetes összetételben erre alig van eset.
- **K4 (07B, feltáró):** valódi banki tételeken mit visz át a szintetikus tanítás a befagyasztott modellekből?

**Az eredmény és a következő lépés előre rögzített kapcsolata** (Dani iránya; a küszöbök a D5-ben):
- ha az állapotjelző B1 önmagában behozza az előnyt (B1-4S nem rosszabb a B1-R-nél K2-ben), az egyszerűbb megoldás
  megy tovább;
- ha mellette is érdemben javít a fej (B1-4R a B1-4S-nél, különösen valódi adaton), indokolt a megbízhatósági fej
  fejlesztése;
- ha főleg az állapothibákat fogja meg, ez lesz a termékfunkció: engedje a megalapozott döntést, kérjen adatot, vagy
  adja tovább a bizonytalan ügyet.

## 2. Karok (07A)

| kar | a B1 válaszlehetőségei | megbízhatóság | szerep |
|---|---|---|---|
| **B1-S** | a 06-os: opciók + „Egyik sem” | a B1 saját pontszáma | a 06 referenciája |
| **B1-R** | a 06-os | a 06 fej, a 06 receptjével és T500-ával (2.1) | a 06 eredménye friss teszten |
| **B1-4S** | opciók + három állapot (2.2) | a B1 saját pontszáma a választott válaszon | az egyszerűbb megoldás |
| **B1-4R** | mint a B1-4S | az új bemenetekre tanított fej, ugyanannyi (T500) példával | a K1 fő vizsgálata |
| B1-LR, B1-4LR | a 06-os, illetve a négyállapotú | a B1-LR az ötjellemzős L2-logisztikus regresszió (06); a B1-4LR ugyanez az új kimenetekkel bővítve (2.3) | egyszerű referencia mindkét prompton |
| B1-N | a 06-os | a B1-S, a NONE hátra | a 06 D20-sora, friss teszten |

### 2.1 A 06 fej friss teszten

- A 06 F5 a finomhangolt fejeket nem mentette el, csak a pontszámokat (`cache/k06/f5/<család>/f1.json`). Megvan
  viszont az előtanított B1-R0 (`cache/k06/b1rel`).
- **A friss teszthez a B1-R-t újratanítjuk** a 06 receptjével, ugyanazzal a T500-zal és ugyanazokkal a seedekkel.
- **Az F0-ban ellenőrizzük, hogy az újratanítás reprodukálja-e** a 06 TESZT-pontszámait az `f1.json`-ból. Eltérésnél
  az eltérés nagyságát közöljük.
- A 07-ben a fejeket elmentjük, hogy a 07B változatlanul használhassa őket.

### 2.2 Az állapotjelző B1

- **A négy válaszlehetőség:**
  - ezt az opciót választom (A, B, C, …);
  - nincs megfelelő opció;
  - hiányzik a döntéshez szükséges adat;
  - a kérés kívül esik a feladaton.

  A címkék és a szövegek: D1.
- **A gold:** MATCH → az opció; NO_MATCH → „nincs megfelelő”; MISSING_DATA → „hiányzó adat”; OUT_OF_SCOPE → „kívül esik”.
- **Helyesség:**
  - a szigorú 06-os helyességnek itt a négyosztályos pontosság felel meg;
  - a 06-os enyhe helyességnek a „nem-MATCH a nem-MATCH-en” változat.
- **Saját pontszám:** a négy opciósorrendre átlagolt valószínűség a választott válaszon. A temperature-t újra kell
  illeszteni (D2); a 06 temperature-je és τ-ja nem öröklődik.
- **Új kód kell.** A 05 kiolvasója a v1a-manifest része, nem módosítható. A 07 saját keretet és kiolvasót kap
  (`kor07/eszkozok/`), a 06 `kiolvas06` mintájára (burkoló, saját promptkerettel és spanokkal).

### 2.3 A B1-4LR jellemzői (D12)

- A négyállapotú változat egyszerű referenciája az új kimeneteket is használja, hogy a B1-4R többletét egy ugyanazon
  bemenetekből dolgozó egyszerű módszerhez mérjük:
  - az X, Y és Z válasz valószínűsége (a négy sorrend átlaga);
  - a választott válasz típusa (opció / X / Y / Z, indikátorok);
  - a 06 jellemzői: top-1 − top-2, a B1 pontszáma, a sorrend-egyetértés.
- L2-logisztikus regresszió, C a {0,01; 0,03; 0,1; 0,3; 1} rácson, sablonos ötszörös CV, mint a 06-ban.
- **A jellemzőlista rögzítve (2026-11-01, az F1 végén, a friss adat kiolvasása után, de a pecsét nyitása előtt; a
  friss adatot sem a lista, sem a fej nem látta):** top-1 − top-2, a választott válasz valószínűsége (q), a sorrendek
  egyetértése, p(X), p(Y), p(Z), és a válasz típusának négy indikátora (opció / X / Y / Z) — 10 jellemző
  (`b1rel07.LR4_JELLEMZOK`). A B1-LR a 06 öt jellemzőjével marad.

## 3. Adat (07A)

### 3.1 Tervezési próba a megismert 06 adaton

- **A szeletek:** a 06 T500, CAL és TESZT. Ezek a 06 F5 óta megismertek, ezért **csak tervezésre** valók.
  - a négyállapotú prompt szövege és címkéi;
  - a temperature illesztése;
  - a fej bemenetei és spanjai;
  - az új mérők kódja.
- **A tervezési próba számai nem állítások,** és nem részei a 07 v1-nek. A naplóba kerülnek, mert a döntéseket ezekre
  alapozzuk.
- **Ami itt már látszik:** a B1-4S döntéseinek helyessége állapotonként, vagyis hogy a B1 egyáltalán képes-e a négy
  állapotot megkülönböztetni.

### 3.2 Friss, érintetlen CAL és TESZT

- **A megerősítés friss szeleteken fut**, mindhárom családon, új sablonokkal: új szintetikus cégek, berendezések,
  szabályzatok, a T500 sablonjaitól diszjunktan.
  - A generátor a 06 `szint06`-ja a D17–D22 javításokkal; az összetétel a 06 D9-e.
  - Családonként CAL 500 + TESZT 1000 (D4).
- **A T500 a 06-os marad** (nyitott tanítóadat), a négyállapotú prompttal újrakiolvasva.
- **A címkeminőség:** címkeaudit a 06 D14 szerint (300 item, Dani), és a Gemma második ítélete triage-ként (D15).
- **Pecsét és rögzítés:** a CAL és a TESZT kiolvasása pecsételve fut, a v1 rögzítése a pecsét nyitása előtt történik
  (a 06 `pecset06` / `befagyaszt06` mintájára).

### 3.3 Diagnosztikai minta: összetéveszthető jelöltek

- **Mi kerül bele:** MATCH-itemek, ahol van helyes opció, de egy másik jelölt előre megadott tulajdonság szerint
  könnyen összetéveszthető vele.
  - **bank:** ugyanaz a partner más összeggel; ugyanaz az összeg más partnernél; egy karakterben eltérő számlaszám;
  - **hibaelhárítás:** azonos tünetű ok, amelyet csak egy megadott mérés zár ki;
  - **szabálycsalád:** szomszédos költségnem, határ közeli összeg.
- **A 06 nehéz negatívjai a B1-nek nem nehezek.** A 06 családterve már tartalmazott ilyen jelölteket, mégis 600
  MATCH-itemből csak 1, 7, illetve 5-nél választott rossz opciót a B1. Ugyanazzal a konstrukcióval a diagnosztikai
  mintán sem lenne mit rangsorolni.
  - Ezért a minta erősebb konstrukciót kap: a két jelölt a szövegben említett minden jegyben egyezik, csak egy, a
    szövegből kiolvasható részletben tér el (például a számlaszám egyetlen karaktere, a mérés egyetlen értéke).
  - **A nehezítés csak a próbamintán történik (D11).** Az F1-ben egy fejlesztési minta készül a 06 ismert sablonjain;
    ezen mérjük a B1 hibaarányát, és a konstrukció addig erősödik, amíg legalább 20% rossz opcióválasztást ad. Utána
    a konstrukció és a végső minta mérete (D6) rögzül.
  - **A végső mintát az F2 generálja friss sablonokkal, a rögzített konstrukcióval, egyszer.** A „legalább 40 rossz
    opcióválasztás” tervezési cél, nem megállási szabály: ha a friss mintán csak 17 ilyen hiba lesz, azt közöljük,
    szélesebb bizonytalansággal; újabb példákat nem generálunk, amíg összegyűlik 40.
- **Közlés:** külön minta, külön közölve; nem keveredik a természetes összetétellel, és nem része a fő szabálynak. A
  nem-SELECT válaszok arányát is közöljük: abból derül ki, ha az új B1 kitér a nehéz választás elől.
- **Mérete:** D6, az F1 próbája után rögzítve, a rögzítés után változatlan.

## 4. Végpontok (07A)

- **K1 elsődleges:** ΔAURC (B1-4R − B1-4S) a friss TESZT-en, a négyosztályos helyességgel, családonként és átlagban.
  A döntési szabály a 06 8.3-a a D4-gyel, változatlanul (D5).
- **K2 gyakorlati (D9):** két arány, mind a négy fő karon, családonként és a három család egyenlő súlyú átlagában.
  - **Hasznos lefedettség:** helyesen lezárt ügyek / összes ügy.
  - **Lezárási hibaarány:** hibásan lezárt ügyek / összes lezárt ügy.
  - **A τ a friss CAL-on, csak a lezárható javaslatokon:** a küszöbválasztásba a SELECT és a „nincs megfelelő opció”
    javaslatok kerülnek (a 06-os prompton a SELECT és a NONE); a precizitás csak ezeken számolódik, CP-alsó ≥ 0,95, és
    a „legalább 200 elfogadott” 200 lezárt ügyet jelent. A helyes adatbekérés és továbbítás nem javíthatja a lezárás
    precizitását: 100 helyes adatbekérés nem ellensúlyoz 10 hibás számlapárosítást.
  - **A felső korlát az összetételből adódik:** csak a MATCH és a NO_MATCH zárható le helyesen, vagyis az itemek 80%-a.
  - **Külön sor:** a helyes adatbekérés és a helyes továbbítás aránya a MISSING_DATA- és OUT_OF_SCOPE-itemeken (a 06-os
    prompton mindig 0, mert ott a B1 nem tudja jelezni); a nem lezárt ügyek bontása: adatbekérés, továbbítás, τ alatt.
  - Az összevetések: B1-4S − B1-R („behozza-e”), B1-4R − B1-4S („javít-e mellette”), a D5 hibafeltételével.
- **Külön sorok:**
  - **A döntések helyessége:** a B1 és a B1-4 válaszai állapotonként (tévesztési mátrix). Ez prompttulajdonság, nem
    sorrend.
  - **A sorrend:** E-AURC mindkét prompton, leíró mérőszámként (D13). Az optimum levonása után is érzékeny marad az
    alapmodell hibaarányára (Traub és mtsai 2024, arXiv 2407.01032), ezért a két prompt között nem összevethető.
    Azonos döntéseken (B1-4R − B1-4S) a ΔAURC a mérvadó; eltérő promptok között a gyakorlati következtetés a K2-re épül.
  - **A 06 D20-sora:** a B1-4R nyeresége SELECT- és nem-SELECT döntésekre bontva.
  - **K3:** a diagnosztikai mintán SELECT-AURC és a rossz opció felismerése (AUROC), B1-4S, B1-4R, B1-4LR; mellette a
    rossz opcióválasztások tényleges száma és a nem-SELECT válaszok aránya (D11).
- **Leíró:** magyar bontás kötelezően; a futások közti eltérés (D24); sablonszám; Brier és ECE.

## 5. Statisztika (07A)

- Mint a 06-ban: sabloncsoportos klaszteres bootstrap (D23), a futások átlaga replikánként (D24), 10 000 ismétlés,
  kétoldali p, a családok Holm-korrigált p-je leíró.
- **A K2 bootstrapja:** a CAL és a TESZT sablonosan újramintázva, a τ replikánként újra; a munkapont nélküli replikák
  aránya külön sor.
- **Erő:** a tervezési próba alapján becsüljük (a 06 `mde06` mintájára), tervezési becslésként. A B1-4R − B1-4S hatás
  várhatóan sokkal kisebb a 06-osnál.

## 6. 07B: valódi magyar adat egy családon

- **Család:** `penzugy.bankparositas`. A DocIT-ban 2026 júniusa óta van banki egyeztetés:
  - `bank_statement_transactions`: dátum, összeg, irány, közlemény, partner, `category` (szabály szerint `salary` /
    `tax`), `match_status`;
  - `bank_transaction_invoice`: tétel ↔ számla kötés, kötésenként `auto` vagy `manual` eredettel.
  - A másik két családhoz nem ismerünk hozzáférhető, ellenőrizhető valódi adatot.
- **Minta:**
  - 200–300 tétel, véletlenszerűen vagy időrendben kiválasztva, egy vagy több hozzájáruló tenantból (D7);
  - csak értékelés, automatikus végrehajtás nélkül;
  - célja az átvitel feltárása, nem magas precizitás igazolása.
- **Gold:** Dani címkéz, a 07A négy állapotával.
  - A `manual` kötés kiinduló javaslat lehet a MATCH-hez.
  - Az `auto` kötés nem gold, mert a rendszer saját szabálya.
- **Opciók:** a szervezet nyitott számlái **a tétel feldolgozása előtti állapotból rekonstruálva** (a kötések és a
  kiegyenlítések időbélyegéből), rögzített jelöltválasztással (például összeg és partner szerinti top-k).
  - A jelöltválasztás határozza meg, mennyi NO_MATCH lesz, ezért előre rögzítjük, és közöljük.
  - **A részfizetés és a több számlát rendező utalás besorolása előre rögzítve (D14):** nem lesz belőlük automatikusan
    NO_MATCH. Javaslat: a részfizetés MATCH a kiegyenlített számlára; a több számlát rendező utalás külön kategória, a
    fő mintából kimarad, és a számát külön közöljük. A pontos szabály a B0 után (D7).
- **Befagyasztott eljárás (D14):** a 07A fejei mellett a temperature és a τ is a szintetikus kalibrációból (a 07A
  CAL-ja) jön; a valódi adaton semmi nem illesztődik. Így mérhető tisztán az átvitel.
- **Sorrend:**
  1. Először a befagyasztott modellek (B1-S, B1-R, B1-4S, B1-4R a 07A banki fejeivel) és a természetes összetétel
     állapotonként.
  2. Ha valódi adaton is célterületi tanítás kell, az külön kör, saját tanító-, kalibrációs és új tesztmintával. Így
     elkülönül, mit visz át a szintetikus tanítás, és mit lehet valódi példákból megtanulni. [kihagyva: ügyféladat]
- **Diagnosztikai minta:** valódi összetéveszthető jelöltpárok előre megadott tulajdonságok szerint (3.3), külön
  közölve a természetes forgalomtól.
- **Adatvédelem:**
  - a valódi tételek és számlák helyben maradnak (`local-evals` mintájára), csak aggregátum publikálható;
  - hogy a kiolvasás a spark-deven futhat-e, az a D7 része.

## 7. Fázisok

| fázis | tartalom | GPU | feltétel |
|---|---|---|---|
| F0 | a 07 keret és kiolvasó; a 06 B1-R reprodukciója az `f1.json`-ra (2.1) | — | a D1–D3 |
| F1 | tervezési próba: a 06 T500 / CAL / TESZT és a fejlesztési diagnosztikai minta kiolvasása a négyállapotú prompttal; temperature; a B1-4 döntései; a diagnosztikai konstrukció és a B1-4LR jellemzőlistája rögzítve | igen | F0 |
| F1M | a D_meta újrakiolvasása a négyállapotú prompttal (a B1-4R előtanításához) | igen | F1 (a prompt végleges) |
| F2 | friss CAL + TESZT + a végső diagnosztikai minta generálása, címkeaudit (Dani), Gemma-triage | igen | F1, D4, D6 |
| F3 | a friss szeletek kiolvasása pecsételve, mindkét prompttal | igen | F2, az audit kapuja |
| **F3R** | **a fejek tanítása és mentése:** a B1-4R előtanítása a D_meta-n; a B1-4R és a B1-R finomhangolása a T500-on; a B1-LR és a B1-4LR illesztése; a temperature-ök. Mind a `cache/k07/fejek` alá mentve, és a v1 manifestjébe kerül | — (CPU) | F1M, F1; GPU-s kiolvasás mellett nem fut (memória) |
| F4 | erőbecslés, a v1 rögzítése a mentett fejekkel | — | F3, F3R, Dani „mehet”-je |
| F5 | a pecsét nyitása: a mentett fejek pontozása a CAL-on és a TESZT-en, a τ a CAL-on, az elemzés, az eredménylap | — | F4 |
| B0 | 07B megvalósíthatóság: mely tenantnál hány kivonat és kézi kötés van, a jelöltválasztás | — | D7; az F1-gyel párhuzamosan mehet (csak olvasó lekérdezés) |
| B1–B2 | a minta, Dani címkéi, a befagyasztott modellek értékelése | igen | F5, B0 |

A GPU-idő becslése az F0-ban készül, a 06 F2–F3 naplója alapján. A 06-tól eltérően a fejek a rögzítés előtt
elkészülnek, és a manifest részei; az F5 csak pontoz.

## 8. Kockázatok

- **A B1 nem tudja megkülönböztetni a négy állapotot.** Ekkor a B1-4S döntései rosszabbak lehetnek a 06-osnál, és a K2
  ezt mutatja meg. Az F1 ezt még a friss adat építése előtt kiderítheti.
- **A négyállapotú prompt eltolhatja a SELECT-döntéseket is.** Ezért a döntések helyessége külön sor.
- **A 06 B1-R újratanítása nem reprodukálja a 06 pontszámait.** Az F0 méri; kis eltérésnél a 07 friss pontszámai
  az irányadók.
- **A diagnosztikai minta a B1-nek nem nehéz.** Ekkor a K3-nak nincs eseménye. Az F1 próbája ezt méri, a konstrukció
  addig erősödik, amíg van mit rangsorolni (3.3).
- **A K1 hatása kicsi lehet.** A négyállapotú prompton a B1-4S-nek már nincsenek biztos állapothibái, a fej többlete
  a 06 „maradék 28%-ának” felel meg (ΔAURC −0,046…−0,059 a 06-ban). Ha ez az új prompton is ekkora, az 1000-es TESZT
  elég; ha kisebb, az erőbecslés nagyobb TESZT-et kérhet (D4).
- **A címkeaudit Dani idejét kéri** (300 item; a diagnosztikai mintával több).
- **07B:** a valódi összetétel nagyon eltérhet a D9-től (kevés MISSING_DATA), és a jelöltválasztás mesterséges
  NO_MATCH-eket hozhat.

## 9. Döntések (Dani)

| # | kérdés | javaslat |
|---|---|---|
| D1 | a négyállapotú prompt címkéi és szövegei | X „nincs megfelelő opció”, Y „hiányzik a döntéshez szükséges adat”, Z „a kérés kívül esik a feladaton”, mindig az opciók után; az angolban ugyanígy. A szövegeket az F1 próbája véglegesíti, a friss adat előtt. **Dani (2026-11-01): megerősítve, a szövegek maradnak** (a próbán a Z-t a B1 ritkán használja; ez eredmény, nem hiba) |
| D2 | a B1-4S temperature-je | a 06 T500-án illesztve (nyitott adat); a CAL a τ-nak marad |
| D3 | a B1-4R receptje | ugyanaz, mint a B1-R (D_meta-előtanítás + T500-finomhangolás, ugyanazok a seedek), a D_meta a négyállapotú prompttal újrakiolvasva. A D_meta állapotcímkéi a 05-ből adottak (`allapot05`: MATCH 5088 / NO_MATCH 480 / MISSING_DATA 141 / OUT_OF_SCOPE 87 pontozott item), tehát a leképezés kész; a MISSING_DATA és az OUT_OF_SCOPE ott ritka (2,4%, illetve 1,5%), ezért az előtanítás ezeket alig látja, a T500 tanítja. A B1-R a 06 receptje marad, előtanítással |
| D4 | a friss szeletek | CAL 500 + TESZT 1000 családonként, új sablonokkal; a T500 a 06-os |
| D5 | a döntési szabályok | K1: kiindulásként a 06 8.3-a a D4-gyel (B1-4R − B1-4S). **Felülvizsgálandó az erőbecslés után, a rögzítés előtt:** a B1-4S AURC-ja várhatóan sokkal kisebb a B1-S-énél, így a 10% relatív csökkenés abszolút értékben kicsi lehet, és az 1000-es TESZT erre nem biztos, hogy elég. K2 (D10): a hasznos lefedettség különbsége **a három család egyenlő súlyú átlagán**, a családonkénti eredmények kötelező közlésével. „Behozza” = a B1-4S − B1-R intervallumának alsó határa > −0,03 **és** mindkét kar teljesíti a közös hibafeltételt; „javít mellette” = a B1-4R − B1-4S intervalluma 0 fölött **és** a B1-4R teljesíti. **A közös hibafeltétel a TESZT-en:** a lezárási hibaarány pontbecslése ≤ 0,05 (a CAL-on célzott 95% precizitás tesztoldali párja). Ha a pontbecslés teljesíti, de az intervallum felső határa 0,05 fölött van, az eredmény „bizonytalan”, nem „behozta”; a CAL-on teljesített 95% önmagában nem tesztgarancia. A 0,03 és a 0,05 gyakorlati választás, mint a 06-os 10%. **Dani (2026-11-01): megerősítve az F4 erőbecslés után** (a K1 szabály a 06 8.3 + D4 marad; a D4 ereje 10%-os valódi csökkenésnél 0,98) |
| D6 | a diagnosztikai minta mérete | az F1 próbája után rögzítve, a B1 mért hibaarányából: a tervezési cél legalább 40 rossz opcióválasztás családonként (20% hibánál 200 item); a rögzítés után a méret változatlan, a tényleges hibaszám közölve (D11). **Dani (2026-11-01): megerősítve.** A minta külön közölt, nem feltétele a v1 rögzítésének; a 3. kör konstrukciója (a számszerű közelség helyett más jellegű összetéveszthetőség) még nyitott |
| D7 | 07B: a tenant(ok), véletlen vagy időrendi minta, a címkézés, a futás helye, a publikálás | bank; a hozzájáruló tenantok közül az, ahol a legtöbb kézi kötés van (a B0 méri); időrendi minta (a természetes forgalom); Dani címkéz; aggregátum publikálható |
| D8 | a H-kar | nincs a 07-ben |
| D9 | K2: a precizitás csak a lezárt ügyeken | **Dani (2026-10-31):** a τ-választásba csak a SELECT és a „nincs megfelelő opció” kerül, a ≥ 200 lezárt ügyet jelent; hasznos lefedettség és lezárási hibaarány külön (4.) |
| D10 | K2: a következtetés és a hibafeltétel | **Dani (2026-10-31):** a −3 pont a három család egyenlő súlyú átlagára; a „behozta” a közös hibafeltételhez kötve, különben „bizonytalan” (D5) |
| D11 | a nehezítés csak a próbamintán | **Dani (2026-10-31):** a 40 hiba tervezési cél, nem megállási szabály; a végső minta egyszer készül; a nem-SELECT válaszok aránya közölve (3.3, 4.) |
| D12 | a B1-4LR jellemzői | **Dani (2026-10-31):** az X/Y/Z valószínűsége, a válasz típusa és a 06 jellemzői; a pontos lista az F1 végén rögzül (2.3) |
| D13 | az E-AURC promptok között | **Dani (2026-10-31):** leíró marad; eltérő promptok között a következtetés a K2-re épül (4.) |
| D14 | 07B: a teljes eljárás befagyasztva | **Dani (2026-10-31):** a fej, a temperature és a τ a szintetikus kalibrációból; a jelöltek a tétel feldolgozása előtti számlaállapotból; a részfizetés és a több számlát rendező utalás besorolása előre (6.) |

## Napló

- **2026-10-31:**
  - v0.1 Dani irányából; önellenőrzés után v0.2 a hat pontosítással (D9–D14) és az F1M / F3R sorokkal.
  - Dani: „az F0–F1 tervezési próbát elindítanám.” Az F0 első lépése a 06 B1-R reprodukciója (`k07f0_repro.sh`,
    K07F0R): a `friss06 tanit` újrafuttatása a `cache/k07/f0_repro` alá, és a pontszámok összevetése a
    `cache/k06/f5` f1.json-jaival (`repro07.py`). Indult 15:02-kor, 15:13-ra kész. **Bitre azonos:** minden kulcson
    (B1-R, B1-R0, B1-LR, H, H-T-meta; T100 / T200 / T500; CAL és TESZT) a legnagyobb eltérés 0, a B1 sorai azonosak
    (`kor07/eredmenyek/F0/repro.md`). A 2.1 reprodukciós kérdése lezárva: a 06 fejei determinisztikusan újratanulnak.
  - **F0, a négyállapotú keret:** `keret07.py` (az Y és a Z ál-opcióként, a valódi opciók keverése a 06-é; a
    tokenizerben az Y = 56, a Z = 57 egytokenes) és `kiolvas07.py` (a 05 kiolvasójának burkolója, a 06 `kiolvas06`
    mintájára). A span-ellenőrzés a 06 T500-án (3 család, 2 permutáció): 3000 prompt, 0 hiba, medián 413 token
    (`kor07/eredmenyek/F0/spanok`). A 30 mintaprompt rendben: a valódi opciók után X, Y, Z.
  - **F1 (K07F1, `k07f1_kiolvas.sh`) elindítva 15:08-kor:** a 06 három családjának T500 / CAL / TESZT szelete a
    négyállapotú prompttal, kanonikus + b1, a `cache/k07/jellemzok` alá (nyitott, a 06 v1 óta). 24 000 forward, kb. 3
    óra; a reprodukció végét megvárja. A kiolvasás 15:13-kor indult, várható vége 18:13.
  - **A nehéz próbaminta (3.3, D11): `szint07.py`**, a `szint06` burkolója a 06 T500-sablonjain, családonként 120 MATCH-terv
    (30 sablon × 4; 60 hu + 60 en), split `NEHEZ`.
    - bank: iker számla ugyanazzal a partnerrel, összeggel és esedékességgel, a számlaszám egy jegyében más (70) vagy
      két szomszédos jegye felcserélve (50); a tételben a partner és a helyes számlaszám is szerepel;
    - szabály: a költségnem másik sávja mellett az összeg a küszöb 93–99%-a vagy 101–107%-a;
    - hiba: a jelölt pár mindkét mérése a saját küszöbe 3%-os környezetében, a valódi ok épphogy teljesíti, a pár
      épphogy nem.
    - **K07F1B (`k07f1b_nehez.sh`) beállítva 15:20-kor a K07F1 mögé:** terv, Muse-generálás, final, majd kiolvasás a
      négyállapotú és a 06-os kétkimenetű kerettel (`kiolvas07 --keret 2`, `cache/k07/jellemzok2`). Várható vége kb.
      19:15.
    - Az elemzés (`b14_07.py`): temperature a 06 T500-án, a B1-4 döntései és tévesztési mátrixa, összevetés a 06
      B1-gyel ugyanazokon az itemeken; a nehéz mintán a két keret B1-je egymás mellett.
  - **Memória-lecke (15:13–15:33):** a HF-betöltés (`hf_jellemzo05.load_model`, 65 GB BF16, `device_map="cuda"`) csúcsa
    a gép teljes 121 GB-ját kéri: ~50 GB névtelen CPU-másolat a MoE-szakértők összefűzése közben. A K07F1-et kétszer
    leállítottam a ≥ 15 GB szabály szerint (15:22: 3 GB-nál, 97%; 15:31: 0 GB-nál, 80%). **A 06 öt kiolvasása azért
    élte túl, mert a spark-deven 16 GB swap van (`/swap.img`)**, és a másolat vége oda lapozódik ki; OOM-kill a gépen
    soha nem volt (`dmesg`). A `py07` konténer-korlátja (`--memory-swap`) ezt a swapot tiltotta volna; kivéve. A
    `lib07.sh` őre csak valódi kimerülésnél (elérhető < 1 GB és szabad swap < 2 GB) állít le. A ≥ 15 GB szabály a
    *betöltés utáni* állandó állapotra és a két modell együttes futására vonatkozik; a betöltési csúcsot a swap viszi.
  - **A harmadik indítás (15:33:53) átment.** A csúcs profilja (`logs/k07f1.memoria.log`): 15:39-től a swap fogy,
    15:40:37-kor a szabad swap 0 GB (elérhető 20 GB), 15:42:17-kor elérhető 3 GB, 15:42:27-től 51–52 GB elérhető és 15 GB
    szabad swap, a kiolvasás fut. A tartalék a csúcson néhány GB: a tartós megoldás egy nagyobb swap (sudo kell, Dani)
    vagy egy kisebb csúcsú betöltő; ez Dani döntése, a 07 a jelenlegi úton fut tovább. Várható vége 18:33, a K07F1B
    (nehéz minta) utána, kb. 19:30.
  - **K07F1 18:27-re, K07F1B 19:30-ra kész**, hiba nélkül. A nehéz minta: 117 / 119 / 120 item (3 bank-szöveg JSON-hibán,
    1 hiba-szöveg a kimondott ok miatt esett ki).
  - **Az F1 tervezési próba eredménye (`kor07/eredmenyek/F1/b14.md`; a 06 megismert szeletein, nem állítás):**
    - **Temperature (D2):** a 06 T500-án, 3 család együtt: 1,584 (családonként 2,32 / 0,87 / 1,27; a 06 B1-é 1,946).
    - **A négyállapotú prompt önmagában behozza a 06 fej nyereségének nagy részét.** A B1-4S saját pontszámú AURC-ja a
      TESZT-en (négyosztályos szigorú helyesség): bank 0,085 (B1-S: 0,142; a 06 B1-R: 0,048), hibaelhárítás 0,048
      (0,248; 0,044), szabálycsalád 0,066 (0,304; 0,050). A két helyességfogalom nem azonos, az összevetés tájékoztató.
    - **A döntések helyessége:** bank 0,730 (06: 0,723), hibaelhárítás 0,838 (0,734), szabálycsalád 0,797 (0,718).
    - **Tévesztés (TESZT):** az OUT_OF_SCOPE-ot a B1-4 a bankon mind a 100-szor X-nek, a szabálycsaládon 77-szer X-nek
      és 21-szer Z-nek, a hibaelhárításon 43-szor Y-nak és 52-szer Z-nek mondja: a Z-t alig használja. A MISSING_DATA-t
      Y-ként a hibaelhárításon 68 / 100, a szabálycsaládon 46 / 100, a bankon 1 / 100 ismeri fel (a banki ikerpárnál
      továbbra is választ). A NO_MATCH-on SELECT: bank 76 → 70, szabály 76 → 63, hibaelhárítás 39 → 63 (romlik). A
      MATCH-en rossz opció továbbra is 0–6. **A négy állapot megkülönböztetése tehát részleges**: ezt a K2 lezárási
      hibaaránya és a helyes továbbítás külön sora fogja megmutatni a friss teszten.
    - **A négy sorrend egyetértése** 0,89–0,94.
    - **A nehéz próbaminta 1. köre nem elég nehéz** (`b14_nehez.md`): rossz opció a bankon 0 / 117 (mindkét keret), a
      hibaelhárításon 6 / 119 (06-os keret 4), a szabálycsaládon 15 / 120 (11); magyarul a szabály 12 / 60. A B1-4 a
      nehéz választás elől nem tér ki (nem-SELECT: 0 / 1 / 0). A SELECT-AUROC 0,87 (hiba), 0,87 (szabály).
    - **D11 szerint a 2. kör a próbamintán:** bank összeg-alapú iker (két szomszédos jegy felcserélve vagy 0,5–3%; a
      tételben csak partner és összeg), hiba 1%-os küszöbközelség, szabály 98–99,5% / 100,5–102%. `szint07 --kor 2`,
      `kor07/adat/nehez2`, K07F1B2. Indult 20:24-kor.
  - **Swap (Dani, 20:40):** `/swap07.img` 48 GB a meglévő 16 mellé (`fallocate`, `mkswap`, `swapon`, fstab), összesen
    63 GB. A HF-betöltés csúcsa ettől fogva nem a gép határán jár; a `lib07.sh` őre változatlan (elérhető < 1 GB és
    szabad swap < 2 GB).
  - **A nehéz minta 2. köre (K07F1B2, 21:30-ra kész; `b14_nehez2.md`):** bank 0 / 118 rossz opció mindkét kereten
    (összeg-csere és összeg-közeli egyaránt), hibaelhárítás 7 / 119 (06-os keret 7), szabálycsalád 12 / 119 (8), ebből
    magyarul 12 / 60, angolul 0. **A B1 a számokat pontosan olvassa**: a számszerű közelség (számlaszám, összeg,
    mérés, küszöb) nem nehezíti. A 20%-os cél két körrel nem elérhető ilyen konstrukcióval; a nehéz minta más jellegű
    összetéveszthetőséget kér (reggeli kérdés Daninak: pl. az összeg szavakkal vagy más formátumban, részfizetés,
    mértékegység-váltás, áfás/nettó összeg).
  - **Éjszakai sor (K07EJ, `k07ejjel.sh`, Dani kérésére, indult 21:40):**
    - **B. F1M:** a D_meta (6000 item, 4500 hu / 1500 en, 646 noul; natív keretű item nincs) a négyállapotú prompttal,
      kanonikus + b1, 24 000 forward, a `cache/k07/jellemzok/k05_D_meta__*` alá. A span-ellenőrzés előre lefutott:
      12 000 prompt, 0 hiba, medián 387, max 2459 token.
    - **C. F2:** friss CAL + TESZT új sablonokkal (`szint07 friss-*`: sablon-id `<család>:k07:<nyelv>:<n>`, item-id
      `…:k07-<n>`, a 06-os id-kkel nincs ütközés; nyelvenként 15 + 30 sablon, családonként 1952 terv a 06 kvótájával
      és tartalékával; a hiba-okkatalógusok a Muse-tól). A bank- és a szabálysablon helyben ellenőrizve (D21 tart).
    - **D. F3:** a friss CAL és TESZT kiolvasása pecsét alatt (`pecset07`, `cache/k07/pecset/jellemzok` és
      `jellemzok2`), mindkét kerettel, 2 × 18 000 forward; pecsétmanifest K07F3. Csak ha az F2 teljes.
    - A sor vége kb. 09:00–10:00. Jelzők: DONE/FAILED-K07F1M, -K07F2, -K07F3; lépések: `logs/k07ejjel/lepesek.log`.
    - **Nem része az éjszakának:** a címkeaudit (Dani), a Gemma-triage, a nehéz minta 3. köre, a B1-4R tanítása.
- **2026-11-01 (reggel) — az éjszakai sor eredménye** (`logs/k07ejjel/lepesek.log`; a gép reggel: 50 GB elérhető,
  63 GB szabad swap, egy konténer, őr nem avatkozott be):
  - **F1M kész 00:34** (2 h 53; 24 000 forward hiba nélkül) → `cache/k07/jellemzok/k05_D_meta__{kanonikus,b1}`. A
    span-ellenőrzés eredménye `kor07/eredmenyek/F1M/spanok/` (12 000 prompt, 0 hiba).
  - **F2 kész 03:13** (Muse 10 perc alatt állt fel; bank 00:45–01:44, hibaelhárítás 01:44–02:44 — ebből a Muse-os
    okkatalógus 28 perc —, szabálycsalád 02:44–03:14). **Mindhárom családon 1500 item** (CAL 500 + TESZT 1000;
    hu/en 750/750; MATCH 900 / NO_MATCH 300 / MISSING_DATA 150 / OUT_OF_SCOPE 150), **hiányos cella nincs.** A
    1952 tervből túlélő: 1917 / 1944 / 1946. Elveszett: bank 35 (31 JSON-hibás Muse-hívás, 1 opció-partner a
    szövegben, 2 hiányzó partner a szövegben, 1 dátum), hibaelhárítás 8 (az ok megnevezve a szövegben), szabály 6
    (rossz nyelv). Újrageneráltatás: bank 250 (201 JSON-hiba, 18 dátum, 14 PII/URL), hiba 40 (24 ok megnevezve,
    13 rossz nyelv), szabály 66 (58 rossz nyelv, 8 PII/URL). A bank JSON-hibaaránya ugyanaz a mintázat, mint a
    06-ban (ott 249 JSON-hibás újrageneráltatás a 309-ből, 38 elveszett a 44-ből): a Muse a banki soroknál téveszt
    formátumot, az ismétlés hozza be. 8 véletlen bank-itemre (4 állapot × 2 nyelv) ránéztem: a szöveg, az opciók és a
    gold összhangban vannak (MATCH: partner + összeg + számlaszám egyezik; NO_MATCH: az összeg más partnernél, a
    partner más összeggel; MISSING: partner nélküli tétel két azonos összegű opcióval; OOS: NAV-befizetés, saját
    megtakarítási átvezetés). Ez nem audit, az a D14-es 300 itemes címkeaudit (Dani).
  - **Helyi szerkezeti ellenőrzés (a lehúzott `kor07/adat/f2/items/*.jsonl`-en):** 1500 egyedi id családonként, mind
    a `<család>:<CAL|TESZT>:<hu|en>:<állapot>:k07-nnnn` mintára illeszkedik; **sabloncsoportok: CAL 30 / TESZT 60,
    közös 0, a 06-os 120–124 sabloncsoporttal közös 0 (D21 tart)**; opciószám 3–6 egyenletesen; `ketertelmu` 0;
    szöveghossz medián 185 / 469 / 333 karakter (bank / hiba / szabály). A `sync.sh back07` a `kor07/adat`-ot nem
    hozza, azt kézi rsync-kel húztam le (`kor07/adat/f2/{items,raw,sablon,terv}`).
  - **F3 kész 07:35** (a négyállapotú keret 03:14–05:27, a 06-os kétkimenetű keret 05:27–07:35; 2 × 18 000 forward
    hiba nélkül, az őr egyszer sem lépett). **Pecsétmanifest `kor07/rogzites/pecset/K07F3.json`** (helyben is):
    `teljes: true`, `v1a_rogzitve: false`; 12 feladat mind kész (családonként CAL kanonikus 500 / b1 1500 sor, TESZT
    kanonikus 1000 / b1 3000 sor); 78 fájl, 1,59 GB, 39 a `jellemzok/`, 39 a `jellemzok2/` alatt; a kódhash-lista
    14 fájl, benne a három friss itemfájl. A pecsét alatti kimenetekről ennél több a rögzítés előtt nem kerül
    naplóba. **Az éjszakai sor vége 07:35:22 (K07EJ: F1M kész · F2 kész · F3 kész).** A gép a sor után: 118 GB
    elérhető, 63 GB szabad swap, nincs konténer. A sor naplói helyben: `jegyzokonyv/spark-logs/k07ejjel/`.
  - **Következő lépések (GPU nélkül is):** a D14-es címkeaudit a friss adaton (Dani, 300 item), a Gemma-triage (D15:
    jelöl, nem töröl), a nehéz minta 3. körének konstrukciója (Dani döntése), a B1-4LR jellemzőlistája (D12). GPU-s:
    F3R (a fejek tanítása és mentése `cache/k07/fejek` alá) — előtte a `b1rel07` megírása.
- **2026-11-01 reggel — az audit felülete, a Gemma-triage és az F3R kódja (Dani: „kérem az audit felületet, és utána
  haladj tovább míg dolgozom rajta”).**
  - **Címkeaudit (D14 a friss adaton):** `kor07/eszkozok/audit07.py` — a 06 `szint06.cmd_audit` és `audit06` burkolója
    07-es útvonalakon (a 06 kódja változatlan). Minta: 300 item, családonként 100, állapot × nyelv szerint rétegezve
    (cellánként 12–13) a friss CAL + TESZT-ből, 07-es seeddel (`szint07:2026-11-01`); a mintában TESZT 191 / CAL 109,
    hu 152 / en 148. A vak lap `kor07/adat/f2/audit/atnezo.html` (sig `300-fbc0d2defa`, kulcsok a001…), a kulcsleképezés
    `atnezo_kulcsok.json`, a kulcs `kulcs.jsonl`. **Szivárgás-ellenőrzés (`audit07 ellenoriz`) rendben:** item-id,
    sablon-id, szelet- és családnév, „(z)” nincs a lapon. A kapu a 06-é: ≤ 2% felső korlát, 300 itemen legfeljebb 1
    hiba (`audit07 osszesit --dontesek …`).
  - **Gemma-triage (K07F2G, `k07f2_gemma.sh`, indult 07:48):** a Gemma 4 26B-A4B-it második ítélete a friss 4500 itemen,
    a 03 `kiolvaso03` ids-módja, négy sorrend, gold és item-id nélkül; kimenet `kor07/eredmenyek/F2/gemma/gemma_f2.jsonl`
    (nem a pecsét alá tartozik). Az összesítés (gemma07) helyben, a kulcsonkénti ítélet Dani vak exportja után nyílik
    meg (mint a 06-ban). A családtávolság-audit a 07-ben nem fut (a családok a 06-éi, csak a sablonok újak).
  - **D12 rögzítve** (2.3): a B1-4LR tíz jellemzője.
  - **F3R kódja: `kor07/eszkozok/b1rel07.py`** (`tanit`): B1-4R0 a D_meta-n (négyállapotú, F1M; 15 kis jellemző, a
    választott válasz sorának rejtett állapotai, Y/Z-nél a saját soruk), B1-4R a T500-on (öt sablonos fold, D23), B1-R a
    06 receptjével a fold-modellek elmentésével, B1-LR és B1-4LR az együtthatók elmentésével, a két temperature; minden
    a `cache/k07/fejek` alá, `fejek.json` sha256-lista. **Önellenőrzés beépítve:** a mentett B1-R fold-modellek átlaga a
    06 TESZT-en az F0 reprodukció pontszámaival összevetve (0-nak kell lennie), és a 05 `to_example` X-feltevése
    (utolsó span) helyett saját négyállapotú példaépítés (opciók, X, Y, Z), spanszám-ellenőrzéssel. A 06 TESZT-en mért
    B1-4R-AURC csak tervezési próba. Futás a Gemma után (memória), `--limit` füstteszttel előbb.
  - **F3R füstteszt (08:00–08:01, `--limit 300 --szalak 6`, a Gemma mellett, 37 GB elérhető):** minden ág lefutott,
    101 fájl; a temperature egyezik az F1-ével (1,5841); a négyállapotú spanok sorrendje (opciók, X, Y, Z) és a span-
    és jellemzőszám minden itemen stimmelt (különben a `to_example4` megáll). A limitált számok nem érvényesek.
    **A teljes F3R 08:02-kor indult** (`logs/k07f3r.log`, `--szalak 8`; a Gemma kiolvasása közben, az elérhető memória
    37 GB, a tanítás ≤ 8 GB-ot kér).
  - **F3R kész 08:04 (2,5 perc; `kor07/eredmenyek/F3R/f3r.{json,md}`; 101 fájl, 310 MB a `cache/k07/fejek` alatt,
    sha256-lista `fejek.json`):**
    - **B1-R repro: max|Δ| = 0 mindhárom családon, mindhárom seeden; a B1-LR is 0.** A mentett fold-modellek átlaga
      pontosan a 06 recept (F0) pontszámait adja a 06 TESZT-en: a fejek elmentése nem változtatott a recepten.
    - **B1-4R0 (D_meta, négyállapotú):** 5796 item (fit 4618, val 1178; a kétértelműek nélkül); a B1-4 helyes 0,719;
      döntések SELECT 5406 / X 362 / Y 23 / Z 5; lr 1e-4; val AUROC seedenként 0,873 / 0,868 / 0,867 (a B1-4 saját
      pontszáma 0,794).
    - **Tervezési próba a 06 TESZT-en (ismert adat, nem állítás), AURC:** bank B1-4R 0,048 (3 seed: 0,0477–0,0483) vs
      B1-4S 0,085, B1-4LR 0,061; hibaelhárítás 0,022 vs 0,048, B1-4LR 0,048; szabálycsalád 0,030 vs 0,066, B1-4LR 0,030.
      A fej a négyállapotú prompton is nagyjából felezi az AURC-t; a 06 B1-R-hez (0,048 / 0,044 / 0,050) képest a
      hibaelhárításon és a szabálycsaládon kisebb. A seedek közti eltérés 0,001 alatt. Ez az F4 erőbecslés bemenete.
    - Nyitott: a `cache/k07/fejek_fust` és a `kor07/eredmenyek/F3R_fust` (füstteszt) törlendő; a `py` root-ként ír, a
      törlés Dani sudo-jával.
  - **A pontozó út (`b1rel07 pontoz`, F5-höz és 07B-hez) önellenőrzése a 06 TESZT-en (08:06, `cache/k07/f3r_proba`):**
    mindkét kerettel 1000 item, 8 pontszámsor (B1-4S, B1-4R0 és B1-4R seedenként, B1-4LR; B1-S, B1-R0 és B1-R
    seedenként, B1-LR). A pontozó B1-4R-AURC-ja minden jegyre azonos a tanítás közben mérttel, a B1-R-logitok az F0
    reprodukcióval 0 eltérésűek. A 07 CAL / TESZT-re a `pontoz` csak a `pecset07.kapu` (v1 rögzítése) után fut. Ezek a
    fájlok a tervezési próba pontszámai: az F4 erőbecslés bemenete.
  - **F4 erőbecslés (`kor07/eszkozok/ero07.py`, `kor07/eredmenyek/F4/ero.{json,md}`; sabloncsoportos bootstrap 4000
    replika, futásátlag; a 06 TESZT ismert adata, nem állítás):**
    - **K1 (B1-4R − B1-4S):** Δ −0,037 / −0,026 / −0,036 (−43% / −55% / −54%), SE 0,003–0,004, a Δ 95%-os
      intervalluma mindhárom családon 0 alatt; az átlag aránya **0,503 [0,458; 0,556]**, SE 0,025, MDE80 relatív
      csökkenésként 7,0%. **A 06 8.3 szabály a D4-gyel 1000-es TESZT-en adekvát:** a D4 ereje pontosan 10%-os valódi
      csökkenésnél 0,98, a „pontbecslés ≥ 10%” a határon 0,50 (definíció szerint), 15%-nál 0,98 együtt. **Javaslat a
      D5-re: a K1 szabály marad a 06 8.3 + D4** (nem kell lazítani vagy nagyobb TESZT); Dani dönt.
    - **Ellenőrzés:** a 06-os pár (B1-R − B1-S) ugyanezzel a bootstrappal 0,205 [0,187; 0,224] — az F5 eredménylap
      száma (0,205 [0,187; 0,224]) visszajön.
    - **A finomhangolás nélküli B1-4R0 rosszabb a B1-4S-nél** (arány 1,47; bank és hiba), mint a 06-ban a B1-R0: a T500
      finomhangolása lényeges. **B1-4LR** a bankon és a szabálycsaládon közel a B1-4R-hez (0,061 / 0,048 / 0,030 vs
      0,048 / 0,022 / 0,030), a hibaelhárításon nem javít a B1-4S-en.
    - **Keresztpár (leíró, D13):** a B1-4S önmagában nem éri el a 06 B1-R-t (arány 1,40 [1,30; 1,51]: bank 0,085 vs
      0,048, szabály 0,066 vs 0,050, hiba 0,048 vs 0,044). Az F1 „behozza a nagy részét” megfogalmazása a B1-S-hez
      képest igaz, a B1-R-hez képest nem. A B1-4R a B1-R-nél a hibaelhárításon és a szabálycsaládon kisebb AURC-jű
      (arány 0,70 [0,64; 0,78]), a bankon azonos. A gyakorlati következtetés a K2-re épül (D13).
    - **Nincs benne:** a K2 (hasznos lefedettség, lezárási hibaarány, τ a CAL-on) ereje; ahhoz a 06 CAL pontozása és az
      F5 elemzőjének (elemzes07) próbája kell — következő lépés.
  - **Gemma-triage kész (K07F2G 08:11; 18 000 kiolvasás, 0 hiba, 14 perc; `gemma07 osszesit` →
    `kor07/eredmenyek/F2/gemma/osszesito.{json,md}`):** 4500 / 4500 item, egyezés a konstrukcióval **89,6%**, a négy
    sorrend egyetértése 95,7%. A mintázat a 06-é: MATCH 99,9% / 97,7% / 100% (bank / hiba / szabály), OUT_OF_SCOPE
    100% mindhárom családon, NO_MATCH 71% / 92% / 77%, MISSING_DATA 4% / 81% / 38% (a Gemma keretében nincs Y: a
    bankon a két azonos összegű opció egyikét választja, mint a 06-ban). Nyelv: hu 82–92%, en 87–98%.
    - **Felülvizsgálati lista (a 06 szabálya: MATCH-eltérés vagy NO_MATCH 4/4; `felulvizsgalat.md`, belső, nem a vak
      audit része):** MATCH-eltérés 22 (hiba hu 18, hiba en 3, bank en 1; 15-nél a Gemma X-et mond, 7-nél más okot;
      sabloncsoportonként legfeljebb 3), NO_MATCH 4/4 ugyanazt az opciót 78 (bank hu 37 / en 13, szabály hu 20, hiba 8).
      A hibaelhárítás magyar MATCH-eltérései a szabálytáblás konstrukcióban (06 D16) a mérésküszöbök olvasását kérik a
      Gemmától; ránézésre nem címkehiba, de ez Dani auditjának és a listának a dolga. Itemet nem töröltünk (D15).
    - **A kulcsonkénti ítélet (`kor07/adat/f2/audit/gemma_itelet.json`: 300 kulcs, a Gemma 51-nél tér el) Dani vak
      exportja előtt nem nyílik meg.**
  - **A 06 CAL pontozása (`pontoz k06:<család>:CAL`, 08:12–08:13) kész, `cache/k07/f3r_proba`:** az F5 elemzőjének
    (elemzes07: K1 + K2 a τ-val) próbájához. A GPU a Gemma óta üres; GPU-munka a nehéz minta 3. köréig (Dani döntése)
    nincs a sorban.
  - **Az F5 elemzője (`kor07/eszkozok/elemzes07.py`) és próbája a 06 CAL / TESZT-en (`kor07/eredmenyek/F4/proba/`,
    2000 replika; ismert adat, nem állítás):** K1 (ΔAURC, 8.3 + D4, Holm), E-AURC leíró, D20 bontás (SELECT / nem-
    SELECT), tévesztési mátrixok, K2 (τ a CAL-on a lezárható javaslatokon, CP-alsó ≥ 0,95, ≥ 200 lezárt; hasznos
    lefedettség, lezárási hibaarány, helyes adatbekérés / továbbítás, a nem lezárt ügyek bontása; a τ replikánként
    újra), a D10 következtetései. **Konvenció:** munkapont nélkül a kar semmit nem zár le (hasznos lefedettség 0, a
    hibaarány nincs értelmezve), a munkapont nélküli futások és replikák aránya külön sor.
    - **Ellenőrzés a 06 F5-tel:** a B1-R munkapontja a 06 adatán 66,5% / 67,9% / 71,7% lezárt, lezárási hiba 1,7% /
      2,5% / 3,3% — a 06 eredménylap (lef 0,665 / 0,679 / 0,717, prec 0,983 / 0,975 / 0,967) visszajön; a K1 arányok az
      `ero07`-tel egyeznek (0,503; 0,205).
    - **K2 a próbán:** a B1-4S-nek a bankon nincs munkapontja (a replikák 83%-ában sem), a hibaelhárításon 45,9%, a
      szabálycsaládon 46,6% hasznos lefedettség; átlag 30,8% vs B1-R 67,0% → a D10 szerint **„nem hozza be”** (−36 pont
      [−53; −18]). **B1-4R 68,8% [62,8; 70,9] vs B1-R 67,0% [63,3; 70,1]: +1,8 pont [−2,8; 3,2], p = 0,57**, lezárási
      hiba 2,7% [1,6; 3,9] (hibafeltétel teljesül). A B1-4R mellett a helyes adatbekérés / továbbítás: bank 1% / 0%,
      hiba 68% / 52%, szabály 46% / 21% (a 06-os prompton 0). A B1-4LR a bankon munkapont nélkül.
    - **Értelmezés (próba):** a prompt önmagában nem elég a gyakorlati végponthoz, a fej kell hozzá; a B1-4R a
      lezárásban a B1-R-rel egyenértékű, többlete a hiányzó adat és a hatókör jelzése (a döntési kapcsolás 3. ága:
      termékfunkció). Ezt a friss TESZT-nek kell megerősítenie.
  - **A v1 rögzítésének eszköze és vázlata:** `kor07/eszkozok/befagyaszt07.py` (`manifest` / `rogzit --jovahagyas` /
    `ellenoriz`; a `befagyaszt06` függvényei 07-es állandókkal: 32 kódfájl, 12 adat- és eredményfájl, a `cache/k07/fejek`
    101 fájlja, a 06 B1-R0 és a 05 H statisztikája, a K07F3 pecsétmanifest és a két pillanatkép), és
    **`kor07/rogzites/v1/v1-vazlat.md`** (K1 / K2 szabályok a D5 javaslattal, adat, karok és mentett fejek, végpontok,
    statisztika, futtatás, a rögzítés előtti döntések: D1 Z-szöveg, D5, D6, az audit kapuja, „mehet”). A manifestből
    most csak az audit összesítője hiányzik (`kor07/eredmenyek/F2/audit/osszesito.json`, Dani exportja után). A
    `sync.sh up07` a helyi eredményeket (audit, Gemma, F4, v1-vázlat) viszi fel a manifesthez; a `back07` a
    `kor07/rogzites`-t is hozza.
  - **Ami Danira vár:** az audit exportja (→ `audit07 osszesit`, a Gemma kulcsonkénti ítélete utána nyitható), a D1 / D5 /
    D6 megerősítése, a nehéz minta 3. körének konstrukciója (GPU-munka), a 07B B0 (a hozzájáruló tenantok banki kézi
    kötéseinek felmérése, csak olvasás; D7).
- **2026-11-01 délelőtt — Dani: a címkeaudit kész („hibátlan lett, 100% helyes”), D1, D5, D6 megerősítve, a 07B B0
  felmérése mehet.**
  - **A címkeaudit kapuja átment** (Dani exportja `kor07/adat/f2/audit/dontesek.json`, sig `300-fbc0d2defa`;
    `audit07 osszesit` → `kor07/eredmenyek/F2/audit/osszesito.{json,md}`): **300 / 300 egyezik a konstrukcióval, 0
    címkehiba, az egyoldali 95%-os felső korlát 0,99% ≤ 2%.** Cellánként 24–26 item; Dani 105 itemhez írt indoklást
    (a MISSING_DATA-knál a hiányzó mérés / összeg / partner, a NO_MATCH-oknál a küszöb alatti érték vagy a listán nem
    szereplő számlaszám) — a konstrukció állapotlogikáját erősítik.
  - **A Gemma kulcsonkénti ítélete (az export után megnyitva):** 51 eltérés a konstrukciótól = 51 eltérés Danitól (bank
    MISSING_DATA 24, NO_MATCH 5; hibaelhárítás MISSING_DATA 3, NO_MATCH 3; szabálycsalád MISSING_DATA 14, NO_MATCH 2);
    **MATCH-eltérés az auditkulcsokon nincs.** A felülvizsgálati szabály (NO_MATCH 4/4 egy opcióra) 5 kulcsot ad (a053,
    a095, a126, a182, a300): mind szándékos közeli zavaró (küszöb alatti mérés egyező tünettel; azonos összeg más
    számlaszámmal), Dani X-e indokolt. A Gemma a hiányzó adatot a kerete miatt nem tudja jelezni (nincs Y), ezért a
    MISSING_DATA-n az egyik azonos összegű opciót választja — ugyanaz, mint a 06-ban. Itemet nem töröltünk (D15).
  - A döntéstábla D1, D5, D6 sorai frissítve. A nehéz minta 3. körének konstrukciója továbbra is nyitott (javaslat:
    összeg szavakkal vagy más formátumban, részfizetés, mértékegység-váltás, áfás / nettó összeg).
  - **07B B0 indul:** a hozzájáruló tenantok [kihagyva: ügyféladat] helyi tükrein, csak olvasó SQL-lel, aggregátum: banki tételek, `match_status`, a kötések `auto` / `manual`
    eredete, több számlát rendező utalás, részfizetés, időtartomány, a tükör frissessége. Tételszöveg nem kerül a
    kontextusba.
  - **B0 kész (`kor07/eredmenyek/B0/b0.md`):** [kihagyva: ügyféladat]
