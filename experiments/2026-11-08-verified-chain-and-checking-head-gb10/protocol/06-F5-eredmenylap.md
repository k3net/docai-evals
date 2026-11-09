# K06F5 eredménylap (06 v1)

A 06-os kör végső mérése a három friss szintetikus családon (`penzugy.bankparositas`, `muszaki.hibaelharitas`,
`szabaly.koltsegelszamolas`). A kérdés: a B1 változatlan javaslatain a célterületen tanított megbízhatósági modell
(B1-R) jobban rendezi-e a helyes és a hibás javaslatokat, mint a B1 saját pontszáma (B1-S).

- **A mérés módja:**
  - **Rögzítés:** a v1 2026-10-31 09:15:32-kor rögzült (`kor06/rogzites/v1/`). A manifest 41 fájlos, a sha256-ja
    `5ff6d801…25ec8`; a pecsétmanifest a K06F3C.
  - **Megtekintés:** a CAL- és TESZT-kiolvasásokat a rögzítés előtt nem néztük meg.
  - **Futás:** az F5 09:15:38–09:48:30 között futott a v1 szerint (`kor06/eszkozok/k06f5.sh`):
    - TESZT-szelet, szigorú helyesség az elsődleges;
    - sabloncsoportos klaszteres bootstrap (D23), családonként 60 TESZT-sablon;
    - 10 000 ismétlés, seed 20261029;
    - a futások átlaga replikánként (D24).
- **Források:**
  - `f5_elemzes.json`: 8.1–8.3, a nyelvi részszeletek, a futások és a sablonszám;
  - `f5_bontas.json`: D20;
  - `f5_munkapont.json`: 8.4.
  - Az `f5_bontas.md` gépi lap fejléce az F1-es szöveget viszi („a 05 v1a kétszintű húzásával”). A tényleges klaszter
    a sabloncsoport (a JSON-ban 60 klaszter rétegenként). A sorok sorrendje: bank, hibaelhárítás, szabálycsalád.
- **Önellenőrzés:**
  - az 1224 kontraszt egyikének pontbecslése sem esik a saját intervallumán kívül;
  - a T500, a CAL és a TESZT sablonjai családonként diszjunktak (30 / 30 / 60, átfedés 0);
  - a kiolvasott promptban nincs item-id és állapotmező, csak a helyzetleírás, a kérdés és az opciók szövege, semleges
    opció-id-kkal.
- **Az értelmezés** (utolsó szakasz) kézzel írt, 2026-10-31.

**Definíciók:**
- **AURC (S+N):** a B1 SELECT- és NONE-javaslatainak kockázat–lefedettség görbéje alatti terület, a kar pontszáma
  szerinti sorrendben. Kisebb a jobb.
- **Optimum:** a hibák a sor végén, ez a B1 javaslatainak legjobb elérhető AURC-ja.
- **E-AURC:** az AURC és az optimum különbsége.
- **SELECT-AURC:** ugyanez csak a B1 SELECT-javaslatain (D7).
- **Szigorú helyesség:** a NONE csak NO_MATCH-en helyes, MISSING_DATA-n és OUT_OF_SCOPE-on hiba.
- **Enyhe helyesség:** a NONE minden nem-MATCH itemen helyes.
- **Δ:** a kar mínusz a B1-S, ugyanazokon a bootstrap-csoportokon; negatív a javulás.

## Összefoglalás

- **A 8.3 szabály a D4-gyel teljesül, nagy tartalékkal: a következő kör indokolt.** Ez kutatási továbblépés, nem
  automatizálási garancia.
  - A B1-R mindhárom családon jobb a B1-S-nél: ΔAURC −0,094, −0,204, illetve −0,254, mind a három intervallum 0 alatt.
  - Az átlagos AURC aránya 0,205 [0,187; 0,224]: a B1-R a B1-S átlagos AURC-jának ötödére csökkenti a sajátját.
- **A siker mindhárom szintje teljesül, mindhárom családon:**
  - a B1-R jobb a B1-N-nél és a B1-LR-nél;
  - a SELECT-javaslatokon is javít.
