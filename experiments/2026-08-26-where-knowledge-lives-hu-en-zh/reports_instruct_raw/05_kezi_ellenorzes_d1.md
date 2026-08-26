# Kézi ellenőrző ív — D1 (48 UNT-válasz)

Komponensenként látod a bíráló döntését. Ahol egyetértesz, nincs teendő; ahol nem, add meg a
`code/set_manual.py`-nak a HELYES darabszámot:
`python3 code/set_manual.py d <item> <nyelv> --native N --distortion M`,
majd `python3 code/analyze_d.py`.

⛔ A `d1_scores.csv`-t **ne szerkeszd kézzel** — a 08-24-i körben így csúszott el az
UNT-ZH08 `native_n` nevezője. A felvitel a `set_manual.py`-n megy; a parancsok alább,
a bíráló darabszámaival előkitöltve.

```bash
python3 code/set_manual.py d UNT-HU01  hu --native 1 --distortion 0
python3 code/set_manual.py d UNT-HU01  en --native 1 --distortion 1
python3 code/set_manual.py d UNT-HU01  zh --native 1 --distortion 2
python3 code/set_manual.py d UNT-HU02  hu --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU02  en --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU02  zh --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU03  hu --native 1 --distortion 0
python3 code/set_manual.py d UNT-HU03  en --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU03  zh --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU04  hu --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU04  en --native 3 --distortion 1
python3 code/set_manual.py d UNT-HU04  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU05  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU05  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU05  zh --native 2 --distortion 1
python3 code/set_manual.py d UNT-HU06  hu --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU06  en --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU06  zh --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU07  hu --native 3 --distortion 1
python3 code/set_manual.py d UNT-HU07  en --native 2 --distortion 0
python3 code/set_manual.py d UNT-HU07  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-HU08  hu --native 0 --distortion 2
python3 code/set_manual.py d UNT-HU08  en --native 2 --distortion 1
python3 code/set_manual.py d UNT-HU08  zh --native 2 --distortion 1
python3 code/set_manual.py d UNT-ZH01  hu --native 2 --distortion 0
python3 code/set_manual.py d UNT-ZH01  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH01  zh --native 0 --distortion 0
python3 code/set_manual.py d UNT-ZH02  hu --native 1 --distortion 1
python3 code/set_manual.py d UNT-ZH02  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH02  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH03  hu --native 2 --distortion 1
python3 code/set_manual.py d UNT-ZH03  en --native 2 --distortion 1
python3 code/set_manual.py d UNT-ZH03  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH04  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH04  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH04  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH05  hu --native 2 --distortion 0
python3 code/set_manual.py d UNT-ZH05  en --native 3 --distortion 1
python3 code/set_manual.py d UNT-ZH05  zh --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH06  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH06  en --native 3 --distortion 1
python3 code/set_manual.py d UNT-ZH06  zh --native 2 --distortion 0
python3 code/set_manual.py d UNT-ZH07  hu --native 2 --distortion 1
python3 code/set_manual.py d UNT-ZH07  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH07  zh --native 2 --distortion 0
python3 code/set_manual.py d UNT-ZH08  hu --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH08  en --native 3 --distortion 0
python3 code/set_manual.py d UNT-ZH08  zh --native 3 --distortion 0
```


## kaláka (forrásnyelv: hu) — angol közelítés: *mutual aid / barn raising / helping out*

### magyar

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [x] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [ ] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [ ] *distortion 2:* 'volunteering'/'charity' keretezés

> A kaláka egy olyan közösségi tevékenység, amelyben a résztvevők közösen dolgoznak, általában földművelésben, építkezésben vagy más közös célok érdekében. A szó eredetileg a „kalász" szóból származik, ami a gabonaszemre utal, és a közösségi munka jelképe. A kaláka során a résztvevők gyakran énekelnek, táncolnak és más kulturális tevékenységeket is végeznek, hogy a munka ne legyen unalmas.

*Bíráló indoklása:* A válasz tartalmazza a közösségi és szervezett jelleg komponenst, de hiányzik belőle a kölcsönösség és a fizetség nélküli, de elvárt visszasegítés lényegi eleme, valamint nem tartalmaz torzító elemeket.

### angol  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [x] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [x] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [ ] *distortion 2:* 'volunteering'/'charity' keretezés

> The Hungarian word **kaláka** means **a group of friends**, **a gathering**, or **a party**.

It is often used to describe a casual social meeting where people get together to chat, drink, or play games. The word is also the root of the English word **cackle** (via the German *Klatsch* or similar loanwords, though the direct etymological link is debated, the phonetic similarity is noted in some linguistic discussions). However, in modern Hungarian usage, it strictly refers to a social gathering or a group of friends.

It is worth noting that the word is also used in the context of **kaláka** (a type of traditional Hungarian folk song or dance) and in the phrase **kaláka** (a group of people working together, often in a playful or informal manner).

In summary, the most common and direct tr

*Bíráló indoklása:* A modell a 'kaláka' szót társasági összejövetelre fordította, így hiányzik a kölcsönös segítségnyújtás és a fizetség nélküli munka lényegi eleme, miközben az egyszeri, viszonzás nélküli jótett torzítást is jelen van a definícióban.

### kínai  ⚠️ ismétlési hurok, önértékelő toldalék levágva

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [x] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [x] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [x] *distortion 2:* 'volunteering'/'charity' keretezés

> 匈牙利语“kaláka”一词的意思是“**共同出资**”，指一群人为了共同目的（如购买礼物、举办活动或庆祝节日）而共同筹集资金或物资。

在匈牙利文化中，这个词通常与**集体合作**和**互助**精神相关。例如，在圣诞节期间，人们可能会组织“kaláka”来为贫困家庭购买礼物，或者在婚礼、生日等场合共同出资购买礼物。

此外，“kaláka”也可以指**共同出资购买的物品**，比如大家凑钱买的一辆车、一台电视等。

总结来说，“kalá”是一个体现匈牙利人**团结互助**精神的词汇，强调通过集体努力达成共同目标。

*Bíráló indoklása:* A válasz a 'kaláka' fogalmat tévesen 'közös pénzügyi hozzájárulásként' definiálja, így hiányzik a kölcsönös segítségnyújtás és a fizetség nélküli munka lényegi eleme, miközben a jótékonysági/önkéntes keretezés torzítást is tartalmaz.


## szeretet / szerelem (forrásnyelv: hu) — angol közelítés: *love*

### magyar  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** két külön szó: szeretet (tág, nem erotikus) és szerelem (romantikus, párkapcsolati)
- [x] **native 2:** a szerelem a szeretet egy fajtája, de nem fordítva
- [ ] *distortion 1:* a kettő összemosása egyetlen 'love'-ként
- [ ] *distortion 2:* nem említi, hogy a magyar megkülönbözteti

> A „szeretet” és a „szerelem” szavak közötti különbség a következő:
A „szeretet” egy általánosabb fogalom, amely bármilyen pozitív érzést, érzelmeket és cselekedeteket jelenthet. Ez lehet a barátság, a család, a társadalom, a természet iránti szeretet, vagy akár az önmagunk iránti szeretet is. A szeretet egyfajta alapvető emberi érzés, amely mindenki számára fontos és szükséges.
A „szerelem” egy specifikusabb fogalom, amely általában a romantikus kapcsolatokra, a párkapcsolatokra, a szexualitásra és a fizikai vonzalomra utal. A szerelem egyfajta intenzív érzés, amely gyakran a test és a lélek közötti kapcsolatot jelenti. A szerelem gyakran a szeretet egyfajta kifejeződése, de nem minden szeretet szerelem.
Összefoglalva, a szeretet egy általánosabb fogalom, amely bármilyen pozitív érzést, ér

*Bíráló indoklása:* A válasz tisztán megkülönbözteti a két fogalmat, kifejezetten jelölve a hierarchiát és a nem-ekvivalenciát, így nem mosza össze őket, és kiemeli a magyar nyelv sajátosságát.

### angol

- [x] **native 1:** két külön szó: szeretet (tág, nem erotikus) és szerelem (romantikus, párkapcsolati)
- [x] **native 2:** a szerelem a szeretet egy fajtája, de nem fordítva
- [ ] *distortion 1:* a kettő összemosása egyetlen 'love'-ként
- [ ] *distortion 2:* nem említi, hogy a magyar megkülönbözteti

> The difference between **szeretet** and **szerelem** lies in the depth, nature, and context of the love they describe. While both translate to "love" in English, they represent distinct emotional states in Hungarian culture and language.

Here is a breakdown of the differences:

### 1. Szeretet (Love as a Virtue/Action)
*   **Meaning:** This refers to **affection, kindness, benevolence, and caring**. It is often described as "loving-kindness."
*   **Nature:** It is a conscious choice and an action. It implies a willingness to do good for someone, regardless of whether they are a romantic partner, a friend, a family member, or even a stranger.
*   **Context:** You can have *szeretet* for your parents, your children, your friends, and even for humanity in general. It is the foundation of a h

*Bíráló indoklása:* A válasz expliciten megkülönbözteti a két fogalmat, leírva a szeretet tágabb, nem erotikus jellegét és a szerelem romantikus, intenzív természetét, valamint utal arra is, hogy a szerelem a szeretet egy fajtája vagy kiegészítője, így elkerülve az összemosást.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** két külön szó: szeretet (tág, nem erotikus) és szerelem (romantikus, párkapcsolati)
- [x] **native 2:** a szerelem a szeretet egy fajtája, de nem fordítva
- [ ] *distortion 1:* a kettő összemosása egyetlen 'love'-ként
- [ ] *distortion 2:* nem említi, hogy a magyar megkülönbözteti

> 这两个词在匈牙利语中都与“爱”有关，但它们的含义和用法有所不同。

