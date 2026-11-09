# Runbook 08: ellenőrzött számítási lánc, és a megbízhatósági fej a maradék értelmezési hibán

**Ha a kinyerést, a számítást és a szabályellenőrzést ellenőrzött kód végzi, a maradó értelmezési hibákból mennyit
ismer fel a megbízhatósági fej, és segít-e ebben az értelmezési hibákon végzett célzott tanítás?**

- **Verzió:** v0.2, 2026-11-02.
  - **v0.1:** Dani iránya a 07 után (07-runbook D16).
  - **v0.2:** Dani hét pontosítása (11-02). Megtartva: friss sablonok, valódi kinyerés, a befagyasztott L-R07
    összevetés, kalibráció az új bemeneten.
  - **Változott:**
    - a lánc három külön állítást tesz (2.1);
    - a kinyerés szerepet és forrásrészletet ad, és a döntést befolyásoló hiba definiált (2.2);
    - két eredményszint van: teljes rendszer és értelmezési diagnózis (5.);
    - az L-RN az elsődleges kar (4.);
    - az eldönthető jel a bemenetben van, a párok együtt mozognak (3.3);
    - a siker három szintje, „nem eldönthető” kimenettel (D9);
    - a rögzítés két lépésben (8., D12);
    - a 08B lépcsős összevetés (7.).
- **Státusz:** Dani 11-02-án jóváhagyta a nyitott javaslatokat (D2, D8, D9, D10), és elindította a G0-t (kód, CPU).
- **Előzmény:** a [07-runbook](07-runbook.md) négy eredménye.
  - **F5 (K1):** az állapotjelző B1 mellett a fej friss teszten javít, az AURC-arány 0,507
    (`kor07/eredmenyek/F5/eredmenylap.md`). A természetes összetételben ez főleg állapothibák felismerése.
  - **K3:** a következtetési lépés hiányából eredő tévedést egyik kar sem ismeri fel. A bankon a fej fordítva
    rangsorol (0,21), mert a „pontos összeg = jó” szabályt tanulta meg. A változatlan τ ezeknek a tételeknek a
    27–100%-át hibásan zárja le (`kor07/eredmenyek/K3/eredmenylap.md` 4–4a).
  - **Páros próba (feltáró):** ha a hiányzó lépés eredménye a szövegben van, a helyes arány bank 29 → 100%, hiba
    52 → 94%, szabály 24 → 67%. A szabálycsaládon a maradék a küszöb-összevetés: a kiszámított nettó mellett is a
    bruttóhoz igazodik a választás, főleg angolul (K3 eredménylap 4b).
  - **07B (valódi adat):**
    - A MATCH-címkén 139 / 139 a helyes számla; a modell valódi adaton sosem mond Y-t és Z-t.
    - A termék mellett, kiegészítőként +3 helyes kötést ad, új hiba nélkül (07 D15).
    - A nem eldönthető (főleg iker) kötést a pontszám elválasztja: AUROC kb. 0,9, utólagos. Ezt a fej nem javítja az
      alany saját bizonyosságához képest (`kor07/eredmenyek/B7/eredmenylap.md`).
- **Amiből a 08 kiindul:** a 07 hibái két fajtára bomlanak.
  - **Ellenőrizhető művelet:** arány, áfa, árfolyam, egységváltás, küszöb-összevetés. Ezt kód elvégezheti, ellenőrizve.
  - **Értelmezés:** melyik partner, melyik szabálypont, melyik ok, eldönthető-e egyáltalán. Ez marad a modellnek.

  A 07 K3 és 4b eredménye indokolja, hogy a számítást és a szabályellenőrzést kód végezze. A 08 ezután külön méri a
  megbízhatósági fej hozzáadott értékét a második fajtán.
- **Két rész:**
  - **08A:** a lánc és a fej a szintetikus családokon;
  - **08B:** a termék, a lánc, a modell és a fej lépcsőzetesen a valódi banki tételeken (7.).
- **Adatelv:** mint a 07-ben.
  - Tanítás csak publikus és szintetikus adaton.
  - Valós tenantadat csak értékelésre (Dani, 2026-10-28), csak aggregátum publikálható.
- **A H tartalmi fej:** a 08-ban sincs.
- **Gép és szabályok:** mint a 07-ben.
  - spark-dev, egyszerre egy nagy GPU-folyamat;
  - ≥ 15 GB szabad memória a betöltés után, modellbetöltés mellett nincs CPU-feladat;
  - a Qwen-család csak alany;
  - a pecsét alatti kimenetekről a rögzítés előtt csak darabszám és idő kerül naplóba.
  - **Új:** a kinyerés az alany vLLM-példányán fut (`SUBJECT_MODEL`, FP8; D1). Ez a nagy GPU-folyamat, alatta nincs
    HF-betöltés.

---

## 1. Kérdések

- **K1 (08A, fő):** az értelmezési mintán (3.3), a lánc után, felismeri-e a fej az alany rossz opcióválasztását?
  - **(b) altípus, eldönthető:** a döntő értelmezési jel a bemenetben van, a modell mégis a másik, a lánc szerint
    szintén lehetséges jelöltet választja. Ez a magabiztos értelmezési tévedés, és **ez a kutatási kérdés magja**.
  - **(a) altípus, nem eldönthető:** ugyanaz az eset a jel nélkül, a gold Y. A 07B szerint itt az alany saját
    bizonyossága is jelez; a kérdés, hogy a fej hoz-e ehhez képest többletet.
  - **Három alkérdés, három összevetéssel (4.):**
    - átvihető-e a korábbi megbízhatósági tudás;
    - segít-e az értelmezési hibák célzott tanítása (**elsődleges**);
    - adnak-e többletet a rejtett állapotok az egyszerű jellemzőkhöz képest.
  - **Mérés:** a K1 az értelmezési diagnózison fut, vagyis azokon a tételeken, ahol a kinyerés és a szabályalkalmazás
    helyes volt (5.). Mellette a teljes rendszer eredménye is közölve.
  - **A fő vizsgálatok (Dani, 11-02, a G1b 2. köre után; D13):**

    | vizsgálat | szerep |
    |---|---|
    | K1(a), mindhárom család | fő: felismerhető-e a megalapozatlan választás? |
    | K1(b), szabálycsalád | fő: felismerhető-e az eldönthető eset rossz értelmezése? |
    | K1(b), bank és hibaelhárítás | leíró, az eseményszám közlésével |

    A bankon és a hibán két kör után is ritka a (b)-hiba (3%); a ritka hibák felismeréséről ott bizonytalan következtetés
    lenne, ezért a nehezítést nem erőltetjük tovább.
- **K2 (08A, a lánc):** valós kinyeréssel és friss sablonokon eltünteti-e a lánc a K3-típusú tévedést, és mennyit
  veszít a kinyerés? Ugyanaz a lánc fut a valós kinyeréssel és a terv tényeiből vett mezőkkel (orákulum); a kettő
  különbsége a kinyerési veszteség. Mellette a lánc saját hibái: döntést befolyásoló kinyerési hiba, hamis átengedés,
  hamis kizárás, hamis automatikus kötés, emberhez küldés.
- **K3 (08A, gyakorlati):** a természetes összetételű friss teszten, azonos megengedett hibaszint mellett, hány ügyet
  zár le helyesen a rendszer? A lánc automatikus döntéseinek hibái a teljes lezárási hibaarányba beszámítanak, mert
  azokat a fej küszöbe már nem tartja vissza. Ugyanezen itemeken a lánc nélküli 07-es karok az összevetési alap.
- **K4 (08B):** a valódi banki tételeken melyik összetevő ad új helyes megoldást, és melyik okoz új hibát (7.)?

**Az eredmény és a következő lépés előre rögzített kapcsolata,** három külön szinten (D9):
- **A lánc működőképessége (K2):** ha az előzetes fejlesztési cél teljesül, a lánc termékspecifikációba megy,
  függetlenül a fejtől. A páros próba után ez a várható kimenet.
- **Kutatási jel (K1):**
  - **Ha az L-RN felismeri a (b) altípus tévedését, és kimutathatóan javít az L-S sorrendjén:** az értelmezési hiba
    tanítható, a fej fejlesztése a lánc mögött indokolt.
  - **Ha az L-R07 vagy az L-R is javít:** a korábbi tanulás is átvisz, célzott tanítás nélkül. Ez ugyanerre erősebb
    jel.
  - **Ha az L-RN sem javít, és az intervallum kizárja a gyakorlatilag számító hatást:** a fej parkol. A maradék
    értelmezési hibára más út kell: emberi jóváhagyás vagy több kontextus.
  - **Ha az intervallum se a hatást, se a hatás hiányát nem zárja ki:** az eredmény „nem eldönthető”. A következő lépés
    a hatás nagysága és bizonytalansága alapján dől el, nem automatikusan.
- **Gyakorlati haszon (K3):** ha a lánc + fej azonos megengedett hibaszint mellett több ügyet zár le helyesen, mint a
  lánc + alany bizonyossága, a fej a termékben is ad valamit. A lefedettséget és az elfogadott döntések hibáját együtt
  vizsgáljuk (Geifman–El-Yaniv 2017, arXiv 1705.08500).
- **Ha a K1(a)-t az alany bizonyossága egyedül is hozza,** a nem eldönthető esetek kiszűréséhez nem kell fej.

## 2. A lánc

### 2.1 Három állítás a jelöltekről (D2, D3)

A lánc minden jelöltről a következő három állítás közül legfeljebb egyet tesz. Ha egyiket sem tudja megtenni, a
jelölt lehetséges marad.

| a lánc megállapítása | következmény |
|---|---|
| a jelölt **bizonyíthatóan ellentmond** az ellenőrzött adatoknak | kizárható, kikerül a listából |
| a jelöltről **nincs elég információ** (a döntéshez szükséges mező hiányzik, nem ellenőrizhető, vagy az átváltás bizonytalan) | lehetséges marad |
| a jelölt **megfelel az előre rögzített, elegendő kötési feltételeknek** | automatikusan kiválasztható |

- **Az, hogy egy jelölt maradt, önmagában nem kötési ok.** Egy banki díj mellett véletlenül maradhat egy azonos összegű
  számla. Ha a megmaradt egy jelölt nem teljesíti a kötési feltételeket, a modell dönt: kiválasztja, vagy X, Y vagy Z.
- **X a lánctól csak akkor,** ha minden jelöltet bizonyított ellentmondás zár ki, és minden kizárás ellenőrzött
  mezőkön áll. Hiányos kinyerésből, bukott ellenőrzésből vagy bizonytalan átváltásból nem következik X.
- **Ikrek:** a lánc **nem ad automatikus Y-t.** Az azonos strukturált mezőjű jelöltek a modellhez mennek, mert a
  szöveg még tartalmazhat döntő jelet. Erre épül a 3.3-as értelmezési minta, és a 07B-ben 40 ikres tételt Dani el
  tudott dönteni. Automatikus Y-hoz külön, igazolt feltétel kellene; a 08-ban ilyet nem vezetünk be. A strukturáltan
  azonos ikrek számát leíró sorként közöljük.
- **A kizárási és kötési feltételek családonként és adatforrásonként előre rögzülnek** (D2, a G1 végén):

| család | kizárás (bizonyított ellentmondás) | automatikus kötés (elegendő feltétel) |
|---|---|---|
| bank (szintetikus) | a számított teljes összeg (arány, árfolyam után) tűrésen túl eltér a jelölt bruttójától, és minden ehhez használt mező ellenőrzött; a deviza ellentmond, és nincs árfolyam | a hivatkozás pontosan egy jelölt számlaszámát tartalmazza teljes egyezéssel, **és** a számított összeg egyezik a jelölt bruttójával, **és** a szöveg nem nevez meg más partnert |
| hibaelhárítás | egy ellenőrzött, a szabály egységére átváltott mérés kívül esik az ok szabálytartományán | nincs: a tünet és az ok illesztése értelmezés |
| szabálycsalád | a számított összeg a szabálypont küszöbének másik oldalára esik | nincs: a kategória értelmezés |
| bank (valódi, 08B) | csak strukturális ellentmondás (például a deviza, az irány); **az összegeltérés itt nem kizáró ok**, mert részfizetés vagy több számlás utalás lehet | mint a szintetikus banknál, a partner a szervezet törzsadatából |

- **Ha az ellenőrzés elbukik,** vagyis a kinyerés ellentmondásos, a tétel emberhez megy („lánc: ellenőrzés bukott”),
  nem lezárt, és nem jut a modellhez.
- **A modell bemenete:** a szöveg, egy „Ellenőrzött adatok” blokk (a kiszámított értékekkel, csak ellenőrzött mezőkből)
  és a megmaradt jelöltek.
- **A lánc négy kimenete:**
  1. automatikus kötés;
  2. X a lánctól;
  3. emberhez;
  4. **a modell dönt** (legalább egy megmaradt jelölt, kötési feltétel nélkül), és a fej ezt a döntést pontozza.

### 2.2 Kinyerés és ellenőrzés

- **A kinyerés (az alany, kötött JSON-séma):** minden mezőhöz négy adat tartozik:
  - érték;
  - szerep (zárt lista családonként, például részlet-arány, áfakulcs, bruttó összeg, árfolyam, mért érték);
  - forrásrészlet (szó szerinti szövegrész);
  - kapcsolat: melyik számlához, melyik méréshez vagy melyik szabályponthoz tartozik, ha a szöveg megmondja.

  Példa a kockázatra: a 27%-os áfakulcsot részfizetési aránynak olvassa. A szó szerinti egyezés ezt átengedné, a kód
  pedig hibátlanul számolna rossz bemenetből.
- **Az ellenőrzés (kód):**
  - a forrásrészlet szó szerint szerepel a szövegben, és az érték a részletből a nyelv számformátumával kiolvasható;
  - **szerepfeltételek:**
    - áfakulcs csak az adott ország kulcsai közül;
    - a részlet-arány 1–99%;
    - az egység a mért mennyiséghez illik;
    - az árfolyam ésszerű sávban;
  - egy forrásrészlet csak egy szerepet tölthet be;
  - ha van kapcsolat, a hivatkozott számlaszám, mérés vagy szabálypont szó szerint létezik a jelöltek vagy a szabályok
    közt;
  - ahol redundáns adat van, belső egyezés (nettó + áfa = bruttó, arány × bruttó = összeg).
- **A döntést befolyásoló kinyerési hiba** (D9): a tételen a lánc kimenete a valós kinyeréssel más, mint ugyanannak a
  láncnak a kimenete a terv tényeiből vett mezőkkel. Más lehet:
  - a kizárt jelöltek halmaza;
  - az automatikus kötés;
  - az X;
  - a modellnek mutatott ellenőrzött értékek.

  A mezőszintű pontosság emellett leíró sor.
- **Hamis átengedés:**
  - **számláló:** azok a tételek, ahol döntést befolyásoló kinyerési hiba van;
  - **nevező:** azok a tételek, amelyeken az ellenőrzés átment.

### 2.3 Feltevések

- **A jelöltek szabályai strukturáltak.**
  - A szintetikus családokban ez a generátor tervéből jön (partner, összeg, típus, küszöb, ok-szabály).
  - A termékben a számlák és a költségszabályzat táblái strukturáltak.
  - A hibaelhárítási szabályok a termékben nem feltétlenül azok. Ez korlát, és az eredménylapon közölni kell.
- **A kinyerés az alany dolga, az ellenőrzés a kódé.** Az alany a rendszer része, ezért a „Qwen csak alany” szabály
  nem sérül. A gold és a címke soha nem az alanytól jön.

### 2.4 Kód

- `kor08/eszkozok/`, a 07 mintájára burkolóként: a 07 manifestelt fájljaihoz nem nyúlunk.
- **Egységtesztek a megismert adaton** (07 T500, F1-próbák, a nehéz minta 1–3. köre, K3 diag):
  - a kinyerés pontossága mezőnként, szerepenként és kapcsolatonként, a terv tényeihez mérve;
  - a döntést befolyásoló kinyerési hibák aránya;
  - a lánc kimeneteinek eloszlása;
  - a K3 diag-on a lánc + alany helyes aránya valós és orákulum-kinyeréssel.
- **Ezek tervezési számok, nem állítások,** ahogy a 07 F1-ében.

## 3. Adat (08A)

### 3.1 Tervezési próba a megismert adaton

- **Szeletek:** a 07 nyitott szeletei (T500, CAL és TESZT az F5 óta, a nehéz minta három köre, a K3 diag). Csak
  tervezésre valók.
- **Ami itt dől el:**
  - a kinyerési séma és a prompt;
  - az ellenőrzés tűrései;
  - a kizárási és kötési feltételek (2.1);
  - a lánc kimenetének szövegformája;
  - az értelmezési konstrukció (3.3).
- **Számolva:** a T500-ból a lánc után hány tanítható modelldöntés marad, és köztük hány helyes és hány hibás. A lánc
  jelentősen csökkentheti a tényleges tanítómintát; ettől függ a 3.5 mérete.
- **Erőbecslés:** itt készül, a próba számaiból (6.).

### 3.2 Friss CAL és TESZT, természetes összetétel

- **Új sablonok,** a 06 és a 07 sabloncsoportjaitól diszjunktan. A generátor mint a 07-ben: Muse-Glimmer-30B,
  rögzített verzióval, a tényellenőrző kapuval. A 07 F2 a három családon kb. 3 óra volt.
- **Összetétel:** a 07 D9-e (MATCH 60 / NO_MATCH 20 / MISSING_DATA 10 / OUT_OF_SCOPE 10%), fele magyar, fele angol.
  Ebből természetesen kevés tétel igényel számítást, ezért a K3 súlya kicsi; a K3-típus és az értelmezési minta
  külön (3.3, 3.4).
- **Méret:** családonként CAL 500 + TESZT 1000, mint a 07-ben (D5).
- **Kalibráció az új bemeneten:** a temperature és a τ a friss CAL-on, a lánc kimenetén (4.).

### 3.3 Értelmezési diagnosztikai minta

- **Mi kerül bele:** MATCH-itemek, ahol a lánc után legalább két jelölt marad lehetséges, és egyik sem teljesíti az
  automatikus kötés feltételeit. A gold és a csali minden ellenőrizhető adatban egyezik, csak egy értelmezési jelben
  tér el.
  - **Bank:**
    - partner-azonosság: kereskedelmi név vagy jogelőd neve a számlán szereplő névvel szemben, vagy hasonló nevű másik
      cég;
    - a közlemény megrendelésszámra vagy szerződésszámra hivatkozik, nem számlaszámra;
    - harmadik fél fizet a partner helyett.
  - **Hibaelhárítás:** két ok, amely minden átváltott mérésnek megfelel; a tünet leírása dönt (mikor jelentkezik,
    milyen körülmény előzte meg).
  - **Szabálycsalád:** kategóriahatár (például oktatással egybekötött vacsora, szoftveroktatás, ajándék vagy
    reprezentáció). A küszöb oldalát a lánc dönti el.
