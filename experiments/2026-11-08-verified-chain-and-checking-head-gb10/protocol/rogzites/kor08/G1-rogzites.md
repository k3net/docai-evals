# 08 — a G1 végi előzetes rögzítés (D12): tervezet

- **Állapot:** **v0.3, Dani jóváhagyta 2026-11-04-én** („1. jóváhagyom, 2. ok, 3. G2 indulhat”); a rögzítés a
  `kor08/rogzites/D12/manifest.json` (14.). A 11-04-i kiegészítések (a próbák nyomán, Dani döntéseivel): a jelfajta-bontás
  (6.), a bank várható K3-kimenete (7.), a jelzett auditminta (5.4), a képzés-kulcsszó javítása, a forgatókönyvek 2.
  köre (5.3), a függőségek és a G3 G1-es bemenetei a rögzítésben (14.), a G2 futtatója technikai megszakadás után
  folytatható (11.).
  - **v0.3 (második kör, Dani 11-03):** a bank feladatszabálya minden szintetikus banki bemenet kérdése után (4.3; a T500 és
    a K3 diag újraolvasva, K08G1I); a szabálycsalád lefedési auditja 80 teljes egység, közös megjelenítéssel (5.4); az
    erő végleges számai (9.); az őr G1-es jelzése és ismétlése (10.).
  - **v0.2 → v0.3 (Dani 11-03, a v0.2 négy nyitott kérdésére):** a tanítás forrásonként 50–50% össz-súllyal (5.3); a
    bank teljes fizetési feltevése kimondott feladatszabály, csak a szintetikus feladatban (4.3); a címkehibánál két
    független hibás alapeset felülvizsgálati küszöb, nem automatikus kizárás, és a konstrukciós hiba külön kezelendő
    (5.4); az audit a szabálycsaládon mindkét nyelvet lefedi, a bankon és a hibán forgatókönyvenként egy, előre
    kiegyensúlyozott nyelvet (5.4).
  - **v0.1 → v0.2 (Dani 11-03):** a hat nyitott kérdés eldőlt; a szabálycsalád tanítómintája 1500 (b) + 500 (a); a két
    fő próba Holm-korrekcióval, az erő ezzel a döntési szabállyal; a SELECT-AURC másodlagos, küszöb nélkül; a lánc
    hiányzó adatból nem zár ki (a bank pénzneme, javítva és a G1-en újrafuttatva); a kód és a modell döntései szétválasztva;
    az audit minden forgatókönyvet és nyelvi változatot lefed, és a címkehiba kezelése előre rögzített; pontos
    darabszámok 1 (a) + 3 (b) egységekben; a keresztellenőrzés külön, leíró K3-összevetés.
- **Mit köt:** a kérdéseket, a karokat, a mintaméreteket, a kizárási és kötési szabályokat, az értelmezési diagnózis
  definícióját, a végpontokat, az olvasati küszöböket, a rögzített konfigurációt és az elemzők kódját, mielőtt friss
  adat készül (08-runbook 8., D12). A G4 már csak a végrehajtást dokumentálja.
- **Alapja:** a 08-runbook v0.2 és Dani döntései a G1 alatt (runbook-napló 11-02 – 11-03), a G1 eredménylapja
  (`kor08/eredmenyek/G1/eredmenylap.md`). A G1 minden száma megismert adaton készült, fejlesztési szám.

---

## 1. Kérdések és fő vizsgálatok

| vizsgálat | szerep | döntés |
|---|---|---|
| **K1(b), szabálycsalád:** felismeri-e a fej az eldönthető eset rossz értelmezését (rossz szabálypont, ha a helyes eldönthető)? | **fő** (1. fő próba) | D13 (11-02) |
| **K1(a), szabálycsalád:** megkülönbözteti-e a fej az eldönthetetlen választást az eldönthető, helyes választástól? | **fő** (2. fő próba) | D13 (11-02) |
| K1(a), bank és hibaelhárítás | leíró | Dani 11-03: az alany saját bizonyossága a pilotban már 0,94 és 0,97 |
| K1(b), bank és hibaelhárítás | leíró, az eseményszámmal | D13 (11-02): a (b)-hiba ott ritka (3%) |
| K2: eltünteti-e a lánc a K3-típusú tévedést valós kinyeréssel, és mennyit veszít a kinyerés? | fő a láncra | runbook 1. |
| K3: a természetes összetételű friss teszten, azonos megengedett hibaszint mellett hány ügyet zár le helyesen a rendszer? | gyakorlati | runbook 1., D4 |
| K3-X: a két kinyerő keresztellenőrzése a K3 tesztjén | leíró, külön | Dani 11-03 (5. pont) |
| K4 (08B): a valódi banki tételeken melyik lépcső ad új helyes megoldást, és melyik új hibát? | külön | D10 |

**A siker szintjei (D9)** a runbook 1. pontja szerint: a lánc működőképessége (K2), a kutatási jel (K1, a 8. pont
olvasataival, köztük „nem eldönthető”), a gyakorlati haszon (K3).

## 2. Karok és összevetések

| kar | a döntés | megbízhatóság | tanítóadat |
|---|---|---|---|
| L-S | lánc + alany | az alany saját pontszáma a választott válaszon (négy sorrend átlaga, `b1rel07.decide4` q) | — |
| L-R07 | lánc + alany | a 07 B1-4R, befagyasztva | a 07-es |
| L-R | lánc + alany | fej: D_meta-előtanítás, finomhangolás, 3 seed (17, 42, 73) | láncos T500 |
| **L-RN** | lánc + alany | mint az L-R | láncos T500 + értelmezési tanítóminta, **forrásonként 50–50% össz-súllyal** (5.3) |
| L-LR | lánc + alany | L2-logisztikus: a 07 B1-4LR 10 jellemzője + a lánc jellemzői | láncos T500 |
| L-LRN | lánc + alany | mint az L-LR | **ugyanazok a példák és súlyok, mint az L-RN-é** |
| 07 B1-4S, B1-4R | lánc nélkül | a 07-es | a 07-es |

- **A két fő próba:** L-RN − L-S AUROC a szabálycsalád K1(b)-jén és K1(a)-ján, **Holm-korrekcióval** (8. pont).
- **Másodlagos:** minden más karösszevetés (L-R07 − L-S, L-R − L-S, L-RN − L-R, L-RN − L-LRN, a szabálycsalád K1(a)-ján is
  az L-RN − L-LRN), a SELECT-AURC mindenütt, a bank és a hiba minden K1-száma.
- **Kalibráció az új bemeneten:** a temperature és a τ minden láncos karnál a friss CAL-on, a lánc kimenetén.

## 3. A pontszámok iránya