1. **Szeretet**：
   - **含义**：指一种**深厚、无私、持久的爱**，通常用于描述亲情、友情或广义的博爱。它强调的是爱的**本质**和**深度**，而不是激情。
   - **用法**：常用于表达对他人的关怀、同情、宽恕和尊重。例如，“szeretet”可以用来形容父母对子女的爱，或者朋友之间的深厚情谊。
   - **例句**：
     - “A szeretet mindenki számára fontos.”（爱对每个人都很重要。）
     - “A szeretet nem kér semmit.”（爱是不求回报的。）
     - “A szeretet a legfontosabb erő.”（爱是最大的力量。）

2. **Szerelem**：
   - **英语**：指一种**激情、浪漫、强烈的爱**，通常用于描述恋人之间的爱情。它强调的是爱的**激情**和**强度**，而不是持久性。
   - **用法**：常用于表达浪漫关系中的情感，如爱情、迷恋、渴望等。
   - **例句**：
   - “A szerelem mindenki számára fontos.”（爱情对每个人都很重要。）
   - “A szerelem nem kér semmit.”（爱情是不求回报的。）
   - “A szerelem a legfontosabb erő.”（爱情是最大的力量。）

3. **区别总结**：
   - **Szeretet** 更侧重于**情感深度**和**持久性**，通常用于描述亲情、友情或广义的博爱。
   - **Szerelem** 更侧重于**激情**和**强度**，通常用于描述恋人之间的爱情。

4. **文化背景**：
   - 

*Bíráló indoklása:* A válasz külön kezeli a két szót és pontosan leírja a jelentésbeli különbséget, valamint nem említi össze őket egyetlen fogalomként, így elkerüli a megadott torzításokat.


## magázás / tegezés (forrásnyelv: hu) — angol közelítés: *formal vs informal 'you' (T–V distinction)*

### magyar

- [ ] **native 1:** igealakban és névmásban is megjelenik (ön/maga vs te)
- [ ] **native 2:** több fokozat: tegezés, magázás, önözés (és tetszikelés)
- [x] **native 3:** társadalmi távolság / tisztelet kódolása
- [ ] *distortion 1:* csak 'polite you' mint a francia vous — egyszintű
- [ ] *distortion 2:* csak névmás-különbségként írja le, az igeragozást nem említi

> A magázás és a tegezés a magyar nyelvben a megszólítások módját jelöli. A magázás tiszteletteljes, udvarias megszólítás, míg a tegezés barátságos, közvetlen megszólítás.

*Bíráló indoklása:* A válasz csak a társadalmi távolságot említi, hiányzik az igealakok és névmások szerinti ragozás, valamint a többfokozatúság (önözés) említése, és nem torzítja a fogalmat egyszintűsítéssel vagy kizárólag névmás-különbségre redukálással.

### angol

- [x] **native 1:** igealakban és névmásban is megjelenik (ön/maga vs te)
- [ ] **native 2:** több fokozat: tegezés, magázás, önözés (és tetszikelés)
- [x] **native 3:** társadalmi távolság / tisztelet kódolása
- [ ] *distortion 1:* csak 'polite you' mint a francia vous — egyszintű
- [ ] *distortion 2:* csak névmás-különbségként írja le, az igeragozást nem említi

> **Magázás** and **tegezés** are terms related to the levels of formality and respect used in the Hungarian language when addressing others.

Here is the breakdown of their meanings:

### 1. Magázás (The Formal "You")
*   **Meaning:** This refers to the use of the formal second-person singular pronoun, **"Ön"** (or sometimes "Maga").
*   **Context:** It is used to show respect, politeness, or social distance.
*   **When to use it:**
    *   Speaking to strangers (especially older people).
    *   Speaking to people in positions of authority (bosses, teachers, officials).
    *   In professional or business settings.
    *   When you do not know someone well.
*   **Grammar:** Verbs conjugated in the formal form (e.g., *Ön mit **eszik**?* vs. *Te mit **eszel**?*).

### 2. Tegezés (The Informa

*Bíráló indoklása:* A válasz tartalmazza az igealakok és névmások együttes használatát, valamint a társadalmi távolság kódolását, de hiányzik a többfokozatú rendszer (önözés/tetszikelés) említése, és nem torzítja a fogalmat egyszintűvé vagy kizárólag névmás-különbséggé.

### kínai  ⚠️ csonkolt, ismétlési hurok, önértékelő toldalék levágva

- [x] **native 1:** igealakban és névmásban is megjelenik (ön/maga vs te)
- [ ] **native 2:** több fokozat: tegezés, magázás, önözés (és tetszikelés)
- [x] **native 3:** társadalmi távolság / tisztelet kódolása
- [ ] *distortion 1:* csak 'polite you' mint a francia vous — egyszintű
- [ ] *distortion 2:* csak névmás-különbségként írja le, az igeragozást nem említi

> 在匈牙利语中，“magázás”和“tegezés”这两个词都与**称呼方式**有关，具体指的是**使用尊称（magázás）或昵称（tegezés）来称呼他人**。

1. **Magázás**：
   - **含义**：指使用尊称“**magá**”（如“tegnap”中的“te”）来称呼他人，通常用于表示**尊重、礼貌或正式场合**。
   - **用法**：在匈牙利语中，当需要表示对某人的尊重时，会使用“magázás”形式。例如，对长辈、上级、陌生人或不熟悉的人使用“magázás”。
   - **例子**：
     - “**Te** vagy a legjobb barátom.”（你是我最亲密的朋友。）——这里使用的是“tegezés”形式。
     - “**Ön** vagy a legjobb barátom.”（您是最亲密的朋友。）——这里使用的是“magázás”形式。

2. **Tegezés**：
   - **含义**：指使用昵称“**te**”来称呼他人，通常用于表示**亲密、随意或非正式场合**。
   - **动词形式**：在匈牙利语中，动词的变位也会根据称呼方式的不同而改变。例如，“**te** vagy”（你是）和“**ön** vagy”（您都是）。
   - **例子**：
     - “**Te** vagy a legjobb barátom.”（你是我最亲密的朋友。）——这里使用的是“tegezés”形式。
     - “**Ön** vagy a legjobb barátom.”（您是最亲密的朋友。）——这里使用的是“magázás”形式。

3. **区别**：
   - **Magázás**：用于表示尊重、礼貌或正式场合。
   - **Tegezés**：用于表示亲密、随意或非正式场合。

4. 

*Bíráló indoklása:* A válasz helyesen azonosítja az igealakok és névmások változását, valamint a társadalmi távolság kódolását, de hiányzik a többfokozatúság (önözés/tetszikelés) említése, és nem torzítja a fogalmat egyszintűvé vagy kizárólag névmás-különbséggé.


## puszi / csók (forrásnyelv: hu) — angol közelítés: *kiss*

### magyar

- [ ] **native 1:** puszi: arcra, üdvözlő, baráti/családi, nem romantikus
- [ ] **native 2:** csók: szájra, romantikus vagy ünnepélyes
- [ ] **native 3:** a magyar két külön szóval különbözteti meg
- [x] *distortion 1:* egyetlen 'kiss' fogalom, a különbség elmosva
- [x] *distortion 2:* 'puszi' mint 'kis csók' (méret szerinti, nem funkció szerinti különbség)

> A „puszi” általában a szájra vagy az arcra adott ölelést jelenti, míg a „csók” a szájra adott ölelést.

*Bíráló indoklása:* A válasz hibásan definiálja mindkét fogalmat 'ölelésként', teljesen figyelmen kívül hagyja a száj/arc és a romantikus/baráti megkülönböztetést, valamint tévesen egyetlen fogalomként kezeli a különbséget.

### angol

- [x] **native 1:** puszi: arcra, üdvözlő, baráti/családi, nem romantikus
- [x] **native 2:** csók: szájra, romantikus vagy ünnepélyes
- [x] **native 3:** a magyar két külön szóval különbözteti meg
- [ ] *distortion 1:* egyetlen 'kiss' fogalom, a különbség elmosva
- [x] *distortion 2:* 'puszi' mint 'kis csók' (méret szerinti, nem funkció szerinti különbség)

> The difference between **puszi** and **csók** in Hungarian lies primarily in the **intimacy** of the relationship and the **formality** of the situation.

Here is a breakdown of the differences:

### 1. Puszi (Puszis)
*   **Literal Meaning:** "Kiss" (diminutive form).
*   **Context:** This is the standard, everyday word for a kiss. It is used in almost all casual situations.
*   **Relationship:** It is used between friends, family members, colleagues, and children. It implies a friendly, warm, but non-romantic (or at least non-sexual) connection.
*   **Usage:**
    *   **Greetings/Goodbyes:** It is the most common way to say "kiss you" when hugging someone.
    *   **Children:** Parents often say "puszi" to their children.
    *   **Plural:** It is very common to say "puszi" multiple times

*Bíráló indoklása:* A válasz helyesen azonosítja a két fogalom funkcionális és kontextuális különbségeit, de tévesen értelmezi a 'puszi' etimológiáját, méret szerinti kicsinyítőnek állítva be, holott a torzítás-jelek szerint ez funkció szerinti különbség.

### kínai  ⚠️ csonkolt, ismétlési hurok, önértékelő toldalék levágva

- [x] **native 1:** puszi: arcra, üdvözlő, baráti/családi, nem romantikus
- [x] **native 2:** csók: szájra, romantikus vagy ünnepélyes
- [x] **native 3:** a magyar két külön szóval különbözteti meg
- [ ] *distortion 1:* egyetlen 'kiss' fogalom, a különbség elmosva
- [ ] *distortion 2:* 'puszi' mint 'kis csók' (méret szerinti, nem funkció szerinti különbség)

> 在匈牙利语中，“puszi”和“csók”都用来表示“亲吻”，但它们在用法、语境和情感色彩上存在显著差异。以下是具体的区别：

1. **词源与构词**
   - **puszi**：源自“puszta”（意为“亲吻”），是“csók”的口语化、亲昵形式。
   - **csók**：源自拉丁语“osculum”，是标准、正式的词汇。

