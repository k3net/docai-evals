# F1 — pilot jegyzőkönyv (K0, S05, A200)

> A runbook §6 szerint az F1 nem eredmény, hanem a protokoll validálása. Ez a fájl azt
> rögzíti, mi történt a validálás közben — beleértve azt, hogy **a pilot első indítása
> megbukott a saját kapuján**, és miért lett a mérés ettől jobb.

---

## 1. ⛔ A párhuzamosság-kapu megbukott (2026-09-18, 16:08)

### Mit mértünk

A runbook §6-ba az F0 során beépített kapu: a párhuzamosított (`parallel=6`) csapda-mérés
12 itemét **sorosan** (`parallel=1`) is lefuttatjuk ugyanazon a kiszolgálón, ugyanazzal a
modellel, és item-szinten, bájtra összevetjük. Kimenet:
`eredmenyek/parhuzam-igazolas.txt`.

```
sha egyezés   : 9/12
pont eltérés  : 1  ['T7-08']
pass eltérés  : 1  ['T7-08']

⛔ VERDIKT: a kötegméret a PASS/FAIL-t is átbillenti.
```

A vezénylő ezen a ponton — ahogy meg volt írva — **leállt**, a további két kar el sem
indult.

### Amit a részletek mondanak

| | párhuzamos (`parallel=6`) | soros (`parallel=1`) |
|---|---|---|
| `T7-08` kimenetek | 2 különböző szöveg 3 futásból | **3/3 azonos** |
| `T7-08` pontszám | 1,00 / 1 → **PASS** | 0,00 / 1 → **FAIL** |
| `T1-01`, `C5-03` | eltérő szöveg, azonos pont | 3/3 azonos |
| mind a 12 item | 72/150 instabil a teljes futáson | **12/12 bájtra reprodukálható** |

Két dolgot érdemes külön kimondani, mert együtt adják ki a bajt:

1. **A `T7-08` nem „ingadozott" — a kötegméret átrakta a másik oldalra.** A párhuzamos
   futás mindhárom ismétlése átment (két különböző szöveggel, de mindkettő jó ítélettel),
   a soros mindhárom ismétlése elbukott, egyetlen, stabil szöveggel. Ez nem zaj, hanem
   **feltételhatás**.
2. **Épp akkora, mint amit mérni akarunk.** A kilenc kar közti várt különbség
   item-szinten néhány item. Ha a kötegméret ugyanennyit mozgat, akkor a folt hatása és a
   mérési körülmény hatása **nem szétválasztható** — ez konfundálás, nem pontatlanság.