- **A döntő jel a bemenetben legyen, ne csak a generátor háttértervében.**
  - Egy kereskedelmi név és egy cégnév kapcsolata csak akkor tesz eldönthetővé egy esetet, ha a bemenet ki is mondja:
    a tétel szövegében („korábbi nevén …”), vagy a jelölt adataiban („… Kft., kereskedelmi név: …”).
  - A tényellenőrző minden (b) itemen igazolja, hogy a jel szerepel; minden (a) itemen azt, hogy sem ez, sem más döntő
    jel nem szerepel.
- **Két altípus párban (D6):**
  - **(b) eldönthető:** a jel a bemenetben, a gold MATCH;
  - **(a) nem eldönthető:** ugyanaz az eset a jel nélkül, a gold Y.

  A javasolt arány 3 : 1, vagyis minden (a) itemnek van (b) párja, de nem minden (b) itemnek van (a) párja.
- **A párok együtt mozognak:**
  - ugyanabban a sabloncsoportban, tehát ugyanabban a tanítási vagy tesztszeletben;
  - a bootstrapban ugyanabban a klaszterben;
  - a vak címkeauditba együtt kerülnek (D7).
- **A nehezítés csak a próbamintán történik,** a 07 D11-e szerint.
  - Fejlesztési minta a 07 ismert sablonjain. A konstrukció addig erősödik, amíg a (b) altípuson az orákulum-lánc +
    alany legalább 20%-ban rossz opciót választ. Az orákulum-láncot azért, hogy a hibát ne a kinyerés okozza.
  - Utána a konstrukció és a méret rögzül, a G1 végén (D12).
  - A végső minta a friss sablonokon készül, egyszer, a rögzítés után; a kiolvasás pecsét alatt fut, a nyitás Dani
    engedélyével.
- **Méret:** két tervezési cél családonként, és mindkettő számít az erőbecslésben:
  - legalább 40 rossz opcióválasztás a (b) altípuson. 20% hibánál ez kb. 200 (b)- és 65 (a)-item;
  - legalább 30 független sabloncsoport.

  **Dani (11-02, a 2. kör után):** a K1(b) fő vizsgálata a szabálycsaládé, és ott a mintaméret az **audit (D7) után
  megmaradó, megbízható hibaarányból** tervezett; a 20% tervezési támpont marad. A bankon és a hibán a (b) mérete a
  K1(a)-hoz kell (a párok miatt), a (b)-hiba eseményszáma leíró. A K1(a) erőbecslése családonként külön (D6).

  A tényleges hibaszámot közöljük, újabb példát nem generálunk.
- **Címkeminőség (D7):**
  - a Gemma második ítélete triage-ként mind az itemen;
  - Dani vakon nézi a jelzetteket és családonként 30 véletlen párt, a párokat együtt.

### 3.4 A K3-típus friss sablonokon (K2)

- **A négy K3-változat** (részfizetés, mértékegység-váltás, nettó / bruttó, deviza) a friss sablonokon, változatonként
  kb. 100 item. Ugyanazzal a rögzített konstrukcióval, mint a K07K3.
- **Három út ugyanazon az itemen:**
  - lánc nélkül (a 07 karjai);
  - lánc valós kinyeréssel;
  - **ugyanaz a lánc** a terv tényeiből vett mezőkkel (orákulum).

  A második és a harmadik különbsége a kinyerési veszteség.

### 3.5 A fej tanítóadata

- **Előtanítás:** a D_meta, a 07 receptje szerint. A lánc ott nem alkalmazható, ezért nyers formátumban.
- **Finomhangolás, L-R:** a 06 T500, a láncon átvezetve, hogy a fej a lánc kimenetének formáját lássa.
  - A T500-ban kevés tétel igényel számítást, és értelmezési tévedés sincs benne. Az L-R így főleg azt vizsgálja, átvisz-e
    a korábbi tanulás az új hibatípusra.
- **Finomhangolás, L-RN (elsődleges, D8):** a láncos T500 plusz egy **értelmezési tanítóminta**.
  - Ugyanaz a konstrukció és ugyanaz a párszerkezet, mint a 3.3-ban, mindkét altípussal.
  - Sabloncsoportjai diszjunktak a 3.3 próbájáétól, a végső mintáétól és a friss CAL / TESZT-étől.
  - A tanítóminta lánca az orákulum-mezőkkel fut. A tanítás így a valódi értelmezési hibán tanul, nem kinyerési zajon.
  - **Méret:** a G1 számaiból rögzül (D8). Javaslat: annyi, hogy a hibás modelldöntések száma legalább akkora legyen,
    mint a láncos T500-é; kiindulásként 300 item családonként.
- **Az L-LRN** ugyanezen az adaton tanul, hogy a rejtett állapotok többlete mérhető legyen.

## 4. Karok és összevetések

| kar | a döntés | megbízhatóság | tanítóadat |
|---|---|---|---|
| **L-S** | lánc + alany | az alany saját pontszáma a választott válaszon | — |
| **L-R07** | lánc + alany | a 07 B1-4R, befagyasztva | a 07-es |
| **L-R** | lánc + alany | fej: D_meta-előtanítás, finomhangolás, 3 seed (17, 42, 73) | láncos T500 |
| **L-RN** | lánc + alany | mint az L-R | láncos T500 + értelmezési tanítóminta |
| **L-LR** | lánc + alany | L2-logisztikus regresszió: a 07 B1-4LR 10 jellemzője + a lánc jellemzői (megmaradt és kizárt jelöltek száma, a számított és a jelölt-érték eltérése) | láncos T500 |
| **L-LRN** | lánc + alany | mint az L-LR | mint az L-RN |
| 07 B1-4S, B1-4R | lánc nélkül | a 07-es | a 07-es |

| kérdés | összevetés |
|---|---|
| átvihető-e a korábbi megbízhatósági tudás? | L-R07 − L-S és L-R − L-S |
| **segít-e az értelmezési hibák célzott tanítása? (elsődleges)** | **L-RN − L-S** és L-RN − L-R |
| adnak-e többletet a rejtett állapotok az egyszerű jellemzőkhöz képest? | L-RN − L-LRN |
| mit tesz a lánc a 07-es rendszerhez képest? (K2, K3) | lánc + L-S vagy L-RN a 07 B1-4S és B1-4R ellen, ugyanazokon az itemeken |

- **Kalibráció az új bemeneten:** a temperature és a τ minden láncos karnál a friss CAL-on, a lánc kimenetén. A 07-es
  nem öröklődik, mert a bemenet formája más.
- **A fejek a G4 előtt készülnek** és a G4 hash-lezárásának részei, ahogy a 07 F3R-ben.

## 5. Végpontok

**Két eredményszint, mindkettő kötelezően közölve:**
- **Teljes rendszer:** minden kinyerési, kizárási, automatikus kötési és döntési hiba beleszámít.
- **Értelmezési diagnózis:** előre rögzített részhalmaz. Ide azok a tételek tartoznak, ahol
  - nincs döntést befolyásoló kinyerési hiba (2.2);
  - a gold nincs kizárva;
  - nincs automatikus kötés, és a tétel a modellhez jutott.

  A részhalmaz arányát közöljük. Mellette azt is, hogy a kiesés összefügg-e az altípussal vagy a nyelvvel, mert a
  kinyerési siker a nehézséggel együtt járhat.

**A végpontok:**
- **K1 elsődleges:**
  - **Két fő vizsgálat (Dani, 11-02; 1.):**
    - **K1(b), a szabálycsaládon:** az értelmezési diagnózison, a (b) altípuson, a modell SELECT-jein a rossz opció
      felismerése (AUROC) és a SELECT-AURC. A bank és a hiba (b)-je leíró, az eseményszámmal; **a háromcsaládos átlag
      nincs a fő döntési szabályban.**
    - **K1(a), mindhárom családon, családonként:** a modell Y-aránya, a bizonytalan esetekből automatikusan lezárt arány,
      és AUROC a (b) helyes SELECT-jei és az (a) SELECT-jei közt (a 07B feltáró számának megerősítő párja).
  - **A fő pár:** L-RN − L-S, mindkét fő vizsgálaton.
  - **Mellette:** a 4. pont többi összevetése. **A szabálycsalád K1(a)-ján külön is:** L-RN − L-LRN (az ugyanazon
    példákon tanított logisztikus kar), mert ott az alany saját bizonyossága a pilotban fordítva rendez (AUROC 0,40, 2. kör).
  - **Ugyanez a teljes rendszeren,** leíróan.
- **K2:** a K3-típuson a helyes arány a három úton (3.4), változatonként és nyelvenként. A lánc hibái a 2.2
  definícióival:
  - a döntést befolyásoló kinyerési hiba aránya;
  - a hamis átengedés;
  - hamis kizárás: a gold kizárva;
  - hamis automatikus kötés;
  - az emberhez küldött arány;
  - a mezőszintű pontosság, leíróan.
- **K3:** a friss TESZT-en a hasznos lefedettség és a lezárási hibaarány a 07 D9-e szerint, **a lánc automatikus
  kötéseivel és X-eivel együtt** (D4). Mellette:
  - a lánc kimeneteinek eloszlása, a saját hibaarányukkal külön sorban;
  - ΔAURC a modell döntésein, L-RN − L-S;
  - ugyanezen itemeken a 07 B1-4S és B1-4R lánc nélkül.
- **Leíró, kötelezően:**
  - családonként és nyelvenként (a páros próbában az angol küszöbhiba külön jelenség volt);
  - a strukturáltan azonos ikrek száma (2.1);
  - a futások közti eltérés;
  - Brier és ECE.

## 6. Statisztika

- **Mint a 07-ben:**
  - sabloncsoportos klaszteres bootstrap, 10 000 ismétlés; az (a)/(b) párok egy klaszterben;
  - a seedek átlaga replikánként;
  - kétoldali p, a családok Holm-korrigált p-je leíró.
- **A K3 bootstrapja** a τ-t replikánként újraválasztja.
- **Olvasat a hatás nagysága és bizonytalansága szerint (D9).** A pontbecslés és a 95%-os intervallum mindig közölve.
  Az olvasat nem egy szignifikanciaküszöbből jön (ASA-állásfoglalás a p-értékekről, 2016). A gyakorlatilag számító
  hatás előre rögzített (D9: AUROC 0,60; ΔAUROC 0,05).

| olvasat | feltétel |
|---|---|
| felismeri, érdemben | az intervallum alsó határa > 0,5, és a pontbecslés ≥ 0,60 |
| felismeri, de gyengén | az alsó határ > 0,5, a pontbecslés < 0,60 |
| nem eldönthető | az intervallum tartalmazza a 0,5-öt, a felső határ ≥ 0,60 |
| gyakorlatilag nem ismeri fel | a felső határ < 0,60, és az intervallum tartalmazza a 0,5-öt |
| fordítva rangsorol | a felső határ < 0,5 |

  - A párokra ugyanez, 0 és 0,05 határokkal: javít érdemben / javít, de gyengén / nem eldönthető / érdemben nem javít
    / ront. A SELECT-AURC-nál, ahol a kisebb a jobb, előjelfordítással.
- **Erő:** a G1-ben becsüljük, a (b) altípus várható rossz opcióválasztásainak számából **és** a független
  sabloncsoportok számából. Ha a becslés szerint a fő pár „nem eldönthető” lenne egy 0,05-ös valódi javulásnál is, azt a
  rögzítés előtt jelezzük, és a méretről Dani dönt.

## 7. 08B: a hozzáadott érték valódi banki tételeken

- **A fő összevetés lépcsőzetes,** a 07 D15 kiegészítő elrendezésében (a meglévő kötést és kategóriát semmi nem írja
  felül):
  1. a termék önmagában;
  2. termék + lánc;
  3. termék + lánc + modell (az alany bizonyosságával, L-S);
  4. ugyanez megbízhatósági fejjel (L-RN, mellette L-R07).

  **Minden lépcsőn két szám:** hány új helyes megoldást ad az előzőhöz képest, és hány új hibát okoz. Mellette az
  ütközésjelzések, ahol a lépcső mást mond, mint a termék.
- **A lánc a valódi adaton:**
  - az összeg és a deviza strukturált mező;
  - a közleményből a hivatkozás és az esetleges arány kinyerése, szereppel és forrásrészlettel;
  - kizárás csak strukturális ellentmondásra, az összegeltérés nem kizáró ok (2.1);
  - automatikus kötés a rögzített feltételekkel;
  - ikrek a modellhez.
- **Fejlesztési ellenőrzés: a 262 <tenant> tétel Dani meglévő címkéivel.** A jelöltlista ugyanaz (07 D7), így a címkék
  újra használhatók. A minta ismert, ezért az eredmény fejlesztési, nem megerősítő. A G0 után bármikor mehet (CPU és egy
  rövid kiolvasás).
- **Megerősítő: friss valódi minta (D10).**
  - **Mi kerül bele:** a <tenant> 10-01 utáni tételei, amint a termékbe kerülnek (kb. 65 tétel / hó). A 150 friss tétel a
    kezdő minta.
  - **Ki címkéz:** Dani, vakon, ugyanazzal a lappal és a 07 D7 szabályaival.
  - **Az eljárás:** a 08A után befagyasztva.
  - **A megerősítő erőt a ténylegesen új lezárások és hibák száma adja, nem a tételszám.** A 07B-ben a modell a 262-ből
    3 új kötést adott. Ugyanilyen arány mellett 150 friss tételben 1–2 új lezárás várható, és ebből a többlet tartós
    megbízhatóságáról kevés következik. Ezért a megerősítő olvasatnak előre rögzített minimuma van (D10). Alatta az
    eredmény leíró, és a minta tovább gyűlik vagy más tenanttal bővül.
- **Adatvédelem:** mint a 07B-ben. A tételek és a címkék helyben, illetve a spark-deven maradnak; csak aggregátum
  kerül ki.

## 8. Fázisok

| fázis | tartalom | GPU | feltétel |
|---|---|---|---|
| G0 | a lánc kódja (kinyerési séma szereppel, forrásrészlettel és kapcsolattal; ellenőrzés; számítás; kizárás és kötés; orákulum-út; kimenetforma), egységtesztek a megismert adat tényein | — | a 10. pont nyitott javaslatai |
| G1 | tervezési próba: kinyerés az alannyal a megismert szeleteken, a lánc pontossága valós és orákulum-úton; a T500 tanítható modelldöntései a lánc után; az értelmezési konstrukció fejlesztési mintája és kiolvasása; erőbecslés. **A G1 végén, a G2 előtt az előzetes rögzítés (D12):** kérdések, karok, mintaméretek, kizárási és kötési szabályok, az értelmezési diagnózis definíciója, végpontok, olvasati küszöbök, az elemzők kódja | igen | G0 |
| G2 | friss sablonok; CAL + TESZT, K3-típus, értelmezési minta és értelmezési tanítóminta generálása; Gemma-triage, Dani auditja | igen | G1 rögzítése, Dani „mehet”-je |
| G3 | kinyerés a friss szeleteken (vLLM, egyszer, a kimenet hash-elve); a lánc valós és orákulum-úton; kiolvasás pecsét alatt (HF, négyállapotú keret), a lánc nélküli kiolvasás is a K2–K3 összevetéséhez | igen | G2, az audit kapuja |
| G3R | a fejek tanítása és mentése (L-R, L-RN, L-LR, L-LRN), temperature-ök | — (CPU) | G2 (a tanítóminta); GPU-s kiolvasás mellett nem fut |
| G4 | **a végrehajtás lezárása:** az elkészült adatok, a kinyerési kimenetek, a lánc kimenetei és a fejek hash-ei; a G1 rögzítésének ellenőrzése | — | G3, G3R |
| G5 | a pecsét nyitása, pontozás, elemzés a G1-ben rögzített elemzőkkel, eredménylap | — | G4, Dani engedélye |
| B8 | 08B: fejlesztési ellenőrzés a 262-n; a megerősítő friss minta, ha eléri a D10 minimumát | kicsi | G0 (fejlesztési); G5 és D10 (megerősítő) |

- **A rögzítés két lépése (D12):**
  - **G1 vége:** az előzetes rögzítés köti a kérdéseket, a szabályokat és az elemzőket, mielőtt friss adat készül.
  - **G4:** csak a végrehajtást dokumentálja, ott már semmi nem dől el.
- **A GPU-idő becslése** a G0-ban készül a 07 F2–F3 és a K07EJ2 naplójából. Újdonság a kinyerés vLLM-futása, amely a
  HF-kiolvasással nem fut egyszerre.

## 9. Kockázatok

- **A lánc túl jól működik, és kevés értelmezési hiba marad.** Ekkor a K1-nek nincs elég eseménye. Erre szolgál az
  értelmezési konstrukció próbája és az erőbecslés a G1-ben. Ha a próbán sem jön össze 20%, azt a rögzítés előtt
  közöljük.
- **A lánc után kevés tanítható modelldöntés marad a T500-ban.** A G1 megszámolja. Ez az L-R-t gyengítheti, az L-RN-t
  a tanítóminta pótolja.
- **Az értelmezési konstrukció valóban kétértelmű,** és a „tévedés” címkezaj. Ellenszer:
  - a jel a bemenetben, tényellenőrzővel igazolva (3.3);
  - Gemma-triage és Dani auditja;
  - az (a)/(b) párok.
- **A kinyerés hibája szerepcserével csúszik át** (például az áfakulcs részlet-aránynak olvasva). Ellenszer:
  - szerep, forrásrészlet és kapcsolat a kinyerésben;
  - szerepfeltételek az ellenőrzésben;
  - a döntést befolyásoló hiba mérése az orákulum-úthoz képest (2.2).
- **Az értelmezési diagnózis szelektált részhalmaz.** Ha a kinyerés éppen a nehéz tételeken bukik, a K1 könnyebb
  tételeken fut. Ezért a kiesést altípus és nyelv szerint közöljük, és a teljes rendszer eredményét is.
- **A strukturált szabály feltevése** a hibaelhárításnál a termékben nem biztos (2.3).
- **A fej más formátumú bemenetet lát, mint amin a 07-ben tanult.** Ezért van külön L-R07, L-R és L-RN.
- **Az L-RN a konstrukciót tanulhatja meg, nem az értelmezést.** A tanítóminta sablonjai diszjunktak, de a konstrukció
  közös. A K1 pozitív eredménye ezért ezen a konstrukción érvényes, és a 08B valódi adata a próbája.
- **A vLLM nemdeterminisztikus** (a spark-deven példányok közt ±2–5 item / 150 billen). A kinyerés egyszer fut, a
  kimenete rögzül, a G4 hash-lezárásának része. Ha reprodukálni kell, a BI + TRITON_ATTN beállítással.
- **A valódi minta kicsi,** és kevés új lezárást ad. A megerősítő 08B hónapokat várhat, vagy más tenant kell hozzá
  (7.).
- **Dani ideje:** az audit (kb. 90 pár + a jelzettek) és a 08B friss címkézése.

## 10. Döntések (Dani)

