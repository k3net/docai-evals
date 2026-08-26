# Ellenőrző validációs napló — 3. kontrollkör

> ⚠️ **Terminológia (2026-08-26):** ahol ez a dokumentum „ellenőrző kör”-t vagy „ellenőrző bírálatt” ír, az a
> **GPT-5.6 Sol ellenőrző bírálata** (tételenként, a teljes válasszal és a rubrikával, a Qwen3.6-35B
> gépi bíráló ítélete mellé); emberi vak értékelés nem történt. A dolgozat ezt végig „ellenőrző kör”
> néven hozza.

**Vizsgált konfiguráció:** Qwen3.5-9B instruct, nyers folytatásos prompt, chat-sablon nélkül.  
**Dátum:** 2026-08-25.  
**Ellenőrzési kör:** Mérés A — 102/102 kötelező HU+ZH válasz; D1 — 48/48 UNT-válasz.  
**Forrás:** a feltöltött tisztított kézi ellenőrző ívek és az eredeti, módosítatlan pontozó CSV-k.

## Rövid eredmény

- **Mérés A:** 43/102 gépi ítéletet javítottam; az ítéletek pontos egyezése 57.8%, Cohen-kappa: **0.417**.
- **Hallucinációk:** a gépi bíráló 1, a tartalmi ellenőrzés **37** hallucinációt azonosított a 102 kötelező válaszban.
- **Részben helyes válaszok:** gépi bíráló 0, kézi bírálat **5**.
- **D1:** 29/48 válasznál változott legalább egy komponensdarabszám.
- **D1 native:** gépi 100/138 (72.5%) → kézi **69/138 (50.0%)**.
- **D1 distortion:** gépi 24/96 (25.0%) → kézi **18/96 (18.8%)**.

> **Módszertani korlát:** a korábbi két kör kézi precedensnaplója, valamint a `src/set_manual.py`, `src/analyze_a.py` és `src/analyze_d.py` projektfájl nem volt a csatolmányok között. Az ítéleteket ezért a 3. kör útmutatójában teljes terjedelemben idézett rubrika alapján hoztam meg. Az eredeti CSV-ket nem szerkesztettem; a dokumentum végén szereplő 150 parancs a projektkörnyezetben biztonságosan visszaírja a döntéseket. A korábbi körökkel páros összehasonlítás és új p-érték a hiányzó korábbi egyedi ítéletek nélkül nem számolható.

## Mérés A — javított pontossági mátrix

A HU és ZH sorok az ellenőrző körben újraítéltek. Az UNI kontrollcsoport nem tartozott a kötelező ellenőrző körbe, ezért ott az eredeti gépi ítélet maradt.

### Szigorú pontosság — csak `helyes`

| Csoport | hu | en | zh |
|---|---:|---:|---:|
| **ZH** | 9/19 · **47.4%** | 13/19 · **68.4%** | 11/19 · **57.9%** |
| **HU** | 1/15 · **6.7%** | 3/15 · **20.0%** | 2/15 · **13.3%** |
| **UNI** | 17/20 · **85.0%** | 20/20 · **100.0%** | 20/20 · **100.0%** |

### Megengedő pontosság — `helyes` + `reszben`

| Csoport | hu | en | zh |
|---|---:|---:|---:|
| **ZH** | 10/19 · **52.6%** | 14/19 · **73.7%** | 11/19 · **57.9%** |
| **HU** | 2/15 · **13.3%** | 4/15 · **26.7%** | 3/15 · **20.0%** |
| **UNI** | 17/20 · **85.0%** | 20/20 · **100.0%** | 20/20 · **100.0%** |

### Ítélet-eloszlás cellánként

| Csoport / nyelv | n | Helyes | Részben | Helytelen | Hallucináció | Csonkolt | Hurok |
|---|---:|---:|---:|---:|---:|---:|---:|
| ZH / hu | 19 | 9 | 1 | 4 | 5 | 12 | 2 |
| ZH / en | 19 | 13 | 1 | 3 | 2 | 4 | 0 |
| ZH / zh | 19 | 11 | 0 | 4 | 4 | 4 | 2 |
| HU / hu | 15 | 1 | 1 | 5 | 8 | 8 | 2 |
| HU / en | 15 | 3 | 1 | 2 | 9 | 3 | 0 |
| HU / zh | 15 | 2 | 1 | 3 | 9 | 11 | 1 |
| UNI / hu | 20 | 17 | 0 | 3 | 0 | 2 | 1 |
| UNI / en | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| UNI / zh | 20 | 20 | 0 | 0 | 0 | 1 | 0 |

### Hallucinációarány a ténylegesen hibás válaszokon belül

A nevező kizárólag a `helytelen` és `hallucinacio` ítéleteket tartalmazza; a részben helyes válaszokat nem sorolom a teljesen hibásak közé.

| Csoport / nyelv | Hallucináció / hibás | Arány |
|---|---:|---:|
| HU / hu | 8/13 | **61.5%** |
| HU / en | 9/11 | **81.8%** |
| HU / zh | 9/12 | **75.0%** |
| ZH / hu | 5/9 | **55.6%** |
| ZH / en | 2/5 | **40.0%** |
| ZH / zh | 4/8 | **50.0%** |

### Gépi és ellenőrző ítéletek összevetése

