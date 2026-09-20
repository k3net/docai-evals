# F0 jegyzőkönyv — előkészítés

> A runbook §0 szabálya: ami menet közben változik vagy kiderül, **dátummal és okkal**
> ide kerül, nem csendben. Ez a fájl az F0 fázis mért leleteit rögzíti, beleértve azt is,
> ami elromlott.

Gép: measurement-host (<remote-host>) · motor-image: `vllm-openai:beta-mirror-dev328`
(vLLM `0.19.1rc1.dev328+g18013df6a`, alap-image digest
`sha256:10c361c5ae827135451100bc30802ccc1239da654ce2a5febc25a602b2a47c8b`) ·
modell: `Qwen/Qwen3.6-35B-A3B-FP8`, snapshot `95a723d08a9490559dae23d0cff1d9466213d989`

---

## F0/2 — céltokenek, két maszk · 2026-09-18

Eszköz: `eszkozok/celtokenek.py`, `eszkozok/unihan_egyszerusitett.py`
Kimenet: `eredmenyek/celtokenek.json`

| | tokenek | a vocab %-ában |
|---|---:|---:|
| vocab (tokenizer) | 248 077 | |
| `lm_head` sorok | 248 320 | |
| **nyers** maszk | **55 424** | 22,34 % |
| **finomított** maszk | **54 939** | 22,15 % |
| törött (U+FFFD), egyik maszk sem skálázza | 953 | |

⭐ **A nyers maszk pontosan 55 424 token — bitre annyi, amennyit a round5 mért.** A
round5 szabálya tehát reprodukálódik; a két kör számai összevethetők.

### ⚠️ Lelet, ami a H3 olvasatát érinti

A finomított maszk **nem** a nyers gyengébb változata — a két halmaz szimmetrikus
különbsége nagy, és nem oda esik, ahova előzetesen gondoltuk:

- **csak a nyersben** (a finomított MEGHAGYJA): 4 056 token
  - ebből **3 964 egykarakteres tiszta Han**, köztük a kínai gyakorisági élmezőny:
    `的 一 不 是 有 人 在 大 中 和 上 生 我 要 可 用 …`
  - 88 CJK-írásjel (`。 、 「 」 【 】 《 》`)
  - 4 vegyes (`日々`, `色々`, `時々`, `少々`)
- **csak a finomítottban**: 3 571 token, döntően **kana** (`し は ン の で ー ・`)

**Miért számít.** A H3 előrejelzése az volt, hogy a két maszk között magyar oldalon
nincs mérhető különbség, kínai oldalon viszont a finomított jobb. Ez áll — de a
runbook hallgatólagosan azt is feltette, hogy **mindkét maszk elviszi a kockázatot
nullára**. Ez most már nem magától értetődő: a round5-ben megfigyelt Han-kimenetek
(`继续`, `新闻`, `我需要`, `没有找到`) többkarakteres szavak voltak, de a `我` önmagában
is egy token, és a finomított maszkban **benne marad**. A finomított kar tehát
elvben adhat nem-nulla kockázatot.

**Amit ezzel teszünk:** semmit nem változtatunk a protokollon. A H1/H5 kockázat-mérés
minden karon lefut, tehát ez a kérdés MÉRVE lesz, nem feltételezve. A jelen bejegyzés
azért van, hogy a mérés után ne lehessen utólag „ezt vártuk"-nak olvasni.

### A „csak-egyszerűsített" karakterlista

Forrás: Unihan 18.0.0 `Unihan_Variants.txt`
(sha256 `4ccfd34b08ac7b9c14353f6668ba43e3796d85c4cdce7952b635be16015aafa2`).
Definíció: `kTraditionalVariant ≠ önmaga` ÉS nincs `kSimplifiedVariant`-ja →
**6 825 karakter** (2 kétes eset kihagyva: `苧`, `蒙`).
Vállalt pontatlanság: a japán *shinjitai* részben ugyanezeket az alakokat használja
(`国`, `学`, `体`), ezek tehát a listára kerülnek. A hatás iránya ismert: a finomított
maszk a japánból többet vesz el, mint a szigorú definíció szerint kellene — a H3
tesztje ezen az oldalon **konzervatív**. A magyar végpontot nem érinti.