| # | kérdés | javaslat / döntés |
|---|---|---|
| D1 | ki végzi a kinyerést | **Dani (11-02): valódi kinyerés, szereppel, forrásrészlettel és kapcsolattal.** Az alany a vLLM-példányán (FP8), családonként kötött JSON-sémával; a szabályalapú kinyerő csak leíró összevetés a G1-ben. A döntések kiolvasása a 07-es HF BF16 úton marad, hogy a 07 karjaival összevethető legyen |
| D2 | a lánc állításai a jelöltekről | **Dani (11-02): három külön állítás** (kizárható / lehetséges marad / automatikusan kiválasztható); egy megmaradt jelölt nem kötési ok; X a lánctól csak akkor, ha minden kizárás ellenőrzött mezőn álló bizonyított ellentmondás. **Dani (11-02): elfogadva** a 2.1 táblája: Automatikus kötés csak a bankon, hivatkozás + számított összeg + nem ellentmondó partner együtt; a hibaelhárításon és a szabálycsaládon nincs. A valódi adaton az összegeltérés nem kizáró ok. Véglegesen a G1 végén rögzül. **Dani (11-02, a G0 után): ha minden jelölt kizárt, a tétel üres listával a modellhez megy, és a modell dönt X, Y és Z közt** (a lánc-X a bank OUT_OF_SCOPE tételein szinte mindig téves volt; `g0.md` 4. pont); az új fejek log(k + 1)-et kapnak, az L-R07 ezeket nem pontozza |
| D3 | ikrek a láncban | **Dani (11-02): az ikrek a modellhez mennek.** A 08-ban nincs automatikus Y; a strukturáltan azonos ikrek száma leíró sor |
| D4 | a lánc automatikus döntései a K3-ban | **Dani (11-02): lezártnak számítanak, és a hibáik a teljes lezárási hibaarányba beszámítanak**; mellette külön sorban, saját hibaarányukkal |
| D5 | a friss szeletek | **Dani (11-02): friss sablonok.** Méret: CAL 500 + TESZT 1000 családonként, mint a 07-ben |
| D6 | az értelmezési minta | **Dani (11-02):** a döntő jel a bemenetben, a párok egy sabloncsoportban, a bootstrapban együtt, az auditban együtt; az erőbecslés a hibaszámot és a sabloncsoportok számát is nézi. **Javaslat:** (b) : (a) = 3 : 1; a próbán az orákulum-láncon ≥ 20% rossz opcióválasztásig erősítve; tervezési cél családonként ≥ 40 rossz opcióválasztás a (b)-n és ≥ 30 független sabloncsoport; a végső minta egyszer. **Dani (11-02, az 1. kör után):** a (b) és az (a) két külön vizsgálati ág (D13), **külön eseményszámmal és erőbecsléssel;** az (a) hibái a (b)-re tervezett D6-feltételt nem teljesíthetik. A 2. kör áttételes jellel; az egyértelműség fontosabb a kulcsszótiltásnál, a szótőegyezés ellenőrző adat, nem a jó példa definíciója; a félrevezető címke 3. körös tartalék, és ha bekerül, ugyanaz a beküldői tipp szerepel az (a)-ban és a (b)-ben; ha ettől az (a) helyes címkéje vitatható, a konstrukció kimarad. **Dani (11-02, a 2. kör után):** a K1(b) fő vizsgálata a szabálycsaládé, mintaméret az audit után megmaradó, megbízható hibaarányból (a 20% tervezési támpont); a bankon és a hibán a nehezítés nem folytatódik, a (b) ott leíró; a félrevezető címke (3. kör) félretéve |
| D7 | a címkeminőség az értelmezési mintán | **Dani (11-02): a párok együtt kerüljenek a vak auditba.** Gemma-triage mind az itemen; Dani a jelzetteket és családonként 30 véletlen párt nézi. **Dani (11-02, a 2. kör után):** az audit előtt a szabálycsalád forgatókönyvei a megadott szabályzat szövegéhez mérve, a modell választásától függetlenül: a (b) legyen egyértelműen eldönthető, az (a) a döntő jel nélkül valóban eldönthetetlen; ami így nem javítható, az egész forgatókönyv kimarad minden változatával. A javított párok modellválasz és bizonyossági pontszám nélkül mennek az auditba |
| D8 | a karok szerepe | **Dani (11-02): az L-RN az elsődleges; az L-LRN ugyanazon az adaton tanul; az L-R07 és az L-R az átvitelt méri.** **Dani (11-02): elfogadva:** az értelmezési tanítóminta mérete a G1 számaiból, kiindulásként 300 item családonként; a tanítóminta lánca orákulum-mezőkkel fut |
| D9 | a siker szintjei és az olvasat | **Dani (11-02): három külön szint** (kutatási jel, a lánc működőképessége, gyakorlati haszon) és **„nem eldönthető” kimenet;** a lánc automatikus döntéseinek hibái a gyakorlati szinten beszámítanak; a hamis átengedés nevezője és a döntést befolyásoló kinyerési hiba definiált (2.2). **Dani (11-02): elfogadva:** a gyakorlatilag számító hatás AUROC 0,60, illetve ΔAUROC 0,05 (6.); a lánc előzetes fejlesztési célja a K3-típus helyes aránya ≥ 90% minden családon és a hamis átengedés ≤ 2% (gyakorlati választás, mint a 07-es 0,03 és 0,05) |
| D10 | 08B | **Dani (11-02): lépcsős összevetés** (termék → + lánc → + modell → + fej), új helyes megoldással és új hibával lépcsőnként; a 262 fejlesztési ellenőrzés; **150 friss tétel kezdő mintának.** **Dani (11-02): elfogadva:** megerősítő olvasat csak legalább 20 új lezárásnál a termékhez képest (a lánc és a modell lépcsőin összesen); alatta leíró, és a minta tovább gyűlik vagy más tenanttal bővül |
| D11 | publikálás | mint a 07-ben: a szintetikus eredmények és a valódi adat aggregátumai |
| D12 | a rögzítés időrendje | **Dani (11-02): két lépés.** A G1 végén, a G2 előtt a kérdések, karok, mintaméretek, kizárási és kötési szabályok, végpontok és elemzők rögzítése; a G4-ben az adatok, a kinyerési kimenetek és a modellek hash-einek lezárása |
| D13 | a K1 két ága és a hamis átengedés mérőszáma | **Dani (11-02):** **K1(a), megalapozatlan választás:** felismeri-e a rendszer, hogy kevés az információ (Y-arány; a bizonytalan esetekből automatikusan lezárt arány). **K1(b), rossz értelmezés:** felismeri-e a fej a rossz számlát, okot vagy szabálypontot, ha a helyes válasz eldönthető (AUROC és SELECT-AURC a (b) választásain). **Gyakorlati eredmény:** hasznos lefedettség a rögzített összetételű teszten. Az (a) SELECT-jei mind hibásak, ezért a (b) helyes SELECT-jeivel vetjük össze, és ezt így nevezzük: az eldönthetetlen választások megkülönböztetése az eldönthető, helyes választásoktól. **Hamis átengedés (D9 ≤ 2%):** a 2.2 szerinti, döntésszintű mérőszám (a lánc kimenete a valós és az orákulumos kinyeréssel eltér, az ellenőrzés átment); a hibás kinyert mező átengedése mezőszinten leíró sor. **Dani (11-02, a 2. kör után):** fő vizsgálat a K1(a) mindhárom családon és a K1(b) a szabálycsaládon; a K1(b) a bankon és a hibán leíró, az eseményszámmal; a háromcsaládos K1(b)-átlag kikerül a fő döntési szabályból |

## Napló

- **11-02:** v0.1 vázlat Dani D16-a alapján (07-runbook). A 07 négy eredményéből: K1, K3, páros próba, 07B.
- **11-02:** v0.2. Dani hét pontosítása beépítve:
  - a lánc három állítása, ikrek a modellhez;
  - szerep, forrásrészlet és kapcsolat a kinyerésben; a döntést befolyásoló hiba és a hamis átengedés definíciója;
  - teljes rendszer és értelmezési diagnózis;
  - orákulum-mezők ugyanazon a láncon;
  - L-RN elsődleges, L-LRN;
  - a jel a bemenetben, párok együtt;
  - három sikerszint, „nem eldönthető”;
  - rögzítés a G1 végén és hash-lezárás a G4-ben;
  - 08B lépcsőzetesen.

  Nyitott javaslatok: D2 tábla, D8 méret, D9 hatásküszöbök, D10 minimum.
- **11-02:** Dani jóváhagyta a négy nyitott javaslatot (D2 tábla, D8 300 / család, D9 AUROC 0,60 és Δ 0,05, D10 ≥ 20 új
  lezárás), és elindította a G0-t.
- **11-02, G0 kész (`kor08/eredmenyek/G0/g0.md`, `kor08/eszkozok/lanc08.py`):** a lánc kódja és az önteszt a
  megismert adaton, orákulum-mezőkkel.
  - **Ellenőrzések:**
    - az opciók kiolvasása 100%, a sablonnal 100% egyezik;
    - a gold kizárva 0, rossz automatikus kötés 0, X a lánctól MATCH-en 0;
    - minden szándékos rontást megfog, Dani 27%-os áfa / részlet-arány példáját is (a 3 átengedett „két szerep” eset
      ismételt érték);
    - a saját egységtábla a K3 VALTAS-ával 71 / 71.
  - **Javítva az önteszt közben:** részfizetési jel arány nélkül → az összeg nem kizáró ok (egy K3-szöveg „40
    százaléka” miatt a gold kizáródott); előjel; CSV-vessző utáni szám; a banki deviza nem kötelező.
  - **Nyitott döntés a G1 előtt (g0.md 4. pont):** ha minden jelölt kizárt, a lánc X-e a bank OUT_OF_SCOPE tételein
    szinte mindig téves (189 / 200, 148 / 150). Javaslat: üres listával a modellhez.
  - **T500 a lánc után a modellhez:** bank 185 / 500 (üres listával 294), hiba 500, szabály 492.
- **11-02:** Dani: minden jelölt kizárva → üres lista a modellnek (D2); a G1 indulhat.
- **11-02 10:13–10:23, G1a-próba (családonként 20, majd 40 item a K3 diag-on és a 06-on, `kor08/eredmenyek/G1/proba`):**
  a valós kinyerés első próbája. **A lánc ellenőrzési szabályán változtattam (a G1 rögzítése előtt, a 2.1
  szövegéhez igazítva):**
  - a bukott mező elvetődik, és a tétel a láncban marad;
  - emberhez csak az ellentmondásos kinyerés megy (ugyanabban a szerepben két eltérő ellenőrzött érték), vagy a
    hiányzó kinyerés.

  Az elvetés csak információvesztés, kizárást vagy kötést nem okozhat. Az első próbán a szigorú szabály egy-egy
  kitalált mező miatt az itemek nagy részét emberhez küldte (a hibán 20 / 20-at a szövegként adott „7,2 mm/s” miatt).
  **További javítások:**
  - a séma szerepenként írja elő, hogy az érték szám legyen, és a kinyert szövegből is az első szám számít;
  - a számlatulajdonos nem partner;
  - a szabálycsaládon a deviza és az alap a forrásrészlet jelölőszavaiból, ha a kinyerő nem adja meg; ismeretlen
    devizánál nincs kizárás (az első próbán 10 gold zárult ki deviza nélküli euróösszeg miatt).

  A 2. próba 240 itemén: emberhez 3, hamis kizárás 0, hamis kötés 0, hamis átengedés 0–8%. A G0 öntesztje a változás
  után is 0 sérülést ad. A vLLM szóköztilalma (`structured_outputs.disable_any_whitespace`) ebben a verzióban nem hat.
- **11-02 10:23, K08G1A elindítva** (`kor08/eszkozok/k08g1a.sh`): kinyerés (06, 07, K3 diag; 64 szál), a lánc két
  úton, a lánc pontossága, kiolvasás (T500 és K3 diag, mindkét út), döntések.
- **11-02, G1b:** az értelmezési konstrukció javaslata (`kor08/ertelmezes-javaslat.md`) Dani jóváhagyására vár; a
  szabálycsalád forgatókönyvei: `kor08/eszkozok/ertelmezes08_szab.py`.
- **11-02 10:28, K08G1A menet:** a kinyerés kb. 2 item / s (a vLLM a kötött JSON-dekódolással kb. 360 token / s 64
  párhuzamos kérésnél). A kinyerés vége kb. 11:55, a kiolvasás (kb. 3500 item, négy sorrend) után a G1a vége kb. 14:00.
- **11-02, G1b előkészítve (CPU):** `kor08/eszkozok/szint08e.py`, a tervek a 07 CAL-sablonokon (családonként 120:
  90 (b) + 30 (a)), a mintapromptok: `kor08/adat/ertelmezes/minta_promptok.md`. A GPU-s generálás Dani jóváhagyására
  vár.
- **11-02 10:45, K08G1A leállítva, rögzítés előtti változás:** a bank 06 első 839 itemén a válaszok 22%-a (185)
  ismétlődő partnermezőkbe futott, és 1024 tokennél csonka JSON lett (a tétel így „nincs kinyerés”, emberhez); ez a
  menetet 0,7 item / s-ra lassította. Javítás: a kinyerő séma legfeljebb 6 mezőt enged (`lanc08.MAX_MEZO`; a valódi
  mezők száma itemenként legfeljebb 4 szerep, illetve 3 mérés), az ismételt azonos mezőket a lánc eddig is összevonta.
  Próba az élő példányon 14 korábban csonka itemen: mind lezárul, a gold bent marad. A G0 öntesztje változatlan. A
  részleges kimenet: `logs/k08g1a/leallitott-1/` (nem használjuk).
- **11-02 10:56, K08G1A újraindítva** (ugyanazzal az alany-példánnyal): az első 320 itemen 0 értelmezhetetlen válasz,
  42 item éri el a 6 mezős korlátot; kb. 1,5 item / s. A kinyerés (11 067 item) vége kb. 13:00, a G1a vége kb. 14:15.
- **11-02, G1b jóváhagyva (Dani: „mehet”)** a javaslat szerint (E-bank-1, E-hiba-1, E-szabály-1). Előtte, a
  generálás nélkül: a tervek `csali_sid` mezőt kaptak a kapuhoz (a tervek egyébként bájtra azonosak, a mintapromptok
  változatlanok); a lánc `ERT` forrása (`lanc08.FORRASOK`; a G0 önteszt forrásai `ONTESZT`-ként változatlanok), az
  `oERT` kiolvasás (`kiolvas08`), a mérés (`kor08/eszkozok/g1b_ert08.py`: kapu = a lánc a goldot és a csalit is
  lehetségesnek hagyja, nincs automatikus kötés, a pár együtt marad vagy esik ki; (b): rossz opcióválasztás, Wilson
  95%; (a): Y-arány). Kapupróba CPU-n, a terv tényeiből írt álszövegeken: családonként 120 / 120 átmegy.
- **11-02 10:57, K08G1B elindítva** (`kor08/eszkozok/k08g1b.sh 1`): megvárja a DONE-K08G1A-t (FAILED esetén nem
  indul), utána Muse → `szint08e gen` + `final` → lánc → kiolvasás → `g1b_ert08` → `kor08/eredmenyek/G1b/kor1.md`.
  Várható vége kb. 15:15.
- **11-02 14:11, K08G1A kész:** 11 067 item kinyerve (értelmezhetetlen válasz 0), hamis kizárás 0, hamis kötés 0
  mindenhol. Eredménylap: `kor08/eredmenyek/G1/eredmenylap.md`.
- **11-02 15:03, K08G1A2 (rögzítés előtti változás):** a bruttó / nettó alap kikövetkeztetése az ellenőrzés
  szabályával (a legközelebbi jelölő az érték körüli ablakban), nem csak a forrásrészletből. Csak a K3 diag valós úton
  változott (22 item); a szabálycsalád lánca újra, a lánc pontossága újra, a `lK3` szabálycsalád kiolvasása újra, a
  döntések újra. K3 diag szabálycsalád, valós úton: 138 → 152 / 199 helyes, hamis átengedés 20,9% → 9,1%. A G0
  önteszt változatlan.
- **11-02 15:01, K08G1B 1. kör kész:** (b) rossz opció 8% / 2% / 7% (a cél ≥ 20%, nem teljesül); (a) Y 1 / 86.
  Feltáró: az alany saját bizonyosságának AUROC-ja helyes vs. hibás döntésre 0,82 / 0,97 / 0,59. A 2. kör javaslata a
  `kor08/ertelmezes-javaslat.md`-ben, Dani döntésére vár (GPU nem fut).
- **11-02 15:35, Dani döntései az 1. kör után:** (1) a 2. kör áttételes jellel, Dani pontosításaival (bank: az aktuális
  fizetés kapcsolata egyértelmű; hiba: a megfigyelés az okleírások alapján csak egy jelöltre illik; szabály: a besorolást
  a megadott szabályzat szövege támasztja alá; az egyértelműség fontosabb a kulcsszótiltásnál). (2) A K1 két ága (D13),
  a D6 külön eseményszámmal és erőbecsléssel ágonként. (3) Célzott kinyerésjavítás most, a fejlesztési adaton: a
  szerepek külön mezőben, a hiányzó érték explicit, az ismétlés nem foglalhat más mező helyén, az árfolyam pénznempárral;
  újrafuttatás a hibás eseteken és egy előre kijelölt kontrollmintán, siker esetén az érintett fejlesztési kimenetek
  egységesen újra. A K3 diag szabálycsalád 34 MATCH → X hibáját (orákulum-úton) külön vizsgálni: érthető-e a blokk és a
  megmaradt szabálypontok jelentése.
- **11-02, javítás a jelentésben:** az (a) döntései 83 / 86 SELECT, 2 X, 1 Y (az első lap 85 / 86 SELECT-et írt). A
  feltáró AUROC az első lapon a két ágat keverte; ágonként: K1(b) 0,85 / 0,99 / 0,85 (7 / 2 / 6 rossz választáson),
  K1(a) 0,81 / 0,98 / 0,52.
- **11-02, a 34 MATCH → X (K3 diag szabálycsalád, orákulum-út):** mind angol nyelvű item (az angol 98-ból 34, a magyar
  100-ból 0); a hibák a küszöbhöz közeli (< 10%) kiszámított értékeknél sűrűsödnek; a gold 7 itemnél az egyetlen
  megmaradt jelölt.