| Gépi \ kézi | Helyes | Részben | Helytelen | Hallucináció |
|---|---:|---:|---:|---:|
| `helyes` | 38 | 1 | 1 | 0 |
| `reszben` | 0 | 0 | 0 | 0 |
| `helytelen` | 1 | 4 | 20 | 36 |
| `hallucinacio` | 0 | 0 | 0 | 1 |

### Teljes kézi döntéstábla — 102 válasz

A `*` azt jelzi, hogy az ítélet eltér a gépi bírálótól.

| Item | hu | en | zh |
|---|---|---|---|
| HU01 | `helytelen` | `hallucinacio` * | `helytelen` |
| HU02 | `reszben` * | `hallucinacio` * | `hallucinacio` * |
| HU03 | `hallucinacio` * | `hallucinacio` * | `hallucinacio` * |
| HU04 | `helytelen` | `helytelen` | `helytelen` * |
| HU05 | `hallucinacio` * | `hallucinacio` * | `helytelen` |
| HU06 | `hallucinacio` * | `hallucinacio` * | `hallucinacio` * |
| HU07 | `helytelen` | `helyes` | `helyes` |
| HU08 | `hallucinacio` * | `reszben` * | `hallucinacio` * |
| HU09 | `hallucinacio` * | `hallucinacio` * | `hallucinacio` * |
| HU10 | `helytelen` | `helytelen` | `hallucinacio` * |
| HU11 | `helyes` | `helyes` | `hallucinacio` * |
| HU12 | `hallucinacio` * | `hallucinacio` | `hallucinacio` * |
| HU13 | `helytelen` | `hallucinacio` * | `reszben` * |
| HU14 | `hallucinacio` * | `hallucinacio` * | `hallucinacio` * |
| HU15 | `hallucinacio` * | `helyes` | `helyes` |
| ZH01 | `helyes` | `helyes` | `helyes` |
| ZH02 | `hallucinacio` * | `hallucinacio` * | `hallucinacio` * |
| ZH03 | `helytelen` | `helytelen` | `helytelen` |
| ZH04 | `helytelen` | `helytelen` | `helytelen` |
| ZH05 | `helyes` | `helyes` | `helyes` |
| ZH06 | `hallucinacio` * | `helyes` | `hallucinacio` * |
| ZH07 | `hallucinacio` * | `hallucinacio` * | `hallucinacio` * |
| ZH08 | `reszben` * | `reszben` * | `helyes` |
| ZH09 | `helyes` | `helyes` | `helyes` |
| ZH10 | `helytelen` | `helytelen` | `helytelen` |
| ZH11 | `hallucinacio` * | `helyes` | `hallucinacio` * |
| ZH12 | `hallucinacio` * | `helyes` | `helyes` |
| ZH13 | `helyes` | `helyes` | `helyes` |
| ZH14 | `helyes` | `helyes` | `helyes` |
| ZH15 | `helyes` | `helyes` | `helyes` |
| ZH16 | `helyes` * | `helyes` | `helyes` |
| ZH17 | `helytelen` | `helyes` | `helytelen` |
| ZH18 | `helyes` | `helyes` | `helyes` |
| ZH19 | `helyes` | `helyes` | `helyes` |

### Eltérések indoklása

