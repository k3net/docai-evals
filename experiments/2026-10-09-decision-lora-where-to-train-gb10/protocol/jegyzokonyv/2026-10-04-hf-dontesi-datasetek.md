# HF-adatkészletek egy általános döntési modellhez — felmérés (2026-10-04)

Cél: kész, nyilvános tanítóadat egy általános, publikálható döntési modellhez (SystemOne-stílus: egy
állapoton több kérdés, `choice` / `noul` / `score`, „egyik sem” / X, kalibrált bizalom), amelyből HF-re
kiadható adapter tanítható.

**Források:**
- saját felmérés: HF API-tagek és kártyák;
- külső kutatási anyag: [open_datasets_research.md](../open_datasets_research.md), a SystemOne-korpuszokkal
  és a magyar készletekkel.

Az alábbi licenceket és méreteket a HF API-n ellenőriztük, kivéve, ahol a sor mást jelöl. Szúrópróba a
kártyákon: esci, MILQA, HelpSteer3, clinc_oos, massive, HuRC, zeshel, a tasksource-korpusz és a
`synthetic-typed-decisions`.

## Fő megállapítások

1. **Létezik kész SystemOne-formátumú döntési korpusz,** ez a gerinc. A `tasksource/tasksource-jev-typed-decisions`
   ~2,5 M sor 670 forrásból, `choice` / `score` / `noul` típussal. Minden sorban ott a forrás licence és egy
   `license_use` mező (`commercial` / `non-commercial` / `unspecified`). Mellette Apache-2.0, MIT és CC0
   licencű kisebb készletek vannak (a táblázat 1–7. sora). A magyar arány ismeretlen: a kártya csak
   `multilingual` címkét visel, magyart nem említ.
2. **Kalibrált absztencióra jelöltlistán kész adat nincs.** Az X-et legtöbbször gold-drop konstrukcióval kell
   előállítani: a helyes jelölt kikerül a listából. Természetes „none” csak néhány helyen van: SQuAD2, MILQA
   (magyar), CLINC-OOS, FEVER NEI, HelpSteer3 tie, arena `both_bad`, When2Call.
3. **Magyar üzleti adat (számla, e-mail, ügyfélszolgálat, csalás) nyílt licenccel nincs.** A magyar oldal:
   - intent: MASSIVE hu-HU;
   - NLI, szentiment, elfogadhatóság, oksági választás: HuLU;
   - jogi témabesorolás: MultiEURLEX;
   - szövegértés: MILQA, HuRC, HuBoolQ.

   A célfeladatokat fordítással és helyi szintetikus generálással kell lefedni.
4. **A legnagyobb kockázat a licenc, nem a mennyiség.**
   - Több népszerű készlet nem kereskedelmi.
   - Több közösségi döntési korpusz zárt modellből (Jev) desztillál.
   - A tanítás-tiltó és a tisztázatlan források csak értékelésre jók.

## Jelöltek

