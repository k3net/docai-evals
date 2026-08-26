# Mérés D — ellenőrző validáció ✅ LEZÁRVA (2026-08-25)

A D1 kötelező köre (**48/48 UNT-válasz**, komponensenként) elkészült, és be van építve a
pipeline-ba: a `results/d1_scores.csv` `manual_native` / `manual_distortion` oszlopa hordozza,
az `src/analyze_d.py` alkalmazza.

**→ A számok helye: [`05_meres_d.md`](05_meres_d.md)** (generált).
**→ Az értelmezési elv és a tételes eltérések: [`kezi_validacio_naplo.md`](kezi_validacio_naplo.md).**

## Mit hozott a ellenőrző kör

**31/48 sorban** változott legalább az egyik darabszám, és a mozgás **egyirányú**: én
szigorúbb voltam a bírálónál. A `native` arány minden cellában csökkent (pl. zh-forrás/angol
88 % → **62 %**), a `distortion` is (zh-forrás/kínai 12 % → **6 %**).

⭐ **A D mérés ítélete NEM változott:** a forrásnyelv egyik irányban sem ad többletet az
angolhoz képest (előjelteszt p = 0,625 mindkét irányban), sőt mindkét irányban valamivel
gyengébb. A szigorúbb pontozás a szinteket vitte lejjebb, a MINTÁZATOT nem.

⚠️ A D1 kontroll (48 hétköznapi szó) tudatosan a gépi ítéleten maradt — opcionális kör volt.

## Előzmény — a 08-24-i kör visszavonva

Az akkori fájlban az UNT-ZH08 `native_n` nevezője 3-ról 2-re változott, ami ellentmond a
08-22-én befagyasztott `items.jsonl`-nek, ezért csak 39 ítélet volt átmenthető.
Az eredeti riport: `scratchpad/05_meres_d_validalt.eredeti-08-24.md`.
**A 08-25-i kör ellenőrizve:** a gépi oszlopok numerikusan egyeznek a méréssel (az eltérés
kizárólag a `1` → `1.0` írásmód volt, normalizálva), a `native_n` egyezik a fagyasztott
korpusszal, 48/48 érvényes darabszám, tartományhiba nincs.