- **A nyereség nagyobbik része a NONE-konvencióból jön (D20).**
  - A B1 a NONE-javaslatainak körülbelül a felénél hibázik szigorú helyességgel, és éppen ezekben a legbiztosabb.
  - Ezek főként a hatókörön kívüli itemek: a B1 mindhárom családon mind a 100 OUT_OF_SCOPE-ra NONE-t mond.
  - Már a NONE-javaslatok hátrasorolása (B1-N) is elhozza az átlagos nyereség 72%-át.
  - A maradék 28%: a B1-R megtanulja, mely NONE-javaslat NO_MATCH (a NONE-on belüli AUROC 0,955–0,998), és a
    SELECT-sorrendet is javítja.
- **A rejtett állapotú fej a SELECT-javaslatokon ad többet az egyszerű referenciánál.**
  - A B1-R a SELECT-AURC-t 13%, 57%, illetve 35%-kal csökkenti.
  - Az ötjellemzős B1-LR a SELECT-sorrenden egyik családon sem javít.
  - Ez teljes módszerek összevetése (D10), önmagában nem bizonyítja, hogy a többletet a rejtett állapotok adják.
- **Enyhe helyességgel a nyereség eltűnik:** az arány 0,965 [0,881; 1,063].
  - Ez várható: a fej szigorú címkén tanult, és enyhe helyességnél a MISSING_DATA- és OUT_OF_SCOPE-itemeken adott
    NONE helyes.
  - Az elsődleges eredmény tehát a szigorú konvencióhoz kötött; a SELECT-javulás mindkét változatban ugyanaz.
- **A B1-R a B1 javaslatait majdnem az optimum szerint rendezi: E-AURC 0,005 mindhárom családon.** Ez szintetikus,
  rögzített összetételű (D9) családokon mért érték; valódi adaton kisebb elválasztásra kell számítani.
- **Munkapont (8.4, leíró):**
  - A B1-S-nek egyik családon sincs munkapontja: a CAL-on egyetlen τ sem éri el a CP-alsó ≥ 0,95-öt 200 elfogadott
    itemmel.
  - A B1-R a TESZT-en az itemek 67–72%-át fogadja el, 0,967–0,983-as precizitással.

## 1. A döntési szabály (8.3, D4)

Szigorú helyesség, TESZT, B1-R a teljes T500-zal (három seed átlaga).

| család | B1-S | B1-R \| T500 | ΔAURC [95% CI] | B1-R / B1-S | Holm-p |
|---|---|---|---|---|---|
| bank | 0,1422 | 0,0480 | −0,0942 [−0,1114; −0,0786] | 0,338 | < 0,001 |
| hibaelhárítás | 0,2478 | 0,0442 | −0,2036 [−0,2307; −0,1773] | 0,178 | < 0,001 |
| szabálycsalád | 0,3037 | 0,0498 | −0,2539 [−0,2778; −0,2270] | 0,164 | < 0,001 |

A 10 000 ismétlés egyikében sem lett a Δ pozitív; a p ennél pontosabban nem adható meg.
| **átlag** | 0,2312 | 0,0473 | — | **0,205 [0,187; 0,224]** | — |

- **1. feltétel:** legalább két családon B1-R − B1-S < 0. Mindhárom családon teljesül. ✓
- **2. feltétel:**
  - az arány ≤ 0,90: 0,205 ✓;
  - az intervallum felső határa < 1 (D4): 0,224 ✓.
- **Az abszolút javulás megoszlása:** bank 17%, hibaelhárítás 37%, szabálycsalád 46%.
- **Az erőbecslés (8.5) tervezési becslés volt.** A várt MDE80 3,9–9,6% relatív csökkenés volt; a mért hatás 80%, ez
  messze fölötte van.

## 2. A siker három szintje (K1, D11)

