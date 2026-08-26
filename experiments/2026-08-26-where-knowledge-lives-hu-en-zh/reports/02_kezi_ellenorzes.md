# Kézi ellenőrző ív — Mérés A (ZH + HU csoport)

**102 válasz.** Ahol egyetértesz a bíráló ítéletével, nincs teendő. Ahol nem, add meg a
`src/set_manual.py`-nak: `python3 src/set_manual.py a <item> <nyelv> <ítélet>`
(`helyes` / `reszben` / `helytelen` / `hallucinacio`), majd `python3 src/analyze_a.py`.

⚠️ Két dolgot érdemes külön figyelni, mert a bíráló ezekben gyenge volt:
1. **hallucináció vs. helytelen** — a bíráló 162 válaszból csak 2-t nevezett hallucinációnak, pedig
   a magabiztosan kitalált konkrétumok (pl. *„A nagy ho-ho-ho-horgászt József Attila írta”*) ide tartoznak;
2. **részben helyes** — a bíráló egyetlen `reszben` ítéletet sem adott, tehát ezt a kategóriát gyakorlatilag
   nem használta.

---

## Beírásra kész parancsok

A sorok a **bíráló ítéletével** vannak előkitöltve. Töröld azokat, amelyekkel egyetértesz
(a megerősítéshez elég a `--confirm-all`), a vitatottakon írd át az utolsó szót, majd
futtasd a maradékot egyben. ⛔ A `scores.csv`-t **ne szerkeszd kézzel** — a 08-24-i kör
így veszett el.

```bash
python3 src/set_manual.py a HU01   hu  helytelen
python3 src/set_manual.py a HU01   en  helytelen
python3 src/set_manual.py a HU01   zh  helytelen
python3 src/set_manual.py a HU02   hu  helytelen
python3 src/set_manual.py a HU02   en  helytelen
python3 src/set_manual.py a HU02   zh  helytelen
python3 src/set_manual.py a HU03   hu  helytelen
python3 src/set_manual.py a HU03   en  helytelen
python3 src/set_manual.py a HU03   zh  helytelen
python3 src/set_manual.py a HU04   hu  helytelen
python3 src/set_manual.py a HU04   en  helytelen
python3 src/set_manual.py a HU04   zh  helytelen
python3 src/set_manual.py a HU05   hu  helytelen
python3 src/set_manual.py a HU05   en  helytelen
python3 src/set_manual.py a HU05   zh  helytelen
python3 src/set_manual.py a HU06   hu  helytelen
python3 src/set_manual.py a HU06   en  helytelen
python3 src/set_manual.py a HU06   zh  helytelen
python3 src/set_manual.py a HU07   hu  helytelen
python3 src/set_manual.py a HU07   en  helyes
python3 src/set_manual.py a HU07   zh  helyes
python3 src/set_manual.py a HU08   hu  helytelen
python3 src/set_manual.py a HU08   en  helyes
python3 src/set_manual.py a HU08   zh  helytelen
python3 src/set_manual.py a HU09   hu  helytelen
python3 src/set_manual.py a HU09   en  helytelen
python3 src/set_manual.py a HU09   zh  helytelen
python3 src/set_manual.py a HU10   hu  helytelen
python3 src/set_manual.py a HU10   en  helytelen
python3 src/set_manual.py a HU10   zh  helytelen
python3 src/set_manual.py a HU11   hu  helyes
python3 src/set_manual.py a HU11   en  helyes
python3 src/set_manual.py a HU11   zh  helyes
python3 src/set_manual.py a HU12   hu  helytelen
python3 src/set_manual.py a HU12   en  helytelen
python3 src/set_manual.py a HU12   zh  hallucinacio
python3 src/set_manual.py a HU13   hu  helytelen
python3 src/set_manual.py a HU13   en  helytelen
python3 src/set_manual.py a HU13   zh  helytelen
python3 src/set_manual.py a HU14   hu  helytelen
python3 src/set_manual.py a HU14   en  helytelen
python3 src/set_manual.py a HU14   zh  helytelen
python3 src/set_manual.py a HU15   hu  helytelen
python3 src/set_manual.py a HU15   en  helytelen
python3 src/set_manual.py a HU15   zh  helyes
python3 src/set_manual.py a ZH01   hu  helyes
python3 src/set_manual.py a ZH01   en  helyes
python3 src/set_manual.py a ZH01   zh  helyes
python3 src/set_manual.py a ZH02   hu  helytelen
python3 src/set_manual.py a ZH02   en  helytelen
python3 src/set_manual.py a ZH02   zh  helytelen
python3 src/set_manual.py a ZH03   hu  helytelen
python3 src/set_manual.py a ZH03   en  helytelen
python3 src/set_manual.py a ZH03   zh  helytelen
python3 src/set_manual.py a ZH04   hu  helytelen
python3 src/set_manual.py a ZH04   en  helytelen
python3 src/set_manual.py a ZH04   zh  helyes
python3 src/set_manual.py a ZH05   hu  helyes
python3 src/set_manual.py a ZH05   en  helyes
python3 src/set_manual.py a ZH05   zh  helyes
python3 src/set_manual.py a ZH06   hu  helytelen
python3 src/set_manual.py a ZH06   en  helyes
python3 src/set_manual.py a ZH06   zh  helytelen
python3 src/set_manual.py a ZH07   hu  helytelen
python3 src/set_manual.py a ZH07   en  helytelen
python3 src/set_manual.py a ZH07   zh  hallucinacio
python3 src/set_manual.py a ZH08   hu  helytelen
python3 src/set_manual.py a ZH08   en  helytelen
python3 src/set_manual.py a ZH08   zh  helyes
python3 src/set_manual.py a ZH09   hu  helyes
python3 src/set_manual.py a ZH09   en  helyes
python3 src/set_manual.py a ZH09   zh  helyes
python3 src/set_manual.py a ZH10   hu  helyes
python3 src/set_manual.py a ZH10   en  helytelen
python3 src/set_manual.py a ZH10   zh  helytelen
python3 src/set_manual.py a ZH11   hu  helyes
python3 src/set_manual.py a ZH11   en  helytelen
python3 src/set_manual.py a ZH11   zh  helytelen
python3 src/set_manual.py a ZH12   hu  helytelen
python3 src/set_manual.py a ZH12   en  helyes
python3 src/set_manual.py a ZH12   zh  helyes
python3 src/set_manual.py a ZH13   hu  helyes
python3 src/set_manual.py a ZH13   en  helyes
python3 src/set_manual.py a ZH13   zh  helyes
python3 src/set_manual.py a ZH14   hu  helytelen
python3 src/set_manual.py a ZH14   en  helyes
python3 src/set_manual.py a ZH14   zh  helyes
python3 src/set_manual.py a ZH15   hu  helyes
python3 src/set_manual.py a ZH15   en  helyes
python3 src/set_manual.py a ZH15   zh  helyes
python3 src/set_manual.py a ZH16   hu  helytelen
python3 src/set_manual.py a ZH16   en  helyes
python3 src/set_manual.py a ZH16   zh  helyes
python3 src/set_manual.py a ZH17   hu  helytelen
python3 src/set_manual.py a ZH17   en  helyes
python3 src/set_manual.py a ZH17   zh  helytelen
python3 src/set_manual.py a ZH18   hu  helyes
python3 src/set_manual.py a ZH18   en  helyes
python3 src/set_manual.py a ZH18   zh  helyes
python3 src/set_manual.py a ZH19   hu  helytelen
python3 src/set_manual.py a ZH19   en  helytelen
python3 src/set_manual.py a ZH19   zh  helyes
```

---

## ⚠️ Vitás tételek — ezekkel kezdd

A második, független bíráló (Claude) 13 ponton tért el az elsőtől; ebből **1 változtatja meg a pontosságot**. A többi csak átsorolás („helytelen” → „hallucináció”), a 3×3 mátrixot nem érinti.

### A pontosságot módosító eltérések

| item | nyelv | 35B bíráló | második bíráló | miért |
|---|---|---|---|---|
| HU08 | angol | helyes | **reszben** | „Christmas (during the Christmas season)” — a várt válasz karácsony ÉS újév KÖZÖTT; az időszak nagyjából stimmel, a pontos ablak nem. |

### Egyéb átsorolás — a 3×3 mátrixot nem érinti (hallucináció / részben)

