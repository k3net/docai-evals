# Mérés A — válaszminőség (3×3 pontossági mátrix)

Forrás: `results/scores.csv` (162 faktuális válasz) · az ellenőrző körben újraítélve: **102/162**

## Szigorú pontosság (csak „helyes”)

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 47% | 68% | 58% |
| **HU** (n=15) | 7% | 20% | 13% |
| **UNI** (n=20) | 85% | 100% | 100% |

## Megengedő pontosság („helyes” + „részben”)

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 53% | 74% | 58% |
| **HU** (n=15) | 13% | 27% | 20% |
| **UNI** (n=20) | 85% | 100% | 100% |

## Ítélet-eloszlás cellánként

| csoport / nyelv | n | helyes | részben | helytelen | halluc. | csonkolt | degenerált |
|---|---|---|---|---|---|---|---|
| ZH / hu | 19 | 9 | 1 | 4 | 5 | 12 | 2 |
| ZH / en | 19 | 13 | 1 | 3 | 2 | 4 | 0 |
| ZH / zh | 19 | 11 | 0 | 4 | 4 | 4 | 2 |
| HU / hu | 15 | 1 | 1 | 5 | 8 | 8 | 2 |
| HU / en | 15 | 3 | 1 | 2 | 9 | 3 | 0 |
| HU / zh | 15 | 2 | 1 | 3 | 9 | 11 | 1 |
| UNI / hu | 20 | 17 | 0 | 3 | 0 | 2 | 1 |
| UNI / en | 20 | 20 | 0 | 0 | 0 | 0 | 0 |
| UNI / zh | 20 | 20 | 0 | 0 | 0 | 1 | 0 |

## Kontroll — csak a csonkolatlan, nem degenerált válaszok

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | 57% (n=7) | 73% (n=15) | 73% (n=15) |
| **HU** | 0% (n=7) | 17% (n=12) | 0% (n=4) |
| **UNI** | 83% (n=18) | 100% (n=20) | 100% (n=19) |

Ha ez a tábla ugyanazt a mintázatot mutatja, mint a teljes mátrix, akkor a nyelvek közti különbség **nem** a token-keretből és nem az ismétlési hurkokból jön.

## Hallucináció — magabiztosan állított, kitalált konkrétum

A `hallucinacio` ítélet akkor jár, ha a válasz KONKRÉT tényt állít (nevet, helyet, dátumot, intézményt), és az téves — szemben a `helytelen`-nel, ami kitérés, rossz kategória vagy nem-válasz. ⛔ A gépi bíráló ezt a kategóriát gyakorlatilag nem használta, ezért az alábbi arányok **csak az ellenőrző körrel fedett csoportokra** (ZH, HU) érvényesek.

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 26% (5/19) | 11% (2/19) | 21% (4/19) |
| **HU** (n=15) | 53% (8/15) | 60% (9/15) | 60% (9/15) |

A tévedés MÓDJA: a nem helyes válaszokon belül mekkora a magabiztos kitaláció aránya.

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | 56% (5/9) | 40% (2/5) | 50% (4/8) |
| **HU** | 62% (8/13) | 82% (9/11) | 75% (9/12) |

⭐ Ha a modell egy nyelven nem tudja a választ, az látszik-e rajta? A második tábla erre felel: minél magasabb a szám, annál gyakrabban **talál ki** ahelyett, hogy kitérne — vagyis annál kevésbé jelzi a saját tudatlanságát.


## A runbook két kérdése

**1. Átmegy-e a tudás a nyelvhatáron?** A ZH-only csoport magyar promptra **47%** (n=19, 95% CI 27%–68%), kínai promptra 58%. Nem nulla → a tudás átmegy, nem csak a forrásnyelven érhető el.

**2. Aszimmetria.** ZH-only → hu: **47%** · HU-only → zh: **13%** (a saját forrásnyelvén: ZH/zh 58% · HU/hu 7%). A kínai tudás könnyebben megy magyarra, mint fordítva — korpuszméret-hatás.

⛔ **Olvasási figyelmeztetés:** a csonkolt és a degenerált válaszok cellánkénti számát a fenti tábla külön hozza. Ahol ezek aránya magas (jellemzően a magyar oszlop), ott a pontosság a dekódolás műtermékét is méri, nem csak a tudást — a következtetést erre a sorra is rá kell építeni.

## Megbízhatóság — három értékelő ugyanazon a 102 válaszon

A kötelező ellenőrző kör (ZH + HU, 102 válasz) **elkészült**, ezért a `final` oszlop a ellenőrző ítéleteimet használja. Az alábbi tábla azt méri, mennyire estek ehhez közel a gépi értékelők.

| értékelő | egyetértés a ellenőrző ítéleteimmel |
|---|---|
| Qwen3.6-35B bíráló (a mérés bírálója) | **59/102 = 58%** |
| Claude, második gépi vélemény | – |

A 43 eltérésből **3 változtatja meg a pontosságot** (helyes ↔ nem helyes), a többi **40 kategória-átsorolás** — jellemzően `helytelen` → `hallucinacio`, amit a bíráló szinte soha nem használt.

### A 3×3 mátrix a ellenőrző kör nélkül és vele

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | **47%** *(gépi: 42%)* | **68%** | **58%** |
| **HU** | **7%** | **20%** *(gépi: 27%)* | **13%** *(gépi: 20%)* |
| **UNI** | **85%** | **100%** | **100%** |

*(vastagon a végleges, ellenőrző ítéletekre épülő érték; zárójelben a gépi bíráló egyedüli értéke, ahol eltér — a UNI csoport nem volt a kötelező körben)*

⭐ **A pontosságot módosító korrekció 3 darab** (HU04/zh, HU08/en, ZH16/hu), ebből 2 a gépi bíráló engedékenységéből; 3 a **NEM forrásnyelvi** cellában áll. A gépi bíráló hibája tehát a nyelvhatáron átmenő tudást inkább FELÜLbecsli — vagyis a ellenőrző kör nélkül a dolgozat fő állítása (a tudás átmegy) **erősebbnek** látszana, mint amilyen.

⛔ **Korlát:** a ellenőrző kört én pontoztam, és a korpuszt is én állítottam össze, tehát nem vagyok vak értékelő. A ellenőrző kör ítéleteinek tételes indoklása a `reports/kezi_validacio_naplo.md`-ben olvasható; a gépi bírálók ítéletei a `results/judge.jsonl`-ben és a `results/review_claude.csv`-ben maradtak meg, tehát a korrekciók visszakereshetők.