| szint | összevetés | bank | hibaelhárítás | szabálycsalád |
|---|---|---|---|---|
| 1. | B1-R − B1-S | −0,0942 [−0,1114; −0,0786] | −0,2036 [−0,2307; −0,1773] | −0,2539 [−0,2778; −0,2270] |
| 2. | B1-R − B1-N | −0,0464 [−0,0530; −0,0401] | −0,0473 [−0,0535; −0,0413] | −0,0592 [−0,0663; −0,0516] |
| 2. | B1-R − B1-LR | −0,0087 [−0,0152; −0,0036] | −0,0227 [−0,0286; −0,0174] | −0,0223 [−0,0340; −0,0133] |
| 3. | SELECT: B1-R − B1-S | −0,0050 [−0,0106; −0,0001] | −0,0131 [−0,0189; −0,0081] | −0,0199 [−0,0271; −0,0129] |
| (3.) | SELECT: B1-LR − B1-S | −0,0009 [−0,0035; 0,0018] | −0,0013 [−0,0032; 0,0006] | −0,0027 [−0,0057; 0,0002] |
| (3.) | SELECT: B1-R − B1-LR | −0,0041 [−0,0107; 0,0011] | −0,0119 [−0,0170; −0,0075] | −0,0172 [−0,0236; −0,0109] |

- **Mindhárom szint teljesül mindhárom családon.** A banki SELECT-javulás határeset: a felső határ −0,0001.
- **Az átlagos AURC aránya:**
  - B1-R / B1-N: 0,48;
  - B1-R / B1-LR: 0,73.

  Ez pontbecslés, intervallum nélkül.
- A SELECT-en a B1-R a B1-LR-nél két családon szignifikánsan jobb, a bankon nem.

## 3. A nyereség bontása NONE- és SELECT-javaslatokra (D20, kötelező sor)

Szigorú helyesség, TESZT; a B1-R pontszáma a három seed átlaga (`bontas06`).

| | bank | hibaelhárítás | szabálycsalád |
|---|---|---|---|
| NONE-javaslat aránya | 22,4% (224) | 34,2% (342) | 22,5% (225) |
| a NONE szigorúan helyes / enyhén helyes | 0,554 / 1,000 | 0,471 / 0,942 | 0,551 / 0,996 |
| NONE-on belüli AUROC: B1-S / B1-R0 / B1-R / B1-LR | 0,044 / 0,306 / 0,998 / 0,947 | 0,362 / 0,474 / 0,955 / 0,872 | 0,015 / 0,275 / 0,995 / 0,985 |
| SELECT szigorúan helyes | 0,772 | 0,871 | 0,766 |
| SELECT-en belüli AUROC: B1-S / B1-R0 / B1-R / B1-LR | 0,963 / 0,840 / 0,976 / 0,966 | 0,902 / 0,829 / 0,993 / 0,908 | 0,901 / 0,848 / 0,977 / 0,911 |
| **teljes ΔAURC (B1-R − B1-S)** | −0,0942 | −0,2036 | −0,2539 |
| ebből a NONE hátrasorolása (B1-N − B1-S) | −0,0478 (51%) | −0,1564 (77%) | −0,1947 (77%) |
| **a maradék: B1-R − B1-N** [CI] | −0,0464 (49%) [−0,0530; −0,0401] | −0,0473 (23%) [−0,0536; −0,0415] | −0,0592 (23%) [−0,0665; −0,0516] |
| SELECT-AURC: B1-S → B1-R | 0,0398 → 0,0348 | 0,0230 → 0,0099 | 0,0562 → 0,0363 |

**A B1 javaslatai állapotonként (TESZT, itemszám; leíró sor):**

| gold-állapot | bank: SELECT / NONE | hibaelhárítás: SELECT / NONE | szabálycsalád: SELECT / NONE |
|---|---|---|---|
| MATCH (600) | 600 / 0 | 580 / 20 | 599 / 1 |
| NO_MATCH (200) | 76 / 124 | 39 / 161 | 76 / 124 |
| MISSING_DATA (100) | 100 / 0 | 39 / 61 | 100 / 0 |
| OUT_OF_SCOPE (100) | 0 / 100 | 0 / 100 | 0 / 100 |

