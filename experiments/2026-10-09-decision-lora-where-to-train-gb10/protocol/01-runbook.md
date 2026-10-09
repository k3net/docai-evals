# Runbook 01: döntési fej eszközválasztásra (tool routing)

**Kalibrált, „egyik sem”-et is ismerő eszközválasztás ugyanazon a kiszolgált Qwen3.6-FP8
vLLM-példányon — a 00-ás kör módszerével, publikus function-calling adaton, magyar réteggel.**

- Verzió: **v1** (2026-10-08). A hipotézisek, a végpontok, a rétegek és a publikálási szabály a
  teszt érintése előtt rögzítve. **Státusz:** az F4 lezárult (2026-10-09). A H1 cáfolt, a publikálási
  szabály „H1 bukik” sora érvényes; ld. az [eredménylapot](kor01/eredmenyek/F4/eredmenylap.md).
- Gép, alany, infrastruktúra: ugyanaz, mint a 00-ban (measurement-host, `Qwen/Qwen3.6-35B-A3B-FP8`
  MTP nélkül, vLLM v0.30.0, `lora-train:2`, leválasztott futások, `lanc.sh`/`folytat.sh`).
- Végtermékek (terv): (1) magyar + angol eszközválasztási adatkészlet publikus forrásokból,
  egy általános eszközkatalógussal; (2) HF döntési adapter, a 8. pont publikálási szabálya
  szerint; (3) tanulmány.

> A v1 előtt modell csak a train-t és a val-t látta (F3-pilot, Napló 2026-10-08). A rögzített
> pontok: 4. (rétegek), 6. (definíciók, hipotézisek, statisztika), 8. (publikálási szabály).
> Ezek utólag csak a Naplóban indokolt, a teszteredmény előtti döntéssel változhatnak.

---

## 0. Kiindulás

### Amit a 00-ás körből tudunk (2026-10-06-i állapot)

| megállapítás | forrás |
|---|---|
| a restricted softmax kiolvasás a címkéken (A–J + X, egytokenesek) működik vLLM-en és HF-ben, a két motor egyezik | 00 Napló, F2–F3 |
| egy r16 LoRA (BF16-bázison tanítva, futásidőben betöltve) az FP8-as vLLM-alanyon hű; a fake-quant nem kell | 00 Napló, F3 pilot |
| az L3 a val-on @95 0,756-ot ér el (L1★: 0,596, L2a: 0,688), az AURC 0,001 (L1★: 0,032) | 00 Napló, F3 |
| **plafonhatás:** a val-on az L3 a helyes besorolás felső korlátján (0,764) ült, így a hangolás és a karválasztás zajra döntött | 00 Napló, F3 hangolás |
| a gold-drop előtti szinonim/duplikátum-opciók hamis X-et és hamis hibát adnak (12/99 hibás címke az első átnézésben) | 00 Napló, F1F |
| a @95 MDE-jét a τ-választás uralja (~11–12 pont), az AURC sokkal felbontóbb | 00 Napló, MDE |

### Amit nem tudunk, és ezért lenne ez a kör

1. Átvihető-e a döntési fej egy **szabványos, publikus** feladatra, ahol a jelöltek nem
   cikkek, hanem eszközleírások (név + leírás + paraméterek)?
2. Veri-e a döntési fej a modell **natív tool callingját** (chat template + `tools`,
   generálás) a „nem kell eszköz” felismerésében és a kalibrált tartózkodásban?
3. Általánosít-e **új eszközökre** (amelyeket a tréning nem látott) és **magyar** kérésekre
   úgy, hogy a tréning nagyrészt angol?
4. Elfér-e **két döntési adapter** (BA-bíráló + eszközválasztó) ugyanazon a példányon
   egymás zavarása nélkül (`--max-loras 2`)?

---

## 1. Kutatási kérdés

Egy kis döntési LoRA az eszközválasztást egyetlen címketokenre redukálva (A–J = jelölt
eszközök, X = egyik sem) kalibráltabb és lefedettebb döntést ad-e, mint (a) a kalibrált
logit-kiolvasás és (b) a natív tool calling, és ez általánosít-e új eszközökre és a magyarra?

**Hatókör:** csak az *eszközválasztás*. Az argumentumok kitöltése a natív generálásé marad
(stretch: router + natív argumentumgenerálás vég-vég mérése a BFCL AST-kiértékelőjével).

---

## 2. Feladatforma

- **Item:** felhasználói kérés (+ opcionálisan rövid előzmény) és 1–10 jelölt eszköz. Az
  eszköz a promptban: `név — leírás (kötelező paraméterek)`, hosszkorláttal.
- **Címkék:** `A`…`J` a jelöltek, `X` = egyik sem: nincs megfelelő eszköz, vagy eszköz
  nélkül kell válaszolni. A címketokenek a 00 K0b-auditja szerint egytokenesek. A kimenet
  mindig egyetlen címketoken; más kimenet nincs.
- **Keretszöveg nyelve:** a keretszöveg a kérés körüli rögzített utasítás, pl. „Melyik
  eszközt kell hívni? Válaszolj egyetlen betűvel.”, illetve „Which tool should be called?
  Answer with a single letter.”. Ez az item nyelvét követi: magyar kérésnél magyar keret,
  angolnál angol. Az eszközleírások a forrás nyelvén maradnak. (Alapértelmezés 2026-10-06,
  ld. Napló.)
- **Kizárva az elsődleges feladatból:** a párhuzamos és a többlépéses hívások (BFCL
  `parallel*`, `multi_turn*`). Ezeknél nem egyetlen döntés a gold. Diagnosztikának megmaradnak.
- **Nincs külön visszakérdezés-címke** (user-döntés 2026-10-06). A When2Call „follow-up”
  itemjeinél a megfelelő eszköz létezik, csak paraméter hiányzik, ezért a gold ez az eszköz;
  a paraméterhiány az argumentum-szakasz dolga. Az „unable to answer” és az eszköz nélküli
  válasz gold-ja `X`.
- **Gold-drop (X-generálás):** a gold eszközt kivesszük a listából (az `xlam-irrelevance`
  receptje). **Előtte kötelező a szinonim-eszközszűrés** (00 F1F-lelet): ha a listán marad
  egy másik eszköz, amely ugyanazt a kérést kiszolgálja, a gold-drop hamis X-et ad. Ezt LLM
  párbíráló dönti el (a 00 `duplikatum_llm.py`-jának mintájára).

---

## 3. Adatforrások — átvilágítva 2026-10-06-án

Licencet és méretet a HF-API-ból és a kártyákból néztem. A „minta” oszlop saját
mintavételezés eredménye.

### 3.1. Fő források

| forrás | méret | licenc | generátor | szerep | megjegyzés |
|---|---|---|---|---|---|
| `gorilla-llm/Berkeley-Function-Calling-Leaderboard` (BFCL v3 fájlok) | simple 400 · **multiple 200** (2–4 eszköz) · **irrelevance 240** (1 eszköz) · live_simple 258 · **live_multiple 1053** (2–37 eszköz, zöme 2–5) · **live_irrelevance 882** (0–12 eszköz) · live_relevance 18 · parallel 200 · parallel_multiple 200 | Apache-2.0 | kézi + felhasználói beküldés (live) | **csak teszt** | ismert benchmark: a Qwen3.6 láthatta, ezért a fő általánosítási réteg a live + magyar + belső. Az elemszámok a fájlokból számolva |
| `Salesforce/xlam-function-calling-60k` | 60 000; 3673 API, 21 kategória | CC-BY-4.0, **gated (auto)** | DeepSeek-V2-Chat (első 33 659), Mixtral-8x22B-Inst (többi) | **train** (választás) | háromlépcsős verifikáció (formátum, végrehajtás, szemantika). A DeepSeek-V2 modell-licencét a publikálás előtt meg kell nézni |
| `MadeAgents/xlam-irrelevance-7.5k` | 7500 | CC-BY-4.0 | xLAM-ból gold-drop | **hivatkozási forrás** (az X-et saját, pótlásos gold-droppal készítjük, ld. Napló) | a Hammer-cikk lelete: a hívásra tanítás rontja az irrelevancia-felismerést, ez ellensúlyozza. Szinonim-szűrés nélkül készült, át kell nézni |
| `nvidia/When2Call` | train_sft 15 000, train_pref 9 000; test: MCQ + LLM-judge részhalmaz | CC-BY-4.0, „ready for commercial use” | Mixtral-8x22B | **train + teszt** | négy viselkedés: hívás / visszakérdezés / „nem tudom eszközzel” / eszköz nélküli válasz. Címkéi: a hívás és a visszakérdezés gold-ja az eszköz, a többié `X` (ld. 2. pont) |
| `stindardlogic/eu-multilang-tool-calling-180k` (hu rész) | 29 240 sor, de csak **136 egyedi beszélgetés** (mind 215×) | ellentmondásos: README Apache-2.0, manifest CC-BY-4.0 | „local models” | magyar train-kiegészítés (user-döntés 2026-10-06, a lelet után felülvizsgálandó) | a 136-ból 63 eszközhívás, 73 X; 12-nél az eszközlista nem nyerhető ki, 17 párhuzamos hívás (ld. 3.3) |
| `AmazonScience/massive` hu-HU | 11 514 / 2033 / 2974 | CC-BY-4.0 | **emberi** lokalizáció | **magyar train + teszt** (javaslat: a fő magyar train-forrás) | 18 scenario, 60 intent → kézzel írt magyar eszközleírások. A tartott intentek adják a gold-drop X-et. **Az egyetlen emberi magyar réteg.** (A Speech-MASSIVE más licencű, NC.) |

### 3.2. Kiegészítő források (feltételesen)

| forrás | méret | licenc | generátor | ítélet |
|---|---|---|---|---|
| `glaiveai/glaive-function-calling-v2` | 112 960 | Apache-2.0 | nem dokumentált | kiegészítő train, ha kell a térfogat; zajos, az „eszköz nélkül válaszol” párbeszédek X-forrásnak jók |
| `Team-ACE/ToolACE` | 10K–100K (részhalmaz) | Apache-2.0 | a kártyán nem dokumentált | kiegészítő train; a generátor ismeretlensége publikálási kockázat |
| `NousResearch/hermes-function-calling-v1` | 10K–100K | Apache-2.0 | nem dokumentált | kiegészítő; vegyes (json-mode, extrakció is) |

### 3.3. A felvetett készletek részletes ítélete

