# A nehéz minta 3. köre — javaslat (2026-11-01; a döntés Danié)

**Állapot:** lefutott (K07F1B3, 11-01 16:37–17:42, Dani jóváhagyásával); az eredmény lent. A végső minta döntései jóváhagyva (19:3x), a végső minta a K07K3 (lent).

## Miért kell más konstrukció

Az 1–2. kör a számszerű közelségre épült (egy jegy, két felcserélt jegy, 0,5–3%, a küszöb 1–3%-os környezete). A B1 a
számokat pontosan olvassa, ezért a rossz opcióválasztás a bankon 0, a másik két családon 5–13% maradt (cél: 20%).

A 3. körben **a döntő részlet a szövegben van, de egy következtetési lépés kell hozzá**: váltás, arány, áfa vagy árfolyam.
A csali az a jelölt, amelyet a felszíni egyezés adna: a pontos összeg vagy a nyers számösszevetés. A gold a tervből
gépileg következik, ítélet nem kell hozzá.

## Az öt változat

| család | változat | a szövegben | gold | csali | terv |
|---|---|---|---|---|---|
| bank | **részfizetés** | a partner és az arány (30 / 40 / 50%), számlaszám nincs | az a számla, amelynek ennyi %-a a tétel | ugyanaz a partner és esedékesség, a bruttója pontosan a tétel összege | 60 |
| bank | **betűvel** | az összeg csak betűvel, a partnerrel | a betűvel írt összegű számla | ugyanaz a partner, két szomszédos jegy felcserélve vagy 0,5–3% | 60 |
| hiba | **mértékegység-váltás** | a két jelölt ok mérése más egységben, mint a szabályban (V ↔ mV, bar ↔ kPa, mm ↔ µm, ms ↔ s, Hz ↔ rpm …) | a valódi ok: átváltva teljesül, nyers számként nem | a pár: átváltva nem teljesül, nyers számként igen | 104 |
| szabály | **nettó / bruttó** | a bruttó összeg az áfakulccsal (hu 27%, en 20%); minden szabálypont küszöbe „nettó” | alsó sáv: a nettó a küszöb alatt | felső sáv: a bruttó a küszöb fölött | 60 |
| szabály | **deviza** | az összeg devizában az árfolyammal (hu: EUR, Ft/EUR; en: GBP, EUR/GBP) | felső sáv: az átszámított érték a küszöb fölött | alsó sáv: a devizás szám a küszöb alatt | 60 |

A két szabálycsaládi változat goldja ellentétes sávban van, így a sáv önmagában nem árulja el a választ.

Egy példa a hibaelhárításból: a szabály „szivárgási áram 5 mA fölött”, a szövegben „0,018 A”. Ez 18 mA, tehát teljesül,
de nyers számként nem. A pár mérése „10000 ms” a „30 s fölött” szabály mellett: valójában 10 s, nem teljesül, nyers
számként igen. A többi változat mintapromptja: `kor07/adat/nehez3/minta_promptok.md`.

## Amit tudni érdemes

- **A hibaelhárításon 104 terv** készül a 120 helyett: 16 sablon-esetben nincs olyan egységpár, ahol a nyers összevetés
  a csalit adná (százalék, dB, hőmérséklet). Ez a nyelvek arányát is elviszi: 48 hu, 56 en.
- **Hőmérséklet nincs a váltásban:** a sablonok hőmérsékleti méréseinek jó része különbség (túlhevülés, emelkedés,
  eltérés), ahol a °C ↔ K eltolás értelmetlen.
- **Néhány váltás szokatlan** a szervizlevélben (V → kV, mm → m, m → km). Ha csak a természetes párokat akarod
  (mV ↔ V, bar ↔ kPa / mbar, ms ↔ s, mm ↔ µm, A ↔ mA, Hz ↔ rpm, L/min ↔ L/h), a terv kisebb lesz.
- **A részfizetés és a deviza a valódi <tenant>-forgalomban is megvan** (B0: 26 részfizetéses kötés, devizás kártyás
  terhelések). A betűvel írt összeg ritka, a 2. körrel közvetlenül összevethető.
- **A tényellenőrző** minden változatnál visszakeresi a döntő részletet, és kiszűri az árulkodó szöveget: például ha a
  generátor kiírja a nettót, az átszámított forintot, vagy zárójelben visszaváltja a mérést. Önteszt: 30 / 30 eset a
  várt módon.