- **11-02 15:50, G1 fejlesztési próbák előkészítve (K08G1C), a futás előtt rögzítve:**
  - **Kinyerés, séma v2** (`lanc08.kinyero_sema2`, `lapit`; `kinyer08 --sema 2`): szerepenként külön mező, a hiányzó
    érték explicit (null / üres lista), szerepenkénti keret (összeg, hivatkozás, partner 2; mérés 5), az árfolyam
    pénznempárral (`par`). A pár ellenőrzése: a pár sávja, és az értékhez legközelebbi párjelölés a szövegben
    („405 Ft/EUR”, „1 EUR = 405 Ft”) ugyanaz a pár; az átszámítás iránya a párból. Pár nélkül (v1, orákulum) a régi
    szabály. A v1 út kimenetei bájtra azonosak, a G0 önteszt változatlan.
  - **A próbaminták** (`kin2_08 valaszt`, `kor08/adat/G1/kin2_proba/minta.json`): hibás = minden item, ahol a v1
    lánckimenete eltér az orákuluméétól vagy emberhez ment (362); kontroll = cellánként 40 a többiből, hash-sorrendben
    (360). sha256: hibas.txt 37c3095d…, kontroll.txt 6bfb7f39….
  - **Az előre rögzített siker:** a hibás eseteken a javult mínusz az elromlott > 0, és a K3 diag szabálycsaládon az
    orákulumtól eltérő és az emberhez küldött itemek száma legalább a felére csökken; a kontrollon legfeljebb 1% új
    eltérés; hamis kizárás és hamis kötés 0. Ha teljesül, az érintett fejlesztési kimenetek (a teljes G1a kinyerés,
    lánc, kiolvasás, döntések) egységesen újra a v2-vel.
  - **Blokk-változatok a szabálycsaládon** (`lanc08 --blokk`, `g1_blokk08`): v1 kimondja, melyik kiszámított értéket
    kell az összeghatárhoz mérni; v2 a megmaradt szabálypontonként kimondja, hogy az összegfeltétel teljesül (a
    lánc ellenőrzött összevetése). K3 diag, orákulum-út; a v0 az eredeti.
- **11-02 15:58, G1b 2. kör előkészítve (CPU), Dani pontosításaival:** `szint08e --kor 2` (saját könyvtár:
  `kor08/adat/ertelmezes/kor2/`, szelet ERT2); a tervek magja az 1. körével azonos (120 / 120), csak a (b) jele új.
  - **Bank:** a közlemény kimondja, hogy ez a fizetés A kötelezettségét rendezi, mert B jogi szerepben fizet (jogutód,
    kezes vagy tartozásátvállaló; `ertelmezes08_szab.BANK_SZEREP2`). A kapu: a szerepszó, a két név, B elöl.
  - **Hiba:** a (b) megfigyeléseket és körülményeket ír le, amelyekből a gold tünete következik; a generátor megkapja a
    többi opció tünetcsoportját is, amelyekre a leírás nem illhet (a gold csoportjának másik oka nincs az opciók közt).
    A kapu: egyik tünet sem szó szerint.
  - **Szabály:** 12 + 12 új, kézzel írt áttételes jel (`JEL2`), mindegyik a gold szabálypont szövegéhez kötve
    (`tamasz`); a kapu: a jel kulcsszava (`kulcs2`) a (b)-ben, az 1. és a 2. kör kulcsszava sem az (a)-ban.
  - A szóátfedés ellenőrző adat, nem kapu (`g1b_ert08` „Ellenőrző adat”). Mintapromptok:
    `kor08/adat/ertelmezes/kor2/minta_promptok.md`. A K08G1B 2. köre a K08G1C után indul.
- **11-02 16:28, K08G1C kész.**
  - **Blokk-változatok (K3 diag szabálycsalád, orákulum-út):** v0 164 / 199 (34 MATCH → X, mind angol), v1 199 / 199,
    v2 198 / 199. A 34 hiba a blokk értelmezésén múlt (melyik kiszámított értéket kell az összeghatárhoz mérni), nem
    értelmezési tévedés volt. `kor08/eredmenyek/G1/blokk_valtozatok.md`.
  - **Kinyerés, séma v2, 1. próba** (`kin2_proba_1.md`): a hibás eseteken 239 / 362 javult, 0 romlott el; a K3 diag
    szabálycsaládon 29 → 5. **A kontrollon 37 / 360 romlott el: az előre rögzített feltétel (≤ 1%) nem teljesül, a
    teljes újrafuttatás nem indul.** Az okok: (1) a v2-ben a deviza kötelező kulcs, a csak számot tartalmazó
    forrásrészletben nem igazolható, és az egész összegmező elvész (bank 06 / 07: 12); (2) a K3 bankon a `reszlet_arany`
    objektum-vagy-null mezője után az alany puszta számot írt volna, a kötött dekódolás szóközzel töltötte ki (13 csonka
    JSON); (3) a „40%-a” összegként (két összeg → emberhez); (4) a hibacsaládon a v2 a mohó dekódolás szórásán belül
    mozgat (kontroll 5 / 120 vissza). A hibás mintán mért javulás részben visszahúzódás az átlaghoz (a mintát a v1
    hibái jelölték ki); a kontroll méri a költséget.
- **11-02 16:33, javítás a 2. próbához (rögzítés előtti változás):** az egyértékű szerepek (részletarány, áfakulcs,
  árfolyam) lapos mezők (`EGYERTEKU2`); az összeg nem lehet százalék és nem lehet árfolyam (a szám után % vagy
  pénznempár); a deviza ellenőrzése és következtetése az érték körüli ablakban, mint az alapé; a hibacsalád a v1 sémán
  marad (`SEMA2_CSALADOK`). A G0 önteszt és az orákulum-út kimenetei változatlanok; a v1 valós úton a szabálycsalád
  22 / 23 / 12 iteme változik, hamis kizárás 0. A 2. próba (K08G1C2) ugyanazon a mintán és ugyanazokkal a feltételekkel
  fut, a bank- és a szabálycsaládon (a kontroll így 240 item); a G1b 2. köre után.
- **11-02 17:19, K08G1B 2. kör kész** (`kor08/eredmenyek/G1b/kor2.md`): (b) rossz opció bank 3 / 89, hiba 3 / 90,
  szabály 20 / 88 (23%); (a) Y 0 / 87. A szabálycsalád 20 hibájából 7 egy forgatókönyvön („szakmai szoftver éves
  licence” → képzés), amelynek a szabályzati alátámasztása gyenge (a tétel szó szerint szoftverlicenc díja); nélküle
  13 / 79 (16%). A D6 teljesülése a szabálycsaládon a D7 auditjától függ; a bankon és a hibán a 2. kör sem éri el.
- **11-02 17:33, K08G1C2 (a kinyerés-javítás 2. próbája) kész** (`kor08/eredmenyek/G1/kin2_proba_2.md`; bank és
  szabály): a hibás eseteken 145 / 313 javult, 1 romlott el; a K3 diag szabálycsaládon 27 → 0. **Az előre rögzített
  siker nem teljesül:** a kontrollon 4 / 240 (1,7%) visszaesés, és **egy hamis kizárás** (07 bank). A teljes
  újrafuttatás nem indul.
  - **A hamis kizárás oka egy ellenőrzési hiba, amely a v1-ben is megvolt:** a „+1 169 690 Ft”-ból kivágott
    „169 690 Ft” forrásrészlet a szövegben megtalálható, és a benne elemzett 169 690 hamis összeget igazolt. Javítás:
    a számok a teljes szövegből, és csak a részleten belül teljesen elférők számítanak.
  - **A kontroll 4 visszaesése:** 1 javítható (a „végösszeg” mellett nincs alapjelölő, a megadott „brutto” miatt az
    egész mező bukott; javítás: ha nincs jelölő, csak az attribútum vetődik el, ellentmondó jelölőnél bukik a mező; a
    devizára és a pénznempárra ugyanígy); 3 a mohó dekódolás szórása (ékezet nélkül átírt forrásrészlet, a mezőnév a
    forrásrészletben, kihagyott részlet-arány).
  - A két javítás után a G0 önteszt és az orákulum-út változatlan; a teljes G1-adaton a v1 valós úton 67 item
    változik, hamis kizárás és hamis kötés 0; a 07-es hamis kizárás itemjén a gold bent marad.
- **11-02 17:39, a 3. próba (K08G1C3) előtt rögzítve:** a feltétel a 2. próbáé, de a **friss `kontroll2` mintán**
  (cellánként 40, a bank- és a szabálycsaládon, a korábbi mintákon kívülről; sha256 ccab1650…), mert a `kontroll`-t két
  próba már látta. Mellette a **zajszint:** a v1 séma újrafuttatása ugyanazon a vLLM-példányon mindkét kontrollmintán
  (a memória szerint a példányok közt ±2–5 item / 150 billen, ezért a ≤ 1%-os feltétel a puszta újrafuttatás zaja
  alatt lehet). A feltétel nem változik; a zajszintet Dani döntéséhez közlöm.
- **11-02 17:59, K08G1C3 (a kinyerés-javítás 3. próbája) kész** (`kor08/eredmenyek/G1/kin2_proba_3.md`; az
  összesítő sor egy előtag-hibáját — a „kontroll” a „kontroll2” kulcsait is összegezte — helyben javítottam és
  újraszámoltam, a cellák nem változtak):
  - hibás esetek: 139 / 313 javult, 1 romlott el; a K3 diag szabálycsaládon 27 → 0; hamis kizárás és kötés 0;
  - **friss kontroll (`kontroll2`): 3 / 240 (1,25%) visszaesés, az előre rögzített feltétel (≤ 1%) szűken nem
    teljesül;** a régi kontrollon 1 / 240. Mind a 3 a K3 bankon: a v2 lapos részlet-arány mezője kimarad, vagy a
    forrásrészlet ékezet nélkül jön („osszege”, „40%-ara”), és nem található a szövegben;
  - **zajszint, a v1 séma újrafuttatása ugyanazon a példányon:** kontroll 8 / 240, kontroll2 5 / 240 tér el az
    orákulumtól (a v2: 1 / 240 és 3 / 240). A v2 a kontrollon kevesebbet billen, mint a v1 a saját újrafuttatásán; a
    ≤ 1%-os feltétel a v1 újrafuttatási zaja (2,7%) alatt van.
  - A teljes újrafuttatás (K08G1A3) nem indul; a feltétel módosítása Dani döntése.
- **11-02 18:19, Dani döntései a 3. próba és a G1b 2. köre után:**
  - **A v2 kinyerés és a v1 blokk megy tovább; a teljes fejlesztési újrafuttatás (K08G1A3) indul.** A 3. próba
    előre rögzített kontrollfeltétele (≤ 1%) **nem teljesült: 3 / 240 = 1,25%;** ez így marad. A zajszint
    összehasonlítási alap lehet, önmagában nem elfogadható hibakeret. (A 17:59-es bejegyzés „tér el” szava pontatlan:
    a v1 újrafuttatásánál is ugyanaz számolt, mint a v2-nél, vagyis a v1 menet a mostani kóddal helyes, az új futás
    nem; csak a kontrollminták helyes itemekből álltak, ezért javulás ott nem volt mérhető.)
  - **A blokk-eredmény megfogalmazása:** a 34 téves X-válasz a bemenet megfogalmazásának javításával megszűnt ezen a
    mintán (a blokk félreértése is értelmezési hiba, amelyre működő javítás van).
  - **Közös kontroll a teljes újrafuttatás mellett, a futás előtt rögzítve:** `kor08/adat/G1/kin2_proba/kozos.txt`
    (sha256 d3488e6e…), cellánként 40 item a bank- és a szabálycsaládon, a `kontroll` és a `kontroll2` mintán kívülről,
    a helyességre szűrés nélkül (16 / 240 a v1 hibás mintájából, a természetes arányukban). Ugyanazon a vLLM-példányon
    a v1 séma friss kinyerése, a v2-é a teljes újrafuttatásból; mindhárom kinyerés (v1 eredeti, v1 újra, v2) ugyanazzal
    a javított lánckóddal és a v1 blokkal. Mért: a v1 eredetihez képest elromlott és javult, emberhez, hamis kizárás és
    kötés, a „friss” és a „hibás mintából” rész külön (a v2-t az utóbbin fejlesztettük). Leíró, nincs elfogadási
    küszöb (`kin2_08 kozos` → `kor08/eredmenyek/G1/kin2_kozos.md`).
  - **A szabálycsalád 2. körének címkéi:** az audit előtt minden forgatókönyv a megadott szabályzat szövegéhez mérve, a
    modell választásától függetlenül (D7); a „szakmai szoftver éves licence” javítva vagy minden változatával kihagyva.
    A 20 / 88 és a kihagyással kapott 13 / 79 dokumentált fejlesztési eredmény marad.
  - **A K1 szűkítése (D6, D13, 1., 3.3, 5.):** fő a K1(a) mindhárom családon és a K1(b) a szabálycsaládon; a K1(b) a
    bankon és a hibán leíró. A félrevezető címke félretéve. A szabálycsalád K1(a)-ján (AUROC 0,40) külön összevetés:
    L-RN az L-S és az ugyanazon példákon tanított L-LRN ellen.
- **11-02 18:40, a szabálycsalád 2. körének címkejavítása (D7 előtt; `ertelmezes08_szab.JAVITAS2`):**
  - **Módszer:** a 12 + 12 forgatókönyv (b) és (a) szövege (a helyzet, illetve a helyzet + az áttételes jel) keverve,
    gold, párosítás és modellválasz nélkül egy független ellenőrhöz került (alügynök), csak a szabályzat öt
    költségnemének egysoros leírásával. Feladat: költségnem vagy „nem eldönthető”, bizonyosság, és vitatható-e. A
    javítás döntései ebből és a szabályzat szövegéből születtek; a forgatókönyvenkénti modellválaszt a döntés előtt nem
    néztem (a 6. forgatókönyv 7 hibája a 17:19-es bejegyzésből ismert volt).
  - **Eredmény (48 szöveg):** négy forgatókönyv tiszta (2., 9., 11., 12.). A 6. („szakmai szoftver éves licence”)
    mindkét változata hibás: a (b) nem eldönthető, az (a) előfizetés. A 3., 7. és 8. (a)-ja egy kategóriába húz (a 7.-é
    és a 8.-é a felszíni szó miatt a csalira: „konferencia-részvétel”, „kiküldetés”), az 1. és a 10. (b)-je csak
    kimondatlan következtetéssel dönthető el (közös számla, illetve a szállodai számlán szereplő vacsora; a szabályzat
    egyikről sem szól).
  - **Javítás:** 1., 10.: a jel a kért összeget mondja ki (a tanfolyam részvételi díja, illetve a félpanziós szállás
    díja, amely a vacsorát tartalmazza). 6.: új helyzet („egy szakmai szoftverhez kapcsolódó szolgáltatás díja”) és új
    jel (a gyártó oktatója négy gyakorlati foglalkozást tartott, vizsgával; a szoftvert a cég korábban megvette). 7., 8.:
    a helyzet a költség jellegét nyitva hagyja („… konferenciához kapcsolódó költségtételek”, „… kiküldetéshez
    kapcsolódó egyik költségtétel”), a 8. jele a számla tárgyát is kimondja.
  - **Második vak ellenőrzés a javított szövegeken (24 szöveg, friss ellenőr):** az 1., 6., 7., 8. és 10. (b)-je a gold,
    (a)-ja „nem eldönthető”. A 3. (a)-ja („laptoptáska és egér vásárlása”) ismét eszköz, ezért **a 3. forgatókönyv
    minden változatával kimarad** (a 2. körben 1 iteme volt). Vitatható maradt: a 7. magyar (b)-je (a
    „konferencia-részvétel” tágan az utat is jelentheti) és a 8. angol (b)-jében a „workshop”; az utóbbi „course” lett,
    a magyar „tréning” mintájára. A D7 audit dönt.
  - **A javított kör (`kor2j`, ERT2J):** 119 terv; 56 betűre azonos a 2. körével (a generálás átvéve), a 6 (a)-tag,
    amelynek promptja nem változott, szintén; a többi újra generálódik (Muse). A lánc a v1 blokkal, az alany döntése
    (B1-4S) a javított körön; a 20 / 88 és a 13 / 79 dokumentált fejlesztési eredmény marad. Utána a vak auditlap
    (`audit08e`, a 06-os lap): minden pár, sablononként egymás után, modellválasz és bizonyosság nélkül. A futtató
    (`k08g1b2j.sh`) a K08G1A3 után indul. A G0 önteszt bájtra azonos.

- **11-02 22:35, a K08G1A3 (20:41) és a K08G1B2J (21:08) eredménye (részletek: `kor08/eredmenyek/G1/eredmenylap.md` 8.):**
  - **Közös kontroll:** friss romlás v2 5 / 224, v1 újra 8 / 224; hamis kizárás és kötés 0. A hibás minta a v1 minden
    hibája, ezért friss itemen javulás e tervben nem mérhető; a v2 12 / 16 javulása a fejlesztési mintáján van.
  - **Teljes futás:** hamis kizárás és kötés 0 minden cellában. Szabálycsalád: a döntést befolyásoló hiba 06: 3,0 →
    1,9%, 07: 3,9 → 2,8%, K3: 9,1 → 0,5%; emberhez 89 → 25.
  - **Visszaesés, K3 diag bank:** 186 → 176 / 186; a 86 angol tételből 10-ben a v2 nem ad részlet-arányt (a v1 mindben
    kinyerte), a 10 téves döntésből 8 ezek közül. Rendszeres, a fejlesztési mintán kívüli hiba. **Dani döntése.**
  - **A v1 blokk a T500 szabálycsaládján** (orákulum-út): helyes 409 → 400, nettó +9 NO_MATCH → SELECT. A K3-on ugyanez
    a blokk a 34 MATCH → X hibát vitte el.
  - **Javított szabálykör:** (b) rossz opció 8 / 87 (9%, Wilson 5–17%); a javított forgatókönyvekben 17 / 45 → 3 / 45,
    a változatlanokban (azonos szöveg, csak a blokk) 3 / 42 → 5 / 42; (a) Y 0 / 28. A 2. kör 20 hibájából 17 a vak
    ellenőrzésen hibásnak talált forgatókönyvekben volt. A D6 20%-a nem teljesül; a mintaméret az audit után.
  - **D7 auditlap kész:** `kor08/adat/ertelmezes/kor2j/audit/atnezo.html` (115 item, sig 115-5d2ef47130).
