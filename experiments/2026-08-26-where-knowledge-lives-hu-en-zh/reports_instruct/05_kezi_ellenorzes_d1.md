# Kézi ellenőrző ív — D1 (48 UNT-válasz)

Komponensenként látod a bíráló döntését. Ahol egyetértesz, nincs teendő; ahol nem, add meg a
`code/set_manual.py`-nak a HELYES darabszámot:
`python3 code/set_manual.py d <item> <nyelv> --native N --distortion M`,
majd `python3 code/analyze_d.py`.

⛔ A `d1_scores.csv`-t **ne szerkeszd kézzel** — a 08-24-i körben így csúszott el az
UNT-ZH08 `native_n` nevezője. A felvitel a `set_manual.py`-n megy; a parancsok alább,
a bíráló darabszámaival előkitöltve.

```bash
python3 code/set_manual.py d UNT-HU01  hu --native 1 --distortion 1
python3 code/set_manual.py d UNT-HU01  en --native 1 --distortion 0
python3 code/set_manual.py d UNT-HU01  zh --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU02  hu --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU02  en --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU02  zh --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU03  hu --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU03  en --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU03  zh --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU04  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU04  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU04  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU05  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU05  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU05  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU06  hu --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU06  en --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU06  zh --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU07  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU07  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU07  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU08  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU08  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU08  zh --native 0 --distortion 2
python3 code/set_manual.py d UNT-ZH01  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH01  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH01  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH02  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH02  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH02  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH03  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH03  en --native 3 --distortion 1
python3 code/set_manual.py d UNT-ZH03  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH04  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH04  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH04  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH05  hu --native 3 --distortion 1
python3 code/set_manual.py d UNT-ZH05  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH05  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH06  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH06  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH06  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH07  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH07  en --native 3 --distortion 1
python3 code/set_manual.py d UNT-ZH07  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH08  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH08  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH08  zh --native 3 --distortion 0
```


## kaláka (forrásnyelv: hu) — angol közelítés: *mutual aid / barn raising / helping out*

### magyar

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [x] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [x] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [ ] *distortion 2:* 'volunteering'/'charity' keretezés

> A **kaláka** szó a magyar nyelvben egy nagyon gazdag jelentésű kifejezés, amely eredetileg a közösségi életből származik, de ma már számos átvitt értelemben is használjuk.

Íme a szó legfontosabb jelentései:

1.  **Közös erőfeszítés vagy cselekvés**: Ez a leggyakoribb jelentése. Olyan közös tevékenységet jelöl, amelyet több ember végez együtt, gyakran önzetlenül vagy segítőkészségből.
    *   *Példa*: „A szomszédok **kalákáztak**, hogy felépítsék a tornatermet." (Itt a közös munka a lényeg).

2.  **Közös pénzbeli hozzájárulás**: Korábban (és néha ma is) arra utalt, hogy a közösség tagjai összeadnak egy kis összeget egy közös célra (pl. egy beteg megsegítésére, egy esküvőre, vagy egy eszköz megvásárlására).
    *   *Példa*: „Egy **kalákából** vettük meg a karácsonyi ajándékot."

3.  **Közös

*Bíráló indoklása:* A válasz hiányolja a kölcsönös viszonozás és a fizetség nélküli de elvárt visszasegítés lényegi elemét, miközben az önkéntes jótett keretezésével torzítja a fogalmat.

### angol

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [x] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [ ] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [ ] *distortion 2:* 'volunteering'/'charity' keretezés

> The Hungarian word **kaláka** (pronounced roughly like *kah-lah-kah*) is a noun that refers to a **group of people**, specifically a band, troupe, or company of performers, musicians, or actors who travel together and perform in various places.

Historically, it described traveling folk troupes (often called *kaláka* or *kalaposok*) that would go from village to village during the winter months to sing, dance, and play music for food, drink, and lodging. Over time, the meaning has broadened slightly to refer to any traveling group of performers or even a collective of people working together in a similar itinerant fashion.

In modern usage, you might encounter it in contexts like:
*   A traveling folk music group.
*   A theatrical troupe.
*   Metaphorically, a group of friends or colleague

*Bíráló indoklása:* A modell a 'kaláka' szót tévesen 'utazó előadócsoportként' definiálta, így hiányzik a kölcsönös segítségnyújtás és a fizetség nélküli, de elvárt visszasegítés lényegi eleme, bár a közösségi jelleg megmaradt.

### kínai  ⚠️ ismétlési hurok

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [ ] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [x] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [x] *distortion 2:* 'volunteering'/'charity' keretezés

> 匈牙利语中的 **"kaláka"** 一词主要指**集体储蓄**、**凑份子**或**共同集资**。

这个词源于古老的匈牙利民间传统，指的是社区成员为了某个共同目标（如举办婚礼、葬礼、建造房屋、购买牲畜或应对紧急情况）而自愿凑钱或凑物。这种互助形式在历史上是匈牙利农村社会生活的重要组成部分，体现了邻里之间的团结和互助精神。

在现代语境中，"kaláka"的含义有所演变，通常指：
1.  **凑钱活动**：一群人为了特定目的共同出资。
2.  **储蓄罐/钱箱**：有时也指用来存放这些集体资金的容器或账户。
3.  **泛指积蓄**：偶尔也可泛指个人的积蓄，但这不如前两个含义常见。

**词源小知识**：
该词可能源自突厥语族（如鞑靼语中的 *qalqa*，意为“钱”或“财富”），反映了匈牙利语中保留的许多古突厥语借词。

**例句**：
*   *A menyasszonyi kalákát már meggyűjtötték.* (新娘的凑份子钱已经凑齐了。)
*   *Ez egy kaláka, amit a falu közös használatára gyűjtünk.* (这是一个为了村庄共同使用而筹集的基金。)

总结来说，**kaláka** 最核心的意思就是**大家凑钱办大事**的集体储蓄行为。

*Bíráló indoklása:* A modell a 'kaláka' szót kizárólag pénzügyi gyűjtésként (kolektív spórolás) értelmezi, így teljesen hiányoznak belőle a fizikai munkavégzésre, kölcsönös segítségre és szervezett közösségi munkára vonatkozó jelentéskomponensek, miközben a 'volunteering' (önkéntesség) és a pénzgyűjtés keretezése torzí


## szeretet / szerelem (forrásnyelv: hu) — angol közelítés: *love*

### magyar  ⚠️ csonkolt

- [x] **native 1:** két külön szó: szeretet (tág, nem erotikus) és szerelem (romantikus, párkapcsolati)
- [x] **native 2:** a szerelem a szeretet egy fajtája, de nem fordítva
- [ ] *distortion 1:* a kettő összemosása egyetlen 'love'-ként
- [ ] *distortion 2:* nem említi, hogy a magyar megkülönbözteti

> Bár a **szeretet** és a **szerelem** szavak gyakran cserélhetők használatban, különösen a romantikus kontextusban, a magyar nyelvben és kultúrában közöttük finnek, de jelentős különbségek húzódnak meg a jelentésben, a hangsúlyban és a felhasználási területekben.

Íme a legfontosabb különbségek részletesen:

### 1. A jelentés mélysége és terjedelme
*   **Szeretet:** Ez egy **általánosabb, tágabb fogalom**. Leírja az érzelmek teljes spektrumát, amelyeket egy másik iránt érezhetünk. A szeretet alapja az elfogadás, a gondoskodás és a jókívánság.
    *   *Példák:* Szeretjük a családot, a barátainkat, az állatokat, az országot, az életet, vagy akár egy művet is.
    *   *Jelleg:* Stabil, cselekvésen alapuló érzés, amely idővel alakulhat ki.
*   **Szerelem:** Ez a szeretet **intenzívebb, felforró

*Bíráló indoklása:* A válasz egyértelműen megkülönbözteti a tágabb szeretet és a romantikus szerelem fogalmát, valamint helyesen állítja, hogy a szerelem a szeretet egy fajtája, miközben elkerüli az összemosást.

### angol

- [x] **native 1:** két külön szó: szeretet (tág, nem erotikus) és szerelem (romantikus, párkapcsolati)
- [x] **native 2:** a szerelem a szeretet egy fajtája, de nem fordítva
- [ ] *distortion 1:* a kettő összemosása egyetlen 'love'-ként
- [ ] *distortion 2:* nem említi, hogy a magyar megkülönbözteti

> While both **szeretet** and **szerelem** translate to "love" in English, they represent two distinct dimensions of the concept in Hungarian culture and language. The difference lies primarily in the **nature** of the feeling, its **scope**, and its **intensity**.

### 1. Szeretet: Unconditional, Broad, and Nurturing
**Szeretet** refers to a deep, warm, and often unconditional affection. It is the love found in family bonds, friendship, and general kindness toward humanity.
*   **Characteristics**: It is calm, steady, selfless, and enduring. It does not necessarily require passion or romance.
*   **Context**: You use this word for your parents, children, siblings, close friends, pets, and even strangers (e.g., *emberi szeretet* = human love/kindness).
*   **Nuance**: It implies a willingnes

*Bíráló indoklása:* A válasz egyértelműen megkülönbözteti a két fogalmat a tág, nem erotikus szeretet és a romantikus szerelem között, valamint helyesen állítja, hogy a szerelem a szeretet egy fajtája, miközben elkerüli az összemosást.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** két külön szó: szeretet (tág, nem erotikus) és szerelem (romantikus, párkapcsolati)
- [x] **native 2:** a szerelem a szeretet egy fajtája, de nem fordítva
- [ ] *distortion 1:* a kettő összemosása egyetlen 'love'-ként
- [ ] *distortion 2:* nem említi, hogy a magyar megkülönbözteti

> 在匈牙利语中，**szeretet** 和 **szerelem** 虽然都涉及“爱”的概念，但它们的侧重点、情感强度和使用语境有显著区别。简单来说，**szerelem** 通常指激情、浪漫或强烈的爱，而 **szeretet** 则指深沉、无私且持久的爱。

以下是具体的对比分析：

### 1. 核心含义与情感色彩

*   **Szerelem (浪漫之爱 / 激情之爱)**
    *   **侧重点**：强调情感的**强度**、激情、渴望、迷恋以及浪漫关系中的吸引力。它往往包含一种“想要占有”或“心跳加速”的感觉。
    *   **对应概念**：类似于英语中的 *passion*, *romantic love*, *infatuation* 或 *lust*（在更强烈的语境下）。
    *   **常见搭配**：
        *   *Szerelem elsőre* (一见钟情)
        *   *Szerelemgyónás* (忏悔罪过，指因失恋或情感受挫而痛苦)
        *   *Szerelemgyilkos* (情杀犯)
    *   **例句**：
        > *A **szerelem** meggyőzhetetlen.* (爱情是不可战胜的/坚不可摧的。)
        > *Szerelmes vagyok.* (我坠入爱河了/我恋爱了。)

*   **Szeretet (慈爱 / 博爱 / 深情)**
    *   **侧重点**：强调爱的**深度**、无私性、关怀、接纳和持久性。它不依赖于激情或性吸引力，而是一种愿意为对方付出、包容和守护的情感。这种爱存在于父母与子女、朋友之间，也存在于成熟的伴侣关系中。
    *   **对应概念**：类似于英语中的 *affection*, *care*

*Bíráló indoklása:* A válasz részletesen megkülönbözteti a két fogalmat, helyesen azonosítva a szeretet tágabb, nem erotikus jellegét és a szerelem romantikus, intenzív természetét, valamint nem mosza össze őket egyetlen fogalommá.


