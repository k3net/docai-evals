# Mérés A — válaszminőség (3×3 pontossági mátrix)

Forrás: `results/scores.csv` (162 faktuális válasz) · az ellenőrző körben újraítélve: **102/162**

## Szigorú pontosság (csak „helyes”)

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 42% | 53% | 63% |
| **HU** (n=15) | 7% | 13% | 20% |
| **UNI** (n=20) | 90% | 100% | 100% |

## Megengedő pontosság („helyes” + „részben”)

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 47% | 63% | 63% |
| **HU** (n=15) | 13% | 20% | 20% |
| **UNI** (n=20) | 90% | 100% | 100% |

## Ítélet-eloszlás cellánként

| csoport / nyelv | n | helyes | részben | helytelen | halluc. | csonkolt | degenerált |
|---|---|---|---|---|---|---|---|
| ZH / hu | 19 | 8 | 1 | 3 | 7 | 8 | 4 |
| ZH / en | 19 | 10 | 2 | 1 | 6 | 2 | 0 |
| ZH / zh | 19 | 12 | 0 | 1 | 6 | 3 | 0 |
| HU / hu | 15 | 1 | 1 | 5 | 8 | 9 | 1 |
| HU / en | 15 | 2 | 1 | 3 | 9 | 0 | 0 |
| HU / zh | 15 | 3 | 0 | 6 | 6 | 3 | 1 |
| UNI / hu | 20 | 18 | 0 | 2 | 0 | 5 | 1 |
| UNI / en | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| UNI / zh | 20 | 20 | 0 | 0 | 0 | 0 | 0 |

## Kontroll — csak a csonkolatlan, nem degenerált válaszok

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | 55% (n=11) | 59% (n=17) | 69% (n=16) |
| **HU** | 0% (n=6) | 13% (n=15) | 17% (n=12) |
| **UNI** | 87% (n=15) | 100% (n=20) | 100% (n=20) |

Ha ez a tábla ugyanazt a mintázatot mutatja, mint a teljes mátrix, akkor a nyelvek közti különbség **nem** a token-keretből és nem az ismétlési hurkokból jön.

## Hallucináció — magabiztosan állított, kitalált konkrétum

A `hallucinacio` ítélet akkor jár, ha a válasz KONKRÉT tényt állít (nevet, helyet, dátumot, intézményt), és az téves — szemben a `helytelen`-nel, ami kitérés, rossz kategória vagy nem-válasz. ⛔ A gépi bíráló ezt a kategóriát gyakorlatilag nem használta, ezért az alábbi arányok **csak az ellenőrző körrel fedett csoportokra** (ZH, HU) érvényesek.

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 37% (7/19) | 32% (6/19) | 32% (6/19) |
| **HU** (n=15) | 53% (8/15) | 60% (9/15) | 40% (6/15) |

A tévedés MÓDJA: a nem helyes válaszokon belül mekkora a magabiztos kitaláció aránya.

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | 70% (7/10) | 86% (6/7) | 86% (6/7) |
| **HU** | 62% (8/13) | 75% (9/12) | 50% (6/12) |

⭐ Ha a modell egy nyelven nem tudja a választ, az látszik-e rajta? A második tábla erre felel: minél magasabb a szám, annál gyakrabban **talál ki** ahelyett, hogy kitérne — vagyis annál kevésbé jelzi a saját tudatlanságát.


## A runbook két kérdése

**1. Átmegy-e a tudás a nyelvhatáron?** A ZH-only csoport magyar promptra **42%** (n=19, 95% CI 23%–64%), kínai promptra 63%. Nem nulla → a tudás átmegy, nem csak a forrásnyelven érhető el.

**2. Aszimmetria.** ZH-only → hu: **42%** · HU-only → zh: **20%** (a saját forrásnyelvén: ZH/zh 63% · HU/hu 7%). A kínai tudás könnyebben megy magyarra, mint fordítva — korpuszméret-hatás.

⛔ **Olvasási figyelmeztetés:** a csonkolt és a degenerált válaszok cellánkénti számát a fenti tábla külön hozza. Ahol ezek aránya magas (jellemzően a magyar oszlop), ott a pontosság a dekódolás műtermékét is méri, nem csak a tudást — a következtetést erre a sorra is rá kell építeni.

## Megbízhatóság — három értékelő ugyanazon a 102 válaszon

A kötelező ellenőrző kör (ZH + HU, 102 válasz) **elkészült**, ezért a `final` oszlop a ellenőrző ítéleteimet használja. Az alábbi tábla azt méri, mennyire estek ehhez közel a gépi értékelők.

| értékelő | egyetértés a ellenőrző ítéleteimmel |
|---|---|
| Qwen3.6-35B bíráló (a mérés bírálója) | **57/102 = 56%** |
| Claude, második gépi vélemény (más modellcsalád) | **70/102 = 69%** |

A 45 eltérésből **2 változtatja meg a pontosságot** (helyes ↔ nem helyes), a többi **43 kategória-átsorolás** — jellemzően `helytelen` → `hallucinacio`, amit a bíráló szinte soha nem használt.

### A 3×3 mátrix a ellenőrző kör nélkül és vele

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | **42%** | **53%** *(gépi: 58%)* | **63%** |
| **HU** | **7%** | **13%** *(gépi: 20%)* | **20%** |
| **UNI** | **90%** | **100%** | **100%** |

*(vastagon a végleges, ellenőrző ítéletekre épülő érték; zárójelben a gépi bíráló egyedüli értéke, ahol eltér — a UNI csoport nem volt a kötelező körben)*

⭐ **A pontosságot módosító korrekció 2 darab** (HU08/en, ZH17/en), és **mind a 2 egy irányba mutat: a gépi bíráló ENGEDÉKENYEBB volt**; 2 a **NEM forrásnyelvi** cellában áll. A gépi bíráló hibája tehát a nyelvhatáron átmenő tudást inkább FELÜLbecsli — vagyis a ellenőrző kör nélkül a dolgozat fő állítása (a tudás átmegy) **erősebbnek** látszana, mint amilyen.

⛔ **Korlát:** a ellenőrző kört én pontoztam, és a korpuszt is én állítottam össze, tehát nem vagyok vak értékelő. A ellenőrző kör ítéleteinek tételes indoklása a `reports/kezi_validacio_naplo.md`-ben olvasható; a gépi bírálók ítéletei a `results/judge.jsonl`-ben és a `results/review_claude.csv`-ben maradtak meg, tehát a korrekciók visszakereshetők.