- **`stindardlogic/eu-multilang-tool-calling-180k` — a legígéretesebb magyar forrás, de csak
  tisztítva.** Bájttartományos mintát vettem a 248 MB-os fájl tíz pontjáról: 2853 sor, ebből
  598 magyar.
  - **A séma eltér a README-től.** Nincs strukturált `tools` mező. Az eszközök a system
    promptban szabad szövegként, vegyes formátumban szerepelnek (YAML-szerű, JSON, próza),
    így ki kell nyerni őket.
  - **Duplikáció:** 598 sorban 129 egyedi első felhasználói üzenet van. A „Milyen az időjárás
    Budapesten ma?” 32-szer szerepel.
  - **Típusok:** egyenletesen oszlanak (`apel_simplu`, `apel_compus`, `apel_cu_eroare`,
    `fara_apel`, `refuz_politicos`). Hívás 355, hívás nélkül 243. Soronként 2–3 eszköz van,
    a mintában összesen 48 eszköznév, 7 domén (adó, bank, e-kereskedelem, naptár, időjárás,
    kormányzati, általános).
  - **Minőség:** a magyar szöveg gépies és hibás („Beszerzi meg az adóinformációkat…
    tartozó adóinformációkat”, „keressd meg az adótarat”). A `fara_apel` válaszok
    hallucinálnak (pl. kitalált tartozásösszeg). A döntési címke ettől még lehet jó, de
    LLM-átnézés kell.
  - **Teljes letöltés után (2026-10-06):** a 29 240 magyar sor csupán **136 egyedi
    beszélgetés**, mindegyik pontosan 215-ször. A hash egyezik a manifesttel. A többi nyelv
    ugyanilyen: a 175 716 sorban összesen ~820 egyedi beszélgetés van.
    - Dedup után a 136-ból 63-ban van eszközhívás, 73 X.
    - 12-nél a system promptból nem nyerhető ki az eszközlista.
    - 17-ben párhuzamos hívás van; ezek az elsődleges feladatból kiesnek.
  - **Ítélet:** a user-döntés (magyar train-forrás) a 30K-s méret feltételezésével született.
    136 egyedi itemmel ez legfeljebb kiegészítés: átnézés után a train-be kerülhet, tesztnek
    nem. **Javaslat:** a fő magyar train-forrás a MASSIVE hu train legyen az általános
    katalógusra képezve (10 862 eszközös és 652 X mondat, emberi magyar). A licencnél a
    szigorúbbat, a CC-BY-4.0-t követjük, forrásmegjelöléssel.
- **`BitAgent/tool_calling` — nem használható.**
  - **Nincs licenc:** alapértelmezésben minden jog fenntartva.
  - **Nem döntési feladat:** 551 285 sor, minden sorban pontosan 1, a kérdésre szabott eszköz
    (pl. `get_amazon_52week_high`), így nincs választási feladat és nincs X.
  - **Ismétlődés:** 12 × 100 egymás utáni sorban 25 egyedi kérdés.
  - **Hibás hívások:** 68/1200 hívásból hiányzik kötelező argumentum. A válaszok
    hallucináltak, „---” műtermékekkel.
- **`Qrzysztof/functiongemma-prepaid-cards-tool-calling-v2` — ötletforrás, nem korpusz.**
  - **Méret:** Apache-2.0, 4858 sor, 3 rögzített eszköz (kártyavásárlás, egyenleg, tranzakciók).
  - **Magyar rész:** 36 sablonos, kézzel fordított sor.
  - **Átvehető ötletek:**
    - a **zajaugmentáció** (elírás, kisbetű, szóvesztés, de számjegy-biztosan);
    - a **sablon-azonosítós split**, hogy egy sablon ne kerüljön a train és a teszt közé is;
    - a **teljesen kitartott nyelvek**;
    - a `greet`/`negative` X-minták.

### 3.4. Kizárva

- `Salesforce/APIGen-MT-5k`: CC-BY-NC-4.0.
- `BitAgent/tool_calling`: licenc nélküli, ld. fent.
- Minden NC licencű, illetve nem dokumentált, zárt modellel (pl. GPT-4) generált forrás, ha
  publikálunk.

### 3.5. Általános eszközkatalógus (user-döntés 2026-10-06)

Belső, docit-specifikus réteg helyett egy **általános katalógus** készül, olyan eszközökből,
amelyeket sok rendszer használ. Ez publikálható, és a publikus adapter célközönségének is ez
a valószerű környezet.

- **Eszközök (~40–60):** időjárás és előrejelzés, e-mail küldése/keresése/olvasása, webes
  keresés, naptáresemény létrehozása/lekérdezése, emlékeztető és ébresztő, útvonaltervezés,
  pénznemváltás, fordítás, hírek, fájlkeresés, jegyzet, teendőlista, zene, okosotthon, étel
  rendelése stb.
  - Mindegyikhez név, magyar és angol leírás, valamint JSON-paraméterséma tartozik.
  - Szándékosan vannak benne **közeli párok** a nehéz zavaráshoz, pl. `send_email` vs.
    `reply_email`, `get_weather` vs. `get_forecast`, `web_search` vs. `news_search`.
- **Lefedés a MASSIVE-vel:** a MASSIVE 18 scenariója (email, calendar, weather, alarm, news,
  transport, music, iot, lists, takeaway, qa, datetime stb.) nagyrészt erre a katalógusra
  képezhető le. A MASSIVE hu-HU **emberi** megfogalmazásai így ugyanezen a katalóguson
  adnak magyar tesztet.
- **Szintetikus kiegészítés:** a MASSIVE-ben nem szereplő eszközökre (pl. webes keresés,
  csatolmányos e-mail, pénznemváltás) Apache-2.0 generátorral (Qwen3.6 vagy Mistral Small 4)
  írt magyar kérések készülnek, plusz a gold-drop X.
- **Tisztaság:** valós személy-, cég- és ügyféladat nem kerül bele.

---

## 4. Splitek és rétegek — rögzítve (v1, 2026-10-08)

A fagyasztás: `kor01/adat/f1s/atnezes/fagyasztas.sha256` (Napló 2026-10-07).

- **Train:** 14 513 item.
  - `items_train`: xLAM 7972, MASSIVE hu 4500, When2Call 1999; ebből 131 kétértelmű, soft céllal.
  - Az EU-180k train-extra: 42 hívásos item, átnézve; a 71 forrás-X kimarad.
- **Val:** 3524 item; val-xlam 1493, val-massive 2031.
  - 89 kétértelmű, 933 X.
  - A plafon 0,729.
  - A val-massive becsült maradék címkezaja ~3,3%.
- **Teszt-rétegek** (pontozott = nem kétértelmű; a klaszter a `meta.klaszter`):

  | réteg | tartalom | item | pontozott | klaszter | X | szerep |
  |---|---|---|---|---|---|---|
  | T-BFCL | simple 399, multiple 200, irrelevance 240 | 839 | 839 | 839 | 28,6% | H1-pool; leíró (a Qwen láthatta) |
  | T-BFCL-live | live_simple 258, live_multiple 1050, live_irrelevance 875 | 2183 | 2183 | 2183 | 40,1% | H1-pool; **H2** |
  | T-When2Call | az MCQ-teszt | 3388 | 3388 | 1293 | 30,5% | H1-pool; a **H2** T-BFCL-live rétegének alrétege |
  | T-hu | MASSIVE hu-teszt, a teljesen átnézett 600-as véletlen részhalmaz (`meta.t_hu_atnezett`) | 593 | 553 | 553 | 34,7% | H1-pool; **H2** |
  | T-katalógus | generált magyar kérések a katalógusra, teljesen átnézve | 636 | 598 | 598 | 26,8% | H1-pool; leíró |
  | T-új-eszköz | keresztréteg a BFCL és a When2Call itemjeiből (lent) | ~3800 nem-X + X | | | | leíró |
  | T-hu-maradék | a MASSIVE-teszt át nem nézett része | 2374 | | | ~32% | leíró, ~10% címkezajjal |

  - **A When2Call** mind a 3388 iteme a BFCL-live kérdéseiből készült: az 1293 klaszter
    mindegyike közös a BFCL-live-éval. A bootstrapban egy klaszternek számít.
  - **A H2 T-BFCL-live rétege:** a BFCL-live és a When2Call együtt, 5571 item, 2183 klaszter.
  - **A H1-pool:** a T-BFCL, a T-BFCL-live, a T-When2Call, a T-hu és a T-katalógus együtt, 7561
    item, ~4170 klaszter (Dani, 2026-10-08).
- **T-új-eszköz definíciója:** bge-m3 a train 3330 eszközének név + leírás szövegén.
  - Nem-X item akkor tartozik ide, ha a gold neve nincs a train eszköznevei közt, és a gold leírásának
    legnagyobb koszinusza a train-eszközökhöz < 0,85.
  - X itemnél ugyanez minden opcióra teljesül.
  - A tagságot a `szivargas.py --uj-eszkoz-x` számolja a tényleges train ellen (az EU-180k
    train-extrával együtt), az F4 elején: `eredmenyek/F1S/uj_eszkoz.jsonl`. Az F1S-audit a
    train-extra nélkül 3802 nem-X itemet adott; a végleges szám ebből a futásból jön.
- **T-hu közel-duplikátumok:** a pontozott 553 itemből 46 kérés áll közel egy train-kéréshez
  (koszinusz ≥ 0,95), ebből 16 szó szerint azonos. Az elsődleges elemzés mind az 553 itemen
  fut, az érzékenységi elemzés a 46 nélkül.
- **A tesztcímkék minősége** (a tanulmány korlátja):
  - A T-hu és a T-katalógus címkéit GPT-modell nézte át teljesen, emberi vak szúrópróbával
    auditálva (300 változatlan + 71 gépi döntés). A becsült maradék zaj 1,2% (felső95 2,4%).
  - A címkejavítás mindig Dani-megerősítésű. Gépi ítélet csak kétértelmű- és kizár-jelölésnél
    maradt (85 item kikerült a pontozásból).
  - A BFCL és a When2Call goldja a benchmarké, átnézetlen.
- **Szivárgás-audit (F1S, kész):** a MASSIVE teszt–train párokon 108 szó szerinti
  kérés-duplikátum és 279 közel-duplikátum (koszinusz ≥ 0,95); a T-katalógus tiszta; a
  val-xlam-ban 17 gold-név szerepel a trainben.

---

## 5. A létra

| kar | leírás |
|---|---|
| **L0n** | **natív tool calling:** chat template + `tools`, greedy; az eredmény, hogy hívott-e eszközt, és melyiket. Egyetlen működési pont, kalibráció nélkül. Bizalomnak az első eszköznév-token logprobja (diagnosztika) |
| L0 / L1★ | a döntési kérdés címke-kiolvasása + a 00-ás kalibrációs karok. **L1★ = `perm_avg`** (4 permutáció átlaga + temperature), a 00-ás szabállyal a val-on választva (F3-pilot, rögzítve) |
| L2a | *(leíró, ha az idő engedi)* lineáris fej a rejtett állapoton (a 00 `l2a_szonda.py`-ja); hipotézis nem tartozik hozzá |
| **L3** | döntési LoRA, a 00 F3-ának győztes receptje (`k01_l3mixse_p30_s1..3`: `mix+se`, r16, α 32, ε = 0,05, lr 1e-4, 1 epoch, fake-quant nélkül), 3 seed. **Újdonság a 00-hoz képest:** az itemek 30%-a véletlen opció-permutációval tanul (a JEV-27B receptje, Napló 2026-10-07; a 00-ás L3 mindig a tárolt sorrendben tanult). Kalibrációs kar: `temp`, a val-on illesztve, seedenként |
| L3+BA | (H4) az L3 és a 00 BA-adaptere egy példányon, egyszerre betöltve |
| L3→S2 | (leíró kar) az L3 a τ fölött dönt, a τ alattiakat a bázismodell gondolkodó módja kapja ugyanazzal a döntési kérdéssel (System 1 → System 2, a JEV mintájára); jelentve: lefedettség, precizitás, késleltetés. A docai-0122 C fokának tervéhez |

---

## 6. Definíciók, hipotézisek, statisztika — rögzítve (v1, 2026-10-08)

### 6.1. Definíciók

A 00-runbook 2. pontjának definíciói változatlanul érvényesek. Ezek: döntési pozíció, címke-token,
szűkített softmax, besorolás, τ-szabály, besorolási lefedettség@95 és @90, precizitás-bukás
(< 93%, illetve < 88%), AURC, döntési lefedettség, X-precizitás és X-fedés, ECE, kétértelmű-átlépés.