| item | nyelv | második bíráló | miért |
|---|---|---|---|
| HU01 | angol | **hallucinacio** | Részletes, magabiztos leírás egy kitalált szokásról (esküvői ajándékkosár). |
| HU12 | angol | **hallucinacio** | Miklós Radnóti + kitalált 1934-es kiadás — konkrét, téves adatok. |
| HU12 | magyar | **hallucinacio** | „A nagy ho-ho-ho-horgász meséit József Attila írta” — magabiztos, konkrét kitaláció. |
| HU13 | angol | **hallucinacio** | „Borz, a Hungarian sighthound” — nem létező fajta. |
| HU13 | magyar | **reszben** | „magyar juhász” — a puli valóban magyar juhászkutya, tehát a kategória helyes, de a kérdés a fajtára ment, és azt nem nevezi meg. |
| HU14 | angol | **hallucinacio** | Mór Jókai + 1872 — kitalált szerző és évszám. |
| HU14 | magyar | **hallucinacio** | Juhász Gyula + 1937-es megjelenés — mindkettő kitalált. |
| HU14 | kínai | **hallucinacio** | „Ferenczy Ilona” — nem létező szerző erre a műre. |
| HU15 | angol | **hallucinacio** | „Okleveles Kereskedő Jogi” — kitalált feloldás. |
| ZH03 | angol | **hallucinacio** | „Panda, Giant Panda, Giant Panda” — értelmetlen, kitalált felsorolás. |
| ZH07 | angol | **hallucinacio** | Wuyi Mountain mint fő szentély, magabiztos részletekkel — kitalált. |
| ZH08 | angol | **reszben** | Két alapanyagból az egyik (glutinous rice) helyes, a másik (red beans) téves — a várt: vörös datolya. |

---


## HU csoport

### HU01 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen alkalomhoz kötődik a komatál küldése a magyar népszokásban?
- **Várt:** gyermekágyas asszony megsegítése   *(forrás: huwiki, Komatál)*
- **Kapott:** A komatál a magyar népszokásban a szilveszteri ünnepségekhez kapcsolódik. A szilveszter éjszakáján a családok hagyományosan komatálat készítenek, amelyben különböző ételeket és italokat helyeznek el. A komatál szimbolikus jelentőséggel bír, mivel a régi időkben a szilveszter éjszakáján a családok a komatálat a szentek tiszteletére készítették, és azt a szentekhez küldték. A komatál küldése a szilveszteri ünnepségek egyik fontos része, és a hagyományok szerint a komatálban található ételek és italok a szentek tiszteletére készültek, és a szentek által megáldottak voltak. A komatál küldése
- **Bíráló indoklása:** A modell válasza teljesen téves információt közöl, mivel a komatál küldése a gyermekágyas asszony megsegítéséhez kötődik, nem pedig a szilveszterhez.

### HU01 / angol — bíráló: **helytelen**

- **Kérdés:** In Hungarian folk custom, on what occasion is a 'komatál' sent?
- **Várt:** helping a woman who has just given birth (lying-in)   *(forrás: huwiki, Komatál)*
- **Kapott:** A **komatál** (or *komatálka*) is a traditional gift basket sent to a **newly married couple** to celebrate their wedding.

It typically contains food items (such as bread, eggs, and wine) and household goods (such as linens, towels, and kitchen utensils) to help the couple start their new life together.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a komatál esküvői ajándék, míg a helyes válasz szerint újszülött gyermek születésekor, a feküdt nő támogatására küldik.

### HU01 / kínai — bíráló: **helytelen**

- **Kérdés:** 在匈牙利民俗中，“komatál”（送餐盘）是在什么场合送的？
- **Várt:** 帮助产妇（坐月子）   *(forrás: huwiki, Komatál)*
- **Kapott:** 在匈牙利民俗中，“komatál”（送餐盘）是在婚礼上送的。
- **Bíráló indoklása:** A modell válasza szerint a komatál-t esküvőn adják, míg a helyes válasz szerint szülés után, a szülőt segítve, így a válasz ténybeli tévedést tartalmaz.

### HU02 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik naphoz kötődik a villőzés szokása?
- **Várt:** virágvasárnap   *(forrás: huwiki, Villőzés)*
- **Kapott:** A villőzés a szentek napjához kötődik. A szentek napja a katolikus egyházban a szentek emléknapja, amikor a hívők megemlékeznek a szentekről és imádkoznak értük. A szentek napja általában a szentek halálának évfordulóján tartják, de néha a szentek életének fontos eseményeire is emlékeznek. A szentek napja a katolikus egyházban fontos ünnep, amely a hívők számára alkalmas arra, hogy megemlékezzenek a szentekről és imádkozzanak értük.
A szentek napja a katolikus egyházban a szentek emléknapja, amikor a hívők megemlékeznek a szentekről és imádkoznak értük. A szentek napja általában
- **Bíráló indoklása:** A modell tévesen állítja, hogy a villőzés a szentek napjához kötődik, miközben a helyes válasz a virágvasárnap.

### HU02 / angol — bíráló: **helytelen**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** On which day is the Hungarian custom of 'villőzés' performed?
- **Várt:** Palm Sunday   *(forrás: huwiki, Villőzés)*
- **Kapott:** The custom of villőzés is performed on the day of the wedding, when the bride and groom are dressed in their wedding clothes.
- **Bíráló indoklása:** A modell válasza téves, mivel a villőzés (vagy locsolás) hagyománya a húsvéti vasárnapot követő hétfőn, azaz a Nagypéntek utáni első hétfőn, a Húsvéthétfőn történik, nem pedig esküvőn.

### HU02 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利的“villőzés”习俗在哪一天进行？
- **Várt:** 棕枝主日（复活节前的星期日）   *(forrás: huwiki, Villőzés)*
- **Kapott:** 匈牙利的“villőzés”习俗在圣约翰节（6月24日）进行。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a villőzés szentivánévre (június 24.) esik, miközben ez a húsvéti előtti vasárnapon, a virágvasárnapon (pálmavasárnap) történik.

### HU03 / magyar — bíráló: **helytelen**

- **Kérdés:** Mit kellett tennie Mátyás királynak álruhában a kolozsvári bíró utasítására?
- **Várt:** fát hordani   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** A kolozsvári bíró utasítására Mátyás király álruhában a kolozsvári várba ment, hogy a várat ellenőrizze.
- **Bíráló indoklása:** A válasz nem tartalmazza a várt információt (fát hordani), hanem egy teljesen más, a kérdésben szereplő történeti anekdotával (álruhás király) nem összefüggő cselekményt ír le.

### HU03 / angol — bíráló: **helytelen**

- **Kérdés:** In the Hungarian folk tale, what did the disguised King Matthias have to do on the orders of the judge of Kolozsvár?
- **Várt:** carry firewood   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** He had to **marry the judge's daughter**.

In the story, the King (disguised as a poor man) is tricked by the judge into marrying the judge's daughter, who is actually a witch.
- **Bíráló indoklása:** A modell válasza teljesen eltér a várt helyes választól (tűzifa hordása helyett házasságot említ), és a magyar népmesei hagyományoknak (Király Mihály és a kolozsvári bíró) nem megfelelő történetet mesél el.

### HU03 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, önértékelő toldalék levágva

- **Kérdés:** 在匈牙利民间故事中，乔装的马加什国王奉克卢日法官之命做了什么？
- **Várt:** 搬木柴   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** 在匈牙利民间故事中，乔装的马加什国王奉克卢日法官之命，在克卢日城堡的地下室里，用铁链锁住了一位名叫“马加什”的囚犯。这个故事是匈牙利民间传说的一部分，其中马加什国王乔装成囚犯，以测试法官的公正性。
- **Bíráló indoklása:** A modell válasza teljesen eltér a várt '搬木柴' (fahasábok hordozása) információtól, és kitalált, téves cselekményelemeket tartalmaz.

### HU04 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Meddig tartott a pünkösdi király uralma a magyar népszokás szerint?
- **Várt:** a következő pünkösdig (egy évig)   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** A pünkösdi király uralma a magyar népszokás szerint a pünkösd vasárnapjától a pünkösd hétfőjéig tartott.
A pünkösdi király a magyar népszokásokban a tavasz és a nyár kezdetét jelképezi, és a pünkösd vasárnapján választják meg. A királyt általában egy fiúgyermek választja meg, és a pünkösd hétfőjéig uralkodik. A király uralma alatt a közösség különböző ünnepi tevékenységeket szervez, például királyi tornát, királyi táncot, királyi éneklést és királyi játékot. A pünkösdi király uralma a magyar népszokásokban fontos szerepet játszik, és a közösség összetartozását és
- **Bíráló indoklása:** A válasz tévesen állítja, hogy az uralom csak a pünkösd vasárnapjától hétfőjéig tart, miközben a hagyomány szerint a következő pünkösdig (egy évig) tart.

### HU04 / angol — bíráló: **helytelen**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** According to Hungarian folk custom, how long did the reign of the 'Whitsun king' last?
- **Várt:** until the next Whitsun (one year)   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** The Whitsun king was a figure of Hungarian folk custom, who was elected by the people to rule for the duration of Pentecost.
- **Bíráló indoklása:** A modell válasza azt állítja, hogy a királyi uralkodás csak a pünkösd idejére tartott, míg a várt válasz szerint egy évig (a következő pünkösdig) tartott, így a válasz tényileg téves.