---

## F0/4 — μ_h becslés · 2026-09-18

Eszköz: `eszkozok/mu_h_becslo.py` · próbahalmazok: `mu-h-probahalmaz-A/B.json` (v1.0)

### ⛔ Amit elrontottunk, és hogyan derült ki

Az első változat `AutoModelForCausalLM`-mel töltötte be a checkpointot. **A betöltés
lefutott, az önteszt átment, és a szám kijött volna — csak épp értelmetlenül.** A
transformers 5.5.4 a MoE szakértőket fúzionált alakban várja
(`mlp.experts.gate_up_proj`), a checkpoint viszont szakértőnként tárol
(`mlp.experts.0.gate_proj.weight`), ezért **mind a 40 réteg összes szakértősúlya
`MISSING` lett, azaz véletlenszerűen inicializálódott**. A logitok belső
konzisztenciáját ellenőrző első önteszt ezt nem látta, mert a `lm_head` és a végső
normalizálás rendben volt.

Ez pontosan az a hibafajta, ami ellen a runbook §0 óv: a mérés lefut, a szám hihető,
és semmi nem szól. Amit tanultunk belőle: **a betöltés önkonzisztenciája nem
bizonyíték a súlyok helyességére**, és a csendes `MISSING` figyelmeztetéseket el kell
olvasni.

**Javítás:** a becslés a vLLM `token_embed` pooling útján megy. Ez egyben jobb is:
ugyanaz a motor, amin a karok ténylegesen futnak. Az új önteszt **tanári
kényszerítés**: a `t`-edik pozíció rejtett állapotából `h·lm_headᵀ` argmaxa a `t+1`-edik
tényleges tokent kell hogy eltalálja. Véletlen szakértőkkel ez nulla közelébe esne.
Küszöb: 30 %.

### Két további, kisebb buktató (mindkettő javítva, a kódban dokumentálva)

1. **A csevegő-sablon token-előtag csapdája.** `add_generation_prompt=True` sztringszinten
   valóban előtagja a teljes sablonnak, **tokenszinten nem**: a záró `\n` a teljes
   változatban a rákövetkező `\n</think>` darabbal egy tokenné olvad. A naiv
   különbségképzés minden itemen leállt. Megoldás: karakter-eltolásos tartomány.
2. **A vLLM lebontása beragad** (`terminate called without an active exception`): az
   eredmény már lemezen van, a konténer mégis fut tovább, és a vezénylő soha nem lép
   a következő karra. Megoldás: `os._exit(0)` a kiírás után.

Egy harmadik: alapbeállításokkal a motor `No available memory for the cache blocks`-szal
elhasalt — nem a súly miatt (33,3 GiB), hanem mert a **vizuális torony** profilozása a
legnagyobb képméretre foglal. Megoldás: `limit_mm_per_prompt={'image':0,'video':0}`.

### Eredmény

| | itemek | önteszt top-1 | ‖μ_h‖ | item↔μ_h koszinusz (átlag / min / max) |
|---|---:|---:|---:|---|
| **A** (termékközeli iratfeldolgozás) | 30 | 2039/3090 = **66,0 %** | 63,4525 | 0,9359 / 0,9036 / 0,9652 |
| **B** (általános magyar köznyelv) | 30 | 1938/2964 = **65,4 %** | 56,2426 | 0,8890 / 0,8072 / 0,9304 |

⭐ **Érzékenység-ellenőrzés (runbook §9): `cos(μ_h^A, μ_h^B) = 0,8893`.** A két
tárgykörében, regiszterében és rendszerpromptjában független halmaz lényegében ugyanazt
az irányt adja. A μ_h tehát nem a próbahalmaz műterméke.

Gyakorlati következmény a beavatkozásra: α=200 mellett a saját irányban a célzott logit
pontosan −200; a **kereszt-logit** A→B `−157,6`, B→A `−200,7`. Az irány-alapú csere
tehát a próbahalmazok között átvihető.

**Döntés:** a karok az **A** halmaz μ_h-jával épülnek (termékközeli, ez a
felhasználási környezet). A B a jegyzőkönyvben marad érzékenység-ellenőrzésként.

---

## F0/5 — kínai képesség-próba · 2026-09-18

