# Ellenőrző kör — mit, hol és hogyan validálj

> ⚠️ **Terminológia (2026-08-26):** ahol ez a dokumentum „ellenőrző kör”-t vagy „ellenőrző bírálatt” ír, az a
> **GPT-5.6 Sol ellenőrző bírálata** (tételenként, a teljes válasszal és a rubrikával, a Qwen3.6-35B
> gépi bíráló ítélete mellé); emberi vak értékelés nem történt. A dolgozat ezt végig „ellenőrző kör”
> néven hozza.

> Ez az útmutató a dolgozat **kötelező ellenőrző validációs körét** írja le. Két kör van
> (Mérés A és Mérés D1), plusz egy opcionális harmadik. Amíg ezek nincsenek meg, a
> `reports/02_meres_a.md` és `reports/05_meres_d.md` fejlécében ott áll a figyelmeztetés,
> hogy a számok csak a gépi bíráló első köréből származnak.

## Miért kötelező ez a kör

A válaszokat első körben a **Qwen3.6-35B** bírálta el (prod vLLM, spark-alpha). Ez a bíráló
**ugyanabból a modellcsaládból** való, mint a vizsgált modell (Qwen3.5-9B-Base) — egy
családon belüli bíráló szisztematikusan elnézőbb lehet a saját rokona hibáival szemben.
A dolgozat fő állításai (3×3 pontossági mátrix, a nyelvhatáron átmenő tudás aránya)
közvetlenül ezekre az ítéletekre épülnek, ezért ezeket embernek kell megerősítenie.

Két független mérés is azt mutatja, hogy **van mit javítani**:

- Egy második, **más modellcsaládból** való bíráló (Claude) a 102 kötelező válaszból
  **15 ponton** tért el az elsőtől (egyezés 85%).
- A **négy pontosságot módosító eltérés mind ugyanabba az irányba mutat: az első bíráló
  volt engedékenyebb**, és négyből három a *nem forrásnyelvi* cellákban. Vagyis a gépi
  bíráló a nyelvhatáron átmenő tudást inkább **felülbecsli** — pont azt a számot, ami a
  dolgozat egyik fő állítása.

---

## Fájltérkép — melyik fájl mire való

| Fájl | Szerep | Ki írja |
|---|---|---|
| `reports/02_kezi_ellenorzes.md` | **1. kör olvasnivalója** — 102 válasz kérdéssel, várt válasszal, a modell válaszával és a bíráló indoklásával | csak olvasod |
| `results/scores.csv` → `manual` oszlop | **1. kör beírnivalója** | te |
| `reports/05_kezi_ellenorzes_d1.md` | **2. kör olvasnivalója** — 48 UNT-válasz, komponensenkénti pipákkal | csak olvasod |
| `results/d1_scores.csv` → `manual_native`, `manual_distortion`, `manual_ctrl` | **2. kör beírnivalója** | te |
| `reports/03_classifier_minta.md` → `osztály` oszlop | **3. (opcionális) kör** — 100 token nyelvi besorolása | te |
| `code/set_manual.py` | segédeszköz a beíráshoz (ajánlott a kézi CSV-szerkesztés helyett) | — |
| `reports/02_meres_a.md`, `reports/05_meres_d.md` | a **kimenet**, amit a körök után újragenerálsz | generált |

⛔ **Ne szerkeszd kézzel a CSV-t szövegszerkesztőben.** A `scores.csv` `answer` oszlopa
idézőjeleket, vesszőket és sortöréseket tartalmaz; egy elrontott sor némán elronthat egy
cellát a mátrixban. Használd a `set_manual.py`-t, vagy nyisd meg táblázatkezelőben
(UTF-8, vesszős elválasztó) és csak a ellenőrző oszlophoz nyúlj.

### Hol tartok?

```bash
cd <experiment-dir>
python3 code/set_manual.py status
```

```
Mérés A   — az ellenőrző körben újraítélve:   0 / 162 válasz (a kötelező 102-ből még 102 hátra)
D1 UNT    — az ellenőrző körben újraítélve:   0 / 48 válasz (még 48 hátra)
D1 kontr. — az ellenőrző körben újraítélve:   0 / 48 válasz (opcionális)
```

✅ A ellenőrző oszlopok **túlélik** a `judge.py` / `judge_d1.py` újrafuttatását — a szkriptek
`(item_id, nyelv)` kulcson átmentik őket. Nyugodtan félbehagyhatod és folytathatod.

---

# 1. kör — Mérés A (kötelező, 102 válasz)