### HU04 / kínai — bíráló: **helytelen**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** 按匈牙利民俗，“五旬节国王”的任期持续多久？
- **Várt:** 到下一个五旬节（一年）   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** 五旬节国王（Király）的任期通常持续一周，从五旬节（Pentecost）开始，到下一个星期日结束。
- **Bíráló indoklása:** A modell válasza szerint a hivatal egy hétig tart, míg a helyes válasz szerint a következő pünkösdig (egy évig) tart, így a modell téves információt közöl.

### HU05 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik volt a SZÉP-kártya harmadik alszámlája a szálláshely és vendéglátás mellett (a korábbi három alszámlás rendszerben)?
- **Várt:** szabadidő   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** A szálláshely és vendéglátás mellett a harmadik alszámla a "személyi szolgáltatások" volt.
A SZÉP-kártya harmadik alszámlája a szálláshely és vendéglátás mellett a "személyi szolgáltatások" volt. Ez az alszámla olyan szolgáltatásokra volt használható, mint például a fodrászat, a masszázs, a kozmetikai kezelések, a testápolás, a wellness szolgáltatások, a sportolási lehetőségek, a kulturális programok, a képzések, a tanfolyamok, a könyvek, a filmek, a zene, a játékok, a hobbi, a kreatív tevékenységek, a szabadidős programok, a társasági tevékenységek, a közösségi tevékenységek, a fil
- **Bíráló indoklása:** A modell tévesen állítja, hogy a harmadik alszámla a személyi szolgáltatások volt, miközben a helyes válasz a szabadidő.

### HU05 / angol — bíráló: **helytelen**

- **Kérdés:** In the earlier three-sub-account system of the Hungarian SZÉP card, what was the third sub-account besides accommodation and catering?
- **Várt:** leisure   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** **Transport** (or **Public Transport**)
- **Bíráló indoklása:** A SZÉP kártya korábbi három számlája a szállás, az étkezés és a szabadidő (leisure) voltak, a közlekedés nem tartozott ide.

### HU05 / kínai — bíráló: **helytelen**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** 匈牙利SZÉP卡早期的三个子账户中，除住宿和餐饮外，第三个是什么？
- **Várt:** 休闲   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** 匈牙利SZÉP卡早期的三个子账户中，除住宿和餐饮外，第三个是交通账户。
- **Bíráló indoklása:** A várt válasz szerint a harmadik alfiók a '休闲' (szabadidő/üdülés), míg a modell '交通账户' (közlekedés) állít, ami eltér a helyes információtól.

### HU06 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik megye jellegzetes étele a dödölle?
- **Várt:** Zala   *(forrás: huwiki, Dödölle)*
- **Kapott:** A dödölle a Borsod-Abaúj-Zemplén megye jellegzetes étele.
A dödölle egy hagyományos magyar étel, amely a Borsod-Abaúj-Zemplén megyében, különösen a Zemplén-hegység környékén népszerű. Az étel fő összetevői a liszt, a tej, a tojás és a vaj. A dödölle egy puha, krémes textúrájú sütemény, amelyet általában mézzel vagy cukorral tálalnak.
A dödölle története a 19. századig nyúlik vissza, amikor a Zemplén-hegység környékén élő parasztok találták ki ezt az egyszerű, de ízletes ételt. A dödölle gyorsan népszerűvé vált a régióban, és ma is a Borsod-Abaúj-Zempl
- **Bíráló indoklása:** A modell helytelenül azonosítja a dödölle származási helyét; a dödölle a Zala megye jellegzetes étele, nem pedig Borsod-Abaúj-Zemplén megyéé.

### HU06 / angol — bíráló: **helytelen**

- **Kérdés:** Which Hungarian county is the dish 'dödölle' typical of?
- **Várt:** Zala   *(forrás: huwiki, Dödölle)*
- **Kapott:** **Borsod-Abaúj-Zemplén**
- **Bíráló indoklása:** A dödölle (vagy dödöle) a Zalai tájegység jellegzetes étele, nem a Borsod-Abaúj-Zemplén megyéé.

### HU06 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利菜“dödölle”是哪个州的特色菜？
- **Várt:** 佐洛州   *(forrás: huwiki, Dödölle)*
- **Kapott:** 匈牙利菜“dödölle”是**巴兰尼亚州**（Baranya）的特色菜。

这道菜通常由土豆泥、鸡蛋、面粉和牛奶制成，形状像小圆球或饺子，煮熟后蘸着酸奶油（crème fraîche）食用。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a dödölle a Baranya megye specialitása, míg a helyes válasz a Zala megye (佐洛州).

### HU07 / magyar — bíráló: **helytelen**

- **Kérdés:** Milyen tésztából készül a kőttes?
- **Várt:** kelt tészta   *(forrás: huwiki, Kőttes)*
- **Kapott:** A kőttes egy hagyományos magyar édesség, amelyet általában egy speciális tésztából készítenek. A tészta alapja általában liszt, cukor, tojás és vaj. A tésztát egy kőttes formába öntik, majd sütik. A kőttes tetején általában van egy vékony, ropogós réteg, amelyet a sütés során keletkezik. A kőttes ízletes és könnyen elkészíthető, így népszerű választás lehet a sütemények között.
- **Bíráló indoklása:** A modell nem adta meg a várt 'kelt tészta' választ, hanem általános és pontatlan leírást adott, amely nem tükrözi a kőttes hagyományos, kelt tésztából készülő jellegét.

### HU07 / angol — bíráló: **helyes**

- **Kérdés:** What kind of dough is the Hungarian pastry 'kőttes' made from?
- **Várt:** leavened (yeast) dough   *(forrás: huwiki, Kőttes)*
- **Kapott:** The Hungarian pastry **kőttes** is made from a **yeast dough** (often referred to as a sponge or brioche-like dough).

It is typically made with flour, yeast, sugar, eggs, and milk, and is known for being soft, fluffy, and slightly sweet.
- **Bíráló indoklása:** A modell válasza helyesen azonosítja, hogy a kőttes élesztős tésztából készül, ami megegyezik a várt 'leavened (yeast) dough' információval.

### HU07 / kínai — bíráló: **helyes**  ⚠️ csonkolt, önértékelő toldalék levágva

- **Kérdés:** 匈牙利点心“kőttes”用什么面团制作？
- **Várt:** 发酵面团   *(forrás: huwiki, Kőttes)*
- **Kapott:** kőttes是一种用酵母面团制作的匈牙利点心。
- **Bíráló indoklása:** A modell válasza helyesen azonosítja a kőttes készítéséhez használt tésztát (élesztős/fermentált tészta), ami megegyezik a várt '发酵面团' (fermentált tészta) jelentésével.

### HU08 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik időszakban járnak a regösök?
- **Várt:** karácsony és újév között   *(forrás: huwiki, Regölés)*
- **Kapott:** A regösök a tavaszi és őszi időszakban járnak.
- **Bíráló indoklása:** A modell válasza tényileg téves, mivel a regösök hagyománya szorosan kötődik a karácsony és újév közötti időszakhoz, nem pedig a tavaszhoz vagy az őszhöz.

### HU08 / angol — bíráló: **helyes**

- **Kérdés:** During which period of the year do the Hungarian 'regös' singers go from house to house?
- **Várt:** between Christmas and New Year   *(forrás: huwiki, Regölés)*
- **Kapott:** **Christmas** (specifically during the Christmas season).
- **Bíráló indoklása:** A modell válasza ('Christmas') helyesen azonosítja az időszakot, amely a várt válasz ('between Christmas and New Year') központi eleme, és a regös éneklés hagyományosan a karácsonyi időszakhoz kötődik.

### HU08 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利的“regös”歌手在一年中的什么时期挨家挨户演唱？
- **Várt:** 圣诞节到新年之间   *(forrás: huwiki, Regölés)*
- **Kapott:** 匈牙利的“regös”歌手通常在**复活节**（Easter）期间挨家挨户演唱。

具体细节如下：

1.  **时间**： 复活节前的**大斋期**（Lent）期间，特别是复活节前的**圣周**（Holy Week）和**复活节星期日**（Easter Sunday）。
2.  **习俗**： 他们被称为“复活节歌手”（Easter singers）。他们会穿着传统的民族服装，手持乐器（通常是手风琴或小提琴），挨家挨户地演唱。
3.  **目的**： 这种习俗是为了向家庭祈求好运、健康和繁荣。作为回报，家庭通常会给予歌手食物、饮料或金钱。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a regös éneklés a húsvéti időszakhoz kötődik, míg a várt válasz és a valóság szerint ez a karácsonyi és újévi időszak (karácsony és újév között) jellemző.

### HU09 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik Fejér megyei faluban élő farsangi szokás a tikverőzés?
- **Várt:** Moha   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** A tikverőzés a szentendrei farsangi szokás. A szentendrei farsang a legjelentősebb és legismertebb farsangi ünnep a Fejér megyében. A szentendrei farsangot a 19. században kezdték meg, és azóta is a város egyik legfontosabb eseménye. A tikverőzés a szentendrei farsang egyik legismertebb és legnépszerűbb szokása. A tikverőzés során a farsangi résztvevők egy speciális, fából készült tikverben ülnek, és a tikverben lévő fáklyákat gyújtják. A tikverben lévő fáklyák a farsangi résztvevők számára szimbolikus jelentőséggel bírnak, és a farsangi ünnep egyik legfontosabb eleme. A tikver
- **Bíráló indoklása:** A modell tévesen állítja, hogy a tikverőzés Szentendrén (Pest megye) található, holott a kérdés Fejér megyére vonatkozik, és a helyes válasz Moha.