## Költség és menet

1. **K07F1B3** (`kor07/eszkozok/k07f1b3_nehez.sh`): önteszt, terv, Muse-generálás, kiolvasás mindkét kerettel. A K07F1B
   alapján kb. 1–1,5 óra GPU; egyetlen nagy GPU-folyamat, nem indul, ha más fázis vagy konténer fut.
2. **Elemzés helyben:** a `b14_07 --nehez --nehez-kor 3` változatonként adja a rossz opcióválasztást és a nem-SELECT
   arányt (D11).
3. **Ha egy változat eléri a 20%-ot,** a konstrukció rögzül, és a végső diagnosztikai minta egyszer készül (D6, D11).

## Döntések (a futás előtt)

1. **Melyik változatok fussanak?** Mind az öt (Dani 16:36: „Mehet a nehéz minta 3. köre”, a javaslat szerint).
2. **A hibaelhárítás egységpárjai:** mind; az elemzés utólag bontja a természetes párok szerint (lent).
3. **A végső minta sablonjai:** nyitott, lent a 4. döntés.

## Eredmény (11-01 19:30; `kor07/eredmenyek/F1/b14_nehez3.md`, `b14_nehez3_bontas.md`)

Fejlesztési próba a 06 ismert T500-sablonjain, nem állítás. Minden item MATCH. A rossz opció a SELECT a nem-gold
opción, az itemek arányában. A „4” a négyállapotú prompt (B1-4), a „2” a 06-os kétkimenetű (B1).

| változat | item | rossz opció, 4 | rossz opció, 2 | ebből a csali | SELECT-AUROC, 4 / 2 | nem-SELECT, 4 |
|---|---|---|---|---|---|---|
| bank, részfizetés | 52 | **42 (81%)** | 42 (81%) | mind | 0,23 / 0,28 | 0 |
| bank, betűvel | 60 | 1 (2%) | 2 (3%) | mind | 0,85 / 0,92 | 1 |
| hiba, mértékegység-váltás | 96 | **46 (48%)** | 46 (48%) | mind | 0,47 / 0,49 | 3 |
| szabály, nettó / bruttó | 60 | **45 (75%)** | 43 (72%) | mind | 0,22 / 0,22 | 0 |
| szabály, deviza | 60 | **47 (78%)** | 48 (80%) | mind | 0,14 / 0,18 | 0 |

- **Négy változat messze a 20%-os cél fölött van.** Az 1–2. kör 0–13%-a után ez minőségi váltás: a B1 a számot
  pontosan olvassa, de a következtetési lépést (arány, váltás, áfa, árfolyam) nem végzi el, hanem a felszíni egyezést
  követi. **A rossz választás minden esetben a csali**, mindkét kereten.
- **A B1 bizonyossága fordított** a részfizetésen és a két szabályváltozaton (SELECT-AUROC 0,14–0,28): amikor a csalit
  választja, magabiztosabb, mint amikor helyesen dönt. Egy q-küszöb ezeket éppen magas bizonyossággal zárná le. A
  mértékegység-váltáson a q nem hordoz jelet (0,47), a választás a pár két tagja közt nagyjából érmedobás.
- **A betűvel írt összeg könnyű maradt** (2%): a B1 a szavakkal írt összeget is pontosan olvassa.
- **A természetes egységpárok nem könnyebbek:** a rossz opció 2 / 2 természetes váltásnál 6 / 11 (55%), 1 / 2-nél
  25 / 50 (50%), 0 / 2-nél 15 / 35 (43%). A szokatlan váltás tehát nem fújja fel a hibaarányt.
- **Nyelvenként:** részfizetés hu 27 / 29, en 15 / 23; nettó / bruttó hu 19 / 30, en 26 / 30; deviza hu 17 / 30,
  en 30 / 30; váltás hu 24 / 44, en 22 / 52.
- **Kiesés a tényellenőrzőn:** bank 8 (6 szövegből hiányzott az arány, 2 JSON-hiba), hiba 8 (7 zárójelben
  visszaváltotta a mérést az eredeti egységre, 1 megnevezte az okot), szabály 0.