Eszköz: `kinai-proba/kinai_proba.py` · itemek: `kinai-proba/items-kinai.jsonl`

36 item, hét kategóriában, zárt értékkészletű válaszokkal, greedy dekódolással, exact
egyezésre pontozva:

| kategória | db | mit mér |
|---|---:|---|
| `liangci` | 6 | 量词 — nyelvtani számlálószó |
| `fanyici` | 6 | ellentétpár, egy karakter |
| `chengyu` | 6 | 成语 kiegészítés, négy karakter — **többkarakteres tiszta Han**, amit MINDKÉT maszk elnyom |
| `fanjian` | 6 | 繁→简 — pontosan az a karakterosztály, amit a finomított maszk céloz (H3) |
| `changshi` | 6 | zárt tényválasz kínaiul |
| `fenlei` | 3 | kétértékű osztályozás kínai címkével |
| `erxuanyi` | 3 | kétválasztós, a válasz maga is kínai szó |

Minden helyes válasz **kínai írásjegyet igényel** — ez nem díszítés: egy pinjinnel vagy
angolul adott válasz épp a folt hatását rejtené el.

**Két mérőszám, nem egy.** A `pontszam` mellett a `han_nelkul` arány is megy a model
cardba: hány itemnél nincs a válaszban EGYÁLTALÁN Han karakter. A kettő mást jelent —
az egyik azt, hogy rosszul válaszol kínaiul, a másik azt, hogy nem tud kínaiul
válaszolni.

---

## F0/1 — a Csapda Korpusz bővítése 50 → 150 itemre · 2026-09-18

Eszközök: `magyar-kie-eval/src/gen_csapda.py`, `src/ellenorzo_csapda.py`
Kimenet: `corpus/C1.md` … `corpus/C9.md`, `gt/items-csapda.jsonl` (100 item),
`gt/items-150.jsonl` (50 régi + 100 új), `gt/tenyek-csapda.json`

Kilenc generált irat, kilenc hibaosztályra, **100 új item**, minden ground truth
számolt. A régi 50 item az összevont fájlban **bájtra érintetlen** — enélkül a
Kapu F0 első feltétele (a kontroll hozza a korábbi eredményt) nem is lenne
értelmezhető.

| osztály | irat | itemek | a csapda |
|---|---|---:|---|
| C1 | tételes elszámolás | 12 | szóközzel szétvágott egységár (`4 0 000`); a helyes érték a sor nettójából **aritmetikailag** visszafejthető |
| C2 | alanyi adómentes számla | 11 | nincs fizetési mód, áfasor, bankszámlaszám, teljesítési dátum → mind „nincs az iratban" |
| C3 | számla engedménnyel és kerekítéssel | 11 | 3 tételsor + 2 összesítő korrekció, ami **nem** tételsor |
| C4 | éves elszámoló számla | 11 | négy majdnem azonos nevű sor, **nem növekvő** összegekkel |
| C5 | villamosenergia-számla | 11 | NUL-bájt, nullaszélességű szóköz, feltételes kötőjel, szóközzel tagolt számok |
| C6 | vállalkozási szerződés | 11 | a hatálybalépés **szövegből**; az iratban van dátum, de nem az |
| C7 | kölcsönös titoktartás | 11 | a séma egyirányú szerepet vár, az irat kétirányú — plusz EGY aszimmetrikus pont |
| C8 | támogatási szerződés | 11 | óradíj **és** fix átalány egyszerre; a végösszeg nincs kiírva, számolni kell |
| C9 | szállítási keretszerződés | 11 | igaz / hamis / **nem dönthető el** — kalibráció, nem nehézség |

**385 konzisztencia-ellenőrzés fut le hibátlanul** (`ellenorzo_csapda.py`). A
legfontosabbak, amik nélkül az item mást mérne, mint hisszük:

- C1: a helyes egységár **nem szerepel ép alakban** az iratban (különben nem csapda);
- C2: a hiányzónak jelölt mezők egyike sem található meg semmilyen alakban;
- C3: a tételtáblában **pontosan három** számozott sor van;
- C4: a négy díj **nem** növekvő sorrendben áll;
- C5: mind a három törött karakter (U+0000, U+200B, U+00AD) ténylegesen jelen van;
- C8: a márciusi nettó végösszeg **nincs kiírva** az iratba.

