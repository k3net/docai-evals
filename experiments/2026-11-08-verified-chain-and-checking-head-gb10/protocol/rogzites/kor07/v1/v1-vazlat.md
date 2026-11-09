# 07 v1 — a rögzített elemzés (vázlat Dani jóváhagyására)

Ez a lap rögzíti, mit és hogyan értékelünk a friss CAL- és TESZT-szeleten, a pecsét nyitása előtt. A runbook
(`07-runbook.md`, a rögzítéskor `07-runbook-v1.md`) a részletes leírás; ahol a kettő eltér, ez a lap dönt. A rögzítés
után a lista csak új verzióval (v1.1) módosítható, a pecsét alatti eredmények megtekintése előtt.

**Állapot:** 2026-11-01. A pecsétmanifest a K07F3 (78 fájl, teljes, mindkét keret). A fejek elkészültek és a
manifestben vannak (F3R). **A címkeaudit kapuja átment** (300 / 300, 0 hiba, felső korlát 0,99%). **D1, D5, D6
megerősítve (Dani, 2026-11-01).** A rögzítéshez Dani „mehet”-je kell; a diagnosztikai minta 3. köre külön, nem feltétel.

## 1. Kérdések és döntési szabályok

- **K1 (elsődleges):** az állapotjelző B1 (négyállapotú prompt) saját pontszámánál (B1-4S) jobb-e a rá tanított
  megbízhatósági fej (B1-4R) rangsora: ΔAURC = AURC(B1-4R) − AURC(B1-4S) a friss TESZT-en, négyosztályos szigorú
  helyességgel, családonként és a három család egyenlő súlyú átlagában.
- **A 06 8.3 szabálya a D4-gyel (D5), előre rögzítve — a fej fejlesztése indokolt, ha:**
  1. legalább két családon B1-4R − B1-4S < 0 (pontbecslés);
  2. átlag(AURC_B1-4R) / átlag(AURC_B1-4S) ≤ 0,90 (pontbecslés), **és** az arány 95%-os bootstrap-intervallumának
     felső határa < 1.
  - Az erőbecslés (F4, a 06 TESZT-en mint próbán): az arány SE-je 0,025, a D4 ereje 10%-os valódi csökkenésnél 0,98,
    a két pont együtt 15%-nál 0,98; a próba hatása −50%. **Javaslat: a szabály marad; Dani megerősítése kell.**
- **K2 (gyakorlati, D9–D10):** a négy fő karon (B1-S, B1-R, B1-4S, B1-4R) a hasznos lefedettség (helyesen lezárt /
  összes ügy) és a lezárási hibaarány (hibásan lezárt / összes lezárt) a friss TESZT-en, a CAL-on választott τ-val.
  - A τ csak a lezárható javaslatokon (SELECT és X / NONE): a legnagyobb elfogadott halmaz, ahol a lezárás
    precizitásának egyoldali 95%-os CP-alsó határa ≥ 0,95 és legalább 200 lezárt ügy van. Munkapont nélkül a kar semmit
    nem zár le (hasznos lefedettség 0).
  - **Következtetés a három család egyenlő súlyú átlagán, a családonkénti eredmények kötelező közlésével:**
    - „a prompt behozza a fejet” = (B1-4S − B1-R) hasznos-lefedettség-különbségének alsó határa > −0,03 **és** mindkét
      kar teljesíti a hibafeltételt;
    - „a fej javít a prompt mellett” = (B1-4R − B1-4S) alsó határa > 0 **és** a B1-4R teljesíti;
    - **hibafeltétel:** a lezárási hibaarány pontbecslése ≤ 0,05 a TESZT-en; ha a 95%-os felső határa 0,05 fölött van,
      az ítélet „bizonytalan”, nem „behozta” / „javít”.
  - **Külön sor:** a helyes adatbekérés (Y a MISSING_DATA-n) és a helyes továbbítás (Z az OUT_OF_SCOPE-on) aránya; a
    nem lezárt ügyek bontása (adatbekérés, továbbítás, τ alatt). A felső korlát az összetételből 80%.
- **A döntési kapcsolás (Dani iránya):** ha a B1-4S önmagában behozza a B1-R-t → az egyszerűbb megoldás; ha a B1-4R a
  B1-4S mellett is javít → a fej fejlesztése; ha a többlet főként a hiányzó adat és a hatókör jelzése → termékfunkció
  (megalapozott döntés, adatbekérés, továbbítás).