- **A goldok kézi ellenőrzése:** 13 olyan item, ahol a B1 a csalit választotta, minden változatból és mindkét nyelven.
  Mindegyikben a gold a szövegből a kimondott lépéssel következik (például 1 906 010 Ft 30%-a 571 803 Ft;
  519 EUR × 410 Ft/EUR = 212 790 Ft > 150 000 Ft; 0,018 A = 18 mA > 5 mA), a csali csak a felszíni számot adja.
- **Egy apró szóhasználati pont:** a banki kérdés „Melyik nyitott számlát egyenlíti ki ez a tétel?”, egy részlet pedig
  szó szerint nem egyenlít ki. A szöveg azonban kimondja az arányt, és a csali (amelynek bruttója a tétel összege) azzal
  ellentmond; az X-et a B1-4 egyszer sem választotta.
- **A fejeket szándékosan nem futtattam a próbamintán**, hogy a konstrukció rögzítése ne függjön attól, hogyan
  teljesítenek rajta (K3 a végső mintán).

## Döntések a végső mintához (D6, D11)

**Dani (2026-11-01 19:3x): „igen, mehet így tovább”** — mind az öt pont a javaslat szerint.

1. **A rögzített konstrukció:** javaslat a négy változat (részfizetés, mértékegység-váltás, nettó / bruttó, deviza), a
   betűvel írt összeg nélkül. A bankcsalád így egyetlen változatból áll. A betűvel írt összeg csak könnyű, helyes
   SELECT-eket adna, és azokon a változatok közti különbség felfújná a rossz opció felismerésének AUROC-ját.
2. **A méret:** a D6 200 itemje családonként marad. A mért arányokkal a 40 rossz opció bőven megvan; most a helyes
   SELECT-ek a szűkös osztály (80%-os hibánál 200 itemből kb. 40), ezért nem érdemes kisebbre venni.
3. **Az egységpárok:** mind. A természetes párok nem könnyebbek, és csak velük kevés sablonból lenne terv.
4. **A sablonok:** a 07 friss TESZT-sablonjai (a fejek ezeken nem tanultak, a K3 külön közölt). Ehhez a `szint07k3`
   sablonforrása átállítandó, külön kimeneti könyvtárral.
5. **A K3 elemzője előre:** javaslat, hogy a K3 elemzője a végső minta kiolvasása előtt rögzüljön (a v1 manifest
   kiegészítéseként), a kiolvasás pedig pecsét alatt fusson, mint az F3.

## A végső minta (K07K3) menete

1. **A K3 elemzője a generálás előtt rögzül** (`rogzit07k3 manifest` + `rogzit`, `kor07/rogzites/k3/`): `k3_07.py`
   (mérők, karok, párok, bootstrap, olvasat; a docstringben), `b1rel07k3.py` (a `b1rel07 pontoz` a `diag:` szeleten),
   `kiolvas07diag.py`, `szint07diag.py`, `pecset07k3.py`, `k07k3_diag.sh`, a runbook és ennek a lapnak a pillanatképe,
   a v1 manifestjének hash-e. Az elemző önteszttel (mesterséges adat) és próbával (a 3. kör nyitott mintáján: csak
   darabszám, mérőérték nem) ellenőrizve.
2. **K07K3:** `szint07diag` a 07 TESZT-sablonjain. Családonként 200 terv, nyelvenként 100; a kiosztás a sablonok
   id-sorrendjében körbe. Helyben, CPU-n: bank 200 részfizetés 60 sablonon; hiba 200 mértékegység-váltás 39 sablonon
   (21 TESZT-sablonon nincs alkalmas egységpár, ezért sablononként kb. 5 terv); szabály 4 × 50 (nyelv × változat) 60
   sablonon. Muse-generálás, tényellenőrzés, a kiolvasás mindkét kerettel a `cache/k07/pecset_k3` alá (root, 700), a
   pecsét lezárása (`kor07/rogzites/pecset/K07K3.json`).
3. **A pecsét nyitása csak Dani jóváhagyásával** (`rogzit07k3 nyit --jovahagyas …`, a manifestek és a pecsét
   ellenőrzése után), utána `b1rel07k3 pontoz --szelet diag:<család> --out cache/k07/k3` és
   `k3_07 elemez --be cache/k07/k3 --out kor07/eredmenyek/K3`.