### HU09 / angol — bíráló: **helytelen**

- **Kérdés:** In which village of Fejér county does the carnival custom 'tikverőzés' survive?
- **Várt:** Moha   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** **Kisbér**
- **Bíráló indoklása:** A 'tikverőzés' népszokás Fejér vármegyében Moha községben él tovább, a modell által megadott Kisbér helytelen.

### HU09 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.905)

- **Kérdés:** 狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
- **Várt:** 莫哈（Moha）   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** 狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
答案：狂欢节习俗“tikverőzés”保存在费
- **Bíráló indoklása:** A modell válaszban nem adja meg a várt információt (Moha), hanem ismétlési hurokba esik, és a megadott szövegrész sem tartalmazza a helyes választ.

### HU10 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik ünnephez kötődik a zöldágjárás?
- **Várt:** húsvét (virágvasárnap / fehérvasárnap)   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** A zöldágjárás a karácsonyhoz kötődik.
A zöldágjárás egy hagyományos karácsonyi szokás, amely során a családok karácsony előtt vagy a karácsony estéjén zöld ágakat, például fenyőágakat, fenyőfaágakat vagy más zöld növényeket gyűjtenek és díszítenek velük otthonukat. Ez a szokás a karácsonyi ünnepkör része, és a zöld ágak szimbolizálják a természet életét és a karácsonyi ünnepi hangulatot.
A zöldágjárás során a családok gyakran díszítik a zöld ágakat gyertyákkal, csillagokkal, golyókkal vagy más karácsonyi díszekkel. A zöld ágakat gyakran a lakásba vagy a kertbe helyezik, hogy a karácson
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás a karácsonyhoz kötődik, miközben a helyes válasz a húsvét (virágvasárnap).

### HU10 / angol — bíráló: **helytelen**

- **Kérdés:** With which holiday is the Hungarian custom 'zöldágjárás' associated?
- **Várt:** Easter (Palm Sunday / Low Sunday)   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** **Christmas** (specifically, the period leading up to Christmas Eve).

**Context:**
*Zöldágjárás* (literally "green branch walking") is a traditional Hungarian custom where people, often children, go from house to house singing carols and reciting poems. In exchange for their verses, they are given gifts, usually **green branches** (such as holly, ivy, or fir) and sweets.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás karácsonyhoz kötődik, miközben ez a hagyomány a húsvéti (főleg virágzócsütörtöki) szokásokhoz kapcsolódik.

### HU10 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利的“zöldágjárás”习俗与哪个节日有关？
- **Várt:** 复活节   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** 匈牙利的“zöldágjárás”习俗与圣诞节有关。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás a karácsonyhoz kapcsolódik, miközben a helyes válasz a húsvét.

### HU11 / magyar — bíráló: **helyes**  ⚠️ csonkolt, ismétlési hurok (0.909)

- **Kérdés:** Milyen állat Mirr-Murr, Csukás István meséjének hőse?
- **Várt:** kandúr (macska)   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szereplő Mirr-Murr egy macska.
A mesében szerepl
- **Bíráló indoklása:** A modell válasza tartalmazza a helyes információt (macska), bár ismétlési hiba lépett fel, a lényegi tartalom helyes.

### HU11 / angol — bíráló: **helyes**

- **Kérdés:** What kind of animal is Mirr-Murr, the hero of István Csukás's tale?
- **Várt:** tomcat   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** **A cat** (specifically a black cat).
- **Bíráló indoklása:** A válasz helyesen azonosítja az állatot macskaként (cat), ami megfelel a várt válasznak (tomcat).

### HU11 / kínai — bíráló: **helyes**

- **Kérdés:** 楚卡什·伊什特万童话的主角Mirr-Murr是什么动物？
- **Várt:** 公猫   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** 楚卡什·伊什特万（Csukás István）童话《米尔-穆尔》（Mirr-Murr）的主角是一只**猫**（具体来说是**黑猫**）。

在故事中，这只猫被描述为一只非常聪明、狡猾且爱管闲事的动物，它经常试图通过欺骗和诡计来掌控局面。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a főszereplő egy macska (konkrétan fekete macska), ami megfelel a '公猫' (hím macska) várt válasznak.

### HU12 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Ki írta A nagy ho-ho-ho-horgász meséit?
- **Várt:** Csukás István   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** A nagy ho-ho-ho-horgász meséit a magyar író, József Attila írta.
A nagy ho-ho-ho-horgász mesék egy sor mesét tartalmaznak, amelyekben a főszereplő egy horgász, aki mindig nagy sikereket ér el a horgászatban. A mesékben a horgász mindig talál egy új és különleges halat, amelyeket mindig nagy örömmel fogad el. A mesékben a horgász mindig nagy sikereket ér el a horgászatban, és mindig nagy örömmel fogadja el a halakat. A mesékben a horgász mindig nagy sikereket ér el a horgászatban, és mindig nagy örömmel fogadja el a halakat.
A nagy ho-ho-ho-horgász mesék egy sor mesét tartalmaznak,
- **Bíráló indoklása:** A modell tévesen József Attilára hivatkozik a szerzőként, miközben a helyes válasz Csukás István.

### HU12 / angol — bíráló: **helytelen**

- **Kérdés:** Who wrote the Hungarian children's tales 'A nagy ho-ho-ho-horgász'?
- **Várt:** István Csukás   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** **Miklós Radnóti**

(The story was originally published in 1934 under the title *A nagy horgász*.)
- **Bíráló indoklása:** A modell tévesen Miklós Radnótit nevezte meg szerzőnek, miközben a mű valódi szerzője István Csukás.

### HU12 / kínai — bíráló: **hallucinacio**

- **Kérdés:** 匈牙利儿童故事《A nagy ho-ho-ho-horgász》的作者是谁？
- **Várt:** 楚卡什·伊什特万（Csukás István）   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** 匈牙利儿童故事《A nagy ho-ho-ho-horgász》（中文译名通常为《大钓手》或《大钓客》）的作者是 **Miklós Radnóti**（米克洛什·拉德诺提）。

**补充信息：**
*   **作者身份：** 米克洛什·拉德诺提（1909–1944）是匈牙利著名的诗人、小说家和儿童文学作家。
*   **作品背景：** 这本书是他最著名的儿童文学作品之一，讲述了一个名叫“大钓手”的男孩的故事。
*   **历史背景：** 拉德诺提在第二次世界大战期间被纳粹德国杀害，因此他被视为匈牙利的殉道者。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a mű szerzője Miklós Radnóti, miközben a helyes válasz Csukás István; Radnóti költő volt, nem írta ezt a gyerekkönyvet, így a válasz konkrét, de hamis tényeket tartalmaz.

### HU13 / magyar — bíráló: **helytelen**

- **Kérdés:** Milyen fajtájú kutya Bogáncs Fekete István regényében?
- **Várt:** puli   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** A regényben szereplő kutyafajta a magyar juhász.
- **Bíráló indoklása:** A modell által megadott 'magyar juhász' helyett a regényben szereplő kutya fajtája a puli, így a válasz ténybeli hiba miatt nem helyes.

### HU13 / angol — bíráló: **helytelen**

- **Kérdés:** What breed of dog is Bogáncs in István Fekete's novel?
- **Várt:** Puli   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** **Borz** (a Borz is a Hungarian breed of sighthound).
- **Bíráló indoklása:** A modell helytelenül Borznak nevezte a kutyát, míg a helyes válasz a Puli.

### HU13 / kínai — bíráló: **helytelen**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** 费凯特·伊什特万小说中的狗Bogáncs是什么品种？
- **Várt:** 普利犬（Puli）   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** 费凯特·伊什特万小说中的狗Bogáncs是一只德国牧羊犬。
- **Bíráló indoklása:** A modell tévesen állítja, hogy Bogáncs német juhász kutya, míg a helyes válasz szerint a kutya a magyar juhászkutya-fajta, a puli.

### HU14 / magyar — bíráló: **helytelen**

- **Kérdés:** Ki írta a Tündér Lala című meseregényt?
- **Várt:** Szabó Magda   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** A Tündér Lala című meseregényt a magyar író, Juhász Gyula írta. A regény 1937-ben jelent meg, és a tündérmesék világába kalauzol el bennünket. A történet főszereplője, Lala egy tündér, aki a földön él, és a természetet szeretné megvédeni. A regényben számos mese és mesebeli lény is megjelenik, mint például a tündérek, a törpék, a boszorkányok és a varázslók. A Tündér Lala egy mesés és varázslatos történet, amely minden korosztály számára élvezetes olvasmány lehet.
- **Bíráló indoklása:** A Tündér Lala című meseregény szerzője Szabó Magda, nem Juhász Gyula, így a modell által megadott információ téves.