- **11-02 22:55, Dani döntései a K08G1A3 és a K08G1B2J után:**
  - **A G2-höz a teljes rendszer még nem rögzül.** A kinyerés családonként, a friss mérés előtt rögzítve: **bank v1** (a
    közös ellenőrzési javításokkal), **hiba v1**, **szabály v2** (`kor08/adat/G1/kinyeres_g1`).
  - **Javítás a 22:35-ös bejegyzéshez:** a bank T500 kinyert útján a modellhez jutó itemeken látszó helyes 125 → 130
    önmagában nem javulás: a helyes automatikus kötéssel együtt 199 + 125 = 324 → 192 + 130 = 322 (hamis kötés 0).
  - **A K3 bank másik két téves döntése** (hu:MATCH:0089, en:MATCH:0000) szintén a v2 kinyerésből jön: a forrásrészlet
    nem szó szerinti (ékezet nélküli „30%-a” a szöveg „30%-ára” helyett, illetve lemaradt előjel, így a szám a részlet
    szélén túl kezdődik); az ellenőrzés elveti a mezőt, kizárás nem marad, az alany a 4 jelölt közül téved. Hamis
    kizárás nincs; a v1 mindkettőt helyesen adja.
  - **Az eredménylap 8. pontjának javítása:** a hibacsalád kinyerése nem változott (a v1 fájl átmásolva); a 06-os
    lánckimenet 1 TESZT-itemen tér el a lánckód javítása miatt, nem a példány nemdeterminizmusa miatt.
  - **A blokk:** a v1 túl könnyen választásra ösztönözhet. A következő blokk válassza szét, melyik kiszámított értéket
    kell használni, melyik részfeltétel teljesül, és mely feltételről nem született döntés (az „összegfeltétel
    teljesül” könnyen „a jelölt helyes” jelentést kap). Először a megismert MATCH és NO_MATCH kontrollokon; a K3 javulása
    és a természetes összetételű minta visszaesése együtt dönt.
  - **Címkeaudit:** a 115 item auditja megy (Dani). Az első, vak választás külön rögzül, a felülvizsgált címke külön.
    A lap javítva (`audit08e`): a 06-os lapon a felfedés után az opciógombok kattinthatók maradtak, és felülírták a vak
    választást, az „Előző” pedig törölte a rekordot. Most a vak választás zárolva (`valasz`), a felülvizsgálat külön
    (`masodik`, `felulvizsgalt`, `megj2`), az „Előző” csak lapoz; a gold, az állapot és a tények kódolva a forrásban.
    Ugyanaz a sig (115-5d2ef47130), ugyanaz a kulcsleképezés.
  - **K1-tervezés:** a szabálycsalád 9%-os arányán nem nehezítünk tovább. Pontbecsléssel kb. 450–500 eldönthető
    szabályesetből várható 40–45 rossz választás (tervezési becslés, nem eseményszám és nem statisztikai erő); a
    végleges méret az audit után, elég különálló sabloncsoporttal. K1(a) mindhárom családon, K1(b) elsődlegesen a
    szabálycsaládon, a bank és a hiba K1(b)-je leíró.
  - **K08G1D (előre rögzítve, a futás előtt):** (1) a bank lánca a v1 kinyerésen, a pontosság és a döntések a
    `kinyeres_g1`-gyel (az előző állapot: `arch_v2/`, `*_v2.md`). (2) Célzott blokkpróba, orákulum-úton, a K3 diag
    (199 MATCH) és a 06 T500 (300 MATCH, 100 NO_MATCH, 50 MISSING_DATA, 50 OUT_OF_SCOPE) szabálycsaládján; a blokk
    csak a MATCH és a NO_MATCH itemekben ír (T500: 300 + 92, K3: 199). Változatok: v0, v1, v2 (megvolt), **v3** (a v1
    sora + „az összeghatár alapján nem kizárt: … pont” + „a rendszer nem ellenőrizte a tétel költségnemét …; az
    összeghatár egyezése önmagában nem jelenti, hogy a pont illik a tételre”), **v4** (a v1 sora + pontonként:
    „összeghatár (…): teljesül / nem ellenőrizhető; a költségnem („…”): nincs ellenőrizve”). Mért (`g1_blokk08b`): a
    helyes szám mintánként és állapotonként, a hibatípusok (főleg NO_MATCH → SELECT és MATCH → X), az itemszintű
    javult / romlott a v0-hoz és a v1-hez. A v0 újraolvasása determinizmus-ellenőrzés (K3: 164, T500: 409). Leíró, a
    választás Dani döntése a két minta együtt alapján; az ERT2J-re (az audit alatti értelmezési mintára) a próba nem fut.
- **11-02 23:04, a D7 audit exportja (`kor2j/audit/dontesek (5).json`, sha256 fd1217a2…; `kor08/eredmenyek/G1b/audit/osszesito.md`):**
  - 115 / 115 átnézve; egyezik 110; eltér 5 (kétértelmű 3, konstrukció hibás 2), **mind az angol 02. forgatókönyv
    (a termékbemutató nap ebédje) (b)-itemje**; az (a) mind a 28 egyezik (M). A 06 D14 2%-os kapuja a D7-nek nem része.
  - **Az eredet tényei:** a 115 vak választás egy időbélyegen (22:47:47), a rekordformátum a zárolás előtti lapé (a
    zip 22:45-ös); a régi lap forrásában a gold, az állapot és a tények nyíltan álltak. Hogy a választás vak volt-e,
    ebből nem ellenőrizhető; Dani dönt, D7-ként fogadja-e.
  - **A tartalom (a szövegek elolvasása alapján):** az angol jel2 („only the organisers from our own staff attended”)
    úgy is olvasható, hogy senki más nem volt jelen; a generált szövegek két itemben a saját munkatársak étkezését
    írják (a vendéglátás gold nem áll), kettőben az ebéd nem szerepel (a költség jogcíme nem derül ki), egyben
    ellentmondásos. A magyar 02 egyértelmű. A 18:40-es vak ellenőrzések a terv mondatait nézték, nem a generált
    szövegeket: ezt a hibát nem láthatták.
  - **A megbízható arány (a jelzett 5 nélkül):** (b) rossz opció 7 / 82 = 8,5% (Wilson 4–17%; minden (b): 8 / 87); a
    jelzett 5-ből az alany 1-en választott rossz opciót. (a) Y 0 / 28. Fejlesztési szám; a tervezési becslés (Dani
    22:55: ~450–500 eldönthető eset → ~40–45 rossz választás) ezzel összhangban.
- **11-02 23:13, Dani döntései a D7 audit után:** (1) **a D7 auditot elfogadja; a szabálycsalád tervezési hibaaránya
  8,5%** (7 / 82, a jelzett 5 nélkül). (2) **Az angol 02. forgatókönyv javítva, nem kihagyva**
  (`JAVITAS2["en"][1]`, `d7`): jel2 „the day was held for the buyers of our three largest partner companies, who were the
  guests at the lunch; of our own staff, only the organisers were present”, kulcs2 + „guest” (hogy az (a) ne mondhassa ki
  a vendégkört). Az angol 02-nek csak (b)-terve van (5: a jelzett a016, a027, a028, a031, a084).
  - **K08G1B2K (a K08G1D után, éjszaka):** az auditált kor2j archiválva (`kor2j/arch_d7`, `G1b/kor2j_d7elott.*`); a
    generálás az auditált rekordokat betűre átveszi (114; helyben szárazon ellenőrizve), csak az 5 `d7` terv új (Muse,
    új seed); őr: a nem `d7` itemek bájtra azonosak az auditálttal, különben leáll. Utána lánc (orákulum, v1 blokk),
    kiolvasás (oERT2J), mérés (`g1b_ert08`), és **vak auditlap csak az 5 új itemre** (`kor2j/audit/kor2/atnezo.html`,
    b001…, a javított lappal). A D7 végeredménye: az 1. kör 110 egyező iteme + a 2. kör ítélete az 5 újon.
- **11-03 00:28, a K08G1D eredménye (eredménylap 9.):**
  - **Bank v1:** K3 bank lánchiba 0,5% (14 → 1), döntés 186 / 186; T500 bank helyes 324 (v2: 322); 07 bank 1,5 → 2,3%.
    Hamis kizárás és kötés 0.
  - **Blokkpróba** (K3 diag / T500 helyes; T500 NO_MATCH → SELECT): v0 164 / 409 (23), v1 199 / 400 (32), v2 198 / 366
    (66), v3 179 / 369 (10, de MATCH → MISSING 24 és NO_MATCH → MISSING 31), v4 198 / 402 (27). A v0 újraolvasása
    determinisztikus (164, 409). A v2 megerősíti, hogy a „teljesül” a jelölt helyességének olvasódik; a v3 a „nem
    ellenőrizte” mondatot hiányzó adatnak olvassa; a v4 a v1-gyel gyakorlatilag egyenértékű (T500-on a v1-hez 11 javult
    / 9 romlott). **A blokk választása Dani döntése.**
- **11-03 06:46, a K08G1B2K eredménye (00:52):**
  - Az őr rendben: a 110 nem `d7` item bájtra azonos az auditálttal; az 5 angol 02-item új. A lánc utáni bemenet
    (`orakulum_ERT2J/items`) 5 / 115 itemen tér el, csak a `d7`-eken.
  - **Az 5 új item vak auditlapja:** `kor08/adat/ertelmezes/kor2j/audit/kor2/atnezo.html` (b001…, sig 5-b99c2faa1d,
    szivárgás-ellenőrzés rendben). A kor2j mérését (`G1b/kor2j.md`) Dani auditja után közlöm, mert az új itemekre
    modellválaszt tartalmaz.
  - **Hiba a futtatóban:** a régi `kor2j.{md,json}` mentése (`kor2j_d7elott.*`) a root tulajdonú G1b-mappába a host-oldali
    `cp`-vel némán elbukott (nem volt rajta `|| fail`), a mérés felülírta: a régi itemszintű JSON elveszett, a md szövege a
    K08G1B2J naplójából visszaállítva (`G1b/kor2j_d7elott.md`). A futtató javítva (konténeres másolás, hibára leáll). A
    7 / 82 és a vele kapott leletek a régi JSON-ból a 23:04-es bejegyzés előtt készültek, azok nem érintettek.
  - **A kiolvasás futásonként nem teljesen determinisztikus:** a magyar 12. forgatókönyv egy (b)-iteme bájtra azonos
    bemeneten rosszról helyesre billent (K08G1B2J → K08G1B2K). A kiolvasás itemenként fut (köteg = 1), tehát nem a köteg
    összetétele: a GPU-számítás futásonkénti eltérése egy határeseten. A v0 újraolvasásai darabszámra egyeztek (164,
    409), itemszinten ez nem ellenőrzött; a kis különbségek (pl. a blokkpróbában a v4 és a v1 közti 11 / 9) ehhez a
    zajhoz mérendők.
- **11-03 07:10, Dani:** (1) a 2. kör 5 itemje (b001–b005) egyértelmű, a válaszok (B, C, F, C, B) a beépített kulccsal
  egyeznek → **a D7 audit lezárva: a `kor2j` mind a 115 itemje auditált és a címkéjével egyező**
  (`G1b/audit/kor2/osszesito.md`; a lapról nincs export, a forrás Dani üzenete). (2) A determinizmus-próba indulhat.
  - **A `kor2j` mérése** (K08G1B2K, `G1b/kor2j.md`): (b) rossz opció **6 / 87 = 6,9%** (Wilson 3–14%), mind a csali;
    (a) Y 0 / 28; K1(b) AUROC 0,79 (81 / 6), K1(a) 0,64. Az előző futáshoz (8 / 87; a jelzett 5 nélkül 7 / 82) képest az
    angol 02 1 → 0 (új szövegek) és a magyar 12 1 → 0 (azonos bemenet).
- **11-03 12:20, a K08G1DET eredménye (07:14–07:38; `G1/determinizmus.md`, `G1b/det/kor2j.md`):** a szabálycsalád T500 v1
  és az ERT2J kiolvasása újra, külön cache-be; az itemfájlok sha256-ja a futás előtt és után azonos, a régi kiolvasásnál
  régebbiek.
  - **T500 (o06): bitre azonos.** 2000 / 2000 sor, minden címke-logprob pontosan egyezik (régi: K08G1A3, 11-02 19:51).
    Helyes 400 / 400; a v4 ↔ v1 11 javult / 9 romlott az új v1-gyel is. **A blokkpróba 11 / 9-e tehát nem kiolvasási zaj,
    hanem a két blokk valódi, itemszintű különbsége** (20 item, nettó +2; előjelpróbán nem különböztethető meg).
  - **ERT2J (oERT2J): nem bitre azonos.** 0 / 460 sor egyezik; a soronkénti legnagyobb logprob-eltérés mediánja 0,44,
    maximuma 1,82 nat, torzítás nélkül (az átlagos eltérés címkecsoportonként ≈ 0). A pred 8 soron, a döntés 2 itemen
    tér el (két (a)-item: rossz opció → másik rossz opció), a helyesség egyiken sem. (b) 6 / 87 mindkét kiolvasással;
    K1(b) AUROC 0,79 → 0,81, K1(a) 0,64 → 0,63.
  - **Értelmezés (feltevés, nem igazolt):** a kiolvasás maga determinisztikus lehet (a T500 két külön folyamatban bitre
    azonos). Mindkét ERT-kiolvasás (K08G1B2J 20:56, K08G1B2K 00:40) közvetlenül egy Muse-vLLM leállítása után indult (a
    memória mélypontja 3 GB, a sebesség 1,54 item/s, most 2,60); a mai, vLLM nélküli folyamat ettől eltér. Lehetséges ok:
    a memóriahelyzettől függő kernel- vagy munkaterület-választás. A magyar 12-es billenés (K08G1B2J → K08G1B2K) is két
    ilyen folyamat között történt. Nem ellenőriztem.
- **11-03 13:05, Dani döntései:** (1) **a szabálycsalád blokkja v4** (pontonként: „összeghatár teljesül; a költségnem
  nincs ellenőrizve”); (2) **a szabálycsalád tervezési hibaaránya 6,9%** (6 / 87, a teljesen auditált `kor2j`; a 23:13-as
  8,5% helyett): a K1(b)-hez 40–45 rossz választás kb. **580–650 eldönthető szabályesetet** kíván (a végső méret a sablon-
  csoportokkal a G1 végi előregisztrációban, D12); (3) **determinizmus-őr minden kiolvasásra**.
  - **Az őr** (`det_or08.py`, `lib08.sh`): a referencia `kor08/adat/G1/det_ref` (rögzített; 50 szabálycsaládi T500-item,
    állapotonként 12 a sha256(id) sorrendjében + a 2 leghosszabb prompt, 25 hu / 25 en, 167–636 token; a sorok a
    K08G1DET bitre azonosnak mért `o06`-kiolvasásából, v1 blokk; items sha256 997a6e92…, sorok d39906eb…). A kiolvasás
    első és utolsó feladata (`det0`, `det1`, kanonikus mód, ~50 sor); utána `det_ellenoriz`: minden sor bemenete és
    minden címke-logprobja bitre egyezzen. Eltéréskor `JELZES-DET-<fázis>` a gép gyökerében, a futás megy tovább.
    Önteszt (13:19): a két régi `o06`-kiolvasás 50 / 50 bitre azonos; az `o06v4` (más bemenet) jelez (22 eltérő
    bemenet, kilépés 3); a hiányzó kimenet jelez.
  - **K08G1E (13:21-től, `k08g1e.sh`):** a v1 blokk állapota archiválva (`G1/arch_blokkv1`, `cache/k08/jellemzok_blokkv1`,
    `*_blokkv1.{md,json}`; a v1 T500-kiolvasás `o06v1` néven marad a blokkpróbához, `g1_blokk08b` átállítva); a
    szabálycsalád lánca v4-gyel (06, 07, K3 diag mindkét úton; ERT2J); kiolvasás (T500, K3 diag mindkét úton, ERT2J) az
    őrrel; lánc-pontosság, döntések, a 2. kör mérése, a blokkpróba újra (változatlan kell legyen).
- **11-03 14:25, a K08G1E eredménye (13:21–14:13; eredménylap 11.):**
  - **Determinizmus-őr: bitre azonos** a kiolvasás elején és végén (det0, det1: 50 / 50). Az új orákulum-úti v4
    T500- és K3-kiolvasás a blokkpróba v4-ével (K08G1D, 11-02 23:49) is bitre azonos (2000 / 2000, 796 / 796 sor); az
    itemek bájtra azonosak voltak. A blokkpróba újraszámolva változatlan (`blokk_proba2.md`); a lánc-pontosság
    változatlan (a blokk a láncot nem érinti).
  - **Döntések, szabálycsalád (v1 → v4):** T500 kinyert 399 → 400, orákulum 400 → 402; NO_MATCH → SELECT 31 / 32 → 27 / 27;
    új hiba MATCH → NONE 1 (mindkét úton). K3 diag: orákulum 199 → 198, valós kinyerés 198 → 197 (MATCH → NONE 1).
  - **A javított 2. kör v4-gyel:** (b) rossz opció **6 / 87 = 6,9%** (változatlan; hu 3 / 44, en 3 / 43; más itemeken:
    hu 07 1 → 3, en 11 0 → 1, en 10 1 → 0, en 12 2 → 1, hu 02 1 → 0); (a) Y 0 / 28, SELECT gold / csali 5 / 23.
    K1(b) AUROC 0,79 → 0,95 (gold / rossz medián q 0,81 / 0,49; csak 6 rossz választáson, nagyon bizonytalan), K1(a)
    0,64 → 0,61.
- **11-03 15:30, Dani: erőbecslés ágankénti bontásban, utána a G1 többi része láncban.**
  - **Erőbecslés** (`ero08.py`): szimuláció, mert a fej még nincs. Sabloncsoportok (40; érzékenység 30, 60), a (b) hibája
    csoportonként béta-binomiális (ICC 0,05), binormális pontszám két karra közös csoporthatással (τ² 0,2) és ρ
    korrelációval (0,3; 0,6), a hatás ΔAUROC 0 / 0,05 / 0,10. 95%-os intervallum a klaszterezett AUROC-varianciával
    (Obuchowski 1997), ellenőrzésként egy helyzet klaszteres bootstrappal. Olvasat a 6. pont tábláival. K1(b): a
    szabálycsalád (b) 450–800 itemmel, 6,9% hibával, az L-S AUROC rácson (0,70 / 0,80 / 0,90: a pilot 6 hibán áll);
    K1(a): családonként, az L-S AUROC a pilotból (bank 0,94, hiba 0,97, szabály 0,61). Feltevés, nem mérés: ρ, τ², ICC
    és a hatás. Az előzetes (100 szimulációs) próba: a K1(b)-n 580–650 (b)-itemmel valódi 0,05-ös javulásnál a fő pár
    kb. 50–60%-ban „nem eldönthető”; 0,10-nél 85–98%-ban kimutatható. A bankon és a hibán a K1(a)-n a plafon szab határt.
  - **Szabályalapú kinyerő** (`szabkin08.py`, D1, leíró): reguláris kifejezések és a lánc számfelismerője; csak a tétel
    szövegét látja (a hibán a szabályok mérésneveit is). **Egy hibajavító kör a megismert adaton** (az „áfá” toldalékos
    alak, az egybetűs számlaszám-előtag, a cégnév elé csúszó szavak és a számlatulajdonos, a szabálynév nélküli mérés);
    utána nem hangoltam. Összevetés az alany kinyerésével a láncon, itemszinten (`g1_kin_szab08.py`).
  - **K08G1F** (`k08g1f.sh`, 15:32): csak CPU, néhány perc. Nem várja meg más konténer leállását (a spark-deven fut a
    `vllm-qwen38-flash-next-uncensored`, nem az enyém, nem nyúltam hozzá), csak azt, hogy ne fusson fázis, ne töltsön
    be modellt konténer, és legyen ≥ 15 GB elérhető memória (indulásnál 16 GB).
