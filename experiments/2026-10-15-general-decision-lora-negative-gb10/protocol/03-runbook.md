# Runbook 03: általános magyar döntési LoRA, kitartott feladatcsaládokon mérve

**Egy döntési LoRA sok feladatcsaládon tanítva: hozza-e a feladatspecifikus LoRA-k nyereségét olyan családon,
amelyet nem látott? A mérés a 00 és a 01 befagyasztott, emberileg átnézett tesztjein megy.**

- **Verzió:** v1, rögzítve 2026-10-14-én (Dani jóváhagyásával; 7. pont, 10. pont 18.). **Státusz:** az F0–F4 kész
  (2026-10-14; Napló). A H1 mindhárom kitartott rétegen „nem teljesíti a követelményeket”: a lefedettség nő, de a
  precizitás a 0,93 alatt marad ([eredménylap](kor03/eredmenyek/F4/eredmenylap.md)). A továbblépés: [04-runbook](04-runbook.md) (v0.1 vázlat, 2026-10-15).
  - A 01 F4 lezárult (2026-10-09, [eredménylap](kor01/eredmenyek/F4/eredmenylap.md)):
    - a feladatspecifikus L3 eloszláson belül nyer;
    - a kitartott teszten az irrelevancián bukik, és a forrás címkézési konvencióit magabiztosan beégeti.

    Ezért a 03 receptje valódi irrelevanciára (négy X-típus) és bázis-horgonyra épül. A tervezett puha tanárcél
    (Apache-2.0 tanár) elmaradt, mert a négy tanárjelölt egyike sem ment át a kapun (10. pont 14.).
  - **A recept, ahogy ténylegesen fut:** a G3 az MVP v2-n tanult (17 500 item), a cél a gold ε = 0,05-tel + 0,5 · Brier
    \+ β · KL(p_L1★ ‖ p_modell) az X-gold itemeken, β = 0,5; a G3-kemény ugyanez β = 0-val.
- **Gép, alany, infrastruktúra:** mint a 00/01-ben (spark-dev, `Qwen/Qwen3.6-35B-A3B-FP8` MTP nélkül, vLLM
  v0.30.0, `lora-train:2`, leválasztott futások).
- **Bemenetek:**
  - [magyar-dontesi-tanitoanyag-otletek.md](magyar-dontesi-tanitoanyag-otletek.md): ötletanyag;
  - [jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md](jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md): HF-felmérés,
    licenccsoportok;
  - [open_datasets_research.md](open_datasets_research.md): külső kutatási anyag. Két licencadata téves vagy
    ellentmondásos, ld. 3.;
  - a 00 és a 01 leletei (0. pont).
- **Végtermékek (terv):**
  1. magyar döntési adatkészlet, licencenként külön konfigurációban;
  2. HF általános döntési adapter, ha az eredmény engedi;
  3. tanulmány.

> A hipotéziseket, a végpontokat, a kitartott családokat és a döntési szabályokat mérés előtt rögzítjük. A v1
> rögzítve: 2026-10-14, az F4 összehasonlító eredményeinek megtekintése előtt (`kor03/rogzites/v1/`, 7.10).

---

## 0. Kiindulás

### Amit a 00/01-ből tudunk (2026-10-09)

| megállapítás | forrás |
|---|---|
| A kalibrált címke-kiolvasás és a döntési LoRA működik. A LoRA nyeresége lef@95-ön +13,7 pont 25% X mellett; 10% X mellett már csak +3,5. A nyereség zöme az X-ből jön | 00 tanulmány |
| A nyereség új szállítókra is átvihető: +19,5 [10,2; 29,2] | 00b |
| Gold-drop előtt kötelező a szinonimaszűrés. A 00-ban 12/99 címke volt hibás; a 01-ben az `xdrop` szűrő kezeli | 00 F1F, 01 F1S |
| A forrás-gold sem zajmentes. A MASSIVE hu intent → eszköz leképezés zaja 12,8% a T-hu-részhalmazon, a T-katalógusé 7,0% | 01 átnézés, 2. adag |
| A bírálói egyetértéses szűrés nem elég, és a tesztet a „bírálónak könnyű” itemek felé torzítja | 01 átnézés, 1. adag |
| A nem-Qwen bírálók X-ben gyengék. A 00 feladaton az X-recall Llama-3.3: 4–10%, Mistral Small 4: 1–3%; a gold-egyezés 58–67%, illetve 41–50% | 00 F1D |
| Gépi címke-átnéző csak emberi vak szúrópróbával fogadható el. Az „átnézett tesztcímke” állítás emberi átnézést jelent | 01 Napló, 2026-10-07 |
| Az `--enable-lora` a MoE-kernelt DeepGEMM-ről Tritonra váltja, a LoRA nélküli forgalom ~6%-a billen | 00 H3(d) |
| Plafonhatás: túl könnyű val mellett a karválasztás zajra dönt | 00 F3 |
| Tréningidő: ~3 óra/epoch 5593 itemre (00 F3 pilot, rövid promptok), azaz ~1,9 ezer item/óra | 00 Napló |
| A 01 L3 a val-on nyer (lef@95 0,724 vs. 0,682, plafon 0,729), a kitartott teszten a H1 cáfolt. A poolon a precizitása 0,84, a cél 0,95; az AURC az L1★ javára mutat (+0,028) | 01 F4 |
| A precizitásesés teljes egészében az X-itemekből jön. A nem-X itemeken az L3 98–100%-ot sorol be, 97–100%-os precizitással. A valódi irrelevanciát (BFCL-live, When2Call) viszont gyakrabban rendeli magabiztosan eszközhöz (X-fedés −8,9 pont). A train X-e zömmel gold-drop volt | 01 F4, leíró bontás |
| A kemény címkés tanítás a forrás címkézési konvencióit magabiztosan beégeti: a T-hu 40 átcímkézett itemjéből az L3 18–24-nél a régi MASSIVE-címkét adja, mindet a τ fölött | 01 F4, leíró bontás |
| A val-on választott τ egyik karnál sem viszi át a 95%-ot egy más X-eloszlású tesztre, a kalibrált bázisnál sem (0,88) | 01 F4 |
| Az S2 (a bázis gondolkodó módja) a τ alatti sávban az X-et 95%-ban helyesen ismeri fel. A magabiztos hibákat viszont nem kapja meg | 01 F4, L3→S2 |
| Két adapter egy vLLM-példányon, párhuzamos terhelés mellett is hű marad (01 H4) | 01 F4 |
| Ott érdemes tanítani, ahol a bázis gyenge: a 00-ban a bázisnak volt hová fejlődnie (lef@95 0,616, plafon 0,756), és a LoRA nyert; a 01-ben a bázis eleve közel volt a plafonhoz (eszközválasztás, AUROC 0,964), és a LoRA rontott (Dani, 2026-10-09) | 00 és 01 F4 |
| JEV-27B: 30% opció-permutáció a sorrendbillenést 41%-ról 2,9%-ra vitte; a „use when” opcióleírás +2,5–4,8 pont (saját közlésük) | JEV-kártya |
| A JEV puha célokkal (KL a tanár eloszlására) tanít, 656 ezer soron, „egyik sem” opció nélkül | JEV-kártya |
| A puha cél önmagában nem védi ki az irrelevancia-csapdát. A 01 When2Call-itemjein a hívás/nem hívás AUROC-ja: JEV-27B 0,949, L3 0,945–0,959, kalibrált bázis 0,964. A CLINC-OOS-t a JEV-27B 38%-ban ismeri fel; a JEV-Gemma4, amely az OOS-t is tanulta, 67%-ban. A When2Call-típust a 01 L3 13%-os train-X aránnyal, a JEV-Gemma4 a teljes train-splittel látta, és egyik sem éri el a bázist: az X-típus tanítása segíthet, de nem bizonyítottan elég | 01 F5b |
| Ha a hívjon-e kérdést a bázis dönti el, és csak az eszközt választja a LoRA, az X-fedés megmarad, de a nyereség ~1 pont: a 01 feladaton a bázis eszközválasztása már eleve szinte hibátlan | 01 F4, leíró bontás |

### Amit nem tudunk, és ezért lenne ez a kör

1. Átviszi-e egy sok családon tanított döntési LoRA a nyereséget olyan családra, amelyet nem látott? Konkrétan: a
   számla → cikk és az eszközválasztás családra.
2. Mekkora ez a nyereség a feladatspecifikus LoRA-éhoz képest, ugyanazon a teszten? Ez az ötletanyag 6. fejezetének
   nyitott kérdése.
3. Átvihető-e a kalibráció? Egy közös val-on illesztett temperature és τ tartja-e a precizitást egy új családon,
   amelynek nincs saját val-ja? Élesben egy új feladatnál épp ez a helyzet.
4. Segít-e egy licencszűrt angol tipizált döntési gerinc a magyar családokon?
5. Kivédi-e a négy X-típus, a bázis-horgony és a puha cél (Apache-2.0 tanár eloszlása) a 01-ben mért két hibát? Az
   egyik az irrelevancia-kompromisszum, a másik a címkekonvenció magabiztos beégése. Az F5b szerint a puha cél egyedül
   az elsőt nem oldja meg, és a kis arányú X-típus-lefedés sem volt elég (0. pont). Ezért itt az X-típusok nagyobb
   aránya és a horgony az elsődleges kar, és nyitott, hogy együtt elérik-e a kalibrált bázist. (A puha cél a 03-ban
   tanár híján elmaradt, 10. pont 14.; a kérdés így a horgonyra és az X-típusokra szűkül, H6.)

---

## 1. Kutatási kérdés

Egy kis döntési LoRA, amelyet sok magyar (és legfeljebb 25%-ban angol) feladatcsaládon tanítunk ugyanazzal a
címkeformával (A–J + X), kalibráltabb és lefedettebb döntést ad-e egy kitartott családon, mint a kalibrált
logit-kiolvasás? És a feladatspecifikus LoRA nyereségének mekkora részét hozza?

**Hatókör:** `choice` és kétopciós `noul`. A `score` kimarad az MVP-ből (2. pont).

---

## 2. Feladatforma

- **Item:** állapot (szöveg) + kérdés + 2–10 opció + X („egyik sem”). Az opcióknak opcionálisan van „use when”
  leírásuk.
- **Címkék és kiolvasás:** ugyanaz, mint a 00/01-ben. A–J + X, egytokenes címkék, a címkékre szűkített softmax.
  - Nincs A–P: a publikált `decision_prompt.py` A–J-t használ, és az átvihetőség feltétele a közös címkekészlet.
  - 10-nél több opció esetén előszűrés (jelöltgenerálás) vagy kizárás.
- **`kind`:**
  - `choice` a fő forma;
  - `noul` kétopciós choice („A) igen”, „B) nem”), plusz X, ahol a forrás ismeri a „nem eldönthető” esetet
    (HuCommitmentBank, MILQA). Nincs külön true/false token: ugyanaz a kiolvasás és ugyanaz a lef@95-definíció
    (az F0-ban így épült, a v1-ben rögzítve);
  - `score` kimarad: egytokenes CE-vel a skála sorrendje elveszik, a lef@95 pedig elfogadás/elutasítás döntésre van
    definiálva. Stretch: sorrendezett choice puha céllal, saját metrikával (MAE, várható érték).
- **Prompt:** chat template, thinking off, egyetlen közös promptépítő (`kozos03.render`) generikus kerettel:
  „Állapot / Kérdés / Opciók”.
  - A kitartott 00/01-tesztek kétféleképpen futnak:
    - **elsődleges:** a saját, eredeti promptjukkal. Ezzel mértük a specifikus LoRA-kat, és élesben is ez fut;
    - **másodlagos:** a generikus kerettel.
  - Egységteszt: a `kozos03.render` a 00/01 itemjeire bájtra ugyanazt a promptot adja, mint a 00 `decision_prompt.py`
    és a 01 `keret.py`.
- **Keretnyelv:** az item nyelvét követi (01, 2. pont).
- **X:**
  - Családonként 10–30%. Legalább két családban 0%, hogy a modell ne tanulja meg a konstans gyanakvást.
  - **Négy X-típus**, mert a 01-ben a csak gold-drop jellegű train-X nem vitte át az irrelevancia-felismerést (0.
    pont). Egyik típus sem haladhatja meg az X-itemek 50%-át (a pool-ban; az MVP v2-ben 60%, 10. pont 17.):
    1. **gold-drop hard-NOTA-val:** a gold kikerül a listáról, de rokon, nem azonos jelölt marad (a 00 S7/S8
       mintájára). Csak szinonimaszűréssel (4.3);
    2. **természetes megválaszolhatatlan:** a forrás maga jelöli (MILQA, HuCB „nem eldönthető”);
    3. **valódi hatókörön kívüli kérés:** olyan állapot vagy kérés, amelyre a lista egyik opciója sem vonatkozik,
       de a lista felületesen közeli. A forrása egy másik család állapota ugyanazzal a listával, vagy generált kérés
       a 3.5 receptjével;
    4. **hiányzó feltétel:** az opció illene, de az állapotból hiányzik a döntéshez szükséges adat, a
       routing-csoporton kívüli családokban. A When2Call-ban ez a `request_for_info` esete; a `cannot_answer`
       („egyik eszköz sem illik”) a 3. típus (javítva 2026-10-09, `kozos03.x_type_01`).
  - Az X-fedést típusonként is jelentjük (01 leíró bontás mintájára).
- **Opciószám:** 2–10, a forrásoknál egyenletesebb eloszlással; nehéz és könnyű disztraktorokkal.
- **Opcióleírás:** a choice itemek ~50%-ánál „use when” leírás. Opciótípusonként egyszer generáljuk Apache-2.0
  modellel. Egy másik családú Apache-2.0 modell ellenőrzi, hogy a leírásból visszaválasztja-e az opciót; ami
  elbukik, leírás nélkül marad (emberi ellenőrzés nincs, 4.6).
- **Permutáció:** az itemek 30%-a véletlen opció-permutációval tanul (a 01 L3 receptje). Egy forrás-item minden
  változata ugyanabba a splitbe kerül.

---

## 3. Adatforrások — átvilágítva 2026-10-07-én

A licencadat a HF-kártyáról vagy a forrás repójából származik, a 2026-10-04-i felmérést kiegészítve.

> **Javítás az `open_datasets_research.md`-hez:**
> - **MultiEURLEX:** a HF-kártya szerint CC-BY-SA-4.0, nem CC BY 4.0.
> - **SIB-200:** a HF-en CC-BY-SA-4.0, a repó Apache-2.0-t ír. Ellentmondás esetén a szigorúbbat követjük.

### 3.1. Magyar, emberi címkés források

| forrás | méret | licenc | szerep | megjegyzés |
|---|---|---|---|---|
| MASSIVE hu-HU | 11 514 / 2 033 / 2 974 | CC-BY-4.0 | **a routing-csoporttal kitartva** (5.) | a test a 01 T-hu, a dev a 01 val-massive; az intentleképezés zaja ~13% |
| HuRTE, HuCOLA, HuWNLI, HuCommitmentBank | 250–9 076 | CC-BY-SA-4.0 | train; a val a teszt | a test címkéi rejtettek („distributed without the labels”, HuCOLA README); a HuCB „nem eldönthető” esete → X |
| HuSST | 9 347 / 1 168 / 1 168 | HF: BSD-2-Clause, GitHub: CC-BY-SA-4.0 → CC-BY-SA | train; a val a teszt | szentiment choice-ként, `score` nélkül |
| HuCoPA | 400 / 100 / 500 | BSD-2-Clause | train | kicsi |
| HuRC | 64 614 train | CC-BY-4.0 | train | cloze entitásválasztás + gold-drop X |
| HuBoolQ | 10K–100K | CC-BY-SA-3.0 | **kizárva** (2026-10-09) | a kártya szerint Google Translate + GPT-4o mini átírás: a 3.6 szerint csak Apache-2.0 fordító, zárt modell kimenete nem |
| MILQA | > 23 500 | CC-BY-SA-4.0 | train; a test tilos | természetes megválaszolhatatlan → X |
| MultiEURLEX hu | 22 664 / 5000 / 5000 | CC-BY-SA-4.0 | train, HO-forrás jelölt | EuroVoc-hierarchia → nehéz negatívok; hosszú szöveg; az 1. szint 21 területének magyar neve a Kiadóhivatal RDF-jéből |
| NerKor | ~1 M token, 67 ezer mondat; train/devel/test | CC-BY-SA-4.0 | train | entitástípus choice; a jogi alkorpusz EU-forrású (DGT-, JRC-Acquis): a MultiEURLEX-szel szivárgás-audit kell |
| Belebele hun_Latn | 900 | CC-BY-SA-4.0 | **csak eval** | FLORES-200-szöveg |
| SIB-200 hun_Latn | 701 / 99 / 204 | CC-BY-SA-4.0 (HF) | **csak eval** | FLORES-200-mondatok: a Belebele-vel közös szöveg, ezért egyik sem lehet train |
| OpinHuBank | — | tisztázatlan (META-SHARE: CC-BY, lábléc: CC BY-NC-SA 3.0) | **kizárva** | |

Minden „gold” forrás csak a gépi zajbecslés után számít goldnak (4.2).

### 3.2. Nyilvános magyar üzleti és közigazgatási szöveg

| forrás | licenc | szerep | megjegyzés |
|---|---|---|---|
| TED-hirdetmények (HU) | szabad újrahasznosítás (2011/833/EU); a szerkesztett tartalom CC BY 4.0 | train; egy CPV-főcsoport HO-forrás | hirdetmény → CPV-főcsoport choice + X, 2. szintű finomítás. **PII:** a kapcsolattartó neve, e-mailje és telefonja kiszűrendő. Napi/havi XML-csomag, bejelentkezés nélkül |
| Közbeszerzési Értesítő (hazai, értékhatár alatti) | saját feltételek | **kimarad**, amíg nincs átnézve | a TED-licenc nem fedi |
| Nemzeti Jogszabálytár | a jogszabályszöveg nem védett (Szjt. 1. § (4)): közkincsként használható (Dani, 2026-10-09) | train | bekezdés → törvény/fejezet; „kötelezettséget állapít meg?” `noul`; hatályos vs. módosított szöveg |
| KN/VTSZ magyar leírások | EU-dokumentum (2011/833/EU), ellenőrizendő | **termék-csoport, kitartva** | termékleírás → árucsoport; a számla → cikk családhoz túl közeli |
| Cégadat (TEÁOR, entitásegyezés) | csak nyílt forrásból | feltételes | **tenantadat kizárva.** Az e-cégjegyzék tömeges felhasználási feltételei ellenőrizendők; ha nincs tiszta forrás, kimarad |
| Wikipédia + Wikidata | CC-BY-SA-3.0 vagy GFDL (a HF `wikimedia/wikipedia` 20231101.hu pillanatképe; a CC-BY-SA-3.0-t választjuk), CC0 (Wikidata) | train | főleg a 3.4 konstrukcióinak forrásszövege |

### 3.3. Angol tipizált döntési gerinc (licencszűrve; csak a G3 karban, H4)

- **Train** (pontosítva 2026-10-09, a kártyák és a build-dokumentáció alapján):
  - `tasksource/tasksource-jev-typed-decisions`, a **`full`** konfiguráció. A `default` keveréket Jev-ítéletek
    súlyozták (forráspontszám, „zone of proximal development”, érdekesség), ezért nem azt használjuk; a `full`-ban a
    címke a forrásadatkészletből jön determinisztikus átírással, a Jev csak a forrásonkénti sorplafont befolyásolta.
    - csak `license_use == "commercial"`, és a sor minden licence megengedő vagy SA: a GPL, AGPL, MPL, ODbL,
      „Custom” és „other” kimarad;
    - **kitartás-lista** forrásnév szerint (`kor03/adat/f0/adapter_angol_riport.json`): routing (CLINC, BANKING77,
      MASSIVE, MTOP, SNIPS, intent-, eszköz- és ügynökdöntés), termék (ESCI), KIE/validáció-rokon (számtan,
      matematika, időbeli következtetés, táblázat), eval-szivárgás (COPA/XCOPA: a HuCoPA forrása; WinoWhy: a HuWNLI
      forrása), zárt modell címkéje (UltraFeedback, WildGuardMix: GPT-4), nem angol (`multilingual/*`);
  - `tasksource/procedural-typed-decisions` (Apache-2.0), 9 feladat: az arithmetic, a record_aggregation, a
    table_lookup (KIE-rokon) és a taxonomy_routing (routing) kimarad;
  - az `Open-Jev` CC0 része, 7 kontroll-konfiguráció: a release-v2 és a browser-drone (ügyfélszolgálati routing,
    ellenőrizetlen licencű leírások) és az amount/email/phone-extraction (KIE) kimarad.
- **Csak eval:** `LocalLLaMA/typed-decisions` test, `fastino/fast-decisions`.
- **Kizárva:**
  - Jev-desztilláció: `tasksource/synthetic-typed-decisions`, `jev-distill-corpus-v3`;
  - `helmo/synthetic-typed-decisions`: a címkéket (valószínűség-eloszlásokat) a DeepSeek-V4-Flash generátor írta,
    ellenőrzés nélkül. A generátor nem Apache-2.0 (9.), és a tanárcél csak kapun átment tanártól jöhet (4.1).
- **Arány:** a train 25%-a (Dani, 2026-10-09), hogy a magyar nyelvi illeszkedés ne sérüljön. A G3-hu kar
  (6.) ugyanaz gerinc nélkül, így a H4 a gerinc hatását méri.

### 3.4. Konstrukciós családok

A gold Pythonból vagy a szöveg szerkezetéből jön; a forrásszöveg az NJT, a Wikipédia és a TED.