| # | HF id | Sorok | Licenc | Nyelv | „X” forrása | Megjegyzés |
|---|---|---|---|---|---|---|
| **SystemOne-formátumú döntési korpuszok** |
| 1 | `tasksource/tasksource-jev-typed-decisions` | ~2,5 M train + 15k val + 15k test (kártya) | `other`, soronként `license_use` | en + multilingual (hu-arány ismeretlen) | noul címkeellenőrzés, choice | 47% osztályozás, 30% MC, 10% graded (puha címke), 10% procedurális, 3% token. A kritériumok többnyire nyers címkenevek. Az MMLU/BIG-bench/BLiMP szándékosan kihagyva. **Csak `license_use == "commercial"`** |
| 2 | `tasksource/procedural-typed-decisions` | ~264k (100K–1M) | Apache-2.0 | en | szabályból | egy JSON-állapoton több kérdés, szabályból számolt (zajmentes) címke: számlálás, aritmetika, keresés, szabályalkalmazás |
| 3 | `ZefanCai/Open-Jev` (`release-v2-redistributable`) | 113 568, ebből 79 116 train | CC0-1.0 (a generált rész) | en, zh, tr | külön OOD split | harmadik fél forrásai saját licenccel (pl. WANLI CC BY 4.0). Qwen3.5-9B + LoRA + skaláris döntési fej, a mi felállásunk közvetlen előzménye |
| 4 | `tasksource/synthetic-typed-decisions` | 8,9k, 235 workflow | Apache-2.0 | en | noul | e-mail/chat/jegy workflow-k. **A címkéket a Jev 1.13 adta (OpenRouteren, a kártya szerint)** → desztillált |
| 5 | `LocalLLaMA/typed-decisions` | 1,6k (4 workflow × 400) | Apache-2.0 | en | — | állapotonként 5 kérdés, több annotátoros puha cél, természetes nyelvű kritériumok. **Értékelésre** (a Laya/Clef közölt eredményeivel összevethető) |
| 6 | `helmo/synthetic-typed-decisions` | 9 879 | MIT | en | noul | choice 2–6 leírt opcióval, noul, score |
| 7 | `fastino/fast-decisions` | 17 domén × 100 (dev) | Apache-2.0 | en | handoff, igen/nem kapu | intent, dokumentumtípus, e-mail- és jegyirányítás. **Értékelésre**: sosem látott séma |
| **Absztenció / megválaszolhatatlan** |
| 8 | `rajpurkar/squad_v2` | 130 319 train | CC-BY-SA-4.0 | en | természetes (~1/3) | a dev gyakori eval |
| 9 | `SzegedAI/MILQA` | >23 500 kérdés | CC-BY-SA-4.0 | **hu** | természetes, csapdakérdésekkel | test tilos |
| 10 | `allenai/cosmos_qa` | 25 262 train | CC-BY-4.0 | en | részben „None of the above” opció | script-alapú |
| 11 | `textmachinelab/quail` | 10 246 train | **CC-BY-NC-SA-4.0** | en | „not enough information” | NC — kerülendő |
| 12 | `copenlu/fever_gold_evidence` | 228 277 train | ellentmondásos (cc-by-sa-3.0 + gpl-3.0) | en | NEI | licenc tisztázatlan |
| 13 | `nvidia/When2Call` | 15k SFT + 9k preferencia (kártya) | CC-BY-4.0 | en | „ne hívj eszközt” | eszközhívás-döntés, hatókörön kívüli kérés |
| **Entitás- / termékpárosítás** |
| 14 | `tasksource/esci` | 2 027 874 pár | Apache-2.0 | en/es/ja | ha nincs Exact a listán | Substitute = hard negative; a test KDD-eval |
| 15 | `naist-nlp/zeshel` | 33 130 mention + 492 321 entitás | CC-BY-SA-3.0 | en | gold-drop | BM25 top-k jelölt a KB-ból |
| 16 | `zidcenek/GLAMI-Entity-Matching-Dataset` | ~1,3M kép | Apache-2.0 (kártya) | **hu**, cs, sk, pl, ro, hr, bg, el | gold-drop, `hard_5` | hiányos kártya, eredete nem dokumentált |
| 17 | `matchbench/*`, `lighteval/EntityMatching` | 1–6k pár / készlet | nincs megadva | en | konstruálható | tisztázatlan, klasszikus eval |
| 18 | WDC Products | 10 422 ajánlat | adat-licenc nincs kimondva | en | konstruálható | a WDC kifejezetten tiltja a tanítást → **csak eval** |
| **LLM-bíráló / preferencia** |
| 19 | `nvidia/HelpSteer3` (preference) | 40 476 pár | CC-BY-4.0 | en + 13 (hu nincs) | 0 = „kb. azonos” | human címke, tiszta forrás |
| 20 | `nvidia/HelpSteer2` | 20 324 train | CC-BY-4.0 | en | — | rubric 0–4 vagy A/B/tie |
| 21 | `lmarena-ai/arena-human-preference-140k` (+55k) | 135 634 (+57 477) | CC-BY-4.0 / Apache-2.0 | főleg en | `both_bad` | a válaszokra a szolgáltatók ToS-a |
| 22 | `openbmb/UltraFeedback` | 63 967 × 4 | MIT | en | — | GPT-4 címkék, OpenAI ToS-kockázat |
| 23 | `tasksource/PRM800K` | ~800k lépés (nem ellenőrzött) | MIT | en | 0 = neutral | MATH test feladatokat tartalmaz |
| **Osztályozás / routing / szabály / eszköz** |
| 24 | `clinc/clinc_oos` (`plus`) | 15 250 train (250 OOS) | CC-BY-3.0 (a DialoGLUE-ban CC-BY-SA-3.0) | en | OOS | test tilos |
| 25 | `PolyAI/banking77` | 13 083 / 77 intent | CC-BY-4.0 | en | gold-drop | fordítandó; sosem látott sémának is jó |
| 26 | `AmazonScience/massive` | hu-HU: 11 514 / 2 033 / 2 974 | CC-BY-4.0 | 51 locale, **hu** | gold-drop | scenario (18) + intent (60) + slotokból noul egy állapoton. A Speech-MASSIVE (CC-BY-NC-SA) más! |
| 27 | `Salesforce/xlam-function-calling-60k` | 60 000 | CC-BY-4.0, **gated** (feltétel-elfogadás) | en | — | „melyik eszköz?” choice, a kritériumok az eszközleírások |
| 28 | `stanfordnlp/snli` + `nyu-mll/multi_nli` | 550k + 393k | CC-BY-SA-4.0 / vegyes | en | neutral csak X-analóg | ismert artefaktumok |
| 29 | `coastalcph/lex_glue` | 188 532 train | CC-BY-4.0 | en | UNFAIR-ToS „nincs” | alkészlet-licencek ellenőrizendők |
| 30 | `MoritzLaurer/synthetic_zeroshot_mixtral_v0.1` | 2 627 036 | Apache-2.0 | en | gold-drop | LLM-generált címkék. A `multilingual-NLI-26lang-2mil7`-ben **nincs** magyar |
| **Magyar** |
| 31 | `NYTK/HuRC` | 64 614 train | CC-BY-4.0 | hu | gold-drop | cloze entitásválasztás; a viewer hibás |
| 32 | HuLU (`NYTK/HuCOLA`, `HuRTE`, `HuCommitmentBank`, `HuWNLI`) | 250–9 076 | CC-BY-SA-4.0 | hu | HuCB: „nem eldönthető” | kicsik; a leaderboard test tilos (rejtett címkék) |
| 33 | `NYTK/HuSST` | 9 347 / 1 168 / 1 168 | HF: BSD-2-Clause; GitHub: CC-BY-SA-4.0 | hu | — | ellentmondás → a szigorúbbat (CC-BY-SA) vesszük |
| 34 | `NYTK/HuCoPA` | 400 / 100 / 500 | BSD-2-Clause | hu | — | oksági választás, megengedő |
| 35 | `NYTK/HuBoolQ` | 10K–100K | CC-BY-SA-3.0 | hu | — | igen/nem → noul |
| 36 | `Davlan/sib200` (hun_Latn) | 701 train | CC-BY-SA-4.0 | 205 nyelv | gold-drop | nagyon kicsi; inkább eval |
| 37 | `coastalcph/multi_eurlex` (hu) | ~22,7k / 5k / 5k (a melléklet szerint; nem ellenőrzött) | **CC-BY-SA-4.0** (HF-kártya; a melléklet CC BY 4.0-t ír — téves) | 23 EU-nyelv | gold-drop / címkénként noul | hosszú szövegek, EuroVoc-leírások |
| **Kalibráció** |
| 38 | `nvidia/Nemotron-RL-QA-Abstention-v1` | 3 150 | CC-BY-4.0 | en | természetes | kicsi, nem MC |