- **11-03 16:30, a K08G1F eredménye (15:32–15:34; eredménylap 12.):**
  - **Erőbecslés, K1(b) szabálycsalád (fő):** 580–650 (b)-itemmel (40–45 várt hiba), L-S AUROC 0,80, ρ 0,6 mellett valódi
    Δ = 0,05-nél az alsó határ 42–46%-ban kerül 0 fölé, az olvasat 50–53%-ban „nem eldönthető”; Δ = 0,10-nél 95–97%.
    ρ 0,3-nál gyengébb (Δ 0,05: 29–31%), L-S 0,90-nél erősebb (75–77%). Az álpozitív arány 3–4% (névleges 2,5%). A
    klaszteres bootstrap az analitikus intervallummal egyezik (40% / 40%, félszélesség 0,059 / 0,058). **A 6. pont
    jelzése:** a tervezett mérettel a fő pár egy 0,05-ös valódi javulásnál nagyobb eséllyel „nem eldönthető”, mint
    kimutatott; 80%-hoz (L-S 0,80, ρ 0,6) kb. 1550 (b)-item kellene (kb. 107 hiba; ρ 0,3-nál kb. 2500). **A méretről Dani
    dönt.**
  - **K1(a):** a szabálycsaládon (L-S 0,61) 193–216 (a)-itemmel Δ 0,05-nél 52–78% (ρ szerint). A bankon (L-S 0,94) és a
    hibán (0,97) a plafon miatt az „érdemben javít” (pontbecslés ≥ 0,05) szinte elérhetetlen: a hibán a lehetséges
    javulás legfeljebb 0,03, a bankon 0,05–0,06. Ott a pár 0,05-ös küszöbe nem működő olvasat; erről is Dani dönt.
  - **A szabályalapú kinyerő** (`kinyero_osszevetes.md`; döntést befolyásoló hiba az átengedetteken, alany / szabály):
    bank 2,5 / 1,9% (06), 2,3 / 1,9% (07), de a szabályalapú **hamis kizárást** is ad (2, 5; az alany 0); hiba 1,2 / 1,3%
    (06), 1,5 / 4,3% (07); szabály 1,9 / 0,0% (06), 2,8 / 0,0% (07), és az alany 15 / 10 tételt emberhez küld (a
    szabályalapú 0-t); K3 diag mindenütt 0,5–1,1%. **A két kinyerő hibái alig fednek át** (bank 06: 50 és 37 hibából 2
    közös; hiba 07: 23 és 64-ből 7). Fejlesztési számok, a szabályalapú kinyerő egy javító köre ezen az adaton készült.
- **11-03 16:40, Dani döntései az erőbecslés után:** (1) **a szabálycsalád értelmezési mintája kb. 1600 (b)-item** (3 : 1
  mellett kb. 533 (a)); (2) **a bank és a hibaelhárítás K1(a)-ja leíró vizsgálat** (a plafon miatt; a K1(b) ott 11-02
  óta leíró). A fő vizsgálat így a szabálycsalád K1(b)-je és K1(a)-ja.
  - **Az erőbecslés a választott mérettel** (`ero08.md`, újrafuttatva a 1200 / 1600-as ráccsal, 16:45): 1600 (b)-itemmel
    kb. 110 hiba; valódi Δ = 0,05-nél P(alsó határ > 0) L-S 0,80 és ρ 0,6 mellett 81% (klaszteres bootstrappal 84%), ρ
    0,3-nál 59%, L-S 0,70-nél 66%, L-S 0,90-nél 93–98%; Δ 0,10-nél 96–100%. A szabálycsalád K1(a)-ja 533 (a)-itemmel
    Δ 0,05-nél 90–99%. Az álpozitív arány 3–4%.
- **11-03 17:00, az előzetes rögzítés tervezete (D12):** `kor08/G1-rogzites.md` v0.1. Kérdések és fő vizsgálatok
  (Dani 11-02 / 11-03), karok, a lánc (séma bank v1 / hiba v1 / szabály v2, blokk v4, kizárás és kötés, ellenőrzési
  feltételek), G2-adat és méretek (szabály 1600 (b) + 533 (a)), értelmezési diagnózis, végpontok, statisztika és olvasat,
  erő, végrehajtási szabályok (pecsét, determinizmus-őr), az elemzők listája és a hash-tábla. **Nem rögzítés:** a G5
  elemzői (`g5_k1_08`, `g5_k2_08`, `g5_k3_08`) még nincsenek megírva, és hat nyitott kérdés Danira vár (a bank és a hiba
  mintamérete, a szabálycsalád sabloncsoportjai, a tanítóminta (b)-hibái, az őr jelzésének kezelése, a két kinyerő
  keresztellenőrzése, a ρ becslése). Javítás: a `kinyero_osszevetes.md` hibaarányának nevezője az átengedett tételek
  száma (mint a `g1_lanc08`-ban); a 07 szabálycsalád alanyi értéke 2,7% helyett 2,8%.
- **11-03 17:10, Dani a D12-tervezetre (v0.1):** jó irány, közel a rögzíthetőhöz. A hat kérdésre: (1) bank és hiba
  200 (b) + 65 (a) marad, leíró, a bizonytalanság közlésével; (2) ≥ 40 sabloncsoport, világos csoportdefinícióval (egy
  alapeset átfogalmazásai és (a)/(b) változatai együtt); (3) **a szabálycsalád tanítómintája kb. 1500 (b) + 500 (a)**
  (a D8 szabálya az (a)-val könnyen teljesül, a K1(b)-hez kb. 100 rossz (b)-választás kell; fix példaszám), a többi
  család a tervezett méretén; az L-RN és az L-LRN ugyanazokat a példákat kapja, a súlyozás a rögzítésbe kerül; (4) az őr
  jelzésénél egy előre rögzített ismétlés, második jelzésnél leállás, hibakeresés a referenciaszeleten, a teszt
  felnyitása nélkül; (5) a két kinyerő keresztellenőrzése külön, előre rögzített leíró K3-összevetés, a fő lánc nem
  változik; (6) ρ a 07 F5-ből, a 0,3 / 0,6 érzékenység mellett. **Négy pontosítás:** (a) a két fő L-RN − L-S AUROC-próba
  Holm-korrekcióval, minden más másodlagos, az erő a döntési szabállyal; a SELECT-AURC-ra nincs +0,05-ös küszöb; a
  pontszám iránya explicit; (b) hiányzó adatból nem következhet kizárás (a bank „deviza ellentmond, és nincs árfolyam”
  szabálya, az elvetett mezők hallgatólagos alapértéke); a kód és a modell döntései és a küszöb hatóköre pontosan, a
  „lánc X-ei” tisztázva; (c) az audit minden szabályforgatókönyvet és nyelvi változatot fedjen le, a címkehiba kezelése
  előre rögzített, modelltől független; (d) pontos darabszámok 1 (a) + 3 (b) csoportszerkezettel, a K3 bootstrapjában a τ
  csak az újramintázott CAL-on, a tanítási recept, a promptok, a sémák, a blokk szövege és a modellrevíziók a
  konfigurációban, a keresztellenőrzésnél az elveszített helyes lezárások is. Utána a G1 zárható, a G2 indulhat; újabb
  nehezítési kör nincs.
  - **A lánc kódja (b) szerint** (`lanc08.lanc`): a szabálycsaládon és a hibán már nem zárt ki hiányzó adatból (ismeretlen
    vagy eltérő pénznem árfolyam nélkül, hiányzó nettó, át nem váltható mérés: lehetséges marad). **A bankon igen:** a
    tétel pénznemét a nyelvből vette (hu → HUF, en → EUR), és ezt az „Ellenőrzött adatok” blokkban ellenőrzöttként mutatta;
    a „Részletek:” és a „Tétel részletei:” fejléc részfizetés-jelnek számított; és részfizetés-jel mellett összeg-
    ellenőrzés nélkül is kötött. A runbook „deviza ellentmond, és nincs árfolyam” kizárását a kód nem valósította meg.
    **Javítva:** a pénznem az igazolt deviza vagy az érték melletti önálló pénznemjelölő (`lanc08.penznem`, szóhatárral);
    nélküle nincs összegalapú kizárás és kötés; a kötéshez azonos pénznem és tűrésen belüli összeg kell; a fejléc nem
    részfizetés-jel. Hatás a megismert adaton (orákulum-út): 06 bank 792 → 786 kötés, 56 tételen több kizárás, 12 tételen a
    pénznem hiányában nincs kizárás; 07 bank 583 → 581; K3 diag változatlan; hamis kizárás és kötés 0 előtte és utána; a
    hiba és a szabálycsalád tételenként változatlan; a valós kinyerés útján 06: 73, 07: 10 tétel tér el. A G0 önteszt
    csak a várt banki számokban tér el.
  - **K08G1G (17:09-től, `k08g1g.sh`):** a 11-03 előtti bank-lánc archiválva (`G1/arch_bankdeviza_elott`, `*_bankdeviza_elott`,
    `cache/k08/jellemzok_bankdeviza_elott`); a bank lánca újra (06, 07, K3 diag mindkét úton), a lánc pontossága, a
    szabályalapú kinyerő összevetése, a bank T500-kiolvasása mindkét úton az őrrel, a döntések.
  - **ρ a 07 F5-ből** (B1-4S ↔ B1-4R seed-átlag, Spearman, normális közelítés, SELECT-eken, osztályon belül; TESZT /
    CAL): szabálycsalád helyes 0,29 / 0,30, hibás 0,46 / 0,45; bank 0,49 / 0,49 és 0,64 / 0,66; hiba 0,32 / 0,42 és
    0,24 / 0,25. Az `ero08` kiegészítve: a két fő próba együtt, közös negatívokkal, 1 (a) + 3 (b) egységekkel, egységen
    belüli hibakorrelációval (ICC_e 0 / 0,3), osztályonkénti ρ-val, Holm-mal.
  - **A tervezet v0.2** (`kor08/G1-rogzites.md`): mindez beépítve; nyitott: a tanítás súlyozása, a bank teljes fizetési
    feltevése, a címkehiba-szabály küszöbe, az audit terhelése. A kód (G5 elemzők, a 08-as fejtanító, a G2 generátora, a
    Gemma-triage) még nincs meg.
- **11-03 20:00, Dani a v0.2 négy és a v0.3 két nyitott kérdésére; K08G1G–J.**
  - **Dani döntései:**
    - **A tanítás súlyozása:** forrásonként 50–50% össz-súly (a láncos T500 és az értelmezési tanítóminta), forráson belül
      egyforma, a ténylegesen tanítható döntések számával; az L-RN és az L-LRN ugyanazokkal a példákkal és súlyokkal;
      a kalibráció a CAL-on. Tervezési kompromisszum, a fő futásban egy változat.
    - **A bank teljes fizetési feltevése:** csak a szintetikus feladatban, kimondott feladatszabállyal. Ha nincs
      részfizetésre utalás, a szabály alkalmazható; ha van utalás, de nincs arány, az hiányos kinyerés. A 08B-n nem
      érvényes. **A szabály mondata minden szintetikus banki bemenetbe** (a T500, a tanítóminta, a CAL, a TESZT és a
      lánc nélküli összehasonlító bemenetek is); a T500-reprezentációk újra; az L-R07-nél dokumentált bemeneti változás.
    - **A címkehiba:** két független hibás alapeset egy forgatókönyv–nyelv cellában felülvizsgálati küszöb, nem
      automatikus kizárás; a konstrukciós hiba egy esetből is felülvizsgálat; egy egység közös hibája egy hiba; a cella
      nyelvenként külön.
    - **Az audit:** a szabálycsaládon minden forgatókönyv mindkét nyelven, teljes egységgel (80 alapeset, 320 item;
      közös megjelenítés, változatonkénti ítélet); a bankon és a hibán forgatókönyvenként egy, előre kiegyensúlyozott
      nyelv, a másik nyelvből véletlen ellenőrzés; a jelzettek mindkét nyelven; a minták átfedhetnek, a címkehibaarány
      csak a véletlen mintából.
  - **K08G1G (17:33):** a bank pénznem-javítása lefutott; **a determinizmus-őr jelzett** (a referenciaszelet mind az 50
    sora eltért, medián 0,47 nat, 4 döntés megfordult; a det0 és a det1 egymással bitre azonos; előtte Dani vLLM-je
    futott a gépen, mint az ERT2J-eltérésnél). A kép, a modell, a driver, a kód és a bemenet változatlan.
  - **K08G1H (18:45):** az előre rögzített ismétlés **bitre azonos**; a végleges erő (2000 szimuláció, Holm, 07 ρ,
    L-S 0,80): mindkét ágon Δ 0,05 → K1(b) 69%, K1(a) 92%; álpozitív 2–3%. A K08G1G kiolvasása archiválva
    (`*_detjelzes_k08g1g`; a bankon 3 / 302 döntést fordított volna).
  - **K08G1I (19:20):** a bank feladatszabálya (`lanc08.bank_kerdes`) a T500 és a K3 diag bankján; a lánc döntései bitre
    változatlanok; az őr bitre azonos; T500 bank helyes 125 → 123.
  - **A rögzítés kódja:** `b1rel08` (`pontoz`: a 07 alakja, az üres listát is kezeli; `tanit`: a 08-as fejtanító,
    súlyozott 05-ciklussal, sabloncsoportos foldokkal), `g5_k1_08`, `g5_k2_08`, `g5_k3_08`. A kód négy részletet rögzít,
    a tervezetben kimondva: a τ csak a modell lezárható döntésein (a kötések utána adódnak); a láncos T500 a tanításban
    orákulum-útról; a lánc két jellemzője a logisztikus karokban; üres listán a `log k` tag 0.
  - **K08G1J (19:54-től):** A szakasz kész (a `g5_k1_08` önellenőrzése a `g1b_ert08` hat számával bitre egyezik; a
    `g5_k2_08` a G1 K3 diag-számait adja); a 06 CAL / TESZT kiolvasása a lánc után (22:04-ig), utána a `g5_k3_08` próbája.
    **K08G1K** utána: a fejtanító próbája (a tanítóminta helyén a G1b 1. köre; csak kódpróba).
  - **A tervezet v0.3:** nyitott kérdés nincs; a rögzítésből a G2 generátora (a szabálycsaládon 90 új, kétnyelvű
    forgatókönyv kell: 40 teszt + 50 tanító; most 12 van), a Gemma-triage és az audit mintavevője és lapja hiányzik.
- **11-03 21:30, a G2 / G3 / G5 kódja; Dani forgatókönyv-átnézése.**
  - **Megírva, CPU-n kipróbálva:** `forgatokonyv08_szab` (90 friss, kétnyelvű szabályforgatókönyv: 40 teszt, 50
    tanító), `szint08` (a G2 generátora; a tervezési próba pontosan az 5.3 darabszámait adja), `gemma08`, `audit08g2`
    (egységenkénti lap, változatonként zárolt vak választás; a próbalapon a szivárgás-ellenőrzés tiszta), `pecset08`,
    `kiolvas08` G2-forrásai a pecsétkapuval, a `k08g2` / `k08g3` / `k08g5` futtatók, `rogzit08` (a D12 manifestje és a
    G5 nyitása, csak Dani jóváhagyására). A runbook nem rögzül (élő napló), a tervezet igen.
  - **Dani átnézése (külső asszisztensi véleményezéssel, `kor08/adat/G2/G2_forgatokonyvek_ertekeles.md`):** 64 rendben,
    26 javítandó, 0 kihagyandó. A 26 csereszöveg beépítve (a prompt alakjára igazítva; F19 támasza „ajándék”), a
    kulcsszavak újraillesztve (a régiek közül több a helyzetbe került vagy kiesett a jelből); a lap újragenerálva
    „javítva” jelöléssel. A tanulságok a modul fejlécében és a tervezet 5.3-ában; a hatókör-mondat (ugyanaz a 20 pár a
    tesztben és a tanításban) az 5.3-ban.
  - **Nyitott (tervezet 13.):** a 26 javított szöveg ítélete; a szó szerinti költségnem-szó a jelben (a G2 jeleinek
    38–50%-a, a G1b-ének 25%-a) — javaslat: marad, a K1(b) mellett leíró bontással.
- **11-03 21:45, éjszakai sor a spark-deven (laptoptól független):** K08G1J (a 06 CAL / TESZT kiolvasása, utána a K3
  pilot, ~22:10) → K08G1K (a fejtanító próbája, ~22:40) → **K08G1L** (Dani 21:40-es engedélyével: a G2 90
  szabályforgatókönyvének eldobható Muse + Gemma próbája, `proba08g2`, saját seeddel és gyökérrel
  (`kor08/adat/G1/proba_g2`), forgatókönyvenként és nyelvenként 1 egység, 720 item; nem G2-adat, nem auditáljuk;
  a próba tervei a valódi G2-éitől sablonban és összegben is mind eltérnek). Kimenet: `kor08/eredmenyek/G1/proba_g2/
  osszesites.md` (a tényellenőrző és a Gemma forgatókönyvenként, a (b) a jel fajtája szerint). Várható vége ~00:30.
- **11-04 reggel, az éjszakai sor eredménye** (K08G1J 21:50, K08G1K 21:53, K08G1L 22:38; mind kész, az őr bitre azonos).
  - **K3 pilot (a 06 CAL / TESZT, fejlesztési szám):** a szabálycsaládon és a hibán minden láncos karnak van
    munkapontja (szabály L-R07 72,0% / 3,0%, L-S 56,1% / 2,1%). **A bankon a láncos karoknak (L-R07, L-S) a
    replikák 100%-ában nincs munkapontjuk** a rögzített τ-szabállyal (csak a modell lezárható döntésein, CP ≥ 0,95,
    ≥ 200 elfogadott): a lezárás csak a lánc kötése (35,8%, 0 hiba); a B1-4R lánc nélkül 65,5% / 2,6%. A rendszer-τ
    változatban a modell is zár (L-R07 10,1%, L-S 3,3%), de 4,9% / 9,1% hibával.
  - **Fejtanító próba:** a kód végigfut (minden kar, három seed, Holm, bontások); a számok nem értelmezhetők.
  - **Forgatókönyv-próba (720 item):** a teljes egység hu 100%, en 86–88%. **Az angol (a) a 18 képzés-goldú
    forgatókönyvből 12-n elbukik** („(a): a jel kulcsszava”, a `kulcs` angolul „course” / „exam”; a G1b-ben ugyanez
    2 egységgel). A (b) a `kulcs2`-n 100%-ban átmegy (4 elbukott próbálkozás, mind pótolva). A Gemma a (b)-n 97%-ban
    egyezik (a szó szerinti jelen 99%, az áttételesen 96%); rendszeres eltérés F12 hu, F83, F85 hu (a csali felé). Az
    (a)-n a Gemma 67%-ban a csalit, 24%-ban a goldot, 8%-ban egyiket sem választja: a Gemma kerete az (a) Y-címkéjét
    nem tudja kifejezni, ezért **a jelzett auditminta a mostani kóddal szinte minden egységet tartalmazna.**
- **11-04 09:00, Dani („rendben”) a reggeli javaslatokra; K08G1M.**
  - **Döntések:** a bank K3 τ-szabálya marad, a várható kimenet a tervezet 7. pontjában; a jelzett auditminta csak a (b)
    Gemma-eltéréséből (`audit08g2`; a próbán 75 egységből 3, a régi szabállyal ~mind), az (a)-választás leíró
    (`gemma08`); a K1 jelfajta szerinti leíró bontása (`forgatokonyv08_szab.jel_fajta`, `g5_k1_08`; a G1b pilotján a fő
    számok bitre a régiek).
  - **K08G1M (08:36–08:52, Muse):** az angol képzés-gold (a) 18 tervén 5-5 szöveg. **Az ok a generált e-mail-címek
    `pelda.example` domainje** (az „exam” részszó; a „course” csak egyszer, „in the course of business”). Javítva: a
    képzés angol `kulcs`-a „exam ” / „exam.” / „exam,” / „exams” / „examination”, az F14 angol `kulcs2`-je „third
    module” / „our own buyers” (az „exam”-mel a (b) jel nélkül is átment volna); az `ellenoriz` őrzi a sablonszöveget.
    Offline: a diagnózis 90 (a)-szövegén 22 helyett 76 megy át; a próba 708 átment szövege mind átmegy. A maradék
    kiesés főleg „rossz nyelv”: a 06 `lang_ok` a rövid angol szöveget magyar ékezetes névvel magyarnak veszi (a
    próbában pótlással kezelve, a 06 kódja nem változik).
  - **Nyitott:** a 26 javított forgatókönyv ítélete; utána a rögzítés.