## magázás / tegezés (forrásnyelv: hu) — angol közelítés: *formal vs informal 'you' (T–V distinction)*

### magyar  ⚠️ csonkolt

- [x] **native 1:** igealakban és névmásban is megjelenik (ön/maga vs te)
- [ ] **native 2:** több fokozat: tegezés, magázás, önözés (és tetszikelés)
- [x] **native 3:** társadalmi távolság / tisztelet kódolása
- [ ] *distortion 1:* csak 'polite you' mint a francia vous — egyszintű
- [ ] *distortion 2:* csak névmás-különbségként írja le, az igeragozást nem említi

> A **magázás** és a **tegezés** a magyar nyelvben a személyek közötti viszonyokat, távolságot és a hierarchiát jelző két alapvető megszólítási mód. Ezek a formák nem csupán nyelvtani szabályok, hanem mélyen gyökerező társadalmi kódok, amelyekkel azonnal jelezhetjük, hogyan viszonyulunk egymáshoz.

Íme a részletes magyarázat:

### 1. Magázás
A magázás a **tiszteletteljes, udvarias és távolságtartó** megszólítás módja.
*   **Kinek használjuk?** Főleg idősebbekkel, felsőbbrendűbbekkel (főnökökkel, tanárokkal, hivatalos személyekkel), ismeretlenekkel, vagy olyan emberekkel, akiket tiszteletben tartunk.
*   **Milyen hatást kelt?** Jelezi a tiszteletet, a komolyságot és a határozott távolságot. Ha valakit „magázunk", azt üzenjük, hogy nem vagyunk egyenrangúak vele, vagy legalábbis nem akarunk túl

*Bíráló indoklása:* A válasz tartalmazza az igealakok és névmások használatát, valamint a társadalmi távolság kódolását, de hiányzik a többfokozatú rendszer (önözés/tetszikelés) említése, és nem torzítja a fogalmat egyszintűvé vagy kizárólag névmás-különbséggé.

### angol

- [x] **native 1:** igealakban és névmásban is megjelenik (ön/maga vs te)
- [ ] **native 2:** több fokozat: tegezés, magázás, önözés (és tetszikelés)
- [x] **native 3:** társadalmi távolság / tisztelet kódolása
- [ ] *distortion 1:* csak 'polite you' mint a francia vous — egyszintű
- [ ] *distortion 2:* csak névmás-különbségként írja le, az igeragozást nem említi

> In Hungarian, both **magázás** and **tegezés** refer to the way people address each other using different pronouns, which is a significant marker of social hierarchy, intimacy, and respect in Hungarian culture.

Here is the breakdown of each term:

### 1. Magázás
*   **Meaning**: This refers to the act of using the formal second-person singular pronoun **"Ön"** (or sometimes "Maga") and its corresponding verb conjugations.
*   **Context**: It is used in formal situations, with strangers, superiors, elders, or in professional settings to show **respect, distance, or politeness**.
*   **Example**: *Üdvözli Önt?* (May I welcome you? / How do you do?)

### 2. Tegezés
*   **Meaning**: This refers to the act of using the informal second-person singular pronoun **"te"** and its corresponding verb

*Bíráló indoklása:* A válasz helyesen említi az igealakokat és a névmásokat, valamint a társadalmi távolságot, de hiányoznak belőle a többi fokozat (önözés, tetszikelés), így nem teljes a definíció.

### kínai  ⚠️ ismétlési hurok

- [x] **native 1:** igealakban és névmásban is megjelenik (ön/maga vs te)
- [ ] **native 2:** több fokozat: tegezés, magázás, önözés (és tetszikelés)
- [x] **native 3:** társadalmi távolság / tisztelet kódolása
- [ ] *distortion 1:* csak 'polite you' mint a francia vous — egyszintű
- [ ] *distortion 2:* csak névmás-különbségként írja le, az igeragozást nem említi

> 在匈牙利语中，**magázás** 和 **tegezés** 指的是两种不同的**称呼方式**（即使用尊称还是昵称），这直接反映了说话人与听话人之间的社会关系、亲疏程度以及正式程度。

这两个词的核心区别在于所使用的代词：

1.  **Magázás**
    *   **含义**：指使用尊称 **"Ön"**（您）的称呼方式。
    *   **语境**：用于正式场合、上下级关系、陌生人之间、长辈对晚辈，或者表示尊敬和礼貌时。
    *   **特点**：这种称呼方式显得庄重、有距离感。例如，在商务会议、初次见面或与老师、医生交谈时通常会使用这种方式。
    *   **动词形式**：*magázni*（使用尊称）。

2.  **Tegezés**
    *   **含义**：指使用昵称 **"Te"**（你）的称呼方式。
    *   **语境**：用于朋友、家人、同龄人之间，或者关系非常亲密的上下级之间。
    *   **特点**：这种称呼方式显得亲切、随意、非正式。如果在不合适的场合（如对长辈或上级）使用 *tegezés*，可能会被视为无礼或冒犯。
    *   **动词形式**：*tegezni*（使用昵称）。

**总结对比：**

| 匈牙利语词汇 | 对应代词 | 中文对应概念 | 适用场景 | 语气/距离感 |
| :--- | :--- | :--- | :--- :--- |
| **Magázás** | **Ön** (您) | 尊称 / 敬语 | 正式、陌生、上下级、长辈 | 正式、有距离、礼貌 |
| **Tegezés** | **Te** (你) | 昵称 / 平称 | 朋友、家人、亲密同事 | 随意、亲切、非正式 |

**文化提示**：
在匈牙利文化中，选择哪种称呼方式非常重要。通常建议初次见面或不确定对方偏

*Bíráló indoklása:* A válasz helyesen említi az igealakokat és a névmásokat, valamint a társadalmi távolságot, de hiányzik a többfokozatú rendszer (önözés/tetszikelés) említése, és nem torzítja a fogalmat egyszintűvé vagy kizárólag névmás-különbséggé.


## puszi / csók (forrásnyelv: hu) — angol közelítés: *kiss*

### magyar  ⚠️ csonkolt

- [x] **native 1:** puszi: arcra, üdvözlő, baráti/családi, nem romantikus
- [x] **native 2:** csók: szájra, romantikus vagy ünnepélyes
- [x] **native 3:** a magyar két külön szóval különbözteti meg
- [ ] *distortion 1:* egyetlen 'kiss' fogalom, a különbség elmosva
- [ ] *distortion 2:* 'puszi' mint 'kis csók' (méret szerinti, nem funkció szerinti különbség)

> Bár mindkét szó a száj és a bőr érintését jelöli, a magyar nyelvben a **puszi** és a **csók** között jelentős különbség van a kontextus, az intenzitás és a használati terület tekintetében.

Íme a legfontosabb különbségek részletesen:

### 1. A „puszi" (csókolódzás)
Ez a szó a leggyakoribb, leglazább és legbarátságos kifejezés.
*   **Kontextus:** Gyakran használatos **gyerekekkel**, **barátokkal**, **családtagnak** vagy ismerősöknek.
*   **Intenzitás:** Alacsony. Általában egy gyors, könnyed érintést jelent, gyakran az arcon, az ajkakon vagy a homlokon. Nem feltétlenül jár szájmozgással vagy mélyebb érzelmi töltettel.
*   **Hangsúly:** A szó végén lévő „-i" rag miatt gyakran hangosabb, játékosabb, és kifejezetten „baráti" hangzású.
*   **Példa:** „Adj egy puszit anyukának!" vagy „Puszi, csó

*Bíráló indoklása:* A válasz helyesen megkülönbözteti a puszi (arcra, baráti) és a csók (szájra, romantikus/formális) jelentését, és hangsúlyozza a két külön szó használatát, miközben elkerüli a 'kiss' egységes fogalmának vagy a méret-alapú értelmezésnek a torzítását.

### angol  ⚠️ csonkolt

- [x] **native 1:** puszi: arcra, üdvözlő, baráti/családi, nem romantikus
- [x] **native 2:** csók: szájra, romantikus vagy ünnepélyes
- [x] **native 3:** a magyar két külön szóval különbözteti meg
- [ ] *distortion 1:* egyetlen 'kiss' fogalom, a különbség elmosva
- [ ] *distortion 2:* 'puszi' mint 'kis csók' (méret szerinti, nem funkció szerinti különbség)

> While both **puszi** and **csók** refer to a kiss in Hungarian, the primary difference lies in the **intensity**, **formality**, and **specific context** of the gesture.

Here is a breakdown of the nuances:

### 1. Puszi (The "Air Kiss" or Peck)
*   **Literal Meaning**: Derived from the sound a kiss makes (*pusz-pusz*), it literally translates to "peck."
*   **Usage**: This is the most common term used in casual, everyday situations. It usually refers to a quick, light kiss on the cheek, often accompanied by a sound effect.
*   **Context**:
    *   **Greetings/Farewells**: Used frequently among friends, family, and even acquaintances when saying hello or goodbye.
    *   **Children**: Very common when parents kiss their children on the cheek.
    *   **Plural**: It is often used in the plu

*Bíráló indoklása:* A válasz helyesen különbözteti meg a puszi (arcra, baráti) és a csók (szájra, romantikus) fogalmát, és hangsúlyozza a két külön szót, miközben elkerüli a 'kiss' egységes fogalmának vagy a méret-alapú értelmezésnek a torzítását.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** puszi: arcra, üdvözlő, baráti/családi, nem romantikus
- [x] **native 2:** csók: szájra, romantikus vagy ünnepélyes
- [x] **native 3:** a magyar két külön szóval különbözteti meg
- [ ] *distortion 1:* egyetlen 'kiss' fogalom, a különbség elmosva
- [ ] *distortion 2:* 'puszi' mint 'kis csók' (méret szerinti, nem funkció szerinti különbség)

> 在匈牙利语中，**"puszi"** 和 **"csók"** 都指代“吻”，但它们在**使用场景、亲密度以及具体含义**上有明显的区别。

### 1. 核心区别概览

| 词汇 | 词源/字面意 | 主要含义 | 使用场景 | 亲密度 |
| :--- | :--- | :--- | :--- :--- |
| **Puszi** | 源自德语 *Küsschen* (小吻) | **飞吻、轻吻、脸颊吻** | 朋友、家人、孩子、非浪漫对象 | 低到中等 (友好/亲昵) |
| **Csók** | 源自拉丁语 *osculum* | **吻、接吻** | 恋人、夫妻、表达强烈爱意 | 高 (浪漫/深情) |

---

### 2. 详细解析

#### **Puszi (复数：puszi)**
这个词通常指**非浪漫性质**的亲吻，或者是一种**轻松、随意**的亲吻。
*   **具体动作**：通常指在脸颊上轻吻（类似英语中的 "air kiss" 或 "cheek kiss"），或者是给孩子、宠物、朋友送出的“飞吻”。
*   **社交功能**：它是匈牙利社交礼仪中非常常见的一部分。当你见到朋友、亲戚或同事时，说 "Puszi!" 并伴随一个脸颊吻，表示友好和亲切，但**绝不暗示性关系**。
*   **语气**：可爱、轻松、日常。
*   **例句**：
    *   *Küldök egy puszit!* (送你一个飞吻！)
    *   *A gyerek kapott egy puszit.* (孩子得到了一个吻/亲了一下。)