**Olvasnivaló:** [`reports/02_kezi_ellenorzes.md`](02_kezi_ellenorzes.md)
**Hatókör:** a **ZH csoport (19 item × 3 nyelv = 57)** és a **HU csoport (15 × 3 = 45)** —
összesen 102 válasz. A UNI csoport 60 válasza **nem kötelező** (ott a pontosság 90–100%,
és a bíráló egyetlen vitatott ítéletet sem hozott).
**Becsült idő:** 2–3 óra. Nem kell egyben.

## A négy ítélet — pontos definíció

Ugyanaz a rubrika, amit a gépi bíráló is kapott:

| ítélet | mikor |
|---|---|
| `helyes` | a válasz tartalmazza a várt információt. A megfogalmazás eltérhet, **a nyelv is**. Bőbeszédű, de helyes válasz = `helyes`. |
| `reszben` | a lényeg megvan, de pontatlan vagy nem teljes; vagy a válasz önmagát cáfolja, és az olvasónak nem egyértelmű, mit állít |
| `helytelen` | más információt ad, kitér, vagy nem válaszol a kérdésre |
| `hallucinacio` | **magabiztosan állít KONKRÉT, kitalált tényeket** — nevet, dátumot, helyet, kiadást —, amelyek tévesek |

### Döntési fa

```
Benne van a várt információ?
├─ IGEN, pontosan ......................................... helyes
├─ RÉSZBEN (jó irány, pontatlan / hiányos / önellentmondó) . reszben
└─ NEM
   ├─ Konkrét kitalált tény van benne (név, évszám, hely)? . hallucinacio
   └─ Egyébként (téved, kitér, nem válaszol) .............. helytelen
```

## ⚠️ Amire külön figyelj — itt volt gyenge a gépi bíráló

1. **`hallucinacio` vs. `helytelen`.** A bíráló 162 válaszból **mindössze 2-t** nevezett
   hallucinációnak. Pedig például *„A nagy ho-ho-ho-horgász meséit József Attila írta”*
   egyértelműen ide tartozik: konkrét, magabiztos, kitalált szerző. A megkülönböztetés
   nem kozmetika — a dolgozat külön állítást tesz a hallucinációs mintázatra.
   *Ez az átsorolás a pontossági mátrixot nem változtatja* (egyik sem `helyes`), de a
   hallucináció-táblát igen.
2. **`reszben`.** A bíráló **egyetlenegyszer sem** használta. Ezért a „szigorú” és a
   „megengedő” pontossági tábla jelenleg karakterre azonos — ami önmagában gyanús.
   Ha a válasz a jó irányba mutat, de nem mondja ki a lényeget, az `reszben`.
3. **A nem forrásnyelvi cellák.** A négy ismert engedékenységi hiba közül három itt volt.
   Ha egy magyar itemre adott angol vagy kínai választ látsz „helyes”-nek jelölve,
   olvasd el kétszer.

## ⚠️ Amit NE rójunk fel

- **A válasz nyelve.** Ha magyar kérdésre angolul válaszol, az önmagában nem hiba —
  a mérés pont azt vizsgálja, hogy a tudás elérhető-e a kérdés nyelvén.
- **Csonkolt vagy hurokba esett válasz.** Ahol a fejlécben ott a `⚠️ csonkolt` vagy
  `⚠️ ismétlési hurok`, ott **csak a meglévő szövegrészt** értékeld. Ha a hiányzó rész
  miatt nem lehet eldönteni, az nem a modell hibája — az addig leírtak alapján ítélj.
  (A 258 válaszból 23 ütközött a token-keretbe és 25 esett ismétlési hurokba, nyelvenként
  eltérő arányban: hu 14 · zh 9 · en 2. Ezért kap külön jelölést.)
- **`⚠️ önértékelő toldalék levágva`.** A base modell néha a saját tanítófeladatát
  másolja a válasz végére („请判断…”, „A single-select problem…”). Ezt a
  `clean_answers.py` levágta; az íven **a megtisztított szöveget látod**, ugyanazt,
  amit a bíráló is kapott. A levágott rész nem számít bele az ítéletbe.

## Ha nem olvasol kínaiul

A 102 kötelező válaszból 34 kínai nyelvű. Ezekhez az íven megvan
- a **várt válasz kínaiul is** (a kérdés nyelvén), és
- a **bíráló indoklása magyarul**, ami idézi, mit állított a modell.

A legtöbb esetben a döntés „ezt állítja-e vagy mást” — ehhez ez elég. Ahol nem vagy
biztos, **hagyd a bíráló ítéletét** és jegyezd fel; a `set_manual.py status` úgyis
megmutatja, mennyi maradt megerősítés nélkül. (Ha kéred, legyártom az ív magyar tükrét,
de akkor a *fordítást* validálod, nem az eredetit — ezt a módszertanban jelezni kell.)

## Kezdd a vitás tételekkel

