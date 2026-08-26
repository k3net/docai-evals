# Ellenőrző validáció — ellenőrzési napló

> ⚠️ **Terminológia (2026-08-26):** ahol ez a dokumentum „ellenőrző kör”-t vagy „ellenőrző bírálatt” ír, az a
> **GPT-5.6 Sol ellenőrző bírálata** (tételenként, a teljes válasszal és a rubrikával, a Qwen3.6-35B
> gépi bíráló ítélete mellé); emberi vak értékelés nem történt. A dolgozat ezt végig „ellenőrző kör”
> néven hozza.

## Hatókör

- Mérés A: **102/102 kötelező válasz** (HU + ZH csoport) tételesen újraítélve az ellenőrző bírálóval, és a `manual` oszlop kitöltve.
- Mérés D1: **48/48 UNT-válasz** komponensenként átnézve; `manual_native` és `manual_distortion` kitöltve.
- D1 kontroll: nem módosítva (opcionális kör).
- Nyelvosztályozó 100 tokenes minta: nem módosítva (opcionális harmadik kör).

## Mérés A — eltérések a gépi bírálótól

Összesen **45 / 102** pontos címkeeltérés. Ezek többsége nem pontosságváltozás, hanem `helytelen` → `hallucinacio` átsorolás a rubrika konkrét kitalált tényekre vonatkozó szabálya miatt.

| item | nyelv | gépi | ellenőrző | várt válasz |
|---|---|---|---|---|
| HU01 | en | helytelen | hallucinacio | helping a woman who has just given birth (lying-in) |
| HU01 | hu | helytelen | hallucinacio | gyermekágyas asszony megsegítése |
| HU02 | zh | helytelen | hallucinacio | 棕枝主日（复活节前的星期日） |
| HU03 | en | helytelen | hallucinacio | carry firewood |
| HU03 | hu | helytelen | hallucinacio | fát hordani |
| HU03 | zh | helytelen | hallucinacio | 搬木柴 |
| HU05 | hu | helytelen | hallucinacio | szabadidő |
| HU06 | en | helytelen | hallucinacio | Zala |
| HU06 | hu | helytelen | hallucinacio | Zala |
| HU06 | zh | helytelen | hallucinacio | 佐洛州 |
| HU08 | en | helyes | reszben | between Christmas and New Year |
| HU08 | zh | helytelen | hallucinacio | 圣诞节到新年之间 |
| HU09 | en | helytelen | hallucinacio | Moha |
| HU09 | hu | helytelen | hallucinacio | Moha |
| HU10 | en | helytelen | hallucinacio | Easter (Palm Sunday / Low Sunday) |
| HU10 | hu | helytelen | hallucinacio | húsvét (virágvasárnap / fehérvasárnap) |
| HU12 | en | helytelen | hallucinacio | István Csukás |
| HU12 | hu | helytelen | hallucinacio | Csukás István |
| HU13 | en | helytelen | hallucinacio | Puli |
| HU13 | hu | helytelen | reszben | puli |
| HU14 | en | helytelen | hallucinacio | Magda Szabó |
| HU14 | hu | helytelen | hallucinacio | Szabó Magda |
| HU14 | zh | helytelen | hallucinacio | 萨博·玛格达（Szabó Magda） |
| HU15 | en | helytelen | hallucinacio | National Training Register (Országos Képzési Jegyzék) |
| ZH02 | en | helytelen | hallucinacio | Hubei |
| ZH02 | hu | helytelen | hallucinacio | Hubei |
| ZH02 | zh | helytelen | hallucinacio | 湖北 |
| ZH03 | en | helytelen | hallucinacio | duck, rabbit, fish |
| ZH03 | hu | helytelen | hallucinacio | kacsa, nyúl, hal |
| ZH04 | hu | helytelen | hallucinacio | hajdina |
| ZH06 | zh | helytelen | hallucinacio | 温州 |
| ZH07 | en | helytelen | hallucinacio | Fangyan (Yongkang) |
| ZH07 | hu | helytelen | hallucinacio | Fangyan (Yongkang) |
| ZH08 | en | helytelen | reszben | glutinous rice, red dates (jujube) |
| ZH08 | hu | helytelen | reszben | ragacsos rizs, vörös datolya |
| ZH10 | en | helytelen | hallucinacio | Duanwu (Dragon Boat Festival) |
| ZH10 | zh | helytelen | hallucinacio | 端午节 |
| ZH11 | en | helytelen | hallucinacio | Hebei |
| ZH11 | zh | helytelen | hallucinacio | 河北 |
| ZH12 | hu | helytelen | hallucinacio | Chongqing |
| ZH16 | hu | helytelen | hallucinacio | Anhui |
| ZH17 | en | helyes | reszben | lotus |
| ZH17 | hu | helytelen | hallucinacio | lótusz |
| ZH17 | zh | helytelen | hallucinacio | 荷花 |
| ZH19 | en | helytelen | hallucinacio | Zhejiang |

