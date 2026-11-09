# 07 K3 — felismerik-e a fejek a valóban összetéveszthető jelöltek közti tévedést?

**2026-11-01 este.** A végső diagnosztikai minta (K07K3) a 07 TESZT-sablonjain, a mentett, befagyasztott fejekkel. A
K3 a 07A diagnosztikai végpontja (07-runbook 1., 3.3, 4.): külön közölt, a fő szabálynak nem része.

- **Eljárás:** a K3 elemzője (`kor07/eszkozok/k3_07.py`) a minta generálása előtt rögzült (19:45:17,
  `kor07/rogzites/k3/`). A kiolvasás pecsét alatt futott (`cache/k07/pecset_k3`, 30 fájl). A pecsétet Dani
  jóváhagyásával nyitottam 21:10:29-kor („nyithatod, ha végzett”). A v1 és a K3 manifestje, valamint a pecsét a nyitás
  előtt és az elemzés után is változatlan volt.
- **A számok forrása:** `k3.md` és `k3.json` (10 000 ismétlés, sabloncsoportos klaszteres bootstrap, seed 20261101).
  Ez a lap a rögzített kimenetet foglalja össze és értelmezi, új számot nem számol. Az egyetlen kivétel a véletlen
  sorrend viszonyítási értéke (lent), amely a közölt darabszámokból adódik.

## 1. A minta

A 3. kör rögzített konstrukciója (`kor07/nehez3-javaslat.md`). Minden item MATCH. A döntő részlet a szövegben van, de
egy következtetési lépés kell hozzá. A csali az a jelölt, amelyet a felszíni egyezés adna.

| család | változat | terv | item | sablon | rossz opció a SELECT-eken (B1-4) | ebből csali | nem-SELECT |
|---|---|---|---|---|---|---|---|
| bank | részfizetés (30 / 40 / 50%) | 200 | 186 | 60 | 127 / 181 (70%) | 127 | 5 |
| hiba | mértékegység-váltás | 200 | 182 | 38 | 80 / 175 (46%) | 80 | 7 |
| szabály | nettó / bruttó, deviza (fele-fele) | 200 | 199 | 60 | 148 / 196 (76%) | 148 | 3 |

- **Kiesés a tényellenőrzőn (a generálás után, a modell előtt):** bank 14 (a szövegből hiányzott az arány), hiba 18 (12
  zárójelben visszaváltotta a mérést, 6 megnevezte az okot), szabály 1 (kiírta az átszámított összeget). Pótlás nem
  készült (D11).
- **A goldok kézi ellenőrzése:** 16 item a pecsét nyitása előtt, mindhárom családból és mindkét nyelven, csak a szöveg
  és a terv alapján. Mindegyikben a gold a kimondott lépéssel következik.
- **Nyelvenként a rossz opció:** bank hu 74 / 100, en 53 / 86; hiba hu 35 / 86, en 45 / 96; szabály hu 55 / 100,
  en 93 / 99.

## 2. A fő sor: a három család átlaga, négyállapotú keret

A rossz opció felismerése AUROC-cal mérve a SELECT-döntéseken: 1 = minden helyes SELECT a rosszak fölött, 0,5 =
véletlen, 0 = fordított. A SELECT-AURC-nál a kisebb a jobb. Véletlen sorrendnél a SELECT-AURC körülbelül a hibaarány:
a három család átlagában 0,64.

| kar | AUROC [95%] | olvasat (előre rögzített) | SELECT-AURC [95%] |
|---|---|---|---|
| B1-4S (a B1 saját bizonyossága) | 0,413 [0,363; 0,462] | fordítva rangsorol | 0,684 [0,634; 0,734] |
| **B1-4R** (megbízhatósági fej) | 0,452 [0,393; 0,507] | nem különbözik a véletlentől | 0,631 [0,579; 0,689] |
| B1-4LR (logisztikus referencia) | 0,438 [0,386; 0,491] | fordítva rangsorol | 0,669 [0,616; 0,722] |