- **Ez kutatási továbblépés**, nem automatizálási garancia. A 10%, a −3 pont és az 5% gyakorlati választás.
- **Érvényességi kör:** a három család, az előírt összetétel (06 D9), az 500 példás célterületi adaptáció, a
  négyállapotú prompt D1 szerinti szövegei.

## 2. Adat

- **Friss szeletek:** családonként CAL 500 + TESZT 1000, új sablonokkal (nyelvenként 15 CAL + 30 TESZT sablon), a
  06 T500 sablonjaitól és egymástól diszjunktan; MATCH 60% / NO_MATCH 20% / MISSING_DATA 10% / OUT_OF_SCOPE 10%, fele
  magyar, fele angol (06 D9). Az itemfájlok sha256-a a K07F3 pecsétmanifestben és a MANIFEST.sha256-ban.
- **Tanítóadat:** a 06 T500 (családonként 500 item, nyitott), a négyállapotú prompttal újrakiolvasva; a B1-4R0 a 05
  D_meta-n (5796 item), a négyállapotú prompttal.
- **A minőség, ami a rögzítéskor ismert:**
  - címkeaudit (06 D14, `audit07`): 300 item, családonként 100, állapot × nyelv rétegezve, vakon — **300 / 300 egyezik,
    0 címkehiba, az egyoldali 95%-os felső korlát 0,99% ≤ 2%: átment** (`kor07/eredmenyek/F2/audit/osszesito.json`);
    a Gemma 51 eltérése mind MISSING_DATA / NO_MATCH, MATCH-eltérés nincs, az 5 felülvizsgált kulcs címkéje helyes;
  - a Gemma második ítélete (06 D15, triage): egyezés 89,6%, a mintázat a 06-é (MATCH 97,7–100%, OUT_OF_SCOPE 100%,
    MISSING_DATA alacsony a Gemma Y nélküli keretében); felülvizsgálati lista 22 MATCH-eltérés + 78 NO_MATCH 4/4;
    itemet nem töröltünk és nem javítottunk;
  - a generálás programellenőrzése (szabálylogika, tények) minden itemen; elveszett terv 35 / 8 / 6 a 1952-ből.
- **Kétértelmű item nincs**; modellkimenet alapján nem válogattunk.

## 3. Karok és a mentett fejek (`b1rel07 tanit`, F3R, 2026-11-01 08:04; `cache/k07/fejek`, 101 fájl, sha256 a `fejek.json`-ban)

| kar | mi | megbízhatósági pontszám |
|---|---|---|
| B1-S | a 06-os prompt | a B1 saját pontszáma (temperature a 05 D_cal_prob-ról, 1,946) |
| B1-N | a 06-os prompt | a B1-S, a NONE-javaslatok hátra (06 D8, D20-sor) |
| B1-R | a 06-os prompt | a 06 fej, a 06 receptje: D_meta-előtanítás (`cache/k06/b1rel`) + T500-finomhangolás, 5 sablonos fold, seed 17 / 42 / 73; a fold-modellek mentve; a 06 TESZT-en bitre azonos az F0 reprodukcióval |
| B1-LR | a 06-os prompt | öt jellemző (top-1 − top-2, p(X), egyetértés, q, NONE-jelző), L2-LR, C sablonos CV-vel; mentve |
| B1-4S | négyállapotú prompt | a B1-4 saját pontszáma: a négy sorrend átlagolt valószínűsége a választott válaszon; temperature a 06 T500-án (1,584; D2) |
| B1-4R0 | négyállapotú prompt | a D_meta-n előtanított fej, célterületi tanítás nélkül |
| B1-4R | négyállapotú prompt | a B1-4R0 a család T500-án finomhangolva (ugyanaz a recept, mint a B1-R; D3); 15 kis jellemző, a választott válasz sorának rejtett állapotai |
| B1-4LR | négyállapotú prompt | D12: top-1 − top-2, q, egyetértés, p(X), p(Y), p(Z), a válasz típusa (4 indikátor); L2-LR |

- **A szeletek szerepe:** T500 tanítás és modellválasztás (sablonos foldok, belső korai megállás, C); CAL csak a τ; TESZT
  végső értékelés, rajta semmi nem illesztődik. A fejek a rögzítés előtt készültek, a friss adatot nem látták.