## Mérés D1 — darabszám-eltérések

Összesen **31 / 48** sorban változott legalább az egyik darabszám.

| item | nyelv | native gépi | native ellenőrző | distortion gépi | distortion ellenőrző |
|---|---|---|---|---|---|
| UNT-HU01 | en | 1.0 | 1.0 | 2.0 | 0.0 |
| UNT-HU01 | zh | 1.0 | 1.0 | 2.0 | 0.0 |
| UNT-HU02 | en | 2.0 | 0.0 | 0.0 | 0.0 |
| UNT-HU03 | en | 2.0 | 1.0 | 0.0 | 2.0 |
| UNT-HU03 | hu | 2.0 | 1.0 | 0.0 | 2.0 |
| UNT-HU03 | zh | 2.0 | 1.0 | 0.0 | 2.0 |
| UNT-HU04 | hu | 1.0 | 1.0 | 2.0 | 1.0 |
| UNT-HU04 | zh | 3.0 | 2.0 | 2.0 | 0.0 |
| UNT-HU05 | hu | 3.0 | 3.0 | 1.0 | 0.0 |
| UNT-HU07 | en | 2.0 | 1.0 | 1.0 | 1.0 |
| UNT-HU07 | hu | 2.0 | 0.0 | 0.0 | 0.0 |
| UNT-HU07 | zh | 3.0 | 2.0 | 0.0 | 0.0 |
| UNT-HU08 | en | 2.0 | 1.0 | 1.0 | 2.0 |
| UNT-HU08 | zh | 0.0 | 0.0 | 2.0 | 1.0 |
| UNT-ZH01 | en | 3.0 | 2.0 | 0.0 | 0.0 |
| UNT-ZH01 | hu | 3.0 | 2.0 | 0.0 | 0.0 |
| UNT-ZH01 | zh | 1.0 | 0.0 | 1.0 | 0.0 |
| UNT-ZH02 | en | 2.0 | 1.0 | 1.0 | 0.0 |
| UNT-ZH02 | hu | 2.0 | 1.0 | 0.0 | 1.0 |
| UNT-ZH03 | en | 3.0 | 2.0 | 1.0 | 0.0 |
| UNT-ZH03 | hu | 2.0 | 2.0 | 1.0 | 0.0 |
| UNT-ZH04 | en | 3.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH04 | hu | 3.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH04 | zh | 3.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH05 | en | 3.0 | 3.0 | 1.0 | 0.0 |
| UNT-ZH06 | en | 2.0 | 2.0 | 2.0 | 1.0 |
| UNT-ZH06 | zh | 2.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH07 | en | 2.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH07 | hu | 2.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH07 | zh | 2.0 | 1.0 | 0.0 | 0.0 |
| UNT-ZH08 | hu | 3.0 | 2.0 | 0.0 | 0.0 |

## Különösen fontos ellenőrző döntések

- `HU08/en`: **reszben** — a „Christmas season” jó időszakot céloz, de nem adja meg a kért karácsony–újév ablakot.
- `HU13/hu`: **reszben** — a „magyar juhász” kategória a puli felé mutat, de nem nevezi meg a fajtát.
- `ZH08/hu` és `ZH08/en`: **reszben** — a két kért alapanyagból a ragacsos rizs megvan, a vörös datolya hiányzik / téves.
- `ZH17/en`: **reszben** — a helyes „lotus” szerepel, de a válasz tévesen egyenrangú alternatívaként hozzáteszi a „water lily”-t.
- A `hallucinacio` címkét akkor használtam, amikor a hibás válasz konkrét kitalált szerzőt, helyet, dátumot, intézményt vagy részletes fabrikált tényt állított; egyszerű rossz kategória vagy nem-válasz `helytelen` maradt.

## D1 értelmezési elv

Egy komponens csak akkor kapott találatot, ha a komponens tartalmi magja ténylegesen megjelent. Összetett komponensnél nem vettem automatikusan teljes találatnak egy részletet. A torzításokat is pozitív állításként kezeltem: csak akkor számoltam, ha a hibás keretezés a válaszban ténylegesen megjelent, puszta hiányból nem következtettem rá — kivéve ahol maga a torzítás definíciója kifejezetten egy jelentésárnyalat hiánya volt.