- **HU01 / en — `helytelen` → `hallucinacio`:** A téves esküvői kerethez kitalált szóeredetet és a fejre helyezett tállal kapcsolatos részletes, magabiztos magyarázatot társít.
- **HU02 / hu — `helytelen` → `reszben`:** A húsvéti ünnepkört felismeri, de a virágvasárnap helyett rossz, egymással is kevert húsvéti időpontokat nevez meg; a hurok nem önálló büntetési ok.
- **HU02 / en — `helytelen` → `hallucinacio`:** A hibás húsvétvasárnap mellé konkrét, alaptalanul megnevezett Kőszeg-környéki helyszínt és részletesen kitalált rítust ad.
- **HU02 / zh — `helytelen` → `hallucinacio`:** A virágvasárnapi szokást magabiztosan december 6-ra és a Mikulás-naphoz köti; ez konkrét, téves dátum.
- **HU03 / hu — `helytelen` → `hallucinacio`:** A fahordás helyett részletesen kidolgozott, kitalált királyi járőrfeladatot és annak politikai célját állítja.
- **HU03 / en — `helytelen` → `hallucinacio`:** Nem létezőnek bemutatott mesecímet, szoborfaragást és részletes büntetési történetet talál ki.
- **HU03 / zh — `helytelen` → `hallucinacio`:** A fahordás helyett konkrét boszorkányégetést és teljesen kitalált cselekménysort állít.
- **HU04 / zh — `helyes` → `helytelen`:** Csak az A–D válaszlehetőségeket sorolja fel; nem jelöli meg a D-t, ezért nem tekinthető válasznak.
- **HU05 / hu — `helytelen` → `hallucinacio`:** Kitalált alszámlákat és egy konkrét, 2015-re tett, részletesen leírt rendszerváltást állít.
- **HU05 / en — `helytelen` → `hallucinacio`:** A téves közlekedési alszámla mellett egy konkrét, 2016-ra tett egyszerűsítési történetet talál ki.
- **HU06 / hu — `helytelen` → `hallucinacio`:** Zala helyett konkrétan Borsod-Abaúj-Zemplént, Miskolcot és Sátoraljaújhely térségét nevezi meg.
- **HU06 / en — `helytelen` → `hallucinacio`:** Zala helyett Békés megyét és egy kitalált Dödölle nevű falut jelöl meg.
- **HU06 / zh — `helytelen` → `hallucinacio`:** Zala helyett konkrétan Baranya megyét és a horvát határ térségét állítja.
- **HU08 / hu — `helytelen` → `hallucinacio`:** A téli szokást konkrétan június–augusztus közé helyezi; ez nem puszta kategóriatévesztés, hanem határozott, téves időablak.
- **HU08 / en — `helyes` → `reszben`:** A karácsonyi időszakot felismeri, de a várt karácsony–újév ablakot advent–vízkeresztre tágítja.
- **HU08 / zh — `helytelen` → `hallucinacio`:** A téli szokást magabiztosan húsvéthoz és konkrét március vége–április eleje időablakhoz köti.
- **HU09 / hu — `helytelen` → `hallucinacio`:** Moha helyett konkrétan Fehérvárhoz köti a szokást, és kitalált tükrös rítust ír le.
- **HU09 / en — `helytelen` → `hallucinacio`:** Moha helyett többször, magabiztosan Kiskunmajsát nevezi meg.
- **HU09 / zh — `helytelen` → `hallucinacio`:** Moha helyett konkrét Bács nevű falut és hibás megyebesorolást állít.
- **HU10 / zh — `helytelen` → `hallucinacio`:** A húsvéti szokást február 14-hez és részletesen kitalált Valentin-napi udvarlási rítushoz köti.
- **HU11 / zh — `helytelen` → `hallucinacio`:** Mirr-Murrt bagolynak állítja, kitalált „szúcs” névvel és mágikus repülős történettel.
- **HU12 / hu — `helytelen` → `hallucinacio`:** Csukás István helyett egy konkrét, kitalált szerzőt, Kurt M. Kappelert nevezi meg.
- **HU12 / zh — `helytelen` → `hallucinacio`:** Csukás István helyett Borgi Ágnest nevezi meg szerzőként és illusztrátorként.
- **HU13 / en — `helytelen` → `hallucinacio`:** A téves német juhász mellett kitalált 1977-es megjelenést, angol címet és náci kivégzőosztagos cselekményt ad.
- **HU13 / zh — `helytelen` → `reszben`:** A magyar juhászkutya tág kategóriáját felismeri, de a konkrét puli fajtát nem nevezi meg.
- **HU14 / hu — `helytelen` → `hallucinacio`:** Szabó Magda helyett konkrétan Kovács Lászlót nevezi meg szerzőként.
- **HU14 / en — `helytelen` → `hallucinacio`:** Szabó Magda helyett Radnóti Miklóst nevezi meg, kitalált 1942-es publikálással és fiktív értelmezéssel.
- **HU14 / zh — `helytelen` → `hallucinacio`:** Szabó Magda helyett Molnár Ágnest és kitalált irodalmi díjakat állít.
- **HU15 / hu — `helytelen` → `hallucinacio`:** Az OKJ-t egy konkrét, nem a rövidítésnek megfelelő intézménynévként oldja fel: „Nemzeti Képzési és Gyakorlati Központ”.
- **ZH02 / hu — `helytelen` → `hallucinacio`:** Hubei helyett konkrétan Hunan tartományt nevezi meg és megerősíti a téves helyszínt.
- **ZH02 / en — `helytelen` → `hallucinacio`:** Hubei helyett konkrétan Hebei tartományt és kitalált közigazgatási elhelyezkedést ad.
- **ZH02 / zh — `helytelen` → `hallucinacio`:** Hubei helyett konkrétan Shanxi tartományt, Linfen várost és Xiangfen megyét állítja.
- **ZH06 / hu — `helytelen` → `hallucinacio`:** Wenzhou helyett konkrétan Yangzhou városát nevezi meg az istenség kultuszhelyeként.
- **ZH06 / zh — `helytelen` → `hallucinacio`:** Wenzhou helyett konkrétan Ningbót nevezi meg; az ismétlési hurok nem változtatja meg a téves helyállítást.
- **ZH07 / hu — `helytelen` → `hallucinacio`:** Fangyan helyett konkrétan Fenghuang-hegyet, Fuzhou városát és Fujian tartományt jelöl meg.
- **ZH07 / en — `helytelen` → `hallucinacio`:** Fangyan helyett konkrétan a Wutai-hegyet és Shanxi tartományt nevezi meg.
- **ZH07 / zh — `helytelen` → `hallucinacio`:** Fangyan helyett konkrétan Fuzhou Yushan-hegyét és egy állítólagos főtemplomot jelöl meg.
- **ZH08 / hu — `helytelen` → `reszben`:** A két várt összetevőből a rizs tág kategóriáját felismeri, a vörös datolya helyett azonban mogyorót ad meg.
- **ZH08 / en — `helytelen` → `reszben`:** A ragacsos rizst helyesen megnevezi, a vörös datolyát is említi, de a két fő összetevő egyikeként tévesen mungóbabot jelöl.
- **ZH11 / hu — `helytelen` → `hallucinacio`:** Hebei helyett konkrétan Hunan tartományt, Hengyang városát és Hengnan megyét állítja.
- **ZH11 / zh — `helytelen` → `hallucinacio`:** Hebei helyett konkrétan Shandong tartományt, Linyi városát és Fei megyét állítja.
- **ZH12 / hu — `helytelen` → `hallucinacio`:** Chongqing helyett konkrétan Huanghua városát és Hebei tartományt nevezi meg.
- **ZH16 / hu — `helytelen` → `helyes`:** A kezdeti Hunan-állítást a válasz egyértelműen visszavonja: „valójában az Anhui tartományban van, nem a Hunanban”.