- **Hibapontszám** (az AUROC-hoz): minél nagyobb, annál nagyobb a hiba kockázata. Az L-S-nél 1 − q; a fejeknél
  1 − a fej megbízhatósági valószínűsége; a logisztikus karoknál ugyanígy. Az AUROC pozitív osztálya a hiba (K1(b): a
  rossz opció; K1(a): az (a) SELECT-je), és az AUROC annak a valószínűsége, hogy egy pozitív hibapontszáma nagyobb egy
  negatívénál.
- **Megbízhatóság** (az AURC-hoz és a K3-hoz): q, illetve a fej valószínűsége. Az AURC a megbízhatóság szerint csökkenő
  sorrendben a kumulált hibaarány átlaga; a kisebb a jobb.
- Az elemző a pontszám irányát a karonként rögzített függvénnyel számolja, és a G1 pilotján önellenőrzéssel igazolja (a
  pilot L-S AUROC-ja a `g1b_ert08` számával egyezzen).

## 4. A lánc

**Kód:** `kor08/eszkozok/lanc08.py` (sha256 a 14. pontban). Ami itt áll, az a kód leírása; eltérésnél a kód érvényes,
és az eltérést a rögzítés előtt javítani kell.

### 4.1 Ki dönt miről

| döntés | ki hozza | megbízhatósági küszöb |
|---|---|---|
| **automatikus kötés** (csak a szintetikus és a valódi bank) | a kód (4.3) | nincs: lezárt (D4), hibája a lezárási hibaarányba számít |
| **emberhez** (nincs kinyerés; ellentmondásos kinyerés: egy szerepben két eltérő ellenőrzött érték) | a kód | nincs: nem lezárt |
| **kizárás** (egy jelölt kikerül a listából) | a kód (4.3) | nincs; a modell a megmaradt jelöltek közül választ |
| **SELECT** a megmaradt jelöltek közül, vagy **X** („nincs megfelelő opció”) | a modell | **van:** τ fölött lezárt, alatta emberhez (07 D9) |
| **Y** (nem eldönthető) és **Z** (nem a hatáskör) | a modell | nincs: emberhez (07 D9) |

- **A lánc nem ad X-et.** Ha minden jelölt kizárt, a tétel üres listával a modellhez megy, és a modell dönt X, Y és Z
  közt (Dani 11-02). A runbook K3-ban említett „lánc X-ei” ezért nincsenek; a K3-ban a lánc automatikus döntése csak a
  kötés.
- Az ikrek a modellhez mennek; automatikus Y nincs (D3).

### 4.2 Kinyerés és ellenőrzés

- **Kinyerés (D1):** az alany a vLLM-példányán (`Qwen/Qwen3.6-35B-A3B-FP8`, vLLM-image `vllm/vllm-openai:v0.30.0`,
  thinking nélkül, temperature 0), kötött JSON-sémával, csak a tétel szövegét látja (a hibacsaládon a szabályok
  mérésneveit is). **Séma (Dani 11-02):** bank v1 (`kinyero_sema`), hibaelhárítás v1, szabálycsalád v2 (`kinyero_sema2`);
  a promptok `lanc08.kinyero_prompt` (a szövegük a rögzített kódban). A G3-ban egyszer fut, a kimenete hash-elve (G4).
- **Ellenőrzés:** a forrásrészlet szó szerint szerepel, és az érték belőle a nyelv számformátumával kiolvasható; egy
  forrásrészlet egy szerepet tölt be; szerepfeltételek: áfakulcs hu {5, 18, 27}, en {0, 5, 20}; részlet-arány 1–99%;
  árfolyam-sávok (HUF/EUR 250–600, EUR/GBP 0,8–2,0 és a fordítottjaik); az egység a mért mennyiséghez illik; a
  szerepjelölő és a deviza az érték 60 karakteres környezetében. Az ellenőrzésen bukott mező elvetődik (csak
  információvesztés, kizárásra vagy kötésre nem vezet).

### 4.3 Kizárás és kötés: hiányzó adatból nem következik kizárás (Dani 11-03)

**Elv:** kizárás csak bizonyított ellentmondásból, ellenőrzött mezőkön. Ha a számításhoz szükséges mező hiányzik, elvetődött
vagy nem ellenőrizhető, a jelölt lehetséges marad; hallgatólagos alapérték nincs. Kötés csak ténylegesen elvégzett
egyezéssel.

| család | kizárás | automatikus kötés | ha egy mező hiányzik |
|---|---|---|---|
| bank (szintetikus) | a számított teljes összeg (részlet-arány után) a tűrésen túl eltér egy **azonos pénznemű** jelölt bruttójától | a hivatkozás pontosan egy jelölt számlaszámát tartalmazza, **és** a pénzneme azonos, **és** a számított összeg a tűrésen belül egyezik, **és** a szöveg nem nevez meg más partnert | pénznem nélkül (sem igazolt deviza, sem önálló pénznemjelölő az érték mellett) nincs összegalapú kizárás és kötés; részfizetés-jel mellett ellenőrzött arány nélkül sincs |
| hibaelhárítás | egy ellenőrzött, a szabály egységére átváltott mérés kívül esik az ok szabálytartományán | nincs | hiányzó vagy át nem váltható mérés: az ok lehetséges marad |
| szabálycsalád | a számított összeg (átszámítás és nettósítás után) a szabálypont küszöbének másik oldalára esik | nincs | ismeretlen pénznem, vagy eltérő pénznem ellenőrzött árfolyam nélkül: nincs kizárás; nettó szabálypont ellenőrzött nettó nélkül (alap vagy áfakulcs hiányzik): az a pont nem mérhető |
| bank (valódi, 08B) | csak strukturális ellentmondás (deviza, irány); az összegeltérés nem kizáró ok | mint a szintetikus banknál, a partner a törzsadatból; az összeg egyezése pozitív bizonyíték, nem a teljes fizetés feltevése | mint fent; a részfizetés-jel hiányából nem következik teljes fizetés |