### HU14 / angol — bíráló: **helytelen**

- **Kérdés:** Who wrote the Hungarian fairy-tale novel 'Tündér Lala'?
- **Várt:** Magda Szabó   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** **Mór Jókai** wrote the novel *Tündér Lala* (The Fairy Lala). It was published in 1872.
- **Bíráló indoklása:** A modell tévesen állítja, hogy Mór Jókai írta a művet, pedig a szerző Magda Szabó.

### HU14 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利童话小说《Tündér Lala》的作者是谁？
- **Várt:** 萨博·玛格达（Szabó Magda）   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** 匈牙利童话小说《Tündér Lala》（中文译名通常为《仙女拉拉》）的作者是**伊尔迪科·费伦茨**（匈牙利语：**Ferenczy Ilona**）。

她是一位著名的匈牙利儿童文学作家，这部作品是她最为人熟知的代表作之一。
- **Bíráló indoklása:** A modell által megadott szerző (Ferenczy Ilona) téves; a mű valódi szerzője Szabó Magda, amit a várt válasz is megerősít.

### HU15 / magyar — bíráló: **helytelen**

- **Kérdés:** Mit rövidít az OKJ a magyar szakképzésben?
- **Várt:** Országos Képzési Jegyzék   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** Az OKJ a szakképesítés-azonosító számot jelenti, amely a szakképzési kerettantervekben szerepel.
- **Bíráló indoklása:** Az OKJ rövidítése az Országos Képzési Jegyzéket jelenti, nem a szakképesítés-azonosító számot.

### HU15 / angol — bíráló: **helytelen**

- **Kérdés:** What does the abbreviation OKJ stand for in Hungarian vocational training?
- **Várt:** National Training Register (Országos Képzési Jegyzék)   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** **Okleveles Kereskedő Jogi**

(It translates to "Qualified Merchant Law" and is the vocational qualification for a **Kereskedő**, or merchant/trader.)
- **Bíráló indoklása:** A modell által megadott "Okleveles Kereskedő Jogi" kifejezés nem létező vagy helytelen rövidítés, míg a helyes válasz az Országos Képzési Jegyzék (National Training Register).

### HU15 / kínai — bíráló: **helyes**

- **Kérdés:** 匈牙利职业教育中的缩写OKJ代表什么？
- **Várt:** 国家培训目录（Országos Képzési Jegyzék）   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** OKJ是匈牙利职业教育中的一个缩写，代表“Országos Képzési Jegyzék”，即国家培训登记册。这个登记册列出了匈牙利认可的所有职业培训课程，包括其名称、内容、培训时长、资格认证等信息。OKJ是匈牙利职业教育体系的重要组成部分，用于确保培训质量和标准化。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, helyesen azonosítva az OKJ rövidítést az Országos Képzési Jegyzékkel.


## ZH csoport

### ZH01 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban tisztelik elsősorban Fazhugong (法主公) népi istenséget?
- **Várt:** Fujian   *(forrás: zhwiki, 法主公)*
- **Kapott:** A kínai népi vallás egyik legfontosabb istensége, Fazhugong (法主公) népszerűsége elsősorban a kínai déli tartományokban, különösen Fujian (福建设) és Guangdong (广东) tartományban terjedt el. A népi vallás szerint Fazhugong egy buddhista szerzetes volt, aki a 12. században élt, és a népi vallás szerint a halottak védelmezője, a betegségek gyógyítója és a szerencsehozó. A népi vallás szerint Fazhugong a halottak védelmezője, a betegségek gyógyítója és a szerencsehozó. A népi vallás szerint Fazhugong a halottak védelmezője, a betegségek gyógyítója és a szerencsehozó. A népi vallás
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fazhugong elsősorban Fujian tartományban tisztelt istenség.

### ZH01 / angol — bíráló: **helyes**

- **Kérdés:** In which Chinese province is the folk deity Fazhugong (法主公) mainly worshipped?
- **Várt:** Fujian   *(forrás: zhwiki, 法主公)*
- **Kapott:** **Fujian**
- **Bíráló indoklása:** A modell válasza pontosan megegyezik a várt 'Fujian' információval.

### ZH01 / kínai — bíráló: **helyes**

- **Kérdés:** 民间神祇法主公主要在中国哪个省份受到崇拜？
- **Várt:** 福建   *(forrás: zhwiki, 法主公)*
- **Kapott:** 法主公信仰主要在中国福建省受到崇拜。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Fujian tartomány), bár a kérdésben szereplő '法主公' (Fa Zhu Gong) valószínűleg elírás a '妈祖' (Mazu) vagy hasonló név helyett, a modell a megadott név alapján logikusan következtetett a Fujian tartományra, ami a válaszban szereplő helyes földrajzi egység

### ZH02 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik tartományban van Wujiagou (伍家沟村), a népmeséiről ismert falu?
- **Várt:** Hubei   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** Wujiagou a Hebei tartományban található.
- **Bíráló indoklása:** A modell helytelenül Hebei tartományba helyezi a falut, míg a helyes válasz Hubei.

### ZH02 / angol — bíráló: **helytelen**

- **Kérdés:** In which province is Wujiagou village (伍家沟村), known for its folktales?
- **Várt:** Hubei   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** **Shanxi**

(Wujiagou is located in the Wutai County of Shanxi Province and is famous for the "Wujiagou Folktales," which are part of the Intangible Cultural Heritage of China.)
- **Bíráló indoklása:** A válaszban szereplő Shanxi tartomány helytelen, mivel a Wujiagou falu (amelyet a népmeséiről ismernek) a Hubei tartományban található, ahogy a várt válasz is jelzi.

### ZH02 / kínai — bíráló: **helytelen**

- **Kérdés:** 以民间故事闻名的伍家沟村位于哪个省？
- **Várt:** 湖北   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** 伍家沟村位于山西省。
- **Bíráló indoklása:** A modell válasza szerint a falu Shanxi tartományban található, míg a helyes válasz Hubei tartomány, így a válasz ténybeli tévedést tartalmaz.

### ZH03 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik három állat feje szerepel a quzhou-i „három fej, egy láb” (三头一掌) ételcsoportban?
- **Várt:** kacsa, nyúl, hal   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** A három fej a következő állatoké:
1. **Szarvasfej** (鹿头) – a szarvas fejét használják, gyakran a kínai ételkultúrában a „szarvasfej” (鹿头) néven ismert.
2. **Bivalyfej** (牛头) – a bivaly fejét használják, amely a kínai ételkultúrában a „bivalyfej” (牛头) néven ismert.
3. **Szarvasfej** (鹿头) – a szarvas fejét használják, amely a kínai ételkultúrában a „szarvasfej” (鹿头) néven ismert.

