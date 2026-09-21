# Runbook: mennyit szabad elvenni egy tokenosztálytól?

**Dózis-hatás mérés a CJK-csillapításra, Qwen3.6-35B-A3B-FP8-on — a végén egy mért,
publikált HuggingFace-modell és egy hivatkozható tanulmány.**

- Kezdés: 2026-09-16 · tervezett zárás: 2026-09-22 (6 nap, ebből ~2 éjszaka GPU)
- Gép: measurement-host (<remote-host>) · minden hosszú mérés **leválasztva** (`setsid nohup`), STATUS-fájllal
- Előzmény: `docai-research/qwen3.8-flash-next/round5/` (jelenség, mérték, első folt, eval-revízió)
- Végtermékek: (1) HF modell + model card, (2) tanulmány a `/kutatas` rovatba,
  (3) a már megírt blogcikk **ezzel együtt** jelenik meg, nem előbb

> ⚠️ Ez a runbook **a mérés előtt** készült, és a hipotéziseket, az elsődleges
> végpontot, a statisztikai eljárást és a publikálási döntési szabályt **előre**
> rögzíti. Ha menet közben változik bármelyik, a változás **dátummal és okkal** ide
> kerül, nem csendben. Ez a különbség a feltáró hibakeresés és a tanulmány között.

---

## 0. Miért van erre szükség, és mi az, ami már megvan

A 2026-09-13–15-i kör (round5) elvégezte a feltáró munkát: megvan a jelenség, a
mérték, egy működő beavatkozás és a mellékhatás-ellenőrzés. Amit **tudunk**:

| megállapítás | erősség |
|---|---|
| a Han-kockázat hőmérséklet-függő: `t=0,6` → 8,4/M, `t=1,0` → 88,0/M, greedy → 0 | mért, ismételt |
| `lm_head` sorskálázás `S=0,5`-tel: minden mért kockázat 0/M-re esik | mért |
| a rögzített billenési ponton a top-20 Han-tömeg 8,314 % → 0,000 % | mért, egy ponton |
| a kinyerési minőség **nem romlik** (két motorbuildon, mindhárom műszeren) | mért, kis n |
| a magyar csapdakorpusz döntetlen: 94:94 (prod-build), 97:97 (beta-build) | mért, ismételt |
| a szorzás előjel-csapdája ebben a modellben nem aktív | mért **egy** ponton |
| ⛔ a foltnak tulajdonított **minőségjavulás visszavonva**: a másik motorbuildon nem reprodukálódik | mért, 2026-09-15 este |
| a **motorbuild** önmagában többet mozdít, mint a folt (KIE 0,979→1,000, csapda 94→97, foltozatlanul) | mért |

Amit **nem tudunk**, és ezért van ez a kör:

1. **Hol van az optimum.** Egyetlen erősséget (`S=0,5`) mértünk végig. Nem tudjuk,
   hogy `0,7` is elég-e, és nem tudjuk, hol kezd fájni.
2. **Hogy jó formájú-e a beavatkozás.** A `ThakiCloud/Qwen3.8-27B-ko-cjk-suppressed`
   nem skáláz, hanem a célsorokat a célnyelven mért átlagos rejtett állapot
   irányába állítja (`W_i := −α·μ_h/‖μ_h‖²`, α=200). Ez **előjel-független** és
   **kontextusérzékeny** — elvben mindkét tulajdonság jobb, mint a szorzásé. Nálunk
   a szorzás előjel-problémája csak azért nem üt ki, mert megmértük, hogy nem üt ki.
3. **Hogy mennyit fizetünk a durva maszkért.** A koreai munka szándékosan
   **meghagyja** az egykarakteres Han-tokeneket, mert a koreai hanja-glossza legitim
   nyelvi elem. Magyarul ilyen nincs — de ez **feltevés, nem mérés**.
4. **Mennyibe kerül kínaiul.** Egyszer sem mértük meg, mit veszít a modell azon a
   nyelven, amit elfojtunk. A model cardba ez kötelező.
5. **Mekkora a felbontásunk.** Eddig „nem romlott" szerepelt CI nélkül. Egy
   tanulmányban ez nem állítás, csak benyomás.

### Ami a publikálhatóságot eldönti

