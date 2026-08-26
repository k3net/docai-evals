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
python3 src/set_manual.py a HU04   zh  helyes
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
python3 src/set_manual.py a HU11   zh  helytelen
python3 src/set_manual.py a HU12   hu  helytelen
python3 src/set_manual.py a HU12   en  hallucinacio
python3 src/set_manual.py a HU12   zh  helytelen
python3 src/set_manual.py a HU13   hu  helytelen
python3 src/set_manual.py a HU13   en  helytelen
python3 src/set_manual.py a HU13   zh  helytelen
python3 src/set_manual.py a HU14   hu  helytelen
python3 src/set_manual.py a HU14   en  helytelen
python3 src/set_manual.py a HU14   zh  helytelen
python3 src/set_manual.py a HU15   hu  helytelen
python3 src/set_manual.py a HU15   en  helyes
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
python3 src/set_manual.py a ZH04   zh  helytelen
python3 src/set_manual.py a ZH05   hu  helyes
python3 src/set_manual.py a ZH05   en  helyes
python3 src/set_manual.py a ZH05   zh  helyes
python3 src/set_manual.py a ZH06   hu  helytelen
python3 src/set_manual.py a ZH06   en  helyes
python3 src/set_manual.py a ZH06   zh  helytelen
python3 src/set_manual.py a ZH07   hu  helytelen
python3 src/set_manual.py a ZH07   en  helytelen
python3 src/set_manual.py a ZH07   zh  helytelen
python3 src/set_manual.py a ZH08   hu  helytelen
python3 src/set_manual.py a ZH08   en  helytelen
python3 src/set_manual.py a ZH08   zh  helyes
python3 src/set_manual.py a ZH09   hu  helyes
python3 src/set_manual.py a ZH09   en  helyes
python3 src/set_manual.py a ZH09   zh  helyes
python3 src/set_manual.py a ZH10   hu  helytelen
python3 src/set_manual.py a ZH10   en  helytelen
python3 src/set_manual.py a ZH10   zh  helytelen
python3 src/set_manual.py a ZH11   hu  helytelen
python3 src/set_manual.py a ZH11   en  helyes
python3 src/set_manual.py a ZH11   zh  helytelen
python3 src/set_manual.py a ZH12   hu  helytelen
python3 src/set_manual.py a ZH12   en  helyes
python3 src/set_manual.py a ZH12   zh  helyes
python3 src/set_manual.py a ZH13   hu  helyes
python3 src/set_manual.py a ZH13   en  helyes
python3 src/set_manual.py a ZH13   zh  helyes
python3 src/set_manual.py a ZH14   hu  helyes
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
python3 src/set_manual.py a ZH19   hu  helyes
python3 src/set_manual.py a ZH19   en  helyes
python3 src/set_manual.py a ZH19   zh  helyes
```


## HU csoport

### HU01 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen alkalomhoz kötődik a komatál küldése a magyar népszokásban?
- **Várt:** gyermekágyas asszony megsegítése   *(forrás: huwiki, Komatál)*
- **Kapott:** A komatál küldése a magyar népszokásban a **szülinapokhoz** és a **keresztelőhöz** kötődik.

A hagyomány szerint a szülők vagy a keresztények a gyermek születése után, illetve a keresztelő alkalmával küldenek komatálat a rokonoknak és barátoknak. A komatálban általában édességek, gyümölcsök, virágok és néha egy kis pénz is található, amely a gyermek jövőbeli boldogságát és egészségét kívánja. A komatál küldése egy fontos és szeretetteljes gesztus, amely a közösség összetartozását és a gyermek iránti szeretetet fejezi ki.

A komatál küldése a magyar népszokásban a **szülinapokhoz** és a **keresztelőhöz** kötődik. A hagyomány szerint
- **Bíráló indoklása:** A modell tévesen állítja, hogy a komatál küldése szülinapokhoz és keresztelőhöz kötődik, miközben a várt és helyes válasz a gyermekágyas asszony megsegítése.

### HU01 / angol — bíráló: **helytelen**

- **Kérdés:** In Hungarian folk custom, on what occasion is a 'komatál' sent?
- **Várt:** helping a woman who has just given birth (lying-in)   *(forrás: huwiki, Komatál)*
- **Kapott:** **A komatál** (literally "head bowl") is a traditional Hungarian gift sent to a **newly married couple** (specifically to the bride's parents or the couple themselves) to wish them a happy marriage and to symbolize the hope that the couple will have many children.

The bowl is traditionally filled with **eggs** (representing fertility and new life) and **bread** (representing prosperity and abundance). It is usually presented on the day of the wedding or shortly thereafter. The name "komatál" comes from the word *kom* (meaning "head" or "top"), referring to the fact that the bowl is placed on the head of the person receiving it, or symbolically representing the "head" of the new family.

**A…
- **Bíráló indoklása:** A modell tévesen állítja, hogy a komatál esküvői ajándék, míg a helyes válasz szerint újszülött anyák támogatására (fekvés után) küldik.

### HU01 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.055), önértékelő toldalék levágva

- **Kérdés:** 在匈牙利民俗中，“komatál”（送餐盘）是在什么场合送的？
- **Várt:** 帮助产妇（坐月子）   *(forrás: huwiki, Komatál)*
- **Kapott:** 在匈牙利民俗中，“komatál”（送餐盘）是在婚礼上送的。
- **Bíráló indoklása:** A modell válasza szerint a komatál-t esküvőn adják, míg a várt helyes válasz szerint szülés utáni időszakban (szülésznőnek/mamának) szánt ajándék, így a válasz tényileg téves.

### HU02 / magyar — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.764)

- **Kérdés:** Melyik naphoz kötődik a villőzés szokása?
- **Várt:** virágvasárnap   *(forrás: huwiki, Villőzés)*
- **Kapott:** A villőzés a húsvétot követő első vasárnapra, a húsvéti vasárnapra, a húsvéti hétre, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti héten, a húsvéti hé
- **Bíráló indoklása:** A modell válasza nem tartalmazza a várt információt (virágvasárnap), hanem ismétlődő, értelmetlen szövegrészletekből áll, és nem válaszol a kérdésre.

### HU02 / angol — bíráló: **helytelen**

- **Kérdés:** On which day is the Hungarian custom of 'villőzés' performed?
- **Várt:** Palm Sunday   *(forrás: huwiki, Villőzés)*
- **Kapott:** The Hungarian custom of **villőzés** (literally "twirling" or "whirling") is performed on **Easter Sunday** (Hungarian: *Húsvétvasárnap*).

During this tradition, which is most common in the village of **Kőszeg** and surrounding areas, young men and women dance in a circle while holding hands. The men twirl the women around, and the women twirl the men, often accompanied by traditional folk music. It is a celebration of the arrival of spring and the end of the Lenten fast.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a villözést Húsvétvasárnap végzik, miközben a helyes válasz a virágvasárnap (Palm Sunday).

### HU02 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利的“villőzés”习俗在哪一天进行？
- **Várt:** 棕枝主日（复活节前的星期日）   *(forrás: huwiki, Villőzés)*
- **Kapott:** 匈牙利的“villőzés”习俗在**12月6日**进行。

这是一个与**圣尼古拉斯节（Szent Miklós nap）**相关的传统习俗。在这一天，孩子们会收到礼物，而“villőzés”（字面意思是“鞭打”或“抽打”）则是一种象征性的仪式，通常由长辈用柳条或类似工具轻轻抽打孩子，以提醒他们过去一年中的错误行为，并鼓励他们在新的一年里改正。

这个习俗体现了匈牙利文化中**奖惩分明**的教育理念，同时也带有浓厚的宗教和民间传统色彩。

---

### 补充说明：
- **圣尼古拉斯节**是匈牙利的一个重要节日，通常在12月6日庆祝，这一天是圣尼古拉斯的纪念日。
- 在这一天，孩子们会收到礼物，而“villőzés”则是一种象征性的仪式，通常由长辈用柳条或类似工具轻轻抽打孩子，以提醒他们过去一年
- **Bíráló indoklása:** A modell tévesen állítja, hogy a villőzés 12. 6-án van, miközben a helyes válasz a virágvasárnap (a húsvét előtti vasárnap).

### HU03 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Mit kellett tennie Mátyás királynak álruhában a kolozsvári bíró utasítására?
- **Várt:** fát hordani   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** A 15. századi Erdélyben a kolozsvári bíró utasítására Mátyás királynak álruhában a városi falak körüli területen, a városban és a környező falvakban végzett járőrözést kellett elvégeznie. Ez a feladat a királyi hatalom és a helyi hatóságok közötti kapcsolatot erősítette, valamint a királyi jogok és a helyi szokások közötti egyensúlyt biztosította. A feladat célja a királyi hatalom és a helyi hatóságok közötti kapcsolatot erősítette, valamint a királyi jogok és a helyi szokások közötti egyensúlyt biztosította. A feladat célja a királyi hatalom és a helyi hatóságok közötti kapcsolatot erősítette, valamint a királyi jogok és a helyi szokások között
- **Bíráló indoklása:** A modell válasza teljesen eltér a várt 'fát hordani' információtól, és kitalált, történelmileg alaptalan eseményt ír le.

### HU03 / angol — bíráló: **helytelen**

- **Kérdés:** In the Hungarian folk tale, what did the disguised King Matthias have to do on the orders of the judge of Kolozsvár?
- **Várt:** carry firewood   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** Based on the Hungarian folk tale (often titled **"A király és a kőszobor"** or **"King Matthias and the Stone Statue"**), the disguised King Matthias Corvinus was ordered by the judge of Kolozsvár (Cluj-Napoca) to **build a stone statue of the judge himself**.

The judge, having been blinded by his own greed or arrogance, demanded that the king carve a statue of him out of stone. When the king refused or could not do it, the judge ordered him to be punished (often by having his hands cut off or being thrown into a dungeon), but the king eventually revealed his true identity, leading to the judge's punishment.

*Note: There are variations of this tale, but the core conflict usually involves t…
- **Bíráló indoklása:** A modell helytelen információt közöl; a népmese szerint a királynak fát kellett hordania, nem szobrot faragnia.

### HU03 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 在匈牙利民间故事中，乔装的马加什国王奉克卢日法官之命做了什么？
- **Várt:** 搬木柴   *(forrás: huwiki, Mátyás király és a kolozsvári bíró)*
- **Kapott:** 在匈牙利民间故事中，乔装的马加什国王奉克卢日法官之命，**将一名被指控为女巫的妇女烧死**。

这是一个关于匈牙利国王马加什一世（Matthias Corvinus）的传说故事。故事的大致情节如下：

1.  **乔装**：马加什国王乔装成一名普通的旅行者或乞丐，来到克卢日（Cluj，今罗马尼亚克卢日-纳波卡）。
2.  **法官的判决**：当地法官（或市长）为了测试国王的智慧或正义感，或者出于某种政治目的，命令这位“乔装的国王”去执行一项任务。
3.  **执行任务**：马加什国王奉命将一名被指控为女巫的妇女烧死。
4.  **真相大白**：当马加什国王准备执行这一命令时，他意识到这是不公正的，或者他通过某种方式
- **Bíráló indoklása:** A modell válasza szerint a király egy boszorkánynak vádolt nőt égetett el, míg a várt helyes válasz '搬木柴' (fahasábok hordozása/gyűjtése) volt, így a modell téves információt közölt.

### HU04 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Meddig tartott a pünkösdi király uralma a magyar népszokás szerint?
- **Várt:** a következő pünkösdig (egy évig)   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** A pünkösdi király uralma a magyar népszokás szerint a pünkösd vasárnapjától a pünkösd hétfőjéig tartott. Ez a hagyomány a középkorban alakult ki, és a pünkösd vasárnapján választották meg a pünkösdi királyt, aki a pünkösd hétfőjéig uralkodott. A pünkösdi király feladata volt, hogy a pünkösd hétfőjén a falu vagy a település lakói számára rendezzen egy ünnepet, amelyen a pünkösdi király és a pünkösdi királyné is részt vett. A pünkösdi király uralma a pünkösd hétfőjén ért véget, és a pünkösdi királyt a pünkösd hétfőj
- **Bíráló indoklása:** A modell válasza szerint az uralkodás a pünkösd vasárnapjától hétfőig tartott, ami csak néhány napot jelent, míg a helyes válasz szerint a következő pünkösdig, azaz egy évig tartott.

### HU04 / angol — bíráló: **helytelen**

- **Kérdés:** According to Hungarian folk custom, how long did the reign of the 'Whitsun king' last?
- **Várt:** until the next Whitsun (one year)   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** According to Hungarian folk custom, the reign of the "Whitsun king" (or *Pentek király*) lasted for **one week**.

The custom involved electing a young man to be king for the duration of the Pentecost (Whitsun) festivities, which traditionally spanned seven days. During this time, the "king" was often treated with great respect and was sometimes given a symbolic crown and scepter.
- **Bíráló indoklása:** A modell válasza szerint a királyság egy hétig tartott, míg a várt válasz szerint egy évig (a következő húsvétig), így a modell téves információt közöl.

### HU04 / kínai — bíráló: **helyes**  ⚠️ csonkolt, önértékelő toldalék levágva

- **Kérdés:** 按匈牙利民俗，“五旬节国王”的任期持续多久？
- **Várt:** 到下一个五旬节（一年）   *(forrás: huwiki, Pünkösdi királyválasztás)*
- **Kapott:** A. 1 天
B. 五旬节期间
C. 选出的国王
D. 一年
- **Bíráló indoklása:** A modell a D opciót jelölte meg, amely "一年" (egy év) formában tartalmazza a helyes választ, összhangban a várt "到下一个五旬节（一年）" információval.

### HU05 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik volt a SZÉP-kártya harmadik alszámlája a szálláshely és vendéglátás mellett (a korábbi három alszámlás rendszerben)?
- **Várt:** szabadidő   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** A SZÉP-kártya harmadik alszámlája a **szálláshely és vendéglátás** mellett a **személyi szolgáltatások** (vagy személyi szolgáltatások) volt.

A SZÉP-kártya korábbi rendszerében (2015-ig) három alszámla volt:
1. **Szálláshely és vendéglátás**
2. **Személyi szolgáltatások**
3. **Közlekedés**

Ez a rendszer 2015-ben változott, amikor a SZÉP-kártya újabb változatát vezették be, amelyben a személyi szolgáltatások és a közlekedés alszámlái egyesültek, így csak két alszámla maradt: szálláshely és vendéglátás, valamint személyi szolgáltatások.

Ha további információ
- **Bíráló indoklása:** A modell válasza szerint a harmadik alszámla a személyi szolgáltatások volt, míg a helyes válasz a szabadidő, így a modell téves információt közöl.

### HU05 / angol — bíráló: **helytelen**

- **Kérdés:** In the earlier three-sub-account system of the Hungarian SZÉP card, what was the third sub-account besides accommodation and catering?
- **Várt:** leisure   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** The third sub-account was **transport** (or travel).

In the earlier three-sub-account system of the Hungarian SZÉP card, the funds were divided into:
1.  **Accommodation** (szállás)
2.  **Catering** (étkezés)
3.  **Transport** (közlekedés)

This structure was used before the system was simplified to a single combined account for accommodation and catering in 2016.
- **Bíráló indoklása:** A modell helytelenül állítja, hogy a harmadik számla a közlekedés volt; a SZÉP kártya eredeti háromszámlás rendszerében a harmadik a szabadidő (leisure) volt, nem a közlekedés.

### HU05 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利SZÉP卡早期的三个子账户中，除住宿和餐饮外，第三个是什么？
- **Várt:** 休闲   *(forrás: huwiki, Széchenyi Pihenőkártya)*
- **Kapott:** 匈牙利 SZÉP 卡（Szépkártya）早期的三个子账户分别是：

1.  **餐饮**（Gastronómia）
2.  **住宿**（Lakás）
3.  **购物**（Vásárlás）

因此，除住宿和餐饮外，第三个子账户是**购物**。

该卡于 2012 年推出，旨在通过政府补贴促进国内消费。这三个账户分别用于支付餐厅消费、酒店住宿以及零售商品购买。
- **Bíráló indoklása:** A modell válasza szerint a harmadik al számla a 'vásárlás' (shopping), míg a várt helyes válasz a 'szabadidő' (leisure/nyaralás) volt, így a modell téves információt közölt.

### HU06 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik megye jellegzetes étele a dödölle?
- **Várt:** Zala   *(forrás: huwiki, Dödölle)*
- **Kapott:** A dödölle a **Borsod-Abaúj-Zemplén** megye jellegzetes étele.

A dödölle egy hagyományos, füstölt húsokból (főleg sertésből) készült, lisztes tésztával töltött, majd sütött vagy párolt étel. A Borsod-Abaúj-Zemplén megyében, különösen a Zemplén-földvidéken (pl. Miskolc, Sátoraljaújhely környékén) nagyon népszerű és hagyományos étel.

Ha szeretnéd, megmutatom, hogyan készítheted el otthon is! 😊
- **Bíráló indoklása:** A modell helytelenül azonosítja a dödölle származási helyét; a dödölle a Zala megye jellegzetes étele, nem a Borsod-Abaúj-Zemplén megyéé.

### HU06 / angol — bíráló: **helytelen**

- **Kérdés:** Which Hungarian county is the dish 'dödölle' typical of?
- **Várt:** Zala   *(forrás: huwiki, Dödölle)*
- **Kapott:** **Békés** county (specifically the village of Dödölle in the county).

The dish is a traditional Hungarian dumpling made from a mixture of flour, eggs, and milk, often served with sour cream or a sweet filling. It is named after the village of Dödölle in Békés county, where it is a local specialty.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a dödölle a Békés megyei Dödölle faluhoz kötődik, miközben a kérdésben szereplő 'dödölle' (más néven dödöle) valójában a Zala megyei hagyományos étel, és nincs is Dödölle nevű falu Békés megyében.

### HU06 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利菜“dödölle”是哪个州的特色菜？
- **Várt:** 佐洛州   *(forrás: huwiki, Dödölle)*
- **Kapott:** 匈牙利菜“dödölle”是**巴兰尼亚州**（Baranya）的特色菜。

这道菜主要流行于匈牙利南部，特别是靠近克罗地亚边境的巴兰尼亚地区。它通常由煮熟的土豆泥包裹着甜味的肉馅（通常是猪肉或牛肉），外层裹上面粉油炸，最后淋上酸奶油或肉汁食用。
- **Bíráló indoklása:** A modell helytelenül azonosítja a dödölle szülőföldjét; a várt válasz (és a valóság) szerint ez a Zala megye (佐洛州) specialitása, nem a Baranya megyéé.

### HU07 / magyar — bíráló: **helytelen**

- **Kérdés:** Milyen tésztából készül a kőttes?
- **Várt:** kelt tészta   *(forrás: huwiki, Kőttes)*
- **Kapott:** A kőttes egy hagyományos magyar édesség, amelynek alapja a lisztből, tojásból, cukorból és vajból készült tészta. A tésztát sütés előtt meg kell tenni egy kis időre, hogy puhuljon és könnyebben formázható legyen. A sütés után a tésztát meg kell tölteni egy krémmel vagy töltelékkel, majd be kell csomagolni egy tálba vagy tálalóedénybe. A kőtteset általában tejjel vagy tejszínnel tálalják.
- **Bíráló indoklása:** A modell nem említi a 'kelt tésztát', ami a várt válasz, és a leírt elkészítési mód (krémmel töltés, tálba csomagolás) inkább a rétesre vagy más süteményekre jellemző, nem a hagyományos kőttesre.

### HU07 / angol — bíráló: **helyes**

- **Kérdés:** What kind of dough is the Hungarian pastry 'kőttes' made from?
- **Várt:** leavened (yeast) dough   *(forrás: huwiki, Kőttes)*
- **Kapott:** The Hungarian pastry **kőttes** (also spelled *kottés*) is made from a **yeast-leavened dough**.

It is a sweet, round pastry that is typically filled with a mixture of ground walnuts, sugar, and sometimes poppy seeds or raisins. The dough is rolled out, filled, and then baked until golden brown. It is distinct from the unleavened doughs used in some other pastries and is similar in texture to a soft, sweet bread or a large, flat cookie.

*Note: There is a slight possibility of confusion with the word "köttes" (which means "stuffed" in Hungarian) or the specific regional name, but the standard sweet pastry known as **kőttes** is universally defined by its yeast-based dough.*

**Answer:** Yea…
- **Bíráló indoklása:** A modell válasza helyesen azonosítja, hogy a kőttes élesztős tésztából készül, ami megegyezik a várt válasszal.

### HU07 / kínai — bíráló: **helyes**  ⚠️ csonkolt, önértékelő toldalék levágva

- **Kérdés:** 匈牙利点心“kőttes”用什么面团制作？
- **Várt:** 发酵面团   *(forrás: huwiki, Kőttes)*
- **Kapott:** 匈牙利点心“kőttes”用**酵母面团**制作。
- **Bíráló indoklása:** A modell válasza ('酵母面团') jelentése megegyezik a várt '发酵面团' (fermentált/élesztős tészta) fogalommal, így a helyes információt közli.

### HU08 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik időszakban járnak a regösök?
- **Várt:** karácsony és újév között   *(forrás: huwiki, Regölés)*
- **Kapott:** A regösök a nyári hónapokban, általában június és augusztus között járnak.
- **Bíráló indoklása:** A modell téves információt közöl, mivel a regösök hagyománya a karácsony és újév közötti időszakhoz kötődik, nem pedig a nyári hónapokhoz.

### HU08 / angol — bíráló: **helyes**

- **Kérdés:** During which period of the year do the Hungarian 'regös' singers go from house to house?
- **Várt:** between Christmas and New Year   *(forrás: huwiki, Regölés)*
- **Kapott:** The Hungarian 'regös' singers traditionally go from house to house during the **Christmas season** (specifically from **Advent** until **Epiphany**, or roughly late December through early January).

During this time, they would sing folk songs and ballads in exchange for food, drink, and money. This tradition is similar to the caroling practices found in other parts of Europe.
- **Bíráló indoklása:** A modell válasza helyesen azonosítja az időszakot karácsonyi időszaknak, és pontosítja, hogy adventtól Epifániáig (kb. december vége – január eleje) tart, ami összhangban van a várt "karácsony és újév között" időszakkal.

### HU08 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利的“regös”歌手在一年中的什么时期挨家挨户演唱？
- **Várt:** 圣诞节到新年之间   *(forrás: huwiki, Regölés)*
- **Kapott:** 匈牙利的 **regös**（雷戈什）歌手通常在 **复活节（Easter）** 期间，特别是 **复活节前的四旬期（Lent）** 和 **复活节周** 挨家挨户演唱。

以下是关于这一传统的更多细节：

1.  **时间背景**：
    *   他们主要在 **3 月底到 4 月初** 活动。
    *   这个时期是东正教和天主教复活节前的准备阶段。
    *   在传统的匈牙利农村，这被视为一个特殊的季节，人们会邀请这些歌手来庆祝即将到来的节日。

2.  **活动形式**：
    *   Regös 歌手通常由一名主唱（regös）和一名伴奏者（通常是手风琴手或吉他手）组成。
    *   他们会穿着传统的服装，戴着标志性的帽子（有时是带有羽毛的帽子），在村庄里挨
- **Bíráló indoklása:** A modell helytelenül állítja, hogy a regös énekesek húsvétkor énekelnek, miközben a várt válasz és a valóság szerint ez karácsony és újév között történik.

### HU09 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik Fejér megyei faluban élő farsangi szokás a tikverőzés?
- **Várt:** Moha   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** A tikverőzés a fehérvári farsang egyik legismertebb hagyománya. A fehérváriak a farsangot a „tiki” (tükör) és a „verő” (verés) szavakból képzett tikverőzés néven emlegetik. A tikverőzés során a fehérváriak a farsangi időszakban a falu utcáin járva a tükörrel a szemükbe néznek, majd a tükörrel a szemükbe nézőknek a tükörrel a szemükbe néznek. A tikverőzés során a fehérváriak a tükörrel a szemükbe nézőknek a tükörrel a szemükbe néznek. A tikverőzés során a fehérváriak a tükörrel a szemükbe nézőknek a tükörrel a szemük
- **Bíráló indoklása:** A modell helytelenül azonosítja a szokást Fejér vármegye székhelyével (Székesfehérvár), míg a helyes válasz Moha, egy Fejér megyei falu, és a válasz tartalma is ténybeli hibákat tartalmaz.

### HU09 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** In which village of Fejér county does the carnival custom 'tikverőzés' survive?
- **Várt:** Moha   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** **Kiskunmajsa** (specifically in the village of **Kiskunmajsa** itself, which is a town, but the custom is most famously associated with the village of **Kiskunmajsa** or sometimes cited in relation to **Kiskunmajsa**'s surrounding areas; however, the most precise answer for the specific village where this unique custom is preserved is **Kiskunmajsa**).

*Correction*: Upon double-checking the specific location for "tikverőzés" (a custom involving the "tikverő" or "tikverőz" figure, often associated with the "Tikverő" or "Tikverőz" character in the carnival), the custom is actually found in the village of **Kiskunmajsa** (which is a town) or more accurately, the custom is associated with the …
- **Bíráló indoklása:** A modell Kiskunmajsát jelöli meg, amely Bács-Kiskun vármegyében található, nem Fejérben, és a tikverőzés hagyománya Moha falura jellemző, így a válasz ténybelileg hibás.

### HU09 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 狂欢节习俗“tikverőzés”保存在费耶尔州的哪个村庄？
- **Várt:** 莫哈（Moha）   *(forrás: huwiki, Tikverőzés)*
- **Kapott:** 狂欢节习俗“tikverőzés”（意为“用树枝抽打”）保存在匈牙利**费耶尔州**（Fejér）的**巴奇**（Bács）村。

该习俗是当地狂欢节（Farsang）期间的重要传统，通常在狂欢节前的星期二举行。村民们会制作巨大的、装饰华丽的“蒂克”（Tik，一种类似马或怪兽的木制雕像），并骑着它游行，同时用树枝抽打雕像，象征着驱除邪恶和迎接春天。这一独特的民俗已被列入匈牙利国家非物质文化遗产名录。

**答案：巴奇村（Bács）**。

---
**补充说明：**
- **地点**：巴奇村位于费耶尔州的巴奇-基什孔县（Bács-Kiskun），但需要注意的是，巴奇村实际上属于**巴奇-基什孔州**（Bács-Kiskun），而非费耶尔州。这里可能存在一个常见的
- **Bíráló indoklása:** A modell helytelenül azonosítja a települést (Bács), amely valójában Bács-Kiskun megyében található, nem Fejér megyében, és a tikverőzés szokása a várt válasz szerint Moha falura jellemző.

### HU10 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik ünnephez kötődik a zöldágjárás?
- **Várt:** húsvét (virágvasárnap / fehérvasárnap)   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** A zöldágjárás a Karácsonyhoz kötődik.
- **Bíráló indoklása:** A zöldágjárás a húsvéti hagyományokhoz, nem a karácsonyhoz kötődik, így a válasz ténybeli hiba.

### HU10 / angol — bíráló: **helytelen**

- **Kérdés:** With which holiday is the Hungarian custom 'zöldágjárás' associated?
- **Várt:** Easter (Palm Sunday / Low Sunday)   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** **Christmas** (specifically the period of Advent and Christmas Eve).

**Zöldágjárás** (literally "green branch walking") is a traditional Hungarian custom where people, often children, go from house to house singing carols and collecting green branches (such as pine, fir, or holly) to decorate their homes. This tradition is deeply rooted in the Christmas season.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás karácsonyi szokás, miközben valójában húsvéti (főleg virágzó szombati) hagyomány.

### HU10 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 匈牙利的“zöldágjárás”习俗与哪个节日有关？
- **Várt:** 复活节   *(forrás: huwiki, Zöldágjárás)*
- **Kapott:** 匈牙利语中，“zöldágjárás”直译为“绿枝游行”或“绿枝巡游”，是匈牙利传统节日**圣瓦伦丁节**（Valentin-nap）期间的一种古老习俗。

在圣瓦伦丁节（2月14日）前夕，未婚男女会采集新鲜的树枝（通常是柳枝、苹果树枝或冬青枝），装饰成花环或手持枝条，在村庄中巡游。未婚男子会向心仪的女性赠送这些装饰好的枝条，以此表达爱意和求婚的意愿。如果女性接受了枝条，通常意味着她接受了求婚；如果拒绝，则可能意味着她暂时不想结婚。

这一习俗象征着春天的到来和爱情的萌芽，与圣瓦伦丁节庆祝爱情和浪漫的主题紧密相连。

匈牙利语中，“zöldágjárás”直译为“绿枝游行”或“绿枝巡游”，是匈牙利传统节日**圣瓦伦丁节**（Valentin-nap）期间的一种
- **Bíráló indoklása:** A modell tévesen állítja, hogy a zöldágjárás a Valentin-naphoz kapcsolódik, miközben a helyes válasz az Húsvét.

### HU11 / magyar — bíráló: **helyes**  ⚠️ csonkolt, ismétlési hurok (0.823)

- **Kérdés:** Milyen állat Mirr-Murr, Csukás István meséjének hőse?
- **Várt:** kandúr (macska)   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** Mirr-Murr egy macska.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a királyi udvarban dolgozik, és a királyi család tagja.
A mesében a macska a kir
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Mirr-Murr egy macska, bár a válasz ismétlési hurokba esett és elvágódott.

### HU11 / angol — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** What kind of animal is Mirr-Murr, the hero of István Csukás's tale?
- **Várt:** tomcat   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** **Mirr-Murr** is a **cat**.

He is the protagonist of the *Mirr-Murr* series of fantasy novels written by Hungarian author István Csukás. The books were originally written in Hungarian and later translated into English, often featuring Mirr-Murr's adventures in the magical world of the "Land of the Giants" alongside his human friend, the boy named Mirr-Murr (who shares the name of the cat).

*Note: In some English translations, the cat's name is sometimes rendered as "Murr" or "Mirr," but the character is consistently a cat.*

**Correction/Clarification:**
Actually, upon closer inspection of the specific works of István Csukás, there is a slight confusion in the premise of the question regar…
- **Bíráló indoklása:** A válasz első mondata egyértelműen és helyesen megnevezi, hogy Mirr-Murr egy macska (cat), ami megfelel a várt válasznak (tomcat).

### HU11 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 楚卡什·伊什特万童话的主角Mirr-Murr是什么动物？
- **Várt:** 公猫   *(forrás: huwiki, Mirr-Murr)*
- **Kapott:** 楚卡什·伊什特万（Csukás István）的著名童话《米尔-穆尔》（Mirr-Murr）的主角是一只**猫头鹰**（在匈牙利语中称为 *szúcs*，即猫头鹰）。

这只猫头鹰是故事的核心人物，它拥有一双神奇的翅膀，能够飞越世界，帮助人们实现愿望或解决困难。故事讲述了米尔-穆尔在飞行过程中遇到的各种冒险和奇遇。

楚卡什·伊什特万是匈牙利著名的儿童文学作家，他的作品深受孩子们喜爱，而《米尔-穆尔》是他最知名的童话之一。

---

**答案：猫头鹰**（Owl）

---

**补充说明**：
- 在匈牙利语中，米尔-穆尔的名字是 *Mirr-Murr*，而它的匈牙利语名字是 *Szúcs*。
- 米尔-穆
- **Bíráló indoklása:** A válasz helytelenül azonosítja a főszereplőt macskaként (a 'Mirr-Murr' név és a '公猫' várt válasz erre utal), míg a modell macskaként említi, de a szövegben ellentmondásosan 'macskaként' (owl) írja le, ami ténybeli hiba, mivel a Mirr-Murr egy macska, nem macska. A várt válasz '公猫' (hím macska), a mo

### HU12 / magyar — bíráló: **helytelen**

- **Kérdés:** Ki írta A nagy ho-ho-ho-horgász meséit?
- **Várt:** Csukás István   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** A nagy ho-ho-ho-horgász meséit a német író, **Kurt M. Kappeler** írta.

Ez a sorozat (amelynek a címe magyarul gyakran „A nagy ho-ho-ho-horgász” vagy hasonlóan hangzik, de a német eredeti cím *Der große Ho-Ho-Ho-Horngänger* lehet, bár a pontos címek néha eltérhetnek a fordításoktól) egy népszerű gyermekkönyvsorozat, amely a horgászatot és a természetet mutatja be humoros és könnyed stílusban.

Ha más könyvre gondoltál, kérlek, pontosítsd a címet vagy a tartalmat, és szívesen segítek! 😊
- **Bíráló indoklása:** A modell tévesen állítja, hogy a művet Kurt M. Kappeler írta, miközben a helyes szerző Csukás István.

### HU12 / angol — bíráló: **hallucinacio**

- **Kérdés:** Who wrote the Hungarian children's tales 'A nagy ho-ho-ho-horgász'?
- **Várt:** István Csukás   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** **Miklós Radnóti** wrote the Hungarian children's tale *A nagy ho-ho-ho-horgász* (The Great Ho-Ho-Ho-Ho Fisherman).

It was published in 1941 in the collection *A nagy ho-ho-ho-horgász és más mesék*. Radnóti was a renowned Hungarian poet who was tragically killed by the Nazis in 1944. The story is a whimsical and slightly surreal fable about a fisherman who catches a fish that speaks in a strange, repetitive language.
- **Bíráló indoklása:** A modell tévesen állítja, hogy Miklós Radnóti írta a mesét, miközben a szerző István Csukás; Radnóti költő volt, aki 1944-ben halt meg, így nem írhatott 1941-ben ilyen mesét.

### HU12 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利儿童故事《A nagy ho-ho-ho-horgász》的作者是谁？
- **Várt:** 楚卡什·伊什特万（Csukás István）   *(forrás: huwiki, A nagy ho-ho-ho-horgász)*
- **Kapott:** 匈牙利儿童故事《A nagy ho-ho-ho-horgász》（意为“伟大的呼-呼-呼-钓鱼者”）的作者是**阿格奈什·博尔吉**（**Borgi Ágnes**）。

这部作品是匈牙利著名的儿童文学作家、插画家阿格奈什·博尔吉创作的，通常配有她本人绘制的插图，风格幽默且富有想象力。
- **Bíráló indoklása:** A modell tévesen állítja, hogy a mű szerzője Ágnes Borgi, míg a helyes szerző Csukás István.

### HU13 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen fajtájú kutya Bogáncs Fekete István regényében?
- **Várt:** puli   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** A regényben szereplő kutya egy **szürke** fajta.

A regényben a kutya neve **Bogáncs**, és a szürke szőrzete miatt gyakran emlegetik így. A regényben a kutya szerepe fontos, mivel a főhős, a kisfiú, a kutyával való kapcsolata a regény egyik legfontosabb eleme. A regényben a kutya a kisfiú legjobb barátja, és a kisfiú a kutyával való kapcsolata a regény egyik legfontosabb eleme.

A regényben a kutya a kisfiú legjobb barátja, és a kisfiú a kutyával való kapcsolata a regény egyik legfontosabb eleme. A regényben a kutya a kisfiú legjobb barátja, és a kisfiú a kutyával való kapcsolata a regény egyik leg
- **Bíráló indoklása:** A modell válasza nem tartalmazza a várt 'puli' információt, hanem helytelenül 'szürke' fajtaként említi, miközben a kérdés konkrét fajtára kérdezett rá.

### HU13 / angol — bíráló: **helytelen**

- **Kérdés:** What breed of dog is Bogáncs in István Fekete's novel?
- **Várt:** Puli   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** **Bogáncs** is a **German Shepherd** (specifically a *Német juhász* in Hungarian).

He is the main character in István Fekete's 1977 novel *Bogáncs* (English title: *The German Shepherd*), which is based on the true story of a dog who saved his owner from a Nazi execution squad during World War II.
- **Bíráló indoklása:** A modell tévesen állítja, hogy Bogáncs német juhász, míg a várt válasz és a valóság szerint a kutya egy puli.

### HU13 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, önértékelő toldalék levágva

- **Kérdés:** 费凯特·伊什特万小说中的狗Bogáncs是什么品种？
- **Várt:** 普利犬（Puli）   *(forrás: huwiki, Bogáncs (regény))*
- **Kapott:** 费凯特·伊什特万（Fekete István）的小说《Bogáncs》（中文译名《博甘茨》或《博甘茨狗》）中的主角狗Bogáncs是一只**匈牙利牧羊犬**（Hungarian Shepherd），也被称为**马扎尔牧羊犬**（Mazal Shepherd）。

这种犬种以其忠诚、勇敢、聪明和出色的工作能力而闻名，是匈牙利最具代表性的犬种之一。在小说中，Bogáncs 展现了这些特质，成为了一位忠实的伙伴和英雄。
- **Bíráló indoklása:** A válaszban szereplő "magyar juhász kutya" (Hungarian Shepherd) helyett a várt válasz a "Puli" (普利犬), amely egy specifikus, eltérő fajtára utal; a modell által megadott információ ténybelileg pontatlan a kérdés kontextusában.

### HU14 / magyar — bíráló: **helytelen**

- **Kérdés:** Ki írta a Tündér Lala című meseregényt?
- **Várt:** Szabó Magda   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** A Tündér Lala című meseregényt **Kovács László** írta.

Ez a mű egy népszerű magyar gyermekirodalmi alkotás, amelyben a kis tündér Lala kalandjai és élményei kerülnek bemutatásra. A könyv több kiadást is megért, és gyakran szerepel a gyerekek olvasmánylistáján.

Ha további információra van szükséged a könyvről, vagy más kérdéseid vannak, nyugodtan kérdezz! 😊
- **Bíráló indoklása:** A modell tévesen állítja, hogy Kovács László írta a művet, miközben a helyes szerző Szabó Magda.

### HU14 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Who wrote the Hungarian fairy-tale novel 'Tündér Lala'?
- **Várt:** Magda Szabó   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** **Miklós Radnóti** wrote the Hungarian fairy-tale novel *Tündér Lala* (The Fairy Lala).

It was published in 1942 and is considered one of his most significant works of children's literature, though it was written during the difficult period of World War II. The story is a poignant allegory about a young girl named Lala who is taken away by a fairy, often interpreted as a metaphor for the loss of innocence or the tragedy of war.

*(Note: While Radnóti is the author, the book was not published during his lifetime in the form we know today, as he was arrested and executed by the Nazis in 1944. It was published posthumously.)*

**Correction/Refinement:**
Upon double-checking the specific title …
- **Bíráló indoklása:** A modell tévesen állítja, hogy Miklós Radnóti írta a művet, miközben a helyes szerző Magda Szabó.

### HU14 / kínai — bíráló: **helytelen**

- **Kérdés:** 匈牙利童话小说《Tündér Lala》的作者是谁？
- **Várt:** 萨博·玛格达（Szabó Magda）   *(forrás: huwiki, Tündér Lala)*
- **Kapott:** 匈牙利童话小说《Tündér Lala》（《拉拉仙女》）的作者是**阿格尼丝·莫尔纳尔**（**Molnár Ágnes**）。

这部作品是匈牙利当代著名的儿童文学作品，讲述了小女孩拉拉（Lala）与一位仙女之间的奇妙友谊和冒险故事。该书曾获得多项匈牙利儿童文学奖项，并被翻译成多种语言。

需要注意的是，虽然书名中带有“童话”二字，但它通常被归类为**儿童小说**或**奇幻文学**，而非传统意义上的民间童话集。
- **Bíráló indoklása:** A modell által megadott Molnár Ágnes helyett a mű valódi szerzője Szabó Magda, így a válasz ténybeli hiba miatt helytelen.

### HU15 / magyar — bíráló: **helytelen**

- **Kérdés:** Mit rövidít az OKJ a magyar szakképzésben?
- **Várt:** Országos Képzési Jegyzék   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** Az OKJ a Nemzeti Képzési és Gyakorlati Központot jelöli.
- **Bíráló indoklása:** A modell helytelen információt közöl; az OKJ a Magyarországon az Országos Képzési Jegyzéket rövidíti, nem pedig a Nemzeti Képzési és Gyakorlati Központot.

### HU15 / angol — bíráló: **helyes**

- **Kérdés:** What does the abbreviation OKJ stand for in Hungarian vocational training?
- **Várt:** National Training Register (Országos Képzési Jegyzék)   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** **OKJ** stands for **Országos Képzési Jegyzék**, which translates to the **National Register of Training** (or National Training Register).

It is the official list of vocational training programs and qualifications recognized by the Hungarian Ministry of Human Capacities. If a training program is not listed in the OKJ, it cannot be officially recognized as a vocational qualification in Hungary.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, megadja a magyar rövidítés teljes nevét (Országos Képzési Jegyzék) és annak angol megfelelőjét is, amely egyezik a várt válasszal.

### HU15 / kínai — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** 匈牙利职业教育中的缩写OKJ代表什么？
- **Várt:** 国家培训目录（Országos Képzési Jegyzék）   *(forrás: huwiki, Országos Képzési Jegyzék)*
- **Kapott:** 匈牙利职业教育中的缩写OKJ代表“Országos Képzési Jegyzék”，即“国家培训登记册”。

这是一个**正确**的回答。

**详细解释：**

*   **全称**：Országos Képzési Jegyzék
*   **中文含义**：国家培训登记册（或国家课程登记册）
*   **功能**：这是匈牙利教育部维护的一份官方文件，列出了该国所有被认可的职业教育和培训项目。
*   **重要性**：
    *   只有列入OKJ的培训项目才被视为国家认可的职业资格。
*   **相关缩写**：
    *   **OKJ**：Országos Képzési Jegyzék（国家培训登记册）
    *   **OKJ-szám**：OKJ编号（每个培训项目的唯一识别码）
    *   **OKJ-kód**：OKJ代码（用于分类和
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, azaz az OKJ rövidítés teljes nevét (Országos Képzési Jegyzék) és magyar jelentését (Nemzeti Képzési Jegyzék), bár a szöveg a tokenkeret miatt elvágódott.


## ZH csoport

### ZH01 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban tisztelik elsősorban Fazhugong (法主公) népi istenséget?
- **Várt:** Fujian   *(forrás: zhwiki, 法主公)*
- **Kapott:** A) Fujian
B) Guangdong
C) Zhuhai
D) Guangxi

A helyes válasz: **A) Fujian**

**Magyarázat:**
Fazhugong (vagy Fazhugong) a kínai népi vallás egyik fontos istene, aki a halottak védelmezőjeként és a betegségek gyógyításaként is tisztelik. Származása és kultuszának központja a **Fujian** tartomány (különösen a Quanzhou és Putian régiók) volt. Bár a kultusz terjedt más régiókba is (például a taiwani és a maláj közösségekbe), a legmélyebb gyökerei és a legnagyobb tisztelet Fujianban található.

*   **Guangdong** és **Guangxi** más népi istenekhez (példá
- **Bíráló indoklása:** A modell válasza egyértelműen megjelöli a Fujian tartományt, amely a várt helyes válasz.

### ZH01 / angol — bíráló: **helyes**

- **Kérdés:** In which Chinese province is the folk deity Fazhugong (法主公) mainly worshipped?
- **Várt:** Fujian   *(forrás: zhwiki, 法主公)*
- **Kapott:** **Fujian**

Fazhugong (also known as Fa Gong or the "Master of the Dharma") is a folk deity primarily worshipped in the **Fujian** province, particularly in the Fuzhou area. He is often depicted as a Taoist priest and is credited with exorcising demons and protecting the community. His cult is also found in neighboring regions like Taiwan and parts of Southeast Asia due to historical migration from Fujian.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fazhugong főként a Fujian tartományban tisztelt.

### ZH01 / kínai — bíráló: **helyes**

- **Kérdés:** 民间神祇法主公主要在中国哪个省份受到崇拜？
- **Várt:** 福建   *(forrás: zhwiki, 法主公)*
- **Kapott:** 法主公主要在中国福建省受到崇拜。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a法主公主要崇拜于福建省.

### ZH02 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban van Wujiagou (伍家沟村), a népmeséiről ismert falu?
- **Várt:** Hubei   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** Wujiagou falu a **Hunan** tartományban található.

A falu híres a hagyományos népmeséiről és a helyi kultúrájáról. A Hunan tartományban található, amely a középső-középkeleten helyezkedik el. A falu népszerű a turizmus és a kulturális örökség miatt.

Ha további információra van szükséged, kérlek, jelezd! 😊

---
**Megjegyzés:** A válaszban szereplő tartomány (Hunan) helyes, de a falu pontos elhelyezkedése és a népmesék kapcsolata további kutatást igényelhet. A válaszban szereplő információk a rendelkezésre álló adatok alapján készültek.

---
**Kiegészítés:** A falu népszerű a turizmus és a kulturális örökség miatt. A falu népszerű
- **Bíráló indoklása:** A modell tévesen Hunan tartományt jelölte meg, míg a helyes válasz Hubei.

### ZH02 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** In which province is Wujiagou village (伍家沟村), known for its folktales?
- **Várt:** Hubei   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** **Hebei**

Wujiagou Village (伍家沟村) is located in **Hebei** Province, China. It is situated in the Xinglong County (formerly part of the Xinglong County of the Xinglong Autonomous County, now part of the Xinglong County of the Xinglong Autonomous County, Hebei). The village is famous for its folktales, particularly those related to the "Five Families" (Wu Jia) and local legends.

(Note: There may be multiple villages with similar names in China, but the one specifically noted for its folktales in general knowledge contexts is in Hebei.)

**Correction/Refinement:**
Upon double-checking specific folklore databases and geographical records, the most prominent "Wujiagou" associated with specific …
- **Bíráló indoklása:** A modell Hebei tartományt jelölte meg, míg a helyes válasz Hubei; a két tartomány neve hasonló, de földrajzilag és tartalmilag eltérő, így a válasz ténybeli hiba miatt helytelen.

### ZH02 / kínai — bíráló: **helytelen**

- **Kérdés:** 以民间故事闻名的伍家沟村位于哪个省？
- **Várt:** 湖北   *(forrás: zhwiki, 伍家沟村)*
- **Kapott:** 伍家沟村位于**山西省**。

该村隶属于山西省临汾市襄汾县，因流传着关于“伍家沟”的民间传说（如“伍家沟的传说”或相关的民间故事）而闻名，是当地著名的旅游景点之一。
- **Bíráló indoklása:** A modell válasza szerint a伍家沟村 (Wujia Gou) 山西省-ban (Sansi) található, míg a helyes válasz szerint 湖北省-ban (Hubei) van, így a modell téves információt közölt.

### ZH03 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik három állat feje szerepel a quzhou-i „három fej, egy láb” (三头一掌) ételcsoportban?
- **Várt:** kacsa, nyúl, hal   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** A három fej a következő:
1.  **Bivalyfej** (牛头)
2.  **Szarvasfej** (鹿头)
3.  **Szarvasmarhafej** (羊头)

Ez a négyes (három fej + egy láb) a kínai éttermekben gyakran előforduló, különleges fogás. A „három fej, egy láb” kifejezés a kínai éttermekben gyakran a **bivalyfej**, **szarvasfej** és **szarvasmarhafej** kombinációját jelenti, amelyeket gyakran egy **szarvasmarha-láb** (vagy más állat lába) kísér. Ez a fogás a kínai éttermekben gyakran előforduló, különleges fogás.

A kérdésedre a válasz: A három fej a **bivalyfej**, **szarvasfej** és **sz
- **Bíráló indoklása:** A modell által megadott állatok (bivaly, szarvas, szarvasmarha) nem egyeznek a várt helyes válaszokkal (kacsa, nyúl, hal), így a válasz ténybelileg téves.

### ZH03 / angol — bíráló: **helytelen**

- **Kérdés:** Which three animals' heads make up the Quzhou dish group 'three heads, one claw' (三头一掌)?
- **Várt:** duck, rabbit, fish   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** The Quzhou dish group "Three Heads, One Claw" (三头一掌) consists of the heads of the following three animals and the trotter (claw) of a fourth:

1.  **Deer** (鹿头 - Lù tóu)
2.  **Pig** (猪头 - Zhū tóu)
3.  **Goat** (羊头 - Yáng tóu)

The "One Claw" (一掌) refers to the **pig trotter** (猪手 - Zhū shǒu).

So, the three animals are the **deer, pig, and goat**.
- **Bíráló indoklása:** A modell helytelen állításokat közöl: a 'három fej, egy mancs' (三头一掌) quzhoui specialitás valójában kacsa-, hal- és nyúlfőből, valamint disznómancsból áll, nem szarvasból, sertésből és kecskéből.

### ZH03 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, önértékelő toldalék levágva

- **Kérdés:** 衢州“三头一掌”中的“三头”是指哪三种动物的头？
- **Várt:** 鸭头、兔头、鱼头   *(forrás: zhwiki, 三头一掌)*
- **Kapott:** 衢州“三头一掌”中的“三头”是指**牛头、羊头、猪头**这三种动物的头。

“三头一掌”是衢州地区极具代表性的传统美食组合，其中“三头”指的是牛头、羊头、猪头，经过卤制或红烧等烹饪方式处理后，肉质软烂入味，风味独特；“一掌”则是指**鸭掌**，同样经过卤制，口感Q弹有嚼劲。

这道菜不仅是衢州饮食文化的象征，也是当地宴席上的必备佳肴，体现了衢州人对食材的巧妙运用和对传统味道的传承。
- **Bíráló indoklása:** A modell helytelenül azonosította a '三头' (három fej) összetevőit; a várt válasz szerint ez a kacsafej, nyúlfej és halfej, míg a modell marha-, bárány- és sertésfejet említett.

### ZH04 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen lisztből készül a shanxi-i wantuo (碗托)?
- **Várt:** hajdina   *(forrás: zhwiki, 碗托)*
- **Kapott:** A shanxi-i wantuo (碗托) egy hagyományos édes vagy sós étel, amely a Shanxi tartományban, különösen a Taiyuan környékén népszerű. A wantuo alapja a **rizsliszt** vagy **rizskenyér**, amely egy speciális, finomra őrölt rizslisztből készül. A lisztet vízbe keverik, majd egy kis időre állni hagyják, hogy a keményítő teljesen feloldódjon. Ezután a keveréket egy kis edénybe öntik, és forró vízzel vagy gőzzel párolják, amíg meg nem keményedik. A wantuo-t általában sós vagy édes szósszal tálalják, és gyakran kiegészítik zöldségekkel, húsokkal vagy tojással.
A wantuo egy nagyon népszerű étel a Shanxi
- **Bíráló indoklása:** A modell tévesen állítja, hogy rizslisztből készül, míg a helyes válasz hajdinaliszt.

### ZH04 / angol — bíráló: **helytelen**

- **Kérdés:** What flour is Shanxi wantuo (碗托) made from?
- **Várt:** buckwheat   *(forrás: zhwiki, 碗托)*
- **Kapott:** Shanxi wantuo is made from **mung bean flour** (also known as green bean flour).

The flour is mixed with water to create a batter, which is then steamed in a bowl to form the characteristic translucent, jelly-like texture. While some variations in other regions might use cornstarch or wheat flour, the traditional and most authentic version in Shanxi relies on mung bean flour.
- **Bíráló indoklása:** A Shanxi wantuo (碗托) hagyományosan hajdina lisztből készül, nem bablisztből, így a modell válasza ténybeli hiba.

### ZH04 / kínai — bíráló: **helytelen**

- **Kérdés:** 山西碗托主要用什么面粉制作？
- **Várt:** 荞麦面   *(forrás: zhwiki, 碗托)*
- **Kapott:** 山西碗托主要用**绿豆面**制作。
- **Bíráló indoklása:** A modell válasza (绿豆面) eltér a várt helyes választól (荞麦面), így ténybeli hibát tartalmaz.

### ZH05 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Haining, a Xiashi-lampionjairól (硖石灯彩) ismert város?
- **Várt:** Zhejiang   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** Haining a **Zhejiang** tartományban található.

Ez a város híres a hagyományos, kézzel készített, színes üvegcserepes lampionjairól, amelyeket a helyi népi művészetek közé sorolnak.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Haining a Zhejiang tartományban található.

### ZH05 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Haining, the city known for Xiashi lanterns (硖石灯彩)?
- **Várt:** Zhejiang   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** **Zhejiang**

Haining is a county-level city located in the Hangzhou metropolitan area of Zhejiang Province, China. It is famous for its traditional lantern-making craft, known as Xiashi lanterns (硖石灯彩).
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang), és helyesen azonosítja a várost és a lámpás hagyományt.

### ZH05 / kínai — bíráló: **helyes**

- **Kérdés:** 以硖石灯彩闻名的海宁市位于哪个省？
- **Várt:** 浙江   *(forrás: zhwiki, 硖石灯彩)*
- **Kapott:** 海宁市位于**浙江省**。

硖石灯彩是浙江省海宁市硖石镇的传统民间艺术，也是国家级非物质文化遗产之一。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a Haining város a Zhejiang tartományban található.

### ZH06 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik városhoz kötődik Yang Fu Ye (杨府爷) népi istenség tisztelete?
- **Várt:** Wenzhou   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** Yang Fu Ye (杨府爷) népi istenség tisztelete a **Yangzhou** (揚州) városhoz kötődik.

A népi hiedelmek szerint Yang Fu Ye egy helyi hős vagy istenség, aki a város védelmét és jólétét szolgálja. A tiszteletet gyakran a városi templomokban és közösségi ünnepségeken fejezik ki.

Ha további információra van szükséged, kérlek, jelezd! 😊
- **Bíráló indoklása:** A modell helytelenül az Yangzhou városhoz rendeli az istenséget, miközben a helyes válasz Wenzhou.

### ZH06 / angol — bíráló: **helyes**

- **Kérdés:** Which city is the worship of the folk deity Yang Fu Ye (杨府爷) associated with?
- **Várt:** Wenzhou   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** **Wenzhou** (specifically the **Longwan** district) in Zhejiang Province, China.

The deity is most famously worshipped at the **Yangfu Temple** (Yangfu Gong) in the **Longwan** area of Wenzhou, where he is revered as a protector of the city and a folk god of the sea. The worship of Yang Fu Ye is a significant part of the local culture in Wenzhou and the surrounding regions.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Wenzhou), és további, helyes kontextuális információval egészíti ki azt.

### ZH06 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.907)

- **Kérdés:** 民间信仰杨府爷主要流行于哪个城市？
- **Várt:** 温州   *(forrás: zhwiki, 杨府爷)*
- **Kapott:** 民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要生成于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要流行于**宁波**。

民间信仰杨府爷主要
- **Bíráló indoklása:** A modell helytelenül állítja, hogy a kinyitó isten (Yang Fuye) főleg Ningbo-ban honos, míg a várt válasz szerint a terjedési központ Wenzhou.

### ZH07 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik hegyen van Hu Gong Da Di (Hu Ze, 胡则) fő szentélye?
- **Várt:** Fangyan (Yongkang)   *(forrás: zhwiki, 胡则)*
- **Kapott:** Hu Gong Da Di (Hu Ze, 胡则) fő szentélye a **Fenghuang Shan** (Fenhuang-hegy) hegyen található.

A szentély a **Fuzhou** város közelében, a **Fujian** tartományban helyezkedik el. Hu Ze egy híres kínai történelmi személy, aki a Song-dinasztia idején élt, és a helyi népi vallás szerint őt tisztelik a Fenghuang Shan hegyen található szentélyben.

Ha további információra van szükséged, kérlek, jelezd! 😊

---
**Megjegyzés:** A válaszban szereplő "Fenghuang Shan" (Fenhuang-hegy) helyesírása és elhelyezkedése a kínai történelmi és vallási kontextusban fontos. Hu Ze szentélye való
- **Bíráló indoklása:** A modell helytelenül azonosítja a szentély helyét Fenghuang Shan-hegyként, míg a várt helyes válasz Fangyan (Yongkang).

### ZH07 / angol — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** On which mountain is the main shrine of Hu Gong Da Di (Hu Ze, 胡则)?
- **Várt:** Fangyan (Yongkang)   *(forrás: zhwiki, 胡则)*
- **Kapott:** **Mount Wutai** (Wutai Shan)

**Explanation:**
Hu Gong Da Di (Hu Ze) is a revered figure in Chinese folk religion and Taoism, often associated with the "Five Great Gods" (Wu Da Di). While he is sometimes associated with Mount Wutai due to his connection with the region and the Five Great Gods, the specific main shrine dedicated to him is located on **Mount Wutai** in Shanxi Province.

However, it is important to note a potential confusion in the question's premise. Hu Gong Da Di (Hu Ze) is most famously associated with **Mount Wutai** as one of the Five Great Gods, but his specific main shrine is often cited as being on **Mount Wutai** (specifically the **Hu Gong** or **Hu Gong Temple**).

W…
- **Bíráló indoklása:** A modell helytelenül az Wutai-hegyet jelöli meg, míg a várt válasz a Fangyan-hegy (Yongkang).

### ZH07 / kínai — bíráló: **helytelen**

- **Kérdés:** 胡公大帝（胡则）的主庙位于哪座山？
- **Várt:** 方岩   *(forrás: zhwiki, 胡则)*
- **Kapott:** 胡公大帝（胡则）的主庙位于**福州于山**（今福州市鼓楼区于山）。

这座主庙名为**于山胡公庙**（又称“胡公祠”或“胡公大帝庙”）。胡则生前曾任福州知州，他去世后，因其清廉爱民、修筑堤坝、疏浚河道等功绩，深受百姓爱戴，被尊为“胡公大帝”。

于山胡公庙始建于南宋，是福州著名的祈福圣地，尤其以“求子”和“求财”最为灵验，香火极为旺盛。
- **Bíráló indoklása:** A modell helytelenül állítja, hogy a fő templom Fuzhouban található, míg a várt válasz szerint a fő szentély a Jiangxi tartománybeli Wuyi-hegyi Fangyan (方岩) hegyen található.

### ZH08 / magyar — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.511)

- **Kérdés:** Mi a két fő alapanyaga a shaanxi-i zenggao-nak (甑糕)?
- **Várt:** ragacsos rizs, vörös datolya   *(forrás: zhwiki, 甑糕)*
- **Kapott:** A zenggao alapanyai a **rizs** és a **mogyoró**.

A zenggao egy hagyományos kínai édes sütemény, amely a rizst és a mogyorót főzik, majd gőzölik. A rizs általában hosszú szemű, míg a mogyoró finomra őrölt. Az édes ízét gyakran mézzel vagy cukorral adják.

A zenggao egy hagyományos kínai édes sütemény, amely a rizst és a mogyorót főzik, majd gőzölik. A rizs általában hosszú szemű, míg a mogyoró finomra őrölt. Az édes ízét gyakran mézzel vagy cukorral adják.

A zenggao egy hagyományos kínai édes sütemény, amely a rizst és a mogyorót főzik, majd gőzö
- **Bíráló indoklása:** A modell helytelen alapanyagokat (rizs és mogyoró) adott meg, míg a várt válasz ragacsos rizs és vörös datolya, így a ténybeli információ téves.

### ZH08 / angol — bíráló: **helytelen**

- **Kérdés:** What are the two main ingredients of Shaanxi zenggao (甑糕)?
- **Várt:** glutinous rice, red dates (jujube)   *(forrás: zhwiki, 甑糕)*
- **Kapott:** The two main ingredients of Shaanxi zenggao (甑糕) are **glutinous rice** (often soaked and sometimes mixed with red dates) and **mung beans**. These are steamed together in a bamboo steamer until the rice becomes soft and the beans are tender.
- **Bíráló indoklása:** A modell tévesen mung babot (zöld babot) említ fő összetevőként, míg a Shaanxi zenggao hagyományos és fő összetevői a ragacsos rizs és a vörös datolya (jujube).

### ZH08 / kínai — bíráló: **helyes**

- **Kérdés:** 陕西甑糕的两种主要原料是什么？
- **Várt:** 糯米、红枣   *(forrás: zhwiki, 甑糕)*
- **Kapott:** 陕西甑糕的两种主要原料是糯米和红枣。
- **Bíráló indoklása:** A modell válasza pontosan tartalmazza a várt két fő összetevőt (糯米 és 红枣), megegyezve a helyes megoldással.

### ZH09 / magyar — bíráló: **helyes**  ⚠️ csonkolt, ismétlési hurok (0.515)

- **Kérdés:** Melyik tartományban van Linyi, a „sa” (糁) húsleves hazája?
- **Várt:** Shandong   *(forrás: zhwiki, 糁)*
- **Kapott:** A „sa” (糁) húsleves Linyi városában, a **Shandong** tartományban található.

A „sa” (糁) egy hagyományos kínai húsleves, amely Linyi városában, a **Shandong** tartományban található. A leírás szerint a „sa” egy húsleves, amelyben a húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húslevesben lévő húsleves
- **Bíráló indoklása:** A válasz tartalmazza a helyes információt (Shandong tartomány), bár a mondat végén ismétlési hurokba esett, a lényegi kérdés megválaszolása megtörtént.

### ZH09 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Linyi, the home of 'sa' (糁) meat soup?
- **Várt:** Shandong   *(forrás: zhwiki, 糁)*
- **Kapott:** **Shandong**

Linyi is a prefecture-level city located in the southern part of Shandong Province in eastern China. The dish known as "sa" (糁) is a traditional breakfast meat soup that originated in Linyi and is now a signature dish of the city.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Shandong), és helyesen azonosítja a tartományt, ahol Linyi található.

### ZH09 / kínai — bíráló: **helyes**

- **Kérdés:** 以“糁”汤闻名的临沂市位于哪个省？
- **Várt:** 山东   *(forrás: zhwiki, 糁)*
- **Kapott:** 临沂市位于**山东省**。

“糁”（sǎn）是临沂著名的传统小吃，以牛肉、牛骨熬制的高汤为底，加入面粉、姜丝、胡椒等调料，味道鲜美，是当地极具代表性的美食。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Linyi város a Shandong tartományban található.

### ZH10 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik ünnephez kötődik Taizhou-ban a shibingtong (食饼筒) fogyasztása?
- **Várt:** Duanwu (sárkányhajó-ünnep)   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** A shibingtong fogyasztása a Taizhou-beli **Nagy Éves Ünnephez** (春分, Chūnfēn) vagy a **Tavaszi Félidő** (春分, Chūnfēn) ünnepéhez kötődik.

A shibingtong egy hagyományos ételek, amelyeket Taizhou-ban (Zhejiang tartományban) fogyasztanak a **Tavaszi Félidő** (春分, Chūnfēn) ünnepén. Ez az ünnep a tavasz közepét jelöli, és a shibingtong egyfajta "tavaszi tortát" vagy "tavaszi tekercset" jelent, amelyben a tészta lapot töltelékkel (pl. zöldségek, hús, tojás) töltik meg, majd tekercsbe csavar
- **Bíráló indoklása:** A modell helytelenül a Chunfen (Tavaszi Félidő) ünnephez köti az ételt, míg a helyes válasz a Duanwu (Sárkányhajó-ünnep).

### ZH10 / angol — bíráló: **helytelen**

- **Kérdés:** With which festival is eating shibingtong (食饼筒) associated in Taizhou?
- **Várt:** Duanwu (Dragon Boat Festival)   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** Answer: The **Spring Festival** (Chinese New Year).

**Shibingtong** (also known as *Shibingjun* or "Spring Festival Rolls") is a traditional food in Taizhou, Zhejiang, specifically associated with the **Spring Festival** (Lunar New Year). It is believed to symbolize "eating the whole year" (eating the whole roll) and represents a wish for a complete and prosperous year ahead. It is traditionally eaten on New Year's Eve or the first day of the Lunar New Year.
- **Bíráló indoklása:** A modell tévesen állítja, hogy a shibingtong a Tavaszünnephez (Spring Festival) kapcsolódik, míg a helyes válasz a Duanwu (Hajóverseny Ünnep) festival.

### ZH10 / kínai — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** 台州人在哪个节日吃食饼筒？
- **Várt:** 端午节   *(forrás: zhwiki, 食饼筒)*
- **Kapott:** 台州人在**春节**期间吃食饼筒。

台州人把食饼筒称为“春卷”，但和北方或江南的春卷不同，台州食饼筒是一种**卷**起来吃的食物，里面包有各种食材，如豆腐干、肉丝、青菜、豆芽、粉丝等，口感丰富，是台州春节期间的传统美食。

此外，台州人也有在**元宵节**吃食饼筒的习俗，但**春节**是最主要的食用时间。

---

**补充说明：**
- 食饼筒是台州地区特有的传统小吃，尤其在临海、温岭等地非常流行。
- 制作食饼筒时，通常用一张薄饼皮，将各种炒好的馅料卷入其中，然后可以生吃或煎熟后吃。
- 台州人认为吃食饼筒象征着“包罗万象”，寓意新的一年生活富足、万事顺遂。

---

**总结：**
台州人主要在
- **Bíráló indoklása:** A modell tévesen állítja, hogy a fő ünnep a tavaszi ünnep (春节), míg a várt helyes válasz az Üveghegyi ünnep (端午节).

### ZH11 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik tartományban van Gengcun (耿村), a népmeséiről ismert falu?
- **Várt:** Hebei   *(forrás: baike, 耿村民间故事)*
- **Kapott:** Gengcun a **Hunan** tartományban található.

A falu a Hunan tartományi **Hengyang** város **Hengnan** megyéjében helyezkedik el. A falu híres a hagyományos népmeséiről és a helyi kultúrájáról.

---

**Forrás:**
- [Gengcun, Hengnan, Hunan](https://en.wikipedia.org/wiki/Gengcun,_Hengnan,_Hunan) (Wikipedia)
- [Hengnan County](https://en.wikipedia.org/wiki/Hengnan_County) (Wikipedia)
- [Hunan Province](https://en.wikipedia.org/wiki/Hunan_Province) (Wikipedia)

Ha további információra van szükséged, kérlek, jelezd! 😊
- **Bíráló indoklása:** A modell tévesen Hunan tartományba helyezi Gengcun-t, míg a helyes válasz Hebei.

### ZH11 / angol — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** In which province is Gengcun (耿村), the village known for its folktales?
- **Várt:** Hebei   *(forrás: baike, 耿村民间故事)*
- **Kapott:** **Hebei**

Gengcun (耿村) is a village located in **Hebei** Province, China. It is situated in the city of Xingtai (Xingtai City), specifically in the Xiang County (Xiang County, Xingtai). The village is famous for the "Gengcun Folktales" (耿村民间故事), which were included in the National Intangible Cultural Heritage list. The most well-known story associated with the village is "The Legend of the Geng Family" (耿氏传说), which tells the story of the Geng family's migration and their contributions to the region.

The village is also known for its unique "Gengcun Stone Carving" (耿村石雕) and its traditional folk customs. The Gengcun Folktales are a significant part of the local cultural heritage and have b…
- **Bíráló indoklása:** A modell válasza egyértelműen megnevezi a helyes tartományt (Hebei), bár a válasz elvágódott a végén, a lényegi információ már megvolt.

### ZH11 / kínai — bíráló: **helytelen**

- **Kérdés:** 以民间故事闻名的耿村位于哪个省？
- **Várt:** 河北   *(forrás: baike, 耿村民间故事)*
- **Kapott:** 耿村位于**山东省**。

该村位于山东省临沂市费县，因明代著名清官、戏曲人物**耿直**（或称耿直公）而得名，是著名的“耿直村”。这里流传着许多关于耿直公的民间故事，如《耿直公断案》等，在当地乃至全国都颇具知名度。
- **Bíráló indoklása:** A modell válasza szerint a耿村 (Gengcun) Shandong tartományban található, míg a helyes válasz Hebei tartomány, így a modell téves információt közölt.

### ZH12 / magyar — bíráló: **helytelen**

- **Kérdés:** Melyik nagyvároshoz tartozik Zouma (走马镇), a népmeséiről ismert település?
- **Várt:** Chongqing   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** Zouma a **Huanghua** (黄骅) városához tartozik.

A település Hebei tartományban található, és híres a hagyományos népmeséiről, amelyek a helyi kultúra fontos részét képezik. A város központi szerepet tölt be a régió gazdasági és kulturális életében.

---
- **Bíráló indoklása:** A válaszban szereplő Huanghua város Hebei tartományban található, míg a népmeséiről ismert Zouma (走马镇) Chongqinghez tartozik, így a modell téves információt közölt.

### ZH12 / angol — bíráló: **helyes**

- **Kérdés:** Which major city does Zouma town (走马镇), known for its folktales, belong to?
- **Várt:** Chongqing   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** **Chongqing** (specifically, it is a town in the Wanzhou District of Chongqing Municipality).

*Note: There is also a Zouma Town in the Yichun District of Chongqing, but the one most famously associated with folktales and the "Zouma" (Horse Running) legend is typically the one in Wanzhou.*

**Answer:** Chongqing
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a Zouma town a Chongqinghez tartozik.

### ZH12 / kínai — bíráló: **helyes**

- **Kérdés:** 以民间故事闻名的走马镇属于哪个直辖市？
- **Várt:** 重庆   *(forrás: baike, 走马镇民间故事)*
- **Kapott:** 走马镇属于**重庆市**。

它位于重庆市渝北区西部，因“走马观花”的典故和独特的古镇风貌而闻名，是重庆著名的旅游胜地之一。
- **Bíráló indoklása:** A modell helyesen azonosította, hogy a kérdésben szereplő走马镇 (Zouma Town) a Chongqinghez tartozik, ami megegyezik a várt válasszal.

### ZH13 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Shengzhou, a hagyományos Shengzhou-i xiaolongbao (嵊州小笼包) hazája?
- **Várt:** Zhejiang   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** A Shengzhou (嵊州) város a **Zhejiang** tartományban található Kínában.

Ez a város híres a hagyományos, finomabb tésztájú és kevésbé zsíros xiaolongbao-iról, amelyek eltérnek a Shanghai-i változattól.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Shengzhou a Zhejiang tartományban található.

### ZH13 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Shengzhou, home of the traditional Shengzhou xiaolongbao (嵊州小笼包)?
- **Várt:** Zhejiang   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** **Zhejiang**

Shengzhou is a county-level city located in the Shaoxing prefecture of Zhejiang Province, China. It is famous for its *Shengzhou xiaolongbao*, which are distinct from the more well-known Shanghai xiaolongbao because they are typically steamed rather than boiled and have a slightly different filling and dough texture.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang), és helyesen azonosítja a tartományt.

### ZH13 / kínai — bíráló: **helyes**

- **Kérdés:** 嵊州小笼包的发源地嵊州位于哪个省？
- **Várt:** 浙江   *(forrás: baike, 嵊州小笼包)*
- **Kapott:** 嵊州小笼包的发源地嵊州位于浙江省。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a helyszín Zhejiang tartományban található.

### ZH14 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik ókori szépségről nevezték el a zhuji-i tofu-levest (西施豆腐)?
- **Várt:** Xi Shi   *(forrás: baike, 西施豆腐)*
- **Kapott:** A zhuji-i tofu-levest a kínai szépség, a **Zhuji-i Zsusi** (西施) nevéről nevezték el.

A történet szerint a kínaiak szerint a Zsusi szépsége olyan volt, hogy a víz is széppé vált, ha tükörképe látszott benne. A zhuji-i tofu-levest a Zsusi nevéről nevezték el, mert a tofu és a leves íze olyan finom és puha, mint a Zsusi arca.

A zhuji-i tofu-levest a **Zhuji** (西施) nevéről nevezték el, amely a **Zhuji** (西施) nevű városban található. A zhuji-i tofu-levest a **Zhuji** (西施) nevű városban található.

A zhuji-i tofu-levest
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Xi Shi / Zsusi), bár a megfogalmazás és a kínai karakterek helyes használata hibás, a lényegi tény helyes.

### ZH14 / angol — bíráló: **helyes**

- **Kérdés:** After which ancient beauty is the Zhuji tofu soup (西施豆腐) named?
- **Várt:** Xi Shi   *(forrás: baike, 西施豆腐)*
- **Kapott:** **Xi Shi** (also known as Xishi), the legendary beauty of ancient China.

The dish is named after her because the legend states that she used this tofu soup to wash her face, and the steam from the soup was said to have made her skin even more beautiful. The name "Xi Shi Tofu" literally translates to "Xi Shi's Tofu."
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Xi Shi), bár a magyarázatban szereplő legenda részletei (mosakodás a gőzzel) eltérnek a szokásos történetektől, a névadás alapja (Xi Shi) helyes.

### ZH14 / kínai — bíráló: **helyes**

- **Kérdés:** 诸暨的西施豆腐是以哪位古代美女命名的？
- **Várt:** 西施   *(forrás: baike, 西施豆腐)*
- **Kapott:** 诸暨的西施豆腐是以古代美女西施命名的。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint a tányér nevét a történelmi személyiség, Xi Shi (西施) után nevezték el.

### ZH15 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik tartományban van Yongkang, a hússal töltött lepényéről (永康肉麦饼) ismert város?
- **Várt:** Zhejiang   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** Yongkang a **Zhejiang** tartományban található.

Ez a város híres a helyi kulináris hagyományairól, különösen a hússal töltött lepényéről, amely a Zhejiangi konyha egyik jellegzetessége. Yongkang a Jangce deltájának északi részén, a Hangzhou közelében helyezkedik el.

Ha szeretnéd, további információkat is megoszthatok a városról vagy a lepényről! 😊
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Yongkang a Zhejiang tartományban található.

### ZH15 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Yongkang, known for its meat-filled wheat cake (永康肉麦饼)?
- **Várt:** Zhejiang   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** **Zhejiang**

Yongkang is a county-level city located in the Jinhua prefecture of Zhejiang Province, China. It is famous for its traditional food, the Yongkang meat-filled wheat cake (肉麦饼).
- **Bíráló indoklása:** A modell válasza tartalmazza a helyes információt, miszerint Yongkang a Zhejiang tartományban található.

### ZH15 / kínai — bíráló: **helyes**

- **Kérdés:** 以肉麦饼闻名的永康市位于哪个省？
- **Várt:** 浙江   *(forrás: baike, 永康肉麦饼)*
- **Kapott:** 永康市位于**浙江省**。

它是浙江省金华市代管的县级市，以制作“肉麦饼”（又称麦饼）而闻名，该小吃是永康的传统美食。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint永康市 (Yongkang) Zhejiang tartományban található.

### ZH16 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Melyik tartományban van Fuyang, a gelatiao (格拉条) tésztáról ismert város?
- **Várt:** Anhui   *(forrás: baike, 格拉条)*
- **Kapott:** Fuyang a **Hunan** tartományban található.

---

**Magyarázat:**
A **gelatiao** (格拉条) egy népszerű kínai tésztafajta, amelynek neve a „hosszú tészta” (gelatiao) jelentéséből ered. Bár a gelatiao eredetileg a **Hunan** tartományból származik, a város, amely leginkább ismert ezzel a tésztával, a **Fuyang** (阜阳), amely a **Anhui** tartományban található.

**Fontos megjegyzés:**
A kérdésben szereplő város, Fuyang, valójában az **Anhui** tartományban van, nem a Hunanban. A gelatiao tészta népszerű az egész Kínában, de a Fuyang-i verzió különösen híres.

**H
- **Bíráló indoklása:** A modell válasza kezdetben helytelenül állítja, hogy Fuyang Hunanban található, bár a magyarázatban később javítja ezt, a közvetlen válasz téves.

### ZH16 / angol — bíráló: **helyes**

- **Kérdés:** In which province is Fuyang, the city known for gelatiao (格拉条) noodles?
- **Várt:** Anhui   *(forrás: baike, 格拉条)*
- **Kapott:** **Anhui**

Fuyang is a prefecture-level city located in the northwestern part of **Anhui** province in eastern China. It is famous for its *gelatiao* (also known as *gelatiao* or "glue noodles"), a local specialty consisting of thick, chewy noodles served in a spicy broth.
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Anhui), és helyesen azonosítja a tartományt, bár a tésztafajta leírásában van egy apró pontatlanság (a név ismétlése), ami nem befolyásolja a fő kérdés helyes megválaszolását.

### ZH16 / kínai — bíráló: **helyes**

- **Kérdés:** 以格拉条闻名的阜阳市位于哪个省？
- **Várt:** 安徽   *(forrás: baike, 格拉条)*
- **Kapott:** 阜阳市位于**安徽省**。

格拉条是阜阳地区极具代表性的传统小吃，以其独特的“辣、香、麻、鲜”口感而闻名，是当地饮食文化的重要标志。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, miszerint Fuyang az Anhui tartományban található.

### ZH17 / magyar — bíráló: **helytelen**  ⚠️ csonkolt

- **Kérdés:** Milyen virágból alakul át sárkánnyá a Changxing-i százlevelű sárkánytánc (百叶龙) kelléke?
- **Várt:** lótusz   *(forrás: baike, 百叶龙)*
- **Kapott:** A **lilium** (liliom) virágból alakul át sárkánnyá.

A **Changxing-i százlevelű sárkánytánc** (百叶龙) egy hagyományos kínai tánc, amely a **lilium** (liliom) virágból alakul át sárkánnyá. A tánc során a liliom virágokból sárkányok alakulnak ki, amelyek a vízben úsznak, és a sárkányok a vízben úsznak. A tánc során a liliom virágokból sárkányok alakulnak ki, amelyek a vízben úsznak, és a sárkányok a vízben úsznak.

A tánc során a liliom virágokból sárkányok alakulnak ki, amelyek a vízben úsznak, és
- **Bíráló indoklása:** A modell a liliumot (liliom) jelölte meg helyettük a várt lótuszvirágnak, ami ténybeli hiba.

### ZH17 / angol — bíráló: **helyes**

- **Kérdés:** From which flower does the prop in the Changxing 'hundred-leaf dragon' dance (百叶龙) transform into a dragon?
- **Várt:** lotus   *(forrás: baike, 百叶龙)*
- **Kapott:** **Lotus** (or **Water Lily**)

**Explanation:**
The Changxing "Hundred-Leaf Dragon" (百叶龙) is a unique folk dance from Changxing County, Zhejiang Province, China. The dragon is constructed from hundreds of lotus leaves (or sometimes lotus flowers) that are attached to a bamboo frame. During the performance, the dancers manipulate the frame so that the lotus leaves unfurl and wave, creating the illusion of a dragon's scales and body moving through the air. The dragon is often said to be "born" from the lotus.
- **Bíráló indoklása:** A modell helyesen azonosította a lótuszként (lotus) megadott várt választ, és a magyarázat is helyes.

### ZH17 / kínai — bíráló: **helytelen**  ⚠️ csonkolt, ismétlési hurok (0.875)

- **Kérdés:** 长兴百叶龙表演中，龙是由什么花变化而来的？
- **Várt:** 荷花   *(forrás: baike, 百叶龙)*
- **Kapott:** 长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百回答：在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。

在长兴百叶龙表演中，龙是由**菊花**变化而来的。
- **Bíráló indoklása:** A modell helytelenül állítja, hogy a hosszúxi bái long (százlevelű sárkány) a kankalinból (vagy más források szerint lótuszból, de a várt válasz a lótusz/荷花) származik, míg a modell a krizantémot (菊花) említi, ami ténybeli hiba.

### ZH18 / magyar — bíráló: **helyes**

- **Kérdés:** Melyik évszakban tartják a Wuzhen-i tömjénvásárt (乌镇香市)?
- **Várt:** tavasz   *(forrás: baike, 乌镇香市)*
- **Kapott:** A Wuzhen-i tömjénvásárt a tavaszi évszakban tartják.
- **Bíráló indoklása:** A modell válasza megegyezik a várt 'tavasz' információval.

### ZH18 / angol — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** In which season is the Wuzhen incense fair (乌镇香市) held?
- **Várt:** spring   *(forrás: baike, 乌镇香市)*
- **Kapott:** **Spring**

The Wuzhen Incense Fair is traditionally held in the spring, typically around the **Lantern Festival** (usually in February or March). It is a historic event that originated in the late Qing Dynasty and early Republic of China era, where merchants from various regions would gather in Wuzhen to trade incense and other goods. While the modern version of the fair is often held in **October** (during the autumn) to coincide with the Wuzhen International Film Festival, the traditional "Incense Fair" is historically associated with the spring season.

*Note: If referring to the specific modern event known as the "Wuzhen Incense Fair" organized by the Wuzhen Tourism Development Co., Ltd…
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (tavasz/spring), bár a modern események kapcsán zavaró kiegészítést is tesz, a történelmi kontextusban a helyes évszakot megadja.

### ZH18 / kínai — bíráló: **helyes**

- **Kérdés:** 乌镇香市在哪个季节举行？
- **Várt:** 春季   *(forrás: baike, 乌镇香市)*
- **Kapott:** 乌镇香市在春季举行。
- **Bíráló indoklása:** A modell válasza megerősíti, hogy az esemény tavasszal (春季) zajlik, ami egyezik a várt válasszal.

### ZH19 / magyar — bíráló: **helyes**  ⚠️ csonkolt

- **Kérdés:** Melyik tartomány rizsföldjein énekelték a Jiashan-i földdalokat (嘉善田歌)?
- **Várt:** Zhejiang   *(forrás: baike, 嘉善田歌)*
- **Kapott:** A Jiashan-i földdalokat a **Zhejiang** tartomány rizsföldjein énekelték.

A dalok a **Jiashan** (嘉善) megye környékén, a **Jiangsu** és **Zhejiang** határvidékén, a **Yangtze** folyó deltájában terjedtek el. A Jiashan-i földdalok a **2006-ban** felvett **nemzeti szellemi örökség** részei, és a **rizsföldi munka** során énekelték őket. A dalok **széles körben** ismertek a **Jiangsu** és **Zhejiang** tartományokban, és a **rizsföldi munka** során énekelték őket.

A **Jiashan-i földdalok** a **rizsföldi munka** során énekelték őket, és
- **Bíráló indoklása:** A modell válasza tartalmazza a helyes információt, miszerint a Jiashan-i földdalokat a Zhejiang tartomány rizsföldjein énekelték, bár a válasz végén elvágódott.

### ZH19 / angol — bíráló: **helyes**

- **Kérdés:** In the rice fields of which province were the Jiashan field songs (嘉善田歌) sung?
- **Várt:** Zhejiang   *(forrás: baike, 嘉善田歌)*
- **Kapott:** **Zhejiang** (specifically in the Jiashan County of Jiaxing City).
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt, Zhejiang tartományt jelölve, és pontosítja, hogy Jiashan megyében hangzottak el.

### ZH19 / kínai — bíráló: **helyes**

- **Kérdés:** 嘉善田歌流行于哪个省的稻田地区？
- **Várt:** 浙江   *(forrás: baike, 嘉善田歌)*
- **Kapott:** 嘉善田歌流行于浙江省的稻田地区。
- **Bíráló indoklása:** A modell válasza tartalmazza a várt információt (Zhejiang tartomány), és helyesen azonosítja a földrajzi elterjedést.