- **A bank feladatszabálya (Dani 11-03), csak a szintetikus feladatban, az alany bemenetében is:** minden szintetikus
  banki tanító- és értékelési bemenet kérdése után ugyanaz a mondat (`lanc08.BANK_FELADATSZABALY`, `bank_kerdes`):
  - hu: *„Ebben a feladatban a részfizetést a leírás mindig jelzi; ilyen jelzés hiányában teljes kiegyenlítést
    feltételezz.”*
  - en: *„In this task, the description always indicates a partial payment; if there is no such indication, assume full
    settlement.”*

  Hatóköre: a láncos T500, az értelmezési tanítóminta, a friss CAL és TESZT, a K3-típus mindhárom útja, és a lánc nélküli
  összehasonlító banki bemenetek (a 07 B1-4S, B1-4R ugyanazokon az itemeken). Ok: a lánc ezen a feltevésen zár ki, ezért
  az alanynak is meg kell kapnia; a kérdés („Melyik nyitott számlát egyenlíti ki ez a tétel?”) ezt nem mondja ki
  egyértelműen. A T500 és a K3 diag banki kiolvasása ezzel újra készült (K08G1I), így az új fejek tanítása és tesztje
  azonos szabályt használ. **Az L-R07** (a 07 fej befagyasztva) ettől a 07-es tanításához képest más bemenetet kap:
  átviteli vizsgálat, a bemeneti változást dokumentáljuk. Ugyanez a szabály áll a G2 generátorának bank-előírásában és
  az audit útmutatójában. Két eset:
  - **a szövegben nincs részfizetésre utalás** (a részfizetés-jelek: hu „részlet”, de nem a „Részletek:” /
    „részletei” fejléc, „részfizet”, „előleg”, „százalék”, „%”; en „instalment”, „partial”, „deposit”, „percent”, „%”):
    a feladatszabály alkalmazható, a számított összeg a tétel összege;
  - **a szövegben van utalás, de a kinyerő nem ad ellenőrzött arányt:** hiányos kinyerés; nincs visszaállás teljes
    fizetésre, nincs összegalapú kizárás és kötés (a kód így működik: `lanc08`, `reszfizetes_jel_arany_nelkul`).
- **A valódi 08B-adaton** a feladatszabály nem érvényes, a mondat nem kerül a bemenetbe: a részfizetés-jel hiányából nem
  következik teljes fizetés, és önmagában nem alapoz meg összegeltérés miatti kizárást (a 08B-n az összegeltérés amúgy
  sem kizáró ok).
- **Javítás a G1-ben (11-03, K08G1G):** a 11-03 előtti kód a bank pénznemét a nyelvből vette (hu → HUF, en → EUR), és a
  „Részletek:” / „részletei” fejlécet részfizetés-jelnek olvasta. A javítás a G1 megismert adatán, orákulum-úton: a 06
  bankon 792 → 786 automatikus kötés (a 6 pénznem nélküli), 56 tételen több kizárás (a gold egyiken sem), 12 tételen a
  pénznem hiányában nincs kizárás; a 07 bankon 583 → 581 kötés; hamis kizárás és hamis kötés 0 előtte és utána; a hiba- és a szabálycsalád
  kimenete változatlan.
- **Az „Ellenőrzött adatok” blokk:** a szabálycsaládon **v4** (Dani 11-03): pontonként „összeghatár teljesül; a
  költségnem nincs ellenőrizve”. A bankon pénznem nélkül „(a pénznem nem ellenőrizhető)”.
- **Mérőszámok:** a döntést befolyásoló kinyerési hiba és a hamis átengedés a runbook 2.2 szerint (`g1_lanc08.kulcs`:
  kimenet, megmaradt jelöltek, automatikus kötés, a modellnek mutatott blokk; a hamis átengedés nevezője az ellenőrzésen
  átment tételek száma).

## 5. Adat (G2)

### 5.1 Közös

- **Friss sablonok,** a 06 és a 07 sabloncsoportjaitól diszjunktan. Generátor: Muse-Glimmer-30B (revízió
  `a4e59da52a7bc87ae7251dd5545c0dd437c44b68`, reasoning „low”), a tényellenőrző kapuval.
- **A darabszámok a generálás tervezett számai.** Ami a tényellenőrző kapun, a lánc-kapun vagy az auditon elbukik, az
  kimarad; utánpótlás nincs, a tényleges számot közöljük.

### 5.2 Friss CAL és TESZT, a K3-típus

- **CAL és TESZT (3.2, D5):** családonként CAL 500 + TESZT 1000; összetétel MATCH 60 / NO_MATCH 20 / MISSING_DATA 10 /
  OUT_OF_SCOPE 10%, fele magyar, fele angol.
- **A K3-típus (3.4):** a négy változat (részfizetés, mértékegység-váltás, nettó / bruttó, deviza), változatonként 100
  item, három úton (lánc nélkül, valós kinyeréssel, orákulum-mezőkkel).

### 5.3 Az értelmezési minta és a tanítóminta

- **Egység:** egy alapeset **1 (a) + 3 (b)** változattal: a három (b) ugyanannak az esetnek három átfogalmazása a döntő
  jellel, az (a) ugyanaz az eset a jel nélkül. Az (a) egyszer számít (a K1(a)-ban egy pozitív), nem háromszor.
- **Sabloncsoport (a bootstrap klasztere):** egy friss szabályforgatókönyv minden egysége, mindkét nyelven. Egy egység
  minden változata ugyanabban a csoportban van; egy csoport egységei ugyanabba a szeletbe (teszt vagy tanítás) kerülnek.
- **Konstrukció:** a G1b-é — a szabálycsaládon a javított 2. kör (`ertelmezes08_szab`, a D7 javításaival és az angol 02.
  forgatókönyv javításával), a bankon és a hibán a 2. kör (áttételes jel).
- **A szabálycsalád friss forgatókönyvei** (`forgatokonyv08_szab`, 90): Dani 11-03-i átnézése szerint 64 rendben, 26
  javítva a csereszövegeivel (`kor08/adat/G2/G2_forgatokonyvek_ertekeles.md`; a modulban `JAVITVA`); a 2. körben (11-04)
  a 26-ból 25 rendben, az F41 jele kiegészítve: a kért összeg a taxifuvar díja. A tanulságok: a kért
  összeg tárgya dönt (vegyes helyzetben a jel külön számlatételt mond ki); ha az (a) már megnevezi a fizetett szolgáltatást,
  a jel nem írhatja át más tárgyú díjjá (az (a) ilyenkor „a szolgáltatónak fizetett díj”); nincs rejtett kategóriahatár
  (a vendég útja / szállása, a nyeremény). **Hatókör:** a teszt és a tanítás ugyanazt a 20 rendezett költségnem-párt
  használja, ezért az eredmény ezeknek a határoknak új eseteire szól, nem új kategóriahatárokra.

| minta | család | sabloncsoport | egység / csoport | egység | (b) | (a) |
|---|---|---|---|---|---|---|
| **értelmezési (teszt)** | szabálycsalád | 40 | 14 | 560 | 1680 | 560 |
| | bank | 33 | 2 | 66 | 198 | 66 |
| | hibaelhárítás | 33 | 2 | 66 | 198 | 66 |
| **tanítóminta (L-RN, L-LRN)** | szabálycsalád | 50 | 10 | 500 | 1500 | 500 |
| | bank | 33 | 5 | 165 | 495 | 165 |
| | hibaelhárítás | 30 | 3 | 90 | 270 | 90 |