A τ a teljes 01-es val-on választódik (val-xlam + val-massive). A 01-ben ezek egészülnek ki:

- **Plafon:** a réteg pontozott nem-X itemjeinek aránya; ennél nagyobb besorolási lefedettség
  hibátlan döntéssel sem érhető el. Minden lefedettség mellé jelentjük, és a plafonhoz mért arányt is.
- **X-arány-standardizált Δ** *(másodlagos)*: a rétegek X-aránya eltér (T-hu 35%, a 00-ban 25%).
  Ezért a Δ lef@95-öt 25%-os és 10%-os X-arányra ritkítva is jelentjük; az X-itemek véletlen
  elhagyása a bootstrap minden replikájában újrahúzva történik.
- **L0n munkapontja (H3):** a natív tool calling egyetlen döntése: hívott-e eszközt, és melyiket.
  - Lefedettség = a hívások aránya; precizitás = a helyes eszköz aránya a hívások közt.
  - Az L3-at ezen a munkaponton két irányban mérjük:
    - **(i)** az L3 precizitása akkora lefedettség mellett, mint az L0n-é;
    - **(ii)** az L3 lefedettsége akkora precizitás mellett, mint az L0n-é.
  - A két L3-küszöb a teszten illesztett munkapont, nem tanult paraméter. Csak a H3-hoz használjuk,
    a H1/H2-höz nem.

### 6.2. Hipotézisek

A karokat mindig motoron belül, vLLM-ben hasonlítjuk össze, ugyanazon a LoRA-s példányon. A HF
csak a motor-hűség ellenőrzése.

**H1 — a döntési LoRA veri a kalibrált logitot** *(elsődleges)*
- **Végpontok:** az L3 (`temp`, 3 seed) és az L1★ (`perm_avg`) a H1-poolon, két
  társ-elsődleges végponttal:
  - (a) L3 > L1★ a lef@95-ben;
  - (b) L3 < L1★ az AURC-ben.
- **Döntés:** Holm-korrekció, családi α = 0,05. A H1 teljesül, ha legalább az egyik végpont
  szignifikáns az L3 javára.
- **Cáfolat végpontonként**, bármelyik elég:
  - a Holm-küszöbön nem szignifikáns, vagy az L1★ javára az;
  - (@95-nél) az L3 precizitás-bukott a poolon;
  - bármelyik seed pontbecslése ≤ L1★ (@95), illetve ≥ L1★ (AURC).

  Ha mindkét végpont cáfolt, a H1 cáfolt.
- **Másodlagos:** lef@90 és az X-arány-standardizált Δ.

**H2 — általánosít** *(elsődleges, háromértékű; Dani, 2026-10-08)*

Külön ítélet a T-BFCL-live rétegen (a When2Call alrétegével) és a T-hu rétegen, a Δ lef@95 (L3 − L1★)
95%-os CI-je alapján:
- alsó határ > 0 → **általánosít**;
- felső határ < 2 százalékpont → **nem általánosít**;
- egyébként → **nem eldönthető**.

Az AURC másodlagos, rétegenként mindig jelentve. A T-új-eszköz és a T-katalógus ugyanígy,
leíróan jelentve, ítélet nélkül.

**H3 — veri a natív tool callingot**
- A H1-poolon az L0n munkapontján mindkettőnek teljesülnie kell:
  - (i) Δ precizitás > 0;
  - (ii) Δ lefedettség > 0.

  Mindkettőnél a párosított, klaszterezett bootstrap CI-jének alsó határa > 0 kell.
- **Cáfolat:** bármelyik alsó határ ≤ 0.
- Külön jelentjük az X-fedést, vagyis az irrelevancia felismerését; rétegenként is.

**H4 — két adapter egy példányon, párhuzamos terhelés mellett is**
- **Elrendezés:** a 01 L3 (s1) és a 00 BA-adaptere (`l3mixse_h2_s1`) egy példányon,
  egyszerre betöltve. Mindkét adapter top-címke-egyezése az egyadapteres példánnyal ≥
  (két friss egyadapteres példány egymás közti egyezése) − 1 százalékpont, egyoldali 95%-os
  alsó korláttal.
- **Mindkét kiolvasási módban teljesülnie kell:**
  - **soros (c = 1);**
  - **párhuzamos (c = 16):** vegyes forgalom adapteres és adapter nélküli kérésekkel.
- **Itemek:** a 01 val (3524) és a 00 val (1006), perm 0. Mérnöki mérés, a teszthez nem nyúl.
- **Cáfolat:** bármelyik feltétel bukik.

**H5 — nincs irrelevancia-kompromisszum**
- A H1-poolon mindkettőnek teljesülnie kell:
  - az X-fedés nem rosszabb: a Δ X-fedés (L3 − L1★) CI-jének alsó határa > −2 százalékpont;
  - a nem-X itemeken a top-1 pontosság nő: a Δ CI-jének alsó határa > 0.
- Ez a Hammer-cikkben leírt kompromisszum ellenpróbája.

**L3→S2** *(leíró)*
- Az L3 a τ fölött dönt; a τ alatti itemeket a bázis gondolkodó módja kapja, ugyanazzal a döntési
  kérdéssel.
- Jelentve: lefedettség, precizitás, késleltetés. A docai-0122 C fokának tervéhez.

**Többszörös tesztelés:**
- A H1 és a H2 együtt adja a fő állítást; mindkettőnek teljesülnie kell, korrekció nem kell (a 00
  szerint).
- A H3 és a H5 egy Holm-családot alkot.
- A H4 kritériumalapú mérnöki ítélet.

### 6.3. Statisztikai protokoll

- **Párosítás:** minden összevetés párosított, ugyanazokon az itemeken, ugyanazon a LoRA-s
  vLLM-példányon. Az L1★ és az L3 kiolvasása egy példányon fut, ahogy a 00 F4-ében.
- **Ismétlési zaj:** az F4 végén az L0 még egyszer lefut (L0′). Az L0↔L0′ eltérés külön
  zajforrásként kerül a tanulmányba.
- **CI: klaszterezett bootstrap**, klaszter = `meta.klaszter`.
  - Minden replikában a val is újramintavételeződik, és a τ újraválasztódik.
  - A H1-nél hierarchikus: seed × klaszter.
  - 10 000 ismétlés, 95% CI. A kétoldali p = 2 · min(P(Δ ≤ 0), P(Δ ≥ 0)).
- **Val/teszt-higiénia:** a küszöb, a temperature és a kalibrációs kar csak a val-on rögzül. A teszt
  egyszer fut, az F4-ben.
- **Bontások:**
  - réteg és forrás;
  - X / nem-X;
  - opciószám (1, 2–5, 6–10);
  - X-arány-standardizálva (25%, 10%);
  - T-hu a 46 közel-duplikátum nélkül.
- **Másodlagos:** McNemar a pontosságra.
- **MDE** (`kor01/eszkozok/mde01.py`, a pilot val-kiolvasásaiból, a 00 `mde.py` módszerével;
  80% erő, kétoldali α = 0,05; seed-komponens nélkül):

  | | H1-pool (~4170 klaszter) | T-BFCL-live (2183) | T-hu (553) |
  |---|---|---|---|
  | lef@95 | 2,0 pont | 2,2 pont | 3,2 pont |
  | lef@90 | 1,0 pont | 1,3 pont | 2,6 pont |
  | AURC | 0,0018 | 0,0025 | 0,0049 |

  A lef@95-szórás 72%-a a τ-ból jön (a 00-ban > 90% volt). A pilot val-Δ-ja +4,1 pont és
  −0,0032 AURC.
  - **Fenntartás:** a val a plafonon ül, így a val-variancia a nehezebb tesztrétegekét alulbecsülheti.
  - **Kockázat:** a plafonon ülő val-on választott τ a nehezebb rétegeken precizitás-bukást adhat. Ez
    maga is mért eredmény (H1 cáfolati ága).

## 7. Fázisok

| fázis | tartalom | állapot / idő |
|---|---|---|
| F0 | letöltés, séma-egységesítés, általános katalógus | kész (2026-10-06) |
| F1 | itemgyártás, szinonimaszűrés, szivárgás-audit, címke-átnézés (gépi + emberi szúrópróba), fagyasztás | kész (2026-10-07) |
| F2 | L0/L1★ a val-on (az F3-pilot példányán); L0n natív kiolvasó, S2-kiolvasó, T-új-eszköz tagság, H4-egyezés, F4-elemző: kész (2026-10-08); L2a leíróként, ha az idő engedi | kész |
| F3 | L3: pilot seed 1 kész; a val a plafonon ült → **nincs hangolás** (a v0.1 előre rögzített F3-szabálya: hangolás csak nem plafonon ülő val mellett); seed 2 és 3: val-lef@95 0,7234 / 0,7231 (s1: 0,7237) | kész (2026-10-08) |
| F4 | `k01f4_vezenylo.sh smoke` → `teszt` (a seed 3 után automatikusan, `lanc.sh`): egy LoRA-s példányon a bázis és az L3 s1 (4 perm.), s2–s3 (perm 0), val + teszt, L0′; L0n (c = 16), L3→S2 (c = 16); H4 öt friss példányon a val-okon. Elemzés a laptopon: `f4_elemzes01.py` (10 000 replika), lap: `f4_riport01.py` | kész (2026-10-09; teszt 18:15–03:15) |
| F5 | stretch: router + natív argumentumgenerálás vég-vég a BFCL AST-kiértékelőjével | opcionális |
| F5b | külső összevetés a JEV-vel: CLINC150+OOS és When2Call MCQ, a JEV közölt itemenkénti valószínűségei, a gold a kit rögzített forrásaiból; a When2Call-on a 01 karjaival ugyanazokon az itemeken. `f5b_jev.py` → `eredmenyek/F5b/f5b_jev.json` | kész (2026-10-09), GPU nélkül |
| F6 | dataset card, adapter-kártya, tanulmány | ~2 nap |

## 8. Licenc és publikálás

- **Publikus adatkészletbe csak engedékeny forrás kerülhet:** Apache-2.0, illetve CC-BY-4.0
  forrásmegjelöléssel. A származtatott sorok a forrás licencét öröklik.
- **Gated forrás:** az xLAM gated; a feltétel része az APIGen-cikk (arXiv:2406.18518) idézése. A feltételeit a letöltés előtt el kell olvasni; ha tiltja a
  továbbadást, csak a mi gold-drop- és fordítási szkriptünket publikáljuk, a sorokat nem.
- **Generátor-licencek:**
  - DeepSeek-V2 (xLAM első fele): a modell-licencet ellenőrizni kell;
  - Mixtral: Apache-2.0;
  - a saját generálás csak Apache-2.0 modellel mehet (Qwen3.6, Mistral Small 4), a
    publikus-modell memóriajegyzet szerint.
- **A BFCL csak teszt:** a tesztsorait nem tanítjuk, és nem tesszük be a publikus készletbe;
  csak a kiértékelő szkript és az eredmény megy ki.
- **Publikálható minden réteg**, a BFCL-sorok kivételével. Az általános katalógus a saját
  munkánk, Apache-2.0 alatt.

**Publikálási döntési szabály — előre, nem utólag (Dani, 2026-10-08):**

