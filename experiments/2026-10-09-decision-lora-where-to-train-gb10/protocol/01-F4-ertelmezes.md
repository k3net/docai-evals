## Értelmezés (kézzel írt, 2026-10-09; a fenti leíró bontásokra épül)

### Hol nyer és hol veszít az L3

1. **A val-on, eloszláson belül nyer.** A 3 seed lef@95-je 0,723–0,724 (plafon 0,729), az L1★-é 0,682. Az AURC
   0,0026–0,0035, az L1★-é 0,0059. A seedek szórása 0,0006.
2. **A teszt nem-X itemjein szinte hibátlan.** A BFCL és a When2Call nem-X itemjeinek 98–100%-át sorolja be
   @95-ön, 97–100%-os precizitással. Az L1★ ugyanitt 93–100%-ot sorol be.
3. **A teljes precizitásesés az X-itemekből jön.** Az L3 az irrelevancia-itemek nagyobb részét rendeli magabiztosan
   eszközhöz:
   - BFCL-live irrelevance: 43–48% (L1★: 33%);
   - When2Call „cannot_answer”: 27–31% (L1★: 21%);
   - BFCL irrelevance: 26–28% (L1★: 14%).

   A train 3774 X-iteméből 80% gold-drop: a saját gold-drop és az xlam-irrelevance is a helyes eszköz kivételével
   készül, ugyanarra a kérésre. 20% természetes X: 499 When2Call cannot_answer és 255 MASSIVE-csevegés. Ebből a LoRA
   azt tanulta meg, hogy ha van hasonló eszköz, hívja meg. A When2Call-típusú irrelevanciát kis arányban látta, és
   mégis romlott rajta a bázishoz képest. A BFCL-live és a When2Call irrelevanciája más: valódi kérés, közeli, de nem illő eszközökkel. Ez a Hammer-cikk
   kompromisszuma (H5 cáfolt: X-fedés −8,9 pont).
4. **Nem a görbehossz műterméke.** Az AURC a 00 definíciója szerint a kar saját besorolásain fut, így a többet
   besoroló kar hosszabb görbét kap. Közös lefedettségre vágva is az L3 kockázata a nagyobb: a poolon 0,5-ös
   lefedettségnél 0,073–0,080, az L1★-é 0,049. Az L3 a rossz X-besorolásokat magas bizalommal, a rangsor elejére
   teszi.
5. **A T-hu-n a MASSIVE címkézési szokásait is megtanulta.** A réteg 40 átcímkézett itemjéből az L3 18–24-nél a
   régi MASSIVE-címkét adja, mindet a τ fölött; az L1★ 8-nál. Az átcímkézettek nélkül az L3 a T-hu-n is jobb:
   - precizitás 0,964–0,980 (L1★: 0,961);
   - AURC 0,0011–0,0019 (L1★: 0,0028).

   Ez utólagos részhalmaz, ezért csak magyarázat. Azt mutatja, hogy a kemény címkés tanítás a forrás címkézési
   konvencióit magabiztosan beégeti.
6. **A τ egyik karnál sem viszi át a 95%-ot a tesztre.** Az L1★ a poolon 88%-on, az L0 89%-on áll. A val
   X-eloszlása (xLAM, MASSIVE) nem képviseli a teszt irrelevancia-típusait. Ez a docai-0122 éles küszöbválasztásának
   is tanulsága: τ csak a célforgalom X-eloszlásán választható.
7. **Az S2 nem tudja javítani.** A τ alatti 1743 item 96%-a X-gold, és ezek 95%-ánál a bázis gondolkodó módja
   helyesen X-et mond. Az L3 X-hibái viszont a τ fölött vannak, így az S2 elé sem jutnak.
8. **Ami megáll:**
   - a natív tool callingot az L3 a natív munkapontján veri (H3);
   - a két adapter egy példányon, párhuzamos terhelés mellett is hű marad (H4);
   - a permutációs billenés a bázis 7,0%-áról 3,9%-ra esik.
