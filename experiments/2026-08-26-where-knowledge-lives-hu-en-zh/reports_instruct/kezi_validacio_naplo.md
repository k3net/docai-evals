# Ellenőrző validáció — 2. kör

> ⚠️ **Terminológia (2026-08-26):** ahol ez a dokumentum „ellenőrző kör”-t vagy „ellenőrző bírálatt” ír, az a
> **GPT-5.6 Sol ellenőrző bírálata** (tételenként, a teljes válasszal és a rubrikával, a Qwen3.6-35B
> gépi bíráló ítélete mellé); emberi vak értékelés nem történt. A dolgozat ezt végig „ellenőrző kör”
> néven hozza.

Az ellenőrzés a `00_KEZI_KOR_UTMUTATO.md` mércéje szerint készült. A csonkolást és a formázást önmagában nem büntettem; csak a látható tartalmat értékeltem. A konkrét kitalált szerzőt, helyet, dátumot vagy részletes fabrikált tényt `hallucinacio`, a közeli időablakot vagy részben eltalált felsorolást `reszben` címkével jelöltem.

## Eredmény

- Mérés A: **102/102** kézzel minősítve
- D1: **48/48** válasz kézi native/distortion darabszámmal ellátva
- Mérés A kézi megoszlása: **46 helyes**, **9 részben**, **11 helytelen**, **36 hallucináció**
- A gépi ítélettől eltérő Mérés A-döntések: **45**
- A gépi komponensszámtól eltérő D1-döntések: **6**

## Különösen fontos ellenőrző döntések

- A gépi bíráló által egyszerűen helytelennek jelölt, konkrétan kitalált szerzőket, településeket, dátumokat és részletes népszokás-leírásokat hallucinációnak vettem.
- A villőzésnél az Easter Sunday/Palm Sunday közelséget, a regölésnél a tágabb karácsonyi időszakot, valamint az egy részben eltalált összetevő- vagy állatfelsorolásokat részben helyesnek vettem.
- A csonkolt HU03/en és ZH08/en válaszban a keresett információ nem jelent meg; ezek helytelenek, nem hallucinációk.
- D1-ben csak ténylegesen megjelenő tartalmi magot számoltam. Emiatt például az utazó előadócsoportként leírt `kaláka` nem kapott közösségi-munka komponenst, a `面子`–`脸` különbséget pedig nem tekintettem teljesítettnek puszta implicit utalásból.

## Kimeneti fájlok

- `scores_manual.csv`: a 102 kötelező Mérés A-sor `manual` és `final` oszlopa kitöltve
- `d1_scores_manual.csv`: a 48 UNT-sor `manual_native` és `manual_distortion` oszlopa kitöltve

Az eredeti csatolmányok változatlanok maradtak; a kitöltött eredmények külön fájlokba kerültek.