- `continuation.next_sentence`, `order.paragraph`, `cloze.word`, `heading.match`, `headline.match`,
  `register.detect`, `duplicate.near`. Az F0-ban elkészült (2026-10-09): a Wikipédiából a szakaszcím- és a
  következőmondat-választás, az NJT-ből a törvény-, fejezet- és címválasztás (`adapter_wiki.py`, `adapter_njt.py`);
- a **KIE/validáció** csoport a HO-új-család (5.). Specifikáció: [kor03/spec/kie_validacio.yaml](kor03/spec/kie_validacio.yaml),
  generátor: `kie03.py`, független ellenőrzés: `test_kie03.py`.
  - **Dokumentum:** szintetikus magyar számla, három szövegformában (táblázatos, folyószöveg, OCR-szerű), változó
    szám- és dátumformával; kitalált nevek, a 99-es törzsszám- és a 999-es bankkód-tartományból vett azonosítók,
    érvényes ellenőrző számjeggyel.
  - **Családok és kérdések:**
    - `kie.osszeg` (numeric.consistency): melyik tételsor hibás; egyezik-e a végösszeg; mennyi az ÁFA-tartalom;
    - `kie.datum` (date.reasoning): a számolt fizetési határidő; késedelmes-e a fizetés; melyik a teljesítés dátuma;
    - `kie.mezo` (KIE-mezőellenőrzés): melyik érték a kérdezett mező; egyezik-e a kinyert érték a dokumentummal.
  - **X:** természetes (egyik sor sem hibás) és hiányzó feltétel (a döntéshez szükséges adat nincs a dokumentumban).
  - **Gold:** az adatszerkezetből. A teszt a renderelt szövegből, a generátor függvényei nélkül számolja újra; a
    mutációs próbán mind a 2400 elrontott goldot elkapja.

Ezek olcsók, de shortcutot hordozhatnak, ezért arányuk legfeljebb 15%. Családonként shortcut-baseline fut rajtuk
(5.).

### 3.5. Szintetikus családok

Apache-2.0 generátorral készülnek: szándékolt címke, utána független ellenőrzés.

- **Családok:**
  - levél- és ügyféltriage;
  - dokumentumtípus;
  - szerződésklauzula;
  - entitásegyezés (cég, személy, cím);
  - RAG-relevancia és -alátámasztás;
  - válaszbírálat;
  - hivatali ügytípus.
- **Nem generálunk** eszközválasztást és termékpárosítást: ezek a kitartott csoportokba tartoznak.
- **Specifikáció:** [kor03/spec/szintetikus_csaladok.yaml](kor03/spec/szintetikus_csaladok.yaml) (családonként
  kérdések, opciók, X-típusok, szcenárió-dimenziók, generátor és ellenőrző, a kitartott csoportoktól tiltott
  kérdésformák).
- **Recept** (az ötletanyag 2.D pontja szerint):
  1. családspecifikáció (YAML);
  2. szcenárióváz;
  3. állapotszöveg;
  4. független visszacímkézés;
  5. ellentényes minimális szerkesztés: a címkét átfordító egy-két szavas módosítás.
- **Címkeszabály:**
  - a generáló szándékolt címkéje a gold-jelölt;
  - a független ellenőrző más családú Apache-2.0 modell; ha eltér, az item kétértelmű (nem pontozott, soft) vagy
    eldobjuk;
  - **a tanított alany családja (Qwen) sem generátor, sem ellenőrző** (Dani, 2026-10-10; 10. pont 11.). A
    generátor a Muse-Glimmer-30B (hat család) és a Mistral Small 4 (RAG-relevancia), az ellenőrző mindenütt a
    Gemma 4 26B-A4B-it;
  - **az ellenőrzőt validálni kell** a val forrás-goldján, az ellenőrző saját szabályával (`ellenorzo_valid03.py`):
    címketömeg-medián ≥ 0,9, X átmenő aránya ≥ 0,5, nem-X legfeljebb 10 ponttal a Gemmáé alatt;
  - családonként gépi zajbecslés (4.2); emberi zajaudit nincs (4.6).

### 3.6. Kizárva vagy feltételes

- **DocAI éles javítások** (az ötletanyag 2.E pontja):
  - a publikus LoRA tanításába soha nem kerülnek;
  - belső eval-ként is csak aggregátum hagyja el a laptopot;
  - a 7 hozzájáruló tenant engedélye nem terjed ki publikus modellre.
  - A 02-es kör belső irattípus-adata ugyanígy legfeljebb belső eval.
- **GVH Árfigyelő és KRTK adatai:** az adatkérési megállapodás köti őket.
- **NC/NC-SA források:** listájuk a 2026-10-04-i jegyzőkönyvben.
- **Zárt modellek kimenete** (GPT, Jev, Claude stb.): sem címke, sem soft target, sem címke-átnéző a tanítóadat
  láncában. Ez a 01-es lelet. A JEV-modellek kimenete (az `autotrust/jev-decision-index-results` valószínűségei is)
  Jev-desztilláció, ezért ugyanígy kizárva; külső összevetésre használható (5. pont).
- **Fordított angol készletek:**
  - a CLINC és a BANKING77 a routing-csoportba tartozik, ezért kitartva;
  - egyéb fordítás legfeljebb a train 10%-a, Apache-2.0 fordítóval, visszafordításos szűréssel;
  - eval-forrás nem lehet fordított.

---

## 4. Címkézés és tanár

1. **A tanítási cél: gold és tanár keveréke** (Dani, 2026-10-09, a 01-lelet után).
   - A 01-ben a kemény címke a forrás konvencióit magabiztosan beégette, és a kalibráció nem vitte át (0. pont). Ezért
     a cél nem a gold egyedül, hanem
     `cél = (1 − α) · gold + α · tanár`,
     ahol a tanár a kalibrált, kapun átment tanárok eloszlásának átlaga (4.4). Az α = 0,5 (10. pont 10.).
   - **A 03-ban egyik tanár sem ment át** (négy jelölt, 4.4; Napló, 2026-10-11): α = 0, a cél a gold
     (10. pont 14.).
   - **A gold rangsora** (melyik címke számít gold-nak, ha több van):
     1. forrás-gold;
     2. konstrukciós gold;
     3. ellenőrzött szintetikus szándékolt címke.
   - **Ahol nincs gold**, a cél a tanáreloszlás egyedül; csak kapun átment tanártól, és X-es családon csak X-kapus
     tanártól.
   - **Tanár–gold ellentmondás:** ha a tanárok átlagos top-1-e eltér a goldtól, és a bizalma ≥ 0,8, az item
     kimarad a tanításból (emberi döntés nincs, 4.6). Az arányát családonként jelentjük, és a gépi zajbecslésbe
     is beszámít (4.2). A 01 T-hu-átnézése szerint pont ezek a tételek hordozzák a forrás konvenciós hibáit.
2. **Gépi zajbecslés forrásonként és családonként** (Dani, 2026-10-09: emberi átnézés nincs, 4.6):
   - 300 train-item, három független kiolvasással: a kapun átment tanárok és a Qwen3.6 gondolkodó módja;
   - **zajjelölt** az item, ahol legalább két modell ≥ 0,8 bizalommal egyezik egymással, és eltér a goldtól;
   - a zajjelöltek aránya a gépi zajbecslés; ha > 10% (10. pont 10.), a forrás kimarad, egyébként
     a zajjelöltek nélkül marad bent;
   - **korlát:** a gépi egyetértés a könnyű itemek felé torzít, és a forrás konvencióit sem feltétlenül ismeri fel
     (01, 0. pont). Ezért a becslés nem helyettesíti az emberi auditot: a forrás-gold rétegek csak leíróak (4.6);
   - az eredmény a forrás `meta.zaj_becsles` mezőjébe kerül.
3. **Szinonimaszűrés** gold-drop és disztraktorkeverés előtt, a 00 S7 és a 01 `xdrop` receptjével: két bíráló,
   mindkét sorrendben; ha bármelyik P(igen) ≥ 0,5, az opció cserélődik.
4. **Tanár (soft target):**
   - Csak Apache-2.0 vagy MIT licencű modell.
   - **Jelöltek** (Dani, 2026-10-09):

     | jelölt | licenc | méret | mellette | ellene |
     |---|---|---|---|---|
     | Mistral Small 4 (`mistralai/Mistral-Small-4-119B-2603-NVFP4`) | Apache-2.0 | 119B, ~6B aktív | a Sparkon bevált recept (`lib.sh mistral_start`); a 00/01-ben bíráló és generátor | a 00-ban X-recall 1–3%; a 01 T-katalógusát ez írta és bírálta (körkörösség, 11. pont) |
     | Gemma 4 26B-A4B-it (`google/gemma-4-26B-A4B-it`) | Apache-2.0 (HF-kártya, 2026-10-09) | 25,2B, 3,8B aktív | más modellcsalád, egyik 01-réteg előállításában sem vett részt; kicsi és gyors; natív function calling; erős döntési alap: a JEV-recepttel a Decision Indexen 58,05, a Qwen-alapú JEV-27B 53,30 (a Gemma-változat a benchmarkok train-splitjein is tanult, ezért ez csak irányjelzés) | a magyar nincs a kártya 35+ kiemelt nyelve közt (140 nyelv az előtanításban); a vLLM v0.30 támogatása a Sparkon ellenőrizendő |
     | Qwen3.6-35B-A3B gondolkodó módban | Apache-2.0 | az alany maga | önmaga-desztilláció, a JEV System 2 logikája; a 01-ben a τ alatti sávban az X-et 95%-ban helyesen ismerte fel | nem független a bázistól, ezért a bázis hibáit is átadhatja. **Kapu: elbukott** (top-1 0,828 vs. 0,818, ECE 0,129); a 03-ban nem fut tovább (10. pont 16.) |
     | Qwen3.8-27B-FP8 (Dani, 2026-10-11, a három jelölt kapuja után) | Apache-2.0 | 27B dense | a bázis ~3B aktív paraméterének kb. kilencszerese, újabb generáció; a vLLM v0.30 ismeri (`Qwen3_5ForConditionalGeneration`); nem gondolkodó logprob-kiolvasás, mint a Gemmánál | a tokenizere és az előtanítási vonala közös a bázisával, így a vakfoltjai is közösek lehetnek (a kapu típusonkénti X-feltétele ezt méri); a jelölt a kapu eredményének ismeretében került be, a szabály változatlan. **Kapu: elbukott** (top-1 0,798 vs. 0,816, ECE 0,030) |

   - **Tanárkapu**, családonként, a forrás- vagy konstrukciós gold val-itemein, szűretlenül (hogy a kapu ne a
     tanárok saját zajszűrésén mérjen), temperature-fit után (így futott, 2026-10-11):
     - top-1 pontosság ≥ az L1★-é;
     - ECE ≤ 0,05;
     - X-es családon az X-fedés ≥ 0,5, típusonként (2. pont).

     Aki nem megy át, az adott családon nem ad soft targetet. Ha két tanár átmegy, a cél a kalibrált eloszlásaik
     átlaga.
   - **Kiolvasás:**
     - nem gondolkodó módban logprob a címketokenekre, a tanár saját tokenizálójával, k = 4 permutáció átlaga;
     - gondolkodó módban n = 8 minta empirikus eloszlása. A 03-ban 600 val-itemen 4 minta (2026-10-10, a napló).
   - **Az eval-függetlenség szabálya:** egy tanár nem lehet egyetlen bírálója vagy generátora egy olyan
     eval-rétegnek, amelyen a tanított kart mérjük. Ha a Mistral tanár, a T-katalógus a HO-routingban csak
     leíró.
5. **Llama** (Dani, 2026-10-07): szűrhet (szinonima, duplikátum, eldönthetőség) és kijelölhet, de címkét és soft
   targetet nem ad.
6. **Nincs új emberi átnézés** (Dani, 2026-10-09). Emberileg átnézett címke csak a 00/01 befagyasztott
   HO-tesztjeiben van, és ezek változatlanok. Ebből következik:
   - **megerősítő állítás** (H1–H4, H6) csak a HO-termék, a HO-routing (a 01 megerősítő tesztje, a T-hu-maradék
     nélkül; 7.3) és a konstrukciós goldú HO-új-család rétegen áll; a teszt-ID, a HO-forrás, a T-hu-maradék és a
     külső evalok leíróak;
   - a gépi átnéző csak a train-t szűri; tesztcímkét nem állít át, mert a 01 szabálya szerint emberi vak
     szúrópróba nélkül nem fogadható el;
   - a H3 célréteg-kalibrációs mintája a HO-tesztek emberileg átnézett itemjeiből jön, a HO-új-családon a
     konstrukciós goldból: új címkézés nem kell;
   - a KIE/validáció konstrukcióját egységteszt ellenőrzi (a gold Pythonból számolt, 3.4).
7. **Veszteség:**
   - KL a keverék-célhoz (4.1) a jelen lévő címkéken + 0,5 · Brier; a label smoothing (ε) a puha cél mellett
     elmarad, puha cél nélkül ε = 0,05. **A 03-ban puha cél nincs** (10. pont 14.): a cél a gold ε = 0,05-tel
     (CE + 0,5 · Brier);
   - **bázis-horgony:** β · KL(p_bázis ‖ p_modell) a bázis perm-átlagolt, kalibrált eloszlására (L1★), az X-gold
     itemeken. Ez a 01 H5-kompromisszumának közvetlen ellenszere: a modell ott ne távolodjon a bázistól, ahol a
     bázis az irrelevanciát jobban ismeri fel. A β = 0,5 (10. pont 10.); a horgony nélküli változat a
     G3-kemény (6. pont).

---

## 5. Családcsoportok, splitek, kitartás

**A kitartás egysége a családcsoport.** Egy csoport minden forrása együtt marad ki, így a rokon forrás sem
szivárogtat.

| csoport | családok és források | szerep |
|---|---|---|
| **termék** | 00 számla → cikk, ESCI, GLAMI-EM, KN/VTSZ árucsoport | **kitartva (HO-termék)** |
| **routing** | 01 eszközválasztás, MASSIVE (scenario, intent, slot), CLINC, BANKING77, xLAM, When2Call, a tasksource intent-forrásai | **kitartva (HO-routing)** |
| **KIE/validáció** | KIE-mezőellenőrzés, `numeric.consistency`, `date.reasoning` | **kitartva (HO-új-család)**; konstrukciós gold, emberi átnézés nélkül, egységteszttel |
| NLI | HuRTE, HuCB, HuWNLI, a tasksource NLI-forrásai | train |
| szentiment, nyelvhelyesség | HuSST, HuCOLA | train |
| QA, megválaszolhatatlan | MILQA, HuRC, HuBoolQ, HuCoPA | train |
| jogi, közigazgatási | MultiEURLEX, NJT, hivatali ügytípus | train (+ HO-forrás jelölt) |
| közbeszerzés | TED CPV | train; egy CPV-főcsoport HO-forrás |
| levél, dokumentum | triage, dokumentumtípus, szerződésklauzula | train |
| RAG, bírálat | relevancia, alátámasztás, válaszbírálat | train |
| entitás | NerKor, entitásegyezés | train |
| konstrukciós | a 3.4 többi családja | train (≤ 15%) |

**Rétegek:**

- **train / val:** a val a train-családokból, nehéz összetétellel a plafon ellen (00-lelet).
- **teszt-ID:** családonként kis, eloszláson belüli teszt.
- **HO-termék:** a 00 befagyasztott, publikus tesztjei:
  - `test`, négy réteg: 3534 item, 3020 pontozott;
  - `test_new_suppliers`: 2107 item, 1673 pontozott.
- **HO-routing:** a 01 befagyasztott tesztjei (T-hu-részhalmaz, T-katalógus, T-BFCL-live, T-új-eszköz, T-BFCL), a
  vak szúrópróba és a fagyasztás után. A T-hu-részhalmaz a T-hu átnézett része; a T-hu-maradék (a MASSIVE-teszt át
  nem nézett része) a 01-ben is leíró volt, itt is az (7.3).
- **HO-új-család:** a KIE/validáció csoport, egyedül (Dani, 2026-10-09). A levéltriage nem lesz második
  HO-új-család, mert emberi átnézést igényelne; a train-ben marad. 2400 item (családonként 800), ebből 200 a H3
  kalibrációs mintája (`meta.kalibracio`).
- **HO-forrás:** egy TED CPV-főcsoport. A gold a forrásból jön, gépi zajbecsléssel; emberi audit nélkül leíró
  réteg (4.6).
- **Külső eval:** Belebele hun, SIB-200 hun, a HuLU val-ok, `LocalLLaMA/typed-decisions` test,
  `fastino/fast-decisions`.
- **Decision Index 0.2.1** (kit: `apolinario/decision-index`, MIT):
  - a választott sávok (CLINC150+OOS, When2Call MCQ, BANKING77, Amazon ESCI) a kittel újraépítve, csak eval;
  - a JEV-modellek itemenkénti valószínűségei (`autotrust/jev-decision-index-results`, Apache-2.0) referencia-karként
    ugyanazokon az itemeken;
  - a JEV-27B és a JEV-9B ezeket a benchmarkokat nem látta, a JEV-Gemma4 a train-splitjeiken tanult, ezért ott nem
    kitartott;
  - a sávok a routing- és a termék-csoporthoz tartoznak, ezért a G3 számára kitartottak, és a 01 F5b eszközeivel
    mérhetők.

**Szabályok:**

- **Csoportosítás:** a permutációk, az ellentényes párok, egy forrás-item változatai és egy állapot összes kérdése
  közös splitbe kerül (`group_id`).
- **Szivárgás-audit:** bge-m3 és MinHash a splitek között és minden eval-készlet ellen, a 00/01 tesztjeit is
  beleértve. MASSIVE-mondat se fordítva, se parafrazálva ne kerüljön be; FLORES-szöveg sehol nincs a trainben.
- **Kitartás-audit:**
  - forrásnév-lista arról, mi tartozik a termék- és a routing-csoportba (a tasksource forrásaira is);
  - a train minden forrása dokumentáltan kívül esik rajtuk.
- **Shortcut-audit:**
  - családonként egy csak kérdést és opciókat látó baseline, állapot nélkül;
  - X-arány, pozíció és listahossz rétegezve (00).
- **Befagyasztás** mérés előtt, hash-sel.

---

## 6. A létra

| kar | leírás |
|---|---|
| L0 / L1★ | a bázismodell kalibrált kiolvasása (00/01 karok), minden rétegen |
| L3-spec | a meglévő specifikus LoRA a saját HO-tesztjén: a 00 publikált adaptere a HO-terméken, a 01 L3 a HO-routingon. Referenciaplafon, új tanítás nélkül |
| **G3** | általános LoRA a három kitartott csoport nélkül; gold-cél ε = 0,05-tel (tanár nem ment át, 10. pont 14.) + bázis-horgony (4.7) az X-gold itemeken, 30% permutáció; magyar + 25% angol gerinc, a HuSST és a HuCB nélkül (10. pont 15.), az MVP v2-n (17.); 3 seed |
| G3-kemény | a G3 β = 0-val (horgony nélkül), minden más azonos, a 0,5 · Brier-taggal együtt; egyben a horgony-abláció a β-döntéshez. A 01 L3 receptjétől csak a Brier-tagban tér el (H6); 1 seed |
| G3-hu | G3 angol gerinc nélkül (H4), 1 seed |
| G3+spec *(stretch)* | a G3 adata + a specifikus család train-je: árt vagy segít-e az általános adat a specifikus feladaton |
| JPT-ref *(leíró)* | a külső `kirp/jpt-35b-a3b` (angol, JEV-típusú döntési LoRA a Qwen3.5-35B-A3B-n; Források) a magyar kitartott rétegeken, a saját `llm2jev`-promptjával és a sajátunkkal is. Azt méri, mennyit visz át magyarra egy angol döntési finomhangolás (H4 mellé). Csak eval, a kimenete sehová nem kerül a tanítóadatba (10. pont 13.) |

---

## 7. Hipotézisek és elemzési terv — v1 (rögzítve 2026-10-14)

Dani 2026-10-14-én jóváhagyta a v1-et, pontosításokkal (10. pont 18.; Napló). Ez a szakasz az érvényes, jóváhagyott
leírás. A rögzített példány: `kor03/rogzites/v1/` (7.10).

### 7.1. Tárgy és vakság

- **Tárgy:** a meglévő MVP v2 (17 500 item, sha256 `65bd0bd7…`), a betanított adapterek, a kitartott rétegek, a
  célréteg-kalibrációs minták és az elsődleges promptkeretek. Új tanítás, új tanárkeresés és új emberi címkézés nincs.
- **A recept, ahogy ténylegesen fut:** puha tanárcél nincs, mert egyik tanár sem ment át (10. pont 14.). A cél a gold
  ε = 0,05-tel; a veszteség CE + 0,5 · Brier + β · KL(p_L1★ ‖ p_modell) az X-gold itemeken.
  - G3: β = 0,5, az MVP v2-n, seed 1–3;
  - G3-kemény: ugyanez β = 0-val, seed 1;
  - G3-hu: a G3 az angol gerinc nélkül, seed 1.
- **Vakság:** a 03-as G3-karok F4-teljesítményét és az összehasonlító eredményeket a döntési szabályok véglegesítéséig
  nem tekintettük meg. Ami ismert volt:
  - az L1★ HO-rétegenkénti eredményei (F2-elemzés);
  - a 00/01 korábbi eredményei, köztük az L3-spec karoké a saját tesztjükön;
  - a G3-karok val-eredményei (F3).

  A technikai hibanaplók és a teljességi adatok (sorszám, (id, perm)-kulcsok, érvényesség, hash) ellenőrzése ettől
  elkülönül (7.9).

### 7.2. Karok és kalibráció