Az ív **első szekciója** (`## ⚠️ Vitás tételek`) hozza azt a 15 pontot, ahol a két gépi
bíráló eltért. Ebből **négy változtatja meg a pontossági mátrixot** — ezekkel kezdd:

| item | nyelv | 1. bíráló | 2. bíráló | a vita tárgya |
|---|---|---|---|---|
| HU04 | angol | helyes | helytelen | „for the duration of Pentecost” — a várt válasz a *következő* pünkösdig, azaz egy év |
| HU07 | kínai | helyes | reszben | az első mondat jó, aztán a válasz önmagát cáfolja |
| HU08 | angol | helyes | reszben | az időszak nagyjából stimmel, a pontos ablak nem |
| ZH10 | magyar | helyes | helytelen | a válasz nem dönt: felsorolja a lehetőségeket, majd elvágódik |

**A te ítéleted a döntő** — a második bíráló is gép, csak másik családból.

## Beírás

```bash
python3 code/set_manual.py a HU04 en helytelen      # item, nyelv (hu|en|zh), ítélet
python3 code/set_manual.py a HU07 zh reszben
python3 code/set_manual.py a ZH10 hu --clear        # visszavonás
```

Vagy táblázatkezelőben: `results/scores.csv`, **`manual`** oszlop, a
`helyes` / `reszben` / `helytelen` / `hallucinacio` szavak valamelyike.

> **Csak akkor írj be, ha ELTÉRSZ?** Nem. Írd be az egyetértést is — a
> `set_manual.py status` így tudja megmutatni, hány válasz van már az ellenőrző körben
> megnézve, és a riport fejléce is ezt a számot hozza. Az „ennyiből ennyi újraítélve” a
> módszertani fejezet egyik mondata.

## Kiértékelés

```bash
python3 code/analyze_a.py
```

Frissül: `reports/02_meres_a.md`, `reports/02_meres_a.json` és a hozzá tartozó ábrák.
A `final` oszlop = a `manual`, ahol ki van töltve, egyébként a `judge`.

**Mit nézz meg utána:**
1. A fejléc `az ellenőrző körben újraítélve: 102/162` és a figyelmeztető mondat eltűnt-e.
2. A **„Megengedő pontosság”** tábla eltér-e már a szigorútól (ha nem adtál egyetlen
   `reszben`-t sem, gondold végig újra).
3. A **„Kontroll — csak a csonkolatlan”** tábla ugyanazt a mintázatot mutatja-e, mint a
   teljes mátrix. Ha igen, a nyelvek közti különbség nem a dekódolás műterméke.
4. Az érzékenységvizsgálati szekció most már **a te köröd** és a második gépi bíráló
   különbségét mutatja.

---

# 2. kör — Mérés D1 (kötelező, 48 válasz)

**Olvasnivaló:** [`reports/05_kezi_ellenorzes_d1.md`](05_kezi_ellenorzes_d1.md)
**Hatókör:** mind a 48 UNT-válasz (16 lefordíthatatlan fogalom × 3 nyelv).
**Becsült idő:** 1–1,5 óra.

## Mit kell eldöntened

Fogalmanként előre rögzítettünk **2–3 kötelező jelentéskomponenst** (`native`) és
**2 torzítás-jelet** (`distortion`). A bíráló mindegyikre külön mondott igent/nemet;
az íven ezt látod pipaként:

```
### magyar  ⚠️ csonkolt, ismétlési hurok

- [ ] **native 1:** kölcsönös: a segítséget viszonozni kell
- [x] **native 2:** közösségi, szervezett (több ember)
- [ ] **native 3:** fizetség nélkül, de elvárt visszasegítés
- [ ] *distortion 1:* egyszeri, önkéntes jótett viszonzás-elvárás nélkül
- [ ] *distortion 2:* 'volunteering'/'charity' keretezés
```

A te dolgod **komponensenként** eldönteni, majd a **darabszámot** beírni.

### Szabályok

- **Tartalmilag számít, nem szó szerint.** Ha a válasz körülírja a komponenst, az találat.
- **A válasz nyelve nem számít.** Kínai válaszban is megjelenhet a magyar komponens.
- **Csonkolt / hurokba esett válasznál csak a meglévő szövegrészt értékeld.**
- A `distortion` a **hibás keretezés**: a fogalmat egy ismerős idegen kategóriába sorolja
  (pl. a *kaláka* → „potluck”, „volunteering”). Ez akkor is torzítás, ha közben egy-két
  natív komponenst eltalál — a kettő **nem zárja ki egymást**.
- A `native` és a `distortion` **egymástól függetlenül** számolandó.

## Beírás