| eredmény | adatkészlet | adapter | tanulmány |
|---|---|---|---|
| H1 igaz, és a H2 a T-hu-n és a T-BFCL-live-on is „általánosít” | publikus | **publikus**; a H3/H4 negatív eredménye megjegyzésként a kártyán | teljes |
| H1 igaz, a H2 valamelyik rétegen „nem általánosít” | publikus | nem | „a javulás nem általánosít” |
| H1 igaz, a H2 valamelyik rétegen „nem eldönthető”, és egyiken sem „nem általánosít” | publikus | nem | a nagyobb réteg igényét mondja ki |
| H1 bukik | publikus | nem | „a kalibrált logit elég”: publikálható negatív eredmény |

- A T-új-eszköz és a T-katalógus eredménye leíró; a kártyán szerepel, a szabályt nem érinti.
- Az adatkészlet `meta.atnezes.forras` mezője jelzi, ki döntött: gépi, gépi + Dani, Dani.

---

## 9. Döntések

1. **Kimenet:** egyetlen döntési címke. A keretszöveg nyelve az item nyelvét követi (2. pont).
2. **Nincs külön visszakérdezés-címke:** csak `A`–`J` + `X`.
3. **Magyar train-forrás:** a **MASSIVE hu train** az általános katalógusra képezve. Az
   EU-180k 136 egyedi iteme kiegészítés, átnézés után (user-döntés 2026-10-06, a
   136-egyedi-lelet után; a korábbi „EU-180k a fő forrás” döntést felváltja).
4. **xLAM:** a user elfogadja a gated feltételeket a `k3dani` HF-fiókkal. A measurement-host
   meglévő HF-bejelentkezése is ehhez a fiókhoz tartozik, így a letöltés a `hf download`
   paranccsal megy, a token kiírása nélkül.
5. **Belső docit-réteg helyett általános eszközkatalógus** (3.5): időjárás, e-mail, keresés,
   naptár és hasonlók, amelyeket sok rendszer használ.
6. **When2Call:** a teszt a BFCL-live alrétege, közös klaszterrel (user-jóváhagyás 2026-10-06).

**A v1 döntései (Dani, 2026-10-08, a teszt érintése előtt):**

7. **H1-pool:** minden réteg (T-BFCL, T-BFCL-live, T-When2Call, T-hu, T-katalógus).
8. **H2-mérce:** a 00 szerint, a Δ lef@95 háromértékű ítéletével; az AURC másodlagos.
9. **H2-rétegek:** a T-BFCL-live (a When2Call alrétegével) és a T-hu. A T-új-eszköz és a T-katalógus leíró.
10. **Publikálás:** a 8. pont táblázata szerint.

**Alapértelmezések (a v1 része):**
- L1★ = `perm_avg`;
- L3-kar: `temp`;
- a T-hu elsődlegesen mind az 553 itemen, a 46 közel-duplikátum nélkül érzékenységként;
- a H4 a val-on fut;
- hangolás nincs (a v0.1 előre rögzített F3-szabálya szerint, mert a val a plafonon ült; Napló 2026-10-08).

---

## 10. Kockázatok

- **BFCL-szennyezés:** a Qwen3.6 láthatta a BFCL-t. Ezért a H2 a live és a magyar rétegen
  ítél, nem a klasszikus BFCL-en; a T-BFCL csak a H1-pool része (mindkét kart egyformán érinti).
- **Plafon:** ha a val túl könnyű, a karválasztás megint zajra dönt (00-lelet). Ellenszer a
  nehéz val, a plafonhoz mért jelentés és az AURC.
- **Szinonim eszközök:** a valós eszközkészletekben gyakori a közel azonos funkció (pl. a
  live_irrelevance `requests.get`-je). Szűrés nélkül hamis X és hamis hiba keletkezik.
- **Zajos magyar szintetika:** az EU-180k gépies magyarja stílusbeli shortcutot taníthat. A
  T-hu (emberi MASSIVE) ezt méri.
- **τ a plafonon ülő val-ról:** a nehezebb rétegeken (BFCL-live, When2Call) precizitás-bukást
  adhat. Ez mért kimenet (H1 cáfolati ága), nem utólag javítható.
- **Gépi címke-átnézés:** a T-hu és a T-katalógus címkéi GPT-adjudikáltak, emberi
  szúrópróbával (maradék zaj ~1,2%, felső95 2,4%); a gépi kétértelmű/kizár ítéletek
  auditálatlanok (4. pont).
- **Hosszú eszközlisták (kezelve, F0):** a 10-nél több eszközös itemek kizárva
  (`forras_konvertal.py`, `MAX_OPT = 10`; a darabszám a `forras_riport.json`-ban). Az eredmény
  így legfeljebb 10 eszközös listákra szól; az előszűrős (jelöltgenerálós) változat nem része
  a körnek.

---

## Források

- BFCL: https://huggingface.co/datasets/gorilla-llm/Berkeley-Function-Calling-Leaderboard
- xLAM-60k: https://huggingface.co/datasets/Salesforce/xlam-function-calling-60k · APIGen: https://arxiv.org/abs/2406.18518
- xlam-irrelevance-7.5k: https://huggingface.co/datasets/MadeAgents/xlam-irrelevance-7.5k · Hammer: https://arxiv.org/abs/2410.04587
- When2Call: https://huggingface.co/datasets/nvidia/When2Call · https://aclanthology.org/2025.naacl-long.174
- MASSIVE: https://huggingface.co/datasets/AmazonScience/massive
- Glaive v2: https://huggingface.co/datasets/glaiveai/glaive-function-calling-v2
- ToolACE: https://huggingface.co/datasets/Team-ACE/ToolACE · https://arxiv.org/abs/2409.00920
- Hermes FC v1: https://huggingface.co/datasets/NousResearch/hermes-function-calling-v1
- EU-180k: https://huggingface.co/datasets/stindardlogic/eu-multilang-tool-calling-180k
- BitAgent: https://huggingface.co/datasets/BitAgent/tool_calling
- Prepaid-cards v2: https://huggingface.co/datasets/Qrzysztof/functiongemma-prepaid-cards-tool-calling-v2
- APIGen-MT-5k (kizárva, NC): https://huggingface.co/datasets/Salesforce/APIGen-MT-5k
- Korábbi forráslista (döntési korpuszok, MASSIVE hu-számok): `jegyzokonyv/2026-10-04-hf-dontesi-datasetek.md`

---

## Napló

- **2026-10-06 — v0 vázlat.** Forrás-átvilágítás:
  - licenc és méret a HF-API-ból;
  - a BFCL elemszámai a fájlokból;
  - a BitAgent, az EU-180k és a prepaid-cards készletből saját minta.
  A 00-ás kör F3-ának tanulságai (plafon, szinonim-gold-drop, AURC) beépítve.
- **2026-10-06 — v0.1.** User-döntések (9. pont):
  - nincs visszakérdezés-címke;
  - a magyar train az EU-180k;
  - az xLAM feltételeit a user elfogadja;
  - belső réteg helyett általános katalógus.
  A keretszöveg nyelvére az item nyelve az alapértelmezés: a user a kérdést nem a keretre
  értette, ezért itt rögzítem, és ha mást szeretne, átírjuk.
  Az INCLUDE, az XTREME és a dijihax/Dataset megvizsgálva, nem kerülnek be:
  - az INCLUDE tudásfelmérő négyválasztós benchmark;
  - az XTREME magyar része NER, POS és Tatoeba;
  - a dijihax nem adatkészlet.
- **2026-10-06 — F0 CPU-részek (`kor01/`).**
  - **Források letöltve** (`kor01/forras/`): BFCL v3 (6 kategória + possible_answer),
    When2Call (teszt + SFT), MASSIVE 1.1 (hu-HU, en-US), EU-180k (teljes, a hash egyezik).
  - **Általános katalógus** (`kor01/eszkozok/katalogus_epit.py` →
    `kor01/katalogus/eszkozok.json`, `massive_lekepezes.json`):
    - 62 eszköz, 18 domén, közeli párokkal;
    - mind a 60 MASSIVE-intent leképezve, ebből 3 csevegős intent X;
    - 14 eszköznek nincs MASSIVE-párja;
    - 6 intentnél (alarm_set, calendar_set, email_sendemail, qa_factoid, social_post,
      takeaway_query) a közeli pár a mondaton is helyes lehet, ezt az F1 LLM-átnézése dönti el.
  - **Egységes item-formátum** (`kor01/eszkozok/forras_konvertal.py` → `kor01/adat/`):
    - BFCL: simple 399, multiple 200, irrelevance 240, live_simple 258, live_multiple 1050,
      live_irrelevance 875. Kizárva a 0 és a 10-nél több eszközös itemek, valamint 1
      possible_answer nélküli;
    - When2Call teszt 3388;
    - When2Call train 7527;
    - MASSIVE hu 16 521 mondat;
    - EU-180k hu 136.
  - **Lelet 1:** az EU-180k 136 egyedi beszélgetés (3.3).
  - **Lelet 2:** a When2Call teszt teljes egészében BFCL-live-ból készült (4. pont).

- **2026-10-06 — xLAM letöltve** (a user a `k3dani` fiókkal elfogadta a feltételeket,
  „Affiliation: K3Net Kft.”).
  - **Forrás:** a measurement-host meglévő HF-bejelentkezésével, majd rsync a laptopra:
    `kor01/forras/xlam/`, 60 000 sor, CC-BY-4.0. A generátor a 0–33 658 id-ig DeepSeek-V2-Chat,
    utána Mixtral-8x22B. Az `xlam-irrelevance-7.5k` mellette (`kor01/forras/xlam_irrel/`).
  - **Konverzió:**
    - xLAM: 39 552 train-item; a többi 20 448 sor több eszközre szóló hívás, ezek kimaradnak.
    - xlam-irrelevance: 6054 X-item. 1446 kimarad, mert a gold kivétele után 0 eszköz maradt.
      4053 itemnek az xLAM-párja is megvan, közös klaszterben (normalizált kérés).
  - **Átfedés:** a When2Call-train mind a 3215 eszközneve xLAM-eszköz, vagyis onnan származik.
  - **Szivárgás, név-szinten (előzetes):** a 3022 BFCL-itemből 269-ben van a train-forrásokkal
    közös eszköznév. Ezek `train_eszkoznev_atfedes` jelzést kapnak, és a T-új-eszköz rétegből
    kiesnek. A leírás-szintű (bge-m3) audit az F1-ben jön.
  - **Hivatkozási kötelezettség** (a gated feltétel szerint): az APIGen-cikk
    (arXiv:2406.18518) idézése minden publikációban, ld. 8. pont.