- **A pontozás:** `b1rel07 pontoz --szelet <család>:<CAL|TESZT>` mindkét kerettel (a `pecset07.kapu` a rögzítés
  után nyit); a pontozó út a 06 TESZT-en ellenőrizve (0 eltérés a tanítás közben mérttől és az F0-tól).

## 4. Végpontok

- **Elsődleges:** K1 ΔAURC (B1-4R − B1-4S), a 8.3 + D4 szabállyal (1.).
- **Gyakorlati:** K2 a négy fő karon, a D10 következtetéseivel (1.); a B1-N, B1-LR, B1-4LR, B1-4R0 leíróan.
- **Kötelező sorok:** a döntések helyessége és a tévesztési mátrix mindkét prompton (prompttulajdonság); a D20 bontás
  (SELECT- és nem-SELECT javaslatok AURC-ja külön); a helyes adatbekérés / továbbítás; **magyar bontás** (minden végpont
  nyelvenként).
- **Leíró:** E-AURC mindkét prompton (D13; promptok között nem összevethető); B1-4R − B1-4LR; B1-4R − B1-R és
  B1-4S − B1-R keresztpárok (a gyakorlati következtetés a K2-re épül); enyhe helyesség; a futások közti eltérés.
- **Nem része a v1-nek:** a diagnosztikai (nehéz) minta — külön közölt, a D6 és a D11 szerint, a 3. kör konstrukciója
  után; a 07B valódi adata.

## 5. Statisztika

- **Bootstrap:** sabloncsoportos klaszteres (D23), családonként; az átlagnál a családok rögzítettek; 10 000 ismétlés,
  seed 20261101; egy ismétlésen belül minden kar ugyanazokat a csoportokat kapja; a K2-nél a CAL is újramintázva, a τ
  replikánként újra; a munkapont nélküli replikák aránya külön sor.
- **A futások összevonása (D24):** a pontbecslés és minden replika a három seed mérőinek átlaga.
- Kétoldali bootstrap-p; a családok Holm-korrigált p-je leíró.
- **Erő (F4, `kor07/eredmenyek/F4/ero.md`; a 06 TESZT mint próba):** az arány SE-je 0,025 (K1), MDE80 7% relatív
  csökkenés; a K2 különbségeinek SE-je a próbán 2–9 pont családonként.

## 6. Futtatás (F5, Dani „mehet”-je után)

```bash
python3 kor07/eszkozok/befagyaszt07.py ellenoriz
# a spark-deven (a pecsét alatti jellemzők ott vannak):
for f in penzugy.bankparositas muszaki.hibaelharitas szabaly.koltsegelszamolas; do
  for s in CAL TESZT; do py kor07/eszkozok/b1rel07.py pontoz --szelet "$f:$s" --out cache/k07/f5; done
done
# helyben (back után):
python3 kor07/eszkozok/elemzes07.py --be cache/k07/f5 --forras k07 --reps 10000 --out kor07/eredmenyek/F5
```

A kód a rögzítés előtt a 06 CAL / TESZT-en futott próbaként (`kor07/eredmenyek/F4/proba/`): a B1-R munkapontja a 06
eredménylapját adja vissza, a K1 arányok az erőbecsléssel egyeznek. Várható futásidő: a pontozás kb. 1 perc, az
elemzés kb. 3 perc.

## 7. Döntések a rögzítés előtt (Dani)

| # | kérdés | állapot |
|---|---|---|
| D1 | a négyállapotú prompt szövegei | **megerősítve (Dani, 2026-11-01): a szövegek maradnak** (a Z ritka használata eredmény, nem hiba) |
| D5 | a K1 szabály | **megerősítve (Dani, 2026-11-01): a 06 8.3 + D4**, az erőbecslés után |
| D6 | a diagnosztikai minta mérete és konstrukciója | **megerősítve (Dani, 2026-11-01)**; a 3. kör konstrukciója külön, nem feltétele a rögzítésnek |
| audit | a címkeaudit kapuja | **átment (2026-11-01): 300 / 300, 0 hiba, 0,99% ≤ 2%** |
| rögzítés | „mehet” | a manifest után, valódi üzenetben — **nyitott** |