### Elsődleges végpont: item-szintű pass-rate, nem súlyozott pontszám

A round5 a 100 pontos, részpontos skálát használta. Az arra épített „nem romlott"
állítás nem tesztelhető: nincs rá értelmes párosított próba, és a CI sem zárt alakú.
A runbook §5 arányokat ír elő, ezért:

> egy item **átmegy**, ha minden ground-truth mezője pontosan stimmel.

A súlyozott pontszám másodlagos végpontként megmarad, és a **régi 50 itemre külön is**
jelentjük — enélkül a round5-tel való összevetés nem elvégezhető.

### Adatvédelmi állapot

Az iratok a hibaosztály **leírásából** készültek, nem az eredeti ügyfélszövegből:
nincs mit átszivárogtatni. Minden cégnév, adószám, cím, összeg és dátum generált, és
minden irat fejlécében szerepel, hogy kitalált tartalmú tesztirat.
⚠️ **Nyitott feladat a publikálás előtt:** az n-gram átfedés-vizsgálat (8 szavas egyező
sorozat = kifogás) az eredeti KIE- és szerződéskorpusz ellen — ehhez hozzáférés kell
azokhoz a korpuszokhoz, és a publikálási kapu része.

---

## F0/3 — a nyolc kar előállítása

Eszközök: `eszkozok/patch_lm_head.py` (kiterjesztve az irány-alapú formára),
`eszkozok/ellenoriz_kar.py`, `eszkozok/karok_epit.sh`

Az igazolás három szintje: fájlszint (minden nem célzott fájl szimlink ugyanarra az
inode-ra), tenzorszint (a foltozott shardban a `lm_head.weight` KIVÉTELÉVEL minden
tenzor bitre azonos — az `outside.safetensors` a vizuális tornyot és a beágyazási
mátrixot is tartalmazza), sorszint (pontosan a célzott sorok változtak, és pontosan
azok is változtak).

Újdonság a round5-höz képest: a patch **előjel-diagnosztikát** is kiír, ha megkapja a
μ_h-t — hány célzott sor logitja negatív a magyar átlagállapotban, és hánynak NŐTT a
logitja a folttól. Ez a legolcsóbb pont, ahol az előjel-csapda egyáltalán látszik; nem
helyettesíti az F3 célzott mérését, de ingyen van.

---

## Statisztikai eszköztár

`eszkozok/statisztika.py` — a runbook §5 eljárásai egy helyen, csak `math`-tal
(nincs scipy-függés, hogy a csomag reprodukálható legyen): Wilson-CI, **Poisson exact
felső korlát** (a `0/M` önmagában nem eredmény), McNemar (kis n-nél exact), párosított
különbség CI-vel a nem-inferioritási döntéshez, Holm-korrekció. Minden eljárás
öntesztelt ismert értékek ellen.

---

## ⭐ Az előjel-csapda MÉRVE — a kör eddigi legfontosabb lelete · 2026-09-18

Eszköz: `eszkozok/elojel_csapda.py` · kimenet: `eredmenyek/elojel-csapda-muh.json`

A runbook §9 az előjel-csapdát nevezte meg a legvékonyabb pontnak: a round5 **egyetlen**
billenési ponton mérte meg, hogy nem aktív. A karépítés előjel-diagnosztikája most
mást mutat, és ezt a mérés előtt kell kimondani.

### A logitszintű kép

A magyar átlagállapotban (`h = μ_h`) a célzott 55 424 sor **96,4 %-ának NEGATÍV a
logitja**. A `0 < S < 1` szorzó ezeket **nulla felé tolja**, azaz a szorzás a célzott
sorok 96,4 %-ánál **növeli** a logitot. A célzott logitok átlaga:

| kar | célzott logit átlag |
|---|---:|
| K0 | −1,654 |
| S07 | −1,158 |
| S05 | −0,827 |

### A valószínűségszintű kép — ez a mérőszám

A logitok számolása önmagában nem eredmény, mert ezek a sorok mélyen a maximum
(7,973) alatt ülnek. A tényleges kérdés a Han-tokenek **összvalószínűsége**:

| kar | Han-tömeg t=0,6 | t=0,8 | t=1,0 |
|---|---:|---:|---:|
| K0 | 0,326 % | 3,931 % | 10,526 % |
| S07 | **0,402 %** (1,23×) | **5,089 %** (1,30×) | **13,351 %** (1,27×) |
| S05 | **0,520 %** (1,59×) | **6,417 %** (1,63×) | **16,138 %** (1,53×) |

⛔ **A szorzásos folt a nyers eloszlásban MEGNÖVELI a Han-tömeget**, minden mért
hőmérsékleten, és **mindkét, egymástól független μ_h próbahalmazon** (a B halmazon
1,21–1,51×). Ez nem zaj: a hatás a beavatkozás előjel-szerkezetéből következik, és
erősebb dózisnál nagyobb.

### Miért működik mégis a gyakorlatban — és mi ennek az ára

A termelési mintavételezés `top_k = 20`, `top_p = 0,95`. Ebben az állapotban a top-20
jelölt között **egyetlen Han token sincs**, tehát a csonkolás után a Han-tömeg
**mindkét karon pontosan 0,000000 %**:

| | nyers | csonkolt (top_k=20, top_p=0,95) |
|---|---:|---:|
| K0 t=1,0 | 10,526 % | 0,000000 % |
| S05 t=1,0 | 16,138 % | 0,000000 % |

Vagyis: **a folt nem azért hatásos, mert elveszi a Han-tömeget, hanem mert a
mintavételező levágja a farkat, ahol az a tömeg ül.** A folt ott dolgozik, ahol a
Han-token ténylegesen bekerül a top-20-ba — ott a logitja POZITÍV, és a szorzó
valóban lehúzza. A round5 `8,314 % → 0,000 %` mérése ilyen billenési ponton készült,
és érvényes; csak épp nem általánosítható a teljes eloszlásra.

### Mit jelent ez a további körre

1. **A model cardba kötelező.** Aki `top_k`-csonkolás nélkül mintavételez (pl. tiszta
   `top_p` vagy `temperature`-only), az a foltozott modelltől **magasabb** nyers
   Han-hajlamot kap, mint az alapmodelltől. Ez a folt ismert kártétele, nem apró betű.
2. **A H2 előrejelzése élesebb lett.** Az irány-alapú csere a sort KICSERÉLI, nem
   szorozza — nála ez a jelenség fogalmilag nem állhat fenn. Ez most már nem elvi
   érv, hanem **ellenőrizhető előrejelzés**: az `A200`/`A050` karokon a nyers
   Han-tömegnek is csökkennie kell. Ha nem csökken, a forma-hipotézis mechanizmusa
   hibás.
3. **Az F3 fázis feladata konkretizálódott.** A μ_h **átlagállapot**, nem valódi
   generálási állapot. A csapdát valódi billenési pontok rejtett állapotain is meg
   kell mérni — a `elojel_csapda.py` erre már fel van készítve (`--allapotok`).

⚠️ **Amit ez NEM mond.** Nem mond ellent a round5-nek, és nem jelenti azt, hogy a folt
rontana a termelési úton. A `0/M` mérés a prod profillal készült, ahol a csonkolás
érvényes. A lelet azt mondja meg, hogy a **hatás mechanizmusa más, mint hittük**, és
hogy a folt hatásossága a mintavételezési profiltól függ.

### A két forma szembeállítva — a H2 mechanizmusa igazolva (a képességköltség még nem)

| kar | célzott logit átlag | nyers Han-tömeg t=0,6 | t=0,8 | t=1,0 | logitja NŐTT |
|---|---:|---:|---:|---:|---:|
| K0 | −1,654 | 0,326 % | 3,931 % | 10,526 % | — |
| S05 (szorzás) | −0,827 | 0,520 % (1,59×) | 6,417 % (1,63×) | 16,138 % (1,53×) | **53 423 / 55 424** |
| A200 (irány) | −200,068 | **0,000000 %** | **0,000000 %** | **0,000000 %** | **0 / 55 424** |