- **2026-10-06 — F1, CPU-rész a laptopon** (`kor01/.venv`: tokenizers, scikit-learn, scipy).
  - **Keretszöveg** (`kor01/eszkozok/keret.py`): magyar és angol, a 00-ás `render_user` mintájára,
    `név: leírás (kötelező: …)` opciósorokkal és `X) Egyik sem` / `X) None of these` zárással.
  - **Tokenhossz** (`tokenhossz.py`, Qwen3.6-tokenizer; `adat/tokenhossz.json`): minden
    forráson p95 < 400 token, a maximum 780. A 00-ás `max_len 1024` elég, a leírást nem kell
    vágni.
  - **Item-összeállítás** (`osszeallit.py`; `adat/items_{train,val,teszt}.jsonl`,
    `osszeallit_riport.json`):
    - **train 14 500:** xLAM 8000, When2Call 2000, MASSIVE hu 4500; X-arány 26,1%.
    - **val 3533:** xLAM 1500 a 280 kitartott eszközzel, MASSIVE hu dev 2033 6–10 opcióval;
      X 26,5%.
    - **teszt 9384:** BFCL 3022, When2Call 3388, MASSIVE hu 2974; X 32,5%.
  - **Változás a terven:** az xLAM-család X-ét saját gold-drop adja, a 00 S7 receptjével (a
    gold helyére véletlen, más nevű eszköz kerül). Az `xlam-irrelevance` itemjei nem kerülnek
    be, mert pótlás nélkül készültek, és a többhívásos kérésekből is merítenek. Így az X és a
    nem-X opciószám- és kéréshossz-eloszlása eltért volna.
  - **Egyéb kiigazítások:**
    - a When2Call-train X-aránya 25%-ra állítva (a forrás 67%), kéréshossz szerint illesztve;
    - az egyeszközös visszakérdezés-itemek az X-ek opciószám-eloszlására pótolva;
    - katalógusnév nem lehet kitartott eszköz.
  - **Shortcut-audit** (egyváltozós AUC az X-re, holtversenyben átlagranggal):
    - train és val: forráscsaládonként minden jellemző ≤ 0,55 (opciószám ≤ 0,52);
    - teszt: a BFCL családon belül az opciószám AUC-ja 0,65, a kéréshosszé 0,75. Ez a benchmark
      saját összetétele (az irrelevance-itemek rövidek és egyeszközösek), és csak teszt, ezért
      rétegenként jelentjük.
    - Egy korábbi futás 0,57–0,70-es értékei részben mérési hibából jöttek: az első AUC-függvény
      nem kezelte a holtversenyt.
  - **Felülvizsgálandó itemek** (közeli pár a listán, vagy gold-drop): train 2419, val 644,
    teszt 290. Ezek az F1 LLM-párbírálatára mennek.
  - **Spark kell még (az F4 után):**
    - szinonim-eszközbírálat a gold-dropokra és a közeli párokra;
    - magyar kérések a 14 MASSIVE nélküli katalóguseszközre (T-katalógus);
    - az EU-180k eszközleírásainak kinyerése;
    - címke-előszűrés, majd Dani átnézése;
    - befagyasztás és MDE.

- **2026-10-07 — A 00 lezárása, a 01 folytatása (Dani döntése).** A 00 adatkészlete és adaptere a HF-re csak a
  01-es kör után kerül fel (00 Napló 2026-10-07). A 00 tanulságai a 01-re:
  - a split- és szivárgás-audit referenciája mindig a **ténylegesen használt** tanítóhalmaz (a 00b-ben a generátor
    újraépített train-je ellen futott);
  - a kitartott egység (itt: eszköz, kérés) párja sosem kerülhet a train-be; a fagyasztás előtt kötelező audit;
  - példányonkénti alany-log, a H-példányok váltakozó sorrendben (a 00 H3 tanulsága).
- **2026-10-07 — F1, spark-rész (K01F1S) előkészítve és indítva (16:55).**
  - **Eszközök** (`kor01/eszkozok/`):
    - `katalogus_kerdes.py`: T-katalógus. A 14 MASSIVE-pár nélküli eszközre eszközönként 8 stílusban 8-8 magyar
      kérés, szűrve (hossz, az eszköz neve nem szerepelhet, CJK) és dedupolva, eszközönként legfeljebb 50.
      Az itemek a MASSIVE-receptjével (opciószám, közeli párok, 25% gold-drop a `felulvizsgal` párok nélkül).
    - `eu180k.py`: az EU-180k eszközlistái a system promptból, LLM-mel kinyerve (a regex csak a valahol meghívott
      neveket találta meg). Ellenőrzés: a név szó szerint a promptban, a gold a listán, 1–10 eszköz; a párhuzamos
      hívásosak kimaradnak. A train-be csak átnézés után kerülhetnek.
    - `szinonim.py`: a szinonim-eszközszűrés (2. pont). `xdrop`: minden gold-drop item minden opciója
      („teljesíti-e ez az eszköz a kérést?”); ha bármelyik bíráló P(igen) ≥ 0,5, az opció nem rokon eszközre
      cserélődik. `kozeli`: a MASSIVE- és T-katalógus-itemek `felulvizsgal`-párjai; ha a két bíráló átlaga
      ≥ 0,5, az item kétértelmű (soft = {gold, pár}), ha csak az egyiké, jelzést kap az átnézésre. A BFCL és a
      When2Call gold-ja a benchmarké, nem nyúlunk hozzá.
    - `biralo01.py`: címke-előszűrés gold nélkül, a 00 4.8 protokollja szerint (csak triage).
    - `szivargas.py`: bge-m3-as audit a ténylegesen használt train ellen (gold-eszköz és kérés legközelebbi
      train-szomszédja, szó szerinti kérés-duplikátum). Kapu itt nincs, a küszöböket a v1 rögzíti.
    - `k01f1s_vezenylo.sh`: Mistral (generálás, kinyerés, szinonim-bírálat) → Llama (szinonim-bírálat, döntés,
      címke-előszűrés) → Mistral (címke-előszűrés) → szivárgás-audit → fagyasztás-jelölt hash.
  - **Döntések (alapértelmezés, Dani felülírhatja):**
    - **Generátor: Mistral Small 4** (Apache-2.0, a 8. pont szerint). Az alany (Qwen3.6) nem írhatja a saját
      tesztjét. A T-katalógusnál a Mistral így generátor és bíráló is; ezt a rétegnél nagyobb emberi
      mintával ellensúlyozzuk.
    - **Bírálók:** Mistral Small 4 és Llama-3.3-70B, mint a 00-ban.
  - **Lelet a CPU-részből:** 36 item (train 29, val 7) opciólistáján két azonos nevű eszköz áll (az xLAM-forrás
    egy listán két azonos nevű API-t is ad). Az opció-id ütközik, és 5 gold-drop itemen a kivett gold neve a
    listán maradt (hamis X). A `szinonim.py dontes` ezeket kizárja.
  - **Próba a laptopon** (hamis bírálatokkal, másolaton): a döntés kétszer futtatva bájtra azonos; nem marad
    azonos nevű opció, és kivett gold sem kerül vissza.
  - Az `eszkozok/folytat.sh` a `kor01/eszkozok` vezénylőit is megtalálja; a `sync.sh` új parancsai: `to01`,
    `back01`. Az újraindulás utáni folytatás hookja telepítve.
- **2026-10-07 — Összevetés az autotrust/JEV-27B(-VL)-vel (Dani kérése) és döntés.** A JEV ugyanaz az ötlet általános
  célra: döntési LoRA (System 1) és a változatlan bázis (System 2) egy vLLM-motoron, kérésenkénti LoRA-routinggal,
  angolul, egy zárt tanár (TypeSafe Jev 1.13) eloszlásaira desztillálva. Részletek a memóriában és a kártyákon.
  - **Átvesszük (Dani döntése):**
    - 30% opció-permutáció az L3-tanításban: náluk ettől a sorrendre billenés 41%-ról 2,9%-ra esett (5. és 7. pont);
    - egyezés-próba soros és párhuzamos (c = 16) kiolvasás között a H4-ben: náluk a vLLM LoRA-útja 8-nál
      nagyobb kötegben hibás valószínűséget adott;
    - System 1 → System 2 leíró kar (L3→S2): a τ alatti itemek a gondolkodó módhoz kerülnek. Náluk 0,70 alatt
      eszkalálva a pontosság 0,792-ről 0,892-re nőtt, 70%-os gyors ággal.
  - **Nem vesszük át most:**
    - a JEV-27B mint külső alapvonal;
    - a 16 címke (A–P);
    - a tanítható, `lm_head`-ből inicializált döntési fej;
    - a „use when” kontrasztív opcióleírás. Ez náluk +2,5–4,8 pontot hozott; a katalógus közeli párjainál
      később prompt-változatként mérhető.
  - **Amiben a mi mérésünk többet mond:**
    - explicit „egyik sem” címke (náluk nincs);
    - kalibráció valódi címkén (az ő 0,0009-es ECE-jük a tanárhoz mért hűség);
    - kitartott rétegek és előregisztráció;
    - a System 2 változatlanságát ők csak PyTorch-úton mérték, vLLM-ben `--enable-lora` mellett nem (a mi H3(d)
      leletünk, 00 Napló).
- **2026-10-07 — K01F1S kész (16:55–20:02).** Az eredmények lent (`sync.sh back01`), a hook eltávolítva.
  - **T-katalógus:** 647 kérés (a 896 tervezettből). A 112 (eszköz, stílus) hívásból 25 nem adott használható
    listát: a modell valószínűleg más JSON-kulccsal válaszolt, a feldolgozó üres listának vette, hibát nem jelzett.
    Eszközönként 24–50 kérés (`set_reminder` 24, `book_restaurant` 37). 647 item, ebből 159 gold-drop X.
  - **EU-180k:** 113 item (71 X). 17 párhuzamos hívásos és 6 hibás eszközszámú kimaradt.
  - **Szinonim-szűrés** (23 814 pár; Mistral 9,2 pár/s, Llama 12 pár/s):
    - a gold-drop opciókra Mistral 1018, Llama 636 igen, a kettő közös része kb. 400;
    - a „bármelyik igen” szabállyal cserélt opció: train 590, val 240, teszt 330, T-katalógus 86;
    - a közeli párok miatt kétértelmű: train 131, val 80, teszt 94; csak az egyik bíráló szerint jelzett: 56 / 36 / 34;
    - kizárva az azonos nevű opció miatt: train 29, val 7.
  - **Címke-előszűrés:** a val, a teszt, a T-katalógus és az EU-180k összes itemjére mindkét bíráló válaszolt (a
    Mistral egy val-itemnél hibázott).
  - **Szivárgás-audit** (a ténylegesen használt, szűrt train ellen; bge-m3):
    - **MASSIVE hu teszt:** 108 kérés szó szerint a train-ben is szerepel (3,6%), 279-nél a koszinusz ≥ 0,95. Ez a
      MASSIVE sablonos mondatainak sajátja (a hivatalos split). A v1-ben döntendő: kizárás vagy külön jelentés.
    - **T-katalógus:** egy kérésnél sincs koszinusz ≥ 0,90; a 14 eszköz a train-ben csak zavaró opcióként fordul elő
      (tervezett).
    - **val-xlam:** 17 item gold-jának neve egy train-opcióéval azonos. A kitartás azonosító szerint történt, az
      xLAM-ban pedig van több azonos nevű API. A T-új-eszköz szűrése a v1-ben név szerint is menjen.
    - BFCL / When2Call: gold-név az xLAM-train-ben 23 / 6 / 24 / 12 / 70 itemnél (simple / multiple / live_simple /
      live_multiple / W2C); ezek a T-új-eszközből kiesnek.
  - **Átnézési minta** (`atnezes01.py`, `adat/f1s/atnezes/`): 377 item.
    - Rétegenként: val-xlam 51, val-massive 80, T-hu 100, T-katalógus 91, EU-180k 55.
    - Szintenként: konszenzus 97, szinonim-jelzés 30, véletlen 250.
    - **Lelet:** az EU-180k 113 itemjéből 44-nél mindkét bíráló magabiztosan mást mond, mint a gold. A mintában
      mind X-gold volt (`fara_apel` 12, `refuz_politicos` 7, …), és a kérésre a listán van illő eszköz. Például:
      „milyen az időjárás Budapesten ma?” → `get_weather`, a gold mégis X. A forrás ezekkel a beszélgetés
      stílusát címkézi (hívás nélküli vagy elutasító válasz), nem azt, hogy nincs illő eszköz.
    - **Döntés (alapértelmezés):** az EU-180k X-itemjei (71) kimaradnak a train-kiegészítésből és az átnézésből.
      Csak a 42 hívásos item marad, átnézés után.
    - **A minta így:** 352 item (val-xlam 51, val-massive 80, T-hu 100, T-katalógus 91, EU-180k 30).
    - **Felület:** `adat/f1s/atnezes/atnezo.html`, másolat: `~/Letöltések/atnezo-01.html`.
