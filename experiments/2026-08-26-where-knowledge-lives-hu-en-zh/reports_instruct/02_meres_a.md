# Mérés A — válaszminőség (3×3 pontossági mátrix)

Forrás: `results/scores.csv` (162 faktuális válasz) · az ellenőrző körben újraítélve: **102/162**

## Szigorú pontosság (csak „helyes”)

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 58% | 58% | 63% |
| **HU** (n=15) | 20% | 27% | 33% |
| **UNI** (n=20) | 100% | 100% | 100% |

## Megengedő pontosság („helyes” + „részben”)

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 74% | 58% | 68% |
| **HU** (n=15) | 20% | 40% | 53% |
| **UNI** (n=20) | 100% | 100% | 100% |

## Ítélet-eloszlás cellánként

| csoport / nyelv | n | helyes | részben | helytelen | halluc. | csonkolt | degenerált |
|---|---|---|---|---|---|---|---|
| ZH / hu | 19 | 11 | 3 | 2 | 3 | 14 | 0 |
| ZH / en | 19 | 11 | 0 | 4 | 4 | 4 | 0 |
| ZH / zh | 19 | 12 | 1 | 2 | 4 | 5 | 0 |
| HU / hu | 15 | 3 | 0 | 1 | 11 | 13 | 0 |
| HU / en | 15 | 4 | 2 | 2 | 7 | 7 | 0 |
| HU / zh | 15 | 5 | 3 | 0 | 7 | 10 | 0 |
| UNI / hu | 20 | 20 | 0 | 0 | 0 | 9 | 0 |
| UNI / en | 20 | 20 | 0 | 0 | 0 | 3 | 0 |
| UNI / zh | 20 | 20 | 0 | 0 | 0 | 4 | 0 |

## Kontroll — csak a csonkolatlan, nem degenerált válaszok

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | 100% (n=5) | 67% (n=15) | 79% (n=14) |
| **HU** | 50% (n=2) | 25% (n=8) | 60% (n=5) |
| **UNI** | 100% (n=11) | 100% (n=17) | 100% (n=16) |

Ha ez a tábla ugyanazt a mintázatot mutatja, mint a teljes mátrix, akkor a nyelvek közti különbség **nem** a token-keretből és nem az ismétlési hurkokból jön.

## Hallucináció — magabiztosan állított, kitalált konkrétum

A `hallucinacio` ítélet akkor jár, ha a válasz KONKRÉT tényt állít (nevet, helyet, dátumot, intézményt), és az téves — szemben a `helytelen`-nel, ami kitérés, rossz kategória vagy nem-válasz. ⛔ A gépi bíráló ezt a kategóriát gyakorlatilag nem használta, ezért az alábbi arányok **csak az ellenőrző körrel fedett csoportokra** (ZH, HU) érvényesek.

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** (n=19) | 16% (3/19) | 21% (4/19) | 21% (4/19) |
| **HU** (n=15) | 73% (11/15) | 47% (7/15) | 47% (7/15) |

A tévedés MÓDJA: a nem helyes válaszokon belül mekkora a magabiztos kitaláció aránya.

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | 60% (3/5) | 50% (4/8) | 67% (4/6) |
| **HU** | 92% (11/12) | 78% (7/9) | 100% (7/7) |

⭐ Ha a modell egy nyelven nem tudja a választ, az látszik-e rajta? A második tábla erre felel: minél magasabb a szám, annál gyakrabban **talál ki** ahelyett, hogy kitérne — vagyis annál kevésbé jelzi a saját tudatlanságát.


## A runbook két kérdése

**1. Átmegy-e a tudás a nyelvhatáron?** A ZH-only csoport magyar promptra **58%** (n=19, 95% CI 36%–77%), kínai promptra 63%. Nem nulla → a tudás átmegy, nem csak a forrásnyelven érhető el.

**2. Aszimmetria.** ZH-only → hu: **58%** · HU-only → zh: **33%** (a saját forrásnyelvén: ZH/zh 63% · HU/hu 20%). A kínai tudás könnyebben megy magyarra, mint fordítva — korpuszméret-hatás.

⛔ **Olvasási figyelmeztetés:** a csonkolt és a degenerált válaszok cellánkénti számát a fenti tábla külön hozza. Ahol ezek aránya magas (jellemzően a magyar oszlop), ott a pontosság a dekódolás műtermékét is méri, nem csak a tudást — a következtetést erre a sorra is rá kell építeni.

## Megbízhatóság — három értékelő ugyanazon a 102 válaszon

A kötelező ellenőrző kör (ZH + HU, 102 válasz) **elkészült**, ezért a `final` oszlop a ellenőrző ítéleteimet használja. Az alábbi tábla azt méri, mennyire estek ehhez közel a gépi értékelők.

| értékelő | egyetértés a ellenőrző ítéleteimmel |
|---|---|
| Qwen3.6-35B bíráló (a mérés bírálója) | **57/102 = 56%** |
| Claude, második gépi vélemény | – |

A 45 eltérésből **1 változtatja meg a pontosságot** (helyes ↔ nem helyes), a többi **44 kategória-átsorolás** — jellemzően `helytelen` → `hallucinacio`, amit a bíráló szinte soha nem használt.

### A 3×3 mátrix a ellenőrző kör nélkül és vele

| csoport | hu | en | zh |
|---|---|---|---|
| **ZH** | **58%** | **58%** | **63%** |
| **HU** | **20%** | **27%** | **33%** *(gépi: 40%)* |
| **UNI** | **100%** | **100%** | **100%** |

*(vastagon a végleges, ellenőrző ítéletekre épülő érték; zárójelben a gépi bíráló egyedüli értéke, ahol eltér — a UNI csoport nem volt a kötelező körben)*

⭐ **A pontosságot módosító korrekció 1 darab** (HU02/zh), és **mind a 1 egy irányba mutat: a gépi bíráló ENGEDÉKENYEBB volt**; 1 a **NEM forrásnyelvi** cellában áll. A gépi bíráló hibája tehát a nyelvhatáron átmenő tudást inkább FELÜLbecsli — vagyis a ellenőrző kör nélkül a dolgozat fő állítása (a tudás átmegy) **erősebbnek** látszana, mint amilyen.

⛔ **Korlát:** a ellenőrző kört én pontoztam, és a korpuszt is én állítottam össze, tehát nem vagyok vak értékelő. A ellenőrző kör ítéleteinek tételes indoklása a `reports/kezi_validacio_naplo.md`-ben olvasható; a gépi bírálók ítéletei a `results/judge.jsonl`-ben és a `results/review_claude.csv`-ben maradtak meg, tehát a korrekciók visszakereshetők.