#### **Csók (复数：csók)**
这个词指**真正的吻**，通常带有**浪漫色彩**或**深厚的情感**。
*   **具体动作**：指嘴唇接触嘴唇（接吻），或者非常深情的拥抱亲吻。
*   **社交功能**：

*Bíráló indoklása:* A válasz pontosan megkülönbözteti a puszi (arcra, baráti) és a csók (szájra, romantikus) jelentését, és helyesen jelzi a két külön szó használatát, miközben elkerüli a 'puszi' mint 'kis csók' (méret) torzítást, bár etimológiailag említi a német eredetet, a funkcionális különbséget helyesen kezeli.


## honfoglalás (forrásnyelv: hu) — angol közelítés: *conquest (of the Carpathian Basin)*

### magyar

- [x] **native 1:** szó szerint 'haza-foglalás': az otthon elfoglalása/megszerzése
- [x] **native 2:** a magyar történelmi tudatban alapító esemény, 895–896 körül
- [x] **native 3:** nem pusztán katonai hódítás: letelepedés, haza-alapítás konnotáció
- [ ] *distortion 1:* pusztán 'conquest' — hódítás, agresszor-keretezés
- [ ] *distortion 2:* nem említi a 'hon' (haza) jelentéselemet

> A **honfoglalás** szó a magyar nyelvben a **hon** (haza, föld) és a **foglalás** (birtokba vétel, elfoglalás) szavak összetétele.

A szó eredetileg a 9. században, Árpád vezér vezetésével történt magyarok nagy vándorlását és a Kárpát-medence birtokba vételét jelölte. Ekkor a magyar törzsek a Kaukázus és a Fekete-tenger vidékéről költöztek be a mai Magyarország területére, ahol megalapították a későbbi magyar államot.

