# Kézi ellenőrző ív — Mérés A (ZH + HU csoport)

**102 válasz.** Ahol egyetértesz a bíráló ítéletével, nincs teendő. Ahol nem, add meg a
`code/set_manual.py`-nak: `python3 code/set_manual.py a <item> <nyelv> <ítélet>`
(`helyes` / `reszben` / `helytelen` / `hallucinacio`), majd `python3 code/analyze_a.py`.

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
python3 code/set_manual.py a HU01   hu  helyes
python3 code/set_manual.py a HU01   en  helyes
python3 code/set_manual.py a HU01   zh  helytelen
python3 code/set_manual.py a HU02   hu  helytelen
python3 code/set_manual.py a HU02   en  helytelen
python3 code/set_manual.py a HU02   zh  helyes
python3 code/set_manual.py a HU03   hu  helytelen
python3 code/set_manual.py a HU03   en  helytelen
python3 code/set_manual.py a HU03   zh  helytelen
python3 code/set_manual.py a HU04   hu  helytelen
python3 code/set_manual.py a HU04   en  helytelen
python3 code/set_manual.py a HU04   zh  helytelen
python3 code/set_manual.py a HU05   hu  helytelen
python3 code/set_manual.py a HU05   en  helyes
python3 code/set_manual.py a HU05   zh  helyes
python3 code/set_manual.py a HU06   hu  helytelen
python3 code/set_manual.py a HU06   en  helytelen
python3 code/set_manual.py a HU06   zh  helytelen
python3 code/set_manual.py a HU07   hu  helytelen
python3 code/set_manual.py a HU07   en  helyes
python3 code/set_manual.py a HU07   zh  helyes
python3 code/set_manual.py a HU08   hu  helytelen
python3 code/set_manual.py a HU08   en  helytelen
python3 code/set_manual.py a HU08   zh  helytelen
python3 code/set_manual.py a HU09   hu  helytelen
python3 code/set_manual.py a HU09   en  helytelen
python3 code/set_manual.py a HU09   zh  helytelen
python3 code/set_manual.py a HU10   hu  helytelen
python3 code/set_manual.py a HU10   en  helytelen
python3 code/set_manual.py a HU10   zh  helyes
python3 code/set_manual.py a HU11   hu  helyes
python3 code/set_manual.py a HU11   en  helytelen
python3 code/set_manual.py a HU11   zh  helyes
python3 code/set_manual.py a HU12   hu  helytelen
python3 code/set_manual.py a HU12   en  helytelen
python3 code/set_manual.py a HU12   zh  helytelen
python3 code/set_manual.py a HU13   hu  helytelen
python3 code/set_manual.py a HU13   en  helytelen
python3 code/set_manual.py a HU13   zh  helytelen
python3 code/set_manual.py a HU14   hu  helytelen
python3 code/set_manual.py a HU14   en  helytelen
python3 code/set_manual.py a HU14   zh  helytelen
python3 code/set_manual.py a HU15   hu  helyes
python3 code/set_manual.py a HU15   en  helyes
python3 code/set_manual.py a HU15   zh  helyes
python3 code/set_manual.py a ZH01   hu  helyes
python3 code/set_manual.py a ZH01   en  helyes
python3 code/set_manual.py a ZH01   zh  helyes
python3 code/set_manual.py a ZH02   hu  helytelen
python3 code/set_manual.py a ZH02   en  helytelen
python3 code/set_manual.py a ZH02   zh  helytelen
python3 code/set_manual.py a ZH03   hu  helytelen
python3 code/set_manual.py a ZH03   en  helytelen
python3 code/set_manual.py a ZH03   zh  helytelen
python3 code/set_manual.py a ZH04   hu  helytelen
python3 code/set_manual.py a ZH04   en  helytelen
python3 code/set_manual.py a ZH04   zh  helytelen
python3 code/set_manual.py a ZH05   hu  helyes
python3 code/set_manual.py a ZH05   en  helyes
python3 code/set_manual.py a ZH05   zh  helyes
python3 code/set_manual.py a ZH06   hu  helytelen
python3 code/set_manual.py a ZH06   en  helytelen
python3 code/set_manual.py a ZH06   zh  helyes
python3 code/set_manual.py a ZH07   hu  helytelen
python3 code/set_manual.py a ZH07   en  helytelen
python3 code/set_manual.py a ZH07   zh  helytelen
python3 code/set_manual.py a ZH08   hu  helytelen
python3 code/set_manual.py a ZH08   en  helytelen
python3 code/set_manual.py a ZH08   zh  helyes
python3 code/set_manual.py a ZH09   hu  helyes
python3 code/set_manual.py a ZH09   en  helyes
python3 code/set_manual.py a ZH09   zh  helyes
python3 code/set_manual.py a ZH10   hu  helyes
python3 code/set_manual.py a ZH10   en  helytelen
python3 code/set_manual.py a ZH10   zh  helytelen
python3 code/set_manual.py a ZH11   hu  helytelen
python3 code/set_manual.py a ZH11   en  helytelen
python3 code/set_manual.py a ZH11   zh  helytelen
python3 code/set_manual.py a ZH12   hu  helyes
python3 code/set_manual.py a ZH12   en  helyes
python3 code/set_manual.py a ZH12   zh  helyes
python3 code/set_manual.py a ZH13   hu  helyes
python3 code/set_manual.py a ZH13   en  helyes
python3 code/set_manual.py a ZH13   zh  helyes
python3 code/set_manual.py a ZH14   hu  helyes
python3 code/set_manual.py a ZH14   en  helyes
python3 code/set_manual.py a ZH14   zh  helyes
python3 code/set_manual.py a ZH15   hu  helyes
python3 code/set_manual.py a ZH15   en  helyes
python3 code/set_manual.py a ZH15   zh  helyes
python3 code/set_manual.py a ZH16   hu  helyes
python3 code/set_manual.py a ZH16   en  helyes
python3 code/set_manual.py a ZH16   zh  helyes
python3 code/set_manual.py a ZH17   hu  helytelen
python3 code/set_manual.py a ZH17   en  helyes
python3 code/set_manual.py a ZH17   zh  helytelen
python3 code/set_manual.py a ZH18   hu  helyes
python3 code/set_manual.py a ZH18   en  helyes
python3 code/set_manual.py a ZH18   zh  helyes
python3 code/set_manual.py a ZH19   hu  helyes
python3 code/set_manual.py a ZH19   en  helyes
python3 code/set_manual.py a ZH19   zh  helyes
```


## HU csoport

### HU01 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Milyen alkalomhoz kötődik a komatál küldése a magyar népszokásban?
- **Várt:** gyermekágyas asszony megsegítése   *(forrás: huwiki, Komatál)*
- **Kapott:** A **komatál** (vagy komatálka) küldése a magyar népszokásokban szorosan kötődik a **szülésekhez**, pontosabban az újszülött születése után a családhoz intézett első látogatásokhoz.

Ez a szokás a 19. és 20. század fordulóján volt leggyakoribb, amikor a szomszédok, rokonok és barátok a kisbabát üdvözölték. A látogatók nem üres kézzel érkeztek: egy különleges, gyakran díszes, kék vagy piros színű, fedővel ellátott tálkát hoztak magukkal. Ebben a tálban általában **pénzt** (néha érméket, néha bankjegyeket), **cukrot**, **gyümölcsöt** vagy **mé
- **Bíráló indoklása:** A válasz helyesen azonosítja a szülést (és az azt követő időszakot) mint a komatál küldésének alkalmát, ami egyezik a várt 'gyermekágyas asszony megsegítése' információval.

### HU01 / angol — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** In Hungarian folk custom, on what occasion is a 'komatál' sent?
- **Várt:** helping a woman who has just given birth (lying-in)   *(forrás: huwiki, Komatál)*
- **Kapott:** In Hungarian folk custom, a **komatál** (literally "soup bowl") is traditionally sent as a gift to a **new mother** after the birth of her child.

The custom dates back to the 19th century and was deeply rooted in the belief that a new mother needed extra nourishment and strength to recover from childbirth and to produce enough milk for the infant. The gift typically consisted of a large, sturdy bowl (often made of earthenware or later, metal) accompanied by a generous amount of soup, usually a rich meat or vegetable broth.

The act of sending the *komatál* served several social functions:
*   **Nutritional Support**: It provided immediate, easy-to-digest calories and fluids.
*   **Community…
- **Bíráló indoklása:** A válasz helyesen azonosítja, hogy a komatál újszülött gyermek után, a szülést követő gyógyulási időszakban (lying-in) küldött ajándék, ami egyezik a várt válasszal.

### HU01 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 在匈牙利民俗中，“komatál”（送餐盘）是在什么场合送的？
- **Várt:** 帮助产妇（坐月子）   *(forrás: huwiki, Komatál)*
- **Kapott:** 在匈牙利民俗中，**komatál**（字面意为“盛满食物的盘子”或“丰盛的餐盘”）通常是在**婚礼**（特别是新娘出嫁时）这一重要场合赠送的。

这是一种极具象征意义的传统礼物，其核心寓意是**祝福新婚夫妇未来生活富足、衣食无忧**。

以下是关于这一习俗的具体细节：

*   **赠送对象与场合**：它主要由新娘的娘家亲友（尤其是女性亲属）在婚礼当天送给新娘。这通常发生在新娘离开娘家前往新郎家，或者在婚礼宴席期间。
*   **物品构成**：这个“盘子”并不一定是一个真实的餐具，更多时候是一种象征性的组合。它通常包括：
    *   一个装饰精美的盘子或托盘。
    *   盘子上堆满了各种食物，如面包、水果、糖果、坚果，有时甚至会有煮熟的鸡蛋或肉类。
    *   在某些地区，盘中
- **Bíráló indoklása:** A modell helytelenül az esküvőhöz köti a komatál szokást, míg a várt válasz szerint a szülés utáni időszakban (szülésznő/koma látogatása) adják.

### HU02 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik naphoz kötődik a villőzés szokása?
- **Várt:** virágvasárnap   *(forrás: huwiki, Villőzés)*
- **Kapott:** A villőzés (vagy villózási szokás) hagyományosan a **karácsonyhoz** kötődik, pontosabban a **karácsony második napjához**, amely a **jézusi nap** (más néven a „második karácsony") vagy a **szenteste** (második adventi vasárnap utáni vasárnap) környékére esik.

Ez a szokás Magyarországon és a környező országokban (főleg a Kárpát-medencében) terjedt el, és a következőképpen működik:
*   **Időpont:** Általában december 26-án, a karácsonyi ebéd után, vagy a második adventi vasárnapon.
*   **Módszer:** A résztvevők (gyerekek, de felnőtt is lehet) egy nagy, gyakran dísz
- **Bíráló indoklása:** A modell tévesen állítja, hogy a villőzés a karácsonyhoz kötődik, miközben a helyes válasz a virágvasárnap.

### HU02 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** On which day is the Hungarian custom of 'villőzés' performed?
- **Várt:** Palm Sunday   *(forrás: huwiki, Villőzés)*
- **Kapott:** The Hungarian custom of **villőzés** (literally "twirling" or "whirling") is performed on **Easter Sunday** (*Húsvétvasárnap*).

This tradition is a playful and symbolic ritual where young men, often accompanied by friends, visit the homes of young women. Upon arrival, the men would twirl the women around by their hands or arms in a circle. This act was believed to have several meanings:
*   **Fertility and Health**: It was thought to ensure the woman's fertility and good health for the coming year.
*   **Protection**: The spinning motion was believed to ward off evil spirits.
*   **Social Bonding**: It served as a lighthearted way for young people to interact and court each other during the…
- **Bíráló indoklása:** A modell tévesen állítja, hogy a villözést Húsvétvasárnap végzik, míg a helyes válasz a virágvasárnap (Palm Sunday).

### HU02 / kínai — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** 匈牙利的“villőzés”习俗在哪一天进行？
- **Várt:** 棕枝主日（复活节前的星期日）   *(forrás: huwiki, Villőzés)*
- **Kapott:** 匈牙利的"villőzés"（意为“剪发”或“剃发”）习俗是在**圣周**（Húsvétvasárnap，即复活节前的星期日，也称为复活节主日）进行的。

在这个特殊的日子里，匈牙利人（尤其是儿童和青少年）会互相用剪刀剪对方的头发，或者用剃刀剃去对方的头发。这一传统主要流行于匈牙利北部和西部的一些地区。其起源众说纷纭，一种流行的说法是这象征着摆脱过去的烦恼、疾病或厄运，通过剪去旧发来祈求新的一年健康、好运和财富。此外，也有观点认为这与古代祈求生育或庆祝春天到来的仪式有关。

值得注意的是，虽然这是一个传统习俗，但在现代匈牙利，它更多被视为一种带有幽默色彩的地方性传统，并非全国上下普遍严格遵守的宗教仪式，且通常只发生在特定的家庭或社区圈子内。

**结论：**
该习俗在**复活节主日**
- **Bíráló indoklása:** A válasz helyesen azonosítja a szertartást a húsvéti időszakra (pontosabban a virágvasárnapra/strawberry Sunday kontextusában, bár a modell a 'Húsvétvasárnap' kifejezést használta, ami a várt 'palm sunday' vagy '复活节前的星期日' fogalmával egyezik a kontextusban, és a lényegi információt, hogy húsvéti szer

### HU03 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Mit kellett tennie Mátyás királynak álruhában a kolozsvári bíró utasítására?
- **Várt:** fát hordani   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** Ez a kérdés egy gyakori téveszmén vagy félreértésen alapul, mivel **Mátyás király (Mátyás Corvin) sosem volt álruhában Kolozsváron, és nem is volt kolozsvári bíró utasítása, amely ilyen cselekményt parancsolna neki.**

A történelmi tények és a népi mondások alapján a helyzet a következő:

1.  **Történelmi valóság:** Mátyás király (1443–1490) valóban többször is látogatott Erdélybe, és Kolozsvárt (Klausenburg) is meglátogatta, de ezek hivatalos királyi látogatások voltak, nem pedig álruhában végrehajtott titkos akciók. A korabeli források nem tartalmaznak olyan eseményt, ahol a király
- **Bíráló indoklása:** A modell tagadja a kérdésben szereplő történelmi eseményt, míg a várt válasz szerint Mátyás királynak fát kellett hordania, így a modell nem adta meg a keresett információt.

### HU03 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** In the Hungarian folk tale, what did the disguised King Matthias have to do on the orders of the judge of Kolozsvár?
- **Várt:** carry firewood   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** In the Hungarian folk tale (often titled *A király és a kőszobor* or *Matthias Corvinus and the Stone Statue*), the disguised King Matthias Corvinus was sentenced by the judge of Kolozsvár (Cluj-Napoca) to a humiliating and physically demanding task.

After the king, disguised as a commoner, was caught stealing a chicken (or in some versions, simply being accused of a crime), the judge ordered him to **carry a heavy stone statue** (sometimes described as a large stone block or a statue of a saint) from the church square to the castle or a specific location. The task was intended to be impossible for an ordinary person due to the immense weight of the object.

However, because the king posses…
- **Bíráló indoklása:** A modell válasza szerint a királynak egy kőszobrot kellett hordania, míg a várt válasz szerint tűzifát kellett szállítania, így a válasz tényileg eltér a helyes megoldástól.

### HU03 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 在匈牙利民间故事中，乔装的马加什国王奉克卢日法官之命做了什么？
- **Várt:** 搬木柴   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** 在匈牙利民间故事（特别是关于马加什国王马加什一世或类似传说的变体）中，乔装的马加什国王奉克卢日（Klausenburg，今克卢日 - 纳波卡）法官之命，通常被要求**在法庭上为一名无辜者辩护**，或者更具体地说，是**在法官面前接受审判并揭露真相**。

在这个经典的故事片段中，马加什国王为了体验民间疾苦或测试司法公正，乔装成一名普通的农民、乞丐或罪犯来到克卢日。当地的法官（有时被描绘为贪婪、腐败或傲慢）在不知情的情况下对他进行了审讯。法官命令这位“平民”完成一项看似不可能或极其卑微的任务，例如：
*   **在法庭上大声朗读法律条文**（以此测试其是否真的懂法，或者嘲笑其无知）；
*   **为法官自己辩护**（陷入逻辑悖论）
- **Bíráló indoklása:** A várt válasz ('搬木柴' / faaprítás) hiányzik a modell válaszából, amely helyette teljesen más, a kérdésben szereplő konkrét cselekvéstől eltérő eseményeket ír le.

### HU04 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Meddig tartott a pünkösdi király uralma a magyar népszokás szerint?
- **Várt:** a következő pünkösdig (egy évig)   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** A magyar népszokás és a népi hitvilág szerint a pünkösdi király (más néven pünkösdi királyfi, pünkösd király) uralma **pünkösd vasárnap reggelétől** kezdődik, és **szentpéter-napig (június 29.)** tart.

Ez a időszak a nyár kezdetét és a termékenység idejét jelképezi. A népi hiedelem szerint ebben az időben a természet „királya" uralkodik, aki védi a növényeket és az állatokat, de egyben a viharok és a zord időjárás okozója is lehet, ha nem tiszteletet tanúsítanak felé. A hagyományok szerint a királyt pünkösd vasárnapon a templomban vagy a templom előtt koszorúzzák
- **Bíráló indoklása:** A válasz tévesen állítja, hogy a pünkösdi király uralma szentpéter-napig (június 29.) tart, míg a helyes válasz szerint a következő pünkösdig (egy évig) tart.

### HU04 / angol — bíráló: **helytelen**

- **Kérdés:** According to Hungarian folk custom, how long did the reign of the 'Whitsun king' last?
- **Várt:** until the next Whitsun (one year)   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** According to Hungarian folk custom, the reign of the **Whitsun king** (known as *Pünkösd király* or *Pünkösd királykám*) lasted for exactly **one day and one night**.

This tradition was rooted in the belief that the king was a supernatural figure, often a spirit or a demon, who would appear on the morning of Pentecost (Whitsunday). His rule was strictly limited to that single day and night; if he were not driven away or killed by the end of the night, it was believed he would bring misfortune, such as a harsh winter or famine, to the community. Consequently, the custom involved a ritual where the king was crowned in the morning and then ritually executed (often by being thrown into a well, …
- **Bíráló indoklása:** A modell válasza szerint a királyság egy napig és éjszakáig tartott, míg a várt válasz szerint egy évig (a következő pünkösdig), így a modell téves információt közöl.

### HU04 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 按匈牙利民俗，“五旬节国王”的任期持续多久？
- **Várt:** 到下一个五旬节（一年）   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** 在匈牙利民俗传统中，“五旬节国王”（Pénteki király，又称“五月国王”）的任期非常短暂，通常**只持续一天**。

这一习俗主要流行于匈牙利及中欧部分地区，时间定在复活节后第 50 天，即**五旬节**（Pentecost）当天。在这一天，村民们会选出一位“国王”（有时也会选出一位“王后”），并为他/她加冕。这位“国王”会佩戴花环，手持权杖，带领人群游行，并负责分发鲜花或糖果。

然而，他的统治仅限于五旬节这一天。到了**次日**（五旬节后的第一个工作日），这位“国王”必须立即退位，将权杖和花环交给下一任的“国王”，或者将其埋入土中/投入水中，象征着权力的终结和新一年的开始。因此，这位民俗人物的任期严格限定为**24
- **Bíráló indoklása:** A modell válasza szerint a királyi tisztség csak egy napig tart, míg a várt válasz szerint a következő pünkösdig, azaz egy évig.

### HU05 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik volt a SZÉP-kártya harmadik alszámlája a szálláshely és vendéglátás mellett (a korábbi három alszámlás rendszerben)?
- **Várt:** szabadidő   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** A korábbi, három alszámlás rendszerben (amelyet 2017. január 1-jétől vezettek be, és amelyet 2024. december 31-ig lehetett használni) a SZÉP-kártya az alábbi területekre oszlott:

1.  **Szálláshely és vendéglátás** (ez volt az alapvető, leggyakrabban használt számla).
2.  **Személyi kölcsön** (ezt a számlát a munkáltatók és a dolgozók számára nyitották meg, hogy a SZÉP-kártyával történő vásárlás után a maradék összeget személyi kölcsönként vissza lehessen utalni a dolgozónak, ha a kártya nem volt teljesen kihasználva, vagy speciális
- **Bíráló indoklása:** A modell válasza teljesen téves információt tartalmaz: a SZÉP-kártya alszámlái nem személyi kölcsönök voltak, hanem étkezés, szállás és szabadidő, így a várt 'szabadidő' helyett hibás tartalmat ad meg.

### HU05 / angol — bíráló: **helyes**

- **Kérdés:** In the earlier three-sub-account system of the Hungarian SZÉP card, what was the third sub-account besides accommodation and catering?
- **Várt:** leisure   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** In the earlier three-sub-account system of the Hungarian SZÉP card (before it was simplified to a two-account system in 2019), the funds were divided into three distinct categories to regulate spending.

The first two accounts were indeed for **accommodation** (hotels, guesthouses, etc.) and **catering** (restaurants, cafés, and food services). The third sub-account was designated for **cultural and leisure activities**.

This third account allowed cardholders to spend their allocated funds on:
*   Museum and gallery tickets
*   Theater, opera, and concert tickets
*   Sports events
*   Zoo and aquarium entries
*   Other approved cultural and recreational services

**Answer:** The third sub-a…
- **Bíráló indoklása:** A modell helyesen azonosította a harmadik számlát szabadidős/kulturális tevékenységekként, ami megfelel a várt "leisure" válasznak.

### HU05 / kínai — bíráló: **helyes**

- **Kérdés:** 匈牙利SZÉP卡早期的三个子账户中，除住宿和餐饮外，第三个是什么？
- **Várt:** 休闲   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** 匈牙利 SZÉP 卡（Szépkártya）在早期（2012 年推出时）的设计中，确实将资金分为了三个独立的子账户，旨在规范旅游和休闲消费。这三个子账户分别是：

1.  **住宿**（Lakás）：用于支付酒店、民宿等住宿费用。
2.  **餐饮**（Étel-ital）：用于支付餐厅、咖啡馆等餐饮消费。
3.  **休闲/娱乐**（Szabadidő）：这是第三个子账户，专门用于支付文化娱乐活动，如剧院门票、博物馆入场费、体育场馆消费等。

因此，除住宿和餐饮外，第三个子账户是**休闲**（或称娱乐/文化）。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (a harmadik al számla a 'szabadidő' vagy '休闲'), bár a magyar szövegben szereplő 'Lakás' (lakás) elírásnak tűnik az 'Szállás' (szállás) helyett, a lényegi válasz helyes.

### HU06 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik megye jellegzetes étele a dödölle?
- **Várt:** Zala   *(forrás: huwiki, Dödölle)*
- **Kapott:** A **dödölle** (vagy dödölle) a **Szabolcs-Szatmár-Bereg vármegye** jellegzetes étele, amely a magyar konyha egyik legismertebb és legkülönlegesebb képviselője.

Bár a tészta eredetét gyakran a szomszédos Szatmár vármegyével (ahol a *dödölle* szó is használatos) vagy a környező régiókkal (pl. Erdély) is összefüggésbe hozzák, a mai Magyarország területén a **Szabolcs-Szatmár-Bereg vármegye** (korábban Szabolcs vármegye) központjában, különösen a **Nyíregyháza** és környéke, vált a dödölle hagyományos otthonává. A helyi változatot gyakran „nyí
- **Bíráló indoklása:** A modell helytelenül az észak-keleti Szabolcs-Szatmár-Bereg vármegyét jelöli meg, míg a dödölle a Zalai régió jellegzetes étele.

### HU06 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Which Hungarian county is the dish 'dödölle' typical of?
- **Várt:** Zala   *(forrás: huwiki, Dödölle)*
- **Kapott:** The dish **dödölle** is most typically associated with **Borsod-Abaúj-Zemplén county** in northeastern Hungary.

While it is a traditional dish found in several counties in the northern part of the country (including Heves, Nógrád, and Szabolcs-Szatmár-Bereg), its origins and strongest cultural presence are in the region around **Miskolc**, the capital of Borsod-Abaúj-Zemplén. The name itself is believed to be a corruption of the German word *Dudeln* (to blow or whistle), referring to the way the dough is rolled or perhaps the sound of the wind in the hills, though local folklore often links it to the shape of the dough resembling a sleeping figure or a specific local legend.

The dish consi…
- **Bíráló indoklása:** A modell tévesen állítja, hogy a dödölle a Borsod-Abaúj-Zemplén megyéhez kötődik, miközben a helyes válasz a Zala megye.

### HU06 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利菜“dödölle”是哪个州的特色菜？
- **Várt:** 佐洛州   *(forrás: huwiki, Dödölle)*
- **Kapott:** 匈牙利菜中的 **Dödölle**（有时也拼作 Dödlle）并不是某个特定“州”（匈牙利行政区划为县，megye）的独家特色菜，而是**匈牙利全境**都非常流行的一道传统菜肴。

这道菜的主要特点是使用一种名为 *dudás* 的长条状面团，将其煮至半熟后，再裹上肉馅（通常是猪肉或牛肉混合洋葱、香料等），最后放入浓稠的酱汁中炖煮。虽然它在匈牙利各地都能吃到，但在**大平原地区**（如佩斯州 Pest、杰尔 - 莫雄 - 肖普朗州 Győr-Moson-Sopron 等）尤为常见，常作为节日或家庭聚餐的主菜。

值得注意的是，Dödölle 在匈牙利语中是“尸体”的复数形式，这个名字源于其外观：煮熟的面团条被肉馅包裹后，形状酷似一具
- **Bíráló indoklása:** A modell tévesen állítja, hogy a dödölle nem egy adott régió specialitása, és helytelenül azonosítja a főzési módszert (nem tésztából készül, hanem krumpliból), így nem adja meg a várt választ (Zala megye).

### HU07 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen tésztából készül a kőttes?
- **Várt:** kelt tészta   *(forrás: huwiki, Kőttes)*
- **Kapott:** A **kőttes** (vagy kőteszt) alapvetően egy egyszerű, de jellegzetes tésztából készül, amelynek a legfontosabb összetevői a **liszt**, a **víz** és a **só**.

A hagyományos recept szerint a tészta nagyon **puha és ragacsos** állagú, mivel a lisztbe kevesebb vizet adnak, mint például a telt tésztákhoz (mint a csusza vagy a nokedli), de többet, mint a szárazabb tésztákhoz. Ez a specifikus állag teszi lehetővé, hogy a tésztát egy lapos kőre (vagy ma már gyakran egy speciális, lapos tepsire) tegyék, és a forró felületen gyorsan, egyenletesen megpiruljon, miközben belül marad puha.

G
- **Bíráló indoklása:** A modell tévesen állítja, hogy a kőttes lisztből, vízből és sóból készül, és nem említi meg a várt választ, a kelt tésztát, amely a kőttes alapanyaga.

### HU07 / angol — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** What kind of dough is the Hungarian pastry 'kőttes' made from?
- **Várt:** leavened (yeast) dough   *(forrás: huwiki, Kőttes)*
- **Kapott:** There appears to be a slight misunderstanding in the name of the pastry you are asking about. The traditional Hungarian pastry is called **köttés** (often spelled with a double 't' or sometimes confused with *kötött*), not "kőttes."

**Köttés** is a type of sweet, rolled pastry that is very similar to a strudel or a rolled dough dessert. It is made from a **thin, elastic yeast dough**.

The dough preparation typically involves:
*   **Flour**: Usually high-protein bread flour to ensure elasticity.
*   **Yeast**: Active dry yeast or fresh yeast to make the dough rise.
*   **Liquid**: Warm milk or water.
*   **Fat**: Butter or sometimes oil, which is crucial for the flaky yet soft texture.
*   …
- **Bíráló indoklása:** A modell helyesen azonosítja, hogy a 'kőttes' valószínűleg a 'köttésre' utal, és megállapítja, hogy élesztős tésztából készül, ami megegyezik a várt 'leavened (yeast) dough' válaszal.

### HU07 / kínai — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** 匈牙利点心“kőttes”用什么面团制作？
- **Várt:** 发酵面团   *(forrás: huwiki, Kőttes)*
- **Kapott:** 这里存在一个误解：**匈牙利并没有一种名为"kőttes"的传统点心**。

这个名字极有可能是对匈牙利著名甜点"**Kürtőskalács**"（中文常译为：烟囱蛋糕、匈牙利甜卷、或烤甜圈）的误记或拼写错误。"Kürtőskalács"在匈牙利语中发音接近"Kurtosh-kalacs"，而"kőttes"可能是听音偏差或输入错误。

如果您指的是**Kürtőskalács**，它的制作面团如下：

### Kürtőskalács（烟囱蛋糕）的面团成分
这种甜点的面团属于**酵母发酵面团**，其特点是可以拉伸成细长的管状，并在特制的烤架上旋转烘烤。主要成分包括：

*   **高筋面粉**：提供支撑力，使面团能拉得很长而不易断裂。
*   **酵母**：用于发酵，使面团蓬松。
*   **糖**：
- **Bíráló indoklása:** A modell helyesen azonosítja, hogy a 'kőttes' valószínűleg a 'Kürtőskalács' elírása, és megadja a helyes választ (élesztős/tésztatípus), bár a válasz elvágódott.

### HU08 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik időszakban járnak a regösök?
- **Várt:** karácsony és újév között   *(forrás: huwiki, Regölés)*
- **Kapott:** A regösök (vagy regősök) hagyományosan **nyáron**, a **naplementétől a hajnalig** járnak.

Ez az időpont a legfontosabb, mivel a regészet eredetileg egyfajta „éjszakai" vagy késő esti műfaj volt, amely a nappali munka befejezése után kezdődött. A hagyomány szerint a regösök akkor indultak el, amikor a nap már lement, és a falvakban a lakosság már lefekvés előtt vagy éppen lefekvéskor volt. Az éjszakai járásnak több oka is volt:
*   **Nyugalom:** A nappali zajos munka után a falvakban csendesebb volt az éjszaka, így a dalok jobban hallatszottak, és kevesebb zavaró tényező volt.
*
- **Bíráló indoklása:** A modell válasza tévesen állítja, hogy a regösök nyáron járnak, miközben a helyes válasz szerint ez a karácsony és újév közötti időszakhoz kötődik.

### HU08 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** During which period of the year do the Hungarian 'regös' singers go from house to house?
- **Várt:** between Christmas and New Year   *(forrás: huwiki, Regölés)*
- **Kapott:** The Hungarian **regös** (or *regő*) singers traditionally go from house to house during the **Christmas season**, specifically from **late November through December**.

This custom is deeply rooted in the folklore of the Carpathian Basin. During this period, these wandering minstrels would travel to villages and towns, singing epic poems, ballads, and folk songs in exchange for food, drink, and sometimes money. Their performances were not merely entertainment but served a social and spiritual function, believed to bring good luck, ward off evil spirits, and ensure a prosperous year for the household.

The timing is significant because it coincides with the pre-Christmas festivities and the p…
- **Bíráló indoklása:** A modell válasza tévesen állítja, hogy a regös éneklés november végétől decemberig tart, míg a várt válasz szerint ez a karácsony és az újév közötti időszakra esik; a megadott dátumok (november 11. - december) nem egyeznek a hagyományos karácsonyi/újévi szokással.

### HU08 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利的“regös”歌手在一年中的什么时期挨家挨户演唱？
- **Várt:** 圣诞节到新年之间   *(forrás: huwiki, Regölés)*
- **Kapott:** 匈牙利的"regös"（复数形式为 regősök）是传统的流浪歌手和说唱艺人，他们通常在**冬季**，特别是从**11 月或 12 月开始，一直持续到次年 3 月或 4 月**，挨家挨户地演唱。

这一传统与匈牙利农村的农业周期紧密相关。在冬季，农闲时节，农民们会聚集在村庄里，而 regös 歌手则利用这段时间穿梭于各个农户之间。他们一边演唱关于历史、传说、爱情或社会讽刺的长篇叙事歌谣（regedő），一边向听众收取报酬（通常是食物、饮料或金钱）。这种活动不仅是娱乐，也是当时乡村社区重要的文化交流和信息传播方式。随着现代娱乐方式的兴起和农村人口结构的变化，这一传统在 20 世纪逐渐衰落，但如今作为文化遗产仍在某些地区得到复兴和表演。

因此，regös 歌手挨家
- **Bíráló indoklása:** A várt válasz a karácsony és az újév közötti időszakra vonatkozik, míg a modell válasza tévesen 11-től 4-ig terjedő időszakot említ, ami nem fedi a regös hagyomány pontos időpontját.

### HU09 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik Fejér megyei faluban élő farsangi szokás a tikverőzés?
- **Várt:** Moha   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** A **tikverőzés** (más néven tikverőzés) a Fejér vármegyei **Sárvíz** faluban élő, rendkívül ősi és egyedi farsangi szokás.

Ez a hagyomány a 17. századból származik, és a helyi néprajzi kutatások szerint eredetileg a szegényebb rétegek által végzett, a gazdagabbak házait „megszegítő" vagy szimbolikus módon „megrontó" játék volt, amely a tél végét és a tavasz eljövetelét ünnepelte. A szokás lényege, hogy a farsang idején a falu fiataljai (korábban a szegényebb fiúk) egy speciális, gyakran faágakból és szalmából készített, de ma már inkább díszes, színes ruhába ö
- **Bíráló indoklása:** A modell helytelenül azonosítja a helyszínt (Sárvíz), míg a várt és helyes válasz Moha.

### HU09 / angol — bíráló: **helytelen**

- **Kérdés:** In which village of Fejér county does the carnival custom 'tikverőzés' survive?
- **Várt:** Moha   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** The carnival custom of **tikverőzés** (which literally translates to "tickling with a feather" or "tickling with a quill") survives in the village of **Szentlőrinc** in Fejér county, Hungary.

This unique tradition is part of the local "Húsvéti" (Easter) festivities, though it has strong roots in the pre-Lenten carnival period. During the custom, participants, often dressed in traditional folk costumes, use long feathers (historically from geese or ducks) to gently tickle the faces and bodies of other villagers. The goal is to induce laughter and good spirits, symbolizing the driving away of winter's gloom and the welcoming of spring. It is considered one of the most distinctive and well-pre…
- **Bíráló indoklása:** A modell helytelenül azonosítja a települést (Szentlőrincet), amely valójában Baranya vármegyében található, míg a tikverőzés hagyománya Fejér vármegye Moha községéhez kötődik.

### HU09 / kínai — bíráló: **helytelen**

- **Kérdés:** 狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
- **Várt:** 莫哈（Moha）   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** 狂欢节习俗"tikverőzés"（意为“涂油”或“抹猪油”）主要保存在匈牙利**费耶尔州**（Fejér）的**巴奇 - 基什孔**（Bácsi）地区，具体所在的村庄是**巴奇**（Bács）。

在这个传统中，狂欢节期间，人们会用猪油涂抹在邻居、朋友甚至陌生人的脸上和身上，以此作为祝福和驱邪的方式。这一独特的民俗活动是当地文化遗产的重要组成部分，旨在保留古老的社区互动形式。

需要注意的是，虽然有时人们会将其与邻近的**巴奇 - 基什孔**（Bács-Kiskun）州的某些习俗混淆，但"tikverőzés"这一特定名称和形式最核心的保存地确实是费耶尔州的**巴奇**（Bács）村。
- **Bíráló indoklása:** A modell helytelenül azonosítja a települést (Bács helyett Moha), és tévesen állítja, hogy Bács a Fehér megyében található, miközben Bács a Bács-Kiskun megyében van, a helyes válasz pedig Moha.

### HU10 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik ünnephez kötődik a zöldágjárás?
- **Várt:** húsvét (virágvasárnap / fehérvasárnap)   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** A **zöldágjárás** (más néven zöldágon járás) a **Karácsonyhoz** kötődő hagyomány.

Ez a szokás Magyarországon és a környező országokban is elterjedt, különösen a falusi környezetben. A lényege, hogy a karácsony estéjén vagy éjszakáján a gyerekek (és néha a felnőttek is) zöld ágakat – gyakran fenyőágakat, de lehetnek tölgy- vagy szilvafák ágai is – hoznak magukkal, és csendben, suttogva járnak a házak között.

A célja az volt, hogy a háziak észrevegyék őket, és így **karácsonyi ajándékokat** kapjanak. Ha a háziak észrevették a zöldágjárókat, aj
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás a karácsonyhoz kötődik, miközben a helyes válasz a húsvét (virágvasárnap).

### HU10 / angol — bíráló: **helytelen**

- **Kérdés:** With which holiday is the Hungarian custom 'zöldágjárás' associated?
- **Várt:** Easter (Palm Sunday / Low Sunday)   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** The Hungarian custom known as **zöldágjárás** (literally "green branch walking") is associated with **Christmas**, specifically the period leading up to and including **Christmas Eve (December 24th)**.

During this time, young people, particularly girls, would go out into the woods or forests to collect green branches, twigs, and evergreen foliage. These green elements were believed to possess protective powers against evil spirits and bad luck for the coming year. Upon returning home, the collected branches were often hung on the doors, windows, or placed in the hearth to ensure the household's safety and prosperity. The practice is deeply rooted in pre-Christian winter solstice traditions …
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás a Karácsonyhoz kapcsolódik, miközben ez a hagyomány a Húsvéti locsolással és a virágvasárnappal (pálmavasárnap) hozható összefüggésbe.

### HU10 / kínai — bíráló: **helyes**

- **Kérdés:** 匈牙利的“zöldágjárás”习俗与哪个节日有关？
- **Várt:** 复活节   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** 匈牙利的"zöldágjárás"（意为“绿枝游行”或“戴绿枝”）习俗主要与**复活节**（Húsvét）有关。

在这个传统中，人们会在复活节期间佩戴用新鲜树枝、树叶或花朵编织的花环、头饰或手持绿枝。这一习俗象征着春天的到来、生命的复苏以及自然的更新。在匈牙利民间传说中，佩戴这些绿色植物被认为能够带来好运、保护免受邪恶力量侵害，并祈求来年的丰收与健康。虽然不同地区的具体形式可能略有差异（例如在特兰西瓦尼亚地区或特定的村庄庆典中），但其核心始终围绕着复活节这一庆祝春天和重生的节日。

**结论**：该习俗与**复活节**有关。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a zöldágjárás a húsvéthoz kapcsolódik.

### HU11 / magyar — bíráló: **helyes**

- **Kérdés:** Milyen állat Mirr-Murr, Csukás István meséjének hőse?
- **Várt:** kandúr (macska)   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** Mirr-Murr **macska**.

Csukás István híres meséjében, amely a *Tündérmesék* gyűjtemény része, Mirr-Murr egy különleges, varázslatos macska, aki képes beszélni és emberi tulajdonságokkal rendelkezik. A történetben gyakran segít a főhősnek, a kisfiúnak, és közösen oldják meg a különböző kalandokat.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Mirr-Murr macska (kandúr).

### HU11 / angol — bíráló: **helytelen**

- **Kérdés:** What kind of animal is Mirr-Murr, the hero of István Csukás's tale?
- **Várt:** tomcat   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** Mirr-Murr is a **magpie** (specifically a European magpie, *Pica pica*).

In István Csukás's famous children's book series *The Adventures of Mirr-Murr* (originally titled *A madárka* or "The Little Bird"), the protagonist is a small, clever, and mischievous magpie who lives in a forest. The story follows his various escapades, often involving his interactions with other forest animals and his attempts to solve problems or outwit challenges. The character has become an iconic figure in Hungarian children's literature, known for his wit and the moral lessons embedded in his adventures.
- **Bíráló indoklása:** A modell tévesen állítja, hogy Mirr-Murr egy holló (magpie), miközben István Csukás meséjének főszereplője egy macska (tomcat).

### HU11 / kínai — bíráló: **helyes**

- **Kérdés:** 楚卡什·伊什特万童话的主角Mirr-Murr是什么动物？
- **Várt:** 公猫   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** 在楚卡什·伊什特万（Csukás István）创作的著名童话《米尔 - 穆尔》（*Mirr-Murr*）中，主角**米尔 - 穆尔**（Mirr-Murr）是一只**猫**。

更具体地说，它是一只**黑猫**。故事讲述了这只聪明、勇敢且富有同情心的黑猫，如何帮助一位名叫米拉（Mira）的公主，并带领她穿越各种奇幻的森林和国度，最终战胜邪恶巫婆的故事。米尔 - 穆尔不仅是公主的忠实伙伴，也是整个冒险旅程中的核心引导者。
- **Bíráló indoklása:** A modell helyesen azonosította a főszereplőt macskaként, ami megfelel a várt válasznak (公猫), bár a történet részletei (pl. Mira hercegnő) valószínűleg hallucináltak, a kérdés konkrét válaszát helyesen adta meg.

### HU12 / magyar — bíráló: **helytelen**

- **Kérdés:** Ki írta A nagy ho-ho-ho-horgász meséit?
- **Várt:** Csukás István   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** A **Nagy ho-ho-ho-horgász** című meséjének szerzője **Kovács István** (1930–2014), aki magyar író, költő és műfordító volt.

Ez a történet a legismertebb alkotása, amelyben a főhős, a nagy ho-ho-ho-horgász egy különleges horgászbotot használ, amellyel nem halakat, hanem emberi érzelmeket és gondolatokat fog. A mese 1978-ban jelent meg először, és azóta több kiadást is megért, gyakran iskolai olvasókönyvekben is szerepel. A történet mesélő stílusa és a benne rejlő bölcsességek miatt vált klasszikussá a magyar gyermekirodalomban.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a mű szerzője Kovács István, miközben a helyes válasz Csukás István.

### HU12 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Who wrote the Hungarian children's tales 'A nagy ho-ho-ho-horgász'?
- **Várt:** István Csukás   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** The Hungarian children's tale **"A nagy ho-ho-ho-horgász"** (The Great Ho-Ho-Ho-Ho Fisherman) was written by **Miklós Radnóti**.

However, it is important to clarify the context of this work. Miklós Radnóti (1909–1944) was a renowned Hungarian poet, but he is not typically known for writing traditional folk tales or children's stories in the classic sense. "A nagy ho-ho-ho-horgász" is actually a **poem** written by Radnóti in 1939. The title is a playful, onomatopoeic reference to the sound of a fisherman's call or the act of fishing, reflecting Radnóti's unique style which often blended surrealism, humor, and deep melancholy.

While the poem is sometimes included in collections of Hungarian…
- **Bíráló indoklása:** A modell tévesen állítja, hogy Miklós Radnóti írta a művet, miközben a szerző István Csukás.

### HU12 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利儿童故事《A nagy ho-ho-ho-horgász》的作者是谁？
- **Várt:** 楚卡什·伊什特万（Csukás István）   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** 《A nagy ho-ho-ho-horgász》（中文常译为《大吼吼吼钓》或《大“吼吼吼”钓鱼》）的作者是匈牙利著名的儿童文学作家、插画家 **伊万·埃斯泰尔哈齐**（**István Eszterházy**，1924–2006）。

这部作品是埃斯泰尔哈齐最著名且深受孩子们喜爱的故事之一。故事讲述了一个名叫“霍霍霍”（Ho-ho-ho）的小男孩，他并不喜欢安静地钓鱼，而是喜欢大声喊叫“霍霍霍”来吸引鱼儿上钩。故事充满了幽默感和童趣，生动地描绘了孩子天真烂漫的想象力。埃斯泰尔哈齐不仅文笔生动，其亲自绘制的插图也极具特色，为故事增添了独特的艺术魅力。

**作者：伊万·埃斯泰尔哈齐 (István Eszter
- **Bíráló indoklása:** A modell tévesen István Eszterházyt nevezte meg szerzőnek, miközben a helyes válasz Csukás István.

### HU13 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen fajtájú kutya Bogáncs Fekete István regényében?
- **Várt:** puli   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** Fekete István *Bogáncs* című regényében a főszereplő, a kisfiú, akit a szülők Bogáncsnak neveznek, egy **szürke, rövidszőrű kutyus**.

A könyvben a kutya nem faji hovatartozása (pl. husky, collie stb.) alapján kerül bemutatásra, hanem inkább mintegy „kerti kutya" vagy házi kedvencként, aki a család tagja. A leírások szerint ő egy csendes, szerény, de nagyon hűséges és okos állat, aki központi szerepet tölt be a történetben, különösen a kisfiú és a nagyapja közötti kapcsolatot erősítve. A regény hangulata és a vidéki környezet miatt a kutya megjelenése is egyszerű, földhözragadt,
- **Bíráló indoklása:** A modell tévesen állítja, hogy a főszereplő kutya, miközben Bogáncs a regény főhőse, egy kisfiú, akit a szülei neveznek így, a kutya pedig egy puli.

### HU13 / angol — bíráló: **helytelen**

- **Kérdés:** What breed of dog is Bogáncs in István Fekete's novel?
- **Várt:** Puli   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** In István Fekete's 1974 novel *Bogáncs* (English title: *The Dog Bogáncs*), the titular character is a **German Shepherd** (specifically a *Német juhász* in Hungarian).

The story follows the life of this dog, who is born in a kennel in Budapest and later becomes a famous police dog known for his exceptional tracking abilities and loyalty. The novel is widely considered a classic of Hungarian children's literature and is often adapted into films and stage plays.

**Answer:** The breed is a **German Shepherd**.
- **Bíráló indoklása:** A modell tévesen állítja, hogy Bogáncs német juhász, míg a várt válasz és a valóság szerint a kutya puli.

### HU13 / kínai — bíráló: **helytelen**

- **Kérdés:** 费凯特·伊什特万小说中的狗Bogáncs是什么品种？
- **Várt:** 普利犬（Puli）   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** 在费凯特·伊什特万（Fekete István）的经典匈牙利儿童文学作品《**博甘茨**》（*Bogáncs*，又译《小狗博甘茨》或《忠犬博甘茨》）中，主角博甘茨（Bogáncs）是一只**匈牙利牧羊犬**（Magyar Pásztó）。

这只狗是小说作者费凯特·伊什特万自己饲养的爱犬，书中的故事很大程度上基于他与博甘茨的真实生活经历。匈牙利牧羊犬以其极高的智商、对主人的绝对忠诚以及出色的放牧能力而闻名，这些特质在小说中得到了充分的体现，使博甘茨成为了匈牙利文学史上最著名的动物形象之一，甚至成为了该国忠诚与友谊的象征。

**结论**：博甘茨的品种是**匈牙利牧羊犬**。
- **Bíráló indoklása:** A várt válasz szerint a kutya fajtája a puli, míg a modell válasza helytelenül magyar pásztorkutyának (vagy általánosan magyar juhászkutyának) nevezi, ami nem egyezik a tényekkel.

### HU14 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Ki írta a Tündér Lala című meseregényt?
- **Várt:** Szabó Magda   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** A **Tündér Lala** című meseregényt (vagy pontosabban a hozzá kapcsolódó meséket és történeteket) **Kovács László** írta.

Kovács László (1928–2011) magyar író, költő és műfordító, aki számos gyermek- és ifjúsági könyvet alkotott. A „Tündér Lala" történetei gyakran szerepelnek a gyűjteményes műveiben, és a tündérkarakter gyakran a szerző sajátos, mesés világának központi alakja, aki segít a gyerekeknek a jóra, a bátorságra és az együttműködésre. A történetek hangulata általában meleg, mesés és nevelő jellegű, ami Kovács László írói stílusának jellem
- **Bíráló indoklása:** A modell tévesen állítja, hogy Kovács László írta a művet, miközben a helyes szerző Szabó Magda.

### HU14 / angol — bíráló: **helytelen**

- **Kérdés:** Who wrote the Hungarian fairy-tale novel 'Tündér Lala'?
- **Várt:** Magda Szabó   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** The Hungarian fairy-tale novel *Tündér Lala* (The Fairy Lala) was written by **Miklós Radnóti**.

Published in 1941, the work is a collection of poems and short stories that blend magical realism with deep psychological insight. It is considered one of Radnóti's most significant literary achievements, showcasing his unique ability to create a dreamlike atmosphere while addressing complex human emotions and societal themes. Although Radnóti is perhaps best known internationally for his tragic poetry written during World War II (for which he was later executed by the Nazis), *Tündér Lala* remains a cornerstone of modern Hungarian literature.
- **Bíráló indoklása:** A modell tévesen állítja, hogy Miklós Radnóti írta a művet, pedig a szerző Magda Szabó.

### HU14 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利童话小说《Tündér Lala》的作者是谁？
- **Várt:** 萨博·玛格达（Szabó Magda）   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** 匈牙利著名的童话小说《Tündér Lala》（中文常译作《拉拉仙女》或《小仙女拉拉》）的作者是**伊万·埃万杰利斯塔·莫尔纳尔**（**Móricz Zsigmond** 的笔名？不，这里需要纠正，作者是 **Móricz** 吗？不是。让我们重新确认）。

经过核实，这部作品的作者是**伊万·埃万杰利斯塔·莫尔纳尔**（**Móricz Zsigmond**）？不对，莫尔纳尔·佐尔坦（Móricz Zsigmond）是著名的现实主义作家，写过《佩列什》等，但不是童话。

正确的作者是**伊万·埃万杰利斯塔·莫尔纳尔**？不，这个名字在记忆中似乎有些混淆。让我们直接检索核心事实：
《Tündér Lala》是匈牙利儿童文学的经典之作。它的作者是
- **Bíráló indoklása:** A modell nem adta meg a helyes szerzőt (Szabó Magda), hanem tévesen említett más szerzőket (Móricz Zsigmond), és a válasz elvágódott, így a helyes információt nem tartalmazza.

### HU15 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Mit rövidít az OKJ a magyar szakképzésben?
- **Várt:** Országos Képzési Jegyzék   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** Az **OKJ** a magyar szakképzési rendszerben a **Országos Képzési Jegyzéket** jelöli.

Ez a hivatalos, jogszabályi háttérrel rendelkező dokumentum, amely tartalmazza az összes szakképesítés megnevezését, a képzés tartalmát, a tanulási időt, a vizsgakövetelményeket és a szakképesítés elérésének feltételeit. A jegyzékben szereplő szakképesítések minősége és elismerhetősége garantált, mivel az Országos Képzési Jegyzékbe történő felvétel és változtatásáról szóló 2011. évi CLIV. törvény szabályozza.

Röviden: **OKJ = Országos Képzési Jegyzék**.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint az OKJ az Országos Képzési Jegyzék rövidítése.

### HU15 / angol — bíráló: **helyes**

- **Kérdés:** What does the abbreviation OKJ stand for in Hungarian vocational training?
- **Várt:** National Training Register (Országos Képzési Jegyzék)   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** In the context of Hungarian vocational training and the education system, **OKJ** stands for **Országos Képesítési Jegyzék**.

Translated into English, this means the **National Qualifications Register**.

It is a comprehensive, state-maintained database that lists all officially recognized vocational qualifications in Hungary. The register serves as the legal basis for vocational education and training, defining the specific learning outcomes, duration, and requirements for each profession. When a student completes a vocational program, they receive a certificate that references a specific code within the OKJ, ensuring that the qualification is nationally standardized and recognized across …
- **Bíráló indoklása:** A modell helyesen azonosítja az OKJ rövidítést az Országos Képesítési Jegyzékként, amely a magyar szakképzésben használt hivatalos elnevezés, bár a várt válaszban szereplő 'Képzési' helyett a pontosabb 'Képesítési' szót használja.

### HU15 / kínai — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** 匈牙利职业教育中的缩写OKJ代表什么？
- **Várt:** 国家培训目录（Országos Képzési Jegyzék）   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** 在匈牙利职业教育体系中，**OKJ** 是 **Országos Képesítési Jegyzék** 的缩写，中文通常译为"**国家资格名录**"或"**国家职业资格目录**"。

它是匈牙利教育、青年和体育部（Nemzeti Fejlesztési Minisztérium）制定的一份官方文件，旨在规范和管理全国的职业教育与培训体系。该名录详细列出了所有被国家认可的职业资格（szakma），包括：

*   **职业名称**：明确界定具体的工种或专业领域。
*   **资格等级**：对应欧盟的资格框架（EQF），通常分为 5 级（5 级为最高，对应高等教育；4 级为中等职业教育）。
*   **培训时长**：完成该职业所需的标准学习周数。
*   **核心能力要求**：规定从业者必须掌握的具体技能和知识。

**OKJ 的核心作用在于：**
1.
- **Bíráló indoklása:** A modell helyesen azonosítja az OKJ rövidítést az Országos Képesítési Jegyzékkel, amely a várt válasz lényegi tartalmát (a magyar rövidítést és a magyar nevet) tartalmazza, bár a várt magyar név ('Képzési') és a modell által megadott ('Képesítési') közötti finom különbség ellenére a válasz tényileg 


## ZH csoport

### ZH01 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban tisztelik elsősorban Fazhugong (法主公) népi istenséget?
- **Várt:** Fujian   *(forrás: zhwiki, 法主公)*
- **Kapott:** A **Fazhugong** (法主公, „A Mester Uralkodója" vagy „A Törvény Uralkodója") népi istenség elsősorban a **Fujian** tartományban tisztelik, különösen a **Quanzhou** és **Zhangzhou** régiókban.

Bár eredete bizonytalan lehet (néhány hagyomány szerint egy buddhista szerzetes, mások szerint egy taoista mester vagy egy helyi hős), a kultuszja mélyen gyökerezett a Fujian déli részén. Az istent gyakran védőszentként tisztelik a kereskedők, a hajósok és a helyi lakosság számára, aki képes a bűnök elűzésére, a betegségek gyógyítására és a szerencse hozatalára. A tiszteletet gyakran kombinálják a taoista és a népi vall
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fazhugong elsősorban a Fujian tartományban tisztelt istenség.

### ZH01 / angol — bíráló: **helyes**

- **Kérdés:** In which Chinese province is the folk deity Fazhugong (法主公) mainly worshipped?
- **Várt:** Fujian   *(forrás: zhwiki, 法主公)*
- **Kapott:** The folk deity **Fazhugong** (法主公), whose full name is often cited as **Fazhu Gong** or **Fazhu Wang**, is mainly worshipped in the province of **Fujian** (福建).

He is a prominent figure in the local folk religion and Taoist traditions of southern Fujian, particularly in the cities of **Quanzhou**, **Xiamen**, and **Zhangzhou**. Devotees believe he possesses the power to exorcise demons, cure illnesses, and protect against evil spirits. His worship is so deeply rooted in the region that he is often referred to as the "Fujian Protector" (福建境主). While his influence has spread to neighboring areas like Taiwan and parts of Southeast Asia due to historical migration, his origin and primary cult c…
- **Bíráló indoklása:** A modell válasza egyértelműen és helyesen azonosítja a Fujian tartományt, amely a várt válasz.

### ZH01 / kínai — bíráló: **helyes**

- **Kérdés:** 民间神祇法主公主要在中国哪个省份受到崇拜？
- **Várt:** 福建   *(forrás: zhwiki, 法主公)*
- **Kapott:** 法主公（又称法主真君、张圣者）主要在中国**福建省**受到最广泛的崇拜，尤其是**福州**地区。

他是道教闾山派（特别是北派）的重要神祇，被尊为驱邪降妖、治病救人的祖师。在福建民间信仰中，法主公的地位极高，福州几乎家家户户都供奉法主公神位，福州话中甚至将“法主公”简称为“法主”。除了福建本土，随着闽人的迁徙，他的信仰也传播到了台湾、浙江南部以及东南亚的华人社区，但其信仰的发源地和核心区域始终在福建。

**结论：福建省**
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi a várt információt, azaz a Fujian tartományt, és ezt helyesen indokolja is.

### ZH02 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban van Wujiagou (伍家沟村), a népmeséiről ismert falu?
- **Várt:** Hubei   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** A **Wujiagou** (伍家沟) falu, amely a hagyományos kínai népmeséiről és a „Wujiagou-i mesék" (Wujiagou guji) című műről ismert, a **Sichuan** tartományban található.

Konkrétabban a falu a **Liangshan Yi, Qiang és Tibetan Autonóm Prefektúrában** (Liangshan), a **Wenquan** (文川) járásban helyezkedik el. Ez a régió a kínai néprajzi és irodalmi örökség egyik fontos központja, ahol a helyi közösségek évszázadok óta őrzik és továbbadják a szokatlanul gazdag mesehagyományukat, amelyeket gyakran a „Wujiagou-i mesék" néven említenek a kulturális dokumentumokban.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a Wujiagou a Sichuan tartományban található, míg a helyes válasz Hubei.

### ZH02 / angol — bíráló: **helytelen**

- **Kérdés:** In which province is Wujiagou village (伍家沟村), known for its folktales?
- **Várt:** Hubei   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** Wujiagou Village (伍家沟村), renowned for its rich collection of folktales and legends, is located in **Shanxi Province**.

Specifically, the village is situated in **Wuquan County** (五台县), which is part of the Taiyuan City prefecture. This area is famous for its deep-rooted cultural heritage, including numerous traditional stories passed down through generations, often intertwined with the region's history of cave dwellings and mountainous terrain. The folktales of Wujiagou are a significant part of the local intangible cultural heritage in Shanxi.
- **Bíráló indoklása:** A modell helytelenül az Sanghaji (Shanxi) tartományba helyezi a falut, míg a helyes válasz Hubei.

### ZH02 / kínai — bíráló: **helytelen**

- **Kérdés:** 以民间故事闻名的伍家沟村位于哪个省？
- **Várt:** 湖北   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** 以民间故事（特别是关于“伍家沟”传说或相关民俗）闻名的**伍家沟村**，通常指的是位于**山西省**的伍家沟村。

该村隶属于**山西省晋中市平遥县**（也有资料指向其位于平遥县襄垣乡或周边区域，具体行政归属可能随时间微调，但核心地理位置在山西）。伍家沟村因保存完好的明清古建筑群、独特的民俗风情以及流传在当地民间的传说故事而著称，是山西省重要的历史文化村落之一。

因此，该村庄位于**山西省**。
- **Bíráló indoklása:** A várt válasz szerint a helyszín Hubei tartományban található, míg a modell válasza Shanxi tartományt jelöli meg, ami eltér a helyes információtól.

### ZH03 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik három állat feje szerepel a quzhou-i „három fej, egy láb” (三头一掌) ételcsoportban?
- **Várt:** kacsa, nyúl, hal   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** A quzhou-i (Csin-csou) „három fej, egy láb" (三头一掌 – *sān tóu yī zhǎng*) ételcsoport a kínai gasztronómia egyik híres specialitása, amely a helyi vadászatból és hagyományokból ered. A név utal arra, hogy az ételkínálás során három különböző állatfejet és egy állatpárt (a „láb" valójában a marhakaréjra utal) tálalnak.

A három fej, amely a névben szerepel, a következők:
1.  **Szarvasfej** (gyakran vaddisznó vagy szarvas, de a hagyományos értelmezésben gyakran a **vaddisznó** feje a legismertebb összetevőként, bár néha szarvast
- **Bíráló indoklása:** A modell tévesen azonosítja az állatokat (szarvas/vaddisznó helyett kacsa, nyúl, hal kellene legyen), és a várt választ nem tartalmazza.

### ZH03 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Which three animals' heads make up the Quzhou dish group 'three heads, one claw' (三头一掌)?
- **Várt:** duck, rabbit, fish   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** The Quzhou dish group known as **"Three Heads, One Claw" (三头一掌)** is a famous culinary specialty from Quzhou, Zhejiang Province, China. The name literally translates to "Three Heads and One Palm," referring to the specific animal parts used in the four signature dishes that make up this group.

The **"Three Heads"** correspond to the heads of the following three animals:
1.  **Deer** (specifically the head of a young deer, often called *Lao Tou* or similar local varieties).
2.  **Pig** (pig's head).
3.  **Goose** (goose's head).

The **"One Claw"** refers to the **chicken's foot** (specifically the chicken's wing or foot, though traditionally referred to as the "claw" in the context of the d…
- **Bíráló indoklása:** A modell tévesen azonosítja az állatokat (szarvas, sertés, lúd), míg a helyes válasz a kacsa, a nyúl és a hal, így a válasz ténybeli hiba miatt nem helyes.

### ZH03 / kínai — bíráló: **helytelen**

- **Kérdés:** 衢州“三头一掌”中的“三头”是指哪三种动物的头？
- **Várt:** 鸭头、兔头、鱼头   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** 衢州“三头一掌”中的“三头”指的是以下三种动物的头：

1.  **兔头**：通常选用免子头，肉质鲜嫩，口感独特。
2.  **牛头**：多指水牛头，经过特殊卤制后，肉质紧实有嚼劲。
3.  **猪头**：即传统的卤猪头肉，肥瘦相间，风味浓郁。

而“一掌”则是指**鸭掌**，通常也是卤制的，口感软糯或脆爽，与三种头肉搭配，构成了衢州极具代表性的特色小吃组合。
- **Bíráló indoklása:** A modell helytelenül azonosította a '三头' (három fej) összetevőit; a várt válasz szerint ez a kacsafej, nyúlfej és halfej, míg a modell tévesen marha- és sertésfejet említett.

### ZH04 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen lisztből készül a shanxi-i wantuo (碗托)?
- **Várt:** hajdina   *(forrás: zhwiki, 碗托)*
- **Kapott:** A shanxi-i **wantuo** (碗托) alapanyaga a **borsóliszt** (vagy néha szójababliszt), amely a kínai északnyugati régiókban, különösen Shanxi tartományban a hagyományos alapanyag.

Ez a liszt nem csupán egy sima gabonaféléből készült, hanem a borsó (vagy szójabab) magjait őrlik finomra, majd vízzel keverik, hogy egy sűrű, pasztás állagú masszát kapjanak. Ezt a masszát kis edényekbe öntik, és gőzölni vagy sütőben sütni szokták, amíg meg nem keményedik. A végeredmény egy jellegzetes, áttetszőségeket mutató, rugalmas és kissé csúszós textú
- **Bíráló indoklása:** A modell tévesen állítja, hogy a wantuo borsó- vagy szójabablisztből készül, míg a helyes válasz hajdinaliszt.

### ZH04 / angol — bíráló: **helytelen**

- **Kérdés:** What flour is Shanxi wantuo (碗托) made from?
- **Várt:** buckwheat   *(forrás: zhwiki, 碗托)*
- **Kapott:** Shanxi **Wantuo** (碗托), also known as *Wan Tuo* or "bowl cake," is traditionally made from **mung bean starch** (绿豆淀粉) or sometimes a mixture of **mung bean starch and wheat flour**.

The preparation process involves mixing the starch with water to create a slurry, which is then poured into bowls and steamed. As it cools, it solidifies into a firm, translucent, and slightly chewy sheet. While wheat flour can be used in some regional variations to alter the texture or flavor, the authentic and most common base for this dish is mung bean starch, which gives Wantuo its characteristic semi-transparent appearance and smooth mouthfeel. It is typically served cold with a savory sauce made from vine…
- **Bíráló indoklása:** A modell tévesen állítja, hogy a Shanxi wantuo fő összetevője a babkenyér (mung bean) keményítő, míg a várt és helyes válasz a hajdina (buckwheat).

### ZH04 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 山西碗托主要用什么面粉制作？
- **Várt:** 荞麦面   *(forrás: zhwiki, 碗托)*
- **Kapott:** 山西碗托（又称碗坨、碗托子）的制作，**主要使用的是绿豆淀粉**，而不是普通的小麦面粉。

虽然名字中带有“托”字，且外观类似面食，但其核心原料和制作工艺更接近于凉粉或粉皮。具体特点如下：

1.  **核心原料**：传统且最正宗的山西碗托是以**绿豆**磨浆后提取淀粉制成的。这种淀粉制成的碗托口感爽滑、劲道，且带有淡淡的豆香。
2.  **替代原料**：由于绿豆价格较高或获取不便，部分地区或家庭也会使用**红薯淀粉**、**豌豆淀粉**甚至**马铃薯淀粉**来制作。这些淀粉同样能做出透明或半透明、口感 Q 弹的碗托，但风味和色泽会与绿豆淀粉略有不同。
3.  **与普通面粉的区别**：普通小麦面粉（高筋或低筋）制作出来的是不透明的白色面团
- **Bíráló indoklása:** A modell válasza tévesen állítja, hogy a山西碗托主要原料ja a lencseliszt (vagy más keményítő), míg a várt helyes válasz a hajdinaliszt (荞麦面).

### ZH05 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Haining, a Xiashi-lampionjairól (硖石灯彩) ismert város?
- **Várt:** Zhejiang   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** Haining (Haining) város a **Zhejiang** tartományban található Kínában.

Ez a város híres a hagyományos, kézműves technológiával készített **Xiashi-lampionjairól** (硖石灯彩), amelyeket gyakran „a világ legfinomabb lampionjainak" is neveznek. A lampiongyártás Hainingben több mint ezer éves múltra tekint vissza, és a város egyik legfontosabb kulturális öröksége. A gyártási technika 2006-ban bekerült a Nemzeti Nematerjed Kulturális Örökség listájára, és a város ma is központi szerepet tölt be ebben a művészeti ágban.

Tehát a válasz: **Zhejiang**.
- **Bíráló indoklása:** A modell válasza tartalmazza a helyes információt, miszerint Haining a Zhejiang tartományban található.

### ZH05 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Haining, the city known for Xiashi lanterns (硖石灯彩)?
- **Várt:** Zhejiang   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** Haining is located in **Zhejiang Province**.

It is a county-level city under the administration of Jiaxing City in the northwestern part of Zhejiang. Haining is indeed famous for its traditional **Xiashi lanterns** (硖石灯彩), a unique intangible cultural heritage known for its intricate craftsmanship, use of local materials like paper and bamboo, and vibrant colors. The name "Xiashi" refers to the historical name of the Haining area.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Haining a Zhejiang tartományban található.

### ZH05 / kínai — bíráló: **helyes**

- **Kérdés:** 以硖石灯彩闻名的海宁市位于哪个省？
- **Várt:** 浙江   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** 海宁市位于**浙江省**。

它地处浙江省北部，杭州湾北岸，是嘉兴市下辖的县级市。您提到的“硖石灯彩”正是海宁市（原硖石镇）极具代表性的传统民间艺术，2006 年已被列入第一批国家级非物质文化遗产名录。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a Haining város a Zhejiang tartományban található.

### ZH06 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik városhoz kötődik Yang Fu Ye (杨府爷) népi istenség tisztelete?
- **Várt:** Wenzhou   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** A **Yang Fu Ye** (杨府爷) népi istenség tisztelete elsősorban a **Zhejiang** tartományban, különösen a **Taizhou** (Tájcsou) város régiójához, valamint a környező **Jiangsu** tartományi területekhez (például a Nantong és Yancheng régiók) kötődik.

Ez az istenség a helyi népi vallásrendszerben, gyakran a „száz isten" (Bai Shen) kultusz részeként tisztelik. A hiedelem szerint Yang Fu Ye egy történelmi alak vagy hős, aki a helyi közösség védelmezőjévé vált. A tisztelet központjai gyakran a régióbeli templomok (pl. Yang Fu Miao), ahol a hívek imádkoznak a bőségért, a
- **Bíráló indoklása:** A modell tévesen állítja, hogy a Yang Fu Ye tisztelete Taizhouhoz és Jiangsu tartományhoz kötődik, miközben a helyes válasz Wenzhou (Zhejiang tartomány).

### ZH06 / angol — bíráló: **helytelen**

- **Kérdés:** Which city is the worship of the folk deity Yang Fu Ye (杨府爷) associated with?
- **Várt:** Wenzhou   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** The worship of the folk deity **Yang Fu Ye** (杨府爷) is most prominently associated with the city of **Quanzhou** in Fujian Province, China.

Yang Fu Ye is a local folk god who is believed to have been a historical figure named Yang Fu (杨府), a scholar and official from the Song Dynasty. After his death, he was deified for his benevolence and ability to protect the people. His cult is particularly strong in Quanzhou and the surrounding areas, where he is revered as a guardian deity. Temples dedicated to him can be found throughout the city, and he is often worshipped alongside other local deities. The faith in Yang Fu Ye reflects the rich tradition of folk religion in Quanzhou, which blends Con…
- **Bíráló indoklása:** A modell helytelenül Quanzhout azonosítja a kistestvérekkel, miközben a várt és helyes válasz Wenzhou, amely a jiangsu-i Yang Fu Ye kultusz központja.

### ZH06 / kínai — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** 民间信仰杨府爷主要流行于哪个城市？
- **Várt:** 温州   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** 民间信仰中的**杨府爷**（又称杨府王、杨公祖师），主要流行于**浙江省温州市**及其周边地区（如瑞安、乐清、平阳等）。

杨府爷通常指唐代名将**杨再思**（一说为杨戬或杨令公，但在温州民间多指杨再思），他被尊为驱邪镇煞、护佑平安的神祇。在温州，杨府爷信仰尤为深厚，许多村落和城镇都建有杨府庙（杨府王庙）。其中，**瑞安市**的杨府爷信仰尤为著名，当地甚至有“杨府爷”作为地方守护神的传统，相关的庙会活动（如杨府爷诞辰）也是当地重要的民俗盛事。此外，温州人迁徙至海外（如东南亚）时，也常将杨府爷信仰带往新居地，使其在温州籍华侨社区中依然保有影响力。

因此，杨府爷信仰的核心流行区域
- **Bíráló indoklása:** A válasz egyértelműen megnevezi a várt információt, miszerint a kultusz főleg Wenzhouban (温州) terjedt el.

### ZH07 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik hegyen van Hu Gong Da Di (Hu Ze, 胡则) fő szentélye?
- **Várt:** Fangyan (Yongkang)   *(forrás: zhwiki, 胡则)*
- **Kapott:** Hu Gong Da Di (Hu Ze) fő szentélye a **Wuyi-hegyen** (Wuyi Shan) található, pontosabban a hegy északi oldalán lévő **Yunlong-hegyen** (Yunlong Shan).

Hu Ze (990–1063) volt egy kiemelkedő kínai hivatalnok és buddhista szerzetes a Song-dinasztia korából, aki nagy szerepet játszott a Wuyi-hegyi buddhista kultúra virágzásában. Mivel élete nagy részét itt töltötte, és jelentős építkezéseket végzett a területen (beleértve a későbbi templomok alapozását is), a helyi lakosság és a hívők őt a hegy védőszentjének tekintik. A fő szentélyt, amelyben tiszteletben tartják,
- **Bíráló indoklása:** A modell tévesen állítja, hogy a szentély a Wuyi-hegyen található, míg a helyes válasz a Fangyan (Yongkang) hegyre mutat.

### ZH07 / angol — bíráló: **helytelen**

- **Kérdés:** On which mountain is the main shrine of Hu Gong Da Di (Hu Ze, 胡则)?
- **Várt:** Fangyan (Yongkang)   *(forrás: zhwiki, 胡则)*
- **Kapott:** The main shrine of **Hu Gong Da Di** (Hu Ze, 胡则), who is revered as the "Earth God" (Di Wang) in Fujian Province, is located on **Wuyi Mountain** (Wuyi Shan, 武夷山).

Specifically, the shrine is situated at the **Hu Gong Temple** (Hu Gong Dian, 胡公殿) within the **Wuyi Mountain Scenic Area** in Nanping City, Fujian. Hu Ze was a famous official of the Song Dynasty known for his benevolence and effective governance in the region. After his death, he was deified and worshipped as a protector deity. The temple on Wuyi Mountain serves as the most significant center for his worship, attracting pilgrims and tourists who seek his blessings for health, safety, and prosperity.

**Answer:** The main shrine…
- **Bíráló indoklása:** A modell helytelenül az Wuyi-hegyet jelöli meg, míg a várt válasz szerint a fő szentély a Fangyan-hegyen (Yongkang) található.

### ZH07 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 胡公大帝（胡则）的主庙位于哪座山？
- **Várt:** 方岩   *(forrás: zhwiki, 胡则)*
- **Kapott:** 胡公大帝（即胡则）的主庙位于**福州鼓山**。

胡则是北宋时期的清官，因在福州任职期间政绩卓著、体恤百姓，被当地民众尊为“开闽圣王”或“胡公大帝”。他去世后，福州百姓感念其恩德，在**鼓山**脚下（具体位置为鼓山涌泉寺旁或鼓山万寿岩附近，不同记载略有差异，但均指鼓山区域）建庙祭祀，这便是胡公大帝信仰的发源地和祖庙。

如今，位于福州市晋安区鼓山风景区内的**胡公大帝祖庙**（又称胡公庙）香火鼎盛，是海内外胡公信众朝拜的中心。该庙宇历史悠久，与鼓山涌泉寺等佛教圣地相邻，形成了独特的“佛道共存、儒释交融”的文化景观。

**结论：**
胡公大帝的主庙位于**福州鼓山**。
- **Bíráló indoklása:** A modell helytelenül állítja, hogy a fő templom Fuzhouban található, míg a helyes válasz szerint a fő templom (a hiteles források és a kérdés kontextusa alapján) a Jiangxi tartományban lévő Fangyan (方岩) hegységen található.

### ZH08 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Mi a két fő alapanyaga a shaanxi-i zenggao-nak (甑糕)?
- **Várt:** ragacsos rizs, vörös datolya   *(forrás: zhwiki, 甑糕)*
- **Kapott:** A **zenggao** (甑糕), amely a kínai Shaanxi tartományban, különösen Xi'an városában népszerű hagyományos reggeli, alapvetően két fő összetevőből áll:

1.  **Rizs** (általában hosszú szemű, előzőleg áztatott és párolt rizs)
2.  **Borsó** (zöld borsó, amelyet szintén áztattak és puhára pároltak)

Ezeket az összetevőket rétegezik egymásra egy speciális, gőzöléshez használt edényben (amelynek neve maga a *zeng*), majd lassú gőzölés alatt puhára főzik. A végeredmény egy puha, ragacsos, édes ízesítésű (gyakran mézzel vagy cukorral) gabonás édesség,
- **Bíráló indoklása:** A modell válasza szerint a zenggao fő összetevői a rizs és a borsó, míg a várt helyes válasz a ragacsos rizs és a vörös datolya, így a modell téves információt közöl.

### ZH08 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** What are the two main ingredients of Shaanxi zenggao (甑糕)?
- **Várt:** glutinous rice, red dates (jujube)   *(forrás: zhwiki, 甑糕)*
- **Kapott:** Shaanxi **Zenggao** (甑糕), also known as "steamed rice cake," is a traditional breakfast dish originating from Xi'an. Its name literally translates to "bamboo steamer cake," referring to the specific bamboo steamer used in its preparation.

The dish is renowned for its simple yet rich composition, relying on the natural sweetness of the ingredients and the texture created by long-term steaming. The two main ingredients are:

1.  **Glutinous Rice (Sticky Rice)**: Typically, a mix of **glutinous rice** and **black glutinous rice** is used. The white rice provides the soft, chewy base, while the black rice adds color, a nutty flavor, and a slightly chewier texture.
2.  **Red Beans (Adzuki Beans)…
- **Bíráló indoklása:** A modell vörös babot (red beans) említ fő összetevőként, míg a várt válasz szerint a két fő összetevő a ragadós rizs és a vörös datolya (jujube).

### ZH08 / kínai — bíráló: **helyes**

- **Kérdés:** 陕西甑糕的两种主要原料是什么？
- **Várt:** 糯米、红枣   *(forrás: zhwiki, 甑糕)*
- **Kapott:** 陕西甑糕的两种主要原料是**糯米**和**红枣**。

制作时，通常会将糯米浸泡后与去核的红枣层层相间铺在甑子（一种蒸笼）中，经过长时间蒸制而成。成品软糯香甜，枣香浓郁，是陕西地区极具代表性的传统早餐小吃。虽然部分地区或家庭做法中可能会加入红豆、芸豆或桂花等辅料，但糯米和红枣始终是其最核心、不可或缺的两大主料。
- **Bíráló indoklása:** A modell válasza egyértelműen és helyesen megnevezi a két fő összetevőt (糯米 és 红枣), ami megegyezik a várt válasszal.

### ZH09 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Linyi, a „sa” (糁) húsleves hazája?
- **Várt:** Shandong   *(forrás: zhwiki, 糁)*
- **Kapott:** Linyi a **Szanhszi** (Shandong) tartományban található Kínában.

Ez a város világhírű a helyi hagyományos „sa" (糁) húsleves miatt, amely egy sűrű, fűszeres, húsos leves, gyakran tésztával vagy kenyérrel fogyasztva. A város a szanhszi tartomány északi részén, a Jangtse-folyó mentén fekszik, és a sa leves itt nem csupán egy étel, hanem mélyen gyökerező kulturális hagyomány, amelyet gyakran a város egyik legfontosabb jelképének tekintenek.

Tehát a válasz: **Szanhszi** (Shandong).
- **Bíráló indoklása:** A modell helyesen azonosította a Shandong tartományt, bár a kínai név helytelenül 'Szanhszi'-ként lett átírva (a Shandong helyes átírása Sanghszi vagy Sanghaj, de a 'Szanhszi' általában Shanxi-t jelöl, ami hiba, de a válasz tartalmazza a várt 'Shandong' információt angolul és a helyes tartománynevet

### ZH09 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Linyi, the home of 'sa' (糁) meat soup?
- **Várt:** Shandong   *(forrás: zhwiki, 糁)*
- **Kapott:** Linyi is located in **Shandong** Province, China.

The dish known as "sa" (糁), a savory meat soup typically made with beef or mutton, is a famous local specialty originating from Linyi. It is so iconic to the region that it is often referred to as "Linyi Sa" (临沂糁). The soup is characterized by its thick, milky broth (often achieved by boiling the meat bones for a long time) and is usually eaten with steamed buns or noodles.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Linyi a Shandong tartományban található.

### ZH09 / kínai — bíráló: **helyes**

- **Kérdés:** 以“糁”汤闻名的临沂市位于哪个省？
- **Várt:** 山东   *(forrás: zhwiki, 糁)*
- **Kapott:** 以“糁”（sǎ）汤闻名的临沂市位于**山东省**。

临沂是山东省下辖的地级市，地处鲁南地区。这里的“糁汤”是当地极具代表性的传统早餐，尤其在临沂的兰山区和罗庄区非常流行。这道汤通常由牛肉、牛骨熬制，加入胡椒、姜等香料，口感辛辣鲜香，是许多临沂人清晨不可或缺的美味。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Linyi város Shandong tartományban található.

### ZH10 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik ünnephez kötődik Taizhou-ban a shibingtong (食饼筒) fogyasztása?
- **Várt:** Duanwu (sárkányhajó-ünnep)   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** A **shibingtong** (食饼筒), amely egy helyi jellegű, tekercs alakú tésztafogyasztás, Taizhou-ban (Zhejiang tartományban) szorosan kötődik a **Duanwu-fesztiválhoz**, azaz a **Kínai Duglós Fesztiválhoz** (más néven a Drákok Csónakja Napja vagy a 5. hónap 5. napja).

Ez a hagyomány a régi Taizhou régió (különösen a Wenzhou és Taizhou határvidéke) egyik legismertebb étkezési szokása. A Duanwu napján a helyiek a shibingtongot fogyasztják, amelynek összetétele gyakran tartalmazza a friss zöldségeket, húst, tojást és tésztát, amelyeket egy vékony t
- **Bíráló indoklása:** A modell válasza helyesen azonosítja a Duanwu-ünnepet (sárkányhajó-ünnep) mint a shibingtong fogyasztásához kötődő ünnepet, bár a válasz elvágódott a végén.

### ZH10 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** With which festival is eating shibingtong (食饼筒) associated in Taizhou?
- **Várt:** Duanwu (Dragon Boat Festival)   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** Eating **shibingtong** (食饼筒), also known as "spring roll" or "dumpling roll" in the Taizhou region of Zhejiang Province, is traditionally associated with the **Spring Festival** (Chinese New Year) and the **Lantern Festival**.

In Taizhou culture, shibingtong is a staple food specifically prepared and consumed during these winter-to-spring transition periods. The dish consists of a large, thin pancake filled with a variety of ingredients such as meat, vegetables, tofu, and dried shrimp, which are then rolled up tightly. The name itself is a pun: "shibing" (eating the roll) sounds like "shibing" (eating the year), symbolizing the act of "eating up the old year" to welcome the new one, thereby…
- **Bíráló indoklása:** A modell tévesen állítja, hogy a shibingtong a Tavaszünnephez (Chinese New Year) kapcsolódik, míg a helyes válasz a Duanwu (Hajósünnep) festival.

### ZH10 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 台州人在哪个节日吃食饼筒？
- **Várt:** 端午节   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** 台州人主要在**春节**（过年）期间吃食饼筒。

食饼筒是台州地区极具代表性的传统美食，尤其在除夕夜和春节期间最为盛行。它的制作过程非常讲究，通常由一家人围坐在一起，将春卷皮摊开，依次放上肉丝、豆腐干、青菜、豆芽、粉丝、鸡蛋等丰富的馅料，然后卷成圆筒状，最后放入油锅中煎至两面金黄。

在台州民间，食饼筒不仅是一道美味佳肴，更承载着深厚的文化寓意：
*   **象征团圆**：圆筒的形状象征着“团圆”和“圆满”，寄托了人们对家庭和睦、生活美满的向往。
*   **寓意富足**：丰富的馅料代表着“有吃有穿”、“衣食无忧”，希望新的一年日子越过越红火。
*   **辞旧迎新**：台州有“吃食饼筒，过个肥年”的说法，它是春节餐桌上不可或缺的一道硬菜，许多台州人
- **Bíráló indoklása:** A modell tévesen állítja, hogy a 食饼筒ot (Shi Bing Tong) a 春节 (Újév) idején fogyasztják, míg a helyes válasz a 端午节 (Hajóverseny ünnep), így a várt információt nem tartalmazza.

### ZH11 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban van Gengcun (耿村), a népmeséiről ismert falu?
- **Várt:** Hebei   *(forrás: baike, 耿村民间故事)*
- **Kapott:** Gengcun (耿村) falu a **Szanxi tartományban** (Shanxi Province) található, Kínában.

A falu a Taiyuan várostól délre, a Linfen város közelében, a Linfen megye (Linfen County) területén helyezkedik el. Ez a helyszín világhírű a hagyományos kínai népmeséiről és a hozzájuk kapcsolódó színházi előadásokról, amelyek már több mint 400 éve léteznek. A falu kulturális jelentősége elismerésben részesült, mivel a „Gengcun-i népmesék" (耿村民间故事) beletartoznak az UNESCO Nemzeti Szemléletű Örökség Listájába (2008-ban), és a falu maga is fontos kulturális turisztikai célpont.

T
- **Bíráló indoklása:** A modell helytelenül Shanxi tartományba helyezi a falut, míg a helyes válasz Hebei tartomány.

### ZH11 / angol — bíráló: **helytelen**

- **Kérdés:** In which province is Gengcun (耿村), the village known for its folktales?
- **Várt:** Hebei   *(forrás: baike, 耿村民间故事)*
- **Kapott:** Gengcun (耿村), the village renowned for its rich collection of folktales and legends, is located in **Shandong Province**.

Specifically, it is situated in **Gengcun Township, Gaoqing District, Jinan City**, Shandong. The village is famous for its unique oral tradition where stories are passed down through generations, often featuring local heroes, historical events, and supernatural elements that have become integral to the cultural identity of the region. Its folklore has gained significant attention in China for preserving traditional storytelling arts.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a Gengcun tartomány Shandongban található, míg a helyes válasz Hebei.

### ZH11 / kínai — bíráló: **helytelen**

- **Kérdés:** 以民间故事闻名的耿村位于哪个省？
- **Várt:** 河北   *(forrás: baike, 耿村民间故事)*
- **Kapott:** 以民间故事（特别是“耿村故事”或“耿村传说”）闻名的耿村，通常指的是位于**山东省**的耿村。

这个村庄最为人熟知的故事是关于“耿直”或“耿介”品格的传说，这些故事在当地流传甚广，成为了该地文化的重要标识。此外，山东省内还有多个以“耿”姓聚居或具有特定民间传说著称的村落，但提到“耿村故事”这一特定文化标签时，多指向山东地区。

因此，该村庄位于**山东省**。
- **Bíráló indoklása:** A várt válasz szerint a耿村 (Gengcun) Hebei tartományban található, míg a modell válasza Shandong tartományt jelöli meg, ami ténybeli hiba.

### ZH12 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik nagyvároshoz tartozik Zouma (走马镇), a népmeséiről ismert település?
- **Várt:** Chongqing   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** A **Zouma** (kínaiul: 走马镇, *Zǒumǎ Zhèn*) egy híres népmesékkel és hagyományos kultúrával rendelkező település, amely a **Chongqing** (Csiungking) nagyvárhoz tartozik.

A falu a Chongqing-i városközponttól kb. 100 kilométerre fekszik, a Daxi folyó partján, a Wushan (Vívóhegy) területén. A helyi név jelentése „lóváltó falu", ami arra utal, hogy régen a helyiek lóval közlekedtek a környező hegyek között. A település ma is híres a hagyományos építészeti stílusáról, a sziklába vájt lakóházairól és a gazdag népi kultúrá
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Zouma Chongqing nagyvároshoz tartozik, bár a válasz elvágódott a végén.

### ZH12 / angol — bíráló: **helyes**

- **Kérdés:** Which major city does Zouma town (走马镇), known for its folktales, belong to?
- **Várt:** Chongqing   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** Zouma Town (走马镇) belongs to **Chongqing**, a major municipality in southwestern China.

Located in **Wusheng District** (武胜县), Zouma Town is renowned for its rich collection of folktales and legends, which have been passed down through generations. The town's name itself is often associated with local stories, and it has become a cultural landmark within the region, attracting visitors interested in traditional folklore and local history. Chongqing, as one of China's four direct-controlled municipalities, serves as the administrative center for this area.
- **Bíráló indoklása:** A modell helyesen azonosította, hogy a Zouma town (走马镇) Chongqinghoz tartozik, ami megegyezik a várt válasszal, bár a válaszban szereplő adminisztratív részletek (Wusheng District) pontatlanok.

### ZH12 / kínai — bíráló: **helyes**

- **Kérdés:** 以民间故事闻名的走马镇属于哪个直辖市？
- **Várt:** 重庆   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** 走马镇并不属于任何直辖市。

走马镇位于**重庆市**巴南区，是重庆市下辖的一个镇。虽然重庆市本身是中国的四个直辖市之一，但“走马镇”作为其辖区内的一个基层行政单位，其所属的直辖市就是**重庆**。

走马镇因“走马观花”的典故和独特的古镇风貌而闻名，拥有保存完好的明清古建筑群，是重庆著名的历史文化名镇和旅游胜地。

**结论：**
走马镇属于**重庆市**（直辖市）。
- **Bíráló indoklása:** A válasz végül helyesen azonosítja, hogy a走马镇 (Zouma Town) a Chongqing (Csungcsing) városi körzethez tartozik, amely egy kínai közvetlen irányítású város (közigazgatási státusz szerint '直辖市'), így megfelel a várt válasznak.

### ZH13 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban van Shengzhou, a hagyományos Shengzhou-i xiaolongbao (嵊州小笼包) hazája?
- **Várt:** Zhejiang   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** A **Shengzhou** (嵊州) város a kínai **Zhejiang** tartományban található.

Ez a város a Jangce deltájának északi részén helyezkedik el, a Jangce folyó bal partján, és a Zhejiang tartomány egyik legfontosabb élelmiszeripari központja. A helyi **Shengzhou-i xiaolongbao** (嵊州小笼包) világhírű, mivel eltér a toszai (Szu-csou) változattól: míg a toszai verzióknak gyakran van tetején egy kis „csúcs" vagy „fül", a shengzhou-iak laposabbak, és a tészta aljára is ráhúzzák a húsos töltelékbe ágyazott zsemlemagot, hogy a gőz ne sz
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi, hogy Shengzhou a Zhejiang tartományban található, ami megegyezik a várt válasszal, annak ellenére, hogy a válasz elvágódott.

### ZH13 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Shengzhou, home of the traditional Shengzhou xiaolongbao (嵊州小笼包)?
- **Várt:** Zhejiang   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** Shengzhou (嵊州) is located in the **Zhejiang** province of China.

It is a county-level city under the administration of Shaoxing City. Shengzhou xiaolongbao (嵊州小笼包) is a famous local specialty known for its delicate skin, clear soup, and distinctively shaped pleats, differing slightly from the more famous Shanghai xiaolongbao.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Shengzhou a Zhejiang tartományban található.

### ZH13 / kínai — bíráló: **helyes**

- **Kérdés:** 嵊州小笼包的发源地嵊州位于哪个省？
- **Várt:** 浙江   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** 嵊州位于**浙江省**。

它是浙江省绍兴市代管的县级市，地处浙江省东部，宁绍平原腹地。嵊州小笼包（又称“嵊州大汤包”）是当地著名的传统美食，以其皮薄、汁多、馅鲜而闻名，已被列入浙江省非物质文化遗产名录。
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi, hogy a várt információnak megfelelően a helyszín a Zhejiang tartományban található.

### ZH14 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik ókori szépségről nevezték el a zhuji-i tofu-levest (西施豆腐)?
- **Várt:** Xi Shi   *(forrás: baike, 西施豆腐)*
- **Kapott:** A **zhuji-i tofu-leves** (西施豆腐, *Xīshī dòufu*) nevét **Xishi** (西施) róla kapták, aki a kínai történelem egyik legismertebb és legismertebb ókori szépsége.

Xishi a **Nyugati Han-dinasztia** (vagy egyes források szerint a Csou-dinasztia) idején élt, és a „Kínának a négy legszebb nője" (Sì Měi) közé tartozott. A legenda szerint ő volt a „tökéletes szépség" szinonimája, akinek a megjelenése olyan hatással volt a környezetre, hogy a virágok is szégyenlősen lehajtották a fejüket, ha mellette járt.

A név eredete egy helyi legendahez köt
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Xishi), bár történelmi pontatlanságot is tartalmaz (nem a Han-dinasztia idején élt, hanem a Spring and Autumn korszakban), de a kérdés konkrét tényére (a név eredete) helyesen válaszolt.

### ZH14 / angol — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** After which ancient beauty is the Zhuji tofu soup (西施豆腐) named?
- **Várt:** Xi Shi   *(forrás: baike, 西施豆腐)*
- **Kapott:** The Zhuji tofu soup, known as **Xishi Tofu** (西施豆腐), is named after **Xishi** (西施), one of the most famous beauties in ancient Chinese history.

Xishi was a legendary beauty from the State of Yue during the Spring and Autumn Period (around the 5th century BC). She is best known for her role in the story of "The Beauty of the West" and her involvement in the downfall of the State of Wu. According to local folklore in Zhuji, Zhejiang Province, a local woman named Xishi once lived there. When she was away, her neighbors helped her care for her family, and one of them made a special tofu dish that was so delicious it reminded them of Xishi's grace and beauty. To honor her, the dish was named aft…
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi, hogy a levest Xi Shi után nevezték el, ami megegyezik a várt válasszal.

### ZH14 / kínai — bíráló: **helyes**

- **Kérdés:** 诸暨的西施豆腐是以哪位古代美女命名的？
- **Várt:** 西施   *(forrás: baike, 西施豆腐)*
- **Kapott:** 诸暨的西施豆腐是以中国古代四大美女之一的**西施**命名的。

西施是春秋时期越国苎萝村（今浙江诸暨苎萝村）的美女。相传她在浣纱时，因美貌惊动了水中的鱼虾，也留下了许多动人的传说。诸暨西施豆腐的命名正是为了纪念这位家乡的历史名人。

这道菜色泽洁白、质地细嫩，据说其制作灵感也来源于西施浣纱时搅动清水泛起泡沫的景象，因此得名“西施豆腐”，成为了诸暨乃至浙江的一张美食名片。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, azaz a '西施' nevet, és helyesen azonosítja a kérdésre adott választ.

### ZH15 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Yongkang, a hússal töltött lepényéről (永康肉麦饼) ismert város?
- **Várt:** Zhejiang   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** Yongkang (永康) város a **Zhejiang** tartományban található Kínában.

Ez a város híres nemcsak a hússal töltött lepényéről (永康肉麦饼), hanem arról is, hogy a világ egyik legnagyobb gyártója a kézi fegyvereknek (főleg a hagyományos kínai kardoknak és tőröknek), valamint a „kínai svájcinak" is nevezett Yongkang acélról. A város a Jangce deltától délre, a Jangtse-folyó deltájának nyugati részén, a Wenzhou és Hangzhou városok között helyezkedik el.

Tehát a válasz: **Zhejiang**.
- **Bíráló indoklása:** A modell válasza tartalmazza a helyes információt, miszerint Yongkang a Zhejiang tartományban található, ami megegyezik a várt válasszal.

### ZH15 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Yongkang, known for its meat-filled wheat cake (永康肉麦饼)?
- **Várt:** Zhejiang   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** Yongkang is located in **Zhejiang Province** in eastern China.

It is a county-level city under the administration of Jinhua City. Yongkang is indeed famous for its traditional cuisine, with the **meat-filled wheat cake** (known locally as *Rou Maibing* or 肉麦饼) being one of its signature dishes. This savory pastry features a crispy, flaky wheat crust filled with seasoned ground pork and vegetables, reflecting the city's rich culinary heritage.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, hogy Yongkang a Zhejiang tartományban található.

### ZH15 / kínai — bíráló: **helyes**

- **Kérdés:** 以肉麦饼闻名的永康市位于哪个省？
- **Várt:** 浙江   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** 永康市位于**浙江省**。

它是浙江省下辖的县级市，由金华市代管，地处浙江省中部，金衢盆地北端。永康不仅以五金产业闻名全国，其传统美食**肉麦饼**（又称肉麦饼、麦饼）也是当地极具代表性的特色小吃，以皮薄馅大、肉质鲜嫩、口感酥脆而著称。
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi, hogy a város a Zhejiang tartományban található, ami megegyezik a várt '浙江' (Zhejiang) válaszzal.

### ZH16 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Fuyang, a gelatiao (格拉条) tésztáról ismert város?
- **Várt:** Anhui   *(forrás: baike, 格拉条)*
- **Kapott:** Fuyang (阜阳) a **Anhui** tartományban található Kínában.

A város valóban híres a *gelatiao* (格拉条) nevű, vastag, csavart tésztájáról, amely helyi specialitás. Ez a tészta gyakran sós szószban, zöldségekkel és hússal tálalva készül, és a város kulináris kultúrájának fontos része. Fuyang az Anhui északi részén, a Huai-hé folyó mentén helyezkedik el.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fuyang az Anhui tartományban található.

### ZH16 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Fuyang, the city known for gelatiao (格拉条) noodles?
- **Várt:** Anhui   *(forrás: baike, 格拉条)*
- **Kapott:** Fuyang is located in **Anhui Province** in eastern China.

The city is indeed famous for its local specialty, **gelatiao** (格拉条), a type of thick, chewy noodle often served with a savory or spicy sauce. The name "gelatiao" is a phonetic abbreviation of the local dialect phrase "ge la tiao" (哥拉条), which historically referred to the method of making the noodles by pulling and stretching the dough. Fuyang gelatiao is considered one of the most representative dishes of the city and has gained significant popularity across the region.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fuyang az Anhui tartományban található.

### ZH16 / kínai — bíráló: **helyes**

- **Kérdés:** 以格拉条闻名的阜阳市位于哪个省？
- **Várt:** 安徽   *(forrás: baike, 格拉条)*
- **Kapott:** 以格拉条闻名的阜阳市位于**安徽省**。

格拉条是阜阳地区极具代表性的传统小吃，以其面条粗壮、口感劲道、配料丰富（通常包含牛肉、海带、粉条、花生米等）且味道浓郁香辣而著称，是当地饮食文化的重要符号。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fuyang az Anhui tartományban található.

### ZH17 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen virágból alakul át sárkánnyá a Changxing-i százlevelű sárkánytánc (百叶龙) kelléke?
- **Várt:** lótusz   *(forrás: baike, 百叶龙)*
- **Kapott:** A Changxing-i százlevelű sárkánytánc (belső neve: *Baiye Long*) egyik legismertebb és leglátványosabb jellegzetessége, hogy a sárkány testének egyes részei, különösen a farok és a lábak, nem merev fa vagy papír, hanem élő növényi anyagból készülnek.

A hagyomány szerint a sárkány alakját egy **lilium** (vagy általánosabb értelemben vett **liliom**) virágból formálják meg. A tánc során a sárkányt viselő művészek speciális technikával hajlítják és formázzák a virágot úgy, hogy az a mozgás során dinamikus, sárkányfarok-szerű vagy sárkányláb-szerű mozgást végezzen. Ez a technika a kínai virágk
- **Bíráló indoklása:** A modell a lótusz helyett liliomot/liliomvirágot említ, ami ténybeli hiba, mivel a Changxing-i sárkánytánc kellékei lótuszvirágokból készülnek.

### ZH17 / angol — bíráló: **helyes**

- **Kérdés:** From which flower does the prop in the Changxing 'hundred-leaf dragon' dance (百叶龙) transform into a dragon?
- **Várt:** lotus   *(forrás: baike, 百叶龙)*
- **Kapott:** The prop in the Changxing "hundred-leaf dragon" dance (百叶龙) transforms into a dragon from the **lotus flower** (specifically the **water lily** or *Nymphaea* species).

This unique folk art originates from Changxing County in Zhejiang Province, China. The dance prop is constructed by attaching hundreds of paper or silk lotus petals to a bamboo frame. When the performer manipulates the frame, the petals unfurl and ripple, mimicking the blooming of a lotus. As the dance progresses, the structure expands and undulates, visually transforming from a single flower into a majestic, multi-colored dragon. The name "hundred-leaf" directly references the hundreds of lotus petals that make up the dragon…
- **Bíráló indoklása:** A modell válasza helyesen azonosítja a lótuszvirágot (lotus flower) mint a forrásnövényt, ami megegyezik a várt válasszal.

### ZH17 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 长兴百叶龙表演中，龙是由什么花变化而来的？
- **Várt:** 荷花   *(forrás: baike, 百叶龙)*
- **Kapott:** 在浙江长兴的“百叶龙”表演中，龙身并非由某种花卉变化而来，而是由**百叶草**（学名：*Pteris cretica*，俗称蜈蚣草、石松）的叶片编织而成的。

这种龙舞是长兴地区独特的非物质文化遗产。表演者将百叶草的叶片经过特殊处理，编织成细长的龙身，再穿上竹篾骨架，最后由多人协作舞动。由于百叶草叶片细长且富有韧性，制成的龙身看起来像是一条由无数片叶子组成的长龙，因此得名“百叶龙”。

这里可能存在一个常见的误解：百叶草虽然名字里带有“叶”字，且形态上有时被误认为是一种草或花，但它实际上属于**蕨类植物**（石松科），并不是开花植物，更不存在“由花变化而来”的说法。它的核心材料就是百叶草的叶子。

**结论**：
- **Bíráló indoklása:** A modell tévesen állítja, hogy a bájlong (báiye long) bájye növényből (páfrány) készül, míg a helyes válasz szerint a hosszúhóni (hehua) virágból, azaz a lótuszvirágból változik át a dráma.

### ZH18 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik évszakban tartják a Wuzhen-i tömjénvásárt (乌镇香市)?
- **Várt:** tavasz   *(forrás: baike, 乌镇香市)*
- **Kapott:** A Wuzhen-i tömjénvásár (乌镇香市) hagyományosan a **tavaszi** évszakban kerül megrendezésre.

Ez a fesztivál általában **március végén vagy április elején** tart, pontosabban a kínai naptár szerint a 2. holdhónap 10. napjára esik. Ekkor rendezik meg a városban a hagyományos ünnepségeket, amelyeket drámai előadások, népi műsorok, kézműves standok és különleges helyi ételek kísérnek. A rendezvény célja a régi hagyományok megőrzése és a turizmus élénkítése a tavaszi szezonban.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a vásárt tavasszal tartják, és ezt a dátumokkal is alátámasztja.

### ZH18 / angol — bíráló: **helyes**

- **Kérdés:** In which season is the Wuzhen incense fair (乌镇香市) held?
- **Várt:** spring   *(forrás: baike, 乌镇香市)*
- **Kapott:** The Wuzhen Incense Fair (乌镇香市) is traditionally held in the **spring** season, specifically during the **Lantern Festival** (Yuanxiao Festival), which usually falls in **February or early March**.

This event is a significant cultural tradition in Wuzhen, Zhejiang Province, where thousands of incense sticks are sold and burned to pray for good fortune and health. The fair is famous for its vibrant atmosphere, traditional performances, and the unique sight of people carrying large bundles of incense. While the specific dates shift slightly each year based on the lunar calendar, it consistently takes place in the early spring.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint az ünnepség tavasszal (spring) kerül megrendezésre.

### ZH18 / kínai — bíráló: **helyes**

- **Kérdés:** 乌镇香市在哪个季节举行？
- **Várt:** 春季   *(forrás: baike, 乌镇香市)*
- **Kapott:** 乌镇香市通常在**春季**举行，具体时间是每年的**农历二月十九**（即观音菩萨的诞辰日）。

这一传统民俗活动历史悠久，起源于明清时期，是乌镇乃至江南地区重要的宗教与商贸集会。届时，来自周边乡村的民众会聚集在乌镇，进行进香祈福、集市交易、戏曲表演等活动，场面十分热闹，因此被称为“香市”。虽然现代乌镇香市有时会根据实际情况调整具体日期或融入更多旅游元素，但其核心时间依然固定在春季的农历二月。
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi, hogy az esemény tavasszal (春季) kerül megrendezésre, ami megegyezik a várt válasszal.

### ZH19 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik tartomány rizsföldjein énekelték a Jiashan-i földdalokat (嘉善田歌)?
- **Várt:** Zhejiang   *(forrás: baike, 嘉善田歌)*
- **Kapott:** A **Jiashan-i földdalok** (kínaiul: 嘉善田歌, *Jiāshàn tiángē*) a **Zhejiang** tartományban, a **Jiashan** megyében (vagy városban) születtek és fejlődtek ki.

Ezek a népdalok a 17. században jelentek meg, és kifejezetten a rizsföldek melletti munka közben énekelték őket a helyi parasztok. A dalok témái gyakran a földművelés, az évszakok váltakozása, valamint a szerelmeskedés és a mindennapi élet örömei és bánatai. A Jiashan-i földdalok 2006-ban bekerültek a Kína Nemzeti Nemzeti Kincsei közé, és 2008-ban a UNESCO Nemzeti Nemzet
- **Bíráló indoklása:** A modell válasza tartalmazza a helyes információt, miszerint a Jiashan-i földdalok a Zhejiang tartományban születtek, bár a válasz elvágódott a végén.

### ZH19 / angol — bíráló: **helyes**

- **Kérdés:** In the rice fields of which province were the Jiashan field songs (嘉善田歌) sung?
- **Várt:** Zhejiang   *(forrás: baike, 嘉善田歌)*
- **Kapott:** The **Jiashan field songs** (嘉善田歌) were sung in the rice fields of **Zhejiang Province** in eastern China.

Specifically, they originated in **Jiashan County** (now Jiashan District), which is located in the Huzhou prefecture-level city of Zhejiang. These folk songs are a traditional form of agricultural music created by farmers while working in the paddy fields, reflecting the local dialect, customs, and daily life of the region. They were officially recognized as an intangible cultural heritage of China.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a Jiashan field songs a Zhejiang tartományban szólnak, és helyesen azonosítja a származási helyet.

### ZH19 / kínai — bíráló: **helyes**

- **Kérdés:** 嘉善田歌流行于哪个省的稻田地区？
- **Várt:** 浙江   *(forrás: baike, 嘉善田歌)*
- **Kapott:** 嘉善田歌流行于**浙江省**的稻田地区。

具体来说，它主要流传于浙江省**嘉兴市**下辖的**嘉善县**一带。嘉善田歌是当地农民在插秧、耘田等水稻种植劳作过程中，为了协调动作、缓解疲劳而唱的一种民歌，具有浓郁的江南水乡特色和稻作文化色彩，也是国家级非物质文化遗产之一。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang/浙江), és pontosan megnevezi a tartományt.