### Különösen fontos ellenőrző döntések

- **HU04 / zh:** az `A. ... B. ... C. ... D. 一年` szöveg nem választja ki a D lehetőséget. A helyes opció puszta jelenléte egy felsorolásban nem helyes válasz.
- **HU08 / en:** az advent–vízkereszt időablak átfedi, de nem azonos a karácsony–újév időszakkal; ezért `reszben`, nem `helyes`.
- **ZH08 / en:** mindkét várt összetevő szerepel a szövegben, de a fő összetevők közé tévesen mungóbabot sorol; ezért `reszben`.
- **ZH16 / hu:** az első mondat hibás, de az explicit későbbi önjavítás egyértelműen Anhuit jelöli meg és Hunant visszavonja; a teljes látható választ értékelve `helyes`.
- **Hibás étel-, állat- és ünnepkategória:** önmagában `helytelen`. `hallucinacio` akkor indokolt, ha a hibát konkrét kitalált hely, név, dátum, intézmény vagy részletesen fabrikált tény támasztja alá.

## D1 — javított jelentéskomponensek

### Összesítés forráscsoport és válasznyelv szerint

| Forrás / nyelv | Native, gépi | Native, kézi | Distortion, gépi | Distortion, kézi |
|---|---:|---:|---:|---:|
| HU / hu | 10/22 · 45.5% | **9/22 · 40.9%** | 7/16 · 43.8% | **4/16 · 25.0%** |
| HU / en | 15/22 · 68.2% | **10/22 · 45.5%** | 5/16 · 31.2% | **5/16 · 31.2%** |
| HU / zh | 15/22 · 68.2% | **11/22 · 50.0%** | 6/16 · 37.5% | **4/16 · 25.0%** |
| ZH / hu | 18/24 · 75.0% | **9/24 · 37.5%** | 3/16 · 18.8% | **2/16 · 12.5%** |
| ZH / en | 23/24 · 95.8% | **14/24 · 58.3%** | 3/16 · 18.8% | **2/16 · 12.5%** |
| ZH / zh | 19/24 · 79.2% | **16/24 · 66.7%** | 0/16 · 0.0% | **1/16 · 6.2%** |

### Teljes D1 döntéstábla — 48 UNT-válasz

Formátum: `native találat / native összes ; distortion találat / distortion összes`. A `*` eltérést jelez a gépi darabszámhoz képest.

| Item | Fogalom | hu | en | zh |
|---|---|---|---|---|
| UNT-HU01 | kaláka | `1/3 ; 0/2` | `1/3 ; 0/2` * | `1/3 ; 1/2` * |
| UNT-HU02 | szeretet / szerelem | `2/2 ; 0/2` | `0/2 ; 0/2` * | `1/2 ; 0/2` * |
| UNT-HU03 | magázás / tegezés | `1/3 ; 0/2` | `2/3 ; 0/2` | `2/3 ; 0/2` |
| UNT-HU04 | puszi / csók | `1/3 ; 1/2` * | `1/3 ; 1/2` * | `3/3 ; 0/2` |
| UNT-HU05 | honfoglalás | `3/3 ; 0/2` | `3/3 ; 0/2` | `2/3 ; 1/2` |
| UNT-HU06 | sógor | `0/2 ; 1/2` * | `0/2 ; 2/2` | `0/2 ; 1/2` * |
| UNT-HU07 | névnap | `1/3 ; 1/2` * | `2/3 ; 0/2` | `2/3 ; 0/2` * |
| UNT-HU08 | ráér | `0/3 ; 1/2` * | `1/3 ; 2/2` * | `0/3 ; 1/2` * |
| UNT-ZH01 | 关系 (guanxi) | `0/3 ; 0/2` * | `2/3 ; 0/2` * | `0/3 ; 0/2` |
| UNT-ZH02 | 面子 (mianzi) | `1/3 ; 0/2` * | `2/3 ; 0/2` * | `2/3 ; 0/2` * |
| UNT-ZH03 | 缘分 (yuanfen) | `2/3 ; 0/2` * | `2/3 ; 0/2` * | `3/3 ; 0/2` |
| UNT-ZH04 | 热闹 (renao) | `0/3 ; 1/2` * | `1/3 ; 0/2` * | `1/3 ; 0/2` * |
| UNT-ZH05 | 江湖 (jianghu) | `0/3 ; 0/2` * | `1/3 ; 1/2` * | `3/3 ; 0/2` |
| UNT-ZH06 | 撒娇 (sajiao) | `3/3 ; 0/2` | `2/3 ; 1/2` * | `2/3 ; 1/2` * |
| UNT-ZH07 | 上火 (shanghuo) | `0/3 ; 1/2` * | `1/3 ; 0/2` * | `2/3 ; 0/2` |
| UNT-ZH08 | 加油 (jiayou) | `3/3 ; 0/2` | `3/3 ; 0/2` | `3/3 ; 0/2` |

### D1 eltérések indoklása