A KIE- és a szerződéskorpusz **ügyféladat, nem publikálható** — ezek csak belső,
megerősítő evidenciaként szerepelhetnek. Az **elsődleges végpont ezért olyan
korpuszon lesz, ami publikálható**: a `docai-research/magyar-kie-eval` Csapda
Korpusz teljesen **generált, kitalált tartalmú** (`corpus/D1.md`: „kizárólag
tesztelési célra készült, kitalált tartalmú irat"), a ground truth pedig **számolt**
(`gt_szamolo`, `munkarend`, `gen_*`), nem kézzel írt. Ez az egyetlen okból lehet
hivatkozható tanulmányunk.

---

## 1. Kutatási kérdés

> Egy nyelvi modell kimeneti mátrixában egy tokenosztály elnyomása megszünteti a
> nem kívánt nyelvváltást. **Mennyit szabad elvenni, mielőtt fizetünk érte — és
> melyik beavatkozási forma fizet kevesebbet ugyanazért a haszonért?**

Két alkérdés, amit külön mérünk:

- **(A) Dózis:** van-e olyan erősség, ahol a kockázat már nulla, de a képesség még
  sértetlen — és hol?
- **(B) Forma:** ugyanazért a kockázat-nulláért a **szorzás** vagy az
  **irány-alapú csere** fizet kevesebbet, magyarul és kínaiul?

---

## 2. Hipotézisek — előre kimondva, cáfolati kritériummal

Minden hipotézisnél ott van, hogy **mit látnánk, ha hamis**. Ez azért fontos, hogy
a mérés utólag ne legyen átértelmezhető.

### H1 — Létezik ártalmatlan dózis *(elsődleges)*

**Állítás:** van olyan `S*` erősség, ahol a Han-kockázat `t=1,0`-n is nulla
(95 %-os Poisson-felső korlát `< 1/M`), és a magyar képesség-vesztés a 95 %-os
CI-n belül nulla.

**Előrejelzés:** `S* ∈ [0,3; 0,7]`. A csapda-pontszám `S=0,5`-ig a kontrolltól
±2 pontnál közelebb marad, `S=0,1`-en viszont mérhetően (≥3 pont) esik.

**Cáfolat:** ha már `S=0,7`-en CI-t nem átfedő veszteség van (a beavatkozás mindig
drága), **vagy** ha `S=0,1`-en sincs veszteség (nincs kompromisszum, és akkor a
„mennyit szabad" kérdés értelmetlen — rögtön a legerősebb kar megy).

### H2 — Az irány-alapú csere dominálja a szorzást *(elsődleges)*

**Állítás:** a `W_i := −α·μ_h/‖μ_h‖²` forma ugyanazt a kockázat-nullát **kisebb
magyar képességköltséggel** éri el, mint a legjobb kockázat-egyenértékű skálázás.

**Előrejelzés:** az α=200 kar csapda-pontszáma ≥ a kockázat-egyenértékű skálázott
karé, és a kockázata `t=1,0`-n nulla.

**Cáfolat:** ha a csapda-pontszáma **alacsonyabb** a kockázat-egyenértékű skálázott
karénál. (Ez reális kimenet: a −217-es logitplafon durvább vágás, mint egy 0,5-es
szorzó.)

### H3 — Magyarul a durva maszk nem rosszabb *(magyar-specifikus)*

**Állítás:** mivel a magyarban nincs legitim Han-használat, a nyers
tartomány-maszk (55 424 token) **nem rosszabb** a koreai mintájú finomítottnál
(kana + csak-egyszerűsített + ≥2 karakteres tiszta Han).

**Előrejelzés:** a két maszk között egyik magyar műszeren sincs mérhető különbség;
a **kínai** próbán viszont a finomított mérhetően jobb.

**Cáfolat:** ha a finomított maszk magyar oldalon is mérhetően jobb. Ez lenne a kör
legérdekesebb eredménye: azt jelentené, hogy van olyan Han-token, ami a **magyar**
folyamatban hasznos — és akkor meg kell keresni, melyik és miért.

### H4 — A csere kontextusérzékenysége kimérhető

**Állítás:** az irány-alapú csere kínai kontextusban kevesebbet veszít, mint az
azonos magyar hatású skálázás, mert a lehúzás csak a célnyelvi rejtett-állapot
irányában erős.

**Előrejelzés:** kínai próbán α=200 > kockázat-egyenértékű `S`; magyarul nincs
különbség (ez a H2-vel együtt olvasandó).

**Cáfolat:** nincs különbség, vagy fordított.

### H5 — A kockázat-nulla nem hőmérséklet-specifikus

**Állítás:** ami `t=0,6`-on nulla, az `t=0,8`-on és `t=1,0`-n is nulla.

**Előrejelzés:** minden `S ≤ S*` karon mindhárom hőmérsékleten nulla.

**Cáfolat:** bármelyik karon `t=1,0`-n visszatér a jelenség. (A round5 ezt `S=0,5`-re
már megmutatta; itt a többi karra terjesztjük ki.)

### H6 — Átvihetőség *(stretch, elhagyható)*

**Állítás:** a jelenség és a folt hatása nem Qwen3.6-specifikus.

Ha az idő nem engedi, **dokumentáltan kimarad** — nem hallgatólagosan.

---

## 3. A karok — mit építünk

Minden kar **egytenzoros** beavatkozás: csak az `lm_head.weight` változik, a többi
súlyfájl és a teljes FP8 kvantálási állapot **bitre azonos**. Ez nem
kényelmi kérdés: ha a kvantálás változik, a mérés elveszíti az ok-okozati erejét.

| kar | forma | paraméter | maszk | miért ez |
|---|---|---|---|---|
| `K0` | kontroll | — | — | foltozatlan viszonyítás |
| `S07` | szorzás | 0,7 | nyers | a leggyengébb komoly dózis |
| `S05` | szorzás | 0,5 | nyers | **a round5-ben már mért** referencia |
| `S03` | szorzás | 0,3 | nyers | a várt `S*` alsó környéke |
| `S01` | szorzás | 0,1 | nyers | ahol a veszteséget várjuk |
| `A200` | irány-csere | α=200 | nyers | a koreai munka paramétere |
| `A050` | irány-csere | α=50 | nyers | gyengébb változat a dózishoz |
| `S05F` | szorzás | 0,5 | **finomított** | H3 tesztje |
| `A200F` | irány-csere | α=200 | **finomított** | H3+H4 együtt |

`S05` az egyetlen kar, amit már mértünk — **újra kell mérni** ebben a protokollban,
hogy a régi és az új szám összevethető legyen. Ha eltér, a protokoll a hibás, nem a
modell.

### Amit meg kell írni (F0)

1. `patch_lm_head.py` kiterjesztése az **irány-alapú** formára. A `μ_h` becslése:
   magyar szövegen mért átlagos utolsó rejtett állapot, **rögzített, verziózott
   próbahalmazon** (a koreai munka 6 mondatot használt — mi legalább 30-at, és a
   halmaz a csomag része lesz, mert enélkül nem reprodukálható).
2. `smoothie_celtokenek.py` kiterjesztése a **finomított** maszkra: kana +
   csak-egyszerűsített + ≥2 karakteres tiszta Han. Az elhagyott
   (egykarakteres) tokenek listája kerüljön ki külön — ez a H3 vizsgálati tárgya.
3. **Kínai képesség-próba** (új): rövid, determinisztikusan pontozható kínai
   feladatsor, hogy a model cardban számmal lehessen megmondani, mit veszít.
   Nem benchmark-utánzat: 30–40 item, zárt értékkészletű válaszokkal.
4. A **Csapda Korpusz bővítése 50 → 150 itemre**. Ez **blokkoló**: 50 item mellett
   a pass-rate CI-je ±4-5 pont, amivel a „nincs veszteség" állítás felbontása
   rosszabb, mint a keresett hatás. A bővítés módszere külön alfejezet, mert nem
   mindegy, **milyen** itemekkel bővítünk (ld. 4.1.).

### 4.1. A bővítés alapja: valódi bukások, generált adatokon

Nem új, kitalált csapdákat írunk. Az új itemek alapja **az üzleti evalok azon
esetei, ahol a két kar eltért, vagy valamelyik elbukott** — vagyis ahol a
mérésünk már bizonyítottan érzékeny. Amit tudunk, hogy nehéz, azt kell mérni.

A módszer három lépés, és a harmadik a lényeg:

1. **Absztrakció hibaosztályra.** Az egyedi eset helyett a *mechanizmus*: nem „a
   doc2480 negyedik tételsora", hanem „szóközzel szétvágott szám törött táblázatban".
2. **Szintetikus újraírás.** A hibaosztályt új, generált dokumentumba építjük — más
   cégnevek, más összegek, más szövegkörnyezet, **de ugyanaz a csapda**. A meglévő
   `gen_*.py` generátorok mintáját követve, számolt ground truth-tal.
3. **Reprodukciós validáció — enélkül az item nem kerül be.** A foltozatlan
   modellen le kell futtatni: **ha az új item nem produkálja újra a bukást, akkor
   nem azt méri, amit hittünk**, és el kell dobni vagy élesíteni. Ez a kapu tartja
   meg a korpusz érzékenységét.

A round5-ből ismert, dokumentált hibaosztályok, amikkel indulunk:

| hibaosztály | honnan tudjuk | hogyan lesz szintetikus item |
|---|---|---|
| szóközzel szétvágott szám törött táblázatban (`4 0 000` → 4 000) | szerződés-eval, egy tételsor egységára | generált táblázat, ahol a számjegyek közé szóköz kerül |
| kitalált érték `null` helyett (fizetési mód, nulla áfaösszeg ott, ahol nincs áfasor) | KIE, három mező | generált számla **áfasor nélkül** és fizetési mód nélkül |
| kitalált **negatív** tételsorok | KIE, a foltozatlan kar két tételt írt a semmiből | generált számla, ahol a tételszám és a végösszeg nem jön ki triviálisan |
| név/szám összetartozás tételsorban (melyik sorhoz tartoznak a számok) | KIE, a gold maga is elrontotta | generált számla hasonló nevű, egymás alatti sorokkal |
| NUL-bájtos / szavak közé szórt számú PDF-kinyerés | KIE, egy villamosenergia-számla | a generátor szándékosan „törött" szövegváltozatot is kiad |
| hatálybalépés alapja szövegből (`aláírásának napján` → nem `explicit_dated`) | szerződés-eval | generált szerződés, ahol a dátum **szövegben van megfogalmazva**, nem kiírva |
| szereposztás, ahol a séma nem illik (NDA: mindkét fél ugyanaz) | szerződés-eval | generált kétirányú titoktartási szerződés |
| számlázási mód levezetése (óradíjas → használatarányos) | szerződés-eval, 11 eltérés | generált szerződés óradíjas és fix tételekkel egyszerre |
| eldönthetetlen állításra határozott ítélet | csapda `T7-08`, a folt 1/3-ban hibázott | több „nem dönthető el" item, változó megfogalmazással |

**Adatvédelmi kapu — ez a korpusz publikálható lesz.** Az újraírás nem
anonimizálás: a szerkezet marad, a **tartalom teljesen új**. Ellenőrizni kell, hogy
nem szivárgott át szó szerinti részlet: minden új item szövegére **n-gram
átfedés-vizsgálat** az eredeti dokumentum ellen (küszöb: 8 szavas egyező sorozat
már kifogás), és a cégnevek, adószámok, címek, összegek mind generáltak. Az
eredeti dokumentumok **nem** kerülnek a csomagba, és a leképezés (melyik item
melyik eredetiből jött) **belső marad** — a publikált korpuszban csak a hibaosztály
neve szerepel.

---

## 4. A műszerek

| műszer | mit mér | determinisztikus? | publikálható? | szerep |
|---|---|---|---|---|
| Han-kockázat (`t=0,6 / 0,8 / 1,0`) | pozíciónkénti CJK-valószínűség, esemény/M | nem (mintavételezett, 3×) | igen (eszköz) | **elsődleges: haszon** |
| Csapda Korpusz (150 item × 3) | magyar nyelvi/kinyerési helyesség | igen (greedy, exact) | **igen** | **elsődleges: költség** |
| Kínai próba (30–40 item) | mit veszít a célnyelven | igen | igen | H4 + model card |
| KIE (31 dok) | belső kinyerés | igen | nem | megerősítő |
| Contract (30 szerződés) | belső kinyerés | igen | nem | megerősítő |
| Chat (19 szcenárió) | ügynöki viselkedés | **nem, zajos** | nem | csak leíró, **nem végpont** |

A chat szándékosan nem végpont: a round5 kimutatta, hogy a futásközi szórás nagyobb,
mint a keresett hatás (`p = 0,42`), és két stabil hibája **termékhiba, mindkét
modellen**. Ha bekerül, akkor kizárólag „nem látszik különbség" formában.

### Egy szabály, ami a round5-ből jött

**Egy futásból nincs regresszió.** A round5-ben a „T3-regressziót" vissza kellett
vonni, mert a kiindulási oldal egyetlen szerencsés futása volt. Ezért: minden
nem-determinisztikus mérés **legalább 3×**, az elsődleges karokon **5×**, és a
karonkénti szórás bekerül a jegyzőkönyvbe akkor is, ha nem érdekes.

---

## 5. Statisztikai protokoll — előre rögzítve

- **Elsődleges végpontok:** (a) Han-kockázat `t=1,0`-n, (b) Csapda-pontszám.
  Minden más **másodlagos**, és annak is nevezzük.
- **Arányok:** Wilson-féle 95 %-os CI. Karok párosított összevetése ugyanazokon az
  itemeken: McNemar-próba (kis n-nél exact).
- **Nulla esemény:** a `0/M` önmagában **nem eredmény**. Poisson exact 95 %-os
  **felső korlát** kell mellé: „< X/M", a tényleges pozíciószámmal.
- **Többszörös összevetés:** a karok kontroll-ellenes összevetéseire **Holm-korrekció**.
  Nyolc kontroll-ellenes összevetés × két elsődleges végpont — korrekció nélkül a
  véletlen találat gyakorlatilag biztos.
- **Nem-inferioritási margó:** a „nem romlott" állításhoz **előre kimondva −2
  pont** a 150 itemes csapda-pontszámon. Ami ennél kisebb, arról azt mondjuk, hogy
  **a felbontásunk alatt van** — nem azt, hogy nincs.
- **Amit nem teszünk:** nem választunk utólag végpontot, nem hagyunk el kart a
  végső táblázatból, és nem összevonunk hőmérsékleteket, ha a részletek nem
  tetszenek. Minden lefuttatott kar bekerül.

---

## 6. Fázisterv, kapukkal

### F0 — Előkészítés (GPU nélkül, ~1 nap)

1. Az F0/1–4 eszközök megírása (ld. 3. pont).
2. A csapdakorpusz 150 itemre bővítése + a bővítés **saját** konzisztencia-ellenőrzése.
3. A karok előállítása: **8 patchelt snapshot** (a `K0` a foltozatlan modell,
   azt nem kell előállítani), mindegyiknél **ellenőrizve**, hogy a nem célzott
   súlyfájlok `sha256`-a a kiindulóval azonos.
4. A `μ_h` próbahalmaz rögzítése és verziózása.

**Kapu F0, két feltétel:**
- a régi 50 item a kontrollon hozza a korábbi eredményt (átfedő CI) — különben a
  környezet változott, nem a korpusz;
- **minden új item reprodukálja a hibaosztályát** a foltozatlan modellen. Ami nem
  reprodukál, az kimarad — de a **kimaradás ténye és oka** bekerül a
  jegyzőkönyvbe, mert az is információ: azt jelenti, hogy a hibaosztály nem
  általánosítható, csak az eredeti dokumentumon élt.

⚠️ Ennek a bővítésnek van egy fontos következménye a számokra: az így épített
korpusz **szándékosan nehezebb**, mint a mostani 50 itemes, tehát a pass-rate
**esni fog**. Ez nem regresszió — a régi és az új itemeket ezért **külön is**
jelentjük, és a kar-összevetés mindig **párosított**, ugyanazokon az itemeken.

### F1 — Pilot három karon (~5 óra GPU, 1 éjszaka)

`K0`, `S05`, `A200` — mind a hat műszeren, a teljes protokollal.

⚠️ A pilotnak van egy pótolnivalója: a folt **haszonoldalát** (Han-kockázat
`t=0,6/0,8/1,0`) eddig **csak a régebbi motorbuildon** mértük. A `0,0/M` tehát
addig nem állítható az új buildre, amíg az `S05` kar itt újra nem hozza.

Ez nem eredmény, hanem **a protokoll validálása**: kiderül, hogy a futásidők
tarthatók-e, hogy az `S05` reprodukálja-e a round5 számait, és hogy a kínai próba
egyáltalán mér-e valamit.

**Kapu F1 — itt lehet elegánsan leállni:**
- ha az `S05` nem reprodukálja a round5-öt (nem átfedő CI) → a protokoll hibás, javítás
- ha a kínai próba a **kontrollon** sem ad értelmes pontszámot → a próba hibás, újraírás
- ha `K0` és `S05` között a csapdán **nagy** (>5 pont) különbség van → valami más
  változott, mint hittük; keresés, nem folytatás

### F2 — A teljes dózis-sor (~9-10 óra GPU, 1 éjszaka)

A maradék **hat** kar (`S07`, `S03`, `S01`, `A050`, `S05F`, `A200F`). Karonként
~90 perc (modellbetöltés + hat műszer, a nem-determinisztikus részeken 3×), tehát
ez egy teljes éjszaka, tartalék nélkül. Ezután áll össze a dózis-hatás görbe és a
H1–H4 válasza.

**Kapu F2:** ha `S*` nem azonosítható (minden kar vagy fizet, vagy nem tisztít),
akkor a tanulmány **negatív eredményt** közöl, és **modell-release nincs**. Ez
megengedett kimenet, nem kudarc.

### F3 — A győztes kar megerősítése (~3 óra GPU)

5× ismétlés az elsődleges végpontokon, `t=0,6 / 0,8 / 1,0` stresszpróba, és az
**előjel-csapda** célzott újraellenőrzése **több** billenési ponton (a round5-ben
csak egy volt — ez a legvékonyabb pontunk).

### F4 — Termékek (~2 nap, GPU nélkül)

1. **HF-modell** + model card (ld. 8. pont)
2. **Tanulmány** a `/kutatas` rovatba
3. A **blogcikk** frissítése a mért számokkal, és **együtt** publikálás

---

## 7. Publikálási döntési szabály — előre, nem utólag

**Modellt akkor publikálunk, ha mind a négy teljesül:**

1. a győztes kar Han-kockázata `t=1,0`-n `< 1/M` — a pozíciónkénti E[Han]
   válaszonkénti bootstrap 95 % felső korlátja, a tényleges futáson; a Poisson-korlát
   mellette jelentve *(átírva 2026-09-18, ld. Napló: az eredeti Poisson-olvasat
   teljesíthetetlen volt)*,
2. a csapda-pontszáma a kontrollhoz képest **nem esik a −2 pontos
   nem-inferioritási margón túl**,
3. a belső KIE és contract **nem mutat romlást** (per-doksi előjelteszt nem
   szignifikáns, mikroszinten nem esik),
4. a kínai veszteség **számmal megadható** a model cardban.

**Ha bármelyik nem teljesül:** tanulmány igen, modell nem. A tanulmány ekkor azt
mondja meg, hogy **hol van a határ** — ami önmagában használható eredmény.

---

## 8. A HF-release tartalma

**Név:** `Qwen3.6-35B-A3B-FP8-cjk-damped-<kar>` — a `cjk-damped` megmondja, mit
tesz. **Nem** `smoothie` (a HF-en a „smooth" jellemzően SmoothQuant, ami
kvantálási technika), és **nem** `hun` (nincs benne magyar tanítás, a folt nem
látott magyar korpuszt).

**A model card kötelező elemei:**

- **Az első bekezdésben:** ez nem jobb modell, hanem **egy képességet levág**. Akinek
  kínai, japán vagy koreai kimenet kell, annak kártétel — a kanjit ugyanez a
  tartomány fedi.
- A teljes dózis-hatás táblázat, **minden** mért karral, nem csak a győztessel.
- A kínai veszteség száma.
- Amit **nem** mértünk (más modellek, más nyelvek, hosszú kontextus).
- Attribúció: `dnotitia/smoothie-qwen` (a célosztály-definíció onnan, változtatás
  nélkül) és `ThakiCloud/Qwen3.8-27B-ko-cjk-suppressed` (a legközelebbi előzmény,
  irány-alapú csere és nyelvspecifikus maszk).
- Licenc: **Apache-2.0**, a base `Qwen/Qwen3.6-35B-A3B-FP8` szerint; a módosítás
  ténye és pontos leírása feltüntetve.
- Reprodukciós útmutató: patch-szkript, célhalmaz-generátor, `μ_h` próbahalmaz,
  kockázatmérő, és a **publikálható** csapdakorpusz + harness.

**Amit nem tesz bele senki:** `cases.jsonl`, a Han-pozitív teljes rekordok, a KIE- és
szerződéskorpusz, bármilyen ügyfélszöveg. A `_raw-spark-measurements` házirendje
érvényes: **nem publikus**.

**A feltöltést a felhasználó végzi.** Ez a runbook a csomagot állítja össze és
ellenőrzi, nem tölt fel.

---

## 9. Amit előre tudni kell a kockázatokról

| kockázat | mit teszünk |
|---|---|
| a `μ_h` becslés a próbahalmazon túl nem általánosít | a halmaz verziózott és publikált; az érzékenységet két független halmazzal ellenőrizzük |
| nyolc kar × sok műszer → véletlen találat | Holm-korrekció, előre rögzített elsődleges végpont |
| a 150 itemes bővítés más nehézségű, mint az 50 | Kapu F0: a kontrollnak át kell fednie a régi eredményt |
| az előjel-csapda máshol aktív, mint ahol mértük | F3: több billenési pont, célzottan |
| a motorbuild-eltérés konfundál — **bizonyítottan**: a beta-build önmagában +3 csapdapontot és hibátlan KIE-t hoz, foltozatlanul is | minden kar **ugyanazon a build-en**, az alap-image **digestje** a jegyzőkönyvben; címke szerinti hivatkozás tilos |
| a GPU-idő elfogy | a fázisok sorrendje úgy van, hogy F1 után is van közölhető eredmény |

### Egy nyitott üzemeltetési kérdés, ami ide tartozik

Az éles rendszerben a hőmérséklet `0,3`-ra csökkentése **ugyanoda visz, folt nélkül**
(`t=0,3` → ~0,0/M). A folt valódi indoka az az **újrapróbálkozási út**, ami
szándékosan `t=0,9`-en perturbál, hogy kijöjjön egy beragadt hurokból — ott a
hőmérséklet-csökkentés funkciót vinne el. A tanulmánynak ezt ki kell mondania,
különben a folt jelentősebbnek tűnik, mint amilyen.

---

## 10. Eredménylap — a váz, amit ki kell tölteni

```
kar | maszk | Han-kockázat t=0,6 / 0,8 / 1,0 [95% felső korlát]
   | csapda 150×3 [Wilson CI] | kínai próba [CI]
   | KIE F1 | contract F1 | per-doksi előjel p | latencia Δ%
```

Plusz kötelezően:

- a **dózis-hatás görbe** (kockázat és költség egy ábrán, az `S*` megjelölve)
- a H1–H6 mindegyikére egy sor: **igazolt / cáfolt / nem dönthető el**
- egy „amit elrontottunk" szakasz — a round5-ben ez volt a legértékesebb rész
  (a törött mérőműszer és a visszavont regresszió)

---

## Napló

| dátum | mi történt |
|---|---|
| 2026-09-15 | runbook megírva, a hipotézisek és a döntési szabály rögzítve; a round5 beta-build replikációja még fut |
| 2026-09-16 | a beta-build replikáció lezárult (23:42). A folt **nem ront** egyik buildon sem, de a korábban mért **javulás visszavonva** — a motorbuild megmagyarázza. A `t=1,0` Han-kockázat a beta motoron **nincs mérve**: az F1 pilotba beépítve. A karok build-digestje: `sha256:10c361c5…` (beta alap-image) |
| 2026-09-18 | **F0 elindult** (részletes jegyzőkönyv: `jegyzokonyv/F0-naplo.md`). Elkészült: a kétmaszkos céltoken-eszköz (a nyers maszk **55 424** — bitre a round5 száma), a két μ_h próbahalmaz és a becslés, a kínai próba (36 item), a Csapda Korpusz bővítése **150 itemre** (9 generált irat, 385 konzisztencia-ellenőrzés), a statisztikai eszköztár és a karépítő + igazoló. |
| 2026-09-18 | ⛔ **Elkerült mérési hiba.** A μ_h becslés első változata `transformers`-szel töltötte be a checkpointot; a MoE szakértősúlyok elrendezése nem egyezik (szakértőnkénti vs. fúzionált), ezért **mind a 40 réteg összes szakértője véletlenszerűen inicializálódott**, miközben a betöltés és az akkori önteszt hibátlannak látszott. Átállás vLLM `token_embed` poolingra + **tanári kényszerítéses** önteszt (top-1 66,0 % / 65,4 %). |
| 2026-09-18 | ⭐ **μ_h érzékenység-ellenőrzés (§9) teljesül:** `cos(μ_h^A, μ_h^B) = 0,8893` két, tárgykörében és regiszterében független 30-itemes halmazon. A karok az **A** (termékközeli) halmazzal épülnek. |
| 2026-09-18 | ⚠️ **A GPU-költségvetés nem tartható a tervezett formában.** Mért: a csapda-korpusz sorosan **40 s/kérés**, azaz 150 item × 3 futás = **~5 óra karonként** — kilenc karral 45 óra, a runbook F2-re egy éjszakát szánt. A harness és a kínai próba **párhuzamosítva** (6 item egyszerre, ~84 perc/kar). ⛔ A párhuzamosítás a mérési körülményt megváltoztathatja (kötegméret-függő numerika greedy mellett), ezért a bevezetése előtt item-szintű, bájtra menő igazolás fut a sorossal szemben (`eszkozok/parhuzam_ellenoriz.py`); a kötegméret minden karon azonos, és a jegyzőkönyvbe kerül. |
| 2026-09-18 | **Végpont-pontosítás.** Az elsődleges költség-végpont **item-szintű pass-rate** (egy item átmegy, ha minden GT-mezője pontosan stimmel), nem a súlyozott, részpontos pontszám: az utóbbin nincs értelmes párosított próba és zárt alakú CI, a §5 viszont arányokat ír elő. A súlyozott pontszám **másodlagos** végpontként megmarad, és a régi 50 itemre külön is jelentjük (enélkül a round5-összevetés nem elvégezhető). |
| 2026-09-18 | ⭐ **ELŐJEL-CSAPDA MÉRVE — a §9 „legvékonyabb pontja".** A szorzásos folt a NYERS eloszlásban **megnöveli** a Han-tömeget: `t=1,0`-n 10,53 % → 13,35 % (S=0,7) → 16,14 % (S=0,5), mindkét μ_h halmazon, dózisarányosan. Ok: a célzott sorok **96,4 %-ának negatív a logitja** a magyar átlagállapotban, a `0<S<1` szorzó pedig nulla felé tolja. A prod mintavételezés (`top_k=20`) viszont levágja a farkat: csonkolás után a tömeg mindkét karon **0,000000 %**. Vagyis a folt nem azért hatásos, mert elveszi a Han-tömeget, **hanem mert a mintavételező levágja azt a tartományt, ahol a tömeg ül**. Az irány-alapú csere (`A200`) ezzel szemben **pontosan nullára** viszi a nyers tömeget is (0/55 424 sor logitja nő). Model card-kötelező; a H2 mechanizmusa igazolva, a képességköltsége még nem. |
| 2026-09-18 | **Döntés — a H1 küszöbe (§2/H1).** A „Poisson 95 % felső korlát < 1/M" a megfigyelt eseményszámra alapozva ~3 millió generált pozíciót igényelne; egy kar felvétele ~14 000 pozíció, a korlát tehát ~220/M. Az elsődleges HASZON-végpont ezért a **pozíciónkénti E[Han] = Σp** becslés (ez a round5 tényleges mérőszáma is), a bizonytalanság **válaszonkénti bootstrap** 95 % CI-vel; a válasz a független megfigyelési egység. A megfigyelt eseményszámra épített Poisson-korlát **mellette** marad jelentve, hogy a gyengesége látszódjon. Mért igazolás a round5 adatán: `cron` t=0,6 → 8,44/M [2,26; 15,22], t=1,0 → 87,95/M [58,90; 114,33]; `smoothie-0,5` → **exact nulla, CI [0,00; 0,00]** minden beállításon. |
| 2026-09-18 | **Döntés — a nem-inferioritási margó (§5) egyértelműsítése.** „−2 pont a 150 itemes csapda-pontszámon" **szó szerint** értendő: −2/150 = **−1,333 százalékpont**, nem −2 százalékpont. Ez a szigorúbb olvasat. |
| 2026-09-18 | **Döntés — az F0-kapu alkalmazása (§4.1/§6).** A kapu szó szerinti olvasata (a K0 által ÁTMENT új itemek kimaradnak) **padló-hatást** okozna: ha a kontroll elbukja az itemet, a foltozott kar is elbukja, és a VESZTESÉG — e kör elsődleges kérdése — épp nem látszik. Ezért **minden item marad**, a jelentés viszont **rétegzett**: a `K0 átment` réteg méri a folt ÁRÁT (itt van fejtér lefelé), a `K0 bukott` réteg a JAVULÁST (itt van fejtér felfelé). A kapu nem itemeket dob ki, hanem azt köti ki, melyik réteg melyik állítást hordozhatja. Egyik réteg sem marad ki a végső táblázatból. |
| 2026-09-18 | ⭐ **KAPU F0 / (1) TELJESÜL.** A régi 50 item a kontrollon **item-szinten párosítva** hozza a round5 beta-buildes eredményét: 49/50 vs. 49/50, **97,00/100 vs. 97,00/100**, McNemar exact p = 1,0000, két item cserélődik oda-vissza (`T3-02`, `T7-08`). A környezet nem változott, és a párhuzamosított mérés a régi számot adja vissza. |
| 2026-09-18 | **A műszer saját zaja MÉRVE.** A három greedy futás külön pontozva: a nyers szöveg 32/79 itemen eltér, a **pontszám 2-nél**, a **PASS/FAIL 1-nél** (a részleges, 79 itemes állás; a teljes 150-en 3/150 = **2,00 pp**). Ez eléri, majd a teljes futáson meg is haladja a −1,33 pp-os nem-inferioritási margót, tehát a margó közelébe eső eltérés **nem különböztethető meg a műszer zajától**; a §5 „a felbontásunk alatt van" fordulatához ezzel van szám. Eltérés a §4-től: a csapdán 3× ismétlés marad az elsődleges karokon is (az 5× +67 % GPU-idő, a mért zaj mellett indokolatlan); ha egy kar a margó közelébe esik, azt a kart külön, 5×-tel újramérjük. |
| 2026-09-18 | **KAPU F0 / (2) — VÉGLEGES.** A kontroll a 150 itemen **144/150 = 96,0 %** [91,5–98,2], 192,50/200 pont; az új 100 itemen **95/100 = 95,0 %**. ⭐ A **C9 (eldönthetetlen állítás)** osztály reprodukál: **7/11**, és a négy bukásból **három a „nem dönthető el" kategória** — vagyis a `T7-08`-ból absztrahált hibaosztály az új, generált iraton is él. A `C4` osztály 10/11. A `K0 bukott` réteg 5 item: a VESZTESÉG mérésére 95 item fejtér van, a JAVULÁSRA kevés — az utóbbira vonatkozó állítás gyenge lesz, és így kell leírni. A 150-ből **72 itemnél** eltér a három greedy futás nyers kimenete, tehát az itemek a döntési határ közelében vannak. |
| 2026-09-18 | ⛔ **A műszer zaja (2,00 pp) MEGHALADJA a −1,33 pp-os margót.** A három greedy futás külön pontozva: nyers szöveg 72/150-en eltér, **pontszám 4-nél**, **PASS/FAIL 3-nál**. A felbontásunk tehát ≈2 pp, nem 1,33 — a margón belüli eltérés **nem különböztethető meg a műszer zajától**. A §5 „a felbontásunk alatt van" fordulatához ezzel van szám. |
| 2026-09-18 | ⚠️ **A H3 olvasatát érintő lelet, a mérés ELŐTT rögzítve.** A finomított maszk **3 964 egykarakteres tiszta Han tokent meghagy**, köztük a kínai gyakorisági élmezőnyt (`的 一 不 是 有 我 你`), plusz 88 CJK-írásjelet; cserébe 3 571 kana tokent hozzávesz. A runbook hallgatólagosan feltette, hogy mindkét maszk nullára viszi a kockázatot — ez most már nem magától értetődő. A protokoll nem változik: a H1/H5 kockázatmérés minden karon lefut, tehát ez MÉRVE lesz. |
| 2026-09-18 | ⛔ **A PÁRHUZAMOSSÁG-KAPU MEGBUKOTT — az F1 első indítása leállt** (16:08, részletek: `jegyzokonyv/F1-naplo.md`). A 12 itemes igazoláson 9/12 sha egyezik, de a `T7-08` itemen a **PASS/FAIL is átbillen**: párhuzamosan 3/3 átment, sorosan 3/3 elbukott. Ez nem zaj, hanem feltételhatás, és épp akkora, mint a mérni kívánt hatás → **konfundál**. A `T7-08` ráadásul az az item, amiből a C9 hibaosztályt absztraháltuk. |
| 2026-09-18 | **Protokollváltozás (§4, §6) — a csapda és a kínai próba SOROSAN fut, ismétlés nélkül.** A §6 két remedy-ága közül az elsőt („soros mérés") választjuk, mert **nem kerül többe**: a soros dekódolás bitre reprodukálható (12/12 item, 3/3 azonos sha), így az ismétlés elhagyható. Mért: `parallel=6 × 3 futás` = 450 kérés ≈ 108 perc/kar → `parallel=1 × 1 futás` = 150 kérés ≈ **46 perc/kar** (61,1 kimeneti token/s). A §4 ismétlés-előírása helyébe lép: **a kontrollon 3×** (a determinizmus bizonyítékaként), a többi karon 1×. A Han-szonda mintavételezett, ott az ismétlés marad. A kapu helyére a **soros determinizmus igazolása** lép a teljes 150 itemen (`eszkozok/determinizmus_ellenoriz.py`), és az F1 ott is megáll, ha bukik. |
| 2026-09-18 | ⚠️ **Az F0 két lezárt száma visszanyílt, mert párhuzamos műszeren született.** (1) A Kapu F0 mindkét ágát a **soros** K0-n kell újra kimondani; a párhuzamos futás `csapda-K0-parhuzamos6.json` néven archiválva marad (ez a bizonyítéka a kötegméret-hatásnak). (2) ⭐ A „**2,00 pp műszerzaj**" nem a műszeré volt, hanem a párhuzamosításé — sorosan a 12 item mindhárom ismétlése bájtra azonos. Ha ez a 150-en is igazolódik, a **−1,33 pp-os margó újra használható**. ⛔ Ez még előrejelzés, nem eredmény. **Előre rögzített, cáfolható előrejelzés:** a round5-höz képest cserélődő két item (`T3-02`, `T7-08`) közül a `T7-08` a soros K0-n a round5-tel EGYEZNI fog, tehát a csere 2-ről legfeljebb 1-re csökken. Ha nem, van egy meg nem értett szabadsági fok, és publikálás előtt meg kell keresni. |
| 2026-09-18 | **Korlát, kimondva:** a belső, megerősítő műszerek (KIE, contract) továbbra is párhuzamosan futnak (a contract `--parallel 3`). Minden karon azonos a beállítás, így az aggregált összevetés áll, de **item-szintű állítás belőlük nem tehető**. A tanulmány korlát-szakaszába bekerül. |
| 2026-09-18 | **Döntés — a §7/1 publikálási feltétel átírva** (menet közbeni önellenőrzés). A szó szerinti „Poisson 95 % felső korlát < 1/M" nulla eseménynél is ~200/M-es padlót ad a kar ~15 000 pozícióján, tehát a modell **soha nem lett volna publikálható** — a H1-döntés ezt nem vezette át a §7-be. Mostantól a §7/1: **a pozíciónkénti E[Han] válaszonkénti bootstrap 95 % felső korlátja `< 1/M` a `t=1,0` tényleges futáson** (exact nullánál `[0; 0]`, tehát elérhető). A Poisson-korlát **mellette jelentve marad**, mint a megfigyelt eseményszám gyengeségének mutatója. |
| 2026-09-18 | **Önellenőrzés — négy tisztázás, változtatás nélkül.** (a) ⛔ Rés a párhuzamosság-kapuban: a párhuzamos és a soros mérés **két kiszolgáló-példányon** futott, a karok összevetése pedig mindig két példány között történik → `eszkozok/k0_ujpeldany.sh` az F1 után friss példányon újraméri a K0-t sorosan, és ugyanazon a példányon a 12 itemet `parallel=6`-tal. A round5 archívum már most valószínűtleníti a példányhatást (a beta-build két lokális szekvenciális futása 0/50 instabil; a `T7-08` szövege bájtra azonos két nap, két példány távlatából), a `t237` szondák instabilitása a **megosztott távoli** kiszolgálóé. (b) A nem-inferioritás „teljesül" verdiktje 150 itemen egyetlen elvesztett itemnél sem érhető el (`CI [−1,97; +0,64]`); a realisztikus kimenet a „felbontás alatt", amit a §7/2 elfogad. A determinizmus a *műszer* zaját nullázta, a *statisztikai* felbontást nem. (c) A haszonoldali dózis-hatás a prod-mintavételen **lépcső**, nem görbe (előjel-csapda: `top_k=20` mellett minden S-kar exact nulla); a Han-szonda 3 eset × 5 ismétlés kontroll/folt szétválasztásra elég, karok rangsorolására nem — a finom haszon-felbontás az offline nyers-tömeg eszköz. (d) Korlát: a költség greedy-n, a haszon `t=0,6–1,0`-n mérve; F3-ban a győztes karra `t=0,6`-os csapda-futás is. `tie_word_embeddings: False` ellenőrizve — a folt csak a kimeneti oldalt éri. |
| 2026-09-19 | ⭐ **KAPU F1 TELJESÜL** (mind a három feltétel; jegyzőkönyv: `jegyzokonyv/F1-naplo.md` §8). `S05` Han-kockázat exact 0, CI `[0; 0]` mindhárom hőmérsékleten; kínai próba a kontrollon 36/36; `K0` vs `S05` a csapdán Δ = 0. |
| 2026-09-19 | ⭐ **A magyar csapda greedy alatt NULLMŰSZER — konstrukcióból.** `K0` ≡ `S05` ≡ `A200` 150/150 itemen bájtra azonos (round5 alap ≡ round5 S05 is 50/50). A folt csak Han-sorok logitját változtatja, azok magyar szövegen soha nem argmaxok; mintavételnél is csak a csonkolt tartóban lévő Han-nál térhet el → **a nem-célnyelvi költség felülről korlátos a nem-célnyelvi Han-kockázattal**. A H1 magyar ága ezzel minden dózisra cáfolva; a §4–§5 „csapda-pontszám" költség-végpont tartalmatlan, a csapda **negatív kontrollként** marad (fantomhatás-teszt). A költség tengelye a **kínai próba**. |
| 2026-09-19 | ⭐ **A költség a kínain totális már S = 0,5-nél:** `K0` 36/36 → `S05` **1/36 (2,8 %)**, 35/36 válaszban egyetlen Han sincs → `A200` **0/36**. McNemar p < 10⁻⁴, Holm után is. Ez a model card száma. A dózis-hatás valódi tengelye a kínai; az F2 kérdése: van-e dózis, ahol a magyar kockázat 0, de a kínai él. Mellék: `A200` a gondolkodásban `t=0,8`-on 5 Han-tokent generált (válaszban 0) — H3-releváns, F2 után vizsgálandó. |
| 2026-09-19 | ⛔ **A KISZOLGÁLÓ-PÉLDÁNY a késélen ülő itemeket átbillenti.** Friss példányon a `K0` 5/150 item PASS/FAIL-jében tér el a determinizmus-kapun átment `K0`-tól; példányon belül minden bitre stabil (150/150, meleg cache 17/17, `parallel=6` 0/12 PASS-eltérés). Példány-sorozat: 4 sima példány → **3 különböző mintázat** a 17 itemen (időzítés-alapú kernelválasztás gyanús: `enable_flashinfer_autotune`, `benchmark_combo_kernel`). **Helyesbítés:** a tegnapi „a 2,00 pp zaj a párhuzamosításé" félig igaz — a példány önmagában is billent, hasonló nagyságrendben; a párhuzamosság-kapu két példányon futott, két hatást mért össze. Mentőöv: a nullműszer-tulajdonság miatt bármely kar bájteltérése `K0`-tól példányzaj, nem folthatás — elkülöníthető. Az F1 három karja egyazon numerikába esett (5 példány, 3 súlykészlet, bájtra azonos), ezért a Kapu F1/3 „tisztán" teljesült — szerencse, nem garancia. A `VLLM_BATCH_INVARIANT=1` mód FlashInfer-rel nem indul; `TRITON_ATTN`-nel próba folyik. **F2 az eredményéig nem indul.** |
| 2026-09-19 | ⭐ **VAN DETERMINISZTIKUS MÉRÉSI ÚT: `VLLM_BATCH_INVARIANT=1` + `--attention-backend TRITON_ATTN`.** Két friss példány **17/17 bájtra azonos**, és ugyanazon a példányon a `parallel=6` is 12/12 azonos a sorossal. ~12 % lassabb sorosan, de a párhuzamosítás rajta ártalmatlan → csapda ~21 perc/kar. Ez **motorváltás** (a numerika a sima példányokétól eltér, negyedik mintázat), tehát az F2 csak akkor épülhet rá, ha a `K0`, `S05`, `A200` is újra lefut rajta; a round5-összevetés a sima motoron marad (ott teljesült). **Döntést kér: melyik motoron fusson az F2.** |
| 2026-09-19 | **Döntés — az F2 a SIMA motoron fut, ahogy eddig** (a BI-út a tanulmányban leírva marad, mint a reprodukálhatóság mért alternatívája). Következmények, előre kimondva: (1) minden kar-összevetésben benne marad a példányzaj (±2–5 item/150); (2) a magyar csapdán bármely eltérés a `K0`-tól **példányzajként jelentendő**, nem folthatásként — a nullműszer-tulajdonság miatt ez nem feltevés, hanem levezetett tény; (3) a kínai próba (36 item, greedy) ugyanennek a zajnak van kitéve, a késélen ülő karokat (ahol a kínai részben él) ez korlátozza — az F3 megerősítés ott több példányon fut; (4) a soros mérés marad (`parallel=1`), mert a sima motoron a kötegméret is billent. |
| 2026-09-19 | ⭐ **F2 LEZÁRULT (13:00–22:35), mind a kilenc kar mérve** — `jegyzokonyv/F2-naplo.md`. **Kapu F2: `S*` azonosítható = `S07`** — az egyetlen kar, ahol a magyar Han-kockázat exact 0 (prod-úton és `t=1,0`-n) ÉS a kínai próba a kontrollal azonos (36/36). A dózis-hatás **két lépcső**: a haszon már S = 0,7-nél nulla, a költség (kínai) 0,7 és 0,5 között zuhan 100 % → 2,8 %. |
| 2026-09-19 | **Hipotézisek (előzetes):** H1 *cáfolva minden dózisra* (a magyar greedy kimenet bájtra érintetlen S = 0,1-nél is; a költség egésze a kínain); H2 mechanizmus igazolt, „olcsóbb" cáfolva (`A050` is 0/36 kínai); **H3 cáfolva** (`S05F` 19,4 %, `A200F` 2,8 %); **H4 cáfolva** (`S05F` `t=1,0`-n 11,3/M, `A200F` a prod-úton 4,3/M és valódi Han a válaszban); H5 igazolt a kontrollon; H6 igazolt. |
| 2026-09-19 | **Példány-módok, végleges kép:** 13 példány → legalább 4 diszkrét numerika-mód, az azonos módúak bájtra reprodukálják egymást (`S01` ≡ `S05F` ≡ `K0`-inst2 a csapdán 150/150 ÉS a belső KIE/contract számjegyre). A csapda nullműszer-tulajdonsága miatt minden kar módja azonosítható → a kar a vele azonos módú `K0`-hoz hasonlítandó. A §7/3 „belső KIE/contract nem romlik" így értendő: azonos módú karok azonos számot adnak; a módok közti ±0,02 példányzaj. |
| 2026-09-19 | **F3 terv (a §6 szerint a győztes megerősítése), kiegészítve:** `S07` 5× Han-szondával, ≥3 példányon, `t=0,6`-os csapdával; az ablak két széle: `S06` (kínai lépcső) és `S08`/`S09` (haszon-lépcső). F3 **nem indul magától**. |
| 2026-09-19 | ⛔ **MÉRÉSI KORLÁT a HASZON-végponton (a felhasználó vette észre).** A Han-szonda `raw_logprobs` módban rögzíti a top-20-at, a `han_kockazat.py` pedig erre a NYERS top-20-ra alkalmazza a mintavételezési láncot (presence_penalty → temperature → top_k → top_p; a repetition_penalty csak jelezve). A vLLM viszont a büntetéseket a top-k **előtt** alkalmazza: a `presence_penalty=1,5` a már látott tokeneket lenyomja, így a nyers 21+. helyezett bejuthat a tényleges top-20-ba — a számítás ezt nem látja. Az előjel-csapda miatt az S-karoknál épp a Han-tokenek másznak felfelé. **Következmény: az „exact nulla" a nyers top-20-ra bizonyított, a tényleges mintavételezői tartóra nem.** A ténylegesen megfigyelt 0 esemény (S07: ~13 000 pozíció, Poisson < 500–860/M) az egyetlen közvetlen bizonyíték, és gyenge. A fejléc-korlát („a becslés alsó korlát") ezt takarta, de a prod-döntésre nézve alulértékeltük. |
| 2026-09-19 | **Döntés — F3 tartalma és sorrendje (felhasználó):** (1) a kockázatmérés igazolása a büntetések és csonkolás **utáni tényleges** eloszláson (a kiszolgáló `--logprobs-mode processed_logprobs` módjában a visszaadott top-20 = a tényleges top-k tartó); (2) `S07`–`K0` megerősítés több friss példányon, változatosabb bemenetekkel és seedekkel, a tényleges prod-beállításokon, **beleértve a `t=0,9`-es újrapróbálkozási utat és az éles párhuzamosságot**; (3) ha rendben, kis forgalmú, visszaállítható **prod-próba `S07`-tel**, Han-előfordulás és feladatminőség követésével. A prod-próba az `S07` saját megerősítését megvárja, az új karokat nem. Új karok prioritása: **S08** (elég-e kisebb beavatkozás), **S09** ha S08 jó, **S06** a tanulmányhoz (hol omlik össze a kínai), prodhoz másodlagos. |
| 2026-09-19 | **F3 elindult** (`eszkozok/f3_vezenylo.sh`, ~10 óra), három fázisban: **A)** a kockázatmérés igazolása a tényleges eloszláson — a kiszolgáló `--logprobs-mode processed_logprobs` módban, `K0` és `S07`, három prod-profil (alap `t=0,6`; alap `t=0,3` = a `config.py` mai `cron_llm_temperature` alapértéke; újrapróbálkozás `t=0,9 / top_p 1,0 / pp 1,8` = `LOOP_RETRY_*`, legfeljebb 1×), 5 seed, plusz a **150 itemes csapda a prod-profilon logprobbal** (~165 000 nem-ügyfél magyar pozíció; a harness új `--logprobs-ki` kapcsolója a szonda rekordformátumát írja); kiértékelés `han_kockazat.py --feldolgozott` (E[Han] = Σ exp(lp) a tényleges tartón, lánc nélkül). **B)** `S07`–`K0` megerősítés a sima motoron: 3 friss `S07`- és 1 friss `K0`-példány, ugyanaz a 3 profil × 5 seed, egy 3-szálas párhuzamos köteg (éles terhelés), csapda a prod-profilon `parallel=6`, 3×. **C)** `S08` → `S09` → `S06` az F2-protokollal, Han 5×. ⚠️ Eltérés: a szonda `cron` profilja `t=0,6`-ot küld (a vizsgált futás kódállapota), a mai `config.py` `0,3`-at mond — az éles érték a felhasználónál; mindkettő mérve. ⚠️ Próbafutás-lelet: az `A200F` a csapda 2 itemjén prod-mintavétel alatt **9 valódi Han-tokent** generált a gondolkodásban (4 685/M) — a H4-cáfolat a nem-ügyfél korpuszon is áll. |
| 2026-09-19 | **Prod-kontextus (felhasználó) és az F3 döntési szabálya, az adat ELŐTT rögzítve.** Az éles cron régebben `t=0,6`-tal futott; **tűzoltásként `0,3`-ra állt**, mert így kevesebb a kínai karakter — a cél az, hogy a folttal **vissza lehessen menni `0,6`-ra**. Ezért az F3 A/B fázisában a viszonyítási alap nem a `K0 @ 0,6`, hanem a **mai éles állapot: `K0 @ 0,3`**, a jelölt pedig **`S07 @ 0,6`** (+ az újrapróbálkozás `@ 0,9`). A prod-próba akkor javasolható, ha (1) a tényleges tartón mért E[Han] `S07 @ 0,6`-on **nem nagyobb**, mint `K0 @ 0,3`-on (ideálisan exact nulla, és `K0 @ 0,3` a kontrafaktuális F1-mérés szerint maga is ~0 volt — tehát a szabály a gyakorlatban „exact nulla az `S07 @ 0,6` és `@ 0,9` tartóján"); (2) a csapda a prod-profilon (`parallel=6`, 3×) `S07 @ 0,6`-on nem rosszabb, mint `K0 @ 0,6` (a példányzaj ±2–5 itemen belül); (3) a három friss `S07`-példány egyike sem mutat valódi Han-eseményt a válaszban a 3×5 seed + párhuzamos köteg alatt. A kínai veszteség `S07`-nél nulla (36/36), tehát a §7/4 model card-feltétel triviálisan teljesül. |
| 2026-09-20 | ⭐ **F3 A) + B) KÉSZ (07:46) — `S07` a prod-próbára javasolható.** Jegyzőkönyv: `jegyzokonyv/F3-naplo.md`. A tényleges tartón (`processed_logprobs`): `S07 @ 0,6` **exact 0**, `@ 0,3` **exact 0**, `@ 0,9` újrapróbálkozás **0,45/M** [0,04; 1,17] (nem exact nulla, 0 esemény); `K0 @ 0,6` 73/M, `@ 0,3` **392/M + 4 valódi Han**, `@ 0,9` 306/M + 3. Sima motoron 3 friss `S07`-példány × 15 seed × 3 profil + párhuzamos köteg + 150 irat (~249 000 poz.): **0 Han-token bárhol**; `K0` ugyanezeken a seedeken 65. Csapda prod-profilon: `S07` 146/150 = `K0`, pontban jobb (194,5 vs 191,0), formátumsértés 0 vs 2. A döntési szabály mindhárom feltétele teljesül. |
| 2026-09-20 | ⛔ **KÉT KORREKCIÓ.** (1) A nyers-top-20-as kockázatszámítás a kontrollt **~10×** alulbecsülte (`K0 @ 0,6`: 5,5/M → 73/M a tényleges tartón) — az F1/F2 eredménylap `K0`-számai alsó korlátok; a foltok exact nullái a tényleges tartón is állnak, kivéve `S07 @ 0,9` (0,45/M). (2) **A `t=0,3`-as tűzoltás nem szünteti meg a kockázatot**: `K0 @ 0,3` a tényleges tartón 392/M és 4 valódi Han 7 869 válaszpozíción — több, mint `0,6`-on. Mechanizmus: a vLLM a büntetést a hőmérséklet-osztás ELŐTT teszi a logitra, alacsony hőmérsékleten tehát erősebben hat (1,5/0,3 = 5), és több helyet nyit a top-20-ban. n kicsi, de a 4 esemény valódi. Következmény: a mai éles állapot **nem biztonságosabb**, mint a `0,6`; az `S07 @ 0,6` mindkettőnél szigorúan jobb. |
| 2026-09-20 | **Korlát:** a három friss `S07`-példány trajektóriája egymással 15/15 azonos (ugyanaz a numerika-mód) — a példányok közti függetlenség kisebb a tervezettnél. A trajektória-azonosság `K0` és `S07` között (`0,3`: 15/15; `0,6` és `0,9`: 13/15, az eltérők épp a Han-billenések) a mechanizmus újabb közvetlen bizonyítéka. |
| 2026-09-20 | ⭐ **F3 C) KÉSZ (13:02) — az ablak mindkét széle bemérve.** `S09`: kínai 36/36, de `t=0,8`-on **16,9/M** → szivárog. `S08`: kínai 36/36, prod-úton (`0,6`, `0,8`) exact 0, `t=1,0`-n 1,6/M (nyers módszer; a tényleges tartón nem mérve). `S06`: kínai **20/36 = 55,6 %**, Han exact 0 → a költség-lépcső **0,7 és 0,6 között** van (nem 0,7/0,5). **`S* = S07` marad**: a legkisebb dózis, ami minden hőmérsékleten exact nulla ÉS ép kínai; közvetlenül a költség-lépcső szélén, a haszon-lépcsőtől egy lépéssel beljebb. Az `S08` a haszonoldalon majdnem egyenértékű, de a tényleges tartón igazolatlan és a kínain nem ad többet. Példány-mód: az `S08`/`S06` egy 5. módba esett (16 példány, 5 mód). Eredménylap 12 karral: `eredmenyek/eredmenylap.txt`. **F3 lezárva; a prod-próba a felhasználóé; F4 (HF-csomag, tanulmány, cikk) következik.** |
| 2026-09-20 | **F4 ELKÉSZÜLT — a csomag, a tanulmány és a cikk együtt, a §8 szerint.** (1) **HF-csomag**: `hf-release/Qwen3.6-35B-A3B-FP8-cjk-damped-S07/` a mérőgépen (55 fájl, 54 bájtra az alap, az átírt shard sha256 = build-rekord; `eszkozok/hf_csomag.sh` építi és ellenőrzi), model card angolul (`hf-release/README.md`: az első bekezdés a képességlevágásról, a teljes 12 karos tábla, a kínai veszteség, a nem mért dolgok, attribúció, Apache-2.0, reprodukciós útmutató, a mintavételezői kitétel), `reproduction/` a publikálható eszközökkel. **A feltöltést a felhasználó végzi.** (2) **Publikus mérési könyvtár**: `docai-evals/experiments/2026-09-18-cjk-damping-dose-response-gb10/` (README a nyolc kérdéssel, eval-card sémára validálva, decision-record, code/, protocol/ = a runbook + jegyzőkönyvek tisztított másolata, dataset/ = csapdakorpusz + kínai próba + μ_h + maszkok, results/ minden karral, figures/); `eszkozok/docai_evals_csomag.sh` építi, a belső gépneveket/IP-ket/útvonalakat kicseréli; ügyféladat nincs benne. (3) **Tanulmány**: `docai.hu/kutatas/cjk-csillapitas` (ResearchController + Blade + 3 ábra), (4) **blog** HU+EN: `/blog/kinai-szavak-a-magyar-valaszban`, `/en/blog/chinese-words-in-the-hungarian-answer`. A 2026-09-16-i cikkterv **nem frissítés, hanem átírás** lett: a §9 „a 0,3 ugyanoda visz" állítását az F3 cáfolta, a §6–7 számai a nyers módszerrel készültek. Ábrák: `article/abrak_f4.py` (SVG → PNG). Git: a felhasználó commitol (docai_web, docai-evals); a sitemap commit után generálandó. |
| 2026-09-20 | ⛔ **Önellenőrzés a lezárás után** (a felhasználó kérésére): független újraszámolás a nyers rekordokból (`eszkozok/han_ujraszamol_mind.py` → `eredmenyek/f3/ujraszamolas-minden-rekord.txt`), plusz a csapda pass-számai, bájt-azonossági csoportjai, a kínai próba és a McNemar újraszámolva. **A táblák számai egyeznek, a következtetés áll.** Négy javítás ([F3-naplo.md](jegyzokonyv/F3-naplo.md) §6): (1) a `han_kockazat.py` a végső válasz nélküli rekordokat (eszközhívásos körök, elszabadult generálások) gondolkodásostul kihagyja — minden rekordot számolva az `S07` továbbra is **0 Han** ~1,09 M különböző pozíción (Poisson < 2,8/M), a `K0` viszont az újrapróbálkozási úton egy rekordban **6 593 Han-tokent** generált, amit a F3 §2 tábla „0 / 0"-nak mutatott; (2) az újrapróbálkozási profil (`t=0,9 / top_p=1,0`) a folttól függetlenül elszabadul (15-ből 2, `K0`-n és `S07`-en is) — a folt a Han-t veszi el, a degenerációt nem; (3) az `S07 @ 0,9` 0,45/M-je **alsó korlát** (top-k holtversenyek, a pozíciók ~4 %-án a tartó > 20); (4) a „~10×" pontbecslések hányadosa (6–13×, három eset), nem mért szorzó. Szövegpontosítás: a nullműszer bájt-azonossága 8 karon **mért**, `S08`/`S06`/`A050` módjában nincs `K0` → ott levezetett; a §7/1 bootstrap-szabály nullánál degenerált, az exact nulla strukturális állítás. A model card, a docai-evals README/decision-record, a tanulmány és a blog ennek megfelelően javítva. |
| 2026-09-21 | **HF-feltöltés kész** (a felhasználó végezte, `hf upload-large-folder`, `k3dani` névtér): <https://huggingface.co/k3dani/Qwen3.6-35B-A3B-FP8-cjk-damped-S07>, publikus. Ellenőrizve a HF API-n: 69 fájl (55 modellfájl + `reproduction/` 13 + `.gitattributes`), helyi és távoli fájlkészlet azonos, az `outside.safetensors` sha256-a = `KAR.json` (`3cbfe634…0bfc5`). A Xet-dedup a 40 réteg-shardból 40 MB új adatot töltött — független jelzés, hogy csak az átírt shard tér el az alaptól. A HF-link beírva a tanulmányba, a két blogba és a docai-evals README-be / decision-recordba. |