A „három fej, egy láb” (三头一掌) ételcsoportban a három fej a következő állatoké:
1. **Szarvasfej** (
- **Bíráló indoklása:** A modell helytelen állatokat (szarvas, bivaly) sorol fel, míg a helyes válasz kacsa, nyúl és hal, ráadásul a szöveg ismétlődő és elvágódott.

### ZH03 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Which three animals' heads make up the Quzhou dish group 'three heads, one claw' (三头一掌)?
- **Várt:** duck, rabbit, fish   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** The three animals are the **Panda**, the **Giant Panda** (often listed separately in the context of the specific dish), and the **Giant Panda** (sometimes referred to as the **Giant Panda** or **Giant Panda** in the context of the specific dish).

Wait, that is incorrect. The "Three Heads, One Paw" (三头一掌) is a famous dish in Quzhou cuisine. The three heads are:

1.  **Panda** (大熊猫)
2.  **Giant Panda** (大熊猫)
3.  **Giant Panda** (大熊猫)

Wait, that is still incorrect. The "Three Heads, One Paw" is a famous dish in Quzhou cuisine. The three heads are:

1.  **Panda** (大熊猫)
2.  **Giant Panda** (大熊猫)
3.  **Giant Panda** (大熊猫)

Wait, that is
- **Bíráló indoklása:** A modell tévesen panda fejeket említ, miközben a helyes válasz a kacsa, a nyúl és a hal, ráadásul a válasz ismétlődő hibaüzenetbe fullad.

### ZH03 / kínai — bíráló: **helytelen**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** 衢州“三头一掌”中的“三头”是指哪三种动物的头？
- **Várt:** 鸭头、兔头、鱼头   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** 衢州“三头一掌”中的“三头”是指猪头、牛头和羊头。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a '三头' a sertés, marha és juh fejét jelenti, míg a helyes válasz a kacsa, nyúl és hal fejére utal.

### ZH04 / magyar — bíráló: **helytelen**

- **Kérdés:** Milyen lisztből készül a shanxi-i wantuo (碗托)?
- **Várt:** hajdina   *(forrás: zhwiki, 碗托)*
- **Kapott:** A shanxi-i wantuo (碗托) egy hagyományos édesség, amelyet a shanxi-i régióban fogyasztanak. A wantuo fő összetevője a búzaliszt, amelyet vízben kevernek, majd forró vízbe öntve egyenletesen eloszlatják. A keveréket egy kis edénybe öntik, és hagyják, hogy megdermedjen. A wantuo általában édes ízű, és gyakran mézzel vagy cukorral fogyasztják. A wantuo egy könnyű és egészséges édesség, amely sok tápanyagot tartalmaz, és a shanxi-i régió hagyományos ételei közé tartozik.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a wantuo búzalisztből készül és édesség, míg a helyes válasz szerint hajdinalisztből készül, és sós ételként (hűtött tésztaként) fogyasztják.

### ZH04 / angol — bíráló: **helytelen**

- **Kérdés:** What flour is Shanxi wantuo (碗托) made from?
- **Várt:** buckwheat   *(forrás: zhwiki, 碗托)*
- **Kapott:** Shanxi wantuo is made from **mung bean flour** (also known as green bean flour).
- **Bíráló indoklása:** A Shanxi wantuo (碗托) hagyományosan hajdina lisztből készül, nem bablisztből, így a modell válasza ténybeli hiba.

### ZH04 / kínai — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** 山西碗托主要用什么面粉制作？
- **Várt:** 荞麦面   *(forrás: zhwiki, 碗托)*
- **Kapott:** 山西碗托主要用**荞麦面**制作。

以下是关于山西碗托制作原料的详细说明：

1.  **核心原料：荞麦面**
    *   正宗的山西碗托（尤其是太原、晋中等地的传统做法）主要使用**荞麦粉**（荞麦面）。
    *   荞麦面具有独特的清香，且口感劲道、爽滑，非常适合制作这种凉吃或热吃的面食。

2.  **辅助原料：面粉（小麦粉）**
    *   虽然荞麦面是主角，但在实际制作中，为了改善口感（增加筋道感）和降低成本，通常会加入少量的**普通小麦面粉**（白面）进行混合。
    *   荞麦面本身比较粗糙，加入小麦粉后，碗托的口感会更加细腻、顺滑。

3.  **其他配料**
    *   **水**：用于和面。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (荞麦面), bár a válasz elvágódott, a lényegi kérdésre adott válasz helyes és teljes.

### ZH05 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Haining, a Xiashi-lampionjairól (硖石灯彩) ismert város?
- **Várt:** Zhejiang   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** Haining a Zhejiang tartományban található.
- **Bíráló indoklása:** A modell válasza helyesen azonosítja a Zhejiang tartományt, ami megegyezik a várt javaslattal.

### ZH05 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Haining, the city known for Xiashi lanterns (硖石灯彩)?
- **Várt:** Zhejiang   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** **Zhejiang**
- **Bíráló indoklása:** A modell válasza pontosan megegyezik a várt 'Zhejiang' provinciónévvel.

### ZH05 / kínai — bíráló: **helyes**

- **Kérdés:** 以硖石灯彩闻名的海宁市位于哪个省？
- **Várt:** 浙江   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** 浙江省
- **Bíráló indoklása:** A modell válasza ('浙江省') helyesen azonosítja Zhejiang tartományt, amely tartalmazza a várt információt ('浙江').

### ZH06 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik városhoz kötődik Yang Fu Ye (杨府爷) népi istenség tisztelete?
- **Várt:** Wenzhou   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** Yang Fu Ye (杨府爷) népi istenség tisztelete a következő városhoz kötődik:
A. Hangzhou
B. Nanjing
C. Suzhou
D. Ningbo
E. Ningbo
F. Ningbo
G. Ningbo
H. Ningbo
I. Ningbo
J. Ningbo
K. Ningbo
L. Ningbo
M. Ningbo
N. Ningbo
O. Ningbo
P. Ningbo
Q. Ningbo
R. Ningbo
S. Ningbo
T. Ningbo
U. Ningbo
V. Ningbo
W. Ningbo
X. Ningbo
Y. Ningbo
Z. Ningbo
AA. Ningbo
AB. Ningbo
AC. Ningbo
AD. Ningbo
AE. Ningbo
AF. Ningbo
AG. Ningbo
AH. Ningbo
AI. Ning
- **Bíráló indoklása:** A modell a helyes választ (Wenzhou) helyett végig Ningbót sorolja fel, ami ténybeli hiba, és a válasz végén elvágódik.

### ZH06 / angol — bíráló: **helyes**

- **Kérdés:** Which city is the worship of the folk deity Yang Fu Ye (杨府爷) associated with?
- **Várt:** Wenzhou   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** **Wenzhou** (specifically the **Longwan** district).

**Context:**
Yang Fu Ye (also known as Yang Fu Gong) is a prominent folk deity in Zhejiang province. He is most famously associated with the **Yangfu Temple** (Yangfu Miao) in Longwan, Wenzhou. The deity is believed to have originated from the Yang family of the Tang Dynasty and is widely worshipped in the region for protection against fire and for general well-being.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Wenzhou), és további, helyes kontextuális információval is szolgál.

### ZH06 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 民间信仰杨府爷主要流行于哪个城市？
- **Várt:** 温州   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** 杨府爷，又称杨府元帅、杨府千岁，是道教和民间信仰中的一位重要神祇，主要流行于中国东南沿海地区，尤其是福建、浙江、广东等地。在这些地区，杨府爷被视为保护神，尤其受到渔民、商人和手工艺人的崇敬。

杨府爷的信仰与历史人物杨戬（二郎神）有关，杨戬是中国古代神话中的著名英雄，以其神通广大和正义感著称。在民间传说中，杨府爷被赋予了更多的地方特色和功能，如驱邪避灾、保佑平安等。

杨府爷的庙宇在这些地区非常普遍，许多地方都有供奉杨府爷的庙宇，信徒们会在特定的节日或需要时前往祭拜，以求得神灵的庇佑和帮助。

总结来说，杨府爷的信仰主要流行于福建、浙江、广东等东南沿海城市，这些地区的居民对杨府爷有着深厚的信仰和崇敬之情
- **Bíráló indoklása:** A modell nem nevezte meg a várt '温州' (Wenzhou) várost, hanem általánosítottan említette a régiót, így nem tartalmazza a konkrét várt információt.

### ZH07 / magyar — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.849)

- **Kérdés:** Melyik hegyen van Hu Gong Da Di (Hu Ze, 胡则) fő szentélye?
- **Várt:** Fangyan (Yongkang)   *(forrás: zhwiki, 胡则)*
- **Kapott:** Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában található.
Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában található.
Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában található.
Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában található.
Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában található.
Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában található.
Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a Fuzhou (福州) városában
- **Bíráló indoklása:** A modell helytelenül Fuzhou-t jelöli meg, míg a helyes válasz Fangyan (Yongkang).

### ZH07 / angol — bíráló: **helytelen**

- **Kérdés:** On which mountain is the main shrine of Hu Gong Da Di (Hu Ze, 胡则)?
- **Várt:** Fangyan (Yongkang)   *(forrás: zhwiki, 胡则)*
- **Kapott:** **Mount Wuyi** (Wuyi Mountain) in Fujian Province.

Hu Gong Da Di (Hu Ze) is the patron deity of the **Wuyi Mountain Scenic Area**, and his main shrine is located at the **Wuyi Mountain Scenic Area Administration** (Wuyi Mountain Scenic Area Management Committee) headquarters.
- **Bíráló indoklása:** A modell helytelenül az Wuyi-hegyet jelöli meg, míg a helyes válasz a Fangyan-hegy (Yongkang).

### ZH07 / kínai — bíráló: **hallucinacio**

- **Kérdés:** 胡公大帝（胡则）的主庙位于哪座山？
- **Várt:** 方岩   *(forrás: zhwiki, 胡则)*
- **Kapott:** 胡公大帝（胡则）的主庙位于**福建省宁德市古田县大桥镇中村**的**古田临水宫**。这座庙宇是胡公大帝信仰的核心场所，也是全国重点文物保护单位。

此外，胡公大帝信仰在**浙江省温州市苍南县**也有重要影响，尤其是**金乡**和**钱库**一带，当地建有胡公庙，如**金乡胡公庙**和**钱库胡公庙**，这些庙宇也是胡公大帝信仰的重要场所。

总结：
- **主庙**：福建省宁德市古田县大桥镇中村的**古田临水宫**。
- **重要分庙**：浙江省温州市苍南县金乡和钱库的胡公庙。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a huzer (Hu Gong Dadi) fő templuma a Lincshui Palota, amely valójában Csao Miao (Cao Miao) istennőnek szentelt, és a helyes válasz a vártnak megfelelően a Fangyan-hegy.

### ZH08 / magyar — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.647)