- **UNT-HU01 / en — native 1 → 1; distortion 1 → 0:** A közösségi csoport megjelenik, de sem egyszeri önkéntes jótettet, sem viszonzás nélküli segítséget nem állít; a d1 találatot el kell venni.
- **UNT-HU01 / zh — native 1 → 1; distortion 2 → 1:** A csoportos együttműködés és a jótékonysági keretezés látható; a külön egyszeri, viszonzás nélküli jótettet nem szabad puszta hiányból beszámítani.
- **UNT-HU02 / en — native 2 → 0; distortion 0 → 0:** A válasz a szeretet leírásánál csonkolódik; a szerelem konkrét romantikus jelentése és a két fogalom hierarchiája egyaránt hiányzik.
- **UNT-HU02 / zh — native 2 → 1; distortion 0 → 0:** A két jelentést megkülönbözteti, de nem állítja, hogy a szerelem a szeretet részhalmaza.
- **UNT-HU04 / hu — native 0 → 1; distortion 2 → 1:** A két külön magyar szó megkülönböztetése megjelenik, de a funkcionális különbség összemosódik; a „kis csók” állítás viszont sehol nem szerepel.
- **UNT-HU04 / en — native 3 → 1; distortion 1 → 1:** A különálló szavakat jelzi és a puszit kicsinyítő alaknak állítja, de az arcon adott puszi és a csók romantikus/szájon adott jelentése a csonkolt szövegben nincs kifejtve.
- **UNT-HU06 / hu — native 0 → 0; distortion 2 → 1:** Csak a testvér férjének irányát említi. A d1 kifejezetten a házastárs fivérére szűkítést jelöli, ez itt nem jelenik meg; a kétirányúság hiánya d2.
- **UNT-HU06 / zh — native 0 → 0; distortion 2 → 1:** Kizárólag a nővér/húg férjéről beszél, nem a d1-ben meghatározott házastárs fivéréről; a kétirányúság elmaradása d2.
- **UNT-HU07 / hu — native 3 → 1; distortion 1 → 1:** A névhez tartozó ünnepnap és a vallásra szűkítő torzítás jelen van, de a születésnappal való egyenrangúság és a teljes naptári/köszöntési komponens nincs kimondva.
- **UNT-HU07 / zh — native 3 → 2; distortion 0 → 0:** A névhez kötött napot és a születésnappal közel egyenrangú szerepet leírja; az összetett harmadik komponensből hiányzik a naptárban feltüntetés.
- **UNT-HU08 / hu — native 0 → 0; distortion 2 → 1:** A válasz hajlandóságról és engedélyről szól, nem szabadidőről; ezért a d1 „free/available” állítás nem szerepel, a halasztó árnyalat hiánya d2.
- **UNT-HU08 / en — native 2 → 1; distortion 1 → 2:** Csak a „van ideje/ráérhető” jelentést adja meg; sem a sürgetés hiánya, sem az udvarias halasztás nincs leírva, ezért mindkét torzítás jelen van.
- **UNT-HU08 / zh — native 2 → 0; distortion 1 → 1:** A szót tévesen „időben odaérni/határidőre odaérni” jelentéssel definiálja; a megnyugtató-halasztó árnyalat hiányzik, de nem pusztán „free/available” fordítást használ.
- **UNT-ZH01 / hu — native 2 → 0; distortion 0 → 0:** A „személyes kapcsolatok hálója” nem tartalmaz kölcsönös hosszú távú kötelezettséget, szívességviszonzást vagy családi/iskolai/területi bizalmi kört.
- **UNT-ZH01 / en — native 3 → 2; distortion 0 → 0:** A kölcsönös kötelezettséget és szívességviszonzást leírja, a családi/iskolai/területi alapú bizalmi kört viszont nem.
- **UNT-ZH02 / hu — native 1 → 1; distortion 1 → 0:** A társadalmi presztízs jelen van, a válasz pedig kifejezetten közösségi szerepet említ, ezért nem egyéni büszkeségre redukálja a fogalmat.
- **UNT-ZH02 / en — native 3 → 2; distortion 0 → 0:** A presztízst és a másik arcának megőrzését bemutatja, a 脸/erkölcsi integritás fogalmától viszont nem különíti el.
- **UNT-ZH02 / zh — native 3 → 2; distortion 0 → 0:** A 给面子/丢面子 és a kölcsönös arcmegőrzés szerepel; a 脸 mint külön erkölcsi integritásfogalom összevetése hiányzik.
- **UNT-ZH03 / hu — native 2 → 2; distortion 1 → 0:** Kifejezetten emberi kapcsolathoz kötött sorskapcsolatot ír le; a „sors” szó használata önmagában nem általános-sors torzítás.
- **UNT-ZH03 / en — native 2 → 2; distortion 1 → 0:** A fated connection és destined relationship egyértelműen kapcsolatspecifikus; a destiny szó jelenléte önmagában nem torzítás.
- **UNT-ZH04 / hu — native 3 → 0; distortion 0 → 1:** Csak „élénk/zajos/forgalmas” és piaci példát ad; a közösségi öröm, a keresett állapot és a csenddel szembeállítás hiányzik, így semleges busy-keretezés marad.
- **UNT-ZH04 / en — native 3 → 1; distortion 0 → 0:** A pozitív, közösségi örömöt és ünnepi példákat bemutatja, de a keresett/kívánatos állapotot és a csend/magány explicit ellentétét nem.
- **UNT-ZH04 / zh — native 3 → 1; distortion 0 → 0:** A pozitív, örömteli közösségi hangulat jelen van; a tudatosan keresett állapot és a csend/magány ellentéteként való értelmezés hiányzik.
- **UNT-ZH05 / hu — native 2 → 0; distortion 0 → 0:** Csak a folyó/tó szó szerinti etimológiáig jut el; a hivatalos társadalmon kívüli világ, a wuxia-közeg és az alternatív rend hiányzik.
- **UNT-ZH05 / en — native 3 → 1; distortion 1 → 1:** A folyók-tavak és a hivatalos struktúrán kívüli világ szerepel, de a szabad, saját erkölcsi kódú wuxia-közeg nincs kifejtve; az underworld bűnözői torzítást viszont tartalmazza.
- **UNT-ZH06 / en — native 3 → 2; distortion 1 → 1:** A közelségkeresést és közeli kapcsolatot bemutatja, de a „lower defenses” és „spoiled/whiny” keret mellett a nem manipulatív harmadik komponens nem adható meg.
- **UNT-ZH06 / zh — native 2 → 2; distortion 0 → 1:** A kedveskedő viselkedés és közeli kapcsolat jelen van, de az 任性 és az „előnyszerzés” pozitívan állított negatív/manipulatív keretezés.
- **UNT-ZH07 / hu — native 2 → 0; distortion 1 → 1:** A TCM említése önmagában nem mondja ki a belső tűztöbbletet; konkrét tüneteket/ételeket sem nevez meg, a gyulladásos fordítás viszont torzítás.
- **UNT-ZH07 / en — native 3 → 1; distortion 0 → 0:** A belső tűz/túlzott hő jelen van, de a csonkolt szövegben nincs étrendi kiváltó ok és egyetlen hűsítő étel sem.