| pár | ΔAUROC [95%] | olvasat | ΔSELECT-AURC [95%] | olvasat |
|---|---|---|---|---|
| B1-4R − B1-4S | +0,039 [−0,020; 0,097] | nem kimutatható | −0,053 [−0,091; −0,013] | javít |
| B1-4LR − B1-4S | +0,026 [0,001; 0,050] | javít | −0,015 [−0,027; −0,004] | javít |
| B1-4R − B1-4LR | +0,014 [−0,043; 0,069] | nem kimutatható | −0,038 [−0,074; 0,001] | nem kimutatható |

A 06-os kereten ugyanez a kép (leíró): B1-S 0,412, B1-R 0,425, B1-LR 0,447, mindhárom fordítva rangsorol;
B1-R − B1-S +0,013 [−0,048; 0,073].

## 3. Családonként (leíró)

| család | B1-4S | B1-4R | B1-4LR | B1-4R − B1-4S |
|---|---|---|---|---|
| bank | 0,310 [0,225; 0,396] | **0,211** [0,142; 0,289] | 0,345 [0,255; 0,434] | −0,099 [−0,195; 0,006] |
| hiba | 0,612 [0,520; 0,698] | **0,696** [0,601; 0,777] | 0,594 [0,500; 0,682] | +0,085 [0,001; 0,168] |
| szabály | 0,316 [0,233; 0,402] | 0,447 [0,322; 0,570] | 0,375 [0,287; 0,468] | +0,131 [0,016; 0,246] |

Az AUROC változatonként és nyelvenként a `k3.md` bontásában van. Ezek kis cellák, csak pontbecslések.

## 4. Értelmezés

1. **A következtetési lépés hiányából eredő tévedést egyik kar sem ismeri fel a három család átlagában.** A B1 saját
   bizonyossága fordított: amikor a csalit választja, magabiztosabb. A megbízhatósági fej (B1-4R) ezt nagyjából a
   véletlen szintjére húzza (SELECT-AURC 0,684 → 0,631, a véletlen sorrend kb. 0,64). Ez mérhető javulás, de nem
   felismerés.
2. **A családok szétválnak:**
   - **Hibaelhárítás:** minden kar 0,5 fölött van, a B1-4R 0,70, és javít a B1-4S-hez képest. A mértékegység-váltásnál
     a tévedés valamennyire látszik a jellemzőkben.
   - **Bank:** minden kar fordított. **A B1-4R a legerősebben (0,21): a fej még jobban preferálja a pontos összegű
     csalit, mint az alapmodell.** A fej a D_meta-n előtanult, és a 06 T500-án finomhangolódott; a T500-ban a
     MATCH-tétel összege mindig a gold számla bruttója. A legvalószínűbb magyarázat, hogy a „pontos összeg = jó”
     szabályt tanulta meg, és részfizetésnél éppen ez vezet félre.
   - **Szabálycsalád:** az alap fordított (0,32). A B1-4R a véletlen közelébe javít (+0,13), angolul viszont szinte
     minden válasz rossz (93 / 99).
3. **Gyakorlati következmény:** a bizonyosságra épülő lezárás (a K2 τ-ja) ezeket a tévedéseket nem szűri ki. A bankon és
   a szabálycsaládon épp a magabiztos válaszok közt vannak. Ezekre a termékben nem megbízhatósági fej kell, hanem
   determinisztikus ellenőrzés: az arány, az áfa, az árfolyam és az egység kiszámítása és összevetése a jelöltekkel a
   modell döntése előtt vagy után. **A 07B-re:** a <tenant> négy hónapjában kevés a valódi részfizetés-jelölt (4 kötés, ahol
   a kötés több mint 2 Ft-tal kisebb a számla bruttójánál; a B0 korábbi „26”-ja kerekítés volt), de ahol előfordul, ott
   ugyanez a csapda fenyeget. A K4-ben ezek külön sorban.

## 4a. Kiegészítés: munkapont a változatlan τ-val (rögzítés utáni, feltáró; Dani kérése, 11-01 este)