- **A teszt mérete:** a szabálycsaládon 560 egység azért, hogy a kapuk és az audit kiesése után is kb. 1600 (b) maradjon
  (Dani 11-03); az erőbecslés 534 egységgel számol (9. pont). A bank és a hiba 198 (b) + 66 (a), a D6 eredeti célja
  (Dani 11-03: leíró vizsgálathoz elfogadható; a ritka hibák melletti bizonytalanságot közöljük).
- **A tanítóminta (Dani 11-03):** a szabálycsaládon 1500 (b) + 500 (a); a pilot 6,9%-ával kb. 100 rossz (b)-választás
  várható. **Fix példaszám,** a tényleges hibaszámot közöljük. A bank és a hiba a D8 szabálya szerinti méret (a hibás
  modelldöntések száma legalább a láncos T500-é). A tanítóminta lánca orákulum-mezőkkel fut; sabloncsoportjai
  diszjunktak a tesztétől, a friss CAL / TESZT-étől és a G1 próbáitól.
- **Súlyozás (Dani 11-03): forrásonként egyenlő össz-súly,** családonként (a fej családonként tanul): a láncos T500
  50%, az értelmezési tanítóminta 50%, forráson belül egyforma példasúllyal. A nevező mindkét forrásban a **ténylegesen
  tanítható döntések száma** a lánc és a kapuk után (a modellhez jutott tétel; az automatikus kötés és az emberhez küldés
  nem tanítópélda): N_T és N_É mellett a T500 példasúlya (N_T + N_É) / (2 N_T), az értelmezési mintáé (N_T + N_É) /
  (2 N_É), így az átlagsúly 1. A súly a tanítási és a korai leállás validációs veszteségében is érvényes; **az L-RN és
  az L-LRN ugyanazokat a példákat ugyanezekkel a súlyokkal kapja.** A kalibráció (temperature, τ) a külön friss CAL-on
  marad, súlyozás nélkül. Indok: az új hibatípus megtanítása mellett megmaradjon a korábbi állapothibák felismerése;
  példánkénti egyforma súllyal a szabálycsaládon kb. 80%-ban az új konstrukció határozná meg a tanítást. **Tervezési
  kompromisszum, nem bizonyítottan jobb recept;** a fő futásban csak ez az egy változat fut.

### 5.4 Címkeminőség (D7)

- **Gemma-triage** mind az itemen.
- **Dani vak auditja,** modellválasz és bizonyossági pontszám nélkül, a zárolt vak választású lapon (`audit08e`). Az
  audit a kiolvasás előtt van, így a kezelése a modell eredményétől független. **Három minta, amelyek átfedhetnek:** a
  többször kijelölt egységet egyszer kell átnézni, de mindegyik mintába beszámít.
  - **Lefedési minta (Dani 11-03), nem véletlen:**
    - **szabálycsalád (fő vizsgálat):** minden forgatókönyv mindkét nyelven, egy teljes egység (1 (a) + 3 (b)), a
      csoport sorrendjében véletlenül választva: 40 × 2 = 80 egység, 320 item (80 alapeset);
    - **bank és hiba (leíró):** forgatókönyvenként egy egység ((a) + egy (b)) egy előre, kiegyensúlyozottan kijelölt
      nyelven (a forgatókönyvek sha256(id) sorrendjében felváltva, 17 / 16): 33 pár, 66 item családonként.
  - **Véletlen minta:** családonként 30 egység, nyelvenként 15, rögzített seeddel az összes egységből (a lefedési
    mintával azonos terjedelemben: a szabálycsaládon teljes egység, a bankon és a hibán (a) + egy (b)); a bankon és a
    hibán ez adja a másik nyelv véletlen ellenőrzését. **A címkehibaarány becslése csak ebből a mintából,** külön
    közölve, a 95%-os intervallummal.
  - **Jelzett minta:** a Gemma által jelzett **(b)** itemek egységükkel együtt, **mindkét nyelven**, a kijelölt nyelvtől
    függetlenül. Az (a) Gemma-eltérése nem jelöl (Dani 11-04): a Gemma keretében nincs Y, ezért az (a)-n mindig
    választ (a próbában az (a) 92%-a „eltérő”: 67% csali, 24% gold); az (a)-n a Gemma választása (gold / csali / egyik
    sem) leíróan, forgatókönyvenként (`gemma08`).
  - A várható terhelés az átfedés előtt: a szabálycsaládon 320 + 120 item, a bankon és a hibán 66 + 60–60 item, plus a
    jelzettek. **A szabálycsalád lefedése 80 alapeset, 320 item (Dani 11-03):** a három (b) külön-külön hordozza a döntő
    bizonyítékot, egy (b) ellenőrzése nem elég. A jelentésben a 80 alapeset és a 320 ellenőrzött item külön szerepel; az
    itemek nem függetlenek.
  - **Megjelenítés (Dani 11-03):** egységenként egy lap; a közös alapeset és az opciók egyszer; az (a) és a három (b)
    egymás mellett, az eltérések kiemelve; minden változatra külön ítélet. Így 80 esetet kell megérteni, és esetenként
    négy változatot elbírálni.
- **A címkehiba kezelése (előre rögzítve; Dani 11-03):**
  - **A hiba fajtája előbb eldöntendő:**
    - **konstrukciós hiba:** a gold nem következik a forgatókönyv szabályzatából (a hiba a tervben vagy a szabály
      mondatában van, nem a generált szövegben) → már **egyetlen bizonyított eset** után a forgatókönyv minden érintett
      változata felülvizsgálat alá kerül (minden egység, minden nyelven, amelyre a hibás terv vonatkozik);
    - **egyedi megvalósítási hiba:** elírás, kimaradt mondat, hibás fordítás egy alapeset generált szövegében → előbb
      az érintett alapeset és a változatai kezelendők.
  - **Az egység kezelése:** **javítható,** ha a hiba csak a gold címkében van, a helyes címke a szövegből és a
    szabályzatból egyértelmű, és az egység a javítás után is a konstrukciónak felel meg (a (b)-ben döntő jel, az (a)-ban
    nincs) → a címke javul, a javítás dokumentált; **egyébként az egész egység kimarad** (1 (a) + 3 (b)).
  - **Számolás:** egy alapeset (a)-jának és három (b)-jének közös hibája **egy** hibás alapeset, nem négy.
  - **Felülvizsgálati küszöb, nem automatikus kizárás:** ha egy forgatókönyv–nyelv cellában **két független hibás
    alapeset** van, a cella minden egysége felülvizsgálat alá kerül (Dani átnézi, az egységszabállyal). Ha a cella
    helyessége így sem tisztázható megbízhatóan, **a cella kimarad.** A cella nyelvenként külön: egy angol
    megfogalmazási hiba önmagában nem zárja ki a magyar változatot.
  - Nincs újragenerálás; a kiesést forgatókönyvenként és cellánként közöljük, a felülvizsgálatok számával.