## Javasolt első keverék

Egységes konverzió minden forrásból:
- K∈[2,10] opció, permutált címkék;
- `noul` = kétopciós choice;
- `score` = sorrendezett choice puha céllal, az átlag két szomszédos szintre osztva (3,4 → 0,6 a 3-ra, 0,4 a
  4-re);
- forrásonként eltérő X-arány (~15–40%), hogy a modell ne konstans X-priort tanuljon.

A mi kiolvasásunk (szűkített softmax) és a soft címkés tréning ezeket változtatás nélkül kezeli.

| arány | forrás | miért |
|---|---|---|
| ~25% | `tasksource-jev-typed-decisions` (`commercial`) + `helmo` + `Open-Jev` (CC0) | általános tipizált döntések; a kritériumokhoz leírás-generálás kell |
| ~10% | `procedural-typed-decisions` | zajmentes szabálycímkék, több kérdés egy állapoton |
| ~25% | saját szintetikus BA-adat (számlasor → cikk) + magyar DocAI-workflow-k | a fő célfeladat, hard-NOTA esetekkel; e-mail, számla, szerződés több kérdéssel |
| ~10% | `tasksource/esci` + `zeshel` | jelöltlistás párosítás, hard negative-ekkel |
| ~10% | MASSIVE hu-HU + CLINC + BANKING77 (fordítva) + When2Call | routing reject-opcióval, magyar intentekkel |
| ~10% | SQuAD2 + MILQA + HuBoolQ + HuRC | valódi megválaszolhatatlan esetek, magyar szövegértés |
| ~5% | HelpSteer3 (preference) | judge-döntés human címkével, tie-jal |
| ~5% | HuLU (HuRTE, HuSST, HuCoPA, HuCB) + kalibrációs puha címkés sorok | magyar NLI/szentiment; puha célok |