- **A szigorúan hibás NONE-ok forrása:**
  - főleg az OUT_OF_SCOPE: a B1 mindhárom családon mind a 100-ra NONE-t mond;
  - a hibaelhárításon a MISSING_DATA 61 iteme és 20 MATCH-item is.
- **A B1-S NONE-on belüli AUROC-ja 0,5 alatt van.**
  - A B1 éppen ezekben a szigorúan hibás NONE-okban a legbiztosabb.
  - Ezért kerülnek a rangsor elejére a biztos hibák, és ezért nincs a B1-S-nek munkapontja.
- **A SELECT-hibák is szinte mind állapothibák.**
  - A bankon és a szabálycsaládon a B1 mind a 100 MISSING_DATA-itemen választ, a NO_MATCH-en 76-on.
  - A MATCH-en rossz opciót a bankon 1, a hibaelhárításon 7, a szabálycsaládon 5 esetben választ. Ez a SELECT-hibák
    1%-a, 8%-a, illetve 3%-a.
  - A SELECT-javulás (3. szint) tehát elsősorban azt méri, hogy a fej felismeri a választott opció mögött a hiányzó
    adatot vagy a nem-egyezést. Az opciók közti tévesztést alig.
- **Az átlagos nyereség 72%-a a NONE hátrasorolásából jön, 28%-a a B1-R tanult többlete.**
- A B1-R − B1-N intervallumai a bontás saját bootstrap-húzásából valók, a 2. pontéi az elemzéséből. A két húzás
  legfeljebb 0,0010-ban tér el.

## 4. Karok családonként (AURC, szigorú, TESZT)

| kar | bank | hibaelhárítás | szabálycsalád | átlag | / B1-S |
|---|---|---|---|---|---|
| B1-S | 0,1422 | 0,2478 | 0,3037 | 0,2312 | 1,000 |
| B1-N | 0,0944 | 0,0915 | 0,1090 | 0,0983 | 0,425 |
| B1-R0 (célterületi tanítás nélkül) | 0,1365 | 0,1211 | 0,1308 | 0,1295 | 0,560 |
| B1-R \| T100 | 0,0837 | 0,0670 | 0,0885 | 0,0798 | 0,345 |
| B1-R \| T200 | 0,0622 | 0,0510 | 0,0639 | 0,0591 | 0,255 |
| **B1-R \| T500** | **0,0480** | **0,0442** | **0,0498** | **0,0473** | **0,205** |
| B1-LR \| T100 | 0,0619 | 0,0737 | 0,0752 | 0,0703 | 0,304 |
| B1-LR \| T200 | 0,0592 | 0,0720 | 0,0733 | 0,0682 | 0,295 |
| B1-LR \| T500 | 0,0567 | 0,0669 | 0,0721 | 0,0652 | 0,282 |
| H | 0,1953 | 0,1921 | 0,1710 | 0,1861 | 0,805 |
| H-T-meta \| T500 | 0,0864 | 0,0836 | 0,0841 | 0,0847 | 0,366 |
| optimum (a B1 javaslatain) | 0,0426 | 0,0391 | 0,0443 | 0,0420 | — |

A B1-R E-AURC-ja: 0,0054, 0,0050, illetve 0,0055. A B1-S-é: 0,0996, 0,2087, illetve 0,2594.

## 5. Tanulási görbe (0, 100, 200, 500 példa)

A Δ a B1-S-hez képest, szigorú helyességgel; mellette zárójelben a SELECT-AURC Δ-ja.

| család | B1-R0 (0) | B1-R \| T100 | B1-R \| T200 | B1-R \| T500 |
|---|---|---|---|---|
| bank | −0,0057 n.s. (+0,0414) | −0,0585 (+0,0168) | −0,0800 (+0,0061) | −0,0942 (−0,0050) |
| hibaelhárítás | −0,1268 (+0,0167) | −0,1808 (−0,0040 n.s.) | −0,1968 (−0,0097) | −0,2036 (−0,0131) |
| szabálycsalád | −0,1729 (+0,0257) | −0,2151 (+0,0062 n.s.) | −0,2397 (−0,0040 n.s.) | −0,2539 (−0,0199) |