## 6. Az értelmezési diagnózis

A runbook 5. pontja szerint: azok a tételek, ahol nincs döntést befolyásoló kinyerési hiba, a gold nincs kizárva, nincs
automatikus kötés, és a tétel a modellhez jutott. Egy egység (b)-je és (a)-ja külön kerül be vagy marad ki. Közölve a
részhalmaz aránya, és hogy a kiesés összefügg-e az altípussal vagy a nyelvvel. A teljes rendszer eredménye mellette
kötelező.

## 7. Végpontok

- **1. fő próba, K1(b), szabálycsalád:** az értelmezési diagnózison a (b) SELECT-jein AUROC (pozitív: rossz opció;
  negatív: a gold választása; hibapontszám a 3. pont szerint). L-RN − L-S.
- **2. fő próba, K1(a), szabálycsalád:** AUROC az (a) SELECT-jei (pozitív) és a (b) helyes SELECT-jei (negatív) közt.
  L-RN − L-S. Mellette leíró: a modell Y-aránya az (a)-n és a bizonytalan esetekből automatikusan lezárt arány.
- **Másodlagos:** a SELECT-AURC mindkét ágon és minden karon (a különbség és a 95%-os intervallum, **érdemi küszöb
  nélkül**); a 2. pont többi összevetése; a bank és a hiba K1(a)-ja és K1(b)-je az eseményszámmal; a teljes rendszeren
  ugyanez.
- **Leíró, kötelezően:** családonként és nyelvenként; a strukturáltan azonos ikrek száma; a futások közti eltérés
  (seedenként); Brier és ECE. **A jel fajtája szerint** (Dani 11-04): a szabálycsaládon a K1(b) és a K1(a) pontbecslése
  és eseményszáma külön a „szó szerinti” jelű forgatókönyveken (a jel kimondja a gold leírásának egy szavát,
  `forgatokonyv08_szab.jel_fajta`) és az „áttételeseken”; a fő próba változatlan.
- **K2:** a K3-típuson a helyes arány a három úton, változatonként és nyelvenként; a lánc hibái a 2.2 definícióival.
- **K3:** a friss TESZT-en a hasznos lefedettség és a lezárási hibaarány a 07 D9-e szerint (lezárás: a kód automatikus
  kötése és a modell τ fölötti SELECT-je és X-e; 4.1), a lánc kimeneteinek eloszlása saját hibaarányukkal, a ΔAURC
  (L-RN − L-S), és ugyanezen itemeken a 07 B1-4S és B1-4R lánc nélkül. **A τ** karonként és seedenként a friss CAL-on,
  a 07 D9 szabályával (a legnagyobb elfogadott halmaz, ahol a lezárás precizitásának egyoldali 95%-os CP-alsó határa
  ≥ 0,95, legalább 200 lezárttal), **csak a modell lezárható döntésein** (a modellhez jutott tételek SELECT-je és X-e); a
  lánc kötései utána adódnak a lezártakhoz. Így a pontos kötések nem engednek több modellhibát, és a 07 karjai ugyanazt a
  szabályt kapják. Munkapont nélkül a kar a modellből semmit nem zár le, a kötések maradnak. Leíróan mellette a τ a teljes
  lezárt halmazon (a kötésekkel együtt; `g5_k3_08 --tau-halmaz rendszer`).
  **A bankon várható kimenet (Dani 11-04, a 06 CAL / TESZT pilotja alapján):** a láncos karoknak (L-R07, L-S, L-RN,
  L-LRN) valószínűleg nincs munkapontjuk (a pilotban a replikák 100%-ában): a lánc a könnyű tételeket köti (35,8%, 0
  hiba), a maradékon a modell legjobb döntéseinek hibaaránya a 0,95-ös CP-alsó határt 200 lezárttal nem éri el. Ezt
  eredményként közöljük, a szabály nem változik (a 200-as küszöb lazítása eltérne a 07 D9-től, a rendszer-τ pedig a
  pontos kötésekkel több modellhibát engedne: a pilotban 4,9–9,1% a modell lezárásain); a rendszer-τ változat leíró.
- **K3-X, a két kinyerő keresztellenőrzése (leíró, Dani 11-03):** a K3 tesztjén egy változat, ahol ha a lánc kimenete az
  alany kinyerésével és a szabályalapú kinyerővel (`szabkin08`, rögzítve) eltér, a tétel emberhez megy. Közölve a fő
  rendszerhez képest: a **visszatartott hibák** (a fő rendszer hibás lezárása, amelyet a keresztellenőrzés emberhez
  küld) és az **elveszített helyes lezárások** (a fő rendszer helyes lezárása, amely emberhez megy), a hasznos
  lefedettség és a lezárási hibaarány. A két kinyerő egyetértése önmagában nem igazolja a helyességet: az egyező, de
  hibás kinyerést külön sor közli (az orákulumhoz mérve). A fő lánc ettől nem változik.

## 8. Statisztika és olvasat

- Sabloncsoportos klaszteres bootstrap, 10 000 ismétlés, egy egység minden változata egy klaszterben; replikánként a
  seedek átlaga; kétoldali p.
- **A két fő próba Holm-korrekcióval** (α = 0,05): a kisebb p-jű próba 0,025-ös szinten, a másik 0,05-ösön, ha az első
  elutasított, különben 0,025-ösön. Az olvasathoz használt intervallum ennek megfelelő (97,5%, illetve 95%); a közölt
  intervallum mellette mindig a 95%-os is. A másodlagos összevetések korrekció nélkül, leíróan.
- **A K3 bootstrapja** a τ-t replikánként **kizárólag az újramintázott CAL-on** választja újra, és a TESZT-replikán
  alkalmazza.