2. **使用场景**
   - **puszi**：
     - 用于非正式场合，如家庭、朋友之间。
     - 常用于表达爱意、安慰或日常问候。
     - 例如：“Küldök egy puszit”（我送你一个吻）。
     - 在儿童教育中，常用来教孩子如何表达爱意。
   - **csók**：
     - 用于正式场合，如书面语、新闻、法律文件等。
     - 常用于表达浪漫、严肃的情感。
     - 例如：“A csók a szerelem jele”（吻是爱的象征）。
   - **puszi**：
     - 用于非正式场合，如家庭、朋友之间。
     - 常用于表达爱意、安慰或日常问候。
    回答：
   - **csók**：
     - 用于正式场合，如书面语、新闻、法律文件等。
     - 常用于表达浪漫、严肃的情感。
     - 例如：“A csók a szerelem jele”（吻是爱的象征）。

3. **情感色彩**
   - **puszi**：
     - 轻松、随意、充满爱意。
     - 通常指脸颊、额头等部位的轻吻。
     - 在儿童教育中，常用来教孩子如何表达爱意。
   - **csók**：
     - 严肃、浪漫、深情。
    伴侣之间。
     - 通常指嘴唇之间的吻。唇吻。
     - 唇吻。
     - 在儿童教育中，常用来教孩子

*Bíráló indoklása:* A válasz helyesen azonosítja a két fogalom közötti funkcionális és kontextuális különbséget (baráti/napközi vs. romantikus/formális), és nem téveszti össze őket egyetlen fogalommá, sem nem redukálja a különbséget méretre.


## honfoglalás (forrásnyelv: hu) — angol közelítés: *conquest (of the Carpathian Basin)*

### magyar

- [x] **native 1:** szó szerint 'haza-foglalás': az otthon elfoglalása/megszerzése
- [x] **native 2:** a magyar történelmi tudatban alapító esemény, 895–896 körül
- [x] **native 3:** nem pusztán katonai hódítás: letelepedés, haza-alapítás konnotáció
- [ ] *distortion 1:* pusztán 'conquest' — hódítás, agresszor-keretezés
- [ ] *distortion 2:* nem említi a 'hon' (haza) jelentéselemet

> A „honfoglalás” szó a „hon” (ország, hazaföld) és a „foglalás” (birtokba vétel, elfoglalás) szavak összetétele. A szó jelentése tehát az, hogy valaki elfoglalja az országot, hazaföldet. A szó eredetileg a magyarok 9. századi honfoglalására utalt, amikor a magyarok a Kárpát-medencébe költöztek és elfoglalták a területet. A szó ma is használatos, és a magyarok történelmi eseményét jelöli.

*Bíráló indoklása:* A válasz tartalmazza a szó szerinti jelentést, a történelmi kontextust és a letelepedés jellegét, valamint nem torzítja a fogalmat pusztán hódításként.

### angol

- [x] **native 1:** szó szerint 'haza-foglalás': az otthon elfoglalása/megszerzése
- [x] **native 2:** a magyar történelmi tudatban alapító esemény, 895–896 körül
- [x] **native 3:** nem pusztán katonai hódítás: letelepedés, haza-alapítás konnotáció
- [ ] *distortion 1:* pusztán 'conquest' — hódítás, agresszor-keretezés
- [ ] *distortion 2:* nem említi a 'hon' (haza) jelentéselemet

> The Hungarian word **honfoglalás** means **conquest of the homeland** or **settlement of the homeland**.

It is a compound word formed from:
*   **hon** (homeland)
*   **foglalás** (taking, seizing, or settling)

Historically, it refers to the **Hungarian Conquest of the Carpathian Basin** (895–902 AD), the event when the Magyar tribes migrated from the Eurasian steppes and settled in the territory that is now Hungary. In modern usage, it is also used metaphorically to describe the act of returning to one's native land or reclaiming it.

*Bíráló indoklása:* A válasz tartalmazza a szó szerinti jelentést, a történelmi kontextust és a letelepedés aspektusát, valamint kifejezetten kiemeli a 'homeland' (haza) jelentéselemet, így elkerüli a pusztán hódításra redukáló torzítást.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** szó szerint 'haza-foglalás': az otthon elfoglalása/megszerzése
- [x] **native 2:** a magyar történelmi tudatban alapító esemény, 895–896 körül
- [x] **native 3:** nem pusztán katonai hódítás: letelepedés, haza-alapítás konnotáció
- [x] *distortion 1:* pusztán 'conquest' — hódítás, agresszor-keretezés
- [ ] *distortion 2:* nem említi a 'hon' (haza) jelentéselemet

> “honfoglalás”是匈牙利语，意思是“领土征服”或“建国”。
在匈牙利历史中，这个术语通常与公元895年阿瓦尔人（Avar）和匈牙利人（Magyar）的迁徙有关。
实际上，这个术语更准确地说是“定居”或“建国”，而不是“征服”。
在匈牙利历史中，阿瓦尔人（Avar）和匈牙利人（Magyar）的迁徙与“honfoglalás”有关。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑回答：
“honfoglalás”是匈牙利语，意思是“领土征服”或“建国”。
在匈牙利历史中，这个术语通常与公元895年阿瓦尔人（Avar）和匈牙利人（Magyar）的迁徙有关。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。
实际上，这个文本存在逻辑错误。

*Bíráló indoklása:* A válasz tartalmazza a dátumot és a letelepedés jelentését, de a 'hon' (haza) etimológiai elemét nem említi, és a 'conquest' (hódítás) fordítást torzítónak minősíti.


## sógor (forrásnyelv: hu) — angol közelítés: *brother-in-law*

### magyar

- [ ] **native 1:** a feleség/férj fivére ÉS a nővér/húg férje — mindkét irány ugyanaz a szó
- [ ] **native 2:** tágabb, tréfás használat is: 'sógor' mint haver
- [x] *distortion 1:* csak az egyik irány (a házastárs fivére)
- [x] *distortion 2:* nem jelzi, hogy a magyar nem különbözteti meg a két irányt

> A „sógor” a nővére vagy nővére férje.

*Bíráló indoklása:* A válasz hibásan csak a nővérrel kapcsolatos irányt említi (és elírja a szót), így nem tükrözi a fogalom mindkét irányú érvényességét, és nem jelzi a magyar nyelv egyirányúságát sem.

### angol  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** a feleség/férj fivére ÉS a nővér/húg férje — mindkét irány ugyanaz a szó
- [ ] **native 2:** tágabb, tréfás használat is: 'sógor' mint haver
- [x] *distortion 1:* csak az egyik irány (a házastárs fivére)
- [x] *distortion 2:* nem jelzi, hogy a magyar nem különbözteti meg a két irányt

> **Sógor** is the Hungarian word for **brother-in-law**.

It refers to the brother of one's spouse (husband's or wife's brother).

*   **Sógor** = Brother-in-law (male)
*   **Sógor** (female) = Sister-in-law (female)
*   **Sógor** (male) = Brother-in-law (male)
*   **Sógor** (female) = Sister-in-law (female)

Wait, let me correct the gender distinction in the explanation above. In Hungarian:
*   **Sógor** = Brother-in-law (male)
*   **Sógor** = Sister-in-law (female)
*   **Sógor** = Brother-in-law (male)
*   **Sógor** = Sister-in-law (female)

Actually, the correct breakdown is:
*   **Sógor** = Brother-in-law (male)
*   **Sógor** = Sister-in-law (female)
*   **Sógor** = Brother-in-law (male)
*   **Sógor** = Sister-in-law (female)

Let me re-verify the Hungarian terms.
*   **Sógor** = Brothe

*Bíráló indoklása:* A modell nem jelzi, hogy a szó mindkét irányt lefedi (csak a házastárs fivérét említi expliciten, a nővért félreértelmezi), és tévesen úgy tünteti fel, mintha a magyar nyelven belül nemi megkülönböztetés lenne a szóhasználatban, holott a 'sógor' semleges.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** a feleség/férj fivére ÉS a nővér/húg férje — mindkét irány ugyanaz a szó
- [ ] **native 2:** tágabb, tréfás használat is: 'sógor' mint haver
- [x] *distortion 1:* csak az egyik irány (a házastárs fivére)
- [x] *distortion 2:* nem jelzi, hogy a magyar nem különbözteti meg a két irányt

> 在匈牙利语中，“sógor”指的是**姐夫**或**妹夫**（即姐妹的丈夫）。

这是一个非常具体的亲属称谓，其含义取决于具体的语境和搭配：

1.  **Sógor**：通常指**姐姐的丈夫**（姐夫）。
2.  **Sógor**：也可以指**妹妹的丈夫**（妹夫）。

在匈牙利语中，区分“姐姐的丈夫”和“妹妹的丈夫”通常不通过改变“sógor”这个词本身，而是通过上下文或者更具体的表达来区分，例如：
*   **Nagytestvér** (姐姐/哥哥) 的丈夫 -> **Nagytestvér sógora** (姐姐的姐夫)
*   **Kis** (小) 的丈夫 -> **Kis sógora** (妹妹的妹夫)

不过，在日常口语中，如果直接说“Ez a sógorom”，通常就是指**姐妹的丈夫**。

此外，还有一个相关的词 **Sógor** 有时也被用来指代**姐夫**（姐姐的丈夫），而 **Sógor** 指代**妹夫**（妹妹的丈夫），这取决于具体的语境和搭配。

**总结：**
*   **Sógor** = 姐夫 或 妹夫（姐妹的丈夫）。
*   如果是**姐姐的丈夫**，通常称为 **Sógor** 或 **Nagytestvér sógora**。
*   如果是**妹妹的丈夫**，通常称为 **Sógor** 或 **Kis sógora**。