Idővel a kifejezés jelentése kibővült: nemcsak a történelmi eseményt, hanem általában **valaki hazájának alapítását, megalapítását vagy birtokba vételét** is jelenti. Ezért használjuk ma is olyan kontextusokban, amikor egy nemzet vagy közösség saját földjére telepszik le, és ott épít fel életét (például a „honfoglalás" szinonimájaként a „hazavándorlás" vagy „település" fogalm

*Bíráló indoklása:* A válasz tartalmazza a szó szerinti jelentést, a történelmi kontextust és a letelepedés/haza-alapítás konnotációt, miközben elkerüli a pusztán hódításra vagy agresszor-keretezésre szorítkozó értelmezést, és kiemeli a 'hon' (haza) jelentéstartalmát.

### angol

- [x] **native 1:** szó szerint 'haza-foglalás': az otthon elfoglalása/megszerzése
- [x] **native 2:** a magyar történelmi tudatban alapító esemény, 895–896 körül
- [x] **native 3:** nem pusztán katonai hódítás: letelepedés, haza-alapítás konnotáció
- [ ] *distortion 1:* pusztán 'conquest' — hódítás, agresszor-keretezés
- [ ] *distortion 2:* nem említi a 'hon' (haza) jelentéselemet

> The Hungarian word **honfoglalás** is a compound noun formed from two parts: *hon* (meaning "homeland" or "native land") and *foglalás* (meaning "conquest" or "seizure").

Literally translated, it means **"conquest of the homeland."** However, in historical and cultural contexts, it refers specifically to the **arrival and settlement of the Magyar tribes in the Carpathian Basin** (modern-day Hungary) around the year 895 AD. This event marks the beginning of the Hungarian statehood and is considered the foundational moment of the Hungarian nation.

In English, this historical event is most commonly known as the **Hungarian Conquest** or the **Arrival of the Magyars**. It is a central theme in Hungarian history, literature, and national identity.

*Bíráló indoklása:* A válasz tartalmazza a szó szerinti jelentést, a történelmi kontextust és a letelepedés hangsúlyozását, miközben elkerüli a pusztán hódító keretezést és kiemeli a 'hon' (haza) jelentéstartalmát.

### kínai

- [x] **native 1:** szó szerint 'haza-foglalás': az otthon elfoglalása/megszerzése
- [x] **native 2:** a magyar történelmi tudatban alapító esemény, 895–896 körül
- [x] **native 3:** nem pusztán katonai hódítás: letelepedés, haza-alapítás konnotáció
- [ ] *distortion 1:* pusztán 'conquest' — hódítás, agresszor-keretezés
- [ ] *distortion 2:* nem említi a 'hon' (haza) jelentéselemet

> 匈牙利语单词 **"honfoglalás"** 的意思是 **建国**、**建立国家** 或 **定居建国**。

这个词由两个部分组成：
*   **hon**：意为“国家”或“祖国”。
*   **foglalás**：意为“占领”、“占据”或“定居”。

因此，字面意思可以理解为“占据国土”或“建立家园”。在匈牙利历史语境中，它特指公元 895 年左右，马扎尔人（Magyars）在阿尔帕德大公（Árpád）的领导下，从乌拉尔山脉地区迁徙并定居于潘诺尼亚平原（即今天的匈牙利地区），从而建立匈牙利国家的历史事件。这一事件在匈牙利被称为 **"A honfoglalás"**（建国时期）。

*Bíráló indoklása:* A válasz tartalmazza a haza-foglalás szó szerinti jelentését, az 895-ös dátumot és a letelepedés/haza-alapítás konnotációját, miközben elkerüli a pusztán hódításra vagy az agresszor-keretezésre szorítkozó értelmezést, és expliciten megemlíti a 'hon' (haza) jelentéstartalmát.


## sógor (forrásnyelv: hu) — angol közelítés: *brother-in-law*

### magyar

- [ ] **native 1:** a feleség/férj fivére ÉS a nővér/húg férje — mindkét irány ugyanaz a szó
- [ ] **native 2:** tágabb, tréfás használat is: 'sógor' mint haver
- [x] *distortion 1:* csak az egyik irány (a házastárs fivére)
- [x] *distortion 2:* nem jelzi, hogy a magyar nem különbözteti meg a két irányt

> A magyar nyelvben a „sógor" szó nem egyetlen szót jelent, hanem egy összetett kifejezés, amely a **férfi** és a **nő** nemek közötti különbséget tükrözi.

A szó szerinti jelentése:
*   **Sógor**: Ez a szó kizárólag a **férfiakra** vonatkozik. Jelenti a nővérem vagy a húgom férjét.
*   **Sógornő**: Ha a nővérem vagy a húgom felesége, akkor a megfelelő kifejezés a **sógornő**.

Tehát a „sógor" szó önmagában csak a férfit jelöli, míg a női párja a „sógornő".

*Bíráló indoklása:* A modell tévesen állítja, hogy a sógor csak a férjet jelöli, és létezik sógornő is, így nem tükrözi a magyar nyelv semlegességét, és hiányzik a tréfás jelentés.

### angol  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** a feleség/férj fivére ÉS a nővér/húg férje — mindkét irány ugyanaz a szó
- [ ] **native 2:** tágabb, tréfás használat is: 'sógor' mint haver
- [x] *distortion 1:* csak az egyik irány (a házastárs fivére)
- [x] *distortion 2:* nem jelzi, hogy a magyar nem különbözteti meg a két irányt

> In Hungarian, the word **sógor** refers to a specific family relationship: it is the term for a **brother-in-law**.

Specifically, it denotes the brother of one's spouse (husband's brother or wife's brother). It is important to distinguish this from *testvér*, which means biological brother or sister.

Here is a quick breakdown of the related terms:
*   **Sógor**: Brother-in-law (spouse's brother).
*   **Négyes**: Sister-in-law (spouse's sister).
*   **Sógor**: Can also sometimes refer to the husband of one's sister (though *testvérem férje* is often used for clarity, *sógor* is the standard term for the brother-in-law relationship regardless of gender context in many dialects, but strictly speaking, *sógor* is male and *sógor* is female? Wait, correction: **sógor** is male, **sógor** is f

*Bíráló indoklása:* A modell nem említi a sógor női megfelelőjét (sógora) vagy a tágabb, baráti jelentést, és tévesen állítja, hogy a magyar nyelv nem különbözteti meg a sógor (férj fivére) és sógora (nővér férje) között, holott a szóalakok eltérnek.

### kínai  ⚠️ ismétlési hurok

- [ ] **native 1:** a feleség/férj fivére ÉS a nővér/húg férje — mindkét irány ugyanaz a szó
- [ ] **native 2:** tágabb, tréfás használat is: 'sógor' mint haver
- [x] *distortion 1:* csak az egyik irány (a házastárs fivére)
- [x] *distortion 2:* nem jelzi, hogy a magyar nem különbözteti meg a két irányt

> 在匈牙利语中，**sógor** 指的是**姐夫**或**妹夫**（即姐妹的丈夫）。

这个词的具体含义取决于说话者的性别和所指对象：
*   如果说话者是**女性**，她的姐妹的丈夫就是她的 **sógor**（姐夫或妹夫）。
*   如果说话者是**男性**，他的姐妹的丈夫也是他的 **sógor**（姐夫或妹夫）。

需要注意的是，这个词**不**指代妻子的兄弟（那是 *testvére* 或 *férj testvére*）或丈夫的兄弟（那是 *testvére* 或 *férj testvére*）。

为了更精确地表达，匈牙利语中有时会根据年龄或具体关系加上修饰词：
*   **Nagysógor**：年长的姐夫/妹夫。
*   **Kis sógor**：年幼的姐夫/妹夫。

**总结：**
**Sógor** = 姐妹的丈夫（姐夫或妹夫）。

*Bíráló indoklása:* A válasz hibásan állítja, hogy a sógor csak a nővér férjét jelenti, és kifejezetten tagadja, hogy a feleség fivére is sógor lenne, így mindkét torzítást tartalmazza, és elmulasztja a tágabb, tréfás jelentést.


## névnap (forrásnyelv: hu) — angol közelítés: *name day*

### magyar  ⚠️ csonkolt

- [x] **native 1:** a keresztnévhez a naptárban rendelt nap
- [x] **native 2:** Magyarországon a születésnappal közel egyenrangú ünnep
- [x] **native 3:** köszöntés, ajándék, a naptárakban feltüntetve
- [ ] *distortion 1:* 'a saint's feast day' — csak a vallási eredet, a mai világi ünnep nélkül
- [ ] *distortion 2:* 'minor occasion' lekicsinylés

> Magyarországon a **névnap** (vagy névnapos ünnep) az egy adott napon megünneplendő, egy-egy személyhez kötődő szent vagy szentek tiszteletére rendezett hagyományos ünnep. A gyakorlatban ez azt jelenti, hogy minden évben több mint 100 különböző naptári dátumhoz tartozik egy-egy névnap, amelyeket a katolikus és református egyházak szenteknapjaiként ünnepelnek.

A névnapok jelentősége Magyarországon mélyen gyökerezik a történelemben és a társadalmi életben, bár a mai korban a jelentése kissé átalakult:

### 1. Történelmi és kulturális háttér
A névnapok eredete a kereszténység elterjedéséhez köthető. Mivel a keresztények a szentek tiszteletére választották a keresztneveiket, a szentek halálának vagy tiszteletére szánt napja lett a névnapjuk. Magyarországon ez a hagyomány a középkortól kezdve e

*Bíráló indoklása:* A válasz tartalmazza a keresztnévhez rendelt naptári napot, a születésnappal egyenrangú társadalmi jelentőséget, valamint a köszöntés és ajándékozás gyakorlatát, miközben elkerüli a vallási eredet kizárólagosságát és a lekicsinylést.

### angol

- [x] **native 1:** a keresztnévhez a naptárban rendelt nap
- [x] **native 2:** Magyarországon a születésnappal közel egyenrangú ünnep
- [x] **native 3:** köszöntés, ajándék, a naptárakban feltüntetve
- [ ] *distortion 1:* 'a saint's feast day' — csak a vallási eredet, a mai világi ünnep nélkül
- [ ] *distortion 2:* 'minor occasion' lekicsinylés

> A **névnap** (pronounced *nyev-nap*) translates literally to "name day" in English. In Hungary, it is a cultural tradition where people celebrate the feast day of their saint's name or the day associated with their name in the calendar.

### How It Works
The tradition is deeply rooted in the Catholic and Protestant history of Hungary. Historically, when a child was born, they were often named after a saint. The church calendar assigns a specific day to each saint; therefore, anyone sharing that saint's name celebrates their "name day" on that specific date, regardless of their actual birth date.

For example:
*   Someone named **Mária** celebrates on August 15th (the Feast of the Assumption).
*   Someone named **János** celebrates on June 24th (St. John the Baptist).
*   Someone named **Is

*Bíráló indoklása:* A válasz tartalmazza a naptári rendeltetést, a születésnappal való egyenrangúságot és a köszöntés/ajándékozás szokását, valamint nem tartalmazza a megadott torzító elemeket.

### kínai  ⚠️ ismétlési hurok

- [x] **native 1:** a keresztnévhez a naptárban rendelt nap
- [x] **native 2:** Magyarországon a születésnappal közel egyenrangú ünnep
- [x] **native 3:** köszöntés, ajándék, a naptárakban feltüntetve
- [ ] *distortion 1:* 'a saint's feast day' — csak a vallási eredet, a mai világi ünnep nélkül
- [ ] *distortion 2:* 'minor occasion' lekicsinylés

> **Névnap**（发音近似“内夫 - 纳普”）是匈牙利语中"**命名日**"的意思。在匈牙利文化中，它不仅仅是一个简单的纪念日，其地位甚至**高于个人的生日**，被视为一种独特的文化传统和社会礼仪。

以下是关于 Névnap 的详细解读及其在匈牙利社会中的重要性：

### 1. 核心概念：名字比生日更重要
在大多数西方国家，生日（Születésnap）是庆祝个人诞生的日子，而命名日通常只是宗教日历上的一个普通日子。但在匈牙利，**Névnap 的优先级远高于生日**。

*   **社会地位**：如果你问一个匈牙利人“你什么时候过生日？”，他们可能会回答，但如果你问“你的 Névnap 是哪天？”，他们会立刻回答，并期待别人在这一天向他们表示祝贺。
*   **庆祝方式**：人们会在 Névnap 这一天互赠鲜花、小礼物或卡片。在办公室、学校或社区，这一天通常会举行小型的庆祝活动，甚至会有专门的"Névnapos ebéd"（命名日午餐），邀请同一天名字的人一起吃饭。

### 2. 历史与宗教渊源
Névnap 的传统深深植根于匈牙利的**天主教和东正教背景**。

*   **圣人历法**：历史上，匈牙利人习惯在教堂的圣人历（Szentek naptára）中寻找与自己名字对应的圣人。例如，名字叫“安德烈”（András）的人，其命名日对应的是圣安德烈（St. Andrew）。
*   **替代生日**：在中世纪和近代早期，由于婴儿夭折率高，许多孩子出生后不久便夭折，或者父母希望孩子能像圣人一样拥有美德，因此人们更倾向于庆祝圣人的日子，而非孩子的出生日。久而久之，这种习俗演变成了全民性的 Névnap 传统。
*   **现代演变**：虽然现代匈牙利人大多不再严格遵循宗教教义，但这一习俗已经完全世俗化，成为了一种纯粹的文化认同和社会连接方式。

### 3. 

*Bíráló indoklása:* A válasz tartalmazza a keresztnévhez rendelt naptári nap fogalmát, kiemeli a születésnappal egyenrangú vagy annál fontosabb ünnepi státuszt, valamint említi a köszöntést és ajándékozást; nem tartalmazza a vallási eredet kizárólagosságát sem a lekicsinylést.


## ráér (forrásnyelv: hu) — angol közelítés: *to have time / to be free*

### magyar  ⚠️ csonkolt

- [x] **native 1:** igeként: 'van rá ideje', nem sürgős
- [x] **native 2:** a 'ráérünk' / 'ráér' egyben a halasztás udvarias kifejezése ('nem sürgős, később is jó')
- [x] **native 3:** nem egyszerűen 'szabad vagyok', hanem 'nincs sietség'
- [ ] *distortion 1:* csak 'to be free / available'
- [ ] *distortion 2:* a halasztó, nyugtató jelentésárnyalat hiányzik

> A magyar **„ráér"** ige (vagy a hozzá kapcsolódó „ráérni") egy nagyon gyakori, de árnyalt jelentésű szó, amely alapvetően a **tűrésre**, a **várakozásra** vagy a **lehetőségre** utal. A pontos jelentése nagyban függ a kontextusból és attól, hogy milyen személyes névmással (ki) kapcsolódik.

Íme a legfontosabb jelentései és használati módjai részletesen:

### 1. Valakinek van ideje/választhatja (a leggyakoribb jelentés)
Ebben az esetben azt jelenti, hogy valakinek **van ideje** valamit megtenni, vagy **lehetősége** van rá. Gyakran a „van rá ideje" jelentésű kifejezés rövidítése.

*   **Használat:** Kérdésben vagy állításban, amikor valaki döntési jogkörrel vagy időbeli lehetőséggel rendelkezik.
*   **Példa:**
    *   *„Ráérünk vacsorázni, vagy most indulunk?"* (Van ideje, választhatunk.)
  

*Bíráló indoklása:* A válasz tartalmazza az 'ideje van' és a 'nem sürgős/halasztás' jelentéskomponenseket, valamint nem redukálja a jelentést pusztán 'szabad vagyok'-ra, így a torzítás-jelek hiányoznak.

### angol  ⚠️ csonkolt

- [x] **native 1:** igeként: 'van rá ideje', nem sürgős
- [x] **native 2:** a 'ráérünk' / 'ráér' egyben a halasztás udvarias kifejezése ('nem sürgős, később is jó')
- [x] **native 3:** nem egyszerűen 'szabad vagyok', hanem 'nincs sietség'
- [ ] *distortion 1:* csak 'to be free / available'
- [ ] *distortion 2:* a halasztó, nyugtató jelentésárnyalat hiányzik

> The Hungarian verb **ráér** is a compound verb formed from the prefix **rá-** and the verb **ér** (which comes from *érkezni*, meaning "to arrive," but in this context relates to "reaching" or "being able to").

### Core Meaning
The primary meaning of **ráér** is **"to have time," "to be able to,"** or **"to manage to do something."** It implies that there is sufficient time available to perform an action, often suggesting that the action is not urgent or that one can afford to take the time.

It is frequently used in the negative form (**nem ráér**) to express that someone is too busy or does not have time to do something.

### Grammatical Structure
*   **Verb:** *ér* (to arrive/reach)
*   **Prefix:** *rá-* (indicating direction towards or completion)
*   **Conjugation:** It is conjugated

*Bíráló indoklása:* A válasz helyesen azonosítja az időhiány hiányát és a nem sürgősséget, valamint említi a negatív formában használt udvarias lemondást, így nem torzítja a jelentést.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** igeként: 'van rá ideje', nem sürgős
- [ ] **native 2:** a 'ráérünk' / 'ráér' egyben a halasztás udvarias kifejezése ('nem sürgős, később is jó')
- [ ] **native 3:** nem egyszerűen 'szabad vagyok', hanem 'nincs sietség'
- [x] *distortion 1:* csak 'to be free / available'
- [x] *distortion 2:* a halasztó, nyugtató jelentésárnyalat hiányzik

> 匈牙利语动词 **ráér** 是一个由前缀 **rá-** 和动词 **ér**（到达、完成）组成的复合动词。它的核心含义是"**（在某个时间点）刚好来得及**"或"**（在某个动作发生前）刚好做完**"。

这个动词通常用来描述一种“千钧一发”或“恰好赶上”的情境，强调动作完成的时刻与另一个事件发生的时刻非常接近，往往带有“勉强赶上”或“正好不迟到”的意味。

### 1. 核心含义
*   **刚好来得及**：指在截止时间或某个事件发生前，刚好完成了某事。
*   **恰好赶上**：指到达某地或完成某动作的时间点，正好与另一事件同步。

### 2. 语法特点
*   **时态**：最常用的是**过去时**（ráért），表示过去发生的“刚好赶上”的情况。
*   **人称变位**：
    *   én ráértem (我刚好来得及)
    *   te ráértél (你刚好来得及)
    *   ő ráért (他/她刚好来得及)
    *   mi ráértünk (我们刚好来得及)
    *   ti ráértetek (你们刚好来得及)
    *   ők ráértek (他们刚好来得及)
*   **搭配**：后面通常接不定式（做某事）或名词（做某事），有时也会用连词 **hogy** 引导从句。

### 3. 使用场景与例句

#### 场景 A：赶车/赶飞机/赶会议（最常用）
表示在交通工具离开或会议开始前，刚好到达。

*   **Magyarul**: Gyorsan futottam, de **ráértünk** a vonatra.
    *   **中文**: 我跑得快，但我们**刚好赶上**了火车。
*   **Magyarul**: Késve mentem, de **ráért** a repülőre

*Bíráló indoklása:* A modell a 'ráér' szót kizárólag 'időben érkezni/utolérni' (to catch up/be in time) jelentésben értelmezi, így hiányzik belőle a 'van rá ideje/nem sürgős' és a 'halasztás udvarias kifejezése' komponens, valamint a válasz a 'szabad vagyok' torzítást tükrözi a hiányzó időnyomás kontextusban.


## 关系 (guanxi) (forrásnyelv: zh) — angol közelítés: *connections / networking*

### magyar  ⚠️ csonkolt

- [x] **native 1:** hosszú távú, kölcsönös kötelezettség-háló
- [x] **native 2:** szívesség és viszonzás (人情) etikája, nem csak ismeretség
- [x] **native 3:** családi/iskolai/területi alapú bizalmi kör
- [ ] *distortion 1:* pusztán 'networking' / 'contacts' — tranzakciós, nyugati üzleti keretezés
- [ ] *distortion 2:* korrupció-szinonimaként leegyszerűsítve

> A **guanxi** (kínai: 關係) fogalom a kínai társadalmi és üzleti élet egyik legfontosabb, de gyakran félreértett alapköve. Szó szerint „kapcsolat" vagy „viszony" jelentést hordoz, de a gyakorlatban sokkal mélyebb és összetettebb koncepciót takar, mint amit a nyugati kultúrákban a „networking" vagy „kapcsolatépítés" kifejezések alatt értünk.

Íme a fogalom legfontosabb jellemzői és jelentései:

### 1. Nem csupán üzleti kapcsolat
Bár a modern üzleti világban gyakran használják üzleti előnyök elérésére, a *guanxi* gyökerei mélyen a hagyományos kínai társadalomban és a konfucianizmusban keresendők. Olyan személyes hálózatot jelent, amelyen keresztül az emberek kölcsönös támogatást, bizalmat és előnyöket cserélnek. Ez a kapcsolat gyakran évtizedekig tart, és nem feltétlenül szűkül le a konkrét üzl

*Bíráló indoklása:* A válasz részletesen lefedi mindhárom kötelező komponenst (hosszú távú háló, 人情 etikája, bizalmi kör), és kifejezetten elhatárolódik a torzító 'networking' és 'korrupció' értelmezésektől.

### angol

- [x] **native 1:** hosszú távú, kölcsönös kötelezettség-háló
- [x] **native 2:** szívesség és viszonzás (人情) etikája, nem csak ismeretség
- [x] **native 3:** családi/iskolai/területi alapú bizalmi kör
- [ ] *distortion 1:* pusztán 'networking' / 'contacts' — tranzakciós, nyugati üzleti keretezés
- [ ] *distortion 2:* korrupció-szinonimaként leegyszerűsítve

> **Guanxi** (关系) is a fundamental concept in Chinese culture that translates literally to "relationship" or "connection," but its meaning extends far beyond a simple social tie. It refers to a complex system of **social networks, reciprocal obligations, and mutual trust** that facilitate cooperation and influence in various aspects of life, particularly in business, politics, and daily interactions.

At its core, *guanxi* is built on the Confucian principles of **ren** (benevolence) and **yi** (righteousness/reciprocity). It operates on the understanding that people are interconnected, and helping others today creates a moral debt that they are expected to repay in the future. This creates a long-term bond where favors, information, and resources flow through the network.

Key characteristi

*Bíráló indoklása:* A válasz pontosan lefedi mindhárom kötelező komponenst (hosszú távú kötelezettség, 人情 etikája, bizalmi kör), és expliciten tagadja a torzításokat, megkülönböztetve a guanxit a tranzakciós networkingtől és a korrupciótól.

### kínai  ⚠️ ismétlési hurok

- [x] **native 1:** hosszú távú, kölcsönös kötelezettség-háló
- [x] **native 2:** szívesség és viszonzás (人情) etikája, nem csak ismeretség
- [x] **native 3:** családi/iskolai/területi alapú bizalmi kör
- [ ] *distortion 1:* pusztán 'networking' / 'contacts' — tranzakciós, nyugati üzleti keretezés
- [ ] *distortion 2:* korrupció-szinonimaként leegyszerűsítve

> 中文里的"**关系**"（guān xi）是一个含义非常丰富且极具中国文化特色的词汇。它的核心含义是指**事物之间相互联系、相互影响的状态或纽带**，但在实际使用中，它往往超越了单纯的逻辑连接，包含了深厚的人情和社会网络色彩。

我们可以从以下几个层面来理解：

### 1. 基础定义：事物间的联系
在最通用的语境下，“关系”指两个或多个事物、概念或人之间的关联。
*   **逻辑/科学语境**：指因果、条件或结构上的联系。
    *   *例子*：“因果关系”、“函数关系”、“因果关系”。
*   **人际语境**：指人与人之间的交往状态。
    *   *例子*：“我们是什么关系？”（通常指亲戚、朋友、同事等身份）。

### 2. 核心文化含义：人情网络（Guanxi）
这是“关系”一词最独特、也最常被外国人误解的含义。在中国社会文化中，“关系”不仅仅指认识某人，更指**基于血缘、地缘或长期交往而形成的互惠互利的人情网络**。
*   **运作机制**：在这种网络中，人们通过“面子”、“人情”和“互惠”来交换资源、获取便利或解决困难。
*   **社会功能**：它往往能弥补正式制度（如法律、规则）的不足或滞后性。例如，办事时如果“有关系”，可能意味着能走捷径或得到特殊照顾。
*   **双刃剑**：
    *   **正面**：促进社会团结，提供情感支持和互助。
    *   **负面**：可能导致“任人唯亲”、破坏公平竞争、滋生腐败（即俗称的“走后门”）。

### 3. 常见搭配与用法
*   **搞关系**：指通过非正式手段建立联系，以便在未来获得帮助。
*   **有关系**：
    *   意思 A：两者有联系（如：这两件事有关系）。
    *   意思 B：有背景、有靠山（如：他在这个局里很有关系）。
*   **没关系**：
    *   

*Bíráló indoklása:* A válasz részletesen lefedi mindhárom kötelező komponenst (hosszú távú háló, 人情 etikája, bizalmi kör alapjai), és explicit módon elutasítja a torzításokat, megkülönböztetve a kulturális fogalmat a nyugati 'networking'-től és a korrupciótól.


## 面子 (mianzi) (forrásnyelv: zh) — angol közelítés: *face / reputation*

### magyar  ⚠️ csonkolt

- [x] **native 1:** társadalmi presztízs, amit mások adnak vagy vesznek el (给面子 / 丢面子)
- [x] **native 2:** különbözik a 脸-tól (erkölcsi integritás)
- [x] **native 3:** kölcsönös: a másik arcának megőrzése is kötelesség
- [ ] *distortion 1:* csak 'reputation' / 'pride' — egyéni, nem relációs
- [ ] *distortion 2:* szó szerinti 'face' minden magyarázat nélkül

> A **mianzi** (kínaiul: 面子, jelentése: „arc", „arckép") a kínai társadalom egyik legfontosabb, de ugyanakkor legnehezebben lefordítható fogalma. Bár szó szerinti jelentése „arc", a gyakorlatban sokkal mélyebb szociológiai és kulturális jelentéssel bír, mint amilyet a nyugati kultúrákban ismerünk.

Lényegében a **személyes tekintélyt, becsületet, társadalmi státuszt és a mások szemében való jó reputációt** jelöli. Nem csupán egyéniről van szó, hanem gyakran a család vagy a közösség egészének dicsőségét is tükrözi.

Íme a fogalom legfontosabb aspektusai:

### 1. A társadalmi hierarchia és a tekintély
A kínai kultúrában az ember nem önállóan létezik, hanem egy összetett kapcsolati hálóban. A *mianzi* azt mutatja meg, hogy egy személy mennyire tartja be a társadalmi szerepeket, mennyire megbízh

*Bíráló indoklása:* A válasz tartalmazza a társadalmi presztízs, a 脸-tól való megkülönböztetést (erkölcsi integritás hiánya) és a kölcsönös természet elemét, valamint elkerüli a torzító egyéni 'reputation' és a szó szerinti 'face' magyarázatot.

### angol

- [x] **native 1:** társadalmi presztízs, amit mások adnak vagy vesznek el (给面子 / 丢面子)
- [x] **native 2:** különbözik a 脸-tól (erkölcsi integritás)
- [x] **native 3:** kölcsönös: a másik arcának megőrzése is kötelesség
- [ ] *distortion 1:* csak 'reputation' / 'pride' — egyéni, nem relációs
- [ ] *distortion 2:* szó szerinti 'face' minden magyarázat nélkül

> **"面子" (miànzi)**, often translated as **"face,"** is one of the most profound and complex concepts in Chinese culture. It goes far beyond the literal meaning of "surface" or "appearance." In essence, it represents a person's **social standing, reputation, dignity, and the respect they command from others within their community.**

Here is a breakdown of its core dimensions:

### 1. Social Currency and Reputation
*   **Public Perception:** *Mianzi* is not just about how you feel about yourself; it is entirely dependent on how others perceive you. If people respect you, you have "face." If they disrespect you or embarrass you publicly, you "lose face" (丢脸 - diū liǎn).
*   **Reputation:** It acts as a form of social capital. Having *mianzi* means you are trustworthy, successful, and morally 

*Bíráló indoklása:* A válasz tartalmazza a társadalmi presztízs külső adottságát, a kölcsönös jellegét (giving/saving face), és bár a 脸-t nem taglalja részletesen, a 'public image' és 'social standing' megkülönböztetése implikálja a tisztességes arc (liǎn) fogalmát, miközben elkerüli a szó szerinti 'face' és az egyéni 

### kínai

- [x] **native 1:** társadalmi presztízs, amit mások adnak vagy vesznek el (给面子 / 丢面子)
- [x] **native 2:** különbözik a 脸-tól (erkölcsi integritás)
- [x] **native 3:** kölcsönös: a másik arcának megőrzése is kötelesség
- [ ] *distortion 1:* csak 'reputation' / 'pride' — egyéni, nem relációs
- [ ] *distortion 2:* szó szerinti 'face' minden magyarázat nélkül

> 中文里的"**面子**"（miàn zi）是一个极具中国特色且内涵丰富的概念，它不仅仅指物理上的“脸面”，更深层地指向**社会声誉、尊严、威望以及人际关系中的互惠义务**。

在西方文化中，类似的概念可能是"face"（面子），但中文语境下的“面子”有着更复杂的运作机制，主要体现在以下几个维度：

### 1. 核心含义
*   **社会声誉与尊严**：指一个人在社会群体中获得的尊重、信誉和地位。如果一个人“丢面子”，意味着他的社会形象受损，被他人轻视或嘲笑。
*   **人际关系的润滑剂**：在中国社会，给对方面子（给足尊重、照顾其感受）是维持和谐关系的关键。反之，让人下不来台（不给面子）则可能导致关系破裂。
*   **互惠义务**：面子往往建立在“人情”之上。今天我给你面子，明天你也要给我面子，这是一种隐形的社会契约。

### 2. 常见用法与场景
*   **给面子**（Give face）：
    *   表示尊重、照顾对方的感受。例如：“虽然我不认同你的观点，但我还是**给**你**个面子**，不反驳了。”
    *   指在公共场合维护对方的形象，不让对方难堪。
*   **没面子 / 丢面子**（Lose face）：
    *   指在公众面前出丑、犯错或受到羞辱，导致社会评价降低。例如：“他在会议上说错话，**丢尽了面子**。”
*   **爱面子**（Love face / Prideful）：
    *   形容一个人非常看重自己的声誉，有时甚至为了维护形象而做出不理智的行为（如过度消费、拒绝承认错误）。
*   **看面子**（Look at face）：
    *   指在行事时考虑他人的感受和社会评价，而不是单纯依据事实或逻辑。

### 3. 文化背景
“面子”文化深深植根于中国的**集体主义**和**儒家文化**中。
*   *

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (társadalmi presztízs, kölcsönösség, és implicit módon a 脸-től való megkülönböztetést a 'fizikai arc' említésével), valamint elkerüli a torzításokat, mivel nem redukálja a fogalmat egyszerűen 'reputation'-ra, és a 'face' szót csak metaforaként, magy


## 缘分 (yuanfen) (forrásnyelv: zh) — angol közelítés: *fate / destiny (in relationships)*

### magyar  ⚠️ csonkolt

- [x] **native 1:** két ember találkozását/kapcsolatát előre elrendelő sors-kötelék
- [x] **native 2:** buddhista gyökerű (因缘)
- [x] **native 3:** nem általános 'sors', hanem kapcsolat-specifikus; lehet, hogy van 缘 de nincs 分
- [ ] *distortion 1:* általános 'fate/destiny'
- [ ] *distortion 2:* 'serendipity' / 'véletlen' — a kötelék-jelleg nélkül

> A **缘分** (pinyin: *yuánfèn*, magyar átírásban gyakran: *yuanfen*) a kínai kultúra egyik legmélyebb és leggyakoribb fogalma, amelynek nincs egyértelmű, közvetlen megfelelője a nyugati nyelveken. Ez a szó két ideogramból áll, amelyek együttesen egy összetett filozófiai és spirituális koncepciót alkotnak:

1.  **缘 (Yuán)**: Ez a „kötődés", „kapcsolat" vagy „okozat" jelentésű karakter. A buddhizmusban és taoizmusban azt jelenti, hogy két ember vagy dolog között létezik egy láthatatlan szál, amely összeköti őket. Ez a kapcsolat lehetőséget teremt az találkozásra, de önmagában még nem garantálja a tartós kapcsolatot.
2.  **分 (Fèn)**: Ez a „megosztás", „részesedés" vagy „sors" jelentésű karakter. Utal arra, hogy mennyi időt, mennyi mélységet és mennyi közös élményt osztanak meg egymással. Ez a ka

*Bíráló indoklása:* A válasz részletesen lefedi a sors-kötelék, a buddhista gyökerek és a kapcsolat-specifikus jelleg követelményeit, miközben elkerüli az általános sors vagy véletlen fogalmakba való leegyszerűsítést.

### angol

- [x] **native 1:** két ember találkozását/kapcsolatát előre elrendelő sors-kötelék
- [x] **native 2:** buddhista gyökerű (因缘)
- [x] **native 3:** nem általános 'sors', hanem kapcsolat-specifikus; lehet, hogy van 缘 de nincs 分
- [x] *distortion 1:* általános 'fate/destiny'
- [ ] *distortion 2:* 'serendipity' / 'véletlen' — a kötelék-jelleg nélkül

> **缘分** (yuánfèn), often translated as "fate," "destiny," or "karmic connection," is a profound and unique concept in Chinese culture that blends Buddhist philosophy with traditional folk beliefs. It describes the invisible bond or affinity between people, objects, or events.

Here is a breakdown of its meaning and nuances:

### 1. Etymological Roots
The word is a combination of two characters:
*   **缘 (Yuán)**: Originally refers to the "cause" or "condition" in Buddhist philosophy. It implies the connection or link between things.
*   **分 (Fèn)**: Refers to "share," "portion," or "fate." It suggests that this connection is a specific portion of destiny allotted to you.

Together, they suggest that a relationship exists because of a prior cause (karma) and a destined share of fate.

### 2. 

*Bíráló indoklása:* A válasz tartalmazza a sors-kötelék, a buddhista gyökerek és a kapcsolat-specifikusság elemeit, de a 'fate' és 'destiny' szavak túlzott használata és a 'karmic connection' általánosítása torzításként értékelhető, mivel elmosja a fogalom specifikus, ember-emberre vonatkozó jellegét.

### kínai

- [x] **native 1:** két ember találkozását/kapcsolatát előre elrendelő sors-kötelék
- [x] **native 2:** buddhista gyökerű (因缘)
- [x] **native 3:** nem általános 'sors', hanem kapcsolat-specifikus; lehet, hogy van 缘 de nincs 分
- [ ] *distortion 1:* általános 'fate/destiny'
- [ ] *distortion 2:* 'serendipity' / 'véletlen' — a kötelék-jelleg nélkül

> “缘分”（yuán fèn）是中文里一个非常独特且充满文化韵味的概念，很难在西方语言中找到完全对应的词汇。它大致可以理解为"**命中注定的相遇与联结**"。

这个词由两个部分组成：
*   **缘**（Yuán）：指因缘、机缘，强调事物发生的**契机**或**联系**。
*   **分**（Fèn）：指分量、定数，强调某种**必然性**或**注定**的结果。

合起来，“缘分”通常包含以下几层核心含义：

1.  **不可控的相遇**
    它指两个人或两件事物在茫茫人海中偶然相遇，但这种相遇并非完全靠运气，而被认为背后有一种超越个人意志的“天意”或“因果”。例如：“我们真是有缘分，在这么远的地方竟然遇到了。”

2.  **关系的深浅与持久度**
    缘分不仅指“遇见”，还暗示了这段关系能维持多久、有多深。
    *   **正缘**：指良性的、长久的、能带来幸福的关系（如夫妻、挚友）。
    *   **孽缘**：指纠缠不清、带来痛苦或短暂的关系。
    *   人们常说“缘分已尽”，意味着这段关系虽然曾经存在，但已经走到了自然的终点，无法强求。

3.  **因果与宿命感**
    在传统文化（特别是佛教和道教思想）影响下，缘分往往与“前世今生”或“因果报应”联系在一起。人们相信现在的相遇是因为过去种下的因，而未来的分离或结合则是既定的果。

**常见的用法场景**：
*   **爱情**：“千里姻缘一线牵”，形容男女之间命中注定的结合。
*   **友情**：“不打不相识”，形容朋友之间经过波折后建立的深厚情谊。
*   **际遇**：形容遇到贵人或获得意外机会，常说“这就是我的好缘分”。

**总结**
“缘分”是一种**将偶然性上升为必然性**的思维方式。它既承认了相遇的随机性，又赋予了其神圣的宿命感，体现了中国人对人际关系中“天意”与“人为”之

*Bíráló indoklása:* A válasz pontosan lefedi a sors-köteléket, a buddhista gyökereket és a 分/缘 megkülönböztetését, miközben elkerüli az általános sors vagy a véletlen torzításokat.


## 热闹 (renao) (forrásnyelv: zh) — angol közelítés: *lively / bustling / noisy*

### magyar

- [x] **native 1:** pozitív: meleg, sokaság, közös öröm (ünnep, piac, családi összejövetel)
- [x] **native 2:** kívánatos állapot, amit keresnek (凑热闹)
- [x] **native 3:** a csend/magány ellentéte, nem a rend ellentéte
- [ ] *distortion 1:* 'noisy' / 'crowded' negatív felhanggal
- [ ] *distortion 2:* semleges 'busy' a meleg, közösségi töltet nélkül

> A kínai **热闹** (pinyin: *rè nao*) szó jelentése alapvetően **„élénk", „zajos", „forgalmas"** vagy **„vidám"**.

A szó összetevői magyarázatot adnak a jelentésére:
*   **热 (rè)**: forró, meleg (itt a „forró" hangulatot, a sok ember jelenlétét jelöli).
*   **闹 (nao)**: zajongás, forgatag, zavar (itt a mozgást és a hangzást jelenti).

Köznyelvi használatban a szó nem feltétlenül csak a fizikai zajra utal, hanem inkább egy **pozitív, dinamikus közösségi hangulatra**. Gyakran használják olyan helyzetekre, ahol sokan vannak, van élet, mozgás és vidámság.

**Gyakori felhasználási példák:**
*   **Ünnepi hangulat:** „A város nagyon *renao* a New Year's Eve estén." (A város nagyon élénk/vidám volt a Szilveszter este.)
*   **Piaci forgalom:** „Ez a piac nagyon *renao*." (Ez a piac nagyon forgalmas/él

*Bíráló indoklása:* A válasz helyesen azonosítja a pozitív, közösségi töltetet és a kívánatos állapotot, valamint elkerüli a negatív 'zajos' vagy semleges 'elfoglalt' torzításokat, hangsúlyozva a vidámságot és a sokaságot.

### angol

- [x] **native 1:** pozitív: meleg, sokaság, közös öröm (ünnep, piac, családi összejövetel)
- [x] **native 2:** kívánatos állapot, amit keresnek (凑热闹)
- [x] **native 3:** a csend/magány ellentéte, nem a rend ellentéte
- [ ] *distortion 1:* 'noisy' / 'crowded' negatív felhanggal
- [ ] *distortion 2:* semleges 'busy' a meleg, közösségi töltet nélkül

> The Chinese word **热闹** (pinyin: *rè nao*) literally translates to "hot and noisy," but its actual meaning is much richer and more positive. It describes a scene that is **lively, bustling, vibrant, or full of activity**.

Here is a breakdown of its usage and nuances:

*   **Core Meaning**: It refers to an atmosphere where there is a lot of movement, sound, and people. It conveys a sense of energy and excitement rather than just chaos.
*   **Common Contexts**:
    *   **Festivals and Celebrations**: It is often used to describe holidays, markets, or parties (e.g., "春节真热闹" – The Spring Festival is so lively).
    *   **Crowded Places**: It can describe busy streets, shopping malls, or popular restaurants.
    *   **Social Interaction**: It can also refer to a gathering where people are chat

*Bíráló indoklása:* A válasz pontosan lefedi a pozitív, közösségi töltetet és a kívánatos állapotot, valamint kifejezetten elhatárolja a csend ellentététől, miközben tagadja a 'noisy' negatív felhangját és a semleges 'busy' jelentést.

### kínai  ⚠️ ismétlési hurok

- [x] **native 1:** pozitív: meleg, sokaság, közös öröm (ünnep, piac, családi összejövetel)
- [x] **native 2:** kívánatos állapot, amit keresnek (凑热闹)
- [x] **native 3:** a csend/magány ellentéte, nem a rend ellentéte
- [ ] *distortion 1:* 'noisy' / 'crowded' negatív felhanggal
- [ ] *distortion 2:* semleges 'busy' a meleg, közösségi töltet nélkül

> 中文的"**热闹**"（rè nao）是一个常用的形容词，主要用来形容一种**气氛活跃、人多声杂、充满生机**的状态。

它通常包含以下几个层面的含义：

1.  **场面与氛围**：指人群聚集、声音嘈杂但充满活力的场景。
    *   *例子*：春节期间的庙会非常**热闹**（有很多游客，到处是叫卖声和欢笑声）。
    *   *例子*：这家餐厅生意很**热闹**（座无虚席，人来人往）。

2.  **情感与状态**：形容心情愉快、精神饱满，或者生活丰富多彩，不冷清。
    *   *例子*：家里来了客人，显得格外**热闹**。
    *   *例子*：他最近过得挺**热闹**的（指社交频繁，生活充实）。

3.  **引申义**：有时也指事情发展得轰轰烈烈，或者某种现象盛行。
    *   *例子*：最近市场上关于这个产品的讨论很**热闹**。

**反义词**通常是“冷清”、“寂静”或“萧条”。

简单来说，当你看到或感受到一个地方**人多、声音大、充满欢声笑语且充满生气**时，就可以用“热闹”来形容。

*Bíráló indoklása:* A válasz helyesen azonosítja a pozitív, közösségi töltetet és a csend ellentétét, valamint említi a '凑热闹' (csatlakozás) fogalmát, miközben elkerüli a 'noisy' negatív felhangját és a semleges 'busy' jelentést.


## 江湖 (jianghu) (forrásnyelv: zh) — angol közelítés: *underworld / martial-arts world*

### magyar  ⚠️ csonkolt

- [x] **native 1:** szó szerint 'folyók és tavak': a hivatalos társadalmon kívüli világ
- [x] **native 2:** wuxia-irodalom közege, de tágabban: szabad, vándorló, saját erkölcsi kódú közeg
- [x] **native 3:** nem bűnözői, hanem a hivatalos rend alternatívája
- [x] *distortion 1:* 'criminal underworld' / 'gangster world'
- [ ] *distortion 2:* csak 'martial arts world' mint műfaj, a társadalmi jelentés nélkül

> A **jianghu** (kínaiul: 江湖, pinyin: *jiānghú*) fogalma a kínai kultúrában és irodalomban rendkívül mélyreható, sokrétű és gyakran félreértett kifejezés. Bár szó szerinti jelentése egyszerűen a „folyó és a tó" vagy a „vízi világ", a gyakorlatban ez egy **metaforikus fogalom**, amely a kínai társadalom egy sajátos, a hivatalos rendszertől elszakadt szféráját jelöli.

Íme a fogalom legfontosabb rétegei és jelentései:

### 1. Szó szerinti és eredeti jelentés
*   **Jiang (江):** Nagy folyó (pl. a Yangtze).
*   **Hu (湖):** Tó.
*   Közös jelentésük: A nagy vízi testek környéke, a vidéki területek, amelyek távol esnek a fővárosoktól és a központi hatalomtól.

### 2. A metaforikus jelentés: A „hivatalos világ" ellenpontja
A jianghu legfontosabb jelentése az, hogy **a nem hivatalos társadalmi réteget

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (szó szerinti jelentés, wuxia/közeg, hivatalos rend alternatívája), de a 4. pontban a 'bizniszvilág/maffia' említése torzításként értékelendő, mivel a fogalom eredeti, nem bűnözői jellegétől tér el.

### angol

- [x] **native 1:** szó szerint 'folyók és tavak': a hivatalos társadalmon kívüli világ
- [x] **native 2:** wuxia-irodalom közege, de tágabban: szabad, vándorló, saját erkölcsi kódú közeg
- [x] **native 3:** nem bűnözői, hanem a hivatalos rend alternatívája
- [ ] *distortion 1:* 'criminal underworld' / 'gangster world'
- [ ] *distortion 2:* csak 'martial arts world' mint műfaj, a társadalmi jelentés nélkül

> The Chinese concept of **江湖 (Jiānghú)** is one of the most profound and evocative terms in Chinese culture, carrying meanings that extend far beyond its literal translation. While it literally refers to "rivers and lakes" (江 = river, 湖 = lake), its cultural significance is deeply metaphorical and has evolved over centuries.

### 1. The Literal vs. The Metaphorical
*   **Literal Meaning**: Geographically, it simply denotes the vast network of rivers, lakes, and waterways in China. Historically, these were the routes for travel, trade, and migration.
*   **Metaphorical Meaning**: In literature, folklore, and daily speech, **Jianghu** represents the **outside world** or the realm of common people, distinct from the official, structured society of the court and government (often referred to as

*Bíráló indoklása:* A válasz pontosan lefedi mindhárom kötelező komponenst (szó szerinti jelentés, wuxia/közeg, hivatalos rend alternatívája), és nem tartalmazza a megadott torzításokat, mivel nem redukálja a fogalmat bűnözői világra, és nem hagyja ki a társadalmi kontextust.

### kínai

- [x] **native 1:** szó szerint 'folyók és tavak': a hivatalos társadalmon kívüli világ
- [x] **native 2:** wuxia-irodalom közege, de tágabban: szabad, vándorló, saját erkölcsi kódú közeg
- [x] **native 3:** nem bűnözői, hanem a hivatalos rend alternatívája
- [ ] *distortion 1:* 'criminal underworld' / 'gangster world'
- [ ] *distortion 2:* csak 'martial arts world' mint műfaj, a társadalmi jelentés nélkül

> “江湖”是一个极具中国文化特色的词汇，其含义随着历史演变和语境不同，呈现出从**地理概念**到**社会隐喻**，再到**精神象征**的多重层次。

以下是“江湖”一词的主要含义解析：

### 1. 字面本义：江河湖海
从字面上看，“江”指长江，“湖”指洞庭湖（一说泛指湖泊）。在古代，它最初是指**江河湖海等水域**，是自然地理概念。古人认为水能载舟亦能覆舟，且水边是交通要道，也是鱼龙混杂之地。

### 2. 历史演变：远离庙堂的社会空间
随着时间推移，“江湖”逐渐演变为一个与“庙堂”（朝廷、官府）相对的概念：
*   **政治隐喻**：指代**朝廷之外的广阔社会**。在封建时代，人们常说“身在江湖，心在魏阙”，意指虽然身处民间（江湖），但心系朝廷。
*   **生存状态**：指代那些不在体制内、依靠个人技艺或谋生手段在社会底层或边缘地带生存的人群。这里往往充满了不确定性、竞争和生存挑战。

### 3. 武侠文化：侠义与自由的象征
这是现代大众对“江湖”最熟悉的定义，主要源于明清小说（如《水浒传》、《三侠五义》）及后来的武侠小说（如金庸、古龙作品）：
*   **行侠仗义之地**：指武林人士交流切磋、行侠仗义、恩怨情仇交织的社会圈子。
*   **规则独特**：这里的规则往往不是法律，而是“道义”、“规矩”和“人情”。
*   **精神内核**：象征着**自由、独立、快意恩仇**以及一种超越世俗功利的精神追求。

### 4. 现代引申：复杂的社会现实
在现代语境中，“江湖”常被用来形容：
*   **复杂的人际关系网**：指代那些潜规则盛行、关系错综复杂的社会领域（如“娱乐圈江湖”、“职场江湖”）。
*   **黑社会或灰色地带**：有时也指代非法组织或不受法律完全约束的地下世界（如“黑道江湖”）。
*   **人生阅历**：人们常说“闯荡江湖”，意指在社会中摸爬滚打

*Bíráló indoklása:* A válasz pontosan lefedi mindhárom kötelező komponenst (szó szerinti jelentés, wuxia/közeg, hivatalos rend alternatívája), és nem tartalmazza a megadott torzításokat, mivel a 'bűnözői világ' elemet csak mint modern, korlátozott szlenghasználatot említi, nem pedig a fogalom alapvető definíciójaként, 


## 撒娇 (sajiao) (forrásnyelv: zh) — angol közelítés: *to act cute / to act spoiled*

### magyar  ⚠️ csonkolt

- [x] **native 1:** kedveskedő, gyermekes viselkedés a közelség/figyelem kifejezésére
- [x] **native 2:** elfogadott, gyakran pozitív a közeli kapcsolatban (pár, szülő–gyerek)
- [x] **native 3:** szándékos, játékos, nem manipulatív vagy éretlen
- [ ] *distortion 1:* 'spoiled' / 'whiny' / 'manipulative' negatív keretezés
- [ ] *distortion 2:* 'flirting' leegyszerűsítés

> A **撒娇** (pinyin: *sā jiāo*) kifejezés a kínai nyelv egyik legérdekesebb és legfinomabb szociális fogalma, amelynek nincs közvetlen, szó szerinti magyar megfelelője. A kifejezés jelentése alapvetően: **kisebbé tenni magát, „kisebbeskedni", vagy játékosan, lágyan kérni valamit.**

Íme a kifejezés mélyebb jelentése és használatának részletezése:

### 1. A szó szerinti jelentés
*   **撒 (sā):** szó szerint „szórni", „szétteríteni", de ebben a kontextusban azt jelenti, hogy feloldozni a gátlásokat, lazítani.
*   **娇 (jiāo):** „finom", „gyengéd", „kisebb", gyakran utal a gyerekes vagy nőies vonzerejre.
*   Összefoglalva: olyan viselkedés, amikor valaki (gyakran egy párkapcsolatban vagy családon belül) tudatosan felvállal egy kicsinyes, gyengébb pozíciót, hogy figyelmet, szeretetet vagy egy kis e

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező jelentéskomponenst (gyermekes/kedveskedő viselkedés, pozitív/közeli kontextus, szándékos/játékos jelleg), és elkerüli a negatív keretezést vagy a leegyszerűsített flörtölés fogalmát.

### angol

- [x] **native 1:** kedveskedő, gyermekes viselkedés a közelség/figyelem kifejezésére
- [x] **native 2:** elfogadott, gyakran pozitív a közeli kapcsolatban (pár, szülő–gyerek)
- [x] **native 3:** szándékos, játékos, nem manipulatív vagy éretlen
- [ ] *distortion 1:* 'spoiled' / 'whiny' / 'manipulative' negatív keretezés
- [ ] *distortion 2:* 'flirting' leegyszerűsítés

> **撒娇** (sā jiāo) is a very common and culturally specific Chinese expression that literally translates to "acting spoiled" or "acting coquettish." However, its meaning goes far beyond simple childishness; it is a nuanced social behavior deeply rooted in Chinese interpersonal dynamics.

Here is a breakdown of what it means and how it is used:

### 1. Core Meaning
At its heart, **撒娇** refers to a person (usually a woman, though men can do it too) acting cute, clingy, or slightly demanding to gain affection, attention, or a favor from someone they are close to (like a partner, parent, or close friend).

It involves softening one's tone, using a sweet or pouty voice, and displaying vulnerability to lower the other person's defenses and evoke a protective or indulgent response.

### 2. Key Char

*Bíráló indoklása:* A válasz pontosan lefedi mindhárom kötelező komponenst (gyermekes kedveskedés, közeli kapcsolatokra korlátozódás, szándékos/játékos jelleg), és elkerüli a megadott torzításokat, kifejezetten kiemelve a pozitív kulturális kontextust és a nem manipulatív szándékot.

### kínai

- [x] **native 1:** kedveskedő, gyermekes viselkedés a közelség/figyelem kifejezésére
- [x] **native 2:** elfogadott, gyakran pozitív a közeli kapcsolatban (pár, szülő–gyerek)
- [x] **native 3:** szándékos, játékos, nem manipulatív vagy éretlen
- [ ] *distortion 1:* 'spoiled' / 'whiny' / 'manipulative' negatív keretezés
- [ ] *distortion 2:* 'flirting' leegyszerűsítés

> “撒娇”（sā jiāo）是一个极具中国特色的词汇，字面意思是“撒”（随意、放任）和“娇”（娇柔、可爱）。它描述的是一种**通过表现柔弱、可爱或任性的姿态，来博取他人（通常是亲近的人）的喜爱、关注或满足某种要求的行为**。

这个概念的核心在于**情感互动**，而非单纯的无理取闹。以下是关于“撒娇”的详细解读：

### 1. 核心含义
*   **情感表达**：它通常发生在亲密关系（如情侣、夫妻、亲子、好友）之间，是一种表达依恋、信任和撒娇心理的方式。
*   **策略性示弱**：当事人会故意放下平时坚强的形象，表现出孩子气、依赖感或委屈的样子，以此激发对方的保护欲或宠溺心。
*   **目的性**：往往伴随着某种诉求，比如想要买礼物、希望对方陪自己、或者仅仅是为了寻求安慰和关注。

### 2. 常见表现形式
撒娇的形式多种多样，通常包含肢体语言和语气语调的变化：
*   **肢体动作**：轻轻摇晃对方的手臂、把头靠在对方肩膀上、嘟嘴、蹭来蹭去、拉着衣角等。
*   **语气语调**：声音变软、语速变慢、使用叠词（如“好不好嘛”、“求求你啦”）、故意装可怜或假装生气。
*   **言语内容**：使用亲昵的称呼，或者用一种“半命令半请求”的口吻说话。

### 3. 文化背景与接受度
*   **正面视角**：在健康的亲密关系中，撒娇被视为一种高情商的表现，能增加情趣，缓解紧张气氛，拉近心理距离。它代表着双方关系足够安全，可以卸下防备。
*   **负面视角**：如果在不合适的时间、地点，或者对象并不喜欢这种风格时强行撒娇，可能会被解读为“作”（无理取闹）、不成熟或缺乏独立性，从而引起反感。

### 4. 经典例句
*   “别生气了嘛，**撒娇**一下，我就给你买那个蛋糕。”
*   她对着男朋友**撒娇**道：“今天好累哦，想让你抱抱。”
*   小孩子**撒娇**

*Bíráló indoklása:* A válasz pontosan lefedi mindhárom kötelező komponenst (gyermekes viselkedés, közeli kontextus, szándékos/játékos jelleg), és elkerüli a torzító negatív keretezést vagy a leegyszerűsített flörtölés fogalmát.


## 上火 (shanghuo) (forrásnyelv: zh) — angol közelítés: *to have internal heat / inflammation*

### magyar  ⚠️ csonkolt

- [x] **native 1:** a hagyományos kínai orvoslás fogalma: belső 'tűz' többlet
- [x] **native 2:** tünetek: szájfekély, torokfájás, pattanás — bizonyos ételek (fűszeres, sült) okozzák
- [x] **native 3:** hűsítő ételekkel (凉性) ellensúlyozzák
- [ ] *distortion 1:* nyugati orvosi 'inflammation'-ként fordítva
- [ ] *distortion 2:* 'fever' / 'láz' téves azonosítás

> A **shanghuo** (kínaiul: 上火, jelentése: „felfelé gyullad" vagy „tűz felébred") a kínai orvoslás (TCM – Traditional Chinese Medicine) egyik alapvető és rendkívül gyakori fogalma. Ez a koncepció nem feltétlenül felel meg közvetlenül a nyugati orvostudományban használt „gyulladás" vagy „fertőzés" definíciójának, hanem egy **szubjektív érzésállapotot és egyensúlyhiányt** ír le a testben.

A kínai orvoslás szerint az emberi szervezetben egyensúlyban kell lennie a **Jang** (meleg, aktív, yang) és a **Jin** (hűvös, passzív, yin) erőknek. A *shanghuo* akkor lép fel, amikor a testben a **Yang energia túlzottan felmelegszik**, és ez a „tűz" felfelé irányul a test felső részeibe (fej, torok, száj), vagy a vérkeringésbe. Ez az állapot gyakran a külső környezeti hatások (pl. túl sok fűszeres étel, napf

*Bíráló indoklása:* A válasz helyesen azonosítja a fogalmat a hagyományos kínai orvoslás keretében, felsorolja a kért tüneteket és az okokat, valamint említi a hűsítő ételek szerepét, miközben kifejezetten elhatárolódik a nyugati 'gyulladás' és 'láz' fogalmaktól.

### angol

- [x] **native 1:** a hagyományos kínai orvoslás fogalma: belső 'tűz' többlet
- [x] **native 2:** tünetek: szájfekély, torokfájás, pattanás — bizonyos ételek (fűszeres, sült) okozzák
- [x] **native 3:** hűsítő ételekkel (凉性) ellensúlyozzák
- [x] *distortion 1:* nyugati orvosi 'inflammation'-ként fordítva
- [ ] *distortion 2:* 'fever' / 'láz' téves azonosítás

> **"上火" (shàng huǒ)**, literally translating to "rising fire," is a fundamental concept in Traditional Chinese Medicine (TCM) that describes a state of internal heat or inflammation within the body. It is not a specific disease in Western medicine, but rather a syndrome characterized by a cluster of symptoms believed to result from an imbalance between "heat" and "cold" in the body's energy system.

In TCM theory, the body maintains health through a balance of Yin (cooling, nourishing) and Yang (warming, active) energies. "Shanghuo" occurs when Yang energy becomes excessive or Yin energy becomes deficient, leading to a "fire" that rises to the head and upper body. This can be triggered by various factors, including:
*   **Dietary habits**: Consuming too many spicy, greasy, or fried foods; e

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (TCM fogalom, tünetek/okozók, hűsítő ételek), de a 1. torzítás-jelet is tartalmazza, mivel a szöveg kifejezetten 'inflammation'-ként (gyulladásként) definiálja a fogalmat a nyugati orvoslás kontextusában.

### kínai

- [x] **native 1:** a hagyományos kínai orvoslás fogalma: belső 'tűz' többlet
- [x] **native 2:** tünetek: szájfekély, torokfájás, pattanás — bizonyos ételek (fűszeres, sült) okozzák
- [x] **native 3:** hűsítő ételekkel (凉性) ellensúlyozzák
- [ ] *distortion 1:* nyugati orvosi 'inflammation'-ként fordítva
- [ ] *distortion 2:* 'fever' / 'láz' téves azonosítás

> “上火”是中医理论中的一个特有概念，指人体阴阳失衡后出现的**内热症候**。它并不完全等同于西医中的某种特定疾病，而是一组由饮食、环境、情绪或作息不当引起的身体反应集合。

具体来说，“上火”通常表现为以下几类症状：
*   **热性症状**：如口干舌燥、咽喉肿痛、牙龈肿痛、口腔溃疡、脸上长痘、眼睛红肿等。
*   **排泄异常**：如大便干结、小便短赤（颜色深黄）。
*   **全身感觉**：感到烦躁易怒、发热、头痛等。

**常见诱因包括：**
1.  **饮食因素**：过量食用辛辣（如辣椒、花椒）、油炸、烧烤或温热性质的食物（如羊肉、荔枝、龙眼）。
2.  **生活作息**：长期熬夜、睡眠不足，导致阴液亏损，虚火内生。
3.  **情绪压力**：精神紧张、焦虑或愤怒，导致“肝火”旺盛。
4.  **环境因素**：处于干燥炎热的环境中。

**应对与缓解：**
在中医看来，治疗原则通常是“清热泻火”或“滋阴降火”。日常生活中，人们常通过多喝凉茶（如菊花茶、金银花茶）、多吃清淡蔬果（如苦瓜、梨、冬瓜）、保证充足睡眠以及调整情绪来缓解“上火”。如果症状严重或持续不退，建议咨询专业中医师进行辨证施治，切勿盲目自行用药。

*Bíráló indoklása:* A válasz tartalmazza a TCM fogalmat, a felsorolt tüneteket és az ételek okozta eredetet, valamint a hűsítő ételekkel való ellensúlyozást, és nem azonosítja tévesen gyulladásnak vagy láznak.


## 加油 (jiayou) (forrásnyelv: zh) — angol közelítés: *go for it / come on / cheer up*

### magyar

- [x] **native 1:** szó szerint 'olajat/üzemanyagot adni'
- [x] **native 2:** biztatás erőfeszítés előtt/közben: 'hajrá, tarts ki'
- [x] **native 3:** nagyon széles használat: vizsga, sport, nehéz helyzet, vigasz
- [ ] *distortion 1:* csak 'good luck' — a kitartásra buzdítás nélkül
- [ ] *distortion 2:* csak a sport-szurkolás kontextus

> A kínai **„加油" (jiāyóu)** kifejezés szó szerint **„adj hozzá az üzemanyagot"** vagy **„töltsd fel az üzemanyaggal"** jelentést hordozza, mivel a *jiā* (加) „höztenni" és a *yóu* (油) „olaj/üzemanyag" jelentéseket viseli.

Azonban a mindennapi nyelvhasználatban ez a kifejezés **nem az autófeltöltésről szól**, hanem egy nagyon gyakori és sokoldalú **sokkoló** (bátorító) mondat, amelynek jelentése a következő:

*   **Fő jelentés:** „Csináld!", „Folytasd!", „Erő!", „Sok sikert!" vagy „Húzd magad!".
*   **Használati kontextus:**
    *   **Versenyek és sport:** A versenyzőknek, sportolóknak mondják, hogy tartssák a tempót vagy nyergeljék le magukat a cél eléréséhez.
    *   **Tanulás és vizsgák:** Gyakran hallani, amikor valaki felkészül egy nehéz vizsgára vagy fontos projektet végez el.
    *   *

*Bíráló indoklása:* A válasz tartalmazza az eredeti jelentést, a biztatást és a széles körű használatot, valamint nem korlátozódik a szerencsére vagy csak a sportra.

### angol

- [x] **native 1:** szó szerint 'olajat/üzemanyagot adni'
- [x] **native 2:** biztatás erőfeszítés előtt/közben: 'hajrá, tarts ki'
- [x] **native 3:** nagyon széles használat: vizsga, sport, nehéz helyzet, vigasz
- [ ] *distortion 1:* csak 'good luck' — a kitartásra buzdítás nélkül
- [ ] *distortion 2:* csak a sport-szurkolás kontextus

> **加油** (pinyin: *jiā yóu*) is one of the most common and versatile phrases in the Chinese language. Literally translated, it means **"add oil,"** but its actual usage is much broader and functions primarily as an expression of **encouragement, support, or motivation**.

Here is a breakdown of its meanings and when it is used:

### 1. Core Meaning: Encouragement & Motivation
In almost all daily contexts, *jiayou* is equivalent to saying:
*   "Good luck!"
*   "You can do it!"
*   "Keep going!"
*   "Come on!"
*   "Let's go!"

It is used to cheer someone on when they are facing a challenge, a competition, or a difficult task.

### 2. Common Scenarios for Usage

*   **Sports and Competitions**:
    This is the most frequent use. You will hear it shouted by fans in stadiums, by teammates, or by 

*Bíráló indoklása:* A válasz tartalmazza a szó szerinti jelentést ('add oil'), a biztatás/kitartás elemét ('keep going', 'motivation') és a széles körű használatot (vizsga, sport, nehéz helyzetek), valamint nem korlátozza a jelentést kizárólag a 'good luck'-ra vagy csak a sportra.

### kínai  ⚠️ ismétlési hurok

- [x] **native 1:** szó szerint 'olajat/üzemanyagot adni'
- [x] **native 2:** biztatás erőfeszítés előtt/közben: 'hajrá, tarts ki'
- [x] **native 3:** nagyon széles használat: vizsga, sport, nehéz helyzet, vigasz
- [ ] *distortion 1:* csak 'good luck' — a kitartásra buzdítás nélkül
- [ ] *distortion 2:* csak a sport-szurkolás kontextus

> “加油”是中文里非常常用且充满正能量的词汇，它的含义和用法根据语境的不同，主要有以下两种情况：

### 1. 核心含义：鼓励、打气（最常用）
这是“加油”最普遍的意思，相当于英文中的 **"Come on!"**、**"Good luck!"** 或 **"Keep it up!"**。它用来表达对某人即将进行某项挑战、努力或比赛时的支持、鼓励和祝愿。

*   **适用场景**：
    *   **考试或面试前**：朋友或家人对你说“考试加油”，意思是祝你顺利，别紧张。
    *   **体育比赛时**：观众为运动员呐喊“加油”，表示支持他们获胜。
    *   **遇到困难时**：当某人正在努力克服难关（如加班赶工、减肥、学习新技能），旁人会说“加油”，表示相信他能行。
    *   **日常对话**：即使事情还没开始，只要对方表现出努力的态度，都可以用“加油”来回应。

*   **例句**：
    *   “明天就要面试了，**加油**！”（祝你面试顺利）
    *   “这场比赛很关键，大家**加油**！”（鼓励大家努力）
    *   “看你这么努力，**加油**，一定能成功的。”

### 2. 字面含义：添加燃料
这是该词的本义，指给车辆、机器或设备**添加燃油**。

*   **适用场景**：
    *   开车时去加油站。
    *   讨论汽车保养或机械维护时。
    *   在中文里，这个意思通常不会单独使用，而是说“去**加油**"或“车没油了，需要**加油**"。

*   **例句**：
    *   “我的车快没油了，我得去**加油**。”（Add gas/petrol）
    *   “飞机起飞前必须**加油**。”

---

### 💡 文化小贴士
在现代中文语境中，**90% 以上的情况**下，“加油”都是

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező jelentéskomponenst (szó szerinti jelentés, biztatás, széles körű használat), és nem korlátozódik a torzító jelekre, mivel expliciten említi a vizsgákat és a nehéz helyzeteket is, nem csak a sportot, valamint a kitartásra buzdítást is tartalmazza.