- **2026-10-07 — Címke-átnézés, 1. adag (export 20:51; a kitöltő gépi ágens volt, ld. a 2. adag bejegyzését): a
  kapu bukott.** 352/352 döntés
  (`adat/f1s/atnezes/dontesek.json`, `osszesites.json`).
  - **Becsült címkezaj:** val-xlam ~0,1%; val-massive ~4%; **T-hu ~10%** (a véletlen nem-X minta 12%-a hibás);
    T-katalógus ~5% (főleg homályos kérés → kétértelmű); EU-180k (hívásos) 3/30.
  - **A teszt maradék zaja:** pont 7,1%, felső95 11,0%; a kapu ≤ 2%.
  - **A hibák:** a MASSIVE-rétegek 34 hibájából 23 hat intentből jön (`qa_definition` 6/9: „mesélj X-ről”, a
    `web_search` a jó; `general_quirky` 5/11: nem csevegés, hanem keresés; `calendar_set` 5/19; `news_query` 3/7;
    `email_query` 2/11; `datetime_query` 2/5: ünnepnap → `get_holidays`). A többi intenten is ~11% (5/45): a
    MASSIVE saját zaja (egyszavas vagy értelmetlen fordítások, kétes intent).
  - **Bírálói szűrés nem elég:** ahol mindkét bíráló egyetért a golddal, ott is 2/32 a hiba, és a T-hu itemjeinek
    felénél legalább az egyik eltér. A szűrés a tesztet a „bírálónak könnyű” itemek felé torzítaná.
  - **Döntés (Dani):**
    - **T-hu:** egy 600 itemes egyszerű véletlen minta a pontozott T-hu-ból, mindet Dani nézi át; a H2 T-hu rétege
      ez a részhalmaz (`meta.t_hu_atnezett`). A többi MASSIVE-teszt leíró marad.
    - **T-katalógus:** mind a 647 item átnézve.
  - **2. adag** (`atnezes01.py potadag`, seed 20261010): 1127 új item (T-hu 571, T-katalógus 556). Az 1. adagból
    29 T-hu és 91 T-katalógus döntés átjön. Felület: `atnezo_adag2.html`, másolat:
    `~/Letöltések/atnezo-01-adag2.html`. Az 1. adag HT-becslése változatlan (csak az 1. adag rekordjain).
- **2026-10-07 — Címke-átnézés, 2. adag (export 21:14): kész, de mindkét adag gépi átnézés.**
  1127/1127 döntés (`adat/f1s/atnezes/dontesek_adag2.json`; az 1. adag ágens-jegyzete:
  `dontesek_adag1_jegyzet.md`).
  - **Ki töltötte ki:**
    - A 2. adag exportjának `meta.kitolto` mezője szerint „ChatGPT / Codex”. A saját megjegyzése szerint nem teljesen
      vak: az első forrásbeolvasáskor a tárolt címkék is látszottak, az érintett itemek köre nem ismert.
    - Az 1. adag időbélyegei pontosan 1 másodpercenként követik egymást, a mellékelt jegyzet pedig szerint a felületet
      nem tudta megnyitni, ezért „az exportot ugyanabban a formátumban állította elő”. Ez is gépi kitöltés.
    - Összevetésként a 00-ás kör átnézése emberi: 150 döntés 12,5 perc alatt, szabálytalan közökkel (medián 4,4 s).
  - **Eredmény** (`osszesit`, a két adag együtt):
    - **T-hu-részhalmaz (600):** 42 hibás gold (7,0%), 35 kétértelmű, 7 rossz kérés; javítás előtti zaj 12,8%.
    - **T-katalógus (647):** 13 hibás gold (2,0%), 32 kétértelmű, 11 rossz kérés; javítás előtti zaj 7,0%.
    - 174 javítás összesen. A `kapu_ok_teljes` gépiesen igaz, mert minden item el van döntve.
  - **Horgonyhatás jele nincs:**
    - A (részben nem vak) 2. adag több zajt talált, mint az 1. adag véletlen „többi” cellái.
    - T-hu: 12,8% vs. 10%; T-katalógus: 7,2% vs. 5%.
  - **Ami ebből nem következik:**
    - Teljes átnézésnél a maradék zaj az átnéző tévedési aránya. A tervezett kapu ezt emberi átnézővel ~0-nak
      vette. Egy GPT-átnézőnél ez az arány nincs megmérve, így a ≤ 2%-os kapu jelenleg nem igazolt.
    - Licenc: ha egy zárt (OpenAI) modell javította címke a tanítóadatba kerül, az ütközik az „Apache-2.0 generátor”
      elvvel (8. pont). Ez érinti az EU-180k beolvasztását (2 javítás, 1 kétértelmű); a val-massive 9 javítása
      csak kalibrációs adat.
  - **Döntés (Dani): emberi vak szúrópróba** a gépi átnézésre (`atnezes01.py szuro`, seed 20261011).
    - **A minta, 221 item:**
      - minden gépi címkejavítás (70: T-hu 46, T-katalógus 13, val-massive 9, EU-180k 2), plusz az EU-180k gépi
        kétértelmű-ítélete (1);
      - 150 egyszerű véletlen item a teljesen átnézett tesztrétegek gépileg változatlanul hagyott itemjeiből
        (pool 1107).
    - **Felület:** `atnezo_szuro.html`, másolat: `~/Letöltések/atnezo-01-szuro.html`. A tárolt címke a gépi javítás
      utáni, a gépi javításnál az eredeti is. Mindkettő csak Dani vak válasza után látszik.
    - **Értékelés:** `szuro_osszesit`.
      - Dani a referencia; a javítások forrása `gepi` / `gepi+dani` / `dani`, a `meta.atnezes.forras` mezőben.
      - Mért mennyiségek: a gépi javítások pontossága és a változatlan cella hibaaránya.
      - A teszt maradék zaja a szúrópróbán kívüli változatlan itemekből (zaj = hibás + kétértelmű + rossz kérés).
    - **Kapu:** felső95 ≤ 2%.
      - A próbaszámítás szerint ez 150-ből 0 hibánál teljesül, 1 hibánál már nem (2,2%).
      - Ha van hiba: +150 véletlen item; 300-ból 3 hibáig teljesül (4 hibánál 2,07%).
    - **EU-180k:** mind a 3 gépi döntés a szúrópróbában van, így a trainbe csak Dani-döntés kerül.
    - **A tesztet érintő maradék torzítás:** a gépi kétértelmű (67) és rossz kérés (18) ítéletek nincsenek
      szúrópróbázva. Ezek az itemek kikerülnek a pontozásból, ami a tesztet a könnyebb itemek felé tolhatja. A
      tanulmányban külön jelentendő.
- **2026-10-07 — Llama-licenc: a szűrés nem tanítás (Dani).**
  - **A felvetés** (a `magyar-dontesi-tanitoanyag-otletek.md` átnézésekor): a licencjegyzet „csak triage” alapon
    zárta le a Llama-kérdést, de a Llama ítélete a tanítóadatot is alakította:
    - a 00 S7 duplikátumszűrésében: mely cikk nem lehet opció, és melyik értelmetlen nevű cikk esik ki;
    - a 01 `xdrop` szinonimaszűrésében: melyik opció cserélődik.
  - **Döntés:** a bírálói szűrés és kiválasztás nem a kimenet tanításra való felhasználása. A 00 publikált
    kiadása marad, ahogy van; a 01-ben sem változtatunk.
  - **Továbbvitel (03):** Llama szűrhet és jelölhet ki itemet, de a kimenete soha nem lehet címke és nem lehet
    soft target.
- **2026-10-07 — Vak szúrópróba, 1. kör (export 21:51): a kapu bukott, pótminta.**
  - **Bevitel:** a 221 döntés időbélyege pontosan 1,000 s-onként követi egymást (3,7 perc), vagyis nem a felületen
    kattintva készült. Dani szerint a döntések az övéi, csak a bevitel ment gépen. Így értékeljük
    (`adat/f1s/atnezes/dontesek_szuro.json`), a `forras: dani` jelölés ezen a nyilatkozaton áll.
  - **Eredmény** (`szuro_osszesit`):
    - a GPT 70 címkejavításából 61 megerősítve (87%, CP95 [77; 94]), 2 hibás és visszaállítva, 7 kétértelmű;
    - az EU-180k gépi kétértelmű-ítélete Dani szerint is kétértelmű;
    - a gépileg változatlan itemekből 148/150 megerősítve, 2 kétértelmű.
  - **Kapu:** a maradék zaj pontbecslése 1,2%, felső95 3,1% > 2% → bukott.
  - **Pótminta** (`szuro_potminta`): +150 item ugyanannak a keverésnek a folytatásából (T-hu 73, T-katalógus 77).
    Az első és a pótminta együtt egyetlen 300-as egyszerű véletlen minta. A reprodukciót a parancs ellenőrzi.
    - Felület: `atnezo_szuro2.html`, másolat: `~/Letöltések/atnezo-01-szuro2.html`, export:
      `dontesek-szuro2.json`.
    - **Kapu a 300-as mintán:** legfeljebb 3 zajos item fér bele (1,73%; 4 zajos itemnél 2,08%). Mivel már 2 van,
      a pótmintában legfeljebb 1 lehet.
- **2026-10-07 — Vak szúrópróba, 2. kör, és az F1S fagyasztása (22:0x).**
  - **Bevitel:** a pótminta döntéseit is gép vitte be (150 döntés, pontosan 1,000 s-onként); a döntések Danié, mint
    az 1. körben.
  - **Eredmény:** a pótmintában 2 kétértelmű és 1 hibás címke. A 300-as mintán együtt 5/300 (1,7%, CP95
    [0,5; 3,8]).
  - **Kapu:** a teszt maradék zaja pont 1,2%, felső95 2,43% > 2%, tehát **bukott.**
  - **Döntés (Dani): elfogadjuk, korlátként jelentjük.**
    - A tanulmányban: „a tesztcímkéket GPT-modell nézte át teljesen, emberi vak szúrópróbával auditálva (300
      változatlan + 70 gépi javítás); a becsült maradék zaj 1,2% (felső95 2,4%); a GPT-javítások 87%-a megerősítve”.
    - Külön jelentendő, hogy a gépi kétértelmű és rossz-kérés ítéletek nincsenek auditálva.
  - **Alkalmazás:** `alkalmaz --javitasok adat/f1s/atnezes/javitasok_vegleges.jsonl`.
    - 62 javítás, 95 kétértelmű, 20 kizárva.
    - Az EU-180k 71 forrás-X-e kimarad a train-extra fájlból (az `alkalmaz` új szabálya).
    - Forrásjelölés a `meta.atnezes.forras`-ban: gepi 83, gepi+dani 61, dani 13. A `gepi` csak kétértelmű- és
      kizár-ítélet, illetve val-réteg; javítás csak `gepi+dani` vagy `dani`.
  - **A befagyasztott H2-rétegek:**
    - **T-hu-részhalmaz:** 593 item (7 kizárva), 553 pontozott, ebből 192 X (35%).
    - **T-katalógus:** 636 item, 598 pontozott, 160 X (27%).
    - **EU-180k train-extra:** 42 item, 41 pontozott.
    - ⚠️ A T-hu X-aránya magasabb a 00-ás 25%-nál. A 00 szerint a nyereség az X-aránnyal skálázódik, ezért a H2-ben
      az X-arány szerinti rétegzett jelentés kell (a v1-ben rögzítendő).
  - **Fagyasztás:** `adat/f1s/atnezes/fagyasztas.sha256` + `FAGYASZTVA.json`.
    - items_train `6eb6966e…`, items_val `5424f165…`, items_teszt `2e836a33…`, items_katalogus `092132308c…`,
      items_eu180k `14979ecd…`.
    - A measurement-host fájljai a felküldés előtt bájtra egyeztek a helyi `*.pre_atnezes` mentésekkel. Felküldés után
      `sha256sum -c` OK.
  - **Következik:** a 01 v1 rögzítése (hipotézisek, végpontok, MDE, a T-hu X-arány kezelése), utána az F2.