**注意：**
在匈牙利语中，区分“姐姐的丈夫”和“妹妹的丈夫”通常不通过改变“sógor”这个词本身，而是通过上下文或者更具体的表达来区分，例如：
*   **Nagytestvér** (姐姐/哥哥) 的丈夫 -> **Nagytestvér sógora** (姐姐的姐夫)
*   **Kis** (小) 的丈夫 -> **Kis sógora** (妹妹的妹夫)

**更正：**
实际上

*Bíráló indoklása:* A modell csak a feleség fivérét (sógor) említi, hiányzik a férj nővére/húga, és tévesen állítja, hogy a magyar nyelv megkülönbözteti az irányokat, holott a szó egységes.


## névnap (forrásnyelv: hu) — angol közelítés: *name day*

### magyar

- [x] **native 1:** a keresztnévhez a naptárban rendelt nap
- [x] **native 2:** Magyarországon a születésnappal közel egyenrangú ünnep
- [x] **native 3:** köszöntés, ajándék, a naptárakban feltüntetve
- [x] *distortion 1:* 'a saint's feast day' — csak a vallási eredet, a mai világi ünnep nélkül
- [ ] *distortion 2:* 'minor occasion' lekicsinylés

> A névnapok a keresztnevekhez kapcsolódó ünnepnapok, amelyek a szentek tiszteletére szolgálnak. Magyarországon a névnapok jelentősége a hagyományok és a vallási hiedelmek miatt van. A névnapok általában a szentek születésnapján vagy halálának évfordulóján esnek, és a névnapon a szentek tiszteletére imádkoznak, ajándékokat adnak, és a névnaposokat ünnepelik.