- **L1★:** a bázis kalibrált kiolvasása az F2-ből (perm-átlag, T = 1,431, val-τ@95 = 0,716).
- **L0′:** ugyanez egy új vLLM-példányon, a sor végén, az L1★ kalibrációjával és τ-jával. A példányzajt méri (a 00 F4
  mintájára).
- **G3 s1–s3, G3-kemény s1, G3-hu s1:** a val-kiolvasás az F3-ból, az eval-kiolvasás az F4-ből. Mindegyik kar a 03
  val-on választott kalibrációs karral fut, a saját temperature-jével és val-τ@95-jével.
  - A kalibrációs kar: nyers, temperature, perm-átlag vagy batch, a val lef@95 szerint; holtversenyben a lef@90, majd
    a kisebb ECE dönt (az L1★ szabálya).
  - A választás az F3-é: perm-átlag, kivéve a G3 s2-t (nyers).
- **L3-spec (H2):** a 00 adapterei (`l3mixse_h2_s1..s3`) a HO-terméken, a 01 L3 (`k01_l3mixse_p30_s1..s3`) a
  HO-routingon. Mindkettő a saját köre F4-es kalibrációjával fut: `temp` kar, a temperature és a τ@95 a saját kör
  F4-es val-kiolvasásán (00 val: 1006 item, 01 val: 3524 item). Ez a specifikus LoRA a saját, élesben is használt
  beállításával.
- **Leíró:** a JPT-ref (később); a v1-es pilot karok csak a val-on.

### 7.3. Rétegek

| réteg | item | pontozott | klaszter | szerep |
|---|---|---|---|---|
| HO-termék (a 00 tesztje, 5 alréteg) | 5441 | 4524 | 2759 | H1, H2, H3, H4, H6 |
| HO-routing (a 01 megerősítő tesztje) | 7493 | 7416 | 4169 | H1, H2, H3, H6 |
| — ebből magyar (a T-hu átnézett része, T-katalógus) | 1204 | 1127 | 1204 | H4 |
| HO-új (KIE/validáció) | 2200 | 2200 | 2200 | H1, H3, H4 |
| T-hu-maradék (a 01 tesztjének át nem nézett MASSIVE-része) | 2320 | 2222 | 2320 | leíró |
| teszt-ID | 22741 | 22741 | 17548 | H5 (leíró) |
| HO-forrás (TED CPV 38) | 166 | 166 | 166 | leíró |
| külső eval | 5004 | 4601 | 3092 | leíró (JEV-referencia) |

- A rétegekből kimarad a célréteg-kalibrációs minta (`adat/f4/kalib.json`).
- **A HO-routing** az 5. pont definíciója szerint a 01 megerősítő tesztje: T-BFCL, T-BFCL-live, When2Call, a T-hu
  átnézett része (593 item) és a T-katalógus. A T-hu-maradék a 01-ben is leíró volt (~10% becsült címkezaj), és a 4.6
  szerint megerősítő állítás csak emberileg átnézett tesztrétegen áll.
  - **Javítás a tervezethez képest** (2026-10-14, az eredmények megtekintése előtt): a v1-tervezet a 01 teljes tesztjét
    vette (9813 item), a T-hu-maradékkal együtt, ami eltért az 5. pont definíciójától. A tervezet rétege érzékenységi
    elemzésként szerepel.
  - A `kalib.json` változatlan. A HO-routing mintájából a megerősítő részbe eső 146 item (82 klaszter) kalibrál; a
    T-hu-maradékba eső 54 item egyik tesztben sem szerepel.
- **A H3(b) kalibrációs mintái:**
  - HO-termék: 200 item, 105 klaszter, 169 pontozott;
  - HO-routing: 146 item, 82 klaszter, 145 pontozott;
  - HO-új: 200 item.
- **Keret:** a HO-terméken és a HO-routingon az eredeti 00/01 prompt (natív) az elsődleges, a többi rétegen a 03
  általános kerete. A másodlagos, generikus keretet a HO-rétegeken az F4 nem olvasta ki, ebben a körben nincs.

### 7.4. Mérőszámok és statisztika

- **Mérőszámok** (a 00 `elemzes.py` definíciói):
  - **lef@95** = a pontozott itemek hányada, ahol a top-1 nem X és a bizalom ≥ τ;
  - **elfogadott item** = ezek száma;
  - **precizitás** = az elfogadott itemek közül a helyesek aránya;
  - **X-fedés** = az X-gold itemek hányada, ahol a top-1 X (τ-tól független);
  - AURC és ECE.
- **Bootstrap:** hierarchikus, 10 000 ismétlés: seed (visszatevéssel) × klaszter (`group_id`; a 00 val-on cikk, a 01
  val-on klaszter).
  - Az összehasonlított karok egy replikán belül közös klasztermintát kapnak (teszt, val, kalibrációs minta).
  - A τ minden replikában, minden karnál újraválasztódik a klaszteresen újramintázott val-on. A H3(b)-ben a célréteg
    kalibrációs mintája is klaszteresen újramintázódik.
  - Az intervallumok a val-on már kiválasztott kiolvasási módra és temperature-re feltételesek. A teljes modell- és
    kalibrációválasztás bizonytalanságát nem fedik le.
  - Kétoldali p = 2 · min(P(Δ ≤ 0), P(Δ ≥ 0)); Holm-korrekció, α = 0,05.
- **Példányzaj:** L0′ vs. L1★ rétegenként (top-1-billenés, lef@95-különbség rögzített τ-val).
  - Ha egy rétegen |Δlef@95| > 1 pont, a H1 ott az L0′-höz mérve is eldől (a G3 − L0′ hat próbája külön
    Holm-családban), és a gyengébb ítélet számít.
  - Az L0′ a bázis példányzaját méri; az adapteres kiolvasások példány-stabilitását önmagában nem igazolja (7.9).

### 7.5. H1 — általánosít kitartott családra

G3 vs. L1★ a HO-terméken, a HO-routingon és a HO-új-családon.

- **Végpontok:** Δlef@95 és ΔAURC, mindkettő elsődleges. Közös Holm-korrekció a hat próbára (3 réteg × 2 végpont),
  α = 0,05.
- **Rétegítélet, ebben a sorrendben:**
  1. **„Nem teljesíti a követelményeket”**, ha a G3 három seedre átlagolt precizitása (val-τ) < 0,93, vagy bármelyik
     végpont Holm után szignifikánsan a G3 ellen szól.
  2. **„Általánosít az adott rétegen”**, ha az 1. nem áll fenn, és legalább egy végpont Holm után szignifikánsan
     javul. A sikert megalapozó végponton mindhárom seed pontbecslése a kedvező oldalon van, vagy nulla.
  3. Minden más eset **„nem eldönthető”**.

  Ha egy seed a rétegen egyetlen itemet sem fogad el, annak a precizitása nem értelmezhető. Ekkor az 1. pont
  precizitás-átlaga a többi seedé, és a réteg nem lehet „általánosít”: legfeljebb „nem eldönthető”, vagy az 1. szerint
  „nem teljesíti”.
- **Jelentés:** a precizitás és a két végpont seedenként is. Az összefoglaló megnevezi, mely HO-rétegeken teljesült a
  feltétel; egyetlen sikeres réteg alapján nem állítható minden feladatcsaládra általánosítás.
- Az L0′-szabály (7.4) megmarad.
- **Leíró:** X-fedés X-típusonként.

### 7.6. H2 — a specifikus LoRA-hoz mérve

A HO-terméken és a HO-routingon, rétegenként, párosított bootstrap-kontraszttal; a G3 és az L3-spec seedjei
hierarchikusan.

- **Feltétel:** a H2 egy rétegen csak akkor értelmezhető, ha az L3-spec − L1★ lefedettségkülönbség 95%-os CI-jének
  alsó határa pozitív. Különben az ítélet „nem értelmezhető”.
- **Kontraszt:** D = [lef(G3) − lef(L1★)] − 0,5 × [lef(L3-spec) − lef(L1★)].
  - Ha D alsó CI-határa > 0: **„érdemi átvitel”**;
  - ha D felső CI-határa < 0: **„nem éri el az előírt 50%-os átvitelt”**;
  - egyébként **„nem eldönthető”**.
- **Nyereségarány** (saját mérőszám, leíró):
  (lef@95(G3) − lef@95(L1★)) / (lef@95(L3-spec) − lef@95(L1★)). Ha 1, a G3 a specifikus LoRA teljes nyereségét hozza;
  ha 0, semmit.
- A H2 intervallumai rétegenkénti 95%-os intervallumok. Vizsgálatszintű, többszörösségre korrigált állítás nem
  következik belőlük.

### 7.7. H3 — a kalibráció átvihető

Két út, mindhárom HO-rétegen, a G3-ra (az L1★-ra leíróan):

- **(a) val-τ:** a G3 a val-on választott τ-jával.
- **(b) célréteg-τ:** a τ a réteg kalibrációs mintáján (7.3), ugyanazzal a szabállyal, mint a val-on; a precizitás és
  a lefedettség a maradék teszten. Ez az éles helyzetet modellezi: egy új feladatnál ennyi címke még beszerezhető.
- **Ítélet:** ha a G3 három seedre átlagolt precizitásának pontbecslése ≥ 0,93, az eredmény **„az előírt
  toleranciaküszöböt teljesítette”**. Ez nem azonos a 95%-os precizitás igazolásával.
  - Ha bármelyik seed egyetlen itemet sem fogad el, a precizitás nem értelmezhető, és az eredmény nem siker.
  - Ha a kalibrációs mintán nincs megfelelő τ (a CP-alsó korlát egyetlen küszöbnél sem éri el a 0,95-öt), akkor
    τ = +∞, és nincs elfogadott item: az eredmény nem siker. Ennek gyakoriságát a bootstrap-replikákban is jelentjük.
- **Jelentés mindkét útnál:** a precizitás CI-je (a seedek hierarchikusan és seedenként), a lefedettség és az
  elfogadott itemek száma. A nulla elfogadott itemű replikák precizitása nem értelmezett, ezek arányát jelentjük.
- **Leíró:** a lefedettségveszteség az oracle-τ-hoz képest (a saját tesztjén illesztve, csak felső korlát).

### 7.8. H4, H5, H6

- **H4 — angol gerinc.** G3 s1 vs. G3-hu s1, párosítva, a HO-terméken, a HO-új-családon és a HO-routing magyar részén
  (7.3).
  - A végpontok és az ítélet a H1-éi, az egyetlen seedre alkalmazva (a precizitás-feltétel a G3 s1-é). Külön
    Holm-család (6 próba); a siker neve „segít”.
  - A H4 az angol adatokkal kibővített tanítás hatását méri ennél a seednél. A nyelv hatása nem választható el a
    nagyobb adatmennyiségtől és a több tanítási lépéstől (a G3-hu 25%-kal kevesebb itemen tanult).
- **H5 — eloszláson belül (leíró).** G3 vs. L1★ a teszt-ID-n, családonként.
- **H6 — a bázis-horgony (feltáró, a mechanizmust vizsgálja).** A HO-routingon és a HO-terméken:
  - (a) **a G3 X-fedésének megőrzése:** a Δ X-fedés (G3 − L1★, a seedek hierarchikusan) CI-jének alsó határa > −2 pont.
    Ugyanez a G3-keménynél (1 seed) leíróan. Ha a feltétel a G3-nál igazolható, a G3-keménynél nem, az önmagában nem
    bizonyít horgonyhatást;
  - (b) **a horgony hatása:** a G3 s1 − G3-kemény s1 közvetlen, párosított X-fedés- és AURC-különbsége, CI-vel;
  - (c) **leíró:** az átnézésben átcímkézett routing-itemeken (51: a T-hu 40, a MASSIVE további 4 és a T-katalógus 7
    iteme) karonként hányszor adja a kar a régi forráscímkét, és ebből hányszor a τ fölött. A routing-csoport kimaradt
    a G3 tanításából, ezért ez nem közvetlen bizonyíték arra, hogy a tanítás kivédi a címkekonvenció beégését.

### 7.9. Az F4 technikai lezárása

Az elemzés előtt (`kor03/eszkozok/f4_teljesseg03.py`):

- **Pontos (item_id, perm)-egyezés minden szükséges karon:** hiány, ismétlődés és érvénytelen sor nélkül; a puszta
  sorszám nem elég. A szükséges karok:
  - az F4 tizenkét kiolvasása;
  - az L1★ F2-es val- és eval-kiolvasása;
  - a G3-karok F3-as val-kiolvasásai;
  - az L3-spec karok saját val-kiolvasásai.
- **Érvénytelen a sor**, ha
  - az opció-sorrend vagy a címkék nem az itemből és a permutációból számoltak;
  - a valószínűségek nem pontosan a jelen lévő címkékre szólnak, vagy nem végesek;
  - címke hiányzik, vagy a címketömeg nem véges pozitív szám;
  - a modell neve nem a karé (a 00/01 val-kiolvasásokon is).

  A kikerült itemek többletsorai (az F2-ben 44 / 85 item) nem hibák: az elemzés id szerint illeszt.
- **Pecsét:** a lepecsételt fájlok `PECSET.sha256`-beli utolsó hash-e a végleges fájlé, a korábbi hash-ek a fájl
  egy-egy sor-előtagjáé. Ez igazolja, hogy a pótlás csak hozzáfűzött, az eredeti sorokhoz nem nyúlt.
  - Az élő `PECSET.sha256` a rögzítéskori pillanatképével kezdődik (`kor03/rogzites/v1/PECSET-pillanatkep.sha256`),
    tehát korábbi sora nem veszhetett el.
  - Lepecsételt karonként a pótolt (id, perm) párok pontosan a hibanapló párjai. Ha a hibanapló nem üres, pótlás-pecsét
    kötelező. Ha a G3-karokon volt pótlás, de a pótolt párok listája üres, az elemzés nem fut.
- **Manifest:**
  - a végleges fájlok hash-e: `eredmenyek/F4/V1-MANIFEST-kiolvasasok.sha256`;
  - a pótlás futásazonosítója és a pótolt (id, perm) párok: `teljesseg.json`, `potolt_parok.jsonl`.
- **A pótolt G3-sorok** (G3 s1: 5545, s3: 2206; a HO-routing 1387, illetve 553 iteme) más vLLM-példányról jönnek,
  mint a kar többi sora. Az L0′ a bázis példányzaját méri, az adapteres kiolvasások stabilitását önmagában nem
  igazolja. Ezért a H1-et a HO-routingon a pótlással érintett és nem érintett itemekre külön is jelentjük
  (érzékenységi bontás).

### 7.10. Rögzítés, jelentés, továbblépés

- **Rögzítés:** `kor03/rogzites/v1/`, benne a runbook pillanatképe (`03-runbook-v1.md`) és a `MANIFEST.sha256`. A
  manifest sha256-ot tartalmaz ezekre:
  - az elemzőkód: `f4_elemzes03.py`, `f4_teljesseg03.py`, a láncszkript és az importált modulok;
  - az item-fájlok és a kalibrációs minták (`kalib.json`);
  - az MVP v2;
  - a val-kiolvasások.

  - a `PECSET.sha256` rögzítéskori pillanatképe.

  A láncszkript a manifest saját hash-ét tartalmazza, ezért ő maga nincs a manifestben; a hash-e a naplóban áll. A
  Sparkon az elemzés előtt a lánc ellenőrzi a manifest hash-ét, majd `sha256sum --strict -c`-vel a tartalmát.
- **Futtatás:** `kor03/eszkozok/f4_elemzes_lanc.sh` (várakozó lánc). A pótlás után ebben a sorrendben fut:
  1. a manifest ellenőrzése;
  2. a technikai lezárás;
  3. az elemzés (`f4_elemzes03.py`, 10 000 ismétlés).

  Dani jóváhagyása szerint ehhez újabb jóváhagyási kör nem kell.
- **Eredménylap:** minden előre rögzített hipotézis eredménye rákerül, a negatív és a nem eldönthető is. A gépi
  táblák az `eredmenyek/F4/eredmenylap_gepi.md`-be kerülnek, mellé kézzel írt értelmezés. Ami a v1-en kívül esik, az
  leíró, és így jelölve.
  - Ilyen érzékenységi blokk: a tervezet HO-routing-rétege; a pótlással érintett és nem érintett itemek.
- **Továbblépés:** az F4 alapján végzett receptmódosítás külön kísérleti kör.

### 7.11. MDE — előzetes érzékenységi becslés

A számítás: `kor03/eszkozok/mde03.py`, a 00 módszerével, a val-ról vetítve. A τ-választás és a mintavétel szórása
külön, 1000 ismétlés; 80% erő, kétoldali α = 0,05; a v1 rétegeinek pontozott tesztméretére. Kimenet:
`eredmenyek/F4/mde03.json`.

| pár | végpont | HO-termék | HO-routing | HO-routing, magyar rész | HO-új | Δ a val-on |
|---|---|---|---|---|---|---|
| H1: G3 s1 − L1★ | lef@95 | 6,6 pont | 6,5 pont | – | 6,8 pont | +15,0 pont |
| | AURC | 0,0040 | 0,0031 | – | 0,0058 | −0,0127 |
| H4: G3 s1 − G3-hu s1 | lef@95 | 4,1 pont | – | 4,7 pont | 4,3 pont | +6,0 pont |
| | AURC | 0,0026 | – | 0,0052 | 0,0037 | −0,0041 |
| H6: G3 s1 − G3-kemény s1 | lef@95 | 2,8 pont | 2,7 pont | – | – | −1,3 pont |
| | AURC | 0,0019 | 0,0015 | – | – | −0,0003 |

- Ez előzetes érzékenységi becslés. Nincs benne a Holm-korrekció és a seed-komponens, ezért nem igazolja a teljes
  döntési szabály 80%-os erejét.
- A lef@95 szórásának 85–89%-a a τ-választásból jön (a 00-lelet itt is): a teszt méretével alig csökken.
- A H1 mindkét végponton bőven erős, ha a val-különbség átvisz.
- A H4 a lef@95-ön a határon; a HO-routing magyar részén (1127 pontozott item) az AURC-n alulerős (MDE 0,0052, a
  val-Δ −0,0041).
- A H6(b) alulerős: a val-Δ AURC (−0,0003) az MDE 11–20%-a, „nem eldönthető” eredmény várható.
- A tervezethez képest csak a HO-routing oszlop változott (a T-hu-maradék nélkül 7416 pontozott item a 9638 helyett:
  H1 lef@95 6,4 → 6,5 pont, AURC 0,0027 → 0,0031); a többi oszlop ugyanazzal a seeddel bitre azonos.


---

## 8. Fázisok és kapacitás

| fázis | tartalom | idő |
|---|---|---|
| F0 | **GPU nélkül, most is mehet.** Forrásletöltés és licencrögzítés soronként (`source_license`); forrásadapterek a közös sémára; családspecifikációk; `kozos03.render` + egységteszt a 00/01 promptjaival; PII-szűrő a TED-re; kitartás-lista | ~3–4 nap |
| F1 | itemgyártás; szinonimaszűrés; gépi zajbecslés; a KIE-konstrukció egységtesztje; szivárgás-, kitartás- és shortcut-audit; befagyasztás; MDE | ~1 hét |
| F2 | L0/L1★ minden rétegen; Gemma 4 smoke a Sparkon (kész, 2026-10-09); tanárkapu négy jelöltre (egyik sem ment át, 10. pont 14.); a bázis-horgony eloszlásai | ~2–3 éjszaka |
| F3 | G3-pilot 15–20 ezer itemen és a G3-kemény (egyben a horgony-abláció), 1 seeddel; családonkénti tanulási görbe (25/50/100%) 1 seeddel; utána seed 2 és 3, valamint G3-hu | ~5–7 éjszaka |
| F4 | végső mérés: HO-rétegek, L3-spec-referencia, JPT-ref (leíró; 66 GB letöltés, ~2–3 óra) | ~1–2 éjszaka |
| F6 | adatkészlet-kártya (licencenként külön konfiguráció), adapter `llm2jev`-illeszkedéssel (9. pont), tanulmány | ~2 nap |

- **Tréningidő:** ~1,9 ezer item/óra (00 F3 pilot, rövid promptok). A 15–20 ezres MVP így ~8–11 óra/epoch.
  - A 2–8K tokenes állapotok ezt többszörösére növelik, ezért az MVP-ben legfeljebb 10% a hosszú item.
  - A 01 F3 a 14,5 ezres train-nel pontosítja a becslést.
  - Az ötletanyag 40–60 ezres MVP-je karonként ~1–1,5 nap/epoch lenne, a 100–200 ezres teljes keverék pedig napokig
    tartana. Előbb a tanulási görbe mutassa meg, hol kell több adat.
- **Átnézési teher (Dani): nincs** (2026-10-09). Helyette a gépi zajbecslés Spark-időt kér: ~10 forrás × 300
  item × 3 kiolvasás, a tanárkapu-futásokba csomagolva.
- **Egyszerre egy nagy folyamat** a Sparkon (00 szabály): generátor, alany, bíráló vagy tréning.

---

## 9. Licenc és publikálás (vázlat)

- **Adatkészlet licencenként külön konfigurációban:**
  - (a) CC-BY-4.0, Apache-2.0, MIT, CC0, BSD rész;
  - (b) CC-BY-SA rész, ShareAlike-kal;
  - (c) a nem továbbadható vagy gated forrásokból csak a szkript publikus.
- **A ShareAlike nem terjed ki az adapter súlyaira** (Dani, 2026-10-09). A CC-BY-SA forrásokból készült
  adatkészlet-konfiguráció (b) ShareAlike marad; az adapter licence a 00/01 gyakorlata szerint Apache-2.0. Ez nem
  jogi tanács, hanem a szokásos gyakorlat követése.