- **2026-10-07 — K01F3-pilot éjszakai lánc indítva (measurement-host, 22:11).** `kor01/eszkozok/k01f3_vezenylo.sh pilot`.
  - Leválasztva fut (setsid + nohup, PPID 1). A reboot-hook újra telepítve (`reboot_hook.sh install`), az
    `AKTIV_FAZIS` alapján a `folytat.sh` viszi tovább.
  - **Lépések:**
    1. fagyasztás-ellenőrzés;
    2. `tren_lora --selftest` 01-es itemeken (döntési pozíció);
    3. 2 lépéses smoke (perm-aug, vLLM-export);
    4. **L3 seed 1** (`k01_l3mixse_p30_s1`): a 00 győztes receptje (mix+se, ε = 0,05, r16, lr 1e-4, 1 epoch) + 30%
       opció-permutáció. A train az `items_train` és az EU-180k train-extra, 14 513 item;
    5. egy LoRA-s vLLM-példányon a val (3524 item) kiolvasása az adapterrel és a bázissal, 4 permutáció, sorosan;
    6. HF-kiolvasás az adapterrel a val-on (perm 0, motor-hűség).
  - **A teszten semmi nem fut,** mert a v1 még nincs rögzítve. A tréning és a val-kiolvasás a runbook 7. pontja
    szerint F3/F2-anyag, a hipotézisektől független.
  - **Kódváltozások:**
    - `common.messages_for`: `request` mezős (01-es) itemekre a `kor01/eszkozok/keret.py` keretét használja,
      fájlútról betöltve. A 00-ás itemekben nincs `request`, ezeknél a viselkedés változatlan;
    - `tren_lora.py`: `--perm-aug` (seedelt, perm-id 1000 + epoch, az értékelő 0–3-tól külön) és vesszős
      `--train`.
  - **Becsült idő:** a 00-ás tréning 5593 itemen 2,06 óra volt (~2,7 ezer item/óra), ebből a tréning ~5,5 óra;
    a vLLM-kiolvasás 2 × ~40 perc; a HF ~30–60 perc. Várható vége ~06:00–07:00.
- **2026-10-08 — K01F3-pilot kész (04:51): az L3 a val plafonján ül, így hangolás nincs; a seed 2–3 elindult.**
  - **Futás:**
    - a tréning 22:29–03:04 tartott (15 987 s, 908 lépés, 14 513 item), a veszteség 0,50 → 0,32;
    - vLLM-kiolvasás: 2 × 14 096 sor, ~34 perc kiolvasásonként;
    - HF perm 0: 2,6 item/s.
  - **Val-elemzés** (`kor01/eszkozok/f3_val01.py`, a 00 `elemzes.py` függvényeivel; a τ a val-on választva, ezért
    a lefedettség in-sample). Eredmény: `kor01/eredmenyek/F3/k01_l3mixse_p30_s1/val_elemzes.json`.

    | | lef@95 | AURC | ECE | pontosság | X-fedés |
    |---|---|---|---|---|---|
    | plafon (a pontozott nem-X itemek aránya) | 0,729 | | | | |
    | bázis, L1★ = `perm_avg` (T = 1,37) | 0,682 | 0,0059 | 0,018 | 0,919 | 0,955 |
    | **L3 s1, `temp`** (T = 0,80) | **0,724** | **0,0026** | 0,024 | 0,953 | 0,959 |

    - Az L3 a plafon 99,3%-án ül (xLAM 0,749/0,751, MASSIVE 0,705/0,711).
    - A bázis is erős, a plafon 93,6%-án.
    - Top-címke-átváltás L1★ → L3: rosszból jó 157, jóból rossz 38.
    - HF ↔ vLLM top-egyezés (perm 0): 99,3%.
  - **Lelet:** a „szándékosan nehéz” val sem elég nehéz, ugyanaz a plafonhatás, mint a 00-ban. A val a karok közt nem
    tud dönteni, a nyereség a tesztrétegeken (BFCL-live, T-hu, T-katalógus, T-új-eszköz) és az AURC-n mérhető. Ezt a
    v1-ben a végpontoknál figyelembe kell venni.
  - **Döntés (a runbook 7. pontja szerint, előre rögzített szabály):** „a hangolás csak akkor, ha a val nem ül a
    plafonon” → nincs hangolás. A seed 2 és 3 ugyanazzal a recepttel indult (`k01f3_vezenylo.sh megerosites`, 06:28).
    - A seed 2 tréningje várhatóan 11:03-ig tart.
    - A két seed kiolvasásokkal együtt ~17:30–18:00-ra lesz kész.
- **2026-10-08 — v1 rögzítve, a teszt érintése előtt.** Átírt szakaszok: fejléc, 4., 5. (karok), 6., 7., 8.
  (publikálási szabály), 9., 10. A rögzítés előtti v0.1 szó szerint: `jegyzokonyv/2026-10-08-01-runbook-v0.1.md`.
  - **Dani döntései:**
    - H1-pool: minden réteg (7561 item, ~4170 klaszter);
    - H2: a 00 szerinti háromértékű ítélet a Δ lef@95-ön;
    - H2-rétegek: a T-BFCL-live (a When2Call alrétegével) és a T-hu; a T-új-eszköz és a T-katalógus leíró;
    - publikálás: az adapter publikus, ha a H1 igaz és a H2 mindkét rétegen „általánosít”.
  - **Alapértelmezések:**
    - L1★ = `perm_avg`, L3-kar = `temp`;
    - a T-hu elsődlegesen mind az 553 itemen, a 46 közel-duplikátum nélkül érzékenységként;
    - a H4 a val-on, c = 1 és c = 16 mellett;
    - X-arány-standardizált Δ (25%, 10%) másodlagosként.
  - **MDE** (`kor01/eszkozok/mde01.py`, pilot val, 1000 replika): lef@95 pool 2,0 / T-BFCL-live 2,2 /
    T-hu 3,2 pont; AURC 0,0018 / 0,0025 / 0,0049; a τ-rész 72%.
  - **Hátravan az F4 előtt (F2):** L0n natív kiolvasó, a T-új-eszköz X-része, a bootstrap-elemző a 01
    rétegeire, a H4 c = 16 kiolvasó.
- **2026-10-08 — F2-eszközök kész, az F4-lánc élesítve.**
  - **Új eszközök** (`kor01/eszkozok/`):
    - `l0n_kiolvaso.py`: natív tool calling. A prompt offline renderelve a modell saját template-jével
      (`tools`, thinking ki), a nyers kimenetből parszolva (Qwen3.6: `<tool_call>` → `<function=NÉV>`).
      Az eszközséma: név, leírás, kötelező paraméterek string típussal, vagyis ugyanaz, amit az L3 kap.
      c = 16, legfeljebb 256 token. Diagnosztika: `p_call0`. A measurement-hosten CPU-n kipróbálva: a prompt és a
      parszolás helyes, a `<tool_call>` egytokenes (248058).
    - `s2_kiolvaso.py`: L3→S2. A τ@95 és a temperature az L3 s1 F4-es val-kiolvasásából; csak a pontozott
      pool τ alatti itemjei; thinkinggel, c = 16. A pilot val-on ugyanazt a T = 0,80 / τ = 0,376-ot adja, és
      27%-ot választ ki.
    - `szivargas.py --uj-eszkoz-x`: a T-új-eszköz tagsága X- és nem-X itemekre, a tényleges train ellen.
    - `h4_egyezes.py`: a H4 ítélete, itemenként párosított bootstrappal.
    - `f4_elemzes01.py`: a 00 `f4_elemzes.py` vektorizált építőelemeivel, H1–H5, a leíró rétegek, az
      X-standardizálás, az S2, az ismétlési zaj és a permutációs billenés. Szintetikus kiolvasásokon
      végigfut, a rétegméretek egyeznek a v1-gyel (pool 7561, T-hu 553 / közel-duplikátumok nélkül 507).
  - **Infrastruktúra:**
    - `lanc.sh`: a `kor01/eszkozok` alatti vezénylőket is megtalálja (mint a `folytat.sh`);
    - `f3_val01.py --bazis`: a seed 2–3 a pilot bázis-kiolvasását használja.
  - **Lánc a measurement-hosten:** `lanc.sh K01F3-megerosites K01F4-smoke` és `lanc.sh K01F4-smoke K01F4-teszt`.
    - **Smoke** (a val-on, a teszt érintése nélkül): adapter be/ki (s1, s2; az eltérő logprob igazolja a
      cserét), L0n 40 itemen, S2 8 itemen, két adapter + párhuzamos kiolvasás. Ha bukik, a teszt nem indul.
    - **Teszt:** seed-őr (minden seed val-lef@95-je > L1★) → T-új-eszköz → fő példány (~6,4 óra) → L0n, S2
      (nem végzetes) → H4 (nem végzetes). Várhatóan ~10 óra.