Az irány-alapú csere a célzott sorok **100 %-ánál** negatív logitot ad (−200,07 átlag),
és a nyers Han-tömeget mindhárom hőmérsékleten **pontosan nullára** viszi. A szorzásnál
ugyanez a tömeg 1,5–1,6-szorosára nő.

⚠️ **Amit ez igazol és amit nem.** Igazolja a H2 **mechanizmusát**: az irány-alapú
forma előjel-független, tehát nincs nála előjel-csapda. Nem igazolja magát a H2-t: az
azt állítja, hogy az irány-csere ugyanazt a kockázat-nullát **kisebb magyar
képességköltséggel** éri el. A költséget a csapda-korpusz méri, és az még nem futott le.
A −200-as logitplafon durvább vágás, mint egy 0,5-es szorzó — a cáfolat továbbra is
reális kimenet.

---

## A nyolc kar — felépítve és igazolva · 2026-09-18

Mind a nyolc snapshot elkészült, mindegyiken **507 ellenőrzés fut le hibátlanul**
(`ellenoriz_kar.py`: fájlszint / tenzorszint / sorszint). Összesen 22 GB — karonként
egyetlen újraírt shard (`outside.safetensors`, 2,93 GB), minden más fájl szimlink a
kiinduló snapshot ugyanazon inode-jára.

| kar | forma | maszk | paraméter | célzott sor | logitja NŐTT (h=μ_h) | shard sha256 |
|---|---|---|---:|---:|---:|---|
| `S07` | szorzás | nyers | 0,7 | 55 424 | 53 423 | `3cbfe634c523cc2e…` |
| `S05` | szorzás | nyers | 0,5 | 55 424 | 53 426 | `8f3e07c236a4902e…` |
| `S03` | szorzás | nyers | 0,3 | 55 424 | 53 424 | `cc670477ae401674…` |
| `S01` | szorzás | nyers | 0,1 | 55 424 | 53 426 | `5e7fa27db0eb3f47…` |
| `S05F` | szorzás | **finomított** | 0,5 | 54 939 | 52 975 | `638bbb6ab94ee28a…` |
| `A200` | irány-csere | nyers | α=200 | 55 424 | **0** | `86b8a492b62b275a…` |
| `A050` | irány-csere | nyers | α=50 | 55 424 | **0** | `e3cd25377fdffcad…` |
| `A200F` | irány-csere | **finomított** | α=200 | 54 939 | **0** | `a8faff4abd2cf8e0…` |

Mind a nyolc shard-sha256 különbözik — tehát nincs véletlen másolat, és minden kar
ténylegesen más modell.

A „logitja NŐTT" oszlop az előjel-csapda ujjlenyomata: a szorzásos karokon a célzott
sorok ~96 %-ának logitja **emelkedik** a folttól, az irány-alapú karokon **egyetlené sem**.

---

## F0 állapot összefoglalva

| F0 tétel | állapot |
|---|---|
| F0/1 — csapdakorpusz 150 itemre | ✅ kész (100 új item, 9 generált irat, 385 konzisztencia-ellenőrzés) |
| F0/2 — céltokenek, két maszk | ✅ kész (nyers 55 424 = a round5 száma; finomított 54 939) |
| F0/3 — nyolc kar + igazolás | ✅ kész (507 ellenőrzés karonként) |
| F0/4 — μ_h, verziózott próbahalmaz | ✅ kész (2×30 item, `cos(A,B)=0,8893`) |
| F0/5 — kínai képesség-próba | ✅ kész (36 item, 7 kategória) |
| statisztikai eszköztár (§5) | ✅ kész, öntesztelve |
| **Kapu F0 — a kontroll hozza a round5-öt?** | ⏳ fut (K0 mérés) |
| **Kapu F0 — az új itemek reprodukálják a hibaosztályukat?** | ⏳ a K0 eredményére vár |
| párhuzamosítás igazolása (soros vs. 6-os köteg) | ⏳ a K0 után |

---

## Kapu F0 — a teljes K0 futás alapján · 2026-09-18