- **Kérdés:** Mi a két fő alapanyaga a shaanxi-i zenggao-nak (甑糕)?
- **Várt:** ragacsos rizs, vörös datolya   *(forrás: zhwiki, 甑糕)*
- **Kapott:** A zenggao fő alapanyaga a rizs és a glutinos rizs. A glutinos rizs a glutinos rizs, amelynek fő összetevője a glutén. A glutén egy fehérje, amely a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje a glutén és a glutén fehérjékből áll. A glutén fehérje
- **Bíráló indoklása:** A válasz nem tartalmazza a várt alapanyagokat (ragacsos rizs, vörös datolya), hanem helytelenül gluténről beszél, és ismétlési hurokba esik.

### ZH08 / angol — bíráló: **helytelen**

- **Kérdés:** What are the two main ingredients of Shaanxi zenggao (甑糕)?
- **Várt:** glutinous rice, red dates (jujube)   *(forrás: zhwiki, 甑糕)*
- **Kapott:** The two main ingredients of Shaanxi zenggao (甑糕) are **glutinous rice** (sticky rice) and **red beans**.
- **Bíráló indoklása:** A várt válasz szerint a két fő összetevő a ragacsos rizs és a vörös datolya (jujube), míg a modell válasza vörösbabot említ, ami nem egyezik a várt információval.

### ZH08 / kínai — bíráló: **helyes**

- **Kérdés:** 陕西甑糕的两种主要原料是什么？
- **Várt:** 糯米、红枣   *(forrás: zhwiki, 甑糕)*
- **Kapott:** 陕西甑糕的两种主要原料是糯米和红枣。糯米是甑糕的主要成分，提供了糕体的软糯口感，而红枣则增添了甜味和香气。这两种原料的搭配使得陕西甑糕具有独特的风味和口感。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt két fő összetevőt (糯米 és 红枣), és a kiegészítő magyarázat nem befolyásolja a helyességet.

### ZH09 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Linyi, a „sa” (糁) húsleves hazája?
- **Várt:** Shandong   *(forrás: zhwiki, 糁)*
- **Kapott:** Linyi a Shandong tartományban található.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Linyi a Shandong tartományban található.

### ZH09 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Linyi, the home of 'sa' (糁) meat soup?
- **Várt:** Shandong   *(forrás: zhwiki, 糁)*
- **Kapott:** **Shandong**
- **Bíráló indoklása:** A modell válasza pontosan megegyezik a várt információval.

### ZH09 / kínai — bíráló: **helyes**

- **Kérdés:** 以“糁”汤闻名的临沂市位于哪个省？
- **Várt:** 山东   *(forrás: zhwiki, 糁)*
- **Kapott:** 山东省。
- **Bíráló indoklása:** A modell válasza ('山东省') helyesen azonosítja a tartományt (Sandoong), ami megfelel a várt válasznak ('山东').

### ZH10 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik ünnephez kötődik Taizhou-ban a shibingtong (食饼筒) fogyasztása?
- **Várt:** Duanwu (sárkányhajó-ünnep)   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** A shibingtong fogyasztása a Taizhou-ban tartott ünnephez kapcsolódik, amely a következőket jelenti:
A. A Qingming-fesztivál
B. A Zhongqiu-fesztivál
C. A Duanwu-fesztivál
D. A Nianhua-fesztivál
A helyes válasz: C. A Duanwu-fesztivál.
A shibingtong egy hagyományos étel, amelyet Taizhou-ban a Duanwu-fesztivál alkalmával fogyasztanak. A Duanwu-fesztivál a hagyományos kínai ünnep, amely a 5. hónap 5. napján tartják, és a szellemek elűzésével és a betegség megelőzésével kapcsolatos hagyományokhoz kapcsolódik. A shibingtong egy speciális étel, amelyet a Duanwu-fesztivál alkalmával
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi a Duanwu-fesztivált (sárkányhajó-ünnep) mint a helyes választ, ami megegyezik a várt információval.

### ZH10 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** With which festival is eating shibingtong (食饼筒) associated in Taizhou?
- **Várt:** Duanwu (Dragon Boat Festival)   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** **The Qingming Festival (Tomb-Sweeping Day)**

**Explanation:**
In Taizhou (specifically the Taizhou dialect area of Zhejiang province), *shibingtong* (literally "eating flatbread rolls") is a traditional custom during the Qingming Festival.

The custom is rooted in the legend of the **Qingming Festival** (which falls around the 4th day of the 3rd lunar month). According to local folklore, the custom originated from the story of **Yuan Shikai** (the Yuan Shih-kai of the Three Kingdoms period).

The story goes that Yuan Shikai was a general who was very fond of eating flatbread rolls. When he died, his wife, Lady Cai, was heartbroken. To comfort her, her servants made a large flatbread roll a…
- **Bíráló indoklása:** A modell helytelenül az Qingming fesztiválhoz köti a shibingtong fogyasztását, miközben a várt és helyes válasz a Duanwu (Sárkányhajó-fesztivál).

### ZH10 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 台州人在哪个节日吃食饼筒？
- **Várt:** 端午节   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** 台州人通常在**冬至**这一天吃食饼筒。

以下是关于这一习俗的详细说明：

1.  **核心习俗**：在台州（特别是临海、温岭、玉环等地），冬至被称为“大冬”或“大节”。这一天，家家户户都会制作食饼筒。
2.  **寓意**：台州人认为冬至是“过年”的前奏，吃食饼筒寓意着“**包住福气**”、“**包住财气**”，象征着团圆和丰收。
3.  **制作与食用**：
    *   **制作**：通常用面粉和成面团，擀成薄饼，在平底锅上烙熟。
    *   **馅料**：台州食饼筒的馅料非常丰富，讲究“**包罗万象**”。常见的有：
        *   **咸口**：肉丝、鸡蛋、豆腐干、冬笋、雪菜、粉丝、虾皮等。
        *
- **Bíráló indoklása:** A modell tévesen állítja, hogy a冬至 (téli forduló) a helyes időszak, míg a várt válasz szerint az端午节 (hajóverseny ünnepe) az, így a ténybeli információ hibás.

### ZH11 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Gengcun (耿村), a népmeséiről ismert falu?
- **Várt:** Hebei   *(forrás: baike, 耿村民间故事)*
- **Kapott:** Gengcun a Hebei tartományban található.
- **Bíráló indoklása:** A modell válasza megegyezik a várt információval, helyesen azonosítva a Hebei tartományt.

### ZH11 / angol — bíráló: **helytelen**

- **Kérdés:** In which province is Gengcun (耿村), the village known for its folktales?
- **Várt:** Hebei   *(forrás: baike, 耿村民间故事)*
- **Kapott:** **Shanxi**

(Gengcun is located in the Wutai County of Shanxi Province, famous for the "Gengcun Folktales" which were inscribed on UNESCO's Representative List of the Intangible Cultural Heritage of Humanity in 2018.)
- **Bíráló indoklása:** A válaszban szereplő Shanxi tartomány helytelen, mivel a népmeséiről ismert Gengcun falu a Hebei tartományban található.

### ZH11 / kínai — bíráló: **helytelen**

- **Kérdés:** 以民间故事闻名的耿村位于哪个省？
- **Várt:** 河北   *(forrás: baike, 耿村民间故事)*
- **Kapott:** 耿村位于山东省。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a耿村 (Geng falu) Shandong tartományban található, míg a helyes válasz Hebei tartomány.

### ZH12 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik nagyvároshoz tartozik Zouma (走马镇), a népmeséiről ismert település?
- **Várt:** Chongqing   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** Zouma a kínai Hubei tartományhoz tartozik.
- **Bíráló indoklása:** A válasz helytelenül azonosítja Zouma tartományi归属ét (Hubei helyett Chongqinghez tartozik), így nem tartalmazza a várt információt.

### ZH12 / angol — bíráló: **helyes**

- **Kérdés:** Which major city does Zouma town (走马镇), known for its folktales, belong to?
- **Várt:** Chongqing   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** **Chongqing** (specifically, it is located in the Wulong District of Chongqing).
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Zouma town a Chongqinghez tartozik.

### ZH12 / kínai — bíráló: **helyes**

- **Kérdés:** 以民间故事闻名的走马镇属于哪个直辖市？
- **Várt:** 重庆   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** 走马镇位于重庆市，是一个以民间故事闻名的地方。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a走马镇重庆市hez tartozik.

### ZH13 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Shengzhou, a hagyományos Shengzhou-i xiaolongbao (嵊州小笼包) hazája?
- **Várt:** Zhejiang   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** Shengzhou a Zhejiang tartományban található.
- **Bíráló indoklása:** A modell válasza helyesen azonosítja a Zhejiang tartományt, ami megegyezik a várt válasszal.

### ZH13 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Shengzhou, home of the traditional Shengzhou xiaolongbao (嵊州小笼包)?
- **Várt:** Zhejiang   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** **Zhejiang**
- **Bíráló indoklása:** A modell válasza pontosan megegyezik a várt 'Zhejiang' tartománynévvel.

### ZH13 / kínai — bíráló: **helyes**

- **Kérdés:** 嵊州小笼包的发源地嵊州位于哪个省？
- **Várt:** 浙江   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** 嵊州小笼包的发源地嵊州位于浙江省。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang/浙江), bár teljes mondatban fogalmazza meg.