A magyar arányt (~40–50%) a célnyelvi teljesítmény alapján érdemes hangolni.

## Konverziós buktató: szinonim címkék a gold-drop előtt (a 2026-10-04-i lelet)

A gold-drop („egyik sem” = a helyes címke kihagyása) és a más feladatokból kevert zavaró opciók
pontosan ott termelnek címkezajt, ahol a kihagyott címkének szinonimája marad a listán. Ilyenek:
- két forrás azonos jelentésű intentje vagy kategóriája;
- egy címkeleírás parafrázisa;
- egy katalógus-duplikátum.

A LoRA-decision-head F1C-adatán Dani 99 átnézett itemjéből 12 volt problémás, ebből 9 ilyen
duplikátum (Napló, F1F). Embedding-hasonlósággal ez nem szűrhető (a valódi párok koszinusza 0,60–0,94,
átfedésben a szándékos nehéz negatívokkal).

**Recept:**
1. Páronkénti LLM-bírálat a kritériumokon („ugyanazt jelölheti-e?”), két független bírálóval, mindkét
   sorrendben (`duplikatum_llm.py`).
2. A szinonim kritériumok egy osztályba vonva, vagy a gold-drop és a keverés közben együtt kezelve.
3. A kérdés a prompt elején, a változó pár a végén. A prefix-cache így ~80%, a Llama-3.3-70B ~9 kérés/s
   GB10-en.

Ugyanez a szűrés kell a címkeleírás-parafrázisok generálása után is.

## Licenc-csoportok publikus adapterhez

- **Tiszta (permissive, attribúcióval):**
  - döntési: `procedural-typed-decisions`, `helmo`, `fastino` (eval), `LocalLLaMA` (eval), `Open-Jev` CC0
    része;
  - párosítás, routing, eszköz: ESCI, CLINC (HF-kártya), BANKING77, MASSIVE, xLAM (gated feltételekkel),
    When2Call;
  - bíráló: HelpSteer2/3;
  - magyar: HuRC, HuCoPA;
  - egyéb: CosmosQA, Nemotron-Abstention, LexGLUE (az alkészletek után), synthetic_zeroshot;
  - a `tasksource-jev-typed-decisions` `commercial` sorai.