> ⛔ **VISSZANYITVA 2026-09-18 17:40-kor.** Az alábbi számok a **párhuzamosított**
> (`parallel=6`, 3×) műszeren születtek. Az F1 párhuzamosság-kapuja utóbb megbukott: a
> kötegméret a `T7-08` itemen a PASS/FAIL-t is átbillenti. A mérőpad sorosra állt, a K0
> újramérése folyik, és a kapu mindkét ágát a **soros** számokon kell újra kimondani.
> Ez a szakasz addig **a párhuzamos műszer leírásaként** érvényes — nem törlöm, mert ez a
> bizonyítéka annak, hogy a kötegméret mit csinál. Részletek és az előre rögzített
> előrejelzés: [F1-naplo.md](F1-naplo.md).

Eszközök: `eszkozok/kapu_f0.py`, `eszkozok/csapda_riport.py`
Bemenet: `reports/csapda-K0.json` (150 item × 3 futás, párhuzam = 6)

### (1) A kontroll hozza a round5-öt — ⭐ TELJESÜL

A régi 50 itemen, **item-szinten párosítva** a round5 beta-buildes kontrollfutásával
(`meres-kiindulo-betabuild.json`):

| | pass-rate | pontszám |
|---|---|---|
| ez a kör (K0) | 49/50 = 98,0 % [89,5–99,6] | **97,00/100** |
| round5 (kiinduló @ beta-build) | 49/50 = 98,0 % [89,5–99,6] | **97,00/100** |

Párosítva: `b=1`, `c=1`, Δ = +0,00 pp [−5,54; +5,54], McNemar exact **p = 1,0000**.
Két item cserélődik oda-vissza: `T3-02` most bukott / akkor átment, `T7-08` fordítva —
épp akkora elmozdulás, amekkora a műszer saját zaja.

A `97:97` a runbook §0 táblázatának beta-buildes száma, tehát **a környezet nem
változott**, és a párhuzamosított mérés a régi számot adja vissza. Az aggregált pontszám
egyezése önmagában gyenge bizonyíték lenne — itt az item-szintű párosítás mutatja, hogy
UGYANAZOK az itemek mennek át.

### (2) Az új itemek reprodukciós állapota — a hibaosztályok RÉSZBEN reprodukálnak

A 2026-09-18-i döntés szerint egyetlen item sem marad ki; a jelentés rétegzett.

| | itemek | K0 pass-rate | pont |
|---|---:|---|---:|
| **MIND** | 150 | **144/150 = 96,0 %** [91,5–98,2] | 192,50/200 |
| régi 50 | 50 | 49/50 = 98,0 % [89,5–99,6] | 97,00/100 |
| **új 100** | 100 | **95/100 = 95,0 %** [88,8–97,8] | 95,50/100 |

Hibaosztályonként:

| osztály | K0 | a csapda |
|---|---|---|
| C1 szétvágott szám | 12/12 | |
| C2 kitalált érték `null` helyett | 11/11 | |
| C3 kitalált tételsorok | 11/11 | |
| **C4** név/szám összetartozás | **10/11** | a `C4-10` (negyedévenkénti dict-lista) bukik |
| C5 törött kinyerés | 11/11 | |
| C6 hatálybalépés szövegből | 11/11 | |
| C7 kétirányú titoktartás | 11/11 | |
| C8 számlázási mód | 11/11 | |
| **C9 eldönthetetlen állítás** | **7/11 = 63,6 %** [35,4–84,8] | ⭐ a legnehezebb |

⭐ **A C9 osztály pontosan úgy reprodukál, ahogy a runbook §4.1 kérte.** A négy bukott
item közül **három a „nem dönthető el" kategória** (`C9-02` keretösszeg automatikus
emelése, `C9-04` sürgős megrendelés határideje, `C9-09` azonnali felmondás
hozzájárulása) — vagyis mind a három olyan állítás, amit az irat KIFEJEZETTEN nyitva
hagy, és a kontroll mégis határozott ítéletet ad rájuk. Ez a `T7-08`-ból absztrahált
hibaosztály, és az új, generált iraton is él. A negyedik (`C9-11`) a nyitva hagyott
kérdések felsorolása.

