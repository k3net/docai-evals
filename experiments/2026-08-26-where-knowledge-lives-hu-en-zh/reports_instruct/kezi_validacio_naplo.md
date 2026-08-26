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

## Hol vannak az ítéletek

Nincs külön „manual” fájl: az ellenőrző kör ítéletei ugyanabban a két CSV-ben élnek, saját
oszlopokban, a gépi bíráló ítélete mellett. Így egy soron mindig látszik mindkét vélemény.

| Fájl | Az ellenőrző kör oszlopai | Gépi bíráló |
|---|---|---|
| `results_instruct/scores.csv` | `manual` (102 sor kitöltve) | `judge` |
| `results_instruct/d1_scores.csv` | `manual_native`, `manual_distortion` (48 UNT-sor) | `native_hit`, `distortion_hit` |

A `scores.csv` `final` oszlopa **származtatott**, nem önálló adat: `manual`, ha nem üres,
különben `judge`. A szabály egyetlen helyen él (`code/check_scores.py` → `derive()`), és
ugyanaz a szkript ellenőrzi is:

```bash
python3 code/check_scores.py          # invariáns-ellenőrzés, hiba esetén 1-es kilépőkód
python3 code/check_scores.py --fix    # a származtatott oszlop újraszámolása
```

⛔ 2026-08-26-ig a lemezre írt `final` oszlop 45 soron elavult volt (ott, ahol az ellenőrző kör
eltért a bírálótól, a `final` a bíráló ítéletén maradt). Az elemzők menet közben újraszámolták,
ezért **egyetlen riport-szám sem volt téves**, de aki a CSV-t közvetlenül olvasta, mást kapott:
a HU-csoport magabiztos kitalálás-aránya 62 % helyett 3 %-ot. Az oszlop javítva, az őr beépítve.