`kor07/eszkozok/munkapont07.py` → `munkapont/munkapont.md`. Az F5 CAL-on kapott τ-k változatlanul, karonként és
családonként (a seedes karoknál seedenként, a számok a három seed átlaga). Lezárva a SELECT vagy X javaslat, ha a
pontszám ≥ τ. Minden item MATCH, így az X-lezárás is hiba.

| család | kar | lezárt / n | ebből hibás | hibás arány | F5 TESZT lezárási hiba |
|---|---|---|---|---|---|
| bank | B1-4S, B1-4LR | nincs munkapont (semmit nem zár le) | – | – | – |
| bank | **B1-4R** | 11 / 186 | 11 | **100%** | 2,5% |
| hiba | B1-4S | 116 / 182 | 46 | 40% | 4,7% |
| hiba | **B1-4R** | 60 / 182 | 16 | **27%** | 1,3% |
| hiba | B1-4LR | 78 / 182 | 35 | 45% | 2,7% |
| szabály | B1-4S | 36 / 199 | 36 | 100% | 2,8% |
| szabály | **B1-4R** | 151 / 199 | 122 | **81%** | 3,8% |
| szabály | B1-4LR | 138 / 199 | 107 | 78% | 3,2% |

**A gyakorlati következmény:** a természetes összetételű friss mintán 1,3–4,7% lezárási hibájú munkapontok ezen a
tévedéstípuson a lezárt tételek 27–100%-át hibásan zárják le. A legtöbbet a B1-4R zárja le a szabálycsaládon
(151 / 199, ebből 122 hibás); a hibás lezárások nagy része a csali kiválasztása, kisebb része X. A bankon a B1-4R
kevés tételt enged át, de azok mind hibásak; a B1-4S-nek és a B1-4LR-nek ott nincs munkapontja. A 06-os keret karjai
hasonlóan viselkednek (a lapon).

## 4b. Kiegészítés: páros próba a kiszámított értékkel (rögzítés utáni, feltáró; Dani kérése, 11-01 este)

`kor07/eszkozok/aug07.py` → `aug/aug.md`. Ugyanazok az itemek és jelöltek, egyszer az eredeti szöveggel, egyszer a
szöveg végén egy sorral, amely a hiányzó lépés eredményét adja meg. Ezt a sort a kód számolja a terv tényeiből, nem
nyelvi modell: a számla teljes bruttója, az átváltott mérés, a nettó összeg, illetve az átszámított összeg. Az alany
és a fejek ugyanazok (K07EJ2, 11-01 22:05–23:07; a 07B pontozása 11-02 08:07-kor futott újra). Négyállapotú keret, helyes =
SELECT a gold opción:

| család | helyes: eredeti → kiegészített | javult / romlott | Δ helyes arány [95%] | B1-4R AUROC: eredeti → kieg. |
|---|---|---|---|---|
| bank (részfizetés) | 54 / 186 (29%) → **186 / 186 (100%)** | 132 / 0 | 0,710 [0,646; 0,771] | 0,211 → nem értelmezett (nincs rossz SELECT) |
| hiba (mértékegység-váltás) | 95 / 182 (52%) → **171 / 182 (94%)** | 78 / 2 | 0,418 [0,328; 0,505] | 0,696 → 0,919 |
| szabály (nettó, deviza) | 48 / 199 (24%) → **134 / 199 (67%)** | 86 / 0 | 0,432 [0,365; 0,500] | 0,447 → 0,547 |
| ebből szabály, magyar | 42 / 100 → 90 / 100 | 48 / 0 | | |
| ebből szabály, angol | 6 / 99 → 44 / 99 | 38 / 0 | | |

Az intervallum sabloncsoportos klaszteres bootstrap (2000 ismétlés), a McNemar-próba mindhárom családon p < 0,0001.
**Minden megmaradt rossz válasz a csali, más rossz opció egyik változatban sincs.** A 06-os keret ugyanezt adja
(Δ 0,683; 0,401; 0,412).