- **2026-10-09 — F4 kész: a H1 cáfolt; a publikálási szabály „H1 bukik” sora érvényes.**
  - **Futás:** a seed 3 18:03-kor, a smoke 18:15-kor, a teszt 03:15-kor végzett, hiba nélkül. A hash-ellenőrzés
    minden itemfájlra OK. Elemzés: `f4_elemzes01.py` 10 000 replikával; lap: `kor01/eszkozok/f4_riport01.py` →
    [eredménylap](kor01/eredmenyek/F4/eredmenylap.md). A kézi értelmezés (`ertelmezes.md`) a generált lap végére
    kerül.
  - **Ítéletek:**
    - **H1 cáfolt**, mindkét végponton.
      - lef@95: Δ = +4,9 pont [3,6; 6,6], de mindhárom seed precizitás-bukott a poolon (0,83–0,85; L1★ 0,88);
      - AURC: Δ = +0,028 [0,022; 0,034], az L1★ javára.
    - **H2:** a definíció szerint mindkét rétegen „általánosít” (T-BFCL-live + W2C +5,3 pont, T-hu +5,1 pont).
      A definíció nem tartalmaz precizitási feltételt, így ez félrevezető; a H1 nélkül nincs rá épülő állítás.
      A 03-ban a rétegítélet már precizitáshoz kötött.
    - **H3 igaz:** az L0n munkapontján +3,4 pont precizitás, +7,4 pont lefedettség. Az X-fedés viszont 6,3 ponttal
      rosszabb, mint a natív tool callingé.
    - **H4 igaz:** mind a négy feltétel; a Δ alsó korlátja ≥ −0,7 pont.
    - **H5 cáfolt:** X-fedés −8,9 pont [−11,4; −6,3], nem-X pontosság +1,4 pont.
  - **Mechanizmus** (leíró, utólagos; részletek az eredménylapon):
    - a nem-X itemeken az L3 szinte hibátlan;
    - a teljes precizitásesés a valódi irrelevancia magabiztos eszközhöz rendeléséből jön (BFCL-live irrelevance
      @95: 43–48% vs. 33%). A train X-e zömmel gold-drop volt;
    - a T-hu 40 átcímkézett itemjéből az L3 18–24-nél a régi MASSIVE-címkét adja, mindet a τ fölött; nélkülük a T-hu-n
      is jobb;
    - közös lefedettségen is az L3 kockázata a nagyobb, tehát nem a görbehossz műterméke;
    - a val-τ a kalibrált bázisnál sem tartja a 95%-ot a teszten (0,88).
  - **L3→S2:** a τ alatti 1743 item 96%-a X-gold, és az S2 ezek 95%-ánál helyesen X-et mond. A magabiztos hibák
    viszont a τ fölött vannak, így az S2 elé sem jutnak.
  - **Összevetés a JEV-27B-vel** (eredménylap, `ertelmezes.md`): a JEV puha célokkal tanít, nincs X-opciója, és a
    kalibrált bázissal nem hasonlít össze; a két eredmény összefér. A tanulságok a 03-runbook v0.2-be kerültek
    (Dani jóváhagyásával): puha keverék-cél Apache-2.0 tanártól (Mistral Small 4, Gemma 4 26B-A4B-it), négy
    X-típus, bázis-horgony, célréteg-kalibráció.
  - **`autotrust/jev-decision-index-results`** (Apache-2.0; átnézve 2026-10-09):
    - csak a JEV-motorok itemenkénti válaszai és valószínűségei vannak benne, bemenet és gold nélkül;
    - tanításra nem használható: a benchmarkok eval-készletek, a valószínűségek pedig a zárt Jev desztillációjából
      származnak (03, 3.3 és 3.6);
    - külső összevetésre viszont értékes. A CLINC150+OOS és a When2Call MCQ itemjei a kittel (MIT) újraépíthetők,
      és a JEV-27B ezeket nem látta tanításkor. Így mérhető a puha célú recept irrelevancia-kezelése, és a JEV-27B
      a mi kalibrált bázisunkkal ugyanazokon az itemeken összevethető (F5b, javaslat);
    - a JEV-Gemma4-26B-A4B ezeknek a benchmarkoknak a train-splitjén is tanult, ezért ott nem kitartott;
    - a BFCL-sávjuk eszközönkénti igen/nem, irrelevancia-kategória nélkül.
- **2026-10-09 — F5b kész: a puha célú JEV sem kerüli el az irrelevancia-csapdát.**
  - **Bemenet:** `autotrust/jev-decision-index-results` (Apache-2.0). A gold a kit (MIT, a JEV-futás commitja
    87d4650, tarballból) építőivel azonos módon, a rögzített forrásokból (sha256 egyezik). A JEV közölt pontosságai
    mindkét sávon, mindhárom modellnél pontosan visszajönnek.
  - **When2Call, a 01 tesztjének ugyanazon 2328 itemjén** (tool_call és cannot_answer): a hívás/nem hívás
    szétválasztása (AUROC):
    - L1★ 0,964;
    - L3 0,945–0,959;
    - JEV-9B 0,953, JEV-27B 0,949, JEV-Gemma4 0,943.

    A hamis hívás 95%-os helyes hívás mellett: L1★ 14%, L3 16–17%, JEV 33–37%. A JEV-27B alacsony nyers
    hívásaránya a cannot_answer itemeken (6%) óvatosabb munkapont: a jó hívások 13%-át is elmulasztja.
  - **CLINC150+OOS:** az OOS top-1 felismerése:
    - JEV-9B 21%;
    - JEV-27B 38%, miközben a hatókörön belüli pontossága 89%;
    - JEV-Gemma4 67% (az OOS-t is tanulta).
  - **Következtetés:**
    - a puha cél önmagában nem védi ki az irrelevancia-csapdát;
    - az X-típus tanítása segíthet (CLINC-OOS: JEV-Gemma4 38 → 67%), de a When2Call-on nem elég. Az L3 a
      When2Call-trainen is tanult (499 cannot_answer, a train-X 13%-a), a JEV-Gemma4 a teljes train-spliten, és
      egyik sem éri el a bázist. A When2Call-összevetésben ezért csak a JEV-27B és a JEV-9B kitartott;
    - a hívás/nem hívás szétválasztásában a kalibrált bázis a legjobb, ami a 03 bázis-horgonyát alátámasztja.

    Az eredménylap értelmezése és a 03-runbook ennek megfelelően frissítve.
  - **Kétlépcsős próba** (utólagos, leíró; az eredménylapon):
    - ha a hívjon-e kérdést a bázis P(X)-e dönti el és az eszközt az L3, az X-fedés a bázis szintjén marad (0,762);
    - a lef@95 viszont csak ~1 ponttal nő (0,726 vs. 0,717), és a val-τ precizitása így is bukik.
  - **Mellékes:** a hook (`pre-bash-guard.sh`) a `docai-labs` alatti relatív `cd`/`-C` célpontokat tévesen tiltotta.
    Javítva, Dani jóváhagyásával: a célpontok feloldva és normalizálva, 19 tesztesettel; a régi `.bak-2026-10-09`.
- **2026-10-09 — Publikálás és tanulság (Dani).**
  - **Az adapter nem publikus**, az előre rögzített szabály szerint. Mellette szólt, hogy a When2Call-szétválasztásban
    a JEV-27B szintjén van. Ez azonban egyetlen mérés, eltérő keretben, és az L3 a When2Call-trainen is tanult. A
    kitartott teszten a kalibrált bázis jobb vagy egyenlő. A natív tool callinggal szembeni előny is főleg a
    kiolvasási módszeré: az L0n munkapontján az L1★ +5,7 pont precizitást és +5,1 pont lefedettséget ad, az L3 +3,4,
    illetve +7,8 pontot.
  - **Publikus:** a tanulmány (a 00-val közösen, a docai.hu `/kutatas` rovatában és üzleti blogposztként), az
    adatkészlet és az itemenkénti kiolvasások.
  - **Tanulság (Dani):** ott érdemes tanítani, ahol a bázis gyenge.
    - A 00-ban a bázisnak volt hová fejlődnie: lef@95 0,616, plafon 0,756, X-fedés 0,43. Az L3 nyert (+13,7 pont).
    - A 01-ben a bázis a nem-X eszközválasztásban eleve szinte hibátlan volt, a hívás/nem hívás AUROC-ja 0,964.
      Az L3 csak az eloszláson belül nyert, a kitartott teszten rontott.
    - Valószínű ok: a bázist (Qwen3.6) kifejezetten tool callingra is tanították, számlasor → cikk besorolásra nem.
- **2026-10-09 — A közös (00 + 01) tanulmány a docai_web-en, lokálisan kész, deploy és commit nélkül.**
  - **Kutatási jelentés:** `/kutatas/hol-erdemes-tanitani`, „Hol érdemes döntésre tanítani a modellt?”, 12
    fejezet + apparátus (`resources/views/kutatas/hol-erdemes-tanitani.blade.php`, `ResearchController::whereToTrain`).
  - **Blogposzt** (az üzleti változat, a `new-blogpost` skill szerint): `/blog/hol-erdemes-tanitani` és
    `/en/blog/where-to-train-the-model` (`BlogController` `wheretotrain`). A kettő kölcsönösen hivatkozik
    egymásra; a poszt az október 5-i döntésimodell-cikk ígéretét váltja be.
  - **Ellenőrzés:** a hat érintett URL 200-at ad; a 41 teszt zöld; a sitemap újragenerálva és érvényes; vizuálisan
    asztalon és mobilon rendben.
  - **Nyitott:** a hivatkozott `docai-evals/experiments/2026-10-09-decision-lora-where-to-train-gb10` mappa még nem
    létezik (a link addig 404). Hozzá Dani döntése kell a T-hu `forras: gepi` címkéiről. A commitot és a deployt Dani
    kezeli.
- **2026-10-09 — A docai-evals mérési csomag összeállítva (`experiments/2026-10-09-decision-lora-where-to-train-gb10`,
  commit nélkül).**
  - **Szerkezet** (a CJK-kör mintájára; forrás: `publikacio/docai-evals/`, csomagoló:
    `eszkozok/docai_evals_csomag.py`):
    - `protocol/`: a két runbook, a v0.1-es vázlat, két jegyzőkönyv és az F4-értelmezés, kitakarva;
    - `code/`: `eszkozok/`, `kor01/eszkozok/` és `verify_package.py`;
    - `dataset/`: r00 = a HF három kiértékelő splitje, r01 = magyar teljes sorok + hivatkozási sorok + katalógus;
    - `results/`: eredménylapok, elemzések, H4, F3, F5b, a két kör itemenkénti kiolvasásai;
    - mellette README (EN), eval-card, decision-record, `corpus_manifest.json`.
    - Mérete 24 MB, 173 fájl. A gyökér-README, a README.hu és a `docs/blog-index.md` egy-egy sorral bővült.
  - **A `forras: gepi` címkék** a 8. pont előírása szerint jelölve kerülnek be, nem Dani-döntésre várva.
    - A gépi-only bejegyzések mind kétértelmű-jelölések, ezért nem pontozottak.
    - Minden címkejavítás emberi megerősítésű (`gepi+dani` vagy `dani`).
  - **Hivatkozási sorok:** a BFCL, a When2Call és az xLAM sorai csak azonosítóval, sha256-tal és álnevesített
    eszköznévvel kerülnek be. Az álnév képlete: `t_` + sha256(só + név)[:12].
    - Ok: a BFCL a 8. pont szerint csak teszt; a When2Call-teszt BFCL-live-ból épült; az xLAM DeepSeek-V2
      generátor-licence nincs ellenőrizve.
    - A kiolvasások ugyanazt az álnevet viselik.
  - **Kitakarás:**
    - a tenant neve és adatbázisa;
    - az ügyfél-azonosító alkategórianév (00 Napló, 2026-10-04);
    - termékkód-útvonalak;
    - gépnevek.
    - Az `auditok.py` valószerűségi auditjában a termék-sémát mutató SQL helyett fájlbeolvasás áll.
    - Kimarad a `tenant_profil.py`, a `sync.sh`, a `reboot_hook.sh`, a licenc- és szerződésjegyzet és a backlog-jegyzet.
    - A csomagoló tiltottminta-ellenőrzése üres.
  - **Ellenőrzés:**
    - `code/verify_package.py` a publikált kiolvasásokból újraszámolja mindkét kör L0/L1★/L3 pontbecsléseit;
      1491 közölt számból 0 tér el (1e-9).
    - A manifest-hash-ek, a HF-manifest és az eval-card séma (`--strict`) is rendben.
  - **Javítás a docai_web-en:** a jelentés melléklete az 1. kör adatkészletét Apache-2.0-nak írta; helyesen
    CC-BY-4.0 (az adapter Apache-2.0). A melléklet a bővebb csomagtartalmat is leírja.
  - **Nyitott:**
    - a docai-evals és a docai_web commitja, deployja (Dani);
    - commit után `php artisan sitemap:generate`;
    - az xLAM generátor-licencének ellenőrzése, a 01 HF-adatkártyája előtt.