9. **A H2 definíciójának gyengesége.** A H2 a Δ lef@95-öt ítéli meg precizitási feltétel nélkül, ezért ad
   „általánosít” ítéletet mindkét rétegen, miközben ott az L3 precizitása bukik. Előre rögzített szabályról van szó,
   ezért nem írjuk át. A H1 nélkül azonban nincs rá épülő állítás, és a 03-ban a rétegítélet a precizitási
   feltételhez kötött.

### Összevetés a JEV-27B(-VL)-vel

A forrás a HF-kártya (`autotrust/JEV-27B`, `autotrust/JEV-27B-VL`, olvasva 2026-10-09).

| | JEV-27B(-VL) | 01 |
|---|---|---|
| Mihez hasonlít | a tanárhoz (TypeSafe Jev 1.13): KL ≈ 0,017, top-1 egyezés 95,8%, ECE 0,0009 | a kalibrált bázishoz, ugyanazokkal az opciókkal (L1★) |
| Bázis-összevetés | nincs a kártyán | a H1 maga |
| „Egyik sem” opció | nincs, rögzített opciókészlet | X; a poolban ~33% X |
| Kiértékelés | főleg a 53 tanító-domén kitartott sorai; az Open-Jev OOD-részén a KL 0,017 → 0,104, a top-1 0,942 | más eloszlású teszt (BFCL-live, When2Call, javított T-hu) |
| Mérőszám | pontosság, KL, ECE | lefedettség 95%-os precizitás mellett, AURC |
| Szelektív döntés | „usage pattern, not benchmarked” | elsődleges végpont |
| Tanítóadat | 656 ezer sor; KL a tanár teljes eloszlására (puha cél) | 14,5 ezer kemény címke, ε = 0,05 |
| Kalibráció | típusonkénti temperature a saját eloszlásukból (10 954 sor), T ≈ 1,0 | temperature és τ a val-on (xLAM, MASSIVE), T ≈ 0,8 |
| System 1 → 2 | 0,792 → 0,892 pontosság, 70% System 1-ben | az S2 elé szinte csak X jut; a hibák a τ fölött vannak |

**A két eredmény összefér.**
- Amit a JEV mér (eloszláson belüli hűség és pontosság rögzített opciókészleten), abban a 01 L3 is jó, a val-on
  egyértelműen.
- Amin a 01 elbukott (irrelevancia és szelektív precizitás eloszlásváltás mellett, kalibrált bázissal szemben), azt
  a JEV-kártya nem méri.

**F5b: a JEV mérve ugyanezen a kérdésen.** Forrás: `autotrust/jev-decision-index-results`, a gold a kit rögzített
forrásaiból újraépítve. A JEV közölt pontosságai mindkét sávon, mindhárom modellnél pontosan visszajönnek. Eredmények:
`eredmenyek/F5b/f5b_jev.json`, szkript: `kor01/eszkozok/f5b_jev.py`. A JEV-9B és a JEV-27B ezeket a benchmarkokat nem
látta. A JEV-Gemma4 a train-splitjükön is tanult, és a 01 L3 is a When2Call-trainen (1999 item: 1500
request_for_info, 499 cannot_answer), ezért a When2Call-on ez a kettő nem kitartott.

- **When2Call, a 01 tesztjének ugyanazon itemjein** (1293 tool_call és 1035 cannot_answer).
  - Kérdés: hív-e eszközt a modell. A 01 karjainál P(hív) = 1 − P(X), a JEV-nél P(tool_call).

    | kar | AUROC | hamis hívás 90% helyes hívásnál | 95%-nál | hívás a cannot_answer itemeken (top-1) |
    |---|---|---|---|---|
    | L1★ | **0,964** | **8,6%** | **14,1%** | 22,5% |
    | L3 s1–s3 | 0,945–0,959 | 9,5–11,7% | 15,7–17,3% | 27–31% |
    | JEV-9B | 0,953 | 10,4% | 33,4% | 24,3% |
    | JEV-27B | 0,949 | 9,7% | 37,3% | 6,2% |
    | JEV-Gemma4 | 0,943 | 15,1% | 35,7% | 12,0% |

  - A JEV-27B alacsony hívásaránya óvatosabb munkapont, nem jobb szétválasztás: a jó tool_call itemeken is csak 87%-ban
    hív (a 01 karjai 97–99%).
  - Küszöbtől függetlenül a puha célú JEV-27B (a When2Call-t nem látta) sem választja szét jobban a „hívni kell” és a
    „nincs illő eszköz” eseteket, mint a kemény címkés L3 (látta), és mindkettő elmarad a kalibrált bázistól. A
    When2Call-trainen tanult két modell (L3, JEV-Gemma4) sem éri el a bázist.
  - A keretek eltérnek: a JEV négy válaszmód közül választ, a 01 eszközlistából és X-ből. Az itemek azonosak.