- **11-04, a forgatókönyvek 2. köre (Dani):** a 26 javítottból 25 rendben, az F41 (b) jele kiegészítve („…és ennek a
  fuvarnak a díját kérem megtéríteni”; angolul a fordítása, Dani megerősítésére); mind a 90 elfogadva. Nyitott: a v0.3
  rögzítésének jóváhagyása, utána a `FORGATOKONYV-JOVAHAGYVA` és a K08G2 (GPU, külön engedéllyel).
- **11-04, a rögzítés előkészítése:** a `rogzit08.FAJLOK`-ból 21 közvetett függőség hiányzott (pl. `kiolvaso03`,
  `lib07.sh`, a 05–06 segédmoduljai) és a Gemma temperature-forrása; pótolva, és a `rogzit` a függőségek zárt halmazát
  ellenőrzi (rögzítetlen függőséggel nem fut). Új: a G3 tanítás G1-es bemenetei fájlonként (`ADATOK`). A spark-deven
  próbaszámolva: 65 fájl, 23 adatfájl, rögzítetlen függőség nincs; a D12 még nincs rögzítve.
- **11-04 10:16, a D12 rögzítve; a G2 indul (Dani: „1. jóváhagyom, 2. ok, 3. G2 indulhat”).**
  - Előtte: a `k08g2` kapuja technikai megszakadás után folytatható (csak a kész G2, `DONE-K08G2` tiltja az újraindítást;
    a katalógus, a terv, a `gen` és a Gemma-kiolvasó a kész részt kihagyja); a tervezet állapotsora „v0.3, Dani
    jóváhagyta”. A helyi és a spark-deves hash-ek egyeztek.
  - **`kor08/rogzites/D12/manifest.json`** (10:16:55; sha256 4a058dab…): 65 fájl, 23 adatfájl, a modellrevíziók, a vLLM
    image digestje; a `rogzit08 ellenoriz` zöld. A `lora-train:2` image-azonosítója a manifestben üres (helyben épített
    image, nincs RepoDigest) → `kor08/rogzites/D12/kepek_kiegeszites.json` (sha256:9d0da0ae…).
  - **`kor08/adat/G2/FORGATOKONYV-JOVAHAGYVA`** a forgatókönyv-modul és a manifest hash-ével.
  - **K08G2** 10:17-től (Muse: sablonok, tervek, generálás és tényellenőrzés a négy részre, utána Gemma-triage);
    kb. 12 000 generálás, a próba ütemével (~36 / perc) várható vége ~17:30.
  - **Innentől a rögzített fájlok nem változhatnak** (a `sync.sh to08` csak azonos tartalmat vihet fel; javítás csak
    burkolással).
- **11-04 16:12, a K08G2 kész** (Muse 10:17–15:29, Gemma 15:30–16:12; a determinizmus-, memória- és hibaőr csendes). A
  helyi kódfájlok a manifesttel egyeznek (62/62; a 3 cache-fájl csak a spark-deven).
  - **Itemek:** friss 3 × 1500; k3 bank 90 / 100 terv, hiba 91, szabály 200 / 200; `ert_teszt` egységek bank 66 / 66, hiba
    66 / 66, szabály 553 / 560; `ert_tanito` bank 162 / 165, hiba 90 / 90, szabály 495 / 500. A kiesés a tényellenőrzésé
    (szabályon főleg „rossz nyelv”, néhány hiányzó áttételes jel; bankon más opció partnere a szövegben).
  - **Gemma-triage (`gemma08`, 10 609 item, 0 hibás olvasás):** a (b)-n `ert_teszt` szabály 98,6% (szó szerint 99%,
    áttételes 98%), hiba 96%, bank 88%; `ert_tanito` szabály 95,8% (áttételes 93%). A szabály (b) leggyengébb
    forgatókönyvei: F83 30/42 (most angolul is), F84 39/42, F80 39/42; `ert_tanito`-ban F85 13/30, F12 16/30 (a próba
    mintázata). Az (a)-n a szabálycsaládon csali 389 / gold 130 / egyik sem 33 (leíró). K3 (leíró): bank 97%, hiba 54%,
    szabály 42% (angol 29%) — a kiszámított lépést a Gemma sem követi (a 07 K3-lelete).
  - **Auditlap (`audit08g2 minta` + `html`, sig 6c285aa7bce4):** `kor08/adat/G2/ert_teszt/audit/atnezo.html`, 223 egység,
    730 item (szabály 121 egység / 484 item, bank 52 / 134, hiba 50 / 112; lefedési 146, véletlen 90, jelzett 40
    egység, átfedéssel); szivárgás nincs. **Nyitott:** Dani vak auditja → `dontesek.json` → `osszesit`, `alkalmaz`,
    utána a K08G3.
- **11-04 18:53, Dani vak auditja kész** (730 döntés, 223 egység, a kulcs megnyitása előtt; a 8 eltérésnél az eredeti
  vak választás megőrizve, mellette utólagos indoklás). `audit08g2 osszesit`:
  - **Címkehibaarány (véletlen minta, alapesetenként, 95% Wilson):** szabály 0/30 = 0,0% [0,0%; 11,4%] (a lefedési 80
    alapesetben sincs hiba); bank 2/30 = 6,7% [1,8%; 21,3%]; hiba 3/30 = 10,0% [3,5%; 25,6%].
  - **8 hibás alapeset, mind egyedi megvalósítási hiba egy-egy (b)-ben** (Dani: M vagy K a konstrukció opciója helyett),
    javítható nincs (M-re javítva a (b)-ből épp a döntő jel hiányozna) → 8 egység kimarad: szabály F55 hu, F80 en (b3:
    a döntő jel nem mondja ki a jogcímet); bank `k08:hu:008` mindkét egysége (a közlemény „X felé fennálló tartozást”
    ír, a jóváírás viszont a számlatulajdonoshoz jön); hiba 081 hu, 016 hu, 029 en (a (b)-ből kimaradt a tünet egyik
    feltétele), 085 en (két hibaok egyszerre igazolt). A szabály K1(b)-alapja 1659 → 1653 (b) item (≥ 1600).
  - **Felülvizsgálandó cella:** bank `k08:hu:008` hu (két független hibás alapeset); a teszten a cella 2 egysége épp a
    kizárt kettő, a sablon a tanítóban nincs. A „felé fennálló” fordulat máshol: 1 nem auditált teszt-item (`k08:hu:068`)
    és 3 tanító-item (045, 091, 093). **Nyitott:** Dani döntése a celláról és erről a négy itemről; utána `alkalmaz`
    és a K08G3.
- **11-04 19:00, Dani: „1. egyetértek, 2. javaslat elfogadva, mehet”.** A cella-döntés
  `kor08/adat/G2/ert_teszt/audit/felulvizsgalat.json` (a bank `k08:hu:008` hu kizárva); a „felé fennálló” fordulatú négy
  nem auditált item változatlan, a G2-jelentésben ismert generálási mintázatként. **`audit08g2 alkalmaz` a spark-deven
  (19:00:35):** kimarad bank 8, hiba 16, szabály 8 item (8 egység × 4); marad bank 256, hiba 248, szabály 2204 (ebből
  1653 (b)); az eredeti az `items_audit_elott/` alatt, `ALKALMAZVA.json`.
- **11-04 19:00, a K08G3 első indítása a `pecset08 nyit`-on megállt** (a GPU-munka előtt): a rögzített `k08g3.sh` a
  pecsétet (`cache/k08/pecset`, a konténer root-jáé, 700) a gazdagép python3-jával nyitja, és ugyanígy hívná a pecsét
  alatti determinizmus-őrt (`det_or08 ellenoriz --jell cache/k08/pecset/jellemzok`: jogosultsági hiba → hamis jelzés,
  ismétlés, ~16 óra GPU után leállás) és a `pecset08 lezar`-t. A 07 ugyanezt a konténerben futtatta (`py … pecset07`); a
  G1 pilotjai pecsét nélkül futottak, ezért ez nem jött elő. **Javítás burkolással, a rögzített fájlok változatlanok:**
  `kor08/eszkozok/k08g3_burok.sh` (a rögzítés ellenőrzése, a pecsét kapuja a konténerből, utána a `k08g3.sh` a PATH
  elején a `kor08/eszkozok/burok_g3/python3` shimmel; a végén a pecsét alatti fájlszám a konténerből). A shim csak a
  `pecset08` és a `det_or08` hívást futtatja a konténerben root-ként (a kísérlet a saját abszolút útján is felcsatolva,
  a kimenet a gazdagép felhasználójáé); minden más a valódi `/usr/bin/python3`. Próbák: az átengedés, a `det_or08 ref`,
  az `ellenoriz` a G1 det0/det1-en (bitre azonos, a `--out` a helyén, <user>), a hibaág kilépési kódja (3), a `nyit`
  (root 700, a gazdagépről nem látható, üres). Az első indítás naplói: `logs/k08g3_inditas1`.
- **11-04 19:06, a K08G3 fut a burokkal** (a rögzítés zöld, a pecsét alatti könyvtár üres, az alany fel). A futtató
  becslései szerint ~15,5 óra, várható vége 11-05 ~11:00. A G4 előtt csak darabszám és idő olvasható.
- **11-05 07:50, a K08G3 megállt a pecsét alatti kiolvasáson (10.: az őr az ismétlésen is jelzett).** Kész és hash-elt:
  a kinyerés (19:06–20:14; 9 rész, értelmezhetetlen válasz 0; `logs/k08g3/kinyeres.sha256`) és a lánc (`kor08/adat/G3/`).
  A zárt kiolvasás két teljes kísérlete (20:15–02:04, 02:04–07:50): a referenciaszelet 0 / 50 bitre azonos (5, ill. 4
  pred eltér; max 1,68, ill. 2,28 nat); folyamaton belül a det0 és a det1 bitre azonos. Az 1. kísérlet kimenete a
  `cache/k08/pecset/jellemzok.jelzes`, a 2.-é a `cache/k08/pecset/jellemzok` alatt (pecsét alatt, olvasatlanul).
- **11-05 07:58–08:16, K08G3DIAG (`kor08/eszkozok/k08g3diag.sh`; 10.: csak a referenciaszeleten):** két friss
  folyamat a tiszta gépen (órák óta nincs vLLM), csak a det0-val; a két kísérlet det-sorai a pecsét alól kimásolva (csak
  a det-könyvtárak). **Eredmény (`logs/k08g3diag/osszevetes.md`): a kiolvasás folyamatonként egy kis, diszkrét
  numerikai „mód” egyikébe kerül, azon belül bitre determinisztikus.** Három mód: **R** = a referencia (K08G1DET két
  folyamata, G1E, G1H, G1I, és most p2), **B** (K08G1G, a zárt 2. kísérlet, p1; egymással bitre azonosak), **A** (a
  zárt 1. kísérlet). Módok közt a referenciaszelet 50 sorából egy sem egyezik, 4–5 pred tér el (max 1,3–2,3 nat). A
  vLLM-előzmény nem ok (p1 tiszta gépen is B), a memória sem (mind ~118 GB elérhetővel indult). A mód a folyamat
  indulásakor dől el (feltevés: a betöltés vagy a kernelválasztás; nem ellenőrzött). Az R a rögzített tanítóbemenetek
  (D12 `ADATOK`: `o06_*_T500`, ebből készült a referencia) módja. **Nyitott: Dani döntése a folytatásról (10.).**
- **11-05 08:20, Dani: „1-es legyen”** — a K08G3 folytatása R-módban (`kor08/eszkozok/k08g3c.sh`; eltérés a rögzített
  futtatótól, a 10. pont szerinti döntés). A kész kinyerés (hash-ellenőrzés) és lánc (`logs/k08g3/lanc.sha256`) marad, a
  vLLM nem fut újra. A kiolvasás friss folyamatban indul; amint a det0 kész, a rögzített `det_or08` dönt: nem bitre
  azonos → a folyamat leáll, a részkimenet olvasatlanul félre (a zárté a pecsét alatt, `arch_c_proba<k>`), új folyamat
  (legfeljebb 6); bitre azonos → a kiolvasás végigmegy, a végén a det0 + det1 őr dönt. A mód tehát egyetlen értékelő item
  kiolvasása előtt, csak a referenciaszeleten dől el; a kritérium nem változik. A feladatlisták és a 4–6. lépés parancsai
  szó szerint a `k08g3.sh`-éi (diff). Az éjszakai két kísérlet olvasatlanul a pecsét alatt: `arch_zart1_A`, `arch_zart2_B`
  (a G5 után, Dani külön engedélyével, leíró módérzékenységi próbának használható).
  - **Indulás 08:23** (a rögzítés zöld, a kinyerés hash-e egyezik, a referencia rendben).
  - **Későbbre:** a rögzített `k08g5.sh` a `pecset08 ellenoriz`-t szintén a gazdagép python3-jával hívja → a G5-höz is a
    `burok_g3/python3` shim kell (és ellenőrizni, hogy az elemzők a pecsét alatti utat konténerből olvassák-e).
- **11-05 15:44, a K08G3 kész** (`DONE-K08G3` 15:43:59; a `k08g3c.sh`-val). Mindkét kiolvasás az első próbára R-módba került,
  újraindítás nem kellett:
  - **zárt:** 08:23:47 – 14:08:39, R-mód 08:32:56; a det0 és a det1 bitre azonos (50/50);
  - **nyílt (tanítóminta):** 14:08:39 – 15:41:12, R-mód 14:17:28; a det0 és a det1 bitre azonos (50/50);
  - **fejek:** 15:41:19 – 15:42:46 (`fejek08`, 97 fájl; a G1 pilotja is ~1 perc volt), **pontozás:** 24/24 szelet, 15:43-ig;
  - **pecsét:** 480 fájl, 6,48 GB (R-módú kiolvasás 152, pontozás 24, `arch_zart1_A` 152, `arch_zart2_B` 152), 50/50 feladat
    kész, `kor08/rogzites/pecset/K08G3.json`. A G5 mind a 24 pontozásfájlja megvan a manifestben.
  - A pontozott itemek száma (csak darabszám): az értelmezési teszt (`lG2T`) szabály 2204, bank 256, hiba 248, a lánc
    kimenetével egyezően.
- **11-05 15:48, a G4 kész** (`kor08/eszkozok/k08g4.sh`; nem rögzített, csak CPU, a rögzített futtatók közt nem volt G4-lépés).
  A rögzítés zöld (65 + 23), a pecsét manifestje egyezik (480 fájl, 0 eltérés), a `kinyeres`, `lanc`, `fejek08` hash-listák
  egyeznek, a `lora-train:2` és a vLLM-image a rögzített. Manifest: `kor08/rogzites/pecset/K08G3.g4.json` (sha256 dffea8d8…):
  G2 62, G3 72, tanítóminta-kiolvasás 30, fejek 97 fájl, a nem rögzített eszközök hash-ei és a rögzített futtatótól való
  eltérések. A neve illik a `rogzit08 nyitas` mintájára, így a nyitás ennek a hash-ét is rögzíti. A pecsét alól csak hash jött
  ki. A `k08g5.sh`-hoz kész a `k08g5_burok.sh` (a shimmel; a `pecset08 ellenoriz` hívását a G4 már kipróbálta).
  **Nyitott: Dani G5-engedélye** → `rogzit08 nyitas --jovahagyas "…"`, utána `k08g5_burok.sh`.
- **11-05 16:16, Dani: „igen, nyithatod”** — a G5 nyitva (`kor08/rogzites/G5/NYITAS.json`, 16:16:25; a `K08G3.json` és a
  `K08G3.g4.json` hash-ével). A `k08g5_burok.sh` 16:16:34-kor indult; a rögzítés zöld, a pecsét 480 fájlja nem tért el, a K3 fut.
- **11-05 16:20, a G5 kész** (`DONE-K08G5` 16:20:30; a rögzített elemzők változatlanul, 10 000 replikával;
  `kor08/eredmenyek/G5/{k1,k2,k3,k3_rendszer}`, hash-ek: `logs/k08g5/g5.sha256`). Minden szám szintetikus adaton, az R-módú
  kiolvasáson. Olvasat a D9 szerint:
  - **K1(a), szabály (2. fő próba):** L-RN − L-S 0,186, Holm-intervallum [0,111; 0,269], p < 0,0001 → **javít érdemben**
    (L-RN 0,924, L-S 0,738). Célzott tanítás és a fej is kell: L-R 0,760, L-LRN 0,761.
  - **K1(b), szabály (1. fő próba):** L-RN − L-S 0,036 [-0,047; 0,086], p = 0,338 → **nem eldönthető** (L-RN 0,927, L-S 0,890;
    74 rossz opció / 1567 gold, 4,5% a tervezett 6,9% helyett; a terv L-S 0,80-at feltételezett). Az L-R és az L-R07 itt ront.
  - **K2:** a kinyert úton a helyes arány 97,8 / 98,9 / 97,5% (bank / hiba / szabály; lánc nélkül 44,4 / 59,3 / 28,0%), a cél
    teljesül. A hamis átengedés bank 1,1%, szabály 0%, **hiba 3,3% (3/91) → a ≤ 2%-os cél a hibán nem teljesül.**
  - **K3:** L-RN − L-S hasznos lefedettség: szabály +9,3 pont [7,4; 18,1], hiba +4,7 [0,2; 9,2], bank 0 (a láncos karoknak
    nincs munkapontjuk, ahogy a 7. pont várta; 36,3% a kötésből, 0 hiba). A hibafeltétel az L-RN-nél szabályon és hibán
    bizonytalan (felső határ 5,8%, 7,1%). Az L-R ugyanezt hozza (72,5%, 67,6%), és az L-RN − B1-4R a szabályon -0,0 [-2,9; 4,7].
  - **Leíró:** az (a)-ból τ fölött lezárt arány a szabályon L-RN 43,5%, L-S 43,0%; a hibán 11,3%, illetve 80,6%.
  - **Ellenőrzés (nem rögzített):** az `ert_tanito` a `ert_teszt`, a `friss` és a `k3` szabály-sabloncsoportjaival 0 közös, a
    tanító és a teszt közt 0 azonos szöveg.