- **Generátor és fordító:** csak Apache-2.0 (Mistral Small 4, Gemma 4, Muse-Glimmer-30B). A Qwen-család az
  alany családja, ezért nem generál (10. pont 11.). A Qwen3.8-Flash-Next (Qwen Community License 1.0) a licence
  miatt sem.
- **Tanár és bíráló:**
  - tanár csak Apache-2.0 vagy MIT licencű modell: a jelöltek a Mistral Small 4, a Gemma 4 26B-A4B-it (a
    HF-kártya szerint Apache-2.0, ellenőrizve 2026-10-09) és a Qwen3.6 (4.4);
  - a Llama csak szűr;
  - zárt modell semmilyen szerepben nincs a tanítóadat láncában.
- **TED:** forrásmegjelölés és PII-szűrés. A hirdetményekben lévő harmadik féltől származó tartalom külön kezelendő.
- **Tenantadat:** soha. A DocAI-arany csak belső eval, csak aggregátum hagyja el a laptopot.
- **Benchmarkok:** a Belebele, a SIB-200, a `LocalLLaMA/typed-decisions` test, a fastino és a BFCL csak eval; soraik
  nem kerülnek a publikus készletbe.
- **A HO-tesztek:** a 00-é már publikus; a 01-é a 01 publikálási szabálya szerint lesz az.
- **`llm2jev`-illeszkedés** (Dani, 2026-10-10; 10. pont 12.): a publikált adapter a JEV típusos döntési
  interfészén (`choice`, `noul`; a `score` nálunk nincs) is kiszolgálható legyen az `llm2jev`-vel (pypi). Ehhez a
  promptkeretet és a címkekiolvasást az `llm2jev` útjához kell igazítani, vagy egy illesztőt adni hozzá. A döntés
  az F6-ban születik, de a promptkeret v1-es rögzítésekor (10. pont, nyitott kérdések) már számítani kell rá.

---

## 10. Döntések

1. **Llama: a szűrés nem tanítás** (Dani, 2026-10-07). A 00 és a 01 eljárása változatlan. A 03-ban a Llama szűrhet,
   de címkét és soft targetet nem ad (4.5).
2. **A 01-tanulságok beépülnek** (Dani, 2026-10-09):
   - puha keverék-cél Apache-2.0 tanártól (4.1, 4.4); a 03-ban egyik tanár sem ment át (14.);
   - valódi irrelevancia a trainben, négy X-típussal (2. pont);
   - bázis-horgony az X-viselkedésre (4.7);
   - célréteg-kalibrációs minta a H3 második útjaként (7. pont).
3. **Tanárjelöltek:** Mistral Small 4 és Gemma 4 26B-A4B-it, mindkettő Apache-2.0 (Dani, 2026-10-09). Mellettük a
   Qwen3.6 gondolkodó módja; a tanárkapu dönt (4.4).

4. **Családválasztás a bázis gyengesége szerint** (Dani, 2026-10-09, a 00/01 tanulsága). Az F2-ben az L1★
   minden train-családon mér. Ahol a bázis a plafon közelében van (javaslat: lef@95 ≥ a plafon 90%-a, és a
   precizitás nem bukik), az a család legfeljebb a train 5%-át adja: ott a tanítás inkább árt, mint segít. A
   kitartott HO-rétegekre ez nem vonatkozik, azok mérésre valók.
5. **Angol gerinc: igen, a train 25%-a** (Dani, 2026-10-09; 3.3). A G3-hu kar méri a hatását (H4).
6. **HO-új-család: csak a KIE/validáció** (Dani, 2026-10-09). A levéltriage train-család marad (5.).
7. **Nincs emberi átnézés a 03-ban** (Dani, 2026-10-09: „nem szeretnék átnézni semmit se”). A zajaudit gépi
   becslés lett (4.2), a tanár–gold ellentmondás kimarad a tanításból (4.1), a megerősítő állítások az emberileg
   átnézett 00/01 HO-rétegekre és a konstrukciós HO-új-családra szűkülnek (4.6).
8. **Nemzeti Jogszabálytár: használható** (Dani, 2026-10-09). A jogszabályszöveg nem védett (Szjt. 1. § (4)); a
   letöltés kíméletes ütemben, rögzített jogszabálylistára megy (3.2).
9. **A ShareAlike nem terjed ki az adapter súlyaira** (Dani, 2026-10-09; 9. pont).
10. **A javasolt értékek elfogadva** (Dani, 2026-10-09): α = 0,5 (gold–tanár keverés, 4.1), β = 0,5 (bázis-horgony,
    4.7), az MVP 15–20 ezer train-item, a gépi zajbecslés küszöbe 10% (4.2). Az F1 indul.
11. **A Qwen-család nem generál és nem ellenőriz szintetikus itemet** (Dani, 2026-10-10: „mivel a qwen modelt
    tanítjuk utó, van értelme qwen modellel generálni adatot? Nem lenne jobb egy idegen model?”).
    - **Indok:** a bázis a saját szövegén eleve jó, így az ilyen itemekből kevés a tanulnivaló. A Qwen-ellenőrző
      ráadásul épp a bázisnak könnyű itemeket tartaná meg, és kiszűrné azokat, amelyeken a bázis hibázik.
    - **A Qwen3.8-27B nem:** licence rendben van (Apache-2.0), de a tokenizere és az előtanítási vonala közös a
      Qwen3.6-éval, így a probléma csak enyhülne.
    - **A három korábbi Qwen-család generátora a Muse-Glimmer-30B** (Dani választása): Meta, Apache-2.0, dense ~30B,
      a modellkártya szerint a szintetikus tanítóadat-gyártás rendeltetésszerű használat. A felhasználási szabályzat
      szerint a kimenet nem tüntethető fel ember által írtnak: az adatkártyán szintetikusként szerepel. A Muse egy
      zárt Meta-modellből desztillált; a licence dönt, mint a Gemmánál.
    - **Ellenőrzők (végleges, Dani, 2026-10-10 délután):** mind a hét szintetikus családot a Gemma ellenőrzi. A
      Gemma-családokat eredetileg a Mistral ellenőrizte, de X-en szinte soha nem választ X-et, és a Muse meg a
      Llama is elbukott az ellenőrző-validáláson (Napló). Ezért a levéltriage-et, az entitásegyezést és a hivatali
      ügytípust a Muse generálja újra, így a generátor: Muse 6 család, Mistral 1 (RAG-relevancia). A tanárkapu nem
      mér szintetikus golddal (4.4: forrás- és konstrukciós gold), így a Gemma ellenőrzői szerepe nem teszi
      körkörössé a kaput.
12. **`llm2jev`-illeszkedés a publikált adapternél** (Dani, 2026-10-10; 9. pont).
13. **JPT-35B-A3B leíró referenciakarként** a magyar kitartott rétegeken, ha odaérünk (Dani, 2026-10-10; 6. pont,
    JPT-ref). Tanár, generátor vagy bíráló nem lehet: a licence CC-BY-NC-4.0, és a tanítóadatában zárt modell írta
    dokumentumok vannak.
14. **A tanítási cél, ha nincs kapun átment tanár** (Dani, 2026-10-11, a tanárkapu után; Napló): a gold, ε = 0,05
    label smoothinggal, és a bázis-horgony (4.7) az X-gold itemeken; puha tanárcél nincs (α = 0).
    - A G3-kemény a G3 β = 0-val, a 0,5 · Brier-taggal együtt, minden más azonos. Így a H6 a horgony hatását méri, a
      horgony nélküli pilot-abláció pedig egybeesik a G3-keménnyel (egy tanítással kevesebb). A 01 L3 receptjétől a
      G3-kemény csak a Brier-tagban tér el.
    - **Végleges** (07:54): a negyedik jelölt, a Qwen3.8-27B-FP8 is elbukott (Napló). Ebben a körben több jelölt
      nincs; a létra (6.), a H6 és a fázisterv (8.) ennek megfelelően átírva.
15. **A HuSST és a HuCommitmentBank kimarad a train-ből** (Dani, 2026-10-11; a 4.2 szabálya szerint, zajjelölt 13,3%
    és 24,7%).
    - A többi kilenc forrás bent marad, a 300-as mintában talált zajjelöltek nélkül. A forrás többi itemjére nincs két
      független olvasó (egyik tanár sem ment át), ezért ott nincs szűrés; a maradék zaj a becslés szerint < 10%.
    - **Tanulság a 04-re:** a HuCB-jelöltek 48/53-a X-gold, amelyet az olvasók nem ismernek fel (a val NLI-csoportjában
      a természetes X-fedésük 0). A zajszabály válassza külön az X-gold elleni egyetértést, ha az olvasók X-fedése
      azon a típuson 0,5 alatt van; ez itt X-vakság, nem címkezaj.
16. **A Qwen gondolkodó módja a 03-ban nem fut tovább** (Dani, 2026-10-11: „qwen nagyon sokat gondolkodik, és mint
    láttuk sokat nem ad hozzá a gondolkodás, ezért kapcsold ki a gondolkodást”).
    - **Indok:** a 600 itemes kapumintán a gondolkodó mód top-1-e 0,828, az L1★-é ugyanott 0,818, mintánként ~900
      token gondolkodással (~430 token/s a Sparkon). A 01-ben az L3→S2 sem segített, mert a hibák a τ fölött voltak.
    - **Következmény:** a G3→S2 kar kimarad a létrából (6.) és az F4-ből (8.); puha cél nélkül (14.) a kérdése is
      gyengébb lett. Minden további Qwen-kiolvasás (a Qwen3.8 tanárjelölt, az L0/L1★, a G3-karok) nem gondolkodó:
      `enable_thinking = false` a chat-sablonban (üres `<think>` blokk), egyetlen címketoken logprobja.
17. **MVP v2: a gold-drop családok X-aránya marad, a típussapka 60%** (Dani, 2026-10-12, a pilot val-eredménye után).
    - **Ok:** az MVP v1-ben az 50%-os típussapka 642 gold-drop X-et ugyanannak a családnak nem-X itemjére cserélt (a
      nem gold-drop X kevés: a természetes X zöme a plafon közeli MILQA-ban van, a HuCB kiesett). A gold-drop
      családok X-aránya így a val-énál kisebb lett (NJT 8% vs. 14%, TED 9% vs. 15%), és minden G3-kar a val-on
      rosszabbul fedte a gold-drop X-et (0,850 → 0,764–0,780), a 25%-os kar is: ez prior-eltolódás, nem a tanítás
      mennyisége. A HO-termék X-ei 89%-ban gold-drop típusúak, ezért a H6(a) ott a keverék miatt bukhatna el.
    - **v2:** a gold-drop családokban a jelöltkészlet X-aránya marad, a többi családban az X elsőbbséget kap a 30%-os
      sapkáig (mint a v1-ben); a típussapka 60%. Eredmény: X 9,25% (1619), ebből gold-drop 59%, csere 0.
    - A szabályváltozást a mechanizmus indokolja, nem a val-pontszám; a kitartott rétegek predikcióihoz nem nyúltunk
      (csak az X-típusok arányát néztük az itemek metaadatában).
    - A v1-es pilot (G3, G3-kemény) és a tanulási görbe leíró marad; a G3-karok (3 seed), a G3-kemény és a G3-hu a
      v2-n fut.

18. **A v1 jóváhagyva, pontosításokkal** (Dani, 2026-10-14; a 7. pont ennek megfelelően átírva, Napló):
    - a tárgy a meglévő MVP v2, az adapterek, a rétegek, a kalibrációs minták és a promptkeretek; új tanítás,
      tanárkeresés és címkézés nincs. Rögzítés verzióval és hash-sel (7.10);
    - a vakság pontos leírása: a G3-karok F4-eredményei és az összehasonlítások nem voltak ismertek; az L1★
      HO-eredményei és a 00/01 eredményei igen (7.1);
    - H1: háromállapotú rétegítélet, közös Holm a hat próbára, seedenkénti jelentés (7.5);
    - H2: pozitív referencianyereség feltétele és a D-kontraszt (7.6);
    - H3: „az előírt toleranciaküszöböt teljesítette”, a nulla elfogadott item és a hiányzó τ előre rögzítve (7.7);
    - H4 és H6 állításainak határa; a H6 feltáró (7.8);
    - a technikai lezárás pontos (id, perm)-egyezéssel és a pótlás érzékenységi bontásával (7.9);
    - az MDE előzetes érzékenységi becslés; minden hipotézis az eredménylapra; a receptmódosítás külön kör (7.10,
      7.11).

    A rögzítés és a technikai lezárás után az F4 elemzése újabb jóváhagyási kör nélkül indulhat.

**A v1 előtt nyitott pontok** (lezárva a v1-ben, 2026-10-14):

- a tanárkapu lefutott, egyik tanár sem ment át (14.);
- a célréteg-kalibrációs minta 200 item rétegenként, egész klaszterekben (`adat/f4/kalib.json`); a HO-routingon
  ebből a megerősítő részbe eső 146 item kalibrál (7.3);
- a promptkeret: a HO-terméken és a HO-routingon az eredeti 00/01 prompt az elsődleges;
- a `noul` kétopciós choice-ként, a `score` kimarad (az F0-ban így épült);
- a kitartott csoportok határa: a MASSIVE és a BFCL/When2Call csak a HO-routingban van, a train-poolban és az MVP-ben
  nincs (2026-10-13, név szerinti ellenőrzés); a KN/VTSZ és az ESCI a 03 adatában sehol nem szerepel, így a
  termék-csoport határa a 00 tesztje (HO-termék).

---

## 11. Kockázatok

- **Shortcut és gold-drop artefaktum:** a modell megtanulhatja, hogy „ha nincs nagyon hasonló jelölt, akkor X”.
  Ellenszer a hard-NOTA, a családonkénti shortcut-baseline és a ≤ 15%-os konstrukciós arány.
- **Konstans X-prior:** ellenszer a családonként eltérő X-arány és a 0%-os családok.
- **A tanár X-gyengesége** (00-mérés): ellenszer a típusonkénti X-kapu és a keverékben a gold (4.1, 4.4).
- **Irrelevancia-kompromisszum** (01 H5): a döntésre tanítás rontja az irrelevancia-felismerést. Ellenszer a négy
  X-típus, a bázis-horgony és a H6.
- **Konvenció-beégés** (01 T-hu): a forrás címkézési szokásai magabiztosan tanulódnak. A tervezett ellenszer, a
  puha cél és a tanár–gold ellentmondások kihagyása (4.1), tanár híján elmaradt (10. pont 14.); a 03-ban csak a
  horgony és a gépi zajszűrés hat erre, és a H6(c) is csak leíró (7.8).
- **Tanár-körkörösség:** a Mistral írta és bírálta a 01 T-katalógusát. Ellenszer az eval-függetlenség szabálya
  (4.4).
- **A kalibráció nem visz át** (01: a val-τ egyik karnál sem tartotta a 95%-ot). Ellenszer a H3 célréteg-kalibrációs
  útja.
- **Forrás-gold zaj:** a MASSIVE-leképezésnél ~13% volt. Ellenszer a gépi zajbecslés (4.2); emberi audit nélkül
  a forrás-gold rétegek leíróak.
- **Kitartás-szivárgás:** rokon forrás maradhat a trainben (tasksource intent-források, ESCI). Ellenszer a
  forrásnév-szintű kitartás-lista.
- **FLORES-szivárgás:** a Belebele és a SIB-200 közös szövegű, ezért egyik sem lehet train.
- **Fordításízű magyar:** ellenszer a ≤ 10%-os fordított arány és az emberi magyar HO-rétegek.
- **Plafonhatás a val-on** (00): ellenszer a nehéz val, az AURC és a plafonhoz mért jelentés.
- **Kapacitás:** ellenszer a kis MVP, a tanulási görbe és a hosszú itemek korlátja.
- **`--enable-lora` kernelváltás** (00 H3(d)): élesben a LoRA külön példányra kerül.
- **Emberi átnézés nélkül** (10. pont) a forrás- és a szintetikus gold zaja csak gépi becslés, és a gépi egyetértés
  a könnyű itemek felé torzít (01). Ellenszer: megerősítő állítás csak az emberileg átnézett 00/01 HO-rétegeken és a
  konstrukciós HO-új-családon (4.6); a szintetikus családok csak train-ben vannak.

---

## Források

- Ötletanyag: [magyar-dontesi-tanitoanyag-otletek.md](magyar-dontesi-tanitoanyag-otletek.md)
- HF-felmérés: [jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md](jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md) ·
  külső anyag: [open_datasets_research.md](open_datasets_research.md)
- Licencjegyzet (Llama, Qwen Community): [jegyzokonyv/2026-10-03-licenc-szerzodes.md](jegyzokonyv/2026-10-03-licenc-szerzodes.md)
- **JPT-35B-A3B** (`kirp/jpt-35b-a3b`, CC-BY-NC-4.0; Dani mutatta 2026-10-10): JEV-interfészű döntési LoRA a
  Qwen3.5-35B-A3B-n, gyakorlatilag a 00 receptjével (r = 16, α = 32, a router fagyasztva), csak Brier-veszteséggel,
  49 ezer angol kérdésen. In-distribution +15 pont, de az ECE 0,031 → 0,171, és egy globális temperature ezt nem
  javítja: a 01 kalibrációs leletének független megerősítése (0. pont, 4.1, 4.7). A gyengéje az aritmetika, a
  dátum és a tudás (nincs gondolkodási fázis), ami a HO-új KIE-családra figyelmeztet. A magyar csak mellékesen
  van benne. A licence és a zárt modell (GPT-6 Luna) írta tanítóadata miatt nálunk legfeljebb leíró
  eval-referencia lehet, tanár vagy generátor nem.
- HuCOLA (licenc, rejtett tesztcímkék): https://github.com/nytud/HuCOLA · HuLU: https://hulu.nytud.hu/tasks
- Belebele: https://preview.aclanthology.org/setup/2024.acl-long.44 · SIB-200: https://huggingface.co/datasets/Davlan/sib200
- MultiEURLEX: https://huggingface.co/datasets/coastalcph/multi_eurlex
- NerKor (licenclista): https://github.com/oroszgy/awesome-hungarian-nlp
- OpinHuBank: https://metashare.nytud.hu/repository/browse/hungarian-opinion-tagged-sentence-bank/608756be64e211e2aa7c68b599c26a068dd5b3551f024f6281131670412d37d3/
- TED jogi nyilatkozat: https://ted.europa.eu/en/legal-notice · adat-újrahasznosítás: https://ted.europa.eu/en/help/data-reuse
- JEV-27B: https://huggingface.co/autotrust/JEV-27B
- Gemma 4 26B-A4B-it: https://huggingface.co/google/gemma-4-26B-A4B-it · Decision Index kit: https://github.com/apolinario/decision-index ·
  JEV-eredmények: https://huggingface.co/datasets/autotrust/jev-decision-index-results

---

## Napló