```bash
# UNT-válasz: hány native és hány distortion komponens van meg
python3 code/set_manual.py d UNT-HU01 hu --native 2 --distortion 1
python3 code/set_manual.py d UNT-ZH05 en --native 0            # csak az egyiket is lehet
python3 code/set_manual.py d UNT-HU01 hu --clear
```

A szkript ellenőrzi, hogy a szám az adott fogalomnál értelmes-e (`native` legfeljebb 2
vagy 3, `distortion` legfeljebb 2) — elgépelt számot nem enged be.

Vagy táblázatkezelőben: `results/d1_scores.csv`, **`manual_native`** és
**`manual_distortion`** oszlop a `kind=unt` sorokban.

## A kontrollszavak (opcionális)

A 48 kontroll-válasz (hétköznapi szavak definíciója) azt méri, hogy a nyelvek közti
különbség a *lefordíthatatlanságból* jön-e, vagy a modell általános nyelvi
teljesítményéből. A bíráló itt megbízhatóbb (egyszerűbb feladat), ezért ez a kör
**nem kötelező** — de ha egy fogalomnál gyanús a kontroll, felülírhatod:

```bash
python3 code/set_manual.py c UNT-HU01 zh rossz     # jo | reszben | rossz
```

## Kiértékelés

```bash
python3 code/analyze_d.py
```

Frissül: `reports/05_meres_d.md`, `reports/05_meres_d.json` + ábrák. A fejléc kiírja,
hány cella lett kézzel felülírva.

**Mit nézz meg utána:**
1. A **D1 komponens-lefedettségi tábla** forrásnyelvi sorai (a `← forrásnyelv` jelölés).
2. A **párosított előjelteszt** p-értéke — a ellenőrző kör ezt mozdíthatja el leginkább,
   mert fogalmanként párosít, tehát kevés elem is számít.
3. A **kontroll-tábla** — ha a nyelvi különbség ott is megvan, a D1 különbsége nem a
   fogalmak lefordíthatatlanságáról szól.

---

# 3. kör — nyelvosztályozó minta (opcionális)

**Fájl:** [`reports/03_classifier_minta.md`](03_classifier_minta.md) — 100 véletlen token
(seed 0) a logit lens top-20-ából, gépi nyelvi besorolással.

Ez a kör **már megvolt egy második értékelővel**: a mért egyezés **92/100**, és mind a
8 eltérés ugyanaz a típus (rövid latin betűs töredék vagy tulajdonnév, ami véletlenül
benne van valamelyik szótárban) — az eredmény a
[`reports/03_classifier_ellenorzes.md`](03_classifier_ellenorzes.md)-ben áll.

Ha harmadik szemként átnézed: írd át az `osztály` oszlopot a
`03_classifier_minta.md`-ben, majd a `code/classifier_check.py`-ban vezetett
`ELTERES` szótárt kell hozzáigazítani. Ez a szám a Mérés B módszertani lábjegyzete —
a fő állításokat nem mozdítja.

---

# Ellenőrző lista — mikor kész a ellenőrző kör

- [ ] `python3 code/set_manual.py status` → **Mérés A: 102/162 (KÉSZ)**
- [ ] `python3 code/set_manual.py status` → **D1 UNT: 48/48 (KÉSZ)**
- [ ] `python3 code/analyze_a.py` lefutott, a `02_meres_a.md` fejlécéből eltűnt a
      „⛔ a kötelező ellenőrző kör … még hátravan” mondat
- [ ] `python3 code/analyze_d.py` lefutott, a fejléc nem 0 ellenőrző felülírást jelez
- [ ] Adtál legalább néhány `reszben` és `hallucinacio` ítéletet (ha egyet sem, az
      valószínűleg azt jelenti, hogy átvetted a bíráló kategória-vakságát)
- [ ] A `02_meres_a.md` „Megengedő pontosság” táblája már **nem** azonos a szigorúval
- [ ] Feljegyezted, hány válasznál tértél el a bírálótól — ez a módszertani fejezetbe megy
      („a 102 válaszból N-nél írtam felül a gépi ítéletet”)

# Gyakori hibák

| ❌ ne | ✅ helyette |
|---|---|
| a CSV `answer` oszlopát átírni | csak a `manual*` oszlophoz nyúlj, vagy `set_manual.py` |
| a csonkolt választ a hiányzó rész miatt lepontozni | csak a meglévő szövegrészt értékeld |
| az idegen nyelvű választ hibának venni | a válasz nyelve nem hiba |
| mindent `helytelen`-re vinni | a kitalált konkrétum `hallucinacio`, a féligazság `reszben` |
| csak az eltéréseket beírni | az egyetértést is írd be — abból lesz a „az ellenőrző körben újraítélve” szám |
| a `judge.py` újrafuttatásától félni | a ellenőrző oszlopokat a szkript átmenti |