### D1 értelmezési elv

- A csonkolt válaszban csak a ténylegesen látható szöveg számít; egy megkezdett felsorolás későbbi, el nem készült fejezete nem kap találatot.
- Összetett komponensnél egy kiragadott részlet nem helyettesíti a teljes jelentésmagot: a `folyók és tavak` önmagában nem bizonyítja a hivatalos társadalmon kívüli közeget, a tünetlista pedig nem bizonyítja az étrendi kiváltó okot vagy a hűsítő ételeket.
- A `fate`, `destiny`, `noisy` vagy `conquest` szó puszta jelenléte nem torzítás, ha a szöveg a megfelelő kapcsolat-specifikus, pozitív vagy nem hódításra szűkített kontextust is megadja.
- Hiányból csak akkor következtettem torzításra, ha a befagyasztott torzításdefiníció maga is hiányt ír elő; ilyen például a `ráér` halasztó árnyalatának hiánya vagy a `sógor` kétirányúságának elmaradása.
- **UNT-HU05 / zh:** a darabszám marad `native 2 ; distortion 1`, de a tényleges torzítás nem a „pusztán hódítás” keret — a válasz ezt kifejezetten visszautasítja —, hanem a `hon`/haza jelentéselem hiánya. A CSV csak darabszámot tárol, ezért ez a komponensszintű csere a számban nem látszik.

## Mit lehet és mit nem lehet ebből a kontrollból kijelenteni?

1. A gépi bíráló ezen a konfiguráción is erősen aluljelöli a magabiztos, konkrét ténykitalációkat, ezért a hallucinációs arány kézi felülvizsgálat nélkül nem értelmezhető.
2. A D1 bíró több esetben a várható folytatást pontozta a ténylegesen látható szöveg helyett; a jelentésmegőrzési mutató ezért a kézi korrekció előtt felülbecsült.
3. A promptozás és a modellsúly hatásának korábbi, páros +1/+10 felbontása nem ellenőrizhető véglegesen kizárólag a most csatolt körből. Ehhez a korábbi két kör azonos item/nyelv szerinti kézi végítéletei és a páros újraszámolás szükségesek.
4. A csonkolás és az ismétlési hurok nem automatikusan hiba: a hurok előtt megadott helyes tény helyes marad, a hiányzó folytatás viszont nem pótolható feltételezéssel.

## Beírásra kész parancsok — mind a 150 döntés

A parancsok az útmutató szerinti validáló szkriptet használják; nem módosítanak közvetlenül CSV-fájlt. A projektkörnyezetben egyben futtathatók.