- **2026-10-14 este — F4: lezárás és elemzés (a v1 szerint; gépi eredménylap: `kor03/eredmenyek/F4/eredmenylap_gepi.md`).**
  - **Futás:** az L0′ 17:37–21:08 (hiba 0), a pótlás 21:08–21:32, majd a lánc. A manifest mind a 32 fájlon egyezik, a
    technikai lezárás rendben:
    - mind a 25 kar teljes, ismétlődés és érvénytelen sor nélkül;
    - a G3 s1-en 5545, az s3-on 2206 pótolt pár, pontosan a hibanapló párjai;
    - az eredeti sorok előtagja a pecsétnek megfelelő;
    - a PECSET a pillanatképpel kezdődik.

    Az elemzés 10 000 ismétléssel 21:33–21:37 között futott; egyik fő kontraszt pontbecslése sem esik a saját CI-jén
    kívül. Az L0′-szabály sehol sem lépett életbe (|Δlef| ≤ 0,2 pont, top-1-billenés 1,2–3,5%).
  - **H1: mindhárom rétegen „nem teljesíti a követelményeket”.** A lefedettség mindenhol szignifikánsan nő, de a G3
    precizitása a val-τ-val a 0,93 alatt van; a HO-terméken és a HO-routingon az AURC is szignifikánsan rosszabb.

    | réteg | L1★ lef / prec. / AURC | G3 (3 seed) lef / prec. / AURC | Δlef@95 [CI] | ΔAURC [CI] |
    |---|---|---|---|---|
    | HO-termék | 0,653 / 0,963 / 0,030 | 0,761 / 0,912 / 0,043 | +11,1 [6,9; 16,1] pont | +0,014 [0,002; 0,027] |
    | HO-routing | 0,644 / 0,918 / 0,034 | 0,732 / 0,866 / 0,082 | +8,9 [6,7; 11,3] pont | +0,047 [0,039; 0,057] |
    | HO-új | 0,568 / 0,938 / 0,072 | 0,636 / 0,905 / 0,044 | +7,2 [3,7; 11,0] pont | −0,027 [−0,033; −0,022] |

    A tervezet HO-routing-rétegén (a T-hu-maradékkal) ugyanez: G3 precizitás 0,882.
  - **H2: formálisan mindkét rétegen „érdemi átvitel”** (D [CI]: HO-termék +0,057 [0,025; 0,097], HO-routing +0,026
    [0,007; 0,049]; nyereségarány 1,05 és 0,71). A H2 csak lefedettséget hasonlít, és ez a lefedettség más
    precizitáson van:
    - HO-terméken a 00 L3 0,97-es precizitással, 0,0016-os AURC-vel ér el ennyit, a G3 0,91-gyel és 0,043-mal;
    - HO-routingon a 01 L3 precizitása 0,84, a G3-é 0,87.
  - **H3: (a) mindhárom rétegen nem teljesítette.** (b) A HO-terméken és a HO-routingon a kalibrációs mintán nincs
    megfelelő τ: nem siker (a replikák 90, illetve 97%-ában sincs). A HO-újon teljesítette: precizitás 0,975, lefedettség
    0,34–0,52; az L1★ ugyanott 0,976 / 0,50.
    - Az oracle-τ-hoz mérve a G3 val-τ-ja túl engedékeny. A HO-routingon a saját tesztjén illesztett τ mellett a G3
      lefedettsége 0,00–0,05 lenne (a bázisé 0,47): a 95%-os precizitás ott a G3-mal gyakorlatilag nem érhető el.
  - **H4 (G3 s1 vs. G3-hu s1):**
    - HO-termék: „nem teljesíti”, mert a G3 s1 precizitása 0,924, és az angollal az AURC szignifikánsan rosszabb
      (+0,005);
    - HO-új: „nem teljesíti”, a precizitás miatt (0,916), pedig a Δlef +2,9 pont szignifikáns;
    - HO-routing magyar része: „segít” (ΔAURC −0,0026 [−0,0048; −0,0010], a precizitás 0,964).
  - **H5 (leíró):** a lef@95 minden teszt-ID-családon nő; a precizitás a jogi családokon esik (MultiEURLEX 0,78 → 0,68,
    NJT fejezet 0,93 → 0,77). Ez a val gold-drop résének folytatása.
  - **H6 (feltáró): az X-fedés megőrzése sem a G3-nál, sem a G3-keménynél nem igazolható.**
    - Δ G3 − L1★: HO-routing −19,3 pont, HO-termék −7,6 pont. A HO-routing out-of-scope X-fedése 0,74 → 0,53: a 01
      irrelevancia-kompromisszuma itt is megjelenik.
    - A horgony (G3 s1 − G3-kemény s1) nem egyirányú:
      - HO-routing: X-fedés −1,1 pont, AURC −0,006;
      - HO-termék: X-fedés −6,7 pont, AURC +0,007.
    - A HO-új természetes X-ét a G3 felismeri (0,01 → 0,84).
    - (c) Az 51 átcímkézett routing-itemen a régi címkét adja (ebből a τ fölött):
      - L1★: 13 (6);
      - G3: 12–15 (8–10);
      - a 01 L3: 26–29 (mind a τ fölött).

      A routing kimaradt a G3 tanításából, ezért ez nem közvetlen bizonyíték.
  - **A pótlás érzékenységi bontása:** a pótolt itemek a HO-routing fájljának első blokkja (BFCL simple, multiple,
    irrelevance, live simple, a live multiple egy része), tehát az összetételük eltér. A G3 precizitása rajtuk 0,952, a
    többin 0,842; a Δlef mindkettőn pozitív (+5,5 és +9,7 pont). A különbség a forrásösszetételből jön, nem
    különíthető el a példányhatástól.
  - **Következtetés:**
    - Az általános G3 a kitartott családokon több itemet fogad el, de a val-on választott τ nem viszi át a 95%-os
      precizitást, ahogy a 01-ben sem.
    - A HO-routingon a G3 az irrelevanciát rosszabbul ismeri fel, és ezt a horgony nem védi ki.
    - A publikus általános döntési adapter feltétele (H1) ebben a körben nem teljesült. A recept módosítása a 7.10
      szerint külön kísérleti kör.
  - **Értelmező eredménylap (2026-10-15):** [kor03/eredmenyek/F4/eredmenylap.md](kor03/eredmenyek/F4/eredmenylap.md).
    Utólagos leíró bontásokkal: `f4_leiro03.py` → `f4_leiro03.json`, a Sparkon számolva, csak aggregátum.
    - A HO-terméken és a HO-routingon a nem-X precizitás 0,99; a precizitásesés teljes egészében abból jön, hogy az
      X-gold itemek nagyobb részét fogadja el (25% és 28%, a bázis 9% és 15%).
    - A HO-újon a kie.összeg aritmetikája buktatja a precizitást.
    - Az angol gerinc nélküli G3-hu az angol routing-irrelevancián sokkal kevésbé romlik (utólagos megfigyelés).
  - **Feltáró kiegészítés (2026-10-15): kétlépcsős döntés** (X a bázisból, opció a G3-ból; `f4_ketlepcso03.py`, az
    eredménylap végén).
    - A G3 kárát eltünteti: a HO-routing a bázis szintjén van, az X-fedés a bázisé.
    - Azonos (95%-os) precizitáson azonban a lefedettsége sehol sem nagyobb a bázisénál: HO-termék 0,675 vs. 0,682,
      HO-routing 0,490 vs. 0,471.
    - A szűk keresztmetszet a kitartott terület X-konvenciója: a 00 L3 94%-ban, a bázis 42%-ban, a G3 34%-ban ismeri fel
      a HO-termék X-ét.
  - **Decision Index 0.3 teljes futtatása (Dani, 2026-10-15): egyelőre elmarad**, mert kevés nyereséggel járna. Becsült
    költsége fél–egy nap illesztés (>10 opció, multi-select, rangsor, 8192 tokenes korlát) és 15–17 óra kiolvasás
    (G3 + bázis); a teljes index helyett benchmarkonkénti pontosságot adna, a mi X-kérdésünket nem mérné. Az 5. pont
    választott DI-sávjai (külső eval réteg, JEV-referencia) ettől függetlenek.
  - **A továbblépés (Dani, 2026-10-15): egyelőre megállunk, és a negatív eredményt közzétesszük.** A 04 terve
    ([04-runbook.md](04-runbook.md), v0.1) parkol. Az eredménylap 7.10 szerinti „nem publikálható” ajánlását Dani
    felülírta: az adapter kutatási melléktermékként, „nem használatra” kártyával kerül ki.
    - **Blog** (docai_web, `generaldecision`): `/blog/altalanos-dontesi-adapter-negativ-eredmeny` és
      `/en/blog/general-decision-adapter-negative-result`. Lokálisan kész, a smoke 200; a commit és a deploy Danié.
    - **HF-adapter:** `k3dani/Qwen3.6-35B-A3B-hu-general-decision-lora-negative-result`.
      - Tartalom: a G3 s1–s3 (peft és vLLM változat), `calibration.json` a val-τ-kkal és a bázis-referenciával,
        `decision_prompt.py`;
      - a promptépítő 86 304 prompton bájtra egyezik a `kozos03.messages`-szel;
      - Apache-2.0 (9. pont).
    - **HF-adatkészlet:** `k3dani/hu-general-decision-mix`. Az MVP v2 train (17 500) és a `val03` (3122), két
      konfigurációban: `permissive` és `sharealike` (9. pont (a)/(b)). Az export: `kor03/eszkozok/hf_export03.py`.
      - A `meta`-ból csak a forrásazonosítók maradnak.
      - PII-minta: a szintetikus e-mailek mind `.example` domainen vannak; a TED egyetlen találata azonosító volt.
    - **Bizonyíték:** `docai-evals/experiments/2026-10-15-general-decision-lora-negative-gb10`.
    - **A két HF-repó egyelőre privát**, és Dani átnézése után lesz nyilvános. A feltöltés a Sparkról ment, a
      `lora-train:2` konténerből: `HF_HOME=/tmp/hfhome`, a token-fájl csak olvashatóan csatolva, mert a Xet írható
      cache-t kér.
  - **Javítás az eredménylapon (2026-10-15):** az „Ami megáll” KIE-pontja a természetes X-hez a hiányzó feltétel
    leírását írta. Helyesen a természetes X az, hogy „egyik tételsor sem hibás” (0,01 → 0,84); a hiányzó feltételt csak
    kissé jobban ismeri fel (0,50 → 0,58).

- **2026-10-14 — A v1 jóváhagyása és rögzítése; az F4-elemzés előkészítése.**
  - **Jóváhagyás (Dani, délelőtt):** a v1 a pontosításaival (10. pont 18.); a 7. pont, a fejléc és a hozzá kapcsolódó
    helyek (4.6, 4.7, 5., 11.) ennek megfelelően átírva. A tervezethez képest:
    - a H1 háromállapotú rétegítéletet kapott;
    - a H2 a pozitív referencianyereség feltételét és a D-kontrasztot;
    - a H3 ítélete „az előírt toleranciaküszöböt teljesítette” lett;
    - a H4 és a H6 állításainak határa rögzítve, a H6 feltáró;
    - a technikai lezárás pontos (id, perm)-egyezéssel és érzékenységi bontással;
    - az MDE előzetes érzékenységi becslés.
  - **Javítás a tervezethez, az eredmények megtekintése előtt:** a tervezet HO-routing-rétege a 01 teljes tesztje volt
    (9813 item), benne a T-hu-maradékkal (2320 item, a 01-ben leíró, ~10% címkezaj). Ez eltért az 5. pont
    definíciójától és a 4.6 szabályától.
    - A v1 HO-routing-rétege a 01 megerősítő tesztje: 7493 item, 7416 pontozott (7.3).
    - A `kalib.json` változatlan: a megerősítő részbe eső 146 item kalibrál, a 54 maradék-item egyik tesztben sincs.
    - A tervezet rétege érzékenységi elemzésként marad.
    - A HO-routing azonosítói a 01 itemekhez a `source_ref` mezőn kapcsolódnak (10 013/10 013, a gold mind egyezik). Az
      átcímkézett itemek száma 51 (a T-hu 40, a MASSIVE további 4, a T-katalógus 7). A tervezet „593” száma a T-hu
      átnézett részének mérete volt, nem az átcímkézetteké.
  - **Elemző: `kor03/eszkozok/f4_elemzes03.py`** (a 7. pont szabályai; gyors τ a Clopper–Pearson-korlát k-küszöbtáblájával).
    - **Önteszt:** a kalibrációs karválasztás mind a hat karon az F3-éval egyezik (kar, T, τ). A gyors τ és a
      mérőszámok klaszteres újramintákon is egyeznek az `elemzes.py`-éval.
    - **Vakpróba** (`--proba`): minden F4-kiolvasás helyett az L1★ F2-es eval-kiolvasása állt. A csővezeték helyben
      és a Sparkon, a `lora-train:2` konténerben is lefut, és az L0′ = L1★ esetén a Δ pontosan 0. 200 ismétlés helyben
      ~1 perc 45 mp; a 10 000 ismétlés ~1 óra.
  - **Technikai lezárás: `kor03/eszkozok/f4_teljesseg03.py`**, csak standard könyvtár, eredményt nem ír ki. Próbafutás
    a kész karokon (09:36):
    - G3 s1: 5545 pár hiányzik, s3: 2206 pár, mind a hibanaplóban;
    - G3 s2, l3mixse s1–s3, k01 s1–s2: teljes, érvénytelen sor 0, a pecsét egyezik;
    - a nem lepecsételt kiolvasások (F2 L1★, F3 val, 00/01 L3 val) teljesek és érvényesek;
    - az append-only előtag-ellenőrzés szintetikus fájlon helyes, a módosított eredeti sort kiszűri.
  - **A bemenetek egyeztetése** (31 fájl, helyben és a Sparkon): 28 bitre azonos. A `kalib.json` csak helyben volt, az
    `items_ho_termek/routing.jsonl` csak a Sparkon: átmásolva, a hash egyezik a vezénylő `bemenet_sha256.txt`-jével.
    Az elemzőkód és a lánc a rögzítéskor került fel.
  - **Az MDE újraszámolva** a v1 rétegeire (`mde03.py`, ugyanazzal a seeddel; 7.11). A HO-termék és a HO-új oszlop
    bitre a tervezeté, a HO-routing H1 lef@95 6,4 → 6,5 pont.
  - **Független kódátnézés a rögzítés előtt** (code-reviewer agent), egy súlyos hibával:
    - **A hiba:** a bootstrap-csoportok közt a 00/01 val és a tesztréteg ugyanazt a nevet kapta (`ho-termek`,
      `ho-routing`). Így az L3-spec karok τ-ja a replikákban a tesztréteg újramintáján választódott (gyakorlatilag
      oracle-τ), a pontbecslésé viszont helyesen a saját val-on. A vakpróbán ez a H2-ítéletet meg is fordította (az L3
      nyereségének pontja +0,235, a CI-je [−0,111; 0,007]).
    - **Javítva**, és a csoportnevek ütközését most egy assert tiltja.
    - **Új önellenőrzés:** a fő kontrasztok pontbecslése essen a saját bootstrap-CI-jükbe. Az ismételt vakpróbán
      egyik sem esik kívül.
    - **További javítások:**
      - a H3(b) „nincs τ” aránya átlag, nem medián;
      - modellnév-ellenőrzés a 00/01 val-kiolvasásokon is;
      - a pótolt párok és a hibanapló párjainak egyezése, valamint a PECSET-pillanatkép (7.9);
      - `sha256sum --strict`;
      - a próbafutás és a részleges lezárás nem írhat a valódi kimenet helyére;
      - a nulla elfogadott itemű seed szabálya pontosítva (7.5).
  - **Rögzítés (10:08):** `kor03/rogzites/v1/`.
    - Tartalma:
      - `03-runbook-v1.md`;
      - `MANIFEST.sha256` (32 fájl), sha256 `86e5e9ac…16abb`;
      - `PECSET-pillanatkep.sha256` (9 sor: G3 s1–s3, a hat L3-spec kar);
      - `ROGZITES.txt`.
    - A lánc (`f4_elemzes_lanc.sh`) sha256-ja `27580db0…a80b`.
    - A manifest helyben és a Sparkon is `sha256sum --strict -c`-vel ellenőrizve, mind a 32 fájl egyezik. Az élő PECSET
      a pillanatképpel kezdődik. Az F4 összehasonlító eredményei a rögzítéskor nem voltak megtekintve.
  - **Az elemzőlánc 10:09-kor indult** a Sparkon (`logs/k03f4_elemzes.out`), és vár a pótlásra (`DONE-K03F4-potlas`).
    - **Közben:** a k01_l3mixse_p30_s3 kész, a G3-kemény 09:46-tól fut. 12:43-kor 11,3 kiolvasás/s-mal halad, a G3 s2
      13,6/s-ánál lassabban (a Spark terhelése normális). 13:40-re végzett, hiba nélkül, lepecsételve.
    - **A G3-hu** 13:40–17:35, hiba nélkül, lepecsételve (a PECSET 11 sor). A fő kiolvasás kész (`DONE-K03F4-kiolvasas`).
    - **Az L0′** 17:37-től fut, adapter nélkül gyorsabban: 18:08-kor 25,7 kiolvasás/s, vége ~19:45. Utána jön a pótlás
      (~20:15).
    - **Utána:** manifest-ellenőrzés, technikai lezárás, majd a bootstrap (~1–1,5 óra). Várható vége szerda
      ~21:30–22:00.

- **2026-10-14 — F4: hiányos G3-kiolvasások, javítás és pótlás.**
  - **Lelet (06:40, csak a hibanaplókból):** a G3 s1 kiolvasásából 5545, az s3-éból 2206 sor maradt el (az s2 teljes),
    mind a HO-routing 01-es itemein (s1: 1387 item, s3: 553 a 10 013-ból). A hiba `module 'ldh_keret01' has no attribute
    'messages_for'`: a `common._keret01` a modult a végrehajtása előtt tette ki a globálisba, így a 64 kiolvasó szál egy
    része félkész modult kapott. A hibás kérés azonnal visszatér, ezért a betöltés néhány másodperce alatt ezrek
    hibáztak. Helyben reprodukálva (64 szál: régi betöltő 63/64 hiba, javított 0/64).
  - **Javítás:** `eszkozok/common.py`, zárral, csak a teljesen végrehajtott modul kerül a globálisba; 06:42-től a
    Sparkon. A futó l3mixse-kar (HO-termék, 01-es item nélkül) a régi modullal fut, a k01-karok, a G3-kemény, a G3-hu
    és az L0′ már a javítottal indul.
  - **A korábbi kiolvasásokat nem érintette:** az F2 és F3 hibanaplóiban nincs ilyen hiba; az F3 val-kiolvasások
    teljesek (12 488 sor). Az F2 `qwen_eval`/`qwen_val` teljes, ismétlődés nélküli, és 44 / 85 olyan itemet is
    tartalmaz, amely azóta kikerült az itemfájlokból: az elemzés id szerint illeszt, ezek kiesnek.
  - **Pótlás** (`kor03/eszkozok/f4_potlas.sh`, várakozó lánc, 06:44-től): az L0′ után minden F4-karra, ha a kimenet
    sorszáma < itemek × 4, ugyanazzal az adapterrel újraolvas; a kiolvasó csak a hiányzó (id, perm) párokat kéri. A
    pótolt sorok más vLLM-példányról jönnek, mint a kar többi sora (példányzaj, az L0′ méri). A pecsét append-only: a
    kiegészített fájl új sha256-ja a `PECSET.sha256` végére kerül, útvonalanként az utolsó sor érvényes. Várható vége
    szerda ~23:00.
- **2026-10-12 — F3: a pilot és a tanulási görbe eredménye; MVP v2.**
  - **Futás:** a G3-kemény 16:35–23:40, a görbe 25%-a 1,7 óra, 50%-a 3,4 óra, a val-kiolvasások 15 perc; hiba 0.
  - **Val (in-sample, karok összevetésére; az MVP v1-en):**

    | kar | lef@95 | AURC | ECE | top-1 | X-fedés | gold-drop X |
    |---|---|---|---|---|---|---|
    | L1★ | 0,669 | 0,025 | 0,026 | 0,848 | 0,808 | 0,850 |
    | G3, 25% | 0,796 | 0,015 | 0,025 | 0,893 | 0,823 | 0,772 |
    | G3, 50% | 0,807 | 0,013 | 0,023 | 0,909 | 0,842 | 0,780 |
    | G3, 100% | 0,831 | 0,012 | 0,018 | 0,921 | 0,853 | 0,772 |
    | G3-kemény | 0,828 | 0,013 | 0,028 | 0,917 | 0,850 | 0,764 |

    - **Tanulási görbe:** a nyereség zöme a 25%-nál megvan (+12,7 pont a +16,2-ből), de 100%-ig nő.
    - **Horgony (G3 vs. G3-kemény):** a val-on csak a kalibrációban látszik (ECE 0,018 vs. 0,028); egy seed.
    - **Gold-drop X:** minden G3-karon esik, a 25%-oson is ugyanannyit. A gold-drop családok X-aránya az MVP v1-ben a
      val-énál kisebb (a típussapka cseréi miatt); a G3 a val gold-drop X-eiből 15-öt elveszít (NJT, MultiEURLEX,
      TED), 5-öt nyer (HuRC). → 10. pont 17., MVP v2.
  - **MVP v2** (`mvp03.py`, `adat/f3/mvp_train_v2.jsonl`, sha256 `65bd0bd7…`, determinisztikus): X 9,25%, gold-drop 59%,
    a gold-drop családok X-aránya a jelöltkészleté; minden más szabály változatlan. A v1 `mvp_train_v1.jsonl` néven.
  - **Tanító:** `--csak-hu` kapcsoló (G3-hu, az angol itemek nélkül, 13 125 item).
  - **F3 v2 indult 06:57-kor** (`f3_vezenylo.sh v2`): G3 s1 → G3-kemény s1 → G3 s2 → G3 s3 → G3-hu s1, mindegyik
    után val-kiolvasás; karok közt `STOP-K03F3`-mal megállítható. Várható vége kedd ~15:30. Az s1 val-eredménye
    (~14:00) mutatja meg, hogy a gold-drop X-fedés helyreállt-e.
  - **G3 s1 az MVP v2-n (06:57–14:08):** tanítás 6,7 óra, val-kiolvasás 15 perc, hiba 0.

    | kar | lef@95 | AURC | ECE | top-1 | X-fedés | gold-drop X |
    |---|---|---|---|---|---|---|
    | L1★ | 0,669 | 0,025 | 0,026 | 0,848 | 0,808 | 0,850 (108/127) |
    | G3 s1, v1 | 0,831 | 0,012 | 0,018 | 0,921 | 0,853 | 0,772 (98/127) |
    | G3 s1, v2 | 0,819 | 0,012 | 0,018 | 0,920 | 0,865 | 0,803 (102/127) |

    - **A gold-drop X részben helyreállt:** +4 item a v1-hez képest (MultiEURLEX +2, NJT fejezet +1, TED +1), de 6
      itemmel még az L1★ alatt (NJT cím 6/10 vs. 8/10, NJT fejezet 5/10 vs. 8/10, MultiEURLEX 21/24 vs. 24/24). A HuRC-n
      a G3 jobb (21/27 vs. 17/27). A prior-eltolódás a csökkenés egy részét magyarázta; a maradék vagy a tanítás
      hatása az NJT-családokon, vagy seed-zaj (a seed 2–3 megmutatja).
    - A lef@95 1,2 ponttal kisebb a v1-énél (több X-prior a gold-drop családokban), a precizitás azonos.
    - A HO-terméken (az X-ek 89%-a gold-drop) a H6(a) a v2-n is kockázatos; az F4 dönt.
  - **G3-kemény s1 az MVP v2-n (14:08–21:21):** lef@95 0,832 (G3: 0,819), AURC 0,012, ECE 0,027 (G3: 0,018), top-1
    0,922, X-fedés 0,868, gold-drop 0,819 (104/127; G3: 102/127). A v1-hez hasonlóan a horgony a val-on csak a
    kalibrációt javítja (ECE 0,018 vs. 0,027); a gold-drop X-et nem védi, pedig az X-gold itemeken a bázis eloszlása
    felé húz. Egy seed; a H6 a kitartott rétegeken dől el.
  - **G3 s2 az MVP v2-n (21:21–04:35):** lef@95 0,834 (a val-on a nyers kiolvasás lett a legjobb kalibrációs kar,
    ECE 0,031), AURC 0,014, top-1 0,912, X-fedés 0,861, gold-drop 0,780 (99/127). Az s1-gyel a top-1 az itemek
    96,8%-án egyezik.
    - **A gold-drop rés szisztematikus, nem seed-zaj:** mindhárom v2-karon (s1, s2, G3-kemény) ugyanott veszít a
      bázishoz képest: MultiEURLEX −3/−4, NJT cím −2, NJT fejezet −2/−3 (a HuRC-n +4/+5). A jogi családokban a
      gold-drop X rokon, nem azonos jelöltekkel marad (hard-NOTA); a tanítás az itemek ~87%-án a legközelebbi
      jelölt választását erősíti, és a bázis óvatosabb volt. A HO-terméken (gold-drop X 89%) ez az F4 fő kockázata.
  - **G3 s3 az MVP v2-n (04:35–11:47):** lef@95 0,832, AURC 0,012, ECE 0,020, top-1 0,918, X-fedés 0,850, gold-drop
    0,780 (99/127). **A G3 három seedje a val-on** (átlag ± szórás): lef@95 0,828 ± 0,008, AURC 0,012 ± 0,001, ECE
    0,023 ± 0,007, top-1 0,917 ± 0,004, X-fedés 0,858 ± 0,008, gold-drop 0,787 ± 0,014 (L1★: 0,669 / 0,025 / 0,026 /
    0,848 / 0,808 / 0,850).
  - **G3-hu s1 az MVP v2-n (11:47–17:18), az F3 vége:** 13 125 item (az angol gerinc nélkül), lef@95 0,759, AURC
    0,016, ECE 0,032, top-1 0,894, X-fedés 0,853, gold-drop 0,811. A különbség zöme a val angol csoportjából jön (lef@95
    0,600 vs. a G3 s1 0,792), de a magyar csoportok is gyengébbek, legjobban az NLI (0,877 vs. 0,932) és a szentiment
    (0,740 vs. 0,828); a közbeszerzésen jobb (0,813 vs. 0,787). Zavaró tényező: a G3-hu 25%-kal kevesebb itemen tanult
    (a görbe szerint ez ~1 pont a teljes val-on). A H4 a kitartott rétegeken dől el.
  - **Az F3 teljes:** v1-en G3 s1, G3-kemény s1, görbe 25/50%; v2-n G3 s1–s3, G3-kemény s1, G3-hu s1. Hiba 0, összesen
    ~60 óra Spark.