- **CLINC150+OOS** (4500 hatókörön belüli és 1000 hatókörön kívüli kérés). Az OOS-felismerés a top-1 alapján:
  - JEV-9B: 21%;
  - JEV-27B: 38%, miközben a hatókörön belüli pontossága 89%;
  - JEV-Gemma4 (az OOS-t is tanulta): 67%.

  95%-os precizitáshoz (keresztillesztett τ) a JEV-27B a kérések 49%-át sorolja be, a plafon 82%.
- **Következtetés:** a puha cél önmagában nem védi ki az irrelevancia-csapdát. Az X-típus tanítása segíthet (a
  CLINC-OOS-on a JEV-Gemma4 38 → 67%), de a When2Call-szétválasztásban a rajta tanult modellek közül egyik sem éri el
  a kalibrált bázist.

**A különbségek súlya, az F5b után:**
1. **Az X-típus lefedése a trainben** a legvalószínűbb kar, de nem elégséges. A JEV-27B a nem látott X-típuson
   (CLINC-OOS, When2Call) ugyanúgy gyenge, mint a 01 L3. A tanítás a CLINC-on javított, a When2Call-on a 13%-os
   train-X arány (01 L3) és a teljes train-split (JEV-Gemma4) sem hozta a bázis szintjére.
2. **Puha célok kemény címke helyett.** Az irrelevancián az F5b szerint nem segít. A konvenció-beégést (5. pont)
   csökkentheti, ez nem mért; a 03 H6-ja méri.
3. **A kalibrációs minta a saját eloszlásukból jön.** A 01-ben a val X-eloszlása eltér a tesztétől (6. pont).
4. **Méret és változatosság:** 53 domén és 656 ezer sor, a 01-ben két forrás és 14,5 ezer sor. Az X-csapdát ez sem
   oldotta meg.

A 24 slotos `lm_head`-fej és a template nélküli prompt nem mutat érdemi különbséget; erre nincs bizonyítékunk egyik
irányba sem.

**Kétlépcsős próba** (utólagos, a fenti táblában). Ha a hívjon-e kérdést a bázis dönti el és az eszközt az L3, az X-fedés
visszajön a bázis szintjére (0,762). A lefedettség viszont csak ~1 ponttal nő (0,726 vs. 0,717), és a val-τ
precizitása így is bukik. A 01 feladaton a döntési fej értéke az X-kezelésben lett volna; az eszközválasztásban a bázis
már eleve szinte hibátlan.

### Következmények a 03-ra (03-runbook v0.2)

- **Valódi irrelevancia a trainben**, nem csak gold-drop, nagyobb arányban. Az F5b szerint ez a legvalószínűbb kar,
  de egyedül nem bizonyítottan elég.
- **Horgony a bázishoz az X-viselkedésre** (KL a bázis eloszlására). Az F5b ezt alátámasztja: a hívás/nem hívás
  szétválasztásában a kalibrált bázis a legjobb.
- **Puha célok Apache-2.0 tanártól** (Mistral Small 4, Gemma 4 26B-A4B-it, Qwen3.6 gondolkodó mód). Az irrelevanciára
  az F5b szerint önmagukban nem elegendők; a konvenció-beégés ellen a H6 méri őket.
- **A kalibrációs minta a célpiaci eloszlásból.**
- **A rétegítélet a precizitási feltételhez kötött.**