- **A célterületi tanítás nélkül a fej rontja a SELECT-sorrendet.** Az előtanított B1-R0 mindhárom családon rosszabb a
  SELECT-en a B1-S-nél, a bankon a teljes AURC-ban sem javít.
- **A SELECT-javulás 500 példát kíván.** A bankon a T100 és a T200 még szignifikánsan ront a SELECT-en, a T500 javít.
- **Kis mintán a B1-LR a jobb** (pontbecslés, a 4. pont táblája). T100-nál a bankon és a szabálycsaládon a B1-LR
  AURC-ja kisebb a B1-R-énél, T200-nál még a bankon is. T500-nál a B1-R mindhárom családon jobb, intervallummal (2. pont).

## 6. A futások közti eltérés (D24)

A ΔAURC (B1-R − B1-S) futásonként, a teljes TESZT-szeleten.

| család | B1-R \| T500 (3 seed) | B1-R \| T200 (5 húzás × 3 seed) | B1-R \| T100 (5 × 3) | H-T-meta \| T500 (3) |
|---|---|---|---|---|
| bank | −0,0945…−0,0938, sd 0,0004 | −0,0918…−0,0656, sd 0,0077 | −0,0790…−0,0252, sd 0,0192 | −0,0646…−0,0512, sd 0,0076 |
| hibaelhárítás | −0,2044…−0,2030, sd 0,0007 | −0,2004…−0,1857, sd 0,0037 | −0,1980…−0,1620, sd 0,0113 | −0,1710…−0,1594, sd 0,0060 |
| szabálycsalád | −0,2541…−0,2536, sd 0,0002 | −0,2456…−0,2312, sd 0,0042 | −0,2325…−0,2017, sd 0,0116 | −0,2344…−0,2114, sd 0,0129 |

- **T500-nál a seedek közti eltérés elhanyagolható** a tesztminta bizonytalanságához képest.
- A T100-as húzások között a bankon négyszeres a különbség: a futásonkénti Δ −0,025 és −0,079 között van.

**A minták sablonszáma (D23):**
- **T100:** bank 30 / 29 / 29 / 29 / 29, hibaelhárítás 30 / 30 / 30 / 30 / 29, szabálycsalád 30 / 27 / 28 / 29 / 29;
- **T200:** minden húzás mind a 30 T500-sablont lefedi.

## 7. Magyar bontás (kötelező, D9)

Szigorú helyesség, TESZT, nyelvenként 500 item.

| család | nyelv | B1-S | B1-R | B1-R − B1-S | B1-R − B1-N | B1-R − B1-LR | SELECT: B1-R − B1-S |
|---|---|---|---|---|---|---|---|
| bank | hu | 0,1256 | 0,0517 | −0,0739 [−0,0887; −0,0601] | −0,0442 [−0,0526; −0,0361] | −0,0069 [−0,0120; −0,0025] | −0,0055 [−0,0108; −0,0010] |
| bank | en | 0,1682 | 0,0447 | −0,1234 [−0,1574; −0,0919] | −0,0494 [−0,0595; −0,0397] | −0,0099 [−0,0207; −0,0015] | −0,0055 [−0,0151; 0,0031] |
| hibaelhárítás | hu | 0,1936 | 0,0510 | −0,1427 [−0,1787; −0,1097] | −0,0387 [−0,0492; −0,0296] | −0,0215 [−0,0305; −0,0131] | −0,0117 [−0,0205; −0,0050] |
| hibaelhárítás | en | 0,2989 | 0,0397 | −0,2592 [−0,2855; −0,2304] | −0,0511 [−0,0578; −0,0448] | −0,0223 [−0,0298; −0,0156] | −0,0124 [−0,0199; −0,0061] |
| szabálycsalád | hu | 0,3289 | 0,0686 | −0,2603 [−0,2933; −0,2233] | −0,0489 [−0,0619; −0,0356] | −0,0115 [−0,0201; −0,0024] | −0,0172 [−0,0299; −0,0047] |
| szabálycsalád | en | 0,3071 | 0,0348 | −0,2723 [−0,3078; −0,2308] | −0,0617 [−0,0701; −0,0537] | −0,0307 [−0,0506; −0,0154] | −0,0186 [−0,0260; −0,0120] |