A `K0 bukott` réteg tehát **nem üres** (5 item), de kicsi: a **JAVULÁS** mérésére kevés
a fejtér, a **VESZTESÉG** mérésére viszont 95 item áll rendelkezésre. A kör elsődleges
kérdése („mennyit fizetünk") ezen a korpuszon jól mérhető; a javulásra vonatkozó
bármilyen állítás gyenge lesz, és ezt így kell leírni.

Hét osztály 100 %-on áll a kontrollon. Ez **nem** azt jelenti, hogy könnyűek: a 150
itemből **72-nél** eltér a három greedy futás nyers kimenete, vagyis az itemek a
döntési határ közelében vannak — csak a többségi kimenet esik a helyes oldalra.

### ⚠️ A műszer saját zaja — a felbontás alsó határa MÉRVE

> ⭐ **UTÓLAG (2026-09-18 17:40): ez a zaj nem a műszeré volt, hanem a párhuzamosításé.**
> A 12 itemes soros kontrollfutás mindhárom ismétlésben **bájtra azonos** kimenetet adott
> (12/12 item). Az alábbi 2,00 pp tehát a `parallel=6` kötegméret-hatását méri, nem a
> modell vagy a korpusz sajátját. Ha a soros determinizmus a teljes 150 itemen is
> igazolódik, a −1,33 pp-os margó **újra használható**, és az alábbi következtetés
> („a margón belüli eltérés nem különböztethető meg a zajtól") érvényét veszti.

A három greedy futás külön pontozva, mind a 150 itemen:

| | db |
|---|---:|
| a nyers szöveg eltér | 72 |
| a **pontszám** eltér | **4** |
| a **PASS/FAIL** eltér | **3** |

Az „instabil" jelölés tehát javarészt kozmetikai (záró szóköz, fogalmazás), és a
tényleges mérés közel determinisztikus. A zaj a pass-szinten **3/150 = 2,00 pp**.

⛔ **Ez MEGHALADJA a választott −1,33 pp-os (−2 pont a 150-es skálán) nem-inferioritási
margót.** Következmény, amit a tanulmányban ki kell mondani: **a margón belüli eltérés
nem különböztethető meg a műszer zajától.** A runbook §5 nyelve erre fel van készítve
(„ami ennél kisebb, arról azt mondjuk, hogy a felbontásunk alatt van — nem azt, hogy
nincs"), de mostantól van hozzá szám: a felbontásunk **≈2 pp**, nem 1,33.

Amit ez gyakorlatilag jelent: a „nem-inferior" verdikt csak akkor mondható ki, ha a
párosított különbség CI-jének alsó vége a margó FÖLÖTT van — és ez a 2 pp-os zaj
mellett csak akkor teljesül, ha a tényleges eltérés lényegében nulla. Ez szigorú, de
őszinte.

**Eltérés a runbook §4-től, okkal:** a runbook „az elsődleges karokon 5×" ismétlést ír
elő. A csapda-korpusz a §4 táblázatában determinisztikusként szerepel. A most mért
pass-szintű zaj (3/150) mellett az 5× +67 % GPU-időbe kerülne minden karon. **Döntés:**
3× marad mindenhol; ha egy kar eltérése a margó közelébe esik, azt a kart külön, 5×
ismétléssel újramérjük.

### Az `S01` kar szerepe: a műszer pozitív kontrollja

Mivel a `K0 bukott` réteg kicsi, felmerül, hogy a bővített korpusz elég érzékeny-e a
veszteség kimutatására — vagy csak túl könnyű. Ezt nem feltevéssel válaszoljuk meg: az
`S01` kar (szorzás, S = 0,1) a runbook H1 előrejelzése szerint az, ahol a veszteséget
**várjuk**. Ezért az `S01` ebben a körben a **műszer pozitív kontrollja**:

- ha `S01`-en mérhető romlás van → a korpusz érzékeny, és a többi kar „nincs veszteség"
  eredménye értelmezhető;
- ha `S01`-en **sincs** romlás → két olvasat lehetséges, és a runbook mindkettőt előre
  kimondta: vagy tényleg nincs kompromisszum (H1 cáfolati ága), vagy a korpusz nem elég
  érzékeny. A kettőt a **kínai próba** választja szét: ha `S01`-en a kínai összeomlik,
  de a magyar nem mozdul, akkor a beavatkozás ténylegesen célzott; ha a kínai sem
  mozdul, akkor a műszerek a hibásak.

Ezért fut az `S01` az F2 sorrendjében előre, nem hátra.