- **ShareAlike (CC-BY-SA):** SQuAD2, MILQA, SNLI, ZESHEL, SIB-200, MultiEURLEX, a HuLU nagy része (a
  HuSST-t is ide soroljuk), HuBoolQ, Belebele. A származtatott *adatkészlet* csak azonos licenccel adható
  tovább. Az, hogy a ShareAlike kiterjed-e az adapter súlyaira, **döntést igényel** (nem jogi tanács).
- **Desztillált, kizárandó vagy átvilágítandó:**
  - `tasksource/synthetic-typed-decisions`: a címkéit a Jev 1.13 adta, a kártya szerint;
  - `jev-distill-corpus-v3`: Apache-2.0 jelöléssel, de a melléklet szerint ~498k sor Jev-desztilláció;
  - UltraFeedback (GPT-4), arena (proprietary kimenetek).

  Az adatkészlet licence nem írja felül a forrásszolgáltatás feltételeit.
- **Kerülendő (NC / NC-SA):**
  - QuAIL, `facebook/anli`, XNLI, `alexandrainst/m_*`, MultiFin, `kiddothe2b/contract-nli`,
    `earino/chaosnli`, `ServiceNow-AI/Abstain-QA`, `facebook/AbstentionBench`, `BAAI/JudgeLM-100K`,
    PKU-SafeRLHF, SciQ;
  - AG News, HunSum-2, Hungarian Twitter Sentiment, Speech-MASSIVE;
  - a tasksource `non-commercial` sorai (pl. BeaverTails, IntentGrasp).
- **Tisztázatlan:**
  - a tasksource `unspecified` sorai;
  - matchbench/Magellan, WDC (+ tanítási tilalom), GLAMI-EM;
  - Skywork-Reward, `stanfordnlp/SHP`, `batubayk/HU-News` (nincs licenc), OpinHuBank.
- **Csak eval:**
  - döntési: `LocalLLaMA/typed-decisions` test, `fastino/fast-decisions`;
  - magyar: `facebook/belebele` (hun_Latn), SIB-200, `NYTK/hu-mmlu`, `EC-DGT-AI/EU-MMLU`, `mhardalov/exams` (hu),
    a MASSIVE hu-HU test;
  - judge, PRM és absztenció: JudgeBench, RewardBench, ProcessBench, AbstentionBench, Abstain-QA;
  - minden test split.

## Generátor-licenc a szintetikus részhez

A szintetikus adatot és a címkeleírásokat helyben futó, **Apache-2.0** licencű modellel kell generálni, és
minden sorban rögzíteni kell a generátor nevét és verzióját. A jelenlegi BA-adat generátora a
Qwen3.8-Flash-Next, ami **Qwen Community License 1.0** alatt van (⚠️, lásd
[licenc-szerzodes](2026-10-03-licenc-szerzodes.md)). Egy publikus általános modellhez ezért
`Qwen/Qwen3.6-35B-A3B` (Apache-2.0, ellenőrizve) vagy `mistralai/Mistral-Small-4-119B-2603-NVFP4`
(Apache-2.0) generáljon.

Független visszacímkézőnek egy másik családú modell kell, és csak az egyező sorok maradnak. A puha cél a
két modell eloszlásának átlaga. Llama-kimenet a Llama-licenc miatt ne kerüljön a tanítóadatba, csak
triage-ra használjuk.

## Hiányok, amelyeket szintetizálni kell

1. **Kalibrált absztenció valós visszakeresési hibákkal.** A gold-drop artefaktust okoz: a modell
   megtanulhatja, hogy „ha nincs nagyon hasonló jelölt, akkor X”. Hard-NOTA esetek kellenek: rokon, de
   nem azonos jelölt. Ezt a mi S7/S8-unk (kényszerített X(a) + testvérek) adja, a duplikátum-szűréssel.