- **A magyar részszeleteken mindhárom családon és mindegyik összevetésben javít a B1-R.**
  - Az átlagos arány magyarul 0,26, angolul 0,15 (pontbecslés).
  - A magyar szeleteken a B1-R AURC-ja mindhárom családon nagyobb az angolnál.
- **Az egyetlen nem szignifikáns sor az angol bank SELECT-javulása.**

## 8. K2: a H tartalmi fej T-meta-finomhangolással

| család | H-T-meta − B1-S | ebből ΔE-AURC | ebből Δoptimum | H-T-meta − B1-R |
|---|---|---|---|---|
| bank | −0,0558 [−0,0714; −0,0408] | −0,0938 | +0,0380 | +0,0384 [0,0282; 0,0493] |
| hibaelhárítás | −0,1643 [−0,1886; −0,1409] | −0,2044 | +0,0401 | +0,0394 [0,0302; 0,0492] |
| szabálycsalád | −0,2195 [−0,2447; −0,1912] | −0,2520 | +0,0324 | +0,0343 [0,0239; 0,0451] |

- **A H-T-meta rangsora lényegében olyan jó, mint a B1-R-é.** Az E-AURC-ja 0,0058, 0,0043, illetve 0,0074.
- **A saját javaslatai viszont több hibát tartalmaznak.**
  - Az optimuma 0,077–0,081, a B1-é 0,039–0,044.
  - Ezért marad el a B1-R-től mindhárom családon.
- A H tartalmi feje a friss családokon nem jobb javaslattevő a B1-nél.

## 9. Enyhe helyesség (leíró)

| család | B1-S | B1-R | B1-R − B1-S | B1-LR − B1-S |
|---|---|---|---|---|
| bank | 0,0344 | 0,0382 | +0,0038 [−0,0017; 0,0087] | +0,0015 [−0,0014; 0,0047] |
| hibaelhárítás | 0,0207 | 0,0229 | +0,0022 [−0,0029; 0,0073] | +0,0178 [0,0131; 0,0234] |
| szabálycsalád | 0,0506 | 0,0409 | −0,0097 [−0,0164; −0,0028] | +0,0095 [0,0001; 0,0235] |

- **Enyhe helyességgel a szabály nem teljesülne:**
  - egy javuló család van;
  - az arány 0,965 [0,881; 1,063].
- **A fejek szigorú címkén tanultak**, ezért az enyhén helyes NONE-ok egy részét hátrasorolják.
- **A B1-R így is a B1-S szintjén marad, a szabálycsaládon jobb is.**
  - A B1-N enyhe helyességgel mindhárom családon rosszabb a B1-S-nél.
  - A B1-LR két családon rosszabb, a bankon a különbség nem szignifikáns.

## 10. Munkapont és kalibráció (8.4, leíró, nem része a szabálynak)

**A munkapont:**
- **A τ megválasztása:** a CAL-on, CP-alsó ≥ 0,95 és ≥ 200 elfogadott itemmel (D23: mennyiségi feltétel).
- **A mérés:** a TESZT-en.
- **A bootstrap:** a CAL és a TESZT sablonosan újramintázva, a τ replikánként újra.
- **Pontbecslés:** a futások átlaga.
- **A hibasorok:** a gold-állapot itemjeinek hányada, amelyen a kar a τ fölött hibásan dönt.