- **11-05 20:30, Dani: „mehet mindkettő”** — két utólagos, leíró vizsgálat a G5 után; a rögzített elemzők és a G5 számai nem változtak.
  - **A K2 hamis átengedései** (`kor08/eszkozok/k2_atengedes08.py`, `kor08/eredmenyek/G5_utolagos/k2_atengedes.md`): mind a 4
    (hiba 3, bank 1) kinyerési hiba, az ellenőrzés mindegyikben eldobta a mezőt, a tétel blokk és kizárás nélkül ment a
    modellhez; gold nem esett ki, rossz kötés nincs. A modell 2-t így is eltalált, a másik 2 lánc nélkül is rossz volt. Okok:
    az alany kinyeréskor átváltott (1,2 kOhm → 1200; 2 tétel), rossz számot idézett (800 → 80 mOhm), a százalékot összegnek
    vette. A friss mintán 101 / 4488 eltérés (2,3%), a gold ott sem esett ki; a banki 49-ből 45 elmaradt kötés; a hibán 2 NO_MATCH
    tételnél többet zár ki, mint az orákulum. A szabálycsaládon 38 eldobott mezőből 37-et csak az ékezet nélküli idézés
    buktatott. **Javítási jelölt a következő körre (friss teszttel):** normalizált forrás-összevetés, kóddal számolt
    mértékegység-váltás.
  - **Módérzékenység** (`kor08/eszkozok/k08g5m.sh`, `modszenz08.py`, `kor08/eredmenyek/G5_modszenz/osszevetes.md`; 20:37–20:44,
    a pecsét manifestje előtte és utána egyezik): az A és a B kiolvasás ugyanazokkal a fejekkel és elemzőkkel. A K1(a)
    0,186 / 0,188 / 0,190 (R / A / B), mindig javít érdemben; a K1(b) 0,036 / 0,030 / 0,040, mindig nem eldönthető; a K2 helyes
    aránya azonos; a K3 szabály +9,3 / +9,8 / +10,1, hiba +4,7 / +5,0 / +4,7 pont. A döntések 2,1% / 1,8%-a fordul 8719 itemen, a
    láncos K3-típuson 0. **Módfüggő:** az L-RN lezárási hibája a hibacsaládon 3,6 / 4,1 / 5,5% (B-ben „nem teljesül”), az (a)-ból
    lezárt arány a szabályon 43,5 / 46,6 / 47,9%.
- **11-05, a K1 a teljes rendszeren** (`kor08/eszkozok/g5_k1t_08.py`, `kor08/eredmenyek/G5_utolagos/k1_teljes/`): a G1-rögzítés 6., 7. pontja
  kötelezővé teszi, a rögzített futtató nem írta ki. A `g5_k1_08` változatlanul, a diagnózis szűrője nélkül: K1(a) 0,187 [0,122; 0,259], K1(b) 0,037
  [-0,046; 0,086], az olvasatok nem változnak. A K1(b) 76 rossz opciója a 40 sabloncsoportból 9-ben van (F83 30, F84 17).
- **11-05, az eredménylap kész:** `kor08/eredmenyek/G5/eredmenylap.md` (a táblák 56 számát a gépi JSON-okkal visszaellenőriztem). **Dani: „készítsd el az
  eredménylapot, után meg indulhat a javító kör”.**
- **11-05 21:00, a javító kör (J) eleje.** Tervezet: `kor08/J-rogzites.md` v0.1; burkolók: `lanc08j.py` (J1 ékezet- és kisbetű-érzéketlen forrásrészlet, J2 az átváltott mérés
  visszavezetése a szöveg számára), `szint08j.py`, `j08.py`, `k08j.sh`. Fejlesztési szám a meglévő kinyerésen (`j_replay08.py`, `kor08/eredmenyek/J/replay.md`): a rögzített lánc a G3
  tárolt kimenetét adja; G2K3 hiba 3/91 → 1/91, friss szabály 39 → 2, értelmezési teszt szabály 47 → 1; új eltérés 0, hamis kizárás és kötés 0, a zavarópróba azonos. A K08JP próba
  (12 item / család a G2K3-ból, másolatban) a futtatót nézi, generálás nélkül. **Nyitott: Dani jóváhagyása a rögzítéshez** (`j08 rogzit`), utána a `k08j.sh`.
  - **K08JP próba kész (21:02–21:26):** a `k08j.sh` a generálás nélküli útján végigfutott (kinyerés, három lánc, kiolvasás első próbára R-módban, a det0 és a det1 bitre azonos, pontozás, K2). A próba csak a
    futtatót igazolja, a 36 item nem mérés. A Muse-lépések parancsai a `k08g2.sh`-éi, a `szint08j` sablon és terv a bankon és a szabályon CPU-n kipróbálva (220 terv / család).
- **11-05 22:10, Dani: „igen, indulhat”** — a J rögzítve (`kor08/rogzites/J/manifest.json`, 5 fájl, a D12 hash-ével). A `k08j.sh` 22:1x-kor indult; becsült vége 11-06 ~01:00. Az eredményt Dani reggel nézi.
- **11-06 00:36, a K08J kész** (22:10–00:36; `kor08/eredmenyek/J/k2`, `k2_rogzitett`; a rögzítések zöldek, a kiolvasás első próbára R-módban, a det0 és a det1 bitre azonos). Minta: bank 197, hiba 210, szabály 220 item; 60 / 46 / 60 sabloncsoport, a G2-vel 0 közös.
  **A J szabálya teljesül mindhárom családon:** helyes 100,0 / 98,6 / 100,0% (lánc nélkül 42,6 / 50,0 / 27,3%), hamis átengedés 0/197, 0/210, 1/220 (0,5% [0,0%; 1,4%]), hamis kizárás és kötés nincs. A rögzített lánc ugyanazon a kinyerésen a hibán 5/210 = 2,4%, tehát ott a célt nem érte volna el; a bankon és a szabályon a két lánc azonos (a G5 banki esete itt nem fordult elő, a J arra nem hat). Eldobott mező a hibán 9 → 0.
- **11-06, a K1(a) felszíni jegyek próbája** (`kor08/eszkozok/felszin08.py`, Dani: „igen, indítsd”; utólagos, leíró). **Az olvasat a futás előtt rögzítve** (szabálycsalád, a tanítómintán legjobb szöveges modell teszt-AUROC-ja): ≥ 0,85 a K1(a) nyeresége nagyrészt felszíni jeggyel magyarázható, a fejről szóló állítás ebben a formában nem tartható; 0,70–0,85 részben, csak az egységen és a kvartiliseken belüli nyereség számít; < 0,70 a TF-IDF szintű jegy nem magyarázza (mélyebb konstrukciós jegyet ez nem zár ki).
  - **Eredmény (08:31):** a legjobb szöveges modell a szabálycsaládon 1,000 (szó 0,987), bankon és hibán 1,000; L-RN 0,926 / 0,994 / 0,998. **A rögzített olvasat első sávja: a K1(a) nyeresége felszíni jeggyel magyarázható, az állítás ebben a formában nem tartható.** Ellenőrzés (`felszin08b.py`): a nyers szövegen, normalizálva, nyelvenként is 0,99–1,00, címkekeveréssel 0,47–0,55, tehát nem a próba hibája. Ok: az (a) rövid, a jel nélküli tőmondatos szöveg. A K1(b), a K2 és a J nem érintett. Eredménylap: E függelék. Eldöntő kísérlet: illesztett (a) nem döntő elbeszélő mondattal, befagyasztott fejekkel.
- **11-06 08:54, az illesztett kontroll (M) első fele** (Dani: „kezd a kontrollal”). Az (a) tervei változatlanok, a generátor utasításába a (b) jelének helyére egy nem döntő mondat kerül (`kor08/eszkozok/illeszt08m.py`: szabálycsalád 40 forgatókönyv × 2 nyelv, bank 3 mondatminta, hiba a bejelentés körülményei; `szint08m.py`, `k08ma.sh`). **Az első fél fejet, kiolvasást és modellkimenetet nem érint,** ezért a mondatok az illesztés próbája alapján javíthatók. Elfogadás a generálás előtt rögzítve (`felszin08m.py`, szabálycsalád): hossz ≤ 0,60, a régi szöveges modell ≤ 0,70, friss sabloncsoportos CV ≤ 0,80. A második fél (kinyerés, rögzített lánc, kiolvasás R-módban, pontozás a befagyasztott fejekkel) csak Dani jóváhagyott rögzítése után fut. A (b) itemek és pontszámaik a G3-éi maradnak.
- **11-06, Dani döntése a D10-ről („elfogadom”):** a 08B fő végpontja a **lezárások hibaaránya Dani címkéjéhez mérve, lépcsőnként, cél ≤ 2%** (a K2 hamis átengedésének valódi adatos párja); az új lezárások száma leíró, a 20-as küszöb nem kapu. Indok: a 07B arányával (3 / 262) a 20 új lezárás kb. 1750 tétel, kb. 25 hónap a <tenant>-en. A termék „kötött, címke M” tételei nem számítanak hibának, mert a termék több adatot látott; a végpont a lánc és a modell saját lezárásaira vonatkozik. **Dani: a valódi adatos lánc készülhet a 262-es fejlesztési próbához.** A fej lépcsője a kontroll (M) eredményétől függ.
- **11-06 09:27, az M első fele kész, az illesztés nem érte el a küszöböt** (`kor08/eredmenyek/M/felszin/illesztes.md`; a `felszin08m` első futása kulcshibán állt meg, javítva, a generálás ettől nem változott). Generálás 551 / 64 / 62 item, veszteség nélkül. Szabálycsalád: hossz 0,582 (teljesül), a régi szöveges modell 0,841 (nem), friss sabloncsoportos CV 0,998 (nem); bank és hiba: a régi modell 1,000 / 0,997. A friss modell a nem döntő mondatok témáját ismeri fel. **Javaslat Daninak (`kor08/M-rogzites.md` v0.1, tervezet):** aszimmetrikus olvasat: ha a fej a megmaradt jegyek mellett sem „javít érdemben”, az állítás elvetve és a fej parkol; ha igen, az nem bizonyíték, erősebb kontroll kell. A futtató (`k08m.sh`, `m08.py`) kész, az orákulum-lánc helyben lefut; rögzítés és kiolvasás csak Dani jóváhagyásával.
- **11-06 09:31, K08V indul:** a 08B fejlesztési próbája (`lanc08v.py`, `v08.py`, `k08v.sh`, értékelés helyben: `v08_ertekel.py`, a 07B számait visszaadja). A jelöltlista a pénznemet és az irányt már szűri, ezért a valódi adaton kizárás nincs, a lánc a kötést adja. A G5 szerint a bankon a láncos karoknak nincs τ-ja, ezért a τ a 262-n választódik ki a friss mintához.
- **11-06 10:25, a K08V kész (a 08B fejlesztési próbája; `kor08/eredmenyek/V/v_ertekeles.md`, közvetlen keresés: `kor08/eredmenyek/V/kozvetlen/`).** Az első futás (09:31–09:57, félretéve: `*_elso_teljes_tetelsor`) nem használható: a burkoló a teljes tételsort adta a kinyerőnek, az alany a `Hivatkozás:` mező banki azonosítóját adta vissza, 0 kötés. Javítva (`kinyeres_kozlemenybol`, a runbook 7. szerint). A második futás R-módban, a det0 és a det1 bitre azonos. **Kinyeréssel:** 22 kötés a 255 tételes hatókörben, 0 hibás; a 93 közleménybeli számlaszámból 30-at hoz, 61-nél nem ad hivatkozást (91 / 93 közlemény 40 karakternél rövidebb). **Közvetlen kereséssel (a jelölt számlaszáma a közleményben, újrajátszás a kiolvasáson):** 70 kötés, 0 hibás, ebből 1 új a termékhez. A modell-lépcső a 262-n választott τ-val: lánc + L-S 126 lezárás, 2 hibás (1,6%); a modell saját lezárásai 56, ebből 2 hibás (3,6%), mindkettő M-címkéjű. A fejek nem adnak többet (L-RN 112–122, L-R07 109–112), az iker-kapu nem számít. **Fejlesztési számok, a τ a mintán választott.**
- **11-06, Dani döntései:** (1) „indulhat”: az M rögzítve a kétirányú olvasattal, a 40 nem döntő mondat változatlan; (2) „elfogadom”: a 08B-n a lánc a kinyerés helyett a jelölt számlaszámát keresi közvetlenül a közleményben (eltérés a 7. ponttól), és két külön fő szám van: a lánc kötéseinek és a modell saját lezárásainak hibaaránya, mindkettő ≤ 2% céllal. A τ a 262-n választott érték, a friss mintára rögzítendő.
- **11-06 11:26, a K08M kész** (10:32–11:26, a második próba került R-módba; a det0 és a det1 bitre azonos; `kor08/eredmenyek/M/k1/g5_k1.md`, eredménylap F függelék). Szabálycsalád, K1(a'): L-RN 0,882 [0,832; 0,925], L-S 0,739, **L-RN − L-S 0,144 [0,085; 0,211], „javít érdemben”; a rögzített olvasat szerint nem bizonyíték, a kérdés nyitva, erősebb kontrollról Dani dönt.** A K1(b) 0,036, ahogy kell. A τ fölött lezárt (a'): szabály L-RN 54,6 / L-S 43,9%, hiba 20,4 / 77,4%. Utólag, leíró (`m_utolagos08.py`): azonos tanítómintán a legjobb szöveges modell 0,827, a kvartiliseken belül L-RN 0,85–0,88, L-S 0,62–0,75.
- **11-06, Dani: „készítsd el, vigyük végig a fej kérdést”.** Erősebb kontroll (N), minimális pár a szabálycsaládon (`szint08n.py`): a (b'') a kért összegről J(f)-et, a korábbi kérelemről L(f')-t mond, az (a'') a kért összegről L(f)-et, a korábbi kérelemről J(f')-t; f' a forgatókönyv párja (azonos gold–csali). Új mondat nincs, a J a `jel2`, az L az `illeszt08m`. Mindkét tag új szöveg, 551 + 551 terv. Első fél: generálás és szöveges ellenőrzés, fej nélkül; küszöbök az M-éi, a generálás előtt rögzítve (`felszin08n.py`). A második fél csak Dani jóváhagyott rögzítése után.
- **11-06 12:48, az N első fele kész, az illesztés elfogadva** (`kor08/eredmenyek/N/felszin/illesztes.md`): hossz 0,505, régi modell 0,518, friss CV 0,714 (küszöbök 0,60 / 0,70 / 0,80), medián hossz 568 / 570. Kihozatal 431 egység (862 item), 34 forgatókönyv: a „másik jel” tiltása a közös kulcsszavú pároknál mindig bukott (150 terv), 3 pár kiesett; nem pótoljuk. A Muse néhány szövegben lazán fogalmaz, ezért vak címkeellenőrzés a kiolvasás előtt (`kor08/adat/N/audit/atnezo.html`, 30 item, kapu ≤ 2 eltérés). Tervezet: `kor08/N-rogzites.md`, futtató: `k08n.sh`, `n08.py`. **Nyitott: Dani címkeellenőrzése és jóváhagyása.**
- **11-08 08:56, az N első címkeellenőrzése: 3 eltérés a 30-ból, a kapu (≤ 2) nem teljesült, a kiolvasás nem indult** (`kor08/adat/N/audit/dontesek.json`, sha256 92cbb28c…). Dani válasza mindhárom tételen helyes, a hiba a generálásé: két (a'')-ben a „korábbi kérelem” mondat üres, és a J a kért összegről szól (F45, F50); egy (b'')-ből a J kimaradt, a tényellenőrzőt az aláírás kulcsszava vitte át (F71). **Javaslat Daninak (`kor08/N-rogzites.md` v0.2, tervezet):** szerkezeti szűrő (`szures08n.py`, csak szöveg és terv): marad 348 egység, 33 forgatókönyv; az illesztés a szűrt mintán hossz 0,506, régi 0,513, friss 0,695; a 3 hibás tétel kiesik. Friss vak ellenőrzés 30 itemen a szűrt mintából (`atnezo2.html`, az 1. körtől diszjunkt), kapu ≤ 2; ha ez is bukik, a fej parkol. A v0.1 jóváhagyása a v0.2-re nem érvényes, az itemek még változatlanok.
- **11-08 09:04, az N második címkeellenőrzése: 0 eltérés a 30-ból, a kapu (≤ 2) teljesült** (`kor08/adat/N/audit/dontesek2.json`, sha256 af0a72a7…; Dani: „vakon kitöltöttem”, 16 szabálypont, 14 M). A szűrő még nincs alkalmazva, az N nincs rögzítve: **Dani „elfogadom”-ja a v0.2-re még hiányzik.**
- **11-08, Dani: „elfogadom, mehet”** — a szűrő alkalmazva (348 egység, 696 item, 33 forgatókönyv; az eredeti `items_szures_elott/`), az illesztés a szűrt mintán hossz 0,506, régi 0,513, friss 0,695; az N rögzítve (`kor08/rogzites/N/manifest.json`), a `k08n.sh` indul.
- **11-08 09:55, a K08N kész** (09:11–09:55, első próbára R-módban, a det0 és a det1 bitre azonos; `kor08/eredmenyek/N/k1/g5_k1.md`, `szoveg.json`, eredménylap G függelék). Szabálycsalád, K1(a''): L-RN 0,872 [0,823; 0,914], L-S 0,797 [0,734; 0,855], **L-RN − L-S 0,075 [0,028; 0,131], „javít érdemben”;** a legjobb szöveges modell ugyanazon a halmazon 0,699 (friss CV), a régi 0,515. **A rögzített olvasat: a fej állítása szűkített formában áll (szabálycsalád, minimális pár, ezek a fejek), a kérdés lezárult.** Mellette: a τ fölött lezárt (a'') L-RN 77,7%, L-S 37,9%; az L-R +0,020, az L-LRN +0,011; K1(b) 0,025 (9 rossz opció). Termékhasznosság ebből nem következik.
- **11-08, önellenőrzés a beszámoló előtt (Dani kérésére; `kor08/eredmenyek/onellenorzes-11-08.md`): kritikus hiba nincs.** Rögzítések zöldek; az N 348 egysége szerkezetileg hibátlan; a F és G függelék 30 száma egyezik a JSON-okkal; érzékenység pár-klaszterrel (17): Δ 0,075 [0,021; 0,148], az olvasat áll; részeset: a fej az (a'') gold-kategóriás választásait is elválasztja (0,844 / 0,760). Nem kritikus, a beszámolóba kerül: egymás utáni próbák a fejen, a 2. címkeellenőrzés gyorsasága és a kulcsfájl helye, Holm az N-ben, a 2. feltétel pontbecslés, a K08V τ-ja. **Dani: „ha nem találsz kritikus hibát, indulhat a beszámoló írása” → indul, először a lánc.**
- **11-08, a beszámoló 1. vázlata:** `kor08/publikacio/beszamolo-lanc.hu.md` (belső magyar, a docai-evals csomag szerkezetében: mire volt a mérés, mi a lánc, protokoll, K2 + J + K3 + K08V, mit jelent, korlátok, anyagok; a fej 2. részként röviden). A számok a gépi JSON-okból, visszaellenőrizve. Nyitott: Dani átnézése, utána az angol csomag (README, decision-record, eval-card, protocol, results, code) és a publikálási döntés (D11: szintetikus eredmények + a valódi adat aggregátuma; a tenant neve nélkül).