A `T7-08` ráadásul nem véletlen item: ebből absztraháltuk a **C9 („eldönthetetlen
állításra határozott ítélet")** hibaosztályt. A korpusz legélesebb döntési határán ülő
item az, amelyik a kötegméretre billen. Ez pontosan az a hely, ahol a folt hatását
keressük.

---

## 2. A remedy: soros mérés — és miért nem kerül többe

A runbook §6 a kapuhoz két ágat nevezett meg: *„vagy soros mérés kell, vagy a
párhuzamosságot a mért változók közé kell venni"*. Az elsőt választjuk.

A második ág (a kötegméretet mért változóként kezelni) kart duplázna, és a végén akkor is
azt mondaná, hogy az item-szintű állítások kötegméret-függők — vagyis a költséget
kifizetnénk azért, hogy a gyengébb állítást pontosan írhassuk le.

**Az első ág viszont ingyen van**, mert a soros mérés determinisztikus, tehát az ismétlés
elhagyható:

| | eddig (párhuzamos) | mostantól (soros) |
|---|---|---|
| beállítás | `--parallel 6 --futasok 3` | `--parallel 1 --futasok 1` |
| kérés / kar | 450 | **150** |
| átlagos kérés-idő | 39,8 s | 23,4 s |
| átbocsátás | — | 61,1 kimeneti token/s |
| **idő / kar** | ~108 perc | **~46 perc** |
| reprodukálható? | nem (72/150 item instabil) | **igen** (12/12 bájtra) |

A három ismétlés eddig nem információt adott, hanem a párhuzamosítás saját zaját
átlagolta ki. A zajforrás megszűnésével az ismétlés is feleslegessé vált.

**Eltérés a runbook §4-től:** a §4 a csapdán 3× (az elsődleges karokon 5×) ismétlést ír
elő. Mostantól a két greedy műszeren (csapda, kínai próba) **1× fut**, a **kontrollon
viszont 3×** — nem zajátlagolásként, hanem a determinizmus bizonyítékaként.

---

## 3. Az új kapu: soros determinizmus a teljes korpuszon

A párhuzamosság-kapu helyére `eszkozok/determinizmus_ellenoriz.py` lép. Ez erősebb
állítást kér, és olcsóbban: nem két mérés egyezését, hanem azt, hogy **a mérés önmagában
reprodukálható** legyen, mind a 150 itemen.

- **Átmegy**, ha a kontroll mind a 150 itemén mindhárom soros ismétlés bájtra azonos.
- **Bukik**, ha bármelyik eltér — és akkor az F1 megáll, mielőtt nyolc kar lefutna. Ebben
  az esetben a mérés felbontása a mért ingadozásnál finomabb nem lehet, és a §5 margóját
  újra kell gondolni.

Az eszköz visszautasítja a nem soros bemenetet (`parallel≠1`), hogy ne lehessen véletlenül
a régi fájlra ráfuttatni.

---

## 4. Amit ez az F0 lezárt eredményeiből visszanyit

⛔ **A `csapda-K0.json`, amin a Kapu F0 megítélése állt, párhuzamos mérés volt.** Ezért:

- archiválva `magyar-kie-eval/reports/csapda-K0-parhuzamos6.json` néven (a kínai próba
  ugyanígy: `kinai-K0-parhuzamos6.json`) — nem töröljük, mert ez a bizonyítéka annak,
  hogy a kötegméret mit csinál;
- a **K0 kontroll újramérése sorosan folyik**, és a Kapu F0 mindkét ágát a soros számokon
  kell újra kimondani.

Ami ettől **változik** az F0 jegyzőkönyvéhez képest:

> ⭐ **A „2,00 pp műszerzaj" nem a műszer sajátja volt, hanem a párhuzamosításé.**
> Az F0 naplója rögzítette, hogy a három greedy futás közül 72/150 itemen tér el a nyers
> szöveg, 4-nél a pontszám és 3-nál a PASS/FAIL, és hogy ez a **2,00 pp** meghaladja a
> −1,33 pp-os nem-inferioritási margót. A 12 itemes soros futás mindhárom ismétlésben
> bájtra azonos kimenetet adott — vagyis ez a zaj a kötegméretből jött, nem a modellből.
> Ha a soros determinizmus a teljes 150 itemen igazolódik, a **margó újra használható**,
> és a §5 „a felbontásunk alatt van" kitétele nem a mérés tehetetlenségét fogja jelenteni.
> ⛔ Ez **még nem eredmény, hanem előrejelzés** — a kapu fogja eldönteni.

### Előre rögzített előrejelzés (a mérés előtt)

A Kapu F0/(1) a párhuzamos K0-n úgy teljesült, hogy a round5-höz képest **két item
cserélődött oda-vissza: `T3-02` és `T7-08`** (49/50 vs. 49/50, 97,00/100 mindkettőn). A
round5 mérése soros volt, és ott a `T7-08` **elbukott** — ahogy most a soros K0-n is.
Ebből az következik, hogy:

> a soros K0 a round5-tel a `T7-08`-on **egyezni fog**, tehát a cserélődő itemek száma
> 2-ről legfeljebb 1-re csökken.

Ha ez így lesz, az a soros mérés mellett szóló független bizonyíték. Ha nem, akkor a
kötegméreten kívül van még egy meg nem értett szabadsági fok, és azt meg kell keresni,
mielőtt bármit publikálunk.

---

## 5. Amit tudatosan NEM állítunk sorosra

| műszer | beállítás | miért maradhat |
|---|---|---|
| Han-szonda | eleve soros | nincs benne párhuzamosítás; ráadásul **mintavételezett** végpont, az ismétlés ott valódi információ (marad 5×, illetve F2-n 3×) |
| eseménypróba | egyetlen pozíció, `temperature=0` | nincs köteg |
| belső KIE | a külső runner alapértelmezése | megerősítő műszer (§7/3. feltétel), **nem publikálható**, minden karon azonos beállítás |
| belső contract | `--parallel 3` | ugyanaz — ⚠️ **item-szintű állítás belőle nem tehető**, csak aggregált összevetés; a tanulmány korlát-szakaszába bekerül |

---

## 6. Időrend

| idő | esemény |
|---|---|
| 15:09 | K0 csapda kész, párhuzamosan (`parallel=6`, 3×) |
| 15:21 | K0 kínai próba kész, párhuzamosan |
| 15:54 | K0 belső műszerek + kockázatszámítás kész |
| 15:57–16:08 | párhuzamosság-igazolás: 12 item sorosan, 3× |
| 16:08 | ⛔ **kapu bukott, F1 leállt** |
| 17:40 | mérőpad átállítva sorosra; párhuzamos K0-kimenetek archiválva |
| 17:45 | **F1 újraindítva**: K0 sorosan 3× → determinizmus-kapu → S05 → A200 |

---

## 7. Menet közbeni önellenőrzés · 2026-09-18 18:00

Adattal újra igazolva: az `lm_head` nem kötött (`tie_word_embeddings: False`); a
beta-build round5-ös két lokális szekvenciális futása **0/50 instabil**, a `T7-08` szövege
bájtra azonos két nap és két példány távlatából; a round5 `t237` szondák instabilitása
a **megosztott távoli** kiszolgálóé (`<remote-host>`) — ugyanaz a mechanizmus, mint a
párhuzamosítás. A soros K0 alatt `num_requests_running = 1`, más kliens nincs.

⛔ **Rés a kapuban:** a párhuzamos és a soros 12 item két kiszolgáló-példányon futott. A
karok összevetése mindig két példány között történik, ezért ezt igazolni kell:
`eszkozok/k0_ujpeldany.sh` az F1 után friss példányon újraméri a K0-t (150 × 1, soros) és
ugyanott a 12 itemet `parallel=6`-tal → `eredmenyek/ujpeldany-igazolas.txt`.

**Döntés:** a §7/1 átírva Σp bootstrap felső korlátra (a Poisson-olvasat ~200/M-es
padlója miatt teljesíthetetlen volt). Részletek és a további három tisztázás a runbook
Naplójában.

**Az előrejelzés kiegészítése:** a round5 referenciában `T3-02 = 33b413c77041` (PASS) és
`T7-08 = b77a16a4b6e9` (FAIL); a párhuzamos K0 **mindkettőt** megfordította. Ha a soros K0
mindkettőt visszaadja, a csere nem ≤1, hanem **0** lesz.

---

## 8. Az F1 lezárult · 2026-09-19 (F1 KÉSZ 23:57, új példány 00:58)

### Kapu F1 — a három előre rögzített feltétel

| feltétel | mért | verdikt |
|---|---|---|
| az `S05` reprodukálja a round5-öt | Han-kockázat: **exact nulla** `t=0,6/0,8/1,0`, bootstrap CI `[0; 0]` mindhárom; csapda: a régi 50 itemen **50/50 sha** azonos a round5 S05 szövegével | ✅ |
| a kínai próba a **kontrollon** mér | `K0`: **36/36 = 100 %** [90,4–100], 0 instabil | ✅ |
| `K0` vs `S05` a csapdán ≤ 5 pont | Δ = **0,00 pp**, 0 diszkordáns pár | ✅ |

A kapu teljesül. Amit az F1 ezen túl megmutatott, az fontosabb, mint maga a kapu.

### ⭐ 1. A magyar csapda greedy alatt vak a beavatkozásra — konstrukcióból

`K0` ≡ `S05` ≡ `A200` a mind a **150 itemen bájtra azonos** (150/150 sha), és a round5
alap ≡ round5 S05 ugyanígy 50/50. Ez nem a modell robusztussága, hanem aritmetika: a
folt kizárólag a Han-sorok logitját változtatja; ezek magyar szövegen soha nem
argmaxok (a szorzásos forma a negatív logitokat nulla felé tolja, az irány-csere
−α-ra állítja — mindkettő messze a tipikus +15…30-as csúcs alatt), tehát a greedy
kimenet **bitre ugyanaz**. Mintavételezés alatt is csak ott térhet el, ahol egy
Han-token benne van a csonkolt tartóban — vagyis:

> **a nem-célnyelvi költség felülről korlátos a nem-célnyelvi Han-kockázattal.**

Ez a runbook H1 („erős dózisnál fizetünk magyarul") **cáfolata minden dózisra**, és
egyben azt is jelenti, hogy a magyar csapda ebben a kísérletben nem költségmérő,
hanem **nullműszer**: bármely kar bájteltérése a `K0`-tól *nem a folt*, hanem a
mérési körülmény. Ez a tulajdonság az alábbi 3. leletnél a mentőöv.

⚠️ Következmény a §4–§5-re: a „csapda-pontszám" elsődleges költség-végpontként
tartalmatlan; a költség tengelye a **kínai próba** (lent), a magyar csapda pedig
**negatív kontrollként** marad (azt igazolja, hogy a mérés nem lát fantomhatást).

### ⭐ 2. A költség egésze a kínain van, és már S = 0,5-nél totális

| kar | kínai pontszám | Han **nélküli** válasz | Han-kockázat `t=1,0` |
|---|---|---|---|
| `K0` | **36/36 = 100 %** | 0/36 | 219,9/M [48; 289] |
| `S05` | **1/36 = 2,8 %** [0,5–14,2] | **35/36** | exact 0 |
| `A200` | **0/36 = 0,0 %** [0–9,6] | **36/36** | exact 0 |

McNemar p < 10⁻⁴ mindkettőn, Holm után is. Az `S05` **nem** „rosszabbul tud
kínaiul" — a válaszok 97 %-ában egyetlen kínai írásjegy sincs: nem tud
megszólalni. Ez a model card száma. A dózis-hatás valódi tengelye tehát a kínai:
az F2 karjai (`S07`, `S03`, `A050`, `S05F`, `A200F`) azt mondják meg, van-e olyan
dózis, ahol a magyar kockázat már nulla, de a kínai még él.

Mellékes, de rögzítendő: az `A200` a **gondolkodásban** `t=0,8`-on 5 Han-tokent
generált (1 134/M a gondolkodás-pozíciókon), a válaszban egyet sem. Az irány-csere
tehát nem teljesen zárja le a Han-t a gondolkodásban — melyik tokenek ezek, és a
nyers maszkban vannak-e, az F2 után nézendő (H3-releváns).

### ⛔ 3. A kiszolgáló-példány a késélen ülő itemeket átbillenti

A menet közbeni önellenőrzésben megtalált rés **valódi**. A friss példányon
újramért `K0` (soros, 1×) a determinizmus-kapun átment `K0`-tól (soros, 3×,
150/150 bájtra stabil) **5/150 item PASS/FAIL-jében eltér**: `C9-09`, `T3-02`,
`T3-03`, `T3-05`, `T7-08`. Ugyanazon a példányon viszont a meleg cache sem
változtat (17/17), és a `parallel=6` sem billenti a PASS/FAIL-t (0/12).

A példány-sorozat (4 sima példány, ugyanaz a 17 item sorosan):

| pár | sha egyezés | PASS/FAIL eltér |
|---|---|---|
| inst1 (`K0`) vs inst3 | **17/17** | 0 |
| inst1 vs inst2 (`ujpeldany`) | 9/17 | **5** |
| inst1 vs inst4 | 8/17 | **3** |
| inst2 vs inst4 | 10/17 | **2** |

Négy példány, **három különböző mintázat** — ez nem két „mód", hanem példányonként
más numerika. Gyanúsítottak a motor-logból: `enable_flashinfer_autotune=True` és
`benchmark_combo_kernel: True` (mindkettő időzítés-alapú kernelválasztás
indításkor). Egy példányon belül minden determinisztikus; a példányok között nem.

**Mit jelent ez a mérésre.** A karok összevetése mindig két példány között
történik, tehát ez a zaj minden kar-összevetésben benne van: ~2–5/150 item. Az
1. lelet miatt viszont **elkülöníthető**: mivel a folt a magyar greedy kimenetet
bizonyíthatóan nem érinti, a `K0`-tól való bármely bájteltérés példányzaj. Az F1
három karja történetesen ugyanabba a numerikába esett (`K0`-inst1 ≡ `S05` ≡
`A200` ≡ round5, öt példány, három súlykészlet), ezért a Kapu F1 harmadik
feltétele „tisztán" teljesült — de ez szerencse volt, nem garancia.

**Helyesbítés a 4. szakaszhoz (2026-09-18):** ott azt írtam, hogy a 2,00 pp
„műszerzaj" a párhuzamosításé volt. Félig igaz: a párhuzamosítás *is* billent, de a
példány önmagában is, hasonló nagyságrendben. A párhuzamos K0 mérés az inst0-n
készült, a soros-12 az inst1-en — a kapu **két hatást mért össze**. A helyes
állítás: *a csapda futásról futásra bitre stabil, példányról példányra nem, és a
példány-zaj ≈ 2–3 pp.*

**A batch-invariáns mód próbája** (`VLLM_BATCH_INVARIANT=1`): az első pár el sem
indult — a mód explicit `FLASH_ATTN`/`TRITON_ATTN` backendet követel, a FlashInfer-t
nem támogatja. Második pár `--attention-backend TRITON_ATTN`-nel — **elindult, és működik**:

| pár | sha egyezés | PASS/FAIL eltér |
|---|---|---|
| inst7-bi vs inst8-bi (két friss példány) | **17/17** | 0 |
| inst8-bi soros vs inst8-bi `parallel=6` | **12/12** | 0 |
| inst7-bi vs inst1 (sima) | 9/17 | 3 |
| inst7-bi vs inst2 / inst4 (sima) | 12/17 · 9/17 | 2 · 2 |

A batch-invariáns mód **példányok között és kötegméretek között is bájtra
reprodukálható** — ez az első mérési út, amelyen a determinizmus nem egy példányra
korlátozódik. Ára: ~12 % lassabb sorosan (53,6 vs 60,7 kimeneti token/s), viszont a
`parallel=6` bizonyítottan ártalmatlan rajta, így a csapda egy karon ~21 percre
rövidül (sima motoron sorosan 46). A BI-numerika a sima példányokétól is eltér (egy
negyedik mintázat), tehát ez **motorváltás**: ha erre épül az F2, a `K0`, `S05`, `A200`
ezen az úton újramérendő, és a round5-összevetés a sima motoron marad érvényes
(Kapu F0/F1 ott már teljesült). Az eszközök: `eszkozok/peldany_sorozat.sh`,
`eszkozok/peldany_sorozat_bi.sh`; eredmények: `eredmenyek/peldany-sorozat*.txt`.

### Amit a Kapu F1 után az F2-ről mondani lehet

- Az F2 **érdemes**: a kínai dózis-hatás az igazi kérdés, és ahhoz a hat kar kell.
- A magyar csapda minden karon **negatív kontroll**: várt eredmény a bájtazonosság
  `K0`-val; eltérés = példányzaj, jelentendő, de nem a folt hatása.
- A példányzaj kezelése az F2 előtt eldöntendő — a BI-próba eredményétől függ.

---

## 9. F2 — futó napló · 2026-09-19 (indult 13:00, sima motor, sorosan, 1×)

Ez a szakasz karonként bővül, ahogy az eredmények érkeznek; az F2 lezárása után külön
jegyzőkönyv (`F2-naplo.md`) foglalja össze.

### S07 (szorzás, S = 0,7, nyers maszk) · kész 14:09

| műszer | eredmény |
|---|---|
| csapda (negatív kontroll) | **150/150 sha azonos a `K0`-val** — a nullműszer-előrejelzés teljesül; a példány a gyakori numerikába esett |
| kínai próba | **36/36 = 100 %** [90,4–100], 0 Han nélküli válasz — **a kínai ép** |
| Han-kockázat `t=0,6 / 0,8 / 1,0` | **exact 0**, bootstrap CI `[0; 0]` mindhárom (5 120 / 4 507 / 3 484 válaszpozíció; 3× ismétlés) |

⭐ **S07 az `S*` jelölt:** S = 0,5-nél a kínai már összeomlik (2,8 %), S = 0,7-nél ép, és a
magyar kockázat a termelési mintavételi úton mindkettőnél exact nulla. A dózis-hatás a
kínai tengelyen tehát **szakadék 0,7 és 0,5 között**, nem lejtő. Két korlát, amit a
következtetés mellé kell írni:

1. **A szonda F2-n 3× fut (F1-en 5×)**, `t=1,0`-n 3 484 válaszpozíció, 3 különböző
   végső válasz — az exact nulla igaz, de a Poisson-korlát 860/M. Az `S*` megerősítése
   F3-ban 5×, több példányon.
2. **Az előjel-csapda S = 0,7-nél is aktív** (F0 mérés): a *nyers* Han-tömeg `t=1,0`-n a
   kontroll 10,5 %-áról **13,4 %-ra nő**; a nulla a `top_k=20` csonkolás terméke. A
   model card kötelező mondata: *a folt csak csonkoló mintavételezéssel hatásos*.

### S03 (szorzás, S = 0,3, nyers maszk) · kész 16:01

| műszer | eredmény |
|---|---|
| csapda (negatív kontroll) | **150/150 sha azonos a `K0`-val** |
| kínai próba | **0/36 = 0,0 %** [0–9,6], 36/36 Han nélküli — a kínai halott |
| Han-kockázat `t=0,6 / 0,8 / 1,0` | **exact 0**, CI `[0; 0]` mindhárom |

A szakadék másik oldala, ahogy vártuk. ⚠️ A Han-szonda pozíciószámai (8 134 / 7 750 /
5 548) **számra azonosak az S07-éivel** — a motor `seed=0`-val fut, és ha egyetlen
pozíción sincs Han a top-20-ban, a csonkolt-újranormált eloszlás minden S-karon
ugyanaz, tehát a mintavételezett trajektória is. Ez a nullműszer-tulajdonság
mintavételezés alatti változata: **az S-karok Han-szondája nem független
mérés, hanem ugyanaz a trajektória** — az „exact nulla" igaz, de a karok közti
különbség a haszonoldalon *definíció szerint* nem mérhető ezen a műszeren (ld. az
önellenőrzés 3. pontját: lépcső, nem görbe).

⭐ **Bájtszintű ellenőrzés (16:10):** az S07 és az S03 Han-szondájának **mind a 27
mintavételezett trajektóriája** (3 eset × 3 ismétlés × 3 hőmérséklet, gondolkodás +
válasz) **karakterre azonos**. Ez a mechanizmus közvetlen bizonyítéka: a folt ott
és csak ott hat, ahol a Han a csonkolt tartóban lenne — máshol a modell viselkedése
a dózistól függetlenül *ugyanaz*. A kontrollhoz képest viszont a trajektóriák
eltérnek (ott a Han a top-20-ba jutott, és a mintavétel más útra vitte a modellt).

### S01 (szorzás, S = 0,1, nyers maszk) · kész 17:30

| műszer | eredmény |
|---|---|
| csapda (negatív kontroll) | a `K0`-tól (inst1) **5 itemen eltér** — de a `K0-ujpeldany`-nyal (inst2) **150/150 sha azonos** |
| kínai próba | **0/36 = 0,0 %**, 36/36 Han nélküli |
| Han-kockázat `t=0,6 / 0,8 / 1,0` | **exact 0**, CI `[0; 0]` mindhárom (3 663 / 3 943 / 5 840 válaszpozíció) |

⭐ **Ez a példányzaj-állítás döntő próbája, és átment.** Az S01 példánya a másik
numerikába esett; a csapdán pontosan az inst2 öt itemje billent (`C9-09`, `T3-02`,
`T3-03`, `T3-05`, `T7-08`), és a teljes 150 item **bájtra** az inst2-es K0. A legerősebb
dózis sem érinti a magyar greedy kimenetet; ami eltér, az a példány. Két következmény:

1. A példány-„módok" **diszkrétek**, nem folytonosak: tíz példányból három mintázat, és
   az S01 az inst2-t bájtra reprodukálta. Valószínűleg néhány kernelkonfiguráció közül
   választ a motor indításkor. A nullműszer-tulajdonság miatt **minden kar csapdája
   azonosítja a saját példányának módját** — ez a példányzaj kezelésének módja az
   F2-ben: a karokat a *velük azonos módú* K0-hoz hasonlítjuk.
2. Az S01 Han-szondájának trajektóriái az S07/S03-étól eltérnek (0/27 azonos), de nem a
   folt miatt, hanem a példány numerikája miatt (más logitok, ugyanaz a seed → más út).
   Az exact nulla ettől függetlenül áll.

Dózis-sor a kínai tengelyen eddig: **S07 100 % · S05 2,8 % · S03 0 % · S01 0 % ·
A200 0 %.** A magyar kockázat mindenütt exact 0.