Munkapont a változatlan τ-val, B1-4R (a seedek átlaga), lezárt / ebből hibás: bank 11 / 11 → 42 / 0; hiba 60 / 16 →
166 / 4; szabály 151 / 122 → 188 / 63.

**Mit jelent:**

1. **A bankon és a hibaelhárításon a tévedést szinte teljesen a ki nem számított lépés magyarázza.** Ha a lépés
   eredménye a szövegben van, az alany jól dönt, és a fej is jól rangsorol (hiba: 0,70 → 0,92). A bankon a kiszámított
   bruttó betűre egyezik a gold opció összegével, ezért a 100% ott felszíni egyezés. Ez azt mutatja, hogy a szűk pont a
   számítás, azt nem, hogy az alany következtet.
2. **A szabálycsaládon a számítás csak a hiba felét viszi el.** A megmaradt hiba a küszöb-összevetés: a kiszámított
   nettó mellett is a bruttóhoz igazodik a választás. Angol példa a mintából: 227 EUR nettó, 250 EUR-s határ, a modell
   mégis a „250 felett” pontot választja. Ugyanez a devizánál: az átszámított 814 EUR mellett a 690 GBP-hez választ.
   Ez angolul a tételek felénél előfordul, magyarul ritkán.
3. **A K3 4. pontjának következtetése ezzel élesebb:** a termékben a számítást (arány, áfa, árfolyam, egység) és a
   szabályfajtáknál a küszöb-összevetést is kód végezze, a modell csak a kiszámított értékek után döntsön. A
   kiegészített szövegen a változatlan τ a szabálycsaládon így is 34%-os hibával zár le, tehát a küszöbös szabályokra a
   fej munkapontja önmagában nem elég.

Korlát: feltáró elemzés a már megismert K3-mintán, ugyanazokon az itemeken; a sor formája („Ellenőrzött számítás: …”)
erős jel, és a valódi termékben az ellenőrzött érték máshogy jelenne meg. A hatás nagysága ezért felső becslés arra,
mennyit hoz a számítás átadása.

## 5. Korlátok

- **Szintetikus, szerkesztett minta.** A csali szándékosan a felszíni egyezés. A minta azt méri, mit tesz a fej egy
  ismert, nehéz tévedéstípuson, nem azt, milyen gyakori ez a valódi forgalomban.
- **A hibaelhárítás 38 sablonon** van (sablononként kb. 5 item). 21 TESZT-sablonban nincs alkalmas egységpár, egy
  további sablon mind a 6 itemje a tényellenőrzőn esett ki. A bootstrap ezt a sablon szerinti klaszterezéssel kezeli,
  de az intervallum emiatt szélesebb.
- **A fejek nem láttak ilyen típusú példát.** A tanító 06 T500-ban a banki MATCH-tétel összege mindig a gold bruttója,
  a mérés a szabály egységében, az összeg a küszöb pénznemében szerepel. A 06 családterve ugyan felsorolja a
  részfizetést és a devizát a banki szcenárió-dimenziók közt, de a generátor ezt nem valósította meg. A K3 ezért azt
  mutatja, hogy a fej nem általánosít erre a tévedéstípusra, nem azt, hogy nem tanulhatná meg.
- **A K3 leíró.** Az olvasat előre rögzített, a családok és a bontások sorai többszörös összevetésre nem korrigáltak.

## Önellenőrzés

- Az elemző, a pontozó, a kiolvasó, a generátor és a futtató a generálás előtt rögzült; a próba a 3. kör nyitott
  mintáján csak darabszámot írt ki, és a darabszámok egyeztek a `b14_nehez3`-mal.
- A pontozó helyessége itemenként egyezik a gold opcióval (az elemző betöltője ellenőrzi). A nem értelmezett
  bootstrap-replikák száma 0.
- A minta tervei a spark-deven bitre egyeztek a helyben készültekkel; az önteszt a TESZT-sablonokon 20 / 20.
- A fenti számok a `k3.md`-ből és a `k3.json`-ból valók; a véletlen sorrend viszonyítási értéke (0,64) a
  hibaarányok átlaga (0,702; 0,457; 0,755).