- **2026-10-13 — F4: lepecsételt kiolvasás** (Dani: „lepecsételt kiolvasás most”, a v1 előtt).
  - **Szabály:** a kiolvasás a v1 (küszöbök, MDE, célréteg-kalibrációs minták) rögzítése előtt fut, az elemzés csak
    Dani jóváhagyása után. Az eredményfájlok a Sparkon maradnak (`kor03/eredmenyek/F4/<kar>/vllm_eval.jsonl`), és
    mindegyik sha256-ja a `PECSET.sha256`-ba kerül, amint elkészül.
  - **`kor03/eszkozok/f4_vezenylo.sh`**, 18:33-tól, ugyanazzal a LORA=1-es alannyal és kiolvasóval, mint az F2 L1★-ja:
    G3 s1–s3 → L3-spec (a 00 `l3mixse_h2_s1..s3` a HO-terméken, a 01 `k01_l3mixse_p30_s1..s3` a HO-routingon) →
    G3-kemény → G3-hu; a G3-karok az összes eval-itemen (45 965), 4 permutációval. Az L1★ eval-kiolvasása az F2-ből
    kész. Várható vége szerda ~18:30; karok közt `STOP-K03F4`-gyel megállítható. A JPT-ref később (66 GB letöltés).
  - **L0′** (`f4_l0r.sh`, várakozó lánc): az L1★ eval-kiolvasásának ismétlése egy új vLLM-példányon a sor végén (a
    példányzaj mérésére, a 00 F4 L0′-jének mintájára), szintén a pecsétbe. Várható vége szerda ~22:15.
  - **v1-tervezet** (7. pont, Dani jóváhagyására vár), a teszt-predikciók megnézése nélkül:
    - célréteg-kalibrációs minták (`f4_kalib03.py` → `adat/f4/kalib.json`): HO-termék 200 item / 105 klaszter, HO-routing
      200 / 136, HO-új a jelölt 200; az X-arányuk a maradék tesztével egyezik (0,220 vs. 0,203; 0,320 vs. 0,322);
    - MDE (`mde03.py`, a val-ról vetítve): H1 lef@95 6,4–6,8 pont (val-Δ +15,0), AURC 0,003–0,006 (val-Δ −0,013); H4
      lef@95 4,0–4,3 (val-Δ +6,0); H6(b) AURC 0,0013–0,0027 (val-Δ −0,0003, alulerős);
    - a csoporthatár-ellenőrzés: a MASSIVE és a BFCL/When2Call csak a HO-routingban van; a KN/VTSZ és az ESCI a 03
      adatában nem szerepel (a v0.3-as vázlat állítása pontatlan volt).

- **2026-10-11 — F2: a gondolkodó kiolvasások és a teljes F2-elemzés.**
  - **Futás:** a tanárkapu-minta 21:51–23:28 (2400 minta), a zajminta 23:28–01:20 (3215 minta), hiba 0, ~430
    token/s. A 4096 tokenes korlátnál levágva 19, illetve 15 minta (ezek nem szavaznak); a gondolkodás mediánja 895,
    illetve 819 token. (Az önellenőrzésben becsült 02:50 túl óvatos volt: a zaj-itemek rövidebbek.)
  - **Tanárkapu (a runbook 4.4 szabálya szerint):** egyik tanár sem megy át, egyik csoportban sem. Kivétel csak a
    Qwen gondolkodó a QA-csoportban, de ott a top-1-e azonos az L1★-éval (0,973), így nyereséget nem hoz.
    - **Qwen gondolkodó** (600 item, 4 minta): top-1 0,828 vs. L1★ 0,818 ugyanazokon az itemeken; csoportonként
      angol 0,853 vs. 0,747, entitás 0,907 vs. 0,867, közbeszerzés 0,907 vs. 0,893, NLI 0,867 vs. 0,853, QA
      0,973 = 0,973, jogi 0,627 vs. 0,693, konstrukciós 0,840 vs. 0,853, szentiment 0,653 vs. 0,667 (n = 75
      csoportonként: 1 item 1,3 pont). Az X-fedés típusonként rendben (gold-drop 0,79, természetes 0,80; az
      out-of-scope 0,38, de n = 8 < 10). Az ECE 0,129, csoportonként 0,02–0,33: a 4 minta egyezése nem bizonyosság
      (4/4 egyezés mellett is téved), a kvantáltság csak részben magyarázza.
    - **Gemma 4** (T = 4,97): összesen top-1 0,793 vs. 0,816, ECE 0,042; csoportonként az ECE 0,05 fölött, a top-1
      csak az angol gerincen (0,783 vs. 0,765) és az entitáson (0,875 = 0,875) éri el az L1★-et; az out-of-scope
      X-fedés 0,13.
    - **Mistral Small 4** (T = 2,30): top-1 0,654, minden csoportban 6–21 ponttal az L1★ alatt.
  - **Gépi zajbecslés** (két olvasó: a Gemma ≥ 0,8 kalibrált bizalommal, a val-on illesztett T-vel, és egy
    gondolkodó Qwen-minta; zajjelölt, ha a kettő ugyanarra a nem-gold címkére szavaz):

    | forrás | n | zajjelölt | + L1★ mint 3. olvasó (leíró) |
    |---|---|---|---|
    | HuCommitmentBank | 215 | **24,7%** | 37,2% |
    | HuSST | 300 | **13,3%** | 17,3% |
    | MultiEURLEX | 300 | 7,0% | 11,7% |
    | HuWNLI | 300 | 6,3% | 9,0% |
    | HuCOLA | 300 | 6,0% | 8,7% |
    | NerKor | 300 | 5,0% | 7,7% |
    | HuCoPA | 300 | 3,7% | 4,3% |
    | TED | 300 | 3,3% | 3,7% |
    | HuRTE | 300 | 1,7% | 2,7% |
    | HuRC | 300 | 1,0% | 1,3% |
    | MILQA | 300 | 0,0% | 0,0% |

    - **A két 10% fölötti forrás szerkezete eltér:**
      - HuSST: 40 zajjelöltből 37-ben a gold „semleges”, a két olvasó negatívat vagy pozitívat mond. Ez a
        semleges–enyhe szentiment határ, valódi címke-bizonytalanság; a szentiment csoportban minden kar gyenge
        (top-1 0,65–0,73).
      - HuCB: 53-ból 48-ban a gold X (a beszélő nem kötelezi el magát), a két olvasó igent vagy nemet mond. Ez
        inkább az olvasók X-vaksága ezen a típuson: a val NLI-csoportjában a természetes X-et sem a Gemma, sem a
        gondolkodó Qwen nem ismeri fel (fedés 0,00, n = 7 és 3). A szabály ezt nem különbözteti meg a címkezajtól.
      - MultiEURLEX (bent marad): 21-ből 18-ban a két olvasó X-et mond egy gold tárgykörre (11× Földrajz).
    - A HuCB kiesése 215 train-itemet és 99 természetes X-et visz (a természetes X-ek 12,5%-a, a maradék 87%-a
      MILQA); a HuSST 1500 train-itemet (a train 4,8%-a).
  - **Költség, ha a gondolkodó Qwen mégis tanár lenne:** az MVP-nek csak az 5 jobb csoportba eső része (~10 ezer
    item) 4 mintával ~36 millió token, ~23 óra Spark; a nyereség az angol gerincen kívül 1–3 item / 75.
  - **Dani döntései (07:00):** a tanítási cél gold + horgony (10. pont 14.), a HuSST és a HuCB kimarad (15.).
  - **Negyedik tanárjelölt: Qwen3.8-27B-FP8** (Dani, 07:00: „esetleg keressünk további modellt tanárnak?”; 4.4).
    Kapupróba a teljes val-on, ugyanazzal a szabállyal és kiolvasással, mint a Gemmánál (`f2_qwen38.sh`, F2T):
    letöltés (~28 GB), smoke 40 itemen (a címketömeg-medián ≥ 0,9, különben a gondolkodás-kapcsoló gyanús), majd
    3122 item × 4 permutáció. Indult 07:01-kor. Tegnap reggel egy letöltése 45/81 fájlnál megállt, amikor a
    generátor a Muse lett; a részleges fájlok nem maradtak meg.
  - **A gondolkodó mód kikapcsolva** (Dani, 07:10; 10. pont 16.): a G3→S2 kar kimarad. A Qwen3.8-próba eleve nem
    gondolkodik: a sablonja `enable_thinking = false` esetén üres `<think>` blokkot tesz a válasz elé (ellenőrizve),
    a kiolvasás `max_tokens = 1`.
  - **A Qwen3.8-27B-FP8 kapupróbája (07:01–07:54):** letöltés 8 perc (29 GB), boot 6,5 perc, smoke 40 itemen
    (címketömeg-medián 0,955, min 0,650), a val 3122 item × 4 permutáció ~39 perc alatt (~5,4 kérés/s, ~2100 prompt
    token/s), hiba 0. **Elbukott:** összesen top-1 0,798 vs. L1★ 0,816, ECE 0,030 (T = 1,40; a négy jelölt közül a
    legjobban kalibrált), X-fedés gold-drop 0,97, természetes 0,83, out-of-scope 0,47 (n = 15).
    - Csoportonként a top-1 az entitáson (0,905 vs. 0,875) és az NLI-n (0,889 vs. 0,833) jobb az L1★-nál. Az
      entitáson az out-of-scope X-fedés miatt bukik (7/15 = 0,47 < 0,5, egy itemen múlt), az NLI-n az ECE miatt
      (0,103). A többi hat csoportban a top-1 1–10 ponttal az L1★ alatt van (a jogin −6,3, a konstrukcióson −9,9).
    - A 27B dense modell tehát ezen a feladaton nem erősebb a bázis kalibrált kiolvasásánál. A tanárkérdés ebben a
      körben lezárva: a 14. döntés végleges (gold + horgony), a létra, a H6 és a fázisterv átírva.
  - **Reprodukálhatósági javítás az elemzőben:** a kapu ECE-je egyenlő elemszámú vödrökkel számol, és a gondolkodó
    tanár negyedekben kvantált bizalmánál a holtversenyek vödörhatára a Python-halmaz futásonként változó bejárási
    sorrendjétől függött (a csoportos ECE két futás közt 0,01–0,02-vel tért el). Most rendezett id-kkel és stabil
    rendezéssel számol; két futás bitre azonos. A kapu kimenete nem változott. Az elemző a zajjelöltek azonosítóit is
    kiírja (`adat/f2/zajjelolt.jsonl`, 195 item).
  - **MVP** (`mvp03.py` → `adat/f3/mvp_train.jsonl`, riport: `eredmenyek/F3/mvp_riport.json`; Dani: „mehetünk
    tovább”):
    - **17 500 item** (a 15–20 ezres sáv közepe), sha256 `cfcd4056…74976`, determinisztikus (két futás azonos).
    - **Kizárva:** HuSST 1500, HuCB 215 (10. pont 15.), 102 zajjelölt (a többi 93 a két kizárt forrásé), 1 horgony
      nélküli (a túl hosszú NJT-item).
    - **Arányok:** angol 25,0%, konstrukciós 15,0% (a sapka fogott: arányosan 15,1% lett volna), szintetikus 16,4%,
      plafon közeli 5,0% (a 12 család a poolbeli méretük arányában: MILQA 324, a három Muse-család 157–162, az angolok
      4–46), hosszú item 1.
    - **X 7,5% (1314):** gold-drop 657, out-of-scope 394, természetes 172, hiányzó feltétel 91.
      - Választás: a családon belül az X elsőbbséget kap, legfeljebb a családi kvóta 30%-áig (a 2. pont sapkája). A
        pool X-arányát tartva az MVP-ben 5,3% lett volna, mert a természetes X zöme (MILQA) plafon közeli, a HuCB
        pedig kiesett.
      - A szűk keresztmetszet a nem gold-drop X (~660): az 50%-os típussapka miatt 642 gold-drop X-et ugyanannak a
        családnak nem-X itemje váltott.
    - **Tanulási görbe:** családonként egymásba ágyazott negyedek: 25% = 4476 item (X 8,3%), 50% = 8771 (X 8,2%),
      100% = 17 500; mindhárom szinten mind a 207 család benne van.
    - A val-pool (3122) változatlan, a két kizárt forrással együtt: a τ és a temperature minden karnál ugyanazon a
      val-on választódik.
  - **F3 előkészítés** (Dani: „mehet”):
    - **Tanító: `kor03/eszkozok/tren03.py`**, a 00/01 `tren_lora.py` receptjével (mix+se, r16, α 32, lr 1e-4, 1 epoch,
      grad-accum 16, 30% perm-aug, döntési pozíció `logits_to_keep=1`), és a célmodulokat, a mentést és a
      vLLM-exportot onnan importálja. Három eltérés:
      - a prompt bitre azonos a 03-as kiolvasóéval (`kozos03.messages`, a bázis snapshotjának tokenizálója, kikapcsolt
        gondolkodás); az önteszt itemenként összeveti;
      - nincs bal oldali csonkolás: az MVP tokenhossza medián 306, p99 1307, max 4476 (7,05 millió token). A 01-es
        `--max-len 1024` 715 item (4%) elejét vágta volna le; most 5120, és a fölötte lévő item hibát ad;
      - veszteség: CE a gold-célra ε = 0,05-tel + 0,5 · Brier + β · KL(p_L1★ ‖ p_modell) az X-gold itemeken, a horgony az
        adott permutáció címkéire vetítve; a kétértelmű itemek célja a puha gold (311 item).
    - **Vezénylő: `kor03/eszkozok/f3_vezenylo.sh`.**
      - smoke: önteszt; 2 lépés a 32 leghosszabb itemen (memória); 4 lépés 64 itemen (sebesség, vLLM-export); az
        adapter a vLLM-ben, 40 val-item kiolvasása (címketömeg-medián ≥ 0,9).
      - pilot: G3 (β = 0,5) és G3-kemény (β = 0), seed 1, mindkettő után val-kiolvasás az adapterrel, 4 permutációval.
    - **Időbecslés:** a 01 tanítása 178 token/s-mal ment (egyesével, batch nélkül). Az MVP 7,05 millió tokenjével ez
      karonként ~11 óra, nem a 8. pontban becsült 8–11 óra alsó fele; a pontos szám a smoke-ból.
    - **Smoke (08:41–09:23), minden lépés zöld:**
      - önteszt 5 itemen (3 normál, 2 X-gold): a prompt bitre azonos a kiolvasóéval, a döntési pozíció helyes (az
        utolsó és a teljes forward eltérése 0,03, az utolsó előtti pozícióé 21–29), a cél és a horgony-vetítés jó;
      - 2 lépés a 32 leghosszabb itemen: memória-csúcs 71,8 GB, 320 token/s;
      - 4 lépés 64 itemen: 70,3 GB, 168 token/s (karonként ~11–12 óra);
      - az adapter a vLLM-ben (LORA=1), 40 val-item: címketömeg-medián 0,997, hiba 0.
      - A tanító konténere rootként ír, ezért a vezénylő a smoke-checkpointot nem tudta törölni (a tanító image-ével
        törölve). A vezénylő javítva (`ckpt_rm`); a Sparkra a pilot után kerül, mert futó szkriptet nem írunk felül.
    - **Pilot indult 09:24-kor:** G3 (β = 0,5), aztán a val-kiolvasása, majd a G3-kemény (β = 0) és a kiolvasása.
      A G3 várható vége ~21:20, a G3-keményé holnap ~09:30.
    - **Val-elemző: `kor03/eszkozok/f3_val03.py`** (az F2 L1★-választásával: a kalibrációs karok közül a val lef@95
      szerinti legjobb, saját temperature-rel és τ-val; in-sample, csak karok összevetésére). Az L1★-ra az F2 számait
      adja vissza (lef@95 0,669, top-1 0,848, τ@95 0,716).
  - **G3, seed 1 (09:24–16:35):** a tanítás 6 óra 46 perc (1094 lépés, ~295 token/s, memória 72 GB, NaN nélkül;
    a smoke 4 lépéses 168 token/s-a a bemelegedés miatt alábecsült), a val-kiolvasás 15 perc, hiba 0.
    - **Val, in-sample (a kar és a τ is a val-on választva; csak karok összevetésére):**

      | kar | lef@95 | lef@90 | precizitás | AURC | ECE | top-1 | X-fedés |
      |---|---|---|---|---|---|---|---|
      | L1★ | 0,669 | 0,821 | 0,958 | 0,025 | 0,026 | 0,848 | 0,808 |
      | G3 | **0,831** | 0,917 | 0,957 | **0,012** | 0,018 | 0,921 | 0,853 |

    - **Csoportonként** a lef@95 mindenhol nő; a legtöbbet az angol gerincen (0,536 → 0,822), a jogin (0,504 → 0,794)
      és a konstrukcióson (0,697 → 0,895). A precizitás a szentimenten 0,830 → 0,793 (mindkettő a 0,93 alatt; a val
      HuSST-itemjei a train-ből kimaradtak), a jogin 1,000 → 0,975.
    - **X-típusonként:** out-of-scope 0,724 → 0,983, természetes 0,806 → 0,875, hiányzó feltétel 0,78 → 1,00 (n = 9),
      de **gold-drop 0,850 → 0,772**: a jogin 0,931 → 0,778, a konstrukcióson 0,667 → 0,556 (n = 9). Lehetséges ok: az
      MVP-ben az 50%-os típussapka 642 gold-drop X-et nem-X itemre cserélt. Az NLI természetes X-ét (HuCB) egyik kar
      sem ismeri fel (0/7).
    - Ez in-distribution val: a családok ugyanazok, mint a train-ben. A H1–H6 a kitartott rétegeken dől el (F4).
  - **Éjszakai lánc (20:45; Dani: „ha elaltatom a gépem, akkor 23:25 után nem megy már semmi se a sparkon?”):** a
    `f3_lanc.sh` megvárja a pilot végét (G3-kemény ~23:40), a javított vezénylőt a helyére teszi (addig
    `f3_vezenylo.sh.uj` néven várt, mert a futó szkriptet nem írjuk felül), és indítja a tanulási görbét: G3 az MVP
    25%-án és 50%-án, seed 1, val-kiolvasással. Várható vége ~05:40. Leállítás: `STOP-K03F3` a kísérleti gyökérben
    (a pilot vége előtt).