```bash
cd <experiment-dir>
export SCOPE_RES=results_instruct_raw
export SCOPE_REPORTS=reports_instruct_raw

# Mérés A — 102/102 kötelező HU + ZH döntés
python3 src/set_manual.py a HU01 hu helytelen
python3 src/set_manual.py a HU01 en hallucinacio
python3 src/set_manual.py a HU01 zh helytelen
python3 src/set_manual.py a HU02 hu reszben
python3 src/set_manual.py a HU02 en hallucinacio
python3 src/set_manual.py a HU02 zh hallucinacio
python3 src/set_manual.py a HU03 hu hallucinacio
python3 src/set_manual.py a HU03 en hallucinacio
python3 src/set_manual.py a HU03 zh hallucinacio
python3 src/set_manual.py a HU04 hu helytelen
python3 src/set_manual.py a HU04 en helytelen
python3 src/set_manual.py a HU04 zh helytelen
python3 src/set_manual.py a HU05 hu hallucinacio
python3 src/set_manual.py a HU05 en hallucinacio
python3 src/set_manual.py a HU05 zh helytelen
python3 src/set_manual.py a HU06 hu hallucinacio
python3 src/set_manual.py a HU06 en hallucinacio
python3 src/set_manual.py a HU06 zh hallucinacio
python3 src/set_manual.py a HU07 hu helytelen
python3 src/set_manual.py a HU07 en helyes
python3 src/set_manual.py a HU07 zh helyes
python3 src/set_manual.py a HU08 hu hallucinacio
python3 src/set_manual.py a HU08 en reszben
python3 src/set_manual.py a HU08 zh hallucinacio
python3 src/set_manual.py a HU09 hu hallucinacio
python3 src/set_manual.py a HU09 en hallucinacio
python3 src/set_manual.py a HU09 zh hallucinacio
python3 src/set_manual.py a HU10 hu helytelen
python3 src/set_manual.py a HU10 en helytelen
python3 src/set_manual.py a HU10 zh hallucinacio
python3 src/set_manual.py a HU11 hu helyes
python3 src/set_manual.py a HU11 en helyes
python3 src/set_manual.py a HU11 zh hallucinacio
python3 src/set_manual.py a HU12 hu hallucinacio
python3 src/set_manual.py a HU12 en hallucinacio
python3 src/set_manual.py a HU12 zh hallucinacio
python3 src/set_manual.py a HU13 hu helytelen
python3 src/set_manual.py a HU13 en hallucinacio
python3 src/set_manual.py a HU13 zh reszben
python3 src/set_manual.py a HU14 hu hallucinacio
python3 src/set_manual.py a HU14 en hallucinacio
python3 src/set_manual.py a HU14 zh hallucinacio
python3 src/set_manual.py a HU15 hu hallucinacio
python3 src/set_manual.py a HU15 en helyes
python3 src/set_manual.py a HU15 zh helyes
python3 src/set_manual.py a ZH01 hu helyes
python3 src/set_manual.py a ZH01 en helyes
python3 src/set_manual.py a ZH01 zh helyes
python3 src/set_manual.py a ZH02 hu hallucinacio
python3 src/set_manual.py a ZH02 en hallucinacio
python3 src/set_manual.py a ZH02 zh hallucinacio
python3 src/set_manual.py a ZH03 hu helytelen
python3 src/set_manual.py a ZH03 en helytelen
python3 src/set_manual.py a ZH03 zh helytelen
python3 src/set_manual.py a ZH04 hu helytelen
python3 src/set_manual.py a ZH04 en helytelen
python3 src/set_manual.py a ZH04 zh helytelen
python3 src/set_manual.py a ZH05 hu helyes
python3 src/set_manual.py a ZH05 en helyes
python3 src/set_manual.py a ZH05 zh helyes
python3 src/set_manual.py a ZH06 hu hallucinacio
python3 src/set_manual.py a ZH06 en helyes
python3 src/set_manual.py a ZH06 zh hallucinacio
python3 src/set_manual.py a ZH07 hu hallucinacio
python3 src/set_manual.py a ZH07 en hallucinacio
python3 src/set_manual.py a ZH07 zh hallucinacio
python3 src/set_manual.py a ZH08 hu reszben
python3 src/set_manual.py a ZH08 en reszben
python3 src/set_manual.py a ZH08 zh helyes
python3 src/set_manual.py a ZH09 hu helyes
python3 src/set_manual.py a ZH09 en helyes
python3 src/set_manual.py a ZH09 zh helyes
python3 src/set_manual.py a ZH10 hu helytelen
python3 src/set_manual.py a ZH10 en helytelen
python3 src/set_manual.py a ZH10 zh helytelen
python3 src/set_manual.py a ZH11 hu hallucinacio
python3 src/set_manual.py a ZH11 en helyes
python3 src/set_manual.py a ZH11 zh hallucinacio
python3 src/set_manual.py a ZH12 hu hallucinacio
python3 src/set_manual.py a ZH12 en helyes
python3 src/set_manual.py a ZH12 zh helyes
python3 src/set_manual.py a ZH13 hu helyes
python3 src/set_manual.py a ZH13 en helyes
python3 src/set_manual.py a ZH13 zh helyes
python3 src/set_manual.py a ZH14 hu helyes
python3 src/set_manual.py a ZH14 en helyes
python3 src/set_manual.py a ZH14 zh helyes
python3 src/set_manual.py a ZH15 hu helyes
python3 src/set_manual.py a ZH15 en helyes
python3 src/set_manual.py a ZH15 zh helyes
python3 src/set_manual.py a ZH16 hu helyes
python3 src/set_manual.py a ZH16 en helyes
python3 src/set_manual.py a ZH16 zh helyes
python3 src/set_manual.py a ZH17 hu helytelen
python3 src/set_manual.py a ZH17 en helyes
python3 src/set_manual.py a ZH17 zh helytelen
python3 src/set_manual.py a ZH18 hu helyes
python3 src/set_manual.py a ZH18 en helyes
python3 src/set_manual.py a ZH18 zh helyes
python3 src/set_manual.py a ZH19 hu helyes
python3 src/set_manual.py a ZH19 en helyes
python3 src/set_manual.py a ZH19 zh helyes

# D1 — 48/48 UNT-válasz
python3 src/set_manual.py d UNT-HU01 hu --native 1 --distortion 0
python3 src/set_manual.py d UNT-HU01 en --native 1 --distortion 0
python3 src/set_manual.py d UNT-HU01 zh --native 1 --distortion 1
python3 src/set_manual.py d UNT-HU02 hu --native 2 --distortion 0
python3 src/set_manual.py d UNT-HU02 en --native 0 --distortion 0
python3 src/set_manual.py d UNT-HU02 zh --native 1 --distortion 0
python3 src/set_manual.py d UNT-HU03 hu --native 1 --distortion 0
python3 src/set_manual.py d UNT-HU03 en --native 2 --distortion 0
python3 src/set_manual.py d UNT-HU03 zh --native 2 --distortion 0
python3 src/set_manual.py d UNT-HU04 hu --native 1 --distortion 1
python3 src/set_manual.py d UNT-HU04 en --native 1 --distortion 1
python3 src/set_manual.py d UNT-HU04 zh --native 3 --distortion 0
python3 src/set_manual.py d UNT-HU05 hu --native 3 --distortion 0
python3 src/set_manual.py d UNT-HU05 en --native 3 --distortion 0
python3 src/set_manual.py d UNT-HU05 zh --native 2 --distortion 1
python3 src/set_manual.py d UNT-HU06 hu --native 0 --distortion 1
python3 src/set_manual.py d UNT-HU06 en --native 0 --distortion 2
python3 src/set_manual.py d UNT-HU06 zh --native 0 --distortion 1
python3 src/set_manual.py d UNT-HU07 hu --native 1 --distortion 1
python3 src/set_manual.py d UNT-HU07 en --native 2 --distortion 0
python3 src/set_manual.py d UNT-HU07 zh --native 2 --distortion 0
python3 src/set_manual.py d UNT-HU08 hu --native 0 --distortion 1
python3 src/set_manual.py d UNT-HU08 en --native 1 --distortion 2
python3 src/set_manual.py d UNT-HU08 zh --native 0 --distortion 1
python3 src/set_manual.py d UNT-ZH01 hu --native 0 --distortion 0
python3 src/set_manual.py d UNT-ZH01 en --native 2 --distortion 0
python3 src/set_manual.py d UNT-ZH01 zh --native 0 --distortion 0
python3 src/set_manual.py d UNT-ZH02 hu --native 1 --distortion 0
python3 src/set_manual.py d UNT-ZH02 en --native 2 --distortion 0
python3 src/set_manual.py d UNT-ZH02 zh --native 2 --distortion 0
python3 src/set_manual.py d UNT-ZH03 hu --native 2 --distortion 0
python3 src/set_manual.py d UNT-ZH03 en --native 2 --distortion 0
python3 src/set_manual.py d UNT-ZH03 zh --native 3 --distortion 0
python3 src/set_manual.py d UNT-ZH04 hu --native 0 --distortion 1
python3 src/set_manual.py d UNT-ZH04 en --native 1 --distortion 0
python3 src/set_manual.py d UNT-ZH04 zh --native 1 --distortion 0
python3 src/set_manual.py d UNT-ZH05 hu --native 0 --distortion 0
python3 src/set_manual.py d UNT-ZH05 en --native 1 --distortion 1
python3 src/set_manual.py d UNT-ZH05 zh --native 3 --distortion 0
python3 src/set_manual.py d UNT-ZH06 hu --native 3 --distortion 0
python3 src/set_manual.py d UNT-ZH06 en --native 2 --distortion 1
python3 src/set_manual.py d UNT-ZH06 zh --native 2 --distortion 1
python3 src/set_manual.py d UNT-ZH07 hu --native 0 --distortion 1
python3 src/set_manual.py d UNT-ZH07 en --native 1 --distortion 0
python3 src/set_manual.py d UNT-ZH07 zh --native 2 --distortion 0
python3 src/set_manual.py d UNT-ZH08 hu --native 3 --distortion 0
python3 src/set_manual.py d UNT-ZH08 en --native 3 --distortion 0
python3 src/set_manual.py d UNT-ZH08 zh --native 3 --distortion 0

# Kötelező státuszellenőrzés és riport-újragenerálás
python3 src/set_manual.py status
python3 src/analyze_a.py
python3 src/analyze_d.py
```

## Ellenőrző lista

- [x] Mérés A: mind a 102 kötelező válasz egyedi, tartalmi ítéletet kapott.
- [x] D1: mind a 48 UNT-válasz külön native és distortion darabszámot kapott.
- [x] Minden D1 érték a változatlan, befagyasztott nevezőn belül marad.
- [x] Az eredeti CSV-k változatlanok; minden visszaírás az előírt `set_manual.py` útján történik.
- [x] Minden eltérés egyedileg indokolt; a teljes 150 soros parancsblokk rendelkezésre áll.
- [ ] A korábbi két kör precedensnaplójával történő utólagos összevetés — a fájlok nem voltak csatolva.
- [ ] `set_manual.py status`, `analyze_a.py` és `analyze_d.py` tényleges projektbeli futtatása — a projekt szkriptjei nem voltak csatolva.

### Eredeti bemenetek változatlansága — SHA-256

- `scores(3).csv`: `817e6ceaf3eb644285e76be7e9b7590f0e903412125e4a2ee1db2f8173dea04c`
- `d1_scores(3).csv`: `83583f5d75cab70f0bd0cf75e4b07889469e09ceb94af67782f9557b3dcc1de2`