- **Olvasat (D9)** a hatás nagysága és bizonytalansága szerint; a pontbecslés és az intervallum mindig közölve.

  | egy kar AUROC-ja | feltétel |
  |---|---|
  | felismeri, érdemben | alsó határ > 0,5 és pontbecslés ≥ 0,60 |
  | felismeri, de gyengén | alsó határ > 0,5 és pontbecslés < 0,60 |
  | nem eldönthető | az intervallum tartalmazza a 0,5-öt, a felső határ ≥ 0,60 |
  | gyakorlatilag nem ismeri fel | felső határ < 0,60, az intervallum tartalmazza a 0,5-öt |
  | fordítva rangsorol | felső határ < 0,5 |

  | a fő pár (L-RN − L-S AUROC) | feltétel (a Holm-szintű intervallummal) |
  |---|---|
  | javít érdemben | alsó határ > 0 és pontbecslés ≥ 0,05 |
  | javít, de gyengén | alsó határ > 0 és pontbecslés < 0,05 |
  | nem eldönthető | az intervallum tartalmazza a 0-t, a felső határ ≥ 0,05 |
  | érdemben nem javít | felső határ < 0,05, az intervallum tartalmazza a 0-t |
  | ront | felső határ < 0 |

  - **A SELECT-AURC-ra nincs érdemi küszöb:** a különbség és a 95%-os intervallum (Dani 11-03).

## 9. Erő (`kor08/eredmenyek/G1/ero08.md`)

Szimuláció a döntési szabállyal (K08G1H, 2000 szimuláció helyzetenként): a két fő próba ugyanazon a mintán,
Holm-korrekcióval; 534 egység (1602 (b) + kb. 534 (a)), 40 sabloncsoport; a (b) hibája 6,9% (várhatóan kb. 111 rossz
(b)-választás), csoport- és egységszinten béta-binomiális; a K1(a) L-S AUROC-ja a pilotból (0,61); a hatás, a
csoporthatás és a korrelációk feltevés. **ρ, a két kar pontszámának korrelációja osztályon belül, a 07 F5 TESZT-jéből**
(B1-4S ↔ B1-4R, seed-átlag): a szabálycsaládon a helyes választásokon 0,29, a hibásakon 0,46; mellette érzékenységként
0,3 / 0,3 és 0,6 / 0,6. P(alsó határ > 0) a Holm-szintű intervallummal, K1(b) / K1(a), ICC_e 0 (0,3-mal legfeljebb 2
pont eltérés):

| ρ (helyes / hibás) | K1(b) L-S AUROC | valódi Δ 0,05 / 0,05 | Δ 0,05 / 0 | Δ 0 / 0,05 | Δ 0 / 0 (álpozitív) | Δ 0,10 / 0,10 |
|---|---|---|---|---|---|---|
| 0,29 / 0,46 (07) | 0,70 | 55% / 91% | 44% / 2% | 3% / 90% | 2% / 2% | 99% / 100% |
| 0,29 / 0,46 (07) | **0,80** | **69% / 92%** | 60% / 2% | 3% / 91% | 2% / 2% | 100% / 100% |
| 0,29 / 0,46 (07) | 0,90 | 96% / 94% | 92% / 3% | 3% / 90% | 3% / 1% | 100% / 100% |
| 0,3 / 0,3 | 0,80 | 61% / 87% | 51% / 2% | 3% / 85% | 2% / 2% | 99% / 100% |
| 0,6 / 0,6 | 0,80 | 80% / 98% | 73% / 3% | 4% / 98% | 2% / 1% | 100% / 100% |

- **Olvasat:** egy 0,05-ös valódi javulást a K1(b) a 07 ρ-jával és L-S 0,80-nal kb. 69%-ban mutat ki (0,70-nél 55%,
  0,90-nél 96%), a K1(a) kb. 90%-ban; a 0,10-es javulást mindkettő gyakorlatilag mindig. Az álpozitív arány próbánként
  1–4%. A K1(b) 80%-os ereje Δ 0,05-nél ρ 0,6-ot vagy L-S ≥ 0,85-öt kívánna: a fő próba Δ 0,05-nél **alulerős
  maradhat**, ezt a „nem eldönthető” olvasat kezeli (8. pont).
- Az „érdemben javít” olvasat (pontbecslés ≥ 0,05) valódi Δ 0,05-nél elvből legfeljebb kb. 50% (`ero08.md`, K1(b)
  egyedül).

## 10. A végrehajtás szabályai

- **Pecsét:** a G3 kiolvasásai pecsét alatt futnak; a rögzítés előtt csak darabszám és idő kerül naplóba; a nyitás (G5)
  Dani engedélyével.
- **Determinizmus-őr (Dani 11-03):** minden kiolvasás a rögzített referenciaszelettel indul és zárul (`det_or08`,
  `kor08/adat/G1/det_ref`); a sorainak bitre egyezniük kell. **Ha az őr jelez:** a kiolvasás egyszer, előre rögzített
  módon megismétlődik egy új folyamatban, vLLM-futás nélküli előzménnyel. **Ha ott is jelez,** az érintett kiolvasás
  leáll; a hibakeresés csak a referenciaszeleten folyik, a teszteredmények felnyitása nélkül, és a folytatásról Dani dönt.
  - **A G1-ben egyszer jelzett** (K08G1G, 11-03 17:33): a referenciaszelet mind az 50 sora eltért (medián 0,47 nat, 4
    döntés megfordult; a det0 és a det1 egymással bitre azonos), a képfájl, a modell, a driver, a kód és a bemenet
    változatlan; előtte a gépen vLLM futott (mint az ERT2J-eltérésnél). Az ismétlés (K08G1H) bitre azonos volt; a K08G1G
    kiolvasása archiválva (`*_detjelzes_k08g1g`), a bankon 302 döntésből 3-at fordított volna. Az ok nem ismert. **A
    G3-ban ezért** a vLLM-es lépések (kinyerés, generálás) és a HF-kiolvasás közt a gép állapota naplózva (memória, GPU,
    a konténerek), és a kiolvasás az őr első szeletével kezdődik.
- **A vLLM nemdeterminisztikus:** a kinyerés egyszer fut, a kimenete rögzül és hash-elve a G4 része; reprodukálni a BI +
  TRITON_ATTN beállítással lehet.
- **Egy nagy GPU-folyamat egyszerre;** ≥ 15 GB szabad memória a betöltés után; a Qwen-család csak alany, a címke soha
  nem tőle jön.

## 11. A rögzített konfiguráció és az elemzők kódja

**A rögzítés feltétele,** hogy az alábbiak a G2 előtt elkészüljenek, a G1 pilotján (megismert adat) lefussanak, és a
hash-ük bekerüljön a 14. pontba.