- **2026-10-09 — F1 indul (Dani: a ShareAlike nem terjed ki a súlyokra; a javaslatok elfogadva, 10. pont 9–10.).**
  - **Keverő v0** (`kevero03.py`, spec: `kor03/spec/kevero.yaml`): jelöltkészlet (pool) ~26 ezer train + 2,6 ezer val
    item a szintetikus családok nélkül, családonkénti kvótával. Ebből az F2 L1★-mérése után lesz a 15–20 ezres MVP
    (10. pont 4.: a plafon közeli család legfeljebb 5%). Szabályok: X családon belül ≤ 30%, egy X-típus ≤ az X-ek 50%-a,
    konstrukciós ≤ 15%, szintetikus ≤ 30%, angol ~25%.
    - A gold-drop X-ek most az X-ek felét adják, így az X-arány 6,8%; a többi X-típust (hatókörön kívüli, hiányzó
      feltétel) zömmel a szintetikus családok hozzák. A keverő a generálás után újrafut.
  - **Szivárgás-audit, szöveges menet** (`szivargas03.py`). Saját mérőszám, a **8-gram-átfedés**: a jelölt
    állapotszövegének szó-8-gramjai közül hány szerepel bármely eval-réteg (teszt-ID, HO-rétegek a 00/01 tesztjeivel,
    külső evalok) szövegében. Kapu ≥ 0,5: kizárás.
    - A 197 ezer train/val jelöltből 4748 (2,4%) esik ki, zömmel a forrás saját splitjei közti közeli duplikátumok: a
      HuCOLA minimális párjai, a HuWNLI közös premisszái, a MultiEURLEX és a TED sablonszövegei. A NerKor jogi
      alkorpusza és a MultiEURLEX között kevés valódi átfedés van.
    - Az első változat a kérdést és az opciókat is mérte; a fix opciólisták (törvénycímek, EuroVoc- és CPV-nevek)
      ettől hamis átfedést adtak. Most csak az állapotszöveg számít.
  - **Szinonimaszűrés** (`szinonim03.py`, 4.3): a szövegből vett disztraktorú kilenc családban (HuRC, MILQA,
    MultiEURLEX, TED, NJT ×3, Wikipédia ×2) minden nem-gold opcióra két bíráló (Mistral Small 4, Llama-3.3) dönt.
    Ha bármelyik szerint helyes lehet, az opció kikerül; ha két opciónál kevesebb marad, az item kiesik. 16 891 item,
    72 890 pár; a célhalmaz a kvóta 1,3-szorosa, hogy a kiesők pótlása is szűrt itemből jöjjön.
  - **Szintetikus családok** (`szint03.py`, vezénylő: `f1_szint.sh`):
    - **Lépések:** a terv (szándékolt címke, opció-részhalmaz, X, szcenárió) determinisztikus, a generátor csak a
      szöveget írja; utána független visszacímkézés másik modellcsaláddal, és csak az egyező, legalább 0,6 bizalmú
      item marad. Családonként 1300 terv, a keverő kvótája 1000.
    - **A Mistral-próba (6 + 6 item) után javítva:** a szögletes zárójeles helykitöltők tiltva; az ellentényes
      változatnál a generátor egy esetben a kérdést és a választ adta vissza a szöveg helyett, ezért pontosabb utasítás
      és őr került be (a kérdés nem lehet benne, a hossz az eredeti 70–130%-a).
    - **A teljes futás** 18:04-kor indult, menet közben kétszer újraindítva (a generálás és a bírálat folytatható):
      - a Mistral NVFP4 a Sparkon 16 szekvenciával ~140, 48-cal ~225 token/s-ot ad (a KV-cache 1% alatt). A
        levéltriage-ből 85 sikeres levélből 67-ben szögletes zárójeles helykitöltő maradt, a tiltás ellenére. Ezért a
        levéltriage generátora a Gemma lett (ellenőrző: Qwen), a prompt konkrét kitalált szereplőket kap, a
        helykitöltős, az igen/nemmel kezdődő és a nem JSON-kimenet újragenerálódik; a Mistral levelei archiválva;
      - a szinonim-bírálat Mistrallal ~9 pár/s. A Llama a 72 890 párra 4–6 órát adott volna, ezért a második
        bíráló a Gemma (a P2-ben amúgy is fut). Az elv változatlan: két független, nem-Qwen bíráló.
    - **Végleges sorrend** (19:00-tól): P1 Mistral (RAG-generálás, szinonim-bírálat), P2 Gemma (entitásegyezés,
      hivatali ügytípus, levéltriage generálása; a RAG ellenőrzése; szinonim-bírálat), P3 Qwen (dokumentumtípus,
      klauzula, válaszbírálat gondolkodó generálása; a Gemma-családok ellenőrzése), P4 Mistral (a Qwen-családok
      ellenőrzése). Várható vége: kb. 01:00.
    - **Entitásegyezés, újraindítva 21:36-kor:** a Gemma első 240 iteme hiba nélkül generálódott, de a rekordokat
      JSON-objektumként adta, és szinte mindegyik ugyanazt a kitalált szereplőt hozta. Javítás: a terv itemenként
      saját alapszereplőt kap (személy, cég, cím, telefon), az objektumrekordot a feldolgozó szöveggé alakítja; a 240
      item archiválva (`elvetett_entitas_v1`). Az újraindítás után az első 91 listás itemben 79 különböző alapszereplő
      van. A listák ~6%-ában a cél pontos másolata kétszer szerepel; ezt a vak ellenőrzés szűri.
    - **P2 (Gemma), 21:36–23:42:** entitásegyezés, hivatali ügytípus és levéltriage 1300–1300 terv, a generálási
      hibaarány 2,2%, 0,2% és 0,5%. A levéltriage-ben egyetlen szögletes zárójeles helykitöltő sincs (a Mistralnál
      85-ből 67 volt). A szinonim-bírálat Gemmával ~31 pár/s, a 72 890 párból 11 253 (15%) P(igen) ≥ 0,5.
    - **P3 (Qwen), a gondolkodó generálás elakadt (23:50–06:20):** 48 szekvenciával a Qwen összesen ~245 token/s-ot
      adott (~5/s szekvenciánként: a MoE ekkora batch-nél lépésenként már szinte minden expertet olvas, a Spark
      memória-sávszélessége a korlát). A legfeljebb 6000 tokenes gondolkodó válaszok ~20 percig tartanak, a kliens
      900 s után feladta és újrakérte őket, így 6,5 óra alatt 118 kérés végzett, 4 item került a fájlba (archiválva:
      `elvetett_qwen_gondolkodo`). A gondolkodó módot a családspecifikáció írta elő, nem döntés. 06:23-tól a Qwen
      gondolkodás nélkül generált, 192 párhuzamos kéréssel ~520 token/s-mal (82% KV). 06:41-kor Dani kérdésére
      leállítva (10. pont 11.), 5 item archiválva (`elvetett_qwen_nemgondolkodo`).
    - **Következmény az F2-re:** a Qwen gondolkodó módja tanárjelölt (n = 8 minta, 4.4) és a gépi zajbecslés egyik
      kiolvasása (4.2). Ez ugyanígy drága lesz: a mintaszámot és a minta méretét a futás előtt a mért sebességhez
      kell igazítani. (Megtörtént: csökkentett minta, 21:20.)
    - **Új sorrend (06:50-től):** P3 Mistral (az entitásegyezés, a hivatali ügytípus és a levéltriage
      ellenőrzése), P4 Muse-Glimmer-30B (dokumentumtípus, klauzula, válaszbírálat generálása; BF16-ból dinamikus
      FP8, `reasoning_strength: low`, a vLLM `muse_glimmer` reasoning-parserével), P5 Gemma (a Muse-családok
      ellenőrzése). A P4 előtt próba (családonként 6 item: magyar minőség, helykitöltők, sebesség); ha elbukik,
      a Gemma generál.
    - **Őr:** a vezénylők eddig minden futó konténerre leálltak, a Muse letöltő konténerére is. Mostantól csak a
      GPU-t használó konténer állítja meg őket (`HostConfig.DeviceRequests`).
    - **P3 (Mistral, 06:51–07:08):** az entitásegyezés, a hivatali ügytípus és a levéltriage ellenőrzése. 96
      párhuzamos kéréssel családonként ~3 perc (éjjel 48-cal a szinonim-bírálat ~9 pár/s volt).
    - **Muse-próba (07:08–07:22):** a boot 9 perc (dinamikus FP8), családonként 6 item, hiba nélkül; 6
      szekvenciával ~7–8 token/s szekvenciánként.
      - A magyar természetes és hivatalos, kitalált, életszerű nevekkel. Nincs helykitöltő, és a gondolkodás sem
        szivárog ki: a parser leválasztja.
      - Javítva: a „nem” címkéjű klauzulák közül kettő szó szerint kimondta a választ („nem keletkeztet egyoldalú
        jogot”). Ez lexikai shortcut, ezért a noul-prompt mostantól kifejezetten tiltja a kérdezett tulajdonság
        kimondását vagy tagadását. A Gemma-családok ezzel a változtatással nem generálódnak újra.
      - Szándékos és változatlan: az X-es dokumentum formájában üzleti irat, tartalmában más (pl. levélfejléc alatt
        recept). Ez a spec nehéz „egyik sem” esete; ha kétértelmű, a Gemma-ellenőrzés kiszűri.
      - A próba itemei archiválva (`proba/muse`); a teljes P4–P5 07:23-kor indult, 128 párhuzamos kéréssel. Az
        éjszakai lánc (`f2_ejszaka.sh`) a `DONE-P4_P5-1300` jelölőre vár.
    - **P4–P5 (07:23–08:50):** a Muse családonként 1300 tervet 12–26 perc alatt generált (128 kéréssel ~430
      token/s), generálási hiba 0–0,1%. A Gemma-ellenőrzés családonként ~2 perc.
  - **Lezárás és F2 első kiolvasásai (a lánc, 08:52-től):**
    - **Szintetikus családok** (megtartott / generált item, az ellenőrző döntése után): levéltriage 901/1524 (59%),
      entitásegyezés 690/1399 (49%), hivatali ügytípus 961/1501 (64%), dokumentumtípus 1221/1517 (80%),
      klauzula 1350/1517 (89%), RAG-relevancia 783/1376 (57%), válaszbírálat 1005/1300 (77%).
    - **Pool:** train 30 589, val 3095, 209 család; angol 26,2%, konstrukciós 11,7%, szintetikus 17,6%, X 7,9%
      (gold-drop 49%, természetes 33%, out-of-scope 18%, hiányzó feltétel 0%).
    - **Szinonimaszűrés** (Mistral ∪ Gemma, P(igen) ≥ 0,5): a disztraktorok kivett aránya családonként 20%
      (TED) és 71% (Wikipédia-szakaszcím) között; 4027 item kiesett, 9062-ből opció került ki, 3802 érintetlen.
    - **Összesítő:** 233 308 item, 216 család; sémahiba, ismétlődő id és több splitben lévő group_id 0. A
      szivárgás-audit 4748 jelöltet zár ki (a szintetikusokból egyet sem). Befagyasztva 31 réteg (+7 szintetikus
      teszt-ID, 748 item), az ellenőrzés 0 eltérés.
    - **Kiolvasási sebesség** (k = 4, a val 12 380 kiolvasása): Gemma 31,6/s, Mistral 9,0/s, Qwen 15,7/s; az
      eval-rétegeken a Qwen ~13/s (az előtöltés ~6500 token/s-on számításkorlátos). Hiba 0.
  - **Két hiba a szintetikus X-ben (11:10, javítás Dani jóváhagyásával: „Mehet”):**
    - **A Mistral mint ellenőrző szinte soha nem választ X-et.** A Gemma-családok X-itemjeinek csak 14–23%-a ment
      át (az X-valószínűség mediánja 0,03–0,08), a Gemma-ellenőrzésű Muse-családokban 86–99%. A val forrás-goldján,
      a 0-s permutáción, az ellenőrző szabályával (top-1 = gold, bizalom ≥ 0,6; saját mérőszám: **átmenő arány**):

      | ellenőrző | nem-X | X | gold-drop | természetes | out-of-scope | címketömeg (medián) |
      |---|---|---|---|---|---|---|
      | Gemma 4 | 0,822 | 0,868 | 0,931 | 0,889 | 0,681 | 1,000 |
      | Qwen3.6 (bázis, csak összevetés) | 0,804 | 0,745 | 0,767 | 0,764 | 0,660 | 0,998 |
      | Mistral Small 4 | 0,597 | 0,379 | 0,466 | 0,333 | 0,234 | 0,973 |

      Reggel a Mistral ellenőrzői kiosztásakor ezt nem vettem figyelembe (a 00-ban mért X-gyengesége ismert volt).
      A RAG-relevancia elutasított „természetes X” itemjei viszont tényleg megválaszolhatók voltak (szúrópróba): ott a
      Mistral generátor hibázott, és a Gemma-ellenőrző jól szűrt.
    - **A „hiányzó feltétel” X-típus a tervezőből kimaradt** (F0-hiba): a spec a levéltriage-ben és a hivatali
      ügytípusban kéri, de a `plan()` minden X-et out-of-scope-nak jelölt.
    - **Javítás** (`f1_javitas.sh`, a lánc a Qwen eval-kiolvasása után megáll):
      - **P7 (Gemma):** a „hiányzó feltétel” pótlása, családonként 130 terv (seq 1300–1429, saját véletlenforrással; a
        korábbi 2 × 1300 terv bájtra változatlan, ellenőrizve).
      - **P8 (Muse):** ellenőrző-validálás a val-on, utána a három Gemma-család minden itemjének ellenőrzése. A Muse
        sablonja gondolkodással kezd, ezért a kiolvasás a válaszcsatornát kényszeríti (`kiolvaso03 --prefix ' to=user<|message|>'`;
        a sablon a gondolkodás nélküli korábbi válaszokat is így írja). A címkék egytokenesek, a renderelés ellenőrizve.
      - **Döntési szabály (a mérés előtt rögzítve, `ellenorzo_valid03.py`):** a Muse ellenőriz, ha a címketömeg
        mediánja ≥ 0,9, az X átmenő aránya ≥ 0,5, és a nem-X átmenő aránya legfeljebb 10 ponttal marad el a
        Gemmáétól. Ha nem, a tartalék a Llama (10. pont 1.: szűrhet, és az ellenőrzés szűrés, a címke a tervből jön).
      - **Eredmény (13:25–14:03):** a P7 a 2 × 130 „hiányzó feltétel” tervet 0,4% és 0,1% generálási hibával adta.
        **A Muse a validáláson elbukott** (átmenő arány a val-on, 0-s permutáció): címketömeg-medián 0,871 (< 0,9),
        nem-X 0,527 (Gemma 0,822: −29,5 pont), X 0,719. X-hajlamos is: X-gold itemen 90%-ban X-et választ, nem-X-en
        csak 69%-ban találja el az opciót; ellenőrzőként a rossz X-itemeket is átengedné. Ezért a tartalék, a
        Llama-3.3-70B kerül sorra ugyanezzel a szabállyal (P9, 14:05-től; a három család exportált itemjei a P8-ból).
      - **A Llama is elbukott (14:05–15:03), egy feltételen:** címketömeg 1,000, nem-X 0,795 (−2,7 pont), de X
        0,451 (< 0,5; gold-drop 0,353). A három családon tájékoztatásul: out-of-scope X 39–63%, nem-X 70–85% maradt
        volna, de az entitásegyezés gold-drop X-ét 100%-ban átengedte (X-hajlam ezen a családon), a „hiányzó
        feltétel” itemekből 5%-ot. A szabályt utólag nem lazítottuk.
      - **Dani döntése (15:20): a Muse generálja újra a három családot, a Gemma ellenőrzi** (`f1_javitas2.sh`: P10
        Muse, levéltriage és hivatali ügytípus 1430, entitásegyezés 1300 terv; P11 Gemma). A Gemma-generálás és
        minden hozzá tartozó ellenőrzés archiválva (`elvetett_gemma_generalas`). Indult 15:25-kor.
      - **Utána:** a lezárás újra (`f1_lezaras2.sh`, `ELLENORZO=gemma`); a három család szintetikus teszt-ID-rétege elemzés előtt újrafagyasztva
        (`befagyaszt03 ujrafagyaszt`, csak szintetikus réteg, indokkal, a régi hash archiválva); a lánc folytatása
        (Qwen: az új val/eval-itemek és a train; Gemma: val és train egy bootban). A Mistral val-kiolvasása az új
        itemekre nem fut újra (egy Mistral-boot): összesítve 18 ponttal a bázis alatt van (top-1 0,668 vs. 0,844), a
        kapuja a meglévő val-kiolvasáson fut, az új szintetikus itemek nélkül.
      - **Eredmény (15:25–17:40):** a Muse az entitásegyezést 42 perc alatt generálta (itemenként ~2000 token, a
        „low” gondolkodás itt hosszú), a levéltriage-et és a hivatali ügytípust 30–35 perc alatt; generálási hiba
        0–0,6%. Az entitás-listákban nincs a keresett rekord pontos másolata (a Gemmánál 6% volt). Gemma-ellenőrzés
        után megtartva: levéltriage 1218/1651 (74%, X 94; korábban Mistral-ellenőrzéssel 59%, X 18), entitásegyezés
        1021/1432 (71%, X 196; korábban 49%, X 47), hivatali ügytípus 1388/1633 (85%, X 271; korábban 64%, X 26).
      - **A „hiányzó feltétel” X:** a hivatali ügytípusban 130-ból 110 maradt, a levéltriage-ben csak 24 (a Gemma a
        homályos levelek többségét egy opcióhoz sorolja). A train-poolban 101 item, az X-ek 3,7%-a: a típus jelen
        van, de vékony; ha a kitartott rétegeken a típusonkénti X-fedés ezt igényli, olcsón pótolható.
      - **Második lezárás (17:39):** pool train 31 374, val 3122; angol 25,5%, konstrukciós 11,4%, szintetikus 19,7%,
        X 8,8% (gold-drop 47%, természetes 29%, out-of-scope 21%, hiányzó feltétel 4%: mind a négy típus megvan,
        egyik sem több 50%-nál). Összesítő: 234 383 item, sémahiba 0. A három szintetikus teszt-ID-réteg
        újrafagyasztva (a régi hash az `archiv` listában, indokkal), az ellenőrzés 31 rétegen 0 eltérés. A lánc
        folytatódott: a Qwen az új val- (112) és eval-itemeket (144) elolvasta, a train-en fut.
  - **Éjszakai lánc a Sparkon** (`kor03/eszkozok/f2_ejszaka.sh`, Dani, 21:45: „fűzzél fel még feladatokat”; a laptop
    éjjel ki van kapcsolva). Megvárja az F1SZ végét, aztán:
    - **Z, az F1 lezárása** a laptopos `f1_zaras.sh` lépéseivel, a Sparkon (az F0-adat és a befagyasztási manifest
      átmásolva, a 24 réteg hash-e ott is egyezik): `szint03 final`, `szinonim03 dontes`, szivárgás-audit, keverő,
      befagyasztás a szintetikus rétegekkel és ellenőrzés, összesítő, az F2-itemlisták (`f2_itemek03.py`: val 2576,
      eval 45 117 a 00/01 HO-tesztjeivel, train 26 470 a keverő előtti állapotban).
    - **F2 első kiolvasásai**, mind k = 4 permutációval (`kiolvaso03.py`): Gemma a val-on, Mistral a val-on
      (tanárkapu), Qwen3.6 L0 a val-on, az eval-rétegeken és a train-en, végül Gemma a train-en.
    - A Qwen-szerver LORA=1-gyel fut, mint a 00/01 L0-ja: az `--enable-lora` MoE-kernelt vált, ezért a LoRA nélküli
      szerver eloszlásai a későbbi G3-karokkal nem lennének összevethetők.
    - **Előellenőrzés** (tokenizálás, szerver nélkül): minden itemtípus renderelhető; medián ~330 token, a
      8192-es korlát fölött egyetlen train-item van. A kiolvasó egy hibás kérésnél nem áll le: a hiba külön fájlba
      megy, és ha 5% fölötti, a lépés hibásnak számít. A kiolvasás hibája a láncot nem állítja meg, a lezárásé igen.

  - **Az F2 első kiolvasásai teljesek (21:13), k = 4 permutációval:**
    - Qwen3.6 L0 (LORA=1-es szerver, adapter nélkül): val 3122/3122, eval 45 965/45 965 (a 00/01 HO-tesztjeivel),
      train 31 373/31 374;
    - Gemma 4: val 3122/3122, train 31 373/31 374;
    - Mistral Small 4: val 3010/3122 (a második lezárás 112 új szintetikus val-itemje nélkül, szándékosan);
    - ellenőrző-validálás (0-s permutáció): Muse és Llama a val-on.
    - Az egyetlen hiányzó train-item (`jogi.njt_cim:2014-88-00-00:4. §:(1):2`, ~10,8 ezer token) a 8192-es
      kontextusba nem fér (HTTP 400); az MVP-válogatásból kimarad.
    - Train-kiolvasás: Qwen 7867 s (~16/s), Gemma 3885 s (~32/s). Hiba csak a fenti item.
  - **A Qwen gondolkodó kiolvasásai, csökkentett mintán** (Dani, 21:20: „a 20 óra Spark túl sok, elfogadom a
    javaslatod”; `f2_minta03.py`, `f2_gondolkodo.sh`, 21:33-tól):
    - **tanárkapu-minta:** 600 val-item, a forrás- és konstrukciós goldú csoportokból 75–75 (a szintetikus nélkül);
      itemenként 4 gondolkodó minta, mintánként más permutációval (a 4 minta egyben a permutációs átlag);
    - **gépi zajbecslés:** 3215 train-item a 11 magyar forrás-gold forrásból (HuCB, HuRTE, HuWNLI, HuCoPA, HuRC,
      MILQA, HuCOLA, HuSST, NerKor, MultiEURLEX, TED), forrásonként 300 (a HuCB-ből mind a 215), 1 minta. A
      második olvasó a Gemma (a train-en kész). A konstrukciós (NJT, Wikipédia), az angol és a szintetikus források
      a keretbe nem fértek; a szintetikusoké amúgy is részben körkörös lenne (a Gemma szűrte őket).
    - Mintavétel a Qwen ajánlásával (temperature 0,6, top-p 0,95, top-k 20), legfeljebb 4096 token, egyórás
      kliens-időkorlát, 128 párhuzamos kérés, LORA=0. A címke a gondolkodás utáni válaszból: egy betű, vagy betű +
      zárójel / pont; a magyar „A” névelő nem címke; több különböző említés esetén hiányzó válasz (13 egységteszt).
    - A 4 mintás empirikus eloszlás bizalma negyedekben kvantált, ezért a kapu ECE-feltétele a gondolkodó tanáron durva
      mérőszám (tájékoztató); a kapu elbírálása reggel, Dani döntésével.
  - **F2-elemzés, előzetes** (`f2_elemzes03.py`, a gondolkodó kiolvasások nélkül; a 00 `elemzes.py` függvényeivel):
    - **L1★ = 4-permutációs átlag** (T = 1,43): a val-on lefedettség@95 0,669 (@90 0,821), precizitás 0,958, AURC
      0,0245, ECE 0,026, top-1 0,848, X-fedés 0,808. τ@95 = 0,716.
    - **Rétegek a val-τ-val (leíró):** HO-termék lef 0,651, precizitás 0,963; HO-routing 0,616 / 0,930 (a határon);
      HO-új (KIE) 0,566 / 0,940, top-1 0,722, X-fedés 0,354 (a JPT-lelet szerint is ez a bázis gyenge pontja);
      teszt-ID 0,644 / 0,891 (bukás); külső eval 0,707 / 0,871 (bukás). A val-τ itt sem visz át mindenhová (H3).
    - **Családválasztás:** 209 train-családból 12 plafon közeli (a dokumentumtípus, a klauzula, a levéltriage, a
      MILQA és 8 angol), ezek legfeljebb a train 5%-át adják.
    - **Tanárkapu (csoportonként, forrás- és konstrukciós gold):** sem a Gemma, sem a Mistral nem megy át egyik
      csoportban sem. A Gemma top-1-e csak az angol gerincen (0,783 vs. 0,765) és az entitáson (0,875 = 0,875) éri el
      az L1★-et; a kalibrációja gyenge (az illesztett temperature 5,0, a csoportos ECE így is 0,06–0,16). A Mistral
      minden csoportban 7–21 ponttal az L1★ alatt van. A Qwen gondolkodó tanár a Spark-futás után kerül be.
  - **Önellenőrzés a gondolkodó futás alatt (22:50, Dani kérésére):** a bemenetek és a kiolvasó a két gépen azonosak
    (md5), a hibafájl üres. Javítva: a zajbecslésben a Gemma train-kiolvasása a val-on illesztett temperature-t kapja
    (eddig a vizsgált zaj-itemeken illesztett volna); a napló három elcsúszott bekezdése a helyére került. Előzetes, 960
    minta (240 item, 4 csoport): címke 951/960 (9 a 4096 tokenes korlátnál), 4/4 egyezés 199 itemen, többség = gold
    0,792; csoportonként top-1 angol 0,841, entitás 0,903, jogi 0,591, konstrukciós 0,700; a nem-X itemek 14%-án X-et
    mond (X-hajlam). Ütem ~19 minta/perc: a val vége kb. 00:00, a zaj kb. 02:50. A Spark gyökerében maradt
    `FAILED-F1B` a 10-04-i kézi leállítás maradványa, egyik lánc sem figyeli.