2. **Magyar adat.** Hiányzik:
   - a magyar termék- és cikkpárosítás;
   - a magyar judge- és preferenciaadat;
   - a nagy magyar NLI;
   - minden számla-, e-mail-, könyvelési és dokumentumtípus-adat.
3. **Kalibrációs célcímkék.** Ezek modell-specifikusak, ezért on-policy kell gyűjteni a Qwen3.6 saját
   helyes és hibás válaszaiból (Kapoor et al. 2024: ~1000 osztályozott példa már segít). Soft label
   forrásnak jó a HelpSteer3 annotátori szórása, a HuCB és a tasksource graded forrásai.
4. **Címkeleírások.** A tasksource kritériumai többnyire nyers címkenevek („entailment”). Címkénként
   2–3 leírást generálunk magyarul és angolul, majd mintavételes emberi ellenőrzés jön. Tanításkor
   véletlenszerűen váltogatjuk a nevet, a leírást és a parafrázist, a szinonima-szűrés után.
5. **Formai változatosság.** Konstruálandó minden forrásból:
   - opciószám (2–10), pozíció-permutáció, címke-egyensúly;
   - több kérdés egy állapoton (MASSIVE: scenario + intent + slot-noul; tasksource `group_id`).
6. **Magyar szabály- és dokumentumtípus-döntés.** Ilyen adat nincs.

## Kitartás és mérőszámok a zero-shot értékeléshez

- **Feladatcsalád szerinti kitartás:**
  - forrás vagy `task_family` alapján egész családok maradjanak ki;
  - egy állapot összes kérdése ugyanabba a splitbe kerüljön (`group_id`).
- **Sosem látott séma:** a CLINC domének egy része, BANKING77, `fastino/fast-decisions`.
- **Magyar teszt:**
  - MASSIVE hu-HU test, HuRTE val, HuSST test, MultiEURLEX hu test, SIB-200, Belebele;
  - 300–500 tételes, kézzel címkézett belső DocAI-arany készlet, amely egyetlen tanítósorhoz sem
    kapcsolódik.
- **Workflow-teszt:** `LocalLLaMA/typed-decisions` test (400 eset, 2000 döntés), a Laya/Clef közölt
  eredményeivel összevethető (ezek a fejlesztők saját mérései).
- **Mérőszámok:**
  - pontosság, Brier, ECE kérdéstípusonként;
  - és mivel a termék küszöbökre épít, **besorolási lefedettség adott precizitásnál és AURC**.

## Referencia-modellek (másodlagos források, ellenőrizetlen)

- **Clef:** fagyasztott Qwen-gerinc, rank-256 LoRA + routing head, label-smoothed CE + Brier, belső
  szintetikus adat, majd RLCD-lépés. Az adat nem publikus. Ez a recept egybevág az L3-tréningünkkel
  (CE + ε + Brier).
- **Laya:** nyilvános szövegosztályozási adatkészletekből tanult (pontos lista nincs). A
  `laya-typed-decisions` a `LocalLLaMA/typed-decisions` train részén finomhangolt.

## Nem ellenőrzött

- a PRM800K sorszáma a HF-en;
- a MultiEURLEX magyar darabszáma;
- a GLAMI `groups_*.csv` `label` mezőjének jelentése;
- az ESCI query-száma;
- a tasksource-korpusz magyar aránya és a `commercial` sorok száma;
- a `jev-distill-corpus-v3` desztillált sorainak száma;
- az RVL-CDIP, Tobacco3482, DocLayNet, Enron, Super-NaturalInstructions, FLAN, P3 és xP3x alkészlet-licencei.

## Források

- a HF-kártyák és az `api/datasets/<id>` tagek a fenti ID-kkal (2026-10-04);
- [open_datasets_research.md](../open_datasets_research.md) — külső kutatási anyag, 62 hivatkozással;
- [WDC Products](https://webdatacommons.org/largescaleproductcorpus/wdc-products/);
- [Kapoor et al. 2024](https://arxiv.org/abs/2406.08391);
- [Abstain-QA](https://arxiv.org/abs/2407.16221).