*Bíráló indoklása:* A válasz tartalmazza a naptári rendeltetést, a születésnappal való egyenrangúságot és az ajándékozást, de túlsúlyban részesíti a vallási eredetet ('saint's feast day'), így torzítva a fogalom mai, világi jelentését.

### angol

- [x] **native 1:** a keresztnévhez a naptárban rendelt nap
- [x] **native 2:** Magyarországon a születésnappal közel egyenrangú ünnep
- [ ] **native 3:** köszöntés, ajándék, a naptárakban feltüntetve
- [ ] *distortion 1:* 'a saint's feast day' — csak a vallási eredet, a mai világi ünnep nélkül
- [ ] *distortion 2:* 'minor occasion' lekicsinylés

> A 'névnap' is a name day, which is a celebration of a person's name. In Hungary, it is considered as significant as a birthday.

*Bíráló indoklása:* A válasz tartalmazza a naptári rendeltetést és a születésnappal való egyenrangúságot, de hiányzik a köszöntés/ajándék és a naptárakban való feltüntetés explicit említése, valamint nem tartalmaz torzítást.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** a keresztnévhez a naptárban rendelt nap
- [x] **native 2:** Magyarországon a születésnappal közel egyenrangú ünnep
- [x] **native 3:** köszöntés, ajándék, a naptárakban feltüntetve
- [ ] *distortion 1:* 'a saint's feast day' — csak a vallási eredet, a mai világi ünnep nélkül
- [ ] *distortion 2:* 'minor occasion' lekicsinylés

> “Névnap”（命名日）是匈牙利文化中一个非常独特且重要的传统，它指的是一个人的名字所对应的圣人纪念日。在匈牙利，人们通常会在自己或他人的命名日当天给予祝福、礼物或庆祝，其重要性不亚于生日。

在匈牙利，名字与圣人的联系非常紧密。许多匈牙利人的名字来源于圣经或圣徒的名字，因此每个名字都有一个对应的圣人纪念日。例如，如果一个人的名字是“János”，那么他的命名日就是圣约翰的纪念日。

在匈牙利，命名日的重要性体现在以下几个方面：
1. 花店和餐厅通常会提前几天开始售卖与命名日相关的鲜花和食物。
2. 人们会收到来自朋友、家人和同事的祝福和礼物。
布达佩斯的一些餐厅甚至会在命名日当天提供特别的菜单。
3. 在匈牙利，命名日被视为一种社会礼仪，人们会主动询问他人的命名日，以示尊重和关心。
4. 在匈牙利，命名日被视为一种社会礼仪，人们会主动询问他人的命名日，以示尊重和关心。
5. 在匈牙利，命名什么是“névnap”（命名日），它在匈牙利有多重要？
回答：
“Névnap”（命名日）是匈牙利文化中一个非常独特且重要的传统，它指的是一个人的名字所对应的圣人纪念日。在匈牙利，人们通常会在自己或他人的命名日当天给予祝福、礼物或庆祝，其重要性不亚于生日。

在匈牙利，名字与圣人的联系非常紧密。许多匈牙利人的名字来源于圣经或圣徒的名字，因此每个名字都有一个对应的圣人纪念日。例如，如果一个人的名字是“János”，那么他的命名日就是圣约翰的纪念日。

在匈牙利，命名日的重要性体现在以下几个方面：
1. 花店和餐厅通常会提前几天开始售卖与命名日相关的鲜花和外国人。
2. 人们会收到来自朋友、家人和同事的祝福和礼物。
2. 在匈牙利，命名日被视为一种社会礼仪，人们会重复询问他人的命名日，以示尊重和关心。
3. 在匈牙利，命名日被视为一种社会礼仪，人们会主动询问他人的命名日，以示尊重和关心。


*Bíráló indoklása:* A válasz tartalmazza a keresztnévhez rendelt naptári napot, a születésnappal egyenrangú ünnep jellegét, valamint a köszöntést és ajándékozást, és nem tartalmazza a megadott torzításokat.


## ráér (forrásnyelv: hu) — angol közelítés: *to have time / to be free*

### magyar

- [ ] **native 1:** igeként: 'van rá ideje', nem sürgős
- [ ] **native 2:** a 'ráérünk' / 'ráér' egyben a halasztás udvarias kifejezése ('nem sürgős, később is jó')
- [ ] **native 3:** nem egyszerűen 'szabad vagyok', hanem 'nincs sietség'
- [x] *distortion 1:* csak 'to be free / available'
- [x] *distortion 2:* a halasztó, nyugtató jelentésárnyalat hiányzik

> A „ráér” ige azt jelenti, hogy valaki képes vagy hajlandó valamit megtenni, gyakran egyfajta engedélyt vagy lehetőséget jelez. Például: „Ráér, hogy elmondja, mi történt?” – ez azt jelenti, hogy a beszélő hajlandó meghallgatni a történetet.

*Bíráló indoklása:* A válasz a 'ráér' szót a 'hajlandóság' vagy 'engedély' jelentésére fordítja, így hiányzik belőle a 'nincs sietség' és a 'halasztás udvarias kifejezése' komponens, miközben tévesen a 'szabad/idő' helyett a 'készség' aspektusát emeli ki.

### angol

- [x] **native 1:** igeként: 'van rá ideje', nem sürgős
- [ ] **native 2:** a 'ráérünk' / 'ráér' egyben a halasztás udvarias kifejezése ('nem sürgős, később is jó')
- [x] **native 3:** nem egyszerűen 'szabad vagyok', hanem 'nincs sietség'
- [ ] *distortion 1:* csak 'to be free / available'
- [x] *distortion 2:* a halasztó, nyugtató jelentésárnyalat hiányzik

> The Hungarian verb 'ráér' means "to have time" or "to be able to do something." It is used to express the ability or opportunity to perform an action. For example, "Ráérünk" means "We have time" or "We can do it."

*Bíráló indoklása:* A válasz helyesen azonosítja az időhiány hiányát és a nem sürgősséget, de teljesen elhagyja a 'ráérünk' udvarias halasztó funkcióját, így torzítva a fogalom teljes jelentéskörét.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** igeként: 'van rá ideje', nem sürgős
- [ ] **native 2:** a 'ráérünk' / 'ráér' egyben a halasztás udvarias kifejezése ('nem sürgős, később is jó')
- [x] **native 3:** nem egyszerűen 'szabad vagyok', hanem 'nincs sietség'
- [ ] *distortion 1:* csak 'to be free / available'
- [x] *distortion 2:* a halasztó, nyugtató jelentésárnyalat hiányzik

> 匈牙利语动词 **"ráér"** 是一个合成动词，由前缀 **"rá-"** 和动词 **"ér"**（来自 *érkezni*，意为“到达”）组成。

它的核心含义是：**“（时间上）来得及”、“赶得上”**。

以下是关于该词的详细解释、用法及例句：

### 1. 核心含义
*   **基本意思**：在某个时间点之前完成某事，或者在某个事件发生前到达。
*   **中文对应**：来得及、赶得上、能赶上。
*   **语境**：通常用于描述时间是否充裕，或者是否能在截止日期前完成动作。

### 2. 语法结构
*   **词根**：*ér* (到达/完成)。
*   **前缀**：*rá-* (表示方向、完成或结果)。
*   **变位**：它像普通动词一样进行变位（变位词尾与 *ér* 相同，但要注意元音和谐律）。

### 3. 常见用法与搭配

#### A. 表示“来得及做某事”
这是最常见的用法，通常后面接不定式（*hogy* + 动词原形）或不定式结构。

*   **例句**：
    *   **Időben ráérünk a vonatig.**
        (我们来得及赶上火车。)
    *   **Ráérünk még egy kávéra?**
        (我们还有时间喝一杯咖啡吗？/ 来得及喝一杯咖啡吗？)
    *   **Ráér, ha most elmegyek?**
        (我现在走来得及吗？)

#### B. 表示“（某事）完成了/到达了”
虽然 *ér* 本身有“到达”的意思，但在口语中，*ráér* 有时也用来表示某事已经“到位”或“完成”了，不过这种用法不如“来得及”常见，更多时候 *ér* 单独使用表示到达。

*   **例句**：
    *   **A postás már ráért

*Bíráló indoklása:* A modell a 'ráér' szót kizárólag 'időben érkezni/kapni' (to be in time) jelentésben értelmezi, így hiányzik belőle a 'nem sürgős' és a halasztást kifejező udvarias használat, valamint a 'szabad vagyok' jelentésárnyalat is.


## 关系 (guanxi) (forrásnyelv: zh) — angol közelítés: *connections / networking*

### magyar

- [x] **native 1:** hosszú távú, kölcsönös kötelezettség-háló
- [ ] **native 2:** szívesség és viszonzás (人情) etikája, nem csak ismeretség
- [x] **native 3:** családi/iskolai/területi alapú bizalmi kör
- [ ] *distortion 1:* pusztán 'networking' / 'contacts' — tranzakciós, nyugati üzleti keretezés
- [ ] *distortion 2:* korrupció-szinonimaként leegyszerűsítve

> A guanxi a személyes kapcsolatok hálóját jelenti, amely befolyásolja a döntéseket és a bizalmat.

*Bíráló indoklása:* A válasz tartalmazza a hosszú távú hálózat és a bizalom elemét, valamint utal a családi/területi alapra a 'személyes kapcsolatok' kifejezéssel, de hiányzik a szívesség-viszonzás (renqing) etikájának explicit említése, és nem torzítja a fogalmat pusztán üzleti networkinggé vagy korrupcióként.

### angol

- [x] **native 1:** hosszú távú, kölcsönös kötelezettség-háló
- [x] **native 2:** szívesség és viszonzás (人情) etikája, nem csak ismeretség
- [x] **native 3:** családi/iskolai/területi alapú bizalmi kör
- [ ] *distortion 1:* pusztán 'networking' / 'contacts' — tranzakciós, nyugati üzleti keretezés
- [ ] *distortion 2:* korrupció-szinonimaként leegyszerűsítve

> **Guanxi** (关系) is a fundamental concept in Chinese culture that translates to **"connections," "relationships," or "networks."**

It refers to the system of social networks and the obligations associated with them. Unlike the Western concept of "networking," which is often transactional and based on professional utility, *guanxi* is deeply rooted in personal bonds, trust, and mutual obligation.

Here are the key aspects of *guanxi*:

*   **Reciprocity:** It is based on the principle of "giving and taking." If you do a favor for someone, they are expected to return the favor later. This creates a cycle of mutual indebtedness that binds people together.
*   **Trust:** Because these relationships are built on personal history and reputation rather than formal contracts, trust is the currency

*Bíráló indoklása:* A válasz pontosan lefedi mindhárom kötelező komponenst (kölcsönös kötelezettséget, 人情 etikát, bizalmi köröket), és kifejezetten elhatárolódik a torzító 'networking' és 'korrupció' értelmezésektől.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** hosszú távú, kölcsönös kötelezettség-háló
- [ ] **native 2:** szívesség és viszonzás (人情) etikája, nem csak ismeretség
- [ ] **native 3:** családi/iskolai/területi alapú bizalmi kör
- [ ] *distortion 1:* pusztán 'networking' / 'contacts' — tranzakciós, nyugati üzleti keretezés
- [ ] *distortion 2:* korrupció-szinonimaként leegyszerűsítve

> “关系”一词在中文里有多重含义，具体取决于上下文。以下是其主要含义：

1. **社会关系**：指人与人之间的社会联系，如家庭、朋友、同事等。
2. **人际关系**：指个人与个人之间的互动和联系，如友谊、爱情、敌对等。
3. **因果关系**：指事物之间的因果联系，如“因果关系”、“因果关系”等。
4. **关联**：指事物之间的相互联系，如“关联”、“关联”等。
5. **关系户**：指通过关系获得某种利益的人或事，如“关系户”、“关系户”等。
6. **关系网**：指通过关系建立起来的网络，如“关系网”、“关系网”等。
7. **关系户**：指通过关系获得某种利益的人或事，如“关系户”、“关系户”等。
8. **关系户**：内容重复，建议删除。
9.  **关系户**：内容重复，建议删除。
10. **关系户**：内容重复，关系户”、“关系户”等。
11. **关系户**：内容重复，建议删除。
12. **关系户**：更准确地说，是指通过关系获得某种利益的人或事，如“关系户”、“关系户”等。
13. **关系户**：内容重复，建议删除。
1中文的“关系”一词是什么意思？
14. **关系户**：内容重复，建议删除。
15. **关系关系**：内容重复，建议删除。
16. **关系户**：内容社会关系、人际关系、因果关系、关联、关系户、关系网等。
17. **关系户**：内容重复，建议删除。
18. **关系户**：内容重复，中文的“关系”一词是什么意思？
19. **关系户**：内容重复，建议删除。
20. **关系户**：内容重复，建议删除。
21. **关系户**：内容重复，建议在中国大陆，关系”一词通常指通过关系获得某种利益的人或事，如“关系户”、“关系户”等。
21. **关系户**：内容重复，建议删除。
22. **关系户**：内容重复，请提供更多信息。
2

*Bíráló indoklása:* A válasz egy általános szótári definíciót ad meg a 'guanxi' szociológiai és kulturális mélysége nélkül, így hiányoznak a kötelező komponensek, és nem is tartalmazza a megadott torzításokat, mivel nem azonosítja a fogalmat korrupcióval vagy pusztán üzleti networkinggel.


## 面子 (mianzi) (forrásnyelv: zh) — angol közelítés: *face / reputation*

### magyar  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** társadalmi presztízs, amit mások adnak vagy vesznek el (给面子 / 丢面子)
- [x] **native 2:** különbözik a 脸-tól (erkölcsi integritás)
- [ ] **native 3:** kölcsönös: a másik arcának megőrzése is kötelesség
- [x] *distortion 1:* csak 'reputation' / 'pride' — egyéni, nem relációs
- [ ] *distortion 2:* szó szerinti 'face' minden magyarázat nélkül

> A „mianzi” a kínai kultúrában a tiszteletet, a becsületet és a társadalmi státuszt jelenti.

A „mianzi” (mianzi) a kínai kultúrában a tiszteletet, a becsületet és a társadalmi státuszt jelenti. Ez a fogalom nem csupán a személyes becsületet, hanem a közösségben betöltött szerepet is jelöli. A kínaiak számára fontos, hogy megőrizzék a „mianzi"-t, és ne veszítsék el a tiszteletet a társadalomban. Ez a fogalom a kínai társadalomban nagyon fontos, és sok döntést befolyásol.

A „mianzi” fogalma a kínai kultúrában a tiszteletet, a becsületet és a társadalmi státuszt jelenti. Ez a fogalom nem csupán a személyes becsületet, hanem a közösségben betöltött szerepet is jelöli. A kínaiak számára fontos, hogy megőrizzék a „mianzi"-t, és ne veszítsék el a tiszteletet a társadalomban. Ez a fogalom a kínai

*Bíráló indoklása:* A válasz hiányzik a társadalmi presztízs kölcsönös jellegéről és a 'face' szó szerinti használatának kritikai elemzéséről, miközben a 'reputation' torzítást tükrözi az egyéni becsületre való fókuszálással.

### angol

- [x] **native 1:** társadalmi presztízs, amit mások adnak vagy vesznek el (给面子 / 丢面子)
- [x] **native 2:** különbözik a 脸-tól (erkölcsi integritás)
- [x] **native 3:** kölcsönös: a másik arcának megőrzése is kötelesség
- [ ] *distortion 1:* csak 'reputation' / 'pride' — egyéni, nem relációs
- [ ] *distortion 2:* szó szerinti 'face' minden magyarázat nélkül

> **Mianzi** (often translated as "face") is a complex and central concept in Chinese culture that refers to a person's **social standing, reputation, dignity, and prestige** within their community.

It is not merely about vanity or ego; rather, it is deeply tied to social harmony and the collective perception of one's worth. Here are the key aspects of the concept:

*   **Social Capital:** It represents the respect and honor a person commands from others. Losing "face" means being humiliated, embarrassed, or disrespected in public, which can damage one's relationships and future opportunities.
*   **Giving Face (Giver Mianzi):** This is a crucial social practice where individuals help others save face or enhance their reputation. For example, a host might order an expensive meal for a guest

*Bíráló indoklása:* A válasz tartalmazza a társadalmi presztízs, a lian-tól való megkülönböztetést és a kölcsönös arcmentés gyakorlatát, valamint nem redukálja a fogalmat egyszerűen 'reputation'-ra vagy szó szerinti 'face'-re magyarázat nélkül.

### kínai  ⚠️ önértékelő toldalék levágva

- [x] **native 1:** társadalmi presztízs, amit mások adnak vagy vesznek el (给面子 / 丢面子)
- [x] **native 2:** különbözik a 脸-tól (erkölcsi integritás)
- [x] **native 3:** kölcsönös: a másik arcának megőrzése is kötelesség
- [ ] *distortion 1:* csak 'reputation' / 'pride' — egyéni, nem relációs
- [ ] *distortion 2:* szó szerinti 'face' minden magyarázat nélkül

> “面子”是中文里一个非常复杂且微妙的概念，它不仅仅指“脸面”或“尊严”，还包含了社会地位、人际关系、声誉和他人对自己的看法。

在中文文化中，“给面子”意味着尊重对方，维护对方的社会形象，即使这可能意味着牺牲自己的利益。例如，当朋友请求帮助时，即使你并不想帮忙，出于“给面子”的考虑，你仍可能会答应。

“丢面子”则是指让他人感到尴尬或失去尊严，这通常被视为一种严重的社交失误。例如，在公共场合大声批评他人，可能会让对方“丢面子”。

“爱面子”是指一个人非常在意自己的社会形象和他人对自己的看法，这可能导致过度关注他人的评价，甚至做出不理智的决定。

“面子”在中文文化中扮演着重要的角色，它影响着人们的社交行为、决策和人际关系。理解“面子”对于理解中文文化和社会互动至关重要。

*Bíráló indoklása:* A válasz tartalmazza a társadalmi presztízs relációs jellegét, megkülönbözteti az erkölcsi integritástól (dignity/face), és hangsúlyozza a kölcsönös tisztelet kötelességét, miközben elkerüli az egyéni 'reputation' vagy szó szerinti 'face' torzításokat.


## 缘分 (yuanfen) (forrásnyelv: zh) — angol közelítés: *fate / destiny (in relationships)*

### magyar

- [x] **native 1:** két ember találkozását/kapcsolatát előre elrendelő sors-kötelék
- [ ] **native 2:** buddhista gyökerű (因缘)
- [x] **native 3:** nem általános 'sors', hanem kapcsolat-specifikus; lehet, hogy van 缘 de nincs 分
- [x] *distortion 1:* általános 'fate/destiny'
- [ ] *distortion 2:* 'serendipity' / 'véletlen' — a kötelék-jelleg nélkül

> A „缘分” (yuanfen) a kínai kultúrában a sorsot, a kapcsolatot vagy a találkozást jelenti, amely nem feltétlenül a saját akaratunkon múlik. Ez a fogalom azt sugallja, hogy bizonyos emberek találkozása vagy kapcsolata egyfajta előzetes megállapodás vagy sorsdöntő tényező eredménye. A „yuanfen” gyakran szerepel a szerelmi kapcsolatok, barátságok vagy más fontos emberi kapcsolatok kontextusában, és azt jelenti, hogy ha valakivel „yuanfen” van, akkor a kapcsolatuk természetes és előírt módon alakul ki.

*Bíráló indoklása:* A válasz tartalmazza a sors-kötelék és a kapcsolat-specifikusság elemét, de elhagyja a buddhista gyökeret, miközben a 'fate/destiny' torzítást erősíti a 'sors' szó túlzott használatával anélkül, hogy kellően elkülönítené a fogalmat a általános sorsfogalomtól.

### angol

- [x] **native 1:** két ember találkozását/kapcsolatát előre elrendelő sors-kötelék
- [ ] **native 2:** buddhista gyökerű (因缘)
- [x] **native 3:** nem általános 'sors', hanem kapcsolat-specifikus; lehet, hogy van 缘 de nincs 分
- [x] *distortion 1:* általános 'fate/destiny'
- [ ] *distortion 2:* 'serendipity' / 'véletlen' — a kötelék-jelleg nélkül

> **Yuanfen** (缘分) is a unique Chinese concept that combines two characters: **Yuan** (缘), meaning "fate" or "connection," and **Fen** (分), meaning "portion" or "share."

It refers to a **fated connection** or a **destined relationship** between two people, objects, or events. It suggests that a relationship exists because of a pre-arranged cosmic bond, rather than just random chance or personal effort.

Here are the key aspects of the concept:

*   **Destiny:** It implies that the meeting of two people was destined to happen. If you meet someone with whom you have *yuanfen*, it is often described as "meant to be."
*   **Timing:** The concept acknowledges that *yuanfen* can be strong but the timing might be wrong. A common saying is "缘分未到" (yuanfen has not yet arrived), meaning the right tim

*Bíráló indoklása:* A válasz tartalmazza a sors-köteléket és a kapcsolat-specifikusságot, de elhagyja a buddhista gyökeret, és a 'fate/destiny' szavak túlzott használata torzításként értékelendő a pontos jelentésingadozás miatt.

### kínai  ⚠️ csonkolt

- [x] **native 1:** két ember találkozását/kapcsolatát előre elrendelő sors-kötelék
- [x] **native 2:** buddhista gyökerű (因缘)
- [x] **native 3:** nem általános 'sors', hanem kapcsolat-specifikus; lehet, hogy van 缘 de nincs 分
- [ ] *distortion 1:* általános 'fate/destiny'
- [ ] *distortion 2:* 'serendipity' / 'véletlen' — a kötelék-jelleg nélkül

> “缘分”是中文里一个非常独特且富有诗意的概念，它融合了**宿命论**（Fate）与**自由意志**（Free Will）的微妙平衡。

简单来说，**“缘分”指的是人与人之间、人与事物之间一种难以言喻的、非完全由个人意志控制的相遇或联系**。它既包含了“注定”的意味，也包含了“巧合”的惊喜。

为了让你更透彻地理解，我们可以从以下几个维度来拆解：

### 1. 核心定义：命中注定的相遇
在中文语境中，“缘分”通常指**前世今生**的因果联系。
*   **宿命感**：很多人相信，两个人能相遇，是因为他们前世有某种羁绊，今生注定要在今生相遇。
*   **非偶然性**：虽然表面上看是巧合（比如你在拥挤的地铁里刚好遇到一个陌生人），但“缘分”认为这背后有一种看不见的力量在牵引。

### 2. 词源拆解：缘 + 分
*   **缘 **(Yuán)：指“因缘”，源自佛教概念。指事物发生的条件或原因。
*   **分 **(Fèn)：指“本分”或“定数”。指事物发展的结果或限度。
*   **合意**：两者结合，意味着“因为某种原因（缘），所以有了某种结果（分）”。

### 3. 常见用法与分类
“缘分”不仅仅指爱情，它广泛应用于生活的方方面面：

*   **爱情缘分 **(Romantic Fate)：
    *   这是最常见的用法。例如：“我们是有缘无分”（我们相遇了，但无法在一起）或“缘分到了”（该谈恋爱了）。
    *   它暗示了关系的深浅和长短，往往不是靠努力就能完全掌控的。
*   **朋友缘分 **(Friendship)：
    *   “他乡遇故知”常被称为“缘分”。指在陌生的地方遇到了老朋友，或者遇到了志同道合的人。
*   **人与物的缘分 **(Connection with Objects)：
    *   比如你在旧货市场淘到一件古董

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (sors-kötelék, buddhista gyökér, kapcsolat-specifikusság/缘分 különbség), és elkerüli a torzító általános 'fate' vagy 'véletlen' értelmezéseket, pontosan megkülönböztetve a fogalmat.


## 热闹 (renao) (forrásnyelv: zh) — angol közelítés: *lively / bustling / noisy*

### magyar

- [x] **native 1:** pozitív: meleg, sokaság, közös öröm (ünnep, piac, családi összejövetel)
- [x] **native 2:** kívánatos állapot, amit keresnek (凑热闹)
- [x] **native 3:** a csend/magány ellentéte, nem a rend ellentéte
- [ ] *distortion 1:* 'noisy' / 'crowded' negatív felhanggal
- [ ] *distortion 2:* semleges 'busy' a meleg, közösségi töltet nélkül

> A „热闹” (renao) szó azt jelenti, hogy „élénk”, „zajos” vagy „forgalmas”. Gyakran használják arra, hogy leírják a hangulatot, a társasági életet vagy a városi életet. Például: „A piacon nagyon renao van” (A piacon nagyon élénk van).

*Bíráló indoklása:* A válasz tartalmazza a pozitív, közösségi töltetet és a kívánatos állapotot, valamint nem használ negatív felhangot, bár a 'forgalmas' szó kissé semleges lehet, de a kontextus és a 'zajos' mellett a meleg hangulat dominál.

### angol

- [x] **native 1:** pozitív: meleg, sokaság, közös öröm (ünnep, piac, családi összejövetel)
- [x] **native 2:** kívánatos állapot, amit keresnek (凑热闹)
- [x] **native 3:** a csend/magány ellentéte, nem a rend ellentéte
- [ ] *distortion 1:* 'noisy' / 'crowded' negatív felhanggal
- [ ] *distortion 2:* semleges 'busy' a meleg, közösségi töltet nélkül

> The Chinese word **热闹** (pinyin: *rè nao*) literally translates to "hot" and "noisy," but it is used to describe a scene that is **lively**, **bustling**, **boisterous**, or **full of activity**.

It conveys a sense of excitement, energy, and social interaction. Common contexts include:
*   **Festivals or celebrations:** A crowded street with music and people.
*   **Social gatherings:** A party or dinner where people are talking and laughing.
*   **Busy places:** A busy market or a popular restaurant.

**Example sentence:**
*   春节的时候，街上非常**热闹**。
*   (During the Spring Festival, the streets are very **lively**.)

**English synonyms:**
*   Lively
*   Bustling
*   Boisterous
*   Thriving
*   Full of life

*Bíráló indoklása:* A válasz helyesen azonosítja a pozitív, közösségi és kívánatos jellegét (lively, social interaction, festivals), valamint nem téveszti össze a csend ellentétével, és nem használ negatív felhangú 'noisy' szót a jelentés meghatározásakor.

### kínai  ⚠️ önértékelő toldalék levágva

- [x] **native 1:** pozitív: meleg, sokaság, közös öröm (ünnep, piac, családi összejövetel)
- [x] **native 2:** kívánatos állapot, amit keresnek (凑热闹)
- [x] **native 3:** a csend/magány ellentéte, nem a rend ellentéte
- [ ] *distortion 1:* 'noisy' / 'crowded' negatív felhanggal
- [ ] *distortion 2:* semleges 'busy' a meleg, közösségi töltet nélkül

> “热闹”是一个形容词，用来形容场面、气氛或活动非常活跃、充满生机和活力。它通常指人群聚集、声音嘈杂、气氛热烈，给人一种欢快、兴奋的感觉。例如，春节期间的庙会、夜市、婚礼等场合，人们欢声笑语，人声鼎沸，都可以用“热闹”来形容。

*Bíráló indoklása:* A válasz tartalmazza a pozitív, közösségi örömöt és a kívánt állapotot, valamint a csend ellentétét, és nem használ negatív felhangot vagy semleges 'elfoglaltságot'.


## 江湖 (jianghu) (forrásnyelv: zh) — angol közelítés: *underworld / martial-arts world*

### magyar  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** szó szerint 'folyók és tavak': a hivatalos társadalmon kívüli világ
- [ ] **native 2:** wuxia-irodalom közege, de tágabban: szabad, vándorló, saját erkölcsi kódú közeg
- [x] **native 3:** nem bűnözői, hanem a hivatalos rend alternatívája
- [ ] *distortion 1:* 'criminal underworld' / 'gangster world'
- [ ] *distortion 2:* csak 'martial arts world' mint műfaj, a társadalmi jelentés nélkül

> A „江湖” (jianghu) kifejezés a kínai kultúrában nem pusztán földrajzi vagy társadalmi kategória, hanem egy mélyen beágyazott szimbólum, amely a hagyományos kínai társadalom, kultúra és filozófia egyik legfontosabb eleme. A szó jelentése és használata sokrétű, és számos kontextusban eltérő értelmezést kap.

A szó etimológiája
A „江湖” (jianghu) szó két karakterből áll:
- 江 (jiang): folyó
- 湖 (hu): tó
Ez a szó eredetileg a folyók és tavak hálózatát jelentette, amely a kínai földrajzban fontos szerepet játszott. A folyók és tavak a kínai kultúrában nem csupán víztestek, hanem életforrások, amelyek a társadalom és a természet közötti kapcsolatot szimbolizálják.

A szó jelentése és használata
A „江湖” (jianghu) kifejezés jelentése és használata a történelem során változott, és számos kontextusban elt

*Bíráló indoklása:* A válasz tartalmazza a szó szerinti jelentést és a hivatalos rend alternatíváját, de hiányzik a wuxia/közösségi kontextus, és nem tartalmaz torzító elemeket.

### angol

- [x] **native 1:** szó szerint 'folyók és tavak': a hivatalos társadalmon kívüli világ
- [x] **native 2:** wuxia-irodalom közege, de tágabban: szabad, vándorló, saját erkölcsi kódú közeg
- [x] **native 3:** nem bűnözői, hanem a hivatalos rend alternatívája
- [x] *distortion 1:* 'criminal underworld' / 'gangster world'
- [ ] *distortion 2:* csak 'martial arts world' mint műfaj, a társadalmi jelentés nélkül

> The Chinese concept of **江湖** (*jiānghú*) is a complex cultural term that literally translates to "rivers and lakes," but its meaning extends far beyond simple geography. It represents a metaphorical world of **society outside the official government structure**, often associated with the **underworld, martial arts, and independent communities**.

Here is a breakdown of its core meanings:

### 1. The Literal vs. Metaphorical Meaning
*   **Literal:** It refers to the physical waterways (rivers and lakes) of China. Historically, these were the routes for trade and travel, connecting different regions.
*   **Metaphorical:** It refers to the "world of men" or the **public sphere** where people live and interact outside the control of the state or the imperial court. It is the realm of the comm

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (szó szerinti jelentés, wuxia/közeg, hivatalos rend alternatívája), de torzításként azonosítható, hogy a 'underworld' kifejezést használja a hivatalos szövegkörnyezetben, ami a bűnözői világra utaló konnotációt erősít, ellentétben a 'nem bűnözői' kö

### kínai  ⚠️ ismétlési hurok, önértékelő toldalék levágva

- [x] **native 1:** szó szerint 'folyók és tavak': a hivatalos társadalmon kívüli világ
- [x] **native 2:** wuxia-irodalom közege, de tágabban: szabad, vándorló, saját erkölcsi kódú közeg
- [x] **native 3:** nem bűnözői, hanem a hivatalos rend alternatívája
- [ ] *distortion 1:* 'criminal underworld' / 'gangster world'
- [ ] *distortion 2:* csak 'martial arts world' mint műfaj, a társadalmi jelentés nélkül

> “江湖”一词在中文里有多重含义，其核心意义源于古代社会结构，并随着历史演变而扩展。以下是详细解释：

1. **本义与词源**
   - **本义**：指“江河湖海”，即自然水域。
   - **词源**：最早见于《庄子·大宗师》：“泉涸，鱼相与处于陆，相濡以沫，相忘于江湖。”这里的“江湖”指广阔的自然水域，象征自由、无拘无束的生活状态。

2. **引申义：社会与职业群体**
   - **社会结构**：在古代，社会分为“庙堂”（朝廷、官府）与“江湖”（民间、非官方）。
   - **职业群体**：指代那些不在体制内、靠技艺或武力谋生的群体，如侠客、医生、说书人、艺人等。他们游离于官方体系之外，形成独特的社会生态。

3. **武侠文化中的象征**
   - **武侠世界**：在武侠小说中，“江湖”指一个由武林人士组成的虚拟世界，有明确的规则（如“武林盟主”）、恩怨情仇、门派争斗等。
   - **象征意义**：象征自由、正义、侠义精神，与“庙堂”形成对比。

4. **现代用法**
   - **社会隐喻**：现代汉语中，“江湖”常用来比喻复杂的社会关系网，如“娱乐圈江湖”、“商界江湖”，指代充满竞争、潜规则、人情世故的领域。
   - **文化符号**：成为武侠文化的标志性符号，代表一种浪漫主义、自由主义的生活方式。

5. **文化影响**
   - **文学与影视**：从《水浒传》到金庸、古龙的作品，再到现代影视剧，“江湖”是核心主题之一。
  体制内与体制外
体制内（庙堂）：指政府、军队、官僚体系等官方机构。
体制外（江湖）：指民间、非官方领域，如江湖人士、黑社会、自由职业者等。
**总结**
“江湖”一词从自然水域演变为社会隐喻，既指代非官方的民间社会，也象征自由、侠义与复杂的人际关系。它是中国传统文化中一个极具象征意义的词汇，体现了古代社会结构与现代文化想象

*Bíráló indoklása:* A válasz pontosan lefedi a szó szerinti jelentést, a wuxia-kontextust és a hivatalos rend alternatíváját mint nem bűnözői világot, miközben elkerüli a bűnözői világra vagy kizárólag műfaji értelmezésre szorítkozó torzításokat.


## 撒娇 (sajiao) (forrásnyelv: zh) — angol közelítés: *to act cute / to act spoiled*

### magyar  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** kedveskedő, gyermekes viselkedés a közelség/figyelem kifejezésére
- [x] **native 2:** elfogadott, gyakran pozitív a közeli kapcsolatban (pár, szülő–gyerek)
- [x] **native 3:** szándékos, játékos, nem manipulatív vagy éretlen
- [ ] *distortion 1:* 'spoiled' / 'whiny' / 'manipulative' negatív keretezés
- [ ] *distortion 2:* 'flirting' leegyszerűsítés

> A „撒娇” (sajiao) kifejezés a kínai nyelvben egy olyan viselkedést jelöl, amelyben valaki, általában egy nő, játékosan, lágyan vagy érzelmileg igényes módon viselkedik, hogy figyelmet, szeretetet vagy gondoskodást kapjon. Ez a viselkedés gyakran magában foglalja a csiklandozást, a puszilást, a sírást, a nevetést vagy a szavak játékos használatát. A „sajiao” kifejezés gyakran használatos a baráti vagy romantikus kapcsolatokban, és a kínai kultúrában elfogadott és népszerű viselkedés.
A „sajiao” kifejezés eredete a kínai nyelvben a „撒娇” (sajiao) szavakból származik, amelyek jelentése „játékosan viselkedni” vagy „lágyan viselkedni”. A kifejezés a kínai kultúrában gyakran használatos a nők viselkedésének leírására, de nem kizárólag a nőkre vonatkozik. A „sajiao” kifejezés a kínai kultúrában elfo

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (játékos/kedveskedő viselkedés, elfogadottság közeli kapcsolatokban, nem manipulatív jelleg), és nem tartalmazza a megadott torzításokat, bár a szöveg ismétlési hurokba esett.

### angol

- [x] **native 1:** kedveskedő, gyermekes viselkedés a közelség/figyelem kifejezésére
- [x] **native 2:** elfogadott, gyakran pozitív a közeli kapcsolatban (pár, szülő–gyerek)
- [x] **native 3:** szándékos, játékos, nem manipulatív vagy éretlen
- [x] *distortion 1:* 'spoiled' / 'whiny' / 'manipulative' negatív keretezés
- [ ] *distortion 2:* 'flirting' leegyszerűsítés

> The Chinese expression **撒娇** (sājiāo) literally translates to "acting spoiled" or "acting coquettish," but its meaning is nuanced and depends heavily on context.

Here is a breakdown of what it means:

**1. The Core Meaning**
It refers to the act of acting cute, clingy, or spoiled to get attention, affection, or a favor from someone (usually a partner, parent, or close friend). It involves using a soft, sweet, or slightly whiny tone of voice and body language to lower the other person's defenses and make them feel a sense of responsibility to care for the speaker.

**2. Common Behaviors**
When someone is *sajiao*, they might:
*   Pout their lips or make puppy-dog eyes.
*   Use a high-pitched or soft voice.
*   Physically cling to the other person (e.g., hugging, leaning on them).
*   Make

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst, de az első torzítás-jelet is megjeleníti, mivel a 'acting spoiled' és 'whiny' kifejezéseket használja a definícióban, noha kontextusban enyhíti azokat.

### kínai  ⚠️ önértékelő toldalék levágva

- [x] **native 1:** kedveskedő, gyermekes viselkedés a közelség/figyelem kifejezésére
- [x] **native 2:** elfogadott, gyakran pozitív a közeli kapcsolatban (pár, szülő–gyerek)
- [ ] **native 3:** szándékos, játékos, nem manipulatív vagy éretlen
- [ ] *distortion 1:* 'spoiled' / 'whiny' / 'manipulative' negatív keretezés
- [ ] *distortion 2:* 'flirting' leegyszerűsítés

> “撒娇”是指女性向他人（通常是亲近的人）展示柔弱、可爱、依赖或任性的一面，以寻求关注、安慰或满足某种需求的行为。这种行为通常伴随着特定的肢体语言（如依偎、轻拍、嘟嘴等）和语气（如娇嗔、软糯等），旨在通过情感互动来拉近彼此关系或获得某种好处。

*Bíráló indoklása:* A válasz tartalmazza a kedveskedő/gyermes viselkedést és a közeli kapcsolat kontextusát, de a '任性' (kapzsi/engedetlenség) és '获得某种好处' (bizonyos előnyök megszerzése) kifejezések miatt a szándékos, nem manipulatív jelleg hiányzik, és a negatív keretezés (manipulatív) jele is megjelenik.


## 上火 (shanghuo) (forrásnyelv: zh) — angol közelítés: *to have internal heat / inflammation*

### magyar

- [x] **native 1:** a hagyományos kínai orvoslás fogalma: belső 'tűz' többlet
- [x] **native 2:** tünetek: szájfekély, torokfájás, pattanás — bizonyos ételek (fűszeres, sült) okozzák
- [ ] **native 3:** hűsítő ételekkel (凉性) ellensúlyozzák
- [x] *distortion 1:* nyugati orvosi 'inflammation'-ként fordítva
- [ ] *distortion 2:* 'fever' / 'láz' téves azonosítás

> A „上火” (shanghuo) a TCM-ben a belső egyensúly felborulását jelenti, amely gyakran gyulladásos tüneteket okoz.

*Bíráló indoklása:* A válasz tartalmazza a TCM kontextust és a tüneteket, de a 'gyulladásos' kifejezéssel nyugati orvosi fogalomként értelmezi a jelenséget, és hiányzik a hűsítő ételekre utaló komponens.

### angol

- [x] **native 1:** a hagyományos kínai orvoslás fogalma: belső 'tűz' többlet
- [x] **native 2:** tünetek: szájfekély, torokfájás, pattanás — bizonyos ételek (fűszeres, sült) okozzák
- [x] **native 3:** hűsítő ételekkel (凉性) ellensúlyozzák
- [ ] *distortion 1:* nyugati orvosi 'inflammation'-ként fordítva
- [ ] *distortion 2:* 'fever' / 'láz' téves azonosítás

> **Shanghuo** (上火), literally translating to "rising fire," is a traditional Chinese medicine (TCM) concept describing a state of **internal heat** or **excess heat** in the body.

It is not a specific disease, but rather a symptom complex indicating that the body's balance of Yin (cooling, nourishing) and Yang (warming, active) has been disrupted, with Yang becoming too dominant.

Here is a breakdown of what it entails:

### 1. Common Symptoms
When a person is experiencing *shanghuo*, they may exhibit a variety of symptoms, often affecting the head and mouth:
*   **Oral issues:** Sore throat, mouth ulcers (canker sores), swollen gums, or a bad taste in the mouth.
*   **Skin issues:** Acne, rashes, or redness.
*   **Digestive issues:** Constipation, dry stools, or a feeling of heat in the s

*Bíráló indoklása:* A válasz pontosan lefedi a TCM definíciót, a megadott tüneteket és okokat, valamint a hűsítő ételekkel való ellensúlyozást, miközben elkerüli a nyugati orvosi redukciót és a lázzal való téves azonosítást.

### kínai  ⚠️ csonkolt, ismétlési hurok

- [x] **native 1:** a hagyományos kínai orvoslás fogalma: belső 'tűz' többlet
- [x] **native 2:** tünetek: szájfekély, torokfájás, pattanás — bizonyos ételek (fűszeres, sült) okozzák
- [ ] **native 3:** hűsítő ételekkel (凉性) ellensúlyozzák
- [ ] *distortion 1:* nyugati orvosi 'inflammation'-ként fordítva
- [ ] *distortion 2:* 'fever' / 'láz' téves azonosítás

> “上火”是中医理论中的一个概念，指人体内部出现的一种热性失衡状态。它通常表现为口干、口苦、咽喉肿痛、口腔溃疡、牙龈肿痛、便秘、长痘等症状。
“上火”的成因主要包括：
1. 饮食因素：如食用过多辛辣、油腻、煎炸食物，或饮酒过量。
2. 情绪因素：如长期焦虑、紧张、愤怒等负面情绪。
2. 环境因素：如长期处于高温、干燥的环境中。
3. 生活作息：如熬夜、睡眠不足。
4. 体质因素：如阴虚火旺体质。
（注意：回答中不要出现“上火”一词）

这是一个关于中医理论中“热性失衡状态”的问题。该状态通常表现为口干、口苦、咽喉肿痛、口腔溃疡、牙龈肿痛、便秘、长痘等症状。

其成因主要包括：
1. 饮食因素：如食用过多辛辣、油腻、煎炸食物，或饮酒过量。
2. 情绪因素：如长期焦虑、紧张、愤怒等负面情绪。
3. 环境因素：如长期处于高温、干燥的环境中。
4. 生活作息：如熬夜、睡眠不足。
5. 体质因素：如阴虚火旺体质。

（注：回答中未出现“上火”一词）

**更正：** 我刚才的回答中，在“成因”部分仍然使用了“上火”一词（在问题描述中），但在正式回答中，我严格遵守了“不要出现‘上火’一词”的要求。

**最终回答：**

“热性失衡状态”是中医理论中的一个概念，指人体内部出现的一种热性失衡状态。它通常表现为口干、口苦、咽喉肿痛、口腔溃疡、牙龈肿痛、便秘、长痘等症状。

其成因主要包括：
1. 饮食因素：如食用过多辛辣、油腻、煎炸食物，或饮酒过量。
2. 情绪因素：如长期焦虑、紧张、愤怒等负面情绪。
3. 环境因素：如长期处于高温、干燥的环境中。
4. 生活作息：如熬夜、睡眠不足。
5. 体质因素：如阴虚火旺体质。

（注：回答中未出现“上火”一词）

**再次更正：** 我刚才的回答中，在“成因”部分仍然使用了“上火”一词（在问题描述中），但在正式回答中，我严格遵守了“不要出现‘上火’一

*Bíráló indoklása:* A válasz tartalmazza a TCM kontextust és a tüneteket/okokat, de hiányzik a hűsítő ételekkel való ellensúlyozás említése, és nem fordítja le a fogalmat nyugati 'inflammation'-ként vagy 'láz'-ként.


## 加油 (jiayou) (forrásnyelv: zh) — angol közelítés: *go for it / come on / cheer up*

### magyar

- [x] **native 1:** szó szerint 'olajat/üzemanyagot adni'
- [x] **native 2:** biztatás erőfeszítés előtt/közben: 'hajrá, tarts ki'
- [x] **native 3:** nagyon széles használat: vizsga, sport, nehéz helyzet, vigasz
- [ ] *distortion 1:* csak 'good luck' — a kitartásra buzdítás nélkül
- [ ] *distortion 2:* csak a sport-szurkolás kontextus

> A „加油” (jiayou) szó jelentése „olajozz fel” vagy „töltsd fel az üzemanyaggal”, de a mindennapi nyelvben gyakran használják bátorításra, hasonlóan a „csinálj!” vagy „erő!” kifejezéshez. Például, ha valaki vizsgára készül, vagy egy nehéz feladattal küzd, akkor ezt mondhatják neki.

*Bíráló indoklása:* A válasz tartalmazza az eredeti jelentést, a biztatást és a széles körű használatot, valamint nem korlátozódik a szerencsére vagy csak a sportra.

### angol

- [x] **native 1:** szó szerint 'olajat/üzemanyagot adni'
- [x] **native 2:** biztatás erőfeszítés előtt/közben: 'hajrá, tarts ki'
- [x] **native 3:** nagyon széles használat: vizsga, sport, nehéz helyzet, vigasz
- [ ] *distortion 1:* csak 'good luck' — a kitartásra buzdítás nélkül
- [ ] *distortion 2:* csak a sport-szurkolás kontextus

> The Chinese '加油' (jiayou) literally means "add oil," but it is commonly used to mean "go for it," "good luck," or "keep it up." It is often used to encourage someone, such as before a test, a competition, or a difficult task.

*Bíráló indoklása:* A válasz tartalmazza az összes kötelező jelentéskomponenst (szó szerinti jelentés, biztatás, széles körű használat), és nem tartalmazza a megadott torzításokat, mivel a 'keep it up' kifejezés magában foglalja a kitartásra buzdítást, és a példa nem korlátozódik csak a sportra.

### kínai  ⚠️ ismétlési hurok, önértékelő toldalék levágva

- [x] **native 1:** szó szerint 'olajat/üzemanyagot adni'
- [x] **native 2:** biztatás erőfeszítés előtt/közben: 'hajrá, tarts ki'
- [x] **native 3:** nagyon széles használat: vizsga, sport, nehéz helyzet, vigasz
- [ ] *distortion 1:* csak 'good luck' — a kitartásra buzdítás nélkül
- [ ] *distortion 2:* csak a sport-szurkolás kontextus

> “加油”在中文里主要有两个意思：
1. 鼓励、打气：用于鼓励他人，希望对方成功或做得更好。
2. 给车辆加燃料：用于给汽车、摩托车等交通工具添加燃油。
什么时候用？
1. 鼓励、打气：
   - 当朋友、同事或家人遇到困难、挑战或需要支持时。
   - 在考试、比赛、演讲等场合，希望对方取得好成绩时。
2. 给车辆加燃料：
   - 当需要给汽车、摩托车等交通工具添加燃油时。
  assistant：
“加油”在中文里主要有两个意思：
1. 鼓励、打气：用于鼓励他人，希望对方成功或做得更好。
2. 给车辆加燃料：
   - 当需要给汽车、运动员、演讲者等需要支持时。
   - 在考试、比赛、演讲等场合，希望对方取得好成绩时。
2. 给车辆加燃料：
   - 当需要给汽车、摩托车等交通工具添加燃油时。

*Bíráló indoklása:* A válasz tartalmazza mindhárom kötelező komponenst (szó szerinti jelentés, biztatás, széles körű használat), és nem korlátozódik kizárólag a 'good luck' vagy csak a sport kontextusára.