| család | kar | lefedettség (S+N) | precizitás | SELECT-lef. | SELECT NO_MATCH-en | SELECT MISSING/OOS-en | NONE MATCH-en | munkapont nélküli replika |
|---|---|---|---|---|---|---|---|---|
| bank | B1-S | nincs munkapont | — | — | — | — | — | 100% |
| bank | B1-N | nincs munkapont | — | — | — | — | — | 81% |
| bank | B1-LR | 0,447 [0,381; 0,703] | 0,989 [0,947; 0,997] | 0,441 | 2,5% | 0,0% | 0,0% | 14% |
| bank | **B1-R** | **0,665 [0,582; 0,732]** | **0,983 [0,957; 0,995]** | 0,545 | 4,5% | 0,7% | 0,0% | 0% |
| hibaelhárítás | B1-S | nincs munkapont | — | — | — | — | — | 100% |
| hibaelhárítás | B1-N | 0,407 [0,374; 0,548] | 0,983 [0,941; 0,995] | 0,407 | 1,5% | 2,0% | 0,0% | 29% |
| hibaelhárítás | B1-LR | 0,443 [0,359; 0,567] | 0,989 [0,948; 0,997] | 0,443 | 1,0% | 1,5% | 0,0% | 33% |
| hibaelhárítás | **B1-R** | **0,679 [0,618; 0,763]** | **0,975 [0,940; 0,990]** | 0,572 | 2,0% | 3,0% | 1,0% | 0,1% |
| szabálycsalád | B1-S | nincs munkapont | — | — | — | — | — | 100% |
| szabálycsalád | B1-N | nincs munkapont | — | — | — | — | — | 54% |
| szabálycsalád | B1-LR | 0,553 [0,436; 0,654] | 0,960 [0,925; 0,983] | 0,481 | 0,0% | 10,0% | 0,2% | 4% |
| szabálycsalád | **B1-R** | **0,717 [0,670; 0,746]** | **0,967 [0,950; 0,982]** | 0,591 | 3,7% | 5,8% | 0,2% | 0% |

- **A B1-R lefedettsége** a legjobb másik karénál 16–24 ponttal nagyobb.
- **A hibaelhárításon a precizitás intervallumának alsó határa (0,940) 0,95 alatt van.** A τ-szabály a CAL-on tartja a
  0,95-öt, a TESZT-en ez nem garantált.

**Kalibráció a TESZT-en, Platt nélkül → a CAL-on illesztett Platt-tal:**

| család | kar | Brier | ECE |
|---|---|---|---|
| bank | B1-S | 0,167 → 0,160 | 0,093 → 0,050 |
| bank | B1-LR | 0,067 → 0,065 | 0,049 → 0,031 |
| bank | B1-R | 0,042 → 0,040 | 0,025 → 0,019 |
| hibaelhárítás | B1-S | 0,199 → 0,188 | 0,161 → 0,114 |
| hibaelhárítás | B1-LR | 0,113 → 0,112 | 0,047 → 0,051 |
| hibaelhárítás | B1-R | 0,048 → 0,044 | 0,037 → 0,021 |
| szabálycsalád | B1-S | 0,204 → 0,197 | 0,090 → 0,090 |
| szabálycsalád | B1-LR | 0,089 → 0,089 | 0,047 → 0,035 |
| szabálycsalád | B1-R | 0,036 → 0,036 | 0,017 → 0,015 |

## Érvényességi kör és korlátok

- **A vizsgált tartomány:** a három vizsgált szintetikus család, az előírt összetétel (MATCH 60 / NO_MATCH 20 /
  MISSING_DATA 10 / OUT_OF_SCOPE 10%, fele magyar, D9) és az 500 példás célterületi adaptáció.
- **Az általánosítás iránya:** a családon belüli, a tanításkor nem látott sablonokra általánosít. Más családra vagy
  valódi adatra ez a mérés nem mond semmit.
- **Az eredmény a szigorú konvencióhoz kötött.** A nyereség nagyobbik része abból jön, hogy a fej megtanulja, mely
  NONE-javaslat esik MISSING_DATA- vagy OUT_OF_SCOPE-itemre (D20). Enyhe helyességnél a teljes nyereség eltűnik, a
  SELECT-javulás megmarad.
- **Az optimumhoz közeli rangsor (E-AURC 0,005) a szintetikus családok jól elkülönülő állapotait tükrözheti.**
- **A B1 hibái ezen az összetételen szinte mind állapothibák** (3. pont, állapotonkénti tábla). Az opciók közti
  tévesztés rendezéséről a mérés alig mond valamit (1–7 eset családonként).
  - A családterv „nehéz negatívjai” (azonos partner más összeggel, azonos összeg más partnernél, elírt számlaszám)
    a B1-nek nem nehezek: 600 MATCH-itemből 1, 7, illetve 5-nél választ rossz opciót.
  - A 3. szint (SELECT-AURC) ezért itt szinte csak az állapothibák felismerését méri.
