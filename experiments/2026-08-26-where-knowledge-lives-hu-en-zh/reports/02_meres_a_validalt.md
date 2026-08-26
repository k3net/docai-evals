# Mérés A — ellenőrző validáció ✅ LEZÁRVA (2026-08-25)

A kötelező ellenőrző kör (ZH + HU, **102/102 válasz**) elkészült, és **be van építve a pipeline-ba**:
a `results/scores.csv` `manual` oszlopa hordozza, az `code/analyze_a.py` pedig alkalmazza.

**→ A számok helye: [`02_meres_a.md`](02_meres_a.md)** (generált). Külön „validált" változat
NINCS és nem is lesz — a dolgozatba kizárólag generált riport száma kerülhet.
**→ Az ítéletek tételes indoklása: [`kezi_validacio_naplo.md`](kezi_validacio_naplo.md).**

## Mit hozott a ellenőrző kör

| | |
|---|---|
| a 35B bíráló egyetértése a ellenőrző ítélettel | **57/102 = 56 %** |
| a második gépi vélemény (Claude) egyetértése | **70/102 = 69 %** |
| ebből a **pontosságot** módosító korrekció | **2** (HU08/en, ZH17/en) — mindkettő a gépi bíráló engedékenységéből |
| kategória-átsorolás | **43**, jellemzően `helytelen` → `hallucinacio` |

⭐ A ellenőrző kör fő hatása tehát nem a pontossági mátrix, hanem a **tévedés MÓDJA**: a gépi
bíráló 162 válaszból alig kettőt nevezett hallucinációnak, a ellenőrző kör után a téves válaszok
**50–86 %-a** magabiztos kitaláció. Ez külön táblát kapott a generált riportban.

⚠️ A pontosságot módosító 2 korrekció **mindkettő egy irányba** mutat (a gépi bíráló
engedékenyebb volt), és mindkettő a **nem forrásnyelvi** cellában áll — vagyis a ellenőrző kör
nélkül a dolgozat fő állítása (a tudás átmegy a nyelvhatáron) **erősebbnek** látszana.

## Előzmény — a 08-24-i kör visszavonva

Az első ellenőrző kör a beadott CSV sérülése miatt elveszett (6 szerkezetileg tört sor, 46
ZH-sorban kicserélt válaszszöveg), és a belőle írt riport „102/162 KÉSZ"-t állított, miközben
54 ítélet volt átmenthető. Az eredeti fájl: `scratchpad/02_meres_a_validalt.eredeti-08-24.md`.
**A 08-25-i kör ellenőrizve:** minden gépi oszlop bitre egyezik a méréssel, 102 érvényes ítélet,
0 szerkezeti hiba.