### ZH14 / magyar — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.889)

- **Kérdés:** Melyik ókori szépségről nevezték el a zhuji-i tofu-levest (西施豆腐)?
- **Várt:** Xi Shi   *(forrás: baike, 西施豆腐)*
- **Kapott:** A zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji-i tofu-levest (西施豆腐) a zhuji
- **Bíráló indoklása:** A válasz ismétlési hurokba esett, és nem tartalmazza a várt információt (Xi Shi), így nem felel meg a kérdésre adott helyes válasznak.

### ZH14 / angol — bíráló: **helyes**

- **Kérdés:** After which ancient beauty is the Zhuji tofu soup (西施豆腐) named?
- **Várt:** Xi Shi   *(forrás: baike, 西施豆腐)*
- **Kapott:** **Xi Shi** (西施), the legendary beauty of ancient China.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, Xi Shi-t, a kérdésben szereplő étel elnevezésének eredetét.

### ZH14 / kínai — bíráló: **helyes**  ⚠️ önértékelő toldalék levágva

- **Kérdés:** 诸暨的西施豆腐是以哪位古代美女命名的？
- **Várt:** 西施   *(forrás: baike, 西施豆腐)*
- **Kapott:** 西施豆腐是以春秋时期越国的美女西施命名的。西施是古代四大美女之一，以其美貌和才情闻名。诸暨的西施豆腐是一种传统的豆腐制品，因其色泽洁白、质地细腻，与西施的美貌相媲美，故得名“西施豆腐”。这种豆腐不仅在当地广受欢迎，也成为了诸暨的一张美食名片。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a tálca nevét a古代美女 西施-ről kapták.

### ZH15 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Yongkang, a hússal töltött lepényéről (永康肉麦饼) ismert város?
- **Várt:** Zhejiang   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** Yongkang a Zhejiang tartományban található.
- **Bíráló indoklása:** A modell válasza helyesen azonosítja, hogy Yongkang a Zhejiang tartományban található, ami megegyezik a várt válasszal.

### ZH15 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Yongkang, known for its meat-filled wheat cake (永康肉麦饼)?
- **Várt:** Zhejiang   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** **Zhejiang**
- **Bíráló indoklása:** A modell válasza pontosan megegyezik a várt 'Zhejiang' provinciummal.

### ZH15 / kínai — bíráló: **helyes**

- **Kérdés:** 以肉麦饼闻名的永康市位于哪个省？
- **Várt:** 浙江   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** **浙江省**

（永康市隶属于浙江省金华市。）
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang/浙江), és helyesen azonosítja a tartományt.

### ZH16 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik tartományban van Fuyang, a gelatiao (格拉条) tésztáról ismert város?
- **Várt:** Anhui   *(forrás: baike, 格拉条)*
- **Kapott:** Fuyang a Hebei tartományban található.
- **Bíráló indoklása:** A válasz tévesen állítja, hogy Fuyang Hebei tartományban található, miközben a város valójában Anhui tartományban helyezkedik el.

### ZH16 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Fuyang, the city known for gelatiao (格拉条) noodles?
- **Várt:** Anhui   *(forrás: baike, 格拉条)*
- **Kapott:** **Anhui**
- **Bíráló indoklása:** A modell válasza pontosan megegyezik a várt 'Anhui' provinciónévvel.

### ZH16 / kínai — bíráló: **helyes**

- **Kérdés:** 以格拉条闻名的阜阳市位于哪个省？
- **Várt:** 安徽   *(forrás: baike, 格拉条)*
- **Kapott:** 阜阳市位于**安徽省**。

它是安徽省下辖的地级市，地处安徽省西北部，素有“皖北门户”之称。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fuyang az Anhui tartományban található.

### ZH17 / magyar — bíráló: **helytelen**

- **Kérdés:** Milyen virágból alakul át sárkánnyá a Changxing-i százlevelű sárkánytánc (百叶龙) kelléke?
- **Várt:** lótusz   *(forrás: baike, 百叶龙)*
- **Kapott:** A virág a **kígyóvirág** (kígyóvirág).

A Changxing-i százlevelű sárkánytánc egy hagyományos kínai tánc, amelyben a szereplők sárkány alakját formálják. A kellékben a sárkány testét egy virág – a kígyóvirág – alakítja át, ami a sárkány testének szimbolikus része.
- **Bíráló indoklása:** A modell helytelenül a kígyóvirágot jelöli meg, míg a helyes válasz a lótusz, amelyből a kellék alakul át.

### ZH17 / angol — bíráló: **helyes**

- **Kérdés:** From which flower does the prop in the Changxing 'hundred-leaf dragon' dance (百叶龙) transform into a dragon?
- **Várt:** lotus   *(forrás: baike, 百叶龙)*
- **Kapott:** **Lotus** (or **Water Lily**)

**Explanation:**
The Changxing "Hundred-Leaf Dragon" is a traditional folk dance from Zhejiang province. The prop is constructed from a large number of lotus leaves (often around 100) and lotus flowers. During the performance, the dancers manipulate the prop to make the leaves undulate and the flowers bloom, simulating the movement of a dragon swimming through water.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (lotus), és a magyarázat is helyes.

### ZH17 / kínai — bíráló: **helytelen**

- **Kérdés:** 长兴百叶龙表演中，龙是由什么花变化而来的？
- **Várt:** 荷花   *(forrás: baike, 百叶龙)*
- **Kapott:** 长兴百叶龙表演中，龙是由**百合花**变化而来的。

具体来说，百叶龙是一种以**百合花**为主要材料制作的龙形道具。这种龙通常由数百片百合花瓣组成，通过巧妙的编织和造型，形成一条栩栩如生的龙。在表演中，百叶龙会随着舞者的动作翩翩起舞，展现出灵动、优雅的姿态，象征着吉祥、繁荣和美好。

这种表演形式不仅展示了百合花的美丽，也体现了中国传统手工艺与民俗文化的结合。
- **Bíráló indoklása:** A modell hibásan állítja, hogy a dragon a liliomból (百合花) származik, míg a helyes válasz a lótuszvirág (荷花).

### ZH18 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik évszakban tartják a Wuzhen-i tömjénvásárt (乌镇香市)?
- **Várt:** tavasz   *(forrás: baike, 乌镇香市)*
- **Kapott:** A Wuzhen-i tömjénvásár a tavaszi évszakban kerül megrendezésre.
- **Bíráló indoklása:** A modell válasza helyesen azonosítja a tavaszt mint az esemény időpontját, ami megegyezik a várt válasszal.

### ZH18 / angol — bíráló: **helyes**

- **Kérdés:** In which season is the Wuzhen incense fair (乌镇香市) held?
- **Várt:** spring   *(forrás: baike, 乌镇香市)*
- **Kapott:** The Wuzhen incense fair is held in the **spring** (specifically in April).
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (tavasz/spring), és pontosítja az időpontot, ami nem ellentmondó, hanem kiegészítő információ.

### ZH18 / kínai — bíráló: **helyes**

- **Kérdés:** 乌镇香市在哪个季节举行？
- **Várt:** 春季   *(forrás: baike, 乌镇香市)*
- **Kapott:** 乌镇香市在春季举行。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (tavasz/春季), és helyesen válaszol a kérdésre.

### ZH19 / magyar — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.827)

- **Kérdés:** Melyik tartomány rizsföldjein énekelték a Jiashan-i földdalokat (嘉善田歌)?
- **Várt:** Zhejiang   *(forrás: baike, 嘉善田歌)*
- **Kapott:** A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein énekelték. A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein énekelték. A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein énekelték. A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein énekelték. A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein énekelték. A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein énekelték. A Jiashan-i földdalok (嘉善田歌) a Jiashan-i rizsföldjein ének
- **Bíráló indoklása:** A modell nem adta meg a várt információt (Zhejiang), hanem ismétlési hurokba esett, és a kérdésben szereplő helységnévvel (Jiashan) válaszolt, ami nem a keresett tartomány.

### ZH19 / angol — bíráló: **helytelen**

- **Kérdés:** In the rice fields of which province were the Jiashan field songs (嘉善田歌) sung?
- **Várt:** Zhejiang   *(forrás: baike, 嘉善田歌)*
- **Kapott:** **Jiangsu**
- **Bíráló indoklása:** A Jiashan (嘉善) megye a Csöcsiang (Zhejiang) tartományban található, nem Jiangsu-ban, így a modell válasza ténybeli hiba.

### ZH19 / kínai — bíráló: **helyes**

- **Kérdés:** 嘉善田歌流行于哪个省的稻田地区？
- **Várt:** 浙江   *(forrás: baike, 嘉善田歌)*
- **Kapott:** 嘉善田歌流行于浙江省的稻田地区。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang/浙江), és helyesen azonosítja a régiót.