- **A címkeminőség:** az audit címkehiba-arányának felső korlátja 1,57% (D14). Egy hibás címkéjű item a fej számára
  „biztos helyes” lehet, és a mérésben hibaként a rangsor elejére kerül. A 0,005-ös E-AURC és az 1,57% nem azonos
  mértékegység, de a nagyságrend hasonló; a B1-R és az optimum közti maradék különbséget ezért tovább nem értelmezzük.
- **A 2. szint teljes módszereket hasonlít (D10).** A B1-R és a B1-LR közti különbség nem bontja külön a rejtett
  állapotok és a tanítási eljárás hozzájárulását.

## Értelmezés (kézzel írt, 2026-10-31)

- **Az előre rögzített kérdésre a válasz igen.**
  - A célterületen 500 példán tanított megbízhatósági fej a B1 változatlan javaslatain mindhárom friss családon, mindkét
    nyelven jobban rendezi a helyes és a hibás javaslatokat, mint a B1 saját pontszáma.
  - A javulás mindhárom családon nagyobb, mint ami az egyszerű NONE-hátrasorolásból és az ötjellemzős referenciából
    adódik.
- **A nyereség nagyobbik része a konvenció megtanulása.**
  - A B1 a hatókörön kívüli esetet (a hibaelhárításon a hiányzó adat többségét is) ugyanúgy NONE-nal jelzi, mint a
    valódi nem-egyezést, és ebben nagyon biztos.
  - A szigorú helyesség ezt hibának számítja, ezért a B1-S rangsorának elején biztos hibák állnak.
  - Ennek háromnegyedét egy szabály (NONE hátra) is kezeli. A NO_MATCH és a többi NONE szétválasztását a B1-LR is nagyrészt
    megtanulja a B1 kimenetéből (NONE-on belüli AUROC 0,87–0,99).
- **A rejtett állapotú fej a SELECT-javaslatokon hoz olyat, amit a referencia nem.**
  - A SELECT-AURC 13–57%-kal kisebb, a B1-LR a SELECT-en nem javít.
  - A SELECT-hibák 92–99%-a állapothiba (hiányzó adat vagy nem-egyezés mögött választott opció). A fej tehát itt is
    elsősorban az állapotot ismeri fel, nem az opciók közti tévesztést. Ez a lelet nem függ a NONE-konvenciótól. A bankon és a szabálycsaládon csak a teljes
  T500-zal jön elő, a hibaelhárításon már T200-nál.
- **A következő kör nyitott kérdései** (Dani döntése; ez a lap nem rögzít tervet):
  - **Konvenció vagy megbízhatóság?** Megmarad-e a nyereség, ha a B1 maga is meg tudja különböztetni a hiányzó adatot és
    a hatókörön kívüli esetet a nem-egyezéstől (külön opció vagy utasítás a promptban)?
  - **Valódi adaton (csak értékelésre):** mekkora az elválasztás és a SELECT-javulás?

## Előzmény

- A 06 F1-pilotja ugyanezt az irányt mutatta (`kor06/eredmenyek/F1`): ott is a NONE-konvenció vitte a nyereséget.
- A D20 ezért írta elő a bontást kötelező, kiemelt sorként a rögzítés előtt.

## Lezárás (Dani, 2026-10-31)

- **A 06-os kör sikeres a vállalt kérdésben.** A sikerkritériumot utólag nem módosítjuk.
- **A fő tanulság:** a fej jelenleg főleg azt ismeri fel, hogy egyáltalán indokolt-e dönteni.
- **A következő kör** ([07-runbook](../../../07-runbook.md)):
  1. erősebb B1-referencia: a B1 maga is jelezheti a négy állapotot;
  2. utána valódi magyar adat egy családon.