- **Megírva, a G1 pilotján fut (K08G1J; 11-03):**
  - `b1rel08.py pontoz`: a döntések (B1-4S) és a karok megbízhatósága a 07 `pontoz` alakjában; az üres listás tétel
    (a lánc minden jelöltet kizárt) is pontozható (a 07 példaépítője ott elhasal; k ≥ 1-nél a kimenet bitre a 07-é);
  - `g5_k1_08.py`: az értelmezési diagnózis szűrése; a két fő próba és a másodlagosak; a pontszámok iránya (3. pont); a
    klaszteres bootstrap (egységek a klaszterekben, seed-átlag); Holm; az olvasat a 8. pont tábláival; a leíró sorok;
    önellenőrzés a `g1b_ert08` számával;
  - `g5_k2_08.py`: a K3-típus három útja; a lánc hibái a 2.2 szerint (a `g1_lanc08` definícióival);
  - `g5_k3_08.py`: a hasznos lefedettség és a lezárási hibaarány a 4.1 szerint; τ replikánként a CAL-on (7.); ΔAURC; a
    K3-X;
  - **`b1rel08.py tanit`, a 08-as fejtanító** (L-R, L-RN, L-LR, L-LRN) a 07 F3R receptjével (a 07 B1-4R0 előtanított
    fejéből, a 07 tanulási rátájával, 3 seed, öt fold a sabloncsoport szerint, foldonként belső 20%-os korai megállás). A
    láncos T500 az **orákulum-útról** (a fej a lánc kimenetének formáját látja, kinyerési zaj nélkül, mint a
    tanítómintán). A neurális fejek architektúrája a 07-é (a lánc a bemeneten át hat: a blokk, a megmaradt opciók, a
    `log k` a megmaradtaké); **a lánc két jellemzője** (log(megmaradt + 1), log(kizárt + 1)) a logisztikus karokban, a
    B1-4LR 10 jellemzője mellett. A súlyozás az 5.3 szerint; súly nélkül (L-R) a ciklus a 05 `train_rel`-é.
- **Megírva, CPU-n kipróbálva (11-03 este; a G2 GPU-s része a rögzítés után, Dani jóváhagyásával):**
  - `forgatokonyv08_szab.py`: a szabálycsalád 90 friss forgatókönyve (40 teszt, 50 tanító; a tesztben mind a 20 rendezett
    költségnem-pár kétszer), szerkezeti ellenőrzéssel; Dani átnézte (11-03: 64 rendben, 26 javítva a csereszövegeivel,
    5.3); a javított 26 jóváhagyása a 2. körben (`kor08/adat/G2/forgatokonyv_szab_atnezes.md`, „javítva” jelöléssel);
  - `szint08.py`, a G2 generátora: friss `k08`-as sablonkészlet diszjunkt készletekkel (CAL, TESZT, K3, ERT-T, ERT-N); a
    friss CAL / TESZT a 07 kvótáival; a K3-típus négy változata, változatonként 100 terv; az értelmezési teszt és
    tanítóminta 1 (a) + 3 (b) egységekkel (a 2. és a 3. (b) más formában), a szabálycsaládon forgatókönyvenként és
    nyelvenként rögzített egységszámmal, a forgatókönyv a klaszter; a banki kérdés a `bank_kerdes`-szel. A tervezési
    próba pontosan az 5.3 számait adja (szabály: 1680 + 560 és 1500 + 500, 40 és 50 klaszter; bank: 198 + 66 és 495 + 165);
  - `gemma08.py`: a Gemma-triage összesítője részenként; az eltérő (b) itemekből a jelzett auditminta; az értelmezési
    részeken leíróan az (a)-választás és a (b)-egyezés jelfajta szerint;
  - **nem rögzül** (próba, 11-03 / 11-04): `proba08g2.py`, `k08g1l.sh`, `k08g1m.sh` — a forgatókönyvek eldobható Muse +
    Gemma próbája saját seeddel (`kor08/eredmenyek/G1/proba_g2`); ebből jött a jelzett minta, a jelfajta-bontás és a
    képzés-kulcsszó javítása;
  - `audit08g2.py`: a három auditminta (átfedéssel, egységenként egyszer), az egységenkénti lap (közös kérdés és
    opciók, a változatok egymás mellett, kiemeléssel, változatonként zárolt vak választás, felülvizsgálat, a hiba
    fajtája), a szivárgás-ellenőrzés és az összesítő az 5.4 kezelési szabályával (javítható csak a (b) opcióra
    javítása; az (a) hibája és a (b) X / M / Z-re javítása kizárja az egységet); a lánc G2-forrásai (`lanc08.FORRASOK`).
- **A futtatók és a rögzítés (megírva, szintaxis- és kapuellenőrzéssel; futni a rögzítés után fognak):**
  - `k08g2.sh`: a G2 (a sablonok, a tervek, a Muse-generálás és a tényellenőrzés a négy részre, utána a
    Gemma-kiolvasás); csak a D12 manifestje és a forgatókönyvek jóváhagyása (`kor08/adat/G2/FORGATOKONYV-JOVAHAGYVA`)
    után indul; egyszer készül (a kész G2 után nem indul újra), technikai megszakadás után ugyanazt folytatja (a kész
    katalógusok, tervek, nyers szövegek és Gemma-sorok kimaradnak);
  - `audit08g2.py alkalmaz`: az audit kezelése az itemeken a kiolvasás előtt (a felülvizsgálandó cellák döntése nélkül
    nem fut);
  - `k08g3.sh`: a kinyerés (egyszer, hash-elve), a szabályalapú kinyerés, a lánc minden úton, a kiolvasás két
    HF-folyamatban a determinizmus-őrrel és az állapotnaplóval (az értékelő szeletek a pecsét alá, a tanítóminta saját
    gyökérbe; jelzésnél egy rögzített ismétlés, a második jelzésnél leáll), a 08-as fejek, a pontozás a pecsét alatt
    (a lánc nélküli szeleteken a 07 karjai B1-4S / B1-4R néven), a pecsét lezárása; `pecset08.py`: a pecsét, csak a G5
    nyitása után olvasható; `kiolvas08.py`: a G2 szeletei, a pecsét kapujával;
  - `k08g5.sh`: a három elemző 10 000 replikával, a nyitási engedély és a pecsét manifestjének ellenőrzése után;
  - `rogzit08.py`: a D12 manifestje (a 14. pont hash-ei, a modellrevíziók és az image-digestek; felülírni nem lehet),
    az ellenőrzés és a G5 nyitása — mindkettő Dani kifejezett jóváhagyására.
- **Megvan, a rögzítésbe kerül:** `lanc08.py` (a kinyerési sémák, a promptok és a blokk szövege benne), `kinyer08.py`,
  `g1_lanc08.py` (definíciók), `g1_dontes08.py` (`helyes`), `b1rel07.py` (`decide4`, manifestelt), `kiolvas08.py`,
  `det_or08.py`, `lib08.sh`, `audit08e.py`, `szabkin08.py` (a K3-X-hez), `ertelmezes08_szab.py`, `szint08e.py`.