- **2026-10-09 — F0 folytatás: KIE/validáció HO-új-család, TED, Wikipédia, szintetikus specifikáció.**
  - **KIE/validáció** (3.4; `kie03.py`, `test_kie03.py`, spec: `kor03/spec/kie_validacio.yaml`): 2400 item, `ho-uj`
    split, ebből 200 a H3 kalibrációs mintája. Három család, nyolc kérdéstípus; X 9–18% (természetes és hiányzó
    feltétel). A teszt a renderelt szövegből, a generátor függvényei nélkül számolja újra a goldot: hibás 0,
    determinisztikus; a mutációs próbán mind a 2400 elrontott goldot elkapja.
    - Javítva generálás közben: a hibás tételsor nettó értéke nem volt 10-re kerek, a helyesek igen; ez az utolsó
      számjegyből elárulta volna a hibás sort. Az eltérés most a forrásérték lépésközével kerekített.
  - **TED** (`ted03.py`): a TED keresési API-n (v3, bejelentkezés nélkül), kérésenként 2 s szünettel; 18 673 magyar
    hirdetmény (2025-01-01 – 2026-09-30), ebből 7931 ajánlatkérés. A `kozbeszerzes.ted_cpv` család 4896 item.
    - **Shortcut:** a `notice-title` a fő CPV-kód nevét tartalmazza („Magyarország – Vasútépítés – …”), ezért az
      állapot csak az eljárás címe és az első rész leírása; a szövegbeli 8 jegyű CPV-kódok kitakarva.
    - **PII:** e-mail, telefonszám vagy kapcsolattartóra utaló szó esetén a hirdetmény kimarad (539); a maradékban a
      „dr.” és a kétszavas nagybetűs nevek intézmény- és utcanevek (Semmelweis Egyetem, Dr. Kenessey Albert Kórház).
    - **Duplikátum:** 2428 ajánlatkérés leírása szó szerint ismétlődik (részek, újraközlés); csak a legkorábbi marad.
    - **HO-forrás:** a szabály szerint (a gyakorisági sorrendben a 10.) a 38-as főcsoport (laboratóriumi, optikai és
      precíziós felszerelések), 166 item; a neve a train-ben opcióként sem fordul elő. A 33-as (orvosi felszerelések)
      a train-ben van és rokon, ezért a réteg leíró (4.6).
  - **Wikipédia** (`adapter_wiki.py`): szakaszcím- és következőmondat-választás, 6000–6000 item, 15% gold-drop X. A
    mondatbontó a rövidítéseknél és a bibliográfiai listáknál töredékeket adott; ezek könnyű, kilógó disztraktorok
    lettek volna, ezért a mondatszűrő szigorodott (legalább hat szó, belül nincs pont, a szavak legalább 40%-a
    kisbetűs). A MILQA-szócikkek kimaradnak (5 találat a shardban).
  - **Angol külső eval** (`adapter_eval_en.py`): LocalLLaMA-teszt 1200 kérdés (a score kimaradt; 403 kétértelmű, mert a
    forráseloszlás csúcsa 0,6 alatt van), fastino 1900 (az egycímkés feladatok).
  - **Szintetikus családok specifikációja** (3.5; `kor03/spec/szintetikus_csaladok.yaml`): hét család (levéltriage,
    dokumentumtípus, szerződésklauzula, entitásegyezés, RAG-relevancia, válaszbírálat, hivatali ügytípus),
    kérdésekkel, opciókkal, X-típusokkal, generátorral és független ellenőrzővel, és a kitartott csoportoktól tiltott
    kérdésformákkal (pl. „melyik hivatal illetékes”: routing-rokon). A generálás az F1-ben fut.
  - **Összesítő:** 226 397 item, 209 család; sémahiba, ismétlődő id és több splitbe lógó csoport nincs. Az eszközök a
    spark-devre szinkronizálva.
  - **Az F0-ból kimaradt:** a KN/VTSZ (opcionális, a HO-termék nélküle is teljes). **Következik az F1:** a szintetikus
    családok generálása, a szinonimaszűrés (HuRC, MultiEURLEX, NJT és Wikipédia gold-drop), a gépi zajbecslés, a
    szivárgás-audit (bge-m3 + MinHash, a NerKor–MultiEURLEX és a NerKor–Wikipédia átfedéssel), a shortcut-baseline,
    a keverő és a befagyasztás.

- **2026-10-09 — v0.3: Dani döntései; F0: letöltések, forrásadapterek, NJT, angol gerinc.**
  - **Döntések** (10. pont, 5–8.): angol gerinc a train 25%-a; HO-új-család csak a KIE/validáció; **nincs emberi
    átnézés a 03-ban**; a Nemzeti Jogszabálytár közkincsként használható. A runbook ennek megfelelően átírva: gépi
    zajbecslés (4.2), a tanár–gold ellentmondás kimarad (4.1), a megerősítő állítások az emberileg átnézett 00/01
    HO-rétegekre és a konstrukciós HO-új-családra szűkülnek (4.6), a H3 kalibrációs mintája a meglévő átnézésből jön.
  - **Letöltve** (`letolt03.py`, rögzített commit, fájlonkénti sha256): MultiEURLEX hu (a parquet-ág), Belebele és
    SIB-200 hun, NerKor (GitHub, commit `7c9c5b5f`), a Wikipédia 20231101.hu egy shardja, a tasksource `full`
    (1,6 GB), a procedural 9 feladata, az Open-Jev 7 konfigurációja, a LocalLLaMA-teszt és a fastino. A tasksource
    HEAD-je napközben elmozdult (`94c2ebb` → `23f4e15`); a rögzített commit maradt.
  - **NJT** (`njt03.py`): 52 törvény (adó, számvitel, Ptk., Mt., közigazgatás, ágazati), kérésenként 3 s szünettel,
    a robots.txt szerint engedett úton; a nyers HTML gzip-pel, sha256-tal, hatálydátummal. A feldolgozás a
    jhId-horgonyokból 32 654 bekezdésszintű egységet ad (§, bekezdés, rész, fejezet, alcím, tagolócím).
  - **Új adapterek, sémahiba 0** (`adapter_qa.py`, `adapter_egyeb.py`, `adapter_njt.py`, `adapter_angol.py`;
    összesítő: `osszesito03.py` → `kor03/adat/f0/osszesito03.md`). Összesen 204 001 item, 201 család (ebből 170 a
    tasksource-forrásoké), ismétlődő id és több splitbe lógó group_id nélkül:

    | család | n | X | megjegyzés |
    |---|---|---|---|
    | qa.milqa | 14 604 | 37%, természetes | a gold a rövid válasz, a disztraktorok ugyanannak a bekezdésnek a többi válasza; eldöntendő kérdés noul-ként |
    | qa.hurc | 59 951 | 20%, gold-drop | cloze entitásválasztás; a jelöltek a szöveg névkifejezései |
    | jogi.multieurlex | 32 664 | 15%, gold-drop | EuroVoc 1. szint, 21 terület |
    | jogi.njt_torveny / _fejezet / _cim | 3119 / 2700 / 3051 | 15%, gold-drop | konstrukciós gold a törvényszerkezetből |
    | entitas.nerkor | 41 974 | 7%, hatókörön kívüli | névtípus; az X egy köznév |
    | qa.belebele, level.sib200 | 900, 1004 | — | csak külső eval |
    | angol gerinc | 21 507 | ~1% | tasksource 9747 (170 forrás), procedural 7560, Open-Jev 4200; 1734 puha (szavazat- vagy valószínűségcél) |

  - **Leletek és javítások:**
    - **HuRC:** a MASK a mondatbeli, ragozott alak, ezért a jelöltek is ragozottak. Csak az az item maradt, ahol a
      gold szó szerint szerepel a szövegben; különben a „szövegben nem szereplő opció a jó” shortcut lenne (10 003
      kimaradt). A gold-drop X-ből a heurisztika kiszűri a gold változatait (közös tő, betűszó, a gold melletti
      névrész, elírás), de a betűszó-összetételt (PTE ↔ Pécsi Tudományegyetem) nem: ezeket az F1 modelles
      szinonimaszűrése (4.3) fogja meg. Egy cikk a forrás train- és val-splitjében is szerepelt; a train-oldali
      példány kimaradt.
    - **MILQA:** 4023 kérdés kimaradt, mert a jelölt szövegrészlet nem maga a válasz („Más a pontos válasz”,
      „Aritmetika”); az X-arány 37%, a 10–30%-os sávot a keverő állítja be.
    - **A kártyák alapján az angol gerinc szűkült** (3.3): a tasksource `default` helyett `full`; a helmo kizárva
      (generátormodell írta a címkéket); az UltraFeedback és a WildGuardMix kizárva (GPT-4 címkék); a COPA/XCOPA és a
      WinoWhy kizárva (a HuCoPA, illetve a HuWNLI forrásai); a KIE-rokon procedural- és Open-Jev-feladatok kizárva,
      hogy a HO-új-család kitartott maradjon.
    - **A Wikipédia licence** a HF-pillanatképen CC-BY-SA-3.0 / GFDL (a runbook 4.0-t írt); javítva.
  - **Hátra van (F0):** a TED-letöltés és a PII-szűrő; a KIE/validáció HO-új-család konstrukciója (családspecifikáció
    és egységteszt); a szintetikus családok specifikációi (YAML); a Wikipédiából a konstrukciós családok; a LocalLLaMA-
    és a fastino-adapter (csak eval); a KN/VTSZ.

- **2026-10-09 — F0 folytatás: Gemma 4 smoke, HuLU-adapterek, HuBoolQ kizárva.**
  - **Gemma 4 26B-A4B-it smoke** (F2-ből előre hozva, Dani jóváhagyásával; `kor03/eszkozok/f2g_smoke.sh`,
    `tanar_smoke.py`; eredmény: `kor03/eredmenyek/F2g/smoke.json`):
    - **Boot:** vLLM v0.30.0 (`sha256:8a69ffad…`), BF16, `--gpu-memory-utilization 0.6`, 511 s alatt; utána
      ~80 GB foglalt, 41 GB szabad.
    - **Címkék:** A–J és X egytokenesek a Gemma tokenizerében. A chat-sablon ismeri az `enable_thinking`-et:
      kikapcsolva üres gondolkodási csatorna kerül a válasz elé.
    - **Kiolvasás:** a címketömeg medián ~1,0 (minimum 0,9987), a mintavett token mindig címke, ~0,19 s/döntés.
    - **Irányjelző pontosság** a natív 00/01 prompttal, perm 0, kalibráció nélkül, 120–120 val-itemen:

      | | top-1 | nem-X | X-felismerés |
      |---|---|---|---|
      | 00 val | 0,75 | 0,91 | 0,38 (n = 29) |
      | 01 val | 0,91 | 0,92 | 0,88 (n = 34) |

      - Ez nem a tanárkapu (4.4): ahhoz temperature-fit, permutáció-átlag és zajauditált gold kell.
      - Összevetés a 00-feladaton: a Llama-3.3 X-recallja 4–10%, a Mistral Small 4-é 1–3% volt (0. pont), a Qwen
        alap X-fedése 0,43. A Gemma tehát X-ben a két korábbi bírálónál jóval erősebb tanárjelölt.
      - A 00 típusú X-en a 0,5-ös típusonkénti kapu alatt van. A termék-csoport kitartott, ott tanár nem kell.
  - **HuBoolQ kizárva.** A kártya szerint Google Translate készítette, utána GPT-4o mini írta át. A 3.6 pont
    csak Apache-2.0 fordítót enged, és zárt modell kimenete nem lehet a láncban; a letöltött példány törölve.
    A többi HuLU-készlet emberi fordítás (HuRTE, HuWNLI, HuCoPA, HuSST) vagy eredetileg magyar (HuCOLA, HuCB),
    a HuRC és a MILQA eredetileg magyar.
  - **HuLU-adapterek** (`kor03/eszkozok/adapter_hulu.py` → `kor03/adat/f0/*.jsonl`, sémahiba 0):
    - noul: HuRTE (2375), HuWNLI (622), HuCOLA (8184); noul + természetes X: HuCB (353, 41% X);
    - choice: HuSST (10 493, három hangvétel), HuCoPA (500, ok/következmény);
    - splitek: a forrás val-ja a teszt-ID, a 03 val-ja a forrás-train 10%-a (item-hash), a forrás-teszt
      nincs használva;
    - **lelet:** a HuCoPA fájljában a címke 0/1 (a kártya 1/2-t ír); példákon ellenőrizve, a 0 az első
      alternatíva.
    - Hátra van: a HuRC (jelölt-entitások kellenek a cloze-hoz) és a MILQA (válaszrészlet-jelöltek). Mindkettő
      jelöltgenerálást igényel, az F1 elején.

- **2026-10-09 — F0 indul (a 01 lezárása után, Dani: „menjünk tovább a 03-al”).**
  - **Közös séma és promptkeret** (`kor03/eszkozok/kozos03.py`, teszt: `test_kozos03.py`, a `kor01/.venv`-vel):
    - séma + validálás (a 2. és az 5. pont mezői; a kitartott csoport csak a saját HO-splitjében lehet);
    - natív keret a 00/01 itemekre (`common.messages_for`) és generikus keret (Állapot / Kérdés / Opciók, X utolsó);
    - a 00/01 kiértékelő itemek átalakítói: X(a) és X(a)-természetes → gold-drop, X(b) → out-of-scope; a 01-ben a
      BFCL irrelevancia, a When2Call `cannot_answer` és a csevegés → out-of-scope, a gold-drop az.
    - **A teszt:**
      - 20 184 item, sémahiba 0;
      - a natív keret 80 736 esetben azonos az eredeti promptépítővel;
      - a Qwen3.6-tokenszám mind a 80 736 kiolvasási rekordon egyezik a mért `n_prompt_tokens`-szel (00 F4, 00b,
        01 F4). Ez a mért prompttal való bájtszintű egyezés bizonyítéka.
      - **Kivétel:** 56 rekord (14 thai vagy dévanágari kérés a 01-ben). A laptop `tokenizers` 0.23.2-je ezek
        kombináló jeleit másképp darabolja, mint a mérőkonténer; a prompt szövege ott is azonos. A magyar családokat
        nem érinti, de a tanár-kiolvasásnál a tokenizálás a mérőgépen történjen.
    - A runbookban javítva: a When2Call `cannot_answer` a 3. X-típus, nem a 4. (2. pont).
  - **Forráslista** (`kor03/eszkozok/forrasok03.py` → `kor03/forras/forrasok03.{json,md}`):
    - 26 forrás; a HF-esek licence a HF-API-ból, commitra rögzítve.
    - Kézi megállapítások:
      - a HuRTE és a HuCommitmentBank a kártya szövege szerint CC-BY-SA-4.0 (metaadat-címke nincs);
      - a HuSST HF-metaadata BSD-2-Clause, a GitHub-repóé CC-BY-SA-4.0: a szigorúbbat követjük.
    - Nyitott: a Nemzeti Jogszabálytár portálfeltételei; a TED, a KN/VTSZ és a NerKor kézi ellenőrzése.
  - **Letöltve** (`letolt03.py`, rögzített commit, fájlonkénti sha256: `kor03/forras/letoltes03.json`): a HuLU
    nyolc készlete és a MILQA train-je (a test a 3.1 szerint tilos, nem töltöttük le), 256 MB.
  - **Első leletek a forrásokból:**
    - a HuCOLA, HuCoPA, HuCB, HuRTE és HuSST tesztcímkéi rejtettek (a val a teszt), a HuWNLI-é nem;
    - **a HuSST val-ja szinte pozitív nélküli** (33/1165 pozitív, a trainben 3720/9328): ha a val a teszt, ott erős
      eloszlásváltás van, ezt az F1 shortcut- és rétegauditja kezelje;
    - a HuCB-ben a `neutral` a „nem eldönthető” → X (természetes, 2. típus).
  - **Gemma 4 (F2-ből előre hozva, csak a letöltés):**
    - a vLLM v0.30.0 modellregisztere ismeri (`Gemma4ForConditionalGeneration`); a modell Apache-2.0, nem gated;
    - letöltés a spark-deven a `~/hf-cache-gemma4` alá, mert a közös HF-cache `.locks` könyvtára root-tulajdonú;
    - a smoke (boot, memória, címketokenek) az F2 része.

- **2026-10-09 — v0.2 vázlat, a 01 F4 után.**
  - **A 01 eredménye:** a H1 cáfolt (a 01 eredménylapja). Az L3 a val-on és a nem-X itemeken nyer. A valódi
    irrelevanciát viszont magabiztosan eszközhöz rendeli (H5 cáfolt), és a MASSIVE címkekonvencióit beégeti.
  - **Összevetés a JEV-27B-vel:** puha célokkal tanít, nincs X-opciója, és a kalibrált bázissal nem hasonlít össze.
    A két eredmény összefér; a különbségek a 01 eredménylapján.
  - **Változott (Dani jóváhagyásával):**
    - a gold elsőbbsége helyett gold–tanár keverék-cél (4.1);
    - tanárjelöltek: Mistral Small 4, Gemma 4 26B-A4B-it, Qwen3.6 gondolkodó mód, típusonkénti X-kapuval (4.4);
    - négy X-típus (2.);
    - bázis-horgony (4.7);
    - új karok: G3-kemény, horgony nélküli abláció (6.);
    - precizitáshoz kötött rétegítélet, célréteg-kalibráció a H3-ban, új H6 (7.);
    - eval-függetlenségi szabály és új kockázatok (4.4, 11.).
    - külső eval: a Decision Index kit választott sávjai, a JEV itemenkénti eredményeivel referenciaként (5.); a
      JEV-kimenet tanításból kizárva (3.6).
  - **01 F5b (ugyanaznap):** a puha cél egyedül nem védi ki az irrelevancia-csapdát (0. pont). Ezért az 1. pont 5.
    kérdése és a súlyozás: az elsődleges kar az X-típusok lefedése és a bázis-horgony, a puha cél a H6-ban mérve.
- **2026-10-07 — v0.1 vázlat.**
  - **Alap:** az ötletanyag, a 2026-10-04-i HF-felmérés és a 00/01 leletei.
  - **Az ötletanyaghoz képest változott:**
    - a kitartott családok tesztje a 00/01 emberileg átnézett tesztjeiből áll, nem tanárcímkés szintetikából;
    - a címkekészlet A–J marad (A–P helyett);
    - a `score` kimarad;
    - tanárkapu került be (a 00-ban mért X-gyengeség miatt);
    - a forrás-gold is zajauditot kap;
    - a DocAI-javítások a publikus modellből kimaradnak;
    - az MVP 15–20 ezer item a kapacitás miatt.
  - **Licencellenőrzés (2026-10-07):**
    - a HuLU tesztcímkéi rejtettek (HuCOLA README);
    - a Belebele, a SIB-200, a MultiEURLEX és a NerKor CC-BY-SA-4.0;
    - a TED szabadon újrahasznosítható, de PII-szűrés kell;
    - az OpinHuBank tisztázatlan, ezért kizárva.
  - **Llama-döntés (Dani):** a szűrés nem tanítás (10. pont).