- **Modellek:** az alany vLLM-pillanatképe (`Qwen/Qwen3.6-35B-A3B-FP8`, HF-cache snapshot), a HF BF16 bázis
  (`cache/qwen36-fp8hu-bf16`), a Muse-Glimmer-30B revíziója, a Gemma-triage modell revíziója, a vLLM- és a tool-image
  digestje (`lib.sh` `record_env`).

## 12. Mi dőlt el a v0.1 és a v0.2 nyitott kérdéseiből (Dani 11-03)

| kérdés | döntés |
|---|---|
| 1. bank és hiba: 200 (b) + 65 (a) | marad (198 + 66 az egységszerkezetben); leíró, a bizonytalanság közlésével |
| 2. ≥ 40 sabloncsoport | elfogadva, a csoportdefinícióval (5.3) |
| 3. tanítóminta | szabálycsalád 1500 (b) + 500 (a); a többi család a D8 szerint |
| 4. determinizmus-őr | egy előre rögzített ismétlés; második jelzésnél leállás, hibakeresés a referenciaszeleten (10.) |
| 5. a két kinyerő keresztellenőrzése | külön, leíró K3-összevetés (7.); a fő lánc nem változik |
| 6. ρ | a 07 F5-ből becsülve, a 0,3 és 0,6 érzékenység mellett (9.) |

**A v0.2 nyitott kérdéseiből (Dani 11-03):**

| kérdés | döntés |
|---|---|
| 1. a tanítás súlyozása | forrásonként 50–50% össz-súly, forráson belül egyforma; a tanítható döntések számával; L-RN és L-LRN azonos példákkal és súlyokkal; tervezési kompromisszum, egy változat (5.3) |
| 2. a bank teljes fizetési feltevése | kimondott feladatszabály, csak a szintetikus feladatban; utalás arány nélkül = hiányos kinyerés; a 08B-n nem érvényes (4.3) |
| 3. a címkehiba-szabály | két független hibás alapeset felülvizsgálati küszöb, nem kizárás; a konstrukciós hiba egy esetből is felülvizsgálat; az egység közös hibája egy hiba; a cella nyelvenként külön (5.4) |
| 4. az audit terhelése | szabálycsalád: minden forgatókönyv mindkét nyelven; bank és hiba: forgatókönyvenként egy kiegyensúlyozott nyelv, a másik nyelvből véletlen ellenőrzés; a jelzettek mindkét nyelven; a minták átfedhetnek, a címkehibaarány csak a véletlen mintából (5.4) |

**A v0.3 nyitott kérdéseiből (Dani 11-03):**

| kérdés | döntés |
|---|---|
| 1. a bank feladatszabálya az alany bemenetében | igen, egy közös mondat minden szintetikus banki tanító- és értékelési bemenetben, a T500 újraolvasásával; az L-R07-nél dokumentált bemeneti változás; a 08B-n nem (4.3) |
| 2. a szabálycsalád lefedési auditja | teljes egység (1 (a) + 3 (b)): 80 alapeset, 320 item, közös megjelenítéssel, változatonkénti ítélettel (5.4) |

**A forgatókönyvek átnézéséből (Dani 11-03):** 90-ből 64 rendben, 26 javítandó, 0 kihagyandó; a 26 javítás a
csereszövegekkel beépítve (5.3), a kulcsszavak újraillesztve. A javított szövegek ítélete a 2. körben (13.).

## 13. Nyitott kérdések Daninak

**A forgatókönyvek lezárva (Dani 11-04):** a 26 javítottból 25 rendben, az F41 jele kiegészítve („…és ennek a fuvarnak a
díját kérem megtéríteni”); a 64 korábbival együtt mind a 90 elfogadva. Az F41 angol jele a magyar kiegészítés fordítása
(„…and I am claiming the fare for that ride”), Dani megerősítésére. **Nyitott:** a v0.3 rögzítésének jóváhagyása; utána a
`FORGATOKONYV-JOVAHAGYVA` jelölő és a K08G2 (GPU, külön engedéllyel). A generált egységek D7-auditja külön lépés (5.4).

**Eldőlt:**

| kérdés | döntés |
|---|---|
| a bank feladatszabálya, a lefedési audit (v0.3) | Dani 11-03 (4.3, 5.4) |
| a 90 forgatókönyv | Dani 11-03: 64 rendben, 26 javítandó; 11-04: a 26-ból 25 rendben, az F41 jele kiegészítve (5.3) |
| a szó szerinti költségnem-szó a jelben (a G2 jeleinek 38–50%-a, a G1b-ének 25%-a) | Dani 11-04: a jelek maradnak; leíró bontás a K1(b) és a K1(a) mellett (6.); a próbában a Gemma (b)-egyezése 99% / 96% |
| a bank K3-munkapontja (a pilotban a láncos karoknak a replikák 100%-ában nincs) | Dani 11-04: a szabály marad, a várható kimenet a 7. pontban előre kimondva |
| a jelzett auditminta (a Gemma kerete az (a) Y-ját nem fejezi ki; a próbában az (a) 92%-a „eltérő”) | Dani 11-04: csak a (b) Gemma-eltérése jelöl; az (a) választása leíró (5.4) |
| az angol képzés-gold (a) kiesése (a próbában 18-ból 12 forgatókönyv) | 11-04, K08G1M diagnózis: a `pelda.example` domain „exam” részszava; a kulcsszavak javítva, sablonszöveg-őrrel (11.); a diagnózis szövegein 22 / 90 helyett 76 / 90 megy át, a próba 708 átment szövege változatlanul átmegy |

## 14. Hash-ek (a rögzítéskor töltendő)

A hash-eket a `rogzit08.py rogzit` számolja ki és írja a `kor08/rogzites/D12/manifest.json`-ba (a fájllista a `FAJLOK`: ez
a tervezet (a runbook élő napló, nem rögzül), a 08 kódja a 11. pont szerint, a determinizmus-őr referenciaszelete, a 05–07 felhasznált kódja és a
07 fejeinek leírói, és 11-04 óta a 03–07 közvetett függőségei: a rögzített Python-fájlok importjainak zárt halmaza és a
futtatók hivatkozásai, a Gemma temperature-forrásával; 65 fájl), a G3 tanítás G1-es bemenetei fájlonként (`ADATOK`: a
láncos T500 orákulum-útja és reprezentációi; 23 fájl), a modellrevíziókkal (az alany snapshotja, a HF BF16 bázis, a Muse
revíziója, a Gemma) és az image-digestekkel. A `rogzit` nem fut, ha a függőségek közt rögzítetlen fájl van. A rögzítés után a `rogzit08.py ellenoriz` minden futtató előtt igazolja, hogy a rögzített fájlok
változatlanok.
